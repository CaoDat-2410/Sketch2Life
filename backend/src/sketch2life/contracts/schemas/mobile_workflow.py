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
    "ActivityRecommendationSetV1",
    "MobileWorkflowCommandV1",
    "MobileWorkflowResultV1",
    "WorkflowFailureV1",
    "WorkflowResultProvenanceV1",
]
