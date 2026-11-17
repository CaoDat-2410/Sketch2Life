"""Own backend copy inventory/provenance, not a provider deletion or client authority report."""

from typing import Literal

from pydantic import Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef, StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference


class CopyRegistryRegistration(StrictPolicyModel):
    organization_id: OpaqueId
    scope_ref: OpaqueId
    copy_id: OpaqueId
    kind: Literal["input", "output", "job", "cache"]
    original_profile_ref: PolicyDefinitionRef


class CopyCoverageObservation(StrictPolicyModel):
    """Backend source report; not a public permission or proof of provider deletion."""

    organization_id: OpaqueId
    scope_ref: OpaqueId
    expected_revision: int = Field(ge=0)
    registry_revision: OpaqueId
    attestation_ref: CopyReceiptReference
    required_sources: tuple[OpaqueId, ...] = Field(min_length=1, max_length=256)
    observed_sources: tuple[OpaqueId, ...] = Field(max_length=256)

    @model_validator(mode="after")
    def source_sets(self) -> "CopyCoverageObservation":
        if (
            len(set(self.required_sources)) != len(self.required_sources)
            or len(set(self.observed_sources)) != len(self.observed_sources)
            or not set(self.observed_sources) <= set(self.required_sources)
        ):
            raise ValueError("coverage sources must be unique explicit subset")
        return self
