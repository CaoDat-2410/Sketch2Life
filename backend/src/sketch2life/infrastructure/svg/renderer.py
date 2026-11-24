"""Deterministic SVG serialization for canonical vector documents."""

from __future__ import annotations

import html
import math
import re
from collections.abc import Mapping
from typing import Any

from sketch2life.domain.svg_engine import SvgRuleError
from sketch2life.infrastructure.svg.sanitizer import SvgInputRejected, _validate_path_grammar

_VIEW_BOX_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_VIEW_BOX = re.compile(rf"^{_VIEW_BOX_NUMBER} {_VIEW_BOX_NUMBER} {_VIEW_BOX_NUMBER} {_VIEW_BOX_NUMBER}$")
_COLOR = re.compile(r"^(?:none|#[0-9a-f]{6})$")


def render_svg_document(document: Mapping[str, Any], *, visible_path_ids: set[str] | None = None) -> str:
    """Serialize only validated canonical path records; never accepts markup."""
    if document.get("schema_version") != "SvgDocumentV1":
        raise SvgRuleError("SVG_DOCUMENT_SCHEMA_UNSUPPORTED")
    view_box = document.get("view_box")
    paths = document.get("paths")
    if not isinstance(view_box, str) or not _VIEW_BOX.fullmatch(view_box):
        raise SvgRuleError("SVG_DOCUMENT_VIEWBOX_INVALID")
    view_values = [float(piece) for piece in view_box.split()]
    if (
        len(view_values) != 4
        or not all(math.isfinite(value) and abs(value) <= 10_000 for value in view_values)
        or view_values[2] <= 0
        or view_values[3] <= 0
    ):
        raise SvgRuleError("SVG_DOCUMENT_VIEWBOX_INVALID")
    if not isinstance(paths, list) or not 1 <= len(paths) <= 400:
        raise SvgRuleError("SVG_DOCUMENT_PATHS_INVALID")
    elements: list[str] = []
    seen_ids: set[str] = set()
    for path in paths:
        if not isinstance(path, Mapping):
            raise SvgRuleError("SVG_DOCUMENT_PATH_INVALID")
        path_id, data = path.get("path_id"), path.get("d")
        fill, stroke, width = path.get("fill"), path.get("stroke"), path.get("stroke_width")
        if (
            not isinstance(path_id, str)
            or not re.fullmatch(r"[A-Za-z0-9._:-]{1,96}", path_id)
            or path_id in seen_ids
            or not isinstance(data, str)
            or not data
            or len(data) > 8192
            or not isinstance(fill, str)
            or not _COLOR.fullmatch(fill)
            or not isinstance(stroke, str)
            or not _COLOR.fullmatch(stroke)
            or isinstance(width, bool)
            or not isinstance(width, (int, float))
            or not 0 < width <= 64
        ):
            raise SvgRuleError("SVG_DOCUMENT_PATH_INVALID")
        try:
            _validate_path_grammar(data)
        except SvgInputRejected as exc:
            raise SvgRuleError("SVG_DOCUMENT_PATH_INVALID") from exc
        seen_ids.add(path_id)
        if visible_path_ids is not None and path_id not in visible_path_ids:
            continue
        elements.append(
            '<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
            'stroke-linecap="round" stroke-linejoin="round" data-path-id="{path_id}"/>'.format(
                d=html.escape(data, quote=True),
                fill=html.escape(fill, quote=True),
                stroke=html.escape(stroke, quote=True),
                width=f"{float(width):.4f}".rstrip("0").rstrip("."),
                path_id=html.escape(path_id, quote=True),
            )
        )
    if visible_path_ids is not None and not visible_path_ids.issubset(seen_ids):
        raise SvgRuleError("SVG_GUIDE_UNKNOWN_PATH")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" '
        f'role="img" aria-label="Hình minh họa">{"".join(elements)}</svg>'
    )


__all__ = ["render_svg_document"]
