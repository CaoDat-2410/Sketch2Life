"""Generic upload sessions for Parent artwork and Teacher occurrence documents (SRS l.1654-1658).

Literal paths under ``/v1/upload-sessions`` (TD-01, C-D9). Lesson sources stay on the Lesson
Library routes (P-17); a lesson session id answers 404 here and a generic id answers 404 there.

This router is mounted only while the StoryRun-lite main demo is off: the demo router owns the
same literal paths with another contract (``story_demo_replaced_routers`` records it).
"""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, Response, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.upload_sessions import (
    UPLOAD_MAX_PARTS,
    UPLOAD_PART_SIZE_BYTES,
)
from sketch2life.contracts.schemas.upload_sessions import (
    CompleteGenericUploadRequestV1,
    CreateGenericUploadRequestV1,
    GenericUploadCompletionV1,
    GenericUploadPartReceiptV1,
    GenericUploadSessionV1,
)
from sketch2life.infrastructure.uploads.resolvers import merged_resolver_factories
from sketch2life.infrastructure.uploads.service import UploadSessionError, UploadSessionService
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key, raise_stale_revision
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/v1/upload-sessions", tags=["Upload Sessions"])

IdempotencyKeyHeader = Annotated[
    str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
]
UploadId = Annotated[str, Path(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")]
_ETAG = re.compile(r'^"([1-9][0-9]*)"$')
_OCTET_STREAM = "application/octet-stream"


def get_upload_session_service(
    request: Request, db: Session = Depends(get_db)
) -> UploadSessionService:
    state = request.app.state
    storage = getattr(state, "lesson_library_storage", None)
    scanner = getattr(state, "lesson_document_scanner", None)
    if storage is None or scanner is None:
        raise HTTPException(status_code=503, detail={"code": "STORAGE_UNAVAILABLE"})
    return UploadSessionService(
        db,
        storage=storage,
        scanner=scanner,
        validator=getattr(state, "upload_media_validator", None),
        resolvers=merged_resolver_factories(
            getattr(state, "upload_target_resolver_factories", None)
        ),
    )


def _raise(exc: UploadSessionError) -> NoReturn:
    if exc.code == "STALE_REVISION" and exc.current_revision is not None:
        raise_stale_revision(current_version=exc.current_revision, etag=str(exc.current_revision))
    detail: dict[str, Any] = {"code": exc.code}
    if exc.field_errors:
        detail["field_errors"] = exc.field_errors
    raise HTTPException(status_code=exc.status_code, detail=detail) from None


def _call[Result](function: Callable[[], Result]) -> Result:
    try:
        return function()
    except UploadSessionError as exc:
        _raise(exc)


def _strong_revision(if_match: str | None) -> int:
    """C-D7: a strong ``If-Match`` carrying the derived session revision."""
    if if_match is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": "If-Match", "code": "REQUIRED"}],
            },
        )
    match = _ETAG.fullmatch(if_match.strip())
    if match is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": "If-Match", "code": "INVALID_FORMAT"}],
            },
        )
    return int(match.group(1))


def _etag(response: Response, revision: int) -> None:
    response.headers["ETag"] = f'"{revision}"'


@router.post(
    "",
    response_model=GenericUploadSessionV1,
    status_code=status.HTTP_201_CREATED,
    summary="Create an upload session for a Parent run artwork or an occurrence document",
)
def create_upload_session(
    payload: CreateGenericUploadRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: UploadSessionService = Depends(get_upload_session_service),
) -> dict[str, Any]:
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.create_session(
            principal=principal, payload=payload, idempotency_key=key
        )
    )
    _etag(response, result["revision"])
    return result


@router.get(
    "/{upload_id}",
    response_model=GenericUploadSessionV1,
    summary="Read an upload session: state, accepted parts, byte count and expiry",
)
def get_upload_session(
    upload_id: UploadId,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: UploadSessionService = Depends(get_upload_session_service),
) -> dict[str, Any]:
    result = _call(lambda: service.get_session(principal=principal, upload_id=upload_id))
    _etag(response, result["revision"])
    return result


@router.put(
    "/{upload_id}/parts/{part_no}",
    response_model=GenericUploadPartReceiptV1,
    summary="Upload one raw part (at most 4 MiB) with its SHA-256",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {_OCTET_STREAM: {"schema": {"type": "string", "format": "binary"}}},
        }
    },
)
async def put_upload_part(
    upload_id: UploadId,
    part_no: Annotated[int, Path(ge=1, le=UPLOAD_MAX_PARTS)],
    request: Request,
    response: Response,
    x_part_sha256: Annotated[str, Header(alias="X-Part-SHA256", pattern=r"^[0-9a-f]{64}$")],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: UploadSessionService = Depends(get_upload_session_service),
) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != _OCTET_STREAM:
        raise HTTPException(status_code=415, detail={"code": "UNSUPPORTED_MEDIA_TYPE"})
    declared = request.headers.get("content-length", "")
    oversize = declared.isdigit() and int(declared) > UPLOAD_PART_SIZE_BYTES
    chunks: list[bytes] = []
    received = 0
    if not oversize:
        async for chunk in request.stream():
            received += len(chunk)
            if received > UPLOAD_PART_SIZE_BYTES:
                oversize = True
                break
            chunks.append(chunk)
    body = b"" if oversize else b"".join(chunks)
    result = await run_in_threadpool(
        _call,
        lambda: service.put_part(
            principal=principal,
            upload_id=upload_id,
            part_no=part_no,
            body=body,
            oversize=oversize,
            part_sha256=x_part_sha256,
        ),
    )
    _etag(response, result["revision"])
    return result


@router.post(
    "/{upload_id}/complete",
    response_model=GenericUploadCompletionV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Verify the parts, the media type and the malware scan, then create the asset",
)
def complete_upload_session(
    upload_id: UploadId,
    payload: CompleteGenericUploadRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: UploadSessionService = Depends(get_upload_session_service),
) -> dict[str, Any]:
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.complete_session(
            principal=principal,
            upload_id=upload_id,
            expected_size_bytes=payload.expected_size_bytes,
            expected_sha256=payload.expected_sha256,
            idempotency_key=key,
        )
    )
    _etag(response, result["revision"])
    return result


@router.delete(
    "/{upload_id}",
    response_model=GenericUploadSessionV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Abort an open upload session (idempotent, strong If-Match)",
)
def abort_upload_session(
    upload_id: UploadId,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: UploadSessionService = Depends(get_upload_session_service),
) -> dict[str, Any]:
    key = parse_idempotency_key(request)
    expected_revision = _strong_revision(if_match)
    result = _call(
        lambda: service.abort_session(
            principal=principal,
            upload_id=upload_id,
            expected_revision=expected_revision,
            idempotency_key=key,
        )
    )
    _etag(response, result["revision"])
    return result
