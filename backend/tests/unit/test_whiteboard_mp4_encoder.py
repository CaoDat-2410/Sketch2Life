from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sketch2life.application.services.whiteboard_video_pipeline import (
    RenderedWhiteboard,
    TtsTrack,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.media.whiteboard_mp4_encoder import (
    WhiteboardMp4EncoderAdapter,
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
        progress=90,
        current_stage="ENCODING",
        attempt=1,
        idempotency_key="idem-1",
        created_at=created_at,
        started_at=created_at + timedelta(seconds=1),
        expires_at=created_at + timedelta(minutes=3),
    )


def test_encoder_validates_and_returns_mp4_artifact(tmp_path) -> None:
    captured: list[tuple[str, str]] = []

    def encode(render_ref: str, tts_ref: str, output_path: str) -> None:
        captured.append((render_ref, tts_ref))
        with open(output_path, "wb") as file:
            file.write(b"fake-mp4")

    adapter = WhiteboardMp4EncoderAdapter(
        encode=encode,
        inspect=lambda _: (8.0, "H264_AVC_HIGH_L4_1", 100),
        output_path_for=lambda job_id: tmp_path / f"{job_id}.mp4",
    )

    result = adapter.encode(
        _job(),
        RenderedWhiteboard("a" * 64, "render-1"),
        TtsTrack("a" * 64, "tts-1"),
    )

    assert captured == [("render-1", "tts-1")]
    assert result.video_artifact_id == "video:job-1"
    assert result.duration_seconds == 8.0
    assert result.codec == "H264_AVC_HIGH_L4_1"
