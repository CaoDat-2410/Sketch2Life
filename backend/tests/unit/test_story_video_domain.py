"""FEAT-066 T-1a: the pure state machine of a Parent video request (SRS l.395, l.394, l.573)."""

from __future__ import annotations

import itertools

import pytest

from sketch2life.application.ports.story_run_lifecycle import PUBLIC_RUN_STATES
from sketch2life.domain.lesson_occurrences import projection as lesson_rules
from sketch2life.domain.story_video import model
from sketch2life.domain.story_video.model import (
    ADMISSION_REFUSALS,
    GenerationKind,
    GenerationState,
    InvalidGenerationTransition,
    can_transition,
    generation_kind_for,
    has_ready_output,
    is_playable,
    require_transition,
)

S = GenerationState
LEGAL = {
    (S.ADMISSION_PENDING, S.ACCEPTED),
    (S.ADMISSION_PENDING, S.ADMISSION_REJECTED),
    (S.ADMISSION_PENDING, S.FAILED),
    (S.ACCEPTED, S.QUEUED),
    (S.ACCEPTED, S.FAILED),
    (S.QUEUED, S.GENERATING),
    (S.QUEUED, S.FAILED),
    (S.GENERATING, S.TECHNICAL_VALIDATING),
    (S.GENERATING, S.FAILED),
    (S.TECHNICAL_VALIDATING, S.SAFETY_VALIDATING),
    (S.TECHNICAL_VALIDATING, S.FAILED),
    (S.SAFETY_VALIDATING, S.READY),
    (S.SAFETY_VALIDATING, S.SAFETY_BLOCKED),
    (S.SAFETY_VALIDATING, S.FAILED),
    (S.READY, S.REJECTED_BY_ADULT),
    (S.READY, S.SUPERSEDED),
}


def test_the_twelve_states_are_the_register_states() -> None:
    assert len(GenerationState) == 12
    assert {state.value for state in GenerationState} == {
        "ADMISSION_PENDING",
        "ADMISSION_REJECTED",
        "ACCEPTED",
        "QUEUED",
        "GENERATING",
        "TECHNICAL_VALIDATING",
        "SAFETY_VALIDATING",
        "READY",
        "SAFETY_BLOCKED",
        "FAILED",
        "REJECTED_BY_ADULT",
        "SUPERSEDED",
    }


@pytest.mark.parametrize(("current", "target"), list(itertools.product(S, S)))
def test_every_edge_is_either_legal_or_refused(current: S, target: S) -> None:
    allowed = (current, target) in LEGAL
    assert can_transition(current, target) is allowed
    if allowed:
        require_transition(current, target)
    else:
        with pytest.raises(InvalidGenerationTransition):
            require_transition(current, target)


def test_settled_states_have_no_outgoing_edge_except_a_ready_video() -> None:
    for state in model.SETTLED_STATES - {S.READY}:
        assert model.TRANSITIONS[state] == frozenset()
    assert model.TRANSITIONS[S.READY] == {S.REJECTED_BY_ADULT, S.SUPERSEDED}


def test_the_open_states_are_exactly_the_partial_unique_predicate() -> None:
    assert {
        S.ADMISSION_PENDING,
        S.ACCEPTED,
        S.QUEUED,
        S.GENERATING,
        S.TECHNICAL_VALIDATING,
        S.SAFETY_VALIDATING,
    } == model.OPEN_STATES
    assert model.OPEN_STATES - {S.ADMISSION_PENDING} == model.IN_FLIGHT_STATES
    assert {
        S.GENERATING,
        S.TECHNICAL_VALIDATING,
        S.SAFETY_VALIDATING,
    } == model.STARTED_STATES
    assert model.OPEN_STATES.isdisjoint(model.SETTLED_STATES)
    assert set(GenerationState) == model.OPEN_STATES | model.SETTLED_STATES


def test_every_mapped_run_state_is_a_public_run_state() -> None:
    assert set(model.RUN_STATE_FOR_GENERATION.values()) <= set(PUBLIC_RUN_STATES)
    assert set(PUBLIC_RUN_STATES) >= model.VIDEO_RUN_STATES
    assert model.RUN_STATE_FOR_GENERATION[S.ADMISSION_PENDING] == "VIDEO_ADMISSION_PENDING"
    # a refused intent returns the run to the script review (l.395)
    assert model.RUN_STATE_FOR_GENERATION[S.ADMISSION_REJECTED] == "SCRIPT_REVIEW"
    assert model.RUN_STATE_FOR_GENERATION[S.ACCEPTED] == "VIDEO_QUEUED"
    assert model.RUN_STATE_FOR_GENERATION[S.TECHNICAL_VALIDATING] == "VIDEO_SAFETY_VALIDATING"
    # SUPERSEDED belongs to no run state of its own
    assert S.SUPERSEDED not in model.RUN_STATE_FOR_GENERATION


def test_a_blocked_output_returns_the_adult_to_the_script_review() -> None:
    """V4-A SAFETY_BLOCKED exit (owner decision C11, SRS l.420, l.2197)."""

    assert model.RUN_STATE_FOR_GENERATION[S.SAFETY_BLOCKED] == "SCRIPT_REVIEW"
    assert model.RUN_JOB_STATE_FOR_GENERATION[S.SAFETY_BLOCKED] == "FAILED"
    # the run state stays a valid value for rows written before the exit (no migration, D6)
    assert "SAFETY_BLOCKED" in model.VIDEO_RUN_STATES
    assert "SAFETY_BLOCKED" in PUBLIC_RUN_STATES
    assert {"SCRIPT_REVIEW", "SAFETY_BLOCKED"} == model.REVIEWABLE_RUN_STATES
    # terminal: the mapping is never read as an expected state
    assert model.TRANSITIONS[S.SAFETY_BLOCKED] == frozenset()


def test_job_state_maps_follow_the_public_job_vocabulary() -> None:
    assert set(model.PUBLIC_JOB_STATE.values()) <= {
        "queued",
        "running",
        "succeeded",
        "failed_exhausted",
        "blocked_unsafe",
    }
    assert model.PUBLIC_JOB_STATE[S.READY] == "succeeded"
    assert model.PUBLIC_JOB_STATE[S.FAILED] == "failed_exhausted"
    assert model.PUBLIC_JOB_STATE[S.SAFETY_BLOCKED] == "blocked_unsafe"
    # an intent and a refused request are not jobs
    assert S.ADMISSION_PENDING not in model.PUBLIC_JOB_STATE
    assert S.ADMISSION_REJECTED not in model.PUBLIC_JOB_STATE
    assert set(model.RUN_JOB_STATE_FOR_GENERATION.values()) <= {
        "QUEUED",
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
    }


def test_the_cap_is_three_accepted_requests_and_the_kinds_follow_it() -> None:
    assert model.MAX_ACCEPTED_REQUESTS == 3
    assert generation_kind_for(0) is GenerationKind.INITIAL
    assert generation_kind_for(1) is GenerationKind.QUALITY_REGEN
    assert generation_kind_for(2) is GenerationKind.QUALITY_REGEN


def test_the_admission_refusals_have_stable_statuses() -> None:
    assert ADMISSION_REFUSALS == {
        "VIDEO_QUOTA_EXCEEDED": 409,
        "SUBSCRIPTION_RESTRICTED": 409,
        "AI_COST_LIMIT_REACHED": 503,
    }
    assert model.QUALITY_REASON_CODES == (
        "QUALITY_LOW",
        "NOT_MATCHING_STORY",
        "CONTENT_CONCERN",
        "OTHER",
    )


# ---------------------------------------------------------- the playback predicate (T-1c-fix)
_PASSED = {"technical": "PASSED", "consistency": "PASSED", "safety": "PASSED", "has_output": True}
_ALL_RUN_STATES = (
    "INPUT_PROCESSING",
    "PREPARATION_REVIEW",
    "SCRIPT_GENERATING",
    "SCRIPT_REVIEW",
    "VIDEO_ADMISSION_PENDING",
    "VIDEO_QUEUED",
    "VIDEO_GENERATING",
    "VIDEO_SAFETY_VALIDATING",
    "VIDEO_READY",
    "COMPLETED",
    "SAFETY_BLOCKED",
    "FAILED",
    "ABANDONED",
    "DELETE_PENDING",
    "DELETED",
)


@pytest.mark.parametrize("run_state", _ALL_RUN_STATES)
def test_is_playable_is_strict_by_default_and_replays_a_completed_run_with_the_flag(
    run_state: str,
) -> None:
    common = {"generation_state": "READY", **_PASSED}
    assert is_playable(run_state=run_state, **common) is (run_state == "VIDEO_READY")
    assert is_playable(run_state=run_state, allow_completed=False, **common) is (
        run_state == "VIDEO_READY"
    )
    assert is_playable(run_state=run_state, allow_completed=True, **common) is (
        run_state in {"VIDEO_READY", "COMPLETED"}
    )


@pytest.mark.parametrize(
    "change",
    [
        {"generation_state": "REJECTED_BY_ADULT"},
        {"generation_state": "SUPERSEDED"},
        {"generation_state": "FAILED"},
        {"generation_state": None},
        {"has_output": False},
        {"safety": "FAILED"},
        {"technical": "PENDING"},
        {"consistency": None},
    ],
)
def test_the_flag_never_relaxes_the_generation_or_the_validations(
    change: dict[str, object],
) -> None:
    arguments = {"generation_state": "READY", **_PASSED, **change}
    for run_state in ("VIDEO_READY", "COMPLETED"):
        assert not is_playable(run_state=run_state, allow_completed=True, **arguments)  # type: ignore[arg-type]


def test_the_replayable_states_and_the_run_state_agnostic_variant() -> None:
    assert {"VIDEO_READY", "COMPLETED"} == model.REPLAYABLE_RUN_STATES
    assert model.COMPLETED_RUN_STATE == "COMPLETED"
    # the Lesson side holds the literal (it imports no Story module): the two must not drift
    assert lesson_rules.RUN_STATE_COMPLETED == model.COMPLETED_RUN_STATE
    assert has_ready_output(generation_state="READY", **_PASSED)
    assert not has_ready_output(generation_state="REJECTED_BY_ADULT", **_PASSED)
