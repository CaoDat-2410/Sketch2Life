"""Bind source-colored areas to the line paths that draw them.

This is a raster approximation, not semantic segmentation. Small disconnected
details are kept for the finished frame; large areas reveal after their nearby
outline instead of appearing in a scene-wide left-to-right wipe.
"""

from __future__ import annotations


def color_reveal_cells(width: int, height: int) -> tuple[tuple[int, int, int, int], ...]:
    """Cover a color region in short, alternating marker-like horizontal passes."""

    if width <= 0 or height <= 0:
        raise ValueError("color region dimensions must be positive")
    rows = min(12, height)
    columns = min(8, width)
    cells = []
    for row in range(rows):
        top = round(height * row / rows)
        bottom = round(height * (row + 1) / rows)
        for position in range(columns):
            column = position if row % 2 == 0 else columns - 1 - position
            left = round(width * column / columns)
            right = round(width * (column + 1) / columns)
            cells.append((left, top, right, bottom))
    return tuple(cells)


def prepare_color_regions(
    color_layer, raw_strokes, *, scale: float, offset_x: float, offset_y: float
):
    import numpy as np
    from PIL import Image

    rgba = np.asarray(color_layer.convert("RGBA"))
    active = rgba[:, :, 3] > 0
    visited = np.zeros(active.shape, dtype=bool)
    height, width = active.shape
    stroke_ends = []
    segment_end = 0
    for stroke in raw_strokes:
        points = stroke["points"]
        segment_end += max(0, len(points) - 1)
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        stroke_ends.append(
            (min(xs), min(ys), max(xs), max(ys), segment_end, stroke.get("color", [35, 35, 35]))
        )

    regions = []
    small = np.zeros(active.shape, dtype=bool)
    for seed_y, seed_x in np.argwhere(active):
        y, x = int(seed_y), int(seed_x)
        if visited[y, x]:
            continue
        visited[y, x] = True
        pending = [(x, y)]
        pixels = []
        left = right = x
        top = bottom = y
        while pending:
            px, py = pending.pop()
            pixels.append((px, py))
            left, right = min(left, px), max(right, px)
            top, bottom = min(top, py), max(bottom, py)
            for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                if 0 <= nx < width and 0 <= ny < height and active[ny, nx] and not visited[ny, nx]:
                    visited[ny, nx] = True
                    pending.append((nx, ny))
        if len(pixels) < 20 or len(regions) >= 128:
            for px, py in pixels:
                small[py, px] = True
            continue

        region = np.zeros((bottom - top + 1, right - left + 1, 4), dtype=np.uint8)
        for px, py in pixels:
            region[py - top, px - left] = rgba[py, px]
        mean_color = np.median(rgba[[py for _, py in pixels], [px for px, _ in pixels], :3], axis=0)
        nearby = [
            item
            for item in stroke_ends
            if item[0] <= right + 4
            and item[2] >= left - 4
            and item[1] <= bottom + 4
            and item[3] >= top - 4
        ]
        matched = [
            item
            for item in nearby
            if sum(abs(int(a) - int(b)) for a, b in zip(item[5], mean_color, strict=True)) < 110
        ]
        trigger = max((item[4] for item in (matched or nearby)), default=segment_end)
        destination = (round(offset_x + left * scale), round(offset_y + top * scale))
        fitted = Image.fromarray(region, "RGBA").resize(
            (max(1, round(region.shape[1] * scale)), max(1, round(region.shape[0] * scale))),
            Image.Resampling.LANCZOS,
        )
        regions.append((fitted, destination, trigger))

    if small.any():
        remaining = rgba.copy()
        remaining[:, :, 3] = np.where(small, rgba[:, :, 3], 0)
        fitted = Image.fromarray(remaining, "RGBA").resize(
            (max(1, round(width * scale)), max(1, round(height * scale))),
            Image.Resampling.LANCZOS,
        )
        regions.append((fitted, (round(offset_x), round(offset_y)), segment_end))
    return regions
