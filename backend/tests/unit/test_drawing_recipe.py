"""FEAT-097: a drawing recipe becomes a guide a child can follow, and broken recipes are refused."""

from __future__ import annotations

import copy
import re
from typing import Any

import pytest

from sketch2life.domain.drawing_recipe import (
    DrawingRecipeError,
    check_recipe,
    compile_recipe,
    parse_recipe,
)


def _circle(x: float, y: float, r: float, **extra: Any) -> dict[str, Any]:
    return {"shape": "circle", "center": [x, y], "radius": r, **extra}


def _line(a: list[float], b: list[float]) -> dict[str, Any]:
    return {"shape": "line", "from": a, "to": b}


def _step(part: str, text: str, *strokes: dict[str, Any]) -> dict[str, Any]:
    return {"part": part, "instruction_vi": text, "strokes": list(strokes)}


def _recipe(**changes: Any) -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.drawing-recipe.v1",
        "subject_id": "chicken",
        "level": "beginner",
        "title_vi": "Vẽ con gà",
        "aliases": ["gà", "con gà"],
        "steps": [
            _step("thân", "Vẽ một hình tròn to làm thân.", _circle(45, 62, 22)),
            _step("đầu", "Vẽ hình tròn nhỏ làm đầu.", _circle(68, 32, 13)),
            _step(
                "mỏ",
                "Vẽ tam giác nhỏ làm mỏ.",
                {"shape": "triangle", "points": [[80, 28], [92, 33], [80, 38]]},
            ),
            _step("mắt", "Chấm một chấm làm mắt.", {"shape": "dot", "center": [71, 29]}),
            _step(
                "chân",
                "Vẽ hai đường thẳng làm chân.",
                _line([38, 83], [38, 94]),
                _line([54, 83], [54, 94]),
            ),
        ],
        **changes,
    }


def _codes(raw: dict[str, Any]) -> list[str]:
    return check_recipe(parse_recipe(raw))


def test_a_good_recipe_passes_every_check() -> None:
    assert _codes(_recipe()) == []


def test_each_step_becomes_paths_in_the_order_they_are_drawn() -> None:
    guide = compile_recipe(parse_recipe(_recipe()))

    assert guide["view_box"] == "0 0 100 100"
    assert [step["instruction_vi"] for step in guide["stages"]][:2] == [
        "Vẽ một hình tròn to làm thân.",
        "Vẽ hình tròn nhỏ làm đầu.",
    ]
    assert [len(step["new_path_ids"]) for step in guide["stages"]] == [1, 1, 1, 1, 2]
    ids = [path["path_id"] for path in guide["paths"]]
    assert ids == [path_id for step in guide["stages"] for path_id in step["new_path_ids"]]
    for path in guide["paths"]:
        assert path["fill"] == "none" and re.fullmatch(r"[MLCZ0-9. \-]+", path["d"]), path["d"]


def test_a_circle_starts_at_the_top_and_goes_clockwise_by_default() -> None:
    first = compile_recipe(parse_recipe(_recipe()))["paths"][0]["d"]

    assert first.startswith("M45 40 C") and first.endswith("45 40")
    # The first curve of a clockwise circle that starts at the top ends at the right-most point.
    assert "67 62" in first.split("C")[1]


@pytest.mark.parametrize(
    "start, point", [("left", "M23 62"), ("bottom", "M45 84"), ("right", "M67 62")]
)
def test_a_shape_can_start_elsewhere(start: str, point: str) -> None:
    raw = _recipe()
    raw["steps"][0]["strokes"][0]["start"] = start

    assert compile_recipe(parse_recipe(raw))["paths"][0]["d"].startswith(point)


@pytest.mark.parametrize(
    "stroke",
    [
        {"shape": "star", "center": [50, 50], "radius": 10},
        {"shape": "circle", "center": [50, 50], "radius": -1},
        {"shape": "circle", "center": [50], "radius": 10},
        {"shape": "line", "from": [1, 2], "to": [1, 2]},
        {"shape": "triangle", "points": [[1, 2], [3, 4]]},
        {"shape": "curve", "points": [[1, 2], [3, 4], [5, 6]]},
        {"shape": "circle", "center": [50, 50], "radius": 10, "extra": 1},
        {"shape": "circle", "center": [50, float("nan")], "radius": 10},
    ],
)
def test_a_malformed_stroke_is_refused(stroke: dict[str, Any]) -> None:
    raw = _recipe()
    raw["steps"][0]["strokes"] = [stroke]

    with pytest.raises(DrawingRecipeError):
        parse_recipe(raw)


@pytest.mark.parametrize(
    "broken",
    [
        {"level": "expert"},
        {"schema_version": "other"},
        {"aliases": []},
        {"title_vi": " "},
        {"steps": []},
    ],
)
def test_a_malformed_recipe_is_refused(broken: dict[str, Any]) -> None:
    with pytest.raises(DrawingRecipeError):
        parse_recipe(_recipe(**broken))


def _changed(change: Any, level: str = "beginner") -> list[str]:
    raw = copy.deepcopy(_recipe(level=level))
    change(raw["steps"])
    return _codes(raw)


@pytest.mark.parametrize(
    "change, code",
    [
        (lambda steps: steps.__delitem__(slice(3, None)), "RECIPE_STEP_COUNT"),
        (
            lambda steps: steps[4]["strokes"].append(_line([46, 83], [46, 94])),
            "RECIPE_TOO_MANY_STROKES_IN_STEP",
        ),
        (
            lambda steps: steps[3]["strokes"].__setitem__(0, {"shape": "dot", "center": [99, 29]}),
            "RECIPE_OUT_OF_FRAME",
        ),
        (
            lambda steps: steps[4]["strokes"].__setitem__(0, _line([5, 5], [5, 20])),
            "RECIPE_STROKE_FLOATS",
        ),
        (
            lambda steps: steps[2]["strokes"].__setitem__(
                0, {"shape": "triangle", "points": [[80, 32], [83, 33], [80, 35]]}
            ),
            "RECIPE_SHAPE_TOO_SMALL",
        ),
        (
            lambda steps: steps[4]["strokes"].__setitem__(1, _line([38, 83], [38, 94])),
            "RECIPE_DUPLICATE_STROKE",
        ),
        (lambda steps: steps.insert(0, steps.pop(1)), "RECIPE_BIGGEST_PART_NOT_FIRST"),
        (
            lambda steps: steps[1].__setitem__("instruction_vi", "Vẽ hình tròn nhỏ."),
            "RECIPE_INSTRUCTION_MISSES_PART",
        ),
        (
            lambda steps: steps[1].__setitem__("instruction_vi", "Vẽ đầu " + "thật tròn " * 8),
            "RECIPE_INSTRUCTION_TOO_LONG",
        ),
    ],
)
def test_each_rule_reports_its_code(change: Any, code: str) -> None:
    assert code in _changed(change)


def test_the_younger_level_refuses_free_curves_and_the_older_level_allows_them() -> None:
    def add_curve(steps: list[dict[str, Any]]) -> None:
        steps[3]["strokes"].append(
            {"shape": "curve", "points": [[30, 60], [40, 75], [55, 75], [62, 60]]}
        )

    assert "RECIPE_SHAPE_NOT_FOR_LEVEL" in _changed(add_curve)
    assert "RECIPE_SHAPE_NOT_FOR_LEVEL" not in _changed(add_curve, level="simple")


def test_the_total_number_of_strokes_is_limited_by_level() -> None:
    def many(steps: list[dict[str, Any]]) -> None:
        for index, step in enumerate(steps):
            step["strokes"] = [
                _line([20 + index, 60], [20 + index, 40 - extra]) for extra in range(3)
            ]

    assert "RECIPE_TOO_MANY_STROKES" in _changed(many)


def test_a_rectangle_is_drawn_from_its_top_left_corner_clockwise() -> None:
    raw = _recipe()
    raw["steps"][0]["strokes"] = [{"shape": "rect", "corner": [22, 40], "width": 44, "height": 44}]

    recipe = parse_recipe(raw)

    assert compile_recipe(recipe)["paths"][0]["d"] == "M22 40 L66 40 L66 84 L22 84 L22 40"
    assert "RECIPE_SHAPE_NOT_FOR_LEVEL" not in check_recipe(recipe)


@pytest.mark.parametrize("size", [{"width": 0, "height": 10}, {"width": 10, "height": -1}])
def test_a_rectangle_needs_a_size(size: dict[str, Any]) -> None:
    raw = _recipe()
    raw["steps"][0]["strokes"] = [{"shape": "rect", "corner": [20, 20], **size}]

    with pytest.raises(DrawingRecipeError):
        parse_recipe(raw)
