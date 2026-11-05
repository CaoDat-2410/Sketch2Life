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
MODAL_ENV = "dev"
APP_NAME = "sketch2life-srs23-language-audio-dev"
SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
OUTPUT_LIMIT = 256 * 1024


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _invoke(
    *,
    workload: str,
    function_name: str,
    asset_path: str,
    content_type: str,
    asset_bytes: bytes,
    output_path: Path | None,
) -> dict[str, Any]:
    job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
    prefix = f"sketch2life/{MODAL_ENV}/{job_id}/{generation_id}/{attempt_id}/"
    manifest = {
        "schema_version": "sketch2life.modal.ai-request.v1",
        "asset": {
            "path": asset_path,
            "content_type": content_type,
            "size_bytes": len(asset_bytes),
            "sha256": _sha256(asset_bytes),
        },
    }
    manifest_bytes = _canonical(manifest)
    payload = {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": MODAL_ENV,
        "workload": workload,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": _sha256(manifest_bytes),
        "input_bytes": len(asset_bytes) + len(manifest_bytes),
    }
    intent_path = OUTPUT_DIR / f"{workload.replace('.', '_')}_{attempt_id}_dispatch_intent.json"
    result_path = OUTPUT_DIR / f"{workload.replace('.', '_')}_{attempt_id}_result.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if intent_path.exists() or result_path.exists():
        raise RuntimeError("Duplicate workload attempt guard found; refusing dispatch.")
    intent = {
        "state": "DISPATCH_INTENT_RECORDED",
        "workload": workload,
        "app": APP_NAME,
        "function": function_name,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "input_sha256": _sha256(asset_bytes),
        "manifest_sha256": _sha256(manifest_bytes),
        "created_at": _now(),
        "max_attempts": 1,
    }
    intent_path.write_text(json.dumps(intent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    volume = modal.Volume.from_name(SCRATCH_VOLUME, environment_name=MODAL_ENV, version=2)
    function = modal.Function.from_name(APP_NAME, function_name, environment_name=MODAL_ENV)
    call_id: str | None = None
    terminal = False
    started = time.perf_counter()
    try:
        with volume.batch_upload() as batch:
            batch.put_file(BytesIO(asset_bytes), f"/{prefix}{asset_path}")
            batch.put_file(BytesIO(manifest_bytes), f"/{prefix}input/manifest.json")
        call = function.spawn(payload)
        call_id = getattr(call, "object_id", None)
        if not isinstance(call_id, str) or not call_id.startswith("fc-"):
            raise TimeoutError("Modal dispatch result is ambiguous; do not retry.")
        output = call.get(timeout=600)
        terminal = True
        if not isinstance(output, dict):
            raise RuntimeError("Worker returned a non-object response.")
        expected = {
            "schema_version": "sketch2life.modal.worker-output.v1",
            "workload": workload,
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
        }
        for key, value in expected.items():
            if output.get(key) != value:
                raise RuntimeError(f"Worker output contract mismatch: {key}.")
        safe_output = dict(output)
        asset = safe_output.get("asset")
        if isinstance(asset, dict):
            asset = dict(asset)
            binary = asset.pop("bytes", None)
            safe_output["asset"] = asset
            if binary is not None:
                if not isinstance(binary, bytes) or len(binary) != asset.get("size_bytes"):
                    raise RuntimeError("Generated audio size mismatch.")
                if _sha256(binary) != asset.get("sha256") or not binary.startswith(b"RIFF"):
                    raise RuntimeError("Generated WAV failed integrity/signature checks.")
                if len(binary) > OUTPUT_LIMIT:
                    raise RuntimeError("Generated WAV exceeds the output byte cap.")
                if output_path is None:
                    raise RuntimeError("Unexpected binary worker output.")
                output_path.write_bytes(binary)
                safe_output["asset_file"] = output_path.name
        record = {
            "workload": workload,
            "function": function_name,
            "call_id": call_id,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "outcome": "SUCCEEDED",
            "output_sha256": _sha256(_canonical(safe_output)),
            "result": safe_output,
        }
        result_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return record
    except Exception as exc:
        record = {
            "workload": workload,
            "function": function_name,
            "call_id": call_id,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "outcome": "UNKNOWN_NO_RETRY" if not terminal else "FAILED_TERMINAL",
            "error_type": type(exc).__name__,
        }
        result_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    finally:
        if terminal:
            volume.remove_file(f"{prefix}input", recursive=True)


def main() -> int:
    request = {"text": "Con bướm bay qua khu vườn đầy nắng.", "voice": "Hải Đăng"}
    tts = _invoke(
        workload="tts.narration.generate",
        function_name="synthesize-vietnamese-narration",
        asset_path="input/request.json",
        content_type="application/json",
        asset_bytes=_canonical(request),
        output_path=OUTPUT_DIR / "synthetic_vietnamese_narration.wav",
    )
    wav_path = OUTPUT_DIR / "synthetic_vietnamese_narration.wav"
    wav = wav_path.read_bytes()
    asr = _invoke(
        workload="asr.transcribe",
        function_name="transcribe-vietnamese-audio",
        asset_path="input/audio.wav",
        content_type="audio/wav",
        asset_bytes=wav,
        output_path=None,
    )
    summary = {
        "tts": {
            "call_id": tts["call_id"],
            "elapsed_ms": tts["elapsed_ms"],
            "audio_file": wav_path.name,
            "audio_sha256": _sha256(wav),
            "audio_size_bytes": len(wav),
        },
        "asr": {
            "call_id": asr["call_id"],
            "elapsed_ms": asr["elapsed_ms"],
            "result": asr["result"].get("result"),
        },
        "finished_at": _now(),
    }
    (OUTPUT_DIR / "speech_roundtrip_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
