"""Private Modal dev workers for the SRS story, TTS, and ASR POCs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from copy import deepcopy
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
    refresh_worker_volume,
    worker_phase,
    worker_stage,
)

APP_NAME = "sketch2life-srs23-language-audio-dev"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
TEXT_MODEL_ID = "Qwen/Qwen3.5-9B"
TEXT_MODEL_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
TEXT_MODEL_DIR = f"{MODEL_MOUNT}/qwen3_5_9b/{TEXT_MODEL_REVISION}"
TEXT_MODEL_MARKER = f"{TEXT_MODEL_DIR}/sketch2life-model-manifest.json"
ASR_MODEL_ID = "Systran/faster-whisper-large-v3"
ASR_MODEL_REVISION = "edaa852ec7e145841d8ffdb056a99866b5f0a478"
ASR_MODEL_DIR = f"{MODEL_MOUNT}/faster-whisper-large-v3/{ASR_MODEL_REVISION}"
ASR_MODEL_MARKER = f"{ASR_MODEL_DIR}/sketch2life-model-manifest.json"
TTS_MODEL_ID = "pnnbao-ump/VieNeu-TTS-v3-Turbo"
TTS_MODEL_REVISION = "61b85e3d937fbbacb387714180e8182823512523"
TTS_MODEL_DIR = f"{MODEL_MOUNT}/vieneu_tts_v3_turbo/{TTS_MODEL_REVISION}"
TTS_CODEC_ID = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX"
TTS_CODEC_REVISION = "ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae"
TTS_CODEC_DIR = f"{MODEL_MOUNT}/moss_audio_tokenizer_nano_onnx/{TTS_CODEC_REVISION}"
TTS_MODEL_MARKER = f"{TTS_MODEL_DIR}/sketch2life-model-manifest.json"
TTS_CODEC_MARKER = f"{TTS_CODEC_DIR}/sketch2life-model-manifest.json"
INPUT_SCHEMA = "sketch2life.modal.ai-request.v1"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
STORY_GENERATION_BUDGET = 4_096  # measured in output tokens
STORY_WORKER_TIMEOUT_SECONDS = 1_800
_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")


def _lmfe_vietnamese_json_alphabet() -> str:
    """Extend LMFE's ASCII alphabet for Vietnamese letters and punctuation."""

    import unicodedata

    ascii_alphabet = (
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "!@#$%^&*()_+-=[]{};:,./<>? `" + "'\"\\"
    )
    unicode_ranges = (
        (0x00A0, 0x0250),  # Latin-1 and Latin Extended-A/B.
        (0x0300, 0x0370),  # Combining marks used by decomposed Vietnamese text.
        (0x1E00, 0x1F00),  # Latin Extended Additional, including Vietnamese.
        (0x2000, 0x2070),  # Typographic punctuation and spaces.
    )
    additions = [
        chr(codepoint)
        for start, end in unicode_ranges
        for codepoint in range(start, end)
        if unicodedata.category(chr(codepoint))[0] in "LMNPS"
        or unicodedata.category(chr(codepoint)) == "Zs"
    ]
    return "".join(dict.fromkeys(ascii_alphabet + "".join(additions)))


LMFE_VIETNAMESE_JSON_ALPHABET = _lmfe_vietnamese_json_alphabet()

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
    .add_local_file(
        str(_observability_file), "/root/worker_observability.py", copy=True
    )
    .pip_install("huggingface_hub==0.33.4")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1"})
)
_text_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .add_local_file(
        str(_observability_file), "/root/worker_observability.py", copy=True
    )
    .uv_pip_install(
        "torch==2.7.1",
        "torchvision==0.22.1",
        "transformers==5.22.1",
        "accelerate==1.8.1",
        "huggingface_hub==1.32.0",
        "Pillow==11.2.1",
        "lm-format-enforcer==0.11.3",
    )
    .env(
        {
            "HF_HUB_DISABLE_TELEMETRY": "1",
        }
    )
)
_story_text_image = _text_image.env(
    {
        "HF_ENABLE_PARALLEL_LOADING": "true",
        "HF_PARALLEL_LOADING_WORKERS": "4",
        "LMFE_STRICT_JSON_FIELD_ORDER": "true",
    }
)
_tts_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .add_local_file(
        str(_observability_file), "/root/worker_observability.py", copy=True
    )
    .pip_install(
        "vieneu==3.8.3",
        "onnxruntime==1.20.1",
        "numpy<2",
        "soundfile==0.13.1",
        "soxr",
        "kaldi-native-fbank>=1.20",
        "tokenizers>=0.20",
        "huggingface_hub==0.33.5",
    )
    .env({"HF_HUB_DISABLE_TELEMETRY": "1"})
)
_asr_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .add_local_file(
        str(_observability_file), "/root/worker_observability.py", copy=True
    )
    .pip_install("faster-whisper==1.2.1", "huggingface_hub==0.33.4")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1"})
)


@app.function(
    name="download-language-audio-models",
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
@observed_worker(workload="model.download.language_audio")
def download_language_audio_models() -> dict[str, Any]:
    """Download the exact public model revisions used by this POC wave."""

    from huggingface_hub import snapshot_download

    with worker_phase("model_volume_reload"):
        model_volume.reload()
    records = [
        (
            TEXT_MODEL_ID,
            TEXT_MODEL_REVISION,
            Path(TEXT_MODEL_DIR),
            Path(TEXT_MODEL_MARKER),
            "Apache-2.0",
        ),
        (
            ASR_MODEL_ID,
            ASR_MODEL_REVISION,
            Path(ASR_MODEL_DIR),
            Path(ASR_MODEL_MARKER),
            "MIT",
        ),
        (
            TTS_MODEL_ID,
            TTS_MODEL_REVISION,
            Path(TTS_MODEL_DIR),
            Path(TTS_MODEL_MARKER),
            "Apache-2.0",
        ),
        (
            TTS_CODEC_ID,
            TTS_CODEC_REVISION,
            Path(TTS_CODEC_DIR),
            Path(TTS_CODEC_MARKER),
            "Apache-2.0",
        ),
    ]
    results: list[dict[str, str]] = []
    download_stages = {
        TEXT_MODEL_ID: "download_qwen_text_model",
        ASR_MODEL_ID: "download_whisper_asr_model",
        TTS_MODEL_ID: "download_vieneu_tts_model",
        TTS_CODEC_ID: "download_moss_tts_codec",
    }
    checkpoint_stages = {
        TEXT_MODEL_ID: "validate_qwen_text_model",
        ASR_MODEL_ID: "validate_whisper_asr_model",
        TTS_MODEL_ID: "validate_vieneu_tts_model",
        TTS_CODEC_ID: "validate_moss_tts_codec",
    }
    for model_id, revision, model_path, marker_path, license_name in records:
        if marker_path.is_file():
            with worker_phase(checkpoint_stages[model_id]):
                marker = json.loads(marker_path.read_text(encoding="utf-8"))
                if (
                    marker.get("model_id") != model_id
                    or marker.get("revision") != revision
                ):
                    raise RuntimeError("MODAL_MODEL_REVISION_MARKER_MISMATCH")
            results.append(
                {
                    "status": "already_present",
                    "model_id": model_id,
                    "revision": revision,
                }
            )
            continue

        model_path.mkdir(parents=True, exist_ok=True)
        with worker_phase(download_stages[model_id]):
            snapshot_download(
                repo_id=model_id, revision=revision, local_dir=str(model_path)
            )
        with worker_phase("model_manifest_write"):
            marker_path.write_text(
                json.dumps(
                    {
                        "schema_version": "sketch2life.modal.model-manifest.v1",
                        "model_id": model_id,
                        "revision": revision,
                        "license": license_name,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
        results.append(
            {"status": "downloaded", "model_id": model_id, "revision": revision}
        )

    with worker_phase("validate_qwen_text_model"):
        _verify_text_checkpoint(Path(TEXT_MODEL_DIR))
    with worker_phase("validate_whisper_asr_model"):
        _verify_asr_checkpoint(Path(ASR_MODEL_DIR))
    with worker_phase("validate_vieneu_tts_model"):
        _verify_tts_checkpoint(Path(TTS_MODEL_DIR), Path(TTS_CODEC_DIR))
    with worker_phase("model_volume_commit"):
        model_volume.commit()
    return {"status": "ready", "models": results}


@app.function(
    name="check-qwen35-readiness",
    image=_story_text_image,
    gpu=["L40S", "L4", "A10"],
    cpu=2.0,
    memory=16_384,
    volumes={MODEL_MOUNT: model_volume.with_mount_options(read_only=True)},
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=300,
    retries=0,
)
def check_qwen35_readiness() -> dict[str, Any]:
    """Check the pinned Qwen checkpoint, processor/runtime imports and allocated GPU."""

    import torch
    import transformers
    from transformers import AutoModelForMultimodalLM, AutoProcessor

    model_path = Path(TEXT_MODEL_DIR)
    _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    _verify_text_checkpoint(model_path)
    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    processor = AutoProcessor.from_pretrained(
        str(model_path), local_files_only=True, trust_remote_code=False
    )
    properties = torch.cuda.get_device_properties(0)
    return {
        "status": "ready",
        "model_id": TEXT_MODEL_ID,
        "revision": TEXT_MODEL_REVISION,
        "checkpoint_verified": True,
        "processor_class": type(processor).__name__,
        "model_loader": AutoModelForMultimodalLM.__name__,
        "transformers_version": transformers.__version__,
        "gpu_name": properties.name,
        "gpu_total_memory_bytes": properties.total_memory,
    }


@app.function(
    name="generate-story-and-storyboard",
    image=_story_text_image,
    gpu=["L40S", "L4", "A10"],
    cpu=4.0,
    memory=32_768,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume.with_mount_options(read_only=True),
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=120,
    timeout=STORY_WORKER_TIMEOUT_SECONDS,
    retries=0,
)
@observed_worker(
    workload="story.generate",
    model_id=TEXT_MODEL_ID,
    model_revision=TEXT_MODEL_REVISION,
    gpu_class="L40S|L4|A10",
    timeout_seconds=STORY_WORKER_TIMEOUT_SECONDS,
)
def generate_story_and_storyboard(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate one adult-review Parent story revision matching the SRS scene contract."""

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "story.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request, expected_asset="input/request.json")
    worker_stage("request_contract_validation")
    expected = {
        "schema_version",
        "role",
        "language",
        "confirmed_subject",
        "understanding_revision",
        "drawing_sha256",
        "visible_features",
        "child_age_months",
        "context_revision",
        "adult_confirmed_idea",
        "rewrite_instruction",
        "lesson_direction",
    }
    if set(data) != expected:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if (
        data.get("schema_version") != "sketch2life.story-generation-input.v1"
        or data.get("role") != "PARENT"
        or data.get("language") != "vi"
        or not isinstance(data.get("confirmed_subject"), str)
        or not data["confirmed_subject"].strip()
        or not 36 <= data.get("child_age_months", 0) <= 120
        or not isinstance(data.get("understanding_revision"), int)
        or data["understanding_revision"] < 1
        or not isinstance(data.get("context_revision"), int)
        or data["context_revision"] < 1
        or not isinstance(data.get("drawing_sha256"), str)
        or _SHA256.fullmatch(data["drawing_sha256"]) is None
        or not isinstance(data.get("visible_features"), list)
        or not 1 <= len(data["visible_features"]) <= 4
        or any(
            not isinstance(item, str) or not item.strip() or len(item) > 160
            for item in data["visible_features"]
        )
        or not isinstance(data.get("adult_confirmed_idea"), str)
        or len(data["adult_confirmed_idea"]) > 500
        or (
            data.get("rewrite_instruction") is not None
            and (
                not isinstance(data["rewrite_instruction"], str)
                or not 1 <= len(data["rewrite_instruction"]) <= 400
            )
        )
        or data.get("lesson_direction") is not None
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")

    worker_stage("runtime_preparation")
    torch_import_started = time.perf_counter()
    import torch

    torch_import_seconds = time.perf_counter() - torch_import_started
    gpu_name = (
        torch.cuda.get_device_name(0) if torch.cuda.is_available() else "unavailable"
    )
    print(
        json.dumps(
            {
                "event": "story_runtime_ready",
                "gpu_name": gpu_name,
                "torch_import_seconds": round(torch_import_seconds, 3),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    with worker_phase("checkpoint_verification"):
        _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    model_load_started = time.perf_counter()
    with worker_phase("model_load"):
        processor, model = _load_text_model()
    tokenizer = processor.tokenizer
    model_load_seconds = time.perf_counter() - model_load_started
    print(
        json.dumps(
            {
                "event": "story_model_loaded",
                "model_load_seconds": round(model_load_seconds, 3),
            }
        ),
        flush=True,
    )
    prompt = _parent_story_prompt(data)
    messages = [
        {
            "role": "system",
            "content": "Bạn là trợ lý viết nội dung giáo dục ngắn, an toàn và trung thực.",
        },
        {"role": "user", "content": prompt},
    ]
    encode_started = time.perf_counter()
    with worker_phase("prompt_encoding"):
        encoded = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors="pt",
            return_dict=True,
        ).to(model.device)
    input_ids = encoded["input_ids"]
    prompt_encode_seconds = time.perf_counter() - encode_started
    print(
        json.dumps(
            {
                "event": "story_prompt_encoded",
                "prompt_encode_seconds": round(prompt_encode_seconds, 3),
            }
        ),
        flush=True,
    )

    generation_config = deepcopy(model.generation_config)
    generation_config.do_sample = False
    generation_config.temperature = 1.0
    generation_config.top_p = 1.0
    generation_config.top_k = 50
    generation_config.max_new_tokens = STORY_GENERATION_BUDGET
    generation_config.pad_token_id = _generation_pad_token_id(model, tokenizer)
    constraint_started = time.perf_counter()
    with worker_phase("constrained_decoder_setup"):
        prefix_allowed_tokens_fn = _build_story_prefix_allowed_tokens_fn(
            tokenizer,
            eos_token_id=model.generation_config.eos_token_id,
        )
    print(
        json.dumps(
            {
                "event": "story_constraint_ready",
                "constraint_build_seconds": round(
                    time.perf_counter() - constraint_started, 3
                ),
            }
        ),
        flush=True,
    )
    generation_started = time.perf_counter()
    with worker_phase("model_inference"), torch.inference_mode():
        generated = model.generate(
            **encoded,
            generation_config=generation_config,
            prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
        )
    generation_seconds = time.perf_counter() - generation_started
    output_token_count = int(generated.shape[-1] - input_ids.shape[-1])
    with worker_phase("output_decode_and_parse"):
        text = tokenizer.decode(
            generated[0, input_ids.shape[-1] :], skip_special_tokens=True
        )
    try:
        content = _parse_story_content_output(text)
    except StoryOutputValidationError as exc:
        hit_limit = output_token_count >= STORY_GENERATION_BUDGET
        print(
            json.dumps(
                {
                    "event": "story_output_truncated"
                    if hit_limit
                    else "story_output_invalid",
                    "reason_code": exc.reason_code,
                    "generation_seconds": round(generation_seconds, 3),
                    "max_new_tokens": STORY_GENERATION_BUDGET,
                    "token_limit_reached": output_token_count
                    >= STORY_GENERATION_BUDGET,
                    "tokenizer_eos_token_id": tokenizer.eos_token_id,
                    "model_eos_token_id": model.generation_config.eos_token_id,
                    **_generation_output_diagnostics(
                        generated, input_ids.shape[-1], model
                    ),
                    **_json_output_diagnostics(text),
                    **_story_output_field_diagnostics(text),
                    **_json_prefix_decoder_diagnostics(
                        prefix_allowed_tokens_fn,
                        generated=generated,
                        input_token_count=input_ids.shape[-1],
                    ),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if hit_limit:
            raise RuntimeError("MODAL_MODEL_OUTPUT_TRUNCATED") from exc
        raise
    print(
        json.dumps(
            {
                "event": "story_tokens_generated",
                "generation_seconds": round(generation_seconds, 3),
                "output_token_count": output_token_count,
                "max_new_tokens": STORY_GENERATION_BUDGET,
                "token_limit_reached": output_token_count >= STORY_GENERATION_BUDGET,
                "json_complete_at_token_limit": output_token_count
                >= STORY_GENERATION_BUDGET,
                "tokenizer_eos_token_id": tokenizer.eos_token_id,
                "model_eos_token_id": model.generation_config.eos_token_id,
                **_json_prefix_decoder_diagnostics(prefix_allowed_tokens_fn),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    try:
        with worker_phase("business_rule_validation"):
            assembled = _assemble_parent_story_output(content)
            result = _parse_story_output(
                json.dumps(assembled, ensure_ascii=False), data
            )
    except StoryOutputValidationError as exc:
        print(
            json.dumps(
                {
                    "event": "story_output_rejected",
                    "reason_code": exc.reason_code,
                    "output_byte_count": len(text.encode("utf-8")),
                    "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID") from exc
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": {"id": TEXT_MODEL_ID, "revision": TEXT_MODEL_REVISION},
        "result": result,
    }


@app.function(
    name="generate-teacher-sketch-deck",
    image=_text_image,
    gpu=["L40S", "L4", "A10"],
    cpu=4.0,
    memory=32_768,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume.with_mount_options(read_only=True),
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=120,
    timeout=1_800,
    retries=0,
)
@observed_worker(
    workload="teacher.sketch-deck.generate",
    model_id=TEXT_MODEL_ID,
    model_revision=TEXT_MODEL_REVISION,
    gpu_class="L40S|L4|A10",
)
def generate_teacher_sketch_deck(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate the ordered drawing-guide text for one reviewed-plan deck draft."""

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "teacher.sketch-deck.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request, expected_asset="input/request.json")
    with worker_phase("approved_plan_contract_validation"):
        _validate_teacher_deck_input(data)
    with worker_phase("checkpoint_verification"):
        _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    with worker_phase("model_load"):
        processor, model = _load_text_model()
    tokenizer = processor.tokenizer
    prompt = _teacher_deck_prompt(data)
    messages = [
        {
            "role": "system",
            "content": (
                "Bạn tạo hướng dẫn vẽ ngắn từ lesson plan đã được người lớn duyệt. "
                "Không thêm hoạt động hay kiến thức ngoài input."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    with worker_phase("prompt_encoding"):
        encoded = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors="pt",
            return_dict=True,
        ).to(model.device)
    import torch

    max_new_tokens = _teacher_deck_max_output_tokens(len(data["drawing_steps"]))
    with worker_phase("constrained_decoder_setup"):
        prefix_allowed_tokens_fn = _build_json_prefix_allowed_tokens_fn(
            tokenizer,
            _teacher_deck_json_schema(len(data["drawing_steps"])),
            eos_token_id=model.generation_config.eos_token_id,
        )
    generation_started = time.perf_counter()
    with worker_phase("model_inference"), torch.inference_mode():
        generated = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=_generation_pad_token_id(model, tokenizer),
            prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
        )
    output_token_count = int(generated.shape[-1] - encoded["input_ids"].shape[-1])
    eos_token_ids = model.generation_config.eos_token_id
    if isinstance(eos_token_ids, int):
        eos_token_ids = [eos_token_ids]
    final_token_id = int(generated[0, -1].item()) if output_token_count else None
    text = tokenizer.decode(
        generated[0, encoded["input_ids"].shape[-1] :], skip_special_tokens=True
    ).strip()
    try:
        with worker_phase("output_parse_and_contract_validation"):
            guide = _parse_teacher_guide(text, data)
    except RuntimeError as exc:
        hit_limit = output_token_count >= max_new_tokens
        print(
            json.dumps(
                {
                    "event": "teacher_deck_output_truncated"
                    if hit_limit
                    else "teacher_deck_output_invalid",
                    "reason_code": str(exc),
                    "generation_seconds": round(
                        time.perf_counter() - generation_started, 3
                    ),
                    "tokenizer_eos_token_id": tokenizer.eos_token_id,
                    "model_eos_token_id": model.generation_config.eos_token_id,
                    **_generation_output_diagnostics(
                        generated, encoded["input_ids"].shape[-1], model
                    ),
                    **_json_output_diagnostics(text),
                    **_json_prefix_decoder_diagnostics(
                        prefix_allowed_tokens_fn,
                        generated=generated,
                        input_token_count=encoded["input_ids"].shape[-1],
                    ),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if hit_limit:
            raise RuntimeError("MODAL_MODEL_OUTPUT_TRUNCATED") from exc
        raise
    print(
        json.dumps(
            {
                "event": "teacher_deck_tokens_generated",
                "generation_seconds": round(
                    time.perf_counter() - generation_started, 3
                ),
                "output_token_count": output_token_count,
                "max_new_tokens": max_new_tokens,
                "token_limit_reached": output_token_count >= max_new_tokens,
                "ended_with_eos": final_token_id in (eos_token_ids or []),
                "json_complete_at_token_limit": output_token_count >= max_new_tokens,
                "tokenizer_eos_token_id": tokenizer.eos_token_id,
                "model_eos_token_id": model.generation_config.eos_token_id,
                **_json_prefix_decoder_diagnostics(prefix_allowed_tokens_fn),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    with worker_phase("approved_activity_mapping"):
        deck = _compose_teacher_deck(data, guide)
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": {"id": TEXT_MODEL_ID, "revision": TEXT_MODEL_REVISION},
        "result": deck,
    }


@app.function(
    name="suggest-lesson-plan",
    image=_story_text_image,
    gpu=["L40S", "L4", "A10"],
    cpu=4.0,
    memory=32_768,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume.with_mount_options(read_only=True),
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=120,
    timeout=1_800,
    retries=0,
)
@observed_worker(
    workload="lesson.plan.suggest",
    model_id=TEXT_MODEL_ID,
    model_revision=TEXT_MODEL_REVISION,
    gpu_class="L40S|L4|A10",
)
def suggest_lesson_plan(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate structured Vietnamese lesson content from allowlisted reviewed fields."""

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "lesson.plan.suggest":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request, expected_asset="input/request.json")
    with worker_phase("lesson_request_validation"):
        _validate_lesson_suggestion_input(data)
    with worker_phase("checkpoint_verification"):
        _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    with worker_phase("model_load"):
        processor, model = _load_text_model()
    tokenizer = processor.tokenizer
    messages = [
        {
            "role": "system",
            "content": (
                "Bạn hỗ trợ người lớn soạn giáo án Montessori lấy trẻ làm trung tâm, tiếng Việt. "
                "Chỉ tạo nội dung bản nháp theo chủ đề, độ tuổi, mục tiêu và hoạt động được "
                "yêu cầu. "
                "Không tự xuất bản, không suy đoán dữ liệu về trẻ, không thêm hồ sơ, "
                "không tạo khẳng định "
                "kiến thức thiếu căn cứ. Nội dung phải có vật liệu, chuẩn bị, từng bước "
                "thực hiện, quan sát "
                "và lưu ý an toàn cho từng hoạt động."
            ),
        },
        {"role": "user", "content": _lesson_suggestion_prompt(data)},
    ]
    with worker_phase("prompt_encoding"):
        encoded = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors="pt",
            return_dict=True,
        ).to(model.device)
    input_ids = encoded["input_ids"]
    max_new_tokens = _lesson_suggestion_max_output_tokens(data["activity_count"])
    with worker_phase("constrained_decoder_setup"):
        prefix_allowed_tokens_fn = _build_json_prefix_allowed_tokens_fn(
            tokenizer,
            _lesson_suggestion_json_schema(data),
            eos_token_id=model.generation_config.eos_token_id,
        )
    import torch

    with worker_phase("model_inference"), torch.inference_mode():
        generated = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=_generation_pad_token_id(model, tokenizer),
            prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
        )
    output_token_count = int(generated.shape[-1] - input_ids.shape[-1])
    text = tokenizer.decode(
        generated[0, input_ids.shape[-1] :], skip_special_tokens=True
    )
    try:
        with worker_phase("output_parse_and_contract_validation"):
            content = _parse_lesson_suggestion_content(text, data)
    except RuntimeError as exc:
        hit_limit = output_token_count >= max_new_tokens
        print(
            json.dumps(
                {
                    "event": "lesson_suggestion_output_truncated"
                    if hit_limit
                    else "lesson_suggestion_output_invalid",
                    "reason_code": str(exc),
                    "tokenizer_eos_token_id": tokenizer.eos_token_id,
                    "model_eos_token_id": model.generation_config.eos_token_id,
                    **_generation_output_diagnostics(
                        generated, input_ids.shape[-1], model
                    ),
                    **_json_output_diagnostics(text),
                    **_json_prefix_decoder_diagnostics(
                        prefix_allowed_tokens_fn,
                        generated=generated,
                        input_token_count=input_ids.shape[-1],
                    ),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if hit_limit:
            raise RuntimeError("MODAL_MODEL_OUTPUT_TRUNCATED") from exc
        raise
    print(
        json.dumps(
            {
                "event": "lesson_suggestion_tokens_generated",
                "output_token_count": output_token_count,
                "max_new_tokens": max_new_tokens,
                "token_limit_reached": output_token_count >= max_new_tokens,
                "json_complete_at_token_limit": output_token_count >= max_new_tokens,
                "tokenizer_eos_token_id": tokenizer.eos_token_id,
                "model_eos_token_id": model.generation_config.eos_token_id,
                **_json_prefix_decoder_diagnostics(prefix_allowed_tokens_fn),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": {"id": TEXT_MODEL_ID, "revision": TEXT_MODEL_REVISION},
        "result": {"draft_only": True, "content": content},
    }


def _validate_lesson_suggestion_input(data: dict[str, Any]) -> None:
    expected = {
        "schema_version",
        "topic",
        "target_age_band_ref",
        "target_age_band_version",
        "target_age_months",
        "objectives",
        "drawing_subject",
        "activity_count",
        "activity_kind",
        "script_following_allowed",
        "script_direction",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if (
        data.get("schema_version") != "sketch2life.lesson-plan-suggest-input.v1"
        or not isinstance(data.get("topic"), str)
        or not 1 <= len(data["topic"].strip()) <= 120
        or not isinstance(data.get("drawing_subject"), str)
        or not 1 <= len(data["drawing_subject"].strip()) <= 160
        or not isinstance(data.get("target_age_band_ref"), str)
        or re.fullmatch(r"[A-Za-z0-9._:-]{1,256}", data["target_age_band_ref"]) is None
        or isinstance(data.get("target_age_band_version"), bool)
        or not isinstance(data.get("target_age_band_version"), int)
        or data["target_age_band_version"] < 1
        or isinstance(data.get("target_age_months"), bool)
        or not isinstance(data.get("target_age_months"), int)
        or not 36 <= data["target_age_months"] <= 120
        or not isinstance(data.get("objectives"), list)
        or not 1 <= len(data["objectives"]) <= 4
        or any(
            not isinstance(value, str) or not value.strip() or len(value) > 1000
            for value in data["objectives"]
        )
        or isinstance(data.get("activity_count"), bool)
        or not isinstance(data.get("activity_count"), int)
        or not 1 <= data["activity_count"] <= 6
        or data.get("activity_kind") not in {"outdoor", "indoor", "mixed"}
        or not isinstance(data.get("script_following_allowed"), bool)
        or (
            data.get("script_direction") is not None
            and (
                not isinstance(data["script_direction"], str)
                or not data["script_direction"].strip()
                or len(data["script_direction"]) > 2000
            )
        )
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")


def _lesson_suggestion_prompt(data: dict[str, Any]) -> str:
    return (
        "Keep every field concise and concrete. Limits: title 80 characters; drawing steps 320; "
        "learning notes 450; script direction 240; activity title 80; objective 180; materials "
        "and preparation 160 each; instructions 450; observation and safety notes 180 each. "
        "Use 3-5 short drawing steps, 2-4 factual learning notes, and 3-5 practical activity "
        "steps. Materials, preparation, observation, and safety should be brief. Do not repeat "
        "information. Return only the requested JSON. "
        "Trả về đúng một JSON object có đúng các trường: title, drawing_steps_text, "
        "subject_learning_notes, script_direction, activities. activities phải có đúng "
        f"{data['activity_count']} phần tử; mỗi phần tử có title, objective, materials_text, "
        "preparation_text, instructions_text, observation_notes, safety_notes, activity_kind. "
        "Mỗi mục tiêu, bước vẽ, ghi chú kiến thức và hoạt động phải cụ thể, ngắn gọn, phù hợp "
        "vai trò người lớn là quan sát/hỗ trợ và để trẻ tự làm. Không đưa lời thoại hay hướng dẫn "
        "quá áp đặt. Dùng đúng activity_kind được yêu cầu cho mọi hoạt động. "
        "Không thay đổi chủ đề, "
        "chủ thể vẽ, mục tiêu, độ tuổi hoặc script_following_allowed. Viết bằng tiếng Việt. "
        "Nếu không thể đưa ra safety_notes cụ thể, hãy nêu rủi ro cần người lớn kiểm tra "
        "thay vì bỏ trống. "
        f"Chủ đề: {data['topic']}. Chủ thể vẽ: {data['drawing_subject']}. "
        f"Tuổi mục tiêu: {data['target_age_months']} tháng. Mục tiêu đã nhập: "
        f"{json.dumps(data['objectives'], ensure_ascii=False)}. "
        f"Loại hoạt động: {data['activity_kind']}. Script following allowed: "
        f"{str(data['script_following_allowed']).lower()}. Hướng kịch bản đã nhập: "
        f"{json.dumps(data['script_direction'], ensure_ascii=False)}."
    )


def _lesson_suggestion_max_output_tokens(activity_count: int) -> int:
    if isinstance(activity_count, bool) or not 1 <= activity_count <= 6:
        raise ValueError("activity_count must be between one and six")
    return 3_200 + (activity_count - 1) * 1_000


def _lesson_suggestion_json_schema(request: dict[str, Any]) -> dict[str, Any]:
    activity_count = request["activity_count"]
    activity_kind = request["activity_kind"]
    activity = {
        "title": {"type": "string", "minLength": 1, "maxLength": 80},
        "objective": {"type": "string", "minLength": 1, "maxLength": 180},
        "materials_text": {"type": "string", "maxLength": 160},
        "preparation_text": {"type": "string", "maxLength": 160},
        "instructions_text": {"type": "string", "minLength": 1, "maxLength": 450},
        "observation_notes": {"type": "string", "maxLength": 180},
        "safety_notes": {"type": "string", "minLength": 1, "maxLength": 180},
        "activity_kind": {"type": "string", "enum": [activity_kind]},
    }
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 80},
            "drawing_steps_text": {"type": "string", "minLength": 1, "maxLength": 320},
            "subject_learning_notes": {
                "type": "string",
                "minLength": 1,
                "maxLength": 450,
            },
            "script_direction": (
                {"type": "string", "maxLength": 240}
                if request["script_following_allowed"]
                else {"type": "null"}
            ),
            "activities": {
                "type": "array",
                "minItems": activity_count,
                "maxItems": activity_count,
                "items": {
                    "type": "object",
                    "properties": activity,
                    "required": list(activity),
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "title",
            "drawing_steps_text",
            "subject_learning_notes",
            "script_direction",
            "activities",
        ],
        "additionalProperties": False,
    }


def _parse_lesson_suggestion_content(
    text: str, request: dict[str, Any]
) -> dict[str, Any]:
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_story_keys)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID") from exc
    if not isinstance(value, dict) or set(value) != {
        "title",
        "drawing_steps_text",
        "subject_learning_notes",
        "script_direction",
        "activities",
    }:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    for field, maximum in (
        ("title", 80),
        ("drawing_steps_text", 320),
        ("subject_learning_notes", 450),
    ):
        item = value[field]
        if not isinstance(item, str) or not item.strip() or len(item.strip()) > maximum:
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    script_direction = value["script_direction"]
    if (
        request["script_following_allowed"]
        and (
            not isinstance(script_direction, str)
            or not script_direction.strip()
            or len(script_direction.strip()) > 240
        )
    ) or (not request["script_following_allowed"] and script_direction is not None):
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    activities = value["activities"]
    if not isinstance(activities, list) or len(activities) != request["activity_count"]:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    activity_fields = {
        "title": 80,
        "objective": 180,
        "materials_text": 160,
        "preparation_text": 160,
        "instructions_text": 450,
        "observation_notes": 180,
        "safety_notes": 180,
    }
    checked_activities: list[dict[str, Any]] = []
    for activity in activities:
        if not isinstance(activity, dict) or set(activity) != {
            *activity_fields,
            "activity_kind",
        }:
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
        for field, maximum in activity_fields.items():
            item = activity[field]
            required = field in {
                "title",
                "objective",
                "instructions_text",
                "safety_notes",
            }
            if (
                not isinstance(item, str)
                or len(item.strip()) > maximum
                or (required and not item.strip())
            ):
                raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
        if activity["activity_kind"] != request["activity_kind"]:
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
        checked_activities.append(
            {
                **{field: activity[field].strip() for field in activity_fields},
                "activity_kind": activity["activity_kind"],
            }
        )
    return {
        "locale": "vi-VN",
        "title": value["title"].strip(),
        "topic": request["topic"].strip(),
        "target_age_band_ref": request["target_age_band_ref"],
        "target_age_band_version": request["target_age_band_version"],
        "objectives": [item.strip() for item in request["objectives"]],
        "drawing_subject": request["drawing_subject"].strip(),
        "drawing_steps_text": value["drawing_steps_text"].strip(),
        "subject_learning_notes": value["subject_learning_notes"].strip(),
        "script_direction": (
            script_direction.strip() if isinstance(script_direction, str) else None
        ),
        "script_following_allowed": request["script_following_allowed"],
        "activities": checked_activities,
    }


def _validate_teacher_deck_input(data: dict[str, Any]) -> None:
    expected = {
        "schema_version",
        "plan_revision_ref",
        "content_hash",
        "topic",
        "target_age_months",
        "objectives",
        "drawing_steps",
        "subject_knowledge",
        "activities",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if (
        data.get("schema_version") != "sketch2life.teacher-deck-input.v1"
        or not isinstance(data.get("plan_revision_ref"), str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", data["plan_revision_ref"])
        or not isinstance(data.get("content_hash"), str)
        or _SHA256.fullmatch(data["content_hash"]) is None
        or not isinstance(data.get("topic"), str)
        or not data["topic"].strip()
        or len(data["topic"]) > 120
        or not isinstance(data.get("target_age_months"), int)
        or isinstance(data.get("target_age_months"), bool)
        or not 36 <= data["target_age_months"] <= 120
        or not isinstance(data.get("objectives"), list)
        or not 1 <= len(data["objectives"]) <= 4
        or not isinstance(data.get("drawing_steps"), list)
        or not 3 <= len(data["drawing_steps"]) <= 5
        or not isinstance(data.get("subject_knowledge"), list)
        or not 1 <= len(data["subject_knowledge"]) <= 8
        or not isinstance(data.get("activities"), list)
        or not 1 <= len(data["activities"]) <= 6
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    plan_payload = {key: value for key, value in data.items() if key != "content_hash"}
    canonical_plan = json.dumps(
        plan_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if hashlib.sha256(canonical_plan).hexdigest() != data["content_hash"]:
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    for field, maximum in (("objectives", 200), ("subject_knowledge", 240)):
        values = data[field]
        if any(
            not isinstance(value, str) or not value.strip() or len(value) > maximum
            for value in values
        ):
            raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    for step_no, step in enumerate(data["drawing_steps"], start=1):
        if (
            not isinstance(step, dict)
            or set(step) != {"step_index", "action", "placement"}
            or step.get("step_index") != step_no
            or any(
                not isinstance(step.get(field), str)
                or not step[field].strip()
                or len(step[field]) > 240
                for field in ("action", "placement")
            )
        ):
            raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    activity_ids: set[str] = set()
    for activity in data["activities"]:
        if (
            not isinstance(activity, dict)
            or set(activity)
            != {
                "activity_ref",
                "title",
                "goal",
                "materials",
                "preparation",
                "instructions",
                "safety_notes",
            }
            or not isinstance(activity.get("activity_ref"), str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", activity["activity_ref"])
            or activity["activity_ref"] in activity_ids
            or not isinstance(activity.get("title"), str)
            or not activity["title"].strip()
            or len(activity["title"]) > 120
            or any(
                not isinstance(activity.get(field), list)
                or not 1 <= len(activity[field]) <= 8
                or any(
                    not isinstance(item, str) or not item.strip() or len(item) > 240
                    for item in activity[field]
                )
                for field in (
                    "goal",
                    "materials",
                    "preparation",
                    "instructions",
                    "safety_notes",
                )
            )
        ):
            raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
        activity_ids.add(activity["activity_ref"])


def _teacher_deck_prompt(data: dict[str, Any]) -> str:
    return (
        "Tạo DUY NHẤT JSON object "
        '{"steps":[{"step_index":1,"instruction":"...","placement":"..."}]}. '
        "Viết tiếng Việt thật ngắn: instruction tối đa 100 ký tự, placement tối đa 80 ký tự. "
        "Mỗi instruction là một lời mời quan sát hoặc vẽ phù hợp tuổi; giữ nguyên thứ tự, "
        "hành động "
        "và vị trí đã duyệt. Không thêm chủ thể, vật liệu, mục tiêu, kiến thức hay activity. "
        "Không nhắc roster, không tạo PowerPoint, không markdown. "
        f"Chủ đề: {data['topic']}; tuổi mục tiêu {data['target_age_months']} tháng. "
        f"Thao tác đã duyệt: {json.dumps(data['drawing_steps'], ensure_ascii=False)}. "
        f"Trả đúng {len(data['drawing_steps'])} bước theo đúng thứ tự, mỗi bước chỉ một câu ngắn."
    )


def _teacher_deck_json_schema(step_count: int) -> dict[str, Any]:
    step_fields = {
        "step_index": {"type": "integer", "minimum": 1, "maximum": step_count},
        "instruction": {"type": "string", "minLength": 1, "maxLength": 100},
        "placement": {"type": "string", "minLength": 1, "maxLength": 80},
    }
    return {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "minItems": step_count,
                "maxItems": step_count,
                "items": {
                    "type": "object",
                    "properties": step_fields,
                    "required": list(step_fields),
                    "additionalProperties": False,
                },
            }
        },
        "required": ["steps"],
        "additionalProperties": False,
    }


def _teacher_deck_max_output_tokens(step_count: int) -> int:
    if isinstance(step_count, bool) or not 3 <= step_count <= 5:
        raise ValueError("step_count must be between three and five")
    return 512 + step_count * 320


def _parse_teacher_guide(text: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        guide = json.loads(text, object_pairs_hook=_reject_duplicate_story_keys)
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID") from exc
    if (
        not isinstance(guide, dict)
        or set(guide) != {"steps"}
        or not isinstance(guide["steps"], list)
        or len(guide["steps"]) != len(data["drawing_steps"])
    ):
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    checked: list[dict[str, Any]] = []
    for index, (candidate, source) in enumerate(
        zip(guide["steps"], data["drawing_steps"], strict=True), start=1
    ):
        if (
            not isinstance(candidate, dict)
            or set(candidate) != {"step_index", "instruction", "placement"}
            or candidate.get("step_index") != index
            or any(
                not isinstance(candidate.get(field), str)
                or not candidate[field].strip()
                or len(candidate[field]) > (100 if field == "instruction" else 80)
                for field in ("instruction", "placement")
            )
        ):
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
        checked.append(
            {
                "step_index": index,
                "instruction": candidate["instruction"].strip(),
                "placement": candidate["placement"].strip(),
                "source_action": source["action"],
                "source_placement": source["placement"],
            }
        )
    return checked


def _compose_teacher_deck(
    data: dict[str, Any], guide: list[dict[str, Any]]
) -> dict[str, Any]:
    slides: list[dict[str, Any]] = [
        {
            "slide_index": 1,
            "kind": "orientation",
            "title": data["topic"],
            "bullets": data["objectives"],
            "activity_ref": None,
        },
        {
            "slide_index": 2,
            "kind": "drawing_guide",
            "title": f"Cùng quan sát và vẽ {data['topic']}",
            "steps": guide,
            "activity_ref": None,
        },
        {
            "slide_index": 3,
            "kind": "subject_exploration",
            "title": f"Cùng tìm hiểu về {data['topic']}",
            "bullets": data["subject_knowledge"],
            "activity_ref": None,
        },
    ]
    for activity in data["activities"]:
        slides.append(
            {
                "slide_index": len(slides) + 1,
                "kind": "approved_activity",
                "title": activity["title"],
                "activity_ref": activity["activity_ref"],
                "goal": activity["goal"],
                "materials": activity["materials"],
                "preparation": activity["preparation"],
                "instructions": activity["instructions"],
                "safety_notes": activity["safety_notes"],
            }
        )
    return {
        "schema_version": "sketch2life.teacher-sketch-deck.v1",
        "status": "DRAFT",
        "plan_revision_ref": data["plan_revision_ref"],
        "content_hash": data["content_hash"],
        "aspect_ratio": "16:9",
        "language": "vi",
        "topic": data["topic"],
        "target_age_months": data["target_age_months"],
        "subject_knowledge": data["subject_knowledge"],
        "slides": slides,
        "approved_activity_refs": [
            activity["activity_ref"] for activity in data["activities"]
        ],
        "review_required": True,
    }


@app.function(
    name="synthesize-vietnamese-narration",
    image=_tts_image,
    cpu=4.0,
    memory=12_288,
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=600,
    retries=0,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume.with_mount_options(read_only=True),
    },
)
@observed_worker(
    workload="tts.narration.generate",
    model_id=TTS_MODEL_ID,
    model_revision=TTS_MODEL_REVISION,
    gpu_class="cpu",
)
def synthesize_vietnamese_narration(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate one short synthetic sentence with the adult preset voice."""

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "tts.narration.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request, expected_asset="input/request.json")
    worker_stage("tts_request_validation")
    if set(data) != {"text", "voice"}:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if (
        data["text"] != "Con bướm bay qua khu vườn đầy nắng."
        or data["voice"] != "Hải Đăng"
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    with worker_phase("tts_checkpoint_verification"):
        _verify_marker(Path(TTS_MODEL_MARKER), TTS_MODEL_ID, TTS_MODEL_REVISION)
        _verify_marker(Path(TTS_CODEC_MARKER), TTS_CODEC_ID, TTS_CODEC_REVISION)

    from vieneu import Vieneu

    with worker_phase("tts_model_load"):
        engine = Vieneu(
            mode="v3turbo",
            backbone_repo=TTS_MODEL_DIR,
            device="cpu",
            backend="onnx",
            precision="fp32",
            onnx_repo=TTS_MODEL_DIR,
            onnx_dir=f"{TTS_MODEL_DIR}/onnx_update",
            codec_repo=TTS_CODEC_DIR,
            codec_dir=TTS_CODEC_DIR,
            threads=4,
        )
    with worker_phase("tts_inference"):
        audio = engine.infer(
            data["text"], voice=data["voice"], max_new_frames=160, max_chars=100
        )
    output_path = Path("/tmp/sketch2life-synthetic-narration.wav")
    with worker_phase("audio_encode_and_validate"):
        engine.save(audio, str(output_path))
        output_bytes = output_path.read_bytes()
        if not output_bytes.startswith(b"RIFF") or len(output_bytes) > MAX_OUTPUT_BYTES:
            raise RuntimeError("MODAL_OUTPUT_INVALID")
    with worker_phase("audio_output_contract_validation"):
        return _media_response(
            request,
            "tts.narration.generate",
            TTS_MODEL_ID,
            TTS_MODEL_REVISION,
            "audio/wav",
            output_bytes,
        )


@app.function(
    name="transcribe-vietnamese-audio",
    image=_asr_image,
    cpu=4.0,
    memory=12_288,
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=600,
    retries=0,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume.with_mount_options(read_only=True),
    },
)
@observed_worker(
    workload="asr.transcribe",
    model_id=ASR_MODEL_ID,
    model_revision=ASR_MODEL_REVISION,
    gpu_class="cpu",
)
def transcribe_vietnamese_audio(payload: dict[str, Any]) -> dict[str, Any]:
    """Transcribe only the synthetic audio asset staged for this POC."""

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "asr.transcribe":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("audio_asset_read_and_verify"):
        audio_path, audio_sha256 = _read_binary_asset(
            request,
            expected_asset="input/audio.wav",
            expected_content_type="audio/wav",
            signature=b"RIFF",
        )
    with worker_phase("asr_checkpoint_verification"):
        _verify_marker(Path(ASR_MODEL_MARKER), ASR_MODEL_ID, ASR_MODEL_REVISION)

    from faster_whisper import WhisperModel

    with worker_phase("asr_model_load"):
        model = WhisperModel(
            ASR_MODEL_DIR,
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=1,
        )
    with worker_phase("asr_inference_and_decode"):
        segments, info = model.transcribe(
            str(audio_path),
            language="vi",
            task="transcribe",
            beam_size=5,
            vad_filter=False,
            condition_on_previous_text=False,
        )
        transcript_segments = []
        for segment in segments:
            transcript_segments.append(
                {
                    "start_seconds": round(float(segment.start), 3),
                    "end_seconds": round(float(segment.end), 3),
                    "text": segment.text.strip()[:500],
                }
            )
            if len(transcript_segments) >= 32:
                break
        transcript = " ".join(item["text"] for item in transcript_segments).strip()
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": request.workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "input_sha256": audio_sha256,
        "model": {"id": ASR_MODEL_ID, "revision": ASR_MODEL_REVISION},
        "result": {
            "language": info.language,
            "language_probability": round(float(info.language_probability), 4),
            "text": transcript[:4_000],
            "segments": transcript_segments,
        },
    }


def _read_json_asset(
    request: ModalWorkerInputV1, *, expected_asset: str
) -> dict[str, Any]:
    path, _ = _read_binary_asset(
        request,
        expected_asset=expected_asset,
        expected_content_type="application/json",
        signature=None,
    )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID") from exc
    if not isinstance(data, dict):
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    return data


def _read_binary_asset(
    request: ModalWorkerInputV1,
    *,
    expected_asset: str,
    expected_content_type: str,
    signature: bytes | None,
) -> tuple[Path, str]:
    scratch_root = Path(SCRATCH_MOUNT).resolve()
    attempt_dir = (scratch_root / request.attempt_prefix.rstrip("/")).resolve()
    if not attempt_dir.is_relative_to(scratch_root):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    input_dir = attempt_dir / "input"
    manifest_path = (input_dir / "manifest.json").resolve()
    asset_path = (attempt_dir / expected_asset).resolve()
    if not manifest_path.is_relative_to(attempt_dir) or not asset_path.is_relative_to(
        attempt_dir
    ):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
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
    asset = manifest.get("asset")
    if manifest.get("schema_version") != INPUT_SCHEMA or not isinstance(asset, dict):
        raise WorkerContractError("MODAL_SCHEMA_UNSUPPORTED")
    if set(asset) != {"path", "content_type", "size_bytes", "sha256"}:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if (
        asset.get("path") != expected_asset
        or asset.get("content_type") != expected_content_type
    ):
        raise WorkerContractError("MODAL_INPUT_TYPE_NOT_ALLOWED")
    try:
        data = asset_path.read_bytes()
    except OSError as exc:
        raise WorkerContractError("MODAL_INPUT_ASSET_MISSING") from exc
    digest = hashlib.sha256(data).hexdigest()
    if (
        not isinstance(asset.get("size_bytes"), int)
        or isinstance(asset.get("size_bytes"), bool)
        or asset["size_bytes"] != len(data)
        or not isinstance(asset.get("sha256"), str)
        or _SHA256.fullmatch(asset["sha256"]) is None
        or digest != asset["sha256"]
        or request.input_bytes != len(data) + len(manifest_bytes)
        or (signature is not None and not data.startswith(signature))
    ):
        raise WorkerContractError("MODAL_INPUT_HASH_MISMATCH")
    return asset_path, digest


def _media_response(
    request: ModalWorkerInputV1,
    workload: str,
    model_id: str,
    revision: str,
    content_type: str,
    data: bytes,
) -> dict[str, Any]:
    if not data or len(data) > MAX_OUTPUT_BYTES:
        raise RuntimeError("MODAL_OUTPUT_LIMIT_EXCEEDED")
    return {
        "schema_version": WORKER_OUTPUT_SCHEMA,
        "workload": workload,
        "job_id": request.job_id,
        "generation_id": request.generation_id,
        "attempt_id": request.attempt_id,
        "model": {"id": model_id, "revision": revision},
        "asset": {
            "content_type": content_type,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": data,
        },
    }


class StoryOutputValidationError(ValueError):
    """Internal safe reason for rejecting a generated story without exposing its text."""

    def __init__(self, reason_code: str) -> None:
        super().__init__("MODAL_MODEL_OUTPUT_INVALID")
        self.reason_code = reason_code


def _reject_duplicate_story_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise StoryOutputValidationError("DUPLICATE_JSON_KEY")
        value[key] = item
    return value


def _parse_story_output(text: str, request: dict[str, Any]) -> dict[str, Any]:
    try:
        data = json.loads(text, object_pairs_hook=_reject_duplicate_story_keys)
    except StoryOutputValidationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise StoryOutputValidationError("JSON_INVALID") from exc

    expected = {"schema_version", "language", "title", "story", "duration_ms", "scenes"}
    if not isinstance(data, dict) or set(data) != expected:
        raise StoryOutputValidationError("TOP_LEVEL_SCHEMA_INVALID")
    story = data["story"]
    scenes = data["scenes"]
    if (
        data.get("schema_version") != "sketch2life.story-revision.v1"
        or data.get("language") != "vi"
        or not isinstance(data["title"], str)
        or not isinstance(story, dict)
        or set(story) != {"opening", "middle", "ending"}
        or any(
            not isinstance(story[key], str)
            or not story[key].strip()
            or len(story[key].strip()) > 900
            for key in story
        )
        or not isinstance(scenes, list)
        or not 5 <= len(scenes) <= 15
        or isinstance(data.get("duration_ms"), bool)
        or not isinstance(data.get("duration_ms"), int)
        or not 30_000 <= data["duration_ms"] <= 90_000
    ):
        raise StoryOutputValidationError("STORY_FIELDS_INVALID")

    title = data["title"].strip()
    if not title or len(title) > 120:
        raise StoryOutputValidationError("STORY_FIELDS_INVALID")
    # The fact validator relies on the canonical opening -> middle -> ending order.
    story = {key: story[key].strip() for key in ("opening", "middle", "ending")}
    checked_scenes: list[dict[str, Any]] = []
    timeline_ms = 0
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict) or set(scene) != {
            "scene_index",
            "title",
            "action",
            "visual_prompt",
            "narration",
            "start_ms",
            "duration_ms",
            "character_anchors",
        }:
            raise StoryOutputValidationError("SCENE_FIELDS_INVALID")
        text_fields = ("title", "action", "visual_prompt", "narration")
        if (
            isinstance(scene.get("scene_index"), bool)
            or not isinstance(scene.get("scene_index"), int)
            or scene["scene_index"] != index
            or any(
                not isinstance(scene.get(key), str) or not scene[key].strip()
                for key in text_fields
            )
            or len(scene["title"].strip()) > 100
            or len(scene["action"].strip()) > 500
            or len(scene["visual_prompt"].strip()) > 900
            or len(scene["narration"].strip()) > 500
            or isinstance(scene.get("start_ms"), bool)
            or not isinstance(scene.get("start_ms"), int)
            or isinstance(scene.get("duration_ms"), bool)
            or not isinstance(scene.get("duration_ms"), int)
            or not 1_000 <= scene["duration_ms"] <= 20_000
            or not isinstance(scene.get("character_anchors"), list)
            or not 1 <= len(scene["character_anchors"]) <= 6
            or any(
                not isinstance(anchor, str)
                or not anchor.strip()
                or len(anchor.strip()) > 120
                for anchor in scene["character_anchors"]
            )
        ):
            raise StoryOutputValidationError("SCENE_FIELDS_INVALID")
        if scene["start_ms"] != timeline_ms:
            raise StoryOutputValidationError("TIMELINE_INVALID")
        timeline_ms += scene["duration_ms"]
        checked_scenes.append(
            {
                **scene,
                "title": scene["title"].strip(),
                "action": scene["action"].strip(),
                "visual_prompt": scene["visual_prompt"].strip(),
                "narration": scene["narration"].strip(),
                "character_anchors": [
                    anchor.strip() for anchor in scene["character_anchors"]
                ],
            }
        )
    if timeline_ms != data["duration_ms"]:
        raise StoryOutputValidationError("TIMELINE_INVALID")
    result = {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": title,
        "story": story,
        "duration_ms": data["duration_ms"],
        "scenes": checked_scenes,
    }
    _validate_butterfly_facts(result, str(request["confirmed_subject"]))
    return result


def _parse_story_content_output(text: str) -> dict[str, Any]:
    try:
        content = json.loads(text, object_pairs_hook=_reject_duplicate_story_keys)
    except StoryOutputValidationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise StoryOutputValidationError("CONTENT_JSON_INVALID") from exc

    if not isinstance(content, dict) or set(content) != {"title", "story", "scenes"}:
        raise StoryOutputValidationError("CONTENT_SCHEMA_INVALID")

    title = content["title"]
    story = content["story"]
    scenes = content["scenes"]
    if (
        not isinstance(title, str)
        or not title.strip()
        or len(title.strip()) > 80
        or not isinstance(story, dict)
        or set(story) != {"opening", "middle", "ending"}
        or any(
            not isinstance(story[key], str)
            or not story[key].strip()
            or len(story[key].strip()) > 300
            for key in ("opening", "middle", "ending")
        )
        or not isinstance(scenes, list)
        or len(scenes) != 5
    ):
        raise StoryOutputValidationError("CONTENT_FIELDS_INVALID")

    normalized_story = {
        key: story[key].strip() for key in ("opening", "middle", "ending")
    }

    scene_keys = {"title", "action", "visual_prompt", "narration", "character_anchors"}
    text_bounds = {"title": 60, "action": 180, "visual_prompt": 240, "narration": 180}
    checked_scenes: list[dict[str, Any]] = []
    for scene in scenes:
        if not isinstance(scene, dict) or set(scene) != scene_keys:
            raise StoryOutputValidationError("CONTENT_SCENE_SCHEMA_INVALID")
        if any(
            not isinstance(scene[key], str)
            or not scene[key].strip()
            or len(scene[key].strip()) > maximum
            for key, maximum in text_bounds.items()
        ):
            raise StoryOutputValidationError("CONTENT_SCENE_TEXT_INVALID")
        anchors = scene["character_anchors"]
        if (
            not isinstance(anchors, list)
            or not 1 <= len(anchors) <= 3
            or any(
                not isinstance(anchor, str)
                or not anchor.strip()
                or len(anchor.strip()) > 60
                for anchor in anchors
            )
        ):
            raise StoryOutputValidationError("CONTENT_SCENE_ANCHORS_INVALID")
        checked_scenes.append(
            {
                **{key: scene[key].strip() for key in text_bounds},
                "character_anchors": [anchor.strip() for anchor in anchors],
            }
        )

    return {
        "title": title.strip(),
        "story": normalized_story,
        "scenes": checked_scenes,
    }


def _assemble_parent_story_output(content: dict[str, Any]) -> dict[str, Any]:
    """Add application-owned fixed timing metadata to validated story content."""

    scenes = [
        {
            "scene_index": index,
            **scene,
            "start_ms": (index - 1) * 6_000,
            "duration_ms": 6_000,
        }
        for index, scene in enumerate(content["scenes"], start=1)
    ]
    return {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": content["title"],
        "story": content["story"],
        "duration_ms": 30_000,
        "scenes": scenes,
    }


def _story_output_field_diagnostics(text: str) -> dict[str, Any]:
    """Describe story text fields without logging generated content."""

    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return {"story_field_diagnostics_available": False}
    if not isinstance(value, dict):
        return {"story_field_diagnostics_available": False}

    metrics: list[dict[str, Any]] = []
    limits = {
        "title": 80,
        "opening": 300,
        "middle": 300,
        "ending": 300,
        "scene_title": 40,
        "action": 180,
        "visual_prompt": 240,
        "narration": 180,
    }

    def add_metric(path: str, field: str, field_value: Any) -> None:
        if not isinstance(field_value, str):
            metrics.append({"field": path, "value_type": type(field_value).__name__})
            return
        metric = {
            "field": path,
            "character_count": len(field_value.strip()),
            "max_length": limits[field],
        }
        if field in {
            "opening",
            "middle",
            "ending",
            "action",
            "visual_prompt",
            "narration",
        }:
            metric["sentence_complete"] = _story_sentence_is_complete(field_value)
        metrics.append(metric)

    add_metric("title", "title", value.get("title"))
    story = value.get("story")
    if isinstance(story, dict):
        for section in ("opening", "middle", "ending"):
            if section in story:
                add_metric(f"story.{section}", section, story[section])
    scenes = value.get("scenes")
    if isinstance(scenes, list):
        for index, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                metrics.append(
                    {"field": f"scenes[{index}]", "value_type": type(scene).__name__}
                )
                continue
            for field, key in (
                ("scene_title", "title"),
                ("action", "action"),
                ("visual_prompt", "visual_prompt"),
                ("narration", "narration"),
            ):
                if key in scene:
                    add_metric(f"scenes[{index}].{key}", field, scene[key])

    incomplete_fields = [
        metric["field"]
        for metric in metrics
        if metric.get("sentence_complete") is False
    ]
    return {
        "story_field_diagnostics_available": True,
        "story_text_field_metric_count": len(metrics),
        "story_incomplete_sentence_fields": incomplete_fields,
        "story_text_field_metrics": metrics,
    }


def _story_sentence_is_complete(value: str) -> bool:
    stripped = value.rstrip().rstrip("\"'”’»)]}")
    return bool(stripped) and stripped[-1] in ".!?…"


def _parent_story_content_json_schema() -> dict[str, Any]:
    scene_fields = {
        "title": {"type": "string", "minLength": 1, "maxLength": 40},
        "action": {"type": "string", "minLength": 1, "maxLength": 180},
        "visual_prompt": {"type": "string", "minLength": 1, "maxLength": 240},
        "narration": {"type": "string", "minLength": 1, "maxLength": 180},
        "character_anchors": {
            "type": "array",
            "minItems": 1,
            "maxItems": 2,
            "items": {"type": "string", "minLength": 1, "maxLength": 40},
        },
    }
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 80},
            "story": {
                "type": "object",
                "properties": {
                    key: {"type": "string", "minLength": 1, "maxLength": 300}
                    for key in ("opening", "middle", "ending")
                },
                "required": ["opening", "middle", "ending"],
                "additionalProperties": False,
            },
            "scenes": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": scene_fields,
                    "required": list(scene_fields),
                    "additionalProperties": False,
                },
            },
        },
        "required": ["title", "story", "scenes"],
        "additionalProperties": False,
    }


_CACHED_STORY_VOCAB_DATA: Any | None = None
_CACHED_STORY_EOS_IDS: tuple[int, ...] | None = None


def _generation_pad_token_id(model: Any, tokenizer: Any) -> int:
    eos_token_id = model.generation_config.eos_token_id
    if isinstance(eos_token_id, int) and not isinstance(eos_token_id, bool):
        return eos_token_id
    if (
        isinstance(eos_token_id, list)
        and eos_token_id
        and isinstance(eos_token_id[0], int)
        and not isinstance(eos_token_id[0], bool)
    ):
        return eos_token_id[0]
    return int(tokenizer.eos_token_id)


def _generation_output_diagnostics(
    generated: Any, input_token_count: int, model: Any
) -> dict[str, Any]:
    output_token_count = max(0, int(generated.shape[-1] - input_token_count))
    final_token_id = int(generated[0, -1].item()) if output_token_count else None
    eos_token_ids = _normalize_token_ids(model.generation_config.eos_token_id)
    return {
        "output_token_count": output_token_count,
        "final_token_id": final_token_id,
        "ended_with_model_eos": final_token_id in eos_token_ids,
    }


def _normalize_token_ids(value: Any) -> list[int]:
    token_ids = value if isinstance(value, (list, tuple)) else [value]
    return [
        int(token_id)
        for token_id in token_ids
        if isinstance(token_id, int) and not isinstance(token_id, bool)
    ]


def _json_output_diagnostics(text: str) -> dict[str, Any]:
    """Return shape-only diagnostics; never include generated text in logs."""

    summary: dict[str, Any] = {"decoded_character_count": len(text)}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        summary.update(
            {
                "json_complete": False,
                "json_error_type": type(exc).__name__,
                "json_error_position": exc.pos,
            }
        )
        active_value = re.search(
            r'"(?P<key>[^"\\]+)"\s*:\s*"(?P<value>(?:\\.|[^"\\])*)$',
            text.rstrip(),
            flags=re.DOTALL,
        )
        if active_value is not None:
            summary["unterminated_string_character_count"] = len(
                active_value.group("value")
            )
    else:
        summary["json_complete"] = True
        summary["json_root_type"] = type(value).__name__
        if isinstance(value, dict):
            summary["json_root_key_count"] = len(value)
    summary["field_key_counts"] = {
        key: text.count(json.dumps(key))
        for key in (
            "instruction",
            "placement",
            "title",
            "action",
            "visual_prompt",
            "narration",
            "drawing_steps_text",
            "subject_learning_notes",
            "instructions_text",
            "safety_notes",
        )
    }
    return summary


def _build_story_prefix_allowed_tokens_fn(
    tokenizer: Any, *, eos_token_id: int | list[int] | None = None
) -> Any:
    return _build_json_prefix_allowed_tokens_fn(
        tokenizer,
        _parent_story_content_json_schema(),
        eos_token_id=eos_token_id,
    )


def _build_json_prefix_allowed_tokens_fn(
    tokenizer: Any,
    schema: dict[str, Any],
    *,
    eos_token_id: int | list[int] | None = None,
) -> Any:
    global _CACHED_STORY_EOS_IDS, _CACHED_STORY_VOCAB_DATA
    # Set before importing LMFE; putting the apostrophe/backslash alphabet in
    # Modal Image.env creates an invalid Dockerfile ENV instruction.
    os.environ["LMFE_DEFAULT_ALPHABET"] = LMFE_VIETNAMESE_JSON_ALPHABET
    try:
        from lmformatenforcer import JsonSchemaParser
        from lmformatenforcer.tokenenforcer import (
            TokenEnforcer,
            TokenEnforcerTokenizerData,
        )
    except ImportError as exc:
        raise RuntimeError("MODAL_CONSTRAINED_DECODER_UNAVAILABLE") from exc
    effective_eos_token_id = (
        tokenizer.eos_token_id if eos_token_id is None else eos_token_id
    )
    eos_token_ids = (
        tuple(effective_eos_token_id)
        if isinstance(effective_eos_token_id, list)
        else (effective_eos_token_id,)
    )
    if _CACHED_STORY_VOCAB_DATA is None or eos_token_ids != _CACHED_STORY_EOS_IDS:
        _CACHED_STORY_VOCAB_DATA = _build_lmfe_tokenizer_data(
            tokenizer,
            TokenEnforcerTokenizerData,
            eos_token_id=effective_eos_token_id,
        )
        _CACHED_STORY_EOS_IDS = eos_token_ids
    token_enforcer = TokenEnforcer(
        _CACHED_STORY_VOCAB_DATA,
        JsonSchemaParser(schema),
    )
    diagnostics: dict[str, Any] = {
        "callback_calls": 0,
        "string_limit_boundary_checks": 0,
        "string_limit_boundary_violations": 0,
        "max_observed_string_length": 0,
        "max_active_string_limit": 0,
        "unbounded_active_string_calls": 0,
        "force_stop_parser_calls": 0,
        "last_parser_can_end": False,
        "last_model_eos_allowed": False,
        "last_parser_state_class": "unknown",
        "model_eos_token_ids": _normalize_token_ids(effective_eos_token_id),
    }
    previous_sequence: tuple[int, ...] | None = None
    previous_boundary_tokens: list[int] | None = None

    def prefix_allowed_tokens_fn(_batch_id: int, input_ids: Any) -> list[int]:
        nonlocal previous_sequence, previous_boundary_tokens
        token_sequence = tuple(input_ids.tolist())
        if (
            previous_sequence is not None
            and len(token_sequence) == len(previous_sequence) + 1
            and token_sequence[:-1] == previous_sequence
            and previous_boundary_tokens is not None
        ):
            diagnostics["string_limit_boundary_checks"] += 1
            if token_sequence[-1] not in previous_boundary_tokens:
                diagnostics["string_limit_boundary_violations"] += 1
        allowed_tokens = token_enforcer.get_allowed_tokens(input_ids.tolist())
        # LMFE 0.11.x returns TokenList; accept its public token list explicitly.
        values = getattr(allowed_tokens, "allowed_tokens", allowed_tokens)
        parser_state = getattr(token_enforcer, "prefix_states", {}).get(token_sequence)
        parser = getattr(parser_state, "parser", None)
        diagnostics["last_parser_state_class"] = type(parser).__name__
        can_end = getattr(parser, "can_end", None)
        diagnostics["last_parser_can_end"] = (
            bool(can_end()) if callable(can_end) else False
        )
        diagnostics["last_model_eos_allowed"] = any(
            token_id in values
            for token_id in _normalize_token_ids(effective_eos_token_id)
        )
        if type(parser).__name__ == "ForceStopParser":
            diagnostics["force_stop_parser_calls"] += 1
        active_string = next(
            (
                item
                for item in reversed(getattr(parser, "object_stack", []))
                if hasattr(item, "parsed_string") and hasattr(item, "max_length")
            ),
            None,
        )
        previous_boundary_tokens = None
        if active_string is not None:
            current_length = len(active_string.parsed_string)
            maximum_length = active_string.max_length
            diagnostics["max_observed_string_length"] = max(
                diagnostics["max_observed_string_length"], current_length
            )
            if maximum_length is None:
                diagnostics["unbounded_active_string_calls"] += 1
            else:
                diagnostics["max_active_string_limit"] = max(
                    diagnostics["max_active_string_limit"], maximum_length
                )
                if current_length >= maximum_length:
                    previous_boundary_tokens = list(values)
        diagnostics["callback_calls"] += 1
        previous_sequence = token_sequence
        return list(values)

    prefix_allowed_tokens_fn.decoder_diagnostics = diagnostics
    prefix_allowed_tokens_fn.decoder = getattr(token_enforcer, "decoder", None)
    prefix_allowed_tokens_fn.json_schema = schema
    prefix_allowed_tokens_fn.tokenizer_special_ids = set(
        getattr(tokenizer, "all_special_ids", ())
    )
    return prefix_allowed_tokens_fn


def _json_prefix_decoder_diagnostics(
    prefix_allowed_tokens_fn: Any,
    *,
    generated: Any | None = None,
    input_token_count: int | None = None,
) -> dict[str, Any]:
    values = getattr(prefix_allowed_tokens_fn, "decoder_diagnostics", {})
    result = {
        key: value
        for key, value in values.items()
        if key
        in {
            "callback_calls",
            "string_limit_boundary_checks",
            "string_limit_boundary_violations",
            "max_observed_string_length",
            "max_active_string_limit",
            "unbounded_active_string_calls",
            "force_stop_parser_calls",
            "last_parser_can_end",
            "last_model_eos_allowed",
            "last_parser_state_class",
            "model_eos_token_ids",
        }
    }
    if generated is not None and input_token_count is not None:
        generated_ids = [
            int(token_id) for token_id in generated[0, input_token_count:].tolist()
        ]
        final_token_id = generated_ids[-1] if generated_ids else None
        eos_token_ids = _normalize_token_ids(values.get("model_eos_token_ids", []))
        if final_token_id is not None:
            result["final_model_eos_was_allowed_at_previous_prefix"] = (
                final_token_id in eos_token_ids
                and bool(values.get("last_model_eos_allowed"))
            )
            result["final_model_eos_prefix_parser_can_end"] = bool(
                values.get("last_parser_can_end")
            )
            result["final_token_id"] = final_token_id
        tokenizer_special_ids = getattr(
            prefix_allowed_tokens_fn, "tokenizer_special_ids", set()
        )
        result["generated_special_token_count"] = sum(
            token_id in tokenizer_special_ids for token_id in generated_ids
        )
        result["generated_non_eos_special_token_count"] = sum(
            token_id in tokenizer_special_ids and token_id not in eos_token_ids
            for token_id in generated_ids
        )
        decoder = getattr(prefix_allowed_tokens_fn, "decoder", None)
        if callable(decoder):
            tokens_for_decode = (
                generated_ids[:-1] if final_token_id in eos_token_ids else generated_ids
            )
            enforcer_text = decoder(tokens_for_decode)
            enforcer_shape = _json_output_diagnostics(enforcer_text)
            for key in (
                "decoded_character_count",
                "json_complete",
                "json_error",
                "json_error_position",
                "unterminated_string_key",
                "unterminated_string_character_count",
            ):
                if key in enforcer_shape:
                    result[f"enforcer_decoder_{key}"] = enforcer_shape[key]
            try:
                from lmformatenforcer import JsonSchemaParser

                replay_parser = JsonSchemaParser(
                    getattr(prefix_allowed_tokens_fn, "json_schema", None)
                )
                replay_errors = 0
                for character in enforcer_text:
                    try:
                        replay_parser = replay_parser.add_character(character)
                    except Exception:  # noqa: BLE001 - record parser behavior only.
                        replay_errors += 1
                        break
                result["replay_parser_can_end"] = replay_parser.can_end()
                result["replay_parser_error_count"] = replay_errors
                result["incremental_vs_replay_can_end_mismatch"] = (
                    bool(values.get("last_parser_can_end")) != replay_parser.can_end()
                )
            except Exception:  # noqa: BLE001 - safe diagnostics must not mask AI errors.
                result["replay_parser_diagnostic_error"] = True
    return result


def _build_lmfe_tokenizer_data(
    tokenizer: Any,
    tokenizer_data_type: Any,
    *,
    eos_token_id: int | list[int] | None = None,
) -> Any:
    """Build LMFE tokenizer data without importing its Transformers 4.x adapter.

    LMFE's adapter imports ``transformers.tokenization_utils.PreTrainedTokenizerBase``,
    which is absent in the pinned Transformers 5.x runtime. TokenEnforcer itself is
    provider-agnostic, so construct its documented token table directly.
    """

    vocab_size = len(tokenizer)
    token_zero = tokenizer.encode("0")[-1]
    special_ids = set(tokenizer.all_special_ids)
    effective_eos_token_id = (
        tokenizer.eos_token_id if eos_token_id is None else eos_token_id
    )
    if isinstance(effective_eos_token_id, int):
        special_ids.add(effective_eos_token_id)
    elif effective_eos_token_id is not None:
        special_ids.update(effective_eos_token_id)

    def decode(tokens: list[int]) -> str:
        # Keep decoder normalization identical to LMFE's Transformers adapter.
        # The prefix tree must use the same tokenizer.decode defaults as the
        # incremental decoder or bounded strings can be undercounted.
        return tokenizer.decode(tokens).rstrip("�")

    regular_tokens: list[tuple[int, str, bool]] = []
    for token_id in range(vocab_size):
        if token_id in special_ids:
            continue
        decoded_after_zero = tokenizer.decode([token_zero, token_id])
        decoded_token = tokenizer.decode([token_id])
        regular_tokens.append(
            (
                token_id,
                decoded_after_zero[1:],
                len(decoded_after_zero) > len(decoded_token),
            )
        )

    return tokenizer_data_type(
        regular_tokens,
        decode,
        effective_eos_token_id,
        use_bitmask=False,
        vocab_size=vocab_size,
    )


@app.function(
    name="check-qwen35-decoder-readiness",
    image=_story_text_image,
    cpu=2.0,
    memory=8_192,
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=120,
    retries=0,
)
def check_qwen35_decoder_readiness() -> dict[str, str]:
    """Verify Qwen3.5/Transformers and LMFE imports without loading a model."""

    import importlib.metadata

    import transformers
    from lmformatenforcer import JsonSchemaParser
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    from transformers import AutoModelForMultimodalLM, AutoProcessor

    return {
        "status": "ready",
        "transformers_version": transformers.__version__,
        "lm_format_enforcer_version": importlib.metadata.version("lm-format-enforcer"),
        "model_loader": AutoModelForMultimodalLM.__name__,
        "processor_loader": AutoProcessor.__name__,
        "schema_parser": JsonSchemaParser.__name__,
        "token_enforcer": TokenEnforcer.__name__,
        "tokenizer_data": TokenEnforcerTokenizerData.__name__,
    }


@app.function(
    name="probe-qwen35-constrained-decoder",
    image=_story_text_image,
    cpu=4.0,
    memory=16_384,
    volumes={MODEL_MOUNT: model_volume.with_mount_options(read_only=True)},
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=300,
    retries=0,
)
def probe_qwen35_constrained_decoder() -> dict[str, Any]:
    """Exercise LMFE maxLength and model EOS with the exact pinned Qwen tokenizer."""

    import torch
    from transformers import AutoConfig, AutoProcessor, GenerationConfig

    model_path = Path(TEXT_MODEL_DIR)
    _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    processor = AutoProcessor.from_pretrained(
        str(model_path), local_files_only=True, trust_remote_code=False
    )
    tokenizer = processor.tokenizer
    model_config = AutoConfig.from_pretrained(
        str(model_path), local_files_only=True, trust_remote_code=False
    )
    generation_config = GenerationConfig.from_model_config(model_config)
    model_eos_token_id = generation_config.eos_token_id
    eos_token_ids = (
        [int(item) for item in model_eos_token_id]
        if isinstance(model_eos_token_id, list)
        else [int(model_eos_token_id)]
    )
    prompt_token_id = next(
        (
            int(token_id)
            for token_id in (
                tokenizer.bos_token_id,
                tokenizer.pad_token_id,
                tokenizer.unk_token_id,
                0,
            )
            if token_id is not None and int(token_id) not in eos_token_ids
        ),
        0,
    )
    schema = {
        "type": "object",
        "properties": {"value": {"type": "string", "minLength": 1, "maxLength": 4}},
        "required": ["value"],
        "additionalProperties": False,
    }

    def check_candidate(
        text: str, candidate_schema: dict[str, Any] = schema
    ) -> dict[str, Any]:
        token_ids = tokenizer.encode(text, add_special_tokens=False)
        if not token_ids:
            return {"accepted": False, "blocked_token_index": 0, "eos_allowed": False}
        prefix_fn = _build_json_prefix_allowed_tokens_fn(
            tokenizer, candidate_schema, eos_token_id=model_eos_token_id
        )
        sequence = [prompt_token_id]
        for index, token_id in enumerate(token_ids):
            allowed = prefix_fn(0, torch.tensor(sequence, dtype=torch.long))
            if int(token_id) not in allowed:
                return {
                    "accepted": False,
                    "blocked_token_index": index,
                    "eos_allowed": False,
                }
            sequence.append(int(token_id))
        allowed_after_candidate = prefix_fn(0, torch.tensor(sequence, dtype=torch.long))
        return {
            "accepted": True,
            "blocked_token_index": None,
            "eos_allowed": any(
                token_id in allowed_after_candidate for token_id in eos_token_ids
            ),
        }

    valid_text = '{"value":"bướm"}'
    overlong_text = '{"value":"bướmx"}'
    valid = check_candidate(valid_text)
    overlong = check_candidate(overlong_text)
    story_schema = _parent_story_content_json_schema()
    story_prefix = (
        '{"title":"t","story":{"opening":"o","middle":"m","ending":"e"},'
        '"scenes":[{"title":"t","action":"a","visual_prompt":"v","narration":"'
    )
    story_overlong = check_candidate(story_prefix + ("n" * 121), story_schema)
    story_partial_vietnamese = check_candidate(
        story_prefix + "b" + chr(0x01B0) + chr(0x1EDB), story_schema
    )
    teacher_schema = _teacher_deck_json_schema(3)
    teacher_prefix = '{"steps":[{"step_index":1,"instruction":"i","placement":"'
    teacher_overlong = check_candidate(teacher_prefix + ("p" * 81), teacher_schema)
    result = {
        "status": (
            "ready"
            if valid["accepted"]
            and valid["eos_allowed"]
            and not overlong["accepted"]
            and not story_overlong["accepted"]
            and story_partial_vietnamese["accepted"]
            and not story_partial_vietnamese["eos_allowed"]
            and not teacher_overlong["accepted"]
            else "failed"
        ),
        "model_id": TEXT_MODEL_ID,
        "revision": TEXT_MODEL_REVISION,
        "vocab_size": len(tokenizer),
        "tokenizer_eos_token_id": tokenizer.eos_token_id,
        "model_eos_token_ids": eos_token_ids,
        "model_eos_is_tokenizer_special": all(
            token_id in set(tokenizer.all_special_ids) for token_id in eos_token_ids
        ),
        "valid_four_character_vietnamese_value": valid,
        "overlong_five_character_vietnamese_value": overlong,
        "story_nested_narration_overlength_rejected": not story_overlong["accepted"],
        "story_partial_vietnamese_eos_blocked": (
            story_partial_vietnamese["accepted"]
            and not story_partial_vietnamese["eos_allowed"]
        ),
        "teacher_nested_placement_overlength_rejected": not teacher_overlong[
            "accepted"
        ],
    }
    if result["status"] != "ready":
        raise RuntimeError("MODAL_QWEN35_CONSTRAINED_DECODER_PROBE_FAILED")
    return result


@app.function(
    name="probe-qwen35-generation-constraints",
    image=_story_text_image,
    gpu=["L40S", "L4", "A10"],
    cpu=4.0,
    memory=32_768,
    volumes={MODEL_MOUNT: model_volume.with_mount_options(read_only=True)},
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=600,
    retries=0,
)
def probe_qwen35_generation_constraints() -> dict[str, Any]:
    """Verify constrained decoding inside the pinned Qwen generate() implementation."""

    import torch

    processor, model = _load_text_model()
    tokenizer = processor.tokenizer
    schema = {
        "type": "object",
        "properties": {"value": {"type": "string", "minLength": 1, "maxLength": 4}},
        "required": ["value"],
        "additionalProperties": False,
    }
    messages = [
        {
            "role": "system",
            "content": "Return exactly one JSON object with a short Vietnamese value.",
        },
        {"role": "user", "content": "Choose a simple word."},
    ]
    encoded = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
        return_tensors="pt",
        return_dict=True,
    ).to(model.device)
    input_token_count = int(encoded["input_ids"].shape[-1])
    prefix_allowed_tokens_fn = _build_json_prefix_allowed_tokens_fn(
        tokenizer,
        schema,
        eos_token_id=model.generation_config.eos_token_id,
    )
    callback_allowed_by_length: dict[int, set[int]] = {}

    def tracked_prefix_allowed_tokens_fn(batch_id: int, input_ids: Any) -> list[int]:
        allowed = prefix_allowed_tokens_fn(batch_id, input_ids)
        callback_allowed_by_length[int(input_ids.shape[-1])] = set(allowed)
        return allowed

    generation_started = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=64,
            pad_token_id=_generation_pad_token_id(model, tokenizer),
            prefix_allowed_tokens_fn=tracked_prefix_allowed_tokens_fn,
        )
    generation_seconds = time.perf_counter() - generation_started
    generated_ids = [
        int(token_id) for token_id in generated[0, input_token_count:].tolist()
    ]
    all_generated_tokens_allowed = all(
        token_id in callback_allowed_by_length.get(input_token_count + offset, set())
        for offset, token_id in enumerate(generated_ids)
    )
    text = tokenizer.decode(generated[0, input_token_count:], skip_special_tokens=True)
    parsed = False
    value_length: int | None = None
    try:
        output = json.loads(text)
        value = output.get("value") if isinstance(output, dict) else None
        parsed = set(output) == {"value"} and isinstance(value, str)
        value_length = len(value) if isinstance(value, str) else None
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    result = {
        "status": (
            "ready"
            if parsed
            and value_length is not None
            and 1 <= value_length <= 4
            and all_generated_tokens_allowed
            else "failed"
        ),
        "model_id": TEXT_MODEL_ID,
        "revision": TEXT_MODEL_REVISION,
        "input_token_count": input_token_count,
        "output_token_count": len(generated_ids),
        "generation_seconds": round(generation_seconds, 3),
        "prefix_callback_calls": len(callback_allowed_by_length),
        "all_generated_tokens_were_allowed": all_generated_tokens_allowed,
        "json_valid": parsed,
        "value_length": value_length,
    }
    if result["status"] != "ready":
        raise RuntimeError("MODAL_QWEN35_GENERATION_CONSTRAINT_PROBE_FAILED")
    return result


def _parent_story_prompt(request: dict[str, Any]) -> str:
    subject = str(request["confirmed_subject"]).strip()
    features = [str(item).strip()[:160] for item in request["visible_features"]]
    age = int(request["child_age_months"])
    idea = (
        str(request["adult_confirmed_idea"]).strip()
        or "Không có ý tưởng bổ sung từ người lớn."
    )
    rewrite = (
        request.get("rewrite_instruction")
        or "Không có yêu cầu viết lại. Đây là bản đầu."
    )
    subject_facts = ""
    folded_subject = _fold_vi(subject)
    if "buom" in folded_subject or "butterfly" in folded_subject:
        subject_facts = (
            "Kiến thức bắt buộc về vòng đời bướm: opening phải nói về trứng; middle phải kể "
            "sâu bướm ăn lá rồi hóa nhộng; ending phải kể bướm trưởng thành chui ra khỏi nhộng. "
            "Giữ đúng thứ tự trứng → sâu bướm → nhộng → bướm trưởng thành. Không viết trứng nở "
            "thành bướm trưởng thành."
        )
    return (
        "Tạo bản nháp story tiếng Việt, Montessori-inspired, lấy trẻ làm trung tâm. "
        "Trả đúng một JSON object: {title, story, scenes}. story có opening, middle, ending. "
        "Tạo đúng 5 cảnh nối tiếp. Mỗi scene chỉ có title, action, visual_prompt, narration, "
        "character_anchors; không thêm key khác. hệ thống sẽ tự thêm số thứ tự và thời gian. "
        "Mỗi phần story chỉ viết 1-2 câu hoàn chỉnh, mục tiêu 100-140 ký tự. Mỗi action là "
        "một câu tiếng Việt ngắn, mục tiêu 45-70 ký tự, tối đa 180. Mỗi visual_prompt là một câu "
        "tiếng Anh ngắn, mục tiêu 55-75 ký tự, tối đa 240. Narration mỗi cảnh gồm 1-2 câu ngắn, "
        "Narration may use concise sentences. visual_prompt may be a short English phrase; terminal punctuation is optional. "
        "Mọi câu ngắn, cụ thể, không lặp. Giới hạn tối đa: "
        "title 80 ký tự; mỗi phần story 300; scene title 40; action 180; visual_prompt 240; "
        "narration 180; 1-2 character_anchors, mỗi anchor 40 ký tự. "
        "Bám chủ thể người lớn xác nhận và đặc điểm nhìn thấy; giữ nhân vật nhất quán. Người lớn "
        "hướng dẫn, trẻ quan sát và tự khám phá. Không gán tên, cảm xúc, năng lực, danh tính hoặc "
        "chẩn đoán cho người vẽ; không có tên trẻ; không thêm activity, lời khuyên y tế, "
        "nguy hiểm, "
        "bạo lực, quảng cáo hoặc bài học áp đặt. Story là DRAFT để người lớn rà soát. "
        f"Chủ thể đã xác nhận: {subject}. Đặc điểm nhìn thấy: "
        f"{json.dumps(features, ensure_ascii=False)}. Tuổi chính xác: {age} tháng. "
        f"Ý tưởng người lớn xác nhận: {idea}. Hướng viết lại: {rewrite}. {subject_facts}"
    )


def _fold_vi(value: str) -> str:
    import unicodedata

    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )


def _validate_butterfly_facts(story: dict[str, Any], subject: str) -> None:
    folded_subject = _fold_vi(subject)
    if "buom" not in folded_subject and "butterfly" not in folded_subject:
        return
    all_text = _fold_vi(
        " ".join(
            [
                story["story"]["opening"],
                story["story"]["middle"],
                story["story"]["ending"],
                *(
                    scene["action"] + " " + scene["narration"]
                    for scene in story["scenes"]
                ),
            ]
        )
    )
    forbidden = (
        r"trung\s+(?:no|nở)\s+(?:(?:ra|thanh)\s+)?(?:con\s+)?buom",
        r"buom(?:\s+\w+){0,4}\s+(?:tim|kiem|xay|lam)\s+(?:mot\s+)?to",
        r"butterfly\s+(?:hatches|looks?\s+for|builds?\s+(?:a\s+)?nest)",
    )
    if any(re.search(pattern, all_text) for pattern in forbidden):
        raise StoryOutputValidationError("EDUCATIONAL_FACT_FORBIDDEN_CLAIM")
    lifecycle_text = _fold_vi(
        " ".join(story["story"][section] for section in ("opening", "middle", "ending"))
    )
    phases = (
        r"\btrung\b",
        r"\b(?:sau\s+buom|au\s+trung)\b",
        r"\bnhong\b",
        r"\b(?:buom\s+truong\s+thanh|buom\s+(?:chui|bay)\s+ra\s+khoi\s+nhong)\b",
    )
    positions = [
        (match.start() if (match := re.search(phase, lifecycle_text)) else None)
        for phase in phases
    ]
    if any(position is None for position in positions):
        raise StoryOutputValidationError("EDUCATIONAL_FACT_STAGE_MISSING")
    if positions != sorted(positions):
        raise StoryOutputValidationError("EDUCATIONAL_FACT_ORDER_INVALID")


def _verify_marker(path: Path, model_id: str, revision: str) -> None:
    if not path.is_file():
        raise RuntimeError("MODAL_MODEL_NOT_READY")
    marker = json.loads(path.read_text(encoding="utf-8"))
    if marker.get("model_id") != model_id or marker.get("revision") != revision:
        raise RuntimeError("MODAL_MODEL_REVISION_MISMATCH")


def _verify_text_checkpoint(path: Path) -> None:
    if not all(
        (path / name).is_file()
        for name in ("config.json", "tokenizer.json", "preprocessor_config.json")
    ):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")
    index_path = path / "model.safetensors.index.json"
    if index_path.is_file():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            weight_map = index.get("weight_map") if isinstance(index, dict) else None
            shard_names = (
                set(weight_map.values()) if isinstance(weight_map, dict) else set()
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE") from None
        if not shard_names or any(
            not isinstance(name, str)
            or Path(name).name != name
            or not (path / name).is_file()
            for name in shard_names
        ):
            raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")
    elif (
        not list(path.glob("model-*.safetensors"))
        and not (path / "model.safetensors").is_file()
    ):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")


def _verify_asr_checkpoint(path: Path) -> None:
    required = ("config.json", "model.bin", "tokenizer.json", "vocabulary.json")
    if not all((path / name).is_file() for name in required):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")


def _verify_tts_checkpoint(model_path: Path, codec_path: Path) -> None:
    required_model = (
        "onnx_update/config.json",
        "onnx_update/tokenizer.json",
        "onnx_update/vieneu_prefill.onnx",
        "onnx_update/vieneu_decode_step.onnx",
        "onnx_update/vieneu_acoustic_cached.onnx",
        "onnx_update/vieneu_backbone_shared.data",
        "onnx_update/vieneu_v3_heads.npz",
    )
    required_codec = (
        "moss_audio_tokenizer_decode_full.onnx",
        "moss_audio_tokenizer_decode_shared.data",
    )
    if not all((model_path / name).is_file() for name in required_model):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")
    if not all((codec_path / name).is_file() for name in required_codec):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")


_CACHED_TEXT_MODEL: Any | None = None
_CACHED_TEXT_PREPROCESSOR: Any | None = None


def _load_text_model() -> tuple[Any, Any]:
    global _CACHED_TEXT_MODEL, _CACHED_TEXT_PREPROCESSOR
    if _CACHED_TEXT_MODEL is not None and _CACHED_TEXT_PREPROCESSOR is not None:
        return _CACHED_TEXT_PREPROCESSOR, _CACHED_TEXT_MODEL
    import torch
    from transformers import AutoModelForMultimodalLM, AutoProcessor

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    _CACHED_TEXT_PREPROCESSOR = AutoProcessor.from_pretrained(
        TEXT_MODEL_DIR,
        local_files_only=True,
        trust_remote_code=False,
    )
    _CACHED_TEXT_MODEL = AutoModelForMultimodalLM.from_pretrained(
        TEXT_MODEL_DIR,
        dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="sdpa",
        low_cpu_mem_usage=True,
        local_files_only=True,
        trust_remote_code=False,
    ).eval()
    return _CACHED_TEXT_PREPROCESSOR, _CACHED_TEXT_MODEL
