"""HTTP API for the illustrated story-video job."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from sketch2life.application.services.story_video_job import StoryVideoJobService
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
    except ValueError as error:
        raise HTTPException(status_code=409, detail="IDEMPOTENCY_KEY_PAYLOAD_MISMATCH") from error
    if not replayed:
        background_tasks.add_task(service.run_safely, job.job_id)
    return job


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
    return job


__all__ = ["router"]
