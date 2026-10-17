"""Owned current-copy metadata and immutable verification observation; not an auth grant."""

from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_copy import (
    CopyAuthorityGrant,
    CopyReceiptReference,
    ReasonCode,
)
from sketch2life.contracts.schemas.ai_policy_copy_reconciliation import (
    CopyOperationReceiptBinding,
    VerifiedOperationReceipt,
)
from sketch2life.contracts.schemas.ai_policy_copy_registry import CopyRegistryRegistration


class CopyLifecycleRecord(StrictPolicyModel):
    registration: CopyRegistryRegistration
    revision: int = Field(ge=0)
    status: Literal[
        "discovered",
        "cancel_requested",
        "purge_requested",
        "deleted",
        "pending",
        "unsupported",
        "exception",
    ]
    purge_reference: CopyReceiptReference | None = None
    purge_evidence_kind: Literal["fixture", "provider"] | None = None
    reason_code: ReasonCode | None = None
    cancel_confirmed: bool = False
    cancel_evidence_kind: Literal["fixture", "provider"] | None = None

    @model_validator(mode="after")
    def coherent_provenance(self) -> "CopyLifecycleRecord":
        if (self.purge_reference is None) != (self.purge_evidence_kind is None):
            raise ValueError("purge provenance mismatch")
        if self.status == "deleted" and self.purge_reference is None:
            raise ValueError("deletion requires receipt")
        if self.cancel_confirmed != (self.cancel_evidence_kind is not None):
            raise ValueError("cancel provenance mismatch")
        return self


class CopyResolutionObservation(StrictPolicyModel):
    binding: CopyOperationReceiptBinding
    proof: VerifiedOperationReceipt
    authority: CopyAuthorityGrant
    observed_at: AwareDatetime
