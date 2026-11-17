"""Owned exact-row delivery lock/ack, without migrations or foreign SQL access."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import Connection, Engine, select, update
from sqlalchemy.exc import DBAPIError

from sketch2life.application.content_consumer_queries import notice_from_outbox
from sketch2life.application.ports.content_consumers import ContentDeliveryTransaction
from sketch2life.contracts.schemas.content_consumers import ContentLifecycleNoticeV1
from sketch2life.domain.learning_content.model import ContentError
from sketch2life.infrastructure.learning_content.tables import OUTBOX


class _SqlDeliveryTransaction:
    def __init__(self, connection: Connection, organization_id: str, event_id: str,
                 notice: ContentLifecycleNoticeV1 | None) -> None:
        self.connection = connection
        self.organization_id = organization_id
        self.event_id = event_id
        self.notice = notice

    def mark_delivered(self, at: datetime) -> None:
        if self.notice is None or at.utcoffset() is None:
            raise ContentError("CONTENT_INVALID_DELIVERY_STATE")
        result = self.connection.execute(update(OUTBOX).where(
            OUTBOX.c.organization_id == self.organization_id,
            OUTBOX.c.event_id == self.event_id, OUTBOX.c.delivered_at.is_(None),
        ).values(delivered_at=at))
        if result.rowcount != 1:
            raise ContentError("CONTENT_DELIVERY_CONFLICT")
        self.notice = None


class SqlContentDeliveryStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @contextmanager
    def delivery(self, organization_id: str,
                 event_id: str) -> Iterator[ContentDeliveryTransaction]:
        try:
            with self.engine.begin() as connection:
                row = connection.execute(select(OUTBOX).where(
                    OUTBOX.c.organization_id == organization_id,
                    OUTBOX.c.event_id == event_id,
                ).with_for_update(nowait=True)).mappings().one_or_none()
                if row is None:
                    raise ContentError("CONTENT_NOTICE_NOT_FOUND")
                notice = None if row["delivered_at"] is not None else notice_from_outbox(
                    event_id, organization_id, json.dumps(row["payload"], allow_nan=False))
                yield _SqlDeliveryTransaction(connection, organization_id, event_id, notice)
        except DBAPIError as error:
            code = getattr(error.orig, "sqlstate", None)
            if code == "55P03":
                raise ContentError("CONTENT_DELIVERY_BUSY") from None
            raise ContentError("CONTENT_DELIVERY_STORAGE_UNAVAILABLE") from None
