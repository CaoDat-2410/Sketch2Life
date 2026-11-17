from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import modal

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[4]
FEATURE = REPO / "features" / "FEAT-063-system-architecture-rearchitecture"
OUTPUT_DIR = FEATURE / "evidence" / "assets" / "flux_component_retest_rev46a_20261105"
APP_NAME = "sketch2life-srs23-flux-image-dev"
ENVIRONMENT = "dev"
SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
MODEL_VOLUME = "sketch2life-dev-model-weights-v2"
MODEL_REVISION = "09561231f44e41381c461caf53d5452005a60ac9"
PUP_REVISION = "a57899549f8f6f64c6c4d88db30827d496ff76d0"
WORKER_INPUT_SCHEMA = "sketch2life.modal.worker-input.v1"
WORKER_OUTPUT_SCHEMA = "sketch2life.modal.worker-output.v1"
WAIT_SECONDS = 900


def now() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="milliseconds")


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _safe_error_category(exc: BaseException) -> str:
    message = str(exc).lower()
    reason_code = re.search(r"\bMODAL_[A-Z0-9_]+\b", str(exc))
    if reason_code:
        return reason_code.group(0)
    if "401" in message or "unauthorized" in message:
        return "HTTP_401"
    if "403" in message or "forbidden" in message:
        return "HTTP_403"
    if "404" in message or "not found" in message:
        return "NOT_FOUND"
    if "timeout" in message or isinstance(exc, TimeoutError):
        return "TIMEOUT"
    return type(exc).__name__


def _save_report(report: dict[str, Any]) -> None:
    report["updated_at"] = now()
    write_json(OUTPUT_DIR / "run_report.json", report)


def download_once(report: dict[str, Any]) -> bool:
    record: dict[str, Any] = {
        "workload": "model.checkpoint.download",
        "app": APP_NAME,
        "function": "download-flux-pinned-model",
        "started_at": now(),
        "max_attempts": 1,
        "secret_resource_name": "huggingface-secret",
        "secret_value_read_by_runner": False,
        "outcome": "DISPATCH_NOT_STARTED",
    }
    write_json(OUTPUT_DIR / "download_dispatch_intent.json", record)
    started = time.perf_counter()
    call = None
    try:
        function = modal.Function.from_name(
            APP_NAME, "download-flux-pinned-model", environment_name=ENVIRONMENT
        )
        call = function.spawn()
        record["call_id"] = getattr(call, "object_id", None)
        if not isinstance(record["call_id"], str) or not record["call_id"].startswith(
            "fc-"
        ):
            record["outcome"] = "UNKNOWN_NO_CALL_ID"
            record["error_category"] = "CALL_ID_MISSING"
            return False
        record["dispatched_at"] = now()
        result = call.get(timeout=1800)
        if not isinstance(result, dict):
            raise TypeError("download result is not an object")
        valid = (
            result.get("status") in {"downloaded", "already_present"}
            and result.get("revision") == MODEL_REVISION
            and result.get("prompt_upsampler_revision") == PUP_REVISION
        )
        record["outcome"] = "SUCCEEDED" if valid else "CONTRACT_FAILED"
        record["result"] = {
            "status": result.get("status"),
            "model_id": result.get("model_id"),
            "revision": result.get("revision"),
            "prompt_upsampler_id": result.get("prompt_upsampler_id"),
            "prompt_upsampler_revision": result.get("prompt_upsampler_revision"),
        }
        record["model_volume_retained"] = True
        record["completed_at"] = now()
        record["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
        report["download"] = record
        _save_report(report)
        return valid
    except TimeoutError as exc:
        record["outcome"] = "UNKNOWN_NO_RETRY"
        record["error_category"] = _safe_error_category(exc)
        record["call_cancel_requested"] = call is not None
        if call is not None:
            try:
                call.cancel(terminate_containers=True)
            except Exception:  # noqa: BLE001 - keep provider details out of local evidence
                record["call_cancel_requested"] = False
    except Exception as exc:  # noqa: BLE001 - store safe category only, not raw remote text
        record["outcome"] = (
            "FAILED_TERMINAL" if call is not None else "FAILED_NO_DISPATCH"
        )
        record["error_type"] = type(exc).__name__
        record["error_category"] = _safe_error_category(exc)
    record["completed_at"] = now()
    record["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    report["download"] = record
    _save_report(report)
    return False


def _lesson_visual_input() -> dict[str, Any]:
    reviewed_revision = {
        "schema_version": "sketch2life.lesson-visual-input.v1",
        "plan_revision_ref": "rev46a-synthetic-reviewed-lesson-v1",
        "topic": "butterfly",
        "steps": [
            {
                "step_index": 1,
                "instruction": "draw a small head and a simple body",
                "placement": "centered with wide margins",
            },
            {
                "step_index": 2,
                "instruction": "add two large upper wings and two smaller lower wings",
                "placement": "symmetrical around the body",
            },
            {
                "step_index": 3,
                "instruction": "add two simple antennae and a few wing patterns",
                "placement": "keep the patterns sparse and inside the wings",
            },
        ],
    }
    return {
        **reviewed_revision,
        "content_hash": sha256(canonical(reviewed_revision)),
    }


def _worker_request(
    workload: str, request_data: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
    prefix = f"sketch2life/{ENVIRONMENT}/{job_id}/{generation_id}/{attempt_id}/"
    request_bytes = canonical(request_data)
    manifest = {
        "schema_version": "sketch2life.modal.ai-request.v1",
        "asset": {
            "path": "input/request.json",
            "content_type": "application/json",
            "size_bytes": len(request_bytes),
            "sha256": sha256(request_bytes),
        },
    }
    manifest_bytes = canonical(manifest)
    payload = {
        "schema_version": WORKER_INPUT_SCHEMA,
        "environment": ENVIRONMENT,
        "workload": workload,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": sha256(manifest_bytes),
        "input_bytes": len(manifest_bytes) + len(request_bytes),
    }
    identity = {
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": prefix,
        "input_sha256": sha256(request_bytes),
        "manifest_sha256": sha256(manifest_bytes),
    }
    return identity, payload, request_bytes, manifest_bytes


def _validate_image_result(
    *,
    workload: str,
    result: Any,
    expected_size: tuple[int, int],
    identity: dict[str, Any],
    request_data: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    if not isinstance(result, dict):
        raise TypeError("worker result is not an object")
    for key, expected in {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": workload,
        "job_id": identity["job_id"],
        "generation_id": identity["generation_id"],
        "attempt_id": identity["attempt_id"],
        "status": "DRAFT",
        "review_required": True,
    }.items():
        if result.get(key) != expected:
            raise ValueError(f"worker output contract mismatch: {key}")
    if workload == "lesson.visual.generate":
        if result.get("plan_revision_ref") != request_data["plan_revision_ref"]:
            raise ValueError("lesson revision lineage mismatch")
        if result.get("content_hash") != request_data["content_hash"]:
            raise ValueError("lesson content hash mismatch")
    asset = result.get("asset")
    if not isinstance(asset, dict):
        raise TypeError("worker image metadata missing")
    image_bytes = asset.get("bytes")
    if not isinstance(image_bytes, bytes):
        raise TypeError("worker image bytes missing")
    if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("output is not a PNG")
    width, height = expected_size
    if (
        len(image_bytes) < 24
        or (
            int.from_bytes(image_bytes[16:20], "big"),
            int.from_bytes(image_bytes[20:24], "big"),
        )
        != expected_size
    ):
        raise ValueError("PNG dimensions invalid")
    if (asset.get("width"), asset.get("height")) != (width, height):
        raise ValueError("image dimensions do not match worker metadata")
    if asset.get("content_type") != "image/png":
        raise ValueError("image content type invalid")
    if asset.get("size_bytes") != len(image_bytes) or asset.get("sha256") != sha256(
        image_bytes
    ):
        raise ValueError("image size/hash verification failed")
    safe = {key: value for key, value in result.items() if key != "asset"}
    safe["asset"] = {
        "content_type": asset["content_type"],
        "size_bytes": asset["size_bytes"],
        "sha256": asset["sha256"],
        "width": asset["width"],
        "height": asset["height"],
    }
    return safe, image_bytes


def run_image_workload(
    *,
    workload: str,
    function_name: str,
    request_data: dict[str, Any],
    output_filename: str,
    expected_size: tuple[int, int],
) -> dict[str, Any]:
    identity, payload, request_bytes, manifest_bytes = _worker_request(
        workload, request_data
    )
    intent = {
        "state": "DISPATCH_INTENT_RECORDED",
        "workload": workload,
        "app": APP_NAME,
        "function": function_name,
        **identity,
        "max_attempts": 1,
        "synthetic_only": True,
        "child_data_in_request": False,
        "started_at": now(),
    }
    write_json(
        OUTPUT_DIR / f"{workload.replace('.', '_')}_dispatch_intent.json", intent
    )
    record: dict[str, Any] = {
        "workload": workload,
        "app": APP_NAME,
        "function": function_name,
        **identity,
        "max_attempts": 1,
        "outcome": "DISPATCH_NOT_STARTED",
        "started_at": now(),
    }
    started = time.perf_counter()
    call = None
    terminal = False
    volume = modal.Volume.from_name(
        SCRATCH_VOLUME, environment_name=ENVIRONMENT, version=2
    )
    try:
        with volume.batch_upload() as batch:
            batch.put_file(
                BytesIO(request_bytes),
                f"/{identity['attempt_prefix']}input/request.json",
            )
            batch.put_file(
                BytesIO(manifest_bytes),
                f"/{identity['attempt_prefix']}input/manifest.json",
            )
        function = modal.Function.from_name(
            APP_NAME, function_name, environment_name=ENVIRONMENT
        )
        call = function.spawn(payload)
        record["call_id"] = getattr(call, "object_id", None)
        if not isinstance(record["call_id"], str) or not record["call_id"].startswith(
            "fc-"
        ):
            record["outcome"] = "UNKNOWN_NO_CALL_ID"
            record["error_category"] = "CALL_ID_MISSING"
            return record
        record["dispatched_at"] = now()
        result = call.get(timeout=WAIT_SECONDS)
        terminal = True
        safe, image_bytes = _validate_image_result(
            workload=workload,
            result=result,
            expected_size=expected_size,
            identity=identity,
            request_data=request_data,
        )
        artifact = OUTPUT_DIR / output_filename
        artifact.write_bytes(image_bytes)
        record.update(
            {
                "outcome": "SUCCEEDED",
                "result": safe,
                "asset_file": output_filename,
                "output_sha256": sha256(canonical(safe)),
                "completed_at": now(),
            }
        )
    except TimeoutError as exc:
        record["outcome"] = "UNKNOWN_NO_RETRY"
        record["error_category"] = _safe_error_category(exc)
        if call is not None:
            try:
                call.cancel(terminate_containers=True)
                record["call_cancel_requested"] = True
            except Exception:  # noqa: BLE001 - do not persist provider exception details
                record["call_cancel_requested"] = False
    except Exception as exc:  # noqa: BLE001 - store safe classification only
        terminal = call is not None
        record["outcome"] = "FAILED_TERMINAL" if terminal else "FAILED_NO_DISPATCH"
        record["error_type"] = type(exc).__name__
        record["error_category"] = _safe_error_category(exc)
    finally:
        record["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
        if terminal:
            try:
                volume.remove_file(f"{identity['attempt_prefix']}input", recursive=True)
                record["scratch_input_removed"] = True
            except Exception as exc:  # noqa: BLE001 - cleanup failure is metadata only
                record["scratch_cleanup_error_type"] = type(exc).__name__
        write_json(OUTPUT_DIR / f"{workload.replace('.', '_')}_result.json", record)
    return record


def main() -> int:
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise SystemExit(
            "Rev46A evidence directory is not empty; refusing duplicate dispatch."
        )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "plan": "PLAN_REV46A_FLUX_COMPONENT_FILES_AND_FAILED_FLOW_RETEST_20261105.md",
        "started_at": now(),
        "synthetic_only": True,
        "child_data_used": False,
        "video_called": False,
        "qwen_story_or_drawing_retested": False,
        "active_qwen_profile": "Qwen/Qwen3.5-9B",
        "qwen2_runtime_called": False,
        "required_model_components": ["transformer", "vae"],
        "max_attempts_per_modal_function": 1,
        "wait_limit_seconds_per_inference": WAIT_SECONDS,
        "secret_resource_name": "huggingface-secret",
        "secret_value_read_by_runner": False,
        "model_volume": MODEL_VOLUME,
        "model_volume_deleted": False,
    }
    _save_report(report)
    if not download_once(report):
        report["inferences"] = [
            {
                "workload": "parent.sketch-guide.generate",
                "outcome": "NOT_RUN_MODEL_NOT_READY",
            },
            {
                "workload": "lesson.visual.generate",
                "outcome": "NOT_RUN_MODEL_NOT_READY",
            },
        ]
        _save_report(report)
        return 1

    inferences = [
        run_image_workload(
            workload="parent.sketch-guide.generate",
            function_name="generate-line-sketch-guide-candidate",
            request_data={
                "topic": "butterfly",
                "difficulty": "beginner",
                "step_count": 3,
            },
            output_filename="parent_sketch_guide_candidate.png",
            expected_size=(768, 512),
        ),
        run_image_workload(
            workload="lesson.visual.generate",
            function_name="generate-approved-lesson-visual-candidate",
            request_data=_lesson_visual_input(),
            output_filename="lesson_visual_candidate.png",
            expected_size=(768, 432),
        ),
    ]
    report["inferences"] = inferences
    report["ended_at"] = now()
    report["outcome"] = (
        "SUCCEEDED_ALL"
        if all(item.get("outcome") == "SUCCEEDED" for item in inferences)
        else "PARTIAL_OR_FAILED"
    )
    _save_report(report)
    return 0 if report["outcome"] == "SUCCEEDED_ALL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
