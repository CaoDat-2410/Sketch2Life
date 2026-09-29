"""Small, dependency-free mask metrics for synthetic/held-out SAM2 evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

Mask = Sequence[Sequence[bool]]


@dataclass(frozen=True, slots=True)
class MaskQualityMetrics:
    iou: float
    dice: float
    boundary_f1: float
    thin_detail_recall: float | None
    false_inclusion_fraction: float
    false_exclusion_fraction: float

    def as_dict(self) -> dict[str, float | None]:
        return asdict(self)


def score_mask(
    reference: Mask,
    candidate: Mask,
    *,
    thin_details: Mask | None = None,
    boundary_tolerance_px: int = 1,
) -> MaskQualityMetrics:
    """Score a binary candidate against pixel truth, including thin-detail recall."""
    height, width = _validate_pair(reference, candidate)
    if boundary_tolerance_px < 0:
        raise ValueError("boundary tolerance must be non-negative")
    if thin_details is not None:
        detail_height, detail_width = _dimensions(thin_details)
        if (detail_height, detail_width) != (height, width):
            raise ValueError("thin-detail mask dimensions differ from reference")

    true_positive = false_positive = false_negative = candidate_count = reference_count = 0
    for y in range(height):
        for x in range(width):
            expected = bool(reference[y][x])
            actual = bool(candidate[y][x])
            reference_count += expected
            candidate_count += actual
            true_positive += expected and actual
            false_positive += actual and not expected
            false_negative += expected and not actual

    union = true_positive + false_positive + false_negative
    dice_denominator = 2 * true_positive + false_positive + false_negative
    reference_boundary = _boundary(reference)
    candidate_boundary = _boundary(candidate)
    precision = _boundary_match_fraction(
        candidate_boundary, reference_boundary, boundary_tolerance_px
    )
    recall = _boundary_match_fraction(
        reference_boundary, candidate_boundary, boundary_tolerance_px
    )
    boundary_f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    detail_recall = None
    if thin_details is not None:
        detail_total = sum(bool(value) for row in thin_details for value in row)
        detail_hit = sum(
            bool(thin_details[y][x]) and bool(candidate[y][x])
            for y in range(height)
            for x in range(width)
        )
        detail_recall = 1.0 if detail_total == 0 else detail_hit / detail_total

    return MaskQualityMetrics(
        iou=1.0 if union == 0 else true_positive / union,
        dice=1.0 if dice_denominator == 0 else 2 * true_positive / dice_denominator,
        boundary_f1=boundary_f1,
        thin_detail_recall=detail_recall,
        false_inclusion_fraction=0.0 if candidate_count == 0 else false_positive / candidate_count,
        false_exclusion_fraction=0.0 if reference_count == 0 else false_negative / reference_count,
    )


def part_parent_consistency(parent: Mask, parts: Sequence[Mask]) -> float:
    """Return the fraction of all part pixels contained by their parent mask."""
    if not parts:
        return 1.0
    height, width = _validate_pair(parent, parts[0])
    part_total = inside_parent = 0
    for part in parts:
        _validate_pair(parent, part)
        for y in range(height):
            for x in range(width):
                if bool(part[y][x]):
                    part_total += 1
                    inside_parent += bool(parent[y][x])
    return 1.0 if part_total == 0 else inside_parent / part_total


def _dimensions(mask: Mask) -> tuple[int, int]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    if height == 0 or width == 0 or any(len(row) != width for row in mask):
        raise ValueError("mask must be a non-empty rectangular grid")
    return height, width


def _validate_pair(first: Mask, second: Mask) -> tuple[int, int]:
    dimensions = _dimensions(first)
    if _dimensions(second) != dimensions:
        raise ValueError("mask dimensions differ")
    return dimensions


def _boundary(mask: Mask) -> set[tuple[int, int]]:
    height, width = _dimensions(mask)
    result: set[tuple[int, int]] = set()
    for y in range(height):
        for x in range(width):
            if not bool(mask[y][x]):
                continue
            if any(
                next_x < 0
                or next_x >= width
                or next_y < 0
                or next_y >= height
                or not bool(mask[next_y][next_x])
                for next_x, next_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            ):
                result.add((x, y))
    return result


def _boundary_match_fraction(
    source: set[tuple[int, int]],
    target: set[tuple[int, int]],
    tolerance: int,
) -> float:
    if not source:
        return 1.0 if not target else 0.0
    hits = sum(
        any(
            (x + dx, y + dy) in target
            for dx in range(-tolerance, tolerance + 1)
            for dy in range(-tolerance, tolerance + 1)
        )
        for x, y in source
    )
    return hits / len(source)


__all__ = ["MaskQualityMetrics", "part_parent_consistency", "score_mask"]
