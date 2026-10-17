"""Pure immutable content lifecycle under approved FEAT-048 P1–P3.

Callers supply verified/current authority; this module is not an identity verifier.
Storage CAS, external eligibility and transaction fencing belong to application ports.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class ContentError(ValueError):
    """Safe public code only, never raw content or an exception from an adapter."""


class ContentState(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CHANGES_REQUESTED = "changes_requested"
    PUBLISHED = "published"
    RECALLED = "recalled"
    ARCHIVED = "archived"


class Capability(StrEnum):
    AUTHOR = "content.author"
    REVIEW_SAFETY = "content.review.safety"
    REVIEW_PEDAGOGICAL = "content.review.pedagogical"
    PUBLISH = "content.publish"
    RECALL = "content.recall"
    READ = "content.read"


@dataclass(frozen=True, slots=True)
class Authority:
    principal_id: str
    organization_id: str
    capabilities: frozenset[Capability]

    def __post_init__(self) -> None:
        if not self.principal_id.strip() or not self.organization_id.strip():
            raise ContentError("CONTENT_INVALID_AUTHORITY")


def authorize(actor: Authority, organization_id: str, capability: Capability,
              *, authored_by: str | None = None) -> None:
    if actor.organization_id != organization_id or capability not in actor.capabilities:
        raise ContentError("CONTENT_FORBIDDEN")
    if capability in {Capability.PUBLISH, Capability.REVIEW_SAFETY,
                      Capability.REVIEW_PEDAGOGICAL} and actor.principal_id == authored_by:
        raise ContentError("CONTENT_SEPARATION_REQUIRED")


def canonical_json(value: object) -> str:
    """Version-1 canonical JSON: sorted keys, UTF-8, no Unicode normalization."""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError):
        raise ContentError("CONTENT_INVALID_PAYLOAD") from None


def content_hash(body_json: str) -> str:
    return hashlib.sha256(body_json.encode("utf-8")).hexdigest()


def _aware(now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ContentError("CONTENT_INVALID_TIME")


@dataclass(frozen=True, slots=True)
class ReviewProof:
    review_id: str
    dimension: str
    decision: str
    target_id: str
    target_version: int
    target_hash: str
    context_revision: int
    audience_hash: str
    reviewer_id: str
    policy_version: str
    review_revision: int
    state: str = "effective"
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ContentVersion:
    record_id: str
    organization_id: str
    version: int
    revision: int
    body_json: str
    hash: str
    state: ContentState
    authored_by: str
    created_at: datetime
    context_revision: int = 0
    review_revision: int = 0
    reviews: tuple[ReviewProof, ...] = ()
    publication_review_ids: tuple[str, ...] = ()
    publication_policy_version: str | None = None
    recalled_at: datetime | None = None
    recall_reason: str | None = None


def create(record_id: str, actor: Authority, body: object, now: datetime,
           *, version: int = 1, revision: int = 1) -> ContentVersion:
    authorize(actor, actor.organization_id, Capability.AUTHOR)
    _aware(now)
    if version < 1 or revision < 1 or not record_id:
        raise ContentError("CONTENT_INVALID_IDENTITY")
    serialized = canonical_json(body)
    return ContentVersion(record_id, actor.organization_id, version, revision, serialized,
                          content_hash(serialized), ContentState.DRAFT, actor.principal_id, now)


def check_revision(content: ContentVersion, expected: int) -> None:
    if isinstance(expected, bool) or expected != content.revision:
        raise ContentError("CONTENT_STALE_REVISION")


def edit(content: ContentVersion, actor: Authority, body: object, now: datetime,
         *, expected_revision: int, next_version: int) -> ContentVersion:
    authorize(actor, content.organization_id, Capability.AUTHOR)
    check_revision(content, expected_revision)
    if content.state in {ContentState.RECALLED, ContentState.ARCHIVED}:
        raise ContentError("CONTENT_TRANSITION_DENIED")
    if next_version <= content.version:
        raise ContentError("CONTENT_INVALID_VERSION")
    return create(content.record_id, actor, body, now, version=next_version,
                  revision=content.revision + 1)


def submit(content: ContentVersion, actor: Authority, *, expected_revision: int) -> ContentVersion:
    authorize(actor, content.organization_id, Capability.AUTHOR)
    check_revision(content, expected_revision)
    if content.state not in {ContentState.DRAFT, ContentState.CHANGES_REQUESTED}:
        raise ContentError("CONTENT_TRANSITION_DENIED")
    return replace(content, state=ContentState.SUBMITTED, revision=content.revision + 1,
                   context_revision=content.context_revision + 1, reviews=(),
                   review_revision=content.review_revision + 1)


def record_review(content: ContentVersion, actor: Authority, proof: ReviewProof,
                  *, expected_revision: int, expected_review_revision: int) -> ContentVersion:
    if proof.dimension not in {"safety", "pedagogical"}:
        raise ContentError("CONTENT_INVALID_REVIEW")
    capability = (Capability.REVIEW_SAFETY if proof.dimension == "safety"
                  else Capability.REVIEW_PEDAGOGICAL)
    authorize(actor, content.organization_id, capability, authored_by=content.authored_by)
    check_revision(content, expected_revision)
    if expected_review_revision != content.review_revision:
        raise ContentError("CONTENT_STALE_REVIEW")
    if content.state != ContentState.SUBMITTED:
        raise ContentError("CONTENT_TRANSITION_DENIED")
    if (proof.target_id, proof.target_version, proof.target_hash, proof.context_revision,
        proof.reviewer_id, proof.review_revision) != (
            content.record_id, content.version, content.hash, content.context_revision,
            actor.principal_id, content.review_revision + 1):
        raise ContentError("CONTENT_REVIEW_MISMATCH")
    if (not proof.review_id or not proof.policy_version or not proof.audience_hash
            or proof.state != "effective"
            or proof.decision not in {"approve", "reject", "request_changes"}):
        raise ContentError("CONTENT_INVALID_REVIEW")
    if proof.decision != "approve" and (
        proof.reason is None or not proof.reason.strip() or len(proof.reason) > 200
    ):
        raise ContentError("CONTENT_REASON_REQUIRED")
    if any(item.review_id == proof.review_id for item in content.reviews):
        raise ContentError("CONTENT_REVIEW_ID_CONFLICT")
    reviews = tuple(item for item in content.reviews if item.dimension != proof.dimension)
    state = (ContentState.SUBMITTED if proof.decision == "approve"
             else ContentState.CHANGES_REQUESTED)
    return replace(content, revision=content.revision + 1,
                   review_revision=content.review_revision + 1, reviews=(*reviews, proof),
                   state=state)


def publish(content: ContentVersion, actor: Authority, *, expected_revision: int,
            safety_review_id: str, pedagogical_review_id: str,
            policy_version: str, audience_hash: str) -> ContentVersion:
    authorize(actor, content.organization_id, Capability.PUBLISH, authored_by=content.authored_by)
    check_revision(content, expected_revision)
    if content.state != ContentState.SUBMITTED:
        raise ContentError("CONTENT_TRANSITION_DENIED")
    references = {"safety": safety_review_id, "pedagogical": pedagogical_review_id}
    if safety_review_id == pedagogical_review_id:
        raise ContentError("CONTENT_REVIEW_REQUIRED")
    for dimension, review_id in references.items():
        matches = [proof for proof in content.reviews
                   if proof.dimension == dimension and proof.review_id == review_id]
        if len(matches) != 1:
            raise ContentError("CONTENT_REVIEW_REQUIRED")
        proof = matches[0]
        if (proof.decision != "approve" or proof.state != "effective"
                or proof.reviewer_id == content.authored_by
                or (proof.target_id, proof.target_version, proof.target_hash,
                    proof.context_revision, proof.policy_version, proof.audience_hash) != (
                    content.record_id, content.version, content.hash,
                    content.context_revision, policy_version, audience_hash)):
            raise ContentError("CONTENT_REVIEW_MISMATCH")
    return replace(content, revision=content.revision + 1, state=ContentState.PUBLISHED,
                   publication_review_ids=(safety_review_id, pedagogical_review_id),
                   publication_policy_version=policy_version)


def retire(content: ContentVersion, actor: Authority, now: datetime, *,
           expected_revision: int, reason: str, archive: bool = False) -> ContentVersion:
    authorize(actor, content.organization_id, Capability.RECALL)
    check_revision(content, expected_revision)
    _aware(now)
    if not reason.strip() or len(reason) > 200:
        raise ContentError("CONTENT_REASON_REQUIRED")
    if (content.state in {ContentState.RECALLED, ContentState.ARCHIVED}
            or (not archive and content.state != ContentState.PUBLISHED)):
        raise ContentError("CONTENT_TRANSITION_DENIED")
    return replace(content, revision=content.revision + 1,
                   state=ContentState.ARCHIVED if archive else ContentState.RECALLED,
                   recalled_at=now, recall_reason=reason)
