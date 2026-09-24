"""HTTP endpoints for the session-local whiteboard video job."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse

from sketch2life.application.services.whiteboard_video_job import WhiteboardVideoJobService
from sketch2life.contracts.schemas.whiteboard_video import (
    WhiteboardVideoCreateRequestV1,
    WhiteboardVideoJobV1,
    WhiteboardVideoStatusV1,
)

router = APIRouter(prefix="/v1/sessions", tags=["whiteboard-video"])


def _service(request: Request) -> WhiteboardVideoJobService:
    service = getattr(request.app.state, "whiteboard_video_job_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="WHITEBOARD_VIDEO_UNAVAILABLE")
    return service


@router.post(
    "/{session_id}/whiteboard-video-jobs",
    response_model=WhiteboardVideoJobV1,
    status_code=status.HTTP_201_CREATED,
)
def create_whiteboard_video_job(
    session_id: str,
    body: WhiteboardVideoCreateRequestV1,
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    service = _service(request)
    try:
        job, replayed = service.create_or_replay(
            session_id=session_id,
            experience_spec_id=body.experience_spec_id,
            source_artifact_id=body.source_artifact_id,
            source_hash=body.source_hash,
            learning_thread_ref=body.learning_thread_ref,
            idempotency_key=body.idempotency_key,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail="IDEMPOTENCY_KEY_PAYLOAD_MISMATCH") from error
    if not replayed and service.can_run:
        background_tasks.add_task(service.run_safely, job.job_id)
    return JSONResponse(
        status_code=200 if replayed else 201,
        content=job.model_dump(mode="json"),
        headers={"Idempotency-Replayed": str(replayed).lower()},
    )


@router.get(
    "/{session_id}/whiteboard-video",
    response_model=WhiteboardVideoStatusV1,
)
def get_whiteboard_video_status(session_id: str, request: Request) -> WhiteboardVideoStatusV1:
    service = _service(request)
    matching = service.store.for_session(session_id)
    if not matching:
        raise HTTPException(status_code=404, detail="WHITEBOARD_VIDEO_NOT_FOUND")
    job = max(matching, key=lambda item: item.created_at)
    result = service.result(job.job_id)
    status_value = {
        "QUEUED": "NOT_STARTED",
        "RUNNING": job.current_stage,
        "READY": "READY",
        "RETRYABLE_FAILURE": "RETRYABLE_FAILURE",
        "FAILED": "FAILED",
        "EXPIRED": "EXPIRED",
    }[job.status]
    return WhiteboardVideoStatusV1(
        job_id=job.job_id,
        session_id=session_id,
        status=status_value,
        progress=job.progress,
        retryable=job.status == "RETRYABLE_FAILURE",
        retry_action="RETRY" if job.status == "RETRYABLE_FAILURE" else "NONE",
        video_artifact_ref=result.mp4_ref if result is not None and job.status == "READY" else None,
    )


__all__ = ["router"]
