"""Backend-only AI-policy emergency command, NOT another CMD-48 action or public API."""

from typing import Literal

from pydantic import Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex, ShortText
from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel


class EmergencyStopCommand(StrictPolicyModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    client_request_id: OpaqueId
    feature_scope: OpaqueId
    expected_epoch: int = Field(ge=0)
    reason: ShortText

    @model_validator(mode="after")
    def nonblank_reason(self) -> "EmergencyStopCommand":
        if not self.reason.strip():
            raise ValueError("reason required")
        return self


class EmergencyStopResult(StrictPolicyModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    organization_id: OpaqueId
    feature_scope: OpaqueId
    epoch: int = Field(ge=1)
    disabled: Literal[True]
    record_id: OpaqueId | None
    version: int | None = Field(ge=1)
    hash: Sha256Hex | None
    replayed: bool = False

    @model_validator(mode="after")
    def complete_pin(self) -> "EmergencyStopResult":
        if len({value is None for value in (self.record_id, self.version, self.hash)}) != 1:
            raise ValueError("pin all present or all absent")
        if type(self.disabled) is not bool:
            raise ValueError("disabled must be true boolean")
        return self
