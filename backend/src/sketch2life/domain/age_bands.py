"""Supported coarse age bands shared by lesson and activity workflows."""

from __future__ import annotations

_AGE_BANDS = (
    (36, 71, "36-71", "age-36-71-months-v1"),
    (72, 107, "72-107", "age-72-107-months-v1"),
    (108, 120, "108-120", "age-108-120-months-v1"),
)


def age_band_for_months(age_months: int) -> tuple[str, str] | None:
    """Return the existing display range and versioned reference for a supported age."""

    if isinstance(age_months, bool) or not isinstance(age_months, int):
        return None
    for minimum, maximum, label, reference in _AGE_BANDS:
        if minimum <= age_months <= maximum:
            return label, reference
    return None
