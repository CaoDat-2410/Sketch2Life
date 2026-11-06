from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
SCRIPT_DIR = SCRIPT.parent
BACKEND_SRC = REPO / "backend" / "src"
OUTPUT_DIR = (
    FEATURE / "evidence" / "nonvideo_modal_ai_reliability_20261106" / "runtime"
)
DISPATCH_GUARD = (
    FEATURE / "evidence" / "nonvideo_modal_ai_reliability_20261106" / "dispatch_intent.json"
)
IMAGE_PATH = (
    FEATURE
    / "evidence"
    / "assets"
    / "parent_generated_image_activity_retest_20261103"
    / "synthetic_childlike_butterfly.png"
)
for value in (str(BACKEND_SRC), str(SCRIPT_DIR)):
    if value not in sys.path:
        sys.path.insert(0, value)

import modal  # noqa: E402
import run_ai_nonvideo_30min_queue_retest_20261104 as qwen  # noqa: E402
import run_speech_nonvideo_retest_20261104 as speech  # noqa: E402
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1  # noqa: E402
from sketch2life.infrastructure.ai.modal_function_client import (  # noqa: E402
    summarize_worker_call_logs,
)

INITIAL_WAIT_SECONDS = 1_800
EXTENSION_WAIT_SECONDS = 1_800
SHORT_INITIAL_WAIT_SECONDS = 600
SHORT_EXTENSION_WAIT_SECONDS = 1_200
LONG_INFERENCE_STAGES = {
    "model_inference",
    "flux_image_inference",
    "prompt_upsampler_inference",
    "sam2_mask_inference",
    "tts_inference",
    "asr_inference_and_decode",
}
EXPECTED_SPEECH = "Con bướm bay qua khu vườn đầy nắng."


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _install_stage_aware_wait() -> None:
    """Extend the same Modal call once only when logs prove inference is running."""
    original_get = modal.FunctionCall.__dict__["get"]
    extended: set[str] = set()

    def invoke_original_get(
        call: Any, timeout: float | None, index: int
    ) -> Any:
        bound_get = original_get.__get__(call, type(call))
        return bound_get(timeout=timeout, index=index)

    def get_with_stage_aware_extension(
        call: Any, timeout: float | None = None, *, index: int = 0
    ) -> Any:
        try:
            return invoke_original_get(call, timeout, index)
        except TimeoutError:
            call_id = getattr(call, "object_id", None)
            if not isinstance(call_id, str) or call_id in extended:
                raise
            summary = summarize_worker_call_logs(call, max_log_wait_seconds=20)
            short_call = timeout is not None and timeout <= SHORT_INITIAL_WAIT_SECONDS
            eligible = (
                summary["worker_started_observed"]
                and summary["worker_terminal_event"] is None
                and summary["worker_last_stage"] in LONG_INFERENCE_STAGES
            )
            if not eligible:
                return _raise_timeout()
            extended.add(call_id)
            extension = (
                SHORT_EXTENSION_WAIT_SECONDS if short_call else EXTENSION_WAIT_SECONDS
            )
            print(
                json.dumps(
                    {
                        "event": "same_call_wait_extended",
                        "call_id": call_id,
                        "last_stage": summary["worker_last_stage"],
                        "additional_wait_seconds": extension,
                    },
                    ensure_ascii=True,
                ),
                flush=True,
            )
            return invoke_original_get(call, extension, index)

    def _raise_timeout() -> Any:
        raise TimeoutError

    modal.FunctionCall.get = get_with_stage_aware_extension


def _lesson_suggestion_request() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.lesson-plan-suggest-input.v1",
        "topic": "Con bướm",
        "target_age_band_ref": "age-band-3-6",
        "target_age_band_version": 1,
        "target_age_months": 60,
        "objectives": ["Quan sát hình dáng và vòng đời của bướm"],
        "drawing_subject": "bướm",
        "activity_count": 1,
        "activity_kind": "outdoor",
        "script_following_allowed": False,
        "script_direction": None,
    }


def _read_results() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(OUTPUT_DIR.glob("*_result.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            value.setdefault("evidence_file", path.name)
            results.append(value)
    return results


def _collect_worker_logs(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    summaries: list[dict[str, Any]] = []
    for result in results:
        call_id = result.get("call_id")
        if not isinstance(call_id, str) or not call_id.startswith("fc-") or call_id in seen:
            continue
        seen.add(call_id)
        workload = result.get("workload", "unknown")
        if workload == "story.generate/storyboard.generate":
            workload_ids = ["story.generate", "storyboard.generate"]
        else:
            workload_ids = [workload] if isinstance(workload, str) else []
        try:
            call = modal.FunctionCall.from_id(call_id)
            summary = summarize_worker_call_logs(call)
        except Exception as exc:  # noqa: BLE001 - keep evidence to the exception class only.
            summary = {
                "worker_logs_available": False,
                "worker_log_event_count": 0,
                "worker_started_observed": False,
                "worker_terminal_event": None,
                "worker_last_stage": None,
                "worker_error_code": None,
                "worker_error_type": type(exc).__name__,
                "worker_duration_ms": None,
                "worker_failure_boundary": "worker_log_fetch_exception",
            }
        summaries.append(
            {
                "call_id": call_id,
                "workload_ids": workload_ids,
                "result_outcome": result.get("outcome", "UNKNOWN"),
                **summary,
            }
        )
    return summaries


def _wer(reference: str, actual: str) -> float:
    expected = reference.casefold().split()
    observed = actual.casefold().split()
    previous = list(range(len(observed) + 1))
    for row, word in enumerate(expected, start=1):
        current = [row]
        for column, actual_word in enumerate(observed, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (word != actual_word),
                )
            )
        previous = current
    return previous[-1] / max(1, len(expected))


def main() -> int:
    if DISPATCH_GUARD.exists():
        raise SystemExit("Rev52 dispatch guard exists; refusing duplicate Modal AI calls.")
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise SystemExit("Rev52 runtime evidence exists; refusing duplicate Modal AI calls.")
    if not IMAGE_PATH.is_file():
        raise SystemExit("The approved synthetic image fixture is missing.")

    DISPATCH_GUARD.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        DISPATCH_GUARD,
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "created_at": _now(),
            "synthetic_only": True,
            "max_attempts_per_workload": 1,
            "same_call_extension_only_after_worker_inference_stage": True,
            "video_called": False,
            "image_fixture": IMAGE_PATH.name,
        },
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _install_stage_aware_wait()
    qwen.OUT_DIR = OUTPUT_DIR
    qwen.IMAGE_PATH = IMAGE_PATH
    qwen.WAIT_SECONDS = INITIAL_WAIT_SECONDS
    speech.OUTPUT_DIR = OUTPUT_DIR

    run_started = _now()
    run_started_perf = time.perf_counter()
    errors: list[dict[str, str]] = []
    try:
        qwen.main()
    except Exception as exc:  # noqa: BLE001 - record only safe exception type.
        errors.append({"stage": "qwen_and_visual_workloads", "error_type": type(exc).__name__})

    lesson_result: dict[str, Any]
    try:
        lesson_result = qwen.invoke_generic(
            workload="lesson.plan.suggest",
            app="sketch2life-srs23-language-audio-dev",
            function="suggest-lesson-plan",
            request_data=_lesson_suggestion_request(),
        )
        if lesson_result.get("outcome") == "SUCCEEDED":
            envelope = (lesson_result.get("result") or {}).get("result")
            if not isinstance(envelope, dict) or envelope.get("draft_only") is not True:
                lesson_result.update(
                    {"outcome": "CONTRACT_FAILED", "contract_error": "DRAFT_ONLY_REQUIRED"}
                )
            else:
                parsed = LessonContentInputV1.model_validate(envelope.get("content"))
                lesson_result["validated_draft"] = {
                    "status": "DRAFT_ONLY",
                    "activity_count": len(parsed.activities),
                    "activity_kinds": [item.activity_kind for item in parsed.activities],
                    "age_band_ref": parsed.target_age_band_ref,
                    "locale": parsed.locale,
                }
        _write_json(OUTPUT_DIR / "lesson_plan_suggest_result.json", lesson_result)
    except Exception as exc:  # noqa: BLE001 - record only safe exception type.
        errors.append({"stage": "lesson.plan.suggest", "error_type": type(exc).__name__})
        lesson_result = {
            "workload": "lesson.plan.suggest",
            "outcome": "FAILED_RUNNER",
            "error_type": type(exc).__name__,
        }
        _write_json(OUTPUT_DIR / "lesson_plan_suggest_result.json", lesson_result)

    narration_path = OUTPUT_DIR / "synthetic_vietnamese_narration.wav"
    tts_result: dict[str, Any]
    asr_result: dict[str, Any]
    try:
        import run_ai_nonvideo_full_retest_20261104 as flow_helper

        tts_result = speech._invoke(
            workload="tts.narration.generate",
            function_name="synthesize-vietnamese-narration",
            asset_path="input/request.json",
            content_type="application/json",
            asset_bytes=flow_helper.canonical_json(
                {"text": EXPECTED_SPEECH, "voice": "Hải Đăng"}
            ),
            output_path=narration_path,
        )
        _write_json(OUTPUT_DIR / "tts_narration_result.json", tts_result)
    except Exception as exc:  # noqa: BLE001 - record only safe exception type.
        errors.append({"stage": "tts.narration.generate", "error_type": type(exc).__name__})
        tts_result = {
            "workload": "tts.narration.generate",
            "outcome": "FAILED_RUNNER",
            "error_type": type(exc).__name__,
        }
        _write_json(OUTPUT_DIR / "tts_narration_result.json", tts_result)

    if tts_result.get("outcome") == "SUCCEEDED" and narration_path.is_file():
        try:
            asr_result = speech._invoke(
                workload="asr.transcribe",
                function_name="transcribe-vietnamese-audio",
                asset_path="input/audio.wav",
                content_type="audio/wav",
                asset_bytes=narration_path.read_bytes(),
                output_path=None,
            )
            transcript = (((asr_result.get("result") or {}).get("result") or {}).get("text"))
            if isinstance(transcript, str):
                asr_result["quality_check"] = {
                    "reference": EXPECTED_SPEECH,
                    "transcript": transcript,
                    "word_error_rate": round(_wer(EXPECTED_SPEECH, transcript), 4),
                    "adult_confirmation_required": True,
                }
        except Exception as exc:  # noqa: BLE001 - record only safe exception type.
            errors.append({"stage": "asr.transcribe", "error_type": type(exc).__name__})
            asr_result = {
                "workload": "asr.transcribe",
                "outcome": "FAILED_RUNNER",
                "error_type": type(exc).__name__,
            }
    else:
        asr_result = {
            "workload": "asr.transcribe",
            "outcome": "NOT_RUN_TTS_FAILED",
        }
    _write_json(OUTPUT_DIR / "asr_transcribe_result.json", asr_result)

    results = _read_results()
    worker_logs = _collect_worker_logs(results)
    _write_json(OUTPUT_DIR / "worker_log_summaries.json", worker_logs)
    workload_results: dict[str, dict[str, Any]] = {}
    for result in results:
        workload = result.get("workload")
        if workload == "story.generate/storyboard.generate":
            workload_results["story.generate"] = result
            workload_results["storyboard.generate"] = result
        elif isinstance(workload, str):
            workload_results[workload] = result
    registered = [
        "asr.transcribe",
        "drawing.analyze",
        "story.generate",
        "storyboard.generate",
        "parent.sketch-guide.generate",
        "teacher.sketch-deck.generate",
        "lesson.plan.suggest",
        "lesson.visual.generate",
        "drawing.segment",
        "tts.narration.generate",
    ]
    logs_by_workload = {
        workload: summary
        for summary in worker_logs
        for workload in summary["workload_ids"]
    }
    matrix = []
    for workload in registered:
        result = workload_results.get(workload)
        log_summary = logs_by_workload.get(workload)
        matrix.append(
            {
                "workload": workload,
                "outcome": (
                    result.get("outcome", "UNKNOWN") if result else "NOT_RUN"
                ),
                "call_id": result.get("call_id") if result else None,
                "worker_started": (
                    log_summary.get("worker_started_observed") if log_summary else False
                ),
                "last_worker_stage": (
                    log_summary.get("worker_last_stage") if log_summary else None
                ),
                "worker_terminal_event": (
                    log_summary.get("worker_terminal_event") if log_summary else None
                ),
                "worker_error_code": (
                    log_summary.get("worker_error_code") if log_summary else None
                ),
                "worker_error_type": (
                    log_summary.get("worker_error_type") if log_summary else None
                ),
                "worker_duration_ms": (
                    log_summary.get("worker_duration_ms") if log_summary else None
                ),
                "worker_failure_boundary": (
                    log_summary.get("worker_failure_boundary") if log_summary else None
                ),
            }
        )

    final = {
        "plan": "PLAN_REV52_NONVIDEO_MODAL_AI_RELIABILITY_20261106.md",
        "started_at": run_started,
        "ended_at": _now(),
        "elapsed_seconds": round(time.perf_counter() - run_started_perf, 3),
        "synthetic_only": True,
        "video_called": False,
        "image_fixture": IMAGE_PATH.name,
        "max_attempts_per_workload": 1,
        "qwen_initial_wait_seconds": INITIAL_WAIT_SECONDS,
        "same_call_extension_seconds": EXTENSION_WAIT_SECONDS,
        "errors": errors,
        "workloads": matrix,
        "worker_log_summaries_file": "worker_log_summaries.json",
        "artifacts": [
            path.name
            for path in sorted(OUTPUT_DIR.iterdir())
            if path.is_file() and path.suffix.lower() in {".png", ".wav"}
        ],
    }
    _write_json(OUTPUT_DIR / "summary.json", final)
    print(
        json.dumps(
            {
                "complete": True,
                "elapsed_seconds": final["elapsed_seconds"],
                "workloads": [
                    {
                        "workload": item["workload"],
                        "outcome": item["outcome"],
                        "stage": item["last_worker_stage"],
                        "error_code": item["worker_error_code"],
                    }
                    for item in matrix
                ],
            },
            ensure_ascii=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
