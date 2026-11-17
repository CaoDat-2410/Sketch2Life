"""BE2-14 strict CMD-48 AI-policy candidate; no production values or authority."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex, ShortText
from sketch2life.contracts.schemas.governance import GovernanceAction
from sketch2life.contracts.schemas.learning_content import PublicationReviewSet


class StrictPolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class PolicyDefinitionRef(StrictPolicyModel):
    ref: OpaqueId
    version: int = Field(ge=1)
    hash: Sha256Hex


class RequiredPolicyGates(StrictPolicyModel):
    teacher_review: Literal[True]
    consent: Literal[True]
    current_source: Literal[True]
    safety: Literal[True]

    @model_validator(mode="before")
    @classmethod
    def actual_booleans(cls, value: object) -> object:
        # Literal[True] alone also accepts integer 1; never permit that coercion.
        if isinstance(value, dict) and any(item is not True for item in value.values()):
            raise ValueError("mandatory gates require true booleans")
        return value


class AiPolicyWrite(StrictPolicyModel):
    title: ShortText
    feature_scope: OpaqueId
    model_profile_refs: tuple[PolicyDefinitionRef, ...] = Field(min_length=1, max_length=64)
    moderation_policy_ref: PolicyDefinitionRef
    retry_policy_ref: PolicyDefinitionRef
    budget_policy_ref: PolicyDefinitionRef
    concurrency_policy_ref: PolicyDefinitionRef
    required_gates: RequiredPolicyGates

    @model_validator(mode="after")
    def meaningful(self) -> AiPolicyWrite:
        if not self.title.strip():
            raise ValueError("nonblank title required")
        refs = self.model_profile_refs
        if len({(ref.ref, ref.version) for ref in refs}) != len(refs):
            raise ValueError("duplicate model profile")
        return self


class AiPolicyReview(StrictPolicyModel):
    target_kind: Literal["ai_policy"]
    target_id: OpaqueId
    target_version: int = Field(ge=1)
    target_hash: Sha256Hex
    context_revision: int = Field(ge=1)
    expected_review_revision: int = Field(ge=0)
    dimension: Literal["safety", "pedagogical"]
    decision: Literal["approve", "reject", "request_changes"]
    review_policy_version: OpaqueId
    reason: ShortText | None = None

    @model_validator(mode="after")
    def negative_reason(self) -> AiPolicyReview:
        if self.decision != "approve" and (self.reason is None or not self.reason.strip()):
            raise ValueError("negative review requires reason")
        if self.reason is not None and not self.reason.strip():
            raise ValueError("nonblank reason required")
        return self


class AiPolicyCommand(StrictPolicyModel):
    """Concrete BaseModel compatible with existing strict typed owner binding.

    Presence rules close each action payload; defaults never admit null spare fields.
    """

    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    record_kind: Literal["policy"]
    policy_kind: Literal["ai"]
    action: GovernanceAction
    client_request_id: OpaqueId
    record_id: OpaqueId | None = None
    target_version: int | None = Field(default=None, ge=1)
    target_hash: Sha256Hex | None = None
    policy: AiPolicyWrite | None = None
    review: AiPolicyReview | None = None
    review_ref: PublicationReviewSet | None = None
    reason: ShortText | None = None

    @model_serializer(mode="wrap")
    def action_payload(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        # Omitted action fields must stay omitted on receipt/binding round trips.
        return {key: value for key, value in handler(self).items() if value is not None}

    @model_validator(mode="after")
    def exact_action(self) -> AiPolicyCommand:
        required = {
            "create": {"policy"}, "edit": {"policy"}, "submit_review": set(),
            "record_review": {"review"}, "request_changes": {"review", "reason"},
            "publish": {"review_ref"}, "recall": {"reason"}, "archive": {"reason"},
        }[self.action]
        if self.action != "create":
            required = required | {"record_id", "target_version", "target_hash"}
        payload_fields = {"record_id", "target_version", "target_hash", "policy",
                          "review", "review_ref", "reason"}
        if self.model_fields_set & payload_fields != required:
            raise ValueError("invalid fields for policy action")
        if any(getattr(self, key) is None for key in required):
            raise ValueError("required policy fields cannot be null")
        if self.reason is not None and not self.reason.strip():
            raise ValueError("nonblank reason required")
        if self.review is not None:
            review = self.review
            if (review.target_id, review.target_version, review.target_hash) != (
                    self.record_id, self.target_version, self.target_hash):
                raise ValueError("review must match exact policy target")
            if self.action == "request_changes" and (
                    review.decision != "request_changes" or review.reason != self.reason):
                raise ValueError("changes command must match review decision and reason")
        if self.review_ref is not None and (
                self.review_ref.safety_review_id == self.review_ref.pedagogical_review_id):
            raise ValueError("distinct review IDs required")
        return self
