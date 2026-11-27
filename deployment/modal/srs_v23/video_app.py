"""Dev-only LTX-2.5 image-to-video workers on Modal L40S.

The scene worker produces a private *scene candidate*. The silent-story worker
also assembles a complete script-driven MP4 candidate, but does not admit
product quota, run child-safety review, publish an asset, or make a result
playable. Those decisions remain owned by the backend.
"""

from __future__ import annotations

import functools
import gc
import hashlib
import inspect
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

import modal

_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from contracts import (
    WorkerContractError,
    parse_worker_input,
)
import render_options
import scene_cache
from ltx_speed import (
    FAST,
    ProfileSwitch,
    PromptCache,
    render_with_fallback,
    warm_up_prompts,
)
from keyframe_plan import (
    KeyframePlanError,
    scene_conditioning,
    validate_keyframe_plan,
)
from scene_prepare_host import (
    PrepWorker,
    PrepWorkerError,
    child_environment,
    read_prepare_request,
)
from story_visual_plan import (
    KEYFRAME_PROMPT_TEMPLATE_VERSION,
    PROMPT_TEMPLATE_VERSION,
    StoryVisualPlanError,
    canonical_sha256,
    compile_keyframe_scene_prompt,
    compile_scene_prompt,
    plan_scene_frames,
    validate_story_visual_plan,
)
from worker_observability import (
    observed_worker,
    refresh_worker_volume,
    worker_phase,
    worker_stage,
)

APP_NAME = "sketch2life-srs23-dev-video"
MODEL_ID = "Lightricks/LTX-2.5"
MODEL_REVISION = "49b093a39c19169a8a81721dcc541e07e945232f"
LTX_CODE_TAG = "v1.6.2"
PINNED_LTX_CODE_COMMIT = "f0f2f8607189c78a72420b2b63cb1975b5eca179"
MODEL_LICENSE_ID = "ltx-2.x-community-license"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
HF_CREDENTIAL_RESOURCE_NAME = "huggingface-secret"
HF_AUTH_ENV_KEY = "HF_TOKEN"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
MODEL_ROOT = f"{MODEL_MOUNT}/ltx-2.5/{MODEL_REVISION}"
# FEAT-087: SAM 2.1 hiera-small box prompts (same pinned checkpoint as drawing_segment_app.py).
SAM2_REPOSITORY_COMMIT = "2b90b9f5ceec907a1c18123530e92e794ad901a4"
SAM2_CHECKPOINT = Path(MODEL_MOUNT) / "sam2.1_hiera_small" / SAM2_REPOSITORY_COMMIT / "sam2.1_hiera_small.pt"
SAM2_MODEL_CONFIG = "configs/sam2.1/sam2.1_hiera_s.yaml"
# FEAT-094 phase 2: scene preparation runs in this container, in its own environment (ADR-0026).
PREPARE_PYTHON = "/opt/prep-venv/bin/python"
PREPARE_SERVER = "/root/scene_prepare_server.py"
PREPARE_TIMEOUT_SECONDS = 600
PLATE_MODEL_ID = "black-forest-labs/flux-3-image-klein"
PLATE_MODEL_REVISION = "09561231f44e41381c461caf53d5452005a60ac9"
MODEL_MARKER = f"{MODEL_ROOT}/sketch2life-model-manifest.json"

INPUT_SCHEMA = "sketch2life.modal.video-scene-input.v1"
OUTPUT_SCHEMA = "sketch2life.modal.video-scene-output.v1"
STORY_INPUT_SCHEMA = "sketch2life.modal.silent-story-video-input.v2"
STORY_OUTPUT_SCHEMA = "sketch2life.modal.silent-story-video-output.v2"
MODEL_PROFILE = "ltx25-distilled-bf16-fp8-cpu-offload-l40s-v1"
FPS = 24.0
OUTPUT_WIDTH = 1280
OUTPUT_HEIGHT = 720
MODEL_FRAME_HEIGHT = 768
MAX_MANIFEST_BYTES = 64 * 1024
MAX_DRAWING_BYTES = 20 * 1024 * 1024
MAX_OUTPUT_BYTES = 256 * 1024 * 1024
MAX_DRAWING_PIXELS = 2_000_000
MAX_VIDEO_SECONDS = 20.0
_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")
_OPAQUE_ID = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z")
_SCENE_ID = re.compile(r"\Ascene-([1-9][0-9]?)\Z")
_ALLOWED_DRAWING_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}

MODEL_FILES = {
    "diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors": "transformer",
    "text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors": "text_encoder",
    "vae/ltx-2.5-video-vae-bf16.safetensors": "video_vae",
    "vae/ltx-2.5-audio-vae-bf16.safetensors": "audio_vae",
    "latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors": "spatial_upsampler",
}
# FEAT-098: staged on its own (``download-ltx25-conv-vae``) and read only when the ``conv_vae`` option is on.
CONV_VAE_FILE = "vae/ltx-2.5-video-vae-conv-bf16.safetensors"
# FEAT-098: speed options of this container (set in the image; none when the setting is absent).
_OPTIONS = render_options.parse_options(os.environ.get(render_options.OPTIONS_ENV, ""))

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(
    MODEL_VOLUME_NAME,
    environment_name="dev",
    version=2,
)
scratch_volume = modal.Volume.from_name(
    SCRATCH_VOLUME_NAME,
    environment_name="dev",
    version=2,
)

_contracts_file = _MODULE_DIR / "contracts.py"
_observability_file = _MODULE_DIR / "worker_observability.py"
_story_visual_plan_file = _MODULE_DIR / "story_visual_plan.py"
_lock_dir = _MODULE_DIR / "locks"
_RUNTIME_MODULES = (
    "ltx_speed.py",
    "render_options.py",
    "scene_cache.py",
    "scene_prepare.py",
    "scene_prepare_host.py",
    "scene_prepare_server.py",
)
_keyframe_modules = (
    "keyframe_compositor.py",
    "keyframe_metrics.py",
    "keyframe_plan.py",
    "keyframe_render.py",
    "sam_masks.py",
    "story_staging_worker.py",
)
_worker_base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .add_local_file(
        str(_observability_file), "/root/worker_observability.py", copy=True
    )
    .add_local_file(
        str(_story_visual_plan_file), "/root/story_visual_plan.py", copy=True
    )
)
for _module_name in _keyframe_modules:
    _worker_base_image = _worker_base_image.add_local_file(
        str(_MODULE_DIR / _module_name), f"/root/{_module_name}", copy=True
    )
_download_image = _worker_base_image.uv_pip_install("huggingface_hub==1.32.0").env(
    {"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1"}
)

# The official inference code is installed from a pinned Lightricks release tag.
# Use the official split-checkpoint pipeline, not Diffusers, ComfyUI, Wan or a
# third-party LTX wrapper. The backend remains the only dispatcher.
# FEAT-094: both Python environments install from committed locks, so a rebuild brings the same packages.
_inference_image = (
    _worker_base_image.apt_install("ffmpeg", "git")
    .pip_install("uv==0.9.8")
    .add_local_file(str(_lock_dir / "ltx-2.5-v1.6.2.uv.lock"), "/opt/locks/ltx.uv.lock", copy=True)
    .add_local_file(str(_lock_dir / "scene-prepare.txt"), "/opt/locks/scene-prepare.txt", copy=True)
    .run_commands(
        "git clone --filter=blob:none --depth 1 --branch v1.6.2 "
        "https://github.com/Lightricks/LTX-2.git /opt/LTX-2",
        "cp /opt/locks/ltx.uv.lock /opt/LTX-2/uv.lock",
        "cd /opt/LTX-2 && uv sync --frozen --package ltx-pipelines",
        # FEAT-098: natten is the fastest video decoder on this GPU generation. The extra belongs to ltx-core and is in
        # the committed lock; --inexact keeps what the pipelines package installed.
        "cd /opt/LTX-2 && uv sync --frozen --package ltx-core --extra natten --inexact",
        "/opt/LTX-2/.venv/bin/python -c 'import natten'",
        "cd /opt/LTX-2 && git rev-parse HEAD > /opt/LTX-2/LTX_CODE_COMMIT "
        "&& sha256sum uv.lock | cut -d ' ' -f 1 > /opt/LTX-2/LTX_UV_LOCK_SHA256",
        f'test "$(cat /opt/LTX-2/LTX_CODE_COMMIT)" = "{PINNED_LTX_CODE_COMMIT}"',
        # FEAT-087: SAM 2.1 for keyframe masks, installed without touching the pinned torch stack.
        "SAM2_BUILD_CUDA=0 uv pip install --python /opt/LTX-2/.venv/bin/python --no-deps "
        f"git+https://github.com/facebookresearch/sam2.git@{SAM2_REPOSITORY_COMMIT}",
        "uv pip install --python /opt/LTX-2/.venv/bin/python hydra-core==1.3.2 iopath==0.1.10",
        # Scene preparation (FLUX background plate and SAM masks) has its own interpreter.
        "uv venv /opt/prep-venv --python /usr/local/bin/python3.12",
        "uv pip install --python /opt/prep-venv/bin/python -r /opt/locks/scene-prepare.txt",
        "SAM2_BUILD_CUDA=0 uv pip install --python /opt/prep-venv/bin/python --no-deps "
        f"git+https://github.com/facebookresearch/sam2.git@{SAM2_REPOSITORY_COMMIT}",
    )
    # FEAT-094: Debian packages are not locked; refuse an ffmpeg series other than the one the checks ran with.
    .run_commands("ffmpeg -version | head -1 | grep -q 'ffmpeg version 7[.]1[.]'")
    .env(
        {
            "PATH": "/opt/LTX-2/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "VIRTUAL_ENV": "/opt/LTX-2/.venv",
            "PYTHONPATH": "/opt/LTX-2/.venv/lib/python3.12/site-packages",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "HF_HOME": f"{MODEL_MOUNT}/huggingface-cache",
            "HF_HUB_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            # FEAT-094: the fast profile runs close to the memory limit.
            "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
            # FEAT-098: the speed options named at deploy time, else the accepted ones ("none": all off).
            render_options.OPTIONS_ENV: os.environ.get(render_options.OPTIONS_ENV, render_options.ACCEPTED),
        }
    )
)


def _with_runtime_modules(image: modal.Image) -> modal.Image:
    """Mount the runtime modules as the last layers, so that editing them never rebuilds a dependency layer."""

    for name in _RUNTIME_MODULES:
        image = image.add_local_file(str(_MODULE_DIR / name), f"/root/{name}")
    return image


# The model mount is read-only, so the child keeps its small Hugging Face files in the container.
_PREPARATION = PrepWorker(
    [PREPARE_PYTHON, PREPARE_SERVER], env=child_environment({**os.environ, "HF_HOME": "/tmp/prepare-hf"})
)


def _with_scene_preparation(render: Any) -> Any:
    """Route preparation calls to their own handler; one container serves both, one call at a time."""

    @functools.wraps(render)
    def entry(payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("prepare_warmup") is True:
            return _warm_up_scene_preparation()
        if payload.get("workload") == "video.scene.prepare":
            return _prepare_scene_job(payload)
        return render(payload)

    return entry


def _start_preparation() -> None:
    """Make room for the preparation child. The checkpoint check comes first: it reloads the model volume, which
    fails once another process holds files on it."""

    if _PREPARATION.running:
        return
    try:
        _require_model_ready()
    except Exception as error:  # noqa: BLE001 - preparation does not need the renderer checkpoint
        print(json.dumps({"event": "scene_model_check_failed", "error_type": type(error).__name__}), flush=True)
    _unload_pipeline()


def _warm_up_scene_preparation() -> dict[str, Any]:
    """Load the plate and mask models and start reading the renderer checkpoint; no job data is read.

    A loaded renderer is left alone (FEAT-098): the pictures may already be waiting in the cache, and unloading it
    would cost the next scene the whole model load again.
    """

    if _PIPELINE is not None:
        return {"warmed": False, "loaded": []}
    _start_preparation()
    try:
        loaded = _PREPARATION.request("warmup", {}, timeout=PREPARE_TIMEOUT_SECONDS).get("loaded", [])
    except PrepWorkerError as error:
        print(json.dumps({"event": "scene_preparation_warm_up_failed", "code": str(error)}), flush=True)
        return {"warmed": False, "loaded": []}
    _start_checkpoint_prefetch()
    return {"warmed": True, "loaded": loaded}


@observed_worker(
    workload="video.scene.prepare",
    model_id=PLATE_MODEL_ID,
    model_revision=PLATE_MODEL_REVISION,
    gpu_class="L40S",
    timeout_seconds=1_800,
)
def _prepare_scene_job(payload: dict[str, Any]) -> dict[str, Any]:
    """FEAT-093: one scene keyframe, the child's subjects over a crayon background plate (paper fallback)."""

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l40s-video")
    refresh_worker_volume(scratch_volume)
    attempt_root = _safe_attempt_root(request.attempt_prefix)
    with worker_phase("input_manifest_read"):
        try:
            drawing, fields = read_prepare_request(
                attempt_root, manifest_sha256=request.input_manifest_sha256, input_bytes=request.input_bytes
            )
        except ValueError as error:
            raise WorkerContractError(str(error)) from None
    cache_root = Path(SCRATCH_MOUNT) / "sketch2life" / "dev" / "prepare-cache"
    cache_key = scene_cache.cache_key(request.input_manifest_sha256, PLATE_MODEL_REVISION)
    kept = scene_cache.lookup(cache_root, cache_key, now=time.time())
    if kept is not None:
        # FEAT-098: prepared while the adult reviewed the script; the renderer stays loaded.
        keyframe, prepared = kept
        print(json.dumps({"event": "scene_prepared_from_cache"}), flush=True)
    else:
        with tempfile.TemporaryDirectory(prefix="sketch2life-prepare-") as directory:
            (Path(directory) / "drawing.png").write_bytes(drawing)
            with worker_phase("scene_prepare"):
                _start_preparation()
                outcome = _PREPARATION.request(
                    "prepare", {"directory": directory, "request": fields}, timeout=PREPARE_TIMEOUT_SECONDS
                )
            keyframe = (Path(directory) / "keyframe.png").read_bytes()
        if not keyframe or len(keyframe) > MAX_DRAWING_BYTES:
            raise RuntimeError("MODAL_OUTPUT_LIMIT_EXCEEDED")
        prepared = {"background": outcome["background"], "reason": outcome["reason"]}
        if prepared["background"] == "AI":  # a paper fallback gets another try next time
            _keep_prepared_scene(cache_root, cache_key, keyframe, prepared)
    return {
        "schema_version": "sketch2life.modal.worker-output.v1",
        "workload": "video.scene.prepare",
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": {"id": PLATE_MODEL_ID, "revision": PLATE_MODEL_REVISION},
        "asset": {
            "content_type": "image/png",
            "size_bytes": len(keyframe),
            "sha256": hashlib.sha256(keyframe).hexdigest(),
            "bytes": keyframe,
        },
        "prepare": prepared,
    }


def _keep_prepared_scene(root: Path, key: str, keyframe: bytes, prepared: dict[str, Any]) -> None:
    """Failing to keep a picture only costs preparing it again."""

    try:
        scene_cache.store(root, key, keyframe, prepared, now=time.time())
        scratch_volume.commit()
    except Exception as error:  # noqa: BLE001
        print(json.dumps({"event": "scene_cache_store_failed", "error_type": type(error).__name__}), flush=True)


@app.function(
    name="health",
    image=_with_runtime_modules(_worker_base_image),
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=15,
)
def health() -> dict[str, Any]:
    """CPU liveness only; this never claims that weights or a GPU are warm."""

    return {
        "status": "ok",
        "app": APP_NAME,
        "workload": "video.scene.generate",
        "inference_ready": False,
        "readiness_note": "CPU liveness does not load or warm a GPU model.",
    }


@app.function(
    name="check-ltx25-model-access",
    image=_with_runtime_modules(_download_image),
    secrets=[
        modal.Secret.from_name(
            HF_CREDENTIAL_RESOURCE_NAME,
            required_keys=[HF_AUTH_ENV_KEY],
        )
    ],
    cpu=1.0,
    memory=2_048,
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=120,
    retries=0,
)
def check_ltx25_model_access() -> dict[str, Any]:
    """Check gated model access and dry-run the pinned file download without weights."""

    from huggingface_hub import HfApi, snapshot_download
    from huggingface_hub.errors import GatedRepoError, HfHubHTTPError

    token = os.environ.get(HF_AUTH_ENV_KEY)
    if not token:
        return {"status": "blocked", "reason_code": "HF_TOKEN_MISSING"}
    try:
        api = HfApi()
        api.whoami(token=token)
    except HfHubHTTPError as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        return {
            "status": "blocked",
            "reason_code": "HF_TOKEN_REJECTED"
            if status_code == 401
            else "HF_TOKEN_VALIDATION_FAILED",
            "http_status": status_code if isinstance(status_code, int) else None,
        }
    try:
        info = api.model_info(
            repo_id=MODEL_ID,
            revision=MODEL_REVISION,
            token=token,
            files_metadata=False,
        )
    except GatedRepoError:
        return {"status": "blocked", "reason_code": "HF_GATED_ACCESS_NOT_GRANTED"}
    except HfHubHTTPError as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        return {
            "status": "blocked",
            "reason_code": "HF_MODEL_ACCESS_CHECK_FAILED",
            "http_status": status_code if isinstance(status_code, int) else None,
        }
    if info.sha != MODEL_REVISION:
        return {"status": "blocked", "reason_code": "HF_MODEL_REVISION_MISMATCH"}
    try:
        with worker_phase("pinned_checkpoint_download_preflight"):
            download_plan = snapshot_download(
                repo_id=MODEL_ID,
                revision=MODEL_REVISION,
                token=token,
                allow_patterns=list(MODEL_FILES) + ["LICENSE*", "README.md"],
                dry_run=True,
            )
    except GatedRepoError as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        return {
            "status": "blocked",
            "reason_code": "HF_TOKEN_REJECTED"
            if status_code == 401
            else "HF_GATED_FILE_ACCESS_NOT_GRANTED",
            "http_status": status_code if isinstance(status_code, int) else None,
        }
    except HfHubHTTPError as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        return {
            "status": "blocked",
            "reason_code": "HF_MODEL_DOWNLOAD_PREFLIGHT_FAILED",
            "http_status": status_code if isinstance(status_code, int) else None,
            "error_type": type(exc).__name__,
        }
    except (OSError, ValueError) as exc:
        return {
            "status": "blocked",
            "reason_code": "HF_MODEL_DOWNLOAD_PREFLIGHT_FAILED",
            "error_type": type(exc).__name__,
        }

    if not download_plan:
        return {"status": "blocked", "reason_code": "HF_CHECKPOINT_FILE_SET_EMPTY"}
    planned_bytes = sum(
        value
        for item in download_plan
        if isinstance((value := getattr(item, "file_size", None)), int)
    )
    return {
        "status": "ready_to_download",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "planned_file_count": len(download_plan),
        "planned_bytes": planned_bytes,
        "license_id": MODEL_LICENSE_ID,
        "terms_review": "NOT_ASSESSED_BY_ENGINEERING",
    }


@app.function(
    name="download-ltx25-pinned-model",
    image=_with_runtime_modules(_download_image),
    secrets=[
        modal.Secret.from_name(
            HF_CREDENTIAL_RESOURCE_NAME,
            required_keys=[HF_AUTH_ENV_KEY],
        )
    ],
    volumes={MODEL_MOUNT: model_volume},
    cpu=4.0,
    memory=16_384,
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=7_200,
    retries=0,
)
def download_ltx25_pinned_model() -> dict[str, Any]:
    """Download only the pinned DistilledPipeline checkpoint pack to existing Volume v2."""

    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import GatedRepoError, HfHubHTTPError

    token = os.environ.get(HF_AUTH_ENV_KEY)
    if not token:
        raise RuntimeError("HF_TOKEN_MISSING")
    root = Path(MODEL_ROOT)
    marker_path = Path(MODEL_MARKER)
    with worker_phase("model_volume_reload"):
        model_volume.reload()
    with worker_phase("existing_checkpoint_check"):
        current = _read_model_manifest(marker_path)
        if current is not None and _verify_model_manifest(root, current):
            return {
                "status": "already_staged",
                "model_id": MODEL_ID,
                "model_revision": MODEL_REVISION,
                "file_count": len(MODEL_FILES),
                "total_bytes": current["total_bytes"],
            }

    root.mkdir(parents=True, exist_ok=True)
    with worker_phase("pinned_checkpoint_download"):
        try:
            snapshot_download(
                repo_id=MODEL_ID,
                revision=MODEL_REVISION,
                local_dir=str(root),
                token=token,
                allow_patterns=list(MODEL_FILES) + ["LICENSE*", "README.md"],
            )
        except GatedRepoError as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            return {
                "status": "blocked",
                "reason_code": "HF_TOKEN_REJECTED"
                if status_code == 401
                else "HF_GATED_FILE_ACCESS_NOT_GRANTED",
                "http_status": status_code if isinstance(status_code, int) else None,
            }
        except HfHubHTTPError as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            return {
                "status": "failed",
                "reason_code": "HF_MODEL_DOWNLOAD_HTTP_ERROR",
                "http_status": status_code if isinstance(status_code, int) else None,
                "error_type": type(exc).__name__,
            }
        except (OSError, ValueError) as exc:
            # Keep diagnostics actionable without retaining URLs, headers or tokens.
            return {
                "status": "failed",
                "reason_code": "HF_MODEL_DOWNLOAD_IO_ERROR"
                if isinstance(exc, OSError)
                else "HF_MODEL_DOWNLOAD_VALUE_ERROR",
                "error_type": type(exc).__name__,
            }
    with worker_phase("checkpoint_integrity_manifest"):
        entries: dict[str, dict[str, Any]] = {}
        for relative_path in MODEL_FILES:
            model_path = _safe_model_path(root, relative_path)
            if not model_path.is_file() or model_path.is_symlink():
                raise RuntimeError("LTX_CHECKPOINT_FILE_MISSING")
            size = model_path.stat().st_size
            if size <= 0:
                raise RuntimeError("LTX_CHECKPOINT_FILE_EMPTY")
            entries[relative_path] = {
                "size_bytes": size,
                "sha256": _sha256_file(model_path),
            }
        total_bytes = sum(item["size_bytes"] for item in entries.values())
        manifest = {
            "schema_version": "sketch2life.modal.ltx-model-manifest.v1",
            "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "code_tag": LTX_CODE_TAG,
            "license_id": MODEL_LICENSE_ID,
            "license_review": "NOT_ASSESSED_BY_ENGINEERING",
            "pipeline": "DistilledPipeline",
            "files": entries,
            "total_bytes": total_bytes,
        }
        marker_path.write_text(
            json.dumps(
                manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            ),
            encoding="utf-8",
        )
    with worker_phase("model_volume_commit"):
        model_volume.commit()
    return {
        "status": "downloaded",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "file_count": len(entries),
        "total_bytes": total_bytes,
    }


@app.function(
    name="download-ltx25-conv-vae",
    image=_with_runtime_modules(_download_image),
    secrets=[
        modal.Secret.from_name(
            HF_CREDENTIAL_RESOURCE_NAME,
            required_keys=[HF_AUTH_ENV_KEY],
        )
    ],
    volumes={MODEL_MOUNT: model_volume},
    cpu=2.0,
    memory=4_096,
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=1_800,
    retries=0,
)
def download_ltx25_conv_vae() -> dict[str, Any]:
    """Stage the optional convolution video VAE of the pinned model revision (FEAT-098)."""

    from huggingface_hub import hf_hub_download

    token = os.environ.get(HF_AUTH_ENV_KEY)
    if not token:
        raise RuntimeError("HF_TOKEN_MISSING")
    model_volume.reload()
    path = _safe_model_path(Path(MODEL_ROOT), CONV_VAE_FILE)
    status = "already_staged"
    if not path.is_file():
        try:
            hf_hub_download(
                repo_id=MODEL_ID,
                revision=MODEL_REVISION,
                filename=CONV_VAE_FILE,
                local_dir=MODEL_ROOT,
                token=token,
            )
        except Exception as error:  # noqa: BLE001 - keep URLs, headers and tokens out of the log
            return {"status": "failed", "reason_code": "HF_MODEL_DOWNLOAD_FAILED", "error_type": type(error).__name__}
        model_volume.commit()
        status = "downloaded"
    return {
        "status": status,
        "model_revision": MODEL_REVISION,
        "file": CONV_VAE_FILE,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


@app.function(
    name="ltx25-model-status",
    image=_with_runtime_modules(_download_image),
    volumes={MODEL_MOUNT: model_volume.with_mount_options(read_only=True)},
    cpu=1.0,
    memory=2_048,
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=30,
    retries=0,
)
def ltx25_model_status() -> dict[str, Any]:
    """Report staged checkpoint state; only an inference call loads the GPU model."""

    model_volume.reload()
    manifest = _read_model_manifest(Path(MODEL_MARKER))
    staged = manifest is not None and _verify_model_manifest(Path(MODEL_ROOT), manifest)
    return {
        "status": "staged" if staged else "not_staged",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_profile": MODEL_PROFILE,
        "gpu_model_loaded": False,
        "inference_ready": False,
        "total_bytes": manifest.get("total_bytes") if staged and manifest else None,
    }


@app.function(
    name="diagnose-ltx25-runtime",
    image=_with_runtime_modules(_inference_image),
    volumes={MODEL_MOUNT: model_volume.with_mount_options(read_only=True)},
    cpu=4.0,
    memory=16_384,
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=600,
    retries=0,
)
@observed_worker(
    workload="video.runtime.diagnose",
    model_id=MODEL_ID,
    model_revision=MODEL_REVISION,
    gpu_class="cpu",
    timeout_seconds=600,
)
def diagnose_ltx25_runtime() -> dict[str, Any]:
    """Check pinned runtime and quantization API on CPU without loading weights/GPU."""

    with worker_phase("checkpoint_manifest_validation"):
        manifest = _require_model_ready()
    with worker_phase("pinned_runtime_revision_validation"):
        code_commit = _read_ltx_code_commit()
        dependency_lock_sha256 = _read_ltx_dependency_lock_sha256()
        if code_commit != PINNED_LTX_CODE_COMMIT:
            raise RuntimeError("LTX_CODE_REVISION_MISMATCH")
        if dependency_lock_sha256 is None:
            raise RuntimeError("LTX_DEPENDENCY_LOCK_INVALID")
    with worker_phase("quantization_api_validation"):
        from ltx_core.quantization.fp8_cast import build_policy as build_fp8_cast_policy
        from ltx_pipelines import DistilledPipeline

        transformer_path = Path(MODEL_ROOT) / next(
            name for name, part in MODEL_FILES.items() if part == "transformer"
        )
        policy = build_fp8_cast_policy(str(transformer_path))
        pipeline_parameters = inspect.signature(DistilledPipeline).parameters
        expected_parameters = {
            "model_paths",
            "spatial_upsampler_path",
            "loras",
            "quantization",
            "offload_mode",
        }
        if not expected_parameters.issubset(pipeline_parameters):
            raise RuntimeError("LTX_PIPELINE_CONSTRUCTOR_API_MISMATCH")
    return {
        "status": "runtime_api_ready",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_profile": MODEL_PROFILE,
        "code_commit": code_commit,
        "dependency_lock_sha256": dependency_lock_sha256,
        "checkpoint_manifest_sha256": _sha256_file(Path(MODEL_MARKER)),
        "checkpoint_bytes": manifest["total_bytes"],
        "quantization_policy_type": type(policy).__name__,
        "pipeline_api_parameters": sorted(pipeline_parameters),
        "gpu_model_loaded": False,
        "gpu_inference_run": False,
    }


@app.function(
    name="generate-video-scene",
    image=_with_runtime_modules(_inference_image),
    gpu="L40S",
    cpu=8.0,
    memory=65_536,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume,
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=300,
    timeout=1_800,
    retries=0,
)
@_with_scene_preparation
@observed_worker(
    workload="video.scene.generate",
    model_id=MODEL_ID,
    model_revision=MODEL_REVISION,
    gpu_class="L40S",
    timeout_seconds=1_800,
)
def generate_video_scene(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate one isolated image-conditioned scene candidate with LTX-2.5."""

    if payload.get("warmup") is True:
        try:
            prompts = warm_up_prompts(payload)
        except ValueError as error:
            raise WorkerContractError(str(error)) from None
        return _warm_up_scene_renderer(prompts or [])
    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l40s-video")
    worker_stage("workload_gate")
    if request.workload != "video.scene.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")

    refresh_worker_volume(scratch_volume)
    attempt_root = _safe_attempt_root(request.attempt_prefix)
    with worker_phase("input_manifest_read"):
        manifest_bytes = _read_bounded(
            _safe_attempt_file(attempt_root, request.input_manifest_ref),
            MAX_MANIFEST_BYTES,
            "VIDEO_INPUT_MANIFEST_LIMIT_EXCEEDED",
        )
        if hashlib.sha256(manifest_bytes).hexdigest() != request.input_manifest_sha256:
            raise WorkerContractError("VIDEO_INPUT_MANIFEST_HASH_MISMATCH")
        manifest = _parse_scene_input(manifest_bytes)
    with tempfile.TemporaryDirectory(prefix="sketch2life-ltx-scene-") as temp_dir:
        working_dir = Path(temp_dir)
        image_path = working_dir / "drawing.png"
        with worker_phase("drawing_integrity_and_decode"):
            source_size = _prepare_drawing(attempt_root, manifest, image_path)
            if source_size + len(manifest_bytes) != request.input_bytes:
                raise WorkerContractError("VIDEO_INPUT_SIZE_MISMATCH")
        with worker_phase("checkpoint_preflight"):
            model_manifest = _require_model_ready()
        raw_path = working_dir / "scene-source.mp4"
        cropped_path = working_dir / "scene.mp4"
        worker_stage("gpu_preflight")
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError("LTX_GPU_UNAVAILABLE")
        torch.cuda.reset_peak_memory_stats()
        model_load_started = time.perf_counter()
        with worker_phase("model_load"):
            _load_pipeline()
        model_load_duration_ms = round(
            (time.perf_counter() - model_load_started) * 1000
        )
        inference_started = time.perf_counter()
        with worker_phase("model_inference"):
            frame_plan = _render_scene(
                image_path=image_path,
                output_path=raw_path,
                visual_prompt=manifest["visual_prompt"],
                seed=manifest["seed"],
                target_duration=manifest["target_duration_seconds"],
                **_end_guide_arguments(manifest, image_path),
            )
        torch.cuda.synchronize()
        inference_duration_ms = round((time.perf_counter() - inference_started) * 1000)
        gpu_properties = torch.cuda.get_device_properties(0)
        runtime = {
            "python_version": platform.python_version(),
            "torch_version": str(torch.__version__),
            "cuda_runtime_version": str(torch.version.cuda),
            "gpu_name": str(gpu_properties.name),
            "gpu_total_memory_bytes": int(gpu_properties.total_memory),
            "peak_gpu_memory_allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
            "peak_gpu_memory_reserved_bytes": int(torch.cuda.max_memory_reserved(0)),
            "model_load_duration_ms": model_load_duration_ms,
            "inference_duration_ms": inference_duration_ms,
        }
        with worker_phase("silent_720p_normalization"):
            _normalize_silent_clip(
                raw_path,
                cropped_path,
                target_duration=manifest["target_duration_seconds"],
                generated_frame_count=int(frame_plan["generated_frame_count"]),
            )
        with worker_phase("scene_media_validation"):
            details = _validate_scene_file(
                cropped_path,
                manifest["target_duration_seconds"],
                expected_frame_count=int(frame_plan["target_frame_count"]),
            )
        with worker_phase("scene_output_commit"):
            output_path = _safe_attempt_file(
                attempt_root, "output/scene.mp4", create_parent=True
            )
            shutil.copyfile(cropped_path, output_path)
            output_size = output_path.stat().st_size
            if output_size <= 0 or output_size > MAX_OUTPUT_BYTES:
                output_path.unlink(missing_ok=True)
                raise WorkerContractError("VIDEO_SCENE_OUTPUT_LIMIT_EXCEEDED")
            output_sha256 = _sha256_file(output_path)
            output_manifest = {
                "schema_version": OUTPUT_SCHEMA,
                "workload": "video.scene.generate",
                "status": "CANDIDATE_READY",
                "product_playable": False,
                "safety_validation": "NOT_RUN",
                "job_id": request.job_id,
                "generation_id": request.generation_id,
                "attempt_id": request.attempt_id,
                "scene_id": manifest["scene_id"],
                "scene_index": manifest["scene_index"],
                "scene_count": manifest["scene_count"],
                "storyboard_sha256": manifest["storyboard_sha256"],
                "source_drawing_sha256": manifest["source_drawing_sha256"],
                "output_ref": "output/scene.mp4",
                "output_sha256": output_sha256,
                "output_size_bytes": output_size,
                "duration_seconds": details["duration_seconds"],
                "width": details["width"],
                "height": details["height"],
                "fps": details["fps"],
                "frame_count": details["frame_count"],
                "video_codec": details["video_codec"],
                "audio_streams": details["audio_streams"],
                "runtime": runtime,
                "model": {
                    "id": MODEL_ID,
                    "revision": MODEL_REVISION,
                    "code_tag": LTX_CODE_TAG,
                    "code_commit": _read_ltx_code_commit(),
                    "dependency_lock_sha256": _read_ltx_dependency_lock_sha256(),
                    "checkpoint_manifest_sha256": _sha256_file(Path(MODEL_MARKER)),
                    "model_profile": MODEL_PROFILE,
                    "license_id": MODEL_LICENSE_ID,
                    "license_review": model_manifest["license_review"],
                },
            }
            output_manifest_path = _safe_attempt_file(
                attempt_root,
                "output/scene-manifest.json",
                create_parent=True,
            )
            output_manifest_bytes = json.dumps(
                output_manifest,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            output_manifest_path.write_bytes(output_manifest_bytes)
            scratch_volume.commit()

    return {
        "schema_version": OUTPUT_SCHEMA,
        "workload": "video.scene.generate",
        "status": "CANDIDATE_READY",
        "product_playable": False,
        "safety_validation": "NOT_RUN",
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "scene_id": manifest["scene_id"],
        "output_ref": "output/scene.mp4",
        "output_sha256": output_sha256,
        "output_size_bytes": output_size,
        "output_manifest_sha256": hashlib.sha256(output_manifest_bytes).hexdigest(),
        "model_profile": MODEL_PROFILE,
        "code_commit": _read_ltx_code_commit(),
        "dependency_lock_sha256": _read_ltx_dependency_lock_sha256(),
        "runtime": runtime,
    }


def _build_silent_story_output_payload(
    request: Any,
    manifest: dict[str, Any],
    *,
    output_sha256: str,
    output_size_bytes: int,
    output_manifest_sha256: str,
    final_details: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    """Return candidate metadata with explicit provenance for every input anchor."""

    return {
        "schema_version": STORY_OUTPUT_SCHEMA,
        "workload": "video.story.generate",
        "status": "CANDIDATE_READY",
        "product_playable": False,
        "safety_validation": "NOT_RUN",
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "story_revision_id": manifest["story_revision_id"],
        "story_sha256": manifest["story_sha256"],
        "storyboard_sha256": manifest["storyboard_sha256"],
        "render_plan_sha256": manifest["render_plan_sha256"],
        "source_drawing_sha256": manifest["source_drawing_sha256"],
        "scene_visual_plan_sha256": canonical_sha256(manifest["scene_visual_plan"]),
        "scene_count": len(manifest["scenes"]),
        "output_ref": "output/video.mp4",
        "output_sha256": output_sha256,
        "output_size_bytes": output_size_bytes,
        "output_manifest_sha256": output_manifest_sha256,
        "duration_seconds": final_details["duration_seconds"],
        "width": final_details["width"],
        "height": final_details["height"],
        "fps": final_details["fps"],
        "video_codec": final_details["video_codec"],
        "audio_streams": final_details["audio_streams"],
        "model_profile": MODEL_PROFILE,
        "code_commit": _read_ltx_code_commit(),
        "dependency_lock_sha256": _read_ltx_dependency_lock_sha256(),
        "runtime": runtime,
    }


@app.function(
    name="generate-silent-story-video",
    image=_with_runtime_modules(_inference_image),
    gpu="L40S",
    cpu=8.0,
    memory=65_536,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume,
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=1_800,
    retries=0,
)
@observed_worker(
    workload="video.story.generate",
    model_id=MODEL_ID,
    model_revision=MODEL_REVISION,
    gpu_class="L40S",
    timeout_seconds=1_800,
)
def generate_silent_story_video(payload: dict[str, Any]) -> dict[str, Any]:
    """Render a confirmed 5–15 scene story from the original drawing, without audio."""

    worker_started = time.perf_counter()
    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l40s-video")
    if request.workload != "video.story.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")

    refresh_worker_volume(scratch_volume)
    attempt_root = _safe_attempt_root(request.attempt_prefix)
    manifest_bytes = _read_bounded(
        _safe_attempt_file(attempt_root, request.input_manifest_ref),
        MAX_MANIFEST_BYTES,
        "VIDEO_INPUT_MANIFEST_LIMIT_EXCEEDED",
    )
    if hashlib.sha256(manifest_bytes).hexdigest() != request.input_manifest_sha256:
        raise WorkerContractError("VIDEO_INPUT_MANIFEST_HASH_MISMATCH")
    with worker_phase("story_manifest_validation"):
        manifest = _parse_story_input(manifest_bytes)

    with tempfile.TemporaryDirectory(prefix="sketch2life-ltx-story-") as temp_dir:
        working_dir = Path(temp_dir)
        image_path = working_dir / "original-drawing-conditioned.png"
        source_bytes = _prepare_story_drawing(attempt_root, manifest, image_path)
        if source_bytes + len(manifest_bytes) != request.input_bytes:
            raise WorkerContractError("VIDEO_INPUT_SIZE_MISMATCH")
        model_manifest = _require_model_ready()
        worker_stage("gpu_preflight")
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError("LTX_GPU_UNAVAILABLE")
        torch.cuda.reset_peak_memory_stats()
        keyframes = None
        if "keyframe_plan" in manifest:
            import keyframe_render

            with worker_phase("keyframe_preparation"):
                keyframes = keyframe_render.prepare_keyframes(
                    _safe_attempt_file(attempt_root, manifest["source_drawing_ref"]),
                    manifest["keyframe_plan"],
                    scene_count=len(manifest["scenes"]),
                    workdir=working_dir,
                    predictor_factory=_load_sam_predictor,
                )
            # SAM is released before the LTX pipeline loads; both do not fit comfortably together.
            gc.collect()
            torch.cuda.empty_cache()
        pipeline_cache_hit = _PIPELINE is not None
        model_load_started = time.perf_counter()
        with worker_phase("model_load"):
            _load_pipeline()
        model_load_duration_ms = round(
            (time.perf_counter() - model_load_started) * 1000
        )

        prompt_template_version = (
            PROMPT_TEMPLATE_VERSION
            if keyframes is None
            else KEYFRAME_PROMPT_TEMPLATE_VERSION
        )

        scene_results: list[dict[str, Any]] = []
        normalized_clips: list[Path] = []
        conditioning_path = image_path
        for scene in manifest["scenes"]:
            scene_index = scene["scene_index"]
            scene_name = f"scene-{scene_index:02d}"
            raw_path = working_dir / f"{scene_name}-source.mp4"
            normalized_path = working_dir / f"{scene_name}.mp4"
            render_inputs = _scene_render_inputs(
                keyframes,
                scene,
                manifest["scene_visual_plan"],
                scene_index=scene_index,
                scene_count=len(manifest["scenes"]),
                legacy_start=conditioning_path,
            )
            compiled_prompt = render_inputs["prompt"]
            prompt_sha256 = hashlib.sha256(compiled_prompt.encode("utf-8")).hexdigest()
            conditioning_sha256 = _sha256_file(render_inputs["start_path"])
            frame_plan = plan_scene_frames(scene["duration_seconds"])
            worker_stage(f"scene_{scene_index:02d}_started")
            inference_started = time.perf_counter()
            with worker_phase(f"scene_{scene_index:02d}_inference"):
                generated_frame_plan = _render_scene(
                    image_path=render_inputs["start_path"],
                    output_path=raw_path,
                    visual_prompt=compiled_prompt,
                    seed=scene["seed"],
                    target_duration=scene["duration_seconds"],
                    prompt_is_compiled=True,
                    end_image_path=render_inputs["end_path"],
                    end_strength=render_inputs["end_strength"],
                )
                torch.cuda.synchronize()
            inference_duration_ms = round(
                (time.perf_counter() - inference_started) * 1000
            )
            normalize_started = time.perf_counter()
            with worker_phase(f"scene_{scene_index:02d}_normalize"):
                _normalize_silent_clip(
                    raw_path,
                    normalized_path,
                    target_duration=scene["duration_seconds"],
                    generated_frame_count=int(
                        generated_frame_plan["generated_frame_count"]
                    ),
                )
            normalization_duration_ms = round(
                (time.perf_counter() - normalize_started) * 1000
            )
            details = _validate_scene_file(
                normalized_path,
                scene["duration_seconds"],
                expected_frame_count=int(frame_plan["target_frame_count"]),
            )
            scene_bytes = normalized_path.stat().st_size
            scene_sha256 = _sha256_file(normalized_path)
            scene_output = _safe_attempt_file(
                attempt_root,
                f"output/scenes/{scene_name}.mp4",
                create_parent=True,
            )
            output_copy_started = time.perf_counter()
            shutil.copyfile(normalized_path, scene_output)
            output_copy_duration_ms = round(
                (time.perf_counter() - output_copy_started) * 1000
            )
            scene_record = {
                "scene_id": scene["scene_id"],
                "scene_index": scene_index,
                "scene_sha256": scene_sha256,
                "scene_size_bytes": scene_bytes,
                "conditioning_frame_sha256": conditioning_sha256,
                "conditioned_from_previous_scene": render_inputs[
                    "chain_from_previous_scene"
                ],
                "conditioning_keyframe": render_inputs["start_keyframe"],
                "end_keyframe": render_inputs["end_keyframe"],
                "end_frame_strength": render_inputs["end_strength"],
                "prompt_template_version": prompt_template_version,
                "prompt_sha256": prompt_sha256,
                "duration_seconds": details["duration_seconds"],
                "width": details["width"],
                "height": details["height"],
                "fps": details["fps"],
                "frame_count": details["frame_count"],
                "generated_frame_count": int(
                    generated_frame_plan["generated_frame_count"]
                ),
                "temporal_scale": generated_frame_plan["temporal_scale"],
                "audio_streams": details["audio_streams"],
                "inference_duration_ms": inference_duration_ms,
                "normalization_duration_ms": normalization_duration_ms,
                "output_copy_duration_ms": output_copy_duration_ms,
            }
            if keyframes is None and scene_index < len(manifest["scenes"]):
                next_conditioning_path = (
                    working_dir / f"scene-{scene_index:02d}-continuity-frame.png"
                )
                extraction_started = time.perf_counter()
                with worker_phase(f"scene_{scene_index:02d}_continuity_frame"):
                    _extract_continuity_frame(
                        normalized_path,
                        next_conditioning_path,
                        frame_count=details["frame_count"],
                    )
                scene_record["continuity_frame_extract_duration_ms"] = round(
                    (time.perf_counter() - extraction_started) * 1000
                )
                scene_record["continuity_frame_sha256"] = _sha256_file(
                    next_conditioning_path
                )
                conditioning_path = next_conditioning_path
            scene_results.append(scene_record)
            normalized_clips.append(normalized_path)
            _write_story_progress(
                attempt_root,
                completed_scenes=len(scene_results),
                scene_count=len(manifest["scenes"]),
                stage="SCENES_RENDERING",
            )
            scratch_volume.commit()

        worker_stage("final_silent_assembly")
        concat_manifest = working_dir / "concat.txt"
        concat_manifest.write_text(
            "".join(f"file '{path.as_posix()}'\n" for path in normalized_clips),
            encoding="utf-8",
        )
        final_path = working_dir / "silent-story.mp4"
        composition_started = time.perf_counter()
        with worker_phase("silent_story_composition"):
            _assemble_silent_story(
                concat_manifest,
                final_path,
                target_duration=float(manifest["target_duration_seconds"]),
            )
        composition_duration_ms = round(
            (time.perf_counter() - composition_started) * 1000
        )
        with worker_phase("final_media_validation"):
            final_details = _validate_final_story(
                final_path,
                target_duration=float(manifest["target_duration_seconds"]),
            )
        if final_path.stat().st_size > MAX_OUTPUT_BYTES:
            raise WorkerContractError("VIDEO_STORY_OUTPUT_LIMIT_EXCEEDED")
        output_path = _safe_attempt_file(
            attempt_root, "output/video.mp4", create_parent=True
        )
        final_copy_started = time.perf_counter()
        shutil.copyfile(final_path, output_path)
        final_copy_duration_ms = round(
            (time.perf_counter() - final_copy_started) * 1000
        )
        output_sha256 = _sha256_file(output_path)
        runtime = {
            "python_version": platform.python_version(),
            "torch_version": str(torch.__version__),
            "cuda_runtime_version": str(torch.version.cuda),
            "gpu_name": str(torch.cuda.get_device_properties(0).name),
            "gpu_total_memory_bytes": int(
                torch.cuda.get_device_properties(0).total_memory
            ),
            "peak_gpu_memory_allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
            "peak_gpu_memory_reserved_bytes": int(torch.cuda.max_memory_reserved(0)),
            "model_load_duration_ms": model_load_duration_ms,
            "composition_duration_ms": composition_duration_ms,
            "final_copy_duration_ms": final_copy_duration_ms,
            "pipeline_cache_hit": pipeline_cache_hit,
            "worker_duration_ms": round((time.perf_counter() - worker_started) * 1000),
        }
        output_manifest = {
            "schema_version": STORY_OUTPUT_SCHEMA,
            "workload": "video.story.generate",
            "status": "CANDIDATE_READY",
            "product_playable": False,
            "safety_validation": "NOT_RUN",
            "audio_streams": final_details["audio_streams"],
            "job_id": request.job_id,
            "generation_id": request.generation_id,
            "attempt_id": request.attempt_id,
            "story_revision_id": manifest["story_revision_id"],
            "story_sha256": manifest["story_sha256"],
            "storyboard_sha256": manifest["storyboard_sha256"],
            "render_plan_sha256": manifest["render_plan_sha256"],
            "scene_visual_plan_sha256": canonical_sha256(manifest["scene_visual_plan"]),
            "source_drawing_sha256": manifest["source_drawing_sha256"],
            "prompt_template_version": prompt_template_version,
            "continuity_mode": (
                "previous_scene_final_frame"
                if keyframes is None
                else "keyframe_chain"
                if keyframes.render_mode == "keyframe"
                else "original_each_scene"
            ),
            "render_mode": "legacy" if keyframes is None else keyframes.render_mode,
            "fallback_reason": None if keyframes is None else keyframes.fallback_reason,
            "keyframes": [] if keyframes is None else keyframes.summaries,
            "scene_count": len(scene_results),
            "scenes": scene_results,
            "image_guides": [],
            "output_ref": "output/video.mp4",
            "output_sha256": output_sha256,
            "output_size_bytes": output_path.stat().st_size,
            "duration_seconds": final_details["duration_seconds"],
            "width": final_details["width"],
            "height": final_details["height"],
            "fps": final_details["fps"],
            "frame_count": final_details["frame_count"],
            "video_codec": final_details["video_codec"],
            "runtime": runtime,
            "model": {
                "id": MODEL_ID,
                "revision": MODEL_REVISION,
                "code_tag": LTX_CODE_TAG,
                "code_commit": _read_ltx_code_commit(),
                "dependency_lock_sha256": _read_ltx_dependency_lock_sha256(),
                "checkpoint_manifest_sha256": _sha256_file(Path(MODEL_MARKER)),
                "model_profile": MODEL_PROFILE,
                "license_id": MODEL_LICENSE_ID,
                "license_review": model_manifest["license_review"],
            },
        }
        output_manifest_bytes = json.dumps(
            output_manifest,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        _safe_attempt_file(
            attempt_root, "output/video-manifest.json", create_parent=True
        ).write_bytes(output_manifest_bytes)
        _write_story_progress(
            attempt_root,
            completed_scenes=len(scene_results),
            scene_count=len(manifest["scenes"]),
            stage="CANDIDATE_READY",
        )
        scratch_volume.commit()

    return _build_silent_story_output_payload(
        request,
        manifest,
        output_sha256=output_sha256,
        output_size_bytes=output_path.stat().st_size,
        output_manifest_sha256=hashlib.sha256(output_manifest_bytes).hexdigest(),
        final_details=final_details,
        runtime=runtime,
    )


def _parse_story_input(raw: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise WorkerContractError("VIDEO_STORY_MANIFEST_INVALID") from None
    if (
        isinstance(payload, dict)
        and payload.get("schema_version")
        == "sketch2life.modal.silent-story-video-input.v1"
    ):
        raise WorkerContractError("VIDEO_STORY_VISUAL_PLAN_REQUIRED")
    expected = {
        "schema_version",
        "story_revision_id",
        "story_sha256",
        "storyboard_sha256",
        "render_plan_sha256",
        "source_drawing_ref",
        "source_drawing_sha256",
        "target_duration_seconds",
        "scene_count",
        "scenes",
        "scene_visual_plan",
    }
    if not isinstance(payload, dict) or set(payload) - {"keyframe_plan"} != expected:
        raise WorkerContractError("VIDEO_STORY_MANIFEST_INVALID")
    story_revision_id = payload.get("story_revision_id")
    scene_count = payload.get("scene_count")
    scenes = payload.get("scenes")
    target_duration = payload.get("target_duration_seconds")
    if (
        payload.get("schema_version") != STORY_INPUT_SCHEMA
        or not isinstance(story_revision_id, str)
        or _OPAQUE_ID.fullmatch(story_revision_id) is None
        or not isinstance(payload.get("story_sha256"), str)
        or _SHA256.fullmatch(payload["story_sha256"]) is None
        or not isinstance(payload.get("storyboard_sha256"), str)
        or _SHA256.fullmatch(payload["storyboard_sha256"]) is None
        or not isinstance(payload.get("render_plan_sha256"), str)
        or _SHA256.fullmatch(payload["render_plan_sha256"]) is None
        or not isinstance(payload.get("source_drawing_sha256"), str)
        or _SHA256.fullmatch(payload["source_drawing_sha256"]) is None
        or payload.get("source_drawing_ref") != "input/drawing.png"
        or type(scene_count) is not int
        or not 5 <= scene_count <= 15
        or not isinstance(scenes, list)
        or len(scenes) != scene_count
        or type(target_duration) not in (int, float)
        or not 30 <= target_duration <= 90
    ):
        raise WorkerContractError("VIDEO_STORY_INPUT_NOT_ALLOWED")

    scene_ids: list[str] = []
    durations: list[float] = []
    for expected_index, scene in enumerate(scenes, start=1):
        scene_keys = {
            "scene_id",
            "scene_index",
            "title",
            "action",
            "visual_prompt",
            "duration_seconds",
            "seed",
            "confirmed_anchor_ids",
        }
        if not isinstance(scene, dict) or set(scene) != scene_keys:
            raise WorkerContractError("VIDEO_STORY_SCENE_INVALID")
        scene_id = scene.get("scene_id")
        duration = scene.get("duration_seconds")
        anchors = scene.get("confirmed_anchor_ids")
        if (
            not isinstance(scene_id, str)
            or _SCENE_ID.fullmatch(scene_id) is None
            or scene_id != f"scene-{expected_index}"
            or type(scene.get("scene_index")) is not int
            or scene["scene_index"] != expected_index
            or not isinstance(scene.get("title"), str)
            or not scene["title"].strip()
            or len(scene["title"]) > 100
            or not isinstance(scene.get("action"), str)
            or not scene["action"].strip()
            or len(scene["action"]) > 500
            or not isinstance(scene.get("visual_prompt"), str)
            or not scene["visual_prompt"].strip()
            or len(scene["visual_prompt"]) > 1_200
            or type(duration) not in (int, float)
            or not 1 <= duration <= MAX_VIDEO_SECONDS
            or type(scene.get("seed")) is not int
            or not 0 <= scene["seed"] <= 2_147_483_647
            or not isinstance(anchors, list)
            or not 1 <= len(anchors) <= 16
            or any(
                not isinstance(anchor, str) or not anchor.strip() or len(anchor) > 120
                for anchor in anchors
            )
        ):
            raise WorkerContractError("VIDEO_STORY_SCENE_INVALID")
        scene_ids.append(scene_id)
        durations.append(float(duration))

    if (
        len(set(scene_ids)) != scene_count
        or abs(sum(durations) - float(target_duration)) > 0.1
    ):
        raise WorkerContractError("VIDEO_STORY_TIMELINE_INVALID")

    try:
        scene_frame_count = sum(
            int(plan_scene_frames(duration)["target_frame_count"])
            for duration in durations
        )
        target_frame_count = int(
            plan_scene_frames(float(target_duration))["target_frame_count"]
        )
    except StoryVisualPlanError as exc:
        raise WorkerContractError(str(exc)) from None
    if scene_frame_count != target_frame_count:
        raise WorkerContractError("VIDEO_STORY_TIMELINE_FRAME_ALIGNMENT_INVALID")

    try:
        validate_story_visual_plan(
            payload["scene_visual_plan"],
            scenes=scenes,
            story_sha256=payload["story_sha256"],
        )
    except StoryVisualPlanError as exc:
        raise WorkerContractError(str(exc)) from None

    render_plan_payload = {
        "schema_version": STORY_INPUT_SCHEMA,
        "story_revision_id": story_revision_id,
        "story_sha256": payload["story_sha256"],
        "storyboard_sha256": payload["storyboard_sha256"],
        "source_drawing_sha256": payload["source_drawing_sha256"],
        "target_duration_seconds": float(target_duration),
        "scenes": scenes,
        "scene_visual_plan": payload["scene_visual_plan"],
    }
    if "keyframe_plan" in payload:
        # FEAT-087: the keyframe plan is part of what the hash promises, but only when present.
        try:
            validate_keyframe_plan(payload["keyframe_plan"], scene_count=scene_count)
        except KeyframePlanError as exc:
            raise WorkerContractError(exc.code) from None
        render_plan_payload["keyframe_plan"] = payload["keyframe_plan"]
    if canonical_sha256(render_plan_payload) != payload["render_plan_sha256"]:
        raise WorkerContractError("VIDEO_STORY_RENDER_PLAN_HASH_MISMATCH")
    return payload


def _prepare_story_drawing(
    attempt_root: Path, manifest: dict[str, Any], output: Path
) -> int:
    source_path = _safe_attempt_file(attempt_root, manifest["source_drawing_ref"])
    raw = _read_bounded(source_path, MAX_DRAWING_BYTES, "VIDEO_DRAWING_LIMIT_EXCEEDED")
    if hashlib.sha256(raw).hexdigest() != manifest["source_drawing_sha256"]:
        raise WorkerContractError("VIDEO_DRAWING_HASH_MISMATCH")
    from PIL import Image, UnidentifiedImageError

    Image.MAX_IMAGE_PIXELS = MAX_DRAWING_PIXELS
    try:
        with Image.open(source_path) as image:
            if image.format not in {"PNG", "JPEG", "WEBP"}:
                raise WorkerContractError("VIDEO_DRAWING_MEDIA_TYPE_INVALID")
            if image.width * image.height > MAX_DRAWING_PIXELS:
                raise WorkerContractError("VIDEO_DRAWING_PIXEL_LIMIT_EXCEEDED")
            image.verify()
        with Image.open(source_path) as image:
            image.load()
            drawing = image.convert("RGB")
    except WorkerContractError:
        raise
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        raise WorkerContractError("VIDEO_DRAWING_DECODE_FAILED") from None

    # LTX renders 1280x768 before the final 720p crop. Fit the complete source
    # drawing inside that frame so the crop removes only white padding, never art.
    margin = 96
    drawing.thumbnail(
        (OUTPUT_WIDTH - margin * 2, MODEL_FRAME_HEIGHT - margin * 2),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", (OUTPUT_WIDTH, MODEL_FRAME_HEIGHT), "white")
    canvas.paste(
        drawing,
        (
            (OUTPUT_WIDTH - drawing.width) // 2,
            (MODEL_FRAME_HEIGHT - drawing.height) // 2,
        ),
    )
    canvas.save(output, format="PNG", optimize=False)
    return len(raw)


def _write_story_progress(
    attempt_root: Path, *, completed_scenes: int, scene_count: int, stage: str
) -> None:
    value = {
        "schema_version": "sketch2life.modal.silent-story-progress.v1",
        "completed_scenes": completed_scenes,
        "scene_count": scene_count,
        "stage": stage,
        "product_playable": False,
    }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    _safe_attempt_file(
        attempt_root, "output/progress.json", create_parent=True
    ).write_bytes(encoded)


def _assemble_silent_story(
    concat_manifest: Path, output: Path, *, target_duration: float
) -> None:
    target_frame_count = int(plan_scene_frames(target_duration)["target_frame_count"])
    command = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_manifest),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        f"fps={int(FPS)},trim=end_frame={target_frame_count},setpts=N/({int(FPS)}*TB)",
        "-frames:v",
        str(target_frame_count),
        "-r",
        str(int(FPS)),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    try:
        completed = subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=900
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("VIDEO_STORY_ASSEMBLY_TIMEOUT") from None
    if completed.returncode != 0 or not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("VIDEO_STORY_ASSEMBLY_FAILED")


def _validate_final_story(path: Path, *, target_duration: float) -> dict[str, Any]:
    expected_frame_count = int(plan_scene_frames(target_duration)["target_frame_count"])
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("VIDEO_STORY_PROBE_TIMEOUT") from None
    if completed.returncode != 0:
        raise RuntimeError("VIDEO_STORY_PROBE_FAILED")
    try:
        info = json.loads(completed.stdout)
        streams = info["streams"]
        video = [stream for stream in streams if stream.get("codec_type") == "video"]
        audio = [stream for stream in streams if stream.get("codec_type") == "audio"]
        duration = float(info["format"]["duration"])
        numerator, denominator = video[0]["avg_frame_rate"].split("/", maxsplit=1)
        frame_rate = float(numerator) / float(denominator)
        frame_count = int(video[0].get("nb_frames") or 0)
        details = {
            "duration_seconds": duration,
            "width": int(video[0]["width"]),
            "height": int(video[0]["height"]),
            "fps": frame_rate,
            "frame_count": frame_count,
            "video_codec": str(video[0]["codec_name"]),
            "audio_streams": len(audio),
        }
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        raise RuntimeError("VIDEO_STORY_PROBE_INVALID") from None
    if (
        len(video) != 1
        or audio
        or details["video_codec"] != "h264"
        or details["width"] != OUTPUT_WIDTH
        or details["height"] != OUTPUT_HEIGHT
        or abs(frame_rate - FPS) > 0.01
        or not 30 <= duration <= 90
        or frame_count != expected_frame_count
        or abs(duration - expected_frame_count / FPS) > 1 / FPS
        or abs(duration - target_duration) > 1 / FPS
        or not 0 < path.stat().st_size <= MAX_OUTPUT_BYTES
    ):
        raise RuntimeError("VIDEO_STORY_PROFILE_INVALID")
    return details


def _parse_scene_input(raw: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise WorkerContractError("VIDEO_INPUT_MANIFEST_INVALID") from None
    expected = {
        "schema_version",
        "scene_id",
        "scene_index",
        "scene_count",
        "purpose",
        "storyboard_sha256",
        "source_drawing_ref",
        "source_drawing_sha256",
        "visual_prompt",
        "target_duration_seconds",
        "seed",
    }
    if not isinstance(payload, dict) or set(payload) - {"end_guide_strength"} != expected:
        raise WorkerContractError("VIDEO_INPUT_MANIFEST_INVALID")
    guide = payload.get("end_guide_strength", 0.7)
    if type(guide) not in (int, float) or not 0.1 <= guide <= 1.0:
        raise WorkerContractError("VIDEO_INPUT_NOT_ALLOWED")
    scene_id = payload.get("scene_id")
    scene_match = _SCENE_ID.fullmatch(scene_id) if isinstance(scene_id, str) else None
    scene_index = payload.get("scene_index")
    scene_count = payload.get("scene_count")
    purpose = payload.get("purpose")
    prompt = payload.get("visual_prompt")
    duration = payload.get("target_duration_seconds")
    seed = payload.get("seed")
    if (
        payload.get("schema_version") != INPUT_SCHEMA
        or scene_match is None
        or type(scene_index) is not int
        or type(scene_count) is not int
        or not 1 <= scene_index <= 15
        or not 1 <= scene_count <= 15
        or scene_index > scene_count
        or scene_match.group(1) != str(scene_index)
        or purpose not in {"SYNTHETIC_FEASIBILITY", "SYNTHETIC_END_TO_END", "PRODUCT"}
        or (purpose == "PRODUCT" and not 5 <= scene_count <= 15)
        or not isinstance(prompt, str)
        or not prompt.strip()
        or len(prompt) > 1_200
        or type(duration) not in (int, float)
        or not 1 <= duration <= MAX_VIDEO_SECONDS
        or type(seed) is not int
        or not 0 <= seed <= 2_147_483_647
        or not isinstance(payload.get("source_drawing_ref"), str)
        or not isinstance(payload.get("source_drawing_sha256"), str)
        or _SHA256.fullmatch(payload["source_drawing_sha256"]) is None
        or not isinstance(payload.get("storyboard_sha256"), str)
        or _SHA256.fullmatch(payload["storyboard_sha256"]) is None
    ):
        raise WorkerContractError("VIDEO_INPUT_NOT_ALLOWED")
    drawing_ref = Path(payload["source_drawing_ref"])
    if (
        drawing_ref.is_absolute()
        or len(drawing_ref.parts) != 2
        or drawing_ref.parts[0] != "input"
        or drawing_ref.name in {".", ".."}
        or drawing_ref.suffix.lower() not in _ALLOWED_DRAWING_SUFFIXES
    ):
        raise WorkerContractError("VIDEO_INPUT_PATH_INVALID")
    return payload


def _prepare_drawing(
    attempt_root: Path,
    manifest: dict[str, Any],
    normalized_path: Path,
) -> int:
    source_path = _safe_attempt_file(attempt_root, manifest["source_drawing_ref"])
    raw = _read_bounded(source_path, MAX_DRAWING_BYTES, "VIDEO_DRAWING_LIMIT_EXCEEDED")
    if hashlib.sha256(raw).hexdigest() != manifest["source_drawing_sha256"]:
        raise WorkerContractError("VIDEO_DRAWING_HASH_MISMATCH")
    from PIL import Image, UnidentifiedImageError

    Image.MAX_IMAGE_PIXELS = MAX_DRAWING_PIXELS
    try:
        with Image.open(source_path) as image:
            if image.format not in {"PNG", "JPEG", "WEBP"}:
                raise WorkerContractError("VIDEO_DRAWING_MEDIA_TYPE_INVALID")
            if image.width * image.height > MAX_DRAWING_PIXELS:
                raise WorkerContractError("VIDEO_DRAWING_PIXEL_LIMIT_EXCEEDED")
            image.verify()
        with Image.open(source_path) as image:
            image.load()
            normalized = image.convert("RGB")
    except WorkerContractError:
        raise
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        raise WorkerContractError("VIDEO_DRAWING_DECODE_FAILED") from None

    normalized.save(normalized_path, format="PNG", optimize=False)
    return len(raw)


def _warm_up_scene_renderer(prompts: list[str] | None = None) -> dict[str, Any]:
    """Prepare the container before the first scene; no job data is read.

    Reads the checkpoint files, builds the pipeline, compiles the decoder with a one second blank render and, when the
    backend already knows the scene prompts, encodes them all in one text-encoder load.
    """

    global _DECODER_COMPILED

    started = time.perf_counter()
    with worker_phase("checkpoint_preflight"):
        _require_model_ready()
    with worker_phase("model_load"):
        if not _DECODER_COMPILED:
            _ensure_checkpoints_read()
        pipeline = _load_pipeline()
    if prompts and isinstance(pipeline.prompt_encoder, PromptCache):
        import torch

        with worker_phase("prompt_encoding"), torch.inference_mode():
            pipeline.prompt_encoder.prepare([_ltx_animation_prompt(prompt) for prompt in prompts])
    if not _DECODER_COMPILED:
        with worker_phase("decoder_compile"):
            _compile_decoder()
        _DECODER_COMPILED = True
    seconds = round(time.perf_counter() - started, 1)
    print(
        json.dumps({"event": "scene_warm_up", "seconds": seconds, "speed_profile": _PROFILES.current}),
        flush=True,
    )
    return {"warmed": True, "seconds": seconds}


def _compile_decoder() -> None:
    """Pay the first-render compilation with a blank one second clip; a failure only costs time later."""

    if _PROFILES.current != FAST:
        return
    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="sketch2life-ltx-warm-") as directory:
        blank = Path(directory) / "blank.png"
        Image.new("RGB", (OUTPUT_WIDTH, MODEL_FRAME_HEIGHT), "white").save(blank, format="PNG")
        try:
            _render_scene(
                image_path=blank,
                output_path=Path(directory) / "warm.mp4",
                visual_prompt="A blank sheet of paper.",
                seed=1,
                target_duration=1.0,
            )
        except Exception as error:  # noqa: BLE001 - the warm-up never fails the first job
            print(
                json.dumps({"event": "scene_warm_up_render_failed", "error_type": type(error).__name__}),
                flush=True,
            )


def _render_scene(**arguments: Any) -> dict[str, int | float]:
    """``_run_ltx`` on the current speed profile, falling back to the safe one when memory runs out."""

    return render_with_fallback(
        _PROFILES,
        lambda: _run_ltx(pipeline=_load_pipeline(), **arguments),
        release=_release_pipeline,
    )


def _release_pipeline() -> None:
    _unload_pipeline()
    print(json.dumps({"event": "scene_speed_fallback", "speed_profile": _PROFILES.current}), flush=True)


def _unload_pipeline() -> None:
    """Give the renderer's GPU memory back, including what a half-finished load left behind."""

    global _PIPELINE

    _PIPELINE = None
    gc.collect()
    import torch

    empty_cache = getattr(torch.cuda, "empty_cache", None)
    if empty_cache is not None:
        empty_cache()


def _checkpoint_names() -> list[str]:
    """The checkpoint files the renderer will load."""

    return [
        CONV_VAE_FILE if _OPTIONS.conv_vae and part == "video_vae" else name
        for name, part in MODEL_FILES.items()
    ]


def _read_checkpoints() -> None:
    """Read every checkpoint file once so that loading the pipeline finds it in the page cache."""

    for name in _checkpoint_names():
        with (Path(MODEL_ROOT) / name).open("rb") as handle:
            while handle.read(64 * 1024 * 1024):
                pass


def _start_checkpoint_prefetch() -> None:
    """Read the checkpoint in the background while scene frames are prepared."""

    global _PREFETCH

    if _CHECKPOINTS_READ.is_set() or (_PREFETCH is not None and _PREFETCH.is_alive()):
        return

    def read() -> None:
        try:
            _read_checkpoints()
        except OSError as error:
            print(json.dumps({"event": "checkpoint_prefetch_failed", "error_type": type(error).__name__}), flush=True)
        else:
            _CHECKPOINTS_READ.set()

    _PREFETCH = threading.Thread(target=read, name="checkpoint-prefetch", daemon=True)
    _PREFETCH.start()


def _ensure_checkpoints_read() -> None:
    if _PREFETCH is not None:
        _PREFETCH.join()
    if not _CHECKPOINTS_READ.is_set():
        _read_checkpoints()
        _CHECKPOINTS_READ.set()


def _load_pipeline() -> Any:
    import torch
    from ltx_core.quantization.fp8_cast import build_policy as build_fp8_cast_policy
    from ltx_pipelines import DistilledPipeline
    from ltx_pipelines.utils.model_paths import ModelPaths
    from ltx_pipelines.utils.types import OffloadMode

    global _PIPELINE
    if _PIPELINE is not None:
        return _PIPELINE
    _PREPARATION.stop()  # the preparation models and the renderer do not fit on the GPU together
    if _read_ltx_code_commit() != PINNED_LTX_CODE_COMMIT:
        raise RuntimeError("LTX_CODE_REVISION_MISMATCH")
    if _read_ltx_dependency_lock_sha256() is None:
        raise RuntimeError("LTX_DEPENDENCY_LOCK_INVALID")
    if not torch.cuda.is_available():
        raise RuntimeError("LTX_GPU_UNAVAILABLE")
    model_root = Path(MODEL_ROOT)
    transformer_path = model_root / next(
        name for name, part in MODEL_FILES.items() if part == "transformer"
    )
    video_vae_path = model_root / next(name for name, part in MODEL_FILES.items() if part == "video_vae")
    if _OPTIONS.conv_vae:
        video_vae_path = model_root / CONV_VAE_FILE
        if not video_vae_path.is_file():
            raise RuntimeError("LTX_CONV_VAE_NOT_STAGED")
    try:
        quantization_policy = build_fp8_cast_policy(str(transformer_path))
    except AttributeError:
        raise RuntimeError("LTX_QUANTIZATION_API_MISMATCH") from None
    paths = ModelPaths.from_split(
        transformer_path=str(transformer_path),
        text_encoder_path=str(
            model_root
            / next(name for name, part in MODEL_FILES.items() if part == "text_encoder")
        ),
        video_vae_path=str(video_vae_path),
        audio_vae_path=str(
            model_root
            / next(name for name, part in MODEL_FILES.items() if part == "audio_vae")
        ),
    )
    upsampler = model_root / next(
        name for name, part in MODEL_FILES.items() if part == "spatial_upsampler"
    )
    fast = _PROFILES.current == FAST
    options: dict[str, Any] = {}
    if fast and not _OPTIONS.conv_vae:  # the decoding modes belong to the diffusion VAE
        from ltx_core.model.video_vae.transformer import DiffVAEMode

        options["diffvae_optimization"] = DiffVAEMode("combined_compile")
    pipeline = DistilledPipeline(
        model_paths=paths,
        spatial_upsampler_path=str(upsampler),
        loras=[],
        quantization=quantization_policy,
        offload_mode=OffloadMode.NONE if fast else OffloadMode.CPU,
        **options,
    )
    if fast:
        # ADR-0026. Gemma loaded whole ran out of memory, so it alone keeps streaming through the CPU.
        pipeline.prompt_encoder._offload_mode = OffloadMode.CPU
        pipeline.prompt_encoder = PromptCache(pipeline.prompt_encoder)
        # One transformer allocation stays on the GPU between calls (pinned LTX v1.6.2 attribute).
        pipeline.stage._active_weights = {}
    _PIPELINE = pipeline
    return _PIPELINE


def _run_ltx(
    *,
    pipeline: Any,
    image_path: Path,
    output_path: Path,
    visual_prompt: str,
    seed: int,
    target_duration: float,
    prompt_is_compiled: bool = False,
    end_image_path: Path | None = None,
    end_strength: float | None = None,
) -> dict[str, int | float]:
    import torch
    from ltx_pipelines.utils.media_io import encode_video
    from ltx_pipelines.utils.types import ImageConditioningInput

    frame_plan = plan_scene_frames(target_duration)
    # FEAT-098: the delivered frame count stays at 24 a second; the model may render at a lower rate.
    num_frames = int(plan_scene_frames(target_duration, frame_rate=_OPTIONS.fps)["generated_frame_count"])
    if num_frames > MAX_VIDEO_SECONDS * _OPTIONS.fps + 8:
        raise WorkerContractError("VIDEO_SCENE_DURATION_LIMIT_EXCEEDED")
    frame_plan = {
        **frame_plan,
        "generated_frame_count": num_frames,
        "temporal_scale": (frame_plan["target_frame_count"] / FPS) / (num_frames / _OPTIONS.fps),
    }
    prompt = (
        visual_prompt if prompt_is_compiled else _ltx_animation_prompt(visual_prompt)
    )
    if (end_image_path is None) != (end_strength is None):
        raise ValueError("end_image_path and end_strength go together")
    conditioning = ImageConditioningInput.replace(
        str(image_path),
        frame_idx=0,
        strength=1.0,
    )
    end_conditioning = _end_frame_conditioning(
        end_image_path, num_frames=num_frames, strength=end_strength
    )
    with torch.inference_mode():
        result = pipeline(
            prompt=prompt,
            seed=seed,
            height=_OPTIONS.height,
            width=_OPTIONS.width,
            frame_rate=float(_OPTIONS.fps),
            images=[conditioning, *end_conditioning],
            num_frames=num_frames,
        )
        # LTX audio is intentionally discarded; this delivery produces silent MP4 only.
        encode_video(
            result.video,
            _OPTIONS.fps,
            None,
            str(output_path),
            video_chunks_number=None,
        )
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError("LTX_SCENE_OUTPUT_MISSING")
    return frame_plan


def _load_sam_predictor() -> Any:
    """SAM 2.1 hiera-small image predictor (box prompts) from the model volume."""

    from sam_masks import MaskError

    if not SAM2_CHECKPOINT.is_file():
        raise MaskError("SAM_CHECKPOINT_UNAVAILABLE")
    import torch
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    model = build_sam2(
        SAM2_MODEL_CONFIG,
        str(SAM2_CHECKPOINT),
        device="cuda" if torch.cuda.is_available() else "cpu",
        apply_postprocessing=False,
    )
    return SAM2ImagePredictor(model)


def _scene_render_inputs(
    keyframes: Any,
    scene: dict[str, Any],
    visual_plan: dict[str, Any],
    *,
    scene_index: int,
    scene_count: int,
    legacy_start: Path | None,
) -> dict[str, Any]:
    """Pick the conditioning images, strengths and prompt for one scene.

    Without a keyframe plan this is the legacy path (v7 prompt, previous scene's final frame).
    """

    if keyframes is None:
        return {
            "start_path": legacy_start,
            "end_path": None,
            "end_strength": None,
            "prompt": compile_scene_prompt(
                scene, visual_plan, first_scene=scene_index == 1
            ),
            "prompt_version": PROMPT_TEMPLATE_VERSION,
            "chain_from_previous_scene": scene_index > 1,
            "start_keyframe": None,
            "end_keyframe": None,
        }
    cond = scene_conditioning(
        keyframes.render_mode, scene_index=scene_index, scene_count=scene_count
    )
    end_keyframe = cond["end_keyframe"]
    return {
        "start_path": keyframes.paths[cond["start_keyframe"]],
        "end_path": None if end_keyframe is None else keyframes.paths[end_keyframe],
        "end_strength": cond["end_strength"],
        "prompt": compile_keyframe_scene_prompt(scene, visual_plan),
        "prompt_version": KEYFRAME_PROMPT_TEMPLATE_VERSION,
        "chain_from_previous_scene": False,
        "start_keyframe": cond["start_keyframe"],
        "end_keyframe": end_keyframe,
    }


def _end_guide_arguments(manifest: dict[str, Any], image_path: Path) -> dict[str, Any]:
    """FEAT-094: guiding the last frame with the first one holds the camera and keeps the subject in the frame."""

    strength = manifest.get("end_guide_strength")
    return {} if strength is None else {"end_image_path": image_path, "end_strength": strength}


def _end_frame_conditioning(
    end_image_path: Path | None, *, num_frames: int, strength: float | None
) -> list[Any]:
    """FEAT-087: the scene's end keyframe is a soft guide on the last generated frame.

    LTX only allows a hard ``replace`` at frame 0 or 1+8k, and the last frame of a clip is 8k, so
    the end still is an ``ImageGuide`` (see evidence/M0_LTX_MULTI_IMAGE_END_FRAME_20261124.md).
    """

    if end_image_path is None or strength is None:
        return []
    from ltx_pipelines.utils.types import ImageConditioningInput

    return [
        ImageConditioningInput.guide(
            str(end_image_path), frame_idx=num_frames - 1, strength=strength
        )
    ]


def _ltx_animation_prompt(visual_prompt: str) -> str:
    """One motion-only paragraph: the action first, then how it moves, then the static camera.

    FEAT-094 E1: the earlier wrapper listed prohibitions and allowed named props; the model drew extra
    objects and zoomed. What must not appear is checked on the output, not written into the prompt.
    """

    direction = " ".join(visual_prompt.split())
    if not direction:
        raise WorkerContractError("VIDEO_SCENE_DIRECTION_REQUIRED")
    if not direction.endswith((".", "!", "?")):
        direction = f"{direction}."
    return (
        f"{direction} The movement is smooth and continuous from the first moment to the last. "
        "The drawing keeps its crayon strokes, colours and paper texture exactly as in the first "
        "frame. The camera remains static throughout."
    )


def _normalize_silent_clip(
    source: Path,
    destination: Path,
    *,
    target_duration: float,
    generated_frame_count: int,
) -> None:
    target_frame_count = int(plan_scene_frames(target_duration)["target_frame_count"])
    if (
        type(generated_frame_count) is not int
        or generated_frame_count < 9
        or (generated_frame_count - 1) % 8 != 0
    ):
        raise WorkerContractError("VIDEO_SCENE_FRAME_PLAN_INVALID")
    command = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        _OPTIONS.video_filter(
            target_frame_count=target_frame_count, generated_frame_count=generated_frame_count
        ),
        "-frames:v",
        str(target_frame_count),
        # ffmpeg 7.1 forgets the rate after setpts and would write 25 frames per second.
        "-r",
        str(int(FPS)),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-fps_mode",
        "cfr",
        "-movflags",
        "+faststart",
        str(destination),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("VIDEO_SCENE_NORMALIZATION_TIMEOUT") from None
    if completed.returncode != 0 or not destination.is_file():
        # FFmpeg stderr may contain untrusted path/prompt fragments; never emit it.
        raise RuntimeError("VIDEO_SCENE_NORMALIZATION_FAILED")


def _validate_scene_file(
    path: Path,
    target_duration: float,
    *,
    expected_frame_count: int | None = None,
) -> dict[str, Any]:
    if expected_frame_count is None:
        expected_frame_count = int(
            plan_scene_frames(target_duration)["target_frame_count"]
        )
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("VIDEO_SCENE_PROBE_TIMEOUT") from None
    if completed.returncode != 0:
        raise RuntimeError("VIDEO_SCENE_PROBE_FAILED")
    try:
        info = json.loads(completed.stdout)
        streams = info["streams"]
        video = [stream for stream in streams if stream.get("codec_type") == "video"]
        audio = [stream for stream in streams if stream.get("codec_type") == "audio"]
        duration = float(info["format"]["duration"])
        frame_rate_text = video[0]["avg_frame_rate"]
        numerator, denominator = frame_rate_text.split("/", maxsplit=1)
        frame_rate = float(numerator) / float(denominator)
        frame_count = int(video[0].get("nb_frames") or 0)
        width = int(video[0]["width"])
        height = int(video[0]["height"])
        codec = str(video[0]["codec_name"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        raise RuntimeError("VIDEO_SCENE_PROBE_INVALID") from None
    if (
        len(video) != 1
        or audio
        or codec != "h264"
        or width != OUTPUT_WIDTH
        or height != OUTPUT_HEIGHT
        or abs(frame_rate - FPS) > 0.01
        or frame_count != expected_frame_count
        or abs(duration - expected_frame_count / FPS) > 1 / FPS
        or abs(duration - target_duration) > 1 / FPS
        or not 0 < path.stat().st_size <= MAX_OUTPUT_BYTES
    ):
        raise RuntimeError("VIDEO_SCENE_PROFILE_INVALID")
    return {
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "fps": frame_rate,
        "frame_count": frame_count,
        "video_codec": codec,
        "audio_streams": len(audio),
    }


def _extract_continuity_frame(
    source: Path, destination: Path, *, frame_count: int
) -> None:
    if type(frame_count) is not int or frame_count <= 0:
        raise WorkerContractError("VIDEO_CONTINUITY_FRAME_COUNT_INVALID")
    filter_graph = (
        f"select=eq(n\\,{frame_count - 1}),"
        f"pad={OUTPUT_WIDTH}:{MODEL_FRAME_HEIGHT}:0:24:white"
    )
    command = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        filter_graph,
        "-fps_mode",
        "vfr",
        "-frames:v",
        "1",
        str(destination),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("VIDEO_CONTINUITY_FRAME_TIMEOUT") from None
    if (
        completed.returncode != 0
        or not destination.is_file()
        or destination.stat().st_size == 0
    ):
        raise RuntimeError("VIDEO_CONTINUITY_FRAME_EXTRACTION_FAILED")


_VERIFIED_MODEL_MANIFEST: dict[str, Any] | None = None


def _require_model_ready() -> dict[str, Any]:
    """The verified manifest of the pinned checkpoint; checked once per container (the model mount is read-only)."""

    global _VERIFIED_MODEL_MANIFEST
    if _VERIFIED_MODEL_MANIFEST is not None:
        return _VERIFIED_MODEL_MANIFEST
    model_volume.reload()
    marker = _read_model_manifest(Path(MODEL_MARKER))
    if marker is None or not _verify_model_manifest(Path(MODEL_ROOT), marker):
        raise RuntimeError("LTX_MODEL_NOT_STAGED")
    _VERIFIED_MODEL_MANIFEST = marker
    return marker


def _read_model_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _verify_model_manifest(root: Path, manifest: dict[str, Any]) -> bool:
    files = manifest.get("files")
    if (
        manifest.get("schema_version") != "sketch2life.modal.ltx-model-manifest.v1"
        or manifest.get("model_id") != MODEL_ID
        or manifest.get("model_revision") != MODEL_REVISION
        or manifest.get("code_tag") != LTX_CODE_TAG
        or not isinstance(files, dict)
        or set(files) != set(MODEL_FILES)
    ):
        return False
    for relative_path, record in files.items():
        if (
            not isinstance(record, dict)
            or type(record.get("size_bytes")) is not int
            or record["size_bytes"] <= 0
            or not isinstance(record.get("sha256"), str)
            or _SHA256.fullmatch(record["sha256"]) is None
        ):
            return False
        file_path = _safe_model_path(root, relative_path)
        if not file_path.is_file() or file_path.is_symlink():
            return False
        if file_path.stat().st_size != record["size_bytes"]:
            return False
    return manifest.get("total_bytes") == sum(
        record["size_bytes"] for record in files.values()
    )


def _safe_model_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise WorkerContractError("LTX_MODEL_PATH_INVALID")
    resolved_root = root.resolve()
    lexical = resolved_root / candidate
    current = resolved_root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise WorkerContractError("LTX_MODEL_PATH_INVALID")
    resolved = lexical.resolve(strict=False)
    if not resolved.is_relative_to(resolved_root):
        raise WorkerContractError("LTX_MODEL_PATH_INVALID")
    return resolved


def _safe_attempt_root(attempt_prefix: str) -> Path:
    parts = Path(attempt_prefix).parts
    if (
        len(parts) != 5
        or parts[:2] != ("sketch2life", "dev")
        or any(_OPAQUE_ID.fullmatch(item) is None for item in parts[2:])
    ):
        raise WorkerContractError("VIDEO_ATTEMPT_PATH_INVALID")
    root = Path(SCRATCH_MOUNT).resolve()
    attempt_root = (root / Path(*parts)).resolve(strict=False)
    if not attempt_root.is_relative_to(root):
        raise WorkerContractError("VIDEO_ATTEMPT_PATH_INVALID")
    return attempt_root


def _safe_attempt_file(
    root: Path, relative: str, *, create_parent: bool = False
) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise WorkerContractError("VIDEO_ATTEMPT_PATH_INVALID")
    resolved_root = root.resolve(strict=False)
    lexical = resolved_root / candidate
    current = resolved_root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise WorkerContractError("VIDEO_ATTEMPT_PATH_INVALID")
    path = lexical.resolve(strict=False)
    if not path.is_relative_to(resolved_root):
        raise WorkerContractError("VIDEO_ATTEMPT_PATH_INVALID")
    if create_parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_bounded(path: Path, limit: int, error_code: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise WorkerContractError("VIDEO_INPUT_FILE_NOT_FOUND")
    size = path.stat().st_size
    if size <= 0 or size > limit:
        raise WorkerContractError(error_code)
    try:
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
    except OSError:
        raise WorkerContractError("VIDEO_INPUT_READ_FAILED") from None
    if len(data) != size or len(data) > limit:
        raise WorkerContractError(error_code)
    return data


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_ltx_code_commit() -> str:
    path = Path("/opt/LTX-2/LTX_CODE_COMMIT")
    try:
        commit = path.read_text(encoding="ascii").strip()
    except OSError:
        return "CODE_COMMIT_UNAVAILABLE"
    return commit if commit == PINNED_LTX_CODE_COMMIT else "CODE_COMMIT_MISMATCH"


def _read_ltx_dependency_lock_sha256() -> str | None:
    digest_path = Path("/opt/LTX-2/LTX_UV_LOCK_SHA256")
    lock_path = Path("/opt/LTX-2/uv.lock")
    try:
        expected = digest_path.read_text(encoding="ascii").strip()
    except OSError:
        return None
    if _SHA256.fullmatch(expected) is None or not lock_path.is_file():
        return None
    try:
        actual = _sha256_file(lock_path)
    except OSError:
        return None
    return expected if actual == expected else None


_PIPELINE: Any | None = None
_PROFILES = ProfileSwitch()
_DECODER_COMPILED = False
_PREFETCH: threading.Thread | None = None
_CHECKPOINTS_READ = threading.Event()
