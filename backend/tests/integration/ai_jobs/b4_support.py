"""Shared Redis/RQ wiring for the BE2-01 Phase B batch B4 tests (synthetic data only).

Configure with ``BE2_TEST_REDIS_HOST`` (optional ``BE2_TEST_REDIS_PORT``). Each test uses its own
``be2_b4_<random>`` RQ queue and deletes only keys containing that unique name afterwards, so
the shared Redis service and other queues are never touched. Without ``BE2_TEST_REDIS_HOST``
the Redis-backed tests skip: NOT_RUN, never PASS.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest
from redis import Redis
from rq import Queue
from sketch2life.application.ports.ai_jobs import WorkerDispatchEnvelope
from sketch2life.infrastructure.ai_jobs.rq_queue import RqDispatchQueue, pop_envelope

UNREACHABLE_PORT = 1  # nothing listens there: an injected unavailable broker endpoint


def redis_settings() -> tuple[str, int] | None:
    host = os.environ.get("BE2_TEST_REDIS_HOST")
    if not host:
        return None
    return host, int(os.environ.get("BE2_TEST_REDIS_PORT", "6379"))


def connect(host: str, port: int) -> Redis:
    return Redis(host=host, port=port, socket_connect_timeout=2, socket_timeout=5)


def isolated_queue() -> Iterator[RqDispatchQueue]:
    settings = redis_settings()
    if settings is None:
        pytest.skip("BE2_TEST_REDIS_HOST not set: Redis/RQ checks NOT_RUN")
    connection = connect(*settings)
    name = f"be2_b4_{uuid.uuid4().hex[:16]}"
    adapter = RqDispatchQueue(connection, name)
    try:
        yield adapter
    finally:
        cleanup(adapter.queue)
        connection.close()


def cleanup(queue: Queue) -> None:
    """Remove this test queue only: its jobs, its keys and its member in RQ's shared
    ``rq:queues`` set (``Queue.delete``), then any remaining key carrying the unique name."""

    queue.delete(delete_jobs=True)
    for key in queue.connection.scan_iter(match=f"*{queue.name}*"):
        queue.connection.delete(key)


def unavailable_queue() -> RqDispatchQueue:
    settings = redis_settings()
    assert settings is not None
    name = f"be2_b4_down_{uuid.uuid4().hex}"
    return RqDispatchQueue(connect(settings[0], UNREACHABLE_PORT), name)


def drain(queue: Queue) -> list[WorkerDispatchEnvelope]:
    received = []
    while (envelope := pop_envelope(queue)) is not None:
        received.append(envelope)
    return received
