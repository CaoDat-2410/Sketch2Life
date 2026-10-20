"""Own resource ledger port; callers retain current authority/use fences to commit."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.domain.ai_policy.accounting import (
    AccountingChange,
    LedgerSnapshot,
    LimitTerms,
    Reservation,
    SettlementProof,
)


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    event_id: str
    principal_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class LedgerReceipt:
    principal_id: str
    client_request_id: str
    fingerprint: str
    reservation_id: str
    operation: str


class ResourceLedgerTransaction(Protocol):
    def snapshot(self, terms: LimitTerms) -> LedgerSnapshot: ...

    def reservation(self, reservation_id: str) -> Reservation | None: ...

    def attempt(self, request_digest: str, attempt_id: str) -> Reservation | None: ...

    def receipt(self, principal_id: str, client_request_id: str) -> LedgerReceipt | None: ...

    def add_receipt(self, receipt: LedgerReceipt) -> None: ...

    def reserve(
        self,
        terms: LimitTerms,
        *,
        reservation_id: str,
        request_digest: str,
        attempt_id: str,
        estimated_units: int,
        event: LedgerEvent,
    ) -> AccountingChange: ...

    def settle(
        self, reservation_id: str, proof: SettlementProof, *, event: LedgerEvent
    ) -> AccountingChange: ...


class ResourceLedgerStore(Protocol):
    def transaction(
        self, organization_id: str, feature_scope: str
    ) -> AbstractContextManager[ResourceLedgerTransaction]:
        """Serialize global scope, then original budget bucket/reservation/receipt.

        All counters, reservation, receipt and audit/outbox share one commit.
        Caller acquires current owner/use/accounting guards BEFORE this UoW and
        holds them through exit. Persistence alone never authorizes AI execution.
        """
        ...
