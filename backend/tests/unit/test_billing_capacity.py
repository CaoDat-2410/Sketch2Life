from datetime import UTC, datetime, timedelta

import pytest

from sketch2life.domain.billing_capacity import effective_state, period_end, prorated_vnd
from sketch2life.domain.platform_admin import AdminError


def test_monthly_and_annual_periods_clamp_calendar_days():
    assert period_end(datetime(2028, 1, 31, tzinfo=UTC), 1) == datetime(2028, 2, 29, tzinfo=UTC)
    assert period_end(datetime(2028, 2, 29, tzinfo=UTC), 12) == datetime(2029, 2, 28, tzinfo=UTC)


def test_proration_uses_exact_remaining_time_and_half_up_vnd_rounding():
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=10)
    assert prorated_vnd(1, 101, start, end, start + timedelta(days=5)) == 51
    assert prorated_vnd(2, 101, start, end, start) == 202
    with pytest.raises(AdminError):
        prorated_vnd(1, 101, start, end, end)


def test_full_seven_day_grace_and_period_end_cancellation():
    end = datetime(2026, 12, 1, tzinfo=UTC)
    assert effective_state("ACTIVE", end, end - timedelta(seconds=1)) == "ACTIVE"
    assert effective_state("ACTIVE", end, end + timedelta(days=7, microseconds=-1)) == "GRACE"
    assert effective_state("ACTIVE", end, end + timedelta(days=7)) == "RESTRICTED"
    assert effective_state("CANCEL_AT_PERIOD_END", end, end) == "CANCELED"


def test_quota_month_uses_vietnam_midnight_boundary():
    from sketch2life.domain.billing_capacity import quota_month

    assert quota_month(datetime(2026, 11, 30, 16, 59, 59, tzinfo=UTC)) == (
        "2026-11",
        datetime(2026, 11, 30, 17, tzinfo=UTC),
    )
    assert quota_month(datetime(2026, 11, 30, 17, tzinfo=UTC)) == (
        "2026-12",
        datetime(2026, 12, 31, 17, tzinfo=UTC),
    )
