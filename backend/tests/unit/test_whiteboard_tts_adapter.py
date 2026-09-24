from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.media.whiteboard_tts_adapter import WhiteboardTtsAdapter


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
        progress=70,
        current_stage="RENDERING",
        attempt=1,
        idempotency_key="idem-1",
        created_at=created_at,
        started_at=created_at + timedelta(seconds=1),
        expires_at=created_at + timedelta(minutes=3),
    )


def test_tts_adapter_uses_learning_thread_and_returns_artifact(tmp_path) -> None:
    captured: list[str] = []

    def synthesize(script: str, output_path: str) -> None:
        captured.append(script)
        with open(output_path, "wb") as file:
            file.write(b"fake-audio")

    adapter = WhiteboardTtsAdapter(
        script_for=lambda ref: f"script for {ref}",
        synthesize=synthesize,
        output_path_for=lambda job_id: tmp_path / f"{job_id}.wav",
    )

    track = adapter.synthesize(_job())

    assert captured == ["script for thread-1"]
    assert track.source_hash == "a" * 64
    assert track.tts_ref.endswith("job-1.wav")
