from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sketch2life.application.services.whiteboard_video_pipeline import MaskBatch
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.media.whiteboard_stroke_adapter import (
    MvpWhiteboardStrokeExtractorAdapter,
)


def _job() -> WhiteboardVideoJobV1:
    created_at = datetime(2026, 9, 24, tzinfo=UTC)
    return WhiteboardVideoJobV1(
        job_id="job-1",
        session_id="session-1",
        experience_spec_id="spec-1",
        source_artifact_id="source-1",
        source_hash="a" * 64,
        learning_thread_ref="thread-1",
        status="RUNNING",
        progress=35,
        current_stage="SEGMENTING",
        attempt=1,
        idempotency_key="idem-1",
        created_at=created_at,
        started_at=created_at + timedelta(seconds=1),
        expires_at=created_at + timedelta(minutes=3),
    )


def test_adapter_validates_mask_and_returns_stroke_ref(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    mask_path = tmp_path / "mask.png"
    image = Image.new("L", (30, 30), 0)
    for x in range(5, 25):
        for y in range(5, 25):
            image.putpixel((x, y), 255)
    image.save(mask_path)

    adapter = MvpWhiteboardStrokeExtractorAdapter(
        mask_path_for=lambda _: mask_path,
        output_path_for=lambda job_id: tmp_path / f"{job_id}.json",
    )

    strokes = adapter.extract(
        _job(),
        MaskBatch(source_hash="a" * 64, mask_refs=("mask-1",)),
    )

    assert strokes.source_hash == "a" * 64
    assert strokes.stroke_refs[0].endswith("job-1.json")
