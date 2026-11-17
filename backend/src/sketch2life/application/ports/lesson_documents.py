"""Ports for deterministic lesson-document parsing and malware scanning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Protocol


@dataclass(frozen=True, slots=True)
class LessonDocumentExtraction:
    detected_media_type: str
    parser_name: str
    parser_version: str
    page_or_slide_count: int | None
    page_coverage: tuple[int, ...]
    extracted_fields: dict[str, object]
    warnings: tuple[str, ...]


class LessonDocumentParser(Protocol):
    def extract(self, file_obj: BinaryIO, *, file_extension: str) -> LessonDocumentExtraction: ...


class MalwareScanner(Protocol):
    def scan(self, file_obj: BinaryIO) -> MalwareScanResult:
        """Return a CLEAN verdict with scanner provenance or raise a safe error."""
        ...


@dataclass(frozen=True, slots=True)
class MalwareScanResult:
    scanner_name: str
    scanner_version: str
    verdict: str


class LessonDocumentRejected(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class MalwareScannerUnavailable(RuntimeError):
    pass


class MalwareDetected(ValueError):
    pass


__all__ = [
    "LessonDocumentExtraction",
    "LessonDocumentParser",
    "LessonDocumentRejected",
    "MalwareDetected",
    "MalwareScanResult",
    "MalwareScanner",
    "MalwareScannerUnavailable",
]
