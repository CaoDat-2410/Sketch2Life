"""Backend accounting shape only: numeric terms come from trusted adopted definitions."""

from typing import Literal

from pydantic import Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_use import (
    PolicyUseObservation,
    PolicyUsePin,
    PolicyUseRequest,
)


class ResourceReservationRequest(StrictPolicyModel):
    client_request_id: OpaqueId
    request: PolicyUseRequest
    pin: PolicyUsePin
    attempt_id: OpaqueId
    phase: Literal["create", "dispatch", "retry"]

    @model_validator(mode="after")
    def exact_request(self) -> "ResourceReservationRequest":
        if self.pin.request != self.request:
            raise ValueError("reservation must bind original request")
        return self


class ResourceQuote(StrictPolicyModel):
    """Trusted server output, NEVER caller settings or proof of production adoption."""

    quote_id: OpaqueId
    binding_digest: Sha256Hex
    observation: PolicyUseObservation
    attempt_id: OpaqueId
    unit: OpaqueId
    window_id: OpaqueId
    budget_ceiling: int = Field(ge=0)
    concurrency_ceiling: int = Field(ge=0)
    estimated_units: int = Field(ge=0)

    @model_validator(mode="after")
    def reservation_phase(self) -> "ResourceQuote":
        if self.observation.phase not in {"create", "dispatch", "retry"}:
            raise ValueError("quote cannot reserve during completion/exposure")
        return self


class AccountingEvidenceRef(StrictPolicyModel):
    ref: OpaqueId
    hash: Sha256Hex


class ResourceSettlementRequest(StrictPolicyModel):
    client_request_id: OpaqueId
    reservation_id: OpaqueId
    operation: Literal["consume", "release", "reconcile"]
    evidence_ref: AccountingEvidenceRef
