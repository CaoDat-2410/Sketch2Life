"""Bounded structured geometry for Teacher-reviewed presentation SVG drafts."""

from __future__ import annotations

import math
from typing import Any

PRESENTATION_SVG_DRAFT_SCHEMA = "sketch2life.presentation-svg-draft.v1"
PRESENTATION_SVG_STROKES = frozenset({"#1f2937", "#2563eb", "#16a34a", "#dc2626", "#d97706"})
_SHAPE_FIELDS = {
    "circle": {"kind", "cx", "cy", "r", "stroke", "stroke_width"},
    "rect": {"kind", "x", "y", "w", "h", "stroke", "stroke_width"},
    "line": {"kind", "x1", "y1", "x2", "y2", "stroke", "stroke_width"},
    "polyline": {"kind", "points", "stroke", "stroke_width"},
    "ellipse": {"kind", "cx", "cy", "rx", "ry", "stroke", "stroke_width"},
}


def validate_presentation_svg_draft(value: object) -> list[dict[str, Any]]:
    """Validate the exact provider result contract and return its shapes."""

    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "review_required",
        "viewbox",
        "shapes",
    }:
        raise ValueError("presentation SVG draft contract is invalid")
    if (
        value["schema_version"] != PRESENTATION_SVG_DRAFT_SCHEMA
        or value["review_required"] is not True
    ):
        raise ValueError("presentation SVG draft contract is invalid")
    viewbox = value["viewbox"]
    if (
        not isinstance(viewbox, list)
        or len(viewbox) != 4
        or any(isinstance(part, bool) or not isinstance(part, int) for part in viewbox)
        or viewbox != [0, 0, 100, 100]
    ):
        raise ValueError("presentation SVG draft viewbox is invalid")
    shapes = value["shapes"]
    if not isinstance(shapes, list) or not 4 <= len(shapes) <= 12:
        raise ValueError("presentation SVG draft shape count is invalid")
    checked: list[dict[str, Any]] = []
    for shape in shapes:
        checked.append(_validate_shape(shape))
    return checked


def build_presentation_svg_source(value: object) -> bytes:
    """Serialize validated geometry as a small SVG with no model-controlled markup."""

    shapes = validate_presentation_svg_draft(value)
    elements = [_serialize_shape(shape) for shape in shapes]
    source = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        + "".join(elements)
        + "</svg>"
    )
    return source.encode("ascii")


def _validate_shape(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("presentation SVG shape must be an object")
    kind = value.get("kind")
    fields = _SHAPE_FIELDS.get(kind) if isinstance(kind, str) else None
    if fields is None or set(value) != fields:
        raise ValueError("presentation SVG shape fields are invalid")
    stroke = value["stroke"]
    stroke_width = value["stroke_width"]
    if not isinstance(stroke, str) or stroke not in PRESENTATION_SVG_STROKES:
        raise ValueError("presentation SVG stroke is invalid")
    if (
        isinstance(stroke_width, bool)
        or not isinstance(stroke_width, int)
        or not 1 <= stroke_width <= 6
    ):
        raise ValueError("presentation SVG stroke width is invalid")

    if kind == "circle":
        cx = _number(value["cx"])
        cy = _number(value["cy"])
        radius = _number(value["r"], minimum=1, maximum=50)
        _require_bounds(cx - radius, cy - radius, cx + radius, cy + radius)
    elif kind == "ellipse":
        cx = _number(value["cx"])
        cy = _number(value["cy"])
        rx = _number(value["rx"], minimum=1, maximum=50)
        ry = _number(value["ry"], minimum=1, maximum=50)
        _require_bounds(cx - rx, cy - ry, cx + rx, cy + ry)
    elif kind == "rect":
        x = _number(value["x"])
        y = _number(value["y"])
        width = _number(value["w"])
        height = _number(value["h"])
        if width <= 0 or height <= 0:
            raise ValueError("presentation SVG rectangle size is invalid")
        _require_bounds(x, y, x + width, y + height)
    elif kind == "line":
        x1 = _number(value["x1"])
        y1 = _number(value["y1"])
        x2 = _number(value["x2"])
        y2 = _number(value["y2"])
        if (x1, y1) == (x2, y2):
            raise ValueError("presentation SVG line is degenerate")
    else:
        points = value["points"]
        if not isinstance(points, list) or not 2 <= len(points) <= 16:
            raise ValueError("presentation SVG polyline point count is invalid")
        checked_points: list[list[float]] = []
        for point in points:
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError("presentation SVG polyline point is invalid")
            checked_points.append([_number(point[0]), _number(point[1])])
        if len({tuple(point) for point in checked_points}) < 2:
            raise ValueError("presentation SVG polyline is degenerate")
    return dict(value)


def _number(value: object, *, minimum: float = 0, maximum: float = 100) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("presentation SVG coordinate is invalid")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError("presentation SVG coordinate is invalid") from exc
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError("presentation SVG coordinate is outside the grid")
    return number


def _require_bounds(left: float, top: float, right: float, bottom: float) -> None:
    if left < 0 or top < 0 or right > 100 or bottom > 100:
        raise ValueError("presentation SVG shape exceeds the grid")


def _serialize_shape(shape: dict[str, Any]) -> str:
    kind = shape["kind"]
    stroke = shape["stroke"]
    width = str(shape["stroke_width"])
    style = f' fill="none" stroke="{stroke}" stroke-width="{width}"'
    if kind == "circle":
        return (
            f'<circle cx="{_format_number(shape["cx"])}" '
            f'cy="{_format_number(shape["cy"])}" r="{_format_number(shape["r"])}"'
            f"{style}/>"
        )
    if kind == "ellipse":
        cx, cy = float(shape["cx"]), float(shape["cy"])
        rx, ry = float(shape["rx"]), float(shape["ry"])
        curve = 0.552284749831
        data = (
            f"M {_format_number(cx + rx)} {_format_number(cy)} "
            f"C {_format_number(cx + rx)} {_format_number(cy - curve * ry)} "
            f"{_format_number(cx + curve * rx)} {_format_number(cy - ry)} "
            f"{_format_number(cx)} {_format_number(cy - ry)} "
            f"C {_format_number(cx - curve * rx)} {_format_number(cy - ry)} "
            f"{_format_number(cx - rx)} {_format_number(cy - curve * ry)} "
            f"{_format_number(cx - rx)} {_format_number(cy)} "
            f"C {_format_number(cx - rx)} {_format_number(cy + curve * ry)} "
            f"{_format_number(cx - curve * rx)} {_format_number(cy + ry)} "
            f"{_format_number(cx)} {_format_number(cy + ry)} "
            f"C {_format_number(cx + curve * rx)} {_format_number(cy + ry)} "
            f"{_format_number(cx + rx)} {_format_number(cy + curve * ry)} "
            f"{_format_number(cx + rx)} {_format_number(cy)} Z"
        )
        return f'<path d="{data}"{style}/>'
    if kind == "line":
        data = (
            f"M {_format_number(shape['x1'])} {_format_number(shape['y1'])} "
            f"L {_format_number(shape['x2'])} {_format_number(shape['y2'])}"
        )
        return f'<path d="{data}"{style}/>'
    if kind == "polyline":
        points = shape["points"]
        data = " ".join(
            ("M " if index == 0 else "L ")
            + f"{_format_number(point[0])} {_format_number(point[1])}"
            for index, point in enumerate(points)
        )
        return f'<path d="{data}"{style}/>'
    x = _format_number(shape["x"])
    y = _format_number(shape["y"])
    right = _format_number(float(shape["x"]) + float(shape["w"]))
    bottom = _format_number(float(shape["y"]) + float(shape["h"]))
    return f'<path d="M {x} {y} L {right} {y} L {right} {bottom} L {x} {bottom} Z"{style}/>'


def _format_number(value: int | float) -> str:
    number = float(value)
    if number == 0:
        return "0"
    if number.is_integer():
        return str(int(number))
    return format(number, ".12g")


__all__ = [
    "PRESENTATION_SVG_DRAFT_SCHEMA",
    "PRESENTATION_SVG_STROKES",
    "build_presentation_svg_source",
    "validate_presentation_svg_draft",
]
