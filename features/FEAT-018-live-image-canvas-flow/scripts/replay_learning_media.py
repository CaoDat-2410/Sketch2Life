#!/usr/bin/env python3
"""Replay the synthetic Person 4 cache/fallback scenarios."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend/src"))

from sketch2life.application.services.learning_media_fallback import (  # noqa: E402
    ApprovedStillNarration,
    LearningMediaFallback,
)
from sketch2life.application.services.learning_media_resolver import (  # noqa: E402
    InMemoryLearningMediaStore,
    LearningMediaResolver,
)
from sketch2life.contracts.schemas.learning_media import (  # noqa: E402
    LearningMediaRequestV1,
    ReviewedLearningMediaAssetV1,
)

SCENARIO_PATH = REPO_ROOT / "features/FEAT-018-live-image-canvas-flow/fixtures/cache_fallback_scenarios.json"


def make_request() -> LearningMediaRequestV1:
    return LearningMediaRequestV1(
        session_id="session-synthetic-001",
        expected_session_version=2,
        request_id="request-synthetic-001",
        idempotency_key="idem-synthetic-001",
        activity_id="ACT-TREE-001",
        activity_version="v1",
        objective_id="OBJ-TREE-001",
        objective_version="v1",
        renderer_plan_id="reveal-v1",
        renderer_plan_version="v1",
        source_session_version=2,
        cache_key="tree-cache-v1",
    )


def make_asset(**overrides: object) -> ReviewedLearningMediaAssetV1:
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


def replay() -> list[dict[str, object]]:
    request = make_request()
    still = ApprovedStillNarration("asset/tree-still-v1", "b" * 64)
    rows: list[dict[str, object]] = []
    for scenario in json.loads(SCENARIO_PATH.read_text(encoding="utf-8")):
        status = scenario["asset_status"]
        if status is None:
            store = InMemoryLearningMediaStore()
        elif status == "IDENTITY_MISMATCH":
            store = InMemoryLearningMediaStore((make_asset(objective_id="OBJ-OTHER-001"),))
        else:
            store = InMemoryLearningMediaStore((make_asset(media_status=status),))

        primary = LearningMediaResolver(store).resolve(request)
        fallback = None
        if primary.status == "BLOCKED":
            fallback = LearningMediaFallback(still).resolve(request, primary.reason_code or "UNKNOWN")
        rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "resolver_status": primary.status,
                "cache_status": primary.cache_status,
                "fallback_type": fallback.fallback_type if fallback else None,
                "reason_code": primary.reason_code,
                "generation_called": primary.generation_called,
                "identity_preserved": (
                    primary.activity_id == request.activity_id
                    and primary.objective_id == request.objective_id
                    and primary.renderer_plan_id == request.renderer_plan_id
                ),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional sanitized JSON evidence path")
    args = parser.parse_args()
    report = {"report_type": "P4_REPLAY_SANITIZED", "scenarios": replay()}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
