"""BE2-03 A1 controlled races at the coordinated commit boundary (plan rev3 §8.2, §11).

Every interleaving respects the shared fake coordinator: a hook inside a coordinated BE2-01
transaction can only *request* an assistance publication, which runs after that transaction
exits; expected orders are named by the actual commit order. Fake-level evidence only."""

from __future__ import annotations

import threading
from collections.abc import Callable

import pytest

from sketch2life.application.ports.assistance import ReceiptOutcome
from sketch2life.application.services.assistance import (
    AssistanceError,
    CommandResult,
    NoticeKind,
    OwnerNotice,
)
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.assistance import RequestStatus, ReservationState, Settlement, StatusReason
from sketch2life.infrastructure.assistance.adapters import SimulatedLostReply
from sketch2life.infrastructure.assistance.fakes import CoordinationError, fixture_policy
from sketch2life.infrastructure.assistance.harness import (
    CANVAS_P,
    DEVICE_A,
    ORG,
    TEACHER,
    AssistanceHarness,
    build_assistance_harness,
)


def jobs(h: AssistanceHarness) -> dict[str, object]:
    return dict(h.job_store.snapshot().jobs)


def nested_during_resolution(h: AssistanceHarness, inner: Callable[[], object]) -> None:
    """Run ``inner`` once, between the outer submit's resolution and its commit."""

    real = h.owner.canvas
    fired: list[bool] = []

    def canvas(organization_id: str, canvas_id: str) -> object:
        facts = real(organization_id, canvas_id)
        if not fired:
            fired.append(True)
            inner()
        return facts

    h.owner.canvas = canvas  # type: ignore[assignment, method-assign]


# ---------------------------------------------------------------- submit races
def test_r01_identical_submissions_with_different_keys_make_one_request() -> None:
    h = build_assistance_harness()
    inner: list[CommandResult] = []
    nested_during_resolution(h, lambda: inner.append(h.submit(h.command())))
    outer = h.submit(h.command())
    assert inner[0].outcome is ReceiptOutcome.CREATED
    assert outer.outcome is ReceiptOutcome.DEDUPLICATED
    assert outer.request.assistance_id == inner[0].request.assistance_id
    assert len(jobs(h)) == 1


def test_r01_threads_identical_submissions() -> None:
    h = build_assistance_harness()
    commands = [h.command(), h.command()]
    barrier = threading.Barrier(2)
    results: list[CommandResult] = []

    def run(index: int) -> None:
        barrier.wait()
        results.append(h.submit(commands[index]))

    threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(str(r.outcome) for r in results) == ["created", "deduplicated"]
    assert len({r.request.assistance_id for r in results}) == 1
    assert len(jobs(h)) == 1


def test_r02_same_key_concurrent_submissions_commit_once() -> None:
    h = build_assistance_harness()
    command = h.command()
    inner: list[CommandResult] = []
    nested_during_resolution(h, lambda: inner.append(h.submit(command)))
    outer = h.submit(command)
    assert not inner[0].replayed and outer.replayed
    assert outer.request == inner[0].request
    assert len(jobs(h)) == 1


def test_r05_last_budget_unit_raced_by_two_targets() -> None:
    h = build_assistance_harness()
    h.policy.snapshot = fixture_policy(per_session_limit=1)
    inner: list[CommandResult] = []
    nested_during_resolution(h, lambda: inner.append(h.submit(h.group_command())))
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command())
    assert exc.value.code == "BUDGET_EXCEEDED"
    assert inner[0].outcome is ReceiptOutcome.CREATED
    assert len(jobs(h)) == 1


# ------------------------------------------------------------- scheduling races
def test_r08a_lost_create_reply_then_resend_links_the_same_job() -> None:
    h = build_assistance_harness(auto_schedule=False)
    request = h.submit().request
    h.job_port.lose_next_reply = True
    with pytest.raises(SimulatedLostReply):
        h.service.schedule(request.assistance_id)
    assert h.request(request.assistance_id).status is RequestStatus.SCHEDULING
    assert len(jobs(h)) == 1  # BE2-01 committed before the reply was lost
    linked = h.service.schedule(request.assistance_id)
    assert linked is not None and linked.status is RequestStatus.SCHEDULED
    assert linked.job_id == next(iter(jobs(h)))
    assert h.job_port.creates == 2 and len(jobs(h)) == 1


def test_r08b_broker_down_after_link_stays_scheduled_and_recovers() -> None:
    h = build_assistance_harness()
    request = h.request(h.submit().request.assistance_id)
    assert request.status is RequestStatus.SCHEDULED
    h.queue.available = False
    assert h.dispatch() == 0
    assert h.request(request.assistance_id).status is RequestStatus.SCHEDULED
    assert h.job(request.job_id).state is JobState.QUEUED  # type: ignore[attr-defined, arg-type]
    assert h.request(request.assistance_id).reservation is ReservationState.HELD
    h.queue.available = True
    h.clock.advance(seconds=11)  # released lease becomes claimable again
    assert h.dispatch() == 1
    assert len(h.queue.messages) == 1 and len(jobs(h)) == 1


def test_r09_cancel_before_create_commit() -> None:
    h = build_assistance_harness(auto_schedule=False)
    request = h.submit().request
    h.service.cancel(h.cancel_command(DEVICE_A, request.assistance_id))
    final = h.service.schedule(request.assistance_id)
    assert final is not None and final.status is RequestStatus.CANCELLED
    assert jobs(h) == {}
    assert final.settlement is Settlement.SETTLED
    assert final.reservation is ReservationState.RELEASED


@pytest.mark.parametrize("explicit_cleanup", [True, False])
def test_r10_cancel_after_create_commit_before_link(explicit_cleanup: bool) -> None:
    h = build_assistance_harness(auto_schedule=False)
    request = h.submit().request
    cancel = h.cancel_command(DEVICE_A, request.assistance_id)
    real = h.job_port.create

    def create(job_request: object) -> object:
        outcome = real(job_request)  # type: ignore[arg-type]
        if not explicit_cleanup:  # isolate the fenced-eligibility path
            h.job_authorization.revoke(DEVICE_A.principal_id)
        h.service.cancel(cancel)  # commits after BE2-01 commit, before the link
        return outcome

    h.job_port.create = create  # type: ignore[assignment, method-assign]
    after = h.service.schedule(request.assistance_id)
    assert after is not None and after.status is RequestStatus.CANCELLED
    assert after.job_id is None and len(after.cleanup_job_ids) == 1
    (job_id,) = after.cleanup_job_ids
    if not explicit_cleanup:
        assert h.job(job_id).state is JobState.QUEUED  # type: ignore[attr-defined]
        assert after.settlement is Settlement.OPEN
        assert after.reservation is ReservationState.HELD
        assert h.dispatch() == 0  # eligibility denies dispatch and cancels the job
    assert h.job(job_id).state is JobState.CANCELLED  # type: ignore[attr-defined]
    final = h.service.reconcile(request.assistance_id)
    assert final is not None and final.status is RequestStatus.CANCELLED  # never re-scheduled
    assert final.settlement is Settlement.SETTLED
    assert final.reservation is ReservationState.RELEASED
    assert h.queue.messages == []


@pytest.mark.parametrize("window", ["before_create", "after_create_before_link"])
def test_r11_stale_in_both_windows(window: str) -> None:
    h = build_assistance_harness(auto_schedule=False)
    request = h.submit().request
    notice = OwnerNotice(f"notice_{window}", ORG, NoticeKind.CANVAS_RESTORED,
                         canvas_id=CANVAS_P)
    if window == "before_create":
        h.service.apply_owner_notice(notice)
    else:
        real = h.job_port.create

        def create(job_request: object) -> object:
            outcome = real(job_request)  # type: ignore[arg-type]
            h.service.apply_owner_notice(notice)
            return outcome

        h.job_port.create = create  # type: ignore[assignment, method-assign]
    h.service.schedule(request.assistance_id)
    h.dispatch()
    final = h.service.reconcile(request.assistance_id)
    assert final is not None and final.status is RequestStatus.STALE
    assert final.status_reason is StatusReason.CANVAS_RESTORED
    assert final.settlement is Settlement.SETTLED
    assert final.reservation is ReservationState.RELEASED
    assert all(job.state is JobState.CANCELLED for job in jobs(h).values())  # type: ignore[attr-defined]


def test_r14_lost_reply_then_requester_revoked_finds_job_by_target() -> None:
    h = build_assistance_harness(auto_schedule=False)
    request = h.submit().request
    h.job_port.lose_next_reply = True
    with pytest.raises(SimulatedLostReply):
        h.service.schedule(request.assistance_id)
    h.job_authorization.revoke(DEVICE_A.principal_id)
    after = h.service.schedule(request.assistance_id)
    assert after is not None and after.status is RequestStatus.STALE
    assert after.status_reason is StatusReason.SCHEDULE_REFUSED
    assert after.settlement is Settlement.OPEN  # the unlinked job was found by target scan
    assert len(jobs(h)) == 1
    assert h.dispatch() == 0
    final = h.service.reconcile(request.assistance_id)
    assert final is not None and final.settlement is Settlement.SETTLED
    assert final.reservation is ReservationState.RELEASED
    assert len(jobs(h)) == 1


# ------------------------------------------------ post-hold / pre-commit seam (F1)
def test_r15a_cancel_first_makes_start_re_decide_and_refuse() -> None:
    h = build_assistance_harness()
    request = h.submit().request
    h.dispatch()
    cancel = h.cancel_command(DEVICE_A, request.assistance_id)
    h.job_authorization.revoke(DEVICE_A.principal_id)  # no explicit job cancel: fence only
    h.eligibility.after_decision = lambda: h.service.cancel(cancel)
    decisions, stale_holds = h.eligibility.decisions, sum(not r.current for r in h.fences.holds)
    result, job_id, _ = h.start_next()
    assert not result.started and result.reason_code == "CANCELLED_BY_CHILD"
    assert h.eligibility.decisions - decisions == 2  # first decision, then re-decision
    assert sum(not r.current for r in h.fences.holds) - stale_holds == 1
    job = h.job(job_id)
    assert job.state is JobState.CANCELLED  # type: ignore[attr-defined]
    assert all(a.started_at is None for a in job.attempts)  # type: ignore[attr-defined]
    assert h.vision_provider.requests == []
    final = h.service.reconcile(request.assistance_id)
    assert final is not None and final.reservation is ReservationState.RELEASED
    assert final.settlement is Settlement.SETTLED


def test_r15b_start_first_defers_same_thread_cancel_until_commit() -> None:
    h = build_assistance_harness()
    request = h.submit().request
    h.dispatch()
    cancel = h.cancel_command(DEVICE_A, request.assistance_id)
    ran_immediately: list[bool] = []

    def hook() -> None:
        assert h.coordinator.in_foundation()
        # Publishing here directly would break the atomic unit; it is refused loudly.
        with pytest.raises(CoordinationError):
            h.service.cancel(cancel)
        ran_immediately.append(
            h.coordinator.request_publication(lambda: h.service.cancel(cancel)))

    h.fences.after_successful_hold = hook
    log_start = len(h.coordinator.commit_log)
    result, job_id, _ = h.start_next()
    assert result.started  # the start transaction committed first
    assert ran_immediately == [False]
    assert h.coordinator.deferred_failures == []
    # Commit order: the foundation start commits before the assistance cancel publication.
    order = h.coordinator.commit_log[log_start:]
    assert order.index("foundation") < order.index("assistance")
    final = h.request(request.assistance_id)
    assert final.status is RequestStatus.CANCELLED
    assert final.reservation is ReservationState.CONSUMED
    job = h.job(job_id)
    assert any(a.started_at is not None for a in job.attempts)  # type: ignore[attr-defined]
    assert final.handoff is None


def test_r15b_other_thread_cancel_blocks_until_start_commits() -> None:
    h = build_assistance_harness()
    request = h.submit().request
    h.dispatch()
    cancel = h.cancel_command(TEACHER, request.assistance_id)
    in_hold, done = threading.Event(), threading.Event()
    outcome: list[str] = []

    def other() -> None:
        in_hold.wait()
        h.service.cancel(cancel)
        outcome.append("cancel_committed")
        done.set()

    def hook() -> None:
        in_hold.set()
        assert not done.wait(timeout=0.2)  # blocked on the coordinator
        outcome.append("start_still_open")

    thread = threading.Thread(target=other)
    thread.start()
    h.fences.after_successful_hold = hook
    result, _, _ = h.start_next()
    thread.join(timeout=5)
    assert result.started
    assert outcome == ["start_still_open", "cancel_committed"]
    assert h.request(request.assistance_id).reservation is ReservationState.CONSUMED


def test_r16_failures_publish_nothing_and_release_the_coordinator() -> None:
    h = build_assistance_harness()
    request = h.submit().request
    h.dispatch()
    cancel = h.cancel_command(DEVICE_A, request.assistance_id)
    epoch = h.fences.epochs[f"eligibility:{ORG}"]

    # Foundation commit failure with a deferred cancel pending.
    def hook() -> None:
        h.job_store.fail_next_commit = True
        h.coordinator.request_publication(lambda: h.service.cancel(cancel))

    h.fences.after_successful_hold = hook
    envelope = h.queue.receive()
    assert envelope is not None
    with pytest.raises(RuntimeError, match="injected commit failure"):
        h.jobs.start_attempt(envelope.capability, envelope.message.job_id,
                             envelope.message.attempt_id)
    job = h.job(envelope.message.job_id)
    # The failed start published nothing: no attempt ever started. The deferred cancel then
    # committed on its own and its explicit cleanup cancelled the still-queued job.
    assert all(a.started_at is None for a in job.attempts)  # type: ignore[attr-defined]
    assert job.state is JobState.CANCELLED  # type: ignore[attr-defined]
    final = h.request(request.assistance_id)
    assert final.status is RequestStatus.CANCELLED
    assert final.reservation is ReservationState.RELEASED
    assert h.fences.epochs[f"eligibility:{ORG}"] == epoch + 1

    # Assistance commit failure: neither state nor epoch is published.
    second = build_assistance_harness()
    pending = second.submit().request
    before = second.fences.epochs[f"eligibility:{ORG}"]
    second.store.fail_next_commit = True
    with pytest.raises(RuntimeError, match="injected assistance commit failure"):
        second.service.cancel(second.cancel_command(TEACHER, pending.assistance_id))
    assert second.request(pending.assistance_id).status is RequestStatus.SCHEDULED
    assert second.fences.epochs[f"eligibility:{ORG}"] == before
    # The coordinator is free: both units can run again immediately.
    second.service.cancel(second.cancel_command(TEACHER, pending.assistance_id))
    assert second.request(pending.assistance_id).status is RequestStatus.CANCELLED


def test_r16_failed_deferred_publication_is_recorded_not_raised() -> None:
    h = build_assistance_harness()
    h.submit()
    h.dispatch()

    def boom() -> None:
        raise ValueError("deferred failure")

    h.fences.after_successful_hold = lambda: h.coordinator.request_publication(boom)
    result, _, _ = h.start_next()
    assert result.started
    assert [str(e) for e in h.coordinator.deferred_failures] == ["deferred failure"]


def test_foundation_call_inside_assistance_transaction_is_refused() -> None:
    h = build_assistance_harness()
    with h.store.transaction(), pytest.raises(CoordinationError), \
            h.job_repository.transaction():
        pass  # pragma: no cover - never entered
    # The read-only job reader surfaces the violation instead of reporting unknown evidence.
    with h.store.transaction(), pytest.raises(CoordinationError):
        h.reader.evidence(ORG, "assist_x", ())
