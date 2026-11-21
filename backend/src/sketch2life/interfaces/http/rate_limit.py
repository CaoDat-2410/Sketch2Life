"""Bounded process-local sliding-window limiter by operation, account and client address.

FEAT-066 T-7c-fix (O-2): SRS NFR-12 (l.637) asks for 429 with ``Retry-After``, counted per
account, IP and operation and never by child id or content; FR-O-06 (l.611) leaves the numbers to
a benchmark (X-18), so the limits are provisional ``Settings`` values. The state is in memory:
several workers multiply the limits and a restart resets them (a shared store is X-18).
"""

from __future__ import annotations

import math
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from threading import Lock

DEFAULT_ACCOUNT_LIMIT = 5
DEFAULT_IP_LIMIT = 20
DEFAULT_WINDOW_SECONDS = 60
MAX_TRACKED_KEYS = 1024

_BucketKey = tuple[str, str]


class SlidingWindowLimiter:
    """Two buckets per call: ``(operation, account)`` and ``(operation, ip)``.

    A call is admitted only when both buckets have room, and it is then recorded in both; a
    refused call charges neither. Each dimension keeps at most ``max_keys`` buckets (LRU), each
    bucket at most its limit of timestamps, so memory is bounded. Under key pressure the oldest
    bucket is evicted, which forgets that key's history (acceptable for a refusal-only gate).
    """

    def __init__(
        self,
        *,
        account_limit: int = DEFAULT_ACCOUNT_LIMIT,
        ip_limit: int = DEFAULT_IP_LIMIT,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        max_keys: int = MAX_TRACKED_KEYS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if min(account_limit, ip_limit, window_seconds, max_keys) < 1:
            raise ValueError("limits, window and key cap must be positive")
        self._account_limit = account_limit
        self._ip_limit = ip_limit
        self._window = float(window_seconds)
        self._max_keys = max_keys
        self._clock = clock
        self._lock = Lock()
        self._accounts: OrderedDict[_BucketKey, deque[float]] = OrderedDict()
        self._ips: OrderedDict[_BucketKey, deque[float]] = OrderedDict()

    def acquire(self, operation: str, *, account: str, ip: str) -> int | None:
        """Admit the call (``None``) or return the whole seconds to wait (at least 1).

        When both buckets refuse, the wait is the longer of the two, so one retry after that
        time can pass both.
        """
        now = self._clock()
        cutoff = now - self._window
        account_key: _BucketKey = (operation, account)
        ip_key: _BucketKey = (operation, ip)
        with self._lock:
            waits: list[float] = []
            buckets = (
                (self._accounts, account_key, self._account_limit),
                (self._ips, ip_key, self._ip_limit),
            )
            for store, key, limit in buckets:
                hits = store.get(key)
                if hits is None:
                    continue
                while hits and hits[0] <= cutoff:
                    hits.popleft()
                if len(hits) >= limit:
                    waits.append(hits[0] + self._window - now)
                    store.move_to_end(key)
            if waits:
                return max(1, math.ceil(max(waits)))
            for store, key, _limit in buckets:
                hits = store.get(key)
                if hits is None:
                    if len(store) >= self._max_keys:
                        store.popitem(last=False)
                    hits = deque()
                    store[key] = hits
                else:
                    store.move_to_end(key)
                hits.append(now)
            return None

    def tracked_keys(self) -> tuple[int, int]:
        """Number of account and IP buckets held (for tests and memory checks)."""
        with self._lock:
            return len(self._accounts), len(self._ips)
