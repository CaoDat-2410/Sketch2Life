"""Redis/RQ ``DispatchQueuePort`` adapter and worker entry for BE2-01 Phase B (ADR-0018 D3,
plan Δ14; B4 publish, B5 receive).

The only broker adapter. PostgreSQL owns job state, the dispatch outbox and redelivery, so RQ
transport retries stay disabled (no ``Retry`` is passed). Each publish carries the transient
``WorkerDispatchEnvelope`` as job args; ``description`` is the outbox ``message_id`` so RQ never
renders the args (and the capability) into its job description, ``result_ttl=0`` and a short
``failure_ttl`` limit how long the transient payload stays in Redis. A broker connection failure
raises the application ``QueueUnavailable`` so the outbox row is released and stays pending.

B5: ``receive_dispatch`` is the RQ job entry point. It rebuilds the envelope and hands it to
the process's installed ``DispatchWorker``; it never raises, so RQ's failure handler (which
would put ``job.args`` into a structured log record) is not reached. ``RedactingSimpleWorker``
additionally replaces that handler and installs the capability redaction filter on RQ's
loggers. ``pop_envelope`` stays a fixture receiver for B4 recovery tests.
"""

from __future__ import annotations

import logging
from typing import Any

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError
from rq import Queue, SimpleWorker
from rq.job import Job

from sketch2life.application.ports.ai_jobs import DispatchMessage, WorkerDispatchEnvelope
from sketch2life.application.services.ai_jobs import QueueUnavailable
from sketch2life.domain.ai_jobs.model import RequestRef
from sketch2life.infrastructure.ai_jobs.worker import install_log_redaction, installed_worker

WORKER_ENTRYPOINT = "sketch2life.infrastructure.ai_jobs.rq_queue.receive_dispatch"
# fixture.durable_jobs.v0 (decision record §5.1): PROPOSED, fixture only.
FIXTURE_FAILURE_TTL_SECONDS = 60
FIXTURE_RESULT_TTL_SECONDS = 0
RQ_LOGGERS = ("rq", "rq.worker", "rq.job", "rq.queue")

_log = logging.getLogger("sketch2life.ai_jobs.rq")


def envelope_args(envelope: WorkerDispatchEnvelope) -> tuple[dict[str, Any], str]:
    message = envelope.message
    payload = {
        "message_id": message.message_id,
        "job_id": message.job_id,
        "attempt_id": message.attempt_id,
        "attempt_number": message.attempt_number,
        "job_type": message.job_type,
        "request_ref": {
            "request_id": message.request_ref.request_id,
            "request_revision": message.request_ref.request_revision,
            "input_hash": message.request_ref.input_hash,
            "context_revision": message.request_ref.context_revision,
        },
    }
    return payload, envelope.capability


def envelope_from_args(payload: dict[str, Any], capability: str) -> WorkerDispatchEnvelope:
    ref = payload["request_ref"]
    message = DispatchMessage(
        message_id=payload["message_id"],
        job_id=payload["job_id"],
        attempt_id=payload["attempt_id"],
        attempt_number=payload["attempt_number"],
        job_type=payload["job_type"],
        request_ref=RequestRef(
            ref["request_id"], ref["request_revision"], ref["input_hash"], ref["context_revision"]
        ),
    )
    return WorkerDispatchEnvelope(message, capability)


def receive_dispatch(payload: dict[str, Any], capability: str) -> str:
    """RQ job entry point (B5). Returns a status code; never raises and never logs the args.
    Anything it cannot handle stays recoverable by the SQL reconciler."""

    message_id = payload.get("message_id") if isinstance(payload, dict) else None
    worker = installed_worker()
    if worker is None:
        _log.error("dispatch %s not handled: no worker installed", message_id)
        return "NOT_INSTALLED"
    try:
        envelope = envelope_from_args(payload, capability)
    except (KeyError, TypeError, ValueError, AttributeError):
        _log.error("dispatch %s not handled: malformed payload", message_id)
        return "MALFORMED"
    try:
        outcome = worker.handle(envelope)
    except Exception as error:
        _log.error("dispatch %s failed in worker: %s", message_id, type(error).__name__)
        return "WORKER_ERROR"
    _log.info("dispatch %s: %s %s", message_id, outcome.status, outcome.reason_code)
    return outcome.status


class RedactingSimpleWorker(SimpleWorker):
    """In-process RQ worker whose failure handler logs only the job id and exception type.

    RQ's default ``handle_exception`` attaches ``job.args`` (the capability) to the record as
    the ``arguments`` extra; this override never does. The redaction filter covers every other
    RQ record."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        install_log_redaction(*RQ_LOGGERS)
        super().__init__(*args, **kwargs)

    def handle_exception(self, job: Job, *exc_info: Any) -> None:
        kind = exc_info[0].__name__ if exc_info and exc_info[0] is not None else "unknown"
        self.log.error("Worker %s: job %s failed (%s)", self.name, job.id, kind)


class RqDispatchQueue:
    def __init__(
        self,
        connection: Redis,
        queue_name: str,
        *,
        failure_ttl: int = FIXTURE_FAILURE_TTL_SECONDS,
    ) -> None:
        self.queue = Queue(queue_name, connection=connection)
        self._failure_ttl = failure_ttl

    def enqueue(self, envelope: WorkerDispatchEnvelope) -> None:
        payload, capability = envelope_args(envelope)
        try:
            self.queue.enqueue(
                WORKER_ENTRYPOINT,
                payload,
                capability,
                description=envelope.message.message_id,
                result_ttl=FIXTURE_RESULT_TTL_SECONDS,
                failure_ttl=self._failure_ttl,
            )
        except (RedisConnectionError, RedisTimeoutError):
            raise QueueUnavailable("dispatch broker unavailable") from None


def pop_envelope(queue: Queue) -> WorkerDispatchEnvelope | None:
    """Fixture receiver: take the next job off the queue without running a worker, rebuild its
    envelope and delete the RQ job (B4 tests only; never a production consumer)."""

    # LPOP directly: RQ 2.12 ``Queue.pop_job_id`` raises on an empty queue instead of
    # returning None (B4-RT01).
    raw = queue.connection.lpop(queue.key)
    if raw is None:
        return None
    job_id = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    job = Job.fetch(job_id, connection=queue.connection)
    payload, capability = job.args
    job.delete()
    return envelope_from_args(payload, capability)


__all__ = [
    "FIXTURE_FAILURE_TTL_SECONDS",
    "FIXTURE_RESULT_TTL_SECONDS",
    "RQ_LOGGERS",
    "WORKER_ENTRYPOINT",
    "RedactingSimpleWorker",
    "RqDispatchQueue",
    "envelope_args",
    "envelope_from_args",
    "pop_envelope",
    "receive_dispatch",
]
