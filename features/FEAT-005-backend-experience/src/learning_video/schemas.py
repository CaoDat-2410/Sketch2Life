"""Versioned contracts for the standalone Person 4 learning-media POC."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AssetType(StrEnum):
    MICRO_VIDEO = "micro_video"
    STILL_NARRATION = "still_narration"


class ReviewStatus(StrEnum):
    REVIEWED = "REVIEWED"
    UNREVIEWED = "UNREVIEWED"
    REJECTED = "REJECTED"


class ResolverStatus(StrEnum):
    HIT = "HIT"
    MISS = "MISS"


class ValidationStatus(StrEnum):
    PASS = "PASS"
    RETRY = "RETRY"
    FALLBACK = "FALLBACK"
    BLOCK = "BLOCK"


class LearningObjective(ContractModel):
    objective_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    version: str = Field(min_length=1, pattern=r"^v[0-9]+$")
    locale: str = Field(min_length=2, max_length=16)
    age_band: str = Field(min_length=1, max_length=32)
    concept: str = Field(min_length=1, max_length=500)


class ProvenanceMetadata(ContractModel):
    source: str = Field(min_length=1, max_length=200)
    model_name: str | None = Field(default=None, max_length=200)
    model_version: str | None = Field(default=None, max_length=100)
    prompt_hash: str | None = Field(default=None, max_length=128)
    config_hash: str | None = Field(default=None, max_length=128)
    created_at: datetime | None = None


class ReviewedAssetBase(ContractModel):
    asset_id: str = Field(min_length=1, max_length=200)
    objective_id: str = Field(min_length=1, max_length=200)
    objective_version: str = Field(min_length=1, pattern=r"^v[0-9]+$")
    locale: str = Field(min_length=2, max_length=16)
    age_band: str = Field(min_length=1, max_length=32)
    review_status: Literal[ReviewStatus.REVIEWED] = ReviewStatus.REVIEWED
    duration_sec: float = Field(gt=0, le=10)
    provenance: ProvenanceMetadata


class MicroVideoAsset(ReviewedAssetBase):
    asset_type: Literal[AssetType.MICRO_VIDEO] = AssetType.MICRO_VIDEO
    video_path: str = Field(min_length=1)


class ReviewedStillNarrationAsset(ReviewedAssetBase):
    asset_type: Literal[AssetType.STILL_NARRATION] = AssetType.STILL_NARRATION
    still_path: str = Field(min_length=1)
    narration_path: str = Field(min_length=1)


LearningExplanationAsset = Annotated[
    Union[MicroVideoAsset, ReviewedStillNarrationAsset], Field(discriminator="asset_type")
]


class ReviewedAsset(ContractModel):
    asset: LearningExplanationAsset


class GenerationBrief(ContractModel):
    objective_id: str = Field(min_length=1, max_length=200)
    objective_version: str = Field(min_length=1, pattern=r"^v[0-9]+$")
    locale: str = Field(min_length=2, max_length=16)
    age_band: str = Field(min_length=1, max_length=32)
    duration_sec: int = Field(ge=5, le=10)
    prompt: str = Field(min_length=1, max_length=2000)
    show: list[str] = Field(min_length=1, max_length=20)
    avoid: list[str] = Field(default_factory=list, max_length=20)
    profile: dict[str, str | int | float | bool] = Field(default_factory=dict)

    @field_validator("show", "avoid")
    @classmethod
    def reject_blank_items(cls, values: list[str]) -> list[str]:
        if any(not item.strip() for item in values):
            raise ValueError("list items must not be blank")
        return values


class GeneratedVideo(ContractModel):
    artifact_id: str = Field(min_length=1, max_length=200)
    objective_id: str = Field(min_length=1, max_length=200)
    objective_version: str = Field(min_length=1, pattern=r"^v[0-9]+$")
    output_path: str = Field(min_length=1)
    duration_sec: float = Field(gt=0, le=10)
    provider: str = Field(min_length=1, max_length=100)
    provenance: ProvenanceMetadata


class FrameSamplingResult(ContractModel):
    status: ValidationStatus
    video_path: str = Field(min_length=1)
    duration_sec: float | None = Field(default=None, ge=0)
    sampled_frame_paths: list[str] = Field(default_factory=list, max_length=5)
    sample_percentages: list[int] = Field(default_factory=list, max_length=5)
    reason_codes: list[str] = Field(default_factory=list, max_length=20)
    validator: Literal["ffmpeg"] = "ffmpeg"


class VisualInspection(ContractModel):
    objective_present: bool
    prohibited_content_found: bool = False
    age_appropriate: bool = True
    visual_corruption_detected: bool = False
    notes: list[str] = Field(default_factory=list, max_length=20)


class ResolverResult(ContractModel):
    status: ResolverStatus
    objective_id: str = Field(min_length=1, max_length=200)
    objective_version: str = Field(min_length=1, pattern=r"^v[0-9]+$")
    asset: LearningExplanationAsset | None = None
    generation_required: bool
    reason_code: str | None = Field(default=None, max_length=100)


class ValidationResult(ContractModel):
    status: ValidationStatus
    objective_id: str = Field(min_length=1, max_length=200)
    objective_version: str = Field(min_length=1, pattern=r"^v[0-9]+$")
    duration_sec: float | None = Field(default=None, ge=0, le=10)
    sampled_frame_paths: list[str] = Field(default_factory=list, max_length=5)
    reason_codes: list[str] = Field(default_factory=list, max_length=20)
    validator: Literal["ffmpeg", "qwen3-vl", "combined"]
