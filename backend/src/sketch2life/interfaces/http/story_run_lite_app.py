"""A standalone FastAPI app; the Rev37 application and its OpenAPI catalog are untouched."""

from __future__ import annotations

from fastapi import FastAPI

from sketch2life.application.services.story_run_lite import StoryRunLiteService
from sketch2life.infrastructure.story_run_lite.composition import runtime_lifespan
from sketch2life.interfaces.http.routers.story_run_lite import install_error_handlers, router


def create_app(*, service: StoryRunLiteService | None = None) -> FastAPI:
    """Build an injectable API for tests or the goal-owned local runner."""

    app = FastAPI(
        title="StoryRun-lite Local Synthetic Parent API",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=None if service is not None else runtime_lifespan,
    )
    app.state.story_run_lite_service = service
    app.include_router(router)
    install_error_handlers(app)
    return app


app = create_app()

__all__ = ["app", "create_app"]
