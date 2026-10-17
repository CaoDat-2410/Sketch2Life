"""BE2-03 A1 chain: real BE2-01 + BE2-02 + BE2-03 services over fakes (P05, P07–P09, N14,
N15, N17, R03a/R03b, R04, R06, R07, R12, R13 and unknown evidence)."""

from __future__ import annotations

import pytest

from sketch2life.application.ports.assistance import ReceiptOutcome
from sketch2life.application.services.assistance import (
    AssistanceError,
    NoticeKind,
    OwnerNotice,
    device_view,
)
from sketch2life.application.services.vision_analysis import VisionAnalysisError
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.assistance import RequestStatus, ReservationState, Settlement, StatusReason
from sketch2life.domain.vision_analysis import (
    LineageVerdict,
    ObservationClaim,
    check_input_hash,
    check_lineage,
    job_scope_matches,
)
from sketch2life.infrastructure.assistance.fakes import fixture_policy
from sketch2life.infrastructure.assistance.harness import (
    CANVAS_P,
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    ORG,
    SESSION,
    TEACHER,
    AssistanceHarness,
    build_assistance_harness,
)
from sketch2life.infrastructure.vision_analysis.job_lineage import AiJobRepositoryLineage


@pytest.fixture
def h() -> AssistanceHarness:
    return build_assistance_harness()


def started(h: AssistanceHarness) -> tuple[str, str]:
    h.dispatch()
    result, job_id, attempt_id = h.start_next()
    assert result.started, result.reason_code
    return job_id, attempt_id


def intents(h: AssistanceHarness) -> int:
    return len(h.sketch.intents)


def test_p05_teacher_cancel_of_queued_never_started_job_releases(h: AssistanceHarness) -> None:
    request = h.submit().request
    result = h.service.cancel(h.cancel_command(TEACHER, request.assistance_id))
    assert result.request.status_reason is StatusReason.CANCELLED_BY_TEACHER
    final = h.request(request.assistance_id)
    assert h.job(final.job_id).state is JobState.CANCELLED  # type: ignore[attr-defined, arg-type]
    assert final.settlement is Settlement.SETTLED
    assert final.reservation is ReservationState.RELEASED
    assert h.dispatch() == 0 and h.queue.messages == []


def test_p07_success_hands_off_once_with_simulated_sketch_intent(h: AssistanceHarness) -> None:
    request = h.submit().request
    final = h.run_vision(request.assistance_id)
    assert final.status is RequestStatus.ANALYSIS_READY
    assert final.reservation is ReservationState.CONSUMED
    assert final.settlement is Settlement.SETTLED
    assert final.handoff is not None and final.handoff.job_id == final.job_id
    (intent,) = h.sketch.intents
    assert intent.status == "SIMULATED_NO_PRODUCER"
    assert intent.analysis_id == final.handoff.analysis_id
    events = [e.event_type for e in h.store.snapshot().events]
    assert events.count("assistance.analysis_ready") == 1
    assert events.count("assistance.sketch_intent_simulated") == 1
    # analysis_ready is not Child availability: the device sees only "pending" and cannot
    # read the analysis through the Teacher-only Vision read.
    assert device_view(final, 2000)["status"] == "pending"
    with pytest.raises(VisionAnalysisError):
        h.vision.downstream_meaning(DEVICE_A, final.handoff.analysis_id)
    # Reconciling again is idempotent.
    assert h.service.reconcile(request.assistance_id) == final
    assert intents(h) == 1


def test_p08_cache_hit_uses_current_reads_and_keeps_original_provenance(
    h: AssistanceHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = h.run_vision(h.submit().request.assistance_id)
    calls: list[object] = []
    real = h.vision.record_observation

    def counted(*args: object, **kwargs: object) -> object:
        calls.append(args)
        return real(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(h.vision, "record_observation", counted)
    jobs_before = len(h.job_store.snapshot().jobs)
    hit = h.submit()  # same semantics, new key; within the debounce window
    assert hit.outcome is ReceiptOutcome.CACHE_HIT
    request = h.request(hit.request.assistance_id)
    assert request.status is RequestStatus.ANALYSIS_READY
    assert request.reservation is None and request.job_id is None
    assert request.cache_hit_of is not None and original.handoff is not None
    assert request.cache_hit_of.assistance_id == original.assistance_id
    assert request.cache_hit_of.job_id == original.job_id
    assert request.cache_hit_of.analysis_id == original.handoff.analysis_id
    assert calls == []  # never worker replay on a terminal job
    assert len(h.job_store.snapshot().jobs) == jobs_before
    # The cached analysis still belongs to its original request/job.
    record = h.vision.analysis_record(TEACHER, original.handoff.analysis_id)
    assert record["candidate"]["assistance_id"] == original.assistance_id  # type: ignore[index]


def test_p09_pin_matches_c1_lineage_scope_and_input_hash(h: AssistanceHarness) -> None:
    request = h.request(h.submit().request.assistance_id)
    job_id, attempt_id = started(h)
    pin = h.service.pin(request.assistance_id)
    job = AiJobRepositoryLineage(h.job_repository).get(job_id)
    assert pin is not None and job is not None
    claim = ObservationClaim(job_id, attempt_id, pin.assistance_id, pin.request_revision,
                             pin.input_snapshot_ref, pin.context_revision)
    assert check_lineage(claim, pin, job) is LineageVerdict.PROCEED
    assert job_scope_matches(job, pin)
    assert check_input_hash(job, h.source_p.snapshot) is LineageVerdict.PROCEED


def test_n14_cancel_after_handoff_is_invalid_state(h: AssistanceHarness) -> None:
    final = h.run_vision(h.submit().request.assistance_id)
    with pytest.raises(AssistanceError) as exc:
        h.service.cancel(h.cancel_command(TEACHER, final.assistance_id))
    assert exc.value.code == "INVALID_STATE"


def test_n15_consent_revoked_after_scheduling(h: AssistanceHarness) -> None:
    request = h.submit().request
    h.revoke_consent(CHILD_A)
    assert h.service.apply_owner_notice(OwnerNotice("notice_fx_1", ORG,
                                                    NoticeKind.CONSENT_REVOKED,
                                                    participant_id=CHILD_A)) == (
        request.assistance_id,)
    assert h.service.apply_owner_notice(OwnerNotice("notice_fx_1", ORG,
                                                    NoticeKind.CONSENT_REVOKED,
                                                    participant_id=CHILD_A)) == ()
    assert h.dispatch() == 0  # denied by the request-aware eligibility; job cancelled
    final = h.service.reconcile(request.assistance_id)
    assert final is not None and final.status is RequestStatus.STALE
    assert final.status_reason is StatusReason.CONSENT_REVOKED
    assert final.reservation is ReservationState.RELEASED
    assert intents(h) == 0


@pytest.mark.parametrize("change", ["context_revision", "vision_meaning", "policy_version"])
def test_n17_cache_is_never_reused_after_facts_or_meaning_move(
    h: AssistanceHarness, change: str
) -> None:
    original = h.run_vision(h.submit().request.assistance_id)
    if change == "context_revision":
        canvas = h.owner.canvases[CANVAS_P]
        from dataclasses import replace

        h.owner.canvases[CANVAS_P] = replace(canvas, context_revision=4)
        h.vision_context.bump(SESSION, CANVAS_P)
        command = h.command(context=4)
    elif change == "vision_meaning":
        h.vision_context.bump(SESSION, CANVAS_P)  # BE2-02 applicability moves only
        command = h.command()
    else:
        h.policy.snapshot = fixture_policy(version="2")
        command = h.command()
    h.clock.advance(seconds=6)
    result = h.submit(command)
    assert result.outcome is ReceiptOutcome.CREATED
    assert h.request(result.request.assistance_id).job_id not in {None, original.job_id}


def test_r03a_cancel_before_handoff_after_observation_accepted(h: AssistanceHarness) -> None:
    request = h.submit().request
    job_id, attempt_id = started(h)
    h.finish_vision(job_id, attempt_id)  # BE2-02 accepted + BE2-01 succeeded
    assert h.job(job_id).state is JobState.SUCCEEDED  # type: ignore[attr-defined]
    h.service.cancel(h.cancel_command(TEACHER, request.assistance_id))
    final = h.service.reconcile(request.assistance_id)
    assert final is not None and final.status is RequestStatus.CANCELLED
    assert final.handoff is None and intents(h) == 0
    assert final.reservation is ReservationState.CONSUMED
    assert final.settlement is Settlement.SETTLED
    assert len(h.vision_store.snapshot().heads) == 1  # BE2-02 history retained


def test_r03b_handoff_before_cancel(h: AssistanceHarness) -> None:
    final = h.run_vision(h.submit().request.assistance_id)
    with pytest.raises(AssistanceError):
        h.service.cancel(h.cancel_command(TEACHER, final.assistance_id))
    assert h.request(final.assistance_id).status is RequestStatus.ANALYSIS_READY
    assert intents(h) == 1


@pytest.mark.parametrize("where", ["be2_03_owner_fact", "be2_02_context"])
def test_r04_context_moves_between_scheduling_and_completion(
    h: AssistanceHarness, where: str
) -> None:
    request = h.submit().request
    job_id, attempt_id = started(h)
    if where == "be2_03_owner_fact":
        h.owner.update_member(CHILD_A, age_revision=2)
    else:
        h.vision_context.bump(SESSION, CANVAS_P)
    h.finish_vision(job_id, attempt_id)
    final = h.service.reconcile(request.assistance_id)
    assert final is not None and final.status in {RequestStatus.STALE, RequestStatus.FAILED}
    if where == "be2_03_owner_fact":
        assert final.status_reason is StatusReason.CONTEXT_CHANGED
    assert final.handoff is None and intents(h) == 0
    assert final.reservation is ReservationState.CONSUMED


def test_r06_start_then_cancel_consumes(h: AssistanceHarness) -> None:
    request = h.submit().request
    job_id, _ = started(h)
    h.service.cancel(h.cancel_command(DEVICE_A, request.assistance_id))
    final = h.request(request.assistance_id)
    assert final.status is RequestStatus.CANCELLED
    assert final.reservation is ReservationState.CONSUMED
    assert h.job(job_id).state is JobState.CANCELLED  # type: ignore[attr-defined]


def test_r07_completion_after_stale_does_not_resurrect(h: AssistanceHarness) -> None:
    request = h.submit().request
    job_id, attempt_id = started(h)
    h.service.apply_owner_notice(OwnerNotice("notice_fx_2", ORG, NoticeKind.SESSION_ENDED,
                                             session_id=SESSION))
    h.finish_vision(job_id, attempt_id)
    final = h.service.reconcile(request.assistance_id)
    assert final is not None and final.status is RequestStatus.STALE
    assert final.handoff is None and intents(h) == 0
    assert final.reservation is ReservationState.CONSUMED
    assert final.settlement is Settlement.SETTLED


def test_r12_started_attempt_then_retry_queued_then_cancel_stays_consumed(
    h: AssistanceHarness,
) -> None:
    request = h.submit().request
    job_id, attempt_id = started(h)
    h.finish_vision(job_id, attempt_id, fail_retryable=True)
    h.service.reconcile(request.assistance_id)
    assert h.request(request.assistance_id).reservation is ReservationState.CONSUMED
    h.clock.advance(seconds=10)
    h.jobs.run_due_retries()
    job = h.job(job_id)
    assert job.state is JobState.QUEUED  # type: ignore[attr-defined]
    assert job.active_attempt.started_at is None  # type: ignore[attr-defined]
    assert len(job.attempts) == 2  # type: ignore[attr-defined]
    h.service.cancel(h.cancel_command(TEACHER, request.assistance_id))
    final = h.request(request.assistance_id)
    assert final.reservation is ReservationState.CONSUMED  # never refunded
    assert final.settlement is Settlement.SETTLED


def test_r13_dispatch_lost_never_started_retry_then_cancel_releases(
    h: AssistanceHarness,
) -> None:
    request = h.submit().request
    outcomes: list[tuple[str, str]] = []
    for _ in range(4):
        h.dispatch()
        h.queue.messages.clear()  # delivered but never started
        h.clock.advance(seconds=6)
        outcomes.extend(h.jobs.recover_unstarted_dispatches())
    assert any(outcome == "dispatch_lost" for _, outcome in outcomes)
    h.clock.advance(seconds=10)
    h.jobs.run_due_retries()
    job = h.job(h.request(request.assistance_id).job_id)  # type: ignore[arg-type]
    assert job.state is JobState.QUEUED and len(job.attempts) == 2  # type: ignore[attr-defined]
    assert all(a.started_at is None for a in job.attempts)  # type: ignore[attr-defined]
    h.service.reconcile(request.assistance_id)
    assert h.request(request.assistance_id).reservation is ReservationState.HELD
    h.service.cancel(h.cancel_command(TEACHER, request.assistance_id))
    final = h.request(request.assistance_id)
    assert final.reservation is ReservationState.RELEASED
    assert final.settlement is Settlement.SETTLED


def test_unknown_evidence_keeps_an_unconsumed_hold(h: AssistanceHarness) -> None:
    request = h.submit().request
    h.service.cancel(h.cancel_command(TEACHER, request.assistance_id))
    # Force a fresh, open, cancelled request whose history is unreadable.
    other = h.submit(h.group_command()).request
    h.service.apply_owner_notice(OwnerNotice("notice_fx_3", ORG, NoticeKind.CONSENT_REVOKED,
                                             participant_id=CHILD_B))
    h.reader.fail_next = True
    current = h.request(other.assistance_id)
    assert h.service.reconcile(other.assistance_id) == current
    assert current.reservation is ReservationState.HELD
    assert current.settlement is Settlement.OPEN
