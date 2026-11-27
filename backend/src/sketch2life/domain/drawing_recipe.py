"""Drawing recipes a child can follow (FEAT-097).

A recipe is data: a few steps, each a few named shapes on a 0 to 100 grid. This module turns it
into drawable paths and checks that a child of the recipe's level can follow it. Nothing here knows
files, HTTP or a model.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

SCHEMA_VERSION: Final = "sketch2life.drawing-recipe.v1"
VIEW_BOX: Final = "0 0 100 100"
STROKE_COLOUR: Final = "#17243e"
STROKE_WIDTH: Final = 1.8
MAX_INSTRUCTION_WORDS: Final = 12
FRAME_MIN: Final = 4.0
FRAME_MAX: Final = 96.0
TOUCH_DISTANCE: Final = 4.0  # a new stroke this close to the drawing does not float
_FORBIDDEN_WORDS: Final = ("svg", "path", "stroke", "người lớn")
_ANGLES: Final = {"right": 0.0, "bottom": 90.0, "left": 180.0, "top": 270.0}


@dataclass(frozen=True, slots=True)
class LevelRules:
    min_steps: int
    max_steps: int
    max_strokes_per_step: int
    max_strokes: int
    min_size: float
    shapes: frozenset[str]


# Rectangles were added in phase 2: vehicles need them, and a square is copied earlier than a
# triangle.
_SIMPLE_SHAPES: Final = frozenset({"circle", "oval", "arc", "line", "dot", "triangle", "rect"})
LEVELS: Final = {
    "beginner": LevelRules(4, 6, 2, 12, 8.0, _SIMPLE_SHAPES),  # about 3 to 5 years
    "simple": LevelRules(
        5, 8, 3, 20, 5.0, _SIMPLE_SHAPES | {"curve", "polyline"}
    ),  # about 6 to 10 years
}


class DrawingRecipeError(ValueError):
    def __init__(self, code: str, *, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class Stroke:
    shape: str
    d: str
    samples: tuple[Point, ...]


@dataclass(frozen=True, slots=True)
class Step:
    part: str
    instruction: str
    strokes: tuple[Stroke, ...]


@dataclass(frozen=True, slots=True)
class Recipe:
    subject_id: str
    level: str
    title: str
    aliases: tuple[str, ...]
    steps: tuple[Step, ...]


def _fail(detail: str) -> DrawingRecipeError:
    return DrawingRecipeError("RECIPE_INVALID", detail=detail)


def _text(value: Any, detail: str, *, maximum: int = 120) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise _fail(detail)
    return unicodedata.normalize("NFC", " ".join(value.split()))


def _number(value: Any, detail: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise _fail(detail)
    return float(value)


def _point(value: Any, detail: str) -> Point:
    if not isinstance(value, Sequence) or isinstance(value, str) or len(value) != 2:
        raise _fail(detail)
    return _number(value[0], detail), _number(value[1], detail)


def _points(value: Any, detail: str) -> list[Point]:
    if not isinstance(value, Sequence) or isinstance(value, str) or len(value) > 25:
        raise _fail(detail)
    return [_point(item, detail) for item in value]


def _keys(raw: Mapping[str, Any], required: set[str], optional: set[str], detail: str) -> None:
    if not required <= set(raw) or set(raw) - required - optional:
        raise _fail(detail)


# ------------------------------------------------------------------ geometry
def _format(value: float) -> str:
    rounded = round(value, 2)
    return "0" if rounded == 0 else f"{rounded:.2f}".rstrip("0").rstrip(".")


def _pair(point: Point) -> str:
    return f"{_format(point[0])} {_format(point[1])}"


def _cubic(p0: Point, c1: Point, c2: Point, p1: Point, count: int = 24) -> list[Point]:
    samples = []
    for index in range(1, count + 1):
        t = index / count
        u = 1 - t
        samples.append(
            (
                u**3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * p1[0],
                u**3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * p1[1],
            )
        )
    return samples


def _segments(
    start: Point, curves: Sequence[tuple[Point, Point, Point]]
) -> tuple[str, list[Point]]:
    d, samples, current = [f"M{_pair(start)}"], [start], start
    for c1, c2, end in curves:
        d.append(f"C{_pair(c1)} {_pair(c2)} {_pair(end)}")
        samples += _cubic(current, c1, c2, end)
        current = end
    return " ".join(d), samples


def _straight(points: Sequence[Point]) -> tuple[str, list[Point]]:
    d, samples = [f"M{_pair(points[0])}"], [points[0]]
    for previous, end in zip(points, points[1:], strict=False):
        d.append(f"L{_pair(end)}")
        samples += [
            (
                previous[0] + (end[0] - previous[0]) * i / 12,
                previous[1] + (end[1] - previous[1]) * i / 12,
            )
            for i in range(1, 13)
        ]
    return " ".join(d), samples


def _elliptic(
    center: Point, rx: float, ry: float, start_deg: float, sweep_deg: float
) -> tuple[str, list[Point]]:
    """An arc of an ellipse as cubic curves.

    Angles grow clockwise on screen: 0 is right, 90 is down.
    """

    pieces = max(1, math.ceil(abs(sweep_deg) / 90 - 1e-9))
    step = math.radians(sweep_deg / pieces)
    k = 4 / 3 * math.tan(step / 4)

    def at(angle: float) -> Point:
        return center[0] + rx * math.cos(angle), center[1] + ry * math.sin(angle)

    def slope(angle: float) -> Point:
        return -rx * math.sin(angle), ry * math.cos(angle)

    angle = math.radians(start_deg)
    start, curves = at(angle), []
    for _ in range(pieces):
        following = angle + step
        p0, p1, d0, d1 = at(angle), at(following), slope(angle), slope(following)
        curves.append(
            ((p0[0] + k * d0[0], p0[1] + k * d0[1]), (p1[0] - k * d1[0], p1[1] - k * d1[1]), p1)
        )
        angle = following
    return _segments(start, curves)


def _round_shape(raw: Mapping[str, Any], rx: float, ry: float) -> tuple[str, list[Point]]:
    start = raw.get("start", "top")
    clockwise = raw.get("clockwise", True)
    if start not in _ANGLES or not isinstance(clockwise, bool) or rx <= 0 or ry <= 0:
        raise _fail("round shape")
    return _elliptic(
        _point(raw["center"], "center"), rx, ry, _ANGLES[start], 360.0 if clockwise else -360.0
    )


def _stroke(raw: Any) -> Stroke:
    if not isinstance(raw, Mapping) or not isinstance(raw.get("shape"), str):
        raise _fail("stroke")
    shape = raw["shape"]
    if shape == "circle":
        _keys(raw, {"shape", "center", "radius"}, {"start", "clockwise"}, shape)
        radius = _number(raw["radius"], shape)
        d, samples = _round_shape(raw, radius, radius)
    elif shape == "oval":
        _keys(raw, {"shape", "center", "rx", "ry"}, {"start", "clockwise"}, shape)
        d, samples = _round_shape(raw, _number(raw["rx"], shape), _number(raw["ry"], shape))
    elif shape == "dot":
        _keys(raw, {"shape", "center"}, {"radius"}, shape)
        radius = _number(raw.get("radius", 1.4), shape)
        if not 0.5 <= radius <= 3:
            raise _fail(shape)
        d, samples = _elliptic(_point(raw["center"], shape), radius, radius, 270.0, 360.0)
    elif shape == "arc":
        _keys(raw, {"shape", "center", "radius", "from_deg", "to_deg"}, {"radius_y"}, shape)
        radius = _number(raw["radius"], shape)
        radius_y = _number(raw.get("radius_y", radius), shape)
        begin, end = _number(raw["from_deg"], shape), _number(raw["to_deg"], shape)
        if radius <= 0 or radius_y <= 0 or not 0 < abs(end - begin) <= 360:
            raise _fail(shape)
        d, samples = _elliptic(_point(raw["center"], shape), radius, radius_y, begin, end - begin)
    elif shape == "rect":
        _keys(raw, {"shape", "corner", "width", "height"}, set(), shape)
        left, top = _point(raw["corner"], shape)
        width, height = _number(raw["width"], shape), _number(raw["height"], shape)
        if width <= 0 or height <= 0:
            raise _fail(shape)
        right, bottom = left + width, top + height
        d, samples = _straight(
            [(left, top), (right, top), (right, bottom), (left, bottom), (left, top)]
        )
    elif shape == "line":
        _keys(raw, {"shape", "from", "to"}, set(), shape)
        begin_point, end_point = _point(raw["from"], shape), _point(raw["to"], shape)
        if begin_point == end_point:
            raise _fail(shape)
        d, samples = _straight([begin_point, end_point])
    elif shape in {"triangle", "polyline"}:
        _keys(raw, {"shape", "points"}, set(), shape)
        corners = _points(raw["points"], shape)
        if (len(corners) != 3) if shape == "triangle" else (len(corners) < 3):
            raise _fail(shape)
        d, samples = _straight([*corners, corners[0]] if shape == "triangle" else corners)
    elif shape == "curve":
        _keys(raw, {"shape", "points"}, set(), shape)
        points = _points(raw["points"], shape)
        if len(points) < 4 or (len(points) - 1) % 3:
            raise _fail(shape)
        d, samples = _segments(
            points[0], [tuple(points[i : i + 3]) for i in range(1, len(points), 3)]
        )
    else:
        raise _fail("unknown shape")
    return Stroke(shape, d, tuple(samples))


def parse_recipe(raw: Mapping[str, Any]) -> Recipe:
    _keys(
        raw,
        {"schema_version", "subject_id", "level", "title_vi", "aliases", "steps"},
        set(),
        "recipe",
    )
    subject_id = raw["subject_id"]
    aliases, steps = raw["aliases"], raw["steps"]
    if (
        raw["schema_version"] != SCHEMA_VERSION
        or raw["level"] not in LEVELS
        or not isinstance(subject_id, str)
        or re.fullmatch(r"[a-z][a-z0-9_]{0,40}", subject_id) is None
        or not isinstance(aliases, list)
        or not aliases
        or not isinstance(steps, list)
        or not 1 <= len(steps) <= 8
    ):
        raise _fail("recipe fields")
    parsed = []
    for step in steps:
        if not isinstance(step, Mapping):
            raise _fail("step")
        _keys(step, {"part", "instruction_vi", "strokes"}, set(), "step")
        strokes = step["strokes"]
        if not isinstance(strokes, list) or not 1 <= len(strokes) <= 8:
            raise _fail("strokes")
        parsed.append(
            Step(
                _text(step["part"], "part", maximum=40),
                _text(step["instruction_vi"], "instruction"),
                tuple(_stroke(item) for item in strokes),
            )
        )
    return Recipe(
        subject_id,
        raw["level"],
        _text(raw["title_vi"], "title"),
        tuple(_text(item, "alias", maximum=60) for item in aliases),
        tuple(parsed),
    )


# ------------------------------------------------------------------ checks
def _folded(value: str) -> str:
    plain = unicodedata.normalize("NFD", value.casefold())
    plain = "".join(char for char in plain if not unicodedata.combining(char)).replace("đ", "d")
    return " ".join(re.findall(r"[a-z0-9]+", plain))


def _box(stroke: Stroke) -> tuple[float, float, float, float]:
    xs, ys = [x for x, _ in stroke.samples], [y for _, y in stroke.samples]
    return min(xs), min(ys), max(xs), max(ys)


def _area(stroke: Stroke) -> float:
    left, top, right, bottom = _box(stroke)
    return (right - left) * (bottom - top)


def _within(stroke: Stroke, box: tuple[float, float, float, float]) -> bool:
    left, top, right, bottom = box
    return all(left <= x <= right and top <= y <= bottom for x, y in stroke.samples)


def _connected(stroke: Stroke, earlier: Sequence[Stroke]) -> bool:
    """Touching the drawing, or an inner detail such as an eye inside a part already drawn."""

    if any(
        math.dist(point, other) <= TOUCH_DISTANCE
        for before in earlier
        for point in stroke.samples
        for other in before.samples
    ):
        return True
    return any(_within(stroke, _box(before)) for before in earlier)


def check_recipe(recipe: Recipe) -> list[str]:
    """The codes of every broken rule, in a stable order and without repeats."""

    rules = LEVELS[recipe.level]
    strokes = [stroke for step in recipe.steps for stroke in step.strokes]
    found: dict[str, None] = {}

    def report(broken: bool, code: str) -> None:
        if broken:
            found[code] = None

    report(not rules.min_steps <= len(recipe.steps) <= rules.max_steps, "RECIPE_STEP_COUNT")
    report(len(strokes) > rules.max_strokes, "RECIPE_TOO_MANY_STROKES")
    for step in recipe.steps:
        report(len(step.strokes) > rules.max_strokes_per_step, "RECIPE_TOO_MANY_STROKES_IN_STEP")
        report(
            _folded(step.part) not in _folded(step.instruction), "RECIPE_INSTRUCTION_MISSES_PART"
        )
        report(len(step.instruction.split()) > MAX_INSTRUCTION_WORDS, "RECIPE_INSTRUCTION_TOO_LONG")
        report(
            any(word in step.instruction.casefold() for word in _FORBIDDEN_WORDS),
            "RECIPE_FORBIDDEN_WORD",
        )
    for index, stroke in enumerate(strokes):
        left, top, right, bottom = _box(stroke)
        report(stroke.shape not in rules.shapes, "RECIPE_SHAPE_NOT_FOR_LEVEL")
        report(min(left, top) < FRAME_MIN or max(right, bottom) > FRAME_MAX, "RECIPE_OUT_OF_FRAME")
        report(
            stroke.shape != "dot" and max(right - left, bottom - top) < rules.min_size,
            "RECIPE_SHAPE_TOO_SMALL",
        )
        report(index > 0 and not _connected(stroke, strokes[:index]), "RECIPE_STROKE_FLOATS")
    report(len({stroke.d for stroke in strokes}) != len(strokes), "RECIPE_DUPLICATE_STROKE")
    first = max(_area(stroke) for stroke in recipe.steps[0].strokes)
    report(any(_area(stroke) > first + 0.01 for stroke in strokes), "RECIPE_BIGGEST_PART_NOT_FIRST")
    return list(found)


# ------------------------------------------------------------------ output
def compile_recipe(recipe: Recipe) -> dict[str, Any]:
    """Paths, parts and stages shaped like the stored stroke guide (``SvgTopicStrokeGuideV1``)."""

    paths, parts, stages = [], [], []
    for number, step in enumerate(recipe.steps, start=1):
        part_id = f"step_{number:02d}"
        ids = [f"{part_id}-{position}" for position in range(1, len(step.strokes) + 1)]
        paths += [
            {
                "path_id": path_id,
                "d": stroke.d,
                "fill": "none",
                "stroke": STROKE_COLOUR,
                "stroke_width": STROKE_WIDTH,
            }
            for path_id, stroke in zip(ids, step.strokes, strict=True)
        ]
        parts.append(
            {
                "part_id": part_id,
                "label_vi": step.part[0].upper() + step.part[1:],
                "path_ids": ids,
                "depends_on": [f"step_{number - 1:02d}"] if number > 1 else [],
            }
        )
        stages.append(
            {
                "step_index": number,
                "instruction_vi": step.instruction,
                "part_ids": [part_id],
                "new_path_ids": ids,
                "animation_order": list(ids),
            }
        )
    return {
        "view_box": VIEW_BOX,
        "title_vi": recipe.title,
        "paths": paths,
        "parts": parts,
        "stages": stages,
    }


__all__ = [
    "LEVELS",
    "SCHEMA_VERSION",
    "DrawingRecipeError",
    "Recipe",
    "check_recipe",
    "compile_recipe",
    "parse_recipe",
]
