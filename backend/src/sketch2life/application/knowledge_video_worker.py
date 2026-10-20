"""Owned08 worker orchestration + guarded private staging/receipt recovery.

No durable bridge implementation, provider activation or production registration.
Local worker outcomes are NOT foundation job-state updates or delivery ACKs.
"""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, replace
from typing import Literal

from sketch2life.application.knowledge_video_media import (
    PreparedVideoMedia,
    VideoMediaPipeline,
    _admit_blob,
    media_operation_key,
)
from sketch2life.application.ports.ai_jobs import WorkerDispatchEnvelope
from sketch2life.application.ports.knowledge_video_media import (
    MediaProfileResolver,
    RenderAttempt,
    RenderAuthority,
)
from sketch2life.application.ports.knowledge_video_worker import (
    AtomicVideoFinalizer,
    StagedVideo,
    VideoFinalizationReceipt,
    VideoPrivateStaging,
    VideoWorkerAdmission,
)
from sketch2life.domain.ai_jobs.model import JobState, ResultDisposition
from sketch2life.domain.knowledge_video.media import MediaProfile, validate_decoded
from sketch2life.domain.knowledge_video.model import (
    FinalArtifact,
    VideoError,
    VideoRun,
    canonical_digest,
    require_hash,
    require_id,
    require_revision,
    require_time,
)


@dataclass(frozen=True, slots=True)
class VideoWorkerOutcome:
    status: Literal["accepted", "discarded", "ignored", "pending", "rejected"]
    reason_code: Literal[
        "VIDEO_ACCEPTED",
        "VIDEO_RESULT_NOT_CURRENT",
        "VIDEO_WORK_NOT_STARTED",
        "VIDEO_WORK_PENDING",
        "VIDEO_DISPATCH_REJECTED",
        "VIDEO_RECEIPT_UNVERIFIED",
    ]
    receipt_ref: str | None = None
    completion_key: str | None = None
    cleanup_state: Literal["not_requested", "pending"] = "not_requested"
    staging_key: str | None = None


def staging_key(attempt: RenderAttempt, media: PreparedVideoMedia) -> str:
    return canonical_digest(
        {
            "schema": "BE2-08.Stage/0.1-candidate",
            "operation": media.operation_key,
            "pin": media.pin_digest,
            "job": attempt.run.job_id,
            "attempt": attempt.run.attempt_id,
            "bytes": media.blob.sha256,
        }
    )


def completion_key(attempt: RenderAttempt, media: PreparedVideoMedia, stage: StagedVideo) -> str:
    return canonical_digest(
        {
            "schema": "BE2-08.Finalize/0.1-candidate",
            "staging": staging_key(attempt, media),
            "artifact": stage.artifact.material(),
        }
    )


def _validate_stage(
    attempt: RenderAttempt, media: PreparedVideoMedia, stage: StagedVideo
) -> StagedVideo:
    stage = replace(stage)
    if (
        stage.job_id != attempt.run.job_id
        or stage.attempt_id != attempt.run.attempt_id
        or stage.pin_digest != attempt.run.pin.digest()
        or stage.staging_key != staging_key(attempt, media)
        or stage.artifact.hash != media.blob.sha256
    ):
        raise VideoError("VIDEO_STAGING_MISMATCH")
    return stage


def _receipt(
    attempt: RenderAttempt,
    media: PreparedVideoMedia,
    stage: StagedVideo,
    result: VideoFinalizationReceipt,
) -> VideoWorkerOutcome:
    key = completion_key(attempt, media, stage)
    if not isinstance(result, VideoFinalizationReceipt) or result.completion_key != key:
        raise VideoError("VIDEO_RECEIPT_MISMATCH")
    receipt = result.job_receipt
    require_id(receipt.receipt_id)
    require_hash(receipt.fingerprint)
    require_revision(receipt.job_revision_after)
    require_time(receipt.recorded_at)
    if (
        receipt.authoritative is not True
        or receipt.job_id != attempt.run.job_id
        or receipt.attempt_id != attempt.run.attempt_id
        or receipt.recorded_at < attempt.run.created_at
        or not isinstance(receipt.disposition, ResultDisposition)
        or not isinstance(result.job_state, JobState)
    ):
        raise VideoError("VIDEO_RECEIPT_MISMATCH")
    if receipt.disposition is ResultDisposition.ACCEPTED:
        if type(result.video_run) is not VideoRun:
            raise VideoError("VIDEO_RECEIPT_MISMATCH")
        completed_run = replace(result.video_run)
        expected = attempt.run.finalize(
            attempt.run.run_revision,
            stage.attempt_id,
            FinalArtifact(
                stage.artifact,
                attempt.run.pin.digest(),
                attempt.run.pin.encoding,
                attempt.run.pin.content_profile,
            ),
        )
        if (
            completed_run != expected
            or receipt.job_revision_after <= attempt.job_revision
            or result.job_state is not JobState.SUCCEEDED
        ):
            raise VideoError("VIDEO_RECEIPT_MISMATCH")
        return VideoWorkerOutcome("accepted", "VIDEO_ACCEPTED", receipt.receipt_id, key)
    if result.video_run is not None:
        raise VideoError("VIDEO_RECEIPT_MISMATCH")
    return VideoWorkerOutcome("discarded", "VIDEO_RESULT_NOT_CURRENT", receipt.receipt_id, key)


class VideoCompletionService:
    def __init__(
        self,
        authority: RenderAuthority,
        profiles: MediaProfileResolver,
        staging: VideoPrivateStaging,
        finalizer: AtomicVideoFinalizer,
    ) -> None:
        self._authority, self._profiles = authority, profiles
        self._staging, self._finalizer = staging, finalizer

    def _validate_binding(self, attempt: RenderAttempt, media: PreparedVideoMedia) -> None:
        pin = attempt.run.pin
        if (
            not isinstance(media, PreparedVideoMedia)
            or media.pin_digest != pin.digest()
            or media.operation_key != media_operation_key(attempt)
            or media.strategy is not pin.strategy
        ):
            raise VideoError("VIDEO_MEDIA_BINDING_MISMATCH")

    def _validate_media(self, attempt: RenderAttempt, media: PreparedVideoMedia) -> None:
        self._validate_binding(attempt, media)
        pin = attempt.run.pin
        profile = self._profiles.resolve(attempt)
        if not isinstance(profile, MediaProfile):
            raise VideoError("VIDEO_PROFILE_UNAVAILABLE")
        profile = replace(profile)
        if (
            profile.content_profile != pin.content_profile
            or profile.encoding != pin.encoding
            or pin.strategy not in profile.strategies
        ):
            raise VideoError("VIDEO_PROFILE_UNAVAILABLE")
        blob = _admit_blob(media.blob, profile)
        report = replace(media.decoded)
        validate_decoded(report, profile, blob.sha256)

    def complete(self, attempt: RenderAttempt, media: PreparedVideoMedia) -> VideoWorkerOutcome:
        # Exceptions here mean pending, not a fabricated failure/completion claim.
        # The outer worker handles redaction; this service never logs raw exceptions.
        attempt = replace(attempt)
        self._authority.check(attempt, "before_stage")
        self._validate_media(attempt, media)
        key = staging_key(attempt, media)
        try:
            stage = _validate_stage(attempt, media, self._staging.stage(attempt, media, key))
        except Exception:
            # Unknown stage ACK can still have created private copies. Keep the
            # original journal key for lookup; never guess foreign cleanup targets.
            return VideoWorkerOutcome("pending", "VIDEO_WORK_PENDING", staging_key=key)
        return self.reconcile(attempt, media, stage)

    def recover_stage(
        self, attempt: RenderAttempt, media: PreparedVideoMedia
    ) -> VideoWorkerOutcome:
        """Use original retained preparation, no provider/stage side effects."""
        self._validate_binding(attempt, media)
        key = staging_key(attempt, media)
        try:
            stage = self._staging.lookup(attempt, key)
            if stage is not None:
                stage = _validate_stage(attempt, media, stage)
        except Exception:
            return VideoWorkerOutcome("pending", "VIDEO_WORK_PENDING", staging_key=key)
        if stage is None:
            return VideoWorkerOutcome("pending", "VIDEO_WORK_PENDING", staging_key=key)
        return self.reconcile(attempt, media, stage)

    def reconcile(
        self, attempt: RenderAttempt, media: PreparedVideoMedia, stage: StagedVideo
    ) -> VideoWorkerOutcome:
        """Recovery from retained private stage; never calls generator/stage again."""
        self._validate_binding(attempt, media)
        stage = _validate_stage(attempt, media, stage)
        key = completion_key(attempt, media, stage)
        # Look up before current teaching eligibility: a prior accepted receipt is
        # historical fact, not current exposure permission. Query MUST authenticate
        # original backend recovery scope. Unavailable is NOT "known absent".
        try:
            previous = self._finalizer.lookup(attempt, key)
        except Exception:
            return VideoWorkerOutcome("pending", "VIDEO_WORK_PENDING", completion_key=key)
        if previous is not None:
            return self._confirmed(attempt, media, stage, previous)
        try:
            self._authority.check(attempt, "after_stage")
            self._validate_media(attempt, media)
            self._authority.check(attempt, "before_finalize")
        except Exception:
            self._quarantine(attempt, stage, key)
            return VideoWorkerOutcome(
                "pending", "VIDEO_RESULT_NOT_CURRENT", completion_key=key, cleanup_state="pending"
            )
        try:
            result = self._finalizer.finish(attempt, stage, media, key)
        except Exception:
            # Commit may already exist. NO cleanup/rerender/retry here; recover by
            # original completion key. Do not quarantine a possibly accepted asset.
            return VideoWorkerOutcome("pending", "VIDEO_WORK_PENDING", completion_key=key)
        return self._confirmed(attempt, media, stage, result)

    def _confirmed(
        self,
        attempt: RenderAttempt,
        media: PreparedVideoMedia,
        stage: StagedVideo,
        result: VideoFinalizationReceipt,
    ) -> VideoWorkerOutcome:
        try:
            outcome = _receipt(attempt, media, stage, result)
        except Exception:
            return VideoWorkerOutcome(
                "pending",
                "VIDEO_RECEIPT_UNVERIFIED",
                completion_key=completion_key(attempt, media, stage),
            )
        if outcome.status == "discarded":
            self._quarantine(attempt, stage, outcome.completion_key or "")
            return replace(outcome, cleanup_state="pending")
        return outcome

    def _quarantine(self, attempt: RenderAttempt, stage: StagedVideo, key: str) -> None:
        # Private registry MUST retain pending cleanup. This request never proves
        # durable acknowledgement or actual effect/deletion, including on failure.
        with suppress(Exception):
            self._staging.request_quarantine(attempt, stage, key)


class VideoWorker:
    def __init__(
        self,
        admission: VideoWorkerAdmission,
        pipeline: VideoMediaPipeline,
        completion: VideoCompletionService,
        *,
        job_type: str,
    ) -> None:
        require_id(job_type)
        self._admission, self._pipeline, self._completion = admission, pipeline, completion
        self._job_type = job_type

    def handle(self, envelope: WorkerDispatchEnvelope) -> VideoWorkerOutcome:
        try:
            if envelope.message.job_type != self._job_type:
                return VideoWorkerOutcome("rejected", "VIDEO_DISPATCH_REJECTED")
            attempt = self._admission.begin(envelope)
            if attempt is None:
                return VideoWorkerOutcome("ignored", "VIDEO_WORK_NOT_STARTED")
            attempt = replace(attempt)
            if (
                attempt.run.job_id != envelope.message.job_id
                or attempt.run.attempt_id != envelope.message.attempt_id
                or attempt.capability != envelope.capability
            ):
                return VideoWorkerOutcome("rejected", "VIDEO_DISPATCH_REJECTED")
            return self._completion.complete(attempt, self._pipeline.prepare(attempt))
        except Exception:
            # No raw diagnostic, failure claim, automatic retry, provider fallback
            # or reset of a terminal job. Foundation owns timeout/retry policy.
            return VideoWorkerOutcome("pending", "VIDEO_WORK_PENDING")
