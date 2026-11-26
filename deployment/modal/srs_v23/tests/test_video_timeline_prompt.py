"""FEAT-093 Amendment C: the timeline prompt keeps its rule lines and a rejected draft is not repeated."""

from __future__ import annotations

import sys
from pathlib import Path

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import video_timeline  # noqa: E402

DATA = {
    "age_band": {
        "band": "3-5", "scene_count": 5, "scene_seconds": 6, "narration_max_words": 7,
        "dialogue_max_lines": 1, "dialogue_max_words": 3, "secondary_max": 1,
    },
    "topic": "Động vật",
    "story": {"title": "Rùa"},
    "subjects": [{"entity_id": "main", "label": "rùa", "role": "main"}],
    "activity": {"title": "t", "objective": "o"},
    "previous_error": None,
}


def test_the_rules_are_separate_lines() -> None:
    prompt = video_timeline.system_prompt(DATA)

    assert "\n\nQuy tắc về lời kể và lời thoại" in prompt
    assert "\n- narration:" in prompt and "\n- dialogue:" in prompt
    assert "\n\nQuy tắc về hình ảnh:" in prompt
    assert "\n\nVí dụ định dạng" in prompt


def test_the_rejected_rule_is_on_its_own_line() -> None:
    prompt = video_timeline.user_prompt({**DATA, "previous_error": "LINE_TOO_MANY_WORDS"})

    assert "\nLần trước bị từ chối vì quy tắc: LINE_TOO_MANY_WORDS." in prompt


def test_the_word_limit_is_also_stated_in_characters() -> None:
    prompt = video_timeline.system_prompt(DATA)

    assert "tối đa 7 từ (không quá 38 ký tự)" in prompt
    assert "mỗi lời tối đa 3 từ (không quá 16 ký tự)" in prompt


def test_only_a_retry_samples() -> None:
    assert video_timeline.sampling_options(DATA) == {"do_sample": False}
    assert video_timeline.sampling_options({**DATA, "previous_error": "X"}) == {
        "do_sample": True, "temperature": 0.6, "top_p": 0.8,
    }


def test_a_single_subject_cannot_have_an_interaction() -> None:
    items = video_timeline.json_schema(DATA)["properties"]["scenes"]["items"]["properties"]
    assert items["interactions"]["maxItems"] == 0

    two = {**DATA, "subjects": [*DATA["subjects"], {"entity_id": "sec-1", "label": "lá", "role": "secondary"}]}
    items = video_timeline.json_schema(two)["properties"]["scenes"]["items"]["properties"]
    assert items["interactions"]["maxItems"] == 2


def test_the_prompt_says_an_interaction_needs_two_different_subjects() -> None:
    assert "actor và target phải là hai entity_id khác nhau" in video_timeline.system_prompt(DATA)
