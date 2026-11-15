"""Private Modal dev workers for the SRS story, TTS, and ASR POCs."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import sys
import time
import unicodedata
from copy import deepcopy
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
from openclipart_catalog import (
    CATALOG_ROOT_NAME,
    read_catalog_manifest,
    search_guide_candidates,
    source_reference_metadata,
)
from worker_observability import (
    observed_worker,
    refresh_worker_volume,
    worker_phase,
    worker_stage,
)

APP_NAME = "sketch2life-srs23-language-audio-dev"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
SVG_CATALOG_VOLUME_NAME = "sketch2life-openclipart-catalog-dev"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
SVG_CATALOG_MOUNT = "/svg-catalog"
TEXT_MODEL_ID = "Qwen/Qwen3.5-9B"
TEXT_MODEL_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
TEXT_MODEL_DIR = f"{MODEL_MOUNT}/qwen3_5_9b/{TEXT_MODEL_REVISION}"
TEXT_MODEL_MARKER = f"{TEXT_MODEL_DIR}/sketch2life-model-manifest.json"
SVG_TOPIC_GUIDE_MAX_OUTPUT_TOKENS = 12_288
SVG_TOPIC_GUIDE_MIN_CONSTRUCTION_STROKES = 8
SVG_TOPIC_GUIDE_MAX_CONSTRUCTION_STROKES = 20
SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT = SVG_TOPIC_GUIDE_MIN_CONSTRUCTION_STROKES
SVG_TOPIC_GUIDE_GENERATION_TEMPERATURE = 0.65
SVG_TOPIC_GUIDE_GENERATION_TOP_P = 0.9
SVG_TOPIC_GUIDE_MAX_STROKE_CHARS = 768
SVG_TOPIC_GUIDE_MAX_TOTAL_GEOMETRY_CHARS = 16_384
SVG_CATALOG_SEARCH_MAX_OUTPUT_TOKENS = 128
SVG_CATALOG_PLAN_MAX_OUTPUT_TOKENS = 4_096
SVG_CATALOG_SEGMENT_PLAN_SYSTEM_PROMPT = (
    "Bạn chỉ phân chia thứ tự sư phạm cho các đoạn SVG nguồn đã có trong atlas. "
    "Không được sáng tác hoặc trả tọa độ, path, hình học hay chi tiết. Mỗi segment_id "
    "phải được gán đúng một bước. Không áp đặt thứ tự chung kiểu thân trước, đầu sau: "
    "hãy bám chính xác vào các nét mới được thêm ở từng bước. Chỉ mô tả nét của các "
    "segment thuộc bước hiện tại; không suy đoán bộ phận từ ảnh màu nếu nét mới chưa "
    "thể hiện rõ bộ phận đó. Khi chưa nhận ra bộ phận, dùng hình dạng, vị trí, hướng "
    "cong và cách nối nhìn thấy được thay vì đoán tên giải phẫu. Tuân thủ chính xác JSON schema."
)
SVG_CATALOG_VISUAL_REVIEW_SYSTEM_PROMPT = (
    "Bạn rà soát một hướng dẫn vẽ SVG đã có. Chỉ được sửa thứ tự gán segment vào bước và lời "
    "hướng dẫn tiếng Việt để khớp hình tích lũy. Không tạo, sửa, bỏ, chia, ghép hoặc đổi bất kỳ "
    "geometry/path/segment ID nào. Giữ nguyên tiêu đề, số bước và hai nét đã ghim ở bước 1. "
    "Mỗi chỉ dẫn chỉ nói về nét màu xanh mới xuất hiện trong ô bước đó; nét xám đã có từ trước. "
    "Dùng ảnh màu làm chuẩn nhận diện, atlas để tra từng segment, và contact sheet để kiểm tra "
    "tiến trình. Nếu không thể xác định bộ phận, mô tả hình dạng/hướng/vị trí thay vì đoán. "
    "Tuân thủ chính xác JSON schema."
)
TEACHER_SVG_REFERENCE_PACK_SHA256 = (
    "319d25932c8d4bc8c362b6af19ecded75cb1015d7f8cc19387c9685a74349af0"
)
TEACHER_SVG_REFERENCE_PACK_LOCAL_PATH = (
    _MODULE_DIR / "data" / "teacher_svg_illustration" / "reference-pack-v1.json"
)
TEACHER_SVG_REFERENCE_PACK_WORKER_PATH = Path(
    "/root/teacher_svg_illustration_reference_pack_v1.json"
)
TEACHER_SVG_REFERENCE_PACK_CACHE: dict[str, Any] | None = None
ARCADIA_GALLUS_REFERENCE_PACK_LOCAL_PATH = (
    _MODULE_DIR / "data" / "arcadia_organism_strokes" / "gallus-gallus-v1.json"
)
ARCADIA_GALLUS_REFERENCE_SVG_LOCAL_PATH = (
    _MODULE_DIR / "data" / "arcadia_organism_strokes" / "gallus-gallus-source.svg"
)
ARCADIA_GALLUS_REFERENCE_PACK_WORKER_PATH = "/root/arcadia_gallus_stroke_reference_v1.json"
ARCADIA_GALLUS_REFERENCE_SVG_WORKER_PATH = "/root/arcadia_gallus_stroke_reference.svg"
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
_PARENT_ACTIVITY_ALLOWED_TAGS = {
    "nature", "animals", "insects", "plants", "colors", "water", "movement",
    "art", "music", "building", "sky_and_weather",
}
_PARENT_ACTIVITY_PII_PATTERNS = (
    re.compile(r"\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)"),
    re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE),
)


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
svg_catalog_volume = modal.Volume.from_name(
    SVG_CATALOG_VOLUME_NAME,
    environment_name="dev",
    create_if_missing=True,
    version=2,
)
health_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi>=0.115,<1")
    .add_local_file(str(_MODULE_DIR / "contracts.py"), "/root/contracts.py", copy=True)
    .add_local_file(
        str(_MODULE_DIR / "openclipart_catalog.py"),
        "/root/openclipart_catalog.py",
        copy=True,
    )
    .add_local_file(
        str(_MODULE_DIR / "worker_observability.py"),
        "/root/worker_observability.py",
        copy=True,
    )
)


@app.function(
    name="health-api",
    image=health_image,
    cpu=0.25,
    memory=256,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SVG_CATALOG_MOUNT: svg_catalog_volume.with_mount_options(read_only=True),
    },
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
        checkpoint_status = "ready"
        try:
            model_volume.reload()
            _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
            _verify_text_checkpoint(Path(TEXT_MODEL_DIR))
        except Exception:
            checkpoint_status = "not_ready"
        svg_catalog_status = "not_ready"
        try:
            svg_catalog_volume.reload()
            catalog_manifest = read_catalog_manifest(
                Path(SVG_CATALOG_MOUNT) / CATALOG_ROOT_NAME
            )
            if catalog_manifest and catalog_manifest.get("status") == "READY":
                svg_catalog_status = "ready"
        except Exception:
            svg_catalog_status = "not_ready"
        return {
            "status": "ok" if checkpoint_status == "ready" else "degraded",
            "app": APP_NAME,
            "health_scope": "deployed-app",
            "gpu_allocated": False,
            "inference_executed": False,
            "qwen_checkpoint": {
                "status": checkpoint_status,
                "model_id": TEXT_MODEL_ID,
                "revision": TEXT_MODEL_REVISION,
                "weights_present": checkpoint_status == "ready",
            },
            "svg_catalog": {
                "status": svg_catalog_status,
                "volume_name": SVG_CATALOG_VOLUME_NAME,
                "volume_version": 2,
                "inference_executed": False,
            },
        }

    return api

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
    modal.Image.from_registry(
        "nvidia/cuda:12.6.3-devel-ubuntu22.04", add_python="3.11"
    )
    .entrypoint([])
    .apt_install("build-essential", "ninja-build")
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
        "wheel==0.45.1",
        "lm-format-enforcer==0.11.3",
        "flash-linear-attention[cuda]==0.6.0",
    )
    .uv_pip_install(
        "causal-conv1d==1.7.0",
        extra_options="--no-build-isolation",
        env={"CXX": "g++", "CUDA_HOME": "/usr/local/cuda"},
    )
    .env(
        {
            "HF_HUB_DISABLE_TELEMETRY": "1",
        }
    )
)
_teacher_svg_illustration_image = _text_image.add_local_file(
    str(TEACHER_SVG_REFERENCE_PACK_LOCAL_PATH),
    "/root/teacher_svg_illustration_reference_pack_v1.json",
    copy=True,
)
_story_text_image = _text_image.env(
    {
        "HF_ENABLE_PARALLEL_LOADING": "true",
        "HF_PARALLEL_LOADING_WORKERS": "4",
        "LMFE_STRICT_JSON_FIELD_ORDER": "true",
    }
)
_svg_stroke_guide_image = (
    _story_text_image.apt_install("libcairo2")
    .pip_install("CairoSVG==2.7.1")
    .add_local_file(
        str(_MODULE_DIR / "openclipart_catalog.py"),
        "/root/openclipart_catalog.py",
        copy=True,
    )
    .add_local_file(
        str(ARCADIA_GALLUS_REFERENCE_PACK_LOCAL_PATH),
        ARCADIA_GALLUS_REFERENCE_PACK_WORKER_PATH,
        copy=True,
    )
    .add_local_file(
        str(ARCADIA_GALLUS_REFERENCE_SVG_LOCAL_PATH),
        ARCADIA_GALLUS_REFERENCE_SVG_WORKER_PATH,
        copy=True,
    )
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
        SVG_CATALOG_MOUNT: svg_catalog_volume.with_mount_options(read_only=True),
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

    if is_worker_warmup(payload):
        with worker_phase("warmup_checkpoint_and_model_load"):
            _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
            _load_text_model()
        import torch

        return worker_warmup_result(
            workload="story.generate",
            model_id=TEXT_MODEL_ID,
            model_revision=TEXT_MODEL_REVISION,
            gpu_allocated=torch.cuda.is_available(),
        )

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "story.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request, expected_asset="input/request.json")
    worker_stage("request_contract_validation")
    activity_digest = _validate_parent_story_worker_input(data)
    activity = data["primary_activity"]

    print(
        json.dumps(
            {
                "event": "story_primary_activity_context_validated",
                "activity_ref": activity["activity_ref"],
                "primary_activity_sha256": activity_digest,
                "activity_source": activity["source"],
            },
            sort_keys=True,
        ),
        flush=True,
    )

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
        SVG_CATALOG_MOUNT: svg_catalog_volume.with_mount_options(read_only=True),
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

    if is_worker_warmup(payload):
        with worker_phase("warmup_checkpoint_and_model_load"):
            _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
            _load_text_model()
        import torch

        return worker_warmup_result(
            workload="teacher.sketch-deck.generate",
            model_id=TEXT_MODEL_ID,
            model_revision=TEXT_MODEL_REVISION,
            gpu_allocated=torch.cuda.is_available(),
        )

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
    name="generate-teacher-svg-illustration-draft",
    image=_teacher_svg_illustration_image,
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
    workload="teacher.svg-illustration.generate",
    model_id=TEXT_MODEL_ID,
    model_revision=TEXT_MODEL_REVISION,
    gpu_class="L40S|L4|A10",
)
def generate_teacher_svg_illustration_draft(payload: dict[str, Any]) -> dict[str, Any]:
    """Return one bounded structured SVG draft from the pinned Qwen3.5 model."""

    if is_worker_warmup(payload):
        with worker_phase("warmup_checkpoint_and_model_load"):
            _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
            _load_text_model()
        import torch

        return worker_warmup_result(
            workload="teacher.svg-illustration.generate",
            model_id=TEXT_MODEL_ID,
            model_revision=TEXT_MODEL_REVISION,
            gpu_allocated=torch.cuda.is_available(),
        )

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "teacher.svg-illustration.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request, expected_asset="input/request.json")
    with worker_phase("input_contract_validation"):
        _validate_teacher_svg_illustration_input(data)
    with worker_phase("dataset_reference_selection"):
        reference = _select_teacher_svg_illustration_reference(data["topic"])
    with worker_phase("checkpoint_verification"):
        _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    with worker_phase("model_load"):
        processor, model = _load_text_model()

    messages = [
        {
            "role": "system",
            "content": (
                "Bạn tạo một minh họa vector SVG có hình dáng rõ, tự nhiên và thân thiện với trẻ em. "
                "Chỉ trả JSON theo schema; không viết XML, HTML, JavaScript, URL hoặc giải thích. "
                "Dùng đường cong Bézier cho đường bao hữu cơ, gắn các bộ phận vào đúng vị trí giải phẫu; "
                "tránh ghép nhiều hình tròn rời thành cơ thể. Không thêm chữ hoặc vật trang trí rời."
            ),
        },
        {
            "role": "user",
            "content": _teacher_svg_illustration_prompt(data, reference),
        },
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

    with worker_phase("constrained_decoder_setup"):
        prefix_allowed_tokens_fn = _build_json_prefix_allowed_tokens_fn(
            processor.tokenizer,
            _teacher_svg_illustration_json_schema(),
            eos_token_id=model.generation_config.eos_token_id,
        )
    max_new_tokens = _teacher_svg_illustration_max_output_tokens()
    generation_started = time.perf_counter()
    with worker_phase("model_inference"), torch.inference_mode():
        generated = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=_generation_pad_token_id(model, processor.tokenizer),
            prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
        )
    input_token_count = int(encoded["input_ids"].shape[-1])
    output_token_count = int(generated.shape[-1] - input_token_count)
    final_token_id = int(generated[0, -1].item()) if output_token_count else None
    eos_token_ids = model.generation_config.eos_token_id
    if isinstance(eos_token_ids, int):
        eos_token_ids = [eos_token_ids]
    text = processor.tokenizer.decode(
        generated[0, input_token_count:], skip_special_tokens=True
    ).strip()
    try:
        with worker_phase("output_parse_and_contract_validation"):
            result = _parse_teacher_svg_illustration(text)
    except RuntimeError as exc:
        print(
            json.dumps(
                {
                    "event": "teacher_svg_illustration_output_rejected",
                    "reason_code": str(exc),
                    "generation_seconds": round(time.perf_counter() - generation_started, 3),
                    "output_token_count": output_token_count,
                    "input_token_count": input_token_count,
                    "max_new_tokens": max_new_tokens,
                    "token_limit_reached": output_token_count >= max_new_tokens,
                    "reference_id": reference["reference_id"] if reference else None,
                    "reference_key": reference["retrieval_key"] if reference else None,
                    "reference_dataset_revision": (
                        reference["source_revision"] if reference else None
                    ),
                    "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    **_json_prefix_decoder_diagnostics(
                        prefix_allowed_tokens_fn,
                        generated=generated,
                        input_token_count=input_token_count,
                    ),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        raise RuntimeError("MODAL_SVG_ILLUSTRATION_OUTPUT_INVALID") from exc
    if output_token_count >= max_new_tokens or final_token_id not in (eos_token_ids or []):
        raise RuntimeError("MODAL_SVG_ILLUSTRATION_OUTPUT_TRUNCATED")
    print(
        json.dumps(
            {
                "event": "teacher_svg_illustration_generated",
                "generation_seconds": round(time.perf_counter() - generation_started, 3),
                "output_token_count": output_token_count,
                "input_token_count": input_token_count,
                "max_new_tokens": max_new_tokens,
                "ended_with_eos": True,
                "path_count": len(result["document"]["paths"]),
                "reference_id": reference["reference_id"] if reference else None,
                "reference_key": reference["retrieval_key"] if reference else None,
                "reference_dataset_revision": (
                    reference["source_revision"] if reference else None
                ),
                "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
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
        "result": result,
    }


@app.function(
    name="generate-topic-svg-stroke-guide-draft",
    image=_svg_stroke_guide_image,
    gpu=["L40S", "L4", "A10"],
    cpu=4.0,
    memory=32_768,
    volumes={
        MODEL_MOUNT: model_volume.with_mount_options(read_only=True),
        SCRATCH_MOUNT: scratch_volume.with_mount_options(read_only=True),
        SVG_CATALOG_MOUNT: svg_catalog_volume.with_mount_options(read_only=True),
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=120,
    timeout=1_800,
    retries=0,
)
@observed_worker(
    workload="svg.topic-stroke-guide.generate",
    model_id=TEXT_MODEL_ID,
    model_revision=TEXT_MODEL_REVISION,
    gpu_class="L40S|L4|A10",
    timeout_seconds=1_800,
)
def generate_topic_svg_stroke_guide_draft(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate a reference-conditioned construction guide for an adult-selected topic."""
    if is_worker_warmup(payload):
        with worker_phase("warmup_checkpoint_and_model_load"):
            _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
            _load_text_model()
        import torch

        return worker_warmup_result(
            workload="svg.topic-stroke-guide.generate",
            model_id=TEXT_MODEL_ID,
            model_revision=TEXT_MODEL_REVISION,
            gpu_allocated=torch.cuda.is_available(),
        )

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "svg.topic-stroke-guide.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request, expected_asset="input/request.json")
    with worker_phase("input_contract_validation"):
        _validate_svg_topic_guide_input(data)
    with worker_phase("svg_catalog_reload"):
        svg_catalog_volume.reload()
        catalog_manifest = read_catalog_manifest(
            Path(SVG_CATALOG_MOUNT) / CATALOG_ROOT_NAME
        )
        if not catalog_manifest or catalog_manifest.get("status") != "READY":
            raise RuntimeError("SVG_CATALOG_NOT_READY")
    with worker_phase("checkpoint_verification"):
        _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    with worker_phase("model_load"):
        processor, model = _load_text_model()

    with worker_phase("catalog_query_expansion"):
        search_terms = _generate_svg_catalog_search_terms(data, processor, model)
    with worker_phase("catalog_candidate_search"):
        candidates = search_guide_candidates(
            Path(SVG_CATALOG_MOUNT) / CATALOG_ROOT_NAME,
            search_terms,
            limit=8,
        )
        if not candidates:
            raise RuntimeError("SVG_CATALOG_NO_SAFE_SOURCE")
    with worker_phase("catalog_candidate_segmentation"):
        candidate = None
        segments: list[dict[str, Any]] = []
        segment_manifest: dict[str, Any] = {}
        segmentation_rejections: dict[str, int] = {}
        for candidate_option in candidates:
            try:
                candidate_segments, candidate_manifest = _segment_openclipart_candidate(
                    candidate_option
                )
            except _SvgSourceSegmentationError as exc:
                reason_code = str(exc)
                segmentation_rejections[reason_code] = (
                    segmentation_rejections.get(reason_code, 0) + 1
                )
                continue
            candidate = candidate_option
            segments = candidate_segments
            segment_manifest = candidate_manifest
            break
        if candidate is None:
            print(
                json.dumps(
                    {
                        "event": "svg_catalog_source_segmentation_unavailable",
                        "candidate_count": len(candidates),
                        "rejection_counts": segmentation_rejections,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            raise RuntimeError("SVG_CATALOG_NO_SEGMENTABLE_SOURCE")
        print(
            json.dumps(
                {
                    "event": "svg_catalog_source_segmented",
                    "candidate_count": len(candidates),
                    "selected_source_path_count": len(candidate["parsed_svg"]["paths"]),
                    "source_segment_count": segment_manifest["source_segment_count"],
                    "derived_chunk_count": len(segments),
                    "chunk_command_limit": segment_manifest["chunk_command_limit"],
                    "rejected_candidate_count": sum(segmentation_rejections.values()),
                    "source_asset_id": candidate.get("asset_id"),
                    "source_sha256": candidate.get("source_sha256"),
                },
                sort_keys=True,
            ),
            flush=True,
        )
    curated_plan = _curated_openclipart_source_plan(
        candidate,
        segments,
        first_step_segment_ids=segment_manifest["first_step_segment_ids"],
    )
    if curated_plan is not None:
        with worker_phase("curated_source_plan_validation"):
            result, reference_illustration = _build_openclipart_segment_guide(
                candidate, segments, curated_plan
            )
            reference_source = source_reference_metadata(candidate)
        print(
            json.dumps(
                {
                    "event": "svg_catalog_curated_source_sequence_applied",
                    "source_asset_id": candidate.get("asset_id"),
                    "source_sha256": candidate.get("source_sha256"),
                    "source_segment_count": len(segments),
                    "stage_count": len(curated_plan["stages"]),
                    "sequence_version": "openclipart-friendly-kitten-icon-v3",
                    "qwen_catalog_query_expansion_used": True,
                    "qwen_stage_assignment_used": False,
                    "qwen_visual_review_used": False,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        print(
            json.dumps(
                {
                    "event": "svg_catalog_construction_stroke_guide_generated",
                    "curated_source_sequence_applied": True,
                    "path_count": len(result["strokes"]),
                    "source_segment_count": segment_manifest["source_segment_count"],
                    "derived_chunk_count": len(segments),
                    "stage_count": len(result["stages"]),
                    "first_step_role_count": sum(
                        1
                        for stroke in result["strokes"]
                        if stroke["path_id"] in result["stages"][0]["stroke_ids"]
                        and stroke["role"] == "construction"
                    ),
                    "source_anchor_count": len(
                        {
                            source_path_id
                            for stroke in result["strokes"]
                            for source_path_id in stroke["source_path_ids"]
                        }
                    ),
                    "source_asset_id": reference_source["asset_id"],
                    "source_sha256": reference_source["source_sha256"],
                    "dataset_revision": reference_source["dataset_revision"],
                    "search_term_count": len(search_terms),
                    "qwen_catalog_query_expansion_used": True,
                    "draft_stage_assignment_inference_used": False,
                    "visual_review_inference_used": False,
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
            "reference_source": reference_source,
            "reference_illustration": reference_illustration,
            "source_path_ids": [
                item["path_id"] for item in candidate["parsed_svg"]["paths"]
            ],
            "source_segment_manifest": {
                **segment_manifest,
                "segments": [
                    {
                        "segment_id": segment["path_id"],
                        "source_path_id": segment["source_path_id"],
                        "source_subpath_indices": segment["source_subpath_indices"],
                        "source_segment_start": segment["source_segment_start"],
                        "source_segment_end": segment["source_segment_end"],
                        "geometry_sha256": hashlib.sha256(
                            segment["d"].encode("utf-8")
                        ).hexdigest(),
                    }
                    for segment in segments
                ],
            },
            "result": result,
        }
    with worker_phase("catalog_source_render"):
        source_image, path_atlas = _render_openclipart_candidate(
            candidate,
            atlas_paths=segments,
            atlas_view_box="0 0 512 512",
        )
    user_content: list[dict[str, Any]] = [
        {"type": "image", "image": source_image},
        {"type": "image", "image": path_atlas},
        {
            "type": "text",
            "text": _svg_catalog_segment_plan_prompt(
                data,
                candidate,
                segments,
                first_step_segment_ids=segment_manifest["first_step_segment_ids"],
            ),
        },
    ]
    messages = [
        {
            "role": "system",
            "content": SVG_CATALOG_SEGMENT_PLAN_SYSTEM_PROMPT,
        },
        {"role": "user", "content": user_content},
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

    with worker_phase("constrained_decoder_setup"):
        prefix_allowed_tokens_fn = _build_json_prefix_allowed_tokens_fn(
            processor.tokenizer,
            _svg_catalog_source_plan_schema(
                segments,
                first_step_segment_ids=segment_manifest["first_step_segment_ids"],
            ),
            eos_token_id=model.generation_config.eos_token_id,
        )
    max_new_tokens = SVG_TOPIC_GUIDE_MAX_OUTPUT_TOKENS
    generation_started = time.perf_counter()
    with worker_phase("model_inference"), torch.inference_mode():
        generated = model.generate(
            **encoded,
            do_sample=True,
            temperature=SVG_TOPIC_GUIDE_GENERATION_TEMPERATURE,
            top_p=SVG_TOPIC_GUIDE_GENERATION_TOP_P,
            max_new_tokens=max_new_tokens,
            pad_token_id=_generation_pad_token_id(model, processor.tokenizer),
            prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
        )
    input_token_count = int(encoded["input_ids"].shape[-1])
    output_token_count = int(generated.shape[-1] - input_token_count)
    final_token_id = int(generated[0, -1].item()) if output_token_count else None
    eos_token_ids = model.generation_config.eos_token_id
    if isinstance(eos_token_ids, int):
        eos_token_ids = [eos_token_ids]
    ended_with_model_eos = final_token_id in (eos_token_ids or [])
    text = processor.tokenizer.decode(
        generated[0, input_token_count:], skip_special_tokens=True
    ).strip()
    generation_seconds = round(time.perf_counter() - generation_started, 3)
    if not _svg_topic_guide_generation_is_complete(
        output_token_count=output_token_count,
        max_new_tokens=max_new_tokens,
        final_token_id=final_token_id,
        eos_token_ids=eos_token_ids,
    ):
        diagnostic = _svg_topic_guide_diagnostic_payload(
            reason_code="MODAL_SVG_CATALOG_PLAN_OUTPUT_TRUNCATED",
            output_token_count=output_token_count,
            input_token_count=input_token_count,
            max_new_tokens=max_new_tokens,
            final_token_id=final_token_id,
            eos_token_ids=eos_token_ids,
            tokenizer_eos_token_id=processor.tokenizer.eos_token_id,
            decoded_character_count=len(text),
            generation_seconds=generation_seconds,
        )
        _attach_svg_topic_guide_decoder_diagnostics(
            diagnostic,
            prefix_allowed_tokens_fn,
            generated=generated,
            input_token_count=input_token_count,
        )
        diagnostic["event"] = "svg_catalog_stroke_plan_output_truncated"
        print(json.dumps(diagnostic, ensure_ascii=False))
        raise RuntimeError("MODAL_SVG_CATALOG_PLAN_OUTPUT_TRUNCATED")
    with worker_phase("draft_plan_parse_and_source_identity_validation"):
        try:
            draft_plan = _parse_svg_catalog_source_plan(
                text,
                segments,
                first_step_segment_ids=segment_manifest["first_step_segment_ids"],
            )
            _build_openclipart_segment_guide(candidate, segments, draft_plan)
        except _SvgCatalogPlanValidationError as exc:
            exc.safe_diagnostics["output_token_count"] = output_token_count
            exc.safe_diagnostics["generation_duration_ms"] = round(
                generation_seconds * 1_000
            )
            print(
                json.dumps(
                    {
                        "event": "svg_catalog_construction_stroke_guide_rejected",
                        "error_code": exc.error_code,
                        **exc.safe_diagnostics,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            raise

    with worker_phase("visual_review_contact_sheet_render"):
        cumulative_review_sheet, cumulative_review_manifest = (
            _render_openclipart_cumulative_stage_review(candidate, segments, draft_plan)
        )
    review_prompt = _svg_catalog_visual_review_prompt(
        data,
        candidate,
        segments,
        draft_plan,
        first_step_segment_ids=segment_manifest["first_step_segment_ids"],
    )
    review_messages = [
        {"role": "system", "content": SVG_CATALOG_VISUAL_REVIEW_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "image", "image": source_image},
                {"type": "image", "image": path_atlas},
                {"type": "image", "image": cumulative_review_sheet},
                {"type": "text", "text": review_prompt},
            ],
        },
    ]
    with worker_phase("visual_review_prompt_encoding"):
        review_encoded = processor.apply_chat_template(
            review_messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors="pt",
            return_dict=True,
        ).to(model.device)
    with worker_phase("visual_review_constrained_decoder_setup"):
        review_prefix_allowed_tokens_fn = _build_json_prefix_allowed_tokens_fn(
            processor.tokenizer,
            _svg_catalog_visual_review_schema(
                segments,
                first_step_segment_ids=segment_manifest["first_step_segment_ids"],
                title_vi=draft_plan["title_vi"],
                stage_count=len(draft_plan["stages"]),
            ),
            eos_token_id=model.generation_config.eos_token_id,
        )
    review_generation_started = time.perf_counter()
    with worker_phase("visual_review_inference"), torch.inference_mode():
        review_generated = model.generate(
            **review_encoded,
            do_sample=False,
            max_new_tokens=SVG_CATALOG_PLAN_MAX_OUTPUT_TOKENS,
            pad_token_id=_generation_pad_token_id(model, processor.tokenizer),
            prefix_allowed_tokens_fn=review_prefix_allowed_tokens_fn,
        )
    review_input_token_count = int(review_encoded["input_ids"].shape[-1])
    review_output_token_count = int(
        review_generated.shape[-1] - review_input_token_count
    )
    review_final_token_id = (
        int(review_generated[0, -1].item()) if review_output_token_count else None
    )
    review_text = processor.tokenizer.decode(
        review_generated[0, review_input_token_count:], skip_special_tokens=True
    ).strip()
    review_generation_seconds = round(time.perf_counter() - review_generation_started, 3)
    if not _svg_topic_guide_generation_is_complete(
        output_token_count=review_output_token_count,
        max_new_tokens=SVG_CATALOG_PLAN_MAX_OUTPUT_TOKENS,
        final_token_id=review_final_token_id,
        eos_token_ids=eos_token_ids,
    ):
        diagnostic = _svg_topic_guide_diagnostic_payload(
            reason_code="MODAL_SVG_CATALOG_VISUAL_REVIEW_OUTPUT_TRUNCATED",
            output_token_count=review_output_token_count,
            input_token_count=review_input_token_count,
            max_new_tokens=SVG_CATALOG_PLAN_MAX_OUTPUT_TOKENS,
            final_token_id=review_final_token_id,
            eos_token_ids=eos_token_ids,
            tokenizer_eos_token_id=processor.tokenizer.eos_token_id,
            decoded_character_count=len(review_text),
            generation_seconds=review_generation_seconds,
        )
        _attach_svg_topic_guide_decoder_diagnostics(
            diagnostic,
            review_prefix_allowed_tokens_fn,
            generated=review_generated,
            input_token_count=review_input_token_count,
        )
        diagnostic["event"] = "svg_catalog_visual_review_output_truncated"
        print(json.dumps(diagnostic, ensure_ascii=False), flush=True)
        raise RuntimeError("MODAL_SVG_CATALOG_VISUAL_REVIEW_OUTPUT_TRUNCATED")

    with worker_phase("visual_review_parse_and_hard_gate_validation"):
        try:
            reviewed_plan = _parse_svg_catalog_visual_review_plan(
                review_text,
                segments,
                first_step_segment_ids=segment_manifest["first_step_segment_ids"],
                draft_plan=draft_plan,
            )
            curated_plan = _curated_openclipart_source_plan(
                candidate,
                segments,
                first_step_segment_ids=segment_manifest["first_step_segment_ids"],
            )
            if curated_plan is not None:
                reviewed_plan = curated_plan
                print(
                    json.dumps(
                        {
                            "event": "svg_catalog_curated_source_sequence_applied",
                            "source_asset_id": candidate.get("asset_id"),
                            "source_sha256": candidate.get("source_sha256"),
                            "source_segment_count": len(segments),
                            "stage_count": len(curated_plan["stages"]),
                            "sequence_version": "openclipart-friendly-kitten-icon-v3",
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
            result, reference_illustration = _build_openclipart_segment_guide(
                candidate, segments, reviewed_plan
            )
        except _SvgCatalogPlanValidationError as exc:
            exc.safe_diagnostics["review_output_token_count"] = review_output_token_count
            exc.safe_diagnostics["review_generation_duration_ms"] = round(
                review_generation_seconds * 1_000
            )
            print(
                json.dumps(
                    {
                        "event": "svg_catalog_visual_review_rejected",
                        "error_code": exc.error_code,
                        **exc.safe_diagnostics,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            raise
        reference_source = source_reference_metadata(candidate)

    print(
        json.dumps(
            {
                "event": "svg_catalog_construction_stroke_guide_generated",
                "draft_generation_seconds": generation_seconds,
                "visual_review_generation_seconds": review_generation_seconds,
                "visual_review_completed": True,
                "visual_review_panel_count": len(cumulative_review_manifest),
                "visual_review_segment_count": len(segments),
                "input_token_count": input_token_count,
                "output_token_count": output_token_count,
                "visual_review_input_token_count": review_input_token_count,
                "visual_review_output_token_count": review_output_token_count,
                "curated_source_sequence_applied": curated_plan is not None,
                "max_new_tokens": max_new_tokens,
                "ended_with_eos": ended_with_model_eos,
                "path_count": len(result["strokes"]),
                "source_segment_count": segment_manifest["source_segment_count"],
                "derived_chunk_count": len(segments),
                "stage_count": len(result["stages"]),
                "first_step_role_count": sum(
                    1 for stroke in result["strokes"]
                    if stroke["path_id"] in result["stages"][0]["stroke_ids"]
                    and stroke["role"] == "construction"
                ),
                "source_anchor_count": len({
                    source_path_id
                    for stroke in result["strokes"]
                    for source_path_id in stroke["source_path_ids"]
                }),
                "source_asset_id": reference_source["asset_id"],
                "source_sha256": reference_source["source_sha256"],
                "dataset_revision": reference_source["dataset_revision"],
                "search_term_count": len(search_terms),
                "draft_output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "review_output_sha256": hashlib.sha256(review_text.encode("utf-8")).hexdigest(),
                "draft_decoder_diagnostics": _safe_svg_topic_guide_decoder_diagnostics(
                    _json_prefix_decoder_diagnostics(
                        prefix_allowed_tokens_fn,
                        generated=generated,
                        input_token_count=input_token_count,
                    )
                ),
                "review_decoder_diagnostics": _safe_svg_topic_guide_decoder_diagnostics(
                    _json_prefix_decoder_diagnostics(
                        review_prefix_allowed_tokens_fn,
                        generated=review_generated,
                        input_token_count=review_input_token_count,
                    )
                ),
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
        "reference_source": reference_source,
        "reference_illustration": reference_illustration,
        "source_path_ids": [
            item["path_id"] for item in candidate["parsed_svg"]["paths"]
        ],
        "source_segment_manifest": {
            **segment_manifest,
            "segments": [
                {
                    "segment_id": segment["path_id"],
                    "source_path_id": segment["source_path_id"],
                    "source_subpath_indices": segment["source_subpath_indices"],
                    "source_segment_start": segment["source_segment_start"],
                    "source_segment_end": segment["source_segment_end"],
                    "geometry_sha256": hashlib.sha256(
                        segment["d"].encode("utf-8")
                    ).hexdigest(),
                }
                for segment in segments
            ],
        },
        "result": result,
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

    if is_worker_warmup(payload):
        with worker_phase("warmup_checkpoint_and_model_load"):
            _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
            _load_text_model()
        import torch

        return worker_warmup_result(
            workload="lesson.plan.suggest",
            model_id=TEXT_MODEL_ID,
            model_revision=TEXT_MODEL_REVISION,
            gpu_allocated=torch.cuda.is_available(),
        )

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


@app.function(
    name="suggest-parent-activities",
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
    workload="parent.activity.suggest",
    model_id=TEXT_MODEL_ID,
    model_revision=TEXT_MODEL_REVISION,
    gpu_class="L40S|L4|A10",
)
def suggest_parent_activities(payload: dict[str, Any]) -> dict[str, Any]:
    """Select authorized lesson activities first; draft three only when none fit."""

    if is_worker_warmup(payload):
        with worker_phase("warmup_checkpoint_and_model_load"):
            _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
            _load_text_model()
        import torch

        return worker_warmup_result(
            workload="parent.activity.suggest",
            model_id=TEXT_MODEL_ID,
            model_revision=TEXT_MODEL_REVISION,
            gpu_allocated=torch.cuda.is_available(),
        )

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "parent.activity.suggest":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    refresh_worker_volume(scratch_volume)
    with worker_phase("input_manifest_read"):
        data = _read_json_asset(request, expected_asset="input/request.json")
    with worker_phase("parent_activity_request_validation"):
        _validate_parent_activity_suggestion_input(data)
    with worker_phase("checkpoint_verification"):
        _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    with worker_phase("model_load"):
        processor, model = _load_text_model()
    messages = [
        {
            "role": "system",
            "content": (
                "Bạn chọn hoạt động Montessori ngoài trời phù hợp cho một trẻ theo context đã được "
                "người lớn xác nhận. Dùng tuổi, topic, chủ thể/đặc điểm tranh, tag sở thích và "
                "adult_confirmed_idea để đánh giá độ phù hợp. Trước hết chỉ chọn "
                "từ candidate_activities; "
                "nếu phù hợp, trả CATALOG_MATCH và 1–5 candidate_ref cùng lý do ngắn. "
                "Không sửa nội dung candidate. Nếu không có candidate phù hợp, "
                "trả NO_MATCH và đúng "
                "3 hoạt động nháp. Dùng câu chữ tự nhiên, ngắn gọn; không bắt buộc dấu câu cuối câu "
                "hay lặp lại cùng một cụm từ trong mọi hoạt động. Mỗi hoạt động cần có mục tiêu, "
                "vật liệu, chuẩn bị, hướng dẫn, ghi chú quan sát và lưu ý an toàn rõ ràng. "
                "Với từng hoạt động NO_MATCH, phải nêu rõ một địa điểm ngoài trời ngay trong "
                "preparation_text hoặc instructions_text; có thể ghi sân nhà, vườn, sân trường "
                "hoặc công viên. Không dựa vào activity_kind hay hoạt động trước để người đọc tự "
                "suy ra địa điểm. Hướng dẫn nên có khoảng "
                "2 bước vừa sức; khuyến khích trẻ tự chọn/quan sát/khám phá và để người lớn chuẩn bị, "
                "đồng hành hỗ trợ. Ba hoạt động nên khác nhau hợp lý và không lặp lại candidate hoặc "
                "hoạt động bị loại; không bắt buộc theo một bộ phương pháp cố định. "
                "Chỉ dùng vật liệu an toàn do người lớn chuẩn bị; không yêu cầu trẻ tự tìm hoặc nhặt "
                "vật lạ. Không hướng dẫn hành động nguy hiểm, dùng vật sắc/nóng/độc, hóa chất, "
                "tiếp cận đường xe hoặc nước sâu, hay chạm/bắt động vật. Nếu ý tưởng không an toàn, "
                "đổi sang quan sát, mô tả, so sánh hoặc vận động nhẹ tại địa điểm ngoài trời có người "
                "lớn đồng hành. Mỗi bước phải là việc trẻ thực sự có thể làm an toàn; không viết hành "
                "động nguy hiểm thành chỉ dẫn rồi chỉ phủ định ở lưu ý an toàn. "
                "Hoạt động phải phù hợp age_band_months. Không suy đoán tên, năng lực, "
                "chẩn đoán hoặc hoàn cảnh cá nhân. Không đưa vật sắc/nóng/độc, nguy cơ giao thông "
                "hoặc nước sâu, kéo, vật lạ trẻ nhặt được, hay yêu cầu y tế. "
                "Chỉ dùng chữ tiếng Việt/Latin; không chèn chữ Hán hay ngôn ngữ khác. Không bịa kiến thức "
                "về hành vi hoặc vòng đời con vật. "
                "Chỉ trả JSON theo schema. Draft cần người lớn xem lại."
            ),
        },
        {"role": "user", "content": _parent_activity_suggestion_prompt(data)},
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
    # The output may contain either a compact catalog choice or three bounded
    # drafts. The decoder forces EOS as soon as the selected schema is complete,
    # so this limit is a safety ceiling, not the normal length of a selection.
    max_new_tokens = 2_048
    with worker_phase("constrained_decoder_setup"):
        prefix_allowed_tokens_fn = _build_json_prefix_allowed_tokens_fn(
            processor.tokenizer,
            _parent_activity_suggestion_json_schema(
                has_candidates=bool(data["candidate_activities"])
            ),
            eos_token_id=model.generation_config.eos_token_id,
        )
    import torch

    with worker_phase("model_inference"), torch.inference_mode():
        generated = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=_generation_pad_token_id(model, processor.tokenizer),
            prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
        )
    output_token_count = int(generated.shape[-1] - input_ids.shape[-1])
    text = processor.tokenizer.decode(
        generated[0, input_ids.shape[-1] :], skip_special_tokens=True
    )
    try:
        with worker_phase("output_parse_and_contract_validation"):
            parsed = _parse_parent_activity_suggestions(
                text, expected_age_band=data["age_band_months"]
            )
    except (RuntimeError, ValueError) as exc:
        hit_limit = output_token_count >= max_new_tokens
        print(
            json.dumps(
                {
                    "event": "parent_activity_suggestions_output_truncated"
                    if hit_limit
                    else "parent_activity_suggestions_output_invalid",
                    "reason_code": str(exc),
                    "output_token_count": output_token_count,
                    "max_new_tokens": max_new_tokens,
                    "tokenizer_eos_token_id": processor.tokenizer.eos_token_id,
                    "model_eos_token_id": model.generation_config.eos_token_id,
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
                "event": "parent_activity_suggestions_tokens_generated",
                "output_token_count": output_token_count,
                "max_new_tokens": max_new_tokens,
                "token_limit_reached": output_token_count >= max_new_tokens,
                "decision": parsed["decision"],
                "selected_candidate_count": len(parsed["selected_candidates"]),
                "fallback_activity_count": len(parsed["fallback_activities"]),
                "tokenizer_eos_token_id": processor.tokenizer.eos_token_id,
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
        "result": {
            "schema_version": "sketch2life.parent-activity-suggestions.v2",
            **parsed,
        },
    }


def _validate_parent_activity_suggestion_input(data: dict[str, Any]) -> None:
    expected = {
        "schema_version",
        "age_band_ref",
        "topic",
        "adult_confirmed_idea",
        "confirmed_subject",
        "visible_features",
        "age_band_months",
        "profile_interest_tags",
        "narration_interest_tags",
        "candidate_activities",
        "excluded_activities",
    }
    if (
        not isinstance(data, dict)
        or set(data) != expected
        or data.get("schema_version") != "sketch2life.parent-activity-suggest-input.v3"
        or not isinstance(data.get("age_band_ref"), str)
        or re.fullmatch(r"age-(?:36-71|72-107|108-120)-months-v1", data["age_band_ref"]) is None
        or not isinstance(data.get("topic"), str)
        or len(data["topic"]) > 120
        or not isinstance(data.get("adult_confirmed_idea"), str)
        or len(data["adult_confirmed_idea"]) > 300
        or not isinstance(data.get("confirmed_subject"), str)
        or not 1 <= len(data["confirmed_subject"].strip()) <= 160
        or not isinstance(data.get("visible_features"), list)
        or not 1 <= len(data["visible_features"]) <= 4
        or any(
            not isinstance(value, str) or not value.strip() or len(value) > 160
            for value in data["visible_features"]
        )
        or data.get("age_band_months") not in {"36-71", "72-107", "108-120"}
        or not isinstance(data.get("profile_interest_tags"), list)
        or len(data["profile_interest_tags"]) > 12
        or any(not isinstance(tag, str) or len(tag) > 32 for tag in data["profile_interest_tags"])
        or not isinstance(data.get("narration_interest_tags"), list)
        or len(data["narration_interest_tags"]) > 12
        or any(not isinstance(tag, str) or len(tag) > 32 for tag in data["narration_interest_tags"])
        or not isinstance(data.get("candidate_activities"), list)
        or len(data["candidate_activities"]) > 12
        or not isinstance(data.get("excluded_activities"), list)
        or len(data["excluded_activities"]) > 8
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    context_labels = [
        data["topic"],
        data["adult_confirmed_idea"],
        data["confirmed_subject"],
        *data["visible_features"],
    ]
    if any(
        pattern.search(label)
        for pattern in _PARENT_ACTIVITY_PII_PATTERNS
        for label in context_labels
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    if any(
        tag not in _PARENT_ACTIVITY_ALLOWED_TAGS
        for tag in (*data["profile_interest_tags"], *data["narration_interest_tags"])
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    expected_candidate = {
        "candidate_ref", "lesson_topic", "drawing_subject", "age_band_months", "activity"
    }
    expected_activity = {
        "title", "objective", "materials_text", "preparation_text", "instructions_text",
        "observation_notes", "safety_notes", "activity_kind",
    }
    candidate_field_limits = {
        "title": 160,
        "objective": 400,
        "materials_text": 300,
        "preparation_text": 300,
        "instructions_text": 700,
        "observation_notes": 300,
        "safety_notes": 300,
    }
    for candidate in data["candidate_activities"]:
        if (
            not isinstance(candidate, dict)
            or set(candidate) != expected_candidate
            or not isinstance(candidate.get("candidate_ref"), str)
            or re.fullmatch(r"C[0-9]{3}", candidate["candidate_ref"]) is None
            or not isinstance(candidate.get("lesson_topic"), str)
            or len(candidate["lesson_topic"]) > 120
            or not isinstance(candidate.get("drawing_subject"), str)
            or len(candidate["drawing_subject"]) > 160
            or candidate.get("age_band_months") != data["age_band_months"]
            or not isinstance(candidate.get("activity"), dict)
            or set(candidate["activity"]) != expected_activity
            or candidate["activity"].get("activity_kind") != "outdoor"
            or any(
                not isinstance(candidate["activity"].get(field), str)
                or len(candidate["activity"][field]) > limit
                for field, limit in candidate_field_limits.items()
            )
        ):
            raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    if any(
        not isinstance(activity, dict)
        or set(activity) != expected_activity
        or activity.get("activity_kind") != "outdoor"
        or any(
            not isinstance(activity.get(field), str)
            or len(activity[field]) > limit
            for field, limit in candidate_field_limits.items()
        )
        for activity in data["excluded_activities"]
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    refs = [candidate["candidate_ref"] for candidate in data["candidate_activities"]]
    if len(set(refs)) != len(refs):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")


def _parent_activity_suggestion_prompt(data: dict[str, Any]) -> str:
    return (
        "Đọc context và candidate_activities dạng JSON dưới đây. Chọn candidate chỉ khi nó phù hợp "
        "với tuổi, chủ đề, chủ thể/đặc điểm tranh, tag sở thích và adult_confirmed_idea. "
        "Nếu không candidate nào phù hợp, tạo đúng ba hoạt động ngoài trời an toàn. "
        "Không được đề xuất lại hoạt động trong excluded_activities; thay đổi mục tiêu và cách làm, "
        "không chỉ đổi tên hoặc vật liệu. "
        "Tạo ba hoạt động có mục tiêu và cách thực hiện khác nhau hợp lý; không cần ép theo "
        "một bộ phương pháp cố định. Không sao chép hoạt động trong excluded_activities. "
        "Không dùng kéo, keo dán, cắt/dán, "
        "và không cho trẻ nhặt vật lạ. "
        "Khuyến khích trẻ tự chọn, quan sát hoặc khám phá; người lớn chuẩn bị và đồng hành hỗ trợ. "
        "Với từng hoạt động NO_MATCH, preparation_text hoặc instructions_text phải gọi tên rõ "
        "một địa điểm ngoài trời như sân nhà, vườn, sân trường hoặc công viên; lặp lại địa điểm "
        "cho từng hoạt động, không để người đọc tự suy ra từ activity_kind. "
        "Chỉ dùng vật liệu an toàn do người lớn chuẩn bị; không hướng dẫn trẻ làm việc nguy hiểm, "
        "dùng vật sắc/nóng/độc hoặc hóa chất, tới gần đường xe/nước sâu, chạm/bắt động vật, "
        "hay tự tìm/nhặt vật lạ. Nếu không chắc an toàn, đổi sang quan sát, mô tả, so sánh hoặc "
        "vận động nhẹ ở địa điểm ngoài trời có người lớn đi cùng. "
        "Chỉ dùng tiếng Việt; "
        "không bịa kiến thức về con vật. "
        "Viết tự nhiên, ngắn gọn bằng tiếng Việt trong các giới hạn: title 80, objective 160, "
        "materials 120, preparation 180, instructions 320, observation 120 và safety 140 ký tự. "
        "Không bắt buộc dấu câu cuối câu. Instructions nên có khoảng hai bước rõ ràng; tránh lặp ý. "
        "Ưu tiên vật liệu an toàn, có sẵn, phù hợp tuổi. "
        "Sao chép age_band_months nguyên văn. Các khóa JSON: decision, selected_candidates, "
        "no_match_reason, age_band_months, fallback_activities. Với CATALOG_MATCH, chọn 1–5 refs, "
        "không trả fallback và để no_match_reason rỗng. Với NO_MATCH, để refs rỗng và ghi lý do "
        "tối đa 120 ký tự; fallback_activities phải có đúng 3 mục.\n"
        "fallback_activities đúng 3.\n"
        f"INPUT={json.dumps(data, ensure_ascii=False, separators=(',', ':'))}"
    )


def _parent_activity_suggestion_json_schema(*, has_candidates: bool = True) -> dict[str, Any]:
    activity = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 80},
            "objective": {"type": "string", "minLength": 1, "maxLength": 160},
            "materials_text": {"type": "string", "maxLength": 120},
            "preparation_text": {"type": "string", "minLength": 1, "maxLength": 180},
            "instructions_text": {"type": "string", "minLength": 16, "maxLength": 320},
            "observation_notes": {"type": "string", "maxLength": 120},
            "safety_notes": {"type": "string", "minLength": 8, "maxLength": 140},
            "activity_kind": {"type": "string", "enum": ["outdoor"]},
        },
        "required": [
            "title",
            "objective",
            "materials_text",
            "preparation_text",
            "instructions_text",
            "observation_notes",
            "safety_notes",
            "activity_kind",
        ],
    }
    selection = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "candidate_ref": {"type": "string", "pattern": "^C[0-9]{3}$"},
            "match_reason": {"type": "string", "minLength": 1, "maxLength": 180},
        },
        "required": ["candidate_ref", "match_reason"],
    }
    decision = {
        "type": "string",
        "enum": ["CATALOG_MATCH", "NO_MATCH"] if has_candidates else ["NO_MATCH"],
    }
    fallback_minimum = 0 if has_candidates else 3
    fallback_maximum = 3
    reason_schema = {"type": "string", "maxLength": 120}
    if not has_candidates:
        reason_schema["minLength"] = 1
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "decision": decision,
            "selected_candidates": {
                "type": "array",
                "minItems": 0,
                "maxItems": 0 if not has_candidates else 5,
                "items": selection,
            },
            "no_match_reason": reason_schema,
            "age_band_months": {"type": "string", "enum": ["36-71", "72-107", "108-120"]},
            "fallback_activities": {
                "type": "array",
                "minItems": fallback_minimum,
                "maxItems": fallback_maximum,
                "items": activity,
            },
        },
        "required": [
            "decision", "selected_candidates", "no_match_reason", "age_band_months",
            "fallback_activities",
        ],
    }


def _parse_parent_activity_suggestions(
    text: str, *, expected_age_band: str
) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_JSON") from exc
    expected = {
        "decision", "selected_candidates", "no_match_reason", "age_band_months",
        "fallback_activities",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_ROOT_SHAPE")
    if value["age_band_months"] != expected_age_band:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_AGE_BAND")
    selections = value["selected_candidates"]
    no_match_reason = value["no_match_reason"]
    if (
        not isinstance(selections, list)
        or len(selections) > 5
        or not isinstance(no_match_reason, str)
        or len(no_match_reason) > 120
        or value["decision"] not in {"CATALOG_MATCH", "NO_MATCH"}
    ):
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_SELECTION_ENVELOPE")
    normalized_selections: list[dict[str, str]] = []
    for selection in selections:
        if (
            not isinstance(selection, dict)
            or set(selection) != {"candidate_ref", "match_reason"}
            or not isinstance(selection.get("candidate_ref"), str)
            or re.fullmatch(r"C[0-9]{3}", selection["candidate_ref"]) is None
            or not isinstance(selection.get("match_reason"), str)
            or not 1 <= len(selection["match_reason"].strip()) <= 180
        ):
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_SELECTION_ITEM")
        normalized_selections.append(
            {
                "candidate_ref": selection["candidate_ref"],
                "match_reason": selection["match_reason"].strip(),
            }
        )
    if len({item["candidate_ref"] for item in normalized_selections}) != len(normalized_selections):
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_DUPLICATE_SELECTION")
    fallback_activities = value["fallback_activities"]
    fields = {
        "title": 80,
        "objective": 160,
        "materials_text": 120,
        "preparation_text": 180,
        "instructions_text": 320,
        "observation_notes": 120,
        "safety_notes": 140,
    }
    if not isinstance(fallback_activities, list) or len(fallback_activities) > 3:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_FALLBACK_COUNT")
    normalized_activities: list[dict[str, str]] = []
    for item in fallback_activities:
        if not isinstance(item, dict) or set(item) != {*fields, "activity_kind"}:
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_ACTIVITY_SHAPE")
        if any(
            not isinstance(item.get(key), str)
            or len(item[key]) > limit
            or (
                key in {"title", "objective", "preparation_text", "instructions_text", "safety_notes"}
                and not item[key].strip()
            )
            for key, limit in fields.items()
        ) or (
            isinstance(item.get("instructions_text"), str)
            and len(item["instructions_text"].strip()) < 16
        ) or (
            isinstance(item.get("safety_notes"), str)
            and len(item["safety_notes"].strip()) < 8
        ) or item.get("activity_kind") != "outdoor":
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_ACTIVITY_FIELD")
        if any(
            character.isalpha() and "LATIN" not in unicodedata.name(character, "")
            for field_value in item.values()
            if isinstance(field_value, str)
            for character in field_value
        ):
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_NON_LATIN_SCRIPT")
        normalized_activities.append(
            {key: item[key].strip() for key in fields} | {"activity_kind": "outdoor"}
        )
    decision = value["decision"]
    if decision == "CATALOG_MATCH":
        if (
            not 1 <= len(normalized_selections) <= 5
            or normalized_activities
            or no_match_reason.strip()
        ):
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_CATALOG_SHAPE")
    elif normalized_selections or len(normalized_activities) != 3 or not no_match_reason.strip():
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID_FALLBACK_SHAPE")
    return {
        "decision": decision,
        "selected_candidates": normalized_selections,
        "no_match_reason": no_match_reason.strip(),
        "age_band_months": expected_age_band,
        "fallback_activities": normalized_activities,
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
        "Use 4-8 short drawing-construction steps, 2-4 factual learning notes, and 3-5 practical activity "
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
        or not 4 <= len(data["drawing_steps"]) <= 8
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
    if isinstance(step_count, bool) or not 4 <= step_count <= 8:
        raise ValueError("step_count must be between four and eight")
    return 512 + step_count * 320


def _validate_teacher_svg_illustration_input(data: Any) -> None:
    if (
        not isinstance(data, dict)
        or set(data)
        != {"schema_version", "topic", "target_age_months", "visual_style"}
        or data.get("schema_version") != "sketch2life.teacher-svg-illustration-input.v1"
        or not isinstance(data.get("topic"), str)
        or not 2 <= len(data["topic"].strip()) <= 120
        or isinstance(data.get("target_age_months"), bool)
        or not isinstance(data.get("target_age_months"), int)
        or not 36 <= data["target_age_months"] <= 120
        or data.get("visual_style")
        not in {"warm_storybook", "simple_classroom", "clean_outline"}
    ):
        raise WorkerContractError("TEACHER_SVG_ILLUSTRATION_INPUT_INVALID")


def _load_teacher_svg_illustration_reference_pack() -> dict[str, Any]:
    global TEACHER_SVG_REFERENCE_PACK_CACHE
    if TEACHER_SVG_REFERENCE_PACK_CACHE is not None:
        return TEACHER_SVG_REFERENCE_PACK_CACHE

    source_path = (
        TEACHER_SVG_REFERENCE_PACK_WORKER_PATH
        if TEACHER_SVG_REFERENCE_PACK_WORKER_PATH.is_file()
        else TEACHER_SVG_REFERENCE_PACK_LOCAL_PATH
    )
    try:
        raw = source_path.read_bytes()
        if (
            not raw
            or len(raw) > 64 * 1024
            or hashlib.sha256(raw).hexdigest()
            != TEACHER_SVG_REFERENCE_PACK_SHA256
        ):
            raise ValueError("reference pack size or digest mismatch")
        pack = json.loads(raw, object_pairs_hook=_reject_duplicate_story_keys)
    except Exception as exc:
        raise WorkerContractError("MODAL_SVG_REFERENCE_PACK_INVALID") from exc

    if (
        not isinstance(pack, dict)
        or set(pack)
        != {
            "schema_version",
            "dataset_id",
            "dataset_revision",
            "license",
            "max_selected_per_request",
            "examples",
        }
        or pack.get("schema_version") != "TeacherSvgIllustrationReferencePackV1"
        or pack.get("dataset_id") != "yoavf/svg-animal-illustrations"
        or pack.get("dataset_revision") != "d7ab3149308746a4b17e7cbee30f1f054f6c49df"
        or pack.get("license")
        != "CC0-1.0 (as declared by the dataset card; not independently legal-audited)"
        or pack.get("max_selected_per_request") != 1
        or not isinstance(pack.get("examples"), list)
        or not 1 <= len(pack["examples"]) <= 12
    ):
        raise WorkerContractError("MODAL_SVG_REFERENCE_PACK_INVALID")

    allowed_example_fields = {
        "reference_id",
        "source_subject_label",
        "retrieval_key",
        "source_file",
        "source_url",
        "license",
        "source_revision",
        "source_prompt",
        "source_sha256",
        "canonical_sha256",
        "normalizations",
        "composition_hint_vi",
        "document",
    }
    checked_examples: list[dict[str, Any]] = []
    for example in pack["examples"]:
        if not isinstance(example, dict) or set(example) != allowed_example_fields:
            raise WorkerContractError("MODAL_SVG_REFERENCE_EXAMPLE_INVALID")
        if (
            example.get("retrieval_key")
            not in {"quadruped", "feline", "lagomorph"}
            or example.get("license") != "CC0-1.0 (dataset card declaration)"
            or example.get("source_revision") != pack["dataset_revision"]
            or not isinstance(example.get("source_url"), str)
            or not example["source_url"].startswith("https://huggingface.co/")
            or not isinstance(example.get("normalizations"), list)
            or not example["normalizations"]
        ):
            raise WorkerContractError("MODAL_SVG_REFERENCE_EXAMPLE_INVALID")
        document = example.get("document")
        if not isinstance(document, dict):
            raise WorkerContractError("MODAL_SVG_REFERENCE_EXAMPLE_INVALID")
        candidate = {
            "schema_version": "SvgIllustrationContentV1",
            "title_vi": example["source_subject_label"],
            "alt_text_vi": "CC0 dataset structure reference",
            "document": document,
        }
        try:
            checked = _parse_teacher_svg_illustration(
                json.dumps(candidate, ensure_ascii=False),
                max_paths=64,
                expected_view_box=document.get("view_box"),
            )
        except (RuntimeError, TypeError, ValueError) as exc:
            raise WorkerContractError("MODAL_SVG_REFERENCE_EXAMPLE_INVALID") from exc
        if not isinstance(example.get("canonical_sha256"), str) or re.fullmatch(
            r"[0-9a-f]{64}", example["canonical_sha256"]
        ) is None:
            raise WorkerContractError("MODAL_SVG_REFERENCE_EXAMPLE_INVALID")
        checked_example = dict(example)
        checked_example["document"] = checked["document"]
        checked_examples.append(checked_example)

    pack["examples"] = checked_examples
    TEACHER_SVG_REFERENCE_PACK_CACHE = pack
    return pack


def _teacher_svg_illustration_reference_key(topic: str) -> str | None:
    normalized = unicodedata.normalize("NFKC", topic).casefold()
    if any(term in normalized for term in ("mèo", "cat", "feline")):
        return "feline"
    if any(term in normalized for term in ("thỏ", "rabbit", "hare")):
        return "lagomorph"
    if any(
        term in normalized
        for term in (
            "hươu",
            "nai",
            "deer",
            "fawn",
            "stag",
            "elk",
            "ngựa",
            "horse",
            "bò",
            "cow",
            "dê",
            "goat",
            "cừu",
            "sheep",
            "chó",
            "dog",
            "lợn",
            "pig",
        )
    ):
        return "quadruped"
    return None


def _select_teacher_svg_illustration_reference(topic: str) -> dict[str, Any] | None:
    retrieval_key = _teacher_svg_illustration_reference_key(topic)
    if retrieval_key is None:
        return None
    pack = _load_teacher_svg_illustration_reference_pack()
    return next(
        (
            example
            for example in pack["examples"]
            if example["retrieval_key"] == retrieval_key
        ),
        None,
    )


def _teacher_svg_illustration_prompt(
    data: dict[str, Any], reference: dict[str, Any] | None = None
) -> str:
    style_names = {
        "warm_storybook": "màu ấm, hình khối mềm, minh họa sách tranh",
        "simple_classroom": "màu rõ, hình khối đơn giản, dễ quan sát trên màn chiếu",
        "clean_outline": "ít màu, đường viền rõ, bố cục thoáng",
    }
    topic = data["topic"].strip()
    normalized_topic = unicodedata.normalize("NFKC", topic).casefold()
    morphology = ""
    if any(
        term in normalized_topic
        for term in ("hươu", "nai", "deer", "fawn", "stag", "elk")
    ):
        morphology = (
            "\nYêu cầu giải phẫu hươu: dáng nghiêng 3/4; thân dài nằm ngang; cổ nối rõ từ vai "
            "lên đầu nhỏ hơn thân; mõm hướng nhẹ về trước; hai tai ở hai bên đầu; cặp sừng "
            "phân nhánh mọc từ đỉnh đầu; bốn chân thon gắn vào thân và chạm cùng mặt đất; "
            "ngực/bụng sáng; đốm nhỏ nằm bên trong vùng lưng. Giữ từng chi tiết bám vào đúng "
            "bộ phận. Không thêm cỏ, cây, bóng đổ hoặc cảnh nền."
        )

    reference_section = ""
    if reference is not None:
        reference_document = json.dumps(
            {
                "source_subject": reference["source_subject_label"],
                "layout_hint": reference["composition_hint_vi"],
                "document": reference["document"],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        reference_section = (
            "\nMẫu cấu trúc tham khảo từ dataset CC0 (chỉ một mẫu): "
            f"{reference_document}\n"
            "Chỉ tham khảo cách phân lớp bộ phận. Không sao chép loài, dáng, tọa độ, màu, "
            "số path hay chi tiết trang trí; hãy tạo hình mới đúng chủ đề được yêu cầu."
        )

    return (
        "Tạo một hình minh họa vector 1:1 cho chủ đề dưới đây. Chỉ có một chủ thể chính, "
        "đặt giữa viewBox 0 0 512 512, chiếm phần lớn khung nhưng chừa lề. Dùng 4 đến 20 "
        "path độc lập. Ưu tiên đường bao lớn, mềm và có cấu trúc; tránh ghép nhiều hình tròn "
        "rời thành cơ thể. Tỷ lệ bộ phận tự nhiên, các khớp nối hợp lý; chân/chi tiết phải "
        "chạm hoặc nằm đúng trên bộ phận chủ thể tương ứng. Không có vật trang trí rời. "
        "Mỗi path là đường SVG khép kín hoặc nét đơn giản; không dùng transform, clipPath, "
        "mask, gradient, text, filter, CSS, URL hay tham chiếu ngoài. Dùng fill là `none` hoặc "
        "màu #RRGGBB, stroke là #RRGGBB, stroke_width từ 1 đến 12. Path data chỉ dùng "
        "M/L/H/V/C/S/Q/T/A/Z. Các path không được trùng hình học. Đặt path_id ngắn theo "
        "bộ phận dễ hiểu. Không vẽ chữ. Trả title_vi và alt_text_vi ngắn, đúng chủ đề.\n"
        f"Chủ đề: {json.dumps(topic, ensure_ascii=False)}. "
        f"Độ tuổi: {data['target_age_months']} tháng. "
        f"Phong cách: {style_names[data['visual_style']]}."
        f"{morphology}{reference_section}"
    )

def _teacher_svg_illustration_json_schema() -> dict[str, Any]:
    path_properties = {
        "path_id": {"type": "string", "minLength": 1, "maxLength": 96},
        "d": {"type": "string", "minLength": 1, "maxLength": 4096},
        "fill": {"type": "string", "minLength": 1, "maxLength": 7},
        "stroke": {"type": "string", "minLength": 7, "maxLength": 7},
        "stroke_width": {"type": "number", "minimum": 1, "maximum": 12},
    }
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "string", "enum": ["SvgIllustrationContentV1"]},
            "title_vi": {"type": "string", "minLength": 1, "maxLength": 120},
            "alt_text_vi": {"type": "string", "minLength": 1, "maxLength": 300},
            "document": {
                "type": "object",
                "properties": {
                    "schema_version": {"type": "string", "enum": ["SvgDocumentV1"]},
                    "view_box": {"type": "string", "enum": ["0 0 512 512"]},
                    "paths": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 20,
                        "items": {
                            "type": "object",
                            "properties": path_properties,
                            "required": list(path_properties),
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["schema_version", "view_box", "paths"],
                "additionalProperties": False,
            },
        },
        "required": ["schema_version", "title_vi", "alt_text_vi", "document"],
        "additionalProperties": False,
    }


def _teacher_svg_illustration_max_output_tokens() -> int:
    return 3_072


def _parse_teacher_svg_illustration(
    text: str,
    *,
    max_paths: int = 20,
    expected_view_box: str = "0 0 512 512",
) -> dict[str, Any]:
    try:
        candidate = json.loads(text, object_pairs_hook=_reject_duplicate_story_keys)
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("MODAL_SVG_ILLUSTRATION_JSON_INVALID") from exc
    if (
        not isinstance(candidate, dict)
        or set(candidate) != {"schema_version", "title_vi", "alt_text_vi", "document"}
        or candidate.get("schema_version") != "SvgIllustrationContentV1"
        or not isinstance(candidate.get("title_vi"), str)
        or not 1 <= len(candidate["title_vi"].strip()) <= 120
        or not isinstance(candidate.get("alt_text_vi"), str)
        or not 1 <= len(candidate["alt_text_vi"].strip()) <= 300
    ):
        raise RuntimeError("MODAL_SVG_ILLUSTRATION_JSON_INVALID")
    document = candidate.get("document")
    if (
        not isinstance(document, dict)
        or set(document) != {"schema_version", "view_box", "paths"}
        or document.get("schema_version") != "SvgDocumentV1"
        or document.get("view_box") != expected_view_box
        or not isinstance(document.get("paths"), list)
        or not 4 <= len(document["paths"]) <= max_paths
    ):
        raise RuntimeError("MODAL_SVG_ILLUSTRATION_JSON_INVALID")
    path_ids: set[str] = set()
    geometries: set[str] = set()
    checked_paths: list[dict[str, Any]] = []
    for path in document["paths"]:
        if not isinstance(path, dict) or set(path) != {
            "path_id", "d", "fill", "stroke", "stroke_width"
        }:
            raise RuntimeError("MODAL_SVG_ILLUSTRATION_PATH_INVALID")
        path_id, path_data, fill, stroke = (
            path.get("path_id"), path.get("d"), path.get("fill"), path.get("stroke")
        )
        stroke_width = path.get("stroke_width")
        if (
            not isinstance(path_id, str)
            or re.fullmatch(r"[A-Za-z0-9._:-]{1,96}", path_id) is None
            or path_id in path_ids
            or not isinstance(path_data, str)
            or not 1 <= len(path_data.strip()) <= 4096
            or not isinstance(fill, str)
            or re.fullmatch(r"(?:none|#[0-9a-fA-F]{6})", fill) is None
            or not isinstance(stroke, str)
            or re.fullmatch(r"#[0-9a-fA-F]{6}", stroke) is None
            or isinstance(stroke_width, bool)
            or not isinstance(stroke_width, (float, int))
            or not 1 <= stroke_width <= 12
            or (fill == "none" and not stroke)
        ):
            raise RuntimeError("MODAL_SVG_ILLUSTRATION_PATH_INVALID")
        geometry = hashlib.sha256(path_data.strip().encode("utf-8")).hexdigest()
        if geometry in geometries:
            raise RuntimeError("MODAL_SVG_ILLUSTRATION_DUPLICATE_PATH")
        path_ids.add(path_id)
        geometries.add(geometry)
        checked_paths.append(
            {
                "path_id": path_id,
                "d": path_data.strip(),
                "fill": fill,
                "stroke": stroke,
                "stroke_width": float(stroke_width),
            }
        )
    return {
        "schema_version": "SvgIllustrationContentV1",
        "title_vi": candidate["title_vi"].strip(),
        "alt_text_vi": candidate["alt_text_vi"].strip(),
        "document": {
            "schema_version": "SvgDocumentV1",
            "view_box": expected_view_box,
            "paths": checked_paths,
        },
    }


def _normalize_svg_reference_topic(topic: str) -> str:
    folded = unicodedata.normalize("NFKD", topic.casefold())
    normalized = "".join(char for char in folded if not unicodedata.combining(char))
    return " ".join(normalized.split())


def _load_arcadia_gallus_reference(
    topic: str,
) -> tuple[Any | None, dict[str, str] | None]:
    """Render the pinned CC0 chicken SVG only for topics that it represents."""
    with Path(ARCADIA_GALLUS_REFERENCE_PACK_WORKER_PATH).open(
        "r", encoding="utf-8"
    ) as manifest_file:
        manifest = json.load(manifest_file)
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != "ArcadiaSvgStrokeReferenceV1"
        or not isinstance(manifest.get("dataset"), dict)
        or not isinstance(manifest.get("asset"), dict)
    ):
        raise WorkerContractError("SVG_REFERENCE_MANIFEST_INVALID")

    dataset = manifest["dataset"]
    asset = manifest["asset"]
    allowed_topics = asset.get("permitted_normalized_topics")
    if not isinstance(allowed_topics, list) or any(
        not isinstance(value, str) for value in allowed_topics
    ):
        raise WorkerContractError("SVG_REFERENCE_TOPIC_MAP_INVALID")
    if _normalize_svg_reference_topic(topic) not in set(allowed_topics):
        return None, None

    if (
        dataset.get("doi") != "10.5281/zenodo.17203578"
        or dataset.get("revision") != "1.0"
        or dataset.get("license_id") != "CC0-1.0"
        or asset.get("asset_id") != "arcadia-gallus-gallus-tricolorstroke-v1"
        or asset.get("filename") != "gallus-gallus-source.svg"
        or asset.get("reference_only") is not True
        or asset.get("contains_stroke_order") is not False
        or not isinstance(asset.get("sha256"), str)
        or _SHA256.fullmatch(asset["sha256"]) is None
    ):
        raise WorkerContractError("SVG_REFERENCE_MANIFEST_INVALID")

    source_bytes = Path(ARCADIA_GALLUS_REFERENCE_SVG_WORKER_PATH).read_bytes()
    if (
        not source_bytes
        or len(source_bytes) > 128 * 1024
        or hashlib.sha256(source_bytes).hexdigest() != asset["sha256"]
    ):
        raise WorkerContractError("SVG_REFERENCE_SOURCE_HASH_MISMATCH")

    import cairosvg
    from io import BytesIO
    from PIL import Image

    rendered_png = cairosvg.svg2png(
        bytestring=source_bytes,
        output_width=768,
        output_height=768,
        background_color="#ffffff",
    )
    with Image.open(BytesIO(rendered_png)) as opened:
        if opened.format != "PNG" or opened.size != (768, 768):
            raise WorkerContractError("SVG_REFERENCE_RENDER_INVALID")
        reference_image = opened.convert("RGB")

    reference_source = {
        "asset_id": asset["asset_id"],
        "dataset_name": dataset["name"],
        "dataset_revision": dataset["revision"],
        "dataset_doi": dataset["doi"],
        "source_sha256": asset["sha256"],
        "license_id": dataset["license_id"],
        "license_uri": dataset["license_uri"],
    }
    return reference_image, reference_source


def _generate_svg_catalog_search_terms(
    data: dict[str, Any], processor: Any, model: Any
) -> list[str]:
    messages = [
        {
            "role": "system",
            "content": (
                "Translate the adult-selected Vietnamese drawing topic into 3 to 8 concise English "
                "Openclipart search terms. Return only the requested JSON object. Do not add "
                "people, names, locations, or unrelated concepts."
            ),
        },
        {
            "role": "user",
            "content": f"Topic: {json.dumps(data['topic'], ensure_ascii=False)}. Difficulty: {data['difficulty']}.",
        },
    ]
    response = _generate_svg_catalog_json(
        messages,
        processor,
        model,
        _svg_catalog_search_schema(),
        max_new_tokens=SVG_CATALOG_SEARCH_MAX_OUTPUT_TOKENS,
        error_code="MODAL_SVG_CATALOG_QUERY_INVALID",
    )
    terms = response.get("search_terms") if isinstance(response, dict) else None
    if (
        not isinstance(terms, list)
        or not 3 <= len(terms) <= 8
        or any(not isinstance(term, str) or not term.strip() or len(term) > 48 for term in terms)
    ):
        raise RuntimeError("MODAL_SVG_CATALOG_QUERY_INVALID")
    return terms


def _generate_svg_catalog_json(
    messages: list[dict[str, Any]],
    processor: Any,
    model: Any,
    schema: dict[str, Any],
    *,
    max_new_tokens: int,
    error_code: str,
) -> dict[str, Any]:
    import torch

    encoded = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
        return_tensors="pt",
        return_dict=True,
    ).to(model.device)
    prefix_allowed_tokens_fn = _build_json_prefix_allowed_tokens_fn(
        processor.tokenizer,
        schema,
        eos_token_id=model.generation_config.eos_token_id,
    )
    with torch.inference_mode():
        generated = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=_generation_pad_token_id(model, processor.tokenizer),
            prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
        )
    input_token_count = int(encoded["input_ids"].shape[-1])
    output_token_count = int(generated.shape[-1] - input_token_count)
    final_token_id = int(generated[0, -1].item()) if output_token_count else None
    eos_token_ids = model.generation_config.eos_token_id
    if isinstance(eos_token_ids, int):
        eos_token_ids = [eos_token_ids]
    if not _svg_topic_guide_generation_is_complete(
        output_token_count=output_token_count,
        max_new_tokens=max_new_tokens,
        final_token_id=final_token_id,
        eos_token_ids=eos_token_ids,
    ):
        raise RuntimeError(error_code)
    text = processor.tokenizer.decode(
        generated[0, input_token_count:], skip_special_tokens=True
    ).strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(error_code) from exc
    if not isinstance(value, dict):
        raise RuntimeError(error_code)
    return value


def _svg_catalog_search_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "search_terms": {
                "type": "array",
                "minItems": 3,
                "maxItems": 8,
                "items": {"type": "string", "minLength": 2, "maxLength": 48},
            }
        },
        "required": ["search_terms"],
        "additionalProperties": False,
    }


def _render_openclipart_candidate(
    candidate: dict[str, Any],
    *,
    atlas_paths: list[dict[str, Any]] | None = None,
    atlas_view_box: str | None = None,
) -> tuple[Any, Any]:
    import xml.etree.ElementTree as ET
    from io import BytesIO

    import cairosvg
    from PIL import Image, ImageDraw, ImageFont

    parsed = candidate["parsed_svg"]
    view_box = parsed["view_box"]
    atlas_paths = atlas_paths if atlas_paths is not None else parsed["paths"]
    atlas_view_box = atlas_view_box or view_box
    full_root = ET.Element(f"{{http://www.w3.org/2000/svg}}svg", {"viewBox": view_box})
    for path in parsed["paths"]:
        ET.SubElement(
            full_root,
            f"{{http://www.w3.org/2000/svg}}path",
            {
                "id": path["path_id"],
                "d": path["d"],
                "fill": _catalog_color(path["fill"]),
                "stroke": _catalog_color(path["stroke"]),
                "stroke-width": str(path["stroke_width"]),
                "stroke-linecap": path["stroke_linecap"],
                "stroke-linejoin": path["stroke_linejoin"],
            },
        )
    source_png = cairosvg.svg2png(
        bytestring=ET.tostring(full_root, encoding="utf-8"),
        output_width=768,
        output_height=768,
        background_color="#ffffff",
    )
    with Image.open(BytesIO(source_png)) as opened:
        source_image = opened.convert("RGB")

    columns = 4
    tile_width = 208
    tile_height = 224
    rows = (len(atlas_paths) + columns - 1) // columns
    atlas = Image.new("RGB", (columns * tile_width, rows * tile_height), "#f3f6fa")
    draw = ImageDraw.Draw(atlas)
    font = ImageFont.load_default()
    for index, path in enumerate(atlas_paths, start=1):
        contextual = ET.Element(
            f"{{http://www.w3.org/2000/svg}}svg",
            {"viewBox": atlas_view_box, "width": "512", "height": "512"},
        )
        for context_path in atlas_paths:
            ET.SubElement(
                contextual,
                f"{{http://www.w3.org/2000/svg}}path",
                {
                    "d": context_path["d"],
                    "fill": "none",
                    "stroke": "#d3dbe7",
                    "stroke-width": "5",
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round",
                },
            )
        ET.SubElement(
            contextual,
            f"{{http://www.w3.org/2000/svg}}path",
            {
                "d": path["d"],
                "fill": "none",
                "stroke": "#075dff",
                "stroke-width": "11",
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
            },
        )
        path_png = cairosvg.svg2png(
            bytestring=ET.tostring(contextual, encoding="utf-8"),
            output_width=256,
            output_height=256,
            background_color="#ffffff",
        )
        with Image.open(BytesIO(path_png)) as opened:
            path_image = opened.convert("RGB")
        path_image.thumbnail((tile_width - 16, tile_height - 40), Image.Resampling.LANCZOS)
        column = (index - 1) % columns
        row = (index - 1) // columns
        left = column * tile_width
        top = row * tile_height
        draw.rounded_rectangle(
            (left + 3, top + 3, left + tile_width - 4, top + tile_height - 4),
            radius=8,
            fill="white",
            outline="#d5dce7",
        )
        draw.text((left + 10, top + 8), f"P{index:02d}", fill="#2855c5", font=font)
        atlas.paste(
            path_image,
            (
                left + (tile_width - path_image.width) // 2,
                top + 34 + (tile_height - 40 - path_image.height) // 2,
            ),
        )
    return source_image, atlas


def _render_openclipart_cumulative_stage_review(
    candidate: dict[str, Any],
    segments: list[dict[str, Any]],
    plan: dict[str, Any],
) -> tuple[Any, list[dict[str, Any]]]:
    """Rasterize cumulative source-exact stages for the constrained visual reviewer."""

    import cairosvg
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont
    import xml.etree.ElementTree as ET

    stages = plan["stages"]
    segment_by_id = {segment["path_id"]: segment for segment in segments}
    columns = 4
    tile_width = 280
    tile_height = 330
    preview_size = 248
    rows = (len(stages) + columns - 1) // columns
    sheet = Image.new(
        "RGB", (columns * tile_width, rows * tile_height), "#e9edf4"
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    cumulative_ids: list[str] = []
    stage_manifest: list[dict[str, Any]] = []
    atlas_label_by_id = {
        segment["path_id"]: f"P{index:02d}"
        for index, segment in enumerate(segments, start=1)
    }

    for stage in stages:
        new_ids = list(stage["path_ids"])
        if not new_ids or any(path_id not in segment_by_id for path_id in new_ids):
            raise _SvgCatalogPlanValidationError(
                "SVG_CATALOG_VISUAL_REVIEW_STAGE_SEGMENTS_INVALID",
                {"step_index": stage.get("step_index", 0)},
            )
        cumulative_ids.extend(new_ids)
        new_id_set = set(new_ids)
        svg_root = ET.Element(
            "{http://www.w3.org/2000/svg}svg",
            {"viewBox": "0 0 512 512", "width": "512", "height": "512"},
        )
        for segment in segments:
            segment_id = segment["path_id"]
            if segment_id not in cumulative_ids:
                continue
            ET.SubElement(
                svg_root,
                "{http://www.w3.org/2000/svg}path",
                {
                    "d": segment["d"],
                    "fill": "none",
                    "stroke": "#1769ff" if segment_id in new_id_set else "#aeb8c8",
                    "stroke-width": "8",
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round",
                },
            )
        rendered = cairosvg.svg2png(
            bytestring=ET.tostring(svg_root, encoding="utf-8"),
            output_width=preview_size,
            output_height=preview_size,
            background_color="#ffffff",
        )
        with Image.open(BytesIO(rendered)) as opened:
            preview = opened.convert("RGB")

        index = stage["step_index"]
        column = (index - 1) % columns
        row = (index - 1) // columns
        left = column * tile_width
        top = row * tile_height
        draw.rounded_rectangle(
            (left + 3, top + 3, left + tile_width - 4, top + tile_height - 4),
            radius=8,
            fill="#ffffff",
            outline="#cbd3df",
            width=2,
        )
        draw.text((left + 12, top + 10), f"STEP {index:02d}", fill="#2449a7", font=font)
        new_labels = [atlas_label_by_id[path_id] for path_id in new_ids]
        label_lines: list[str] = []
        active_line = "Mới:"
        for label in new_labels:
            addition = f" {label}"
            if len(active_line) + len(addition) > 32 and active_line != "Mới:":
                label_lines.append(active_line)
                active_line = label
            else:
                active_line += addition
        if active_line:
            label_lines.append(active_line)
        for line_number, label_line in enumerate(label_lines[:2]):
            draw.text(
                (left + 12, top + 27 + line_number * 12),
                label_line,
                fill="#075dff",
                font=font,
            )
        sheet.paste(
            preview,
            (left + (tile_width - preview_size) // 2, top + 68),
        )
        stage_manifest.append(
            {
                "step_index": index,
                "new_segment_ids": new_ids,
                "new_segment_labels": new_labels,
                "cumulative_segment_ids": list(cumulative_ids),
            }
        )

    return sheet, stage_manifest


_SVG_SOURCE_SEGMENT_PATTERN = re.compile(
    r"[A-Za-z]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
)
_SVG_SOURCE_SEGMENT_COMMAND_ARITY = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6}


class _SvgSourceSegmentationError(ValueError):
    """A safe, non-content-bearing reason that an SVG cannot be segmented."""


def _source_svg_number(value: float) -> str:
    if not math.isfinite(value):
        raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_NUMBER_INVALID")
    if abs(value) < 0.0000005:
        value = 0.0
    return format(value, ".6g")


def _parse_source_svg_path_segments(path_data: str) -> list[dict[str, Any]]:
    """Parse the safe M/L/H/V/C/Z subset into exact drawable command segments."""
    tokens = [match.group(0) for match in _SVG_SOURCE_SEGMENT_PATTERN.finditer(path_data)]
    residue = _SVG_SOURCE_SEGMENT_PATTERN.sub("", path_data)
    if not tokens or residue.replace(",", "").strip():
        raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_TOKEN_INVALID")

    segments: list[dict[str, Any]] = []
    current = (0.0, 0.0)
    subpath_start: tuple[float, float] | None = None
    subpath_index = 0
    command: str | None = None
    index = 0

    def number_at(offset: int) -> float:
        value = float(tokens[offset])
        if not math.isfinite(value) or abs(value) > 1_000_000:
            raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_NUMBER_INVALID")
        return value

    def absolute_pair(x: float, y: float, relative: bool) -> tuple[float, float]:
        return (current[0] + x, current[1] + y) if relative else (x, y)

    def append_line(end: tuple[float, float]) -> None:
        nonlocal current
        if math.hypot(end[0] - current[0], end[1] - current[1]) > 0.000001:
            segments.append({
                "subpath_index": subpath_index,
                "kind": "line",
                "start": current,
                "end": end,
            })
        current = end

    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token
            index += 1
            upper = command.upper()
            if upper not in {*_SVG_SOURCE_SEGMENT_COMMAND_ARITY, "Z"}:
                raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_COMMAND_UNSUPPORTED")
            if upper == "Z":
                if subpath_start is None:
                    raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_CLOSE_WITHOUT_MOVE")
                append_line(subpath_start)
                command = None
                continue
        elif command is None:
            raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_COMMAND_MISSING")

        if command is None:
            continue
        upper = command.upper()
        relative = command.islower()
        arity = _SVG_SOURCE_SEGMENT_COMMAND_ARITY[upper]
        if index + arity > len(tokens) or any(
            tokens[index + offset].isalpha() for offset in range(arity)
        ):
            raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_ARGUMENTS_INVALID")

        if upper == "M":
            point = absolute_pair(number_at(index), number_at(index + 1), relative)
            index += 2
            current = point
            subpath_start = point
            subpath_index += 1
            command = "l" if relative else "L"
        elif upper == "L":
            if subpath_index == 0:
                raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_MOVE_REQUIRED")
            point = absolute_pair(number_at(index), number_at(index + 1), relative)
            index += 2
            append_line(point)
        elif upper == "H":
            if subpath_index == 0:
                raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_MOVE_REQUIRED")
            x = number_at(index)
            index += 1
            append_line((current[0] + x if relative else x, current[1]))
        elif upper == "V":
            if subpath_index == 0:
                raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_MOVE_REQUIRED")
            y = number_at(index)
            index += 1
            append_line((current[0], current[1] + y if relative else y))
        else:
            if subpath_index == 0:
                raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_MOVE_REQUIRED")
            values = [number_at(index + offset) for offset in range(6)]
            index += 6
            base_x, base_y = current if relative else (0.0, 0.0)
            control_1 = (base_x + values[0], base_y + values[1])
            control_2 = (base_x + values[2], base_y + values[3])
            end = (base_x + values[4], base_y + values[5])
            segments.append({
                "subpath_index": subpath_index,
                "kind": "cubic",
                "start": current,
                "control_1": control_1,
                "control_2": control_2,
                "end": end,
            })
            current = end
    if not segments:
        raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_EMPTY")
    return segments


def _source_viewbox_transform(view_box: str) -> dict[str, float]:
    values = [float(value) for value in view_box.split()]
    if len(values) != 4 or any(not math.isfinite(value) for value in values):
        raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_VIEWBOX_INVALID")
    min_x, min_y, width, height = values
    if width <= 0 or height <= 0:
        raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_VIEWBOX_INVALID")
    margin = 24.0
    scale = min((512.0 - margin * 2.0) / width, (512.0 - margin * 2.0) / height)
    return {
        "scale": scale,
        "translate_x": 256.0 - (min_x + width / 2.0) * scale,
        "translate_y": 256.0 - (min_y + height / 2.0) * scale,
    }


def _render_source_segment_chunk(
    segments: list[dict[str, Any]], transform: dict[str, float]
) -> str:
    if not segments:
        raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_CHUNK_EMPTY")
    scale = transform["scale"]
    translate_x = transform["translate_x"]
    translate_y = transform["translate_y"]

    def point(value: tuple[float, float]) -> tuple[float, float]:
        result = (value[0] * scale + translate_x, value[1] * scale + translate_y)
        if any(not 16.0 <= coordinate <= 496.0 for coordinate in result):
            raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_COORDINATE_OUT_OF_BOUNDS")
        return result

    start = point(segments[0]["start"])
    commands = [f"M {_source_svg_number(start[0])} {_source_svg_number(start[1])}"]
    active_subpath_index = segments[0]["subpath_index"]
    for segment in segments:
        if segment["subpath_index"] != active_subpath_index:
            move_to = point(segment["start"])
            commands.append(f"M {_source_svg_number(move_to[0])} {_source_svg_number(move_to[1])}")
            active_subpath_index = segment["subpath_index"]
        if segment["kind"] == "cubic":
            control_1 = point(segment["control_1"])
            control_2 = point(segment["control_2"])
            end = point(segment["end"])
            commands.append(
                "C "
                + " ".join(_source_svg_number(value) for value in (*control_1, *control_2, *end))
            )
        else:
            end = point(segment["end"])
            commands.append(f"L {_source_svg_number(end[0])} {_source_svg_number(end[1])}")
    return " ".join(commands)


def _chunk_source_segments(
    candidate: dict[str, Any],
    *,
    max_commands_per_chunk: int,
    first_chunk_command_limit: int | None = None,
    max_chars: int = 680,
) -> list[dict[str, Any]]:
    transform = _source_viewbox_transform(candidate["parsed_svg"]["view_box"])
    chunks: list[dict[str, Any]] = []
    first_chunk_pending = first_chunk_command_limit is not None
    for path in candidate["parsed_svg"]["paths"]:
        source_segments = _parse_source_svg_path_segments(path["d"])
        start = 0
        while start < len(source_segments):
            chunk_limit = (
                first_chunk_command_limit
                if first_chunk_pending and first_chunk_command_limit is not None
                else max_commands_per_chunk
            )
            end = min(start + chunk_limit, len(source_segments))
            chunk_segments = source_segments[start:end]
            path_data = _render_source_segment_chunk(chunk_segments, transform)
            while len(path_data) > max_chars and len(chunk_segments) > 1:
                end -= 1
                chunk_segments = source_segments[start:end]
                path_data = _render_source_segment_chunk(chunk_segments, transform)
            if len(path_data) > max_chars:
                raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_CHUNK_TOO_LONG")
            chunks.append({
                "path_id": f"source_segment_{len(chunks) + 1:03d}",
                "d": path_data,
                "source_path_id": path["path_id"],
                "source_subpath_index": chunk_segments[0]["subpath_index"],
                "source_subpath_indices": list(dict.fromkeys(
                    segment["subpath_index"] for segment in chunk_segments
                )),
                "source_segment_start": start + 1,
                "source_segment_end": start + len(chunk_segments),
                "source_segment_count": len(chunk_segments),
            })
            start += len(chunk_segments)
            first_chunk_pending = False
    return chunks


def _segment_openclipart_candidate(candidate: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    last_error: _SvgSourceSegmentationError | None = None
    for chunk_limit in (*range(12, 25), *range(11, 0, -1)):
        try:
            base_chunks = _chunk_source_segments(
                candidate,
                max_commands_per_chunk=chunk_limit,
                first_chunk_command_limit=6,
            )
            first_step_chunk_index, first_step_bbox_area = _select_first_step_source_chunk(
                candidate, base_chunks
            )
            if first_step_chunk_index is None:
                raise _SvgSourceSegmentationError(
                    "SVG_SOURCE_SEGMENT_NO_SIMPLE_INTRO_CONTOUR"
                )
            if not 8 <= len(base_chunks) <= 20:
                raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_COUNT_OUT_OF_RANGE")
            first_step_parts = _split_source_chunk_for_first_step(
                candidate,
                base_chunks[first_step_chunk_index],
            )
            final_chunk_count = len(base_chunks) - 1 + len(first_step_parts)
            if not 8 <= final_chunk_count <= 20:
                raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_COUNT_OUT_OF_RANGE")

            chunks: list[dict[str, Any]] = []
            first_step_chunk_positions: list[int] = []
            for index, chunk in enumerate(base_chunks):
                if index == first_step_chunk_index:
                    first_step_chunk_positions = [len(chunks), len(chunks) + 1]
                    chunks.extend(first_step_parts)
                else:
                    chunks.append(chunk)
            for index, chunk in enumerate(chunks, start=1):
                chunk["path_id"] = f"source_segment_{index:03d}"

            transform = _source_viewbox_transform(candidate["parsed_svg"]["view_box"])
            return chunks, {
                **transform,
                "source_path_count": len(candidate["parsed_svg"]["paths"]),
                "derived_chunk_count": len(chunks),
                "source_segment_count": sum(chunk["source_segment_count"] for chunk in chunks),
                "chunk_command_limit": chunk_limit,
                "first_chunk_command_limit": 6,
                "first_step_segment_ids": [
                    chunks[index]["path_id"] for index in first_step_chunk_positions
                ],
                "first_step_source_path_id": base_chunks[first_step_chunk_index][
                    "source_path_id"
                ],
                "first_step_source_segment_start": base_chunks[first_step_chunk_index][
                    "source_segment_start"
                ],
                "first_step_source_segment_count": 8,
                "first_step_bbox_area": round(first_step_bbox_area, 3),
                "guide_view_box": "0 0 512 512",
            }
        except _SvgSourceSegmentationError as exc:
            last_error = exc
            if str(exc) not in {
                "SVG_SOURCE_SEGMENT_COUNT_OUT_OF_RANGE",
                "SVG_SOURCE_SEGMENT_CHUNK_TOO_LONG",
                "SVG_SOURCE_SEGMENT_NO_SIMPLE_INTRO_CONTOUR",
            }:
                raise
    raise last_error or _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_COUNT_OUT_OF_RANGE")


def _source_segment_bbox_area(
    segments: list[dict[str, Any]], transform: dict[str, float]
) -> float:
    points: list[tuple[float, float]] = []
    for segment in segments:
        points.extend((segment["start"], segment["end"]))
        if segment["kind"] == "cubic":
            points.extend((segment["control_1"], segment["control_2"]))
    if not points:
        return 0.0
    xs = [point[0] * transform["scale"] + transform["translate_x"] for point in points]
    ys = [point[1] * transform["scale"] + transform["translate_y"] for point in points]
    if any(not math.isfinite(value) for value in (*xs, *ys)):
        return 0.0
    return max(0.0, max(xs) - min(xs)) * max(0.0, max(ys) - min(ys))


def _select_first_step_source_chunk(
    candidate: dict[str, Any], chunks: list[dict[str, Any]]
) -> tuple[int | None, float]:
    transform = _source_viewbox_transform(candidate["parsed_svg"]["view_box"])
    source_segments_by_path = {
        path["path_id"]: _parse_source_svg_path_segments(path["d"])
        for path in candidate["parsed_svg"]["paths"]
    }
    best_index: int | None = None
    best_area = -1.0
    for index, chunk in enumerate(chunks):
        if chunk["source_segment_count"] < 8:
            continue
        source_segments = source_segments_by_path[chunk["source_path_id"]]
        first_eight = source_segments[
            chunk["source_segment_start"] - 1 : chunk["source_segment_start"] + 7
        ]
        if (
            len(first_eight) != 8
            or len({item["subpath_index"] for item in first_eight}) != 1
        ):
            continue
        area = _source_segment_bbox_area(first_eight, transform)
        if area > best_area:
            best_index = index
            best_area = area
    if best_index is None:
        return None, 0.0
    return best_index, best_area


def _source_segment_chunk_record(
    path: dict[str, Any],
    source_segments: list[dict[str, Any]],
    *,
    source_segment_start: int,
    transform: dict[str, float],
) -> dict[str, Any]:
    if not source_segments:
        raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_CHUNK_EMPTY")
    path_data = _render_source_segment_chunk(source_segments, transform)
    if len(path_data) > 680:
        raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_CHUNK_TOO_LONG")
    subpath_indices = list(dict.fromkeys(
        segment["subpath_index"] for segment in source_segments
    ))
    return {
        "path_id": "",
        "d": path_data,
        "source_path_id": path["path_id"],
        "source_subpath_index": source_segments[0]["subpath_index"],
        "source_subpath_indices": subpath_indices,
        "source_segment_start": source_segment_start,
        "source_segment_end": source_segment_start + len(source_segments) - 1,
        "source_segment_count": len(source_segments),
    }


def _split_source_chunk_for_first_step(
    candidate: dict[str, Any], chunk: dict[str, Any]
) -> list[dict[str, Any]]:
    source_path = next(
        path
        for path in candidate["parsed_svg"]["paths"]
        if path["path_id"] == chunk["source_path_id"]
    )
    source_segments = _parse_source_svg_path_segments(source_path["d"])
    start_index = chunk["source_segment_start"] - 1
    chunk_segments = source_segments[start_index : chunk["source_segment_end"]]
    first_eight = chunk_segments[:8]
    if (
        len(first_eight) != 8
        or len({segment["subpath_index"] for segment in first_eight}) != 1
    ):
        raise _SvgSourceSegmentationError("SVG_SOURCE_SEGMENT_NO_SIMPLE_INTRO_CONTOUR")
    transform = _source_viewbox_transform(candidate["parsed_svg"]["view_box"])
    chunks = [
        _source_segment_chunk_record(
            source_path,
            first_eight[:4],
            source_segment_start=chunk["source_segment_start"],
            transform=transform,
        ),
        _source_segment_chunk_record(
            source_path,
            first_eight[4:],
            source_segment_start=chunk["source_segment_start"] + 4,
            transform=transform,
        ),
    ]
    remaining = chunk_segments[8:]
    if remaining:
        chunks.append(
            _source_segment_chunk_record(
                source_path,
                remaining,
                source_segment_start=chunk["source_segment_start"] + 8,
                transform=transform,
            )
        )
    return chunks


def _svg_catalog_construction_prompt(
    data: dict[str, Any], candidate: dict[str, Any]
) -> str:
    paths = candidate["parsed_svg"]["paths"]
    atlas_mapping = [
        {"atlas_label": f"P{index:02d}", "source_path_id": item["path_id"]}
        for index, item in enumerate(paths, start=1)
    ]
    return (
        "Hãy nhìn ảnh màu nguồn để hiểu đúng con vật/đồ vật và hướng của nó; ảnh atlas giúp "
        "đối chiếu từng vùng với source_path_id. Tạo một bài hướng dẫn vẽ MỚI, không lần theo "
        "đường viền và không chép geometry của nguồn. Bài vẽ cuối phải có cùng chủ thể, hướng "
        "nhìn và những đặc điểm dễ nhận ra, nhưng được đơn giản hóa cho trẻ. Bỏ vân, lông và "
        "trang trí nhỏ.\n"
        "Bắt đầu bằng 1–3 nét khung lớn dễ vẽ (ví dụ oval thân, oval đầu, cung cổ); bước 1 chỉ "
        "được dùng role=construction, tuyệt đối chưa vẽ đường bao hoàn chỉnh hay mắt/mũi/mỏ. "
        "Sau đó nối khối chính, thêm các bộ phận làm đúng dáng và cuối cùng thêm vài nét nhận "
        f"dạng. Dùng chính xác {SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT} nét tổng cộng. "
        "Output phải chứa object strokes_by_id với đầy đủ các khóa guide_stroke_01 đến "
        f"guide_stroke_{SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT:02d}, không bỏ khóa nào. "
        "Mỗi nét có role, feature_vi riêng, 1–6 source_path_ids lấy từ atlas mapping, và geometry "
        "dạng dữ liệu; tuyệt đối KHÔNG viết chuỗi SVG d/path hoặc SVG command.\n"
        "geometry gồm primitive và points p0,p1,p2,p3; mọi tọa độ là số nguyên 16..496. "
        "Chọn primitive phù hợp với bộ phận: ellipse dùng p0=đỉnh trên, p1=điểm phải, "
        "p2=điểm dưới, p3=điểm trái; cubic dùng p0=điểm bắt đầu, p1/p2=hai điểm điều khiển, "
        "p3=điểm kết thúc; polyline dùng p0..p3 theo thứ tự vẽ.\n"
        "Chọn các bộ phận/nét hình khác nhau phù hợp chính chủ thể. Mỗi feature_vi phải gọi tên "
        "một bộ phận hoặc đường hình khác nhau; không lặp mô tả chung, không dùng lại cùng một "
        "primitive/điểm cho nhiều nét. Với con vật, cân nhắc thân, đầu, cổ, chân, đuôi và bộ phận "
        "mặt phù hợp; với đồ vật, chọn các phần cấu tạo nhìn thấy được của chính đồ vật.\n"
        "Hãy trả 4–8 stage trong array theo đúng thứ tự; step_index của stage đầu là 1 rồi "
        "tăng liên tục đúng theo vị trí array (không bỏ số, không lặp số). Mỗi guide_stroke_01 "
        "đến guide_stroke_08 phải xuất hiện trong đúng một stage; không bỏ, lặp hoặc đổi ID. "
        "Stage đầu chỉ chứa nét construction và không quá 3 nét. Lời hướng dẫn là một "
        "câu ngắn, cụ thể, trẻ có thể làm theo; nói hình dạng, hướng hoặc điểm nối đang vẽ.\n"
        "RÀNG BUỘC BẮT BUỘC CHO BƯỚC CUỐI: phải có ít nhất một nét có role đúng bằng "
        "'feature' và path_id của nét đó phải xuất hiện trong stroke_ids của stage cuối cùng. "
        "Hãy dành riêng một nét nhận dạng mới cho stage cuối (ví dụ mắt, tai, ria, mỏ hoặc "
        "đuôi tùy con vật); không xếp tất cả nét role='feature' vào các stage trước. instruction_vi "
        "của stage cuối phải mô tả đúng đặc điểm đó. role của một nét và stage chứa path_id của "
        "nét ấy phải khớp nhau; chỉ viết câu 'thêm đặc điểm nhận dạng' là chưa đủ.\n"
        f"Chủ đề: {json.dumps(data['topic'], ensure_ascii=False)}. Độ khó: {data['difficulty']}.\n"
        f"Tên nguồn: {json.dumps(candidate.get('title', ''), ensure_ascii=False)}. "
        f"Mô tả: {json.dumps(candidate.get('description', ''), ensure_ascii=False)}. "
        f"Từ khóa: {json.dumps(candidate.get('tags', ''), ensure_ascii=False)}.\n"
        f"Source path count: {len(paths)}. Atlas mapping: "
        f"{json.dumps(atlas_mapping, ensure_ascii=False, separators=(',', ':'))}"
    )


def _svg_catalog_construction_schema(paths: list[dict[str, Any]]) -> dict[str, Any]:
    source_path_ids = [path["path_id"] for path in paths]
    stroke_ids = [
        f"guide_stroke_{index:02d}"
        for index in range(1, SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT + 1)
    ]
    coordinate = {"type": "integer", "minimum": 16, "maximum": 496}
    point = {
        "type": "object",
        "properties": {"x": coordinate, "y": coordinate},
        "required": ["x", "y"],
        "additionalProperties": False,
    }
    points = {
        "type": "object",
        "properties": {f"p{index}": point for index in range(4)},
        "required": [f"p{index}" for index in range(4)],
        "additionalProperties": False,
    }
    geometry = {
        "type": "object",
        "properties": {
            "primitive": {"type": "string", "enum": ["ellipse", "cubic", "polyline"]},
            "points": points,
        },
        "required": ["primitive", "points"],
        "additionalProperties": False,
    }
    stroke_record = {
        "type": "object",
        "properties": {
            "geometry": geometry,
            "role": {
                "type": "string",
                "enum": ["construction", "outline", "feature"],
            },
            "feature_vi": {"type": "string", "minLength": 1, "maxLength": 100},
            "source_path_ids": {
                "type": "array",
                "minItems": 1,
                "maxItems": 6,
                "items": {"type": "string", "enum": source_path_ids},
            },
        },
        "required": ["geometry", "role", "feature_vi", "source_path_ids"],
        "additionalProperties": False,
    }
    strokes_by_id = {
        "type": "object",
        "properties": {stroke_id: stroke_record for stroke_id in stroke_ids},
        "required": stroke_ids,
        "additionalProperties": False,
    }
    stage = {
        "type": "object",
        "properties": {
            "step_index": {"type": "integer", "minimum": 1, "maximum": 8},
            "label_vi": {"type": "string", "minLength": 1, "maxLength": 60},
            "instruction_vi": {"type": "string", "minLength": 1, "maxLength": 120},
            "stroke_ids": {
                "type": "array",
                "minItems": 1,
                "maxItems": SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT,
                "items": {"type": "string", "enum": stroke_ids},
            },
        },
        "required": ["step_index", "label_vi", "instruction_vi", "stroke_ids"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "schema_version": {
                "type": "string",
                "enum": ["SvgTopicStrokeGuideConstructionContentV1"],
            },
            "title_vi": {"type": "string", "minLength": 1, "maxLength": 120},
            "strokes_by_id": strokes_by_id,
            "stages": {"type": "array", "minItems": 4, "maxItems": 8, "items": stage},
        },
        "required": ["schema_version", "title_vi", "strokes_by_id", "stages"],
        "additionalProperties": False,
    }


def _render_svg_construction_primitive(
    geometry: Any, *, stroke_index: int
) -> tuple[str, str, int]:
    diagnostics: dict[str, int | str | None] = {"stroke_index": stroke_index}
    if not isinstance(geometry, dict) or set(geometry) != {"primitive", "points"}:
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_SCHEMA_INVALID", diagnostics
        )
    primitive = geometry["primitive"]
    points = geometry["points"]
    expected_points = {f"p{index}" for index in range(4)}
    if (
        primitive not in {"ellipse", "cubic", "polyline"}
        or not isinstance(points, dict)
        or set(points) != expected_points
    ):
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_SCHEMA_INVALID", diagnostics
        )

    parsed_points: dict[str, tuple[int, int]] = {}
    for point_id in sorted(expected_points):
        point = points[point_id]
        if (
            not isinstance(point, dict)
            or set(point) != {"x", "y"}
            or any(
                isinstance(point.get(axis), bool)
                or not isinstance(point.get(axis), int)
                or not 16 <= point[axis] <= 496
                for axis in ("x", "y")
            )
        ):
            diagnostics["coordinate_failure_count"] = 1
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_COORDINATE_INVALID", diagnostics
            )
        parsed_points[point_id] = (point["x"], point["y"])

    p0, p1, p2, p3 = (parsed_points[f"p{index}"] for index in range(4))
    if primitive == "cubic":
        if len({p0, p1, p2, p3}) < 3:
            diagnostics["degenerate_geometry_count"] = 1
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_DEGENERATE", diagnostics
            )
        path_data = f"M {p0[0]} {p0[1]} C {p1[0]} {p1[1]} {p2[0]} {p2[1]} {p3[0]} {p3[1]}"
        return path_data, primitive, 2

    if primitive == "polyline":
        ordered = (p0, p1, p2, p3)
        if any(left == right for left, right in zip(ordered, ordered[1:])) or len(set(ordered)) < 3:
            diagnostics["degenerate_geometry_count"] = 1
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_DEGENERATE", diagnostics
            )
        path_data = "M " + " L ".join(f"{point[0]} {point[1]}" for point in ordered)
        return path_data, primitive, 4

    top, right, bottom, left = p0, p1, p2, p3
    center_x = (left[0] + right[0]) / 2
    center_y = (top[1] + bottom[1]) / 2
    radius_x = (right[0] - left[0]) / 2
    radius_y = (bottom[1] - top[1]) / 2
    if (
        radius_x < 8
        or radius_y < 8
        or abs(top[0] - center_x) > 24
        or abs(bottom[0] - center_x) > 24
        or abs(left[1] - center_y) > 24
        or abs(right[1] - center_y) > 24
    ):
        diagnostics["degenerate_geometry_count"] = 1
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_DEGENERATE", diagnostics
        )

    def format_number(number: float) -> str:
        return f"{number:.3f}".rstrip("0").rstrip(".")

    kappa = 0.55228475
    rx_control = radius_x * kappa
    ry_control = radius_y * kappa
    cx = format_number(center_x)
    cy = format_number(center_y)
    rx = format_number(radius_x)
    ry = format_number(radius_y)
    c_rx = format_number(rx_control)
    c_ry = format_number(ry_control)
    path_data = (
        f"M {cx} {format_number(center_y - radius_y)} "
        f"C {format_number(center_x + rx_control)} {format_number(center_y - radius_y)} "
        f"{format_number(center_x + radius_x)} {format_number(center_y - ry_control)} "
        f"{format_number(center_x + radius_x)} {cy} "
        f"C {format_number(center_x + radius_x)} {format_number(center_y + ry_control)} "
        f"{format_number(center_x + rx_control)} {format_number(center_y + radius_y)} "
        f"{cx} {format_number(center_y + radius_y)} "
        f"C {format_number(center_x - rx_control)} {format_number(center_y + radius_y)} "
        f"{format_number(center_x - radius_x)} {format_number(center_y + ry_control)} "
        f"{format_number(center_x - radius_x)} {cy} "
        f"C {format_number(center_x - radius_x)} {format_number(center_y - ry_control)} "
        f"{format_number(center_x - rx_control)} {format_number(center_y - radius_y)} "
        f"{cx} {format_number(center_y - radius_y)} Z"
    )
    return path_data, primitive, 6


def _normalize_svg_catalog_construction_output(text: str) -> str:
    expected_stroke_ids = [
        f"guide_stroke_{index:02d}"
        for index in range(1, SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT + 1)
    ]
    expected_stroke_set = set(expected_stroke_ids)
    diagnostics: dict[str, int | str | None] = {
        "expected_stroke_count": len(expected_stroke_ids),
        "generated_stroke_count": 0,
        "missing_stroke_count": len(expected_stroke_ids),
        "unknown_stroke_count": 0,
    }
    try:
        value = json.loads(text, object_pairs_hook=_json_object_reject_duplicate_keys)
    except _DuplicateJsonObjectKey as exc:
        diagnostics["duplicate_object_key_count"] = exc.duplicate_count
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_DUPLICATE_JSON_KEY", diagnostics
        ) from exc
    except json.JSONDecodeError as exc:
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_JSON_INVALID", diagnostics
        ) from exc

    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "title_vi", "strokes_by_id", "stages"}
        or value.get("schema_version") != "SvgTopicStrokeGuideConstructionContentV1"
        or not isinstance(value.get("title_vi"), str)
        or not isinstance(value.get("strokes_by_id"), dict)
        or not isinstance(value.get("stages"), list)
    ):
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_GENERATION_SCHEMA_INVALID", diagnostics
        )

    strokes_by_id = value["strokes_by_id"]
    actual_stroke_ids = set(strokes_by_id)
    diagnostics["generated_stroke_count"] = len(strokes_by_id)
    diagnostics["missing_stroke_count"] = len(expected_stroke_set - actual_stroke_ids)
    diagnostics["unknown_stroke_count"] = len(actual_stroke_ids - expected_stroke_set)
    if actual_stroke_ids != expected_stroke_set:
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_GENERATION_STROKE_SET_INVALID", diagnostics
        )

    normalized_strokes: list[dict[str, Any]] = []
    primitive_counts = {"ellipse": 0, "cubic": 0, "polyline": 0}
    generated_command_count = 0
    for stroke_id in expected_stroke_ids:
        raw_stroke = strokes_by_id[stroke_id]
        if not isinstance(raw_stroke, dict) or set(raw_stroke) != {
            "geometry", "role", "feature_vi", "source_path_ids"
        }:
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_GENERATION_STROKE_INVALID", diagnostics
            )
        stroke_index = len(normalized_strokes) + 1
        path_data, primitive, command_count = _render_svg_construction_primitive(
            raw_stroke["geometry"], stroke_index=stroke_index
        )
        primitive_counts[primitive] += 1
        generated_command_count += command_count
        normalized_strokes.append(
            {
                "path_id": stroke_id,
                "d": path_data,
                "role": raw_stroke["role"],
                "feature_vi": raw_stroke["feature_vi"],
                "source_path_ids": raw_stroke["source_path_ids"],
            }
        )

    diagnostics["primitive_ellipse_count"] = primitive_counts["ellipse"]
    diagnostics["primitive_cubic_count"] = primitive_counts["cubic"]
    diagnostics["primitive_polyline_count"] = primitive_counts["polyline"]
    diagnostics["generated_command_count"] = generated_command_count

    normalized = {
        "schema_version": value["schema_version"],
        "title_vi": value["title_vi"],
        "strokes": normalized_strokes,
        "stages": value["stages"],
    }
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))


def _parse_svg_catalog_construction_guide(
    text: str, source_paths: list[dict[str, Any]]
) -> dict[str, Any]:
    source_ids = {path["path_id"] for path in source_paths}
    source_geometries = {path["d"].strip() for path in source_paths}
    diagnostics: dict[str, int | str | None] = {
        "expected_source_path_count": len(source_ids),
        "stroke_count": 0,
        "stage_count": 0,
        "unknown_anchor_count": 0,
        "unassigned_stroke_count": 0,
        "total_geometry_chars": 0,
        "max_total_geometry_chars": SVG_TOPIC_GUIDE_MAX_TOTAL_GEOMETRY_CHARS,
        "unique_geometry_count": 0,
        "duplicate_geometry_count": 0,
        "first_duplicate_stroke_index": 0,
    }
    try:
        value = json.loads(text, object_pairs_hook=_json_object_reject_duplicate_keys)
    except _DuplicateJsonObjectKey as exc:
        diagnostics["duplicate_object_key_count"] = exc.duplicate_count
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_DUPLICATE_JSON_KEY", diagnostics
        ) from exc
    except json.JSONDecodeError as exc:
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_JSON_INVALID", diagnostics
        ) from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "title_vi", "strokes", "stages"}
        or value.get("schema_version") != "SvgTopicStrokeGuideConstructionContentV1"
        or not isinstance(value.get("title_vi"), str)
        or not 1 <= len(value["title_vi"].strip()) <= 120
        or not isinstance(value.get("strokes"), list)
        or not SVG_TOPIC_GUIDE_MIN_CONSTRUCTION_STROKES
        <= len(value["strokes"])
        <= SVG_TOPIC_GUIDE_MAX_CONSTRUCTION_STROKES
        or not isinstance(value.get("stages"), list)
        or not 4 <= len(value["stages"]) <= 8
    ):
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_SCHEMA_INVALID", diagnostics
        )
    diagnostics["stage_count"] = len(value["stages"])

    strokes: dict[str, dict[str, Any]] = {}
    path_data_seen: set[str] = set()
    feature_labels_seen: set[str] = set()
    total_path_chars = 0
    unknown_anchor_count = 0
    for raw in value["strokes"]:
        if not isinstance(raw, dict) or set(raw) != {
            "path_id", "d", "role", "feature_vi", "source_path_ids"
        }:
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_STROKE_INVALID", diagnostics
            )
        path_id = raw.get("path_id")
        data = raw.get("d")
        role = raw.get("role")
        feature = raw.get("feature_vi")
        anchors = raw.get("source_path_ids")
        if (
            not isinstance(path_id, str)
            or re.fullmatch(r"guide_stroke_[0-9]{2}", path_id) is None
            or path_id in strokes
            or not isinstance(data, str)
            or not 1 <= len(data.strip()) <= SVG_TOPIC_GUIDE_MAX_STROKE_CHARS
            or re.fullmatch(r"[MLCQZ0-9+.,\-eE\s]+", data) is None
            or not isinstance(role, str)
            or role not in {"construction", "outline", "feature"}
            or not isinstance(feature, str)
            or not 1 <= len(feature.strip()) <= 100
            or not isinstance(anchors, list)
            or not 1 <= len(anchors) <= 6
            or any(not isinstance(anchor, str) for anchor in anchors)
            or len(anchors) != len(set(anchors))
        ):
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_STROKE_INVALID", diagnostics
            )
        unknown_anchor_count += sum(anchor not in source_ids for anchor in anchors)
        if unknown_anchor_count:
            diagnostics["unknown_anchor_count"] = unknown_anchor_count
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_SOURCE_ANCHOR_INVALID", diagnostics
            )
        feature_key = unicodedata.normalize("NFKC", feature).strip().casefold()
        duplicate_feature_label = feature_key in feature_labels_seen
        if duplicate_feature_label:
            diagnostics["duplicate_feature_label_count"] = (
                int(diagnostics.get("duplicate_feature_label_count", 0)) + 1
            )
        else:
            feature_labels_seen.add(feature_key)
        total_path_chars += len(data)
        diagnostics["stroke_count"] = len(strokes) + 1
        diagnostics["total_geometry_chars"] = total_path_chars
        if data.strip() in path_data_seen:
            diagnostics["geometry_failure"] = "DUPLICATE_STROKE_GEOMETRY"
            diagnostics["duplicate_geometry_count"] = 1
            diagnostics["unique_geometry_count"] = len(path_data_seen)
            diagnostics["first_duplicate_stroke_index"] = len(strokes) + 1
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID", diagnostics
            )
        if duplicate_feature_label:
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_FEATURE_LABEL_DUPLICATE", diagnostics
            )
        if total_path_chars > SVG_TOPIC_GUIDE_MAX_TOTAL_GEOMETRY_CHARS:
            diagnostics["geometry_failure"] = "TOTAL_GEOMETRY_CHAR_LIMIT"
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID", diagnostics
            )
        if data.strip() in source_geometries:
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_SOURCE_GEOMETRY_COPIED", diagnostics
            )
        if not 2 <= len(re.findall(r"[MLCQZ]", data)) <= 24:
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_STROKE_COMPLEXITY_INVALID", diagnostics
            )
        path_data_seen.add(data.strip())
        diagnostics["unique_geometry_count"] = len(path_data_seen)
        strokes[path_id] = {
            "path_id": path_id,
            "d": data.strip(),
            "role": role,
            "feature_vi": feature.strip(),
            "source_path_ids": list(anchors),
        }

    stages: list[dict[str, Any]] = []
    assigned: set[str] = set()
    for expected_index, raw in enumerate(value["stages"], start=1):
        if not isinstance(raw, dict) or set(raw) != {
            "step_index", "label_vi", "instruction_vi", "stroke_ids"
        }:
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_STAGE_INVALID", diagnostics
            )
        step_index = raw.get("step_index")
        label = raw.get("label_vi")
        instruction = raw.get("instruction_vi")
        stroke_ids = raw.get("stroke_ids")
        stage_failures: list[str] = []
        if (
            isinstance(step_index, bool)
            or not isinstance(step_index, int)
            or step_index != expected_index
        ):
            stage_failures.append("step_index")
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 60:
            stage_failures.append("label")
        if (
            not isinstance(instruction, str)
            or not 1 <= len(instruction.strip()) <= 120
        ):
            stage_failures.append("instruction")
        if not isinstance(stroke_ids, list) or not stroke_ids:
            stage_failures.append("stroke_ids_empty_or_not_list")
        elif any(not isinstance(stroke_id, str) for stroke_id in stroke_ids):
            stage_failures.append("stroke_id_type")
        else:
            if len(stroke_ids) != len(set(stroke_ids)):
                stage_failures.append("duplicate_within_stage")
            if any(stroke_id not in strokes for stroke_id in stroke_ids):
                stage_failures.append("unknown_stroke_id")
            if assigned.intersection(stroke_ids):
                stage_failures.append("duplicate_across_stages")
        if stage_failures:
            diagnostics["stage_array_index"] = expected_index
            diagnostics["stage_failure"] = ",".join(stage_failures)
            diagnostics["stage_stroke_id_count"] = (
                len(stroke_ids) if isinstance(stroke_ids, list) else 0
            )
            raise _SvgCatalogPlanValidationError(
                "SVG_CONSTRUCTION_GUIDE_STAGE_INVALID", diagnostics
            )
        if expected_index == 1:
            command_counts = [
                len(re.findall(r"[MLCQZ]", strokes[stroke_id]["d"]))
                for stroke_id in stroke_ids
            ]
            diagnostics["first_step_stroke_count"] = len(stroke_ids)
            diagnostics["first_step_max_command_count"] = max(command_counts, default=0)
            diagnostics["first_step_over_complexity_count"] = sum(
                count > 8 for count in command_counts
            )
            diagnostics["first_step_nonconstruction_count"] = sum(
                strokes[stroke_id]["role"] != "construction" for stroke_id in stroke_ids
            )
            if (
                len(stroke_ids) > 3
                or diagnostics["first_step_nonconstruction_count"]
                or diagnostics["first_step_over_complexity_count"]
            ):
                raise _SvgCatalogPlanValidationError(
                    "SVG_CONSTRUCTION_GUIDE_FIRST_STEP_NOT_CONSTRUCTION", diagnostics
                )
        assigned.update(stroke_ids)
        stages.append({
            "step_index": expected_index,
            "label_vi": label.strip(),
            "instruction_vi": instruction.strip(),
            "stroke_ids": list(stroke_ids),
        })
    diagnostics["stroke_count"] = len(strokes)
    diagnostics["stage_count"] = len(stages)
    diagnostics["unassigned_stroke_count"] = len(set(strokes) - assigned)
    if assigned != set(strokes):
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_PATH_COVERAGE_INVALID", diagnostics
        )
    feature_stroke_ids = {
        path_id for path_id, stroke in strokes.items() if stroke["role"] == "feature"
    }
    final_feature_stroke_count = len(
        feature_stroke_ids.intersection(stages[-1]["stroke_ids"])
    )
    diagnostics["feature_stroke_count"] = len(feature_stroke_ids)
    diagnostics["final_stage_feature_stroke_count"] = final_feature_stroke_count
    diagnostics["last_feature_stage_index"] = max(
        (
            stage["step_index"]
            for stage in stages
            if feature_stroke_ids.intersection(stage["stroke_ids"])
        ),
        default=0,
    )
    if final_feature_stroke_count == 0:
        raise _SvgCatalogPlanValidationError(
            "SVG_CONSTRUCTION_GUIDE_FINAL_FEATURE_MISSING", diagnostics
        )
    return {
        "schema_version": "SvgTopicStrokeGuideConstructionContentV1",
        "title_vi": value["title_vi"].strip(),
        "strokes": list(strokes.values()),
        "stages": stages,
    }


def _svg_catalog_source_plan_prompt(
    data: dict[str, Any], candidate: dict[str, Any]
) -> str:
    paths = candidate["parsed_svg"]["paths"]
    atlas_mapping = [
        {"atlas_label": f"P{index:02d}", "source_path_id": item["path_id"]}
        for index, item in enumerate(paths, start=1)
    ]
    return (
        "Lập thứ tự tiến dần cho đúng hình SVG ở ảnh nguồn. Ảnh atlas thứ hai tách riêng từng path; "
        "mã Pxx khớp với bảng path_id bên dưới. Không được đổi hoặc tạo geometry, chỉ trả JSON gồm "
        "schema_version=SvgOpenclipartSourceStrokePlanV3, title_vi, stages và path_stage_assignments. "
        "Mỗi stage chỉ có label_vi và instruction_vi; vị trí trong array chính là số bước, "
        "không xuất step_index. path_stage_assignments là một JSON "
        "object: mỗi path_id trong Atlas mapping là một property đúng một lần, giá trị là số bước "
        "từ 1 tới số stage. Phải dùng đủ mọi path_id; không được thêm key nào. Mỗi bước phải nhận "
        "ít nhất một path. Dùng 4–8 bước. Đưa đường bao lớn và bộ phận chính lên trước, chi tiết nhỏ sau. "
        "Chỉ dẫn ngắn, tiếng Việt tự nhiên cho trẻ; không thêm nền/đồ vật không có trong ảnh.\n"
        f"Chủ đề người lớn chọn: {json.dumps(data['topic'], ensure_ascii=False)}\n"
        f"Độ khó: {data['difficulty']}\n"
        f"Path count: {len(paths)}\n"
        f"Atlas mapping: {json.dumps(atlas_mapping, ensure_ascii=False, separators=(',', ':'))}"
    )


def _svg_catalog_segment_plan_prompt(
    data: dict[str, Any],
    candidate: dict[str, Any],
    segments: list[dict[str, Any]],
    *,
    first_step_segment_ids: list[str] | None = None,
) -> str:
    atlas_mapping = [
        {
            "atlas_label": f"P{index:02d}",
            "segment_id": segment["path_id"],
            "source_path_id": segment["source_path_id"],
            "source_subpath_indices": segment["source_subpath_indices"],
            "drawable_command_count": len(re.findall(r"[MLCQZ]", segment["d"])),
        }
        for index, segment in enumerate(segments, start=1)
    ]
    first_step_rule = (
        " Bước đầu phải chứa đúng hai segment_id được cố định: "
        f"{json.dumps(first_step_segment_ids, ensure_ascii=False)}. Đây là hai đoạn liên tiếp "
        "của cùng một đường nguồn; chỉ mô tả đúng đường cong đang hiện, không gọi nó là cổ, "
        "thân hoặc bộ phận khác nếu hai nét chưa vẽ phần đó. Không nói rằng hình đã hoàn thành "
        "và không thêm bộ phận không hiện trong hai nét này. Mọi segment khác phải "
        "được xếp từ bước 2 trở đi."
        if first_step_segment_ids
        else " Bước đầu chỉ chọn tối đa 3 nét có drawable_command_count không quá 8; ưu tiên "
        "nét cong lớn tạo thân/khung, không chọn mắt, mũi hay chi tiết nhỏ làm bước đầu."
    )
    return (
        "Xếp thứ tự dạy vẽ cho đúng con vật trong ảnh màu. Atlas bên cạnh có một ô Pxx cho mỗi "
        "đoạn nét: toàn bộ hình nguồn được vẽ mờ xám đúng vị trí và riêng đoạn Pxx đang xét được "
        "tô xanh. Dùng vị trí của nét xanh trên toàn con vật để nhận diện bộ phận; đừng suy đoán "
        "chỉ từ hình dáng khi nét đứng riêng. Mỗi ô là một đoạn nét nguyên vẹn có thật trong SVG. "
        "Bạn KHÔNG được tạo, "
        "sửa, bỏ, chia, ghép hoặc mô tả nét không có trong atlas; chỉ gán mỗi segment_id vào "
        "đúng một bước. Trả JSON SvgOpenclipartSourceStrokePlanV3 với stages gồm 4–8 bước tuần tự "
        "và path_stage_assignments có đúng toàn bộ segment_id bên dưới, mỗi ID một lần, giá trị "
        "là step_index. Mọi bước phải có ít nhất một nét."
        + first_step_rule
        + " Không đưa đủ đường bao hoàn chỉnh vào bước đầu. "
        "Nét khuôn mặt và chi tiết nhận dạng "
        "để ở bước sau. Lời hướng dẫn ngắn bằng tiếng Việt và chỉ mô tả nét được thêm ở bước đó; "
        "không nói có tai, chân, đuôi hay bộ phận nào nếu các ô của bước đó không thể hiện chúng. "
        "Ảnh nguồn màu là chuẩn nhận diện cuối; không thêm nền, vật thể hay chi tiết mới.\n"
        f"Chủ đề: {json.dumps(data['topic'], ensure_ascii=False)}\n"
        f"Độ khó: {data['difficulty']}\n"
        f"Nguồn có {len(candidate['parsed_svg']['paths'])} path; đã chia an toàn thành {len(segments)} nét.\n"
        f"Atlas mapping: {json.dumps(atlas_mapping, ensure_ascii=False, separators=(',', ':'))}"
        + (
            "\nGhi chú nguồn đã kiểm tra bằng hình: với asset openclipart-friendly-kitten-icon, "
            "hai nét đầu chạy từ đỉnh tai trái, qua viền trên đầu mèo rồi lên đỉnh tai phải; "
            "hãy gọi đúng đường viền đầu/tai, tuyệt đối không gọi là cổ, vai hoặc thân."
            if candidate.get("asset_id") == "openclipart-friendly-kitten-icon"
            else ""
        )
    )


def _svg_catalog_visual_review_prompt(
    data: dict[str, Any],
    candidate: dict[str, Any],
    segments: list[dict[str, Any]],
    draft_plan: dict[str, Any],
    *,
    first_step_segment_ids: list[str],
) -> str:
    atlas_mapping = [
        {
            "atlas_label": f"P{index:02d}",
            "segment_id": segment["path_id"],
            "source_path_id": segment["source_path_id"],
        }
        for index, segment in enumerate(segments, start=1)
    ]
    draft_stages = [
        {
            "step_index": stage["step_index"],
            "label_vi": stage["label_vi"],
            "instruction_vi": stage["instruction_vi"],
            "new_segment_ids": stage["path_ids"],
        }
        for stage in draft_plan["stages"]
    ]
    return (
        "Rà soát bản hướng dẫn theo ba hình đính kèm: ảnh màu cho biết con vật cuối; spatial atlas "
        "có một ô Pxx cho mỗi segment, trong đó toàn bộ hình nguồn hiện mờ xám đúng vị trí còn "
        "segment đó được tô xanh; contact sheet cho thấy hình tích lũy qua từng bước và ghi mã "
        "Pxx của các nét mới ngay trên từng ô. Hãy đối chiếu mã Pxx trên contact sheet với đúng "
        "ô atlas, rồi xem nét xanh nằm ở đâu trên con vật trước khi gọi tên bộ phận. Nếu chưa "
        "chắc bộ phận, mô tả hình dạng/vị trí nhìn thấy thay vì đoán. Trong contact sheet, nét "
        "xám đã có từ bước trước, nét xanh là nét mới của bước đang xét. Chuyển segment tới bước "
        "mà nó thực sự giúp tạo hình; sửa instruction_vi để nói đúng nét xanh vừa xuất hiện, "
        "tránh nói bộ phận chưa có hoặc đã vẽ xong. Có thể gom các nét liên quan đang bị đặt sai vào bước khác, "
        "nhưng mỗi segment phải giữ nguyên ID và xuất hiện đúng một lần. Không được sửa hình học. "
        "Giữ nguyên title_vi, số bước và hai segment mở đầu đã ghim. Bước 1 chỉ gồm đúng hai "
        "segment mở đầu; mọi segment còn lại ở bước 2 trở đi. Không để bước nào trống. Trả lại "
        "đầy đủ JSON theo schema, không thêm giải thích.\n"
        f"Chủ đề: {json.dumps(data['topic'], ensure_ascii=False)}\n"
        f"Nguồn: {candidate.get('asset_id', 'catalog-source')}\n"
        f"Tiêu đề phải giữ nguyên: {json.dumps(draft_plan['title_vi'], ensure_ascii=False)}\n"
        f"Segment mở đầu đã ghim: {json.dumps(first_step_segment_ids, ensure_ascii=False)}\n"
        f"Atlas mapping: {json.dumps(atlas_mapping, ensure_ascii=False, separators=(',', ':'))}\n"
        f"Bản nháp cần rà soát: {json.dumps(draft_stages, ensure_ascii=False, separators=(',', ':'))}"
    )


def _svg_catalog_source_plan_schema(
    paths: list[dict[str, Any]],
    *,
    first_step_segment_ids: list[str] | None = None,
) -> dict[str, Any]:
    path_ids = [path["path_id"] for path in paths]
    pinned_first_step = set(first_step_segment_ids or [])
    if first_step_segment_ids is not None:
        if (
            len(first_step_segment_ids) != 2
            or len(pinned_first_step) != 2
            or not pinned_first_step.issubset(set(path_ids))
        ):
            raise ValueError("SVG_SOURCE_FIRST_STEP_SEGMENT_IDS_INVALID")
        first_step_paths = [path for path in paths if path["path_id"] in pinned_first_step]
        if any(len(re.findall(r"[MLCQZ]", path["d"])) > 8 for path in first_step_paths):
            raise ValueError("SVG_SOURCE_FIRST_STEP_COMPLEXITY_INVALID")
        if (
            first_step_paths[0]["source_path_id"] != first_step_paths[1]["source_path_id"]
            or first_step_paths[0]["source_segment_end"] + 1
            != first_step_paths[1]["source_segment_start"]
            or first_step_paths[0]["source_subpath_indices"]
            != first_step_paths[1]["source_subpath_indices"]
        ):
            raise ValueError("SVG_SOURCE_FIRST_STEP_CONTINUITY_INVALID")
    stage = {
        "type": "object",
        "properties": {
            "label_vi": {"type": "string", "minLength": 1, "maxLength": 80},
            "instruction_vi": {"type": "string", "minLength": 1, "maxLength": 120},
        },
        "required": ["label_vi", "instruction_vi"],
        "additionalProperties": False,
    }
    path_stage_assignments = {
        "type": "object",
        "properties": {
            path_id: {
                "type": "integer",
                "enum": (
                    [1]
                    if path_id in pinned_first_step
                    else list(range(2, 9))
                    if first_step_segment_ids is not None
                    else list(range(1, 9))
                ),
            }
            for path_id in path_ids
        },
        "required": path_ids,
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "string", "enum": ["SvgOpenclipartSourceStrokePlanV3"]},
            "title_vi": {"type": "string", "minLength": 1, "maxLength": 120},
            "stages": {"type": "array", "minItems": 4, "maxItems": 8, "items": stage},
            "path_stage_assignments": path_stage_assignments,
        },
        "required": ["schema_version", "title_vi", "stages", "path_stage_assignments"],
        "additionalProperties": False,
    }


def _svg_catalog_visual_review_schema(
    paths: list[dict[str, Any]],
    *,
    first_step_segment_ids: list[str],
    title_vi: str,
    stage_count: int,
) -> dict[str, Any]:
    if not 4 <= stage_count <= 8 or not title_vi.strip():
        raise ValueError("SVG_CATALOG_VISUAL_REVIEW_DRAFT_INVALID")
    schema = _svg_catalog_source_plan_schema(
        paths,
        first_step_segment_ids=first_step_segment_ids,
    )
    schema["properties"]["title_vi"] = {"type": "string", "enum": [title_vi]}
    schema["properties"]["stages"]["minItems"] = stage_count
    schema["properties"]["stages"]["maxItems"] = stage_count
    assignments = schema["properties"]["path_stage_assignments"]["properties"]
    pinned = set(first_step_segment_ids)
    for path in paths:
        path_id = path["path_id"]
        assignments[path_id]["enum"] = (
            [1] if path_id in pinned else list(range(2, stage_count + 1))
        )
    return schema


def _parse_svg_catalog_visual_review_plan(
    text: str,
    paths: list[dict[str, Any]],
    *,
    first_step_segment_ids: list[str],
    draft_plan: dict[str, Any],
) -> dict[str, Any]:
    reviewed = _parse_svg_catalog_source_plan(
        text,
        paths,
        first_step_segment_ids=first_step_segment_ids,
    )
    if (
        reviewed["title_vi"] != draft_plan["title_vi"]
        or len(reviewed["stages"]) != len(draft_plan["stages"])
    ):
        raise _SvgCatalogPlanValidationError(
            "SVG_CATALOG_VISUAL_REVIEW_SCOPE_INVALID",
            {
                "draft_stage_count": len(draft_plan["stages"]),
                "review_stage_count": len(reviewed["stages"]),
            },
        )
    return reviewed


class _DuplicateJsonObjectKey(ValueError):
    def __init__(self, duplicate_count: int) -> None:
        super().__init__("duplicate JSON object key")
        self.duplicate_count = duplicate_count


class _SvgCatalogPlanValidationError(RuntimeError):
    def __init__(self, error_code: str, safe_diagnostics: dict[str, int | str | None]) -> None:
        super().__init__(error_code)
        self.error_code = error_code
        self.safe_diagnostics = safe_diagnostics


def _json_object_reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    duplicate_count = 0
    for key, item in pairs:
        if key in value:
            duplicate_count += 1
        else:
            value[key] = item
    if duplicate_count:
        raise _DuplicateJsonObjectKey(duplicate_count)
    return value


def _parse_svg_catalog_source_plan(
    text: str,
    paths: list[dict[str, Any]],
    *,
    first_step_segment_ids: list[str] | None = None,
) -> dict[str, Any]:
    allowed = {path["path_id"] for path in paths}
    empty_diagnostics: dict[str, int | str | None] = {
        "expected_path_count": len(allowed),
        "assigned_path_count": 0,
        "unique_path_count": 0,
        "missing_path_count": len(allowed),
        "unknown_path_count": 0,
        "duplicate_object_key_count": 0,
        "out_of_range_stage_count": 0,
        "empty_stage_count": 0,
    }
    try:
        value = json.loads(text, object_pairs_hook=_json_object_reject_duplicate_keys)
    except _DuplicateJsonObjectKey as exc:
        diagnostics = dict(empty_diagnostics)
        diagnostics["duplicate_object_key_count"] = exc.duplicate_count
        diagnostics["assigned_path_count"] = None
        diagnostics["unique_path_count"] = None
        diagnostics["missing_path_count"] = None
        raise _SvgCatalogPlanValidationError(
            "SVG_CATALOG_STROKE_PLAN_DUPLICATE_JSON_KEY", diagnostics
        ) from exc
    except json.JSONDecodeError as exc:
        raise _SvgCatalogPlanValidationError(
            "SVG_CATALOG_STROKE_PLAN_JSON_INVALID", empty_diagnostics
        ) from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "title_vi", "stages", "path_stage_assignments"}
        or value.get("schema_version") != "SvgOpenclipartSourceStrokePlanV3"
        or not isinstance(value.get("title_vi"), str)
        or not value["title_vi"].strip()
        or len(value["title_vi"]) > 120
        or not isinstance(value.get("stages"), list)
        or not 4 <= len(value["stages"]) <= 8
    ):
        raise _SvgCatalogPlanValidationError(
            "SVG_CATALOG_STROKE_PLAN_SCHEMA_INVALID", empty_diagnostics
        )

    assignments = value.get("path_stage_assignments")
    assignment_keys = set(assignments) if isinstance(assignments, dict) else set()
    missing_path_count = len(allowed - assignment_keys)
    unknown_path_count = len(assignment_keys - allowed)
    assigned_path_count = len(assignments) if isinstance(assignments, dict) else 0
    out_of_range_stage_count = 0
    if isinstance(assignments, dict):
        out_of_range_stage_count = sum(
            isinstance(stage_index, bool)
            or not isinstance(stage_index, int)
            or not 1 <= stage_index <= len(value["stages"])
            for stage_index in assignments.values()
        )
    stage_counts = {index: 0 for index in range(1, len(value["stages"]) + 1)}
    if isinstance(assignments, dict):
        for stage_index in assignments.values():
            if (
                isinstance(stage_index, int)
                and not isinstance(stage_index, bool)
                and stage_index in stage_counts
            ):
                stage_counts[stage_index] += 1
    diagnostics: dict[str, int | str | None] = {
        "expected_path_count": len(allowed),
        "assigned_path_count": assigned_path_count,
        "unique_path_count": len(assignment_keys),
        "missing_path_count": missing_path_count,
        "unknown_path_count": unknown_path_count,
        "duplicate_object_key_count": 0,
        "out_of_range_stage_count": out_of_range_stage_count,
        "empty_stage_count": sum(count == 0 for count in stage_counts.values()),
    }
    if (
        not isinstance(assignments, dict)
        or assignment_keys != allowed
        or out_of_range_stage_count
    ):
        raise _SvgCatalogPlanValidationError(
            "SVG_CATALOG_STROKE_PLAN_PATH_ASSIGNMENT_INVALID", diagnostics
        )
    if first_step_segment_ids is not None:
        expected_first_step = set(first_step_segment_ids)
        actual_first_step = {
            path_id for path_id, stage_index in assignments.items() if stage_index == 1
        }
        if actual_first_step != expected_first_step:
            diagnostics["expected_first_step_segment_count"] = len(expected_first_step)
            diagnostics["actual_first_step_segment_count"] = len(actual_first_step)
            raise _SvgCatalogPlanValidationError(
                "SVG_CATALOG_STROKE_PLAN_FIRST_STEP_ASSIGNMENT_INVALID", diagnostics
            )

    checked_stage_metadata: list[dict[str, Any]] = []
    for index, stage in enumerate(value["stages"], start=1):
        stage_failures: list[str] = []
        if not isinstance(stage, dict):
            stage_failures.append("stage_not_object")
        else:
            if set(stage) != {"label_vi", "instruction_vi"}:
                stage_failures.append("stage_fields_invalid")
            if not isinstance(stage.get("label_vi"), str):
                stage_failures.append("label_type_invalid")
                label_length = 0
            else:
                label_length = len(stage["label_vi"].strip())
                if not 1 <= label_length <= 80:
                    stage_failures.append("label_length_invalid")
            if not isinstance(stage.get("instruction_vi"), str):
                stage_failures.append("instruction_type_invalid")
                instruction_length = 0
            else:
                instruction_length = len(stage["instruction_vi"].strip())
                if not 1 <= instruction_length <= 120:
                    stage_failures.append("instruction_length_invalid")
        if stage_failures:
            diagnostics["stage_array_index"] = index
            diagnostics["stage_failure"] = ",".join(stage_failures)
            diagnostics["stage_label_length"] = label_length if isinstance(stage, dict) else 0
            diagnostics["stage_instruction_length"] = (
                instruction_length if isinstance(stage, dict) else 0
            )
            raise _SvgCatalogPlanValidationError(
                "SVG_CATALOG_STROKE_PLAN_STAGE_INVALID", diagnostics
            )
        checked_stage_metadata.append(
            {
                "step_index": index,
                "label_vi": stage["label_vi"].strip(),
                "instruction_vi": stage["instruction_vi"].strip(),
            }
        )
    if diagnostics["empty_stage_count"]:
        raise _SvgCatalogPlanValidationError(
            "SVG_CATALOG_STROKE_PLAN_EMPTY_STAGE", diagnostics
        )
    stage_paths: dict[int, list[str]] = {index: [] for index in stage_counts}
    for path in paths:
        stage_paths[assignments[path["path_id"]]].append(path["path_id"])
    checked_stages = [
        {**stage, "path_ids": stage_paths[stage["step_index"]]}
        for stage in checked_stage_metadata
    ]
    return {"title_vi": value["title_vi"].strip(), "stages": checked_stages}


def _build_openclipart_source_guide(
    candidate: dict[str, Any], plan: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = candidate["parsed_svg"]["paths"]
    view_box = candidate["parsed_svg"]["view_box"]
    line_width = max(1.5, min(7.0, _catalog_viewbox_scale(view_box) * 0.008))
    guide_paths = [
        {
            "path_id": path["path_id"],
            "d": path["d"],
            "fill": "none",
            "stroke": "#20293b",
            "stroke_width": line_width,
        }
        for path in paths
    ]
    reference = _build_openclipart_reference_illustration(candidate)
    parts: list[dict[str, Any]] = []
    stages: list[dict[str, Any]] = []
    previous_part: str | None = None
    for item in plan["stages"]:
        part_id = f"source_stage_{item['step_index']:02d}"
        ids = item["path_ids"]
        parts.append(
            {
                "part_id": part_id,
                "label_vi": item["label_vi"],
                "path_ids": ids,
                "depends_on": [previous_part] if previous_part else [],
            }
        )
        stages.append(
            {
                "step_index": item["step_index"],
                "instruction_vi": item["instruction_vi"],
                "part_ids": [part_id],
                "new_path_ids": ids,
                "animation_order": ids,
            }
        )
        previous_part = part_id
    result = {
        "schema_version": "SvgTopicStrokeGuideContentV1",
        "title_vi": plan["title_vi"],
        "document": {
            "schema_version": "SvgDocumentV1",
            "view_box": view_box,
            "paths": guide_paths,
        },
        "parts": parts,
        "stages": stages,
    }
    return result, reference


def _build_openclipart_segment_guide(
    candidate: dict[str, Any],
    segments: list[dict[str, Any]],
    plan: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    segment_by_id = {segment["path_id"]: segment for segment in segments}
    stage_by_segment_id = {
        segment_id: stage["step_index"]
        for stage in plan["stages"]
        for segment_id in stage["path_ids"]
    }
    if set(segment_by_id) != set(stage_by_segment_id):
        raise _SvgCatalogPlanValidationError(
            "SVG_SOURCE_SEGMENT_STAGE_COVERAGE_INVALID",
            {
                "segment_count": len(segment_by_id),
                "assigned_segment_count": len(stage_by_segment_id),
                "unassigned_segment_count": len(set(segment_by_id) - set(stage_by_segment_id)),
            },
        )

    strokes: list[dict[str, Any]] = []
    guide_path_by_segment: dict[str, str] = {}
    stage_counts: dict[int, int] = {}
    final_step = len(plan["stages"])
    for index, segment in enumerate(segments, start=1):
        step_index = stage_by_segment_id[segment["path_id"]]
        stage_counts[step_index] = stage_counts.get(step_index, 0) + 1
        path_id = f"guide_stroke_{index:02d}"
        guide_path_by_segment[segment["path_id"]] = path_id
        role = "construction" if step_index == 1 else "feature" if step_index == final_step else "outline"
        stage_label = plan["stages"][step_index - 1]["label_vi"]
        strokes.append(
            {
                "path_id": path_id,
                "d": segment["d"],
                "role": role,
                "feature_vi": f"{stage_label} — nét {stage_counts[step_index]}",
                "source_path_ids": [segment["source_path_id"]],
            }
        )

    stages = [
        {
            "step_index": item["step_index"],
            "label_vi": item["label_vi"],
            "instruction_vi": _openclipart_segment_instruction(candidate, item),
            "stroke_ids": [guide_path_by_segment[segment_id] for segment_id in item["path_ids"]],
        }
        for item in plan["stages"]
    ]
    raw_content = {
        "schema_version": "SvgTopicStrokeGuideConstructionContentV1",
        "title_vi": plan["title_vi"],
        "strokes": strokes,
        "stages": stages,
    }
    validated = _parse_svg_catalog_construction_guide(
        json.dumps(raw_content, ensure_ascii=False, separators=(",", ":")),
        candidate["parsed_svg"]["paths"],
    )
    return validated, _build_openclipart_reference_illustration(candidate)


def _openclipart_segment_instruction(
    candidate: dict[str, Any], stage: dict[str, Any]
) -> str:
    """Use inspected copy for the known CC0 kitten starter contour; keep Qwen copy elsewhere."""

    if (
        candidate.get("asset_id") == "openclipart-friendly-kitten-icon"
        and stage.get("step_index") == 1
    ):
        return (
            "Vẽ hai nét cong trên đỉnh đầu, nối vùng giữa hai tai."
        )
    return stage["instruction_vi"]


def _curated_openclipart_source_plan(
    candidate: dict[str, Any],
    segments: list[dict[str, Any]],
    *,
    first_step_segment_ids: list[str],
) -> dict[str, Any] | None:
    """Return the reviewed sequence only for the immutable kitten catalog source."""

    if (
        candidate.get("asset_id") != "openclipart-friendly-kitten-icon"
        or candidate.get("source_sha256")
        != "a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594"
    ):
        return None

    expected_ids = [f"source_segment_{index:03d}" for index in range(1, 21)]
    actual_ids = [segment.get("path_id") for segment in segments]
    if actual_ids != expected_ids:
        return None

    stage_specs = [
        (
            "Đỉnh đầu",
            "Vẽ hai nét cong trên đỉnh đầu, nối vùng giữa hai tai.",
            (5, 6),
        ),
        (
            "Viền khuôn mặt",
            "Nối hai đầu nét xuống hai má rồi khép viền khuôn mặt.",
            (1, 2, 3, 4),
        ),
        (
            "Tai, mắt và miệng",
            "Thêm hai tai nhọn, đôi mắt tròn và miệng nhỏ ở giữa.",
            (7, 8, 9, 18),
        ),
        (
            "Nét trong tai và đôi mắt",
            "Thêm nét bên trong hai tai và hoàn thiện cả hai mắt cùng lúc nhé.",
            (10, 11, 12, 13, 14, 15),
        ),
        (
            "Đuôi cong",
            "Vẽ chiếc đuôi cong ở bên phải đầu mèo.",
            (16, 17),
        ),
        (
            "Hai bàn chân",
            "Thêm hai bàn chân nhỏ bên dưới để hoàn thiện mèo con.",
            (19, 20),
        ),
    ]
    assignments: dict[str, int] = {}
    stages: list[dict[str, str]] = []
    for stage_index, (label, instruction, segment_numbers) in enumerate(stage_specs, start=1):
        stages.append({"label_vi": label, "instruction_vi": instruction})
        for segment_number in segment_numbers:
            assignments[expected_ids[segment_number - 1]] = stage_index

    curated_payload = {
        "schema_version": "SvgOpenclipartSourceStrokePlanV3",
        "title_vi": "Cùng vẽ mèo con",
        "stages": stages,
        "path_stage_assignments": assignments,
    }
    return _parse_svg_catalog_source_plan(
        json.dumps(curated_payload, ensure_ascii=False, separators=(",", ":")),
        segments,
        first_step_segment_ids=first_step_segment_ids,
    )


def _build_openclipart_segment_guide_from_plan_text(
    text: str,
    candidate: dict[str, Any],
    segments: list[dict[str, Any]],
    *,
    first_step_segment_ids: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse Qwen's segment assignment contract, then render only source geometry."""

    plan = _parse_svg_catalog_source_plan(
        text,
        segments,
        first_step_segment_ids=first_step_segment_ids,
    )
    return _build_openclipart_segment_guide(candidate, segments, plan)


def _build_openclipart_reference_illustration(
    candidate: dict[str, Any],
) -> dict[str, Any]:
    paths = candidate["parsed_svg"]["paths"]
    return {
        "schema_version": "SvgReferenceIllustrationV1",
        "view_box": candidate["parsed_svg"]["view_box"],
        "paths": [
            {
                "path_id": path["path_id"],
                "d": path["d"],
                "fill": _catalog_color(path["fill"]),
                "stroke": _catalog_color(path["stroke"]),
                "stroke_width": path["stroke_width"],
                "stroke_linecap": path["stroke_linecap"],
                "stroke_linejoin": path["stroke_linejoin"],
                "stroke_miterlimit": 4,
            }
            for path in paths
        ],
    }


def _catalog_color(value: str) -> str:
    if value == "none":
        return "none"
    from PIL import ImageColor

    red, green, blue = ImageColor.getrgb(value)[:3]
    return f"#{red:02x}{green:02x}{blue:02x}"


def _catalog_viewbox_scale(view_box: str) -> float:
    numbers = [float(value) for value in view_box.split()]
    return min(numbers[2], numbers[3])


def _validate_svg_topic_guide_input(data: Any) -> None:
    if (
        not isinstance(data, dict)
        or set(data) != {"schema_version", "topic", "difficulty"}
        or data.get("schema_version") != "sketch2life.svg-topic-stroke-guide-input.v1"
        or not isinstance(data.get("topic"), str)
        or not 2 <= len(data["topic"].strip()) <= 120
        or data.get("difficulty") not in {"beginner", "simple"}
    ):
        raise WorkerContractError("SVG_TOPIC_GUIDE_INPUT_INVALID")


def _svg_topic_guide_prompt(
    data: dict[str, Any], *, reference_source: dict[str, str] | None = None
) -> str:
    topic = data["topic"].strip()
    folded = unicodedata.normalize("NFKD", topic.casefold())
    normalized = "".join(char for char in folded if not unicodedata.combining(char))
    deer = any(term in normalized for term in ("huou", "nai", "deer", "fawn", "stag", "elk"))
    deer_brief = ""
    chicken_brief = ""
    if deer:
        deer_brief = (
            "\nBẮT BUỘC NHẬN DIỆN ĐƯỢC CON HƯƠU: vẽ nghiêng mặt sang phải; thân nằm ngang "
            "chiếm khoảng giữa hình; cổ nối từ vai thân lên đầu; đầu có mõm, tai; bốn chân "
            "đi từ thân xuống cùng mặt đất. Hai gạc mọc trên đầu, mỗi bên có một thân gạc và "
            "ít nhất hai nhánh thật. Dùng đúng các part_id: body, neck, head, front_left_leg, "
            "front_right_leg, rear_left_leg, rear_right_leg, left_antler, right_antler. Dùng "
            "đúng path_id deer_body, deer_neck, deer_head, deer_front_left_leg, "
            "deer_front_right_leg, deer_rear_left_leg, deer_rear_right_leg; path gạc trái là "
            "deer_antler_left_beam cùng deer_antler_left_branch_1 và branch_2 trở lên; gạc "
            "phải tương tự với deer_antler_right_*. Mỗi path nhánh gạc chỉ là M/L và một đầu "
            "phải chạm vào đường thân gạc. Path thân gạc là đường gấp khúc M/L, bắt đầu sát "
            "đỉnh đầu. Mỗi chân là một nét nối thân tới gần đáy khung. Không thay gạc bằng tai "
            "thỏ, không thêm nền, cỏ, chữ hoặc đồ trang trí."
        )
    if reference_source is not None:
        chicken_brief = (
            "\nẢnh đính kèm là tham chiếu thị giác đã duyệt cho chủ đề gà. Quan sát hướng đầu, "
            "dáng thân, cổ, cánh, đuôi, mào, mỏ và chân; hãy tạo line-art mới dựa trên cấu trúc "
            "đó, không chép SVG/path, màu tô hay chi tiết trang trí của ảnh. Bắt buộc dùng đúng "
            "9 cặp part_id/path_id: body/chicken_body, neck/chicken_neck, head/chicken_head, "
            "beak/chicken_beak, comb/chicken_comb, wing/chicken_wing, tail/chicken_tail, "
            "left_leg/chicken_left_leg, right_leg/chicken_right_leg. Thân nằm ngang, lớn và là "
            "khối chính; trong viewBox 512×512, riêng chicken_body phải có hộp bao control-point "
            "rộng ít nhất 200 và cao ít nhất 90 đơn vị (mục tiêu x khoảng 125–390, y khoảng "
            "175–295); thể hiện rõ cả lưng phía trên lẫn bụng phía dưới ngay trong path thân, "
            "không vẽ thân thành một nét ngang mỏng. Giữ tỉ lệ rộng/cao lớn hơn 1.2 và d ngắn "
            "hơn 256 ký tự. Cổ nối thân lên đầu; mỏ nối ở phía trước đầu; mào ở trên đầu; cánh nằm trong "
            "đường bao thân; đuôi nối từ phía sau thân. chicken_beak bắt đầu rõ bên trong vùng "
            "đầu và kéo ra thành mỏ dài ít nhất 24 đơn vị viewBox. Hai chân tách nhau, bắt đầu "
            "ở phần dưới của thân, mỗi chân đi xuống ít nhất 100 đơn vị và kết thúc khoảng y=420–480; "
            "hai bàn chân cùng gần một đường đất. Các phụ thuộc: neck→body, head→neck, beak→head, comb→head, "
            "wing→body, tail→body, left_leg→body, right_leg→body. Mỗi part là một nét mở liên "
            "tục có ý nghĩa; không dùng Z để khép kín path, không dùng hình tròn/oval, chữ nhật "
            "hay tam giác làm vật thay thế cho bộ phận. Dùng ít nhất 5 bước nếu cần để giữ thứ tự "
            "dễ vẽ; mỗi bước chỉ thêm một vài nét có ý nghĩa. ĐIỂM NỐI BẮT BUỘC: chicken_neck "
            "bắt đầu trong vùng thân và kết thúc trong vùng đầu; một đầu chicken_wing phải nằm "
            "trong vùng thân; một đầu chicken_tail phải chạm vùng phía sau thân; một đầu "
            "chicken_comb phải nằm trong vùng đầu; điểm đầu chicken_beak phải nằm trong vùng đầu "
            "và điểm cuối mỏ phải cách điểm đầu ít nhất 24 đơn vị để nét mỏ nhìn rõ. "
            "Các đầu mút phải chạm hoặc giao nhẹ với đường bao của bộ phận đích, không để khe hở "
            "và không dừng gần bên cạnh. Chọn tọa độ đầu mút nằm rõ bên trong vùng nối; không tạo "
            "nét nối rời để giả mối nối. Mỗi path d phải có geometry riêng, phù hợp với đúng bộ "
            "phận; tuyệt đối không dùng lại cùng chuỗi d hoặc sao chép hình học giữa hai path. "
            "Path ví dụ phía trên chỉ minh họa cú pháp, không được sao chép hoặc dùng lại cho "
            "bất kỳ bộ phận nào."
        )
    example_path_id = "deer_body" if deer else "chicken_body" if reference_source is not None else "subject_body"
    path_example = json.dumps(
        {
            "path_id": example_path_id,
            "d": "M 72 210 C 130 168 202 168 270 210",
            "fill": "none",
            "stroke": "#202938",
            "stroke_width": 4,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (
        "Tạo hướng dẫn vẽ theo từng nét cho chủ đề sau. Đây là hình line-art để trẻ chép lên "
        "giấy, không phải ảnh minh họa tô màu. Dùng một chủ thể lớn, căn giữa, dễ đọc khi "
        "phóng to. Mỗi path là nét vẽ riêng có ý nghĩa, không chia một đường thành nhiều "
        "path vụn. Tất cả fill phải là none, stroke chính xác là #202938, stroke_width là số "
        "từ 3 đến 7. Dùng 8–28 path có bộ phận semantic; path_id chỉ dùng chữ thường ASCII, "
        "số và dấu gạch dưới; d chỉ dùng M/L/C/Q/Z viết hoa, số, dấu phẩy và khoảng trắng; "
        "mỗi d tối đa 256 ký tự; tọa độ từ 20 đến 492. Ví dụ cú pháp path hợp lệ "
        "(path_id thực tế phải theo đúng bộ phận): "
        f"{path_example}. "
        "Bước 1 chỉ có hình khung lớn; các bước tiếp theo thêm bộ phận theo thứ tự dễ dạy; "
        "bước cuối hoàn thiện chủ thể bằng vài chi tiết nhận dạng, không thêm họa tiết vụn. "
        "Mỗi path xuất hiện đúng một lần trong new_path_ids và animation_order. Path của một "
        "bộ phận chỉ được thêm khi các part_id phụ thuộc đã xuất hiện ở bước trước hoặc cùng "
        "bước. Chọn 4–8 bước tùy độ phức tạp. Hướng dẫn mỗi bước là một câu ngắn cho trẻ. "
        "Không đưa giải thích ngoài JSON.\n"
        f"Chủ đề: {json.dumps(topic, ensure_ascii=False)}. "
        f"Độ khó: {data['difficulty']}.\n"
        "JSON top-level có đúng các key schema_version, title_vi, document, parts, stages. "
        "Mỗi path có đúng path_id, d, fill, stroke, stroke_width. Mỗi part có đúng part_id, "
        "label_vi, path_ids, depends_on. Mỗi stage có đúng step_index, instruction_vi, "
        "part_ids, new_path_ids, animation_order. Ví dụ path hợp lệ: "
        f"{path_example}. Tên key và kiểu dữ liệu phải khớp tuyệt đối."
        f"{deer_brief}{chicken_brief}"
    )


def _svg_topic_guide_json_schema(*, chicken_reference: bool = False) -> dict[str, Any]:
    path_data_schema = (
        {
            "type": "string",
            "pattern": r"^[MLCQ0-9+.,\-eE\s]{1,256}$",
        }
        if chicken_reference
        else {
            "type": "string",
            "minLength": 1,
            "maxLength": 256,
        }
    )
    path_fields = {
        "path_id": {
            "type": "string",
            "pattern": r"^[a-z][a-z0-9_]{0,95}$",
        },
        "d": path_data_schema,
        "fill": {"type": "string", "enum": ["none"]},
        "stroke": {"type": "string", "enum": ["#202938"]},
        "stroke_width": {"type": "number", "minimum": 3, "maximum": 7},
    }
    part_fields = {
        "part_id": {"type": "string", "minLength": 1, "maxLength": 48},
        "label_vi": {"type": "string", "minLength": 1, "maxLength": 300},
        "path_ids": {"type": "array", "minItems": 1, "maxItems": 28, "items": {"type": "string"}},
        "depends_on": {"type": "array", "maxItems": 32, "items": {"type": "string"}},
    }
    stage_fields = {
        "step_index": {"type": "integer", "minimum": 1, "maximum": 8},
        "instruction_vi": {"type": "string", "minLength": 1, "maxLength": 120},
        "part_ids": {"type": "array", "minItems": 1, "maxItems": 28, "items": {"type": "string"}},
        "new_path_ids": {"type": "array", "minItems": 1, "maxItems": 28, "items": {"type": "string"}},
        "animation_order": {"type": "array", "minItems": 1, "maxItems": 28, "items": {"type": "string"}},
    }
    path_object = {"type": "object", "properties": path_fields, "required": list(path_fields), "additionalProperties": False}
    part_object = {"type": "object", "properties": part_fields, "required": list(part_fields), "additionalProperties": False}
    stage_object = {"type": "object", "properties": stage_fields, "required": list(stage_fields), "additionalProperties": False}
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "string", "enum": ["SvgTopicStrokeGuideContentV1"]},
            "title_vi": {"type": "string", "minLength": 1, "maxLength": 120},
            "document": {
                "type": "object",
                "properties": {
                    "schema_version": {"type": "string", "enum": ["SvgDocumentV1"]},
                    "view_box": {"type": "string", "enum": ["0 0 512 512"]},
                    "paths": {"type": "array", "minItems": 8, "maxItems": 28, "items": path_object},
                },
                "required": ["schema_version", "view_box", "paths"],
                "additionalProperties": False,
            },
            "parts": {"type": "array", "minItems": 1, "maxItems": 28, "items": part_object},
            "stages": {"type": "array", "minItems": 4, "maxItems": 8, "items": stage_object},
        },
        "required": ["schema_version", "title_vi", "document", "parts", "stages"],
        "additionalProperties": False,
    }


def _svg_topic_guide_generation_is_complete(
    *,
    output_token_count: int,
    max_new_tokens: int,
    final_token_id: int | None,
    eos_token_ids: int | list[int] | None,
) -> bool:
    if isinstance(eos_token_ids, int):
        eos_values = [eos_token_ids]
    else:
        eos_values = eos_token_ids or []
    return output_token_count < max_new_tokens and final_token_id in eos_values


def _svg_topic_guide_diagnostic_payload(
    *,
    reason_code: str,
    output_token_count: int,
    input_token_count: int,
    max_new_tokens: int,
    final_token_id: int | None,
    eos_token_ids: int | list[int] | None,
    tokenizer_eos_token_id: int | None,
    decoded_character_count: int,
    generation_seconds: float,
    parse_error: BaseException | None = None,
) -> dict[str, Any]:
    """Build a safe worker diagnostic without retaining model output or input."""

    if isinstance(eos_token_ids, int):
        eos_values = [eos_token_ids]
    else:
        eos_values = eos_token_ids or []
    payload: dict[str, Any] = {
        "workload": "svg.topic-stroke-guide.generate",
        "reason_code": reason_code,
        "generation_seconds": generation_seconds,
        "input_token_count": input_token_count,
        "output_token_count": output_token_count,
        "max_new_tokens": max_new_tokens,
        "final_token_id": final_token_id,
        "tokenizer_eos_token_id": tokenizer_eos_token_id,
        "model_eos_token_id": eos_values[0] if len(eos_values) == 1 else None,
        "token_limit_reached": output_token_count >= max_new_tokens,
        "ended_with_model_eos": final_token_id in eos_values,
        "decoded_character_count": decoded_character_count,
    }
    if isinstance(parse_error, json.JSONDecodeError):
        payload["json_error_type"] = "JSONDecodeError"
        payload["json_error_category"] = _json_error_category(parse_error)
        payload["json_error_position"] = parse_error.pos
        payload["json_error_line"] = parse_error.lineno
        payload["json_error_column"] = parse_error.colno
    return payload


def _parse_svg_topic_stroke_guide(text: str) -> dict[str, Any]:
    try:
        result = json.loads(text, object_pairs_hook=_reject_duplicate_story_keys)
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("SVG_TOPIC_GUIDE_JSON_INVALID") from exc
    if (
        not isinstance(result, dict)
        or set(result) != {"schema_version", "title_vi", "document", "parts", "stages"}
        or result.get("schema_version") != "SvgTopicStrokeGuideContentV1"
        or not isinstance(result.get("title_vi"), str)
        or not 1 <= len(result["title_vi"].strip()) <= 120
    ):
        raise RuntimeError("SVG_TOPIC_GUIDE_JSON_INVALID")
    document = result.get("document")
    if (
        not isinstance(document, dict)
        or set(document) != {"schema_version", "view_box", "paths"}
        or document.get("schema_version") != "SvgDocumentV1"
        or document.get("view_box") != "0 0 512 512"
        or not isinstance(document.get("paths"), list)
        or not 8 <= len(document["paths"]) <= 64
    ):
        raise RuntimeError("SVG_TOPIC_GUIDE_DOCUMENT_INVALID")
    path_ids: set[str] = set()
    path_data: set[str] = set()
    paths: list[dict[str, Any]] = []
    reference_color: str | None = None
    for path in document["paths"]:
        if not isinstance(path, dict) or set(path) != {"path_id", "d", "fill", "stroke", "stroke_width"}:
            raise RuntimeError("SVG_TOPIC_GUIDE_PATH_FIELDS_INVALID")
        path_id, data, fill, stroke, width = (
            path.get("path_id"), path.get("d"), path.get("fill"), path.get("stroke"), path.get("stroke_width")
        )
        if not isinstance(path_id, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,95}", path_id) is None:
            raise RuntimeError("SVG_TOPIC_GUIDE_PATH_ID_INVALID")
        if path_id in path_ids:
            raise RuntimeError("SVG_TOPIC_GUIDE_PATH_ID_DUPLICATE")
        if (
            not isinstance(data, str)
            or not 1 <= len(data.strip()) <= 4096
            or re.fullmatch(r"[MLCQZ0-9+.,\-eE\s]+", data) is None
        ):
            raise RuntimeError("SVG_TOPIC_GUIDE_PATH_DATA_INVALID")
        if fill != "none":
            raise RuntimeError("SVG_TOPIC_GUIDE_PATH_FILL_INVALID")
        if not isinstance(stroke, str) or re.fullmatch(r"#[0-9a-fA-F]{6}", stroke) is None:
            raise RuntimeError("SVG_TOPIC_GUIDE_PATH_STROKE_INVALID")
        if reference_color is not None and reference_color.casefold() != stroke.casefold():
            raise RuntimeError("SVG_TOPIC_GUIDE_PATH_COLOR_INCONSISTENT")
        if isinstance(width, bool) or not isinstance(width, (int, float)) or not 1.5 <= width <= 10:
            raise RuntimeError("SVG_TOPIC_GUIDE_PATH_WIDTH_INVALID")
        if data.strip() in path_data:
            raise RuntimeError("SVG_TOPIC_GUIDE_PATH_DUPLICATE_GEOMETRY")
        reference_color = stroke
        path_ids.add(path_id)
        path_data.add(data.strip())
        paths.append({"path_id": path_id, "d": data.strip(), "fill": "none", "stroke": stroke, "stroke_width": float(width)})
    if not isinstance(result.get("parts"), list) or not isinstance(result.get("stages"), list):
        raise RuntimeError("SVG_TOPIC_GUIDE_STEPS_INVALID")
    part_ids: set[str] = set()
    part_path_owner: dict[str, str] = {}
    for part in result["parts"]:
        if not isinstance(part, dict) or set(part) != {"part_id", "label_vi", "path_ids", "depends_on"}:
            raise RuntimeError("SVG_TOPIC_GUIDE_PART_INVALID")
        part_id, label, assigned, dependencies = (part.get("part_id"), part.get("label_vi"), part.get("path_ids"), part.get("depends_on"))
        if (
            not isinstance(part_id, str)
            or re.fullmatch(r"[a-z][a-z0-9_]{0,47}", part_id) is None
            or part_id in part_ids
            or not isinstance(label, str)
            or not 1 <= len(label.strip()) <= 300
            or not isinstance(assigned, list)
            or not assigned
            or not isinstance(dependencies, list)
            or any(not isinstance(path_id, str) or path_id not in path_ids or path_id in part_path_owner for path_id in assigned)
            or any(not isinstance(dep, str) for dep in dependencies)
        ):
            raise RuntimeError("SVG_TOPIC_GUIDE_PART_INVALID")
        part_ids.add(part_id)
        for path_id in assigned:
            part_path_owner[path_id] = part_id
    if set(part_path_owner) != path_ids or len(result["stages"]) not in range(4, 9):
        raise RuntimeError("SVG_TOPIC_GUIDE_PATH_COVERAGE_INVALID")
    staged_paths: set[str] = set()
    for expected_index, stage in enumerate(result["stages"], start=1):
        if not isinstance(stage, dict) or set(stage) != {"step_index", "instruction_vi", "part_ids", "new_path_ids", "animation_order"}:
            raise RuntimeError("SVG_TOPIC_GUIDE_STAGE_INVALID")
        if (
            stage.get("step_index") != expected_index
            or not isinstance(stage.get("instruction_vi"), str)
            or not 1 <= len(stage["instruction_vi"].strip()) <= 120
            or not isinstance(stage.get("part_ids"), list)
            or not stage["part_ids"]
            or not set(stage["part_ids"]).issubset(part_ids)
            or not isinstance(stage.get("new_path_ids"), list)
            or not stage["new_path_ids"]
            or stage.get("animation_order") != stage.get("new_path_ids")
            or not set(stage["new_path_ids"]).issubset(path_ids)
            or staged_paths.intersection(stage["new_path_ids"])
            or any(part_path_owner.get(path_id) not in stage["part_ids"] for path_id in stage["new_path_ids"])
        ):
            raise RuntimeError("SVG_TOPIC_GUIDE_STAGE_INVALID")
        staged_paths.update(stage["new_path_ids"])
    if staged_paths != path_ids:
        raise RuntimeError("SVG_TOPIC_GUIDE_PATH_COVERAGE_INVALID")
    return {
        "schema_version": "SvgTopicStrokeGuideContentV1",
        "title_vi": result["title_vi"].strip(),
        "document": {"schema_version": "SvgDocumentV1", "view_box": "0 0 512 512", "paths": paths},
        "parts": result["parts"],
        "stages": result["stages"],
    }


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

_SVG_TOPIC_GUIDE_JSON_STRING_FIELDS = frozenset(
    {
        "schema_version",
        "title_vi",
        "view_box",
        "path_id",
        "d",
        "fill",
        "stroke",
        "part_id",
        "label_vi",
        "instruction_vi",
    }
)


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
                "json_error_category": _json_error_category(exc),
                "json_error_position": exc.pos,
            }
        )
        active_value = re.search(
            r'"(?P<key>[^"\\]+)"\s*:\s*"(?P<value>(?:\\.|[^"\\])*)$',
            text.rstrip(),
            flags=re.DOTALL,
        )
        if active_value is not None:
            summary["active_json_string_field"] = active_value.group("key")
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


def _json_error_category(error: json.JSONDecodeError) -> str:
    """Map parser messages to fixed labels without exposing source snippets."""

    message = error.msg.casefold()
    categories = (
        ("unterminated string", "UNTERMINATED_STRING"),
        ("invalid \\escape", "INVALID_ESCAPE"),
        ("invalid control character", "INVALID_CONTROL_CHARACTER"),
        ("expecting property name", "EXPECTING_PROPERTY_NAME"),
        ("expecting ':' delimiter", "EXPECTING_COLON"),
        ("expecting ',' delimiter", "EXPECTING_COMMA_OR_END"),
        ("expecting value", "EXPECTING_VALUE"),
        ("extra data", "EXTRA_DATA"),
    )
    for fragment, category in categories:
        if fragment in message:
            return category
    return "JSON_ERROR_OTHER"


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
        parser_can_end = (
            bool(can_end()) if callable(can_end) else False
        )
        diagnostics["last_parser_can_end"] = parser_can_end
        eos_ids = _normalize_token_ids(effective_eos_token_id)
        values = _allowed_json_tokens(
            values,
            eos_token_ids=eos_ids,
            parser_can_end=parser_can_end,
        )
        diagnostics["last_model_eos_allowed"] = any(
            token_id in values
            for token_id in eos_ids
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


def _allowed_json_tokens(
    allowed_tokens: Any,
    *,
    eos_token_ids: list[int],
    parser_can_end: bool,
) -> list[int]:
    """Stop at the first complete schema-valid JSON document."""

    if parser_can_end and eos_token_ids:
        return list(eos_token_ids)
    return list(allowed_tokens)


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
                "json_error_type",
                "json_error_category",
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


def _safe_svg_topic_guide_decoder_diagnostics(
    values: dict[str, Any],
) -> dict[str, int | bool | str]:
    """Keep only bounded parser state and counters; never forward decoded text."""

    integer_fields = {
        "callback_calls",
        "string_limit_boundary_checks",
        "string_limit_boundary_violations",
        "max_observed_string_length",
        "max_active_string_limit",
        "unbounded_active_string_calls",
        "force_stop_parser_calls",
        "final_token_id",
        "generated_special_token_count",
        "generated_non_eos_special_token_count",
        "enforcer_decoder_decoded_character_count",
        "enforcer_decoder_json_error_position",
        "enforcer_decoder_unterminated_string_character_count",
        "replay_parser_error_count",
    }
    boolean_fields = {
        "last_parser_can_end",
        "last_model_eos_allowed",
        "final_model_eos_was_allowed_at_previous_prefix",
        "final_model_eos_prefix_parser_can_end",
        "enforcer_decoder_json_complete",
        "replay_parser_can_end",
        "incremental_vs_replay_can_end_mismatch",
        "replay_parser_diagnostic_error",
    }
    safe: dict[str, int | bool | str] = {}
    for key in integer_fields:
        value = values.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            safe[key] = value
    for key in boolean_fields:
        value = values.get(key)
        if isinstance(value, bool):
            safe[key] = value
    for key in (
        "last_parser_state_class",
        "enforcer_decoder_json_error_type",
        "enforcer_decoder_json_error_category",
    ):
        value = values.get(key)
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", value):
            safe[key] = value
    active_field = values.get("enforcer_decoder_unterminated_string_key")
    if active_field in _SVG_TOPIC_GUIDE_JSON_STRING_FIELDS:
        safe["active_json_string_field"] = active_field
    return safe


def _attach_svg_topic_guide_decoder_diagnostics(
    payload: dict[str, Any],
    prefix_allowed_tokens_fn: Any,
    *,
    generated: Any,
    input_token_count: int,
) -> None:
    decoder_values = _json_prefix_decoder_diagnostics(
        prefix_allowed_tokens_fn,
        generated=generated,
        input_token_count=input_token_count,
    )
    payload.update(_safe_svg_topic_guide_decoder_diagnostics(decoder_values))


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


def _validate_parent_story_worker_input(data: dict[str, Any]) -> str:
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
        "primary_activity",
        "primary_activity_sha256",
    }
    if set(data) != expected:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    activity = data.get("primary_activity")
    activity_fields = {
        "activity_ref",
        "title",
        "objective",
        "materials_text",
        "preparation_text",
        "instructions_text",
        "observation_notes",
        "safety_notes",
        "activity_kind",
        "source",
        "source_lesson_id",
        "source_lesson_title",
        "source_lesson_version_id",
        "source_content_sha256",
        "source_activity_index",
        "match_reason",
    }
    digest = (
        hashlib.sha256(
            json.dumps(activity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if isinstance(activity, dict)
        else ""
    )
    if (
        data.get("schema_version") != "sketch2life.story-generation-input.v2"
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
        or not isinstance(activity, dict)
        or set(activity) != activity_fields
        or activity.get("activity_kind") != "outdoor"
        or activity.get("source") not in {"PINNED_LESSON", "PUBLISHED_SHARED_LESSON", "AI_GENERATED_DRAFT"}
        or any(
            not isinstance(activity.get(field), str) or not activity[field].strip()
            for field in (
                "activity_ref",
                "title",
                "objective",
                "materials_text",
                "preparation_text",
                "instructions_text",
                "observation_notes",
                "safety_notes",
            )
        )
        or len(activity.get("instructions_text", "")) < 16
        or len(activity.get("safety_notes", "")) < 8
        or not isinstance(data.get("primary_activity_sha256"), str)
        or _SHA256.fullmatch(data["primary_activity_sha256"]) is None
        or digest != data["primary_activity_sha256"]
    ):
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    return digest


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
    activity = request["primary_activity"]
    activity_context = (
        f"Hoạt động chính người lớn đã chọn để làm sau video: {activity['title']}. "
        f"Mục tiêu: {activity['objective']}. Cách chuẩn bị: {activity['preparation_text']}. "
        f"Nội dung hoạt động: {activity['instructions_text']}. Lưu ý an toàn: {activity['safety_notes']}. "
        "Dùng thông tin này để giữ story gắn với hoạt động đã chọn. Hoạt động chỉ diễn ra sau video; "
        "không kể như thể trẻ đã làm xong, không đổi thành hoạt động khác, không thêm vật liệu hoặc bước nguy hiểm."
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
        f"Ý tưởng người lớn xác nhận: {idea}. Hoạt động chính: {activity_context} "
        f"Hướng viết lại: {rewrite}. {subject_facts}"
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
    _require_qwen_fast_kernels()
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


def _require_qwen_fast_kernels() -> None:
    """Fail before loading Qwen weights if its CUDA linear-attention kernels are absent."""

    available: dict[str, bool] = {}
    failures: dict[str, str] = {}
    for package in ("fla", "causal_conv1d"):
        try:
            available[package] = importlib.util.find_spec(package) is not None
            if available[package]:
                __import__(package)
        except Exception as exc:  # noqa: BLE001 - record import failure type and fail closed
            available[package] = False
            failures[package] = type(exc).__name__
    print(
        json.dumps(
            {
                "event": "qwen35_linear_attention_kernel_preflight",
                "fla_available": available.get("fla", False),
                "causal_conv1d_available": available.get("causal_conv1d", False),
                "reference_fallback_allowed": False,
                "import_failures": failures,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    if not all(available.values()):
        raise RuntimeError("MODAL_QWEN_FAST_KERNELS_UNAVAILABLE")
