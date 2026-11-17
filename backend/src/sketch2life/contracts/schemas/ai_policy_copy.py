"""BE2-14 verification boundary; reuse foundation copy lifecycle/report, no raw receipts."""

from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef, StrictPolicyModel

ReasonCode = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{1,79}$")]


class ProviderCopyCommand(StrictPolicyModel):
    client_request_id: OpaqueId
    data_request_ref: PolicyDefinitionRef
    scope_ref: OpaqueId
    operation: Literal["cancel", "purge"]


class CopyReceiptReference(StrictPolicyModel):
    ref: OpaqueId
    hash: Sha256Hex


class CopyAuthorityGrant(StrictPolicyModel):
    organization_id: OpaqueId
    principal_id: OpaqueId
    command_digest: Sha256Hex
    authority_revision: OpaqueId
    expires_at: AwareDatetime
    allowed: bool


class CopyVerificationBinding(StrictPolicyModel):
    principal_id: OpaqueId
    organization_id: OpaqueId
    command: ProviderCopyCommand
    authority_revision: OpaqueId
    copy_id: OpaqueId
    kind: Literal["input", "output", "job", "cache"]
    profile_ref: PolicyDefinitionRef


class VerifiedCopyReceipt(StrictPolicyModel):
    """Trusted verifier output only; client commands never contain these assertions."""

    binding_digest: Sha256Hex
    reference: CopyReceiptReference
    outcome: Literal["deleted", "pending", "unsupported", "exception"]
    verified: bool
    evidence_kind: Literal["fixture", "provider"]
    expires_at: AwareDatetime
    reason_code: ReasonCode | None = None
