"""Parent-owned synthetic profile HTTP operations."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from typing import Any, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.parent_profiles import ParentProfileService
from sketch2life.contracts.schemas.parent_profiles import (
    CreateParentProfileRequest,
    ParentErrorResponse,
    ParentProfileReference,
    ParentProfileView,
    PatchParentProfileRequest,
)
from sketch2life.domain.parent_profiles import ParentProfileError, ProfileSnapshot
from sketch2life.interfaces.http.parent_runtime import (
    get_parent_principal,
    get_parent_profile_service,
    parent_idempotency_key,
    parent_request_id,
)

PARENT_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ParentErrorResponse, "description": "The request is invalid"},
    401: {"model": ParentErrorResponse, "description": "Authentication is required or invalid"},
    404: {"model": ParentErrorResponse, "description": "The profile was not found"},
    409: {"model": ParentErrorResponse, "description": "The request conflicts with profile state"},
    503: {"model": ParentErrorResponse, "description": "A required service is unavailable"},
}

router = APIRouter(prefix="/v1/parent/profiles", tags=["Parent Profiles"])


def _raise_parent_error(error: ParentProfileError) -> NoReturn:
    detail: dict[str, object] = {"code": error.code, "message": error.message}
    if error.current_version is not None:
        detail["current_version"] = error.current_version
    raise HTTPException(
        status_code=error.status_code,
        detail=detail,
    ) from None


def _response_request_id(body: dict[str, object], fallback: str) -> str:
    request_id = body.get("request_id")
    return request_id if isinstance(request_id, str) and request_id else fallback


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ParentProfileReference,
    responses=PARENT_ERROR_RESPONSES,
)
def create_parent_profile(
    payload: CreateParentProfileRequest,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileService = Depends(get_parent_profile_service),
    idempotency_key: str = Depends(parent_idempotency_key),
) -> JSONResponse:
    try:
        result = service.create_profile(
            principal=principal,
            snapshot=ProfileSnapshot(
                display_name=payload.display_name,
                age_months=payload.age_months,
                interests_summary=payload.interests_summary,
            ),
            idempotency_key=idempotency_key,
            request_id=parent_request_id(request),
        )
    except ParentProfileError as error:
        _raise_parent_error(error)
    return JSONResponse(
        status_code=result.status_code,
        content=result.body,
        headers={
            "X-Request-ID": _response_request_id(
                result.body, parent_request_id(request)
            )
        },
    )


@router.get(
    "/{profile_id}",
    response_model=ParentProfileView,
    responses=PARENT_ERROR_RESPONSES,
)
def read_parent_profile(
    profile_id: UUID,
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileService = Depends(get_parent_profile_service),
) -> dict[str, object]:
    try:
        return service.get_profile(principal=principal, profile_id=profile_id)
    except ParentProfileError as error:
        _raise_parent_error(error)


@router.patch(
    "/{profile_id}",
    response_model=ParentProfileView,
    responses=PARENT_ERROR_RESPONSES,
)
def patch_parent_profile(
    profile_id: UUID,
    payload: PatchParentProfileRequest,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileService = Depends(get_parent_profile_service),
    idempotency_key: str = Depends(parent_idempotency_key),
) -> JSONResponse:
    try:
        result = service.patch_profile(
            principal=principal,
            profile_id=profile_id,
            expected_revision=payload.expected_revision,
            snapshot=ProfileSnapshot(
                display_name=payload.display_name,
                age_months=payload.age_months,
                interests_summary=payload.interests_summary,
            ),
            idempotency_key=idempotency_key,
            request_id=parent_request_id(request),
        )
    except ParentProfileError as error:
        _raise_parent_error(error)
    return JSONResponse(
        status_code=result.status_code,
        content=result.body,
        headers={
            "X-Request-ID": _response_request_id(
                result.body, parent_request_id(request)
            )
        },
    )


__all__ = ["router"]
