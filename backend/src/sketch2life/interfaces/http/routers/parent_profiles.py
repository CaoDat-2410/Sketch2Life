"""Parent-owned synthetic profile HTTP operations."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import json
from typing import Any, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_roles import (
    ParentRoleReader,
    ParentRoleStoreUnavailable,
)
from sketch2life.application.services.parent_profile_context import (
    ParentProfileContextService,
)
from sketch2life.application.services.parent_profiles import ParentProfileService
from sketch2life.application.services.support_needs import ParentSupportNeedsService
from sketch2life.contracts.schemas.parent_profiles import (
    CreateParentContextEntryRequest,
    CreateParentProfileRequest,
    ParentContextEntryEnvelope,
    ParentContextEntryListView,
    ParentErrorResponse,
    ParentProfileDeletePendingView,
    ParentProfileListView,
    ParentProfileReference,
    ParentProfileView,
    ParentRequest,
    ParentSupportNeedsV1,
    ParentSupportNeedsWriteV1,
    PatchParentProfileRequest,
    SupportNeedsPutV1,
    parent_field_errors,
)
from sketch2life.domain.parent_profile_context import (
    ContextEntryDraft,
    parse_approximate_date,
)
from sketch2life.domain.parent_profiles import ParentProfileError, ProfileSnapshot
from sketch2life.interfaces.http.parent_runtime import (
    get_parent_principal,
    get_parent_profile_context_service,
    get_parent_profile_service,
    get_parent_role_reader,
    get_parent_support_needs_service,
    parent_request_id,
)

PARENT_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ParentErrorResponse, "description": "The request is invalid"},
    401: {"model": ParentErrorResponse, "description": "Authentication is required or invalid"},
    404: {
        "model": ParentErrorResponse,
        "description": "The profile was not found, or the caller is not an active Parent",
    },
    409: {"model": ParentErrorResponse, "description": "The request conflicts with profile state"},
    503: {"model": ParentErrorResponse, "description": "A required service is unavailable"},
}

router = APIRouter(prefix="/v1/parent/profiles", tags=["Parent Profiles"])

_NO_STORE = "private, no-store"

_IDEMPOTENCY_PARAMETER = {
    "name": "Idempotency-Key",
    "in": "header",
    "required": True,
    "schema": {"type": "string", "minLength": 1, "maxLength": 128},
}


def _raise_parent_error(error: ParentProfileError) -> NoReturn:
    detail: dict[str, object] = {"code": error.code, "message": error.message}
    if error.current_version is not None:
        detail["current_version"] = error.current_version
    if error.field_errors:
        detail["field_errors"] = error.field_errors
    raise HTTPException(status_code=error.status_code, detail=detail) from None


def _response_request_id(body: dict[str, object], fallback: str) -> str:
    request_id = body.get("request_id")
    return request_id if isinstance(request_id, str) and request_id else fallback


def _require_active_parent(
    principal: VerifiedPrincipal, role_reader: ParentRoleReader
) -> None:
    try:
        active_parent = role_reader.has_active_parent_role(principal=principal)
    except ParentRoleStoreUnavailable:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PARENT_STORE_UNAVAILABLE",
                "message": "The profile store is unavailable",
            },
        ) from None
    if not active_parent:
        # CONV-1 (SRS l.864-865, C-D4, OD-18b): a caller who is not an active Parent is out of
        # scope for every profile route, so it gets the family's own not-found body.
        raise HTTPException(
            status_code=404,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile was not found"},
        )


def _parse_profile_id(request: Request, declared_value: str) -> UUID:
    raw_value = request.path_params.get("profile_id")
    if not isinstance(raw_value, str) or raw_value != declared_value:
        _raise_invalid([{"field": "profile_id", "code": "INVALID_FORMAT"}])
    try:
        return UUID(raw_value)
    except ValueError:
        _raise_invalid([{"field": "profile_id", "code": "INVALID_FORMAT"}])


def _idempotency_key(request: Request) -> tuple[str | None, list[dict[str, str]]]:
    values = request.headers.getlist("Idempotency-Key")
    if not values:
        return None, [{"field": "Idempotency-Key", "code": "REQUIRED"}]
    if len(values) != 1:
        return None, [{"field": "Idempotency-Key", "code": "INVALID_FORMAT"}]
    raw_value = values[0]
    if not 1 <= len(raw_value) <= 128 or any(
        ord(char) < 33 or ord(char) > 126 for char in raw_value
    ):
        return None, [{"field": "Idempotency-Key", "code": "INVALID_FORMAT"}]
    return raw_value, []


async def _body_model(
    request: Request,
    model_type: type[ParentRequest],
) -> tuple[ParentRequest | None, list[dict[str, str]]]:
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, [{"field": "body", "code": "INVALID_FORMAT"}]
    try:
        return model_type.model_validate(payload), []
    except ValidationError as error:
        return None, parent_field_errors(error.errors())


def _raise_invalid(field_errors: list[dict[str, str]]) -> NoReturn:
    normalized = [
        {"field": field, "code": code}
        for field, code in sorted(
            {(item["field"], item["code"]) for item in field_errors}
        )
    ]
    raise HTTPException(
        status_code=400,
        detail={
            "code": "INVALID_REQUEST",
            "message": "The request is invalid",
            "field_errors": normalized,
        },
    )


def _list_query(
    request: Request,
) -> tuple[int | None, str | None, list[dict[str, str]]]:
    query = request.query_params
    errors: list[dict[str, str]] = []
    limit_values = query.getlist("limit")
    limit: int | None = 25
    if len(limit_values) > 1:
        limit = None
        errors.append({"field": "limit", "code": "INVALID_FORMAT"})
    elif limit_values:
        raw_limit = limit_values[0]
        if not raw_limit or not raw_limit.isascii() or not raw_limit.isdigit():
            limit = None
            errors.append({"field": "limit", "code": "INVALID_TYPE"})
        else:
            limit = int(raw_limit)
            if not 1 <= limit <= 100:
                errors.append({"field": "limit", "code": "OUT_OF_RANGE"})
    cursor_values = query.getlist("cursor")
    cursor: str | None = None
    if len(cursor_values) > 1:
        errors.append({"field": "cursor", "code": "INVALID_FORMAT"})
    elif cursor_values:
        cursor = cursor_values[0]
    if set(query.keys()) - {"limit", "cursor"}:
        errors.append({"field": "<unknown>", "code": "UNKNOWN_FIELD"})
    return limit, cursor, errors


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ParentProfileReference,
    responses=PARENT_ERROR_RESPONSES,
    openapi_extra={
        "parameters": [_IDEMPOTENCY_PARAMETER],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/CreateParentProfileRequest"}
                }
            },
        },
    },
)
async def create_parent_profile(
    request: Request,
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileService = Depends(get_parent_profile_service),
    role_reader: ParentRoleReader = Depends(get_parent_role_reader),
) -> JSONResponse:
    _require_active_parent(principal, role_reader)
    idempotency_key, key_errors = _idempotency_key(request)
    payload, body_errors = await _body_model(request, CreateParentProfileRequest)
    errors = key_errors + body_errors
    if errors:
        _raise_invalid(errors)
    assert idempotency_key is not None
    assert isinstance(payload, CreateParentProfileRequest)
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
    "",
    response_model=ParentProfileListView,
    responses=PARENT_ERROR_RESPONSES,
    openapi_extra={
        "parameters": [
            {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
            {"name": "cursor", "in": "query", "required": False, "schema": {"type": "string"}},
        ]
    },
)
def list_parent_profiles(
    request: Request,
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileService = Depends(get_parent_profile_service),
    role_reader: ParentRoleReader = Depends(get_parent_role_reader),
) -> dict[str, object]:
    _require_active_parent(principal, role_reader)
    limit, cursor, field_errors = _list_query(request)
    if field_errors:
        _raise_invalid(field_errors)
    assert limit is not None
    try:
        result = service.list_profiles(principal=principal, limit=limit, cursor=cursor)
    except ParentProfileError as error:
        _raise_parent_error(error)
    return {
        "items": result.items,
        "next_cursor": result.next_cursor,
        "request_id": parent_request_id(request),
    }


@router.get(
    "/{profile_id}",
    response_model=ParentProfileView | ParentProfileDeletePendingView,
    responses=PARENT_ERROR_RESPONSES,
)
def read_parent_profile(
    request: Request,
    profile_id: str = Path(..., json_schema_extra={"format": "uuid"}),
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileService = Depends(get_parent_profile_service),
    role_reader: ParentRoleReader = Depends(get_parent_role_reader),
) -> dict[str, object]:
    parsed_id = _parse_profile_id(request, profile_id)
    try:
        service.assert_profile_owned(principal=principal, profile_id=parsed_id)
    except ParentProfileError as error:
        _raise_parent_error(error)
    _require_active_parent(principal, role_reader)
    try:
        return service.get_profile(
            principal=principal,
            profile_id=parsed_id,
            request_id=parent_request_id(request),
        )
    except ParentProfileError as error:
        _raise_parent_error(error)


@router.patch(
    "/{profile_id}",
    response_model=ParentProfileView,
    responses=PARENT_ERROR_RESPONSES,
    openapi_extra={
        "parameters": [_IDEMPOTENCY_PARAMETER],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/PatchParentProfileRequest"}
                }
            },
        },
    },
)
async def patch_parent_profile(
    request: Request,
    profile_id: str = Path(..., json_schema_extra={"format": "uuid"}),
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileService = Depends(get_parent_profile_service),
    role_reader: ParentRoleReader = Depends(get_parent_role_reader),
) -> JSONResponse:
    parsed_id = _parse_profile_id(request, profile_id)
    try:
        service.assert_profile_owned(principal=principal, profile_id=parsed_id)
    except ParentProfileError as error:
        _raise_parent_error(error)
    _require_active_parent(principal, role_reader)
    idempotency_key, key_errors = _idempotency_key(request)
    payload, body_errors = await _body_model(request, PatchParentProfileRequest)
    errors = key_errors + body_errors
    if errors:
        _raise_invalid(errors)
    assert idempotency_key is not None
    assert isinstance(payload, PatchParentProfileRequest)
    try:
        result = service.patch_profile(
            principal=principal,
            profile_id=parsed_id,
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


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ParentProfileDeletePendingView,
    responses=PARENT_ERROR_RESPONSES,
    openapi_extra={"parameters": [_IDEMPOTENCY_PARAMETER]},
)
def request_parent_profile_deletion(
    request: Request,
    profile_id: str = Path(..., json_schema_extra={"format": "uuid"}),
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileService = Depends(get_parent_profile_service),
    role_reader: ParentRoleReader = Depends(get_parent_role_reader),
) -> JSONResponse:
    parsed_id = _parse_profile_id(request, profile_id)
    try:
        service.assert_profile_owned(principal=principal, profile_id=parsed_id)
    except ParentProfileError as error:
        _raise_parent_error(error)
    _require_active_parent(principal, role_reader)
    idempotency_key, field_errors = _idempotency_key(request)
    if field_errors:
        _raise_invalid(field_errors)
    assert idempotency_key is not None
    try:
        result = service.delete_profile(
            principal=principal,
            profile_id=parsed_id,
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


# T-12a (SRS l.263-265, l.497-499): the adult-entered context entries of a stable profile. Both
# routes act on an ACTIVE profile of the caller only; the order is the one of the profile PATCH:
# UUID, owner lookup (any state), active-Parent role, then key and body.
@router.get(
    "/{profile_id}/context-entries",
    operation_id="listParentProfileContextEntriesV1",
    response_model=ParentContextEntryListView,
    responses=PARENT_ERROR_RESPONSES,
    openapi_extra={
        "parameters": [
            {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
            {"name": "cursor", "in": "query", "required": False, "schema": {"type": "string"}},
        ]
    },
)
def list_parent_profile_context_entries(
    request: Request,
    profile_id: str = Path(..., json_schema_extra={"format": "uuid"}),
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileContextService = Depends(get_parent_profile_context_service),
    role_reader: ParentRoleReader = Depends(get_parent_role_reader),
) -> JSONResponse:
    parsed_id = _parse_profile_id(request, profile_id)
    try:
        service.assert_profile_owned(principal=principal, profile_id=parsed_id)
    except ParentProfileError as error:
        _raise_parent_error(error)
    _require_active_parent(principal, role_reader)
    limit, cursor, field_errors = _list_query(request)
    if field_errors:
        _raise_invalid(field_errors)
    assert limit is not None
    try:
        page = service.list_context_entries(
            principal=principal, profile_id=parsed_id, limit=limit, cursor=cursor
        )
    except ParentProfileError as error:
        _raise_parent_error(error)
    return JSONResponse(
        status_code=200,
        content={
            "context_entries": page.items,
            "next_cursor": page.next_cursor,
            "limit": limit,
        },
        headers={"Cache-Control": _NO_STORE},
    )


@router.post(
    "/{profile_id}/context-entries",
    operation_id="createParentProfileContextEntryV1",
    status_code=status.HTTP_201_CREATED,
    response_model=ParentContextEntryEnvelope,
    responses=PARENT_ERROR_RESPONSES,
    openapi_extra={
        "parameters": [_IDEMPOTENCY_PARAMETER],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/CreateParentContextEntryRequest"}
                }
            },
        },
    },
)
async def create_parent_profile_context_entry(
    request: Request,
    profile_id: str = Path(..., json_schema_extra={"format": "uuid"}),
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentProfileContextService = Depends(get_parent_profile_context_service),
    role_reader: ParentRoleReader = Depends(get_parent_role_reader),
) -> JSONResponse:
    parsed_id = _parse_profile_id(request, profile_id)
    try:
        service.assert_profile_owned(principal=principal, profile_id=parsed_id)
    except ParentProfileError as error:
        _raise_parent_error(error)
    _require_active_parent(principal, role_reader)
    idempotency_key, key_errors = _idempotency_key(request)
    payload, body_errors = await _body_model(request, CreateParentContextEntryRequest)
    errors = key_errors + body_errors
    if errors:
        _raise_invalid(errors)
    assert idempotency_key is not None
    assert isinstance(payload, CreateParentContextEntryRequest)
    try:
        result = service.create_context_entry(
            principal=principal,
            profile_id=parsed_id,
            entry=ContextEntryDraft(
                entry_kind=payload.entry_kind,
                short_text=payload.short_text,
                source_kind=payload.source_kind,
                source_ref=payload.source_ref,
                approximate_date=(
                    parse_approximate_date(payload.approximate_date)
                    if payload.approximate_date is not None
                    else None
                ),
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
            "X-Request-ID": _response_request_id(result.body, parent_request_id(request)),
            "Cache-Control": _NO_STORE,
        },
    )


# T-12c (SRS l.264 BR-20, l.499 FR-C-07, l.932, l.1922): the encrypted support needs of a profile.
# Order of both routes: UUID, owner (404), active Parent (404), key source (503), then on the
# PUT the key and body (400); the repository then refuses a profile in DELETE_PENDING (409),
# replays, checks the revision (409) and writes in one transaction. Nothing here logs or echoes
# a value; the no-store header keeps a decrypted answer out of caches.
@router.get(
    "/{profile_id}/support-needs",
    operation_id="parentGetSupportNeedsV1",
    response_model=ParentSupportNeedsV1,
    responses=PARENT_ERROR_RESPONSES,
)
def get_parent_profile_support_needs(
    request: Request,
    profile_id: str = Path(..., json_schema_extra={"format": "uuid"}),
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentSupportNeedsService = Depends(get_parent_support_needs_service),
    role_reader: ParentRoleReader = Depends(get_parent_role_reader),
) -> JSONResponse:
    parsed_id = _parse_profile_id(request, profile_id)
    try:
        service.assert_profile_owned(principal=principal, profile_id=parsed_id)
    except ParentProfileError as error:
        _raise_parent_error(error)
    _require_active_parent(principal, role_reader)
    try:
        service.require_available()
        body = service.get_support_needs(principal=principal, profile_id=parsed_id)
    except ParentProfileError as error:
        _raise_parent_error(error)
    return JSONResponse(
        status_code=200,
        content=body,
        headers={"Cache-Control": _NO_STORE, "X-Request-ID": parent_request_id(request)},
    )


@router.put(
    "/{profile_id}/support-needs",
    operation_id="parentPutSupportNeedsV1",
    response_model=ParentSupportNeedsWriteV1,
    responses=PARENT_ERROR_RESPONSES,
    openapi_extra={
        "parameters": [_IDEMPOTENCY_PARAMETER],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/SupportNeedsPutV1"}}
            },
        },
    },
)
async def put_parent_profile_support_needs(
    request: Request,
    profile_id: str = Path(..., json_schema_extra={"format": "uuid"}),
    principal: VerifiedPrincipal = Depends(get_parent_principal),
    service: ParentSupportNeedsService = Depends(get_parent_support_needs_service),
    role_reader: ParentRoleReader = Depends(get_parent_role_reader),
) -> JSONResponse:
    parsed_id = _parse_profile_id(request, profile_id)
    try:
        service.assert_profile_owned(principal=principal, profile_id=parsed_id)
    except ParentProfileError as error:
        _raise_parent_error(error)
    _require_active_parent(principal, role_reader)
    try:
        service.require_available()
    except ParentProfileError as error:
        _raise_parent_error(error)
    idempotency_key, key_errors = _idempotency_key(request)
    payload, body_errors = await _body_model(request, SupportNeedsPutV1)
    errors = key_errors + body_errors
    if errors:
        _raise_invalid(errors)
    assert idempotency_key is not None
    assert isinstance(payload, SupportNeedsPutV1)
    try:
        body = service.put_support_needs(
            principal=principal,
            profile_id=parsed_id,
            expected_revision=payload.expected_revision,
            category=payload.category,
            note=payload.note,
            idempotency_key=idempotency_key,
        )
    except ParentProfileError as error:
        _raise_parent_error(error)
    return JSONResponse(
        status_code=200,
        content=body,
        headers={"Cache-Control": _NO_STORE, "X-Request-ID": parent_request_id(request)},
    )


__all__ = ["router"]
