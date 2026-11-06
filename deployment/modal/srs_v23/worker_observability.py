"""Privacy-safe lifecycle events for synthetic Modal AI workers."""

from __future__ import annotations

import contextvars
import hashlib
import json
import re
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import wraps
from typing import Any, TypeVar

EVENT_SCHEMA = "sketch2life.modal.worker-event.v1"
_OPAQUE_ID = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z")
_SAFE_CODE = re.compile(r"\A[A-Z][A-Z0-9_]{2,95}\Z")
_SAFE_STAGE = re.compile(r"\A[a-z][a-z0-9_]{1,63}\Z")
_ACTIVE_RUN: contextvars.ContextVar[WorkerRun | None] = contextvars.ContextVar(
    "modal_worker_run", default=None
)
_F = TypeVar("_F", bound=Callable[..., Any])


def _safe_identity(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict):
        return {}
    result: dict[str, str] = {}
    for key in ("job_id", "generation_id", "attempt_id"):
        value = payload.get(key)
        if isinstance(value, str) and _OPAQUE_ID.fullmatch(value):
            ref_key = {
                "job_id": "job_ref",
                "generation_id": "generation_ref",
                "attempt_id": "attempt_ref",
            }[key]
            result[ref_key] = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return result


def _error_code(exc: BaseException) -> str:
    candidate = getattr(exc, "reason_code", None) or getattr(exc, "code", None)
    if candidate is None and isinstance(exc, (ValueError, RuntimeError)):
        candidate = str(exc)
    if isinstance(candidate, str) and _SAFE_CODE.fullmatch(candidate):
        return candidate
    if isinstance(exc, TimeoutError):
        return "WORKER_TIMEOUT"
    if isinstance(exc, ImportError):
        return "WORKER_DEPENDENCY_IMPORT_ERROR"
    if isinstance(exc, OSError):
        return "WORKER_IO_ERROR"
    if isinstance(exc, ValueError):
        return "WORKER_VALUE_ERROR"
    return "UNCLASSIFIED_FAILURE"


def _binary_size(value: Any) -> int:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return len(value)
    if isinstance(value, dict):
        return sum(_binary_size(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return sum(_binary_size(item) for item in value)
    return 0



def _binary_sha256(value: Any) -> str | None:
    digest = hashlib.sha256()
    count = 0

    def visit(item: Any) -> None:
        nonlocal count
        if isinstance(item, (bytes, bytearray, memoryview)):
            data = bytes(item)
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
            count += 1
        elif isinstance(item, dict):
            for key in sorted(item, key=str):
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            for nested in item:
                visit(nested)

    visit(value)
    return digest.hexdigest() if count else None

def _json_shape(value: Any) -> Any:
    """Replace binary leaves without retaining any generated text or media bytes."""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {"binary_size_bytes": len(value)}
    if isinstance(value, dict):
        return {str(key): _json_shape(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_shape(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return type(value).__name__


class WorkerRun:
    """One invocation's allowlisted lifecycle and phase timing."""

    def __init__(
        self,
        *,
        workload: str,
        model_id: str,
        model_revision: str,
        gpu_class: str,
        payload: Any,
    ) -> None:
        self.workload = workload
        self.model_id = model_id
        self.model_revision = model_revision
        self.gpu_class = gpu_class
        self.identity = _safe_identity(payload)
        self.started = time.perf_counter()
        self.current_stage = "worker_entrypoint"
        self.failed_stage: str | None = None
        self._active_stage_started: float | None = None

    def emit(self, event: str, **fields: Any) -> None:
        record: dict[str, Any] = {
            "schema_version": EVENT_SCHEMA,
            "event": event,
            "workload": self.workload,
            **self.identity,
            "stage": self.current_stage,
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        if self.model_id:
            record["model_id"] = self.model_id
        if self.model_revision:
            record["model_revision"] = self.model_revision
        if self.gpu_class:
            record["gpu_class"] = self.gpu_class
        allowed = {
            "duration_ms",
            "error_code",
            "error_type",
            "output_kind",
            "output_size_bytes",
            "binary_output_bytes",
            "output_sha256",
            "binary_output_sha256",
        }
        record.update({key: value for key, value in fields.items() if key in allowed})
        print(
            json.dumps(record, ensure_ascii=True, separators=(",", ":")),
            file=sys.stdout,
            flush=True,
        )

    def start(self) -> None:
        self.emit("worker_started")

    def succeed(self, output: Any) -> None:
        self.finish_stage()
        binary_size = _binary_size(output)
        try:
            json_size = len(
                json.dumps(
                    _json_shape(output), ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")
            )
        except (TypeError, ValueError):
            json_size = 0
        try:
            output_shape = json.dumps(
                _json_shape(output),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            output_sha256 = hashlib.sha256(output_shape).hexdigest()
        except (TypeError, ValueError):
            output_sha256 = None
        binary_output_sha256 = _binary_sha256(output)
        self.current_stage = "terminal"
        self.emit(
            "worker_succeeded",
            duration_ms=round((time.perf_counter() - self.started) * 1000),
            output_kind="media" if binary_size else "json",
            output_size_bytes=json_size + binary_size,
            binary_output_bytes=binary_size,
            output_sha256=output_sha256,
            binary_output_sha256=binary_output_sha256,
        )

    def fail(self, exc: BaseException) -> None:
        if self._active_stage_started is not None:
            error_type = _safe_error_type(exc)
            self.failed_stage = self.current_stage
            self.emit(
                "worker_phase_failed",
                duration_ms=round((time.perf_counter() - self._active_stage_started) * 1000),
                error_code=_error_code(exc),
                error_type=error_type,
            )
            self._active_stage_started = None
        self.current_stage = self.failed_stage or self.current_stage
        self.emit(
            "worker_failed",
            duration_ms=round((time.perf_counter() - self.started) * 1000),
            error_code=_error_code(exc),
            error_type=_safe_error_type(exc),
        )

    def mark_stage(self, name: str) -> None:
        if not _SAFE_STAGE.fullmatch(name):
            raise ValueError("worker phase name must be a fixed safe identifier")
        self.finish_stage()
        self.current_stage = name
        self._active_stage_started = time.perf_counter()
        self.emit("worker_phase_started")

    def finish_stage(self) -> None:
        if self._active_stage_started is None:
            return
        self.emit(
            "worker_phase_succeeded",
            duration_ms=round((time.perf_counter() - self._active_stage_started) * 1000),
        )
        self._active_stage_started = None

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        self.mark_stage(name)
        try:
            yield
        except BaseException:
            self.failed_stage = self.current_stage
            raise
        else:
            self.finish_stage()


@contextmanager
def worker_phase(name: str) -> Iterator[None]:
    """Emit timing for the current worker phase, if called within a worker."""
    run = _ACTIVE_RUN.get()
    if run is None:
        yield
        return
    with run.phase(name):
        yield


def worker_stage(name: str) -> None:
    """Mark a validation or processing block whose existing code is not a context manager."""
    run = _ACTIVE_RUN.get()
    if run is not None:
        run.mark_stage(name)


def refresh_worker_volume(volume: Any) -> None:
    """Refresh a mounted scratch Volume before reading a newly uploaded attempt."""
    with worker_phase("scratch_volume_reload"):
        try:
            volume.reload()
        except Exception:
            raise RuntimeError("MODAL_SCRATCH_VOLUME_RELOAD_FAILED") from None


def _safe_error_type(exc: BaseException) -> str:
    error_type = type(exc).__name__
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", error_type):
        return "Exception"
    return error_type


def observed_worker(
    *, workload: str, model_id: str = "", model_revision: str = "", gpu_class: str = "cpu"
) -> Callable[[_F], _F]:
    """Wrap a Modal entrypoint with safe start and terminal lifecycle events."""

    def decorate(function: _F) -> _F:
        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            payload = args[0] if args else kwargs.get("payload")
            run = WorkerRun(
                workload=workload,
                model_id=model_id,
                model_revision=model_revision,
                gpu_class=gpu_class,
                payload=payload,
            )
            token = _ACTIVE_RUN.set(run)
            run.start()
            try:
                result = function(*args, **kwargs)
            except BaseException as exc:
                run.fail(exc)
                raise
            else:
                run.succeed(result)
                return result
            finally:
                _ACTIVE_RUN.reset(token)

        return wrapped  # type: ignore[return-value]

    return decorate
