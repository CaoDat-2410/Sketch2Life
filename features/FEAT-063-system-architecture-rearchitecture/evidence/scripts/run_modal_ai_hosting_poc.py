"""Run the approved, synthetic-only Modal language/audio POC calls."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import uuid
from typing import Any

import modal


SCRIPT_PATH = Path(__file__).resolve()
FEATURE_DIR = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]
APP_NAME = "sketch2life-srs23-language-audio-dev"
FLUX_APP_NAME = "sketch2life-srs23-flux-image-dev"
WAN_APP_NAME = "sketch2life-srs23-video-candidate-dev"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
SCRATCH_VOLUME_VERSION = 2
WORKER_INPUT_SCHEMA = "sketch2life.modal.worker-input.v1"
INPUT_SCHEMA = "sketch2life.modal.ai-request.v1"
MAX_STAGED_INPUT_BYTES = 48 * 1024 * 1024
OUTPUT_DIR = FEATURE_DIR / "evidence" / "assets" / "modal_ai_hosting_wave_20261103"

CONTRACT_DIR = REPO_ROOT / "deployment" / "modal" / "srs_v23"
sys.path.insert(0, str(CONTRACT_DIR))
from contracts import parse_worker_input  # noqa: E402


def _stage_json(
    volume: Any,
    *,
    workload: str,
    job_id: str,
    generation_id: str,
    data: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    request_bytes = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _stage_asset(
        volume,
        workload=workload,
        job_id=job_id,
        generation_id=generation_id,
        asset_path="input/request.json",
        content_type="application/json",
        asset_bytes=request_bytes,
    )


def _stage_asset(
    volume: Any,
    *,
    workload: str,
    job_id: str,
    generation_id: str,
    asset_path: str,
    content_type: str,
    asset_bytes: bytes,
) -> tuple[dict[str, Any], str]:
    attempt_id = f"attempt-{uuid.uuid4().hex[:12]}"
    attempt_prefix = f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/"
    manifest = {
        "schema_version": INPUT_SCHEMA,
        "asset": {
            "path": asset_path,
            "content_type": content_type,
            "size_bytes": len(asset_bytes),
            "sha256": hashlib.sha256(asset_bytes).hexdigest(),
        },
    }
    manifest_bytes = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    input_bytes = len(asset_bytes) + len(manifest_bytes)
    if input_bytes > MAX_STAGED_INPUT_BYTES:
        raise ValueError("Synthetic request exceeds the approved Modal input cap")

    payload: dict[str, Any] = {
        "schema_version": WORKER_INPUT_SCHEMA,
        "environment": "dev",
        "workload": workload,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": attempt_prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "input_bytes": input_bytes,
    }
    parse_worker_input(payload, execution_group="l4")
    with volume.batch_upload() as batch:
        batch.put_file(io.BytesIO(asset_bytes), f"/{attempt_prefix}{asset_path}")
        batch.put_file(io.BytesIO(manifest_bytes), f"/{attempt_prefix}input/manifest.json")
    return payload, attempt_prefix


def _cleanup(volume: Any, attempt_prefix: str) -> None:
    volume.remove_file(attempt_prefix.rstrip("/"), recursive=True)


def _save_json(name: str, data: dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def download_models() -> None:
    function = modal.Function.from_name(
        APP_NAME,
        "download-language-audio-models",
        environment_name="dev",
    )
    print(json.dumps(function.remote(), ensure_ascii=False, sort_keys=True))


def download_flux_model() -> None:
    function = modal.Function.from_name(
        FLUX_APP_NAME,
        "download-flux-pinned-model",
        environment_name="dev",
    )
    print(json.dumps(function.remote(), ensure_ascii=False, sort_keys=True))


def download_wan_video_model() -> None:
    function = modal.Function.from_name(
        WAN_APP_NAME,
        "download-wan-video-candidate-model",
        environment_name="dev",
    )
    print(json.dumps(function.remote(), ensure_ascii=False, sort_keys=True))


def run_story() -> None:
    volume = modal.Volume.from_name(
        SCRATCH_VOLUME_NAME,
        environment_name="dev",
        version=SCRATCH_VOLUME_VERSION,
    )
    payload, prefix = _stage_json(
        volume,
        workload="story.generate",
        job_id="modal-ai-hosting-20261103",
        generation_id="story-butterfly-v1",
        data={"topic": "bướm", "language": "vi", "scene_count": 5},
    )
    try:
        function = modal.Function.from_name(
            APP_NAME,
            "generate-story-and-storyboard",
            environment_name="dev",
        )
        started = time.perf_counter()
        result = function.remote(payload)
        elapsed = round(time.perf_counter() - started, 3)
        _save_json(
            "qwen_story_storyboard_result.json",
            {
                "elapsed_seconds_including_cold_start": elapsed,
                "input_manifest_sha256": payload["input_manifest_sha256"],
                "result": result,
            },
        )
        print(json.dumps({"elapsed_seconds": elapsed, "result": result}, ensure_ascii=False, sort_keys=True))
    finally:
        _cleanup(volume, prefix)


def run_speech() -> None:
    volume = modal.Volume.from_name(
        SCRATCH_VOLUME_NAME,
        environment_name="dev",
        version=SCRATCH_VOLUME_VERSION,
    )
    job_id = "modal-ai-hosting-20261103"

    tts_payload, tts_prefix = _stage_json(
        volume,
        workload="tts.narration.generate",
        job_id=job_id,
        generation_id="speech-v1",
        data={"text": "Con bướm bay qua khu vườn đầy nắng.", "voice": "Hải Đăng"},
    )
    try:
        tts_function = modal.Function.from_name(
            APP_NAME,
            "synthesize-vietnamese-narration",
            environment_name="dev",
        )
        started = time.perf_counter()
        tts_result = tts_function.remote(tts_payload)
        tts_elapsed = round(time.perf_counter() - started, 3)
    finally:
        _cleanup(volume, tts_prefix)

    asset = tts_result.get("asset")
    if not isinstance(asset, dict) or not isinstance(asset.get("bytes"), bytes):
        raise RuntimeError("VieNeu POC response is missing the bounded WAV bytes")
    audio_bytes = asset["bytes"]
    if (
        len(audio_bytes) != asset.get("size_bytes")
        or hashlib.sha256(audio_bytes).hexdigest() != asset.get("sha256")
        or not audio_bytes.startswith(b"RIFF")
    ):
        raise RuntimeError("VieNeu POC output integrity check failed")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = OUTPUT_DIR / "vieneu_synthetic_narration.wav"
    audio_path.write_bytes(audio_bytes)

    asr_payload, asr_prefix = _stage_asset(
        volume,
        workload="asr.transcribe",
        job_id=job_id,
        generation_id="speech-v1",
        asset_path="input/audio.wav",
        content_type="audio/wav",
        asset_bytes=audio_bytes,
    )
    try:
        asr_function = modal.Function.from_name(
            APP_NAME,
            "transcribe-vietnamese-audio",
            environment_name="dev",
        )
        started = time.perf_counter()
        asr_result = asr_function.remote(asr_payload)
        asr_elapsed = round(time.perf_counter() - started, 3)
    finally:
        _cleanup(volume, asr_prefix)

    evidence = {
        "tts_elapsed_seconds_including_cold_start": tts_elapsed,
        "asr_elapsed_seconds_including_cold_start": asr_elapsed,
        "audio_file": audio_path.name,
        "audio_sha256": asset["sha256"],
        "audio_bytes": len(audio_bytes),
        "tts": {key: value for key, value in tts_result.items() if key != "asset"},
        "tts_asset": {key: value for key, value in asset.items() if key != "bytes"},
        "asr": asr_result,
    }
    _save_json("vieneu_faster_whisper_result.json", evidence)
    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))


def run_flux() -> None:
    volume = modal.Volume.from_name(
        SCRATCH_VOLUME_NAME,
        environment_name="dev",
        version=SCRATCH_VOLUME_VERSION,
    )
    payload, prefix = _stage_json(
        volume,
        workload="parent.sketch-guide.generate",
        job_id="modal-ai-hosting-20261103",
        generation_id="flux-butterfly-guide-v1",
        data={"topic": "butterfly", "difficulty": "beginner", "step_count": 3},
    )
    try:
        function = modal.Function.from_name(
            FLUX_APP_NAME,
            "generate-line-sketch-guide-candidate",
            environment_name="dev",
        )
        started = time.perf_counter()
        result = function.remote(payload)
        elapsed = round(time.perf_counter() - started, 3)
    finally:
        _cleanup(volume, prefix)

    asset = result.get("asset")
    if not isinstance(asset, dict) or not isinstance(asset.get("bytes"), bytes):
        raise RuntimeError("FLUX POC response is missing the bounded PNG bytes")
    image_bytes = asset["bytes"]
    if (
        len(image_bytes) != asset.get("size_bytes")
        or hashlib.sha256(image_bytes).hexdigest() != asset.get("sha256")
        or not image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        raise RuntimeError("FLUX POC output integrity check failed")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image_path = OUTPUT_DIR / "flux2_klein_synthetic_butterfly_guide.png"
    image_path.write_bytes(image_bytes)
    evidence = {
        "elapsed_seconds_including_cold_start": elapsed,
        "image_file": image_path.name,
        "image_sha256": asset["sha256"],
        "image_bytes": len(image_bytes),
        "width": asset.get("width"),
        "height": asset.get("height"),
        "model": result.get("model"),
        "limitations": result.get("limitations"),
    }
    _save_json("flux2_klein_synthetic_guide_result.json", evidence)
    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))


def run_wan_video_candidate() -> None:
    volume = modal.Volume.from_name(
        SCRATCH_VOLUME_NAME,
        environment_name="dev",
        version=SCRATCH_VOLUME_VERSION,
    )
    image_path = FEATURE_DIR / "evidence" / "assets" / "drawing_vlm_synthetic_butterfly.png"
    image_bytes = image_path.read_bytes()
    image_sha256 = hashlib.sha256(image_bytes).hexdigest()
    if image_sha256 != "4b18777ae70eb429273c1e0ba7189ff005171b9dda88491510d91965aafa07fc":
        raise RuntimeError("Synthetic butterfly input fixture hash changed")
    payload, prefix = _stage_asset(
        volume,
        workload="video.scene.generate",
        job_id="modal-ai-hosting-20261103",
        generation_id="wan-butterfly-v1",
        asset_path="input/drawing.png",
        content_type="image/png",
        asset_bytes=image_bytes,
    )
    try:
        function = modal.Function.from_name(
            WAN_APP_NAME,
            "generate-wan-video-candidate",
            environment_name="dev",
        )
        started = time.perf_counter()
        result = function.remote(payload)
        elapsed = round(time.perf_counter() - started, 3)
    finally:
        _cleanup(volume, prefix)

    asset = result.get("asset")
    if not isinstance(asset, dict) or not isinstance(asset.get("bytes"), bytes):
        raise RuntimeError("Wan POC response is missing the bounded MP4 bytes")
    video_bytes = asset["bytes"]
    if (
        len(video_bytes) != asset.get("size_bytes")
        or hashlib.sha256(video_bytes).hexdigest() != asset.get("sha256")
        or len(video_bytes) < 12
        or video_bytes[4:8] != b"ftyp"
        or asset.get("content_type") != "video/mp4"
    ):
        raise RuntimeError("Wan POC output integrity check failed")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    video_path = OUTPUT_DIR / "wan22_synthetic_butterfly_candidate.mp4"
    video_path.write_bytes(video_bytes)
    evidence = {
        "elapsed_seconds_including_cold_start": elapsed,
        "input_sha256": image_sha256,
        "video_file": video_path.name,
        "video_sha256": asset["sha256"],
        "video_bytes": len(video_bytes),
        "duration_seconds": asset.get("duration_seconds"),
        "frame_count": asset.get("frame_count"),
        "fps": asset.get("fps"),
        "model": result.get("model"),
        "runtime": result.get("runtime"),
        "limitations": result.get("limitations"),
    }
    _save_json("wan22_synthetic_video_candidate_result.json", evidence)
    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--download-language-audio-models", action="store_true")
    group.add_argument("--download-flux-model", action="store_true")
    group.add_argument("--download-wan-video-model", action="store_true")
    group.add_argument("--story", action="store_true")
    group.add_argument("--speech", action="store_true")
    group.add_argument("--flux", action="store_true")
    group.add_argument("--wan-video", action="store_true")
    args = parser.parse_args()
    if args.download_language_audio_models:
        download_models()
    elif args.download_flux_model:
        download_flux_model()
    elif args.download_wan_video_model:
        download_wan_video_model()
    elif args.story:
        run_story()
    elif args.speech:
        run_speech()
    elif args.wan_video:
        run_wan_video_candidate()
    else:
        run_flux()


if __name__ == "__main__":
    main()
