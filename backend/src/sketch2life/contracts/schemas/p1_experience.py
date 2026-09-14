"""Fixture-only P1 contracts for the FEAT-018 experience compiler.

The contracts in this module are deliberately provider-neutral.  They describe
the handoff between a confirmed observation and the curated P1 activity
catalog; they do not contain model prompts, provider endpoints, UI state, or
child data.  The revision-2 engine is approved for the P1 slice only, so these
contracts are kept in the backend package until the shared registry is frozen.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class P1ContractBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class VersionedRefV1(P1ContractBase):
    id: str = Field(min_length=1, max_length=120)
    version: int = Field(ge=1, le=999)


class AnchorProvenanceV1(P1ContractBase):
    source_artifact_id: str = Field(min_length=1, max_length=200)
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_contract_name: str = Field(min_length=1, max_length=120)
    source_contract_version: str = Field(min_length=1, max_length=40)
    source_claim_ids: tuple[str, ...] = ()


class SemanticAnchorV1(P1ContractBase):
    anchor_id: str = Field(min_length=1, max_length=120)
    kind: Literal["subject", "action", "visual_feature", "story"]
    original_label: str = Field(min_length=1, max_length=200)
    normalized_label: str = Field(min_length=1, max_length=200)
    semantic_tags: tuple[str, ...] = ()
    confidence: float = Field(ge=0, le=1)
    adult_confirmed: bool
    provenance: AnchorProvenanceV1

    @model_validator(mode="after")
    def require_confirmed_provenance(self) -> SemanticAnchorV1:
        if not self.adult_confirmed:
            raise ValueError("P1 requires an adult-confirmed anchor")
        if not self.provenance.source_claim_ids:
            raise ValueError("anchor provenance must retain source claim IDs")
        return self


class SemanticAnchorSetV1(P1ContractBase):
    contract_name: Literal["SemanticAnchorSetV1"] = "SemanticAnchorSetV1"
    contract_version: Literal["1.0"] = "1.0"
    anchor_set_id: str = Field(min_length=1, max_length=120)
    anchor_set_version: int = Field(default=1, ge=1)
    source_artifact_id: str = Field(min_length=1, max_length=200)
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    gate_a_status: Literal["CONFIRMED"]
    adult_confirmation_actor: Literal["CAREGIVER", "GUIDE", "PROJECT_OWNER"]
    primary_anchor: SemanticAnchorV1
    secondary_anchors: tuple[SemanticAnchorV1, ...] = ()
    adult_correction_label: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def require_source_match(self) -> SemanticAnchorSetV1:
        provenance = self.primary_anchor.provenance
        if provenance.source_artifact_id != self.source_artifact_id:
            raise ValueError("primary anchor source artifact does not match anchor set")
        if provenance.source_artifact_sha256 != self.source_artifact_sha256:
            raise ValueError("primary anchor source hash does not match anchor set")
        if any(
            anchor.anchor_id == self.primary_anchor.anchor_id for anchor in self.secondary_anchors
        ):
            raise ValueError("primary anchor cannot also be secondary")
        return self


class SemanticMatchEvidenceV1(P1ContractBase):
    contract_name: Literal["SemanticMatchEvidenceV1"] = "SemanticMatchEvidenceV1"
    contract_version: Literal["1.0"] = "1.0"
    match_mode: Literal["EXACT", "ALIAS", "SAFE_FALLBACK"]
    profile_id: str = Field(min_length=1, max_length=120)
    profile_version: int = Field(ge=1)
    score: int = Field(ge=0, le=100)
    matched_phrases_vi: tuple[str, ...] = ()
    matched_concept_ids: tuple[str, ...] = ()
    evidence_claim_ids: tuple[str, ...] = Field(min_length=1)
    reason_codes: tuple[str, ...] = ()
    fallback_reason: str | None = Field(default=None, max_length=160)

    @model_validator(mode="after")
    def validate_fallback_reason(self) -> SemanticMatchEvidenceV1:
        if self.match_mode == "SAFE_FALLBACK" and not self.fallback_reason:
            raise ValueError("safe fallback evidence requires fallback_reason")
        if self.match_mode != "SAFE_FALLBACK" and self.fallback_reason is not None:
            raise ValueError("exact/alias evidence cannot carry fallback_reason")
        return self


class P1ContextV1(P1ContractBase):
    """Adult-supplied eligibility context; never inferred from media."""

    contract_name: Literal["P1ContextV1"] = "P1ContextV1"
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=1)
    age_months: int | None = Field(default=None, ge=0, le=155)
    readiness_ids: tuple[str, ...] | None = None
    completed_activity_ids: tuple[str, ...] | None = None
    available_material_option_ids: tuple[str, ...] | None = None
    supervision_level: Literal["NONE", "NEARBY", "DIRECT"] | None = None
    policy_flags: tuple[str, ...] | None = None
    candidate_status: Literal["ACTIVE_FIXTURE", "INACTIVE_FIXTURE", "INACTIVE"] | None = None
    gate_a_confirmed: bool = False
    selected_activity_id: str | None = Field(default=None, max_length=120)
    selected_activity_version: int | None = Field(default=None, ge=1)
    selected_objective_id: str | None = Field(default=None, max_length=120)
    selected_objective_version: int | None = Field(default=None, ge=1)

    def missing_fields(self) -> tuple[str, ...]:
        required = (
            "age_months",
            "readiness_ids",
            "completed_activity_ids",
            "available_material_option_ids",
            "supervision_level",
            "policy_flags",
            "candidate_status",
        )
        return tuple(field for field in required if getattr(self, field) is None)


class LearningFocusV1(P1ContractBase):
    contract_name: Literal["LearningFocusV1"] = "LearningFocusV1"
    contract_version: Literal["1.0"] = "1.0"
    objective_ref: VersionedRefV1
    selected_anchor_id: str = Field(min_length=1, max_length=120)
    child_facing_goal_vi: str = Field(min_length=1, max_length=500)
    selection_policy_version: str = Field(min_length=1, max_length=40)
    rejected_alternatives: tuple[VersionedRefV1, ...] = ()
    provenance: Literal["P1_CURATED_CATALOG"] = "P1_CURATED_CATALOG"


class ActivityTemplateV1(P1ContractBase):
    contract_name: Literal["ActivityTemplateV1"] = "ActivityTemplateV1"
    contract_version: Literal["1.0"] = "1.0"
    template_id: str = Field(min_length=1, max_length=120)
    template_version: int = Field(ge=1)
    activity_ref: VersionedRefV1
    objective_refs: tuple[VersionedRefV1, ...] = Field(min_length=1)
    supported_anchor_labels: tuple[str, ...] = Field(min_length=1)
    supported_anchor_kinds: tuple[Literal["subject", "action", "visual_feature", "story"], ...]
    interaction_mode: Literal[
        "OBJECT_PERMANENCE",
        "TRANSFER",
        "SEQUENCE",
        "CARE",
        "SORTING",
        "TRACING",
        "OBSERVATION",
        "RESEARCH",
    ]
    age_months_min: int = Field(ge=0, le=155)
    age_months_max: int = Field(ge=0, le=155)
    readiness_ids: tuple[str, ...] = ()
    prerequisite_activity_ids: tuple[str, ...] = ()
    material_option_ids: tuple[str, ...] = Field(min_length=1)
    minimum_supervision: Literal["NONE", "NEARBY", "DIRECT"]
    policy_constraints: tuple[str, ...] = ()
    safety_rule_ids: tuple[str, ...] = Field(min_length=1)
    steps_vi: tuple[str, ...] = Field(min_length=1)
    personalization_slots: tuple[str, ...] = ()
    provenance_source: str = Field(min_length=1, max_length=240)
    provenance_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_status: Literal["PROVISIONAL_OWNER_REVIEWED"]
    production_eligible: Literal[False] = False

    @model_validator(mode="after")
    def validate_age_range(self) -> ActivityTemplateV1:
        if self.age_months_max < self.age_months_min:
            raise ValueError("template age max must be >= min")
        return self


class MediaContinuityPlanV1(P1ContractBase):
    consumer: Literal["VIDEO", "ORIGINAL_ART_ANIMATION"]
    source_artifact_id: str = Field(min_length=1, max_length=200)
    anchor_id: str = Field(min_length=1, max_length=120)
    objective_ref: VersionedRefV1
    template_ref: VersionedRefV1
    continuity_requirements: tuple[str, ...] = Field(min_length=1)


class ActivityPlanV1(P1ContractBase):
    activity_ref: VersionedRefV1
    template_ref: VersionedRefV1
    objective_ref: VersionedRefV1
    material_option_ids: tuple[str, ...] = Field(min_length=1)
    presentation_steps_vi: tuple[str, ...] = Field(min_length=1)
    safety_rule_ids: tuple[str, ...] = Field(min_length=1)


class BridgeSentenceV1(P1ContractBase):
    contract_name: Literal["BridgeSentenceV1"] = "BridgeSentenceV1"
    contract_version: Literal["1.0"] = "1.0"
    sentence_vi: str = Field(min_length=1, max_length=500)
    anchor_id: str = Field(min_length=1, max_length=120)
    objective_ref: VersionedRefV1
    template_ref: VersionedRefV1


class ActivityFitEvaluationV1(P1ContractBase):
    contract_name: Literal["ActivityFitEvaluationV1"] = "ActivityFitEvaluationV1"
    contract_version: Literal["1.0"] = "1.0"
    status: Literal["PASS", "REJECT", "BLOCKED"]
    drawing_relevance: int = Field(ge=0, le=100)
    objective_alignment: int = Field(ge=0, le=100)
    video_continuity: int = Field(ge=0, le=100)
    montessori_safety: int = Field(ge=0, le=100)
    total_score: int = Field(ge=0, le=100)
    threshold: int = Field(default=80, ge=0, le=100)
    reason_codes: tuple[str, ...] = ()
    evaluated_template_ref: VersionedRefV1
    evaluated_catalog_ref: VersionedRefV1

    @model_validator(mode="after")
    def validate_score(self) -> ActivityFitEvaluationV1:
        weighted = round(
            self.drawing_relevance * 0.30
            + self.objective_alignment * 0.35
            + self.video_continuity * 0.20
            + self.montessori_safety * 0.15
        )
        if weighted != self.total_score:
            raise ValueError(f"total_score must equal weighted score {weighted}")
        if self.status == "PASS" and self.total_score < self.threshold:
            raise ValueError("PASS fit evaluation must meet threshold")
        if self.status == "REJECT" and self.total_score >= self.threshold:
            raise ValueError("REJECT fit evaluation must be below threshold")
        return self


class ExperienceSpecV1(P1ContractBase):
    contract_name: Literal["ExperienceSpecV1"] = "ExperienceSpecV1"
    contract_version: Literal["1.0"] = "1.0"
    spec_id: str = Field(min_length=1, max_length=120)
    spec_version: int = Field(ge=1)
    session_id: str = Field(min_length=1, max_length=120)
    source_artifact_id: str = Field(min_length=1, max_length=200)
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    anchor_set: SemanticAnchorSetV1
    learning_focus: LearningFocusV1
    activity_template: ActivityTemplateV1
    video_plan: MediaContinuityPlanV1
    animation_plan: MediaContinuityPlanV1
    activity_plan: ActivityPlanV1
    bridge_sentence: BridgeSentenceV1
    fit_evaluation: ActivityFitEvaluationV1
    semantic_match: SemanticMatchEvidenceV1 | None = None
    policy_versions: tuple[str, ...] = Field(min_length=1)
    spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_identity_continuity(self) -> ExperienceSpecV1:
        template_ref = VersionedRefV1(
            id=self.activity_template.template_id, version=self.activity_template.template_version
        )
        activity_ref = self.activity_template.activity_ref
        objective_ref = self.learning_focus.objective_ref
        if self.anchor_set.primary_anchor.anchor_id != self.learning_focus.selected_anchor_id:
            raise ValueError("learning focus anchor must be the confirmed primary anchor")
        consumers = (self.video_plan, self.animation_plan)
        for plan in consumers:
            if (
                plan.source_artifact_id != self.source_artifact_id
                or plan.anchor_id != self.learning_focus.selected_anchor_id
                or plan.objective_ref != objective_ref
                or plan.template_ref != template_ref
            ):
                raise ValueError("downstream plan identity diverges from ExperienceSpec")
        if (
            self.activity_plan.activity_ref != activity_ref
            or self.activity_plan.objective_ref != objective_ref
            or self.activity_plan.template_ref != template_ref
        ):
            raise ValueError("activity plan identity diverges from ExperienceSpec")
        if (
            self.bridge_sentence.anchor_id != self.learning_focus.selected_anchor_id
            or self.bridge_sentence.objective_ref != objective_ref
            or self.bridge_sentence.template_ref != template_ref
        ):
            raise ValueError("bridge sentence identity diverges from ExperienceSpec")
        if (
            self.fit_evaluation.evaluated_template_ref != template_ref
            or self.fit_evaluation.evaluated_catalog_ref != activity_ref
        ):
            raise ValueError("fit evaluation identity diverges from ExperienceSpec")
        return self


class P1FilterResultV1(P1ContractBase):
    contract_name: Literal["P1FilterResultV1"] = "P1FilterResultV1"
    contract_version: Literal["1.0"] = "1.0"
    status: Literal[
        "VALID_CANDIDATE",
        "MISSING_CONTEXT",
        "NO_ELIGIBLE_ACTIVITY",
        "UNKNOWN_ANCHOR",
        "AMBIGUOUS_ANCHOR",
        "CONFLICTING_ANCHOR",
    ]
    activity_ref: VersionedRefV1 | None = None
    objective_ref: VersionedRefV1 | None = None
    template_ref: VersionedRefV1 | None = None
    reason_codes: tuple[str, ...] = ()
    candidate_refs: tuple[VersionedRefV1, ...] = ()


class IntegrationGateDecisionV1(P1ContractBase):
    contract_name: Literal["IntegrationGateDecisionV1"] = "IntegrationGateDecisionV1"
    contract_version: Literal["1.0"] = "1.0"
    gate: Literal["B"] = "B"
    status: Literal["APPROVED", "BLOCKED"]
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=1)
    activity_ref: VersionedRefV1 | None = None
    objective_ref: VersionedRefV1 | None = None
    template_ref: VersionedRefV1 | None = None
    spec_ref: VersionedRefV1 | None = None
    reason_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_approval_identity(self) -> IntegrationGateDecisionV1:
        refs = (self.activity_ref, self.objective_ref, self.template_ref, self.spec_ref)
        if self.status == "APPROVED" and any(ref is None for ref in refs):
            raise ValueError("approved Gate B requires activity/objective/template/spec refs")
        return self


class ActivityHandoffV1(P1ContractBase):
    contract_name: Literal["ActivityHandoffV1"] = "ActivityHandoffV1"
    contract_version: Literal["1.0"] = "1.0"
    status: Literal["READY", "BLOCKED"]
    session_id: str = Field(min_length=1, max_length=120)
    spec_ref: VersionedRefV1
    activity_ref: VersionedRefV1
    objective_ref: VersionedRefV1
    template_ref: VersionedRefV1
    reason_codes: tuple[str, ...] = ()
