"""Canonical FEAT-018 Person 4 learning-media contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LearningMediaProvenanceV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source: Literal["reviewed_cache", "synthetic_fixture", "renderer_fallback"]
    asset_ref: str | None = Field(default=None, min_length=1)
    asset_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    review_status: Literal["REVIEWED", "NOT_APPLICABLE"]
    provenance_version: Literal["1.0"] = "1.0"

    @model_validator(mode="after")
    def require_reviewed_asset(self) -> LearningMediaProvenanceV1:
        if self.source == "reviewed_cache" and (
            self.asset_ref is None
            or self.asset_sha256 is None
            or self.review_status != "REVIEWED"
        ):
            raise ValueError("reviewed cache provenance requires ref, hash, and REVIEWED status")
        return self


class LearningMediaRequestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["LearningMediaRequestV1"] = "LearningMediaRequestV1"
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=0)
    request_id: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=200)
    activity_id: str = Field(min_length=1, max_length=120)
    activity_version: str = Field(pattern=r"^v[0-9]+$")
    objective_id: str = Field(min_length=1, max_length=120)
    objective_version: str = Field(pattern=r"^v[0-9]+$")
    renderer_plan_id: str = Field(min_length=1, max_length=120)
    renderer_plan_version: str = Field(pattern=r"^v[0-9]+$")
    source_session_version: int = Field(ge=0)
    cache_key: str = Field(min_length=1, max_length=512)


class ReviewedLearningMediaAssetV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_ref: str = Field(min_length=1, max_length=300)
    asset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    activity_id: str = Field(min_length=1, max_length=120)
    activity_version: str = Field(pattern=r"^v[0-9]+$")
    objective_id: str = Field(min_length=1, max_length=120)
    objective_version: str = Field(pattern=r"^v[0-9]+$")
    renderer_plan_id: str = Field(min_length=1, max_length=120)
    renderer_plan_version: str = Field(pattern=r"^v[0-9]+$")
    cache_key: str = Field(min_length=1, max_length=512)
    review_status: Literal["REVIEWED"] = "REVIEWED"
    media_status: Literal["AVAILABLE", "STALE", "CORRUPT", "UNSAFE"] = "AVAILABLE"


class LearningMediaResultV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["LearningMediaResultV1"] = "LearningMediaResultV1"
    contract_version: Literal["1.0"] = "1.0"
    status: Literal["READY", "FALLBACK", "BLOCKED"]
    cache_status: Literal["HIT", "MISS", "NOT_ATTEMPTED"]
    activity_id: str = Field(min_length=1, max_length=120)
    activity_version: str = Field(pattern=r"^v[0-9]+$")
    objective_id: str = Field(min_length=1, max_length=120)
    objective_version: str = Field(pattern=r"^v[0-9]+$")
    renderer_plan_id: str = Field(min_length=1, max_length=120)
    renderer_plan_version: str = Field(pattern=r"^v[0-9]+$")
    asset_ref: str | None = Field(default=None, min_length=1)
    generation_called: bool
    provenance: LearningMediaProvenanceV1
    reason_code: Literal[
        "CACHE_MISS",
        "STALE_MEDIA",
        "CORRUPT_MEDIA",
        "UNSAFE_MEDIA",
        "RENDERER_FAILURE",
        "MEDIA_UNAVAILABLE",
        "PROVIDER_TIMEOUT",
    ] | None = None

    @model_validator(mode="after")
    def validate_result_state(self) -> LearningMediaResultV1:
        if self.status == "READY" and self.asset_ref is None:
            raise ValueError("ready learning media requires an asset reference")
        if self.status != "READY" and self.reason_code is None:
            raise ValueError("fallback or blocked learning media requires a typed reason")
        if self.cache_status == "HIT" and self.status != "READY":
            raise ValueError("a cache hit must return ready media")
        return self
