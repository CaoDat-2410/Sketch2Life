"""BE2-01 Phase B batch B3: SQL repository / unit of work on real PostgreSQL.

Acceptance (FEAT-044 PHASE_B_PLAN.md rev3 §8): B-07 durable semantic scope isolation and
CAS/unique typing, B-08(a) no partial state on failure at any create/cancel write or commit
boundary, B-08(b) B3 part: no accepted create/cancel without its durable audit intent in the
same commit. Owner decisions come from the ASSUMED_CONTRACT fixture. Every test here is
``requires_postgres``; skipped means NOT_RUN, never PASS.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import timedelta

import b3_support as s
import pytest
from sketch2life.application.ports.ai_jobs import (
    CommandReceipt,
    CommandScopeKey,
    JobRevisionConflict,
    SemanticRequestKey,
    UniqueConflict,
)
from sketch2life.application.services.ai_jobs import (
    FIXTURE_RETRY_POLICY,
    AiJobError,
    CancelJobCommand,
)
from sketch2life.domain.ai_jobs import model as jobs
from sketch2life.domain.ai_jobs.model import (
    JobProgress,
    JobScope,
    ProgressKind,
    ResultDisposition,
    ResultRef,
)
from sketch2life.infrastructure.ai_jobs.harness import FIXTURE_START, ORG, TEACHER, request_ref
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobUnitOfWork
from sqlalchemy import select
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres

ZERO = {
    "job": 0,
    "attempt": 0,
    "semantic_request": 0,
    "command_receipt": 0,
    "completion_receipt": 0,
    "outbox_dispatch": 0,
    "outbox_audit": 0,
}


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


def _scope(session_id: str | None = "session_rt") -> JobScope:
    return JobScope(ORG, session_id, ("child_rt_a", "child_rt_b"), "purpose_rt", "target_rt")


def test_job_and_attempts_round_trip_through_every_lifecycle_shape(db: URL) -> None:
    rig = s.build_rig(db)
    now = FIXTURE_START
    created = jobs.create_job(
        job_id="job_rt_1",
        attempt_id="att_rt_1",
        job_type="sketch_assistance",
        scope=_scope(None),
        request_ref=request_ref("req_rt"),
        correlation_id="corr_rt",
        retry_policy=FIXTURE_RETRY_POLICY,
        now=now,
    )
    started = jobs.start_attempt(created, "att_rt_1", now + timedelta(seconds=1))
    progressed = jobs.report_progress(
        started, "att_rt_1", JobProgress(ProgressKind.PERCENTAGE, 37.5), now + timedelta(seconds=2)
    )
    failed = jobs.record_failure(
        progressed,
        "att_rt_1",
        code="PROVIDER_UNAVAILABLE",
        retryable=True,
        public_message="temporary",
        now=now + timedelta(seconds=3),
    )
    requeued = jobs.requeue_for_retry(
        failed, new_attempt_id="att_rt_2", now=failed.retry_not_before or now
    )
    restarted = jobs.start_attempt(requeued, "att_rt_2", now + timedelta(seconds=10))
    succeeded = jobs.succeed(
        restarted,
        "att_rt_2",
        result_refs=(ResultRef("artifact_rt", "c" * 64, "sketch_assistance:att_rt_2"),),
        disposition=ResultDisposition.STALE,
        now=now + timedelta(seconds=11),
        lineage_note="source context 1 superseded by 2",
    )
    with rig.repository.transaction() as tx:
        tx.insert_job(created)
    previous = created
    for state in (started, progressed, failed, requeued, restarted, succeeded):
        with rig.repository.transaction() as tx:
            tx.cas_job(expected_revision=previous.job_revision, job=state)
        previous = state
        # A different engine/connection ("restart") reads back the identical aggregate.
        assert s.build_rig(db).job(state.job_id) == state


def test_cas_and_plain_inserts_are_typed_and_roll_back_whole(db: URL) -> None:
    rig = s.build_rig(db)
    job = jobs.create_job(
        job_id="job_cas_1",
        attempt_id="att_cas_1",
        job_type="sketch_assistance",
        scope=_scope(),
        request_ref=request_ref("req_cas"),
        correlation_id="corr_cas",
        retry_policy=FIXTURE_RETRY_POLICY,
        now=FIXTURE_START,
    )
    with rig.repository.transaction() as tx:
        tx.insert_job(job)
    moved = jobs.start_attempt(job, "att_cas_1", FIXTURE_START)
    # The stored revision is 1: a write expecting 2 must be refused by the UPDATE itself.
    with pytest.raises(JobRevisionConflict), rig.repository.transaction() as tx:
        tx.cas_job(
            expected_revision=job.job_revision + 1,
            job=replace(moved, job_revision=job.job_revision + 2),
        )
    with pytest.raises(UniqueConflict) as conflict, rig.repository.transaction() as tx:
        tx.insert_job(
            replace(
                job,
                job_id="job_cas_2",
                attempts=(replace(job.attempts[0], attempt_id="att_cas_2"),),
            )
        )
        tx.insert_job(job)
    assert conflict.value.kind == "job"
    key = CommandScopeKey(ORG, TEACHER.principal_id, "CreateAiJob", "target_rt", "k")
    receipt = CommandReceipt(key, "a" * 64, job.job_id, "created", 1, FIXTURE_START)
    semantic = SemanticRequestKey(
        ORG, "sketch_assistance", "req_cas", 1, "b" * 64, 1, "target_rt", "purpose_rt", None, ("x",)
    )
    with rig.repository.transaction() as tx:
        tx.put_command_receipt(receipt)
        tx.put_semantic(semantic, job.job_id)
    writes: tuple[tuple[Callable[[SqlAiJobUnitOfWork], None], str], ...] = (
        (lambda tx: tx.put_command_receipt(receipt), "command_receipt"),
        (lambda tx: tx.put_semantic(semantic, job.job_id), "semantic_request"),
    )
    for write, kind in writes:
        with pytest.raises(UniqueConflict) as conflict, rig.repository.transaction() as tx:
            tx.cas_job(expected_revision=job.job_revision, job=moved)
            write(tx)
        assert conflict.value.kind == kind
    # Every failed transaction above rolled back as a whole: job_cas_2 and the start are gone.
    assert rig.job(job.job_id) == job
    assert s.counts(rig.engine)["job"] == 1


def test_concurrent_cas_lets_exactly_one_writer_win(db: URL) -> None:
    rig = s.build_rig(db)
    job = jobs.create_job(
        job_id="job_race_cas",
        attempt_id="att_race_cas",
        job_type="sketch_assistance",
        scope=_scope(),
        request_ref=request_ref("req_race_cas"),
        correlation_id="corr_race_cas",
        retry_policy=FIXTURE_RETRY_POLICY,
        now=FIXTURE_START,
    )
    with rig.repository.transaction() as tx:
        tx.insert_job(job)
    started = jobs.start_attempt(job, "att_race_cas", FIXTURE_START)
    cancelled = jobs.cancel(
        job, reason_code="CANCELLED_BY_TEACHER", public_message="x", now=FIXTURE_START
    )
    wrote = threading.Event()
    release = threading.Event()
    conflicts: list[JobRevisionConflict] = []

    def first() -> None:
        with rig.repository.transaction() as tx:
            tx.cas_job(expected_revision=1, job=started)
            wrote.set()
            assert release.wait(30)

    def second() -> None:
        try:
            with rig.repository.transaction() as tx:
                tx.cas_job(expected_revision=1, job=cancelled)
        except JobRevisionConflict as error:
            conflicts.append(error)

    writer = threading.Thread(target=first)
    writer.start()
    try:
        assert wrote.wait(30)
        loser = threading.Thread(target=second)
        loser.start()
        loser.join(1.0)
        # READ COMMITTED: the second UPDATE waits on the uncommitted row version.
        assert loser.is_alive()
    finally:
        release.set()
        writer.join(30)
    loser.join(30)
    assert len(conflicts) == 1  # re-evaluated against revision 2 after the first commit
    assert rig.job(job.job_id) == started


@pytest.mark.parametrize(
    "stage",
    [
        "insert_job",
        "put_semantic",
        "put_command_receipt",
        "add_outbox",
        "add_audit_intent",
        "before_commit",
    ],
)
def test_failure_at_each_create_boundary_leaves_nothing(
    db: URL, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    def fail(uow: SqlAiJobUnitOfWork) -> None:
        if uow.writes:  # the write transaction's commit boundary, not the read round
            raise RuntimeError("injected storage failure")

    rig = s.build_rig(db, before_commit=fail if stage == "before_commit" else None)
    if stage != "before_commit":
        original = getattr(SqlAiJobUnitOfWork, stage)

        def wrapped(self: SqlAiJobUnitOfWork, *args: object, **kwargs: object) -> None:
            original(self, *args, **kwargs)
            raise RuntimeError("injected storage failure")

        monkeypatch.setattr(SqlAiJobUnitOfWork, stage, wrapped)
    with pytest.raises(RuntimeError, match="injected"):
        rig.service.create_job(s.command())
    assert s.counts(rig.engine) == ZERO
    monkeypatch.undo()
    # The same command then succeeds once with its full durable bundle (B-08b, B3 part).
    result = s.build_rig(db).service.create_job(s.command())
    assert result.outcome == "created" and not result.replayed
    assert s.counts(rig.engine) == {
        **ZERO,
        "job": 1,
        "attempt": 1,
        "semantic_request": 1,
        "command_receipt": 1,
        "outbox_dispatch": 1,
        "outbox_audit": 1,
    }


def test_create_bundle_is_durable_token_free_and_records_held_fences(db: URL) -> None:
    rig = s.build_rig(db)
    result = rig.service.create_job(s.command())
    with rig.engine.connect() as connection:
        row = connection.execute(select(t.job).where(t.job.c.job_id == result.job_id)).one()
        outbox = connection.execute(select(t.outbox)).all()
        semantic = connection.execute(select(t.semantic_request)).one()
    grant = fx.grant_scope(ORG, TEACHER.principal_id)
    eligibility = fx.eligibility_scope(ORG, s.REQUESTS[0])
    assert row.accepted_fences == {
        grant: rig.owner.epoch(grant),
        eligibility: rig.owner.epoch(eligibility),
    }
    command = s.command()
    expected_key = SemanticRequestKey(
        ORG,
        command.job_type,
        command.request_ref.request_id,
        command.request_ref.request_revision,
        command.request_ref.input_hash,
        command.request_ref.context_revision,
        command.target_id,
        command.purpose_code,
        command.session_id,
        tuple(sorted(command.subject_refs)),
    )
    assert semantic.semantic_key_sha256 == expected_key.sha256()
    assert semantic.job_id == result.job_id
    kinds = sorted(r.kind for r in outbox)
    assert kinds == ["audit", "dispatch"]
    for message in outbox:
        assert not {"capability", "token", "worker_capability"} & set(message.payload)
        assert message.job_id == result.job_id
    audit = next(r for r in outbox if r.kind == "audit")
    assert audit.payload["event_type"] == "job.created" and len(audit.event_id) == 64


def test_cancel_commits_state_receipt_and_audit_together_or_nothing(db: URL) -> None:
    def fail(uow: SqlAiJobUnitOfWork) -> None:
        if uow.writes:
            raise RuntimeError("injected commit failure")

    rig = s.build_rig(db)
    created = rig.service.create_job(s.command())
    cancel = CancelJobCommand(TEACHER, "idem_cancel_1", created.job_id, created.job_revision)
    failing = s.build_rig(db, before_commit=fail)
    with pytest.raises(RuntimeError, match="injected"):
        failing.service.cancel_job(cancel)
    assert rig.job(created.job_id).state is jobs.JobState.QUEUED
    assert s.counts(rig.engine)["command_receipt"] == 1
    assert s.counts(rig.engine)["outbox_audit"] == 1
    result = rig.service.cancel_job(cancel)
    assert result.outcome == "cancelled"
    assert rig.job(created.job_id).state is jobs.JobState.CANCELLED
    assert s.counts(rig.engine)["command_receipt"] == 2
    assert s.counts(rig.engine)["outbox_audit"] == 2
    assert rig.service.cancel_job(cancel).replayed


@pytest.mark.parametrize(
    "variation",
    [
        {"target": "target_other"},
        {"purpose": "purpose_other"},
        {"session_id": None},
        {"session_id": "session_other"},
        {"subjects": ("child_fx_001", "child_fx_002")},
        {"job_type": "sketch_other"},
        {"request": s.REQUESTS[1]},
        {"context": 2},
    ],
)
def test_semantic_scope_isolation_is_durable(db: URL, variation: dict[str, object]) -> None:
    rig = s.build_rig(db)
    first = rig.service.create_job(s.command(key="iso_1"))
    other = rig.service.create_job(s.command(key="iso_2", **variation))  # type: ignore[arg-type]
    assert other.outcome == "created" and other.job_id != first.job_id
    # A restarted service (new engine) still deduplicates both scopes exactly.
    restarted = s.build_rig(db).service
    again_first = restarted.create_job(s.command(key="iso_3"))
    again_other = restarted.create_job(s.command(key="iso_4", **variation))  # type: ignore[arg-type]
    assert (again_first.outcome, again_first.job_id) == ("deduplicated", first.job_id)
    assert (again_other.outcome, again_other.job_id) == ("deduplicated", other.job_id)
    assert s.counts(rig.engine)["job"] == 2 and s.no_orphans(rig.engine)


def test_unsupported_owner_fence_contract_version_is_refused(db: URL) -> None:
    class WrongVersion(fx.FixtureFenceHold):
        contract_version = "OwnerFenceV0"

    rig = s.build_rig(db)
    rig.repository._owner_fences = WrongVersion
    with pytest.raises(RuntimeError, match="contract version"):
        rig.service.create_job(s.command())
    assert s.counts(rig.engine) == ZERO


def test_unresolved_unique_conflicts_return_typed_retryable_conflict(
    db: URL, monkeypatch: pytest.MonkeyPatch
) -> None:
    def always_conflict(self: SqlAiJobUnitOfWork, key: object, job_id: str) -> None:
        raise UniqueConflict("semantic_request")

    rig = s.build_rig(db)
    monkeypatch.setattr(SqlAiJobUnitOfWork, "put_semantic", always_conflict)
    with pytest.raises(AiJobError) as error:
        rig.service.create_job(s.command())
    assert (error.value.code, error.value.http_status, error.value.retryable) == (
        "IDEMPOTENCY_CONFLICT",
        409,
        True,
    )
    assert rig.repository.transactions == 4  # two bounded rounds of read + write
    assert s.counts(rig.engine) == ZERO
