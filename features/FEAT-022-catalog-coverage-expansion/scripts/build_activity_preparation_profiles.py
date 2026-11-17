"""Build the deterministic preparation classification for all active activities.

This script is intentionally conservative and explainable.  It reads authored
catalog records only; it never calls an AI provider and never creates printable
artwork.  Run from the repository root with the project's Python interpreter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


REVISION = "catalog-2026-09-expansion-1"
CLASSIFICATION_VERSION = "1"
MANIFEST_NAME = "activity-preparation-profiles.v1.json"
REPORT_NAME = "ACTIVITY_PREPARATION_CLASSIFICATION_20260923.json"

REQUIRED_MATERIAL_KINDS: dict[str, str] = {
    "MAT_MATCHING_CARDS": "MATCHING_CARD_SET",
    "MAT_SEQUENCE_CARDS": "SEQUENCE_CARD_SET",
    "MAT_PATTERN_CARDS": "OTHER_REVIEWED_PRINTABLE",
    "MAT_NUMBER_CARDS": "PICTURE_CARD_SET",
    "MAT_CHART_CARDS": "WORKSHEET",
    "MAT_EMOTION_CARDS": "PICTURE_CARD_SET",
    "MAT_LANGUAGE_CARDS": "PICTURE_CARD_SET",
    "MAT_RHYTHM_CARDS": "PICTURE_CARD_SET",
    "MAT_SHAPE_CARDS": "PICTURE_CARD_SET",
    "MAT_POSITION_CARDS": "PICTURE_CARD_SET",
    "MAT_SKY_CARDS": "PICTURE_CARD_SET",
    "MAT_WEATHER_CARDS": "PICTURE_CARD_SET",
    "MAT_VEHICLE_CARDS": "PICTURE_CARD_SET",
}

REQUIRED_ID_MARKERS: tuple[tuple[str, str], ...] = (
    ("MATCHING", "MATCHING_CARD_SET"),
    ("SEQUENCE", "SEQUENCE_CARD_SET"),
    ("TIMELINE", "SEQUENCE_CARD_SET"),
    ("EVENT_CARDS", "SEQUENCE_CARD_SET"),
    ("LABEL", "LABEL_SET"),
    ("CHART", "WORKSHEET"),
    ("SHEET", "WORKSHEET"),
    ("TEMPLATE", "WORKSHEET"),
    ("BOARD", "SORTING_BOARD"),
    ("CARDS", "PICTURE_CARD_SET"),
    ("MAP", "REFERENCE_SHEET"),
    ("JOURNAL", "OBSERVATION_RECORD_SHEET"),
    ("NOTEBOOK", "OBSERVATION_RECORD_SHEET"),
    ("GRAPH_PAPER", "WORKSHEET"),
    ("GRID_PAPER", "WORKSHEET"),
)

PRINTABLE_TEXT_MARKERS = (
    "thẻ",
    "phiếu",
    "nhãn",
    "bảng",
    "bản đồ",
    "lưới",
    "biểu đồ",
    "dòng thời gian",
    "mẫu ghi",
    "sơ đồ",
)
CORE_OPERATION_MARKERS = (
    "ghép",
    "xếp",
    "sắp",
    "phân loại",
    "điền",
    "ghi lại",
    "ghi hai",
    "đánh dấu",
    "nối",
    "đặt thẻ",
    "chọn thẻ",
    "dùng thẻ",
)
OPTIONAL_PRINT_MARKERS = (
    "nhật ký",
    "sổ tay",
    "quan sát",
    "ghi nhận",
    "bản đồ",
    "dòng thời gian",
    "lưới",
    "biểu đồ",
    "phiếu",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalise(value: object) -> str:
    return str(value or "").casefold().replace("đ", "d")


def _material_ids(raw: dict[str, Any]) -> tuple[str, ...]:
    if "material_option_ids" in raw:
        values = raw.get("material_option_ids", [])
        return tuple(str(value) for value in values if isinstance(value, str))
    result: list[str] = []
    for group in raw.get("material_groups", []):
        if not isinstance(group, dict):
            continue
        result.extend(
            str(value)
            for value in group.get("any_of", [])
            if isinstance(value, str) and not value.endswith("_APPROVED_SUBSTITUTE")
        )
    return tuple(dict.fromkeys(result))


def _collect_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    curated_dir = root / "data" / "activity-catalog" / "curated" / "v2"
    for path in sorted(curated_dir.glob("activity-families.v2.part*.json")):
        document = _read_json(path)
        for family in document.get("families", []):
            if not isinstance(family, dict):
                continue
            for variant in family.get("variants", []):
                if not isinstance(variant, dict):
                    continue
                records.append(
                    {
                        "id": variant["activity_id"],
                        "version": 1,
                        "title_vi": variant["title_vi"],
                        "age_band": variant["age_band"],
                        "family_id": family["family_id"],
                        "materials": tuple(family.get("material_option_ids", [])),
                        "text": " ".join(
                            str(variant.get(key, ""))
                            for key in ("title_vi", "action_vi", "challenge_vi")
                        ),
                        "source": "curated/v2",
                    }
                )
    mvp = _read_json(root / "data" / "activity-catalog" / "mvp" / "activities.v1.json")
    for activity in mvp.get("activities", []):
        if not isinstance(activity, dict):
            continue
        title = activity.get("title", {}).get("vi-VN", activity.get("slug", ""))
        steps = " ".join(
            str(step) for step in activity.get("steps_vi", []) if isinstance(step, str)
        )
        labels = " ".join(
            str(group.get("label_vi", ""))
            for group in activity.get("material_groups", [])
            if isinstance(group, dict)
        )
        records.append(
            {
                "id": activity["id"],
                "version": int(activity.get("version", 1)),
                "title_vi": title,
                "age_band": activity.get("age_band", ""),
                "family_id": activity.get("slug", "MVP"),
                "materials": _material_ids(activity),
                "text": f"{title} {labels} {steps}",
                "source": "mvp/v1",
            }
        )
    return sorted(records, key=lambda item: (item["id"], item["version"]))


def _kind_from_material(material_id: str) -> str | None:
    material_id = material_id.upper()
    if material_id.endswith("_APPROVED_SUBSTITUTE"):
        material_id = material_id.removesuffix("_APPROVED_SUBSTITUTE")
    if material_id in REQUIRED_MATERIAL_KINDS:
        return REQUIRED_MATERIAL_KINDS[material_id]
    for marker, kind in REQUIRED_ID_MARKERS:
        if marker in material_id:
            return kind
    return None


def _ordered_kinds(record: dict[str, Any]) -> tuple[str, ...]:
    text = _normalise(record["text"])
    kinds: list[str] = []
    for material_id in record["materials"]:
        kind = _kind_from_material(material_id)
        if kind and kind not in kinds:
            kinds.append(kind)
    if "ghép" in text and any(token in text for token in ("thẻ", "hình", "tranh")):
        if "MATCHING_CARD_SET" not in kinds:
            kinds.insert(0, "MATCHING_CARD_SET")
    if any(token in text for token in ("phiếu quan sát", "phiếu ghi", "sổ tay", "nhật ký", "ghi dữ liệu")):
        if "OBSERVATION_RECORD_SHEET" not in kinds:
            kinds.append("OBSERVATION_RECORD_SHEET")
    if any(token in text for token in ("bảng quyết định", "bảng phân loại", "khóa phân loại")):
        if "SORTING_BOARD" not in kinds:
            kinds.append("SORTING_BOARD")
    if not kinds and any(token in text for token in ("bản đồ", "tham chiếu", "tờ hướng dẫn")):
        kinds.append("REFERENCE_SHEET")
    return tuple(kinds[:4])


def _classify(record: dict[str, Any]) -> tuple[str, tuple[str, ...], str, str]:
    text = _normalise(record["text"])
    kinds = _ordered_kinds(record)
    explicit_core = any(marker in text for marker in CORE_OPERATION_MARKERS)
    explicit_print = any(marker in text for marker in PRINTABLE_TEXT_MARKERS)
    fixed_material = any(_kind_from_material(material_id) for material_id in record["materials"])
    card_material = any(
        _kind_from_material(material_id) in {"PICTURE_CARD_SET", "MATCHING_CARD_SET", "SEQUENCE_CARD_SET"}
        for material_id in record["materials"]
    )
    if kinds and (explicit_core or any(kind != "PICTURE_CARD_SET" for kind in kinds) or not card_material):
        requirement = "PRINT_REQUIRED"
    elif card_material or explicit_print or any(marker in text for marker in OPTIONAL_PRINT_MARKERS):
        requirement = "PRINT_RECOMMENDED"
    else:
        requirement = "NO_PRINTABLE_ASSET"

    if requirement == "NO_PRINTABLE_ASSET":
        kinds = ()
        note = "Không cần in; chuẩn bị vật liệu thật hoặc vật liệu thay thế theo hướng dẫn."
        status = "NOT_APPLICABLE"
    elif requirement == "PRINT_REQUIRED":
        if not kinds:
            kinds = ("OTHER_REVIEWED_PRINTABLE",)
        note = _note_for(kinds, required=True)
        status = "PLANNED"
    else:
        if not kinds:
            kinds = ("REFERENCE_SHEET",)
        note = _note_for(kinds, required=False)
        status = "PLANNED"
    return requirement, kinds, note, status


def _note_for(kinds: tuple[str, ...], *, required: bool) -> str:
    prefix = "Cần in" if required else "Có thể in"
    labels = {
        "MATCHING_CARD_SET": "bộ thẻ ghép",
        "SEQUENCE_CARD_SET": "bộ thẻ trình tự",
        "PICTURE_CARD_SET": "bộ thẻ hình",
        "SORTING_BOARD": "bảng phân loại",
        "WORKSHEET": "phiếu hoạt động",
        "LABEL_SET": "bộ nhãn",
        "OBSERVATION_RECORD_SHEET": "phiếu quan sát",
        "REFERENCE_SHEET": "tờ tham chiếu",
        "OTHER_REVIEWED_PRINTABLE": "tài liệu in hỗ trợ",
    }
    joined = " và ".join(dict.fromkeys(labels[kind] for kind in kinds))
    suffix = " trước khi bắt đầu hoạt động." if required else " để hoạt động dễ chuẩn bị và tự kiểm tra hơn."
    return f"{prefix} {joined}{suffix}"


def _profile(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    requirement, kinds, note, status = _classify(record)
    printable = requirement != "NO_PRINTABLE_ASSET"
    profile: dict[str, Any] = {
        "contract_name": "ActivityPreparationProfileV1",
        "contract_version": "1.0",
        "activity_ref": {"id": record["id"], "version": record["version"]},
        "catalog_revision": REVISION,
        "print_requirement": requirement,
        "guide_note_vi": note,
        "planned_asset_kinds": list(kinds),
        "asset_set_status": status,
        "asset_set_refs": [],
        "print_defaults": (
            {
                "paper_size": "A4",
                "preferred_format": "PDF",
                "editable_source_formats": ["SVG", "PNG"],
                "color_mode": "COLOR",
                "copies": 1,
                "cut_required": any(kind.endswith("CARD_SET") or kind in {"LABEL_SET", "SORTING_BOARD"} for kind in kinds),
                "lamination": "OPTIONAL",
            }
            if printable
            else None
        ),
        "provenance": {
            "source": "AUTHORED_CATALOG",
            "review_status": "PENDING_OWNER_REVIEW",
            "classification_version": CLASSIFICATION_VERSION,
        },
    }
    matrix_row = {
        "activity_id": record["id"],
        "activity_version": record["version"],
        "title_vi": record["title_vi"],
        "family_id": record["family_id"],
        "age_band": record["age_band"],
        "source": record["source"],
        "material_option_ids": list(record["materials"]),
        "classification": requirement,
        "planned_asset_kinds": list(kinds),
        "classification_basis": {
            "authored_material_signal": bool(record["materials"]),
            "explicit_printable_text": any(marker in _normalise(record["text"]) for marker in PRINTABLE_TEXT_MARKERS),
            "core_print_operation": any(marker in _normalise(record["text"]) for marker in CORE_OPERATION_MARKERS),
            "note_vi": note,
        },
    }
    return profile, matrix_row


def build(root: Path, manifest_path: Path, report_path: Path) -> dict[str, Any]:
    records = _collect_records(root)
    if len(records) != 300:
        raise ValueError(f"expected 300 active activities, found {len(records)}")
    refs = [(record["id"], record["version"]) for record in records]
    if len(refs) != len(set(refs)):
        raise ValueError("active catalog contains duplicate activity refs")
    profiles: list[dict[str, Any]] = []
    matrix: list[dict[str, Any]] = []
    for record in records:
        profile, row = _profile(record)
        profiles.append(profile)
        matrix.append(row)
    manifest = {
        "contract_name": "ActivityPreparationCatalogV1",
        "contract_version": "1.0",
        "catalog_revision": REVISION,
        "profiles": profiles,
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    counts = Counter(row["classification"] for row in matrix)
    report = {
        "report_name": "ActivityPreparationClassificationV1",
        "report_version": "1.0",
        "catalog_revision": REVISION,
        "classification_version": CLASSIFICATION_VERSION,
        "activity_count": len(matrix),
        "counts": {key: counts.get(key, 0) for key in ("PRINT_REQUIRED", "PRINT_RECOMMENDED", "NO_PRINTABLE_ASSET")},
        "manifest_sha256": hashlib.sha256(manifest_text.encode("utf-8")).hexdigest(),
        "matrix": matrix,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    report = build(
        root,
        args.manifest or root / "data" / "activity-catalog" / "curated" / "v2" / MANIFEST_NAME,
        args.report
        or root
        / "features"
        / "FEAT-022-catalog-coverage-expansion"
        / "evidence"
        / "metrics"
        / REPORT_NAME,
    )
    print(json.dumps({"activity_count": report["activity_count"], "counts": report["counts"], "manifest_sha256": report["manifest_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
