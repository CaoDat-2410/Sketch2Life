"""Strict, bounded SVG input parser that emits a provider-neutral path document."""

from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sketch2life.domain.svg_engine import classify_svg_source

MAX_SOURCE_BYTES = 1_000_000
MAX_ELEMENTS = 400
MAX_PATHS = 400
MAX_PATH_CHARS = 8192
MAX_CANONICAL_BYTES = 5_000_000
MAX_COORDINATE = 10_000.0
SANITIZER_VERSION = "svg-sanitizer-v1"
SANITIZER_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_NUMBER_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_PATH_PATTERN = re.compile(r"[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_COLOR_PATTERN = re.compile(r"^(?:none|#[0-9a-fA-F]{6})$")
_POINTS_PATTERN = re.compile(r"^[0-9eE+.,\-\s]+$")
_SVG_NS = "http://www.w3.org/2000/svg"


class SvgInputRejected(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SanitizedSvg:
    document: dict[str, Any]
    source_sha256: str
    canonical_sha256: str
    readiness: dict[str, Any]
    sanitizer_version: str = SANITIZER_VERSION


def sanitize_svg_source(source: bytes) -> SanitizedSvg:
    if not source or len(source) > MAX_SOURCE_BYTES:
        raise SvgInputRejected("SVG_SOURCE_SIZE_INVALID")
    lowered = source.lower()
    if any(marker in lowered for marker in (b"<!doctype", b"<!entity", b"<?xml-stylesheet")):
        raise SvgInputRejected("SVG_XML_DECLARATION_FORBIDDEN")
    try:
        root = ET.fromstring(source)
    except (ET.ParseError, ValueError) as exc:
        raise SvgInputRejected("SVG_XML_INVALID") from exc
    if _local_name(root.tag) != "svg" or _namespace(root.tag) not in {"", _SVG_NS}:
        raise SvgInputRejected("SVG_ROOT_INVALID")

    view_box = _parse_view_box(root.attrib)
    paths: list[dict[str, Any]] = []
    source_elements = 0
    filled_shape_count = 0

    def walk(element: ET.Element) -> None:
        nonlocal source_elements, filled_shape_count
        source_elements += 1
        if source_elements > MAX_ELEMENTS:
            raise SvgInputRejected("SVG_ELEMENT_LIMIT_EXCEEDED")
        name = _local_name(element.tag)
        namespace = _namespace(element.tag)
        if namespace not in {"", _SVG_NS}:
            raise SvgInputRejected("SVG_NAMESPACE_FORBIDDEN")
        if name in {"script", "foreignObject", "image", "use", "animate", "animateTransform", "set"}:
            raise SvgInputRejected("SVG_ACTIVE_CONTENT_FORBIDDEN")
        if name == "g":
            _require_attributes(element, allowed={"id"})
            if not list(element):
                raise SvgInputRejected("SVG_EMPTY_GROUP")
            for child in list(element):
                walk(child)
            if (element.text or "").strip() or any((child.tail or "").strip() for child in element):
                raise SvgInputRejected("SVG_TEXT_CONTENT_FORBIDDEN")
            return
        if name not in {"path", "line", "polyline", "polygon", "rect", "circle", "ellipse"}:
            raise SvgInputRejected("SVG_ELEMENT_UNSUPPORTED")

        allowed = {
            "path": {"id", "d", "fill", "stroke", "stroke-width"},
            "line": {"id", "x1", "y1", "x2", "y2", "fill", "stroke", "stroke-width"},
            "polyline": {"id", "points", "fill", "stroke", "stroke-width"},
            "polygon": {"id", "points", "fill", "stroke", "stroke-width"},
            "rect": {"id", "x", "y", "width", "height", "fill", "stroke", "stroke-width"},
            "circle": {"id", "cx", "cy", "r", "fill", "stroke", "stroke-width"},
            "ellipse": {"id", "cx", "cy", "rx", "ry", "fill", "stroke", "stroke-width"},
        }[name]
        _require_attributes(element, allowed=allowed)
        if list(element) or (element.text or "").strip():
            raise SvgInputRejected("SVG_DRAWABLE_CHILDREN_FORBIDDEN")
        path_data = _shape_to_path(name, element.attrib)
        path_data = _normalize_path_data(path_data)
        path_id = element.attrib.get("id") or f"path-{len(paths) + 1:03d}"
        if not re.fullmatch(r"[A-Za-z0-9._:-]{1,96}", path_id):
            raise SvgInputRejected("SVG_PATH_ID_INVALID")
        fill = _color(element.attrib.get("fill", "none"))
        stroke = _color(element.attrib.get("stroke", "#1f2937"))
        if stroke == "none":
            if fill == "none":
                raise SvgInputRejected("SVG_PATH_NOT_VISIBLE")
            stroke = "#1f2937"
        stroke_width = _number(element.attrib.get("stroke-width", "2"))
        if stroke_width <= 0 or stroke_width > 64:
            raise SvgInputRejected("SVG_STROKE_WIDTH_INVALID")
        if fill != "none":
            filled_shape_count += 1
        paths.append(
            {
                "path_id": path_id,
                "d": path_data,
                "fill": fill,
                "stroke": stroke,
                "stroke_width": stroke_width,
            }
        )
        if len(paths) > MAX_PATHS:
            raise SvgInputRejected("SVG_PATH_LIMIT_EXCEEDED")

    if root.attrib.get("id") and not re.fullmatch(r"[A-Za-z0-9._:-]{1,96}", root.attrib["id"]):
        raise SvgInputRejected("SVG_ROOT_ATTRIBUTE_FORBIDDEN")
    for child in list(root):
        walk(child)
    if (root.text or "").strip() or any((child.tail or "").strip() for child in root):
        raise SvgInputRejected("SVG_TEXT_CONTENT_FORBIDDEN")
    if not paths:
        raise SvgInputRejected("SVG_NO_DRAWABLE_PATHS")
    if len({path["path_id"] for path in paths}) != len(paths):
        raise SvgInputRejected("SVG_PATH_ID_DUPLICATE")
    geometry_hashes = [hashlib.sha256(path["d"].encode("ascii")).hexdigest() for path in paths]
    if len(set(geometry_hashes)) != len(geometry_hashes):
        raise SvgInputRejected("SVG_DUPLICATE_GEOMETRY")

    document = {
        "schema_version": "SvgDocumentV1",
        "view_box": view_box,
        "paths": paths,
    }
    canonical = canonical_json_bytes(document)
    if len(canonical) > MAX_CANONICAL_BYTES:
        raise SvgInputRejected("SVG_CANONICAL_SIZE_INVALID")
    readiness = classify_svg_source(
        drawable_path_ids=[path["path_id"] for path in paths],
        filled_shape_count=filled_shape_count,
        educator_approved=False,
        curator_grouping_allowed=False,
    )
    return SanitizedSvg(
        document=document,
        source_sha256=hashlib.sha256(source).hexdigest(),
        canonical_sha256=hashlib.sha256(canonical).hexdigest(),
        readiness=readiness,
    )


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _namespace(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


def _require_attributes(element: ET.Element, *, allowed: set[str]) -> None:
    for name, value in element.attrib.items():
        if name.startswith("{") or name.lower().startswith("on") or name not in allowed:
            raise SvgInputRejected("SVG_ATTRIBUTE_FORBIDDEN")
        if any(marker in value.lower() for marker in ("url(", "javascript:", "data:", "http:", "https:")):
            raise SvgInputRejected("SVG_EXTERNAL_RESOURCE_FORBIDDEN")


def _parse_view_box(attributes: dict[str, str]) -> str:
    allowed = {"xmlns", "viewBox", "width", "height", "id"}
    if any(name not in allowed for name in attributes):
        raise SvgInputRejected("SVG_ROOT_ATTRIBUTE_FORBIDDEN")
    raw = attributes.get("viewBox")
    if raw is None:
        width = _number(attributes.get("width", "0"))
        height = _number(attributes.get("height", "0"))
        raw = f"0 0 {width} {height}"
    pieces = re.split(r"[\s,]+", raw.strip())
    if len(pieces) != 4:
        raise SvgInputRejected("SVG_VIEWBOX_INVALID")
    numbers = [_number(piece) for piece in pieces]
    x, y, width, height = numbers
    if width <= 0 or height <= 0:
        raise SvgInputRejected("SVG_VIEWBOX_INVALID")
    if any(abs(number) > MAX_COORDINATE for number in numbers):
        raise SvgInputRejected("SVG_COORDINATE_LIMIT_EXCEEDED")
    return " ".join(_format_number(number) for number in numbers)


def _number(raw: str) -> float:
    if not isinstance(raw, str) or not _NUMBER_PATTERN.fullmatch(raw.strip()):
        raise SvgInputRejected("SVG_NUMBER_INVALID")
    number = float(raw)
    if not math.isfinite(number) or abs(number) > MAX_COORDINATE:
        raise SvgInputRejected("SVG_COORDINATE_LIMIT_EXCEEDED")
    return number


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _color(value: str) -> str:
    normalized = value.strip().lower()
    if not _COLOR_PATTERN.fullmatch(normalized):
        raise SvgInputRejected("SVG_COLOR_INVALID")
    return normalized


def _shape_to_path(name: str, attributes: dict[str, str]) -> str:
    if name == "path":
        value = attributes.get("d", "")
        if not value or len(value) > MAX_PATH_CHARS:
            raise SvgInputRejected("SVG_PATH_DATA_INVALID")
        _validate_path_grammar(value)
        return value
    if name == "line":
        x1, y1, x2, y2 = (_number(attributes.get(key, "0")) for key in ("x1", "y1", "x2", "y2"))
        return f"M {_format_number(x1)} {_format_number(y1)} L {_format_number(x2)} {_format_number(y2)}"
    if name in {"polyline", "polygon"}:
        points = attributes.get("points", "")
        if not points or len(points) > MAX_PATH_CHARS or not _POINTS_PATTERN.fullmatch(points):
            raise SvgInputRejected("SVG_POINTS_INVALID")
        numbers = [_number(item) for item in re.split(r"[\s,]+", points.strip()) if item]
        if len(numbers) < 4 or len(numbers) % 2:
            raise SvgInputRejected("SVG_POINTS_INVALID")
        chunks = [f"M {_format_number(numbers[0])} {_format_number(numbers[1])}"]
        chunks.extend(
            f"L {_format_number(numbers[index])} {_format_number(numbers[index + 1])}"
            for index in range(2, len(numbers), 2)
        )
        if name == "polygon":
            chunks.append("Z")
        return " ".join(chunks)
    if name == "rect":
        x, y = _number(attributes.get("x", "0")), _number(attributes.get("y", "0"))
        width, height = _number(attributes.get("width", "0")), _number(attributes.get("height", "0"))
        if width <= 0 or height <= 0:
            raise SvgInputRejected("SVG_RECT_SIZE_INVALID")
        right_value, bottom_value = x + width, y + height
        if abs(right_value) > MAX_COORDINATE or abs(bottom_value) > MAX_COORDINATE:
            raise SvgInputRejected("SVG_COORDINATE_LIMIT_EXCEEDED")
        right, bottom = _format_number(right_value), _format_number(bottom_value)
        return (
            f"M {_format_number(x)} {_format_number(y)} L {right} {_format_number(y)} "
            f"L {right} {bottom} L {_format_number(x)} {bottom} Z"
        )
    if name in {"circle", "ellipse"}:
        cx, cy = _number(attributes.get("cx", "0")), _number(attributes.get("cy", "0"))
        rx = _number(attributes.get("r", "0")) if name == "circle" else _number(attributes.get("rx", "0"))
        ry = rx if name == "circle" else _number(attributes.get("ry", "0"))
        if rx <= 0 or ry <= 0:
            raise SvgInputRejected("SVG_ELLIPSE_SIZE_INVALID")
        left, right = _format_number(cx - rx), _format_number(cx + rx)
        top, bottom = _format_number(cy - ry), _format_number(cy + ry)
        return (
            f"M {left} {_format_number(cy)} A {_format_number(rx)} {_format_number(ry)} 0 1 0 "
            f"{right} {_format_number(cy)} A {_format_number(rx)} {_format_number(ry)} 0 1 0 "
            f"{left} {_format_number(cy)} Z"
        )
    raise SvgInputRejected("SVG_ELEMENT_UNSUPPORTED")


def _normalize_path_data(value: str) -> str:
    normalized = re.sub(r"\s*,\s*", ",", value.strip())
    normalized = re.sub(r"\s+", " ", normalized)
    if len(normalized) > MAX_PATH_CHARS:
        raise SvgInputRejected("SVG_PATH_DATA_INVALID")
    _validate_path_grammar(normalized)
    return normalized


def _validate_path_grammar(value: str) -> None:
    """Validate command arity and numeric bounds before handing data to an SVG renderer."""
    tokens = _PATH_PATTERN.findall(value)
    compact = re.sub(r"[\s,]+", "", value)
    if not tokens or "".join(tokens) != compact:
        raise SvgInputRejected("SVG_PATH_DATA_INVALID")

    arity = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7}
    index = 0
    command: str | None = None
    saw_move = False
    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token
            index += 1
            if command in "Zz":
                if not saw_move:
                    raise SvgInputRejected("SVG_PATH_DATA_INVALID")
                command = None
                continue
            if command in "Mm":
                if saw_move:
                    # A later move is legal, and starts another subpath.
                    pass
                saw_move = True
            elif not saw_move:
                raise SvgInputRejected("SVG_PATH_DATA_INVALID")
        elif command is None:
            raise SvgInputRejected("SVG_PATH_DATA_INVALID")

        if command is None:
            continue
        values: list[float] = []
        while index < len(tokens) and not tokens[index].isalpha():
            raw = tokens[index]
            if not _NUMBER_PATTERN.fullmatch(raw):
                raise SvgInputRejected("SVG_PATH_DATA_INVALID")
            number = float(raw)
            if not math.isfinite(number) or abs(number) > MAX_COORDINATE:
                raise SvgInputRejected("SVG_COORDINATE_LIMIT_EXCEEDED")
            values.append(number)
            index += 1
        upper = command.upper()
        count = arity.get(upper)
        if count is None or len(values) < count or len(values) % count:
            raise SvgInputRejected("SVG_PATH_DATA_INVALID")
        if upper == "A":
            for offset in range(0, len(values), 7):
                if values[offset] < 0 or values[offset + 1] < 0:
                    raise SvgInputRejected("SVG_PATH_DATA_INVALID")
                if values[offset + 3] not in {0.0, 1.0} or values[offset + 4] not in {0.0, 1.0}:
                    raise SvgInputRejected("SVG_PATH_DATA_INVALID")
        if upper == "M":
            # Subsequent coordinate pairs are implicit line segments.
            command = "l" if command.islower() else "L"


__all__ = [
    "MAX_CANONICAL_BYTES",
    "MAX_SOURCE_BYTES",
    "SANITIZER_VERSION",
    "SANITIZER_CODE_SHA256",
    "SanitizedSvg",
    "SvgInputRejected",
    "canonical_json_bytes",
    "sanitize_svg_source",
]
