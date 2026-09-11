from sketch2life.application.services.learning_media_fallback import (
    ApprovedStillNarration,
    LearningMediaFallback,
)
from sketch2life.contracts.schemas.learning_media import LearningMediaRequestV1


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
        cache_key="tree-cache-v1",
    )


def test_approved_still_narration_is_first_fallback() -> None:
    result = LearningMediaFallback(
        ApprovedStillNarration("asset/tree-still-v1", "b" * 64)
    ).resolve(request(), "MEDIA_UNAVAILABLE")

    assert result.status == "FALLBACK"
    assert result.fallback_type == "STILL_NARRATION"
    assert result.asset_ref == "asset/tree-still-v1"
    assert result.generation_called is False


def test_missing_still_uses_whole_image_reveal() -> None:
    result = LearningMediaFallback().resolve(request(), "PROVIDER_TIMEOUT")

    assert result.fallback_type == "WHOLE_IMAGE_REVEAL"
    assert result.asset_ref is None


def test_handoff_keeps_exact_identity() -> None:
    result = LearningMediaFallback.handoff(request(), "RENDERER_FAILURE")

    assert result.fallback_type == "SUPERVISED_HANDOFF"
    assert result.activity_id == "ACT-TREE-001"
    assert result.objective_id == "OBJ-TREE-001"
    assert result.renderer_plan_id == "reveal-v1"
    assert result.generation_called is False
