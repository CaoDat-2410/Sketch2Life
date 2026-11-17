from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))

import run_ai_nonvideo_full_retest_20261104 as runner  # noqa: E402

OUTPUT_DIR = FEATURE / "evidence" / "assets" / "ai_nonvideo_full_retest_20261104"
TRACE_PATH = OUTPUT_DIR / "api_contract_non_ai_v2_trace.json"
RESULT_PATH = OUTPUT_DIR / "api_contract_non_ai_v2_results.json"
GUARD_PATH = OUTPUT_DIR / "api_contract_non_ai_v2_dispatch_guard.json"
ACTOR_SCOPE = "synthetic-parent-api-contract-retest-v2-20261104"


def _record(name: str, response: requests.Response, body: dict[str, Any], assessment: str) -> dict[str, Any]:
    return {
        "name": name,
        "method": response.request.method,
        "path": response.request.path_url.split("?", 1)[0],
        "status": response.status_code,
        "assessment": assessment,
        "response_code": body.get("code"),
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if any(path.exists() for path in (TRACE_PATH, RESULT_PATH, GUARD_PATH)):
        raise SystemExit("API contract evidence already exists; refusing duplicate mutations.")
    if not runner.DB_URL.endswith("/storyrun_lite_feat063_ai_api_contract_20261104"):
        raise SystemExit("A separate task-owned API contract database is required.")

    image_bytes = runner.IMAGE_PATH.read_bytes()
    image_sha = hashlib.sha256(image_bytes).hexdigest()
    flow_id = str(uuid.uuid4())
    trace: dict[str, Any] = {
        "started_at": runner.now_local(),
        "scope": "synthetic route contract checks; no AI dispatch",
        "actor_scope_ref": ACTOR_SCOPE,
        "ai_dispatches": 0,
        "video_calls": 0,
        "api_records": [],
    }
    runner.TRACE_PATH = TRACE_PATH
    runner.dump_json(GUARD_PATH, {"state": "NO_AI_DISPATCH_GUARD", "created_at": trace["started_at"], "max_ai_dispatches": 0})

    port = runner.get_free_port()
    base = f"http://127.0.0.1:{port}"
    session = requests.Session()
    records: list[dict[str, Any]] = []
    harness = runner.start_api_server(
        port=port,
        run_id=str(uuid.uuid4()),
        trace=trace,
        actor_scope_ref=ACTOR_SCOPE,
    )
    try:
        runner.wait_for_api(base, harness)

        response, body = runner.api_call(
            trace, session, name="reject_missing_age", method="POST", base_url=base,
            path="/v1/story-runs", headers={"Idempotency-Key": f"{flow_id}:missing-age"},
            json={"profile_ref": "synthetic-parent-demo"},
        )
        runner.require_status(response, body, {422}, "missing child age")
        records.append(_record("POST /v1/story-runs missing-age validation", response, body, "expected 422"))

        created, created_body = runner.api_call(
            trace, session, name="create_contract_run", method="POST", base_url=base,
            path="/v1/story-runs", headers={"Idempotency-Key": f"{flow_id}:create-run"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 60},
        )
        runner.require_status(created, created_body, {201}, "create run")
        run_ref = created_body["run_ref"]
        fetched, fetched_body = runner.api_call(
            trace, session, name="get_contract_run", method="GET", base_url=base,
            path=f"/v1/story-runs/{run_ref}",
        )
        runner.require_status(fetched, fetched_body, {200}, "get run")
        records.append(_record("POST /v1/story-runs", created, created_body, "passed 201"))
        records.append(_record("GET /v1/story-runs/{run_ref}", fetched, fetched_body, "passed 200"))

        invalid_attach, invalid_attach_body = runner.api_call(
            trace, session, name="reject_unknown_asset_without_ai", method="POST", base_url=base,
            path=f"/v1/story-runs/{run_ref}/assets",
            headers={"Idempotency-Key": f"{flow_id}:invalid-asset", "If-Match": fetched.headers.get("ETag", "")},
            json={"asset_ref": "unknown-synthetic-asset", "expected_revision": fetched_body["revision"]},
        )
        runner.require_status(invalid_attach, invalid_attach_body, {404, 409}, "unknown asset attach")
        records.append(_record("POST /v1/story-runs/{run_ref}/assets invalid reference", invalid_attach, invalid_attach_body, "expected no-AI rejection"))

        subject, subject_body = runner.api_call(
            trace, session, name="reject_subject_confirmation_before_analysis", method="POST", base_url=base,
            path=f"/v1/story-runs/{run_ref}/subject-confirmation",
            headers={"Idempotency-Key": f"{flow_id}:subject", "If-Match": fetched.headers.get("ETag", "")},
            json={"decision": "CONFIRM", "expected_understanding_revision": 1},
        )
        runner.require_status(subject, subject_body, {409}, "subject confirmation without VLM")
        records.append(_record("POST /v1/story-runs/{run_ref}/subject-confirmation", subject, subject_body, "expected 409 before AI result"))

        story, story_body = runner.api_call(
            trace, session, name="reject_story_before_subject_confirmation", method="POST", base_url=base,
            path=f"/v1/story-runs/{run_ref}/story-revisions",
            headers={"Idempotency-Key": f"{flow_id}:story-guard", "If-Match": fetched.headers.get("ETag", "")},
            json={"expected_understanding_revision": 1, "adult_confirmed_idea": "synthetic test"},
        )
        runner.require_status(story, story_body, {409}, "story guard without confirmed subject")
        records.append(_record("POST /v1/story-runs/{run_ref}/story-revisions no-dispatch guard", story, story_body, "expected 409 before AI dispatch"))

        missing_revision = str(uuid.uuid4())
        revision_get, revision_body = runner.api_call(
            trace, session, name="get_missing_story_revision", method="GET", base_url=base,
            path=f"/v1/story-runs/{run_ref}/story-revisions/{missing_revision}",
        )
        runner.require_status(revision_get, revision_body, {404}, "read missing revision")
        records.append(_record("GET /v1/story-runs/{run_ref}/story-revisions/{revision_ref}", revision_get, revision_body, "expected 404 for absent revision"))

        revision_confirm, revision_confirm_body = runner.api_call(
            trace, session, name="confirm_missing_story_revision", method="POST", base_url=base,
            path=f"/v1/story-runs/{run_ref}/story-revisions/{missing_revision}/confirmation",
            headers={"Idempotency-Key": f"{flow_id}:missing-confirm", "If-Match": fetched.headers.get("ETag", "")},
            json={"expected_revision": 1, "story_sha256": "0" * 64},
        )
        runner.require_status(revision_confirm, revision_confirm_body, {404}, "confirm missing revision")
        records.append(_record("POST /v1/story-runs/{run_ref}/story-revisions/{revision_ref}/confirmation", revision_confirm, revision_confirm_body, "expected 404 for absent revision"))

        cancelled, cancelled_body = runner.api_call(
            trace, session, name="cancel_contract_run", method="POST", base_url=base,
            path=f"/v1/story-runs/{run_ref}/cancel",
            headers={"Idempotency-Key": f"{flow_id}:cancel", "If-Match": fetched.headers.get("ETag", "")},
            json={"expected_revision": created_body["revision"]},
        )
        runner.require_status(cancelled, cancelled_body, {202}, "cancel run")
        records.append(_record("POST /v1/story-runs/{run_ref}/cancel", cancelled, cancelled_body, "passed 202"))

        upload_target, upload_target_body = runner.api_call(
            trace, session, name="create_upload_target_run", method="POST", base_url=base,
            path="/v1/story-runs", headers={"Idempotency-Key": f"{flow_id}:upload-target"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 72},
        )
        runner.require_status(upload_target, upload_target_body, {201}, "create upload target")
        upload, upload_body = runner.api_call(
            trace, session, name="create_upload_session", method="POST", base_url=base,
            path="/v1/upload-sessions", headers={"Idempotency-Key": f"{flow_id}:upload-create"},
            json={"target_ref": upload_target_body["run_ref"], "purpose": "RUN_ARTWORK", "media_type": "image/png", "expected_size_bytes": len(image_bytes), "expected_sha256": image_sha},
        )
        runner.require_status(upload, upload_body, {201}, "create upload session")
        records.append(_record("POST /v1/upload-sessions", upload, upload_body, "passed 201"))
        put_part, part_body = runner.api_call(
            trace, session, name="put_upload_part", method="PUT", base_url=base,
            path=f"/v1/upload-sessions/{upload_body['upload_ref']}/parts/1",
            headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(image_bytes)), "Content-SHA256": image_sha},
            data=image_bytes, timeout=120,
        )
        runner.require_status(put_part, part_body, {200}, "put upload part")
        records.append(_record("PUT /v1/upload-sessions/{upload_ref}/parts/{part_no}", put_part, part_body, "passed 200"))
        read_upload, read_upload_body = runner.api_call(
            trace, session, name="get_upload_before_complete", method="GET", base_url=base,
            path=f"/v1/upload-sessions/{upload_body['upload_ref']}",
        )
        runner.require_status(read_upload, read_upload_body, {200}, "get upload session")
        records.append(_record("GET /v1/upload-sessions/{upload_ref}", read_upload, read_upload_body, "passed 200"))
        complete, complete_body = runner.api_call(
            trace, session, name="complete_upload", method="POST", base_url=base,
            path=f"/v1/upload-sessions/{upload_body['upload_ref']}/complete",
            headers={"Idempotency-Key": f"{flow_id}:upload-complete", "If-Match": read_upload.headers.get("ETag", "")},
            json={"expected_size_bytes": len(image_bytes), "expected_sha256": image_sha}, timeout=180,
        )
        runner.require_status(complete, complete_body, {200, 202}, "complete upload")
        complete_status = complete_body.get("state")
        deadline = time.perf_counter() + 60
        while complete_status not in {"READY", "FAILED", "ABORTED", "EXPIRED"} and time.perf_counter() < deadline:
            read_upload, read_upload_body = runner.api_call(
                trace, session, name="poll_completed_upload", method="GET", base_url=base,
                path=f"/v1/upload-sessions/{upload_body['upload_ref']}",
            )
            runner.require_status(read_upload, read_upload_body, {200}, "poll upload")
            complete_status = read_upload_body.get("state")
            time.sleep(1)
        if complete_status != "READY":
            raise RuntimeError(f"Synthetic upload did not reach READY: {complete_status}")
        records.append(_record("POST /v1/upload-sessions/{upload_ref}/complete", complete, complete_body, f"passed; final state {complete_status}"))

        upload_target_state, upload_target_state_body = runner.api_call(
            trace, session, name="read_upload_target_run", method="GET", base_url=base,
            path=f"/v1/story-runs/{upload_target_body['run_ref']}",
        )
        runner.require_status(upload_target_state, upload_target_state_body, {200}, "read upload target run")
        upload_target_cancel, upload_target_cancel_body = runner.api_call(
            trace, session, name="cancel_upload_target_run", method="POST", base_url=base,
            path=f"/v1/story-runs/{upload_target_body['run_ref']}/cancel",
            headers={"Idempotency-Key": f"{flow_id}:cancel-upload-target", "If-Match": upload_target_state.headers.get("ETag", "")},
            json={"expected_revision": upload_target_state_body["revision"]},
        )
        runner.require_status(upload_target_cancel, upload_target_cancel_body, {202}, "cancel upload target run")

        delete_target, delete_target_body = runner.api_call(
            trace, session, name="create_delete_target_run", method="POST", base_url=base,
            path="/v1/story-runs", headers={"Idempotency-Key": f"{flow_id}:delete-target"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 48},
        )
        runner.require_status(delete_target, delete_target_body, {201}, "create delete target")
        pending, pending_body = runner.api_call(
            trace, session, name="create_pending_upload_for_delete", method="POST", base_url=base,
            path="/v1/upload-sessions", headers={"Idempotency-Key": f"{flow_id}:pending-upload"},
            json={"target_ref": delete_target_body["run_ref"], "purpose": "RUN_ARTWORK", "media_type": "image/png", "expected_size_bytes": len(image_bytes), "expected_sha256": image_sha},
        )
        runner.require_status(pending, pending_body, {201}, "create pending upload")
        deleted, deleted_body = runner.api_call(
            trace, session, name="delete_pending_upload", method="DELETE", base_url=base,
            path=f"/v1/upload-sessions/{pending_body['upload_ref']}",
            headers={"Idempotency-Key": f"{flow_id}:upload-delete", "If-Match": pending.headers.get("ETag", "")},
        )
        runner.require_status(deleted, deleted_body, {202}, "delete pending upload")
        records.append(_record("DELETE /v1/upload-sessions/{upload_ref}", deleted, deleted_body, "passed 202"))
    finally:
        runner.stop_api_server(harness)

    trace["ended_at"] = runner.now_local()
    trace["api_route_contracts"] = records
    runner.dump_json(TRACE_PATH, trace)
    result = {
        "started_at": trace["started_at"],
        "ended_at": trace["ended_at"],
        "actor_scope_ref": ACTOR_SCOPE,
        "task_database": "storyrun_lite_feat063_ai_api_contract_20261104",
        "api_dispatches": 0,
        "video_calls": 0,
        "routes_covered": len(records),
        "routes": records,
        "expected_limitations": [
            "AI success paths are reported separately; this contract pass used no AI dispatch.",
            "The full Parent asset-attach path is the separate Modal-backed run and ended VISION_OUTCOME_UNKNOWN.",
        ],
    }
    runner.dump_json(RESULT_PATH, result)
    print(json.dumps({"routes_covered": len(records), "api_dispatches": 0, "statuses": [{"name": r["name"], "status": r["status"]} for r in records]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
