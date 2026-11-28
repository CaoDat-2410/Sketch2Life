"""Modal-backed ``SpeechTranscriberPort`` for the Parent and Teacher voice idea (SRS FR-P-03).

The stored audio is read by its key (the upload already passed the clean-scan step), checked
against the recorded SHA-256, staged for one attempt and removed afterwards. The transcript is
returned to the job runner only; neither it nor the audio is ever logged.
"""

from __future__ import annotations

import hashlib
import io
import uuid
from typing import Any, Final

from structlog import get_logger

from sketch2life.application.ports.object_storage import ObjectStoragePort
from sketch2life.application.ports.parent_story_inputs import (
    ASR_FAILED,
    ASR_UNAVAILABLE,
    SpeechTranscriptionFailure,
    SpeechTranscriptionRequest,
    SpeechTranscriptionResult,
)
from sketch2life.domain.ai_jobs.completion import canonical_json
from sketch2life.infrastructure.ai.modal_function_client import (
    ENVIRONMENT_NAME,
    SCRATCH_VOLUME_NAME,
)

APP_NAME: Final = "sketch2life-srs23-language-audio-dev"
FUNCTION_NAME: Final = "transcribe-vietnamese-audio"
WORKLOAD: Final = "asr.transcribe"
MODEL_ID: Final = "Systran/faster-whisper-large-v3"
MODEL_REVISION: Final = "edaa852ec7e145841d8ffdb056a99866b5f0a478"
ASR_PROFILE_REF: Final = "modal-faster-whisper-large-v3"
WAIT_SECONDS: Final = 600
MAX_AUDIO_BYTES: Final = 20_000_000
MAX_AUDIO_DURATION_MS: Final = 120_000
_ASSET_NAMES: Final = {"audio/wav": "audio.wav", "audio/mp4": "audio.m4a"}

_LOGGER = get_logger(__name__)


class ModalSpeechTranscriber:
    def __init__(
        self,
        storage: ObjectStoragePort,
        *,
        volume: Any | None = None,
        function: Any | None = None,
    ) -> None:
        self._storage = storage
        self._volume = volume
        self._function = function

    def transcribe(self, request: SpeechTranscriptionRequest) -> SpeechTranscriptionResult:
        name = _ASSET_NAMES.get(request.media_type)
        if name is None or request.duration_ms > MAX_AUDIO_DURATION_MS:
            raise SpeechTranscriptionFailure(ASR_FAILED)
        audio = self._read(request)
        job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
        prefix = f"sketch2life/{ENVIRONMENT_NAME}/{job_id}/{generation_id}/{attempt_id}/"
        manifest = canonical_json(
            {
                "schema_version": "sketch2life.modal.ai-request.v1",
                "asset": {
                    "path": f"input/{name}",
                    "content_type": request.media_type,
                    "size_bytes": len(audio),
                    "sha256": request.audio_sha256,
                },
            }
        ).encode("utf-8")
        payload = {
            "schema_version": "sketch2life.modal.worker-input.v1",
            "environment": ENVIRONMENT_NAME,
            "workload": WORKLOAD,
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "attempt_prefix": prefix,
            "input_manifest_ref": "input/manifest.json",
            "input_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "input_bytes": len(audio) + len(manifest),
        }
        try:
            volume, function = self._modal()
            with volume.batch_upload() as batch:
                batch.put_file(io.BytesIO(audio), f"/{prefix}input/{name}")
                batch.put_file(io.BytesIO(manifest), f"/{prefix}input/manifest.json")
        except Exception as exc:  # noqa: BLE001 - provider faults stay recoverable
            _LOGGER.warning("parent_speech_modal_unavailable", exception_type=type(exc).__name__)
            raise SpeechTranscriptionFailure(ASR_UNAVAILABLE) from None
        try:
            call = function.spawn(payload)
            output = call.get(timeout=WAIT_SECONDS)
        except Exception as exc:  # noqa: BLE001 - never retried; the adult types the idea instead
            _LOGGER.warning("parent_speech_modal_failed", exception_type=type(exc).__name__)
            raise SpeechTranscriptionFailure(ASR_FAILED) from None
        finally:
            try:
                volume.remove_file(f"{prefix}input", recursive=True)
            except Exception as exc:  # noqa: BLE001 - cleanup is reported, not fatal
                _LOGGER.warning(
                    "parent_speech_scratch_cleanup_failed", exception_type=type(exc).__name__
                )
        return _result(output, job_id=job_id, attempt_id=attempt_id)

    def _modal(self) -> tuple[Any, Any]:
        if self._volume is not None and self._function is not None:
            return self._volume, self._function
        import modal

        volume = self._volume or modal.Volume.from_name(
            SCRATCH_VOLUME_NAME, environment_name=ENVIRONMENT_NAME, version=2
        )
        function = self._function or modal.Function.from_name(
            APP_NAME, FUNCTION_NAME, environment_name=ENVIRONMENT_NAME
        )
        return volume, function

    def _read(self, request: SpeechTranscriptionRequest) -> bytes:
        try:
            stored = self._storage.get_object(request.audio_asset_ref)
            if stored is None or not 0 < stored.content_length <= MAX_AUDIO_BYTES:
                raise SpeechTranscriptionFailure(ASR_FAILED)
            chunks: list[bytes] = []
            total = 0
            while chunk := stored.body.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_AUDIO_BYTES:
                    raise SpeechTranscriptionFailure(ASR_FAILED)
                chunks.append(chunk)
        except SpeechTranscriptionFailure:
            raise
        except Exception as exc:  # noqa: BLE001 - a storage fault is recoverable
            _LOGGER.warning("parent_speech_storage_failed", exception_type=type(exc).__name__)
            raise SpeechTranscriptionFailure(ASR_UNAVAILABLE) from None
        audio = b"".join(chunks)
        if hashlib.sha256(audio).hexdigest() != request.audio_sha256:
            raise SpeechTranscriptionFailure(ASR_FAILED)
        return audio


def _result(output: Any, *, job_id: str, attempt_id: str) -> SpeechTranscriptionResult:
    if (
        not isinstance(output, dict)
        or output.get("workload") != WORKLOAD
        or output.get("job_id") != job_id
        or output.get("attempt_id") != attempt_id
        or output.get("model") != {"id": MODEL_ID, "revision": MODEL_REVISION}
    ):
        raise SpeechTranscriptionFailure(ASR_FAILED)
    result = output.get("result")
    text = result.get("text") if isinstance(result, dict) else None
    if not isinstance(result, dict) or not isinstance(text, str):
        raise SpeechTranscriptionFailure(ASR_FAILED)
    timing: list[dict[str, int]] = []
    for segment in result.get("segments") or []:
        start, end = segment.get("start_seconds"), segment.get("end_seconds")
        if isinstance(start, int | float) and isinstance(end, int | float):
            timing.append({"start_ms": round(start * 1000), "end_ms": round(end * 1000)})
    language = result.get("language")
    return SpeechTranscriptionResult(
        text=text,
        language=language if isinstance(language, str) else "vi",
        model_revision=MODEL_REVISION,
        asr_profile_ref=ASR_PROFILE_REF,
        segment_timing=tuple(timing) or None,
    )


__all__ = ["ModalSpeechTranscriber"]
