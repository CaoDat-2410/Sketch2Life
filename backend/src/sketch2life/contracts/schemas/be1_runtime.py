"""Versioned HTTP payloads for the task-scoped BE1 runtime API."""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


class Be1Request(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


DisplayName = Annotated[str, StringConstraints(min_length=1, max_length=200)]
Identifier = Annotated[str, StringConstraints(min_length=1, max_length=128)]
PurposeRef = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class CreateClassRequest(Be1Request):
    display_name: DisplayName


class CreateAssignmentRequest(Be1Request):
    subject: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    role: Literal["school_admin", "teacher", "guide", "observer"]
    class_id: Identifier | None = None


class CreateProfileRequest(Be1Request):
    child_id: Identifier
    class_id: Identifier
    consent_id: Identifier
    purpose_ref: PurposeRef
    display_name: DisplayName
    age_months: int = Field(ge=36, le=155)


class RecordConsentRequest(Be1Request):
    class_id: Identifier
    child_id: Identifier
    purpose_ref: PurposeRef
    evidence_ref: str | None = Field(default=None, max_length=512)


class CreateSessionRequest(Be1Request):
    class_id: Identifier
    purpose_ref: PurposeRef
    configuration: dict[str, Any] = Field(default_factory=dict, max_length=64)

    @field_validator("configuration")
    @classmethod
    def validate_configuration_size(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > 8192:
            raise ValueError("session configuration exceeds the supported size")
        return value


class SessionTransitionRequest(Be1Request):
    expected_revision: int = Field(ge=1)


class JoinRequest(Be1Request):
    join_code: str = Field(min_length=8, max_length=32)
    device_key: str = Field(min_length=24, max_length=256)


class JoinRoomCodeRequest(Be1Request):
    room_code: str = Field(pattern=r"^[0-9]{6}$")
    device_key: str = Field(min_length=24, max_length=256)


class StageAdvanceRequest(Be1Request):
    expected_stage_revision: int = Field(ge=1)
    target_stage: Literal[
        "join",
        "explore_draw",
        "assistance",
        "sharing",
        "knowledge",
        "off_screen",
        "reflection",
        "completion",
    ]
    assistance_disposition: Literal["not_needed"] | None = None
    unfinished_group_ids: list[Identifier] = Field(default_factory=list, max_length=40)
    unfinished_group_disposition: Literal["save_draft"] | None = None

    @model_validator(mode="after")
    def validate_group_draft_disposition(self) -> StageAdvanceRequest:
        if self.unfinished_group_ids and self.unfinished_group_disposition != "save_draft":
            raise ValueError("unfinished groups require save_draft")
        if len(set(self.unfinished_group_ids)) != len(self.unfinished_group_ids):
            raise ValueError("unfinished_group_ids must be unique")
        return self


class CompleteSessionRequest(Be1Request):
    expected_stage_revision: int = Field(ge=1)
    outcome: Literal["completed", "ended_early"]
    reason_category: Literal["time", "safety", "technical", "other"] | None = None
    teacher_note: str | None = Field(default=None, max_length=240)
    outcome_refs: list[Annotated[str, StringConstraints(min_length=1, max_length=256)]] = Field(
        default_factory=list, max_length=20
    )

    @model_validator(mode="after")
    def validate_outcome_reason(self) -> CompleteSessionRequest:
        if self.outcome == "ended_early" and self.reason_category is None:
            raise ValueError("ended_early requires reason_category")
        if self.outcome == "completed" and self.reason_category is not None:
            raise ValueError("completed does not accept an early-stop reason")
        return self


class AdmitDeviceRequest(Be1Request):
    child_id: Identifier


class CreateGroupRequest(Be1Request):
    display_name: Annotated[str, StringConstraints(min_length=1, max_length=120)]


class AssignMemberRequest(Be1Request):
    child_id: Identifier
    expected_revision: int = Field(ge=1)


class GroupControlRequest(Be1Request):
    action: Literal["lock", "unlock"]
    expected_revision: int = Field(ge=1)


class DataRequestCreate(Be1Request):
    request_type: Literal["export", "delete"]
    target_ref: Annotated[str, StringConstraints(min_length=1, max_length=256)]


class GalleryCreateRequest(Be1Request):
    session_id: Identifier
    artifact_ref: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    audience: Literal["class", "school"]
    contributor_ids: list[Identifier] = Field(min_length=1, max_length=40)
    caption: str | None = Field(default=None, max_length=500)


class ObservationCreateRequest(Be1Request):
    session_id: Identifier
    child_id: Identifier
    kind: Literal["observation", "reflection", "assessment"]
    content: dict[str, Any]
    source_refs: list[Annotated[str, StringConstraints(max_length=256)]] = Field(
        default_factory=list, max_length=20
    )


class GalleryAnnotationRequest(Be1Request):
    text: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class ProgressRequest(Be1Request):
    progress: Literal["not_started", "in_progress", "ready", "completed"]


class CanvasOperationRequest(Be1Request):
    operation_id: Identifier
    turn_id: Identifier
    document_epoch: int = Field(ge=1)
    expected_revision: int = Field(ge=1)
    operation_payload: dict[str, Any]

    @field_validator("operation_payload")
    @classmethod
    def validate_operation_size(cls, value: dict[str, Any]) -> dict[str, Any]:
        if (
            len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
            > 32768
        ):
            raise ValueError("canvas operation exceeds 32 KiB")
        return value


class CanvasCheckpointRequest(Be1Request):
    document_epoch: int = Field(ge=1)
    document_revision: int = Field(ge=1)
    snapshot: dict[str, Any]

    @field_validator("snapshot")
    @classmethod
    def validate_snapshot_size(cls, value: dict[str, Any]) -> dict[str, Any]:
        if (
            len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
            > 2 * 1024 * 1024
        ):
            raise ValueError("canvas checkpoint exceeds 2 MiB")
        return value


class CanvasRestoreRequest(Be1Request):
    checkpoint_id: Identifier
    expected_revision: int = Field(ge=1)


class Be1Error(BaseModel):
    code: str
    message: str
    request_id: str


__all__ = [
    "AdmitDeviceRequest",
    "AssignMemberRequest",
    "Be1Error",
    "CanvasCheckpointRequest",
    "CanvasOperationRequest",
    "CanvasRestoreRequest",
    "CreateAssignmentRequest",
    "CreateClassRequest",
    "CreateGroupRequest",
    "CreateProfileRequest",
    "CreateSessionRequest",
    "DataRequestCreate",
    "GalleryCreateRequest",
    "GalleryAnnotationRequest",
    "GroupControlRequest",
    "JoinRequest",
    "JoinRoomCodeRequest",
    "StageAdvanceRequest",
    "CompleteSessionRequest",
    "ObservationCreateRequest",
    "ProgressRequest",
    "RecordConsentRequest",
    "SessionTransitionRequest",
]
