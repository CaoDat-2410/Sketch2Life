from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = ROOT / "data" / "activity-catalog" / "golden" / "v1"
BASE_DIR = ROOT / "data" / "activity-catalog" / "mvp"


class CatalogError(ValueError):
    """Raised when committed Golden artifacts are unavailable or inconsistent."""


@dataclass(frozen=True)
class GoldenCatalog:
    records: dict[str, dict[str, Any]]
    material_doc: dict[str, Any]
    known_activity_ids: set[str]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(
            f"cannot load committed catalog artifact: {path.name}"
        ) from exc


def load_catalog(root: Path = ROOT) -> GoldenCatalog:
    golden_dir = root / "data" / "activity-catalog" / "golden" / "v1"
    base_dir = root / "data" / "activity-catalog" / "mvp"
    activity_doc = _read_json(golden_dir / "activities.v2.json")
    material_doc = _read_json(golden_dir / "material-registry.v1.json")
    base_doc = _read_json(base_dir / "activities.v1.json")
    if activity_doc.get("schema_version") != 2:
        raise CatalogError("Golden activity schema version must be 2")
    records_list = activity_doc.get("activities", [])
    records = {item.get("id"): item for item in records_list}
    if len(records_list) != 20 or len(records) != 20 or None in records:
        raise CatalogError("Golden catalog must contain 20 unique activity IDs")
    if any(
        item.get("version") != 2
        or item.get("review", {}).get("status") != "PROVISIONAL_OWNER_REVIEWED"
        or item.get("review", {}).get("production_eligible") is not False
        for item in records.values()
    ):
        raise CatalogError("Golden review/version/non-production guard is invalid")
    groups = material_doc.get("groups", [])
    options = material_doc.get("options", [])
    if len(groups) != 20 or len(options) != 40:
        raise CatalogError("Golden material registry must contain 20 groups/40 options")
    known_activity_ids = {item.get("id") for item in base_doc.get("activities", [])}
    if None in known_activity_ids or len(known_activity_ids) != 100:
        raise CatalogError("FEAT-002 baseline activity identities are invalid")
    return GoldenCatalog(records, material_doc, known_activity_ids)


def list_activity_summaries(catalog: GoldenCatalog) -> list[dict[str, Any]]:
    groups = {item["id"]: item for item in catalog.material_doc["groups"]}
    options = {item["id"]: item for item in catalog.material_doc["options"]}
    summaries: list[dict[str, Any]] = []
    for activity_id in sorted(catalog.records):
        activity = catalog.records[activity_id]
        material_ids = [
            option_id
            for group_id in activity["material_group_ids"]
            for option_id in groups[group_id]["any_of"]
        ]
        summaries.append(
            {
                "activity_ref": {"id": activity_id, "version": 2},
                "title_vi": activity["title"]["vi-VN"],
                "age_months": activity["age_months"],
                "minimum_supervision": activity["safety"]["minimum_supervision"],
                "readiness_ids": [
                    item["id"] for item in activity["readiness_criteria"]
                ],
                "material_options": [
                    {
                        "id": option_id,
                        "kind": options[option_id]["kind"],
                        "label_vi": options[option_id]["label_vi"],
                    }
                    for option_id in material_ids
                ],
                "review_status": activity["review"]["status"],
                "production_eligible": False,
            }
        )
    return summaries
