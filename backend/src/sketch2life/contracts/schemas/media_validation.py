"""Versioned Pydantic boundary contracts for deterministic media validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.domain.understanding.media_quality import (
    AudioQualitySignals,
    ImageQualitySignals,
    MediaDecision,
    MediaQualityAssessment,
    MediaRecaptureReason,
)


class SourceMediaReferenceV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_ref: str = Field(min_length=1)
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    source_status: Literal["AVAILABLE", "MISSING", "UNREADABLE"] = "AVAILABLE"
    working_copy_ref: None = None

    @model_validator(mode="after")
    def validate_provenance(self) -> SourceMediaReferenceV1:
        if self.source_status == "AVAILABLE" and self.sha256 is None:
            raise ValueError("available source must carry a content hash")
        if self.source_status != "AVAILABLE" and self.sha256 is not None:
            raise ValueError("unavailable source must not carry a content hash")
        return self


class ImageQualitySignalsV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    mean_luminance: float | None = Field(default=None, ge=0, le=255)
    luminance_standard_deviation: float | None = Field(default=None, ge=0)
    edge_strength: float | None = Field(default=None, ge=0)
    border_ink_ratio: float | None = Field(default=None, ge=0, le=1)


class AudioQualitySignalsV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    duration_seconds: float | None = Field(default=None, ge=0)
    sample_rate_hz: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)
    rms: float | None = Field(default=None, ge=0, le=1)
    clipping_ratio: float | None = Field(default=None, ge=0, le=1)
    speech_activity_ratio: float | None = Field(default=None, ge=0, le=1)
    zero_crossing_ratio: float | None = Field(default=None, ge=0, le=1)


class MediaValidationResultV1(BaseModel):
    """Public contract; sources are immutable and normalization is not performed in P2-T1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["MediaValidationResultV1"] = "MediaValidationResultV1"
    contract_version: Literal["1.0"] = "1.0"
    decision: MediaDecision
    recapture_reasons: tuple[MediaRecaptureReason, ...]
    image: SourceMediaReferenceV1
    audio: SourceMediaReferenceV1
    image_signals: ImageQualitySignalsV1
    audio_signals: AudioQualitySignalsV1
    recapture_message: str = Field(min_length=1, max_length=1_000)
    validator_policy_version: str = Field(min_length=1)
    validator_name: Literal["deterministic-media-validator"] = "deterministic-media-validator"


class MediaFixtureManifestEntryV1(BaseModel):
    """Fixture declaration. It intentionally contains no real child data."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fixture_id: str = Field(pattern=r"^[a-z0-9-]+$")
    image_ref: str = Field(min_length=1)
    audio_ref: str = Field(min_length=1)
    expected_decision: MediaDecision
    expected_reasons: tuple[MediaRecaptureReason, ...]
    image_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    audio_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    declared_image_width: int | None = Field(default=None, ge=1)
    declared_image_height: int | None = Field(default=None, ge=1)
    declared_audio_duration_seconds: float | None = Field(default=None, ge=0)
    declared_audio_sample_rate_hz: int | None = Field(default=None, ge=1)
    synthetic_data: Literal[True] = True


class MediaFixtureManifestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["MediaFixtureManifestV1"] = "MediaFixtureManifestV1"
    contract_version: Literal["1.0"] = "1.0"
    data_policy: Literal["synthetic-only"] = "synthetic-only"
    generator: str = Field(min_length=1)
    fixtures: tuple[MediaFixtureManifestEntryV1, ...] = Field(min_length=1)


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
        recapture_message=_recapture_message(assessment.reasons),
        validator_policy_version=assessment.policy_version,
    )


def _recapture_message(reasons: tuple[MediaRecaptureReason, ...]) -> str:
    if not reasons:
        return "Media quality passed"
    messages = {
        MediaRecaptureReason.IMAGE_UNREADABLE: "Retake the drawing image",
        MediaRecaptureReason.IMAGE_DIMENSIONS_TOO_SMALL: "Retake the drawing at a larger size",
        MediaRecaptureReason.IMAGE_TOO_DARK: "Retake the drawing with more light",
        MediaRecaptureReason.IMAGE_LOW_CONTRAST: "Retake the drawing with clearer contrast",
        MediaRecaptureReason.IMAGE_BLURRY: "Retake the drawing without camera movement",
        MediaRecaptureReason.IMAGE_FRAMING_RISK: "Retake the drawing with all edges visible",
        MediaRecaptureReason.AUDIO_UNREADABLE: "Record the narration again",
        MediaRecaptureReason.AUDIO_DURATION_OUT_OF_RANGE: (
            "Record a narration between 0.5 and 180 seconds"
        ),
        MediaRecaptureReason.AUDIO_SILENT: "Record narration with audible speech",
        MediaRecaptureReason.AUDIO_NO_SPEECH_SIGNAL: "Record narration with a clear speech signal",
        MediaRecaptureReason.AUDIO_CLIPPING: "Record narration below the microphone clipping level",
    }
    return "; ".join(messages[reason] for reason in reasons)
