"""Worker/receipt protocol COMPONENT only. Synthetic receipts are NOT actual
foundation/SQL/storage/authority/copy integration evidence.
"""

from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from sketch2life.application.knowledge_video_media import PreparedVideoMedia, media_operation_key
from sketch2life.application.knowledge_video_worker import (
    VideoCompletionService,
    VideoWorker,
    completion_key,
    staging_key,
)
from sketch2life.application.ports.ai_jobs import (
    CompletionReceipt,
    DispatchMessage,
    WorkerDispatchEnvelope,
)
from sketch2life.application.ports.knowledge_video_media import RenderAttempt
from sketch2life.application.ports.knowledge_video_worker import (
    StagedVideo,
    VideoFinalizationReceipt,
)
from sketch2life.domain.ai_jobs.model import JobState, RequestRef, ResultDisposition
from sketch2life.domain.knowledge_video.media import DecodedMedia, MediaBlob, MediaProfile
from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    FinalArtifact,
    Strategy,
    VideoError,
    VideoPin,
    VideoRun,
)

NOW = datetime(2026, 10, 18, tzinfo=UTC)
JOB_TYPE = "fixture.knowledge_video"
# sha256(b"abc"), bytes are expressly NOT real video/decoder evidence.
MEDIA_HASH = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def ref(name):
    return ExactRef(name, 1, "a" * 64)


def harness():
    pin = VideoPin(
        "school",
        "session",
        ref("bundle"),
        0,
        0,
        0,
        (ref("source"),),
        Strategy.GENERATE,
        ref("profile"),
        ref("encoding"),
        ref("rights"),
        ref("retry"),
        ref("policy"),
        1,
        ref("model"),
    )
    run = VideoRun("video", 1, 1, 1, "job", pin, NOW).start(1, "attempt")
    attempt = RenderAttempt(run, 2, "fixture-private-capability")
    profile = MediaProfile(
        pin.content_profile,
        pin.encoding,
        tuple(Strategy),
        ("fixture",),
        ("fixture",),
        ((16, 16),),
        100,
        1000,
        128,
        2,
        (),
        0,
    )
    media = PreparedVideoMedia(
        pin.digest(),
        media_operation_key(attempt),
        MediaBlob(b"abc", MEDIA_HASH),
        DecodedMedia(MEDIA_HASH, "fixture", "fixture", 16, 16, 500, 12, (), True),
        pin.strategy,
    )
    stage = StagedVideo(
        ExactRef("private.asset", 1, MEDIA_HASH),
        "job",
        "attempt",
        pin.digest(),
        staging_key(attempt, media),
    )
    key = completion_key(attempt, media, stage)
    receipt = CompletionReceipt(
        "receipt", "job", "attempt", "c" * 64, ResultDisposition.ACCEPTED, None, 3, NOW, True
    )
    ready = run.finalize(
        2, "attempt", FinalArtifact(stage.artifact, pin.digest(), pin.encoding, pin.content_profile)
    )
    finalized = VideoFinalizationReceipt(key, receipt, ready, JobState.SUCCEEDED)
    h = SimpleNamespace(
        attempt=attempt,
        media=media,
        stage=stage,
        key=key,
        finalized=finalized,
        authority=Mock(),
        profiles=Mock(resolve=Mock(return_value=profile)),
        staging=Mock(stage=Mock(return_value=stage)),
        finalizer=Mock(lookup=Mock(return_value=None), finish=Mock(return_value=finalized)),
        admission=Mock(begin=Mock(return_value=attempt)),
        pipeline=Mock(prepare=Mock(return_value=media)),
    )
    h.completion = VideoCompletionService(h.authority, h.profiles, h.staging, h.finalizer)
    h.worker = VideoWorker(h.admission, h.pipeline, h.completion, job_type=JOB_TYPE)
    h.envelope = WorkerDispatchEnvelope(
        DispatchMessage(
            "dispatch", "job", "attempt", 1, JOB_TYPE, RequestRef("video", 1, pin.digest(), 0)
        ),
        attempt.capability,
    )
    return h


def test_success_has_exact_receipt_but_no_playback_grant_or_raw_capability():
    h = harness()
    result = h.worker.handle(h.envelope)
    assert result.status == "accepted" and result.receipt_ref == "receipt"
    assert result.completion_key == h.key
    assert not hasattr(result, "artifact") and not hasattr(result, "playback_url")
    assert "fixture-private-capability" not in repr(result)
    assert h.attempt.run.artifact is None  # Original immutable snapshot unchanged.
    h.staging.request_quarantine.assert_not_called()


def test_already_settled_dispatch_never_calls_pipeline_or_stage():
    h = harness()
    h.admission.begin.return_value = None
    assert h.worker.handle(h.envelope).status == "ignored"
    h.pipeline.prepare.assert_not_called()
    h.staging.stage.assert_not_called()


def test_wrong_job_type_rejected_before_admission():
    h = harness()
    envelope = replace(h.envelope, message=replace(h.envelope.message, job_type="wrong"))
    assert h.worker.handle(envelope).status == "rejected"
    h.admission.begin.assert_not_called()


@pytest.mark.parametrize("field,value", [("job_id", "other"), ("attempt_id", "other")])
def test_admission_cannot_substitute_attempt(field, value):
    h = harness()
    changed = replace(h.attempt.run, **{field: value})
    h.admission.begin.return_value = replace(h.attempt, run=changed)
    assert h.worker.handle(h.envelope).status == "rejected"
    h.pipeline.prepare.assert_not_called()


def test_admission_cannot_substitute_capability():
    h = harness()
    h.admission.begin.return_value = replace(h.attempt, capability="other")
    assert h.worker.handle(h.envelope).status == "rejected"
    h.pipeline.prepare.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("pin_digest", "b" * 64),
        ("operation_key", "b" * 64),
        ("strategy", Strategy.REVIEWED_LIBRARY),
    ],
)
def test_prepared_media_bound_before_staging(field, value):
    h = harness()
    h.pipeline.prepare.return_value = replace(h.media, **{field: value})
    assert h.worker.handle(h.envelope).status == "pending"
    h.staging.stage.assert_not_called()
    h.finalizer.finish.assert_not_called()


def test_wrong_byte_hash_never_staged():
    h = harness()
    h.pipeline.prepare.return_value = replace(h.media, blob=MediaBlob(b"wrong", MEDIA_HASH))
    assert h.worker.handle(h.envelope).status == "pending"
    h.staging.stage.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("job_id", "other"),
        ("attempt_id", "other"),
        ("pin_digest", "b" * 64),
        ("staging_key", "b" * 64),
        ("artifact", ExactRef("other", 1, "b" * 64)),
    ],
)
def test_foreign_stage_never_finalized_or_quarantined(field, value):
    h = harness()
    h.staging.stage.return_value = replace(h.stage, **{field: value})
    assert h.worker.handle(h.envelope).status == "pending"
    h.finalizer.finish.assert_not_called()
    h.staging.request_quarantine.assert_not_called()


@pytest.mark.parametrize("phase", ["before_stage", "after_stage", "before_finalize"])
def test_revocation_boundaries_do_not_commit(phase):
    h = harness()

    def check(attempt, current):
        if current == phase:
            raise VideoError("VIDEO_STALE_CONTEXT")

    h.authority.check.side_effect = check
    assert h.worker.handle(h.envelope).status == "pending"
    h.finalizer.finish.assert_not_called()
    if phase == "before_stage":
        h.staging.stage.assert_not_called()
        h.staging.request_quarantine.assert_not_called()
    else:
        h.staging.request_quarantine.assert_called_once_with(h.attempt, h.stage, h.key)


@pytest.mark.parametrize("disposition", [ResultDisposition.STALE, ResultDisposition.REJECTED])
def test_verified_unaccepted_receipt_requests_private_cleanup_not_deleted(disposition):
    h = harness()
    h.finalizer.finish.return_value = replace(
        h.finalized,
        job_receipt=replace(h.finalized.job_receipt, disposition=disposition),
        video_run=None,
        job_state=JobState.CANCELLED,
    )
    result = h.worker.handle(h.envelope)
    assert result.status == "discarded"
    assert not hasattr(result, "deleted")
    h.staging.request_quarantine.assert_called_once()


def test_lost_completion_ack_does_not_quarantine_possibly_accepted_artifact():
    h = harness()
    h.finalizer.finish.side_effect = TimeoutError("synthetic secret diagnostic")
    pending = h.worker.handle(h.envelope)
    assert pending.status == "pending" and pending.completion_key == h.key
    h.staging.request_quarantine.assert_not_called()
    assert "secret" not in repr(pending)
    h.finalizer.lookup.return_value = h.finalized
    recovered = h.completion.reconcile(h.attempt, h.media, h.stage)
    assert recovered.status == "accepted"
    assert (
        h.staging.stage.call_count
        == h.pipeline.prepare.call_count
        == h.finalizer.finish.call_count
        == 1
    )
    h.staging.request_quarantine.assert_not_called()


def test_lookup_unavailable_does_not_assume_absent_or_commit_again():
    h = harness()
    h.finalizer.lookup.side_effect = TimeoutError("synthetic")
    assert h.worker.handle(h.envelope).status == "pending"
    h.finalizer.finish.assert_not_called()
    h.staging.request_quarantine.assert_not_called()


def test_historical_accepted_receipt_not_reinterpreted_after_later_revoke():
    h = harness()
    h.finalizer.lookup.return_value = h.finalized
    h.authority.check.side_effect = VideoError("VIDEO_STALE_CONTEXT")
    result = h.completion.reconcile(h.attempt, h.media, h.stage)
    assert result.status == "accepted"  # Historical fact only, NOT exposure authorization.
    h.authority.check.assert_not_called()
    h.finalizer.finish.assert_not_called()
    h.staging.request_quarantine.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("job_id", "other"),
        ("attempt_id", "other"),
        ("authoritative", False),
        ("authoritative", 1),
        ("job_revision_after", True),
        ("job_revision_after", 2),
        ("receipt_id", "https://secret"),
        ("fingerprint", "bad"),
        ("recorded_at", NOW.replace(tzinfo=None)),
        ("disposition", "accepted"),
    ],
)
def test_invalid_native_receipt_never_accepted_or_cleaned_up(field, value):
    h = harness()
    h.finalizer.finish.return_value = replace(
        h.finalized, job_receipt=replace(h.finalized.job_receipt, **{field: value})
    )
    result = h.worker.handle(h.envelope)
    assert result.status == "pending" and result.reason_code == "VIDEO_RECEIPT_UNVERIFIED"
    h.staging.request_quarantine.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("completion_key", "b" * 64),
        ("video_run", None),
        ("job_state", JobState.FAILED_EXHAUSTED),
        ("job_state", "succeeded"),
    ],
)
def test_wrong_completion_snapshot_not_accepted(field, value):
    h = harness()
    h.finalizer.finish.return_value = replace(h.finalized, **{field: value})
    assert h.worker.handle(h.envelope).reason_code == "VIDEO_RECEIPT_UNVERIFIED"
    h.staging.request_quarantine.assert_not_called()


def test_stage_error_ambiguous_copy_left_pending_not_guessed_deleted():
    h = harness()
    h.staging.stage.side_effect = TimeoutError("synthetic")
    outcome = h.worker.handle(h.envelope)
    assert outcome.status == "pending" and outcome.staging_key == h.stage.staging_key
    h.finalizer.finish.assert_not_called()
    h.staging.request_quarantine.assert_not_called()


def test_generator_error_no_completion_claim_retry_or_stage():
    h = harness()
    h.pipeline.prepare.side_effect = RuntimeError("private internal diagnostic")
    outcome = h.worker.handle(h.envelope)
    assert outcome.status == "pending" and "private" not in repr(outcome)
    h.finalizer.finish.assert_not_called()
    h.staging.stage.assert_not_called()


def test_quarantine_request_failure_does_not_fake_success_or_deletion():
    h = harness()
    h.finalizer.finish.return_value = replace(
        h.finalized,
        video_run=None,
        job_receipt=replace(h.finalized.job_receipt, disposition=ResultDisposition.STALE),
    )
    h.staging.request_quarantine.side_effect = TimeoutError("synthetic")
    result = h.worker.handle(h.envelope)
    assert result.status == "discarded" and not hasattr(result, "deleted")
    assert result.cleanup_state == "pending"


@pytest.mark.parametrize("field", ["video_version", "review_revision"])
def test_native_completed_run_cannot_smuggle_boolean_revision(field):
    h = harness()
    forged = replace(h.finalized.video_run)
    object.__setattr__(forged, field, True)
    h.finalizer.finish.return_value = replace(h.finalized, video_run=forged)
    outcome = h.worker.handle(h.envelope)
    assert outcome.status == "pending" and outcome.reason_code == "VIDEO_RECEIPT_UNVERIFIED"
    h.staging.request_quarantine.assert_not_called()


def test_lost_stage_ack_recovered_by_original_journal_without_rerender():
    h = harness()
    h.staging.stage.side_effect = TimeoutError("synthetic lost ACK")
    pending = h.worker.handle(h.envelope)
    assert pending.staging_key == h.stage.staging_key
    h.staging.lookup.return_value = h.stage
    result = h.completion.recover_stage(h.attempt, h.media)
    assert result.status == "accepted"
    assert h.pipeline.prepare.call_count == h.staging.stage.call_count == 1
    h.staging.lookup.assert_called_once_with(h.attempt, pending.staging_key)
    h.staging.request_quarantine.assert_not_called()


@pytest.mark.parametrize("unavailable", [True, False])
def test_stage_lookup_missing_or_unavailable_does_not_render_or_restage(unavailable):
    h = harness()
    if unavailable:
        h.staging.lookup.side_effect = TimeoutError("synthetic")
    else:
        h.staging.lookup.return_value = None
    result = h.completion.recover_stage(h.attempt, h.media)
    assert result.status == "pending" and result.staging_key == h.stage.staging_key
    h.pipeline.prepare.assert_not_called()
    h.staging.stage.assert_not_called()
    h.finalizer.finish.assert_not_called()
    h.staging.request_quarantine.assert_not_called()
