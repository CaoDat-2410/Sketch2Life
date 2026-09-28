"""Storage boundary for short-lived FEAT-030 renderer artifact capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RigArtifactGrant:
    capability_sha256: str
    session_id: str
    artifact_ref: str
    artifact_sha256: str
    expires_at: datetime
    remaining_reads: int


class RigArtifactGrantStore(Protocol):
    def put(self, grant: RigArtifactGrant) -> None: ...

    def consume(self, capability_sha256: str, *, now: datetime) -> RigArtifactGrant | None: ...

    def purge_expired(self, *, now: datetime) -> int: ...


# Backward-compatible names for the original package-only storage boundary.
RigPackageGrant = RigArtifactGrant
RigPackageGrantStore = RigArtifactGrantStore

__all__ = [
    "RigArtifactGrant",
    "RigArtifactGrantStore",
    "RigPackageGrant",
    "RigPackageGrantStore",
]
