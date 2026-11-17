"""Strict BE2-06 offline CMD-36, viewer projection and historical event candidates."""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.sketch_proposals import ChildResponseV1
from sketch2life.contracts.schemas.sketch_reviews import SketchChildPayloadV0

CONTRACT_NAME = "ChildResponseCommand"
CONTRACT_VERSION = "0.1-candidate"
OpaqueId = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Revision = Annotated[int, Field(ge=1)]
Action = Literal["viewed", "hidden", "declined"]
ETag = Annotated[str, Field(min_length=1, max_length=300, pattern=r'^"child-response:[^"]+"$')]


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class ChildResponseCommandV1(_Strict):
    contract_name: Literal["ChildResponseCommand"] = "ChildResponseCommand"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    action: Action
    expected_proposal_version: Revision
    review_ref: OpaqueId
    turn_id: OpaqueId


class ReviewAccessSnapshotV1(_Strict):
    """Allowlisted access result; this participant alone passed the exact review gate."""

    organization_id: OpaqueId
    class_id: OpaqueId
    session_id: OpaqueId
    canvas_id: OpaqueId
    proposal_id: OpaqueId
    proposal_version: Revision
    content_sha256: Sha256Hex
    participant_id: OpaqueId
    review_ref: OpaqueId


class TurnSnapshotV1(_Strict):
    participant_id: OpaqueId
    turn_id: OpaqueId
    turn_revision: Revision | None = None


class ChildResponseOutcomeV1(_Strict):
    contract_name: Literal["ChildResponseOutcome"] = "ChildResponseOutcome"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    applied: bool
    response_id: OpaqueId
    response_revision: Annotated[int, Field(ge=2)]
    etag: ETag
    proposal_id: OpaqueId
    proposal_version: Revision
    content_sha256: Sha256Hex
    review_ref: OpaqueId
    participant_id: OpaqueId
    child_response: ChildResponseV1

    @model_validator(mode="after")
    def _response_is_real_and_attributed(self) -> ChildResponseOutcomeV1:
        if (self.child_response.action == "available"
                or self.child_response.participant_id != self.participant_id):
            raise ValueError("outcome requires an attributed actual response")
        return self


class ChildResponseProjectionV1(_Strict):
    contract_name: Literal["ChildResponseProjection"] = "ChildResponseProjection"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    access: ReviewAccessSnapshotV1
    visibility: Literal["available", "viewed", "hidden", "declined"]
    response_revision: Revision
    etag: ETag
    turn_id: OpaqueId | None
    child_response: ChildResponseV1 | None

    @model_validator(mode="after")
    def _consistent_choice(self) -> ChildResponseProjectionV1:
        if self.child_response is None:
            if self.visibility != "available" or self.response_revision != 1:
                raise ValueError("initial choice is null at virtual revision 1")
        elif (self.child_response.action == "available" or self.response_revision < 2
              or self.child_response.participant_id != self.access.participant_id
              or self.visibility != self.child_response.action):
            raise ValueError("projection must preserve this participant's actual choice")
        return self


class AuthorizedChildReadV1(_Strict):
    contract_name: Literal["AuthorizedChildRead"] = "AuthorizedChildRead"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    access: ReviewAccessSnapshotV1
    payload: SketchChildPayloadV0

    @model_validator(mode="after")
    def _same_exact_result(self) -> AuthorizedChildReadV1:
        if (self.payload.status != "available"
                or self.payload.proposal_id != self.access.proposal_id
                or self.payload.review_ref != self.access.review_ref):
            raise ValueError("read payload must belong to this successful access result")
        return self


class ChildResponseReadV1(_Strict):
    contract_name: Literal["ChildResponseRead"] = "ChildResponseRead"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    projection: ChildResponseProjectionV1
    payload: SketchChildPayloadV0 | None

    @model_validator(mode="after")
    def _same_viewer_read(self) -> ChildResponseReadV1:
        if self.payload is not None:
            if self.projection.visibility == "declined":
                raise ValueError("declined content stays suppressed")
            AuthorizedChildReadV1(access=self.projection.access, payload=self.payload)
        return self


class TeacherResponseEventV1(_Strict):
    contract_name: Literal["TeacherResponseEvent"] = "TeacherResponseEvent"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    event_id: OpaqueId
    response_id: OpaqueId
    operation_key: OpaqueId
    access: ReviewAccessSnapshotV1
    response_revision: Annotated[int, Field(ge=2)]
    turn_id: OpaqueId
    turn_revision: Revision | None
    action: Action
    responded_at: AwareDatetime


def command_fingerprint(proposal_id: str, command: ChildResponseCommandV1) -> str:
    """Hash semantic fields only; request formatting, operation key and ETag are excluded."""

    payload = {"proposal_id": proposal_id, **command.model_dump(mode="json")}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode()).hexdigest()
