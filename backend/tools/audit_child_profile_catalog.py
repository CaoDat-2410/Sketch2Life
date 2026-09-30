"""Print measured Montessori catalog coverage for FEAT-018 profile dimensions."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path

from sketch2life.contracts.schemas.p1_experience import ActivityTemplateV1
from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    SemanticActivityProfileV2,
)
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library

ROOT = Path(__file__).resolve().parents[2]

# Audit-only mapping from FEAT-022 Decision 2. It does not add demand tiers to
# catalog records or affect the runtime matcher.
_TIER_A_CONCEPTS = frozenset(
    {
        "ANIMAL",
        "ANIMAL_BUTTERFLY",
        "ANIMAL_GENERIC",
        "ANIMAL_MOVEMENT",
        "COLOR_BASIC",
        "COUNTING_DATA",
        "COUNTING_NUMBER",
        "MOVEMENT_COORDINATION",
        "PEOPLE_FAMILY",
        "PLANT_FLOWER",
        "PLANT_STRUCTURE",
        "SENSORIAL_COLOR",
        "SHAPE_GEOMETRY",
    }
)
_TIER_B_CONCEPTS = frozenset(
    {
        "MOON_PHASE",
        "NATURE_OBSERVATION",
        "SOUND_MUSIC",
        "SUN_LIGHT",
        "VEHICLE_TRANSPORT",
        "WATER_CYCLE",
        "WATER_NATURE",
        "WEATHER_NATURE",
    }
)
_TIER_MINIMUMS = {"A": 5, "B": 3, "C": 2}
_AGE_MONTHS_BY_BAND = {"0-3": 18, "3-6": 54, "6-9": 90, "9-12": 132}

# FEAT-022 names these demand families; IDs not present in the current catalog
# remain visible as zero-coverage rows instead of disappearing from the audit.
_DEMAND_FAMILY_CONCEPTS = {
    "animal": frozenset({"ANIMAL", "ANIMAL_BUTTERFLY", "ANIMAL_GENERIC", "ANIMAL_MOVEMENT"}),
    "plant/flower": frozenset({"PLANT_FLOWER", "PLANT_STRUCTURE"}),
    "family/person": frozenset({"PEOPLE_FAMILY"}),
    "color": frozenset({"COLOR_BASIC", "SENSORIAL_COLOR"}),
    "shape": frozenset({"SHAPE_GEOMETRY"}),
    "movement": frozenset({"MOVEMENT_COORDINATION", "ANIMAL_MOVEMENT"}),
    "number": frozenset({"COUNTING_DATA", "COUNTING_NUMBER"}),
    "vehicle": frozenset({"VEHICLE_TRANSPORT"}),
    "house/home": frozenset(),
    "weather": frozenset({"WEATHER_NATURE"}),
    "sun/moon/space": frozenset({"SUN_LIGHT", "MOON_PHASE"}),
    "water": frozenset({"WATER_CYCLE", "WATER_NATURE"}),
    "sound/music": frozenset({"SOUND_MUSIC"}),
    "nature": frozenset({"NATURE_OBSERVATION"}),
    "language/print": frozenset({"LANGUAGE_PRINT"}),
    "practical life": frozenset({"PRACTICAL_LIFE"}),
    "science": frozenset({"SCIENCE_NATURE", "SCIENCE_OBSERVATION"}),
}
_TIER_A_DEMAND_FAMILIES = frozenset(
    {"animal", "plant/flower", "family/person", "color", "shape", "movement", "number"}
)
_TIER_B_DEMAND_FAMILIES = frozenset(
    {"vehicle", "house/home", "weather", "sun/moon/space", "water", "sound/music", "nature"}
)


def _demand_tier(concept_id: str) -> str:
    if concept_id in _TIER_A_CONCEPTS:
        return "A"
    if concept_id in _TIER_B_CONCEPTS:
        return "B"
    return "C"


def _activity_family_id(profile: SemanticActivityProfileV2) -> str:
    family_id = profile.activity_family_id.strip()
    activity_id = profile.activity_id
    return family_id or f"FAMILY-{activity_id}"


def _demand_families_for_concept(concept_id: str) -> tuple[str, ...]:
    return tuple(
        family
        for family, concept_ids in _DEMAND_FAMILY_CONCEPTS.items()
        if concept_id in concept_ids
    )


def _demand_family_tier(family: str) -> str:
    if family in _TIER_A_DEMAND_FAMILIES:
        return "A"
    if family in _TIER_B_DEMAND_FAMILIES:
        return "B"
    return "C"


def _int_field(row: dict[str, object], field: str) -> int:
    value = row[field]
    if not isinstance(value, int):
        raise TypeError(f"Catalog audit field {field!r} must be an integer")
    return value


def _production_approved_activity_ids(
    profiles: Iterable[SemanticActivityProfileV2],
    templates: Iterable[ActivityTemplateV1],
) -> set[str]:
    """Return activities approved in both the semantic and P1 template catalogs."""
    production_template_ids = {
        item.activity_ref.id
        for item in templates
        if item.review_status == "PRODUCTION_APPROVED" and item.production_eligible
    }
    return {
        item.activity_id
        for item in profiles
        if item.review_status == "PRODUCTION_APPROVED"
        and item.production_eligible
        and item.activity_id in production_template_ids
    }


def _has_no_authored_readiness_prerequisite(template: ActivityTemplateV1) -> bool:
    """Return true only when an authored template has no child-readiness criteria."""
    return template.readiness_metadata_status == "AUTHORED" and not template.readiness_ids


def _tier_age_summary(
    concept_age_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for tier, minimum in _TIER_MINIMUMS.items():
        for age_band in ("0-3", "3-6", "6-9", "9-12"):
            applicable = [
                row
                for row in concept_age_rows
                if row["demand_tier"] == tier
                and row["age_band"] == age_band
                and _int_field(row, "review_eligible_profiles") > 0
            ]
            output.append(
                {
                    "demand_tier": tier,
                    "age_band": age_band,
                    "minimum_safe_candidates": minimum,
                    "applicable_concept_slices": len(applicable),
                    "slices_meeting_minimum_after_static_gates": sum(
                        _int_field(row, "after_static_hard_gates_if_readiness_confirmed_candidates")
                        >= minimum
                        for row in applicable
                    ),
                    "slices_below_minimum_after_static_gates": sum(
                        _int_field(row, "after_static_hard_gates_if_readiness_confirmed_candidates")
                        < minimum
                        for row in applicable
                    ),
                    "empty_slices_after_static_gates": sum(
                        _int_field(
                            row,
                            "after_static_hard_gates_if_readiness_confirmed_candidates",
                        )
                        == 0
                        for row in applicable
                    ),
                    "surviving_activity_candidates": sum(
                        _int_field(row, "after_static_hard_gates_if_readiness_confirmed_candidates")
                        for row in applicable
                    ),
                    "surviving_activity_families": sum(
                        _int_field(row, "after_static_hard_gates_if_readiness_confirmed_families")
                        for row in applicable
                    ),
                    "family_count_note": (
                        "Sum across concept slices; a catalog activity family tagged to more than "
                        "one concept may be counted more than once."
                    ),
                    "candidate_count_note": (
                        "Sum across concept slices; one activity tagged to multiple concepts may "
                        "be counted more than once."
                    ),
                }
            )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for a JSON evidence copy; stdout is always emitted too.",
    )
    args = parser.parse_args()
    semantic = load_activity_semantic_catalog_v2(ROOT, include_expansion=True)
    templates = load_p1_template_library(ROOT, include_mvp=True, include_expansion=True)
    reviewed = tuple(
        item for item in semantic.profiles if item.review_status not in {"BLOCKED", "DEPRECATED"}
    )
    template_rows = templates.templates
    templates_by_activity = {item.activity_ref.id: item for item in template_rows}
    raw_concept_age: Counter[tuple[str, str]] = Counter()
    eligible_concept_age: Counter[tuple[str, str]] = Counter()
    unknown_readiness_concept_age: Counter[tuple[str, str]] = Counter()
    eligible_concept_candidates: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    eligible_concept_families: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    unknown_concept_families: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    raw_demand_family_age: Counter[tuple[str, str]] = Counter()
    eligible_demand_family_age: Counter[tuple[str, str]] = Counter()
    raw_demand_candidates: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    eligible_demand_candidates: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    eligible_demand_activity_families: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    raw_objective_age: Counter[tuple[str, str]] = Counter()
    eligible_objective_age: Counter[tuple[str, str]] = Counter()
    eligible_without_readiness_age: Counter[tuple[str, str]] = Counter()
    eligible_objective_candidates: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    eligible_objective_families: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    unknown_objective_families: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    missing_template_profile_count = 0
    eligible_profile_count = 0
    production_approved_static_gate_survivors = 0
    unknown_readiness_profile_count = 0
    production_approved_activity_ids = _production_approved_activity_ids(
        semantic.profiles, template_rows
    )
    for profile in reviewed:
        template = templates_by_activity.get(profile.activity_id)
        if template is None:
            missing_template_profile_count += 1
            continue
        age_months = _AGE_MONTHS_BY_BAND[profile.age_band]
        activity_family_id = _activity_family_id(profile)
        in_age_range = template.age_months_min <= age_months <= template.age_months_max
        has_authored_readiness = template.readiness_metadata_status == "AUTHORED"
        has_no_unobserved_history_prerequisite = not template.prerequisite_activity_ids
        has_material_and_safety_metadata = bool(
            template.material_option_ids and template.safety_rule_ids
        )
        ideal_adult_confirmed_eligible = (
            in_age_range
            and has_authored_readiness
            and has_no_unobserved_history_prerequisite
            and has_material_and_safety_metadata
        )
        readiness_unknown_eligible = (
            ideal_adult_confirmed_eligible
            and _has_no_authored_readiness_prerequisite(template)
        )
        if ideal_adult_confirmed_eligible:
            eligible_profile_count += 1
            if profile.activity_id in production_approved_activity_ids:
                production_approved_static_gate_survivors += 1
        if readiness_unknown_eligible:
            unknown_readiness_profile_count += 1
        profile_concepts = tuple(
            concept for concept in profile.concept_ids if not concept.startswith("ACTIVITY_")
        )
        profile_objectives = tuple(
            dict.fromkeys(
                (
                    profile.primary_objective_id,
                    *profile.secondary_objective_ids,
                )
            )
        )
        for concept in profile_concepts:
            raw_concept_age[(concept, profile.age_band)] += 1
            if ideal_adult_confirmed_eligible:
                eligible_concept_age[(concept, profile.age_band)] += 1
                eligible_concept_candidates[(concept, profile.age_band)].add(profile.activity_id)
                eligible_concept_families[(concept, profile.age_band)].add(activity_family_id)
            if readiness_unknown_eligible:
                unknown_readiness_concept_age[(concept, profile.age_band)] += 1
                unknown_concept_families[(concept, profile.age_band)].add(activity_family_id)
            for demand_family in _demand_families_for_concept(concept):
                raw_demand_family_age[(demand_family, profile.age_band)] += 1
                raw_demand_candidates[(demand_family, profile.age_band)].add(profile.activity_id)
                if ideal_adult_confirmed_eligible:
                    eligible_demand_family_age[(demand_family, profile.age_band)] += 1
                    eligible_demand_candidates[(demand_family, profile.age_band)].add(
                        profile.activity_id
                    )
                    eligible_demand_activity_families[(demand_family, profile.age_band)].add(
                        activity_family_id
                    )
        for objective in profile_objectives:
            raw_objective_age[(objective, profile.age_band)] += 1
            if ideal_adult_confirmed_eligible:
                eligible_objective_age[(objective, profile.age_band)] += 1
                eligible_objective_candidates[(objective, profile.age_band)].add(
                    profile.activity_id
                )
                eligible_objective_families[(objective, profile.age_band)].add(activity_family_id)
            if readiness_unknown_eligible:
                eligible_without_readiness_age[(objective, profile.age_band)] += 1
                unknown_objective_families[(objective, profile.age_band)].add(activity_family_id)

    all_concepts = sorted({concept for concept, _ in raw_concept_age})
    all_objectives = sorted({objective for objective, _ in raw_objective_age})
    bands = tuple(_AGE_MONTHS_BY_BAND)
    concept_age_matrix = [
        {
            "concept_id": concept,
            "demand_tier": _demand_tier(concept),
            "age_band": age_band,
            "review_eligible_profiles": raw_concept_age[(concept, age_band)],
            "after_static_hard_gates_if_readiness_confirmed": eligible_concept_age[
                (concept, age_band)
            ],
            "after_static_hard_gates_if_readiness_confirmed_candidates": len(
                eligible_concept_candidates[(concept, age_band)]
            ),
            "after_static_hard_gates_if_readiness_confirmed_families": len(
                eligible_concept_families[(concept, age_band)]
            ),
            "after_static_hard_gates_if_readiness_unknown": unknown_readiness_concept_age[
                (concept, age_band)
            ],
            "after_static_hard_gates_if_readiness_unknown_families": len(
                unknown_concept_families[(concept, age_band)]
            ),
        }
        for concept in all_concepts
        for age_band in bands
    ]
    objective_age_matrix = [
        {
            "objective_id": objective,
            "age_band": age_band,
            "review_eligible_profiles": raw_objective_age[(objective, age_band)],
            "after_static_hard_gates_if_readiness_confirmed": eligible_objective_age[
                (objective, age_band)
            ],
            "after_static_hard_gates_if_readiness_confirmed_candidates": len(
                eligible_objective_candidates[(objective, age_band)]
            ),
            "after_static_hard_gates_if_readiness_confirmed_families": len(
                eligible_objective_families[(objective, age_band)]
            ),
            "after_static_hard_gates_if_readiness_unknown": eligible_without_readiness_age[
                (objective, age_band)
            ],
            "after_static_hard_gates_if_readiness_unknown_families": len(
                unknown_objective_families[(objective, age_band)]
            ),
        }
        for objective in all_objectives
        for age_band in bands
    ]
    objective_age_summary = [
        {
            "age_band": age_band,
            "minimum_distinct_activity_families": 2,
            "applicable_objective_slices": sum(
                raw_objective_age[(objective, age_band)] > 0 for objective in all_objectives
            ),
            "slices_meeting_minimum_after_static_gates": sum(
                len(eligible_objective_families[(objective, age_band)]) >= 2
                for objective in all_objectives
                if raw_objective_age[(objective, age_band)] > 0
            ),
            "slices_below_minimum_after_static_gates": sum(
                len(eligible_objective_families[(objective, age_band)]) < 2
                for objective in all_objectives
                if raw_objective_age[(objective, age_band)] > 0
            ),
            "empty_slices_after_static_gates": sum(
                len(eligible_objective_families[(objective, age_band)]) == 0
                for objective in all_objectives
                if raw_objective_age[(objective, age_band)] > 0
            ),
        }
        for age_band in bands
    ]
    demand_family_age_coverage = [
        {
            "demand_tier": _demand_family_tier(family),
            "demand_family": family,
            "age_band": age_band,
            "review_eligible_profiles": raw_demand_family_age[(family, age_band)],
            "after_static_hard_gates_if_readiness_confirmed": eligible_demand_family_age[
                (family, age_band)
            ],
            "after_static_hard_gates_if_readiness_confirmed_candidates": len(
                eligible_demand_candidates[(family, age_band)]
            ),
            "after_static_hard_gates_if_readiness_confirmed_families": len(
                eligible_demand_activity_families[(family, age_band)]
            ),
            "minimum_safe_candidates": _TIER_MINIMUMS[_demand_family_tier(family)],
        }
        for family in _DEMAND_FAMILY_CONCEPTS
        for age_band in bands
    ]
    readiness_status_counts = Counter(item.readiness_metadata_status for item in template_rows)
    for row in demand_family_age_coverage:
        row["meets_minimum_after_static_gates"] = (
            _int_field(row, "after_static_hard_gates_if_readiness_confirmed_candidates")
            >= _int_field(row, "minimum_safe_candidates")
        )
    output = {
        "contract_name": "ChildProfileCatalogCoverageAuditV1",
        "catalog_revision": "catalog-2026-09",
        "semantic_profile_count": len(semantic.profiles),
        "review_eligible_profile_count": len(reviewed),
        "unique_scene_concepts": len(all_concepts),
        "unique_learning_objectives": len(all_objectives),
        "concept_age_coverage": concept_age_matrix,
        "objective_age_coverage": objective_age_matrix,
        "objective_age_minimum_coverage": objective_age_summary,
        "demand_family_age_coverage": demand_family_age_coverage,
        "demand_tier_age_summary": _tier_age_summary(concept_age_matrix),
        "demand_tier_mapping": {
            "source": "features/FEAT-022-catalog-coverage-expansion/DECISIONS.md#decision-2",
            "minimum_targets": {
                "A": "5 candidates per applicable age band (original target range 5-8)",
                "B": "3 candidates per applicable age band",
                "C": "2 candidates per applicable age band",
            },
            "interpretation": (
                "Audit-only concept mapping; no runtime tier metadata or matcher behavior changes. "
                "House/home currently has no mapped catalog concept and is reported as zero. "
                "Space is grouped with sun/moon per FEAT-022 and is not separately represented."
            ),
        },
        "interest_and_dislike_coverage": {
            "profiles_with_scene_concepts": sum(bool(item.concept_ids) for item in reviewed),
            "explicit_child_preference_history_in_catalog": 0,
        },
        "adult_progress_coverage": {
            "profiles_with_objective_metadata": sum(
                bool(item.primary_objective_id) for item in reviewed
            ),
            "historical_child_progress_records_in_catalog": 0,
            "templates_with_prerequisite_activity_ids": sum(
                bool(item.prerequisite_activity_ids) for item in template_rows
            ),
        },
        "readiness_coverage": {
            "metadata_status_counts": dict(sorted(readiness_status_counts.items())),
            "templates_with_authored_empty_readiness": sum(
                item.readiness_metadata_status == "AUTHORED" and not item.readiness_ids
                for item in template_rows
            ),
            "templates_with_readiness_ids": sum(bool(item.readiness_ids) for item in template_rows),
            "templates_total": len(template_rows),
        },
        "material_coverage": {
            "templates_with_material_options": sum(
                bool(item.material_option_ids) for item in template_rows
            ),
            "templates_total": len(template_rows),
            "material_registry_options": len(
                json.loads(
                    (ROOT / "data/activity-catalog/golden/v1/material-registry.v1.json").read_text(
                        encoding="utf-8"
                    )
                )["options"]
            ),
        },
        "supervision_coverage": {
            "templates_with_minimum_supervision": sum(
                bool(item.minimum_supervision) for item in template_rows
            ),
            "templates_total": len(template_rows),
        },
        "safety_coverage": {
            "templates_with_safety_rules": sum(
                bool(item.safety_rule_ids) for item in template_rows
            ),
            "templates_missing_safety_rules": sum(
                not item.safety_rule_ids for item in template_rows
            ),
            "templates_total": len(template_rows),
        },
        "static_hard_gate_coverage": {
            "profiles_with_matching_template": len(reviewed) - missing_template_profile_count,
            "profiles_missing_template": missing_template_profile_count,
            "ideal_static_gate_survivors": eligible_profile_count,
            "pre_production_review_scope_static_gate_survivors": eligible_profile_count,
            "production_approved_static_gate_survivors": (
                production_approved_static_gate_survivors
            ),
            "unknown_readiness_static_gate_survivors": unknown_readiness_profile_count,
            "excluded_for_unobserved_activity_history_prerequisites": sum(
                bool(item.prerequisite_activity_ids) for item in template_rows
            ),
            "interpretation": (
                "Upper-bound static catalog coverage only; assumes age-band midpoint, an adult "
                "can provide direct supervision, all listed materials are available, and all "
                "authored readiness is observed when computing the confirmed case. The ideal and "
                "pre-production counts include DEMO_ELIGIBLE and PROVISIONAL_OWNER_REVIEWED data; "
                "they are not production coverage. Production survivors require both semantic and "
                "P1 template records to be PRODUCTION_APPROVED and production_eligible=true. "
                "The audit does not evaluate topic match, activity-specific safety context, or "
                "actual child answers."
            ),
            "unknown_readiness_interpretation": (
                "Unknown-readiness survivors are limited to otherwise eligible templates whose "
                "readiness metadata is AUTHORED and has no readiness IDs, so no child-readiness "
                "answer is required for those activities. This does not treat unknown readiness "
                "as satisfying any authored readiness prerequisite; templates with readiness IDs "
                "remain excluded unless those criteria are confirmed."
            ),
        },
        "production_eligibility_coverage": {
            "semantic_profiles_by_review_status": dict(
                sorted(Counter(item.review_status for item in semantic.profiles).items())
            ),
            "p1_templates_by_review_status": dict(
                sorted(Counter(item.review_status for item in template_rows).items())
            ),
            "production_eligible_semantic_profiles": sum(
                item.production_eligible for item in semantic.profiles
            ),
            "production_eligible_p1_templates": sum(
                item.production_eligible for item in template_rows
            ),
            "activities_approved_in_both_catalogs": len(production_approved_activity_ids),
            "activities_surviving_static_hard_gates": (
                production_approved_static_gate_survivors
            ),
            "interpretation": (
                "A profile is counted as production eligible only when its semantic record and "
                "matching P1 template both carry PRODUCTION_APPROVED and production_eligible=true. "
                "Pre-production review-scope counts elsewhere in this report must not be described "
                "as production availability."
            ),
        },
        "learning_support_coverage": {
            "explicit_support_tags_in_semantic_profiles": 0,
            "v1_implementation": (
                "bounded crosswalk from reviewed interaction mode/objective; "
                "low-distraction support is not inferred"
            ),
        },
        "catalog_expansion_decision": (
            "No activities or readiness criteria were invented. Follow up on the measured "
            "UNSPECIFIED readiness-metadata gap with an authoritative source and reviewer; "
            "do not increase record count just to meet a larger advertised library size. Current "
            "post-gate counts are pre-production review-scope coverage, not production "
            "availability."
        ),
    }
    rendered = json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
