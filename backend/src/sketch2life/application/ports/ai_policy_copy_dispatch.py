"""Explicit current worker/retry/deadline authority. No permissive/default implementation."""

from contextlib import AbstractContextManager
from typing import Literal, Protocol

from sketch2life.application.ports.ai_policy_copy import ProviderCopyVerificationAccess
from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyDeliveryAuthority
from sketch2life.contracts.schemas.ai_policy_copy_operation import CopyOperationEnvelope
from sketch2life.domain.ai_policy.copy_delivery import DeliveryState

DeliveryPhase = Literal["claim", "dispatch", "completion"]


class CopyDispatchAccess(ProviderCopyVerificationAccess, Protocol):
    def authorize_delivery(
        self,
        envelope: CopyOperationEnvelope,
        state: DeliveryState,
        phase: DeliveryPhase,
        binding_digest: str,
    ) -> CopyDeliveryAuthority:
        """Current worker/action/retry policy and deadline, exact envelope/state/phase.

        Enforce current BE1 subject/purpose/source/profile/expiry/revocation and
        adopted delivery/retry ceilings, never infer permission from old intent or
        mechanically retryable state. Explicit approved claim deadline, no TTL
        default. Pre-acquire all fences before own scope lock; confirmation under
        DB lock must not acquire outer locks/network. Hold real owner/profile and
        deadline fences through commits and hook invocation, without a DB lock.
        """
        ...


class CopyDispatchBoundary(Protocol):
    def guard(
        self, principal_id: str, organization_id: str
    ) -> AbstractContextManager[CopyDispatchAccess]:
        """Actual integration must enforce remote-start/commit deadlines, not just app prechecks."""
        ...
