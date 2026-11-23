"""Pure rules of the story review epoch (goal v4, T-1b-fix; SRS l.255, l.406, l.416, l.1728).

A story revision is confirmed by a review row. A video request consumes the latest review of the
latest revision; when that request ends without a usable video (the adult marked it unsuitable, the
deadline failed it, or the safety check blocked it) the review is *spent*. The adult may then keep
the current story and confirm it again: a new review row with the next epoch, or ask for a rewrite.

Two questions are kept apart on purpose:

* :func:`review_is_spent` asks about ONE review. It decides whether a re-confirmation is accepted
  and whether the run envelope asks the adult to confirm.
* :func:`revision_has_spent_video` asks about ALL reviews of one revision. It decides whether a
  rewrite is allowed from a confirmed revision. After a re-confirmation (a fresh, unspent review)
  the first answer is false and the second stays true, so the adult can still rewrite.

No database access and no SQL here: the repositories read the generation states and call these.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

# A generation in one of these states was accepted and gave no playable video.
# ``ADMISSION_REJECTED`` is not here: a refused admission never consumed the review
# (``uq_vg_review_consumed``).
SPENT_GENERATION_STATES: Final = frozenset({"REJECTED_BY_ADULT", "FAILED", "SAFETY_BLOCKED"})

# One review epoch per accepted request (SRS l.405: at most three).
MIN_REVIEW_EPOCH: Final = 1
MAX_REVIEW_EPOCH: Final = 3


def review_is_spent(generation_states_of_one_review: Iterable[str]) -> bool:
    """``True`` when a generation on this review ended without a usable video."""

    return any(state in SPENT_GENERATION_STATES for state in generation_states_of_one_review)


def revision_has_spent_video(generation_states_by_review: Iterable[Iterable[str]]) -> bool:
    """``True`` when any review of the revision is spent (the rewrite door, SRS l.416)."""

    return any(review_is_spent(states) for states in generation_states_by_review)


def next_review_epoch(latest_epoch: int) -> int:
    """The epoch of the next review of the same revision."""

    return latest_epoch + 1


def story_confirmation_required(
    *,
    run_state: str,
    story_status: str | None,
    latest_review_spent: bool,
    reviewable_run_states: frozenset[str] = frozenset({"SCRIPT_REVIEW"}),
) -> bool:
    """``True`` when the adult has to confirm the current story before a video can be requested.

    The run is at the script review and the latest revision is a ``DRAFT``, or it is ``CONFIRMED``
    and its latest review is spent. Anything else (no story yet, a confirmed story with an unspent
    review, a run past the review) is ``False``. ``reviewable_run_states`` is the one place the
    SAFETY_BLOCKED exit widens.
    """

    if run_state not in reviewable_run_states:
        return False
    if story_status == "DRAFT":
        return True
    return story_status == "CONFIRMED" and latest_review_spent


__all__ = [
    "MAX_REVIEW_EPOCH",
    "MIN_REVIEW_EPOCH",
    "SPENT_GENERATION_STATES",
    "next_review_epoch",
    "review_is_spent",
    "revision_has_spent_video",
    "story_confirmation_required",
]
