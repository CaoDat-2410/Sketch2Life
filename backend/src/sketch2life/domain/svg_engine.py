"""Framework-free rules for safe SVG sources and progressive drawing guides."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

MIN_GUIDE_STAGES = 4
MAX_GUIDE_STAGES = 8
MIN_INDEPENDENT_PATHS = 4
GUIDE_SCHEMA_VERSION = "SketchStrokeGuideV3"
TOPIC_GUIDE_CONTENT_SCHEMA_VERSION = "SvgTopicStrokeGuideContentV1"
TOPIC_CONSTRUCTION_GUIDE_CONTENT_SCHEMA_VERSION = "SvgTopicStrokeGuideConstructionContentV1"
TOPIC_GUIDE_SCHEMA_VERSION = "SvgTopicStrokeGuideV1"
MAX_CONSTRUCTION_GUIDE_STROKES = 20
MAX_CONSTRUCTION_GUIDE_STROKE_CHARS = 768
MAX_CONSTRUCTION_GUIDE_TOTAL_PATH_CHARS = 16_384
_TOPIC_PATH_PATTERN = re.compile(r"[MLCQZ]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
_TOPIC_PATH_NUMBER = re.compile(r"^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?$")
_TOPIC_STROKE_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
ARCADIA_GALLUS_REFERENCE_SOURCE_V1 = {
    "asset_id": "arcadia-gallus-gallus-tricolorstroke-v1",
    "dataset_name": "Arcadia Science Free Organism Illustration Library",
    "dataset_revision": "1.0",
    "dataset_doi": "10.5281/zenodo.17203578",
    "source_sha256": "4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed",
    "license_id": "CC0-1.0",
    "license_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
}
ARCADIA_GALLUS_SUPPORTED_TOPICS = frozenset(
    {
        "ga",
        "con ga",
        "ga mai",
        "con ga mai",
        "ga trong",
        "con ga trong",
        "chicken",
        "rooster",
    }
)


def topic_uses_arcadia_gallus_reference(topic: str) -> bool:
    normalized = unicodedata.normalize("NFKD", topic.casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return normalized.strip() in ARCADIA_GALLUS_SUPPORTED_TOPICS


class SvgRuleError(ValueError):
    """A stable domain rejection code for invalid vector or guide content."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class SvgReadiness(StrEnum):
    STROKE_READY = "STROKE_READY"
    REQUIRES_MANUAL_AUTHORING = "REQUIRES_MANUAL_AUTHORING"
    STATIC_ONLY = "STATIC_ONLY"
    REJECTED = "REJECTED"


def classify_svg_source(
    *,
    drawable_path_ids: Sequence[str],
    filled_shape_count: int,
    educator_approved: bool,
    curator_grouping_allowed: bool,
) -> dict[str, Any]:
    """Return structural facts separately from human pedagogical decisions."""
    path_count = len(drawable_path_ids)
    if any(not isinstance(value, str) or not value.strip() for value in drawable_path_ids):
        raise SvgRuleError("SVG_PATH_ID_INVALID")
    if len(set(drawable_path_ids)) != path_count:
        raise SvgRuleError("SVG_PATH_ID_INVALID")
    if filled_shape_count < 0 or filled_shape_count > path_count:
        raise SvgRuleError("SVG_STRUCTURE_FACT_INVALID")

    filled_ratio = filled_shape_count / path_count if path_count else 0.0
    drawable_ratio = (path_count - filled_shape_count) / path_count if path_count else 0.0
    facts = {
        "drawable_stroke_count": path_count,
        "drawable_stroke_ratio": round(drawable_ratio, 6),
        "filled_shape_count": filled_shape_count,
        "filled_shape_ratio": round(filled_ratio, 6),
    }

    if path_count < MIN_INDEPENDENT_PATHS:
        return {
            "classification": SvgReadiness.STATIC_ONLY.value,
            "reason_codes": ["PATH_COUNT_BELOW_MIN"],
            "facts": facts,
        }

    missing_reviews: list[str] = []
    if not educator_approved:
        missing_reviews.append("EDUCATOR_REVIEW_REQUIRED")
    if not curator_grouping_allowed:
        missing_reviews.append("CURATOR_GROUPING_NOT_ENABLED")
    if missing_reviews:
        return {
            "classification": SvgReadiness.REQUIRES_MANUAL_AUTHORING.value,
            "reason_codes": missing_reviews,
            "facts": facts,
        }

    return {
        "classification": SvgReadiness.STROKE_READY.value,
        "reason_codes": [],
        "facts": facts,
    }


def validate_guide_v3(
    value: Mapping[str, Any],
    *,
    source_path_ids: Sequence[str],
    expected_source_sha256: str,
) -> dict[str, Any]:
    """Validate a path-assignment guide without accepting client geometry."""
    if value.get("schema_version") != GUIDE_SCHEMA_VERSION:
        raise SvgRuleError("SVG_GUIDE_SCHEMA_UNSUPPORTED")
    required_text = ("guide_id", "title_vi", "source_asset_ref", "source_sha256")
    if any(
        not isinstance(value.get(key), str)
        or not str(value[key]).strip()
        or len(str(value[key])) > 256
        for key in required_text
    ):
        raise SvgRuleError("SVG_GUIDE_REQUIRED_FIELD")
    if value.get("source_sha256") != expected_source_sha256:
        raise SvgRuleError("SVG_SOURCE_REVISION_MISMATCH")
    asset_version = value.get("source_asset_version")
    if isinstance(asset_version, bool) or not isinstance(asset_version, int) or asset_version < 1:
        raise SvgRuleError("SVG_GUIDE_SOURCE_VERSION_INVALID")

    parts_raw = value.get("parts")
    stages_raw = value.get("stages")
    if not isinstance(parts_raw, list) or not isinstance(stages_raw, list):
        raise SvgRuleError("SVG_GUIDE_COLLECTION_INVALID")
    if not MIN_GUIDE_STAGES <= len(stages_raw) <= MAX_GUIDE_STAGES:
        raise SvgRuleError("SVG_GUIDE_STAGE_COUNT_INVALID")

    source_ids = set(source_path_ids)
    if len(source_ids) != len(source_path_ids):
        raise SvgRuleError("SVG_SOURCE_PATH_ID_DUPLICATE")

    parts: dict[str, dict[str, Any]] = {}
    assigned_part_paths: set[str] = set()
    for part in parts_raw:
        if not isinstance(part, Mapping):
            raise SvgRuleError("SVG_GUIDE_PART_INVALID")
        part_id = part.get("part_id")
        label = part.get("label_vi")
        path_ids = part.get("path_ids")
        dependencies = part.get("depends_on", [])
        if (
            not isinstance(part_id, str)
            or not part_id.strip()
            or not isinstance(label, str)
            or not label.strip()
            or not isinstance(path_ids, list)
            or not path_ids
            or not isinstance(dependencies, list)
        ):
            raise SvgRuleError("SVG_GUIDE_PART_INVALID")
        if (
            part_id in parts
            or any(not isinstance(path_id, str) for path_id in path_ids)
            or len(set(path_ids)) != len(path_ids)
        ):
            raise SvgRuleError("SVG_GUIDE_PART_DUPLICATE")
        if any(not isinstance(path_id, str) or path_id not in source_ids for path_id in path_ids):
            raise SvgRuleError("SVG_GUIDE_UNKNOWN_PATH")
        if assigned_part_paths.intersection(path_ids):
            raise SvgRuleError("SVG_GUIDE_PATH_ASSIGNED_TWICE")
        if any(not isinstance(dep, str) or not dep.strip() for dep in dependencies):
            raise SvgRuleError("SVG_GUIDE_DEPENDENCY_INVALID")
        assigned_part_paths.update(path_ids)
        parts[part_id] = {
            "part_id": part_id,
            "label_vi": label.strip(),
            "path_ids": list(path_ids),
            "depends_on": list(dependencies),
        }

    if not parts:
        raise SvgRuleError("SVG_GUIDE_PART_REQUIRED")
    for part in parts.values():
        if any(dep not in parts or dep == part["part_id"] for dep in part["depends_on"]):
            raise SvgRuleError("SVG_GUIDE_DEPENDENCY_INVALID")
    _assert_acyclic_dependencies(parts)

    stages: list[dict[str, Any]] = []
    seen_stage_paths: set[str] = set()
    stage_part_ids: set[str] = set()
    for expected_index, stage in enumerate(stages_raw, start=1):
        if not isinstance(stage, Mapping):
            raise SvgRuleError("SVG_GUIDE_STAGE_INVALID")
        step_index = stage.get("step_index")
        instruction = stage.get("instruction_vi")
        new_path_ids = stage.get("new_path_ids")
        animation_order = stage.get("animation_order")
        part_ids = stage.get("part_ids")
        if (
            isinstance(step_index, bool)
            or step_index != expected_index
            or not isinstance(instruction, str)
            or not instruction.strip()
            or not isinstance(new_path_ids, list)
            or not new_path_ids
            or not isinstance(animation_order, list)
            or not isinstance(part_ids, list)
            or not part_ids
        ):
            raise SvgRuleError("SVG_GUIDE_STAGE_INVALID")
        if (
            any(not isinstance(path_id, str) for path_id in new_path_ids)
            or any(not isinstance(path_id, str) for path_id in animation_order)
            or any(not isinstance(part_id, str) for part_id in part_ids)
            or len(set(new_path_ids)) != len(new_path_ids)
            or set(animation_order) != set(new_path_ids)
        ):
            raise SvgRuleError("SVG_GUIDE_ANIMATION_ORDER_INVALID")
        if len(animation_order) != len(new_path_ids):
            raise SvgRuleError("SVG_GUIDE_ANIMATION_ORDER_INVALID")
        if any(path_id not in source_ids for path_id in new_path_ids):
            raise SvgRuleError("SVG_GUIDE_UNKNOWN_PATH")
        if seen_stage_paths.intersection(new_path_ids):
            raise SvgRuleError("SVG_GUIDE_PATH_ASSIGNED_TWICE")
        if any(part_id not in parts for part_id in part_ids):
            raise SvgRuleError("SVG_GUIDE_UNKNOWN_PART")
        available_paths = {
            path_id for part_id in part_ids for path_id in parts[part_id]["path_ids"]
        }
        if not set(new_path_ids).issubset(available_paths):
            raise SvgRuleError("SVG_GUIDE_PART_STAGE_MISMATCH")
        seen_stage_paths.update(new_path_ids)
        stage_part_ids.update(part_ids)
        stages.append(
            {
                "step_index": expected_index,
                "instruction_vi": instruction.strip(),
                "part_ids": list(part_ids),
                "new_path_ids": list(new_path_ids),
                "animation_order": list(animation_order),
            }
        )

    if len(seen_stage_paths) < MIN_INDEPENDENT_PATHS:
        raise SvgRuleError("SVG_GUIDE_DRAWABLE_PATH_COUNT_INVALID")
    if seen_stage_paths != assigned_part_paths:
        raise SvgRuleError("SVG_GUIDE_PATH_STAGE_COVERAGE_INVALID")
    if len(stages) > len(seen_stage_paths):
        raise SvgRuleError("SVG_GUIDE_EMPTY_STAGE")
    if stage_part_ids != set(parts):
        raise SvgRuleError("SVG_GUIDE_UNUSED_PART")

    return {
        "schema_version": GUIDE_SCHEMA_VERSION,
        "guide_id": str(value["guide_id"]).strip(),
        "title_vi": str(value["title_vi"]).strip(),
        "source_asset_ref": str(value["source_asset_ref"]).strip(),
        "source_asset_version": asset_version,
        "source_sha256": expected_source_sha256,
        "parts": list(parts.values()),
        "stages": stages,
    }


def validate_topic_stroke_guide_v1(value: Mapping[str, Any], *, topic: str) -> dict[str, Any]:
    """Validate an ephemeral, ordered topic guide and its drawable topology."""
    if value.get("schema_version") != TOPIC_GUIDE_CONTENT_SCHEMA_VERSION:
        raise SvgRuleError("SVG_TOPIC_GUIDE_SCHEMA_UNSUPPORTED")
    title = value.get("title_vi")
    document = value.get("document")
    parts_raw = value.get("parts")
    stages_raw = value.get("stages")
    if (
        not isinstance(title, str)
        or not title.strip()
        or len(title.strip()) > 120
        or not isinstance(document, Mapping)
        or document.get("schema_version") != "SvgDocumentV1"
        or document.get("view_box") != "0 0 512 512"
        or not isinstance(document.get("paths"), list)
        or not 8 <= len(document["paths"]) <= 64
        or not isinstance(parts_raw, list)
        or not isinstance(stages_raw, list)
        or not MIN_GUIDE_STAGES <= len(stages_raw) <= MAX_GUIDE_STAGES
    ):
        raise SvgRuleError("SVG_TOPIC_GUIDE_SHAPE_INVALID")

    paths: dict[str, Mapping[str, Any]] = {}
    geometry: dict[str, dict[str, Any]] = {}
    canonical_d: set[str] = set()
    color: str | None = None
    total_path_chars = 0
    for path in document["paths"]:
        if not isinstance(path, Mapping):
            raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_INVALID")
        path_id = path.get("path_id")
        data = path.get("d")
        stroke = path.get("stroke")
        width = path.get("stroke_width")
        if (
            not isinstance(path_id, str)
            or not re.fullmatch(r"[A-Za-z0-9._:-]{1,96}", path_id)
            or path_id in paths
            or not isinstance(data, str)
            or not data.strip()
            or len(data) > 4096
            or path.get("fill") != "none"
            or not isinstance(stroke, str)
            or _TOPIC_STROKE_COLOR.fullmatch(stroke) is None
            or isinstance(width, bool)
            or not isinstance(width, (int, float))
            or not 1.5 <= float(width) <= 10
        ):
            raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_INVALID")
        total_path_chars += len(data)
        if total_path_chars > 32_768 or data in canonical_d:
            raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_COMPLEXITY_INVALID")
        if color is not None and color.casefold() != stroke.casefold():
            raise SvgRuleError("SVG_TOPIC_GUIDE_STROKE_STYLE_INVALID")
        color = stroke
        points, first_point, last_point = _topic_path_geometry(data)
        if any(not (0 <= x <= 512 and 0 <= y <= 512) for x, y in points):
            raise SvgRuleError("SVG_TOPIC_GUIDE_COORDINATE_OUT_OF_BOUNDS")
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        paths[path_id] = path
        canonical_d.add(data)
        geometry[path_id] = {
            "points": points,
            "first": first_point,
            "last": last_point,
            "bbox": (min(xs), min(ys), max(xs), max(ys)),
            "commands": set(re.findall(r"[A-Za-z]", data)),
        }

    parts: dict[str, dict[str, Any]] = {}
    path_owner: dict[str, str] = {}
    for raw in parts_raw:
        if not isinstance(raw, Mapping):
            raise SvgRuleError("SVG_TOPIC_GUIDE_PART_INVALID")
        part_id = raw.get("part_id")
        label = raw.get("label_vi")
        path_ids = raw.get("path_ids")
        dependencies = raw.get("depends_on", [])
        if (
            not isinstance(part_id, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", part_id)
            or part_id in parts
            or not isinstance(label, str)
            or not label.strip()
            or len(label) > 300
            or not isinstance(path_ids, list)
            or not path_ids
            or not isinstance(dependencies, list)
            or len(set(path_ids)) != len(path_ids)
        ):
            raise SvgRuleError("SVG_TOPIC_GUIDE_PART_INVALID")
        if any(not isinstance(path_id, str) or path_id not in paths for path_id in path_ids):
            raise SvgRuleError("SVG_TOPIC_GUIDE_UNKNOWN_PATH")
        if any(path_id in path_owner for path_id in path_ids):
            raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_ASSIGNED_TWICE")
        if any(not isinstance(dep, str) or not dep.strip() for dep in dependencies):
            raise SvgRuleError("SVG_TOPIC_GUIDE_DEPENDENCY_INVALID")
        parts[part_id] = {
            "part_id": part_id,
            "label_vi": label.strip(),
            "path_ids": list(path_ids),
            "depends_on": list(dependencies),
        }
        for path_id in path_ids:
            path_owner[path_id] = part_id
    if set(path_owner) != set(paths) or not parts:
        raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_COVERAGE_INVALID")
    for part in parts.values():
        if any(dep not in parts or dep == part["part_id"] for dep in part["depends_on"]):
            raise SvgRuleError("SVG_TOPIC_GUIDE_DEPENDENCY_INVALID")
    _assert_acyclic_dependencies(parts)

    stages: list[dict[str, Any]] = []
    staged_paths: set[str] = set()
    staged_parts: set[str] = set()
    first_part_stage: dict[str, int] = {}
    for index, raw in enumerate(stages_raw, start=1):
        if not isinstance(raw, Mapping):
            raise SvgRuleError("SVG_TOPIC_GUIDE_STAGE_INVALID")
        step_index = raw.get("step_index")
        instruction = raw.get("instruction_vi")
        part_ids = raw.get("part_ids")
        new_path_ids = raw.get("new_path_ids")
        animation_order = raw.get("animation_order")
        if (
            isinstance(step_index, bool)
            or step_index != index
            or not isinstance(instruction, str)
            or not instruction.strip()
            or len(instruction.strip()) > 120
            or any(
                term in instruction.casefold() for term in ("svg", "path", "stroke", "người lớn")
            )
            or not isinstance(part_ids, list)
            or not part_ids
            or not isinstance(new_path_ids, list)
            or not new_path_ids
            or not isinstance(animation_order, list)
            or len(set(part_ids)) != len(part_ids)
            or len(set(new_path_ids)) != len(new_path_ids)
            or len(set(animation_order)) != len(animation_order)
            or animation_order != new_path_ids
        ):
            raise SvgRuleError("SVG_TOPIC_GUIDE_STAGE_INVALID")
        if any(part_id not in parts for part_id in part_ids):
            raise SvgRuleError("SVG_TOPIC_GUIDE_UNKNOWN_PART")
        if any(path_id not in paths for path_id in new_path_ids):
            raise SvgRuleError("SVG_TOPIC_GUIDE_UNKNOWN_PATH")
        if staged_paths.intersection(new_path_ids):
            raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_ASSIGNED_TWICE")
        if any(path_owner[path_id] not in part_ids for path_id in new_path_ids):
            raise SvgRuleError("SVG_TOPIC_GUIDE_PART_STAGE_MISMATCH")
        for part_id in part_ids:
            first_part_stage.setdefault(part_id, index)
        staged_paths.update(new_path_ids)
        staged_parts.update(part_ids)
        stages.append(
            {
                "step_index": index,
                "instruction_vi": instruction.strip(),
                "part_ids": list(part_ids),
                "new_path_ids": list(new_path_ids),
                "animation_order": list(animation_order),
            }
        )
    if staged_paths != set(paths) or staged_parts != set(parts):
        raise SvgRuleError("SVG_TOPIC_GUIDE_FINAL_COVERAGE_INVALID")
    for part in parts.values():
        stage = first_part_stage[part["part_id"]]
        if any(first_part_stage[dependency] > stage for dependency in part["depends_on"]):
            raise SvgRuleError("SVG_TOPIC_GUIDE_DEPENDENCY_ORDER_INVALID")

    topic_key = unicodedata.normalize("NFKD", topic.casefold())
    topic_key = "".join(char for char in topic_key if not unicodedata.combining(char))
    deer_requested = any(
        term in topic_key for term in ("huou", "nai", "deer", "fawn", "stag", "elk")
    )
    if deer_requested:
        _validate_deer_guide_topology(parts, paths, geometry)
    if topic_uses_arcadia_gallus_reference(topic):
        _validate_chicken_guide_topology(parts, geometry)

    return {
        "schema_version": TOPIC_GUIDE_SCHEMA_VERSION,
        "guide_id": str(value.get("guide_id") or "topic-draft"),
        "title_vi": title.strip(),
        "parts": list(parts.values()),
        "stages": stages,
    }


def validate_source_bound_topic_stroke_guide_v1(
    value: Mapping[str, Any], *, topic: str
) -> dict[str, Any]:
    """Validate an AI ordering over pinned source paths without rewriting their geometry."""
    if value.get("schema_version") != TOPIC_GUIDE_CONTENT_SCHEMA_VERSION:
        raise SvgRuleError("SVG_SOURCE_GUIDE_SCHEMA_UNSUPPORTED")
    title = value.get("title_vi")
    document = value.get("document")
    parts_raw = value.get("parts")
    stages_raw = value.get("stages")
    if (
        not isinstance(title, str)
        or not title.strip()
        or len(title.strip()) > 120
        or not isinstance(document, Mapping)
        or document.get("schema_version") != "SvgDocumentV1"
        or not isinstance(document.get("view_box"), str)
        or not isinstance(document.get("paths"), list)
        or not 4 <= len(document["paths"]) <= 32
        or not isinstance(parts_raw, list)
        or not isinstance(stages_raw, list)
        or not MIN_GUIDE_STAGES <= len(stages_raw) <= MAX_GUIDE_STAGES
    ):
        raise SvgRuleError("SVG_SOURCE_GUIDE_SHAPE_INVALID")

    paths: dict[str, Mapping[str, Any]] = {}
    color: str | None = None
    total_path_chars = 0
    for path in document["paths"]:
        if not isinstance(path, Mapping):
            raise SvgRuleError("SVG_SOURCE_GUIDE_PATH_INVALID")
        path_id = path.get("path_id")
        data = path.get("d")
        stroke = path.get("stroke")
        width = path.get("stroke_width")
        if (
            not isinstance(path_id, str)
            or not re.fullmatch(r"[A-Za-z0-9._:-]{1,96}", path_id)
            or path_id in paths
            or not isinstance(data, str)
            or not data.strip()
            or len(data) > 8192
            or path.get("fill") != "none"
            or not isinstance(stroke, str)
            or not re.fullmatch(r"#[0-9a-fA-F]{6}", stroke)
            or isinstance(width, bool)
            or not isinstance(width, (int, float))
            or not 1.5 <= float(width) <= 10
        ):
            raise SvgRuleError("SVG_SOURCE_GUIDE_PATH_INVALID")
        total_path_chars += len(data)
        if total_path_chars > 128 * 1024:
            raise SvgRuleError("SVG_SOURCE_GUIDE_PATH_COMPLEXITY_INVALID")
        if color is not None and color.casefold() != stroke.casefold():
            raise SvgRuleError("SVG_SOURCE_GUIDE_STROKE_STYLE_INVALID")
        color = stroke
        paths[path_id] = path

    parts: dict[str, dict[str, Any]] = {}
    path_owner: dict[str, str] = {}
    for raw in parts_raw:
        if not isinstance(raw, Mapping):
            raise SvgRuleError("SVG_SOURCE_GUIDE_PART_INVALID")
        part_id = raw.get("part_id")
        label = raw.get("label_vi")
        path_ids = raw.get("path_ids")
        dependencies = raw.get("depends_on", [])
        if (
            not isinstance(part_id, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", part_id)
            or part_id in parts
            or not isinstance(label, str)
            or not label.strip()
            or len(label) > 300
            or not isinstance(path_ids, list)
            or not path_ids
            or not isinstance(dependencies, list)
            or len(set(path_ids)) != len(path_ids)
        ):
            raise SvgRuleError("SVG_SOURCE_GUIDE_PART_INVALID")
        if any(not isinstance(path_id, str) or path_id not in paths for path_id in path_ids):
            raise SvgRuleError("SVG_SOURCE_GUIDE_UNKNOWN_PATH")
        if any(path_id in path_owner for path_id in path_ids):
            raise SvgRuleError("SVG_SOURCE_GUIDE_PATH_ASSIGNED_TWICE")
        if any(not isinstance(dep, str) or not dep.strip() for dep in dependencies):
            raise SvgRuleError("SVG_SOURCE_GUIDE_DEPENDENCY_INVALID")
        parts[part_id] = {
            "part_id": part_id,
            "label_vi": label.strip(),
            "path_ids": list(path_ids),
            "depends_on": list(dependencies),
        }
        for path_id in path_ids:
            path_owner[path_id] = part_id
    if set(path_owner) != set(paths) or len(parts) != len(stages_raw):
        raise SvgRuleError("SVG_SOURCE_GUIDE_PATH_COVERAGE_INVALID")
    for part in parts.values():
        if any(dep not in parts or dep == part["part_id"] for dep in part["depends_on"]):
            raise SvgRuleError("SVG_SOURCE_GUIDE_DEPENDENCY_INVALID")
    _assert_acyclic_dependencies(parts)

    stages: list[dict[str, Any]] = []
    staged_paths: set[str] = set()
    staged_parts: set[str] = set()
    first_part_stage: dict[str, int] = {}
    for index, raw in enumerate(stages_raw, start=1):
        if not isinstance(raw, Mapping):
            raise SvgRuleError("SVG_SOURCE_GUIDE_STAGE_INVALID")
        instruction = raw.get("instruction_vi")
        part_ids = raw.get("part_ids")
        new_path_ids = raw.get("new_path_ids")
        animation_order = raw.get("animation_order")
        if (
            isinstance(raw.get("step_index"), bool)
            or not isinstance(raw.get("step_index"), int)
            or raw.get("step_index") != index
            or not isinstance(instruction, str)
            or not instruction.strip()
            or len(instruction.strip()) > 120
            or any(
                term in instruction.casefold() for term in ("svg", "path", "stroke", "người lớn")
            )
            or not isinstance(part_ids, list)
            or len(part_ids) != 1
            or not isinstance(new_path_ids, list)
            or not new_path_ids
            or not isinstance(animation_order, list)
            or animation_order != new_path_ids
            or len(set(new_path_ids)) != len(new_path_ids)
        ):
            raise SvgRuleError("SVG_SOURCE_GUIDE_STAGE_INVALID")
        if any(part_id not in parts for part_id in part_ids):
            raise SvgRuleError("SVG_SOURCE_GUIDE_UNKNOWN_PART")
        if any(path_id not in paths for path_id in new_path_ids):
            raise SvgRuleError("SVG_SOURCE_GUIDE_UNKNOWN_PATH")
        if staged_paths.intersection(new_path_ids):
            raise SvgRuleError("SVG_SOURCE_GUIDE_PATH_ASSIGNED_TWICE")
        if any(path_owner[path_id] not in part_ids for path_id in new_path_ids):
            raise SvgRuleError("SVG_SOURCE_GUIDE_PART_STAGE_MISMATCH")
        for part_id in part_ids:
            first_part_stage.setdefault(part_id, index)
        staged_parts.update(part_ids)
        staged_paths.update(new_path_ids)
        stages.append(
            {
                "step_index": index,
                "instruction_vi": instruction.strip(),
                "part_ids": list(part_ids),
                "new_path_ids": list(new_path_ids),
                "animation_order": list(animation_order),
            }
        )
    if staged_paths != set(paths) or staged_parts != set(parts):
        raise SvgRuleError("SVG_SOURCE_GUIDE_FINAL_COVERAGE_INVALID")
    for part in parts.values():
        stage = first_part_stage[part["part_id"]]
        if any(first_part_stage[dependency] > stage for dependency in part["depends_on"]):
            raise SvgRuleError("SVG_SOURCE_GUIDE_DEPENDENCY_ORDER_INVALID")
    return {
        "schema_version": TOPIC_GUIDE_SCHEMA_VERSION,
        "guide_id": str(value.get("guide_id") or "source-topic-draft"),
        "title_vi": title.strip(),
        "parts": list(parts.values()),
        "stages": stages,
    }


def validate_construction_topic_stroke_guide_v1(
    value: Mapping[str, Any],
    *,
    topic: str,
    source_path_ids: Sequence[str],
    source_path_geometries: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate independently authored construction strokes anchored to a color source."""
    if value.get("schema_version") != TOPIC_CONSTRUCTION_GUIDE_CONTENT_SCHEMA_VERSION:
        raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_SCHEMA_UNSUPPORTED")
    title = value.get("title_vi")
    strokes_raw = value.get("strokes")
    stages_raw = value.get("stages")
    allowed_source_ids = set(source_path_ids)
    if (
        not isinstance(title, str)
        or not title.strip()
        or len(title.strip()) > 120
        or not allowed_source_ids
        or not isinstance(strokes_raw, list)
        or not 8 <= len(strokes_raw) <= MAX_CONSTRUCTION_GUIDE_STROKES
        or not isinstance(stages_raw, list)
        or not MIN_GUIDE_STAGES <= len(stages_raw) <= MAX_GUIDE_STAGES
    ):
        raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_SHAPE_INVALID")

    strokes: dict[str, dict[str, Any]] = {}
    path_data_seen: set[str] = set()
    total_path_chars = 0
    for raw in strokes_raw:
        if not isinstance(raw, Mapping) or set(raw) != {
            "path_id",
            "d",
            "role",
            "feature_vi",
            "source_path_ids",
        }:
            raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_STROKE_INVALID")
        path_id = raw.get("path_id")
        data = raw.get("d")
        role = raw.get("role")
        feature = raw.get("feature_vi")
        anchors = raw.get("source_path_ids")
        if (
            not isinstance(path_id, str)
            or re.fullmatch(r"guide_stroke_[0-9]{2}", path_id) is None
            or path_id in strokes
            or not isinstance(data, str)
            or not 1 <= len(data.strip()) <= MAX_CONSTRUCTION_GUIDE_STROKE_CHARS
            or re.fullmatch(r"[MLCQZ0-9+.,\-eE\s]+", data) is None
            or not isinstance(role, str)
            or role not in {"construction", "outline", "feature"}
            or not isinstance(feature, str)
            or not 1 <= len(feature.strip()) <= 100
            or not isinstance(anchors, list)
            or not 1 <= len(anchors) <= 6
            or any(not isinstance(anchor, str) for anchor in anchors)
            or len(set(anchors)) != len(anchors)
            or any(anchor not in allowed_source_ids for anchor in anchors)
        ):
            raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_STROKE_INVALID")
        total_path_chars += len(data)
        if (
            total_path_chars > MAX_CONSTRUCTION_GUIDE_TOTAL_PATH_CHARS
            or data.strip() in path_data_seen
        ):
            raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID")
        if source_path_geometries and any(
            data.strip() == source_path_geometries.get(anchor, "") for anchor in anchors
        ):
            raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_SOURCE_GEOMETRY_COPIED")
        command_count = len(re.findall(r"[MLCQZ]", data))
        if not 2 <= command_count <= 24:
            raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_STROKE_COMPLEXITY_INVALID")
        points, _first, _last = _topic_path_geometry(data)
        if any(not (16 <= x <= 496 and 16 <= y <= 496) for x, y in points):
            raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_COORDINATE_OUT_OF_BOUNDS")
        path_data_seen.add(data.strip())
        strokes[path_id] = {
            "path_id": path_id,
            "d": data.strip(),
            "role": role,
            "feature_vi": feature.strip(),
            "source_path_ids": list(anchors),
        }

    stages: list[dict[str, Any]] = []
    assigned_path_ids: set[str] = set()
    part_path_owner: dict[str, str] = {}
    parts: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    for index, raw in enumerate(stages_raw, start=1):
        if not isinstance(raw, Mapping) or set(raw) != {
            "step_index",
            "label_vi",
            "instruction_vi",
            "stroke_ids",
        }:
            raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_STAGE_INVALID")
        step_index = raw.get("step_index")
        label = raw.get("label_vi")
        instruction = raw.get("instruction_vi")
        stroke_ids = raw.get("stroke_ids")
        if (
            isinstance(step_index, bool)
            or not isinstance(step_index, int)
            or step_index != index
            or not isinstance(label, str)
            or not 1 <= len(label.strip()) <= 60
            or not isinstance(instruction, str)
            or not 1 <= len(instruction.strip()) <= 120
            or any(
                term in instruction.casefold()
                for term in ("svg", "path", "stroke", "silhouette", "người lớn")
            )
            or not isinstance(stroke_ids, list)
            or not stroke_ids
            or any(not isinstance(stroke_id, str) for stroke_id in stroke_ids)
            or len(stroke_ids) != len(set(stroke_ids))
            or any(stroke_id not in strokes for stroke_id in stroke_ids)
            or assigned_path_ids.intersection(stroke_ids)
        ):
            raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_STAGE_INVALID")
        if index == 1:
            if len(stroke_ids) > 3 or any(
                strokes[stroke_id]["role"] != "construction" for stroke_id in stroke_ids
            ):
                raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_FIRST_STEP_NOT_CONSTRUCTION")
            if any(
                len(re.findall(r"[MLCQZ]", strokes[stroke_id]["d"])) > 8 for stroke_id in stroke_ids
            ):
                raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_FIRST_STEP_TOO_COMPLEX")
        part_id = f"step_{index:02d}"
        parts.append(
            {
                "part_id": part_id,
                "label_vi": label.strip(),
                "path_ids": list(stroke_ids),
                "depends_on": [f"step_{index - 1:02d}"] if index > 1 else [],
            }
        )
        for stroke_id in stroke_ids:
            part_path_owner[stroke_id] = part_id
            stroke = strokes[stroke_id]
            lineage.append(
                {
                    "derived_path_id": stroke_id,
                    "source_path_ids": stroke["source_path_ids"],
                    "feature_vi": stroke["feature_vi"],
                    "role": stroke["role"],
                }
            )
        assigned_path_ids.update(stroke_ids)
        stages.append(
            {
                "step_index": index,
                "instruction_vi": instruction.strip(),
                "part_ids": [part_id],
                "new_path_ids": list(stroke_ids),
                "animation_order": list(stroke_ids),
            }
        )

    if assigned_path_ids != set(strokes):
        raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_PATH_COVERAGE_INVALID")
    if not any(strokes[stroke_id]["role"] == "feature" for stroke_id in stages[-1]["new_path_ids"]):
        raise SvgRuleError("SVG_CONSTRUCTION_GUIDE_FINAL_FEATURE_MISSING")

    document = {
        "schema_version": "SvgDocumentV1",
        "view_box": "0 0 512 512",
        "paths": [
            {
                "path_id": stroke["path_id"],
                "d": stroke["d"],
                "fill": "none",
                "stroke": "#202938",
                "stroke_width": 6,
            }
            for stroke in strokes.values()
        ],
    }
    return {
        "schema_version": TOPIC_GUIDE_SCHEMA_VERSION,
        "guide_id": "construction-topic-draft",
        "title_vi": title.strip(),
        "document": document,
        "parts": parts,
        "stages": stages,
        "path_lineage": lineage,
    }


def _topic_path_geometry(
    data: str,
) -> tuple[list[tuple[float, float]], tuple[float, float], tuple[float, float]]:
    if any(char not in "MLCQZmlcqz0123456789+-.eE, \t\r\n" for char in data):
        raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_COMMAND_UNSUPPORTED")
    tokens = _TOPIC_PATH_PATTERN.findall(data)
    if not tokens or "".join(tokens).replace(",", "") != re.sub(r"[\s,]+", "", data):
        raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_SYNTAX_INVALID")
    points: list[tuple[float, float]] = []
    command: str | None = None
    current = (0.0, 0.0)
    subpath_start = (0.0, 0.0)
    i = 0
    first: tuple[float, float] | None = None
    while i < len(tokens):
        if not _TOPIC_PATH_NUMBER.fullmatch(tokens[i]):
            command = tokens[i]
            i += 1
            if command in "Zz":
                current = subpath_start
                points.append(current)
                command = None
                continue
            if command not in {"M", "L", "C", "Q"}:
                raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_COMMAND_UNSUPPORTED")
        if command is None:
            raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_SYNTAX_INVALID")
        count = {"M": 2, "L": 2, "C": 6, "Q": 4}[command]
        if i + count > len(tokens) or any(
            not _TOPIC_PATH_NUMBER.fullmatch(token) for token in tokens[i : i + count]
        ):
            raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_SYNTAX_INVALID")
        values = [float(token) for token in tokens[i : i + count]]
        if command in {"M", "L"}:
            end = (values[0], values[1])
            segment_points = [end]
        elif command == "C":
            end = (values[4], values[5])
            segment_points = [(values[offset], values[offset + 1]) for offset in range(0, 6, 2)]
        else:
            end = (values[2], values[3])
            segment_points = [(values[offset], values[offset + 1]) for offset in range(0, 4, 2)]
        if command == "M":
            subpath_start = end
        if first is None:
            first = end
        points.extend(segment_points)
        current = end
        i += count
        if command == "M":
            command = "L"
    if first is None or len(points) < 2:
        raise SvgRuleError("SVG_TOPIC_GUIDE_PATH_EMPTY")
    return points, first, current


def _validate_deer_guide_topology(
    parts: Mapping[str, Mapping[str, Any]],
    paths: Mapping[str, Mapping[str, Any]],
    geometry: Mapping[str, Mapping[str, Any]],
) -> None:
    required_parts = {
        "body",
        "neck",
        "head",
        "front_left_leg",
        "front_right_leg",
        "rear_left_leg",
        "rear_right_leg",
        "left_antler",
        "right_antler",
    }
    if not required_parts.issubset(parts):
        raise SvgRuleError("SVG_DEER_ANATOMY_PARTS_MISSING")

    def single_path(part_id: str, expected_id: str) -> str:
        path_ids = parts[part_id]["path_ids"]
        if len(path_ids) != 1 or path_ids[0] != expected_id:
            raise SvgRuleError("SVG_DEER_ANATOMY_PATH_MAPPING_INVALID")
        return expected_id

    body_id = single_path("body", "deer_body")
    neck_id = single_path("neck", "deer_neck")
    head_id = single_path("head", "deer_head")
    body_box = geometry[body_id]["bbox"]
    neck_box = geometry[neck_id]["bbox"]
    head_box = geometry[head_id]["bbox"]
    body_width = body_box[2] - body_box[0]
    body_height = body_box[3] - body_box[1]
    if body_width < body_height * 1.25 or not _boxes_overlap(body_box, neck_box, 24):
        raise SvgRuleError("SVG_DEER_BODY_NECK_DISCONNECTED")
    if neck_box[1] >= body_box[1] or not _boxes_overlap(neck_box, head_box, 24):
        raise SvgRuleError("SVG_DEER_NECK_HEAD_DISCONNECTED")

    ground_ys: list[float] = []
    for part_id in ("front_left_leg", "front_right_leg", "rear_left_leg", "rear_right_leg"):
        path_id = single_path(part_id, f"deer_{part_id}")
        first = geometry[path_id]["first"]
        last = geometry[path_id]["last"]
        if not _point_in_box(first, body_box, 24) or first[1] < body_box[1] + body_height * 0.45:
            raise SvgRuleError("SVG_DEER_LEG_BODY_DISCONNECTED")
        if last[1] <= first[1] + 30 or last[1] < 400:
            raise SvgRuleError("SVG_DEER_LEG_NOT_GROUNDED")
        ground_ys.append(last[1])
    if max(ground_ys) - min(ground_ys) > 56:
        raise SvgRuleError("SVG_DEER_LEG_GROUND_ALIGNMENT_INVALID")

    for side in ("left", "right"):
        part_id = f"{side}_antler"
        prefix = f"deer_antler_{side}_"
        path_ids = parts[part_id]["path_ids"]
        beam_ids = [path_id for path_id in path_ids if path_id == f"{prefix}beam"]
        branch_ids = [
            path_id for path_id in path_ids if re.fullmatch(prefix + r"branch_[1-9][0-9]*", path_id)
        ]
        if len(beam_ids) != 1 or len(branch_ids) < 2 or len(path_ids) != 1 + len(branch_ids):
            raise SvgRuleError("SVG_DEER_ANTLER_BRANCHES_MISSING")
        beam_id = beam_ids[0]
        beam = geometry[beam_id]
        if not beam["commands"].issubset({"M", "L", "Z"}) or len(beam["points"]) < 3:
            raise SvgRuleError("SVG_DEER_ANTLER_BEAM_INVALID")
        if not _point_in_box(beam["first"], head_box, 28):
            raise SvgRuleError("SVG_DEER_ANTLER_HEAD_DISCONNECTED")
        for branch_id in branch_ids:
            branch = geometry[branch_id]
            if branch["commands"] != {"M", "L"} or len(branch["points"]) != 2:
                raise SvgRuleError("SVG_DEER_ANTLER_BRANCH_INVALID")
            if (
                min(
                    _distance_to_polyline(point, beam["points"])
                    for point in (branch["first"], branch["last"])
                )
                > 16
            ):
                raise SvgRuleError("SVG_DEER_ANTLER_BRANCH_DISCONNECTED")


def _validate_chicken_guide_topology(
    parts: Mapping[str, Mapping[str, Any]],
    geometry: Mapping[str, Mapping[str, Any]],
) -> None:
    """Require connected, recognizable chicken anatomy for the pinned SVG source."""
    path_by_part = {
        "body": "chicken_body",
        "neck": "chicken_neck",
        "head": "chicken_head",
        "beak": "chicken_beak",
        "comb": "chicken_comb",
        "wing": "chicken_wing",
        "tail": "chicken_tail",
        "left_leg": "chicken_left_leg",
        "right_leg": "chicken_right_leg",
    }
    if not set(path_by_part).issubset(parts):
        raise SvgRuleError("SVG_CHICKEN_ANATOMY_PARTS_MISSING")
    for part_id, path_id in path_by_part.items():
        if (
            parts[part_id]["path_ids"] != [path_id]
            or path_id not in geometry
            or "Z" in geometry[path_id]["commands"]
        ):
            raise SvgRuleError("SVG_CHICKEN_ANATOMY_PATH_MAPPING_INVALID")

    expected_dependencies = {
        "body": {"head"},
        "neck": {"body", "head"},
        "head": set(),
        "beak": {"head"},
        "comb": {"head"},
        "wing": {"body"},
        "tail": {"body"},
        "left_leg": {"body"},
        "right_leg": {"body"},
    }
    if any(
        not dependencies.issubset(parts[part_id]["depends_on"])
        for part_id, dependencies in expected_dependencies.items()
    ):
        raise SvgRuleError("SVG_CHICKEN_ANATOMY_DEPENDENCY_INVALID")

    boxes = {part_id: geometry[path_id]["bbox"] for part_id, path_id in path_by_part.items()}
    body_box = boxes["body"]
    neck_box = boxes["neck"]
    head_box = boxes["head"]
    body_width = body_box[2] - body_box[0]
    body_height = body_box[3] - body_box[1]
    if body_width < 120 or body_height < 56 or body_width < body_height * 1.2:
        raise SvgRuleError("SVG_CHICKEN_BODY_SHAPE_INVALID")

    if (
        not _boxes_overlap(body_box, neck_box, 24)
        or not _boxes_overlap(neck_box, head_box, 24)
        or not _boxes_overlap(body_box, boxes["wing"], 16)
        or not _boxes_overlap(body_box, boxes["tail"], 20)
        or not _boxes_overlap(head_box, boxes["comb"], 18)
    ):
        raise SvgRuleError("SVG_CHICKEN_ANATOMY_CONNECTION_INVALID")

    def endpoint_touches(
        path_id: str,
        target_box: tuple[float, float, float, float],
        margin: float,
    ) -> bool:
        candidate = geometry[path_id]
        return _point_in_box(candidate["first"], target_box, margin) or _point_in_box(
            candidate["last"], target_box, margin
        )

    if (
        not _point_in_box(geometry[path_by_part["neck"]]["first"], body_box, 24)
        or not _point_in_box(geometry[path_by_part["neck"]]["last"], head_box, 24)
        or not endpoint_touches(path_by_part["wing"], body_box, 16)
        or not endpoint_touches(path_by_part["tail"], body_box, 20)
        or not endpoint_touches(path_by_part["comb"], head_box, 18)
    ):
        raise SvgRuleError("SVG_CHICKEN_ANATOMY_ENDPOINT_DISCONNECTED")

    beak = geometry[path_by_part["beak"]]
    if (
        not _point_in_box(beak["first"], head_box, 20)
        or math.dist(beak["first"], beak["last"]) < 12
    ):
        raise SvgRuleError("SVG_CHICKEN_BEAK_CONNECTION_INVALID")

    ground_points: list[tuple[float, float]] = []
    for part_id in ("left_leg", "right_leg"):
        leg = geometry[path_by_part[part_id]]
        if (
            not _point_in_box(leg["first"], body_box, 24)
            or leg["last"][1] < 400
            or leg["last"][1] <= leg["first"][1] + 40
        ):
            raise SvgRuleError("SVG_CHICKEN_LEG_NOT_GROUNDED")
        ground_points.append(leg["last"])
    if (
        abs(ground_points[0][1] - ground_points[1][1]) > 56
        or abs(ground_points[0][0] - ground_points[1][0]) < 18
    ):
        raise SvgRuleError("SVG_CHICKEN_LEG_GROUND_ALIGNMENT_INVALID")


def _boxes_overlap(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
    tolerance: float,
) -> bool:
    return not (
        first[2] + tolerance < second[0]
        or second[2] + tolerance < first[0]
        or first[3] + tolerance < second[1]
        or second[3] + tolerance < first[1]
    )


def _point_in_box(
    point: tuple[float, float], box: tuple[float, float, float, float], margin: float
) -> bool:
    return (
        box[0] - margin <= point[0] <= box[2] + margin
        and box[1] - margin <= point[1] <= box[3] + margin
    )


def _distance_to_polyline(point: tuple[float, float], line: Sequence[tuple[float, float]]) -> float:
    if len(line) == 1:
        return math.dist(point, line[0])
    minimum = float("inf")
    for start, end in zip(line, line[1:], strict=False):
        dx, dy = end[0] - start[0], end[1] - start[1]
        length_squared = dx * dx + dy * dy
        if length_squared == 0:
            distance = math.dist(point, start)
        else:
            ratio = max(
                0.0,
                min(
                    1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_squared
                ),
            )
            closest = (start[0] + ratio * dx, start[1] + ratio * dy)
            distance = math.dist(point, closest)
        minimum = min(minimum, distance)
    return minimum


def _assert_acyclic_dependencies(parts: Mapping[str, Mapping[str, Any]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(part_id: str) -> None:
        if part_id in visiting:
            raise SvgRuleError("SVG_GUIDE_DEPENDENCY_CYCLE")
        if part_id in visited:
            return
        visiting.add(part_id)
        for dependency in parts[part_id]["depends_on"]:
            visit(dependency)
        visiting.remove(part_id)
        visited.add(part_id)

    for identifier in parts:
        visit(identifier)


__all__ = [
    "GUIDE_SCHEMA_VERSION",
    "MAX_GUIDE_STAGES",
    "MIN_GUIDE_STAGES",
    "MIN_INDEPENDENT_PATHS",
    "SvgReadiness",
    "SvgRuleError",
    "classify_svg_source",
    "validate_guide_v3",
    "validate_topic_stroke_guide_v1",
]
