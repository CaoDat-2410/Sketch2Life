"""Versioned contracts for SRS-aligned Parent story drafts."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictAiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ParentStoryGenerationRequest(StrictAiModel):
    expected_understanding_revision: int = Field(ge=1)
    adult_confirmed_idea: str = Field(default="", max_length=500)
    rewrite_instruction: str | None = Field(default=None, min_length=1, max_length=400)


class StorySceneV1(StrictAiModel):
    scene_index: int = Field(ge=1, le=15)
    title: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=500)
    visual_prompt: str = Field(min_length=1, max_length=900)
    narration: str = Field(min_length=1, max_length=500)
    start_ms: int = Field(ge=0, le=90_000)
    duration_ms: int = Field(ge=1_000, le=20_000)
    character_anchors: list[str] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def validate_anchor_values(self) -> StorySceneV1:
        if any(not item or len(item) > 120 for item in self.character_anchors):
            raise ValueError("character_anchors must contain short visible traits")
        return self


class StoryRevisionDraftV1(StrictAiModel):
    schema_version: Literal["sketch2life.story-revision.v1"]
    language: Literal["vi"]
    title: str = Field(min_length=1, max_length=120)
    story: dict[str, str]
    duration_ms: int = Field(ge=30_000, le=90_000)
    scenes: list[StorySceneV1] = Field(min_length=5, max_length=15)

    @model_validator(mode="after")
    def validate_revision_shape(self) -> StoryRevisionDraftV1:
        if set(self.story) != {"opening", "middle", "ending"} or any(
            not isinstance(value, str) or not value.strip() or len(value) > 900
            for value in self.story.values()
        ):
            raise ValueError("story must contain non-empty opening, middle, and ending sections")
        total = 0
        cursor = 0
        for expected_index, scene in enumerate(self.scenes, start=1):
            if scene.scene_index != expected_index or scene.start_ms != cursor:
                raise ValueError("scenes must be sequential and have contiguous timing")
            cursor += scene.duration_ms
            total += scene.duration_ms
        if total != self.duration_ms or not 30_000 <= total <= 90_000:
            raise ValueError("scene timing must sum to duration_ms within 30–90 seconds")
        return self


class ConfirmStoryRevisionRequest(StrictAiModel):
    expected_revision: int = Field(ge=1)
    story_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def validate_butterfly_lifecycle_v1(story: StoryRevisionDraftV1, *, confirmed_subject: str) -> None:
    """Reject the specific lifecycle errors observed in the prior synthetic run."""

    normalized_subject = _fold(confirmed_subject)
    if "buom" not in normalized_subject and "butterfly" not in normalized_subject:
        return
    text = _fold(
        " ".join(
            [
                story.story["opening"],
                story.story["middle"],
                story.story["ending"],
                *(f"{scene.action} {scene.narration}" for scene in story.scenes),
            ]
        )
    )
    forbidden = (
        r"trung\s+(?:no|nở)\s+(?:(?:ra|thanh)\s+)?(?:con\s+)?buom",
        r"buom(?:\s+\w+){0,4}\s+(?:tim|kiem|xay|lam)\s+(?:mot\s+)?to",
        r"butterfly\s+(?:hatches|looks?\s+for|builds?\s+(?:a\s+)?nest)",
    )
    if any(re.search(pattern, text) for pattern in forbidden):
        raise ValueError("EDUCATIONAL_FACT_FORBIDDEN_CLAIM")

    lifecycle_text = _fold(
        " ".join(story.story[section] for section in ("opening", "middle", "ending"))
    )
    required_stages = (
        r"\btrung\b",
        r"\b(?:sau\s+buom|au\s+trung)\b",
        r"\bnhong\b",
        r"\b(?:buom\s+truong\s+thanh|buom\s+(?:chui|bay)\s+ra\s+khoi\s+nhong)\b",
    )
    positions = [
        (match.start() if (match := re.search(stage, lifecycle_text)) else None)
        for stage in required_stages
    ]
    if any(position is None for position in positions):
        raise ValueError("EDUCATIONAL_FACT_STAGE_MISSING")
    if positions != sorted(positions):
        raise ValueError("EDUCATIONAL_FACT_ORDER_INVALID")


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


__all__ = [
    "ConfirmStoryRevisionRequest",
    "ParentStoryGenerationRequest",
    "StoryRevisionDraftV1",
    "StorySceneV1",
    "validate_butterfly_lifecycle_v1",
]
