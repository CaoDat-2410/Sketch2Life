"""File-backed workflow metadata adapter.

This adapter owns the remaining catalog-file details needed by the workflow
handoff. The application service sees only ``ActivityCatalogMetadataPort``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sketch2life.contracts.schemas.activity_preparation import ActivityPreparationProfileV1
from sketch2life.contracts.schemas.semantic_personalization_v2 import ActivityDurationV2
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
        self._material_labels = self._load_material_labels()

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

    def material_labels_for_ids(self, material_ids: tuple[str, ...]) -> dict[str, str]:
        return {
            material_id: self._material_labels.get(
                material_id, _MATERIAL_LABELS_VI.get(material_id, "Vật liệu phù hợp")
            )
            for material_id in material_ids
        }

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

    def recommendation_display(
        self, activity_id: str, activity_version: int = 1
    ) -> dict[str, Any] | None:
        variant = self._curated_by_id.get(activity_id)
        if variant is not None and variant.activity_version == activity_version:
            material_labels = tuple(
                self._material_labels.get(
                    material_id, _MATERIAL_LABELS_VI.get(material_id, "Vật liệu quen thuộc")
                )
                for material_id in variant.material_option_ids
            )
            supervision = _supervision_label(variant.minimum_supervision)
            minimum, maximum = variant.age_months
            preparation = self._preparation_catalog.profile_for(
                activity_id, variant.activity_version
            )
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

        record = self._records_by_id.get(activity_id)
        if record is None or record.get("version") != activity_version:
            return None
        title = record.get("title")
        title_vi = title.get("vi-VN") if isinstance(title, dict) else None
        age = record.get("age_months")
        safety = record.get("safety")
        duration = record.get("duration_minutes")
        if not isinstance(title_vi, str) or not isinstance(age, dict):
            return None
        if not isinstance(safety, dict):
            return None
        try:
            minimum_age = int(age["min"])
            maximum_age = int(age["max"])
            duration_minutes = (
                int(duration["min"]) if isinstance(duration, dict) else int(duration)
            )
        except (KeyError, TypeError, ValueError):
            return None
        if minimum_age < 0 or maximum_age < minimum_age or duration_minutes < 1:
            return None
        supervision = _supervision_label(safety.get("minimum_supervision"))
        if supervision is None:
            return None
        material_labels = tuple(
            self._material_labels.get(
                material_id, _MATERIAL_LABELS_VI.get(material_id, "Vật liệu quen thuộc")
            )
            for material_id in self.primary_material_ids(activity_id)
            if material_id in self._material_labels
        )
        purpose = record.get("purpose_vi") or record.get("direct_aim_vi")
        summary = purpose if isinstance(purpose, str) else "Hoạt động theo chủ đề đã xác nhận."
        try:
            preparation = self._preparation_catalog.profile_for(activity_id, activity_version)
        except ActivityPreparationCatalogError:
            preparation_fields: dict[str, Any] = {
                "preparation_requirement": "PRINT_RECOMMENDED",
                "preparation_summary_vi": (
                    "Chưa có hồ sơ chuẩn bị được duyệt cho phiên bản này; "
                    "người lớn cần kiểm tra lại vật liệu và hướng dẫn trước khi bắt đầu."
                ),
                "preparation_asset_kinds": (),
                "preparation_asset_status": "BLOCKED",
            }
        else:
            preparation_fields = {
                "preparation_requirement": preparation.print_requirement,
                "preparation_summary_vi": preparation.guide_note_vi,
                "preparation_asset_kinds": preparation.planned_asset_kinds,
                "preparation_asset_status": preparation.asset_set_status,
            }
        return {
            "title_vi": title_vi,
            "summary_vi": summary,
            "duration_minutes": duration_minutes,
            "age_label_vi": f"{minimum_age // 12}–{(maximum_age + 1) // 12} tuổi",
            "supervision_label_vi": supervision,
            "material_labels_vi": material_labels[:4],
            **preparation_fields,
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

    def _load_material_labels(self) -> dict[str, str]:
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
        return {
            item["id"]: item["label_vi"]
            for item in document.get("options", [])
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and isinstance(item.get("label_vi"), str)
        }


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


def _supervision_label(value: object) -> str | None:
    return {
        "NONE": "Trẻ có thể tự làm khi đã sẵn sàng",
        "NEARBY": "Người lớn ở gần hỗ trợ",
        "DIRECT": "Người lớn cùng thực hiện",
    }.get(value)
