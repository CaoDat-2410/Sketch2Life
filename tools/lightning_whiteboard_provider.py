"""Minimal Lightning GPU provider for FEAT-018 whiteboard localization/segmentation."""

from __future__ import annotations

import base64
import hashlib
import importlib
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from contextlib import nullcontext
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Sketch2Life Whiteboard Provider", version="1.0.0")
_LOGGER = logging.getLogger("sketch2life.whiteboard_provider")

MODEL_ID = os.getenv("SKETCH2LIFE_VLM_MODEL", "Qwen/Qwen3-VL-2B-Instruct")
_vlm = None
_processor = None
_sam_predictor = None
_boxes: dict[str, list[float]] = {}


def _decode_source(payload: dict[str, Any]) -> tuple[bytes, Any, str]:
    from PIL import Image

    source = payload.get("source_image")
    if not isinstance(source, dict):
        raise TypeError("source_image is required")
    encoded = source.get("content_base64")
    expected_hash = source.get("sha256")
    if not isinstance(encoded, str) or not isinstance(expected_hash, str):
        raise TypeError("source image payload is invalid")
    try:
        data = base64.b64decode(encoded, validate=True)
        image = Image.open(io.BytesIO(data)).convert("RGB")
    except (ValueError, OSError) as error:
        raise ValueError("source image is invalid") from error
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_hash:
        raise ValueError("source hash mismatch")
    return data, image, digest


def _load_vlm() -> tuple[Any, Any]:
    global _vlm, _processor
    if _vlm is None or _processor is None:
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

        _vlm = Qwen3VLForConditionalGeneration.from_pretrained(
            MODEL_ID,
            dtype="auto",
            device_map="auto",
        )
        _processor = AutoProcessor.from_pretrained(MODEL_ID)
    return _vlm, _processor


def _parse_box(text: str, width: int, height: int) -> list[float]:
    match = re.search(r"\[[^\]]{1,120}\]", text)
    if match is None:
        raise ValueError("localizer did not return a bounding box")
    values = json.loads(match.group(0))
    if not isinstance(values, list) or len(values) != 4:
        raise ValueError("localizer box must contain four coordinates")
    coordinates = [float(value) for value in values]
    scale_x = width / 1024.0
    scale_y = height / 1024.0
    x1, y1, x2, y2 = (
        coordinates[0] * scale_x,
        coordinates[1] * scale_y,
        coordinates[2] * scale_x,
        coordinates[3] * scale_y,
    )
    box = [max(0.0, x1), max(0.0, y1), min(float(width), x2), min(float(height), y2)]
    if box[2] <= box[0] or box[3] <= box[1]:
        raise ValueError("localizer returned an invalid bounding box")
    return box


def _cpu_foreground_mask(image: Any) -> Any:
    """Build a conservative mask for CPU-only development environments."""

    import numpy as np

    pixels = np.asarray(image.convert("RGB"))
    return np.any(pixels < 245, axis=2)


def _mask_box(mask: Any) -> list[float]:
    import numpy as np

    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("cpu fallback could not find foreground pixels")
    return [float(xs.min()), float(ys.min()), float(xs.max() + 1), float(ys.max() + 1)]


def _cpu_fallback_enabled() -> bool:
    import torch

    return not torch.cuda.is_available()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "whiteboard-provider"}


@app.get("/v1/story-video/preflight")
def story_video_preflight() -> dict[str, Any]:
    """Report all local requirements before an expensive story-video run."""

    checks: dict[str, dict[str, str | bool]] = {}

    def record(name: str, ready: bool, detail: str) -> None:
        checks[name] = {"ready": ready, "detail": detail}

    provider = os.getenv("SKETCH2LIFE_TTS_PROVIDER", "edge_tts").strip().lower()
    if provider == "edge_tts":
        try:
            importlib.import_module("edge_tts")
            record("tts", True, "Edge TTS is importable")
        except ImportError:
            record("tts", False, "Install edge-tts in the provider Python environment")
    elif provider == "elevenlabs":
        configured = bool(os.getenv("ELEVENLABS_API_KEY") and os.getenv("ELEVENLABS_VOICE_ID"))
        tts_detail = (
            "ElevenLabs credentials configured"
            if configured else "ElevenLabs API key or voice ID missing"
        )
        record(
            "tts", configured, tts_detail,
        )
    else:
        record("tts", False, "Unsupported TTS provider")

    for executable in ("ffmpeg", "ffprobe"):
        record(executable, shutil.which(executable) is not None, f"{executable} must be on PATH")

    model_id = os.getenv("SKETCH2LIFE_IMAGE_MODEL", "").strip()
    record("image_model", bool(model_id), model_id or "Set SKETCH2LIFE_IMAGE_MODEL")
    try:
        importlib.import_module("accelerate")
        from diffusers import AutoPipelineForImage2Image  # noqa: F401

        record("image_libraries", True, "Diffusers and Accelerate import successfully")
    except Exception as error:  # noqa: BLE001 - report broken optional runtime imports
        detail = f"Image import failed: {type(error).__name__}: {error}"[:240]
        record("image_libraries", False, detail)

    try:
        import torch

        cuda_ready = torch.cuda.is_available()
        record("cuda", cuda_ready, "CUDA GPU available" if cuda_ready else "CUDA GPU unavailable")
    except Exception as error:  # noqa: BLE001 - report broken optional runtime imports
        record("cuda", False, f"PyTorch failed: {type(error).__name__}: {error}"[:240])

    motion_profile = os.getenv(
        "SKETCH2LIFE_STORY_MOTION_PROVIDER", "whiteboard-stroke-v1"
    ).strip()
    if motion_profile == "whiteboard-stroke-v1":
        try:
            importlib.import_module("sketch2life.infrastructure.media.whiteboard_mvp_renderer")
            importlib.import_module("sketch2life.infrastructure.media.whiteboard_stroke_extraction")
            importlib.import_module("imageio")
            record("whiteboard_renderer", True, "Stroke renderer and ImageIO are importable")
        except ImportError:
            record("whiteboard_renderer", False, "Install the backend whiteboard-renderer extra")
    elif motion_profile == "wan2.2-ti2v-5b":
        repo_value = os.getenv("WAN_REPO_DIR", "").strip()
        ckpt_value = os.getenv("WAN_CKPT_DIR", "").strip()
        repo = Path(repo_value).expanduser() if repo_value else None
        ckpt = Path(ckpt_value).expanduser() if ckpt_value else None
        record(
            "wan_code", bool(repo and (repo / "generate.py").is_file()),
            "WAN_REPO_DIR must contain generate.py",
        )
        checkpoint_ready = bool(ckpt and ckpt.is_dir() and any(ckpt.iterdir()))
        record("wan_checkpoint", checkpoint_ready, "WAN_CKPT_DIR must contain model files")
        wan_python = Path(os.getenv("WAN_PYTHON", sys.executable)).expanduser()
        record("wan_python", wan_python.is_file(), "WAN_PYTHON must point to Python")
    else:
        record("motion_profile", False, "Unsupported story motion profile")

    return {
        "ready": all(item["ready"] for item in checks.values()),
        "checks": checks,
        "note": "This checks local dependencies and paths, not model downloads or render quality.",
    }


@app.post("/v1/whiteboard/localize")
def localize(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        _, image, source_hash = _decode_source(payload)
        job_id = str(payload.get("job_id", ""))
        if not job_id:
            raise ValueError("job_id is required")
        if _cpu_fallback_enabled():
            _boxes[job_id] = _mask_box(_cpu_foreground_mask(image))
            return {
                "source_hash": source_hash,
                "regions": [{
                    "region_ref": f"{job_id}:region-001",
                    "confidence": 0.99,
                }],
            }
        vlm, processor = _load_vlm()
        image_path = "/tmp/whiteboard-provider-input.png"
        image.save(image_path)
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {
                    "type": "text",
                    "text": (
                        "Return only one JSON array [x1,y1,x2,y2] in 0-1024 "
                        "coordinates covering the main character."
                    ),
                },
            ],
        }]
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        from qwen_vl_utils import process_vision_info

        image_inputs, video_inputs = process_vision_info(messages)
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            return_tensors="pt",
        ).to(device)

        with torch.inference_mode():
            output = vlm.generate(**inputs, max_new_tokens=64, do_sample=False)
        trimmed = [
            out[len(inp) :]
            for inp, out in zip(inputs.input_ids, output, strict=True)
        ]
        answer = processor.batch_decode(trimmed, skip_special_tokens=True)[0]
        box = _parse_box(answer, image.width, image.height)
        _boxes[job_id] = box
        return {
            "source_hash": source_hash,
            "regions": [{"region_ref": f"{job_id}:region-001", "confidence": 0.9}],
        }
    except (KeyError, TypeError, ValueError, OSError, RuntimeError) as error:
        _LOGGER.exception("whiteboard_localization_failed")
        raise HTTPException(status_code=422, detail="LOCALIZATION_FAILED") from error


@app.post("/v1/whiteboard/segment")
def segment(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        import numpy as np
        import torch
        from PIL import Image

        _, image, source_hash = _decode_source(payload)
        job_id = str(payload.get("job_id", ""))
        box = _boxes.get(job_id)
        if box is None:
            raise ValueError("localization is required before segmentation")
        if _cpu_fallback_enabled():
            buffer = io.BytesIO()
            Image.fromarray(
                _cpu_foreground_mask(image).astype("uint8") * 255
            ).save(buffer, format="PNG")
            return {
                "source_hash": source_hash,
                "masks": [{
                    "mask_ref": f"{job_id}:mask-001",
                    "content_base64": base64.b64encode(buffer.getvalue()).decode("ascii"),
                }],
            }
        global _sam_predictor
        if _sam_predictor is None:
            from sam2.sam2_image_predictor import SAM2ImagePredictor

            _sam_predictor = SAM2ImagePredictor.from_pretrained("facebook/sam2.1-hiera-small")
        image_array = np.asarray(image)
        _sam_predictor.set_image(image_array)
        autocast_context = (
            torch.autocast("cuda", dtype=torch.bfloat16)
            if torch.cuda.is_available()
            else nullcontext()
        )
        with torch.inference_mode(), autocast_context:
            masks, scores, _ = _sam_predictor.predict(box=np.asarray(box), multimask_output=True)
        mask = np.asarray(masks[int(np.argmax(scores))]).squeeze() > 0.5
        buffer = io.BytesIO()
        Image.fromarray(mask.astype(np.uint8) * 255).save(buffer, format="PNG")
        return {
            "source_hash": source_hash,
            "masks": [{
                "mask_ref": f"{job_id}:mask-001",
                "content_base64": base64.b64encode(buffer.getvalue()).decode("ascii"),
            }],
        }
    except (KeyError, TypeError, ValueError, OSError, RuntimeError) as error:
        _LOGGER.exception("whiteboard_segmentation_failed")
        raise HTTPException(status_code=422, detail="SEGMENTATION_FAILED") from error


def _story_video_blocked(contract: str, error_code: str) -> dict[str, Any]:
    """Return an honest typed result until the corresponding model is configured."""

    if contract == "NarrationAssetV1":
        return {
            "contract": contract,
            "version": "1.0",
            "status": "BLOCKED",
            "locale": "vi-VN",
            "voice_model_ref": "unconfigured",
            "segment_timing_seconds": [],
            "error_code": error_code,
        }
    if contract == "IllustrationAssetV1":
        return {
            "contract": contract,
            "version": "1.0",
            "status": "BLOCKED",
            "scene_id": "scene-1",
            "source_image_ref": "unavailable",
            "source_image_sha256": "0" * 64,
            "model_profile_ref": "unconfigured",
            "error_code": error_code,
        }
    if contract == "VideoSceneArtifactV1":
        return {
            "contract": contract,
            "version": "1.0",
            "status": "BLOCKED",
            "scene_id": "scene-1",
            "model_profile_ref": os.getenv(
                "SKETCH2LIFE_STORY_MOTION_PROVIDER", "whiteboard-stroke-v1"
            ),
            "error_code": error_code,
        }
    return {
        "contract": "VideoArtifactV1",
        "version": "1.0",
        "status": "BLOCKED",
        "error_code": error_code,
    }


def _story_video_artifact_root() -> Path:
    root = Path(
        os.getenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", "/tmp/story-video-artifacts")
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _story_video_package_root(request: dict[str, Any]) -> Path:
    """Keep concurrently rendered packages from overwriting each other's scenes."""

    package_hash = str(request.get("package_hash", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", package_hash):
        raise ValueError("PACKAGE_HASH_INVALID")
    root = _story_video_artifact_root() / package_hash
    root.mkdir(parents=True, exist_ok=True)
    return root


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
    if rate <= 0 or frames <= 0:
        raise ValueError("generated audio has no measurable duration")
    return frames / rate


def _elevenlabs_tts(text: str, *, voice_id: str, key: str, model_id: str) -> bytes:
    request = Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": model_id}).encode(),
        headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            data = response.read()
    except HTTPError as error:
        retryable = error.code in {408, 429} or error.code >= 500
        raise RuntimeError(
            "ELEVENLABS_TTS_RETRYABLE" if retryable else "ELEVENLABS_TTS_REJECTED"
        ) from error
    except (TimeoutError, URLError) as error:
        raise RuntimeError("ELEVENLABS_TTS_UNAVAILABLE") from error
    if not data.startswith(b"ID3") and not data.startswith(b"\xff\xfb"):
        raise ValueError("ElevenLabs TTS returned invalid MP3")
    return data


def _edge_tts(text: str, *, voice: str) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temporary:
        output = Path(temporary.name)
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "edge_tts",
                "--voice",
                voice,
                "--text",
                text,
                "--write-media",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            if "No module named edge_tts" in result.stderr:
                raise RuntimeError("EDGE_TTS_NOT_INSTALLED")
            raise RuntimeError("EDGE_TTS_FAILED")
        data = output.read_bytes()
        if not data:
            raise ValueError("Edge TTS returned empty MP3")
        return data
    finally:
        output.unlink(missing_ok=True)


def _mp3_to_wav(mp3: bytes, output: Path) -> None:
    ffmpeg = _require_executable("ffmpeg")
    source = output.with_suffix(".mp3")
    source.write_bytes(mp3)
    subprocess.run(
        [ffmpeg, "-y", "-i", str(source), "-ar", "24000", "-ac", "1", str(output)],
        check=True,
        capture_output=True,
    )


def _concat_wavs(paths: list[Path], output: Path) -> None:
    if not paths:
        raise ValueError("no audio segments to concatenate")
    with wave.open(str(paths[0]), "rb") as first:
        params = first.getparams()
        frames = [first.readframes(first.getnframes())]
    for path in paths[1:]:
        with wave.open(str(path), "rb") as segment:
            # ``nframes`` depends on the sentence duration and is expected to
            # differ between segments. Compare only the actual WAV format.
            if segment.getparams()[:3] != params[:3]:
                raise ValueError("TTS segments have incompatible WAV parameters")
            frames.append(segment.readframes(segment.getnframes()))
    with wave.open(str(output), "wb") as combined:
        combined.setparams(params)
        combined.writeframes(b"".join(frames))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    duration = float(result.stdout.strip())
    if duration <= 0:
        raise ValueError("media duration is not positive")
    return duration


def _ffprobe_streams(path: Path) -> list[dict[str, Any]]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,codec_name,width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    streams = json.loads(result.stdout).get("streams")
    if not isinstance(streams, list):
        raise TypeError("FFPROBE_STREAMS_INVALID")
    return [item for item in streams if isinstance(item, dict)]


def _assembled_streams_ready(streams: list[dict[str, Any]]) -> bool:
    video = [item for item in streams if item.get("codec_type") == "video"]
    audio = [item for item in streams if item.get("codec_type") == "audio"]
    return (
        len(video) == 1
        and len(audio) == 1
        and video[0].get("codec_name") == "h264"
        and audio[0].get("codec_name") == "aac"
        and isinstance(video[0].get("width"), int)
        and video[0]["width"] > 0
        and isinstance(video[0].get("height"), int)
        and video[0]["height"] > 0
    )


def _require_executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name.upper()}_NOT_INSTALLED")
    return executable


@app.post("/v1/story-video/narration")
def story_video_narration(payload: dict[str, Any]) -> dict[str, Any]:
    request = payload.get("request")
    texts = payload.get("texts")
    provider = os.getenv("SKETCH2LIFE_TTS_PROVIDER", "edge_tts").strip().lower()
    eleven_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    eleven_voice = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
    eleven_model = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5").strip()
    edge_voice = os.getenv("EDGE_TTS_VOICE", "vi-VN-HoaiMyNeural").strip()
    if not isinstance(request, dict) or not isinstance(texts, list) or not texts:
        raise HTTPException(status_code=422, detail="NARRATION_REQUEST_INVALID")
    if provider not in {"edge_tts", "elevenlabs"}:
        return _story_video_blocked("NarrationAssetV1", "TTS_PROVIDER_UNSUPPORTED")
    if provider == "elevenlabs" and (not eleven_key or not eleven_voice):
        return _story_video_blocked("NarrationAssetV1", "TTS_RUNTIME_NOT_CONFIGURED")
    if not all(isinstance(text, str) and text.strip() for text in texts):
        raise HTTPException(status_code=422, detail="NARRATION_TEXT_INVALID")
    segment_paths: list[Path] = []
    timings: list[float] = []
    try:
        root = _story_video_package_root(request)
        job_name = re.sub(r"[^A-Za-z0-9_-]", "_", str(request.get("package_id", "story")))
        for index, text in enumerate(texts, 1):
            path = root / f"{job_name}.segment-{index}.wav"
            if provider == "edge_tts":
                audio = _edge_tts(text, voice=edge_voice)
            else:
                audio = _elevenlabs_tts(
                    text,
                    voice_id=eleven_voice,
                    key=eleven_key,
                    model_id=eleven_model,
                )
            _mp3_to_wav(audio, path)
            timings.append(round(_wav_duration(path), 3))
            segment_paths.append(path)
        combined = root / f"{job_name}.wav"
        _concat_wavs(segment_paths, combined)
        data = combined.read_bytes()
        return {
            "contract": "NarrationAssetV1",
            "version": "1.0",
            "status": "READY",
            "audio_ref": str(combined),
            "audio_sha256": hashlib.sha256(data).hexdigest(),
            "duration_seconds": round(sum(timings), 3),
            "locale": str(request.get("locale", "vi-VN")),
            "voice_model_ref": (
                f"edge-tts:{edge_voice}"
                if provider == "edge_tts"
                else f"elevenlabs:{eleven_model}:{eleven_voice}"
            ),
            "segment_timing_seconds": timings,
        }
    except (OSError, RuntimeError, TimeoutError, ValueError, subprocess.SubprocessError) as error:
        _LOGGER.exception("story_video_narration_failed")
        code = (
            str(error)
            if str(error).startswith(("ELEVENLABS_TTS_", "EDGE_TTS_"))
            else "TTS_RENDER_FAILED"
        )
        return _story_video_blocked("NarrationAssetV1", code)


@app.post("/v1/story-video/illustration")
def story_video_illustration(payload: dict[str, Any]) -> dict[str, Any]:
    request = payload.get("request")
    source = payload.get("source_image")
    model_id = os.getenv("SKETCH2LIFE_IMAGE_MODEL", "").strip()
    if not isinstance(request, dict) or not isinstance(source, dict):
        raise HTTPException(status_code=422, detail="ILLUSTRATION_REQUEST_INVALID")
    if not model_id:
        return _story_video_blocked("IllustrationAssetV1", "IMAGE_RUNTIME_NOT_CONFIGURED")
    encoded = source.get("content_base64")
    source_hash = source.get("sha256")
    if not isinstance(encoded, str) or not isinstance(source_hash, str):
        raise HTTPException(status_code=422, detail="SOURCE_IMAGE_INVALID")
    try:
        root = _story_video_package_root(request)
        scene_id = str(request.get("scene_id", "scene-1"))
        if not re.fullmatch(r"scene-[1-9][0-9]*", scene_id):
            raise ValueError("SCENE_ID_INVALID")
        source_path = root / f"{scene_id}.source.png"
        output_path = root / f"{scene_id}.illustration.png"
        source_bytes = base64.b64decode(encoded, validate=True)
        if hashlib.sha256(source_bytes).hexdigest() != source_hash:
            raise ValueError("source image hash mismatch")
        source_path.write_bytes(source_bytes)
        from PIL import Image

        image = Image.open(io.BytesIO(source_bytes)).convert("RGB")
        import torch
        from diffusers import AutoPipelineForImage2Image

        pipe = AutoPipelineForImage2Image.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            variant=os.getenv("SKETCH2LIFE_IMAGE_VARIANT", "fp16"),
        )
        pipe.enable_model_cpu_offload()
        result = pipe(
            prompt=str(request.get("visual_prompt", "")),
            image=image,
            strength=float(os.getenv("SKETCH2LIFE_IMAGE_STRENGTH", "0.35")),
            guidance_scale=float(os.getenv("SKETCH2LIFE_IMAGE_GUIDANCE", "6.0")),
            num_inference_steps=int(os.getenv("SKETCH2LIFE_IMAGE_STEPS", "25")),
        ).images[0]
        result.save(output_path, format="PNG")
        return {
            "contract": "IllustrationAssetV1",
            "version": "1.0",
            "status": "READY",
            "scene_id": scene_id,
            "asset_ref": str(output_path),
            "asset_sha256": _file_sha256(output_path),
            "content_type": "image/png",
            "width": result.width,
            "height": result.height,
            "source_image_ref": str(request.get("source_image_ref", "")),
            "source_image_sha256": source_hash,
            "model_profile_ref": model_id,
        }
    except (ImportError, OSError, RuntimeError, ValueError):
        _LOGGER.exception("story_video_illustration_failed")
        return _story_video_blocked("IllustrationAssetV1", "IMAGE_RENDER_FAILED")


@app.post("/v1/story-video/scene")
def story_video_scene(payload: dict[str, Any]) -> dict[str, Any]:
    request = payload.get("request")
    if not isinstance(request, dict):
        raise HTTPException(status_code=422, detail="SCENE_REQUEST_INVALID")
    profile = str(request.get("model_profile_ref", "whiteboard-stroke-v1"))
    if profile == "whiteboard-stroke-v1":
        return _render_whiteboard_story_scene(request)
    if profile != "wan2.2-ti2v-5b":
        return _story_video_blocked("VideoSceneArtifactV1", "MOTION_PROFILE_UNSUPPORTED")
    repo_value = os.getenv("WAN_REPO_DIR", "").strip()
    ckpt_value = os.getenv("WAN_CKPT_DIR", "").strip()
    repo_dir = Path(repo_value).expanduser() if repo_value else None
    ckpt_dir = Path(ckpt_value).expanduser() if ckpt_value else None
    if (
        not repo_dir or not (repo_dir / "generate.py").is_file()
        or not ckpt_dir or not ckpt_dir.is_dir()
    ):
        return _story_video_blocked("VideoSceneArtifactV1", "WAN_RUNTIME_NOT_CONFIGURED")
    image_path = Path(str(request.get("illustration_ref", "")))
    if not image_path.is_file():
        return _story_video_blocked("VideoSceneArtifactV1", "ILLUSTRATION_ARTIFACT_MISSING")
    scene_id = str(request.get("scene_id", "scene-1"))
    prompt = str(request.get("motion_prompt", ""))
    duration_seconds = float(request.get("duration_seconds", 5.0))
    frame_num = max(5, round(duration_seconds * 24))
    frame_num = 4 * round((frame_num - 1) / 4) + 1
    package_hash = str(request.get("package_hash", ""))
    base_seed = int(package_hash[:12], 16) if len(package_hash) >= 12 else 0
    try:
        if not re.fullmatch(r"scene-[1-9][0-9]*", scene_id):
            raise ValueError("SCENE_ID_INVALID")
        root = _story_video_package_root(request)
        output_path = root / f"{scene_id}.mp4"
        command = [
            os.getenv("WAN_PYTHON", sys.executable),
            str(repo_dir / "generate.py"),
            "--task", "ti2v-5B",
            "--size", os.getenv("WAN_SIZE", "1280*704"),
            "--ckpt_dir", str(ckpt_dir),
            "--offload_model", "True",
            "--convert_model_dtype",
            "--t5_cpu",
            "--frame_num", str(frame_num),
            "--base_seed", str(base_seed),
            "--image", str(image_path),
            "--prompt", prompt,
            "--save_file", str(output_path),
        ]
        subprocess.run(command, cwd=repo_dir, check=True, timeout=1800)
        duration = _ffprobe_duration(output_path)
        return {
            "contract": "VideoSceneArtifactV1",
            "version": "1.0",
            "status": "READY",
            "scene_id": scene_id,
            "silent_clip_ref": str(output_path),
            "silent_clip_sha256": _file_sha256(output_path),
            "duration_seconds": duration,
            "model_profile_ref": "wan2.2-ti2v-5b",
        }
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError):
        _LOGGER.exception("story_video_scene_failed")
        return _story_video_blocked("VideoSceneArtifactV1", "WAN_RENDER_FAILED")


def _render_whiteboard_story_scene(request: dict[str, Any]) -> dict[str, Any]:
    """Turn one generated scene illustration into a narrated whiteboard clip."""

    image_path = Path(str(request.get("illustration_ref", "")))
    if not image_path.is_file():
        return _story_video_blocked("VideoSceneArtifactV1", "ILLUSTRATION_ARTIFACT_MISSING")
    try:
        from sketch2life.infrastructure.media.whiteboard_mvp_renderer import (
            WhiteboardMvpRenderSpec,
            render_stroke_animation,
        )
        from sketch2life.infrastructure.media.whiteboard_stroke_extraction import (
            extract_image_line_art,
        )

        root = _story_video_package_root(request)
        scene_id = str(request.get("scene_id", ""))
        if not re.fullmatch(r"scene-[1-9][0-9]*", scene_id):
            raise ValueError("SCENE_ID_INVALID")
        duration = float(request.get("duration_seconds", 0))
        if not 5.0 <= duration <= 20.0:
            raise ValueError("SCENE_DURATION_INVALID")
        stroke_path = root / f"{scene_id}.strokes.json"
        output_path = root / f"{scene_id}.whiteboard.mp4"
        extract_image_line_art(
            image_path,
            stroke_path,
            source_hash=_file_sha256(image_path),
        )
        result = render_stroke_animation(
            stroke_path,
            output_path,
            spec=WhiteboardMvpRenderSpec(duration_seconds=duration),
        )
        return {
            "contract": "VideoSceneArtifactV1",
            "version": "1.0",
            "status": "READY",
            "scene_id": scene_id,
            "silent_clip_ref": str(output_path),
            "silent_clip_sha256": _file_sha256(output_path),
            "duration_seconds": duration,
            "frame_count": round(result.fps * duration),
            "fps": float(result.fps),
            "model_profile_ref": "whiteboard-stroke-v1",
        }
    except (ImportError, OSError, RuntimeError, ValueError):
        _LOGGER.exception("whiteboard_story_scene_failed")
        return _story_video_blocked("VideoSceneArtifactV1", "WHITEBOARD_RENDER_FAILED")


@app.post("/v1/story-video/assembly")
def story_video_assembly(payload: dict[str, Any]) -> dict[str, Any]:
    request = payload.get("request")
    if not isinstance(request, dict):
        raise HTTPException(status_code=422, detail="ASSEMBLY_REQUEST_INVALID")
    scene_refs = request.get("scene_artifact_refs")
    narration_ref = request.get("narration_ref")
    if not isinstance(scene_refs, list) or not scene_refs or not isinstance(narration_ref, str):
        raise HTTPException(status_code=422, detail="ASSEMBLY_REQUEST_INVALID")
    try:
        ffmpeg = _require_executable("ffmpeg")
        audio_path = Path(narration_ref)
        scene_paths = [Path(str(ref)) for ref in scene_refs]
        if not audio_path.is_file() or any(not path.is_file() for path in scene_paths):
            return _story_video_blocked("VideoArtifactV1", "ASSEMBLY_ARTIFACT_MISSING")
        root = _story_video_package_root(request)
        list_path = root / "scenes.concat.txt"
        output_path = root / "story.final.mp4"
        list_path.write_text(
            "".join(
                f"file '{path.as_posix().replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'\n"
                for path in scene_paths
            ),
            encoding="utf-8",
        )
        subtitle_cues = request.get("subtitle_cues")
        subtitle_path = root / "story.srt"
        filter_args: list[str] = []
        if isinstance(subtitle_cues, list) and subtitle_cues:
            subtitle_path.write_text(_subtitle_srt(subtitle_cues), encoding="utf-8")
            escaped = (
                str(subtitle_path)
                .replace("\\", "/")
                .replace(":", r"\:")
                .replace("'", r"\'")
            )
            style = (
                "FontName=DejaVu Sans,FontSize=12,BorderStyle=1,Outline=1,"
                "Shadow=0,MarginV=24,Alignment=2"
            )
            filter_args = [
                "-vf", f"subtitles='{escaped}':charenc=UTF-8:force_style='{style}'"
            ]
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-i",
                str(audio_path),
                *filter_args,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            timeout=600,
        )
        duration = _ffprobe_duration(output_path)
        if not _assembled_streams_ready(_ffprobe_streams(output_path)):
            return _story_video_blocked("VideoArtifactV1", "ASSEMBLY_STREAM_MISMATCH")
        expected = (
            float(subtitle_cues[-1]["end_seconds"])
            if isinstance(subtitle_cues, list) and subtitle_cues
            else None
        )
        if expected is not None and abs(duration - expected) > 0.6:
            return _story_video_blocked("VideoArtifactV1", "ASSEMBLY_DURATION_MISMATCH")
        return {
            "contract": "VideoArtifactV1",
            "version": "1.0",
            "status": "READY",
            "video_ref": str(output_path),
            "video_sha256": _file_sha256(output_path),
            "duration_seconds": duration,
            "audio_ref": str(audio_path),
            "video_codec": "h264",
            "audio_codec": "aac",
        }
    except (OSError, RuntimeError, subprocess.SubprocessError, TypeError, ValueError):
        _LOGGER.exception("story_video_assembly_failed")
        return _story_video_blocked("VideoArtifactV1", "ASSEMBLY_FAILED")


def _subtitle_srt(cues: list[dict[str, Any]]) -> str:
    """Serialize approved scene narration as UTF-8 SRT cues."""

    def timestamp(seconds: float) -> str:
        millis = max(0, round(seconds * 1000))
        hours, millis = divmod(millis, 3_600_000)
        minutes, millis = divmod(millis, 60_000)
        secs, millis = divmod(millis, 1_000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    blocks: list[str] = []
    for index, cue in enumerate(cues, 1):
        if not isinstance(cue, dict):
            continue
        text = str(cue.get("text", "")).replace("\r", "").strip()
        if not text:
            continue
        blocks.append(
            f"{index}\n{timestamp(float(cue.get('start_seconds', 0)))} --> "
            f"{timestamp(float(cue.get('end_seconds', 0)))}\n{text}\n"
        )
    return "\n".join(blocks)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
