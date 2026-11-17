"""Quality gates for masks produced by the whiteboard segmentation stage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WhiteboardMaskQuality:
    width: int
    height: int
    foreground_pixels: int
    coverage_ratio: float
    bounding_box: tuple[int, int, int, int]


def validate_mask_file(
    mask_path: str | Path,
    *,
    min_coverage_ratio: float = 0.01,
    max_coverage_ratio: float = 0.85,
) -> WhiteboardMaskQuality:
    """Validate a grayscale/boolean mask and return safe quality metrics."""

    if not 0.0 < min_coverage_ratio < max_coverage_ratio < 1.0:
        raise ValueError("mask coverage thresholds must satisfy 0 < min < max < 1")

    try:
        import numpy as np
        from PIL import Image
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "mask validation requires the whiteboard-renderer dependencies"
        ) from error

    mask = np.asarray(Image.open(mask_path).convert("L")) > 0
    height, width = mask.shape
    foreground_pixels = int(mask.sum())
    coverage_ratio = foreground_pixels / float(width * height)

    if foreground_pixels == 0:
        raise ValueError("MASK_EMPTY")
    if coverage_ratio < min_coverage_ratio:
        raise ValueError("MASK_TOO_SPARSE")
    if coverage_ratio > max_coverage_ratio:
        raise ValueError("MASK_TOO_DENSE")

    ys, xs = np.where(mask)
    bounding_box = (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))
    return WhiteboardMaskQuality(
        width=width,
        height=height,
        foreground_pixels=foreground_pixels,
        coverage_ratio=coverage_ratio,
        bounding_box=bounding_box,
    )


__all__ = ["WhiteboardMaskQuality", "validate_mask_file"]
