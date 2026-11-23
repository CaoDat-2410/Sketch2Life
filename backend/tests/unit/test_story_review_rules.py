"""FEAT-066 goal v4 T-1b-fix: the pure rules of the story review epoch (SRS l.406, l.416, l.1728).

``review_is_spent`` answers for ONE review, ``revision_has_spent_video`` for all reviews of one
revision, and ``story_confirmation_required`` builds the additive envelope field. After a
re-confirmation (a fresh, unspent review) the two spent questions give different answers, which is
what keeps the rewrite available.
"""

from __future__ import annotations

import pytest

from sketch2life.application.services.story_review_rules import (
    MAX_REVIEW_EPOCH,
    MIN_REVIEW_EPOCH,
    SPENT_GENERATION_STATES,
    next_review_epoch,
    review_is_spent,
    revision_has_spent_video,
    story_confirmation_required,
)
from sketch2life.domain.story_video.model import MAX_ACCEPTED_REQUESTS, GenerationState


def test_the_spent_states_are_the_three_that_end_without_a_usable_video() -> None:
    assert {"REJECTED_BY_ADULT", "FAILED", "SAFETY_BLOCKED"} == set(SPENT_GENERATION_STATES)
    # every name is a real generation state, and ADMISSION_REJECTED never spends a review
    assert {str(state) for state in GenerationState} >= SPENT_GENERATION_STATES
    assert "ADMISSION_REJECTED" not in SPENT_GENERATION_STATES
    assert MIN_REVIEW_EPOCH == 1
    assert MAX_REVIEW_EPOCH == MAX_ACCEPTED_REQUESTS


@pytest.mark.parametrize(
    ("states", "spent"),
    [
        ([], False),
        (["ADMISSION_PENDING"], False),
        (["ADMISSION_REJECTED"], False),
        (["ACCEPTED"], False),
        (["GENERATING"], False),
        (["READY"], False),
        (["REJECTED_BY_ADULT"], True),
        (["FAILED"], True),
        (["SAFETY_BLOCKED"], True),
        (["ADMISSION_REJECTED", "FAILED"], True),
        (["ADMISSION_REJECTED", "ADMISSION_REJECTED"], False),
    ],
)
def test_review_is_spent_truth_table(states: list[str], spent: bool) -> None:
    assert review_is_spent(states) is spent
    assert review_is_spent(iter(states)) is spent


def test_a_re_confirmed_revision_has_an_unspent_latest_review_but_still_a_spent_video() -> None:
    first_review = ["REJECTED_BY_ADULT"]
    second_review: list[str] = []  # confirmed again, nothing requested yet
    assert review_is_spent(second_review) is False  # no second re-confirmation (D5)
    assert revision_has_spent_video([first_review, second_review]) is True  # the rewrite stays open


@pytest.mark.parametrize(
    ("by_review", "spent"),
    [
        ([], False),
        ([[]], False),
        ([["READY"]], False),
        ([["ADMISSION_REJECTED"]], False),
        ([["FAILED"]], True),
        ([["READY"], ["SAFETY_BLOCKED"]], True),
        ([["REJECTED_BY_ADULT"], ["REJECTED_BY_ADULT"], []], True),
    ],
)
def test_revision_has_spent_video_truth_table(by_review: list[list[str]], spent: bool) -> None:
    assert revision_has_spent_video(by_review) is spent


def test_the_next_epoch_adds_one() -> None:
    assert [next_review_epoch(value) for value in (1, 2)] == [2, 3]


@pytest.mark.parametrize(
    ("run_state", "story_status", "spent", "required"),
    [
        ("SCRIPT_REVIEW", "DRAFT", False, True),
        ("SCRIPT_REVIEW", "CONFIRMED", True, True),
        ("SCRIPT_REVIEW", "CONFIRMED", False, False),
        ("SCRIPT_REVIEW", "SUPERSEDED", True, False),
        ("SCRIPT_REVIEW", "GENERATING", False, False),
        ("SCRIPT_REVIEW", None, False, False),
        ("SCRIPT_GENERATING", "DRAFT", False, False),
        ("VIDEO_READY", "CONFIRMED", True, False),
        ("VIDEO_QUEUED", "CONFIRMED", False, False),
        ("SAFETY_BLOCKED", "CONFIRMED", True, False),  # widened by the SAFETY_BLOCKED exit task
        ("COMPLETED", "CONFIRMED", True, False),
    ],
)
def test_story_confirmation_required_truth_table(
    run_state: str, story_status: str | None, spent: bool, required: bool
) -> None:
    assert (
        story_confirmation_required(
            run_state=run_state, story_status=story_status, latest_review_spent=spent
        )
        is required
    )


def test_the_reviewable_run_states_are_the_one_place_the_blocked_exit_widens() -> None:
    kwargs = {"story_status": "CONFIRMED", "latest_review_spent": True}
    assert story_confirmation_required(run_state="SAFETY_BLOCKED", **kwargs) is False  # type: ignore[arg-type]
    assert (
        story_confirmation_required(
            run_state="SAFETY_BLOCKED",
            reviewable_run_states=frozenset({"SCRIPT_REVIEW", "SAFETY_BLOCKED"}),
            **kwargs,  # type: ignore[arg-type]
        )
        is True
    )
