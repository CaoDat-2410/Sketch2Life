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
RESULT_PATH = ASSET_DIR / "api_mutation_results.json"
GUARD_PATH = ASSET_DIR / "api_mutation_corrected_guard.json"
ACTOR_SCOPE = "synthetic-parent-api-remainder-20261104"


def load_runner():
    spec = importlib.util.spec_from_file_location("feat063_api_mutation_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the approved API harness.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    if not TRACE_PATH.is_file() or RESULT_PATH.exists() or GUARD_PATH.exists():
        raise SystemExit("API mutation evidence is missing or already exists; refusing to replay.")
    trace: dict[str, Any] = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
    parent = trace.get("parent_flow") or {}
    flow_id = parent.get("flow_id")
    if not flow_id:
        raise SystemExit("The synthetic Parent flow identifier is missing.")

    runner.dump_json(
        GUARD_PATH,
        {"state": "API_MUTATION_CHECKS_STARTED", "actor_scope_ref": ACTOR_SCOPE, "created_at": runner.now_local(), "ai_dispatches": 0},
    )
    port = runner.get_free_port()
    base_url = f"http://127.0.0.1:{port}"
    session = requests.Session()
    start_index = len(trace.get("api_records", []))
    harness = runner.start_api_server(
        port=port,
        run_id=parent.get("run_ref", "00000000-0000-4000-8000-000000000001"),
        trace=trace,
        actor_scope_ref=ACTOR_SCOPE,
    )
    try:
        runner.wait_for_api(base_url, harness)
        created, created_body = runner.api_call(
            trace, session, name="create_run_for_cancel_route", method="POST",
            base_url=base_url, path="/v1/story-runs",
            headers={"Idempotency-Key": f"{flow_id}:api-remainder-cancel-create"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 48},
        )
        runner.require_status(created, created_body, {201}, "create synthetic run for cancel")
        cancelled, cancelled_body = runner.api_call(
            trace, session, name="cancel_run_route", method="POST", base_url=base_url,
            path=f"/v1/story-runs/{created_body['run_ref']}/cancel",
            headers={
                "Idempotency-Key": f"{flow_id}:api-remainder-cancel",
                "If-Match": created.headers.get("ETag", ""),
            },
            json={"expected_revision": created_body["revision"]},
        )
        runner.require_status(cancelled, cancelled_body, {202}, "cancel synthetic run")

        upload_target, upload_target_body = runner.api_call(
            trace, session, name="create_run_for_upload_abort_route", method="POST",
            base_url=base_url, path="/v1/story-runs",
            headers={"Idempotency-Key": f"{flow_id}:api-remainder-upload-target"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 72},
        )
        runner.require_status(upload_target, upload_target_body, {201}, "create synthetic run for upload abort")
        upload, upload_body = runner.api_call(
            trace, session, name="create_upload_session_route", method="POST",
            base_url=base_url, path="/v1/upload-sessions",
            headers={"Idempotency-Key": f"{flow_id}:api-remainder-upload-create"},
            json={
                "target_ref": upload_target_body["run_ref"],
                "purpose": "RUN_ARTWORK",
                "media_type": "image/png",
                "expected_size_bytes": parent["image"]["size_bytes"],
                "expected_sha256": parent["image"]["sha256"],
            },
        )
        runner.require_status(upload, upload_body, {201}, "create upload session")
        aborted, aborted_body = runner.api_call(
            trace, session, name="abort_upload_session_route", method="DELETE",
            base_url=base_url, path=f"/v1/upload-sessions/{upload_body['upload_ref']}",
            headers={
                "Idempotency-Key": f"{flow_id}:api-remainder-upload-abort",
                "If-Match": upload.headers.get("ETag", ""),
            },
        )
        runner.require_status(aborted, aborted_body, {202}, "abort upload session")

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
            "actor_scope_ref": ACTOR_SCOPE,
            "ai_dispatches": 0,
            "api_records": added_records,
            "not_mounted": ["GET /health", "GET /openapi.json"],
        },
    )
    runner.dump_json(
        GUARD_PATH,
        {"state": "API_MUTATION_CHECKS_FINISHED", "actor_scope_ref": ACTOR_SCOPE, "ended_at": runner.now_local(), "ai_dispatches": 0},
    )
    print(json.dumps({"api_checks": len(added_records), "statuses": [{"name": r["name"], "status": r["status"]} for r in added_records], "ai_dispatches": 0}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
