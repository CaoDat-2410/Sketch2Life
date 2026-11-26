"""FEAT-093 Amendment D (live Run 1): nobody the child did not draw, and subjects that stand on the ground."""

from __future__ import annotations

import pytest

from sketch2life.application.video_pipeline.visual_prompt_guard import (
    drawn_only_prompt,
    is_airborne,
    person_is_drawn,
)


def test_a_clause_with_a_person_is_removed_from_a_scene_prompt() -> None:
    prompt = "A child points at the black saddle, the red bicycle stands under a tree, crayon style."

    guarded = drawn_only_prompt(prompt, person_drawn=False)

    assert "child" not in guarded.lower()
    assert "red bicycle stands under a tree" in guarded
    assert guarded.startswith("The drawn subject moves gently.")
    assert guarded.endswith("nothing new enters the frame.")


def test_a_prompt_without_people_only_gains_the_closing_sentence() -> None:
    guarded = drawn_only_prompt("The red bicycle rolls forward, crayon style.", person_drawn=False)

    assert guarded.startswith("The red bicycle rolls forward, crayon style.")
    assert guarded.endswith("nothing new enters the frame.")


def test_a_drawn_person_keeps_the_prompt_unchanged() -> None:
    assert drawn_only_prompt("A girl waves.", person_drawn=True) == "A girl waves."


@pytest.mark.parametrize(
    ("labels", "drawn"),
    [(("xe đạp", "hoa"), False), (("con ong",), False), (("bé gái", "hoa"), True), (("người nông dân",), True),
     (("mẹ",), True), (("con bò",), False)],
)
def test_a_person_is_drawn_only_when_a_label_names_one(labels: tuple[str, ...], drawn: bool) -> None:
    assert person_is_drawn(labels) is drawn


@pytest.mark.parametrize(
    ("label", "airborne"),
    [("con bướm", True), ("máy bay", True), ("con chim", True), ("con cá", True), ("xe đạp", False),
     ("con rùa", False), ("con gà con", False), ("cái cây", False)],
)
def test_only_flying_or_floating_subjects_keep_their_height(label: str, airborne: bool) -> None:
    assert is_airborne(label) is airborne
