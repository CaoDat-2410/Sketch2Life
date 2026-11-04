"""Private Modal dev worker for a synthetic FLUX.2 Klein line-guide POC."""

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
    WORKER_OUTPUT_SCHEMA,
    ModalWorkerInputV1,
    WorkerContractError,
    parse_worker_input,
)

APP_NAME = "sketch2life-srs23-flux-image-dev"
MODEL_ID = "black-forest-labs/FLUX.2-klein-4B"
MODEL_REVISION = "e7b7dc27f91deacad38e78976d1f2b499d76a294"
MODEL_LICENSE = "Apache-2.0"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
MODEL_DIR = f"{MODEL_MOUNT}/flux_2_klein_4b/{MODEL_REVISION}"
MODEL_MARKER = f"{MODEL_DIR}/sketch2life-model-manifest.json"
INPUT_SCHEMA = "sketch2life.modal.ai-request.v1"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
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

_contracts_file = _MODULE_DIR / "contracts.py"
_download_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .pip_install("huggingface_hub==0.33.4")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1"})
)
_inference_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .uv_pip_install("torch==2.7.1", "torchvision==0.22.1")
    .uv_pip_install(
        "diffusers==0.42.1",
        "transformers==5.22.1",
        "accelerate==1.15.0",
        "huggingface_hub==1.32.0",
        "Pillow==11.2.1",
        "safetensors==0.8.0",
    )
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_HOME": "/tmp/huggingface"})
)


@app.function(
    name="download-flux-pinned-model",
    image=_download_image,
    volumes={MODEL_MOUNT: model_volume},
    cpu=4.0,
    memory=16_384,
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=3_600,
    retries=0,
)
def download_flux_model() -> dict[str, str]:
    """Download the public immutable FLUX.2 Klein checkpoint into Modal."""

    from huggingface_hub import snapshot_download

    marker = Path(MODEL_MARKER)
    model_path = Path(MODEL_DIR)
    model_volume.reload()
    if marker.is_file():
        record = json.loads(marker.read_text(encoding="utf-8"))
        if record.get("model_id") != MODEL_ID or record.get("revision") != MODEL_REVISION:
            raise RuntimeError("MODAL_MODEL_REVISION_MARKER_MISMATCH")
        _verify_checkpoint(model_path)
        return {"status": "already_present", "model_id": MODEL_ID, "revision": MODEL_REVISION}

    model_path.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=MODEL_ID, revision=MODEL_REVISION, local_dir=str(model_path))
    _verify_checkpoint(model_path)
    marker.write_text(
        json.dumps(
            {
                "schema_version": "sketch2life.modal.model-manifest.v1",
                "model_id": MODEL_ID,
                "revision": MODEL_REVISION,
                "license": MODEL_LICENSE,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    model_volume.commit()
    return {"status": "downloaded", "model_id": MODEL_ID, "revision": MODEL_REVISION}


@app.function(
    name="generate-line-sketch-guide-candidate",
    image=_inference_image,
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
    timeout=900,
    retries=0,
)
def generate_line_sketch_guide_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    """Return one experimental, generic-topic guide image; never product-ready."""

    request = parse_worker_input(payload, execution_group="l4")
    if request.workload != "parent.sketch-guide.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    data = _read_json_asset(request)
    if set(data) != {"topic", "difficulty", "step_count"}:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if data != {"topic": "butterfly", "difficulty": "beginner", "step_count": 3}:
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    _verify_marker()

    import torch
    from diffusers import Flux2KleinPipeline

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    pipeline = Flux2KleinPipeline.from_pretrained(
        MODEL_DIR,
        torch_dtype=torch.bfloat16,
        local_files_only=True,
    ).to("cuda")
    prompt = (
        "Create a clean educational line-art guide on a plain white background. "
        "Show exactly three large, separate panels in left-to-right order teaching how to draw "
        "a simple butterfly: "
        "panel one has only a simple body and head; panel two adds four large wing outlines; "
        "panel three adds a few simple wing details. Thin dark pencil lines, no color, no shading, "
        "no decorative background, no extra objects, no readable text, no labels, no watermark."
    )
    with torch.inference_mode():
        image = pipeline(
            prompt=prompt,
            height=512,
            width=768,
            guidance_scale=1.0,
            num_inference_steps=4,
            generator=torch.Generator(device="cuda").manual_seed(20261103),
        ).images[0]
    import io

    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    image_bytes = output.getvalue()
    if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n") or len(image_bytes) > MAX_OUTPUT_BYTES:
        raise RuntimeError("MODAL_OUTPUT_INVALID")
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "asset": {
            "content_type": "image/png",
            "size_bytes": len(image_bytes),
            "sha256": hashlib.sha256(image_bytes).hexdigest(),
            "width": image.width,
            "height": image.height,
            "bytes": image_bytes,
        },
        "limitations": [
            "single synthetic feasibility sample",
            "step order and child usability are not validated",
            "output is not safety-approved or product-ready",
        ],
    }


@app.function(
    name="generate-approved-lesson-visual-candidate",
    image=_inference_image,
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
    timeout=900,
    retries=0,
)
def generate_approved_lesson_visual_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate one evidence-only 16:9 guide visual from reviewed, generic lesson steps."""

    request = parse_worker_input(payload, execution_group="l4")
    if request.workload != "lesson.visual.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    data = _read_json_asset(request)
    if set(data) != {"schema_version", "plan_revision_ref", "content_hash", "topic", "steps"}:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if (
        data.get("schema_version") != "sketch2life.lesson-visual-input.v1"
        or not isinstance(data.get("plan_revision_ref"), str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", data["plan_revision_ref"])
        or not isinstance(data.get("content_hash"), str)
        or _SHA256.fullmatch(data["content_hash"]) is None
        or not isinstance(data.get("topic"), str)
        or not data["topic"].strip()
        or len(data["topic"]) > 120
        or not isinstance(data.get("steps"), list)
        or not 3 <= len(data["steps"]) <= 5
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    for index, step in enumerate(data["steps"], start=1):
        if (
            not isinstance(step, dict)
            or set(step) != {"step_index", "instruction", "placement"}
            or step.get("step_index") != index
            or any(
                not isinstance(step.get(key), str) or not step[key].strip() or len(step[key]) > 200
                for key in ("instruction", "placement")
            )
        ):
            raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    _verify_marker()

    import torch
    from diffusers import Flux2KleinPipeline

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    pipeline = Flux2KleinPipeline.from_pretrained(
        MODEL_DIR,
        torch_dtype=torch.bfloat16,
        local_files_only=True,
    ).to("cuda")
    panels = " | ".join(
        f"panel {step['step_index']}: {step['instruction']}; placement: {step['placement']}"
        for step in data["steps"]
    )
    prompt = (
        "Create one landscape 16:9 teaching visual on a clean white background. "
        f"Show exactly {len(data['steps'])} separate equal panels in left-to-right order, "
        f"progressively teaching a simple line drawing of {data['topic']}. "
        f"Follow the reviewed step sequence exactly: {panels}. "
        "Use simple dark pencil-like outlines, no color fill, no shading, no background scene, "
        "no people, no child, no extra objects, no readable text, no numbers, no watermark. "
        "This is a generic illustration guide, not a child's artwork."
    )
    with torch.inference_mode():
        image = pipeline(
            prompt=prompt,
            height=432,
            width=768,
            guidance_scale=1.0,
            num_inference_steps=4,
            generator=torch.Generator(device="cuda").manual_seed(20261104),
        ).images[0]
    import io

    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    image_bytes = output.getvalue()
    if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n") or len(image_bytes) > MAX_OUTPUT_BYTES:
        raise RuntimeError("MODAL_OUTPUT_INVALID")
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "plan_revision_ref": data["plan_revision_ref"],
        "content_hash": data["content_hash"],
        "status": "DRAFT",
        "asset": {
            "content_type": "image/png",
            "size_bytes": len(image_bytes),
            "sha256": hashlib.sha256(image_bytes).hexdigest(),
            "width": image.width,
            "height": image.height,
            "bytes": image_bytes,
        },
        "review_required": True,
        "limitations": [
            "one synthetic illustration candidate; no ordered-step quality evaluation",
            "not safety-approved, not registered as a product asset, and not publishable",
        ],
    }


def _read_json_asset(request: ModalWorkerInputV1) -> dict[str, Any]:
    root = Path(SCRATCH_MOUNT).resolve()
    attempt_dir = (root / request.attempt_prefix.rstrip("/")).resolve()
    if not attempt_dir.is_relative_to(root):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    manifest_path = (attempt_dir / "input/manifest.json").resolve()
    asset_path = (attempt_dir / "input/request.json").resolve()
    if not manifest_path.is_relative_to(attempt_dir) or not asset_path.is_relative_to(attempt_dir):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    try:
        manifest_bytes = manifest_path.read_bytes()
        request_bytes = asset_path.read_bytes()
    except OSError as exc:
        raise WorkerContractError("MODAL_INPUT_ASSET_MISSING") from exc
    if (
        len(manifest_bytes) > MAX_MANIFEST_BYTES
        or hashlib.sha256(manifest_bytes).hexdigest() != request.input_manifest_sha256
        or request.input_bytes != len(manifest_bytes) + len(request_bytes)
    ):
        raise WorkerContractError("MODAL_INPUT_HASH_MISMATCH")
    try:
        manifest = json.loads(manifest_bytes)
        data = json.loads(request_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID") from exc
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "asset"}:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    asset = manifest["asset"]
    if (
        manifest.get("schema_version") != INPUT_SCHEMA
        or not isinstance(asset, dict)
        or set(asset) != {"path", "content_type", "size_bytes", "sha256"}
        or asset.get("path") != "input/request.json"
        or asset.get("content_type") != "application/json"
        or asset.get("size_bytes") != len(request_bytes)
        or asset.get("sha256") != hashlib.sha256(request_bytes).hexdigest()
    ):
        raise WorkerContractError("MODAL_INPUT_HASH_MISMATCH")
    if not isinstance(data, dict):
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    return data


def _verify_marker() -> None:
    path = Path(MODEL_MARKER)
    if not path.is_file():
        raise RuntimeError("MODAL_MODEL_NOT_READY")
    marker = json.loads(path.read_text(encoding="utf-8"))
    if marker.get("model_id") != MODEL_ID or marker.get("revision") != MODEL_REVISION:
        raise RuntimeError("MODAL_MODEL_REVISION_MISMATCH")


def _verify_checkpoint(path: Path) -> None:
    if (
        not (path / "model_index.json").is_file()
        or not (path / "flux-2-klein-4b.safetensors").is_file()
    ):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")
