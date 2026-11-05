from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
ASSET_DIR = FEATURE / "evidence" / "assets" / "ai_flow_srs_alignment_20261104"
RUNNER_PATH = SCRIPT.with_name("run_ai_flow_srs_alignment_20261104.py")
TRACE_PATH = ASSET_DIR / "poc_run_trace.json"
RESULT_PATH = ASSET_DIR / "remaining_api_results.json"
GUARD_PATH = ASSET_DIR / "remaining_api_dispatch_guard.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("feat063_remaining_api_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the approved API harness.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    if not TRACE_PATH.is_file() or RESULT_PATH.exists() or GUARD_PATH.exists():
        raise SystemExit("API remainder evidence is missing or already exists; refusing to replay.")
    trace: dict[str, Any] = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
    parent = trace.get("parent_flow") or {}
    run_ref = parent.get("run_ref")
    flow_id = parent.get("flow_id")
    story_record = next(
        (item for item in trace.get("api_records", []) if item.get("name") == "generate_parent_story_once"),
        None,
    )
    if not run_ref or not flow_id or not story_record or story_record.get("status") != 202:
        raise SystemExit("Expected the persisted synthetic run and terminal story response are not present.")
    story_ref = (story_record.get("response") or {}).get("story_revision_ref")
    if not story_ref:
        raise SystemExit("The terminal story response did not identify its pollable revision.")

    runner.dump_json(
        GUARD_PATH,
        {"state": "API_REMAINDER_STARTED", "run_ref": run_ref, "created_at": runner.now_local(), "ai_dispatches": 0},
    )
    port = runner.get_free_port()
    base_url = f"http://127.0.0.1:{port}"
    session = requests.Session()
    start_index = len(trace.get("api_records", []))
    harness = runner.start_api_server(port=port, run_id=run_ref, trace=trace)
    try:
        runner.wait_for_api(base_url, harness)
        current, current_body = runner.api_call(
            trace, session, name="read_run_for_remaining_api_checks", method="GET",
            base_url=base_url, path=f"/v1/story-runs/{run_ref}",
        )
        runner.require_status(current, current_body, {200}, "read run for remaining checks")
        revision, revision_body = runner.api_call(
            trace, session, name="read_story_revision_after_terminal_worker_error", method="GET",
            base_url=base_url, path=f"/v1/story-runs/{run_ref}/story-revisions/{story_ref}",
        )
        runner.require_status(revision, revision_body, {200}, "read terminal story revision")
        confirmation, confirmation_body = runner.api_call(
            trace, session, name="reject_confirmation_of_non_draft_story", method="POST",
            base_url=base_url,
            path=f"/v1/story-runs/{run_ref}/story-revisions/{story_ref}/confirmation",
            headers={
                "Idempotency-Key": f"{flow_id}:confirm-non-draft-negative-check",
                "If-Match": current.headers.get("ETag", ""),
            },
            json={"expected_revision": revision_body["revision_no"], "story_sha256": "0" * 64},
        )
        runner.require_status(confirmation, confirmation_body, {409}, "reject confirmation of non-draft")

        cancel_create, cancel_body = runner.api_call(
            trace, session, name="create_run_for_cancel_route_check", method="POST",
            base_url=base_url, path="/v1/story-runs",
            headers={"Idempotency-Key": f"{flow_id}:remaining-cancel-create"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 48},
        )
        runner.require_status(cancel_create, cancel_body, {201}, "create run for cancel route")
        cancel, cancel_result = runner.api_call(
            trace, session, name="cancel_run_route_check", method="POST", base_url=base_url,
            path=f"/v1/story-runs/{cancel_body['run_ref']}/cancel",
            headers={
                "Idempotency-Key": f"{flow_id}:remaining-cancel",
                "If-Match": cancel_create.headers.get("ETag", ""),
            },
            json={"expected_revision": cancel_body["revision"]},
        )
        runner.require_status(cancel, cancel_result, {202}, "cancel run route")

        upload_target, upload_target_body = runner.api_call(
            trace, session, name="create_run_for_upload_delete_route_check", method="POST",
            base_url=base_url, path="/v1/story-runs",
            headers={"Idempotency-Key": f"{flow_id}:remaining-upload-target"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 72},
        )
        runner.require_status(upload_target, upload_target_body, {201}, "create run for upload delete route")
        upload_create, upload_body = runner.api_call(
            trace, session, name="create_upload_for_delete_route_check", method="POST",
            base_url=base_url, path="/v1/upload-sessions",
            headers={"Idempotency-Key": f"{flow_id}:remaining-upload-create"},
            json={
                "target_ref": upload_target_body["run_ref"],
                "purpose": "RUN_ARTWORK",
                "media_type": "image/png",
                "expected_size_bytes": parent["image"]["size_bytes"],
                "expected_sha256": parent["image"]["sha256"],
            },
        )
        runner.require_status(upload_create, upload_body, {201}, "create upload for delete route")
        upload_delete, upload_delete_body = runner.api_call(
            trace, session, name="delete_upload_session_route_check", method="DELETE",
            base_url=base_url, path=f"/v1/upload-sessions/{upload_body['upload_ref']}",
            headers={
                "Idempotency-Key": f"{flow_id}:remaining-upload-delete",
                "If-Match": upload_create.headers.get("ETag", ""),
            },
        )
        runner.require_status(upload_delete, upload_delete_body, {202}, "delete upload session route")

        for name, path in (("health_route_not_mounted", "/health"), ("openapi_route_not_mounted", "/openapi.json")):
            response, body = runner.api_call(
                trace, session, name=name, method="GET", base_url=base_url, path=path
            )
            runner.require_status(response, body, {404}, name)
    finally:
        runner.stop_api_server(harness)

    added_records = trace.get("api_records", [])[start_index:]
    runner.dump_json(TRACE_PATH, trace)
    runner.dump_json(
        RESULT_PATH,
        {
            "run_ref": run_ref,
            "story_revision_ref": story_ref,
            "ai_dispatches": 0,
            "api_records": added_records,
            "expected_business_rule_rejection": "non-DRAFT story confirmation returned 409",
            "not_mounted": ["GET /health", "GET /openapi.json"],
        },
    )
    runner.dump_json(
        GUARD_PATH,
        {"state": "API_REMAINDER_FINISHED", "run_ref": run_ref, "ended_at": runner.now_local(), "ai_dispatches": 0},
    )
    print(json.dumps({"api_checks": len(added_records), "statuses": [{"name": r["name"], "status": r["status"]} for r in added_records], "ai_dispatches": 0}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
