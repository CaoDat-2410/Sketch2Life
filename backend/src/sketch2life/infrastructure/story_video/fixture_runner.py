"""Fixture video job runner (FEAT-066 T-1a, D11; OD-13 owns the real worker).

No provider is called. The runner advances one accepted generation, one step per call, from
``ACCEPTED`` to a settled state behind ``VideoRenderPort`` (a scripted fixture renderer here). It is
stepped by tests and never scheduled. On ``READY`` it writes a tiny synthetic MP4 stand-in through
``ObjectStoragePort`` and a ``PARENT_ACCOUNT`` ``core_asset_metadata`` row whose ``source_refs`` is
the run id, so the FR-C-08 purge removes it with the run (the key sits under ``parent/{run}/``).
The row carries the generation's own scope: ``PARENT_ACCOUNT`` for a Parent run; ``ORGANIZATION``
with the organization id as ref AND as organization for a Teacher run (T-4b3b D16: the asset
trigger and the T-13a purge need the organization id, never NULL).
The storage key stays inside Story: it is written to ``output_asset_ref`` and never serialized.
"""

from __future__ import annotations

import hashlib
import io
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.story_run_actor import TEACHER_COMMAND_SCOPE_KIND
from sketch2life.application.ports.story_video import (
    GenerationRecord,
    ProgressEvent,
    ProgressResult,
    StoryVideoAdapters,
    VideoRenderPort,
    VideoRenderRequest,
    VideoRenderResult,
)
from sketch2life.application.services.story_run_video import StoryVideoProgressService
from sketch2life.domain.story_video.model import GenerationState
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository

VIDEO_MEDIA_TYPE = "video/mp4"
PROFILE_REF = "fixture-video-profile-v1"
MODEL_REVISION = "fixture-model-1"
SAFETY_POLICY_VERSION = "fixture-safety-1"
_ASSET_VERSION = 1


def synthetic_mp4(seed: str) -> bytes:
    """A few bytes shaped like an MP4 container; never decodable media and never a real clip."""

    ftyp = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"
    payload = hashlib.sha256(seed.encode("utf-8")).digest()
    return ftyp + (8 + len(payload)).to_bytes(4, "big") + b"mdat" + payload


@dataclass
class FixtureVideoRenderer:
    """Scripted renderer: a result registered for a generation id, else a passing clip."""

    results: dict[str, VideoRenderResult] = field(default_factory=dict)
    requests: list[VideoRenderRequest] = field(default_factory=list)

    def render(self, request: VideoRenderRequest) -> VideoRenderResult:
        self.requests.append(request)
        scripted = self.results.get(request.generation_id)
        if scripted is not None:
            return scripted
        return VideoRenderResult(
            content=synthetic_mp4(request.generation_id), media_type=VIDEO_MEDIA_TYPE
        )


class FixtureVideoRunner:
    def __init__(
        self,
        session_factory: Callable[[], Session] | sessionmaker[Session],
        storage: ObjectStoragePort,
        adapters: StoryVideoAdapters | None,
        renderer: VideoRenderPort | None = None,
    ) -> None:
        self._sessions = session_factory
        self._storage = storage
        self._adapters = adapters
        self._renderer: VideoRenderPort = renderer or FixtureVideoRenderer()
        self._rendered: dict[str, VideoRenderResult] = {}

    def step(self, generation_id: str) -> ProgressResult:
        """One state step of one generation; a settled or unknown generation is a no-op."""

        with self._sessions() as session:
            repository = SqlStoryVideoRepository(session)
            record = repository.get_generation(generation_id)
            if record is None:
                return ProgressResult(False, None, "NOT_FOUND")
            service = StoryVideoProgressService(repository, self._adapters)
            state = GenerationState(record.state)
            if state is GenerationState.ACCEPTED:
                return service.apply(generation_id, _move(state, GenerationState.QUEUED))
            if state is GenerationState.QUEUED:
                return service.apply(generation_id, _move(state, GenerationState.GENERATING))
            if state is GenerationState.GENERATING:
                return self._generate(service, record)
            if state is GenerationState.TECHNICAL_VALIDATING:
                return service.apply(generation_id, _move(state, GenerationState.SAFETY_VALIDATING))
            if state is GenerationState.SAFETY_VALIDATING:
                return self._conclude(service, record)
            return ProgressResult(False, record, "SETTLED")

    def run_to_end(self, generation_id: str, *, limit: int = 12) -> ProgressResult:
        result = ProgressResult(False, None, "NOT_FOUND")
        for _ in range(limit):
            result = self.step(generation_id)
            if not result.applied:
                break
        return result

    # ------------------------------------------------------------------ steps
    def _generate(
        self, service: StoryVideoProgressService, record: GenerationRecord
    ) -> ProgressResult:
        rendered = self._renderer.render(
            VideoRenderRequest(
                generation_id=record.generation_id,
                run_id=record.run_id,
                story_revision_id=record.story_revision_id,
                script_hash=record.script_hash,
                scene_count=0,
                job_ref=record.job_ref or "",
            )
        )
        if rendered.failure_code is not None or not (
            rendered.technical_passed and rendered.consistency_passed
        ):
            return service.apply(
                record.generation_id,
                ProgressEvent(
                    expected_state=str(GenerationState.GENERATING),
                    target_state=str(GenerationState.FAILED),
                    safe_failure_code=rendered.failure_code or "VIDEO_VALIDATION_FAILED",
                ),
            )
        self._rendered[record.generation_id] = rendered
        return service.apply(
            record.generation_id,
            ProgressEvent(
                expected_state=str(GenerationState.GENERATING),
                target_state=str(GenerationState.TECHNICAL_VALIDATING),
                video_profile_ref=PROFILE_REF,
                model_revision=MODEL_REVISION,
                config_hash=hashlib.sha256(PROFILE_REF.encode("utf-8")).hexdigest(),
            ),
        )

    def _conclude(
        self, service: StoryVideoProgressService, record: GenerationRecord
    ) -> ProgressResult:
        rendered = self._rendered.pop(record.generation_id, None)
        if rendered is None:
            rendered = VideoRenderResult(
                content=synthetic_mp4(record.generation_id), media_type=VIDEO_MEDIA_TYPE
            )
        if not rendered.safety_passed:
            return service.apply(
                record.generation_id,
                ProgressEvent(
                    expected_state=str(GenerationState.SAFETY_VALIDATING),
                    target_state=str(GenerationState.SAFETY_BLOCKED),
                    safe_failure_code="SAFETY_BLOCKED",
                    safety_finding_codes=rendered.safety_finding_codes,
                    safety_policy_version=SAFETY_POLICY_VERSION,
                ),
            )
        key = f"parent/{record.run_id}/video/{record.generation_id}/output.mp4"
        try:
            self._storage.put_object(
                key,
                io.BytesIO(rendered.content),
                content_type=rendered.media_type,
                content_length=len(rendered.content),
                metadata={"sha256": hashlib.sha256(rendered.content).hexdigest()},
            )
        except ObjectStorageFailure:
            return service.apply(
                record.generation_id,
                ProgressEvent(
                    expected_state=str(GenerationState.SAFETY_VALIDATING),
                    target_state=str(GenerationState.FAILED),
                    safe_failure_code="STORAGE_UNAVAILABLE",
                ),
            )
        self._write_asset(record, key, rendered)
        result = service.apply(
            record.generation_id,
            ProgressEvent(
                expected_state=str(GenerationState.SAFETY_VALIDATING),
                target_state=str(GenerationState.READY),
                output_asset_ref=key,
                output_asset_version=_ASSET_VERSION,
                safety_policy_version=SAFETY_POLICY_VERSION,
            ),
        )
        if not result.applied:
            # The run was cancelled meanwhile: the late result is stale and leaves no object.
            self._discard(key)
        return result

    def _write_asset(self, record: GenerationRecord, key: str, rendered: VideoRenderResult) -> None:
        organization_id = output_asset_organization(record)
        with self._sessions() as session:
            session.add(
                CoreAssetMetadataModel(
                    asset_ref=key,
                    asset_version=_ASSET_VERSION,
                    organization_id=organization_id,
                    owner_scope_kind=record.scope_kind,
                    owner_scope_ref=record.scope_ref,
                    content_sha256=hashlib.sha256(rendered.content).hexdigest(),
                    media_type=rendered.media_type,
                    source_refs=[record.run_id],
                    derived_from_ref=None,
                )
            )
            session.commit()

    def _discard(self, key: str) -> None:
        try:
            self._storage.delete_object(key)
        except ObjectStorageFailure:
            return
        with self._sessions() as session:
            session.execute(
                delete(CoreAssetMetadataModel.__table__).where(  # type: ignore[arg-type]
                    CoreAssetMetadataModel.__table__.c.asset_ref == key
                )
            )
            session.commit()


def output_asset_organization(record: GenerationRecord) -> str | None:
    """The ``organization_id`` of the output asset row: the organization of a Teacher run (also
    its scope ref), NULL for a Parent run (T-4b3b D16)."""

    return record.scope_ref if record.scope_kind == TEACHER_COMMAND_SCOPE_KIND else None


def _move(current: GenerationState, target: GenerationState) -> ProgressEvent:
    return ProgressEvent(expected_state=str(current), target_state=str(target))


__all__ = [
    "MODEL_REVISION",
    "PROFILE_REF",
    "SAFETY_POLICY_VERSION",
    "VIDEO_MEDIA_TYPE",
    "FixtureVideoRenderer",
    "FixtureVideoRunner",
    "output_asset_organization",
    "synthetic_mp4",
]
