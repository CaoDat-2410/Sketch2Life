"""Ephemeral one-time source-image capabilities for the local Pixi renderer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RendererSourceGrant:
    capability_sha256: str
    session_id: str
    artifact_ref: str
    artifact_sha256: str
    expires_at: datetime
    remaining_reads: int


class RendererSourceGrantStore(Protocol):
    def put(self, grant: RendererSourceGrant) -> None: ...

    def consume(self, capability_sha256: str, *, now: datetime) -> RendererSourceGrant | None: ...

    def purge_expired(self, *, now: datetime) -> int: ...


__all__ = ["RendererSourceGrant", "RendererSourceGrantStore"]
