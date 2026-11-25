"""FEAT-092: a suggestion-based main-activity snapshot must round-trip through the response schema."""

from sketch2life.contracts.schemas.parent_story_runs import ParentMainActivityV1


def test_suggestion_snapshot_with_provenance_fields_validates() -> None:
    snapshot = {
        "state": "SELECTED",
        "selected": {
            "activity_ref": None,
            "title": "Tìm côn trùng",
            "objective": "Quan sát",
            "materials_text": "Không",
            "preparation_text": "Không",
            "instructions_text": "Đi dạo",
            "observation_notes": "Ghi lại",
            "safety_notes": "Có người lớn",
            "activity_kind": "outdoor",
            "source": "AI_GENERATED_DRAFT",
            "lesson_title": None,
            "lesson_topic": None,
            "source_lesson_id": None,
            "source_lesson_version_id": None,
            "source_content_sha256": None,
            "source_activity_index": None,
            "match_reason": "Chưa có hoạt động phù hợp.",
            "suggestion_set_id": "b493b820-826c-4950-aa2e-c1461ea110ac",
            "suggestion_set_revision": 1,
            "suggestion_activity_index": 1,
        },
        "selected_at": "2026-11-25T05:00:00+00:00",
    }
    assert ParentMainActivityV1.model_validate(snapshot).selected.suggestion_activity_index == 1
