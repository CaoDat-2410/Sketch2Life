"""Internal hook result references only; no client verified/deleted/cancelled assertions."""

from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_copy import (
    CopyAuthorityGrant,
    CopyReceiptReference,
    ReasonCode,
)


class CopyHookResponse(StrictPolicyModel):
    operation_key: Sha256Hex
    binding_digest: Sha256Hex
    outcome: Literal["pending", "unsupported", "exception", "receipt_available"]
    reference: CopyReceiptReference | None = None
    reason_code: ReasonCode | None = None

    @model_validator(mode="after")
    def truthful_reference(self) -> "CopyHookResponse":
        if self.outcome == "receipt_available":
            if self.reference is None:
                raise ValueError("receipt reference required")
        elif self.reference is not None or self.reason_code is None:
            raise ValueError("nonreceipt response requires reason only")
        return self


class CopyDeliveryRecord(StrictPolicyModel):
    """Internal persistence shape; domain constructor validates full transition invariants."""

    operation_key: Sha256Hex
    binding_digest: Sha256Hex
    revision: int = Field(ge=0)
    status: Literal[
        "queued", "in_flight", "pending", "unsupported", "exception", "receipt_available"
    ]
    claim_token: OpaqueId | None
    claim_started_at: AwareDatetime | None
    claim_expires_at: AwareDatetime | None
    used_tokens: tuple[OpaqueId, ...]
    last_response: CopyHookResponse | None


class CopyDeliveryAuthority(StrictPolicyModel):
    """Trusted current delivery policy output, never a request field or cached grant."""

    grant: CopyAuthorityGrant
    claim_deadline: AwareDatetime

    @model_validator(mode="after")
    def bounded_deadline(self) -> "CopyDeliveryAuthority":
        if self.claim_deadline > self.grant.expires_at:
            raise ValueError("claim exceeds current authority")
        return self


class CopyDeliveryAuthorityEvidence(StrictPolicyModel):
    organization_id: OpaqueId
    principal_id: OpaqueId
    scope_ref: OpaqueId
    operation_key: Sha256Hex
    phase: Literal["claim", "dispatch", "completion"]
    state_revision: int = Field(ge=0)
    authority: CopyDeliveryAuthority
    observed_at: AwareDatetime
