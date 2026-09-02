"""Retry policy and reviewed still+narration fallback."""

from __future__ import annotations

from .library import AssetLibrary
from .schemas import (
    AssetType,
    FallbackResult,
    LearningObjective,
    ReviewedStillNarrationAsset,
    ValidationResult,
    ValidationStatus,
)


class RetryPolicy:
    def __init__(self, max_retries: int = 1) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must not be negative")
        self.max_retries = max_retries

    def can_retry(self, validation: ValidationResult, retry_count: int) -> bool:
        return (
            validation.status is ValidationStatus.RETRY
            and retry_count < self.max_retries
        )


class StillNarrationFallback:
    def __init__(self, library: AssetLibrary) -> None:
        self._library = library

    def resolve(
        self,
        objective: LearningObjective,
        failure: ValidationResult,
    ) -> FallbackResult:
        asset = self._library.find_reviewed(objective, AssetType.STILL_NARRATION)
        if isinstance(asset, ReviewedStillNarrationAsset):
            return FallbackResult(
                status=ValidationStatus.FALLBACK,
                objective_id=objective.objective_id,
                objective_version=objective.version,
                asset=asset,
                reason_code=f"VIDEO_FAILED:{failure.reason_codes[0] if failure.reason_codes else 'UNKNOWN'}",
            )

        return FallbackResult(
            status=ValidationStatus.BLOCK,
            objective_id=objective.objective_id,
            objective_version=objective.version,
            reason_code="NO_REVIEWED_FALLBACK",
        )
