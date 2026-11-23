"""Parent activity suggestions use the L4 worker envelope, not the video pool."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

from contracts import WorkerContractError, parse_worker_input  # noqa: E402


def _payload() -> dict[str, object]:
    return {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": "dev",
        "workload": "parent.activity.suggest",
        "job_id": "parent-activity-gate-job",
        "generation_id": "parent-activity-gate-generation",
        "attempt_id": "parent-activity-gate-attempt",
        "attempt_prefix": (
            "sketch2life/dev/parent-activity-gate-job/"
            "parent-activity-gate-generation/parent-activity-gate-attempt/"
        ),
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": "a" * 64,
        "input_bytes": 256,
    }


def test_parent_activity_suggestion_is_allowed_by_l4_worker_envelope() -> None:
    parsed = parse_worker_input(_payload(), execution_group="l4")

    assert parsed.workload == "parent.activity.suggest"


def test_parent_activity_suggestion_is_not_allowed_in_video_execution_group() -> None:
    with pytest.raises(WorkerContractError, match="MODAL_WORKLOAD_NOT_ALLOWED"):
        parse_worker_input(_payload(), execution_group="l40s-video")


def test_product_activity_workload_registry_remains_disabled() -> None:
    registry = json.loads((MODAL_DIR / "workloads.json").read_text(encoding="utf-8"))
    activity = next(item for item in registry["workloads"] if item["id"] == "parent.activity.suggest")

    assert activity["enabled"] is False
