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
    luminance = np.asarray(gray, dtype=np.uint8)
    dark_ink = luminance < 170
    if int(dark_ink.sum()) >= 20 and float(dark_ink.mean()) <= 0.45:
        ink = _thin_ink(dark_ink)
    else:
        edges = np.asarray(gray.filter(ImageFilter.FIND_EDGES), dtype=np.uint8)
        ink = edges > 48
    ink[[0, -1], :] = False
    ink[:, [0, -1]] = False
    if int(ink.sum()) < 20:
        raise ValueError("LINE_ART_EMPTY")
    if float(ink.mean()) > 0.45:
        raise ValueError("LINE_ART_TOO_DENSE")

    ys, xs = np.where(ink)
    left, right = int(xs.min()), int(xs.max()) + 1
    top, bottom = int(ys.min()), int(ys.max()) + 1
    margin_x = max(6, round((right - left) * 0.08))
    margin_y = max(6, round((bottom - top) * 0.08))
    crop_left = max(0, left - margin_x)
    crop_top = max(0, top - margin_y)
    crop_right = min(ink.shape[1], right + margin_x)
    crop_bottom = min(ink.shape[0], bottom + margin_y)
    ink = ink[crop_top:crop_bottom, crop_left:crop_right]

    paths = _connected_ink_paths(ink, preserve_dots=True)
    if not paths:
        raise ValueError("LINE_ART_EMPTY")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_type": "whiteboard_strokes_v1",
        "source_hash": source_hash,
        "source_width": image.width,
        "source_height": image.height,
        "crop_box": [crop_left, crop_top, crop_right, crop_bottom],
        "width": ink.shape[1],
        "height": ink.shape[0],
        "strokes": [
            {"stroke_id": f"line-{index:04}", "points": points}
            for index, points in enumerate(paths, 1)
        ],
    }
    output.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return WhiteboardStrokeExtraction(
        source_hash=source_hash,
        stroke_ref=str(output),
        width=ink.shape[1],
        height=ink.shape[0],
        point_count=sum(len(path) for path in paths),
        stroke_count=len(paths),
    )


def _thin_ink(mask):
    """Reduce thick raster pen marks to one-pixel paths (Zhang-Suen thinning)."""

    import numpy as np

    ink = mask.copy()
    for _ in range(80):
        changed = False
        for first_pass in (True, False):
            padded = np.pad(ink, 1, mode="constant")
            p2 = padded[:-2, 1:-1]
            p3 = padded[:-2, 2:]
            p4 = padded[1:-1, 2:]
            p5 = padded[2:, 2:]
            p6 = padded[2:, 1:-1]
            p7 = padded[2:, :-2]
            p8 = padded[1:-1, :-2]
            p9 = padded[:-2, :-2]
            neighbors = (p2, p3, p4, p5, p6, p7, p8, p9)
            count = sum(point.astype(np.uint8) for point in neighbors)
            transitions = sum(
                (~point & neighbors[(index + 1) % 8]).astype(np.uint8)
                for index, point in enumerate(neighbors)
            )
            if first_pass:
                corner_a = ~(p2 & p4 & p6)
                corner_b = ~(p4 & p6 & p8)
            else:
                corner_a = ~(p2 & p4 & p8)
                corner_b = ~(p2 & p6 & p8)
            remove = (
                ink & (count >= 2) & (count <= 6) & (transitions == 1)
                & corner_a & corner_b
            )
            if bool(remove.any()):
                ink[remove] = False
                changed = True
        if not changed:
            break
    return ink


def _connected_ink_paths(ink, *, preserve_dots: bool = False) -> list[list[list[int]]]:
    """Trace adjacent pixels, drawing each connected ink component first."""

    import numpy as np

    ys, xs = np.where(ink)
    ordered = [(int(x), int(y)) for y, x in zip(ys, xs, strict=True)]
    remaining = set(ordered)
    paths: list[list[list[int]]] = []
    neighbors = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
    unassigned = remaining.copy()
    components: list[list[tuple[int, int]]] = []
    for seed in sorted(ordered, key=lambda point: (point[0], point[1])):
        if seed not in unassigned:
            continue
        unassigned.remove(seed)
        component = [seed]
        pending = [seed]
        while pending:
            x, y = pending.pop()
            for dx, dy in neighbors:
                neighbor = (x + dx, y + dy)
                if neighbor in unassigned:
                    unassigned.remove(neighbor)
                    pending.append(neighbor)
                    component.append(neighbor)
        components.append(component)

    for component in components:
        for start in sorted(component, key=lambda point: (point[1], point[0])):
            if start not in remaining:
                continue
            remaining.remove(start)
            path = [start]
            while True:
                x, y = path[-1]
                candidates = [
                    (x + dx, y + dy)
                    for dx, dy in neighbors
                    if (x + dx, y + dy) in remaining
                ]
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
            elif preserve_dots:
                # A short isolated mark is still visible ink (e.g. an eye or a dot).
                # Encode it as a zero-length pen stroke so the renderer can reveal it.
                x, y = path[0]
                paths.append([[x, y], [x, y]])
    return paths


__all__ = ["WhiteboardStrokeExtraction", "extract_image_line_art", "extract_mask_contours"]
