# ruff: noqa: E501, F811, SIM117, B023
"""Unit tests for E2 (T-TCH2) review gaps (safe JSON access, cursor errors, history guards)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
)
from sketch2life.infrastructure.lesson_occurrences import service as occurrence_service_module
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.infrastructure.lesson_occurrences.service import LessonOccurrenceService


class _MappingResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> _MappingResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _ActivityFakeDb:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def execute(self, _statement: Any) -> _MappingResult:
        return _MappingResult(self._rows)


def _valid_activity(kind: str = "outdoor") -> dict[str, Any]:
    return {
        "title": "Draw",
        "objective": "Explore shapes",
        "activity_kind": kind,
        "materials_text": "Paper",
        "preparation_text": "Cut sheets",
        "instructions_text": "Sketch gently",
        "observation_notes": "Watch grip",
        "safety_notes": "Use blunt crayons",
    }


@pytest.mark.parametrize(
    ("content_json", "activity_json"),
    [
        (None, _valid_activity()),
        ({"title": "Lesson"}, _valid_activity()),
        ({"title": "Lesson", "topic": None}, _valid_activity()),
        ({"title": "Lesson", "topic": "Shapes"}, "not-a-dict"),
        ({"title": "Lesson", "topic": "Shapes"}, {**_valid_activity(), "safety_notes": None}),
        ({"title": "Lesson", "topic": "Shapes"}, _valid_activity(kind="virtual")),
    ],
)
def test_list_teacher_activities_skips_malformed_json_without_keyerror(
    content_json: Any, activity_json: Any
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md P3-2 (safe JSON access without KeyError 500)"""
    valid_row = {
        "lesson_id": "lesson-ok",
        "version_id": "ver-ok",
        "version_no": 1,
        "content_sha256": "a" * 64,
        "updated_at": datetime(2026, 11, 25, tzinfo=UTC),
        "content_json": {"title": "Lesson OK", "topic": "Shapes"},
        "lesson_activity_id": "act-ok",
        "activity_order": 1,
        "activity_json": _valid_activity(),
    }
    bad_row = {
        **valid_row,
        "lesson_activity_id": "act-bad",
        "activity_order": 2,
        "content_json": content_json,
        "activity_json": activity_json,
    }
    service = LessonLibraryService(
        _ActivityFakeDb([bad_row, valid_row]),  # type: ignore[arg-type]
        storage=None,  # type: ignore[arg-type]
        parser=None,  # type: ignore[arg-type]
        scanner=None,  # type: ignore[arg-type]
    )
    page = service.list_teacher_activities(
        organization_id="org-1",
        actor="teacher-1",
        manager=False,
        limit=25,
        cursor=None,
    )
    assert [item["lesson_activity_id"] for item in page["items"]] == ["act-ok"]


def test_list_teacher_activities_rejects_malformed_cursor() -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md Checked-(a) (bad cursor -> 422 INVALID_REQUEST)"""
    service = LessonLibraryService(
        _ActivityFakeDb([]),  # type: ignore[arg-type]
        storage=None,  # type: ignore[arg-type]
        parser=None,  # type: ignore[arg-type]
        scanner=None,  # type: ignore[arg-type]
    )
    with pytest.raises(LessonLibraryError) as exc:
        service.list_teacher_activities(
            organization_id="org-1",
            actor="teacher-1",
            manager=False,
            limit=25,
            cursor="not-base64-cursor",
        )
    assert exc.value.status_code == 422
    assert exc.value.code == "INVALID_REQUEST"


def test_list_teacher_history_denies_when_caller_facts_missing_and_validates_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md Checked-(b) (load_caller_facts None -> 404, limit bounds)"""
    principal = VerifiedPrincipal(subject="t-1", issuer="iss", roles=frozenset())
    service = LessonOccurrenceService(object())  # type: ignore[arg-type]

    monkeypatch.setattr(occurrence_service_module, "load_caller_facts", lambda *_args: None)
    with pytest.raises(LessonOccurrenceError) as not_found_exc:
        service.list_teacher_history(
            organization_id="org-1",
            principal=principal,
            state=None,
            limit=25,
            cursor=None,
        )
    assert not_found_exc.value.status_code == 404
    assert not_found_exc.value.code == "RESOURCE_NOT_FOUND"

    monkeypatch.setattr(
        occurrence_service_module,
        "load_caller_facts",
        lambda *_args: object(),
    )
    for bad_limit in (0, 101):
        with pytest.raises(LessonOccurrenceError) as limit_exc:
            service.list_teacher_history(
                organization_id="org-1",
                principal=principal,
                state=None,
                limit=bad_limit,
                cursor=None,
            )
        assert limit_exc.value.status_code == 400
        assert limit_exc.value.code == "INVALID_REQUEST"
