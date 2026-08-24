"""FastAPI composition root."""

from fastapi import FastAPI

from sketch2life.interfaces.http.routers.health import router as health_router


def create_app() -> FastAPI:
    """Create the health-only foundation app."""
    application = FastAPI(
        title="Sketch2Life API",
        version="0.0.0",
        docs_url="/docs",
        redoc_url=None,
    )
    application.include_router(health_router)
    return application
