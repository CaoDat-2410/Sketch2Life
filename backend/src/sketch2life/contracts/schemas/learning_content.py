"""BE2-12 DATA-33 content candidate; shared DATA-24 remains owned by BE2-05."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewCommandV1,
    OpaqueId,
    Sha256Hex,
    ShortText,
)


class StrictContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ArtifactReference(StrictContentModel):
    ref: OpaqueId
    version: int = Field(ge=1)
    hash: Sha256Hex


class AgeEligibility(StrictContentModel):
    age_policy_ref: OpaqueId
    min_months: int = Field(ge=36, le=155)
    max_months: int = Field(ge=36, le=155)

    @model_validator(mode="after")
    def ordered(self) -> AgeEligibility:
        if self.min_months > self.max_months:
            raise ValueError("invalid age interval")
        return self


class ContentWrite(StrictContentModel):
    content_kind: Literal["knowledge", "activity", "video"]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    asset_refs: tuple[ArtifactReference, ...] = Field(max_length=64)
    source_refs: tuple[ArtifactReference, ...] = Field(min_length=1, max_length=64)
    age_eligibility: AgeEligibility
    purpose_codes: tuple[OpaqueId, ...] = Field(min_length=1, max_length=16)
    editorial_note: Annotated[str, Field(max_length=2000)]
    content_policy_ref: OpaqueId

    @model_validator(mode="after")
    def meaningful(self) -> ContentWrite:
        if not self.title.strip() or len(set(self.purpose_codes)) != len(self.purpose_codes):
            raise ValueError("blank title or duplicate purposes")
        for references in (self.asset_refs, self.source_refs):
            if len({(r.ref, r.version) for r in references}) != len(references):
                raise ValueError("duplicate artifact reference")
        return self


class CommandBase(StrictContentModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    record_kind: Literal["learning_content"]
    client_request_id: OpaqueId


class CreateContent(CommandBase):
    action: Literal["create"]
    content: ContentWrite


class TargetCommand(CommandBase):
    record_id: OpaqueId
    target_version: int = Field(ge=1)
    target_hash: Sha256Hex


class EditContent(TargetCommand):
    action: Literal["edit"]
    content: ContentWrite


class SubmitContent(TargetCommand):
    action: Literal["submit_review"]


class RecordContentReview(TargetCommand):
    action: Literal["record_review"]
    review: ExactContentReviewCommandV1

    @model_validator(mode="after")
    def exact_target(self) -> RecordContentReview:
        if (self.review.target_kind != "learning_content"
                or self.review.review_context.kind != "generic_library"
                or (self.record_id, self.target_version, self.target_hash) != (
                    self.review.target_id, self.review.target_version, self.review.target_hash)):
            raise ValueError("review must target exact generic library content")
        return self


class RequestContentChanges(TargetCommand):
    action: Literal["request_changes"]
    review: ExactContentReviewCommandV1
    reason: ShortText

    @model_validator(mode="after")
    def changes_review(self) -> RequestContentChanges:
        RecordContentReview(
            record_kind=self.record_kind, client_request_id=self.client_request_id,
            action="record_review", record_id=self.record_id,
            target_version=self.target_version, target_hash=self.target_hash, review=self.review)
        if self.review.decision != "request_changes" or self.review.reason != self.reason:
            raise ValueError("request_changes needs matching exact review and reason")
        return self


class PublicationReviewSet(StrictContentModel):
    safety_review_id: OpaqueId
    pedagogical_review_id: OpaqueId
    review_policy_version: OpaqueId


class PublishContent(TargetCommand):
    action: Literal["publish"]
    review_ref: PublicationReviewSet


class RetireContent(TargetCommand):
    action: Literal["recall", "archive"]
    reason: ShortText

    @model_validator(mode="after")
    def meaningful_reason(self) -> RetireContent:
        if not self.reason.strip():
            raise ValueError("reason required")
        return self


ContentCommand = Annotated[
    CreateContent | EditContent | SubmitContent | RecordContentReview |
    RequestContentChanges | PublishContent | RetireContent,
    Field(discriminator="action"),
]
CONTENT_COMMAND_ADAPTER: TypeAdapter[ContentCommand] = TypeAdapter(ContentCommand)
