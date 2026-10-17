"""Scoped original copy inventory; current owner authorization belongs outside persistence."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from sketch2life.contracts.schemas.ai_policy_copy_candidates import (
    CopyCandidateCursor,
    CopyCandidateRequest,
)
from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyDeliveryAuthorityEvidence
from sketch2life.contracts.schemas.ai_policy_copy_history import CopyInventoryEvidence
from sketch2life.contracts.schemas.ai_policy_copy_operation import (
    CopyOperationAuthorization,
    CopyOperationEnvelope,
)
from sketch2life.contracts.schemas.ai_policy_copy_registry import (
    CopyCoverageObservation,
    CopyRegistryRegistration,
)
from sketch2life.domain.ai_jobs.provider_copy import CopyKind, ProviderCopy, request_purge
from sketch2life.domain.ai_policy.copy_delivery import DeliveryResponse, DeliveryState


@dataclass(frozen=True, slots=True)
class RegisteredProviderCopy:
    registration: CopyRegistryRegistration
    initially_quarantined: bool

    def initial_copy(self) -> ProviderCopy:
        """Initial metadata only; later lifecycle/authorization must load current state."""
        item = self.registration
        copy = ProviderCopy(
            item.copy_id,
            item.organization_id,
            item.scope_ref,
            CopyKind(item.kind),
            item.original_profile_ref.ref,
        )
        return request_purge(copy) if self.initially_quarantined else copy


@dataclass(frozen=True, slots=True)
class CopyRegistryPage:
    revision: int
    scope_purging: bool
    records: tuple[RegisteredProviderCopy, ...]
    next_after: str | None
    coverage: CopyCoverageObservation | None

    @property
    def coverage_status(self) -> Literal["unknown", "partial", "reported_complete"]:
        if self.coverage is None:
            return "unknown"
        return (
            "reported_complete"
            if set(self.coverage.observed_sources) == set(self.coverage.required_sources)
            else "partial"
        )


@dataclass(frozen=True, slots=True)
class CopyOperationPage:
    """Historical intent keys, NOT pending status, a claim or current permission."""

    revision: int
    operation_keys: tuple[str, ...]
    next_after: str | None


@dataclass(frozen=True, slots=True)
class CopyCandidatePage:
    revision: int
    as_of: datetime
    operation_keys: tuple[str, ...]
    next_cursor: CopyCandidateCursor | None


class ProviderCopyRegistryTransaction(Protocol):
    def delivery_candidates(self, request: CopyCandidateRequest) -> CopyCandidatePage:
        """Internal metadata under current owner read guard, never claim/retry authority."""
        ...

    def record_delivery_authority(self, evidence: CopyDeliveryAuthorityEvidence) -> None:
        """Historical phase grant in mutation/pre-dispatch UoW, never a live grant."""
        ...

    def get_delivery(self, operation_key: str) -> DeliveryState:
        """Historical state only; lazy queued state requires an existing exact intent."""
        ...

    def claim_delivery(
        self, operation_key: str, *, expected_revision: int, token: str, expires_at: datetime
    ) -> DeliveryState:
        """Caller owns current authority and approved deadline, no implicit TTL or permission."""
        ...

    def finish_delivery(
        self, response: DeliveryResponse, *, expected_revision: int, token: str
    ) -> DeliveryState:
        """Record hook metadata atomically, never verified deletion/cancel confirmation."""
        ...

    def operation_page(
        self, *, limit: int, after: str | None = None, expected_revision: int | None = None
    ) -> CopyOperationPage:
        """Scoped internal discovery under adopted current read guard; never a dispatch grant."""
        ...

    def get_operation(self, operation_key: str) -> CopyOperationEnvelope | None:
        """Recover immutable metadata only; never a dispatch/authorization grant."""
        ...

    def enqueue_operation(
        self, envelope: CopyOperationEnvelope, authorization: CopyOperationAuthorization
    ) -> CopyOperationEnvelope:
        """Atomic exact intent/event/fence/history; caller holds current owner/profile guard."""
        ...

    def record_evidence(self, evidence: CopyInventoryEvidence) -> None:
        """Append immutable historical verification in this UoW; not a live grant."""
        ...

    def get(self, copy_id: str) -> RegisteredProviderCopy | None: ...

    def register(self, registration: CopyRegistryRegistration) -> RegisteredProviderCopy: ...

    def mark_purging(self) -> int: ...

    def record_coverage(self, observation: CopyCoverageObservation) -> int: ...

    def page(
        self, *, limit: int, after: str | None = None, expected_revision: int | None = None
    ) -> CopyRegistryPage: ...


class ProviderCopyInventoryStore(Protocol):
    def transaction(
        self, organization_id: str, scope_ref: str, *, principal_id: str, for_update: bool = False
    ) -> AbstractContextManager[ProviderCopyRegistryTransaction]:
        """Hold current owner/profile/discovery guard BEFORE own registry scope lock.

        Persistence is not authorization or source completeness proof. Write UoW
        shares registration/fence/coverage/audit commit; read UoW holds scope SHARE.
        No provider call under registry lock. Pages are inventory, never deletion
        proof or permission for late results to expose in a purging scope.
        """
        ...
