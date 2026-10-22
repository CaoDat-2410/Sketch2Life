"""BE2-01 Phase A application semantics with deterministic fakes (fake CAS/receipts only)."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from dataclasses import asdict, replace

import pytest
from sketch2life.application.ports.ai_jobs import CancellationNotice
from sketch2life.application.ports.knowledge_video import (
    VideoLifecycleCreateV1,
    VideoRequestContext,
)
from sketch2life.application.services.ai_jobs import (
    FIXTURE_RETRY_POLICY,
    AiJobError,
    CancelJobCommand,
)
from sketch2life.domain.ai_jobs.completion import CompletionClaim, Moderation, OutputRef
from sketch2life.domain.ai_jobs.model import (
    AiJob,
    JobProgress,
    JobState,
    ProgressKind,
    ResultDisposition,
)
from sketch2life.domain.ai_jobs.provider_copy import CopyKind, CopyStatus, ProviderCopy
from sketch2life.domain.knowledge_video.model import ExactRef, Strategy, VideoPin
from sketch2life.infrastructure.ai_jobs.fakes import FakeProvider, JobRevisionConflict
from sketch2life.infrastructure.ai_jobs.harness import (
    DEVICE,
    ORG,
    OUTSIDER,
    TEACHER,
    TEACHER_2,
    UNGRANTED,
    FixtureHarness,
    build_fixture_harness,
    request_ref,
)

BACKOFF = FIXTURE_RETRY_POLICY.backoff_max_ms


@pytest.fixture
def h() -> FixtureHarness:
    return build_fixture_harness()


def job(h: FixtureHarness, job_id: str) -> AiJob:
    with h.store.transaction() as tx:
        found = tx.get_job(job_id)
    assert found is not None
    return found


def error(fn: Callable[[], object]) -> AiJobError:
    with pytest.raises(AiJobError) as caught:
        fn()
    return caught.value


# ------------------------------------------------------------------ A-03 / A-04
def test_duplicate_semantic_request_yields_one_job_attempt_and_cost(h: FixtureHarness) -> None:
    provider = FakeProvider(lambda m: h.success_claim(m))
    first = h.service.create_job(h.create(key="k1"))
    replay = h.service.create_job(h.create(key="k1"))
    dedup = h.service.create_job(h.create(key="k2"))
    assert replay.replayed and replay.job_id == first.job_id and replay.outcome == "created"
    assert dedup.job_id == first.job_id and dedup.outcome == "deduplicated"
    h.service.dispatch_outbox()
    while h.worker(provider).run_once() is not None:
        pass
    snap = h.store.snapshot()
    assert len(snap.jobs) == 1 and len(snap.jobs[first.job_id].attempts) == 1
    assert dict(provider.calls) == {first.job_id: 1}


def test_same_key_changed_payload_conflicts_and_keeps_original(h: FixtureHarness) -> None:
    first = h.service.create_job(h.create(key="k1"))
    exc = error(lambda: h.service.create_job(h.create(key="k1", ref=request_ref("req_other"))))
    assert (exc.code, exc.http_status) == ("IDEMPOTENCY_PAYLOAD_MISMATCH", 409)
    assert job(h, first.job_id).request_ref == request_ref()
    assert len(h.store.snapshot().jobs) == 1


def test_video_lifecycle_binding_must_match_command_identity(h: FixtureHarness) -> None:
    command = h.create()
    request = command.request_ref
    pin = VideoPin(
        command.principal.organization_id,
        command.session_id or "session_fx_001",
        ExactRef(request.request_id, request.request_revision, request.input_hash),
        0,
        request.context_revision,
        request.context_revision,
        (ExactRef("source_fx_001", 1, "b" * 64),),
        Strategy.GENERATE,
        ExactRef("profile_fx_001", 1, "c" * 64),
        ExactRef("encoding_fx_001", 1, "d" * 64),
        ExactRef("rights_fx_001", 1, "e" * 64),
        ExactRef("retry_fx_001", 1, "f" * 64),
        ExactRef("policy_fx_001", 1, "0" * 64),
        1,
        ExactRef("model_fx_001", 1, "1" * 64),
    )
    binding = VideoLifecycleCreateV1(
        command.job_type,
        VideoRequestContext(
            "different_principal",
            command.principal.organization_id,
            command.session_id or "session_fx_001",
            command.idempotency_key,
            command.correlation_id,
        ),
        "2" * 64,
        pin,
    )

    with pytest.raises(AiJobError, match="VIDEO_IDENTITY_MISMATCH"):
        h.service.create_job(replace(command, video_lifecycle=binding))

    assert not h.store.snapshot().jobs


def test_command_scope_includes_principal_and_organization(h: FixtureHarness) -> None:
    first = h.service.create_job(h.create(key="k1"))
    peer = h.service.create_job(h.create(TEACHER_2, key="k1"))
    assert peer.job_id == first.job_id and not peer.replayed and peer.outcome == "deduplicated"
    foreign = h.service.create_job(h.create(OUTSIDER, key="k1"))
    assert foreign.job_id != first.job_id
    assert job(h, foreign.job_id).organization_id == OUTSIDER.organization_id
    assert error(lambda: h.service.create_job(h.create(UNGRANTED, key="k1"))).code == (
        "FORBIDDEN_SCOPE"
    )
    assert len(h.store.snapshot().command_receipts) == 3


def test_receipt_replay_rechecks_current_read_authority(h: FixtureHarness) -> None:
    created = h.service.create_job(h.create(key="k1"))
    command = CancelJobCommand(TEACHER, "cancel_1", created.job_id, 1)
    h.service.cancel_job(command)
    assert h.service.cancel_job(command).replayed
    h.authorization.revoke(TEACHER.principal_id)
    assert error(lambda: h.service.cancel_job(command)).code == "RESOURCE_NOT_FOUND"


# ------------------------------------------------------------------ A-05 / A-06
def test_queue_redelivery_and_duplicate_completion_have_one_effect(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    cap = h.capability(job_id)
    assert h.last_envelope is not None
    h.queue.redeliver(h.last_envelope)
    redelivered = h.queue.receive()
    assert redelivered is not None and redelivered.message == message
    assert h.service.start_attempt(cap, job_id, message.attempt_id).reason_code == (
        "DUPLICATE_DELIVERY"
    )
    claim = h.success_claim(message)
    first = h.service.accept_completion(cap, claim)
    revision = job(h, job_id).job_revision
    assert h.service.accept_completion(cap, claim) == first
    assert job(h, job_id).job_revision == revision and len(job(h, job_id).attempts) == 1


def test_concurrent_different_completions_have_one_winner(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    cap = h.capability(job_id)
    claims = [h.success_claim(message, body=b"a"), h.success_claim(message, body=b"b")]
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def complete(claim: CompletionClaim) -> None:
        barrier.wait()
        try:
            outcomes.append(str(h.service.accept_completion(cap, claim).disposition))
        except AiJobError as exc:
            outcomes.append(exc.code)

    threads = [threading.Thread(target=complete, args=(c,)) for c in claims]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(outcomes) == ["COMPLETION_CONFLICT", "accepted"]
    assert any(e.event_type == "job.completion_conflict" for e in h.audit.events)
    assert job(h, job_id).state is JobState.SUCCEEDED


def test_fake_cas_and_atomic_commit(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    current = job(h, job_id)
    with pytest.raises(JobRevisionConflict), h.store.transaction() as tx:
        tx.cas_job(expected_revision=current.job_revision + 1, job=current)
    h.store.fail_next_commit = True
    with pytest.raises(RuntimeError):
        h.service.create_job(h.create(key="k2", ref=request_ref("req_2")))
    snap = h.store.snapshot()
    assert set(snap.jobs) == {job_id} and len(snap.command_receipts) == 1
    assert len(snap.outbox) == 1


def test_queue_outage_keeps_job_recoverably_queued(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    h.queue.available = False
    assert h.service.dispatch_outbox() == 0
    assert job(h, job_id).state is JobState.QUEUED and len(h.store.snapshot().outbox) == 1
    h.queue.available = True
    assert h.service.dispatch_outbox() == 1 and not h.store.snapshot().outbox


# ------------------------------------------------------------------ A-07 / A-08
def test_timeouts_retry_with_backoff_until_policy_exhausted(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    for attempt in range(1, FIXTURE_RETRY_POLICY.max_attempts + 1):
        h.start_next()
        h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
        assert h.service.expire_overdue_attempts() == (job_id,)
        if attempt < FIXTURE_RETRY_POLICY.max_attempts:
            assert job(h, job_id).state is JobState.FAILED_RETRYABLE
            assert h.service.run_due_retries() == ()
            h.clock.advance(milliseconds=BACKOFF)
            assert h.service.run_due_retries() == (job_id,)
    final = job(h, job_id)
    assert final.state is JobState.FAILED_EXHAUSTED
    assert len(final.attempts) == FIXTURE_RETRY_POLICY.max_attempts
    assert final.failure is not None and final.failure.code == "PROVIDER_TIMEOUT"
    h.clock.advance(seconds=600)
    assert h.service.run_due_retries() == () and h.service.dispatch_outbox() == 0


def test_progress_reports_keep_unknown_null_and_ignore_stale_attempts(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    cap = h.capability(job_id)
    view = h.service.get_job_status(TEACHER, job_id).view
    assert view is not None and view["progress"] == {
        "kind": "unknown", "value": None, "stage_label": None
    }
    assert h.service.report_progress(cap, job_id, message.attempt_id,
                                     JobProgress(ProgressKind.STAGES, None, "outline"))
    # B5 Δ8: a stale attempt is ignored with its own capability; the active attempt's
    # capability is refused for any other attempt (no job-only fallback).
    assert not h.service.report_progress(h.capability(job_id, "att_old"), job_id, "att_old",
                                         JobProgress(ProgressKind.PERCENTAGE, 99.0))
    with pytest.raises(AiJobError) as denied:
        h.service.report_progress(cap, job_id, "att_old",
                                  JobProgress(ProgressKind.PERCENTAGE, 99.0))
    assert denied.value.code == "WORKER_CAPABILITY_INVALID"
    assert job(h, job_id).progress == JobProgress(ProgressKind.STAGES, None, "outline")


# --------------------------------------------------------------- A-11 / A-12
def test_superseded_attempt_completion_is_stale_and_never_overwrites(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    first = h.start_next()
    cap = h.capability(job_id)
    late = h.success_claim(first)
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    h.service.expire_overdue_attempts()
    h.clock.advance(milliseconds=BACKOFF)
    h.service.run_due_retries()
    second = h.start_next()
    receipt = h.service.accept_completion(cap, late)
    assert receipt.disposition is ResultDisposition.STALE
    assert receipt.reason_code == "ATTEMPT_SUPERSEDED"
    current = job(h, job_id)
    assert current.state is JobState.RUNNING
    assert current.active_attempt.attempt_id == second.attempt_id and current.result_refs == ()
    assert late.outputs[0].artifact_ref in h.artifacts.quarantined


@pytest.mark.parametrize(
    "change",
    [{"input_hash": "0" * 64}, {"expected_request_revision": 9}, {"context_revision": 7}],
)
def test_completion_for_wrong_pinned_input_is_rejected(
    h: FixtureHarness, change: dict[str, object]
) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    claim = replace(h.success_claim(message), **change)  # type: ignore[arg-type]
    receipt = h.service.accept_completion(h.capability(job_id), claim)
    assert receipt.disposition is ResultDisposition.REJECTED
    assert receipt.reason_code == "INPUT_MISMATCH"
    assert job(h, job_id).state is JobState.RUNNING
    assert any(e.event_type == "job.completion_input_mismatch" for e in h.audit.events)


def test_context_change_marks_result_stale_with_lineage(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    h.eligibility.context_revisions["req_fx_001"] = 4
    receipt = h.service.accept_completion(h.capability(job_id), h.success_claim(message))
    current = job(h, job_id)
    assert receipt.reason_code == "STALE_CONTEXT"
    assert current.state is JobState.SUCCEEDED
    assert current.result_disposition is ResultDisposition.STALE
    assert current.request_ref.context_revision == 1
    assert current.lineage_note == "source context 1 superseded by 4"
    view = h.service.get_job_status(TEACHER, job_id).view
    assert view is not None and view["result_refs"] == []


# --------------------------------------------------------------- A-13 / A-14
@pytest.mark.parametrize("state", ["queued", "running", "failed_retryable"])
def test_cancel_blocks_retry_callbacks_and_late_results(h: FixtureHarness, state: str) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = None if state == "queued" else h.start_next()
    if state == "failed_retryable":
        assert message is not None
        h.service.accept_completion(h.capability(job_id), h.failure_claim(message))
    before = job(h, job_id)
    h.service.cancel_job(CancelJobCommand(TEACHER, "c1", job_id, before.job_revision))
    h.clock.advance(milliseconds=BACKOFF)
    assert not h.service.retry_job(job_id, before.active_attempt.attempt_number)
    assert h.service.run_due_retries() == ()
    assert h.service.dispatch_outbox() == 0
    if state == "running":
        assert message is not None
        receipt = h.service.accept_completion(h.capability(job_id), h.success_claim(message))
        assert receipt.reason_code == "JOB_CANCELLED"
    after = job(h, job_id)
    assert after.state is JobState.CANCELLED and len(after.attempts) == len(before.attempts)
    assert after.result_refs == ()


def test_cancel_requires_current_if_match_and_rejects_terminal(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    no_match = error(lambda: h.service.cancel_job(CancelJobCommand(TEACHER, "c0", job_id, None)))
    assert (no_match.code, no_match.http_status) == ("PRECONDITION_REQUIRED", 428)
    stale = error(lambda: h.service.cancel_job(CancelJobCommand(TEACHER, "c1", job_id, 7)))
    assert (stale.code, stale.http_status) == ("STALE_AGGREGATE", 412)
    h.service.cancel_job(CancelJobCommand(TEACHER, "c2", job_id, 1))
    assert error(
        lambda: h.service.cancel_job(CancelJobCommand(TEACHER, "c3", job_id, 2))
    ).code == "INVALID_STATE"
    assert error(
        lambda: h.service.cancel_job(CancelJobCommand(DEVICE, "c4", job_id, 2))
    ).code == "FORBIDDEN_SCOPE"


ELIGIBILITY: dict[str, Callable[[FixtureHarness], None]] = {
    "CONSENT_REVOKED": lambda h: h.eligibility.revoked_subjects.add("child_fx_001"),
    "SESSION_ENDED": lambda h: h.eligibility.ended_sessions.add("session_fx_001"),
    "CONTENT_RECALLED": lambda h: h.eligibility.recalled_requests.add("req_fx_001"),
    "SOURCE_EXPIRED": lambda h: h.eligibility.expired_requests.add("req_fx_001"),
    "KILL_SWITCH": lambda h: h.eligibility.killed_job_types.add("sketch_assistance"),
    "BUDGET_EXCEEDED": lambda h: h.eligibility.budget_exhausted_targets.add("assistance_fx_001"),
}


@pytest.mark.parametrize("reason", sorted(ELIGIBILITY))
def test_current_eligibility_gates_create_start_retry_and_completion(reason: str) -> None:
    h = build_fixture_harness()
    ELIGIBILITY[reason](h)
    create_error = error(lambda: h.service.create_job(h.create()))
    assert create_error.code != "RESOURCE_NOT_FOUND"
    assert not h.store.snapshot().command_receipts

    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    h.service.dispatch_outbox()
    envelope = h.queue.receive()
    assert envelope is not None
    message = envelope.message
    ELIGIBILITY[reason](h)
    started = h.service.start_attempt(h.capability(job_id), job_id, message.attempt_id)
    assert (started.started, started.reason_code) == (False, reason)
    assert job(h, job_id).failure is not None and job(h, job_id).failure.code == reason  # type: ignore[union-attr]

    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    ELIGIBILITY[reason](h)
    receipt = h.service.accept_completion(h.capability(job_id), h.success_claim(message))
    assert receipt.disposition is ResultDisposition.REJECTED and receipt.reason_code == reason
    assert job(h, job_id).state is JobState.CANCELLED and h.artifacts.quarantined

    h = build_fixture_harness()
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    h.service.accept_completion(h.capability(job_id), h.failure_claim(message))
    ELIGIBILITY[reason](h)
    h.clock.advance(milliseconds=BACKOFF)
    assert h.service.run_due_retries() == ()
    assert job(h, job_id).state is JobState.CANCELLED


def test_denied_create_does_not_reserve_key_success(h: FixtureHarness) -> None:
    h.eligibility.revoked_subjects.add("child_fx_001")
    assert error(lambda: h.service.create_job(h.create(key="k1"))).code == "CONSENT_REQUIRED"
    h.eligibility.revoked_subjects.clear()
    assert h.service.create_job(h.create(key="k1")).outcome == "created"


def test_cancellation_notices_are_scoped_and_idempotent(h: FixtureHarness) -> None:
    a = h.service.create_job(h.create(key="k1")).job_id
    b = h.service.create_job(h.create(key="k2", ref=request_ref("req_b"), session_id="s_other",
                                      subjects=("child_fx_009",))).job_id
    foreign = h.service.create_job(h.create(OUTSIDER, key="k1")).job_id
    notice = CancellationNotice("n1", ORG, "SESSION_ENDED", session_id="session_fx_001")
    assert h.service.apply_cancellation_notice(notice) == (a,)
    assert h.service.apply_cancellation_notice(notice) == ()
    assert job(h, b).state is JobState.QUEUED and job(h, foreign).state is JobState.QUEUED
    consent = CancellationNotice("n2", ORG, "CONSENT_REVOKED", subject_ref="child_fx_009")
    assert h.service.apply_cancellation_notice(consent) == (b,)


# --------------------------------------------------------------- A-15 / A-16 / A-17
def test_unsafe_output_is_blocked_and_quarantined(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    claim = h.success_claim(message, moderation=Moderation.UNSAFE)
    receipt = h.service.accept_completion(h.capability(job_id), claim)
    current = job(h, job_id)
    assert current.state is JobState.BLOCKED_UNSAFE and receipt.reason_code == "UNSAFE_CONTENT"
    assert claim.outputs[0].artifact_ref in h.artifacts.quarantined
    assert current.result_refs == ()


@pytest.mark.parametrize("variant", ["no_outputs", "unknown_ref", "hash_mismatch", "foreign_org"])
def test_malformed_output_fails_without_exposure(h: FixtureHarness, variant: str) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    good = h.success_claim(message)
    out = good.outputs[0]
    outputs = {
        "no_outputs": (),
        "unknown_ref": (OutputRef("artifact_missing", out.sha256),),
        "hash_mismatch": (OutputRef(out.artifact_ref, "f" * 64),),
        "foreign_org": (h.artifacts.put(OUTSIDER.organization_id, b"x"),),
    }[variant]
    receipt = h.service.accept_completion(h.capability(job_id), replace(good, outputs=outputs))
    current = job(h, job_id)
    assert receipt.reason_code == "OUTPUT_MALFORMED"
    assert current.state is JobState.FAILED_EXHAUSTED and current.result_refs == ()
    assert current.failure is not None and current.failure.retryable is False


def test_provider_diagnostics_are_redacted(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    secret = "token=sk-fixture-secret url=https://provider.invalid/raw trace=Traceback"
    h.service.accept_completion(
        h.capability(job_id),
        h.failure_claim(message, code="PROVIDER_ERROR", retryable=False, diagnostic=secret),
    )
    rendered = json.dumps(
        [h.service.get_job_status(TEACHER, job_id).view, [asdict(e) for e in h.audit.events]],
        default=str,
    )
    for fragment in ("sk-fixture-secret", "provider.invalid", "Traceback"):
        assert fragment not in rendered
    assert "diagnostic_sha256" in rendered


def test_success_exposes_exact_refs_to_teacher_only(h: FixtureHarness) -> None:
    job_id = h.service.create_job(h.create()).job_id
    message = h.start_next()
    claim = h.success_claim(message)
    h.service.accept_completion(h.capability(job_id), claim)
    teacher = h.service.get_job_status(TEACHER, job_id).view
    device = h.service.get_job_status(DEVICE, job_id).view
    assert teacher is not None and device is not None
    assert teacher["result_refs"] == [
        {"artifact_ref": claim.outputs[0].artifact_ref, "sha256": claim.outputs[0].sha256}
    ]
    assert teacher["result_disposition"] == "accepted"
    assert set(device) == {"job_id", "job_type", "job_revision", "state", "progress", "failure",
                           "poll_after_ms"}
    assert not {"approved", "review_state", "playback_state"} & set(teacher)


@pytest.mark.parametrize("capability", ["", "wcap_fx_forged", "other_job"])
def test_worker_ports_require_job_scoped_capability(h: FixtureHarness, capability: str) -> None:
    job_id = h.service.create_job(h.create()).job_id
    other = h.service.create_job(h.create(key="k2", ref=request_ref("req_2"))).job_id
    message = h.start_next()
    token = h.capability(other) if capability == "other_job" else capability
    for call in (
        lambda: h.service.accept_completion(token, h.success_claim(message)),
        lambda: h.service.start_attempt(token, job_id, message.attempt_id),
    ):
        assert error(call).code == "WORKER_CAPABILITY_INVALID"


# --------------------------------------------------------------------- A-18
def test_provider_copy_lifecycle_fake_is_scoped_idempotent_and_truthful(
    h: FixtureHarness,
) -> None:
    scope = "job_fx_scope"
    for index, profile in enumerate(["fixture-deletes", "fixture-pending",
                                     "fixture-unsupported", "fixture-exception"]):
        h.copy_service.register_copy(ProviderCopy(f"c{index}", ORG, scope, CopyKind.CACHE,
                                                  profile))
    h.copy_service.register_copy(ProviderCopy("x", "org_other", scope, CopyKind.CACHE,
                                              "fixture-deletes"))
    cancelled = h.copy_service.cancel_scope(ORG, scope)
    assert {o.status for o in cancelled} == {"cancel_requested"}
    first = h.copy_service.purge_scope(ORG, scope, "p1")
    assert h.copy_service.purge_scope(ORG, scope, "p1") == first
    assert len(h.copy_adapter.purge_requests) == 4
    labels = [o.report_label for o in first]
    assert labels == ["fixture_deleted_not_actual", "pending", "unsupported", "exception"]
    assert not any(o.actual_deletion_proven for o in first)
    retry = h.copy_service.purge_scope(ORG, scope, "p2")
    assert [o.report_label for o in retry][0] == "fixture_deleted_not_actual"
    assert len(h.copy_adapter.purge_requests) == 7
    late = h.copy_service.register_copy(ProviderCopy("late", ORG, scope, CopyKind.OUTPUT,
                                                     "fixture-deletes"))
    assert late.status is CopyStatus.PURGE_REQUESTED
    other = h.copy_service.discover("org_other", scope)
    assert [o.status for o in other] == ["discovered"]
