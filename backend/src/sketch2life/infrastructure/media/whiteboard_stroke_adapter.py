"""Pipeline adapter for mask validation and deterministic stroke extraction."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoPipelineError,
)
from sketch2life.application.services.whiteboard_video_pipeline import (
    MaskBatch,
    StrokeBatch,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1

from .whiteboard_mask_validation import validate_mask_file
from .whiteboard_stroke_extraction import extract_mask_contours


class MvpWhiteboardStrokeExtractorAdapter:
    """Validate a mask and produce a source-bound contour artifact."""

    def __init__(
        self,
        *,
        mask_path_for: Callable[[str], str | Path],
        output_path_for: Callable[[str], str | Path],
    ) -> None:
        self._mask_path_for = mask_path_for
        self._output_path_for = output_path_for

    def extract(self, job: WhiteboardVideoJobV1, masks: MaskBatch) -> StrokeBatch:
        if not masks.mask_refs:
            raise WhiteboardVideoPipelineError("NO_MASK_ARTIFACT", retryable=False)

        try:
            mask_path = self._mask_path_for(masks.mask_refs[0])
            validate_mask_file(mask_path)
            extraction = extract_mask_contours(
                mask_path,
                self._output_path_for(job.job_id),
                source_hash=job.source_hash,
            )
        except (OSError, RuntimeError, ValueError) as error:
            code = str(error) if str(error).startswith("MASK_") else "STROKE_EXTRACTION_FAILED"
            raise WhiteboardVideoPipelineError(code, retryable=False) from error

        return StrokeBatch(
            source_hash=extraction.source_hash,
            stroke_refs=(extraction.stroke_ref,),
        )


__all__ = ["MvpWhiteboardStrokeExtractorAdapter"]
