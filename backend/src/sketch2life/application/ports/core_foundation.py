"""Replaceable ports for core identity, policy, aggregate, and audit access."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from sketch2life.domain.core_foundation import (
    CanvasOperation,
    ConsentGrant,
    CoreScope,
    IdempotencyReceipt,
    ManagedChildProfile,
    SessionMembership,
    VerifiedPrincipal,
)


@dataclass(frozen=True, slots=True)
class CanvasMutationCommit:
    """Minimal trusted command data that must commit as one durable unit."""

    aggregate_id: str
    expected_revision: int
    next_revision: int
    organization_id: str
    actor_id: str
    operation: CanvasOperation
    receipt: IdempotencyReceipt
    outbox_event_id: str
    operation_payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CanvasCheckpointMetadata:
    checkpoint_id: str
    organization_id: str
    canvas_id: str
    document_epoch: int
    revision: int
    through_operation_id: str
    checksum_sha256: str
    storage_ref: str


@dataclass(frozen=True, slots=True)
class CoreAssetMetadata:
    asset_ref: str
    version: int
    organization_id: str
    content_sha256: str
    media_type: str
    source_refs: tuple[str, ...]
    derived_from_ref: str | None = None


@dataclass(frozen=True, slots=True)
class OutboxEnvelope:
    event_id: str
    event_type: str
    organization_id: str
    aggregate_id: str
    aggregate_revision: int


class OutboxDeliveryStatus(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    DELIVERED = "delivered"


@dataclass(frozen=True, slots=True)
class CanvasOperationRecord:
    organization_id: str
    operation: CanvasOperation
    resulting_revision: int
    request_fingerprint: str
    operation_payload: dict[str, object]
    accepted_at: datetime


@dataclass(frozen=True, slots=True)
class CoreAuditRecord:
    audit_id: str
    organization_id: str
    actor_ref: str | None
    action: str
    resource_type: str
    resource_id: str
    decision: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class OutboxState:
    event_id: str
    event_type: str
    organization_id: str
    aggregate_id: str
    aggregate_revision: int
    status: OutboxDeliveryStatus
    attempt_count: int
    available_at: datetime
    lease_until: datetime | None
    delivered_at: datetime | None


class VerifiedIdentityPort(Protocol):
    def resolve(self, principal_id: str) -> VerifiedPrincipal | None: ...


class ManagedProfilePort(Protocol):
    def get_profile(self, child_id: str) -> ManagedChildProfile | None: ...


class PurposeConsentPort(Protocol):
    def get_consent(self, *, organization_id: str, child_id: str) -> ConsentGrant | None: ...


class SessionMembershipPort(Protocol):
    def get_membership(self, *, session_id: str, child_id: str) -> SessionMembership | None: ...


class AggregateRevisionPort(Protocol):
    def current_revision(self, aggregate_id: str, *, organization_id: str) -> int | None: ...


class IdempotencyReceiptPort(Protocol):
    def get_receipt(
        self, *, organization_id: str, scope: str, key: str
    ) -> IdempotencyReceipt | None: ...


class CoreMutationTransactionPort(Protocol):
    """Atomically compare revision and persist operation, receipt, audit, and outbox."""

    def commit_canvas_mutation(self, mutation: CanvasMutationCommit) -> bool: ...


class CanvasOperationReadPort(Protocol):
    def get_operation(
        self, *, organization_id: str, operation_id: str
    ) -> CanvasOperationRecord | None: ...

    def list_operations(
        self,
        *,
        organization_id: str,
        canvas_id: str,
        after_revision: int,
        limit: int = 200,
    ) -> tuple[CanvasOperationRecord, ...]: ...


class ScopedAuditPort(Protocol):
    def append(
        self, *, organization_id: str, action: str, resource_id: str, decision: str
    ) -> None: ...


class ScopedAuditReadPort(Protocol):
    def list_for_resource(
        self, *, organization_id: str, resource_id: str, limit: int = 100
    ) -> tuple[CoreAuditRecord, ...]: ...


class ResourceScopePort(Protocol):
    def resolve_scope(self, resource_id: str) -> CoreScope | None: ...


class CanvasCheckpointPort(Protocol):
    def save_checkpoint(self, checkpoint: CanvasCheckpointMetadata) -> bool: ...

    def get_checkpoint(
        self, checkpoint_id: str, *, organization_id: str
    ) -> CanvasCheckpointMetadata | None: ...


class CoreAssetMetadataPort(Protocol):
    def save_asset_metadata(self, asset: CoreAssetMetadata) -> bool: ...

    def get_asset_metadata(
        self, asset_ref: str, version: int, *, organization_id: str
    ) -> CoreAssetMetadata | None: ...


class OutboxStatePort(Protocol):
    def get_state(self, *, organization_id: str, event_id: str) -> OutboxState | None: ...


__all__ = [
    "AggregateRevisionPort",
    "CanvasOperationReadPort",
    "CanvasOperationRecord",
    "CanvasCheckpointMetadata",
    "CanvasCheckpointPort",
    "CanvasMutationCommit",
    "CoreMutationTransactionPort",
    "CoreAssetMetadata",
    "CoreAssetMetadataPort",
    "CoreAuditRecord",
    "IdempotencyReceiptPort",
    "OutboxEnvelope",
    "OutboxDeliveryStatus",
    "OutboxState",
    "OutboxStatePort",
    "ManagedProfilePort",
    "PurposeConsentPort",
    "ResourceScopePort",
    "ScopedAuditPort",
    "ScopedAuditReadPort",
    "SessionMembershipPort",
    "VerifiedIdentityPort",
]
