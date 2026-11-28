"""Optional structured drawing sources for Teacher Sketch Deck steps.

This adapter reuses approved catalog guides and FEAT-097 recipes. It stores only bounded numeric
shape data in the existing step layout-hint field; it never serializes SVG markup.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from sketch2life.domain.lesson_occurrences.presentation_svg_shapes import (
    validate_presentation_svg_draft,
)
from sketch2life.domain.lesson_occurrences.sketch_deck import (
    MAX_LAYOUT_HINT_BYTES,
    SketchDeckStep,
    canonical_json,
)
from sketch2life.infrastructure.svg.recipe_guide import find_recipe

_PATH_PIECE = re.compile(r"[MLCQZ]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_MAX_VIEWBOX_COORDINATE = 10_000.0
_DEFAULT_STROKE = "#1f2937"


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("drawing coordinate is invalid")
    result = float(value)
    if not math.isfinite(result) or abs(result) > _MAX_VIEWBOX_COORDINATE:
        raise ValueError("drawing coordinate is out of range")
    rounded = round(result, 3)
    return 0 if rounded == 0 else rounded


def _viewbox(value: object) -> list[int | float]:
    if isinstance(value, str):
        parts = re.split(r"[\s,]+", value.strip())
        if len(parts) != 4:
            raise ValueError("drawing viewbox is invalid")
        values = [_number(float(part)) for part in parts]
    elif isinstance(value, list) and len(value) == 4:
        values = [_number(part) for part in value]
    else:
        raise ValueError("drawing viewbox is invalid")
    if values[2] <= 0 or values[3] <= 0:
        raise ValueError("drawing viewbox is invalid")
    return [int(part) if float(part).is_integer() else part for part in values]


def _polyline(
    points: Sequence[tuple[float, float]], *, stroke_width: object = 2
) -> dict[str, Any] | None:
    if len(points) < 2 or len(points) > 256:
        return None
    try:
        width = _number(stroke_width)
        normalized = [[_number(x), _number(y)] for x, y in points]
    except (TypeError, ValueError):
        return None
    if not 0.25 <= width <= 64:
        return None
    return {
        "kind": "polyline",
        "points": normalized,
        "stroke": _DEFAULT_STROKE,
        "stroke_width": width,
    }


def _finish_path(
    points: list[tuple[float, float]], output: list[dict[str, Any]], width: object
) -> None:
    shape = _polyline(points, stroke_width=width)
    if shape is not None:
        output.append(shape)


def _path_polylines(data: object, *, stroke_width: object) -> list[dict[str, Any]]:
    """Sample the catalog construction subset into numeric polylines."""

    if not isinstance(data, str) or not 1 <= len(data) <= 32_768:
        return []
    tokens = _PATH_PIECE.findall(data)
    if not tokens or "".join(tokens).replace(",", "") != re.sub(r"[\s,]+", "", data):
        return []
    output: list[dict[str, Any]] = []
    points: list[tuple[float, float]] = []
    current = (0.0, 0.0)
    subpath_start = (0.0, 0.0)
    command: str | None = None
    index = 0
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
            if command == "Z":
                if points and current != subpath_start:
                    points.append(subpath_start)
                _finish_path(points, output, stroke_width)
                points = []
                current = subpath_start
                command = None
                continue
            if command not in {"M", "L", "C", "Q"}:
                return []
        if command is None:
            return []
        arity = {"M": 2, "L": 2, "C": 6, "Q": 4}[command]
        values: list[float] = []
        while index < len(tokens) and not tokens[index].isalpha():
            try:
                values.append(float(tokens[index]))
            except ValueError:
                return []
            index += 1
        if not values or len(values) % arity:
            return []
        original_command = command
        for group_index in range(0, len(values), arity):
            group = values[group_index : group_index + arity]
            effective = "L" if original_command == "M" and group_index else original_command
            if effective == "M":
                if points:
                    _finish_path(points, output, stroke_width)
                current = (group[0], group[1])
                subpath_start = current
                points = [current]
            elif effective == "L":
                current = (group[0], group[1])
                if not points:
                    subpath_start = current
                    points = [current]
                else:
                    points.append(current)
            elif effective == "C":
                if not points:
                    return []
                start = current
                control1 = (group[0], group[1])
                control2 = (group[2], group[3])
                end = (group[4], group[5])
                for step in range(1, 13):
                    t = step / 12
                    u = 1 - t
                    points.append(
                        (
                            u**3 * start[0]
                            + 3 * u**2 * t * control1[0]
                            + 3 * u * t**2 * control2[0]
                            + t**3 * end[0],
                            u**3 * start[1]
                            + 3 * u**2 * t * control1[1]
                            + 3 * u * t**2 * control2[1]
                            + t**3 * end[1],
                        )
                    )
                current = end
            else:
                if not points:
                    return []
                start = current
                control = (group[0], group[1])
                end = (group[2], group[3])
                for step in range(1, 13):
                    t = step / 12
                    u = 1 - t
                    points.append(
                        (
                            u**2 * start[0] + 2 * u * t * control[0] + t**2 * end[0],
                            u**2 * start[1] + 2 * u * t * control[1] + t**2 * end[1],
                        )
                    )
                current = end
            if len(points) > 256:
                return []
        command = "L" if original_command == "M" else original_command
    if points:
        _finish_path(points, output, stroke_width)
    return output


def _catalog_drawing(item: Mapping[str, Any]) -> dict[str, Any] | None:
    guide = item.get("guide")
    document = item.get("document")
    if not isinstance(guide, Mapping) or not isinstance(document, Mapping):
        return None
    try:
        viewbox = _viewbox(document.get("view_box"))
    except (TypeError, ValueError, OverflowError):
        return None

    stages = guide.get("stages")
    if not isinstance(stages, list) or not stages:
        return None
    by_id: dict[str, Mapping[str, Any]] = {}
    construction_strokes = guide.get("strokes")
    if isinstance(construction_strokes, list):
        for stroke in construction_strokes:
            if isinstance(stroke, Mapping) and isinstance(stroke.get("path_id"), str):
                by_id[stroke["path_id"]] = stroke
    else:
        paths = document.get("paths")
        if not isinstance(paths, list):
            return None
        for path in paths:
            if isinstance(path, Mapping) and isinstance(path.get("path_id"), str):
                by_id[path["path_id"]] = path

    drawing_strokes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for stage in stages:
        if not isinstance(stage, Mapping):
            return None
        order = stage.get("stroke_ids")
        if not isinstance(order, list):
            order = stage.get("animation_order")
        if not isinstance(order, list):
            order = stage.get("new_path_ids")
        if not isinstance(order, list) or not order:
            return None
        for path_id in order:
            if not isinstance(path_id, str) or path_id in seen:
                continue
            path = by_id.get(path_id)
            if path is None:
                return None
            shapes = _path_polylines(path.get("d"), stroke_width=path.get("stroke_width", 2))
            if not shapes:
                return None
            drawing_strokes.extend(shapes)
            seen.add(path_id)
    return _make_drawing(viewbox, drawing_strokes, "catalog") if drawing_strokes else None


def _subject_key(subject: str) -> str:
    decomposed = unicodedata.normalize("NFKD", subject.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    plain = plain.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")[:96]


# The Teacher deck always draws with the 6-10 recipe set; the 3-5 set is not used here.
_DECK_RECIPE_LEVEL = "simple"


def _recipe_drawing(subject: str) -> dict[str, Any] | None:
    try:
        recipe = find_recipe([subject], _DECK_RECIPE_LEVEL)
    except Exception:
        return None
    if recipe is None:
        return None
    strokes: list[dict[str, Any]] = []
    recipe_steps: list[dict[str, Any]] = []
    for step in recipe.steps:
        shapes = [
            shape
            for stroke in step.strokes
            if (shape := _polyline(stroke.samples, stroke_width=1.8)) is not None
        ]
        if shapes:
            strokes.extend(shapes)
            words = getattr(step, "instruction", "")
            recipe_steps.append({"stroke_count": len(shapes), "instruction": words})
    drawing = _make_drawing([0, 0, 100, 100], strokes, "recipe") if strokes else None
    return {**drawing, "recipe_steps": recipe_steps} if drawing else None


def _make_drawing(
    viewbox: object, strokes: Sequence[Mapping[str, Any]], source: str
) -> dict[str, Any] | None:
    try:
        normalized_viewbox = _viewbox(viewbox)
        normalized_strokes = [dict(stroke) for stroke in strokes]
        if not normalized_strokes or source not in {"catalog", "recipe", "ai_draft"}:
            return None
        hashed = {"viewbox": normalized_viewbox, "strokes": normalized_strokes, "source": source}
        return {**hashed, "sha256": hashlib.sha256(canonical_json(hashed)).hexdigest()}
    except (TypeError, ValueError, OverflowError):
        return None


def resolve_local_drawing(
    *, subject: str, target_age_band: str, catalog: Any | None = None
) -> dict[str, Any] | None:
    """Choose an approved exact-key catalog guide, then a deterministic recipe."""

    if catalog is not None:
        try:
            page = catalog.list_parent_guides(topic_key=_subject_key(subject), limit=1)
            items = page.get("items") if isinstance(page, Mapping) else None
            if isinstance(items, list) and items:
                first = items[0]
                if isinstance(first, Mapping):
                    drawing = _catalog_drawing(first)
                    if drawing is not None:
                        return drawing
        except Exception:
            pass
    return _recipe_drawing(subject)


def drawing_from_ai_draft(value: object) -> dict[str, Any] | None:
    """Validate the optional worker result with the existing presentation SVG schema."""

    if not isinstance(value, Mapping):
        return None
    try:
        shapes = validate_presentation_svg_draft(dict(value))
        viewbox = _viewbox(value.get("viewbox"))
    except (TypeError, ValueError, OverflowError):
        return None
    return _make_drawing(viewbox, shapes, "ai_draft")


def split_strokes(
    strokes: Sequence[Mapping[str, Any]], step_count: int
) -> list[list[dict[str, Any]]]:
    """Return exactly N balanced, ordered stroke groups; empty tail groups are allowed."""

    if step_count < 1:
        return []
    quotient, remainder = divmod(len(strokes), step_count)
    groups: list[list[dict[str, Any]]] = []
    offset = 0
    for index in range(step_count):
        size = quotient + (1 if index < remainder else 0)
        groups.append([dict(stroke) for stroke in strokes[offset : offset + size]])
        offset += size
    return groups


def _split_recipe_steps(
    strokes: Sequence[Mapping[str, Any]], recipe_steps: Sequence[Mapping[str, Any]], step_count: int
) -> list[tuple[list[dict[str, Any]], str]]:
    """N ordered groups of WHOLE recipe steps, each with the words that describe its strokes."""

    quotient, remainder = divmod(len(recipe_steps), step_count)
    groups: list[tuple[list[dict[str, Any]], str]] = []
    step_offset = stroke_offset = 0
    for index in range(step_count):
        size = quotient + (1 if index < remainder else 0)
        members = recipe_steps[step_offset : step_offset + size]
        step_offset += len(members)
        size = sum(int(member["stroke_count"]) for member in members)
        sentences = [str(member["instruction"]).strip() for member in members]
        caption = " ".join(
            text if text.endswith((".", "!", "?", "…")) else f"{text}."
            for text in sentences
            if text
        )
        taken = strokes[stroke_offset : stroke_offset + size]
        groups.append(([dict(stroke) for stroke in taken], caption))
        stroke_offset += size
    return groups


def _layout_hint_fits(value: Mapping[str, Any]) -> bool:
    try:
        canonical_size = len(canonical_json(dict(value)))
        spaced_size = len(
            json.dumps(dict(value), ensure_ascii=False, sort_keys=True).encode("utf-8")
        )
    except (TypeError, ValueError, UnicodeError):
        return False
    return canonical_size <= MAX_LAYOUT_HINT_BYTES and spaced_size <= MAX_LAYOUT_HINT_BYTES


def attach_progressive_drawing(
    steps: Sequence[SketchDeckStep], drawing: Mapping[str, Any] | None
) -> tuple[SketchDeckStep, ...]:
    """Add one non-cumulative stroke group per step, or preserve the text-only steps."""

    if not isinstance(drawing, Mapping):
        return tuple(steps)
    viewbox, strokes, source, digest = (
        drawing.get("viewbox"),
        drawing.get("strokes"),
        drawing.get("source"),
        drawing.get("sha256"),
    )
    if (
        not isinstance(viewbox, list)
        or not isinstance(strokes, list)
        or not strokes
        or source not in {"catalog", "recipe", "ai_draft"}
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
    ):
        return tuple(steps)
    groups: dict[tuple[str | None, str], list[SketchDeckStep]] = {}
    for step in steps:
        groups.setdefault((step.plan_activity_id, step.instruction_group_key), []).append(step)
    replacements: dict[tuple[str | None, str, int], SketchDeckStep] = {}
    for (activity_id, group_key), members in groups.items():
        ordered = sorted(members, key=lambda step: step.step_index)
        recipe_steps = drawing.get("recipe_steps")
        if source == "recipe" and isinstance(recipe_steps, list) and recipe_steps:
            stroke_groups = _split_recipe_steps(strokes, recipe_steps, len(ordered))
        else:
            stroke_groups = [(group, "") for group in split_strokes(strokes, len(ordered))]
        for step, (step_strokes, caption) in zip(ordered, stroke_groups, strict=True):
            drawing_hint = {
                "viewbox": list(viewbox),
                "strokes": step_strokes,
                "source": source,
                "sha256": digest,
                **({"caption": caption} if caption else {}),
            }
            hints = {**dict(step.bounded_layout_hints), "drawing": drawing_hint}
            if not _layout_hint_fits(hints):
                return tuple(steps)
            replacements[(activity_id, group_key, step.step_index)] = replace(
                step, bounded_layout_hints=hints
            )
    return tuple(
        replacements.get(
            (step.plan_activity_id, step.instruction_group_key, step.step_index), step
        )
        for step in steps
    )


__all__ = [
    "attach_progressive_drawing",
    "drawing_from_ai_draft",
    "resolve_local_drawing",
    "split_strokes",
]
