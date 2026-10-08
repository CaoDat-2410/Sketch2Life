"""Media-provider contracts for the illustrated story-video pipeline."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.story_video import Sha256


class NarrationRenderRequestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["NarrationRenderRequestV1"] = "NarrationRenderRequestV1"
    version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=200)
    package_id: str = Field(min_length=1, max_length=120)
    package_hash: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    locale: str = Field(min_length=2, max_length=20)
    narration_profile_ref: str = Field(min_length=1, max_length=300)
    segment_ids: tuple[str, ...] = Field(min_length=1, max_length=12)
    approved_text_hash: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")


class NarrationAssetV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["NarrationAssetV1"] = "NarrationAssetV1"
    version: Literal["1.0"] = "1.0"
    status: Literal["READY", "RETRYABLE_FAILURE", "BLOCKED", "INVALID"]
    audio_ref: str | None = Field(default=None, max_length=300)
    audio_sha256: Sha256 | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    duration_seconds: float | None = Field(default=None, gt=0, le=120)
    locale: str = Field(min_length=2, max_length=20)
    voice_model_ref: str = Field(min_length=1, max_length=300)
    segment_timing_seconds: tuple[float, ...] = Field(default=(), max_length=12)
    error_code: str | None = Field(default=None, max_length=120)


class IllustrationImageRequestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["IllustrationImageRequestV1"] = "IllustrationImageRequestV1"
    version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=200)
    package_id: str = Field(min_length=1, max_length=120)
    package_hash: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    scene_id: str = Field(pattern=r"^scene-[1-9][0-9]*$", max_length=40)
    source_image_ref: str = Field(min_length=1, max_length=300)
    source_image_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    visual_prompt: str = Field(min_length=1, max_length=2_000)
    style_profile_ref: str = Field(min_length=1, max_length=300)
    safety_policy_version: str = Field(min_length=1, max_length=80)


class IllustrationAssetV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["IllustrationAssetV1"] = "IllustrationAssetV1"
    version: Literal["1.0"] = "1.0"
    status: Literal["READY", "RETRYABLE_FAILURE", "BLOCKED", "INVALID"]
    scene_id: str = Field(pattern=r"^scene-[1-9][0-9]*$", max_length=40)
    asset_ref: str | None = Field(default=None, max_length=300)
    asset_sha256: Sha256 | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    content_type: Literal["image/png", "image/jpeg", "image/webp"] | None = None
    width: int | None = Field(default=None, gt=0, le=8_000)
    height: int | None = Field(default=None, gt=0, le=8_000)
    source_image_ref: str = Field(min_length=1, max_length=300)
    source_image_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    model_profile_ref: str = Field(min_length=1, max_length=300)
    error_code: str | None = Field(default=None, max_length=120)


class VideoSceneRenderRequestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["VideoSceneRenderRequestV1"] = "VideoSceneRenderRequestV1"
    version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=200)
    package_id: str = Field(min_length=1, max_length=120)
    package_hash: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    storyboard_id: str = Field(min_length=1, max_length=120)
    storyboard_hash: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    scene_id: str = Field(pattern=r"^scene-[1-9][0-9]*$", max_length=40)
    illustration_ref: str = Field(min_length=1, max_length=300)
    illustration_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    approved_fact_ids: tuple[str, ...] = Field(min_length=1, max_length=16)
    confirmed_anchor_ids: tuple[str, ...] = Field(min_length=1, max_length=16)
    model_profile_ref: str = Field(default="wan2.2-ti2v-5b", min_length=1, max_length=200)
    duration_seconds: float = Field(gt=0, le=20)
    resource_preflight: Literal["PASSED"]


class VideoSceneArtifactV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["VideoSceneArtifactV1"] = "VideoSceneArtifactV1"
    version: Literal["1.0"] = "1.0"
    status: Literal["READY", "RETRYABLE_FAILURE", "BLOCKED", "INVALID"]
    scene_id: str = Field(pattern=r"^scene-[1-9][0-9]*$", max_length=40)
    silent_clip_ref: str | None = Field(default=None, max_length=300)
    silent_clip_sha256: Sha256 | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    duration_seconds: float | None = Field(default=None, gt=0, le=20)
    frame_count: int | None = Field(default=None, gt=0)
    fps: float | None = Field(default=None, gt=0, le=120)
    model_profile_ref: str = Field(min_length=1, max_length=300)
    error_code: str | None = Field(default=None, max_length=120)


class SubtitleCueV1(BaseModel):
    """One narration-aligned subtitle cue for the final stitched video."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = Field(min_length=1, max_length=2_000)
    start_seconds: float = Field(ge=0, le=120)
    end_seconds: float = Field(gt=0, le=120)

    @model_validator(mode="after")
    def validate_order(self) -> SubtitleCueV1:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("subtitle cue must end after it starts")
        return self


class VideoAssemblyRequestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["VideoAssemblyRequestV1"] = "VideoAssemblyRequestV1"
    version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=200)
    package_id: str = Field(min_length=1, max_length=120)
    package_hash: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    storyboard_id: str = Field(min_length=1, max_length=120)
    scene_ids: tuple[str, ...] = Field(min_length=1, max_length=12)
    scene_artifact_refs: tuple[str, ...] = Field(min_length=1, max_length=12)
    scene_artifact_sha256: tuple[Sha256, ...] = Field(min_length=1, max_length=12)
    narration_ref: str = Field(min_length=1, max_length=300)
    narration_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    subtitle_cues: tuple[SubtitleCueV1, ...] = Field(default=(), max_length=48)
    target_duration_min_seconds: int = Field(default=40, ge=40, le=60)
    target_duration_max_seconds: int = Field(default=60, ge=40, le=60)

    @model_validator(mode="after")
    def validate_assembly_inputs(self) -> VideoAssemblyRequestV1:
        if not (
            len(self.scene_ids)
            == len(self.scene_artifact_refs)
            == len(self.scene_artifact_sha256)
        ):
            raise ValueError("scene IDs, artifacts and hashes must have the same length")
        if any(not re.fullmatch(r"[a-f0-9]{64}", digest) for digest in self.scene_artifact_sha256):
            raise ValueError("scene artifact hashes must be SHA-256 digests")
        if self.subtitle_cues and not (
            len(self.scene_ids) <= len(self.subtitle_cues) <= len(self.scene_ids) * 4
        ):
            raise ValueError("subtitle cues must contain one to four cues per scene")
        if any(
            current.start_seconds < previous.end_seconds - 0.01
            for previous, current in zip(self.subtitle_cues, self.subtitle_cues[1:], strict=False)
        ):
            raise ValueError("subtitle cues must not overlap")
        return self


class VideoArtifactV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["VideoArtifactV1"] = "VideoArtifactV1"
    version: Literal["1.0"] = "1.0"
    status: Literal["READY", "RETRYABLE_FAILURE", "BLOCKED", "INVALID"]
    video_ref: str | None = Field(default=None, max_length=300)
    video_sha256: Sha256 | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    duration_seconds: float | None = Field(default=None, gt=0, le=120)
    audio_ref: str | None = Field(default=None, max_length=300)
    video_codec: str | None = Field(default=None, max_length=40)
    audio_codec: str | None = Field(default=None, max_length=40)
    error_code: str | None = Field(default=None, max_length=120)


class VideoJobStatusV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["VideoJobStatusV1"] = "VideoJobStatusV1"
    version: Literal["1.0"] = "1.0"
    job_id: str = Field(min_length=1, max_length=120)
    session_id: str = Field(min_length=1, max_length=120)
    state: Literal[
        "QUEUED", "PREFLIGHT", "NARRATION_READY", "ILLUSTRATIONS_READY",
        "SCENES_RENDERING", "ASSEMBLING", "VALIDATING", "READY",
        "BLOCKED", "RETRYABLE_FAILURE", "FAILED", "CANCELLED", "STALE_INPUT", "EXPIRED",
    ]
    stage: str = Field(min_length=1, max_length=80)
    progress_percent: int = Field(ge=0, le=100)
    retry_count: int = Field(ge=0)
    public_message: str = Field(min_length=1, max_length=300)
    video_artifact_ref: str | None = Field(default=None, max_length=500)


__all__ = [name for name in globals() if name.endswith("V1")]
