"""Redis/RQ ``DispatchQueuePort`` adapter for BE2-01 Phase B batch B4 (ADR-0018 D3, plan Δ14).

The only broker adapter. PostgreSQL owns job state, the dispatch outbox and redelivery, so RQ
transport retries stay disabled (no ``Retry`` is passed). Each publish carries the transient
``WorkerDispatchEnvelope`` as job args; ``description`` is the outbox ``message_id`` so RQ never
renders the args (and the capability) into its job description, ``result_ttl=0`` and a short
``failure_ttl`` limit how long the transient payload stays in Redis. A broker connection failure
raises the application ``QueueUnavailable`` so the outbox row is released and stays pending.

The worker loop that consumes these jobs is batch B5; ``receive_dispatch`` only marks the
entry point. ``pop_envelope`` is a fixture receiver for B4 recovery tests.
"""

from __future__ import annotations

from typing import Any

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError
from rq import Queue
from rq.job import Job

from sketch2life.application.ports.ai_jobs import DispatchMessage, WorkerDispatchEnvelope
from sketch2life.application.services.ai_jobs import QueueUnavailable
from sketch2life.domain.ai_jobs.model import RequestRef

WORKER_ENTRYPOINT = "sketch2life.infrastructure.ai_jobs.rq_queue.receive_dispatch"
# fixture.durable_jobs.v0 (decision record §5.1): PROPOSED, fixture only.
FIXTURE_FAILURE_TTL_SECONDS = 60
FIXTURE_RESULT_TTL_SECONDS = 0


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


def receive_dispatch(payload: dict[str, Any], capability: str) -> None:
    """RQ job entry point. The worker loop (start/provider/completion) is batch B5."""

    raise NotImplementedError("BE2-01 worker loop is Phase B batch B5")


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
    "WORKER_ENTRYPOINT",
    "RqDispatchQueue",
    "envelope_args",
    "envelope_from_args",
    "pop_envelope",
    "receive_dispatch",
]
