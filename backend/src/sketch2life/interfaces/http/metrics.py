"""Process-local HTTP metrics and Prometheus text exposition for `/metrics` (T0.3, SRS l.814).

Deliberately small and dependency-free. Every label comes from a fixed, tiny vocabulary: no
route, path, user, organization, run or job label exists, so the series count cannot grow with
traffic and no identifier can leak. The registry is per process (the container runs one worker);
the HELP text says so. Business aggregates are not part of this task.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

SERVICE_NAME = "sketch2life-api"
EXPOSITION_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"
DURATION_BUCKETS: tuple[float, ...] = (
    0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0,
)
_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "OTHER")
_STATUS_CLASSES = ("1xx", "2xx", "3xx", "4xx", "5xx")

Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


def method_label(method: str) -> str:
    upper = method.upper()
    return upper if upper in _METHODS[:-1] else "OTHER"


def status_class_label(status: int) -> str:
    index = status // 100
    return f"{index}xx" if 1 <= index <= 5 else "5xx"


class MetricsRegistry:
    """Thread-safe counters, one histogram and one gauge behind a single lock."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._requests: dict[tuple[str, str], int] = {}
        self._bucket_counts = [0] * len(DURATION_BUCKETS)
        self._duration_sum = 0.0
        self._duration_count = 0
        self._in_flight = 0

    def request_started(self) -> None:
        with self._lock:
            self._in_flight += 1

    def request_finished(self, *, method: str, status: int | None, seconds: float) -> None:
        with self._lock:
            self._in_flight = max(0, self._in_flight - 1)
            if status is None:
                return
            key = (method_label(method), status_class_label(status))
            self._requests[key] = self._requests.get(key, 0) + 1
            self._duration_sum += seconds
            self._duration_count += 1
            for index, bound in enumerate(DURATION_BUCKETS):
                if seconds <= bound:
                    self._bucket_counts[index] += 1

    def render(self) -> str:
        with self._lock:
            requests = dict(self._requests)
            buckets = list(self._bucket_counts)
            duration_sum = self._duration_sum
            duration_count = self._duration_count
            in_flight = self._in_flight
            started_at = self._started_at
        lines = [
            "# HELP sketch2life_build_info Constant 1; the service name is the only label.",
            "# TYPE sketch2life_build_info gauge",
            f'sketch2life_build_info{{service="{SERVICE_NAME}"}} 1',
            "# HELP sketch2life_process_start_time_seconds Start time of this process, Unix"
            " seconds.",
            "# TYPE sketch2life_process_start_time_seconds gauge",
            f"sketch2life_process_start_time_seconds {started_at:.3f}",
            "# HELP sketch2life_http_requests_total HTTP requests by method and status class."
            " Per process; the container runs one worker.",
            "# TYPE sketch2life_http_requests_total counter",
        ]
        for method in _METHODS:
            for status_class in _STATUS_CLASSES:
                count = requests.get((method, status_class), 0)
                if count:
                    lines.append(
                        "sketch2life_http_requests_total"
                        f'{{method="{method}",status_class="{status_class}"}} {count}'
                    )
        lines += [
            "# HELP sketch2life_http_request_duration_seconds HTTP request duration, all routes"
            " together. Per process.",
            "# TYPE sketch2life_http_request_duration_seconds histogram",
        ]
        for bound, count in zip(DURATION_BUCKETS, buckets, strict=True):
            lines.append(
                f'sketch2life_http_request_duration_seconds_bucket{{le="{bound:g}"}} {count}'
            )
        lines += [
            f'sketch2life_http_request_duration_seconds_bucket{{le="+Inf"}} {duration_count}',
            f"sketch2life_http_request_duration_seconds_sum {duration_sum:.6f}",
            f"sketch2life_http_request_duration_seconds_count {duration_count}",
            "# HELP sketch2life_http_requests_in_flight HTTP requests being served now."
            " Per process.",
            "# TYPE sketch2life_http_requests_in_flight gauge",
            f"sketch2life_http_requests_in_flight {in_flight}",
        ]
        return "\n".join(lines) + "\n"


class HttpMetricsMiddleware:
    """Pure ASGI middleware. Added last so it is the outermost user middleware."""

    def __init__(self, app: ASGIApp, *, registry: MetricsRegistry) -> None:
        self._app = app
        self._registry = registry

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        status: int | None = None

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = int(message["status"])
            await send(message)

        started = time.perf_counter()
        self._registry.request_started()
        try:
            await self._app(scope, receive, send_wrapper)
        except Exception:
            # The unhandled-exception handler sits outside user middleware, so the 500 is
            # invisible here: count it as 5xx when no response had started, then re-raise.
            if status is None:
                status = 500
            raise
        finally:
            self._registry.request_finished(
                method=str(scope.get("method", "")),
                status=status,
                seconds=time.perf_counter() - started,
            )
