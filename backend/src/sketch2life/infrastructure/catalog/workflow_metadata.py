"""File-backed workflow metadata adapter.

This adapter owns the remaining catalog-file details needed by the workflow
handoff. The application service sees only ``ActivityCatalogMetadataPort``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sketch2life.contracts.schemas.semantic_personalization_v2 import ActivityDurationV2
from sketch2life.contracts.schemas.activity_preparation import ActivityPreparationProfileV1
from sketch2life.infrastructure.catalog.activity_preparation import (
    ActivityPreparationCatalogError,
    load_activity_preparation_catalog,
)
from sketch2life.infrastructure.catalog.curated_catalog import load_curated_catalog_v2


class WorkflowMetadataLoadError(ValueError):
    """Raised when workflow catalog metadata cannot be loaded safely."""


class FileWorkflowCatalogMetadata:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._records_by_id = self._load_records()
        try:
            self._curated_by_id = load_curated_catalog_v2(self._root).by_activity_id()
        except (OSError, ValueError) as exc:
            raise WorkflowMetadataLoadError("cannot load curated workflow metadata") from exc
        try:
            self._preparation_catalog = load_activity_preparation_catalog(self._root)
        except ActivityPreparationCatalogError as exc:
            raise WorkflowMetadataLoadError(
                "cannot load activity preparation metadata"
            ) from exc
        self._primary_materials = self._load_primary_materials()

    def primary_material_ids(self, activity_id: str) -> tuple[str, ...]:
        primary = self._primary_materials.get(activity_id)
        if primary:
            return primary
        record = self._records_by_id.get(activity_id)
        if isinstance(record, dict):
            values = tuple(
                option
                for group in record.get("material_groups", [])
                if isinstance(group, dict)
                for option in group.get("any_of", [])[:1]
                if isinstance(option, str)
            )
            if values:
                return values
        variant = self._curated_by_id.get(activity_id)
        return tuple(variant.material_option_ids) if variant is not None else ()

    def duration_spec(self, activity_id: str) -> dict[str, Any] | None:
        record = self._records_by_id.get(activity_id)
        if isinstance(record, dict):
            value = record.get("duration_minutes")
            if isinstance(value, int):
                return ActivityDurationV2(
                    duration_type="SINGLE_SESSION",
                    min_minutes=value,
                    max_minutes=value,
                ).model_dump(mode="json")
            if isinstance(value, dict):
                try:
                    minimum = int(value["min"])
                    maximum = int(value["max"])
                except (KeyError, TypeError, ValueError):
                    minimum = maximum = -1
                if 0 <= minimum <= maximum:
                    return ActivityDurationV2(
                        duration_type="SINGLE_SESSION",
                        min_minutes=minimum,
                        max_minutes=maximum,
                    ).model_dump(mode="json")
        variant = self._curated_by_id.get(activity_id)
        if variant is None:
            return None
        if variant.duration_type == "MULTI_DAY":
            return ActivityDurationV2(
                duration_type="MULTI_DAY",
                initial_session_minutes=variant.initial_session_minutes,
                daily_observation_minutes=variant.daily_observation_minutes,
                min_days=variant.min_days,
                max_days=variant.max_days,
            ).model_dump(mode="json")
        return ActivityDurationV2(
            duration_type="SINGLE_SESSION",
            min_minutes=variant.duration_minutes,
            max_minutes=variant.duration_minutes,
        ).model_dump(mode="json")

    def recommendation_display(self, activity_id: str) -> dict[str, Any] | None:
        variant = self._curated_by_id.get(activity_id)
        if variant is None:
            return None
        material_labels = tuple(
            _MATERIAL_LABELS_VI.get(material_id, "Vật liệu quen thuộc")
            for material_id in variant.material_option_ids
        )
        supervision = {
            "NONE": "Trẻ có thể tự làm khi đã sẵn sàng",
            "NEARBY": "Người lớn ở gần hỗ trợ",
            "DIRECT": "Người lớn cùng thực hiện",
        }[variant.minimum_supervision]
        minimum, maximum = variant.age_months
        preparation = self._preparation_catalog.profile_for(activity_id, variant.activity_version)
        return {
            "title_vi": variant.title_vi,
            "summary_vi": variant.action_vi,
            "duration_minutes": variant.duration_minutes,
            "age_label_vi": f"{minimum // 12}–{(maximum + 1) // 12} tuổi",
            "supervision_label_vi": supervision,
            "material_labels_vi": material_labels[:4],
            "preparation_requirement": preparation.print_requirement,
            "preparation_summary_vi": preparation.guide_note_vi,
            "preparation_asset_kinds": preparation.planned_asset_kinds,
            "preparation_asset_status": preparation.asset_set_status,
        }

    def preparation_profile(
        self, activity_id: str, activity_version: int = 1
    ) -> ActivityPreparationProfileV1:
        return self._preparation_catalog.profile_for(activity_id, activity_version)

    def _load_records(self) -> dict[str, dict[str, Any]]:
        records: dict[str, dict[str, Any]] = {}
        paths = (
            self._root / "data" / "activity-catalog" / "golden" / "v1" / "activities.v2.json",
            self._root / "data" / "activity-catalog" / "mvp" / "activities.v1.json",
        )
        for path in paths:
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise WorkflowMetadataLoadError(
                    f"cannot read workflow catalog: {path.name}"
                ) from exc
            for record in document.get("activities", []):
                if isinstance(record, dict) and isinstance(record.get("id"), str):
                    records.setdefault(record["id"], record)
        if not records:
            raise WorkflowMetadataLoadError("workflow catalog contains no activity records")
        return records

    def _load_primary_materials(self) -> dict[str, tuple[str, ...]]:
        path = (
            self._root
            / "data"
            / "activity-catalog"
            / "golden"
            / "v1"
            / "material-registry.v1.json"
        )
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkflowMetadataLoadError("cannot read material registry") from exc
        option_kinds = {
            item["id"]: item.get("kind")
            for item in document.get("options", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        result: dict[str, tuple[str, ...]] = {}
        for group in document.get("groups", []):
            if not isinstance(group, dict) or not isinstance(group.get("activity_id"), str):
                continue
            values = tuple(
                option_id
                for option_id in group.get("any_of", [])
                if isinstance(option_id, str) and option_kinds.get(option_id) == "PRIMARY"
            )
            if values:
                result[group["activity_id"]] = (*result.get(group["activity_id"], ()), *values)
        return result


__all__ = ["FileWorkflowCatalogMetadata", "WorkflowMetadataLoadError"]


_MATERIAL_LABELS_VI: dict[str, str] = {
    "MAT_NATURE_OBJECTS": "Vật mẫu thiên nhiên an toàn",
    "MAT_PICTURE_CARDS": "Thẻ hình",
    "MAT_SORTING_TRAY": "Khay phân loại",
    "MAT_MOVEMENT_MARKERS": "Dấu mốc vận động",
    "MAT_CARE_TRAY": "Khay chăm sóc",
    "MAT_PAPER_CRAYON": "Giấy và bút màu",
    "MAT_PLANT_TRAY": "Khay quan sát cây",
    "MAT_SEQUENCE_CARDS": "Thẻ trình tự",
    "MAT_FLOOR_TAPE": "Băng dán sàn",
}
