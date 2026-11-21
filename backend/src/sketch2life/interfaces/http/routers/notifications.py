"""Notification inbox routes (FEAT-066 goal v3, T-8a; SRS l.812, l.1681, l.1697; FR-B-09; UC-15).

Literal paths under ``/v1/notifications``. The inbox is the source of truth; nothing here sends
an e-mail or a push, and the push-endpoint routes (SRS l.1682-1683) are T-8b, deferred: they are
not registered, so the framework answers 404. Every route is open to any active adult with a role
and acts on the caller's own inbox only; another user's item, an unknown item and a caller without
an identity row are the same 404 (SRS l.864-865). The two mark-read commands are keyed
(``Idempotency-Key``, SRS l.1697) and answer 200; the page read answers 25 items by default and at
most 100 with an opaque keyset cursor.

Notes (T-8a implementation review): ``unread_count`` is a second statement without a shared
snapshot, so a concurrent insert may count an item the page does not hold (a badge only); a replayed
mark-read returns the first stored result even when the item has since expired (SRS l.1697); an item
id longer than 64 characters is a 400, one of 37-64 valid characters is a 404.
"""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, Response
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.notifications import utc_iso
from sketch2life.contracts.schemas.notifications import (
    NotificationPageV1,
    NotificationReadAllV1,
    NotificationV1,
)
from sketch2life.infrastructure.notifications.inbox_repository import (
    NotificationError,
    NotificationInboxService,
)
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

router = APIRouter(prefix=NOTIFICATIONS_BASE, tags=["Notifications"])

IdempotencyKeyHeader = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]
# A NUL byte can never be part of an id and PostgreSQL text cannot hold it: refuse it as a 400
# before any query instead of a retryable 503.
InboxItemId = Annotated[str, Path(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")]
_READ_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Authorization"}


def get_notification_service(db: Session = Depends(get_db)) -> NotificationInboxService:
    return NotificationInboxService(db)


def _raise(exc: NotificationError) -> NoReturn:
    raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None


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
