"""BE2-01 Phase B batch B4: lease takeover, crash windows and SQL-owned recovery (B-04, B-06a/b).

Disposable PostgreSQL plus, where a broker is part of the window, an isolated queue on the real
test Redis/RQ. The worker side is a controlled fixture receiver (``pop_envelope``): "worker died
after receive, before durable start" means the envelope is taken and dropped. The B5 worker loop,
provider and completion recovery are not exercised. ``requires_postgres``; skipped = NOT_RUN.
"""

from __future__ import annotations

import multiprocessing
import os
import threading
from collections.abc import Callable, Iterator
from dataclasses import replace
from hashlib import sha256
from typing import Any

import b3_support as s
import b4_support as r
import pytest
from sketch2life.application.ports.ai_jobs import AttemptDispatch, WorkerDispatchEnvelope
from sketch2life.application.services.ai_jobs import (
    FIXTURE_DISPATCH_POLICY,
    FIXTURE_RETRY_POLICY,
    AiJobService,
    StartResult,
)
from sketch2life.domain.ai_jobs.completion import (
    CompletionClaim,
    Moderation,
    OutcomeKind,
    OutputRef,
)
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.infrastructure.ai_jobs.harness import ORG
from sketch2life.infrastructure.ai_jobs.rq_queue import RqDispatchQueue
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobUnitOfWork
from sqlalchemy import select, update
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres

SPAWN = multiprocessing.get_context("spawn")
TIMEOUT = 30
POLICY = FIXTURE_DISPATCH_POLICY


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


@pytest.fixture
def rq_queue() -> Iterator[RqDispatchQueue]:
    yield from r.isolated_queue()


def _dispatch_row(rig: s.SqlRig, message_id: str) -> Any:
    with rig.engine.connect() as connection:
        return connection.execute(select(t.outbox).where(t.outbox.c.message_id == message_id)).one()


def _attempt_dispatch(rig: s.SqlRig, attempt_id: str) -> AttemptDispatch:
    with rig.repository.transaction() as tx:
        found = tx.attempt_dispatch(attempt_id)
    assert found is not None
    return found


def _pending_dispatches(rig: s.SqlRig) -> int:
    with rig.engine.connect() as connection:
        return len(
            connection.execute(
                select(t.outbox.c.message_id).where(
                    t.outbox.c.kind == "dispatch", t.outbox.c.delivered_at.is_(None)
                )
            ).all()
        )


# ---------------------------------------------------------------------------- B-04c lease
def test_stale_lease_holder_mark_and_release_are_no_ops_after_takeover(db: URL) -> None:
    rig = s.build_rig(db)
    created = rig.service.create_job(s.command())
    attempt_id = rig.job(created.job_id).active_attempt.attempt_id
    with rig.repository.transaction() as tx:
        (stale,) = tx.claim_outbox("dispatcher_a", rig.clock.now(), POLICY.lease, 10)
    rig.clock.advance(milliseconds=POLICY.lease_ms)
    with rig.repository.transaction() as tx:
        (current,) = tx.claim_outbox("dispatcher_b", rig.clock.now(), POLICY.lease, 10)
    assert current.lease.generation == stale.lease.generation + 1
    with rig.repository.transaction() as tx:
        assert not tx.ack_dispatch(stale.lease, rig.clock.now())
        assert not tx.release_outbox(stale.lease, "LATE")
        assert not tx.dispose_outbox(stale.lease, "LATE")
    assert _attempt_dispatch(rig, attempt_id).dispatch_count == 0
    row = _dispatch_row(rig, current.message.message_id)
    assert (row.lease_owner, row.lease_generation, row.delivered_at) == ("dispatcher_b", 2, None)
    with rig.repository.transaction() as tx:
        assert tx.ack_dispatch(current.lease, rig.clock.now())
    with rig.repository.transaction() as tx:
        assert not tx.ack_dispatch(current.lease, rig.clock.now())  # repeat changes nothing
    dispatch = _attempt_dispatch(rig, attempt_id)
    assert (dispatch.dispatched_at, dispatch.dispatch_count) == (rig.clock.now(), 1)


# ---------------------------------------------------- B-06a enqueue-before-mark, real kill
def _dispatch_then_die(url: URL, host: str, port: int, queue_name: str) -> None:
    """Child dispatcher: the real RQ enqueue succeeds, then the process dies before the
    fenced acknowledgement commits."""

    real = RqDispatchQueue(r.connect(host, port), queue_name)

    class DieAfterEnqueue:
        def enqueue(self, envelope: WorkerDispatchEnvelope) -> None:
            real.enqueue(envelope)
            os._exit(17)

    rig = s.build_rig(url)
    rig.with_ports(queue=DieAfterEnqueue()).dispatch_outbox(owner="dispatcher_dead")


def test_enqueue_then_crash_before_mark_republishes_same_attempt_and_start_dedups(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    rig = s.build_rig(db)
    created = rig.service.create_job(s.command())
    attempt_id = rig.job(created.job_id).active_attempt.attempt_id
    settings = r.redis_settings()
    assert settings is not None
    child = SPAWN.Process(
        target=_dispatch_then_die, args=(db, settings[0], settings[1], rq_queue.queue.name)
    )
    child.start()
    child.join(TIMEOUT)
    if child.is_alive():
        child.terminate()
    assert child.exitcode == 17
    with rig.engine.connect() as connection:
        (row,) = connection.execute(select(t.outbox).where(t.outbox.c.kind == "dispatch")).all()
    assert row.delivered_at is None and row.lease_owner == "dispatcher_dead"
    assert len(rq_queue.queue.job_ids) == 1  # the effect happened, the mark did not

    live = rig.with_ports(queue=rq_queue)
    assert live.dispatch_outbox(owner="dispatcher_live") == 0  # lease not yet expired
    rig.clock.advance(milliseconds=POLICY.lease_ms)
    assert live.dispatch_outbox(owner="dispatcher_live") == 1
    first, second = r.drain(rq_queue.queue)
    assert first.message == second.message and first.message.attempt_id == attempt_id
    assert live.start_attempt(first.capability, created.job_id, attempt_id).started
    duplicate = live.start_attempt(second.capability, created.job_id, attempt_id)
    assert duplicate == StartResult(False, "DUPLICATE_DELIVERY")
    row = _dispatch_row(rig, row.message_id)
    assert row.delivered_at is not None and row.lease_generation == 2
    assert _attempt_dispatch(rig, attempt_id).dispatch_count == 1
    assert len(rig.job(created.job_id).attempts) == 1


# ------------------------------------------------- B-04a/b same-attempt republish and loss
def _lose_one_publish(service: AiJobService, rig: s.SqlRig, queue: RqDispatchQueue) -> None:
    """Publish through RQ; the worker takes the envelope and dies before durable start."""

    assert service.dispatch_outbox() == 1
    assert len(r.drain(queue.queue)) == 1
    rig.clock.advance(milliseconds=POLICY.start_timeout_ms)


def _success_claim(rig: s.SqlRig, job_id: str, attempt_id: str) -> CompletionClaim:
    ref = f"artifact_b4_{attempt_id}"
    digest = sha256(ref.encode()).hexdigest()
    rig.owner.set(
        fx.artifact_scope(ref),
        {
            "sha256": digest,
            "organization_id": ORG,
            "producer_job_id": job_id,
            "producer_attempt_id": attempt_id,
        },
    )
    pinned = rig.job(job_id).active_attempt.request_ref
    return CompletionClaim(
        job_id,
        attempt_id,
        pinned.request_revision,
        pinned.input_hash,
        pinned.context_revision,
        OutcomeKind.SUCCESS,
        (OutputRef(ref, digest),),
        Moderation.PASSED,
    )


def test_lost_receive_is_republished_as_the_same_attempt_and_completes(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    rig = s.build_rig(db)
    service = rig.with_ports(queue=rq_queue)
    created = service.create_job(s.command())
    attempt_id = rig.job(created.job_id).active_attempt.attempt_id
    _lose_one_publish(service, rig, rq_queue)
    assert service.recover_unstarted_dispatches() == ((created.job_id, "republished"),)
    assert service.recover_unstarted_dispatches() == ()  # pending intent excludes it
    assert service.dispatch_outbox() == 1
    (envelope,) = r.drain(rq_queue.queue)
    assert envelope.message.attempt_id == attempt_id
    assert service.start_attempt(envelope.capability, created.job_id, attempt_id).started
    receipt = service.accept_completion(
        envelope.capability, _success_claim(rig, created.job_id, attempt_id)
    )
    job = rig.job(created.job_id)
    assert receipt.attempt_id == attempt_id and job.state is JobState.SUCCEEDED
    assert len(job.attempts) == 1 and _attempt_dispatch(rig, attempt_id).dispatch_count == 2


def test_publish_bound_then_dispatch_loss_keeps_provenance_and_policy_retries(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    rig = s.build_rig(db)
    service = rig.with_ports(queue=rq_queue)
    created = service.create_job(s.command())
    original = rig.job(created.job_id)
    for publish in range(1, POLICY.max_publishes + 1):
        _lose_one_publish(service, rig, rq_queue)
        outcome = "republished" if publish < POLICY.max_publishes else "dispatch_lost"
        assert service.recover_unstarted_dispatches() == ((created.job_id, outcome),)
        assert len(rig.job(created.job_id).attempts) == 1  # never a new attempt early
    lost = rig.job(created.job_id)
    attempt = lost.active_attempt
    assert lost.state is JobState.FAILED_RETRYABLE and lost.failure is not None
    assert (lost.failure.code, lost.failure.retryable) == ("DISPATCH_LOST", True)
    assert lost.retry_not_before == rig.clock.now() + FIXTURE_RETRY_POLICY.backoff_after(1)
    assert attempt.started_at is None and attempt.outcome == "dispatch_lost"
    assert attempt.request_ref == original.request_ref
    assert attempt.attempt_id == original.active_attempt.attempt_id
    assert _attempt_dispatch(rig, attempt.attempt_id).dispatch_count == POLICY.max_publishes
    assert service.recover_unstarted_dispatches() == ()
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    assert service.run_due_retries() == (created.job_id,)
    retried = rig.job(created.job_id)
    assert retried.state is JobState.QUEUED
    assert [a.attempt_number for a in retried.attempts] == [1, 2]


def test_final_attempt_dispatch_loss_is_exhausted_and_never_reopened(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    rig = s.build_rig(db)
    single = replace(FIXTURE_RETRY_POLICY, policy_id="fixture.job_retry.single", max_attempts=1)
    service = rig.with_ports(queue=rq_queue, retry_policy=single)
    created = service.create_job(s.command())
    for _ in range(POLICY.max_publishes):
        _lose_one_publish(service, rig, rq_queue)
        service.recover_unstarted_dispatches()
    job = rig.job(created.job_id)
    assert job.state is JobState.FAILED_EXHAUSTED and job.retry_not_before is None
    assert job.completed_at == rig.clock.now() and job.active_attempt.started_at is None
    rig.clock.advance(seconds=600)
    assert service.run_due_retries() == () and service.recover_unstarted_dispatches() == ()
    assert rig.job(created.job_id) == job


# ----------------------------------------------------------- B-04b(iv) CAS race vs start
def _due_at_publish_bound(rig: s.SqlRig) -> tuple[str, str, AttemptDispatch]:
    """A queued attempt already published ``max_publishes`` times, overdue for start
    (synthetic SQL bookkeeping, so the race below is the only moving part)."""

    created = rig.service.create_job(s.command())
    attempt_id = rig.job(created.job_id).active_attempt.attempt_id
    with rig.engine.begin() as connection:
        connection.execute(
            update(t.outbox)
            .where(t.outbox.c.attempt_id == attempt_id)
            .values(delivered_at=rig.clock.now())
        )
        connection.execute(
            update(t.attempt)
            .where(t.attempt.c.attempt_id == attempt_id)
            .values(dispatched_at=rig.clock.now(), dispatch_count=POLICY.max_publishes)
        )
    rig.clock.advance(milliseconds=POLICY.start_timeout_ms)
    with rig.repository.transaction() as tx:
        (due,) = tx.queued_dispatched_not_started(rig.clock.now(), POLICY.start_timeout, 10)
    return created.job_id, attempt_id, due


def _paused_rig(db: URL) -> tuple[s.SqlRig, threading.Event, threading.Event]:
    ready, release = threading.Event(), threading.Event()

    def pause(uow: SqlAiJobUnitOfWork) -> None:
        if uow.writes:
            ready.set()
            assert release.wait(TIMEOUT)

    return s.build_rig(db, before_commit=pause), ready, release


def _run(target: Callable[[], Any]) -> tuple[threading.Thread, dict[str, Any]]:
    box: dict[str, Any] = {}

    def run() -> None:
        try:
            box["result"] = target()
        except BaseException as error:
            box["error"] = error

    thread = threading.Thread(target=run)
    thread.start()
    return thread, box


@pytest.mark.parametrize("first", ["start", "reconciler"])
def test_dispatch_loss_and_start_have_exactly_one_winner(db: URL, first: str) -> None:
    rig = s.build_rig(db)
    job_id, attempt_id, due = _due_at_publish_bound(rig)
    paused, ready, release = _paused_rig(db)
    paused.clock.advance(milliseconds=POLICY.start_timeout_ms)
    capability = rig.capabilities.issue(job_id)
    paused_capability = paused.capabilities.issue(job_id)

    def start(service: AiJobService, token: str) -> Callable[[], Any]:
        return lambda: service.start_attempt(token, job_id, attempt_id)

    def recover(service: AiJobService) -> Callable[[], Any]:
        return lambda: service._recover_unstarted(due)

    if first == "start":
        winner, winner_box = _run(start(paused.service, paused_capability))
        assert ready.wait(TIMEOUT)  # start holds the job row lock, not yet committed
        loser, loser_box = _run(recover(rig.service))
    else:
        winner, winner_box = _run(recover(paused.service))
        assert ready.wait(TIMEOUT)  # dispatch loss written, not yet committed
        loser, loser_box = _run(start(rig.service, capability))
    try:
        loser.join(1.0)
        assert loser.is_alive()  # waits on the job row lock instead of overwriting
    finally:
        release.set()
        winner.join(TIMEOUT)
        loser.join(TIMEOUT)
    assert "error" not in winner_box and "error" not in loser_box, (winner_box, loser_box)
    job = rig.job(job_id)
    if first == "start":
        assert winner_box["result"] == StartResult(True, None)
        assert loser_box["result"] is None
        assert job.state is JobState.RUNNING and job.active_attempt.started_at is not None
    else:
        assert winner_box["result"] == (job_id, "dispatch_lost")
        assert loser_box["result"] == StartResult(False, "JOB_NOT_QUEUED")
        assert job.state is JobState.FAILED_RETRYABLE and job.active_attempt.started_at is None


def test_concurrent_reconcilers_create_exactly_one_recovery_intent(db: URL) -> None:
    rig = s.build_rig(db)
    job_id, attempt_id, due = _due_at_publish_bound(rig)
    with rig.engine.begin() as connection:  # below the bound: recovery republishes
        connection.execute(
            update(t.attempt).where(t.attempt.c.attempt_id == attempt_id).values(dispatch_count=1)
        )
    due = replace(due, dispatch_count=1)
    paused, ready, release = _paused_rig(db)
    paused.clock.advance(milliseconds=POLICY.start_timeout_ms)
    first, first_box = _run(lambda: paused.service._recover_unstarted(due))
    assert ready.wait(TIMEOUT)
    second, second_box = _run(lambda: rig.service._recover_unstarted(due))
    try:
        second.join(1.0)
        assert second.is_alive()
    finally:
        release.set()
        first.join(TIMEOUT)
        second.join(TIMEOUT)
    assert first_box.get("result") == (job_id, "republished")
    assert "error" not in second_box and second_box["result"] is None
    assert _pending_dispatches(rig) == 1
    assert len(rig.job(job_id).attempts) == 1


# ------------------------------------------------------------- B-06b targeted sweeps
def test_overdue_running_and_due_retry_sweeps_are_targeted(db: URL) -> None:
    rig = s.build_rig(db)
    queued = rig.service.create_job(s.command(key="q", request=s.REQUESTS[0])).job_id
    running = rig.service.create_job(s.command(key="r", request=s.REQUESTS[1])).job_id
    failing = rig.service.create_job(s.command(key="f", request=s.REQUESTS[2])).job_id
    assert rig.service.dispatch_outbox() == 3
    queue = rig.deps.queue
    received = {}
    while (envelope := queue.receive()) is not None:  # type: ignore[attr-defined]
        received[envelope.message.job_id] = envelope
    for job_id in (running, failing):
        envelope = received[job_id]
        assert rig.service.start_attempt(
            envelope.capability, job_id, envelope.message.attempt_id
        ).started
    pinned = rig.job(failing).active_attempt
    rig.service.accept_completion(
        received[failing].capability,
        CompletionClaim(
            failing,
            pinned.attempt_id,
            pinned.request_ref.request_revision,
            pinned.request_ref.input_hash,
            pinned.request_ref.context_revision,
            OutcomeKind.FAILURE,
            failure_code="PROVIDER_UNAVAILABLE",
            retryable=True,
        ),
    )
    with rig.repository.transaction() as tx:
        now = rig.clock.now()
        assert tx.overdue_running(now, 10) == ()
        assert tx.due_retries(now, 10) == ()
        assert tx.queued_dispatched_not_started(now, POLICY.start_timeout, 10) == ()
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    with rig.repository.transaction() as tx:
        now = rig.clock.now()
        assert tx.overdue_running(now, 10) == (running,)
        assert tx.due_retries(now, 10) == ((failing, 1),)
        due = tx.queued_dispatched_not_started(now, POLICY.start_timeout, 10)
        assert [d.job_id for d in due] == [queued]
    assert rig.service.expire_overdue_attempts() == (running,)
    expired = rig.job(running)
    assert expired.state is JobState.FAILED_RETRYABLE and expired.failure is not None
    assert expired.failure.code == "PROVIDER_TIMEOUT"
    assert rig.service.run_due_retries() == (failing,)  # running's backoff is not yet due
    assert len(rig.job(failing).attempts) == 2 and rig.job(queued).state is JobState.QUEUED
