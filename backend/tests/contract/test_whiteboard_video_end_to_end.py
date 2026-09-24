from __future__ import annotations

from fastapi.testclient import TestClient

from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoResultV1
from sketch2life.application.services.whiteboard_video_job import WhiteboardVideoJobService
from sketch2life.interfaces.http.app import create_app


SOURCE_HASH = "a" * 64


class ReadyPipeline:
    def run(self, job, update_stage):
        for stage, progress in (
            ("LOCALIZING", 15),
            ("SEGMENTING", 35),
            ("EXTRACTING_STROKES", 55),
            ("RENDERING", 70),
            ("ENCODING", 90),
        ):
            update_stage(stage, progress)
        return WhiteboardVideoResultV1(
            job_id=job.job_id,
            video_artifact_id="artifact-video-001",
            mp4_ref="video/whiteboard.mp4",
            mask_refs=("artifact-mask-001",),
            stroke_refs=("artifact-stroke-001",),
            tts_ref="artifact-tts-001",
            source_hash=job.source_hash,
            experience_spec_id=job.experience_spec_id,
            learning_thread_ref=job.learning_thread_ref,
            duration_seconds=8,
            codec="H264_AVC_HIGH_L4_1",
            size_bytes=4_000_000,
        )


def test_whiteboard_video_api_runs_configured_pipeline_to_ready() -> None:
    service = WhiteboardVideoJobService(pipeline=ReadyPipeline())
    client = TestClient(create_app(whiteboard_video_job_service=service))

    response = client.post(
        "/v1/sessions/session-001/whiteboard-video-jobs",
        json={
            "experience_spec_id": "spec-001",
            "source_artifact_id": "artifact-source-001",
            "source_hash": SOURCE_HASH,
            "learning_thread_ref": "thread-001",
            "idempotency_key": "idem-e2e-001",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "QUEUED"

    status = client.get("/v1/sessions/session-001/whiteboard-video")

    assert status.status_code == 200
    assert status.json()["status"] == "READY"
    assert status.json()["progress"] == 100
    assert status.json()["video_artifact_ref"] == "video/whiteboard.mp4"
