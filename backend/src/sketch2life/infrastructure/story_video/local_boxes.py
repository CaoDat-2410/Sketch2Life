"""Validation of the stored 20x20 grid boxes of drawing subjects (shared by the video source reader)."""

from __future__ import annotations

from typing import Any

GRID_MAX = 20


def grid_box(value: Any) -> tuple[int, int, int, int] | None:
    """``(x0, y0, x1, y1)`` inside the 0..20 grid with positive size, else None."""

    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    if any(isinstance(item, bool) or not isinstance(item, int) for item in value):
        return None
    x0, y0, x1, y1 = value
    if not (0 <= x0 < x1 <= GRID_MAX and 0 <= y0 < y1 <= GRID_MAX):
        return None
    return x0, y0, x1, y1


__all__ = ["GRID_MAX", "grid_box"]
