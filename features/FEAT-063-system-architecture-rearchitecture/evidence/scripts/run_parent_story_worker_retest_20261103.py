from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = SCRIPT.parents[4]
OUT = FEATURE / "evidence" / "assets" / "parent_image_to_script_retest_20261103"
INTENT = OUT / "story_worker_dispatch_intent.json"
RESULT = OUT / "qwen_story_storyboard_result.json"
SUMMARY = OUT / "story_worker_summary.json"
POC = FEATURE / "evidence" / "scripts" / "run_modal_ai_hosting_poc.py"

OUT.mkdir(parents=True, exist_ok=True)
if INTENT.exists():
    raise SystemExit("Story worker dispatch intent already exists; refusing another call.")
checkpoint = json.loads((OUT / "checkpoint.json").read_text(encoding="utf-8"))
if checkpoint.get("vision_call_outcome") != "HTTP_RESPONSE":
    raise SystemExit("Vision API result has not been recorded; refusing detached worker call.")
run = checkpoint.get("post_vision_run") or {}
if run.get("job_state") != "AWAITING_RECONCILIATION":
    raise SystemExit("Expected the recorded ambiguous vision outcome; refusing fallback call.")

intent = {
    "state": "DISPATCH_INTENT_RECORDED",
    "workload": "story.generate",
    "app": "sketch2life-srs23-language-audio-dev",
    "function": "generate-story-and-storyboard",
    "topic": "bướm",
    "language": "vi",
    "scene_count": 5,
    "input_source": "visually verified synthetic butterfly fixture label; detached from unresolved Parent API run",
    "parent_subject_confirmation_api_passed": False,
    "video_inference": False,
}
INTENT.write_text(json.dumps(intent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

spec = importlib.util.spec_from_file_location("modal_ai_hosting_poc", POC)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load the existing approved Modal worker helper.")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
module.OUTPUT_DIR = OUT
started = time.perf_counter()
captured = io.StringIO()
try:
    with contextlib.redirect_stdout(captured):
        module.run_story()
except Exception as exc:  # noqa: BLE001 - no retry after a possible dispatch
    outcome = {
        **intent,
        "state": "UNKNOWN_NO_RETRY",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "exception_type": type(exc).__name__,
        "exception_message": str(exc)[:500],
        "worker_output_file_exists": RESULT.exists(),
    }
    SUMMARY.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, ensure_ascii=False))
    raise SystemExit(2) from None

worker = json.loads(RESULT.read_text(encoding="utf-8"))
canonical = json.dumps(worker.get("result"), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
result_payload = worker.get("result")
outcome = {
    **intent,
    "state": "SUCCEEDED",
    "elapsed_seconds_including_cold_start": round(time.perf_counter() - started, 3),
    "input_manifest_sha256": worker.get("input_manifest_sha256"),
    "result_sha256": hashlib.sha256(canonical).hexdigest(),
    "result_top_level_keys": sorted(result_payload) if isinstance(result_payload, dict) else [],
    "result_file": RESULT.name,
    "result_bytes": RESULT.stat().st_size,
}
SUMMARY.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(outcome, ensure_ascii=False))
