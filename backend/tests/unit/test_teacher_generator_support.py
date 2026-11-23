"""FEAT-066 goal v4 OPEN-A D4: may a composed story generator take a Teacher story?

``generator_supports_role`` is computed by the route and handed down as a boolean; the repository
never calls the generator. A generator without a ``supports_role`` attribute (every existing one)
keeps working, no generator composed keeps today's behaviour, and a generator that refuses the role
(or whose check fails) stops the start so a Teacher story is never sent to it.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind
from sketch2life.interfaces.http.routers.parent_story_inputs import generator_supports_role

TEACHER = RunActor(kind=RunActorKind.TEACHER, account_id="teacher-account")
PARENT = RunActor(kind=RunActorKind.PARENT, account_id="parent-account")


def _request(generator: Any = None, *, composed: bool = True) -> Any:
    state = SimpleNamespace()
    if composed:
        state.story_generator = generator
    return SimpleNamespace(app=SimpleNamespace(state=state))


class _Plain:
    def generate(self, worker_input: Any) -> Any:  # pragma: no cover - never called here
        raise AssertionError


class _Capable(_Plain):
    def __init__(self, answer: bool) -> None:
        self.answer = answer
        self.asked: list[str] = []

    def supports_role(self, role: str) -> bool:
        self.asked.append(role)
        return self.answer


class _Broken(_Plain):
    def supports_role(self, role: str) -> bool:
        raise RuntimeError("synthetic")


def test_no_generator_composed_keeps_todays_behaviour() -> None:
    assert generator_supports_role(_request(None), TEACHER) is True
    assert generator_supports_role(_request(composed=False), TEACHER) is True


@pytest.mark.parametrize("generator", [_Plain(), object(), SimpleNamespace(supports_role=None)])
def test_a_generator_without_the_capability_attribute_is_accepted(generator: Any) -> None:
    assert generator_supports_role(_request(generator), TEACHER) is True


def test_a_capable_generator_is_asked_for_the_teacher_role_and_its_answer_wins() -> None:
    yes, no = _Capable(True), _Capable(False)
    assert generator_supports_role(_request(yes), TEACHER) is True
    assert generator_supports_role(_request(no), TEACHER) is False
    assert yes.asked == ["TEACHER"] and no.asked == ["TEACHER"]


def test_a_failing_capability_check_counts_as_unsupported() -> None:
    assert generator_supports_role(_request(_Broken()), TEACHER) is False


def test_a_parent_is_never_checked() -> None:
    refusing = _Capable(False)
    assert generator_supports_role(_request(refusing), PARENT) is True
    assert refusing.asked == []
