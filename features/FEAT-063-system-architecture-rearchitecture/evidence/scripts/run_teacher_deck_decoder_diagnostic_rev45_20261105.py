from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
QUEUE_SCRIPT_DIR = SCRIPT.parent
BACKEND_SRC = REPO / "backend" / "src"
for import_path in (str(BACKEND_SRC), str(QUEUE_SCRIPT_DIR)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

import run_ai_nonvideo_30min_queue_retest_20261104 as qwen

OUTPUT_DIR = FEATURE / "evidence" / "assets" / "ai_nonvideo_ai_end_to_end_20261105" / "worker_fix_retest_04"
MAX_WAIT_SECONDS = 600


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise SystemExit("Diagnostic evidence exists; refusing a duplicate dispatch.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    qwen.OUT_DIR = OUTPUT_DIR
    qwen.WAIT_SECONDS = MAX_WAIT_SECONDS
    plan = qwen.flow.synthetic_approved_plan()
    started_at = _now()
    started = time.perf_counter()
    result = qwen.invoke_generic(
        workload="teacher.sketch-deck.generate",
        app="sketch2life-srs23-language-audio-dev",
        function="generate-teacher-sketch-deck",
        request_data=plan,
    )
    summary = {
        "started_at": started_at,
        "purpose": "Inspect shape-only diagnostics and tokenizer/model EOS IDs for one synthetic Teacher Deck call.",
        "synthetic_only": True,
        "video_called": False,
        "max_wait_seconds": MAX_WAIT_SECONDS,
        "outcome": result.get("outcome"),
        "call_id": result.get("call_id"),
        "elapsed_ms": result.get("elapsed_ms", round((time.perf_counter() - started) * 1000, 2)),
        "ended_at": _now(),
    }
    _save_json(OUTPUT_DIR / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
