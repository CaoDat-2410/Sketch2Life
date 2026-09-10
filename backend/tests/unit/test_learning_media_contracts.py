import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.learning_media import (
    LearningMediaProvenanceV1,
    LearningMediaRequestV1,
    LearningMediaResultV1,
)


def request() -> LearningMediaRequestV1:
    return LearningMediaRequestV1(
        session_id="session-001",
        expected_session_version=2,
        request_id="request-001",
        idempotency_key="idem-001",
        activity_id="ACT-TREE-001",
        activity_version="v1",
        objective_id="OBJ-TREE-001",
        objective_version="v1",
        renderer_plan_id="reveal-v1",
        renderer_plan_version="v1",
        source_session_version=2,
        cache_key="ACT-TREE-001:v1|OBJ-TREE-001:v1|reveal-v1:v1",
    )


def reviewed_provenance() -> LearningMediaProvenanceV1:
    return LearningMediaProvenanceV1(
        source="reviewed_cache",
        asset_ref="asset/tree-learning-v1",
        asset_sha256="a" * 64,
        review_status="REVIEWED",
    )


def result(**overrides: object) -> LearningMediaResultV1:
    values: dict[str, object] = {
        "status": "READY",
        "cache_status": "HIT",
        "activity_id": "ACT-TREE-001",
        "activity_version": "v1",
        "objective_id": "OBJ-TREE-001",
        "objective_version": "v1",
        "renderer_plan_id": "reveal-v1",
        "renderer_plan_version": "v1",
        "asset_ref": "asset/tree-learning-v1",
        "generation_called": False,
        "provenance": reviewed_provenance(),
    }
    values.update(overrides)
    return LearningMediaResultV1(**values)


def test_request_contains_transport_and_exact_identity() -> None:
    payload = request().model_dump(mode="json")

    assert payload["contract_name"] == "LearningMediaRequestV1"
    assert payload["contract_version"] == "1.0"
    assert payload["activity_id"] == "ACT-TREE-001"
    assert payload["renderer_plan_version"] == "v1"


def test_reviewed_cache_hit_is_ready_without_generation() -> None:
    media = result()

    assert media.status == "READY"
    assert media.cache_status == "HIT"
    assert media.generation_called is False


def test_fallback_requires_typed_reason_and_preserves_identity() -> None:
    media = result(
        status="FALLBACK",
        cache_status="MISS",
        asset_ref="asset/tree-still-narration-v1",
        fallback_type="STILL_NARRATION",
        generation_called=False,
        provenance=LearningMediaProvenanceV1(
            source="synthetic_fixture",
            review_status="NOT_APPLICABLE",
        ),
        reason_code="MEDIA_UNAVAILABLE",
    )

    assert media.activity_id == "ACT-TREE-001"
    assert media.objective_id == "OBJ-TREE-001"
    assert media.reason_code == "MEDIA_UNAVAILABLE"


def test_cache_hit_cannot_be_fallback() -> None:
    with pytest.raises(ValidationError):
        result(status="FALLBACK", reason_code="MEDIA_UNAVAILABLE")


def test_ready_media_requires_asset() -> None:
    with pytest.raises(ValidationError):
        result(asset_ref=None)


def test_reviewed_cache_requires_hash_and_review_status() -> None:
    with pytest.raises(ValidationError):
        LearningMediaProvenanceV1(
            source="reviewed_cache",
            asset_ref="asset/tree-learning-v1",
            review_status="REVIEWED",
        )
