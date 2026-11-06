from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
SCRIPT_DIR = SCRIPT.parent
BACKEND_SRC = REPO / "backend" / "src"
MODAL_APP_DIR = REPO / "deployment" / "modal" / "srs_v23"
for value in (str(BACKEND_SRC), str(SCRIPT_DIR), str(MODAL_APP_DIR)):
    if value not in sys.path:
        sys.path.insert(0, value)

import modal  # noqa: E402
import run_ai_nonvideo_30min_queue_retest_20261104 as qwen  # noqa: E402
import run_ai_nonvideo_full_retest_20261104 as flow  # noqa: E402
import run_rev52_nonvideo_ai_retest_20261106 as rev52  # noqa: E402
import run_speech_nonvideo_retest_20261104 as speech  # noqa: E402
from contracts import WORKER_OUTPUT_SCHEMA  # noqa: E402
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1  # noqa: E402
from sketch2life.infrastructure.ai.modal_function_client import (  # noqa: E402
    summarize_worker_call_logs,
)

OUTPUT_DIR = (
    FEATURE
    / "evidence"
    / "nonvideo_modal_ai_reliability_20261106"
    / "runtime"
    / "recovery_after_wait_fix_20261106"
)
GUARD = OUTPUT_DIR / "dispatch_guard.json"
IMAGE_PATH = (
    FEATURE
    / "evidence"
    / "assets"
    / "parent_generated_image_activity_retest_20261103"
    / "synthetic_childlike_butterfly.png"
)
RECOVERED_TTS_PATH = (
    FEATURE
    / "evidence"
    / "nonvideo_modal_ai_reliability_20261106"
    / "runtime"
    / "recovered_tts.wav"
)
SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
EXPECTED_SPEECH = "Con bướm bay qua khu vườn đầy nắng."
INITIAL_WAIT_SECONDS = 1_800
EXTENSION_WAIT_SECONDS = 1_800
SAM2_WAIT_SECONDS = 600


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _existing_speech_result(workload: str) -> dict[str, Any] | None:
    prefix = workload.replace(".", "_") + "_"
    matches = sorted(OUTPUT_DIR.glob(f"{prefix}*_result.json"))
    if not matches:
        return None
    try:
        value = json.loads(matches[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _call_log_summary(call_id: Any) -> dict[str, Any] | None:
    if not isinstance(call_id, str) or not call_id.startswith("fc-"):
        return None
    try:
        return summarize_worker_call_logs(
            modal.FunctionCall.from_id(call_id), max_log_wait_seconds=20
        )
    except Exception as exc:  # noqa: BLE001 - keep only safe exception class.
        return {
            "worker_logs_available": False,
            "worker_failure_boundary": "worker_log_fetch_exception",
            "error_type": type(exc).__name__,
        }


def _run_workload(
    workload: str,
    operation: Callable[[], dict[str, Any]],
    *,
    result_file: str,
    aliases: tuple[str, ...] = (),
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        record = operation()
        if not isinstance(record, dict):
            record = {"workload": workload, "outcome": "INVALID_RUNNER_RESULT"}
    except Exception as exc:  # noqa: BLE001 - persist safe boundary, not exception text.
        record = {
            "workload": workload,
            "outcome": "FAILED_RUNNER",
            "error_type": type(exc).__name__,
        }
    record.setdefault("workload", workload)
    record.setdefault("outcome", "UNKNOWN")
    record["runner_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    record["worker_log_summary"] = _call_log_summary(record.get("call_id"))
    _write(OUTPUT_DIR / result_file, record)
    result = {
        "workload": workload,
        "aliases": list(aliases),
        "outcome": record["outcome"],
        "call_id": record.get("call_id"),
        "runner_elapsed_ms": record["runner_elapsed_ms"],
        "worker_log_summary": record["worker_log_summary"],
        "evidence_file": result_file,
    }
    print(
        json.dumps(
            {
                "workload": workload,
                "aliases": list(aliases),
                "outcome": result["outcome"],
                "call_id": result["call_id"],
                "worker_last_stage": (record["worker_log_summary"] or {}).get(
                    "worker_last_stage"
                ),
                "worker_terminal_event": (record["worker_log_summary"] or {}).get(
                    "worker_terminal_event"
                ),
                "worker_error_code": (record["worker_log_summary"] or {}).get(
                    "worker_error_code"
                ),
                "worker_duration_ms": (record["worker_log_summary"] or {}).get(
                    "worker_duration_ms"
                ),
            },
            ensure_ascii=True,
        ),
        flush=True,
    )
    return result


def _suggest_lesson() -> dict[str, Any]:
    result = qwen.invoke_generic(
        workload="lesson.plan.suggest",
        app="sketch2life-srs23-language-audio-dev",
        function="suggest-lesson-plan",
        request_data=rev52._lesson_suggestion_request(),
    )
    if result.get("outcome") == "SUCCEEDED":
        envelope = (result.get("result") or {}).get("result")
        if not isinstance(envelope, dict) or envelope.get("draft_only") is not True:
            result.update({"outcome": "CONTRACT_FAILED", "contract_error": "DRAFT_ONLY_REQUIRED"})
        else:
            try:
                parsed = LessonContentInputV1.model_validate(envelope.get("content"))
            except Exception as exc:  # noqa: BLE001 - do not persist model content.
                result.update(
                    {
                        "outcome": "CONTRACT_FAILED",
                        "contract_error_type": type(exc).__name__,
                    }
                )
            else:
                result["validated_draft"] = {
                    "status": "DRAFT_ONLY",
                    "activity_count": len(parsed.activities),
                    "activity_kinds": [item.activity_kind for item in parsed.activities],
                    "age_band_ref": parsed.target_age_band_ref,
                    "locale": parsed.locale,
                }
    return result


def _lesson_plan_and_visual_requests() -> tuple[dict[str, Any], dict[str, Any]]:
    plan = flow.synthetic_approved_plan()
    visual = {
        "schema_version": "sketch2life.lesson-visual-input.v1",
        "plan_revision_ref": plan["plan_revision_ref"],
        "content_hash": plan["content_hash"],
        "topic": plan["topic"],
        "steps": [
            {
                "step_index": step["step_index"],
                "instruction": step["action"],
                "placement": step["placement"],
            }
            for step in plan["drawing_steps"]
        ],
    }
    return plan, visual


def _invoke_sam2_segment() -> dict[str, Any]:
    image_bytes = IMAGE_PATH.read_bytes()
    source_sha = _sha(image_bytes)
    job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
    prefix = f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/"
    manifest = {
        "schema_version": "sketch2life.modal.drawing-input.v1",
        "asset": {
            "path": "input/drawing.png",
            "content_type": "image/png",
            "size_bytes": len(image_bytes),
            "sha256": source_sha,
        },
    }
    manifest_bytes = flow.canonical_json(manifest)
    payload = {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": "dev",
        "workload": "drawing.segment",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": _sha(manifest_bytes),
        "input_bytes": len(image_bytes) + len(manifest_bytes),
    }
    _write(
        OUTPUT_DIR / "drawing_segment_dispatch_intent.json",
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "workload": "drawing.segment",
            "app": "sketch2life-srs23-drawing-segment-dev",
            "function": "segment-synthetic-drawing-candidate",
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "source_image_sha256": source_sha,
            "max_attempts": 1,
            "started_at": _now(),
            "video_called": False,
        },
    )
    volume = modal.Volume.from_name(
        SCRATCH_VOLUME, environment_name="dev", version=2
    )
    with volume.batch_upload() as batch:
        batch.put_file(BytesIO(image_bytes), f"/{prefix}input/drawing.png")
        batch.put_file(BytesIO(manifest_bytes), f"/{prefix}input/manifest.json")
    function = modal.Function.from_name(
        "sketch2life-srs23-drawing-segment-dev",
        "segment-synthetic-drawing-candidate",
        environment_name="dev",
    )
    call = function.spawn(payload)
    call_id = getattr(call, "object_id", None)
    started = time.perf_counter()
    terminal = False
    try:
        output = call.get(timeout=SAM2_WAIT_SECONDS)
        terminal = True
        expected = {
            "schema_version": WORKER_OUTPUT_SCHEMA,
            "workload": "drawing.segment",
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "input_sha256": source_sha,
        }
        if not isinstance(output, dict) or any(
            output.get(key) != value for key, value in expected.items()
        ):
            raise ValueError("SAM2 output lineage did not match the synthetic source")
        asset = output.get("asset")
        if not isinstance(asset, dict):
            raise ValueError("SAM2 output omitted derived mask metadata")
        asset = dict(asset)
        mask_bytes = asset.pop("bytes", None)
        if (
            not isinstance(mask_bytes, bytes)
            or len(mask_bytes) != asset.get("size_bytes")
            or _sha(mask_bytes) != asset.get("sha256")
            or not mask_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        ):
            raise ValueError("SAM2 mask failed byte count, digest, or PNG validation")
        mask_file = "sam2_synthetic_butterfly_mask.png"
        (OUTPUT_DIR / mask_file).write_bytes(mask_bytes)
        record: dict[str, Any] = {
            "workload": "drawing.segment",
            "outcome": "SUCCEEDED",
            "call_id": call_id,
            "runner_elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "source_image_sha256": source_sha,
            "source_image_unchanged": _sha(IMAGE_PATH.read_bytes()) == source_sha,
            "mask_file": mask_file,
            "mask_sha256": _sha(mask_bytes),
            "mask_bytes": len(mask_bytes),
            "asset": asset,
            "result": output.get("result"),
        }
    except TimeoutError as exc:
        record = {
            "workload": "drawing.segment",
            "outcome": "UNKNOWN_NO_RETRY",
            "call_id": call_id,
            "runner_elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "error_type": type(exc).__name__,
        }
        try:
            call.cancel(terminate_containers=True)
            call.get(timeout=1)
        except Exception:  # noqa: BLE001 - timeout/cancel is already evidenced above.
            pass
    except Exception as exc:  # noqa: BLE001 - only safe error class is retained.
        record = {
            "workload": "drawing.segment",
            "outcome": "FAILED_TERMINAL" if terminal else "UNKNOWN_NO_RETRY",
            "call_id": call_id,
            "runner_elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "error_type": type(exc).__name__,
        }
    record["worker_log_summary"] = _call_log_summary(call_id)
    log_summary = record["worker_log_summary"] or {}
    if record["outcome"] == "UNKNOWN_NO_RETRY" and log_summary.get(
        "worker_terminal_event"
    ) in {"worker_succeeded", "worker_failed"}:
        record["outcome"] = (
            "FAILED_TERMINAL"
            if log_summary["worker_terminal_event"] == "worker_failed"
            else "OUTPUT_VALIDATION_FAILED"
        )
    if log_summary.get("worker_terminal_event") in {"worker_succeeded", "worker_failed"}:
        volume.remove_file(f"{prefix}input", recursive=True)
    _write(OUTPUT_DIR / "drawing_segment_result.json", record)
    print(
        json.dumps(
            {
                "workload": "drawing.segment",
                "outcome": record["outcome"],
                "call_id": call_id,
                "worker_last_stage": log_summary.get("worker_last_stage"),
                "worker_terminal_event": log_summary.get("worker_terminal_event"),
                "worker_error_code": log_summary.get("worker_error_code"),
                "worker_duration_ms": log_summary.get("worker_duration_ms"),
            },
            ensure_ascii=True,
        ),
        flush=True,
    )
    return record


def main() -> int:
    if GUARD.exists() or OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise SystemExit("Recovery dispatch guard exists; refusing duplicate AI calls.")
    if not IMAGE_PATH.is_file():
        raise SystemExit("The synthetic butterfly drawing fixture is missing.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    started_perf = time.perf_counter()
    started = _now()
    GUARD.write_text(
        json.dumps(
            {
                "state": "DISPATCH_INTENT_RECORDED",
                "created_at": started,
                "recovery_fix": "stage_aware_wait_descriptor_binding_and_terminal_cleanup",
                "synthetic_only": True,
                "video_called": False,
                "max_attempts_per_workload": 1,
                "same_call_extension_only_after_worker_inference_stage": True,
                "workloads": [
                    "drawing.analyze",
                    "story.generate/storyboard.generate",
                    "parent.sketch-guide.generate",
                    "teacher.sketch-deck.generate",
                    "lesson.plan.suggest",
                    "lesson.visual.generate",
                    "tts.narration.generate",
                    "asr.transcribe",
                    "drawing.segment",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    qwen.OUT_DIR = OUTPUT_DIR
    qwen.IMAGE_PATH = IMAGE_PATH
    qwen.WAIT_SECONDS = INITIAL_WAIT_SECONDS
    speech.OUTPUT_DIR = OUTPUT_DIR
    rev52._install_stage_aware_wait()
    outcomes: list[dict[str, Any]] = []

    first = _run_workload(
        "drawing.analyze",
        qwen.invoke_drawing,
        result_file="drawing_analyze_result.json",
    )
    outcomes.append(first)
    first_logs = first.get("worker_log_summary") or {}
    first_error_code = first_logs.get("worker_error_code")
    unresolved_first_call = (
        first["outcome"] in {"UNKNOWN", "UNKNOWN_NO_RETRY", "FAILED_RUNNER"}
        and not first_logs.get("worker_terminal_event")
    )
    bad_input_stage = first_error_code in {
        "MODAL_INPUT_MANIFEST_MISSING",
        "MODAL_INPUT_ASSET_MISSING",
        "MODAL_INPUT_MANIFEST_INVALID",
    }
    if unresolved_first_call or bad_input_stage:
        remaining = [
            "story.generate/storyboard.generate",
            "parent.sketch-guide.generate",
            "teacher.sketch-deck.generate",
            "lesson.plan.suggest",
            "lesson.visual.generate",
            "tts.narration.generate",
            "asr.transcribe",
            "drawing.segment",
        ]
        outcomes.extend(
            {"workload": name, "outcome": "NOT_RUN_SYSTEMIC_PREFLIGHT_FAILURE"}
            for name in remaining
        )
        summary = {
            "plan": "PLAN_REV52_NONVIDEO_MODAL_AI_RELIABILITY_20261106.md",
            "started_at": started,
            "ended_at": _now(),
            "runner_elapsed_seconds": round(time.perf_counter() - started_perf, 3),
            "synthetic_only": True,
            "image_fixture": IMAGE_PATH.name,
            "video_called": False,
            "stop_reason": "FIRST_WORKLOAD_INPUT_OR_TERMINAL_STATE_UNSAFE",
            "workloads": outcomes,
        }
        _write(OUTPUT_DIR / "summary.json", summary)
        _write(
            OUTPUT_DIR / "workload_matrix.json",
            {"workloads": outcomes, "registered_workload_count": 9, "video_called": False},
        )
        guard = json.loads(GUARD.read_text(encoding="utf-8"))
        guard.update(
            {
                "state": "ABORTED_AFTER_DRAWING_PREFLIGHT",
                "failure_code": first_error_code,
                "failure_boundary": first_logs.get("worker_failure_boundary"),
                "unknown_outcome": unresolved_first_call,
            }
        )
        _write(GUARD, guard)
        print(
            json.dumps(
                {
                    "stopped_early": True,
                    "failure_code": first_error_code,
                    "failure_boundary": first_logs.get("worker_failure_boundary"),
                    "remaining_workloads_not_run": len(remaining),
                    "video_called": False,
                },
                ensure_ascii=True,
            ),
            flush=True,
        )
        return 2

    outcomes.append(
        _run_workload(
            "story.generate",
            lambda: qwen.invoke_story(
                confirmed_subject="bướm",
                visible_features=["hai đôi cánh rộng", "thân hình thon", "râu cong"],
            ),
            result_file="story_generate_result.json",
            aliases=("storyboard.generate",),
        )
    )
    outcomes.append(
        _run_workload(
            "parent.sketch-guide.generate",
            lambda: qwen.invoke_generic(
                workload="parent.sketch-guide.generate",
                app="sketch2life-srs23-flux-image-dev",
                function="generate-line-sketch-guide-candidate",
                request_data={"topic": "bướm", "difficulty": "beginner", "step_count": 3},
                output_name="parent_sketch_guide.png",
            ),
            result_file="parent_sketch-guide_generate_result.json",
        )
    )
    plan, visual_request = _lesson_plan_and_visual_requests()
    outcomes.append(
        _run_workload(
            "teacher.sketch-deck.generate",
            lambda: qwen.invoke_generic(
                workload="teacher.sketch-deck.generate",
                app="sketch2life-srs23-language-audio-dev",
                function="generate-teacher-sketch-deck",
                request_data=plan,
            ),
            result_file="teacher_sketch-deck_generate_result.json",
        )
    )
    outcomes.append(
        _run_workload(
            "lesson.plan.suggest",
            _suggest_lesson,
            result_file="lesson_plan_suggest_result.json",
        )
    )
    outcomes.append(
        _run_workload(
            "lesson.visual.generate",
            lambda: qwen.invoke_generic(
                workload="lesson.visual.generate",
                app="sketch2life-srs23-flux-image-dev",
                function="generate-approved-lesson-visual-candidate",
                request_data=visual_request,
                output_name="lesson_visual.png",
            ),
            result_file="lesson_visual_generate_result.json",
        )
    )

    tts_path = OUTPUT_DIR / "synthetic_vietnamese_narration.wav"

    def run_tts() -> dict[str, Any]:
        result = speech._invoke(
            workload="tts.narration.generate",
            function_name="synthesize-vietnamese-narration",
            asset_path="input/request.json",
            content_type="application/json",
            asset_bytes=flow.canonical_json(
                {"text": EXPECTED_SPEECH, "voice": "Hải Đăng"}
            ),
            output_path=tts_path,
        )
        result["output_file"] = tts_path.name
        result["output_sha256"] = _sha(tts_path.read_bytes())
        return result

    tts_result = _run_workload(
        "tts.narration.generate",
        run_tts,
        result_file="tts_narration_result.json",
    )
    if tts_result["outcome"] != "SUCCEEDED":
        prior_tts = _existing_speech_result("tts.narration.generate")
        if prior_tts and prior_tts.get("call_id"):
            tts_result["prior_completed_call_id"] = prior_tts["call_id"]
        if not tts_path.is_file() and RECOVERED_TTS_PATH.is_file():
            tts_path.write_bytes(RECOVERED_TTS_PATH.read_bytes())
            tts_result["asr_source"] = "previously_validated_completed_tts_call"
    outcomes.append(tts_result)

    audio_path = tts_path if tts_path.is_file() else RECOVERED_TTS_PATH

    def run_asr() -> dict[str, Any]:
        audio_bytes = audio_path.read_bytes()
        if not audio_bytes.startswith(b"RIFF") or audio_bytes[8:12] != b"WAVE":
            return {"workload": "asr.transcribe", "outcome": "INPUT_INVALID"}
        result = speech._invoke(
            workload="asr.transcribe",
            function_name="transcribe-vietnamese-audio",
            asset_path="input/audio.wav",
            content_type="audio/wav",
            asset_bytes=audio_bytes,
            output_path=None,
        )
        transcript = (((result.get("result") or {}).get("result") or {}).get("text"))
        if isinstance(transcript, str):
            result["quality_check"] = {
                "reference": EXPECTED_SPEECH,
                "transcript": transcript,
                "word_error_rate": round(rev52._wer(EXPECTED_SPEECH, transcript), 4),
                "adult_confirmation_required": True,
            }
        result["input_audio_sha256"] = _sha(audio_bytes)
        result["input_audio_source"] = audio_path.name
        return result

    outcomes.append(
        _run_workload(
            "asr.transcribe", run_asr, result_file="asr_transcribe_result.json"
        )
    )
    outcomes.append(
        _run_workload(
            "drawing.segment",
            _invoke_sam2_segment,
            result_file="drawing_segment_result.json",
        )
    )

    summary = {
        "plan": "PLAN_REV52_NONVIDEO_MODAL_AI_RELIABILITY_20261106.md",
        "started_at": started,
        "ended_at": _now(),
        "runner_elapsed_seconds": round(time.perf_counter() - started_perf, 3),
        "synthetic_only": True,
        "image_fixture": IMAGE_PATH.name,
        "video_called": False,
        "max_attempts_per_workload": 1,
        "initial_wait_seconds": INITIAL_WAIT_SECONDS,
        "same_call_extension_seconds": EXTENSION_WAIT_SECONDS,
        "sam2_function_wait_seconds": SAM2_WAIT_SECONDS,
        "workloads": outcomes,
    }
    _write(OUTPUT_DIR / "summary.json", summary)
    _write(
        OUTPUT_DIR / "workload_matrix.json",
        {
            "workloads": outcomes,
            "registered_workload_count": 9,
            "video_called": False,
        },
    )
    print(
        json.dumps(
            {
                "summary": "summary.json",
                "video_called": False,
                "workloads": [
                    {"workload": item["workload"], "outcome": item["outcome"]}
                    for item in outcomes
                ],
            },
            ensure_ascii=True,
        ),
        flush=True,
    )
    return 0 if all(item["outcome"] == "SUCCEEDED" for item in outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
