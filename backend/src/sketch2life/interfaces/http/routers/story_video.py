"""HTTP API for the illustrated story-video job."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import FileResponse

from sketch2life.application.services.story_video_job import (
    StoryVideoInputError,
    StoryVideoJobService,
)
from sketch2life.contracts.schemas.story_video_http import StoryVideoCreateRequestV1
from sketch2life.contracts.schemas.story_video_media import VideoJobStatusV1

router = APIRouter(prefix="/v1/sessions", tags=["story-video"])


def _service(request: Request) -> StoryVideoJobService:
    service = getattr(request.app.state, "story_video_job_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="STORY_VIDEO_UNAVAILABLE")
    return service


@router.post(
    "/{session_id}/story-video-jobs",
    response_model=VideoJobStatusV1,
    status_code=status.HTTP_201_CREATED,
)
def create_story_video_job(
    session_id: str,
    body: StoryVideoCreateRequestV1,
    request: Request,
    background_tasks: BackgroundTasks,
) -> VideoJobStatusV1:
    service = _service(request)
    try:
        job, replayed = service.create_or_replay(
            session_id=session_id,
            idempotency_key=body.idempotency_key,
            package=body.package,
            segments=body.segments,
        )
    except StoryVideoInputError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail="IDEMPOTENCY_KEY_PAYLOAD_MISMATCH") from error
    if not replayed:
        background_tasks.add_task(service.run_safely, job.job_id)
    return job


def _status_with_download_url(
    request: Request, service: StoryVideoJobService, job: VideoJobStatusV1
) -> VideoJobStatusV1:
    if job.state != "READY" or service.result(job.job_id) is None:
        return job
    return job.model_copy(
        update={
            "video_artifact_ref": str(
                request.url_for(
                    "stream_story_video", session_id=job.session_id, job_id=job.job_id
                )
            )
        }
    )


@router.get("/{session_id}/story-video-jobs", response_model=list[VideoJobStatusV1])
def list_story_video_jobs(session_id: str, request: Request) -> list[VideoJobStatusV1]:
    service = _service(request)
    return [
        _status_with_download_url(request, service, job)
        for job in service.for_session(session_id)
    ]


@router.get("/{session_id}/story-video/{job_id}", response_model=VideoJobStatusV1)
def get_story_video_status(
    session_id: str, job_id: str, request: Request
) -> VideoJobStatusV1:
    service = _service(request)
    try:
        job = service.get(job_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="STORY_VIDEO_NOT_FOUND") from error
    if job.session_id != session_id:
        raise HTTPException(status_code=404, detail="STORY_VIDEO_NOT_FOUND")
    return _status_with_download_url(request, service, job)


@router.get(
    "/{session_id}/story-video/{job_id}/file",
    name="stream_story_video",
    response_class=FileResponse,
)
def stream_story_video(session_id: str, job_id: str, request: Request) -> FileResponse:
    service = _service(request)
    try:
        job = service.get(job_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="STORY_VIDEO_NOT_FOUND") from error
    if job.session_id != session_id:
        raise HTTPException(status_code=404, detail="STORY_VIDEO_NOT_FOUND")
    run = service.result(job_id)
    if (
        job.state != "READY"
        or run is None
        or run.video.video_ref is None
        or run.video.video_sha256 is None
    ):
        raise HTTPException(status_code=409, detail="STORY_VIDEO_NOT_READY")
    path = Path(run.video.video_ref)
    if not path.is_file() or path.suffix.lower() != ".mp4":
        raise HTTPException(status_code=404, detail="STORY_VIDEO_FILE_NOT_FOUND")
    try:
        with path.open("rb") as video:
            actual_sha256 = hashlib.file_digest(video, "sha256").hexdigest()
    except OSError as error:
        raise HTTPException(status_code=404, detail="STORY_VIDEO_FILE_NOT_FOUND") from error
    if actual_sha256 != run.video.video_sha256:
        raise HTTPException(status_code=409, detail="STORY_VIDEO_FILE_HASH_MISMATCH")
    return FileResponse(path, media_type="video/mp4", filename=f"{job_id}.mp4")


__all__ = ["router"]
