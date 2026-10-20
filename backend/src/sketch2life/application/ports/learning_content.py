"""BE2-12 storage boundaries. SQL/identity/adapters never leak into application."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.domain.learning_content.model import Authority, ContentVersion, ReviewProof

CONTENT_BOUNDARY_CONTRACT_VERSION = "0.1-candidate"


@dataclass(frozen=True, slots=True)
class ContentEvent:
    event_id: str
    kind: str
    principal_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ContentReceipt:
    organization_id: str
    principal_id: str
    request_id: str
    fingerprint: str
    result_json: str


class ContentTransaction(Protocol):
    def review_history(self, organization_id: str, record_id: str, *, version: int,
                       after_revision: int, limit: int) -> tuple[ReviewProof, ...]: ...

    def published_versions(self, organization_id: str,
                           record_id: str) -> tuple[ContentVersion, ...]: ...

    def load(self, organization_id: str, record_id: str, *, version: int | None = None,
             for_update: bool = False) -> ContentVersion | None: ...

    def save(self, content: ContentVersion, *, expected_revision: int | None,
             event: ContentEvent) -> None: ...

    def receipt(self, organization_id: str, principal_id: str,
                request_id: str) -> ContentReceipt | None: ...

    def add_receipt(self, receipt: ContentReceipt) -> None: ...


class ContentStore(Protocol):
    def transaction(self) -> AbstractContextManager[ContentTransaction]: ...


@dataclass(frozen=True, slots=True)
class ContentPolicy:
    """Current owner-supplied policy, not policy chosen by this feature."""

    version: str
    content_policy_ref: str
    age_policy_ref: str
    content_kinds: frozenset[str]
    purpose_codes: frozenset[str]


@dataclass(frozen=True, slots=True)
class SourceAssessment:
    """Server-derived assessment bound to the exact content and policy."""

    organization_id: str
    record_id: str
    version: int
    hash: str
    policy_version: str
    classification: str
    usage_allowed: bool
    moderation_passed: bool


class ContentAccess(Protocol):
    authority: Authority
    policy: ContentPolicy

    def assess_sources(self, content: ContentVersion) -> SourceAssessment: ...

    def review_effective(self, content: ContentVersion, proof: ReviewProof) -> bool: ...


class ContentBoundary(Protocol):
    """Candidate owner integration contract, not a production auth adapter.

    Enter verifies current principal/org; while held, authority, policy, source
    usage and review-effectiveness decisions are fenced against revocation.
    The application MUST hold this guard outside the entire storage transaction,
    through commit/rollback. Adapters unable to guarantee this must fail closed.
    Cross-owner adoption and durable fencing require separate runtime evidence.
    """

    def guard(self, principal_id: str,
              organization_id: str) -> AbstractContextManager[ContentAccess]: ...
