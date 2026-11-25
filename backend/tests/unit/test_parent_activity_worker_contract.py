from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from deployment.modal.srs_v23 import language_audio_app as worker  # noqa: E402
from sketch2life.contracts.schemas.modal_ai import (  # noqa: E402
    PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH,
    ParentActivityFallbackDraftV1,
    ParentActivitySuggestionWorkerResponseV2,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (  # noqa: E402
    _story_primary_activity,
)


def _sentence(body: str) -> dict[str, str]:
    return {"body": body, "terminator": "."}


def _activity(index: int, preparation: str) -> dict[str, object]:
    titles = ("Quan sát mai rùa", "So sánh màu sắc", "Bước chân rùa con")
    focuses = ("NOTICE_AND_RECORD", "COMPARE_AND_CLASSIFY", "MOVEMENT_GAME")
    materials = ("Tranh rùa, giấy và bút màu", "Thẻ màu, giấy và bút sáp", "Sân trống và vạch giấy")
    return {
        "title": titles[index],
        "activity_focus": focuses[index],
        "objective": _sentence("Trẻ tìm một đặc điểm của rùa và kể điều mình nhận ra"),
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


def _fallback_result(preparation: str) -> dict[str, object]:
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


def _render_fallback(preparation: str):
    result = _fallback_result(preparation)
    parsed = worker._parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
    )
    return ParentActivitySuggestionWorkerResponseV2.model_validate(
        {"schema_version": "sketch2life.parent-activity-suggestions.v2", **parsed}
    )


def test_worker_contract_and_prompt_keep_three_realistic_bounded_drafts():
    schema = worker._parent_activity_suggestion_json_schema(has_candidates=False)
    activity_schema = schema["properties"]["fallback_activities"]["items"]["properties"]
    # FEAT-092: the worker drafts four so a draft failing a quality gate can be dropped; at most
    # three reach the backend contract.
    assert schema["properties"]["fallback_activities"]["minItems"] == 4
    assert schema["properties"]["fallback_activities"]["maxItems"] == 4
    for field in ("preparation_text", "observation_notes", "safety_notes"):
        assert (
            activity_schema[field]["properties"]["body"]["maxLength"]
            == PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH - 1
        )

    prompt = worker._parent_activity_suggestion_prompt(
        {
            "age_band_ref": "age-36-71-months-v1",
            "topic": "động vật",
            "adult_confirmed_idea": "",
            "confirmed_subject": "rùa",
            "visible_features": ["mai xanh"],
            "age_band_months": "36-71",
            "profile_interest_tags": [],
            "narration_interest_tags": [],
            "candidate_activities": [],
        }
    )
    assert "đời sống thường ngày" in prompt
    assert "3–5 bước" in prompt
    assert "khoảng 180 ký tự" in prompt
    assert "Không gợi ý ra đường" in prompt


def test_worker_parser_and_backend_contract_accept_complete_detail_over_300_chars():
    preparation = (
        "Người lớn chuẩn bị giấy và bút màu ở hiên nhà để trẻ so sánh màu mai rùa "
        "rồi kể điều vừa phát hiện; "
    ) * 4
    preparation = preparation.rstrip(" ;")
    assert 300 < len(preparation) < PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH

    response = _render_fallback(preparation)

    assert len(response.fallback_activities) == 3
    assert response.fallback_activities[0].preparation_text == f"{preparation}."


def test_backend_worker_contract_rejects_detail_over_shared_ceiling():
    preparation = (
        "Người lớn chuẩn bị giấy và bút màu ở hiên nhà để trẻ so sánh màu mai rùa "
        "rồi kể điều vừa phát hiện; "
    ) * 8
    preparation = preparation.rstrip(" ;") + "."
    assert len(preparation) > PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH

    with pytest.raises(ValidationError):
        ParentActivityFallbackDraftV1(
            title="Quan sát mai rùa",
            objective="Trẻ tìm một đặc điểm của rùa.",
            materials_text="Tranh rùa và giấy màu",
            preparation_text=preparation,
            instructions_text="1. Trẻ chọn chi tiết.\n2. Trẻ quan sát.\n3. Trẻ kể lại.",
            observation_notes="Người lớn ghi nhận điều trẻ tự chọn.",
            safety_notes="Người lớn ở cạnh trẻ trong sân nhà an toàn.",
            activity_kind="outdoor",
        )


def test_worker_parser_still_rejects_dangling_tail():
    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT"):
        _render_fallback("Người lớn chuẩn bị giấy và bút màu cho trẻ quan sát và")


def test_worker_parser_selects_only_candidate_refs_for_catalog_match():
    result = {
        "decision": "CATALOG_MATCH",
        "selected_candidates": [
            {
                "candidate_ref": "C001",
                "match_reason": worker._PARENT_ACTIVITY_MATCH_REASON_MARKER,
            }
        ],
        "no_match_reason": "",
        "age_band_months": "36-71",
        "fallback_activities": [],
    }

    parsed = worker._parse_parent_activity_suggestions(
        json.dumps(result, ensure_ascii=False), expected_age_band="36-71"
    )

    assert parsed["decision"] == "CATALOG_MATCH"
    assert parsed["selected_candidates"] == [
        {
            "candidate_ref": "C001",
            "match_reason": "Phù hợp với chủ đề, độ tuổi và nội dung tranh đã xác nhận.",
        }
    ]
    assert parsed["fallback_activities"] == []


def test_worker_rejects_identity_and_artwork_fields_in_activity_request():
    data = {
        "schema_version": "sketch2life.parent-activity-suggest-input.v3",
        "age_band_months": "36-71",
        "age_band_ref": "age-36-71-months-v1",
        "topic": "động vật",
        "adult_confirmed_idea": "",
        "confirmed_subject": "rùa",
        "visible_features": ["mai xanh"],
        "profile_interest_tags": [],
        "narration_interest_tags": [],
        "candidate_activities": [],
    }
    worker._validate_parent_activity_suggestion_input(data)
    data["image_base64"] = "not-allowed"

    with pytest.raises(worker.WorkerContractError, match="MODAL_INPUT_NOT_ALLOWED"):
        worker._validate_parent_activity_suggestion_input(data)


def test_selected_activity_snapshot_preserves_detail_over_old_limit():
    preparation = "Người lớn chuẩn bị giấy và bút màu cho trẻ quan sát rùa. " * 7
    preparation = preparation.strip()
    assert 300 < len(preparation) <= PARENT_ACTIVITY_DETAIL_TEXT_MAX_LENGTH
    activity = {
        "title": "Quan sát mai rùa",
        "objective": "Trẻ tìm một đặc điểm của rùa.",
        "materials_text": "Tranh rùa, giấy và bút màu",
        "preparation_text": preparation,
        "instructions_text": "1. Trẻ chọn chi tiết.\n2. Trẻ quan sát.\n3. Trẻ kể lại.",
        "observation_notes": "Người lớn ghi nhận điều trẻ tự chọn.",
        "safety_notes": "Người lớn ở cạnh trẻ trong sân nhà an toàn.",
        "activity_kind": "outdoor",
    }

    stored = _story_primary_activity(activity)

    assert stored["preparation_text"] == preparation


def test_backend_contract_accepts_one_to_three_fallback_drafts_and_rejects_four_or_none():
    base = _render_fallback("Người lớn chuẩn bị giấy và bút màu ở hiên nhà để trẻ so sánh màu mai rùa.")
    payload = base.model_dump(mode="json")
    drafts = payload["fallback_activities"]

    for count in (1, 2, 3):
        ParentActivitySuggestionWorkerResponseV2.model_validate(
            {**payload, "fallback_activities": drafts[:count]}
        )
    for bad in ([], drafts + drafts[:1]):
        with pytest.raises(ValidationError):
            ParentActivitySuggestionWorkerResponseV2.model_validate(
                {**payload, "fallback_activities": bad}
            )
