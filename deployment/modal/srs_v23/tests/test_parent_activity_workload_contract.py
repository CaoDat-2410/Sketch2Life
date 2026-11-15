"""Parent activity selection is allowed only through the L4 worker envelope."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

from contracts import WorkerContractError, parse_worker_input  # noqa: E402


def _payload() -> dict[str, object]:
    job_id = "parent-activity-job"
    generation_id = "parent-activity-generation"
    attempt_id = "parent-activity-attempt"
    return {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": "dev",
        "workload": "parent.activity.suggest",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/",
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": "a" * 64,
        "input_bytes": 1,
    }


def test_parent_activity_suggestion_is_allowed_by_l4_worker_envelope() -> None:
    parsed = parse_worker_input(_payload(), execution_group="l4")

    assert parsed.workload == "parent.activity.suggest"


def test_parent_activity_suggestion_remains_disallowed_in_video_group() -> None:
    with pytest.raises(WorkerContractError, match="MODAL_WORKLOAD_NOT_ALLOWED"):
        parse_worker_input(_payload(), execution_group="l40s-video")
