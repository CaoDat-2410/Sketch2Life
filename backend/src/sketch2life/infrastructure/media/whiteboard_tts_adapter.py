"""Provider-neutral TTS adapter for the whiteboard narration track."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoPipelineError,
)
from sketch2life.application.services.whiteboard_video_pipeline import TtsTrack
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1


class WhiteboardTtsAdapter:
    """Create an independent narration artifact from the learning thread script."""

    def __init__(
        self,
        *,
        script_for: Callable[[str], str],
        synthesize: Callable[[str, str | Path], None],
        output_path_for: Callable[[str], str | Path],
        locale: str = "vi-VN",
    ) -> None:
        if not locale or len(locale) > 32:
            raise ValueError("TTS locale must be a short non-empty value")
        self._script_for = script_for
        self._synthesize = synthesize
        self._output_path_for = output_path_for
        self._locale = locale

    def synthesize(self, job: WhiteboardVideoJobV1) -> TtsTrack:
        try:
            script = self._script_for(job.learning_thread_ref)
            if not script or len(script) > 10_000:
                raise ValueError("TTS script is empty or exceeds the safety limit")
            output_path = self._output_path_for(job.job_id)
            self._synthesize(script, output_path)
            artifact = Path(output_path)
            if not artifact.is_file() or artifact.stat().st_size <= 0:
                raise ValueError("TTS synthesizer produced no audio artifact")
        except (OSError, RuntimeError, ValueError) as error:
            raise WhiteboardVideoPipelineError("TTS_FAILED", retryable=True) from error

        return TtsTrack(source_hash=job.source_hash, tts_ref=str(output_path))


__all__ = ["WhiteboardTtsAdapter"]
