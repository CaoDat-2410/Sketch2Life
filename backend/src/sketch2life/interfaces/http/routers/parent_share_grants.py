"""Parent-owned share grant and delivery-history routes (T-SHARE1)."""

# FastAPI dependencies intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import re
from typing import Any, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_roles import ParentRoleReader, ParentRoleStoreUnavailable
from sketch2life.contracts.schemas.profile_sharing import (
    CreateShareGrantRequestV1,
    ParentShareDeliveryListV1,
    ParentShareGrantCreatedV1,
    ParentShareGrantListV1,
    ParentShareGrantV1,
)
from sketch2life.domain.profile_sharing import (
    ShareFieldError,
    normalize_granted_fields,
)
from sketch2life.infrastructure.persistence.be1_parent_role_adapter import Be1ParentRoleAdapter
from sketch2life.infrastructure.profile_sharing.service import (
    create_grant,
    get_grant,
    list_deliveries,
    list_grants,
    revoke_grant,
)
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.api_conventions import (
    decode_time_cursor,
    encode_cursor,
    parse_idempotency_key,
)
from sketch2life.interfaces.http.be1_runtime import (
    Be1Runtime,
    get_db,
    get_runtime,
    get_verified_adult,
)
from sketch2life.interfaces.http.error_envelope import PARENT_SHARE_GRANTS_BASE
from sketch2life.interfaces.http.profile_sharing_errors import (
    call_profile_share_service as _share_call,
)

router = APIRouter(tags=["Parent Profiles"])
_READ_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Authorization"}
_ETAG_PATTERN = re.compile(r'^"([1-9][0-9]*)"$')


def get_share_grant_role_reader(
    runtime: Be1Runtime = Depends(get_runtime),
) -> ParentRoleReader:
    if runtime.session_factory is None:
        raise HTTPException(status_code=503, detail={"code": "DATABASE_NOT_CONFIGURED"}) from None
    return Be1ParentRoleAdapter(runtime.session_factory)


def _require_active_parent(principal: VerifiedPrincipal, role_reader: ParentRoleReader) -> None:
    try:
        active = role_reader.has_active_parent_role(principal=principal)
    except ParentRoleStoreUnavailable:
        raise HTTPException(status_code=503, detail={"code": "DATABASE_UNAVAILABLE"}) from None
    if not active:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"}) from None


def _invalid(field: str, code: str) -> NoReturn:
    raise HTTPException(
        status_code=400,
        detail={
            "code": "INVALID_REQUEST",
            "field_errors": [{"field": field, "code": code}],
        },
    )


def _uuid(raw: str, field: str) -> UUID:
    try:
        return UUID(raw)
    except (TypeError, ValueError):
        _invalid(field, "INVALID_FORMAT")


def _page_query(request: Request, *, profile_required: bool) -> tuple[UUID | None, int, str | None]:
    query = request.query_params
    allowed = {"profile_id", "limit", "cursor"} if profile_required else {"limit", "cursor"}
    unknown = sorted(set(query.keys()) - allowed)
    if unknown:
        _invalid(unknown[0], "UNKNOWN_FIELD")
    profile_id: UUID | None = None
    profile_values = query.getlist("profile_id")
    if profile_required:
        if not profile_values:
            _invalid("profile_id", "REQUIRED")
        if len(profile_values) != 1:
            _invalid("profile_id", "INVALID_FORMAT")
        profile_id = _uuid(profile_values[0], "profile_id")
    limit_values = query.getlist("limit")
    if len(limit_values) > 1:
        _invalid("limit", "INVALID_FORMAT")
    limit = 25
    if limit_values:
        raw_limit = limit_values[0]
        if not raw_limit.isascii() or not raw_limit.isdecimal():
            _invalid("limit", "INVALID_FORMAT")
        limit = int(raw_limit)
        if not 1 <= limit <= 100:
            _invalid("limit", "OUT_OF_RANGE")
    cursor_values = query.getlist("cursor")
    if len(cursor_values) > 1:
        _invalid("cursor", "INVALID_FORMAT")
    cursor = cursor_values[0] if cursor_values else None
    if cursor is not None and not 1 <= len(cursor) <= 2048:
        _invalid("cursor", "INVALID_FORMAT")
    return profile_id, limit, cursor


def _if_match(request: Request) -> int:
    values = request.headers.getlist("If-Match")
    if not values:
        _invalid("If-Match", "REQUIRED")
    if len(values) != 1:
        _invalid("If-Match", "INVALID_FORMAT")
    match = _ETAG_PATTERN.fullmatch(values[0])
    if match is None:
        _invalid("If-Match", "INVALID_FORMAT")
    return int(match.group(1))


def _set_read_headers(response: Response) -> None:
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value


_IDEMPOTENCY_PARAMETER: dict[str, Any] = {
    "name": "Idempotency-Key",
    "in": "header",
    "required": True,
    "schema": {"type": "string", "minLength": 1, "maxLength": 128},
}
_IF_MATCH_PARAMETER: dict[str, Any] = {
    "name": "If-Match",
    "in": "header",
    "required": True,
    "schema": {"type": "string"},
}


@router.post(
    PARENT_SHARE_GRANTS_BASE,
    response_model=ParentShareGrantCreatedV1,
    status_code=status.HTTP_201_CREATED,
    operation_id="parentCreateShareGrantV1",
    openapi_extra={"parameters": [_IDEMPOTENCY_PARAMETER]},
)
async def create_parent_share_grant(
    request: Request,
    response: Response,
    body: CreateShareGrantRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    role_reader: ParentRoleReader = Depends(get_share_grant_role_reader),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_active_parent(principal, role_reader)
    key = parse_idempotency_key(request)
    try:
        fields = normalize_granted_fields(body.granted_fields)
    except ShareFieldError as error:
        _invalid(error.field, error.code)
    result, etag = _share_call(
        create_grant,
        db,
        principal,
        profile_id=body.profile_id,
        granted_fields=fields,
        idempotency_key=key,
    )
    response.headers["Location"] = f"{PARENT_SHARE_GRANTS_BASE}/{result['share_grant_id']}"
    response.headers["ETag"] = etag
    response.headers["Vary"] = "Authorization"
    return result


@router.get(
    PARENT_SHARE_GRANTS_BASE,
    response_model=ParentShareGrantListV1,
    operation_id="parentListShareGrantsV1",
)
def list_parent_share_grants(
    request: Request,
    response: Response,
    profile_id: UUID = Query(...),
    limit: int = Query(25, ge=1, le=100),
    cursor_value: str | None = Query(default=None, alias="cursor"),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    role_reader: ParentRoleReader = Depends(get_share_grant_role_reader),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_active_parent(principal, role_reader)
    parsed_profile_id, parsed_limit, parsed_cursor = _page_query(request, profile_required=True)
    if (parsed_profile_id, parsed_limit, parsed_cursor) != (profile_id, limit, cursor_value):
        _invalid("query", "INVALID_FORMAT")
    _set_read_headers(response)
    scope = f"parent-share-grants:{parent_scope_ref(principal)}:{profile_id}"
    decoded_cursor = None
    if cursor_value is not None:
        cursor_time, item_id = decode_time_cursor(cursor_value, scope=scope)
        try:
            cursor_id = UUID(item_id)
        except (TypeError, ValueError):
            _invalid("cursor", "INVALID_FORMAT")
        decoded_cursor = (cursor_time, cursor_id)
    result, next_cursor = _share_call(
        list_grants,
        db,
        principal,
        profile_id=profile_id,
        limit=limit,
        cursor=decoded_cursor,
    )
    result["next_cursor"] = (
        encode_cursor(
            scope=scope,
            sort_key=next_cursor[0].isoformat(),
            item_id=next_cursor[1],
        )
        if next_cursor is not None
        else None
    )
    return result


@router.get(
    f"{PARENT_SHARE_GRANTS_BASE}/{{share_grant_id}}",
    response_model=ParentShareGrantV1,
    operation_id="parentGetShareGrantV1",
)
def get_parent_share_grant(
    share_grant_id: UUID,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    role_reader: ParentRoleReader = Depends(get_share_grant_role_reader),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_active_parent(principal, role_reader)
    result, etag = _share_call(get_grant, db, principal, share_grant_id=share_grant_id)
    response.headers["ETag"] = etag
    _set_read_headers(response)
    return result


@router.post(
    f"{PARENT_SHARE_GRANTS_BASE}/{{share_grant_id}}/revoke",
    response_model=ParentShareGrantV1,
    operation_id="parentRevokeShareGrantV1",
    openapi_extra={"parameters": [_IF_MATCH_PARAMETER, _IDEMPOTENCY_PARAMETER]},
)
def revoke_parent_share_grant(
    share_grant_id: UUID,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    role_reader: ParentRoleReader = Depends(get_share_grant_role_reader),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_active_parent(principal, role_reader)
    expected = _if_match(request)
    key = parse_idempotency_key(request)
    result, etag = _share_call(
        revoke_grant,
        db,
        principal,
        share_grant_id=share_grant_id,
        expected_revision=expected,
        idempotency_key=key,
    )
    response.headers["ETag"] = etag
    response.headers["Vary"] = "Authorization"
    return result


@router.get(
    f"{PARENT_SHARE_GRANTS_BASE}/{{share_grant_id}}/deliveries",
    response_model=ParentShareDeliveryListV1,
    operation_id="parentListShareDeliveriesV1",
)
def list_parent_share_deliveries(
    share_grant_id: UUID,
    request: Request,
    response: Response,
    limit: int = Query(25, ge=1, le=100),
    cursor_value: str | None = Query(default=None, alias="cursor"),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    role_reader: ParentRoleReader = Depends(get_share_grant_role_reader),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_active_parent(principal, role_reader)
    _profile_id, parsed_limit, parsed_cursor = _page_query(request, profile_required=False)
    if (parsed_limit, parsed_cursor) != (limit, cursor_value):
        _invalid("query", "INVALID_FORMAT")
    _set_read_headers(response)
    scope = f"parent-share-deliveries:{share_grant_id}"
    decoded_cursor = None
    if cursor_value is not None:
        cursor_time, item_id = decode_time_cursor(cursor_value, scope=scope)
        try:
            cursor_id = UUID(item_id)
        except (TypeError, ValueError):
            _invalid("cursor", "INVALID_FORMAT")
        decoded_cursor = (cursor_time, str(cursor_id))
    result, next_cursor = _share_call(
        list_deliveries,
        db,
        principal,
        share_grant_id=share_grant_id,
        limit=limit,
        cursor=decoded_cursor,
    )
    result["next_cursor"] = (
        encode_cursor(
            scope=scope,
            sort_key=next_cursor[0].isoformat(),
            item_id=next_cursor[1],
        )
        if next_cursor is not None
        else None
    )
    return result


__all__ = ["router"]
