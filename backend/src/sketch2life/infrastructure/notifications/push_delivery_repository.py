"""Transactional PostgreSQL store for durable, content-free push delivery attempts (T-NTF1)."""

from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import CursorResult, exists, literal, or_, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from sketch2life.application.ports.push_delivery import (
    PushDeliveryClaim,
    PushDeliveryClaimResult,
    PushDeliveryRecordResult,
    PushSendOutcome,
    PushSendResult,
    TemplateKey,
)
from sketch2life.application.ports.push_endpoints import ConcurrentPushEndpointWrite
from sketch2life.domain.push_delivery import (
    CLAIM_LEASE,
    MAX_ATTEMPTS,
    PushDeliveryErrorCode,
    PushDeliveryStatus,
    retry_delay,
)
from sketch2life.domain.push_endpoints import PushEndpointState, revoke_endpoint
from sketch2life.domain.story_run_reminder import require_aware_utc
from sketch2life.infrastructure.notifications.push_endpoint_repository import (
    SqlPushEndpointStore,
)
from sketch2life.infrastructure.notifications.tables import (
    INBOX_ITEMS,
    PUSH_DELIVERIES,
    PUSH_ENDPOINTS,
)


def _eligible_clause(table: Any, eligible_templates: frozenset[TemplateKey]) -> Any:
    if not eligible_templates:
        return literal(False)
    return tuple_(table.c.notification_type, table.c.template_version).in_(
        tuple(sorted(eligible_templates))
    )


class SqlPushDeliveryStore:
    """Implements the delivery store port; every claim and result is a short transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def enroll(
        self,
        *,
        now: datetime,
        limit: int,
        eligible_templates: frozenset[TemplateKey],
        window: timedelta,
    ) -> int:
        instant = require_aware_utc(now, field="now")
        if type(limit) is not int or limit < 1:
            raise ValueError("limit must be positive")
        if not eligible_templates:
            self._session.rollback()
            return 0

        item = INBOX_ITEMS.alias("enroll_item")
        endpoint = PUSH_ENDPOINTS.alias("enroll_endpoint")
        existing = PUSH_DELIVERIES.alias("existing_delivery")
        not_enrolled = ~exists(
            select(literal(1))
            .select_from(existing)
            .where(
                existing.c.inbox_item_id == item.c.inbox_item_id,
                existing.c.push_endpoint_id == endpoint.c.push_endpoint_id,
            )
        )
        statement = (
            select(
                item.c.inbox_item_id.label("inbox_item_id"),
                item.c.recipient_account_id.label("recipient_account_id"),
                item.c.created_at.label("item_created_at"),
                endpoint.c.push_endpoint_id.label("push_endpoint_id"),
            )
            .select_from(
                item.join(endpoint, endpoint.c.recipient_account_id == item.c.recipient_account_id)
            )
            .where(
                endpoint.c.state == PushEndpointState.ACTIVE.value,
                item.c.read_at.is_(None),
                or_(item.c.expires_at.is_(None), item.c.expires_at > instant),
                item.c.created_at >= instant - window,
                item.c.created_at <= instant,
                _eligible_clause(item, eligible_templates),
                not_enrolled,
            )
            .order_by(endpoint.c.push_endpoint_id, item.c.created_at, item.c.inbox_item_id)
            .limit(limit)
        )
        try:
            rows = self._session.execute(statement).mappings().all()
            values = [
                {
                    "delivery_id": str(uuid4()),
                    "inbox_item_id": str(row["inbox_item_id"]),
                    "push_endpoint_id": str(row["push_endpoint_id"]),
                    "recipient_account_id": str(row["recipient_account_id"]),
                    "status": PushDeliveryStatus.PENDING.value,
                    "attempt_count": 0,
                    "next_attempt_at": instant,
                    # Inbox order keeps per-endpoint order inside one batch.
                    "created_at": row["item_created_at"],
                }
                for row in rows
            ]
            if not values:
                self._session.rollback()
                return 0
            inserted = self._session.execute(
                pg_insert(PUSH_DELIVERIES)
                .values(values)
                .on_conflict_do_nothing(index_elements=["inbox_item_id", "push_endpoint_id"])
                .returning(PUSH_DELIVERIES.c.delivery_id)
            ).all()
            self._session.commit()
            return len(inserted)
        except BaseException:
            self._session.rollback()
            raise

    def claim_due(
        self, *, now: datetime, eligible_templates: frozenset[TemplateKey]
    ) -> PushDeliveryClaimResult:
        instant = require_aware_utc(now, field="now")
        delivery = PUSH_DELIVERIES.alias("claim_delivery")
        item = INBOX_ITEMS.alias("claim_item")
        endpoint = PUSH_ENDPOINTS.alias("claim_endpoint")
        earlier = PUSH_DELIVERIES.alias("earlier_pending_delivery")
        has_earlier = exists(
            select(literal(1))
            .select_from(earlier)
            .where(
                earlier.c.push_endpoint_id == delivery.c.push_endpoint_id,
                earlier.c.status == PushDeliveryStatus.PENDING.value,
                tuple_(earlier.c.created_at, earlier.c.inbox_item_id)
                < tuple_(delivery.c.created_at, delivery.c.inbox_item_id),
            )
        )
        statement = (
            select(
                delivery.c.delivery_id.label("delivery_id"),
                delivery.c.inbox_item_id.label("inbox_item_id"),
                delivery.c.push_endpoint_id.label("push_endpoint_id"),
                delivery.c.recipient_account_id.label("recipient_account_id"),
                delivery.c.attempt_count.label("attempt_count"),
                delivery.c.created_at.label("created_at"),
                item.c.read_at.label("read_at"),
                item.c.expires_at.label("expires_at"),
                item.c.recipient_account_id.label("item_recipient_account_id"),
                item.c.notification_type.label("notification_type"),
                item.c.template_version.label("template_version"),
                endpoint.c.recipient_account_id.label("endpoint_recipient_account_id"),
                endpoint.c.state.label("endpoint_state"),
                endpoint.c.endpoint_ciphertext.label("endpoint_ciphertext"),
            )
            .select_from(
                delivery.join(item, item.c.inbox_item_id == delivery.c.inbox_item_id).join(
                    endpoint, endpoint.c.push_endpoint_id == delivery.c.push_endpoint_id
                )
            )
            .where(
                delivery.c.status == PushDeliveryStatus.PENDING.value,
                delivery.c.next_attempt_at <= instant,
                delivery.c.created_at <= instant,
                ~has_earlier,
            )
            .order_by(
                delivery.c.next_attempt_at,
                delivery.c.push_endpoint_id,
                delivery.c.created_at,
                delivery.c.inbox_item_id,
            )
            .with_for_update(of=(delivery, endpoint), skip_locked=True)
            .limit(1)
        )
        try:
            row = self._session.execute(statement).mappings().one_or_none()
            if row is None:
                self._session.rollback()
                return PushDeliveryClaimResult(None)

            delivery_id = str(row["delivery_id"])
            attempt_count = int(row["attempt_count"])
            stale = (
                row["read_at"] is not None
                or (row["expires_at"] is not None and row["expires_at"] <= instant)
                or row["item_recipient_account_id"] != row["recipient_account_id"]
                or row["endpoint_recipient_account_id"] != row["recipient_account_id"]
                or (str(row["notification_type"]), int(row["template_version"]))
                not in eligible_templates
                or row["endpoint_state"] != PushEndpointState.ACTIVE.value
            )
            if stale:
                self._session.execute(
                    update(PUSH_DELIVERIES)
                    .where(
                        PUSH_DELIVERIES.c.delivery_id == delivery_id,
                        PUSH_DELIVERIES.c.status == PushDeliveryStatus.PENDING.value,
                        PUSH_DELIVERIES.c.attempt_count == attempt_count,
                    )
                    .values(
                        status=PushDeliveryStatus.SKIPPED.value,
                        completed_at=instant,
                    )
                )
                self._session.commit()
                return PushDeliveryClaimResult(None, skipped=True)

            if attempt_count >= MAX_ATTEMPTS:
                self._session.execute(
                    update(PUSH_DELIVERIES)
                    .where(
                        PUSH_DELIVERIES.c.delivery_id == delivery_id,
                        PUSH_DELIVERIES.c.status == PushDeliveryStatus.PENDING.value,
                        PUSH_DELIVERIES.c.attempt_count == attempt_count,
                    )
                    .values(
                        status=PushDeliveryStatus.FAILED.value,
                        completed_at=instant,
                    )
                )
                self._session.commit()
                return PushDeliveryClaimResult(None, failed=True)

            next_attempt = attempt_count + 1
            changed = self._session.execute(
                update(PUSH_DELIVERIES)
                .where(
                    PUSH_DELIVERIES.c.delivery_id == delivery_id,
                    PUSH_DELIVERIES.c.status == PushDeliveryStatus.PENDING.value,
                    PUSH_DELIVERIES.c.attempt_count == attempt_count,
                )
                .values(
                    attempt_count=next_attempt,
                    last_attempt_at=instant,
                    next_attempt_at=instant + CLAIM_LEASE,
                )
            )
            if cast("CursorResult[Any]", changed).rowcount != 1:
                self._session.rollback()
                return PushDeliveryClaimResult(None)
            claim = PushDeliveryClaim(
                delivery_id=delivery_id,
                inbox_item_id=str(row["inbox_item_id"]),
                push_endpoint_id=str(row["push_endpoint_id"]),
                recipient_account_id=str(row["recipient_account_id"]),
                endpoint_ciphertext=bytes(row["endpoint_ciphertext"]),
                attempt_count=next_attempt,
                created_at=row["created_at"],
            )
            self._session.commit()
            return PushDeliveryClaimResult(claim)
        except BaseException:
            self._session.rollback()
            raise

    def record_outcome(
        self,
        *,
        claim: PushDeliveryClaim,
        result: PushSendResult,
        now: datetime,
    ) -> PushDeliveryRecordResult:
        instant = require_aware_utc(now, field="now")
        outcome = result.outcome
        if outcome is PushSendOutcome.SENT:
            status = PushDeliveryStatus.SENT
            error_code = None
            completed_at = instant
            next_attempt_at = None
            record_result = PushDeliveryRecordResult.SENT
        elif outcome is PushSendOutcome.ENDPOINT_GONE:
            status = PushDeliveryStatus.DEAD_ENDPOINT
            error_code = PushDeliveryErrorCode.ENDPOINT_GONE.value
            completed_at = instant
            next_attempt_at = None
            record_result = PushDeliveryRecordResult.DEAD_ENDPOINT
        else:
            error_code = PushDeliveryErrorCode(outcome.value).value
            if claim.attempt_count >= MAX_ATTEMPTS:
                status = PushDeliveryStatus.FAILED
                completed_at = instant
                next_attempt_at = None
                record_result = PushDeliveryRecordResult.FAILED
            else:
                status = PushDeliveryStatus.PENDING
                completed_at = None
                next_attempt_at = instant + retry_delay(claim.attempt_count)
                record_result = PushDeliveryRecordResult.RETRY

        values: dict[str, object] = {
            "status": status.value,
            "last_error_code": error_code,
            "completed_at": completed_at,
        }
        if next_attempt_at is not None:
            values["next_attempt_at"] = next_attempt_at
        try:
            changed = self._session.execute(
                update(PUSH_DELIVERIES)
                .where(
                    PUSH_DELIVERIES.c.delivery_id == claim.delivery_id,
                    PUSH_DELIVERIES.c.status == PushDeliveryStatus.PENDING.value,
                    PUSH_DELIVERIES.c.attempt_count == claim.attempt_count,
                )
                .values(**values)
            )
            if cast("CursorResult[Any]", changed).rowcount != 1:
                self._session.rollback()
                return PushDeliveryRecordResult.STALE

            if outcome is PushSendOutcome.ENDPOINT_GONE:
                endpoint_store = SqlPushEndpointStore(self._session)
                endpoint = endpoint_store.find_owned(
                    endpoint_id=claim.push_endpoint_id,
                    recipient_account_id=claim.recipient_account_id,
                    for_update=True,
                )
                if endpoint is not None and endpoint.state is PushEndpointState.ACTIVE:
                    revoked = revoke_endpoint(
                        endpoint,
                        expected_version=endpoint.version,
                        now=instant,
                    )
                    # A lost endpoint CAS does not undo the delivery result.
                    with suppress(ConcurrentPushEndpointWrite):
                        endpoint_store.update_endpoint(revoked)
            self._session.commit()
            return record_result
        except BaseException:
            self._session.rollback()
            raise


__all__ = ["SqlPushDeliveryStore"]
