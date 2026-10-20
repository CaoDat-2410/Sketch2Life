"""Current BE1 data-request and adopted provider-receipt authority, not a client assertion."""

from contextlib import AbstractContextManager
from typing import Protocol

from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import (
    CopyAuthorityGrant,
    CopyReceiptReference,
    CopyVerificationBinding,
    ProviderCopyCommand,
    VerifiedCopyReceipt,
)
from sketch2life.domain.ai_jobs.provider_copy import ProviderCopy


class ProviderCopyVerificationAccess(Protocol):
    def authorize(self, command: ProviderCopyCommand, command_digest: str) -> CopyAuthorityGrant:
        """Resolve actual BE1 subject/purpose/revocation/source/data-request expiry.

        Echo exact actor/org/command digest and current authority revision. Expiry
        bounded by all applicable approved owner/source deadlines, no default TTL.
        Retain owner fence through caller verification/registry commit; raw role or
        client allowed/verified boolean never constitutes authority.
        """
        ...

    def resolve_profile(self, copy: ProviderCopy) -> PolicyDefinitionRef:
        """Exact ORIGINAL profile provenance for org/scope/copy, currently adopted.

        Resolve immutable original version/hash, not latest alias or a provider
        choice. Missing original provenance fails closed; never repin a copy.
        """
        ...

    def verify_receipt(
        self,
        binding: CopyVerificationBinding,
        reference: CopyReceiptReference,
        binding_digest: str,
    ) -> VerifiedCopyReceipt:
        """Authenticate exact bytes/hash/issuer/operation key/target/profile/outcome.

        Verify adopted backend/provider evidence and immutable reference, not a
        caller verified flag, bare receipt id or cached report. Fixture remains
        fixture. No actual provider side effect performed by verification. Retain
        current guard; missing/unknown proof fails, never invent deletion.
        """
        ...


class ProviderCopyVerificationBoundary(Protocol):
    def guard(
        self, principal_id: str, organization_id: str
    ) -> AbstractContextManager[ProviderCopyVerificationAccess]:
        """Current owner/profile/evidence fence; real implementation/adoption separate.

        Caller must compose same guard with eventual registry UoW. Returning a
        verified receipt from a closed context does not authorize later mutation.
        Real guard must enforce source/request expiry at the owner's commit fence;
        merely holding a mutex does not freeze time or prove deadline eligibility.
        No production adapter, permission or provider call inferred from protocol.
        """
        ...
