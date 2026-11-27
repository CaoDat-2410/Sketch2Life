"""FEAT-098 S2: scene pictures are prepared and the renderer loaded while the adult reads the script."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from test_video_pipeline_orchestrator import _learning_source, _pipeline, _Prep, _source

from sketch2life.application.video_pipeline.orchestrator import prepare_ahead
from sketch2life.application.video_pipeline.ports import VideoPipelineError
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.story_video.modal_scene_preparation import ModalScenePreparation
from sketch2life.infrastructure.story_video.prepare_ahead import VideoPrepareAhead


class _Ahead(_Prep):
    def __init__(self) -> None:
        super().__init__()
        self.ahead: list[Any] = []

    def prepare_ahead(self, job):
        self.ahead.append(job)


class _Primed:
    def __init__(self) -> None:
        self.prompts: list[list[str]] = []

    def prime(self, prompts):
        self.prompts.append(prompts)


def test_the_pictures_asked_for_ahead_are_exactly_the_ones_the_video_asks_for_later() -> None:
    ahead, renderer = _Ahead(), _Primed()
    later: list[Any] = []

    class _Seen(_Prep):
        def prepare(self, job):
            later.append(job)
            return super().prepare(job)

    sent = prepare_ahead(_learning_source(), ahead, renderer)
    pipeline, _ = _pipeline(prep=_Seen())
    pipeline.run(_learning_source())

    assert sent == 5 and ahead.ahead == later
    assert renderer.prompts == [[job.scene.visual_prompt for job in later]]


def test_a_story_without_a_learning_script_is_not_prepared_ahead() -> None:
    ahead, renderer = _Ahead(), _Primed()

    assert prepare_ahead(_source(), ahead, renderer) == 0
    assert ahead.ahead == [] and renderer.prompts == []


class _Reader:
    def __init__(self, source: Any) -> None:
        self.source = source
        self.requests: list[Any] = []

    def read(self, request):
        self.requests.append(request)
        return self.source


def test_a_revision_is_prepared_once_and_failures_stay_silent() -> None:
    ahead, renderer = _Ahead(), _Primed()
    reader = _Reader(_learning_source())
    service = VideoPrepareAhead(reader, ahead, renderer)

    assert service.request("run-1", "rev-1") is True
    assert service.request("run-1", "rev-1") is False
    assert len(ahead.ahead) == 5
    assert (reader.requests[0].run_id, reader.requests[0].story_revision_id) == ("run-1", "rev-1")

    class _Down(_Ahead):
        def prepare_ahead(self, job):
            raise VideoPipelineError("VIDEO_SCENE_PREPARE_DISPATCH_UNKNOWN")

    assert VideoPrepareAhead(reader, _Down(), renderer).request("run-1", "rev-2") is False
    assert VideoPrepareAhead(_Reader(None), ahead, renderer).request("run-1", "rev-3") is False


def test_a_revision_that_could_not_be_read_may_be_tried_again() -> None:
    reader = _Reader(None)
    service = VideoPrepareAhead(reader, _Ahead(), _Primed())

    service.request("run-1", "rev-1")
    reader.source = _learning_source()

    assert service.request("run-1", "rev-1") is True


def test_the_ahead_call_sends_the_job_and_does_not_wait_for_it() -> None:
    sent: list[Any] = []

    class _Function:
        def spawn(self, payload):
            sent.append(payload)
            return SimpleNamespace(get=lambda **_: (_ for _ in ()).throw(AssertionError("waited")))

    class _Batch:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def put_file(self, *_):
            return None

    jobs: list[Any] = []

    class _Seen(_Prep):
        def prepare(self, job):
            jobs.append(job)
            return super().prepare(job)

    pipeline, _ = _pipeline(prep=_Seen())
    pipeline.run(_learning_source())
    adapter = ModalScenePreparation(volume=SimpleNamespace(batch_upload=_Batch), function=_Function())

    adapter.prepare_ahead(jobs[0])

    assert [payload["workload"] for payload in sent] == ["video.scene.prepare"]


def test_preparing_ahead_is_off_unless_switched_on() -> None:
    assert Settings.model_fields["story_video_prepare_ahead"].default is False
