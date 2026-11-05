"""Private Modal L4 POC for SRS v2.3 drawing.analyze."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import modal

_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from contracts import (  # noqa: E402
    MAX_STAGED_INPUT_BYTES,
    WORKER_OUTPUT_SCHEMA,
    ModalWorkerInputV1,
    WorkerContractError,
    parse_worker_input,
)

APP_NAME = "sketch2life-srs23-drawing-vlm-dev"
_CONTRACTS_FILE = _MODULE_DIR / "contracts.py"
MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"
MODEL_REVISION = "cc594898137f460bfe9f0759e9844b3ce807cfb5"
MODEL_LICENSE = "Apache-2.0"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
MODEL_DIR = f"{MODEL_MOUNT}/qwen2_5_vl_7b_instruct/{MODEL_REVISION}"
MODEL_MANIFEST = f"{MODEL_DIR}/sketch2life-model-manifest.json"
DRAWING_INPUT_SCHEMA = "sketch2life.modal.drawing-input.v1"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_IMAGE_PIXELS = 2_000_000
MAX_PROCESSOR_PIXELS = 512 * 512
MAX_OUTPUT_UNITS = 128
_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(
    MODEL_VOLUME_NAME,
    environment_name="dev",
    create_if_missing=True,
    version=2,
)
scratch_volume = modal.Volume.from_name(
    SCRATCH_VOLUME_NAME,
    environment_name="dev",
    create_if_missing=True,
    version=2,
)

download_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_CONTRACTS_FILE), "/root/contracts.py", copy=True)
    .pip_install("huggingface_hub==0.33.4")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1"})
)
inference_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_CONTRACTS_FILE), "/root/contracts.py", copy=True)
    .uv_pip_install("torch==2.7.1", "torchvision==0.22.1")
    .uv_pip_install(
        "transformers==4.53.0",
        "accelerate==1.8.1",
        "huggingface_hub==0.33.4",
        "Pillow==11.2.1",
    )
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_HOME": "/tmp/huggingface"})
)


@app.function(
    name="download-pinned-model",
    image=download_image,
    volumes={MODEL_MOUNT: model_volume},
    cpu=4.0,
    memory=16_384,
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=3_600,
    retries=0,
)
def download_pinned_model() -> dict[str, Any]:
    """Download only the public immutable checkpoint into the dev weights Volume."""

    from huggingface_hub import snapshot_download

    model_path = Path(MODEL_DIR)
    marker_path = Path(MODEL_MANIFEST)
    model_volume.reload()
    if marker_path.is_file():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if marker.get("model_id") == MODEL_ID and marker.get("revision") == MODEL_REVISION:
            _ensure_checkpoint_files(model_path)
            return {
                "status": "already_present",
                "model_id": MODEL_ID,
                "revision": MODEL_REVISION,
                "license": MODEL_LICENSE,
            }
        raise RuntimeError("MODAL_MODEL_REVISION_MARKER_MISMATCH")

    model_path.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=str(model_path),
    )
    _ensure_checkpoint_files(model_path)
    marker_path.write_text(
        json.dumps(
            {
                "schema_version": "sketch2life.modal.model-manifest.v1",
                "model_id": MODEL_ID,
                "revision": MODEL_REVISION,
                "license": MODEL_LICENSE,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    model_volume.commit()
    return {
        "status": "downloaded",
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "license": MODEL_LICENSE,
    }


@app.function(
    name="analyze-drawing",
    image=inference_image,
    gpu="L4",
    cpu=4.0,
    memory=32_768,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume.with_mount_options(read_only=True),
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=600,
    retries=0,
)
def analyze_drawing(payload: dict[str, Any]) -> dict[str, Any]:
    """Inspect one staged drawing and return a candidate requiring adult confirmation."""

    request = parse_worker_input(payload, execution_group="l4")
    if request.workload != "drawing.analyze":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")

    image_path, image_sha256 = _verify_staged_input(request)
    model, processor = _load_model()

    from PIL import Image

    with Image.open(image_path) as opened:
        drawing = opened.convert("RGB")

    prompt = (
        "Hãy quan sát bức vẽ đường nét đen trên nền trắng. Chỉ mô tả chủ thể có thể nhận ra "
        "và những đặc điểm nhìn thấy trực tiếp; không suy đoán tuổi, danh tính, cảm xúc hay "
        "hoàn cảnh của người vẽ. Trả về đúng một JSON object, không markdown, theo mẫu: "
        '{"candidate_subject":"...","visible_features":["...","..."]}. '
        'Nếu không nhận ra chủ thể, ghi candidate_subject là "chưa xác định".'
    )
    messages = [
        {
            "role": "user",
            "content": [{"type": "image"}, {"type": "text", "text": prompt}],
        }
    ]
    rendered_prompt = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = processor(
        text=[rendered_prompt],
        images=[drawing],
        return_tensors="pt",
        padding=True,
    ).to(model.device)

    import torch

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            do_sample=False,
            max_new_tokens=MAX_OUTPUT_UNITS,
        )
    answer_ids = output_ids[0][inputs.input_ids.shape[-1] :]
    answer = processor.decode(
        answer_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    ).strip()
    candidate = _parse_candidate(answer)

    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": "drawing.analyze",
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "input_sha256": image_sha256,
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "result": {
            **candidate,
            "decision": "NEEDS_ADULT_CONFIRMATION",
            "adult_confirmation_required": True,
        },
    }


def _ensure_checkpoint_files(model_path: Path) -> None:
    required = (
        "config.json",
        "model.safetensors.index.json",
        "model-00001-of-00005.safetensors",
        "model-00002-of-00005.safetensors",
        "model-00003-of-00005.safetensors",
        "model-00004-of-00005.safetensors",
        "model-00005-of-00005.safetensors",
        "preprocessor_config.json",
        "tokenizer.json",
    )
    if not all((model_path / name).is_file() for name in required):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")


def _verify_staged_input(request: ModalWorkerInputV1) -> tuple[Path, str]:
    scratch_root = Path(SCRATCH_MOUNT).resolve()
    attempt_dir = (scratch_root / request.attempt_prefix.rstrip("/")).resolve()
    if not attempt_dir.is_relative_to(scratch_root):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")

    input_dir = attempt_dir / "input"
    manifest_path = (input_dir / "manifest.json").resolve()
    image_path = (input_dir / "drawing.png").resolve()
    if not manifest_path.is_relative_to(attempt_dir) or not image_path.is_relative_to(attempt_dir):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    try:
        if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            raise WorkerContractError("MODAL_INPUT_LIMIT_EXCEEDED")
    except OSError as exc:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_MISSING") from exc
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_MISSING") from exc
    if len(manifest_bytes) > MAX_MANIFEST_BYTES:
        raise WorkerContractError("MODAL_INPUT_LIMIT_EXCEEDED")
    if hashlib.sha256(manifest_bytes).hexdigest() != request.input_manifest_sha256:
        raise WorkerContractError("MODAL_INPUT_HASH_MISMATCH")

    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID") from exc
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "asset"}:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if manifest.get("schema_version") != DRAWING_INPUT_SCHEMA:
        raise WorkerContractError("MODAL_SCHEMA_UNSUPPORTED")
    asset = manifest.get("asset")
    if not isinstance(asset, dict) or set(asset) != {
        "path",
        "content_type",
        "size_bytes",
        "sha256",
    }:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if asset.get("path") != "input/drawing.png" or asset.get("content_type") != "image/png":
        raise WorkerContractError("MODAL_INPUT_TYPE_NOT_ALLOWED")
    asset_size = asset.get("size_bytes")
    asset_sha256 = asset.get("sha256")
    if (
        isinstance(asset_size, bool)
        or not isinstance(asset_size, int)
        or asset_size < 0
        or asset_size > MAX_STAGED_INPUT_BYTES
        or not isinstance(asset_sha256, str)
        or _SHA256.fullmatch(asset_sha256) is None
    ):
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")

    try:
        if image_path.stat().st_size != asset_size:
            raise WorkerContractError("MODAL_INPUT_SIZE_MISMATCH")
        image_bytes = image_path.read_bytes()
    except OSError as exc:
        raise WorkerContractError("MODAL_INPUT_ASSET_MISSING") from exc
    image_sha256 = hashlib.sha256(image_bytes).hexdigest()
    if (
        not image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        or asset_sha256 != image_sha256
        or asset_size != len(image_bytes)
        or request.input_bytes != len(image_bytes) + len(manifest_bytes)
        or request.input_bytes > MAX_STAGED_INPUT_BYTES
    ):
        raise WorkerContractError("MODAL_INPUT_HASH_MISMATCH")

    from PIL import Image, UnidentifiedImageError

    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
    try:
        with Image.open(image_path) as opened:
            if opened.format != "PNG" or opened.width * opened.height > MAX_IMAGE_PIXELS:
                raise WorkerContractError("MODAL_INPUT_IMAGE_INVALID")
            opened.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise WorkerContractError("MODAL_INPUT_IMAGE_INVALID") from exc
    return image_path, image_sha256


def _load_model() -> tuple[Any, Any]:
    global _CACHED_MODEL, _CACHED_PROCESSOR
    if _CACHED_MODEL is not None and _CACHED_PROCESSOR is not None:
        return _CACHED_MODEL, _CACHED_PROCESSOR

    marker_path = Path(MODEL_MANIFEST)
    if not marker_path.is_file():
        raise RuntimeError("MODAL_MODEL_NOT_READY")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if marker.get("model_id") != MODEL_ID or marker.get("revision") != MODEL_REVISION:
        raise RuntimeError("MODAL_MODEL_REVISION_MISMATCH")
    model_path = Path(MODEL_DIR)
    _ensure_checkpoint_files(model_path)

    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    _CACHED_PROCESSOR = AutoProcessor.from_pretrained(
        str(model_path),
        local_files_only=True,
        min_pixels=224 * 224,
        max_pixels=MAX_PROCESSOR_PIXELS,
    )
    _CACHED_MODEL = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(model_path),
        torch_dtype=torch.float16,
        device_map="auto",
        attn_implementation="sdpa",
        low_cpu_mem_usage=True,
        local_files_only=True,
    )
    _CACHED_MODEL.eval()
    return _CACHED_MODEL, _CACHED_PROCESSOR


def _parse_candidate(answer: str) -> dict[str, Any]:
    try:
        parsed = json.loads(answer)
    except json.JSONDecodeError as exc:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID") from exc
    if not isinstance(parsed, dict) or set(parsed) != {
        "candidate_subject",
        "visible_features",
    }:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    subject = parsed.get("candidate_subject")
    features = parsed.get("visible_features")
    if (
        not isinstance(subject, str)
        or not subject.strip()
        or len(subject) > 100
        or not isinstance(features, list)
        or not 1 <= len(features) <= 4
        or any(
            not isinstance(item, str) or not item.strip() or len(item) > 160 for item in features
        )
    ):
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    return {
        "candidate_subject": subject.strip(),
        "visible_features": [item.strip() for item in features],
    }


_CACHED_MODEL: Any | None = None
_CACHED_PROCESSOR: Any | None = None
