from __future__ import annotations

import pytest

from sketch2life.benchmark.sam21_synthetic_masks import (
    SYNTHETIC_ARCHETYPES,
    archetype_mask,
    empty_mask,
)
from sketch2life.infrastructure.ai.sam21_quality import (
    part_parent_consistency,
    score_mask,
)


@pytest.mark.parametrize(
    "archetype",
    SYNTHETIC_ARCHETYPES,
)
def test_pixel_metrics_capture_region_boundary_and_thin_detail_errors(archetype: str) -> None:
    reference, detail = archetype_mask(archetype)
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
    parent = empty_mask(5)
    part = empty_mask(5)
    for y in range(1, 4):
        for x in range(1, 4):
            parent[y][x] = True
    part[1][1] = True
    part[2][2] = True
    part[4][4] = True

    assert part_parent_consistency(parent, (part,)) == pytest.approx(2 / 3)


def test_metrics_reject_mismatched_or_ragged_masks() -> None:
    with pytest.raises(ValueError, match="dimensions differ"):
        score_mask(empty_mask(), empty_mask(4))
    with pytest.raises(ValueError, match="rectangular"):
        score_mask([[True], [True, False]], [[True], [True, False]])
