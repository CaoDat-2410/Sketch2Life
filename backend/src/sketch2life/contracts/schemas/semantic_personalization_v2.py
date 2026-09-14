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
    review_status: Literal["PROVISIONAL_OWNER_REVIEWED", "SEMANTIC_REVIEWED", "DEMO_ELIGIBLE"]
    production_eligible: bool = False
    activity_family_id: str = ""
    variant_id: str = ""
    catalog_revision: str = "catalog-2026-09"

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
    matched_concept_ids: tuple[str, ...] = ()
    matched_phrases_vi: tuple[str, ...] = ()
    matched_anchor_labels_vi: tuple[str, ...] = ()
    evidence_claim_ids: tuple[str, ...] = Field(min_length=1)
    reason_codes: tuple[str, ...] = Field(min_length=1)
    fallback_reason: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_mode(self) -> SemanticActivityMatchV2:
        is_fallback = self.match_mode == "AGE_BASELINE_FALLBACK"
        if is_fallback and not self.fallback_reason:
            raise ValueError("baseline fallback requires fallback_reason")
        if not is_fallback and self.fallback_reason is not None:
            raise ValueError("personalized match cannot carry fallback_reason")
        return self


class AgeAdaptationV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    age_band: AgeBand
    age_months: int = Field(ge=0, le=155)
    abstraction_level: Literal["FOUNDATION", "CONCRETE", "ABSTRACT"]
    objective_adaptation_vi: str = Field(min_length=1, max_length=240)
    complexity_level: Literal["FOUNDATION", "STANDARD", "EXTENSION"]
    supervision_level: Literal["NONE", "NEARBY", "DIRECT"]
    duration_minutes: dict[str, int] | None = None


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
    "AgeAdaptationV2",
    "BackendWorkflowResultV2",
    "ConfirmedSceneUnderstandingV2",
    "ExperienceSpecV2",
    "SceneConceptV2",
    "SemanticActivityMatchV2",
    "SemanticActivityProfileV2",
    "WorkflowBandResultV2",
    "finalize_backend_workflow_result_v2",
]
