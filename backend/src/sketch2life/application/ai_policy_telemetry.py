"""Validate source binding and expiry without inventing telemetry or live health."""

from datetime import datetime

from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_telemetry import (
    OperationsTelemetryObservation,
    OperationsTelemetryView,
)
from sketch2life.domain.ai_policy.model import PolicyError


def telemetry_view(
    raw: OperationsTelemetryObservation | None,
    organization_id: str,
    feature_scope: str,
    source: PolicyDefinitionRef | None,
    now: datetime,
) -> OperationsTelemetryView:
    try:
        if now.utcoffset() is None:
            raise ValueError("aware observation clock required")
        if raw is None:
            return OperationsTelemetryView()
        if source is None:
            raise ValueError("configured telemetry source required")
        source = PolicyDefinitionRef.model_validate(source.model_dump(mode="python"), strict=True)
        observation = OperationsTelemetryObservation.model_validate(
            raw.model_dump(mode="python"), strict=True
        )
        if (observation.organization_id, observation.feature_scope, observation.source_ref) != (
            organization_id,
            feature_scope,
            source,
        ) or observation.observed_at > now:
            raise ValueError("wrong telemetry binding or future observation")
        stale = observation.expires_at <= now
        return OperationsTelemetryView(
            availability="stale" if stale else "fresh",
            source_ref=source,
            evidence_kind=observation.evidence_kind,
            observed_at=observation.observed_at,
            expires_at=observation.expires_at,
            health_state=None if stale else observation.health_state,
            queued_jobs=None if stale else observation.queued_jobs,
            running_jobs=None if stale else observation.running_jobs,
        )
    except (ValueError, TypeError, AttributeError):
        raise PolicyError("AI_POLICY_OPERATIONS_UNAVAILABLE") from None
