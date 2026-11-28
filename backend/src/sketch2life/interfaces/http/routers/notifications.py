"""Notification inbox and endpoint routes (T-8a/T-8b; SRS l.812, l.1684-1685, l.1697).

Literal paths under ``/v1/notifications``. The inbox is the source of truth; this router never
sends an e-mail or push. Registration and revoke are Parent-scoped, keyed commands. Registration
fails closed unless proof and key adapters are injected; it does not imply provider delivery.
Inbox reads and mark-read continue to act only on the caller's own items.

Notes (T-8a implementation review): ``unread_count`` is a second statement without a shared
snapshot, so a concurrent insert may count an item the page does not hold (a badge only); a replayed
mark-read returns the first stored result even when the item has since expired (SRS l.1697); an item
id longer than 64 characters is a 400, one of 37-64 valid characters is a 404.
"""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import re
from typing import Annotated, Any, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, Response
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.push_endpoints import PushEndpointStoreUnavailable
from sketch2life.application.services.notifications import utc_iso
from sketch2life.application.services.push_endpoints import (
    PushEndpointCommandService,
    PushEndpointError,
    PushEndpointRegistration,
)
from sketch2life.contracts.schemas.notifications import (
    NotificationPageV1,
    NotificationReadAllV1,
    NotificationV1,
    PushEndpointRegistrationV1,
    PushEndpointV1,
)
from sketch2life.infrastructure.notifications.inbox_repository import (
    NotificationError,
    NotificationInboxService,
)
from sketch2life.infrastructure.notifications.push_endpoint_repository import SqlPushEndpointStore
from sketch2life.interfaces.http.api_conventions import (
    cursor_query,
    decode_time_cursor,
    encode_cursor,
    limit_query,
    parse_idempotency_key,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.error_envelope import NOTIFICATIONS_BASE

CURSOR_SCOPE = "notifications"
_STRONG_ETAG = re.compile(r'^"([1-9][0-9]*)"$', re.ASCII)

router = APIRouter(prefix=NOTIFICATIONS_BASE, tags=["Notifications"])

IdempotencyKeyHeader = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]
# A NUL byte can never be part of an id and PostgreSQL text cannot hold it: refuse it as a 400
# before any query instead of a retryable 503.
InboxItemId = Annotated[str, Path(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")]
EndpointId = Annotated[
    str,
    Path(
        pattern=r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$",
        description="Opaque push endpoint UUID.",
    ),
]
_READ_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Authorization"}


def get_notification_service(db: Session = Depends(get_db)) -> NotificationInboxService:
    return NotificationInboxService(db)


def get_push_endpoint_service(db: Session = Depends(get_db)) -> PushEndpointCommandService:
    # Production adapters remain unconfigured until proof and key sources receive security review.
    return PushEndpointCommandService(store=SqlPushEndpointStore(db))


def _raise(exc: NotificationError) -> NoReturn:
    raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None


def _raise_push(exc: PushEndpointError) -> NoReturn:
    detail: dict[str, object] = {"code": exc.code}
    if exc.current_version is not None:
        detail["current_version"] = exc.current_version
    raise HTTPException(status_code=exc.status_code, detail=detail) from None


def _strong_if_match(value: str | None, request: Request) -> int:
    match = _STRONG_ETAG.fullmatch(value or "")
    if match is None or len(request.headers.getlist("If-Match")) != 1:
        raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST"}) from None
    try:
        return int(match.group(1))
    except ValueError:
        raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST"}) from None


@router.get(
    "",
    response_model=NotificationPageV1,
    summary="Read the caller's notification inbox, newest first",
)
def list_notifications(
    response: Response,
    limit: int = limit_query(),
    cursor: str | None = cursor_query(),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: NotificationInboxService = Depends(get_notification_service),
) -> dict[str, Any]:
    after = decode_time_cursor(cursor, scope=CURSOR_SCOPE) if cursor is not None else None
    try:
        page = service.list_page(principal=principal, limit=limit, after=after)
    except NotificationError as exc:
        _raise(exc)
    next_cursor = None
    if page.has_more and page.last_created_at is not None and page.last_item_id is not None:
        next_cursor = encode_cursor(
            scope=CURSOR_SCOPE,
            sort_key=utc_iso(page.last_created_at),
            item_id=page.last_item_id,
        )
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value
    return {
        "contract": "NotificationPageV1",
        "items": page.items,
        "next_cursor": next_cursor,
        "unread_count": page.unread_count,
    }


@router.post(
    "/read-all",
    response_model=NotificationReadAllV1,
    summary="Mark every unread notification of the caller as read",
)
def mark_all_notifications_read(
    request: Request,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: NotificationInboxService = Depends(get_notification_service),
) -> dict[str, Any]:
    # The declaration above publishes the header as required; parse_idempotency_key (C-D5, 1-128
    # visible ASCII) is the authority.
    del idempotency_key
    key = parse_idempotency_key(request)
    try:
        return service.mark_all_read(principal=principal, idempotency_key=key)
    except NotificationError as exc:
        _raise(exc)


@router.post(
    "/{inbox_item_id}/read",
    response_model=NotificationV1,
    summary="Mark one notification of the caller as read",
)
def mark_notification_read(
    inbox_item_id: InboxItemId,
    request: Request,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: NotificationInboxService = Depends(get_notification_service),
) -> dict[str, Any]:
    del idempotency_key
    key = parse_idempotency_key(request)
    try:
        return service.mark_read(
            principal=principal, inbox_item_id=inbox_item_id, idempotency_key=key
        )
    except NotificationError as exc:
        _raise(exc)


@router.post(
    "/push-endpoints",
    response_model=PushEndpointV1,
    status_code=201,
    responses={
        201: {
            "headers": {
                "ETag": {"description": "Strong endpoint version", "schema": {"type": "string"}},
                "Cache-Control": {"schema": {"type": "string"}},
            }
        }
    },
    summary="Register the caller's verified web push endpoint",
)
def register_push_endpoint(
    payload: PushEndpointRegistrationV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: PushEndpointCommandService = Depends(get_push_endpoint_service),
) -> dict[str, object]:
    # Authorize before parsing unsupported-platform or key details; the service rechecks scope
    # inside the command transaction before reading or writing a receipt.
    try:
        service.authorize_parent(principal)
        del idempotency_key
        key = parse_idempotency_key(request)
        result = service.register(
            principal=principal,
            command=PushEndpointRegistration(
                contract=payload.contract,
                platform_kind=payload.platform_kind,
                provider_kind=payload.provider_kind,
                encrypted_registration_proof=payload.encrypted_registration_proof,
                app_version=payload.app_version,
            ),
            idempotency_key=key,
        )
    except PushEndpointError as exc:
        _raise_push(exc)
    except PushEndpointStoreUnavailable:
        raise HTTPException(
            status_code=503, detail={"code": "DEPENDENCY_UNAVAILABLE"}
        ) from None
    response.headers["ETag"] = f'"{result.version}"'
    response.headers["Cache-Control"] = "no-store"
    return {
        "contract": "PushEndpointV1",
        "endpoint_id": UUID(result.endpoint_id),
        "version": result.version,
    }


@router.delete(
    "/push-endpoints/{endpoint_id}",
    status_code=204,
    response_model=None,
    responses={
        204: {
            "headers": {"Cache-Control": {"schema": {"type": "string"}}}
        }
    },
    summary="Revoke the caller's push endpoint at the expected version",
)
def revoke_push_endpoint(
    request: Request,
    endpoint_id: EndpointId,
    idempotency_key: IdempotencyKeyHeader,
    if_match: Annotated[
        str,
        Header(alias="If-Match", description='Strong ETag in the form "<positive-version>".'),
    ],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: PushEndpointCommandService = Depends(get_push_endpoint_service),
) -> Response:
    try:
        service.authorize_parent(principal)
        if request.headers.get("content-length", "0").strip() not in {"", "0"}:
            raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST"}) from None
        del idempotency_key
        key = parse_idempotency_key(request)
        expected_version = _strong_if_match(if_match, request)
        service.revoke(
            principal=principal,
            endpoint_id=endpoint_id,
            expected_version=expected_version,
            idempotency_key=key,
        )
    except PushEndpointError as exc:
        _raise_push(exc)
    except PushEndpointStoreUnavailable:
        raise HTTPException(
            status_code=503, detail={"code": "DEPENDENCY_UNAVAILABLE"}
        ) from None
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
