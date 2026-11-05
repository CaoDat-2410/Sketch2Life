"""Versioned routes for the separate local StoryRun-lite demo application."""

from __future__ import annotations

import uuid
from typing import Annotated, cast

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from sketch2life.application.ports.story_run_lite import CommandResult
from sketch2life.application.services.story_run_lite import StoryRunLiteService
from sketch2life.contracts.schemas.ai_story import (
    ConfirmStoryRevisionRequest,
    ParentStoryGenerationRequest,
)
from sketch2life.contracts.schemas.story_run_lite import (
    AttachAssetRequest,
    CancelRunRequest,
    CompleteUploadRequest,
    ConfirmSubjectRequest,
    CreateRunRequest,
    CreateUploadRequest,
)
from sketch2life.domain.story_run_lite import MAX_PART_BYTES, StoryRunLiteError, etag

router = APIRouter(prefix="/v1")
_RETRY_AFTER_SECONDS = "1"


def _service(request: Request) -> StoryRunLiteService:
    runtime = getattr(request.app.state, "story_run_lite_runtime", None)
    if runtime is not None:
        runtime.repository.require_singleton_lock()
    service = getattr(request.app.state, "story_run_lite_service", None)
    if service is None:
        raise StoryRunLiteError(
            503, "SERVICE_NOT_READY", "StoryRun-lite runtime is not configured.", retryable=True
        )
    return cast(StoryRunLiteService, service)


def _result(result: CommandResult) -> JSONResponse:
    body = result.body
    status_code = result.status_code
    version = result.resource_version
    headers = {"Cache-Control": "no-store"}
    if version is not None:
        headers["ETag"] = etag(int(version))
    if status_code == 202:
        if isinstance(body.get("run_ref"), str):
            if isinstance(body.get("story_revision_ref"), str):
                headers["Location"] = (
                    f"/v1/story-runs/{body['run_ref']}/story-revisions/{body['story_revision_ref']}"
                )
            else:
                headers["Location"] = f"/v1/story-runs/{body['run_ref']}"
        elif isinstance(body.get("upload_ref"), str):
            headers["Location"] = f"/v1/upload-sessions/{body['upload_ref']}"
        else:
            raise RuntimeError("A 202 response must identify its pollable resource.")
        headers["Retry-After"] = _RETRY_AFTER_SECONDS
    return JSONResponse(body, status_code=status_code, headers=headers)


@router.post("/story-runs")
def create_run(
    payload: CreateRunRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> JSONResponse:
    return _result(_service(request).create_run(payload, idempotency_key=idempotency_key))


@router.get("/story-runs/readiness")
def readiness(request: Request) -> JSONResponse:
    """Report readiness of the configured StoryRun runtime and its pinned singleton session."""

    runtime = getattr(request.app.state, "story_run_lite_runtime", None)
    if runtime is None or getattr(request.app.state, "story_run_lite_service", None) is None:
        raise StoryRunLiteError(
            503, "SERVICE_NOT_READY", "StoryRun-lite runtime is not configured.", retryable=False
        )
    runtime.ensure_ready()
    return JSONResponse(
        {"status": "ready", "service": "storyrun-lite"},
        headers={"Cache-Control": "no-store"},
    )


@router.get("/story-runs/{run_ref}")
def get_run(run_ref: str, request: Request) -> JSONResponse:
    return _result(_service(request).get_run(run_ref))


@router.post("/story-runs/{run_ref}/assets")
def attach_asset(
    run_ref: str,
    payload: AttachAssetRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> JSONResponse:
    return _result(
        _service(request).attach_asset(
            run_id=run_ref,
            request=payload,
            if_match=if_match,
            idempotency_key=idempotency_key,
        )
    )


@router.post("/story-runs/{run_ref}/subject-confirmation")
def confirm_subject(
    run_ref: str,
    payload: ConfirmSubjectRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> JSONResponse:
    return _result(
        _service(request).confirm_subject(
            run_id=run_ref,
            request=payload,
            if_match=if_match,
            idempotency_key=idempotency_key,
        )
    )


@router.post("/story-runs/{run_ref}/story-revisions")
def generate_story_revision(
    run_ref: str,
    payload: ParentStoryGenerationRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> JSONResponse:
    return _result(
        _service(request).generate_story_revision(
            run_id=run_ref,
            request=payload,
            if_match=if_match,
            idempotency_key=idempotency_key,
        )
    )


@router.get("/story-runs/{run_ref}/story-revisions/{story_revision_ref}")
def get_story_revision(run_ref: str, story_revision_ref: str, request: Request) -> JSONResponse:
    return _result(
        _service(request).get_story_revision(run_id=run_ref, story_revision_id=story_revision_ref)
    )


@router.post("/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation")
def confirm_story_revision(
    run_ref: str,
    story_revision_ref: str,
    payload: ConfirmStoryRevisionRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> JSONResponse:
    return _result(
        _service(request).confirm_story_revision(
            run_id=run_ref,
            story_revision_id=story_revision_ref,
            request=payload,
            if_match=if_match,
            idempotency_key=idempotency_key,
        )
    )


@router.post("/story-runs/{run_ref}/cancel")
def cancel_run(
    run_ref: str,
    payload: CancelRunRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> JSONResponse:
    return _result(
        _service(request).cancel_run(
            run_id=run_ref,
            request=payload,
            if_match=if_match,
            idempotency_key=idempotency_key,
        )
    )


@router.post("/upload-sessions")
def create_upload(
    payload: CreateUploadRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> JSONResponse:
    return _result(_service(request).create_upload(payload, idempotency_key=idempotency_key))


@router.put("/upload-sessions/{upload_ref}/parts/{part_no}")
async def put_upload_part(
    upload_ref: str,
    part_no: int,
    request: Request,
    content_length: Annotated[str | None, Header(alias="Content-Length")] = None,
    content_sha256: Annotated[str | None, Header(alias="Content-SHA256")] = None,
) -> JSONResponse:
    if content_length is None:
        raise StoryRunLiteError(
            411, "CONTENT_LENGTH_REQUIRED", "Content-Length is required for a bounded raw part."
        )
    try:
        declared_length = int(content_length)
    except ValueError:
        raise StoryRunLiteError(
            400, "INVALID_CONTENT_LENGTH", "Content-Length must be a positive integer."
        ) from None
    if declared_length < 1:
        raise StoryRunLiteError(
            400, "INVALID_CONTENT_LENGTH", "Content-Length must be a positive integer."
        )
    if declared_length > MAX_PART_BYTES:
        raise StoryRunLiteError(413, "PART_TOO_LARGE", "The part exceeds part_size_bytes.")
    if content_sha256 is None:
        raise StoryRunLiteError(
            400, "PART_HASH_REQUIRED", "Content-SHA256 is required for each part."
        )
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/octet-stream":
        raise StoryRunLiteError(
            415, "UNSUPPORTED_MEDIA_TYPE", "Upload parts must use application/octet-stream."
        )

    chunks: list[bytes] = []
    received = 0
    async for chunk in request.stream():
        received += len(chunk)
        if received > MAX_PART_BYTES or received > declared_length:
            raise StoryRunLiteError(
                413, "PART_TOO_LARGE", "The raw part exceeded its declared bounded size."
            )
        chunks.append(chunk)
    if received != declared_length:
        raise StoryRunLiteError(
            400, "CONTENT_LENGTH_MISMATCH", "Content-Length must match the raw part bytes."
        )
    result = _service(request).put_part(
        upload_id=upload_ref,
        part_number=part_no,
        payload=b"".join(chunks),
        declared_length=declared_length,
        declared_sha256=content_sha256,
    )
    return _result(result)


@router.post("/upload-sessions/{upload_ref}/complete")
def complete_upload(
    upload_ref: str,
    payload: CompleteUploadRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> JSONResponse:
    return _result(
        _service(request).complete_upload(
            upload_id=upload_ref,
            request=payload,
            if_match=if_match,
            idempotency_key=idempotency_key,
        )
    )


@router.get("/upload-sessions/{upload_ref}")
def get_upload(upload_ref: str, request: Request) -> JSONResponse:
    return _result(_service(request).get_upload(upload_ref))


@router.delete("/upload-sessions/{upload_ref}")
def abort_upload(
    upload_ref: str,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> JSONResponse:
    return _result(
        _service(request).abort_upload(
            upload_id=upload_ref,
            if_match=if_match,
            idempotency_key=idempotency_key,
        )
    )


async def story_error_response(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StoryRunLiteError):
        raise TypeError("StoryRun-lite error handler requires StoryRunLiteError")
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    body = {
        "code": exc.code,
        "message": exc.message,
        "correlation_id": correlation_id,
        "retryable": exc.retryable,
        "field_errors": exc.field_errors or None,
    }
    return JSONResponse(body, status_code=exc.status_code, headers={"Cache-Control": "no-store"})


async def story_validation_error_response(request: Request, exc: object) -> JSONResponse:
    from fastapi.exceptions import RequestValidationError

    if not isinstance(exc, RequestValidationError):
        raise TypeError("StoryRun-lite validation handler requires RequestValidationError")
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    fields = [
        {
            "field": ".".join(str(part) for part in error.get("loc", ()) if part != "body"),
            "code": "INVALID_FIELD",
            "message": "The field is missing or has an invalid value.",
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        {
            "code": "INVALID_REQUEST",
            "message": "The request body or path parameters are invalid.",
            "correlation_id": correlation_id,
            "retryable": False,
            "field_errors": fields,
        },
        status_code=422,
        headers={"Cache-Control": "no-store"},
    )


async def story_unexpected_error_response(request: Request, _exc: Exception) -> JSONResponse:
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    return JSONResponse(
        {
            "code": "INTERNAL_ERROR",
            "message": "The request could not be completed.",
            "correlation_id": correlation_id,
            "retryable": False,
        },
        status_code=500,
        headers={"Cache-Control": "no-store"},
    )


def install_error_handlers(app: object) -> None:
    from fastapi import FastAPI
    from fastapi.exceptions import RequestValidationError

    if not isinstance(app, FastAPI):
        raise TypeError("StoryRun-lite error handlers require FastAPI")
    app.add_exception_handler(StoryRunLiteError, story_error_response)
    app.add_exception_handler(RequestValidationError, story_validation_error_response)
    app.add_exception_handler(Exception, story_unexpected_error_response)


__all__ = ["install_error_handlers", "router"]
