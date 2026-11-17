from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import requests

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
ASSET_DIR = FEATURE / "evidence" / "assets" / "parent_generated_image_activity_retest_20261103"
IMAGE_PATH = ASSET_DIR / "synthetic_childlike_butterfly.png"
RESULT_PATH = ASSET_DIR / "storyrun_api_result.json"
GUARD_PATH = ASSET_DIR / "storyrun_execution_started.json"
DISPATCH_INTENT_PATH = ASSET_DIR / "drawing_dispatch_intent.json"
BASE_URL = "http://127.0.0.1:8002"
POLL_INTERVAL_SECONDS = 2.0
UPLOAD_WAIT_SECONDS = 90.0
VISION_READ_WAIT_SECONDS = 25.0


class UnknownRequestOutcome(RuntimeError):
    def __init__(self, step: str, error_type: str) -> None:
        super().__init__(f"{step} transport outcome is unknown ({error_type}); do not retry.")
        self.step = step
        self.error_type = error_type


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if GUARD_PATH.exists() or RESULT_PATH.exists():
        raise SystemExit("This task flow already started; refusing to create another run or dispatch.")
    if os.environ.get("STORYRUN_LITE_VISION_MODE") != "modal_function":
        raise SystemExit("API runtime is not pinned to the approved Modal function mode.")
    modal_run_id = os.environ.get("STORYRUN_LITE_MODAL_RUN_ID")
    if not modal_run_id or not re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        modal_run_id,
    ):
        raise SystemExit("A task-scoped Modal run UUID is not configured.")

    image_bytes = IMAGE_PATH.read_bytes()
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    started_at_local = datetime.now().astimezone()
    overall_started = time.perf_counter()
    flow_id = str(uuid.uuid4())
    trace: dict[str, object] = {
        "flow_id": flow_id,
        "started_at_local": started_at_local.isoformat(),
        "modal_run_id": modal_run_id,
        "image": {
            "file": IMAGE_PATH.name,
            "sha256": image_hash,
            "byte_length": len(image_bytes),
        },
        "records": [],
        "run_ref": None,
        "upload_ref": None,
        "final_run": None,
        "subject_confirmed": False,
        "confirmed_subject_label": None,
        "video_calls": 0,
    }
    write_json(GUARD_PATH, {
        "state": "TASK_FLOW_STARTED",
        "flow_id": flow_id,
        "created_at_local": started_at_local.isoformat(),
        "one_run_only": True,
        "one_drawing_inference_only": True,
        "video_enabled": False,
    })
    session = requests.Session()

    def call(name: str, method: str, path: str, **kwargs):
        started = time.perf_counter()
        try:
            response = session.request(method, BASE_URL + path, **kwargs)
        except requests.RequestException as exc:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            trace["records"].append({
                "step": name,
                "method": method.upper(),
                "path": path,
                "http_status": None,
                "elapsed_ms": elapsed_ms,
                "transport_outcome": "UNKNOWN_NO_RETRY",
                "exception_type": type(exc).__name__,
            })
            write_json(RESULT_PATH, trace)
            raise UnknownRequestOutcome(name, type(exc).__name__) from None
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        try:
            body = response.json()
        except Exception:
            body = {"body_prefix": response.text[:500]}
        header_subset = {
            key: response.headers.get(key)
            for key in ("ETag", "Location", "Retry-After", "X-Correlation-ID")
            if response.headers.get(key) is not None
        }
        record = {
            "step": name,
            "method": method.upper(),
            "path": path,
            "http_status": response.status_code,
            "elapsed_ms": elapsed_ms,
            "request_id": kwargs.get("headers", {}).get("X-Correlation-ID"),
            "headers": header_subset,
            "response": body,
        }
        trace["records"].append(record)
        write_json(RESULT_PATH, trace)
        return response, body, header_subset

    # Route availability probes are read-only. StoryRun-lite intentionally has no health/OpenAPI endpoints.
    for name, path in (("health_probe", "/health"), ("openapi_probe", "/openapi.json")):
        response, body, _ = call(name, "GET", path, timeout=8)
        if response.status_code != 404:
            raise RuntimeError(f"Unexpected {name} response: {response.status_code} {body}")

    run_response, run_body, run_headers = call(
        "create_story_run",
        "POST",
        "/v1/story-runs",
        headers={"Idempotency-Key": f"{flow_id}:create-run"},
        json={"profile_ref": "synthetic-parent-demo"},
        timeout=15,
    )
    if run_response.status_code != 201:
        raise RuntimeError(f"StoryRun create failed: {run_response.status_code} {run_body}")
    run_ref = run_body["run_ref"]
    trace["run_ref"] = run_ref

    upload_response, upload_body, upload_headers = call(
        "create_upload_session",
        "POST",
        "/v1/upload-sessions",
        headers={"Idempotency-Key": f"{flow_id}:create-upload"},
        json={
            "target_ref": run_ref,
            "purpose": "RUN_ARTWORK",
            "media_type": "image/png",
            "expected_size_bytes": len(image_bytes),
            "expected_sha256": image_hash,
        },
        timeout=15,
    )
    if upload_response.status_code != 201:
        raise RuntimeError(f"Upload session create failed: {upload_response.status_code} {upload_body}")
    upload_ref = upload_body["upload_ref"]
    trace["upload_ref"] = upload_ref

    part_response, part_body, part_headers = call(
        "upload_image_part",
        "PUT",
        f"/v1/upload-sessions/{upload_ref}/parts/1",
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(image_bytes)),
            "Content-SHA256": image_hash,
        },
        data=image_bytes,
        timeout=60,
    )
    if part_response.status_code != 200:
        raise RuntimeError(f"Upload part failed: {part_response.status_code} {part_body}")

    complete_response, complete_body, _ = call(
        "complete_upload_admission",
        "POST",
        f"/v1/upload-sessions/{upload_ref}/complete",
        headers={
            "Idempotency-Key": f"{flow_id}:complete-upload",
            "If-Match": part_headers.get("ETag", upload_headers.get("ETag", '"v1"')),
        },
        json={"expected_size_bytes": len(image_bytes), "expected_sha256": image_hash},
        timeout=60,
    )
    if complete_response.status_code not in {200, 202}:
        raise RuntimeError(f"Upload completion failed: {complete_response.status_code} {complete_body}")

    upload_deadline = time.perf_counter() + UPLOAD_WAIT_SECONDS
    admitted: dict[str, object] | None = None
    while time.perf_counter() < upload_deadline:
        poll_response, poll_body, _ = call(
            "poll_upload_admission",
            "GET",
            f"/v1/upload-sessions/{upload_ref}",
            timeout=15,
        )
        if poll_response.status_code != 200:
            raise RuntimeError(f"Upload poll failed: {poll_response.status_code} {poll_body}")
        if poll_body.get("state") == "READY":
            admitted = poll_body
            break
        if poll_body.get("state") in {"REJECTED", "FAILED", "ABORTED", "EXPIRED"}:
            raise RuntimeError(f"Upload admission ended in {poll_body.get('state')}: {poll_body}")
        time.sleep(POLL_INTERVAL_SECONDS)
    if admitted is None:
        raise RuntimeError("Upload admission did not become READY within the bounded wait.")

    attach_intent = {
        "state": "DISPATCH_INTENT_RECORDED",
        "flow_id": flow_id,
        "run_ref": run_ref,
        "modal_run_id": modal_run_id,
        "asset_ref": admitted.get("asset_ref"),
        "derived_asset_ref": admitted.get("derived_asset_ref"),
        "image_sha256": image_hash,
        "created_at_local": datetime.now().astimezone().isoformat(),
        "max_attempts": 1,
        "video_enabled": False,
    }
    write_json(DISPATCH_INTENT_PATH, attach_intent)
    try:
        attach_response, attach_body, _ = call(
            "attach_artwork_and_run_modal_vision",
            "POST",
            f"/v1/story-runs/{run_ref}/assets",
            headers={
                "Idempotency-Key": f"{flow_id}:attach-artwork-and-analyze-once",
                "If-Match": run_headers.get("ETag", '"v1"'),
            },
            json={"asset_ref": admitted["asset_ref"], "expected_revision": run_body["revision"]},
            timeout=(10, 980),
        )
    except UnknownRequestOutcome as exc:
        trace["vision_outcome"] = "UNKNOWN_NO_RETRY"
        trace["vision_transport_error_type"] = exc.error_type
        try:
            current_response, current_body, _ = call(
                "read_story_run_after_unknown_transport",
                "GET",
                f"/v1/story-runs/{run_ref}",
                timeout=15,
            )
            if current_response.status_code == 200:
                trace["final_run"] = current_body
        except UnknownRequestOutcome:
            pass
        trace["total_elapsed_ms"] = round((time.perf_counter() - overall_started) * 1000, 3)
        trace["ended_at_local"] = datetime.now().astimezone().isoformat()
        trace["video_calls"] = 0
        trace["limitations"] = [
            "The drawing request transport outcome is unknown; no retry was sent.",
            "The StoryRun-lite API has no story/script-generation operation.",
            "The activity-list route is a separate legacy demo session and is not attached to this StoryRun.",
        ]
        write_json(RESULT_PATH, trace)
        print(json.dumps({
            "result_file": RESULT_PATH.name,
            "run_ref": run_ref,
            "vision_outcome": "UNKNOWN_NO_RETRY",
            "transport_error_type": exc.error_type,
            "final_run_state": (trace.get("final_run") or {}).get("run_state")
            if isinstance(trace.get("final_run"), dict)
            else None,
            "video_calls": 0,
        }, ensure_ascii=True))
        return 2
    trace["attach_http_status"] = attach_response.status_code
    trace["attach_initial_response"] = attach_body

    run_deadline = time.perf_counter() + VISION_READ_WAIT_SECONDS
    final_run: dict[str, object] | None = None
    while time.perf_counter() < run_deadline:
        get_response, get_body, _ = call(
            "read_story_run_after_vision",
            "GET",
            f"/v1/story-runs/{run_ref}",
            timeout=15,
        )
        if get_response.status_code != 200:
            raise RuntimeError(f"StoryRun read failed: {get_response.status_code} {get_body}")
        final_run = get_body
        if get_body.get("run_state") == "SUBJECT_REVIEW":
            break
        if get_body.get("action_required") == "OPERATOR_REVIEW" or get_body.get("job_state") == "AWAITING_RECONCILIATION":
            break
        if get_body.get("run_state") in {"FAILED", "SAFETY_BLOCKED", "CANCELLED"}:
            break
        time.sleep(POLL_INTERVAL_SECONDS)

    if final_run is None:
        raise RuntimeError("No StoryRun state was captured after the drawing analysis request.")

    if final_run.get("run_state") == "SUBJECT_REVIEW":
        result = final_run.get("result") or {}
        subject_label = str(result.get("subject_label") or "")
        normalized = subject_label.casefold()
        if not any(token in normalized for token in ("bướm", "butterfly")):
            trace["adult_confirmation_gate"] = {
                "status": "NOT_CONFIRMED_MISMATCH",
                "model_subject_label": subject_label,
                "reason": "The synthetic image is visibly a butterfly; no mismatched label was confirmed.",
            }
        else:
            confirmation_response, confirmation_body, _ = call(
                "adult_subject_confirmation",
                "POST",
                f"/v1/story-runs/{run_ref}/subject-confirmation",
                headers={
                    "Idempotency-Key": f"{flow_id}:adult-confirm-subject",
                    "If-Match": f'"v{final_run["version"]}"',
                },
                json={
                    "decision": "CONFIRM",
                    "expected_understanding_revision": result["understanding_revision"],
                },
                timeout=15,
            )
            trace["subject_confirmed"] = confirmation_response.status_code == 200
            trace["confirmed_subject_label"] = subject_label
            trace["subject_confirmation_response"] = confirmation_body
            if confirmation_response.status_code != 200:
                raise RuntimeError(f"Adult subject confirmation failed: {confirmation_response.status_code} {confirmation_body}")
            final_response, final_body, _ = call(
                "read_story_run_after_confirmation",
                "GET",
                f"/v1/story-runs/{run_ref}",
                timeout=15,
            )
            if final_response.status_code == 200:
                final_run = final_body

    trace["final_run"] = final_run
    trace["total_elapsed_ms"] = round((time.perf_counter() - overall_started) * 1000, 3)
    trace["ended_at_local"] = datetime.now().astimezone().isoformat()
    trace["story_worker_ready"] = bool(trace.get("subject_confirmed"))
    trace["limitations"] = [
        "The StoryRun-lite API has no story/script-generation operation; the story worker is a separate call after adult subject confirmation.",
        "No video generation was requested or called.",
        "The activity-list route is a separate legacy demo session; it is not attached to this StoryRun.",
    ]
    write_json(RESULT_PATH, trace)
    print(json.dumps({
        "result_file": RESULT_PATH.name,
        "flow_id": flow_id,
        "run_ref": run_ref,
        "upload_ref": upload_ref,
        "subject_confirmed": trace.get("subject_confirmed"),
        "confirmed_subject_label": trace.get("confirmed_subject_label"),
        "final_run_state": (final_run or {}).get("run_state"),
        "final_job_state": (final_run or {}).get("job_state"),
        "video_calls": 0,
        "records": [
            {k: row.get(k) for k in ("step", "method", "path", "http_status", "elapsed_ms")}
            for row in trace["records"]
        ],
        "total_elapsed_ms": trace["total_elapsed_ms"],
    }, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
