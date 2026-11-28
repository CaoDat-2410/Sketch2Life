"""Offline tests for the capacity purchase quote foundation."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.billing.capacity_commerce import capacity_quote

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(days=30)
SETTINGS = SimpleNamespace(
    billing_real_payments_enabled=True,
    momo_payment_configured=True,
    vnpay_payment_configured=False,
)


class QuoteDB:
    def __init__(self):
        self.subscription = SimpleNamespace(
            subscription_id="sub", price_id="price", addon_slots=3, state="ACTIVE",
            period_start=START, period_end=END,
        )
        self.price = SimpleNamespace(
            price_id="price", cycle_months=1, base_amount_vnd=10000, slot_amount_vnd=1001,
        )
        self.scheduled = None
        self.calls = 0

    def scalar(self, statement):
        self.calls += 1
        return self.subscription if self.calls == 1 else self.scheduled

    def get(self, model, key):
        return self.price


def test_quote_uses_pinned_price_and_half_up_proration():
    result = capacity_quote(QuoteDB(), "org", 1, START + timedelta(days=15), SETTINGS)
    assert result["price_id"] == "price"
    assert result["amount_vnd"] == 501
    assert result["remaining_time_ratio"] == "0.5"
    assert result["resulting_capacity"] == 14
    assert result["period_end"] == END.isoformat()
    assert result["momo_checkout_enabled"] is True
    assert result["vnpay_checkout_enabled"] is False
    assert result["synthetic_sandbox_price"] is True


@pytest.mark.parametrize(
    ("change", "quantity", "now", "code"),
    [
        ("missing", 1, START, "SUBSCRIPTION_REQUIRED"),
        ("state", 1, START, "SUBSCRIPTION_NOT_ACTIVE"),
        ("none", 1, END, "SUBSCRIPTION_PERIOD_ENDED"),
        ("none", 998, START, "CAPACITY_LIMIT_EXCEEDED"),
        ("scheduled", 1, START, "DOWNGRADE_SCHEDULED"),
        ("none", 0, START, "INVALID_CAPACITY_QUOTE"),
    ],
)
def test_quote_refusals(change, quantity, now, code):
    db = QuoteDB()
    if change == "missing":
        db.subscription = None
    elif change == "state":
        db.subscription.state = "GRACE"
    elif change == "scheduled":
        db.scheduled = "event"
    with pytest.raises(AdminError) as error:
        capacity_quote(db, "org", quantity, now, SETTINGS)
    assert error.value.code == code
