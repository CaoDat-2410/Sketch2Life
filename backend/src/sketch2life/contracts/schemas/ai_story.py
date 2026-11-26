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
        _validate_display_text(self.title)
        for value in self.story.values():
            _validate_display_text(value, complete_sentence=True)
        total = 0
        cursor = 0
        for expected_index, scene in enumerate(self.scenes, start=1):
            if scene.scene_index != expected_index or scene.start_ms != cursor:
                raise ValueError("scenes must be sequential and have contiguous timing")
            _validate_display_text(scene.title)
            _validate_display_text(scene.action, complete_sentence=True)
            _validate_display_text(scene.narration, complete_sentence=True)
            _validate_display_text(scene.visual_prompt)
            for anchor in scene.character_anchors:
                _validate_display_text(anchor)
            cursor += scene.duration_ms
            total += scene.duration_ms
        if total != self.duration_ms or not 30_000 <= total <= 90_000:
            raise ValueError("scene timing must sum to duration_ms within 30–90 seconds")
        return self


class ConfirmStoryRevisionRequest(StrictAiModel):
    expected_revision: int = Field(ge=1)
    story_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


_INCOMPLETE_VI_SENTENCE_ENDINGS = frozenset(
    {
        "bị", "và", "hoặc", "nếu", "khi", "vì", "để", "với", "của",
        "trong", "trên", "dưới", "cho", "bằng", "từ", "đến", "là", "có",
        "đang", "mà", "nhưng", "rằng", "được",
    }
)


# A location or result word legitimately ends a sentence after these words ("phía trên",
# "leo qua được"). Keep in step with the story worker in deployment/modal/srs_v23.
_COMPLETE_ENDING_PREFIXES = (
    {
        "trên": frozenset({"bên", "phía", "ở", "lên", "đằng"}),
        "dưới": frozenset({"bên", "phía", "ở", "xuống", "đằng"}),
        "trong": frozenset({"bên", "phía", "ở", "vào", "đằng"}),
        "được": frozenset({"qua", "làm", "tìm", "thấy", "lấy", "đi", "leo", "bò"}),
    }
)


def _has_non_latin_letter(value: str) -> bool:
    return any(
        character.isalpha()
        and "LATIN" not in unicodedata.name(character, "")
        for character in value
    )


def _sentence_is_complete(value: str) -> bool:
    stripped = value.rstrip().rstrip("\"'”’»)]}")
    if not stripped or stripped[-1] not in ".!?…":
        return False
    normalized = unicodedata.normalize("NFC", stripped.casefold())
    for sentence in re.split(r"[.!?…]+", normalized):
        words = re.findall(r"[^\W\d_]+", sentence, flags=re.UNICODE)
        if not words or words[-1] not in _INCOMPLETE_VI_SENTENCE_ENDINGS:
            continue
        previous = words[-2] if len(words) > 1 else ""
        if previous not in _COMPLETE_ENDING_PREFIXES.get(words[-1], frozenset()):
            return False
    return True


def _validate_display_text(value: str, *, complete_sentence: bool = False) -> None:
    if _has_non_latin_letter(value):
        raise ValueError("STORY_TEXT_NON_LATIN_SCRIPT")
    if complete_sentence and not _sentence_is_complete(value):
        raise ValueError("STORY_TEXT_INCOMPLETE")


__all__ = [
    "ConfirmStoryRevisionRequest",
    "ParentStoryGenerationRequest",
    "StoryRevisionDraftV1",
    "StorySceneV1",
]
