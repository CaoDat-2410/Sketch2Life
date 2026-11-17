"""Versioned HTTP payloads for the task-scoped BE1 runtime API."""

from __future__ import annotations

import hashlib
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
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class CreateClassRequest(Be1Request):
    display_name: DisplayName


class CreateAssignmentRequest(Be1Request):
    subject: Annotated[str, StringConstraints(min_length=1, max_length=256)]


class CreateProfileRequest(Be1Request):
    class_id: Identifier
    display_name: Annotated[
        str,
        StringConstraints(min_length=11, max_length=200, pattern=r"^Synthetic .+$"),
    ]
    age_months: int = Field(ge=36, le=120)


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
    code: str
    message: str
    request_id: str


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
