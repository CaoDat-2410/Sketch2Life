from __future__ import annotations

import base64
import hashlib
import html as html_lib
import json
import os
import socket
import tempfile
import threading
import time
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
ASSET_DIR = FEATURE / "evidence" / "assets" / "ai_flow_srs_alignment_20261104"
IMAGE_PATH = FEATURE / "evidence" / "assets" / "parent_generated_image_activity_retest_20261103" / "synthetic_childlike_butterfly.png"
RESULT_PATH = ASSET_DIR / "parent_flow_results.json"
TRACE_PATH = ASSET_DIR / "poc_run_trace.json"
PLAN_PATH = ASSET_DIR / "approved_plan_fixture.json"
DECK_PATH = ASSET_DIR / "teacher_deck_output.json"
VISUAL_PATH = ASSET_DIR / "teacher_visual.png"
VISUAL_PROVENANCE_PATH = ASSET_DIR / "teacher_visual_provenance.json"
PREVIEW_PATH = ASSET_DIR / "teacher_deck_preview.html"
GUARD_PATH = ASSET_DIR / "POC_DISPATCH_INTENT.json"
TEMP_ROOT = Path(tempfile.gettempdir()) / "sketch2life-feat063-ai-flow-20261104"
DB_URL = os.environ.get("STORYRUN_LITE_DATABASE_URL", "")
MODAL_ENV = "dev"
SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
LANGUAGE_APP = "sketch2life-srs23-language-audio-dev"
FLUX_APP = "sketch2life-srs23-flux-image-dev"
PARENT_ADULT_IDEA = "Kể hành trình của bướm qua các giai đoạn sống, rồi bay đến những bông hoa. Giữ thông tin khoa học chính xác."


def now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def dump_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def synthetic_approved_plan() -> dict[str, Any]:
    plan: dict[str, Any] = {
        "schema_version": "sketch2life.teacher-deck-input.v1",
        "plan_revision_ref": "synthetic-approved-butterfly-plan-v1",
        "topic": "Con bướm",
        "target_age_months": 60,
        "objectives": [
            "Trẻ quan sát hình dáng và một số đặc điểm dễ nhận thấy của con bướm.",
            "Trẻ tìm hiểu vòng đời của bướm bằng ngôn ngữ phù hợp lứa tuổi.",
        ],
        "drawing_steps": [
            {"step_index": 1, "action": "Vẽ đầu tròn nhỏ và thân dài mảnh.", "placement": "Ở giữa trang giấy, chừa khoảng trống hai bên."},
            {"step_index": 2, "action": "Thêm hai cặp cánh lớn hai bên thân.", "placement": "Cánh trên lớn hơn, cánh dưới nhỏ hơn và cân đối."},
            {"step_index": 3, "action": "Vẽ hai chiếc râu cong trên đầu.", "placement": "Hai râu hướng lên, gần đầu bướm."},
            {"step_index": 4, "action": "Thêm vài đường gân đơn giản trên cánh.", "placement": "Rải nhẹ trên cánh, giữ nhiều khoảng trắng."},
        ],
        "subject_knowledge": [
            "Vòng đời của bướm gồm trứng, sâu bướm, nhộng rồi đến bướm trưởng thành.",
            "Sâu bướm nở từ trứng; bướm trưởng thành chui ra khỏi nhộng.",
            "Nhiều loài bướm trưởng thành hút mật hoa bằng vòi dài.",
        ],
        "activities": [
            {
                "activity_ref": "synthetic-activity-observe-butterfly",
                "title": "Quan sát bướm từ xa",
                "goal": ["Luyện quan sát và nhận ra đặc điểm của bướm trong môi trường tự nhiên."],
                "materials": ["Sổ quan sát", "Bút chì"],
                "preparation": ["Chọn khu vườn an toàn có hoa và đứng cùng trẻ."],
                "instructions": ["Quan sát bướm từ khoảng cách an toàn.", "Mời trẻ kể điều mình nhìn thấy; không bắt hoặc chạm vào bướm."],
                "safety_notes": ["Người lớn luôn ở cạnh trẻ.", "Không bắt, đuổi hoặc chạm vào côn trùng."],
            },
            {
                "activity_ref": "synthetic-activity-compare-flowers",
                "title": "Tìm những bông hoa khác nhau",
                "goal": ["So sánh hình dáng và màu sắc của các bông hoa thu hút bướm."],
                "materials": ["Thẻ quan sát bằng giấy"],
                "preparation": ["Chọn lối đi bằng phẳng, tránh cây có gai và khu vực xe cộ."],
                "instructions": ["Quan sát hai bông hoa khác nhau mà không ngắt hoa.", "Mời trẻ mô tả điểm giống và khác nhau."],
                "safety_notes": ["Người lớn ở gần; không nếm hoặc bứt cây.", "Rửa tay sau hoạt động ngoài trời."],
            },
        ],
    }
    plan["content_hash"] = sha256(canonical_json(plan))
    return plan


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@dataclass(slots=True)
class LocalApiHarness:
    engine: Any
    repository: Any
    service: Any
    server: Any
    thread: threading.Thread


def start_api_server(
    *,
    port: int,
    run_id: str,
    trace: dict[str, Any],
    actor_scope_ref: str = "synthetic-parent-local-v1",
) -> LocalApiHarness:
    import uvicorn
    from sketch2life.application.services.story_run_lite import StoryRunLiteService
    from sketch2life.domain.story_run_lite import OwnerScopeKind
    from sketch2life.infrastructure.ai.modal_function_client import (
        ModalStoryFunctionClient,
    )
    from sketch2life.infrastructure.story_run_lite.clamav import ClamAvScanner
    from sketch2life.infrastructure.story_run_lite.composition import goal_database_url
    from sketch2life.infrastructure.story_run_lite.image_worker import (
        WindowsJobObjectImageNormalizer,
    )
    from sketch2life.infrastructure.story_run_lite.photo_bridge import (
        ModalFunctionPhotoVisionBridge,
    )
    from sketch2life.infrastructure.story_run_lite.quarantine import QuarantineStore
    from sketch2life.infrastructure.story_run_lite.repository import (
        SqlStoryRunLiteRepository,
    )
    from sketch2life.interfaces.http.story_run_lite_app import create_app
    from sqlalchemy import create_engine, text

    if not DB_URL:
        raise RuntimeError("STORYRUN_LITE_DATABASE_URL is required for the synthetic API harness.")
    safe_url, expected_database = goal_database_url(DB_URL)
    if expected_database != "storyrun_lite_feat063_ai_20261104":
        raise RuntimeError("The API harness only accepts its named task-owned database.")
    engine = create_engine(safe_url, pool_pre_ping=True, hide_parameters=True)
    locked = False
    try:
        with engine.connect() as connection:
            identity = connection.execute(
                text(
                    "SELECT current_database() AS database_name, current_user AS current_user, "
                    "pg_get_userbyid(datdba) AS database_owner, inet_server_addr()::text AS server_address "
                    "FROM pg_database WHERE datname = current_database()"
                )
            ).mappings().one()
        if (
            identity["database_name"] != expected_database
            or identity["current_user"] != identity["database_owner"]
        ):
            raise RuntimeError("Task PostgreSQL identity is not the expected owned synthetic database.")
        quarantine_root = TEMP_ROOT / "local_quarantine"
        repository = SqlStoryRunLiteRepository(
            engine=engine,
            quarantine=QuarantineStore(quarantine_root),
        )
        repository.acquire_singleton_lock()
        locked = True
        repository.recover_after_restart()
        vision = ModalFunctionPhotoVisionBridge(
            engine=engine,
            repository=repository,
            pinned_run_id=run_id,
        )
        vision.reconcile_completed_results()
        service = StoryRunLiteService(
            repository=repository,
            scanner=ClamAvScanner(host="127.0.0.1", port=3310),
            normalizer=WindowsJobObjectImageNormalizer(temporary_root=quarantine_root / "workers"),
            vision=vision,
            story_generator=ModalStoryFunctionClient(),
            story_references=repository,
            asset_admission=repository,
            actor_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
            actor_scope_ref=actor_scope_ref,
        )
        app = create_app(service=service)
        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)
        )
        thread = threading.Thread(target=server.run, name="feat063-storyrun-api", daemon=True)
        thread.start()
        trace["database_guard"] = {
            "database": expected_database,
            "current_user_is_owner": True,
            "api_client_target": "127.0.0.1",
            "postgres_container_server_address": identity["server_address"],
            "test_harness_only": True,
            "product_loopback_guard_changed": False,
        }
        dump_json(TRACE_PATH, trace)
        return LocalApiHarness(engine, repository, service, server, thread)
    except Exception:
        if locked:
            repository.release_singleton_lock()
        engine.dispose()
        raise


def stop_api_server(harness: LocalApiHarness | None) -> None:
    if harness is None:
        return
    harness.server.should_exit = True
    harness.thread.join(timeout=20)
    if harness.thread.is_alive():
        raise RuntimeError("Task-owned local API server did not stop cleanly.")
    harness.repository.release_singleton_lock()
    harness.engine.dispose()


def wait_for_api(base_url: str, harness: LocalApiHarness, seconds: float = 45.0) -> None:
    deadline = time.perf_counter() + seconds
    while time.perf_counter() < deadline:
        if not harness.thread.is_alive():
            raise RuntimeError("Local StoryRun-lite API process exited during startup.")
        try:
            response = requests.get(base_url + "/health", timeout=1)
            if response.status_code == 404 and response.json().get("detail") == "Not Found":
                return
        except requests.RequestException:
            time.sleep(0.25)
    raise TimeoutError("Local StoryRun-lite API did not become ready within 45 seconds.")


def api_call(
    trace: dict[str, Any],
    session: requests.Session,
    *,
    name: str,
    method: str,
    base_url: str,
    path: str,
    timeout: float | tuple[float, float] = 30.0,
    **kwargs: Any,
) -> tuple[requests.Response, dict[str, Any]]:
    started = time.perf_counter()
    try:
        response = session.request(method, base_url + path, timeout=timeout, **kwargs)
    except requests.RequestException as exc:
        record = {
            "name": name,
            "method": method.upper(),
            "path": path,
            "status": None,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "outcome": "UNKNOWN_NO_RETRY",
            "error_type": type(exc).__name__,
        }
        trace.setdefault("api_records", []).append(record)
        dump_json(TRACE_PATH, trace)
        raise RuntimeError(f"{name} transport outcome is unknown; do not retry.") from None
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    try:
        body = response.json()
    except requests.JSONDecodeError:
        body = {"body_prefix": response.text[:300]}
    header_values = {
        key: response.headers[key]
        for key in ("ETag", "Location", "Retry-After", "Cache-Control")
        if key in response.headers
    }
    trace.setdefault("api_records", []).append(
        {
            "name": name,
            "method": method.upper(),
            "path": path,
            "status": response.status_code,
            "elapsed_ms": elapsed_ms,
            "headers": header_values,
            "response": body,
        }
    )
    dump_json(TRACE_PATH, trace)
    return response, body


def require_status(response: requests.Response, body: dict[str, Any], allowed: set[int], step: str) -> None:
    if response.status_code not in allowed:
        raise RuntimeError(f"{step} returned HTTP {response.status_code}: {body.get('code', body.get('detail', ''))}")


def parent_api_flow(trace: dict[str, Any], port: int) -> None:
    image_bytes = IMAGE_PATH.read_bytes()
    image_sha = sha256(image_bytes)
    flow_id = str(uuid.uuid4())
    trace["parent_flow"] = {
        "flow_id": flow_id,
        "started_at": now_local(),
        "image": {"file": IMAGE_PATH.name, "sha256": image_sha, "size_bytes": len(image_bytes)},
        "video_calls": 0,
        "activities_selected": False,
    }
    base = f"http://127.0.0.1:{port}"
    session = requests.Session()

    # Create the run before pinning the Modal vision adapter to it. No AI is dispatched yet.
    harness: LocalApiHarness | None = None
    try:
        harness = start_api_server(
            port=port,
            run_id="00000000-0000-4000-8000-000000000001",
            trace=trace,
        )
        wait_for_api(base, harness)
        invalid, invalid_body = api_call(
            trace, session, name="reject_create_without_age", method="POST", base_url=base,
            path="/v1/story-runs", headers={"Idempotency-Key": f"{flow_id}:missing-age"},
            json={"profile_ref": "synthetic-parent-demo"},
        )
        require_status(invalid, invalid_body, {422}, "missing age rule")
        created, created_body = api_call(
            trace, session, name="create_parent_story_run", method="POST", base_url=base,
            path="/v1/story-runs", headers={"Idempotency-Key": f"{flow_id}:create-run"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 60},
        )
        require_status(created, created_body, {201}, "create run")
        run_ref = str(created_body["run_ref"])
        trace["parent_flow"]["run_ref"] = run_ref
        from sketch2life.infrastructure.story_run_lite.photo_bridge import (
            ModalFunctionPhotoVisionBridge,
        )

        harness.service._vision = ModalFunctionPhotoVisionBridge(
            engine=harness.engine,
            repository=harness.repository,
            pinned_run_id=run_ref,
        )
        initial, initial_body = api_call(
            trace, session, name="read_new_run", method="GET", base_url=base,
            path=f"/v1/story-runs/{run_ref}",
        )
        require_status(initial, initial_body, {200}, "read run")

        invalid_story, invalid_story_body = api_call(
            trace, session, name="reject_parent_activity_preselection", method="POST", base_url=base,
            path=f"/v1/story-runs/{run_ref}/story-revisions",
            headers={"Idempotency-Key": f"{flow_id}:activities-not-allowed", "If-Match": initial.headers["ETag"]},
            json={"expected_understanding_revision": 1, "activities": ["synthetic-activity-observe-butterfly"]},
        )
        require_status(invalid_story, invalid_story_body, {422}, "Parent activity preselection rule")

        upload, upload_body = api_call(
            trace, session, name="create_artwork_upload", method="POST", base_url=base,
            path="/v1/upload-sessions", headers={"Idempotency-Key": f"{flow_id}:create-upload"},
            json={
                "target_ref": run_ref, "purpose": "RUN_ARTWORK", "media_type": "image/png",
                "expected_size_bytes": len(image_bytes), "expected_sha256": image_sha,
            },
        )
        require_status(upload, upload_body, {201}, "create upload")
        upload_ref = str(upload_body["upload_ref"])
        trace["parent_flow"]["upload_ref"] = upload_ref

        part, part_body = api_call(
            trace, session, name="upload_artwork_part", method="PUT", base_url=base,
            path=f"/v1/upload-sessions/{upload_ref}/parts/1",
            headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(image_bytes)), "Content-SHA256": image_sha},
            data=image_bytes, timeout=120,
        )
        require_status(part, part_body, {200}, "upload image part")

        uploaded, uploaded_body = api_call(
            trace, session, name="read_upload_before_complete", method="GET", base_url=base,
            path=f"/v1/upload-sessions/{upload_ref}",
        )
        require_status(uploaded, uploaded_body, {200}, "read upload before complete")
        completed, completed_body = api_call(
            trace, session, name="complete_artwork_admission", method="POST", base_url=base,
            path=f"/v1/upload-sessions/{upload_ref}/complete",
            headers={"Idempotency-Key": f"{flow_id}:complete-upload", "If-Match": uploaded.headers["ETag"]},
            json={"expected_size_bytes": len(image_bytes), "expected_sha256": image_sha}, timeout=180,
        )
        require_status(completed, completed_body, {200, 202}, "complete upload")

        deadline = time.perf_counter() + 120
        admitted: dict[str, Any] | None = None
        while time.perf_counter() < deadline:
            polled, polled_body = api_call(
                trace, session, name="poll_artwork_admission", method="GET", base_url=base,
                path=f"/v1/upload-sessions/{upload_ref}",
            )
            require_status(polled, polled_body, {200}, "poll upload")
            if polled_body.get("state") == "READY":
                admitted = polled_body
                break
            if polled_body.get("state") in {"FAILED", "ABORTED", "EXPIRED"}:
                raise RuntimeError(f"Upload admission stopped in {polled_body.get('state')}.")
            time.sleep(1)
        if admitted is None:
            raise TimeoutError("Synthetic drawing was not admitted within 120 seconds.")

        current, current_body = api_call(
            trace, session, name="read_run_before_vision", method="GET", base_url=base,
            path=f"/v1/story-runs/{run_ref}",
        )
        require_status(current, current_body, {200}, "read run before vision")
        intent = {
            "state": "DRAWING_VLM_DISPATCH_INTENT_RECORDED",
            "flow_id": flow_id,
            "run_ref": run_ref,
            "image_sha256": image_sha,
            "created_at": now_local(),
            "max_attempts": 1,
            "video_enabled": False,
        }
        dump_json(ASSET_DIR / "drawing_vlm_dispatch_intent.json", intent)
        attached, attached_body = api_call(
            trace, session, name="attach_drawing_and_run_vlm_once", method="POST", base_url=base,
            path=f"/v1/story-runs/{run_ref}/assets",
            headers={"Idempotency-Key": f"{flow_id}:attach-drawing", "If-Match": current.headers["ETag"]},
            json={"asset_ref": admitted["asset_ref"], "expected_revision": current_body["revision"]},
            timeout=(15, 980),
        )
        require_status(attached, attached_body, {202}, "attach artwork / VLM")

        deadline = time.perf_counter() + 900
        review_run: dict[str, Any] | None = None
        review_etag: str | None = None
        while time.perf_counter() < deadline:
            polled, polled_body = api_call(
                trace, session, name="read_run_after_vlm", method="GET", base_url=base,
                path=f"/v1/story-runs/{run_ref}",
            )
            require_status(polled, polled_body, {200}, "read run after drawing analysis")
            if polled_body.get("run_state") in {"SUBJECT_REVIEW", "FAILED", "SCRIPT_GENERATION_UNKNOWN"}:
                review_run, review_etag = polled_body, polled.headers.get("ETag")
                break
            time.sleep(2)
        if review_run is None:
            raise TimeoutError("No terminal subject-review state arrived within the approved wait.")
        trace["parent_flow"]["run_after_vlm"] = review_run
        trace["parent_flow"]["drawing_model"] = (review_run.get("result") or {}).get("model")
        if review_run.get("run_state") != "SUBJECT_REVIEW":
            raise RuntimeError(f"Drawing VLM did not reach adult subject review: {review_run.get('error')}")
        if not review_etag:
            raise RuntimeError("StoryRun API omitted ETag on the subject-review response.")

        subject_result = review_run.get("result") or {}
        label = str(subject_result.get("subject_label", ""))
        folded = "".join(ch for ch in unicodedata.normalize("NFKD", label.casefold()) if not unicodedata.combining(ch))
        if "buom" not in folded and "butterfly" not in folded:
            trace["parent_flow"]["adult_subject_decision"] = {"decision": "NOT_CONFIRMED", "candidate": label}
            raise RuntimeError("Synthetic drawing candidate was not recognized as a butterfly; adult did not confirm a mismatch.")

        subject_confirmed, subject_body = api_call(
            trace, session, name="adult_confirms_drawing_subject", method="POST", base_url=base,
            path=f"/v1/story-runs/{run_ref}/subject-confirmation",
            headers={"Idempotency-Key": f"{flow_id}:confirm-subject", "If-Match": review_etag},
            json={"decision": "CONFIRM", "expected_understanding_revision": subject_result["understanding_revision"]},
        )
        require_status(subject_confirmed, subject_body, {202}, "adult subject confirmation")
        trace["parent_flow"]["adult_subject_decision"] = {"decision": "CONFIRM", "candidate": label}

        prepared_run, prepared_body = api_call(
            trace, session, name="read_run_before_story", method="GET", base_url=base,
            path=f"/v1/story-runs/{run_ref}",
        )
        require_status(prepared_run, prepared_body, {200}, "read run before story")
        story_started = time.perf_counter()
        story, story_body = api_call(
            trace, session, name="generate_parent_story_once", method="POST", base_url=base,
            path=f"/v1/story-runs/{run_ref}/story-revisions",
            headers={"Idempotency-Key": f"{flow_id}:initial-story", "If-Match": prepared_run.headers["ETag"]},
            json={"expected_understanding_revision": subject_result["understanding_revision"], "adult_confirmed_idea": PARENT_ADULT_IDEA},
            timeout=(20, 1_250),
        )
        trace["parent_flow"]["story_generation_elapsed_ms"] = round((time.perf_counter() - story_started) * 1000, 2)
        if story.status_code == 202:
            trace["parent_flow"]["state"] = "STORY_OUTCOME_UNKNOWN_NO_RETRY"
            trace["parent_flow"]["story_generation_error"] = story_body
            dump_json(RESULT_PATH, {"parent_flow": trace["parent_flow"], "api_records": trace.get("api_records", [])})
            raise RuntimeError("STORY_OUTCOME_UNKNOWN_NO_RETRY")
        if story.status_code != 201:
            trace["parent_flow"]["story_generation_error"] = story_body
            raise RuntimeError(f"Story generation returned HTTP {story.status_code}: {story_body.get('code', 'unknown')}")
        revision_ref = str(story_body["story_revision_ref"])
        trace["parent_flow"]["story_revision_ref"] = revision_ref

        fetched, fetched_body = api_call(
            trace, session, name="read_story_revision", method="GET", base_url=base,
            path=f"/v1/story-runs/{run_ref}/story-revisions/{revision_ref}",
        )
        require_status(fetched, fetched_body, {200}, "read story revision")
        if fetched_body.get("status") != "DRAFT" or not fetched_body.get("story_sha256"):
            trace["parent_flow"]["state"] = "STORY_DRAFT_NOT_READY"
            trace["parent_flow"]["story_generation_error"] = fetched_body.get("status")
            raise RuntimeError(f"Story revision is not a reviewable DRAFT: {fetched_body.get('status')}")
        dump_json(RESULT_PATH, {"parent_flow": trace["parent_flow"], "story_revision": fetched_body})

        if fetched_body.get("status") == "DRAFT" and fetched_body.get("story_sha256"):
            confirmed, confirmed_body = api_call(
                trace, session, name="adult_confirms_story_revision", method="POST", base_url=base,
                path=f"/v1/story-runs/{run_ref}/story-revisions/{revision_ref}/confirmation",
                headers={"Idempotency-Key": f"{flow_id}:confirm-story", "If-Match": story.headers["ETag"]},
                json={"expected_revision": fetched_body["revision_no"], "story_sha256": fetched_body["story_sha256"]},
            )
            require_status(confirmed, confirmed_body, {200}, "adult script confirmation")
            trace["parent_flow"]["story_confirmation"] = confirmed_body
        final_run, final_body = api_call(
            trace, session, name="read_run_after_script_confirmation", method="GET", base_url=base,
            path=f"/v1/story-runs/{run_ref}",
        )
        require_status(final_run, final_body, {200}, "read run after script confirmation")
        trace["parent_flow"].update(
            {
                "state": "SUCCEEDED",
                "ended_at": now_local(),
                "final_run": final_body,
                "final_story_revision": fetched_body,
                "story_scene_count": len(fetched_body.get("scenes", [])),
                "story_duration_ms": fetched_body.get("duration_ms"),
                "video_calls": 0,
            }
        )

        # Exercise the remaining existing mutating operations without dispatching AI.
        cancelled, cancel_body = api_call(
            trace, session, name="create_run_for_cancel_test", method="POST", base_url=base,
            path="/v1/story-runs", headers={"Idempotency-Key": f"{flow_id}:cancel-run-create"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 48},
        )
        require_status(cancelled, cancel_body, {201}, "create run for cancel")
        cancelled_run, cancelled_run_body = api_call(
            trace, session, name="cancel_story_run", method="POST", base_url=base,
            path=f"/v1/story-runs/{cancel_body['run_ref']}/cancel",
            headers={"Idempotency-Key": f"{flow_id}:cancel-run", "If-Match": cancelled.headers["ETag"]},
            json={"expected_revision": cancel_body["revision"]},
        )
        require_status(cancelled_run, cancelled_run_body, {202}, "cancel story run")

        disposable_run, disposable_body = api_call(
            trace, session, name="create_run_for_upload_abort_test", method="POST", base_url=base,
            path="/v1/story-runs", headers={"Idempotency-Key": f"{flow_id}:abort-run-create"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 72},
        )
        require_status(disposable_run, disposable_body, {201}, "create run for upload abort")
        disposable_upload, disposable_upload_body = api_call(
            trace, session, name="create_upload_for_abort_test", method="POST", base_url=base,
            path="/v1/upload-sessions", headers={"Idempotency-Key": f"{flow_id}:abort-upload-create"},
            json={
                "target_ref": disposable_body["run_ref"], "purpose": "RUN_ARTWORK", "media_type": "image/png",
                "expected_size_bytes": len(image_bytes), "expected_sha256": image_sha,
            },
        )
        require_status(disposable_upload, disposable_upload_body, {201}, "create upload for abort")
        aborted, aborted_body = api_call(
            trace, session, name="abort_upload_session", method="DELETE", base_url=base,
            path=f"/v1/upload-sessions/{disposable_upload_body['upload_ref']}",
            headers={"Idempotency-Key": f"{flow_id}:abort-upload", "If-Match": disposable_upload.headers["ETag"]},
        )
        require_status(aborted, aborted_body, {202}, "abort upload")

        # Health/OpenAPI endpoints are intentionally not exposed by this standalone local API.
        for name, path in (("unmounted_health_route", "/health"), ("unmounted_openapi_route", "/openapi.json")):
            probe, probe_body = api_call(trace, session, name=name, method="GET", base_url=base, path=path)
            require_status(probe, probe_body, {404}, name)
    finally:
        stop_api_server(harness)
    dump_json(RESULT_PATH, {"parent_flow": trace.get("parent_flow"), "api_records": trace.get("api_records", [])})


def modal_payload(workload: str, request_data: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any], bytes, bytes]:
    job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
    prefix = f"sketch2life/{MODAL_ENV}/{job_id}/{generation_id}/{attempt_id}/"
    request_bytes = canonical_json(request_data)
    manifest = {
        "schema_version": "sketch2life.modal.ai-request.v1",
        "asset": {
            "path": "input/request.json",
            "content_type": "application/json",
            "size_bytes": len(request_bytes),
            "sha256": sha256(request_bytes),
        },
    }
    manifest_bytes = canonical_json(manifest)
    payload = {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": MODAL_ENV,
        "workload": workload,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": sha256(manifest_bytes),
        "input_bytes": len(manifest_bytes) + len(request_bytes),
    }
    return {"prefix": prefix, "job_id": job_id, "generation_id": generation_id, "attempt_id": attempt_id}, payload, request_bytes, manifest_bytes


def invoke_modal_worker(
    trace: dict[str, Any], *, workload: str, app_name: str, function_name: str, request_data: dict[str, Any], timeout: int
) -> dict[str, Any]:
    import modal

    identity, payload, request_bytes, manifest_bytes = modal_payload(workload, request_data)
    dispatch = {
        "state": "DISPATCH_INTENT_RECORDED",
        "workload": workload,
        "app": app_name,
        "function": function_name,
        **identity,
        "input_sha256": sha256(request_bytes),
        "manifest_sha256": sha256(manifest_bytes),
        "created_at": now_local(),
        "max_attempts": 1,
    }
    dump_json(
        ASSET_DIR / f"{workload.replace('.', '_')}_{identity['attempt_id']}_dispatch_intent.json",
        dispatch,
    )
    volume = modal.Volume.from_name(SCRATCH_VOLUME, environment_name=MODAL_ENV, version=2)
    function = modal.Function.from_name(app_name, function_name, environment_name=MODAL_ENV)
    call_id: str | None = None
    terminal = False
    started = time.perf_counter()
    with volume.batch_upload() as batch:
        batch.put_file(BytesIO(request_bytes), f"/{identity['prefix']}input/request.json")
        batch.put_file(BytesIO(manifest_bytes), f"/{identity['prefix']}input/manifest.json")
    try:
        call = function.spawn(payload)
        call_id = getattr(call, "object_id", None)
        if not isinstance(call_id, str) or not call_id.startswith("fc-"):
            raise RuntimeError("Modal dispatch result is ambiguous; do not retry.")
        result = call.get(timeout=timeout)
        terminal = True
        if not isinstance(result, dict):
            raise RuntimeError("Modal worker returned a non-object result.")
        safe_result = dict(result)
        image_bytes = None
        if isinstance(safe_result.get("asset"), dict):
            asset = dict(safe_result["asset"])
            candidate = asset.pop("bytes", None)
            safe_result["asset"] = asset
            if isinstance(candidate, bytes):
                image_bytes = candidate
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        record = {
            "workload": workload,
            "app": app_name,
            "function": function_name,
            "call_id": call_id,
            "elapsed_ms": elapsed_ms,
            "output_sha256": sha256(canonical_json(safe_result)),
            "result": safe_result,
            "outcome": "SUCCEEDED",
        }
        if image_bytes is not None:
            if sha256(image_bytes) != safe_result["asset"].get("sha256"):
                raise RuntimeError("FLUX output bytes failed their worker SHA-256 check.")
            VISUAL_PATH.write_bytes(image_bytes)
            record["asset_file"] = VISUAL_PATH.name
        trace.setdefault("modal_workers", []).append(record)
        dump_json(TRACE_PATH, trace)
        return record
    except Exception as exc:
        unknown = not terminal
        record = {
            "workload": workload,
            "app": app_name,
            "function": function_name,
            "call_id": call_id,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "outcome": "UNKNOWN_NO_RETRY" if unknown else "FAILED_TERMINAL",
            "error_type": type(exc).__name__,
        }
        trace.setdefault("modal_workers", []).append(record)
        dump_json(TRACE_PATH, trace)
        raise
    finally:
        if terminal:
            volume.remove_file(f"{identity['prefix']}input", recursive=True)


def create_slide_preview(deck: dict[str, Any], visual_path: Path) -> None:
    def esc(value: object) -> str:
        return html_lib.escape(str(value), quote=True)

    encoded_visual = base64.b64encode(visual_path.read_bytes()).decode("ascii") if visual_path.is_file() else ""
    visual_markup = f'<img class="guide" alt="Hình gợi ý vẽ do AI tạo, bản nháp" src="data:image/png;base64,{encoded_visual}">' if encoded_visual else ""
    slides: list[str] = []
    for slide in deck["slides"]:
        kind = slide["kind"]
        if kind == "orientation":
            body = "".join(f"<li>{esc(item)}</li>" for item in slide["bullets"])
        elif kind == "drawing_guide":
            body = '<ol class="steps">' + "".join(
                f"<li><b>{esc(step['instruction'])}</b><span>{esc(step['placement'])}</span></li>"
                for step in slide["steps"]
            ) + "</ol>" + visual_markup
        elif kind == "subject_exploration":
            body = "".join(f"<li>{esc(item)}</li>" for item in slide["bullets"])
        else:
            body = (
                "<div class='columns'><section><h3>Chuẩn bị</h3><ul>"
                + "".join(f"<li>{esc(x)}</li>" for x in slide["materials"] + slide["preparation"])
                + "</ul></section><section><h3>Cùng làm</h3><ol>"
                + "".join(f"<li>{esc(x)}</li>" for x in slide["instructions"])
                + "</ol></section></div><aside><b>An toàn:</b> "
                + " ".join(esc(x) for x in slide["safety_notes"])
                + "</aside>"
            )
            body = f"<p class='goal'><b>Mục tiêu:</b> {' '.join(esc(x) for x in slide['goal'])}</p>" + body
        list_tag = "ol" if kind == "drawing_guide" else "ul"
        if kind in {"orientation", "subject_exploration"}:
            body = f"<{list_tag} class='facts'>{body}</{list_tag}>"
        slides.append(
            f"<article class='slide' data-kind='{kind}'><div class='eyebrow'>Sketch2Life · Bài nháp · {slide['slide_index']:02d}/{len(deck['slides']):02d}</div>"
            f"<h1>{esc(slide['title'])}</h1>{body}</article>"
        )
    html = """<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sketch2Life · Bản xem trước bài học</title><style>
*{box-sizing:border-box}body{margin:0;background:#f2f3f0;color:#26312b;font:20px/1.45 'Segoe UI',sans-serif}.top{max-width:1200px;margin:20px auto 8px;display:flex;justify-content:space-between;align-items:center;color:#69736c;font-size:14px}.frame{width:min(1200px,calc(100vw - 40px));aspect-ratio:16/9;margin:0 auto;background:#fff;border:1px solid #dbe1d8;border-radius:18px;box-shadow:0 18px 50px #24332814;overflow:hidden;position:relative}.slide{height:100%;padding:5.4% 7%;display:none;overflow:auto}.slide.active{display:block}.eyebrow{font-size:14px;letter-spacing:.08em;text-transform:uppercase;color:#64816c}h1{font-size:clamp(28px,4vw,46px);line-height:1.15;margin:14px 0 26px;color:#2d563b}li{margin:12px 0}.facts{font-size:clamp(19px,2.1vw,27px);max-width:900px}.steps{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;padding-left:28px}.steps li{padding:10px 14px;background:#f4f7ef;border-radius:12px}.steps span{display:block;color:#69736c;font-size:16px}.guide{display:block;margin:12px auto 0;width:min(54%,580px);height:auto;max-height:45%;object-fit:contain;border-radius:12px;background:#fff}.columns{display:grid;grid-template-columns:1fr 1.2fr;gap:36px;font-size:18px}.columns h3{color:#64816c}aside{margin-top:18px;background:#fff5e5;padding:13px 17px;border-radius:12px;font-size:16px}.controls{max-width:1200px;margin:12px auto;display:flex;justify-content:center;align-items:center;gap:16px}.controls button{border:0;border-radius:999px;padding:11px 24px;background:#40764c;color:#fff;font-size:16px;cursor:pointer}.controls button:disabled{opacity:.4;cursor:default}#counter{font-variant-numeric:tabular-nums;color:#68736b}.draft{position:absolute;right:20px;top:18px;background:#fff4d8;color:#7a5721;border-radius:999px;padding:5px 12px;font-size:13px}@media(max-width:650px){body{font-size:15px}.frame{width:calc(100vw - 20px);border-radius:12px}.slide{padding:7%}.steps{grid-template-columns:1fr;gap:3px}.steps li{margin:3px}.columns{font-size:14px;gap:12px}.guide{width:70%;max-height:36%}.top,.controls{margin-left:10px;margin-right:10px}}
</style><body><div class="top"><b>Sketch2Life · Bài học: Con bướm</b><span>60 tháng · Bản nháp cần giáo viên duyệt</span></div><div class="frame"><span class="draft">DRAFT · Chưa xuất bản</span>""" + "".join(slides) + """</div>
<nav class="controls"><button id="prev">Trước</button><span id="counter"></span><button id="next">Tiếp</button></nav><script>
const slides=[...document.querySelectorAll('.slide')];let current=0;function show(n){current=Math.max(0,Math.min(slides.length-1,n));slides.forEach((s,i)=>s.classList.toggle('active',i===current));document.querySelector('#counter').textContent=`${current+1} / ${slides.length}`;document.querySelector('#prev').disabled=current===0;document.querySelector('#next').disabled=current===slides.length-1}document.querySelector('#prev').onclick=()=>show(current-1);document.querySelector('#next').onclick=()=>show(current+1);document.addEventListener('keydown',e=>{if(e.key==='ArrowRight')show(current+1);if(e.key==='ArrowLeft')show(current-1)});show(0);
</script></body></html>"""
    PREVIEW_PATH.write_text(html, encoding="utf-8")


def teacher_deck_flow(trace: dict[str, Any]) -> None:
    plan = synthetic_approved_plan()
    dump_json(PLAN_PATH, plan)
    deck_record = invoke_modal_worker(
        trace,
        workload="teacher.sketch-deck.generate",
        app_name=LANGUAGE_APP,
        function_name="generate-teacher-sketch-deck",
        request_data=plan,
        timeout=900,
    )
    deck = deck_record["result"].get("result")
    if not isinstance(deck, dict) or deck.get("status") != "DRAFT" or deck.get("aspect_ratio") != "16:9":
        raise RuntimeError("Teacher deck worker returned an invalid draft envelope.")
    dump_json(DECK_PATH, deck)
    guide = next(slide for slide in deck["slides"] if slide["kind"] == "drawing_guide")
    visual_request = {
        "schema_version": "sketch2life.lesson-visual-input.v1",
        "plan_revision_ref": plan["plan_revision_ref"],
        "content_hash": plan["content_hash"],
        "topic": plan["topic"],
        "steps": [
            {"step_index": step["step_index"], "instruction": step["instruction"], "placement": step["placement"]}
            for step in guide["steps"]
        ],
    }
    visual_record = invoke_modal_worker(
        trace,
        workload="lesson.visual.generate",
        app_name=FLUX_APP,
        function_name="generate-approved-lesson-visual-candidate",
        request_data=visual_request,
        timeout=1_200,
    )
    visual_result = visual_record["result"].get("result", visual_record["result"])
    asset = visual_result.get("asset") if isinstance(visual_result, dict) else None
    if not isinstance(asset, dict) or asset.get("width") != 768 or asset.get("height") != 432:
        raise RuntimeError("FLUX visual did not produce the expected 16:9 candidate.")
    dump_json(
        VISUAL_PROVENANCE_PATH,
        {
            "status": "DRAFT",
            "source_plan_revision_ref": plan["plan_revision_ref"],
            "source_plan_sha256": plan["content_hash"],
            "source_artifact_sha256": asset["sha256"],
            "provider_model": visual_result["model"],
            "provider_call_id": visual_record["call_id"],
            "width": asset["width"],
            "height": asset["height"],
            "review_required": True,
            "publishable": False,
        },
    )
    create_slide_preview(deck, VISUAL_PATH)
    trace["teacher_deck"] = {
        "status": "DRAFT_PREVIEW_CREATED",
        "slide_count": len(deck["slides"]),
        "drawing_step_count": len(guide["steps"]),
        "approved_activity_refs": deck["approved_activity_refs"],
        "aspect_ratio": deck["aspect_ratio"],
        "html_preview": PREVIEW_PATH.name,
        "image": VISUAL_PROVENANCE_PATH.name,
        "publishable": False,
    }
    dump_json(TRACE_PATH, trace)


def main() -> int:
    for path in (TRACE_PATH, GUARD_PATH, RESULT_PATH):
        if path.exists():
            raise SystemExit(f"Refusing to rerun a guarded POC: {path.name} already exists.")
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    trace: dict[str, Any] = {
        "started_at": now_local(),
        "feature": "FEAT-063",
        "srs_version": "2.3-draft",
        "video_called": False,
        "modal_environment": MODAL_ENV,
        "local_api_port": get_free_port(),
        "api_records": [],
        "modal_workers": [],
    }
    dump_json(GUARD_PATH, {"state": "POC_STARTED", "created_at": trace["started_at"], "max_attempts_per_ai_workload": 1, "video_enabled": False})
    dump_json(TRACE_PATH, trace)
    failures: list[dict[str, str]] = []
    try:
        parent_api_flow(trace, trace["local_api_port"])
    except Exception as exc:
        failures.append({"stage": "parent_api_flow", "error_type": type(exc).__name__, "message": str(exc)[:300]})
        trace["parent_flow"] = trace.get("parent_flow", {})
        trace["parent_flow"].update({"state": "FAILED", "ended_at": now_local(), "error_type": type(exc).__name__, "error": str(exc)[:300]})
        dump_json(RESULT_PATH, {"parent_flow": trace["parent_flow"], "api_records": trace.get("api_records", [])})
    try:
        teacher_deck_flow(trace)
    except Exception as exc:
        failures.append({"stage": "teacher_deck_flow", "error_type": type(exc).__name__, "message": str(exc)[:300]})
        trace["teacher_deck"] = {"status": "FAILED", "error_type": type(exc).__name__, "error": str(exc)[:300]}
        dump_json(TRACE_PATH, trace)
    trace.update({"ended_at": now_local(), "failures": failures, "video_called": False})
    dump_json(TRACE_PATH, trace)
    print(json.dumps({
        "trace": TRACE_PATH.name,
        "parent_state": (trace.get("parent_flow") or {}).get("state"),
        "teacher_deck_state": (trace.get("teacher_deck") or {}).get("status"),
        "api_operations": len(trace.get("api_records", [])),
        "modal_workloads": [{"workload": item["workload"], "outcome": item["outcome"], "call_id": item.get("call_id")} for item in trace.get("modal_workers", [])],
        "failures": failures,
        "video_called": False,
    }, ensure_ascii=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
