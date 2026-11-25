from __future__ import annotations

import inspect
from typing import Any

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from sketch2life.domain.lesson_library.model import (
    LessonLibraryRuleError,
    canonical_content_hash,
    remix_request_fingerprint,
    verify_remix_source_content,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key


def _content() -> dict[str, Any]:
    return {
        "locale": "vi-VN",
        "title": "Bài học mẫu",
        "topic": "Quan sát",
        "target_age_band_ref": "age-3-6",
        "target_age_band_version": 1,
        "objectives": ["Quan sát chi tiết"],
        "drawing_subject": "Lá cây",
        "drawing_steps_text": "Nhìn đường viền trước.",
        "subject_learning_notes": "Lá có gân.",
        "script_direction": None,
        "script_following_allowed": False,
        "activities": [
            {
                "title": "Tìm lá",
                "objective": "Quan sát lá",
                "materials_text": "",
                "preparation_text": "",
                "instructions_text": "Tìm một chiếc lá.",
                "observation_notes": "",
                "safety_notes": "",
                "activity_kind": "outdoor",
            },
            {
                "title": "Vẽ gân lá",
                "objective": "Nhận biết gân",
                "materials_text": "Bút chì",
                "preparation_text": "",
                "instructions_text": "Vẽ các đường gân.",
                "observation_notes": "",
                "safety_notes": "",
                "activity_kind": "indoor",
            },
        ],
    }


class _ActivityRows:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> _ActivityRows:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows

    def __iter__(self) -> Any:
        return iter(self._rows)


class _ActivitySession:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.statement = None

    def execute(self, statement: Any) -> _ActivityRows:
        self.statement = statement
        return _ActivityRows(self.rows)


def test_remix_reconstructs_ordered_content_and_hash() -> None:
    expected = _content()
    session = _ActivitySession(
        [{"activity_json": item} for item in expected["activities"]]
    )
    service = LessonLibraryService(
        session, storage=None, parser=None, scanner=None  # type: ignore[arg-type]
    )

    reconstructed = service._full_content(
        {
            "version_id": "source-version",
            "content_json": {key: value for key, value in expected.items() if key != "activities"},
        }
    )

    assert reconstructed == expected
    assert "activity_order" in str(session.statement)
    assert verify_remix_source_content(
        reconstructed,
        stored_hash=canonical_content_hash(expected),
        requested_hash=canonical_content_hash(expected),
    ) == canonical_content_hash(expected)


def test_remix_rejects_bad_source_hash_after_guard() -> None:
    content = _content()
    stored_hash = canonical_content_hash(content)
    with pytest.raises(LessonLibraryRuleError, match="STALE_SOURCE_VERSION") as error:
        verify_remix_source_content(
            content,
            stored_hash=stored_hash,
            requested_hash="0" * 64,
        )
    assert error.value.code == "STALE_SOURCE_VERSION"

    source = inspect.getsource(LessonLibraryService._attempt_public_remix)
    assert source.index("_load_public_remix_source") < source.index("_verified_remix_hash")
    assert source.index("_verified_remix_hash") < source.index("_find_remix_receipt")


def test_remix_fingerprint_binds_destination_and_exact_source() -> None:
    common = {
        "destination_organization_id": "destination-a",
        "lesson_id": "lesson-source",
        "source_version_id": "version-a",
        "source_content_sha256": "a" * 64,
    }
    original = remix_request_fingerprint(**common)
    assert remix_request_fingerprint(
        **{**common, "destination_organization_id": "destination-b"}
    ) != original
    assert remix_request_fingerprint(**{**common, "source_version_id": "version-b"}) != original
    assert remix_request_fingerprint(**{**common, "source_content_sha256": "b" * 64}) != original
    assert remix_request_fingerprint(**{**common, "lesson_id": "another-lesson"}) != original


def test_remix_no_ai_or_source_mutation() -> None:
    operation = inspect.getsource(LessonLibraryService._attempt_public_remix)
    guard = inspect.getsource(LessonLibraryService._load_public_remix_source)
    assert "parser" not in operation and "scanner" not in operation
    assert "LIBRARY_ITEMS.insert" in operation
    assert "LIBRARY_VERSION_LINEAGE.insert" in operation
    assert ".update(" not in operation
    assert ".update(" not in guard
    assert "ACCESS_GRANTS.update" not in operation
    assert "LIBRARY_VERSIONS.update" not in operation


def _request_with_keys(*values: str) -> Request:
    headers = [(b"idempotency-key", value.encode("latin-1")) for value in values]
    return Request({"type": "http", "method": "POST", "path": "/remixes", "headers": headers})


def test_remix_key_parser_visible_ascii_bounds() -> None:
    assert parse_idempotency_key(_request_with_keys("K")) == "K"
    assert len(parse_idempotency_key(_request_with_keys("K" * 128))) == 128
    for value in ("", "K" * 129, "has space", "bad\x7f", "bad\x80"):
        with pytest.raises(HTTPException) as error:
            parse_idempotency_key(_request_with_keys(value))
        assert error.value.status_code == 400
    with pytest.raises(HTTPException) as missing:
        parse_idempotency_key(_request_with_keys())
    assert missing.value.status_code == 400
    with pytest.raises(HTTPException) as duplicate:
        parse_idempotency_key(_request_with_keys("one", "two"))
    assert duplicate.value.status_code == 400


def test_remix_receipt_conflict_matches_the_real_receipt_primary_key_name() -> None:
    from sqlalchemy.exc import IntegrityError

    # Name created by migration 20261119_ar_0002_be1_command_receipts.
    class _Diag:
        constraint_name = "pk_be1_command_receipts"

    class _Orig(Exception):
        sqlstate = "23505"
        diag = _Diag()

    exc = IntegrityError("insert", {}, _Orig())
    assert LessonLibraryService._is_remix_receipt_conflict(exc) is True

    _Orig.sqlstate = "23503"
    assert LessonLibraryService._is_remix_receipt_conflict(exc) is False
