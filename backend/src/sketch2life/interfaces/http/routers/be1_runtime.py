"""Versioned runtime router composed from BE1 capability modules."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from sketch2life.interfaces.http.be1_runtime import get_db
from sketch2life.interfaces.http.routers import (
    be1_artifacts,
    be1_canvas,
    be1_records,
    be1_registry,
    be1_sessions,
)
from sketch2life.interfaces.http.routers.be1_common import BE1_ERROR_RESPONSES

router = APIRouter(responses=BE1_ERROR_RESPONSES)
router.include_router(be1_registry.router)
router.include_router(be1_sessions.router)
router.include_router(be1_canvas.router)
router.include_router(be1_artifacts.router)
router.include_router(be1_records.router)


@router.get("/api/be1/v1/health", tags=["BE1 runtime v1"])
def be1_health(db: Session = Depends(get_db)) -> dict[str, str]:
    del db
    return {"status": "ready", "database": "postgresql", "api": "be1-v1"}


__all__ = ["router"]
