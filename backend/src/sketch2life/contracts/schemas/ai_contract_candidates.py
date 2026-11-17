"""BE2 candidate contract pack published from the BE2-01 foundation (fixture scope).

* DATA-24 ExactContentReview: shared exact-review candidate; primary schema owner BE2-05.
* ProviderCopyLifecycle report: contract owner BE2-14; BE2-01 supplies fake support only.
* DATA-21..29/33 shape specs: lightweight required-field/enum checks so consumer fixtures can be
  exercised before the owning cards implement full schemas. These are not business logic.

All versions are ``0.1-candidate``; registry adoption is a separate cross-review decision.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

OpaqueId = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
ShortText = Annotated[str, Field(min_length=1, max_length=200)]


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


# ------------------------------------------------------------------ DATA-24 (BE2-05)
class ConsentRevisionRefV1(_Strict):
    subject_ref: OpaqueId
    revision: int = Field(ge=0)


class SessionContentContextV1(_Strict):
    kind: Literal["session_content"]
    session_id: OpaqueId
    audience_context_revision: int = Field(ge=0)
    consent_revision_refs: tuple[ConsentRevisionRefV1, ...] = Field(max_length=64)
    review_purpose: Literal["teaching_delivery"]


class GenericLibraryContextV1(_Strict):
    kind: Literal["generic_library"]
    content_kind: OpaqueId
    age_policy_ref: OpaqueId
    content_policy_ref: OpaqueId
    publication_scope: Literal["school_library"]
    review_purpose: Literal["library_publication"]


class SessionAudienceV1(_Strict):
    session_id: OpaqueId
    group_ids: tuple[OpaqueId, ...] = Field(max_length=64)
    participant_ids: tuple[OpaqueId, ...] = Field(max_length=64)


class LibraryAudienceV1(_Strict):
    publication_scope: Literal["school_library"]
    age_policy_ref: OpaqueId
    purpose_codes: tuple[OpaqueId, ...] = Field(min_length=1, max_length=16)


class ExactContentReviewCommandV1(_Strict):
    """DATA-24 command candidate. Owner BE2-05; consumed by BE2-09/BE2-12 without Sketch live."""

    contract_name: Literal["ExactContentReview"] = "ExactContentReview"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    target_kind: Literal["sketch_proposal", "knowledge_video", "learning_content"]
    target_id: OpaqueId
    target_version: int = Field(ge=1)
    target_hash: Sha256Hex
    source_context_revision: int = Field(ge=0)
    decision: Literal["approve", "reject", "request_changes"]
    reason: ShortText | None = None
    review_context: Annotated[
        SessionContentContextV1 | GenericLibraryContextV1, Field(discriminator="kind")
    ]
    audience_scope: SessionAudienceV1 | LibraryAudienceV1
    review_dimension: Literal["safety", "pedagogical"] | None = None
    expected_review_revision: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _consistent(self) -> ExactContentReviewCommandV1:
        if self.decision in {"reject", "request_changes"} and self.reason is None:
            raise ValueError("reason is required for reject/request_changes")
        session = isinstance(self.review_context, SessionContentContextV1)
        if session != isinstance(self.audience_scope, SessionAudienceV1):
            raise ValueError("audience_scope must match review_context.kind")
        if session:
            assert isinstance(self.audience_scope, SessionAudienceV1)
            assert isinstance(self.review_context, SessionContentContextV1)
            if self.audience_scope.session_id != self.review_context.session_id:
                raise ValueError("audience session must equal review_context session")
        else:
            if self.target_kind == "sketch_proposal":
                raise ValueError("sketch proposals are reviewed only in session_content")
            if self.review_dimension is None or self.expected_review_revision is None:
                raise ValueError("generic_library needs review_dimension and expected revision")
        return self


class ExactContentReviewRecordV1(_Strict):
    contract_name: Literal["ExactContentReviewRecord"] = "ExactContentReviewRecord"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    review_id: OpaqueId
    review_revision: int = Field(ge=1)
    reviewer_principal_id: OpaqueId
    reviewed_at: AwareDatetime
    policy_version: OpaqueId
    state: Literal["effective", "revoked", "stale"]


# ------------------------------------------------------- ProviderCopyLifecycle (BE2-14)
class ProviderCopyStatusV1(_Strict):
    copy_id: OpaqueId
    kind: Literal["input", "output", "job", "cache"]
    status: Literal[
        "discovered",
        "cancel_requested",
        "purge_requested",
        "deleted",
        "pending",
        "unsupported",
        "exception",
    ]
    report_label: str = Field(min_length=1, max_length=40)
    receipt_id: OpaqueId | None
    evidence_kind: Literal["fixture", "provider"] | None
    reason_code: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{1,79}$")] | None
    actual_deletion_proven: bool

    @model_validator(mode="after")
    def _truthful(self) -> ProviderCopyStatusV1:
        proven = self.status == "deleted" and self.evidence_kind == "provider"
        if self.actual_deletion_proven != proven:
            raise ValueError("actual_deletion_proven needs a deleted status with provider evidence")
        if self.status == "deleted" and self.receipt_id is None:
            raise ValueError("deleted needs a receipt")
        if self.status != "deleted" and self.report_label == "deleted":
            raise ValueError("non-deleted copy cannot be labelled deleted")
        if self.evidence_kind == "fixture" and self.report_label == "deleted":
            raise ValueError("fixture receipt cannot be reported as actual deletion")
        return self


class ProviderCopyLifecycleReportV1(_Strict):
    contract_name: Literal["ProviderCopyLifecycleReport"] = "ProviderCopyLifecycleReport"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    contract_owner: Literal["BE2-14"] = "BE2-14"
    fake_support_owner: Literal["BE2-01"] = "BE2-01"
    fixture_marker: bool
    organization_id: OpaqueId
    scope_ref: OpaqueId
    copies: tuple[ProviderCopyStatusV1, ...] = Field(max_length=256)

    @model_validator(mode="after")
    def _fixture_marked(self) -> ProviderCopyLifecycleReportV1:
        if any(c.evidence_kind == "fixture" for c in self.copies) and not self.fixture_marker:
            raise ValueError("fixture receipts require fixture_marker=true")
        return self


# ------------------------------------------------------------- shape specs DATA-21..33
Rule = Callable[[Mapping[str, object]], str | None]


@dataclass(frozen=True, slots=True)
class ShapeSpec:
    data_id: str
    name: str
    owner_card: str
    variant: str
    required: tuple[str, ...]
    enums: Mapping[str, frozenset[str]] = field(default_factory=dict)
    rules: tuple[Rule, ...] = ()
    contract_version: str = "0.1-candidate"


def _confidence_rule(payload: Mapping[str, object]) -> str | None:
    candidates = payload.get("object_candidates")
    if not isinstance(candidates, list):
        return "object_candidates must be a list"
    for item in candidates:
        if not isinstance(item, dict) or "label" not in item or "confidence" not in item:
            return "object_candidates items need label and confidence"
        value = item["confidence"]
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int | float) or not 0 <= value <= 1
        ):
            return "confidence must be null or a number in [0,1]"
    return None


def _data28_rule(payload: Mapping[str, object]) -> str | None:
    reason = payload.get("reason")
    return None if isinstance(reason, str) and reason.strip() else "reason is required"


def _data33_rule(payload: Mapping[str, object]) -> str | None:
    action = payload.get("action")
    if action != "create" and not payload.get("record_id"):
        return "record_id is required except for create"
    if action in {"request_changes", "recall", "archive"} and not payload.get("reason"):
        return "reason is required for request_changes/recall/archive"
    if action == "publish" and not payload.get("review_ref"):
        return "review_ref is required for publish"
    return None


SHAPE_SPECS: Mapping[str, ShapeSpec] = {
    "DATA-21": ShapeSpec(
        "DATA-21", "AssistanceRequest", "BE2-03", "command",
        ("canvas_id", "checkpoint_ref", "target_scope", "requested_level", "request_reason",
         "context_revision", "client_request_id"),
        {"request_reason": frozenset({"child_request", "teacher_request",
                                      "explicit_help_signal"})},
    ),
    "DATA-22": ShapeSpec(
        "DATA-22", "AnalysisResultAndCorrection", "BE2-02", "worker_candidate",
        ("assistance_id", "expected_request_revision", "input_snapshot_ref", "context_revision",
         "job_id", "job_attempt_id", "contract_version", "object_candidates", "uncertainty",
         "evidence_refs", "provenance", "moderation_outcome"),
        rules=(_confidence_rule,),
    ),
    "DATA-23": ShapeSpec(
        "DATA-23", "SketchProposal", "BE2-04", "response",
        ("proposal_id", "proposal_version", "review_revision", "assistance_id",
         "request_revision", "source_snapshot_ref", "context_revision", "assistance_level",
         "display_mode", "moderation_state", "pipeline_state", "created_at"),
        {
            "display_mode": frozenset({"side_reference", "overlay"}),
            "pipeline_state": frozenset({
                "requested", "analyzing", "pending_teacher_review", "approved", "rejected",
                "blocked_unsafe", "cancelled", "stale", "failed",
            }),
        },
    ),
    "DATA-26": ShapeSpec(
        "DATA-26", "KnowledgeBundle", "BE2-07", "response",
        ("bundle_id", "bundle_version", "organization_id", "session_id", "audience_context_ref",
         "source_snapshot_refs", "confirmed_topic", "knowledge_claims", "source_records",
         "script_sections", "editorial_revision", "editorial_state", "created_by", "created_at",
         "child_imagined_elements", "teacher_corrections"),
    ),
    "DATA-27": ShapeSpec(
        "DATA-27", "KnowledgeVideoRun", "BE2-08", "create_command",
        ("bundle_id", "bundle_version", "bundle_hash", "audience_context_revision", "strategy"),
        {"strategy": frozenset({"reviewed_library", "generate", "compose_library"})},
    ),
    "DATA-28": ShapeSpec(
        "DATA-28", "FailedVideoDisposition", "BE2-10", "command",
        ("action", "reason", "expected_video_version", "expected_job_revision",
         "expected_session_revision"),
        {"action": frozenset({"retry", "skip", "end_session"})},
        (_data28_rule,),
    ),
    "DATA-29": ShapeSpec(
        "DATA-29", "ActivityAssignment", "BE2-11", "command",
        ("activity_ref", "audience_scope"),
    ),
    "DATA-33": ShapeSpec(
        "DATA-33", "VersionedPresetAndContentRecord", "BE2-12", "action_envelope",
        ("action", "record_kind"),
        {
            "action": frozenset({"create", "edit", "submit_review", "record_review",
                                 "request_changes", "publish", "recall", "archive"}),
            "record_kind": frozenset({"preset", "learning_content", "policy"}),
        },
        (_data33_rule,),
    ),
}
FULL_SCHEMA_IDS = {"DATA-24": "ExactContentReviewCommandV1", "DATA-25": "AsyncJobViewV1"}


def check_shape(data_id: str, payload: object) -> list[str]:
    spec = SHAPE_SPECS[data_id]
    if not isinstance(payload, Mapping):
        return ["payload must be an object"]
    errors = [f"missing required field {name}" for name in spec.required if name not in payload]
    errors += [
        f"{name} must be one of {sorted(allowed)}"
        for name, allowed in spec.enums.items()
        if name in payload
        and not (isinstance(payload[name], str) and payload[name] in allowed)
    ]
    if not errors:
        errors += [message for rule in spec.rules if (message := rule(payload)) is not None]
    return errors


__all__ = [
    "FULL_SCHEMA_IDS",
    "SHAPE_SPECS",
    "ExactContentReviewCommandV1",
    "ExactContentReviewRecordV1",
    "GenericLibraryContextV1",
    "LibraryAudienceV1",
    "ProviderCopyLifecycleReportV1",
    "ProviderCopyStatusV1",
    "SessionAudienceV1",
    "SessionContentContextV1",
    "ShapeSpec",
    "check_shape",
]
