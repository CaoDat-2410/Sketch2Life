"""Storage boundary for short-lived FEAT-030 rig package capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RigPackageGrant:
    capability_sha256: str
    session_id: str
    artifact_ref: str
    package_sha256: str
    expires_at: datetime
    remaining_reads: int


class RigPackageGrantStore(Protocol):
    def put(self, grant: RigPackageGrant) -> None: ...

    def consume(self, capability_sha256: str, *, now: datetime) -> RigPackageGrant | None: ...

    def purge_expired(self, *, now: datetime) -> int: ...


__all__ = ["RigPackageGrant", "RigPackageGrantStore"]
