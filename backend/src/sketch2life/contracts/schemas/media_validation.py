"""Versioned Pydantic boundary contracts for deterministic media validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from sketch2life.domain.understanding.media_quality import (
    AudioQualitySignals,
    ImageQualitySignals,
    MediaDecision,
    MediaQualityAssessment,
    MediaRecaptureReason,
)


class SourceMediaReferenceV1(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact_ref: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    working_copy_ref: None = None


class ImageQualitySignalsV1(BaseModel):
    model_config = ConfigDict(frozen=True)

    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    mean_luminance: float | None = Field(default=None, ge=0, le=255)
    luminance_standard_deviation: float | None = Field(default=None, ge=0)
    edge_strength: float | None = Field(default=None, ge=0)
    border_ink_ratio: float | None = Field(default=None, ge=0, le=1)


class AudioQualitySignalsV1(BaseModel):
    model_config = ConfigDict(frozen=True)

    duration_seconds: float | None = Field(default=None, ge=0)
    sample_rate_hz: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)
    rms: float | None = Field(default=None, ge=0, le=1)
    clipping_ratio: float | None = Field(default=None, ge=0, le=1)
    speech_activity_ratio: float | None = Field(default=None, ge=0, le=1)
    zero_crossing_ratio: float | None = Field(default=None, ge=0, le=1)


class MediaValidationResultV1(BaseModel):
    """Public contract; sources are immutable and normalization is not performed in P2-T1."""

    model_config = ConfigDict(frozen=True)

    contract_name: Literal["MediaValidationResultV1"] = "MediaValidationResultV1"
    contract_version: Literal["1.0"] = "1.0"
    decision: MediaDecision
    recapture_reasons: tuple[MediaRecaptureReason, ...]
    image: SourceMediaReferenceV1
    audio: SourceMediaReferenceV1
    image_signals: ImageQualitySignalsV1
    audio_signals: AudioQualitySignalsV1
    validator_policy_version: str = Field(min_length=1)
    validator_name: Literal["deterministic-media-validator"] = "deterministic-media-validator"


class MediaFixtureManifestEntryV1(BaseModel):
    """Fixture declaration. It intentionally contains no real child data."""

    model_config = ConfigDict(frozen=True)

    fixture_id: str = Field(pattern=r"^[a-z0-9-]+$")
    image_ref: str = Field(min_length=1)
    audio_ref: str = Field(min_length=1)
    expected_decision: MediaDecision
    expected_reasons: tuple[MediaRecaptureReason, ...]
    synthetic_data: Literal[True] = True


def image_signals_contract(signals: ImageQualitySignals) -> ImageQualitySignalsV1:
    return ImageQualitySignalsV1(
        width=signals.width,
        height=signals.height,
        mean_luminance=signals.mean_luminance,
        luminance_standard_deviation=signals.luminance_standard_deviation,
        edge_strength=signals.edge_strength,
        border_ink_ratio=signals.border_ink_ratio,
    )


def audio_signals_contract(signals: AudioQualitySignals) -> AudioQualitySignalsV1:
    return AudioQualitySignalsV1(
        duration_seconds=signals.duration_seconds,
        sample_rate_hz=signals.sample_rate_hz,
        channels=signals.channels,
        rms=signals.rms,
        clipping_ratio=signals.clipping_ratio,
        speech_activity_ratio=signals.speech_activity_ratio,
        zero_crossing_ratio=signals.zero_crossing_ratio,
    )


def media_validation_contract(
    assessment: MediaQualityAssessment,
    image: SourceMediaReferenceV1,
    audio: SourceMediaReferenceV1,
) -> MediaValidationResultV1:
    return MediaValidationResultV1(
        decision=assessment.decision,
        recapture_reasons=assessment.reasons,
        image=image,
        audio=audio,
        image_signals=image_signals_contract(assessment.image_signals),
        audio_signals=audio_signals_contract(assessment.audio_signals),
        validator_policy_version=assessment.policy_version,
    )
