"""Versioned Parent platform contracts for profile sharing, inbox, quota and lesson history."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateProfileShareRequestV1(_Strict):
    teacher_subject: str = Field(min_length=1, max_length=128)


class AcceptProfileShareRequestV1(_Strict):
    managed_profile_ref: str = Field(min_length=1, max_length=128)


class ProfileShareGrantV1(_Strict):
    contract: Literal["ParentProfileShareGrantV1"]
    grant_id: UUID
    parent_profile_id: UUID
    teacher_subject: str
    managed_profile_ref: str | None
    state: Literal["INVITED", "ACTIVE", "DECLINED", "REVOKED", "EXPIRED"]
    created_at: datetime
    expires_at: datetime | None
    accepted_at: datetime | None
    revoked_at: datetime | None
    revision: int = Field(ge=1)


class ProfileShareEnvelopeV1(_Strict):
    request_id: UUID
    grant: ProfileShareGrantV1


class ProfileSharePageV1(_Strict):
    contract: Literal["ParentProfileSharePageV1"] = "ParentProfileSharePageV1"
    items: list[ProfileShareGrantV1]


class TeacherProfileShareInvitationV1(_Strict):
    contract: Literal["ParentProfileShareInvitationV1"] = "ParentProfileShareInvitationV1"
    grant_id: UUID
    parent_profile_ref: UUID
    state: Literal["INVITED"]
    created_at: datetime


class TeacherProfileShareInvitationPageV1(_Strict):
    contract: Literal["TeacherProfileShareInvitationPageV1"] = "TeacherProfileShareInvitationPageV1"
    items: list[TeacherProfileShareInvitationV1]


class NotificationInboxItemV1(_Strict):
    contract: Literal["NotificationInboxItemV1"]
    notification_id: UUID
    kind: Literal["PROFILE_SHARE_INVITATION", "PROFILE_SHARE_ACCEPTED", "LESSON_FEEDBACK", "LESSON_REPLY"]
    title: str
    resource_kind: str | None
    resource_ref: str | None
    created_at: datetime
    read_at: datetime | None


class NotificationInboxPageV1(_Strict):
    contract: Literal["NotificationInboxPageV1"] = "NotificationInboxPageV1"
    items: list[NotificationInboxItemV1]
    next_cursor: str | None


class ParentVideoQuotaSummaryV1(_Strict):
    contract: Literal["ParentVideoQuotaSummaryV1"]
    configuration_state: Literal["CONFIGURED", "NOT_CONFIGURED"]
    period_start: datetime
    period_end: datetime
    granted: int | None
    used: int | None
    available: int | None


class LessonDeliveryCreateRequestV1(_Strict):
    lesson_version_id: UUID
    managed_profile_ref: str = Field(min_length=1, max_length=128)


class LessonDeliveryOccurrenceV1(_Strict):
    contract: Literal["LessonDeliveryOccurrenceV1"]
    occurrence_id: UUID
    lesson_id: UUID
    version_id: UUID
    title: str
    topic: str
    delivered_at: datetime


class LessonDeliveryV1(_Strict):
    contract: Literal["ParentLessonDeliveryV1"]
    occurrence_id: UUID
    lesson_id: UUID
    version_id: UUID
    title: str
    topic: str
    delivered_at: datetime
    feedback: dict[str, object] | None
    replies: list[dict[str, object]]


class ParentLessonDeliveryPageV1(_Strict):
    contract: Literal["ParentLessonDeliveryPageV1"] = "ParentLessonDeliveryPageV1"
    items: list[LessonDeliveryV1]
    next_cursor: str | None


class LessonDeliveryFeedbackRequestV1(_Strict):
    parent_profile_id: UUID
    feedback_text: str = Field(min_length=1, max_length=1200)


class LessonDeliveryFeedbackReplyRequestV1(_Strict):
    reply_text: str = Field(min_length=1, max_length=1200)


class LessonDeliveryFeedbackResponseV1(_Strict):
    contract: Literal["LessonDeliveryFeedbackV1"]
    feedback_id: UUID
    feedback_text: str
    created_at: datetime
    updated_at: datetime


class LessonDeliveryFeedbackReplyResponseV1(_Strict):
    contract: Literal["LessonFeedbackReplyV1"]
    reply_id: UUID
    occurrence_id: UUID
    reply_text: str
    created_at: datetime


__all__ = [
    "AcceptProfileShareRequestV1",
    "CreateProfileShareRequestV1",
    "LessonDeliveryCreateRequestV1",
    "LessonDeliveryFeedbackReplyRequestV1",
    "LessonDeliveryFeedbackReplyResponseV1",
    "LessonDeliveryFeedbackRequestV1",
    "LessonDeliveryFeedbackResponseV1",
    "LessonDeliveryOccurrenceV1",
    "NotificationInboxItemV1",
    "NotificationInboxPageV1",
    "ParentLessonDeliveryPageV1",
    "ParentVideoQuotaSummaryV1",
    "ProfileShareEnvelopeV1",
    "ProfileShareGrantV1",
    "ProfileSharePageV1",
    "TeacherProfileShareInvitationPageV1",
    "TeacherProfileShareInvitationV1",
]
