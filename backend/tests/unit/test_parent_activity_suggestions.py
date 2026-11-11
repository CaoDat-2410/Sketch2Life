from __future__ import annotations

from dataclasses import replace

import pytest

from sketch2life.application.ports.parent_activity_catalog import ParentActivityLesson
from sketch2life.application.services.parent_activity_suggestions import (
    ParentActivitySuggestionError,
    ParentActivitySuggestionService,
    _contains_unsafe_action,
)


def _activity(title: str, *, kind: str = "outdoor") -> dict[str, str]:
    return {
        "title": title,
        "objective": "Quan sát cánh bướm và các hình dạng trong khu vườn.",
        "materials_text": "Giấy và bút sáp tùy chọn.",
        "preparation_text": "Người lớn chọn khu vườn an toàn và chuẩn bị giấy.",
        "instructions_text": (
            "Ngoài trời trong vườn, trẻ tự chọn vị trí để quan sát bướm; "
            "người lớn ở cạnh hỗ trợ và mời trẻ mô tả điều con nhìn thấy."
        ),
        "observation_notes": "Ghi nhận trẻ chọn quan sát màu sắc hay chuyển động.",
        "safety_notes": "Không chạm hoặc bắt côn trùng; luôn có người lớn giám sát.",
        "activity_kind": kind,
    }


def _lesson(
    *,
    band: str = "age-72-107-months-v1",
    activity: dict[str, str] | None = None,
    access_source: str = "PUBLIC",
) -> ParentActivityLesson:
    return ParentActivityLesson(
        lesson_id="lesson-1",
        version_id="version-4",
        version_no=4,
        content_sha256="a" * 64,
        title="Bài học về bướm",
        topic="Bướm trong khu vườn",
        drawing_subject="Bướm",
        target_age_band_ref=band,
        target_age_band_version=1,
        access_source=access_source,
        activities=(activity or _activity("Quan sát bướm trong vườn"),),
    )


class _Catalog:
    def __init__(self, lessons: tuple[ParentActivityLesson, ...]) -> None:
        self.lessons = lessons

    def list_accessible_lessons(self, *, parent_principal_ref: str):
        assert parent_principal_ref == "synthetic-parent"
        return self.lessons


def _prepare(
    lessons: tuple[ParentActivityLesson, ...],
    *,
    adult_idea: str = "Con muốn quan sát bướm màu tím cùng mẹ.",
):
    service = ParentActivitySuggestionService(_Catalog(lessons))
    prepared = service.prepare(
        parent_principal_ref="synthetic-parent",
        context_snapshot={
            "age_months": 72,
            "interests_summary": "Thích động vật và màu tím; tên bé là Linh.",
            "topic": "Bướm",
            "adult_confirmed_idea": adult_idea,
        },
        subject_label="Bướm",
        visible_features=["cánh đối xứng", "râu"],
        pinned_lesson_snapshot=None,
    )
    return service, prepared


def _fallbacks() -> list[dict[str, str]]:
    return [
        {
            **_activity("Theo dấu bóng cánh bướm"),
            "objective": "So sánh bóng của cánh bướm với hình dáng trong bức tranh.",
            "instructions_text": (
                "Ở sân vườn ngoài trời, trẻ tự chọn nơi có nắng để quan sát bóng lá; "
                "người lớn hỗ trợ đặt giấy và hỏi trẻ muốn so sánh hình nào."
            ),
            "safety_notes": "Tránh nhìn trực tiếp vào mặt trời; luôn có người lớn ở cạnh.",
        },
        {
            **_activity("Tìm màu hoa quanh vườn"),
            "objective": "Quan sát màu hoa và liên hệ với màu sắc của con bướm.",
            "instructions_text": (
                "Trong khu vườn ngoài trời, trẻ có thể chọn một bông hoa đã rụng để quan sát; "
                "người lớn đi cùng và giúp trẻ so sánh màu mà không cần hái hoa."
            ),
            "safety_notes": "Không nếm hoa hoặc lá; người lớn nhắc trẻ rửa tay sau hoạt động.",
        },
        {
            **_activity("Đếm cánh và lá rơi"),
            "objective": "Luyện quan sát và đếm bằng cách so sánh cánh bướm với lá rụng.",
            "instructions_text": (
                "Ở bãi cỏ an toàn, trẻ tự chọn vài chiếc lá đã rụng để đếm và so sánh; "
                "người lớn giám sát, hỗ trợ khi trẻ muốn ghi lại kết quả."
            ),
            "safety_notes": "Chỉ dùng lá đã rụng, tránh cây lạ và luôn có người lớn giám sát.",
        },
    ]


def _worker_result(*, decision: str, selections=None, reason="", activities=None):
    return {
        "schema_version": "sketch2life.parent-activity-suggestions.v2",
        "decision": decision,
        "selected_candidates": selections or [],
        "no_match_reason": reason,
        "age_band_months": "72-107",
        "fallback_activities": activities or [],
    }


def test_prepare_sends_minimized_context_and_only_exact_age_public_shared_candidates():
    eligible_public = _lesson()
    eligible_shared = replace(
        _lesson(activity=_activity("Mô tả bướm trong vườn")),
        lesson_id="lesson-2",
        version_id="version-2",
        access_source="SHARED",
    )
    wrong_age = replace(
        _lesson(band="age-36-71-months-v1"),
        lesson_id="lesson-younger",
        version_id="version-younger",
    )
    unknown_legacy_band = replace(
        _lesson(band="age-3-6"),
        lesson_id="lesson-unknown-band",
        version_id="version-unknown-band",
    )
    private = replace(_lesson(access_source="PRIVATE"), lesson_id="private")
    indoor = replace(
        _lesson(activity=_activity("Vẽ bướm trong lớp", kind="indoor")),
        lesson_id="indoor",
    )
    pii_activity = _activity("Quan sát bướm có thông tin liên hệ")
    pii_activity["instructions_text"] += " Liên hệ linh@example.test."
    pii_lesson = replace(
        _lesson(activity=pii_activity),
        lesson_id="lesson-with-pii",
        version_id="version-with-pii",
    )
    service, prepared = _prepare(
        (
            eligible_public,
            eligible_shared,
            wrong_age,
            unknown_legacy_band,
            private,
            indoor,
            pii_lesson,
        )
    )

    assert prepared.candidate_count == 2
    assert set(prepared.candidates_by_ref) == {"C001", "C002"}
    assert prepared.worker_input["age_band_months"] == "72-107"
    assert prepared.worker_input["adult_confirmed_idea"] == (
        "Con muốn quan sát bướm màu tím cùng mẹ."
    )
    assert prepared.worker_input["profile_interest_tags"] == ["animals", "colors"]
    assert prepared.worker_input["narration_interest_tags"] == ["insects", "colors"]
    assert "Linh" not in str(prepared.worker_input)
    assert "image" not in prepared.worker_input
    assert "parent_principal_ref" not in prepared.worker_input
    assert "linh@example.test" not in str(prepared.worker_input)


def test_prepare_sends_only_sanitized_adult_confirmed_idea_to_worker():
    _, prepared = _prepare(
        (),
        adult_idea=(
            "Con muốn quan sát bướm màu tím. Liên hệ linh@example.test hoặc 0901234567."
        ),
    )

    idea = prepared.worker_input["adult_confirmed_idea"]
    assert "quan sát bướm màu tím" in idea
    assert "linh@example.test" not in idea
    assert "0901234567" not in idea
    assert len(idea) <= 300


def test_catalog_selection_returns_canonical_versioned_activity_not_worker_rewrite():
    service, prepared = _prepare((_lesson(),))
    rewritten = _activity("Worker rewrite that must not be returned")
    raw = _worker_result(
        decision="CATALOG_MATCH",
        selections=[{"candidate_ref": "C001", "match_reason": "Khớp chủ đề và quan sát bướm."}],
    )
    raw["fallback_activities"] = []

    response = service.resolve(
        prepared=prepared,
        raw_result=raw,
        request_id="00000000-0000-0000-0000-000000000001",
        story_run_id="00000000-0000-0000-0000-000000000002",
        understanding_revision=1,
        modal_call_id="modal-call",
    )

    activity = response["activities"][0]
    assert activity["title"] == "Quan sát bướm trong vườn"
    assert activity["title"] != rewritten["title"]
    assert activity["source"] == "PUBLISHED_SHARED_LESSON"
    assert activity["source_lesson_version_id"] == "version-4"
    assert activity["source_content_sha256"] == "a" * 64
    assert activity["match_reason"] == "Khớp chủ đề và quan sát bướm."
    assert response["selection_mode"] == "CATALOG_SELECTION"


def test_pinned_lesson_uses_exact_immutable_version_and_age_band_snapshot():
    service = ParentActivitySuggestionService(_Catalog(()))
    pinned = {
        "lesson_id": "lesson-pinned",
        "version_id": "version-pinned-3",
        "version_no": 3,
        "content_sha256": "b" * 64,
        "title": "Bài bướm đã chọn",
        "topic": "Bướm",
        "drawing_subject": "Bướm",
        "target_age_band_ref": "age-72-107-months-v1",
        "target_age_band_version": 1,
        "activities": [_activity("Quan sát bướm")],
    }
    prepared = service.prepare(
        parent_principal_ref="synthetic-parent",
        context_snapshot={
            "age_months": 72,
            "interests_summary": "Thiên nhiên",
            "topic": "Bướm",
            "adult_confirmed_idea": "Quan sát bướm",
        },
        subject_label="Bướm",
        visible_features=["cánh"],
        pinned_lesson_snapshot=pinned,
    )

    assert prepared.candidate_count == 1
    candidate = prepared.candidates_by_ref["C001"]
    assert candidate.version_id == "version-pinned-3"
    assert candidate.content_sha256 == "b" * 64
    assert candidate.source == "PINNED_LESSON"


def test_catalog_selection_rejects_unknown_candidate_ref():
    service, prepared = _prepare((_lesson(),))
    raw = _worker_result(
        decision="CATALOG_MATCH",
        selections=[{"candidate_ref": "C999", "match_reason": "Phù hợp."}],
    )
    raw["fallback_activities"] = []

    with pytest.raises(ParentActivitySuggestionError, match="MODAL_OUTPUT_CONTRACT_INVALID"):
        service.resolve(
            prepared=prepared,
            raw_result=raw,
            request_id="00000000-0000-0000-0000-000000000001",
            story_run_id="00000000-0000-0000-0000-000000000002",
            understanding_revision=1,
            modal_call_id=None,
        )


def test_fallback_requires_three_distinct_safe_outdoor_child_led_drafts():
    service, prepared = _prepare(())
    raw = _worker_result(
        decision="NO_MATCH",
        reason="Không có hoạt động catalog phù hợp với bối cảnh này.",
        activities=_fallbacks(),
    )

    response = service.resolve(
        prepared=prepared,
        raw_result=raw,
        request_id="00000000-0000-0000-0000-000000000001",
        story_run_id="00000000-0000-0000-0000-000000000002",
        understanding_revision=1,
        modal_call_id="modal-call",
    )

    assert response["selection_mode"] == "AI_GENERATED_FALLBACK"
    assert len(response["activities"]) == 3
    assert {item["source"] for item in response["activities"]} == {"AI_GENERATED_DRAFT"}
    assert all(item["source_lesson_version_id"] is None for item in response["activities"])


def test_fallback_allows_concise_materials_and_observation_fragments():
    service, prepared = _prepare(())
    activities = _fallbacks()
    activities[0]["materials_text"] = "Giấy, bút sáp"
    activities[0]["observation_notes"] = "Màu cánh, cách trẻ lựa chọn"
    raw = _worker_result(
        decision="NO_MATCH",
        reason="Không có hoạt động phù hợp.",
        activities=activities,
    )

    response = service.resolve(
        prepared=prepared,
        raw_result=raw,
        request_id="00000000-0000-0000-0000-000000000001",
        story_run_id="00000000-0000-0000-0000-000000000002",
        understanding_revision=1,
        modal_call_id=None,
    )

    assert response["selection_mode"] == "AI_GENERATED_FALLBACK"
    assert response["activities"][0]["materials_text"] == "Giấy, bút sáp"
    assert response["activities"][0]["observation_notes"] == "Màu cánh, cách trẻ lựa chọn"


@pytest.mark.parametrize("field", ["instructions_text", "safety_notes"])
def test_fallback_still_rejects_incomplete_core_sentences(field):
    service, prepared = _prepare(())
    activities = _fallbacks()
    activities[0][field] = activities[0][field].rstrip(".!?… ")
    raw = _worker_result(
        decision="NO_MATCH",
        reason="Không có hoạt động phù hợp.",
        activities=activities,
    )

    with pytest.raises(ParentActivitySuggestionError) as caught:
        service.resolve(
            prepared=prepared,
            raw_result=raw,
            request_id="00000000-0000-0000-0000-000000000001",
            story_run_id="00000000-0000-0000-0000-000000000002",
            understanding_revision=1,
            modal_call_id=None,
        )

    assert caught.value.diagnostic_code == "ACTIVITY_TEXT_INCOMPLETE"


def test_fire_safety_gate_distinguishes_lua_fabric_from_fire():
    assert not _contains_unsafe_action("Trẻ dùng khăn lụa làm cánh bướm ngoài trời.")
    assert _contains_unsafe_action("Trẻ đốt lửa trong khu vườn.")
    assert not _contains_unsafe_action("Người lớn nhắc trẻ tránh lửa.")


def test_fallback_accepts_safe_lua_fabric_in_materials():
    service, prepared = _prepare(())
    activities = _fallbacks()
    activities[2]["materials_text"] = "Khăn lụa mềm, giấy màu và khoảng sân rộng."
    raw = _worker_result(
        decision="NO_MATCH",
        reason="Không có hoạt động phù hợp.",
        activities=activities,
    )

    response = service.resolve(
        prepared=prepared,
        raw_result=raw,
        request_id="00000000-0000-0000-0000-000000000001",
        story_run_id="00000000-0000-0000-0000-000000000002",
        understanding_revision=1,
        modal_call_id=None,
    )

    assert response["selection_mode"] == "AI_GENERATED_FALLBACK"


def test_fallback_gate_exposes_safe_diagnostic_code_for_outdoor_setting():
    service, prepared = _prepare(())
    activities = _fallbacks()
    activities[0]["instructions_text"] = (
        "Trẻ tự chọn nơi quan sát bướm; người lớn đi cùng và hỗ trợ khi cần."
    )
    activities[0]["preparation_text"] = "Người lớn chuẩn bị giấy và bút màu."
    raw = _worker_result(
        decision="NO_MATCH",
        reason="Không có hoạt động phù hợp.",
        activities=activities,
    )

    with pytest.raises(ParentActivitySuggestionError) as caught:
        service.resolve(
            prepared=prepared,
            raw_result=raw,
            request_id="00000000-0000-0000-0000-000000000001",
            story_run_id="00000000-0000-0000-0000-000000000002",
            understanding_revision=1,
            modal_call_id=None,
        )

    assert caught.value.code == "PARENT_ACTIVITY_QUALITY_GATE_REJECTED"
    assert caught.value.diagnostic_code == "OUTDOOR_SETTING_NOT_EXPLICIT"


def test_fallback_gate_rejects_non_latin_script_with_safe_diagnostic():
    service, prepared = _prepare(())
    activities = _fallbacks()
    activities[0]["objective"] += " 見."
    raw = _worker_result(
        decision="NO_MATCH",
        reason="Không có hoạt động phù hợp.",
        activities=activities,
    )

    with pytest.raises(ParentActivitySuggestionError) as caught:
        service.resolve(
            prepared=prepared,
            raw_result=raw,
            request_id="00000000-0000-0000-0000-000000000001",
            story_run_id="00000000-0000-0000-0000-000000000002",
            understanding_revision=1,
            modal_call_id=None,
        )

    assert caught.value.diagnostic_code == "NON_VIETNAMESE_SCRIPT"


def test_fallback_gate_rejects_truncated_text_with_safe_diagnostic():
    service, prepared = _prepare(())
    activities = _fallbacks()
    activities[0]["objective"] = "Trẻ khám phá màu sắc của cánh bướm ngoài"
    raw = _worker_result(
        decision="NO_MATCH",
        reason="Không có hoạt động phù hợp.",
        activities=activities,
    )

    with pytest.raises(ParentActivitySuggestionError) as caught:
        service.resolve(
            prepared=prepared,
            raw_result=raw,
            request_id="00000000-0000-0000-0000-000000000001",
            story_run_id="00000000-0000-0000-0000-000000000002",
            understanding_revision=1,
            modal_call_id=None,
        )

    assert caught.value.diagnostic_code == "ACTIVITY_TEXT_INCOMPLETE"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda items: items.__setitem__(0, {**items[0], "activity_kind": "indoor"}),
        lambda items: items.__setitem__(0, {**items[0], "instructions_text": "Dùng dao cắt lá."}),
        lambda items: items.__setitem__(
            0, {**items[0], "instructions_text": "Trẻ làm theo hướng dẫn."}
        ),
        lambda items: items.__setitem__(1, dict(items[0])),
    ],
)
def test_fallback_quality_gate_fails_closed(mutate):
    service, prepared = _prepare(())
    activities = _fallbacks()
    mutate(activities)
    raw = _worker_result(
        decision="NO_MATCH",
        reason="Không có hoạt động phù hợp.",
        activities=activities,
    )

    with pytest.raises(
        ParentActivitySuggestionError, match="PARENT_ACTIVITY_QUALITY_GATE_REJECTED"
    ):
        service.resolve(
            prepared=prepared,
            raw_result=raw,
            request_id="00000000-0000-0000-0000-000000000001",
            story_run_id="00000000-0000-0000-0000-000000000002",
            understanding_revision=1,
            modal_call_id=None,
        )
