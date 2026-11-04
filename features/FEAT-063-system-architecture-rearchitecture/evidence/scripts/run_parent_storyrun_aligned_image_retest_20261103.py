from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import requests

FEATURE = Path(__file__).resolve().parents[2]
ASSET_DIR = FEATURE / "evidence" / "assets" / "parent_generated_image_activity_retest_20261103"
IMAGE_PATH = ASSET_DIR / "synthetic_childlike_butterfly.png"
SEED_PATH = ASSET_DIR / "storyrun_recovery_seed.json"
RESULT_PATH = ASSET_DIR / "storyrun_aligned_api_result.json"
GUARD_PATH = ASSET_DIR / "storyrun_aligned_execution_started.json"
DISPATCH_PATH = ASSET_DIR / "storyrun_aligned_drawing_dispatch_intent.json"
BASE_URL = "http://127.0.0.1:8002"
UPLOAD_WAIT_SECONDS = 90.0
VISION_WAIT_SECONDS = 900.0
POLL_SECONDS = 2.0


class UnknownRequestOutcome(RuntimeError):
    def __init__(self, step: str, error_type: str) -> None:
        super().__init__(f"{step} transport outcome unknown; do not retry")
        self.step = step
        self.error_type = error_type


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if RESULT_PATH.exists() or GUARD_PATH.exists() or DISPATCH_PATH.exists():
        raise SystemExit("Aligned StoryRun already attempted; refusing a second run or dispatch.")
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    seed_body = seed.get("response", {})
    if seed.get("http_status") != 201 or not seed_body.get("run_ref"):
        raise SystemExit("No successful approved recovery run is available.")
    run_ref = seed_body["run_ref"]
    image = IMAGE_PATH.read_bytes()
    image_sha256 = hashlib.sha256(image).hexdigest()
    started_at = datetime.now().astimezone().isoformat()
    overall = time.perf_counter()
    trace: dict[str, object] = {
        "flow_id": seed.get("response", {}).get("run_ref"),
        "run_ref": run_ref,
        "started_at": started_at,
        "image": {"file": IMAGE_PATH.name, "sha256": image_sha256, "byte_length": len(image)},
        "records": [],
        "subject_confirmed": False,
        "video_calls": 0,
    }
    write_json(GUARD_PATH, {
        "state": "TASK_FLOW_STARTED",
        "run_ref": run_ref,
        "one_drawing_inference_only": True,
        "video_enabled": False,
    })
    session = requests.Session()

    def call(name: str, method: str, path: str, **kwargs):
        start = time.perf_counter()
        try:
            response = session.request(method, BASE_URL + path, **kwargs)
        except requests.RequestException as exc:
            row = {
                "step": name,
                "method": method.upper(),
                "path": path,
                "http_status": None,
                "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
                "transport_outcome": "UNKNOWN_NO_RETRY",
                "exception_type": type(exc).__name__,
            }
            trace["records"].append(row)
            write_json(RESULT_PATH, trace)
            raise UnknownRequestOutcome(name, type(exc).__name__) from None
        elapsed = round((time.perf_counter() - start) * 1000, 3)
        try:
            body = response.json()
        except ValueError:
            body = {"body_prefix": response.text[:500]}
        row = {
            "step": name,
            "method": method.upper(),
            "path": path,
            "http_status": response.status_code,
            "elapsed_ms": elapsed,
            "headers": {
                key: response.headers[key]
                for key in ("ETag", "Location", "Retry-After", "X-Correlation-ID")
                if key in response.headers
            },
            "response": body,
        }
        trace["records"].append(row)
        write_json(RESULT_PATH, trace)
        return response, body

    run_response, run_body = call("read_replacement_story_run", "GET", f"/v1/story-runs/{run_ref}", timeout=15)
    if run_response.status_code != 200 or run_body.get("run_state") != "INPUT_PROCESSING":
        raise RuntimeError(f"Replacement StoryRun not ready: {run_response.status_code} {run_body}")

    create_response, create_body = call(
        "create_upload_session",
        "POST",
        "/v1/upload-sessions",
        headers={"Idempotency-Key": f"{run_ref}:create-upload"},
        json={
            "target_ref": run_ref,
            "purpose": "RUN_ARTWORK",
            "media_type": "image/png",
            "expected_size_bytes": len(image),
            "expected_sha256": image_sha256,
        },
        timeout=15,
    )
    if create_response.status_code != 201:
        raise RuntimeError(f"Upload session create failed: {create_response.status_code} {create_body}")
    upload_ref = create_body["upload_ref"]

    part_response, part_body = call(
        "upload_image_part",
        "PUT",
        f"/v1/upload-sessions/{upload_ref}/parts/1",
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(image)),
            "Content-SHA256": image_sha256,
        },
        data=image,
        timeout=60,
    )
    if part_response.status_code != 200:
        raise RuntimeError(f"Image part upload failed: {part_response.status_code} {part_body}")

    complete_response, complete_body = call(
        "complete_upload_admission",
        "POST",
        f"/v1/upload-sessions/{upload_ref}/complete",
        headers={
            "Idempotency-Key": f"{run_ref}:complete-upload",
            "If-Match": part_response.headers.get("ETag", create_response.headers.get("ETag", '"v1"')),
        },
        json={"expected_size_bytes": len(image), "expected_sha256": image_sha256},
        timeout=60,
    )
    if complete_response.status_code not in {200, 202}:
        raise RuntimeError(f"Upload admission failed: {complete_response.status_code} {complete_body}")

    upload_deadline = time.perf_counter() + UPLOAD_WAIT_SECONDS
    admitted = None
    while time.perf_counter() < upload_deadline:
        response, body = call("poll_upload_admission", "GET", f"/v1/upload-sessions/{upload_ref}", timeout=15)
        if response.status_code != 200:
            raise RuntimeError(f"Upload status failed: {response.status_code} {body}")
        if body.get("state") == "READY":
            admitted = body
            break
        if body.get("state") in {"FAILED", "REJECTED", "ABORTED", "EXPIRED"}:
            raise RuntimeError(f"Upload admission terminal: {body.get('state')}")
        time.sleep(POLL_SECONDS)
    if not admitted:
        raise RuntimeError("Upload admission did not become READY within its bound.")

    current_response, current_body = call("read_story_run_before_attach", "GET", f"/v1/story-runs/{run_ref}", timeout=15)
    if current_response.status_code != 200 or current_body.get("run_state") != "INPUT_PROCESSING":
        raise RuntimeError(f"StoryRun changed before attach: {current_response.status_code} {current_body}")
    DISPATCH_PATH.write_text(
        json.dumps(
            {
                "state": "DISPATCH_INTENT_RECORDED",
                "run_ref": run_ref,
                "upload_ref": upload_ref,
                "asset_ref": admitted.get("asset_ref"),
                "derived_asset_ref": admitted.get("derived_asset_ref"),
                "image_sha256": image_sha256,
                "created_at": datetime.now().astimezone().isoformat(),
                "max_attempts": 1,
                "video_enabled": False,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    try:
        attach_response, attach_body = call(
            "attach_artwork_and_run_modal_vision_once",
            "POST",
            f"/v1/story-runs/{run_ref}/assets",
            headers={
                "Idempotency-Key": f"{run_ref}:attach-and-analyze-once",
                "If-Match": current_response.headers.get("ETag", f'"v{current_body["version"]}"'),
            },
            json={"asset_ref": admitted["asset_ref"], "expected_revision": current_body["revision"]},
            timeout=(10, 980),
        )
    except UnknownRequestOutcome as exc:
        trace["vision_outcome"] = "UNKNOWN_NO_RETRY"
        trace["vision_transport_error_type"] = exc.error_type
        attach_response = None
        attach_body = None
    if attach_response is not None and attach_response.status_code not in {200, 202}:
        raise RuntimeError(f"Vision attach failed: {attach_response.status_code} {attach_body}")

    deadline = time.perf_counter() + VISION_WAIT_SECONDS
    final_run = None
    while time.perf_counter() < deadline:
        response, body = call("poll_story_run_after_vision", "GET", f"/v1/story-runs/{run_ref}", timeout=15)
        if response.status_code != 200:
            raise RuntimeError(f"StoryRun poll failed: {response.status_code} {body}")
        final_run = body
        state = body.get("run_state")
        if state in {"SUBJECT_REVIEW", "PREPARATION_REVIEW", "FAILED", "SAFETY_BLOCKED", "CANCELLED"}:
            break
        if body.get("action_required") == "OPERATOR_REVIEW" or body.get("job_state") == "AWAITING_RECONCILIATION":
            break
        time.sleep(POLL_SECONDS)

    trace["attach_initial_response"] = attach_body
    trace["final_run"] = final_run
    if final_run and final_run.get("run_state") == "SUBJECT_REVIEW":
        result = final_run.get("result") or {}
        label = str(result.get("subject_label") or "")
        normalized = label.casefold()
        if any(token in normalized for token in ("b\u01b0\u1edbm", "butterfly")):
            confirm_response, confirm_body = call(
                "adult_subject_confirmation",
                "POST",
                f"/v1/story-runs/{run_ref}/subject-confirmation",
                headers={
                    "Idempotency-Key": f"{run_ref}:adult-confirm-subject",
                    "If-Match": f'"v{final_run["version"]}"',
                },
                json={
                    "decision": "CONFIRM",
                    "expected_understanding_revision": result["understanding_revision"],
                },
                timeout=15,
            )
            trace["subject_confirmed"] = confirm_response.status_code == 200
            trace["confirmed_subject_label"] = label
            trace["subject_confirmation_response"] = confirm_body
            if confirm_response.status_code != 200:
                raise RuntimeError(f"Adult confirmation failed: {confirm_response.status_code} {confirm_body}")
            final_response, final_body = call("read_story_run_after_confirmation", "GET", f"/v1/story-runs/{run_ref}", timeout=15)
            if final_response.status_code == 200:
                final_run = final_body
                trace["final_run"] = final_run
        else:
            trace["subject_mismatch"] = label

    trace["story_worker_ready"] = bool(trace.get("subject_confirmed"))
    trace["ended_at"] = datetime.now().astimezone().isoformat()
    trace["total_elapsed_ms"] = round((time.perf_counter() - overall) * 1000, 3)
    trace["limitations"] = [
        "The StoryRun-lite API has no script-generation route; the story worker is a separate call after adult confirmation.",
        "No video generation was requested or called.",
        "The activity-list route remains a separate legacy demo session, not attached to this StoryRun.",
    ]
    write_json(RESULT_PATH, trace)
    print(json.dumps({
        "result_file": RESULT_PATH.name,
        "run_ref": run_ref,
        "final_run_state": (final_run or {}).get("run_state"),
        "subject_confirmed": trace.get("subject_confirmed"),
        "confirmed_subject_label": trace.get("confirmed_subject_label"),
        "story_worker_ready": trace.get("story_worker_ready"),
        "video_calls": 0,
        "total_elapsed_ms": trace["total_elapsed_ms"],
        "records": [
            {key: row.get(key) for key in ("step", "method", "path", "http_status", "elapsed_ms")}
            for row in trace["records"]
        ],
    }, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
