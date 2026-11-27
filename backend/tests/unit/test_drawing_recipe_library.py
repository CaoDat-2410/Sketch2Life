"""FEAT-097: every stored recipe passes the checks and the common names of its subject find it."""

from __future__ import annotations

import json

import pytest

from sketch2life.domain.drawing_recipe import check_recipe, parse_recipe
from sketch2life.infrastructure.svg.recipe_guide import (
    RECIPE_DIRECTORY,
    build_recipe_guide,
    find_recipe,
)
from sketch2life.resources.parent_topic_catalog_vi_v2 import TOPICS

# Catalog cards that are drawn with the recipe of the same thing (plan amendment A).
SHARED_RECIPES = {"toy-train": "train", "toy-car": "car", "school-bus": "bus"}
# Every drawing card the app can offer, with the recipe that draws it.
CARDS = [
    (card[2], SHARED_RECIPES.get(card[0], card[0].replace("-", "_")))
    for topic in TOPICS
    for card in topic["subjects"]
]
SUBJECTS = sorted({subject for _card, subject in CARDS})
FILES = sorted(RECIPE_DIRECTORY.glob("*.json"))


def test_every_subject_exists_at_both_levels() -> None:
    assert len(SUBJECTS) == 150
    assert [path.name for path in FILES] == sorted(
        f"vi.{subject}.{level}.json" for subject in SUBJECTS for level in ("beginner", "simple")
    )


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.stem)
def test_every_stored_recipe_passes_every_check(path) -> None:
    recipe = parse_recipe(json.loads(path.read_text(encoding="utf-8")))

    assert path.name == f"vi.{recipe.subject_id}.{recipe.level}.json"
    assert check_recipe(recipe) == []


@pytest.mark.parametrize("level", ["beginner", "simple"])
def test_every_catalog_card_finds_its_own_recipe(level: str) -> None:
    found = [(card, getattr(find_recipe([card], level), "subject_id", None)) for card, _ in CARDS]

    assert found == CARDS


@pytest.mark.parametrize(
    "text, subject",
    [
        ("con gà", "chicken"),
        ("Gà", "chicken"),
        ("ga", "chicken"),
        ("Con Gà Trống", "chicken"),
        ("Rùa biển", "turtle"),
        ("Rua Bien", "turtle"),
        ("con bướm", "butterfly"),
        ("buom", "butterfly"),
        ("cún con", "dog"),
        ("Bé thích vẽ con gà đang ăn", "chicken"),
    ],
)
def test_common_names_find_the_subject(text: str, subject: str) -> None:
    recipe = find_recipe([text], "beginner")

    assert recipe is not None and recipe.subject_id == subject


@pytest.mark.parametrize(
    "sentence, subject",
    [
        ("Bé muốn vẽ con cá heo nhảy", "dolphin"),
        ("Bé muốn vẽ con sâu bướm", "caterpillar"),
        ("Bé muốn vẽ con cú mèo", "owl"),
        ("Bé muốn vẽ con bọ rùa đỏ", "ladybug"),
        ("Bé muốn vẽ con cá voi xanh", "whale"),
        ("Bé muốn vẽ ngôi sao biển", "starfish"),
        ("vẽ chiếc đũa phép", "wand"),
        # Two names overlap: the one that ends later is the thing meant.
        ("vẽ cái cây cầu", "bridge"),
        ("vẽ cái bát cơm", "rice_bowl"),
        ("vẽ cái ô tô", "car"),
        ("vẽ chiếc áo mưa", "raincoat"),
        ("vẽ cái ghế công viên", "park_bench"),
        ("vẽ cái đèn đường", "streetlight"),
        # Two names apart: the first one is what the child draws, the rest says where it is.
        ("vẽ bông hoa trong chậu cây", "flower"),
        ("vẽ con gà bên ngôi nhà", "chicken"),
    ],
)
def test_the_name_that_is_meant_wins_over_a_name_inside_it(sentence: str, subject: str) -> None:
    assert find_recipe([sentence], "simple").subject_id == subject


@pytest.mark.parametrize(
    "text",
    [
        "con cá mập",
        "ngà voi",
        "con hổ",
        "khủng long",
        "",
        # Each of these holds the name of a recipe but is something else.
        "xe máy xúc",
        "máy bay trực thăng",
        "con sáo",
        "nàng tiên cá",
        "quả bóng bay",
        "cái bóng đèn",
        "con diều hâu",
        "cái cầu thang",
        "chiếc cầu trượt",
        "cái bàn chải",
        "cái đèn lồng",
        "cái đèn pin",
        "chiếc áo dài",
    ],
)
def test_other_words_find_nothing(text: str) -> None:
    assert find_recipe([text], "beginner") is None


def test_the_adults_idea_is_looked_at_before_the_topic() -> None:
    assert find_recipe(["vẽ con rùa", "con gà"], "simple").subject_id == "turtle"
    assert find_recipe(["một ngày vui", "con gà"], "simple").subject_id == "chicken"


@pytest.mark.parametrize("level", ["beginner", "simple"])
def test_a_built_guide_names_its_recipe_and_shows_the_finished_picture(level: str) -> None:
    guide = build_recipe_guide(["con gà"], level)

    assert guide is not None and guide.engine_id == "sketch2life-shape-recipe"
    assert guide.derivation_method == "AUTHORED_SHAPE_RECIPE_V1"
    assert guide.reference_source.asset_id == f"recipe-chicken-{level}"
    assert (
        len(guide.reference_illustration.paths)
        == len(guide.generated.document.paths)
        == guide.source_path_count
    )
    assert build_recipe_guide(["sao hỏa"], level) is None
