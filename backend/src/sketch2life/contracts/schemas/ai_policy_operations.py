"""Allowlisted internal operational metadata, never permission or actual cost proof."""

from typing import Literal

from pydantic import Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef, StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_telemetry import OperationsTelemetryView


class BudgetWindowRef(StrictPolicyModel):
    definition: PolicyDefinitionRef
    unit: OpaqueId
    window_id: OpaqueId


class PolicyOperationsRequest(StrictPolicyModel):
    feature_scope: OpaqueId
    budget_window: BudgetWindowRef | None = None


class LedgerOperationsSnapshot(StrictPolicyModel):
    organization_id: OpaqueId
    request: PolicyOperationsRequest
    occupied_slots: int | None = Field(default=None, ge=0)
    bucket_available: bool = False
    recorded_held_units: int | None = Field(default=None, ge=0)
    recorded_spent_units: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def consistent(self) -> "LedgerOperationsSnapshot":
        counts = self.recorded_held_units, self.recorded_spent_units
        if self.bucket_available:
            if self.request.budget_window is None or self.occupied_slots is None or None in counts:
                raise ValueError("available bucket requires exact window and counters")
        elif counts != (None, None):
            raise ValueError("missing bucket never means zero")
        return self


class PolicyScopeMetadata(StrictPolicyModel):
    epoch: int = Field(ge=0)
    disabled: bool
    policy_ref: PolicyDefinitionRef | None = None
    policy_state: (
        Literal["draft", "submitted", "changes_requested", "published", "recalled", "archived"]
        | None
    ) = None

    @model_validator(mode="after")
    def consistent(self) -> "PolicyScopeMetadata":
        if (self.policy_ref is None) != (self.policy_state is None):
            raise ValueError("pin metadata must be paired")
        if self.epoch == 0 and (self.disabled or self.policy_ref is not None):
            raise ValueError("uninitialized scope cannot have a pin or stop")
        if self.epoch > 0 and not self.disabled and self.policy_ref is None:
            raise ValueError("activated scope requires pin")
        if not self.disabled and self.policy_ref is not None and self.policy_state != "published":
            raise ValueError("active pin requires published metadata")
        return self


class PolicyOperationsView(StrictPolicyModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    organization_id: OpaqueId
    request: PolicyOperationsRequest
    scope: PolicyScopeMetadata | None
    ledger: LedgerOperationsSnapshot
    telemetry: OperationsTelemetryView = Field(default_factory=OperationsTelemetryView)
    accounting_semantics: Literal["recorded_ledger_not_actual_cost"] = (
        "recorded_ledger_not_actual_cost"
    )
    actual_cost: None = None

    @model_validator(mode="after")
    def consistent(self) -> "PolicyOperationsView":
        if (self.ledger.organization_id, self.ledger.request) != (
            self.organization_id,
            self.request,
        ):
            raise ValueError("wrong operational snapshot binding")
        return self
