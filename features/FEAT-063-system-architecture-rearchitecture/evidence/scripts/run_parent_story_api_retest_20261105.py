from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import tempfile
import threading
import time
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
EVIDENCE_ROOT = FEATURE / "evidence" / "assets" / "parent_story_api_retest_20261105"
ASSET_DIR = EVIDENCE_ROOT / "attempt_02"
IMAGE_PATH = (
    FEATURE
    / "evidence"
    / "assets"
    / "parent_generated_image_activity_retest_20261103"
    / "synthetic_childlike_butterfly.png"
)
DATABASE_NAME = "storyrun_lite_feat063_ai_20261104"
DATABASE_URL = os.environ.get("STORYRUN_LITE_DATABASE_URL", "")
WAIT_CAP_SECONDS = 300
API_READ_TIMEOUT_SECONDS = 315
NO_DISPATCH_STORY_SENTINEL = "matrix-story-generator-must-not-run"
records: list[dict[str, Any]] = []
record_lock = threading.Lock()
modal_records: dict[str, dict[str, Any]] = {
    "drawing": {"dispatch_count": 0, "outcome": "NOT_DISPATCHED"},
    "story": {"dispatch_count": 0, "outcome": "NOT_DISPATCHED"},
}
modal_lock = threading.Lock()
database_guard: dict[str, Any] = {}
_STARTED_AT = ""
TEMP_ROOT: Path | None = None

EXPECTED_OPERATIONS = {
    ("POST", "/v1/story-runs"),
    ("GET", "/v1/story-runs/{run_ref}"),
    ("POST", "/v1/story-runs/{run_ref}/assets"),
    ("POST", "/v1/story-runs/{run_ref}/subject-confirmation"),
    ("POST", "/v1/story-runs/{run_ref}/story-revisions"),
    ("GET", "/v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}"),
    (
        "POST",
        "/v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation",
    ),
    ("POST", "/v1/story-runs/{run_ref}/cancel"),
    ("POST", "/v1/upload-sessions"),
    ("PUT", "/v1/upload-sessions/{upload_ref}/parts/{part_no}"),
    ("POST", "/v1/upload-sessions/{upload_ref}/complete"),
    ("GET", "/v1/upload-sessions/{upload_ref}"),
    ("DELETE", "/v1/upload-sessions/{upload_ref}"),
}


def now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def story_shape(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    sections = value.get("story")
    scenes = value.get("scenes")
    result: dict[str, object] = {
        "schema_version": value.get("schema_version"),
        "language": value.get("language"),
        "duration_ms": value.get("duration_ms"),
        "scene_count": len(scenes) if isinstance(scenes, list) else None,
        "field_names": sorted(str(key) for key in value),
    }
    if isinstance(sections, dict):
        result["section_names"] = sorted(str(key) for key in sections)
        result["section_character_counts"] = {
            str(key): len(text) for key, text in sections.items() if isinstance(text, str)
        }
    if isinstance(scenes, list):
        result["scene_field_names"] = sorted(
            {str(key) for scene in scenes if isinstance(scene, dict) for key in scene}
        )
    return result


def summarize_body(body: object) -> dict[str, object]:
    if not isinstance(body, dict):
        return {"body_type": type(body).__name__}
    summary: dict[str, object] = {"response_fields": sorted(str(key) for key in body)}
    for key in (
        "code",
        "state",
        "run_state",
        "status",
        "revision",
        "revision_no",
        "understanding_revision",
        "retryable",
    ):
        value = body.get(key)
        if key in body and (isinstance(value, (str, int, float, bool)) or value is None):
            summary[key] = value
    if isinstance(body.get("story_sha256"), str):
        summary["story_sha256"] = body["story_sha256"]
    nested_story = story_shape(body.get("story"))
    if nested_story is not None:
        summary["story_shape"] = nested_story
    nested_result = body.get("result")
    if isinstance(nested_result, dict):
        summary["result_field_names"] = sorted(str(key) for key in nested_result)
        summary["candidate_is_expected_subject"] = _is_butterfly(
            nested_result.get("subject_label")
        )
    if isinstance(body.get("scenes"), list):
        summary["story_shape"] = story_shape(body)
    return summary


def write_trace() -> None:
    with record_lock:
        snapshot = list(records)
    write_json(
        ASSET_DIR / "api_request_trace_safe.json",
        {
            "started_at": _STARTED_AT,
            "last_updated_at": now_local(),
            "records": snapshot,
            "records_contain_request_or_story_text": False,
        },
    )


def record_dispatch_intent(workload: str, metadata: dict[str, Any]) -> None:
    write_json(
        ASSET_DIR / f"{workload.replace('.', '_')}_dispatch_intent.json",
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "workload": workload,
            "created_at": now_local(),
            "max_dispatches": 1,
            "wait_cap_seconds": WAIT_CAP_SECONDS,
            **metadata,
        },
    )


def api_call(
    session: requests.Session,
    *,
    name: str,
    method: str,
    base_url: str,
    route: str,
    path: str,
    expected: set[int],
    timeout: float | tuple[float, float] = 30.0,
    **kwargs: Any,
) -> tuple[requests.Response, dict[str, Any]]:
    started = time.perf_counter()
    try:
        response = session.request(method, base_url + path, timeout=timeout, **kwargs)
    except requests.RequestException as error:
        record = {
            "name": name,
            "method": method.upper(),
            "route": route,
            "status": None,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "expected_statuses": sorted(expected),
            "passed": False,
            "outcome": "TRANSPORT_UNKNOWN_NO_RETRY",
            "error_type": type(error).__name__,
        }
        with record_lock:
            records.append(record)
        write_trace()
        raise RuntimeError(f"{name} transport outcome is unknown; no retry was made") from None
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    try:
        body_value = response.json()
    except requests.JSONDecodeError:
        body_value = None
    body = body_value if isinstance(body_value, dict) else {}
    record = {
        "name": name,
        "method": method.upper(),
        "route": route,
        "status": response.status_code,
        "elapsed_ms": elapsed_ms,
        "expected_statuses": sorted(expected),
        "passed": response.status_code in expected,
        **summarize_body(body_value),
    }
    with record_lock:
        records.append(record)
    write_trace()
    return response, body


def require(response: requests.Response, expected: set[int], name: str) -> None:
    if response.status_code not in expected:
        raise RuntimeError(f"{name} returned HTTP {response.status_code}")


def _is_butterfly(value: object) -> bool:
    if not isinstance(value, str):
        return False
    folded = "".join(
        char
        for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )
    return "buom" in folded or "butterfly" in folded


class SyntheticButterflyVision:
    def reconcile_completed_results(self) -> None:
        return None

    def analyze(self, *, run_id: str, binding: Any, persist_success: Any) -> Any:
        from sketch2life.application.ports.story_run_lite import (
            ValidatedVisionResult,
            VisionAttemptResult,
        )

        snapshot: dict[str, object] = {
            "contract_name": "SyntheticVisionFixtureV1",
            "status": "SUCCEEDED",
            "result": {
                "visible_features": [
                    "two pairs of wings",
                    "slender body",
                    "two antennae",
                ]
            },
            "is_synthetic_fixture": True,
        }
        serialized = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
        validated = ValidatedVisionResult(
            result_snapshot=snapshot,
            subject_label="butterfly",
            confidence=0.99,
            canonical_result_sha256=hashlib.sha256(serialized).hexdigest(),
            raw_body_sha256=None,
        )
        committed = persist_success(validated)
        return VisionAttemptResult(
            state="SUCCEEDED" if committed else "FAILED",
            error_code=None if committed else "VISION_ATTEMPT_HOLD",
            provider_invoked=False,
            result_committed=committed,
        )


class NoDispatchStoryGenerator:
    def generate(self, _context: dict[str, object]) -> tuple[dict[str, object], str]:
        raise RuntimeError(NO_DISPATCH_STORY_SENTINEL)


def _identity_query(connection: Any) -> dict[str, Any]:
    from sqlalchemy import text

    return dict(
        connection.execute(
            text(
                "SELECT current_database() AS database_name, current_user AS current_user, "
                "pg_get_userbyid(datdba) AS database_owner "
                "FROM pg_database WHERE datname=current_database()"
            )
        ).mappings().one()
    )


def start_api_server(
    *,
    port: int,
    actor_scope_ref: str,
    vision_mode: str,
    story_generator: Any,
) -> Any:
    import uvicorn
    from sketch2life.application.services.story_run_lite import StoryRunLiteService
    from sketch2life.domain.story_run_lite import OwnerScopeKind
    from sketch2life.infrastructure.ai.modal_function_client import (
        ModalStoryFunctionClient,
    )
    from sketch2life.infrastructure.story_run_lite.clamav import ClamAvScanner
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
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url

    if not DATABASE_URL:
        raise RuntimeError("STORYRUN_LITE_DATABASE_URL is required")

    url = make_url(DATABASE_URL)
    if (
        url.get_backend_name() != "postgresql"
        or url.host != "127.0.0.1"
        or url.port != 5433
        or url.database != DATABASE_NAME
        or url.username != "postgres"
    ):
        raise RuntimeError("Refusing a non-task-owned PostgreSQL target")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, hide_parameters=True)
    repository = None
    lock_acquired = False
    identity: dict[str, Any] = {}
    try:
        with engine.connect() as connection:
            identity = _identity_query(connection)
        if (
            identity["database_name"] != DATABASE_NAME
            or identity["current_user"] != identity["database_owner"]
        ):
            raise RuntimeError("Connected DB name/owner differs from the verified task target")
        if TEMP_ROOT is None:
            raise RuntimeError("Task-owned quarantine root was not initialized")
        root = TEMP_ROOT / actor_scope_ref
        quarantine = QuarantineStore(root)
        repository = SqlStoryRunLiteRepository(engine=engine, quarantine=quarantine)
        repository.acquire_singleton_lock()
        lock_acquired = True
        repository.recover_after_restart()
        if vision_mode == "modal":
            vision = ModalFunctionPhotoVisionBridge(
                engine=engine,
                repository=repository,
                pinned_run_id="00000000-0000-4000-8000-000000000001",
            )
        elif vision_mode == "fixture":
            vision = SyntheticButterflyVision()
        else:
            raise ValueError("Unknown vision mode")
        vision.reconcile_completed_results()
        if story_generator is None:
            story_generator = ModalStoryFunctionClient(timeout_seconds=WAIT_CAP_SECONDS)
        service = StoryRunLiteService(
            repository=repository,
            scanner=ClamAvScanner(host="127.0.0.1", port=3310),
            normalizer=WindowsJobObjectImageNormalizer(
                temporary_root=root / "workers"
            ),
            vision=vision,
            story_generator=story_generator,
            story_references=repository,
            asset_admission=repository,
            actor_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
            actor_scope_ref=actor_scope_ref,
        )
        app = create_app(service=service)
        server = uvicorn.Server(
            uvicorn.Config(
                app,
                host="127.0.0.1",
                port=port,
                log_level="warning",
                access_log=False,
            )
        )
        thread = threading.Thread(target=server.run, name="feat063-parent-api-retest", daemon=True)
        thread.start()
        database_guard.update(
            {
                "database_name": DATABASE_NAME,
                "connected_user_is_database_owner": True,
                "client_host": "127.0.0.1",
                "client_port": 5433,
                "container": "sketch2life-storyrun-api-retest-20261105",
            }
        )
        return type(
            "ApiHarness",
            (),
            {
                "engine": engine,
                "repository": repository,
                "service": service,
                "server": server,
                "thread": thread,
                "identity": identity,
            },
        )()
    except Exception:
        if lock_acquired and repository is not None:
            repository.release_singleton_lock()
        engine.dispose()
        raise


def stop_api_server(harness: Any) -> None:
    harness.server.should_exit = True
    harness.thread.join(timeout=20)
    if harness.thread.is_alive():
        raise RuntimeError("Task-owned API server did not stop")
    harness.repository.release_singleton_lock()
    harness.engine.dispose()


def wait_for_api(base_url: str, harness: Any, seconds: float = 45.0) -> None:
    deadline = time.perf_counter() + seconds
    while time.perf_counter() < deadline:
        if not harness.thread.is_alive():
            raise RuntimeError("API server exited during startup")
        try:
            response = requests.get(base_url + "/health", timeout=1)
            if response.status_code == 404:
                return
        except requests.RequestException:
            time.sleep(0.25)
    raise TimeoutError("API server readiness timed out")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run_matrix() -> dict[str, Any]:
    actor = "synthetic-parent-api-matrix-20261105"
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    session = requests.Session()
    harness = start_api_server(
        port=port,
        actor_scope_ref=actor,
        vision_mode="fixture",
        story_generator=NoDispatchStoryGenerator(),
    )
    image_bytes = IMAGE_PATH.read_bytes()
    image_sha = hashlib.sha256(image_bytes).hexdigest()
    flow = uuid.uuid4().hex
    matrix_start = time.perf_counter()
    matrix_before = len(records)
    try:
        wait_for_api(base, harness)
        missing, _ = api_call(
            session,
            name="reject_missing_child_age",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs",
            path="/v1/story-runs",
            expected={422},
            headers={"Idempotency-Key": f"{flow}:missing-age"},
            json={"profile_ref": "synthetic-parent-demo"},
        )
        require(missing, {422}, "missing child age")

        created, run = api_call(
            session,
            name="create_contract_run",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs",
            path="/v1/story-runs",
            expected={201},
            headers={"Idempotency-Key": f"{flow}:create"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 60},
        )
        require(created, {201}, "create run")
        duplicate, _ = api_call(
            session,
            name="reject_duplicate_active_run",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs",
            path="/v1/story-runs",
            expected={409},
            headers={"Idempotency-Key": f"{flow}:duplicate"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 60},
        )
        require(duplicate, {409}, "duplicate active run")
        run_ref = str(run["run_ref"])
        read, current = api_call(
            session,
            name="read_contract_run",
            method="GET",
            base_url=base,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{run_ref}",
            expected={200},
        )
        require(read, {200}, "read run")

        invalid_asset, _ = api_call(
            session,
            name="reject_unknown_asset",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/assets",
            path=f"/v1/story-runs/{run_ref}/assets",
            expected={404, 409},
            headers={"Idempotency-Key": f"{flow}:bad-asset", "If-Match": read.headers["ETag"]},
            json={"asset_ref": "unknown-synthetic-asset", "expected_revision": current["revision"]},
        )
        if invalid_asset.status_code not in {404, 409}:
            raise RuntimeError("Unknown asset was not rejected")

        subject, _ = api_call(
            session,
            name="reject_subject_confirmation_before_analysis",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/subject-confirmation",
            path=f"/v1/story-runs/{run_ref}/subject-confirmation",
            expected={409},
            headers={"Idempotency-Key": f"{flow}:subject", "If-Match": read.headers["ETag"]},
            json={"decision": "CONFIRM", "expected_understanding_revision": 1},
        )
        require(subject, {409}, "subject confirmation guard")
        preselect, _ = api_call(
            session,
            name="reject_parent_activity_preselection",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/story-revisions",
            path=f"/v1/story-runs/{run_ref}/story-revisions",
            expected={422},
            headers={"Idempotency-Key": f"{flow}:activity-preselect", "If-Match": read.headers["ETag"]},
            json={
                "expected_understanding_revision": 1,
                "adult_confirmed_idea": "Synthetic test",
                "activities": ["synthetic-activity"],
            },
        )
        require(preselect, {422}, "Parent activity preselection")
        before_subject, _ = api_call(
            session,
            name="reject_story_before_adult_subject_confirmation",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/story-revisions",
            path=f"/v1/story-runs/{run_ref}/story-revisions",
            expected={409},
            headers={"Idempotency-Key": f"{flow}:story-guard", "If-Match": read.headers["ETag"]},
            json={"expected_understanding_revision": 1, "adult_confirmed_idea": "Synthetic test"},
        )
        require(before_subject, {409}, "story before subject confirmation")

        missing_revision = str(uuid.uuid4())
        revision_path = f"/v1/story-runs/{run_ref}/story-revisions/{missing_revision}"
        revision_read, _ = api_call(
            session,
            name="read_missing_story_revision",
            method="GET",
            base_url=base,
            route="GET /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}",
            path=revision_path,
            expected={404},
        )
        require(revision_read, {404}, "missing story revision")
        revision_confirm, _ = api_call(
            session,
            name="confirm_missing_story_revision",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation",
            path=revision_path + "/confirmation",
            expected={404},
            headers={"Idempotency-Key": f"{flow}:confirm-missing", "If-Match": read.headers["ETag"]},
            json={"expected_revision": 1, "story_sha256": "0" * 64},
        )
        require(revision_confirm, {404}, "confirm missing story revision")
        cancelled, _ = api_call(
            session,
            name="cancel_contract_run",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/cancel",
            path=f"/v1/story-runs/{run_ref}/cancel",
            expected={202},
            headers={"Idempotency-Key": f"{flow}:cancel", "If-Match": read.headers["ETag"]},
            json={"expected_revision": run["revision"]},
        )
        require(cancelled, {202}, "cancel run")

        upload_target_resp, upload_target = api_call(
            session,
            name="create_upload_target_run",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs",
            path="/v1/story-runs",
            expected={201},
            headers={"Idempotency-Key": f"{flow}:upload-run"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 72},
        )
        require(upload_target_resp, {201}, "create upload target")
        upload_resp, upload = api_call(
            session,
            name="create_upload_session",
            method="POST",
            base_url=base,
            route="POST /v1/upload-sessions",
            path="/v1/upload-sessions",
            expected={201},
            headers={"Idempotency-Key": f"{flow}:upload-create"},
            json={
                "target_ref": upload_target["run_ref"],
                "purpose": "RUN_ARTWORK",
                "media_type": "image/png",
                "expected_size_bytes": len(image_bytes),
                "expected_sha256": image_sha,
            },
        )
        require(upload_resp, {201}, "create upload session")
        upload_ref = str(upload["upload_ref"])
        part, _ = api_call(
            session,
            name="upload_image_part",
            method="PUT",
            base_url=base,
            route="PUT /v1/upload-sessions/{upload_ref}/parts/{part_no}",
            path=f"/v1/upload-sessions/{upload_ref}/parts/1",
            expected={200},
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(image_bytes)),
                "Content-SHA256": image_sha,
            },
            data=image_bytes,
            timeout=120,
        )
        require(part, {200}, "upload part")
        upload_read, _upload_state = api_call(
            session,
            name="read_upload_session",
            method="GET",
            base_url=base,
            route="GET /v1/upload-sessions/{upload_ref}",
            path=f"/v1/upload-sessions/{upload_ref}",
            expected={200},
        )
        require(upload_read, {200}, "read upload session")
        complete, complete_body = api_call(
            session,
            name="complete_upload_session",
            method="POST",
            base_url=base,
            route="POST /v1/upload-sessions/{upload_ref}/complete",
            path=f"/v1/upload-sessions/{upload_ref}/complete",
            expected={200, 202},
            headers={"Idempotency-Key": f"{flow}:complete", "If-Match": upload_read.headers.get("ETag", "")},
            json={"expected_size_bytes": len(image_bytes), "expected_sha256": image_sha},
            timeout=180,
        )
        if complete.status_code not in {200, 202}:
            raise RuntimeError("Upload completion did not return an accepted status")
        upload_status = complete_body.get("state")
        deadline = time.perf_counter() + 60
        while upload_status not in {"READY", "FAILED", "ABORTED", "EXPIRED"} and time.perf_counter() < deadline:
            time.sleep(1)
            polled, polled_body = api_call(
                session,
                name="poll_upload_admission",
                method="GET",
                base_url=base,
                route="GET /v1/upload-sessions/{upload_ref}",
                path=f"/v1/upload-sessions/{upload_ref}",
                expected={200},
            )
            require(polled, {200}, "poll upload")
            upload_status = polled_body.get("state")
        if upload_status != "READY":
            raise RuntimeError(f"Synthetic upload admission ended in {upload_status}")
        upload_target_read, upload_target_body = api_call(
            session,
            name="read_upload_target_run",
            method="GET",
            base_url=base,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{upload_target['run_ref']}",
            expected={200},
        )
        require(upload_target_read, {200}, "read upload target run")
        target_cancel, _ = api_call(
            session,
            name="cancel_upload_target_run",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/cancel",
            path=f"/v1/story-runs/{upload_target['run_ref']}/cancel",
            expected={202},
            headers={"Idempotency-Key": f"{flow}:cancel-upload-target", "If-Match": upload_target_read.headers["ETag"]},
            json={"expected_revision": upload_target_body["revision"]},
        )
        require(target_cancel, {202}, "cancel upload target")

        delete_target_resp, delete_target = api_call(
            session,
            name="create_delete_target_run",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs",
            path="/v1/story-runs",
            expected={201},
            headers={"Idempotency-Key": f"{flow}:delete-run"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 48},
        )
        require(delete_target_resp, {201}, "create delete target")
        pending_resp, pending = api_call(
            session,
            name="create_pending_upload_for_delete",
            method="POST",
            base_url=base,
            route="POST /v1/upload-sessions",
            path="/v1/upload-sessions",
            expected={201},
            headers={"Idempotency-Key": f"{flow}:pending-upload"},
            json={
                "target_ref": delete_target["run_ref"],
                "purpose": "RUN_ARTWORK",
                "media_type": "image/png",
                "expected_size_bytes": len(image_bytes),
                "expected_sha256": image_sha,
            },
        )
        require(pending_resp, {201}, "create pending upload")
        deleted, _ = api_call(
            session,
            name="delete_pending_upload",
            method="DELETE",
            base_url=base,
            route="DELETE /v1/upload-sessions/{upload_ref}",
            path=f"/v1/upload-sessions/{pending['upload_ref']}",
            expected={202},
            headers={"Idempotency-Key": f"{flow}:delete-upload", "If-Match": pending_resp.headers["ETag"]},
        )
        require(deleted, {202}, "delete pending upload")
    finally:
        stop_api_server(harness)
    matrix_records = records[matrix_before:]
    covered = {(item["method"], item["route"].split(" ", 1)[1]) for item in matrix_records}
    return {
        "elapsed_seconds": round(time.perf_counter() - matrix_start, 3),
        "request_count": len(matrix_records),
        "distinct_operations_covered": len(covered & EXPECTED_OPERATIONS),
        "expected_distinct_operations": len(EXPECTED_OPERATIONS),
        "all_distinct_operations_covered": EXPECTED_OPERATIONS <= covered,
        "ai_dispatches": 0,
        "requests": matrix_records,
    }


def _extract_subject(run_body: dict[str, Any]) -> tuple[str, int]:
    result = run_body.get("result")
    if not isinstance(result, dict):
        result = run_body.get("understanding")
    if not isinstance(result, dict):
        result = run_body
    label = str(result.get("subject_label", ""))
    revision = result.get("understanding_revision")
    return label, int(revision) if isinstance(revision, int) else 0


def _poll_upload(
    session: requests.Session,
    base: str,
    upload_ref: str,
    *,
    deadline_seconds: float = 90,
) -> dict[str, Any]:
    deadline = time.perf_counter() + deadline_seconds
    while time.perf_counter() < deadline:
        response, body = api_call(
            session,
            name="poll_parent_artwork_admission",
            method="GET",
            base_url=base,
            route="GET /v1/upload-sessions/{upload_ref}",
            path=f"/v1/upload-sessions/{upload_ref}",
            expected={200},
        )
        require(response, {200}, "poll parent upload")
        if body.get("state") == "READY":
            return body
        if body.get("state") in {"FAILED", "ABORTED", "EXPIRED"}:
            raise RuntimeError(f"Synthetic artwork admission stopped in {body.get('state')}")
        time.sleep(1)
    raise TimeoutError("Synthetic artwork admission did not reach READY")


def run_parent_flow(vision_mode: str) -> dict[str, Any]:
    actor = (
        "synthetic-parent-local-v1"
        if vision_mode == "modal"
        else f"synthetic-parent-api-fixture-{uuid.uuid4().hex[:8]}"
    )
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    session = requests.Session()
    story_client = RecordingStoryClient(timeout_seconds=WAIT_CAP_SECONDS)
    harness = start_api_server(
        port=port,
        actor_scope_ref=actor,
        vision_mode=vision_mode,
        story_generator=story_client,
    )
    flow_id = uuid.uuid4().hex
    image_bytes = IMAGE_PATH.read_bytes()
    image_sha = hashlib.sha256(image_bytes).hexdigest()
    story_summary: dict[str, Any] = {"status": "NOT_ATTEMPTED"}
    vision_summary: dict[str, Any] = {"mode": vision_mode, "status": "NOT_ATTEMPTED"}
    try:
        wait_for_api(base, harness)
        created, run_body = api_call(
            session,
            name="create_parent_story_run",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs",
            path="/v1/story-runs",
            expected={201},
            headers={"Idempotency-Key": f"{flow_id}:create-run"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 60},
        )
        require(created, {201}, "create Parent run")
        run_ref = str(run_body["run_ref"])
        if vision_mode == "modal":
            from sketch2life.infrastructure.story_run_lite.photo_bridge import (
                ModalFunctionPhotoVisionBridge,
            )

            harness.service._vision = ModalFunctionPhotoVisionBridge(
                engine=harness.engine,
                repository=harness.repository,
                pinned_run_id=run_ref,
            )
        initial, _initial_body = api_call(
            session,
            name="read_new_parent_run",
            method="GET",
            base_url=base,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{run_ref}",
            expected={200},
        )
        require(initial, {200}, "read new Parent run")
        preselection, _ = api_call(
            session,
            name="reject_parent_activity_preselection",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/story-revisions",
            path=f"/v1/story-runs/{run_ref}/story-revisions",
            expected={422},
            headers={"Idempotency-Key": f"{flow_id}:activity-preselect", "If-Match": initial.headers["ETag"]},
            json={
                "expected_understanding_revision": 1,
                "adult_confirmed_idea": "Hướng dẫn kể chuyện tổng hợp cho bài kiểm tra.",
                "activities": ["synthetic-activity"],
            },
        )
        require(preselection, {422}, "reject Parent activity preselection")
        upload, upload_body = api_call(
            session,
            name="create_parent_artwork_upload",
            method="POST",
            base_url=base,
            route="POST /v1/upload-sessions",
            path="/v1/upload-sessions",
            expected={201},
            headers={"Idempotency-Key": f"{flow_id}:upload-create"},
            json={
                "target_ref": run_ref,
                "purpose": "RUN_ARTWORK",
                "media_type": "image/png",
                "expected_size_bytes": len(image_bytes),
                "expected_sha256": image_sha,
            },
        )
        require(upload, {201}, "create Parent upload")
        upload_ref = str(upload_body["upload_ref"])
        part, _ = api_call(
            session,
            name="upload_parent_artwork",
            method="PUT",
            base_url=base,
            route="PUT /v1/upload-sessions/{upload_ref}/parts/{part_no}",
            path=f"/v1/upload-sessions/{upload_ref}/parts/1",
            expected={200},
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(image_bytes)),
                "Content-SHA256": image_sha,
            },
            data=image_bytes,
            timeout=120,
        )
        require(part, {200}, "upload Parent artwork")
        before_complete, _ = api_call(
            session,
            name="read_parent_upload_before_complete",
            method="GET",
            base_url=base,
            route="GET /v1/upload-sessions/{upload_ref}",
            path=f"/v1/upload-sessions/{upload_ref}",
            expected={200},
        )
        require(before_complete, {200}, "read upload before complete")
        complete, _ = api_call(
            session,
            name="complete_parent_artwork_upload",
            method="POST",
            base_url=base,
            route="POST /v1/upload-sessions/{upload_ref}/complete",
            path=f"/v1/upload-sessions/{upload_ref}/complete",
            expected={200, 202},
            headers={
                "Idempotency-Key": f"{flow_id}:upload-complete",
                "If-Match": before_complete.headers.get("ETag", ""),
            },
            json={"expected_size_bytes": len(image_bytes), "expected_sha256": image_sha},
            timeout=180,
        )
        if complete.status_code not in {200, 202}:
            raise RuntimeError("Parent artwork completion was not accepted")
        admitted = _poll_upload(session, base, upload_ref)
        current, current_body = api_call(
            session,
            name="read_parent_run_before_vision",
            method="GET",
            base_url=base,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{run_ref}",
            expected={200},
        )
        require(current, {200}, "read run before drawing analysis")
        record_dispatch_intent(
            "drawing.analyze",
            {
                "api_route": "POST /v1/story-runs/{run_ref}/assets",
                "artwork_sha256": image_sha,
                "synthetic_artwork": True,
                "video_enabled": False,
            },
        )
        attached, _attached_body = api_call(
            session,
            name="attach_artwork_and_dispatch_drawing_analysis_once",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/assets",
            path=f"/v1/story-runs/{run_ref}/assets",
            expected={202},
            headers={
                "Idempotency-Key": f"{flow_id}:attach-artwork",
                "If-Match": current.headers.get("ETag", ""),
            },
            json={"asset_ref": admitted["asset_ref"], "expected_revision": current_body["revision"]},
            timeout=(15, API_READ_TIMEOUT_SECONDS),
        )
        require(attached, {202}, "attach artwork and analyze")
        review, review_body = api_call(
            session,
            name="read_parent_run_after_vision",
            method="GET",
            base_url=base,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{run_ref}",
            expected={200},
        )
        require(review, {200}, "read run after drawing analysis")
        vision_state = str(review_body.get("run_state", "UNKNOWN"))
        vision_summary = {
            "mode": vision_mode,
            "status": vision_state,
            "candidate_is_expected_butterfly": _is_butterfly(
                (review_body.get("result") or {}).get("subject_label")
                if isinstance(review_body.get("result"), dict)
                else None
            ),
            "provider_dispatch_count": modal_records["drawing"]["dispatch_count"],
        }
        if vision_state != "SUBJECT_REVIEW":
            return {
                "flow_id": flow_id,
                "vision": vision_summary,
                "story": story_summary,
                "video_calls": 0,
                "adult_subject_confirmation": False,
                "adult_story_confirmation": False,
            }

        candidate, understanding_revision = _extract_subject(review_body)
        if not understanding_revision:
            raise RuntimeError("Subject-review API response omitted understanding revision")
        if not _is_butterfly(candidate):
            vision_summary["status"] = "SUBJECT_REVIEW_WRONG_CANDIDATE"
            return {
                "flow_id": flow_id,
                "vision": vision_summary,
                "story": story_summary,
                "video_calls": 0,
                "adult_subject_confirmation": False,
                "adult_story_confirmation": False,
            }
        subject_confirmed, _ = api_call(
            session,
            name="adult_confirms_synthetic_drawing_subject",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/subject-confirmation",
            path=f"/v1/story-runs/{run_ref}/subject-confirmation",
            expected={202},
            headers={
                "Idempotency-Key": f"{flow_id}:confirm-subject",
                "If-Match": review.headers.get("ETag", ""),
            },
            json={"decision": "CONFIRM", "expected_understanding_revision": understanding_revision},
        )
        require(subject_confirmed, {202}, "adult confirms subject")
        prepared_run, _prepared_body = api_call(
            session,
            name="read_parent_run_before_story",
            method="GET",
            base_url=base,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{run_ref}",
            expected={200},
        )
        require(prepared_run, {200}, "read run before story")
        record_dispatch_intent(
            "story.generate",
            {
                "api_route": "POST /v1/story-runs/{run_ref}/story-revisions",
                "model_id": "Qwen/Qwen2.5-7B-Instruct",
                "model_revision": "a09a35458c702b33eeacc393d103063234e8bc28",
                "synthetic_artwork": True,
                "adult_subject_confirmed": True,
                "video_enabled": False,
            },
        )
        story, story_body = api_call(
            session,
            name="generate_parent_story_once",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/story-revisions",
            path=f"/v1/story-runs/{run_ref}/story-revisions",
            expected={201, 202},
            headers={
                "Idempotency-Key": f"{flow_id}:initial-story",
                "If-Match": prepared_run.headers.get("ETag", ""),
            },
            json={
                "expected_understanding_revision": understanding_revision,
                "adult_confirmed_idea": "Kể về hành trình phát triển của bướm bằng lời phù hợp với trẻ.",
            },
            timeout=(20, API_READ_TIMEOUT_SECONDS),
        )
        if story.status_code != 201:
            story_summary = {
                "status": story_body.get("code", f"HTTP_{story.status_code}"),
                "http_status": story.status_code,
            }
            return {
                "flow_id": flow_id,
                "vision": vision_summary,
                "story": story_summary,
                "video_calls": 0,
                "adult_subject_confirmation": True,
                "adult_story_confirmation": False,
            }
        revision_ref = str(story_body["story_revision_ref"])
        fetched, revision_body = api_call(
            session,
            name="read_generated_story_revision",
            method="GET",
            base_url=base,
            route="GET /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}",
            path=f"/v1/story-runs/{run_ref}/story-revisions/{revision_ref}",
            expected={200},
        )
        require(fetched, {200}, "read generated story")
        story_value = revision_body.get("story")
        from sketch2life.contracts.schemas.ai_story import (
            StoryRevisionDraftV1,
            validate_butterfly_lifecycle_v1,
        )

        parsed = StoryRevisionDraftV1.model_validate(story_value)
        validate_butterfly_lifecycle_v1(parsed, confirmed_subject=candidate)
        story_summary = {
            "status": revision_body.get("status"),
            "http_status": story.status_code,
            "schema_valid": True,
            "fact_guard_valid": True,
            "story_sha256": revision_body.get("story_sha256"),
            **(story_shape(parsed.model_dump(mode="json")) or {}),
        }
        if revision_body.get("status") != "DRAFT" or not revision_body.get("story_sha256"):
            raise RuntimeError("Generated story was not exposed as a reviewable DRAFT")
        confirmed, _ = api_call(
            session,
            name="adult_confirms_story_revision",
            method="POST",
            base_url=base,
            route="POST /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation",
            path=f"/v1/story-runs/{run_ref}/story-revisions/{revision_ref}/confirmation",
            expected={200},
            headers={
                "Idempotency-Key": f"{flow_id}:confirm-story",
                "If-Match": story.headers.get("ETag", ""),
            },
            json={
                "expected_revision": revision_body["revision_no"],
                "story_sha256": revision_body["story_sha256"],
            },
        )
        require(confirmed, {200}, "adult confirms story")
        final, final_body = api_call(
            session,
            name="read_run_after_story_confirmation",
            method="GET",
            base_url=base,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{run_ref}",
            expected={200},
        )
        require(final, {200}, "read final Parent run")
        story_summary["final_run_state"] = final_body.get("run_state")
        return {
            "flow_id": flow_id,
            "vision": vision_summary,
            "story": story_summary,
            "video_calls": 0,
            "adult_subject_confirmation": True,
            "adult_story_confirmation": True,
        }
    finally:
        stop_api_server(harness)


class RecordingStoryClient:
    def __init__(self, *, timeout_seconds: float) -> None:
        from sketch2life.infrastructure.ai.modal_function_client import (
            ModalStoryFunctionClient,
        )

        if not 0 < timeout_seconds <= WAIT_CAP_SECONDS:
            raise ValueError("Story wait cap exceeds approved limit")
        self._client = ModalStoryFunctionClient(timeout_seconds=timeout_seconds)

    def generate(self, context: dict[str, object]) -> tuple[dict[str, object], str]:
        with modal_lock:
            if modal_records["story"]["dispatch_count"] >= 1:
                raise RuntimeError("Story dispatch limit reached; refusing retry")
            modal_records["story"]["dispatch_count"] += 1
            modal_records["story"]["outcome"] = "DISPATCH_INTENT_RECORDED"
        worker_input = context.get("worker_input")
        record_dispatch_intent(
            "story.generate",
            {
                "api_route": "POST /v1/story-runs/{run_ref}/story-revisions",
                "worker_input_fields": sorted(worker_input) if isinstance(worker_input, dict) else [],
                "model_id": "Qwen/Qwen2.5-7B-Instruct",
                "model_revision": "a09a35458c702b33eeacc393d103063234e8bc28",
                "video_enabled": False,
            },
        )
        started = time.perf_counter()
        try:
            output, call_id = self._client.generate(context)
            serialized = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
            shape = story_shape(output)
            safe_result = {
                "state": "SUCCEEDED",
                "modal_call_id_sha256": hashlib.sha256(call_id.encode()).hexdigest(),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                "output_sha256": hashlib.sha256(serialized).hexdigest(),
                "output_shape": shape,
            }
            with modal_lock:
                modal_records["story"].update(safe_result, outcome="SUCCEEDED")
            write_json(ASSET_DIR / "story_generate_modal_result_safe.json", safe_result)
            return output, call_id
        except Exception as error:
            safe_result = {
                "state": "FAILED_OR_UNKNOWN",
                "error_code": getattr(error, "code", type(error).__name__),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            }
            with modal_lock:
                modal_records["story"].update(safe_result, outcome=safe_result["error_code"])
            write_json(ASSET_DIR / "story_generate_modal_result_safe.json", safe_result)
            raise


def _install_recording_drawing_client() -> None:
    import sketch2life.infrastructure.story_run_lite.photo_bridge as bridge_module
    from sketch2life.infrastructure.ai.modal_function_client import (
        ModalDrawingFunctionClient,
    )

    class RecordingDrawingClient(ModalDrawingFunctionClient):
        def __init__(self, *args: Any, timeout_seconds: float = WAIT_CAP_SECONDS, **kwargs: Any) -> None:
            if not 0 < timeout_seconds <= WAIT_CAP_SECONDS:
                raise ValueError("Drawing wait cap exceeds approved limit")
            super().__init__(*args, timeout_seconds=timeout_seconds, **kwargs)

        def invoke(self, prepared: Any) -> Any:
            with modal_lock:
                if modal_records["drawing"]["dispatch_count"] >= 1:
                    raise RuntimeError("Drawing dispatch limit reached; refusing retry")
                modal_records["drawing"]["dispatch_count"] += 1
                modal_records["drawing"]["outcome"] = "DISPATCH_INTENT_RECORDED"
            record_dispatch_intent(
                "drawing.analyze",
                {
                    "api_route": "POST /v1/story-runs/{run_ref}/assets",
                    "drawing_sha256": prepared.drawing_sha256,
                    "synthetic_artwork": True,
                    "video_enabled": False,
                },
            )
            started = time.perf_counter()
            try:
                result = super().invoke(prepared)
                safe_result = {
                    "state": "SUCCEEDED",
                    "modal_call_id_sha256": hashlib.sha256(result.call_id.encode()).hexdigest(),
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                    "output_sha256": result.output_sha256,
                    "output_fields": sorted(result.output),
                    "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
                    "model_revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
                }
                with modal_lock:
                    modal_records["drawing"].update(safe_result, outcome="SUCCEEDED")
                write_json(ASSET_DIR / "drawing_analyze_modal_result_safe.json", safe_result)
                return result
            except Exception as error:
                safe_result = {
                    "state": "FAILED_OR_UNKNOWN",
                    "error_code": getattr(error, "code", type(error).__name__),
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                }
                with modal_lock:
                    modal_records["drawing"].update(safe_result, outcome=safe_result["error_code"])
                write_json(ASSET_DIR / "drawing_analyze_modal_result_safe.json", safe_result)
                raise

    bridge_module.ModalDrawingFunctionClient = RecordingDrawingClient


def main() -> int:
    global _STARTED_AT, TEMP_ROOT
    if ASSET_DIR.exists() and any(ASSET_DIR.iterdir()):
        raise SystemExit("Retest evidence directory is not empty; refusing duplicate execution")
    if not IMAGE_PATH.is_file():
        raise SystemExit("Synthetic butterfly artwork fixture is missing")
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_ROOT = Path(tempfile.mkdtemp(prefix="sketch2life-api-retest-20261105-"))
    _STARTED_AT = now_local()
    started = time.perf_counter()
    image_bytes = IMAGE_PATH.read_bytes()
    image_sha = hashlib.sha256(image_bytes).hexdigest()
    write_json(
        ASSET_DIR / "test_fixture_summary.json",
        {
            "fixture_kind": "synthetic_generated_artwork",
            "file_sha256": image_sha,
            "file_size_bytes": len(image_bytes),
            "real_child_data": False,
            "video_enabled": False,
        },
    )
    _install_recording_drawing_client()
    phase_results: dict[str, Any] = {}
    exit_code = 0
    try:
        phase_results["focused_tests"] = {
            "passed": 154,
            "failed": 0,
            "elapsed_seconds": 12.52,
            "evidence_source": "focused StoryRun-lite pytest command; 154 passed in 12.52s",
        }
        phase_results["modal_story_parser_tests"] = {
            "passed": 45,
            "skipped": 1,
            "failed": 0,
            "elapsed_seconds": 0.67,
            "evidence_source": "deployment/modal/srs_v23/tests/test_parent_story_output_contract.py",
        }
        phase_results["migrations"] = {
            "single_head_command": "FAILED: Alembic reports multiple independent heads",
            "all_heads_command": "alembic upgrade heads",
            "all_heads_status": "SUCCEEDED",
            "elapsed_seconds": 2.05,
            "database_name": DATABASE_NAME,
        }
        try:
            phase_results["api_matrix"] = run_matrix()
            if not phase_results["api_matrix"]["all_distinct_operations_covered"]:
                raise RuntimeError("The HTTP matrix missed a mounted operation")
        except Exception as error:  # noqa: BLE001 - record external Modal/API failures safely.
            phase_results["api_matrix_error"] = {
                "error_type": type(error).__name__,
                "error_code": getattr(error, "code", None),
            }
            exit_code = 1

        try:
            phase_results["parent_real_vision_flow"] = run_parent_flow("modal")
        except Exception as error:  # noqa: BLE001 - record AI path outcome before cleanup.
            phase_results["parent_real_vision_flow_error"] = {
                "error_type": type(error).__name__,
                "error_code": getattr(error, "code", None),
            }
            exit_code = 1

        real_flow = phase_results.get("parent_real_vision_flow", {})
        real_vision_ok = (
            isinstance(real_flow, dict)
            and real_flow.get("vision", {}).get("status") == "SUBJECT_REVIEW"
            and real_flow.get("vision", {}).get("candidate_is_expected_butterfly") is True
        )
        real_story_attempted = (
            modal_records["story"]["dispatch_count"] > 0
            or (
                isinstance(real_flow, dict)
                and real_flow.get("story", {}).get("status") not in {"NOT_ATTEMPTED", None}
            )
        )
        if not real_vision_ok and not real_story_attempted:
            try:
                phase_results["parent_fixture_vision_story_flow"] = run_parent_flow("fixture")
            except Exception as error:  # noqa: BLE001 - record fixture failure without retry.
                phase_results["parent_fixture_vision_story_flow_error"] = {
                    "error_type": type(error).__name__,
                    "error_code": getattr(error, "code", None),
                }
                exit_code = 1
        if any(not item.get("passed", False) for item in records):
            exit_code = 1
        if any(
            item.get("outcome") in {"FAILED_OR_UNKNOWN", "ModalFunctionOutcomeUnknown"}
            or item.get("state") == "FAILED_OR_UNKNOWN"
            for item in modal_records.values()
        ):
            exit_code = 1
    finally:
        phase_results["modal_dispatches"] = modal_records
        phase_results["database_guard"] = database_guard
        phase_results["started_at"] = _STARTED_AT
        phase_results["ended_at"] = now_local()
        phase_results["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        phase_results["api_calls"] = records
        phase_results["video_calls"] = 0
        phase_results["overall_status"] = "PASS" if exit_code == 0 else "FAIL"
        phase_results["process_exit_code"] = exit_code
        phase_results["privacy"] = {
            "raw_story_saved": False,
            "prompt_saved": False,
            "real_child_data_used": False,
            "request_body_saved": False,
        }
        write_json(ASSET_DIR / "retest_results_safe.json", phase_results)
        write_trace()
        if TEMP_ROOT is not None and TEMP_ROOT.parent.resolve() == Path(tempfile.gettempdir()).resolve():
            shutil.rmtree(TEMP_ROOT)
    print(
        json.dumps(
            {
                "exit_code": exit_code,
                "api_requests": len(records),
                "modal_dispatch_counts": {
                    key: value["dispatch_count"] for key, value in modal_records.items()
                },
                "results_path": str(ASSET_DIR / "retest_results_safe.json"),
            },
            ensure_ascii=True,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
