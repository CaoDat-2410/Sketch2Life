"""Safe, identity-preserving fallback chain for Person 4 learning media."""

from __future__ import annotations

from dataclasses import dataclass

from sketch2life.contracts.schemas.learning_media import (
    LearningMediaProvenanceV1,
    LearningMediaRequestV1,
    LearningMediaResultV1,
)


@dataclass(frozen=True)
class ApprovedStillNarration:
    asset_ref: str
    asset_sha256: str


class LearningMediaFallback:
    """Select an approved fallback without calling a provider or changing identity."""

    def __init__(self, still_narration: ApprovedStillNarration | None = None) -> None:
        self._still_narration = still_narration

    def resolve(self, request: LearningMediaRequestV1, reason_code: str) -> LearningMediaResultV1:
        if self._still_narration is not None:
            return self._result(
                request,
                reason_code,
                fallback_type="STILL_NARRATION",
                asset_ref=self._still_narration.asset_ref,
                provenance=LearningMediaProvenanceV1(
                    source="reviewed_cache",
                    asset_ref=self._still_narration.asset_ref,
                    asset_sha256=self._still_narration.asset_sha256,
                    review_status="REVIEWED",
                ),
            )

        return self._result(
            request,
            reason_code,
            fallback_type="WHOLE_IMAGE_REVEAL",
            provenance=LearningMediaProvenanceV1(
                source="renderer_fallback",
                review_status="NOT_APPLICABLE",
            ),
        )

    @staticmethod
    def handoff(request: LearningMediaRequestV1, reason_code: str) -> LearningMediaResultV1:
        return LearningMediaFallback._result(
            request,
            reason_code,
            fallback_type="SUPERVISED_HANDOFF",
            provenance=LearningMediaProvenanceV1(
                source="renderer_fallback",
                review_status="NOT_APPLICABLE",
            ),
        )

    @staticmethod
    def _result(
        request: LearningMediaRequestV1,
        reason_code: str,
        *,
        fallback_type: str,
        provenance: LearningMediaProvenanceV1,
        asset_ref: str | None = None,
    ) -> LearningMediaResultV1:
        return LearningMediaResultV1(
            status="FALLBACK",
            cache_status="MISS",
            activity_id=request.activity_id,
            activity_version=request.activity_version,
            objective_id=request.objective_id,
            objective_version=request.objective_version,
            renderer_plan_id=request.renderer_plan_id,
            renderer_plan_version=request.renderer_plan_version,
            asset_ref=asset_ref,
            fallback_type=fallback_type,
            generation_called=False,
            provenance=provenance,
            reason_code=reason_code,
        )
