"""Current inventory owner/source/profile authority; no permissive production implementation."""

from contextlib import AbstractContextManager
from typing import Literal, Protocol

from sketch2life.contracts.schemas.ai_policy_copy import CopyAuthorityGrant, CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_inventory import (
    CopyInventoryContext,
    CopyInventoryCoverageProof,
    CopyInventorySourceProof,
)
from sketch2life.contracts.schemas.ai_policy_copy_registry import CopyRegistryRegistration

CopyInventoryAction = Literal["register", "read", "coverage", "fence"]


class CopyInventoryAccess(Protocol):
    def authorize(
        self, context: CopyInventoryContext, action: CopyInventoryAction, binding_digest: str
    ) -> CopyAuthorityGrant:
        """Current exact BE1 data-request subject/purpose/expiry/revocation and action.

        Bind actor/org/full operation digest, owner revision/deadline. Author/ops
        role alone is insufficient. Recheck on replay; no client allowed assertion.
        Repeated confirmation under registry lock must use already-held fences;
        never acquire outer locks or perform network work at that point.
        """
        ...

    def registration_source(
        self,
        context: CopyInventoryContext,
        registration: CopyRegistryRegistration,
        reference: CopyReceiptReference,
        binding_digest: str,
    ) -> CopyInventorySourceProof:
        """Authenticate original source/copy kind/id/scope/profile version/hash and bytes.

        Verify exact source reference/hash/issuer and current adopted original
        provenance, not latest profile alias or caller asserted original ref.
        Keep source/profile fence and deadline valid through registry commit.
        """
        ...

    def coverage_source(
        self,
        context: CopyInventoryContext,
        expected_revision: int,
        reference: CopyReceiptReference,
        binding_digest: str,
    ) -> CopyInventoryCoverageProof:
        """Resolve authenticated explicit required/observed source inventory snapshot.

        Bind org/scope/revision and immutable exact attestation bytes/hash/issuer.
        No empty-list all-provider deletion inference. Return original report
        under current discovery fence; report is not overall BE1 closure authority.
        """
        ...


class CopyInventoryBoundary(Protocol):
    def guard(
        self, principal_id: str, organization_id: str, context: CopyInventoryContext
    ) -> AbstractContextManager[CopyInventoryAccess]:
        """Pre-acquire current owner/source/profile fences, hold through own UoW commit.

        Real owner must enforce source/request deadline at commit; a mutex or
        application-time precheck alone is not that adoption. No production
        defaults, credentials, provider selection or side effect from this port.
        """
        ...
