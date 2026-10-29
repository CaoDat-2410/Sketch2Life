"""BE2-12 H-CONTENT-PRESET candidate; references/notices are metadata, NOT grants."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.learning_content import (
    ContentStatus,
    PublicationReviewSet,
    StrictContentModel,
)


class ContentReferenceQueryV1(StrictContentModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    record_id: OpaqueId
    age_months: int = Field(ge=0)
    purpose_code: OpaqueId
    version: int | None = Field(default=None, ge=1)
    expected_hash: Sha256Hex | None = None

    @model_validator(mode="after")
    def exact_hash(self) -> ContentReferenceQueryV1:
        if self.expected_hash is not None and self.version is None:
            raise ValueError("hash requires explicit version")
        return self


class PublishedContentReferenceV1(StrictContentModel):
    contract_name: Literal["PublishedContentReference"] = "PublishedContentReference"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    record_id: OpaqueId
    organization_id: OpaqueId
    version: int = Field(ge=1)
    revision: int = Field(ge=1)
    hash: Sha256Hex
    publication_review_ref: PublicationReviewSet

    @model_validator(mode="after")
    def distinct_reviews(self) -> PublishedContentReferenceV1:
        ref = self.publication_review_ref
        if ref.safety_review_id == ref.pedagogical_review_id:
            raise ValueError("two distinct review proofs required")
        return self


class ContentLifecyclePayloadV1(StrictContentModel):
    """Exact existing learning_content event/outbox payload, without raw content."""

    record_id: OpaqueId
    organization_id: OpaqueId
    version: int = Field(ge=1)
    revision: int = Field(ge=1)
    hash: Sha256Hex
    state: ContentStatus
    kind: Literal[
        "content.create", "content.edit", "content.submit_review", "content.record_review",
        "content.request_changes", "content.publish", "content.recall", "content.archive"]

    @model_validator(mode="after")
    def action_state(self) -> ContentLifecyclePayloadV1:
        allowed = {
            "content.create": {"draft"}, "content.edit": {"draft"},
            "content.submit_review": {"submitted"},
            "content.record_review": {"submitted", "changes_requested"},
            "content.request_changes": {"changes_requested"}, "content.publish": {"published"},
            "content.recall": {"recalled"}, "content.archive": {"archived"},
        }
        if self.state not in allowed[self.kind]:
            raise ValueError("lifecycle action/state mismatch")
        return self


class ContentLifecycleNoticeV1(StrictContentModel):
    contract_name: Literal["ContentLifecycleNotice"] = "ContentLifecycleNotice"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    event_id: OpaqueId
    payload: ContentLifecyclePayloadV1


class ContentNoticeAckV1(StrictContentModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    event_id: OpaqueId
    organization_id: OpaqueId
    consumer_id: OpaqueId
    outcome: Literal["accepted", "duplicate"]
