"""Port for validating an assembled upload against its declared media type.

The port is optional: ``app.state.upload_media_validator`` is ``None`` unless a test double is
composed (T-2z). A later consumer (T-2a) may call the port or, when it is ``None``, use
``header_matches_media_type`` directly, so there is one signature table (SRS FR-C-12 l.504,
l.1657: an asset is usable only after hash, media validation and malware scan).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import BinaryIO, Protocol

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

HEADER_BYTES = 16

UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
UPLOAD_CONTENT_MISMATCH = "UPLOAD_CONTENT_MISMATCH"

_PNG = b"\x89PNG\r\n\x1a\n"
_ZIP_LOCAL_HEADER = b"PK\x03\x04"


def _is_riff(header: bytes, form: bytes) -> bool:
    return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == form


# Declared media type -> predicate over the first ``HEADER_BYTES`` bytes. Types only; the set of
# types each upload purpose accepts belongs to the purpose (T-2a, T-2c), not to this table.
_SIGNATURES: dict[str, Callable[[bytes], bool]] = {
    "image/png": lambda header: header.startswith(_PNG),
    "image/jpeg": lambda header: header.startswith(b"\xff\xd8\xff"),
    "image/webp": lambda header: _is_riff(header, b"WEBP"),
    "application/pdf": lambda header: header.startswith(b"%PDF-"),
    "audio/wav": lambda header: _is_riff(header, b"WAVE"),
    DOCX_MEDIA_TYPE: lambda header: header.startswith(_ZIP_LOCAL_HEADER),
    PPTX_MEDIA_TYPE: lambda header: header.startswith(_ZIP_LOCAL_HEADER),
}


def normalize_media_type(declared_media_type: str) -> str:
    return declared_media_type.strip().lower()


def is_known_media_type(declared_media_type: str) -> bool:
    return normalize_media_type(declared_media_type) in _SIGNATURES


def header_matches_media_type(declared_media_type: str, header: bytes) -> bool:
    """True when the leading bytes carry the signature of the declared type (pure, no I/O)."""
    check = _SIGNATURES.get(normalize_media_type(declared_media_type))
    return bool(check is not None and check(header[:HEADER_BYTES]))


@dataclass(frozen=True, slots=True)
class MediaValidationResult:
    detected_media_type: str
    validator_name: str
    validator_version: str


class UploadMediaRejected(ValueError):
    """Carries only a stable code: ``UNSUPPORTED_MEDIA_TYPE`` or ``UPLOAD_CONTENT_MISMATCH``."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class UploadMediaValidator(Protocol):
    def validate(self, file_obj: BinaryIO, *, declared_media_type: str) -> MediaValidationResult:
        """Return the validated type or raise ``UploadMediaRejected``."""
        ...


__all__ = [
    "DOCX_MEDIA_TYPE",
    "HEADER_BYTES",
    "PPTX_MEDIA_TYPE",
    "UNSUPPORTED_MEDIA_TYPE",
    "UPLOAD_CONTENT_MISMATCH",
    "MediaValidationResult",
    "UploadMediaRejected",
    "UploadMediaValidator",
    "header_matches_media_type",
    "is_known_media_type",
    "normalize_media_type",
]
