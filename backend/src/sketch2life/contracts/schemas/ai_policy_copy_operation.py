"""Immutable queued copy operation and historical authority, not a dispatch grant."""

from pydantic import AwareDatetime, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_copy import CopyAuthorityGrant, ProviderCopyCommand
from sketch2life.contracts.schemas.ai_policy_copy_registry import CopyRegistryRegistration


class CopyOperationEnvelope(StrictPolicyModel):
    operation_key: Sha256Hex
    binding_digest: Sha256Hex
    principal_id: OpaqueId
    organization_id: OpaqueId
    command: ProviderCopyCommand
    target: CopyRegistryRegistration
    initial_authority: CopyAuthorityGrant
    created_at: AwareDatetime

    @model_validator(mode="after")
    def exact_target_and_authority(self) -> "CopyOperationEnvelope":
        if (self.target.organization_id, self.target.scope_ref) != (
            self.organization_id,
            self.command.scope_ref,
        ):
            raise ValueError("operation target scope mismatch")
        grant = self.initial_authority
        if (
            (grant.organization_id, grant.principal_id, grant.command_digest)
            != (self.organization_id, self.principal_id, self.binding_digest)
            or grant.allowed is not True
            or grant.expires_at <= self.created_at
        ):
            raise ValueError("operation initial authority mismatch")
        return self

    def binding(self) -> dict[str, object]:
        return dict(
            principal_id=self.principal_id,
            organization_id=self.organization_id,
            command=self.command.model_dump(mode="json"),
            target=self.target.model_dump(mode="json"),
        )

    def key_binding(self) -> dict[str, object]:
        return dict(
            principal_id=self.principal_id,
            organization_id=self.organization_id,
            scope_ref=self.command.scope_ref,
            client_request_id=self.command.client_request_id,
            copy_id=self.target.copy_id,
            operation=self.command.operation,
        )


class CopyOperationAuthorization(StrictPolicyModel):
    operation_key: Sha256Hex
    authority: CopyAuthorityGrant
    observed_at: AwareDatetime

    @model_validator(mode="after")
    def usable_at_observation(self) -> "CopyOperationAuthorization":
        if self.authority.allowed is not True or self.authority.expires_at <= self.observed_at:
            raise ValueError("invalid historical operation authority")
        return self
