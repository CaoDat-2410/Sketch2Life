"""Minimal Lightning GPU provider for FEAT-018 whiteboard localization/segmentation."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import wave
from contextlib import nullcontext
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape as xml_escape

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
                {"type": "text", "text": "Return only one JSON array [x1,y1,x2,y2] in 0-1024 coordinates covering the main character."},
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
        trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, output)]
        answer = processor.batch_decode(trimmed, skip_special_tokens=True)[0]
        box = _parse_box(answer, image.width, image.height)
        _boxes[job_id] = box
        return {"source_hash": source_hash, "regions": [{"region_ref": f"{job_id}:region-001", "confidence": 0.9}]}
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
            "model_profile_ref": "wan2.2-ti2v-5b",
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


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
    if rate <= 0 or frames <= 0:
        raise ValueError("generated audio has no measurable duration")
    return frames / rate


def _azure_tts(text: str, *, voice: str, key: str, region: str) -> bytes:
    ssml = (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xml:lang="vi-VN">'
        f'<voice name="{xml_escape(voice)}"><prosody rate="0%">'
        f"{xml_escape(text)}"
        "</prosody></voice></speak>"
    ).encode()
    request = Request(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml,
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
            "User-Agent": "Sketch2Life-story-video/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            data = response.read()
    except HTTPError as error:
        retryable = error.code in {408, 429} or error.code >= 500
        raise RuntimeError(
            "AZURE_TTS_RETRYABLE" if retryable else "AZURE_TTS_REJECTED"
        ) from error
    except (TimeoutError, URLError) as error:
        raise RuntimeError("AZURE_TTS_UNAVAILABLE") from error
    if not data.startswith(b"RIFF") or len(data) < 44:
        raise ValueError("Azure TTS returned invalid WAV")
    return data


def _concat_wavs(paths: list[Path], output: Path) -> None:
    if not paths:
        raise ValueError("no audio segments to concatenate")
    with wave.open(str(paths[0]), "rb") as first:
        params = first.getparams()
        frames = [first.readframes(first.getnframes())]
    for path in paths[1:]:
        with wave.open(str(path), "rb") as segment:
            if segment.getparams()[:4] != params[:4]:
                raise ValueError("TTS segments have incompatible WAV parameters")
            frames.append(segment.readframes(segment.getnframes()))
    with wave.open(str(output), "wb") as combined:
        combined.setparams(params)
        combined.writeframes(b"".join(frames))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    duration = float(result.stdout.strip())
    if duration <= 0:
        raise ValueError("media duration is not positive")
    return duration


def _require_executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name.upper()}_NOT_INSTALLED")
    return executable


@app.post("/v1/story-video/narration")
def story_video_narration(payload: dict[str, Any]) -> dict[str, Any]:
    request = payload.get("request")
    texts = payload.get("texts")
    key = os.getenv("AZURE_SPEECH_KEY", "").strip()
    region = os.getenv("AZURE_SPEECH_REGION", "").strip()
    voice = os.getenv("AZURE_TTS_VOICE", "vi-VN-HoaiMyNeural").strip()
    if not isinstance(request, dict) or not isinstance(texts, list) or not texts:
        raise HTTPException(status_code=422, detail="NARRATION_REQUEST_INVALID")
    if not key or not region:
        return _story_video_blocked("NarrationAssetV1", "TTS_RUNTIME_NOT_CONFIGURED")
    if not all(isinstance(text, str) and text.strip() for text in texts):
        raise HTTPException(status_code=422, detail="NARRATION_TEXT_INVALID")
    root = _story_video_artifact_root()
    job_name = re.sub(r"[^A-Za-z0-9_-]", "_", str(request.get("package_id", "story")))
    segment_paths: list[Path] = []
    timings: list[float] = []
    try:
        for index, text in enumerate(texts, 1):
            path = root / f"{job_name}.segment-{index}.wav"
            path.write_bytes(_azure_tts(text, voice=voice, key=key, region=region))
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
            "voice_model_ref": f"azure-speech:{voice}",
            "segment_timing_seconds": timings,
        }
    except (OSError, RuntimeError, TimeoutError, ValueError) as error:
        _LOGGER.exception("story_video_narration_failed")
        code = str(error) if str(error).startswith("AZURE_TTS_") else "TTS_RENDER_FAILED"
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
    root = _story_video_artifact_root()
    scene_id = str(request.get("scene_id", "scene-1"))
    source_path = root / f"{scene_id}.source.png"
    output_path = root / f"{scene_id}.illustration.png"
    try:
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
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        _LOGGER.exception("story_video_illustration_failed")
        return _story_video_blocked("IllustrationAssetV1", str(error) or "IMAGE_RENDER_FAILED")


@app.post("/v1/story-video/scene")
def story_video_scene(payload: dict[str, Any]) -> dict[str, Any]:
    request = payload.get("request")
    if not isinstance(request, dict):
        raise HTTPException(status_code=422, detail="SCENE_REQUEST_INVALID")
    repo_dir = Path(os.getenv("WAN_REPO_DIR", "")).expanduser()
    ckpt_dir = Path(os.getenv("WAN_CKPT_DIR", "")).expanduser()
    if not repo_dir.is_dir() or not ckpt_dir.is_dir():
        return _story_video_blocked("VideoSceneArtifactV1", "WAN_RUNTIME_NOT_CONFIGURED")
    image_path = Path(str(request.get("illustration_ref", "")))
    if not image_path.is_file():
        return _story_video_blocked("VideoSceneArtifactV1", "ILLUSTRATION_ARTIFACT_MISSING")
    root = _story_video_artifact_root()
    scene_id = str(request.get("scene_id", "scene-1"))
    output_path = root / f"{scene_id}.mp4"
    prompt = str(request.get("motion_prompt", ""))
    command = [
        os.getenv("WAN_PYTHON", sys.executable),
        str(repo_dir / "generate.py"),
        "--task", "ti2v-5B",
        "--size", os.getenv("WAN_SIZE", "1280*704"),
        "--ckpt_dir", str(ckpt_dir),
        "--offload_model", "True",
        "--convert_model_dtype",
        "--t5_cpu",
        "--image", str(image_path),
        "--prompt", prompt,
        "--save_file", str(output_path),
    ]
    try:
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
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        _LOGGER.exception("story_video_scene_failed")
        return _story_video_blocked("VideoSceneArtifactV1", str(error) or "WAN_RENDER_FAILED")


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
        root = _story_video_artifact_root()
        list_path = root / f"{request.get('package_id', 'story')}.concat.txt"
        output_path = root / f"{request.get('package_id', 'story')}.final.mp4"
        list_path.write_text("".join(f"file '{path.as_posix()}'\n" for path in scene_paths))
        subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-i", str(audio_path),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(output_path)],
            check=True,
            capture_output=True,
            timeout=600,
        )
        duration = _ffprobe_duration(output_path)
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
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        _LOGGER.exception("story_video_assembly_failed")
        return _story_video_blocked("VideoArtifactV1", str(error) or "ASSEMBLY_FAILED")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
