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
    captured: dict[str, object] = {}

    def fake_render(
        stroke_path, output_path, *, spec, motion_schedule, motion_durations_seconds
    ):
        captured["stroke"] = str(stroke_path)
        captured["output"] = str(output_path)
        captured["duration"] = spec.duration_seconds
        captured["motion_schedule"] = motion_schedule
        captured["motion_durations"] = motion_durations_seconds
        return WhiteboardMvpRenderResult(
            output_path=str(output_path),
            width=1280,
            height=720,
            fps=30,
            duration_seconds=8.0,
            codec="H264_AVC_HIGH_L4_1",
            size_bytes=100,
        )

    monkeypatch.setattr(adapter_module, "render_stroke_animation", fake_render)
    adapter = MvpWhiteboardRendererAdapter(
        stroke_path_for=lambda ref: tmp_path / f"{ref}.json",
        output_path_for=lambda job_id: tmp_path / f"{job_id}.mp4",
    )

    rendered = adapter.render(
        _job(),
        StrokeBatch(source_hash="a" * 64, stroke_refs=("cutout-1",)),
    )

    assert captured["stroke"].endswith("cutout-1.json")
    assert captured["output"].endswith("job-1.mp4")
    assert captured["duration"] == 8.0
    assert captured["motion_schedule"] == ()
    assert rendered.source_hash == "a" * 64
    assert rendered.render_ref.endswith("job-1.mp4")


def test_adapter_forwards_storyboard_motion_schedule(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    def fake_render(
        stroke_path, output_path, *, spec, motion_schedule, motion_durations_seconds
    ):
        captured["motion_schedule"] = motion_schedule
        captured["motion_durations"] = motion_durations_seconds
        return WhiteboardMvpRenderResult(
            output_path=str(output_path),
            width=1280,
            height=720,
            fps=30,
            duration_seconds=14.0,
            codec="H264_AVC_HIGH_L4_1",
            size_bytes=100,
        )

    monkeypatch.setattr(adapter_module, "render_stroke_animation", fake_render)
    adapter = MvpWhiteboardRendererAdapter(
        stroke_path_for=lambda ref: tmp_path / f"{ref}.json",
        output_path_for=lambda job_id: tmp_path / f"{job_id}.mp4",
    )
    job = _job().model_copy(
        update={
            "video_duration_seconds": 14.0,
            "scene_motions": ("INTRO", "FOCUS", "DEMONSTRATE", "RECAP"),
        }
    )

    adapter.render(
        job,
        StrokeBatch(source_hash="a" * 64, stroke_refs=("cutout-1",)),
    )

    assert captured["motion_schedule"] == (
        "INTRO",
        "FOCUS",
        "DEMONSTRATE",
        "RECAP",
    )
