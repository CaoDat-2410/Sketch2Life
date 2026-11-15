"""Read-only local demo quota projection; it never reserves or consumes quota."""

from __future__ import annotations

from datetime import UTC, datetime

from sketch2life.contracts.schemas.parent_video_quota import ParentVideoQuotaSummaryV1


class LocalParentVideoQuotaUnavailable(RuntimeError):
    """Raised when the local-only quota projection is requested elsewhere."""


class LocalParentVideoQuotaService:
    def get_summary(
        self, *, granted: int, used: int, now: datetime | None = None
    ) -> ParentVideoQuotaSummaryV1:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        period_start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)

        return ParentVideoQuotaSummaryV1(
            mode="LOCAL_DEMO",
            configuration_state="CONFIGURED",
            period_start=period_start,
            period_end=period_end,
            granted=granted,
            used=used,
            available=max(granted - used, 0),
            notice=(
                "Số liệu demo local, chỉ để xem. Chưa có Billing thật và không trừ lượt."
            ),
        )


__all__ = ["LocalParentVideoQuotaService", "LocalParentVideoQuotaUnavailable"]
