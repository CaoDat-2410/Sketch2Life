"""Process-local whiteboard video job state machine for FEAT-018."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Protocol
from uuid import uuid4

from sketch2life.contracts.schemas.whiteboard_video import (
    WhiteboardVideoJobV1,
    WhiteboardVideoResultV1,
)


class WhiteboardVideoPipelineError(RuntimeError):
    """Sanitized pipeline failure; provider details must stay outside the contract."""

    def __init__(self, code: str, *, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class UnconfiguredWhiteboardVideoPipeline:
    """Default local adapter; real provider wiring is a later implementation slice."""

    def run(self, job: WhiteboardVideoJobV1, update_stage: Callable[[str, int], None]) -> WhiteboardVideoResultV1:
        del job, update_stage
        raise WhiteboardVideoPipelineError("PIPELINE_NOT_CONFIGURED", retryable=False)


class WhiteboardVideoPipeline(Protocol):
    def run(
        self,
        job: WhiteboardVideoJobV1,
        update_stage: Callable[[str, int], None],
    ) -> WhiteboardVideoResultV1: ...


class InMemoryWhiteboardVideoJobStore:
    """Deterministic process-local store for contract and API integration tests."""

    def __init__(self) -> None:
        self._jobs: dict[str, WhiteboardVideoJobV1] = {}
        self._attempt_history: dict[str, list[WhiteboardVideoJobV1]] = {}

    def put(self, job: WhiteboardVideoJobV1) -> None:
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> WhiteboardVideoJobV1:
        return self._jobs[job_id]

    def history(self, job_id: str) -> tuple[WhiteboardVideoJobV1, ...]:
        return tuple(self._attempt_history.get(job_id, ()))

    def for_session(self, session_id: str) -> tuple[WhiteboardVideoJobV1, ...]:
        return tuple(job for job in self._jobs.values() if job.session_id == session_id)

    def record(self, job: WhiteboardVideoJobV1) -> None:
        self._attempt_history.setdefault(job.job_id, []).append(job)


class WhiteboardVideoJobService:
    """Create, run and retry a bounded whiteboard video job."""

    def __init__(
        self,
        *,
        pipeline: WhiteboardVideoPipeline,
        store: InMemoryWhiteboardVideoJobStore | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._pipeline = pipeline
        self._store = store or InMemoryWhiteboardVideoJobStore()
        self._now = now
        self._lock = RLock()
        self._idempotency: dict[tuple[str, str], tuple[tuple[str, ...], str]] = {}
        self._results: dict[str, WhiteboardVideoResultV1] = {}

    @property
    def store(self) -> InMemoryWhiteboardVideoJobStore:
        return self._store

    def create_job(
        self,
        *,
        session_id: str,
        experience_spec_id: str,
        source_artifact_id: str,
        source_hash: str,
        learning_thread_ref: str,
        idempotency_key: str,
    ) -> WhiteboardVideoJobV1:
        now = self._now()
        job = WhiteboardVideoJobV1(
            job_id=str(uuid4()),
            session_id=session_id,
            experience_spec_id=experience_spec_id,
            source_artifact_id=source_artifact_id,
            source_hash=source_hash,
            learning_thread_ref=learning_thread_ref,
            status="QUEUED",
            progress=0,
            current_stage="NOT_STARTED",
            attempt=1,
            idempotency_key=idempotency_key,
            created_at=now,
            expires_at=now + timedelta(minutes=3),
        )
        with self._lock:
            self._store.put(job)
            self._store.record(job)
        return job

    def create_or_replay(
        self,
        *,
        session_id: str,
        experience_spec_id: str,
        source_artifact_id: str,
        source_hash: str,
        learning_thread_ref: str,
        idempotency_key: str,
    ) -> tuple[WhiteboardVideoJobV1, bool]:
        fingerprint = (
            experience_spec_id,
            source_artifact_id,
            source_hash,
            learning_thread_ref,
        )
        key = (session_id, idempotency_key)
        with self._lock:
            prior = self._idempotency.get(key)
            if prior is not None:
                if prior[0] != fingerprint:
                    raise ValueError("idempotency key payload mismatch")
                return self._store.get(prior[1]), True
            job = self.create_job(
                session_id=session_id,
                experience_spec_id=experience_spec_id,
                source_artifact_id=source_artifact_id,
                source_hash=source_hash,
                learning_thread_ref=learning_thread_ref,
                idempotency_key=idempotency_key,
            )
            self._idempotency[key] = (fingerprint, job.job_id)
            return job, False

    def run(self, job_id: str) -> WhiteboardVideoResultV1:
        with self._lock:
            job = self._store.get(job_id)
            self._update(job, status="RUNNING", progress=max(job.progress, 1))
            job = self._store.get(job_id)

        try:
            result = self._pipeline.run(job, lambda stage, progress: self._advance(job_id, stage, progress))
        except WhiteboardVideoPipelineError as error:
            with self._lock:
                current = self._store.get(job_id)
                terminal_status = "RETRYABLE_FAILURE" if error.retryable and current.attempt < 3 else "FAILED"
                self._update(
                    current,
                    status=terminal_status,
                    failure_ref=error.code,
                    completed_at=self._now(),
                )
            raise

        with self._lock:
            current = self._store.get(job_id)
            if result.source_hash != current.source_hash:
                self._update(
                    current,
                    status="FAILED",
                    failure_ref="SOURCE_HASH_MISMATCH",
                    completed_at=self._now(),
                )
                raise WhiteboardVideoPipelineError("SOURCE_HASH_MISMATCH", retryable=False)
            self._update(
                current,
                status="READY",
                progress=100,
                completed_at=self._now(),
            )
            self._results[job_id] = result
        return result

    def result(self, job_id: str) -> WhiteboardVideoResultV1 | None:
        return self._results.get(job_id)

    def retry(self, job_id: str, *, idempotency_key: str) -> WhiteboardVideoJobV1:
        with self._lock:
            current = self._store.get(job_id)
            if current.status != "RETRYABLE_FAILURE":
                raise ValueError("only retryable failures can be retried")
            if current.attempt >= 3:
                raise ValueError("whiteboard job retry budget is exhausted")
            next_job = current.model_copy(
                update={
                    "job_version": current.job_version + 1,
                    "status": "QUEUED",
                    "progress": 0,
                    "current_stage": "NOT_STARTED",
                    "attempt": current.attempt + 1,
                    "idempotency_key": idempotency_key,
                    "failure_ref": None,
                    "started_at": None,
                    "completed_at": None,
                }
            )
            self._store.put(next_job)
            self._store.record(next_job)
            return next_job

    def _advance(self, job_id: str, stage: str, progress: int) -> None:
        with self._lock:
            current = self._store.get(job_id)
            self._update(current, current_stage=stage, progress=progress)

    def _update(self, current: WhiteboardVideoJobV1, **updates: object) -> None:
        self._store.put(current.model_copy(update=updates))


__all__ = [
    "InMemoryWhiteboardVideoJobStore",
    "WhiteboardVideoJobService",
    "WhiteboardVideoPipeline",
    "WhiteboardVideoPipelineError",
    "UnconfiguredWhiteboardVideoPipeline",
]
