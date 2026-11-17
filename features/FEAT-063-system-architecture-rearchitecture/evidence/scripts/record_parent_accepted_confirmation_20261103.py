from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import requests

FEATURE = Path(__file__).resolve().parents[2]
ASSET_DIR = FEATURE / "evidence" / "assets" / "parent_generated_image_activity_retest_20261103"
RESULT_PATH = ASSET_DIR / "storyrun_aligned_api_result.json"
BASE_URL = "http://127.0.0.1:8002"


def main() -> int:
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    if result.get("confirmation_followup_recorded"):
        raise SystemExit("Read-only confirmation follow-up already recorded.")
    confirmation = next(
        (row for row in reversed(result.get("records", [])) if row.get("step") == "adult_subject_confirmation"),
        None,
    )
    if not confirmation or confirmation.get("http_status") != 202:
        raise SystemExit("No accepted asynchronous confirmation response to verify.")
    run_ref = result["run_ref"]
    started = time.perf_counter()
    try:
        response = requests.get(f"{BASE_URL}/v1/story-runs/{run_ref}", timeout=15)
    except requests.RequestException as exc:
        row = {
            "step": "read_story_run_after_accepted_confirmation",
            "method": "GET",
            "path": f"/v1/story-runs/{run_ref}",
            "http_status": None,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "transport_outcome": "UNKNOWN_NO_RETRY",
            "exception_type": type(exc).__name__,
        }
        result.setdefault("records", []).append(row)
        result["confirmation_followup_recorded"] = True
        result["story_worker_ready"] = False
        RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise SystemExit("Follow-up read outcome unknown; no retry or story dispatch.") from None
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    try:
        body = response.json()
    except ValueError:
        body = {"body_prefix": response.text[:500]}
    row = {
        "step": "read_story_run_after_accepted_confirmation",
        "method": "GET",
        "path": f"/v1/story-runs/{run_ref}",
        "http_status": response.status_code,
        "elapsed_ms": elapsed_ms,
        "headers": {
            key: response.headers[key]
            for key in ("ETag", "Location", "X-Correlation-ID")
            if key in response.headers
        },
        "response": body,
    }
    result.setdefault("records", []).append(row)
    result["confirmation_followup_recorded"] = True
    result["adult_confirmation_accepted"] = response.status_code == 200 and body.get("run_state") == "PREPARATION_REVIEW"
    result["subject_confirmed"] = bool(result["adult_confirmation_accepted"])
    previous_subject = ((result.get("final_run") or {}).get("result") or {}).get("subject_label")
    result["confirmed_subject_label"] = previous_subject if result["subject_confirmed"] else None
    result["final_run"] = body
    result["story_worker_ready"] = bool(
        result["subject_confirmed"]
        and body.get("run_state") == "PREPARATION_REVIEW"
        and body.get("job_state") == "SUCCEEDED"
        and not body.get("error")
    )
    result["ended_at"] = datetime.now().astimezone().isoformat()
    result["limitations"] = [
        "The StoryRun-lite API has no script-generation route; the story worker is a separate call after adult confirmation.",
        "No video generation was requested or called.",
        "The activity-list route remains a separate legacy demo session, not attached to this StoryRun.",
    ]
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "followup_http_status": response.status_code,
        "elapsed_ms": elapsed_ms,
        "run_state": body.get("run_state"),
        "job_state": body.get("job_state"),
        "confirmed_subject_label": result.get("confirmed_subject_label"),
        "story_worker_ready": result.get("story_worker_ready"),
    }, ensure_ascii=True))
    return 0 if result["story_worker_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
