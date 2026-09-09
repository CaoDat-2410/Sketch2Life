"""Fixture-only tests for FEAT-018 P1 selection and ExperienceSpec."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.contracts.schemas.p1_experience import (
    ActivityTemplateV1,
    AnchorProvenanceV1,
    P1ContextV1,
    SemanticAnchorSetV1,
    SemanticAnchorV1,
    VersionedRefV1,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library

ROOT = Path(__file__).resolve().parents[3]


def _anchor(
    *, label: str = "butterfly", tags: tuple[str, ...] = ("wings", "symmetry")
) -> SemanticAnchorSetV1:
    artifact_id = "fixture-art-butterfly-001"
    artifact_hash = "a" * 64
    return SemanticAnchorSetV1(
        anchor_set_id="anchors-fixture-001",
        source_artifact_id=artifact_id,
        source_artifact_sha256=artifact_hash,
        gate_a_status="CONFIRMED",
        adult_confirmation_actor="CAREGIVER",
        primary_anchor=SemanticAnchorV1(
            anchor_id="anchor-butterfly",
            kind="subject",
            original_label=label,
            normalized_label=label,
            semantic_tags=tags,
            confidence=0.98,
            adult_confirmed=True,
            provenance=AnchorProvenanceV1(
                source_artifact_id=artifact_id,
                source_artifact_sha256=artifact_hash,
                source_contract_name="RawUnderstandingResultV1",
                source_contract_version="1.0",
                source_claim_ids=("claim-001",),
            ),
        ),
    )


def _context(template: ActivityTemplateV1, *, gate_a_confirmed: bool = True) -> P1ContextV1:
    return P1ContextV1(
        session_id="session-fixture-001",
        expected_session_version=3,
        age_months=min(max(template.age_months_min, 36), template.age_months_max),
        readiness_ids=template.readiness_ids,
        completed_activity_ids=template.prerequisite_activity_ids,
        available_material_option_ids=(template.material_option_ids[0],),
        supervision_level=template.minimum_supervision,
        policy_flags=template.policy_constraints or ("CAREGIVER_PRESENT",),
        candidate_status="ACTIVE_FIXTURE",
        gate_a_confirmed=gate_a_confirmed,
    )


def _butterfly_template() -> ActivityTemplateV1:
    return ActivityTemplateV1(
        template_id="TPL-FIXTURE-BUTTERFLY-FOLD-PRINT-V1",
        template_version=1,
        activity_ref=VersionedRefV1(id="ACT-FIXTURE-BUTTERFLY-FOLD-PRINT", version=1),
        objective_refs=(VersionedRefV1(id="OBJ_SENSORIAL_DISCRIMINATION", version=1),),
        supported_anchor_labels=("butterfly", "wings", "symmetry"),
        supported_anchor_kinds=("subject", "visual_feature"),
        interaction_mode="SORTING",
        age_months_min=36,
        age_months_max=71,
        material_option_ids=("MAT-FIXTURE-PAPER",),
        minimum_supervision="NEARBY",
        safety_rule_ids=("FIXTURE_NO_SMALL_PARTS",),
        steps_vi=(
            "Gấp giấy theo đường giữa.",
            "Chấm màu ở một bên cánh.",
            "Mở giấy và quan sát hai cánh đối xứng.",
        ),
        personalization_slots=("colour_choice",),
        provenance_source="tests/fixtures/p1-experience/butterfly-pass.json",
        provenance_sha256="b" * 64,
        review_status="PROVISIONAL_OWNER_REVIEWED",
    )


def test_catalog_loader_promotes_twenty_golden_templates_and_act0004_mapping() -> None:
    library = load_p1_template_library(ROOT)
    assert len(library.templates) == 20
    act0004 = library.by_activity("ACT-0004")[0]
    assert act0004.activity_ref.version == 2
    assert act0004.objective_refs[0] == VersionedRefV1(id="OBJ_OBJECT_PERMANENCE", version=1)
    assert act0004.objective_refs[1] == VersionedRefV1(id="OBJ_RECEPTIVE_LANGUAGE", version=1)
    assert all(template.production_eligible is False for template in library.templates)


def test_butterfly_fold_print_compiles_one_spec_and_gate_b_locks_identity() -> None:
    library = load_p1_template_library(ROOT)
    fixture = _butterfly_template()
    compiler = P1ExperienceCompiler(
        (*library.templates, fixture),
        {
            **library.objective_titles_vi,
            "OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng",
        },
    )
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)

    assert result.filter_result.status == "VALID_CANDIDATE"
    assert result.fit_evaluation is not None
    assert result.fit_evaluation.status == "PASS"
    assert result.spec is not None
    assert result.gate_b.status == "APPROVED"
    assert result.handoff is not None
    assert result.spec.video_plan.objective_ref == result.spec.activity_plan.objective_ref
    assert result.spec.video_plan.template_ref == result.spec.activity_plan.template_ref
    assert result.spec.video_plan.anchor_id == result.spec.anchor_set.primary_anchor.anchor_id
    assert result.spec.spec_sha256 == result.spec.spec_sha256
    rechecked = compiler.approve_gate_b(result.spec, context)
    assert rechecked.status == "APPROVED"
    assert rechecked.spec_ref is not None
    assert rechecked.spec_ref.id == result.spec.spec_id


def test_unrelated_sorting_template_is_rejected_below_fit_threshold() -> None:
    library = load_p1_template_library(ROOT)
    sorting = library.by_activity("ACT-0039")[0]
    compiler = P1ExperienceCompiler(library.templates, library.objective_titles_vi)
    result = compiler.compile(
        _anchor(), _context(sorting), preferred_template_id=sorting.template_id
    )

    assert result.filter_result.status == "NO_ELIGIBLE_ACTIVITY"
    assert result.fit_evaluation is not None
    assert result.fit_evaluation.status == "REJECT"
    assert result.fit_evaluation.total_score < result.fit_evaluation.threshold
    assert "ANCHOR_TEMPLATE_MISMATCH" in result.fit_evaluation.reason_codes
    assert result.gate_b.status == "BLOCKED"


def test_missing_context_is_typed_before_selection() -> None:
    library = load_p1_template_library(ROOT)
    template = library.by_activity("ACT-0004")[0]
    context = P1ContextV1(
        session_id="session-missing-context",
        expected_session_version=1,
        gate_a_confirmed=True,
    )
    result = P1ExperienceCompiler(library.templates, library.objective_titles_vi).compile(
        _anchor(label="object", tags=("covered",)),
        context,
        preferred_template_id=template.template_id,
    )
    assert result.filter_result.status == "MISSING_CONTEXT"
    assert any(code.startswith("MISSING_CONTEXT:") for code in result.filter_result.reason_codes)
    assert result.gate_b.status == "BLOCKED"


def test_stale_template_is_blocked_at_gate_b() -> None:
    fixture = _butterfly_template()
    compiler = P1ExperienceCompiler((fixture,), {"OBJ_SENSORIAL_DISCRIMINATION": "Đối xứng"})
    result = compiler.compile(
        _anchor(), _context(fixture), preferred_template_id=fixture.template_id
    )
    assert result.spec is not None
    stale_compiler = P1ExperienceCompiler((), {})
    decision = stale_compiler.approve_gate_b(result.spec, _context(fixture))
    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("STALE_TEMPLATE",)


def test_contract_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        P1ContextV1(
            session_id="session-extra",
            expected_session_version=1,
            unknown_field="must-be-rejected",  # type: ignore[call-arg]
        )
