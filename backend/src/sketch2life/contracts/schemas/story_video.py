"""Draft contracts for the illustrated story-video pipeline.

These contracts intentionally describe the approved hand-off between planning,
TTS, illustration, motion and assembly. They do not imply that a provider has
successfully rendered an asset; provider results must carry an explicit status.
"""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Sha256 = str
AssetStatus = Literal["READY", "RETRYABLE_FAILURE", "BLOCKED", "INVALID"]


class StoryScriptSegmentV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    segment_id: str = Field(pattern=r"^segment-[1-9][0-9]*$", max_length=40)
    text: str = Field(min_length=1, max_length=2_000)
    approved_fact_ids: tuple[str, ...] = Field(min_length=1, max_length=16)
    confirmed_anchor_ids: tuple[str, ...] = Field(min_length=1, max_length=16)
    scene_purpose: Literal["INTRO", "EXPLAIN", "DEMONSTRATE", "RECAP"]


class ApprovedStoryPackageV1(BaseModel):
    """Immutable input gate for every downstream media provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["ApprovedStoryPackageV1"] = "ApprovedStoryPackageV1"
    version: Literal["1.0"] = "1.0"
    package_id: str = Field(min_length=1, max_length=120)
    session_id: str = Field(min_length=1, max_length=120)
    session_version: int = Field(ge=0)
    source_image_ref: str = Field(min_length=1, max_length=300)
    source_image_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    source_audio_ref: str | None = Field(default=None, max_length=300)
    source_audio_sha256: Sha256 | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    confirmed_understanding_ref: str = Field(min_length=1, max_length=300)
    confirmed_understanding_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    experience_spec_ref: str = Field(min_length=1, max_length=300)
    experience_spec_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    story_script_ref: str = Field(min_length=1, max_length=300)
    story_script_revision: int = Field(ge=1)
    story_script_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    audience_profile_ref: str = Field(min_length=1, max_length=300)
    audience_profile_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_set_ref: str = Field(min_length=1, max_length=300)
    evidence_set_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    locale: str = Field(min_length=2, max_length=20)
    narration_profile_ref: str = Field(min_length=1, max_length=300)
    narration_profile_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    target_duration_min_seconds: int = Field(default=40, ge=40, le=60)
    target_duration_max_seconds: int = Field(default=60, ge=40, le=60)
    approval_ref: str = Field(min_length=1, max_length=300)
    approval_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    content_validator_version: str = Field(min_length=1, max_length=80)
    content_validator_result: Literal["PASSED"]
    created_at: str = Field(min_length=1, max_length=80)
    package_hash: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_duration_window(self) -> ApprovedStoryPackageV1:
        if self.target_duration_min_seconds > self.target_duration_max_seconds:
            raise ValueError("target duration minimum must not exceed maximum")
        if (self.source_audio_ref is None) != (self.source_audio_sha256 is None):
            raise ValueError("source audio ref and hash must be supplied together")
        required_hashes = (
            self.source_image_sha256,
            self.confirmed_understanding_sha256,
            self.experience_spec_sha256,
            self.story_script_sha256,
            self.audience_profile_sha256,
            self.evidence_set_sha256,
            self.narration_profile_sha256,
            self.approval_sha256,
            self.package_hash,
        )
        if any(digest == "0" * 64 for digest in required_hashes):
            raise ValueError("story package contains an unresolved placeholder hash")
        return self


class StoryboardSceneV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scene_id: str = Field(pattern=r"^scene-[1-9][0-9]*$", max_length=40)
    order: int = Field(ge=1)
    segment_ids: tuple[str, ...] = Field(min_length=1, max_length=8)
    narration_text: str = Field(min_length=1, max_length=2_000)
    visual_prompt: str = Field(min_length=1, max_length=2_000)
    motion_prompt: str = Field(min_length=1, max_length=1_000)
    approved_fact_ids: tuple[str, ...] = Field(min_length=1, max_length=16)
    confirmed_anchor_ids: tuple[str, ...] = Field(min_length=1, max_length=16)
    duration_seconds: float = Field(gt=0, le=20)
    duration_basis: Literal["ESTIMATE", "MEASURED_TTS"]


class StoryboardPlanV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["StoryboardPlanV1"] = "StoryboardPlanV1"
    version: Literal["1.0"] = "1.0"
    storyboard_id: str = Field(min_length=1, max_length=120)
    package_id: str = Field(min_length=1, max_length=120)
    package_hash: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    scenes: tuple[StoryboardSceneV1, ...] = Field(min_length=1, max_length=12)
    duration_seconds: float = Field(gt=0, le=120)
    duration_basis: Literal["ESTIMATE", "MEASURED_TTS"]

    @model_validator(mode="after")
    def validate_plan(self) -> StoryboardPlanV1:
        if len({scene.scene_id for scene in self.scenes}) != len(self.scenes):
            raise ValueError("storyboard scene IDs must be unique")
        if tuple(scene.order for scene in self.scenes) != tuple(range(1, len(self.scenes) + 1)):
            raise ValueError("storyboard scenes must have contiguous order")
        if abs(sum(scene.duration_seconds for scene in self.scenes) - self.duration_seconds) > 0.01:
            raise ValueError("storyboard duration must equal scene duration sum")
        if any(scene.duration_basis != self.duration_basis for scene in self.scenes):
            raise ValueError("plan and scene duration basis must match")
        return self


def stable_model_hash(model: BaseModel, *, exclude: set[str] | None = None) -> str:
    """Hash canonical JSON for immutable refs without depending on key order."""

    payload = model.model_dump(mode="json", exclude=exclude or set())
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "ApprovedStoryPackageV1",
    "Sha256",
    "StoryScriptSegmentV1",
    "StoryboardPlanV1",
    "StoryboardSceneV1",
    "stable_model_hash",
]
