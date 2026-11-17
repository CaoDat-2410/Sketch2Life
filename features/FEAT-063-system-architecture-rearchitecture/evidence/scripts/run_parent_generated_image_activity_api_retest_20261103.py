from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = SCRIPT.parents[4]
ASSET_DIR = FEATURE / "evidence" / "assets" / "parent_generated_image_activity_retest_20261103"
IMAGE_PATH = ASSET_DIR / "synthetic_childlike_butterfly.png"
RESULT_PATH = ASSET_DIR / "activity_api_result.json"
TEST_MODULE_PATH = REPO / "backend" / "tests" / "contract" / "test_live_image_demo_api.py"
sys.path.insert(0, str(REPO / "backend" / "src"))


def load_contract_harness():
    spec = importlib.util.spec_from_file_location("live_image_demo_api_contract_fixture", TEST_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the existing API contract test fixture.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_contract_harness()
    image_bytes = IMAGE_PATH.read_bytes()
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    session_id = str(uuid.uuid4())
    vision = module._CountingVision(label="bướm")
    client, _ = module._client(vision=vision)
    records: list[dict[str, object]] = []
    responses: dict[str, object] = {}
    started_at_local = datetime.now().astimezone()
    started_all = time.perf_counter()

    def record(name: str, method: str, path: str, **kwargs):
        started = time.perf_counter()
        response = getattr(client, method)(path, **kwargs)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        try:
            body = response.json()
        except Exception:
            body = {"body_prefix": response.text[:500]}
        records.append({
            "step": name,
            "method": method.upper(),
            "path": path,
            "http_status": response.status_code,
            "application_status": body.get("status") if isinstance(body, dict) else None,
            "failure_code": (body.get("failure") or {}).get("code") if isinstance(body, dict) else None,
            "observed_session_version": body.get("observed_session_version") if isinstance(body, dict) else None,
            "elapsed_ms": elapsed_ms,
        })
        responses[name] = body
        return response, body

    run_request_id = str(uuid.uuid4())
    created, create_body = record(
        "create_session",
        "post",
        "/v1/sessions",
        json={
            "request_id": run_request_id,
            "idempotency_key": f"{session_id}:create",
            "session_id": session_id,
            "expected_session_version": 0,
            "actor_ref": "demo:local",
            "payload": {"operation": "CREATE_SESSION"},
        },
    )
    if created.status_code not in {200, 201}:
        raise RuntimeError(f"create_session failed: {created.status_code} {created.text[:500]}")
    version = create_body["observed_session_version"]

    image_headers = {
        "X-Request-ID": str(uuid.uuid4()),
        "X-Expected-Session-Version": str(version),
        "Idempotency-Key": f"{session_id}:upload-image",
        "X-Actor-Ref": "demo:local",
        "X-Synthetic-Non-Child-Confirmed": "true",
    }
    uploaded, upload_body = record(
        "upload_generated_image",
        "post",
        f"/v1/sessions/{session_id}/media/image",
        headers=image_headers,
        files={"image": (IMAGE_PATH.name, image_bytes, "image/png")},
    )
    if uploaded.status_code != 200 or upload_body.get("status") != "SUCCEEDED":
        raise RuntimeError(f"upload failed: {uploaded.status_code} {json.dumps(upload_body)[:700]}")
    version = upload_body["observed_session_version"]

    understood, understand_body = record(
        "fixture_vision_understanding",
        "post",
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": str(uuid.uuid4()),
            "idempotency_key": f"{session_id}:understanding",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )
    if understood.status_code != 200 or understand_body.get("status") != "SUCCEEDED":
        raise RuntimeError(f"understanding failed: {understood.status_code} {json.dumps(understand_body)[:700]}")
    version = understand_body["observed_session_version"]
    candidates = (understand_body.get("payload") or {}).get("subject_candidates") or []
    subject = candidates[0] if candidates else None
    if not subject:
        raise RuntimeError("Fixture VLM returned no subject candidate.")
    subject_id = subject.get("subject_id") or subject.get("anchor_id") or "subject-1"

    confirmed, confirm_body = record(
        "adult_subject_confirmation",
        "post",
        f"/v1/sessions/{session_id}/gate-a/confirm",
        json={
            "request_id": str(uuid.uuid4()),
            "idempotency_key": f"{session_id}:gate-a",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "CONFIRM_GATE_A",
                "user_initiated": True,
                "primary_anchor_id": subject_id,
                "confirmation": {
                    "contract_name": "GateAConfirmationV1",
                    "contract_version": "1.0",
                    "meaning_version": 1,
                    "confirmed_claim_ids": [subject_id],
                    "correction": None,
                },
            },
        },
    )
    if confirmed.status_code != 200 or confirm_body.get("status") != "SUCCEEDED":
        raise RuntimeError(f"subject confirmation failed: {confirmed.status_code} {json.dumps(confirm_body)[:700]}")
    version = confirm_body["observed_session_version"]

    suggestions, suggestions_body = record(
        "activity_suggestions",
        "post",
        f"/v1/sessions/{session_id}/p1/activity-suggestions",
        headers={
            "X-Request-ID": str(uuid.uuid4()),
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
        json={
            "contract_name": "P1ActivitySuggestionsRequestV1",
            "contract_version": "1.0",
            "age_months": 60,
            "child_profile": {
                "contract_name": "ConfirmedChildPreferencesV1",
                "contract_version": "1.0",
                "profile_declared_by": "CAREGIVER",
                "profile_recorded_at": datetime.now(UTC).isoformat(),
                "preference_tags_confirmed": True,
                "interests": [],
                "dislikes": [],
            },
            "adult_participating": True,
            "caregiver_participating": False,
        },
    )
    if suggestions.status_code != 200 or suggestions_body.get("status") != "SUCCEEDED":
        raise RuntimeError(f"activity suggestions failed: {suggestions.status_code} {json.dumps(suggestions_body)[:700]}")
    suggestion_set = suggestions_body.get("payload") or {}
    options = suggestion_set.get("options") or []
    selected = options[0] if options else None

    selection_summary = None
    if selected:
        selected_response, selected_body = record(
            "select_first_activity",
            "put",
            f"/v1/sessions/{session_id}/p1-context",
            json={
                "request_id": str(uuid.uuid4()),
                "idempotency_key": f"{session_id}:select-activity",
                "session_id": session_id,
                "expected_session_version": version,
                "actor_ref": "demo:local",
                "payload": {
                    "operation": "SET_P1_CONTEXT",
                    "user_initiated": True,
                    "context": {
                        "contract_name": "P1ContextV4",
                        "contract_version": "4.0",
                        "candidate_selection_mode": "COMPLETE_TOPIC_AGE_LIST",
                        "discovery_policy": "TOPIC_AGE_SAFETY_DISCOVERY_V1",
                        "session_id": session_id,
                        "expected_session_version": version,
                        "age_months": 60,
                        "readiness_ids": None,
                        "completed_activity_ids": None,
                        "available_material_option_ids": None,
                        "supervision_level": None,
                        "policy_flags": None,
                        "candidate_status": None,
                        "gate_a_confirmed": True,
                        "selected_activity_id": selected["activity_id"],
                        "selected_activity_version": selected["activity_version"],
                        "caregiver_participating": False,
                        "adult_participating": True,
                    },
                },
            },
        )
        if selected_response.status_code == 200:
            selection_summary = {
                "activity_id": selected["activity_id"],
                "title_vi": selected["title_vi"],
                "activity_version": selected["activity_version"],
                "selection_http_status": selected_response.status_code,
                "result_status": selected_body.get("status"),
            }

    result = {
        "started_at_local": started_at_local.isoformat(),
        "session_id": session_id,
        "image": {
            "file": IMAGE_PATH.name,
            "sha256": image_hash,
            "byte_length": len(image_bytes),
        },
        "harness": {
            "kind": "in-process FastAPI TestClient",
            "vision": "existing deterministic test fixture; label set to visually verified synthetic topic 'bướm'",
            "vision_calls": vision.calls,
            "activity_catalog": "current curated catalog service; no AI ranking call",
        },
        "activity_set": suggestion_set,
        "selected_activity": selection_summary,
        "timings": records,
        "total_elapsed_ms": round((time.perf_counter() - started_all) * 1000, 3),
        "responses": responses,
        "limitations": [
            "This legacy demo API is a separate in-memory session from StoryRun-lite.",
            "Activity suggestions are returned before video in this legacy route, unlike SRS §31.5 post-video lesson activities.",
            "The image admission decoder and VLM are test fixtures; this run is not ClamAV/production-normalization evidence or a live AI result.",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "result_file": RESULT_PATH.name,
        "session_id": session_id,
        "vision_calls": vision.calls,
        "activity_count": len(options),
        "selected_activity": selection_summary,
        "timings": records,
        "total_elapsed_ms": result["total_elapsed_ms"],
        "all_http_statuses": [item["http_status"] for item in records],
    }, ensure_ascii=True))
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
