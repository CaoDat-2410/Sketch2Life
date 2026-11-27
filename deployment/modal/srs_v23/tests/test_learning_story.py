"""FEAT-094 phase 4: the Qwen worker writes one learning script and checks it before answering."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import learning_story as learning  # noqa: E402

FACTS = [
    {"id": "what", "kind": "WHAT_IT_IS", "part": None, "text": "Gà là một loài chim.", "key_terms": ["loài chim"]},
    {"id": "beak", "kind": "PART", "part": "mỏ", "text": "Gà dùng mỏ để mổ thóc.", "key_terms": ["mỏ"]},
    {"id": "use", "kind": "USE", "part": None, "text": "Gà mái đẻ trứng.", "key_terms": ["trứng"]},
]
NARRATIONS = [
    "Gà Vàng là một loài chim đáng yêu. Bạn ấy sống ở sân vườn.",
    "Gà Vàng dùng chiếc mỏ nhỏ xinh. Bạn ấy mổ từng hạt thóc vàng.",
    "Buổi trưa trời nắng to quá. Gà Vàng đi tìm bóng mát dưới cây.",
    "Khi đã lớn, gà mái đẻ trứng. Những quả trứng tròn nằm trong ổ.",
    "Gà Vàng vui vẻ vẫy chiếc đuôi. Bạn ấy chào buổi chiều trong vườn.",
]


def _block(**changes: Any) -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.learning-request.v1",
        "scene_count": 5,
        "scene_seconds": 10,
        "max_words": 18,
        "fact_count": 3,
        "facts": FACTS,
        "fact_source": "CARD",
        "motion_hints": ["con gà mổ thóc"],
        "setting": "sân vườn",
        "interest_tags": ["vehicles"],
        **changes,
    }


def _data(**changes: Any) -> dict[str, Any]:
    return {
        "confirmed_subject": "con gà",
        "visible_features": ["mỏ cam", "đuôi hồng"],
        "child_age_months": 48,
        "topic": "Các loài chim",
        "adult_confirmed_idea": "",
        "rewrite_instruction": None,
        "lesson_subject_learning_notes": None,
        "learning": _block(),
        **changes,
    }


def _script(narrations: list[str] = NARRATIONS) -> str:
    return json.dumps(
        {
            "title": "Gà Vàng trong vườn",
            "scenes": [
                {
                    "title": f"Cảnh vườn {index}",
                    "narration": text,
                    "key_term": "gà",
                    "action_en": "The chick pecks the ground gently.",
                    "setting_en": "A sunny farm yard with green grass.",
                }
                for index, text in enumerate(narrations, start=1)
            ],
        },
        ensure_ascii=False,
    )


class _Model:
    def __init__(self, *answers: str) -> None:
        self.answers = list(answers)
        self.prompts: list[str] = []
        self.schemas: list[dict[str, Any]] = []

    def __call__(self, system: str, prompt: str, schema: dict[str, Any], max_tokens: int) -> str:
        self.prompts.append(prompt)
        self.schemas.append(schema)
        return self.answers.pop(0)


NO_CLAIMS = json.dumps({"scenes_with_other_facts": []})


def test_the_request_block_is_checked_before_any_model_call() -> None:
    assert learning.request_valid(_block()) and learning.request_valid(_block(facts=[], fact_source="AI_DRAFT"))
    for broken in (
        _block(scene_count=4),
        _block(max_words=60),
        _block(fact_count=1),
        _block(fact_source="WEB"),
        _block(facts=FACTS[:2]),
        _block(schema_version="other"),
        _block(interest_tags=["x" * 80]),
        {"scene_count": 5},
        None,
    ):
        assert not learning.request_valid(broken)


@pytest.mark.parametrize(
    "scenes, facts, expected",
    [
        (5, 3, ["what", "p1", None, "use", None]),
        (6, 4, ["what", "p1", "p2", None, "use", None]),
        (7, 5, ["what", "p1", "p2", "p3", None, "use", None]),
    ],
)
def test_the_code_decides_which_scene_tells_which_fact(scenes: int, facts: int, expected: list[Any]) -> None:
    chosen = [{"id": "what"}, *({"id": f"p{i}"} for i in range(1, facts - 1)), {"id": "use"}]

    assigned = learning.assign_facts(scenes, chosen)

    assert [fact and fact["id"] for fact in assigned] == expected


def test_a_script_from_approved_facts_needs_one_writing_call_and_one_claim_check() -> None:
    model = _Model(_script(), NO_CLAIMS)

    story, block = learning.generate_learning_story(_data(), model)

    assert story["schema_version"] == "sketch2life.story-revision.v1" and story["duration_ms"] == 50_000
    assert [scene["narration"] for scene in story["scenes"]] == NARRATIONS
    assert [scene["start_ms"] for scene in story["scenes"]] == [0, 10_000, 20_000, 30_000, 40_000]
    assert story["scenes"][0]["visual_prompt"] == "The chick pecks the ground gently."
    assert story["scenes"][0]["character_anchors"] == ["mỏ cam", "đuôi hồng"]
    assert story["story"]["opening"] == NARRATIONS[0] and story["story"]["ending"] == NARRATIONS[-1]
    assert story["story"]["middle"] == " ".join(NARRATIONS[1:-1])
    assert block["fact_source"] == "CARD" and block["facts"] == FACTS
    assert [entry["fact_id"] for entry in block["scenes"]] == ["what", "beak", None, "use", None]
    assert block["scenes"][1]["part"] == "mỏ"
    assert "Gà dùng mỏ để mổ thóc." in model.prompts[0] and "18" in model.prompts[0]


def test_a_broken_rule_is_named_to_the_model_and_the_script_written_again() -> None:
    long = list(NARRATIONS)
    long[2] = " ".join(["gà"] * 25) + "."
    model = _Model(_script(long), _script(), NO_CLAIMS)

    story, _block_out = learning.generate_learning_story(_data(), model)

    assert story["scenes"][2]["narration"] == NARRATIONS[2]
    assert "LEARNING_NARRATION_TOO_LONG" in model.prompts[1] and "LEARNING" not in model.prompts[0]


def test_narration_that_leaves_the_scene_silent_is_written_again_but_never_blocks_the_last_attempt() -> None:
    thin = list(NARRATIONS)
    thin[4] = "Gà Vàng đi ngủ ngoan."
    model = _Model(_script(thin), _script(thin), _script(thin))

    story, _block_out = learning.generate_learning_story(_data(), model)

    assert story["scenes"][4]["narration"] == thin[4] and len(model.prompts) == 3
    assert "LEARNING_NARRATION_TOO_THIN" in model.prompts[1]


def test_lines_well_under_the_word_cap_are_asked_for_again() -> None:
    short = list(NARRATIONS)
    short[2] = "Buổi trưa, Gà Vàng đi tìm bóng mát dưới gốc cây."  # 11 words, about three seconds of voice
    model = _Model(_script(short), _script(), NO_CLAIMS)

    story, _block_out = learning.generate_learning_story(_data(), model)

    assert story["scenes"][2]["narration"] == NARRATIONS[2]
    assert "LEARNING_NARRATION_TOO_THIN" in model.prompts[1] and "14 đến 18 từ" in model.prompts[0]


@pytest.mark.parametrize("action", ["The chick flaps its wings.", "The chick jumps up high.", "The chick spins around."])
def test_a_fast_motion_that_smears_the_drawing_is_written_again(action: str) -> None:
    fast = json.loads(_script())
    fast["scenes"][2]["action_en"] = action
    model = _Model(json.dumps(fast, ensure_ascii=False), _script(), NO_CLAIMS)

    story, _block_out = learning.generate_learning_story(_data(), model)

    assert story["scenes"][2]["visual_prompt"] == "The chick pecks the ground gently."
    assert "LEARNING_ACTION_TOO_FAST" in model.prompts[1]


def test_a_fast_motion_never_blocks_the_last_attempt() -> None:
    fast = json.loads(_script())
    fast["scenes"][2]["action_en"] = "The chick flaps its wings."
    text = json.dumps(fast, ensure_ascii=False)
    model = _Model(text, text, text, NO_CLAIMS)

    story, _block_out = learning.generate_learning_story(_data(), model)

    assert story["scenes"][2]["visual_prompt"] == "The chick flaps its wings." and len(model.prompts) == 3


def test_three_broken_scripts_end_the_job_with_the_last_rule() -> None:
    short = list(NARRATIONS)
    short[1] = "Gà đi chơi."
    model = _Model(_script(short), _script(short), _script(short))

    with pytest.raises(learning.LearningStoryError, match="LEARNING_FACT_TERM_MISSING|LEARNING_NARRATION_TOO_SHORT"):
        learning.generate_learning_story(_data(), model)

    assert len(model.prompts) == 3


def test_a_claim_outside_the_facts_is_rewritten_but_never_blocks_the_last_attempt() -> None:
    claims = json.dumps({"scenes_with_other_facts": [3]})
    model = _Model(_script(), claims, _script(), claims, _script())

    story, _block_out = learning.generate_learning_story(_data(), model)

    assert len(story["scenes"]) == 5 and len(model.prompts) == 5
    assert "LEARNING_UNLISTED_CLAIM" in model.prompts[2]


def test_without_facts_the_model_drafts_them_and_a_second_pass_drops_the_doubtful_ones() -> None:
    candidates = [
        FACTS[0],
        {"id": "wing", "kind": "PART", "part": "cánh", "text": "Cánh giúp gà bay đến mặt trăng.", "key_terms": ["cánh"]},
        FACTS[1],
        FACTS[2],
    ]
    draft = json.dumps(
        {"facts": [{k: v for k, v in fact.items() if k != "id"} for fact in candidates]}, ensure_ascii=False
    )
    review = json.dumps({"doubtful": [2]})
    model = _Model(draft, review, _script(), NO_CLAIMS)

    _story, block = learning.generate_learning_story(
        _data(learning=_block(facts=[], fact_source="AI_DRAFT")), model
    )

    assert block["fact_source"] == "AI_DRAFT"
    assert [fact["part"] for fact in block["facts"]] == [None, "mỏ", None]
    assert "con gà" in model.prompts[0]


def test_lesson_notes_are_the_only_ground_for_lesson_facts() -> None:
    draft = json.dumps({"facts": [{k: v for k, v in f.items() if k != "id"} for f in FACTS]}, ensure_ascii=False)
    model = _Model(draft, json.dumps({"doubtful": []}), _script(), NO_CLAIMS)
    data = _data(
        learning=_block(facts=[], fact_source="LESSON"), lesson_subject_learning_notes="Gà có mỏ và đẻ trứng."
    )

    _story, block = learning.generate_learning_story(data, model)

    assert block["fact_source"] == "LESSON"
    assert "Gà có mỏ và đẻ trứng." in model.prompts[0] and "Gà có mỏ và đẻ trứng." in model.prompts[1]


def test_too_few_usable_draft_facts_end_the_job() -> None:
    draft = json.dumps({"facts": [{k: v for k, v in FACTS[0].items() if k != "id"}]}, ensure_ascii=False)
    model = _Model(draft, json.dumps({"doubtful": []}), draft, json.dumps({"doubtful": []}))

    with pytest.raises(learning.LearningStoryError, match="LEARNING_FACTS_UNAVAILABLE"):
        learning.generate_learning_story(_data(learning=_block(facts=[], fact_source="AI_DRAFT")), model)


def test_interests_and_motion_hints_reach_the_writing_prompt_as_data() -> None:
    model = _Model(_script(), NO_CLAIMS)

    learning.generate_learning_story(_data(), model)

    assert "vehicles" in model.prompts[0] and "con gà mổ thóc" in model.prompts[0]


def test_every_schema_is_closed_so_the_model_cannot_add_fields() -> None:
    draft = json.dumps({"facts": [{k: v for k, v in f.items() if k != "id"} for f in FACTS]}, ensure_ascii=False)
    model = _Model(draft, json.dumps({"doubtful": []}), _script(), NO_CLAIMS)

    learning.generate_learning_story(_data(learning=_block(facts=[], fact_source="AI_DRAFT")), model)

    for schema in model.schemas:
        assert schema["additionalProperties"] is False and set(schema["required"]) == set(schema["properties"])


def test_the_length_is_asked_for_sentence_by_sentence() -> None:
    model = _Model(_script(), NO_CLAIMS)

    learning.generate_learning_story(_data(), model)

    # The writer ignored a total word range in the live run; counts per sentence are easier to follow.
    assert "mỗi câu từ 7 đến 9 từ" in model.prompts[0]


@pytest.mark.parametrize("setting", ["Close-up of the chicken near grains.", "A yard with two dogs and grass."])
def test_a_background_that_names_an_animal_is_written_again(setting: str) -> None:
    named = json.loads(_script())
    named["scenes"][1]["setting_en"] = setting
    model = _Model(json.dumps(named, ensure_ascii=False), _script(), NO_CLAIMS)

    _story, block = learning.generate_learning_story(_data(), model)

    assert block["scenes"][1]["setting_en"] == "A sunny farm yard with green grass."
    assert "LEARNING_SETTING_HAS_ANIMAL" in model.prompts[1]
