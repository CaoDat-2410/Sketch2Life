"""Teacher activity, occurrence history, and own-profile read route."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.lesson_occurrences import (
    LessonOccurrencePageV1,
    OccurrenceStateV1,
)
from sketch2life.contracts.schemas.teacher_workspace import TeacherProfileV1
from sketch2life.infrastructure.lesson_occurrences.service import LessonOccurrenceService
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.be1_common import failure
from sketch2life.interfaces.http.routers.lesson_occurrences import (
    _READ_HEADERS,
    _call,
    get_occurrence_service,
)

router = APIRouter(prefix="/api/teacher/v1")


def _active_teacher_identity(
    db: Session, principal: VerifiedPrincipal
) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.issuer != principal.issuer
        or identity.account_role != "teacher"
    ):
        raise failure(403, "ACTION_NOT_ALLOWED", "The action is not allowed for this role")
    return identity


def _database_unavailable(db: Session) -> HTTPException:
    db.rollback()
    return failure(503, "DATABASE_UNAVAILABLE", "Database service is temporarily unavailable")


def _provider_unavailable() -> HTTPException:
    return failure(
        503,
        "IDENTITY_PROVIDER_UNAVAILABLE",
        "Identity service is temporarily unavailable",
    )


@router.get(
    "/organizations/{organization_id}/history",
    response_model=LessonOccurrencePageV1,
    tags=["Lesson Occurrences"],
)
def list_teacher_history(
    organization_id: str,
    response: Response,
    state: OccurrenceStateV1 | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    cursor: str | None = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonOccurrenceService = Depends(get_occurrence_service),
) -> dict[str, Any]:
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    return _call(
        lambda: service.list_teacher_history(
            organization_id=organization_id,
            principal=principal,
            state=state,
            limit=limit,
            cursor=cursor,
        )
    )


@router.get(
    "/me/profile",
    response_model=TeacherProfileV1,
    tags=["BE1 — Organizations & Classes"],
)
def read_teacher_profile(
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Read the active Teacher's own profile.

    display-name edit is not in the SRS; owner dropped it (2026-11-25)
    """
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Vary"] = "Authorization"
    try:
        identity = _active_teacher_identity(db, principal)
    except SQLAlchemyError:
        raise _database_unavailable(db) from None
    provisioner = getattr(request.app.state, "identity_account_provisioner", None)
    read_profiles = getattr(provisioner, "get_account_profiles", None)
    if not callable(read_profiles):
        raise _provider_unavailable()
    try:
        profiles = read_profiles([principal.subject])
        profile = profiles.get(principal.subject)
    except Exception:
        raise _provider_unavailable() from None
    if profile is None:
        raise _provider_unavailable()
    return {
        "contract": "TeacherProfileV1",
        "account_ref": identity.account_id,
        "display_name": profile.display_name,
        "email": profile.email,
    }
