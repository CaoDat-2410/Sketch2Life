"""HTTP contracts for the provider-neutral story-video job."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from sketch2life.contracts.schemas.story_video import ApprovedStoryPackageV1, StoryScriptSegmentV1


class StoryVideoCreateRequestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["StoryVideoCreateRequestV1"] = "StoryVideoCreateRequestV1"
    version: Literal["1.0"] = "1.0"
    idempotency_key: str = Field(min_length=1, max_length=200)
    package: ApprovedStoryPackageV1
    segments: tuple[StoryScriptSegmentV1, ...] = Field(min_length=1, max_length=12)


__all__ = ["StoryVideoCreateRequestV1"]
