"""One-request HTTP JSON transport with a total monotonic deadline and durable guard."""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import queue
import re
import socket
import ssl
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast
from urllib.parse import urlsplit

from sketch2life.application.ports.vision_analysis import InvocationGuardPort
from sketch2life.infrastructure.ai.lightning_client import JsonTransport, LightningProviderError

_MAX_RESPONSE_BYTES = 1_000_000
_HEADER_NAME = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")
_REQUEST_PATH = re.compile(r"/[A-Za-z0-9._~!$&'()*+,;=:@/-]*\Z")
_AddressInfo = tuple[int, int, int, str, tuple[Any, ...]]
_Resolver = Callable[[str, int], Sequence[_AddressInfo]]
_RESOLVER_WORKER_LIMIT = 2


@dataclass(slots=True)
class _ResolverRequest:
    resolver: _Resolver
    host: str
    port: int
    completed: threading.Event = field(default_factory=threading.Event)
    addresses: Sequence[_AddressInfo] = ()
    succeeded: bool = False


@dataclass(slots=True)
class _ResolverWorker:
    requests: queue.Queue[_ResolverRequest] = field(default_factory=lambda: queue.Queue(maxsize=1))
    thread: threading.Thread | None = None
    busy: bool = False
    retiring: bool = False


class _BoundedResolverPool:
    """Keep process-wide DNS work on a fixed number of daemon workers."""

    def __init__(self, max_workers: int) -> None:
        if max_workers < 1:
            raise ValueError("resolver worker limit must be positive")
        self._max_workers = max_workers
        self._lock = threading.Lock()
        self._workers: list[_ResolverWorker] = []
        register_at_fork = getattr(os, "register_at_fork", None)
        if callable(register_at_fork):
            register_at_fork(after_in_child=self._reset_after_fork)

    @property
    def worker_count(self) -> int:
        with self._lock:
            return sum(
                worker.thread is not None and worker.thread.is_alive() for worker in self._workers
            )

    @property
    def active_worker_count(self) -> int:
        with self._lock:
            return sum(worker.busy for worker in self._workers)

    def resolve(
        self,
        resolver: _Resolver,
        host: str,
        port: int,
        *,
        deadline: float,
        monotonic: Callable[[], float],
    ) -> Sequence[_AddressInfo]:
        def remaining() -> float:
            seconds = deadline - monotonic()
            if seconds <= 0:
                raise TimeoutError("HTTP exchange exceeded the total deadline")
            return seconds

        request = _ResolverRequest(resolver=resolver, host=host, port=port)
        if not self._lock.acquire(timeout=remaining()):
            raise TimeoutError("HTTP exchange exceeded the total deadline")
        try:
            self._ensure_workers_locked()
            remaining()
            worker = next(
                (
                    candidate
                    for candidate in self._workers
                    if not candidate.busy
                    and not candidate.retiring
                    and candidate.thread is not None
                    and candidate.thread.is_alive()
                ),
                None,
            )
            if worker is None:
                raise OSError("hostname resolver capacity is exhausted")
            worker.busy = True
            try:
                worker.requests.put_nowait(request)
            except queue.Full:
                worker.busy = False
                raise OSError("hostname resolver capacity is exhausted") from None
        finally:
            self._lock.release()

        if not request.completed.wait(remaining()):
            raise TimeoutError("HTTP exchange exceeded the total deadline")
        if not request.succeeded:
            raise OSError("hostname resolution failed") from None
        return request.addresses

    def _ensure_workers_locked(self) -> None:
        while len(self._workers) < self._max_workers:
            index = len(self._workers) + 1
            self._workers.append(self._start_worker(index))
        for index, worker in enumerate(tuple(self._workers), start=1):
            if worker.busy:
                continue
            if worker.thread is None or not worker.thread.is_alive():
                self._workers[index - 1] = self._start_worker(index)

    def _start_worker(self, index: int) -> _ResolverWorker:
        worker = _ResolverWorker()
        worker.thread = threading.Thread(
            target=self._serve,
            args=(worker,),
            name=f"vision-dns-resolution-{index}",
            daemon=True,
        )
        try:
            worker.thread.start()
        except RuntimeError:
            raise OSError("hostname resolver workers are unavailable") from None
        return worker

    def _serve(self, worker: _ResolverWorker) -> None:
        while True:
            request = worker.requests.get()
            fatal = False
            try:
                try:
                    request.addresses = request.resolver(request.host, request.port)
                    request.succeeded = True
                except Exception:
                    request.succeeded = False
                except BaseException:
                    request.succeeded = False
                    fatal = True
                finally:
                    request.completed.set()
            finally:
                with self._lock:
                    worker.busy = False
                    worker.retiring = fatal
                worker.requests.task_done()
            if fatal:
                return

    def _reset_after_fork(self) -> None:
        # A forked child inherits Python state but not the resolver worker threads.
        self._lock = threading.Lock()
        self._workers = []


_PROCESS_RESOLVER_POOL = _BoundedResolverPool(_RESOLVER_WORKER_LIMIT)


class HttpJsonTransport(JsonTransport):
    """Send one JSON POST, refusing redirects and bounding the complete HTTP exchange."""

    def __init__(
        self,
        *,
        base_url: str,
        guard: InvocationGuardPort,
        total_timeout_seconds: float = 160.0,
        max_response_bytes: int = _MAX_RESPONSE_BYTES,
        headers: Mapping[str, str] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        resolver: _Resolver | None = None,
    ) -> None:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("provider base URL is invalid")
        if parsed.scheme != "https" and parsed.hostname.casefold() not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise ValueError("provider transport requires HTTPS outside loopback tests")
        if total_timeout_seconds <= 0:
            raise ValueError("total timeout must be positive")
        if not 1 <= max_response_bytes <= _MAX_RESPONSE_BYTES:
            raise ValueError("response limit is outside the approved maximum")
        safe_headers = dict(headers or {})
        for name, value in safe_headers.items():
            if _HEADER_NAME.fullmatch(name) is None or "\r" in value or "\n" in value:
                raise ValueError("HTTP header is invalid")
        self._base = parsed
        self._base_path = parsed.path.rstrip("/")
        self._guard = guard
        self._timeout = total_timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._headers = safe_headers
        self._monotonic = monotonic
        self._resolver = resolver or self._resolve_system

    @property
    def invocation_guard_identity(self) -> InvocationGuardPort:
        """Expose the exact attempt guard to the bridge/decorator binding check."""
        return self._guard

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        target = self._target(path)
        body = json.dumps(
            payload, ensure_ascii=True, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        refusal = self._guard.claim()
        if refusal is not None:
            raise LightningProviderError("GUARD_REFUSED", "invocation was refused", False)

        deadline = self._monotonic() + self._timeout
        connection = self._connection(self._remaining(deadline))
        response: http.client.HTTPResponse | None = None
        response_status: int | None = None
        received = bytearray()
        try:
            # Connect/TLS handshake occurs before the durable SENT transition. No HTTP bytes are
            # written until mark_sent has committed successfully.
            self._connect_before_deadline(connection, deadline)
            remaining = self._remaining(deadline)
            if connection.sock is None:
                raise OSError("HTTP connection did not open")
            connection.sock.settimeout(remaining)
            refusal = self._guard.mark_sent()
            if refusal is not None:
                raise LightningProviderError("GUARD_REFUSED", "invocation was refused", False)

            connection.sock.settimeout(self._remaining(deadline))
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Connection": "close",
                **self._headers,
            }
            connection.request("POST", target, body=body, headers=headers)
            if connection.sock is not None:
                connection.sock.settimeout(self._remaining(deadline))
            response = connection.getresponse()
            response_status = response.status
            if response_status != 200:
                self._guard.record_response(
                    status_code=response_status,
                    body_sha256=None,
                    body_complete=False,
                    json_object=False,
                    within_deadline=self._monotonic() <= deadline,
                )
                raise LightningProviderError(
                    "PROVIDER_ERROR", "HTTP status was not accepted", False
                )

            expected_length = response.length
            if expected_length is not None and expected_length > self._max_response_bytes:
                self._record_partial(response_status, received, deadline)
                raise LightningProviderError("MALFORMED_OUTPUT", "response limit exceeded", False)

            while True:
                remaining = self._remaining(deadline)
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                capacity = self._max_response_bytes + 1 - len(received)
                chunk = response.read1(min(8192, capacity))
                if not chunk:
                    break
                received.extend(chunk)
                if len(received) > self._max_response_bytes:
                    self._record_partial(response_status, received, deadline)
                    raise LightningProviderError(
                        "MALFORMED_OUTPUT", "response limit exceeded", False
                    )

            if expected_length is not None and len(received) != expected_length:
                self._record_partial(response_status, received, deadline)
                raise LightningProviderError("MALFORMED_OUTPUT", "response was incomplete", False)

            body_hash = hashlib.sha256(received).hexdigest()
            try:
                decoded = json.loads(received.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._guard.record_response(
                    status_code=response_status,
                    body_sha256=body_hash,
                    body_complete=True,
                    json_object=False,
                    within_deadline=self._monotonic() <= deadline,
                )
                raise LightningProviderError(
                    "MALFORMED_OUTPUT", "response was not JSON", False
                ) from None

            within_deadline = self._monotonic() <= deadline
            is_object = isinstance(decoded, dict)
            self._guard.record_response(
                status_code=response_status,
                body_sha256=body_hash,
                body_complete=True,
                json_object=is_object,
                within_deadline=within_deadline,
            )
            if not within_deadline:
                raise TimeoutError("HTTP exchange exceeded the total deadline")
            if not is_object:
                raise LightningProviderError(
                    "MALFORMED_OUTPUT", "response root was not an object", False
                )
            return cast(Mapping[str, object], decoded)
        except TimeoutError:
            self._record_if_unset(response_status, received, deadline)
            raise TimeoutError("HTTP exchange exceeded the total deadline") from None
        except LightningProviderError:
            raise
        except (http.client.HTTPException, OSError):
            self._record_if_unset(response_status, received, deadline)
            raise LightningProviderError("PROVIDER_ERROR", "HTTP exchange failed", False) from None
        finally:
            connection.close()

    def mark_bridge_outcome_validated(self) -> None:
        self._guard.mark_bridge_outcome_validated()

    def _target(self, path: str) -> str:
        parsed_path = urlsplit(path)
        if (
            _REQUEST_PATH.fullmatch(path) is None
            or parsed_path.scheme
            or parsed_path.netloc
            or parsed_path.query
            or parsed_path.fragment
            or ".." in parsed_path.path.split("/")
        ):
            raise ValueError("provider request path is invalid")
        return f"{self._base_path}{parsed_path.path}"

    def _connection(self, timeout: float) -> http.client.HTTPConnection:
        host = self._base.hostname
        assert host is not None
        port = self._base.port
        if self._base.scheme == "https":
            return http.client.HTTPSConnection(host, port=port, timeout=timeout)
        return http.client.HTTPConnection(host, port=port, timeout=timeout)

    @staticmethod
    def _resolve_system(host: str, port: int) -> Sequence[_AddressInfo]:
        return cast(
            Sequence[_AddressInfo],
            socket.getaddrinfo(host, port, type=socket.SOCK_STREAM),
        )

    def _resolve_before_deadline(
        self,
        host: str,
        port: int,
        deadline: float,
    ) -> Sequence[_AddressInfo]:
        addresses = _PROCESS_RESOLVER_POOL.resolve(
            self._resolver,
            host,
            port,
            deadline=deadline,
            monotonic=self._monotonic,
        )
        if not addresses:
            raise OSError("hostname resolution returned no addresses")
        return addresses

    def _connect_before_deadline(
        self,
        connection: http.client.HTTPConnection,
        deadline: float,
    ) -> None:
        host = self._base.hostname
        assert host is not None
        port = self._base.port or (443 if self._base.scheme == "https" else 80)
        addresses = self._resolve_before_deadline(host, port, deadline)
        last_error: OSError | None = None

        for family, socktype, protocol, _canonical_name, address in addresses:
            raw_socket = socket.socket(family, socktype, protocol)
            try:
                raw_socket.settimeout(self._remaining(deadline))
                raw_socket.connect(cast(Any, address))
            except TimeoutError:
                raw_socket.close()
                raise
            except OSError as exc:
                raw_socket.close()
                last_error = exc
                continue

            connection.sock = raw_socket
            if self._base.scheme == "https":
                if not isinstance(connection, http.client.HTTPSConnection):
                    raise OSError("HTTPS connection type was not preserved")
                context = cast(ssl.SSLContext, cast(Any, connection)._context)
                if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
                    raise ssl.SSLError("HTTPS certificate and hostname verification are required")
                tls_socket = context.wrap_socket(
                    raw_socket,
                    server_hostname=host,
                    do_handshake_on_connect=False,
                )
                connection.sock = tls_socket
                tls_socket.settimeout(self._remaining(deadline))
                tls_socket.do_handshake()
            return

        if last_error is not None:
            raise last_error
        raise OSError("hostname resolution returned no usable address")

    def _remaining(self, deadline: float) -> float:
        remaining = deadline - self._monotonic()
        if remaining <= 0:
            raise TimeoutError("HTTP exchange exceeded the total deadline")
        return remaining

    def _record_partial(
        self,
        status_code: int | None,
        body: bytearray,
        deadline: float,
    ) -> None:
        digest = hashlib.sha256(body).hexdigest() if body else None
        self._guard.record_response(
            status_code=status_code,
            body_sha256=digest,
            body_complete=False,
            json_object=False,
            within_deadline=self._monotonic() <= deadline,
        )

    def _record_if_unset(
        self,
        status_code: int | None,
        body: bytearray,
        deadline: float,
    ) -> None:
        metadata = self._guard.response_metadata
        if metadata.status_code is None and metadata.body_sha256 is None:
            self._record_partial(status_code, body, deadline)


__all__ = ["HttpJsonTransport"]
