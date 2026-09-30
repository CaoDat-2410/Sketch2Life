"""Deterministic binary mask fixtures shared by SAM quality tests and offline tooling."""

from __future__ import annotations

SYNTHETIC_ARCHETYPES = (
    "butterfly",
    "bird",
    "flower",
    "tree_branch",
    "fish",
    "biped",
    "rigid",
    "generic_organic",
    "unknown",
)


def empty_mask(size: int = 64) -> list[list[bool]]:
    return [[False for _ in range(size)] for _ in range(size)]


def ellipse(mask: list[list[bool]], cx: int, cy: int, rx: int, ry: int) -> None:
    for y in range(max(0, cy - ry), min(len(mask), cy + ry + 1)):
        for x in range(max(0, cx - rx), min(len(mask[0]), cx + rx + 1)):
            if ((x - cx) / max(1, rx)) ** 2 + ((y - cy) / max(1, ry)) ** 2 <= 1:
                mask[y][x] = True


def line(
    mask: list[list[bool]], x0: int, y0: int, x1: int, y1: int
) -> list[tuple[int, int]]:
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    points: list[tuple[int, int]] = []
    while True:
        if 0 <= x0 < len(mask[0]) and 0 <= y0 < len(mask):
            mask[y0][x0] = True
            points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return points
        double_error = 2 * error
        if double_error >= dy:
            error += dy
            x0 += sx
        if double_error <= dx:
            error += dx
            y0 += sy


def archetype_mask(archetype: str) -> tuple[list[list[bool]], list[list[bool]]]:
    """Return an analytic subject silhouette and a thin-feature reference mask."""
    mask = empty_mask()
    if archetype == "butterfly":
        ellipse(mask, 21, 24, 11, 13)
        ellipse(mask, 43, 24, 11, 13)
        ellipse(mask, 32, 30, 3, 15)
        detail_points = line(mask, 30, 15, 25, 8) + line(mask, 34, 15, 39, 8)
    elif archetype == "bird":
        ellipse(mask, 30, 32, 14, 9)
        ellipse(mask, 42, 24, 7, 7)
        line(mask, 16, 33, 8, 28)
        detail_points = line(mask, 48, 24, 56, 24) + line(mask, 28, 40, 26, 50)
    elif archetype == "flower":
        line(mask, 32, 34, 32, 57)
        ellipse(mask, 32, 27, 5, 5)
        for cx, cy in ((32, 17), (42, 27), (32, 37), (22, 27), (39, 20), (25, 20)):
            ellipse(mask, cx, cy, 5, 5)
        detail_points = line(mask, 32, 43, 24, 39)
    elif archetype == "tree_branch":
        line(mask, 32, 57, 32, 17)
        line(mask, 32, 34, 14, 18)
        line(mask, 32, 29, 51, 14)
        for cx, cy in ((13, 14), (20, 20), (52, 12), (44, 20)):
            ellipse(mask, cx, cy, 5, 4)
        detail_points = line(mask, 32, 34, 40, 39)
    elif archetype == "fish":
        ellipse(mask, 29, 31, 15, 9)
        line(mask, 43, 31, 55, 20)
        line(mask, 43, 31, 55, 42)
        detail_points = line(mask, 21, 27, 22, 27)
    elif archetype == "biped":
        ellipse(mask, 32, 13, 7, 7)
        line(mask, 32, 20, 32, 39)
        line(mask, 32, 27, 21, 36)
        line(mask, 32, 27, 43, 36)
        line(mask, 32, 39, 24, 54)
        line(mask, 32, 39, 40, 54)
        detail_points = line(mask, 28, 12, 29, 12)
    elif archetype == "rigid":
        for y in range(20, 39):
            for x in range(15, 50):
                mask[y][x] = True
        ellipse(mask, 21, 41, 6, 6)
        ellipse(mask, 44, 41, 6, 6)
        detail_points = line(mask, 32, 20, 32, 12)
    elif archetype == "generic_organic":
        ellipse(mask, 31, 31, 15, 13)
        ellipse(mask, 20, 22, 7, 8)
        detail_points = line(mask, 42, 28, 53, 21) + line(mask, 43, 35, 54, 41)
    elif archetype == "unknown":
        ellipse(mask, 25, 27, 10, 12)
        ellipse(mask, 38, 35, 11, 8)
        ellipse(mask, 40, 20, 4, 5)
        detail_points = line(mask, 25, 39, 18, 48)
    else:
        raise ValueError(f"Unsupported synthetic SAM archetype: {archetype}")

    details = empty_mask()
    for x, y in detail_points:
        details[y][x] = True
    return mask, details


__all__ = ["SYNTHETIC_ARCHETYPES", "archetype_mask", "ellipse", "empty_mask", "line"]
