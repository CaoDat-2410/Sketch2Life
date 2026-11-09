from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
OUTPUT = (
    FEATURE
    / "evidence"
    / "nonvideo_modal_ai_reliability_20261106"
    / "runtime"
    / "parent_api_confirmation_resume_20261106"
)
PRIOR_API_SUMMARY = (
    FEATURE
    / "evidence"
    / "nonvideo_modal_ai_reliability_20261106"
    / "runtime"
    / "parent_api_story_resume_20261106"
    / "summary.json"
)
RUN_ID = "945a2673-33ef-4690-9055-5f4991a8aa8f"
ACTOR_SCOPE_REF = "synthetic-parent-local-v1"
DATABASE_NAME = "storyrun_lite_feat063_rev52_20261106"
CONTAINER = "sketch2life-rev52-parent-api-pg-20261106"
DATABASE_URL = os.environ.get("STORYRUN_LITE_DATABASE_URL", "")

for item in (
    str(REPO / "backend" / "src"),
    str(FEATURE / "evidence" / "scripts"),
):
    if item not in sys.path:
        sys.path.insert(0, item)

import run_parent_story_api_retest_20261105 as api  # noqa: E402
from sketch2life.contracts.schemas.ai_story import (  # noqa: E402
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class NoDispatchStoryClient:
    def generate(self, _context: dict[str, object]) -> tuple[dict[str, object], str]:
        raise RuntimeError("Unexpected story model dispatch in confirmation-only resume")


def verify_target() -> tuple[dict[str, Any], str]:
    if not DATABASE_URL:
        raise RuntimeError("STORYRUN_LITE_DATABASE_URL is required")
    url = make_url(DATABASE_URL)
    if (
        url.get_backend_name() != "postgresql"
        or url.host != "127.0.0.1"
        or url.port != 5433
        or url.database != DATABASE_NAME
        or url.username != "postgres"
        or url.password is not None
    ):
        raise RuntimeError("Refusing any database outside the task-owned disposable target")
    if not PRIOR_API_SUMMARY.is_file():
        raise RuntimeError("Prior Parent API story evidence is missing")
    prior = json.loads(PRIOR_API_SUMMARY.read_text(encoding="utf-8"))
    story_api = prior.get("story_api")
    revision_ref = story_api.get("revision_ref") if isinstance(story_api, dict) else None
    if not isinstance(revision_ref, str) or not revision_ref:
        raise RuntimeError("Prior story revision reference is missing")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, hide_parameters=True)
    try:
        with engine.connect() as connection:
            identity = dict(
                connection.execute(
                    text(
                        "select current_database() as database_name, current_user, "
                        "pg_get_userbyid(datdba) as database_owner "
                        "from pg_database where datname = current_database()"
                    )
                ).mappings().one()
            )
            run = connection.execute(
                text(
                    "select run_id, actor_scope_ref, run_state, job_state, version "
                    "from story.runs where run_id = :run_id"
                ),
                {"run_id": RUN_ID},
            ).mappings().one_or_none()
            revision = connection.execute(
                text(
                    "select story_revision_id, revision_no, status, story_sha256 "
                    "from story.story_revisions where run_id = :run_id"
                ),
                {"run_id": RUN_ID},
            ).mappings().one_or_none()
        if (
            identity["database_name"] != DATABASE_NAME
            or identity["current_user"] != identity["database_owner"]
            or run is None
            or run["actor_scope_ref"] != ACTOR_SCOPE_REF
            or run["run_state"] != "SCRIPT_REVIEW"
            or run["job_state"] != "SUCCEEDED"
            or revision is None
            or revision["story_revision_id"] != revision_ref
            or revision["revision_no"] != 1
            or revision["status"] != "DRAFT"
            or not revision["story_sha256"]
        ):
            raise RuntimeError("Existing synthetic run is not in the expected reviewable state")
        return (
            {
                "database_name": DATABASE_NAME,
                "database_owner_verified": True,
                "container": CONTAINER,
                "run_id": RUN_ID,
                "run_state_before": run["run_state"],
                "revision_status_before": revision["status"],
                "video_called": False,
                "modal_calls": 0,
            },
            revision_ref,
        )
    finally:
        engine.dispose()


def main() -> int:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise SystemExit("Confirmation-resume evidence exists; refusing another command")
    database, revision_ref = verify_target()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    api.EVIDENCE_ROOT = OUTPUT
    api.ASSET_DIR = OUTPUT / "api_requests"
    api.DATABASE_NAME = DATABASE_NAME
    api.DATABASE_URL = DATABASE_URL
    api.WAIT_CAP_SECONDS = 90
    api.API_READ_TIMEOUT_SECONDS = 105
    api.records.clear()
    api.modal_records = {"drawing": {"dispatch_count": 0}, "story": {"dispatch_count": 0}}
    api.database_guard = {
        "database_name": DATABASE_NAME,
        "container": CONTAINER,
        "client_host": "127.0.0.1",
        "client_port": 5433,
        "task_owned_disposable_database": True,
        "credentials_embedded": False,
    }
    api.TEMP_ROOT = Path(tempfile.mkdtemp(prefix="sketch2life-rev52-confirm-resume-"))
    api._STARTED_AT = datetime.now().astimezone().isoformat(timespec="seconds")
    started = time.perf_counter()
    result: dict[str, Any] = {
        "started_at": api._STARTED_AT,
        "database": database,
        "revision_ref": revision_ref,
        "video_calls": 0,
        "modal_calls": 0,
    }
    session = api.requests.Session()
    harness = None
    exit_code = 0
    try:
        port = api.free_port()
        base_url = f"http://127.0.0.1:{port}"
        harness = api.start_api_server(
            port=port,
            actor_scope_ref=ACTOR_SCOPE_REF,
            vision_mode="fixture",
            story_generator=NoDispatchStoryClient(),
        )
        api.database_guard["container"] = CONTAINER
        api.wait_for_api(base_url, harness)

        run_response, run_body = api.api_call(
            session,
            name="read_current_parent_run_etag_for_story_confirmation",
            method="GET",
            base_url=base_url,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{RUN_ID}",
            expected={200},
        )
        if run_response.status_code != 200 or run_body.get("run_state") != "SCRIPT_REVIEW":
            raise RuntimeError("Parent run was not at the adult script-review gate")

        revision_response, revision_body = api.api_call(
            session,
            name="read_reviewable_parent_story_revision",
            method="GET",
            base_url=base_url,
            route="GET /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}",
            path=f"/v1/story-runs/{RUN_ID}/story-revisions/{revision_ref}",
            expected={200},
        )
        if revision_response.status_code != 200 or revision_body.get("status") != "DRAFT":
            raise RuntimeError("Story revision is not available for adult review")
        draft = StoryRevisionDraftV1.model_validate(
            {
                "schema_version": revision_body.get("schema_version"),
                "language": revision_body.get("language"),
                "title": revision_body.get("title"),
                "story": revision_body.get("story"),
                "duration_ms": revision_body.get("duration_ms"),
                "scenes": revision_body.get("scenes"),
            }
        )
        validate_butterfly_lifecycle_v1(draft, confirmed_subject="bướm")
        if not run_response.headers.get("ETag"):
            raise RuntimeError("GET StoryRun omitted the required current ETag")

        confirm_response, _confirm_body = api.api_call(
            session,
            name="adult_confirms_reviewable_parent_story_revision",
            method="POST",
            base_url=base_url,
            route="POST /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation",
            path=f"/v1/story-runs/{RUN_ID}/story-revisions/{revision_ref}/confirmation",
            expected={200},
            headers={
                "Idempotency-Key": f"rev52-confirm-resume:{RUN_ID}:confirm-story",
                "If-Match": run_response.headers["ETag"],
            },
            json={
                "expected_revision": revision_body["revision_no"],
                "story_sha256": revision_body["story_sha256"],
            },
        )
        if confirm_response.status_code != 200:
            raise RuntimeError("Adult story confirmation did not succeed")

        final, final_body = api.api_call(
            session,
            name="read_parent_run_after_story_confirmation",
            method="GET",
            base_url=base_url,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{RUN_ID}",
            expected={200},
        )
        if final.status_code != 200 or final_body.get("run_state") != "VIDEO_ADMISSION_PENDING":
            raise RuntimeError("Confirmed story did not reach pre-video admission state")
        result["final_run_state"] = final_body.get("run_state")
        result["video_generation_started"] = False
        result["story_revision_schema_valid"] = True
        result["story_revision_lifecycle_valid"] = True
        result["story_confirmation_status"] = confirm_response.status_code
        result["status"] = "PASS"
    except Exception as exc:  # noqa: BLE001 - only safe exception class is retained.
        result["status"] = "FAIL"
        result["error_type"] = type(exc).__name__
        result["error_code"] = getattr(exc, "code", None)
        exit_code = 1
    finally:
        if harness is not None:
            try:
                api.stop_api_server(harness)
                result["api_server_stopped"] = True
            except Exception as exc:  # noqa: BLE001 - only the exception class is retained.
                result["api_server_stopped"] = False
                result["shutdown_error_type"] = type(exc).__name__
                result["status"] = "FAIL"
                exit_code = 1
        session.close()
        result["api_request_count"] = len(api.records)
        result["api_requests_all_expected"] = all(
            row.get("passed") is True for row in api.records
        )
        result["api_routes_exercised"] = sorted(
            {str(row.get("route")) for row in api.records}
        )
        result["api_request_results"] = list(api.records)
        result["ended_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        api.write_trace()
        write_json(OUTPUT / "summary.json", result)
        if api.TEMP_ROOT is not None:
            import shutil

            shutil.rmtree(api.TEMP_ROOT, ignore_errors=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
