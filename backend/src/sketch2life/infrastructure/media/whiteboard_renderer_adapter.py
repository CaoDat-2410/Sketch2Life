"""Pipeline adapter for the validated whiteboard MVP renderer."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoPipelineError,
)
from sketch2life.application.services.whiteboard_video_pipeline import (
    RenderedWhiteboard,
    StrokeBatch,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1

from .whiteboard_mvp_renderer import (
    WhiteboardMvpRenderSpec,
    render_progressive_reveal,
)


class MvpWhiteboardRendererAdapter:
    """Adapt a resolved cutout artifact to the pipeline renderer port.

    Artifact lookup and output storage remain injected so this adapter does not
    expose local filesystem details through the HTTP contract.
    """

    def __init__(
        self,
        *,
        cutout_path_for: Callable[[str], str | Path],
        output_path_for: Callable[[str], str | Path],
        spec: WhiteboardMvpRenderSpec | None = None,
    ) -> None:
        self._cutout_path_for = cutout_path_for
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
            result = render_progressive_reveal(
                self._cutout_path_for(strokes.stroke_refs[0]),
                self._output_path_for(job.job_id),
                spec=self._spec,
            )
        except (OSError, RuntimeError, ValueError) as error:
            raise WhiteboardVideoPipelineError("RENDER_FAILED", retryable=True) from error

        return RenderedWhiteboard(
            source_hash=job.source_hash,
            render_ref=result.output_path,
        )


__all__ = ["MvpWhiteboardRendererAdapter"]
