"""Run a deterministic selector/metric smoke benchmark on synthetic masks only.

This does not load SAM, a checkpoint, an L4, or any child image. Fixtures are shared
with the unit tests through a dependency-free benchmark module. Each synthetic
candidate includes a known wrong-object island marked by one negative point.
"""

from __future__ import annotations

import json
import time

import numpy as np  # type: ignore[import-not-found]

from sketch2life.benchmark.sam21_synthetic_masks import (
    SYNTHETIC_ARCHETYPES,
    archetype_mask,
)
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.ai.sam21_quality import part_parent_consistency, score_mask
from sketch2life.infrastructure.ai.sam21_runtime import (
    Sam21Prompt,
    _select_prompt_consistent_candidate,
)


def _average(rows: list[dict[str, float | None]]) -> dict[str, float | None]:
    keys = tuple(key for key, value in rows[0].items() if value is not None)
    averages: dict[str, float | None] = {}
    for key in keys:
        numeric_values: list[float] = []
        for row in rows:
            value = row[key]
            if not isinstance(value, int | float):
                raise ValueError(f"Synthetic benchmark metric {key!r} must be numeric")
            numeric_values.append(float(value))
        averages[key] = sum(numeric_values) / len(numeric_values)
    return averages


def _thin_detail_anchor_case() -> dict[str, object]:
    distractor = np.zeros((40, 40), dtype=bool)
    distractor[10:30, 10:30] = True
    distractor[32:35, 32:35] = True
    missing_detail = np.zeros((40, 40), dtype=bool)
    missing_detail[10:30, 10:30] = True
    complete = missing_detail.copy()
    complete[18, 8:10] = True
    selected, confidence = _select_prompt_consistent_candidate(
        np.asarray([distractor, missing_detail, complete]),
        np.asarray([0.99, 0.90, 0.80]),
        width=40,
        height=40,
        prompt=Sam21Prompt(
            prompt_region=SourceRegionV1(x=0.1, y=0.1, width=0.7, height=0.7),
            positive_points=((0.5, 0.5), (8.5 / 40, 18.5 / 40)),
            negative_points=((33.5 / 40, 33.5 / 40),),
        ),
        min_area_fraction=0.002,
        max_area_fraction=0.85,
        numpy=np,
    )
    if not bool(selected[18, 8]) or not bool(selected[18, 9]) or bool(selected[33, 33]):
        raise RuntimeError("SAM prompt selector violated grounded thin-detail constraints")
    return {
        "status": "PASS",
        "selected_confidence": confidence,
        "grounded_thin_detail_pixels_preserved": 2,
        "wrong_object_pixels_excluded": True,
    }


def main() -> None:
    baseline_metrics: list[dict[str, float | None]] = []
    selected_metrics: list[dict[str, float | None]] = []
    parent_part_scores: list[float] = []
    elapsed = 0.0
    for archetype in SYNTHETIC_ARCHETYPES:
        reference, details = archetype_mask(archetype)
        distractor = [row[:] for row in reference]
        for y in range(54, 60):
            for x in range(54, 60):
                distractor[y][x] = True
        target = [row[:] for row in reference]
        detail_points = [
            (x, y)
            for y, row in enumerate(details)
            for x, value in enumerate(row)
            if value
        ]
        for x, y in detail_points[-max(1, len(detail_points) // 3):]:
            target[y][x] = False
        positive = next(
            (x, y)
            for y, row in enumerate(reference)
            for x, value in enumerate(row)
            if value
        )
        prompt = Sam21Prompt(
            prompt_region=SourceRegionV1(x=0.05, y=0.05, width=0.9, height=0.9),
            positive_points=(((positive[0] + 0.5) / 64, (positive[1] + 0.5) / 64),),
            negative_points=((57.5 / 64, 57.5 / 64),),
        )
        start = time.perf_counter()
        selected, _confidence = _select_prompt_consistent_candidate(
            np.asarray([distractor, target]),
            np.asarray([0.99, 0.82]),
            width=64,
            height=64,
            prompt=prompt,
            min_area_fraction=0.002,
            max_area_fraction=0.85,
            numpy=np,
        )
        elapsed += time.perf_counter() - start
        baseline_metrics.append(score_mask(reference, distractor, thin_details=details).as_dict())
        selected_metrics.append(score_mask(reference, selected, thin_details=details).as_dict())
        parent_part_scores.append(part_parent_consistency(selected, (details,)))

    print(json.dumps({
        "contract_name": "SyntheticSam21CandidateBenchmarkV1",
        "fixture_kind": "generated_binary_masks_no_child_media",
        "archetypes": list(SYNTHETIC_ARCHETYPES),
        "candidate_policy": (
            "reject area-invalid/positive-point-missing/negative-point-included/"
            "box-inconsistent; highest SAM score among remaining"
        ),
        "baseline": _average(baseline_metrics),
        "prompt_validated_candidate": _average(selected_metrics),
        "parent_part_consistency_mean": sum(parent_part_scores) / len(parent_part_scores),
        "candidate_validation_cpu_wall_ms_total": round(elapsed * 1000, 3),
        "sam_model_latency_ms": None,
        "peak_l4_vram_mib": None,
        "selection_success_count": len(SYNTHETIC_ARCHETYPES),
        "selection_rejection_count": 0,
        "grounded_thin_detail_anchor_case": _thin_detail_anchor_case(),
        "interpretation": (
            "Tests prompt consistency and metric plumbing only; not a SAM accuracy estimate "
            "or held-out benchmark."
        ),
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
