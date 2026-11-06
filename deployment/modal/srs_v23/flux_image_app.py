"""Dev-only FLUX.3 image workers for generic sketch and lesson visuals."""

from __future__ import annotations

import gc
import hashlib
import json
import os
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
from worker_observability import (  # noqa: E402
    observed_worker,
    worker_phase,
    worker_stage,
)

APP_NAME = "sketch2life-srs23-flux-image-dev"
MODEL_ID = "black-forest-labs/flux-3-image-klein"
MODEL_REVISION = "09561231f44e41381c461caf53d5452005a60ac9"
PUP_MODEL_ID = "black-forest-labs/flux-3-image-klein-pup"
PUP_MODEL_REVISION = "a57899549f8f6f64c6c4d88db30827d496ff76d0"
MODEL_LICENSE = "FLUX Kommunity License v1.0"
PUP_LICENSE = "Apache-2.0"
FLUX3_ENABLED = True
HF_CREDENTIAL_RESOURCE_NAME = "huggingface-secret"
HF_AUTH_ENV_KEY = "HF_TOKEN"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
MODEL_ROOT = f"{MODEL_MOUNT}/flux_3_image_klein/{MODEL_REVISION}"
MODEL_DIR = f"{MODEL_ROOT}/image"
PUP_DIR = f"{MODEL_ROOT}/prompt_upsampler"
MODEL_MARKER = f"{MODEL_ROOT}/sketch2life-model-manifest.json"
INPUT_SCHEMA = "sketch2life.modal.ai-request.v1"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
MODEL_REQUIRED_FILES = (
    "modular_model_index.json",
    "model.safetensors",
    "ae.safetensors",
    "text_encoder/config.json",
    "text_encoder/model-00001-of-00002.safetensors",
    "text_encoder/model-00002-of-00002.safetensors",
    "transformer/config.json",
    "transformer/diffusion_pytorch_model-00001-of-00002.safetensors",
    "transformer/diffusion_pytorch_model-00002-of-00002.safetensors",
    "transformer/diffusion_pytorch_model.safetensors.index.json",
    "vae/config.json",
    "vae/diffusion_pytorch_model.safetensors",
)
PUP_REQUIRED_FILES = (
    "config.json",
    "generation_config.json",
    "chat_template.jinja",
    "preprocessor_config.json",
    "processor_config.json",
    "system_prompts.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "model.safetensors",
)
MODEL_ALLOW_PATTERNS = (
    "LICENSE.md",
    "NOTICE.md",
    "config.json",
    "manifest.json",
    "modular_model_index.json",
    "model.safetensors",
    "ae.safetensors",
    "text_encoder/*",
    "transformer/*",
    "vae/*",
)
_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")
_TOPIC = re.compile(r"\A[^\r\n\x00]{1,120}\Z")

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
_observability_file = _MODULE_DIR / "worker_observability.py"
_download_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .pip_install("huggingface_hub==1.32.0")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1"})
)
_inference_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .add_local_file(str(_observability_file), "/root/worker_observability.py", copy=True)
    .uv_pip_install("torch==2.7.1", "torchvision==0.22.1")
    .uv_pip_install(
        "diffusers==0.42.1",
        "transformers==5.22.1",
        "accelerate==1.15.0",
        "huggingface_hub==1.32.0",
        "Pillow==11.2.1",
        "safetensors==0.8.0",
    )
    .env(
        {
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "HF_HOME": f"{MODEL_MOUNT}/huggingface-cache",
            "HF_HUB_OFFLINE": "1",
        }
    )
)


@app.function(
    name="download-flux-pinned-model",
    image=_download_image,
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
    timeout=3_600,
    retries=0,
)
def download_flux_model() -> dict[str, str]:
    """Stage both immutable FLUX.3 checkpoints in the existing dev Volume."""

    _require_flux3_enabled()

    from huggingface_hub import snapshot_download

    marker = Path(MODEL_MARKER)
    model_path = Path(MODEL_DIR)
    pup_path = Path(PUP_DIR)
    model_volume.reload()
    if marker.is_file():
        record = json.loads(marker.read_text(encoding="utf-8"))
        _verify_record(record)
        if _checkpoint_is_complete(model_path, pup_path):
            return {
                "status": "already_present",
                "model_id": MODEL_ID,
                "revision": MODEL_REVISION,
                "prompt_upsampler_id": PUP_MODEL_ID,
                "prompt_upsampler_revision": PUP_MODEL_REVISION,
            }

    token = os.environ.get(HF_AUTH_ENV_KEY)
    if not token:
        raise RuntimeError("MODAL_HF_TOKEN_MISSING")
    model_path.mkdir(parents=True, exist_ok=True)
    pup_path.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=str(model_path),
        token=token,
        allow_patterns=list(MODEL_ALLOW_PATTERNS),
    )
    snapshot_download(
        repo_id=PUP_MODEL_ID,
        revision=PUP_MODEL_REVISION,
        local_dir=str(pup_path),
        token=token,
        allow_patterns=[
            "config.json",
            "generation_config.json",
            "chat_template.jinja",
            "preprocessor_config.json",
            "processor_config.json",
            "system_prompts.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "model.safetensors",
        ],
    )
    _verify_checkpoint(model_path, pup_path)
    record = {
        "schema_version": "sketch2life.modal.model-manifest.v1",
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "license": MODEL_LICENSE,
        "prompt_upsampler_id": PUP_MODEL_ID,
        "prompt_upsampler_revision": PUP_MODEL_REVISION,
        "prompt_upsampler_license": PUP_LICENSE,
        "prompt_upsampler_mode": "transformers-sequential-before-image-model",
    }
    marker.write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    model_volume.commit()
    return {
        "status": "downloaded",
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "prompt_upsampler_id": PUP_MODEL_ID,
        "prompt_upsampler_revision": PUP_MODEL_REVISION,
    }


@app.function(
    name="generate-line-sketch-guide-candidate",
    image=_inference_image,
    gpu="L40S",
    cpu=4.0,
    memory=40_960,
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
@observed_worker(
    workload="parent.sketch-guide.generate",
    model_id=MODEL_ID,
    model_revision=MODEL_REVISION,
    gpu_class="L40S",
)
def generate_line_sketch_guide_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate a generic, non-child-specific step guide as a private candidate."""

    with worker_phase("feature_gate"):
        _require_flux3_enabled()
    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "parent.sketch-guide.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request)
    with worker_phase("guide_request_validation"):
        _validate_sketch_guide_input(data)
    with worker_phase("checkpoint_verification"):
        _verify_marker()

    prompt = _sketch_guide_scene_request(
        topic=data["topic"],
        difficulty=data["difficulty"],
        step_count=data["step_count"],
    )
    worker_stage("gpu_preflight")
    image, expanded_prompt_sha256 = _generate_flux3_image(
        prompt=prompt,
        height=512,
        width=768,
        seed=20261105,
    )
    with worker_phase("image_encode_and_metadata"):
        image_bytes = _encode_png(image)
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": _model_provenance(),
        "prompt_sha256": expanded_prompt_sha256,
        "asset": _asset_metadata(image, image_bytes),
        "status": "DRAFT",
        "review_required": True,
        "limitations": [
            "synthetic candidate only; line-step ordering and child usability are unevaluated",
            "not safety-approved, not registered as a product asset, and not publishable",
            "no child, profile, drawing, voice, or image reference was used",
        ],
    }


@app.function(
    name="generate-approved-lesson-visual-candidate",
    image=_inference_image,
    gpu="L40S",
    cpu=4.0,
    memory=40_960,
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
@observed_worker(
    workload="lesson.visual.generate",
    model_id=MODEL_ID,
    model_revision=MODEL_REVISION,
    gpu_class="L40S",
)
def generate_approved_lesson_visual_candidate(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Generate an unapproved visual from a reviewed lesson revision."""

    with worker_phase("feature_gate"):
        _require_flux3_enabled()
    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "lesson.visual.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request)
    with worker_phase("approved_lesson_contract_validation"):
        _validate_lesson_visual_input(data)
    with worker_phase("checkpoint_verification"):
        _verify_marker()

    prompt = _lesson_visual_scene_request(data)
    worker_stage("gpu_preflight")
    image, expanded_prompt_sha256 = _generate_flux3_image(
        prompt=prompt,
        height=432,
        width=768,
        seed=20261105,
    )
    with worker_phase("image_encode_and_metadata"):
        image_bytes = _encode_png(image)
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": _model_provenance(),
        "prompt_sha256": expanded_prompt_sha256,
        "plan_revision_ref": data["plan_revision_ref"],
        "content_hash": data["content_hash"],
        "status": "DRAFT",
        "review_required": True,
        "asset": _asset_metadata(image, image_bytes),
        "limitations": [
            "synthetic lesson candidate; exact visual fidelity to approved steps is unevaluated",
            "not safety-approved, not registered as a product asset, and not publishable",
            "source lesson text and approved revision/hash are retained as provenance",
        ],
    }


def _require_flux3_enabled() -> None:
    if not FLUX3_ENABLED:
        raise RuntimeError("MODAL_FLUX3_IMPLEMENTATION_NOT_READY")


def _validate_sketch_guide_input(data: dict[str, Any]) -> None:
    if set(data) != {"topic", "difficulty", "step_count"}:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    topic = data.get("topic")
    if (
        not isinstance(topic, str)
        or not _TOPIC.fullmatch(topic.strip())
        or data.get("difficulty") not in {"beginner", "simple"}
        or type(data.get("step_count")) is not int
        or not 3 <= data["step_count"] <= 5
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")


def _validate_lesson_visual_input(data: dict[str, Any]) -> None:
    if set(data) != {
        "schema_version",
        "plan_revision_ref",
        "content_hash",
        "topic",
        "steps",
    }:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if (
        data.get("schema_version") != "sketch2life.lesson-visual-input.v1"
        or not isinstance(data.get("plan_revision_ref"), str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", data["plan_revision_ref"])
        or not isinstance(data.get("content_hash"), str)
        or _SHA256.fullmatch(data["content_hash"]) is None
        or not isinstance(data.get("topic"), str)
        or not _TOPIC.fullmatch(data["topic"].strip())
        or not isinstance(data.get("steps"), list)
        or not 3 <= len(data["steps"]) <= 5
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    for index, step in enumerate(data["steps"], start=1):
        if (
            not isinstance(step, dict)
            or set(step) != {"step_index", "instruction", "placement"}
            or type(step.get("step_index")) is not int
            or step["step_index"] != index
            or any(
                not isinstance(step.get(key), str)
                or not step[key].strip()
                or len(step[key]) > 200
                for key in ("instruction", "placement")
            )
        ):
            raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")


def _sketch_guide_scene_request(
    *, topic: str, difficulty: str, step_count: int
) -> str:
    return (
        "Create a child-friendly educational drawing worksheet as one wide horizontal "
        f"image with exactly {step_count} equal panels in left-to-right order. The topic "
        f"is {topic.strip()!r}; drawing difficulty is {difficulty}. Show the same simple, "
        "recognizable subject progressively built across panels, adding only a small number "
        "of clear pencil-outline strokes in each next panel. Keep every panel large, separate, "
        "and visually consistent. Use a pure white background, clean thin black line art, "
        "no color, no shading, no scene background, no extra subjects, no child, no hand, "
        "no readable text, no labels, no numbers, and no watermark."
    )


def _lesson_visual_scene_request(data: dict[str, Any]) -> str:
    steps = "\n".join(
        f"Panel {step['step_index']}: draw {step['instruction']}; place it {step['placement']}."
        for step in data["steps"]
    )
    return (
        "Create one clean white-background, horizontal educational drawing guide with "
        f"exactly {len(data['steps'])} equal panels in left-to-right order. Topic: "
        f"{data['topic'].strip()}. Preserve the approved panel count, order, and meaning "
        "exactly; do not add or remove drawing steps. Use the same simple subject in each "
        "panel and progressively add only the approved strokes. Reviewed drawing steps:\n"
        f"{steps}\n"
        "Use simple dark pencil outlines, no color fill, no shading, no background scene, "
        "no people, no child, no extra objects, no readable text, no labels, no numbers, "
        "and no watermark. This is a generic teaching illustration, not a child's artwork."
    )


def _generate_flux3_image(
    *, prompt: str, height: int, width: int, seed: int
) -> tuple[Any, str]:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")

    with worker_phase("prompt_upsampler_inference"):
        caption = _upsample_prompt(prompt, torch)
    caption_hash = hashlib.sha256(caption.encode("utf-8")).hexdigest()
    gc.collect()
    torch.cuda.empty_cache()

    from diffusers import ModularPipeline

    with worker_phase("flux_model_load"):
        pipeline_spec = ModularPipeline.from_pretrained(
            MODEL_DIR,
            local_files_only=True,
        )
        blocks = pipeline_spec.blocks
        if "prompt_upsampler" not in blocks.sub_blocks:
            raise RuntimeError("MODAL_FLUX3_PROMPT_UPSAMPLER_BLOCK_MISSING")
        blocks.sub_blocks.pop("prompt_upsampler")
        pipeline = blocks.init_pipeline(MODEL_DIR)
        del pipeline_spec, blocks
        gc.collect()
        torch.cuda.empty_cache()

        pipeline.load_components(
            dtype={"vae": torch.float32, "default": torch.bfloat16},
            local_files_only=True,
        )
        pipeline.to("cuda")
    with worker_phase("flux_image_inference"), torch.inference_mode():
        image = pipeline(
            prompt=caption,
            height=height,
            width=width,
            generator=torch.Generator(device="cuda").manual_seed(seed),
            output="images",
        )[0]
    del pipeline
    gc.collect()
    torch.cuda.empty_cache()
    return image, caption_hash


def _upsample_prompt(prompt: str, torch: Any) -> str:
    """Expand the short request with BFL's pinned Qwen3.5 prompt upsampler."""

    from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration

    processor = AutoProcessor.from_pretrained(PUP_DIR, local_files_only=True)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        PUP_DIR,
        dtype=torch.bfloat16,
        local_files_only=True,
    ).to("cuda").eval()
    system_prompts = json.loads(
        (Path(PUP_DIR) / "system_prompts.json").read_text(encoding="utf-8")
    )
    system_prompt = system_prompts.get("t2i")
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        raise RuntimeError("MODAL_FLUX3_PROMPT_UPSAMPLER_PROMPT_MISSING")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        enable_thinking=False,
    ).to(model.device)
    with torch.inference_mode():
        output_ids = model.generate(**inputs, max_new_tokens=512, do_sample=False)
    caption = processor.decode(
        output_ids[0, inputs["input_ids"].shape[1] :],
        skip_special_tokens=True,
    ).strip()
    if not 80 <= len(caption) <= 8_000 or "\x00" in caption:
        raise RuntimeError("MODAL_FLUX3_PROMPT_UPSAMPLER_OUTPUT_INVALID")
    del model, processor, inputs, output_ids
    gc.collect()
    torch.cuda.empty_cache()
    return caption


def _encode_png(image: Any) -> bytes:
    import io

    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=True)
    image_bytes = output.getvalue()
    if (
        not image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        or len(image_bytes) > MAX_OUTPUT_BYTES
    ):
        raise RuntimeError("MODAL_OUTPUT_INVALID")
    return image_bytes


def _asset_metadata(image: Any, image_bytes: bytes) -> dict[str, Any]:
    return {
        "content_type": "image/png",
        "size_bytes": len(image_bytes),
        "sha256": hashlib.sha256(image_bytes).hexdigest(),
        "width": image.width,
        "height": image.height,
        "bytes": image_bytes,
    }


def _model_provenance() -> dict[str, dict[str, str]]:
    return {
        "image_generator": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "prompt_upsampler": {
            "id": PUP_MODEL_ID,
            "revision": PUP_MODEL_REVISION,
        },
    }


def _read_json_asset(request: ModalWorkerInputV1) -> dict[str, Any]:
    root = Path(SCRATCH_MOUNT).resolve()
    attempt_dir = (root / request.attempt_prefix.rstrip("/")).resolve()
    if not attempt_dir.is_relative_to(root):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    manifest_path = (attempt_dir / "input/manifest.json").resolve()
    asset_path = (attempt_dir / "input/request.json").resolve()
    if not manifest_path.is_relative_to(attempt_dir) or not asset_path.is_relative_to(
        attempt_dir
    ):
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
    _verify_record(json.loads(path.read_text(encoding="utf-8")))
    _verify_checkpoint(Path(MODEL_DIR), Path(PUP_DIR))


def _verify_record(record: dict[str, Any]) -> None:
    if (
        record.get("schema_version") != "sketch2life.modal.model-manifest.v1"
        or record.get("model_id") != MODEL_ID
        or record.get("revision") != MODEL_REVISION
        or record.get("prompt_upsampler_id") != PUP_MODEL_ID
        or record.get("prompt_upsampler_revision") != PUP_MODEL_REVISION
        or record.get("prompt_upsampler_mode")
        != "transformers-sequential-before-image-model"
    ):
        raise RuntimeError("MODAL_MODEL_REVISION_MARKER_MISMATCH")


def _verify_checkpoint(model_path: Path, pup_path: Path) -> None:
    if any(not (model_path / name).is_file() for name in MODEL_REQUIRED_FILES) or any(
        not (pup_path / name).is_file() for name in PUP_REQUIRED_FILES
    ):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")
    if any(
        (model_path / name).stat().st_size <= 0 for name in MODEL_REQUIRED_FILES
    ) or any(
        (pup_path / name).stat().st_size <= 0 for name in PUP_REQUIRED_FILES
    ):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")


def _checkpoint_is_complete(model_path: Path, pup_path: Path) -> bool:
    try:
        _verify_checkpoint(model_path, pup_path)
    except RuntimeError as exc:
        if exc.args == ("MODAL_MODEL_CHECKPOINT_INCOMPLETE",):
            return False
        raise
    return True
