"""BE2-01 Phase A pure domain lifecycle (DATA-25 candidate) and provider-copy semantics."""

from __future__ import annotations

import ast
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sketch2life.domain.ai_jobs import model as jobs
from sketch2life.domain.ai_jobs import provider_copy as copies
from sketch2life.domain.ai_jobs.completion import (
    CompletionClaim,
    OutcomeKind,
    PreconditionVerdict,
    canonical_sha256,
    check_completion_preconditions,
)
from sketch2life.domain.ai_jobs.model import (
    InvalidJobTransition,
    InvalidProgress,
    JobPollPolicy,
    JobProgress,
    JobRetryPolicy,
    JobScope,
    JobState,
    ProgressKind,
    RequestRef,
    ResultDisposition,
    ResultRef,
)

NOW = datetime(2026, 10, 14, 13, 0, tzinfo=UTC)
POLICY = JobRetryPolicy("test.retry.v0", 3, 1000, 2, 8000, 30000)
POLL = JobPollPolicy("test.poll.v0", 2000, 10000, 10)
REF = RequestRef("req_1", 1, "a" * 64, 1)
SCOPE = JobScope("org_1", "session_1", ("child_1",), "purpose_1", "target_1")
RESULT = (ResultRef("artifact_1", "b" * 64, "test"),)


def new_job() -> jobs.AiJob:
    return jobs.create_job(job_id="job_1", attempt_id="att_1", job_type="t", scope=SCOPE,
                           request_ref=REF, correlation_id="corr_1", retry_policy=POLICY, now=NOW)


def running() -> jobs.AiJob:
    return jobs.start_attempt(new_job(), "att_1", NOW)


def test_created_job_is_queued_with_first_attempt_and_unknown_progress() -> None:
    job = new_job()
    assert job.state is JobState.QUEUED
    assert (job.job_revision, job.active_attempt.attempt_number) == (1, 1)
    assert job.progress == JobProgress(ProgressKind.UNKNOWN)
    assert job.progress.value is None and job.started_at is None


def test_happy_path_revisions_increase_and_success_is_not_approval() -> None:
    job = running()
    assert job.state is JobState.RUNNING and job.job_revision == 2
    done = jobs.succeed(job, "att_1", result_refs=RESULT, disposition=ResultDisposition.ACCEPTED,
                        now=NOW)
    assert done.state is JobState.SUCCEEDED and done.job_revision == 3
    assert done.result_disposition is ResultDisposition.ACCEPTED
    assert not {"approved", "played", "session_complete"} & set(done.__slots__)


def test_retryable_failure_backs_off_then_requeues_same_semantic_job() -> None:
    failed = jobs.record_failure(running(), "att_1", code="PROVIDER_TIMEOUT", retryable=True,
                                 public_message="m", now=NOW)
    assert failed.state is JobState.FAILED_RETRYABLE
    assert failed.retry_not_before == NOW + timedelta(milliseconds=1000)
    assert failed.failure is not None and failed.failure.attempts_remaining == 2
    with pytest.raises(InvalidJobTransition, match="backoff"):
        jobs.requeue_for_retry(failed, new_attempt_id="att_2", now=NOW)
    later = NOW + timedelta(seconds=1)
    again = jobs.requeue_for_retry(failed, new_attempt_id="att_2", now=later)
    assert again.state is JobState.QUEUED and again.job_id == "job_1"
    assert [a.attempt_number for a in again.attempts] == [1, 2]
    assert again.active_attempt.request_ref == REF


def test_retries_are_bounded_by_named_policy() -> None:
    job = running()
    moment = NOW
    for attempt in range(1, 4):
        job = jobs.record_failure(job, job.active_attempt.attempt_id, code="PROVIDER_TIMEOUT",
                                  retryable=True, public_message="m", now=moment)
        if attempt < 3:
            moment += POLICY.backoff_after(attempt)
            job = jobs.requeue_for_retry(job, new_attempt_id=f"att_{attempt + 1}", now=moment)
            job = jobs.start_attempt(job, f"att_{attempt + 1}", moment)
    assert job.state is JobState.FAILED_EXHAUSTED and len(job.attempts) == 3
    assert job.failure is not None and job.failure.attempts_remaining == 0
    assert POLICY.backoff_after(10) == timedelta(milliseconds=8000)


def test_non_retryable_failure_exhausts_immediately() -> None:
    job = jobs.record_failure(running(), "att_1", code="OUTPUT_MALFORMED", retryable=False,
                              public_message="m", now=NOW)
    assert job.state is JobState.FAILED_EXHAUSTED and job.completed_at == NOW


@pytest.mark.parametrize("state", ["queued", "running", "failed_retryable"])
def test_cancel_invalidates_scheduled_retry_and_terminal_never_reopens(state: str) -> None:
    job = new_job() if state == "queued" else running()
    if state == "failed_retryable":
        job = jobs.record_failure(job, "att_1", code="X_ERR", retryable=True, public_message="m",
                                  now=NOW)
    cancelled = jobs.cancel(job, reason_code="CANCELLED_BY_TEACHER", public_message="m", now=NOW)
    assert cancelled.state is JobState.CANCELLED and cancelled.retry_not_before is None
    later = NOW + timedelta(minutes=5)
    for transition in (
        lambda: jobs.requeue_for_retry(cancelled, new_attempt_id="att_9", now=later),
        lambda: jobs.start_attempt(cancelled, "att_1", later),
        lambda: jobs.succeed(cancelled, "att_1", result_refs=RESULT,
                             disposition=ResultDisposition.ACCEPTED, now=later),
        lambda: jobs.cancel(cancelled, reason_code="AGAIN", public_message="m", now=later),
    ):
        with pytest.raises(InvalidJobTransition):
            transition()


def test_unsafe_block_and_stale_success_are_distinct_axes() -> None:
    blocked = jobs.block_unsafe(running(), "att_1", public_message="m", now=NOW)
    assert blocked.state is JobState.BLOCKED_UNSAFE
    assert blocked.result_disposition is ResultDisposition.REJECTED
    stale = jobs.succeed(running(), "att_1", result_refs=RESULT,
                         disposition=ResultDisposition.STALE, now=NOW, lineage_note="ctx 1->2")
    assert stale.state is JobState.SUCCEEDED and stale.result_disposition is ResultDisposition.STALE
    assert "stale" not in {s.value for s in JobState}
    with pytest.raises(InvalidJobTransition):
        jobs.succeed(running(), "att_1", result_refs=(), disposition=ResultDisposition.ACCEPTED,
                     now=NOW)


@pytest.mark.parametrize(
    ("kind", "value", "label"),
    [
        (ProgressKind.UNKNOWN, 0.0, None),
        (ProgressKind.UNKNOWN, None, "x"),
        (ProgressKind.PERCENTAGE, None, None),
        (ProgressKind.PERCENTAGE, 100.5, None),
        (ProgressKind.PERCENTAGE, -1.0, None),
        (ProgressKind.PERCENTAGE, float("nan"), None),
        (ProgressKind.PERCENTAGE, True, None),
        (ProgressKind.STAGES, None, None),
        (ProgressKind.STAGES, None, ""),
    ],
)
def test_malformed_progress_is_rejected_not_coerced(
    kind: ProgressKind, value: float | None, label: str | None
) -> None:
    with pytest.raises(InvalidProgress):
        JobProgress(kind, value, label)


def test_truthful_progress_values_are_preserved() -> None:
    job = jobs.report_progress(running(), "att_1", JobProgress(ProgressKind.PERCENTAGE, 0.0), NOW)
    assert job.progress.value == 0.0 and job.job_revision == 3
    same = jobs.report_progress(job, "att_1", JobProgress(ProgressKind.PERCENTAGE, 0.0), NOW)
    assert same is job
    with pytest.raises(InvalidJobTransition):
        jobs.report_progress(job, "att_other", JobProgress(ProgressKind.UNKNOWN), NOW)


def test_poll_hint_is_bounded_and_stops_on_terminal() -> None:
    job = new_job()
    assert jobs.poll_after_ms(job, POLL, NOW) == 2000
    assert jobs.poll_after_ms(job, POLL, NOW + timedelta(seconds=10)) == 4000
    assert jobs.poll_after_ms(job, POLL, NOW + timedelta(hours=1)) == 10000
    failed = jobs.record_failure(running(), "att_1", code="X_ERR", retryable=True,
                                 public_message="m", now=NOW)
    assert jobs.poll_after_ms(failed, POLL, NOW) == 2000
    done = jobs.cancel(job, reason_code="CANCELLED_BY_TEACHER", public_message="m", now=NOW)
    assert jobs.poll_after_ms(done, POLL, NOW) is None


def claim(job_id: str = "job_1", attempt_id: str = "att_1", **changes: object) -> CompletionClaim:
    base = CompletionClaim(job_id, attempt_id, 1, "a" * 64, 1, OutcomeKind.SUCCESS)
    return replace(base, **changes)  # type: ignore[arg-type]


def test_completion_preconditions_order() -> None:
    assert check_completion_preconditions(running(), claim()) is PreconditionVerdict.PROCEED
    assert check_completion_preconditions(new_job(), claim()) is PreconditionVerdict.INVALID_STATE
    assert check_completion_preconditions(running(), claim(attempt_id="att_0")) is (
        PreconditionVerdict.ATTEMPT_SUPERSEDED
    )
    for change in ({"input_hash": "c" * 64}, {"expected_request_revision": 2},
                   {"context_revision": 5}):
        assert check_completion_preconditions(running(), claim(**change)) is (
            PreconditionVerdict.INPUT_MISMATCH
        )
    cancelled = jobs.cancel(running(), reason_code="CANCELLED_BY_TEACHER", public_message="m",
                            now=NOW)
    assert check_completion_preconditions(cancelled, claim()) is PreconditionVerdict.JOB_CANCELLED


def test_completion_fingerprint_ignores_diagnostics_but_not_outputs() -> None:
    assert claim(diagnostic="secret-1").fingerprint() == claim(diagnostic="other").fingerprint()
    assert claim().fingerprint() != claim(moderation="unsafe").fingerprint()
    assert canonical_sha256({"b": "é", "a": 1}) == canonical_sha256({"a": 1, "b": "é"})


def test_request_ref_and_timestamps_are_validated() -> None:
    with pytest.raises(ValueError):
        RequestRef("req", 1, "A" * 64, 0)
    with pytest.raises(ValueError):
        jobs.create_job(job_id="j", attempt_id="a", job_type="t", scope=SCOPE, request_ref=REF,
                        correlation_id="c", retry_policy=POLICY, now=datetime(2026, 10, 14))


def _copy(profile: str = "p") -> copies.ProviderCopy:
    return copies.ProviderCopy("copy_1", "org_1", "job_1", copies.CopyKind.OUTPUT, profile)


def _receipt(outcome: copies.ReceiptOutcome, verified: bool,
             evidence: copies.EvidenceKind = copies.EvidenceKind.FIXTURE) -> copies.PurgeReceipt:
    return copies.PurgeReceipt("r1", "copy_1", outcome, verified, evidence)


def test_provider_copy_deleted_requires_verified_receipt_and_fixture_is_not_actual() -> None:
    purging = copies.request_purge(_copy())
    unverified = copies.apply_receipt(purging, _receipt(copies.ReceiptOutcome.DELETED, False))
    assert unverified.status is copies.CopyStatus.PENDING
    fixture = copies.apply_receipt(purging, _receipt(copies.ReceiptOutcome.DELETED, True))
    assert fixture.status is copies.CopyStatus.DELETED and not fixture.actual_deletion_proven
    assert copies.report_label(fixture) == "fixture_deleted_not_actual"
    provider = copies.apply_receipt(
        purging, _receipt(copies.ReceiptOutcome.DELETED, True, copies.EvidenceKind.PROVIDER)
    )
    assert provider.actual_deletion_proven and copies.report_label(provider) == "deleted"
    for outcome in (copies.ReceiptOutcome.PENDING, copies.ReceiptOutcome.UNSUPPORTED,
                    copies.ReceiptOutcome.EXCEPTION):
        result = copies.apply_receipt(purging, _receipt(outcome, True))
        assert result.status is not copies.CopyStatus.DELETED
        assert copies.report_label(result) != "deleted"
    with pytest.raises(copies.InvalidCopyTransition):
        copies.apply_receipt(fixture, replace(_receipt(copies.ReceiptOutcome.PENDING, False),
                                              receipt_id="r2"))
    assert copies.request_cancel(fixture) is fixture
    assert (copies.CONTRACT_OWNER, copies.FAKE_SUPPORT_OWNER) == ("BE2-14", "BE2-01")


def test_domain_package_imports_no_framework_storage_queue_or_provider() -> None:
    banned = {"fastapi", "pydantic", "sqlalchemy", "redis", "rq", "boto3", "httpx", "torch"}
    package = Path(jobs.__file__).resolve().parent
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = (
                [a.name for a in node.names] if isinstance(node, ast.Import)
                else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            )
            assert not {n.split(".")[0] for n in names} & banned, path.name
