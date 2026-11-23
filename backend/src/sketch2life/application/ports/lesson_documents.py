"""Ports for deterministic lesson-document parsing and malware scanning."""

from __future__ import annotations

import hashlib
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
    # Full extracted text, normalised (no NUL or other control character, no lone surrogate) and
    # at most 2 MiB of UTF-8. Added for the occurrence document attach (FEAT-066 T-3b); the lesson
    # library ignores it, hence the default.
    extracted_text: str = ""


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


def scanner_identity_sha256(scanner_name: str, scanner_version: str) -> str:
    """SHA-256 of the scanner identity (name, NUL, version), the Parent lineage formula.

    ``core_asset_lineage.scanner_sha256`` is written with this value by the Parent artwork
    repository. The StoryRun-lite writer stores a content digest in the same column (finding
    F-1); this helper does not settle that meaning, it only names the Parent one.
    """
    return hashlib.sha256(f"{scanner_name}\0{scanner_version}".encode()).hexdigest()


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
    "scanner_identity_sha256",
]
