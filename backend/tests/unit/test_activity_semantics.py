"""Regression tests for the reviewed semantic activity gate and full catalog."""

from __future__ import annotations

from pathlib import Path

from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.contracts.schemas.p1_experience import (
    AnchorProvenanceV1,
    P1ContextV1,
    SemanticAnchorSetV1,
    SemanticAnchorV1,
)
from sketch2life.infrastructure.catalog.activity_semantics import (
    load_activity_semantic_catalog,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library

ROOT = Path(__file__).resolve().parents[3]


def _anchor(label: str, *, kind: str = "subject") -> SemanticAnchorSetV1:
    artifact_id = "semantic-test-image"
    artifact_hash = "a" * 64
    return SemanticAnchorSetV1(
        anchor_set_id="semantic-test-anchor-set",
        source_artifact_id=artifact_id,
        source_artifact_sha256=artifact_hash,
        gate_a_status="CONFIRMED",
        adult_confirmation_actor="CAREGIVER",
        primary_anchor=SemanticAnchorV1(
            anchor_id="semantic-test-primary",
            kind=kind,  # type: ignore[arg-type]
            original_label=label,
            normalized_label=label,
            semantic_tags=tuple(label.casefold().split()),
            confidence=0.95,
            adult_confirmed=True,
            provenance=AnchorProvenanceV1(
                source_artifact_id=artifact_id,
                source_artifact_sha256=artifact_hash,
                source_contract_name="SemanticTestV1",
                source_contract_version="1.0",
                source_claim_ids=("claim-semantic-test",),
            ),
        ),
    )


def test_full_catalog_and_semantic_profiles_cover_all_age_bands() -> None:
    library = load_p1_template_library(ROOT, include_mvp=True)
    catalog = load_activity_semantic_catalog(ROOT)

    assert len(library.templates) == 100
    assert len(catalog.profiles) == 100
    assert {
        profile.age_band
        for profile in catalog.profiles
        if profile.fallback_tier == "AGE_BASELINE"
    } == {"0-3", "3-6", "6-9", "9-12"}


def test_ambiguous_binh_minh_never_becomes_exact_pouring_activity() -> None:
    catalog = load_activity_semantic_catalog(ROOT)
    profile = catalog.profile_for("ACT-0026")

    result = catalog.match(_anchor("bình minh"), profile)

    assert result is not None
    assert result.match_mode == "SAFE_FALLBACK"
    assert result.score == 55
    assert "NO_EXACT_SEMANTIC_MATCH" in result.reason_codes


def test_safe_fallback_still_compiles_through_gate_b() -> None:
    catalog = load_activity_semantic_catalog(ROOT)
    library = load_p1_template_library(ROOT, include_mvp=True)
    template = library.by_activity("ACT-0026")[0]
    anchor_set = _anchor("bình minh")
    semantic_match = catalog.match(anchor_set, catalog.profile_for("ACT-0026"))
    assert semantic_match is not None
    context = P1ContextV1(
        session_id="semantic-fallback-session",
        expected_session_version=1,
        age_months=54,
        readiness_ids=template.readiness_ids,
        completed_activity_ids=template.prerequisite_activity_ids,
        available_material_option_ids=template.material_option_ids,
        supervision_level=template.minimum_supervision,
        policy_flags=template.policy_constraints,
        candidate_status="ACTIVE_FIXTURE",
        gate_a_confirmed=True,
    )
    result = P1ExperienceCompiler(
        library.templates,
        library.objective_titles_vi,
    ).compile(
        anchor_set,
        context,
        preferred_template_id=template.template_id,
        semantic_match=semantic_match,
    )

    assert result.spec is not None
    assert result.spec.semantic_match is not None
    assert result.spec.semantic_match.match_mode == "SAFE_FALLBACK"
    assert result.gate_b.status == "APPROVED"


def test_butterfly_bay_does_not_select_water_cycle_activity() -> None:
    catalog = load_activity_semantic_catalog(ROOT)
    profile = catalog.profile_for("ACT-0058")

    assert catalog.match(_anchor("bướm bay"), profile) is None


def test_reviewed_negative_phrase_blocks_unrelated_moon_activity() -> None:
    catalog = load_activity_semantic_catalog(ROOT)
    profile = catalog.profile_for("ACT-0091")

    assert catalog.match(_anchor("bình minh"), profile) is None


def test_moon_phrase_selects_reviewed_moon_activity() -> None:
    catalog = load_activity_semantic_catalog(ROOT)
    profile = catalog.profile_for("ACT-0091")

    result = catalog.match(_anchor("mặt trăng"), profile)

    assert result is not None
    assert result.match_mode == "ALIAS"
    assert result.score == 88
    assert result.matched_phrases_vi == ("mặt trăng",)