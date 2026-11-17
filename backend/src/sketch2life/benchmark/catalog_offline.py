"""Deterministic offline evaluator for the curated catalog revision.

This evaluator deliberately starts after scene understanding. It validates
catalog and matcher behavior from a fixed, provider-free scene corpus; it
does not inject a recommendation or call a model.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from sketch2life.application.services.scene_understanding import (
    SceneCandidateV2Input,
    build_confirmed_scene_understanding,
)
from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    ConfirmedSceneUnderstandingV2,
)
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    ActivitySemanticCatalogV2,
    load_activity_semantic_catalog_v2,
)

_MATCH_PRIORITY = {
    "PERSONALIZED_EXACT": 4,
    "PERSONALIZED_ALIAS": 3,
    "PERSONALIZED_CONCEPT": 2,
}


def _load_corpus(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("contract_name") != "CatalogOfflineSceneCorpusV1":
        raise ValueError("offline corpus contract name is invalid")
    scenes = document.get("scenes")
    if not isinstance(scenes, list) or not 100 <= len(scenes) <= 300:
        raise ValueError("offline corpus must contain 100 to 300 scenes")
    return [scene for scene in scenes if isinstance(scene, dict)]


def _scene_from_case(case: dict[str, Any]) -> ConfirmedSceneUnderstandingV2:
    label = str(case["label_vi"])
    transcript = str(case["transcript_vi"])
    return build_confirmed_scene_understanding(
        scene_understanding_id=str(case["scene_id"]),
        image_artifact_ref=f"offline/{case['scene_id']}.png",
        image_sha256="a" * 64,
        audio_artifact_ref=f"offline/{case['scene_id']}.wav",
        audio_sha256="b" * 64,
        candidates=(
            SceneCandidateV2Input(
                label_vi=label,
                kind="subject",
                confidence=0.92,
                claim_ids=(f"{case['scene_id']}:vlm",),
                source_kind="VLM",
            ),
        ),
        asr_transcript_vi=transcript,
    )


def _rank_key(match: Any) -> tuple[float, float, int, int]:
    return (
        match.child_interest_alignment,
        match.overall_personalization_score,
        _MATCH_PRIORITY.get(match.match_mode, 0),
        match.semantic_relevance,
    )


def _candidates(
    catalog: ActivitySemanticCatalogV2,
    scene: Any,
    age_band: str,
) -> list[tuple[Any, Any]]:
    results: list[tuple[Any, Any]] = []
    for profile in catalog.profiles:
        if profile.age_band != age_band:
            continue
        match = catalog.match_scene(scene, profile)
        if match is not None and match.match_mode != "AGE_BASELINE_FALLBACK":
            results.append((profile, match))
    return results


def _select(candidates: list[tuple[Any, Any]], seed: int) -> tuple[Any, Any]:
    if not candidates:
        raise ValueError("cannot select from empty candidate list")
    strongest_score = max(_rank_key(match) for _, match in candidates)
    strongest = sorted(
        (
            item
            for item in candidates
            if _rank_key(item[1]) == strongest_score
        ),
        key=lambda item: (item[1].activity_family_id, item[1].activity_id),
    )
    return random.Random(seed).choice(strongest)


def evaluate_catalog_offline(
    root: Path,
    corpus_path: Path,
) -> dict[str, Any]:
    cases = _load_corpus(corpus_path)
    catalog = load_activity_semantic_catalog_v2(root, include_expansion=True)
    selected_ids: list[str] = []
    selected_families: list[str] = []
    candidate_counts: list[int] = []
    no_match: list[str] = []
    concept_mismatches: list[str] = []
    objective_mismatches: list[str] = []
    same_seed_failures: list[str] = []
    different_seed_changes = 0
    butterfly_counts: dict[str, list[int]] = {}

    for case in cases:
        scene = _scene_from_case(case)
        candidates = _candidates(catalog, scene, str(case["age_band"]))
        candidate_counts.append(len(candidates))
        expected_concept = str(case["expected_concept_id"])
        if expected_concept == "ANIMAL_BUTTERFLY":
            butterfly_counts.setdefault(str(case["age_band"]), []).append(len(candidates))
        if not candidates:
            no_match.append(str(case["scene_id"]))
            continue
        profile, match = _select(candidates, int(case["seed"]))
        selected_ids.append(profile.activity_id)
        selected_families.append(profile.activity_family_id)
        if expected_concept not in match.matched_concept_ids:
            concept_mismatches.append(str(case["scene_id"]))
        if (
            match.objective_activity_alignment != 1.0
            or match.selected_objective_id != profile.primary_objective_id
        ):
            objective_mismatches.append(str(case["scene_id"]))
        same_seed = _select(candidates, int(case["seed"]))[0].activity_id
        if same_seed != profile.activity_id:
            same_seed_failures.append(str(case["scene_id"]))
        if len(candidates) > 1:
            other = _select(candidates, int(case["seed"]) + 1)[0].activity_id
            different_seed_changes += other != profile.activity_id

    activity_counts = Counter(selected_ids)
    family_counts = Counter(selected_families)
    return {
        "contract_name": "CatalogOfflineEvaluationReportV1",
        "contract_version": "1.0",
        "corpus_ref": corpus_path.relative_to(root).as_posix(),
        "scene_count": len(cases),
        "catalog_revision": catalog.profiles[-1].catalog_revision,
        "selectable_profile_count": len(catalog.profiles),
        "no_match_count": len(no_match),
        "no_match_scene_ids": no_match,
        "objective_mismatch_count": len(objective_mismatches),
        "objective_mismatch_scene_ids": objective_mismatches,
        "concept_mismatch_count": len(concept_mismatches),
        "concept_mismatch_scene_ids": concept_mismatches,
        "same_seed_reproducibility_failures": same_seed_failures,
        "different_seed_changed_selection_count": different_seed_changes,
        "candidate_count_min": min(candidate_counts),
        "candidate_count_mean": round(sum(candidate_counts) / len(candidate_counts), 2),
        "top_activity_share": round(
            max(activity_counts.values(), default=0) / max(len(selected_ids), 1), 4
        ),
        "top_family_share": round(
            max(family_counts.values(), default=0) / max(len(selected_families), 1), 4
        ),
        "distinct_activity_count": len(activity_counts),
        "distinct_family_count": len(family_counts),
        "butterfly_candidate_counts_by_age": {
            age_band: {
                "min": min(counts),
                "max": max(counts),
                "meets_three_candidate_target": min(counts) >= 3,
            }
            for age_band, counts in sorted(butterfly_counts.items())
        },
        "status": (
            "PASS"
            if not no_match
            and not concept_mismatches
            and not objective_mismatches
            and not same_seed_failures
            and all(
                item["meets_three_candidate_target"]
                for item in (
                    {
                        "meets_three_candidate_target": min(counts) >= 3
                    }
                    for counts in butterfly_counts.values()
                )
            )
            else "FAIL"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline catalog validation")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--corpus",
        default="features/FEAT-023-catalog-contract-hardening/fixtures/offline-corpus.v1.json",
    )
    parser.add_argument(
        "--output",
        default="features/FEAT-023-catalog-contract-hardening/evidence/metrics/offline-report.json",
    )
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    report = evaluate_catalog_offline(root, root / args.corpus)
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "scene_count": report["scene_count"]}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
