"""Pinned Teacher activity projection used by story and video inputs (no database)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select
from sqlalchemy.dialects import postgresql

from sketch2life.domain.story_teacher import TEACHER_PIN_SCHEMA
from sketch2life.infrastructure.story_teacher.story_activity import (
    pinned_story_activity,
    teacher_lesson_direction_text,
)

PLAN_REVISION = "plan-revision-1"
PLAN_ACTIVITY = "plan-activity-1"


class _Result:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self._row = row

    def mappings(self) -> _Result:
        return self

    def one_or_none(self) -> dict[str, Any] | None:
        return self._row


class _Session:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row
        self.statement: Select[Any] | None = None

    def execute(self, statement: Select[Any]) -> _Result:
        self.statement = statement
        return _Result(self.row)


def _pin(*, kind: str = "CUSTOM", snapshot_hash: str | None = None) -> dict[str, Any]:
    return {
        "lesson_pin_snapshot": {
            "schema_version": TEACHER_PIN_SCHEMA,
            "occurrence_id": "occurrence-1",
            "plan_revision_id": PLAN_REVISION,
            "activity": {
                "plan_activity_id": PLAN_ACTIVITY,
                "kind": kind,
                "snapshot_hash": snapshot_hash,
            },
        },
        "context_snapshot": {"objectives": ["Name circles", "Tell a short story"]},
    }


def _row(
    *,
    kind: str = "CUSTOM",
    title: str | None = "Draw with fingers",
    description: str | None = "Draw one shape with an adult.",
    snapshot: dict[str, Any] | None = None,
    snapshot_hash: str | None = None,
) -> dict[str, Any]:
    return {
        "plan_revision_id": PLAN_REVISION,
        "plan_activity_id": PLAN_ACTIVITY,
        "activity_kind": kind,
        "custom_title": title,
        "custom_description": description,
        "activity_snapshot": snapshot,
        "activity_snapshot_hash": snapshot_hash,
    }


def test_custom_activity_uses_custom_fields_and_context_objectives_fallback() -> None:
    session = _Session(_row())

    result = pinned_story_activity(
        session,
        _pin(),
        occurrence_id="occurrence-1",
        organization_id="organization-1",
    )  # type: ignore[arg-type]

    assert result == {
        "title": "Draw with fingers",
        "objective": "Name circles; Tell a short story",
        "materials_text": "",
        "preparation_text": "",
        "instructions_text": "Draw one shape with an adult.",
        "observation_notes": "",
        "safety_notes": "",
        "activity_kind": "indoor",
    }
    assert session.statement is not None
    params = session.statement.compile(dialect=postgresql.dialect()).params
    assert set(params.values()) == {
        PLAN_REVISION,
        PLAN_ACTIVITY,
        "occurrence-1",
        "organization-1",
    }


def test_catalog_activity_uses_snapshot_values_and_parent_field_limits() -> None:
    snapshot = {
        "title": "T" * 200,
        "objective": "O" * 500,
        "materials_text": "M" * 400,
        "preparation_text": "P" * 500,
        "instructions_text": "I" * 800,
        "observation_notes": "N" * 500,
        "safety_notes": "S" * 500,
        "activity_kind": "mixed",
    }
    pin = _pin(kind="CATALOG", snapshot_hash="a" * 64)
    row = _row(
        kind="CATALOG",
        title=None,
        description=None,
        snapshot=snapshot,
        snapshot_hash="a" * 64,
    )

    result = pinned_story_activity(_Session(row), pin)  # type: ignore[arg-type]

    assert result is not None
    assert {key: len(value) for key, value in result.items()} == {
        "title": 160,
        "objective": 400,
        "materials_text": 300,
        "preparation_text": 480,
        "instructions_text": 700,
        "observation_notes": 480,
        "safety_notes": 480,
        "activity_kind": 5,
    }
    assert result["activity_kind"] == "mixed"


def test_non_custom_hash_or_row_identity_mismatch_fails_closed() -> None:
    pin = _pin(kind="LESSON", snapshot_hash="a" * 64)
    snapshot = {"title": "Draw a leaf"}
    assert (
        pinned_story_activity(
            _Session(_row(kind="LESSON", snapshot=snapshot, snapshot_hash="b" * 64)),
            pin,
        )
        is None
    )
    mismatched_row = _row(kind="LESSON", snapshot=snapshot, snapshot_hash="a" * 64)
    mismatched_row["plan_revision_id"] = "another-plan"
    assert pinned_story_activity(_Session(mismatched_row), pin) is None  # type: ignore[arg-type]
    mismatched_row["plan_revision_id"] = PLAN_REVISION
    mismatched_row["activity_kind"] = "CUSTOM"
    assert pinned_story_activity(_Session(mismatched_row), pin) is None  # type: ignore[arg-type]


def test_missing_activity_title_refuses_the_pin() -> None:
    assert pinned_story_activity(_Session(_row(title=None, description=None)), _pin()) is None  # type: ignore[arg-type]


def test_teacher_direction_is_plain_text_and_stays_within_worker_limit() -> None:
    rendered = teacher_lesson_direction_text(
        {
            "teacher_direction": "Tell a gentle story.",
            "objectives": ["Name circles", "Notice colors"],
            "activity_title": "Draw with fingers",
            "selection_id": "must not travel",
        }
    )

    assert rendered == (
        "Định hướng: Tell a gentle story.\n"
        "Mục tiêu: Name circles; Notice colors\n"
        "Hoạt động: Draw with fingers"
    )
    assert "must not travel" not in rendered
    assert teacher_lesson_direction_text({}) is None
    assert len(teacher_lesson_direction_text({"teacher_direction": "x" * 5000}) or "") <= 2000
