"""Ports and immutable results for the internal T-1d2 reminder sweep.

The scan is a read-only keyset page. Processing re-locks and rechecks one run in a short
transaction; the infrastructure adapter owns that transaction and composes the existing producer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ReminderScanCursor:
    wait_since: datetime
    run_id: str


@dataclass(frozen=True, slots=True)
class ReminderCandidate:
    """Scan-time compare values; transaction code must take the recipient from the locked row."""

    run_id: str
    run_state: str
    revision: int
    owner_account_id: str | None
    wait_since: datetime

    @property
    def cursor(self) -> ReminderScanCursor:
        return ReminderScanCursor(wait_since=self.wait_since, run_id=self.run_id)


@dataclass(frozen=True, slots=True)
class ReminderCandidatePage:
    candidates: tuple[ReminderCandidate, ...]
    has_more: bool


class ReminderOutcome(StrEnum):
    CREATED = "created"
    ALREADY_PRESENT = "already_present"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class ReminderSweepResult:
    scanned: int
    created: int
    already_present: int
    skipped_stale: int
    failed: int
    next_cursor: str | None

    def __post_init__(self) -> None:
        counts = (self.scanned, self.created, self.already_present, self.skipped_stale, self.failed)
        if any(type(count) is not int or count < 0 for count in counts):
            raise ValueError("reminder sweep counts must be nonnegative integers")
        if self.created + self.already_present + self.skipped_stale + self.failed != self.scanned:
            raise ValueError("every scanned candidate must have exactly one outcome")


class ReminderScanPort(Protocol):
    def scan_candidates(
        self,
        now: datetime,
        limit: int,
        cursor: ReminderScanCursor | None,
    ) -> ReminderCandidatePage:
        """List due candidates in `(wait_since, run_id)` order without holding a transaction."""
        ...


class ReminderTransactionPort(Protocol):
    def enqueue_if_due(self, candidate: ReminderCandidate, now: datetime) -> ReminderOutcome:
        """Lock, revalidate, globally dedupe and enqueue one recipient-scoped inbox command."""
        ...


__all__ = [
    "ReminderCandidate",
    "ReminderCandidatePage",
    "ReminderOutcome",
    "ReminderScanCursor",
    "ReminderScanPort",
    "ReminderSweepResult",
    "ReminderTransactionPort",
]
