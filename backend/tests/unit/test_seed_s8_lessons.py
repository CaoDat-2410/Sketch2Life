"""Pure fixture checks for the S8 lesson occurrence seed stage."""

from __future__ import annotations

import re
import uuid
from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy import Engine

from sketch2life.domain.lesson_library.model import validate_content
from sketch2life.domain.lesson_occurrences.documents import text_sha256
from tools.seed import data, s8_lessons
from tools.seed import s8_lessons_data as fixtures
from tools.seed.guard import SeedGuardError
from tools.seed.stage_common import check_database_prefix


def test_occurrence_specs_have_the_expected_classes_teachers_dates_and_pins() -> None:
    assert [(row.key, row.class_number) for row in fixtures.OCCURRENCES] == [
        ("o1", 1),
        ("o2", 1),
        ("o3", 1),
        ("o4", 2),
        ("o5", 3),
    ]
    assert [row.teacher_subject for row in fixtures.OCCURRENCES] == [
        data.ORG_A_TEACHERS[0],
        data.ORG_A_TEACHERS[0],
        data.ORG_A_TEACHERS[0],
        data.ORG_A_TEACHERS[1],
        data.ORG_A_TEACHERS[0],
    ]
    assert [(row.lesson_key, row.lesson_version_no) for row in fixtures.OCCURRENCES] == [
        ("l1", 2),
        ("l2", 1),
        ("l4", 1),
        (None, None),
        ("l1", 1),
    ]
    assert len({row.title for row in fixtures.OCCURRENCES}) == 5
    assert all("[SEED]" not in row.title for row in fixtures.OCCURRENCES)


def test_document_fixtures_are_synthetic_metadata_with_valid_text_and_revisions() -> None:
    assert len(fixtures.DOCUMENTS) == 3
    assert all(
        "/" not in row.safe_file_name and "\\" not in row.safe_file_name
        for row in fixtures.DOCUMENTS
    )
    assert all(row.extension in {".docx", ".pdf", ".pptx"} for row in fixtures.DOCUMENTS)
    assert all(len(row.extracted_text) >= 400 for row in fixtures.DOCUMENTS)
    assert all(
        1 <= len(row.extracted_text.encode("utf-8")) <= 2_097_152 for row in fixtures.DOCUMENTS
    )
    assert fixtures.DOCUMENTS[1].warnings == ("OCR_NOT_SUPPORTED_PAGES",)
    assert fixtures.DOCUMENTS[1].page_coverage == (1,)
    assert 400 <= len(fixtures.DOCUMENT_EDIT_TEXT) <= 900
    assert len(text_sha256(fixtures.DOCUMENT_EDIT_TEXT)) == 64
    assert uuid.UUID(fixtures.source_document_id("doc-o1")).version == 5
    assert uuid.UUID(fixtures.document_revision_id("doc-o1", 1)).version == 5
    assert fixtures.source_document_id("doc-o1") != fixtures.source_document_id("doc-o2")


def test_plan_fixtures_cover_the_lesson_lifecycle_and_keep_text_authored() -> None:
    assert fixtures.EXPECTED == {
        "lesson_occurrences": 5,
        "lesson_source_documents": 3,
        "lesson_document_revisions": 4,
        "lesson_plan_revisions": 5,
        "lesson_plan_activities": 10,
        "lesson_presentations": 1,
        "lesson_presentation_revisions": 1,
    }
    o1 = [row for row in fixtures.PLANS if row.occurrence_key == "o1"]
    o2 = [row for row in fixtures.PLANS if row.occurrence_key == "o2"]
    o3 = [row for row in fixtures.PLANS if row.occurrence_key == "o3"]
    assert len(o1) == len(o2) == 1 and len(o3) == 3
    assert o1[0].document_revision_no == 2 and o1[0].activity_orders == (1, 2)
    assert o2[0].document_revision_no == 1 and o2[0].activity_orders == (1, 2)
    assert [row.confirm for row in o3] == [True, True, False]
    assert all(row.activity_orders == (1, 2) for row in o3)
    assert [row.expected_head_revision_no for row in o3] == [0, 1, 2]
    assert len({row.objectives for row in o3}) == 3
    assert len({row.teacher_direction for row in o3}) == 3
    for row in fixtures.PLANS:
        assert row.objectives and all(value.strip() for value in row.objectives)
        assert row.teacher_direction.strip() and row.safety_notes.strip()
    for _key, _visibility, _revision, versions in data.LESSON_SPECS:
        for _version, _state, content in versions:
            validate_content(content)
    for version in data.library_version_rows():
        assert len(version["structured_content_hash"]) == 64


def test_every_confirmed_seeded_plan_has_activities() -> None:
    assert all(plan.activity_orders for plan in fixtures.PLANS if plan.confirm)


def test_house_lesson_is_pinnable_by_occurrence_teacher() -> None:
    occurrence = next(row for row in fixtures.OCCURRENCES if row.key == "o3")
    item = next(row for row in data.library_item_rows() if row["lesson_id"] == data.lesson_id("l4"))
    version = next(
        row for row in data.library_version_rows() if row["version_id"] == data.version_id("l4", 1)
    )
    assert item["created_by"] == occurrence.teacher_subject
    assert (item["state"], item["moderation_state"], item["visibility"]) == (
        "ACTIVE", "VISIBLE", "PRIVATE"
    )
    assert version["review_state"] == "APPROVED"
    activities = [
        row for row in data.version_activity_rows() if row["version_id"] == version["version_id"]
    ]
    assert len(activities) == 2


def test_occurrence_and_plan_keys_are_fixed_and_distinct() -> None:
    assert len({fixtures.occurrence_key(row.key) for row in fixtures.OCCURRENCES}) == 5
    create_keys = {
        fixtures.plan_create_key(row.occurrence_key, row.revision_no) for row in fixtures.PLANS
    }
    confirm_keys = {
        fixtures.plan_confirm_key(row.occurrence_key, row.revision_no)
        for row in fixtures.PLANS
        if row.confirm
    }
    assert len(create_keys) == 5 and len(confirm_keys) == 3
    assert create_keys.isdisjoint(confirm_keys)
    assert fixtures.presentation_create_key("o1") not in create_keys | confirm_keys
    assert all(re.fullmatch(r"[A-Za-z0-9:_-]+", value) for value in create_keys | confirm_keys)


def test_stage_guard_refuses_seed_database_without_frc08_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tools.seed.stage_common.check_target",
        lambda _environ=None: SimpleNamespace(database="s2l_seed_fixture"),
    )
    with pytest.raises(SeedGuardError, match="frc08_"):
        check_database_prefix({})

    monkeypatch.setattr(
        "tools.seed.stage_common.check_target",
        lambda _environ=None: SimpleNamespace(database="frc08_seed_fixture"),
    )
    check_database_prefix({})


def test_run_s8_orchestrates_each_fixture_once_with_a_fake_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []

    class FakeEngine:
        def connect(self) -> FakeEngine:
            return self

        def __enter__(self) -> FakeEngine:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    counts = iter([{}, dict(fixtures.EXPECTED)])
    monkeypatch.setattr(s8_lessons, "count_s8_rows", lambda _connection: next(counts))
    monkeypatch.setattr(s8_lessons, "create_core_session_factory", lambda _engine: object())

    def create_occurrence(_factory: object, spec: fixtures.OccurrenceSpec) -> dict[str, str]:
        calls.append(("occurrence", spec.key))
        return {"occurrence_id": f"occurrence-{spec.key}"}

    monkeypatch.setattr(
        s8_lessons,
        "_create_occurrence",
        create_occurrence,
    )
    monkeypatch.setattr(
        s8_lessons,
        "_insert_document_rows",
        lambda _factory, spec, occurrence_id: calls.append(("document", spec.key, occurrence_id)),
    )
    monkeypatch.setattr(
        s8_lessons,
        "_edit_o1_document",
        lambda _factory, occurrence_id: calls.append(("edit", occurrence_id)),
    )

    def create_plan(
        _factory: object,
        occurrence_id: str,
        _occurrence: fixtures.OccurrenceSpec,
        plan: fixtures.PlanSpec,
    ) -> dict[str, str]:
        calls.append(("plan", plan.occurrence_key, plan.revision_no, occurrence_id))
        return {"content_hash": f"hash-{plan.occurrence_key}-{plan.revision_no}"}

    monkeypatch.setattr(
        s8_lessons,
        "_create_plan",
        create_plan,
    )
    monkeypatch.setattr(
        s8_lessons,
        "_confirm_plan",
        lambda _factory, occurrence_id, _occurrence, plan, content_hash: calls.append(
            ("confirm", plan.occurrence_key, plan.revision_no, occurrence_id, content_hash)
        ),
    )
    monkeypatch.setattr(
        s8_lessons,
        "_create_presentation",
        lambda _factory, occurrence_id, spec: calls.append(
            ("presentation", occurrence_id, spec.key)
        ),
    )

    result = s8_lessons.run_s8(cast(Engine, FakeEngine()))

    assert result.ok
    assert result.before == {}
    assert result.after == fixtures.EXPECTED
    assert [call for call in calls if call[0] == "occurrence"] == [
        ("occurrence", spec.key) for spec in fixtures.OCCURRENCES
    ]
    assert len([call for call in calls if call[0] == "document"]) == 3
    assert len([call for call in calls if call[0] == "edit"]) == 1
    assert len([call for call in calls if call[0] == "plan"]) == 5
    assert len([call for call in calls if call[0] == "confirm"]) == 3
    assert [call for call in calls if call[0] == "presentation"] == [
        ("presentation", "occurrence-o1", "o1")
    ]
