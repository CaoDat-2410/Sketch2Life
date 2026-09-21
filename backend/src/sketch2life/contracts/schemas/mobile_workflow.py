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
    "MobileWorkflowCommandV1",
    "MobileWorkflowResultV1",
    "WorkflowFailureV1",
    "WorkflowResultProvenanceV1",
]
