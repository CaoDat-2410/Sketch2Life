"""Versioned HTTP DTOs for the no-AI Lesson Library API."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

OpaqueId = Annotated[str, Field(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9._:-]+$")]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
ShortText = Annotated[str, Field(min_length=1, max_length=4000)]


class StrictLessonModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LessonActivityInputV1(StrictLessonModel):
    title: Annotated[str, Field(min_length=1, max_length=160)]
    objective: Annotated[str, Field(min_length=1, max_length=1000)]
    materials_text: Annotated[str, Field(max_length=2000)] = ""
    preparation_text: Annotated[str, Field(max_length=2000)] = ""
    instructions_text: Annotated[str, Field(min_length=1, max_length=5000)]
    observation_notes: Annotated[str, Field(max_length=3000)] = ""
    safety_notes: Annotated[str, Field(max_length=3000)] = ""
    activity_kind: Literal["outdoor", "indoor", "mixed"] = "outdoor"


class LessonContentInputV1(StrictLessonModel):
    locale: Literal["vi-VN"] = "vi-VN"
    title: Annotated[str, Field(min_length=1, max_length=160)]
    topic: Annotated[str, Field(min_length=1, max_length=120)]
    target_age_band_ref: OpaqueId
    target_age_band_version: int = Field(ge=1)
    objectives: list[Annotated[str, Field(min_length=1, max_length=1000)]] = Field(
        min_length=1, max_length=12
    )
    drawing_subject: Annotated[str, Field(min_length=1, max_length=160)]
    drawing_steps_text: Annotated[str, Field(min_length=1, max_length=4000)]
    subject_learning_notes: Annotated[str, Field(min_length=1, max_length=5000)]
    script_direction: Annotated[str, Field(max_length=2000)] | None = None
    script_following_allowed: bool = False
    activities: list[LessonActivityInputV1] = Field(min_length=1, max_length=24)

    @model_validator(mode="after")
    def no_blank_items(self) -> LessonContentInputV1:
        if any(not value.strip() for value in self.objectives):
            raise ValueError("objectives must not be blank")
        if self.script_direction is not None and not self.script_direction.strip():
            raise ValueError("script_direction must be null or non-empty")
        return self


class CreateLessonRequestV1(StrictLessonModel):
    contract: Literal["CreateLessonRequestV1"] = "CreateLessonRequestV1"
    content: LessonContentInputV1
    visibility: Literal["PRIVATE", "SCHOOL"] = "PRIVATE"


class UpdateLessonRequestV1(StrictLessonModel):
    contract: Literal["UpdateLessonRequestV1"] = "UpdateLessonRequestV1"
    content: LessonContentInputV1


class CreateLessonVersionRequestV1(StrictLessonModel):
    contract: Literal["CreateLessonVersionRequestV1"] = "CreateLessonVersionRequestV1"
    source_document_revision_id: OpaqueId
    content: LessonContentInputV1


class CreateLessonUploadSessionRequestV1(StrictLessonModel):
    contract: Literal["CreateLessonUploadSessionRequestV1"] = "CreateLessonUploadSessionRequestV1"
    file_name: Annotated[str, Field(min_length=1, max_length=255)]
    media_type: Annotated[str, Field(min_length=1, max_length=128)]
    byte_length: int = Field(ge=1, le=25_000_000)
    sha256: Sha256Hex


class CreateLessonAccessGrantRequestV1(StrictLessonModel):
    contract: Literal["CreateLessonAccessGrantRequestV1"] = "CreateLessonAccessGrantRequestV1"
    version_id: OpaqueId
    audience_kind: Literal["PUBLIC", "ORGANIZATION", "PRINCIPAL", "PARENT_GROUP"]
    audience_ref: OpaqueId | None = None
    capability: Literal["VIEW", "DOWNLOAD", "REUSE"]
    expires_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def target_shape(self) -> CreateLessonAccessGrantRequestV1:
        if self.audience_kind == "PUBLIC" and self.audience_ref is not None:
            raise ValueError("PUBLIC grants cannot include audience_ref")
        if self.audience_kind != "PUBLIC" and self.audience_ref is None:
            raise ValueError("audience_ref is required for this audience")
        return self


class DecideLessonAccessGrantRequestV1(StrictLessonModel):
    contract: Literal["DecideLessonAccessGrantRequestV1"] = "DecideLessonAccessGrantRequestV1"
    decision: Literal["APPROVE", "REQUEST_CHANGES"]
    reason: Annotated[str, Field(max_length=1000)] | None = None

    @model_validator(mode="after")
    def request_changes_needs_reason(self) -> DecideLessonAccessGrantRequestV1:
        if self.decision == "REQUEST_CHANGES" and not (self.reason or "").strip():
            raise ValueError("reason is required when requesting changes")
        if self.reason is not None and not self.reason.strip():
            raise ValueError("reason must be null or non-empty")
        return self


class CreateParentGroupRequestV1(StrictLessonModel):
    contract: Literal["CreateParentGroupRequestV1"] = "CreateParentGroupRequestV1"
    display_name: Annotated[str, Field(min_length=1, max_length=120)]


class InviteParentToGroupRequestV1(StrictLessonModel):
    contract: Literal["InviteParentToGroupRequestV1"] = "InviteParentToGroupRequestV1"
    parent_principal_ref: OpaqueId


class ModerateLessonRequestV1(StrictLessonModel):
    contract: Literal["ModerateLessonRequestV1"] = "ModerateLessonRequestV1"
    state: Literal["HIDDEN", "VISIBLE"]
    reason: Annotated[str, Field(min_length=1, max_length=1000)]


class LessonVersionV1(StrictLessonModel):
    contract: Literal["LessonVersionV1"] = "LessonVersionV1"
    lesson_id: OpaqueId
    version_id: OpaqueId
    version_no: int = Field(ge=1)
    review_state: Literal["DRAFT", "PENDING_REVIEW", "CHANGES_REQUESTED", "APPROVED"]
    structured_content_hash: Sha256Hex
    source_document_revision_id: OpaqueId | None = None
    authored_principal_ref: OpaqueId
    created_at: AwareDatetime
    content: LessonContentInputV1 | None = None


class LessonDetailV1(StrictLessonModel):
    contract: Literal["LessonDetailV1"] = "LessonDetailV1"
    lesson_id: OpaqueId
    organization_id: OpaqueId
    owner_kind: Literal["ORGANIZATION"] = "ORGANIZATION"
    created_by: OpaqueId
    state: Literal["ACTIVE", "ARCHIVED"]
    visibility: Literal["PRIVATE", "SCHOOL", "SELECTED_AUDIENCE", "PUBLIC"]
    moderation_state: Literal["VISIBLE", "HIDDEN"] = "VISIBLE"
    current_version: LessonVersionV1
    revision: int = Field(ge=1)
    created_at: AwareDatetime
    updated_at: AwareDatetime


class LessonSummaryV1(StrictLessonModel):
    contract: Literal["LessonSummaryV1"] = "LessonSummaryV1"
    lesson_id: OpaqueId
    title: str
    topic: str
    current_version_no: int = Field(ge=1)
    review_state: str
    visibility: str
    activity_count: int = Field(ge=0)
    updated_at: AwareDatetime


class LessonPageV1(StrictLessonModel):
    contract: Literal["LessonPageV1"] = "LessonPageV1"
    items: list[LessonSummaryV1]
    next_cursor: str | None


class LessonAccessGrantV1(StrictLessonModel):
    contract: Literal["LessonAccessGrantV1"] = "LessonAccessGrantV1"
    access_grant_id: OpaqueId
    lesson_id: OpaqueId
    version_id: OpaqueId
    audience_kind: str
    audience_ref: OpaqueId | None = None
    capability: str
    state: str
    granted_by: OpaqueId
    approved_by: OpaqueId | None = None
    approved_at: AwareDatetime | None = None
    expires_at: AwareDatetime | None = None
    revoked_at: AwareDatetime | None = None
    revision: int = Field(ge=1)


class LessonAccessGrantPageV1(StrictLessonModel):
    contract: Literal["LessonAccessGrantPageV1"] = "LessonAccessGrantPageV1"
    items: list[LessonAccessGrantV1]
    next_cursor: str | None


class UploadSessionV1(StrictLessonModel):
    contract: Literal["UploadSessionV1"] = "UploadSessionV1"
    upload_session_id: OpaqueId
    state: str
    part_size_bytes: int = Field(ge=1)
    expected_parts: int = Field(ge=1)
    accepted_part_numbers: list[int]
    expires_at: AwareDatetime


class UploadPartReceiptV1(StrictLessonModel):
    contract: Literal["UploadPartReceiptV1"] = "UploadPartReceiptV1"
    part_number: int = Field(ge=1)
    byte_length: int = Field(ge=1)
    sha256: Sha256Hex
    accepted: bool


class LessonSourceDocumentStatusV1(StrictLessonModel):
    contract: Literal["LessonSourceDocumentStatusV1"] = "LessonSourceDocumentStatusV1"
    source_document_id: OpaqueId
    state: str
    safe_file_name: str
    file_extension: str
    page_or_slide_count: int | None = None
    warnings: list[str]
    parser_version: str | None = None
    asset_sha256: Sha256Hex
    revision_id: OpaqueId | None = None


class LessonDocumentRevisionPreviewV1(StrictLessonModel):
    contract: Literal["LessonDocumentRevisionPreviewV1"] = "LessonDocumentRevisionPreviewV1"
    revision_id: OpaqueId
    extracted_fields: dict[str, object]
    warnings: list[str]
    page_coverage: list[int]
    review_state: str
    parser_version: str


class LessonAccessGrantDecisionResponseV1(StrictLessonModel):
    contract: Literal["LessonAccessGrantDecisionResponseV1"] = "LessonAccessGrantDecisionResponseV1"
    access_grant_id: OpaqueId
    state: Literal["ACTIVE", "CHANGES_REQUESTED"]
    approved_by: OpaqueId | None
    decided_at: AwareDatetime
    revision: int = Field(ge=1)


class ParentGroupV1(StrictLessonModel):
    contract: Literal["ParentGroupV1"] = "ParentGroupV1"
    parent_group_id: OpaqueId
    organization_id: OpaqueId
    display_name: str
    state: Literal["ACTIVE", "ARCHIVED"]
    created_at: AwareDatetime


class ParentGroupPageV1(StrictLessonModel):
    contract: Literal["ParentGroupPageV1"] = "ParentGroupPageV1"
    items: list[ParentGroupV1]
    next_cursor: str | None


class ParentGroupMembershipV1(StrictLessonModel):
    contract: Literal["ParentGroupMembershipV1"] = "ParentGroupMembershipV1"
    membership_id: OpaqueId
    parent_group_id: OpaqueId
    state: Literal["INVITED", "ACTIVE", "REVOKED", "EXPIRED"]
    invited_at: AwareDatetime
    expires_at: AwareDatetime | None = None
    accepted_at: AwareDatetime | None = None
    revision: int = Field(ge=1)


class ParentGroupInvitationPageV1(StrictLessonModel):
    contract: Literal["ParentGroupInvitationPageV1"] = "ParentGroupInvitationPageV1"
    items: list[ParentGroupMembershipV1]
    next_cursor: str | None


class ParentGroupInvitationV1(ParentGroupMembershipV1):
    contract: Literal["ParentGroupInvitationV1"] = "ParentGroupInvitationV1"


class LessonInvitationPageV1(StrictLessonModel):
    contract: Literal["LessonInvitationPageV1"] = "LessonInvitationPageV1"
    items: list[LessonAccessGrantV1]
    next_cursor: str | None


class ParentLessonSummaryV1(StrictLessonModel):
    contract: Literal["ParentLessonSummaryV1"] = "ParentLessonSummaryV1"
    lesson_id: OpaqueId
    version_id: OpaqueId
    title: str
    topic: str
    target_age_band_ref: OpaqueId
    target_age_band_version: int = Field(ge=1)
    activity_count: int = Field(ge=1)
    access_source: Literal["PUBLIC", "SHARED"]


class ParentLessonPageV1(StrictLessonModel):
    contract: Literal["ParentLessonPageV1"] = "ParentLessonPageV1"
    items: list[ParentLessonSummaryV1]
    next_cursor: str | None


class ParentLessonDetailV1(StrictLessonModel):
    contract: Literal["ParentLessonDetailV1"] = "ParentLessonDetailV1"
    lesson_id: OpaqueId
    version_id: OpaqueId
    version_no: int = Field(ge=1)
    title: str
    topic: str
    locale: Literal["vi-VN"] = "vi-VN"
    target_age_band_ref: OpaqueId
    target_age_band_version: int = Field(ge=1)
    objectives: list[str]
    drawing_subject: str
    drawing_steps_text: str
    subject_learning_notes: str
    script_direction: str | None
    script_following_allowed: bool
    activities: list[LessonActivityInputV1]
    access_source: Literal["PUBLIC", "SHARED"]
    access_expires_at: AwareDatetime | None


class LessonExportV1(ParentLessonDetailV1):
    contract: Literal["LessonExportV1"] = "LessonExportV1"


class LessonModerationV1(StrictLessonModel):
    contract: Literal["LessonModerationV1"] = "LessonModerationV1"
    lesson_id: OpaqueId
    state: Literal["HIDDEN", "VISIBLE"]
    reason: str
    moderator_ref: OpaqueId
    decided_at: AwareDatetime
    revision: int = Field(ge=1)


__all__ = [name for name in globals() if name.endswith("V1")]
