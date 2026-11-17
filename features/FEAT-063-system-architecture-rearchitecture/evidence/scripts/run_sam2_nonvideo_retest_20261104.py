from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import modal

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
OUTPUT_DIR = FEATURE / "evidence" / "assets" / "ai_nonvideo_full_retest_20261104"
IMAGE_PATH = FEATURE / "evidence" / "assets" / "parent_generated_image_activity_retest_20261103" / "synthetic_childlike_butterfly.png"
APP_NAME = "sketch2life-srs23-drawing-segment-dev"
SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
MODEL_COMMIT = "2b90b9f5ceec907a1c18123530e92e794ad901a4"
MAX_WAIT_SECONDS = 600
MAX_OUTPUT_BYTES = 16 * 1024 * 1024


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _save(name: str, value: object) -> None:
    (OUTPUT_DIR / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _bounded_call(function: Any, args: tuple[Any, ...], *, timeout: int, label: str) -> tuple[Any, str, float]:
    call = function.spawn(*args)
    call_id = getattr(call, "object_id", None)
    if not isinstance(call_id, str) or not call_id.startswith("fc-"):
        raise RuntimeError(f"{label}: dispatch outcome unknown before call ID.")
    started = time.perf_counter()
    try:
        result = call.get(timeout=timeout)
    except TimeoutError:
        call.cancel(terminate_containers=True)
        raise
    return result, call_id, round((time.perf_counter() - started) * 1000, 2)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    download_guard = OUTPUT_DIR / "sam2_checkpoint_download_dispatch_intent.json"
    inference_guard = OUTPUT_DIR / "sam2_segment_dispatch_intent.json"
    if download_guard.exists() or inference_guard.exists():
        raise SystemExit("SAM2 dispatch guard already exists; refusing duplicate model work.")

    download_start = _now()
    _save(
        download_guard.name,
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "stage": "checkpoint_download",
            "app": APP_NAME,
            "function": "download-sam2-hiera-small-checkpoint",
            "started_at": download_start,
            "max_attempts": 1,
        },
    )
    download_function = modal.Function.from_name(
        APP_NAME, "download-sam2-hiera-small-checkpoint", environment_name="dev"
    )
    try:
        checkpoint, download_call_id, download_elapsed = _bounded_call(
            download_function, (), timeout=MAX_WAIT_SECONDS, label="SAM2 checkpoint download"
        )
    except Exception as exc:
        _save(
            "sam2_checkpoint_download_result.json",
            {"outcome": "UNKNOWN_NO_RETRY", "error_type": type(exc).__name__, "ended_at": _now()},
        )
        return 1
    if not isinstance(checkpoint, dict) or checkpoint.get("status") not in {"downloaded", "already_present"}:
        _save("sam2_checkpoint_download_result.json", {"outcome": "FAILED_TERMINAL", "ended_at": _now()})
        return 1
    checkpoint_record = {
        "outcome": "SUCCEEDED",
        "call_id": download_call_id,
        "elapsed_ms": download_elapsed,
        "started_at": download_start,
        "ended_at": _now(),
        "checkpoint": checkpoint,
    }
    _save("sam2_checkpoint_download_result.json", checkpoint_record)

    image_bytes = IMAGE_PATH.read_bytes()
    image_sha = _sha(image_bytes)
    job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
    prefix = f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/"
    manifest = {
        "schema_version": "sketch2life.modal.drawing-input.v1",
        "asset": {
            "path": "input/drawing.png",
            "content_type": "image/png",
            "size_bytes": len(image_bytes),
            "sha256": image_sha,
        },
    }
    manifest_bytes = _json_bytes(manifest)
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
        "input_bytes": len(image_bytes) + len(manifest_bytes),
    }
    _save(
        inference_guard.name,
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "workload": "drawing.segment",
            "app": APP_NAME,
            "function": "segment-synthetic-drawing-candidate",
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "source_image_sha256": image_sha,
            "source_image_bytes": len(image_bytes),
            "started_at": _now(),
            "max_attempts": 1,
            "source_image_is_immutable": True,
        },
    )
    volume = modal.Volume.from_name(SCRATCH_VOLUME, environment_name="dev", version=2)
    with volume.batch_upload() as batch:
        batch.put_file(BytesIO(image_bytes), f"/{prefix}input/drawing.png")
        batch.put_file(BytesIO(manifest_bytes), f"/{prefix}input/manifest.json")
    function = modal.Function.from_name(
        APP_NAME, "segment-synthetic-drawing-candidate", environment_name="dev"
    )
    inference_started = _now()
    terminal = False
    try:
        output, call_id, elapsed_ms = _bounded_call(
            function, (payload,), timeout=MAX_WAIT_SECONDS, label="SAM2 segmentation"
        )
        terminal = True
        if not isinstance(output, dict):
            raise RuntimeError("SAM2 returned a non-object output.")
        expected = {
            "schema_version": "sketch2life.modal.worker-output.v1",
            "workload": "drawing.segment",
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "input_sha256": image_sha,
        }
        if any(output.get(key) != value for key, value in expected.items()):
            raise RuntimeError("SAM2 worker output contract or source lineage mismatch.")
        asset = output.get("asset")
        if not isinstance(asset, dict):
            raise RuntimeError("SAM2 response is missing derived mask metadata.")
        mask_bytes = asset.pop("bytes", None)
        if (
            not isinstance(mask_bytes, bytes)
            or len(mask_bytes) != asset.get("size_bytes")
            or len(mask_bytes) > MAX_OUTPUT_BYTES
            or _sha(mask_bytes) != asset.get("sha256")
            or not mask_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        ):
            raise RuntimeError("SAM2 derived mask failed integrity checks.")
        mask_path = OUTPUT_DIR / "sam2_synthetic_butterfly_mask.png"
        mask_path.write_bytes(mask_bytes)
        safe_output = {key: value for key, value in output.items() if key != "asset"}
        safe_output["asset"] = asset
        result = {
            "outcome": "SUCCEEDED",
            "call_id": call_id,
            "elapsed_ms": elapsed_ms,
            "started_at": inference_started,
            "ended_at": _now(),
            "source_image_sha256": image_sha,
            "source_image_unchanged": _sha(IMAGE_PATH.read_bytes()) == image_sha,
            "mask_file": mask_path.name,
            "mask_sha256": _sha(mask_bytes),
            "mask_bytes": len(mask_bytes),
            "worker_output": safe_output,
        }
        _save("sam2_segment_result.json", result)
        print(json.dumps({"outcome": "SUCCEEDED", "call_id": call_id, "elapsed_ms": elapsed_ms, "mask_sha256": result["mask_sha256"]}, ensure_ascii=True))
        return 0
    except Exception as exc:
        result = {
            "outcome": "UNKNOWN_NO_RETRY" if not terminal else "FAILED_TERMINAL",
            "error_type": type(exc).__name__,
            "started_at": inference_started,
            "ended_at": _now(),
            "source_image_sha256": image_sha,
        }
        _save("sam2_segment_result.json", result)
        print(json.dumps(result, ensure_ascii=True))
        return 1
    finally:
        volume.remove_file(f"{prefix}input", recursive=True)


if __name__ == "__main__":
    raise SystemExit(main())
