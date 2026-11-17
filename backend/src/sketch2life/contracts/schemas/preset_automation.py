"""Closed candidate DATA-33 preset branch; no additional CMD-48 route."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex, ShortText
from sketch2life.contracts.schemas.learning_content import PublicationReviewSet, StrictContentModel
from sketch2life.domain.preset_automation.model import Body, Rule


class PresetRule(StrictContentModel):
    rule_id: OpaqueId
    condition: Literal["stage_is", "help_pending"]
    expected: OpaqueId
    action: Literal["notify_teacher", "request_support"]

    @model_validator(mode="after")
    def validate_rule(self) -> PresetRule:
        Rule(self.rule_id, self.condition, self.expected, self.action)
        return self


class PresetBody(StrictContentModel):
    title: ShortText
    effective_age_policy_ref: OpaqueId
    tool_policy_ref: OpaqueId
    canvas_mode: OpaqueId
    assistance_policy_ref: OpaqueId
    stage_rules: tuple[PresetRule, ...] = Field(max_length=32)
    notification_rules: tuple[PresetRule, ...] = Field(max_length=32)
    video_policy_ref: OpaqueId
    activity_policy_ref: OpaqueId
    assessment_policy_ref: OpaqueId

    def domain(self) -> Body:
        data = self.model_dump(exclude={"stage_rules", "notification_rules"})
        return Body(
            **data,
            stage_rules=tuple(Rule(**r.model_dump()) for r in self.stage_rules),
            notification_rules=tuple(Rule(**r.model_dump()) for r in self.notification_rules),
        )

    @model_validator(mode="after")
    def validate_body(self) -> PresetBody:
        self.domain()
        return self


class PresetReview(StrictContentModel):
    review_id: OpaqueId
    dimension: Literal["safety", "pedagogical"]
    policy_ref: OpaqueId
    decision: Literal["approve", "reject", "request_changes"]
    reason: ShortText | None = None


class PresetCommand(StrictContentModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    record_kind: Literal["preset"] = "preset"
    action: Literal[
        "create",
        "edit",
        "submit_review",
        "record_review",
        "request_changes",
        "publish",
        "recall",
        "archive",
    ]
    client_request_id: OpaqueId
    record_id: OpaqueId | None = None
    target_version: int | None = Field(default=None, ge=1)
    target_hash: Sha256Hex | None = None
    body: PresetBody | None = None
    review: PresetReview | None = None
    review_ref: PublicationReviewSet | None = None
    reason: ShortText | None = None

    @model_validator(mode="after")
    def shape(self) -> PresetCommand:
        if self.action == "create":
            if any(v is not None for v in (self.record_id, self.target_version, self.target_hash)):
                raise ValueError("create has no target")
        elif any(v is None for v in (self.record_id, self.target_version, self.target_hash)):
            raise ValueError("exact target required")
        if (self.body is not None) != (self.action in {"create", "edit"}):
            raise ValueError("body action mismatch")
        if (self.review is not None) != (self.action == "record_review"):
            raise ValueError("review action mismatch")
        if (self.review_ref is not None) != (self.action == "publish"):
            raise ValueError("publication action mismatch")
        if self.action in {"request_changes", "recall", "archive"}:
            if not self.reason:
                raise ValueError("reason required")
        elif self.reason is not None:
            raise ValueError("unexpected reason")
        if self.review is not None and self.review.decision != "approve" and not self.review.reason:
            raise ValueError("review reason required")
        return self
