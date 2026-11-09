from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
BACKEND_SRC = REPO / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import modal  # noqa: E402
from sketch2life.infrastructure.ai.modal_function_client import (  # noqa: E402
    summarize_worker_call_logs,
)

RUNTIME = FEATURE / "evidence" / "nonvideo_modal_ai_reliability_20261106" / "runtime"
RECOVERY = RUNTIME / "recovery_after_wait_fix_20261106"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _refresh_call(call_id: str) -> dict[str, Any]:
    return summarize_worker_call_logs(
        modal.FunctionCall.from_id(call_id),
        max_entries=500,
        max_log_wait_seconds=3,
    )


def main() -> int:
    summary_path = RECOVERY / "summary.json"
    summary = _read_json(summary_path)
    results: list[dict[str, Any]] = []

    for workload in summary.get("workloads", []):
        if not isinstance(workload, dict):
            continue
        call_id = workload.get("call_id")
        evidence_file = workload.get("evidence_file")
        if (
            not isinstance(call_id, str)
            or not call_id.startswith("fc-")
            or not isinstance(evidence_file, str)
        ):
            continue
        logs = _refresh_call(call_id)
        workload["worker_log_summary"] = logs
        result_path = RECOVERY / evidence_file
        if result_path.is_file():
            result = _read_json(result_path)
            result["worker_log_summary"] = logs
            _write_json(result_path, result)
        results.append(
            {
                "workload": workload.get("workload"),
                "worker_logs_available": logs.get("worker_logs_available"),
                "worker_terminal_event": logs.get("worker_terminal_event"),
                "worker_last_stage": logs.get("worker_last_stage"),
                "worker_error_code": logs.get("worker_error_code"),
                "phase_event_count": len(logs.get("worker_phase_history", [])),
            }
        )

    _write_json(summary_path, summary)

    drawing_path = RUNTIME / "parent_api_20261106" / "parent_api_drawing_worker.json"
    if drawing_path.is_file():
        drawing = _read_json(drawing_path)
        call_id = drawing.get("call_id")
        if isinstance(call_id, str) and call_id.startswith("fc-"):
            drawing["worker_log_summary"] = _refresh_call(call_id)
            _write_json(drawing_path, drawing)

    print(json.dumps(results, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
