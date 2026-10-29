"""BE2-05 Sketch review contracts (0.1-candidate, FEAT-052).

DATA-24 V1 (``ExactContentReviewCommandV1``/``ExactContentReviewRecordV1``) is reused byte-for-byte
from the shared candidate pack; this module only adds the Sketch binder (OD-02 refinement), the
CMD-35 result wrapper and the Teacher/Child read views. It is not a parallel DATA-24 schema.
"""

from __future__ import annotations

import contextlib
import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewCommandV1,
    ExactContentReviewRecordV1,
    SessionAudienceV1,
    SessionContentContextV1,
)

CONTRACT_VERSION = "0.1-candidate"
OpaqueId = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
REASON_MAX = 128  # SRS LIMIT_TEXT_SHORT (PROPOSED); V1 allows 200

# Every code exists in SRS B22.1 (lines 1718-1731).
ERROR_STATUS: Mapping[str, int] = {
    "MALFORMED_REQUEST": 400,
    "FORBIDDEN_SCOPE": 403,
    "CONSENT_REQUIRED": 403,
    "GRANT_REVOKED": 403,
    "RESOURCE_NOT_FOUND": 404,
    "INVALID_STATE": 409,
    "STALE_CONTEXT": 409,
    "POLICY_UNRESOLVED": 409,
    "IDEMPOTENCY_PAYLOAD_MISMATCH": 409,
    "IDEMPOTENCY_CONFLICT": 409,
    "STALE_AGGREGATE": 412,
    "PRECONDITION_REQUIRED": 428,
    "FIELD_VALIDATION_FAILED": 422,
    "FIELD_NOT_ALLOWED": 422,
    "DEPENDENCY_UNAVAILABLE": 503,
}


class SketchReviewBindError(Exception):
    def __init__(self, code: str, field_name: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.field_name = field_name


@dataclass(frozen=True, slots=True)
class BindTarget:
    """What the binder compares a DATA-24 command against (resolved by the service)."""

    proposal_id: str
    proposal_version: int
    content_sha256: str
    context_revision: int
    session_id: str
    group_ids: frozenset[str]
    audience: frozenset[str]


@dataclass(frozen=True, slots=True)
class BoundSketchReview:
    decision: str
    reason: str | None
    session_id: str
    group_ids: tuple[str, ...]
    participant_ids: tuple[str, ...]
    audience_context_revision: int
    consent_refs: tuple[tuple[str, int], ...]


def _reason(value: str | None) -> str | None:
    if value is None:
        return None
    text = unicodedata.normalize("NFC", value).strip()
    if not text or len(text) > REASON_MAX or _CONTROL.search(text):
        raise SketchReviewBindError("FIELD_VALIDATION_FAILED", "reason")
    return text


def canonical_review_command(command: ExactContentReviewCommandV1) -> dict[str, object]:
    """Pure semantic form used for the receipt fingerprint (RV-CR05).

    Reason is NFC + trimmed (an invalid reason keeps its raw form, the binder rejects it later);
    set-valued fields (participants, groups, consent refs) are sorted. Duplicates are kept so the
    binder still refuses them."""

    data: dict[str, Any] = json.loads(command.model_dump_json())
    reason = data.get("reason")
    if isinstance(reason, str):
        with contextlib.suppress(SketchReviewBindError):
            data["reason"] = _reason(reason)
    audience = data["audience_scope"]
    for name in ("participant_ids", "group_ids"):
        if isinstance(audience.get(name), list):
            audience[name] = sorted(audience[name])
    context = data["review_context"]
    if isinstance(context.get("consent_revision_refs"), list):
        context["consent_revision_refs"] = sorted(
            context["consent_revision_refs"], key=lambda r: (r["subject_ref"], r["revision"]))
    return data


def bind_sketch_review(command: ExactContentReviewCommandV1, target: BindTarget,
                       path_proposal_id: str) -> BoundSketchReview:
    """Bind a validated DATA-24 V1 command to one resolved Sketch target (mirrors 09's binder).

    Client audience is matched against the producer binding, never accepted as a grant."""

    context, audience = command.review_context, command.audience_scope
    if (command.target_kind != "sketch_proposal"
            or not isinstance(context, SessionContentContextV1)
            or not isinstance(audience, SessionAudienceV1)
            or command.review_dimension is not None
            or command.expected_review_revision is not None):
        raise SketchReviewBindError("FIELD_VALIDATION_FAILED", "review_context")
    if command.target_id != path_proposal_id:
        raise SketchReviewBindError("FIELD_VALIDATION_FAILED", "target_id")
    reason = _reason(command.reason)
    if command.decision != "approve" and reason is None:
        raise SketchReviewBindError("FIELD_VALIDATION_FAILED", "reason")
    if (command.target_id != target.proposal_id
            or command.target_version != target.proposal_version
            or command.target_hash != target.content_sha256
            or command.source_context_revision != target.context_revision):
        raise SketchReviewBindError("STALE_CONTEXT", "target")
    if (audience.session_id != target.session_id
            or len(set(audience.participant_ids)) != len(audience.participant_ids)
            or len(set(audience.group_ids)) != len(audience.group_ids)
            or not audience.participant_ids
            or not set(audience.participant_ids) <= target.audience
            or not set(audience.group_ids) <= target.group_ids):
        raise SketchReviewBindError("FIELD_VALIDATION_FAILED", "audience_scope")
    refs = tuple(sorted((r.subject_ref, r.revision) for r in context.consent_revision_refs))
    if len({s for s, _ in refs}) != len(refs):
        raise SketchReviewBindError("FIELD_VALIDATION_FAILED", "consent_revision_refs")
    return BoundSketchReview(command.decision, reason, audience.session_id,
                             tuple(sorted(audience.group_ids)),
                             tuple(sorted(audience.participant_ids)),
                             context.audience_context_revision, refs)


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class ReviewTargetRefV0(_Strict):
    kind: Literal["sketch_proposal"] = "sketch_proposal"
    id: OpaqueId
    version: int = Field(ge=1)
    hash: Sha256Hex


class SketchReviewResultV0(_Strict):
    """CMD-35 response ``data``: the DATA-24 record plus what V1 does not carry (M-02)."""

    contract_name: Literal["SketchReviewResult"] = "SketchReviewResult"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    record: ExactContentReviewRecordV1
    decision: Literal["approve", "reject", "request_changes"]
    target: ReviewTargetRefV0
    review_etag: str = Field(min_length=1, max_length=300)
    semantic_duplicate: bool
    replayed: bool


class SketchReviewQueueItemV0(_Strict):
    contract_name: Literal["SketchReviewQueueItem"] = "SketchReviewQueueItem"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    proposal_id: OpaqueId
    proposal_version: int = Field(ge=1)
    content_sha256: Sha256Hex | None
    source_snapshot_ref: OpaqueId
    session_id: OpaqueId
    group_id: OpaqueId | None
    audience_participant_ids: tuple[OpaqueId, ...]
    context_revision: int = Field(ge=0)
    assistance_level: OpaqueId
    display_mode: Literal["side_reference", "overlay"]
    text_or_question: str | None
    overlay_asset_ref: OpaqueId | None
    pipeline_state: str
    moderation_state: Literal["not_applicable", "pending", "passed", "blocked"]
    moderation_reason: OpaqueId | None
    current_decision: Literal["approve", "reject", "request_changes"] | None
    decision_applicable: bool
    version_terminal: bool
    approve_allowed: bool
    terminal_first_decision: Literal["reject", "request_changes"] | None
    approval_ref: OpaqueId | None
    review_etag: str = Field(min_length=1, max_length=300)


class SketchChildPayloadV0(_Strict):
    contract_name: Literal["SketchChildPayload"] = "SketchChildPayload"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    proposal_id: OpaqueId
    status: Literal["available", "pending", "unavailable"]
    display_mode: Literal["side_reference", "overlay"] | None = None
    text_or_question: str | None = None
    overlay_asset_ref: OpaqueId | None = None
    review_ref: OpaqueId | None = None


__all__ = [
    "CONTRACT_VERSION",
    "ERROR_STATUS",
    "BindTarget",
    "BoundSketchReview",
    "ReviewTargetRefV0",
    "SketchChildPayloadV0",
    "SketchReviewBindError",
    "SketchReviewQueueItemV0",
    "SketchReviewResultV0",
    "bind_sketch_review",
    "canonical_review_command",
]
