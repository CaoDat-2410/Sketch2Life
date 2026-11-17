"""Capacity and cooperative rendering budgets for the bounded canvas pilot."""

from __future__ import annotations

import math
from time import monotonic

from sketch2life.contracts.schemas.be1_runtime import CanvasSourceExportV1

MAX_STROKES = 500
MAX_POINTS = 60_000
RENDER_DEADLINE_SECONDS = 6.0


class CanvasSourceTooLarge(ValueError):
    """The authoritative operation history exceeds the pilot canvas capacity."""


class CanvasRenderBusy(RuntimeError):
    """Another render held the single process slot through the remaining budget."""


class CanvasRenderDeadlineExceeded(TimeoutError):
    """The cooperative total rendering budget has expired."""


def check_render_deadline(deadline: float) -> None:
    if not math.isfinite(deadline) or monotonic() >= deadline:
        raise CanvasRenderDeadlineExceeded("canvas rendering deadline exceeded")


def validate_source_capacity(source: CanvasSourceExportV1) -> None:
    """Count server-exported operations and array-valued points before allocating an image."""

    if len(source.operations) > MAX_STROKES:
        raise CanvasSourceTooLarge("canvas source exceeds the stroke limit")
    points_count = 0
    for operation in source.operations:
        points = operation.operation_payload.get("points")
        if isinstance(points, list):
            points_count += len(points)
        if points_count > MAX_POINTS:
            raise CanvasSourceTooLarge("canvas source exceeds the point limit")


__all__ = [
    "MAX_POINTS",
    "MAX_STROKES",
    "RENDER_DEADLINE_SECONDS",
    "CanvasRenderBusy",
    "CanvasRenderDeadlineExceeded",
    "CanvasSourceTooLarge",
    "check_render_deadline",
    "monotonic",
    "validate_source_capacity",
]
