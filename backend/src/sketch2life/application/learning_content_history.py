"""Authorized, read-only review history; derived status never rewrites originals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sketch2life.application.learning_content_eligibility import audience_hash, stored_body
from sketch2life.application.ports.learning_content import (
    ContentAccess,
    ContentBoundary,
    ContentStore,
)
from sketch2life.domain.learning_content.model import (
    Capability,
    ContentError,
    ContentState,
    ContentVersion,
    ReviewProof,
    authorize,
    check_revision,
)

HistoryReason = Literal[
    "content_recalled", "content_archived", "context_changed", "dimension_replaced",
    "superseded_unpublished_version", "policy_changed", "recorded_ineffective",
    "audience_changed", "owner_ineffective"]


@dataclass(frozen=True, slots=True)
class ReviewHistoryEntry:
    original_proof: ReviewProof
    state: Literal["effective", "stale", "revoked"]
    stale_reason: HistoryReason | None


@dataclass(frozen=True, slots=True)
class ReviewHistoryPage:
    contract_version: Literal["0.1-candidate"]
    organization_id: str
    record_id: str
    version: int
    hash: str
    record_revision: int
    entries: tuple[ReviewHistoryEntry, ...]
    next_after_revision: int | None


def _entry(proof: ReviewProof, target: ContentVersion, head: ContentVersion,
           access: ContentAccess) -> ReviewHistoryEntry:
    if ((proof.target_id, proof.target_version, proof.target_hash) != (
            target.record_id, target.version, target.hash)
            or proof.review_revision < 1 or proof.review_revision > target.review_revision
            or not 0 <= proof.context_revision <= target.context_revision
            or proof.dimension not in {"safety", "pedagogical"}):
        raise ContentError("CONTENT_REVIEW_MISMATCH")
    reason: HistoryReason | None = None
    state: Literal["effective", "stale", "revoked"] = "stale"
    if target.state == ContentState.RECALLED:
        reason = "content_recalled"
    elif target.state == ContentState.ARCHIVED:
        reason = "content_archived"
    elif proof.context_revision != target.context_revision:
        reason = "context_changed"
    elif not any(p.review_id == proof.review_id for p in target.reviews):
        reason = "dimension_replaced"
    elif target.version != head.version and target.state != ContentState.PUBLISHED:
        reason = "superseded_unpublished_version"
    elif proof.policy_version != access.policy.version:
        reason = "policy_changed"
    elif proof.audience_hash != audience_hash(stored_body(target)):
        reason = "audience_changed"
    elif proof.state != "effective":
        if proof.state not in {"stale", "revoked"}:
            raise ContentError("CONTENT_INVALID_REVIEW")
        state = "revoked" if proof.state == "revoked" else "stale"
        reason = "recorded_ineffective"
    elif access.review_effective(target, proof) is not True:
        # Boolean owner port cannot tell revoked vs stale or provide a reason.
        # Do not fabricate a revocation cause or mutate the original record.
        reason = "owner_ineffective"
    else:
        state = "effective"
    return ReviewHistoryEntry(proof, state, reason)


class ContentReviewHistory:
    def __init__(self, store: ContentStore, boundary: ContentBoundary) -> None:
        self.store, self.boundary = store, boundary

    def read(self, principal_id: str, organization_id: str, record_id: str, *,
             version: int, page_size: int, after_revision: int = 0,
             snapshot_revision: int | None = None) -> ReviewHistoryPage:
        # 100 is a technical page admission bound, not a business policy/TTL.
        if (type(version) is not int or version < 1 or type(page_size) is not int
                or not 1 <= page_size <= 100 or type(after_revision) is not int
                or after_revision < 0 or (after_revision and snapshot_revision is None)
                or (snapshot_revision is not None and (
                    type(snapshot_revision) is not int or snapshot_revision < 1))):
            raise ContentError("CONTENT_INVALID_QUERY")
        with self.boundary.guard(principal_id, organization_id) as access:
            if (access.authority.principal_id, access.authority.organization_id) != (
                principal_id, organization_id
            ):
                raise ContentError("CONTENT_INVALID_AUTHORITY")
            authorize(access.authority, organization_id, Capability.READ)
            with self.store.transaction() as tx:
                head = tx.load(organization_id, record_id)
                target = tx.load(organization_id, record_id, version=version)
                if head is None or target is None:
                    raise ContentError("CONTENT_NOT_FOUND")
                for item in (head, target):
                    if (item.organization_id != organization_id or item.record_id != record_id
                            or item.revision != head.revision):
                        raise ContentError("CONTENT_STORAGE_SCOPE_MISMATCH")
                if target.version != version:
                    raise ContentError("CONTENT_STORAGE_SCOPE_MISMATCH")
                if snapshot_revision is not None:
                    check_revision(head, snapshot_revision)
                rows = tx.review_history(organization_id, record_id, version=version,
                                         after_revision=after_revision, limit=page_size + 1)
                revisions = [p.review_revision for p in rows]
                if (len(rows) > page_size + 1 or revisions != sorted(set(revisions))
                        or any(r <= after_revision for r in revisions)):
                    raise ContentError("CONTENT_INVALID_HISTORY")
                entries = tuple(_entry(p, target, head, access) for p in rows[:page_size])
                return ReviewHistoryPage(
                    "0.1-candidate", organization_id, record_id, version, target.hash,
                    head.revision, entries,
                    entries[-1].original_proof.review_revision if len(rows) > page_size else None)
