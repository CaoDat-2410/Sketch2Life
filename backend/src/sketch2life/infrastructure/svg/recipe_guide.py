"""Parent drawing guides from the project's own shape recipes (FEAT-097).

One JSON recipe per subject and level lives in ``resources/drawing_recipes``. A recipe that breaks
a rule of its level is never served. No model, network or third-party picture is involved.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

from sketch2life.contracts.schemas.svg_engine import (
    SvgReferenceIllustrationDocumentV1,
    SvgReferenceSourceProvenanceV1,
    SvgTopicStrokeGuideModelResultV1,
)
from sketch2life.domain.drawing_recipe import (
    DrawingRecipeError,
    Recipe,
    check_recipe,
    compile_recipe,
    parse_recipe,
)

RECIPE_DIRECTORY: Final = Path(__file__).resolve().parents[2] / "resources" / "drawing_recipes"
ENGINE_ID: Final = "sketch2life-shape-recipe"
ENGINE_REVISION: Final = "1.0.0"
METHOD: Final = "AUTHORED_SHAPE_RECIPE_V1"
_REPOSITORY_URL: Final = "https://github.com/CaoDat-2410/Sketch2Life"
_FILLERS: Final = frozenset({"con", "chú", "bạn", "chiếc", "cái"})
# Names that hold the name of a recipe but mean something else: they get no picture.
_OTHER_THINGS: Final = (
    "xe máy xúc",
    "máy bay trực thăng",
    "con sáo",
    "tiên cá",
    "bóng bay",
    "bóng đèn",
    "diều hâu",
    "cầu thang",
    "cầu trượt",
    "cầu lông",
    "bàn chải",
    "bàn tay",
    "bàn chân",
    "bàn là",
    "đèn lồng",
    "đèn pin",
    "đèn ông sao",
    "áo dài",
)


@dataclass(frozen=True, slots=True)
class RecipeGuide:
    generated: SvgTopicStrokeGuideModelResultV1
    reference_source: SvgReferenceSourceProvenanceV1
    reference_illustration: SvgReferenceIllustrationDocumentV1
    engine_id: str
    engine_revision: str
    source_guide_uri: str | None
    source_guide_sha256: str
    derivation_method: str
    source_path_count: int
    path_lineage: tuple[dict[str, Any], ...]


@lru_cache(maxsize=1)
def _library() -> tuple[tuple[Recipe, str], ...]:
    """Every servable recipe with the hash of its file."""

    found = []
    for path in sorted(RECIPE_DIRECTORY.glob("*.json")):
        payload = path.read_bytes()
        recipe = parse_recipe(json.loads(payload.decode("utf-8")))
        broken = check_recipe(recipe)
        if broken:
            raise DrawingRecipeError(broken[0], detail=path.name)
        found.append((recipe, hashlib.sha256(payload.replace(b"\r\n", b"\n")).hexdigest()))
    return tuple(found)


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


def _plain(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", " ".join(_words(text)))
    return "".join(c for c in decomposed if not unicodedata.combining(c)).replace("đ", "d")


def _core(words: list[str]) -> list[str]:
    return words[1:] if len(words) > 1 and words[0] in _FILLERS else words


def _end_of(name: list[str], words: list[str]) -> int:
    """Where ``name`` ends in ``words`` (its last occurrence), or 0 when it is not there."""

    size = len(name)
    ends = [i + size for i in range(len(words) - size + 1) if words[i : i + size] == name]
    return ends[-1] if ends else 0


def _named_in(words: list[str], recipes: Sequence[Recipe]) -> Recipe | None:
    """The recipe a sentence is about, from the names of two words or more that it holds.

    Where two names share words, the one with more words is meant; of two as long, the one that
    ends later, since the later words say what the thing is ("cái cây cầu" is a bridge, not a tree).
    Of names that are apart, the first is the subject ("bông hoa trong chậu cây" is a flower).
    """

    found = [
        (len(name), end, recipe)
        for recipe in recipes
        for name in map(_words, recipe.aliases)
        if len(name) > 1 and (end := _end_of(name, words))
    ]
    kept: list[tuple[int, int, Recipe]] = []
    for size, end, recipe in sorted(found, key=lambda item: item[:2], reverse=True):
        if all(end <= other_end - other or end - size >= other_end for other, other_end, _ in kept):
            kept.append((size, end, recipe))
    return min(kept, key=lambda item: item[1] - item[0])[2] if kept else None


def _match(text: str, recipes: Sequence[Recipe]) -> Recipe | None:
    words = _words(text)
    if not words or any(_end_of(_words(other), words) for other in _OTHER_THINGS):
        return None
    # 1. The text is a name of the subject, with or without a word such as "con".
    for recipe in recipes:
        if any(_core(words) == _core(_words(alias)) for alias in recipe.aliases):
            return recipe
    # 2. A longer sentence holds a name of two words or more. Single words are not searched: they
    # hide in other words.
    named = _named_in(words, recipes)
    if named is not None:
        return named
    # 3. Typed without accents: accepted only when the whole text is one subject's name.
    if _plain(text) == " ".join(words):
        plain = {
            r.subject_id: r
            for r in recipes
            if any(_plain(alias) == _plain(text) for alias in r.aliases)
        }
        if len(plain) == 1:
            return next(iter(plain.values()))
    return None


def find_recipe(texts: Sequence[str], level: str) -> Recipe | None:
    """The recipe of ``level`` named by the first text that names one."""

    recipes = [recipe for recipe, _digest in _library() if recipe.level == level]
    for text in texts:
        found = _match(text, recipes)
        if found is not None:
            return found
    return None


def build_recipe_guide(texts: Sequence[str], level: str) -> RecipeGuide | None:
    recipe = find_recipe(texts, level)
    if recipe is None:
        return None
    digest = next(digest for stored, digest in _library() if stored is recipe)
    compiled = compile_recipe(recipe)
    generated = SvgTopicStrokeGuideModelResultV1.model_validate(
        {
            "schema_version": "SvgTopicStrokeGuideContentV1",
            "title_vi": compiled["title_vi"],
            "document": {
                "schema_version": "SvgDocumentV1",
                "view_box": compiled["view_box"],
                "paths": compiled["paths"],
            },
            "parts": compiled["parts"],
            "stages": compiled["stages"],
        }
    )
    asset_id = f"recipe-{recipe.subject_id}-{recipe.level}"
    illustration = SvgReferenceIllustrationDocumentV1.model_validate(
        {"view_box": compiled["view_box"], "paths": [dict(path) for path in compiled["paths"]]}
    )
    labels = {
        path_id: part["label_vi"] for part in compiled["parts"] for path_id in part["path_ids"]
    }
    return RecipeGuide(
        generated=generated,
        reference_source=SvgReferenceSourceProvenanceV1(
            asset_id=asset_id,
            dataset_name="Sketch2Life drawing recipes",
            dataset_revision=ENGINE_REVISION,
            dataset_uri=None,
            source_sha256=digest,
            license_id="PROJECT-OWNED",
            license_uri=_REPOSITORY_URL,
        ),
        reference_illustration=illustration,
        engine_id=ENGINE_ID,
        engine_revision=ENGINE_REVISION,
        source_guide_uri=None,
        source_guide_sha256=digest,
        derivation_method=METHOD,
        source_path_count=len(compiled["paths"]),
        path_lineage=tuple(
            {
                "derived_path_id": path["path_id"],
                "source_path_ids": [path["path_id"]],
                "feature_vi": labels[path["path_id"]],
                "operation": METHOD,
            }
            for path in compiled["paths"]
        ),
    )


__all__ = [
    "ENGINE_ID",
    "METHOD",
    "RECIPE_DIRECTORY",
    "RecipeGuide",
    "build_recipe_guide",
    "find_recipe",
]
