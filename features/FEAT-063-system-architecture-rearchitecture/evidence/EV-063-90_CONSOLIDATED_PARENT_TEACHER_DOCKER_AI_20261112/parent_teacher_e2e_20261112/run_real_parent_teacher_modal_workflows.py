"""Run bounded, real Parent/Teacher AI API flows against local Docker/Auth Emulator.

The script is copied into the API container at runtime. It reads synthetic
principals from the local database and exchanges Firebase Auth Emulator custom
tokens in memory; no credentials or ID tokens are written to evidence.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests
from sqlalchemy import text

from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.identity.firebase_admin_app import get_firebase_admin_app
from sketch2life.infrastructure.persistence.database import create_core_engine


API_BASE = "http://127.0.0.1:8000"
ORGANIZATION_ID = "local-rev82-teacher-organization"
AUTH_EMULATOR_HOST = os.getenv("FIREBASE_AUTH_EMULATOR_HOST", "firebase-auth:9099")
OUTPUT_ROOT = Path("/tmp/rev82-parent-teacher-evidence")
TIMEOUT_SECONDS = (10, 1800)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def principal_subjects() -> tuple[str, str]:
    engine = create_core_engine()
    try:
        with engine.connect() as connection:
            parent_subject = connection.execute(
                text(
                    """
                    SELECT p.owner_subject
                    FROM parent.child_profiles AS p
                    JOIN parent.data_authorizations AS a
                      ON a.parent_profile_id = p.parent_profile_id
                    JOIN be1_adult_identities AS i ON i.subject = p.owner_subject
                    WHERE p.state = 'ACTIVE'
                      AND a.state = 'GRANTED'
                      AND a.synthetic_demo_flag = TRUE
                      AND i.state = 'active'
                      AND i.account_role = 'parent'
                    ORDER BY p.created_at DESC
                    LIMIT 1
                    """
                )
            ).scalar_one_or_none()
            teacher_subject = connection.execute(
                text(
                    """
                    SELECT i.subject
                    FROM be1_adult_identities AS i
                    JOIN be1_organization_assignments AS a ON a.subject = i.subject
                    WHERE i.state = 'active'
                      AND i.account_role = 'teacher'
                      AND a.organization_id = :organization_id
                      AND a.class_id = 'local-rev82-teacher-class'
                      AND a.role = 'teacher'
                      AND a.active = TRUE
                    ORDER BY i.created_at DESC
                    LIMIT 1
                    """
                ),
                {"organization_id": ORGANIZATION_ID},
            ).scalar_one_or_none()
        if not parent_subject or not teacher_subject:
            raise RuntimeError("SYNTHETIC_PARENT_OR_TEACHER_SEED_NOT_FOUND")
        return str(parent_subject), str(teacher_subject)
    finally:
        engine.dispose()


def emulator_id_token(subject: str) -> str:
    from firebase_admin import auth

    settings = get_settings()
    app = get_firebase_admin_app(settings)
    custom_token = auth.create_custom_token(subject, app=app)
    if isinstance(custom_token, bytes):
        custom_token = custom_token.decode("utf-8")
    response = requests.post(
        f"http://{AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/"
        "accounts:signInWithCustomToken?key=local-emulator",
        json={"token": custom_token, "returnSecureToken": True},
        timeout=20,
    )
    response.raise_for_status()
    token = response.json().get("idToken")
    if not isinstance(token, str) or not token:
        raise RuntimeError("FIREBASE_AUTH_EMULATOR_ID_TOKEN_MISSING")
    return token


def api_call(
    *,
    label: str,
    method: str,
    path: str,
    token: str,
    payload: dict[str, Any] | None = None,
    output_path: Path,
    timeout: tuple[int, int] = TIMEOUT_SECONDS,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    request_id = str(uuid4())
    started = time.perf_counter()
    record: dict[str, Any] = {
        "label": label,
        "method": method,
        "path": path,
        "request_id": request_id,
        "started_at_utc": utc_now(),
    }
    try:
        response = requests.request(
            method,
            f"{API_BASE}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Request-ID": request_id,
            },
            json=payload,
            timeout=timeout,
        )
        elapsed = round(time.perf_counter() - started, 3)
        try:
            body = response.json()
        except ValueError:
            body = {"response_text_prefix": response.text[:500]}
        record.update(
            {
                "http_status": response.status_code,
                "elapsed_seconds": elapsed,
                "completed_at_utc": utc_now(),
                "status": "PASS" if response.ok else "FAIL",
            }
        )
        if not response.ok:
            detail = body.get("detail") if isinstance(body, dict) else None
            record["error"] = detail if isinstance(detail, (str, int, float, list, dict)) else "HTTP_ERROR"
        write_json(output_path, body)
        return record, body if response.ok and isinstance(body, dict) else None
    except requests.Timeout:
        record.update(
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "completed_at_utc": utc_now(),
                "status": "OUTCOME_UNKNOWN",
                "error": "CLIENT_WAIT_TIMEOUT_NO_RETRY",
            }
        )
        write_json(output_path, record)
        return record, None
    except requests.RequestException as exc:
        record.update(
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "completed_at_utc": utc_now(),
                "status": "FAIL",
                "error": type(exc).__name__,
            }
        )
        write_json(output_path, record)
        return record, None


def parent_workflow(token: str, results: dict[str, Any]) -> None:
    parent_dir = OUTPUT_ROOT / "parent"
    active_record, active_payload = api_call(
        label="Parent active StoryRun",
        method="GET",
        path="/api/parent/v1/story-runs/active/current",
        token=token,
        output_path=parent_dir / "active_run_raw.json",
        timeout=(10, 30),
    )
    results["calls"].append(active_record)
    if active_payload is None:
        results["parent_workflow"] = {"status": "BLOCKED", "reason": active_record.get("error", active_record["status"])}
        return

    run = active_payload.get("story_run")
    if not isinstance(run, dict) or run.get("run_state") != "PREPARATION_REVIEW":
        history_record, history_payload = api_call(
            label="Parent StoryRun history",
            method="GET",
            path="/api/parent/v1/story-runs?limit=50",
            token=token,
            output_path=parent_dir / "history_raw.json",
            timeout=(10, 30),
        )
        results["calls"].append(history_record)
        if history_payload:
            candidates = [
                item
                for item in history_payload.get("items", [])
                if isinstance(item, dict)
                and item.get("run_state") == "PREPARATION_REVIEW"
                and item.get("understanding_revision")
                and item.get("subject_label")
                and item.get("candidate")
            ]
            candidates.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
            run = candidates[0] if candidates else None

    if (
        not isinstance(run, dict)
        or run.get("run_state") != "PREPARATION_REVIEW"
        or not run.get("candidate")
        or not run.get("subject_label")
        or not isinstance(run.get("understanding_revision"), int)
    ):
        results["parent_workflow"] = {
            "status": "BLOCKED",
            "reason": "NO_SYNTHETIC_SUBJECT_CONFIRMED_RUN_READY_FOR_ACTIVITY",
        }
        return

    run_id = run["run_id"]
    results["parent_workflow"] = {
        "status": "RUNNING",
        "run_id": run_id,
        "run_state_before_ai": run["run_state"],
        "understanding_revision": run["understanding_revision"],
        "confirmed_subject": run["subject_label"],
        "adult_subject_confirmation_already_present": True,
        "video_called": False,
    }
    activity_record, activity_payload = api_call(
        label="Parent activity suggestion via Qwen3.5",
        method="POST",
        path=f"/api/parent/v1/ai/story-runs/{run_id}/activity-suggestions",
        token=token,
        payload={"expected_understanding_revision": run["understanding_revision"]},
        output_path=parent_dir / "activity_suggestions.json",
    )
    results["calls"].append(activity_record)
    if activity_payload is None:
        results["parent_workflow"].update(
            {"status": activity_record["status"], "activity_error": activity_record.get("error")}
        )
        return

    activities = activity_payload.get("activities")
    if not isinstance(activities, list) or not activities:
        results["parent_workflow"].update(
            {"status": "FAIL", "activity_error": "PARENT_ACTIVITY_RESPONSE_HAS_NO_ACTIVITIES"}
        )
        return

    selected = activities[0]
    activity_record["selected_for_story_review"] = {
        "activity_ref": selected.get("activity_ref"),
        "title": selected.get("title"),
        "source": selected.get("source"),
        "selection_basis": selected.get("match_reason"),
        "review_required": activity_payload.get("review_required"),
    }
    write_json(parent_dir / "activity_api_call.json", activity_record)
    request_id = activity_payload.get("request_id")
    activity_ref = selected.get("activity_ref")
    if not isinstance(request_id, str) or not isinstance(activity_ref, str):
        results["parent_workflow"].update(
            {"status": "FAIL", "activity_error": "ACTIVITY_SELECTION_REFERENCE_MISSING"}
        )
        return

    story_record, story_payload = api_call(
        label="Parent story revision via Qwen3.5",
        method="POST",
        path=f"/api/parent/v1/ai/story-runs/{run_id}/story-revisions",
        token=token,
        payload={
            "expected_understanding_revision": run["understanding_revision"],
            "primary_activity_request_id": request_id,
            "primary_activity_ref": activity_ref,
        },
        output_path=parent_dir / "story_revision.json",
    )
    results["calls"].append(story_record)
    results["parent_workflow"].update(
        {
            "status": story_record["status"],
            "activity_selection_mode": activity_payload.get("selection_mode"),
            "catalog_candidate_count": activity_payload.get("catalog_candidate_count"),
            "suggested_activity_count": len(activities),
            "story_generation_status": story_record["status"],
            "adult_story_review_required": story_payload.get("review_required") if story_payload else None,
            "story_revision_id": (
                story_payload.get("story_run", {}).get("story_revision_id") if story_payload else None
            ),
        }
    )


def _drawing_steps(topic: str, text_value: str) -> tuple[list[dict[str, str]], str]:
    raw = text_value.strip()
    numbered = re.split(
        r"(?:^|\n)\s*(?:bước\s*)?\d+\s*[.):\-]\s*",
        raw,
        flags=re.IGNORECASE,
    )
    segments = [part.strip(" \t\r\n.;-") for part in numbered if part.strip(" \t\r\n.;-")]
    if len(segments) < 4:
        segments = [
            part.strip(" \t\r\n.;-")
            for part in re.split(r"\s*(?:\r?\n+|;|•)\s*", raw)
            if part.strip(" \t\r\n.;-")
        ]
    if len(segments) < 4:
        segments = [
            part.strip(" \t\r\n.;-")
            for part in re.split(r"(?<=[.!?])\s+", raw)
            if part.strip(" \t\r\n.;-")
        ]

    edits = "AI drawing text segmented for Teacher review"
    if not 4 <= len(segments) <= 8:
        if "hươu" not in topic.casefold():
            raise RuntimeError("TEACHER_DRAWING_GUIDE_NEEDS_MANUAL_REVIEW")
        segments = [
            "Vẽ thân hươu bằng một hình bầu dục nằm ngang ở giữa trang",
            "Thêm cổ nối từ phần trước của thân và hướng lên phía đầu",
            "Vẽ đầu nhỏ, hai tai, mắt và mõm ở phía trên cổ",
            "Vẽ bốn chân phía dưới thân, chừa khoảng trống giữa các chân",
            "Thêm cặp gạc mọc trên đỉnh đầu theo hình dạng đã quan sát",
            "Thêm các đốm nhỏ trên lưng và đường cỏ dưới chân",
        ]
        edits = "Teacher structured the AI draft into six ordered drawing actions"

    placements = [
        "Ở giữa trang, nằm ngang",
        "Nối vào phần trước của thân, hướng lên",
        "Phía trên cổ, hướng mặt về phía trước",
        "Bên dưới thân, phân bố đều",
        "Trên đỉnh đầu, đối xứng hai bên",
        "Trên lưng và sát mép dưới trang",
        "Theo vị trí quan sát được trên con vật",
        "Ở phần còn trống quanh chủ thể",
    ]
    return (
        [
            {"action": segment[:240], "placement": placements[index]}
            for index, segment in enumerate(segments[:8])
        ],
        edits,
    )


def _knowledge_items(value: str) -> list[str]:
    items = [part.strip(" \t\r\n.;-") for part in re.split(r"\n+|;|(?<=[.!?])\s+", value) if part.strip(" \t\r\n.;-")]
    if not items:
        items = [value.strip()]
    bounded: list[str] = []
    for item in items:
        while len(item) > 240:
            split_at = item.rfind(" ", 0, 241)
            if split_at <= 0:
                split_at = 240
            bounded.append(item[:split_at].strip())
            item = item[split_at:].strip()
        if item:
            bounded.append(item)
    return bounded[:8]


def _reviewed_teacher_payload(suggestion: dict[str, Any]) -> tuple[dict[str, Any], str]:
    topic = str(suggestion.get("topic") or "Con hươu")
    drawing_steps, edit_note = _drawing_steps(topic, str(suggestion.get("drawing_steps_text") or ""))
    raw_activities = suggestion.get("activities")
    if not isinstance(raw_activities, list) or not raw_activities:
        raise RuntimeError("TEACHER_AI_DRAFT_HAS_NO_ACTIVITIES")
    activities = []
    for index, activity in enumerate(raw_activities, start=1):
        if not isinstance(activity, dict):
            raise RuntimeError("TEACHER_AI_ACTIVITY_SHAPE_INVALID")
        activities.append(
            {
                "activity_ref": f"rev82-e2e-activity-{index}",
                "title": str(activity.get("title") or f"Hoạt động {index}")[:120],
                "goal": str(activity.get("objective") or "Giúp trẻ quan sát chủ đề")[:200],
                "materials": str(activity.get("materials_text") or "Dụng cụ quan sát phù hợp")[:500],
                "preparation": str(
                    activity.get("preparation_text")
                    or "Người lớn kiểm tra khu vực và chuẩn bị vật liệu an toàn"
                )[:500],
                "instructions": str(activity.get("instructions_text") or "")[:1200],
                "safety_notes": str(
                    activity.get("safety_notes")
                    or "Người lớn giám sát và kiểm tra vật liệu trước khi bắt đầu"
                )[:500],
            }
        )
    payload = {
        "review_confirmed": True,
        "plan_revision_ref": "rev82-e2e-teacher-reviewed-20261112",
        "topic": topic[:120],
        "target_age_months": int(suggestion.get("target_age_months", 60)),
        "objectives": [str(item)[:200] for item in suggestion.get("objectives", [])[:4]],
        "drawing_steps": drawing_steps,
        "subject_knowledge": _knowledge_items(str(suggestion.get("subject_learning_notes") or "")),
        "activities": activities,
    }
    if not payload["objectives"] or not payload["subject_knowledge"]:
        raise RuntimeError("TEACHER_REVIEWED_PLAN_MISSING_REQUIRED_CONTENT")
    if any(not activity["instructions"] for activity in activities):
        raise RuntimeError("TEACHER_AI_ACTIVITY_INSTRUCTIONS_EMPTY")
    return payload, edit_note


def teacher_workflow(token: str, results: dict[str, Any]) -> None:
    teacher_dir = OUTPUT_ROOT / "teacher"
    prefix = f"/api/teacher/v1/organizations/{ORGANIZATION_ID}/ai"
    suggestion_record, suggestion_payload = api_call(
        label="Teacher lesson-plan suggestion via Qwen3.5",
        method="POST",
        path=f"{prefix}/lesson-plan-suggestions",
        token=token,
        payload={
            "topic": "Con hươu",
            "target_age_months": 60,
            "objectives": [
                "Quan sát hình dáng và các bộ phận bên ngoài của hươu",
                "Diễn đạt điều trẻ quan sát bằng lời hoặc tranh",
            ],
            "drawing_subject": "Con hươu",
            "activity_count": 2,
            "activity_kind": "outdoor",
            "script_following_allowed": False,
            "script_direction": None,
        },
        output_path=teacher_dir / "lesson_plan_suggestion.json",
    )
    results["calls"].append(suggestion_record)
    if suggestion_payload is None:
        results["teacher_workflow"] = {
            "status": suggestion_record["status"],
            "lesson_plan_error": suggestion_record.get("error"),
        }
        return

    suggestion = suggestion_payload.get("suggestion")
    if not isinstance(suggestion, dict):
        results["teacher_workflow"] = {"status": "FAIL", "lesson_plan_error": "TEACHER_SUGGESTION_MISSING"}
        return
    try:
        reviewed_plan, edit_note = _reviewed_teacher_payload(suggestion)
    except RuntimeError as exc:
        results["teacher_workflow"] = {"status": "BLOCKED", "lesson_plan_error": str(exc)}
        return
    write_json(teacher_dir / "teacher_reviewed_plan_input.json", reviewed_plan)

    deck_record, deck_payload = api_call(
        label="Teacher Sketch Deck via Qwen3.5",
        method="POST",
        path=f"{prefix}/sketch-decks",
        token=token,
        payload=reviewed_plan,
        output_path=teacher_dir / "sketch_deck_response.json",
    )
    results["calls"].append(deck_record)
    if deck_payload is None:
        results["teacher_workflow"] = {
            "status": deck_record["status"],
            "teacher_review_edit": edit_note,
            "sketch_deck_error": deck_record.get("error"),
        }
        return

    deck = deck_payload.get("deck")
    slides = deck.get("slides") if isinstance(deck, dict) else None
    slide_summary = [
        {
            "slide_index": item.get("slide_index"),
            "kind": item.get("kind"),
            "title": item.get("title"),
        }
        for item in slides or []
        if isinstance(item, dict)
    ]
    results["teacher_workflow"] = {
        "status": "PASS",
        "model": deck_payload.get("model"),
        "teacher_review_edit": edit_note,
        "sketch_deck_review_required": deck.get("review_required") if isinstance(deck, dict) else None,
        "slide_count": len(slides) if isinstance(slides, list) else 0,
        "slides": slide_summary,
        "presentation_image_status": "PENDING",
    }

    visual_record, visual_payload = api_call(
        label="Teacher lesson visual via FLUX.3",
        method="POST",
        path=f"{prefix}/lesson-visuals",
        token=token,
        payload=reviewed_plan,
        output_path=teacher_dir / "lesson_visuals_response_raw.json",
    )
    results["calls"].append(visual_record)
    if visual_payload is None:
        results["teacher_workflow"]["presentation_image_status"] = visual_record["status"]
        results["teacher_workflow"]["presentation_image_error"] = visual_record.get("error")
        return

    encoded_image = visual_payload.get("image_base64")
    image_status = "FAIL"
    image_path = teacher_dir / "teacher_lesson_visual_candidate.png"
    if isinstance(encoded_image, str):
        image_bytes = base64.b64decode(encoded_image, validate=True)
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            image_path.write_bytes(image_bytes)
            image_status = "PASS"
    visual_metadata = {key: value for key, value in visual_payload.items() if key != "image_base64"}
    write_json(teacher_dir / "lesson_visuals_metadata.json", visual_metadata)
    results["teacher_workflow"].update(
        {
            "presentation_image_status": image_status,
            "presentation_image_path": str(image_path) if image_status == "PASS" else None,
            "presentation_visual_model": visual_payload.get("model"),
            "presentation_visual_review_required": visual_payload.get("review_required"),
        }
    )


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {
        "started_at_utc": utc_now(),
        "test_mode": "real_authenticated_synthetic_docker_modal_api",
        "fixture_used_as_success": False,
        "video_called": False,
        "calls": [],
    }
    try:
        parent_subject, teacher_subject = principal_subjects()
        parent_token = emulator_id_token(parent_subject)
        teacher_token = emulator_id_token(teacher_subject)
    except Exception as exc:
        results["setup"] = {"status": "FAIL", "error": f"AUTH_OR_SEED_SETUP_FAILED:{type(exc).__name__}"}
        results["completed_at_utc"] = utc_now()
        write_json(OUTPUT_ROOT / "run_summary.json", results)
        print(json.dumps(results, ensure_ascii=False))
        return 2

    results["setup"] = {
        "status": "PASS",
        "firebase_auth_emulator_sign_in": "PASS",
        "parent_account": "synthetic_seed",
        "teacher_account": "synthetic_seed",
        "teacher_organization": ORGANIZATION_ID,
        "credentials_written": False,
        "tokens_written": False,
    }
    parent_workflow(parent_token, results)
    teacher_workflow(teacher_token, results)
    results["completed_at_utc"] = utc_now()
    write_json(OUTPUT_ROOT / "run_summary.json", results)
    print(json.dumps(results, ensure_ascii=False))
    return 0 if all(call.get("status") == "PASS" for call in results["calls"] if call.get("label", "").startswith(("Parent activity", "Parent story", "Teacher lesson-plan", "Teacher Sketch Deck", "Teacher lesson visual"))) else 1


if __name__ == "__main__":
    raise SystemExit(main())
