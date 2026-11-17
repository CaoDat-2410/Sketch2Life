"""Private Modal dev worker for the synthetic Wan2.2 image-to-video candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
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


APP_NAME = "sketch2life-srs23-video-candidate-dev"
MODEL_ID = "Wan-AI/Wan2.2-TI2V-5B"
MODEL_REVISION = "921dbaf3f1674a56f47e83fb80a34bac8a8f203e"
MODEL_LICENSE = "Apache-2.0"
WAN_REPOSITORY = "https://github.com/Wan-Video/Wan2.2.git"
WAN_REPOSITORY_COMMIT = "1ea34ff48f87168174e12956e200b1d908b1c5ff"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
MODEL_DIR = f"{MODEL_MOUNT}/wan2_2_ti2v_5b/{MODEL_REVISION}"
MODEL_MARKER = f"{MODEL_DIR}/sketch2life-model-manifest.json"
INPUT_SCHEMA = "sketch2life.modal.ai-request.v1"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
SYNTHETIC_DRAWING_SHA256 = "4b18777ae70eb429273c1e0ba7189ff005171b9dda88491510d91965aafa07fc"
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
    .apt_install("git", "ffmpeg")
    .run_commands(
        f"git clone --no-checkout {WAN_REPOSITORY} /opt/Wan2.2",
        f"git -C /opt/Wan2.2 fetch --depth 1 origin {WAN_REPOSITORY_COMMIT}",
        f"git -C /opt/Wan2.2 checkout --detach {WAN_REPOSITORY_COMMIT}",
    )
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .uv_pip_install("torch==2.7.1", "torchvision==0.22.1")
    .uv_pip_install(
        "accelerate==1.8.1",
        "diffusers==0.31.0",
        "easydict==1.13",
        "ftfy==6.3.1",
        "huggingface_hub==0.33.4",
        "imageio[ffmpeg]==2.37.0",
        "numpy==1.26.4",
        "opencv-python-headless==4.10.0.84",
        "safetensors==0.6.2",
        "sentencepiece==0.2.0",
        "tokenizers==0.21.2",
        "tqdm==4.67.1",
        "transformers==4.51.3",
    )
    .env(
        {
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "HF_HOME": "/tmp/huggingface",
            "PYTHONPATH": "/opt/Wan2.2",
            "TOKENIZERS_PARALLELISM": "false",
        }
    )
)


@app.function(
    name="download-wan-video-candidate-model",
    image=_download_image,
    volumes={MODEL_MOUNT: model_volume},
    cpu=4.0,
    memory=16_384,
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=7_200,
    retries=0,
)
def download_wan_video_candidate_model() -> dict[str, Any]:
    """Download the public, immutable Wan2.2 TI2V-5B checkpoint to Modal."""

    from huggingface_hub import snapshot_download

    model_volume.reload()
    model_path = Path(MODEL_DIR)
    marker_path = Path(MODEL_MARKER)
    if marker_path.is_file():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if marker.get("model_id") != MODEL_ID or marker.get("revision") != MODEL_REVISION:
            raise RuntimeError("MODAL_MODEL_REVISION_MARKER_MISMATCH")
        _verify_checkpoint(model_path)
        return {"status": "already_present", "model_id": MODEL_ID, "revision": MODEL_REVISION}

    model_path.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=MODEL_ID, revision=MODEL_REVISION, local_dir=str(model_path))
    _verify_checkpoint(model_path)
    marker_path.write_text(
        json.dumps(
            {
                "schema_version": "sketch2life.modal.model-manifest.v1",
                "model_id": MODEL_ID,
                "revision": MODEL_REVISION,
                "license": MODEL_LICENSE,
                "official_runtime_repository": WAN_REPOSITORY,
                "official_runtime_commit": WAN_REPOSITORY_COMMIT,
            },
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
        "runtime_commit": WAN_REPOSITORY_COMMIT,
    }


@app.function(
    name="generate-wan-video-candidate",
    image=_inference_image,
    gpu="L40S",
    cpu=8.0,
    memory=65_536,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume.with_mount_options(read_only=True),
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=1_800,
    retries=0,
)
def generate_wan_video_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate one short synthetic image-to-video candidate for feasibility."""

    request = parse_worker_input(payload, execution_group="l40s-video")
    if request.workload != "video.scene.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    image_path, input_digest = _read_drawing(request)
    if input_digest != SYNTHETIC_DRAWING_SHA256:
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    _verify_marker()

    import torch
    import wan
    from wan.configs import MAX_AREA_CONFIGS, WAN_CONFIGS
    from wan.utils.utils import save_video
    from PIL import Image

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    cfg = WAN_CONFIGS["ti2v-5B"]
    cfg.t5_tokenizer = str(Path(MODEL_DIR) / "google/umt5-xxl")
    pipeline = wan.WanTI2V(
        config=cfg,
        checkpoint_dir=MODEL_DIR,
        device_id=0,
        rank=0,
        t5_cpu=True,
        convert_model_dtype=True,
    )
    prompt = (
        "Animate the same simple butterfly from the supplied child's drawing. "
        "Keep the butterfly's original hand-drawn outline and colors recognizable. "
        "It gently flaps its wings and moves a short distance above a plain garden flower. "
        "One continuous shot, calm movement, no cuts, no text, no extra characters."
    )
    output_path = Path("/tmp/wan_synthetic_candidate.mp4")
    with Image.open(image_path) as source_image:
        image = source_image.convert("RGB")
    with torch.inference_mode():
        frames = pipeline.generate(
            input_prompt=prompt,
            img=image,
            max_area=MAX_AREA_CONFIGS["1280*704"],
            frame_num=17,
            shift=cfg.sample_shift,
            sample_solver="unipc",
            sampling_steps=8,
            guide_scale=cfg.sample_guide_scale,
            seed=20261103,
            offload_model=True,
        )
    save_video(
        tensor=frames[None],
        save_file=str(output_path),
        fps=cfg.sample_fps,
        nrow=1,
        normalize=True,
        value_range=(-1, 1),
    )
    if not output_path.is_file():
        raise RuntimeError("MODAL_VIDEO_OUTPUT_MISSING")
    video_bytes = output_path.read_bytes()
    if len(video_bytes) < 12 or video_bytes[4:8] != b"ftyp" or len(video_bytes) > MAX_OUTPUT_BYTES:
        raise RuntimeError("MODAL_VIDEO_OUTPUT_INVALID")
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "runtime": {"repository": WAN_REPOSITORY, "commit": WAN_REPOSITORY_COMMIT},
        "asset": {
            "content_type": "video/mp4",
            "size_bytes": len(video_bytes),
            "sha256": hashlib.sha256(video_bytes).hexdigest(),
            "duration_seconds": round(17 / cfg.sample_fps, 3),
            "frame_count": 17,
            "fps": cfg.sample_fps,
            "bytes": video_bytes,
        },
        "limitations": [
            "alternative Wan2.2 feasibility candidate; not the SRS LTX-2.5 model",
            "single synthetic sub-second clip with reduced sampling steps",
            "identity consistency, safety, narration, and product quality are not validated",
        ],
    }


def _read_drawing(request: ModalWorkerInputV1) -> tuple[Path, str]:
    root = Path(SCRATCH_MOUNT).resolve()
    attempt_dir = (root / request.attempt_prefix.rstrip("/")).resolve()
    if not attempt_dir.is_relative_to(root):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    manifest_path = (attempt_dir / "input/manifest.json").resolve()
    image_path = (attempt_dir / "input/drawing.png").resolve()
    if not manifest_path.is_relative_to(attempt_dir) or not image_path.is_relative_to(attempt_dir):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    try:
        manifest_bytes = manifest_path.read_bytes()
        image_bytes = image_path.read_bytes()
    except OSError as exc:
        raise WorkerContractError("MODAL_INPUT_ASSET_MISSING") from exc
    digest = hashlib.sha256(image_bytes).hexdigest()
    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID") from exc
    asset = manifest.get("asset") if isinstance(manifest, dict) else None
    if (
        len(manifest_bytes) > MAX_MANIFEST_BYTES
        or hashlib.sha256(manifest_bytes).hexdigest() != request.input_manifest_sha256
        or request.input_bytes != len(manifest_bytes) + len(image_bytes)
        or not isinstance(asset, dict)
        or set(manifest) != {"schema_version", "asset"}
        or manifest.get("schema_version") != INPUT_SCHEMA
        or set(asset) != {"path", "content_type", "size_bytes", "sha256"}
        or asset.get("path") != "input/drawing.png"
        or asset.get("content_type") != "image/png"
        or asset.get("size_bytes") != len(image_bytes)
        or asset.get("sha256") != digest
        or not _SHA256.fullmatch(digest)
        or not image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        raise WorkerContractError("MODAL_INPUT_HASH_MISMATCH")
    return image_path, digest


def _verify_marker() -> None:
    marker_path = Path(MODEL_MARKER)
    if not marker_path.is_file():
        raise RuntimeError("MODAL_MODEL_NOT_READY")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if marker.get("model_id") != MODEL_ID or marker.get("revision") != MODEL_REVISION:
        raise RuntimeError("MODAL_MODEL_REVISION_MISMATCH")


def _verify_checkpoint(path: Path) -> None:
    required_files = (
        "config.json",
        "Wan2.2_VAE.pth",
        "models_t5_umt5-xxl-enc-bf16.pth",
        "diffusion_pytorch_model-00001-of-00003.safetensors",
        "diffusion_pytorch_model-00002-of-00003.safetensors",
        "diffusion_pytorch_model-00003-of-00003.safetensors",
        "diffusion_pytorch_model.safetensors.index.json",
        "google/umt5-xxl/tokenizer.json",
        "google/umt5-xxl/tokenizer_config.json",
        "google/umt5-xxl/spiece.model",
    )
    if any(not (path / filename).is_file() for filename in required_files):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")
