"""Adapt the frozen HTTP envelope to FEAT-016's reducer command vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sketch2life.contracts.schemas.mobile_workflow import MobileWorkflowCommandV1


@dataclass(frozen=True, slots=True)
class RuntimeCommandEnvelope:
    command_id: str
    session_id: str
    expected_session_version: int
    actor_ref: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AdaptedMobileCommand:
    """Keep HTTP idempotency separate from the reducer's one command identifier."""

    runtime_envelope: RuntimeCommandEnvelope
    idempotency_key: str


def adapt_mobile_command(command: MobileWorkflowCommandV1) -> AdaptedMobileCommand:
    return AdaptedMobileCommand(
        runtime_envelope=RuntimeCommandEnvelope(
            command_id=command.request_id,
            session_id=command.session_id,
            expected_session_version=command.expected_session_version,
            actor_ref=command.actor_ref,
            created_at=command.created_at,
        ),
        idempotency_key=command.idempotency_key,
    )


__all__ = ["AdaptedMobileCommand", "RuntimeCommandEnvelope", "adapt_mobile_command"]
