"""Infrastructure probes: `/health`, `/health/live`, `/health/ready` and `/metrics`.

`/health` and `/health/live` are public and carry no detail. `/health/ready` and `/metrics` are
operator probes guarded by `probe_access_denial` (SRS l.814); they are not part of the Swagger
contract. Readiness bounds its own wait with a PostgreSQL connect and statement timeout on a
short-lived connection, never with a thread-cancellation timeout alone.
"""

from __future__ import annotations

import threading
from typing import Literal, TypedDict

import anyio
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool

from sketch2life.interfaces.http.metrics import EXPOSITION_CONTENT_TYPE, MetricsRegistry
from sketch2life.interfaces.http.probe_access import probe_access_denial


class HealthResponse(TypedDict):
    status: Literal["ok"]
    service: str


class LiveResponse(TypedDict):
    status: Literal["ok"]


router = APIRouter(tags=["health"])

_NO_STORE = {"Cache-Control": "no-store"}
# libpq connect_timeout (seconds) and server-side statement_timeout (ms) bound the probe itself.
_PROBE_CONNECT_TIMEOUT_SECONDS = 2
_PROBE_STATEMENT_TIMEOUT_MS = 2000
# Outer wait for the worker thread: covers what libpq does not bound (for example name lookup).
_PROBE_OUTER_BOUND_SECONDS = 4.0
# At most this many probe threads exist at once; further probes answer "down" without a thread.
_MAX_PROBE_THREADS = 2
_probe_lock = threading.Lock()
_probe_threads = 0


class _ProbeSlot:
    """One counted probe thread; released exactly once, by the thread or by the caller."""

    def __init__(self) -> None:
        self.started = False
        self.released = False


def _acquire_probe_slot() -> _ProbeSlot | None:
    global _probe_threads
    with _probe_lock:
        if _probe_threads >= _MAX_PROBE_THREADS:
            return None
        _probe_threads += 1
        return _ProbeSlot()


def _release_probe_slot(slot: _ProbeSlot) -> None:
    global _probe_threads
    with _probe_lock:
        if not slot.released:
            slot.released = True
            _probe_threads -= 1


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return {"status": "ok", "service": "sketch2life-api"}


@router.get("/health/live", response_model=LiveResponse)
def health_live() -> LiveResponse:
    """Process liveness: no dependency is called and no detail is returned."""
    return {"status": "ok"}


def _probe_database(url: URL, slot: _ProbeSlot) -> bool:
    """Open a fresh connection with its own timeouts and run SELECT 1; any error is False."""
    with _probe_lock:
        if slot.released:
            return False
        slot.started = True
    try:
        engine = create_engine(
            url,
            poolclass=NullPool,
            hide_parameters=True,
            connect_args={
                "connect_timeout": _PROBE_CONNECT_TIMEOUT_SECONDS,
                "options": f"-c statement_timeout={_PROBE_STATEMENT_TIMEOUT_MS}",
            },
        )
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        finally:
            engine.dispose()
    except Exception:
        return False
    finally:
        _release_probe_slot(slot)


async def _database_is_up(request: Request) -> bool:
    runtime = getattr(request.app.state, "be1_runtime", None)
    engine = getattr(runtime, "engine", None)
    if engine is None or getattr(runtime, "database_error", None):
        return False
    slot = _acquire_probe_slot()
    if slot is None:
        return False
    try:
        with anyio.fail_after(_PROBE_OUTER_BOUND_SECONDS):
            return await anyio.to_thread.run_sync(
                _probe_database, engine.url, slot, abandon_on_cancel=True
            )
    except Exception:
        # Timeout (a TimeoutError) or any other failure: not ready.
        return False
    finally:
        # Also runs on cancellation (a BaseException). A started thread frees its own slot
        # when it ends; if the thread never started, free the slot here.
        with _probe_lock:
            never_started = not slot.started
        if never_started:
            _release_probe_slot(slot)


@router.get("/health/ready", include_in_schema=False, response_model=None)
async def health_ready(request: Request) -> Response:
    """Readiness: the database must answer. The body never carries error text or addresses."""
    denial = probe_access_denial(request)
    if denial is not None:
        return denial
    if await _database_is_up(request):
        return JSONResponse(
            {"status": "ready", "checks": {"database": "up"}}, headers=_NO_STORE
        )
    return JSONResponse(
        {"status": "not_ready", "checks": {"database": "down"}},
        status_code=503,
        headers=_NO_STORE,
    )


@router.get("/metrics", include_in_schema=False, response_model=None)
async def metrics(request: Request) -> Response:
    """Prometheus text exposition 0.0.4 for the operator; no database call."""
    denial = probe_access_denial(request)
    if denial is not None:
        return denial
    registry = getattr(request.app.state, "metrics_registry", None)
    if not isinstance(registry, MetricsRegistry):
        registry = MetricsRegistry()
    return Response(
        registry.render(), media_type=EXPOSITION_CONTENT_TYPE, headers=_NO_STORE
    )


async def _hidden_probe_path_other_method() -> Response:
    """Any method other than GET on a hidden probe path answers like an unknown path (404)."""
    raise HTTPException(status_code=404)


for _probe_path in ("/health/ready", "/metrics"):
    router.add_api_route(
        _probe_path,
        _hidden_probe_path_other_method,
        methods=["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE"],
        include_in_schema=False,
        response_model=None,
    )
