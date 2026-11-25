"""``VideoRenderPort`` backed by the Parent video pipeline (FEAT-093).

The fixture runner asks this port for the video of one accepted generation. The renderer reads the confirmed story
inputs through ``VideoSourceReaderPort``, runs the pipeline (timeline, scene preparation on C2, scenes on C1, narration,
captions, assembly, checks) and answers with the MP4 bytes, or with a safe failure code. Progress and cancel are
forwarded to optional callables so the worker process can project them into the job row.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from sketch2life.application.ports.story_video import VideoRenderRequest, VideoRenderResult
from sketch2life.application.video_pipeline.orchestrator import VideoPipeline
from sketch2life.application.video_pipeline.ports import (
    PipelineResult,
    VideoPipelineCancelled,
    VideoPipelineError,
    VideoSource,
)

VIDEO_MEDIA_TYPE = "video/mp4"
CANCELLED_CODE = "VIDEO_CANCELLED"
UNEXPECTED_CODE = "VIDEO_PIPELINE_UNEXPECTED_ERROR"
SOURCE_UNAVAILABLE_CODE = "VIDEO_SOURCE_UNAVAILABLE"


class VideoSourceReaderPort(Protocol):
    def read(self, request: VideoRenderRequest) -> VideoSource | None:
        """The confirmed story, subjects, activity and drawing of the run, or None when unavailable."""


ProgressCallback = Callable[[str, int | None, int], None]


class PipelineVideoRenderer:
    def __init__(
        self,
        *,
        pipeline: VideoPipeline,
        reader: VideoSourceReaderPort,
        on_progress: Callable[[VideoRenderRequest, str, int | None, int], None] | None = None,
        on_result: Callable[[VideoRenderRequest, PipelineResult], None] | None = None,
        is_cancelled: Callable[[VideoRenderRequest], bool] | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._reader = reader
        self._on_progress = on_progress
        self._on_result = on_result
        self._is_cancelled = is_cancelled

    def render(self, request: VideoRenderRequest) -> VideoRenderResult:
        source = self._reader.read(request)
        if source is None:
            return _failed(SOURCE_UNAVAILABLE_CODE)
        progress = (lambda stage, scene, count: self._on_progress(request, stage, scene, count)) if self._on_progress else None
        cancelled = (lambda: self._is_cancelled(request)) if self._is_cancelled else None
        try:
            result = self._pipeline.run(source, progress=progress, cancelled=cancelled)
        except VideoPipelineCancelled:
            return _failed(CANCELLED_CODE)
        except VideoPipelineError as error:
            return _failed(error.code)
        except Exception:  # noqa: BLE001 - never leak provider text into the job
            return _failed(UNEXPECTED_CODE)
        if self._on_result is not None:
            self._on_result(request, result)
        report = result.report
        return VideoRenderResult(
            content=result.video,
            media_type=VIDEO_MEDIA_TYPE,
            technical_passed=report.technical_ok,
            consistency_passed=report.consistency_ok,
            safety_passed=report.safety_ok,
            safety_finding_codes=report.finding_codes if not report.safety_ok else (),
        )


def _failed(code: str) -> VideoRenderResult:
    return VideoRenderResult(content=b"", media_type=VIDEO_MEDIA_TYPE, technical_passed=False, failure_code=code)


__all__ = ["PipelineVideoRenderer", "VideoSourceReaderPort"]
