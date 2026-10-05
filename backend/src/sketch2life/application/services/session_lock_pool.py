"""Short-lived per-session mutation locks for the process-local demo services."""

from __future__ import annotations

from threading import RLock
from weakref import WeakValueDictionary


class SessionLockPool:
    """Serialize one session without making unrelated sessions wait behind it.

    Callers hold the returned lock for the duration of their state transition. Weak values
    ensure idle session IDs do not accumulate for the lifetime of the process.
    """

    def __init__(self) -> None:
        self._guard = RLock()
        self._locks: WeakValueDictionary[str, RLock] = WeakValueDictionary()

    def for_session(self, session_id: str) -> RLock:
        with self._guard:
            lock = self._locks.get(session_id)
            if lock is None:
                lock = RLock()
                self._locks[session_id] = lock
            return lock


__all__ = ["SessionLockPool"]
