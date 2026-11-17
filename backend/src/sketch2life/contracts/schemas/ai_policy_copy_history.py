"""Historical backend verification record; never a client grant or execution intent."""

from typing import Literal

from pydantic import AwareDatetime, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_copy import CopyAuthorityGrant
from sketch2life.contracts.schemas.ai_policy_copy_inventory import (
    CopyInventoryContext,
    CopyInventorySourceProof,
)
from sketch2life.contracts.schemas.ai_policy_copy_registry import (
    CopyCoverageObservation,
    CopyRegistryRegistration,
)


class CopyInventoryEvidence(StrictPolicyModel):
    principal_id: OpaqueId
    organization_id: OpaqueId
    context: CopyInventoryContext
    action: Literal["register", "coverage", "fence"]
    command_digest: Sha256Hex
    authority: CopyAuthorityGrant
    observed_at: AwareDatetime
    source: CopyInventorySourceProof | None = None
    registration: CopyRegistryRegistration | None = None
    coverage: CopyCoverageObservation | None = None

    @model_validator(mode="after")
    def exact_history(self) -> "CopyInventoryEvidence":
        grant = self.authority
        if (
            (grant.principal_id, grant.organization_id, grant.command_digest)
            != (self.principal_id, self.organization_id, self.command_digest)
            or grant.allowed is not True
            or grant.expires_at <= self.observed_at
        ):
            raise ValueError("invalid historical authority")
        target = self.registration if self.action == "register" else self.coverage
        if self.action == "fence":
            if any(value is not None for value in (self.source, self.registration, self.coverage)):
                raise ValueError("fence has no source payload")
            return self
        if (
            self.source is None
            or self.source.verified is not True
            or self.source.binding_digest != self.command_digest
            or self.source.expires_at <= self.observed_at
            or target is None
            or (target.organization_id, target.scope_ref)
            != (self.organization_id, self.context.scope_ref)
            or (self.action == "register" and self.coverage is not None)
            or (self.action == "coverage" and self.registration is not None)
        ):
            raise ValueError("invalid historical source")
        if self.coverage is not None and self.coverage.attestation_ref != self.source.reference:
            raise ValueError("coverage reference mismatch")
        return self

    def command_binding(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self.source is not None:
            payload["reference"] = self.source.reference.model_dump(mode="json")
        if self.registration is not None:
            payload["registration"] = self.registration.model_dump(mode="json")
        if self.coverage is not None:
            payload["expected_revision"] = self.coverage.expected_revision
        return dict(
            principal_id=self.principal_id,
            organization_id=self.organization_id,
            action="copy_inventory." + self.action,
            context=self.context.model_dump(mode="json"),
            payload=payload,
        )
