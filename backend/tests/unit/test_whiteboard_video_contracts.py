from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.whiteboard_video import (
    WhiteboardVideoJobV1,
    WhiteboardVideoResultV1,
    WhiteboardVideoStatusV1,
)


NOW = datetime(2026, 9, 24, 8, 0, tzinfo=timezone.utc)
HASH = "a" * 64


def make_job(**overrides: object) -> WhiteboardVideoJobV1:
    values: dict[str, object] = {
        "job_id": "job-001",
        "session_id": "session-001",
        "experience_spec_id": "spec-001",
        "source_artifact_id": "artifact-source-001",
        "source_hash": HASH,
        "learning_thread_ref": "thread-001",
        "status": "RUNNING",
        "progress": 45,
        "current_stage": "SEGMENTING",
        "attempt": 1,
        "idempotency_key": "idem-001",
        "created_at": NOW,
        "started_at": NOW,
        "expires_at": NOW.replace(hour=9),
    }
    values.update(overrides)
    return WhiteboardVideoJobV1(**values)


def test_job_requires_timezone_aware_timestamps() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        make_job(created_at=datetime(2026, 9, 24, 8, 0))


def test_job_rejects_failure_without_typed_failure_ref() -> None:
    with pytest.raises(ValidationError, match="typed failure"):
        make_job(status="RETRYABLE_FAILURE", failure_ref=None)


def test_status_ready_requires_artifact_and_complete_progress() -> None:
    with pytest.raises(ValidationError, match="ready status"):
        WhiteboardVideoStatusV1(
            job_id="job-001",
            session_id="session-001",
            status="READY",
            progress=99,
            retryable=False,
            retry_action="NONE",
        )


def test_status_hides_artifact_until_ready() -> None:
    with pytest.raises(ValidationError, match="non-ready"):
        WhiteboardVideoStatusV1(
            job_id="job-001",
            session_id="session-001",
            status="SEGMENTING",
            progress=45,
            retryable=False,
            retry_action="NONE",
            video_artifact_ref="artifact-video-001",
        )


def test_result_rejects_oversized_mp4() -> None:
    with pytest.raises(ValidationError):
        WhiteboardVideoResultV1(
            job_id="job-001",
            video_artifact_id="artifact-video-001",
            mp4_ref="artifact-ref/video.mp4",
            mask_refs=("artifact-mask-001",),
            stroke_refs=("artifact-stroke-001",),
            tts_ref="artifact-tts-001",
            source_hash=HASH,
            experience_spec_id="spec-001",
            learning_thread_ref="thread-001",
            duration_seconds=8,
            codec="H264_AVC_HIGH_L4_1",
            size_bytes=12 * 1024 * 1024 + 1,
        )


def test_result_accepts_valid_ready_artifacts() -> None:
    result = WhiteboardVideoResultV1(
        job_id="job-001",
        video_artifact_id="artifact-video-001",
        mp4_ref="artifact-ref/video.mp4",
        mask_refs=("artifact-mask-001",),
        stroke_refs=("artifact-stroke-001",),
        tts_ref="artifact-tts-001",
        source_hash=HASH,
        experience_spec_id="spec-001",
        learning_thread_ref="thread-001",
        duration_seconds=8,
        codec="H264_AVC_HIGH_L4_1",
        size_bytes=4_000_000,
    )

    assert result.status == "READY"
    assert result.safety_status == "PASSED"
