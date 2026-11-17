"""Trusted exact operation proof DTOs, not client assertions or raw provider bytes."""

from typing import Literal

from pydantic import AwareDatetime, Field

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference, ReasonCode
from sketch2life.contracts.schemas.ai_policy_copy_operation import CopyOperationEnvelope


class CopyOperationReceiptBinding(StrictPolicyModel):
    envelope: CopyOperationEnvelope
    delivery_revision: int = Field(ge=1)
    reference: CopyReceiptReference
    authority_revision: OpaqueId


class VerifiedOperationReceipt(StrictPolicyModel):
    binding_digest: Sha256Hex
    reference: CopyReceiptReference
    outcome: Literal["deleted", "cancel_confirmed", "pending", "unsupported", "exception"]
    verified: bool
    evidence_kind: Literal["fixture", "provider"]
    expires_at: AwareDatetime
    reason_code: ReasonCode | None = None
