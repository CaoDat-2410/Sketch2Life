"""Static PixiJS asset selection adapter for FEAT-020.

This adapter only reads committed JSON/SVG metadata. It never creates, downloads or
mutates an asset. PixiJS itself is deliberately not imported here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sketch2life.contracts.schemas.workflow_demo import PixiAssetSelectionV1


class AssetCatalogError(ValueError):
    """Raised when a static asset catalog or selection contract is invalid."""


class PixiAssetCatalog:
    def __init__(self, feature_root: Path) -> None:
        pixi_root = feature_root / "assets" / "generated" / "pixi"
        self._pixi_root = pixi_root
        self._catalog = _read_object(pixi_root / "ASSET_CATALOG.json")
        self._selection = _read_object(pixi_root / "WORKFLOW_ASSET_SELECTION.json")
        self._age_intents = _read_object(pixi_root / "AGE_BAND_RENDER_INTENTS.json")
        self._assets = {
            str(item["assetId"]): item
            for item in _require_list(self._catalog, "assets")
            if isinstance(item, dict) and isinstance(item.get("assetId"), str)
        }
        if len(self._assets) != len(_require_list(self._catalog, "assets")):
            raise AssetCatalogError("asset catalog contains duplicate or invalid asset IDs")
        if self._catalog.get("runtimePolicy") != "STATIC_LOCAL_NO_RUNTIME_GENERATION":
            raise AssetCatalogError("asset catalog does not declare static-only runtime policy")
        if self._catalog.get("preserveOriginalChildArt") is not True:
            raise AssetCatalogError("asset catalog must preserve original child art")

    @property
    def version(self) -> str:
        value = self._catalog.get("catalogVersion")
        if not isinstance(value, str) or not value:
            raise AssetCatalogError("asset catalog version is missing")
        return value

    @property
    def status(self) -> str:
        value = self._catalog.get("status")
        if value not in {"GENERATED_PENDING_REVIEW", "APPROVED", "APPLIED"}:
            raise AssetCatalogError("asset catalog status is invalid")
        return str(value)

    def resolve(self, age_band: str) -> PixiAssetSelectionV1:
        intents = self._age_intents.get("ageBands")
        if not isinstance(intents, dict) or not isinstance(intents.get(age_band), dict):
            raise AssetCatalogError(f"missing age-band render intent: {age_band}")
        age_intent = intents[age_band]
        selected: list[str] = []
        for stage in ("ART_PLAN_READY", "HANDOFF_READY", "FEEDBACK_RECORDED"):
            stage_contract = self._selection.get("selection", {}).get(stage)
            if not isinstance(stage_contract, dict):
                raise AssetCatalogError(f"missing asset selection stage: {stage}")
            for asset_id in (
                *_strings(stage_contract.get("required")),
                *_strings(stage_contract.get("optional")),
            ):
                if asset_id != "original-child-art" and asset_id not in selected:
                    selected.append(asset_id)
        for asset_id in _strings(age_intent.get("assetIds")):
            if asset_id not in selected:
                selected.append(asset_id)
        missing = tuple(asset_id for asset_id in selected if asset_id not in self._assets)
        if missing:
            raise AssetCatalogError("ASSET_CATALOG_MISS:" + ",".join(missing))
        motion_kinds = _strings(age_intent.get("motionKinds"))
        return PixiAssetSelectionV1(
            catalog_version=self.version,
            catalog_status=self.status,  # type: ignore[arg-type]
            asset_ids=tuple(selected),
            render_intents=motion_kinds,
        )

    def validate_all_age_bands(self) -> None:
        for age_band in ("0-3", "3-6", "6-9", "9-12"):
            self.resolve(age_band)


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetCatalogError(f"cannot read asset contract: {path.name}") from exc
    if not isinstance(value, dict):
        raise AssetCatalogError(f"asset contract must be an object: {path.name}")
    return value


def _require_list(value: dict[str, Any], key: str) -> list[Any]:
    items = value.get(key)
    if not isinstance(items, list):
        raise AssetCatalogError(f"asset contract field is not an array: {key}")
    return items


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


__all__ = ["AssetCatalogError", "PixiAssetCatalog"]
