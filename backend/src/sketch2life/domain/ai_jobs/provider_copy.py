"""ProviderCopyLifecycle candidate semantics (contract owner BE2-14; BE2-01 fake support).

Only a *verified* receipt may move a copy to ``deleted``. A fixture receipt is marked as such
and never proves actual provider deletion. Pending/Unsupported/Exception never read as Deleted.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

CONTRACT_OWNER = "BE2-14"
FAKE_SUPPORT_OWNER = "BE2-01"


class CopyKind(StrEnum):
    INPUT = "input"
    OUTPUT = "output"
    JOB = "job"
    CACHE = "cache"


class CopyStatus(StrEnum):
    DISCOVERED = "discovered"
    CANCEL_REQUESTED = "cancel_requested"
    PURGE_REQUESTED = "purge_requested"
    DELETED = "deleted"
    PENDING = "pending"
    UNSUPPORTED = "unsupported"
    EXCEPTION = "exception"


class ReceiptOutcome(StrEnum):
    DELETED = "deleted"
    PENDING = "pending"
    UNSUPPORTED = "unsupported"
    EXCEPTION = "exception"


class EvidenceKind(StrEnum):
    FIXTURE = "fixture"
    PROVIDER = "provider"


class InvalidCopyTransition(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderCopy:
    copy_id: str
    organization_id: str
    scope_ref: str
    kind: CopyKind
    provider_profile: str
    status: CopyStatus = CopyStatus.DISCOVERED
    receipt_id: str | None = None
    evidence_kind: EvidenceKind | None = None
    reason_code: str | None = None

    @property
    def actual_deletion_proven(self) -> bool:
        return self.status is CopyStatus.DELETED and self.evidence_kind is EvidenceKind.PROVIDER


@dataclass(frozen=True, slots=True)
class PurgeReceipt:
    receipt_id: str
    copy_id: str
    outcome: ReceiptOutcome
    verified: bool
    evidence_kind: EvidenceKind
    reason_code: str | None = None


FINAL_STATUSES = frozenset({CopyStatus.DELETED})


def request_cancel(copy: ProviderCopy) -> ProviderCopy:
    if copy.status is not CopyStatus.DISCOVERED:
        return copy
    return replace(copy, status=CopyStatus.CANCEL_REQUESTED)


def request_purge(copy: ProviderCopy) -> ProviderCopy:
    if copy.status in FINAL_STATUSES:
        return copy
    return replace(copy, status=CopyStatus.PURGE_REQUESTED)


def apply_receipt(copy: ProviderCopy, receipt: PurgeReceipt) -> ProviderCopy:
    if receipt.copy_id != copy.copy_id:
        raise InvalidCopyTransition("receipt does not belong to this copy")
    if copy.status is CopyStatus.DELETED:
        if receipt.receipt_id == copy.receipt_id:
            return copy
        raise InvalidCopyTransition("deleted copy cannot change status")
    if copy.status not in {CopyStatus.PURGE_REQUESTED, CopyStatus.PENDING, CopyStatus.EXCEPTION}:
        raise InvalidCopyTransition(f"purge receipt not expected in {copy.status}")
    status = {
        ReceiptOutcome.DELETED: CopyStatus.DELETED,
        ReceiptOutcome.PENDING: CopyStatus.PENDING,
        ReceiptOutcome.UNSUPPORTED: CopyStatus.UNSUPPORTED,
        ReceiptOutcome.EXCEPTION: CopyStatus.EXCEPTION,
    }[receipt.outcome]
    if status is CopyStatus.DELETED and not receipt.verified:
        status = CopyStatus.PENDING
    return replace(
        copy,
        status=status,
        receipt_id=receipt.receipt_id,
        evidence_kind=receipt.evidence_kind,
        reason_code=receipt.reason_code,
    )


def report_label(copy: ProviderCopy) -> str:
    """Human/report label; a fixture deletion is never reported as actual deletion."""

    if copy.status is CopyStatus.DELETED:
        return "deleted" if copy.actual_deletion_proven else "fixture_deleted_not_actual"
    return str(copy.status)


__all__ = [
    "CONTRACT_OWNER",
    "FAKE_SUPPORT_OWNER",
    "CopyKind",
    "CopyStatus",
    "EvidenceKind",
    "InvalidCopyTransition",
    "ProviderCopy",
    "PurgeReceipt",
    "ReceiptOutcome",
    "apply_receipt",
    "report_label",
    "request_cancel",
    "request_purge",
]
