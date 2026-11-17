"""BE2-01 Phase B batch B5: real HMAC worker capability through real Redis/RQ and PostgreSQL
(B-05e, B-10c, Δ8/Δ14) and worker process restart / duplicate receive (B-04a, B-06a/b).

One ephemeral HMAC key per test run, shared with worker child processes through the spawn
pipe only. Owner decisions and sinks come from the ASSUMED_CONTRACT fixture; the provider is a
fake. ``requires_postgres``; without PostgreSQL or Redis the tests skip: NOT_RUN, never PASS.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import b3_support as s
import b5_support as b5
import pytest
from rq.job import Job
from sketch2life.application.services.ai_jobs import (
    FIXTURE_DISPATCH_POLICY,
    FIXTURE_RETRY_POLICY,
    AiJobError,
)
from sketch2life.domain.ai_jobs.completion import CompletionClaim, OutcomeKind
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.infrastructure.ai_jobs.fakes import FakeProvider
from sketch2life.infrastructure.ai_jobs.rq_queue import (
    RedactingSimpleWorker,
    RqDispatchQueue,
    envelope_from_args,
)
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.ai_jobs.worker import DispatchWorker, install_worker
from sketch2life.infrastructure.ai_jobs.worker_capability import HmacCapabilityVerifier
from sqlalchemy import func, select
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


@pytest.fixture
def rq_queue() -> Iterator[RqDispatchQueue]:
    yield from b5.isolated_queue()


@pytest.fixture
def logs(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture every record at DEBUG. Alembic's fileConfig disables pre-existing loggers, so
    re-enable them for the test; otherwise RQ/app records would be silently dropped."""

    disabled = [
        logger
        for logger in logging.root.manager.loggerDict.values()
        if isinstance(logger, logging.Logger) and logger.disabled
    ]
    for logger in disabled:
        logger.disabled = False
    try:
        with caplog.at_level(logging.DEBUG):
            yield caplog
    finally:
        for logger in disabled:
            logger.disabled = True


def _queued_tokens(queue: RqDispatchQueue) -> list[tuple[dict[str, object], str]]:
    """Payload and capability of each queued RQ job (read from Redis, as the worker would)."""

    connection = queue.queue.connection
    queued = []
    for job_id in queue.queue.job_ids:
        payload, capability = Job.fetch(job_id, connection=connection).args
        queued.append((payload, capability))
    return queued


def _assert_absent(token: str, rig: b5.B5Rig, logs: pytest.LogCaptureFixture) -> None:
    assert token not in b5.sql_text(rig.engine)
    for record in logs.records:
        rendered = " ".join(str(v) for v in (record.getMessage(), record.args, vars(record)))
        assert token not in rendered


def _burst(rig: b5.B5Rig, queue: RqDispatchQueue, worker: DispatchWorker) -> None:
    install_worker(worker)
    try:
        RedactingSimpleWorker([queue.queue], connection=queue.queue.connection).work(burst=True)
    finally:
        install_worker(None)


def test_hmac_capability_reaches_the_worker_only_through_rq_and_completes_the_job(
    db: URL, rq_queue: RqDispatchQueue, logs: pytest.LogCaptureFixture
) -> None:
    rig = b5.build_b5_rig(db)
    service = rig.with_ports(queue=rq_queue)
    created = service.create_job(s.command())
    assert service.dispatch_outbox() == 1
    ((payload, token),) = _queued_tokens(rq_queue)
    verified = HmacCapabilityVerifier(rig.key, rig.clock).verify(token)
    attempt_id = rig.base.job(created.job_id).active_attempt.attempt_id
    assert verified is not None and (verified.job_id, verified.attempt_id) == (
        created.job_id, attempt_id
    )
    assert "capability" not in payload and token not in repr(payload)
    provider = FakeProvider(lambda m: b5.success_claim(rig.base.owner, m))
    _burst(rig, rq_queue, DispatchWorker(service, provider))
    settled = rig.base.job(created.job_id)
    assert settled.state is JobState.SUCCEEDED and provider.calls[created.job_id] == 1
    assert rq_queue.queue.count == 0
    _assert_absent(token, rig, logs)  # SQL rows, receipts, audit/quarantine, sinks, logs
    events = [event_type for _, event_type, _ in rig.audit_sink.applied()]
    assert "job.completion" in events and "job.created" in events


def test_rq_failure_path_never_logs_the_capability(
    db: URL, rq_queue: RqDispatchQueue, logs: pytest.LogCaptureFixture
) -> None:
    rig = b5.build_b5_rig(db)
    token = rig.issuer.issue("job_synthetic", "att_synthetic", rig.clock.now())
    rq_queue.queue.enqueue("b5_support.explode", {"message_id": "msg_x"}, token,
                           description="msg_x", result_ttl=0, failure_ttl=60)
    RedactingSimpleWorker([rq_queue.queue], connection=rq_queue.queue.connection).work(
        burst=True
    )
    errors = [rec for rec in logs.records if rec.name.startswith("rq") and rec.levelno >= 40]
    assert errors  # the failure was logged by RQ ...
    _assert_absent(token, rig, logs)  # ... without the capability in any record field


def test_cross_attempt_wrong_job_and_expired_tokens_are_denied_on_sql(db: URL) -> None:
    rig = b5.build_b5_rig(db)
    created = rig.service.create_job(s.command())
    first = rig.base.job(created.job_id).active_attempt
    token_1 = rig.capability(created.job_id)
    assert rig.service.start_attempt(token_1, created.job_id, first.attempt_id).started
    pinned = first.request_ref
    rig.service.accept_completion(
        token_1,
        CompletionClaim(created.job_id, first.attempt_id, pinned.request_revision,
                        pinned.input_hash, pinned.context_revision, OutcomeKind.FAILURE,
                        failure_code="PROVIDER_UNAVAILABLE", retryable=True),
    )
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    assert rig.service.run_due_retries() == (created.job_id,)
    second = rig.base.job(created.job_id).active_attempt
    before = rig.base.job(created.job_id)
    other = rig.service.create_job(s.command(key="idem_other", request=s.REQUESTS[1]))
    for token, job_id, attempt in (
        (token_1, created.job_id, second.attempt_id),  # attempt A token, attempt B
        (rig.capability(other.job_id), created.job_id, second.attempt_id),  # wrong job
    ):
        with pytest.raises(AiJobError) as error:
            rig.service.start_attempt(token, job_id, attempt)
        assert error.value.code == "WORKER_CAPABILITY_INVALID"
    token_2 = rig.capability(created.job_id)
    rig.clock.advance(milliseconds=FIXTURE_DISPATCH_POLICY.capability_ttl_ms)
    with pytest.raises(AiJobError):
        rig.service.start_attempt(token_2, created.job_id, second.attempt_id)  # expired
    assert rig.base.job(created.job_id) == before


def test_worker_dies_after_receive_then_restarted_worker_completes_the_same_attempt(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    rig = b5.build_b5_rig(db)
    service = rig.with_ports(queue=rq_queue)
    created = service.create_job(s.command())
    attempt_id = rig.base.job(created.job_id).active_attempt.attempt_id
    assert service.dispatch_outbox() == 1
    assert b5.spawn_worker(db, rq_queue, rig.key, "die_before_start") == (
        b5.EXIT_DIED_BEFORE_START
    )
    lost = rig.base.job(created.job_id)
    assert lost.state is JobState.QUEUED and lost.active_attempt.started_at is None
    rig.clock.advance(milliseconds=FIXTURE_DISPATCH_POLICY.start_timeout_ms)
    assert service.recover_unstarted_dispatches() == ((created.job_id, "republished"),)
    assert service.dispatch_outbox() == 1  # fresh capability, same attempt
    assert b5.spawn_worker(db, rq_queue, rig.key, "normal") == b5.EXIT_DONE  # restarted
    done = rig.base.job(created.job_id)
    assert done.state is JobState.SUCCEEDED
    assert [a.attempt_id for a in done.attempts] == [attempt_id]


def test_duplicate_receive_after_completion_never_reaches_the_provider(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    rig = b5.build_b5_rig(db)
    service = rig.with_ports(queue=rq_queue)
    created = service.create_job(s.command())
    assert service.dispatch_outbox() == 1
    ((payload, token),) = _queued_tokens(rq_queue)
    assert b5.spawn_worker(db, rq_queue, rig.key, "normal") == b5.EXIT_DONE
    outputs = _child_outputs(rig)
    # The fake provider re-registers the same artifact scope on every run, and each owner
    # change bumps that scope's epoch: unchanged epochs prove the provider did not run again.
    epochs = {scope: rig.base.owner.epoch(scope) for scope in outputs}
    rq_queue.enqueue(envelope_from_args(payload, token))  # broker-level duplicate delivery
    assert b5.spawn_worker(db, rq_queue, rig.key, "normal") == b5.EXIT_DONE
    assert rig.base.job(created.job_id).state is JobState.SUCCEEDED
    assert _child_outputs(rig) == outputs
    assert {scope: rig.base.owner.epoch(scope) for scope in outputs} == epochs
    with rig.engine.connect() as connection:
        receipts = connection.execute(select(func.count()).select_from(t.completion_receipt))
        assert receipts.scalar_one() == 1


def test_provider_output_without_completion_is_recovered_only_by_policy_retry(
    db: URL, rq_queue: RqDispatchQueue
) -> None:
    rig = b5.build_b5_rig(db)
    service = rig.with_ports(queue=rq_queue)
    created = service.create_job(s.command())
    first = rig.base.job(created.job_id).active_attempt.attempt_id
    assert service.dispatch_outbox() == 1
    assert b5.spawn_worker(db, rq_queue, rig.key, "die_after_provider") == (
        b5.EXIT_DIED_AFTER_PROVIDER
    )
    assert _child_outputs(rig)  # the provider produced output ...
    with rig.engine.connect() as connection:  # ... but no completion was committed
        assert connection.execute(
            select(func.count()).select_from(t.completion_receipt)
        ).scalar_one() == 0
    assert rig.base.job(created.job_id).state is JobState.RUNNING
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    assert service.expire_overdue_attempts() == (created.job_id,)
    failed = rig.base.job(created.job_id)
    assert failed.state is JobState.FAILED_RETRYABLE and failed.failure is not None
    assert failed.failure.code == "PROVIDER_TIMEOUT"
    rig.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    assert service.run_due_retries() == (created.job_id,)
    retried = rig.base.job(created.job_id)
    assert retried.active_attempt.attempt_number == 2 and retried.active_attempt.attempt_id != first


def _child_outputs(rig: b5.B5Rig) -> list[str]:
    with rig.engine.connect() as connection:
        return sorted(
            connection.execute(
                select(fx.decision.c.fence_scope).where(
                    fx.decision.c.fence_scope.like("artifact:artifact_child_%")
                )
            ).scalars()
        )
