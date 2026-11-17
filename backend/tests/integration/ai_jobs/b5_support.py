"""Shared wiring for the BE2-01 Phase B batch B5 PostgreSQL/Redis tests (synthetic data only).

The service runs on ``SqlAiJobRepository`` with the ASSUMED_CONTRACT owner fixture, the real
HMAC capability issuer/verifier with one ephemeral key per test run, and the component audit
and artifact sinks (``owner_fence_fixture``), so side effects survive process restarts.

Worker child processes (spawn) receive the key, database URL and Redis endpoint as process
arguments through the multiprocessing pipe: the key is never written to disk, an environment
variable or a log. Children run ``RedactingSimpleWorker`` in burst mode over the test's own
``be2_b4_<random>`` queue and exit with a code that tells the parent what happened.
"""

from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import b3_support as s
from redis import Redis
from rq import Queue
from sketch2life.application.ports.ai_jobs import AuditEvent, DispatchMessage
from sketch2life.application.services.ai_jobs import AiJobDependencies, AiJobService
from sketch2life.domain.ai_jobs.completion import (
    CompletionClaim,
    Moderation,
    OutcomeKind,
    OutputRef,
)
from sketch2life.infrastructure.ai_jobs.fakes import FakeClock, FakeProvider
from sketch2life.infrastructure.ai_jobs.harness import ORG
from sketch2life.infrastructure.ai_jobs.rq_queue import RedactingSimpleWorker, RqDispatchQueue
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.ai_jobs.worker import DispatchWorker, install_worker
from sketch2life.infrastructure.ai_jobs.worker_capability import (
    CapabilityKey,
    HmacCapabilityIssuer,
    HmacCapabilityVerifier,
)
from sqlalchemy import Engine, select
from sqlalchemy.engine import URL

KEY_ID = "b5_test_run"
TESTS_DIR = str(Path(__file__).resolve().parent)

# Child exit codes (parent assertions).
EXIT_DONE = 0
EXIT_DIED_BEFORE_START = 17
EXIT_DIED_AFTER_PROVIDER = 18


def new_run_key() -> CapabilityKey:
    """One ephemeral HMAC key per test run (accepted Q6); never persisted or logged."""

    return CapabilityKey(KEY_ID, os.urandom(32))


@dataclass
class B5Rig:
    base: s.SqlRig
    service: AiJobService
    deps: AiJobDependencies
    key: CapabilityKey
    issuer: HmacCapabilityIssuer
    audit_sink: fx.FixtureAuditSink

    @property
    def engine(self) -> Engine:
        return self.base.engine

    @property
    def clock(self) -> FakeClock:
        return self.base.clock

    def with_ports(self, **changes: Any) -> AiJobService:
        values = {name: getattr(self.deps, name) for name in self.deps.__dataclass_fields__}
        values.update(changes)
        return AiJobService(AiJobDependencies(**values))

    def capability(self, job_id: str, attempt_id: str | None = None) -> str:
        if attempt_id is None:
            attempt_id = self.base.job(job_id).active_attempt.attempt_id
        return self.issuer.issue(job_id, attempt_id, self.clock.now())


def build_b5_rig(url: URL, key: CapabilityKey | None = None, **rig_options: Any) -> B5Rig:
    base = s.build_rig(url, **rig_options)
    key = key or new_run_key()
    issuer = HmacCapabilityIssuer(key)
    sink = fx.FixtureAuditSink(base.engine)
    values = {name: getattr(base.deps, name) for name in base.deps.__dataclass_fields__}
    values.update(
        capability_issuer=issuer,
        worker_capability=HmacCapabilityVerifier(key, base.clock),
        audit=sink,
    )
    deps = AiJobDependencies(**values)
    return B5Rig(base, AiJobService(deps), deps, key, issuer, sink)


def eligible(rig: B5Rig | s.SqlRig, request: str) -> None:
    owner = rig.base.owner if isinstance(rig, B5Rig) else rig.owner
    owner.set(fx.eligibility_scope(ORG, request), {"eligible": True})


def register_output(owner: fx.OwnerFixture, message: DispatchMessage, label: str) -> OutputRef:
    """Synthetic output owned by the message's job/attempt in the fixture artifact port."""

    ref = f"artifact_{label}_{message.attempt_id[-12:]}"
    digest = hashlib.sha256(f"synthetic:{label}:{message.attempt_id}".encode()).hexdigest()
    owner.set(
        fx.artifact_scope(ref),
        {
            "sha256": digest,
            "organization_id": ORG,
            "producer_job_id": message.job_id,
            "producer_attempt_id": message.attempt_id,
        },
    )
    return OutputRef(ref, digest)


def success_claim(
    owner: fx.OwnerFixture,
    message: DispatchMessage,
    *,
    label: str = "out",
    moderation: Moderation = Moderation.PASSED,
) -> CompletionClaim:
    ref = message.request_ref
    return CompletionClaim(
        message.job_id,
        message.attempt_id,
        ref.request_revision,
        ref.input_hash,
        ref.context_revision,
        OutcomeKind.SUCCESS,
        outputs=(register_output(owner, message, label),),
        moderation=moderation,
    )


def message_for(rig: B5Rig, job_id: str) -> DispatchMessage:
    job = rig.base.job(job_id)
    attempt = job.active_attempt
    return DispatchMessage("msg_direct", job_id, attempt.attempt_id, attempt.attempt_number,
                           job.job_type, attempt.request_ref)


def sql_text(engine: Engine) -> str:
    """Every row of the ai_jobs tables and the fixture sinks, as one text blob."""

    tables = (t.job, t.attempt, t.command_receipt, t.semantic_request, t.completion_receipt,
              t.cancellation_notice, t.outbox, fx.audit_applied, fx.quarantine_applied,
              fx.decision, fx.notice)
    with engine.connect() as connection:
        return "\n".join(repr(row) for table in tables
                         for row in connection.execute(select(table)).all())


def outbox_rows(engine: Engine, kind: str) -> list[Any]:
    with engine.connect() as connection:
        return list(
            connection.execute(
                select(t.outbox).where(t.outbox.c.kind == kind).order_by(t.outbox.c.message_id)
            ).all()
        )


def applied_quarantines(engine: Engine) -> list[str]:
    with engine.connect() as connection:
        return sorted(connection.execute(select(fx.quarantine_applied.c.event_id)).scalars())


class FailingAuditSink:
    """Audit sink that is down (crash-before-delivery window)."""

    def __init__(self) -> None:
        self.calls = 0

    def record(self, event: AuditEvent) -> None:
        self.calls += 1
        raise ConnectionError("audit sink unavailable")


# ------------------------------------------------------------------- RQ test job functions
def explode(payload: dict[str, Any], capability: str) -> None:
    """RQ job that fails with the capability in its message: exercises RQ's failure path."""

    raise RuntimeError(f"synthetic failure while holding {capability}")


# --------------------------------------------------------------------- worker child process
def _child_rig(url_text: str, key: CapabilityKey) -> tuple[AiJobService, Any]:
    from sqlalchemy.engine import make_url

    base = s.build_rig(make_url(url_text))
    values = {name: getattr(base.deps, name) for name in base.deps.__dataclass_fields__}
    values.update(
        worker_capability=HmacCapabilityVerifier(key, base.clock),
        capability_issuer=HmacCapabilityIssuer(key),
        audit=fx.FixtureAuditSink(base.engine),
    )
    return AiJobService(AiJobDependencies(**values)), base.owner


class _DieBeforeStart(DispatchWorker):
    def handle(self, envelope: Any) -> Any:
        sys.stdout.flush()
        os._exit(EXIT_DIED_BEFORE_START)


def worker_child(
    url_text: str,
    redis_host: str,
    redis_port: int,
    queue_name: str,
    key: CapabilityKey,
    mode: str,
) -> None:
    """Child process entry (spawn). ``mode``: ``normal`` | ``die_before_start`` |
    ``die_after_provider``. Never prints the key, the URL or a capability."""

    service, owner = _child_rig(url_text, key)

    def script(message: DispatchMessage) -> CompletionClaim:
        claim = success_claim(owner, message, label="child")
        if mode == "die_after_provider":
            os._exit(EXIT_DIED_AFTER_PROVIDER)  # provider output exists, completion never sent
        return claim

    provider = FakeProvider(script)
    worker = (_DieBeforeStart if mode == "die_before_start" else DispatchWorker)(service, provider)
    install_worker(worker)
    connection = Redis(host=redis_host, port=redis_port, socket_connect_timeout=2,
                       socket_timeout=5)
    RedactingSimpleWorker([Queue(queue_name, connection=connection)], connection=connection).work(
        burst=True
    )
    os._exit(EXIT_DONE)


def spawn_worker(
    url: URL, queue: RqDispatchQueue, key: CapabilityKey, mode: str, *, timeout: float = 60
) -> int:
    """Run one worker child to completion and return its exit code."""

    import multiprocessing

    if TESTS_DIR not in sys.path:
        sys.path.insert(0, TESTS_DIR)
    context = multiprocessing.get_context("spawn")
    connection = queue.queue.connection
    kwargs = connection.connection_pool.connection_kwargs
    process = context.Process(
        target=worker_child,
        args=(
            url.render_as_string(hide_password=False),
            kwargs["host"],
            int(kwargs.get("port", 6379)),
            queue.queue.name,
            key,  # the run key reaches the child only through the spawn pipe (pickled)
        ),
        kwargs={"mode": mode},
        daemon=True,
    )
    process.start()
    process.join(timeout)
    if process.is_alive():
        process.kill()
        process.join(5)
        raise AssertionError("worker child did not finish in time")
    assert process.exitcode is not None
    return process.exitcode



def wait_for_lock_waiters(engine: Engine, count: int = 1, timeout: float = 30) -> None:
    """Block until ``count`` backends of this database wait on a lock (deterministic race)."""

    import time

    from sqlalchemy import text

    deadline = time.monotonic() + timeout
    query = text(
        "SELECT count(*) FROM pg_stat_activity "
        "WHERE datname = current_database() AND wait_event_type = 'Lock'"
    )
    while time.monotonic() < deadline:
        with engine.connect() as connection:
            if int(connection.execute(query).scalar_one()) >= count:
                return
        time.sleep(0.05)
    raise AssertionError("no backend started waiting on the expected lock")


def pause_first_write(
    *, fail: bool = False
) -> tuple[Any, Any, Any]:
    """``before_commit`` hook that pauses (or fails) the first transaction that wrote rows.
    Returns ``(hook, ready, release)`` events."""

    import threading

    ready, release = threading.Event(), threading.Event()
    fired: list[bool] = []

    def hook(uow: Any) -> None:
        if uow.writes and not fired:
            fired.append(True)
            if fail:
                raise RuntimeError("injected commit failure")
            ready.set()
            assert release.wait(60)

    return hook, ready, release


def run_thread(fn: Any) -> tuple[Any, list[Any]]:
    """Run ``fn`` in a thread; the box receives ("ok", value) or ("error", exception)."""

    import threading

    box: list[Any] = []

    def target() -> None:
        try:
            box.append(("ok", fn()))
        except BaseException as error:  # noqa: BLE001 - reported to the asserting thread
            box.append(("error", error))

    thread = threading.Thread(target=target)
    thread.start()
    return thread, box


def isolated_queue() -> Any:
    """``b4_support.isolated_queue`` plus removal of jobs a dead or failing worker left in this
    queue's started/failed registries (their synthetic args must not outlive the test)."""

    from contextlib import suppress

    import b4_support as r
    from rq.exceptions import NoSuchJobError
    from rq.job import Job

    for queue in r.isolated_queue():
        try:
            yield queue
        finally:
            rq = queue.queue
            for registry in (rq.started_job_registry, rq.failed_job_registry,
                             rq.finished_job_registry):
                for job_id in registry.get_job_ids():
                    with suppress(NoSuchJobError):
                        Job.fetch(job_id, connection=rq.connection).delete()
