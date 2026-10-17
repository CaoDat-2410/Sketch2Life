"""Serialized own ledger UoW. This adapter is not a use/quote/evidence authority."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from typing import Any

from sqlalchemy import Connection, Engine, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError, IntegrityError

from sketch2life.application.ports.ai_policy_ledger import (
    LedgerEvent,
    LedgerReceipt,
    ResourceLedgerTransaction,
)
from sketch2life.domain.ai_policy import accounting as domain
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.accounting_tables import (
    BUCKET,
    LEDGER_EVENT,
    LEDGER_RECEIPT,
    RESERVATION,
    RESOURCE_SCOPE,
)


def bucket_id(key: domain.BudgetKey) -> str:
    return hashlib.sha256(
        json.dumps(asdict(key), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _key(value: dict[str, Any]) -> domain.BudgetKey:
    return domain.BudgetKey(**(value | {"definition": domain.DefinitionKey(**value["definition"])}))


def decode_reservation(value: dict[str, Any]) -> domain.Reservation:
    """Validate stored domain invariants; never promote persisted JSON to authority."""
    try:
        raw_terms = value["terms"]
        terms = domain.LimitTerms(
            **(
                raw_terms
                | {
                    "key": _key(raw_terms["key"]),
                    "concurrency_definition": domain.DefinitionKey(
                        **raw_terms["concurrency_definition"]
                    ),
                }
            )
        )
        proof = value["settlement"]
        if proof is not None:
            proof = domain.SettlementProof(
                **(
                    proof
                    | {
                        "key": _key(proof["key"]),
                        "outcome": domain.SettlementOutcome(proof["outcome"]),
                        "evidence_kind": domain.AccountingEvidence(proof["evidence_kind"]),
                    }
                )
            )
        return domain.Reservation(
            **(
                value
                | {
                    "terms": terms,
                    "settlement": proof,
                    "state": domain.ReservationState(value["state"]),
                }
            )
        )
    except (TypeError, ValueError, KeyError, AttributeError):
        raise PolicyError("AI_POLICY_INVALID_LEDGER_STORAGE") from None


def _id(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", value):
        raise PolicyError("AI_POLICY_INVALID_ACCOUNTING_ID")


class SqlResourceLedgerTransaction:
    def __init__(self, connection: Connection, organization_id: str, feature_scope: str) -> None:
        _id(organization_id)
        _id(feature_scope)
        self.connection = connection
        self.organization_id, self.feature_scope = organization_id, feature_scope
        self.scope_filter = (RESOURCE_SCOPE.c.organization_id == organization_id) & (
            RESOURCE_SCOPE.c.feature_scope == feature_scope
        )
        connection.execute(
            pg_insert(RESOURCE_SCOPE)
            .values(
                organization_id=organization_id,
                feature_scope=feature_scope,
                occupied_slots=0,
            )
            .on_conflict_do_nothing()
        )
        connection.execute(select(RESOURCE_SCOPE).where(self.scope_filter).with_for_update()).one()

    def _scope(self, key: domain.BudgetKey) -> None:
        if (key.organization_id, key.feature_scope) != (self.organization_id, self.feature_scope):
            raise PolicyError("AI_POLICY_ACCOUNTING_SCOPE_MISMATCH")

    def snapshot(self, terms: domain.LimitTerms) -> domain.LedgerSnapshot:
        key = terms.key
        self._scope(key)
        self.connection.execute(
            pg_insert(BUCKET)
            .values(
                organization_id=self.organization_id,
                feature_scope=self.feature_scope,
                bucket_id=bucket_id(key),
                key=asdict(key),
                held_units=0,
                spent_units=0,
            )
            .on_conflict_do_nothing()
        )
        row = (
            self.connection.execute(
                select(BUCKET).where(
                    BUCKET.c.organization_id == self.organization_id,
                    BUCKET.c.bucket_id == bucket_id(key),
                )
            )
            .mappings()
            .one()
        )
        if row["key"] != asdict(key) or row["feature_scope"] != self.feature_scope:
            raise PolicyError("AI_POLICY_INVALID_LEDGER_STORAGE")
        slots: int = self.connection.execute(
            select(RESOURCE_SCOPE.c.occupied_slots).where(self.scope_filter)
        ).scalar_one()
        return domain.LedgerSnapshot(key, row["held_units"], row["spent_units"], slots)

    def _reservation(self, **filters: str) -> domain.Reservation | None:
        row = (
            self.connection.execute(
                select(RESERVATION).where(
                    RESERVATION.c.organization_id == self.organization_id,
                    *(RESERVATION.c[name] == value for name, value in filters.items()),
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        value = decode_reservation(row["payload"])
        self._scope(value.terms.key)
        if (
            row["feature_scope"],
            row["bucket_id"],
            row["reservation_id"],
            row["request_digest"],
            row["attempt_id"],
            row["state"],
        ) != (
            self.feature_scope,
            bucket_id(value.terms.key),
            value.reservation_id,
            value.request_digest,
            value.attempt_id,
            value.state.value,
        ):
            raise PolicyError("AI_POLICY_INVALID_LEDGER_STORAGE")
        return value

    def reservation(self, reservation_id: str) -> domain.Reservation | None:
        _id(reservation_id)
        return self._reservation(reservation_id=reservation_id)

    def attempt(self, request_digest: str, attempt_id: str) -> domain.Reservation | None:
        return self._reservation(request_digest=request_digest, attempt_id=attempt_id)

    def receipt(self, principal_id: str, client_request_id: str) -> LedgerReceipt | None:
        row = (
            self.connection.execute(
                select(LEDGER_RECEIPT).where(
                    LEDGER_RECEIPT.c.organization_id == self.organization_id,
                    LEDGER_RECEIPT.c.principal_id == principal_id,
                    LEDGER_RECEIPT.c.client_request_id == client_request_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        if row["feature_scope"] != self.feature_scope:
            raise PolicyError("AI_POLICY_RESOURCE_RECEIPT_CONFLICT")
        return LedgerReceipt(**{name: row[name] for name in LedgerReceipt.__dataclass_fields__})

    def add_receipt(self, receipt: LedgerReceipt) -> None:
        _id(receipt.principal_id)
        _id(receipt.client_request_id)
        if receipt.operation not in {
            "reserve",
            "consume",
            "release",
            "reconcile",
        } or not re.fullmatch(r"[0-9a-f]{64}", receipt.fingerprint):
            raise PolicyError("AI_POLICY_RESOURCE_RECEIPT_CONFLICT")
        if self.reservation(receipt.reservation_id) is None:
            raise PolicyError("AI_POLICY_RESERVATION_NOT_FOUND")
        self.connection.execute(
            insert(LEDGER_RECEIPT).values(
                organization_id=self.organization_id,
                feature_scope=self.feature_scope,
                **asdict(receipt),
            )
        )

    def reserve(
        self,
        terms: domain.LimitTerms,
        *,
        reservation_id: str,
        request_digest: str,
        attempt_id: str,
        estimated_units: int,
        event: LedgerEvent,
    ) -> domain.AccountingChange:
        self._scope(terms.key)
        existing = self.reservation(reservation_id)
        previous_attempt = self.attempt(request_digest, attempt_id)
        if previous_attempt is not None and previous_attempt != existing:
            raise PolicyError("AI_POLICY_RESERVATION_CONFLICT")
        change = domain.reserve(
            self.snapshot(terms),
            terms,
            reservation_id=reservation_id,
            request_digest=request_digest,
            attempt_id=attempt_id,
            estimated_units=estimated_units,
            existing=existing,
        )
        self._persist(change, event, previous=existing)
        return change

    def settle(
        self, reservation_id: str, proof: domain.SettlementProof, *, event: LedgerEvent
    ) -> domain.AccountingChange:
        previous = self.reservation(reservation_id)
        if previous is None:
            raise PolicyError("AI_POLICY_RESERVATION_NOT_FOUND")
        change = domain.settle(self.snapshot(previous.terms), previous, proof)
        self._persist(change, event, previous=previous)
        return change

    def _persist(
        self,
        change: domain.AccountingChange,
        event: LedgerEvent,
        *,
        previous: domain.Reservation | None,
    ) -> None:
        if change.replayed:
            return
        _id(event.event_id)
        _id(event.principal_id)
        if event.occurred_at.utcoffset() is None:
            raise PolicyError("AI_POLICY_INVALID_TIME")
        reservation, counters = change.reservation, change.snapshot
        self.connection.execute(
            update(RESOURCE_SCOPE)
            .where(self.scope_filter)
            .values(occupied_slots=counters.scope_occupied_slots)
        )
        self.connection.execute(
            update(BUCKET)
            .where(
                BUCKET.c.organization_id == self.organization_id,
                BUCKET.c.bucket_id == bucket_id(counters.key),
            )
            .values(held_units=counters.held_units, spent_units=counters.spent_units)
        )
        values = dict(
            organization_id=self.organization_id,
            reservation_id=reservation.reservation_id,
            feature_scope=self.feature_scope,
            bucket_id=bucket_id(counters.key),
            request_digest=reservation.request_digest,
            attempt_id=reservation.attempt_id,
            state=reservation.state.value,
            payload=asdict(reservation),
        )
        if previous is None:
            self.connection.execute(insert(RESERVATION).values(**values))
        else:
            result = self.connection.execute(
                update(RESERVATION)
                .where(
                    RESERVATION.c.organization_id == self.organization_id,
                    RESERVATION.c.reservation_id == reservation.reservation_id,
                    RESERVATION.c.state == domain.ReservationState.RESERVED.value,
                )
                .values(**values)
            )
            if result.rowcount != 1:
                raise PolicyError("AI_POLICY_RESERVATION_CONFLICT")
        self.connection.execute(
            insert(LEDGER_EVENT).values(
                organization_id=self.organization_id,
                feature_scope=self.feature_scope,
                reservation_id=reservation.reservation_id,
                **asdict(event),
                payload={
                    "kind": "ai_policy.resource_" + reservation.state.value,
                    "feature_scope": self.feature_scope,
                    "reservation": asdict(reservation),
                    "counters": asdict(counters),
                },
            )
        )


class SqlResourceLedgerStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @contextmanager
    def transaction(
        self, organization_id: str, feature_scope: str
    ) -> Iterator[ResourceLedgerTransaction]:
        try:
            with self.engine.begin() as connection:
                yield SqlResourceLedgerTransaction(connection, organization_id, feature_scope)
        except IntegrityError:
            raise PolicyError("AI_POLICY_RESOURCE_WRITE_CONFLICT") from None
        except DBAPIError:
            raise PolicyError("AI_POLICY_RESOURCE_STORAGE_UNAVAILABLE") from None
