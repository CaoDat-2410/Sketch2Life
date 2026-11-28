from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.application.services.story_output import (
    STORY_OUTPUT_INVALID,
    StoryOutputInvalid,
    normalize_story_output,
)
from sketch2life.contracts.schemas.ai_story import (
    STORY_SENTENCE_COMPLETENESS_FALSE_POSITIVE_THRESHOLD_V1,
    VI_SENTENCE_COMPLETE_V1,
    StoryRevisionDraftV1,
    validate_story_sentence_completeness_v1,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "deployment"
    / "modal"
    / "srs_v23"
    / "tests"
    / "fixtures"
    / "story_sentence_completeness_v1.json"
)
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _valid_story() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": "Chuyến đi của chiếc lá",
        "story": {
            "opening": "Chiếc lá đung đưa trên cành.",
            "middle": "Gió đưa chiếc lá đi xa.",
            "ending": "Chiếc lá tìm được nơi nghỉ ngơi.",
        },
        "duration_ms": 30_000,
        "scenes": [
            {
                "scene_index": index,
                "title": f"Cảnh {index}",
                "action": "Bạn nhỏ nhặt chiếc lá lên.",
                "visual_prompt": "a leaf in a sunny garden",
                "narration": "Chiếc lá nằm trên lòng bàn tay.",
                "start_ms": (index - 1) * 6_000,
                "duration_ms": 6_000,
                "character_anchors": ["chiếc lá xanh"],
            }
            for index in range(1, 6)
        ],
    }


def _case_text(case: dict[str, Any]) -> str:
    if "text" in case:
        return case["text"]
    return case["repeat_char"] * case["repeat_count"] + case["suffix"]


def _apply_case(case: dict[str, Any]) -> dict[str, Any]:
    story = _valid_story()
    field = case["field"]
    value = _case_text(case)
    if field.startswith("story."):
        story["story"][field.split(".", 1)[1]] = value
    elif field.startswith("scenes["):
        scene_index = int(field.split("[", 1)[1].split("]", 1)[0]) - 1
        scene_field = field.split("].", 1)[1]
        story["scenes"][scene_index][scene_field] = value
    else:
        story[field] = value
    return story


def test_completeness_v1_validator_rejects_incomplete_vietnamese_endings_from_fixtures() -> None:
    cases = [
        case for case in FIXTURE["cases"] if case["validation"] == "sentence" and not case["valid"]
    ]
    for case in cases:
        with pytest.raises(StoryOutputInvalid) as error:
            normalize_story_output(
                _apply_case(case),
                confirmed_subject="con rong",
                completeness_rules=VI_SENTENCE_COMPLETE_V1,
            )
        assert error.value.code == STORY_OUTPUT_INVALID, case["name"]


def test_completeness_v1_validator_accepts_supported_terminal_punctuation_and_closers() -> None:
    cases = [
        case for case in FIXTURE["cases"] if case["validation"] == "sentence" and case["valid"]
    ]
    false_positive_count = 0
    for case in cases:
        try:
            normalize_story_output(
                _apply_case(case),
                confirmed_subject="con rong",
                completeness_rules=VI_SENTENCE_COMPLETE_V1,
            )
        except StoryOutputInvalid:
            false_positive_count += 1
    false_positive_rate = false_positive_count / len(cases)
    assert false_positive_rate <= STORY_SENTENCE_COMPLETENESS_FALSE_POSITIVE_THRESHOLD_V1


def test_completeness_v1_validator_ignores_visual_prompt_and_title_punctuation() -> None:
    cases = [case for case in FIXTURE["cases"] if case["validation"] == "excluded"]
    for case in cases:
        normalized, _ = normalize_story_output(
            _apply_case(case),
            confirmed_subject="con rong",
            completeness_rules=VI_SENTENCE_COMPLETE_V1,
        )
        if case["field"] == "title":
            assert normalized["title"] == case["text"]
        else:
            assert normalized["scenes"][0]["visual_prompt"] == case["text"]


def test_default_story_output_normalization_unchanged_without_completeness_rules() -> None:
    story = _valid_story()
    story["story"]["opening"] = "Bạn nhỏ nhìn quanh"

    normalized, _ = normalize_story_output(story, confirmed_subject="con rong")

    assert normalized["story"]["opening"] == "Bạn nhỏ nhìn quanh"


def test_validator_failure_diagnostics_carry_field_path_and_reason_only() -> None:
    raw_story = _valid_story()
    raw_story["story"]["opening"] = "Private sentinel runs under the leaves và."
    incomplete = StoryRevisionDraftV1.model_validate(raw_story)

    with pytest.raises(ValueError) as error:
        validate_story_sentence_completeness_v1(incomplete)

    assert str(error.value) == "story.opening:DANGLING_VI_ENDING"
    assert "Private sentinel" not in str(error.value)


@pytest.mark.parametrize("case_name", ["empty_after_strip", "over_900_character_boundary"])
def test_sentence_fixtures_retain_schema_length_boundaries(case_name: str) -> None:
    case = next(item for item in FIXTURE["cases"] if item["name"] == case_name)
    with pytest.raises(ValidationError):
        StoryRevisionDraftV1.model_validate(_apply_case(case))
