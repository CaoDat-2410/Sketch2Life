"""Owned08 worker/staging/atomic-completion candidate. Actual D03 adoption OPEN."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sketch2life.application.knowledge_video_media import PreparedVideoMedia
from sketch2life.application.ports.ai_jobs import CompletionReceipt, WorkerDispatchEnvelope
from sketch2life.application.ports.knowledge_video_media import RenderAttempt
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    VideoError,
    VideoRun,
    require_hash,
    require_id,
)


@dataclass(frozen=True, slots=True)
class StagedVideo:
    """Private immutable candidate, never a public URL/exposure capability."""

    artifact: ExactRef
    job_id: str
    attempt_id: str
    pin_digest: str
    staging_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.artifact, ExactRef):
            raise VideoError("VIDEO_STAGING_MISMATCH")
        ExactRef(self.artifact.ref, self.artifact.version, self.artifact.hash)
        require_id(self.job_id)
        require_id(self.attempt_id)
        require_hash(self.pin_digest)
        require_hash(self.staging_key)


@dataclass(frozen=True, slots=True)
class VideoFinalizationReceipt:
    completion_key: str
    job_receipt: CompletionReceipt
    video_run: VideoRun | None
    job_state: JobState


class VideoWorkerAdmission(Protocol):
    def begin(self, envelope: WorkerDispatchEnvelope) -> RenderAttempt | None:
        """Use actual foundation start/capability/current request and owner guards.
        Verify message type/expected original request refs against persisted job.
        Coordinate own run start through adopted same-UoW/recoverable protocol;
        never describe separately committed job/run starts as atomic.
        None means do not invoke provider (settled/duplicate/not current); it does
        NOT mean succeeded. Recover ambiguous persisted work without rerendering.
        No direct job table write, role-based bypass or unverified broker payload.
        """
        ...


class VideoPrivateStaging(Protocol):
    def lookup(self, attempt: RenderAttempt, staging_key: str) -> StagedVideo | None:
        """Authenticated original-scope recovery from private durable journal.
        None means known absent; unavailable raises. No inference to rerender or
        create another copy. Retained preparation metadata/bytes allow recovery.
        """
        ...

    def stage(
        self, attempt: RenderAttempt, media: PreparedVideoMedia, staging_key: str
    ) -> StagedVideo:
        """Outside DB tx; original scoped immutable bytes, key/body dedup. Durably
        register private copies BEFORE/with effect so lost ACKs stay discoverable.
        Stage never exposes output or overwrites an original/final artifact.
        """
        ...

    def request_quarantine(
        self, attempt: RenderAttempt, staged: StagedVideo, completion_key: str
    ) -> None:
        """Scoped idempotent keep-private intent, not verified purge/deletion.
        Never after ambiguous commit. Processing MUST fence accepted references
        atomically with finalization: accepted wins even if another worker commits
        after caller's absent lookup. Request alone cannot hide/delete accepted
        artifacts. Actual storage authority/intent persistence/receipt are external.
        """
        ...


class AtomicVideoFinalizer(Protocol):
    def lookup(
        self, attempt: RenderAttempt, completion_key: str
    ) -> VideoFinalizationReceipt | None:
        """Authenticated original-scope authoritative receipt query for recovery.
        None must mean known absent, NOT timeout/unavailable. Missing/unavailable
        authority raises and leaves pending; never guess that commit did not occur.
        """
        ...

    def finish(
        self,
        attempt: RenderAttempt,
        staged: StagedVideo,
        media: PreparedVideoMedia,
        completion_key: str,
    ) -> VideoFinalizationReceipt:
        """One adopted authorized foundation UoW: verify capability/current attempt,
        request/context/policy epoch and current owner/source/consent/profile/kill;
        private stage/hash/decoder proof; run+job CAS, exact receipt/audit/outbox.
        Hold actual fences to commit; do not call job acceptance then commit video
        separately. Stale/rejected output stays unexposed and cleanup intent durable.
        Foundation receipt fingerprint is its OWN namespace, not completion_key.
        No new Teacher approval/playback/stage advance. Ambiguous exceptions require
        lookup; a native authoritative=True field alone is not actual conformance.
        """
        ...
