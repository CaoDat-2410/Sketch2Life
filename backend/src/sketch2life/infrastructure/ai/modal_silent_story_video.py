"""Adapter for the deployed dev-only silent LTX story-video worker."""

from __future__ import annotations

import io
import logging
import time
from typing import Any

from sketch2life.application.ports.parent_video_candidates import (
    SilentStoryWorkerOutput,
)

_LOGGER = logging.getLogger(__name__)
_APP_NAME = "sketch2life-srs23-dev-video"
_FUNCTION_NAME = "generate-silent-story-video"
_ENVIRONMENT = "dev"
_SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
_VOLUME_VERSION = 2
_MAX_OUTPUT_BYTES = 256 * 1024 * 1024
_MAX_MANIFEST_BYTES = 64 * 1024


class ModalSilentStoryVideoWorker:
    """Upload one manifest and drawing, then spawn/poll the deployed Modal function."""

    def __init__(
        self,
        *,
        volume: Any | None = None,
        function_resolver: Any | None = None,
        call_resolver: Any | None = None,
    ) -> None:
        self._volume = volume
        self._function_resolver = function_resolver
        self._call_resolver = call_resolver

    def dispatch(
        self,
        *,
        worker_input: dict[str, Any],
        drawing_bytes: bytes,
        manifest_bytes: bytes,
    ) -> str:
        if not drawing_bytes or len(drawing_bytes) > 20 * 1024 * 1024:
            raise ValueError("VIDEO_DRAWING_INPUT_LIMIT_EXCEEDED")
        if not manifest_bytes or len(manifest_bytes) > _MAX_MANIFEST_BYTES:
            raise ValueError("VIDEO_MANIFEST_INPUT_LIMIT_EXCEEDED")

        volume = self._resolve_volume()
        started = time.perf_counter()
        _LOGGER.info(
            "modal_video_candidate_upload_started job_id=%s generation_id=%s "
            "attempt_id=%s drawing_bytes=%s manifest_bytes=%s",
            worker_input.get("job_id"),
            worker_input.get("generation_id"),
            worker_input.get("attempt_id"),
            len(drawing_bytes),
            len(manifest_bytes),
        )
        attempt_prefix = _validated_attempt_prefix(worker_input)
        try:
            with volume.batch_upload() as batch:
                batch.put_file(
                    io.BytesIO(drawing_bytes),
                    f"/{attempt_prefix}input/drawing.png",
                )
                batch.put_file(
                    io.BytesIO(manifest_bytes),
                    f"/{attempt_prefix}input/manifest.json",
                )
        except Exception as exc:  # noqa: BLE001 - provider errors are never sent to the UI.
            _LOGGER.error(
                "modal_video_candidate_upload_failed job_id=%s generation_id=%s "
                "attempt_id=%s exception_type=%s elapsed_ms=%s",
                worker_input.get("job_id"),
                worker_input.get("generation_id"),
                worker_input.get("attempt_id"),
                type(exc).__name__,
                round((time.perf_counter() - started) * 1000),
            )
            raise RuntimeError("MODAL_VIDEO_INPUT_STAGE_FAILED") from None

        function = self._resolve_function()
        _LOGGER.info(
            "modal_video_candidate_upload_completed job_id=%s generation_id=%s "
            "attempt_id=%s elapsed_ms=%s",
            worker_input.get("job_id"),
            worker_input.get("generation_id"),
            worker_input.get("attempt_id"),
            round((time.perf_counter() - started) * 1000),
        )
        try:
            call = function.spawn(worker_input)
        except Exception as exc:  # noqa: BLE001 - spawn outcome may be ambiguous.
            _LOGGER.error(
                "modal_video_candidate_spawn_unknown job_id=%s generation_id=%s "
                "attempt_id=%s exception_type=%s elapsed_ms=%s",
                worker_input.get("job_id"),
                worker_input.get("generation_id"),
                worker_input.get("attempt_id"),
                type(exc).__name__,
                round((time.perf_counter() - started) * 1000),
            )
            raise RuntimeError("MODAL_VIDEO_DISPATCH_OUTCOME_UNKNOWN") from None
        call_id = getattr(call, "object_id", None)
        if not isinstance(call_id, str) or not call_id.startswith("fc-") or len(call_id) > 128:
            raise RuntimeError("MODAL_VIDEO_CALL_REFERENCE_INVALID")
        _LOGGER.info(
            "modal_video_candidate_spawned modal_call_id=%s job_id=%s "
            "generation_id=%s attempt_id=%s elapsed_ms=%s",
            call_id,
            worker_input.get("job_id"),
            worker_input.get("generation_id"),
            worker_input.get("attempt_id"),
            round((time.perf_counter() - started) * 1000),
        )
        return call_id

    def collect_if_ready(
        self,
        *,
        modal_call_id: str,
        job_id: str,
        generation_id: str,
        attempt_id: str,
        attempt_prefix: str,
    ) -> SilentStoryWorkerOutput | None:
        if not modal_call_id.startswith("fc-") or len(modal_call_id) > 128:
            raise ValueError("MODAL_VIDEO_CALL_REFERENCE_INVALID")
        if not _valid_prefix(attempt_prefix):
            raise ValueError("MODAL_VIDEO_ATTEMPT_PREFIX_INVALID")
        started = time.perf_counter()
        try:
            call = self._resolve_call(modal_call_id)
            result = call.get(timeout=0)
        except TimeoutError:
            _LOGGER.info(
                "modal_video_candidate_pending modal_call_id=%s job_id=%s "
                "generation_id=%s attempt_id=%s",
                modal_call_id,
                job_id,
                generation_id,
                attempt_id,
            )
            return None
        except Exception as exc:  # noqa: BLE001 - terminal worker/provider detail stays private.
            _LOGGER.error(
                "modal_video_candidate_worker_failed modal_call_id=%s job_id=%s "
                "generation_id=%s attempt_id=%s exception_type=%s elapsed_ms=%s",
                modal_call_id,
                job_id,
                generation_id,
                attempt_id,
                type(exc).__name__,
                round((time.perf_counter() - started) * 1000),
            )
            raise RuntimeError("MODAL_VIDEO_WORKER_FAILED") from None

        if not isinstance(result, dict):
            raise RuntimeError("MODAL_VIDEO_WORKER_OUTPUT_INVALID")
        if (
            result.get("job_id") != job_id
            or result.get("generation_id") != generation_id
            or result.get("attempt_id") != attempt_id
        ):
            raise RuntimeError("MODAL_VIDEO_WORKER_OUTPUT_ID_MISMATCH")

        volume = self._resolve_volume()
        try:
            video_bytes = _read_volume_file(
                volume,
                f"{attempt_prefix}output/video.mp4",
                maximum_bytes=_MAX_OUTPUT_BYTES,
            )
            manifest_bytes = _read_volume_file(
                volume,
                f"{attempt_prefix}output/video-manifest.json",
                maximum_bytes=_MAX_MANIFEST_BYTES,
            )
        except Exception as exc:  # noqa: BLE001 - no file content/provider detail is logged.
            _LOGGER.error(
                "modal_video_candidate_output_read_failed modal_call_id=%s job_id=%s "
                "generation_id=%s attempt_id=%s exception_type=%s elapsed_ms=%s",
                modal_call_id,
                job_id,
                generation_id,
                attempt_id,
                type(exc).__name__,
                round((time.perf_counter() - started) * 1000),
            )
            raise RuntimeError("MODAL_VIDEO_OUTPUT_UNAVAILABLE") from None
        _LOGGER.info(
            "modal_video_candidate_output_read modal_call_id=%s job_id=%s "
            "generation_id=%s attempt_id=%s video_bytes=%s manifest_bytes=%s "
            "elapsed_ms=%s",
            modal_call_id,
            job_id,
            generation_id,
            attempt_id,
            len(video_bytes),
            len(manifest_bytes),
            round((time.perf_counter() - started) * 1000),
        )
        return SilentStoryWorkerOutput(
            result=result,
            output_manifest_bytes=manifest_bytes,
            video_bytes=video_bytes,
        )

    def _resolve_volume(self) -> Any:
        if self._volume is not None:
            return self._volume
        import modal

        self._volume = modal.Volume.from_name(
            _SCRATCH_VOLUME,
            environment_name=_ENVIRONMENT,
            version=_VOLUME_VERSION,
        )
        return self._volume

    def _resolve_function(self) -> Any:
        if self._function_resolver is not None:
            return self._function_resolver(_APP_NAME, _FUNCTION_NAME)
        import modal

        return modal.Function.from_name(
            _APP_NAME,
            _FUNCTION_NAME,
            environment_name=_ENVIRONMENT,
        )

    def _resolve_call(self, call_id: str) -> Any:
        if self._call_resolver is not None:
            return self._call_resolver(call_id)
        import modal

        return modal.FunctionCall.from_id(call_id)


def _validated_attempt_prefix(worker_input: dict[str, Any]) -> str:
    prefix = worker_input.get("attempt_prefix")
    if not _valid_prefix(prefix):
        raise ValueError("MODAL_VIDEO_ATTEMPT_PREFIX_INVALID")
    return prefix


def _valid_prefix(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sketch2life/dev/")
        and value.endswith("/")
        and len(value) <= 256
        and all(part not in {"", ".", ".."} for part in value.rstrip("/").split("/"))
    )


def _read_volume_file(volume: Any, path: str, *, maximum_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in volume.read_file(path):
        if not isinstance(chunk, bytes):
            raise ValueError("MODAL_VOLUME_READ_INVALID")
        total += len(chunk)
        if total > maximum_bytes:
            raise ValueError("MODAL_VOLUME_FILE_LIMIT_EXCEEDED")
        chunks.append(chunk)
    if total == 0:
        raise ValueError("MODAL_VOLUME_FILE_EMPTY")
    return b"".join(chunks)


__all__ = ["ModalSilentStoryVideoWorker"]
