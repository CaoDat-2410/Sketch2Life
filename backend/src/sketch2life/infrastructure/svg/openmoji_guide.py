"""Build child-friendly Parent guides from a tiny pinned OpenMoji SVG pack."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Any

from pydantic import ValidationError

from sketch2life.contracts.schemas.svg_engine import (
    SvgPathV1,
    SvgReferenceIllustrationDocumentV1,
    SvgReferenceIllustrationPathV1,
    SvgReferenceSourceProvenanceV1,
    SvgTopicStrokeGuideModelResultV1,
    SvgTopicStrokeGuidePartV1,
    SvgTopicStrokeGuideStageV1,
)
from sketch2life.infrastructure.svg.sanitizer import sanitize_svg_source


_MANIFEST_FILENAME = "parent-guide-manifest.json"
_MANIFEST_SHA256 = "086957a6a66c87a523edef5296d71517411a1a5c6d30b1b11626cd3d0af98ede"
_LICENSE_SHA256 = "28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5"
_EXPECTED_DATASET_REVISION = "f9fc506a3f913be9897ab0181d611d4c910a4104"
_MAX_MANIFEST_BYTES = 32_000
_MAX_SOURCE_BYTES = 64_000
_SVG_NS = "http://www.w3.org/2000/svg"
_ALLOWED_GROUPS = frozenset({"color", "line", "hair", "skin", "skin-shadow"})
_SHAPE_TAGS = frozenset({"path", "line", "polyline", "polygon", "circle", "ellipse", "rect"})
_STYLE_ATTRIBUTES = frozenset(
    {"fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit"}
)
_DERIVATION_METHOD = "OPENMOJI_SOURCE_SHAPE_TO_PATH_V1"
_DEFAULT_GUIDE_STROKE = "#20293b"
_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


class OpenMojiGuideUnavailable(ValueError):
    """A pinned source, license, manifest, or source/color pair failed validation."""


@dataclass(frozen=True, slots=True)
class _SourceShape:
    source_shape_id: str
    tag: str
    d: str
    fill: str
    stroke: str
    stroke_width: float
    stroke_linecap: str
    stroke_linejoin: str
    stroke_miterlimit: float


@dataclass(frozen=True, slots=True)
class OpenMojiDerivedGuide:
    generated: SvgTopicStrokeGuideModelResultV1
    reference_source: SvgReferenceSourceProvenanceV1
    reference_illustration: SvgReferenceIllustrationDocumentV1
    engine_id: str
    engine_revision: str
    source_guide_uri: str
    source_guide_sha256: str
    derivation_method: str
    source_path_count: int
    path_lineage: tuple[dict[str, Any], ...]


def build_openmoji_guide(topic: str) -> OpenMojiDerivedGuide | None:
    """Resolve supported topics to a locally pinned, no-AI progressive guide."""
    if not _source_directory().is_dir():
        return None
    manifest, manifest_hash = _load_manifest()
    asset = _resolve_asset(manifest, topic)
    if asset is None:
        return None

    source_dir = _source_directory()
    license_file = manifest["dataset"]["license_file"]
    license_bytes = _read_bounded(source_dir / license_file, _MAX_SOURCE_BYTES)
    if hashlib.sha256(license_bytes).hexdigest() != _LICENSE_SHA256:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_LICENSE_HASH_MISMATCH")
    if manifest["dataset"].get("license_sha256") != _LICENSE_SHA256:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_MANIFEST_LICENSE_MISMATCH")

    black_bytes = _read_bounded(source_dir / asset["black_filename"], _MAX_SOURCE_BYTES)
    color_bytes = _read_bounded(source_dir / asset["color_filename"], _MAX_SOURCE_BYTES)
    black_sha256 = hashlib.sha256(black_bytes).hexdigest()
    color_sha256 = hashlib.sha256(color_bytes).hexdigest()
    if black_sha256 != asset.get("black_sha256") or color_sha256 != asset.get("color_sha256"):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SOURCE_HASH_MISMATCH")

    black_shapes, black_groups, view_box = _read_source_svg(black_bytes, expected_view_box=asset["view_box"])
    color_shapes, color_groups, color_view_box = _read_source_svg(color_bytes, expected_view_box=asset["view_box"])
    if view_box != color_view_box or "line" not in black_groups or "line" not in color_groups:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SOURCE_PAIR_INVALID")
    guide_shapes = black_groups["line"]
    color_line_shapes = color_groups["line"]
    if len(guide_shapes) != asset.get("source_shape_count"):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SOURCE_SHAPE_COUNT_MISMATCH")
    source_shape_ids = [shape.source_shape_id for shape in guide_shapes]
    if source_shape_ids != asset.get("source_shape_ids"):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SOURCE_SHAPE_INVENTORY_MISMATCH")
    if len(guide_shapes) != len(color_line_shapes):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_COLOR_LINE_COUNT_MISMATCH")

    guide_safe = _sanitize_shapes(guide_shapes, force_line_only=True)
    color_line_safe = _sanitize_shapes(color_line_shapes, force_line_only=True)
    if [item["d"] for item in guide_safe] != [item["d"] for item in color_line_safe]:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_COLOR_LINE_GEOMETRY_MISMATCH")

    color_only = [shape for shape in color_shapes if shape.source_shape_id not in {item.source_shape_id for item in color_line_shapes}]
    reference_shapes = [*color_only, *color_line_shapes]
    reference_safe = _sanitize_shapes(
        reference_shapes,
        force_line_only=True,
        allow_duplicate_geometry=True,
    )
    if len(reference_safe) != len(reference_shapes):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_REFERENCE_SANITIZER_MISMATCH")

    stage_specs = asset.get("stages")
    if not isinstance(stage_specs, list) or not 4 <= len(stage_specs) <= 8:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_STAGE_COUNT_INVALID")
    assigned_ids: list[str] = []
    parts: list[SvgTopicStrokeGuidePartV1] = []
    stages: list[SvgTopicStrokeGuideStageV1] = []
    path_labels: dict[str, str] = {}
    for expected_index, stage_spec in enumerate(stage_specs, start=1):
        if not isinstance(stage_spec, dict) or stage_spec.get("step_index") != expected_index:
            raise OpenMojiGuideUnavailable("SVG_OPENMOJI_STAGE_ORDER_INVALID")
        part_id = stage_spec.get("part_id")
        path_ids = stage_spec.get("path_ids")
        label = stage_spec.get("label_vi")
        instruction = stage_spec.get("instruction_vi")
        if (
            not isinstance(part_id, str)
            or not re.fullmatch(r"[A-Za-z0-9._:-]{1,96}", part_id)
            or not isinstance(path_ids, list)
            or not 1 <= len(path_ids) <= 6
            or not isinstance(label, str)
            or not isinstance(instruction, str)
            or not label.strip()
            or not instruction.strip()
        ):
            raise OpenMojiGuideUnavailable("SVG_OPENMOJI_STAGE_CONTENT_INVALID")
        if any(path_id not in source_shape_ids for path_id in path_ids):
            raise OpenMojiGuideUnavailable("SVG_OPENMOJI_STAGE_SHAPE_UNKNOWN")
        if len(set(path_ids)) != len(path_ids) or set(assigned_ids).intersection(path_ids):
            raise OpenMojiGuideUnavailable("SVG_OPENMOJI_STAGE_SHAPE_DUPLICATE")
        parts.append(
            SvgTopicStrokeGuidePartV1(
                part_id=part_id,
                label_vi=label,
                path_ids=path_ids,
                depends_on=[parts[-1].part_id] if parts else [],
            )
        )
        stages.append(
            SvgTopicStrokeGuideStageV1(
                step_index=expected_index,
                instruction_vi=instruction,
                part_ids=[part_id],
                new_path_ids=path_ids,
                animation_order=path_ids,
            )
        )
        assigned_ids.extend(path_ids)
        path_labels.update({path_id: label for path_id in path_ids})
    if len(assigned_ids) != len(source_shape_ids) or set(assigned_ids) != set(source_shape_ids):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SOURCE_SHAPE_COVERAGE_INVALID")

    sanitized_by_id = {item["path_id"]: item for item in guide_safe}
    source_by_id = {shape.source_shape_id: shape for shape in guide_shapes}
    guide_paths = [
        SvgPathV1(
            path_id=path_id,
            d=sanitized_by_id[path_id]["d"],
            fill="none",
            stroke=source_by_id[path_id].stroke if source_by_id[path_id].stroke != "none" else _DEFAULT_GUIDE_STROKE,
            stroke_width=source_by_id[path_id].stroke_width,
        )
        for path_id in assigned_ids
    ]
    try:
        generated = SvgTopicStrokeGuideModelResultV1.model_validate(
            {
                "schema_version": "SvgTopicStrokeGuideContentV1",
                "title_vi": asset["title_vi"],
                "document": {
                    "schema_version": "SvgDocumentV1",
                    "view_box": view_box,
                    "paths": [path.model_dump(mode="json") for path in guide_paths],
                },
                "parts": [part.model_dump(mode="json") for part in parts],
                "stages": [stage.model_dump(mode="json") for stage in stages],
            }
        )
    except (KeyError, TypeError, ValidationError) as exc:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_GUIDE_SCHEMA_INVALID") from exc

    guide_by_id = {path.path_id: path for path in generated.document.paths}
    if list(guide_by_id) != assigned_ids or any(path.fill != "none" for path in generated.document.paths):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_GUIDE_GEOMETRY_INVALID")

    reference_paths = []
    for shape, item in zip(reference_shapes, reference_safe, strict=True):
        reference_paths.append(
            SvgReferenceIllustrationPathV1(
                path_id=item["path_id"],
                d=item["d"],
                fill=shape.fill,
                stroke=shape.stroke,
                stroke_width=shape.stroke_width,
                stroke_linecap=shape.stroke_linecap,
                stroke_linejoin=shape.stroke_linejoin,
                stroke_miterlimit=shape.stroke_miterlimit,
            )
        )
    reference_illustration = SvgReferenceIllustrationDocumentV1(
        view_box=view_box,
        paths=reference_paths,
    )
    reference_source = SvgReferenceSourceProvenanceV1(
        asset_id=asset["asset_id"],
        dataset_name=manifest["dataset"]["name"],
        dataset_revision=manifest["dataset"]["revision"],
        dataset_doi=None,
        dataset_uri=(
            f"{manifest['dataset']['repository']}/blob/"
            f"{manifest['dataset']['revision']}/{asset['upstream_color_path']}"
        ),
        source_sha256=color_sha256,
        license_id=manifest["dataset"]["license_id"],
        license_uri=manifest["dataset"]["license_uri"],
    )
    lineage = tuple(
        {
            "derived_path_id": path_id,
            "source_path_ids": [path_id],
            "feature_vi": path_labels[path_id],
            "operation": _DERIVATION_METHOD,
        }
        for path_id in assigned_ids
    )
    return OpenMojiDerivedGuide(
        generated=generated,
        reference_source=reference_source,
        reference_illustration=reference_illustration,
        engine_id="openmoji-source-shape-guide",
        engine_revision=f"1.0.0+{manifest_hash[:12]}",
        source_guide_uri=(
            f"{manifest['dataset']['repository']}/blob/"
            f"{manifest['dataset']['revision']}/{asset['upstream_black_path']}"
        ),
        source_guide_sha256=black_sha256,
        derivation_method=_DERIVATION_METHOD,
        source_path_count=len(source_shape_ids),
        path_lineage=lineage,
    )


def _source_directory() -> Path:
    return Path(__file__).resolve().parents[5] / "deployment" / "modal" / "srs_v23" / "data" / "openmoji"


def _load_manifest() -> tuple[dict[str, Any], str]:
    manifest_bytes = _read_bounded(_source_directory() / _MANIFEST_FILENAME, _MAX_MANIFEST_BYTES)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_hash != _MANIFEST_SHA256:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_MANIFEST_HASH_MISMATCH")
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_MANIFEST_INVALID") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != "OpenMojiParentGuideManifestV1"
        or not isinstance(manifest.get("dataset"), dict)
        or not isinstance(manifest.get("assets"), list)
        or manifest["dataset"].get("revision") != _EXPECTED_DATASET_REVISION
    ):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_MANIFEST_INVALID")
    return manifest, manifest_hash


def _resolve_asset(manifest: dict[str, Any], topic: str) -> dict[str, Any] | None:
    normalized = _normalize_topic(topic)
    matched: list[dict[str, Any]] = []
    for asset in manifest["assets"]:
        if not isinstance(asset, dict) or not isinstance(asset.get("topic_aliases"), list):
            raise OpenMojiGuideUnavailable("SVG_OPENMOJI_ASSET_MANIFEST_INVALID")
        aliases = {_normalize_topic(alias) for alias in asset["topic_aliases"] if isinstance(alias, str)}
        if normalized in aliases:
            matched.append(asset)
    if len(matched) > 1:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_TOPIC_ALIAS_AMBIGUOUS")
    return matched[0] if matched else None


def _read_source_svg(source_bytes: bytes, *, expected_view_box: str) -> tuple[list[_SourceShape], dict[str, list[_SourceShape]], str]:
    if b"<!DOCTYPE" in source_bytes.upper() or b"<!ENTITY" in source_bytes.upper() or b"<?XML-STYLESHEET" in source_bytes.upper():
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_XML_DECLARATION_FORBIDDEN")
    try:
        root = ET.fromstring(source_bytes)
    except ET.ParseError as exc:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SOURCE_XML_INVALID") from exc
    if root.tag != f"{{{_SVG_NS}}}svg" or root.attrib.get("viewBox") != expected_view_box:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SOURCE_ROOT_INVALID")
    if set(root.attrib) - {"id", "viewBox", "xmlns", "version"}:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_ROOT_ATTRIBUTE_FORBIDDEN")
    if (root.text or "").strip():
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_TEXT_FORBIDDEN")

    groups: dict[str, list[_SourceShape]] = {}
    all_shapes: list[_SourceShape] = []
    for group in list(root):
        if group.tag != f"{{{_SVG_NS}}}g" or set(group.attrib) != {"id"}:
            raise OpenMojiGuideUnavailable("SVG_OPENMOJI_GROUP_UNSUPPORTED")
        group_id = group.attrib["id"]
        if group_id not in _ALLOWED_GROUPS or group_id in groups:
            raise OpenMojiGuideUnavailable("SVG_OPENMOJI_GROUP_ID_INVALID")
        group_shapes: list[_SourceShape] = []
        for element in list(group):
            if element.tag not in {f"{{{_SVG_NS}}}{tag}" for tag in _SHAPE_TAGS}:
                raise OpenMojiGuideUnavailable("SVG_OPENMOJI_ELEMENT_UNSUPPORTED")
            if list(element) or (element.text or "").strip() or (element.tail or "").strip():
                raise OpenMojiGuideUnavailable("SVG_OPENMOJI_DRAWABLE_CHILDREN_FORBIDDEN")
            shape = _read_shape(element, group_id=group_id, index=len(group_shapes) + 1)
            group_shapes.append(shape)
            all_shapes.append(shape)
        if (group.text or "").strip() or any((child.tail or "").strip() for child in group):
            raise OpenMojiGuideUnavailable("SVG_OPENMOJI_TEXT_FORBIDDEN")
        groups[group_id] = group_shapes
    if not groups.get("line"):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_LINE_GROUP_REQUIRED")
    return all_shapes, groups, expected_view_box


def _read_shape(element: ET.Element, *, group_id: str, index: int) -> _SourceShape:
    tag = element.tag.rsplit("}", 1)[-1]
    geometry_attributes = {
        "path": {"d"},
        "line": {"x1", "y1", "x2", "y2"},
        "polyline": {"points"},
        "polygon": {"points"},
        "circle": {"cx", "cy", "r"},
        "ellipse": {"cx", "cy", "rx", "ry"},
        "rect": {"x", "y", "width", "height"},
    }[tag]
    allowed = geometry_attributes | _STYLE_ATTRIBUTES | {"id"}
    if any(name not in allowed or name.lower().startswith("on") or name.startswith("{") for name in element.attrib):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SHAPE_ATTRIBUTE_FORBIDDEN")
    if "style" in element.attrib or any(key.startswith("data-") for key in element.attrib):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SHAPE_STYLE_FORBIDDEN")
    try:
        d = _shape_to_path(tag, element.attrib)
        fill = _normalize_color(element.attrib.get("fill", "#000000"))
        stroke = _normalize_color(element.attrib.get("stroke", "none"))
        stroke_width = _bounded_decimal(element.attrib.get("stroke-width", "1"), maximum=64)
        miterlimit = _bounded_decimal(element.attrib.get("stroke-miterlimit", "4"), minimum=1, maximum=10)
    except (ValueError, InvalidOperation, KeyError) as exc:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SHAPE_VALUE_INVALID") from exc
    if not d or len(d) > 8192 or stroke_width <= 0:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SHAPE_GEOMETRY_INVALID")
    linecap = element.attrib.get("stroke-linecap", "round")
    linejoin = element.attrib.get("stroke-linejoin", "round")
    if linecap not in {"butt", "round", "square"} or linejoin not in {"miter", "round", "bevel"}:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_LINE_STYLE_INVALID")
    prefix = "source-shape" if group_id == "line" else f"reference-{group_id}"
    return _SourceShape(
        source_shape_id=f"{prefix}-{index:03d}",
        tag=tag,
        d=d,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        stroke_linecap=linecap,
        stroke_linejoin=linejoin,
        stroke_miterlimit=miterlimit,
    )


def _shape_to_path(tag: str, attributes: dict[str, str]) -> str:
    if tag == "path":
        return attributes["d"].strip()
    if tag == "line":
        return f"M{_n(attributes['x1'])} {_n(attributes['y1'])}L{_n(attributes['x2'])} {_n(attributes['y2'])}"
    if tag in {"polyline", "polygon"}:
        points = [_n(match.group(0)) for match in _NUMBER.finditer(attributes["points"])]
        if not points or len(points) % 2:
            raise ValueError("SVG_POINTS_INVALID")
        pairs = [f"{points[index]} {points[index + 1]}" for index in range(0, len(points), 2)]
        data = "M" + "L".join(pairs)
        return data + ("Z" if tag == "polygon" else "")
    if tag == "circle":
        cx, cy, radius = (_n(attributes[key]) for key in ("cx", "cy", "r"))
        r = Decimal(radius)
        if r <= 0:
            raise ValueError("SVG_RADIUS_INVALID")
        left, right = _n(str(Decimal(cx) - r)), _n(str(Decimal(cx) + r))
        return f"M{left} {cy}A{radius} {radius} 0 1 0 {right} {cy}A{radius} {radius} 0 1 0 {left} {cy}"
    if tag == "ellipse":
        cx, cy, rx, ry = (_n(attributes[key]) for key in ("cx", "cy", "rx", "ry"))
        if Decimal(rx) <= 0 or Decimal(ry) <= 0:
            raise ValueError("SVG_RADIUS_INVALID")
        left, right = _n(str(Decimal(cx) - Decimal(rx))), _n(str(Decimal(cx) + Decimal(rx)))
        return f"M{left} {cy}A{rx} {ry} 0 1 0 {right} {cy}A{rx} {ry} 0 1 0 {left} {cy}"
    if tag == "rect":
        x, y, width, height = (_n(attributes[key]) for key in ("x", "y", "width", "height"))
        if Decimal(width) <= 0 or Decimal(height) <= 0:
            raise ValueError("SVG_RECT_SIZE_INVALID")
        right, bottom = _n(str(Decimal(x) + Decimal(width))), _n(str(Decimal(y) + Decimal(height)))
        return f"M{x} {y}H{right}V{bottom}H{x}Z"
    raise ValueError("SVG_ELEMENT_UNSUPPORTED")


def _sanitize_shapes(
    shapes: list[_SourceShape],
    *,
    force_line_only: bool,
    allow_duplicate_geometry: bool = False,
) -> list[dict[str, Any]]:
    if not shapes or len(shapes) > 64:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SHAPE_LIMIT_INVALID")
    if allow_duplicate_geometry:
        clean_paths: list[dict[str, Any]] = []
        for shape in shapes:
            clean_paths.extend(
                _sanitize_shapes([shape], force_line_only=force_line_only)
            )
        return clean_paths
    root = ET.Element(f"{{{_SVG_NS}}}svg", {"viewBox": "0 0 72 72"})
    for shape in shapes:
        ET.SubElement(
            root,
            f"{{{_SVG_NS}}}path",
            {
                "id": shape.source_shape_id,
                "d": shape.d,
                "fill": "none" if force_line_only else shape.fill,
                "stroke": shape.stroke if shape.stroke != "none" else _DEFAULT_GUIDE_STROKE,
                "stroke-width": _n(str(shape.stroke_width)),
            },
        )
    try:
        sanitized = sanitize_svg_source(ET.tostring(root, encoding="utf-8"))
    except ValueError as exc:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SANITIZER_REJECTED_SOURCE") from exc
    paths = sanitized.document.get("paths")
    if not isinstance(paths, list) or len(paths) != len(shapes):
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SANITIZER_PATH_COUNT_MISMATCH")
    return paths


def _normalize_color(value: str) -> str:
    if value == "none":
        return value
    if re.fullmatch(r"#[0-9a-fA-F]{3}", value):
        value = "#" + "".join(character * 2 for character in value[1:])
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("SVG_COLOR_INVALID")
    return value.lower()


def _bounded_decimal(value: str, *, minimum: float = 0, maximum: float) -> float:
    number = Decimal(value)
    if not number.is_finite() or number < Decimal(str(minimum)) or number > Decimal(str(maximum)):
        raise ValueError("SVG_NUMBER_OUT_OF_RANGE")
    return float(number)


def _n(value: str) -> str:
    matches = list(_NUMBER.finditer(value))
    stripped = _NUMBER.sub("", value)
    if not matches or stripped.strip(" ,\t\r\n"):
        raise ValueError("SVG_NUMBER_INVALID")
    normalized: list[str] = []
    for match in matches:
        number = Decimal(match.group(0))
        if not number.is_finite() or abs(number) > Decimal("10000"):
            raise ValueError("SVG_COORDINATE_INVALID")
        normalized.append(format(number.normalize(), "f"))
    if len(normalized) != 1:
        raise ValueError("SVG_NUMBER_INVALID")
    return normalized[0]


def _read_bounded(path: Path, max_bytes: int) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SOURCE_FILE_UNAVAILABLE") from exc
    if not payload or len(payload) > max_bytes:
        raise OpenMojiGuideUnavailable("SVG_OPENMOJI_SOURCE_SIZE_INVALID")
    return payload


def _normalize_topic(topic: str) -> str:
    folded = unicodedata.normalize("NFKD", topic.casefold())
    plain = "".join(character for character in folded if not unicodedata.combining(character))
    return " ".join(re.findall(r"[a-z0-9]+", plain))


__all__ = ["OpenMojiDerivedGuide", "OpenMojiGuideUnavailable", "build_openmoji_guide"]
