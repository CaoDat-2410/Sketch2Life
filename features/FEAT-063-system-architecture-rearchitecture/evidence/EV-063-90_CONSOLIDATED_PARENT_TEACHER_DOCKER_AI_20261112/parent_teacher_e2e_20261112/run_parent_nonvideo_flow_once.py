"""Run one bounded synthetic Parent non-video AI flow via local Docker APIs."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests


API_BASE = "http://127.0.0.1:8000"
AUTH_EMULATOR_HOST = "firebase-auth:9099"
OUTPUT_ROOT = Path("/tmp/rev82-parent-teacher-evidence/parent_final_20261112")
INPUT_IMAGE = OUTPUT_ROOT / "synthetic_deer_drawing.png"
AI_TIMEOUT = (10, 1800)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def error_code(body: Any) -> str:
    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, dict) and isinstance(detail.get("code"), str):
            return detail["code"]
    return "HTTP_ERROR"


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if not INPUT_IMAGE.is_file():
        raise RuntimeError("SYNTHETIC_DRAWING_INPUT_MISSING")

    result: dict[str, Any] = {
        "started_at_utc": now(),
        "test_mode": "real_synthetic_docker_firebase_auth_emulator_modal_api",
        "fixture_used_as_success": False,
        "video_called": False,
        "parent_guide_reused": True,
        "account_credentials_written": False,
        "firebase_tokens_written": False,
        "consent_scope": "LOCAL_SYNTHETIC_TEST_ONLY_NOT_LEGAL_CONSENT",
        "calls": [],
    }

    def call(
        label: str,
        method: str,
        path: str,
        *,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        timeout: tuple[int, int] = AI_TIMEOUT,
        save_body: bool = True,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        request_id = str(uuid4())
        started = time.perf_counter()
        record: dict[str, Any] = {
            "label": label,
            "method": method,
            "path": path,
            "request_id": request_id,
            "started_at_utc": now(),
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Request-ID": request_id,
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = requests.request(
                method,
                f"{API_BASE}{path}",
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            try:
                body = response.json()
            except ValueError:
                body = {"detail": {"code": "NON_JSON_API_RESPONSE"}}
            record.update(
                {
                    "http_status": response.status_code,
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "completed_at_utc": now(),
                    "status": "PASS" if response.ok else "FAIL",
                }
            )
            if not response.ok:
                record["error_code"] = error_code(body)
            if save_body:
                write_json(OUTPUT_ROOT / f"{label}.json", body)
            result["calls"].append(record)
            return record, body if response.ok and isinstance(body, dict) else None
        except requests.Timeout:
            record.update(
                {
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "completed_at_utc": now(),
                    "status": "OUTCOME_UNKNOWN",
                    "error_code": "CLIENT_WAIT_TIMEOUT_NO_RETRY",
                }
            )
            result["calls"].append(record)
            return record, None
        except requests.RequestException as exc:
            record.update(
                {
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "completed_at_utc": now(),
                    "status": "FAIL",
                    "error_code": type(exc).__name__,
                }
            )
            result["calls"].append(record)
            return record, None

    suffix = uuid4().hex
    email = f"parent-rev82-{suffix}@example.invalid"
    password = secrets.token_urlsafe(24)
    registration, registration_body = call(
        "01_registration",
        "POST",
        "/api/auth/v1/registrations",
        payload={"email": email, "password": password},
        timeout=(10, 30),
    )
    if registration_body is None or registration_body.get("role") != "parent":
        result["parent_workflow"] = {"status": registration["status"], "blocked_at": "registration"}
        return finish(result)

    try:
        auth_response = requests.post(
            f"http://{AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/"
            "accounts:signInWithPassword?key=local-emulator",
            json={"email": email, "password": password, "returnSecureToken": True},
            timeout=20,
        )
        auth_response.raise_for_status()
        token = auth_response.json().get("idToken")
    except requests.RequestException as exc:
        result["parent_workflow"] = {
            "status": "FAIL",
            "blocked_at": "firebase_auth_emulator_sign_in",
            "error_code": type(exc).__name__,
        }
        return finish(result)
    if not isinstance(token, str) or not token:
        result["parent_workflow"] = {
            "status": "FAIL",
            "blocked_at": "firebase_auth_emulator_sign_in",
            "error_code": "FIREBASE_ID_TOKEN_MISSING",
        }
        return finish(result)
    result["parent_account_created"] = True

    me_record, me_body = call(
        "02_account_role",
        "GET",
        "/api/auth/v1/me",
        token=token,
        timeout=(10, 30),
    )
    if me_body is None or me_body.get("role") != "parent":
        result["parent_workflow"] = {"status": me_record["status"], "blocked_at": "account_role"}
        return finish(result)

    policy_record, policy_body = call(
        "03_consent_policy",
        "GET",
        "/api/parent/v1/consent-policy",
        token=token,
        timeout=(10, 30),
        save_body=False,
    )
    policy = policy_body.get("policy") if policy_body else None
    if not isinstance(policy, dict) or not isinstance(policy.get("policy_version"), str):
        result["parent_workflow"] = {"status": policy_record["status"], "blocked_at": "consent_policy"}
        return finish(result)
    result["consent_policy_version"] = policy["policy_version"]

    profile_record, profile_body = call(
        "04_child_profile",
        "POST",
        "/api/parent/v1/child-profiles",
        token=token,
        payload={
            "age_months": 60,
            "display_name": "Synthetic Child Rev82",
            "interests_summary": "Thiên nhiên và động vật",
            "consent_accepted": True,
            "consent_policy_version": policy["policy_version"],
        },
        timeout=(10, 30),
    )
    profile = profile_body.get("profile") if profile_body else None
    revision = profile.get("current_revision") if isinstance(profile, dict) else None
    if not isinstance(profile, dict) or not isinstance(revision, dict):
        result["parent_workflow"] = {"status": profile_record["status"], "blocked_at": "child_profile"}
        return finish(result)

    run_record, run_body = call(
        "05_story_run",
        "POST",
        "/api/parent/v1/story-runs",
        token=token,
        payload={
            "parent_profile_id": profile["parent_profile_id"],
            "expected_profile_revision_id": revision["profile_revision_id"],
            "consent_policy_version": policy["policy_version"],
            "topic": "Con hươu",
            "adult_confirmed_idea": "",
            "context_confirmed": True,
        },
        timeout=(10, 30),
    )
    story_run = run_body.get("story_run") if run_body else None
    if not isinstance(story_run, dict) or not isinstance(story_run.get("run_id"), str):
        result["parent_workflow"] = {"status": run_record["status"], "blocked_at": "story_run"}
        return finish(result)

    image_bytes = INPUT_IMAGE.read_bytes()
    result["input_image"] = {
        "sha256": hashlib.sha256(image_bytes).hexdigest(),
        "size_bytes": len(image_bytes),
        "synthetic": True,
    }
    run_id = story_run["run_id"]
    drawing_record, drawing_body = call(
        "06_drawing_understanding",
        "POST",
        "/api/parent/v1/ai/drawing-understandings",
        token=token,
        payload={
            "story_run_id": run_id,
            "image_base64": base64.b64encode(image_bytes).decode("ascii"),
            "media_type": "image/png",
            "replace_existing": False,
            "expected_input_revision": 1,
        },
    )
    if drawing_body is None:
        result["parent_workflow"] = {
            "status": drawing_record["status"],
            "blocked_at": "drawing_understanding",
            "error_code": drawing_record.get("error_code"),
        }
        return finish(result)
    candidate = drawing_body.get("candidate")
    if not isinstance(candidate, dict):
        result["parent_workflow"] = {"status": "FAIL", "blocked_at": "drawing_candidate_contract"}
        return finish(result)
    subject = str(candidate.get("candidate_subject") or "")
    matches_deer = any(term in subject.casefold() for term in ("hươu", "huou", "nai", "deer"))
    if not matches_deer or candidate.get("topic_match") != "MATCH":
        result["drawing_understanding"] = {
            "candidate_subject": subject,
            "confidence": candidate.get("confidence"),
            "topic_match": candidate.get("topic_match"),
            "visible_features": candidate.get("visible_features"),
            "review_required": drawing_body.get("review_required"),
        }
        result["parent_workflow"] = {
            "status": "BLOCKED",
            "blocked_at": "adult_topic_mismatch_decision",
            "reason": "MODEL_SUBJECT_OR_TOPIC_DOES_NOT_MATCH_SYNTHETIC_DEER_INPUT",
        }
        return finish(result)
    result["drawing_understanding"] = {
        "candidate_subject": subject,
        "confidence": candidate.get("confidence"),
        "topic_match": candidate.get("topic_match"),
        "visible_features": candidate.get("visible_features"),
        "review_required": drawing_body.get("review_required"),
    }
    understanding_revision = drawing_body.get("understanding_revision")

    subject_record, subject_body = call(
        "07_subject_confirmation",
        "POST",
        f"/api/parent/v1/story-runs/{run_id}/subject-confirmations",
        token=token,
        payload={
            "expected_understanding_revision": understanding_revision,
            "confirmed_subject": subject,
        },
        timeout=(10, 30),
    )
    if subject_body is None:
        result["parent_workflow"] = {"status": subject_record["status"], "blocked_at": "subject_confirmation"}
        return finish(result)

    activity_record, activity_body = call(
        "08_activity_suggestions",
        "POST",
        f"/api/parent/v1/ai/story-runs/{run_id}/activity-suggestions",
        token=token,
        payload={"expected_understanding_revision": understanding_revision},
    )
    activities = activity_body.get("activities") if activity_body else None
    if not isinstance(activities, list) or not activities:
        result["parent_workflow"] = {
            "status": activity_record["status"] if activity_body is None else "FAIL",
            "blocked_at": "activity_suggestions",
            "error_code": activity_record.get("error_code"),
        }
        return finish(result)
    result["activity_suggestions"] = {
        "selection_mode": activity_body.get("selection_mode"),
        "catalog_candidate_count": activity_body.get("catalog_candidate_count"),
        "suggested_activity_count": len(activities),
        "activities": [
            {
                "activity_ref": item.get("activity_ref"),
                "title": item.get("title"),
                "source": item.get("source"),
                "match_reason": item.get("match_reason"),
            }
            for item in activities
            if isinstance(item, dict)
        ],
        "review_required": activity_body.get("review_required"),
    }
    selected = activities[0]
    activity_request_id = activity_body.get("request_id")
    if not isinstance(activity_request_id, str) or not isinstance(selected.get("activity_ref"), str):
        result["parent_workflow"] = {"status": "FAIL", "blocked_at": "adult_activity_selection_contract"}
        return finish(result)

    story_record, story_body = call(
        "09_story_revision",
        "POST",
        f"/api/parent/v1/ai/story-runs/{run_id}/story-revisions",
        token=token,
        payload={
            "expected_understanding_revision": understanding_revision,
            "primary_activity_request_id": activity_request_id,
            "primary_activity_ref": selected["activity_ref"],
        },
    )
    story = story_body.get("story_run") if story_body else None
    story_revision = story_body.get("story_revision") if story_body else None
    generated_story = story_revision if isinstance(story_revision, dict) else story
    if story_body:
        result["story"] = {
            "title": generated_story.get("title") if isinstance(generated_story, dict) else None,
            "scene_count": len(generated_story.get("scenes", [])) if isinstance(generated_story, dict) else None,
            "review_required": story_body.get("review_required"),
        }
    result["parent_workflow"] = {
        "status": story_record["status"],
        "story_run_id": run_id,
        "subject_confirmed_by_test_adult": True,
        "activity_selected_by_test_adult": selected.get("activity_ref"),
        "video_called": False,
    }
    return finish(result)


def finish(result: dict[str, Any]) -> int:
    result["completed_at_utc"] = now()
    result["calls_summary"] = [
        {
            key: call.get(key)
            for key in ("label", "http_status", "elapsed_seconds", "status", "error_code")
            if key in call
        }
        for call in result.get("calls", [])
    ]
    write_json(OUTPUT_ROOT / "run_summary.json", result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result.get("parent_workflow", {}).get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
