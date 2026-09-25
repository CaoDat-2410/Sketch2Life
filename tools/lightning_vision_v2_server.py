"""Lightning Vision V2 + faster-whisper ASR service for the FEAT-018 demo.

Deploy this service in the configured Lightning environment. It exposes only the explicit
image-understanding and optional narration-ASR routes. Provider output, transcripts, credentials,
and temporary media files are never logged.
"""

from __future__ import annotations

import base64
import json
import logging
import math
import os
import re
import sys
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    VisionMappingDiagnosticV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_v2,
)
from sketch2life.infrastructure.ai.qwen_vision import (
    KillableSubprocessQwenGenerationRunner,
    QwenDeviceUnavailableError,
    QwenModelLoadError,
    QwenPermanentRuntimeError,
    QwenTimeoutError,
    QwenVisionAdapter,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import (
    VISION_MODEL_CACHE_DIR_ENV_VAR,
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
_OPERATOR_MODEL_DIR_ENV_VAR = "MODEL_DIR"
logger = logging.getLogger("sketch2life.lightning_vision_v2")
_ASR_MODEL_LOCK = Lock()
_ASR_MODEL = None

_PROMPT = """Return exactly one strict JSON object and no surrounding text. Analyze visible marks in
this synthetic, non-child drawing. Do not infer a child's personality, emotions, intent, diagnosis,
ability, development, or mental state.
Use exactly these root keys: entities, actions, relations, themes, ambiguous_regions. Use arrays;
use [] when uncertain. Maximums: 5 entities, 2 actions, 3 relations, 2 themes, 2 ambiguous regions.
Prioritize entities in this order: (1) the most specific, central, visually recognizable subject,
(2) other concrete subjects, and (3) scenery/background such as grass, sky, or broad nature labels.
Keep the main subject first in entities; keep scenery/background last. Use concise Vietnamese
labels whenever the object is recognizable (for example "con chim", "cành cây", "chiếc lá",
"đậu trên cành"). Prefer a specific visible label such as "con bướm" or "bông hoa" over a broad
label such as "thiên nhiên". Never repeat the same normalized entity, action, or theme. Do not emit
an aggregate phrase such as "chim trên cành" when the same bird, branch, and relation/action are
already represented separately. Emit an action only when
it is visibly anchored to an entity, and emit a theme only when it describes concrete scene context.
Do not use a background label as the main subject when a specific subject is visible.
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
inventing them. If the drawing contains any recognizable visible mark, emit at least one concrete
grounded entity; do not return all five arrays empty for a non-empty admitted image."""

_LOCALIZATION_PROMPT = """Return exactly one strict JSON object and no surrounding text.
Locate only the listed visible drawing subjects. Do not invent a subject that is not visibly
present. Use exactly one root key: regions. Each region must contain target_ref, x, y, width,
height, confidence. Coordinates are normalized to the full source image: x/y is the top-left,
width/height are positive and every rectangle must stay inside 0..1. Return at most one region
per target_ref and omit targets that cannot be located confidently. Prefer a tight rectangle around
the visible subject, including its full hand-drawn mark but little background. The allowed target
refs and Vietnamese labels are supplied below. Copy target_ref exactly from the allowed target
refs; never replace it with the label. Confidence must be a decimal number from 0 to 1, never a
percentage. Do not emit markdown, explanations, masks, pixels, or any other keys."""

_LOCALIZATION_FENCE_PATTERN = re.compile(
    r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE
)


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


def _repair_prompt_with_diagnostics(
    _request: VisionUnderstandingRequestV2,
    diagnostics: tuple[VisionMappingDiagnosticV2, ...],
) -> str:
    """Build a closed repair prompt without echoing model/provider/user content."""

    tokens = tuple(dict.fromkeys(item.value for item in diagnostics))
    diagnostic_text = ", ".join(tokens) or "SCHEMA_TYPE_OR_CONSTRAINT_INVALID"
    return (
        f"{_PROMPT}\n\n"
        "The previous response failed the output contract. Repair only the JSON shape. "
        "Do not add explanations, markdown, metadata, or new scene claims. "
        f"Closed diagnostic categories: {diagnostic_text}."
    )


def _semantic_empty_repair_prompt(_request: VisionUnderstandingRequestV2) -> str:
    """Ask for one bounded re-inspection without echoing content or widening the schema."""

    return (
        f"{_PROMPT}\n\n"
        "The previous response was valid JSON but contained no grounded observations. Re-inspect "
        "the visible drawing carefully and emit at least one concrete entity when a recognizable "
        "mark is present. Use a broad visible label only when necessary. Do not invent claims, "
        "do not add explanations, and do not return all arrays empty for a non-empty image. "
        "This is a closed semantic-empty repair; keep the exact JSON contract."
    )


def _quality_repair_prompt(
    _request: VisionUnderstandingRequestV2,
    narration_context: str | None,
) -> str:
    return (
        f"{_prompt_with_narration(narration_context)}\n\n"
        "The previous response passed the schema but was too broad, duplicated labels, or missed "
        "a clearly narrated visible subject. Re-inspect the drawing once. Put the specific central "
        "subject first, use concise Vietnamese labels, remove semantic duplicates, and connect a "
        "visible action to its entity. Keep only image-grounded observations and the exact schema."
    )


def _needs_quality_repair(
    result: VisionUnderstandingSuccessV2,
    narration_context: str | None,
) -> bool:
    labels = [item.label.value.casefold().strip() for item in result.entities]
    actions = [item.label.value.casefold().strip() for item in result.actions]
    themes = [item.label.value.casefold().strip() for item in result.themes]
    if len(labels) != len(set(labels)) or len(actions) != len(set(actions)):
        return True
    if len(themes) != len(set(themes)):
        return True
    broad = {"nature", "thiên nhiên", "outdoor scene", "khung cảnh ngoài trời", "background"}
    if labels and labels[0] in broad and any(label not in broad for label in labels[1:]):
        return True
    narration = (narration_context or "").casefold()
    narrated_subjects = (
        ({"bird", "chim"}, {"bird", "chim"}),
        ({"butterfly", "bướm"}, {"butterfly", "bướm"}),
        ({"flower", "hoa"}, {"flower", "hoa"}),
    )
    all_labels = " ".join(labels)
    return any(
        any(token in narration for token in narration_tokens)
        and not any(token in all_labels for token in output_tokens)
        for narration_tokens, output_tokens in narrated_subjects
    )


def _vision_runtime_environment(environ: Mapping[str, str]) -> dict[str, str]:
    """Resolve the live model path without treating a blank env value as configured."""

    runtime_env = dict(environ)
    model_dir = runtime_env.get(VISION_MODEL_DIR_ENV_VAR, "").strip()
    cache_dir = runtime_env.get(VISION_MODEL_CACHE_DIR_ENV_VAR, "").strip()
    if not model_dir and not cache_dir:
        for env_name in (_OPERATOR_MODEL_DIR_ENV_VAR, "SKETCH2LIFE_VLM_ROOT"):
            candidate = runtime_env.get(env_name, "").strip()
            if candidate:
                runtime_env[VISION_MODEL_DIR_ENV_VAR] = candidate
                break
        else:
            runtime_env[VISION_MODEL_DIR_ENV_VAR] = str(VLM_ROOT)
    return runtime_env


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


class _LocalizationRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["SceneLocalizationRequestV1"] = "SceneLocalizationRequestV1"
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=120)
    experience_spec_ref: dict[str, object] | None = None
    source_image: _SourceImageV1
    targets: list[str] = Field(min_length=1, max_length=3)
    target_labels: dict[str, str] = Field(default_factory=dict, max_length=3)


class _LocalizationRegionV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target_ref: str = Field(min_length=1, max_length=120)
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_inside(self) -> _LocalizationRegionV1:
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("region outside source")
        return self


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


@app.exception_handler(RequestValidationError)
async def request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Log only safe field locations for malformed provider requests."""

    fields: list[str] = []
    for error in exc.errors():
        location = ".".join(
            str(part) for part in error.get("loc", ()) if str(part) not in {"body"}
        )
        if location and location not in fields:
            fields.append(location)
    logger.warning(
        "request_validation_failed path=%s fields=%s",
        request.url.path,
        ",".join(fields) or "UNKNOWN",
    )
    return JSONResponse(status_code=422, content={"detail": "request contract invalid"})


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
            runtime_env = _vision_runtime_environment(os.environ)
            runtime = QwenVisionRuntimeConfig.from_env(runtime_env)
            mapping_diagnostics: list[str] = []

            def capture_mapping_diagnostics(items: tuple[object, ...]) -> None:
                for item in items:
                    value = getattr(item, "value", None)
                    if isinstance(value, str) and value not in mapping_diagnostics:
                        mapping_diagnostics.append(value)

            adapter = QwenVisionAdapter(
                runtime,
                content_policy=LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
                prompt=_prompt_with_narration(payload.narration_context),
                repair_prompt_builder=_repair_prompt_with_diagnostics,
                semantic_empty_repair_prompt_builder=_semantic_empty_repair_prompt,
                quality_repair_prompt_builder=lambda request: _quality_repair_prompt(
                    request, payload.narration_context
                ),
                quality_repair_predicate=lambda result: _needs_quality_repair(
                    result, payload.narration_context
                ),
                on_mapping_diagnostic=capture_mapping_diagnostics,
                enable_bounded_repair=True,
            )
            result = adapter.understand(local_request)
            # Keep the Lightning console useful without logging image bytes, model output,
            # prompts, credentials, or child data. HTTP 200 can still carry a typed FAILED
            # Vision result, so log the contract outcome explicitly.
            diagnostics_text = ",".join(mapping_diagnostics) or "NONE"
            if result.status == "FAILED":
                logger.warning(
                    "vision_request_completed status=FAILED error_code=%s error_detail=%s "
                    "retryable=%s attempt=%s repair_attempted=%s mapping_diagnostics=%s",
                    result.error_code.value,
                    result.error_detail.value,
                    result.retryable,
                    result.attempt_number,
                    result.repair_attempted,
                    diagnostics_text,
                )
            else:
                logger.info(
                    "vision_request_completed status=SUCCEEDED entities=%d actions=%d themes=%d "
                    "attempt=%s repair_attempted=%s mapping_diagnostics=%s",
                    len(result.entities),
                    len(result.actions),
                    len(result.themes),
                    result.attempt_number,
                    result.repair_attempted,
                    diagnostics_text,
                )
            wire_result = result.model_dump(mode="json")
            wire_result["source_image_ref"]["artifact_ref"] = artifact.artifact_ref
            return wire_result
    except (OSError, ValueError, RuntimeError):
        raise HTTPException(status_code=503, detail="vision runtime is unavailable") from None


@app.post("/v2/localize")
def localize_v2(
    payload: _LocalizationRequestV1,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    """Run one bounded geometry pass for confirmed semantic subjects."""

    _require_auth(authorization)
    artifact = payload.source_image
    try:
        image = base64.b64decode(artifact.content_base64, validate=True)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="invalid image payload") from None
    if not image or len(image) > MAX_INPUT_BYTES or sha256(image).hexdigest() != artifact.sha256:
        raise HTTPException(status_code=422, detail="source image integrity check failed")
    if artifact.content_type == "image/png" and not image.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=422, detail="image type mismatch")
    if artifact.content_type == "image/jpeg" and not image.startswith(b"\xff\xd8\xff"):
        raise HTTPException(status_code=422, detail="image type mismatch")
    labels = {
        target: payload.target_labels.get(target, target)
        for target in payload.targets
    }
    prompt = (
        f"{_LOCALIZATION_PROMPT}\n\nALLOWED TARGETS (use exact target_ref):\n"
        + "\n".join(f"- {target}: {label}" for target, label in labels.items())
    )
    try:
        with tempfile.TemporaryDirectory(prefix="sketch2life-localize-") as temporary:
            suffix = ".png" if artifact.content_type == "image/png" else ".jpg"
            image_path = Path(temporary) / f"source{suffix}"
            image_path.write_bytes(image)
            runtime = QwenVisionRuntimeConfig.from_env(_vision_runtime_environment(os.environ))
            profile = vision_profile_catalog_v2().resolve(
                next(iter(vision_profile_catalog_v2().profiles)).profile_id
            )
            raw_output = KillableSubprocessQwenGenerationRunner().generate(
                profile,
                runtime,
                image_path,
                prompt,
            )
        parsed_regions = _parse_localization_output(raw_output)
        regions: list[dict[str, object]] = []
        seen: set[str] = set()
        for region in parsed_regions:
            target_ref = _resolve_localization_target_ref(region.target_ref, payload)
            if target_ref in seen:
                raise ValueError("localization target invalid")
            seen.add(target_ref)
            regions.append(
                {
                    "target_ref": target_ref,
                    "region": {
                        "x": region.x,
                        "y": region.y,
                        "width": region.width,
                        "height": region.height,
                    },
                    "confidence": region.confidence,
                }
            )
        return {
            "contract_name": "SceneLocalizationResultV1",
            "contract_version": "1.0",
            "regions": regions[:3],
        }
    except json.JSONDecodeError:
        return _localization_fallback("MODEL_OUTPUT_JSON_INVALID")
    except TypeError:
        return _localization_fallback("MODEL_OUTPUT_SCHEMA_INVALID")
    except ValueError:
        return _localization_fallback("MODEL_OUTPUT_REGION_INVALID")
    except QwenTimeoutError:
        return _localization_fallback("MODEL_RUNTIME_TIMEOUT")
    except (QwenModelLoadError, QwenDeviceUnavailableError):
        return _localization_fallback("MODEL_UNAVAILABLE")
    except (OSError, QwenPermanentRuntimeError, RuntimeError):
        return _localization_fallback("MODEL_RUNTIME_FAILURE")


def _parse_localization_output(raw_output: str) -> list[_LocalizationRegionV1]:
    """Accept bounded JSON and harmless provider formatting variants only."""

    text = raw_output.strip()
    fence_match = _LOCALIZATION_FENCE_PATTERN.fullmatch(text)
    if fence_match is not None:
        text = fence_match.group(1).strip()
    decoded = json.loads(text)
    if not isinstance(decoded, dict) or not isinstance(decoded.get("regions"), list):
        raise TypeError("localization schema invalid")

    parsed: list[_LocalizationRegionV1] = []
    for item in decoded["regions"]:
        if not isinstance(item, dict):
            raise TypeError("localization item invalid")
        normalized = item
        nested = item.get("region")
        if nested is not None:
            if not isinstance(nested, dict):
                raise TypeError("localization region invalid")
            if set(item) != {"target_ref", "region", "confidence"}:
                raise TypeError("localization item has unexpected keys")
            if set(nested) != {"x", "y", "width", "height"}:
                raise TypeError("localization region has unexpected keys")
            normalized = {
                "target_ref": item.get("target_ref"),
                "x": nested.get("x"),
                "y": nested.get("y"),
                "width": nested.get("width"),
                "height": nested.get("height"),
                "confidence": item.get("confidence"),
            }
        confidence = normalized.get("confidence")
        if (
            isinstance(confidence, (int, float))
            and not isinstance(confidence, bool)
            and 1 < confidence <= 100
        ):
            normalized = {**normalized, "confidence": confidence / 100}
        coordinates = {
            key: normalized.get(key) for key in ("x", "y", "width", "height")
        }
        if all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in coordinates.values()
        ):
            normalized_coordinates = {
                key: _normalize_localization_scalar(float(value))
                for key, value in coordinates.items()
            }
            if any(value > 1.0 for value in normalized_coordinates.values()):
                raise ValueError("localization coordinate unit is unsupported")
            x = min(max(normalized_coordinates["x"], 0.0), 1.0)
            y = min(max(normalized_coordinates["y"], 0.0), 1.0)
            normalized = {
                **normalized,
                "x": x,
                "y": y,
                "width": min(normalized_coordinates["width"], 1.0 - x),
                "height": min(normalized_coordinates["height"], 1.0 - y),
            }
        parsed.append(_LocalizationRegionV1.model_validate(normalized))
    return parsed


def _normalize_localization_scalar(value: float) -> float:
    if not math.isfinite(value):
        return value
    if 1.0 < value <= 100.0:
        return value / 100.0
    return value


def _resolve_localization_target_ref(
    target_ref: str, payload: _LocalizationRequestV1
) -> str:
    if target_ref in payload.targets:
        return target_ref
    normalized = target_ref.strip().casefold()
    matches = [
        candidate
        for candidate in payload.targets
        if payload.target_labels.get(candidate, "").strip().casefold() == normalized
    ]
    if len(matches) == 1:
        return matches[0]
    raise ValueError("localization target invalid")


def _localization_fallback(reason: str) -> dict[str, object]:
    logger.warning("localization_request_completed status=FALLBACK reason=%s", reason)
    return {
        "contract_name": "SceneLocalizationResultV1",
        "contract_version": "1.0",
        "status": "FALLBACK_REQUIRED",
        "regions": [],
        "fallback_reason": reason,
    }


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
                ).encode()
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
