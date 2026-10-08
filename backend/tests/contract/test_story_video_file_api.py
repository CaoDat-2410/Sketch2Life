"""The final MP4 is visible only to the matching READY story job."""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.contracts.schemas.story_video_media import VideoJobStatusV1
from sketch2life.interfaces.http.routers.story_video import router


def _app(job: VideoJobStatusV1, video_ref: str | None) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    class Service:
        def get(self, job_id: str) -> VideoJobStatusV1:
            if job_id != job.job_id:
                raise KeyError(job_id)
            return job

        def result(self, job_id: str):
            if job_id != job.job_id or video_ref is None:
                return None
            return SimpleNamespace(video=SimpleNamespace(video_ref=video_ref))

    app.state.story_video_job_service = Service()
    return app


def _job(state: str) -> VideoJobStatusV1:
    return VideoJobStatusV1(
        job_id="job-1",
        session_id="session-1",
        state=state,
        stage=state,
        progress_percent=100 if state == "READY" else 50,
        retry_count=0,
        public_message="Test job.",
    )


def test_ready_story_video_exposes_download_and_other_session_cannot_read(tmp_path) -> None:
    video = tmp_path / "video.mp4"
    video.write_bytes(b"synthetic-test-mp4")
    client = TestClient(_app(_job("READY"), str(video)))

    status = client.get("/v1/sessions/session-1/story-video/job-1")
    assert status.status_code == 200
    assert status.json()["video_artifact_ref"].endswith(
        "/v1/sessions/session-1/story-video/job-1/file"
    )
    response = client.get("/v1/sessions/session-1/story-video/job-1/file")
    assert response.status_code == 200
    assert response.content == b"synthetic-test-mp4"
    assert client.get("/v1/sessions/other/story-video/job-1/file").status_code == 404


def test_unready_story_video_never_exposes_file(tmp_path) -> None:
    video = tmp_path / "video.mp4"
    video.write_bytes(b"synthetic-test-mp4")
    client = TestClient(_app(_job("SCENES_RENDERING"), str(video)))

    status = client.get("/v1/sessions/session-1/story-video/job-1")
    assert status.json()["video_artifact_ref"] is None
    assert client.get("/v1/sessions/session-1/story-video/job-1/file").status_code == 409
