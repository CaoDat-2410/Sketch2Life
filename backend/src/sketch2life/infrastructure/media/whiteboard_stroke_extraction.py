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
    """Extract deterministic contour points and persist a JSON stroke artifact.

    A raster mask cannot recover the artist's original hand order. It can still
    provide a stable contour order for the whiteboard renderer, which is a useful
    approximation until the image generator emits layered/SVG stroke data.
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
    paths = _connected_ink_paths(boundary)
    if not paths:
        raise ValueError("MASK_CONTOUR_EMPTY")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_type": "whiteboard_strokes_v1",
        "source_hash": source_hash,
        "width": width,
        "height": height,
        "strokes": [
            {"stroke_id": f"contour-{index:03}", "points": points}
            for index, points in enumerate(paths, 1)
        ],
    }
    output.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return WhiteboardStrokeExtraction(
        source_hash=source_hash,
        stroke_ref=str(output),
        width=width,
        height=height,
        point_count=sum(len(points) for points in paths),
        stroke_count=len(paths),
    )


def extract_image_line_art(
    image_path: str | Path,
    output_path: str | Path,
    *,
    source_hash: str,
) -> WhiteboardStrokeExtraction:
    """Trace visible lines in a scene illustration into short connected paths.

    This approximates drawing order from a raster image. Each path contains
    adjacent pixels only, so the renderer never draws a line across empty space.
    """

    if len(source_hash) != 64 or any(char not in "0123456789abcdef" for char in source_hash):
        raise ValueError("source_hash must be a lowercase SHA-256 hex digest")
    try:
        import numpy as np
        from PIL import Image, ImageFilter, ImageOps
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError("line-art extraction requires Pillow and NumPy") from error

    image = Image.open(image_path).convert("RGB")
    image.thumbnail((560, 560), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(image)
    edges = np.asarray(gray.filter(ImageFilter.FIND_EDGES), dtype=np.uint8)
    ink = edges > 48
    ink[[0, -1], :] = False
    ink[:, [0, -1]] = False
    if int(ink.sum()) < 20:
        raise ValueError("LINE_ART_EMPTY")
    if float(ink.mean()) > 0.45:
        raise ValueError("LINE_ART_TOO_DENSE")

    paths = _connected_ink_paths(ink)
    if not paths:
        raise ValueError("LINE_ART_EMPTY")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_type": "whiteboard_strokes_v1",
        "source_hash": source_hash,
        "width": image.width,
        "height": image.height,
        "strokes": [
            {"stroke_id": f"line-{index:04}", "points": points}
            for index, points in enumerate(paths, 1)
        ],
    }
    output.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return WhiteboardStrokeExtraction(
        source_hash=source_hash,
        stroke_ref=str(output),
        width=image.width,
        height=image.height,
        point_count=sum(len(path) for path in paths),
        stroke_count=len(paths),
    )


def _connected_ink_paths(ink) -> list[list[list[int]]]:
    """Greedily trace adjacent ink pixels, splitting at every pen lift."""

    import numpy as np

    ys, xs = np.where(ink)
    ordered = [(int(x), int(y)) for y, x in zip(ys, xs, strict=True)]
    remaining = set(ordered)
    paths: list[list[list[int]]] = []
    neighbors = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
    for start in ordered:
        if start not in remaining:
            continue
        remaining.remove(start)
        path = [start]
        while True:
            x, y = path[-1]
            candidates = [(x + dx, y + dy) for dx, dy in neighbors if (x + dx, y + dy) in remaining]
            if not candidates:
                break
            if len(path) > 1:
                prev_x, prev_y = path[-2]
                dx, dy = x - prev_x, y - prev_y
                next_point = max(
                    candidates,
                    key=lambda point: (
                        (point[0] - x) * dx + (point[1] - y) * dy,
                        -point[1],
                        -point[0],
                    ),
                )
            else:
                next_point = candidates[0]
            remaining.remove(next_point)
            path.append(next_point)
        if len(path) >= 2:
            paths.append([[x, y] for x, y in path])
    return paths


__all__ = ["WhiteboardStrokeExtraction", "extract_image_line_art", "extract_mask_contours"]
