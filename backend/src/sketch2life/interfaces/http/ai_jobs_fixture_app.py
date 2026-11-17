"""Isolated FIXTURE/TEST composition for CMD-44 (BE2-01 Phase A).

Never imported by ``interfaces/http/app.py``. Principals are resolved from synthetic
``Authorization: Fixture <token>`` values mapped in memory; this is a test double for the P2
identity port and must not be reused as live authentication.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from fastapi import FastAPI, Request

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.application.services.ai_jobs import AiJobService
from sketch2life.interfaces.http.routers.ai_jobs import CANDIDATE_PREFIX, build_ai_jobs_router

FIXTURE_SCHEME = "Fixture "


def create_ai_jobs_fixture_app(
    service: AiJobService, principals: Mapping[str, Principal], *, prefix: str = CANDIDATE_PREFIX
) -> FastAPI:
    tokens = dict(principals)

    def resolve(request: Request) -> Principal | None:
        header = request.headers.get("authorization", "")
        if not header.startswith(FIXTURE_SCHEME):
            return None
        return tokens.get(header.removeprefix(FIXTURE_SCHEME).strip())

    app = FastAPI(title="sketch2life-ai-jobs-fixture", docs_url=None, redoc_url=None,
                  openapi_url=None)
    app.include_router(build_ai_jobs_router(service, resolve, prefix=prefix))
    app.state.fixture_only = True
    return app


def route_surface(routes: Iterable[object], prefix: str = "") -> set[tuple[str, str]]:
    """Flatten (path, method) pairs, including routers wrapped by ``include_router``."""

    surface: set[tuple[str, str]] = set()
    for route in routes:
        inner = getattr(route, "original_router", None)
        if inner is not None:
            context = getattr(route, "include_context", None)
            surface |= route_surface(inner.routes, prefix + str(getattr(context, "prefix", "")))
            continue
        path = getattr(route, "path", None)
        for method in getattr(route, "methods", None) or ():
            surface.add((prefix + str(path), str(method)))
    return surface


__all__ = ["FIXTURE_SCHEME", "create_ai_jobs_fixture_app", "route_surface"]
