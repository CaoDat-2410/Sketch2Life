"""One-shot, synthetic-only SAM 2.1 checkpoint preflight and mask retest."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
MODAL_DIR = REPO / "deployment" / "modal" / "srs_v23"
BACKEND_SRC = REPO / "backend" / "src"
for import_path in (MODAL_DIR, BACKEND_SRC):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import modal  # noqa: E402
from sketch2life.infrastructure.ai.modal_function_client import (  # noqa: E402
    summarize_worker_call_logs,
)

OUTPUT_DIR = FEATURE / "evidence" / "sam2_gate_retest_20261106"
IMAGE_PATH = (
    FEATURE
    / "evidence"
    / "assets"
    / "parent_generated_image_activity_retest_20261103"
    / "synthetic_childlike_butterfly.png"
)
APP_NAME = "sketch2life-srs23-drawing-segment-dev"
MODEL_VOLUME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
SAM2_REVISION = "2b90b9f5ceec907a1c18123530e92e794ad901a4"
CHECKPOINT_MAX_BYTES = 512 * 1024 * 1024
OUTPUT_MAX_BYTES = 16 * 1024 * 1024
CHECKPOINT_WAIT_SECONDS = 600
INFERENCE_WAIT_SECONDS = 1_800
SAFE_CODE = re.compile(r"\A(?:MODAL|SAM2)_[A-Z0-9_]{1,76}\Z")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _safe_error(exc: Exception) -> dict[str, object]:
    value: dict[str, object] = {"error_type": type(exc).__name__}
    code = getattr(exc, "code", None)
    if isinstance(code, str) and SAFE_CODE.fullmatch(code):
        value["error_code"] = code
    http_status = getattr(exc, "code", None)
    if isinstance(http_status, int) and 100 <= http_status <= 599:
        value["http_status"] = http_status
    return value


def _call_logs(call_id: str | None) -> dict[str, Any] | None:
    if not isinstance(call_id, str) or not call_id.startswith("fc-"):
        return None
    try:
        return summarize_worker_call_logs(
            modal.FunctionCall.from_id(call_id), max_log_wait_seconds=20
        )
    except Exception as exc:  # noqa: BLE001 - keep only safe exception metadata.
        return {
            "worker_logs_available": False,
            "worker_failure_boundary": "worker_log_fetch_exception",
            **_safe_error(exc),
        }


def _terminal_outcome(call_id: str | None, fallback: str) -> tuple[str, dict[str, Any] | None]:
    logs = _call_logs(call_id) if call_id else None
    terminal = logs.get("worker_terminal_event") if logs else None
    if terminal == "worker_failed":
        return "FAILED_TERMINAL", logs
    if terminal == "worker_succeeded":
        return "OUTPUT_VALIDATION_FAILED", logs
    return fallback, logs


def _checkpoint_preflight() -> dict[str, Any]:
    started = time.perf_counter()
    record: dict[str, Any] = {
        "stage": "checkpoint_preflight",
        "function": "download-sam2-hiera-small-checkpoint",
        "started_at": _now(),
        "max_attempts": 1,
        "timeout_seconds": CHECKPOINT_WAIT_SECONDS,
    }
    _write(OUTPUT_DIR / "checkpoint_preflight_dispatch_intent.json", record)
    call_id: str | None = None
    try:
        function = modal.Function.from_name(
            APP_NAME,
            "download-sam2-hiera-small-checkpoint",
            environment_name="dev",
        )
        call = function.spawn()
        call_id = getattr(call, "object_id", None)
        record["call_id"] = call_id
        _write(OUTPUT_DIR / "checkpoint_preflight_dispatch_intent.json", record)
        result = call.get(timeout=CHECKPOINT_WAIT_SECONDS)
    except TimeoutError as exc:
        if call_id:
            try:
                modal.FunctionCall.from_id(call_id).cancel(terminate_containers=True)
            except Exception:  # noqa: BLE001 - preserve timeout as the primary signal.
                pass
        outcome, logs = _terminal_outcome(call_id, "UNKNOWN_NO_RETRY")
        record.update(
            {
                "outcome": outcome,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                "ended_at": _now(),
                "worker_log_summary": logs,
                **_safe_error(exc),
            }
        )
        _write(OUTPUT_DIR / "checkpoint_preflight_result.json", record)
        return record
    except Exception as exc:  # noqa: BLE001 - stage/code are enough for safe diagnosis.
        outcome, logs = _terminal_outcome(call_id, "UNKNOWN_NO_RETRY" if call_id else "DISPATCH_FAILED_NO_CALL")
        record.update(
            {
                "outcome": outcome,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                "ended_at": _now(),
                "worker_log_summary": logs,
                **_safe_error(exc),
            }
        )
        _write(OUTPUT_DIR / "checkpoint_preflight_result.json", record)
        return record

    logs = _call_logs(call_id) if call_id else None
    digest = result.get("checkpoint_sha256") if isinstance(result, dict) else None
    size = result.get("checkpoint_size_bytes") if isinstance(result, dict) else None
    revision = result.get("repository_commit") if isinstance(result, dict) else None
    status = result.get("status") if isinstance(result, dict) else None
    verified = (
        status in {"downloaded", "already_present"}
        and revision == SAM2_REVISION
        and isinstance(digest, str)
        and re.fullmatch(r"[a-f0-9]{64}", digest) is not None
        and isinstance(size, int)
        and not isinstance(size, bool)
        and 0 < size <= CHECKPOINT_MAX_BYTES
    )
    record.update(
        {
            "outcome": "SUCCEEDED" if verified else "FAILED_TERMINAL",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "ended_at": _now(),
            "worker_log_summary": logs,
            "checkpoint_status": status,
            "repository_commit": revision,
            "checkpoint_sha256": digest if isinstance(digest, str) else None,
            "checkpoint_size_bytes": size if isinstance(size, int) else None,
            "license": result.get("license") if isinstance(result, dict) else None,
        }
    )
    _write(OUTPUT_DIR / "checkpoint_preflight_result.json", record)
    return record


def _run_inference(source_bytes: bytes) -> dict[str, Any]:
    source_sha = _sha(source_bytes)
    job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
    prefix = f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/"
    manifest = {
        "schema_version": "sketch2life.modal.drawing-input.v1",
        "asset": {
            "path": "input/drawing.png",
            "content_type": "image/png",
            "size_bytes": len(source_bytes),
            "sha256": source_sha,
        },
    }
    manifest_bytes = _canonical_json(manifest)
    payload = {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": "dev",
        "workload": "drawing.segment",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": _sha(manifest_bytes),
        "input_bytes": len(source_bytes) + len(manifest_bytes),
    }
    intent: dict[str, Any] = {
        "state": "DISPATCH_INTENT_RECORDED",
        "stage": "gpu_inference",
        "app": APP_NAME,
        "function": "segment-synthetic-drawing-candidate",
        "workload": "drawing.segment",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "source_image_sha256": source_sha,
        "source_image_size_bytes": len(source_bytes),
        "max_attempts": 1,
        "wait_timeout_seconds": INFERENCE_WAIT_SECONDS,
        "worker_timeout_seconds": 600,
        "started_at": _now(),
        "video_called": False,
    }
    _write(OUTPUT_DIR / "inference_dispatch_intent.json", intent)

    volume = modal.Volume.from_name(SCRATCH_VOLUME, environment_name="dev", version=2)
    with volume.batch_upload() as batch:
        batch.put_file(BytesIO(source_bytes), f"/{prefix}input/drawing.png")
        batch.put_file(BytesIO(manifest_bytes), f"/{prefix}input/manifest.json")

    started = time.perf_counter()
    call_id: str | None = None
    terminal = False
    try:
        function = modal.Function.from_name(
            APP_NAME,
            "segment-synthetic-drawing-candidate",
            environment_name="dev",
        )
        call = function.spawn(payload)
        call_id = getattr(call, "object_id", None)
        intent["call_id"] = call_id
        intent["state"] = "DISPATCHED"
        _write(OUTPUT_DIR / "inference_dispatch_intent.json", intent)
        output = call.get(timeout=INFERENCE_WAIT_SECONDS)
        terminal = True
    except TimeoutError as exc:
        if call_id:
            try:
                modal.FunctionCall.from_id(call_id).cancel(terminate_containers=True)
                modal.FunctionCall.from_id(call_id).get(timeout=5)
                terminal = True
            except Exception:  # noqa: BLE001 - bounded cancellation confirmation.
                pass
        outcome, logs = _terminal_outcome(call_id, "UNKNOWN_NO_RETRY")
        record = {
            "workload": "drawing.segment",
            "outcome": outcome,
            "call_id": call_id,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "source_image_sha256": source_sha,
            "worker_log_summary": logs,
            "video_calls": 0,
            **_safe_error(exc),
        }
        _write(OUTPUT_DIR / "inference_result.json", record)
        if terminal:
            volume.remove_file(f"{prefix}input", recursive=True)
        return record
    except Exception as exc:  # noqa: BLE001 - preserve safe type/code and worker phases.
        outcome, logs = _terminal_outcome(
            call_id, "UNKNOWN_NO_RETRY" if call_id else "DISPATCH_FAILED_NO_CALL"
        )
        record = {
            "workload": "drawing.segment",
            "outcome": outcome,
            "call_id": call_id,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "source_image_sha256": source_sha,
            "worker_log_summary": logs,
            "video_calls": 0,
            **_safe_error(exc),
        }
        _write(OUTPUT_DIR / "inference_result.json", record)
        if terminal:
            volume.remove_file(f"{prefix}input", recursive=True)
        return record

    logs = _call_logs(call_id) if call_id else None
    asset = output.get("asset") if isinstance(output, dict) else None
    mask_bytes = asset.get("bytes") if isinstance(asset, dict) else None
    expected = {
        "schema_version": "sketch2life.modal.worker-output.v1",
        "workload": "drawing.segment",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "input_sha256": source_sha,
    }
    output_contract_valid = isinstance(output, dict) and all(
        output.get(key) == value for key, value in expected.items()
    )
    asset_valid = (
        isinstance(asset, dict)
        and isinstance(mask_bytes, bytes)
        and len(mask_bytes) == asset.get("size_bytes")
        and 0 < len(mask_bytes) <= OUTPUT_MAX_BYTES
        and _sha(mask_bytes) == asset.get("sha256")
        and mask_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        and asset.get("content_type") == "image/png"
    )
    if output_contract_valid and asset_valid:
        mask_path = OUTPUT_DIR / "sam2_synthetic_butterfly_mask.png"
        mask_path.write_bytes(mask_bytes)
        result = output.get("result")
        model = output.get("model")
        record = {
            "workload": "drawing.segment",
            "outcome": "SUCCEEDED",
            "call_id": call_id,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "source_image_sha256": source_sha,
            "source_image_size_bytes": len(source_bytes),
            "source_image_unchanged": _sha(IMAGE_PATH.read_bytes()) == source_sha,
            "mask_file": mask_path.name,
            "mask_sha256": _sha(mask_bytes),
            "mask_size_bytes": len(mask_bytes),
            "mask_content_type": asset.get("content_type"),
            "mask_dimensions": [asset.get("width"), asset.get("height")],
            "model": {
                "id": model.get("id") if isinstance(model, dict) else None,
                "revision": model.get("revision") if isinstance(model, dict) else None,
                "checkpoint_sha256": model.get("checkpoint_sha256") if isinstance(model, dict) else None,
            },
            "result": {
                key: result.get(key)
                for key in ("status", "mask_score", "mask_area_ratio", "review_required")
            }
            if isinstance(result, dict)
            else None,
            "worker_log_summary": logs,
            "video_calls": 0,
        }
    else:
        terminal_outcome = "OUTPUT_VALIDATION_FAILED"
        terminal_event = logs.get("worker_terminal_event") if logs else None
        if terminal_event == "worker_failed":
            terminal_outcome = "FAILED_TERMINAL"
        record = {
            "workload": "drawing.segment",
            "outcome": terminal_outcome,
            "call_id": call_id,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "source_image_sha256": source_sha,
            "output_contract_valid": output_contract_valid,
            "asset_valid": bool(asset_valid),
            "worker_log_summary": logs,
            "video_calls": 0,
        }

    _write(OUTPUT_DIR / "inference_result.json", record)
    if terminal:
        volume.remove_file(f"{prefix}input", recursive=True)
    return record


def main() -> int:
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise SystemExit("Rev53 evidence guard exists; refusing duplicate SAM2 work.")
    if not IMAGE_PATH.is_file():
        raise SystemExit("Synthetic source fixture is missing; no Modal calls made.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_bytes = IMAGE_PATH.read_bytes()
    source_sha = _sha(source_bytes)
    started = _now()

    _write(
        OUTPUT_DIR / "run_metadata.json",
        {
            "plan": "PLAN_REV53_SAM2_GATE_RETEST_20261106.md",
            "environment": "dev",
            "app": APP_NAME,
            "synthetic_only": True,
            "source_fixture": IMAGE_PATH.name,
            "source_sha256": source_sha,
            "source_size_bytes": len(source_bytes),
            "inference_attempt_limit": 1,
            "checkpoint_preflight_attempt_limit": 1,
            "checkpoint_wait_seconds": CHECKPOINT_WAIT_SECONDS,
            "inference_wait_seconds": INFERENCE_WAIT_SECONDS,
            "worker_timeout_seconds": 600,
            "video_called": False,
            "started_at": started,
        },
    )

    checkpoint = _checkpoint_preflight()
    if checkpoint.get("outcome") != "SUCCEEDED":
        summary = {
            "status": "STOPPED_BEFORE_GPU_PREFLIGHT_FAILED",
            "started_at": started,
            "ended_at": _now(),
            "checkpoint_preflight": checkpoint,
            "inference_dispatched": False,
            "video_calls": 0,
        }
        _write(OUTPUT_DIR / "summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1

    inference = _run_inference(source_bytes)
    summary = {
        "status": inference.get("outcome"),
        "started_at": started,
        "ended_at": _now(),
        "checkpoint_preflight": {
            key: checkpoint.get(key)
            for key in (
                "outcome",
                "call_id",
                "elapsed_ms",
                "repository_commit",
                "checkpoint_sha256",
                "checkpoint_size_bytes",
            )
        },
        "inference": inference,
        "inference_dispatched": bool(inference.get("call_id")),
        "video_calls": 0,
    }
    _write(OUTPUT_DIR / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if inference.get("outcome") == "SUCCEEDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
