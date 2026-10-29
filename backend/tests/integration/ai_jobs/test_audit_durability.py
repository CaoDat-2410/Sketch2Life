"""BE2-01 Phase B batch B5: durable incidents and side-effect delivery on PostgreSQL
(B-06c/d, B-08b, Δ9/Δ15).

Audit-only incidents commit before the answer (503 if they cannot); repeated and concurrent
incidents deduplicate by event id; committed intents survive a crash before delivery and a
crash after the sink effect but before the mark, and are redelivered with the stored event id
as a sink no-op; stale lease holders are no-ops; rolled-back rounds and foreign lineage
produce nothing. ASSUMED_CONTRACT fixture and component sinks; synthetic data only.
``requires_postgres``; without PostgreSQL the tests skip: NOT_RUN, never PASS.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from hashlib import sha256
from typing import Any

import b3_support as s
import b5_support as b5
import pytest
from sqlalchemy import select
from sqlalchemy.engine import URL

from sketch2life.application.ports.ai_jobs import AuditEvent, DispatchMessage, QuarantineIntent
from sketch2life.application.services.ai_jobs import (
    FIXTURE_DISPATCH_POLICY,
    FIXTURE_RETRY_POLICY,
    AiJobError,
)
from sketch2life.domain.ai_jobs.completion import CompletionClaim, Moderation
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.infrastructure.ai_jobs.harness import ORG
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.ai_jobs.sql.repository import (
    SqlAiJobRepository,
    SqlAiJobUnitOfWork,
)

pytestmark = pytest.mark.requires_postgres
TIMEOUT = 30
LEASE_MS = FIXTURE_DISPATCH_POLICY.lease_ms


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


class _Crash(BaseException):
    """Simulated process death: not an ``Exception``, so nothing on the path catches it."""


class _DownArtifacts:
    def __init__(self, port: fx.FixtureArtifacts) -> None:
        self._port = port

    def describe(self, artifact_ref: str) -> Any:
        return self._port.describe(artifact_ref)

    def quarantine(self, intent: QuarantineIntent) -> None:
        raise ConnectionError("artifact sink unavailable")


def _started(rig: b5.B5Rig) -> tuple[str, Any, str]:
    created = rig.service.create_job(s.command())
    token = rig.capability(created.job_id)
    message = b5.message_for(rig, created.job_id)
    assert rig.service.start_attempt(token, created.job_id, message.attempt_id).started
    return created.job_id, message, token


def _superseded(rig: b5.B5Rig) -> tuple[str, str, CompletionClaim]:
    job_id, first, token = _started(rig)
    late = b5.success_claim(rig.base.owner, first, label="late")
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    assert rig.service.expire_overdue_attempts() == (job_id,)
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    assert rig.service.run_due_retries() == (job_id,)
    return job_id, token, late


def _audit(rig: b5.B5Rig, event_type: str) -> list[Any]:
    return [row for row in b5.outbox_rows(rig.engine, "audit")
            if row.payload["event_type"] == event_type]


def _pending(rig: b5.B5Rig) -> list[Any]:
    return [row for kind in ("audit", "quarantine") for row in b5.outbox_rows(rig.engine, kind)
            if row.delivered_at is None]


def test_guard_incident_is_durable_before_the_answer(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    job_id, token, late = _superseded(rig)
    before = rig.base.job(job_id)
    receipt = rig.service.accept_completion(token, late)
    assert not receipt.authoritative and receipt.reason_code == "ATTEMPT_SUPERSEDED"
    (incident,) = _audit(rig, "job.completion_rejected")
    assert incident.payload["reason_code"] == "ATTEMPT_SUPERSEDED"
    (quarantine,) = b5.outbox_rows(rig.engine, "quarantine")
    assert quarantine.payload["artifact_refs"] == [late.outputs[0].artifact_ref]
    assert rig.base.job(job_id) == before
    assert incident.event_id in {event_id for event_id, _, _ in rig.audit_sink.applied()}


def test_incident_commit_failure_is_a_retryable_503(db: URL) -> None:
    hook, _, _ = b5.pause_first_write(fail=True)
    armed = {"on": False}

    def before_commit(uow: SqlAiJobUnitOfWork) -> None:
        if armed["on"]:
            hook(uow)

    rig = b5.build_b5_rig(db, before_commit=before_commit)
    _, token, late = _superseded(rig)
    armed["on"] = True
    with pytest.raises(AiJobError) as error:
        rig.service.accept_completion(token, late)
    assert (error.value.code, error.value.http_status, error.value.retryable) == (
        "DEPENDENCY_UNAVAILABLE", 503, True
    )
    assert _audit(rig, "job.completion_rejected") == []
    assert b5.outbox_rows(rig.engine, "quarantine") == []
    assert not rig.service.accept_completion(token, late).authoritative  # retry lands
    assert len(_audit(rig, "job.completion_rejected")) == 1


def test_repeated_incident_is_stored_and_applied_once(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    _, token, late = _superseded(rig)
    rig.service.accept_completion(token, late)
    rig.service.accept_completion(token, late)
    (incident,) = _audit(rig, "job.completion_rejected")
    assert rig.audit_sink.deliveries.count(incident.event_id) == 2
    assert [event_id for event_id, _, _ in rig.audit_sink.applied()].count(incident.event_id) == 1
    assert len(b5.applied_quarantines(rig.engine)) == 1


def test_concurrent_identical_conflict_incidents_roll_back_and_dedup(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    _, message, token = _started(rig)
    rig.service.accept_completion(token, b5.success_claim(rig.base.owner, message, label="a"))
    conflicting = b5.success_claim(rig.base.owner, message, label="b")
    hook, ready, release = b5.pause_first_write()
    paused = rig.with_ports(repository=SqlAiJobRepository(
        rig.engine, lambda c: fx.FixtureFenceHold(c), before_commit=hook
    ))
    first, first_box = b5.run_thread(lambda: paused.accept_completion(token, conflicting))
    assert ready.wait(TIMEOUT)  # incident row inserted, not committed
    second, second_box = b5.run_thread(lambda: rig.service.accept_completion(token, conflicting))
    b5.wait_for_lock_waiters(rig.engine)  # the second insert waits on the unique key
    release.set()
    first.join(TIMEOUT)
    second.join(TIMEOUT)
    for status, error in (first_box[0], second_box[0]):
        assert status == "error" and isinstance(error, AiJobError)
        assert error.code == "COMPLETION_CONFLICT"  # not 503: the loser re-read the winner
    assert len(_audit(rig, "job.completion_conflict")) == 1


def test_crash_before_delivery_is_redelivered_by_a_restarted_process(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    down = rig.with_ports(audit=b5.FailingAuditSink(),
                          artifacts=_DownArtifacts(fx.FixtureArtifacts(rig.base.owner)))
    job_id, message, token = _started(rig)
    claim = b5.success_claim(rig.base.owner, message, moderation=Moderation.UNSAFE)
    assert down.accept_completion(token, claim).authoritative  # committed despite the sinks
    pending = _pending(rig)
    assert {row.kind for row in pending} == {"audit", "quarantine"}
    assert b5.applied_quarantines(rig.engine) == []
    restarted = b5.build_b5_rig(db, key=rig.key)  # fresh engine/process state, same run key
    assert restarted.service.deliver_side_effects() == len(pending)
    assert _pending(rig) == []
    applied = {event_id for event_id, _, _ in rig.audit_sink.applied()}
    assert {row.event_id for row in pending if row.kind == "audit"} <= applied
    assert b5.applied_quarantines(rig.engine) == sorted(
        row.event_id for row in pending if row.kind == "quarantine"
    )
    assert restarted.service.deliver_side_effects() == 0
    assert rig.base.job(job_id).state is JobState.BLOCKED_UNSAFE


def test_crash_after_sink_effect_before_mark_is_a_sink_no_op(
    db: URL, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = b5.build_b5_rig(db)
    _, message, token = _started(rig)
    assert rig.service.deliver_side_effects() >= 1  # settle the create intent first
    assert _pending(rig) == []
    down = rig.with_ports(audit=b5.FailingAuditSink(),
                          artifacts=_DownArtifacts(fx.FixtureArtifacts(rig.base.owner)))
    claim = b5.success_claim(rig.base.owner, message, moderation=Moderation.UNSAFE)
    assert down.accept_completion(token, claim).authoritative
    scope = fx.artifact_scope(claim.outputs[0].artifact_ref)
    epoch_before = rig.base.owner.epoch(scope)
    original = SqlAiJobUnitOfWork.mark_side_effect

    def die_on_quarantine(self: SqlAiJobUnitOfWork, lease: Any, now: Any) -> bool:
        if lease.message_id.startswith("qtn_"):
            raise _Crash()  # the sink applied the quarantine, the holder dies before marking
        return original(self, lease, now)

    monkeypatch.setattr(SqlAiJobUnitOfWork, "mark_side_effect", die_on_quarantine)
    with pytest.raises(_Crash):
        rig.service.deliver_side_effects(owner="crashing")
    monkeypatch.setattr(SqlAiJobUnitOfWork, "mark_side_effect", original)
    (pending,) = _pending(rig)
    assert pending.kind == "quarantine" and pending.lease_owner == "crashing"
    assert b5.applied_quarantines(rig.engine) == [pending.event_id]
    epoch_applied = rig.base.owner.epoch(scope)
    assert epoch_applied is not None and epoch_before is not None and epoch_applied > epoch_before
    rig.clock.advance(milliseconds=LEASE_MS)  # the dead holder's lease expires
    assert rig.service.deliver_side_effects(owner="restarted") == 1
    assert _pending(rig) == []
    assert b5.applied_quarantines(rig.engine) == [pending.event_id]  # stored id: sink no-op
    assert rig.base.owner.epoch(scope) == epoch_applied  # artifact state changed only once


def test_stale_side_effect_lease_holder_is_a_no_op(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    rig.service.create_job(s.command())
    lease = rig.deps.dispatch_policy.lease
    with rig.base.repository.transaction() as tx:
        (old,) = tx.claim_side_effects("holder_a", rig.clock.now(), lease, 10)
    rig.clock.advance(milliseconds=LEASE_MS)
    with rig.base.repository.transaction() as tx:
        (new,) = tx.claim_side_effects("holder_b", rig.clock.now(), lease, 10)
    assert new.lease.generation == old.lease.generation + 1
    with rig.base.repository.transaction() as tx:
        assert not tx.mark_side_effect(old.lease, rig.clock.now())
        assert not tx.release_outbox(old.lease, "LATE")
        assert tx.mark_side_effect(new.lease, rig.clock.now())
    (row,) = b5.outbox_rows(rig.engine, "audit")
    assert row.delivered_at is not None and row.lease_owner is None


def test_rolled_back_round_and_foreign_lineage_produce_no_quarantine(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    _, message, token = _started(rig)
    own = b5.success_claim(rig.base.owner, message, moderation=Moderation.UNSAFE)
    stranger = DispatchMessage("msg_foreign", "job_foreign", "att_foreign", 1, message.job_type,
                               message.request_ref)
    foreign = b5.register_output(rig.base.owner, stranger, "foreign")
    claim = replace(own, outputs=(*own.outputs, foreign))
    scope = fx.eligibility_scope(ORG, s.REQUESTS[0])

    def bump(call: int) -> None:
        if call == 1:  # owner change between precheck and write: the first round rolls back
            rig.base.owner.change(scope, {"eligible": True}, notice_id=None)

    service = rig.with_ports(
        eligibility=s.HookedEligibility(fx.FixtureEligibility(rig.base.owner), bump)
    )
    receipt = service.accept_completion(token, claim)
    assert receipt.authoritative and receipt.reason_code == "UNSAFE_CONTENT"
    (row,) = b5.outbox_rows(rig.engine, "quarantine")  # only the committed round's intent
    assert row.payload["artifact_refs"] == [own.outputs[0].artifact_ref]
    assert b5.applied_quarantines(rig.engine) == [row.event_id]
    found = rig.base.owner.read(fx.artifact_scope(foreign.artifact_ref))
    assert found is not None and found[0].get("quarantine_reason") is None


def test_side_effect_delivery_never_touches_attempt_dispatch_bookkeeping(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    job_id, message, token = _started(rig)
    rig.service.accept_completion(token, b5.success_claim(rig.base.owner, message))

    def dispatch() -> list[Any]:
        with rig.engine.connect() as connection:
            return list(connection.execute(
                select(t.attempt.c.attempt_id, t.attempt.c.dispatched_at,
                       t.attempt.c.dispatch_count).where(t.attempt.c.job_id == job_id)
            ).all())

    before = dispatch()
    assert rig.service.deliver_side_effects() > 0
    assert dispatch() == before


def test_failing_audit_backlog_never_starves_quarantine_on_sql(db: URL) -> None:
    """B5-R01 on the real adapter: more failing audit rows than one claim page sit before a
    pending quarantine; only the artifact sink recovers."""

    rig = b5.build_b5_rig(db)
    policy = replace(FIXTURE_DISPATCH_POLICY, claim_limit=3)
    for index in range(4):
        b5.eligible(rig, f"req_bl_{index}")
        rig.service.create_job(s.command(key=f"bl_{index}", request=f"req_bl_{index}"))
    _, message, token = _started(rig)
    claim = b5.success_claim(rig.base.owner, message, moderation=Moderation.UNSAFE)
    down = rig.with_ports(audit=b5.FailingAuditSink(),
                          artifacts=_DownArtifacts(fx.FixtureArtifacts(rig.base.owner)))
    assert down.accept_completion(token, claim).authoritative
    audits = [row for row in _pending(rig) if row.kind == "audit"]
    (quarantine,) = [row for row in _pending(rig) if row.kind == "quarantine"]
    assert len(audits) > policy.claim_limit  # the failing prefix is longer than a page
    audit_down = b5.FailingAuditSink()
    recovering = rig.with_ports(audit=audit_down, dispatch_policy=policy)
    assert recovering.deliver_side_effects(owner="pass_1") == 1
    assert b5.applied_quarantines(rig.engine) == [quarantine.event_id]
    assert sorted(row.event_id for row in _pending(rig)) == sorted(r.event_id for r in audits)
    assert audit_down.calls == len(audits)  # every failing row tried once, then released
    assert all(row.lease_owner is None for row in _pending(rig))
    assert recovering.deliver_side_effects(owner="pass_2") == 0  # finite, no duplicate effect
    assert b5.applied_quarantines(rig.engine) == [quarantine.event_id]
    healthy = rig.with_ports(dispatch_policy=policy)
    assert healthy.deliver_side_effects(owner="pass_3") == len(audits)  # audit recovered
    assert _pending(rig) == []


def test_side_effect_delivery_has_a_finite_budget_under_new_sql_arrivals(db: URL) -> None:
    """Count on the real adapter excludes dispatch/delivered rows; newly committed work
    cannot keep one invocation alive indefinitely. No service/DB clock comparison is used."""

    rig = b5.build_b5_rig(db)
    for index in range(2):
        request = f"req_producer_{index}"
        b5.eligible(rig, request)
        rig.service.create_job(s.command(key=f"producer_{index}", request=request))
    with rig.base.repository.transaction() as tx:
        assert tx.pending_side_effects_count() == 2  # two dispatch rows are excluded
    initial = {row.event_id for row in _pending(rig)}
    calls: list[str] = []

    class ProducingAuditSink:
        def record(self, event: AuditEvent) -> None:
            calls.append(event.event_id)
            assert len(calls) <= len(initial), "delivery chased arrivals beyond its budget"
            rig.audit_sink.record(event)
            rig.clock.advance(seconds=1)
            event_id = sha256(f"producer_arrival_{len(calls)}".encode()).hexdigest()
            arrived = AuditEvent("job.probe", ORG, None, None, event_id=event_id)
            with rig.base.repository.transaction() as tx:
                tx.add_audit_intent(arrived.event_id, arrived)

    policy = replace(FIXTURE_DISPATCH_POLICY, claim_limit=2)
    service = rig.with_ports(audit=ProducingAuditSink(), dispatch_policy=policy)
    assert service.deliver_side_effects() == len(initial)
    assert set(calls) == initial
    with rig.base.repository.transaction() as tx:
        assert tx.pending_side_effects_count() == len(initial)  # delivered rows excluded
    healthy = rig.with_ports(dispatch_policy=policy)
    assert healthy.deliver_side_effects() == len(initial)
    with rig.base.repository.transaction() as tx:
        assert tx.pending_side_effects_count() == 0
    assert healthy.deliver_side_effects() == 0
