import json
from pathlib import Path

from sketch2life.application.services.learning_media_resolver import (
    InMemoryLearningMediaStore,
    LearningMediaResolver,
)
from sketch2life.contracts.schemas.learning_media import (
    LearningMediaRequestV1,
    ReviewedLearningMediaAssetV1,
)


SCENARIOS = Path(__file__).parents[3] / "features/FEAT-018-live-image-canvas-flow/fixtures/cache_fallback_scenarios.json"


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


def test_scenario_matrix_matches_resolver_policy() -> None:
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))

    for scenario in scenarios:
        status = scenario["asset_status"]
        if status is None:
            store = InMemoryLearningMediaStore()
        elif status == "IDENTITY_MISMATCH":
            store = InMemoryLearningMediaStore((asset(objective_id="OBJ-OTHER-001"),))
        else:
            store = InMemoryLearningMediaStore((asset(media_status=status),))

        result = LearningMediaResolver(store).resolve(request())

        assert result.status == scenario["expected_status"], scenario["scenario_id"]
        assert result.cache_status == scenario["expected_cache_status"], scenario["scenario_id"]
        assert result.reason_code == scenario["expected_reason"], scenario["scenario_id"]
        assert result.generation_called is False
