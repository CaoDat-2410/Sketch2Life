"""Read-only owned ledger metadata, not actual cost/provider permission."""

from typing import Protocol

from sketch2life.contracts.schemas.ai_policy_operations import (
    LedgerOperationsSnapshot,
    PolicyOperationsRequest,
)


class ResourceOperationsReader(Protocol):
    def snapshot(
        self, organization_id: str, request: PolicyOperationsRequest
    ) -> LedgerOperationsSnapshot:
        """Bounded exact scoped read, no lazy row creation or unknown-as-zero.

        Caller holds current operations-read guard. Values are recorded counters,
        may include fixture accounting and never establish actual provider cost.
        """
        ...
