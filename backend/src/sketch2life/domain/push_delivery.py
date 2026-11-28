"""Pure state and payload rules for best-effort push delivery (FEAT-066 goal v4, T-NTF1)."""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum
from typing import Final


class PushDeliveryStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DEAD_ENDPOINT = "DEAD_ENDPOINT"
    SKIPPED = "SKIPPED"


class PushDeliveryErrorCode(StrEnum):
    TRANSIENT = "TRANSIENT"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    ENDPOINT_GONE = "ENDPOINT_GONE"
    REJECTED = "REJECTED"
    SENDER_ERROR = "SENDER_ERROR"


MAX_ATTEMPTS: Final = 5
CLAIM_LEASE: Final = timedelta(seconds=120)
ENROLL_WINDOW: Final = timedelta(hours=24)
RETRY_BASE_SECONDS: Final = 60
RETRY_CAP_SECONDS: Final = 900


def retry_delay(attempt: int) -> timedelta:
    """Return the bounded exponential delay after a failed one-based attempt."""

    if type(attempt) is not int or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    seconds = RETRY_CAP_SECONDS if attempt >= 5 else RETRY_BASE_SECONDS * 2 ** (attempt - 1)
    return timedelta(seconds=seconds)


def push_pointer(inbox_item_id: str) -> dict[str, object]:
    """Build the content-free push pointer; inbox remains the notification source of truth."""

    if not isinstance(inbox_item_id, str) or not 1 <= len(inbox_item_id) <= 36:
        raise ValueError("inbox_item_id must be a non-empty inbox identifier")
    return {"v": 1, "kind": "INBOX_POINTER", "inbox_item_id": inbox_item_id}


__all__ = [
    "CLAIM_LEASE",
    "ENROLL_WINDOW",
    "MAX_ATTEMPTS",
    "PushDeliveryErrorCode",
    "PushDeliveryStatus",
    "RETRY_BASE_SECONDS",
    "RETRY_CAP_SECONDS",
    "push_pointer",
    "retry_delay",
]
