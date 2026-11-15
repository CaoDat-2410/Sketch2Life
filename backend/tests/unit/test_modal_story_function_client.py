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
    activity = {
        "activity_ref": "draft_request-1_001",
        "title": "Quan sát lá ngoài trời",
        "objective": "Quan sát hình dáng lá quanh chủ đề con bướm.",
        "materials_text": "Lá đã rụng và giấy.",
        "preparation_text": "Người lớn chọn khu vực sân chơi an toàn.",
        "instructions_text": "Ngoài trời ở sân chơi, trẻ tự chọn lá đã rụng để quan sát; người lớn đi cùng.",
        "observation_notes": "Ghi nhận điều trẻ tự chọn quan sát.",
        "safety_notes": "Không nếm lá; người lớn luôn giám sát.",
        "activity_kind": "outdoor",
        "source": "AI_GENERATED_DRAFT",
        "source_lesson_id": None,
        "source_lesson_title": None,
        "source_lesson_version_id": None,
        "source_content_sha256": None,
        "source_activity_index": None,
        "match_reason": "Bản nháp AI cần người lớn xem lại.",
    }
    activity_sha256 = hashlib.sha256(
        json.dumps(activity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "worker_input": {
            "schema_version": "sketch2life.story-generation-input.v2",
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
            "primary_activity": activity,
            "primary_activity_sha256": activity_sha256,
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
    assert request["schema_version"] == "sketch2life.story-generation-input.v2"
    assert request["primary_activity"]["activity_ref"] == "draft_request-1_001"
    assert request["primary_activity_sha256"] == _story_context()["worker_input"]["primary_activity_sha256"]
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
            assert entries == 500
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
                                "event": "worker_phase_started",
                                "workload": "story.generate",
                                "stage": "model_inference",
                                "prompt": "phase private prompt",
                            }
                        )
                        + "\n"
                        + json.dumps(
                            {
                                "schema_version": "sketch2life.modal.worker-event.v1",
                                "event": "worker_phase_failed",
                                "workload": "story.generate",
                                "stage": "model_inference",
                                "duration_ms": 6500,
                                "error_code": "MODEL_INFERENCE_TIMEOUT",
                                "error_type": "InputCancellation",
                                "generated_text": "discard this content",
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
                                "gpu_class": "L40S|L4|A10",
                                "error_code": "MODAL_MODEL_OUTPUT_INVALID",
                                "error_type": "RuntimeError",
                                "generated_text": "private generated story",
                            }
                        )
                        + "\n"
                        + json.dumps(
                            {
                                "event": "story_output_rejected",
                                "reason_code": "EDUCATIONAL_FACT_STAGE_MISSING",
                                "generation_seconds": 6.5,
                                "output_token_count": 812,
                                "max_new_tokens": 4096,
                                "token_limit_reached": False,
                                "ended_with_model_eos": True,
                                "decoded_character_count": 3812,
                                "json_complete": True,
                                "json_root_type": "dict",
                                "json_root_key_count": 3,
                                "field_key_counts": {
                                    "narration": 5,
                                    "generated_text": "private data omitted",
                                },
                                "story_field_diagnostics_available": True,
                                "story_text_field_metric_count": 1,
                                "story_incomplete_sentence_fields": [
                                    "scenes[2].visual_prompt",
                                    "private generated text",
                                ],
                                "story_text_field_metrics": [
                                    {
                                        "field": "scenes[2].visual_prompt",
                                        "character_count": 27,
                                        "max_length": 240,
                                        "sentence_complete": False,
                                    },
                                    {
                                        "field": "scenes[2].private_generated_text",
                                        "character_count": 999,
                                        "max_length": 999,
                                    },
                                ],
                                "generated_text": "private story content",
                            }
                        )
                    },
                )()
            ]

    summary = summarize_worker_call_logs(type("Call", (), {"logs": _Logs()})())

    assert summary == {
        "worker_logs_available": True,
        "worker_log_event_count": 4,
        "worker_phase_history": [
            {"event": "worker_phase_started", "stage": "model_inference"},
            {
                "event": "worker_phase_failed",
                "stage": "model_inference",
                "duration_ms": 6500,
                "error_code": "MODEL_INFERENCE_TIMEOUT",
                "error_type": "InputCancellation",
            },
        ],
        "worker_started_observed": True,
        "worker_terminal_event": "worker_failed",
        "worker_last_stage": "business_rule_validation",
        "worker_error_code": "MODAL_MODEL_OUTPUT_INVALID",
        "worker_diagnostic_code": "EDUCATIONAL_FACT_STAGE_MISSING",
        "worker_diagnostic_details": {
            "event": "story_output_rejected",
            "generation_seconds": 6.5,
            "output_token_count": 812,
            "max_new_tokens": 4096,
            "token_limit_reached": False,
            "ended_with_model_eos": True,
            "decoded_character_count": 3812,
            "json_complete": True,
            "json_root_type": "dict",
            "json_root_key_count": 3,
            "field_key_counts": {"narration": 5},
            "story_field_diagnostics_available": True,
            "story_text_field_metric_count": 1,
            "story_incomplete_sentence_fields": ["scenes[2].visual_prompt"],
            "story_text_field_metrics": [
                {
                    "field": "scenes[2].visual_prompt",
                    "character_count": 27,
                    "max_length": 240,
                    "sentence_complete": False,
                }
            ],
        },
        "worker_error_type": "RuntimeError",
        "worker_duration_ms": 1234,
        "worker_model_id": None,
        "worker_model_revision": None,
        "worker_gpu_class": "L40S|L4|A10",
        "worker_output_size_bytes": None,
        "worker_output_sha256": None,
        "worker_binary_output_sha256": None,
        "worker_failure_boundary": "worker_terminal_failure_observed",
    }
    assert "private prompt" not in repr(summary)
    assert "private generated story" not in repr(summary)
    assert "phase private prompt" not in repr(summary)
    assert "discard this content" not in repr(summary)
    assert "private story content" not in repr(summary)


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
    sleep_delays: list[float] = []
    monkeypatch.setattr(client_module.time, "sleep", sleep_delays.append)
    summary = summarize_worker_call_logs(type("Call", (), {"logs": logs})())

    assert logs.calls == 2
    assert sleep_delays == [0.25]
    assert client_module.summarize_worker_call_logs.__kwdefaults__["max_log_wait_seconds"] == 5.0
    assert summary["worker_terminal_event"] == "worker_succeeded"
    assert summary["worker_diagnostic_code"] is None
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
    assert summary["worker_diagnostic_code"] is None
    assert "provider diagnostic" not in repr(summary)


def test_worker_log_summary_preserves_safe_svg_generation_diagnostics() -> None:
    class _Logs:
        def tail(self, *, entries: int):
            return [
                type(
                    "Entry",
                    (),
                    {
                        "message": "\n".join(
                            json.dumps(event)
                            for event in (
                                {
                                    "event": "svg_topic_stroke_guide_output_invalid",
                                    "workload": "svg.topic-stroke-guide.generate",
                                    "reason_code": "SVG_TOPIC_GUIDE_JSON_INVALID",
                                    "input_token_count": 812,
                                    "output_token_count": 1200,
                                    "max_new_tokens": 12288,
                                    "generation_seconds": 240.5,
                                    "token_limit_reached": False,
                                    "ended_with_model_eos": True,
                                    "decoded_character_count": 2400,
                                    "callback_calls": 1201,
                                    "force_stop_parser_calls": 0,
                                    "last_parser_can_end": True,
                                    "last_model_eos_allowed": True,
                                    "last_parser_state_class": "ObjectParser",
                                    "final_model_eos_was_allowed_at_previous_prefix": True,
                                    "final_model_eos_prefix_parser_can_end": True,
                                    "generated_special_token_count": 1,
                                    "generated_non_eos_special_token_count": 0,
                                    "enforcer_decoder_decoded_character_count": 2400,
                                    "enforcer_decoder_json_complete": False,
                                    "enforcer_decoder_json_error_type": "JSONDecodeError",
                                    "enforcer_decoder_json_error_category": "UNTERMINATED_STRING",
                                    "enforcer_decoder_json_error_position": 2300,
                                    "enforcer_decoder_unterminated_string_character_count": 0,
                                    "active_json_string_field": "d",
                                    "replay_parser_can_end": False,
                                    "replay_parser_error_count": 0,
                                    "incremental_vs_replay_can_end_mismatch": True,
                                    "replay_parser_diagnostic_error": False,
                                    "json_error_type": "JSONDecodeError",
                                    "json_error_position": 2300,
                                    "json_error_line": 1,
                                    "json_error_column": 2301,
                                    "generated_text": "private SVG model output",
                                },
                                {
                                    "schema_version": "sketch2life.modal.worker-event.v1",
                                    "event": "worker_failed",
                                    "workload": "svg.topic-stroke-guide.generate",
                                    "stage": "output_parse_and_contract_validation",
                                    "duration_ms": 388003,
                                    "error_code": "SVG_TOPIC_GUIDE_JSON_INVALID",
                                    "error_type": "RuntimeError",
                                },
                            )
                        )
                    },
                )()
            ]

    summary = summarize_worker_call_logs(type("Call", (), {"logs": _Logs()})())

    assert summary["worker_terminal_event"] == "worker_failed"
    assert summary["worker_diagnostic_code"] == "SVG_TOPIC_GUIDE_JSON_INVALID"
    assert summary["worker_diagnostic_details"] == {
        "event": "svg_topic_stroke_guide_output_invalid",
        "input_token_count": 812,
        "output_token_count": 1200,
        "max_new_tokens": 12288,
        "generation_seconds": 240.5,
        "token_limit_reached": False,
        "ended_with_model_eos": True,
        "decoded_character_count": 2400,
        "callback_calls": 1201,
        "force_stop_parser_calls": 0,
        "last_parser_can_end": True,
        "last_model_eos_allowed": True,
        "last_parser_state_class": "ObjectParser",
        "final_model_eos_was_allowed_at_previous_prefix": True,
        "final_model_eos_prefix_parser_can_end": True,
        "generated_special_token_count": 1,
        "generated_non_eos_special_token_count": 0,
        "enforcer_decoder_decoded_character_count": 2400,
        "enforcer_decoder_json_complete": False,
        "enforcer_decoder_json_error_type": "JSONDecodeError",
        "enforcer_decoder_json_error_category": "UNTERMINATED_STRING",
        "enforcer_decoder_json_error_position": 2300,
        "enforcer_decoder_unterminated_string_character_count": 0,
        "active_json_string_field": "d",
        "replay_parser_can_end": False,
        "replay_parser_error_count": 0,
        "incremental_vs_replay_can_end_mismatch": True,
        "replay_parser_diagnostic_error": False,
        "json_error_type": "JSONDecodeError",
        "json_error_position": 2300,
        "json_error_line": 1,
        "json_error_column": 2301,
    }
    assert "private SVG model output" not in repr(summary)
