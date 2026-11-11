"""Strict request and response contracts for Parent profile routes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class ParentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class CreateParentProfileRequest(ParentRequest):
    display_name: str = Field(min_length=1, max_length=120)
    age_months: StrictInt = Field(ge=36, le=120)
    interests_summary: str | None = Field(default=None, max_length=2000)

    @field_validator("display_name")
    @classmethod
    def display_name_must_contain_visible_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("display_name must contain non-whitespace text")
        return value


class PatchParentProfileRequest(ParentRequest):
    expected_revision: StrictInt = Field(ge=1)
    display_name: str = Field(min_length=1, max_length=120)
    age_months: StrictInt = Field(ge=36, le=120)
    interests_summary: str | None = Field(default=None, max_length=2000)

    @field_validator("display_name")
    @classmethod
    def display_name_must_contain_visible_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("display_name must contain non-whitespace text")
        return value


class ParentProfileReference(BaseModel):
    profile_id: str
    revision_no: int
    revision_hash: str


class ParentProfileView(ParentProfileReference):
    display_name: str
    age_months: int
    age_band_ref: str | None
    age_band_version: str | None
    interests_summary: str | None
    state: str
    data_origin: str


class ParentErrorResponse(BaseModel):
    code: str
    message: str
    correlation_id: str
    retryable: bool
    request_id: str
    retry_after_seconds: int | None = None
    current_version: int | None = None
    field_errors: list[dict[str, str]] | None = None
