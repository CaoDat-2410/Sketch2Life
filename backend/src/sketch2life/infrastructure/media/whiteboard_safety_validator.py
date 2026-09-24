"""Fail-closed safety and provenance gate before a whiteboard job is READY."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoPipelineError,
)
from sketch2life.application.services.whiteboard_video_pipeline import (
    EncodedWhiteboard,
    LocalizedRegionBatch,
    MaskBatch,
    RenderedWhiteboard,
    StrokeBatch,
    TtsTrack,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1


class WhiteboardSafetyValidator:
    """Validate artifact continuity and existence without exposing provider details."""

    def __init__(self, *, artifact_exists: Callable[[str | Path], bool]) -> None:
        self._artifact_exists = artifact_exists

    def validate(
        self,
        job: WhiteboardVideoJobV1,
        regions: LocalizedRegionBatch,
        masks: MaskBatch,
        strokes: StrokeBatch,
        render: RenderedWhiteboard,
        tts: TtsTrack,
        encoded: EncodedWhiteboard,
    ) -> None:
        if any(batch.source_hash != job.source_hash for batch in (regions, masks, strokes)):
            raise WhiteboardVideoPipelineError("PROVENANCE_MISMATCH", retryable=False)
        if render.source_hash != job.source_hash or tts.source_hash != job.source_hash:
            raise WhiteboardVideoPipelineError("PROVENANCE_MISMATCH", retryable=False)
        if encoded.source_hash != job.source_hash:
            raise WhiteboardVideoPipelineError("PROVENANCE_MISMATCH", retryable=False)
        refs = (*masks.mask_refs, *strokes.stroke_refs, render.render_ref, tts.tts_ref, encoded.mp4_ref)
        if not refs or not all(self._artifact_exists(ref) for ref in refs):
            raise WhiteboardVideoPipelineError("ARTIFACT_MISSING", retryable=False)
        if not 5.0 <= encoded.duration_seconds <= 10.0:
            raise WhiteboardVideoPipelineError("VIDEO_DURATION_INVALID", retryable=False)
        if encoded.codec != "H264_AVC_HIGH_L4_1":
            raise WhiteboardVideoPipelineError("VIDEO_CODEC_INVALID", retryable=False)
        if encoded.size_bytes <= 0 or encoded.size_bytes > 12 * 1024 * 1024:
            raise WhiteboardVideoPipelineError("VIDEO_SIZE_INVALID", retryable=False)


__all__ = ["WhiteboardSafetyValidator"]
