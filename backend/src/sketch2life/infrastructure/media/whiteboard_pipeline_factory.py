"""Composition root for the provider-backed whiteboard MVP pipeline."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from sketch2life.application.services.whiteboard_video_pipeline import (
    LocalizerPort,
    MaskBatch,
    Mp4EncoderPort,
    StrokeBatch,
    WhiteboardVideoPipelineError,
    WhiteboardSafetyValidatorPort,
    WhiteboardVideoPipeline,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.ai.lightning_whiteboard import (
    LightningWhiteboardLocalizationAdapter,
)
from sketch2life.infrastructure.ai.lightning_whiteboard_segmentation import (
    LightningWhiteboardSegmentationAdapter,
)
from sketch2life.infrastructure.ai.lightning_client import JsonTransport
from sketch2life.infrastructure.storage.in_memory import InMemoryArtifactStore

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


def build_lightning_whiteboard_mvp_pipeline(
    *,
    transport: JsonTransport,
    artifacts: InMemoryArtifactStore,
    artifact_root: str | Path,
    script_for: Callable[[str], str],
    synthesize_tts: Callable[[str, str | Path], None],
    encode_mp4: Callable[[str, str, str | Path], None],
    inspect_mp4: Callable[[str | Path], tuple[float, str, int]],
    localization_path: str = "/v1/whiteboard/localize",
    segmentation_path: str = "/v1/whiteboard/segment",
    max_size_bytes: int = 12 * 1024 * 1024,
) -> WhiteboardVideoPipeline:
    """Build the real provider-backed MVP stage graph.

    Provider responses are copied into the process-local artifact store before
    stroke extraction. The source image remains loaded from the existing
    session artifact store, so every stage keeps the original source hash.
    TTS and FFmpeg remain injected boundaries and are never silently replaced
    with fake success implementations.
    """

    root = Path(artifact_root).resolve()

    def load_artifact(artifact_ref: str) -> bytes:
        stored = artifacts.get(artifact_ref)
        if stored is None:
            raise KeyError("whiteboard source artifact is unavailable")
        return stored[1]

    def store_mask(mask_ref: str, content: bytes) -> str:
        safe_name = hashlib.sha256(mask_ref.encode("utf-8")).hexdigest()
        path = root / "masks" / f"{safe_name}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def mask_path_for(mask_ref: str) -> str:
        return mask_ref

    def job_path(job_id: str, suffix: str) -> str:
        if not job_id or Path(job_id).name != job_id:
            raise ValueError("invalid whiteboard job id")
        path = (root / job_id).with_suffix(suffix).resolve()
        path.relative_to(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    localizer = LightningWhiteboardLocalizationAdapter(
        transport=transport,
        artifact_loader=load_artifact,
        endpoint_path=localization_path,
    )
    segmenter = LightningWhiteboardSegmentationAdapter(
        transport=transport,
        artifact_loader=load_artifact,
        artifact_sink=store_mask,
        endpoint_path=segmentation_path,
    )

    cutouts: dict[str, str] = {}
    stroke_extractor = MvpWhiteboardStrokeExtractorAdapter(
        mask_path_for=mask_path_for,
        output_path_for=lambda job_id: job_path(job_id, ".strokes.json"),
    )

    class StrokeAndCutoutAdapter:
        def extract(
            self, job: WhiteboardVideoJobV1, masks: MaskBatch
        ) -> StrokeBatch:
            strokes = stroke_extractor.extract(job, masks)
            try:
                from io import BytesIO

                import numpy as np
                from PIL import Image

                source = Image.open(BytesIO(load_artifact(job.source_artifact_id))).convert("RGBA")
                mask = Image.open(masks.mask_refs[0]).convert("L")
                if mask.size != source.size:
                    raise ValueError("mask and source dimensions differ")
                rgba = np.asarray(source).copy()
                rgba[:, :, 3] = np.asarray(mask)
                cutout_path = job_path(job.job_id, ".cutout.png")
                Image.fromarray(rgba, mode="RGBA").save(cutout_path, format="PNG")
                cutouts[strokes.stroke_refs[0]] = cutout_path
            except (OSError, RuntimeError, ValueError, ImportError) as error:
                raise WhiteboardVideoPipelineError(
                    "CUTOUT_FAILED", retryable=False
                ) from error
            return strokes

    def cutout_path_for(stroke_ref: str) -> str:
        path = cutouts.get(stroke_ref)
        if path is None:
            raise KeyError("cutout artifact is unavailable")
        return path

    return WhiteboardVideoPipeline(
        localizer=localizer,
        segmenter=segmenter,
        stroke_extractor=StrokeAndCutoutAdapter(),
        renderer=MvpWhiteboardRendererAdapter(
            cutout_path_for=cutout_path_for,
            output_path_for=lambda job_id: job_path(job_id, ".render.mp4"),
        ),
        tts=WhiteboardTtsAdapter(
            script_for=script_for,
            synthesize=synthesize_tts,
            output_path_for=lambda job_id: job_path(job_id, ".tts.wav"),
        ),
        encoder=WhiteboardMp4EncoderAdapter(
            encode=encode_mp4,
            inspect=inspect_mp4,
            output_path_for=lambda job_id: job_path(job_id, ".mp4"),
            max_size_bytes=max_size_bytes,
        ),
        safety_validator=WhiteboardSafetyValidator(
            artifact_exists=lambda ref: Path(ref).is_file()
        ),
    )


__all__ = [
    "build_lightning_whiteboard_mvp_pipeline",
    "build_whiteboard_mvp_pipeline",
]
