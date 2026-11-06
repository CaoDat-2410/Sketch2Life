from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worker_observability import observed_worker, worker_phase  # noqa: E402


def _records(captured: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in captured.splitlines() if line.startswith("{")]


def test_worker_success_records_safe_phases_without_input_or_output_text(capsys) -> None:
    @observed_worker(
        workload="lesson.plan.suggest",
        model_id="Qwen/Qwen3.5-9B",
        model_revision="abc123",
        gpu_class="L4|L40S|A10",
    )
    def run(payload):
        with worker_phase("input_validation"):
            assert payload["child_name"] == "Private Child Name"
        with worker_phase("model_inference"):
            pass
        return {"draft": "private generated lesson text", "asset": b"synthetic"}

    result = run(
        {
            "job_id": "job-opaque-01",
            "generation_id": "gen-opaque-02",
            "attempt_id": "attempt-opaque-03",
            "child_name": "Private Child Name",
            "prompt": "never log this prompt",
            "image": b"never log these pixels",
        }
    )

    records = _records(capsys.readouterr().out)
    assert result["asset"] == b"synthetic"
    assert [record["event"] for record in records] == [
        "worker_started",
        "worker_phase_started",
        "worker_phase_succeeded",
        "worker_phase_started",
        "worker_phase_succeeded",
        "worker_succeeded",
    ]
    serialized = json.dumps(records)
    for private_value in (
        "Private Child Name",
        "never log this prompt",
        "never log these pixels",
        "private generated lesson text",
    ):
        assert private_value not in serialized
    terminal = records[-1]
    assert terminal["workload"] == "lesson.plan.suggest"
    assert terminal["job_ref"] == "754d8901b3b7bc03"
    assert terminal["model_revision"] == "abc123"
    assert terminal["binary_output_bytes"] == len(b"synthetic")
    assert terminal["output_kind"] == "media"
    assert all("timestamp_utc" in record and "stage" in record for record in records)


def test_worker_failure_identifies_failing_stage_and_safe_stable_code(capsys) -> None:
    @observed_worker(workload="drawing.analyze", model_id="Qwen/Qwen3.5-9B")
    def run(_payload):
        with worker_phase("model_load"):
            raise RuntimeError("MODEL_CHECKPOINT_INVALID")

    with pytest.raises(RuntimeError):
        run({"job_id": "job-safe-01", "prompt": "do not log"})

    records = _records(capsys.readouterr().out)
    phase_failure, terminal_failure = records[-2:]
    assert phase_failure["event"] == "worker_phase_failed"
    assert phase_failure["stage"] == "model_load"
    assert phase_failure["error_code"] == "MODEL_CHECKPOINT_INVALID"
    assert terminal_failure["event"] == "worker_failed"
    assert terminal_failure["stage"] == "model_load"
    assert terminal_failure["error_code"] == "MODEL_CHECKPOINT_INVALID"
    assert "do not log" not in json.dumps(records)


def test_worker_failure_does_not_emit_arbitrary_exception_message(capsys) -> None:
    @observed_worker(workload="asr.transcribe")
    def run(_payload):
        with worker_phase("model_load"):
            raise RuntimeError("provider response included private input data")

    with pytest.raises(RuntimeError):
        run({"attempt_id": "attempt-safe-01"})

    records = _records(capsys.readouterr().out)
    terminal = records[-1]
    assert terminal["error_code"] == "UNCLASSIFIED_FAILURE"
    assert terminal["error_type"] == "RuntimeError"
    assert "private input data" not in json.dumps(records)


def test_worker_rejects_unbounded_phase_labels() -> None:
    @observed_worker(workload="asr.transcribe")
    def run(_payload):
        with worker_phase("raw user supplied label"):
            return None

    with pytest.raises(ValueError, match="fixed safe identifier"):
        run({})
