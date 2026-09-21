"""Replaceable ports for process-local demo session, job, and media state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Protocol, TypeVar


class DuplicateSessionError(ValueError):
    """Repository rejected creation because the session identity already exists."""


class IdempotencyConflict(ValueError):
    """Idempotency key was already bound to a different request fingerprint."""


@dataclass(frozen=True, slots=True)
class SessionRecord[T]:
    """Opaque snapshot plus repository-only metadata; never a public contract."""

    session_id: str
    version: int
    expires_at: datetime
    snapshot: T
    owner_principal_key: str | None = None


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    artifact_ref: str
    session_id: str
    sha256: str
    content_type: str
    byte_length: int


@dataclass(frozen=True, slots=True)
class IdempotencyReceipt:
    scope: str
    key: str
    request_sha256: str
    response_body: bytes


SnapshotT = TypeVar("SnapshotT")
JobT = TypeVar("JobT")


class SessionRepository[SnapshotT](Protocol):
    def create(self, record: SessionRecord[SnapshotT]) -> None: ...

    def get(self, session_id: str) -> SessionRecord[SnapshotT] | None: ...

    def compare_and_swap(
        self, *, session_id: str, expected_version: int, record: SessionRecord[SnapshotT]
    ) -> None: ...

    def expired_before(self, cutoff: datetime) -> tuple[str, ...]: ...

    def delete(self, session_id: str) -> bool: ...


class JobStore[JobT](Protocol):
    def create(self, job_id: str, job: JobT) -> None: ...

    def get(self, job_id: str) -> JobT | None: ...

    def replace(self, job_id: str, *, expected: JobT, updated: JobT) -> None: ...

    def delete(self, job_id: str) -> bool: ...


class ArtifactStore(Protocol):
    def put(self, *, session_id: str, content_type: str, body: bytes) -> StoredArtifact: ...

    def get(self, artifact_ref: str) -> tuple[StoredArtifact, bytes] | None: ...

    def delete_session(self, session_id: str) -> int: ...


class IdempotencyStore(Protocol):
    def get(self, *, scope: str, key: str) -> IdempotencyReceipt | None: ...

    def record(self, receipt: IdempotencyReceipt) -> None: ...

    def delete_scope(self, scope: str) -> int: ...


def artifact_sha256(body: bytes) -> str:
    return sha256(body).hexdigest()


__all__ = [
    "ArtifactStore",
    "DuplicateSessionError",
    "IdempotencyConflict",
    "IdempotencyReceipt",
    "IdempotencyStore",
    "JobStore",
    "SessionRecord",
    "SessionRepository",
    "StoredArtifact",
    "artifact_sha256",
]
