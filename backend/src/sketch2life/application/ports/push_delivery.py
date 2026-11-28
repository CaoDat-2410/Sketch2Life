"""Application boundaries for local-only push delivery (T-NTF1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol

from sketch2life.domain.push_delivery import PushDeliveryErrorCode

TemplateKey = tuple[str, int]


class PushSenderUnavailable(RuntimeError):
    """Raised when no approved sender composition exists for this environment."""


class PushSendOutcome(StrEnum):
    SENT = "SENT"
    TRANSIENT = PushDeliveryErrorCode.TRANSIENT.value
    TIMEOUT = PushDeliveryErrorCode.TIMEOUT.value
    RATE_LIMITED = PushDeliveryErrorCode.RATE_LIMITED.value
    ENDPOINT_GONE = PushDeliveryErrorCode.ENDPOINT_GONE.value
    REJECTED = PushDeliveryErrorCode.REJECTED.value
    SENDER_ERROR = PushDeliveryErrorCode.SENDER_ERROR.value


@dataclass(frozen=True, slots=True)
class PushMessage:
    """Opaque endpoint bytes plus the three-field content-free inbox pointer."""

    delivery_id: str
    push_endpoint_id: str
    endpoint_ciphertext: bytes = field(repr=False)
    payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class PushSendResult:
    outcome: PushSendOutcome


class PushSenderPort(Protocol):
    def send(self, message: PushMessage) -> PushSendResult:
        """Attempt one push without logging or retaining endpoint bytes or payload."""
        ...


@dataclass(frozen=True, slots=True)
class PushDeliveryClaim:
    delivery_id: str
    inbox_item_id: str
    push_endpoint_id: str
    recipient_account_id: str
    endpoint_ciphertext: bytes = field(repr=False)
    attempt_count: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PushDeliveryClaimResult:
    claim: PushDeliveryClaim | None
    skipped: bool = False
    failed: bool = False


class PushDeliveryRecordResult(StrEnum):
    SENT = "SENT"
    RETRY = "RETRY"
    FAILED = "FAILED"
    DEAD_ENDPOINT = "DEAD_ENDPOINT"
    STALE = "STALE"


class PushDeliveryStore(Protocol):
    def enroll(
        self,
        *,
        now: datetime,
        limit: int,
        eligible_templates: frozenset[TemplateKey],
        window: timedelta,
    ) -> int:
        """Insert missing ACTIVE endpoint/item pairs and return the inserted row count."""
        ...

    def claim_due(
        self, *, now: datetime, eligible_templates: frozenset[TemplateKey]
    ) -> PushDeliveryClaimResult:
        """Claim one head-of-line due row or mark one stale row SKIPPED."""
        ...

    def record_outcome(
        self,
        *,
        claim: PushDeliveryClaim,
        result: PushSendResult,
        now: datetime,
    ) -> PushDeliveryRecordResult:
        """Compare-and-set one sender result and optionally revoke a dead endpoint."""
        ...


__all__ = [
    "PushDeliveryClaim",
    "PushDeliveryClaimResult",
    "PushDeliveryRecordResult",
    "PushDeliveryStore",
    "PushMessage",
    "PushSendOutcome",
    "PushSenderPort",
    "PushSenderUnavailable",
    "PushSendResult",
    "TemplateKey",
]
