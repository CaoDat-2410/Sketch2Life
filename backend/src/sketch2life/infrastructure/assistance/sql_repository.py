"""PostgreSQL persistence for the selected FEAT-064 assistance pilot methods."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import cast

from sqlalchemy import Connection, Engine, func, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.assistance import (
    AssistanceEvent,
    AssistanceRevisionConflict,
    AssistanceUniqueConflict,
    CommandReceipt,
    ReceiptKey,
    SketchIntent,
)
from sketch2life.domain.assistance import (
    AssistanceRequest,
    CacheHit,
    RequestStatus,
    ReservationState,
)
from sketch2life.infrastructure.vision_analysis import tables
from sketch2life.infrastructure.vision_analysis.codec import from_payload, to_payload


def _require_org(actual: str, expected: str) -> None:
    if not actual or actual != expected:
        raise ValueError("organization scope mismatch")


def _request_values(request: AssistanceRequest) -> dict[str, object]:
    return {
        "organization_id": request.facts.organization_id,
        "assistance_id": request.assistance_id,
        "record_version": request.record_version,
        "semantic_identity": request.semantic_identity,
        "operation_target": request.operation_target,
        "debounce_key": request.debounce_key,
        "session_id": request.facts.session_id,
        "target_key": request.facts.target.key(),
        "status": request.status.value,
        "reservation": request.reservation.value if request.reservation else None,
        "counts_for_debounce": request.counts_for_debounce,
        "created_at": request.created_at,
        "payload": to_payload(request),
    }


class SqlAssistanceUnitOfWork:
    """Organization-bound unit of work; unsupported cache/sketch writes fail closed."""

    def __init__(self, connection: Connection, organization_id: str) -> None:
        self._connection = connection
        self._organization_id = organization_id
        self._dirty = False

    def _check_org(self, organization_id: str) -> None:
        _require_org(organization_id, self._organization_id)

    def get(self, assistance_id: str) -> AssistanceRequest | None:
        payload = self._connection.execute(
            select(tables.requests.c.payload).where(
                tables.requests.c.organization_id == self._organization_id,
                tables.requests.c.assistance_id == assistance_id,
            )
        ).scalar_one_or_none()
        return None if payload is None else from_payload(payload, AssistanceRequest)

    def insert(self, request: AssistanceRequest) -> None:
        self._check_org(request.facts.organization_id)
        try:
            self._connection.execute(insert(tables.requests).values(**_request_values(request)))
        except IntegrityError as exc:
            raise AssistanceUniqueConflict("assistance request identity already exists") from exc
        self._dirty = True

    def cas(self, *, expected_record_version: int, request: AssistanceRequest) -> None:
        self._check_org(request.facts.organization_id)
        if request.record_version != expected_record_version + 1:
            raise AssistanceRevisionConflict("record version must advance by one")
        result = self._connection.execute(
            update(tables.requests)
            .where(
                tables.requests.c.organization_id == self._organization_id,
                tables.requests.c.assistance_id == request.assistance_id,
                tables.requests.c.record_version == expected_record_version,
            )
            .values(**_request_values(request))
        )
        if result.rowcount != 1:
            raise AssistanceRevisionConflict("assistance request revision changed")
        self._dirty = True

    def find_active_semantic(self, organization_id: str, identity: str) -> str | None:
        self._check_org(organization_id)
        return self._connection.execute(
            select(tables.requests.c.assistance_id).where(
                tables.requests.c.organization_id == self._organization_id,
                tables.requests.c.semantic_identity == identity,
                tables.requests.c.status.in_(
                    (RequestStatus.SCHEDULING.value, RequestStatus.SCHEDULED.value)
                ),
            )
        ).scalar_one_or_none()

    def active_by_operation_target(
        self, organization_id: str, key: str
    ) -> tuple[AssistanceRequest, ...]:
        self._check_org(organization_id)
        payloads = self._connection.execute(
            select(tables.requests.c.payload)
            .where(
                tables.requests.c.organization_id == self._organization_id,
                tables.requests.c.operation_target == key,
                tables.requests.c.status.in_(
                    (RequestStatus.SCHEDULING.value, RequestStatus.SCHEDULED.value)
                ),
            )
            .order_by(tables.requests.c.created_at, tables.requests.c.assistance_id)
        ).scalars()
        return tuple(from_payload(payload, AssistanceRequest) for payload in payloads)

    def latest_counted(self, organization_id: str, debounce_key: str) -> datetime | None:
        self._check_org(organization_id)
        result = self._connection.execute(
            select(func.max(tables.requests.c.created_at)).where(
                tables.requests.c.organization_id == self._organization_id,
                tables.requests.c.debounce_key == debounce_key,
                tables.requests.c.counts_for_debounce.is_(True),
            )
        ).scalar_one()
        return cast(datetime | None, result)

    def count_reserved(self, organization_id: str, session_id: str, target_key: str | None) -> int:
        self._check_org(organization_id)
        predicates = [
            tables.requests.c.organization_id == self._organization_id,
            tables.requests.c.session_id == session_id,
            tables.requests.c.reservation == ReservationState.HELD.value,
        ]
        if target_key is not None:
            predicates.append(tables.requests.c.target_key == target_key)
        return int(
            self._connection.execute(
                select(func.count()).select_from(tables.requests).where(*predicates)
            ).scalar_one()
        )

    def get_receipt(self, key: ReceiptKey) -> CommandReceipt | None:
        self._check_org(key.organization_id)
        payload = self._connection.execute(
            select(tables.receipts.c.payload).where(
                tables.receipts.c.organization_id == self._organization_id,
                tables.receipts.c.principal_id == key.principal_id,
                tables.receipts.c.contract_name == key.contract_name,
                tables.receipts.c.target_id == key.target_id,
                tables.receipts.c.idempotency_key == key.idempotency_key,
            )
        ).scalar_one_or_none()
        return None if payload is None else from_payload(payload, CommandReceipt)

    def put_receipt(self, receipt: CommandReceipt) -> None:
        key = receipt.key
        self._check_org(key.organization_id)
        self._check_org(receipt.snapshot.facts.organization_id)
        values = {
            "organization_id": self._organization_id,
            "principal_id": key.principal_id,
            "contract_name": key.contract_name,
            "target_id": key.target_id,
            "idempotency_key": key.idempotency_key,
            "assistance_id": receipt.snapshot.assistance_id,
            "payload": to_payload(receipt),
        }
        try:
            result = self._connection.execute(
                pg_insert(tables.receipts).values(**values).on_conflict_do_nothing()
            )
        except IntegrityError as exc:
            raise AssistanceUniqueConflict("receipt conflicts with its request") from exc
        if result.rowcount == 1:
            self._dirty = True
            return
        existing = self.get_receipt(key)
        if existing != receipt:
            raise AssistanceUniqueConflict("receipt key is already bound to another command")

    def find_cache(self, organization_id: str, identity: str) -> CacheHit | None:
        self._check_org(organization_id)
        raise NotImplementedError("cache is outside this pilot")

    def put_cache(self, organization_id: str, identity: str, hit: CacheHit) -> None:
        self._check_org(organization_id)
        raise NotImplementedError("cache is outside this pilot")

    def add_event(self, event: AssistanceEvent) -> None:
        self._check_org(event.organization_id)
        try:
            self._connection.execute(
                insert(tables.events).values(
                    organization_id=self._organization_id,
                    event_id=event.event_id,
                    assistance_id=event.assistance_id,
                    payload=to_payload(event),
                )
            )
        except IntegrityError as exc:
            raise AssistanceUniqueConflict("assistance event already exists") from exc
        self._dirty = True

    def add_sketch_intent(self, intent: SketchIntent) -> None:
        raise NotImplementedError("sketch generation is outside this pilot")

    def notice_seen(self, notice_id: str) -> bool:
        return (
            self._connection.execute(
                select(tables.notices.c.notice_id).where(
                    tables.notices.c.organization_id == self._organization_id,
                    tables.notices.c.notice_id == notice_id,
                )
            ).scalar_one_or_none()
            is not None
        )

    def record_notice(self, notice_id: str) -> None:
        result = self._connection.execute(
            pg_insert(tables.notices)
            .values(organization_id=self._organization_id, notice_id=notice_id)
            .on_conflict_do_nothing()
        )
        self._dirty = self._dirty or result.rowcount == 1

    def list_requests(self, organization_id: str) -> tuple[AssistanceRequest, ...]:
        self._check_org(organization_id)
        payloads = self._connection.execute(
            select(tables.requests.c.payload)
            .where(tables.requests.c.organization_id == self._organization_id)
            .order_by(tables.requests.c.created_at, tables.requests.c.assistance_id)
        ).scalars()
        return tuple(from_payload(payload, AssistanceRequest) for payload in payloads)

    def publish_request_fence(self, organization_id: str) -> None:
        self._check_org(organization_id)
        self._dirty = True

    def decision_epoch(self, organization_id: str) -> tuple[int, int]:
        self._check_org(organization_id)
        row = self._connection.execute(
            select(tables.epochs.c.request_epoch, tables.epochs.c.analysis_epoch).where(
                tables.epochs.c.organization_id == self._organization_id
            )
        ).one_or_none()
        return (0, 0) if row is None else (int(row[0]), int(row[1]))


class SqlAssistanceRepository:
    def __init__(self, engine: Engine, organization_id: str) -> None:
        if not organization_id:
            raise ValueError("organization scope is required")
        self._engine = engine
        self._organization_id = organization_id

    @contextmanager
    def transaction(self) -> Iterator[SqlAssistanceUnitOfWork]:
        with self._engine.begin() as connection:
            if connection.dialect.name != "postgresql":
                raise RuntimeError("PostgreSQL is required for pilot persistence")
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
                {"scope": "feat064-pilot:" + self._organization_id},
            )
            unit = SqlAssistanceUnitOfWork(connection, self._organization_id)
            yield unit
            if unit._dirty:
                epoch_insert = pg_insert(tables.epochs).values(
                    organization_id=self._organization_id,
                    request_epoch=1,
                    analysis_epoch=0,
                )
                connection.execute(
                    epoch_insert.on_conflict_do_update(
                        index_elements=[tables.epochs.c.organization_id],
                        set_={"request_epoch": tables.epochs.c.request_epoch + 1},
                    )
                )


__all__ = ["SqlAssistanceRepository", "SqlAssistanceUnitOfWork"]
