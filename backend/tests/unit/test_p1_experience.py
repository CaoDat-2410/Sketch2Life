"""Fixture-only tests for FEAT-018 P1 selection and ExperienceSpec."""

from __future__ import annotations

import json
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


def _fixture_compiler(*templates: ActivityTemplateV1) -> P1ExperienceCompiler:
    selected = templates or (_butterfly_template(),)
    return P1ExperienceCompiler(
        selected,
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
    )


def test_strict_continuity_fixture_manifest_is_sanitized_and_contract_pinned() -> None:
    manifest_path = ROOT / "tests/fixtures/p1-experience/strict-continuity-manifest.v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["manifest_version"] == "p1-strict-continuity-manifest-v1"
    assert len(manifest["fixture_ids"]) == 5
    assert manifest["raw_media_included"] is False
    assert manifest["real_child_data_included"] is False
    assert manifest["provider_credentials_included"] is False
    assert manifest["contract_versions"] == {
        "ActivityFitEvaluationV1": "1.0",
        "BridgeSentenceV1": "1.0",
        "ExperienceSpecV1": "1.0",
    }


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
    assert result.spec.activity_plan.activity_ref == fixture.activity_ref
    assert result.spec.activity_plan.template_ref.id == fixture.template_id
    assert "P1_STRICT_CONTINUITY_V1" in result.spec.policy_versions
    assert result.spec.learning_focus.selection_policy_version == "P1_STRICT_CONTINUITY_V1"
    assert (
        result.spec.anchor_set.primary_anchor.normalized_label
        in result.spec.bridge_sentence.sentence_vi
    )
    assert "phân biệt đặc điểm đối xứng" in result.spec.bridge_sentence.sentence_vi.casefold()
    assert result.handoff is not None
    assert result.handoff.spec_ref.id == result.spec.spec_id
    assert result.handoff.activity_ref == result.spec.activity_plan.activity_ref
    assert result.handoff.objective_ref == result.spec.learning_focus.objective_ref
    assert result.handoff.template_ref == result.spec.activity_plan.template_ref
    assert result.spec.spec_sha256 == result.spec.spec_sha256
    rechecked = compiler.approve_gate_b(result.spec, context)
    assert rechecked.status == "APPROVED"
    assert rechecked.spec_ref is not None
    assert rechecked.spec_ref.id == result.spec.spec_id


def test_unsupported_anchor_kind_is_rejected_before_spec_compilation() -> None:
    fixture = _butterfly_template().model_copy(
        update={"supported_anchor_kinds": ("visual_feature",)}
    )
    compiler = P1ExperienceCompiler(
        (fixture,),
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
    )

    result = compiler.compile(
        _anchor(), _context(fixture), preferred_template_id=fixture.template_id
    )

    assert result.spec is None
    assert result.fit_evaluation is not None
    assert result.fit_evaluation.status == "REJECT"
    assert "ANCHOR_KIND_TEMPLATE_MISMATCH" in result.fit_evaluation.reason_codes
    assert "FIT_BELOW_THRESHOLD" in result.fit_evaluation.reason_codes
    assert result.gate_b.status == "BLOCKED"


def test_matching_anchor_with_unrelated_objective_is_rejected_by_strict_fit() -> None:
    fixture = _butterfly_template()
    unrelated_objective = VersionedRefV1(id="OBJ_UNRELATED_SORTING", version=1)

    fit = P1ExperienceCompiler._fit_evaluation(
        _anchor(), fixture, unrelated_objective, match_score=5
    )

    assert fit.status == "REJECT"
    assert fit.objective_alignment == 0
    assert fit.video_continuity == 0
    assert fit.total_score < fit.threshold
    assert "OBJECTIVE_TEMPLATE_MISMATCH" in fit.reason_codes
    assert "FIT_BELOW_THRESHOLD" in fit.reason_codes


def test_ambiguous_anchor_blocks_without_preferred_template() -> None:
    first = _butterfly_template()
    second = first.model_copy(update={"template_id": "TPL-FIXTURE-BUTTERFLY-FOLD-PRINT-V2"})
    compiler = P1ExperienceCompiler(
        (first, second),
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
    )

    result = compiler.compile(_anchor(), _context(first))

    assert result.filter_result.status == "AMBIGUOUS_ANCHOR"
    assert result.filter_result.reason_codes == ("MULTIPLE_EQUAL_ANCHOR_MATCHES",)
    assert result.spec is None
    assert result.gate_b.status == "BLOCKED"


def test_gate_b_blocks_bridge_identity_drift() -> None:
    fixture = _butterfly_template()
    compiler = P1ExperienceCompiler(
        (fixture,),
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
    )
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    wrong_bridge = result.spec.bridge_sentence.model_copy(
        update={"template_ref": VersionedRefV1(id="TPL-WRONG", version=1)}
    )
    tampered = result.spec.model_copy(update={"bridge_sentence": wrong_bridge})

    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("BRIDGE_IDENTITY_MISMATCH",)


def test_gate_b_blocks_bridge_objective_drift() -> None:
    fixture = _butterfly_template()
    compiler = P1ExperienceCompiler(
        (fixture,),
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
    )
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    wrong_bridge = result.spec.bridge_sentence.model_copy(
        update={"objective_ref": VersionedRefV1(id="OBJ_WRONG", version=1)}
    )
    tampered = result.spec.model_copy(update={"bridge_sentence": wrong_bridge})

    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("BRIDGE_IDENTITY_MISMATCH",)


def test_gate_b_blocks_media_identity_drift() -> None:
    fixture = _butterfly_template()
    compiler = P1ExperienceCompiler(
        (fixture,),
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
    )
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    wrong_video = result.spec.video_plan.model_copy(
        update={"objective_ref": VersionedRefV1(id="OBJ_WRONG", version=1)}
    )
    tampered = result.spec.model_copy(update={"video_plan": wrong_video})

    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("ACTIVITY_IDENTITY_MISMATCH",)


def test_gate_b_blocks_spec_hash_drift() -> None:
    fixture = _butterfly_template()
    compiler = P1ExperienceCompiler(
        (fixture,),
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
    )
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    tampered = result.spec.model_copy(update={"spec_sha256": "c" * 64})
    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("SPEC_HASH_MISMATCH",)


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


@pytest.mark.parametrize(
    ("template_update", "context_update", "expected_reason"),
    [
        ({}, {"candidate_status": "INACTIVE_FIXTURE"}, "BLOCK_INACTIVE"),
        ({}, {"age_months": 35}, "BLOCK_AGE"),
        (
            {"readiness_ids": ("READY_FOCUS",)},
            {"readiness_ids": ()},
            "BLOCK_MISSING_READINESS",
        ),
        (
            {"prerequisite_activity_ids": ("ACT-PREV",)},
            {"completed_activity_ids": ()},
            "BLOCK_MISSING_PREREQUISITE",
        ),
        (
            {"minimum_supervision": "DIRECT"},
            {"supervision_level": "NEARBY"},
            "BLOCK_INSUFFICIENT_SUPERVISION",
        ),
        (
            {"policy_constraints": ("CAREGIVER_PRESENT", "NO_GLUE")},
            {"policy_flags": ("CAREGIVER_PRESENT",)},
            "BLOCK_POLICY_CONSTRAINT",
        ),
        ({}, {"available_material_option_ids": ()}, "BLOCK_MISSING_MATERIAL"),
    ],
)
def test_hard_eligibility_rules_block_before_fit(
    template_update: dict[str, object],
    context_update: dict[str, object],
    expected_reason: str,
) -> None:
    fixture = _butterfly_template().model_copy(update=template_update)
    context = _context(fixture).model_copy(update=context_update)

    result = _fixture_compiler(fixture).compile(
        _anchor(), context, preferred_template_id=fixture.template_id
    )

    assert result.filter_result.status == "NO_ELIGIBLE_ACTIVITY"
    assert f"{fixture.activity_ref.id}:{expected_reason}" in result.filter_result.reason_codes
    assert result.fit_evaluation is None
    assert result.spec is None
    assert result.gate_b.status == "BLOCKED"


def test_gate_a_unconfirmed_blocks_before_context_or_selection() -> None:
    fixture = _butterfly_template()
    context = _context(fixture, gate_a_confirmed=False)

    result = _fixture_compiler(fixture).compile(_anchor(), context)

    assert result.filter_result.status == "NO_ELIGIBLE_ACTIVITY"
    assert result.filter_result.reason_codes == ("BLOCK_GATE_A_UNCONFIRMED",)
    assert result.fit_evaluation is None
    assert result.spec is None
    assert result.gate_b.status == "BLOCKED"


def test_unknown_anchor_blocks_without_generic_activity_fallback() -> None:
    fixture = _butterfly_template()
    result = _fixture_compiler(fixture).compile(
        _anchor(label="volcano", tags=("lava", "mountain")), _context(fixture)
    )

    assert result.filter_result.status == "UNKNOWN_ANCHOR"
    assert result.filter_result.reason_codes == ("ANCHOR_NOT_IN_TEMPLATE_LIBRARY",)
    assert result.filter_result.activity_ref is None
    assert result.spec is None
    assert result.gate_b.status == "BLOCKED"


def test_missing_preferred_template_is_typed_as_stale() -> None:
    fixture = _butterfly_template()
    result = _fixture_compiler(fixture).compile(
        _anchor(), _context(fixture), preferred_template_id="TPL-NOT-IN-CATALOG"
    )

    assert result.filter_result.status == "NO_ELIGIBLE_ACTIVITY"
    assert result.filter_result.reason_codes == ("STALE_TEMPLATE",)
    assert result.spec is None
    assert result.gate_b.status == "BLOCKED"


def test_selection_prefers_highest_anchor_score_deterministically() -> None:
    primary = _butterfly_template()
    lower_score = primary.model_copy(
        update={
            "template_id": "TPL-FIXTURE-BUTTERFLY-LOWER-SCORE",
            "activity_ref": VersionedRefV1(
                id="ACT-FIXTURE-BUTTERFLY-LOWER-SCORE", version=1
            ),
            "supported_anchor_labels": ("butterfly",),
        }
    )

    result = _fixture_compiler(primary, lower_score).compile(
        _anchor(), _context(primary)
    )

    assert result.filter_result.status == "VALID_CANDIDATE"
    assert result.filter_result.template_ref is not None
    assert result.filter_result.template_ref.id == primary.template_id
    assert result.filter_result.candidate_refs == (
        primary.activity_ref,
        lower_score.activity_ref,
    )
    assert result.gate_b.status == "APPROVED"


def test_hard_ineligible_candidate_is_excluded_from_candidate_refs() -> None:
    valid = _butterfly_template()
    age_blocked = valid.model_copy(
        update={
            "template_id": "TPL-FIXTURE-BUTTERFLY-AGE-BLOCKED",
            "age_months_min": 0,
            "age_months_max": 35,
        }
    )

    result = _fixture_compiler(valid, age_blocked).compile(_anchor(), _context(valid))

    assert result.filter_result.status == "VALID_CANDIDATE"
    assert result.filter_result.candidate_refs == (valid.activity_ref,)
    assert result.filter_result.template_ref is not None
    assert result.filter_result.template_ref.id == valid.template_id


def test_semantic_tag_can_be_the_exact_continuity_anchor() -> None:
    fixture = _butterfly_template()
    result = _fixture_compiler(fixture).compile(
        _anchor(label="insect", tags=("wings",)),
        _context(fixture),
        preferred_template_id=fixture.template_id,
    )

    assert result.fit_evaluation is not None
    assert result.fit_evaluation.status == "PASS"
    assert result.spec is not None
    assert result.spec.anchor_set.primary_anchor.normalized_label == "insect"
    assert "insect" in result.spec.bridge_sentence.sentence_vi


def test_anchor_matching_is_case_and_whitespace_tolerant() -> None:
    fixture = _butterfly_template()
    result = _fixture_compiler(fixture).compile(
        _anchor(label=" Butterfly "),
        _context(fixture),
        preferred_template_id=fixture.template_id,
    )

    assert result.fit_evaluation is not None
    assert result.fit_evaluation.status == "PASS"
    assert result.gate_b.status == "APPROVED"


def test_gate_b_blocks_session_drift() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    decision = compiler.approve_gate_b(
        result.spec,
        context.model_copy(update={"session_id": "session-other"}),
    )

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("SESSION_ID_MISMATCH",)


def test_gate_b_rechecks_gate_a_confirmation() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    decision = compiler.approve_gate_b(
        result.spec,
        context.model_copy(update={"gate_a_confirmed": False}),
    )

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("BLOCK_GATE_A_UNCONFIRMED",)


def test_gate_b_rechecks_required_context() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    decision = compiler.approve_gate_b(
        result.spec,
        context.model_copy(update={"available_material_option_ids": None}),
    )

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("MISSING_CONTEXT:available_material_option_ids",)


def test_gate_b_blocks_catalog_template_version_drift() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    newer_catalog = fixture.model_copy(update={"template_version": 2})
    decision = _fixture_compiler(newer_catalog).approve_gate_b(result.spec, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("STALE_TEMPLATE",)


def test_gate_b_blocks_activity_ref_drift() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    wrong_activity = result.spec.activity_template.model_copy(
        update={"activity_ref": VersionedRefV1(id="ACT-WRONG", version=1)}
    )
    tampered = result.spec.model_copy(update={"activity_template": wrong_activity})
    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("ACTIVITY_IDENTITY_MISMATCH",)


def test_gate_b_blocks_learning_focus_anchor_drift() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    wrong_focus = result.spec.learning_focus.model_copy(update={"selected_anchor_id": "other"})
    tampered = result.spec.model_copy(update={"learning_focus": wrong_focus})
    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("ACTIVITY_IDENTITY_MISMATCH",)


def test_gate_b_blocks_bridge_sentence_text_drift() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    wrong_bridge = result.spec.bridge_sentence.model_copy(
        update={"sentence_vi": "Hãy thử hoạt động này nhé."}
    )
    tampered = result.spec.model_copy(update={"bridge_sentence": wrong_bridge})
    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("BRIDGE_IDENTITY_MISMATCH",)


def test_gate_b_blocks_animation_source_artifact_drift() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    wrong_animation = result.spec.animation_plan.model_copy(
        update={"source_artifact_id": "artifact-other"}
    )
    tampered = result.spec.model_copy(update={"animation_plan": wrong_animation})
    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("ACTIVITY_IDENTITY_MISMATCH",)


def test_gate_b_blocks_fit_catalog_reference_drift() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    wrong_fit = result.spec.fit_evaluation.model_copy(
        update={"evaluated_catalog_ref": VersionedRefV1(id="ACT-WRONG", version=1)}
    )
    tampered = result.spec.model_copy(update={"fit_evaluation": wrong_fit})
    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("ACTIVITY_IDENTITY_MISMATCH",)


def test_same_inputs_produce_same_spec_id_and_hash() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)

    first = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    second = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)

    assert first.spec is not None
    assert second.spec is not None
    assert first.spec.spec_id == second.spec.spec_id
    assert first.spec.spec_sha256 == second.spec.spec_sha256
    assert first.spec == second.spec


def test_experience_spec_is_immutable_after_compilation() -> None:
    fixture = _butterfly_template()
    result = _fixture_compiler(fixture).compile(
        _anchor(), _context(fixture), preferred_template_id=fixture.template_id
    )
    assert result.spec is not None

    with pytest.raises(ValidationError):
        result.spec.spec_id = "SPEC-TAMPERED"  # type: ignore[misc]


@pytest.mark.parametrize("age_months", [36, 71])
def test_age_bounds_are_inclusive(age_months: int) -> None:
    fixture = _butterfly_template()
    context = _context(fixture).model_copy(update={"age_months": age_months})

    result = _fixture_compiler(fixture).compile(
        _anchor(), context, preferred_template_id=fixture.template_id
    )

    assert result.fit_evaluation is not None
    assert result.fit_evaluation.status == "PASS"
    assert result.gate_b.status == "APPROVED"


def test_satisfied_readiness_prerequisite_and_material_rules_allow_selection() -> None:
    fixture = _butterfly_template().model_copy(
        update={
            "readiness_ids": ("READY_FOCUS",),
            "prerequisite_activity_ids": ("ACT-PREV",),
            "material_option_ids": ("MAT-FIXTURE-PAPER", "MAT-FIXTURE-PAINT"),
        }
    )

    result = _fixture_compiler(fixture).compile(
        _anchor(), _context(fixture), preferred_template_id=fixture.template_id
    )

    assert result.filter_result.status == "VALID_CANDIDATE"
    assert result.fit_evaluation is not None
    assert result.fit_evaluation.status == "PASS"
    assert result.gate_b.status == "APPROVED"


def test_preferred_template_explicitly_resolves_equal_or_lower_candidate() -> None:
    primary = _butterfly_template()
    alternate = primary.model_copy(
        update={
            "template_id": "TPL-FIXTURE-BUTTERFLY-ALTERNATE",
            "activity_ref": VersionedRefV1(id="ACT-FIXTURE-BUTTERFLY-ALTERNATE", version=1),
            "supported_anchor_labels": ("butterfly",),
        }
    )
    compiler = _fixture_compiler(primary, alternate)

    result = compiler.compile(
        _anchor(), _context(primary), preferred_template_id=alternate.template_id
    )

    assert result.filter_result.status == "VALID_CANDIDATE"
    assert result.filter_result.template_ref is not None
    assert result.filter_result.template_ref.id == alternate.template_id
    assert result.spec is not None
    assert result.spec.activity_plan.activity_ref == alternate.activity_ref


def test_gate_b_blocks_rejected_fit_status_even_when_identity_is_unchanged() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    rejected_fit = result.spec.fit_evaluation.model_copy(
        update={
            "status": "REJECT",
            "drawing_relevance": 0,
            "objective_alignment": 0,
            "video_continuity": 0,
            "total_score": 15,
        }
    )
    tampered = result.spec.model_copy(update={"fit_evaluation": rejected_fit})
    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("FIT_BELOW_THRESHOLD",)


def test_custom_selection_policy_version_is_recorded_in_spec() -> None:
    fixture = _butterfly_template()
    compiler = P1ExperienceCompiler(
        (fixture,),
        {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
        policy_version="P1_STRICT_CONTINUITY_TEST_V2",
    )

    result = compiler.compile(
        _anchor(), _context(fixture), preferred_template_id=fixture.template_id
    )

    assert result.spec is not None
    assert result.spec.learning_focus.selection_policy_version == "P1_STRICT_CONTINUITY_TEST_V2"
    assert "P1_STRICT_CONTINUITY_V1" in result.spec.policy_versions



def test_catalog_anchor_labels_exclude_objectives_and_area_taxonomy() -> None:
    library = load_p1_template_library(ROOT)
    area_tokens = {"language", "mathematics", "practical_life", "science", "sensorial"}

    assert all(
        not label.upper().startswith("OBJ_")
        and label not in area_tokens
        and label == label.strip().casefold()
        for template in library.templates
        for label in template.supported_anchor_labels
    )
    assert all(template.supported_anchor_labels for template in library.templates)


def test_catalog_objective_refs_all_have_nonempty_titles() -> None:
    library = load_p1_template_library(ROOT)

    assert all(
        library.objective_titles_vi[ref.id].strip()
        for template in library.templates
        for ref in template.objective_refs
    )


def test_duplicate_template_id_fails_fast() -> None:
    fixture = _butterfly_template()

    with pytest.raises(ValueError, match="DUPLICATE_TEMPLATE_ID"):
        P1ExperienceCompiler(
            (fixture, fixture),
            {"OBJ_SENSORIAL_DISCRIMINATION": "Phân biệt đặc điểm đối xứng"},
        )


def test_missing_objective_title_fails_fast_for_injected_templates() -> None:
    fixture = _butterfly_template()

    with pytest.raises(ValueError, match="OBJECTIVE_TITLE_MISSING"):
        P1ExperienceCompiler((fixture,), {})


@pytest.mark.parametrize(
    ("context_update", "expected_reason"),
    [
        (
            {"selected_activity_id": "ACT-WRONG", "selected_activity_version": 1},
            "CONTEXT_ACTIVITY_ID_MISMATCH",
        ),
        (
            {
                "selected_activity_id": "ACT-FIXTURE-BUTTERFLY-FOLD-PRINT",
                "selected_activity_version": 2,
            },
            "CONTEXT_ACTIVITY_VERSION_MISMATCH",
        ),
        (
            {"selected_objective_id": "OBJ-WRONG", "selected_objective_version": 1},
            "CONTEXT_OBJECTIVE_ID_MISMATCH",
        ),
        (
            {
                "selected_objective_id": "OBJ_SENSORIAL_DISCRIMINATION",
                "selected_objective_version": 2,
            },
            "CONTEXT_OBJECTIVE_VERSION_MISMATCH",
        ),
        (
            {"selected_activity_id": "ACT-FIXTURE-BUTTERFLY-FOLD-PRINT"},
            "CONTEXT_ACTIVITY_REF_INCOMPLETE",
        ),
        (
            {"selected_objective_version": 1},
            "CONTEXT_OBJECTIVE_REF_INCOMPLETE",
        ),
    ],
)
def test_optional_selected_context_refs_block_before_fit(
    context_update: dict[str, object], expected_reason: str
) -> None:
    fixture = _butterfly_template()
    context = _context(fixture).model_copy(update=context_update)

    result = _fixture_compiler(fixture).compile(
        _anchor(), context, preferred_template_id=fixture.template_id
    )

    assert result.filter_result.status == "NO_ELIGIBLE_ACTIVITY"
    assert f"{fixture.activity_ref.id}:{expected_reason}" in result.filter_result.reason_codes
    assert result.fit_evaluation is None
    assert result.spec is None
    assert result.gate_b.status == "BLOCKED"


def test_matching_optional_selected_context_refs_pass() -> None:
    fixture = _butterfly_template()
    context = _context(fixture).model_copy(
        update={
            "selected_activity_id": fixture.activity_ref.id,
            "selected_activity_version": fixture.activity_ref.version,
            "selected_objective_id": fixture.objective_refs[0].id,
            "selected_objective_version": fixture.objective_refs[0].version,
        }
    )

    result = _fixture_compiler(fixture).compile(
        _anchor(), context, preferred_template_id=fixture.template_id
    )

    assert result.fit_evaluation is not None
    assert result.fit_evaluation.status == "PASS"
    assert result.gate_b.status == "APPROVED"


def test_gate_b_rechecks_context_selected_ref_drift() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    drifted_context = context.model_copy(
        update={
            "selected_activity_id": "ACT-WRONG",
            "selected_activity_version": 1,
        }
    )
    decision = compiler.approve_gate_b(result.spec, drifted_context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("CONTEXT_ACTIVITY_ID_MISMATCH",)


def test_compile_and_explicit_gate_b_share_one_approval_decision() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    rechecked = compiler.approve_gate_b(result.spec, context)

    assert result.gate_b == rechecked
    assert result.handoff is not None
    assert result.handoff.spec_ref == rechecked.spec_ref
    assert result.handoff.activity_ref == rechecked.activity_ref
    assert result.handoff.objective_ref == rechecked.objective_ref
    assert result.handoff.template_ref == rechecked.template_ref


def test_gate_b_blocks_spec_id_drift_before_hash_check() -> None:
    fixture = _butterfly_template()
    compiler = _fixture_compiler(fixture)
    context = _context(fixture)
    result = compiler.compile(_anchor(), context, preferred_template_id=fixture.template_id)
    assert result.spec is not None

    tampered = result.spec.model_copy(update={"spec_id": "SPEC-TAMPERED"})
    decision = compiler.approve_gate_b(tampered, context)

    assert decision.status == "BLOCKED"
    assert decision.reason_codes == ("SPEC_ID_MISMATCH",)
