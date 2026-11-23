"""Resolve a tiny pinned Openclipart SVG pack for Parent drawing guides."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Any

from pydantic import ValidationError

from sketch2life.contracts.schemas.svg_engine import (
    SvgReferenceIllustrationDocumentV1,
    SvgReferenceIllustrationPathV1,
    SvgReferenceSourceProvenanceV1,
    SvgTopicStrokeGuideModelResultV1,
    SvgTopicStrokeGuidePartV1,
    SvgTopicStrokeGuideStageV1,
)
from sketch2life.infrastructure.svg.sanitizer import (
    MAX_REFERENCE_PATH_CHARS,
    SvgInputRejected,
    sanitize_svg_source,
)


_MANIFEST_FILENAME = "parent-guide-manifest.json"
_MANIFEST_SHA256 = "570aa1bfa36c3e43d832edc745a2ce8320fd2cbe83880816016f793776099f3e"
_NOTICE_SHA256 = "231f9a0024319227977fa0ffc248334188f2df01e2f3fbdd40d76ad5f432d4e3"
_MAX_MANIFEST_BYTES = 32_000
_MAX_GUIDE_BYTES = 200_000
_MAX_SOURCE_BYTES = 128_000
_SVG_NS = "http://www.w3.org/2000/svg"


class OpenclipartGuideUnavailable(ValueError):
    """A pinned Openclipart asset, guide mapping, or provenance failed validation."""


@dataclass(frozen=True, slots=True)
class OpenclipartDerivedGuide:
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


def build_openclipart_guide(topic: str) -> OpenclipartDerivedGuide | None:
    """Resolve a generic topic to a pinned, local guide; never calls a model."""
    if not _data_directory().is_dir():
        return None
    manifest, manifest_sha256 = _load_manifest()
    asset = _resolve_asset(manifest, topic)
    if asset is None:
        return None
    _verify_source_file(asset, "color_source_file", "color_sha256")
    _verify_source_file(asset, "line_source_file", "line_sha256")
    guide_data_bytes = _read_bounded(_data_directory() / asset["guide_data_file"], _MAX_GUIDE_BYTES)
    if hashlib.sha256(guide_data_bytes).hexdigest() != asset.get("guide_data_sha256"):
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_HASH_MISMATCH")
    try:
        guide_data = json.loads(guide_data_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_JSON_INVALID") from exc
    if (
        not isinstance(guide_data, dict)
        or guide_data.get("schema_version") != "OpenclipartParentGuideDataV1"
        or guide_data.get("asset_id") != asset.get("asset_id")
    ):
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_SCHEMA_INVALID")
    source = guide_data.get("source")
    if not isinstance(source, dict) or any(
        source.get(key) != asset.get(manifest_key)
        for key, manifest_key in (
            ("color_source_file", "color_source_file"),
            ("line_source_file", "line_source_file"),
            ("color_sha256", "color_sha256"),
            ("line_sha256", "line_sha256"),
            ("color_source_uri", "color_source_uri"),
            ("line_source_uri", "line_source_uri"),
        )
    ) or any(
        source.get(key) != manifest.get(manifest_key)
        for key, manifest_key in (
            ("dataset_name", "dataset_name"),
            ("dataset_revision", "dataset_revision"),
            ("license_id", "license_id"),
            ("license_uri", "license_uri"),
        )
    ):
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_SOURCE_MISMATCH")

    raw_guide_paths = guide_data.get("guide_paths")
    raw_stages = guide_data.get("stages")
    if not isinstance(raw_guide_paths, list) or not isinstance(raw_stages, list) or not 4 <= len(raw_stages) <= 8:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_INVENTORY_INVALID")
    guide_root = ET.Element(
        f"{{{_SVG_NS}}}svg",
        {"viewBox": guide_data.get("guide_view_box", "")},
    )
    path_ids: list[str] = []
    source_path_ids: dict[str, str] = {}
    for item in raw_guide_paths:
        if not isinstance(item, dict):
            raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_PATH_INVALID")
        path_id = item.get("path_id")
        source_path_id = item.get("source_path_id")
        d = item.get("d")
        if (
            not isinstance(path_id, str)
            or not re.fullmatch(r"[A-Za-z0-9._:-]{1,96}", path_id)
            or not isinstance(source_path_id, str)
            or not re.fullmatch(r"[A-Za-z0-9._:-]{1,96}", source_path_id)
            or not isinstance(d, str)
            or not d
            or len(d) > 8192
            or item.get("fill") != "none"
            or item.get("stroke") != "#20293b"
        ):
            raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_PATH_INVALID")
        path_ids.append(path_id)
        source_path_ids[path_id] = source_path_id
        ET.SubElement(
            guide_root,
            f"{{{_SVG_NS}}}path",
            {
                "id": path_id,
                "d": d,
                "fill": "none",
                "stroke": "#20293b",
                "stroke-width": _format_number(item.get("stroke_width")),
            },
        )
    if len(path_ids) != len(set(path_ids)) or len(source_path_ids.values()) != len(set(source_path_ids.values())):
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_PATH_DUPLICATE")
    try:
        sanitized_guide = sanitize_svg_source(ET.tostring(guide_root, encoding="utf-8"))
    except (SvgInputRejected, ValueError) as exc:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_SANITIZER_REJECTED") from exc
    sanitized_guide_paths = sanitized_guide.document.get("paths")
    if not isinstance(sanitized_guide_paths, list) or [item.get("path_id") for item in sanitized_guide_paths] != path_ids:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_SANITIZER_MISMATCH")

    assigned: list[str] = []
    parts: list[SvgTopicStrokeGuidePartV1] = []
    stages: list[SvgTopicStrokeGuideStageV1] = []
    stage_labels: dict[str, str] = {}
    for index, stage in enumerate(raw_stages, start=1):
        if not isinstance(stage, dict) or stage.get("step_index") != index:
            raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_STAGE_ORDER_INVALID")
        stage_path_ids = stage.get("path_ids")
        part_id = stage.get("part_id")
        label = stage.get("label_vi")
        instruction = stage.get("instruction_vi")
        if (
            not isinstance(stage_path_ids, list)
            or not stage_path_ids
            or len(stage_path_ids) > 64
            or not isinstance(part_id, str)
            or not isinstance(label, str)
            or not isinstance(instruction, str)
            or not label.strip()
            or not instruction.strip()
            or any(path_id not in path_ids for path_id in stage_path_ids)
            or len(set(stage_path_ids)) != len(stage_path_ids)
            or set(assigned).intersection(stage_path_ids)
        ):
            raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_STAGE_CONTENT_INVALID")
        parts.append(
            SvgTopicStrokeGuidePartV1(
                part_id=part_id,
                label_vi=label,
                path_ids=stage_path_ids,
                depends_on=[parts[-1].part_id] if parts else [],
            )
        )
        stages.append(
            SvgTopicStrokeGuideStageV1(
                step_index=index,
                instruction_vi=instruction,
                part_ids=[part_id],
                new_path_ids=stage_path_ids,
                animation_order=stage_path_ids,
            )
        )
        assigned.extend(stage_path_ids)
        stage_labels.update({path_id: label for path_id in stage_path_ids})
    if len(assigned) != len(path_ids) or set(assigned) != set(path_ids):
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_STAGE_COVERAGE_INVALID")

    try:
        generated = SvgTopicStrokeGuideModelResultV1.model_validate(
            {
                "schema_version": "SvgTopicStrokeGuideContentV1",
                "title_vi": guide_data["title_vi"],
                "document": sanitized_guide.document,
                "parts": [part.model_dump(mode="json") for part in parts],
                "stages": [stage.model_dump(mode="json") for stage in stages],
            }
        )
        reference_illustration = _build_reference_illustration(guide_data)
    except (KeyError, TypeError, ValidationError, SvgInputRejected, ValueError) as exc:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_GUIDE_CONTRACT_INVALID") from exc

    reference_source = SvgReferenceSourceProvenanceV1(
        asset_id=asset["asset_id"],
        dataset_name=manifest["dataset_name"],
        dataset_revision=manifest["dataset_revision"],
        dataset_doi=None,
        dataset_uri=asset["color_source_uri"],
        source_sha256=asset["color_sha256"],
        license_id=manifest["license_id"],
        license_uri=manifest["license_uri"],
    )
    lineage = tuple(
        {
            "derived_path_id": path_id,
            "source_path_ids": [source_path_ids[path_id]],
            "feature_vi": stage_labels[path_id],
            "operation": "OPENCLIPART_SOURCE_CONTOUR_TO_DRAW_PATH_V1",
        }
        for path_id in assigned
    )
    return OpenclipartDerivedGuide(
        generated=generated,
        reference_source=reference_source,
        reference_illustration=reference_illustration,
        engine_id="openclipart-source-contour-guide",
        engine_revision=f"1.0.0+{manifest_sha256[:12]}",
        source_guide_uri=asset["line_source_uri"],
        source_guide_sha256=asset["line_sha256"],
        derivation_method="OPENCLIPART_SOURCE_CONTOUR_TO_DRAW_PATH_V1",
        source_path_count=len(path_ids),
        path_lineage=lineage,
    )


def _build_reference_illustration(data: dict[str, Any]) -> SvgReferenceIllustrationDocumentV1:
    paths = data.get("reference_paths")
    if not isinstance(paths, list) or not paths or len(paths) > 128:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_REFERENCE_INVENTORY_INVALID")
    root = ET.Element(
        f"{{{_SVG_NS}}}svg",
        {"viewBox": data.get("reference_view_box", "")},
    )
    for item in paths:
        if not isinstance(item, dict):
            raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_REFERENCE_PATH_INVALID")
        ET.SubElement(
            root,
            f"{{{_SVG_NS}}}path",
            {
                "id": item.get("path_id", ""),
                "d": item.get("d", ""),
                "fill": item.get("fill", "none"),
                "stroke": item.get("stroke", item.get("fill", "none")),
                "stroke-width": _format_number(item.get("stroke_width", 1.5)),
            },
        )
    sanitized = sanitize_svg_source(
        ET.tostring(root, encoding="utf-8"),
        max_path_chars=MAX_REFERENCE_PATH_CHARS,
    )
    clean = sanitized.document.get("paths")
    if not isinstance(clean, list) or len(clean) != len(paths):
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_REFERENCE_SANITIZER_MISMATCH")
    reference_paths = [
        SvgReferenceIllustrationPathV1(
            path_id=path["path_id"],
            d=path["d"],
            fill=path["fill"],
            stroke=path["stroke"],
            stroke_width=path["stroke_width"],
        )
        for path in clean
    ]
    return SvgReferenceIllustrationDocumentV1(
        view_box=sanitized.document["view_box"],
        paths=reference_paths,
    )


def _verify_source_file(asset: dict[str, Any], filename_key: str, digest_key: str) -> None:
    filename = asset.get(filename_key)
    digest = asset.get(digest_key)
    if not isinstance(filename, str) or Path(filename).name != filename or not isinstance(digest, str):
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_SOURCE_MANIFEST_INVALID")
    source = _read_bounded(_data_directory() / filename, _MAX_SOURCE_BYTES)
    if hashlib.sha256(source).hexdigest() != digest:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_SOURCE_HASH_MISMATCH")


def _data_directory() -> Path:
    return Path(__file__).resolve().parent / "data" / "openclipart"


def _load_manifest() -> tuple[dict[str, Any], str]:
    data = _read_bounded(_data_directory() / _MANIFEST_FILENAME, _MAX_MANIFEST_BYTES)
    digest = hashlib.sha256(data).hexdigest()
    if digest != _MANIFEST_SHA256:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_MANIFEST_HASH_MISMATCH")
    try:
        manifest = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_MANIFEST_INVALID") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != "OpenclipartParentGuideManifestV1"
        or manifest.get("dataset_name") != "Openclipart"
        or manifest.get("dataset_revision") != "2026-11-14-curated"
        or manifest.get("license_id") != "CC0-1.0"
        or manifest.get("license_uri") != "https://creativecommons.org/publicdomain/zero/1.0/"
        or manifest.get("license_notice_file") != "NOTICE.md"
        or not isinstance(manifest.get("assets"), list)
    ):
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_MANIFEST_INVALID")
    notice = _read_bounded(_data_directory() / manifest.get("license_notice_file", ""), _MAX_SOURCE_BYTES)
    if hashlib.sha256(notice).hexdigest() != _NOTICE_SHA256:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_NOTICE_HASH_MISMATCH")
    return manifest, digest


def _resolve_asset(manifest: dict[str, Any], topic: str) -> dict[str, Any] | None:
    normalized = _normalize_topic(topic)
    matches = []
    for asset in manifest["assets"]:
        if not isinstance(asset, dict) or not isinstance(asset.get("topic_aliases"), list):
            raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_ASSET_MANIFEST_INVALID")
        aliases = {_normalize_topic(value) for value in asset["topic_aliases"] if isinstance(value, str)}
        if normalized in aliases:
            matches.append(asset)
    if len(matches) > 1:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_TOPIC_ALIAS_AMBIGUOUS")
    return matches[0] if matches else None


def _read_bounded(path: Path, maximum: int) -> bytes:
    try:
        value = path.read_bytes()
    except OSError as exc:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_SOURCE_FILE_UNAVAILABLE") from exc
    if not value or len(value) > maximum:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_SOURCE_SIZE_INVALID")
    return value


def _format_number(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_NUMBER_INVALID") from exc
    if not (number == number and abs(number) < 10_000):
        raise OpenclipartGuideUnavailable("SVG_OPENCLIPART_NUMBER_INVALID")
    return format(number, ".6g")


def _normalize_topic(topic: str) -> str:
    folded = unicodedata.normalize("NFKD", topic.casefold())
    plain = "".join(character for character in folded if not unicodedata.combining(character))
    return " ".join(re.findall(r"[a-z0-9]+", plain))


__all__ = ["OpenclipartDerivedGuide", "OpenclipartGuideUnavailable", "build_openclipart_guide"]
