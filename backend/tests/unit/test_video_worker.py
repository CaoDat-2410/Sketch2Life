"""FEAT-093: the worker advances runnable generations and survives a failing one."""

from __future__ import annotations

from types import SimpleNamespace

import sketch2life.infrastructure.story_video.video_worker as video_worker
from sketch2life.infrastructure.story_video.video_worker import VideoWorker


class _Session:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _Runner:
    def __init__(self):
        self.calls = []

    def run_to_end(self, generation_id):
        self.calls.append(generation_id)
        if generation_id == "bad":
            raise RuntimeError("provider text must not escape")


def test_every_runnable_generation_is_advanced_even_when_one_fails(monkeypatch) -> None:
    class _Repo:
        def __init__(self, session):
            pass

        def runnable_generations(self, limit):
            return [SimpleNamespace(generation_id=name) for name in ("a", "bad", "c")]

    monkeypatch.setattr(video_worker, "SqlStoryVideoRepository", _Repo)
    runner = _Runner()

    handled = VideoWorker(lambda: _Session(), runner).run_once()

    assert handled == 3 and runner.calls == ["a", "bad", "c"]


def test_the_renderer_setting_defaults_to_the_fixture() -> None:
    from sketch2life.infrastructure.config.settings import Settings

    assert Settings.model_fields["story_video_renderer"].default == "fixture"
