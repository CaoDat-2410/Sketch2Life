from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))

import run_ai_nonvideo_full_retest_20261104 as flow  # noqa: E402


def main() -> int:
    for workload_prefix in ("teacher_sketch-deck_generate_", "lesson_visual_generate_"):
        if any(flow.ASSET_DIR.glob(f"{workload_prefix}*_dispatch_intent.json")):
            raise SystemExit(f"Guarded {workload_prefix} attempt already exists; refusing duplicate dispatch.")
    trace = json.loads(flow.TRACE_PATH.read_text(encoding="utf-8"))
    trace.setdefault("modal_workers", [])
    trace["video_called"] = False
    try:
        flow.teacher_deck_flow(trace)
    except Exception as exc:
        trace["teacher_deck"] = {"status": "FAILED_OR_UNKNOWN", "error_type": type(exc).__name__}
        flow.dump_json(flow.TRACE_PATH, trace)
        print(json.dumps({"teacher_deck": trace["teacher_deck"], "error_type": type(exc).__name__}))
        return 1
    print(json.dumps({"teacher_deck": trace.get("teacher_deck"), "video_called": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
