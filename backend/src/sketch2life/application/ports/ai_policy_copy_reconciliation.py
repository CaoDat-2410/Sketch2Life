"""Current authority and exact receipt bytes/issuer verification; no default adapter."""

from contextlib import AbstractContextManager
from typing import Protocol

from sketch2life.application.ports.ai_policy_copy import ProviderCopyVerificationAccess
from sketch2life.contracts.schemas.ai_policy_copy_reconciliation import (
    CopyOperationReceiptBinding,
    VerifiedOperationReceipt,
)


class CopyOperationReceiptAccess(ProviderCopyVerificationAccess, Protocol):
    def verify_operation_receipt(
        self, binding: CopyOperationReceiptBinding, binding_digest: str
    ) -> VerifiedOperationReceipt:
        """Authenticate exact stored reference/hash/issuer/original profile/operation.

        Distinguish confirmed cancel vs purge; verified output must come from
        adopted backend evidence verification, never raw booleans or latest alias.
        Fixture stays fixture. No provider side effect, BE1 request closure or job
        mutation. Current source/profile/evidence fences precede own DB locks.
        """
        ...


class CopyOperationReceiptBoundary(Protocol):
    def guard(
        self, principal_id: str, organization_id: str
    ) -> AbstractContextManager[CopyOperationReceiptAccess]:
        """Hold actual current rights/profile/source/evidence/deadline fences through commit."""
        ...
