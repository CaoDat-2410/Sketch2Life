"""Strict persisted run envelope. No schema adoption or authority inferred from JSON."""

from __future__ import annotations

import json
from dataclasses import asdict

from pydantic import AwareDatetime, Field

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.knowledge_video import StrictVideoModel, VideoExactRef
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    FinalArtifact,
    ReviewState,
    Strategy,
    VideoError,
    VideoPin,
    VideoRun,
)


class _Pin(StrictVideoModel):
    organization_id: OpaqueId
    session_id: OpaqueId
    bundle: VideoExactRef
    editorial_revision: int = Field(ge=0)
    context_revision: int = Field(ge=0)
    audience_revision: int = Field(ge=0)
    sources: tuple[VideoExactRef, ...] = Field(min_length=1)
    strategy: Strategy
    content_profile: VideoExactRef
    encoding: VideoExactRef
    rights: VideoExactRef
    retry_policy: VideoExactRef
    policy: VideoExactRef
    policy_epoch: int = Field(ge=1)
    model_profile: VideoExactRef | None
    library_asset: VideoExactRef | None


class _Artifact(StrictVideoModel):
    artifact: VideoExactRef
    pin_digest: Sha256Hex
    encoding: VideoExactRef
    content_profile: VideoExactRef


class _Run(StrictVideoModel):
    video_id: OpaqueId
    video_version: int = Field(ge=1)
    run_revision: int = Field(ge=1)
    review_revision: int = Field(ge=1)
    job_id: OpaqueId
    pin: _Pin
    created_at: AwareDatetime
    generation_state: JobState
    review_state: ReviewState
    attempt_id: OpaqueId | None
    artifact: _Artifact | None


def encode_run(run: VideoRun) -> dict[str, object]:
    try:
        payload = _Run.model_validate(asdict(run)).model_dump(mode="json")
        decode_run(payload)  # Recheck domain invariants, not merely field shapes.
        return payload
    except (TypeError, ValueError):
        raise VideoError("VIDEO_STORAGE_CORRUPT") from None


def _ref(value: VideoExactRef) -> ExactRef:
    return ExactRef(value.ref, value.version, value.hash)


def decode_run(payload: object) -> VideoRun:
    try:
        stored = _Run.model_validate_json(json.dumps(payload, allow_nan=False))
        p = stored.pin
        pin = VideoPin(
            p.organization_id, p.session_id, _ref(p.bundle), p.editorial_revision,
            p.context_revision, p.audience_revision, tuple(_ref(item) for item in p.sources),
            p.strategy, _ref(p.content_profile), _ref(p.encoding), _ref(p.rights),
            _ref(p.retry_policy), _ref(p.policy), p.policy_epoch,
            None if p.model_profile is None else _ref(p.model_profile),
            None if p.library_asset is None else _ref(p.library_asset)
        )
        a = stored.artifact
        artifact = None if a is None else FinalArtifact(
            _ref(a.artifact), a.pin_digest, _ref(a.encoding), _ref(a.content_profile)
        )
        return VideoRun(
            stored.video_id, stored.video_version, stored.run_revision, stored.review_revision,
            stored.job_id, pin, stored.created_at, stored.generation_state,
            stored.review_state, stored.attempt_id, artifact
        )
    except (TypeError, ValueError, OverflowError, RecursionError):
        raise VideoError("VIDEO_STORAGE_CORRUPT") from None
