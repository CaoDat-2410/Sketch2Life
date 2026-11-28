"""Unit coverage for Teacher activity reads and BE1 portfolio access."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from starlette.responses import Response

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.interfaces.http.routers import be1_records

ISSUER = "https://issuer.example.test/teacher-workspace"
PRINCIPAL = VerifiedPrincipal(subject="teacher-1", issuer=ISSUER, roles=frozenset())
ORG = "org-1"
CLASS = "class-1"
CHILD = "child-1"


class _MappingResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> _MappingResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _Scalars:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _ActivityQuerySession:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.statement = ""

    def execute(self, statement: Any) -> _MappingResult:
        self.statement = str(statement)
        return _MappingResult(self.rows)


class _PortfolioSession:
    def __init__(self, profile: Any) -> None:
        self.profile = profile
        self.added: list[Any] = []
        self.did_commit = False
        self.did_rollback = False

    def get(self, _model: Any, _key: Any) -> Any:
        return SimpleNamespace(state="active", account_role="teacher", issuer=ISSUER)

    def scalars(self, _statement: Any) -> _Scalars:
        return _Scalars(
            [
                SimpleNamespace(
                    organization_id=ORG,
                    subject=PRINCIPAL.subject,
                    role="teacher",
                    class_id=CLASS,
                    active=True,
                    assignment_id="a-1",
                )
            ]
        )

    def scalar(self, statement: Any) -> Any:
        query = str(statement)
        if "FROM be1_classrooms" in query:
            return SimpleNamespace(
                organization_id=ORG,
                class_id=CLASS,
                state="active",
            )
        if "FROM be1_managed_profiles" in query:
            return self.profile
        return None

    def execute(self, _statement: Any) -> _MappingResult:
        return _MappingResult(
            [
                {
                    "observation_id": "observation-1",
                    "session_id": "session-1",
                    "kind": "observation",
                    "content": {"note": "Synthetic note"},
                    "created_at": "2026-11-25T00:00:00+00:00",
                    "created_by": "adult-private",
                    "source_refs": ["asset-private"],
                }
            ]
        )

    def add(self, row: Any) -> None:
        self.added.append(row)

    def commit(self) -> None:
        self.did_commit = True

    def rollback(self) -> None:
        self.did_rollback = True


def _profile() -> Any:
    return SimpleNamespace(
        child_id=CHILD,
        organization_id=ORG,
        class_id=CLASS,
        data_origin="SYNTHETIC_DEV",
        consent_purpose_ref=None,
    )


def test_teacher_activities_sort_by_order_and_skip_malformed_json() -> None:
    activity = {
        "title": "Activity",
        "objective": "Objective",
        "activity_kind": "outdoor",
        "materials_text": "Materials",
        "preparation_text": "Preparation",
        "instructions_text": "Instructions",
        "observation_notes": "Observation",
        "safety_notes": "Safety",
    }
    lesson = {"title": "Lesson", "topic": "Topic"}
    common = {
        "lesson_id": "lesson-1",
        "version_id": "version-1",
        "version_no": 1,
        "content_sha256": "a" * 64,
        "updated_at": datetime(2026, 11, 25, tzinfo=UTC),
        "content_json": lesson,
    }
    db = _ActivityQuerySession(
        [
            {
                **common,
                "lesson_activity_id": "f" * 36,
                "activity_order": 1,
                "activity_json": activity,
            },
            {
                **common,
                "lesson_activity_id": "0" * 36,
                "activity_order": 2,
                "activity_json": activity,
            },
            {
                **common,
                "lesson_activity_id": "1" * 36,
                "activity_order": 3,
                "activity_json": {"title": None},
            },
        ]
    )
    service = LessonLibraryService(
        db, storage=None, parser=None, scanner=None  # type: ignore[arg-type]
    )

    result = service.list_teacher_activities(
        organization_id=ORG,
        actor="teacher-1",
        manager=False,
        limit=25,
        cursor=None,
    )

    assert db.statement.index("activity_order ASC") < db.statement.index("activity_id ASC")
    assert [item["activity_order"] for item in result["items"]] == [1, 2]


@pytest.mark.parametrize(
    ("withdrawn", "released", "status_code", "code"),
    [
        (False, True, 200, None),
        (False, False, 409, "CONSENT_NOT_EFFECTIVE"),
        (True, False, 404, "RESOURCE_NOT_FOUND"),
    ],
)
def test_portfolio_release_withdrawal_decision_table(
    monkeypatch: pytest.MonkeyPatch,
    withdrawn: bool,
    released: bool,
    status_code: int,
    code: str | None,
) -> None:
    monkeypatch.setattr(be1_records, "_profile_withdrawn", lambda _db, _row: withdrawn)
    monkeypatch.setattr(
        be1_records,
        "_profile_released",
        lambda _db, _row, *, for_write, real_data_enabled: released,
    )
    db = _PortfolioSession(_profile())
    response = Response()
    try:
        body = be1_records.read_portfolio(
            ORG,
            CLASS,
            CHILD,
            response,
            limit=25,
            principal=PRINCIPAL,
            db=db,  # type: ignore[arg-type]
        )
    except HTTPException as exc:
        assert exc.status_code == status_code
        assert isinstance(exc.detail, dict)
        assert exc.detail["code"] == code
        if withdrawn:
            assert db.did_rollback
            assert db.added == []
        else:
            assert db.did_commit
            assert len(db.added) == 1
    else:
        assert status_code == 200
        assert body["contract"] == "Be1PortfolioPageV1"
        item = body["items"][0]
        assert set(item) == {"observation_id", "session_id", "kind", "content", "created_at"}
        assert "created_by" not in item and "source_refs" not in item
        assert response.headers["Cache-Control"] == "private, no-store"
