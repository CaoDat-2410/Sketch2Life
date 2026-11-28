"""Ports and immutable results for the billing notice scan and inbox transaction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from sketch2life.domain.billing_notice import BillingNoticeKind, BillingNoticeSource


@dataclass(frozen=True, slots=True)
class BillingNoticeScanCursor:
    source: BillingNoticeSource
    timestamp: datetime
    candidate_id: str


@dataclass(frozen=True, slots=True)
class BillingNoticeCandidate:
    """Scan-time compare values; recipients and current source state are re-read transactionally."""

    source: BillingNoticeSource
    kind: BillingNoticeKind
    subject_id: str
    timestamp: datetime
    owner_kind: str
    owner_ref: str
    state: str
    invoice_id: str | None = None

    @property
    def cursor(self) -> BillingNoticeScanCursor:
        return BillingNoticeScanCursor(
            source=self.source,
            timestamp=self.timestamp,
            candidate_id=self.subject_id,
        )


@dataclass(frozen=True, slots=True)
class BillingNoticeCandidatePage:
    """A bounded page, including failed rows and the key of its last scanned row."""

    candidates: tuple[BillingNoticeCandidate, ...]
    has_more: bool
    failed_count: int = 0
    last_cursor: BillingNoticeScanCursor | None = None


class BillingNoticeOutcome(StrEnum):
    CREATED = "created"
    ALREADY_PRESENT = "already_present"
    STALE = "stale"
    NO_RECIPIENT = "no_recipient"


@dataclass(frozen=True, slots=True)
class BillingNoticeSweepResult:
    scanned: int
    created: int
    already_present: int
    skipped_stale: int
    no_recipient: int
    failed: int
    next_cursor: str | None

    def __post_init__(self) -> None:
        counts = (
            self.scanned,
            self.created,
            self.already_present,
            self.skipped_stale,
            self.no_recipient,
            self.failed,
        )
        if any(type(count) is not int or count < 0 for count in counts):
            raise ValueError("billing notice sweep counts must be nonnegative integers")
        outcomes = (
            self.created
            + self.already_present
            + self.skipped_stale
            + self.no_recipient
            + self.failed
        )
        if outcomes != self.scanned:
            raise ValueError("every scanned candidate must have exactly one outcome")


class BillingNoticeScanPort(Protocol):
    def scan_candidates(
        self,
        now: datetime,
        source: BillingNoticeSource,
        limit: int,
        cursor: BillingNoticeScanCursor | None,
    ) -> BillingNoticeCandidatePage:
        """Read one bounded source page without retaining a transaction or lock."""
        ...


class BillingNoticeTransactionPort(Protocol):
    def enqueue_if_due(
        self, candidate: BillingNoticeCandidate, now: datetime
    ) -> BillingNoticeOutcome:
        """Lock, revalidate, globally dedupe and enqueue all current recipients atomically."""
        ...


__all__ = [
    "BillingNoticeCandidate",
    "BillingNoticeCandidatePage",
    "BillingNoticeOutcome",
    "BillingNoticeScanCursor",
    "BillingNoticeScanPort",
    "BillingNoticeSweepResult",
    "BillingNoticeTransactionPort",
]
