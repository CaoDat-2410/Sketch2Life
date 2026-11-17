"""Emit a row-level, metadata-only audit for FEAT-034's active P1 catalog."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from sketch2life.infrastructure.catalog import activity_semantics_v2
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library
from sketch2life.infrastructure.catalog.workflow_metadata import FileWorkflowCatalogMetadata


def build_report(root: Path) -> dict[str, Any]:
    catalog = load_activity_semantic_catalog_v2(root, include_expansion=True)
    library = load_p1_template_library(root, include_mvp=True, include_expansion=True)
    metadata = FileWorkflowCatalogMetadata(root)
    templates = {item.activity_ref.id: item for item in library.templates}

    semantic_overrides_path = (
        root / "data/activity-catalog/curated/v2/semantic-mapping-overrides.v1.json"
    )
    semantic_overrides = json.loads(semantic_overrides_path.read_text(encoding="utf-8"))
    family_overrides = {
        item["family_id"]: item for item in semantic_overrides.get("families", [])
    }
    profiles = tuple(catalog.profiles)
    if len(profiles) != 300 or len({item.activity_id for item in profiles}) != 300:
        raise ValueError("FEAT-034 audit requires 300 unique active semantic profiles")

    rows: list[dict[str, Any]] = []
    for profile in sorted(profiles, key=lambda item: item.activity_id):
        template = templates.get(profile.activity_id)
        card = metadata.recommendation_display(profile.activity_id, profile.activity_version)
        family_override = family_overrides.get(profile.activity_family_id)
        activity_override = profile.activity_id in activity_semantics_v2._ACTIVITY_CONCEPT_OVERRIDES
        if family_override or activity_override:
            disposition = "CORRECT"
            rationale = (
                family_override["rationale"]
                if family_override
                else (
                    "An explicit activity-level concept override replaces "
                    "broad/string-derived tags."
                )
            )
        else:
            disposition = "NEEDS_REVIEW"
            rationale = (
                "Automated checks verify shape and renderability, but no qualified Montessori "
                "review sign-off is recorded for this exact topic/objective/action mapping."
            )

        rows.append(
            {
                "activity_id": profile.activity_id,
                "activity_version": profile.activity_version,
                "activity_family_id": profile.activity_family_id,
                "variant_id": profile.variant_id,
                "age_band": profile.age_band,
                "catalog_revision": profile.catalog_revision,
                "review_status": profile.review_status,
                "pedagogical_alignment_status": profile.pedagogical_alignment_status,
                "concept_ids": list(profile.concept_ids),
                "parent_concept_ids": list(profile.parent_concept_ids),
                "direct_observation_concept_ids": list(
                    profile.direct_observation_concept_ids
                ),
                "exact_phrases_vi": list(profile.exact_phrases_vi),
                "aliases_vi": list(profile.aliases_vi),
                "negative_phrases_vi": list(profile.negative_phrases_vi),
                "primary_objective_id": profile.primary_objective_id,
                "primary_objective_title_vi": library.objective_titles_vi.get(
                    profile.primary_objective_id
                ),
                "secondary_objective_ids": list(profile.secondary_objective_ids),
                "secondary_objective_titles_vi": [
                    library.objective_titles_vi.get(item)
                    for item in profile.secondary_objective_ids
                ],
                "title_vi": card["title_vi"] if card else None,
                "action_summary_vi": card["summary_vi"] if card else None,
                "duration_minutes": card["duration_minutes"] if card else None,
                "material_option_ids": list(template.material_option_ids) if template else [],
                "material_option_groups": [
                    list(group) for group in template.material_option_groups
                ] if template else [],
                "material_labels_vi": list(
                    metadata.material_labels_for_ids(template.material_option_ids).values()
                ) if template else [],
                "minimum_supervision": template.minimum_supervision if template else None,
                "policy_constraints": list(template.policy_constraints) if template else [],
                "safety_rule_ids": list(template.safety_rule_ids) if template else [],
                "adult_steps_vi": list(template.steps_vi) if template else [],
                "displayable": card is not None,
                "provenance_source": profile.provenance_source,
                "provenance_sha256": profile.provenance_sha256,
                "disposition": disposition,
                "rationale": rationale,
            }
        )

    concept_ids = sorted(
        {
            concept_id
            for profile in profiles
            for concept_id in (*profile.concept_ids, *profile.parent_concept_ids)
        }
    )
    age_bands = ("0-3", "3-6", "6-9", "9-12")
    coverage: list[dict[str, Any]] = []
    for concept_id in concept_ids:
        for age_band in age_bands:
            members = [
                profile
                for profile in profiles
                if profile.age_band == age_band
                and concept_id
                in (*profile.concept_ids, *profile.parent_concept_ids)
            ]
            direct = [
                profile
                for profile in members
                if concept_id in profile.direct_observation_concept_ids
            ]
            related = [profile for profile in members if profile not in direct]
            displayable = [
                profile
                for profile in members
                if metadata.recommendation_display(
                    profile.activity_id, profile.activity_version
                )
                is not None
            ]
            coverage.append(
                {
                    "concept_id": concept_id,
                    "age_band": age_band,
                    "direct_match_count": len(direct),
                    "related_match_count": len(related),
                    "displayable_match_count": len(displayable),
                    "non_displayable_activity_ids": [
                        profile.activity_id
                        for profile in members
                        if profile not in displayable
                    ],
                    "supervision_counts": dict(
                        Counter(
                            templates[item.activity_id].minimum_supervision
                            for item in members
                            if item.activity_id in templates
                        )
                    ),
                    "activities_missing_safety_metadata": [
                        item.activity_id
                        for item in members
                        if item.activity_id not in templates
                        or not templates[item.activity_id].safety_rule_ids
                    ],
                }
            )

    dispositions = Counter(row["disposition"] for row in rows)
    missing_cards = [row["activity_id"] for row in rows if not row["displayable"]]
    return {
        "report_id": "FEAT-034-CATALOG-TOPIC-MAPPING-AUDIT-V1",
        "generated_from": "runtime-loaded P1 semantic profiles, workflow cards, and templates",
        "catalog_revision": semantic_overrides["catalog_revision"],
        "row_count": len(rows),
        "unique_activity_count": len({row["activity_id"] for row in rows}),
        "renderable_card_count": len(rows) - len(missing_cards),
        "missing_card_activity_ids": missing_cards,
        "disposition_counts": dict(dispositions),
        "topic_concept_count": len(concept_ids),
        "age_bands": list(age_bands),
        "coverage_matrix": coverage,
        "review_limitations": [
            (
                "CORRECT denotes explicit code-level mapping corrections, "
                "not pedagogical certification."
            ),
            "NEEDS_REVIEW rows require qualified Montessori review before production approval.",
            "Coverage counts are structural; a present tag is not proof of pedagogical relevance.",
        ],
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_report(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"rows={report['row_count']} cards={report['renderable_card_count']} "
        f"dispositions={report['disposition_counts']} concepts={report['topic_concept_count']}"
    )


if __name__ == "__main__":
    main()
