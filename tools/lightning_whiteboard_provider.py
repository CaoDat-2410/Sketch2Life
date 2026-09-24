"""Minimal Lightning GPU provider for FEAT-018 whiteboard localization/segmentation."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
from typing import Any

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Sketch2Life Whiteboard Provider", version="1.0.0")

MODEL_ID = os.getenv("SKETCH2LIFE_VLM_MODEL", "Qwen/Qwen3-VL-2B-Instruct")
_vlm = None
_processor = None
_sam_predictor = None
_boxes: dict[str, list[float]] = {}


def _decode_source(payload: dict[str, Any]) -> tuple[bytes, Any, str]:
    from PIL import Image

    source = payload.get("source_image")
    if not isinstance(source, dict):
        raise ValueError("source_image is required")
    encoded = source.get("content_base64")
    expected_hash = source.get("sha256")
    if not isinstance(encoded, str) or not isinstance(expected_hash, str):
        raise ValueError("source image payload is invalid")
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "whiteboard-provider"}


@app.post("/v1/whiteboard/localize")
def localize(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        _, image, source_hash = _decode_source(payload)
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
        inputs = processor(text=[text], images=image_inputs, videos=video_inputs, return_tensors="pt").to("cuda")
        import torch

        with torch.inference_mode():
            output = vlm.generate(**inputs, max_new_tokens=64, do_sample=False)
        trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, output)]
        answer = processor.batch_decode(trimmed, skip_special_tokens=True)[0]
        box = _parse_box(answer, image.width, image.height)
        job_id = str(payload.get("job_id", ""))
        if not job_id:
            raise ValueError("job_id is required")
        _boxes[job_id] = box
        return {"source_hash": source_hash, "regions": [{"region_ref": f"{job_id}:region-001", "confidence": 0.9}]}
    except (KeyError, TypeError, ValueError, OSError) as error:
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
        global _sam_predictor
        if _sam_predictor is None:
            from sam2.sam2_image_predictor import SAM2ImagePredictor

            _sam_predictor = SAM2ImagePredictor.from_pretrained("facebook/sam2.1-hiera-small")
        image_array = np.asarray(image)
        _sam_predictor.set_image(image_array)
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            masks, scores, _ = _sam_predictor.predict(box=np.asarray(box), multimask_output=True)
        mask = np.asarray(masks[int(np.argmax(scores))]).squeeze() > 0.5
        buffer = io.BytesIO()
        Image.fromarray((mask.astype(np.uint8) * 255)).save(buffer, format="PNG")
        return {
            "source_hash": source_hash,
            "masks": [{
                "mask_ref": f"{job_id}:mask-001",
                "content_base64": base64.b64encode(buffer.getvalue()).decode("ascii"),
            }],
        }
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise HTTPException(status_code=422, detail="SEGMENTATION_FAILED") from error


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
