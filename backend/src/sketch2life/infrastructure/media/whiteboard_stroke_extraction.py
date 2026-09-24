"""Deterministic contour extraction from a validated whiteboard mask."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WhiteboardStrokeExtraction:
    source_hash: str
    stroke_ref: str
    width: int
    height: int
    point_count: int
    stroke_count: int


def extract_mask_contours(
    mask_path: str | Path,
    output_path: str | Path,
    *,
    source_hash: str,
) -> WhiteboardStrokeExtraction:
    """Extract deterministic boundary points and persist a JSON stroke artifact.

    This MVP preserves the source mask geometry. It does not infer the original
    hand-drawn order; that remains a later stroke-order strategy.
    """

    if len(source_hash) != 64 or any(char not in "0123456789abcdef" for char in source_hash):
        raise ValueError("source_hash must be a lowercase SHA-256 hex digest")

    try:
        import numpy as np
        from PIL import Image
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "stroke extraction requires the whiteboard-renderer dependencies"
        ) from error

    mask = np.asarray(Image.open(mask_path).convert("L")) > 0
    height, width = mask.shape
    if not bool(mask.any()):
        raise ValueError("MASK_EMPTY")

    interior = mask.copy()
    interior[1:, :] &= mask[:-1, :]
    interior[:-1, :] &= mask[1:, :]
    interior[:, 1:] &= mask[:, :-1]
    interior[:, :-1] &= mask[:, 1:]
    boundary = mask & ~interior
    ys, xs = np.where(boundary)
    points = [[int(x), int(y)] for y, x in zip(ys.tolist(), xs.tolist(), strict=True)]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_type": "whiteboard_strokes_v1",
        "source_hash": source_hash,
        "width": width,
        "height": height,
        "strokes": [{"stroke_id": "contour-001", "points": points}],
    }
    output.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return WhiteboardStrokeExtraction(
        source_hash=source_hash,
        stroke_ref=str(output),
        width=width,
        height=height,
        point_count=len(points),
        stroke_count=1,
    )


__all__ = ["WhiteboardStrokeExtraction", "extract_mask_contours"]
