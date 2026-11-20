"""FEAT-066 T-3c: unit tests of the text edit rules, the receipt and the request size guard.

No database. The text rules (SRS l.546, l.1437), the fingerprint and the schema are pure; the
receipt test uses a recording stand-in for the session; the ASGI guard is driven directly with
scripted messages so the streamed (no ``Content-Length``) case is covered without a server.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.lesson_occurrences import EditDocumentRevisionRequestV1
from sketch2life.domain.lesson_occurrences import documents as rules
from sketch2life.infrastructure.lesson_occurrences.documents import (
    EDIT_RECEIPT_SCOPE,
    DocumentError,
    OccurrenceDocumentService,
)
from sketch2life.interfaces.http.middleware.bounded_image_upload import (
    MAX_REVISION_EDIT_BODY_BYTES,
    BoundedImageUploadMiddleware,
)

TWO_MIB = 2 * 1024 * 1024


# ----------------------------------------------------------------------------- text rules
def test_the_text_limit_is_two_mib_of_utf8_bytes_and_the_cap_is_fifty() -> None:
    assert rules.MAX_TEXT_BYTES == TWO_MIB == 2_097_152
    assert rules.MAX_REVISIONS_PER_DOCUMENT == 50


@pytest.mark.parametrize(
    "text",
    [
        "a",
        "Tiêu đề: Vẽ con mèo\nBước 1",
        "  leading and trailing  ",
        "tab\tand\r\nCRLF\r\n",
        "\u0001\u001f control characters other than NUL are the Teacher's own text",
        "a" * TWO_MIB,
        "é" * (TWO_MIB // 2),  # 2 bytes each: exactly 2 MiB with half the characters
        "€" * (TWO_MIB // 3) + "ab",  # 3 bytes each: 2,097,152 bytes exactly
        "😀" * (TWO_MIB // 4),  # 4 bytes each, outside the BMP
    ],
    ids=[
        "one-char",
        "vietnamese",
        "padded",
        "crlf",
        "control",
        "ascii-at-limit",
        "two-byte-at-limit",
        "three-byte-at-limit",
        "four-byte-at-limit",
    ],
)
def test_texts_that_the_database_can_store_pass(text: str) -> None:
    assert len(text.encode("utf-8")) <= TWO_MIB
    assert rules.edit_text_problem(text) is None


def test_the_limit_counts_bytes_not_characters() -> None:
    at_limit = "é" * (TWO_MIB // 2)
    assert len(at_limit) == TWO_MIB // 2 and len(at_limit.encode()) == TWO_MIB
    assert rules.edit_text_problem(at_limit) is None
    assert rules.edit_text_problem(at_limit + "a") == "TOO_LONG"
    # fewer characters than the character cap, more bytes than the byte cap
    assert rules.edit_text_problem("€" * (TWO_MIB // 3 + 1)) == "TOO_LONG"
    assert rules.edit_text_problem("a" * (TWO_MIB + 1)) == "TOO_LONG"


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("", "EMPTY"),
        ("   ", "EMPTY"),
        ("\n\t\r\n", "EMPTY"),
        ("  　", "EMPTY"),
        ("co NUL \x00 giua", "INVALID_FORMAT"),
        ("\x00", "INVALID_FORMAT"),
        ("abc\ud800def", "INVALID_FORMAT"),  # a lone high surrogate
        ("\udc00", "INVALID_FORMAT"),  # a lone low surrogate
        ("abc\ud800\x00", "INVALID_FORMAT"),
    ],
)
def test_texts_that_cannot_be_stored_name_the_field_code(text: str, code: str) -> None:
    assert rules.edit_text_problem(text) == code


def test_a_lone_surrogate_never_reaches_encode_or_the_hash() -> None:
    bad = "abc\ud800def"
    with pytest.raises(UnicodeEncodeError):
        bad.encode("utf-8")
    assert rules.edit_text_problem(bad) == "INVALID_FORMAT"  # the guard answers instead


def test_line_endings_and_edge_whitespace_are_part_of_the_text() -> None:
    lf, crlf = "a\nb\n", "a\r\nb\r\n"
    assert rules.text_sha256(lf) != rules.text_sha256(crlf)
    assert rules.text_sha256(" a ") != rules.text_sha256("a")
    assert rules.text_sha256("Tiêu đề") == hashlib.sha256("Tiêu đề".encode()).hexdigest()


# ----------------------------------------------------------------------------- fingerprint
def test_the_fingerprint_binds_the_fence_and_the_exact_text_hash() -> None:
    first = rules.edit_fingerprint(2, rules.text_sha256("a"))
    assert len(first) == 64 and first == rules.edit_fingerprint(2, rules.text_sha256("a"))
    assert first != rules.edit_fingerprint(3, rules.text_sha256("a"))
    assert first != rules.edit_fingerprint(2, rules.text_sha256("b"))
    assert first != rules.edit_fingerprint(2, rules.text_sha256("a "))


# ----------------------------------------------------------------------------- schema
def test_the_request_keeps_the_text_exactly_and_forbids_anything_else() -> None:
    padded = "  a\r\n  "
    request = EditDocumentRevisionRequestV1(extracted_text=padded, expected_head_revision_no=2)
    assert request.extracted_text == padded  # no str_strip_whitespace
    assert EditDocumentRevisionRequestV1.model_config["extra"] == "forbid"
    assert not EditDocumentRevisionRequestV1.model_config.get("str_strip_whitespace")
    for bad in (
        {"extracted_text": "a", "expected_head_revision_no": 0},
        {"extracted_text": "a", "expected_head_revision_no": "1"},
        {"extracted_text": "a", "expected_head_revision_no": True},
        {"extracted_text": "", "expected_head_revision_no": 1},
        {"extracted_text": 1, "expected_head_revision_no": 1},
        {"extracted_text": "a", "expected_head_revision_no": 1, "origin": "EXTRACTION"},
        {"expected_head_revision_no": 1},
    ):
        with pytest.raises(ValidationError):
            EditDocumentRevisionRequestV1(**bad)  # type: ignore[arg-type]


# ----------------------------------------------------------------------------- errors
def test_a_stale_error_carries_the_head_as_an_integer_and_the_etag() -> None:
    error = DocumentError(409, "STALE_REVISION", current_version=4, etag="4")
    assert (error.status_code, error.code, error.current_version, error.etag) == (
        409,
        "STALE_REVISION",
        4,
        "4",
    )
    plain = DocumentError(409, "RESOURCE_CONFLICT")
    assert plain.current_version is None and plain.etag is None and plain.retry_after is None


# ----------------------------------------------------------------------------- receipt
class RecordingSession:
    """Collects the objects added to the session; any query is a test failure."""

    def __init__(self) -> None:
        self.added: list[Any] = []

    def add(self, row: Any) -> None:
        self.added.append(row)


def test_the_receipt_holds_references_only_never_the_text() -> None:
    session = RecordingSession()
    service = OccurrenceDocumentService(session, storage=None, parser=None)  # type: ignore[arg-type]
    text = "Một đoạn văn bản rất dài " * 5000
    principal = VerifiedPrincipal(subject="subject-1", issuer="issuer", roles=frozenset())
    service._store_edit_receipt(
        principal,
        "occ-1",
        "doc-1",
        "key-1",
        "org-1",
        rules.edit_fingerprint(2, rules.text_sha256(text)),
        status_code=201,
        revision_id="rev-uuid",
        revision_no=3,
        review_state="NEEDS_REVIEW",
    )
    ((row),) = session.added
    assert row.operation_scope == EDIT_RECEIPT_SCOPE.format(
        occurrence_id="occ-1", document_id="doc-1"
    )
    assert row.operation_scope == ("POST /v1/lesson-occurrences/occ-1/documents/doc-1/revisions")
    assert row.response_json == {
        "status_code": 201,
        "document_revision_id": "rev-uuid",
        "revision_no": 3,
        "review_state": "NEEDS_REVIEW",
    }
    assert text not in json.dumps(row.response_json)
    assert len(json.dumps(row.response_json)) < 200
    assert len(row.request_fingerprint) == 64 and row.organization_id == "org-1"


def test_the_receipt_scope_fits_its_column_for_the_longest_ids() -> None:
    scope = EDIT_RECEIPT_SCOPE.format(occurrence_id="o" * 36, document_id="d" * 36)
    assert len(scope) <= 256


# ----------------------------------------------------------------------------- size guard
def test_the_body_cap_covers_the_worst_case_escaped_text() -> None:
    assert MAX_REVISION_EDIT_BODY_BYTES == 13 * 1024 * 1024
    worst = len(json.dumps({"extracted_text": "\u0001" * TWO_MIB, "expected_head_revision_no": 1}))
    assert 6 * TWO_MIB < worst < MAX_REVISION_EDIT_BODY_BYTES
    worst_non_bmp = len(
        json.dumps({"extracted_text": "😀" * (TWO_MIB // 4), "expected_head_revision_no": 1})
    )
    assert worst_non_bmp < worst  # 12 bytes for four: three per byte, below the control case


EDIT_PATH = "/v1/lesson-occurrences/occ-1/documents/doc-1/revisions"


class Harness:
    """Runs the middleware around a scripted application and records what happened."""

    def __init__(self, *, swallow_with_400: bool = True) -> None:
        self.app_calls = 0
        self.body_seen = 0
        self.sent: list[dict[str, Any]] = []
        self.swallow_with_400 = swallow_with_400

    async def app(self, scope: Any, receive: Any, send: Any) -> None:
        self.app_calls += 1
        try:
            while True:
                message = await receive()
                self.body_seen += len(message.get("body", b""))
                if not message.get("more_body", False):
                    break
        except Exception:
            if not self.swallow_with_400:
                raise
            # what FastAPI does with any failure while it reads the body
            await send({"type": "http.response.start", "status": 400, "headers": []})
            await send({"type": "http.response.body", "body": b"{}"})
            return
        await send({"type": "http.response.start", "status": 201, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    def run(
        self,
        chunks: list[bytes],
        *,
        method: str = "POST",
        path: str = EDIT_PATH,
        content_length: int | None = None,
    ) -> None:
        headers: list[tuple[bytes, bytes]] = []
        if content_length is not None:
            headers.append((b"content-length", str(content_length).encode()))
        scope = {"type": "http", "method": method, "path": path, "headers": headers}
        pending = list(chunks)

        async def receive() -> dict[str, Any]:
            body = pending.pop(0) if pending else b""
            return {"type": "http.request", "body": body, "more_body": bool(pending)}

        async def send(message: dict[str, Any]) -> None:
            self.sent.append(message)

        middleware = BoundedImageUploadMiddleware(self.app)  # type: ignore[arg-type]
        asyncio.run(middleware(scope, receive, send))  # type: ignore[arg-type]

    @property
    def status(self) -> int:
        return int(next(m["status"] for m in self.sent if m["type"] == "http.response.start"))

    @property
    def body(self) -> dict[str, Any]:
        raw = b"".join(m.get("body", b"") for m in self.sent if m["type"] == "http.response.body")
        return dict(json.loads(raw))


def test_a_declared_length_over_the_cap_is_413_without_calling_the_application() -> None:
    harness = Harness()
    harness.run([b"x"], content_length=MAX_REVISION_EDIT_BODY_BYTES + 1)
    assert harness.status == 413 and harness.app_calls == 0
    assert harness.body["code"] == "MEDIA_TOO_LARGE" and harness.body["message"]
    assert len(harness.sent) == 2  # one start and one body, nothing else


def test_a_garbled_content_length_is_refused_as_too_large() -> None:
    harness = Harness()
    scope_headers = [(b"content-length", b"not-a-number")]
    scope = {"type": "http", "method": "POST", "path": EDIT_PATH, "headers": scope_headers}

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        harness.sent.append(message)

    asyncio.run(BoundedImageUploadMiddleware(harness.app)(scope, receive, send))  # type: ignore[arg-type]
    assert harness.status == 413 and harness.app_calls == 0


def test_a_streamed_body_over_the_cap_is_413_even_when_the_application_swallows_the_error() -> None:
    harness = Harness(swallow_with_400=True)
    chunk = b"a" * (1024 * 1024)
    harness.run([chunk] * 14)  # no Content-Length at all
    assert harness.status == 413 and harness.body["code"] == "MEDIA_TOO_LARGE"
    assert harness.body_seen <= MAX_REVISION_EDIT_BODY_BYTES  # the rest was never delivered
    assert [m["type"] for m in harness.sent].count("http.response.start") == 1


def test_a_streamed_body_over_the_cap_is_413_when_the_error_propagates() -> None:
    harness = Harness(swallow_with_400=False)
    harness.run([b"a" * (1024 * 1024)] * 14)
    assert harness.status == 413


def test_a_body_at_the_cap_reaches_the_application() -> None:
    harness = Harness()
    chunk = b"a" * (1024 * 1024)
    harness.run([chunk] * 12 + [b"a" * (1024 * 1024)], content_length=MAX_REVISION_EDIT_BODY_BYTES)
    assert harness.status == 201 and harness.app_calls == 1
    assert harness.body_seen == MAX_REVISION_EDIT_BODY_BYTES


def test_the_guard_matches_only_the_edit_route() -> None:
    for method, path in (
        ("GET", EDIT_PATH),
        ("POST", "/v1/lesson-occurrences/occ-1/documents"),
        ("POST", "/v1/lesson-occurrences/occ-1/documents/doc-1/revisions/2"),
        ("POST", "/v1/lesson-occurrences/occ-1/documents/doc-1/revisions/extra/more"),
        ("POST", "/v1/other/occ-1/documents/doc-1/revisions"),
    ):
        harness = Harness()
        harness.run(
            [b"x"], method=method, path=path, content_length=MAX_REVISION_EDIT_BODY_BYTES + 1
        )
        assert harness.app_calls == 1, (method, path)
        assert harness.status == 201
    trailing = Harness()
    trailing.run([b"x"], path=EDIT_PATH + "/", content_length=MAX_REVISION_EDIT_BODY_BYTES + 1)
    assert trailing.status == 413
