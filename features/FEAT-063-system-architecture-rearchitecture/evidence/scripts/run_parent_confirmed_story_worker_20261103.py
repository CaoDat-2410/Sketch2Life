from __future__ import annotations

import importlib.util
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import modal

FEATURE = Path(__file__).resolve().parents[2]
ASSET_DIR = FEATURE / "evidence" / "assets" / "parent_generated_image_activity_retest_20261103"
PARENT_RESULT = ASSET_DIR / "storyrun_aligned_api_result.json"
INTENT_PATH = ASSET_DIR / "story_worker_dispatch_intent.json"
RESULT_PATH = ASSET_DIR / "story_worker_result.json"
POC_PATH = FEATURE / "evidence" / "scripts" / "run_modal_ai_hosting_poc.py"


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_poc():
    spec = importlib.util.spec_from_file_location("approved_modal_hosting_poc", POC_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the approved Modal scratch-volume helper.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if INTENT_PATH.exists() or RESULT_PATH.exists():
        raise SystemExit("Story worker already attempted; refusing a second dispatch.")
    parent = json.loads(PARENT_RESULT.read_text(encoding="utf-8"))
    if not parent.get("story_worker_ready") or not parent.get("subject_confirmed"):
        raise SystemExit("Parent adult confirmation is not recorded; no story worker call made.")
    topic = str(parent.get("confirmed_subject_label") or "")
    if topic != "b\u01b0\u1edbm":
        record = {
            "state": "NOT_DISPATCHED_INPUT_CONTRACT_MISMATCH",
            "confirmed_subject_label": topic,
            "worker_contract_topic": "b\u01b0\u1edbm",
            "reason": "The deployed worker accepts only its pinned synthetic topic; no substitution was made.",
        }
        write_json(RESULT_PATH, record)
        print(json.dumps(record, ensure_ascii=True))
        return 3

    poc = load_poc()
    job_id = f"parent-story-{uuid.uuid4().hex[:12]}"
    generation_id = f"story-v1-{uuid.uuid4().hex[:8]}"
    start = time.perf_counter()
    started_at = datetime.now().astimezone().isoformat()
    volume = modal.Volume.from_name(
        poc.SCRATCH_VOLUME_NAME,
        environment_name="dev",
        version=poc.SCRATCH_VOLUME_VERSION,
    )
    payload: dict[str, Any] | None = None
    prefix: str | None = None
    call = None
    terminal = False
    try:
        stage_started = time.perf_counter()
        payload, prefix = poc._stage_json(
            volume,
            workload="story.generate",
            job_id=job_id,
            generation_id=generation_id,
            data={"topic": topic, "language": "vi", "scene_count": 5},
        )
        stage_ms = round((time.perf_counter() - stage_started) * 1000, 3)
        function = modal.Function.from_name(
            poc.APP_NAME,
            "generate-story-and-storyboard",
            environment_name="dev",
        )
        intent = {
            "state": "DISPATCH_INTENT_RECORDED",
            "started_at": started_at,
            "run_ref": parent.get("run_ref"),
            "topic": topic,
            "language": "vi",
            "scene_count": 5,
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_prefix": prefix,
            "input_manifest_sha256": payload["input_manifest_sha256"],
            "max_attempts": 1,
            "video_enabled": False,
        }
        write_json(INTENT_PATH, intent)
        dispatch_started = time.perf_counter()
        try:
            call = function.spawn(payload)
        except Exception as exc:
            write_json(RESULT_PATH, {
                "state": "UNKNOWN_NO_RETRY",
                "exception_type": type(exc).__name__,
                "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
                "stage_elapsed_ms": stage_ms,
                "video_calls": 0,
            })
            return 2
        call_id = getattr(call, "object_id", None)
        if not isinstance(call_id, str) or not call_id.startswith("fc-"):
            write_json(RESULT_PATH, {
                "state": "UNKNOWN_NO_RETRY",
                "error": "Modal returned no valid Function Call ID after dispatch.",
                "job_id": job_id,
                "generation_id": generation_id,
                "stage_elapsed_ms": stage_ms,
                "video_calls": 0,
            })
            return 2
        intent["modal_function_call_id"] = call_id
        write_json(INTENT_PATH, intent)
        try:
            output = call.get(timeout=720)
            terminal = True
        except TimeoutError:
            write_json(RESULT_PATH, {
                "state": "UNKNOWN_NO_RETRY",
                "modal_function_call_id": call_id,
                "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
                "stage_elapsed_ms": stage_ms,
                "reason": "Worker did not reach a terminal response within the bounded wait.",
                "video_calls": 0,
            })
            return 2
        except Exception as exc:
            # No second call. Preserve staged input until the terminal failure is reconciled.
            write_json(RESULT_PATH, {
                "state": "WORKER_FAILED_NO_RETRY",
                "modal_function_call_id": call_id,
                "exception_type": type(exc).__name__,
                "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
                "stage_elapsed_ms": stage_ms,
                "video_calls": 0,
            })
            return 1

        output_bytes = json.dumps(output, ensure_ascii=False, sort_keys=True).encode("utf-8")
        import hashlib

        result = {
            "state": "COMPLETED",
            "started_at": started_at,
            "ended_at": datetime.now().astimezone().isoformat(),
            "modal_function_call_id": call_id,
            "job_id": job_id,
            "generation_id": generation_id,
            "topic": topic,
            "language": "vi",
            "scene_count_requested": 5,
            "stage_elapsed_ms": stage_ms,
            "worker_elapsed_ms": round((time.perf_counter() - dispatch_started) * 1000, 3),
            "total_elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
            "result_sha256": hashlib.sha256(output_bytes).hexdigest(),
            "result": output,
            "video_calls": 0,
            "limitations": [
                "The deployed story worker accepts a topic, language, and fixed scene count; it does not consume the child's drawing pixels.",
                "StoryRun-lite currently exposes no parent script-generation API route; this is a direct worker call after API confirmation.",
            ],
        }
        write_json(RESULT_PATH, result)
        print(json.dumps({
            "result_file": RESULT_PATH.name,
            "state": result["state"],
            "modal_function_call_id": call_id,
            "elapsed_ms": result["total_elapsed_ms"],
            "storyboard_scenes": len((output.get("result") or {}).get("storyboard", []))
            if isinstance(output, dict) else None,
            "video_calls": 0,
        }, ensure_ascii=True))
        return 0
    finally:
        # Clean staged inputs only after a terminal worker response; timeouts keep them for safe reconciliation.
        if terminal and prefix is not None:
            try:
                poc._cleanup(volume, prefix)
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
