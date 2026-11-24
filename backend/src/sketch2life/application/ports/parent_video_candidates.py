"""Application contracts for the local synthetic Parent LTX candidate path."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from sketch2life.application.ports.identity import VerifiedPrincipal


class ParentVideoCandidateError(RuntimeError):
    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ParentVideoCandidateScene:
    scene_index: int
    title: str
    action: str
    visual_prompt: str
    duration_ms: int
    character_anchors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KeyframeSecondary:
    entity_id: str
    label: str
    box: tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class KeyframeInputs:
    """FEAT-087: what the video worker needs to compose keyframes (never shown to the adult)."""

    main_box: tuple[int, int, int, int]
    facing: str
    secondaries: tuple[KeyframeSecondary, ...]
    staging: dict[str, Any] | None
    staging_issue: str | None


@dataclass(frozen=True, slots=True)
class ParentVideoCandidateSource:
    run_id: str
    profile_id: str
    story_revision_id: str
    story_revision_no: int
    story_sha256: str
    story_duration_ms: int
    source_asset_ref: str
    source_asset_version: int
    source_asset_sha256: str
    source_media_type: str
    source_size_bytes: int
    confirmed_subject: str
    activity_selection_id: str
    activity_snapshot_sha256: str
    scenes: tuple[ParentVideoCandidateScene, ...]
    keyframe_inputs: KeyframeInputs | None = None


@dataclass(frozen=True, slots=True)
class ParentVideoCandidateRecord:
    video_candidate_id: str
    run_id: str
    story_revision_id: str
    story_revision_no: int
    story_sha256: str
    source_asset_sha256: str
    activity_selection_id: str
    activity_snapshot_sha256: str
    state: str
    modal_call_id: str | None
    job_id: str
    generation_id: str
    attempt_id: str
    attempt_prefix: str
    output_asset_ref: str | None
    output_sha256: str | None
    output_size_bytes: int | None
    output_manifest_sha256: str | None
    output_metadata: dict[str, Any] | None
    safe_failure_code: str | None
    created_at: datetime
    updated_at: datetime


class ParentVideoCandidateRepositoryPort(Protocol):
    def reserve_candidate(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_profile_id: str,
        expected_story_revision: int,
        expected_story_sha256: str,
        idempotency_key_sha256: str,
        request_fingerprint_sha256: str,
        video_candidate_id: str,
        job_id: str,
        generation_id: str,
        attempt_id: str,
        attempt_prefix: str,
    ) -> tuple[ParentVideoCandidateRecord, ParentVideoCandidateSource | None, bool]: ...

    def get_current_candidate(
        self, *, principal: VerifiedPrincipal, run_id: str
    ) -> ParentVideoCandidateRecord | None: ...

    def get_candidate(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord: ...

    def mark_dispatching(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord: ...

    def mark_dispatched(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        video_candidate_id: str,
        modal_call_id: str,
    ) -> ParentVideoCandidateRecord: ...

    def mark_generating(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord: ...

    def mark_dispatch_uncertain(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord: ...

    def mark_failed(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        video_candidate_id: str,
        safe_failure_code: str,
    ) -> ParentVideoCandidateRecord: ...

    def begin_output_contract_recovery(
        self, *, principal: VerifiedPrincipal, run_id: str, video_candidate_id: str
    ) -> ParentVideoCandidateRecord | None: ...

    def mark_candidate_ready(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        video_candidate_id: str,
        output_asset_ref: str,
        output_sha256: str,
        output_size_bytes: int,
        output_manifest_sha256: str,
        output_metadata: dict[str, Any],
    ) -> ParentVideoCandidateRecord: ...


@dataclass(frozen=True, slots=True)
class SilentStoryWorkerOutput:
    result: dict[str, Any]
    output_manifest_bytes: bytes
    video_bytes: bytes


class SilentStoryVideoWorkerPort(Protocol):
    def dispatch(
        self,
        *,
        worker_input: dict[str, Any],
        drawing_bytes: bytes,
        manifest_bytes: bytes,
    ) -> str: ...

    def collect_if_ready(
        self,
        *,
        modal_call_id: str,
        job_id: str,
        generation_id: str,
        attempt_id: str,
        attempt_prefix: str,
    ) -> SilentStoryWorkerOutput | None: ...


__all__ = [
    "ParentVideoCandidateError",
    "ParentVideoCandidateRecord",
    "ParentVideoCandidateRepositoryPort",
    "ParentVideoCandidateScene",
    "ParentVideoCandidateSource",
    "SilentStoryVideoWorkerPort",
    "SilentStoryWorkerOutput",
]
