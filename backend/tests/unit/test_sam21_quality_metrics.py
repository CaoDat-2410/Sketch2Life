from __future__ import annotations

import pytest

from sketch2life.infrastructure.ai.sam21_quality import (
    part_parent_consistency,
    score_mask,
)


def _empty(size: int = 64) -> list[list[bool]]:
    return [[False for _ in range(size)] for _ in range(size)]


def _ellipse(mask: list[list[bool]], cx: int, cy: int, rx: int, ry: int) -> None:
    for y in range(max(0, cy - ry), min(len(mask), cy + ry + 1)):
        for x in range(max(0, cx - rx), min(len(mask[0]), cx + rx + 1)):
            if ((x - cx) / max(1, rx)) ** 2 + ((y - cy) / max(1, ry)) ** 2 <= 1:
                mask[y][x] = True


def _line(mask: list[list[bool]], x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
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


def _archetype_mask(archetype: str) -> tuple[list[list[bool]], list[list[bool]]]:
    mask = _empty()
    if archetype == "butterfly":
        _ellipse(mask, 21, 24, 11, 13)
        _ellipse(mask, 43, 24, 11, 13)
        _ellipse(mask, 32, 30, 3, 15)
        detail_points = _line(mask, 30, 15, 25, 8) + _line(mask, 34, 15, 39, 8)
    elif archetype == "bird":
        _ellipse(mask, 30, 32, 14, 9)
        _ellipse(mask, 42, 24, 7, 7)
        _line(mask, 16, 33, 8, 28)
        detail_points = _line(mask, 48, 24, 56, 24) + _line(mask, 28, 40, 26, 50)
    elif archetype == "flower":
        _line(mask, 32, 34, 32, 57)
        _ellipse(mask, 32, 27, 5, 5)
        for cx, cy in ((32, 17), (42, 27), (32, 37), (22, 27), (39, 20), (25, 20)):
            _ellipse(mask, cx, cy, 5, 5)
        detail_points = _line(mask, 32, 43, 24, 39)
    elif archetype == "tree_branch":
        _line(mask, 32, 57, 32, 17)
        _line(mask, 32, 34, 14, 18)
        _line(mask, 32, 29, 51, 14)
        for cx, cy in ((13, 14), (20, 20), (52, 12), (44, 20)):
            _ellipse(mask, cx, cy, 5, 4)
        detail_points = _line(mask, 32, 34, 40, 39)
    elif archetype == "fish":
        _ellipse(mask, 29, 31, 15, 9)
        _line(mask, 43, 31, 55, 20)
        _line(mask, 43, 31, 55, 42)
        detail_points = _line(mask, 21, 27, 22, 27)
    elif archetype == "biped":
        _ellipse(mask, 32, 13, 7, 7)
        _line(mask, 32, 20, 32, 39)
        _line(mask, 32, 27, 21, 36)
        _line(mask, 32, 27, 43, 36)
        _line(mask, 32, 39, 24, 54)
        _line(mask, 32, 39, 40, 54)
        detail_points = _line(mask, 28, 12, 29, 12)
    elif archetype == "rigid":
        for y in range(20, 39):
            for x in range(15, 50):
                mask[y][x] = True
        _ellipse(mask, 21, 41, 6, 6)
        _ellipse(mask, 44, 41, 6, 6)
        detail_points = _line(mask, 32, 20, 32, 12)
    elif archetype == "generic_organic":
        _ellipse(mask, 31, 31, 15, 13)
        _ellipse(mask, 20, 22, 7, 8)
        detail_points = _line(mask, 42, 28, 53, 21) + _line(mask, 43, 35, 54, 41)
    else:
        _ellipse(mask, 25, 27, 10, 12)
        _ellipse(mask, 38, 35, 11, 8)
        _ellipse(mask, 40, 20, 4, 5)
        detail_points = _line(mask, 25, 39, 18, 48)
    details = _empty()
    for x, y in detail_points:
        details[y][x] = True
    return mask, details


@pytest.mark.parametrize(
    "archetype",
    (
        "butterfly",
        "bird",
        "flower",
        "tree_branch",
        "fish",
        "biped",
        "rigid",
        "generic_organic",
        "unknown",
    ),
)
def test_pixel_metrics_capture_region_boundary_and_thin_detail_errors(archetype: str) -> None:
    reference, detail = _archetype_mask(archetype)
    baseline = [row[:] for row in reference]
    for y in range(54, 60):
        for x in range(54, 60):
            baseline[y][x] = True  # synthetic wrong-object inclusion
    chosen = [row[:] for row in reference]
    detail_points = [(x, y) for y, row in enumerate(detail) for x, value in enumerate(row) if value]
    for x, y in detail_points[-max(1, len(detail_points) // 3):]:
        chosen[y][x] = False  # bounded candidate omits part of a thin feature

    baseline_metrics = score_mask(reference, baseline, thin_details=detail)
    chosen_metrics = score_mask(reference, chosen, thin_details=detail)
    assert chosen_metrics.iou > baseline_metrics.iou
    assert chosen_metrics.boundary_f1 > baseline_metrics.boundary_f1
    assert chosen_metrics.thin_detail_recall is not None
    assert 0.0 <= chosen_metrics.thin_detail_recall < 1.0
    assert baseline_metrics.false_inclusion_fraction > chosen_metrics.false_inclusion_fraction


def test_parent_part_containment_is_measured_separately() -> None:
    parent = _empty(5)
    part = _empty(5)
    for y in range(1, 4):
        for x in range(1, 4):
            parent[y][x] = True
    part[1][1] = True
    part[2][2] = True
    part[4][4] = True

    assert part_parent_consistency(parent, (part,)) == pytest.approx(2 / 3)


def test_metrics_reject_mismatched_or_ragged_masks() -> None:
    with pytest.raises(ValueError, match="dimensions differ"):
        score_mask(_empty(), _empty(4))
    with pytest.raises(ValueError, match="rectangular"):
        score_mask([[True], [True, False]], [[True], [True, False]])
