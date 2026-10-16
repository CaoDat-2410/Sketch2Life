"""Isolated FIXTURE/TEST composition for CMD-34 (BE2-02 C1).

Never imported by ``interfaces/http/app.py``. Principals are resolved from synthetic
``Authorization: Fixture <token>`` values mapped in memory; this is a test double for the
identity port and must not be reused as live authentication.
"""

from __future__ import annotations

from collections.abc import Mapping

from fastapi import FastAPI, Request

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.application.services.vision_analysis import VisionAnalysisService
from sketch2life.interfaces.http.routers.analysis_corrections import (
    CANDIDATE_PREFIX,
    build_analysis_corrections_router,
)

FIXTURE_SCHEME = "Fixture "


def create_analysis_corrections_fixture_app(
    service: VisionAnalysisService,
    principals: Mapping[str, Principal],
    *,
    prefix: str = CANDIDATE_PREFIX,
) -> FastAPI:
    tokens = dict(principals)

    def resolve(request: Request) -> Principal | None:
        header = request.headers.get("authorization", "")
        if not header.startswith(FIXTURE_SCHEME):
            return None
        return tokens.get(header.removeprefix(FIXTURE_SCHEME).strip())

    app = FastAPI(title="sketch2life-analysis-corrections-fixture", docs_url=None,
                  redoc_url=None, openapi_url=None)
    app.include_router(build_analysis_corrections_router(service, resolve, prefix=prefix))
    app.state.fixture_only = True
    return app


__all__ = ["FIXTURE_SCHEME", "create_analysis_corrections_fixture_app"]
