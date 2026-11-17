"""ProviderCopyLifecycle application candidate (contract owner BE2-14; BE2-01 fake support).

Scoped discovery, cancel and purge dispatch with idempotent receipts. Request authority comes
from the P2 lifecycle owner; this service only executes an already-authorised scope. Fake
receipts are fixture-marked and never reported as actual deletion.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from sketch2life.application.ports.ai_jobs import (
    ProviderCopyAdapterPort,
    ProviderCopyRegistryPort,
)
from sketch2life.domain.ai_jobs import provider_copy as lifecycle
from sketch2life.domain.ai_jobs.provider_copy import CopyStatus, ProviderCopy, PurgeReceipt


@dataclass(frozen=True, slots=True)
class CopyOutcome:
    copy_id: str
    kind: str
    status: str
    report_label: str
    receipt_id: str | None
    evidence_kind: str | None
    reason_code: str | None
    actual_deletion_proven: bool


class ProviderCopyLifecycleService:
    def __init__(
        self, registry: ProviderCopyRegistryPort, adapter: ProviderCopyAdapterPort
    ) -> None:
        self._registry = registry
        self._adapter = adapter

    def register_copy(self, copy: ProviderCopy) -> ProviderCopy:
        """A late copy in a purging scope is born purge-requested (no resurrection)."""

        with self._registry.scope_lock(copy.organization_id, copy.scope_ref):
            stored = self._registry.register(copy)
            if (
                self._registry.is_scope_purging(copy.organization_id, copy.scope_ref)
                and stored.status is CopyStatus.DISCOVERED
            ):
                stored = lifecycle.request_purge(stored)
                self._registry.save(stored)
            return stored

    def discover(self, organization_id: str, scope_ref: str) -> tuple[CopyOutcome, ...]:
        return tuple(
            _outcome(c) for c in self._registry.list_scope(organization_id, scope_ref)
        )

    def cancel_scope(self, organization_id: str, scope_ref: str) -> tuple[CopyOutcome, ...]:
        """Read, dispatch and save under the same scope lock as purge, so a stale cancellation
        can never overwrite a copy (and receipt) that a purge already advanced."""

        results = []
        with self._registry.scope_lock(organization_id, scope_ref):
            for copy in self._registry.list_scope(organization_id, scope_ref):
                updated = lifecycle.request_cancel(copy)
                if updated is not copy:
                    self._adapter.request_cancel(copy)
                    self._registry.save(updated)
                results.append(_outcome(updated))
        return tuple(results)

    def purge_scope(
        self, organization_id: str, scope_ref: str, idempotency_key: str
    ) -> tuple[CopyOutcome, ...]:
        """Purge each copy once per key. Concurrent same-key calls are serialised by the
        registry's scope lock, so exactly one dispatch happens and every caller sees the stored
        receipt. Replaying a key returns that request's immutable result and never mutates or
        re-dispatches a copy that a newer request already advanced (current state: discover)."""

        if not idempotency_key:
            raise ValueError("purge requires an idempotency key")
        results = []
        with self._registry.scope_lock(organization_id, scope_ref):
            self._registry.mark_scope_purging(organization_id, scope_ref)
            for copy in self._registry.list_scope(organization_id, scope_ref):
                receipt_key = f"{organization_id}:{scope_ref}:{idempotency_key}:{copy.copy_id}"
                stored = self._registry.get_purge_receipt(receipt_key)
                if stored is not None:
                    results.append(_outcome(_result_of(copy, stored)))
                    continue
                if copy.status is CopyStatus.DELETED:
                    results.append(_outcome(copy))
                    continue
                requested = lifecycle.request_purge(copy)
                receipt = self._registry.put_purge_receipt(
                    receipt_key, self._adapter.request_purge(requested)
                )
                current = lifecycle.apply_receipt(requested, receipt)
                self._registry.save(current)
                results.append(_outcome(current))
        return tuple(results)


def _result_of(copy: ProviderCopy, receipt: PurgeReceipt) -> ProviderCopy:
    """Projection of the copy as that receipt left it (pure; never saved)."""

    requested = replace(copy, status=CopyStatus.PURGE_REQUESTED, receipt_id=None,
                        evidence_kind=None, reason_code=None)
    return lifecycle.apply_receipt(requested, receipt)


def _outcome(copy: ProviderCopy) -> CopyOutcome:
    return CopyOutcome(
        copy_id=copy.copy_id,
        kind=str(copy.kind),
        status=str(copy.status),
        report_label=lifecycle.report_label(copy),
        receipt_id=copy.receipt_id,
        evidence_kind=str(copy.evidence_kind) if copy.evidence_kind else None,
        reason_code=copy.reason_code,
        actual_deletion_proven=copy.actual_deletion_proven,
    )


__all__ = ["CopyOutcome", "ProviderCopyLifecycleService"]
