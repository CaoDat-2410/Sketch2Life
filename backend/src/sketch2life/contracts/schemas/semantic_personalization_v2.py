"""V2 contracts for stable scene understanding and mode-aware personalization."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from json import dumps
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.workflow_demo import (
    AgeBand,
    AgeMatrixSummaryV1,
    BackendWorkflowResultV1,
    WorkflowStatus,
    WorkflowTerminalStatus,
)


class SceneConceptV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    concept_id: str = Field(min_length=1, max_length=120)
    label_vi: str = Field(min_length=1, max_length=160)
    parent_concept_ids: tuple[str, ...] = ()
    confidence: float = Field(ge=0, le=1)
    concept_role: Literal[
        "PRIMARY_CHILD_INTEREST",
        "PRIMARY_VISUAL",
        "SECONDARY_CHILD_INTEREST",
        "SECONDARY_VISUAL",
        "UNCLASSIFIED",
    ] = "SECONDARY_VISUAL"
    child_interest_alignment: float = Field(default=0.0, ge=0, le=1)
    evidence_claim_ids: tuple[str, ...] = Field(min_length=1)
    source_kinds: tuple[Literal["ASR", "VLM", "FUSION"], ...] = Field(min_length=1)


class ConfirmedSceneUnderstandingV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["ConfirmedSceneUnderstandingV2"] = "ConfirmedSceneUnderstandingV2"
    contract_version: Literal["2.0"] = "2.0"
    scene_understanding_id: str = Field(min_length=1, max_length=120)
    source_image_artifact_ref: str = Field(min_length=1, max_length=500)
    source_image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_audio_artifact_ref: str = Field(min_length=1, max_length=500)
    source_audio_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    gate_a_status: Literal["CONFIRMED", "UNAVAILABLE"] = "CONFIRMED"
    adult_confirmation_actor: Literal[
        "CAREGIVER",
        "GUIDE",
        "PROJECT_OWNER",
    ] | None = "PROJECT_OWNER"
    primary_anchor_label_vi: str = Field(min_length=1, max_length=240)
    primary_concept: SceneConceptV2
    secondary_concepts: tuple[SceneConceptV2, ...] = ()
    child_interest_concept_id: str | None = Field(default=None, max_length=120)
    asr_vlm_resolution: Literal[
        "ASR_AND_VLM_AGREE",
        "ASR_PRIMARY_VLM_SUPPORTS",
        "ASR_VLM_CONFLICT",
        "VLM_ONLY",
        "ASR_UNAVAILABLE",
    ] = "ASR_UNAVAILABLE"
    observed_anchor_labels_vi: tuple[str, ...] = Field(min_length=1)
    observed_entity_labels_vi: tuple[str, ...] = ()
    observed_action_labels_vi: tuple[str, ...] = ()
    observed_theme_labels_vi: tuple[str, ...] = ()
    asr_transcript_vi: str = ""
    supported_modalities: tuple[Literal["ASR", "VLM"], ...] = Field(min_length=1)
    conflict_preserved: bool = True
    normalization_policy_version: str = Field(min_length=1, max_length=80)
    scene_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class SemanticActivityProfileV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["SemanticActivityProfileV2"] = "SemanticActivityProfileV2"
    contract_version: Literal["2.0"] = "2.0"
    profile_id: str = Field(min_length=1, max_length=120)
    profile_version: int = Field(ge=1)
    activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    activity_version: int = Field(ge=1)
    age_band: AgeBand
    concept_ids: tuple[str, ...] = Field(min_length=1)
    parent_concept_ids: tuple[str, ...] = ()
    exact_phrases_vi: tuple[str, ...] = Field(min_length=1)
    aliases_vi: tuple[str, ...] = ()
    negative_phrases_vi: tuple[str, ...] = ()
    fallback_tier: Literal["NONE", "AGE_BASELINE"] = "NONE"
    provenance_source: str = Field(min_length=1, max_length=240)
    provenance_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    review_status: Literal[
        "PROVISIONAL_OWNER_REVIEWED",
        "SEMANTIC_REVIEWED",
        "DEMO_ELIGIBLE",
        "OWNER_REVIEWED",
        "PRODUCTION_APPROVED",
        "DEPRECATED",
        "BLOCKED",
    ]
    production_eligible: bool = False
    activity_family_id: str = ""
    variant_id: str = ""
    catalog_revision: str = "catalog-2026-09"
    primary_objective_id: str = Field(min_length=1, max_length=120)
    secondary_objective_ids: tuple[str, ...] = ()
    pedagogical_alignment_status: Literal[
        "DEMO_REVIEWED",
        "OWNER_REVIEWED",
        "PRODUCTION_APPROVED",
    ] = "DEMO_REVIEWED"
    pedagogical_observable_behavior_vi: str = Field(
        default="Hoạt động có hành vi quan sát được phù hợp mục tiêu.",
        min_length=1,
        max_length=500,
    )
    continuity_mode: Literal["DIRECT_CONTINUATION", "RELATED_EXPANSION"] = (
        "DIRECT_CONTINUATION"
    )
    expansion_bridge_required: bool = False
    direct_observation_concept_ids: tuple[str, ...] = ()
    age_specific_goal_vi: str = Field(
        default="Trẻ thực hiện một hành vi quan sát được phù hợp lứa tuổi.",
        min_length=1,
        max_length=500,
    )
    video_setup_vi: str = Field(
        default="Chuẩn bị một không gian yên tĩnh và vật liệu an toàn.",
        min_length=1,
        max_length=500,
    )
    video_focus_cues_vi: tuple[str, ...] = Field(
        default=("Theo dõi chi tiết chính trong tranh.",), min_length=1, max_length=5
    )
    video_handoff_prompt_vi: str = Field(
        default="Bây giờ cùng người lớn thử hoạt động này.",
        min_length=1,
        max_length=500,
    )
    offscreen_instruction_vi: str = Field(
        default="Thực hiện hoạt động ngoài màn hình cùng người lớn.",
        min_length=1,
        max_length=800,
    )

    @model_validator(mode="after")
    def validate_production_state(self) -> SemanticActivityProfileV2:
        if self.production_eligible != (self.review_status == "PRODUCTION_APPROVED"):
            raise ValueError(
                "production_eligible must be true only for PRODUCTION_APPROVED profiles"
            )
        if self.primary_objective_id in self.secondary_objective_ids:
            raise ValueError("primary objective cannot also be secondary")
        if self.continuity_mode == "RELATED_EXPANSION" and not self.expansion_bridge_required:
            raise ValueError("related expansion profiles require expansion_bridge_required=true")
        return self

class SemanticActivityMatchV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["SemanticActivityMatchV2"] = "SemanticActivityMatchV2"
    contract_version: Literal["2.0"] = "2.0"
    match_mode: Literal[
        "PERSONALIZED_EXACT",
        "PERSONALIZED_ALIAS",
        "PERSONALIZED_CONCEPT",
        "AGE_BASELINE_FALLBACK",
    ]
    profile_id: str = Field(min_length=1, max_length=120)
    profile_version: int = Field(ge=1)
    activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    activity_version: int = Field(ge=1)
    activity_family_id: str = ""
    variant_id: str = ""
    catalog_revision: str = "catalog-2026-09"
    semantic_relevance: int = Field(ge=0, le=100)
    selected_concept_id: str | None = Field(default=None, max_length=120)
    selected_concept_role: Literal[
        "PRIMARY_CHILD_INTEREST",
        "PRIMARY_VISUAL",
        "SECONDARY_CHILD_INTEREST",
        "SECONDARY_VISUAL",
        "UNCLASSIFIED",
    ] | None = None
    concept_match_confidence: float = Field(default=0.0, ge=0, le=1)
    child_interest_alignment: float = Field(default=0.0, ge=0, le=1)
    age_fit_score: float = Field(default=1.0, ge=0, le=1)
    activity_safety_score: float = Field(default=1.0, ge=0, le=1)
    catalog_quality_score: float = Field(default=0.0, ge=0, le=1)
    overall_personalization_score: float = Field(default=0.0, ge=0, le=1)
    selected_objective_id: str | None = Field(default=None, max_length=120)
    objective_activity_alignment: float = Field(default=0.0, ge=0, le=1)
    matched_objective_ids: tuple[str, ...] = ()
    matched_concept_ids: tuple[str, ...] = ()
    matched_phrases_vi: tuple[str, ...] = ()
    matched_anchor_labels_vi: tuple[str, ...] = ()
    evidence_claim_ids: tuple[str, ...] = Field(min_length=1)
    reason_codes: tuple[str, ...] = Field(min_length=1)
    fallback_reason: str | None = Field(default=None, max_length=200)
    continuity_mode: Literal["DIRECT_CONTINUATION", "RELATED_EXPANSION"] = (
        "DIRECT_CONTINUATION"
    )
    planned_video_continuity_score: float = Field(default=0.0, ge=0, le=1)
    expansion_bridge_required: bool = False
    age_specific_goal_vi: str = Field(
        default="Trẻ thực hiện một hành vi quan sát được phù hợp lứa tuổi.",
        min_length=1,
        max_length=500,
    )
    video_setup_vi: str = Field(
        default="Chuẩn bị một không gian yên tĩnh và vật liệu an toàn.",
        min_length=1,
        max_length=500,
    )
    video_focus_cues_vi: tuple[str, ...] = Field(
        default=("Theo dõi chi tiết chính trong tranh.",), min_length=1, max_length=5
    )
    video_handoff_prompt_vi: str = Field(
        default="Bây giờ cùng người lớn thử hoạt động này.",
        min_length=1,
        max_length=500,
    )
    offscreen_instruction_vi: str = Field(
        default="Thực hiện hoạt động ngoài màn hình cùng người lớn.",
        min_length=1,
        max_length=800,
    )

    @model_validator(mode="after")
    def validate_mode(self) -> SemanticActivityMatchV2:
        is_fallback = self.match_mode == "AGE_BASELINE_FALLBACK"
        if is_fallback and not self.fallback_reason:
            raise ValueError("baseline fallback requires fallback_reason")
        if not is_fallback and self.fallback_reason is not None:
            raise ValueError("personalized match cannot carry fallback_reason")
        return self


class RankingTraceEntryV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rank: int = Field(ge=1, le=5)
    activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    activity_version: int = Field(ge=1)
    activity_family_id: str = Field(min_length=1, max_length=120)
    variant_id: str = Field(min_length=1, max_length=160)
    catalog_revision: str = Field(min_length=1, max_length=120)
    selected_concept_id: str | None = Field(default=None, max_length=120)
    semantic_score: int = Field(ge=0, le=100)
    child_interest_alignment: float = Field(ge=0, le=1)
    objective_activity_alignment: float = Field(ge=0, le=1)
    age_fit_score: float = Field(ge=0, le=1)
    activity_safety_score: float = Field(ge=0, le=1)
    catalog_quality_score: float = Field(ge=0, le=1)
    diversity_recency_penalty: float = Field(ge=0, le=1)
    final_score: float = Field(ge=0, le=1)
    score_breakdown: dict[str, float] = {}
    filter_status: Literal["PASS"] = "PASS"
    reason_codes: tuple[str, ...] = ()
    selected: bool = False
    lost_to_selected_because: Literal[
        "LOWER_SELECTION_RANK",
        "SAME_SELECTION_RANK_RANDOMIZED_OR_NON_REPEAT_POLICY",
    ] | None = None


class RejectedCandidateEvidenceV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    template_id: str = Field(min_length=1, max_length=160)
    filter_status: Literal["REJECT"] = "REJECT"
    reason_codes: tuple[str, ...] = Field(min_length=1)


class RankingDebugEvidenceV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["RankingDebugEvidenceV2"] = "RankingDebugEvidenceV2"
    contract_version: Literal["2.0"] = "2.0"
    visibility: Literal["BACKEND_DEBUG_ONLY"] = "BACKEND_DEBUG_ONLY"
    top_k: Literal[5] = 5
    selected_activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    selected_activity_family_id: str = Field(min_length=1, max_length=120)
    ranking_trace: tuple[RankingTraceEntryV2, ...] = Field(min_length=1, max_length=5)
    rejected_candidates: tuple[RejectedCandidateEvidenceV2, ...] = ()


class AgeAdaptationV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    age_band: AgeBand
    age_months: int = Field(ge=0, le=155)
    abstraction_level: Literal["FOUNDATION", "CONCRETE", "ABSTRACT"]
    objective_adaptation_vi: str = Field(min_length=1, max_length=240)
    complexity_level: Literal["FOUNDATION", "STANDARD", "EXTENSION"]
    supervision_level: Literal["NONE", "NEARBY", "DIRECT"]
    duration_minutes: dict[str, int] | None = None
    duration_spec: ActivityDurationV2 | None = None


class ExperienceContinuityV2(BaseModel):
    """Separates a planned video setup from a post-render assessment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    continuity_mode: Literal["DIRECT_CONTINUATION", "RELATED_EXPANSION"]
    drawing_video_planned_score: int = Field(ge=0, le=100)
    drawing_activity_planned_score: int = Field(ge=0, le=100)
    video_activity_planned_score: int = Field(ge=0, le=100)
    age_fit_score: int = Field(ge=0, le=100)
    objective_fit_score: int = Field(ge=0, le=100)
    safety_score: int = Field(ge=0, le=100)
    planned_overall_score: int = Field(ge=0, le=100)
    planned_video_continuity_score: float = Field(ge=0, le=1)
    actual_video_continuity_score: float | None = Field(default=None, ge=0, le=1)
    actual_video_status: Literal["NOT_RENDERED", "ASSESSED", "FAILED"] = "NOT_RENDERED"
    actual_video_artifact_ref: str | None = Field(default=None, min_length=1, max_length=500)
    bridge_required: bool = False
    reason_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_actual_assessment(self) -> ExperienceContinuityV2:
        if self.actual_video_status == "NOT_RENDERED":
            if self.actual_video_continuity_score is not None:
                raise ValueError("not-rendered video cannot have an actual continuity score")
            if self.actual_video_artifact_ref is not None:
                raise ValueError("not-rendered video cannot have an artifact reference")
        elif self.actual_video_continuity_score is None:
            raise ValueError("assessed or failed video must carry an actual continuity score")
        if self.continuity_mode == "RELATED_EXPANSION" and not self.bridge_required:
            raise ValueError("related expansion requires an explicit bridge")
        return self


class ActivityBridgeV2(BaseModel):
    """Age-specific handoff from planned video context to the real activity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    age_band: AgeBand
    continuity_mode: Literal["DIRECT_CONTINUATION", "RELATED_EXPANSION"]
    setup_instruction_vi: str = Field(min_length=1, max_length=500)
    focus_cues_vi: tuple[str, ...] = Field(min_length=1, max_length=5)
    handoff_prompt_vi: str = Field(min_length=1, max_length=500)
    offscreen_instruction_vi: str = Field(min_length=1, max_length=800)
    bridge_status: Literal["READY", "REQUIRES_HUMAN_SETUP", "UNAVAILABLE"]


class ActivityDurationV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    duration_type: Literal["SINGLE_SESSION", "MULTI_DAY"]
    min_minutes: int | None = Field(default=None, ge=1, le=1440)
    max_minutes: int | None = Field(default=None, ge=1, le=1440)
    initial_session_minutes: int | None = Field(default=None, ge=1, le=1440)
    daily_observation_minutes: int | None = Field(default=None, ge=1, le=1440)
    min_days: int | None = Field(default=None, ge=1, le=365)
    max_days: int | None = Field(default=None, ge=1, le=365)

    @model_validator(mode="after")
    def validate_shape(self) -> ActivityDurationV2:
        if self.duration_type == "SINGLE_SESSION":
            if self.min_minutes is None or self.max_minutes is None:
                raise ValueError("single-session duration requires min/max minutes")
            if self.max_minutes < self.min_minutes:
                raise ValueError("single-session max must be >= min")
            if any(
                value is not None
                for value in (
                    self.initial_session_minutes,
                    self.daily_observation_minutes,
                    self.min_days,
                    self.max_days,
                )
            ):
                raise ValueError("single-session duration cannot contain multi-day fields")
        else:
            if any(
                value is None
                for value in (
                    self.initial_session_minutes,
                    self.daily_observation_minutes,
                    self.min_days,
                    self.max_days,
                )
            ):
                raise ValueError("multi-day duration requires session, daily and day bounds")
            assert self.min_days is not None and self.max_days is not None
            if self.max_days < self.min_days:
                raise ValueError("multi-day max_days must be >= min_days")
            if self.min_minutes is not None or self.max_minutes is not None:
                raise ValueError("multi-day duration cannot use single-session min/max fields")
        return self


class ExperienceSpecV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["ExperienceSpecV2"] = "ExperienceSpecV2"
    contract_version: Literal["2.0"] = "2.0"
    spec_id: str = Field(min_length=1, max_length=160)
    session_id: str = Field(min_length=1, max_length=120)
    scene_understanding_id: str = Field(min_length=1, max_length=120)
    activity_ref: dict[str, Any]
    objective_ref: dict[str, Any]
    experience_mode: Literal["PERSONALIZED", "AGE_BASELINE_FALLBACK"]
    semantic_match: SemanticActivityMatchV2
    age_adaptation: AgeAdaptationV2
    gate_b_status: Literal["PERSONALIZED_APPROVED", "BASELINE_APPROVED", "BLOCKED"]
    bridge_sentence_vi: str = Field(min_length=1, max_length=300)
    continuity: ExperienceContinuityV2 | None = None
    activity_bridge: ActivityBridgeV2 | None = None
    story_mode: Literal["SCENE_GROUNDED", "AGE_BASELINE"]
    legacy_spec: dict[str, Any]
    spec_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_gate_mode(self) -> ExperienceSpecV2:
        activity_id = self.activity_ref.get("id")
        activity_version = self.activity_ref.get("version")
        if activity_id != self.semantic_match.activity_id:
            raise ValueError("activity_ref and semantic_match activity IDs must match")
        if activity_version != self.semantic_match.activity_version:
            raise ValueError("activity_ref and semantic_match activity versions must match")
        legacy_activity = (
            self.legacy_spec.get("activity_template", {}).get("activity_ref", {})
            if isinstance(self.legacy_spec.get("activity_template"), dict)
            else {}
        )
        if legacy_activity:
            if legacy_activity.get("id") != activity_id:
                raise ValueError("legacy projection activity ID diverges from V2")
            if legacy_activity.get("version") != activity_version:
                raise ValueError("legacy projection activity version diverges from V2")
        if self.experience_mode == "PERSONALIZED" and self.gate_b_status != "PERSONALIZED_APPROVED":
            raise ValueError("personalized experience requires PERSONALIZED_APPROVED")
        if (
            self.experience_mode == "AGE_BASELINE_FALLBACK"
            and self.gate_b_status != "BASELINE_APPROVED"
        ):
            raise ValueError("baseline fallback requires BASELINE_APPROVED")
        if self.experience_mode == "PERSONALIZED" and self.story_mode != "SCENE_GROUNDED":
            raise ValueError("personalized experience requires scene-grounded story mode")
        if (
            self.experience_mode == "AGE_BASELINE_FALLBACK"
            and self.story_mode != "AGE_BASELINE"
        ):
            raise ValueError("fallback experience requires age-baseline story mode")
        return self


class WorkflowBandResultV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    age_band: AgeBand
    age_months: int = Field(ge=0, le=155)
    status: WorkflowStatus
    terminal_status: WorkflowTerminalStatus
    experience_mode: Literal["PERSONALIZED", "AGE_BASELINE_FALLBACK", "UNAVAILABLE"] | None = None
    scene_understanding_id: str = Field(min_length=1, max_length=120)
    semantic_relevance: int | None = Field(default=None, ge=0, le=100)
    selected_concept_id: str | None = Field(default=None, max_length=120)
    child_interest_alignment: float | None = Field(default=None, ge=0, le=1)
    unavailable_reason_code: str | None = Field(default=None, max_length=120)
    experience_spec: ExperienceSpecV2 | None = None
    legacy_band: dict[str, Any]
    warnings: tuple[str, ...] = ()


class BackendWorkflowResultV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["BackendWorkflowResultV2"] = "BackendWorkflowResultV2"
    contract_version: Literal["2.0"] = "2.0"
    workflow_run_id: str = Field(min_length=1, max_length=120)
    status: WorkflowStatus
    terminal_status: WorkflowTerminalStatus
    input_mode: Literal["MULTIMODAL"] = "MULTIMODAL"
    scene_understanding: ConfirmedSceneUnderstandingV2
    age_matrix_summary: AgeMatrixSummaryV1
    age_bands: tuple[WorkflowBandResultV2, ...] = Field(min_length=1)
    personalized_band_count: int = Field(ge=0)
    fallback_band_count: int = Field(ge=0)
    unavailable_age_bands: tuple[AgeBand, ...] = ()
    legacy_result: BackendWorkflowResultV1
    created_at: datetime
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_band_counts(self) -> BackendWorkflowResultV2:
        selected_count = sum(
            band.experience_mode in {"PERSONALIZED", "AGE_BASELINE_FALLBACK"}
            for band in self.age_bands
        )
        if self.personalized_band_count + self.fallback_band_count != selected_count:
            raise ValueError("V2 band mode counts do not match band results")
        return self

    @model_validator(mode="after")
    def validate_manifest_hash(self) -> BackendWorkflowResultV2:
        payload = self.model_dump(mode="json")
        recorded = payload.pop("manifest_sha256")
        expected = _canonical_hash(payload)
        if recorded != expected:
            raise ValueError("V2 manifest hash mismatch")
        return self


def _canonical_hash(value: object) -> str:
    encoded = dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def finalize_backend_workflow_result_v2(payload: dict[str, Any]) -> BackendWorkflowResultV2:
    unsigned = dict(payload)
    unsigned.pop("manifest_sha256", None)
    normalized = BackendWorkflowResultV2.model_construct(
        **unsigned,
        manifest_sha256="0" * 64,
    ).model_dump(mode="json", warnings=False)
    normalized.pop("manifest_sha256", None)
    return BackendWorkflowResultV2.model_validate(
        {**normalized, "manifest_sha256": _canonical_hash(normalized)}
    )


__all__ = [
    "ActivityBridgeV2",
    "ActivityDurationV2",
    "AgeAdaptationV2",
    "BackendWorkflowResultV2",
    "ConfirmedSceneUnderstandingV2",
    "ExperienceSpecV2",
    "ExperienceContinuityV2",
    "SceneConceptV2",
    "SemanticActivityMatchV2",
    "SemanticActivityProfileV2",
    "RankingDebugEvidenceV2",
    "RankingTraceEntryV2",
    "RejectedCandidateEvidenceV2",
    "WorkflowBandResultV2",
    "finalize_backend_workflow_result_v2",
]
