from __future__ import annotations

import json

import pytest

from deployment.modal.srs_v23 import language_audio_app as worker


def _sentence(body: str) -> dict[str, str]:
    return {"body": body, "terminator": "."}


def _activity(index: int, preparation: str) -> dict[str, object]:
    titles = ("Quan sát mai rùa", "So sánh màu sắc", "Bước chân rùa con")
    focuses = ("NOTICE_AND_RECORD", "COMPARE_AND_CLASSIFY", "MOVEMENT_GAME")
    materials = ("Tranh rùa, giấy và bút màu", "Thẻ màu, giấy và bút sáp", "Sân trống và vạch giấy")
    return {
        "title": titles[index],
        "activity_focus": focuses[index],
        "objective": _sentence("Trẻ tìm một đặc điểm của rùa và kể lại điều mình nhận ra"),
        "materials_text": materials[index],
        "preparation_text": _sentence(preparation),
        "steps": [
            _sentence("Trẻ chọn một chi tiết của rùa trên tranh để quan sát"),
            _sentence("Trẻ dùng bút khoanh màu của chi tiết mình đã chọn"),
            _sentence("Trẻ kể phát hiện của mình cho người lớn nghe"),
        ],
        "observation_notes": _sentence("Người lớn ghi nhận chi tiết trẻ tự chọn và cách trẻ kể"),
        "safety_notes": _sentence("Người lớn ở cạnh trẻ và giữ hoạt động trong sân nhà an toàn"),
        "activity_kind": "outdoor",
    }


def _result(preparation: str) -> dict[str, object]:
    return {
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": worker._PARENT_ACTIVITY_NO_MATCH_REASON_MARKER,
        "age_band_months": "36-71",
        "fallback_activities": [
            _activity(0, preparation),
            _activity(1, "Người lớn đặt thẻ màu và giấy trên bàn ngoài hiên."),
            _activity(2, "Người lớn chọn khoảng sân bằng phẳng, không có vật cản."),
        ],
    }


def test_parent_activity_detail_schema_allows_complete_sentence_over_old_limit() -> None:
    schema = worker._parent_activity_suggestion_json_schema(has_candidates=False)
    activity_schema = schema["properties"]["fallback_activities"]["items"]["properties"]
    for field in ("preparation_text", "observation_notes", "safety_notes"):
        assert activity_schema[field]["properties"]["body"]["maxLength"] == 479

    body = (
        "Người lớn chuẩn bị giấy và bút màu ở hiên nhà để trẻ so sánh màu mai rùa "
        "rồi kể điều vừa phát hiện; "
    ) * 4
    body = body.rstrip(" ;")
    assert len(body) > 299

    parsed = worker._parse_parent_activity_suggestions(
        json.dumps(_result(body), ensure_ascii=False), expected_age_band="36-71"
    )

    assert parsed["fallback_activities"][0]["preparation_text"] == f"{body}."


def test_parent_activity_drops_a_draft_with_a_dangling_tail_and_keeps_the_rest() -> None:
    result = _result("Người lớn chuẩn bị giấy và bút màu cho trẻ quan sát và")

    parsed = worker._parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
    )

    assert [item["title"] for item in parsed["fallback_activities"]] == [
        "So sánh màu sắc",
        "Bước chân rùa con",
    ]


def test_parent_activity_still_rejects_when_every_draft_has_a_dangling_tail() -> None:
    result = _result("Người lớn chuẩn bị giấy và bút màu cho trẻ quan sát và")
    for activity in result["fallback_activities"]:
        activity["preparation_text"] = _sentence("Người lớn chuẩn bị giấy và bút màu cho trẻ quan sát và")

    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT"):
        worker._parse_parent_activity_suggestions(
            json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
        )


def test_parent_activity_forwards_all_four_valid_drafts_for_the_backend_to_choose() -> None:
    result = _result("Người lớn chuẩn bị vật liệu trên hiên nhà trước khi trẻ bắt đầu.")
    extra = _activity(2, "Người lớn chuẩn bị vật liệu trên hiên nhà trước khi trẻ bắt đầu.")
    extra["title"] = "Tìm dấu chân rùa"
    result["fallback_activities"].append(extra)

    parsed = worker._parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
    )

    assert [item["title"] for item in parsed["fallback_activities"]] == [
        "Quan sát mai rùa",
        "So sánh màu sắc",
        "Bước chân rùa con",
        "Tìm dấu chân rùa",
    ]


def test_parent_activity_schema_asks_for_four_drafts_when_no_candidates() -> None:
    schema = worker._parent_activity_suggestion_json_schema(has_candidates=False)
    drafts = schema["properties"]["fallback_activities"]
    assert drafts["minItems"] == 5 and drafts["maxItems"] == 5


def test_parent_activity_prompt_requires_complete_preparation_sentence_endings() -> None:
    prompt = worker._parent_activity_suggestion_prompt({})

    assert "Riêng preparation_text phải là một câu ngắn, trọn ý" in prompt
    assert "không kết thúc bằng từ nối" in prompt
    assert "'để', 'với', 'của', 'trong'" in prompt
    assert "Nêu rõ trẻ/bé/các em" in prompt
    assert "nhìn kỹ, theo dõi, lắng nghe" in prompt
    assert "đếm, ghi lại, mô tả điều vừa thấy hoặc đặt câu hỏi" in prompt


def test_parent_activity_parser_allows_repeated_internal_focus_labels() -> None:
    result = _result("Người lớn chuẩn bị vật liệu trên hiên nhà trước khi trẻ bắt đầu.")
    for activity in result["fallback_activities"]:
        activity["activity_focus"] = "COMPARE_AND_CLASSIFY"

    parsed = worker._parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
    )

    assert len(parsed["fallback_activities"]) == 3
    assert [item["title"] for item in parsed["fallback_activities"]] == [
        "Quan sát mai rùa",
        "So sánh màu sắc",
        "Bước chân rùa con",
    ]


def test_parent_activity_parser_allows_shared_materials_with_distinct_activity_content() -> None:
    result = _result("Người lớn chuẩn bị vật liệu trên hiên nhà trước khi trẻ bắt đầu.")
    for activity in result["fallback_activities"]:
        activity["materials_text"] = "Giấy, bút màu và thẻ hình do người lớn chuẩn bị"

    parsed = worker._parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
    )

    assert len(parsed["fallback_activities"]) == 3
    assert len({item["title"] for item in parsed["fallback_activities"]}) == 3


def test_parent_activity_parser_still_requires_known_focus_label() -> None:
    result = _result("Người lớn chuẩn bị vật liệu trên hiên nhà trước khi trẻ bắt đầu.")
    result["fallback_activities"][0]["activity_focus"] = "UNKNOWN_FOCUS"

    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID_ACTIVITY_FOCUS"):
        worker._parse_parent_activity_suggestions(
            json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
        )


def test_parent_activity_parser_drops_a_duplicate_title_draft() -> None:
    result = _result("Người lớn chuẩn bị vật liệu trên hiên nhà trước khi trẻ bắt đầu.")
    result["fallback_activities"][1]["title"] = result["fallback_activities"][0]["title"]

    parsed = worker._parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
    )

    assert [item["title"] for item in parsed["fallback_activities"]] == [
        "Quan sát mai rùa",
        "Bước chân rùa con",
    ]


def test_parent_activity_schema_and_parser_require_exactly_three_steps() -> None:
    schema = worker._parent_activity_suggestion_json_schema(has_candidates=False)
    steps_schema = schema["properties"]["fallback_activities"]["items"]["properties"]["steps"]
    assert steps_schema["minItems"] == 3
    assert steps_schema["maxItems"] == 3

    result = _result("Người lớn chuẩn bị vật liệu trên hiên nhà trước khi trẻ bắt đầu.")
    result["fallback_activities"][0]["steps"].append(
        _sentence("Trẻ kể lại điều mình vừa nhận ra cho người lớn")
    )
    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID_ACTIVITY_STEPS"):
        worker._parse_parent_activity_suggestions(
            json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
        )
