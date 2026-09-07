"""FastAPI composition root."""

from fastapi import FastAPI

from sketch2life.interfaces.http.routers.health import router as health_router
from sketch2life.interfaces.http.routers.live_understanding import (
    router as live_understanding_router,
)


def create_app() -> FastAPI:
    """Create the foundation app with the approved local live-AI route."""
    application = FastAPI(
        title="Sketch2Life API",
        version="0.0.0",
        docs_url="/docs",
        redoc_url=None,
    )
    application.include_router(health_router)
    application.include_router(live_understanding_router)
    return application
