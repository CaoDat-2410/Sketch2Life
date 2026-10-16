"""BE2-01 Phase B batch B4: fenced SQL outbox dispatch through real Redis/RQ (B-02, Δ6, Δ14).

Disposable PostgreSQL (conftest) plus an isolated RQ queue on the shared test Redis
(b4_support). Owner decisions come from the ASSUMED_CONTRACT fixture. Worker capability is the
fixture issuer; the B5 worker loop is not exercised. ``requires_postgres``; without PostgreSQL
or Redis the tests skip: NOT_RUN, never PASS.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterator
from typing import Any

import b3_support as s
import b4_support as r
import pytest
from rq.job import Job
from sketch2life.infrastructure.ai_jobs.rq_queue import (
    FIXTURE_FAILURE_TTL_SECONDS,
    WORKER_ENTRYPOINT,
    RqDispatchQueue,
)
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sqlalchemy import select
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


@pytest.fixture
def rq_queue() -> Iterator[RqDispatchQueue]:
    yield from r.isolated_queue()


def _outbox(rig: s.SqlRig) -> list[Any]:
    with rig.engine.connect() as connection:
        return list(connection.execute(select(t.outbox).where(t.outbox.c.kind == "dispatch")))


def _all_ai_jobs_text(rig: s.SqlRig) -> str:
    """Every ai_jobs row rendered as JSON text, to search for a leaked capability."""

    with rig.engine.connect() as connection:
        rows = [
            str(row)
            for table in t.AI_JOBS_METADATA.sorted_tables
            for row in connection.execute(select(table))
        ]
    return "\n".join(rows)


def test_dispatch_publishes_through_rq_and_commits_the_ack_bundle(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    rig = s.build_rig(db)
    service = rig.with_ports(queue=rq_queue)
    created = service.create_job(s.command())
    attempt_id = rig.job(created.job_id).active_attempt.attempt_id
    assert service.dispatch_outbox(owner="dispatcher_a") == 1

    (job_id,) = rq_queue.queue.job_ids
    job = Job.fetch(job_id, connection=rq_queue.queue.connection)
    (row,) = _outbox(rig)
    assert job.func_name == WORKER_ENTRYPOINT
    assert job.description == row.message_id  # args (and capability) never rendered
    assert job.result_ttl == 0 and job.failure_ttl == FIXTURE_FAILURE_TTL_SECONDS
    assert not job.retries_left  # RQ transport retries disabled; SQL owns redelivery
    (envelope,) = r.drain(rq_queue.queue)
    assert envelope.message.attempt_id == attempt_id
    assert envelope.message.message_id == row.message_id

    assert row.delivered_at == rig.clock.now() and row.lease_owner is None
    assert row.lease_until is None and row.lease_generation == 1
    with rig.repository.transaction() as tx:
        dispatch = tx.attempt_dispatch(attempt_id)
    assert dispatch is not None
    assert (dispatch.dispatched_at, dispatch.dispatch_count) == (rig.clock.now(), 1)
    # The transient capability exists only in the broker envelope, never in SQL rows.
    assert envelope.capability not in _all_ai_jobs_text(rig)


def test_broker_outage_keeps_sql_pending_and_recovery_adds_no_attempt(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    rig = s.build_rig(db)
    down = rig.with_ports(queue=r.unavailable_queue())
    created = down.create_job(s.command())
    for _ in range(2):
        assert down.dispatch_outbox(owner="dispatcher_a") == 0
    (row,) = _outbox(rig)
    assert row.delivered_at is None and row.lease_owner is None  # released, still pending
    assert row.last_error_code == "QUEUE_UNAVAILABLE" and row.publish_attempts == 2
    assert rig.job(created.job_id).state.value == "queued"

    up = rig.with_ports(queue=rq_queue)
    assert up.dispatch_outbox(owner="dispatcher_b") == 1
    assert len(r.drain(rq_queue.queue)) == 1
    counts = s.counts(rig.engine)
    assert (counts["job"], counts["attempt"], counts["semantic_request"]) == (1, 1, 1)
    assert len(rig.job(created.job_id).attempts) == 1


def test_dispatcher_and_rq_logs_never_carry_the_capability(
    db: URL, rq_queue: RqDispatchQueue, caplog: pytest.LogCaptureFixture
) -> None:
    rig = s.build_rig(db)
    service = rig.with_ports(queue=rq_queue)
    created = service.create_job(s.command())
    # Alembic's fileConfig disables pre-existing loggers; re-enable them so RQ/redis/app
    # records are really captured rather than silently dropped.
    disabled = [
        logger
        for logger in logging.root.manager.loggerDict.values()
        if isinstance(logger, logging.Logger) and logger.disabled
    ]
    for logger in disabled:
        logger.disabled = False
    try:
        with caplog.at_level(logging.DEBUG):
            assert service.dispatch_outbox() == 1
    finally:
        for logger in disabled:
            logger.disabled = True
    (envelope,) = r.drain(rq_queue.queue)
    assert envelope.message.job_id == created.job_id
    for record in caplog.records:
        rendered = " ".join(str(v) for v in (record.getMessage(), record.args, vars(record)))
        assert envelope.capability not in rendered


def test_concurrent_claims_lease_disjoint_rows(db: URL) -> None:
    rig = s.build_rig(db)
    for index in range(2):
        rig.service.create_job(s.command(key=f"k{index}", request=s.REQUESTS[index]))
    first_claimed = threading.Event()
    release = threading.Event()
    claimed: dict[str, list[str]] = {}

    def claim_and_hold() -> None:
        with rig.repository.transaction() as tx:
            rows = tx.claim_outbox("a", rig.clock.now(), rig.deps.dispatch_policy.lease, 1)
            claimed["a"] = [c.message.message_id for c in rows]
            first_claimed.set()
            assert release.wait(30)

    holder = threading.Thread(target=claim_and_hold)
    holder.start()
    try:
        assert first_claimed.wait(30)
        with rig.repository.transaction() as tx:  # SKIP LOCKED: no wait on the held row
            rows = tx.claim_outbox("b", rig.clock.now(), rig.deps.dispatch_policy.lease, 10)
            claimed["b"] = [c.message.message_id for c in rows]
    finally:
        release.set()
        holder.join(30)
    assert len(claimed["a"]) == 1 and len(claimed["b"]) == 1
    assert set(claimed["a"]).isdisjoint(claimed["b"])
