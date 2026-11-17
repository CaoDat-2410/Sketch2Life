from sketch2life.application.services.learning_media_resolver import (
    InMemoryLearningMediaStore,
    LearningMediaResolver,
)
from sketch2life.contracts.schemas.learning_media import (
    LearningMediaRequestV1,
    ReviewedLearningMediaAssetV1,
)


def request(**overrides: object) -> LearningMediaRequestV1:
    values: dict[str, object] = {
        "session_id": "session-001",
        "expected_session_version": 2,
        "request_id": "request-001",
        "idempotency_key": "idem-001",
        "activity_id": "ACT-TREE-001",
        "activity_version": "v1",
        "objective_id": "OBJ-TREE-001",
        "objective_version": "v1",
        "renderer_plan_id": "reveal-v1",
        "renderer_plan_version": "v1",
        "source_session_version": 2,
        "cache_key": "tree-cache-v1",
    }
    values.update(overrides)
    return LearningMediaRequestV1(**values)


def asset(**overrides: object) -> ReviewedLearningMediaAssetV1:
    values: dict[str, object] = {
        "asset_ref": "asset/tree-learning-v1",
        "asset_sha256": "a" * 64,
        "activity_id": "ACT-TREE-001",
        "activity_version": "v1",
        "objective_id": "OBJ-TREE-001",
        "objective_version": "v1",
        "renderer_plan_id": "reveal-v1",
        "renderer_plan_version": "v1",
        "cache_key": "tree-cache-v1",
    }
    values.update(overrides)
    return ReviewedLearningMediaAssetV1(**values)


def test_exact_reviewed_asset_is_cache_hit() -> None:
    result = LearningMediaResolver(InMemoryLearningMediaStore((asset(),))).resolve(request())

    assert result.status == "READY"
    assert result.cache_status == "HIT"
    assert result.generation_called is False
    assert result.asset_ref == "asset/tree-learning-v1"


def test_unknown_key_is_typed_cache_miss_without_generation() -> None:
    result = LearningMediaResolver(InMemoryLearningMediaStore()).resolve(request())

    assert result.status == "BLOCKED"
    assert result.cache_status == "MISS"
    assert result.reason_code == "CACHE_MISS"
    assert result.generation_called is False


def test_identity_mismatch_fails_closed() -> None:
    result = LearningMediaResolver(
        InMemoryLearningMediaStore((asset(objective_id="OBJ-OTHER-001"),))
    ).resolve(request())

    assert result.status == "BLOCKED"
    assert result.reason_code == "STALE_MEDIA"
    assert result.objective_id == "OBJ-TREE-001"


def test_corrupt_or_unsafe_asset_is_rejected() -> None:
    corrupt = LearningMediaResolver(
        InMemoryLearningMediaStore((asset(media_status="CORRUPT"),))
    ).resolve(request())
    unsafe = LearningMediaResolver(
        InMemoryLearningMediaStore((asset(media_status="UNSAFE"),))
    ).resolve(request())

    assert corrupt.reason_code == "CORRUPT_MEDIA"
    assert unsafe.reason_code == "UNSAFE_MEDIA"
