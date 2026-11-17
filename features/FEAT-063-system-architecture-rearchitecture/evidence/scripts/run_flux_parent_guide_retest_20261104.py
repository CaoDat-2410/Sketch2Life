from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))

import run_ai_nonvideo_full_retest_20261104 as flow  # noqa: E402

OUTPUT_DIR = flow.ASSET_DIR
ARTIFACT_PATH = OUTPUT_DIR / "parent_sketch_guide_candidate.png"
DISPATCH_GUARD = OUTPUT_DIR / "parent_sketch_guide_dispatch_guard.json"


def main() -> int:
    if DISPATCH_GUARD.exists():
        raise SystemExit("Parent Sketch Guide already dispatched; refusing retry.")
    flow.dump_json(
        DISPATCH_GUARD,
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "workload": "parent.sketch-guide.generate",
            "created_at": flow.now_local(),
            "input_policy": "generic topic and difficulty only; no child/profile/artwork data",
            "max_attempts": 1,
        },
    )
    trace = json.loads(flow.TRACE_PATH.read_text(encoding="utf-8"))
    flow.VISUAL_PATH = ARTIFACT_PATH
    try:
        record = flow.invoke_modal_worker(
            trace,
            workload="parent.sketch-guide.generate",
            app_name=flow.FLUX_APP,
            function_name="generate-line-sketch-guide-candidate",
            request_data={"topic": "butterfly", "difficulty": "beginner", "step_count": 3},
            timeout=600,
        )
        result = record["result"]
        if result.get("workload") != "parent.sketch-guide.generate":
            raise RuntimeError("Parent Sketch Guide output workload mismatch.")
        asset = result.get("asset")
        if not isinstance(asset, dict) or (asset.get("width"), asset.get("height")) != (768, 512):
            raise RuntimeError("Parent Sketch Guide image dimensions are invalid.")
        flow.dump_json(
            OUTPUT_DIR / "parent_sketch_guide_provenance.json",
            {
                "status": "DRAFT",
                "source_topic": "butterfly",
                "source_artifact_sha256": asset["sha256"],
                "provider_model": result.get("model"),
                "provider_call_id": record["call_id"],
                "width": asset["width"],
                "height": asset["height"],
                "review_required": True,
                "publishable": False,
                "child_data_in_request": False,
            },
        )
        print(json.dumps({"outcome": record["outcome"], "call_id": record["call_id"], "elapsed_ms": record["elapsed_ms"], "artifact": ARTIFACT_PATH.name}, ensure_ascii=True))
        return 0
    except Exception as exc:
        print(json.dumps({"outcome": "FAILED_OR_UNKNOWN", "error_type": type(exc).__name__}, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
