"""FEAT-097: the Parent guide comes from the project's own recipes, at the asked level."""

from __future__ import annotations

import pytest

from sketch2life.application.services.parent_svg_guide import build_parent_svg_guide
from sketch2life.infrastructure.svg.openmoji_guide import build_openmoji_guide


@pytest.mark.parametrize("subject", ["Rùa biển", "Con rùa biển", "Rua Bien"])
def test_parent_svg_guide_resolves_sea_turtle_aliases(subject: str) -> None:
    result = build_parent_svg_guide(topic="Đại dương", intended_subject=subject)

    assert result is not None
    assert result["intended_subject"] == subject
    assert result["generation_source"] == "CURATED_SOURCE_DERIVATION"
    assert result["derivation"]["engine_id"] == "sketch2life-shape-recipe"
    assert result["derivation"]["method"] == "AUTHORED_SHAPE_RECIPE_V1"
    assert result["reference_source"]["asset_id"] == "recipe-turtle-beginner"
    assert result["status"] == "DRAFT" and result["review_required"] is True
    assert 4 <= result["stage_count"] <= 8
    assert result["path_count"] <= 12


def test_the_older_level_gets_its_own_recipe() -> None:
    young = build_parent_svg_guide(topic="con gà", intended_subject=None)
    older = build_parent_svg_guide(topic="con gà", intended_subject=None, difficulty="simple")

    assert young["reference_source"]["asset_id"] == "recipe-chicken-beginner"
    assert older["reference_source"]["asset_id"] == "recipe-chicken-simple"
    assert young["document"] != older["document"]


def test_an_idea_that_names_nothing_falls_back_to_the_topic() -> None:
    result = build_parent_svg_guide(topic="con bướm", intended_subject="một ngày thật vui")

    assert result["reference_source"]["asset_id"] == "recipe-butterfly-beginner"


def test_a_subject_without_a_recipe_has_no_guide() -> None:
    assert build_parent_svg_guide(topic="Đại dương", intended_subject="Con hổ") is None


def test_openmoji_does_not_match_unrelated_sea_subject_to_turtle() -> None:
    assert build_openmoji_guide("Sao biển") is None
    assert build_openmoji_guide("Rùa biển") is not None
