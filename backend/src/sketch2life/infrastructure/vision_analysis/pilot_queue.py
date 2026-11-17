"""Bounded in-process dispatch queue for the explicitly enabled pilot."""

from __future__ import annotations

from queue import Empty, Full, Queue

from sketch2life.application.ports.ai_jobs import DispatchQueuePort, WorkerDispatchEnvelope
from sketch2life.application.services.ai_jobs import QueueUnavailable
from sketch2life.infrastructure.ai_jobs.typed_dispatch import VideoDispatchOutcome
from sketch2life.infrastructure.ai_jobs.worker import (
    DispatchWorker,
    WorkerOutcome,
)


class InProcessDispatchQueue(DispatchQueuePort):
    """FIFO queue with no implicit retry or persistence claim.

    Queue saturation raises the application signal so the durable outbox remains pending.
    Once dequeued, a process crash can lose this in-memory delivery; this is a dev pilot and
    must not be treated as the production dispatch mechanism.
    """

    def __init__(self, *, capacity: int = 32) -> None:
        if type(capacity) is not int or capacity < 1:
            raise ValueError("queue capacity must be a positive integer")
        self._queue: Queue[WorkerDispatchEnvelope] = Queue(maxsize=capacity)

    def enqueue(self, envelope: WorkerDispatchEnvelope) -> None:
        try:
            self._queue.put_nowait(envelope)
        except Full:
            raise QueueUnavailable("in-process pilot queue is full") from None

    def receive_nowait(self) -> WorkerDispatchEnvelope | None:
        try:
            return self._queue.get_nowait()
        except Empty:
            return None

    def run_one(self, worker: DispatchWorker) -> WorkerOutcome | VideoDispatchOutcome | None:
        envelope = self.receive_nowait()
        if envelope is None:
            return None
        try:
            return worker.handle(envelope)
        finally:
            self._queue.task_done()

    def __len__(self) -> int:
        return self._queue.qsize()


__all__ = ["InProcessDispatchQueue"]
