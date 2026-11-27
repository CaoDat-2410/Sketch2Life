"""FEAT-094 phase 4: the rules a learning script has to meet, checked again by the backend (plan 6)."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from sketch2life.domain.learning_script import (
    LearningScriptError,
    band_for_age_months,
    check_learning_script,
    learning_view,
)

FACTS = [
    {"id": "what", "kind": "WHAT_IT_IS", "part": None, "text": "Gà là một loài chim.", "key_terms": ["loài chim"]},
    {"id": "beak", "kind": "PART", "part": "mỏ", "text": "Gà dùng mỏ để mổ thóc.", "key_terms": ["mỏ"]},
    {"id": "use", "kind": "USE", "part": None, "text": "Gà mái đẻ trứng.", "key_terms": ["trứng"]},
]
NARRATIONS = [
    "Gà Vàng là một loài chim đáng yêu sống ở sân vườn.",
    "Gà Vàng dùng chiếc mỏ nhỏ để mổ từng hạt thóc.",
    "Buổi trưa, Gà Vàng đi tìm bóng mát dưới gốc cây.",
    "Khi lớn lên, gà mái đẻ trứng cho mọi người.",
    "Gà Vàng vui vẻ vẫy đuôi chào buổi chiều trong vườn.",
]


def _story(narrations: list[str] | None = None) -> dict[str, Any]:
    narrations = narrations or NARRATIONS
    return {
        "scenes": [
            {"scene_index": index, "narration": text, "duration_ms": 10_000}
            for index, text in enumerate(narrations, start=1)
        ]
    }


def _learning() -> dict[str, Any]:
    fact_ids = ["what", "beak", None, "use", None]
    return {
        "fact_source": "AI_DRAFT",
        "facts": copy.deepcopy(FACTS),
        "scenes": [
            {
                "scene_index": index,
                "fact_id": fact_id,
                "key_term": "gà",
                "part": "mỏ" if fact_id == "beak" else None,
                "action_en": "The chick pecks the ground gently.",
                "setting_en": "A sunny farm yard with green grass.",
            }
            for index, fact_id in enumerate(fact_ids, start=1)
        ],
    }


def _request(**changes: Any) -> dict[str, Any]:
    return {"scene_count": 5, "scene_seconds": 10, "max_words": 18, "fact_count": 3, "facts": [], **changes}


def _check(story: dict[str, Any] | None = None, learning: dict[str, Any] | None = None, **request: Any) -> dict:
    return check_learning_script(
        story or _story(), learning or _learning(), request=_request(**request), subject="con gà"
    )


@pytest.mark.parametrize(
    "months, expected",
    [
        (36, (5, 25, 5)),
        (71, (5, 25, 5)),
        (72, (6, 32, 6)),
        (107, (6, 32, 6)),
        (108, (7, 32, 7)),
        (120, (7, 32, 7)),
    ],
)
def test_the_age_table_of_the_plan(months: int, expected: tuple[int, int, int]) -> None:
    band = band_for_age_months(months)

    assert (band.scene_count, band.max_words, band.fact_count) == expected
    assert band.scene_seconds == 10
    assert 30 <= band.scene_count * band.scene_seconds <= 90


@pytest.mark.parametrize("months", [35, 121])
def test_an_unsupported_age_is_refused(months: int) -> None:
    with pytest.raises(LearningScriptError, match="LEARNING_AGE_UNSUPPORTED"):
        band_for_age_months(months)


def test_a_complete_script_is_accepted_with_only_its_known_fields() -> None:
    learning = _learning()
    learning["unexpected"] = "dropped"

    checked = _check(learning=learning)

    assert set(checked) == {"fact_source", "facts", "scenes"}
    assert [scene["fact_id"] for scene in checked["scenes"]] == ["what", "beak", None, "use", None]


def _broken(path: str) -> tuple[dict[str, Any], dict[str, Any]]:
    story, learning = _story(), _learning()
    if path == "count":
        story["scenes"].pop()
    elif path == "words":
        story["scenes"][2]["narration"] = " ".join(["gà"] * 19) + "."
    elif path == "key_term":
        story["scenes"][1]["narration"] = "Gà Vàng đi dạo quanh sân và nhìn thấy hạt thóc."
    elif path == "missing_fact":
        learning["scenes"][1]["fact_id"] = None
    elif path == "twice":
        learning["scenes"][2]["fact_id"] = "beak"
        story["scenes"][2]["narration"] = "Buổi trưa, Gà Vàng dùng mỏ tìm bóng mát dưới gốc cây."
    elif path == "unknown_fact":
        learning["scenes"][2]["fact_id"] = "wings"
    elif path == "name":
        for scene in story["scenes"]:
            scene["narration"] = scene["narration"].replace("Gà Vàng", "Bạn ấy").replace("gà mái", "bạn ấy")
    elif path == "child":
        story["scenes"][2]["narration"] = "Bé đi tìm gà dưới bóng mát của gốc cây."
    elif path == "person":
        learning["scenes"][2]["action_en"] = "A child feeds the chick."
    elif path == "language":
        learning["scenes"][2]["setting_en"] = "Một khu vườn đầy nắng."
    elif path == "length":
        story["scenes"][3]["duration_ms"] = 6_000
    elif path == "source":
        learning["fact_source"] = "SOMEWHERE"
    return story, learning


@pytest.mark.parametrize(
    "path, code",
    [
        ("count", "LEARNING_SCENE_COUNT"),
        ("words", "LEARNING_NARRATION_TOO_LONG"),
        ("key_term", "LEARNING_FACT_TERM_MISSING"),
        ("missing_fact", "LEARNING_FACT_NOT_TOLD_ONCE"),
        ("twice", "LEARNING_FACT_NOT_TOLD_ONCE"),
        ("unknown_fact", "LEARNING_FACT_UNKNOWN"),
        ("name", "LEARNING_SUBJECT_NOT_REPEATED"),
        ("child", "LEARNING_CHILD_AS_PROTAGONIST"),
        ("person", "LEARNING_PROMPT_NOT_ALLOWED"),
        ("language", "LEARNING_PROMPT_NOT_ALLOWED"),
        ("length", "LEARNING_SCENE_LENGTH"),
        ("source", "LEARNING_SHAPE_INVALID"),
    ],
)
def test_each_broken_rule_is_named(path: str, code: str) -> None:
    story, learning = _broken(path)

    with pytest.raises(LearningScriptError) as error:
        _check(story, learning)

    assert error.value.code == code


def test_facts_given_by_the_backend_cannot_be_changed_by_the_worker() -> None:
    learning = _learning()
    learning["facts"][0]["text"] = "Gà là một loài cá."

    with pytest.raises(LearningScriptError, match="LEARNING_FACT_CHANGED"):
        _check(learning=learning, facts=copy.deepcopy(FACTS))


def test_a_person_as_the_drawn_subject_may_be_the_protagonist() -> None:
    story = _story([text.replace("Gà Vàng", "Bé gái").replace("gà mái", "bé gái") for text in NARRATIONS])

    check_learning_script(story, _learning(), request=_request(), subject="bé gái")


def test_the_adult_sees_the_learning_points_and_whether_they_were_checked() -> None:
    view = learning_view(_check())

    assert view == {
        "fact_source": "AI_DRAFT",
        "verified": False,
        "points": ["Gà là một loài chim.", "Gà dùng mỏ để mổ thóc.", "Gà mái đẻ trứng."],
    }
    assert learning_view({**_check(), "fact_source": "CARD"})["verified"] is True
    assert learning_view(None) is None


def _two_facts() -> tuple[dict[str, Any], dict[str, Any]]:
    """Four facts, the second scene telling two."""

    story, learning = _story(), _learning()
    learning["facts"].append(
        {
            "id": "tail",
            "kind": "PART",
            "part": "đuôi",
            "text": "Đuôi gà giúp giữ thăng bằng.",
            "key_terms": ["đuôi"],
        }
    )
    learning["scenes"][1]["also_fact_id"] = "tail"
    story["scenes"][1]["narration"] = "Gà Vàng dùng mỏ để mổ thóc. Đuôi gà giữ thăng bằng."
    return story, learning


def test_a_scene_may_tell_two_facts() -> None:
    story, learning = _two_facts()

    checked = _check(story, learning, fact_count=5)

    assert checked["scenes"][1]["also_fact_id"] == "tail"
    assert "also_fact_id" not in checked["scenes"][0]


@pytest.mark.parametrize(
    "damage, code",
    [
        ("term", "LEARNING_FACT_TERM_MISSING"),
        ("unknown", "LEARNING_FACT_UNKNOWN"),
        ("alone", "LEARNING_SHAPE_INVALID"),
        ("again", "LEARNING_FACT_NOT_TOLD_ONCE"),
    ],
)
def test_a_second_fact_follows_the_same_rules(damage: str, code: str) -> None:
    story, learning = _two_facts()
    if damage == "term":
        story["scenes"][1]["narration"] = "Gà Vàng dùng mỏ để mổ thóc trong sân vườn."
    elif damage == "unknown":
        learning["scenes"][1]["also_fact_id"] = "wings"
    elif damage == "alone":
        learning["scenes"][2]["also_fact_id"] = "tail"
        del learning["scenes"][1]["also_fact_id"]
    else:
        learning["scenes"][1]["also_fact_id"] = "beak"

    with pytest.raises(LearningScriptError, match=code):
        _check(story, learning, fact_count=5)


def test_more_facts_than_asked_for_are_refused_and_given_facts_must_all_be_told() -> None:
    story, learning = _two_facts()
    with pytest.raises(LearningScriptError, match="LEARNING_FACT_NOT_TOLD_ONCE"):
        _check(story, learning, fact_count=3)
    with pytest.raises(LearningScriptError, match="LEARNING_FACT_NOT_TOLD_ONCE"):
        _check(facts=[*_learning()["facts"], _two_facts()[1]["facts"][-1]], fact_count=5)
