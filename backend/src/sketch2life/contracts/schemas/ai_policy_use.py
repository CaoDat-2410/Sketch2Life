"""Backend-only exact request/policy pin metadata; never an authorization token."""

from typing import Literal

from pydantic import Field

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef, StrictPolicyModel

PolicyUsePhase = Literal["create", "dispatch", "retry", "completion", "exposure"]


class PolicyUseRequest(StrictPolicyModel):
    request_id: OpaqueId
    request_revision: int = Field(ge=1)
    input_hash: Sha256Hex
    purpose_code: OpaqueId
    feature_scope: OpaqueId
    model_profile_ref: PolicyDefinitionRef


class PolicyUsePin(StrictPolicyModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    organization_id: OpaqueId
    request: PolicyUseRequest
    policy_ref: PolicyDefinitionRef
    activation_epoch: int = Field(ge=1)
    registry_revision: OpaqueId


class PolicyUseDecision(StrictPolicyModel):
    organization_id: OpaqueId
    principal_id: OpaqueId
    binding_digest: Sha256Hex
    allowed: bool


class PolicyUseObservation(StrictPolicyModel):
    """Valid only while enclosing lease/current guards are held; not a bearer grant."""

    pin: PolicyUsePin
    phase: PolicyUsePhase
    current_scope_epoch: int = Field(ge=1)
    current_registry_revision: OpaqueId
    required_budget_ref: PolicyDefinitionRef
    required_concurrency_ref: PolicyDefinitionRef
    required_retry_ref: PolicyDefinitionRef
