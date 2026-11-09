from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
BACKEND_SRC = REPO / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import modal
from sketch2life.contracts.schemas.ai_story import (
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)

ASSET_DIR = FEATURE / "evidence" / "assets" / "modal_story_parser_alignment_20261105"
APP_NAME = "sketch2life-srs23-language-audio-dev"
FUNCTION_NAME = "generate-story-and-storyboard"
SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
MODAL_ENV = "dev"
WAIT_SECONDS = 300
STORY_INPUT_SCHEMA = "sketch2life.modal.ai-request.v1"
WORKER_INPUT_SCHEMA = "sketch2life.modal.worker-input.v1"
WORKER_OUTPUT_SCHEMA = "sketch2life.modal.worker-output.v1"
STORY_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
STORY_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
INTENT_PATH = ASSET_DIR / "story_dispatch_intent.json"
RESULT_PATH = ASSET_DIR / "story_result.json"
LOG_PATH = ASSET_DIR / "modal_function_logs.txt"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_json(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def cancel_call(call: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"requested": False, "state_check": "not_checked"}
    try:
        call.cancel(terminate_containers=True)
        result["requested"] = True
        result["requested_at"] = now()
    except Exception as exc:  # noqa: BLE001 - retain type only; never retry an ambiguous call.
        result["error_type"] = type(exc).__name__
    try:
        call.get(timeout=1)
        result["state_check"] = "result_arrived_during_cancel"
    except TimeoutError:
        result["state_check"] = "still_pending_after_cancel"
    except Exception as exc:  # noqa: BLE001 - only the exception type is evidence.
        result["state_check"] = f"terminal_{type(exc).__name__}"
    return result


def collect_call_logs(call_id: str) -> dict[str, Any]:
    command = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "modal",
        "app",
        "logs",
        APP_NAME,
        "--env",
        MODAL_ENV,
        "--function-call",
        call_id,
        "--tail",
        "1000",
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - persist only a bounded collection failure type.
        return {"state": "failed", "error_type": type(exc).__name__}
    LOG_PATH.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    return {"state": "saved", "exit_code": completed.returncode}


def main() -> int:
    if INTENT_PATH.exists() or RESULT_PATH.exists():
        raise SystemExit("Dispatch evidence already exists; refusing to send another story call.")

    image_path = (
        FEATURE
        / "evidence"
        / "assets"
        / "parent_generated_image_activity_retest_20261103"
        / "synthetic_childlike_butterfly.png"
    )
    if not image_path.is_file():
        raise SystemExit(f"Synthetic drawing fixture missing: {image_path}")

    drawing_sha = sha256(image_path.read_bytes())
    request_data = {
        "schema_version": "sketch2life.story-generation-input.v1",
        "role": "PARENT",
        "language": "vi",
        "confirmed_subject": "butterfly",
        "understanding_revision": 1,
        "drawing_sha256": drawing_sha,
        "visible_features": ["thân nhỏ ở giữa", "hai cặp cánh ở hai bên", "hai râu cong trên đầu"],
        "child_age_months": 60,
        "context_revision": 1,
        "adult_confirmed_idea": (
            "Kể vòng đời thật theo đúng thứ tự trứng, sâu bướm, nhộng, bướm trưởng thành; "
            "trứng nở thành sâu bướm, sâu bướm ăn lá rồi hóa nhộng, bướm trưởng thành chui ra khỏi nhộng."
        ),
        "rewrite_instruction": None,
        "lesson_direction": None,
    }
    identity = {
        "job_id": str(uuid.uuid4()),
        "generation_id": str(uuid.uuid4()),
        "attempt_id": str(uuid.uuid4()),
    }
    attempt_prefix = (
        f"sketch2life/{MODAL_ENV}/{identity['job_id']}/"
        f"{identity['generation_id']}/{identity['attempt_id']}/"
    )
    identity["prefix"] = attempt_prefix
    request_bytes = canonical_json(request_data)
    manifest_data = {
        "schema_version": STORY_INPUT_SCHEMA,
        "asset": {
            "path": "input/request.json",
            "content_type": "application/json",
            "size_bytes": len(request_bytes),
            "sha256": sha256(request_bytes),
        },
    }
    manifest_bytes = canonical_json(manifest_data)
    payload = {
        "schema_version": WORKER_INPUT_SCHEMA,
        "environment": MODAL_ENV,
        "workload": "story.generate",
        **{key: identity[key] for key in ("job_id", "generation_id", "attempt_id")},
        "attempt_prefix": attempt_prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": sha256(manifest_bytes),
        "input_bytes": len(manifest_bytes) + len(request_bytes),
    }
    intent = {
        "state": "DISPATCH_INTENT_RECORDED",
        "workload": "story.generate",
        "app": APP_NAME,
        "function": FUNCTION_NAME,
        **identity,
        "input_sha256": sha256(request_bytes),
        "manifest_sha256": sha256(manifest_bytes),
        "synthetic_parent_fixture": True,
        "source_drawing_sha256": drawing_sha,
        "wait_limit_seconds": WAIT_SECONDS,
        "created_at": now(),
        "max_calls": 1,
        "video_calls": 0,
    }
    save_json(INTENT_PATH, intent)
    record: dict[str, Any] = {**intent, "outcome": "DISPATCH_FAILED_NO_CALL"}
    call: Any | None = None
    volume: Any | None = None
    try:
        volume = modal.Volume.from_name(SCRATCH_VOLUME, environment_name=MODAL_ENV, version=2)
        with volume.batch_upload() as batch:
            batch.put_file(BytesIO(request_bytes), f"/{attempt_prefix}input/request.json")
            batch.put_file(BytesIO(manifest_bytes), f"/{attempt_prefix}input/manifest.json")

        remote = modal.Function.from_name(APP_NAME, FUNCTION_NAME, environment_name=MODAL_ENV)
        call = remote.spawn(payload)
        call_id = getattr(call, "object_id", None)
        record.update(
            {
                "call_id": call_id,
                "dispatched_at": now(),
                "state": "CALL_PENDING",
                "outcome": "PENDING",
            }
        )
        save_json(RESULT_PATH, record)
        print(
            json.dumps(
                {"event": "story_call_dispatched", "call_id": call_id, "wait_limit_seconds": WAIT_SECONDS}
            ),
            flush=True,
        )
        if not isinstance(call_id, str) or not call_id.startswith("fc-"):
            record.update({"state": "UNKNOWN_NO_CALL_ID", "outcome": "UNKNOWN_NO_CALL_ID_NO_RETRY"})
            return 2

        try:
            output = call.get(timeout=WAIT_SECONDS)
        except TimeoutError:
            record.update(
                {
                    "state": "CANCELLED_OR_UNKNOWN",
                    "outcome": "QUEUE_OR_WORKER_TIMEOUT_NO_RETRY",
                    "cancel": cancel_call(call),
                }
            )
            return 2

        record["state"] = "REMOTE_RESULT_RETURNED"
        record["completed_at"] = now()
        expected_envelope = {
            "schema_version": WORKER_OUTPUT_SCHEMA,
            "workload": "story.generate",
            "job_id": identity["job_id"],
            "generation_id": identity["generation_id"],
            "attempt_id": identity["attempt_id"],
            "model": {"id": STORY_MODEL_ID, "revision": STORY_MODEL_REVISION},
        }
        if not isinstance(output, dict) or any(
            output.get(key) != value for key, value in expected_envelope.items()
        ):
            raise ValueError("worker output envelope or model revision mismatch")
        draft = StoryRevisionDraftV1.model_validate(output.get("result"))
        validate_butterfly_lifecycle_v1(draft, confirmed_subject="butterfly")
        record.update(
            {
                "state": "CALL_TERMINAL_SUCCESS",
                "outcome": "SUCCEEDED",
                "scene_count": len(draft.scenes),
                "duration_ms": draft.duration_ms,
                "story_output_sha256": sha256(canonical_json(draft.model_dump(mode="json"))),
                "schema_validation": "passed",
                "butterfly_lifecycle_validation": "passed",
                "model": expected_envelope["model"],
            }
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - no prompt or result text is retained.
        error_message = str(exc)
        record.update(
            {
                "state": "CALL_TERMINAL_FAILURE" if call is not None else "DISPATCH_FAILED",
                "outcome": (
                    "MODEL_OUTPUT_INVALID"
                    if error_message == "MODAL_MODEL_OUTPUT_INVALID"
                    else "FAILED_TERMINAL" if call is not None else "DISPATCH_FAILED_NO_CALL"
                ),
            }
        )
        if error_message == "MODAL_MODEL_OUTPUT_INVALID":
            record["error_code"] = error_message
        else:
            record["error_type"] = type(exc).__name__
        return 2
    finally:
        record.setdefault("ended_at", now())
        if call is not None:
            call_id = getattr(call, "object_id", None)
            record["call_id"] = call_id
            if isinstance(call_id, str) and call_id.startswith("fc-"):
                record["worker_logs"] = collect_call_logs(call_id)
        if volume is not None and record.get("outcome") in {
            "SUCCEEDED",
            "FAILED_TERMINAL",
            "MODEL_OUTPUT_INVALID",
        }:
            try:
                volume.remove_file(f"{attempt_prefix}input", recursive=True)
                record["scratch_cleanup"] = "removed"
            except Exception as exc:  # noqa: BLE001 - record cleanup failure for manual follow-up.
                record["scratch_cleanup"] = f"failed_{type(exc).__name__}"
        save_json(RESULT_PATH, record)
        print(
            json.dumps(
                {
                    "event": "story_call_finished",
                    "outcome": record.get("outcome"),
                    "call_id": record.get("call_id"),
                    "scene_count": record.get("scene_count"),
                },
                sort_keys=True,
            ),
            flush=True,
        )


if __name__ == "__main__":
    raise SystemExit(main())
