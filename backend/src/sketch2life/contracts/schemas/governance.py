"""BE2-12 fixed DATA-33 routing/response contracts; owner payloads bind separately."""

from __future__ import annotations

import json
from typing import Literal

from pydantic import AwareDatetime, Field, ValidationError, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex, ShortText
from sketch2life.contracts.schemas.learning_content import (
    ContentStatus,
    PublicationReviewSet,
    StrictContentModel,
)

GovernanceAction = Literal[
    "create", "edit", "submit_review", "record_review", "request_changes", "publish",
    "recall", "archive"]
GovernanceBranch = Literal["learning_content", "preset", "ai_policy", "core_policy"]


class GovernanceSelection(StrictContentModel):
    """Routing facts only. Never treat selection success as payload validation."""

    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    record_kind: Literal["learning_content", "preset", "policy"]
    policy_kind: Literal["ai", "core"] | None = None
    action: GovernanceAction
    client_request_id: OpaqueId

    @model_validator(mode="after")
    def branch_scope(self) -> GovernanceSelection:
        if (self.record_kind == "policy") != (self.policy_kind is not None):
            raise ValueError("policy kind is required only for policy records")
        return self

    @property
    def branch(self) -> GovernanceBranch:
        if self.record_kind == "policy":
            return "ai_policy" if self.policy_kind == "ai" else "core_policy"
        return self.record_kind


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("non-JSON number")


def select_governance(raw: bytes) -> GovernanceSelection:
    """Inspect only the closed envelope; do not forward the decoded dictionary."""
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_invalid_constant)
        if not isinstance(value, dict):
            raise ValueError("object required")
        keys = {"contract_version", "record_kind", "policy_kind", "action", "client_request_id"}
        return GovernanceSelection.model_validate({k: v for k, v in value.items() if k in keys})
    except (ValueError, UnicodeError, ValidationError, RecursionError):
        raise ValueError("INVALID_GOVERNANCE_COMMAND") from None


class DelegateRecord(StrictContentModel):
    record_kind: Literal["preset", "policy"]
    policy_kind: Literal["ai", "core"] | None = None
    record_id: OpaqueId
    organization_id: OpaqueId
    version: int = Field(ge=1)
    revision: int = Field(ge=1)
    hash: Sha256Hex
    state: ContentStatus
    authored_by: OpaqueId
    created_at: AwareDatetime
    publication_review_ref: PublicationReviewSet | None
    recalled_at: AwareDatetime | None
    recall_reason: ShortText | None

    @model_validator(mode="after")
    def policy_scope(self) -> DelegateRecord:
        if (self.record_kind == "policy") != (self.policy_kind is not None):
            raise ValueError("invalid policy scope")
        return self


class DelegateTarget(StrictContentModel):
    record_id: OpaqueId
    target_version: int = Field(ge=1)
    target_hash: Sha256Hex


class DelegateResult(StrictContentModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    record: DelegateRecord
    replayed: bool = False
    current_revision: int = Field(ge=1)
    current_state: ContentStatus
