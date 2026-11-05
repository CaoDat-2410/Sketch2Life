"""Private, synthetic-only SAM 2.1 image-mask feasibility worker."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

import modal

_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from contracts import (
    MAX_STAGED_INPUT_BYTES,
    WORKER_OUTPUT_SCHEMA,
    ModalWorkerInputV1,
    WorkerContractError,
    parse_worker_input,
)

APP_NAME = "sketch2life-srs23-drawing-segment-dev"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
SAM2_REPOSITORY_COMMIT = "2b90b9f5ceec907a1c18123530e92e794ad901a4"
SAM2_CHECKPOINT_URL = (
    "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt"
)
SAM2_CHECKPOINT_MAX_BYTES = 512 * 1024 * 1024
SAM2_GPU_CANDIDATES = ("L40S", "L4", "A10")
SAM2_CHECKPOINT_DIR = Path(MODEL_MOUNT) / "sam2.1_hiera_small" / SAM2_REPOSITORY_COMMIT
SAM2_CHECKPOINT = SAM2_CHECKPOINT_DIR / "sam2.1_hiera_small.pt"
SAM2_MARKER = SAM2_CHECKPOINT_DIR / "sketch2life-model-manifest.json"
MAX_IMAGE_PIXELS = 2_000_000
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
_SHA256 = re.compile(r"\A[a-f0-9]{64}\Z")

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

_contracts_file = _MODULE_DIR / "contracts.py"
_download_image = modal.Image.debian_slim(python_version="3.11").add_local_file(
    str(_contracts_file), "/root/contracts.py", copy=True
)
_inference_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .uv_pip_install("torch==2.7.1", "torchvision==0.22.1")
    .env({"SAM2_BUILD_CUDA": "0", "HF_HUB_DISABLE_TELEMETRY": "1"})
    .uv_pip_install(f"git+https://github.com/facebookresearch/sam2.git@{SAM2_REPOSITORY_COMMIT}")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_HOME": "/tmp/huggingface"})
)


@app.function(
    name="download-sam2-hiera-small-checkpoint",
    image=_download_image,
    volumes={MODEL_MOUNT: model_volume},
    cpu=2.0,
    memory=8_192,
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=600,
    retries=0,
)
def download_sam2_checkpoint() -> dict[str, Any]:
    """Download one bounded public checkpoint to a new, isolated Volume path."""

    model_volume.reload()
    if SAM2_MARKER.is_file() and SAM2_CHECKPOINT.is_file():
        marker = json.loads(SAM2_MARKER.read_text(encoding="utf-8"))
        digest, size = _hash_file(SAM2_CHECKPOINT)
        if (
            marker.get("repository_commit") != SAM2_REPOSITORY_COMMIT
            or marker.get("checkpoint_sha256") != digest
            or marker.get("checkpoint_size_bytes") != size
        ):
            raise RuntimeError("SAM2_CHECKPOINT_MARKER_MISMATCH")
        return {"status": "already_present", **marker}
    if SAM2_CHECKPOINT.exists() or SAM2_MARKER.exists():
        raise RuntimeError("SAM2_CHECKPOINT_UNATTESTED_PARTIAL_STATE")

    SAM2_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        SAM2_CHECKPOINT_URL,
        headers={"User-Agent": "Sketch2Life-FEAT-063-synthetic-poc/1"},
    )
    digest = hashlib.sha256()
    total = 0
    with (
        urllib.request.urlopen(request, timeout=60) as response,
        SAM2_CHECKPOINT.open("wb") as target,
    ):
        advertised = response.headers.get("Content-Length")
        if advertised is not None and int(advertised) > SAM2_CHECKPOINT_MAX_BYTES:
            raise RuntimeError("SAM2_CHECKPOINT_SIZE_LIMIT_EXCEEDED")
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > SAM2_CHECKPOINT_MAX_BYTES:
                raise RuntimeError("SAM2_CHECKPOINT_SIZE_LIMIT_EXCEEDED")
            digest.update(chunk)
            target.write(chunk)
    if total < 1:
        raise RuntimeError("SAM2_CHECKPOINT_EMPTY")

    marker = {
        "schema_version": "sketch2life.modal.model-manifest.v1",
        "model_id": "facebookresearch/sam2.1-hiera-small",
        "repository_commit": SAM2_REPOSITORY_COMMIT,
        "checkpoint_url": SAM2_CHECKPOINT_URL,
        "checkpoint_sha256": digest.hexdigest(),
        "checkpoint_size_bytes": total,
        "license": "Apache-2.0",
        "cuda_extension": "disabled for this feasibility POC",
    }
    SAM2_MARKER.write_text(
        json.dumps(marker, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    model_volume.commit()
    return {"status": "downloaded", **marker}


@app.function(
    name="segment-synthetic-drawing-candidate",
    image=_inference_image,
    gpu=list(SAM2_GPU_CANDIDATES),
    cpu=4.0,
    memory=24_576,
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
def segment_synthetic_drawing_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    """Create one point-prompted mask; never replace or mutate the source image."""

    request = parse_worker_input(payload, execution_group="l4")
    if request.workload != "drawing.segment":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    image_path, source_sha256 = _read_drawing(request)
    marker = _verify_checkpoint()

    import numpy as np
    import torch
    from PIL import Image
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    with Image.open(image_path) as opened:
        rgb = opened.convert("RGB")
    width, height = rgb.size
    if width * height > MAX_IMAGE_PIXELS:
        raise WorkerContractError("MODAL_INPUT_IMAGE_INVALID")

    model = build_sam2(
        "configs/sam2.1/sam2.1_hiera_s.yaml",
        str(SAM2_CHECKPOINT),
        device="cuda",
        apply_postprocessing=False,
    )
    predictor = SAM2ImagePredictor(model)
    predictor.set_image(np.asarray(rgb))
    point_coords = np.array([[width * 0.5, height * 0.53]], dtype=np.float32)
    point_labels = np.array([1], dtype=np.int32)
    with torch.inference_mode():
        masks, scores, _ = predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=True,
        )
    selected_index = int(np.argmax(scores))
    mask = np.asarray(masks[selected_index], dtype=np.bool_)
    mask_bytes_buffer = __import__("io").BytesIO()
    Image.fromarray(mask.astype(np.uint8) * 255, mode="L").save(
        mask_bytes_buffer,
        format="PNG",
        optimize=True,
    )
    mask_bytes = mask_bytes_buffer.getvalue()
    if not mask_bytes.startswith(b"\x89PNG\r\n\x1a\n") or len(mask_bytes) > MAX_OUTPUT_BYTES:
        raise RuntimeError("SAM2_OUTPUT_INVALID")

    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "input_sha256": source_sha256,
        "model": {
            "id": "facebookresearch/sam2.1-hiera-small",
            "revision": SAM2_REPOSITORY_COMMIT,
            "checkpoint_sha256": marker["checkpoint_sha256"],
        },
        "result": {
            "status": "DRAFT",
            "width": width,
            "height": height,
            "point_prompt_normalized": [0.5, 0.53],
            "mask_score": float(scores[selected_index]),
            "mask_area_ratio": float(mask.mean()),
            "source_artifact_unchanged": True,
            "review_required": True,
        },
        "asset": {
            "content_type": "image/png",
            "size_bytes": len(mask_bytes),
            "sha256": hashlib.sha256(mask_bytes).hexdigest(),
            "width": width,
            "height": height,
            "bytes": mask_bytes,
        },
    }


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def _verify_checkpoint() -> dict[str, Any]:
    if not SAM2_MARKER.is_file() or not SAM2_CHECKPOINT.is_file():
        raise RuntimeError("SAM2_CHECKPOINT_MISSING")
    marker = json.loads(SAM2_MARKER.read_text(encoding="utf-8"))
    digest, size = _hash_file(SAM2_CHECKPOINT)
    if (
        marker.get("repository_commit") != SAM2_REPOSITORY_COMMIT
        or marker.get("checkpoint_sha256") != digest
        or marker.get("checkpoint_size_bytes") != size
        or not 0 < size <= SAM2_CHECKPOINT_MAX_BYTES
    ):
        raise RuntimeError("SAM2_CHECKPOINT_INTEGRITY_INVALID")
    return marker


def _read_drawing(request: ModalWorkerInputV1) -> tuple[Path, str]:
    scratch_root = Path(SCRATCH_MOUNT).resolve()
    attempt_dir = (scratch_root / request.attempt_prefix.rstrip("/")).resolve()
    if not attempt_dir.is_relative_to(scratch_root):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    input_dir = attempt_dir / "input"
    manifest_path = (input_dir / "manifest.json").resolve()
    drawing_path = (input_dir / "drawing.png").resolve()
    if not manifest_path.is_relative_to(attempt_dir) or not drawing_path.is_relative_to(
        attempt_dir
    ):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    try:
        manifest_bytes = manifest_path.read_bytes()
        drawing_bytes = drawing_path.read_bytes()
    except OSError as exc:
        raise WorkerContractError("MODAL_INPUT_ASSET_MISSING") from exc
    if hashlib.sha256(manifest_bytes).hexdigest() != request.input_manifest_sha256:
        raise WorkerContractError("MODAL_INPUT_HASH_MISMATCH")
    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID") from exc
    asset = manifest.get("asset") if isinstance(manifest, dict) else None
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"schema_version", "asset"}
        or manifest.get("schema_version") != "sketch2life.modal.drawing-input.v1"
        or not isinstance(asset, dict)
        or set(asset) != {"path", "content_type", "size_bytes", "sha256"}
        or asset.get("path") != "input/drawing.png"
        or asset.get("content_type") != "image/png"
        or asset.get("size_bytes") != len(drawing_bytes)
        or request.input_bytes != len(manifest_bytes) + len(drawing_bytes)
        or request.input_bytes > MAX_STAGED_INPUT_BYTES
    ):
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    source_sha256 = hashlib.sha256(drawing_bytes).hexdigest()
    if (
        not drawing_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        or asset.get("sha256") != source_sha256
        or not isinstance(asset.get("sha256"), str)
        or _SHA256.fullmatch(asset["sha256"]) is None
    ):
        raise WorkerContractError("MODAL_INPUT_HASH_MISMATCH")
    try:
        from PIL import Image, UnidentifiedImageError

        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
        with Image.open(drawing_path) as opened:
            if opened.format != "PNG" or opened.width * opened.height > MAX_IMAGE_PIXELS:
                raise WorkerContractError("MODAL_INPUT_IMAGE_INVALID")
            opened.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise WorkerContractError("MODAL_INPUT_IMAGE_INVALID") from exc
    return drawing_path, source_sha256
