"""Session-only gallery, background-job, and feedback wire contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.p1_experience import VersionedRefV1


class SessionJourneyEntryV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entry_id: str = Field(min_length=1, max_length=120)
    stage: Literal[
        "MEDIA",
        "UNDERSTANDING",
        "GATE_A",
        "P1",
        "GATE_B",
        "EXPERIENCE",
        "HANDOFF",
        "FEEDBACK",
    ]
    status: Literal["COMPLETED", "BLOCKED"]
    occurred_at: datetime
    artifact_refs: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_aware_timestamp(self) -> SessionJourneyEntryV1:
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("journey timestamp must be timezone-aware")
        return self


class SessionGalleryV1(BaseModel):
    """Projection for one in-memory session; media bytes and durable-owner data are excluded."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["SessionGalleryV1"] = "SessionGalleryV1"
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=120)
    session_version: int = Field(ge=0)
    status: Literal["ACTIVE", "EXPIRED"]
    entries: tuple[SessionJourneyEntryV1, ...] = Field(max_length=64)
    media_bytes_included: Literal[False] = False
    durable: Literal[False] = False


class WorkflowJobV1(BaseModel):
    """Pollable process-local job status with sanitized terminal references."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["WorkflowJobV1"] = "WorkflowJobV1"
    contract_version: Literal["1.0"] = "1.0"
    job_id: str = Field(min_length=1, max_length=120)
    session_id: str = Field(min_length=1, max_length=120)
    request_id: str = Field(min_length=1, max_length=120)
    status: Literal[
        "QUEUED",
        "RUNNING",
        "SUCCEEDED",
        "PARTIAL_SUCCESS",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
        "EXPIRED",
    ]
    created_at: datetime
    updated_at: datetime
    result_ref: str | None = Field(default=None, max_length=300)
    failure: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{1,79}$")

    @model_validator(mode="after")
    def validate_terminal_state(self) -> WorkflowJobV1:
        for value in (self.created_at, self.updated_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("job timestamps must be timezone-aware")
        if self.updated_at < self.created_at:
            raise ValueError("job updated_at cannot precede created_at")
        terminal = self.status not in {"QUEUED", "RUNNING"}
        if terminal and self.status == "FAILED" and self.failure is None:
            raise ValueError("failed job requires a typed failure code")
        if (
            terminal
            and self.status in {"SUCCEEDED", "PARTIAL_SUCCESS", "BLOCKED"}
            and self.result_ref is None
        ):
            raise ValueError("completed job requires a result reference")
        if not terminal and (self.failure is not None or self.result_ref is not None):
            raise ValueError("non-terminal job cannot expose a result or failure")
        return self


class SessionSnapshotV1(BaseModel):
    """Public process-local snapshot; ownership and persistence are intentionally absent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["SessionSnapshotV1"] = "SessionSnapshotV1"
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=120)
    version: int = Field(ge=0)
    state: Literal[
        "CREATED",
        "MEDIA_RECAPTURE",
        "UNDERSTANDING_PROPOSED",
        "GATE_A_PENDING",
        "CONTEXT_REQUIRED",
        "CANDIDATES_READY",
        "GATE_B_PENDING",
        "EXPERIENCE_READY",
        "HANDOFF_READY",
        "FEEDBACK_RECORDED",
    ]
    status: Literal["ACTIVE", "EXPIRED"]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    last_job: WorkflowJobV1 | None = None
    durable: Literal[False] = False

    @model_validator(mode="after")
    def validate_session_lifetime(self) -> SessionSnapshotV1:
        for value in (self.created_at, self.updated_at, self.expires_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("session timestamps must be timezone-aware")
        if self.updated_at < self.created_at or self.expires_at <= self.updated_at:
            raise ValueError("session expiry must follow its last update")
        return self


class FeedbackV1(BaseModel):
    """Non-identifying feedback linked to the exact approved experience identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["FeedbackV1"] = "FeedbackV1"
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=1)
    actor_ref: str = Field(min_length=1, max_length=160)
    activity_ref: VersionedRefV1
    objective_ref: VersionedRefV1
    template_ref: VersionedRefV1
    spec_ref: VersionedRefV1
    completion_status: Literal["COMPLETED", "PARTIAL", "NOT_ATTEMPTED"]
    interest_score: int | None = Field(default=None, ge=1, le=5)
    independence_score: int | None = Field(default=None, ge=1, le=5)
    observation_tags: tuple[
        Literal[
            "STARTED_INDEPENDENTLY",
            "COMPLETED_STEPS",
            "ASKED_FOR_HELP",
            "CHANGED_APPROACH",
            "STOPPED_EARLY",
        ],
        ...,
    ] = ()
    recorded_at: datetime

    @model_validator(mode="after")
    def require_aware_timestamp(self) -> FeedbackV1:
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("feedback timestamp must be timezone-aware")
        return self


__all__ = [
    "FeedbackV1",
    "SessionGalleryV1",
    "SessionJourneyEntryV1",
    "SessionSnapshotV1",
    "WorkflowJobV1",
]
