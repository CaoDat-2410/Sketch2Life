from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta, timezone

import pytest

from sketch2life.domain.billing_notice import (
    GRACE_PERIOD,
    NOTICE_LOOKBACK,
    RENEWAL_LEAD_1D,
    RENEWAL_LEAD_7D,
    BillingNoticeKind,
    billing_notice_local_date,
    billing_notice_trigger_id,
    canonical_utc,
    payment_notice_due,
    subscription_notice_due,
    subscription_notice_kind,
)

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("offset", "expected"),
    (
        (RENEWAL_LEAD_7D, BillingNoticeKind.RENEWAL_7D),
        (RENEWAL_LEAD_1D + timedelta(microseconds=1), BillingNoticeKind.RENEWAL_7D),
        (RENEWAL_LEAD_1D, BillingNoticeKind.RENEWAL_1D),
        (timedelta(microseconds=1), BillingNoticeKind.RENEWAL_1D),
        (timedelta(0), None),
    ),
)
def test_renewal_schedule_boundaries(offset: timedelta, expected: BillingNoticeKind | None) -> None:
    period_end = NOW + offset
    assert subscription_notice_kind("ACTIVE", period_end, NOW) is expected


def test_renewal_due_rejects_other_stored_states_and_cancellation() -> None:
    period_end = NOW + timedelta(days=7)
    for state in ("CANCEL_AT_PERIOD_END", "PAYMENT_PENDING", "GRACE", "CANCELED"):
        assert subscription_notice_kind(state, period_end, NOW) is None
    assert not subscription_notice_due(
        BillingNoticeKind.RENEWAL_1D,
        "ACTIVE",
        period_end,
        NOW,
    )


def test_grace_expiry_is_due_at_seven_days_and_expires_after_lookback() -> None:
    period_end = NOW - GRACE_PERIOD
    assert subscription_notice_kind("ACTIVE", period_end, NOW) is BillingNoticeKind.GRACE_EXPIRED
    assert subscription_notice_due(
        BillingNoticeKind.GRACE_EXPIRED,
        "GRACE",
        period_end,
        NOW,
    )
    assert (
        subscription_notice_kind(
            "ACTIVE",
            period_end,
            period_end + GRACE_PERIOD + NOTICE_LOOKBACK,
        )
        is None
    )
    assert (
        subscription_notice_kind(
            "ACTIVE",
            period_end,
            period_end + GRACE_PERIOD + NOTICE_LOOKBACK - timedelta(microseconds=1),
        )
        is BillingNoticeKind.GRACE_EXPIRED
    )


def test_payment_notice_matches_outcome_and_inclusive_lookback_edge() -> None:
    event_at = NOW - NOTICE_LOOKBACK
    assert payment_notice_due(
        BillingNoticeKind.PAYMENT_SUCCEEDED,
        "PAID",
        "PAID",
        event_at,
        NOW,
    )
    assert not payment_notice_due(
        BillingNoticeKind.PAYMENT_SUCCEEDED,
        "PAID",
        "CANCELED",
        event_at,
        NOW,
    )
    assert not payment_notice_due(
        BillingNoticeKind.PAYMENT_SUCCEEDED,
        "FAILED",
        "FAILED",
        event_at,
        NOW,
    )
    assert not payment_notice_due(
        BillingNoticeKind.PAYMENT_FAILED,
        "FAILED",
        "FAILED",
        event_at - timedelta(microseconds=1),
        NOW,
    )


def test_trigger_identity_is_stable_content_free_and_bounded() -> None:
    period_end = datetime(2026, 12, 2, 12, 0, 0, 123456, tzinfo=UTC)
    canonical = json.dumps(
        ["RENEWAL_7D", "sub-secret-account-42", "2026-12-02T12:00:00.123456Z"],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    trigger_id = billing_notice_trigger_id(
        BillingNoticeKind.RENEWAL_7D,
        "sub-secret-account-42",
        period_end=period_end,
    )
    assert trigger_id == "billing-notice." + hashlib.sha256(canonical.encode()).hexdigest()
    assert trigger_id == billing_notice_trigger_id(
        BillingNoticeKind.RENEWAL_7D,
        "sub-secret-account-42",
        period_end=period_end,
    )
    assert len(trigger_id) == 79 and len(trigger_id) <= 128
    assert "sub-secret-account-42" not in trigger_id
    assert "2026-12-02" not in trigger_id
    assert billing_notice_trigger_id(
        BillingNoticeKind.PAYMENT_SUCCEEDED,
        "provider-event-secret",
    ) == billing_notice_trigger_id(
        BillingNoticeKind.PAYMENT_SUCCEEDED,
        "provider-event-secret",
    )
    assert canonical_utc(period_end) == "2026-12-02T12:00:00.123456Z"
    with pytest.raises(ValueError):
        billing_notice_trigger_id(BillingNoticeKind.RENEWAL_7D, "sub-1")


def test_local_display_date_crosses_utc_midnight() -> None:
    period_end = datetime(2026, 1, 31, 17, 30, tzinfo=UTC)
    assert billing_notice_local_date(BillingNoticeKind.RENEWAL_1D, period_end) == "2026-02-01"
    assert billing_notice_local_date(BillingNoticeKind.GRACE_EXPIRED, period_end) == "2026-02-08"


@pytest.mark.parametrize("bad_now", (datetime(2026, 11, 25, 12, 0),))
def test_naive_now_is_rejected(bad_now: datetime) -> None:
    with pytest.raises(ValueError):
        subscription_notice_kind("ACTIVE", NOW + timedelta(days=7), bad_now)
    with pytest.raises(ValueError):
        payment_notice_due(
            BillingNoticeKind.PAYMENT_SUCCEEDED,
            "PAID",
            "PAID",
            NOW,
            bad_now,
        )


def test_non_utc_now_is_rejected_but_stored_timestamp_offsets_normalize() -> None:
    local_now = datetime(2026, 11, 25, 19, 0, tzinfo=timezone(timedelta(hours=7)))
    with pytest.raises(ValueError):
        subscription_notice_kind("ACTIVE", NOW + timedelta(days=7), local_now)
    local_period_end = datetime(2026, 12, 2, 19, 0, tzinfo=timezone(timedelta(hours=7)))
    assert canonical_utc(local_period_end) == "2026-12-02T12:00:00.000000Z"
