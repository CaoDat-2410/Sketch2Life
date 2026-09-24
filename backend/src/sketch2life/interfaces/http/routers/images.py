"""FEAT-018 media ingress and explicit understanding routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Header, Request, UploadFile
from fastapi.responses import JSONResponse

from sketch2life.application.services.ephemeral_sessions import (
    SessionWorkflowError,
    failure_result,
)
from sketch2life.application.services.live_image_demo import LiveImageDemoService
from sketch2life.contracts.schemas.mobile_workflow import (
    MobileWorkflowCommandV1,
    MobileWorkflowResultV1,
)

_MAX_IMAGE_BYTES = 5_000_000
_MAX_AUDIO_BYTES = 20_000_000

router = APIRouter(prefix="/v1/sessions", tags=["image-demo"])


@router.post(
    "/{session_id}/media/image",
    response_model=MobileWorkflowResultV1,
    summary="Upload and admit one synthetic non-child image",
)
async def upload_image(
    session_id: str,
    request: Request,
    image: Annotated[UploadFile, File(description="Single static JPEG or PNG; max 5 MB")],
    request_id: Annotated[str, Header(alias="X-Request-ID", min_length=1, max_length=120)],
    expected_session_version: Annotated[int, Header(alias="X-Expected-Session-Version", ge=0)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=200)],
    actor_ref: Annotated[str, Header(alias="X-Actor-Ref", min_length=1, max_length=160)],
    synthetic_non_child_confirmed: Annotated[bool, Header(alias="X-Synthetic-Non-Child-Confirmed")],
) -> JSONResponse:
    service: LiveImageDemoService | None = request.app.state.live_image_demo_service
    if service is None:
        error = SessionWorkflowError(
            code="IMAGE_DEMO_NOT_CONFIGURED",
            status_code=503,
            safe_message="The image-only demo service is not configured.",
        )
        return _error_response(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    body = await image.read(_MAX_IMAGE_BYTES + 1)
    await image.close()
    try:
        result, replayed = service.upload_image(
            session_id=session_id,
            request_id=request_id,
            expected_session_version=expected_session_version,
            idempotency_key=idempotency_key,
            actor_ref=actor_ref,
            synthetic_non_child_confirmed=synthetic_non_child_confirmed,
            filename=image.filename or "image",
            body=body,
        )
    except SessionWorkflowError as error:
        return _error_response(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    return JSONResponse(
        status_code=200,
        content=result.model_dump(mode="json"),
        headers={"Idempotency-Replayed": str(replayed).lower()},
    )


@router.post(
    "/{session_id}/media/audio",
    response_model=MobileWorkflowResultV1,
    summary="Upload optional session-local narration audio",
)
async def upload_audio(
    session_id: str,
    request: Request,
    audio: Annotated[UploadFile, File(description="Narration audio; max 20 MB")],
    request_id: Annotated[str, Header(alias="X-Request-ID", min_length=1, max_length=120)],
    expected_session_version: Annotated[int, Header(alias="X-Expected-Session-Version", ge=0)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=200)],
    actor_ref: Annotated[str, Header(alias="X-Actor-Ref", min_length=1, max_length=160)],
) -> JSONResponse:
    service: LiveImageDemoService | None = request.app.state.live_image_demo_service
    if service is None:
        error = SessionWorkflowError(
            code="IMAGE_DEMO_NOT_CONFIGURED",
            status_code=503,
            safe_message="The live demo service is not configured.",
        )
        return _error_response(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    body = await audio.read(_MAX_AUDIO_BYTES + 1)
    await audio.close()
    try:
        result, replayed = service.upload_audio(
            session_id=session_id,
            request_id=request_id,
            expected_session_version=expected_session_version,
            idempotency_key=idempotency_key,
            actor_ref=actor_ref,
            filename=audio.filename or "narration",
            declared_content_type=audio.content_type,
            body=body,
        )
    except SessionWorkflowError as error:
        return _error_response(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    return JSONResponse(
        status_code=200,
        content=result.model_dump(mode="json"),
        headers={"Idempotency-Replayed": str(replayed).lower()},
    )


@router.post(
    "/{session_id}/understanding",
    response_model=MobileWorkflowResultV1,
    summary="Explicitly run optional narration then Vision V2 understanding",
)
def run_understanding(
    session_id: str,
    command: MobileWorkflowCommandV1,
    request: Request,
) -> JSONResponse:
    service: LiveImageDemoService | None = request.app.state.live_image_demo_service
    if service is None:
        error = SessionWorkflowError(
            code="IMAGE_DEMO_NOT_CONFIGURED",
            status_code=503,
            safe_message="The image-only demo service is not configured.",
        )
        return _error_response(
            error,
            request_id=command.request_id,
            session_id=command.session_id,
            expected_version=command.expected_session_version,
        )
    if command.session_id != session_id:
        error = SessionWorkflowError(
            code="SESSION_ID_MISMATCH",
            status_code=422,
            safe_message="The path and command session identifiers must match.",
        )
        return _error_response(
            error,
            request_id=command.request_id,
            session_id=command.session_id,
            expected_version=command.expected_session_version,
        )
    try:
        if command.payload.get("operation") == "SELECT_SUBJECT":
            result, replayed = service.select_subject(command)
        else:
            result, replayed = service.run_understanding(command)
    except SessionWorkflowError as error:
        return _error_response(
            error,
            request_id=command.request_id,
            session_id=command.session_id,
            expected_version=command.expected_session_version,
        )
    return JSONResponse(
        status_code=200,
        content=result.model_dump(mode="json"),
        headers={"Idempotency-Replayed": str(replayed).lower()},
    )


@router.get(
    "/{session_id}/understanding/progress",
    response_model=MobileWorkflowResultV1,
    summary="Read the last sanitized understanding stage projection",
)
def read_understanding_progress(
    session_id: str,
    request: Request,
    request_id: str = Header(default="progress-read"),
    expected_session_version: int = Header(default=0, alias="X-Expected-Session-Version"),
) -> JSONResponse:
    service: LiveImageDemoService | None = request.app.state.live_image_demo_service
    if service is None:
        error = SessionWorkflowError(
            code="IMAGE_DEMO_NOT_CONFIGURED",
            status_code=503,
            safe_message="The image-only demo service is not configured.",
        )
        return _error_response(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    try:
        result = service.read_understanding_progress(
            session_id=session_id,
            request_id=request_id,
            expected_version=expected_session_version,
        )
    except SessionWorkflowError as error:
        return _error_response(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    return JSONResponse(status_code=200, content=result.model_dump(mode="json"))


def _error_response(
    error: SessionWorkflowError,
    *,
    request_id: str,
    session_id: str,
    expected_version: int,
) -> JSONResponse:
    result = failure_result(
        request_id=request_id,
        session_id=session_id,
        expected_session_version=expected_version,
        observed_session_version=None,
        error=error,
    )
    return JSONResponse(status_code=error.status_code, content=result.model_dump(mode="json"))


__all__ = ["router"]
