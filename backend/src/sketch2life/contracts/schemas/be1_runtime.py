"""Versioned HTTP payloads for the task-scoped BE1 runtime API."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    StringConstraints,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

from sketch2life.contracts.schemas.support_needs import (
    require_one_value,
    validated_category,
    validated_note,
)
from sketch2life.domain.be1_profile_revisions import (
    INTEREST_MAX_ITEMS,
    ProfileRevisionRuleViolation,
    has_control_character,
    normalize_interests,
)
from sketch2life.domain.support_needs import (
    MAX_CATEGORY_CHARS,
    MAX_NOTE_CHARS,
    MAX_REVISION,
)


class Be1Request(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


DisplayName = Annotated[str, StringConstraints(min_length=1, max_length=200)]
Identifier = Annotated[str, StringConstraints(min_length=1, max_length=128)]
PurposeRef = Annotated[str, StringConstraints(min_length=1, max_length=128)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class CreateClassRequest(Be1Request):
    display_name: DisplayName


class CreateAssignmentRequest(Be1Request):
    """FEAT-066 M9-B (O-3b): the opaque candidate ref from the candidate list, never a subject."""

    candidate_ref: Annotated[str, StringConstraints(min_length=1, max_length=36)]


class CreateProfileRequest(Be1Request):
    """T-7c (SRS l.543, l.1651): the class is the path only; the server decides the data origin.

    Every profile written today is `SYNTHETIC_DEV`, so the `Synthetic ` name rule holds for every
    create whatever the flags (T-7c-DEC-3). `consent_id` is the reference a real-data create
    would carry; it is refused while real data is off and, when on, the create is still refused
    until X-19 defines a valid consent state (T-7c-DEC-5).
    """

    display_name: Annotated[
        str,
        StringConstraints(min_length=11, max_length=200, pattern=r"^Synthetic .+$"),
    ]
    age_months: int = Field(ge=36, le=120)
    consent_id: Identifier | None = None


class EditProfileRequest(Be1Request):
    """T-12b (SRS l.497, l.829, l.1651, l.1697): a Teacher edit of one managed profile.

    The expected revision is the head revision number the client last read; at least one of the
    three editable fields must be sent and an omitted field keeps its value. An explicit null is
    refused. The `Synthetic ` name rule of the create schema holds for an edited name (every
    profile written today is synthetic); the age keeps the new-value range of 36 to 120 months.
    """

    expected_revision: int = Field(ge=1)
    display_name: (
        Annotated[
            str,
            StringConstraints(min_length=11, max_length=200, pattern=r"^Synthetic .+$"),
        ]
        | None
    ) = None
    age_months: int | None = Field(default=None, ge=36, le=120)
    structured_interests: list[str] | None = Field(default=None, max_length=INTEREST_MAX_ITEMS)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str | None) -> str | None:
        if value is not None and has_control_character(value):
            raise ValueError("INVALID_FORMAT")
        return value

    @field_validator("structured_interests")
    @classmethod
    def validate_interests(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        try:
            return list(normalize_interests(value))
        except ProfileRevisionRuleViolation as exc:
            if exc.code == "DIAGNOSIS_LIKE":
                raise PydanticCustomError(
                    "diagnosis_like", "value must not name a diagnosis"
                ) from None
            raise ValueError(exc.code) from None

    @model_validator(mode="before")
    @classmethod
    def refuse_null_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for name in ("display_name", "age_months", "structured_interests"):
                if name in data and data[name] is None:
                    raise ValueError(f"{name} must not be null")
        return data

    @model_validator(mode="after")
    def require_one_editable_field(self) -> EditProfileRequest:
        if not self.model_fields_set & {"display_name", "age_months", "structured_interests"}:
            raise ValueError("at least one editable field is required")
        return self


class MoveProfileRequest(Be1Request):
    """T-7d (SRS l.544, l.1651, l.1699): move a child to another class of the same Teacher.

    The source class is the path; the source revision is the strong ``If-Match``; the target is
    named here with the revision the client last read (both checked, source first).
    """

    target_class_id: Identifier
    target_class_revision: int = Field(ge=1)


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
    profile_version: str | None = Field(default=None, max_length=64)
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


class CanvasReconnectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["Be1CanvasReconnectV1"]
    canvas_id: Identifier
    turn_id: Identifier | None
    profile_version: str | None = Field(default=None, max_length=64)
    document_epoch: int = Field(ge=1)
    current_revision: int = Field(ge=0)
    checkpoint: dict[str, Any] | None
    operations: list[dict[str, Any]]


class CanvasSourceOperationV1(Be1Request):
    operation_id: Identifier
    participant_id: Identifier
    document_epoch: int = Field(ge=1)
    resulting_revision: int = Field(ge=2)
    operation_payload: dict[str, Any]
    payload_sha256: Sha256

    @model_validator(mode="after")
    def validate_payload_digest(self) -> CanvasSourceOperationV1:
        if _canonical_sha256(self.operation_payload) != self.payload_sha256:
            raise ValueError("operation payload digest does not match")
        return self


class CanvasSourceOperationManifestV1(Be1Request):
    operation_id: Identifier
    participant_id: Identifier
    document_epoch: int = Field(ge=1)
    resulting_revision: int = Field(ge=2)
    payload_sha256: Sha256


def _canvas_source_document_payload(
    *,
    canvas_id: str,
    document_epoch: int,
    document_revision: int,
    operations: list[CanvasSourceOperationV1],
) -> dict[str, object]:
    return {
        "canvas_id": canvas_id,
        "document_epoch": document_epoch,
        "document_revision": document_revision,
        "operations": [
            {
                "operation_id": operation.operation_id,
                "participant_id": operation.participant_id,
                "document_epoch": operation.document_epoch,
                "resulting_revision": operation.resulting_revision,
                "operation_payload": operation.operation_payload,
            }
            for operation in operations
        ],
    }


def _canvas_source_binding_payload(
    *,
    organization_id: str,
    session_id: str,
    canvas_id: str,
    profile_id: str,
    profile_version: str,
    document_epoch: int,
    document_revision: int,
    canonical_document_sha256: str,
    operation_manifest_sha256: str,
) -> dict[str, object]:
    return {
        "contract": "CanvasSourceExportV1",
        "organization_id": organization_id,
        "session_id": session_id,
        "canvas_id": canvas_id,
        "profile_id": profile_id,
        "profile_version": profile_version,
        "document_epoch": document_epoch,
        "document_revision": document_revision,
        "canonical_document_sha256": canonical_document_sha256,
        "operation_manifest_sha256": operation_manifest_sha256,
    }


class CanvasSourceExportV1(Be1Request):
    contract: Literal["CanvasSourceExportV1"]
    organization_id: Identifier
    session_id: Identifier
    canvas_id: Identifier
    profile_id: Literal["canvas-operation-profile-v1"]
    profile_version: Literal["CanvasOperationProfileV1"]
    document_epoch: int = Field(ge=1)
    document_revision: int = Field(ge=2)
    operations: list[CanvasSourceOperationV1] = Field(min_length=1)
    operation_manifest: list[CanvasSourceOperationManifestV1] = Field(min_length=1)
    operation_manifest_sha256: Sha256
    canonical_document_sha256: Sha256
    source_sha256: Sha256
    source_ref: Annotated[
        str,
        StringConstraints(pattern=r"^be1-canvas-source-v1:[0-9a-f]{64}$"),
    ]

    @classmethod
    def from_operations(
        cls,
        *,
        organization_id: str,
        session_id: str,
        canvas_id: str,
        document_epoch: int,
        document_revision: int,
        operations: list[CanvasSourceOperationV1],
    ) -> CanvasSourceExportV1:
        manifest = [
            CanvasSourceOperationManifestV1(
                operation_id=operation.operation_id,
                participant_id=operation.participant_id,
                document_epoch=operation.document_epoch,
                resulting_revision=operation.resulting_revision,
                payload_sha256=operation.payload_sha256,
            )
            for operation in operations
        ]
        manifest_digest = _canonical_sha256([item.model_dump(mode="json") for item in manifest])
        document_digest = _canonical_sha256(
            _canvas_source_document_payload(
                canvas_id=canvas_id,
                document_epoch=document_epoch,
                document_revision=document_revision,
                operations=operations,
            )
        )
        binding = _canvas_source_binding_payload(
            organization_id=organization_id,
            session_id=session_id,
            canvas_id=canvas_id,
            profile_id="canvas-operation-profile-v1",
            profile_version="CanvasOperationProfileV1",
            document_epoch=document_epoch,
            document_revision=document_revision,
            canonical_document_sha256=document_digest,
            operation_manifest_sha256=manifest_digest,
        )
        source_digest = _canonical_sha256(binding)
        return cls(
            contract="CanvasSourceExportV1",
            organization_id=organization_id,
            session_id=session_id,
            canvas_id=canvas_id,
            profile_id="canvas-operation-profile-v1",
            profile_version="CanvasOperationProfileV1",
            document_epoch=document_epoch,
            document_revision=document_revision,
            operations=operations,
            operation_manifest=manifest,
            operation_manifest_sha256=manifest_digest,
            canonical_document_sha256=document_digest,
            source_sha256=source_digest,
            source_ref=f"be1-canvas-source-v1:{source_digest}",
        )

    @model_validator(mode="after")
    def validate_complete_binding(self) -> CanvasSourceExportV1:
        revisions = [operation.resulting_revision for operation in self.operations]
        if revisions != list(range(2, self.document_revision + 1)):
            raise ValueError("source operations must cover the complete revision history")
        if len({operation.operation_id for operation in self.operations}) != len(self.operations):
            raise ValueError("source operation identifiers must be unique")
        if any(operation.document_epoch != self.document_epoch for operation in self.operations):
            raise ValueError("source operations must share the exported epoch")

        expected_manifest = [
            CanvasSourceOperationManifestV1(
                operation_id=operation.operation_id,
                participant_id=operation.participant_id,
                document_epoch=operation.document_epoch,
                resulting_revision=operation.resulting_revision,
                payload_sha256=operation.payload_sha256,
            ).model_dump(mode="json")
            for operation in self.operations
        ]
        actual_manifest = [item.model_dump(mode="json") for item in self.operation_manifest]
        if actual_manifest != expected_manifest:
            raise ValueError("operation manifest must exactly match the exported operations")

        manifest_digest = _canonical_sha256(actual_manifest)
        if manifest_digest != self.operation_manifest_sha256:
            raise ValueError("operation manifest digest does not match")
        document_digest = _canonical_sha256(
            _canvas_source_document_payload(
                canvas_id=self.canvas_id,
                document_epoch=self.document_epoch,
                document_revision=self.document_revision,
                operations=self.operations,
            )
        )
        if document_digest != self.canonical_document_sha256:
            raise ValueError("canonical document digest does not match")
        source_digest = _canonical_sha256(
            _canvas_source_binding_payload(
                organization_id=self.organization_id,
                session_id=self.session_id,
                canvas_id=self.canvas_id,
                profile_id=self.profile_id,
                profile_version=self.profile_version,
                document_epoch=self.document_epoch,
                document_revision=self.document_revision,
                canonical_document_sha256=self.canonical_document_sha256,
                operation_manifest_sha256=self.operation_manifest_sha256,
            )
        )
        if source_digest != self.source_sha256 or self.source_ref != (
            f"be1-canvas-source-v1:{source_digest}"
        ):
            raise ValueError("source reference binding does not match")
        return self


class Be1Response(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Be1ProfileAgeBandV1(Be1Response):
    band_version: int
    band_code: str


class Be1ProfileRevisionV1(Be1Response):
    """One immutable profile revision. The author is never part of the answer (T-12b)."""

    contract: Literal["Be1ProfileRevisionV1"]
    child_id: Identifier
    profile_revision_id: Annotated[str, StringConstraints(min_length=1, max_length=36)]
    revision_no: int = Field(ge=1)
    display_name: DisplayName
    age_months: int
    age_band: Be1ProfileAgeBandV1 | None
    structured_interests: list[str]
    revision_hash: Sha256
    created_at: datetime


class Be1ProfileRevisionPageV1(Be1Response):
    contract: Literal["Be1ProfileRevisionPageV1"]
    items: list[Be1ProfileRevisionV1]
    next_cursor: str | None


class Be1ProfileEditResultV1(Be1Response):
    contract: Literal["Be1ProfileEditResultV1"]
    child_id: Identifier
    profile_revision_id: Annotated[str, StringConstraints(min_length=1, max_length=36)]
    revision_no: int = Field(ge=1)
    revision_hash: Sha256


class Be1SupportNeedsPutV1(Be1Request):
    """T-12c: replace the encrypted support needs of a managed profile.

    ``expected_revision`` 0 means no record yet. Both keys are required and nullable, and the text
    is kept exactly as sent (no whitespace stripping), so the model overrides the base config.
    Validation errors name the field and a code, never the submitted text.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    expected_revision: StrictInt = Field(ge=0, le=MAX_REVISION)
    category: StrictStr | None = Field(max_length=MAX_CATEGORY_CHARS)
    note: StrictStr | None = Field(max_length=MAX_NOTE_CHARS)

    @field_validator("category")
    @classmethod
    def category_rules(cls, value: str | None) -> str | None:
        return validated_category(value)

    @field_validator("note")
    @classmethod
    def note_rules(cls, value: str | None) -> str | None:
        return validated_note(value)

    @model_validator(mode="after")
    def at_least_one_value(self) -> Be1SupportNeedsPutV1:
        require_one_value(self.category, self.note)
        return self


class Be1SupportNeedsV1(Be1Response):
    """The decrypted record; revision 0 means no record (both values null)."""

    contract: Literal["Be1SupportNeedsV1"]
    child_id: Identifier
    revision: int = Field(ge=0)
    category: str | None
    note: str | None


class Be1SupportNeedsWriteV1(Be1Response):
    """The safe answer of a write: the new revision only, never a value."""

    contract: Literal["Be1SupportNeedsWriteV1"]
    child_id: Identifier
    revision: int = Field(ge=1)


class Be1PilotProfileItem(Be1Request):
    child_id: Identifier
    display_name: DisplayName


class Be1PilotProfileListResponse(Be1Request):
    contract: Literal["Be1PilotProfileListV1"]
    items: list[Be1PilotProfileItem]


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
    """CONV-1 error envelope (SRS §9.8 fields plus `request_id`; published as `ApiError`)."""

    code: str
    message: str
    correlation_id: str
    retryable: bool
    retry_after_seconds: int | None = None
    field_errors: list[dict[str, str]] | None = None
    request_id: str
    current_version: int | None = None


__all__ = [
    "AdmitDeviceRequest",
    "AssignMemberRequest",
    "Be1Error",
    "CanvasCheckpointRequest",
    "CanvasOperationRequest",
    "CanvasReconnectResponse",
    "CanvasSourceExportV1",
    "CanvasSourceOperationManifestV1",
    "CanvasSourceOperationV1",
    "Be1PilotProfileItem",
    "Be1PilotProfileListResponse",
    "Be1ProfileAgeBandV1",
    "Be1ProfileEditResultV1",
    "Be1ProfileRevisionPageV1",
    "Be1ProfileRevisionV1",
    "Be1SupportNeedsPutV1",
    "Be1SupportNeedsV1",
    "Be1SupportNeedsWriteV1",
    "CanvasRestoreRequest",
    "CreateAssignmentRequest",
    "CreateClassRequest",
    "CreateGroupRequest",
    "CreateProfileRequest",
    "CreateSessionRequest",
    "DataRequestCreate",
    "EditProfileRequest",
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
