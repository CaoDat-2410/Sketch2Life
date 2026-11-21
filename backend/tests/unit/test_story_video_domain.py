"""FEAT-066 T-1a: the pure state machine of a Parent video request (SRS l.395, l.394, l.573)."""

from __future__ import annotations

import itertools

import pytest

from sketch2life.application.ports.story_run_lifecycle import PUBLIC_RUN_STATES
from sketch2life.domain.story_video import model
from sketch2life.domain.story_video.model import (
    ADMISSION_REFUSALS,
    GenerationKind,
    GenerationState,
    InvalidGenerationTransition,
    can_transition,
    generation_kind_for,
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
