"""Access guard for the operator probes `/health/ready` and `/metrics` (T0.3, SRS l.814).

The probes are for the System Operator principal (SRS l.1602, l.1625), not for a user session.
Access rules, fail closed:

1. `Authorization: Bearer <credential>` equal to the configured `ops_probe_token`
   (constant-time comparison of SHA-256 digests); or
2. only when the environment is `local` or `test` and no credential is configured: a direct
   loopback request (loopback client and server, local Host, no proxy header).

A deployment that sets a credential never gets the loopback bypass. In `staging` and
`production` only the credential works. Denial: 401 with the shared error body when a credential
is configured, otherwise a plain 404 that is byte-identical to the answer for an unknown path.
The presented value is never logged or echoed.
"""

from __future__ import annotations

import hashlib
import hmac
from ipaddress import ip_address
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response

from sketch2life.infrastructure.config.settings import Settings, get_settings
from sketch2life.interfaces.http.error_envelope import build_error_body

_PROXY_HEADERS = frozenset({"forwarded", "x-forwarded-for", "x-real-ip"})


def is_loopback_address(address: object) -> bool:
    try:
        return ip_address(str(address)).is_loopback
    except ValueError:
        return False


def is_local_host_header(value: str) -> bool:
    try:
        parsed = urlsplit("http://" + value)
        return bool(
            parsed.hostname in {"127.0.0.1", "::1", "localhost"}
            and parsed.username is None and parsed.password is None
            and not parsed.path and not parsed.query and not parsed.fragment
            and (parsed.port is None or 1 <= parsed.port <= 65535)
        )
    except ValueError:
        return False


def is_direct_loopback_request(request: Request) -> bool:
    """Loopback client and server, local Host header and no proxy forwarding header."""
    client = request.scope.get("client")
    server = request.scope.get("server")
    if not client or not server:
        return False
    return (
        is_loopback_address(client[0])
        and is_loopback_address(server[0])
        and is_local_host_header(request.headers.get("host", ""))
        and not any(header in request.headers for header in _PROXY_HEADERS)
    )


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def _bearer_credential(request: Request) -> str | None:
    headers = request.headers.getlist("authorization")
    if len(headers) != 1:
        return None
    scheme, _, credential = headers[0].partition(" ")
    if scheme.lower() != "bearer" or not credential:
        return None
    return credential


def _settings(request: Request) -> Settings:
    runtime = getattr(request.app.state, "be1_runtime", None)
    settings = getattr(runtime, "settings", None)
    return settings if isinstance(settings, Settings) else get_settings()


def probe_access_denial(request: Request) -> Response | None:
    """Return None when the caller may use the probe, a 401 response, or raise a plain 404."""
    settings = _settings(request)
    configured = settings.ops_probe_token.get_secret_value() if settings.ops_probe_token else None
    if configured:
        presented = _bearer_credential(request)
        if presented is not None and hmac.compare_digest(_digest(presented), _digest(configured)):
            return None
        request_id = getattr(request.state, "be1_request_id", None) or str(uuid4())
        return JSONResponse(
            status_code=401,
            content=build_error_body(status=401, code="AUTH_REQUIRED", request_id=request_id),
            headers={"WWW-Authenticate": "Bearer", "X-Request-ID": request_id},
        )
    if settings.env in {"local", "test"} and is_direct_loopback_request(request):
        return None
    raise HTTPException(status_code=404)
