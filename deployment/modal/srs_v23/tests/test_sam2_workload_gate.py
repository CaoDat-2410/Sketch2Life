"""The optional SAM2 worker is envelope-allowlisted without enabling product dispatch."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

from contracts import WorkerContractError, parse_worker_input  # noqa: E402


def _payload(workload: str) -> dict[str, object]:
    job_id = "sam2-gate-job"
    generation_id = "sam2-gate-generation"
    attempt_id = "sam2-gate-attempt"
    return {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": "dev",
        "workload": workload,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/",
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": "a" * 64,
        "input_bytes": 1,
    }


def test_drawing_segment_is_allowed_by_dedicated_l4_worker_envelope() -> None:
    parsed = parse_worker_input(_payload("drawing.segment"), execution_group="l4")

    assert parsed.workload == "drawing.segment"


def test_drawing_segment_remains_disallowed_in_video_execution_group() -> None:
    with pytest.raises(WorkerContractError, match="MODAL_WORKLOAD_NOT_ALLOWED"):
        parse_worker_input(_payload("drawing.segment"), execution_group="l40s-video")


def test_drawing_segment_product_registry_remains_disabled() -> None:
    registry = json.loads((MODAL_DIR / "workloads.json").read_text(encoding="utf-8"))
    sam2 = next(item for item in registry["workloads"] if item["id"] == "drawing.segment")

    assert sam2["enabled"] is False
