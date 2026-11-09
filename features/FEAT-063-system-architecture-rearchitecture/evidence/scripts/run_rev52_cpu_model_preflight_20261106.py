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
BACKEND_SRC = REPO / "backend" / "src"
for value in (str(BACKEND_SRC),):
    if value not in sys.path:
        sys.path.insert(0, value)

import modal  # noqa: E402
from sketch2life.infrastructure.ai.modal_function_client import (  # noqa: E402
    summarize_worker_call_logs,
)

OUTPUT_DIR = (
    FEATURE / "evidence" / "nonvideo_modal_ai_reliability_20261106" / "runtime"
)
GUARD = OUTPUT_DIR / "cpu_model_preflight_dispatch_guard.json"
RESULT_PATH = OUTPUT_DIR / "cpu_model_preflight.json"
APPS = (
    ("drawing_vlm", "sketch2life-srs23-drawing-vlm-dev", "download-pinned-model"),
    ("flux3", "sketch2life-srs23-flux-image-dev", "download-flux-pinned-model"),
    (
        "language_audio",
        "sketch2life-srs23-language-audio-dev",
        "download-language-audio-models",
    ),
    (
        "sam2",
        "sketch2life-srs23-drawing-segment-dev",
        "download-sam2-hiera-small-checkpoint",
    ),
)


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _safe_output(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"output_type": type(value).__name__}
    result: dict[str, Any] = {"status": value.get("status")}
    models = value.get("models")
    if isinstance(models, list):
        result["model_count"] = len(models)
        result["model_statuses"] = [
            item.get("status")
            for item in models
            if isinstance(item, dict) and isinstance(item.get("status"), str)
        ]
    return result


def main() -> int:
    if GUARD.exists() or RESULT_PATH.exists():
        raise SystemExit("CPU model preflight guard exists; refusing duplicate calls.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GUARD.write_text(
        json.dumps(
            {
                "state": "DISPATCH_INTENT_RECORDED",
                "created_at": _now(),
                "gpu_inference_called": False,
                "video_called": False,
                "max_attempts_per_function": 1,
                "functions": [function for _, _, function in APPS],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    results: list[dict[str, Any]] = []
    for name, app_name, function_name in APPS:
        started = time.perf_counter()
        record: dict[str, Any] = {
            "check": name,
            "app": app_name,
            "function": function_name,
            "started_at": _now(),
            "outcome": "DISPATCH_FAILED_NO_CALL",
            "gpu_inference_called": False,
            "video_called": False,
        }
        call = None
        try:
            function = modal.Function.from_name(
                app_name, function_name, environment_name="dev"
            )
            call = function.spawn()
            call_id = getattr(call, "object_id", None)
            record["call_id"] = call_id
            if not isinstance(call_id, str) or not call_id.startswith("fc-"):
                record["outcome"] = "UNKNOWN_NO_CALL_ID"
            else:
                output = call.get(timeout=600)
                record["outcome"] = "SUCCEEDED"
                record["result"] = _safe_output(output)
        except Exception as exc:  # noqa: BLE001 - keep only a safe exception class.
            record["outcome"] = "FAILED_TERMINAL" if call is not None else "DISPATCH_FAILED_NO_CALL"
            record["error_type"] = type(exc).__name__
        record["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
        record["ended_at"] = _now()
        if call is not None:
            try:
                record["worker_log_summary"] = summarize_worker_call_logs(
                    call, max_log_wait_seconds=20
                )
            except Exception as exc:  # noqa: BLE001 - retain safe exception class only.
                record["worker_log_summary"] = {
                    "worker_logs_available": False,
                    "worker_failure_boundary": "worker_log_fetch_exception",
                    "error_type": type(exc).__name__,
                }
        results.append(record)
        RESULT_PATH.write_text(
            json.dumps(
                {
                    "started_at": results[0]["started_at"],
                    "ended_at": _now(),
                    "gpu_inference_called": False,
                    "video_called": False,
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "check": name,
                    "outcome": record["outcome"],
                    "call_id": record.get("call_id"),
                    "elapsed_ms": record["elapsed_ms"],
                    "worker_terminal_event": (record.get("worker_log_summary") or {}).get(
                        "worker_terminal_event"
                    ),
                    "worker_last_stage": (record.get("worker_log_summary") or {}).get(
                        "worker_last_stage"
                    ),
                    "worker_error_code": (record.get("worker_log_summary") or {}).get(
                        "worker_error_code"
                    ),
                },
                ensure_ascii=True,
            ),
            flush=True,
        )
    return 0 if all(item["outcome"] == "SUCCEEDED" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
