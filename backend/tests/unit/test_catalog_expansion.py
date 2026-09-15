"""FEAT-022 catalog expansion and quality-gate tests."""

from __future__ import annotations

from pathlib import Path

from sketch2life.infrastructure.catalog.activity_catalog_quality import (
    build_activity_diversity_report,
    build_coverage_quality_report,
    build_objective_age_coverage_report,
    diff_catalogs,
    lint_curated_catalog_v2,
)
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.infrastructure.catalog.curated_catalog import load_curated_catalog_v2
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library

ROOT = Path(__file__).resolve().parents[3]


def test_expansion_is_opt_in_and_keeps_mvp_rollback() -> None:
    baseline = load_p1_template_library(ROOT, include_mvp=True)
    expanded = load_p1_template_library(
        ROOT,
        include_mvp=True,
        include_expansion=True,
    )

    assert len(baseline.templates) == 100
    assert len(expanded.templates) == 300
    assert {template.activity_ref.id for template in baseline.templates}.isdisjoint(
        template.activity_ref.id for template in expanded.templates[100:]
    )


def test_curated_quality_gate_passes_against_baseline_plus_expansion() -> None:
    curated = load_curated_catalog_v2(ROOT)
    baseline_profiles = load_activity_semantic_catalog_v2(ROOT).profiles

    report = lint_curated_catalog_v2(
        curated,
        baseline_profiles=baseline_profiles,
    )

    assert report.passed is True
    assert report.selectable_variant_count == 300
    assert report.activity_family_count >= 60


def test_post_filter_tiered_coverage_has_no_remaining_scoped_gaps() -> None:
    expanded = load_activity_semantic_catalog_v2(ROOT, include_expansion=True)

    report = build_coverage_quality_report(expanded.profiles)

    assert report.selectable_variant_count == 300
    assert report.covered_pair_ratio == 1.0
    assert report.gaps == ()


def test_objective_age_coverage_has_two_candidates_per_age_band() -> None:
    curated = load_curated_catalog_v2(ROOT)

    report = build_objective_age_coverage_report(curated)

    assert report.objective_count == 13
    assert report.objective_age_pair_count == 52
    assert report.covered_pair_ratio == 1.0
    assert report.gaps == ()


def test_diversity_report_tracks_activity_and_family_concentration() -> None:
    expanded = load_activity_semantic_catalog_v2(ROOT, include_expansion=True)
    selected_ids = (
        "ACT-0101",
        "ACT-0102",
        "ACT-0105",
        "ACT-0121",
        "ACT-0161",
        "ACT-0181",
        "ACT-0201",
        "ACT-0221",
        "ACT-0241",
        "ACT-0265",
        "ACT-0289",
    )

    report = build_activity_diversity_report(expanded.profiles, selected_ids)

    assert report.recommendation_count == len(selected_ids)
    assert report.distinct_activity_count == len(selected_ids)
    assert report.distinct_family_count == 10
    assert report.immediate_repeat_rate == 0.0
    assert report.top_activity_share == 1 / len(selected_ids)


def test_catalog_diff_identifies_the_authored_revision() -> None:
    baseline = load_activity_semantic_catalog_v2(ROOT).profiles
    expanded = load_activity_semantic_catalog_v2(ROOT, include_expansion=True).profiles

    report = diff_catalogs(baseline, expanded)

    assert len(report.added_activity_ids) == 200
    assert report.removed_activity_ids == ()
    assert len(report.added_family_ids) >= 50
    assert report.to_revision == "mixed"


def test_revision_two_exposes_variant_objectives_butterfly_and_typed_duration() -> None:
    curated = load_curated_catalog_v2(ROOT)
    by_id = curated.by_activity_id()

    assert curated.catalog_revision == "catalog-2026-09-expansion-2"
    assert {
        item.activity_id
        for item in curated.variants
        if item.activity_family_id == "FAM-ANIMAL-BUTTERFLY"
    } == {"ACT-0113", "ACT-0114", "ACT-0115", "ACT-0116"}
    assert by_id["ACT-0123"].primary_objective_id == "OBJ_SCIENTIFIC_OBSERVATION"
    assert by_id["ACT-0123"].secondary_objective_ids == ("OBJ_INDEPENDENCE_SELF_CARE",)
    assert by_id["ACT-0123"].duration_type == "MULTI_DAY"
    assert by_id["ACT-0123"].initial_session_minutes == 20
    assert by_id["ACT-0123"].daily_observation_minutes == 5
    assert (by_id["ACT-0123"].min_days, by_id["ACT-0123"].max_days) == (3, 5)
    assert by_id["ACT-0123"].to_template().production_eligible is False


def test_expansion_one_rollback_revision_remains_loadable() -> None:
    rollback = load_curated_catalog_v2(
        ROOT,
        revision="catalog-2026-09-expansion-1",
    )

    assert rollback.catalog_revision == "catalog-2026-09-expansion-1"
    assert len(rollback.by_family_id()) == 50
    assert len(rollback.variants) == 200
    assert rollback.by_activity_id()["ACT-0113"].activity_family_id == "FAM-ANIMAL-HABITAT"
    assert rollback.by_activity_id()["ACT-0123"].objective_ids == (
        "OBJ_INDEPENDENCE_SELF_CARE",
    )
    assert all("ANIMAL_BUTTERFLY" not in variant.concept_ids for variant in rollback.variants)
