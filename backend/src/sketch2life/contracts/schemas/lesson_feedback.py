"""Parent lesson feedback wire contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ParentLessonFeedbackInputV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    feedback_text: Annotated[str, Field(min_length=1, max_length=1200)]


class ParentLessonFeedbackV1(BaseModel):
    contract: Literal["ParentLessonFeedbackV1"] = "ParentLessonFeedbackV1"
    feedback_id: str
    lesson_id: str
    version_id: str
    revision: int
    feedback_text: str
    created_at: AwareDatetime
    updated_at: AwareDatetime
    reply_count: int


class ParentLessonFeedbackStateV1(BaseModel):
    contract: Literal["ParentLessonFeedbackStateV1"] = "ParentLessonFeedbackStateV1"
    lesson_id: str
    feedback: ParentLessonFeedbackV1 | None


class ParentLessonFeedbackReplyV1(BaseModel):
    reply_id: str
    reply_text: str
    created_at: AwareDatetime


class ParentLessonFeedbackReplyPageV1(BaseModel):
    contract: Literal["ParentLessonFeedbackReplyPageV1"] = "ParentLessonFeedbackReplyPageV1"
    feedback_id: str | None
    items: list[ParentLessonFeedbackReplyV1]
    next_cursor: str | None


FeedbackAuthorRole = Literal["parent", "teacher", "school_manager", "platform_admin", "other"]


class LessonFeedbackSummaryV1(BaseModel):
    thread_id: str
    lesson_id: str
    version_id: str
    lesson_title: str | None = None
    version_no: int | None = None
    revision: int
    created_at: AwareDatetime


class LessonFeedbackPageV1(BaseModel):
    total: int
    limit: int
    next_cursor: str | None
    items: list[LessonFeedbackSummaryV1]


class LessonFeedbackMessageV1(BaseModel):
    message_id: str
    body: str
    from_you: bool
    author_role: FeedbackAuthorRole
    author_display_name: str | None = None
    created_at: AwareDatetime


class LessonFeedbackThreadV1(BaseModel):
    thread_id: str
    organization_id: str
    lesson_id: str
    version_id: str
    lesson_title: str | None = None
    version_no: int | None = None
    revision: int
    limit: int
    next_cursor: str | None
    items: list[LessonFeedbackMessageV1]
