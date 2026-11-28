"""Offline checks that seeded Parent runs can list a matching catalog activity."""

from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.ports.parent_activity_catalog import ParentActivityLesson
from sketch2life.application.ports.parent_story_runs import ParentActivityContext
from sketch2life.application.services.parent_activity_selection import (
    ParentActivitySelectionService,
)
from sketch2life.application.services.parent_activity_suggestions import (
    ParentActivitySuggestionService,
)
from tools.seed import data as s1_data
from tools.seed import s7b_story_states as s7b_stage
from tools.seed import s7b_story_states_data as s7b_data
from tools.seed import s12_story_v4a_data as s12_data


class _Catalog:
    def __init__(self, lessons: Sequence[ParentActivityLesson]) -> None:
        self.lessons = lessons

    def list_accessible_lessons(
        self, *, parent_principal_ref: str
    ) -> Sequence[ParentActivityLesson]:
        return self.lessons


class _RunRepository:
    def __init__(self, context: ParentActivityContext) -> None:
        self.context = context

    def read_activity_context(
        self, *, principal: Any, run_id: str
    ) -> ParentActivityContext:
        return self.context


class _FakeSession:
    def __enter__(self) -> _FakeSession:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class _FakeLessonLibraryService:
    def __init__(self) -> None:
        self.grant: dict[str, Any] | None = None

    def create_access_grant(self, **kwargs: Any) -> dict[str, str]:
        self.grant = kwargs
        return {"state": "ACTIVE"}


def _context(
    *,
    age_months: int,
    topic: str,
    idea: str,
    interests: str,
    subject: str,
    visible_features: Sequence[str],
) -> ParentActivityContext:
    return ParentActivityContext(
        run_id="seed-parent-activity-run",
        run_revision=1,
        understanding_revision=1,
        context_snapshot={
            "age_months": age_months,
            "topic": topic,
            "adult_confirmed_idea": idea,
            "interests_summary": interests,
        },
        subject_label=subject,
        visible_features=list(visible_features),
        lesson_pin_snapshot=None,
    )


def _seed_lesson(lesson_key: str, version_no: int) -> ParentActivityLesson:
    content = next(
        version_content
        for key, _visibility, _revision, versions in s1_data.LESSON_SPECS
        if key == lesson_key
        for number, _review_state, version_content in versions
        if number == version_no
    )
    return ParentActivityLesson(
        lesson_id=s1_data.lesson_id(lesson_key),
        version_id=s1_data.version_id(lesson_key, version_no),
        version_no=version_no,
        content_sha256=s1_data.canonical_content_hash(content),
        title=content["title"],
        topic=content["topic"],
        drawing_subject=content["drawing_subject"],
        target_age_band_ref=content["target_age_band_ref"],
        target_age_band_version=content["target_age_band_version"],
        access_source="SHARED",
        activities=content["activities"],
    )


def _seed_lesson_for_grant(grant: dict[str, Any]) -> ParentActivityLesson:
    for lesson_key, _visibility, _revision, versions in s1_data.LESSON_SPECS:
        for version_no, _review_state, _content in versions:
            if (
                s1_data.lesson_id(lesson_key) == grant["lesson_id"]
                and s1_data.version_id(lesson_key, version_no) == grant["version_id"]
            ):
                return _seed_lesson(lesson_key, version_no)
    raise AssertionError("the P3 grant must reference a seeded lesson version")


def _lesson_from_content(
    *,
    lesson_id: str,
    version_id: str,
    content: dict[str, Any],
    access_source: str,
) -> ParentActivityLesson:
    return ParentActivityLesson(
        lesson_id=lesson_id,
        version_id=version_id,
        version_no=1,
        content_sha256=s1_data.canonical_content_hash(content),
        title=content["title"],
        topic=content["topic"],
        drawing_subject=content["drawing_subject"],
        target_age_band_ref=content["target_age_band_ref"],
        target_age_band_version=content["target_age_band_version"],
        access_source=access_source,
        activities=content["activities"],
    )


def _list_activities(
    *, parent_subject: str, context: ParentActivityContext, lessons: Sequence[ParentActivityLesson]
) -> list[dict[str, Any]]:
    service = ParentActivitySelectionService(
        _RunRepository(context), _Catalog(lessons)
    )
    result = service.list_activities(
        principal=SimpleNamespace(subject=parent_subject), run_id=context.run_id
    )
    return result["items"]


def test_p3_activity_grant_exposes_a_matching_outdoor_catalog_lesson(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lesson_library = _FakeLessonLibraryService()
    monkeypatch.setattr(
        s7b_stage,
        "_build_lesson_library_service",
        lambda _session: lesson_library,
    )

    s7b_stage._ensure_p3_story_catalog_access(lambda: _FakeSession())

    assert lesson_library.grant is not None
    p3_subject = s1_data.PARENT_SUBJECTS["p3"]
    active_groups = {
        row["parent_group_id"]
        for row in s1_data.parent_group_member_rows()
        if row["parent_principal_ref"] == p3_subject and row["state"] == "active"
    }
    assert len(active_groups) == 1
    assert lesson_library.grant["audience_kind"] == "PARENT_GROUP"
    assert lesson_library.grant["audience_ref"] == next(iter(active_groups))

    lesson = _seed_lesson_for_grant(lesson_library.grant)
    context = _context(
        age_months=s7b_data.PROFILE_SNAPSHOT.age_months,
        topic=s7b_data.P3_RUN_A[0],
        idea=s7b_data.P3_RUN_A[1],
        interests=s7b_data.PROFILE_SNAPSHOT.interests_summary or "",
        subject=s7b_data.DRAWING_RESULTS["p3-a"].subject,
        visible_features=s7b_data.DRAWING_RESULTS["p3-a"].visible_features,
    )
    items = _list_activities(
        parent_subject=p3_subject, context=context, lessons=[lesson]
    )

    assert [item["activity_ref"]["lesson_id"] for item in items] == [
        s1_data.lesson_id(s7b_data.P3_ACTIVITY_LESSON_KEY)
    ]
    assert lesson_library.grant["lesson_id"] == s1_data.lesson_id(
        s7b_data.P3_ACTIVITY_LESSON_KEY
    )
    assert lesson_library.grant["version_id"] == s1_data.version_id(
        s7b_data.P3_ACTIVITY_LESSON_KEY,
        s7b_data.P3_ACTIVITY_LESSON_VERSION_NO,
    )
    assert [item["activity_ref"] for item in items] == [
        {
            "lesson_id": s1_data.lesson_id(s7b_data.P3_ACTIVITY_LESSON_KEY),
            "version_id": s1_data.version_id(
                s7b_data.P3_ACTIVITY_LESSON_KEY,
                s7b_data.P3_ACTIVITY_LESSON_VERSION_NO,
            ),
            "content_sha256": lesson.content_sha256,
            "activity_index": 0,
        }
    ]


def test_p5_activity_fixture_is_age_fit_relevant_and_outdoor() -> None:
    profile = s1_data.current_profile_revision("k5")
    content = s7b_data.P5_ACTIVITY_LESSON_CONTENT
    lesson = _lesson_from_content(
        lesson_id="seed-p5-activity-lesson",
        version_id="seed-p5-activity-version",
        content=content,
        access_source="PUBLIC",
    )
    context = _context(
        age_months=int(profile["age_months"]),
        topic=s7b_data.P5_SUBJECT,
        idea=s7b_data.P5_SUBJECT,
        interests=str(profile["interests_summary"] or ""),
        subject=s7b_data.P5_SUBJECT,
        visible_features=s7b_data.DRAWING_RESULTS["p5"].visible_features,
    )

    items = _list_activities(
        parent_subject=s1_data.PARENT_SUBJECTS["p5"], context=context, lessons=[lesson]
    )

    assert content["locale"] == "vi-VN"
    assert content["target_age_band_ref"] == "age-72-107-months-v1"
    assert content["activities"][0]["activity_kind"] == "outdoor"
    assert len(items) == 1
    assert items[0]["activity_ref"]["lesson_id"] == lesson.lesson_id


def test_s12_suggestion_fixture_has_a_public_matching_outdoor_candidate() -> None:
    profile = s12_data.PARENTS_BY_KEY["p6"]
    content = {
        **s12_data.LESSON_CONTENT,
        "activities": list(s12_data.LESSON_ACTIVITIES),
    }
    lesson = _lesson_from_content(
        lesson_id=s12_data.LESSON_ID,
        version_id=s12_data.LESSON_VERSION_ID,
        content=content,
        access_source="PUBLIC",
    )
    service = ParentActivitySuggestionService(_Catalog([lesson]))

    prepared = service.prepare(
        parent_principal_ref=profile.subject,
        context_snapshot={
            "age_months": profile.age_months,
            "interests_summary": profile.interests_summary,
        },
        subject_label=lesson.drawing_subject,
        visible_features=[lesson.drawing_subject],
        pinned_lesson_snapshot=None,
    )

    assert lesson.target_age_band_ref == "age-36-71-months-v1"
    assert all(item["activity_kind"] == "outdoor" for item in lesson.activities)
    assert prepared.candidate_count >= 1
