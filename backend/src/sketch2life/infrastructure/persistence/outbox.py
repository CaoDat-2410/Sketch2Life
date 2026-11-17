"""Leased outbox delivery with an atomic local consumer receipt boundary."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import and_, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.core_foundation import (
    OutboxDeliveryStatus,
    OutboxEnvelope,
    OutboxState,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreOutboxConsumerReceiptModel,
    CoreOutboxEventModel,
)

LocalOutboxEffect = Callable[[Session, OutboxEnvelope], None]


class PostgresOutbox:
    """Claim outbox rows and process local effects exactly once per consumer key."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def claim_ready(
        self, *, worker_id: str, limit: int = 50, lease_seconds: int = 30
    ) -> Sequence[OutboxEnvelope]:
        if not 1 <= limit <= 500 or not 1 <= lease_seconds <= 3600:
            raise ValueError("outbox claim limits are outside the allowed bounds")
        now = datetime.now(UTC)
        lease_until = now + timedelta(seconds=lease_seconds)
        with self._sessions.begin() as session:
            rows = list(
                session.scalars(
                    select(CoreOutboxEventModel)
                    .where(
                        or_(
                            and_(
                                CoreOutboxEventModel.status == "pending",
                                CoreOutboxEventModel.available_at <= now,
                            ),
                            and_(
                                CoreOutboxEventModel.status == "leased",
                                CoreOutboxEventModel.lease_until <= now,
                            ),
                        )
                    )
                    .order_by(CoreOutboxEventModel.created_at, CoreOutboxEventModel.event_id)
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
            )
            envelopes = []
            for row in rows:
                row.status = "leased"
                row.lease_owner = worker_id
                row.lease_until = lease_until
                row.attempt_count += 1
                envelopes.append(self._envelope(row))
            return tuple(envelopes)

    def get_state(self, *, organization_id: str, event_id: str) -> OutboxState | None:
        with self._sessions() as session:
            row = session.scalar(
                select(CoreOutboxEventModel).where(
                    CoreOutboxEventModel.organization_id == organization_id,
                    CoreOutboxEventModel.event_id == event_id,
                )
            )
            if row is None:
                return None
            return OutboxState(
                event_id=row.event_id,
                event_type=row.event_type,
                organization_id=row.organization_id,
                aggregate_id=row.aggregate_id,
                aggregate_revision=row.aggregate_revision,
                status=OutboxDeliveryStatus(row.status),
                attempt_count=row.attempt_count,
                available_at=row.available_at,
                lease_until=row.lease_until,
                delivered_at=row.delivered_at,
            )

    def defer(
        self,
        *,
        event_id: str,
        worker_id: str,
        retry_after_seconds: int,
    ) -> bool:
        if not 1 <= retry_after_seconds <= 86_400:
            raise ValueError("outbox retry delay is outside the allowed bounds")
        now = datetime.now(UTC)
        with self._sessions.begin() as session:
            result = cast(
                CursorResult[Any],
                session.execute(
                    update(CoreOutboxEventModel)
                    .where(
                        CoreOutboxEventModel.event_id == event_id,
                        CoreOutboxEventModel.status == "leased",
                        CoreOutboxEventModel.lease_owner == worker_id,
                    )
                    .values(
                        status="pending",
                        available_at=now + timedelta(seconds=retry_after_seconds),
                        lease_owner=None,
                        lease_until=None,
                    )
                ),
            )
            return result.rowcount == 1

    def process_local_once(
        self,
        *,
        event_id: str,
        worker_id: str,
        consumer_name: str,
        effect: LocalOutboxEffect,
    ) -> bool:
        """Commit a local consumer effect and its receipt in one DB transaction.

        The callback must only write through the supplied session. It must not call a
        remote service because a remote effect cannot join this database transaction.
        """

        with self._sessions.begin() as session:
            row = session.scalar(
                select(CoreOutboxEventModel)
                .where(CoreOutboxEventModel.event_id == event_id)
                .with_for_update()
            )
            if row is None:
                return False
            if row.status == "delivered":
                return False
            if row.status != "leased" or row.lease_owner != worker_id:
                return False

            receipt_key = (consumer_name, event_id)
            if session.get(CoreOutboxConsumerReceiptModel, receipt_key) is not None:
                self._mark_delivered(row)
                return False

            envelope = self._envelope(row)
            session.add(
                CoreOutboxConsumerReceiptModel(
                    consumer_name=consumer_name,
                    event_id=event_id,
                )
            )
            effect(session, envelope)
            self._mark_delivered(row)
            session.flush()
            return True

    @staticmethod
    def _mark_delivered(row: CoreOutboxEventModel) -> None:
        row.status = "delivered"
        row.delivered_at = datetime.now(UTC)
        row.lease_owner = None
        row.lease_until = None

    @staticmethod
    def _envelope(row: CoreOutboxEventModel) -> OutboxEnvelope:
        return OutboxEnvelope(
            event_id=row.event_id,
            event_type=row.event_type,
            organization_id=row.organization_id,
            aggregate_id=row.aggregate_id,
            aggregate_revision=row.aggregate_revision,
        )


__all__ = ["LocalOutboxEffect", "PostgresOutbox"]
