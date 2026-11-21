"""PostgreSQL inbox: the producer adapter and the recipient's reads and mark-read commands.

FEAT-066 goal v3, T-8a (SRS l.784, l.812, l.1681, l.1697; FR-B-09; UC-15). Two entry points share
the one table ``notifications.inbox_items``:

* ``SqlNotificationProducer`` is the only writer. It joins the caller's transaction (never
  commits), takes ``created_at`` from the injected clock, validates the command with the allowlist
  of ``application.services.notifications`` and inserts with ``ON CONFLICT DO NOTHING`` on the
  ``(recipient, dedupe key)`` constraint. A conflict with the same command hash returns the stored
  item; another hash raises ``NotificationDedupeConflict``.
* ``NotificationInboxService`` serves the recipient. Every query filters on the caller's own
  ``account_id`` taken from the verified identity row, so there is no way to name another
  recipient. No identity row, an inactive or foreign-issuer identity, an identity without one of
  the four roles, another user's item and an unknown item are the same 404. The two mark-read
  commands keep a receipt in ``be1_command_receipts`` (SRS l.1697) written in the same
  transaction as the effect; the effect is monotone SQL (``read_at`` is set once, never moved).

Nothing is delivered from here: no e-mail, no push, no provider call, no worker.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, func, literal, or_, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.notifications import (
    EnqueueResult,
    NotificationCommandV1,
    NotificationDedupeConflict,
)
from sketch2life.application.services.notifications import (
    READ_ALL_SCOPE,
    READ_ONE_SCOPE,
    RECIPIENT_ROLES,
    UNREAD_COUNT_CAP,
    command_sha256,
    read_fingerprint,
    validate_command,
)
from sketch2life.infrastructure.notifications.tables import INBOX_ITEMS
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
)

Clock = Callable[[], datetime]
_ITEM_ID_MAX = 36


def utc_now() -> datetime:
    return datetime.now(UTC)


class NotificationError(Exception):
    """A refusal with its HTTP status and public code; the router maps it to the CONV-1 body."""

    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


def not_found() -> NotificationError:
    return NotificationError(404, "RESOURCE_NOT_FOUND")


class SqlNotificationProducer:
    """``NotificationProducerPort`` on the inbox table; joins the caller's transaction."""

    def __init__(self, session: Session, clock: Clock = utc_now) -> None:
        self._session = session
        self._clock = clock

    def enqueue(self, command: NotificationCommandV1) -> EnqueueResult:
        created_at = self._clock()
        validate_command(command, created_at=created_at)
        digest = command_sha256(command)
        statement = (
            pg_insert(INBOX_ITEMS)
            .values(
                inbox_item_id=str(uuid4()),
                recipient_account_id=command.recipient_account_id,
                recipient_role=command.recipient_role,
                organization_ref=command.organization_ref,
                notification_type=command.notification_type,
                template_version=command.template_version,
                trigger_id=command.trigger_id,
                trigger_dedupe_key=command.dedupe_key,
                command_sha256=digest,
                safe_parameters=dict(command.safe_parameters),
                created_at=created_at,
                expires_at=command.expires_at,
            )
            .on_conflict_do_nothing(index_elements=["recipient_account_id", "trigger_dedupe_key"])
            .returning(INBOX_ITEMS.c.inbox_item_id)
        )
        inserted = self._session.execute(statement).scalar_one_or_none()
        if inserted is not None:
            return EnqueueResult(inbox_item_id=str(inserted), created=True)
        existing = (
            self._session.execute(
                select(INBOX_ITEMS.c.inbox_item_id, INBOX_ITEMS.c.command_sha256).where(
                    INBOX_ITEMS.c.recipient_account_id == command.recipient_account_id,
                    INBOX_ITEMS.c.trigger_dedupe_key == command.dedupe_key,
                )
            )
            .mappings()
            .one()
        )
        if existing["command_sha256"] != digest:
            raise NotificationDedupeConflict(command.dedupe_key)
        return EnqueueResult(inbox_item_id=str(existing["inbox_item_id"]), created=False)


@dataclass(frozen=True, slots=True)
class Recipient:
    account_id: str
    role: str


@dataclass(frozen=True, slots=True)
class InboxPage:
    """One page of the caller's items plus the keyset of the last item and the unread badge."""

    items: list[dict[str, Any]]
    has_more: bool
    unread_count: int
    last_created_at: datetime | None
    last_item_id: str | None


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def item_body(row: RowMapping) -> dict[str, Any]:
    """The ``NotificationV1`` body: no recipient, role, organization, trigger, key or hash."""
    return {
        "contract": "NotificationV1",
        "inbox_item_id": row["inbox_item_id"],
        "notification_type": row["notification_type"],
        "template_version": row["template_version"],
        "safe_parameters": dict(row["safe_parameters"]),
        "created_at": row["created_at"],
        "read_at": row["read_at"],
        "expires_at": row["expires_at"],
    }


_ITEM_COLUMNS = (
    INBOX_ITEMS.c.inbox_item_id,
    INBOX_ITEMS.c.notification_type,
    INBOX_ITEMS.c.template_version,
    INBOX_ITEMS.c.safe_parameters,
    INBOX_ITEMS.c.created_at,
    INBOX_ITEMS.c.read_at,
    INBOX_ITEMS.c.expires_at,
)


class NotificationInboxService:
    """Recipient-only reads and mark-read commands (SRS l.812, l.1681, l.1697)."""

    def __init__(self, db: Session, clock: Clock = utc_now) -> None:
        self.db = db
        self._clock = clock

    # ------------------------------------------------------------------ identity
    def _recipient(self, principal: VerifiedPrincipal) -> Recipient:
        """The caller's own account, or the uniform 404 (no identity, inactive, other issuer)."""
        if not principal.subject or not principal.issuer:
            raise not_found()
        identity = self.db.get(AdultIdentityModel, principal.subject)
        if (
            identity is None
            or identity.state != "active"
            or identity.issuer != principal.issuer
            or identity.account_role not in RECIPIENT_ROLES
        ):
            raise not_found()
        return Recipient(account_id=identity.account_id, role=str(identity.account_role))

    @staticmethod
    def _visible(recipient: Recipient, now: datetime) -> Any:
        return and_(
            INBOX_ITEMS.c.recipient_account_id == recipient.account_id,
            or_(INBOX_ITEMS.c.expires_at.is_(None), INBOX_ITEMS.c.expires_at > now),
        )

    # ------------------------------------------------------------------ list
    def list_page(
        self,
        *,
        principal: VerifiedPrincipal,
        limit: int,
        after: tuple[datetime, str] | None,
    ) -> InboxPage:
        """The caller's unexpired items, newest first, keyset ``(created_at, inbox_item_id)``."""
        recipient = self._recipient(principal)
        now = self._clock()
        visible = self._visible(recipient, now)
        statement = select(*_ITEM_COLUMNS).where(visible)
        if after is not None:
            statement = statement.where(
                tuple_(INBOX_ITEMS.c.created_at, INBOX_ITEMS.c.inbox_item_id)
                < tuple_(literal(after[0]), literal(after[1]))
            )
        rows = (
            self.db.execute(
                statement.order_by(
                    INBOX_ITEMS.c.created_at.desc(), INBOX_ITEMS.c.inbox_item_id.desc()
                ).limit(limit + 1)
            )
            .mappings()
            .all()
        )
        has_more = len(rows) > limit
        page_rows = rows[:limit]
        unread = self.db.scalar(
            select(func.count()).select_from(
                select(literal(1))
                .select_from(INBOX_ITEMS)
                .where(visible, INBOX_ITEMS.c.read_at.is_(None))
                .limit(UNREAD_COUNT_CAP)
                .subquery()
            )
        )
        last = page_rows[-1] if page_rows else None
        return InboxPage(
            items=[item_body(row) for row in page_rows],
            has_more=has_more,
            unread_count=int(unread or 0),
            last_created_at=last["created_at"] if last is not None else None,
            last_item_id=last["inbox_item_id"] if last is not None else None,
        )

    # ------------------------------------------------------------------ receipts
    def _receipt(
        self, principal: VerifiedPrincipal, scope: str, key: str
    ) -> Be1CommandReceiptModel | None:
        return self.db.get(Be1CommandReceiptModel, (principal.subject, scope, key))

    @staticmethod
    def _replay(receipt: Be1CommandReceiptModel, fingerprint: str) -> dict[str, Any]:
        if receipt.request_fingerprint != fingerprint:
            raise NotificationError(400, "INVALID_IDEMPOTENCY_KEY")
        return dict(receipt.response_json)

    def _store(
        self,
        principal: VerifiedPrincipal,
        scope: str,
        key: str,
        fingerprint: str,
        body: dict[str, Any],
    ) -> None:
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=scope,
                idempotency_key=key,
                organization_id=None,
                request_fingerprint=fingerprint,
                response_json=_json_safe(body),
            )
        )

    def _commit_with_receipt(
        self, principal: VerifiedPrincipal, scope: str, key: str, fingerprint: str
    ) -> dict[str, Any] | None:
        """Commit; when a concurrent first use of the same key won, return its stored body."""
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            receipt = self._receipt(principal, scope, key)
            if receipt is None:
                raise
            return self._replay(receipt, fingerprint)
        return None

    # ------------------------------------------------------------------ mark read
    def mark_read(
        self, *, principal: VerifiedPrincipal, inbox_item_id: str, idempotency_key: str
    ) -> dict[str, Any]:
        """Mark one item read (200 with the item); the first ``read_at`` is never moved."""
        recipient = self._recipient(principal)
        fingerprint = read_fingerprint("read", inbox_item_id)
        receipt = self._receipt(principal, READ_ONE_SCOPE, idempotency_key)
        if receipt is not None:
            replayed = self._replay(receipt, fingerprint)
            self.db.rollback()
            return replayed
        if not 0 < len(inbox_item_id) <= _ITEM_ID_MAX:
            raise not_found()
        now = self._clock()
        visible = and_(self._visible(recipient, now), INBOX_ITEMS.c.inbox_item_id == inbox_item_id)
        exists = self.db.execute(select(INBOX_ITEMS.c.inbox_item_id).where(visible)).first()
        if exists is None:
            raise not_found()
        self.db.execute(
            update(INBOX_ITEMS)
            .where(visible, INBOX_ITEMS.c.read_at.is_(None))
            .values(read_at=func.greatest(literal(now), INBOX_ITEMS.c.created_at))
        )
        row = self.db.execute(select(*_ITEM_COLUMNS).where(visible)).mappings().one()
        body = _json_safe(item_body(row))
        self._store(principal, READ_ONE_SCOPE, idempotency_key, fingerprint, body)
        replayed_body = self._commit_with_receipt(
            principal, READ_ONE_SCOPE, idempotency_key, fingerprint
        )
        return replayed_body if replayed_body is not None else body

    def mark_all_read(
        self, *, principal: VerifiedPrincipal, idempotency_key: str
    ) -> dict[str, Any]:
        """Mark every unread, unexpired item of the caller read; the count is stored for replay."""
        recipient = self._recipient(principal)
        fingerprint = read_fingerprint("read-all", None)
        receipt = self._receipt(principal, READ_ALL_SCOPE, idempotency_key)
        if receipt is not None:
            replayed = self._replay(receipt, fingerprint)
            self.db.rollback()
            return replayed
        now = self._clock()
        marked = self.db.execute(
            update(INBOX_ITEMS)
            .where(self._visible(recipient, now), INBOX_ITEMS.c.read_at.is_(None))
            .values(read_at=func.greatest(literal(now), INBOX_ITEMS.c.created_at))
            .returning(INBOX_ITEMS.c.inbox_item_id)
        ).all()
        body: dict[str, Any] = {"contract": "NotificationReadAllV1", "marked_count": len(marked)}
        self._store(principal, READ_ALL_SCOPE, idempotency_key, fingerprint, body)
        replayed_body = self._commit_with_receipt(
            principal, READ_ALL_SCOPE, idempotency_key, fingerprint
        )
        return replayed_body if replayed_body is not None else body


__all__ = [
    "InboxPage",
    "NotificationError",
    "NotificationInboxService",
    "Recipient",
    "SqlNotificationProducer",
    "item_body",
    "not_found",
    "utc_now",
]
