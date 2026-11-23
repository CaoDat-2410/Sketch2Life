"""Framework-independent rules of the occurrence source document (FEAT-066 goal v3, T-3b).

SRS l.545-546 (PDF, DOCX and PPTX up to 25 MB and 100 pages or slides, scan pages marked and never
read by OCR), l.1437 and §9.8 l.862-873 (safe stable refusal codes), l.1653 (attach a completed
upload), l.1699 (revisions and hashes). Nothing here knows HTTP, SQL or a framework.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Final

MAX_DOCUMENT_BYTES: Final = 25_000_000
MAX_TEXT_BYTES: Final = 2 * 1024 * 1024
MAX_REVISIONS_PER_DOCUMENT: Final = 50
ASSET_HANDLE_PREFIX: Final = "upl_"
CURSOR_MAX_LENGTH: Final = 512

JOB_PURPOSE_CODE: Final = "LESSON_SOURCE_EXTRACTION"
JOB_POLICY_ID: Final = "lesson.inline.v1"
RESULT_ARTIFACT_PREFIX: Final = "lesson-document-revision:"

OCR_PAGES_WARNING: Final = "OCR_NOT_SUPPORTED_PAGES"

# Parser rejection code -> (HTTP status, public code). New routes follow §9.8: an unsupported type
# is 415, a scan-only document is 422 ``OCR_NOT_SUPPORTED``, unreadable or hostile content is 400
# ``INVALID_FILE_CONTENT``. ``ENCRYPTED_DOCUMENT_UNSUPPORTED``, ``DOCUMENT_PAGE_LIMIT_EXCEEDED`` and
# ``DOCUMENT_TEXT_LIMIT_EXCEEDED`` are not named by §9.8; they keep the parser's own stable codes
# (T-3b-DEC-5, owner may rename). Anything unknown fails closed as ``INVALID_FILE_CONTENT``.
PARSER_REJECTIONS: Final[dict[str, tuple[int, str]]] = {
    "UNSUPPORTED_MEDIA_TYPE": (415, "UNSUPPORTED_LESSON_TYPE"),
    "OCR_NOT_SUPPORTED": (422, "OCR_NOT_SUPPORTED"),
    "INVALID_SOURCE_DOCUMENT": (400, "INVALID_FILE_CONTENT"),
    "DOCUMENT_EXPANSION_LIMIT_EXCEEDED": (400, "INVALID_FILE_CONTENT"),
    "ENCRYPTED_DOCUMENT_UNSUPPORTED": (422, "ENCRYPTED_DOCUMENT_UNSUPPORTED"),
    "DOCUMENT_PAGE_LIMIT_EXCEEDED": (422, "DOCUMENT_PAGE_LIMIT_EXCEEDED"),
    "DOCUMENT_TEXT_LIMIT_EXCEEDED": (422, "DOCUMENT_TEXT_LIMIT_EXCEEDED"),
}


class DocumentRuleError(ValueError):
    """A request value breaks a rule of the document routes; ``field`` names it."""

    def __init__(self, field: str, code: str) -> None:
        self.field = field
        self.code = code
        super().__init__(f"{field}:{code}")


def map_parser_rejection(code: str) -> tuple[int, str]:
    return PARSER_REJECTIONS.get(code, (400, "INVALID_FILE_CONTENT"))


def upload_id_from_handle(asset_ref: str) -> str | None:
    """The upload session id inside an opaque ``upl_`` handle, else ``None`` (SRS l.1692)."""
    if not asset_ref.startswith(ASSET_HANDLE_PREFIX):
        return None
    upload_id = asset_ref[len(ASSET_HANDLE_PREFIX) :]
    return upload_id if 0 < len(upload_id) <= 64 else None


def text_sha256(text: str) -> str:
    """SHA-256 of the UTF-8 bytes of the stored text (the database CHECK computes the same)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def storable_text_problem(text: str) -> str | None:
    """Why ``text`` cannot be stored, else ``None``: NUL, lone surrogate, empty or over 2 MiB."""
    if "\x00" in text:
        return "NUL"
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError:
        return "SURROGATE"
    if not encoded.strip():
        return "EMPTY"
    if len(encoded) > MAX_TEXT_BYTES:
        return "TOO_LARGE"
    return None


def edit_text_problem(text: str) -> str | None:
    """The field-error code of a Teacher-edited text, else ``None`` (T-3c-DEC-2).

    The text is stored exactly as sent, so the only rules are the ones the database cannot take:
    a lone surrogate or a NUL (``INVALID_FORMAT``), more than 2 MiB of UTF-8 bytes (``TOO_LONG``;
    the byte length, not the character count, is the limit) and a text that is blank after
    trimming (``EMPTY``). The encoding is strict, so a lone surrogate is a 400 and never a
    ``UnicodeEncodeError`` 500 later.
    """
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError:
        return "INVALID_FORMAT"
    if "\x00" in text:
        return "INVALID_FORMAT"
    if len(encoded) > MAX_TEXT_BYTES:
        return "TOO_LONG"
    if not text.strip():
        return "EMPTY"
    return None


def edit_fingerprint(expected_head_revision_no: int, text_hash: str) -> str:
    """Request fingerprint of a revision edit: the fence and the hash of the exact text."""
    canonical = json.dumps(
        {"expected_head_revision_no": expected_head_revision_no, "text_hash": text_hash},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def derive_warnings(
    parser_warnings: Sequence[str], page_or_slide_count: int | None, page_coverage: Sequence[int]
) -> list[str]:
    """Parser warnings plus ``OCR_NOT_SUPPORTED_PAGES`` when some pages have no text (UC-04).

    The parser reports which pages have text, not which have none; a document with some text and
    some blank or scan-only pages is accepted and the gap is marked (SRS l.545, l.1437, no OCR).
    A DOCX has no page count at HEAD, so it never carries this warning.
    """
    warnings = list(dict.fromkeys(parser_warnings))
    if (
        page_or_slide_count is not None
        and len(set(page_coverage)) < page_or_slide_count
        and OCR_PAGES_WARNING not in warnings
    ):
        warnings.append(OCR_PAGES_WARNING)
    return warnings


def revision_ref(document_revision_id: str) -> str:
    """The opaque artifact ref of a job result (no slash, so no storage URL can match)."""
    return f"{RESULT_ARTIFACT_PREFIX}{document_revision_id}"


def document_etag(head_revision_no: int) -> str:
    return f'"{head_revision_no}"'


def revision_etag(text_hash: str, review_state: str) -> str:
    """The text is immutable but the review stamp changes, so the hash alone is not a validator."""
    return f'"{text_hash}.{review_state}"'


def etag_matches(header: str | None, etag: str) -> bool:
    if header is None:
        return False
    return any(token.strip() in {etag, "*"} for token in header.split(","))


def _encode(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode(cursor: str, keys: frozenset[str]) -> dict[str, object]:
    try:
        if not 0 < len(cursor) <= CURSOR_MAX_LENGTH:
            raise ValueError
        encoded = cursor.encode("ascii")
        decoded = json.loads(
            base64.b64decode(encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
        )
        if not isinstance(decoded, dict) or set(decoded) != keys or decoded.get("v") != 1:
            raise ValueError
        if type(decoded["v"]) is not int:
            raise ValueError
        return decoded
    except (binascii.Error, json.JSONDecodeError, UnicodeError, ValueError):
        raise DocumentRuleError("cursor", "INVALID_FORMAT") from None


def encode_document_cursor(uploaded_at: datetime, source_document_id: str) -> str:
    return _encode({"k": "doc", "t": uploaded_at.isoformat(), "i": source_document_id, "v": 1})


def decode_document_cursor(cursor: str) -> tuple[datetime, str]:
    decoded = _decode(cursor, frozenset({"k", "t", "i", "v"}))
    try:
        uploaded_text, document_id = decoded["t"], decoded["i"]
        if decoded["k"] != "doc" or not isinstance(uploaded_text, str):
            raise ValueError
        if not isinstance(document_id, str) or not 0 < len(document_id) <= 36:
            raise ValueError
        uploaded_at = datetime.fromisoformat(uploaded_text)
        if uploaded_at.tzinfo is None or uploaded_at.utcoffset() is None:
            raise ValueError
        return uploaded_at.astimezone(UTC), document_id
    except ValueError:
        raise DocumentRuleError("cursor", "INVALID_FORMAT") from None


def encode_revision_cursor(revision_no: int) -> str:
    return _encode({"k": "rev", "n": revision_no, "v": 1})


def decode_revision_cursor(cursor: str) -> int:
    decoded = _decode(cursor, frozenset({"k", "n", "v"}))
    number = decoded["n"]
    if decoded["k"] != "rev" or type(number) is not int or number < 1:
        raise DocumentRuleError("cursor", "INVALID_FORMAT")
    return number


__all__ = [
    "ASSET_HANDLE_PREFIX",
    "JOB_POLICY_ID",
    "JOB_PURPOSE_CODE",
    "MAX_DOCUMENT_BYTES",
    "MAX_REVISIONS_PER_DOCUMENT",
    "MAX_TEXT_BYTES",
    "OCR_PAGES_WARNING",
    "PARSER_REJECTIONS",
    "RESULT_ARTIFACT_PREFIX",
    "DocumentRuleError",
    "decode_document_cursor",
    "decode_revision_cursor",
    "derive_warnings",
    "document_etag",
    "edit_fingerprint",
    "edit_text_problem",
    "encode_document_cursor",
    "encode_revision_cursor",
    "etag_matches",
    "map_parser_rejection",
    "revision_etag",
    "revision_ref",
    "storable_text_problem",
    "text_sha256",
    "upload_id_from_handle",
]
