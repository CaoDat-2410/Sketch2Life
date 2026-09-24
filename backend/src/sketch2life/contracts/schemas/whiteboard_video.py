"""Canonical FEAT-018 contracts for the session-local whiteboard MP4 job."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WhiteboardVideoJobV1(BaseModel):
    """Pollable job state; media bytes and provider diagnostics are excluded."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["WhiteboardVideoJobV1"] = "WhiteboardVideoJobV1"
    contract_version: Literal["1.0"] = "1.0"
    job_id: str = Field(min_length=1, max_length=120)
    job_version: int = Field(default=1, ge=1)
    session_id: str = Field(min_length=1, max_length=120)
    experience_spec_id: str = Field(min_length=1, max_length=160)
    source_artifact_id: str = Field(min_length=1, max_length=200)
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    learning_thread_ref: str = Field(min_length=1, max_length=200)
    status: Literal[
        "QUEUED",
        "RUNNING",
        "READY",
        "RETRYABLE_FAILURE",
        "FAILED",
        "EXPIRED",
    ]
    progress: int = Field(ge=0, le=100)
    current_stage: Literal[
        "NOT_STARTED",
        "LOCALIZING",
        "SEGMENTING",
        "EXTRACTING_STROKES",
        "RENDERING",
        "ENCODING",
    ]
    attempt: int = Field(ge=1, le=3)
    idempotency_key: str = Field(min_length=1, max_length=200)
    failure_ref: str | None = Field(
        default=None,
        pattern=r"^[A-Z][A-Z0-9_]{1,79}$",
    )
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    expires_at: datetime

    @model_validator(mode="after")
    def validate_job_state(self) -> WhiteboardVideoJobV1:
        timestamps = (self.created_at, self.started_at, self.completed_at, self.expires_at)
        for value in timestamps:
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("whiteboard job timestamps must be timezone-aware")

        if self.expires_at <= self.created_at:
            raise ValueError("whiteboard job expiry must follow creation")
        if self.started_at is not None and self.started_at < self.created_at:
            raise ValueError("whiteboard job start cannot precede creation")
        if self.completed_at is not None and self.started_at is not None:
            if self.completed_at < self.started_at:
                raise ValueError("whiteboard job completion cannot precede start")

        if self.status == "QUEUED" and self.progress != 0:
            raise ValueError("queued whiteboard job must have zero progress")
        if self.status == "READY" and self.progress != 100:
            raise ValueError("ready whiteboard job must have complete progress")
        if self.status in {"RETRYABLE_FAILURE", "FAILED", "EXPIRED"} and self.failure_ref is None:
            raise ValueError("failed whiteboard job requires a typed failure reference")
        if self.status in {"QUEUED", "RUNNING", "READY"} and self.failure_ref is not None:
            raise ValueError("active or ready whiteboard job cannot expose a failure")
        return self


class WhiteboardVideoStatusV1(BaseModel):
    """Sanitized status response used by the polling API."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["WhiteboardVideoStatusV1"] = "WhiteboardVideoStatusV1"
    contract_version: Literal["1.0"] = "1.0"
    job_id: str = Field(min_length=1, max_length=120)
    session_id: str = Field(min_length=1, max_length=120)
    status: Literal[
        "NOT_STARTED",
        "LOCALIZING",
        "SEGMENTING",
        "EXTRACTING_STROKES",
        "RENDERING",
        "ENCODING",
        "READY",
        "RETRYABLE_FAILURE",
        "FAILED",
        "EXPIRED",
    ]
    progress: int = Field(ge=0, le=100)
    retryable: bool
    retry_action: Literal["RETRY", "NONE"]
    video_artifact_ref: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validate_status_response(self) -> WhiteboardVideoStatusV1:
        if self.retryable != (self.status == "RETRYABLE_FAILURE"):
            raise ValueError("retryable flag must match retryable failure status")
        if self.retry_action == "RETRY" and not self.retryable:
            raise ValueError("retry action is only available for retryable failure")
        if self.status == "READY":
            if self.progress != 100 or self.video_artifact_ref is None:
                raise ValueError("ready status requires complete progress and video artifact")
        elif self.video_artifact_ref is not None:
            raise ValueError("non-ready status cannot expose a video artifact")
        return self


class WhiteboardVideoResultV1(BaseModel):
    """Validated terminal result; READY is impossible without all artifacts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["WhiteboardVideoResultV1"] = "WhiteboardVideoResultV1"
    contract_version: Literal["1.0"] = "1.0"
    job_id: str = Field(min_length=1, max_length=120)
    status: Literal["READY"] = "READY"
    video_artifact_id: str = Field(min_length=1, max_length=200)
    mp4_ref: str = Field(min_length=1, max_length=300)
    mask_refs: tuple[str, ...] = Field(min_length=1, max_length=32)
    stroke_refs: tuple[str, ...] = Field(min_length=1, max_length=32)
    tts_ref: str = Field(min_length=1, max_length=300)
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    experience_spec_id: str = Field(min_length=1, max_length=160)
    learning_thread_ref: str = Field(min_length=1, max_length=200)
    duration_seconds: float = Field(ge=5, le=10)
    codec: Literal["H264_AVC_HIGH_L4_1"]
    size_bytes: int = Field(gt=0, le=12 * 1024 * 1024)
    safety_status: Literal["PASSED"] = "PASSED"

