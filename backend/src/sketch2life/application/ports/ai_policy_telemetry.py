"""Trusted scoped telemetry producer, not raw provider monitoring or job-table access."""

from typing import Protocol

from sketch2life.contracts.schemas.ai_policy_telemetry import OperationsTelemetryObservation


class OperationsTelemetryReader(Protocol):
    def snapshot(
        self, organization_id: str, feature_scope: str
    ) -> OperationsTelemetryObservation | None:
        """Bounded aggregate for exactly this scope; None means no observation.

        Called after current read authorization, outside own SQL transaction.
        Source profile is explicitly bound in server composition. Adopt health
        measurement/expiry policy, same-snapshot queued/running job semantics and
        safe scoped aggregate disclosure. Never derive queue depth from outbox
        side effects. Runtime adapter is not supplied by the fixture component.
        No raw logs/identity/prompt/media/endpoint/credentials in this contract.
        """
        ...
