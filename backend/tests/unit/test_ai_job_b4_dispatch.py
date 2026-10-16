"""BE2-01 Phase B batch B4 offline checks: Δ13 domain transition and fake parity for the
fenced dispatcher, same-attempt recovery and targeted sweeps (Δ6/Δ7/Δ11/Δ14).

Fakes only: these are not broker or PostgreSQL evidence (see tests/integration/ai_jobs).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sketch2life.application.ports.ai_jobs import AttemptDispatch, OutboxLease
from sketch2life.application.services.ai_jobs import (
    FIXTURE_DISPATCH_POLICY,
    FIXTURE_RETRY_POLICY,
)
from sketch2life.domain.ai_jobs import model as jobs
from sketch2life.domain.ai_jobs.model import InvalidJobTransition, JobScope, JobState
from sketch2life.infrastructure.ai_jobs.harness import (
    FixtureHarness,
    build_fixture_harness,
    request_ref,
)

NOW = datetime(2026, 10, 15, 9, 0, tzinfo=UTC)
START_TIMEOUT_MS = FIXTURE_DISPATCH_POLICY.start_timeout_ms
LEASE_MS = FIXTURE_DISPATCH_POLICY.lease_ms


def _queued(attempt_number: int = 1) -> jobs.AiJob:
    job = jobs.create_job(
        job_id="job_b4",
        attempt_id="att_1",
        job_type="sketch_assistance",
        scope=JobScope("org", None, ("s",), "p", "t"),
        request_ref=request_ref(),
        correlation_id="corr",
        retry_policy=FIXTURE_RETRY_POLICY,
        now=NOW,
    )
    for number in range(2, attempt_number + 1):
        started = jobs.start_attempt(job, job.active_attempt.attempt_id, NOW)
        failed = jobs.record_failure(
            started,
            started.active_attempt.attempt_id,
            code="PROVIDER_ERROR",
            retryable=True,
            public_message="x",
            now=NOW,
        )
        job = jobs.requeue_for_retry(
            failed, new_attempt_id=f"att_{number}", now=failed.retry_not_before or NOW
        )
    return job


@pytest.fixture
def h() -> FixtureHarness:
    return build_fixture_harness()


# ------------------------------------------------------------------------------ Δ13 domain
def test_dispatch_loss_with_budget_schedules_existing_backoff_without_inventing_a_start() -> None:
    job = _queued()
    lost = jobs.record_dispatch_loss(job, "att_1", public_message="late", now=NOW)
    attempt = lost.active_attempt
    assert lost.state is JobState.FAILED_RETRYABLE
    assert lost.failure == jobs.JobFailure(
        "DISPATCH_LOST", True, "late", FIXTURE_RETRY_POLICY.attempts_remaining(1)
    )
    assert lost.retry_not_before == NOW + FIXTURE_RETRY_POLICY.backoff_after(1)
    assert attempt.started_at is None and attempt.finished_at == NOW
    assert attempt.outcome == "dispatch_lost" and attempt.request_ref == job.request_ref
    assert lost.job_revision == job.job_revision + 1 and lost.history[-1] == "dispatch_lost"
    assert lost.completed_at is None and len(lost.attempts) == 1


def test_dispatch_loss_on_final_attempt_is_exhausted_and_never_scheduled() -> None:
    job = _queued(FIXTURE_RETRY_POLICY.max_attempts)
    lost = jobs.record_dispatch_loss(
        job, job.active_attempt.attempt_id, public_message="x", now=NOW
    )
    assert lost.state is JobState.FAILED_EXHAUSTED and lost.retry_not_before is None
    assert lost.completed_at == NOW and lost.failure is not None
    assert (lost.failure.retryable, lost.failure.attempts_remaining) == (False, 0)


def test_dispatch_loss_guards_and_record_failure_stays_running_only() -> None:
    job = _queued()
    with pytest.raises(InvalidJobTransition):
        jobs.record_dispatch_loss(job, "att_other", public_message="x", now=NOW)
    running = jobs.start_attempt(job, "att_1", NOW)
    with pytest.raises(InvalidJobTransition):
        jobs.record_dispatch_loss(running, "att_1", public_message="x", now=NOW)
    with pytest.raises(InvalidJobTransition):
        jobs.record_failure(
            job, "att_1", code="PROVIDER_ERROR", retryable=True, public_message="x", now=NOW
        )


# --------------------------------------------------------------------------- Δ6/Δ14 dispatch
def test_dispatch_carries_a_fresh_attempt_capability_only_in_the_envelope(
    h: FixtureHarness,
) -> None:
    created = h.service.create_job(h.create())
    assert h.service.dispatch_outbox() == 1
    envelope = h.queue.receive()
    assert envelope is not None and envelope.message.job_id == created.job_id
    assert h.capabilities.issued == [(created.job_id, envelope.message.attempt_id)]
    assert envelope.capability not in repr(envelope)
    snapshot = h.store.snapshot()
    assert not snapshot.outbox and snapshot.attempt_dispatch[envelope.message.attempt_id] == (
        h.clock.now(),
        1,
    )


def test_stale_lease_holder_mark_and_release_are_no_ops(h: FixtureHarness) -> None:
    h.service.create_job(h.create())
    with h.store.transaction() as tx:
        (first,) = tx.claim_outbox("a", h.clock.now(), timedelta(milliseconds=LEASE_MS), 10)
    h.clock.advance(milliseconds=LEASE_MS)
    with h.store.transaction() as tx:
        (second,) = tx.claim_outbox("b", h.clock.now(), timedelta(milliseconds=LEASE_MS), 10)
    assert second.lease.generation == first.lease.generation + 1
    with h.store.transaction() as tx:
        assert not tx.ack_dispatch(first.lease, h.clock.now())
        assert not tx.release_outbox(first.lease, "LATE")
        assert not tx.dispose_outbox(first.lease, "LATE")
        assert tx.lease_current(second.lease)
    assert h.store.snapshot().attempt_dispatch == {}
    with h.store.transaction() as tx:
        assert tx.ack_dispatch(second.lease, h.clock.now())
        assert not tx.ack_dispatch(second.lease, h.clock.now())  # repeated ack counts once
    assert list(h.store.snapshot().attempt_dispatch.values()) == [(h.clock.now(), 1)]


def test_enqueue_before_mark_crash_republishes_same_attempt_and_start_dedups(
    h: FixtureHarness,
) -> None:
    created = h.service.create_job(h.create())

    class CrashAfterEnqueue:
        def __init__(self) -> None:
            self.calls = 0

        def enqueue(self, envelope: object) -> None:
            h.queue.enqueue(envelope)  # type: ignore[arg-type]
            self.calls += 1
            if self.calls == 1:
                raise SystemExit("dispatcher died before the fenced mark")

    crashing = CrashAfterEnqueue()
    h.service._d = h.service._d.__class__(**{**_deps(h), "queue": crashing})
    with pytest.raises(SystemExit):
        h.service.dispatch_outbox(owner="dispatcher_a")
    assert len(h.store.snapshot().outbox) == 1  # still pending, still leased by the dead holder
    assert h.service.dispatch_outbox(owner="dispatcher_b") == 0  # lease not expired yet
    h.clock.advance(milliseconds=LEASE_MS)
    assert h.service.dispatch_outbox(owner="dispatcher_b") == 1
    first, second = h.queue.receive(), h.queue.receive()
    assert first is not None and second is not None
    assert first.message == second.message  # same message, same attempt
    assert h.service.start_attempt(
        first.capability, created.job_id, first.message.attempt_id
    ).started
    assert (
        h.service.start_attempt(
            second.capability, created.job_id, second.message.attempt_id
        ).reason_code
        == "DUPLICATE_DELIVERY"
    )
    assert list(h.store.snapshot().attempt_dispatch.values())[0][1] == 1


def test_broker_outage_keeps_work_pending_without_new_attempts(h: FixtureHarness) -> None:
    created = h.service.create_job(h.create())
    h.queue.available = False
    for _ in range(3):
        assert h.service.dispatch_outbox() == 0
    snapshot = h.store.snapshot()
    assert len(snapshot.outbox) == 1 and not snapshot.leases
    assert len(snapshot.jobs[created.job_id].attempts) == 1
    h.queue.available = True
    assert h.service.dispatch_outbox() == 1
    assert len(h.store.snapshot().jobs[created.job_id].attempts) == 1


# ----------------------------------------------------------------------- Δ7/Δ13 recovery
def _lose_publish(h: FixtureHarness) -> None:
    """Publish, then the worker dies after receive and before durable start."""

    assert h.service.dispatch_outbox() == 1
    assert h.queue.receive() is not None
    h.clock.advance(milliseconds=START_TIMEOUT_MS)


def test_unstarted_attempt_is_republished_as_the_same_attempt_then_completes(
    h: FixtureHarness,
) -> None:
    created = h.service.create_job(h.create())
    original = h.store.snapshot().jobs[created.job_id].active_attempt.attempt_id
    _lose_publish(h)
    assert h.service.recover_unstarted_dispatches() == ((created.job_id, "republished"),)
    assert h.service.recover_unstarted_dispatches() == ()  # pending intent: no fan-out
    assert h.service.dispatch_outbox() == 1
    envelope = h.queue.receive()
    assert envelope is not None and envelope.message.attempt_id == original
    assert h.service.start_attempt(envelope.capability, created.job_id, original).started
    receipt = h.service.accept_completion(envelope.capability, h.success_claim(envelope.message))
    assert receipt.attempt_id == original
    job = h.store.snapshot().jobs[created.job_id]
    assert job.state is JobState.SUCCEEDED and len(job.attempts) == 1


def test_publish_bound_then_dispatch_loss_then_policy_retry(h: FixtureHarness) -> None:
    created = h.service.create_job(h.create())
    for publish in range(1, FIXTURE_DISPATCH_POLICY.max_publishes + 1):
        _lose_publish(h)
        outcome = h.service.recover_unstarted_dispatches()
        expected = (
            "republished" if publish < FIXTURE_DISPATCH_POLICY.max_publishes else ("dispatch_lost")
        )
        assert outcome == ((created.job_id, expected),)
        assert len(h.store.snapshot().jobs[created.job_id].attempts) == 1
    job = h.store.snapshot().jobs[created.job_id]
    assert job.state is JobState.FAILED_RETRYABLE and job.failure is not None
    assert job.failure.code == "DISPATCH_LOST" and job.active_attempt.started_at is None
    assert job.retry_not_before == h.clock.now() + FIXTURE_RETRY_POLICY.backoff_after(1)
    assert any(e.event_type == "job.dispatch_lost" for e in h.audit.events)
    assert h.service.run_due_retries() == ()
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_after(1) // timedelta(milliseconds=1))
    assert h.service.run_due_retries() == (created.job_id,)
    assert len(h.store.snapshot().jobs[created.job_id].attempts) == 2


def test_recovery_after_a_start_won_is_a_no_op(h: FixtureHarness) -> None:
    created = h.service.create_job(h.create())
    _lose_publish(h)
    with h.store.transaction() as tx:
        (due,) = tx.queued_dispatched_not_started(
            h.clock.now(), FIXTURE_DISPATCH_POLICY.start_timeout, 10
        )
    attempt_id = due.attempt_id
    assert h.service.start_attempt(h.capability(created.job_id), created.job_id, attempt_id).started
    before = h.store.snapshot().jobs[created.job_id]
    assert h.service._recover_unstarted(due) is None
    stale = AttemptDispatch(
        due.job_id,
        attempt_id,
        before.job_revision,
        due.dispatched_at,
        FIXTURE_DISPATCH_POLICY.max_publishes,
    )
    assert h.service._recover_unstarted(stale) is None
    assert h.store.snapshot().jobs[created.job_id] == before


def test_sweep_queries_are_targeted(h: FixtureHarness) -> None:
    fresh = h.service.create_job(h.create(key="a")).job_id
    running = h.service.create_job(h.create(key="b", ref=request_ref("req_b"))).job_id
    h.service.dispatch_outbox()
    for _ in range(2):
        envelope = h.queue.receive()
        assert envelope is not None
        if envelope.message.job_id == running:
            h.service.start_attempt(envelope.capability, running, envelope.message.attempt_id)
    now = h.clock.now()
    with h.store.transaction() as tx:
        assert tx.overdue_running(now, 10) == ()
        assert tx.due_retries(now, 10) == ()
        assert (
            tx.queued_dispatched_not_started(now, FIXTURE_DISPATCH_POLICY.start_timeout, 10) == ()
        )
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    with h.store.transaction() as tx:
        assert tx.overdue_running(h.clock.now(), 10) == (running,)
        due = tx.queued_dispatched_not_started(
            h.clock.now(), FIXTURE_DISPATCH_POLICY.start_timeout, 10
        )
        assert [d.job_id for d in due] == [fresh]
        assert not tx.lease_current(OutboxLease("missing", "x", 1))


def _deps(h: FixtureHarness) -> dict[str, Any]:
    d = h.service._d
    return {name: getattr(d, name) for name in d.__dataclass_fields__}
