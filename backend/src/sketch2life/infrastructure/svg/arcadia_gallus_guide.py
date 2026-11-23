"""Load and verify the pinned, source-derived Arcadia chicken guide."""

from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from sketch2life.contracts.schemas.svg_engine import (
    SvgPathV1,
    SvgReferenceIllustrationDocumentV1,
    SvgReferenceIllustrationPathV1,
    SvgReferenceSourceProvenanceV1,
    SvgTopicStrokeGuideModelResultV1,
)
from sketch2life.domain.svg_engine import (
    ARCADIA_GALLUS_REFERENCE_SOURCE_V1,
    topic_uses_arcadia_gallus_reference,
)
from sketch2life.infrastructure.svg.sanitizer import sanitize_svg_source

_SOURCE_FILENAME = "gallus-gallus-source.svg"
_SOURCE_METADATA_FILENAME = "gallus-gallus-v1.json"
_SOURCE_PATH_SEQUENCE_FILENAME = "arcadia-gallus-source-path-sequence-v7.json"
_SOURCE_PATH_SEQUENCE_SHA256 = "22eb7e077416b64db52b65ede1a45b584e1315a96d1b7e1ac110118510e532c6"
_EXPECTED_SOURCE_PATH_COUNT = 77
_DERIVATION_METHOD = "EXACT_SOURCE_PATH_SEQUENCE_V7"
_GUIDE_STROKE_COLOR = "#221f1f"
_SVG_NS = "http://www.w3.org/2000/svg"
_CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_CSS_PROPERTY = re.compile(r"^([a-z-]+)\s*:\s*([^;]+)$")
_SAFE_CSS_PROPERTIES = {"fill", "stroke", "stroke-width", "stroke-miterlimit"}


class ArcadiaDerivedGuideUnavailable(ValueError):
    """The pinned source/derivation failed a provenance or shape check."""


@dataclass(frozen=True)
class ArcadiaDerivedGuide:
    generated: SvgTopicStrokeGuideModelResultV1
    reference_source: SvgReferenceSourceProvenanceV1
    reference_illustration: SvgReferenceIllustrationDocumentV1
    engine_id: str
    engine_revision: str
    derivation_method: str
    source_path_count: int
    path_lineage: tuple[dict[str, Any], ...]


def build_arcadia_gallus_guide(topic: str) -> ArcadiaDerivedGuide | None:
    """Build a progressive line guide from the pinned illustration's exact paths."""
    if not topic_uses_arcadia_gallus_reference(topic) or not _source_directory().is_dir():
        return None

    source_dir = _source_directory()
    source_bytes = _read_bounded(source_dir / _SOURCE_FILENAME, max_bytes=256_000)
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != ARCADIA_GALLUS_REFERENCE_SOURCE_V1["source_sha256"]:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_HASH_MISMATCH")

    source_metadata = _load_json(source_dir / _SOURCE_METADATA_FILENAME)
    metadata_asset = source_metadata.get("asset")
    if (
        not isinstance(metadata_asset, dict)
        or metadata_asset.get("sha256") != source_sha256
        or metadata_asset.get("reference_only") is not True
        or metadata_asset.get("contains_stroke_order") is not False
    ):
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_METADATA_INVALID")

    _, source_path_ids, reference_illustration = _read_source_paths(source_bytes)
    if len(source_path_ids) != _EXPECTED_SOURCE_PATH_COUNT:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_PATH_COUNT_MISMATCH")

    manifest_bytes = _read_bounded(source_dir / _SOURCE_PATH_SEQUENCE_FILENAME, max_bytes=64_000)
    if hashlib.sha256(manifest_bytes).hexdigest() != _SOURCE_PATH_SEQUENCE_SHA256:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_GUIDE_MANIFEST_HASH_MISMATCH")
    manifest = _decode_json(manifest_bytes)
    source_record = manifest.get("source")
    derivation = manifest.get("derivation")
    if (
        manifest.get("schema_version") != "ArcadiaSourcePathSequenceGuideV7"
        or not isinstance(source_record, dict)
        or any(
            source_record.get(key) != expected
            for key, expected in ARCADIA_GALLUS_REFERENCE_SOURCE_V1.items()
        )
        or source_record.get("source_sha256") != source_sha256
        or source_record.get("source_path_count") != len(source_path_ids)
        or source_record.get("contains_stroke_order") is not False
        or not isinstance(derivation, dict)
        or derivation.get("engine_id") != "arcadia-source-svg-path-sequence"
        or derivation.get("engine_revision") != "7.0.0"
        or derivation.get("method") != _DERIVATION_METHOD
    ):
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_DERIVATION_PROVENANCE_INVALID")

    supported_topics = manifest.get("supported_topics")
    if not isinstance(supported_topics, list) or not any(
        _normalized_topic(topic) == _normalized_topic(alias) for alias in supported_topics
    ):
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_TOPIC_NOT_PINNED")

    source_paths_by_id = {path.path_id: path for path in reference_illustration.paths}
    expected_source_path_ids = [path.path_id for path in reference_illustration.paths]
    guide_parts, guide_stages, feature_by_path = _build_v7_guide_structure(
        manifest.get("stages"), expected_source_path_ids
    )
    guide_paths = [
        SvgPathV1(
            path_id=path_id,
            d=source_paths_by_id[path_id].d,
            fill="none",
            stroke=_GUIDE_STROKE_COLOR,
            stroke_width=source_paths_by_id[path_id].stroke_width,
        )
        for stage in guide_stages
        for path_id in stage.new_path_ids
    ]
    guide_content = {
        "schema_version": "SvgTopicStrokeGuideContentV1",
        "title_vi": manifest.get("title_vi"),
        "document": {
            "schema_version": "SvgDocumentV1",
            "view_box": reference_illustration.view_box,
            "paths": [path.model_dump(mode="json", exclude_none=True) for path in guide_paths],
        },
        "parts": [part.model_dump(mode="json") for part in guide_parts],
        "stages": [stage.model_dump(mode="json") for stage in guide_stages],
    }
    try:
        generated = SvgTopicStrokeGuideModelResultV1.model_validate(guide_content)
    except ValidationError as exc:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_GUIDE_SCHEMA_INVALID") from exc

    generated_by_id = {path.path_id: path for path in generated.document.paths}
    ordered_guide_path_ids = [
        path_id for stage in generated.stages for path_id in stage.new_path_ids
    ]
    if (
        list(generated_by_id) != ordered_guide_path_ids
        or len(ordered_guide_path_ids) != len(expected_source_path_ids)
        or set(ordered_guide_path_ids) != set(expected_source_path_ids)
        or any(path.fill != "none" for path in generated.document.paths)
        or any(
            generated_by_id[path_id].d != source_paths_by_id[path_id].d
            for path_id in expected_source_path_ids
        )
    ):
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_PATH_IDENTITY_INVALID")
    lineage = tuple(
        {
            "derived_path_id": path_id,
            "source_path_ids": [path_id],
            "feature_vi": feature_by_path[path_id],
            "operation": _DERIVATION_METHOD,
        }
        for path_id in expected_source_path_ids
    )

    reference_source = SvgReferenceSourceProvenanceV1.model_validate(
        {key: source_record[key] for key in ARCADIA_GALLUS_REFERENCE_SOURCE_V1}
    )
    return ArcadiaDerivedGuide(
        generated=generated,
        reference_source=reference_source,
        reference_illustration=reference_illustration,
        engine_id=derivation["engine_id"],
        engine_revision=derivation["engine_revision"],
        derivation_method=derivation["method"],
        source_path_count=len(source_path_ids),
        path_lineage=lineage,
    )


def _build_v7_guide_structure(
    value: Any,
    expected_path_ids: list[str],
) -> tuple[list[Any], list[Any], dict[str, str]]:
    from sketch2life.contracts.schemas.svg_engine import (
        SvgTopicStrokeGuidePartV1,
        SvgTopicStrokeGuideStageV1,
    )

    if not isinstance(value, list) or not 4 <= len(value) <= 8:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_STAGE_MANIFEST_INVALID")
    parts: list[Any] = []
    stages: list[Any] = []
    feature_by_path: dict[str, str] = {}
    previous_part_ids: list[str] = []
    staged_path_ids: list[str] = []
    try:
        for expected_index, raw in enumerate(value, start=1):
            if not isinstance(raw, dict) or raw.get("step_index") != expected_index:
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_STAGE_MANIFEST_INVALID")
            part_id = raw.get("part_id")
            label = raw.get("label_vi")
            instruction = raw.get("instruction_vi")
            path_ids = raw.get("path_ids")
            dependencies = raw.get("depends_on")
            if (
                not isinstance(part_id, str)
                or not isinstance(label, str)
                or not isinstance(instruction, str)
                or not isinstance(path_ids, list)
                or not path_ids
                or not isinstance(dependencies, list)
                or any(not isinstance(path_id, str) for path_id in path_ids)
            ):
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_STAGE_MANIFEST_INVALID")
            if any(path_id not in expected_path_ids for path_id in path_ids):
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_STAGE_PATH_UNKNOWN")
            if set(staged_path_ids).intersection(path_ids):
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_STAGE_PATH_DUPLICATED")
            if any(dependency not in previous_part_ids for dependency in dependencies):
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_STAGE_DEPENDENCY_INVALID")
            part = SvgTopicStrokeGuidePartV1(
                part_id=part_id,
                label_vi=label,
                path_ids=path_ids,
                depends_on=dependencies,
            )
            stage = SvgTopicStrokeGuideStageV1(
                step_index=expected_index,
                instruction_vi=instruction,
                part_ids=[part_id],
                new_path_ids=path_ids,
                animation_order=path_ids,
            )
            parts.append(part)
            stages.append(stage)
            feature_by_path.update({path_id: label for path_id in path_ids})
            staged_path_ids.extend(path_ids)
            previous_part_ids.append(part_id)
    except ValidationError as exc:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_STAGE_MANIFEST_INVALID") from exc

    if len(staged_path_ids) != len(expected_path_ids) or set(staged_path_ids) != set(
        expected_path_ids
    ):
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_PATH_COVERAGE_INVALID")
    return parts, stages, feature_by_path


def _source_directory() -> Path:
    return Path(__file__).resolve().parent / "data" / "arcadia_organism_strokes"


def arcadia_source_pack_installed() -> bool:
    """Return whether the optional pinned Arcadia source pack is available locally."""
    return _source_directory().is_dir()


def _read_bounded(path: Path, *, max_bytes: int) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_UNAVAILABLE") from exc
    if not payload or len(payload) > max_bytes:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_SIZE_INVALID")
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    payload = _read_bounded(path, max_bytes=256_000)
    return _decode_json(payload)


def _decode_json(payload: bytes) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_MANIFEST_INVALID") from exc
    if not isinstance(value, dict):
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_MANIFEST_INVALID")
    return value


def _read_source_paths(
    source_bytes: bytes,
) -> tuple[set[str], set[str], SvgReferenceIllustrationDocumentV1]:
    upper = source_bytes.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_XML_INVALID")
    try:
        root = ET.fromstring(source_bytes)
    except ET.ParseError as exc:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_XML_INVALID") from exc
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_XML_INVALID")
    if set(root.attrib) - {"id", "version", "viewBox"}:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_ATTRIBUTE_INVALID")
    view_box = root.attrib.get("viewBox")
    if view_box != "0 0 252 252":
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_VIEWBOX_INVALID")
    style_text = "\n".join(
        element.text or "" for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "style"
    )
    class_styles = _parse_source_styles(style_text)
    path_data: set[str] = set()
    path_ids: set[str] = set()
    illustration_paths: list[SvgReferenceIllustrationPathV1] = []
    for element in root.iter():
        name = element.tag.rsplit("}", 1)[-1]
        if name not in {"svg", "defs", "style", "g", "path"}:
            raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_ELEMENT_INVALID")
        if name in {"svg", "defs", "g"}:
            allowed = {"id", "version", "viewBox"} if name == "svg" else {"id"}
            if set(element.attrib) - allowed:
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_ATTRIBUTE_INVALID")
            continue
        if name == "style":
            if element.attrib or list(element):
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")
            continue
        if set(element.attrib) - {"id", "class", "d"}:
            raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_ATTRIBUTE_INVALID")
        data = element.attrib.get("d")
        classes = element.attrib.get("class", "").split()
        if not data or len(data) > 8192 or len(classes) != 1:
            raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_PATH_INVALID")
        style = class_styles.get(classes[0])
        if style is None:
            raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")
        fill = _source_color(style.get("fill", "none"))
        stroke = _source_color(style.get("stroke", "none"))
        if fill == "none" and stroke == "none":
            raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_PATH_INVISIBLE")
        width = _source_number(style.get("stroke-width", "0.71px"), allow_px=True)
        miterlimit = _source_number(style.get("stroke-miterlimit", "4"))
        if width <= 0 or width > 64 or miterlimit < 1 or miterlimit > 10:
            raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")

        validation_root = ET.Element(f"{{{_SVG_NS}}}svg", {"viewBox": view_box})
        validation_stroke = stroke
        if validation_stroke == "none":
            validation_stroke = fill if fill != "none" else "#000000"
        ET.SubElement(
            validation_root,
            f"{{{_SVG_NS}}}path",
            {
                "id": f"source-path-{len(path_ids) + 1:03d}",
                "d": data,
                "fill": fill,
                "stroke": validation_stroke,
                "stroke-width": f"{width:g}",
            },
        )
        try:
            sanitized = sanitize_svg_source(ET.tostring(validation_root, encoding="utf-8"))
        except ValueError as exc:
            raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_PATH_INVALID") from exc
        normalized_data = sanitized.document["paths"][0]["d"]
        path_data.add(data)
        path_ids.add(f"source-path-{len(path_ids) + 1:03d}")
        illustration_paths.append(
            SvgReferenceIllustrationPathV1(
                path_id=f"source-path-{len(path_ids):03d}",
                d=normalized_data,
                fill=fill,
                stroke=stroke,
                stroke_width=width,
                stroke_linecap="butt",
                stroke_linejoin="miter",
                stroke_miterlimit=miterlimit,
            )
        )
    if len(illustration_paths) != _EXPECTED_SOURCE_PATH_COUNT:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_PATH_COUNT_MISMATCH")
    return (
        path_data,
        path_ids,
        SvgReferenceIllustrationDocumentV1(
            view_box=view_box,
            paths=illustration_paths,
        ),
    )


def _parse_source_styles(style_text: str) -> dict[str, dict[str, str]]:
    remainder = re.sub(r"/\*.*?\*/", "", style_text, flags=re.DOTALL)
    styles: dict[str, dict[str, str]] = {}
    cursor = 0
    for match in _CSS_RULE.finditer(remainder):
        if remainder[cursor : match.start()].strip():
            raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")
        selectors, declarations = match.groups()
        parsed: dict[str, str] = {}
        for declaration in declarations.split(";"):
            declaration = declaration.strip()
            if not declaration:
                continue
            property_match = _CSS_PROPERTY.fullmatch(declaration)
            if property_match is None:
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")
            key, value = property_match.groups()
            if key not in _SAFE_CSS_PROPERTIES:
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")
            parsed[key] = value.strip()
        for selector in selectors.split(","):
            class_name = selector.strip().removeprefix(".")
            if not re.fullmatch(r"st[0-9]+", class_name):
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")
            styles.setdefault(class_name, {}).update(parsed)
        cursor = match.end()
    if remainder[cursor:].strip() or not styles:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")
    return styles


def _source_color(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "none":
        return normalized
    if re.fullmatch(r"#[0-9a-f]{3}", normalized):
        return "#" + "".join(character * 2 for character in normalized[1:])
    if re.fullmatch(r"#[0-9a-f]{6}", normalized):
        return normalized
    raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")


def _source_number(value: str, *, allow_px: bool = False) -> float:
    normalized = value.strip().lower()
    if allow_px and normalized.endswith("px"):
        normalized = normalized[:-2].strip()
    try:
        number = float(normalized)
    except ValueError as exc:
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID") from exc
    if not math.isfinite(number):
        raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_SOURCE_STYLE_INVALID")
    return number


def _normalized_topic(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.casefold())
    return " ".join("".join(ch for ch in normalized if not unicodedata.combining(ch)).split())
