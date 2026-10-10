from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sketch2life.application.services.whiteboard_video_pipeline import LocalizedRegionBatch
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.media.whiteboard_segmenter_adapter import (
    MvpWhiteboardSegmenterAdapter,
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
        progress=15,
        current_stage="LOCALIZING",
        attempt=1,
        idempotency_key="idem-1",
        created_at=created_at,
        started_at=created_at + timedelta(seconds=1),
        expires_at=created_at + timedelta(minutes=3),
    )


def test_segmenter_validates_each_region_mask(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    mask_path = tmp_path / "region-1.png"
    image = Image.new("L", (40, 40), 0)
    for x in range(5, 35):
        for y in range(5, 35):
            image.putpixel((x, y), 255)
    image.save(mask_path)

    adapter = MvpWhiteboardSegmenterAdapter(mask_path_for=lambda _: mask_path)
    masks = adapter.segment(
        _job(),
        LocalizedRegionBatch(source_hash="a" * 64, region_refs=("region-1",)),
    )

    assert masks.source_hash == "a" * 64
    assert masks.mask_refs == (str(mask_path),)
