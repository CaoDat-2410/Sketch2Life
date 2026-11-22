"""Framework-independent rules of the Teacher random-child selection (FEAT-066 goal v3, T-4b1).

SRS l.341 and l.345 (candidates and the equal-probability pick), l.346 and l.350 (a stale candidate
is reselected at most once; an empty set stops), l.348 (every read revalidates), l.349 (expiry and
resume are OPEN), l.352 (the Teacher confirms before a run exists), l.354 and BR-34 (metadata-only
evidence: no seed, no name), l.549 FR-T-10, l.1441 UC-05, l.1447-1448, AC-56. Nothing here
knows HTTP,
SQL or a framework; the pick takes an injected ``randbelow`` and the clock is a parameter.

Owner approval conditions applied here: the evidence of a draw is the opaque ref, the candidate
count and a hash of the sorted opaque candidate refs; the drawn index, the generator state and any
seed are never stored, hashed, logged or returned.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Final

from sketch2life.domain.lesson_occurrences.model import (
    TEACHER_ROLE,
    AccessOutcome,
    AssignmentFact,
)

POLICY_VERSION: Final = "teacher-sample-eligibility-v1"
ELIGIBILITY_BASIS: Final = "SYNTHETIC_DEV"
SYNTHETIC_ORIGIN: Final = "SYNTHETIC_DEV"

# l.2742: a child of 121-155 months takes no new run; 36 months is the lower bound of the profile.
MIN_AGE_MONTHS: Final = 36
MAX_AGE_MONTHS: Final = 120

# l.349 leaves timeout, expiry and resume OPEN: these are interim product values (OPEN-7).
OPEN_TTL: Final = timedelta(seconds=900)
CONFIRMED_TTL: Final = timedelta(seconds=900)

# The most draw rows (one DRAW, one stale RESELECT) an occurrence ever has. A product deviation that
# goes beyond l.346 (OPEN-3): the DDL admits draw numbers 1 and 2 only, so a value above 2 needs a
# migration; a value of 1 forbids the reselect.
DEFAULT_MAX_DRAWS: Final = 2
MAX_DRAWS_LIMIT: Final = 2

SELECTION_KINDS: Final = ("DRAW", "RESELECT", "REOFFER", "EMPTY")
STORED_STATES: Final = ("OPEN", "CONFIRMED", "CONSUMED", "EXPIRED", "STALE", "VOID", "EMPTY")
LIVE_STATES: Final = frozenset({"OPEN", "CONFIRMED"})
# Stored states that never change again and never carry child data: the only rows a read may answer
# 304 for (T4B1-IR-01). A live row's view state is computed at read time, so its ETag is not enough.
IMMUTABLE_STATES: Final = frozenset({"CONSUMED", "EXPIRED", "STALE", "VOID", "EMPTY"})
# The legal edges of the row state machine (the database trigger enforces the same table).
STATE_EDGES: Final = {
    "OPEN": frozenset({"CONFIRMED", "EXPIRED", "STALE", "VOID"}),
    "CONFIRMED": frozenset({"CONSUMED", "EXPIRED", "STALE", "VOID"}),
}

# The state a caller sees when no row is behind the answer (case h).
STATE_STOPPED: Final = "STOPPED"
OUTCOME_SELECTED: Final = "SELECTED"
OUTCOME_NONE: Final = "NO_ELIGIBLE_CHILD"

AUDIT_ACTIONS: Final = {
    "DRAW": "lesson.occurrence.child_selection.draw",
    "RESELECT": "lesson.occurrence.child_selection.reselect",
    "REOFFER": "lesson.occurrence.child_selection.reoffer",
    "EMPTY": "lesson.occurrence.child_selection.empty",
    "CONFIRM": "lesson.occurrence.child_selection.confirm",
}


@dataclass(frozen=True, slots=True)
class SelectionPolicy:
    """The tunable product values; the defaults are the ones the plan records as OPEN-3/OPEN-7."""

    max_draws: int = DEFAULT_MAX_DRAWS
    open_ttl: timedelta = OPEN_TTL
    confirmed_ttl: timedelta = CONFIRMED_TTL

    def __post_init__(self) -> None:
        if not 1 <= self.max_draws <= MAX_DRAWS_LIMIT:
            raise ValueError("max_draws must be 1 or 2 (a higher cap needs a migration)")
        if self.open_ttl <= timedelta(0) or self.confirmed_ttl <= timedelta(0):
            raise ValueError("expiry intervals must be positive")


def canonical_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def candidate_set_hash(
    *,
    organization_ref: str,
    class_ref: str,
    plan_revision_id: str,
    children: Sequence[str],
) -> str:
    """SHA-256 of the canonical JSON of the policy, scope and the sorted opaque profile refs.

    No age and no name is part of it. Sorting is by code point so the value does not depend on a
    database collation.
    """
    return canonical_hash(
        {
            "policy_version": POLICY_VERSION,
            "organization_ref": organization_ref,
            "class_ref": class_ref,
            "plan_revision_id": plan_revision_id,
            "children": sorted(children),
        }
    )


def selection_sha256(
    *,
    selection_id: str,
    occurrence_id: str,
    plan_revision_id: str,
    plan_hash: str,
    selected_child_ref: str,
    candidate_set_hash: str,
    policy_version: str,
) -> str:
    """The hash the Teacher confirms: exactly the offer that was shown (l.346)."""
    return canonical_hash(
        {
            "selection_id": selection_id,
            "occurrence_id": occurrence_id,
            "plan_revision_id": plan_revision_id,
            "plan_hash": plan_hash,
            "selected_child_ref": selected_child_ref,
            "candidate_set_hash": candidate_set_hash,
            "policy_version": policy_version,
        }
    )


def pick_child(candidates: Sequence[str], randbelow: Callable[[int], int]) -> str:
    """Equal probability over the code-point-sorted candidates (l.341, l.549, AC-56).

    The index is local to this call: it is never returned, stored or logged (l.354).
    """
    ordered = sorted(candidates)
    if not ordered:
        raise ValueError("no candidate to draw from")
    position = randbelow(len(ordered))
    if not 0 <= position < len(ordered):
        raise ValueError("the generator returned a value outside the candidate set")
    return ordered[position]


def candidate_age_ok(age_months: int) -> bool:
    return MIN_AGE_MONTHS <= age_months <= MAX_AGE_MONTHS


# ----------------------------------------------------------------------------- authorization
def decide_child_data(
    rows: Sequence[AssignmentFact],
    class_id: str,
    *,
    caller_account_ref: str,
    responsible_teacher_ref: str,
) -> AccessOutcome:
    """Access to the child data of an occurrence (FR-T-14; aligned with the T-7a2 ruling).

    The caller's rows are the active teacher-family rows in the occurrence's organization (empty
    when the caller is not a valid Teacher there). Nobody whose rows do not cover the class learns
    that it exists: the uniform 404. A covered caller needs an exact-class ``teacher`` row and has
    to be the responsible Teacher; an organization-wide ``teacher`` row, a ``guide`` and an
    ``observer`` get no child data (403), which is stricter than ``decide_write`` on purpose.
    """
    covering = [row for row in rows if row.class_id is None or row.class_id == class_id]
    if not covering:
        return AccessOutcome.NOT_FOUND
    if not any(row.role == TEACHER_ROLE and row.class_id == class_id for row in rows):
        return AccessOutcome.FORBIDDEN
    if caller_account_ref != responsible_teacher_ref:
        return AccessOutcome.FORBIDDEN
    return AccessOutcome.PROCEED


# ----------------------------------------------------------------------------- the D5 table
class Case(StrEnum):
    """The cases a to h of the plan's D5 table (the letters are the test names)."""

    A_RETURN_LIVE = "a"
    C_EMPTY_FIRST = "c"
    D_DRAW = "d"
    E_REOFFER = "e"
    F_RESELECT = "f"
    G_EMPTY = "g"
    H_STOPPED = "h"


@dataclass(frozen=True, slots=True)
class RowFacts:
    """What the decision needs from one stored row (no name, no age, nothing of the child)."""

    selection_id: str
    kind: str
    draw_no: int | None
    state: str
    child_ref: str | None
    plan_revision_id: str
    teacher_ref: str
    candidate_set_hash: str
    expires_at: datetime | None
    confirmation_expires_at: datetime | None


def is_past_due(row: RowFacts, now: datetime) -> bool:
    """An ``OPEN`` row expires at ``expires_at``, a ``CONFIRMED`` one at its own deadline."""
    if row.state == "OPEN":
        return row.expires_at is not None and now >= row.expires_at
    if row.state == "CONFIRMED":
        deadline = row.confirmation_expires_at
        return deadline is not None and now >= deadline
    return False


@dataclass(frozen=True, slots=True)
class Transition:
    selection_id: str
    new_state: str


@dataclass(frozen=True, slots=True)
class Decision:
    """The result of ``decide_next``: transitions to write first, then one action."""

    case: Case
    transitions: tuple[Transition, ...] = ()
    kind: str | None = None
    draw_no: int | None = None
    reuse_child: str | None = None
    pick: bool = False
    coalesce_with: str | None = None
    return_row: str | None = None


def sweep(
    live: RowFacts | None,
    *,
    current_plan_revision_id: str,
    caller_account_ref: str,
    now: datetime,
) -> tuple[Transition, ...]:
    """Steps 2 and 3 of D5: a past-due live row expires; a live row of another plan revision or
    another Teacher (N-3) becomes ``VOID``."""
    if live is None:
        return ()
    if is_past_due(live, now):
        return (Transition(live.selection_id, "EXPIRED"),)
    if live.plan_revision_id != current_plan_revision_id or live.teacher_ref != caller_account_ref:
        return (Transition(live.selection_id, "VOID"),)
    return ()


def decide_next(
    *,
    live: RowFacts | None,
    anchor: RowFacts | None,
    latest: RowFacts | None,
    candidates: Sequence[str],
    candidate_hash: str,
    current_plan_revision_id: str,
    caller_account_ref: str,
    now: datetime,
    policy: SelectionPolicy,
) -> Decision:
    """The total state machine of a selection command (D5, cases a to h).

    ``live`` is the occurrence's only ``OPEN``/``CONFIRMED`` row, ``anchor`` the latest ``DRAW`` or
    ``RESELECT`` row (any state) and ``latest`` the newest row of any kind. The candidate set is the
    current one. Every combination of the inputs lands in exactly one case, and the returned
    ``transitions`` are written before the action.
    """
    candidate_set = frozenset(candidates)
    transitions = list(
        sweep(
            live,
            current_plan_revision_id=current_plan_revision_id,
            caller_account_ref=caller_account_ref,
            now=now,
        )
    )
    # After the sweep a surviving live row is current, the caller's and not past due.
    survivor = live if live is not None and not transitions else None
    if survivor is not None:
        if survivor.child_ref in candidate_set:
            return Decision(
                Case.A_RETURN_LIVE, tuple(transitions), return_row=survivor.selection_id
            )
        transitions.append(Transition(survivor.selection_id, "STALE"))
    found = tuple(transitions)

    if anchor is None:
        if not candidate_set:
            return _empty(Case.C_EMPTY_FIRST, found, latest, candidate_hash)
        return Decision(Case.D_DRAW, found, kind="DRAW", draw_no=1, pick=True)
    if anchor.child_ref in candidate_set:
        assert anchor.draw_no is not None
        return Decision(
            Case.E_REOFFER,
            found,
            kind="REOFFER",
            draw_no=anchor.draw_no,
            reuse_child=anchor.child_ref,
        )
    assert anchor.draw_no is not None
    if anchor.draw_no >= policy.max_draws:
        return Decision(Case.H_STOPPED, found)
    if not candidate_set:
        return _empty(Case.G_EMPTY, found, latest, candidate_hash)
    return Decision(Case.F_RESELECT, found, kind="RESELECT", draw_no=anchor.draw_no + 1, pick=True)


def _empty(
    case: Case, transitions: tuple[Transition, ...], latest: RowFacts | None, candidate_hash: str
) -> Decision:
    """A new ``EMPTY`` row, unless the newest row already is an ``EMPTY`` of the same set."""
    if (
        latest is not None
        and latest.kind == "EMPTY"
        and latest.candidate_set_hash == candidate_hash
    ):
        return Decision(case, transitions, kind="EMPTY", coalesce_with=latest.selection_id)
    return Decision(case, transitions, kind="EMPTY")


def reselect_available(draw_rows: int, policy: SelectionPolicy) -> bool:
    """True while a stale offer can still be replaced: at least one draw row, below the cap."""
    return 1 <= draw_rows < policy.max_draws


def view_state(row: RowFacts, *, now: datetime, child_is_eligible: bool) -> str:
    """The state a read reports: stored, or computed for a live row (l.348). Writes nothing."""
    if row.state in LIVE_STATES:
        if is_past_due(row, now):
            return "EXPIRED"
        if not child_is_eligible:
            return "STALE"
    return row.state


def etag_for_revision(revision: int) -> str:
    """Strong ETag of a selection: the quoted stored revision (the ``If-Match`` of the confirm)."""
    return f'"{revision}"'


def if_none_match_matches(header: str | None, revision: int) -> bool:
    if header is None:
        return False
    current = etag_for_revision(revision)
    return any(token.strip() in {current, "*"} for token in header.split(","))


__all__ = [
    "AUDIT_ACTIONS",
    "CONFIRMED_TTL",
    "DEFAULT_MAX_DRAWS",
    "ELIGIBILITY_BASIS",
    "IMMUTABLE_STATES",
    "LIVE_STATES",
    "MAX_AGE_MONTHS",
    "MAX_DRAWS_LIMIT",
    "MIN_AGE_MONTHS",
    "OPEN_TTL",
    "OUTCOME_NONE",
    "OUTCOME_SELECTED",
    "POLICY_VERSION",
    "SELECTION_KINDS",
    "STATE_EDGES",
    "STATE_STOPPED",
    "STORED_STATES",
    "SYNTHETIC_ORIGIN",
    "Case",
    "Decision",
    "RowFacts",
    "SelectionPolicy",
    "Transition",
    "candidate_age_ok",
    "candidate_set_hash",
    "canonical_hash",
    "decide_child_data",
    "decide_next",
    "etag_for_revision",
    "if_none_match_matches",
    "is_past_due",
    "pick_child",
    "reselect_available",
    "selection_sha256",
    "sweep",
    "view_state",
]
