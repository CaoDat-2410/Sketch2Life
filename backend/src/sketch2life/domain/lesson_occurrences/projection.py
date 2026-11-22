"""Framework-independent rules of the class projection confirmation (FEAT-066 goal v3, T-5a).

SRS l.396 (the output that passed safety and can be played claims the sample slot atomically; a
failed run before playback keeps the slot; deleting a run clears the pointer but keeps the claim),
l.552 (FR-T-13: after the first claim the slot never reopens), l.555 (FR-T-16: only the current
responsible Teacher may project; a short-lived authorization, no reusable capability for class
members), l.777 (``ClassProjectionConfirmationV1``), l.1449 and l.1661-1662 (the confirmation names
the audience and use; no confirmation, no projection token), OD-14 (the claim is the first
projection confirmation). Nothing here knows HTTP, SQL or a framework.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Final

PROJECTION_AUDIENCE: Final = "CLASS"
PROJECTION_USE: Final = "CLASS_PROJECTION"
CONTRACT_NAME: Final = "ClassProjectionConfirmationV1"
# The occurrence states a confirmation may start from; all hold a plan pointer (ck_occ_plan_state).
CONFIRMABLE_STATES: Final = frozenset({"APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"})
SLOT_AVAILABLE: Final = "AVAILABLE"
SLOT_CLAIMED: Final = "CLAIMED"
STATE_SAMPLE_USED: Final = "SAMPLE_USED"
# A plan that was approved at some time (a run stays pinned to it, SRS l.2697).
PIN_PLAN_STATES: Final = frozenset({"APPROVED", "SUPERSEDED"})
AUDIT_CONFIRM_DECISION: Final = f"{PROJECTION_AUDIENCE}/{PROJECTION_USE}"
AUDIT_CLAIM_DECISION: Final = "CLAIMED"

_EPOCH: Final = datetime(1970, 1, 1, tzinfo=UTC)
_MILLISECOND: Final = timedelta(milliseconds=1)


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def confirmed_ms(moment: datetime) -> int:
    """The confirmation time in whole milliseconds since the epoch, truncated (never rounded).

    The token carries this number and the stream compares it with the same function applied to the
    stored timestamp, so a microsecond difference never splits the two sides. Integer arithmetic
    only: a float would lose the last digits.
    """

    return (_aware(moment) - _EPOCH) // _MILLISECOND


def confirmation_covers(confirmed_at: datetime | None, ready_at: datetime | None) -> bool:
    """A confirmation covers a generation only when it was given after the generation was ready.

    The occurrence row stores the confirmation time and the confirming Teacher but no generation
    (DDL-A, REG l.352), so the generation is bound through time: a newer generation becomes ready
    later than any earlier confirmation and therefore needs its own (SRS l.777, l.1661). With no
    readiness time the confirmation cannot be shown to cover anything.
    """

    if confirmed_at is None or ready_at is None:
        return False
    return _aware(confirmed_at) >= _aware(ready_at)


class ClaimDecision(StrEnum):
    FIRST_CLAIM = "FIRST_CLAIM"
    SAME_RUN = "SAME_RUN"
    REFUSED = "REFUSED"


def decide_claim(*, slot_state: str, successful_run_ref: str | None, run_id: str) -> ClaimDecision:
    """The slot decision of a confirmation of ``run_id`` (OD-14, FR-T-13).

    ``AVAILABLE`` is claimed by this confirmation. ``CLAIMED`` by this run only refreshes or
    repeats. ``CLAIMED`` by another run, or with an empty pointer (a deleted run clears the pointer
    and keeps the claim, l.396), is refused: the slot never reopens.
    """

    if slot_state == SLOT_AVAILABLE:
        return ClaimDecision.FIRST_CLAIM
    if slot_state == SLOT_CLAIMED and successful_run_ref == run_id:
        return ClaimDecision.SAME_RUN
    return ClaimDecision.REFUSED


class WriteKind(StrEnum):
    NONE = "NONE"  # the stored confirmation already covers this run and generation
    REFRESH = "REFRESH"  # another Teacher or a newer generation: the pair is rewritten
    CLAIM = "CLAIM"


def decide_write(
    decision: ClaimDecision,
    *,
    confirmed_by: str | None,
    confirmed_at: datetime | None,
    caller_account: str,
    ready_at: datetime | None,
) -> WriteKind:
    """What a non-refused confirmation writes.

    A repeat by the SAME Teacher whose stored confirmation already covers the generation writes
    nothing (a double click with two keys never ends a playing token). Another Teacher, or a
    generation that became ready after the stored confirmation, rewrites the pair.
    """

    if decision is ClaimDecision.FIRST_CLAIM:
        return WriteKind.CLAIM
    same_teacher = confirmed_by is not None and confirmed_by == caller_account
    if (
        decision is ClaimDecision.SAME_RUN
        and same_teacher
        and confirmation_covers(confirmed_at, ready_at)
    ):
        return WriteKind.NONE
    return WriteKind.REFRESH


def pin_matches_plan(
    *,
    pin_plan_revision_id: str | None,
    pin_revision_no: int | None,
    pin_hash: str | None,
    plan_revision_id: str | None,
    plan_revision_no: int | None,
    plan_hash: str | None,
    plan_state: str | None,
) -> bool:
    """The run's plan pin names a plan revision of this occurrence that was approved at some time
    and its number and hash agree with that row (the pin is read from the CURRENT input
    revision)."""

    return (
        pin_plan_revision_id is not None
        and pin_plan_revision_id == plan_revision_id
        and pin_revision_no is not None
        and pin_revision_no == plan_revision_no
        and pin_hash is not None
        and pin_hash == plan_hash
        and plan_state in PIN_PLAN_STATES
    )


def request_fingerprint(*, expected_revision: int, run_id: str, generation_id: str) -> str:
    """SHA-256 of the exact request (replay equality, SRS l.1697)."""

    canonical = json.dumps(
        {
            "command": "projection-confirmation",
            "expected_revision": expected_revision,
            "run_id": run_id,
            "generation_id": generation_id,
            "audience": PROJECTION_AUDIENCE,
            "use": PROJECTION_USE,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ReceiptFacts:
    occurrence_id: str
    run_id: str
    generation_id: str
    confirmed_at: datetime
    confirmed_by_ref: str
    class_revision: int
    plan_revision_no: int
    plan_hash: str
    plan_is_current: bool
    occurrence_revision: int
    slot_state: str
    claimed_at: datetime | None
    slot_run_ref: str | None


def receipt_body(facts: ReceiptFacts) -> dict[str, Any]:
    """``ClassProjectionConfirmationV1`` (SRS l.777): refs and times only, no name, no media key,
    no token and no capability for class members."""

    return {
        "contract": CONTRACT_NAME,
        "occurrence_id": facts.occurrence_id,
        "run_id": facts.run_id,
        "generation_id": facts.generation_id,
        "audience": PROJECTION_AUDIENCE,
        "use": PROJECTION_USE,
        "confirmed_at": facts.confirmed_at,
        "confirmed_by_ref": facts.confirmed_by_ref,
        "assignment": {"class_revision": facts.class_revision},
        "plan": {
            "revision_no": facts.plan_revision_no,
            "plan_hash": facts.plan_hash,
            "is_current": facts.plan_is_current,
        },
        "occurrence_revision": facts.occurrence_revision,
        "sample_video": {
            "slot_state": facts.slot_state,
            "claimed_at": facts.claimed_at,
            "run_ref": facts.slot_run_ref,
        },
    }


__all__ = [
    "AUDIT_CLAIM_DECISION",
    "AUDIT_CONFIRM_DECISION",
    "CONFIRMABLE_STATES",
    "CONTRACT_NAME",
    "PIN_PLAN_STATES",
    "PROJECTION_AUDIENCE",
    "PROJECTION_USE",
    "SLOT_AVAILABLE",
    "SLOT_CLAIMED",
    "STATE_SAMPLE_USED",
    "ClaimDecision",
    "ReceiptFacts",
    "WriteKind",
    "confirmation_covers",
    "confirmed_ms",
    "decide_claim",
    "decide_write",
    "pin_matches_plan",
    "receipt_body",
    "request_fingerprint",
]
