"""Cache-first learning-asset resolution."""

from __future__ import annotations

from .library import AssetLibrary
from .schemas import LearningObjective, ResolverResult, ResolverStatus


class CacheFirstResolver:
    def __init__(self, library: AssetLibrary) -> None:
        self._library = library

    def resolve(self, objective: LearningObjective) -> ResolverResult:
        asset = self._library.find_reviewed(objective)
        if asset is not None:
            return ResolverResult(
                status=ResolverStatus.HIT,
                objective_id=objective.objective_id,
                objective_version=objective.version,
                asset=asset,
                generation_required=False,
            )

        return ResolverResult(
            status=ResolverStatus.MISS,
            objective_id=objective.objective_id,
            objective_version=objective.version,
            generation_required=True,
            reason_code="NO_REVIEWED_ASSET",
        )
