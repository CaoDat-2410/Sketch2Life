"""Closed source observations; fixture/runtime labels are not execution authority."""

from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef, StrictPolicyModel

HealthState = Literal["healthy", "degraded", "unavailable"]


class OperationsTelemetryObservation(StrictPolicyModel):
    organization_id: OpaqueId
    feature_scope: OpaqueId
    source_ref: PolicyDefinitionRef
    evidence_kind: Literal["fixture", "runtime"]
    observed_at: AwareDatetime
    expires_at: AwareDatetime
    health_state: HealthState | None = None
    queued_jobs: int | None = Field(default=None, ge=0)
    running_jobs: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def meaningful(self) -> "OperationsTelemetryObservation":
        if self.expires_at <= self.observed_at:
            raise ValueError("observation expiry must follow observation time")
        if (self.health_state, self.queued_jobs, self.running_jobs) == (None, None, None):
            raise ValueError("empty observation is not telemetry")
        return self


class OperationsTelemetryView(StrictPolicyModel):
    availability: Literal["unavailable", "fresh", "stale"] = "unavailable"
    source_ref: PolicyDefinitionRef | None = None
    evidence_kind: Literal["fixture", "runtime"] | None = None
    observed_at: AwareDatetime | None = None
    expires_at: AwareDatetime | None = None
    health_state: HealthState | None = None
    queued_jobs: int | None = Field(default=None, ge=0)
    running_jobs: int | None = Field(default=None, ge=0)
    semantics: Literal["reported_by_source_not_execution_authority"] = (
        "reported_by_source_not_execution_authority"
    )

    @model_validator(mode="after")
    def coherent(self) -> "OperationsTelemetryView":
        metadata = self.source_ref, self.evidence_kind, self.observed_at, self.expires_at
        values = self.health_state, self.queued_jobs, self.running_jobs
        if self.availability == "unavailable":
            if metadata != (None, None, None, None) or values != (None, None, None):
                raise ValueError("unavailable telemetry cannot invent values")
        else:
            if any(value is None for value in metadata):
                raise ValueError("available/stale telemetry requires provenance")
            assert self.expires_at is not None and self.observed_at is not None
            if self.expires_at <= self.observed_at:
                raise ValueError("invalid observation interval")
            if self.availability == "fresh" and values == (None, None, None):
                raise ValueError("fresh telemetry requires a value")
            if self.availability == "stale" and values != (None, None, None):
                raise ValueError("stale telemetry must suppress values")
        return self
