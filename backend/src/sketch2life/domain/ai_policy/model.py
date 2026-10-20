"""Approved BE2-14 P1 lifecycle. No storage, provider, identity or registry claims."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class PolicyError(ValueError):
    """Safe error codes only."""


class Capability(StrEnum):
    AUTHOR = "ai_policy.author"
    REVIEW_SAFETY = "ai_policy.review.safety"
    REVIEW_PEDAGOGICAL = "ai_policy.review.pedagogical"
    PUBLISH = "ai_policy.publish"
    DISABLE = "ai_policy.disable"
    OPERATIONS_READ = "ai_policy.operations.read"
    COPY_LIFECYCLE = "ai_policy.copy.lifecycle"


class State(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CHANGES_REQUESTED = "changes_requested"
    PUBLISHED = "published"
    RECALLED = "recalled"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Authority:
    principal_id: str
    organization_id: str
    capabilities: frozenset[Capability]


def authorize(actor: Authority, organization_id: str, capability: Capability,
              authored_by: str | None = None) -> None:
    if (not actor.principal_id.strip() or actor.organization_id != organization_id
            or capability not in actor.capabilities):
        raise PolicyError("AI_POLICY_FORBIDDEN")
    if (capability in {Capability.REVIEW_SAFETY, Capability.REVIEW_PEDAGOGICAL, Capability.PUBLISH}
            and actor.principal_id == authored_by):
        raise PolicyError("AI_POLICY_SEPARATION_REQUIRED")


def canonical_json(body: object) -> str:
    try:
        return json.dumps(body, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError):
        raise PolicyError("AI_POLICY_INVALID_BODY") from None


def _aware(now: datetime) -> None:
    if now.utcoffset() is None:
        raise PolicyError("AI_POLICY_INVALID_TIME")


@dataclass(frozen=True, slots=True)
class Review:
    review_id: str
    target_id: str
    target_version: int
    target_hash: str
    context_revision: int
    review_revision: int
    dimension: str
    decision: str
    reviewer_id: str
    policy_version: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PolicyVersion:
    record_id: str
    organization_id: str
    version: int
    revision: int
    body_json: str
    hash: str
    state: State
    authored_by: str
    created_at: datetime
    context_revision: int = 0
    review_revision: int = 0
    reviews: tuple[Review, ...] = ()
    publication_review_ids: tuple[str, ...] = ()
    publication_policy_version: str | None = None
    recalled_at: datetime | None = None
    recall_reason: str | None = None


def create(record_id: str, actor: Authority, body: object, now: datetime, *,
           version: int = 1, revision: int = 1) -> PolicyVersion:
    authorize(actor, actor.organization_id, Capability.AUTHOR)
    _aware(now)
    if (not record_id or not actor.organization_id or type(version) is not int
            or type(revision) is not int or version < 1 or revision < 1):
        raise PolicyError("AI_POLICY_INVALID_IDENTITY")
    encoded = canonical_json(body)
    return PolicyVersion(record_id, actor.organization_id, version, revision, encoded,
                         hashlib.sha256(encoded.encode("utf-8")).hexdigest(), State.DRAFT,
                         actor.principal_id, now)


def check_revision(policy: PolicyVersion, expected: int) -> None:
    if type(expected) is not int or expected != policy.revision:
        raise PolicyError("AI_POLICY_STALE_REVISION")


def edit(policy: PolicyVersion, actor: Authority, body: object, now: datetime, *,
         expected_revision: int, next_version: int) -> PolicyVersion:
    authorize(actor, policy.organization_id, Capability.AUTHOR)
    check_revision(policy, expected_revision)
    if type(next_version) is not int or next_version != policy.version + 1:
        raise PolicyError("AI_POLICY_INVALID_VERSION")
    return create(policy.record_id, actor, body, now, version=next_version,
                  revision=policy.revision + 1)


def submit(policy: PolicyVersion, actor: Authority, *, expected_revision: int) -> PolicyVersion:
    authorize(actor, policy.organization_id, Capability.AUTHOR)
    check_revision(policy, expected_revision)
    if policy.state not in {State.DRAFT, State.CHANGES_REQUESTED}:
        raise PolicyError("AI_POLICY_TRANSITION_DENIED")
    return replace(policy, state=State.SUBMITTED, revision=policy.revision + 1,
                   context_revision=policy.context_revision + 1,
                   review_revision=policy.review_revision + 1, reviews=())


def record_review(policy: PolicyVersion, actor: Authority, proof: Review, *,
                  expected_revision: int, expected_review_revision: int) -> PolicyVersion:
    capability = {"safety": Capability.REVIEW_SAFETY,
                  "pedagogical": Capability.REVIEW_PEDAGOGICAL}.get(proof.dimension)
    if capability is None or proof.decision not in {"approve", "reject", "request_changes"}:
        raise PolicyError("AI_POLICY_INVALID_REVIEW")
    authorize(actor, policy.organization_id, capability, policy.authored_by)
    check_revision(policy, expected_revision)
    if (type(expected_review_revision) is not int
            or expected_review_revision != policy.review_revision):
        raise PolicyError("AI_POLICY_STALE_REVIEW")
    if policy.state != State.SUBMITTED:
        raise PolicyError("AI_POLICY_TRANSITION_DENIED")
    if (not proof.review_id or not proof.policy_version
            or (proof.target_id, proof.target_version, proof.target_hash,
                proof.context_revision, proof.review_revision, proof.reviewer_id) != (
                    policy.record_id, policy.version, policy.hash, policy.context_revision,
                    policy.review_revision + 1, actor.principal_id)
            or any(item.review_id == proof.review_id for item in policy.reviews)):
        raise PolicyError("AI_POLICY_REVIEW_MISMATCH")
    if proof.decision != "approve" and (proof.reason is None or not proof.reason.strip()):
        raise PolicyError("AI_POLICY_REASON_REQUIRED")
    reviews = tuple(item for item in policy.reviews if item.dimension != proof.dimension) + (proof,)
    return replace(policy, revision=policy.revision + 1, review_revision=proof.review_revision,
                   reviews=reviews, state=(State.SUBMITTED if proof.decision == "approve"
                                           else State.CHANGES_REQUESTED))


def publish(policy: PolicyVersion, actor: Authority, *, expected_revision: int,
            safety_review_id: str, pedagogical_review_id: str,
            current_review_policy: str) -> PolicyVersion:
    authorize(actor, policy.organization_id, Capability.PUBLISH, policy.authored_by)
    check_revision(policy, expected_revision)
    if policy.state != State.SUBMITTED:
        raise PolicyError("AI_POLICY_TRANSITION_DENIED")
    refs = (safety_review_id, pedagogical_review_id)
    if not current_review_policy or not all(refs) or len(set(refs)) != 2:
        raise PolicyError("AI_POLICY_REVIEW_REQUIRED")
    for dimension, expected_id in zip(("safety", "pedagogical"), refs, strict=True):
        proof = next((item for item in policy.reviews if item.dimension == dimension), None)
        if (proof is None or proof.decision != "approve"
                or proof.reviewer_id == policy.authored_by
                or (proof.review_id, proof.target_id, proof.target_version, proof.target_hash,
                    proof.context_revision, proof.policy_version) != (
                        expected_id, policy.record_id, policy.version, policy.hash,
                        policy.context_revision, current_review_policy)):
            raise PolicyError("AI_POLICY_REVIEW_REQUIRED")
    return replace(policy, state=State.PUBLISHED, revision=policy.revision + 1,
                   publication_review_ids=refs, publication_policy_version=current_review_policy)


def retire(policy: PolicyVersion, actor: Authority, now: datetime, *,
           expected_revision: int, archive: bool, reason: str) -> PolicyVersion:
    authorize(actor, policy.organization_id, Capability.DISABLE)
    check_revision(policy, expected_revision)
    _aware(now)
    if not reason.strip():
        raise PolicyError("AI_POLICY_REASON_REQUIRED")
    if policy.state in {State.RECALLED, State.ARCHIVED} or (
            not archive and policy.state != State.PUBLISHED):
        raise PolicyError("AI_POLICY_TRANSITION_DENIED")
    return replace(policy, state=State.ARCHIVED if archive else State.RECALLED,
                   revision=policy.revision + 1, recalled_at=now, recall_reason=reason)
