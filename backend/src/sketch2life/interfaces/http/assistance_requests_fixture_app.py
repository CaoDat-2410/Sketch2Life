"""Isolated FIXTURE/TEST composition for CMD-32/CMD-33 (BE2-03 A1).

Never imported by ``interfaces/http/app.py``. Principals are resolved from synthetic
``Authorization: Fixture <name>`` values mapped in memory; this is a test double for the
identity port and must not be reused as live authentication.
"""

from __future__ import annotations

from collections.abc import Mapping

from fastapi import FastAPI, Request

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.application.services.assistance import AssistanceService
from sketch2life.interfaces.http.routers.assistance_requests import (
    CANDIDATE_PREFIX,
    build_assistance_requests_router,
)

FIXTURE_SCHEME = "Fixture "


def create_assistance_requests_fixture_app(
    service: AssistanceService,
    principals: Mapping[str, Principal],
    *,
    prefix: str = CANDIDATE_PREFIX,
) -> FastAPI:
    known = dict(principals)

    def resolve(request: Request) -> Principal | None:
        header = request.headers.get("authorization", "")
        if not header.startswith(FIXTURE_SCHEME):
            return None
        return known.get(header.removeprefix(FIXTURE_SCHEME).strip())

    app = FastAPI(title="sketch2life-assistance-requests-fixture", docs_url=None,
                  redoc_url=None, openapi_url=None)
    app.include_router(build_assistance_requests_router(service, resolve, prefix=prefix))
    app.state.fixture_only = True
    return app


__all__ = ["FIXTURE_SCHEME", "create_assistance_requests_fixture_app"]
