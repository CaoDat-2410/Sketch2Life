"""BE2-01 Phase B batch B6: process kill/restart recovery on PostgreSQL (B-01; plan §7.1 W01,
W02, W06, W08).

Each case runs the service in a spawned child process that dies with ``os._exit`` at a chosen
boundary (no clean shutdown, no rollback hooks). The parent then restarts from a fresh engine,
checks what is durable and lets the normal dispatcher/reconciler/side-effect passes recover.
One ephemeral HMAC key per test reaches the child only through the spawn pipe. Fake provider and
ASSUMED_CONTRACT owner fixture; synthetic data. ``requires_postgres`` (W02 also needs Redis);
without services the tests skip: NOT_RUN, never PASS.
"""

from __future__ import annotations

import hashlib
import multiprocessing
import os
from collections.abc import Iterator
from multiprocessing.connection import Connection
from typing import Any

import b3_support as s
import b4_support as r
import b5_support as b5
import pytest
from sketch2life.application.ports.ai_jobs import DispatchMessage, QuarantineIntent
from sketch2life.application.services.ai_jobs import FIXTURE_RETRY_POLICY
from sketch2life.domain.ai_jobs.completion import Moderation
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.infrastructure.ai_jobs.rq_queue import RqDispatchQueue
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.ai_jobs.worker_capability import (
    CapabilityKey,
    HmacCapabilityIssuer,
    HmacCapabilityVerifier,
)
from sqlalchemy import Engine, select
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres
SPAWN = multiprocessing.get_context("spawn")
TIMEOUT = 60
EXIT_BEFORE_COMMIT = 24
EXIT_AFTER_COMMIT = 23
EXIT_AFTER_START = 25


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


@pytest.fixture
def rq_queue() -> Iterator[RqDispatchQueue]:
    yield from b5.isolated_queue()


def checksum(engine: Engine) -> str:
    """Every ai_jobs row (all columns, primary-key order): revisions, attempts, receipts and
    fingerprints, semantic keys, outbox rows with lease/delivery state."""

    digest = hashlib.sha256()
    with engine.connect() as connection:
        for table in t.AI_JOBS_METADATA.sorted_tables:
            order = list(table.primary_key.columns)
            for row in connection.execute(select(table).order_by(*order)).all():
                digest.update(repr(tuple(row)).encode("utf-8"))
            digest.update(f"|{table.name}|".encode())
    return digest.hexdigest()


def _run(target: Any, *args: Any) -> int:
    child = SPAWN.Process(target=target, args=args)
    child.start()
    child.join(TIMEOUT)
    if child.is_alive():
        child.kill()
        child.join(5)
        raise AssertionError("child did not finish in time")
    assert child.exitcode is not None
    return child.exitcode


# ------------------------------------------------------------- W01 crash before create commit
def _create_and_die_before_commit(url: URL) -> None:
    def die(uow: Any) -> None:
        if uow.writes:  # every create statement ran; the commit never happens
            os._exit(EXIT_BEFORE_COMMIT)

    s.build_rig(url, before_commit=die).service.create_job(s.command(key="idem_b6_w01"))
    os._exit(0)  # unreachable when the hook fires


def test_crash_before_create_commit_leaves_nothing_and_the_same_key_creates(db: URL) -> None:
    assert _run(_create_and_die_before_commit, db) == EXIT_BEFORE_COMMIT
    rig = s.build_rig(db)  # restart: fresh engine and process state
    assert all(value == 0 for value in s.counts(rig.engine).values())
    result = rig.service.create_job(s.command(key="idem_b6_w01"))  # caller retries the key
    assert (result.outcome, result.replayed) == ("created", False)
    assert s.counts(rig.engine)["job"] == 1 and s.no_orphans(rig.engine)


# ------------------------------------- W02/W08 kill after commits, restart and recover
class _Down:
    def __init__(self, port: Any) -> None:
        self._port = port

    def describe(self, artifact_ref: str) -> Any:
        return self._port.describe(artifact_ref)

    def quarantine(self, intent: QuarantineIntent) -> None:
        raise ConnectionError("artifact sink unavailable")


def _commit_then_die(url: URL, key: CapabilityKey, out: Connection) -> None:
    """Child: two creates (one never published) and one unsafe completion whose side effects
    cannot be delivered; then the process is killed right after the last commit."""

    rig = s.build_rig(url)
    ports = {"capability_issuer": HmacCapabilityIssuer(key),
             "worker_capability": HmacCapabilityVerifier(key, rig.clock)}
    service = rig.with_ports(**ports)
    first = service.create_job(s.command(key="idem_b6_a", request=s.REQUESTS[0]))
    second = service.create_job(s.command(key="idem_b6_b", request=s.REQUESTS[1]))
    job = rig.job(first.job_id)
    attempt = job.active_attempt
    token = HmacCapabilityIssuer(key).issue(first.job_id, attempt.attempt_id, rig.clock.now())
    assert service.start_attempt(token, first.job_id, attempt.attempt_id).started
    message = DispatchMessage("msg_b6_direct", first.job_id, attempt.attempt_id,
                              attempt.attempt_number, job.job_type, attempt.request_ref)
    claim = b5.success_claim(rig.owner, message, moderation=Moderation.UNSAFE)
    down = rig.with_ports(**ports, audit=b5.FailingAuditSink(),
                          artifacts=_Down(fx.FixtureArtifacts(rig.owner)))
    receipt = down.accept_completion(token, claim)  # committed; delivery fails
    out.send({"checksum": checksum(rig.engine), "first": first.job_id, "second": second.job_id,
              "attempt": attempt.attempt_id, "receipt": receipt.receipt_id,
              "fingerprint": receipt.fingerprint, "claim_ref": claim.outputs[0].artifact_ref})
    out.close()
    os._exit(EXIT_AFTER_COMMIT)


def test_kill_after_commit_keeps_rows_then_restart_publishes_and_delivers(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    key = CapabilityKey("b6_restart_test", os.urandom(32))
    receive, send = SPAWN.Pipe(duplex=False)
    assert _run(_commit_then_die, db, key, send) == EXIT_AFTER_COMMIT
    assert receive.poll(TIMEOUT)
    child = receive.recv()

    rig = b5.build_b5_rig(db, key=key)  # restart: fresh engine, process, sinks, same run key
    assert checksum(rig.engine) == child["checksum"]  # B-01: every committed row unchanged
    first = rig.base.job(child["first"])
    assert first.state is JobState.BLOCKED_UNSAFE and first.job_revision >= 3
    with rig.base.repository.transaction() as tx:
        stored = tx.get_completion_receipt(child["first"], child["attempt"])
    assert stored is not None
    assert (stored.receipt_id, stored.fingerprint) == (child["receipt"], child["fingerprint"])

    service = rig.with_ports(queue=rq_queue)
    assert service.dispatch_outbox(owner="restarted") == 1  # W02: the never-published create
    (envelope,) = r.drain(rq_queue.queue)
    assert envelope.message.job_id == child["second"]
    pending = [row for kind in ("audit", "quarantine") for row in b5.outbox_rows(rig.engine, kind)
               if row.delivered_at is None]
    assert {row.kind for row in pending} == {"audit", "quarantine"}
    assert rig.service.deliver_side_effects(owner="restarted") == len(pending)  # W08
    found = rig.base.owner.read(fx.artifact_scope(child["claim_ref"]))
    assert found is not None and found[0]["quarantine_reason"] == "UNSAFE_CONTENT"
    assert sorted(b5.applied_quarantines(rig.engine)) == sorted(
        row.event_id for row in pending if row.kind == "quarantine"
    )
    assert rig.service.deliver_side_effects(owner="restarted") == 0


# --------------------------------------------- W06 started, died before provider result
def _start_then_die(url: URL, key: CapabilityKey) -> None:
    rig = s.build_rig(url)
    service = rig.with_ports(capability_issuer=HmacCapabilityIssuer(key),
                             worker_capability=HmacCapabilityVerifier(key, rig.clock))
    created = service.create_job(s.command(key="idem_b6_w06"))
    attempt = rig.job(created.job_id).active_attempt.attempt_id
    token = HmacCapabilityIssuer(key).issue(created.job_id, attempt, rig.clock.now())
    assert service.start_attempt(token, created.job_id, attempt).started
    os._exit(EXIT_AFTER_START)  # durable start committed; the provider never ran


def test_worker_dies_after_start_before_provider_then_policy_retry_recovers(db: URL) -> None:
    key = CapabilityKey("b6_start_test", os.urandom(32))
    assert _run(_start_then_die, db, key) == EXIT_AFTER_START
    rig = b5.build_b5_rig(db, key=key)
    with rig.engine.connect() as connection:
        (job_id,) = connection.execute(select(t.job.c.job_id)).scalars().all()
    running = rig.base.job(job_id)
    assert running.state is JobState.RUNNING and running.active_attempt.started_at is not None
    first_attempt = running.active_attempt.attempt_id
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    assert rig.service.expire_overdue_attempts() == (job_id,)
    failed = rig.base.job(job_id)
    assert failed.state is JobState.FAILED_RETRYABLE and failed.failure is not None
    assert failed.failure.code == "PROVIDER_TIMEOUT"
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    assert rig.service.run_due_retries() == (job_id,)
    retried = rig.base.job(job_id)
    assert retried.state is JobState.QUEUED and retried.active_attempt.attempt_number == 2
    assert retried.attempts[0].attempt_id == first_attempt
    with rig.engine.connect() as connection:
        receipts = connection.execute(select(t.completion_receipt)).all()
    assert receipts == []  # no claim was invented for the attempt that died
