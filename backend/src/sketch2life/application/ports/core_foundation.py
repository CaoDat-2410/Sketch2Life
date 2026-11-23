"""Replaceable ports for core identity, policy, aggregate, and audit access."""

from __future__ import annotations

import re
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Final, Protocol
from uuid import UUID

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
    organization_id: str | None
    aggregate_id: str
    aggregate_revision: int
    owner_scope_kind: str = "ORGANIZATION"
    owner_scope_ref: str | None = None
    attempt_count: int = 0


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
    organization_id: str | None
    actor_ref: str | None
    action: str
    resource_type: str
    resource_id: str
    decision: str
    created_at: datetime
    owner_scope_kind: str = "ORGANIZATION"
    owner_scope_ref: str | None = None


@dataclass(frozen=True, slots=True)
class OutboxState:
    event_id: str
    event_type: str
    organization_id: str | None
    aggregate_id: str
    aggregate_revision: int
    status: OutboxDeliveryStatus
    attempt_count: int
    available_at: datetime
    lease_until: datetime | None
    delivered_at: datetime | None
    owner_scope_kind: str = "ORGANIZATION"
    owner_scope_ref: str | None = None


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

    def current_revision_for_scope(
        self, aggregate_id: str, *, scope: LifecycleScope
    ) -> int | None: ...


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

    def get_state_for_scope(
        self, *, scope: LifecycleScope, event_id: str
    ) -> OutboxState | None: ...


# --------------------------------------------------------------------------------------------
# FR-C-08 lifecycle: typed owner scope, Core asset purge (port design Draft 6 §5), Core upload
# close, outbox lease cycle, BE1 receipt store, lifecycle audit write and the AI Jobs notice
# port used by the BE1 lifecycle consumer (DTR Draft 6 §6.2-§6.3).
# --------------------------------------------------------------------------------------------

PARENT_SCOPE_KIND: Final = "PARENT_ACCOUNT"
ORGANIZATION_SCOPE_KIND: Final = "ORGANIZATION"
_SCOPE_KINDS: Final = frozenset({PARENT_SCOPE_KIND, ORGANIZATION_SCOPE_KIND})
_SCOPE_REF = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


@dataclass(frozen=True, slots=True)
class LifecycleScope:
    """``OwnerScopeRefV1``: a typed owner scope; ``GLOBAL`` is never accepted (DTR rule 1)."""

    kind: str
    ref: str

    def __post_init__(self) -> None:
        if self.kind not in _SCOPE_KINDS or not _SCOPE_REF.fullmatch(self.ref):
            raise CoreAssetPurgeError("SCOPE_INVALID")


class CoreAssetPurgeError(RuntimeError):
    """Typed Core lifecycle failure (port design §8); messages carry the code only."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def validate_run_ref(value: object) -> str:
    """Port design §4 item 6: 36 characters and equal to ``str(UUID(value))``."""

    if not isinstance(value, str) or len(value) != 36:
        raise CoreAssetPurgeError("RUN_REF_INVALID")
    try:
        canonical = str(UUID(value))
    except ValueError:
        raise CoreAssetPurgeError("RUN_REF_INVALID") from None
    if canonical != value:
        raise CoreAssetPurgeError("RUN_REF_INVALID")
    return value


def run_object_prefix(run_ref: str) -> str:
    return "parent/" + validate_run_ref(run_ref) + "/"


RETAINED_REASON_CODES: Final = (
    "SHARED_REFERENCE",
    "SCOPE_MISMATCH",
    "KEY_UNKNOWN",
    "LINEAGE_KEPT",
)


@dataclass(frozen=True, slots=True, order=True)
class AssetKey:
    asset_ref: str
    asset_version: int = 1


@dataclass(frozen=True, slots=True)
class AssetCandidate:
    """One ``core_asset_metadata`` row of the run's closure (any scope)."""

    asset_ref: str
    asset_version: int
    owner_scope_kind: str
    owner_scope_ref: str | None
    source_refs: tuple[str, ...]
    derived_from_ref: str | None

    @property
    def key(self) -> AssetKey:
        return AssetKey(self.asset_ref, self.asset_version)


@dataclass(frozen=True, slots=True)
class RetainedAsset:
    key: AssetKey
    reason_code: str


@dataclass(frozen=True, slots=True)
class CandidateSet:
    scope: LifecycleScope
    run_ref: str
    assets: tuple[AssetCandidate, ...]
    edges: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class RunAssetPurgePlan:
    scope: LifecycleScope
    run_ref: str
    referenced_elsewhere: tuple[str, ...]
    removable: tuple[AssetKey, ...]
    retained: tuple[RetainedAsset, ...]
    removable_key_count: int
    removable_digest: str
    plan_sha256: str
    candidate_count: int

    @property
    def empty(self) -> bool:
        """Port design §5.1: no candidate at all; a retained plan is never empty."""

        return self.candidate_count == 0 and not self.retained


@dataclass(frozen=True, slots=True)
class ObjectPurgeResult:
    deleted_object_count: int


@dataclass(frozen=True, slots=True)
class SweepResult:
    swept_count: int


@dataclass(frozen=True, slots=True)
class RowPurgeResult:
    metadata_rows_deleted: int
    lineage_edges_deleted: int


@dataclass(frozen=True, slots=True)
class RunAssetPurgeVerification:
    complete: bool
    remaining_row_count: int
    unexpected_object_count: int


@dataclass(frozen=True, slots=True)
class ReviewReport:
    retained: tuple[RetainedAsset, ...]
    unclean_keys: tuple[str, ...]
    listed_candidate_keys: tuple[str, ...]


class RunAssetPurgePort(Protocol):
    """Core Asset alone deletes asset rows, lineage and the objects they name (§4 item 1)."""

    def closure_candidates(self, scope: LifecycleScope, run_ref: str) -> CandidateSet: ...

    def plan_run_purge(
        self, candidates: CandidateSet, referenced_elsewhere: frozenset[str]
    ) -> RunAssetPurgePlan: ...

    def purge_objects(self, plan: RunAssetPurgePlan) -> ObjectPurgeResult: ...

    def sweep_run_prefix(self, scope: LifecycleScope, run_ref: str) -> SweepResult: ...

    def delete_rows(
        self, plan: RunAssetPurgePlan, referenced_elsewhere_now: frozenset[str]
    ) -> RowPurgeResult: ...

    def verify_run_purged(
        self, scope: LifecycleScope, run_ref: str
    ) -> RunAssetPurgeVerification: ...

    def review_report(
        self, scope: LifecycleScope, run_ref: str, referenced_elsewhere: frozenset[str]
    ) -> ReviewReport: ...


class RunUploadClosePort(Protocol):
    """Core upload records that name the run (DTR step 1)."""

    def plan_close_run_uploads(self, scope: LifecycleScope, run_ref: str) -> tuple[str, ...]:
        """Sorted ids of the open upload sessions that name the run (read only)."""
        ...

    def close_run_uploads(self, scope: LifecycleScope, run_ref: str) -> int:
        """Close every open upload session of the run in one transaction (idempotent)."""
        ...


LifecycleEffect = Callable[[Any, OutboxEnvelope], None]


class LifecycleOutboxPort(Protocol):
    """Core outbox lease cycle (DTR §6.3): claim, renew, defer and the local effect."""

    def claim_ready(
        self,
        *,
        worker_id: str,
        limit: int = 50,
        lease_seconds: int = 30,
        event_types: Collection[str] | None = None,
    ) -> Sequence[OutboxEnvelope]: ...

    def renew_lease(self, *, event_id: str, worker_id: str, lease_seconds: int) -> bool: ...

    def defer(self, *, event_id: str, worker_id: str, retry_after_seconds: int) -> bool: ...

    def process_local_once(
        self,
        *,
        event_id: str,
        worker_id: str,
        consumer_name: str,
        effect: LifecycleEffect,
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class LifecycleReceipt:
    """A ``be1_data_lifecycle_requests`` row as the lifecycle consumer sees it."""

    request_id: str
    state: str
    result_ref: str | None
    unresolved_items: int
    owner_scope_kind: str
    owner_scope_ref: str | None
    completed_at: datetime | None = None
    # ``story_run:<run_id>``; None only when a store cannot report it.
    target_ref: str | None = None


class LifecycleReceiptStorePort(Protocol):
    """BE1-owned durable receipt; every update is a compare-and-set (DTR §6.3)."""

    def read(self, request_id: str, *, tx: Any = None) -> LifecycleReceipt | None: ...

    def ensure(
        self, *, request_id: str, run_ref: str, scope: LifecycleScope, tx: Any = None
    ) -> LifecycleReceipt:
        """Insert the receipt if absent (``requested``, four unresolved items)."""
        ...

    def compare_and_set(
        self,
        *,
        request_id: str,
        expected_state: str,
        expected_result_ref: str | None,
        state: str,
        result_ref: str | None,
        unresolved_items: int,
        completed_at: datetime | None = None,
        tx: Any = None,
    ) -> bool: ...


class LifecycleAuditWriterPort(Protocol):
    def write_exception(
        self,
        *,
        tx: Any,
        request_id: str,
        run_ref: str,
        scope: LifecycleScope,
        processed_event_id: str,
    ) -> None:
        """Insert-if-absent ``lifecycle.exception`` with the event-keyed audit id."""
        ...


class LifecycleNoticePort(Protocol):
    """AI Jobs cancellation notice of a StoryRun lifecycle (DTR §5.2); matches no job."""

    def notice_exists(self, notice_id: str) -> bool: ...

    def record_parent_notice(
        self,
        *,
        notice_id: str,
        scope: LifecycleScope,
        story_run_ref: str,
        reason_code: str,
    ) -> None:
        """Insert-if-absent, ``COMPLETE`` with ``applied_count = 0``; a Parent scope only."""
        ...

    def record_lifecycle_notice(
        self,
        *,
        notice_id: str,
        scope: LifecycleScope,
        story_run_ref: str,
        reason_code: str,
    ) -> None:
        """Insert-if-absent, ``COMPLETE`` with ``applied_count = 0``, for the Parent scope and
        for an ``ORGANIZATION`` scope (a Teacher run, FEAT-066 T-13a). It never selects a job
        (T-4b2 adds the job match, hand-off H2)."""
        ...


__all__ = [
    "AggregateRevisionPort",
    "AssetCandidate",
    "AssetKey",
    "CandidateSet",
    "CoreAssetPurgeError",
    "LifecycleAuditWriterPort",
    "LifecycleEffect",
    "LifecycleNoticePort",
    "LifecycleOutboxPort",
    "LifecycleReceipt",
    "LifecycleReceiptStorePort",
    "LifecycleScope",
    "ORGANIZATION_SCOPE_KIND",
    "ObjectPurgeResult",
    "PARENT_SCOPE_KIND",
    "RETAINED_REASON_CODES",
    "RetainedAsset",
    "ReviewReport",
    "RowPurgeResult",
    "RunAssetPurgePlan",
    "RunAssetPurgePort",
    "RunAssetPurgeVerification",
    "RunUploadClosePort",
    "SweepResult",
    "run_object_prefix",
    "validate_run_ref",
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
