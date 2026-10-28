"""Local-only lesson-source object-storage example; not the Lesson Library API."""

from __future__ import annotations

import hashlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import BinaryIO
from uuid import UUID, uuid4

from sketch2life.application.ports.object_storage import (
    ObjectStorageFailure,
    ObjectStoragePort,
    ReadableObjectBody,
)

_READ_CHUNK_BYTES = 256 * 1024
_SPOOL_MEMORY_BYTES = 1024 * 1024
_ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


class StorageExampleRejected(ValueError):
    pass


class StorageExampleTooLarge(StorageExampleRejected):
    pass


class StorageExampleNotFound(LookupError):
    pass


class StorageExampleUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class StorageExampleReceipt:
    object_id: str
    file_name: str
    content_type: str
    byte_length: int
    sha256: str


@dataclass(frozen=True, slots=True)
class StorageExampleDownload:
    file_name: str
    content_type: str
    content_length: int
    sha256: str
    body: ReadableObjectBody


class StorageExampleService:
    _KEY_PREFIX = "lesson-source-examples"

    def __init__(self, storage: ObjectStoragePort, *, max_upload_bytes: int) -> None:
        self._storage = storage
        self._max_upload_bytes = max_upload_bytes

    def upload(
        self, source: BinaryIO, *, file_name: str, client_content_type: str | None
    ) -> StorageExampleReceipt:
        safe_name = self._safe_file_name(file_name)
        extension = PurePosixPath(safe_name).suffix.lower()
        expected_type = _ALLOWED_TYPES.get(extension)
        if expected_type is None:
            raise StorageExampleRejected("Only PDF, DOCX, and PPTX examples are accepted")

        supplied_type = (client_content_type or "").split(";", maxsplit=1)[0].strip().lower()
        if supplied_type and supplied_type not in {expected_type, "application/octet-stream"}:
            raise StorageExampleRejected("File extension and media type do not match")

        digest = hashlib.sha256()
        byte_length = 0
        object_id = uuid4().hex
        object_key = f"{self._KEY_PREFIX}/{object_id}"

        try:
            with tempfile.SpooledTemporaryFile(
                max_size=min(_SPOOL_MEMORY_BYTES, self._max_upload_bytes), mode="w+b"
            ) as buffered:
                while chunk := source.read(_READ_CHUNK_BYTES):
                    byte_length += len(chunk)
                    if byte_length > self._max_upload_bytes:
                        raise StorageExampleTooLarge("File exceeds the configured upload limit")
                    digest.update(chunk)
                    buffered.write(chunk)
                if byte_length == 0:
                    raise StorageExampleRejected("Empty files cannot be uploaded")

                sha256 = digest.hexdigest()
                buffered.seek(0)
                self._storage.put_object(
                    object_key,
                    buffered,
                    content_type=expected_type,
                    content_length=byte_length,
                    metadata={"sha256": sha256, "file_name": safe_name},
                )
        except ObjectStorageFailure as exc:
            raise StorageExampleUnavailable("Object storage is temporarily unavailable") from exc

        return StorageExampleReceipt(
            object_id=object_id,
            file_name=safe_name,
            content_type=expected_type,
            byte_length=byte_length,
            sha256=sha256,
        )

    def download(self, object_id: str) -> StorageExampleDownload:
        object_key = self._object_key(object_id)
        try:
            stored = self._storage.get_object(object_key)
        except ObjectStorageFailure as exc:
            raise StorageExampleUnavailable("Object storage is temporarily unavailable") from exc
        if stored is None:
            raise StorageExampleNotFound("Object was not found")

        file_name = self._safe_file_name(stored.metadata.get("file_name", "lesson-source.pdf"))
        return StorageExampleDownload(
            file_name=file_name,
            content_type=stored.content_type,
            content_length=stored.content_length,
            sha256=stored.metadata.get("sha256", ""),
            body=stored.body,
        )

    def delete(self, object_id: str) -> None:
        object_key = self._object_key(object_id)
        try:
            self._storage.delete_object(object_key)
        except ObjectStorageFailure as exc:
            raise StorageExampleUnavailable("Object storage is temporarily unavailable") from exc

    @staticmethod
    def _safe_file_name(file_name: str) -> str:
        basename = (file_name or "").replace("\\", "/").rsplit("/", maxsplit=1)[-1].strip()
        if not basename or basename in {".", ".."}:
            raise StorageExampleRejected("A file name is required")
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", basename)[:120]
        if not safe_name:
            raise StorageExampleRejected("A valid file name is required")
        return safe_name

    @classmethod
    def _object_key(cls, object_id: str) -> str:
        try:
            canonical_id = UUID(object_id).hex
        except (ValueError, AttributeError) as exc:
            raise StorageExampleNotFound("Object was not found") from exc
        return f"{cls._KEY_PREFIX}/{canonical_id}"


__all__ = [
    "StorageExampleDownload",
    "StorageExampleNotFound",
    "StorageExampleReceipt",
    "StorageExampleRejected",
    "StorageExampleService",
    "StorageExampleTooLarge",
    "StorageExampleUnavailable",
]
