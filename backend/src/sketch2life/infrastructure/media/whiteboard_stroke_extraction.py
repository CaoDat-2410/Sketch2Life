"""Deterministic contour extraction from a validated whiteboard mask."""

from __future__ import annotations

import hashlib
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
    rgb = np.asarray(image, dtype=np.uint8)
    gray = ImageOps.grayscale(image)
    luminance = np.asarray(gray, dtype=np.uint8)
    chromatic = (
        (rgb.max(axis=2).astype("int16") - rgb.min(axis=2).astype("int16") > 35)
        & (rgb.min(axis=2) < 230)
    )
    dark_ink = (luminance < 170) & ~chromatic
    color_interior = chromatic.copy()
    color_interior[1:, :] &= chromatic[:-1, :]
    color_interior[:-1, :] &= chromatic[1:, :]
    color_interior[:, 1:] &= chromatic[:, :-1]
    color_interior[:, :-1] &= chromatic[:, 1:]
    visible_ink = dark_ink | (chromatic & ~color_interior)
    if int(visible_ink.sum()) >= 20 and float(visible_ink.mean()) <= 0.45:
        ink = _thin_ink(visible_ink)
    else:
        edges = np.asarray(image.filter(ImageFilter.FIND_EDGES), dtype=np.uint8)
        ink = edges.max(axis=2) > 48
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
    cropped_rgb = rgb[crop_top:crop_bottom, crop_left:crop_right]
    cropped_chromatic = chromatic[crop_top:crop_bottom, crop_left:crop_right]

    # Traverse edges rather than consuming pixels. Greedy pixel removal leaves
    # many false isolated dots around curved/junction pixels (the synthetic
    # three-figure sample produced 125 dots from only 159 paths).
    paths = _graph_ink_paths(ink, preserve_dots=True)
    if not paths:
        raise ValueError("LINE_ART_EMPTY")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    color_layer_sha256 = None
    if bool(cropped_chromatic.any()):
        color_pixels = np.empty((*cropped_rgb.shape[:2], 4), dtype=np.uint8)
        color_pixels[:, :, :3] = cropped_rgb
        color_pixels[:, :, 3] = np.where(cropped_chromatic, 255, 0).astype(np.uint8)
        color_layer_path = output.with_suffix(".color.png")
        Image.fromarray(color_pixels, "RGBA").save(color_layer_path)
        with color_layer_path.open("rb") as source:
            color_layer_sha256 = hashlib.file_digest(source, "sha256").hexdigest()

    def path_color(points: list[list[int]]) -> list[int]:
        colors = np.asarray([cropped_rgb[y, x] for x, y in points], dtype=np.uint8)
        return [int(channel) for channel in np.median(colors, axis=0)]

    payload = {
        "artifact_type": "whiteboard_strokes_v1",
        "source_hash": source_hash,
        "source_width": image.width,
        "source_height": image.height,
        "crop_box": [crop_left, crop_top, crop_right, crop_bottom],
        "width": ink.shape[1],
        "height": ink.shape[0],
        "strokes": [
            {"stroke_id": f"line-{index:04}", "points": points, "color": path_color(points)}
            for index, points in enumerate(paths, 1)
        ],
    }
    if color_layer_sha256 is not None:
        payload["color_layer_sha256"] = color_layer_sha256
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


def _graph_ink_paths(ink, *, preserve_dots: bool = False) -> list[list[list[int]]]:
    """Trace each skeleton edge into a continuous chain without orphaning pixels.

    Diagonal edges are suppressed only when an orthogonal two-step alternative
    exists. This removes tiny triangle branches around antialiased corners.
    The result is deterministic and still cannot infer the artist's pen order.
    """

    import numpy as np

    ys, xs = np.where(ink)
    pixels = {(int(x), int(y)) for y, x in zip(ys, xs, strict=True)}
    directions = ((1, 0), (0, 1), (-1, 0), (0, -1),
                  (1, 1), (-1, 1), (-1, -1), (1, -1))
    neighbors: dict[tuple[int, int], tuple[tuple[int, int], ...]] = {}
    for x, y in pixels:
        adjacent = []
        for dx, dy in directions:
            other = (x + dx, y + dy)
            if other not in pixels:
                continue
            if dx and dy and ((x + dx, y) in pixels or (x, y + dy) in pixels):
                continue
            adjacent.append(other)
        neighbors[x, y] = tuple(sorted(adjacent, key=lambda p: (p[1], p[0])))

    def edge(a, b):
        return (a, b) if a <= b else (b, a)

    used: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    paths: list[list[list[int]]] = []

    def walk(start, next_point):
        chain = [start, next_point]
        used.add(edge(start, next_point))
        previous, current = start, next_point
        while len(neighbors[current]) == 2:
            candidates = [p for p in neighbors[current] if p != previous]
            if not candidates or edge(current, candidates[0]) in used:
                break
            following = candidates[0]
            used.add(edge(current, following))
            chain.append(following)
            previous, current = current, following
        paths.append([[x, y] for x, y in chain])

    ordered = sorted(pixels, key=lambda p: (p[0], p[1]))
    for pixel in ordered:
        if len(neighbors[pixel]) != 2:
            if not neighbors[pixel] and preserve_dots:
                paths.append([[pixel[0], pixel[1]], [pixel[0], pixel[1]]])
            for other in neighbors[pixel]:
                if edge(pixel, other) not in used:
                    walk(pixel, other)
    # Remaining edges belong to closed loops with no endpoint or junction.
    for pixel in ordered:
        for other in neighbors[pixel]:
            if edge(pixel, other) not in used:
                walk(pixel, other)
    return paths


__all__ = ["WhiteboardStrokeExtraction", "extract_image_line_art", "extract_mask_contours"]
