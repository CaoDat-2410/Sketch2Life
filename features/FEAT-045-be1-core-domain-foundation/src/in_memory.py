"""Synthetic adapters used only by the BE1-01 fixture runner."""

from __future__ import annotations

from threading import RLock

from sketch2life.application.ports.core_foundation import CanvasMutationCommit
from sketch2life.domain.core_foundation import IdempotencyReceipt


class InMemoryCoreMutationLedger:
    """Fixture implementation of revision and idempotency ports with atomic commit."""

    def __init__(self) -> None:
        self._revisions: dict[str, int] = {}
        self._receipts: dict[tuple[str, str], IdempotencyReceipt] = {}
        self._operation_ids: set[str] = set()
        self._outbox_event_ids: set[str] = set()
        self._audit_count = 0
        self._lock = RLock()

    def set_revision(self, aggregate_id: str, revision: int) -> None:
        with self._lock:
            self._revisions[aggregate_id] = revision

    def seed_receipt(self, receipt: IdempotencyReceipt) -> None:
        with self._lock:
            self._receipts[(receipt.scope, receipt.key)] = receipt

    def current_revision(self, aggregate_id: str) -> int | None:
        with self._lock:
            return self._revisions.get(aggregate_id)

    def get_receipt(self, *, scope: str, key: str) -> IdempotencyReceipt | None:
        with self._lock:
            return self._receipts.get((scope, key))

    def commit_canvas_mutation(self, mutation: CanvasMutationCommit) -> bool:
        with self._lock:
            receipt = mutation.receipt
            receipt_key = (receipt.scope, receipt.key)
            current = self._revisions.get(mutation.aggregate_id)
            if (
                current != mutation.expected_revision
                or mutation.next_revision != mutation.expected_revision + 1
                or receipt.resulting_revision != mutation.next_revision
            ):
                return False
            if (
                receipt_key in self._receipts
                or mutation.operation.operation_id in self._operation_ids
                or mutation.outbox_event_id in self._outbox_event_ids
            ):
                return False
            self._revisions[mutation.aggregate_id] = mutation.next_revision
            self._receipts[receipt_key] = receipt
            self._operation_ids.add(mutation.operation.operation_id)
            self._outbox_event_ids.add(mutation.outbox_event_id)
            self._audit_count += 1
            return True


__all__ = ["InMemoryCoreMutationLedger"]
