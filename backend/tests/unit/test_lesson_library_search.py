from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import DateTime, String, column, select

from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
    _decode_scoped_cursor,
    _encode_scoped_cursor,
    _escape_like_literal,
    _normalize_search_filters,
    _scoped_cursor_filter,
)


def test_search_filter_normalization_and_bounds() -> None:
    normalized = _normalize_search_filters(
        q="  Bướm  ",
        topic="  Côn trùng  ",
        target_age_band_ref="age-3-6",
        target_age_band_version=1,
    )
    assert normalized == {
        "q": "Bướm",
        "topic": "Côn trùng",
        "target_age_band_ref": "age-3-6",
        "target_age_band_version": 1,
    }
    assert _normalize_search_filters(
        q=None, topic=None, target_age_band_ref=None, target_age_band_version=None
    ) == {
        "q": None,
        "topic": None,
        "target_age_band_ref": None,
        "target_age_band_version": None,
    }

    for filters in (
        {"q": "   "},
        {"q": "x" * 101},
        {"topic": "x" * 121},
        {"q": "a\x00b"},
        {"topic": "a\x00b"},
        {"q": "a\x1fb"},
        {"target_age_band_ref": "age-3-6"},
        {"target_age_band_version": 1},
        {"target_age_band_ref": "invalid ref", "target_age_band_version": 1},
        {"target_age_band_ref": "age-3-6", "target_age_band_version": 0},
    ):
        arguments: dict[str, Any] = {
            "q": None,
            "topic": None,
            "target_age_band_ref": None,
            "target_age_band_version": None,
        }
        arguments.update(filters)
        with pytest.raises(LessonLibraryError) as refused:
            _normalize_search_filters(**arguments)
        assert (refused.value.status_code, refused.value.code) == (400, "INVALID_REQUEST")


def test_cursor_binds_actor_route_and_filters() -> None:
    scope = {
        "actor": "teacher-a",
        "route": "GET /organizations/org-a/public-lessons",
        "source": "PUBLIC",
        "filters": {"q": "bướm", "topic": None},
        "order": "updated_at:desc,lesson_id:desc",
    }
    sort_value = datetime(2026, 11, 24, tzinfo=UTC)
    cursor = _encode_scoped_cursor(
        scope=scope, sort_value=sort_value, row_id="lesson-a", value_kind="datetime"
    )
    assert _decode_scoped_cursor(
        cursor=cursor, scope=scope, value_kind="datetime"
    ) == (sort_value, "lesson-a")

    for changed_scope in (
        {**scope, "actor": "teacher-b"},
        {**scope, "route": "GET /organizations/org-b/public-lessons"},
        {**scope, "filters": {"q": "other", "topic": None}},
        {**scope, "source": "SHARED"},
    ):
        with pytest.raises(LessonLibraryError) as refused:
            _decode_scoped_cursor(
                cursor=cursor, scope=changed_scope, value_kind="datetime"
            )
        assert (refused.value.status_code, refused.value.code) == (400, "INVALID_REQUEST")


def test_cursor_tie_breaker_equal_sort_values() -> None:
    scope = {"actor": "parent-a", "route": "GET /me/lessons", "order": "created_at-desc"}
    sort_value = datetime(2026, 11, 24, tzinfo=UTC)
    cursor = _encode_scoped_cursor(
        scope=scope, sort_value=sort_value, row_id="lesson-b", value_kind="datetime"
    )
    sort_col = column("created_at", DateTime(timezone=True))
    id_col = column("lesson_id", String())
    stmt = _scoped_cursor_filter(
        select(sort_col, id_col),
        cursor,
        scope=scope,
        sort_col=sort_col,
        id_col=id_col,
        value_kind="datetime",
    )
    predicate = str(stmt._where_criteria[0].compile(compile_kwargs={"literal_binds": True}))
    assert "created_at <" in predicate
    assert "created_at =" in predicate
    assert "lesson_id < 'lesson-b'" in predicate


def test_literal_search_escapes_wildcards() -> None:
    assert _escape_like_literal(r"100%_\literal") == r"100\%\_\\literal"
    assert _escape_like_literal("bướm") == "bướm"


class _MappingResult:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row

    def mappings(self) -> _MappingResult:
        return self

    def one_or_none(self) -> dict[str, Any] | None:
        return self.row


class _ExactVersionDb:
    def __init__(self, lesson_id: str) -> None:
        self.lesson_id = lesson_id
        self.statements: list[Any] = []

    def execute(self, statement: Any) -> _MappingResult:
        self.statements.append(statement)
        if len(self.statements) == 1:
            return _MappingResult(
                {"lesson_id": self.lesson_id, "visibility": "PRIVATE", "created_by": "teacher-a"}
            )
        return _MappingResult(None)


def test_exact_version_lookup_never_falls_back() -> None:
    db = _ExactVersionDb("lesson-a")
    service = LessonLibraryService(db, storage=None, parser=None, scanner=None)
    with pytest.raises(LessonLibraryError) as missing:
        service.get_lesson_version(
            organization_id="org-a",
            lesson_id="lesson-a",
            version_id="other-version",
            actor="teacher-a",
        )
    assert (missing.value.status_code, missing.value.code) == (404, "RESOURCE_NOT_FOUND")
    assert len(db.statements) == 2
    version_query = db.statements[1]
    assert {"lesson-a", "other-version"} <= set(version_query.compile().params.values())
    assert "current_version_id" not in str(version_query)
