"""Fixture-local reviewed learning-asset library."""

from __future__ import annotations

import json
from pathlib import Path

from .schemas import LearningExplanationAsset, LearningObjective, ReviewedAsset


class AssetLibrary:
    """Loads reviewed asset metadata and performs deterministic lookups.

    File existence is intentionally checked by the media-validation phase. The
    library only owns metadata eligibility, which keeps cache resolution usable
    with metadata-only fixtures and with a later object-storage adapter.
    """

    def __init__(self, assets: list[LearningExplanationAsset]) -> None:
        self._assets = tuple(assets)

    @classmethod
    def from_directory(cls, directory: Path) -> AssetLibrary:
        assets: list[LearningExplanationAsset] = []
        for path in sorted(directory.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            assets.append(ReviewedAsset.model_validate(payload).asset)
        return cls(assets)

    @property
    def assets(self) -> tuple[LearningExplanationAsset, ...]:
        return self._assets

    def find_reviewed(self, objective: LearningObjective) -> LearningExplanationAsset | None:
        for asset in self._assets:
            if (
                asset.objective_id == objective.objective_id
                and asset.objective_version == objective.version
                and asset.locale == objective.locale
                and asset.age_band == objective.age_band
            ):
                return asset
        return None
