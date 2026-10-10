"""Pipeline adapter for SAM2-produced mask artifacts."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoPipelineError,
)
from sketch2life.application.services.whiteboard_video_pipeline import (
    LocalizedRegionBatch,
    MaskBatch,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1

from .whiteboard_mask_validation import validate_mask_file


class MvpWhiteboardSegmenterAdapter:
    """Resolve and validate one mask artifact for each localized region."""

    def __init__(
        self,
        *,
        mask_path_for: Callable[[str], str | Path],
    ) -> None:
        self._mask_path_for = mask_path_for

    def segment(
        self,
        job: WhiteboardVideoJobV1,
        regions: LocalizedRegionBatch,
    ) -> MaskBatch:
        if not regions.region_refs:
            raise WhiteboardVideoPipelineError("NO_LOCALIZED_REGION", retryable=False)

        mask_refs: list[str] = []
        try:
            for region_ref in regions.region_refs:
                mask_path = self._mask_path_for(region_ref)
                validate_mask_file(mask_path)
                mask_refs.append(str(mask_path))
        except (OSError, RuntimeError, ValueError) as error:
            code = str(error) if str(error).startswith("MASK_") else "SEGMENTATION_FAILED"
            raise WhiteboardVideoPipelineError(code, retryable=False) from error

        return MaskBatch(source_hash=job.source_hash, mask_refs=tuple(mask_refs))


__all__ = ["MvpWhiteboardSegmenterAdapter"]
