"""BE2-07 trusted authority ports; fixture adapters implement these outside the domain."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from sketch2life.contracts.schemas.knowledge_bundles import (
    KnowledgeBundleRecordV1,
    KnowledgeSupersededV1,
)
from sketch2life.domain.knowledge_bundle import (
    AudienceContextV1,
    BasisRef,
    BundleHead,
    ContributorV1,
    CorrectionV1,
    KnowledgeBasisV1,
    KnowledgeBundleVersion,
    ReviewedClaimV1,
    ReviewedSourceV1,
)


class KnowledgeFacts(Protocol):
    @property
    def coordination_token(self) -> object: ...

    def catalog_claims(self) -> tuple[ReviewedClaimV1, ...]: ...

    def sources(self) -> tuple[ReviewedSourceV1, ...]: ...

    def basis(self, ref: BasisRef) -> KnowledgeBasisV1 | None: ...

    def audience(self, organization_id: str, session_id: str) -> AudienceContextV1 | None: ...

    def contributor_allowed(
        self, organization_id: str, session_id: str, contributor: ContributorV1
    ) -> bool: ...

    def contributor_disclosure_allowed(
        self, organization_id: str, session_id: str, contributor: ContributorV1
    ) -> bool: ...

    def policy(self) -> tuple[str, bool]: ...

    def mutation_allowed(self, organization_id: str, session_id: str) -> bool: ...

    def teacher_allowed(self, organization_id: str, principal_id: str, session_id: str) -> bool: ...

    def disclosure_allowed(
        self, organization_id: str, principal_id: str, session_id: str
    ) -> bool: ...


ReceiptKey = tuple[str, str, str, str, str]


@dataclass(frozen=True)
class KnowledgeResult:
    status: int
    record: KnowledgeBundleRecordV1


@dataclass(frozen=True)
class KnowledgeReceipt:
    key: ReceiptKey
    fingerprint: str
    result: KnowledgeResult
    version: KnowledgeBundleVersion


@dataclass(frozen=True)
class KnowledgeAudit:
    operation_id: str
    action: str
    bundle_id: str
    bundle_version: int
    principal_id: str


class KnowledgeUnitOfWork(Protocol):
    def get_head(self, bundle_id: str) -> BundleHead | None: ...

    def get_version(self, bundle_id: str, version: int) -> KnowledgeBundleVersion | None: ...

    def get_receipt(self, key: ReceiptKey) -> KnowledgeReceipt | None: ...

    def put_head(self, head: BundleHead, expected_version: int) -> None: ...

    def put_version(self, version: KnowledgeBundleVersion) -> None: ...

    def put_correction(self, correction: CorrectionV1) -> None: ...

    def put_receipt(self, receipt: KnowledgeReceipt) -> None: ...

    def add_audit(self, audit: KnowledgeAudit) -> None: ...

    def add_event(self, event: KnowledgeSupersededV1) -> None: ...


class KnowledgeRepository(Protocol):
    @property
    def coordination_token(self) -> object: ...

    def transaction(self) -> AbstractContextManager[KnowledgeUnitOfWork]: ...


class KnowledgeConflict(ValueError):
    """A staged revision or unique identity lost to an accepted unit."""


class KnowledgeStorageFailure(RuntimeError):
    """Fixture failure; after_commit means acknowledgement was lost, not rollback."""
