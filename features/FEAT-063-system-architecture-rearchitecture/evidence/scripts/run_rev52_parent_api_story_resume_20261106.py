from __future__ import annotations

import hashlib
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
EVIDENCE = FEATURE / "evidence" / "nonvideo_modal_ai_reliability_20261106"
OUTPUT = EVIDENCE / "runtime" / "parent_api_story_resume_20261106"
STORY_RESULT = (
    EVIDENCE
    / "runtime"
    / "recovery_after_wait_fix_20261106"
    / "story_generate_result.json"
)
RUN_ID = "945a2673-33ef-4690-9055-5f4991a8aa8f"
ACTOR_SCOPE_REF = "synthetic-parent-local-v1"
DATABASE_NAME = "storyrun_lite_feat063_rev52_20261106"
CONTAINER = "sketch2life-rev52-parent-api-pg-20261106"
DATABASE_URL = os.environ.get("STORYRUN_LITE_DATABASE_URL", "")
MAX_STORY_WAIT_SECONDS = 90

for item in (
    str(REPO / "backend" / "src"),
    str(FEATURE / "evidence" / "scripts"),
    str(REPO / "deployment" / "modal" / "srs_v23"),
):
    if item not in sys.path:
        sys.path.insert(0, item)

import language_audio_app as modal_language_audio  # noqa: E402
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
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_previously_validated_modal_story() -> tuple[dict[str, object], str, bool]:
    if not STORY_RESULT.is_file():
        raise RuntimeError("Previously completed synthetic Modal story result is missing")
    raw = STORY_RESULT.read_bytes()
    artifact = json.loads(raw)
    if not isinstance(artifact, dict) or artifact.get("outcome") != "SUCCEEDED":
        raise RuntimeError("Previous story workload did not have a successful terminal result")
    result = artifact.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("Previous story workload result is not an object")
    content = {
        "title": result.get("title"),
        "story": result.get("story"),
        "scenes": [
            {
                key: scene[key]
                for key in (
                    "title",
                    "action",
                    "visual_prompt",
                    "narration",
                    "character_anchors",
                )
            }
            for scene in result.get("scenes", [])
            if isinstance(scene, dict)
        ],
    }
    parsed_content = modal_language_audio._parse_story_content_output(
        json.dumps(content, ensure_ascii=False)
    )
    assembled = modal_language_audio._assemble_parent_story_output(parsed_content)
    validated = modal_language_audio._parse_story_output(
        json.dumps(assembled, ensure_ascii=False),
        {"confirmed_subject": "bướm"},
    )
    parsed = StoryRevisionDraftV1.model_validate(validated)
    validate_butterfly_lifecycle_v1(parsed, confirmed_subject="bướm")
    normalized = parsed.model_dump(mode="json")
    normalized_fragments = normalized != result
    return normalized, hashlib.sha256(raw).hexdigest(), normalized_fragments


class ReusedModalOutputStoryFixture:
    def __init__(self, *, timeout_seconds: float, story: dict[str, object]) -> None:
        if not 0 < timeout_seconds <= api.WAIT_CAP_SECONDS:
            raise ValueError("Fixture story timeout exceeds approved cap")
        self._story = story

    def generate(self, context: dict[str, object]) -> tuple[dict[str, object], str]:
        if not api._is_butterfly(context.get("confirmed_subject")):
            raise RuntimeError("Synthetic fixture subject did not match the confirmed drawing")
        return self._story, "rev52-verified-modal-story-fixture"


def verify_database_target() -> dict[str, Any]:
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
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, hide_parameters=True)
    try:
        with engine.connect() as connection:
            identity = dict(
                connection.execute(
                    text(
                        "select current_database() as database_name, "
                        "current_user, pg_get_userbyid(datdba) as database_owner "
                        "from pg_database where datname = current_database()"
                    )
                ).mappings().one()
            )
            row = connection.execute(
                text(
                    "select r.run_id, r.run_state, r.job_state, r.understanding_revision, "
                    "r.subject_label, r.actor_scope_ref, r.child_age_months, "
                    "(select count(*) from story.story_revisions s where s.run_id = r.run_id) "
                    "as story_revision_count "
                    "from story.runs r where r.run_id = :run_id"
                ),
                {"run_id": RUN_ID},
            ).mappings().one_or_none()
            if row is None:
                raise RuntimeError("The existing synthetic Parent run is missing")
            run = dict(row)
        if (
            identity["database_name"] != DATABASE_NAME
            or identity["current_user"] != identity["database_owner"]
        ):
            raise RuntimeError("Connected database identity differs from the disposable target")
        if (
            run["run_state"] != "SUBJECT_REVIEW"
            or run["job_state"] != "SUCCEEDED"
            or run["understanding_revision"] != 1
            or not api._is_butterfly(run["subject_label"])
            or run["child_age_months"] != 60
            or run["actor_scope_ref"] != ACTOR_SCOPE_REF
            or run["story_revision_count"] != 0
        ):
            raise RuntimeError("Existing synthetic run is not in the safe expected pre-story state")
        return {
            "database_name": DATABASE_NAME,
            "database_owner_verified": True,
            "container": CONTAINER,
            "host": "127.0.0.1",
            "port": 5433,
            "run_id": RUN_ID,
            "run_state": run["run_state"],
            "vision_job_state": run["job_state"],
            "story_revision_count_before": run["story_revision_count"],
            "synthetic_only": True,
        }
    finally:
        engine.dispose()


def configure(story: dict[str, object]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if any(OUTPUT.iterdir()):
        raise RuntimeError("Resume evidence exists; refusing a duplicate Parent API run")
    api.EVIDENCE_ROOT = OUTPUT
    api.ASSET_DIR = OUTPUT / "api_requests"
    api.DATABASE_NAME = DATABASE_NAME
    api.DATABASE_URL = DATABASE_URL
    api.WAIT_CAP_SECONDS = MAX_STORY_WAIT_SECONDS
    api.API_READ_TIMEOUT_SECONDS = MAX_STORY_WAIT_SECONDS + 15
    api.records.clear()
    api.modal_records = {
        "drawing": {"dispatch_count": 0, "outcome": "REUSED_COMPLETED_RESULT"},
        "story": {"dispatch_count": 0, "outcome": "FIXTURE_FROM_COMPLETED_MODAL_OUTPUT"},
    }
    api.database_guard = {
        "database_name": DATABASE_NAME,
        "container": CONTAINER,
        "client_host": "127.0.0.1",
        "client_port": 5433,
        "task_owned_disposable_database": True,
        "credentials_embedded": False,
    }
    api.TEMP_ROOT = Path(tempfile.mkdtemp(prefix="sketch2life-rev52-parent-api-story-"))
    api._STARTED_AT = datetime.now().astimezone().isoformat(timespec="seconds")
    api.RecordingStoryClient = lambda *, timeout_seconds: ReusedModalOutputStoryFixture(
        timeout_seconds=timeout_seconds,
        story=story,
    )


def require_status(response: Any, expected: set[int], name: str) -> None:
    if response.status_code not in expected:
        raise RuntimeError(f"{name} returned unexpected HTTP {response.status_code}")


def main() -> int:
    story, source_sha256, normalized_fragments = load_previously_validated_modal_story()
    database = verify_database_target()
    configure(story)
    fixture_summary = {
        "source_artifact_sha256": source_sha256,
        "source_workload": "story.generate",
        "source_model_id": "Qwen/Qwen3.5-9B",
        "source_model_revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        "scene_count": len(story["scenes"]),
        "schema_valid_before_api": True,
        "butterfly_lifecycle_valid_before_api": True,
        "trailing_fragments_normalized": normalized_fragments,
        "modal_call_for_api_route": False,
    }
    write_json(
        OUTPUT / "dispatch_guard.json",
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "database": database,
            "story_fixture": fixture_summary,
            "video_called": False,
            "drawing_modal_calls": 0,
            "story_modal_calls": 0,
        },
    )
    started = time.perf_counter()
    server = None
    session = api.requests.Session()
    result: dict[str, Any] = {
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "database": database,
        "story_fixture": fixture_summary,
        "video_calls": 0,
        "modal_calls": {"drawing.analyze": 0, "story.generate": 0},
        "api_requests": [],
    }
    exit_code = 0
    try:
        port = api.free_port()
        base_url = f"http://127.0.0.1:{port}"
        story_client = ReusedModalOutputStoryFixture(
            timeout_seconds=MAX_STORY_WAIT_SECONDS,
            story=story,
        )
        server = api.start_api_server(
            port=port,
            actor_scope_ref=ACTOR_SCOPE_REF,
            vision_mode="fixture",
            story_generator=story_client,
        )
        api.database_guard["container"] = CONTAINER
        api.wait_for_api(base_url, server)

        initial, initial_body = api.api_call(
            session,
            name="read_existing_parent_run_before_story",
            method="GET",
            base_url=base_url,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{RUN_ID}",
            expected={200},
        )
        require_status(initial, {200}, "read existing Parent run")
        if initial_body.get("run_state") != "SUBJECT_REVIEW":
            raise RuntimeError("Existing Parent run left SUBJECT_REVIEW before continuation")

        subject, subject_body = api.api_call(
            session,
            name="confirm_ai_recognized_synthetic_subject",
            method="POST",
            base_url=base_url,
            route="POST /v1/story-runs/{run_ref}/subject-confirmation",
            path=f"/v1/story-runs/{RUN_ID}/subject-confirmation",
            expected={202},
            headers={
                "Idempotency-Key": f"rev52-resume:{RUN_ID}:confirm-subject",
                "If-Match": initial.headers.get("ETag", ""),
            },
            json={
                "decision": "CONFIRM",
                "expected_understanding_revision": 1,
            },
        )
        require_status(subject, {202}, "confirm synthetic drawing subject")

        ready, ready_body = api.api_call(
            session,
            name="read_parent_run_before_story_generation",
            method="GET",
            base_url=base_url,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{RUN_ID}",
            expected={200},
        )
        require_status(ready, {200}, "read Parent run before story")
        if ready_body.get("run_state") not in {"PREPARATION_REVIEW", "SCRIPT_REVIEW"}:
            raise RuntimeError("Subject confirmation did not reach the expected pre-story state")

        story_response, story_body = api.api_call(
            session,
            name="create_parent_story_revision_from_verified_modal_output_fixture",
            method="POST",
            base_url=base_url,
            route="POST /v1/story-runs/{run_ref}/story-revisions",
            path=f"/v1/story-runs/{RUN_ID}/story-revisions",
            expected={202},
            headers={
                "Idempotency-Key": f"rev52-resume:{RUN_ID}:initial-story",
                "If-Match": ready.headers.get("ETag", ""),
            },
            json={
                "expected_understanding_revision": 1,
                "adult_confirmed_idea": (
                    "Kể vòng đời thật của bướm từ trứng, sâu bướm, nhộng đến bướm trưởng thành; "
                    "không gán việc nở trứng cho bướm trưởng thành."
                ),
            },
            timeout=(15, MAX_STORY_WAIT_SECONDS + 15),
        )
        require_status(story_response, {202}, "create story revision")
        revision_ref = story_body.get("story_revision_ref")
        if not isinstance(revision_ref, str) or not revision_ref:
            raise RuntimeError("Story generation response omitted story_revision_ref")

        deadline = time.perf_counter() + MAX_STORY_WAIT_SECONDS
        revision_response = None
        revision_body: dict[str, Any] = {}
        while time.perf_counter() < deadline:
            revision_response, revision_body = api.api_call(
                session,
                name="poll_parent_story_revision_until_terminal",
                method="GET",
                base_url=base_url,
                route="GET /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}",
                path=f"/v1/story-runs/{RUN_ID}/story-revisions/{revision_ref}",
                expected={200},
                timeout=10,
            )
            require_status(revision_response, {200}, "read story revision")
            revision_status = revision_body.get("status")
            if revision_status in {"DRAFT", "FAILED", "AWAITING_RECONCILIATION"}:
                break
            time.sleep(0.5)
        else:
            raise TimeoutError(
                "Parent story revision did not reach a terminal state within 90 seconds"
            )

        if revision_body.get("status") != "DRAFT":
            result["story_failure"] = {
                "status": revision_body.get("status"),
                "error_code": revision_body.get("code"),
            }
            raise RuntimeError("Parent story revision did not reach reviewable DRAFT")
        parsed = StoryRevisionDraftV1.model_validate(
            {
                "schema_version": revision_body.get("schema_version"),
                "language": revision_body.get("language"),
                "title": revision_body.get("title"),
                "story": revision_body.get("story"),
                "duration_ms": revision_body.get("duration_ms"),
                "scenes": revision_body.get("scenes"),
            }
        )
        validate_butterfly_lifecycle_v1(parsed, confirmed_subject="butterfly")
        result["story_api"] = {
            "create_status": story_response.status_code,
            "revision_ref": revision_ref,
            "revision_status": revision_body.get("status"),
            "schema_valid": True,
            "butterfly_lifecycle_valid": True,
            "review_required": revision_body.get("review_required"),
            "story_sha256": revision_body.get("story_sha256"),
            "scene_count": len(parsed.scenes),
            "fixture_dispatches": 1,
            "modal_dispatches": 0,
        }

        current_run, _current_run_body = api.api_call(
            session,
            name="read_parent_run_after_story_generation_before_confirmation",
            method="GET",
            base_url=base_url,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{RUN_ID}",
            expected={200},
        )
        require_status(current_run, {200}, "read Parent run before story confirmation")

        confirmed, confirmation_body = api.api_call(
            session,
            name="adult_confirms_parent_story_revision",
            method="POST",
            base_url=base_url,
            route="POST /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation",
            path=f"/v1/story-runs/{RUN_ID}/story-revisions/{revision_ref}/confirmation",
            expected={200},
            headers={
                "Idempotency-Key": f"rev52-resume:{RUN_ID}:confirm-story",
                "If-Match": current_run.headers.get("ETag", ""),
            },
            json={
                "expected_revision": revision_body["revision_no"],
                "story_sha256": revision_body["story_sha256"],
            },
        )
        require_status(confirmed, {200}, "confirm Parent story revision")
        final, final_body = api.api_call(
            session,
            name="read_parent_run_after_story_confirmation",
            method="GET",
            base_url=base_url,
            route="GET /v1/story-runs/{run_ref}",
            path=f"/v1/story-runs/{RUN_ID}",
            expected={200},
        )
        require_status(final, {200}, "read Parent run after story confirmation")
        result["final_run_state"] = final_body.get("run_state")
        result["story_confirmation_status"] = confirmed.status_code
        result["status"] = "PASS"
    except Exception as exc:  # noqa: BLE001 - retain safe error class only.
        result["status"] = "FAIL"
        result["error_type"] = type(exc).__name__
        result["error_code"] = getattr(exc, "code", None)
        exit_code = 1
    finally:
        if server is not None:
            try:
                api.stop_api_server(server)
                result["api_server_stopped"] = True
            except Exception as exc:  # noqa: BLE001 - retain safe error class only.
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
        result["video_calls"] = 0
        api.write_trace()
        write_json(OUTPUT / "summary.json", result)
        guard = {
            "state": "COMPLETED" if result.get("status") == "PASS" else "COMPLETED_WITH_FAILURES",
            "ended_at": result["ended_at"],
            "video_called": False,
            "drawing_modal_calls": 0,
            "story_modal_calls": 0,
            "api_server_stopped": result.get("api_server_stopped", server is None),
        }
        write_json(OUTPUT / "dispatch_guard.json", guard)
        if api.TEMP_ROOT is not None:
            import shutil

            shutil.rmtree(api.TEMP_ROOT, ignore_errors=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
