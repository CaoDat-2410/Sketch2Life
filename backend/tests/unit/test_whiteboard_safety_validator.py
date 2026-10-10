from __future__ import annotations

from pathlib import Path

from sketch2life.application.services.whiteboard_video_pipeline import (
    EncodedWhiteboard,
    LocalizedRegionBatch,
    MaskBatch,
    RenderedWhiteboard,
    StrokeBatch,
    TtsTrack,
)
from sketch2life.application.services.whiteboard_video_job import WhiteboardVideoPipelineError
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.media.whiteboard_safety_validator import (
    WhiteboardSafetyValidator,
)
from test_whiteboard_video_job import SuccessfulPipeline, make_job, make_service


def _artifacts() -> tuple[LocalizedRegionBatch, MaskBatch, StrokeBatch, RenderedWhiteboard, TtsTrack, EncodedWhiteboard]:
    digest = "a" * 64
    return (
        LocalizedRegionBatch(digest, ("region",)),
        MaskBatch(digest, ("mask",)),
        StrokeBatch(digest, ("stroke",)),
        RenderedWhiteboard(digest, "render"),
        TtsTrack(digest, "tts"),
        EncodedWhiteboard(digest, "video", "mp4", 8.0, "H264_AVC_HIGH_L4_1", 100),
    )


def test_safety_validator_accepts_complete_provenance(tmp_path) -> None:
    paths = {name: tmp_path / name for name in ("mask", "stroke", "render", "tts", "mp4")}
    for path in paths.values():
        path.write_bytes(b"artifact")
    regions, masks, strokes, render, tts, encoded = _artifacts()
    masks = MaskBatch(masks.source_hash, (str(paths["mask"]),))
    strokes = StrokeBatch(strokes.source_hash, (str(paths["stroke"]),))
    render = RenderedWhiteboard(render.source_hash, str(paths["render"]))
    tts = TtsTrack(tts.source_hash, str(paths["tts"]))
    encoded = EncodedWhiteboard(encoded.source_hash, "video", str(paths["mp4"]), 8.0, encoded.codec, 100)
    service = make_service(SuccessfulPipeline())
    job = make_job(service)
    WhiteboardSafetyValidator(artifact_exists=lambda ref: Path(ref).is_file()).validate(
        job, regions, masks, strokes, render, tts, encoded
    )


def test_safety_validator_rejects_provenance_mismatch() -> None:
    service = make_service(SuccessfulPipeline())
    job = make_job(service)
    regions, masks, strokes, render, tts, encoded = _artifacts()

    try:
        WhiteboardSafetyValidator(artifact_exists=lambda _: True).validate(
            job,
            LocalizedRegionBatch("b" * 64, regions.region_refs),
            masks,
            strokes,
            render,
            tts,
            encoded,
        )
    except WhiteboardVideoPipelineError as error:
        assert error.code == "PROVENANCE_MISMATCH"
    else:
        raise AssertionError("provenance mismatch must fail closed")
