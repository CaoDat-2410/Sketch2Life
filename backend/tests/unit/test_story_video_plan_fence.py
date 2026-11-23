"""FEAT-066 goal v4 OPEN-A D8: the plan fence of the video repository, offline.

A Teacher run whose pin names a plan that is no longer the approved plan is fenced by two read-only
checks (``begin_intent`` and the worker-start steps of ``advance``). This module proves the rule
itself with a scripted session and a scripted read port: no port is no fence, a Parent run is never
fenced, and every missing fact (no occurrence pin, no plan id in the pin, no approved plan) means
"not superseded". The behaviour inside the real transactions is proven on PostgreSQL in
``tests/integration/story_teacher/test_teacher_plan_fence_postgres.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from sketch2life.application.ports.approved_plan_read import ApprovedPlanRef
from sketch2life.domain.story_video.model import public_failure_code
from sketch2life.infrastructure.lesson_occurrences.approved_plan_reader import SqlApprovedPlanReader
from sketch2life.infrastructure.story_video.repository import (
    PLAN_SUPERSEDED,
    SqlStoryVideoRepository,
)


class _Session:
    def __init__(self, pin: Any) -> None:
        self.pin = pin
        self.reads = 0

    def scalar(self, _statement: Any) -> Any:
        self.reads += 1
        return self.pin


class _Reader:
    def __init__(self, approved: ApprovedPlanRef | None) -> None:
        self.approved = approved
        self.asked: list[str] = []

    def approved_plan(self, occurrence_ref: str) -> ApprovedPlanRef | None:
        self.asked.append(occurrence_ref)
        return self.approved


def _run(**changes: Any) -> dict[str, Any]:
    run: dict[str, Any] = {
        "run_id": "run-1",
        "actor_scope_kind": "ORGANIZATION",
        "occurrence_ref": "occurrence-1",
        "current_input_revision": 1,
    }
    run.update(changes)
    return run


def _repository(pin: Any, approved: ApprovedPlanRef | None, *, port: bool = True) -> Any:
    session = _Session(pin)
    reader = _Reader(approved)
    repository = SqlStoryVideoRepository(
        session,  # type: ignore[arg-type]
        plan_read=reader if port else None,
    )
    return repository, session, reader


CURRENT = ApprovedPlanRef(plan_revision_id="plan-2", revision_no=2)


def test_a_run_pinned_to_another_plan_is_superseded_and_names_the_approved_number() -> None:
    repository, _, reader = _repository({"plan_revision_id": "plan-1"}, CURRENT)
    assert repository._superseded_plan_no(_run()) == 2
    assert reader.asked == ["occurrence-1"]


@pytest.mark.parametrize(
    "case",
    [
        "no_port",
        "parent_run",
        "no_occurrence_pin",
        "pin_without_plan_id",
        "pin_is_not_a_mapping",
        "no_approved_plan",
        "still_the_approved_plan",
    ],
)
def test_every_missing_fact_and_the_unchanged_plan_mean_no_fence(case: str) -> None:
    pin: Any = {"plan_revision_id": "plan-1"}
    approved: ApprovedPlanRef | None = CURRENT
    run = _run()
    port = True
    if case == "no_port":
        port = False
    elif case == "parent_run":
        run = _run(actor_scope_kind="PARENT_ACCOUNT")
    elif case == "no_occurrence_pin":
        run = _run(occurrence_ref=None)
    elif case == "pin_without_plan_id":
        pin = {"plan_hash": "x"}
    elif case == "pin_is_not_a_mapping":
        pin = None
    elif case == "no_approved_plan":
        approved = None
    else:
        pin = {"plan_revision_id": "plan-2"}
    repository, _, _ = _repository(pin, approved, port=port)
    assert repository._superseded_plan_no(run) is None


def test_a_bare_repository_reads_nothing_and_has_no_fence() -> None:
    repository, session, _ = _repository({"plan_revision_id": "plan-1"}, CURRENT, port=False)
    assert repository._superseded_plan_no(_run()) is None
    assert session.reads == 0


def test_the_stored_code_is_shown_to_a_client_as_a_technical_failure() -> None:
    assert PLAN_SUPERSEDED == "PLAN_SUPERSEDED"
    assert public_failure_code(PLAN_SUPERSEDED) == "VIDEO_TECHNICAL_FAILURE"


def test_the_reader_is_read_only_and_names_the_two_facts_of_the_approved_plan() -> None:
    seen: list[Any] = []

    class _Result:
        def one_or_none(self) -> Any:
            return ("plan-2", 2)

    class _ReadSession:
        def execute(self, statement: Any) -> _Result:
            seen.append(statement)
            return _Result()

    reader = SqlApprovedPlanReader(_ReadSession())  # type: ignore[arg-type]
    assert reader.approved_plan("occurrence-1") == ApprovedPlanRef("plan-2", 2)
    (statement,) = seen
    text = str(statement).lower()
    assert text.startswith("select") and "for update" not in text and "for share" not in text
