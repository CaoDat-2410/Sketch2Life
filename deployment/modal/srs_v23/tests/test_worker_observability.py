from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worker_observability import (  # noqa: E402
    GenerationProgress,
    _error_code,
    observed_worker,
    refresh_worker_volume,
    worker_runtime_verified,
    worker_phase,
)


def _records(captured: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in captured.splitlines() if line.startswith("{")]


def test_worker_success_records_safe_phases_without_input_or_output_text(
    capsys,
) -> None:
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
    assert len(terminal["output_sha256"]) == 64
    assert len(terminal["binary_output_sha256"]) == 64
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


def test_modal_input_cancellation_near_configured_inference_deadline_is_timeout() -> (
    None
):
    error = type("InputCancellation", (Exception,), {})()

    assert (
        _error_code(
            error,
            timeout_seconds=1_800,
            elapsed_seconds=1_800.007,
            stage="model_inference",
        )
        == "MODEL_INFERENCE_TIMEOUT"
    )


def test_modal_input_cancellation_before_deadline_is_cancellation() -> None:
    error = type("InputCancellation", (Exception,), {})()

    assert (
        _error_code(
            error,
            timeout_seconds=1_800,
            elapsed_seconds=120,
            stage="model_inference",
        )
        == "WORKER_CANCELLED"
    )


def test_worker_rejects_unbounded_phase_labels() -> None:
    @observed_worker(workload="asr.transcribe")
    def run(_payload):
        with worker_phase("raw user supplied label"):
            return None

    with pytest.raises(ValueError, match="fixed safe identifier"):
        run({})


def test_refresh_worker_volume_emits_phase_events(capsys) -> None:
    class _Volume:
        reloaded = False

        def reload(self) -> None:
            self.reloaded = True

    volume = _Volume()

    @observed_worker(workload="story.generate")
    def run(_payload):
        refresh_worker_volume(volume)

    run({})
    records = _records(capsys.readouterr().out)
    assert volume.reloaded is True
    reload_events = [
        record for record in records if record.get("stage") == "scratch_volume_reload"
    ]
    assert [record["event"] for record in reload_events] == [
        "worker_phase_started",
        "worker_phase_succeeded",
    ]


def test_refresh_worker_volume_failure_has_safe_code(capsys) -> None:
    class _Volume:
        def reload(self) -> None:
            raise OSError("provider detail must not be logged")

    @observed_worker(workload="drawing.analyze")
    def run(_payload):
        refresh_worker_volume(_Volume())

    with pytest.raises(RuntimeError, match="MODAL_SCRATCH_VOLUME_RELOAD_FAILED"):
        run({})
    records = _records(capsys.readouterr().out)
    assert records[-1]["stage"] == "scratch_volume_reload"
    assert records[-1]["error_code"] == "MODAL_SCRATCH_VOLUME_RELOAD_FAILED"
    assert "provider detail" not in json.dumps(records)


def test_generation_progress_and_runtime_events_contain_only_allowlisted_metadata(
    capsys,
) -> None:
    @observed_worker(workload="parent.activity.suggest")
    def run(_payload):
        worker_runtime_verified(
            torch_version="2.7.1",
            torch_cuda_version="12.6",
            fla_version="0.6.0",
            causal_conv1d_version="1.7.0",
            triton_version="3.3.1",
            gpu_capability="8.9",
            prompt="must not be logged",
        )
        with GenerationProgress(max_new_tokens=20, heartbeat_seconds=0.01) as progress:
            progress.update(3)
            time.sleep(0.025)
            progress.update(8)

    run({"prompt": "private request"})
    records = _records(capsys.readouterr().out)
    progress = [record for record in records if record["event"] == "model_generation_progress"]
    runtime = next(record for record in records if record["event"] == "worker_runtime_verified")

    assert [record["progress_kind"] for record in progress][0] == "started"
    assert "heartbeat" in {record["progress_kind"] for record in progress}
    assert progress[-1]["progress_kind"] == "completed"
    assert progress[-1]["generated_token_count"] == 8
    assert progress[-1]["max_new_tokens"] == 20
    assert runtime["fla_version"] == "0.6.0"
    assert "prompt" not in runtime
    assert "private request" not in json.dumps(records)
    assert "must not be logged" not in json.dumps(records)
