"""Loader and coverage validation for activity preparation profiles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from sketch2life.contracts.schemas.activity_preparation import (
    ActivityPreparationCatalogV1,
    ActivityPreparationProfileV1,
)
from sketch2life.infrastructure.catalog.curated_catalog import load_curated_catalog_v2


class ActivityPreparationCatalogError(ValueError):
    """Raised when the preparation manifest is incomplete or unsafe."""


@dataclass(frozen=True, slots=True)
class ActivityPreparationCatalog:
    document: ActivityPreparationCatalogV1
    catalog_source: str

    @property
    def profiles(self) -> tuple[ActivityPreparationProfileV1, ...]:
        return self.document.profiles

    @property
    def by_activity_ref(self) -> dict[tuple[str, int], ActivityPreparationProfileV1]:
        return {
            (profile.activity_ref.id, profile.activity_ref.version): profile
            for profile in self.profiles
        }

    def profile_for(
        self, activity_id: str, activity_version: int = 1
    ) -> ActivityPreparationProfileV1:
        try:
            return self.by_activity_ref[(activity_id, activity_version)]
        except KeyError as exc:
            raise ActivityPreparationCatalogError(
                f"preparation profile missing: {activity_id} v{activity_version}"
            ) from exc

    def validate_complete(self, expected_refs: set[tuple[str, int]]) -> None:
        actual_refs = set(self.by_activity_ref)
        missing = sorted(expected_refs - actual_refs)
        unexpected = sorted(actual_refs - expected_refs)
        if missing or unexpected:
            details: list[str] = []
            if missing:
                details.append(f"missing={missing[:5]}")
            if unexpected:
                details.append(f"unexpected={unexpected[:5]}")
            raise ActivityPreparationCatalogError(
                "preparation catalog coverage mismatch: " + "; ".join(details)
            )


def load_activity_preparation_catalog(
    root: Path,
    *,
    path: Path | None = None,
    validate_active_catalog: bool = True,
) -> ActivityPreparationCatalog:
    manifest_path = path or (
        root
        / "data"
        / "activity-catalog"
        / "curated"
        / "v2"
        / "activity-preparation-profiles.v1.json"
    )
    manifest_path = manifest_path.resolve()
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        document = ActivityPreparationCatalogV1.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise ActivityPreparationCatalogError(
            f"cannot load activity preparation catalog: {manifest_path.name}"
        ) from exc

    catalog = ActivityPreparationCatalog(
        document=document,
        catalog_source=str(manifest_path.relative_to(root.resolve())),
    )
    if validate_active_catalog:
        try:
            curated = load_curated_catalog_v2(root)
            expected_refs = {
                (item.activity_id, item.activity_version) for item in curated.variants
            }
            mvp_path = root / "data" / "activity-catalog" / "mvp" / "activities.v1.json"
            mvp_document = json.loads(mvp_path.read_text(encoding="utf-8"))
            expected_refs.update(
                (str(item["id"]), int(item["version"]))
                for item in mvp_document.get("activities", [])
                if isinstance(item, dict) and "id" in item and "version" in item
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ActivityPreparationCatalogError(
                "cannot resolve active activity catalog coverage"
            ) from exc
        catalog.validate_complete(expected_refs)
    return catalog


__all__ = [
    "ActivityPreparationCatalog",
    "ActivityPreparationCatalogError",
    "load_activity_preparation_catalog",
]
