"""Print measured Montessori catalog coverage for FEAT-018 profile dimensions."""

from __future__ import annotations

import json
from pathlib import Path

from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    semantic = load_activity_semantic_catalog_v2(ROOT, include_expansion=True)
    templates = load_p1_template_library(ROOT, include_mvp=True, include_expansion=True)
    reviewed = tuple(
        item for item in semantic.profiles if item.review_status not in {"BLOCKED", "DEPRECATED"}
    )
    objectives = {objective for item in reviewed for objective in (
        item.primary_objective_id, *item.secondary_objective_ids
    )}
    concepts = {concept for item in reviewed for concept in (
        *item.concept_ids, *item.parent_concept_ids
    )}
    template_rows = templates.templates
    output = {
        "contract_name": "ChildProfileCatalogCoverageAuditV1",
        "catalog_revision": "catalog-2026-09",
        "semantic_profile_count": len(semantic.profiles),
        "review_eligible_profile_count": len(reviewed),
        "unique_scene_concepts": len(concepts),
        "unique_learning_objectives": len(objectives),
        "interest_and_dislike_coverage": {
            "profiles_with_scene_concepts": sum(bool(item.concept_ids) for item in reviewed),
            "explicit_child_preference_history_in_catalog": 0,
        },
        "adult_progress_coverage": {
            "profiles_with_objective_metadata": sum(bool(item.primary_objective_id) for item in reviewed),
            "historical_child_progress_records_in_catalog": 0,
            "templates_with_prerequisite_activity_ids": sum(bool(item.prerequisite_activity_ids) for item in template_rows),
        },
        "readiness_coverage": {
            "templates_with_readiness_ids": sum(bool(item.readiness_ids) for item in template_rows),
            "templates_total": len(template_rows),
        },
        "material_coverage": {
            "templates_with_material_options": sum(bool(item.material_option_ids) for item in template_rows),
            "templates_total": len(template_rows),
            "material_registry_options": len(json.loads(
                (ROOT / "data/activity-catalog/golden/v1/material-registry.v1.json").read_text(encoding="utf-8")
            )["options"]),
        },
        "supervision_coverage": {
            "templates_with_minimum_supervision": sum(bool(item.minimum_supervision) for item in template_rows),
            "templates_total": len(template_rows),
        },
        "learning_support_coverage": {
            "explicit_support_tags_in_semantic_profiles": 0,
            "v1_implementation": "bounded crosswalk from reviewed interaction mode/objective; low-distraction support is not inferred",
        },
        "catalog_expansion_decision": "No entries added: current catalog has broad reviewed concept/objective/readiness/material/supervision metadata; per-child history is runtime input, not a catalog row.",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
