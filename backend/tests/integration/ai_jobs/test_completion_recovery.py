"""BE2-01 Phase B batch B5: authoritative completion on PostgreSQL (B-05, B-08a, Δ9/Δ15).

Concurrent identical/conflicting completions, an injected failure at each write boundary of a
job-changing completion, and the bounded provider/completion window (no same-claim recovery).
ASSUMED_CONTRACT owner fixture and component sinks; real HMAC capability; synthetic data.
``requires_postgres``; without PostgreSQL the tests skip: NOT_RUN, never PASS.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import b3_support as s
import b5_support as b5
import pytest
from sketch2life.application.services.ai_jobs import FIXTURE_RETRY_POLICY, AiJobError
from sketch2life.domain.ai_jobs.completion import Moderation
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobUnitOfWork
from sqlalchemy import func, select
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres
TIMEOUT = 30


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


def _started(rig: b5.B5Rig) -> tuple[str, Any, str]:
    created = rig.service.create_job(s.command())
    token = rig.capability(created.job_id)
    message = b5.message_for(rig, created.job_id)
    assert rig.service.start_attempt(token, created.job_id, message.attempt_id).started
    return created.job_id, message, token


def _count(rig: b5.B5Rig, table: Any, *where: Any) -> int:
    with rig.engine.connect() as connection:
        return int(connection.execute(select(func.count()).select_from(table).where(*where))
                   .scalar_one())


def _snapshot(rig: b5.B5Rig, job_id: str) -> tuple[Any, ...]:
    return (
        rig.base.job(job_id),
        _count(rig, t.completion_receipt),
        _count(rig, t.outbox, t.outbox.c.kind == "audit"),
        _count(rig, t.outbox, t.outbox.c.kind == "quarantine"),
        b5.applied_quarantines(rig.engine),
        len(rig.audit_sink.applied()),
    )


@pytest.mark.parametrize("conflicting", [False, True])
def test_concurrent_completions_have_one_authoritative_winner(db: URL, conflicting: bool) -> None:
    hook, ready, release = b5.pause_first_write()
    armed = {"on": False}

    def before_commit(uow: SqlAiJobUnitOfWork) -> None:
        if armed["on"]:  # only the completion writes, not the setup
            hook(uow)

    rig = b5.build_b5_rig(db, before_commit=before_commit)
    job_id, message, token = _started(rig)
    winner_claim = b5.success_claim(rig.base.owner, message, label="first")
    other_claim = (b5.success_claim(rig.base.owner, message, label="second")
                   if conflicting else winner_claim)
    armed["on"] = True
    first, first_box = b5.run_thread(lambda: rig.service.accept_completion(token, winner_claim))
    assert ready.wait(TIMEOUT)  # winner holds the job row lock, not committed yet
    second, second_box = b5.run_thread(lambda: rig.service.accept_completion(token, other_claim))
    b5.wait_for_lock_waiters(rig.engine)
    release.set()
    first.join(TIMEOUT)
    second.join(TIMEOUT)
    (status, receipt) = first_box[0]
    assert status == "ok" and receipt.authoritative
    if conflicting:
        (status, error) = second_box[0]
        assert status == "error" and isinstance(error, AiJobError)
        assert error.code == "COMPLETION_CONFLICT"
        conflicts = [row for row in b5.outbox_rows(rig.engine, "audit")
                     if row.payload["event_type"] == "job.completion_conflict"]
        assert len(conflicts) == 1  # durable incident, receipt untouched
    else:
        assert second_box[0] == ("ok", receipt)  # identical replay: the same receipt
    assert _count(rig, t.completion_receipt) == 1
    completion = [row for row in b5.outbox_rows(rig.engine, "audit")
                  if row.payload["event_type"] == "job.completion"]
    assert len(completion) == 1
    assert rig.base.job(job_id).state is JobState.SUCCEEDED


@pytest.mark.parametrize(
    "boundary",
    ["cas_job", "put_completion_receipt", "add_quarantine_intent", "add_audit_intent",
     "before_commit"],
)
def test_failure_at_each_completion_boundary_leaves_no_partial_rows(
    db: URL, monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    fail = {"on": False}

    def before_commit(uow: SqlAiJobUnitOfWork) -> None:
        if fail["on"] and boundary == "before_commit" and uow.writes:
            raise RuntimeError("injected commit failure")

    rig = b5.build_b5_rig(db, before_commit=before_commit)
    job_id, message, token = _started(rig)
    claim = b5.success_claim(rig.base.owner, message, moderation=Moderation.UNSAFE)
    before = _snapshot(rig, job_id)
    if boundary != "before_commit":
        original = getattr(SqlAiJobUnitOfWork, boundary)

        def failing(self: SqlAiJobUnitOfWork, *args: Any, **kwargs: Any) -> Any:
            original(self, *args, **kwargs)  # the statement ran, then the boundary fails
            if fail["on"]:
                raise RuntimeError(f"injected failure after {boundary}")

        monkeypatch.setattr(SqlAiJobUnitOfWork, boundary, failing)
    fail["on"] = True
    with pytest.raises(RuntimeError, match="injected"):
        rig.service.accept_completion(token, claim)
    fail["on"] = False
    assert _snapshot(rig, job_id) == before  # nothing partial, no sink effect
    receipt = rig.service.accept_completion(token, claim)
    assert receipt.authoritative and receipt.reason_code == "UNSAFE_CONTENT"
    assert rig.base.job(job_id).state is JobState.BLOCKED_UNSAFE
    assert len(b5.outbox_rows(rig.engine, "quarantine")) == 1
    assert len(b5.applied_quarantines(rig.engine)) == 1


def test_uncommitted_provider_output_gets_no_same_claim_recovery(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    job_id, first, token = _started(rig)
    late = b5.success_claim(rig.base.owner, first, label="orphan")  # output exists, no commit
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    assert rig.service.expire_overdue_attempts() == (job_id,)
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    assert rig.service.run_due_retries() == (job_id,)
    second = rig.base.job(job_id).active_attempt
    assert second.attempt_id != first.attempt_id
    receipt = rig.service.accept_completion(token, late)  # attempt-1 token is still live
    assert not receipt.authoritative and receipt.reason_code == "ATTEMPT_SUPERSEDED"
    assert _count(rig, t.completion_receipt, t.completion_receipt.c.attempt_id
                  == first.attempt_id) == 0
    (quarantine,) = b5.outbox_rows(rig.engine, "quarantine")
    assert quarantine.payload["artifact_refs"] == [late.outputs[0].artifact_ref]
    found = rig.base.owner.read(fx.artifact_scope(late.outputs[0].artifact_ref))
    assert found is not None and found[0]["quarantine_reason"] == "ATTEMPT_SUPERSEDED"
    job = rig.base.job(job_id)
    assert job.state is JobState.QUEUED and job.active_attempt.attempt_id == second.attempt_id
