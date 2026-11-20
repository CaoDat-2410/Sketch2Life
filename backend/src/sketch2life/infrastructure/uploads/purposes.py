"""Upload purposes: accepted media types, size caps and codes (SRS l.983, l.545, l.1654).

``RUN_ARTWORK`` (Parent): JPEG, PNG or WebP, at most 20 MiB encoded (SRS l.983, l.1942); the 40
megapixel decode check belongs to T-2b. ``OCCURRENCE_DOCUMENT`` (Teacher): PDF, DOCX or PPTX, at
most 25,000,000 bytes (FR-T-06, l.545); page count and encryption checks belong to T-3b.
``RUN_AUDIO`` is deferred to T-2c: the SRS lists no audio type and the 2 minute rule needs a
decoder (l.982, l.1942), so it is declared but disabled.

Signatures are not repeated here: the shared table of ``upload_validation`` decides whether the
bytes match a declared type (T-2z).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from sketch2life.application.ports.upload_validation import DOCX_MEDIA_TYPE, PPTX_MEDIA_TYPE

RUN_ARTWORK: Final = "RUN_ARTWORK"
RUN_AUDIO: Final = "RUN_AUDIO"
OCCURRENCE_DOCUMENT: Final = "OCCURRENCE_DOCUMENT"

MAX_IMAGE_BYTES: Final = 20 * 1024 * 1024
MAX_DOCUMENT_BYTES: Final = 25_000_000

DOCUMENT_EXTENSIONS: Final[dict[str, str]] = {
    ".pdf": "application/pdf",
    ".docx": DOCX_MEDIA_TYPE,
    ".pptx": PPTX_MEDIA_TYPE,
}
IMAGE_EXTENSIONS: Final[dict[str, str]] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@dataclass(frozen=True, slots=True)
class UploadPurposePolicy:
    purpose: str
    account_role: str
    media_types: frozenset[str]
    max_bytes: int
    too_large_code: str
    unsupported_code: str
    needs_file_name: bool
    enabled: bool


POLICIES: Final[dict[str, UploadPurposePolicy]] = {
    RUN_ARTWORK: UploadPurposePolicy(
        purpose=RUN_ARTWORK,
        account_role="parent",
        media_types=frozenset(IMAGE_EXTENSIONS),
        max_bytes=MAX_IMAGE_BYTES,
        too_large_code="MEDIA_TOO_LARGE",
        unsupported_code="UNSUPPORTED_MEDIA_TYPE",
        needs_file_name=False,
        enabled=True,
    ),
    OCCURRENCE_DOCUMENT: UploadPurposePolicy(
        purpose=OCCURRENCE_DOCUMENT,
        account_role="teacher",
        media_types=frozenset(DOCUMENT_EXTENSIONS.values()),
        max_bytes=MAX_DOCUMENT_BYTES,
        too_large_code="LESSON_FILE_TOO_LARGE",
        unsupported_code="UNSUPPORTED_LESSON_TYPE",
        needs_file_name=True,
        enabled=True,
    ),
    RUN_AUDIO: UploadPurposePolicy(
        purpose=RUN_AUDIO,
        account_role="parent",
        media_types=frozenset(),
        max_bytes=20 * 1000 * 1000,
        too_large_code="AUDIO_TOO_LARGE",
        unsupported_code="UNSUPPORTED_MEDIA_TYPE",
        needs_file_name=False,
        enabled=False,
    ),
}
# Purposes the generic routes serve. ``LESSON_SOURCE`` stays on the lesson routes (P-17) and
# ``PROFILE_IMAGE`` has no producer; every other value is invisible to these routes.
GENERIC_PURPOSES: Final = frozenset(POLICIES)


def safe_document_name(raw: str) -> str:
    """Last path segment without control characters; empty when nothing usable remains."""
    name = raw.replace("\\", "/").rsplit("/", 1)[-1]
    return "".join(char for char in name if ord(char) >= 32 and ord(char) != 127).strip()


def document_media_type_for(file_name: str) -> str | None:
    suffix = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    return DOCUMENT_EXTENSIONS.get(suffix)


__all__ = [
    "GENERIC_PURPOSES",
    "MAX_DOCUMENT_BYTES",
    "MAX_IMAGE_BYTES",
    "OCCURRENCE_DOCUMENT",
    "POLICIES",
    "RUN_ARTWORK",
    "RUN_AUDIO",
    "UploadPurposePolicy",
    "document_media_type_for",
    "safe_document_name",
]
