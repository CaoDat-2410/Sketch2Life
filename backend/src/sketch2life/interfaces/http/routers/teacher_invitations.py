"""School Manager Teacher invitation and resend routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, NoReturn, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, Response
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.teacher_invitations import (
    TeacherInvitationError,
    TeacherInvitationIdempotencyMismatch,
    TeacherInvitationIdentityUnavailable,
    TeacherInvitationKeyUnavailable,
    TeacherInvitationNotFound,
    TeacherInvitationSetupUnavailable,
    TeacherInvitationStoreUnavailable,
    TeacherInvitationWriteConflict,
)
from sketch2life.application.services.teacher_invitations import TeacherInvitationService
from sketch2life.contracts.schemas.teacher_invitations import (
    TeacherInvitationRequest,
    TeacherInvitationResponse,
)
from sketch2life.infrastructure.persistence.be1_models import OrganizationModel
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.be1_common import (
    BE1_ERROR_RESPONSES,
    require_assignment,
)

router = APIRouter(
    prefix="/api/be1/v1",
    tags=["BE1 — Organizations & Classes"],
    responses=cast(dict[int | str, dict[str, Any]], BE1_ERROR_RESPONSES),
)

_NO_STORE = {"Cache-Control": "private, no-store"}
def failure(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
        headers=_NO_STORE,
    )


def require_teacher_invitation_manager(
    organization_id: Annotated[str, Path(min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> VerifiedPrincipal:
    """Reauthorize active School Manager scope before any receipt lookup or replay."""
    assignments = require_assignment(
        db,
        principal,
        organization_id,
        roles={"school_admin"},
    )
    if not any(row.role == "school_admin" and row.class_id is None for row in assignments):
        raise failure(404, "RESOURCE_NOT_FOUND", "The requested resource was not found")
    organization = db.get(OrganizationModel, organization_id)
    if organization is None or organization.state != "active":
        raise failure(404, "RESOURCE_NOT_FOUND", "The requested resource was not found")
    return principal


def get_teacher_invitation_service(
    request: Request,
    db: Session = Depends(get_db),
) -> TeacherInvitationService:
    factory = getattr(request.app.state, "teacher_invitation_service_factory", None)
    if not callable(factory):
        raise failure(503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable")
    service_factory = cast(Callable[[Session], TeacherInvitationService], factory)
    return service_factory(db)


@router.post(
    "/organizations/{organization_id}/teacher-invitations",
    status_code=202,
    response_model=TeacherInvitationResponse,
)
def invite_teacher(
    organization_id: Annotated[str, Path(min_length=1, max_length=128)],
    payload: TeacherInvitationRequest,
    request: Request,
    response: Response,
    idempotency_key_header: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=1,
            max_length=128,
            description="Required; 1–128 printable ASCII characters.",
        ),
    ],
    principal: VerifiedPrincipal = Depends(require_teacher_invitation_manager),
    service: TeacherInvitationService = Depends(get_teacher_invitation_service),
) -> TeacherInvitationResponse:
    response.headers["Cache-Control"] = "private, no-store"
    idempotency_key = parse_idempotency_key(request)
    try:
        result = service.invite_teacher(
            principal_subject=principal.subject,
            principal_issuer=principal.issuer,
            organization_id=organization_id,
            email=str(payload.email),
            idempotency_key=idempotency_key,
        )
    except TeacherInvitationError as exc:
        _raise_http_error(exc)
    return TeacherInvitationResponse(account_ref=result.account_ref, status=result.status)


@router.post(
    "/organizations/{organization_id}/teacher-invitations/{account_ref}/resend",
    status_code=202,
    response_model=TeacherInvitationResponse,
)
def resend_teacher_invitation(
    organization_id: Annotated[str, Path(min_length=1, max_length=128)],
    account_ref: Annotated[str, Path(min_length=1, max_length=36)],
    request: Request,
    response: Response,
    idempotency_key_header: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=1,
            max_length=128,
            description="Required; 1–128 printable ASCII characters.",
        ),
    ],
    principal: VerifiedPrincipal = Depends(require_teacher_invitation_manager),
    service: TeacherInvitationService = Depends(get_teacher_invitation_service),
) -> TeacherInvitationResponse:
    response.headers["Cache-Control"] = "private, no-store"
    idempotency_key = parse_idempotency_key(request)
    try:
        result = service.resend_teacher_invitation(
            principal_subject=principal.subject,
            principal_issuer=principal.issuer,
            organization_id=organization_id,
            account_ref=account_ref,
            idempotency_key=idempotency_key,
        )
    except TeacherInvitationError as exc:
        _raise_http_error(exc)
    return TeacherInvitationResponse(account_ref=result.account_ref, status=result.status)


def _raise_http_error(error: TeacherInvitationError) -> NoReturn:
    if isinstance(error, TeacherInvitationIdempotencyMismatch):
        raise failure(
            400,
            "INVALID_IDEMPOTENCY_KEY",
            "Idempotency-Key was already used for another request",
        ) from None
    if isinstance(error, TeacherInvitationNotFound):
        raise failure(404, "RESOURCE_NOT_FOUND", "The requested resource was not found") from None
    if isinstance(error, (TeacherInvitationSetupUnavailable, TeacherInvitationWriteConflict)):
        raise failure(409, "ACCOUNT_SETUP_UNAVAILABLE", "Account setup is unavailable") from None
    if isinstance(error, TeacherInvitationIdentityUnavailable):
        raise failure(
            503,
            "IDENTITY_PROVIDER_UNAVAILABLE",
            "Identity service is temporarily unavailable",
        ) from None
    if isinstance(error, TeacherInvitationKeyUnavailable):
        raise failure(
            503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable"
        ) from None
    if isinstance(error, TeacherInvitationStoreUnavailable):
        raise failure(
            503, "DATABASE_UNAVAILABLE", "The service is temporarily unavailable"
        ) from None
    raise failure(503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable") from None
