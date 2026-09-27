"""Contracts for an age-bounded educational whiteboard storyboard."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WhiteboardStoryboardPreviewRequestV1(BaseModel):
    """Preview input before the storyboard is connected to live Vision claims."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["WhiteboardStoryboardPreviewRequestV1"] = (
        "WhiteboardStoryboardPreviewRequestV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    subject_claim: str = Field(min_length=1, max_length=120)
    feature_claim: str = Field(default="ria mèo", min_length=1, max_length=120)
    audience_band: Literal["EARLY_PRIMARY", "PRIMARY"] = "EARLY_PRIMARY"
    age_months: int | None = Field(default=None, ge=0, le=155)


class WhiteboardStoryboardSceneV1(BaseModel):
    """One renderable scene with narration and motion intent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scene_id: str = Field(pattern=r"^scene-[1-9][0-9]*$", max_length=32)
    duration_seconds: float = Field(ge=1.0, le=12.0)
    narration_vi: str = Field(min_length=1, max_length=500)
    visual_prompt_vi: str = Field(min_length=1, max_length=500)
    motion: Literal["INTRO", "FOCUS", "DEMONSTRATE", "RECAP"]
    source_claims: tuple[str, ...] = Field(min_length=1, max_length=8)


class WhiteboardStoryboardV1(BaseModel):
    """Validated storyboard consumed by the future scene renderer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["WhiteboardStoryboardV1"] = "WhiteboardStoryboardV1"
    contract_version: Literal["1.0"] = "1.0"
    storyboard_id: str = Field(min_length=1, max_length=120)
    topic_vi: str = Field(min_length=1, max_length=200)
    audience_age_min: int = Field(ge=3, le=18)
    audience_age_max: int = Field(ge=3, le=18)
    duration_seconds: float = Field(ge=5.0, le=45.0)
    source_claims: tuple[str, ...] = Field(min_length=1, max_length=16)
    scenes: tuple[WhiteboardStoryboardSceneV1, ...] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def validate_storyboard(self) -> WhiteboardStoryboardV1:
        if self.audience_age_min > self.audience_age_max:
            raise ValueError("minimum audience age must not exceed maximum age")
        if len({scene.scene_id for scene in self.scenes}) != len(self.scenes):
            raise ValueError("storyboard scene IDs must be unique")
        total = sum(scene.duration_seconds for scene in self.scenes)
        if abs(total - self.duration_seconds) > 0.01:
            raise ValueError("storyboard duration must equal the sum of scene durations")
        source_claims = set(self.source_claims)
        if any(not source_claims.intersection(scene.source_claims) for scene in self.scenes):
            raise ValueError("every scene must remain grounded in a source claim")
        return self


__all__ = [
    "WhiteboardStoryboardPreviewRequestV1",
    "WhiteboardStoryboardSceneV1",
    "WhiteboardStoryboardV1",
]
