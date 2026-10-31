"""HTTP DTOs for the local StoryRun-lite synthetic Parent contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sketch2life.domain.story_run_lite import MAX_UPLOAD_BYTES, require_sha256


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateRunRequest(StrictRequest):
    profile_ref: Literal["synthetic-parent-demo"]


class CreateUploadRequest(StrictRequest):
    target_ref: str = Field(min_length=1, max_length=128)
    purpose: Literal["RUN_ARTWORK"]
    media_type: Literal["image/jpeg", "image/png", "image/webp"]
    expected_size_bytes: int = Field(ge=1, le=MAX_UPLOAD_BYTES)
    expected_sha256: str

    @field_validator("expected_sha256")
    @classmethod
    def validate_sha(cls, value: str) -> str:
        return require_sha256(value, "expected_sha256")


class CompleteUploadRequest(StrictRequest):
    expected_size_bytes: int = Field(ge=1, le=MAX_UPLOAD_BYTES)
    expected_sha256: str

    @field_validator("expected_sha256")
    @classmethod
    def validate_sha(cls, value: str) -> str:
        return require_sha256(value, "expected_sha256")


class AttachAssetRequest(StrictRequest):
    asset_ref: str = Field(min_length=1, max_length=256)
    expected_revision: int = Field(ge=1)


class ConfirmSubjectRequest(StrictRequest):
    decision: Literal["CONFIRM"]
    expected_understanding_revision: int = Field(ge=1)


class CancelRunRequest(StrictRequest):
    expected_revision: int = Field(ge=1)


class ErrorField(BaseModel):
    field: str
    code: str
    message: str


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    correlation_id: str
    retryable: bool
    retry_after_seconds: int | None = None
    field_errors: list[ErrorField] | None = None
