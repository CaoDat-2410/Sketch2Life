"""Reference-only inventory calls and trusted backend source-proof output."""

from pydantic import AwareDatetime, Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef, StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_registry import CopyCoverageObservation


class CopyInventoryContext(StrictPolicyModel):
    data_request_ref: PolicyDefinitionRef
    scope_ref: OpaqueId


class CopyInventoryReadRequest(CopyInventoryContext):
    limit: int = Field(ge=1, le=256)
    after: OpaqueId | None = None
    expected_revision: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def versioned_cursor(self) -> "CopyInventoryReadRequest":
        if self.after is not None and self.expected_revision is None:
            raise ValueError("continuation requires revision")
        return self


class CopyInventorySourceProof(StrictPolicyModel):
    """Trusted verifier output, NEVER a field accepted from client inventory calls."""

    binding_digest: Sha256Hex
    reference: CopyReceiptReference
    verified: bool
    expires_at: AwareDatetime


class CopyInventoryCoverageProof(CopyInventorySourceProof):
    observation: CopyCoverageObservation
