"""BE2-01 Phase B batch B3, finding B3-R01: unlocked aggregate reads during start/retry.

A writer (``start_attempt`` or ``retry_job``) is paused just before its commit while it holds
the job row lock. An unlocked reader then reads the aggregate; a cursor hook on the reader lets
the writer commit right after the reader's first statement on ``ai_jobs.job`` and waits for that
commit. A read split across statements would then combine the old job row with the new attempt
rows (the reviewed torn read). The reader must instead return exactly the pre-commit version, and
its public projection must validate against the candidate wire contract. The unlocked reader
never waits on the writer's row lock, so the hook cannot deadlock. ``requires_postgres``;
skipped means NOT_RUN.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from typing import Any

import b3_support as s
import pytest
from sketch2life.application.ports.ai_jobs import PrincipalRole
from sketch2life.application.services.ai_jobs import FIXTURE_POLL_POLICY, project_job
from sketch2life.contracts.schemas.ai_jobs import AsyncJobViewV1
from sketch2life.domain.ai_jobs import model as jobs
from sketch2life.domain.ai_jobs.completion import CompletionClaim, OutcomeKind
from sketch2life.domain.ai_jobs.model import AiJob, JobState
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobUnitOfWork
from sqlalchemy import event
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres

TIMEOUT = 30


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


def _validated_view(rig: s.SqlRig, job: AiJob) -> AsyncJobViewV1:
    """The candidate polling path: projection, then the wire model the router serialises."""

    poll_after = jobs.poll_after_ms(job, FIXTURE_POLL_POLICY, rig.clock.now())
    view = project_job(job, PrincipalRole.TEACHER, False, poll_after)
    return AsyncJobViewV1.model_validate(view, strict=False)


def _read_while_writer_commits(
    db: URL, job_id: str, write: Callable[[s.SqlRig], Any], prepare: Callable[[s.SqlRig], None]
) -> tuple[AiJob, s.SqlRig]:
    ready = threading.Event()
    release = threading.Event()
    committed = threading.Event()
    failures: list[BaseException] = []

    def pause_before_commit(uow: SqlAiJobUnitOfWork) -> None:
        if uow.writes:  # the write transaction, holding the job row lock
            ready.set()
            assert release.wait(TIMEOUT)

    writer = s.build_rig(db, before_commit=pause_before_commit)
    prepare(writer)

    def run_writer() -> None:
        try:
            write(writer)
        except BaseException as error:  # surfaced by the main thread
            failures.append(error)
        finally:
            committed.set()

    reader = s.build_rig(db)
    fired: list[str] = []

    def commit_between_statements(*args: Any) -> None:
        statement = str(args[2])
        if not fired and "FROM ai_jobs.job" in statement:
            fired.append(statement)
            release.set()
            assert committed.wait(TIMEOUT)

    thread = threading.Thread(target=run_writer)
    thread.start()
    try:
        assert ready.wait(TIMEOUT), "writer never reached its commit boundary"
        event.listen(reader.engine, "after_cursor_execute", commit_between_statements)
        try:
            with reader.repository.transaction() as tx:
                observed = tx.get_job(job_id)
        finally:
            event.remove(reader.engine, "after_cursor_execute", commit_between_statements)
    finally:
        release.set()
        thread.join(TIMEOUT)
    assert not thread.is_alive() and not failures, failures
    assert fired, "reader statement hook never fired"
    assert observed is not None
    return observed, reader


def test_read_overlapping_start_commit_returns_one_coherent_version(db: URL) -> None:
    setup = s.build_rig(db)
    created = setup.service.create_job(s.command())
    before = setup.job(created.job_id)
    assert before.state is JobState.QUEUED and before.active_attempt.started_at is None

    observed, reader = _read_while_writer_commits(
        db,
        created.job_id,
        lambda w: w.service.start_attempt(
            w.capability(created.job_id, before.active_attempt.attempt_id),
            created.job_id,
            before.active_attempt.attempt_id,
        ),
        lambda w: None,
    )
    assert observed == before  # the snapshot predates the writer's commit
    _validated_view(reader, observed)
    after = reader.job(created.job_id)
    assert after.state is JobState.RUNNING and after.job_revision == before.job_revision + 1
    assert after.active_attempt.started_at is not None
    _validated_view(reader, after)


def test_read_overlapping_retry_commit_returns_one_coherent_version(db: URL) -> None:
    setup = s.build_rig(db)
    created = setup.service.create_job(s.command())
    attempt = setup.job(created.job_id).active_attempt
    capability = setup.capability(created.job_id)
    assert setup.service.start_attempt(capability, created.job_id, attempt.attempt_id).started
    pinned = attempt.request_ref
    setup.service.accept_completion(
        capability,
        CompletionClaim(
            job_id=created.job_id,
            attempt_id=attempt.attempt_id,
            expected_request_revision=pinned.request_revision,
            input_hash=pinned.input_hash,
            context_revision=pinned.context_revision,
            kind=OutcomeKind.FAILURE,
            failure_code="PROVIDER_UNAVAILABLE",
            retryable=True,
        ),
    )
    before = setup.job(created.job_id)
    assert before.state is JobState.FAILED_RETRYABLE and len(before.attempts) == 1
    assert before.retry_not_before is not None
    wait = int((before.retry_not_before - setup.clock.now()).total_seconds()) + 1

    def due(writer: s.SqlRig) -> None:
        writer.clock.advance(seconds=wait)  # writer clocks start at the same fixture instant

    observed, reader = _read_while_writer_commits(
        db, created.job_id, lambda w: w.service.retry_job(created.job_id, 1), due
    )
    assert observed == before  # old revision with exactly its own single attempt
    _validated_view(reader, observed)
    after = reader.job(created.job_id)
    assert after.state is JobState.QUEUED and after.job_revision == before.job_revision + 1
    assert [a.attempt_number for a in after.attempts] == [1, 2]
    _validated_view(reader, after)
