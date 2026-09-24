"""Validated MP4 encoder boundary for the whiteboard pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoPipelineError,
)
from sketch2life.application.services.whiteboard_video_pipeline import (
    EncodedWhiteboard,
    RenderedWhiteboard,
    TtsTrack,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1


class WhiteboardMp4EncoderAdapter:
    """Adapt an encoder implementation while enforcing the MP4 contract."""

    def __init__(
        self,
        *,
        encode: Callable[[str, str, str | Path], None],
        inspect: Callable[[str | Path], tuple[float, str, int]],
        output_path_for: Callable[[str], str | Path],
        max_size_bytes: int = 12 * 1024 * 1024,
    ) -> None:
        self._encode = encode
        self._inspect = inspect
        self._output_path_for = output_path_for
        self._max_size_bytes = max_size_bytes

    def encode(
        self,
        job: WhiteboardVideoJobV1,
        render: RenderedWhiteboard,
        tts: TtsTrack,
    ) -> EncodedWhiteboard:
        output_path = self._output_path_for(job.job_id)
        try:
            self._encode(render.render_ref, tts.tts_ref, output_path)
            output = Path(output_path)
            if not output.is_file() or output.stat().st_size <= 0:
                raise ValueError("encoder produced no MP4 artifact")
            duration_seconds, codec, size_bytes = self._inspect(output)
            if codec != "H264_AVC_HIGH_L4_1":
                raise ValueError("encoded video codec is not contract compatible")
            if not 5.0 <= duration_seconds <= 10.0:
                raise ValueError("encoded video duration is outside the contract range")
            if size_bytes <= 0 or size_bytes > self._max_size_bytes:
                raise ValueError("encoded video size is outside the contract range")
        except (OSError, RuntimeError, ValueError) as error:
            raise WhiteboardVideoPipelineError("ENCODING_FAILED", retryable=True) from error

        return EncodedWhiteboard(
            source_hash=job.source_hash,
            video_artifact_id=f"video:{job.job_id}",
            mp4_ref=str(output_path),
            duration_seconds=duration_seconds,
            codec=codec,
            size_bytes=size_bytes,
        )


__all__ = ["WhiteboardMp4EncoderAdapter"]
