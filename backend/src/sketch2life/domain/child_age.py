"""Supported product audience age boundary, independent of catalog coverage."""

from __future__ import annotations

SUPPORTED_CHILD_MIN_AGE_MONTHS = 0
SUPPORTED_CHILD_MAX_AGE_MONTHS = 107
SUPPORTED_CHILD_AGE_BANDS = ("0-3", "3-6", "6-9")


def supported_child_age_band(age_months: int) -> str:
    """Return the supported product band for an adult/profile-supplied age in months."""

    if isinstance(age_months, bool) or not isinstance(age_months, int):
        raise ValueError("child age must be an integer number of completed months")
    if not SUPPORTED_CHILD_MIN_AGE_MONTHS <= age_months <= SUPPORTED_CHILD_MAX_AGE_MONTHS:
        raise ValueError("supported child age is under nine years (0–107 completed months)")
    if age_months < 36:
        return "0-3"
    if age_months < 72:
        return "3-6"
    return "6-9"
