"""Private Modal L4 POC for SRS v2.3 drawing.analyze."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from copy import deepcopy
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
from worker_observability import (  # noqa: E402
    observed_worker,
    refresh_worker_volume,
    worker_phase,
    worker_stage,
)

APP_NAME = "sketch2life-srs23-drawing-vlm-dev"
_CONTRACTS_FILE = _MODULE_DIR / "contracts.py"
_OBSERVABILITY_FILE = _MODULE_DIR / "worker_observability.py"
MODEL_ID = "Qwen/Qwen3.5-9B"
MODEL_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
MODEL_LICENSE = "Apache-2.0"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
MODEL_DIR = f"{MODEL_MOUNT}/qwen3_5_9b/{MODEL_REVISION}"
MODEL_MANIFEST = f"{MODEL_DIR}/sketch2life-model-manifest.json"
DRAWING_INPUT_SCHEMA = "sketch2life.modal.drawing-input.v1"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_IMAGE_PIXELS = 2_000_000
MAX_PROCESSOR_PIXELS = 512 * 512
MAX_OUTPUT_UNITS = 512
DRAWING_CONFIDENCE_LEVELS = tuple(round(step / 10, 1) for step in range(11))
_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")


def _lmfe_vietnamese_json_alphabet() -> str:
    """Allow Vietnamese text while keeping LMFE's JSON schema constraints."""

    ascii_alphabet = (
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "!@#$%^&*()_+-=[]{};:,./<>? `" + "'\"\\"
    )
    unicode_ranges = (
        (0x00A0, 0x0250),
        (0x0300, 0x0370),
        (0x1E00, 0x1F00),
        (0x2000, 0x2070),
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

download_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_CONTRACTS_FILE), "/root/contracts.py", copy=True)
    .add_local_file(str(_OBSERVABILITY_FILE), "/root/worker_observability.py", copy=True)
    .pip_install("huggingface_hub==0.33.4")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1"})
)
inference_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_CONTRACTS_FILE), "/root/contracts.py", copy=True)
    .add_local_file(str(_OBSERVABILITY_FILE), "/root/worker_observability.py", copy=True)
    .uv_pip_install("torch==2.7.1", "torchvision==0.22.1")
    .uv_pip_install(
        "transformers==5.22.1",
        "accelerate==1.8.1",
        "huggingface_hub==1.32.0",
        "Pillow==11.2.1",
        "lm-format-enforcer==0.11.3",
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
@observed_worker(
    workload="model.download.drawing_vlm",
    model_id=MODEL_ID,
    model_revision=MODEL_REVISION,
)
def download_pinned_model() -> dict[str, Any]:
    """Download only the public immutable checkpoint into the dev weights Volume."""

    from huggingface_hub import snapshot_download

    model_path = Path(MODEL_DIR)
    marker_path = Path(MODEL_MANIFEST)
    with worker_phase("model_volume_reload"):
        model_volume.reload()
    if marker_path.is_file():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if (
            marker.get("model_id") == MODEL_ID
            and marker.get("revision") == MODEL_REVISION
        ):
            with worker_phase("checkpoint_validation"):
                _ensure_checkpoint_files(model_path)
            return {
                "status": "already_present",
                "model_id": MODEL_ID,
                "revision": MODEL_REVISION,
                "license": MODEL_LICENSE,
            }
        raise RuntimeError("MODAL_MODEL_REVISION_MARKER_MISMATCH")

    model_path.mkdir(parents=True, exist_ok=True)
    with worker_phase("checkpoint_download"):
        snapshot_download(
            repo_id=MODEL_ID,
            revision=MODEL_REVISION,
            local_dir=str(model_path),
        )
    with worker_phase("checkpoint_validation"):
        _ensure_checkpoint_files(model_path)
    with worker_phase("model_manifest_write"):
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
    with worker_phase("model_volume_commit"):
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
    gpu=["L40S", "L4", "A10"],
    cpu=4.0,
    memory=32_768,
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
@observed_worker(
    workload="drawing.analyze",
    model_id=MODEL_ID,
    model_revision=MODEL_REVISION,
    gpu_class="L40S|L4|A10",
)
def analyze_drawing(payload: dict[str, Any]) -> dict[str, Any]:
    """Inspect one staged drawing and return a candidate requiring adult confirmation."""

    with worker_phase("input_envelope"):
        request = parse_worker_input(payload, execution_group="l4")
    worker_stage("workload_gate")
    if request.workload != "drawing.analyze":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")

    refresh_worker_volume(scratch_volume)
    with worker_phase("input_asset_verify"):
        image_path, image_sha256 = _verify_staged_input(request)
    with worker_phase("model_load"):
        model, processor = _load_model()

    from PIL import Image

    with worker_phase("image_preprocess"), Image.open(image_path) as opened:
        drawing = opened.convert("RGB")

    prompt = (
        "Quan sát ảnh tranh đường nét đen trên nền trắng. Chỉ mô tả chủ thể và đặc điểm "
        "nhìn thấy trực tiếp trong ảnh. Không suy đoán tuổi, danh tính, cảm xúc, năng lực "
        "hay hoàn cảnh của người vẽ. Nếu không nhận ra chủ thể, dùng candidate_subject "
        "là ‘chưa xác định’. visible_features gồm từ 1 đến 4 mô tả ngắn, cụ thể. "
        "confidence là một trong các số 0.0, 0.1, 0.2, …, 1.0 (đúng một chữ số thập phân, "
        "không dùng phần trăm), biểu thị mức chắc chắn rằng candidate_subject "
        "là chủ thể chính nhìn thấy trong ảnh: gần 0 khi không nhận diện được, khoảng 0.5 "
        "khi còn mơ hồ, gần 1 khi có dấu hiệu hình ảnh rõ ràng. Chỉ dựa trên ảnh; không "
        "tăng confidence theo chủ đề hay ý định vẽ. Đây chỉ là ước lượng hỗ trợ người lớn, "
        "không thay thế xác nhận của người lớn. "
        "Không viết lời dẫn hoặc nội dung ngoài JSON."
    )
    with worker_phase("prompt_encode"):
        messages = _drawing_messages(drawing, prompt)
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)

    import torch

    tokenizer = processor.tokenizer
    generation_config = deepcopy(model.generation_config)
    model_eos_token_id = generation_config.eos_token_id
    if model_eos_token_id is None:
        model_eos_token_id = tokenizer.eos_token_id
    generation_config.eos_token_id = model_eos_token_id
    generation_config.pad_token_id = _drawing_generation_pad_token_id(
        model_eos_token_id, tokenizer
    )
    generation_config.do_sample = False
    generation_config.max_new_tokens = MAX_OUTPUT_UNITS
    generation_config.min_new_tokens = 16
    with worker_phase("constrained_decoder_setup"):
        prefix_allowed_tokens_fn = _build_drawing_prefix_allowed_tokens_fn(
            tokenizer, eos_token_id=model_eos_token_id
        )
    with worker_phase("model_inference"), torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            generation_config=generation_config,
            prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
        )
    answer_ids = output_ids[0][inputs.input_ids.shape[-1] :]
    generated_token_count = int(answer_ids.shape[-1])
    generated_ids = [int(token_id) for token_id in answer_ids.tolist()]
    model_eos_token_ids = _normalize_token_ids(model_eos_token_id)
    ended_with_model_eos = bool(
        generated_ids and generated_ids[-1] in model_eos_token_ids
    )
    print(
        json.dumps(
            {
                "event": "drawing_candidate_generated",
                "generated_token_count": generated_token_count,
                "max_output_units": MAX_OUTPUT_UNITS,
                "token_limit_reached": generated_token_count >= MAX_OUTPUT_UNITS,
                "model_eos_token_ids": model_eos_token_ids,
                "ended_with_model_eos": ended_with_model_eos,
                **_drawing_decoder_diagnostics(
                    prefix_allowed_tokens_fn,
                    generated_ids=generated_ids,
                    input_token_count=int(inputs.input_ids.shape[-1]),
                    model_eos_token_ids=model_eos_token_ids,
                ),
                "empty_output": generated_token_count == 0,
                "input_token_count": int(inputs.input_ids.shape[-1]),
                "output_sequence_length": int(output_ids.shape[-1]),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    worker_stage("model_output_validation")
    if generated_token_count == 0:
        raise RuntimeError("MODAL_MODEL_OUTPUT_EMPTY")
    answer = processor.batch_decode(
        [answer_ids],
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0].strip()
    try:
        with worker_phase("output_parse_and_contract_validation"):
            candidate = _parse_candidate(answer)
    except RuntimeError as exc:
        if str(exc) != "MODAL_MODEL_OUTPUT_INVALID":
            raise
        diagnostics = _drawing_json_diagnostics(answer)
        truncated = generated_token_count >= MAX_OUTPUT_UNITS and not ended_with_model_eos
        print(
            json.dumps(
                {
                    "event": "drawing_output_truncated" if truncated else "drawing_output_invalid",
                    "reason_code": (
                        "MODAL_MODEL_OUTPUT_TRUNCATED"
                        if truncated
                        else "MODAL_MODEL_OUTPUT_INVALID"
                    ),
                    "workload": "drawing.analyze",
                    "generated_token_count": generated_token_count,
                    "max_output_units": MAX_OUTPUT_UNITS,
                    "token_limit_reached": generated_token_count >= MAX_OUTPUT_UNITS,
                    "model_eos_token_ids": model_eos_token_ids,
                    "ended_with_model_eos": ended_with_model_eos,
                    **diagnostics,
                    **_drawing_decoder_diagnostics(
                        prefix_allowed_tokens_fn,
                        generated_ids=generated_ids,
                        input_token_count=int(inputs.input_ids.shape[-1]),
                        model_eos_token_ids=model_eos_token_ids,
                    ),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        raise RuntimeError(
            "MODAL_MODEL_OUTPUT_TRUNCATED" if truncated else "MODAL_MODEL_OUTPUT_INVALID"
        ) from None

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
    required = ("config.json", "preprocessor_config.json", "tokenizer.json")
    if not model_path.is_dir() or not all(
        (model_path / name).is_file() for name in required
    ):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")
    index_path = model_path / "model.safetensors.index.json"
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
            or not (model_path / name).is_file()
            for name in shard_names
        ):
            raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")
    elif not (model_path / "model.safetensors").is_file() and not list(
        model_path.glob("model-*.safetensors")
    ):
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")


def _drawing_messages(drawing: Any, prompt: str) -> list[dict[str, Any]]:
    """Use the documented Qwen3.5 image-in-message input representation."""

    return [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": drawing},
                {"type": "text", "text": prompt},
            ],
        }
    ]


_CACHED_QWEN_VOCAB_DATA: Any | None = None
_CACHED_QWEN_EOS_IDS: tuple[int, ...] | None = None


def _drawing_output_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "candidate_subject": {"type": "string", "minLength": 1, "maxLength": 100},
            "visible_features": {
                "type": "array",
                "minItems": 1,
                "maxItems": 4,
                "items": {"type": "string", "minLength": 1, "maxLength": 160},
            },
            # LMFE 0.11.3 does not enforce numeric minimum/maximum or digit count, so a
            # bounded range let the model emit 85 / 1.5 / endless digits and fail
            # parsing after EOS. A closed enum is enforced character by character.
            "confidence": {"type": "number", "enum": list(DRAWING_CONFIDENCE_LEVELS)},
        },
        "required": ["candidate_subject", "visible_features", "confidence"],
        "additionalProperties": False,
    }


def _build_drawing_prefix_allowed_tokens_fn(
    tokenizer: Any, *, eos_token_id: int | list[int] | None = None
) -> Any:
    """Constrain Qwen3.5 to the exact VLM result schema at generation time."""

    global _CACHED_QWEN_VOCAB_DATA, _CACHED_QWEN_EOS_IDS
    os.environ["LMFE_DEFAULT_ALPHABET"] = LMFE_VIETNAMESE_JSON_ALPHABET
    try:
        from lmformatenforcer import JsonSchemaParser
        from lmformatenforcer.tokenenforcer import (
            TokenEnforcer,
            TokenEnforcerTokenizerData,
        )
    except ImportError as exc:
        raise RuntimeError("MODAL_CONSTRAINED_DECODER_UNAVAILABLE") from exc

    effective_eos_token_id = tokenizer.eos_token_id if eos_token_id is None else eos_token_id
    eos_ids = tuple(_normalize_token_ids(effective_eos_token_id))
    if _CACHED_QWEN_VOCAB_DATA is None or eos_ids != _CACHED_QWEN_EOS_IDS:
        _CACHED_QWEN_VOCAB_DATA = _build_qwen_tokenizer_data(
            tokenizer,
            TokenEnforcerTokenizerData,
            eos_token_id=effective_eos_token_id,
        )
        _CACHED_QWEN_EOS_IDS = eos_ids
    enforcer = TokenEnforcer(
        _CACHED_QWEN_VOCAB_DATA,
        JsonSchemaParser(_drawing_output_json_schema()),
    )
    diagnostics: dict[str, Any] = {
        "callback_calls": 0,
        "last_parser_can_end": False,
        "last_model_eos_allowed": False,
        "last_parser_state_class": "unknown",
    }

    def allowed_tokens(_batch_id: int, input_ids: Any) -> list[int]:
        token_ids = input_ids.tolist()
        allowed = enforcer.get_allowed_tokens(token_ids)
        values = getattr(allowed, "allowed_tokens", allowed)
        prefix_state = getattr(enforcer, "prefix_states", {}).get(tuple(token_ids))
        parser = getattr(prefix_state, "parser", None)
        diagnostics["last_parser_state_class"] = type(parser).__name__
        can_end = getattr(parser, "can_end", None)
        diagnostics["last_parser_can_end"] = bool(can_end()) if callable(can_end) else False
        diagnostics["last_model_eos_allowed"] = any(
            token_id in values for token_id in eos_ids
        )
        diagnostics["callback_calls"] += 1
        return list(values)

    allowed_tokens.decoder_diagnostics = diagnostics
    return allowed_tokens


def _build_qwen_tokenizer_data(
    tokenizer: Any,
    tokenizer_data_type: Any,
    *,
    eos_token_id: int | list[int] | None = None,
) -> Any:
    """Build LMFE tokenizer data with all model EOS IDs treated as special."""

    vocab_size = len(tokenizer)
    token_zero = tokenizer.encode("0")[-1]
    special_ids = set(tokenizer.all_special_ids)
    effective_eos_token_id = tokenizer.eos_token_id if eos_token_id is None else eos_token_id
    special_ids.update(_normalize_token_ids(effective_eos_token_id))

    def decode(tokens: list[int]) -> str:
        # Incremental decoder only: LMFE strips a trailing partial UTF-8 character
        # here so multi-token characters are emitted once they are complete.
        return tokenizer.decode(tokens).rstrip("�")

    regular_tokens: list[tuple[int, str, bool]] = []
    for token_id in range(vocab_size):
        if token_id in special_ids:
            continue
        # Match LMFE's Transformers adapter and the story worker: build the prefix
        # tree from raw decodes. Stripping "\ufffd" here turns byte-fragment tokens
        # into empty strings marked as new words; LMFE then allows them in every
        # parser state (including after the closing brace) without ever applying
        # their characters, so the final text can carry bytes the parser never saw.
        decoded_after_zero = tokenizer.decode([token_zero, token_id])
        decoded_token = tokenizer.decode([token_id])
        regular_tokens.append(
            (token_id, decoded_after_zero[1:], len(decoded_after_zero) > len(decoded_token))
        )

    return tokenizer_data_type(
        regular_tokens,
        decode,
        effective_eos_token_id,
        use_bitmask=False,
        vocab_size=vocab_size,
    )


def _normalize_token_ids(value: Any) -> list[int]:
    if isinstance(value, int) and not isinstance(value, bool):
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, int) and not isinstance(item, bool)]
    return []


def _drawing_generation_pad_token_id(eos_token_id: Any, tokenizer: Any) -> int:
    eos_ids = _normalize_token_ids(eos_token_id)
    if eos_ids:
        return eos_ids[0]
    pad_id = getattr(tokenizer, "pad_token_id", None)
    if isinstance(pad_id, int) and not isinstance(pad_id, bool):
        return pad_id
    raise RuntimeError("MODAL_GENERATION_EOS_UNAVAILABLE")


def _drawing_json_diagnostics(answer: str) -> dict[str, Any]:
    details: dict[str, Any] = {"decoded_character_count": len(answer)}
    try:
        parsed = json.loads(answer)
    except json.JSONDecodeError as exc:
        message = exc.msg.lower()
        if "unterminated string" in message:
            error_type = "UnterminatedString"
        elif "expecting value" in message:
            error_type = "ExpectingValue"
        elif "expecting property name" in message:
            error_type = "ExpectingPropertyName"
        elif "delimiter" in message:
            error_type = "DelimiterError"
        elif "extra data" in message:
            error_type = "ExtraData"
        elif "control character" in message:
            error_type = "InvalidControlCharacter"
        elif "escape" in message:
            error_type = "InvalidEscape"
        else:
            error_type = "OtherJSONError"
        details.update(
            {
                "json_complete": False,
                "json_error_type": error_type,
                "json_error_position": exc.pos,
            }
        )
        return details
    details["json_complete"] = True
    details["json_root_type"] = type(parsed).__name__
    if isinstance(parsed, dict):
        details["json_root_key_count"] = len(parsed)
    details["contract_violation"] = _drawing_contract_violation(parsed)
    return details


def _drawing_decoder_diagnostics(
    prefix_allowed_tokens_fn: Any,
    *,
    generated_ids: list[int],
    input_token_count: int,
    model_eos_token_ids: list[int],
) -> dict[str, Any]:
    diagnostics = getattr(prefix_allowed_tokens_fn, "decoder_diagnostics", {})
    result: dict[str, Any] = {
        key: diagnostics[key]
        for key in (
            "callback_calls",
            "last_parser_can_end",
            "last_model_eos_allowed",
            "last_parser_state_class",
        )
        if key in diagnostics
    }
    if generated_ids:
        result["final_token_id"] = generated_ids[-1]
        result["final_model_eos_was_allowed_at_previous_prefix"] = (
            generated_ids[-1] in model_eos_token_ids
            and bool(diagnostics.get("last_model_eos_allowed"))
        )
    result["input_token_count"] = input_token_count
    return result


def _verify_staged_input(request: ModalWorkerInputV1) -> tuple[Path, str]:
    scratch_root = Path(SCRATCH_MOUNT).resolve()
    attempt_dir = (scratch_root / request.attempt_prefix.rstrip("/")).resolve()
    if not attempt_dir.is_relative_to(scratch_root):
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")

    input_dir = attempt_dir / "input"
    manifest_path = (input_dir / "manifest.json").resolve()
    image_path = (input_dir / "drawing.png").resolve()
    if not manifest_path.is_relative_to(attempt_dir) or not image_path.is_relative_to(
        attempt_dir
    ):
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
    if (
        asset.get("path") != "input/drawing.png"
        or asset.get("content_type") != "image/png"
    ):
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
            if (
                opened.format != "PNG"
                or opened.width * opened.height > MAX_IMAGE_PIXELS
            ):
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
    from transformers import AutoModelForMultimodalLM, AutoProcessor

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    _CACHED_PROCESSOR = AutoProcessor.from_pretrained(
        str(model_path),
        local_files_only=True,
        min_pixels=224 * 224,
        max_pixels=MAX_PROCESSOR_PIXELS,
    )
    _CACHED_MODEL = AutoModelForMultimodalLM.from_pretrained(
        str(model_path),
        dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="sdpa",
        low_cpu_mem_usage=True,
        local_files_only=True,
    )
    _CACHED_MODEL.eval()
    return _CACHED_MODEL, _CACHED_PROCESSOR


def _drawing_contract_violation(parsed: Any) -> str:
    """Content-free code naming which output-contract rule a complete JSON value broke."""

    expected = {"candidate_subject", "visible_features", "confidence"}
    if not isinstance(parsed, dict):
        return "ROOT_NOT_OBJECT"
    if set(parsed) != expected:
        return "MISSING_KEYS" if set(parsed) < expected else "UNEXPECTED_KEYS"
    subject = parsed["candidate_subject"]
    if not isinstance(subject, str) or not subject.strip() or len(subject) > 100:
        return "SUBJECT_INVALID"
    features = parsed["visible_features"]
    if not isinstance(features, list) or not 1 <= len(features) <= 4:
        return "FEATURES_COUNT_INVALID"
    if any(not isinstance(i, str) or not i.strip() or len(i) > 160 for i in features):
        return "FEATURE_ITEM_INVALID"
    confidence = parsed["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return "CONFIDENCE_NOT_NUMBER"
    if not math.isfinite(float(confidence)) or not 0 <= float(confidence) <= 1:
        return "CONFIDENCE_OUT_OF_RANGE"
    return "NONE"


def _parse_candidate(answer: str) -> dict[str, Any]:
    try:
        parsed = json.loads(answer, object_pairs_hook=_reject_duplicate_candidate_keys)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID") from exc
    if not isinstance(parsed, dict) or set(parsed) != {
        "candidate_subject",
        "visible_features",
        "confidence",
    }:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    subject = parsed.get("candidate_subject")
    features = parsed.get("visible_features")
    confidence = parsed.get("confidence")
    if (
        not isinstance(subject, str)
        or not subject.strip()
        or len(subject) > 100
        or not isinstance(features, list)
        or not 1 <= len(features) <= 4
        or any(
            not isinstance(item, str) or not item.strip() or len(item) > 160
            for item in features
        )
        or isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
    ):
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    try:
        confidence_value = float(confidence)
    except (OverflowError, ValueError):
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID") from None
    if not math.isfinite(confidence_value) or not 0 <= confidence_value <= 1:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    return {
        "candidate_subject": subject.strip(),
        "visible_features": [item.strip() for item in features],
        "confidence": confidence_value,
    }


def _reject_duplicate_candidate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


_CACHED_MODEL: Any | None = None
_CACHED_PROCESSOR: Any | None = None
