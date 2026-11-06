from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from io import BytesIO
from typing import Any

import pytest
from sketch2life.infrastructure.ai import modal_function_client as client_module
from sketch2life.infrastructure.ai.modal_function_client import (
    ModalFunctionExecutionFailed,
    ModalStoryFunctionClient,
    summarize_worker_call_logs,
)


class _Batch:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def put_file(self, source: BytesIO, remote_path: str) -> None:
        self.files[remote_path] = source.getvalue()


class _Volume:
    def __init__(self) -> None:
        self.batch = _Batch()
        self.removed_paths: list[str] = []

    @contextmanager
    def batch_upload(self):
        yield self.batch

    def remove_file(self, path: str, *, recursive: bool) -> None:
        assert recursive
        self.removed_paths.append(path)


class _Call:
    object_id = "fc-story-test-0001"

    def __init__(
        self, output: dict[str, Any] | None = None, error: Exception | None = None
    ) -> None:
        self.output = output
        self.error = error

    def get(self, *, timeout: float) -> dict[str, Any]:
        assert timeout > 0
        if self.error is not None:
            raise self.error
        assert self.output is not None
        return self.output


class _Function:
    def __init__(self, *, terminal_error: Exception | None = None) -> None:
        self.terminal_error = terminal_error
        self.call: _Call | None = None

    def spawn(self, payload: dict[str, Any]) -> _Call:
        if self.terminal_error is not None:
            self.call = _Call(error=self.terminal_error)
        else:
            self.call = _Call(
                output={
                    "schema_version": client_module.WORKER_OUTPUT_SCHEMA,
                    "workload": "story.generate",
                    "job_id": payload["job_id"],
                    "generation_id": payload["generation_id"],
                    "attempt_id": payload["attempt_id"],
                    "model": {
                        "id": client_module.STORY_MODEL_ID,
                        "revision": client_module.STORY_MODEL_REVISION,
                    },
                    "result": {"fixture": "valid"},
                }
            )
        return self.call


def _story_context() -> dict[str, object]:
    return {
        "worker_input": {
            "schema_version": "sketch2life.story-generation-input.v1",
            "role": "PARENT",
            "language": "vi",
            "confirmed_subject": "Con bướm",
            "understanding_revision": 1,
            "drawing_sha256": "a" * 64,
            "visible_features": ["hai cặp cánh", "thân mảnh"],
            "child_age_months": 60,
            "context_revision": 1,
            "adult_confirmed_idea": "Kể đúng vòng đời của bướm.",
            "rewrite_instruction": None,
            "lesson_direction": None,
        }
    }


def test_story_manifest_uses_generic_modal_ai_request_schema() -> None:
    volume = _Volume()
    function = _Function()
    result, call_id = ModalStoryFunctionClient(volume=volume, function=function).generate(
        _story_context()
    )

    manifest_path, manifest_bytes = next(
        (path, data)
        for path, data in volume.batch.files.items()
        if path.endswith("input/manifest.json")
    )
    request_path, request_bytes = next(
        (path, data)
        for path, data in volume.batch.files.items()
        if path.endswith("input/request.json")
    )
    manifest = json.loads(manifest_bytes)
    request = json.loads(request_bytes)

    assert manifest["schema_version"] == "sketch2life.modal.ai-request.v1"
    assert manifest["asset"] == {
        "path": "input/request.json",
        "content_type": "application/json",
        "size_bytes": len(request_bytes),
        "sha256": hashlib.sha256(request_bytes).hexdigest(),
    }
    assert request["schema_version"] == "sketch2life.story-generation-input.v1"
    assert "activities" not in request
    assert call_id == "fc-story-test-0001"
    assert result == {"fixture": "valid"}
    assert manifest_path.rsplit("/", 1)[0] == request_path.rsplit("/", 1)[0]
    assert volume.removed_paths == [
        manifest_path.lstrip("/").rsplit("input/manifest.json", 1)[0] + "input"
    ]


def test_known_modal_schema_rejection_is_terminal_not_unknown() -> None:
    volume = _Volume()
    function = _Function(
        terminal_error=RuntimeError("WorkerContractError: MODAL_SCHEMA_UNSUPPORTED")
    )
    client = ModalStoryFunctionClient(volume=volume, function=function)

    with pytest.raises(ModalFunctionExecutionFailed) as error:
        client.generate(_story_context())

    assert error.value.code == "STORY_INPUT_CONTRACT_INVALID"
    assert volume.removed_paths


def test_modal_remote_error_is_terminal_not_unknown() -> None:
    volume = _Volume()
    remote_error = type("RemoteError", (Exception,), {"__module__": "modal.exception"})
    function = _Function(terminal_error=remote_error("remote worker failed"))
    client = ModalStoryFunctionClient(volume=volume, function=function)

    with pytest.raises(ModalFunctionExecutionFailed) as error:
        client.generate(_story_context())

    assert error.value.code == "STORY_WORKER_FAILED_TERMINAL"
    assert volume.removed_paths


def test_worker_log_summary_keeps_allowlisted_diagnosis_only() -> None:
    class _Logs:
        def tail(self, *, entries: int):
            assert entries == 100
            return [
                type(
                    "Entry",
                    (),
                    {
                        "message": json.dumps(
                            {
                                "schema_version": "sketch2life.modal.worker-event.v1",
                                "event": "worker_started",
                                "workload": "story.generate",
                                "job_id": "job-safe-01",
                                "stage": "worker_entrypoint",
                                "prompt": "private prompt must be discarded",
                            }
                        )
                        + "\n"
                        + json.dumps(
                            {
                                "schema_version": "sketch2life.modal.worker-event.v1",
                                "event": "worker_failed",
                                "workload": "story.generate",
                                "stage": "business_rule_validation",
                                "duration_ms": 1234,
                                "error_code": "EDUCATIONAL_FACT_INVALID",
                                "error_type": "RuntimeError",
                                "generated_text": "private generated story",
                            }
                        )
                    },
                )()
            ]

    summary = summarize_worker_call_logs(type("Call", (), {"logs": _Logs()})())

    assert summary == {
        "worker_logs_available": True,
        "worker_log_event_count": 2,
        "worker_started_observed": True,
        "worker_terminal_event": "worker_failed",
        "worker_last_stage": "business_rule_validation",
        "worker_error_code": "EDUCATIONAL_FACT_INVALID",
        "worker_error_type": "RuntimeError",
        "worker_duration_ms": 1234,
        "worker_model_id": None,
        "worker_model_revision": None,
        "worker_gpu_class": None,
        "worker_output_size_bytes": None,
        "worker_output_sha256": None,
        "worker_binary_output_sha256": None,
        "worker_failure_boundary": "worker_terminal_failure_observed",
    }
    assert "private prompt" not in repr(summary)
    assert "private generated story" not in repr(summary)



def test_worker_log_summary_retries_until_terminal_event_is_indexed(monkeypatch) -> None:
    class _Logs:
        calls = 0

        def tail(self, *, entries: int):
            self.calls += 1
            if self.calls == 1:
                return []
            return [
                type(
                    "Entry",
                    (),
                    {
                        "message": json.dumps(
                            {
                                "schema_version": "sketch2life.modal.worker-event.v1",
                                "event": "worker_succeeded",
                                "workload": "asr.transcribe",
                                "stage": "terminal",
                                "duration_ms": 99,
                                "model_id": "Systran/faster-whisper-large-v3",
                                "model_revision": "abc123",
                                "gpu_class": "cpu",
                                "output_size_bytes": 42,
                                "output_sha256": "a" * 64,
                                "binary_output_sha256": "b" * 64,
                                "private_text": "must not be surfaced",
                            }
                        )
                    },
                )()
            ]

    logs = _Logs()
    monkeypatch.setattr(client_module.time, "sleep", lambda _delay: None)
    summary = summarize_worker_call_logs(type("Call", (), {"logs": logs})())

    assert logs.calls == 2
    assert summary["worker_terminal_event"] == "worker_succeeded"
    assert summary["worker_model_id"] == "Systran/faster-whisper-large-v3"
    assert summary["worker_gpu_class"] == "cpu"
    assert summary["worker_output_size_bytes"] == 42
    assert summary["worker_output_sha256"] == "a" * 64
    assert summary["worker_binary_output_sha256"] == "b" * 64
    assert "must not be surfaced" not in repr(summary)


def test_worker_log_summary_fails_closed_when_modal_logs_unavailable() -> None:
    class _Logs:
        def tail(self, *, entries: int):
            raise RuntimeError("provider diagnostic that must not be surfaced")

    summary = summarize_worker_call_logs(type("Call", (), {"logs": _Logs()})())

    assert summary["worker_logs_available"] is False
    assert summary["worker_started_observed"] is False
    assert "provider diagnostic" not in repr(summary)
