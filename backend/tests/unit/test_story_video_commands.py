"""FEAT-066 T-1b: ``video-unsuitable`` and ``complete`` without a database (SRS l.1671-1672).

The service guard, the legal and illegal edges, the pure checks of the repository (state first,
then revision, then the current ready generation), the fingerprints and the receipt operations.
Behaviour against PostgreSQL lives in the story_video integration module
``test_video_commands_postgres.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_video import RunCommandResult, StoryVideoRepository
from sketch2life.application.services.story_run_video import StoryVideoCommandService
from sketch2life.domain.story_video.model import (
    MAX_ACCEPTED_REQUESTS,
    QUALITY_REASON_CODES,
    RUN_STATE_FOR_GENERATION,
    SETTLED_STATES,
    TRANSITIONS,
    UNSUITABLE_REASON_CODES,
    VIDEO_READY_RUN_STATE,
    GenerationState,
    can_transition,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.repository import (
    COMPLETE_OPERATION,
    UNSUITABLE_OPERATION,
    SqlStoryVideoRepository,
    _command_fingerprint,
)

PRINCIPAL = VerifiedPrincipal("adult-1", "issuer-1", frozenset())
RUN_ID = "22222222-2222-4222-8222-222222222222"
GEN_ID = "33333333-3333-4333-8333-333333333333"


class _Repository:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def mark_unsuitable(self, **kwargs: Any) -> RunCommandResult:
        self.calls.append(("mark_unsuitable", kwargs))
        return RunCommandResult(kwargs["run_id"], False)

    def complete_run(self, **kwargs: Any) -> RunCommandResult:
        self.calls.append(("complete_run", kwargs))
        return RunCommandResult(kwargs["run_id"], False)


def _service() -> tuple[StoryVideoCommandService, _Repository]:
    repository = _Repository()
    return StoryVideoCommandService(repository), repository  # type: ignore[arg-type]


# ------------------------------------------------------------------------- the service
@pytest.mark.parametrize("reason", sorted(UNSUITABLE_REASON_CODES))
def test_every_safe_reason_is_forwarded_with_the_whole_request(reason: str) -> None:
    service, repository = _service()
    result = service.mark_unsuitable(
        principal=PRINCIPAL,
        run_id=RUN_ID,
        expected_revision=7,
        generation_id=GEN_ID,
        reason_code=reason,
        idempotency_key="key-1",
    )
    assert result == RunCommandResult(RUN_ID, False)
    assert repository.calls == [
        (
            "mark_unsuitable",
            {
                "principal": PRINCIPAL,
                "run_id": RUN_ID,
                "expected_revision": 7,
                "generation_id": GEN_ID,
                "reason_code": reason,
                "idempotency_key": "key-1",
            },
        )
    ]


@pytest.mark.parametrize("reason", ["", "quality_low", "TOO_BAD", "QUALITY_LOW ", "free text here"])
def test_a_reason_outside_the_closed_set_is_refused_before_the_repository(reason: str) -> None:
    service, repository = _service()
    with pytest.raises(ParentStoryRunError) as raised:
        service.mark_unsuitable(
            principal=PRINCIPAL,
            run_id=RUN_ID,
            expected_revision=7,
            generation_id=GEN_ID,
            reason_code=reason,
            idempotency_key="key-1",
        )
    assert raised.value.status_code == 400 and raised.value.code == "INVALID_REQUEST"
    assert raised.value.field_errors == [{"field": "reason_code", "code": "INVALID_VALUE"}]
    assert repository.calls == []


def test_complete_forwards_the_revision_and_the_key() -> None:
    service, repository = _service()
    service.complete(
        principal=PRINCIPAL, run_id=RUN_ID, expected_revision=4, idempotency_key="key-2"
    )
    assert repository.calls == [
        (
            "complete_run",
            {
                "principal": PRINCIPAL,
                "run_id": RUN_ID,
                "expected_revision": 4,
                "idempotency_key": "key-2",
            },
        )
    ]


def test_a_repository_refusal_passes_through_unchanged() -> None:
    error = ParentStoryRunError(409, "STALE_REVISION", current_version=9)

    class Refusing(_Repository):
        def complete_run(self, **kwargs: Any) -> RunCommandResult:
            raise error

    service = StoryVideoCommandService(Refusing())  # type: ignore[arg-type]
    with pytest.raises(ParentStoryRunError) as raised:
        service.complete(
            principal=PRINCIPAL, run_id=RUN_ID, expected_revision=1, idempotency_key="key-2"
        )
    assert raised.value is error


def test_the_repository_port_declares_both_commands() -> None:
    for name in ("mark_unsuitable", "complete_run"):
        assert callable(getattr(StoryVideoRepository, name))
        assert callable(getattr(SqlStoryVideoRepository, name))


# ------------------------------------------------------------------------- the state machine
def test_the_reason_set_is_the_closed_quality_set_and_never_free_text() -> None:
    assert UNSUITABLE_REASON_CODES == QUALITY_REASON_CODES
    assert set(UNSUITABLE_REASON_CODES) == {
        "QUALITY_LOW",
        "NOT_MATCHING_STORY",
        "CONTENT_CONCERN",
        "OTHER",
    }
    assert VIDEO_READY_RUN_STATE == "VIDEO_READY"


def test_a_ready_video_is_rejected_by_the_adult_and_only_a_ready_one() -> None:
    legal = {
        state
        for state in GenerationState
        if can_transition(state, GenerationState.REJECTED_BY_ADULT)
    }
    assert legal == {GenerationState.READY}
    assert GenerationState.REJECTED_BY_ADULT in TRANSITIONS[GenerationState.READY]
    assert TRANSITIONS[GenerationState.REJECTED_BY_ADULT] == frozenset()
    assert GenerationState.REJECTED_BY_ADULT in SETTLED_STATES
    assert RUN_STATE_FOR_GENERATION[GenerationState.REJECTED_BY_ADULT] == "SCRIPT_REVIEW"
    assert RUN_STATE_FOR_GENERATION[GenerationState.READY] == VIDEO_READY_RUN_STATE


def test_complete_leaves_the_generation_ready_so_no_generation_edge_is_used() -> None:
    # COMPLETED is a run state only: the SRS says it is not a video approval (l.1672).
    assert "COMPLETED" not in RUN_STATE_FOR_GENERATION.values()
    assert GenerationState.READY in TRANSITIONS and TRANSITIONS[GenerationState.READY] == frozenset(
        {GenerationState.REJECTED_BY_ADULT, GenerationState.SUPERSEDED}
    )


def test_the_regeneration_cap_is_the_first_request_and_two_regenerations() -> None:
    assert MAX_ACCEPTED_REQUESTS == 3


# ------------------------------------------------------------------------- the repository checks
_RUN_STATES = (
    "INPUT_PROCESSING",
    "INPUT_REVIEW",
    "SUBJECT_REVIEW",
    "PREPARATION_REVIEW",
    "SCRIPT_GENERATING",
    "SCRIPT_GENERATION_UNKNOWN",
    "SCRIPT_REVIEW",
    "VIDEO_ADMISSION_PENDING",
    "VIDEO_QUEUED",
    "VIDEO_GENERATING",
    "VIDEO_SAFETY_VALIDATING",
    "SAFETY_BLOCKED",
    "COMPLETED",
    "FAILED",
    "ABANDONED",
    "DELETE_PENDING",
    "DELETED",
)


@pytest.mark.parametrize("state", _RUN_STATES)
def test_every_state_but_video_ready_refuses_both_commands(state: str) -> None:
    with pytest.raises(ParentStoryRunError) as raised:
        SqlStoryVideoRepository._require_video_ready({"run_state": state, "revision": 5}, 5)
    assert raised.value.status_code == 409 and raised.value.code == "INVALID_STATE_TRANSITION"


def test_the_state_is_checked_before_the_revision() -> None:
    with pytest.raises(ParentStoryRunError) as raised:
        SqlStoryVideoRepository._require_video_ready({"run_state": "COMPLETED", "revision": 9}, 1)
    assert raised.value.code == "INVALID_STATE_TRANSITION"


def test_a_stale_revision_names_the_current_one() -> None:
    with pytest.raises(ParentStoryRunError) as raised:
        SqlStoryVideoRepository._require_video_ready({"run_state": "VIDEO_READY", "revision": 9}, 8)
    assert raised.value.status_code == 409 and raised.value.code == "STALE_REVISION"
    assert raised.value.current_version == 9


def test_the_current_revision_is_returned() -> None:
    assert (
        SqlStoryVideoRepository._require_video_ready({"run_state": "VIDEO_READY", "revision": 9}, 9)
        == 9
    )


class _NoSession:
    def execute(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("a pointer mismatch must not read the database")


@pytest.mark.parametrize("pointer", [None, "44444444-4444-4444-8444-444444444444"])
def test_a_generation_that_is_not_the_current_one_is_stale_without_a_read(
    pointer: str | None,
) -> None:
    repository = SqlStoryVideoRepository(_NoSession())  # type: ignore[arg-type]
    run = {"run_id": RUN_ID, "revision": 6, "current_video_generation_id": pointer}
    with pytest.raises(ParentStoryRunError) as raised:
        repository._current_ready_generation(run, GEN_ID)  # type: ignore[arg-type]
    assert raised.value.status_code == 409 and raised.value.code == "STALE_REVISION"
    assert raised.value.current_version == 6


# ------------------------------------------------------------------------- fingerprints, receipts
def test_the_fingerprint_depends_on_every_field_and_not_on_their_order() -> None:
    base = _command_fingerprint(
        run_id=RUN_ID, expected_revision=7, generation_id=GEN_ID, reason_code="QUALITY_LOW"
    )
    assert len(base) == 64
    assert base == _command_fingerprint(
        reason_code="QUALITY_LOW", generation_id=GEN_ID, expected_revision=7, run_id=RUN_ID
    )
    for change in (
        {"run_id": GEN_ID},
        {"expected_revision": 8},
        {"generation_id": RUN_ID},
        {"reason_code": "OTHER"},
    ):
        fields: dict[str, Any] = {
            "run_id": RUN_ID,
            "expected_revision": 7,
            "generation_id": GEN_ID,
            "reason_code": "QUALITY_LOW",
        }
        fields.update(change)
        assert _command_fingerprint(**fields) != base
    assert _command_fingerprint(run_id=RUN_ID, expected_revision=7) != base


def test_the_two_commands_use_receipt_operations_the_table_already_allows() -> None:
    assert UNSUITABLE_OPERATION == "MARK_VIDEO_UNSUITABLE"
    assert COMPLETE_OPERATION == "COMPLETE_RUN"
    check = next(
        str(constraint.sqltext)
        for constraint in story_tables.story_command_receipts.constraints
        if getattr(constraint, "name", None) == "ck_story_receipt_operation"
    )
    assert f"'{UNSUITABLE_OPERATION}'" in check and f"'{COMPLETE_OPERATION}'" in check
