"""Local-only S3-compatible storage examples; never part of the product API surface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Literal, NoReturn

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from sketch2life.application.ports.object_storage import ReadableObjectBody
from sketch2life.application.services.storage_example import (
    StorageExampleNotFound,
    StorageExampleRejected,
    StorageExampleService,
    StorageExampleTooLarge,
    StorageExampleUnavailable,
)

router = APIRouter(prefix="/api/dev/v1/storage-examples", tags=["local-storage-example"])


class StorageExampleUploadResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["StorageExampleUploadResponseV1"] = "StorageExampleUploadResponseV1"
    object_id: str
    file_name: str
    content_type: str
    byte_length: int
    sha256: str


def get_storage_example_service(request: Request) -> StorageExampleService:
    service = getattr(request.app.state, "storage_example_service", None)
    if not isinstance(service, StorageExampleService):
        raise HTTPException(status_code=404, detail="Not found")
    return service


def _raise_http_error(exc: Exception) -> NoReturn:
    if isinstance(exc, StorageExampleTooLarge):
        raise HTTPException(status_code=413, detail="File exceeds the configured upload limit")
    if isinstance(exc, StorageExampleRejected):
        raise HTTPException(status_code=415, detail=str(exc))
    if isinstance(exc, StorageExampleNotFound):
        raise HTTPException(status_code=404, detail="Object was not found")
    if isinstance(exc, StorageExampleUnavailable):
        raise HTTPException(status_code=503, detail="Object storage is temporarily unavailable")
    raise HTTPException(status_code=500, detail="Storage example failed")


@router.post(
    "/lesson-source-documents",
    response_model=StorageExampleUploadResponseV1,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a local lesson-source storage example",
)
def upload_lesson_source_example(
    file: UploadFile = File(...),
    service: StorageExampleService = Depends(get_storage_example_service),
) -> StorageExampleUploadResponseV1:
    try:
        receipt = service.upload(
            file.file,
            file_name=file.filename or "",
            client_content_type=file.content_type,
        )
    except (StorageExampleRejected, StorageExampleUnavailable) as exc:
        _raise_http_error(exc)
    finally:
        file.file.close()

    return StorageExampleUploadResponseV1(
        object_id=receipt.object_id,
        file_name=receipt.file_name,
        content_type=receipt.content_type,
        byte_length=receipt.byte_length,
        sha256=receipt.sha256,
    )


def _iter_body(body: ReadableObjectBody) -> Iterator[bytes]:
    try:
        while chunk := body.read(64 * 1024):
            yield chunk
    finally:
        body.close()


@router.get(
    "/lesson-source-documents/{object_id}",
    summary="Stream a local lesson-source storage example",
    response_class=StreamingResponse,
)
def download_lesson_source_example(
    object_id: str,
    service: StorageExampleService = Depends(get_storage_example_service),
) -> StreamingResponse:
    try:
        stored = service.download(object_id)
    except (StorageExampleNotFound, StorageExampleUnavailable) as exc:
        _raise_http_error(exc)

    return StreamingResponse(
        _iter_body(stored.body),
        media_type=stored.content_type,
        headers={
            "Content-Length": str(stored.content_length),
            "Content-Disposition": f'attachment; filename="{stored.file_name}"',
            "X-Content-SHA256": stored.sha256,
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete(
    "/lesson-source-documents/{object_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a local lesson-source storage example",
)
def delete_lesson_source_example(
    object_id: str,
    service: StorageExampleService = Depends(get_storage_example_service),
) -> None:
    try:
        service.delete(object_id)
    except (StorageExampleNotFound, StorageExampleUnavailable) as exc:
        _raise_http_error(exc)


__all__ = ["router"]
