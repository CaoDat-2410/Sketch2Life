"""Pipeline adapter for the source-preserving whiteboard renderer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoPipelineError,
)
from sketch2life.application.services.whiteboard_video_pipeline import (
    RenderedWhiteboard,
    StrokeBatch,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1

from .whiteboard_mvp_renderer import WhiteboardMvpRenderSpec, render_stroke_animation


class MvpWhiteboardRendererAdapter:
    """Adapt a resolved cutout artifact to the pipeline renderer port.

    Artifact lookup and output storage remain injected so this adapter does not
    expose local filesystem details through the HTTP contract.
    """

    def __init__(
        self,
        *,
        output_path_for: Callable[[str], str | Path],
        stroke_path_for: Callable[[str], str | Path] | None = None,
        cutout_path_for: Callable[[str], str | Path] | None = None,
        spec: WhiteboardMvpRenderSpec | None = None,
    ) -> None:
        resolver = stroke_path_for or cutout_path_for
        if resolver is None:
            raise ValueError("a stroke artifact resolver is required")
        self._stroke_path_for = resolver
        self._output_path_for = output_path_for
        self._spec = spec

    def render(
        self,
        job: WhiteboardVideoJobV1,
        strokes: StrokeBatch,
    ) -> RenderedWhiteboard:
        if not strokes.stroke_refs:
            raise WhiteboardVideoPipelineError("NO_STROKE_ARTIFACT", retryable=False)

        try:
            render_spec = self._spec or WhiteboardMvpRenderSpec()
            render_spec = replace(
                render_spec,
                duration_seconds=job.video_duration_seconds,
            )
            result = render_stroke_animation(
                self._stroke_path_for(strokes.stroke_refs[0]),
                self._output_path_for(job.job_id),
                spec=render_spec,
                motion_schedule=job.scene_motions,
                motion_durations_seconds=job.scene_durations_seconds,
            )
        except (OSError, RuntimeError, ValueError) as error:
            raise WhiteboardVideoPipelineError("RENDER_FAILED", retryable=True) from error

        return RenderedWhiteboard(
            source_hash=job.source_hash,
            render_ref=result.output_path,
        )


__all__ = ["MvpWhiteboardRendererAdapter"]
