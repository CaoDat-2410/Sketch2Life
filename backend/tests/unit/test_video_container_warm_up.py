"""FEAT-093/FEAT-094: the video adapters ask Modal to start and fill the one video container early."""

from __future__ import annotations

from sketch2life.infrastructure.story_video.modal_scene_preparation import ModalScenePreparation
from sketch2life.infrastructure.story_video.modal_scene_renderer import ModalSceneRenderer


class _Function:
    def __init__(self, error: Exception | None = None):
        self.payloads: list[dict] = []
        self.error = error

    def spawn(self, payload):
        self.payloads.append(payload)
        if self.error is not None:
            raise self.error
        return object()


def test_preparation_spawns_a_content_free_warm_up() -> None:
    prepare = _Function()

    ModalScenePreparation(function=prepare).warm_up()

    assert prepare.payloads == [{"prepare_warmup": True}]


def test_a_warm_up_that_cannot_be_dispatched_is_ignored() -> None:
    ModalScenePreparation(function=_Function(RuntimeError("x"))).warm_up()


def test_the_renderer_primes_the_scene_prompts_within_the_worker_limits() -> None:
    render = _Function()

    ModalSceneRenderer(function=render).prime(["A turtle walks.", "x" * 2_000])

    assert render.payloads == [{"warmup": True, "prompts": ["A turtle walks.", "x" * 1_200]}]
    ModalSceneRenderer(function=_Function(RuntimeError("x"))).prime(["a"])
