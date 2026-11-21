"""UTC billing-period arithmetic with explicit half-up VND rounding."""

import calendar
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sketch2life.domain.platform_admin import AdminError


def period_end(start: datetime, months: int) -> datetime:
    if start.tzinfo is None or months not in {1, 12}:
        raise AdminError("INVALID_BILLING_PERIOD", 422)
    year, month = divmod(start.year * 12 + start.month - 1 + months, 12)
    month += 1
    return start.replace(
        year=year, month=month, day=min(start.day, calendar.monthrange(year, month)[1])
    )


def prorated_vnd(slots: int, slot_price: int, start: datetime, end: datetime, now: datetime) -> int:
    if slots < 1 or slot_price < 1 or not start <= now < end:
        raise AdminError("INVALID_CAPACITY_QUOTE", 422)

    def micros(delta: timedelta):
        return delta.days * 86400000000 + delta.seconds * 1000000 + delta.microseconds

    amount = Decimal(slots * slot_price) * Decimal(micros(end - now)) / Decimal(micros(end - start))
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def effective_state(state: str, end: datetime, now: datetime) -> str:
    if now < end:
        return state
    if state == "CANCEL_AT_PERIOD_END":
        return "CANCELED"
    if state in {"ACTIVE", "GRACE"}:
        return "GRACE" if now < end + timedelta(days=7) else "RESTRICTED"
    return state


def quota_month(now):
    """Product quota follows the Vietnam calendar, independent of server timezone."""
    from zoneinfo import ZoneInfo

    local = now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    end = datetime(local.year + (local.month == 12), local.month % 12 + 1, 1, tzinfo=local.tzinfo)
    return local.strftime("%Y-%m"), end.astimezone(UTC)
