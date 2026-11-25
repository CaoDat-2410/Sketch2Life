"""C2 adapter: synthesise one narration clause with the deployed ``synthesize-narration-clause`` function (FEAT-093).

Implements ``NarrationPort``. The clause is staged as ``input/request.json`` on the scratch volume, the call is awaited
and the WAV comes back in the worker response; its hash is verified. Failures are ``VideoPipelineError`` codes only.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import uuid
from collections.abc import Callable
from typing import Any, Final

from sketch2life.application.video_pipeline.ports import VideoPipelineError
from sketch2life.infrastructure.ai.modal_function_client import APP_NAME as LANGUAGE_AUDIO_APP_NAME
from sketch2life.infrastructure.ai.modal_silent_story_video import (
    _ENVIRONMENT,
    _SCRATCH_VOLUME,
    _VOLUME_VERSION,
)

FUNCTION_NAME: Final = "synthesize-narration-clause"
MANIFEST_SCHEMA: Final = "sketch2life.modal.ai-request.v1"
WORKER_INPUT_SCHEMA: Final = "sketch2life.modal.worker-input.v1"
WORKER_OUTPUT_SCHEMA: Final = "sketch2life.modal.worker-output.v1"
WORKLOAD: Final = "tts.narration.generate"
VOICE: Final = "Hải Đăng"
CLAUSE_MAX_CHARS: Final = 100
WAIT_TIMEOUT_SECONDS: Final = 280
APP_NAME: Final = LANGUAGE_AUDIO_APP_NAME


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ModalNarrationSynthesizer:
    """``NarrationPort`` on the CPU narration container."""

    def __init__(
        self,
        *,
        volume: Any | None = None,
        function: Any | None = None,
        timeout_seconds: float = WAIT_TIMEOUT_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._volume = volume
        self._function = function
        self._timeout = timeout_seconds
        self._sleep = sleep

    def synthesize(self, spoken_text: str) -> bytes:
        text = spoken_text.strip()
        if not text or len(text) > CLAUSE_MAX_CHARS:
            raise VideoPipelineError("VIDEO_NARRATION_CLAUSE_INVALID")
        request_bytes = _canonical({"text": text, "voice": VOICE})
        manifest = {
            "schema_version": MANIFEST_SCHEMA,
            "asset": {
                "path": "input/request.json",
                "content_type": "application/json",
                "size_bytes": len(request_bytes),
                "sha256": hashlib.sha256(request_bytes).hexdigest(),
            },
        }
        manifest_bytes = _canonical(manifest)
        job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
        prefix = f"sketch2life/{_ENVIRONMENT}/{job_id}/{generation_id}/{attempt_id}/"
        worker_input = {
            "schema_version": WORKER_INPUT_SCHEMA,
            "environment": _ENVIRONMENT,
            "workload": WORKLOAD,
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "attempt_prefix": prefix,
            "input_manifest_ref": "input/manifest.json",
            "input_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "input_bytes": len(request_bytes) + len(manifest_bytes),
        }
        try:
            with self._resolve_volume().batch_upload() as batch:
                batch.put_file(io.BytesIO(request_bytes), f"/{prefix}input/request.json")
                batch.put_file(io.BytesIO(manifest_bytes), f"/{prefix}input/manifest.json")
        except Exception:  # noqa: BLE001 - provider detail never leaves this layer
            raise VideoPipelineError("VIDEO_NARRATION_STAGING_FAILED") from None
        try:
            call = self._resolve_function().spawn(worker_input)
        except Exception:  # noqa: BLE001
            raise VideoPipelineError("VIDEO_NARRATION_DISPATCH_UNKNOWN") from None
        deadline = time.monotonic() + self._timeout
        while True:
            try:
                result = call.get(timeout=0)
                break
            except TimeoutError:
                if time.monotonic() >= deadline:
                    raise VideoPipelineError("VIDEO_NARRATION_TIMEOUT") from None
                self._sleep(1.0)
            except Exception:  # noqa: BLE001
                raise VideoPipelineError("VIDEO_NARRATION_FAILED") from None
        asset = result.get("asset") if isinstance(result, dict) else None
        if (
            not isinstance(result, dict)
            or result.get("schema_version") != WORKER_OUTPUT_SCHEMA
            or result.get("job_id") != job_id
            or result.get("attempt_id") != attempt_id
            or not isinstance(asset, dict)
            or asset.get("content_type") != "audio/wav"
            or not isinstance(asset.get("bytes"), bytes)
        ):
            raise VideoPipelineError("VIDEO_NARRATION_OUTPUT_INVALID")
        audio: bytes = asset["bytes"]
        if hashlib.sha256(audio).hexdigest() != asset.get("sha256") or len(audio) != asset.get("size_bytes"):
            raise VideoPipelineError("VIDEO_NARRATION_HASH_MISMATCH")
        return audio

    def _resolve_volume(self) -> Any:
        if self._volume is None:
            import modal

            self._volume = modal.Volume.from_name(_SCRATCH_VOLUME, environment_name=_ENVIRONMENT, version=_VOLUME_VERSION)
        return self._volume

    def _resolve_function(self) -> Any:
        if self._function is None:
            import modal

            self._function = modal.Function.from_name(APP_NAME, FUNCTION_NAME, environment_name=_ENVIRONMENT)
        return self._function


__all__ = ["ModalNarrationSynthesizer"]
