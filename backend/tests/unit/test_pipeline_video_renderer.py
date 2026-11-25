"""FEAT-093: the render port runs the pipeline and maps outcomes to safe results."""

from __future__ import annotations

from sketch2life.application.ports.story_video import VideoRenderRequest
from sketch2life.application.video_pipeline.ports import (
    PipelineResult,
    ValidationReport,
    VideoPipelineCancelled,
    VideoPipelineError,
)
from sketch2life.infrastructure.story_video.pipeline_renderer import PipelineVideoRenderer

REQUEST = VideoRenderRequest("gen-1", "run-1", "rev-1", "a" * 64, 0, "job-1")


class _Pipeline:
    def __init__(self, outcome):
        self.outcome, self.sources = outcome, []

    def run(self, source, *, progress=None, cancelled=None):
        self.sources.append(source)
        if progress:
            progress("RENDERING", 2, 5)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class _Reader:
    def __init__(self, source="SOURCE"):
        self.source = source

    def read(self, request):
        return self.source


def _result(report=None):
    return PipelineResult(video=b"MP4", captions_vtt="WEBVTT", cues=(), plan=None, report=report or ValidationReport(),  # type: ignore[arg-type]
                          backgrounds={})


def test_a_finished_pipeline_returns_the_mp4_and_reports_progress_and_result() -> None:
    seen, results = [], []
    renderer = PipelineVideoRenderer(
        pipeline=_Pipeline(_result()), reader=_Reader(),  # type: ignore[arg-type]
        on_progress=lambda req, stage, scene, count: seen.append((req.generation_id, stage, scene, count)),
        on_result=lambda req, result: results.append(result.captions_vtt),
    )

    answer = renderer.render(REQUEST)

    assert answer.content == b"MP4" and answer.failure_code is None and answer.media_type == "video/mp4"
    assert seen == [("gen-1", "RENDERING", 2, 5)] and results == ["WEBVTT"]


def test_failures_and_cancel_become_safe_codes_without_content() -> None:
    for outcome, code in (
        (VideoPipelineError("VIDEO_SCENE_TIMEOUT"), "VIDEO_SCENE_TIMEOUT"),
        (VideoPipelineCancelled(), "VIDEO_CANCELLED"),
        (RuntimeError("secret provider text"), "VIDEO_PIPELINE_UNEXPECTED_ERROR"),
    ):
        answer = PipelineVideoRenderer(pipeline=_Pipeline(outcome), reader=_Reader()).render(REQUEST)  # type: ignore[arg-type]
        assert answer.failure_code == code and answer.content == b"" and not answer.technical_passed


def test_missing_source_and_failed_checks_are_reported() -> None:
    missing = PipelineVideoRenderer(pipeline=_Pipeline(_result()), reader=_Reader(None)).render(REQUEST)  # type: ignore[arg-type]
    assert missing.failure_code == "VIDEO_SOURCE_UNAVAILABLE"

    blocked = PipelineVideoRenderer(
        pipeline=_Pipeline(_result(ValidationReport(safety_ok=False, finding_codes=("X",)))), reader=_Reader()  # type: ignore[arg-type]
    ).render(REQUEST)
    assert not blocked.safety_passed and blocked.safety_finding_codes == ("X",)
