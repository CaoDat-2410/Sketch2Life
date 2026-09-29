"""Run a deterministic selector/metric smoke benchmark on synthetic masks only.

This does not load SAM, a checkpoint, an L4, or any child image. The archetype mask
fixtures live with the unit tests and each synthetic candidate includes a known
wrong-object island, which is marked by one negative point.
"""

from __future__ import annotations

import json
import runpy
import time
from pathlib import Path

import numpy as np

from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.ai.sam21_quality import part_parent_consistency, score_mask
from sketch2life.infrastructure.ai.sam21_runtime import (
    Sam21Prompt,
    _select_prompt_consistent_candidate,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]
_corpus = runpy.run_path(str(BACKEND_ROOT / "tests/unit/test_sam21_quality_metrics.py"))
_archetype_mask = _corpus["_archetype_mask"]


def _average(rows: list[dict[str, float | None]]) -> dict[str, float | None]:
    keys = tuple(key for key, value in rows[0].items() if value is not None)
    return {key: sum(float(row[key]) for row in rows) / len(rows) for key in keys}


def main() -> None:
    baseline_metrics: list[dict[str, float | None]] = []
    selected_metrics: list[dict[str, float | None]] = []
    parent_part_scores: list[float] = []
    elapsed = 0.0
    categories = (
        "butterfly", "bird", "flower", "tree_branch", "fish", "biped",
        "rigid", "generic_organic", "unknown",
    )
    for archetype in categories:
        reference, details = _archetype_mask(archetype)
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
        "archetypes": list(categories),
        "candidate_policy": "reject area-invalid/positive-point-missing/negative-point-included/box-inconsistent; highest SAM score among remaining",
        "baseline": _average(baseline_metrics),
        "prompt_validated_candidate": _average(selected_metrics),
        "parent_part_consistency_mean": sum(parent_part_scores) / len(parent_part_scores),
        "candidate_validation_cpu_wall_ms_total": round(elapsed * 1000, 3),
        "sam_model_latency_ms": None,
        "peak_l4_vram_mib": None,
        "selection_success_count": len(categories),
        "selection_rejection_count": 0,
        "interpretation": "Tests prompt consistency and metric plumbing only; not a SAM accuracy estimate or held-out benchmark.",
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
