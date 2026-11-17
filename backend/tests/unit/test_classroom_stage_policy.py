from __future__ import annotations

import pytest
from pydantic import ValidationError

from sketch2life.application.services.classroom_stage_policy import (
    STAGES,
    StageTransitionError,
    require_next_stage,
)
from sketch2life.contracts.schemas.be1_runtime import (
    CompleteSessionRequest,
    JoinRoomCodeRequest,
    StageAdvanceRequest,
)


@pytest.mark.parametrize("index", range(len(STAGES) - 1))
def test_stage_policy_accepts_only_the_next_ordered_stage(index: int) -> None:
    assert require_next_stage(STAGES[index], STAGES[index + 1]) == STAGES[index + 1]


@pytest.mark.parametrize(
    ("current", "requested"),
    [
        ("preparation", "explore_draw"),
        ("explore_draw", "preparation"),
        ("completion", "completion"),
        ("unknown", "join"),
    ],
)
def test_stage_policy_rejects_skip_rewind_and_terminal_repeat(current: str, requested: str) -> None:
    with pytest.raises(StageTransitionError):
        require_next_stage(current, requested)


def test_room_code_join_accepts_exact_six_ascii_digits_only() -> None:
    payload = JoinRoomCodeRequest(room_code="004206", device_key="d" * 24)
    assert payload.room_code == "004206"
    for invalid in ("4206", "1234567", "12ab56", "１２３４５６"):
        with pytest.raises(ValidationError):
            JoinRoomCodeRequest(room_code=invalid, device_key="d" * 24)


def test_unfinished_group_requires_explicit_saved_draft() -> None:
    with pytest.raises(ValidationError):
        StageAdvanceRequest(
            expected_stage_revision=4,
            target_stage="sharing",
            unfinished_group_ids=["group-1"],
        )
    accepted = StageAdvanceRequest(
        expected_stage_revision=4,
        target_stage="sharing",
        unfinished_group_ids=["group-1"],
        unfinished_group_disposition="save_draft",
    )
    assert accepted.unfinished_group_disposition == "save_draft"


def test_early_end_requires_one_of_the_confirmed_categories() -> None:
    with pytest.raises(ValidationError):
        CompleteSessionRequest(expected_stage_revision=8, outcome="ended_early")
    assert (
        CompleteSessionRequest(
            expected_stage_revision=8,
            outcome="ended_early",
            reason_category="technical",
        ).reason_category
        == "technical"
    )
    with pytest.raises(ValidationError):
        CompleteSessionRequest(
            expected_stage_revision=8,
            outcome="completed",
            reason_category="time",
        )
