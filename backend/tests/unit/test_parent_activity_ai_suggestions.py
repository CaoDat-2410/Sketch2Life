from __future__ import annotations

import pytest

from sketch2life.application.services.parent_activity_suggestions import (
    ParentActivitySuggestionError,
    ParentActivitySuggestionService,
    _contains_unsafe_action,
)
from sketch2life.contracts.schemas.modal_ai import ParentActivitySuggestionItemV1
from sketch2life.infrastructure.ai.modal_function_client import _current_modal_story_worker_input


def _drafts() -> list[dict[str, str]]:
    return [
        {
            "title": "Quan sat canh buom",
            "objective": "Tre quan sat mau canh buom va so sanh voi hoa.",
            "materials_text": "Giay ve va but mau.",
            "preparation_text": "Nguoi lon chon san vuon va dat giay tren ban.",
            "instructions_text": (
                "Ngoai troi trong vuon, tre tu chon goc an toan de quan sat buom; "
                "nguoi lon ho tro va moi tre mo ta mau sac."
            ),
            "observation_notes": "Ghi nhan cach tre so sanh mau canh buom va hoa.",
            "safety_notes": "Khong bat buom; nguoi lon giam sat tre.",
            "activity_kind": "outdoor",
        },
        {
            "title": "Tim duong bay cua buom",
            "objective": "Tre thu nghiem ve va so sanh cac huong bay.",
            "materials_text": "Bang giay nho va but mau.",
            "preparation_text": "Nguoi huong dan chuan bi bang giay tai san truong.",
            "instructions_text": (
                "Tai san truong ngoai troi, tre tu quyet dinh cach ve duong bay sau khi "
                "quan sat; nguoi huong dan ho tro khi can."
            ),
            "observation_notes": "Quan sat cach tre chon huong va net ve.",
            "safety_notes": "Tranh chay nhanh; nguoi lon nhac tre giu khoang cach.",
            "activity_kind": "outdoor",
        },
        {
            "title": "Phan loai mau hoa va buom",
            "objective": "Tre phan loai mau giay theo sac tren canh buom va hoa.",
            "materials_text": "Mau giay cat san va tam bia.",
            "preparation_text": "Nguoi cham soc dat giay tren hien nha sach se.",
            "instructions_text": (
                "Ngoai troi ben hien nha, tre tu chon mau giay de phan loai sac tren canh "
                "buom; nguoi cham soc khuyen khich tre thu nghiem cach xep."
            ),
            "observation_notes": "Ghi nhan cach tre doi nhom va giai thich lua chon.",
            "safety_notes": "Khong nem giay; nguoi lon giup thu gon sau hoat dong.",
            "activity_kind": "outdoor",
        },
    ]


def _worker_result(activities: list[dict[str, str]]) -> dict[str, object]:
    return {
        "schema_version": "sketch2life.parent-activity-suggestions.v2",
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": "No suitable catalog activity was found.",
        "age_band_months": "72-107",
        "fallback_activities": activities,
    }


def test_route_worker_input_contains_only_sanitized_topic_and_coarse_age_band() -> None:
    worker_input = ParentActivitySuggestionService.fallback_worker_input(
        age_months=84,
        topic="buom parent@example.test",
    )

    assert worker_input["schema_version"] == "sketch2life.parent-activity-suggest-input.v3"
    assert worker_input["age_band_months"] == "72-107"
    assert worker_input["topic"] == "buom"
    assert worker_input["adult_confirmed_idea"] == ""
    assert worker_input["profile_interest_tags"] == []
    assert worker_input["narration_interest_tags"] == []
    assert worker_input["candidate_activities"] == []
    assert "parent@example.test" not in str(worker_input)
    assert "age_months" not in worker_input


def test_route_gate_accepts_one_valid_draft_when_parameterized_for_one() -> None:
    activity = ParentActivitySuggestionItemV1.model_validate(_drafts()[0])

    ParentActivitySuggestionService.quality_gate_for_activity_suggestions(
        activities=[activity],
        expected_count=1,
        context_terms=frozenset({"buom"}),
    )


def test_route_gate_rejects_an_unsafe_draft_with_a_safe_diagnostic() -> None:
    unsafe = _drafts()[0]
    unsafe["instructions_text"] = (
        "Ngoai troi, tre tu chon leo len hang rao de quan sat; nguoi lon ho tro tre."
    )
    activity = ParentActivitySuggestionItemV1.model_validate(unsafe)

    with pytest.raises(ParentActivitySuggestionError) as caught:
        ParentActivitySuggestionService.quality_gate_for_activity_suggestions(
            activities=[activity],
            expected_count=1,
        )

    assert caught.value.code == "PARENT_ACTIVITY_QUALITY_GATE_REJECTED"
    assert caught.value.diagnostic_code == "UNSAFE_ACTION_TEXT"


@pytest.mark.parametrize(
    "field",
    (
        "title",
        "objective",
        "materials_text",
        "preparation_text",
        "instructions_text",
        "observation_notes",
        "safety_notes",
    ),
)
def test_route_gate_checks_unsafe_actions_in_every_draft_text_field(field: str) -> None:
    unsafe = _drafts()[0]
    unsafe[field] = (
        "Ngoai troi, tre tu chon goc de quan sat buom, tre leo len hang rao; "
        "nguoi lon ho tro tre."
        if field == "instructions_text"
        else "Tre leo len hang rao. Nguoi lon giam sat tre."
    )
    activity = ParentActivitySuggestionItemV1.model_validate(unsafe)

    with pytest.raises(ParentActivitySuggestionError) as caught:
        ParentActivitySuggestionService.quality_gate_for_activity_suggestions(
            activities=[activity],
            expected_count=1,
            context_terms=frozenset({"buom"}),
        )

    assert caught.value.diagnostic_code == "UNSAFE_ACTION_TEXT"


def test_route_gate_rejects_an_empty_context_as_mismatched() -> None:
    activity = ParentActivitySuggestionItemV1.model_validate(_drafts()[0])

    with pytest.raises(ParentActivitySuggestionError) as caught:
        ParentActivitySuggestionService.quality_gate_for_activity_suggestions(
            activities=[activity], expected_count=1, context_terms=frozenset()
        )

    assert caught.value.diagnostic_code == "ACTIVITY_CONTEXT_MISMATCH"


def test_unsafe_action_negation_is_limited_to_the_same_sentence() -> None:
    assert _contains_unsafe_action("Khong leo len hang rao. Tre leo len hang rao.")
    assert not _contains_unsafe_action("Khong leo len hang rao. Tre quan sat ngoai vuon.")


def test_route_gate_uses_the_requested_draft_count() -> None:
    activities = [ParentActivitySuggestionItemV1.model_validate(item) for item in _drafts()[:2]]

    with pytest.raises(ParentActivitySuggestionError) as caught:
        ParentActivitySuggestionService.quality_gate_for_activity_suggestions(
            activities=activities,
            expected_count=3,
        )

    assert caught.value.code == "PARENT_ACTIVITY_QUALITY_GATE_REJECTED"
    assert caught.value.diagnostic_code == "FALLBACK_COUNT_INVALID"


def test_route_fallback_requires_three_drafts_and_marks_each_as_ai_generated() -> None:
    worker_input = ParentActivitySuggestionService.fallback_worker_input(
        age_months=84,
        topic="buom",
    )
    activities = ParentActivitySuggestionService.resolve_fallback_drafts(
        worker_input=worker_input,
        raw_result=_worker_result(_drafts()),
    )

    assert len(activities) == 3
    assert {item["source"] for item in activities} == {"AI_GENERATED_DRAFT"}
    assert all(item["source_lesson_id"] is None for item in activities)
    assert all(item["source_lesson_version_id"] is None for item in activities)
    assert all(item["match_reason"] is None for item in activities)

    with pytest.raises(ParentActivitySuggestionError) as caught:
        ParentActivitySuggestionService.resolve_fallback_drafts(
            worker_input=worker_input,
            raw_result=_worker_result(_drafts()[:2]),
        )
    # The worker response contract rejects a non-three count before the safety gate sees it.
    assert caught.value.code == "MODAL_OUTPUT_CONTRACT_INVALID"


def test_route_fallback_without_a_topic_compares_with_the_label_the_worker_got() -> None:
    worker_input = ParentActivitySuggestionService.fallback_worker_input(age_months=84, topic="")
    assert worker_input["topic"] == "" and worker_input["confirmed_subject"]
    drafts = _drafts()
    for draft in drafts:
        draft["title"] = f"{draft['title']} - {worker_input['confirmed_subject']}"[:60]

    activities = ParentActivitySuggestionService.resolve_fallback_drafts(
        worker_input=worker_input,
        raw_result=_worker_result(drafts),
    )

    assert len(activities) == 3


def test_existing_context_dependent_quality_gate_stays_separate() -> None:
    service_gate = ParentActivitySuggestionService._quality_gate
    route_gate = ParentActivitySuggestionService.quality_gate_for_activity_suggestions

    assert service_gate is not route_gate


def test_first_story_v1_adapter_deliberately_drops_selected_activity() -> None:
    worker_input = {
        "schema_version": "sketch2life.story-generation-input.v3",
        "role": "PARENT",
        "language": "vi",
        "confirmed_subject": "rounded shapes",
        "understanding_revision": 1,
        "drawing_sha256": "a" * 64,
        "visible_features": ["round outline"],
        "child_age_months": 60,
        "context_revision": 1,
        "adult_confirmed_idea": "",
        "activity": {
            "title": "Observe a round shape",
            "objective": "Notice one visible detail.",
            "instructions_text": "Observe the shape with an adult nearby.",
            "safety_notes": "Stay with an adult.",
            "activity_kind": "outdoor",
            "source": "AI_DRAFT",
            "lesson_id": None,
            "version_id": None,
            "content_sha256": None,
        },
        "lesson_direction": None,
        "context_entries": [],
    }

    modal_input = _current_modal_story_worker_input(worker_input)

    assert modal_input["schema_version"] == "sketch2life.story-generation-input.v1"
    assert "activity" not in modal_input
    assert "context_entries" not in modal_input
