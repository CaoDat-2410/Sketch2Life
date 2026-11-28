"""Pure schedule, identity and privacy rules for billing admin notices (T-BILLN1)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Final
from zoneinfo import ZoneInfo

from sketch2life.domain.billing_capacity import effective_state

RENEWAL_LEAD_7D: Final = timedelta(days=7)
RENEWAL_LEAD_1D: Final = timedelta(days=1)
GRACE_PERIOD: Final = timedelta(days=7)
NOTICE_LOOKBACK: Final = timedelta(hours=72)
MAX_ORG_RECIPIENTS: Final = 20
BILLING_DISPLAY_TZ: Final = "Asia/Ho_Chi_Minh"
BILLING_TEMPLATE_VERSION: Final = 1
BILLING_TEMPLATE_KIND: Final = "BILLING"
_TRIGGER_PREFIX: Final = "billing-notice."
_LOCAL_TZ: Final = ZoneInfo(BILLING_DISPLAY_TZ)


class BillingNoticeKind(StrEnum):
    RENEWAL_7D = "RENEWAL_7D"
    RENEWAL_1D = "RENEWAL_1D"
    GRACE_EXPIRED = "GRACE_EXPIRED"
    PAYMENT_SUCCEEDED = "PAYMENT_SUCCEEDED"
    PAYMENT_FAILED = "PAYMENT_FAILED"


class BillingNoticeSource(StrEnum):
    SUBSCRIPTIONS = "subscriptions"
    PAYMENTS = "payments"


BILLING_RENEWAL_DUE_7D: Final = "BILLING_RENEWAL_DUE_7D"
BILLING_RENEWAL_DUE_1D: Final = "BILLING_RENEWAL_DUE_1D"
BILLING_GRACE_EXPIRED: Final = "BILLING_GRACE_EXPIRED"
BILLING_ORG_PAYMENT_SUCCEEDED: Final = "BILLING_ORG_PAYMENT_SUCCEEDED"
BILLING_ORG_PAYMENT_FAILED: Final = "BILLING_ORG_PAYMENT_FAILED"
BILLING_PARENT_PAYMENT_SUCCEEDED: Final = "BILLING_PARENT_PAYMENT_SUCCEEDED"
BILLING_PARENT_PAYMENT_FAILED: Final = "BILLING_PARENT_PAYMENT_FAILED"

SUBSCRIPTION_NOTICE_KINDS: Final = frozenset(
    {
        BillingNoticeKind.RENEWAL_7D,
        BillingNoticeKind.RENEWAL_1D,
        BillingNoticeKind.GRACE_EXPIRED,
    }
)
PAYMENT_NOTICE_KINDS: Final = frozenset(
    {BillingNoticeKind.PAYMENT_SUCCEEDED, BillingNoticeKind.PAYMENT_FAILED}
)


def require_aware_utc(value: datetime, *, field: str = "datetime") -> datetime:
    """Return a UTC instant and reject naive or non-UTC injected clocks."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be UTC")
    return value.astimezone(UTC)


def normalize_utc(value: datetime, *, field: str = "datetime") -> datetime:
    """Normalize a stored timezone-aware timestamp; PostgreSQL may return another offset."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def canonical_utc(value: datetime) -> str:
    """Return the same six-digit UTC ``Z`` spelling used by the reminder identity."""

    instant = normalize_utc(value, field="timestamp")
    return instant.isoformat(timespec="microseconds").replace("+00:00", "Z")


def subscription_notice_kind(
    state: str, period_end: datetime, now: datetime
) -> BillingNoticeKind | None:
    """Select the one currently open subscription notice window, if any."""

    instant = require_aware_utc(now, field="now")
    end = normalize_utc(period_end, field="period_end")
    if state == "ACTIVE":
        if end - RENEWAL_LEAD_7D <= instant < end - RENEWAL_LEAD_1D:
            return BillingNoticeKind.RENEWAL_7D
        if end - RENEWAL_LEAD_1D <= instant < end:
            return BillingNoticeKind.RENEWAL_1D
    if (
        effective_state(state, end, instant) == "RESTRICTED"
        and instant < end + GRACE_PERIOD + NOTICE_LOOKBACK
    ):
        return BillingNoticeKind.GRACE_EXPIRED
    return None


def subscription_notice_due(
    kind: BillingNoticeKind, state: str, period_end: datetime, now: datetime
) -> bool:
    """Check a candidate kind without allowing one renewal window to leak into another."""

    return subscription_notice_kind(state, period_end, now) is kind


def payment_notice_due(
    kind: BillingNoticeKind,
    outcome: str,
    invoice_state: str,
    created_at: datetime,
    now: datetime,
) -> bool:
    """Whether one immutable payment event is recent and still matches its invoice outcome."""

    instant = require_aware_utc(now, field="now")
    created = normalize_utc(created_at, field="created_at")
    expected_outcome = {
        BillingNoticeKind.PAYMENT_SUCCEEDED: "PAID",
        BillingNoticeKind.PAYMENT_FAILED: "FAILED",
    }.get(kind)
    return (
        expected_outcome is not None
        and outcome == expected_outcome
        and invoice_state == expected_outcome
        and created >= instant - NOTICE_LOOKBACK
    )


def billing_notice_trigger_id(
    kind: BillingNoticeKind,
    subject_id: str,
    *,
    period_end: datetime | None = None,
) -> str:
    """Return a stable, content-free trigger key for a subscription period or payment event."""

    if not subject_id:
        raise ValueError("subject_id must not be empty")
    if kind in SUBSCRIPTION_NOTICE_KINDS:
        if period_end is None:
            raise ValueError("subscription notices require period_end")
        identity = [kind.value, subject_id, canonical_utc(period_end)]
    elif kind in PAYMENT_NOTICE_KINDS:
        if period_end is not None:
            raise ValueError("payment notices do not use period_end")
        identity = [kind.value, subject_id]
    else:  # defensive when this enum grows without an identity rule
        raise ValueError("unsupported billing notice kind")
    canonical = json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
    return f"{_TRIGGER_PREFIX}{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def billing_notice_local_date(kind: BillingNoticeKind, period_end: datetime) -> str:
    """Format the displayed due date in the configured billing timezone."""

    if kind not in SUBSCRIPTION_NOTICE_KINDS:
        raise ValueError("local due date applies only to subscription notices")
    due_at = normalize_utc(period_end, field="period_end")
    if kind is BillingNoticeKind.GRACE_EXPIRED:
        due_at += GRACE_PERIOD
    return due_at.astimezone(_LOCAL_TZ).date().isoformat()


__all__ = [
    "BILLING_DISPLAY_TZ",
    "BILLING_GRACE_EXPIRED",
    "BILLING_ORG_PAYMENT_FAILED",
    "BILLING_ORG_PAYMENT_SUCCEEDED",
    "BILLING_PARENT_PAYMENT_FAILED",
    "BILLING_PARENT_PAYMENT_SUCCEEDED",
    "BILLING_RENEWAL_DUE_1D",
    "BILLING_RENEWAL_DUE_7D",
    "BILLING_TEMPLATE_KIND",
    "BILLING_TEMPLATE_VERSION",
    "BillingNoticeKind",
    "BillingNoticeSource",
    "GRACE_PERIOD",
    "MAX_ORG_RECIPIENTS",
    "NOTICE_LOOKBACK",
    "PAYMENT_NOTICE_KINDS",
    "RENEWAL_LEAD_1D",
    "RENEWAL_LEAD_7D",
    "SUBSCRIPTION_NOTICE_KINDS",
    "billing_notice_local_date",
    "billing_notice_trigger_id",
    "canonical_utc",
    "normalize_utc",
    "payment_notice_due",
    "require_aware_utc",
    "subscription_notice_due",
    "subscription_notice_kind",
]
