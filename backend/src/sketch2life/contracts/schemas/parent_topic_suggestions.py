"""Versioned Parent topic and drawing-subject suggestion contracts."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParentTopicCardV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    topic_id: str = Field(min_length=2, max_length=48, pattern=r"^[a-z0-9-]+$")
    title_vi: str = Field(min_length=2, max_length=80)
    description_vi: str = Field(min_length=2, max_length=160)


class ParentTopicSuggestionSetV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    contract: Literal["ParentTopicSuggestionSetV1"]
    set_id: str = Field(pattern=r"^pts_[0-9a-f]{24}$")
    draft_id: UUID
    catalog_revision: str = Field(min_length=1, max_length=80)
    cards: list[ParentTopicCardV1] = Field(min_length=3, max_length=3)
    excluded_set_ids: list[str] = Field(default_factory=list, max_length=16)


class ParentDrawingSubjectCardV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    subject_id: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    title_vi: str = Field(min_length=2, max_length=80)
    guide_subject: str = Field(min_length=2, max_length=120)
    relation_to_topic_vi: str | None = Field(default=None, min_length=2, max_length=120)


class ParentDrawingSubjectSuggestionSetV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    contract: Literal["ParentDrawingSubjectSuggestionSetV1"]
    set_id: str = Field(pattern=r"^pds_[0-9a-f]{24}$")
    draft_id: UUID
    topic_id: str = Field(min_length=2, max_length=48, pattern=r"^[a-z0-9-]+$")
    topic: str = Field(min_length=2, max_length=120)
    catalog_revision: str = Field(min_length=1, max_length=80)
    generation_source: Literal["CURATED_CATALOG", "QWEN_DRAFT"] = "CURATED_CATALOG"
    review_required: Literal[True] = True
    cards: list[ParentDrawingSubjectCardV1] = Field(min_length=3, max_length=3)
    excluded_set_ids: list[str] = Field(default_factory=list, max_length=16)


class ParentTopicSubjectDraftItemV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    title_vi: str = Field(min_length=2, max_length=80)
    guide_subject: str = Field(min_length=2, max_length=120)
    relation_to_topic_vi: str = Field(min_length=2, max_length=120)


class ParentTopicSubjectDraftResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["sketch2life.parent-topic-subjects.v1"]
    subjects: list[ParentTopicSubjectDraftItemV1] = Field(min_length=3, max_length=3)


class ParentCustomSubjectValidationRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    topic_id: str = Field(min_length=2, max_length=48, pattern=r"^[a-z0-9-]+$")
    topic: str = Field(min_length=2, max_length=120)
    subject: str = Field(min_length=2, max_length=120)


class ParentCustomSubjectValidationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    contract: Literal["ParentCustomSubjectValidationV1"]
    decision: Literal["ON_TOPIC", "OUT_OF_TOPIC", "NEEDS_CLARIFICATION"]
    normalized_subject: str | None = Field(default=None, max_length=120)
    message_vi: str = Field(min_length=2, max_length=240)


__all__ = [
    "ParentCustomSubjectValidationRequestV1",
    "ParentCustomSubjectValidationV1",
    "ParentDrawingSubjectCardV1",
    "ParentDrawingSubjectSuggestionSetV1",
    "ParentTopicCardV1",
    "ParentTopicSuggestionSetV1",
    "ParentTopicSubjectDraftItemV1",
    "ParentTopicSubjectDraftResponseV1",
]
