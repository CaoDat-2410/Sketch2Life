"""FEAT-093 Amendment C: the GPU adapters ask Modal to start their containers early."""

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


def test_the_renderer_and_preparation_spawn_a_content_free_warm_up() -> None:
    render, prepare = _Function(), _Function()

    ModalSceneRenderer(function=render).warm_up()
    ModalScenePreparation(function=prepare).warm_up()

    assert render.payloads == [{"warmup": True}] and prepare.payloads == [{"warmup": True}]


def test_a_warm_up_that_cannot_be_dispatched_is_ignored() -> None:
    ModalSceneRenderer(function=_Function(RuntimeError("x"))).warm_up()
    ModalScenePreparation(function=_Function(RuntimeError("x"))).warm_up()
