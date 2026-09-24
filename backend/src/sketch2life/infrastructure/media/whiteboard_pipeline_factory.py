"""Composition root for the provider-backed whiteboard MVP pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sketch2life.application.services.whiteboard_video_pipeline import (
    LocalizerPort,
    Mp4EncoderPort,
    WhiteboardSafetyValidatorPort,
    WhiteboardVideoPipeline,
)

from .whiteboard_renderer_adapter import MvpWhiteboardRendererAdapter
from .whiteboard_safety_validator import WhiteboardSafetyValidator
from .whiteboard_segmenter_adapter import MvpWhiteboardSegmenterAdapter
from .whiteboard_stroke_adapter import MvpWhiteboardStrokeExtractorAdapter
from .whiteboard_tts_adapter import WhiteboardTtsAdapter
from .whiteboard_mp4_encoder import WhiteboardMp4EncoderAdapter


def build_whiteboard_mvp_pipeline(
    *,
    localizer: LocalizerPort,
    mask_path_for: Callable[[str], str | Path],
    stroke_output_path_for: Callable[[str], str | Path],
    cutout_path_for: Callable[[str], str | Path],
    render_output_path_for: Callable[[str], str | Path],
    script_for: Callable[[str], str],
    synthesize_tts: Callable[[str, str | Path], None],
    tts_output_path_for: Callable[[str], str | Path],
    encode_mp4: Callable[[str, str, str | Path], None],
    inspect_mp4: Callable[[str | Path], tuple[float, str, int]],
    mp4_output_path_for: Callable[[str], str | Path],
    artifact_exists: Callable[[str | Path], bool],
    safety_validator: WhiteboardSafetyValidatorPort | None = None,
) -> WhiteboardVideoPipeline:
    """Build the complete MVP stage graph without leaking provider credentials."""

    return WhiteboardVideoPipeline(
        localizer=localizer,
        segmenter=MvpWhiteboardSegmenterAdapter(mask_path_for=mask_path_for),
        stroke_extractor=MvpWhiteboardStrokeExtractorAdapter(
            mask_path_for=mask_path_for,
            output_path_for=stroke_output_path_for,
        ),
        renderer=MvpWhiteboardRendererAdapter(
            cutout_path_for=cutout_path_for,
            output_path_for=render_output_path_for,
        ),
        tts=WhiteboardTtsAdapter(
            script_for=script_for,
            synthesize=synthesize_tts,
            output_path_for=tts_output_path_for,
        ),
        encoder=WhiteboardMp4EncoderAdapter(
            encode=encode_mp4,
            inspect=inspect_mp4,
            output_path_for=mp4_output_path_for,
        ),
        safety_validator=safety_validator or WhiteboardSafetyValidator(
            artifact_exists=artifact_exists
        ),
    )


__all__ = ["build_whiteboard_mvp_pipeline"]
