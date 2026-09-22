"""Lightning Vision V2 + faster-whisper ASR service for the FEAT-018 demo.

Deploy this service in the configured Lightning environment. It exposes only the explicit
image-understanding and optional narration-ASR routes. Provider output, transcripts, credentials,
and temporary media files are never logged.
"""

from __future__ import annotations

import base64
import logging
import os
import sys
import tempfile
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_SRC = _REPO_ROOT / "backend" / "src"
if _BACKEND_SRC.is_dir() and str(_BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(_BACKEND_SRC))

from sketch2life.contracts.schemas.asr import (
    AsrErrorCode,
    AsrErrorDetail,
    AsrFailureV1,
    AsrQualityMetadataV1,
    AsrRequestV1,
    AsrSegmentV1,
    AsrSpeechDiagnostic,
    AsrSuccessV1,
)
from sketch2life.contracts.schemas.vision import VisionImageReferenceV1
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingRequestV2,
)
from sketch2life.infrastructure.ai.qwen_vision import QwenVisionAdapter
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import (
    VISION_MODEL_DIR_ENV_VAR,
    QwenVisionRuntimeConfig,
)
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

MAX_INPUT_BYTES = 5_000_000
MAX_AUDIO_BYTES = 20_000_000
EXPECTED_AUTH = os.getenv("LIGHTNING_DEV_AUTH", "").strip()
VLM_ROOT = Path(os.getenv("SKETCH2LIFE_VLM_ROOT", "models/vlm/qwen3-vl-8b-instruct"))
logger = logging.getLogger("sketch2life.lightning_vision_v2")
_ASR_MODEL_LOCK = Lock()
_ASR_MODEL = None

_PROMPT = """Return exactly one strict JSON object and no surrounding text. Analyze visible marks in
this synthetic, non-child drawing. Do not infer a child's personality, emotions, intent, diagnosis,
ability, development, or mental state.
Use exactly these root keys: entities, actions, relations, themes, ambiguous_regions. Use arrays;
use [] when uncertain. Maximums: 5 entities, 2 actions, 3 relations, 2 themes, 2 ambiguous regions.
Every text value is an object with value and language. Use language {status: DECLARED, tags: [vi]}
for Vietnamese labels, or {status: NOT_DETERMINED, tags: []} when unknown. is_ground_truth must be
false if emitted.
Use a unique lowercase observation_id containing only a-z, 0-9, hyphens. Include confidence from
0 to 1. Entities: observation_id,label,confidence. Actions: observation_id,label,actor_ref,
object_ref,confidence; refs are entity IDs or null. Relations: observation_id,predicate,subject_ref,
object_ref,confidence; refs point to distinct entity/action IDs. Themes: observation_id,label,
evidence_refs,confidence; evidence refs point to entity/action/relation IDs. Ambiguous regions:
observation_id,note.
Do not add keys, markdown fences, geometry, or metadata. Omit uncertain observations instead of
inventing them."""


def _prompt_with_narration(context: str | None) -> str:
    if not context:
        return _PROMPT
    return (
        f"{_PROMPT}\n\nA narration context is supplied below. Treat it as an adult-provided "
        "description to help disambiguate visible marks only; do not treat it as proof, do not "
        "infer personal traits, and do not emit facts not grounded in the image.\n"
        "--- NARRATION CONTEXT START ---\n"
        f"{context[:2_000]}\n"
        "--- NARRATION CONTEXT END ---"
    )


class _SourceImageV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_ref: str = Field(min_length=1, max_length=300)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: Literal["image/jpeg", "image/png"]
    content_base64: str = Field(min_length=1, max_length=6_666_668)


class LightningVisionRequestV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["LightningVisionRequestV2"] = "LightningVisionRequestV2"
    contract_version: Literal["2.0"] = "2.0"
    request: VisionUnderstandingRequestV2
    source_image: _SourceImageV1
    narration_context: str | None = Field(default=None, max_length=2_000)


class _SourceAudioV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_ref: str = Field(min_length=1, max_length=300)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_base64: str = Field(min_length=1, max_length=26_666_668)


class LightningAsrRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["AsrRequestV1"] = "AsrRequestV1"
    contract_version: Literal["1.0"] = "1.0"
    request: AsrRequestV1
    source_audio: _SourceAudioV1


app = FastAPI(title="Sketch2Life Lightning Vision and ASR", version="2.1.0", redoc_url=None)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lightning-vision-v2"}


@app.post("/v2/vision")
def vision_v2(
    payload: LightningVisionRequestV2,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    if not EXPECTED_AUTH:
        raise HTTPException(status_code=503, detail="provider authentication is not configured")
    if authorization != f"Bearer {EXPECTED_AUTH}":
        raise HTTPException(status_code=401, detail="unauthorized")

    reference = payload.request.source_image_ref
    artifact = payload.source_image
    if artifact.artifact_ref != reference.artifact_ref or artifact.sha256 != reference.sha256:
        raise HTTPException(status_code=422, detail="source identity mismatch")
    try:
        image = base64.b64decode(artifact.content_base64, validate=True)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="invalid image payload") from None
    if not image or len(image) > MAX_INPUT_BYTES:
        raise HTTPException(status_code=413, detail="image size is outside the allowed range")
    if sha256(image).hexdigest() != artifact.sha256:
        raise HTTPException(status_code=422, detail="source digest mismatch")
    if artifact.content_type == "image/png" and not image.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=422, detail="image type mismatch")
    if artifact.content_type == "image/jpeg" and not image.startswith(b"\xff\xd8\xff"):
        raise HTTPException(status_code=422, detail="image type mismatch")
    if (
        payload.request.media_validation is None
        or payload.request.media_validation.decision != "PASS"
    ):
        raise HTTPException(status_code=422, detail="image admission is required")

    try:
        with tempfile.TemporaryDirectory(prefix="sketch2life-vision-") as temporary:
            suffix = ".png" if artifact.content_type == "image/png" else ".jpg"
            image_path = Path(temporary) / f"source{suffix}"
            image_path.write_bytes(image)
            relative_path = os.path.relpath(image_path.resolve(), start=Path.cwd())
            local_reference = VisionImageReferenceV1(
                artifact_ref=relative_path,
                sha256=artifact.sha256,
            )
            local_request = VisionUnderstandingRequestV2.model_validate(
                {
                    **payload.request.model_dump(mode="python"),
                    "source_image_ref": local_reference,
                }
            )
            runtime_env = dict(os.environ)
            runtime_env.setdefault(VISION_MODEL_DIR_ENV_VAR, str(VLM_ROOT))
            runtime = QwenVisionRuntimeConfig.from_env(runtime_env)
            adapter = QwenVisionAdapter(
                runtime,
                content_policy=LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
                prompt=_prompt_with_narration(payload.narration_context),
                enable_bounded_repair=False,
            )
            result = adapter.understand(local_request)
            # Keep the Lightning console useful without logging image bytes, model output,
            # prompts, credentials, or child data. HTTP 200 can still carry a typed FAILED
            # Vision result, so log the contract outcome explicitly.
            if result.status == "FAILED":
                logger.warning(
                    "vision_request_completed status=FAILED error_code=%s retryable=%s",
                    result.error_code.value,
                    result.retryable,
                )
            else:
                logger.info(
                    "vision_request_completed status=SUCCEEDED entities=%d actions=%d themes=%d",
                    len(result.entities),
                    len(result.actions),
                    len(result.themes),
                )
            wire_result = result.model_dump(mode="json")
            wire_result["source_image_ref"]["artifact_ref"] = artifact.artifact_ref
            return wire_result
    except (OSError, ValueError, RuntimeError):
        raise HTTPException(status_code=503, detail="vision runtime is unavailable") from None


def _require_auth(authorization: str | None) -> None:
    if not EXPECTED_AUTH:
        raise HTTPException(status_code=503, detail="provider authentication is not configured")
    if authorization != f"Bearer {EXPECTED_AUTH}":
        raise HTTPException(status_code=401, detail="unauthorized")


def _decode_audio(source: _SourceAudioV1) -> bytes:
    try:
        audio = base64.b64decode(source.content_base64, validate=True)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="invalid audio payload") from None
    if not audio or len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="audio size is outside the allowed range")
    if sha256(audio).hexdigest() != source.sha256:
        raise HTTPException(status_code=422, detail="source digest mismatch")
    if _audio_suffix(audio) is None:
        raise HTTPException(status_code=422, detail="audio type is unsupported")
    return audio


def _audio_suffix(audio: bytes) -> str | None:
    if audio.startswith(b"RIFF") and audio[8:12] == b"WAVE":
        return ".wav"
    if audio.startswith(b"OggS"):
        return ".ogg"
    if audio.startswith(b"\x1a\x45\xdf\xa3"):
        return ".webm"
    if len(audio) >= 12 and audio[4:8] == b"ftyp":
        return ".m4a"
    return None


def _load_asr_model():
    global _ASR_MODEL
    model_root = os.getenv("SKETCH2LIFE_ASR_MODEL_ROOT", "").strip()
    model_size = os.getenv("SKETCH2LIFE_ASR_MODEL_SIZE", "large-v3-turbo").strip()
    device = os.getenv("SKETCH2LIFE_ASR_DEVICE", "cuda").strip()
    compute_type = os.getenv("SKETCH2LIFE_ASR_COMPUTE_TYPE", "float16").strip()
    cache_key = (model_root or model_size, device, compute_type)
    if getattr(_load_asr_model, "_cache_key", None) == cache_key and _ASR_MODEL is not None:
        return _ASR_MODEL
    with _ASR_MODEL_LOCK:
        if getattr(_load_asr_model, "_cache_key", None) == cache_key and _ASR_MODEL is not None:
            return _ASR_MODEL
        from faster_whisper import WhisperModel

        _ASR_MODEL = WhisperModel(
            model_root or model_size,
            device=device,
            compute_type=compute_type,
        )
        _load_asr_model._cache_key = cache_key  # type: ignore[attr-defined]
        return _ASR_MODEL


def _asr_failure(
    request: AsrRequestV1,
    error_code: AsrErrorCode,
    error_detail: AsrErrorDetail,
    *,
    retryable: bool,
) -> AsrFailureV1:
    return AsrFailureV1(
        correlation_id=request.correlation_id,
        executed_at=datetime.now(UTC),
        source_audio_ref=request.source_audio_ref,
        profile_id=request.requested_profile_id,
        attempt_number=1,
        repair_attempted=False,
        error_code=error_code,
        retryable=retryable,
        error_detail=error_detail,
    )


@app.post("/v1/asr")
def asr_v1(
    payload: LightningAsrRequestV1,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_auth(authorization)
    reference = payload.request.source_audio_ref
    artifact = payload.source_audio
    if artifact.artifact_ref != reference.artifact_ref or artifact.sha256 != reference.sha256:
        raise HTTPException(status_code=422, detail="source identity mismatch")
    if payload.request.media_validation is None or payload.request.media_validation.decision != "PASS":
        raise HTTPException(status_code=422, detail="audio admission is required")
    audio = _decode_audio(artifact)
    suffix = _audio_suffix(audio)
    assert suffix is not None
    try:
        model = _load_asr_model()
        with tempfile.TemporaryDirectory(prefix="sketch2life-asr-") as temporary:
            audio_path = Path(temporary) / f"narration{suffix}"
            audio_path.write_bytes(audio)
            segments_raw, info = model.transcribe(
                str(audio_path),
                language=None,
                vad_filter=True,
                beam_size=int(os.getenv("SKETCH2LIFE_ASR_BEAM_SIZE", "5")),
            )
            segments = []
            for index, segment in enumerate(list(segments_raw)):
                text = str(getattr(segment, "text", "")).strip()
                if not text:
                    continue
                segments.append(
                    AsrSegmentV1(
                        index=index,
                        start_seconds=max(0.0, float(getattr(segment, "start", 0.0))),
                        end_seconds=max(
                            0.001,
                            float(getattr(segment, "end", 0.001)),
                        ),
                        text=text,
                        average_log_probability=getattr(segment, "avg_logprob", None),
                        compression_ratio=getattr(segment, "compression_ratio", None),
                        no_speech_probability=getattr(segment, "no_speech_prob", None),
                    )
                )
            duration = max(
                0.001,
                float(getattr(info, "duration", 0.0) or 0.0),
                *(segment.end_seconds for segment in segments),
            )
            transcript = " ".join(segment.text for segment in segments).strip()
            if not transcript:
                transcript = ""
            no_speech_values = [
                value
                for value in (segment.no_speech_probability for segment in segments)
                if value is not None
            ]
            logprob_values = [
                value
                for value in (segment.average_log_probability for segment in segments)
                if value is not None
            ]
            try:
                import faster_whisper

                runtime_version = str(getattr(faster_whisper, "__version__", "unknown"))
            except ImportError:
                # The model factory can be injected by an offline route test; the real
                # Lightning path has already imported faster-whisper in _load_asr_model().
                runtime_version = "unknown"
            model_identifier = os.getenv("SKETCH2LIFE_ASR_MODEL_ROOT") or os.getenv(
                "SKETCH2LIFE_ASR_MODEL_SIZE", "large-v3-turbo"
            )
            config_hash = sha256(
                (
                    f"{model_identifier}|{os.getenv('SKETCH2LIFE_ASR_DEVICE', 'cuda')}|"
                    f"{os.getenv('SKETCH2LIFE_ASR_COMPUTE_TYPE', 'float16')}|vad=true|beam=5"
                ).encode("utf-8")
            ).hexdigest()
            result = AsrSuccessV1(
                correlation_id=payload.request.correlation_id,
                executed_at=datetime.now(UTC),
                source_audio_ref=reference,
                profile_id=payload.request.requested_profile_id,
                attempt_number=1,
                repair_attempted=False,
                transcript_raw=transcript,
                speech_diagnostic=(
                    AsrSpeechDiagnostic.DETECTED
                    if segments
                    else AsrSpeechDiagnostic.NO_SPEECH_SUSPECTED
                ),
                detected_language=str(getattr(info, "language", "und") or "und"),
                language_probability=getattr(info, "language_probability", None),
                segments=tuple(segments),
                input_duration_seconds=duration,
                vad_enabled=True,
                duration_after_vad_seconds=duration if segments else 0.0,
                model_identifier=model_identifier,
                model_revision=os.getenv("SKETCH2LIFE_ASR_MODEL_REVISION", "lightning-runtime"),
                adapter_version="faster-whisper-lightning-v1",
                runtime_version=runtime_version,
                config_hash=config_hash,
                quality_metadata=AsrQualityMetadataV1(
                    media_validation_artifact_ref=payload.request.media_validation.validation_artifact_ref,
                    media_validation_artifact_sha256=payload.request.media_validation.validation_artifact_sha256,
                    mean_segment_log_probability=(
                        sum(logprob_values) / len(logprob_values) if logprob_values else None
                    ),
                    mean_no_speech_probability=(
                        sum(no_speech_values) / len(no_speech_values) if no_speech_values else None
                    ),
                ),
            )
            logger.info(
                "asr_request_completed status=SUCCEEDED segments=%d language=%s",
                len(segments),
                result.detected_language,
            )
            return result.model_dump(mode="json")
    except HTTPException:
        raise
    except ImportError:
        logger.error("asr_request_completed status=FAILED error_code=ASR_MODEL_UNAVAILABLE")
        return _asr_failure(
            payload.request,
            AsrErrorCode.ASR_MODEL_UNAVAILABLE,
            AsrErrorDetail.MODEL_LOAD_FAILED,
            retryable=False,
        ).model_dump(mode="json")
    except RuntimeError as exc:
        detail = (
            AsrErrorDetail.DEVICE_UNAVAILABLE
            if any(token in str(exc).lower() for token in ("cuda", "cudnn", "device"))
            else AsrErrorDetail.PERMANENT_RUNTIME_FAILURE
        )
        logger.error(
            "asr_request_completed status=FAILED error_code=ASR_PROVIDER_FAILURE detail=%s",
            detail.value,
        )
        return _asr_failure(
            payload.request,
            AsrErrorCode.ASR_PROVIDER_FAILURE,
            detail,
            retryable=False,
        ).model_dump(mode="json")
    except (OSError, ValueError, TypeError):
        logger.error("asr_request_completed status=FAILED error_code=ASR_PROVIDER_FAILURE")
        return _asr_failure(
            payload.request,
            AsrErrorCode.ASR_PROVIDER_FAILURE,
            AsrErrorDetail.PERMANENT_RUNTIME_FAILURE,
            retryable=False,
        ).model_dump(mode="json")


__all__ = ["app", "asr_v1", "vision_v2"]
