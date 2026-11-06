from __future__ import annotations

import json
import sys
from pathlib import Path

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

RUNTIME = (
    FEATURE
    / "evidence"
    / "nonvideo_modal_ai_reliability_20261106"
    / "runtime"
    / "story_parser_srs_aligned_text_contract_retest_20261106"
)


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    summary_path = RUNTIME / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    call_id = summary.get("call_id")
    if not isinstance(call_id, str) or not call_id.startswith("fc-"):
        raise SystemExit("No valid Modal call id in the safe summary")

    worker_logs = summarize_worker_call_logs(
        modal.FunctionCall.from_id(call_id), max_log_wait_seconds=20
    )
    summary["worker_log_summary"] = worker_logs
    summary["worker_diagnostic_code"] = worker_logs["worker_diagnostic_code"]
    _write_json(summary_path, summary)

    result_path = RUNTIME / "story_generate_result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["worker_log_summary"] = worker_logs
    _write_json(result_path, result)

    print(
        json.dumps(
            {
                "call_id": call_id,
                "worker_diagnostic_code": worker_logs["worker_diagnostic_code"],
                "worker_diagnostic_details": worker_logs["worker_diagnostic_details"],
                "worker_last_stage": worker_logs["worker_last_stage"],
                "worker_error_code": worker_logs["worker_error_code"],
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
