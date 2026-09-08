"""Fixture-only Lightning Studio provider server.

This process is intentionally separate from the Sketch2Life backend.  It loads
the approved tech-stack models in a Lightning Studio and exposes only the
versioned P2 ASR/VLM HTTP boundary consumed by the local backend.
"""

from __future__ import annotations

import base64
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException

ASR_MODEL = os.getenv("SKETCH2LIFE_ASR_MODEL", "large-v3-turbo")
ASR_ROOT = Path(os.getenv("SKETCH2LIFE_ASR_ROOT", "models/asr"))
VLM_ROOT = Path(
    os.getenv("SKETCH2LIFE_VLM_ROOT", "models/vlm/qwen3-vl-8b-instruct")
)
MAX_INPUT_BYTES = 5_000_000
EXPECTED_AUTH = os.getenv("LIGHTNING_DEV_AUTH", "").strip()

app = FastAPI(title="Sketch2Life Lightning Dev Provider")

_asr_model: Any = None
_vlm_model: Any = None
_vlm_processor: Any = None


def _authorize(authorization: str | None) -> None:
    if EXPECTED_AUTH and authorization != f"Bearer {EXPECTED_AUTH}":
        raise HTTPException(status_code=401, detail="unauthorized")


def _decode_artifact(payload: dict[str, Any], key: str) -> tuple[bytes, str]:
    artifact = payload.get(key)
    if not isinstance(artifact, dict):
        raise HTTPException(status_code=400, detail="malformed artifact envelope")
    encoded = artifact.get("content_base64")
    digest = artifact.get("sha256")
    if not isinstance(encoded, str) or not isinstance(digest, str):
        raise HTTPException(status_code=400, detail="malformed artifact envelope")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="malformed artifact content") from None
    if len(data) > MAX_INPUT_BYTES:
        raise HTTPException(status_code=413, detail="artifact exceeds input limit")
    return data, digest


def _image_bytes_for_vlm(data: bytes) -> bytes:
    if not data.lstrip().startswith(b"<svg"):
        return data
    try:
        import cairosvg
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="SVG fixture requires cairosvg in the provider environment",
        ) from exc
    try:
        return cairosvg.svg2png(bytestring=data)
    except (OSError, RuntimeError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="invalid SVG fixture") from None

def _load_asr() -> Any:
    global _asr_model
    if _asr_model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("faster-whisper is not installed") from exc
        _asr_model = WhisperModel(
            ASR_MODEL,
            device="cuda",
            compute_type="float16",
            download_root=str(ASR_ROOT),
        )
    return _asr_model


def _load_vlm() -> tuple[Any, Any]:
    global _vlm_model, _vlm_processor
    if _vlm_model is None or _vlm_processor is None:
        try:
            import torch
            from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        except ImportError as exc:
            raise RuntimeError("Qwen3-VL Transformers dependencies are not installed") from exc
        _vlm_model = Qwen3VLForConditionalGeneration.from_pretrained(
            str(VLM_ROOT),
            dtype=torch.bfloat16,
            device_map="auto",
        )
        _vlm_processor = AutoProcessor.from_pretrained(str(VLM_ROOT))
    return _vlm_model, _vlm_processor


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "lightning-dev-provider",
        "asr_model": ASR_MODEL,
        "asr_loaded": _asr_model is not None,
        "vlm_model": "Qwen/Qwen3-VL-8B-Instruct",
        "vlm_loaded": _vlm_model is not None,
    }


@app.post("/v1/asr")
def asr(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, object]:
    _authorize(authorization)
    audio, _ = _decode_artifact(payload, "source_audio")
    model = _load_asr()
    with tempfile.NamedTemporaryFile(suffix=".wav") as handle:
        handle.write(audio)
        handle.flush()
        segments, info = model.transcribe(handle.name, beam_size=5)
        materialized = list(segments)
    mapped = [
        {
            "start_seconds": float(segment.start),
            "end_seconds": float(segment.end),
            "text": str(segment.text).strip(),
            "confidence": max(0.0, min(1.0, 1.0 - float(segment.no_speech_prob))),
        }
        for segment in materialized
    ]
    transcript = " ".join(item["text"] for item in mapped).strip()
    no_speech = (
        sum(float(segment.no_speech_prob) for segment in materialized) / len(materialized)
        if materialized
        else None
    )
    avg_logprob = (
        sum(float(segment.avg_logprob) for segment in materialized) / len(materialized)
        if materialized
        else None
    )
    return {
        "transcript": transcript,
        "language": getattr(info, "language", None),
        "language_confidence": getattr(info, "language_probability", None),
        "segments": mapped,
        "quality": {
            "no_speech_probability": no_speech,
            "average_log_probability": avg_logprob,
            "segment_count": len(mapped),
        },
    }


def _json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)
    match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
    if match is None:
        raise ValueError("vision model did not return a JSON object")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise TypeError("vision model output is not an object")
    return value


@app.post("/v1/vision")
def vision(
    payload: dict[str, Any], authorization: str | None = Header(default=None)
) -> dict[str, object]:
    _authorize(authorization)
    image_bytes, _ = _decode_artifact(payload, "source_image")
    image_bytes = _image_bytes_for_vlm(image_bytes)
    model, processor = _load_vlm()
    prompt = (
        "Analyze this synthetic child drawing. Return ONLY JSON with keys "
        "entities, actions, relations, themes, ambiguous_regions, uncertainty. "
        "Each entity/action/theme has label and confidence. Each relation has "
        "subject, predicate, object, confidence. Each ambiguous region has label, "
        "description, confidence. Do not infer personality, diagnosis, emotion, "
        "mental state, or psychological traits."
    )
    with tempfile.NamedTemporaryFile(suffix=".png") as handle:
        handle.write(image_bytes)
        handle.flush()
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": handle.name},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)
        generated = model.generate(**inputs, max_new_tokens=256)
        trimmed = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(inputs.input_ids, generated)
        ]
        text = processor.batch_decode(
            trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]
    result = _json_object(text)
    prohibited = {
        "personality",
        "diagnosis",
        "mental_state",
        "psychological_profile",
        "psychological_inference",
        "emotion_inference",
    }
    if any(str(key).lower() in prohibited for key in result):
        raise HTTPException(status_code=502, detail="vision output contains prohibited fields")
    return {
        "entities": result.get("entities", []),
        "actions": result.get("actions", []),
        "relations": result.get("relations", []),
        "themes": result.get("themes", []),
        "ambiguous_regions": result.get("ambiguous_regions", []),
        "uncertainty": result.get("uncertainty", 1.0),
    }
