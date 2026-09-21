"""Thread-safe, process-local storage adapters for the non-persistent demo."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import RLock
from uuid import uuid4

from sketch2life.application.ports.session_storage import (
    DuplicateSessionError,
    IdempotencyConflict,
    IdempotencyReceipt,
    SessionRecord,
    StoredArtifact,
    artifact_sha256,
)


class SessionVersionConflict(ValueError):
    pass


class InMemorySessionRepository[SnapshotT]:
    def __init__(self) -> None:
        self._records: dict[str, SessionRecord[SnapshotT]] = {}
        self._lock = RLock()

    def create(self, record: SessionRecord[SnapshotT]) -> None:
        if record.version != 0:
            raise ValueError("new session must start at version zero")
        _require_aware(record.expires_at)
        with self._lock:
            if record.session_id in self._records:
                raise DuplicateSessionError("session already exists")
            self._records[record.session_id] = deepcopy(record)

    def get(self, session_id: str) -> SessionRecord[SnapshotT] | None:
        with self._lock:
            record = self._records.get(session_id)
            return deepcopy(record) if record is not None else None

    def compare_and_swap(
        self, *, session_id: str, expected_version: int, record: SessionRecord[SnapshotT]
    ) -> None:
        _require_aware(record.expires_at)
        if record.session_id != session_id or record.version != expected_version + 1:
            raise ValueError("replacement session identity/version is invalid")
        with self._lock:
            current = self._records.get(session_id)
            if current is None or current.version != expected_version:
                raise SessionVersionConflict("session is missing or has a newer version")
            self._records[session_id] = deepcopy(record)

    def expired_before(self, cutoff: datetime) -> tuple[str, ...]:
        _require_aware(cutoff)
        with self._lock:
            return tuple(
                sorted(
                    session_id
                    for session_id, record in self._records.items()
                    if record.expires_at <= cutoff
                )
            )

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._records.pop(session_id, None) is not None


class InMemoryJobStore[JobT]:
    def __init__(self) -> None:
        self._jobs: dict[str, JobT] = {}
        self._lock = RLock()

    def create(self, job_id: str, job: JobT) -> None:
        with self._lock:
            if job_id in self._jobs:
                raise ValueError("job already exists")
            self._jobs[job_id] = deepcopy(job)

    def get(self, job_id: str) -> JobT | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return deepcopy(job) if job is not None else None

    def replace(self, job_id: str, *, expected: JobT, updated: JobT) -> None:
        with self._lock:
            if job_id not in self._jobs or self._jobs[job_id] != expected:
                raise ValueError("job changed or does not exist")
            self._jobs[job_id] = deepcopy(updated)

    def delete(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None


class InMemoryArtifactStore:
    def __init__(self) -> None:
        self._items: dict[str, tuple[StoredArtifact, bytes]] = {}
        self._lock = RLock()

    def put(self, *, session_id: str, content_type: str, body: bytes) -> StoredArtifact:
        if not session_id or not content_type or not body:
            raise ValueError("session, content type, and non-empty artifact are required")
        ref = f"artifact:{uuid4()}"
        descriptor = StoredArtifact(
            artifact_ref=ref,
            session_id=session_id,
            sha256=artifact_sha256(body),
            content_type=content_type,
            byte_length=len(body),
        )
        with self._lock:
            self._items[ref] = (descriptor, bytes(body))
        return descriptor

    def get(self, artifact_ref: str) -> tuple[StoredArtifact, bytes] | None:
        with self._lock:
            value = self._items.get(artifact_ref)
            return deepcopy(value) if value is not None else None

    def delete_session(self, session_id: str) -> int:
        with self._lock:
            refs = [
                ref
                for ref, (descriptor, _) in self._items.items()
                if descriptor.session_id == session_id
            ]
            for ref in refs:
                del self._items[ref]
            return len(refs)


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._receipts: dict[tuple[str, str], IdempotencyReceipt] = {}
        self._lock = RLock()

    def get(self, *, scope: str, key: str) -> IdempotencyReceipt | None:
        with self._lock:
            return deepcopy(self._receipts.get((scope, key)))

    def record(self, receipt: IdempotencyReceipt) -> None:
        identity = (receipt.scope, receipt.key)
        with self._lock:
            previous = self._receipts.get(identity)
            if previous is not None:
                if previous.request_sha256 != receipt.request_sha256:
                    raise IdempotencyConflict("idempotency key was reused for another request")
                return
            self._receipts[identity] = deepcopy(receipt)

    def delete_scope(self, scope: str) -> int:
        with self._lock:
            identities = [identity for identity in self._receipts if identity[0] == scope]
            for identity in identities:
                del self._receipts[identity]
            return len(identities)


def _require_aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("session timestamps must be timezone-aware")


__all__ = [
    "DuplicateSessionError",
    "IdempotencyConflict",
    "InMemoryArtifactStore",
    "InMemoryIdempotencyStore",
    "InMemoryJobStore",
    "InMemorySessionRepository",
    "SessionVersionConflict",
]
