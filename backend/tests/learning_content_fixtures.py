"""Synthetic BE2-12 component/SQL harness, NOT adopted BE1/BE2-05 adapters.

No fixture here is imported by production. Memory rollback/locks are not SQL or
real owner revocation evidence; SQL tests explicitly inject these assumed ports.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from threading import RLock, local
from typing import cast

from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.application.ports.learning_content import (
    ContentAccess,
    ContentEvent,
    ContentPolicy,
    ContentReceipt,
    ContentTransaction,
    SourceAssessment,
)
from sketch2life.contracts.schemas.learning_content import (
    CONTENT_COMMAND_ADAPTER,
    ContentCommand,
    ContentRecord,
)
from sketch2life.domain.learning_content.model import (
    Authority,
    Capability,
    ContentError,
    ContentState,
    ContentVersion,
    ReviewProof,
)

NOW = datetime(2026, 10, 17, tzinfo=UTC)
BODY = {
    "content_kind": "knowledge", "title": "Butterfly", "asset_refs": [],
    "source_refs": [{"ref": "source", "version": 1, "hash": "a" * 64}],
    "age_eligibility": {"min_months": 36, "max_months": 155, "age_policy_ref": "age-v1"},
    "purpose_codes": ["classroom"], "editorial_note": "", "content_policy_ref": "content-v1"}


class AssumedAccess:
    def __init__(self, boundary: AssumedBoundary, principal_id: str, organization_id: str) -> None:
        self.boundary = boundary
        self.authority = Authority(principal_id, organization_id,
                                   boundary.capabilities.get(principal_id, frozenset()))
        self.policy = boundary.policy

    def assess_sources(self, content: ContentVersion) -> SourceAssessment:
        return SourceAssessment(
            content.organization_id, content.record_id, content.version, content.hash,
            self.policy.version, self.boundary.classification, self.boundary.usage,
            self.boundary.moderation)

    def review_effective(self, content: ContentVersion, proof: ReviewProof) -> bool:
        return (proof.review_id not in self.boundary.revoked_reviews
                and proof.reviewer_id not in self.boundary.revoked_reviewers)


class AssumedBoundary:
    """Thread-local scope spy, NOT a durable consistency/fencing implementation."""

    def __init__(self) -> None:
        self.policy = ContentPolicy("policy-v1", "content-v1", "age-v1",
                                    frozenset({"knowledge", "activity", "video"}),
                                    frozenset({"classroom", "observation"}))
        self.capabilities = {
            "author": frozenset({Capability.AUTHOR}),
            "reviewer": frozenset({Capability.REVIEW_SAFETY, Capability.REVIEW_PEDAGOGICAL}),
            "publisher": frozenset({Capability.PUBLISH}),
            "recaller": frozenset({Capability.RECALL}),
            "consumer": frozenset({Capability.READ}),
            "editor": frozenset(Capability),
        }
        self.classification = "generic_authored"
        self.usage = True
        self.moderation = True
        self.revoked_reviews: set[str] = set()
        self.revoked_reviewers: set[str] = set()
        self.thread = local()

    @property
    def held(self) -> bool:
        return getattr(self.thread, "held", False)

    @contextmanager
    def guard(self, principal_id: str, organization_id: str) -> Iterator[ContentAccess]:
        # Test fixture supports only this synthetic organization; not client auth.
        if organization_id != "school":
            raise ContentError("CONTENT_FORBIDDEN")
        self.thread.held = True
        try:
            yield AssumedAccess(self, principal_id, organization_id)
        finally:
            self.thread.held = False


class ComponentStore:
    def __init__(self, boundary: AssumedBoundary) -> None:
        self.boundary = boundary
        self.lock = RLock()
        self.versions: dict[tuple[str, str, int], ContentVersion] = {}
        self.heads: dict[tuple[str, str], tuple[int, int]] = {}
        self.receipts: dict[tuple[str, str, str], ContentReceipt] = {}
        self.events: list[ContentEvent] = []
        self.proofs: dict[tuple[str, str], ReviewProof] = {}
        self.fail_receipt = False
        self.commits = 0

    @contextmanager
    def transaction(self) -> Iterator[ContentTransaction]:
        assert self.boundary.held
        with self.lock:
            before = deepcopy((self.versions, self.heads, self.receipts, self.events, self.proofs))
            try:
                yield cast(ContentTransaction, self)
                assert self.boundary.held
                self.commits += 1
            except Exception:
                self.versions, self.heads, self.receipts, self.events, self.proofs = before
                assert self.boundary.held
                raise

    def load(self, organization_id: str, record_id: str, *, version: int | None = None,
             for_update: bool = False) -> ContentVersion | None:
        head = self.heads.get((organization_id, record_id))
        if head is None:
            return None
        item = self.versions.get((organization_id, record_id, version or head[0]))
        return replace(item, revision=head[1]) if item else None

    def published_versions(self, organization_id: str,
                           record_id: str) -> tuple[ContentVersion, ...]:
        return tuple(self.load(organization_id, record_id, version=version)
                     for (org, ref, version), item in self.versions.items()
                     if org == organization_id and ref == record_id
                     and item.state == ContentState.PUBLISHED)

    def save(self, content: ContentVersion, *, expected_revision: int | None,
             event: ContentEvent) -> None:
        key = (content.organization_id, content.record_id)
        head = self.heads.get(key)
        if expected_revision is None:
            if head:
                raise ContentError("CONTENT_WRITE_CONFLICT")
        elif not head or head[1] != expected_revision:
            raise ContentError("CONTENT_STALE_REVISION")
        self.heads[key] = (max(head[0] if head else 0, content.version), content.revision)
        self.versions[(*key, content.version)] = content
        for proof in content.reviews:
            self.proofs.setdefault((content.organization_id, proof.review_id), proof)
        self.events.append(event)

    def review_history(self, organization_id: str, record_id: str, *, version: int,
                       after_revision: int, limit: int) -> tuple[ReviewProof, ...]:
        return tuple(sorted((p for (org, _), p in self.proofs.items()
                             if org == organization_id and p.target_id == record_id
                             and p.target_version == version
                             and p.review_revision > after_revision),
                            key=lambda p: p.review_revision))[:limit]

    def receipt(self, organization_id: str, principal_id: str,
                request_id: str) -> ContentReceipt | None:
        return self.receipts.get((organization_id, principal_id, request_id))

    def add_receipt(self, receipt: ContentReceipt) -> None:
        if self.fail_receipt:
            raise ContentError("SYNTHETIC_RECEIPT_FAILURE")
        key = (receipt.organization_id, receipt.principal_id, receipt.request_id)
        if key in self.receipts:
            raise ContentError("CONTENT_WRITE_CONFLICT")
        self.receipts[key] = receipt


def command(action: str, request: str, record: ContentRecord | None = None,
            **fields: object) -> ContentCommand:
    value: dict[str, object] = {
        "action": action, "record_kind": "learning_content", "client_request_id": request}
    if record is not None:
        value.update(record_id=record.record_id, target_version=record.version,
                     target_hash=record.hash)
    value.update(fields)
    return CONTENT_COMMAND_ADAPTER.validate_json(json.dumps(value))


def review_command(record: ContentRecord, dimension: str, request: str, *,
                   decision: str = "approve", action: str = "record_review",
                   **overrides: object) -> ContentCommand:
    review: dict[str, object] = {
        "target_kind": "learning_content", "target_id": record.record_id,
        "target_version": record.version, "target_hash": record.hash,
        "source_context_revision": record.context_revision, "decision": decision,
        "review_context": {"kind": "generic_library", "content_kind": "knowledge",
                           "age_policy_ref": "age-v1", "content_policy_ref": "content-v1",
                           "publication_scope": "school_library",
                           "review_purpose": "library_publication"},
        "audience_scope": {"publication_scope": "school_library", "age_policy_ref": "age-v1",
                           "purpose_codes": ["classroom"]},
        "review_dimension": dimension, "expected_review_revision": record.review_revision}
    if decision != "approve":
        review["reason"] = "needs revision"
    review.update(overrides)
    fields: dict[str, object] = {"review": review}
    if action == "request_changes":
        fields["reason"] = review["reason"]
    return command(action, request, record, **fields)


def submitted(service: ContentCommands) -> ContentRecord:
    result = service.execute("author", "school", command("create", "create", content=BODY))
    return service.execute("author", "school", command("submit_review", "submit", result.record),
                           expected_revision=result.record.revision).record


def approved(service: ContentCommands) -> tuple[ContentRecord, dict[str, str]]:
    record = submitted(service)
    refs: dict[str, str] = {"review_policy_version": "policy-v1"}
    for dimension in ("safety", "pedagogical"):
        result = service.execute("reviewer", "school", review_command(record, dimension, dimension),
                                 expected_revision=record.revision)
        record = result.record
        refs[dimension + "_review_id"] = result.review_record.review_id
    return record, refs
