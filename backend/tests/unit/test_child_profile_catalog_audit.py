from types import SimpleNamespace

from backend.tools.audit_child_profile_catalog import (
    _demand_families_for_concept,
    _demand_family_tier,
    _demand_tier,
    _has_no_authored_readiness_prerequisite,
    _production_approved_activity_ids,
    _tier_age_summary,
)


def test_audit_tiers_follow_feat022_and_keep_unmapped_topics_specialist() -> None:
    assert _demand_tier("ANIMAL_BUTTERFLY") == "A"
    assert _demand_tier("SUN_LIGHT") == "B"
    assert _demand_tier("SCIENCE_OBSERVATION") == "C"
    assert _demand_family_tier("house/home") == "B"
    assert _demand_families_for_concept("ANIMAL_MOVEMENT") == ("animal", "movement")
    assert _demand_families_for_concept("HOUSE_HOME") == ()


def test_tier_target_counts_candidates_not_distinct_activity_families() -> None:
    rows = [
        {
            "demand_tier": "A",
            "age_band": "3-6",
            "review_eligible_profiles": 5,
            "after_static_hard_gates_if_readiness_confirmed_candidates": 5,
            "after_static_hard_gates_if_readiness_confirmed_families": 1,
        }
    ]

    rows_by_age = _tier_age_summary(rows)
    tier_a_3_6 = next(
        row
        for row in rows_by_age
        if row["demand_tier"] == "A" and row["age_band"] == "3-6"
    )

    assert tier_a_3_6["minimum_safe_candidates"] == 5
    assert tier_a_3_6["slices_meeting_minimum_after_static_gates"] == 1
    assert tier_a_3_6["slices_below_minimum_after_static_gates"] == 0


def test_production_coverage_requires_both_semantic_and_template_approval() -> None:
    approved_template = SimpleNamespace(
        activity_ref=SimpleNamespace(id="ACT_APPROVED"),
        review_status="PRODUCTION_APPROVED",
        production_eligible=True,
    )
    provisional_template = SimpleNamespace(
        activity_ref=SimpleNamespace(id="ACT_PROVISIONAL"),
        review_status="PROVISIONAL_OWNER_REVIEWED",
        production_eligible=False,
    )
    semantic_profiles = [
        SimpleNamespace(
            activity_id="ACT_APPROVED",
            review_status="PRODUCTION_APPROVED",
            production_eligible=True,
        ),
        SimpleNamespace(
            activity_id="ACT_PROVISIONAL",
            review_status="PROVISIONAL_OWNER_REVIEWED",
            production_eligible=False,
        ),
        SimpleNamespace(
            activity_id="ACT_SEMANTIC_ONLY",
            review_status="PRODUCTION_APPROVED",
            production_eligible=True,
        ),
    ]

    assert _production_approved_activity_ids(
        semantic_profiles,
        [approved_template, provisional_template],
    ) == {"ACT_APPROVED"}


def test_unknown_child_readiness_only_passes_authored_templates_without_prerequisites() -> None:
    assert _has_no_authored_readiness_prerequisite(
        SimpleNamespace(readiness_metadata_status="AUTHORED", readiness_ids=())
    )
    assert not _has_no_authored_readiness_prerequisite(
        SimpleNamespace(readiness_metadata_status="AUTHORED", readiness_ids=("READY_X",))
    )
    assert not _has_no_authored_readiness_prerequisite(
        SimpleNamespace(readiness_metadata_status="UNSPECIFIED", readiness_ids=())
    )
