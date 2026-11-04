"""Private Modal dev workers for the SRS story, TTS, and ASR POCs."""

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

APP_NAME = "sketch2life-srs23-language-audio-dev"
MODEL_VOLUME_NAME = "sketch2life-dev-model-weights-v2"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
MODEL_MOUNT = "/models"
SCRATCH_MOUNT = "/scratch"
TEXT_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
TEXT_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
TEXT_MODEL_DIR = f"{MODEL_MOUNT}/qwen2_5_7b_instruct/{TEXT_MODEL_REVISION}"
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
_text_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
    .uv_pip_install("torch==2.7.1", "transformers==4.53.0", "accelerate==1.8.1")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1"})
)
_tts_image = (
    modal.Image.debian_slim(python_version="3.11")
    .add_local_file(str(_contracts_file), "/root/contracts.py", copy=True)
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
def download_language_audio_models() -> dict[str, Any]:
    """Download the exact public model revisions used by this POC wave."""

    from huggingface_hub import snapshot_download

    model_volume.reload()
    records = [
        (
            TEXT_MODEL_ID,
            TEXT_MODEL_REVISION,
            Path(TEXT_MODEL_DIR),
            Path(TEXT_MODEL_MARKER),
            "Apache-2.0",
        ),
        (ASR_MODEL_ID, ASR_MODEL_REVISION, Path(ASR_MODEL_DIR), Path(ASR_MODEL_MARKER), "MIT"),
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
    for model_id, revision, model_path, marker_path, license_name in records:
        if marker_path.is_file():
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
            if marker.get("model_id") != model_id or marker.get("revision") != revision:
                raise RuntimeError("MODAL_MODEL_REVISION_MARKER_MISMATCH")
            results.append(
                {"status": "already_present", "model_id": model_id, "revision": revision}
            )
            continue

        model_path.mkdir(parents=True, exist_ok=True)
        snapshot_download(repo_id=model_id, revision=revision, local_dir=str(model_path))
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
        results.append({"status": "downloaded", "model_id": model_id, "revision": revision})

    _verify_text_checkpoint(Path(TEXT_MODEL_DIR))
    _verify_asr_checkpoint(Path(ASR_MODEL_DIR))
    _verify_tts_checkpoint(Path(TTS_MODEL_DIR), Path(TTS_CODEC_DIR))
    model_volume.commit()
    return {"status": "ready", "models": results}


@app.function(
    name="generate-story-and-storyboard",
    image=_text_image,
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
def generate_story_and_storyboard(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate one adult-review Parent story revision matching the SRS scene contract."""

    request = parse_worker_input(payload, execution_group="l4")
    if request.workload != "story.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    data = _read_json_asset(request, expected_asset="input/request.json")
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

    _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    tokenizer, model = _load_text_model()
    prompt = _parent_story_prompt(data)
    messages = [
        {
            "role": "system",
            "content": "Bạn là trợ lý viết nội dung giáo dục ngắn, an toàn và trung thực.",
        },
        {"role": "user", "content": prompt},
    ]
    encoded = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)
    import torch

    with torch.inference_mode():
        generated = model.generate(
            encoded,
            do_sample=False,
            max_new_tokens=2_400,
            pad_token_id=tokenizer.eos_token_id,
        )
    text = tokenizer.decode(generated[0, encoded.shape[-1] :], skip_special_tokens=True).strip()
    result = _parse_story_output(text, data)
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
def generate_teacher_sketch_deck(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate the ordered drawing-guide text for one reviewed-plan deck draft."""

    request = parse_worker_input(payload, execution_group="l4")
    if request.workload != "teacher.sketch-deck.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    data = _read_json_asset(request, expected_asset="input/request.json")
    _validate_teacher_deck_input(data)
    _verify_marker(Path(TEXT_MODEL_MARKER), TEXT_MODEL_ID, TEXT_MODEL_REVISION)
    tokenizer, model = _load_text_model()
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
    encoded = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)
    import torch

    with torch.inference_mode():
        generated = model.generate(
            encoded,
            do_sample=False,
            max_new_tokens=900,
            pad_token_id=tokenizer.eos_token_id,
        )
    text = tokenizer.decode(generated[0, encoded.shape[-1] :], skip_special_tokens=True).strip()
    guide = _parse_teacher_guide(text, data)
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
                for field in ("goal", "materials", "preparation", "instructions", "safety_notes")
            )
        ):
            raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
        activity_ids.add(activity["activity_ref"])


def _teacher_deck_prompt(data: dict[str, Any]) -> str:
    return (
        "Tạo DUY NHẤT JSON object "
        '{"steps":[{"step_index":1,"instruction":"...","placement":"..."}]}. '
        "Viết tiếng Việt ngắn, phù hợp trẻ theo tuổi mục tiêu. Hãy biến các thao tác vẽ đã duyệt "
        "thành lời mời quan sát/vẽ đơn giản, tiến triển từ hình cơ bản sang chi tiết; giữ nguyên "
        "thứ tự và vị trí. Không thêm vật thể/chủ thể mới, activity, vật liệu, mục tiêu học tập "
        "hoặc tuyên bố kiến thức. Không nhắc tên trẻ/roster và không tạo PowerPoint. "
        "Không markdown. "
        f"Chủ đề: {data['topic']}; tuổi mục tiêu {data['target_age_months']} tháng. "
        f"Thao tác đã duyệt: {json.dumps(data['drawing_steps'], ensure_ascii=False)}. "
        f"Số bước phải đúng {len(data['drawing_steps'])}."
    )


def _parse_teacher_guide(text: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        start = text.find("{")
        guide, _ = json.JSONDecoder().raw_decode(text[start:])
    except (ValueError, json.JSONDecodeError, IndexError) as exc:
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
                or len(candidate[field]) > 200
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


def _compose_teacher_deck(data: dict[str, Any], guide: list[dict[str, Any]]) -> dict[str, Any]:
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
        "approved_activity_refs": [activity["activity_ref"] for activity in data["activities"]],
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
def synthesize_vietnamese_narration(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate one short synthetic sentence with the adult preset voice."""

    request = parse_worker_input(payload, execution_group="l4")
    if request.workload != "tts.narration.generate":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    data = _read_json_asset(request, expected_asset="input/request.json")
    if set(data) != {"text", "voice"}:
        raise WorkerContractError("MODAL_INPUT_MANIFEST_INVALID")
    if data["text"] != "Con bướm bay qua khu vườn đầy nắng." or data["voice"] != "Hải Đăng":
        raise WorkerContractError("MODAL_INPUT_NOT_ALLOWED")
    _verify_marker(Path(TTS_MODEL_MARKER), TTS_MODEL_ID, TTS_MODEL_REVISION)
    _verify_marker(Path(TTS_CODEC_MARKER), TTS_CODEC_ID, TTS_CODEC_REVISION)

    from vieneu import Vieneu

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
    audio = engine.infer(data["text"], voice=data["voice"], max_new_frames=160, max_chars=100)
    output_path = Path("/tmp/sketch2life-synthetic-narration.wav")
    engine.save(audio, str(output_path))
    output_bytes = output_path.read_bytes()
    if not output_bytes.startswith(b"RIFF") or len(output_bytes) > MAX_OUTPUT_BYTES:
        raise RuntimeError("MODAL_OUTPUT_INVALID")
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
def transcribe_vietnamese_audio(payload: dict[str, Any]) -> dict[str, Any]:
    """Transcribe only the synthetic audio asset staged for this POC."""

    request = parse_worker_input(payload, execution_group="l4")
    if request.workload != "asr.transcribe":
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")
    audio_path, audio_sha256 = _read_binary_asset(
        request,
        expected_asset="input/audio.wav",
        expected_content_type="audio/wav",
        signature=b"RIFF",
    )
    _verify_marker(Path(ASR_MODEL_MARKER), ASR_MODEL_ID, ASR_MODEL_REVISION)

    from faster_whisper import WhisperModel

    model = WhisperModel(
        ASR_MODEL_DIR,
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
        num_workers=1,
    )
    segments, info = model.transcribe(
        str(audio_path),
        language="vi",
        task="transcribe",
        beam_size=1,
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


def _read_json_asset(request: ModalWorkerInputV1, *, expected_asset: str) -> dict[str, Any]:
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
    if not manifest_path.is_relative_to(attempt_dir) or not asset_path.is_relative_to(attempt_dir):
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
    if asset.get("path") != expected_asset or asset.get("content_type") != expected_content_type:
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


def _parse_story_output(text: str, request: dict[str, Any]) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    start = text.find("{")
    if start < 0:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    try:
        data, _ = decoder.raw_decode(text[start:])
    except json.JSONDecodeError as exc:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID") from exc
    expected = {"schema_version", "language", "title", "story", "duration_ms", "scenes"}
    if not isinstance(data, dict) or set(data) != expected:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    story = data["story"]
    scenes = data["scenes"]
    if (
        data.get("schema_version") != "sketch2life.story-revision.v1"
        or data.get("language") != "vi"
        or not isinstance(data["title"], str)
        or not isinstance(story, dict)
        or set(story) != {"opening", "middle", "ending"}
        or any(not isinstance(story[key], str) or not story[key].strip() for key in story)
        or not isinstance(scenes, list)
        or not 5 <= len(scenes) <= 15
        or isinstance(data.get("duration_ms"), bool)
        or not isinstance(data.get("duration_ms"), int)
        or not 30_000 <= data["duration_ms"] <= 90_000
    ):
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    checked_scenes: list[dict[str, Any]] = []
    timeline_ms = 0
    for index, scene in enumerate(scenes, start=1):
        if (
            not isinstance(scene, dict)
            or set(scene)
            != {
                "scene_index",
                "title",
                "action",
                "visual_prompt",
                "narration",
                "start_ms",
                "duration_ms",
                "character_anchors",
            }
            or scene.get("scene_index") != index
            or any(
                not isinstance(scene.get(key), str) or not scene[key].strip()
                for key in ("title", "action", "visual_prompt", "narration")
            )
            or isinstance(scene.get("start_ms"), bool)
            or scene.get("start_ms") != timeline_ms
            or isinstance(scene.get("duration_ms"), bool)
            or not isinstance(scene.get("duration_ms"), int)
            or not 1_000 <= scene["duration_ms"] <= 20_000
            or not isinstance(scene.get("character_anchors"), list)
            or not 1 <= len(scene["character_anchors"]) <= 6
            or any(
                not isinstance(anchor, str) or not anchor.strip() or len(anchor) > 120
                for anchor in scene["character_anchors"]
            )
        ):
            raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
        timeline_ms += scene["duration_ms"]
        checked_scenes.append(scene)
    if timeline_ms != data["duration_ms"]:
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID")
    result = {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": data["title"].strip()[:120],
        "story": story,
        "duration_ms": data["duration_ms"],
        "scenes": checked_scenes,
    }
    _validate_butterfly_facts(result, str(request["confirmed_subject"]))
    return result


def _parent_story_prompt(request: dict[str, Any]) -> str:
    subject = str(request["confirmed_subject"]).strip()
    features = [str(item).strip()[:160] for item in request["visible_features"]]
    age = int(request["child_age_months"])
    idea = str(request["adult_confirmed_idea"]).strip() or "Không có ý tưởng bổ sung từ người lớn."
    rewrite = request.get("rewrite_instruction") or "Không có yêu cầu viết lại. Đây là bản đầu."
    facts = ""
    folded_subject = _fold_vi(subject)
    if "buom" in folded_subject or "butterfly" in folded_subject:
        facts = (
            "FACT PACK butterfly-lifecycle-v1 (phải tuân thủ): trứng nở thành sâu bướm/ấu trùng; "
            "sâu bướm ăn lá và lớn lên; sâu bướm hóa nhộng; bướm trưởng thành chui ra khỏi nhộng. "
            "Bắt buộc kể đủ và đúng thứ tự bốn giai đoạn, dùng đúng các tên: trứng, sâu bướm, "
            "nhộng, "
            "bướm trưởng thành. Trứng không nở thành bướm trưởng thành. Không viết chi tiết về tổ."
        )
    return (
        "Bạn viết story draft giáo dục ngắn, bằng tiếng Việt, child-centered "
        "và Montessori-inspired. "
        "Người lớn là người hướng dẫn; trẻ quan sát, tò mò và tự khám phá. Không gán tên, cảm xúc, "
        "khả năng, danh tính hoặc chẩn đoán cho người vẽ. Không viết lời khuyên y tế, nguy hiểm, "
        "quảng cáo, bạo lực hay bài học áp đặt. Bám chủ thể đã được người lớn xác nhận và các nét "
        "nhìn thấy trong tranh; giữ các nét đó làm character anchors nhất quán. "
        "Không thêm activity "
        "hoặc yêu cầu phụ huynh chọn activity trước video. Không có tên trẻ trong input/output. "
        f"Chủ thể đã xác nhận: {subject}. "
        f"Nét nhìn thấy trong tranh: {json.dumps(features, ensure_ascii=False)}. "
        f"Độ tuổi chính xác: {age} tháng; dùng câu ngắn, từ vựng và mức khám phá phù hợp tuổi, "
        "không bịa age-band. Ý tưởng đã được người lớn xác nhận: " + idea + ". "
        "Yêu cầu viết lại của người lớn (chỉ là hướng dẫn, không được ghi nguyên xi vào story): "
        + str(rewrite)
        + ". "
        + (facts + " ")
        + (
            "Tạo mở đầu, diễn biến, kết thúc và 5–15 cảnh theo cùng một mạch. "
            "Chọn tổng thời lượng 30–90 giây. Cảnh nối tiếp theo thứ tự, không lặp nội dung "
            "để đủ số cảnh. Mỗi cảnh có action, visual_prompt chỉ mô tả hình ảnh chuyển động "
            "phù hợp tranh, narration ngắn, start_ms liên tục, duration_ms, và 1–6 "
            "character_anchors lấy từ nét tranh. Tổng duration các cảnh phải bằng duration_ms. "
            "Trả về DUY NHẤT JSON object, không markdown, đúng keys: "
            '{"schema_version":"sketch2life.story-revision.v1","language":"vi","title":"...",'
            '"story":{"opening":"...","middle":"...","ending":"..."},"duration_ms":48000,'
            '"scenes":[{"scene_index":1,"title":"...","action":"...","visual_prompt":"...",'
            '"narration":"...","start_ms":0,"duration_ms":6000,"character_anchors":["..."]}]} '
            "Không thêm key nào khác. Chỉ tạo nội dung DRAFT cần người lớn xem/xác nhận."
        )
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
                *story["story"].values(),
                *(scene["action"] + " " + scene["narration"] for scene in story["scenes"]),
            ]
        )
    )
    forbidden = (
        r"trung\s+(?:no|nở)\s+(?:(?:ra|thanh)\s+)?(?:con\s+)?buom",
        r"buom(?:\s+\w+){0,4}\s+(?:tim|kiem|xay|lam)\s+(?:mot\s+)?to",
        r"butterfly\s+(?:hatches|looks?\s+for|builds?\s+(?:a\s+)?nest)",
    )
    if any(re.search(pattern, all_text) for pattern in forbidden):
        raise RuntimeError("MODAL_EDUCATIONAL_FACT_CHECK_FAILED")
    phases = ("trung", "sau buom", "nhong", "buom truong thanh")
    positions = [all_text.find(phase) for phase in phases]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise RuntimeError("MODAL_EDUCATIONAL_FACT_CHECK_FAILED")


def _verify_marker(path: Path, model_id: str, revision: str) -> None:
    if not path.is_file():
        raise RuntimeError("MODAL_MODEL_NOT_READY")
    marker = json.loads(path.read_text(encoding="utf-8"))
    if marker.get("model_id") != model_id or marker.get("revision") != revision:
        raise RuntimeError("MODAL_MODEL_REVISION_MISMATCH")


def _verify_text_checkpoint(path: Path) -> None:
    if not (path / "config.json").is_file() or not (path / "tokenizer.json").is_file():
        raise RuntimeError("MODAL_MODEL_CHECKPOINT_INCOMPLETE")
    if not list(path.glob("model-*.safetensors")) and not (path / "model.safetensors").is_file():
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
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not torch.cuda.is_available():
        raise RuntimeError("MODAL_GPU_UNAVAILABLE")
    _CACHED_TEXT_PREPROCESSOR = AutoTokenizer.from_pretrained(
        TEXT_MODEL_DIR,
        local_files_only=True,
        trust_remote_code=False,
    )
    _CACHED_TEXT_MODEL = AutoModelForCausalLM.from_pretrained(
        TEXT_MODEL_DIR,
        torch_dtype=torch.float16,
        device_map="auto",
        attn_implementation="sdpa",
        low_cpu_mem_usage=True,
        local_files_only=True,
        trust_remote_code=False,
    ).eval()
    return _CACHED_TEXT_PREPROCESSOR, _CACHED_TEXT_MODEL
