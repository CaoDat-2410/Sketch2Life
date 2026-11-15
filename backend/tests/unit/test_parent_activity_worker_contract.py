from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from deployment.modal.srs_v23 import language_audio_app as worker_app  # noqa: E402

from sketch2life.contracts.schemas.modal_ai import (  # noqa: E402
    ParentActivityFallbackDraftV1,
    ParentActivitySuggestionWorkerRequestV3,
)

_parent_activity_suggestion_json_schema = worker_app._parent_activity_suggestion_json_schema
_parent_activity_suggestion_prompt = worker_app._parent_activity_suggestion_prompt
_parse_parent_activity_suggestions = worker_app._parse_parent_activity_suggestions
_validate_parent_activity_suggestion_input = worker_app._validate_parent_activity_suggestion_input
WorkerContractError = worker_app.WorkerContractError


def _activity(title: str) -> dict[str, str]:
    return {
        "title": title,
        "objective": "Quan sát bướm ngoài trời.",
        "materials_text": "Giấy.",
        "preparation_text": "Người lớn chọn khu vườn an toàn.",
        "instructions_text": "Trẻ tự chọn nơi để quan sát; người lớn đi cùng và hỗ trợ.",
        "observation_notes": "Ghi nhận màu sắc.",
        "safety_notes": "Không chạm côn trùng.",
        "activity_kind": "outdoor",
    }


def _input() -> dict[str, object]:
    return {
        "schema_version": "sketch2life.parent-activity-suggest-input.v3",
        "age_band_months": "72-107",
        "age_band_ref": "age-72-107-months-v1",
        "topic": "Bướm",
        "adult_confirmed_idea": "Con muốn quan sát bướm có màu tím.",
        "confirmed_subject": "Bướm",
        "visible_features": ["cánh"],
        "profile_interest_tags": ["insects"],
        "narration_interest_tags": ["colors"],
        "candidate_activities": [
            {
                "candidate_ref": "C001",
                "lesson_topic": "Bướm trong vườn",
                "drawing_subject": "Bướm",
                "age_band_months": "72-107",
                "activity": _activity("Quan sát bướm"),
            }
        ],
        "excluded_activities": [],
    }


def test_worker_input_contract_accepts_bounded_versioned_candidates():
    _validate_parent_activity_suggestion_input(_input())
    backend_schema = ParentActivitySuggestionWorkerRequestV3.model_json_schema()
    assert "excluded_activities" in backend_schema["required"]
    schema = _parent_activity_suggestion_json_schema()
    assert schema["properties"]["fallback_activities"]["maxItems"] == 3
    assert schema["properties"]["selected_candidates"]["maxItems"] == 5
    fallback_schema = _parent_activity_suggestion_json_schema(has_candidates=False)
    assert fallback_schema["properties"]["decision"]["enum"] == ["NO_MATCH"]
    assert fallback_schema["properties"]["selected_candidates"]["maxItems"] == 0
    assert fallback_schema["properties"]["fallback_activities"]["minItems"] == 3
    assert fallback_schema["properties"]["fallback_activities"]["maxItems"] == 3
    activity_schema = fallback_schema["properties"]["fallback_activities"]["items"]["properties"]
    assert activity_schema["title"] == {"type": "string", "minLength": 1, "maxLength": 80}
    assert activity_schema["objective"] == {"type": "string", "minLength": 1, "maxLength": 160}
    assert activity_schema["materials_text"] == {"type": "string", "maxLength": 120}
    assert activity_schema["preparation_text"] == {
        "type": "string",
        "minLength": 1,
        "maxLength": 180,
    }
    assert activity_schema["instructions_text"] == {
        "type": "string",
        "minLength": 16,
        "maxLength": 320,
    }
    assert activity_schema["observation_notes"] == {"type": "string", "maxLength": 120}
    assert activity_schema["safety_notes"] == {"type": "string", "minLength": 8, "maxLength": 140}
    backend_activity_schema = ParentActivityFallbackDraftV1.model_json_schema()["properties"]
    for field in activity_schema:
        for constraint in ("minLength", "maxLength"):
            assert activity_schema[field].get(constraint) == backend_activity_schema[field].get(
                constraint
            )
    assert fallback_schema["properties"]["no_match_reason"]["maxLength"] == 120


def test_fallback_prompt_keeps_core_sentences_concise_and_allows_list_fragments():
    prompt = _parent_activity_suggestion_prompt(_input())

    assert "ngoài trời" in prompt
    assert "khu vườn" in prompt
    assert "Không bắt buộc dấu câu cuối câu" in prompt
    assert "Khuyến khích trẻ tự chọn" in prompt
    assert "khoảng hai bước" in prompt
    assert "Không dùng kéo" in prompt
    assert "một bộ phương pháp cố định" in prompt
    assert "lặp lại địa điểm cho từng hoạt động" in prompt
    assert "không để người đọc tự suy ra từ activity_kind" in prompt
    assert "Chỉ dùng vật liệu an toàn do người lớn chuẩn bị" in prompt
    assert "dùng vật sắc/nóng/độc hoặc hóa chất" in prompt


def test_worker_rejects_direct_identity_or_artwork_fields():
    data = _input()
    data["image_base64"] = "not-allowed"
    with pytest.raises(WorkerContractError, match="MODAL_INPUT_NOT_ALLOWED"):
        _validate_parent_activity_suggestion_input(data)

    data = _input()
    data["adult_confirmed_idea"] = "x" * 301
    with pytest.raises(WorkerContractError, match="MODAL_INPUT_NOT_ALLOWED"):
        _validate_parent_activity_suggestion_input(data)

    data = _input()
    data["adult_confirmed_idea"] = "Liên hệ parent@example.test"
    with pytest.raises(WorkerContractError, match="MODAL_INPUT_NOT_ALLOWED"):
        _validate_parent_activity_suggestion_input(data)

    data = _input()
    data["profile_interest_tags"] = ["unexpected-identity-tag"]
    with pytest.raises(WorkerContractError, match="MODAL_INPUT_NOT_ALLOWED"):
        _validate_parent_activity_suggestion_input(data)


def test_worker_parser_accepts_catalog_selection_and_no_mix():
    parsed = _parse_parent_activity_suggestions(
        '{"decision":"CATALOG_MATCH","selected_candidates":[{"candidate_ref":"C001",'
        '"match_reason":"Khớp chủ đề bướm."}],"no_match_reason":"",'
        '"age_band_months":"72-107","fallback_activities":[]}',
        expected_age_band="72-107",
    )
    assert parsed["decision"] == "CATALOG_MATCH"
    assert parsed["selected_candidates"][0]["candidate_ref"] == "C001"
    assert parsed["fallback_activities"] == []


def test_worker_parser_requires_exactly_three_fallback_drafts():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": "Không có lựa chọn phù hợp.",
        "age_band_months": "72-107",
        "fallback_activities": [
            _activity("Hoạt động một"),
            _activity("Hoạt động hai"),
            _activity("Hoạt động ba"),
        ],
    }
    parsed = _parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
    )
    assert len(parsed["fallback_activities"]) == 3

    result["fallback_activities"].pop()
    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
        _parse_parent_activity_suggestions(
            json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
        )


def test_worker_parser_accepts_unpunctuated_materials_and_observation_fragments():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": "Không có lựa chọn phù hợp.",
        "age_band_months": "72-107",
        "fallback_activities": [
            _activity("Hoạt động một"),
            _activity("Hoạt động hai"),
            _activity("Hoạt động ba"),
        ],
    }
    result["fallback_activities"][0]["materials_text"] = "Giấy, bút sáp"
    result["fallback_activities"][0]["observation_notes"] = "Màu sắc, lựa chọn của trẻ"

    parsed = _parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
    )

    assert parsed["fallback_activities"][0]["materials_text"] == "Giấy, bút sáp"
    assert parsed["fallback_activities"][0]["observation_notes"] == "Màu sắc, lựa chọn của trẻ"


@pytest.mark.parametrize(
    "field", ["objective", "preparation_text", "instructions_text", "safety_notes"]
)
def test_worker_parser_accepts_complete_fields_without_terminal_punctuation(field):
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": "Không có lựa chọn phù hợp.",
        "age_band_months": "72-107",
        "fallback_activities": [
            _activity("Hoạt động một"),
            _activity("Hoạt động hai"),
            _activity("Hoạt động ba"),
        ],
    }
    result["fallback_activities"][0][field] = result["fallback_activities"][0][field].rstrip(
        ".!?… "
    )

    parsed = _parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
    )
    assert len(parsed["fallback_activities"]) == 3


def test_worker_parser_rejects_non_latin_script():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": "Không có lựa chọn phù hợp.",
        "age_band_months": "72-107",
        "fallback_activities": [
            _activity("Hoạt động một"),
            _activity("Hoạt động hai"),
            _activity("Hoạt động ba"),
        ],
    }
    result["fallback_activities"][0]["objective"] += " 見"

    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID_NON_LATIN_SCRIPT"):
        _parse_parent_activity_suggestions(
            json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
        )


def test_worker_parser_accepts_concise_preparation_fragment_without_punctuation():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": "Không có lựa chọn phù hợp.",
        "age_band_months": "72-107",
        "fallback_activities": [
            _activity("Hoạt động một"),
            _activity("Hoạt động hai"),
            _activity("Hoạt động ba"),
        ],
    }
    result["fallback_activities"][1]["preparation_text"] = (
        "Người lớn chuẩn bị thẻ ngoài trời"
    )

    parsed = _parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
    )
    assert parsed["fallback_activities"][1]["preparation_text"] == (
        "Người lớn chuẩn bị thẻ ngoài trời"
    )
