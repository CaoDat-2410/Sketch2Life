from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))

import run_ai_nonvideo_full_retest_20261104 as flow  # noqa: E402

OUTPUT_DIR = flow.ASSET_DIR
ARTIFACT_PATH = OUTPUT_DIR / "lesson_visual_candidate.png"
GUARD_PATH = OUTPUT_DIR / "lesson_visual_dispatch_guard.json"
RESULT_PATH = OUTPUT_DIR / "lesson_visual_result.json"


def main() -> int:
    if GUARD_PATH.exists() or RESULT_PATH.exists():
        raise SystemExit("Lesson visual already dispatched; refusing retry.")
    plan = flow.synthetic_approved_plan()
    data = {
        "schema_version": "sketch2life.lesson-visual-input.v1",
        "plan_revision_ref": plan["plan_revision_ref"],
        "content_hash": plan["content_hash"],
        "topic": plan["topic"],
        "steps": [
            {
                "step_index": item["step_index"],
                "instruction": item["action"],
                "placement": item["placement"],
            }
            for item in plan["drawing_steps"]
        ],
    }
    flow.dump_json(
        GUARD_PATH,
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "workload": "lesson.visual.generate",
            "created_at": flow.now_local(),
            "source_plan_revision_ref": plan["plan_revision_ref"],
            "source_plan_sha256": plan["content_hash"],
            "child_data_in_request": False,
            "max_attempts": 1,
        },
    )
    trace = json.loads(flow.TRACE_PATH.read_text(encoding="utf-8"))
    flow.VISUAL_PATH = ARTIFACT_PATH
    try:
        record = flow.invoke_modal_worker(
            trace,
            workload="lesson.visual.generate",
            app_name=flow.FLUX_APP,
            function_name="generate-approved-lesson-visual-candidate",
            request_data=data,
            timeout=600,
        )
        output = record["result"]
        asset = output.get("asset")
        if output.get("status") != "DRAFT" or not isinstance(asset, dict):
            raise RuntimeError("Lesson visual output did not return a DRAFT asset.")
        if (asset.get("width"), asset.get("height")) != (768, 432):
            raise RuntimeError("Lesson visual dimensions did not match 16:9.")
        result = {
            "outcome": "SUCCEEDED",
            "call_id": record["call_id"],
            "elapsed_ms": record["elapsed_ms"],
            "source_plan_revision_ref": plan["plan_revision_ref"],
            "source_plan_sha256": plan["content_hash"],
            "artifact": asset,
            "artifact_file": ARTIFACT_PATH.name,
            "review_required": True,
            "publishable": False,
            "video_called": False,
        }
        flow.dump_json(RESULT_PATH, result)
        print(json.dumps({"outcome": "SUCCEEDED", "call_id": record["call_id"], "elapsed_ms": record["elapsed_ms"], "artifact": ARTIFACT_PATH.name}, ensure_ascii=True))
        return 0
    except Exception as exc:
        result = {"outcome": "FAILED_OR_UNKNOWN", "error_type": type(exc).__name__, "ended_at": flow.now_local(), "video_called": False}
        flow.dump_json(RESULT_PATH, result)
        print(json.dumps(result, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
