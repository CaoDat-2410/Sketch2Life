"""Pure, deterministic media-quality policy for the understanding workstream."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MediaDecision(StrEnum):
    PASS = "PASS"
    RECAPTURE = "RECAPTURE"


class MediaRecaptureReason(StrEnum):
    IMAGE_UNREADABLE = "IMAGE_UNREADABLE"
    IMAGE_DIMENSIONS_TOO_SMALL = "IMAGE_DIMENSIONS_TOO_SMALL"
    IMAGE_TOO_DARK = "IMAGE_TOO_DARK"
    IMAGE_LOW_CONTRAST = "IMAGE_LOW_CONTRAST"
    IMAGE_BLURRY = "IMAGE_BLURRY"
    IMAGE_FRAMING_RISK = "IMAGE_FRAMING_RISK"
    AUDIO_UNREADABLE = "AUDIO_UNREADABLE"
    AUDIO_DURATION_OUT_OF_RANGE = "AUDIO_DURATION_OUT_OF_RANGE"
    AUDIO_SILENT = "AUDIO_SILENT"
    AUDIO_NO_SPEECH_SIGNAL = "AUDIO_NO_SPEECH_SIGNAL"
    AUDIO_CLIPPING = "AUDIO_CLIPPING"


@dataclass(frozen=True, slots=True)
class ImageQualitySignals:
    width: int | None
    height: int | None
    mean_luminance: float | None
    luminance_standard_deviation: float | None
    edge_strength: float | None
    border_ink_ratio: float | None


@dataclass(frozen=True, slots=True)
class AudioQualitySignals:
    duration_seconds: float | None
    sample_rate_hz: int | None
    channels: int | None
    rms: float | None
    clipping_ratio: float | None
    speech_activity_ratio: float | None
    zero_crossing_ratio: float | None


@dataclass(frozen=True, slots=True)
class MediaQualityPolicy:
    version: str = "media-quality-policy-v1"
    min_image_width: int = 128
    min_image_height: int = 128
    minimum_mean_luminance: float = 24.0
    minimum_luminance_standard_deviation: float = 9.0
    minimum_edge_strength: float = 1.25
    maximum_border_ink_ratio: float = 0.55
    minimum_audio_duration_seconds: float = 0.5
    maximum_audio_duration_seconds: float = 180.0
    silence_rms_threshold: float = 0.008
    minimum_speech_activity_ratio: float = 0.15
    minimum_zero_crossing_ratio: float = 0.002
    maximum_clipping_ratio: float = 0.02


@dataclass(frozen=True, slots=True)
class MediaQualityAssessment:
    decision: MediaDecision
    reasons: tuple[MediaRecaptureReason, ...]
    image_signals: ImageQualitySignals
    audio_signals: AudioQualitySignals
    policy_version: str


def assess_image(
    signals: ImageQualitySignals, policy: MediaQualityPolicy
) -> tuple[MediaRecaptureReason, ...]:
    if signals.width is None or signals.height is None:
        return (MediaRecaptureReason.IMAGE_UNREADABLE,)

    reasons: list[MediaRecaptureReason] = []
    if signals.width < policy.min_image_width or signals.height < policy.min_image_height:
        reasons.append(MediaRecaptureReason.IMAGE_DIMENSIONS_TOO_SMALL)
    if (
        signals.mean_luminance is not None
        and signals.mean_luminance < policy.minimum_mean_luminance
    ):
        reasons.append(MediaRecaptureReason.IMAGE_TOO_DARK)
    if (
        signals.luminance_standard_deviation is not None
        and signals.luminance_standard_deviation < policy.minimum_luminance_standard_deviation
    ):
        reasons.append(MediaRecaptureReason.IMAGE_LOW_CONTRAST)
    if signals.edge_strength is not None and signals.edge_strength < policy.minimum_edge_strength:
        reasons.append(MediaRecaptureReason.IMAGE_BLURRY)
    if (
        signals.border_ink_ratio is not None
        and signals.border_ink_ratio > policy.maximum_border_ink_ratio
    ):
        reasons.append(MediaRecaptureReason.IMAGE_FRAMING_RISK)
    return tuple(reasons)


def assess_audio(
    signals: AudioQualitySignals, policy: MediaQualityPolicy
) -> tuple[MediaRecaptureReason, ...]:
    if signals.duration_seconds is None:
        return (MediaRecaptureReason.AUDIO_UNREADABLE,)

    reasons: list[MediaRecaptureReason] = []
    if not (
        policy.minimum_audio_duration_seconds
        <= signals.duration_seconds
        <= policy.maximum_audio_duration_seconds
    ):
        reasons.append(MediaRecaptureReason.AUDIO_DURATION_OUT_OF_RANGE)
    if signals.rms is not None and signals.rms < policy.silence_rms_threshold:
        reasons.append(MediaRecaptureReason.AUDIO_SILENT)
    elif (
        signals.speech_activity_ratio is not None
        and signals.zero_crossing_ratio is not None
        and (
            signals.speech_activity_ratio < policy.minimum_speech_activity_ratio
            or signals.zero_crossing_ratio < policy.minimum_zero_crossing_ratio
        )
    ):
        reasons.append(MediaRecaptureReason.AUDIO_NO_SPEECH_SIGNAL)
    if (
        signals.clipping_ratio is not None
        and signals.clipping_ratio > policy.maximum_clipping_ratio
    ):
        reasons.append(MediaRecaptureReason.AUDIO_CLIPPING)
    return tuple(reasons)


def assess_media(
    image_signals: ImageQualitySignals,
    audio_signals: AudioQualitySignals,
    policy: MediaQualityPolicy,
) -> MediaQualityAssessment:
    reasons = assess_image(image_signals, policy) + assess_audio(audio_signals, policy)
    return MediaQualityAssessment(
        decision=MediaDecision.PASS if not reasons else MediaDecision.RECAPTURE,
        reasons=reasons,
        image_signals=image_signals,
        audio_signals=audio_signals,
        policy_version=policy.version,
    )
