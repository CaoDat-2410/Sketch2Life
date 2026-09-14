"""Standalone cache-first resolver for the FEAT-018 Person 4 boundary."""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.learning_media import (
    LearningMediaProvenanceV1,
    LearningMediaRequestV1,
    LearningMediaResultV1,
    ReviewedLearningMediaAssetV1,
)


class LearningMediaStore(Protocol):
    def get(self, cache_key: str) -> ReviewedLearningMediaAssetV1 | None:
        """Return the reviewed asset for an exact cache key."""


class InMemoryLearningMediaStore:
    """Deterministic fixture store; no database, cloud storage, or provider."""

    def __init__(self, assets: tuple[ReviewedLearningMediaAssetV1, ...] = ()) -> None:
        self._assets = {asset.cache_key: asset for asset in assets}

    def get(self, cache_key: str) -> ReviewedLearningMediaAssetV1 | None:
        return self._assets.get(cache_key)

    def put(self, asset: ReviewedLearningMediaAssetV1) -> None:
        self._assets[asset.cache_key] = asset


class LearningMediaResolver:
    def __init__(self, store: LearningMediaStore) -> None:
        self._store = store

    def resolve(self, request: LearningMediaRequestV1) -> LearningMediaResultV1:
        asset = self._store.get(request.cache_key)
        if asset is None:
            return self._failure(request, "CACHE_MISS")

        if not self._identity_matches(request, asset):
            return self._failure(request, "STALE_MEDIA")
        if asset.media_status != "AVAILABLE":
            reason = {
                "STALE": "STALE_MEDIA",
                "CORRUPT": "CORRUPT_MEDIA",
                "UNSAFE": "UNSAFE_MEDIA",
            }[asset.media_status]
            return self._failure(request, reason)

        return LearningMediaResultV1(
            status="READY",
            cache_status="HIT",
            activity_id=request.activity_id,
            activity_version=request.activity_version,
            objective_id=request.objective_id,
            objective_version=request.objective_version,
            renderer_plan_id=request.renderer_plan_id,
            renderer_plan_version=request.renderer_plan_version,
            asset_ref=asset.asset_ref,
            generation_called=False,
            provenance=LearningMediaProvenanceV1(
                source="reviewed_cache",
                asset_ref=asset.asset_ref,
                asset_sha256=asset.asset_sha256,
                review_status="REVIEWED",
            ),
        )

    @staticmethod
    def _identity_matches(
        request: LearningMediaRequestV1,
        asset: ReviewedLearningMediaAssetV1,
    ) -> bool:
        return (
            request.activity_id == asset.activity_id
            and request.activity_version == asset.activity_version
            and request.objective_id == asset.objective_id
            and request.objective_version == asset.objective_version
            and request.renderer_plan_id == asset.renderer_plan_id
            and request.renderer_plan_version == asset.renderer_plan_version
        )

    @staticmethod
    def _failure(request: LearningMediaRequestV1, reason: str) -> LearningMediaResultV1:
        return LearningMediaResultV1(
            status="BLOCKED",
            cache_status="MISS",
            activity_id=request.activity_id,
            activity_version=request.activity_version,
            objective_id=request.objective_id,
            objective_version=request.objective_version,
            renderer_plan_id=request.renderer_plan_id,
            renderer_plan_version=request.renderer_plan_version,
            generation_called=False,
            provenance=LearningMediaProvenanceV1(
                source="synthetic_fixture",
                review_status="NOT_APPLICABLE",
            ),
            reason_code=reason,
        )
