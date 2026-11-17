from __future__ import annotations

import json
import os
import shutil
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
    / "parent_api_20261106"
)
IMAGE = (
    FEATURE
    / "evidence"
    / "assets"
    / "parent_generated_image_activity_retest_20261103"
    / "synthetic_childlike_butterfly.png"
)
DB_NAME = "storyrun_lite_feat063_rev52_20261106"
CONTAINER = "sketch2life-rev52-parent-api-pg-20261106"
DB_URL = os.environ.get("STORYRUN_LITE_DATABASE_URL", "")

for item in (str(REPO / "backend" / "src"), str(SCRIPT.parent)):
    if item not in sys.path:
        sys.path.insert(0, item)

import modal  # noqa: E402
import run_parent_story_api_retest_20261105 as api  # noqa: E402
import sketch2life.infrastructure.story_run_lite.photo_bridge as photo_bridge  # noqa: E402
from sketch2life.contracts.schemas.ai_story import (  # noqa: E402
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)
from sketch2life.infrastructure.ai.modal_function_client import (  # noqa: E402
    MODEL_ID,
    MODEL_REVISION,
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    ModalDrawingFunctionClient,
    summarize_worker_call_logs,
)
from sqlalchemy.engine import make_url  # noqa: E402

drawing_result: dict[str, Any] = {"outcome": "NOT_DISPATCHED"}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def summarize_call(call_id: Any) -> dict[str, Any] | None:
    if not isinstance(call_id, str) or not call_id.startswith("fc-"):
        return None
    try:
        return summarize_worker_call_logs(
            modal.FunctionCall.from_id(call_id), max_log_wait_seconds=20
        )
    except Exception as exc:  # noqa: BLE001 - only safe exception class is retained.
        return {
            "worker_logs_available": False,
            "worker_failure_boundary": "worker_log_fetch_exception",
            "error_type": type(exc).__name__,
        }


class CapturingDrawingClient(ModalDrawingFunctionClient):
    def invoke(self, prepared: Any) -> Any:
        global drawing_result
        started = time.perf_counter()
        try:
            result = super().invoke(prepared)
        except Exception as exc:
            call_id = getattr(exc, "call_id", None)
            drawing_result = {
                "workload": "drawing.analyze",
                "outcome": "FAILED_OR_UNKNOWN",
                "model_id": MODEL_ID,
                "model_revision": MODEL_REVISION,
                "call_id": call_id,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                "error_type": type(exc).__name__,
                "worker_log_summary": summarize_call(call_id),
            }
            write_json(OUTPUT / "parent_api_drawing_worker.json", drawing_result)
            raise
        drawing_result = {
            "workload": "drawing.analyze",
            "outcome": "SUCCEEDED",
            "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "call_id": result.call_id,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "output_sha256": result.output_sha256,
            "worker_log_summary": summarize_call(result.call_id),
        }
        api.modal_records["drawing"]["dispatch_count"] += 1
        api.modal_records["drawing"].update(
            {
                "outcome": "SUCCEEDED",
                "elapsed_ms": drawing_result["elapsed_ms"],
                "call_id": result.call_id,
            }
        )
        write_json(OUTPUT / "parent_api_drawing_worker.json", drawing_result)
        return result


def fixture_story() -> dict[str, object]:
    actions = [
        "Trung nho nam tren la.",
        "Trung no thanh sau buom.",
        "Sau buom an la va lon len.",
        "Sau buom hoa thanh nhong.",
        "Buom truong thanh bay toi bong hoa.",
    ]
    story: dict[str, object] = {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": "Hanh trinh cua buom",
        "story": {
            "opening": "Tren chiec la, trung buom nho nam yen.",
            "middle": (
                "Trung no thanh sau buom. Sau buom an la va lon len. "
                "Sau do, sau tao ken roi hoa nhong."
            ),
            "ending": "Tu nhong, buom truong thanh chui ra va bay toi bong hoa.",
        },
        "duration_ms": 30_000,
        "scenes": [
            {
                "scene_index": i,
                "title": f"Canh {i}",
                "action": actions[i - 1],
                "visual_prompt": "Minh hoa net ve don gian, giu dung hinh dang.",
                "narration": actions[i - 1],
                "start_ms": (i - 1) * 6_000,
                "duration_ms": 6_000,
                "character_anchors": ["than sau mong", "canh buom ro net"],
            }
            for i in range(1, 6)
        ],
    }
    parsed = StoryRevisionDraftV1.model_validate(story)
    validate_butterfly_lifecycle_v1(parsed, confirmed_subject="butterfly")
    return parsed.model_dump(mode="json")


class FixtureStoryClient:
    def __init__(self, *, timeout_seconds: float) -> None:
        if not 0 < timeout_seconds <= api.WAIT_CAP_SECONDS:
            raise ValueError("Fixture story timeout exceeds cap")

    def generate(self, _context: dict[str, object]) -> tuple[dict[str, object], str]:
        return fixture_story(), "synthetic-fixture-story-v1"


def safe_dispatch_intent(workload: str, _metadata: dict[str, Any]) -> None:
    safe = (
        {
            "api_route": "POST /v1/story-runs/{run_ref}/assets",
            "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "synthetic_artwork": True,
        }
        if workload == "drawing.analyze"
        else {
            "api_route": "POST /v1/story-runs/{run_ref}/story-revisions",
            "provider": "synthetic_fixture",
            "modal_dispatch": False,
        }
    )
    api.write_json(
        api.ASSET_DIR / f"{workload.replace('.', '_')}_dispatch_intent.json",
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "workload": workload,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "max_dispatches": 1,
            "video_enabled": False,
            **safe,
        },
    )


def configure() -> None:
    if not DB_URL:
        raise RuntimeError("STORYRUN_LITE_DATABASE_URL is required")
    url = make_url(DB_URL)
    if (
        url.get_backend_name() != "postgresql"
        or url.host != "127.0.0.1"
        or url.port != 5433
        or url.database != DB_NAME
        or url.username != "postgres"
        or url.password is not None
    ):
        raise RuntimeError("Refusing any database outside the disposable local target")
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("Evidence exists; refusing duplicate API calls")
    if not IMAGE.is_file():
        raise RuntimeError("Synthetic artwork fixture is missing")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    api.EVIDENCE_ROOT = OUTPUT
    api.ASSET_DIR = OUTPUT / "api_requests"
    api.DATABASE_NAME = DB_NAME
    api.DATABASE_URL = DB_URL
    api.WAIT_CAP_SECONDS = 300
    api.API_READ_TIMEOUT_SECONDS = 315
    api.records.clear()
    api.modal_records = {
        "drawing": {"dispatch_count": 0, "outcome": "NOT_DISPATCHED"},
        "story": {"dispatch_count": 0, "outcome": "NOT_DISPATCHED"},
    }
    api.database_guard = {
        "database_name": DB_NAME,
        "container": CONTAINER,
        "client_host": "127.0.0.1",
        "client_port": 5433,
        "task_owned_disposable_database": True,
        "credentials_embedded": False,
    }
    api.TEMP_ROOT = Path(tempfile.mkdtemp(prefix="sketch2life-rev52-parent-api-"))
    api._STARTED_AT = datetime.now().astimezone().isoformat(timespec="seconds")
    api.RecordingStoryClient = FixtureStoryClient
    api.record_dispatch_intent = safe_dispatch_intent
    photo_bridge.ModalDrawingFunctionClient = CapturingDrawingClient


def main() -> int:
    configure()
    started = time.perf_counter()
    write_json(
        OUTPUT / "dispatch_guard.json",
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "database_name": DB_NAME,
            "container": CONTAINER,
            "synthetic_only": True,
            "video_called": False,
            "modal_story_called": False,
            "modal_drawing_max_calls": 1,
        },
    )
    results: dict[str, Any] = {
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "synthetic_only": True,
        "video_called": False,
        "database": api.database_guard,
        "model_pins": {
            "drawing.analyze": {"model_id": MODEL_ID, "revision": MODEL_REVISION},
            "story.fixture": {
                "model_id": STORY_MODEL_ID,
                "revision": STORY_MODEL_REVISION,
                "inference_called": False,
            },
        },
    }
    exit_code = 0
    try:
        try:
            results["api_matrix"] = api.run_matrix()
        except Exception as exc:  # noqa: BLE001 - only the safe exception class is saved.
            results["api_matrix_error"] = {"error_type": type(exc).__name__}
            exit_code = 1

        api.modal_records = {
            "drawing": {"dispatch_count": 0, "outcome": "NOT_DISPATCHED"},
            "story": {"dispatch_count": 0, "outcome": "NOT_DISPATCHED"},
        }
        try:
            results["parent_modal_drawing_fixture_story_flow"] = api.run_parent_flow("modal")
        except Exception as exc:  # noqa: BLE001 - no payload or exception text is retained.
            results["parent_modal_drawing_fixture_story_flow_error"] = {
                "error_type": type(exc).__name__
            }
            exit_code = 1

        api.modal_records = {
            "drawing": {"dispatch_count": 0, "outcome": "NOT_DISPATCHED"},
            "story": {"dispatch_count": 0, "outcome": "NOT_DISPATCHED"},
        }
        try:
            results["parent_fixture_story_flow"] = api.run_parent_flow("fixture")
        except Exception as exc:  # noqa: BLE001 - no payload or exception text is retained.
            results["parent_fixture_story_flow_error"] = {"error_type": type(exc).__name__}
            exit_code = 1
    finally:
        api.write_trace()
        api_records = list(api.records)
        write_json(OUTPUT / "api_request_results.json", api_records)
        results["api_request_count"] = len(api_records)
        results["api_requests_all_expected"] = all(row.get("passed") is True for row in api_records)
        results["api_routes_exercised"] = sorted({str(row.get("route")) for row in api_records})
        results["modal_drawing"] = drawing_result
        results["modal_story_dispatches"] = 0
        results["video_calls"] = 0
        results["ended_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        results["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        matrix_ok = results.get("api_matrix", {}).get("all_distinct_operations_covered") is True
        modal_flow = results.get("parent_modal_drawing_fixture_story_flow", {})
        fixture_flow = results.get("parent_fixture_story_flow", {})
        results["status"] = (
            "PASS"
            if exit_code == 0
            and matrix_ok
            and results["api_requests_all_expected"]
            and drawing_result.get("outcome") == "SUCCEEDED"
            and modal_flow.get("vision", {}).get("candidate_is_expected_butterfly") is True
            and modal_flow.get("adult_story_confirmation") is True
            and fixture_flow.get("adult_story_confirmation") is True
            else "FAIL"
        )
        write_json(OUTPUT / "summary.json", results)
        guard = json.loads((OUTPUT / "dispatch_guard.json").read_text(encoding="utf-8"))
        guard.update(
            {
                "state": "COMPLETED" if results["status"] == "PASS" else "COMPLETED_WITH_FAILURES",
                "ended_at": results["ended_at"],
                "video_called": False,
            }
        )
        write_json(OUTPUT / "dispatch_guard.json", guard)
        temp_root = api.TEMP_ROOT
        if (
            temp_root is not None
            and temp_root.name.startswith("sketch2life-rev52-parent-api-")
            and temp_root.parent.resolve() == Path(tempfile.gettempdir()).resolve()
        ):
            shutil.rmtree(temp_root)

    print(
        json.dumps(
            {
                "status": results["status"],
                "api_request_count": results["api_request_count"],
                "modal_drawing_outcome": drawing_result.get("outcome"),
                "api_routes": results["api_routes_exercised"],
                "video_called": False,
            },
            ensure_ascii=True,
        ),
        flush=True,
    )
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
