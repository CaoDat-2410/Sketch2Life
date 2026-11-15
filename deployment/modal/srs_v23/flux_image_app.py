"""Dev-only FLUX.3 image workers for generic sketch and lesson visuals."""

from __future__ import annotations

import gc
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

import modal

_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from contracts import (
    WORKER_OUTPUT_SCHEMA,
    ModalWorkerInputV1,
    WorkerContractError,
    is_worker_warmup,
    parse_worker_input,
    worker_warmup_result,
)
from worker_observability import (
    observed_worker,
    refresh_worker_volume,
    worker_phase,
    worker_stage,
)

APP_NAME = "sketch2life-srs23-flux-image-dev"
_GUIDE_PANEL_MIN_INK_COVERAGE = 0.0015
_GUIDE_PANEL_MAX_INK_COVERAGE = 0.32
_GUIDE_MIN_ADDITIONAL_COVERAGE = 0.0002
_GUIDE_MIN_RETAINED_PREVIOUS_STROKES = 0.20
_GUIDE_HARD_RETAINED_STROKES_FLOOR = 0.08
_GUIDE_MIN_PROGRESSIVE_TRANSITION_FRACTION = 0.50
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
_CACHED_FLUX_PIPELINE: Any | None = None
_CACHED_PUP_MODEL: Any | None = None
_CACHED_PUP_PROCESSOR: Any | None = None

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
health_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi>=0.115,<1")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .add_local_file(str(_observability_file), "/root/worker_observability.py", copy=True)
)


@app.function(
    name="health-api",
    image=health_image,
    cpu=0.25,
    memory=256,
    max_containers=1,
    scaledown_window=15,
    timeout=20,
)
@modal.asgi_app()
def health_api():
    """Expose a tiny control-plane health route without requesting a GPU."""

    from fastapi import FastAPI

    api = FastAPI()

    @api.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "app": APP_NAME,
            "health_scope": "deployed-app",
            "gpu_allocated": False,
            "inference_executed": False,
        }

    return api

_download_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .add_local_file(str(_observability_file), "/root/worker_observability.py", copy=True)
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
@observed_worker(
    workload="model.download.flux3",
    model_id=MODEL_ID,
    model_revision=MODEL_REVISION,
)
def download_flux_model() -> dict[str, str]:
    """Stage both immutable FLUX.3 checkpoints in the existing dev Volume."""

    with worker_phase("model_policy_check"):
        _require_flux3_enabled()

    from huggingface_hub import snapshot_download

    marker = Path(MODEL_MARKER)
    model_path = Path(MODEL_DIR)
    pup_path = Path(PUP_DIR)
    with worker_phase("model_volume_reload"):
        model_volume.reload()
    if marker.is_file():
        record = json.loads(marker.read_text(encoding="utf-8"))
        with worker_phase("checkpoint_validation"):
            _verify_record(record)
            checkpoint_is_complete = _checkpoint_is_complete(model_path, pup_path)
        if checkpoint_is_complete:
            return {
                "status": "already_present",
                "model_id": MODEL_ID,
                "revision": MODEL_REVISION,
                "prompt_upsampler_id": PUP_MODEL_ID,
                "prompt_upsampler_revision": PUP_MODEL_REVISION,
            }

    token = os.environ.get(HF_AUTH_ENV_KEY)
    with worker_phase("credential_presence_check"):
        if not token:
            raise RuntimeError("MODAL_HF_TOKEN_MISSING")
    model_path.mkdir(parents=True, exist_ok=True)
    pup_path.mkdir(parents=True, exist_ok=True)
    with worker_phase("main_checkpoint_download"):
        snapshot_download(
            repo_id=MODEL_ID,
            revision=MODEL_REVISION,
            local_dir=str(model_path),
            token=token,
            allow_patterns=list(MODEL_ALLOW_PATTERNS),
        )
    with worker_phase("prompt_upsampler_download"):
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
    with worker_phase("checkpoint_validation"):
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
    with worker_phase("model_manifest_write"):
        marker.write_text(
            json.dumps(record, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
    with worker_phase("model_volume_commit"):
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

    if is_worker_warmup(payload):
        with worker_phase("warmup_feature_and_checkpoint_gate"):
            _require_flux3_enabled()
            _verify_marker()
        with worker_phase("warmup_model_load"):
            gpu_allocated = _warm_flux3_models()
        return worker_warmup_result(
            workload="parent.sketch-guide.generate",
            model_id=MODEL_ID,
            model_revision=MODEL_REVISION,
            gpu_allocated=gpu_allocated,
        )

    with worker_phase("feature_gate"):
        _require_flux3_enabled()
    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "parent.sketch-guide.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
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
    panel_layout = _progressive_panel_layout(data["step_count"])
    worker_stage("gpu_preflight")
    image, expanded_prompt_sha256 = _generate_flux3_image(
        prompt=prompt,
        height=panel_layout["rows"] * 384,
        width=panel_layout["columns"] * 384,
        seed=int(hashlib.sha256(data["topic"].strip().casefold().encode()).hexdigest()[:8], 16),
    )
    with worker_phase("progressive_panel_quality_gate"):
        _validate_progressive_panels(image, data["step_count"], panel_layout)
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
        "panel_layout": panel_layout,
        "stages": [
            {"step_index": index + 1, "row": index // panel_layout["columns"], "column": index % panel_layout["columns"]}
            for index in range(data["step_count"])
        ],
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

    if is_worker_warmup(payload):
        with worker_phase("warmup_feature_and_checkpoint_gate"):
            _require_flux3_enabled()
            _verify_marker()
        with worker_phase("warmup_model_load"):
            gpu_allocated = _warm_flux3_models()
        return worker_warmup_result(
            workload="lesson.visual.generate",
            model_id=MODEL_ID,
            model_revision=MODEL_REVISION,
            gpu_allocated=gpu_allocated,
        )

    with worker_phase("feature_gate"):
        _require_flux3_enabled()
    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "lesson.visual.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request)
    with worker_phase("approved_lesson_contract_validation"):
        _validate_lesson_visual_input(data)
    with worker_phase("checkpoint_verification"):
        _verify_marker()

    prompt = _lesson_visual_scene_request(data)
    panel_layout = _progressive_panel_layout(len(data["steps"]))
    worker_stage("gpu_preflight")
    image, expanded_prompt_sha256 = _generate_flux3_image(
        prompt=prompt,
        height=panel_layout["rows"] * 384,
        width=panel_layout["columns"] * 384,
        seed=int(data["content_hash"][:8], 16),
    )
    with worker_phase("progressive_panel_quality_gate"):
        _validate_progressive_panels(image, len(data["steps"]), panel_layout)
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
        "panel_layout": panel_layout,
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
        or not 4 <= data["step_count"] <= 8
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
        or not 4 <= len(data["steps"]) <= 8
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
    layout = _progressive_panel_layout(step_count)
    return (
        "Create a child-friendly drawing lesson as a strict storyboard grid. The image has "
        f"{layout['columns']} columns and {layout['rows']} rows, read left-to-right then top-to-bottom. "
        f"Fill exactly the first {step_count} panels; leave any unused final cell blank. Topic: "
        f"{topic.strip()!r}; difficulty: {difficulty}. Every panel must show the same subject in "
        "the same position and scale. PROGRESSION IS REQUIRED: panel 1 contains only a few "
        "large construction shapes; each next panel repeats all earlier construction strokes "
        "in the same positions and adds only a few new structural strokes; the last panel has a "
        "clear, recognizable complete subject. For an animal, build head/body/neck or limbs and "
        "other defining anatomy before adding small decorative details. Never draw an almost "
        "finished outline in an early panel and use later panels only for decoration. Use clear "
        "black dashed tracing strokes on a pure white background, no color, no shading, no scene, "
        "no extra subjects, no child, no hand, no text, no panel numbers, no borders, and no watermark."
    )


def _lesson_visual_scene_request(data: dict[str, Any]) -> str:
    steps = "\n".join(
        f"Panel {step['step_index']}: draw {step['instruction']}; place it {step['placement']}."
        for step in data["steps"]
    )
    layout = _progressive_panel_layout(len(data["steps"]))
    return (
        "Create a clean white-background educational drawing guide as a strict storyboard grid. "
        f"It has {layout['columns']} columns and {layout['rows']} rows, read left-to-right then top-to-bottom, "
        f"with exactly {len(data['steps'])} equal panels. Topic: "
        f"{data['topic'].strip()}. Preserve the approved panel count, order, and meaning "
        "exactly; do not add or remove drawing steps. Every panel must repeat all earlier "
        "structural strokes in the same positions and add only the next approved construction "
        "strokes. Major body parts and recognizable anatomy must be complete before decorative "
        "detail. Use black dashed tracing strokes on pure white, no colors, shading, extra scene, "
        "labels, text, panel borders or watermark. Reviewed drawing steps:\n"
        f"{steps}\n"
        "Use simple dark pencil outlines, no color fill, no shading, no background scene, "
        "no people, no child, no extra objects, no readable text, no labels, no numbers, "
        "and no watermark. This is a generic teaching illustration, not a child's artwork."
    )


def _progressive_panel_layout(step_count: int) -> dict[str, Any]:
    if not 4 <= step_count <= 8:
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    columns = 2 if step_count <= 4 else 3 if step_count <= 6 else 4
    rows = math.ceil(step_count / columns)
    return {
        "schema_version": "sketch2life.progressive-guide-layout.v1",
        "columns": columns,
        "rows": rows,
        "step_count": step_count,
        "reading_order": "ROW_MAJOR",
        "stages": [
            {"step_index": index + 1, "row": index // columns, "column": index % columns}
            for index in range(step_count)
        ],
    }


def _validate_progressive_panels(
    image: Any, step_count: int, layout: dict[str, Any]
) -> None:
    """Reject blank, non-progressive or materially redrawn FLUX guide panels."""

    from PIL import ImageChops, ImageFilter

    columns = int(layout["columns"])
    rows = int(layout["rows"])
    panel_width = image.width // columns
    panel_height = image.height // rows
    if (
        image.width != panel_width * columns
        or image.height != panel_height * rows
        or panel_width < 256
        or panel_height < 256
    ):
        raise WorkerContractError("MODAL_PROGRESSIVE_GUIDE_LAYOUT_INVALID")

    previous_mask = None
    previous_coverage = 0.0
    progressive_transition_count = 0
    low_retention_transition_count = 0
    for index in range(step_count):
        row, column = divmod(index, columns)
        left = column * panel_width
        top = row * panel_height
        inset_x = max(2, int(panel_width * 0.06))
        inset_y = max(2, int(panel_height * 0.06))
        panel = image.convert("L").crop(
            (left + inset_x, top + inset_y, left + panel_width - inset_x, top + panel_height - inset_y)
        )
        mask = panel.point(lambda value: 255 if value < 205 else 0, mode="L")
        histogram = mask.histogram()
        ink_pixels = sum(histogram[1:])
        total_pixels = panel.width * panel.height
        coverage = ink_pixels / total_pixels
        if not _GUIDE_PANEL_MIN_INK_COVERAGE <= coverage <= _GUIDE_PANEL_MAX_INK_COVERAGE:
            raise WorkerContractError("MODAL_PROGRESSIVE_GUIDE_PANEL_INK_INVALID")
        if previous_mask is not None:
            # FLUX may move an accumulated line by several pixels between panels.
            # A 15px neighborhood at this panel scale allows moderate drift while
            # retaining a 20% soft target. An eight-step guide may contain one
            # transition down to the 8% hard floor; other guides keep the 20% floor.
            retained_strokes = previous_mask.filter(ImageFilter.MaxFilter(15))
            overlap = ImageChops.multiply(retained_strokes, mask).histogram()
            retained = sum(overlap[1:]) / max(1, sum(previous_mask.histogram()[1:]))
            hard_floor = (
                _GUIDE_HARD_RETAINED_STROKES_FLOOR
                if step_count == 8
                else _GUIDE_MIN_RETAINED_PREVIOUS_STROKES
            )
            print(
                json.dumps(
                    {
                        "event": "progressive_panel_transition_quality",
                        "transition_index": index,
                        "measured_overlap": round(retained, 4),
                        "soft_threshold": _GUIDE_MIN_RETAINED_PREVIOUS_STROKES,
                        "hard_floor": hard_floor,
                        "previous_coverage": round(previous_coverage, 6),
                        "current_coverage": round(coverage, 6),
                    },
                    separators=(",", ":"),
                ),
                flush=True,
            )
            if retained < hard_floor:
                raise WorkerContractError("MODAL_PROGRESSIVE_GUIDE_STROKES_CHANGED")
            if retained < _GUIDE_MIN_RETAINED_PREVIOUS_STROKES:
                low_retention_transition_count += 1
                if step_count != 8 or low_retention_transition_count > 1:
                    raise WorkerContractError("MODAL_PROGRESSIVE_GUIDE_STROKES_CHANGED")
            # FLUX can vary panel detail and stroke weight. Measure new ink with
            # only a 2px antialias tolerance; don't require every transition to
            # grow. The whole sequence must still show meaningful progress.
            novelty_reference = previous_mask.filter(ImageFilter.MaxFilter(5))
            added_ink = ImageChops.subtract(mask, novelty_reference).histogram()
            added_coverage = sum(added_ink[1:]) / total_pixels
            if added_coverage >= _GUIDE_MIN_ADDITIONAL_COVERAGE:
                progressive_transition_count += 1
        previous_mask = mask
        previous_coverage = coverage

    transition_count = max(1, step_count - 1)
    minimum_progressive_transitions = max(
        1,
        math.ceil(transition_count * _GUIDE_MIN_PROGRESSIVE_TRANSITION_FRACTION),
    )
    if progressive_transition_count < minimum_progressive_transitions:
        raise WorkerContractError("MODAL_PROGRESSIVE_GUIDE_NOT_CUMULATIVE")


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

    with worker_phase("flux_model_load"):
        pipeline = _load_flux3_pipeline(torch)
    try:
        pipeline.to("cuda")
        with worker_phase("flux_image_inference"), torch.inference_mode():
            image = pipeline(
                prompt=caption,
                height=height,
                width=width,
                generator=torch.Generator(device="cuda").manual_seed(seed),
                output="images",
            )[0]
    finally:
        pipeline.to("cpu")
        gc.collect()
        torch.cuda.empty_cache()
    return image, caption_hash


def _load_flux3_pipeline(torch: Any) -> Any:
    """Load and retain FLUX weights in CPU RAM for this worker container."""

    global _CACHED_FLUX_PIPELINE
    if _CACHED_FLUX_PIPELINE is not None:
        return _CACHED_FLUX_PIPELINE

    from diffusers import ModularPipeline

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
    pipeline.load_components(
        dtype={"vae": torch.float32, "default": torch.bfloat16},
        local_files_only=True,
    )
    _CACHED_FLUX_PIPELINE = pipeline
    return pipeline


def _load_prompt_upsampler(torch: Any) -> tuple[Any, Any]:
    """Load and retain BFL's prompt model on CPU; inference moves it temporarily."""

    global _CACHED_PUP_MODEL, _CACHED_PUP_PROCESSOR
    if _CACHED_PUP_MODEL is not None and _CACHED_PUP_PROCESSOR is not None:
        return _CACHED_PUP_PROCESSOR, _CACHED_PUP_MODEL

    from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration

    _CACHED_PUP_PROCESSOR = AutoProcessor.from_pretrained(
        PUP_DIR, local_files_only=True
    )
    _CACHED_PUP_MODEL = Qwen3_5ForConditionalGeneration.from_pretrained(
        PUP_DIR,
        dtype=torch.bfloat16,
        local_files_only=True,
    ).eval()
    return _CACHED_PUP_PROCESSOR, _CACHED_PUP_MODEL


def _warm_flux3_models() -> bool:
    """Load model weights without running prompt or image generation."""

    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    _load_flux3_pipeline(torch)
    _, prompt_model = _load_prompt_upsampler(torch)
    prompt_model.to("cuda")
    prompt_model.to("cpu")
    _CACHED_FLUX_PIPELINE.to("cuda")
    _CACHED_FLUX_PIPELINE.to("cpu")
    gc.collect()
    torch.cuda.empty_cache()
    return True


def _upsample_prompt(prompt: str, torch: Any) -> str:
    """Expand the short request with BFL's pinned Qwen3.5 prompt upsampler."""

    processor, model = _load_prompt_upsampler(torch)
    model.to("cuda")
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
    del inputs, output_ids
    model.to("cpu")
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
