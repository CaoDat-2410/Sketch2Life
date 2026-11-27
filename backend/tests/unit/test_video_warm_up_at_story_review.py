"""FEAT-094 S6: the video container starts when the Parent gets the story to review, not after they confirm it."""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.story_video.modal_video_warm_up import VideoWarmUp
from sketch2life.interfaces.http.routers import parent_ai


class _Function:
    def __init__(self, error: Exception | None = None) -> None:
        self.payloads: list[dict[str, Any]] = []
        self.error = error

    def spawn(self, payload: dict[str, Any]) -> None:
        self.payloads.append(payload)
        if self.error is not None:
            raise self.error


def test_the_warm_up_carries_no_data_and_is_sent_once_while_the_container_stays_up() -> None:
    clock = [1_000.0]
    function = _Function()
    warm_up = VideoWarmUp(function=function, clock=lambda: clock[0])

    assert warm_up.request() is True
    clock[0] += 200
    assert warm_up.request() is False
    clock[0] += 41  # the idle container is gone after five minutes
    assert warm_up.request() is True
    assert function.payloads == [{"prepare_warmup": True}] * 2


def test_the_warm_up_targets_the_function_that_prepares_and_renders() -> None:
    from sketch2life.infrastructure.story_video import modal_scene_renderer as renderer

    assert (VideoWarmUp.APP, VideoWarmUp.FUNCTION) == (renderer.APP_NAME, renderer.FUNCTION_NAME)


def test_a_warm_up_that_cannot_be_dispatched_is_silent() -> None:
    assert VideoWarmUp(function=_Function(RuntimeError("down")), clock=lambda: 1.0).request() is False


def test_the_warm_up_is_off_unless_switched_on() -> None:
    assert Settings.model_fields["story_video_warm_up"].default is False


class _Background:
    def __init__(self) -> None:
        self.tasks: list[Any] = []

    def add_task(self, task: Any) -> None:
        self.tasks.append(task)


@pytest.mark.parametrize(
    "switch, provider, adapters, expected",
    [
        (True, "modal_dev", "local_test", 1),
        (False, "modal_dev", "local_test", 0),
        (True, "disabled", "local_test", 0),
        (True, "modal_dev", "unconfigured", 0),
    ],
)
def test_a_gpu_is_started_only_when_the_video_flow_can_use_it(
    monkeypatch: pytest.MonkeyPatch, switch: bool, provider: str, adapters: str, expected: int
) -> None:
    settings = SimpleNamespace(story_video_warm_up=switch, ai_provider=provider, story_video_adapters=adapters)
    monkeypatch.setattr(parent_ai, "get_settings", lambda: settings)
    background = _Background()

    parent_ai._warm_up_video_container(background)

    assert len(background.tasks) == expected


def test_the_story_route_warms_the_container_after_the_story_is_stored() -> None:
    source = inspect.getsource(parent_ai.generate_story_revision)

    assert "background: BackgroundTasks" in source
    assert source.index("complete_generated_story(") < source.index("_warm_up_video_container(background)")
