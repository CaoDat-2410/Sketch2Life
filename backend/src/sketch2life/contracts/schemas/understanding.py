"""Versioned, provider-neutral contracts for the Person 2 understanding boundary."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.media_validation import SourceMediaReferenceV1


class AdapterFailureV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: Literal[
        "VALIDATION_REJECTED",
        "TIMEOUT",
        "PROVIDER_ERROR",
        "MALFORMED_OUTPUT",
        "PROHIBITED_FIELD",
        "SOURCE_MISMATCH",
    ]
    message: str = Field(min_length=1, max_length=200)
    retryable: bool


class ModelProvenanceV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: Literal["fixture", "lightning", "runpod", "unknown"]
    model: str = Field(min_length=1, max_length=120)
    adapter_version: str = Field(min_length=1, max_length=40)
    config_version: str = Field(min_length=1, max_length=40)


class AsrSegmentV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    text: str = Field(max_length=2_000)
    confidence: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_interval(self) -> AsrSegmentV1:
        if self.end_seconds < self.start_seconds:
            raise ValueError("segment end must not precede segment start")
        return self


class AsrQualityV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    no_speech_probability: float | None = Field(default=None, ge=0, le=1)
    average_log_probability: float | None = None
    segment_count: int = Field(ge=0)


class AsrRequestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["AsrRequestV1"] = "AsrRequestV1"
    contract_version: Literal["1.0"] = "1.0"
    source_audio: SourceMediaReferenceV1
    media_validation: Literal["PASS"]

    @model_validator(mode="after")
    def require_readable_source(self) -> AsrRequestV1:
        if self.source_audio.source_status != "AVAILABLE":
            raise ValueError("ASR request requires an available source audio reference")
        return self


class AsrResultV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["AsrResultV1"] = "AsrResultV1"
    contract_version: Literal["1.0"] = "1.0"
    status: Literal["SUCCEEDED", "FAILED"]
    source_audio: SourceMediaReferenceV1
    transcript: str | None = Field(default=None, max_length=20_000)
    language: str | None = Field(default=None, min_length=2, max_length=20)
    language_confidence: float | None = Field(default=None, ge=0, le=1)
    segments: tuple[AsrSegmentV1, ...] = ()
    quality: AsrQualityV1 | None = None
    provenance: ModelProvenanceV1
    failure: AdapterFailureV1 | None = None

    @model_validator(mode="after")
    def validate_status_payload(self) -> AsrResultV1:
        if self.status == "SUCCEEDED":
            if (
                self.source_audio.source_status != "AVAILABLE"
                or self.failure is not None
                or self.transcript is None
                or self.quality is None
            ):
                raise ValueError(
                    "successful ASR result requires available source, transcript, "
                    "quality, and no failure"
                )
        elif self.failure is None:
            raise ValueError("failed ASR result requires a typed failure")
        return self


class VisionCandidateV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str = Field(min_length=1, max_length=120)
    confidence: float = Field(ge=0, le=1)


class VisionRelationV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    subject: str = Field(min_length=1, max_length=120)
    predicate: str = Field(min_length=1, max_length=120)
    object: str = Field(min_length=1, max_length=120)
    confidence: float = Field(ge=0, le=1)


class VisionRegionV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class VisionRequestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["VisionRequestV1"] = "VisionRequestV1"
    contract_version: Literal["1.0"] = "1.0"
    source_image: SourceMediaReferenceV1
    media_validation: Literal["PASS"]
    response_schema_version: Literal["VisionUnderstandingResultV1"] = "VisionUnderstandingResultV1"

    @model_validator(mode="after")
    def require_readable_source(self) -> VisionRequestV1:
        if self.source_image.source_status != "AVAILABLE":
            raise ValueError("vision request requires an available source image reference")
        return self


class VisionUnderstandingResultV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["VisionUnderstandingResultV1"] = "VisionUnderstandingResultV1"
    contract_version: Literal["1.0"] = "1.0"
    status: Literal["SUCCEEDED", "FAILED"]
    source_image: SourceMediaReferenceV1
    entities: tuple[VisionCandidateV1, ...] = ()
    actions: tuple[VisionCandidateV1, ...] = ()
    relations: tuple[VisionRelationV1, ...] = ()
    themes: tuple[VisionCandidateV1, ...] = ()
    ambiguous_regions: tuple[VisionRegionV1, ...] = ()
    uncertainty: float = Field(ge=0, le=1)
    provenance: ModelProvenanceV1
    failure: AdapterFailureV1 | None = None

    @model_validator(mode="after")
    def validate_status_payload(self) -> VisionUnderstandingResultV1:
        if self.status == "SUCCEEDED" and (
            self.source_image.source_status != "AVAILABLE" or self.failure is not None
        ):
            raise ValueError("successful vision result requires an available source and no failure")
        if self.status == "FAILED" and self.failure is None:
            raise ValueError("failed vision result requires a typed failure")
        return self
