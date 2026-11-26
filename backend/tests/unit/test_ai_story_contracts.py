from __future__ import annotations

import pytest
from pydantic import ValidationError
from sketch2life.contracts.schemas.ai_story import (
    ParentStoryGenerationRequest,
    StoryRevisionDraftV1,
)
from sketch2life.contracts.schemas.story_run_lite import CreateRunRequest


def _story(*, incorrect_lifecycle: bool = False) -> dict[str, object]:
    story_text = {
        "opening": "Trên chiếc lá có một chấm trứng nhỏ.",
        "middle": "Trứng nở thành sâu bướm. Sâu bướm ăn lá, lớn lên rồi hóa nhộng.",
        "ending": (
            "Bướm trưởng thành chui ra khỏi nhộng và bay đến bông hoa."
            if not incorrect_lifecycle
            else "Trứng nở thành bướm. Bướm đi tìm tổ trên cành cây."
        ),
    }
    return {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": "Hành trình của bướm",
        "story": story_text,
        "duration_ms": 30_000,
        "scenes": [
            {
                "scene_index": index,
                "title": f"Cảnh {index}",
                "action": "Một chấm trứng nằm trên chiếc lá."
                if index == 1
                else "Sâu bướm quan sát chiếc lá.",
                "visual_prompt": "Đường nét cánh bướm đơn giản, giữ nguyên hình dáng tranh.",
                "narration": "Cùng quan sát chiếc lá.",
                "start_ms": (index - 1) * 6_000,
                "duration_ms": 6_000,
                "character_anchors": ["viền cánh tròn", "thân bướm mảnh"],
            }
            for index in range(1, 6)
        ],
    }


def test_parent_story_generation_request_rejects_activity_selection_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ParentStoryGenerationRequest.model_validate(
            {"expected_understanding_revision": 1, "activities": ["ACT-01"]}
        )


def test_create_run_requires_exact_child_age_instead_of_silently_assuming_five_years() -> None:
    with pytest.raises(ValidationError):
        CreateRunRequest.model_validate({"profile_ref": "synthetic-parent-demo"})
    assert (
        CreateRunRequest.model_validate(
            {"profile_ref": "synthetic-parent-demo", "child_age_months": 48}
        ).child_age_months
        == 48
    )


def test_story_revision_requires_ordered_scenes_and_total_duration_between_30_and_90_seconds() -> (
    None
):
    parsed = StoryRevisionDraftV1.model_validate(_story())
    assert len(parsed.scenes) == 5
    assert parsed.duration_ms == 30_000

    invalid = _story()
    invalid["scenes"][2]["start_ms"] = 1_000
    with pytest.raises(ValidationError, match="sequential"):
        StoryRevisionDraftV1.model_validate(invalid)


def test_public_story_contract_keeps_prose_as_strings_not_worker_sentence_objects() -> None:
    payload = _story()
    validated = StoryRevisionDraftV1.model_validate(payload)
    assert isinstance(validated.story["opening"], str)
    assert isinstance(validated.scenes[0].action, str)
    assert isinstance(validated.scenes[0].narration, str)

    internal_worker_shape = _story()
    internal_worker_shape["story"]["opening"] = {
        "body": "Trên chiếc lá có một chấm trứng nhỏ",
        "terminator": ".",
    }
    with pytest.raises(ValidationError):
        StoryRevisionDraftV1.model_validate(internal_worker_shape)


def test_story_contract_rejects_unfinished_paragraph_and_mixed_script() -> None:
    payload = _story()
    payload["story"]["middle"] = payload["story"]["middle"].rstrip(".")

    with pytest.raises(ValidationError, match="STORY_TEXT_INCOMPLETE"):
        StoryRevisionDraftV1.model_validate(payload)

    payload = _story()
    payload["story"]["opening"] = "Bé quan sát con rùa 完."
    with pytest.raises(ValidationError, match="STORY_TEXT_NON_LATIN_SCRIPT"):
        StoryRevisionDraftV1.model_validate(payload)


def test_story_contract_rejects_dangling_sentence_even_with_punctuation() -> None:
    payload = _story()
    payload["story"]["middle"] = "Bé đặt thẻ xuống đất để không bị."

    with pytest.raises(ValidationError, match="STORY_TEXT_INCOMPLETE"):
        StoryRevisionDraftV1.model_validate(payload)


def test_story_contract_allows_unpunctuated_english_visual_prompt() -> None:
    payload = _story()
    payload["scenes"][0]["visual_prompt"] = "A turtle card beside a child's drawing"

    parsed = StoryRevisionDraftV1.model_validate(payload)

    assert parsed.scenes[0].visual_prompt == payload["scenes"][0]["visual_prompt"]


def test_story_scene_count_is_bounded_to_srs_range() -> None:
    invalid = _story()
    invalid["scenes"] = invalid["scenes"][:4]
    with pytest.raises(ValidationError):
        StoryRevisionDraftV1.model_validate(invalid)


@pytest.mark.parametrize(
    "sentence",
    [
        "Chú rùa ngước nhìn chiếc lá ở phía trên.",
        "Rùa chậm rãi bò lên trên.",
        "Chiếc lá rơi xuống dưới.",
        "Rùa rụt đầu vào bên trong.",
        "Rùa kiên nhẫn leo qua được.",
    ],
)
def test_story_contract_accepts_complete_directional_endings(sentence: str) -> None:
    payload = _story()
    payload["story"]["middle"] = sentence

    assert StoryRevisionDraftV1.model_validate(payload).story["middle"] == sentence


@pytest.mark.parametrize("sentence", ["Rùa bò chậm trên.", "Viên sỏi đã được."])
def test_story_contract_still_rejects_bare_dangling_endings(sentence: str) -> None:
    payload = _story()
    payload["story"]["middle"] = sentence

    with pytest.raises(ValidationError, match="STORY_TEXT_INCOMPLETE"):
        StoryRevisionDraftV1.model_validate(payload)
