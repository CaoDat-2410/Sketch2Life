"""Provider-neutral object-storage boundary for application use cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Mapping, Protocol


class ObjectStorageFailure(RuntimeError):
    """Raised when an object-storage operation cannot be completed."""


class ReadableObjectBody(Protocol):
    def read(self, size: int = -1) -> bytes: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class StoredObject:
    body: ReadableObjectBody
    content_length: int
    content_type: str
    metadata: Mapping[str, str]


class ObjectStoragePort(Protocol):
    def put_object(
        self,
        key: str,
        body: BinaryIO,
        *,
        content_type: str,
        content_length: int,
        metadata: Mapping[str, str],
    ) -> None: ...

    def get_object(self, key: str) -> StoredObject | None: ...

    def delete_object(self, key: str) -> None: ...


__all__ = [
    "ObjectStorageFailure",
    "ObjectStoragePort",
    "ReadableObjectBody",
    "StoredObject",
]
