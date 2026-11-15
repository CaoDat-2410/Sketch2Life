"""Make the single approved post-fix Teacher visual API call in local Docker."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import requests
from firebase_admin import auth
from sqlalchemy import text

from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.identity.firebase_admin_app import get_firebase_admin_app
from sketch2life.infrastructure.persistence.database import create_core_engine


API_BASE = "http://127.0.0.1:8000"
AUTH_EMULATOR_HOST = "firebase-auth:9099"
ORGANIZATION_ID = "local-rev82-teacher-organization"
OUTPUT_ROOT = Path("/tmp/rev82-parent-teacher-evidence/teacher")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def teacher_subject() -> str:
    engine = create_core_engine()
    try:
        with engine.connect() as connection:
            subject = connection.execute(
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
        if not subject:
            raise RuntimeError("SYNTHETIC_TEACHER_SEED_NOT_FOUND")
        return str(subject)
    finally:
        engine.dispose()


def main() -> int:
    started_at = now()
    started = time.perf_counter()
    request_id = str(uuid4())
    result: dict[str, object] = {
        "label": "Teacher lesson visual post-fix verification",
        "request_id": request_id,
        "started_at_utc": started_at,
        "test_mode": "real_authenticated_synthetic_docker_modal_api",
        "video_called": False,
        "retry_count": 0,
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        settings = get_settings()
        app = get_firebase_admin_app(settings)
        custom_token = auth.create_custom_token(teacher_subject(), app=app)
        if isinstance(custom_token, bytes):
            custom_token = custom_token.decode("utf-8")
        token_response = requests.post(
            f"http://{AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/"
            "accounts:signInWithCustomToken?key=local-emulator",
            json={"token": custom_token, "returnSecureToken": True},
            timeout=20,
        )
        token_response.raise_for_status()
        id_token = token_response.json().get("idToken")
        if not isinstance(id_token, str) or not id_token:
            raise RuntimeError("FIREBASE_AUTH_EMULATOR_ID_TOKEN_MISSING")

        plan = json.loads(
            (OUTPUT_ROOT / "teacher_reviewed_plan_input.json").read_text(encoding="utf-8")
        )
        response = requests.post(
            f"{API_BASE}/api/teacher/v1/organizations/{ORGANIZATION_ID}/ai/lesson-visuals",
            headers={
                "Authorization": f"Bearer {id_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Request-ID": request_id,
            },
            json=plan,
            timeout=(10, 1800),
        )
        result["http_status"] = response.status_code
        result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        result["completed_at_utc"] = now()
        result["status"] = "PASS" if response.ok else "FAIL"
        try:
            body = response.json()
        except ValueError:
            body = {"error": "NON_JSON_API_RESPONSE"}

        if not response.ok:
            detail = body.get("detail") if isinstance(body, dict) else None
            result["error"] = detail if isinstance(detail, dict) else {"code": "HTTP_ERROR"}
            (OUTPUT_ROOT / "lesson_visual_postfix_error.json").write_text(
                json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        else:
            encoded = body.get("image_base64") if isinstance(body, dict) else None
            if not isinstance(encoded, str):
                result["status"] = "FAIL"
                result["error"] = {"code": "TEACHER_VISUAL_IMAGE_MISSING"}
            else:
                image = base64.b64decode(encoded, validate=True)
                if not image.startswith(b"\x89PNG\r\n\x1a\n"):
                    result["status"] = "FAIL"
                    result["error"] = {"code": "TEACHER_VISUAL_IMAGE_NOT_PNG"}
                else:
                    image_path = OUTPUT_ROOT / "teacher_lesson_visual_candidate.png"
                    image_path.write_bytes(image)
                    metadata = {key: value for key, value in body.items() if key != "image_base64"}
                    metadata["image_sha256"] = hashlib.sha256(image).hexdigest()
                    metadata["image_size_bytes"] = len(image)
                    (OUTPUT_ROOT / "lesson_visuals_metadata.json").write_text(
                        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    result["modal_call_id"] = body.get("modal_call_id")
                    result["image_path"] = str(image_path)
                    result["image_sha256"] = metadata["image_sha256"]
                    result["image_size_bytes"] = len(image)
                    result["model"] = body.get("model")
                    result["review_required"] = body.get("review_required")
                    result["panel_layout"] = body.get("panel_layout")
    except requests.Timeout:
        result.update(
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "completed_at_utc": now(),
                "status": "OUTCOME_UNKNOWN",
                "error": {"code": "CLIENT_WAIT_TIMEOUT_NO_RETRY"},
            }
        )
    except requests.RequestException as exc:
        result.update(
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "completed_at_utc": now(),
                "status": "FAIL",
                "error": {"code": type(exc).__name__},
            }
        )
    except Exception as exc:
        result.update(
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "completed_at_utc": now(),
                "status": "FAIL",
                "error": {"code": type(exc).__name__},
            }
        )

    (OUTPUT_ROOT / "lesson_visual_postfix_summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
