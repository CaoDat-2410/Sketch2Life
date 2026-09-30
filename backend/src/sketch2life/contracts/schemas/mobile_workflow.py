"""Versioned mobile/backend transport envelopes for the supervised workflow."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MobileWorkflowCommandV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["MobileWorkflowCommandV1"] = "MobileWorkflowCommandV1"
    contract_version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=200)
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=0)
    actor_ref: str = Field(min_length=1, max_length=160)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any]

    @model_validator(mode="after")
    def require_timezone_aware_timestamp(self) -> MobileWorkflowCommandV1:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return self


class WorkflowResultProvenanceV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["WorkflowResultProvenanceV1"] = "WorkflowResultProvenanceV1"
    contract_version: Literal["1.0"] = "1.0"
    producer: Literal["APPLICATION", "HUMAN", "VISION", "ASR", "P1", "PIXI", "P4"]
    component: str = Field(min_length=1, max_length=120)
    component_version: str = Field(min_length=1, max_length=40)
    source_contracts: tuple[str, ...] = ()


class WorkflowFailureV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["WorkflowFailureV1"] = "WorkflowFailureV1"
    contract_version: Literal["1.0"] = "1.0"
    domain: Literal["TRANSPORT", "SESSION", "MEDIA", "AI", "P1", "GATE", "PIXI", "P4"]
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,79}$")
    retryable: bool
    safe_message: str = Field(min_length=1, max_length=240)


class ActivityRecommendationCardV1(BaseModel):
    """Adult-readable, bounded activity choice derived from reviewed catalog data."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["ActivityRecommendationCardV1"] = (
        "ActivityRecommendationCardV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    priority: int = Field(ge=1, le=3)
    activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    activity_version: int = Field(ge=1)
    title_vi: str = Field(min_length=1, max_length=160)
    summary_vi: str = Field(min_length=1, max_length=500)
    match_reason_vi: str = Field(min_length=1, max_length=300)
    duration_minutes: int = Field(ge=1, le=240)
    age_label_vi: str = Field(min_length=1, max_length=80)
    supervision_label_vi: str = Field(min_length=1, max_length=120)
    material_labels_vi: tuple[str, ...] = Field(default=(), max_length=4)
    preparation_requirement: Literal[
        "NO_PRINTABLE_ASSET",
        "PRINT_RECOMMENDED",
        "PRINT_REQUIRED",
    ] = "NO_PRINTABLE_ASSET"
    preparation_summary_vi: str = Field(default="", max_length=320)
    preparation_asset_kinds: tuple[str, ...] = Field(default=(), max_length=4)
    preparation_asset_status: Literal[
        "NOT_APPLICABLE",
        "PLANNED",
        "READY",
        "BLOCKED",
        "DEPRECATED",
    ] = "NOT_APPLICABLE"
    fit_source: Literal["DIRECT", "RELATED"]


class ActivityRecommendationSetV1(BaseModel):
    """Versioned additive read model; the frozen P1 option contract stays intact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["ActivityRecommendationSetV1"] = (
        "ActivityRecommendationSetV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    topic_label_vi: str = Field(min_length=1, max_length=240)
    options: tuple[ActivityRecommendationCardV1, ...] = Field(max_length=3)


class ActivityRecommendationCardV2(BaseModel):
    """One reviewed activity in the complete topic-and-age discovery set."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["ActivityRecommendationCardV2"] = "ActivityRecommendationCardV2"
    contract_version: Literal["2.0"] = "2.0"
    priority: int = Field(ge=1)
    activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    activity_version: int = Field(ge=1)
    template_id: str = Field(min_length=1, max_length=120)
    template_version: int = Field(ge=1)
    title_vi: str = Field(min_length=1, max_length=160)
    summary_vi: str = Field(min_length=1, max_length=500)
    match_reason_vi: str = Field(min_length=1, max_length=300)
    duration_minutes: int = Field(ge=1, le=240)
    age_label_vi: str = Field(min_length=1, max_length=80)
    minimum_supervision: Literal["NONE", "NEARBY", "DIRECT"]
    supervision_label_vi: str = Field(min_length=1, max_length=120)
    material_labels_vi: tuple[str, ...] = Field(default=(), max_length=48)
    policy_constraints: tuple[str, ...] = Field(default=(), max_length=24)
    fit_source: Literal["DIRECT", "RELATED"]


class ActivityRecommendationSetV2(BaseModel):
    """Complete reviewed topic+age result set; unlike V1 this is not top-three bounded."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["ActivityRecommendationSetV2"] = "ActivityRecommendationSetV2"
    contract_version: Literal["2.0"] = "2.0"
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=1)
    age_months: int = Field(ge=0, le=155)
    confirmed_anchor_label: str = Field(min_length=1, max_length=200)
    topic_label_vi: str = Field(min_length=1, max_length=240)
    total_count: int = Field(ge=0)
    options: tuple[ActivityRecommendationCardV2, ...]

    @model_validator(mode="after")
    def validate_complete_ordered_set(self) -> ActivityRecommendationSetV2:
        if self.total_count != len(self.options):
            raise ValueError("total_count must equal the complete option count")
        activity_ids = [option.activity_id for option in self.options]
        if len(activity_ids) != len(set(activity_ids)):
            raise ValueError("activity suggestion IDs must be unique")
        if [option.priority for option in self.options] != list(range(1, len(self.options) + 1)):
            raise ValueError("activity priority must enumerate the complete ordered set")
        return self


class ActivityRecommendationSetV3(BaseModel):
    """Full eligible list plus an explicit diagnosis when the list is empty."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["ActivityRecommendationSetV3"] = "ActivityRecommendationSetV3"
    contract_version: Literal["3.0"] = "3.0"
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=1)
    age_months: int = Field(ge=0, le=155)
    confirmed_anchor_label: str = Field(min_length=1, max_length=200)
    topic_label_vi: str = Field(min_length=1, max_length=240)
    total_count: int = Field(ge=0)
    options: tuple[ActivityRecommendationCardV2, ...]
    empty_reason: Literal[
        "TOPIC_UNMAPPED",
        "NO_RELEVANT_ACTIVITY_FOR_AGE",
        "RELEVANT_ACTIVITY_BLOCKED_BY_SAFETY_OR_ADULT_PRESENCE",
        "CATALOG_CARD_NOT_DISPLAYABLE",
    ] | None = None

    @model_validator(mode="after")
    def validate_complete_ordered_set(self) -> ActivityRecommendationSetV3:
        if self.total_count != len(self.options):
            raise ValueError("total_count must equal the complete option count")
        activity_ids = [option.activity_id for option in self.options]
        if len(activity_ids) != len(set(activity_ids)):
            raise ValueError("activity suggestion IDs must be unique")
        if [option.priority for option in self.options] != list(range(1, len(self.options) + 1)):
            raise ValueError("activity priority must enumerate the complete ordered set")
        if (self.total_count == 0) != (self.empty_reason is not None):
            raise ValueError("empty_reason is required exactly when the option list is empty")
        return self


class MobileWorkflowResultV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["MobileWorkflowResultV1"] = "MobileWorkflowResultV1"
    contract_version: Literal["1.0"] = "1.0"
    status: Literal["ACCEPTED", "SUCCEEDED", "BLOCKED", "FAILED"]
    request_id: str = Field(min_length=1, max_length=120)
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=0)
    observed_session_version: int = Field(ge=0)
    provenance: WorkflowResultProvenanceV1
    payload: dict[str, Any] | None = None
    failure: WorkflowFailureV1 | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> MobileWorkflowResultV1:
        if self.status == "FAILED":
            if self.failure is None or self.payload is not None:
                raise ValueError("failed result requires a typed failure and no payload")
        elif self.failure is not None or self.payload is None:
            raise ValueError("non-failed result requires a payload and cannot carry failure")
        return self


__all__ = [
    "ActivityRecommendationCardV1",
    "ActivityRecommendationCardV2",
    "ActivityRecommendationSetV1",
    "ActivityRecommendationSetV2",
    "MobileWorkflowCommandV1",
    "MobileWorkflowResultV1",
    "WorkflowFailureV1",
    "WorkflowResultProvenanceV1",
]
