from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from deployment.modal.srs_v23 import language_audio_app as worker_app  # noqa: E402

_parent_activity_suggestion_json_schema = worker_app._parent_activity_suggestion_json_schema
_parent_activity_suggestion_prompt = worker_app._parent_activity_suggestion_prompt
_parse_parent_activity_suggestions = worker_app._parse_parent_activity_suggestions
_validate_parent_activity_suggestion_input = worker_app._validate_parent_activity_suggestion_input
WorkerContractError = worker_app.WorkerContractError


def _sentence(body: str) -> dict[str, str]:
    return {"body": body, "terminator": "."}


def _activity(title: str, index: int = 0) -> dict[str, object]:
    objective, preparation, safety = worker_app._PARENT_ACTIVITY_FALLBACK_MARKERS[index]
    content_title, materials, observation = worker_app._PARENT_ACTIVITY_CONTENT_MARKERS[index]
    return {
        "title": content_title,
        "objective": _sentence(objective),
        "materials_text": materials,
        "preparation_text": _sentence(preparation),
        "instructions_text": {
            "first_sentence": _sentence("Bước một"),
            "second_sentence": _sentence("Bước hai"),
        },
        "observation_notes": observation,
        "safety_notes": _sentence(safety),
        "activity_kind": "outdoor",
    }


def _activities(*titles: str) -> list[dict[str, object]]:
    return [_activity(title, index) for index, title in enumerate(titles)]


def _candidate_activity(title: str) -> dict[str, str]:
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
                "activity": _candidate_activity("Quan sát bướm"),
            }
        ],
    }


def test_worker_input_contract_accepts_bounded_versioned_candidates():
    _validate_parent_activity_suggestion_input(_input())
    schema = _parent_activity_suggestion_json_schema()
    assert schema["properties"]["fallback_activities"]["maxItems"] == 3
    assert schema["properties"]["selected_candidates"]["maxItems"] == 5
    fallback_schema = _parent_activity_suggestion_json_schema(has_candidates=False)
    assert fallback_schema["properties"]["decision"]["enum"] == ["NO_MATCH"]
    assert fallback_schema["properties"]["selected_candidates"]["maxItems"] == 0
    assert fallback_schema["properties"]["fallback_activities"]["minItems"] == 3
    assert fallback_schema["properties"]["fallback_activities"]["maxItems"] == 3
    activity_schema = fallback_schema["properties"]["fallback_activities"]["items"]["properties"]
    assert activity_schema["title"]["enum"] == [
        row[0] for row in worker_app._PARENT_ACTIVITY_CONTENT_MARKERS
    ]
    assert activity_schema["objective"]["properties"]["body"]["enum"] == [
        row[0] for row in worker_app._PARENT_ACTIVITY_FALLBACK_MARKERS
    ]
    assert activity_schema["objective"]["properties"]["terminator"]["enum"] == ["."]
    assert activity_schema["materials_text"]["enum"] == [
        row[1] for row in worker_app._PARENT_ACTIVITY_CONTENT_MARKERS
    ]
    assert activity_schema["preparation_text"]["properties"]["body"]["enum"] == [
        row[1] for row in worker_app._PARENT_ACTIVITY_FALLBACK_MARKERS
    ]
    instructions = activity_schema["instructions_text"]["properties"]
    assert instructions["first_sentence"]["properties"]["body"]["enum"] == ["Bước một"]
    assert instructions["second_sentence"]["properties"]["body"]["enum"] == ["Bước hai"]
    assert activity_schema["observation_notes"]["enum"] == [
        row[2] for row in worker_app._PARENT_ACTIVITY_CONTENT_MARKERS
    ]
    assert activity_schema["safety_notes"]["properties"]["body"]["enum"] == [
        row[2] for row in worker_app._PARENT_ACTIVITY_FALLBACK_MARKERS
    ]
    assert fallback_schema["properties"]["no_match_reason"]["enum"] == [
        worker_app._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER
    ]


def test_fallback_prompt_keeps_core_sentences_concise_and_allows_list_fragments():
    prompt = _parent_activity_suggestion_prompt(_input())

    assert "ngoài trời" in prompt
    assert "khu vườn" in prompt
    assert "Worker sẽ dựng câu hướng dẫn hoàn chỉnh" in prompt
    assert "Vật liệu một/hai/ba" in prompt
    assert "first_sentence.body='Bước một'" in prompt
    assert "không tự viết nội dung các trường này" in prompt
    assert "chữ Hán" in prompt
    assert "Không dùng kéo" in prompt
    assert "vận động mô phỏng" in prompt


def test_fallback_prompt_requires_explicit_precaution_marker_for_safety_gate():
    prompt = _parent_activity_suggestion_prompt(_input())

    for marker in ("'An toàn một'", "'An toàn hai'", "'An toàn ba'"):
        assert marker in prompt
    assert "Không sửa hoặc thêm chữ vào marker" in prompt


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
        '"match_reason":"' + worker_app._PARENT_ACTIVITY_MATCH_REASON_MARKER
        + '"}],"no_match_reason":"",'
        + '"age_band_months":"72-107","fallback_activities":[]}',
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
        "no_match_reason": worker_app._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER,
        "age_band_months": "72-107",
        "fallback_activities": _activities("Hoạt động một", "Hoạt động hai", "Hoạt động ba"),
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


def test_worker_parser_renders_complete_material_and_observation_templates():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": worker_app._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER,
        "age_band_months": "72-107",
        "fallback_activities": _activities("Hoạt động một", "Hoạt động hai", "Hoạt động ba"),
    }
    parsed = _parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
    )

    assert parsed["fallback_activities"][0]["materials_text"] == "Bức tranh đã chụp."
    assert parsed["fallback_activities"][0]["observation_notes"] == (
        "Người lớn quan sát chi tiết trẻ tự chọn."
    )


def test_worker_parser_rejects_model_authored_safety_instead_of_a_marker():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": worker_app._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER,
        "age_band_months": "72-107",
        "fallback_activities": _activities("Hoạt động một", "Hoạt động hai", "Hoạt động ba"),
    }
    result["fallback_activities"][0]["safety_notes"] = _sentence(
        "Không dùng kéo hoặc"
    )

    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID_ACTIVITY_FIELD"):
        _parse_parent_activity_suggestions(
            json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
        )


def test_worker_parser_renders_subject_aware_objective_and_safety_templates():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": worker_app._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER,
        "age_band_months": "72-107",
        "fallback_activities": _activities("Hoạt động một", "Hoạt động hai", "Hoạt động ba"),
    }
    parsed = _parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False),
        expected_age_band="72-107",
        confirmed_subject="bướm tím",
    )

    activities = parsed["fallback_activities"]
    assert activities[0]["objective"] == "Trẻ quan sát hình dáng của bướm tím qua tranh."
    assert activities[1]["objective"] == "Trẻ so sánh đặc điểm của bướm tím qua thẻ."
    assert activities[2]["objective"] == "Trẻ vận động mô phỏng bướm tím ngoài sân."
    assert activities[0]["safety_notes"] == "Người lớn giám sát trẻ khi quan sát ở sân nhà."
    assert activities[1]["safety_notes"] == "Người lớn giám sát trẻ khi dùng thẻ giấy."
    assert activities[2]["safety_notes"] == "Trẻ vận động ở sân phẳng, an toàn."


def test_worker_parser_rejects_a_marker_with_modified_terminator():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": worker_app._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER,
        "age_band_months": "72-107",
        "fallback_activities": _activities("Hoạt động một", "Hoạt động hai", "Hoạt động ba"),
    }
    result["fallback_activities"][0]["objective"]["terminator"] = "!"

    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID_ACTIVITY_FIELD"):
        _parse_parent_activity_suggestions(
            json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
        )


def test_worker_parser_uses_confirmed_subject_for_safe_instruction_templates():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": worker_app._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER,
        "age_band_months": "72-107",
        "fallback_activities": _activities("Quan sát bướm", "So sánh thẻ bướm", "Tạo dáng bướm"),
    }
    parsed = _parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False),
        expected_age_band="72-107",
        confirmed_subject="bướm tím",
    )

    instructions = [
        item["instructions_text"] for item in parsed["fallback_activities"]
    ]
    assert "Trẻ quan sát hình dáng bướm tím qua tranh cùng người lớn." in instructions[0]
    assert "Trẻ so sánh đặc điểm trên hai thẻ cùng người lớn." in instructions[1]
    assert "Trẻ thử nghiệm tạo dáng mô phỏng bướm tím cùng người lớn." in instructions[2]
    assert all("Trẻ tự chọn" in value and value.count(".") == 2 for value in instructions)


def test_worker_parser_rejects_non_latin_script():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": worker_app._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER,
        "age_band_months": "72-107",
        "fallback_activities": _activities("Hoạt động một", "Hoạt động hai", "Hoạt động ba"),
    }
    result["fallback_activities"][0]["objective"]["body"] += " 見"

    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID_NON_LATIN_SCRIPT"):
        _parse_parent_activity_suggestions(
            json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
        )


def test_worker_parser_rejects_text_cut_off_mid_sentence():
    import json

    result = {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": worker_app._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER,
        "age_band_months": "72-107",
        "fallback_activities": _activities("Hoạt động một", "Hoạt động hai", "Hoạt động ba"),
    }
    result["fallback_activities"][1]["preparation_text"] = _sentence(
        "Người lớn chuẩn bị thẻ ngoài trời hoặc"
    )

    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID_ACTIVITY_FIELD"):
        _parse_parent_activity_suggestions(
            json.dumps(result, ensure_ascii=False), expected_age_band="72-107"
        )
