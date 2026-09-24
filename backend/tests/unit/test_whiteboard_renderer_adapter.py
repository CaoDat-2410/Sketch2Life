from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sketch2life.application.services.whiteboard_video_pipeline import StrokeBatch
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.media import whiteboard_renderer_adapter as adapter_module
from sketch2life.infrastructure.media.whiteboard_mvp_renderer import (
    WhiteboardMvpRenderResult,
)
from sketch2life.infrastructure.media.whiteboard_renderer_adapter import (
    MvpWhiteboardRendererAdapter,
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
        progress=55,
        current_stage="EXTRACTING_STROKES",
        attempt=1,
        idempotency_key="idem-1",
        created_at=created_at,
        started_at=created_at + timedelta(seconds=1),
        expires_at=created_at + timedelta(minutes=3),
    )


def test_adapter_resolves_cutout_and_returns_render_reference(monkeypatch, tmp_path) -> None:
    captured: dict[str, str] = {}

    def fake_render(cutout_path, output_path, *, spec):
        captured["cutout"] = str(cutout_path)
        captured["output"] = str(output_path)
        return WhiteboardMvpRenderResult(
            output_path=str(output_path),
            width=1280,
            height=720,
            fps=30,
            duration_seconds=8.0,
            codec="H264_AVC_HIGH_L4_1",
            size_bytes=100,
        )

    monkeypatch.setattr(adapter_module, "render_progressive_reveal", fake_render)
    adapter = MvpWhiteboardRendererAdapter(
        cutout_path_for=lambda ref: tmp_path / f"{ref}.png",
        output_path_for=lambda job_id: tmp_path / f"{job_id}.mp4",
    )

    rendered = adapter.render(
        _job(),
        StrokeBatch(source_hash="a" * 64, stroke_refs=("cutout-1",)),
    )

    assert captured["cutout"].endswith("cutout-1.png")
    assert captured["output"].endswith("job-1.mp4")
    assert rendered.source_hash == "a" * 64
    assert rendered.render_ref.endswith("job-1.mp4")
