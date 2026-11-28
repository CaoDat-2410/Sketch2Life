"""Pure state rules for the BE1-to-Story Teacher assignment transfer saga."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class TransferAction(StrEnum):
    REASSIGN = "REASSIGN"
    OFFBOARD = "OFFBOARD"


class TransferState(StrEnum):
    TRANSFER_PENDING = "TRANSFER_PENDING"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    COMPLETED = "COMPLETED"
    OFFBOARDED = "OFFBOARDED"
    COMPENSATED_CONFLICT = "COMPENSATED_CONFLICT"


TERMINAL_STATES = frozenset(
    {
        TransferState.COMPLETED,
        TransferState.OFFBOARDED,
        TransferState.COMPENSATED_CONFLICT,
    }
)

_TRANSITIONS = {
    TransferState.TRANSFER_PENDING: frozenset(
        {
            TransferState.RECONCILE_REQUIRED,
            TransferState.COMPLETED,
            TransferState.OFFBOARDED,
            TransferState.COMPENSATED_CONFLICT,
        }
    ),
    TransferState.RECONCILE_REQUIRED: frozenset(
        {
            TransferState.RECONCILE_REQUIRED,
            TransferState.COMPLETED,
            TransferState.OFFBOARDED,
            TransferState.COMPENSATED_CONFLICT,
        }
    ),
}


class TransferStateError(ValueError):
    """A transfer attempted a state change that the saga does not define."""


@dataclass(frozen=True, slots=True)
class TransferEnvelope:
    transfer_id: str
    organization_id: str
    class_id: str
    action: TransferAction
    principal_ref: str
    old_subject: str
    new_subject: str | None
    old_assignment_id: str
    new_assignment_id: str | None
    expected_revision: int
    fenced_revision: int
    operation_scope: str
    idempotency_key: str
    fingerprint: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TransferProgress:
    state: TransferState
    state_revision: int
    attempt_count: int
    last_failure_code: str | None
    story_receipt_ref: str | None
    updated_at: datetime
    finalized_at: datetime | None


def transition(
    current: TransferState,
    target: TransferState,
    *,
    state_revision: int,
    updated_at: datetime,
    previous_updated_at: datetime,
    attempt_count: int,
    previous_attempt_count: int,
) -> tuple[int, datetime, int]:
    """Validate the declared transition and return its next revision/time/attempt count."""
    if target not in _TRANSITIONS.get(current, frozenset()):
        raise TransferStateError(f"undeclared transfer transition: {current} -> {target}")
    if state_revision < 1 or attempt_count < previous_attempt_count:
        raise TransferStateError("transfer progress cannot move backwards")
    if updated_at < previous_updated_at:
        raise TransferStateError("transfer updated_at cannot move backwards")
    return state_revision + 1, updated_at, attempt_count


def replace_progress(
    progress: TransferProgress,
    *,
    target: TransferState,
    updated_at: datetime,
    failure_code: str | None = None,
    story_receipt_ref: str | None = None,
    finalized_at: datetime | None = None,
    count_attempt: bool = True,
) -> TransferProgress:
    """Build the next immutable progress value after checking the state machine."""
    attempts = progress.attempt_count + int(count_attempt)
    revision, updated, attempts = transition(
        progress.state,
        target,
        state_revision=progress.state_revision,
        updated_at=updated_at,
        previous_updated_at=progress.updated_at,
        attempt_count=attempts,
        previous_attempt_count=progress.attempt_count,
    )
    receipt = progress.story_receipt_ref
    if receipt is not None and story_receipt_ref not in {None, receipt}:
        raise TransferStateError("Story receipt reference is immutable once recorded")
    return replace(
        progress,
        state=target,
        state_revision=revision,
        attempt_count=attempts,
        last_failure_code=failure_code,
        story_receipt_ref=story_receipt_ref or receipt,
        updated_at=updated,
        finalized_at=finalized_at,
    )


def assert_same_envelope(before: TransferEnvelope, after: TransferEnvelope) -> None:
    """Reject mutation of the command envelope pinned by the first accepted request."""
    if before != after:
        raise TransferStateError("transfer envelope is immutable")


__all__ = [
    "TERMINAL_STATES",
    "TransferAction",
    "TransferEnvelope",
    "TransferProgress",
    "TransferState",
    "TransferStateError",
    "assert_same_envelope",
    "replace_progress",
    "transition",
]
