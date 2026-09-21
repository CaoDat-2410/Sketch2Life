"""Thread-safe, process-local adapter for short-lived Pixi source capabilities."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from threading import RLock

from sketch2life.application.ports.renderer_source_storage import RendererSourceGrant


class InMemoryRendererSourceGrantStore:
    def __init__(self) -> None:
        self._items: dict[str, RendererSourceGrant] = {}
        self._lock = RLock()

    def put(self, grant: RendererSourceGrant) -> None:
        with self._lock:
            self._items[grant.capability_sha256] = grant

    def consume(self, capability_sha256: str, *, now: datetime) -> RendererSourceGrant | None:
        with self._lock:
            grant = self._items.get(capability_sha256)
            if grant is None:
                return None
            if grant.expires_at <= now or grant.remaining_reads <= 0:
                del self._items[capability_sha256]
                return None
            if grant.remaining_reads == 1:
                del self._items[capability_sha256]
            else:
                self._items[capability_sha256] = replace(
                    grant, remaining_reads=grant.remaining_reads - 1
                )
            return grant

    def purge_expired(self, *, now: datetime) -> int:
        with self._lock:
            expired = tuple(key for key, grant in self._items.items() if grant.expires_at <= now)
            for key in expired:
                del self._items[key]
            return len(expired)


__all__ = ["InMemoryRendererSourceGrantStore"]
