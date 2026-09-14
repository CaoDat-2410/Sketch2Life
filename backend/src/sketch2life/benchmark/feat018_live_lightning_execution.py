"""Offline-safe orchestration boundary for the FEAT-018 live Lightning smoke path.

This module owns only the execution control plane.  The existing Qwen adapter remains the
authority for prompt-to-model mapping, schema validation, policy evaluation, and its one
explicit transient retry.  The runner below supplies the missing killable/bounded process
seam; it never exposes provider output, provider exceptions, or runtime paths to the caller.

Importing this module does not load an optional model package, inspect CUDA, contact Lightning,
or start a process.  A real process is created only when the runner's ``generate`` method is
called without an injected process seam.
"""

from __future__ import annotations

import gc
import io
import json
import math
import multiprocessing
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, redirect_stderr, redirect_stdout, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, Protocol, TypeGuard, cast

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.contracts.schemas.vision import VisionErrorCode
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)
from sketch2life.infrastructure.ai.qwen_vision import (
    QwenDeviceUnavailableError,
    QwenGenerationRunner,
    QwenModelLoadError,
    QwenPermanentRuntimeError,
    QwenTimeoutError,
    QwenTransientRuntimeError,
    QwenVisionAdapter,
    _default_model_factory,
    _generate_from_bundle,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig

PER_ATTEMPT_TIMEOUT_SECONDS = 120.0
"""The approved V2 profile deadline; it is deliberately not configurable for live use."""

_PROCESS_JOIN_GRACE_SECONDS = 1.0
_MAX_IDENTIFIER_LENGTH = 160
_SAFE_IDENTIFIER_PATTERN = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
)
_HASH_LENGTH = 64


class LiveLightningExecutionFailureCode(StrEnum):
    """Closed coordinator failures safe to place in a report."""

    PRE_ADAPTER_REJECTED = "PRE_ADAPTER_REJECTED"
    PROMPT_HASH_MISMATCH = "PROMPT_HASH_MISMATCH"
    TOTAL_ADAPTER_CAP_EXCEEDED = "TOTAL_ADAPTER_CAP_EXCEEDED"
    PER_ATTEMPT_TIMEOUT = "PER_ATTEMPT_TIMEOUT"
    MALFORMED_CHILD_RESPONSE = "MALFORMED_CHILD_RESPONSE"
    RAW_OUTPUT_TOO_LARGE = "RAW_OUTPUT_TOO_LARGE"
    IPC_ENVELOPE_TOO_LARGE = "IPC_ENVELOPE_TOO_LARGE"
    STDOUT_TOO_LARGE = "STDOUT_TOO_LARGE"
    STDERR_TOO_LARGE = "STDERR_TOO_LARGE"
    PROCESS_START_FAILED = "PROCESS_START_FAILED"
    PROCESS_TERMINATION_FAILED = "PROCESS_TERMINATION_FAILED"
    ADAPTER_RESULT_MALFORMED = "ADAPTER_RESULT_MALFORMED"
    INVALID_CARDINALITY = "INVALID_CARDINALITY"
    ADAPTER_EXCEPTION = "ADAPTER_EXCEPTION"
    MAPPER_FAILED = "MAPPER_FAILED"
    CLEANUP_FAILED = "CLEANUP_FAILED"
    EVIDENCE_FAILED = "EVIDENCE_FAILED"


class GenerationAttemptOutcome(StrEnum):
    """Safe per-call trace tokens; no provider detail is retained."""

    SUCCESS = "SUCCESS"
    MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"
    DEVICE_UNAVAILABLE = "DEVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    TRANSIENT_RUNTIME_FAILURE = "TRANSIENT_RUNTIME_FAILURE"
    PERMANENT_RUNTIME_FAILURE = "PERMANENT_RUNTIME_FAILURE"


@dataclass(frozen=True, slots=True)
class LiveLightningExecutionCaps:
    """Explicit execution ceilings for one adapter call.

    The plan fixes the per-attempt deadline at 120 seconds.  The live plan leaves the total,
    raw-output, IPC, stdout, and stderr values to the owner approval, so those values are
    required constructor inputs rather than invented defaults.
    """

    total_adapter_cap_seconds: float
    raw_output_max_bytes: int
    ipc_envelope_max_bytes: int
    stdout_max_bytes: int
    stderr_max_bytes: int
    per_attempt_timeout_seconds: float = PER_ATTEMPT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if (
            not math.isfinite(self.total_adapter_cap_seconds)
            or self.total_adapter_cap_seconds <= 0
        ):
            raise ValueError("total_adapter_cap_seconds must be finite and positive")
        if self.per_attempt_timeout_seconds != PER_ATTEMPT_TIMEOUT_SECONDS:
            raise ValueError("per_attempt_timeout_seconds must be the approved 120-second value")
        _require_positive_integer(self.raw_output_max_bytes, "raw_output_max_bytes")
        _require_positive_integer(self.ipc_envelope_max_bytes, "ipc_envelope_max_bytes")
        _require_non_negative_integer(self.stdout_max_bytes, "stdout_max_bytes")
        _require_non_negative_integer(self.stderr_max_bytes, "stderr_max_bytes")


def _require_positive_integer(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")


def _require_non_negative_integer(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


class _ConnectionLike(Protocol):
    def poll(self, timeout: float) -> bool: ...

    def recv_bytes(self, maxlength: int = -1) -> bytes: ...

    def send_bytes(self, buffer: bytes) -> None: ...

    def close(self) -> None: ...


class _ProcessLike(Protocol):
    pid: int | None

    def start(self) -> None: ...

    def is_alive(self) -> bool: ...

    def join(self, timeout: float | None = None) -> None: ...

    def terminate(self) -> None: ...


ProcessFactory = Callable[..., _ProcessLike]
PipeFactory = Callable[[], tuple[_ConnectionLike, _ConnectionLike]]
ProcessTreeTerminator = Callable[[_ProcessLike], None]
ResourceCleanup = Callable[[], None]
RawMapper = Callable[..., object]


class _RunnerFailure(Exception):
    """Internal fixed-code runner failure; its message never crosses the adapter boundary."""

    def __init__(self, code: LiveLightningExecutionFailureCode) -> None:
        self.code = code


class _StreamLimitExceeded(Exception):
    def __init__(self, stream_name: Literal["stdout", "stderr"]) -> None:
        self.stream_name = stream_name


class _BoundedTextSink(io.TextIOBase):
    """Count a child stream without retaining any stream contents."""

    def __init__(self, stream_name: Literal["stdout", "stderr"], max_bytes: int) -> None:
        super().__init__()
        self._stream_name = stream_name
        self._max_bytes = max_bytes
        self._written_bytes = 0

    @property
    def encoding(self) -> str:  # type: ignore[override]
        return "utf-8"

    def write(self, text: str) -> int:
        if not isinstance(text, str):
            raise TypeError("bounded stream accepts text only")
        try:
            encoded_length = len(text.encode("utf-8"))
        except UnicodeError as exc:
            raise _StreamLimitExceeded(self._stream_name) from exc
        if self._written_bytes + encoded_length > self._max_bytes:
            raise _StreamLimitExceeded(self._stream_name)
        self._written_bytes += encoded_length
        return len(text)

    def flush(self) -> None:
        return None

    def writable(self) -> bool:
        return True


def _clear_cuda_cache() -> None:
    """Drop child-owned Python/GPU references without importing optional packages eagerly."""

    gc.collect()
    torch_module = sys.modules.get("torch")
    if torch_module is None:
        return
    try:
        cuda = getattr(torch_module, "cuda", None)
        empty_cache = getattr(cuda, "empty_cache", None)
        if callable(empty_cache):
            empty_cache()
    except Exception:
        # Cleanup must not leak a provider/runtime exception.  The parent process still owns the
        # kill/join confirmation and can report a typed cleanup failure through an injected hook.
        return


def _serialize_envelope(envelope: Mapping[str, object]) -> bytes:
    try:
        return json.dumps(
            dict(envelope), ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise _RunnerFailure(LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE) from exc


def _send_bounded_envelope(
    connection: _ConnectionLike,
    envelope: Mapping[str, object],
    max_bytes: int,
) -> None:
    try:
        payload = _serialize_envelope(envelope)
    except _RunnerFailure:
        return
    if len(payload) > max_bytes:
        payload = _serialize_envelope({"kind": "ipc_envelope_too_large"})
    if len(payload) > max_bytes:
        # A cap too small even for the fixed failure token is fail-closed: the parent sees EOF.
        return
    with suppress(BrokenPipeError, EOFError, OSError):
        connection.send_bytes(payload)


def _worker_failure_kind(exc: BaseException) -> str:
    if isinstance(exc, QwenModelLoadError):
        return "model_load_failed"
    if isinstance(exc, QwenDeviceUnavailableError):
        return "device_unavailable"
    if isinstance(exc, (QwenTimeoutError, TimeoutError)):
        return "timeout"
    if isinstance(exc, QwenTransientRuntimeError):
        return "transient_runtime_failure"
    return "permanent_runtime_failure"


def _worker_success_envelope(
    raw_output: object, caps: LiveLightningExecutionCaps
) -> dict[str, object]:
    if not isinstance(raw_output, str):
        return {"kind": "malformed_child_response"}
    try:
        if len(raw_output.encode("utf-8")) > caps.raw_output_max_bytes:
            return {"kind": "raw_output_too_large"}
    except UnicodeError:
        return {"kind": "malformed_child_response"}
    envelope: dict[str, object] = {"kind": "success", "raw_output": raw_output}
    try:
        encoded_envelope = _serialize_envelope(envelope)
    except _RunnerFailure:
        return {"kind": "malformed_child_response"}
    if len(encoded_envelope) > caps.ipc_envelope_max_bytes:
        return {"kind": "ipc_envelope_too_large"}
    return envelope


def _bounded_qwen_worker_entry(
    connection: _ConnectionLike,
    profile: VisionProfileV2,
    runtime_config: QwenVisionRuntimeConfig,
    image_path: str,
    prompt: str,
    caps: LiveLightningExecutionCaps,
) -> None:
    """Run one load/generate/decode attempt and send only a bounded fixed envelope."""

    if os.name != "nt":
        create_session = getattr(os, "setsid", None)
        if callable(create_session):
            with suppress(OSError):
                create_session()
    stdout_sink = _BoundedTextSink("stdout", caps.stdout_max_bytes)
    stderr_sink = _BoundedTextSink("stderr", caps.stderr_max_bytes)
    bundle: object | None = None
    envelope: dict[str, object]
    try:
        with redirect_stdout(stdout_sink), redirect_stderr(stderr_sink):
            try:
                bundle = _default_model_factory(profile, runtime_config)
                raw_output = _generate_from_bundle(
                    cast(Any, bundle), profile, Path(image_path), prompt
                )
                envelope = _worker_success_envelope(raw_output, caps)
            except _StreamLimitExceeded as exc:
                envelope = {"kind": f"{exc.stream_name}_too_large"}
            except Exception as exc:  # noqa: BLE001 - only a fixed kind crosses IPC
                envelope = {"kind": _worker_failure_kind(exc)}
    except _StreamLimitExceeded as exc:
        envelope = {"kind": f"{exc.stream_name}_too_large"}
    except Exception:
        envelope = {"kind": "permanent_runtime_failure"}
    finally:
        bundle = None
        _clear_cuda_cache()
    _send_bounded_envelope(connection, envelope, caps.ipc_envelope_max_bytes)


def _terminate_process_tree(process: _ProcessLike) -> None:
    """Terminate a process and its descendants without allowing command output to escape."""

    pid = process.pid
    if pid is not None and pid > 0:
        if os.name == "nt":
            with suppress(OSError, subprocess.SubprocessError):
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        else:
            get_process_group = getattr(os, "getpgid", None)
            terminate_process_group = getattr(os, "killpg", None)
            if callable(get_process_group) and callable(terminate_process_group):
                with suppress(OSError):
                    terminate_process_group(get_process_group(pid), signal.SIGTERM)
    with suppress(OSError):
        process.terminate()


def _close_connection(connection: _ConnectionLike | None) -> None:
    if connection is not None:
        with suppress(Exception):
            connection.close()


def _safe_relative_path(path: Path) -> None:
    if path.is_absolute() or str(path).startswith(("/", "\\")):
        raise _RunnerFailure(LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE)


class Feat018BoundedKillableQwenGenerationRunner:
    """Qwen generation runner with bounded IPC, killable attempts, and reusable total cap."""

    def __init__(
        self,
        caps: LiveLightningExecutionCaps,
        *,
        process_factory: ProcessFactory | None = None,
        pipe_factory: PipeFactory | None = None,
        worker: Callable[..., None] = _bounded_qwen_worker_entry,
        process_tree_terminator: ProcessTreeTerminator = _terminate_process_tree,
        resource_cleanup: ResourceCleanup = _clear_cuda_cache,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.caps = caps
        self._context = multiprocessing.get_context("spawn")
        self._process_factory: ProcessFactory = process_factory or cast(
            ProcessFactory, self._context.Process
        )
        self._pipe_factory: PipeFactory = pipe_factory or self._make_pipe
        self._worker = worker
        self._process_tree_terminator = process_tree_terminator
        self._resource_cleanup = resource_cleanup
        self._clock = clock
        self._adapter_deadline: float | None = None
        self._attempt_trace: list[GenerationAttemptOutcome] = []
        self._last_attempt_trace: tuple[GenerationAttemptOutcome, ...] = ()
        self._last_failure_code: LiveLightningExecutionFailureCode | None = None
        self._attempt_started = False

    def _make_pipe(self) -> tuple[_ConnectionLike, _ConnectionLike]:
        receiver, sender = self._context.Pipe(duplex=False)
        return cast(_ConnectionLike, receiver), cast(_ConnectionLike, sender)

    @property
    def last_attempt_trace(self) -> tuple[GenerationAttemptOutcome, ...]:
        return self._last_attempt_trace

    @property
    def last_failure_code(self) -> LiveLightningExecutionFailureCode | None:
        return self._last_failure_code

    @contextmanager
    def adapter_call_scope(self) -> Iterator[None]:
        """Anchor one total cap across all adapter-owned generation attempts."""

        if self._adapter_deadline is not None:
            raise ValueError("adapter call scopes cannot be nested")
        self._adapter_deadline = self._clock() + self.caps.total_adapter_cap_seconds
        self._attempt_trace = []
        self._last_failure_code = None
        try:
            yield
        finally:
            self._last_attempt_trace = tuple(self._attempt_trace)
            self._adapter_deadline = None

    def run_adapter_call(
        self,
        adapter: VisionUnderstandingPortV2,
        request: VisionUnderstandingRequestV2,
    ) -> VisionUnderstandingResultV2:
        """Invoke the supplied adapter once under the total cap; never retry at this layer."""

        with self.adapter_call_scope():
            result = adapter.understand(request)
            if self._adapter_deadline is not None and self._clock() >= self._adapter_deadline:
                self._last_failure_code = (
                    LiveLightningExecutionFailureCode.TOTAL_ADAPTER_CAP_EXCEEDED
                )
                raise QwenTimeoutError from None
            return result

    def generate(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        """Run exactly one generation attempt; the adapter decides whether to retry it."""

        implicit_scope = self._adapter_deadline is None
        if implicit_scope:
            self._adapter_deadline = self._clock() + self.caps.total_adapter_cap_seconds
            self._attempt_trace = []
            self._last_failure_code = None
        self._attempt_started = False
        failure: BaseException | None = None
        result: str | None = None
        try:
            if profile.timeout_seconds != self.caps.per_attempt_timeout_seconds:
                self._last_failure_code = LiveLightningExecutionFailureCode.PER_ATTEMPT_TIMEOUT
                raise QwenPermanentRuntimeError from None
            result = self._run_child(profile, runtime_config, image_path, prompt)
            self._record_attempt(GenerationAttemptOutcome.SUCCESS)
        except QwenModelLoadError:
            self._record_attempt(GenerationAttemptOutcome.MODEL_LOAD_FAILED)
            failure = QwenModelLoadError()
        except QwenDeviceUnavailableError:
            self._record_attempt(GenerationAttemptOutcome.DEVICE_UNAVAILABLE)
            failure = QwenDeviceUnavailableError()
        except (QwenTimeoutError, TimeoutError):
            self._record_attempt(GenerationAttemptOutcome.TIMEOUT)
            failure = QwenTimeoutError()
        except QwenTransientRuntimeError:
            self._record_attempt(GenerationAttemptOutcome.TRANSIENT_RUNTIME_FAILURE)
            failure = QwenTransientRuntimeError()
        except _RunnerFailure as exc:
            self._last_failure_code = exc.code
            self._record_attempt(GenerationAttemptOutcome.PERMANENT_RUNTIME_FAILURE)
            failure = QwenPermanentRuntimeError()
        except QwenPermanentRuntimeError:
            self._record_attempt(GenerationAttemptOutcome.PERMANENT_RUNTIME_FAILURE)
            failure = QwenPermanentRuntimeError()
        except Exception:
            self._last_failure_code = LiveLightningExecutionFailureCode.PROCESS_START_FAILED
            self._record_attempt(GenerationAttemptOutcome.PERMANENT_RUNTIME_FAILURE)
            failure = QwenPermanentRuntimeError()
        finally:
            cleanup_failed = False
            try:
                self._resource_cleanup()
            except Exception:
                cleanup_failed = True
            if cleanup_failed:
                self._last_failure_code = LiveLightningExecutionFailureCode.CLEANUP_FAILED
                failure = QwenPermanentRuntimeError()
            if implicit_scope:
                self._last_attempt_trace = tuple(self._attempt_trace)
                self._adapter_deadline = None
        if failure is not None:
            raise failure from None
        assert result is not None
        if implicit_scope:
            self._last_attempt_trace = tuple(self._attempt_trace)
        return result

    def _record_attempt(self, outcome: GenerationAttemptOutcome) -> None:
        if self._attempt_started:
            self._attempt_trace.append(outcome)

    def _remaining_seconds(self, profile: VisionProfileV2) -> float:
        if self._adapter_deadline is None:
            raise _RunnerFailure(LiveLightningExecutionFailureCode.TOTAL_ADAPTER_CAP_EXCEEDED)
        remaining = self._adapter_deadline - self._clock()
        if remaining <= 0:
            self._last_failure_code = LiveLightningExecutionFailureCode.TOTAL_ADAPTER_CAP_EXCEEDED
            raise QwenTimeoutError from None
        return min(profile.timeout_seconds, remaining)

    def _run_child(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        _safe_relative_path(image_path)
        self._remaining_seconds(profile)
        receiver: _ConnectionLike | None = None
        sender: _ConnectionLike | None = None
        process: _ProcessLike | None = None
        started = False
        primary_failure: BaseException | None = None
        result: str | None = None
        try:
            receiver, sender = self._pipe_factory()
            process = self._process_factory(
                target=self._worker,
                args=(sender, profile, runtime_config, str(image_path), prompt, self.caps),
                daemon=True,
            )
            self._attempt_started = True
            try:
                process.start()
                started = True
            except Exception:
                self._last_failure_code = LiveLightningExecutionFailureCode.PROCESS_START_FAILED
                raise QwenModelLoadError from None
            _close_connection(sender)
            sender = None

            poll_timeout = self._remaining_seconds(profile)
            if not receiver.poll(poll_timeout):
                if poll_timeout < profile.timeout_seconds:
                    self._last_failure_code = (
                        LiveLightningExecutionFailureCode.TOTAL_ADAPTER_CAP_EXCEEDED
                    )
                else:
                    self._last_failure_code = LiveLightningExecutionFailureCode.PER_ATTEMPT_TIMEOUT
                self._terminate_and_join(process, force=True)
                raise QwenTimeoutError from None

            try:
                payload = receiver.recv_bytes(maxlength=self.caps.ipc_envelope_max_bytes)
            except OSError:
                # ``Connection.recv_bytes(maxlength=...)`` uses OSError for an envelope that is
                # larger than the requested bound.  EOF and malformed UTF-8 have separate paths.
                self._last_failure_code = LiveLightningExecutionFailureCode.IPC_ENVELOPE_TOO_LARGE
                raise QwenPermanentRuntimeError from None
            except (EOFError, ValueError, TypeError):
                self._last_failure_code = LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE
                raise QwenPermanentRuntimeError from None
            if len(payload) > self.caps.ipc_envelope_max_bytes:
                self._last_failure_code = LiveLightningExecutionFailureCode.IPC_ENVELOPE_TOO_LARGE
                raise QwenPermanentRuntimeError from None
            result = self._decode_child_payload(payload)
            process.join(timeout=_PROCESS_JOIN_GRACE_SECONDS)
            if process.is_alive():
                self._terminate_and_join(process, force=True)
            if self._adapter_deadline is not None and self._clock() >= self._adapter_deadline:
                self._last_failure_code = (
                    LiveLightningExecutionFailureCode.TOTAL_ADAPTER_CAP_EXCEEDED
                )
                raise QwenTimeoutError from None
            return result
        except (QwenModelLoadError, QwenDeviceUnavailableError, QwenTimeoutError):
            raise
        except QwenTransientRuntimeError:
            raise
        except QwenPermanentRuntimeError:
            raise
        except _RunnerFailure:
            raise
        except Exception:
            self._last_failure_code = LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE
            primary_failure = QwenPermanentRuntimeError()
        finally:
            if process is not None and started:
                try:
                    if process.is_alive():
                        self._terminate_and_join(process, force=True)
                except Exception:
                    self._last_failure_code = (
                        LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
                    )
                    primary_failure = QwenPermanentRuntimeError()
            _close_connection(sender)
            _close_connection(receiver)
        if primary_failure is not None:
            raise primary_failure from None
        assert result is not None
        return result

    def _terminate_and_join(self, process: _ProcessLike, *, force: bool) -> None:
        if force or process.is_alive():
            try:
                self._process_tree_terminator(process)
            except Exception:
                self._last_failure_code = (
                    LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
                )
                raise _RunnerFailure(
                    LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
                ) from None
        try:
            process.join(timeout=_PROCESS_JOIN_GRACE_SECONDS)
        except Exception:
            self._last_failure_code = (
                LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
            )
            raise _RunnerFailure(
                LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
            ) from None
        if process.is_alive():
            kill_method = getattr(process, "kill", None)
            if not callable(kill_method):
                self._last_failure_code = (
                    LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
                )
                raise _RunnerFailure(
                    LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
                ) from None
            try:
                kill_method()
                process.join(timeout=_PROCESS_JOIN_GRACE_SECONDS)
            except Exception:
                self._last_failure_code = (
                    LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
                )
                raise _RunnerFailure(
                    LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
                ) from None
        if process.is_alive():
            self._last_failure_code = (
                LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED
            )
            raise _RunnerFailure(LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED)

    def _decode_child_payload(self, payload: bytes) -> str:
        try:
            envelope = json.loads(payload.decode("utf-8"))
        except (UnicodeError, ValueError, TypeError):
            self._last_failure_code = LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE
            raise QwenPermanentRuntimeError from None
        if not isinstance(envelope, dict) or not isinstance(envelope.get("kind"), str):
            self._last_failure_code = LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE
            raise QwenPermanentRuntimeError from None
        kind = envelope["kind"]
        if kind == "success":
            if set(envelope) != {"kind", "raw_output"} or not isinstance(
                envelope.get("raw_output"), str
            ):
                self._last_failure_code = LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE
                raise QwenPermanentRuntimeError from None
            raw_output = cast(str, envelope["raw_output"])
            try:
                if len(raw_output.encode("utf-8")) > self.caps.raw_output_max_bytes:
                    self._last_failure_code = LiveLightningExecutionFailureCode.RAW_OUTPUT_TOO_LARGE
                    raise QwenPermanentRuntimeError from None
            except UnicodeError:
                self._last_failure_code = LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE
                raise QwenPermanentRuntimeError from None
            return raw_output
        if set(envelope) != {"kind"}:
            self._last_failure_code = LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE
            raise QwenPermanentRuntimeError from None
        fixed_failures: dict[
            str, tuple[type[BaseException], LiveLightningExecutionFailureCode]
        ] = {
            "model_load_failed": (
                QwenModelLoadError,
                LiveLightningExecutionFailureCode.PROCESS_START_FAILED,
            ),
            "device_unavailable": (
                QwenDeviceUnavailableError,
                LiveLightningExecutionFailureCode.ADAPTER_EXCEPTION,
            ),
            "timeout": (QwenTimeoutError, LiveLightningExecutionFailureCode.PER_ATTEMPT_TIMEOUT),
            "transient_runtime_failure": (
                QwenTransientRuntimeError,
                LiveLightningExecutionFailureCode.ADAPTER_EXCEPTION,
            ),
            "permanent_runtime_failure": (
                QwenPermanentRuntimeError,
                LiveLightningExecutionFailureCode.ADAPTER_EXCEPTION,
            ),
            "raw_output_too_large": (
                QwenPermanentRuntimeError,
                LiveLightningExecutionFailureCode.RAW_OUTPUT_TOO_LARGE,
            ),
            "ipc_envelope_too_large": (
                QwenPermanentRuntimeError,
                LiveLightningExecutionFailureCode.IPC_ENVELOPE_TOO_LARGE,
            ),
            "stdout_too_large": (
                QwenPermanentRuntimeError,
                LiveLightningExecutionFailureCode.STDOUT_TOO_LARGE,
            ),
            "stderr_too_large": (
                QwenPermanentRuntimeError,
                LiveLightningExecutionFailureCode.STDERR_TOO_LARGE,
            ),
            "malformed_child_response": (
                QwenPermanentRuntimeError,
                LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE,
            ),
        }
        failure = fixed_failures.get(kind)
        if failure is None:
            self._last_failure_code = LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE
            raise QwenPermanentRuntimeError from None
        exception_type, failure_code = failure
        self._last_failure_code = failure_code
        raise exception_type from None


class PreAdapterRejection(Exception):
    """Fixed-code stop before the adapter is invoked."""

    def __init__(
        self,
        code: LiveLightningExecutionFailureCode = (
            LiveLightningExecutionFailureCode.PRE_ADAPTER_REJECTED
        ),
    ) -> None:
        self.code = code


@dataclass(frozen=True, slots=True)
class LiveLightningExecutionResult:
    """Safe orchestration result; it never serializes a V2 object wholesale."""

    status: Literal["SUCCEEDED", "FAILED"]
    adapter_call_count: int
    attempt_count: int | None
    vision_result: VisionUnderstandingResultV2 | None = None
    mapped_result: object | None = None
    run_failure_code: LiveLightningExecutionFailureCode | None = None
    cleanup_status: Literal["SUCCEEDED", "FAILED"] = "SUCCEEDED"
    adapter_wall_clock_ms: float | None = None

    def sanitized_evidence(
        self,
        *,
        run_id: str,
        correlation_id: str,
        session_id: str,
        caps: LiveLightningExecutionCaps,
        prompt_protocol_id: str | None = None,
        prompt_sha256: str | None = None,
        fixture_id: str | None = None,
        source_sha256: str | None = None,
    ) -> dict[str, object]:
        """Return only fixed identifiers, counters, caps, and typed result tokens."""

        for identifier in (run_id, correlation_id, session_id):
            _require_safe_identifier(identifier)
        optional_ids = {
            "prompt_protocol_id": prompt_protocol_id,
            "fixture_id": fixture_id,
        }
        for _label, optional_value in optional_ids.items():
            if optional_value is not None:
                _require_safe_identifier(optional_value)
        if prompt_sha256 is not None:
            _require_sha256(prompt_sha256, "prompt_sha256")
        if source_sha256 is not None:
            _require_sha256(source_sha256, "source_sha256")

        evidence: dict[str, object] = {
            "contract_name": "Feat018LiveLightningExecutionResultV1",
            "contract_version": "1.0",
            "run_id": run_id,
            "correlation_id": correlation_id,
            "session_id": session_id,
            "status": self.status,
            "adapter_call_count": self.adapter_call_count,
            "attempt_count": self.attempt_count,
            "per_attempt_timeout_seconds": caps.per_attempt_timeout_seconds,
            "total_adapter_cap_seconds": caps.total_adapter_cap_seconds,
            "raw_output_max_bytes": caps.raw_output_max_bytes,
            "ipc_envelope_max_bytes": caps.ipc_envelope_max_bytes,
            "stdout_max_bytes": caps.stdout_max_bytes,
            "stderr_max_bytes": caps.stderr_max_bytes,
            "cleanup_status": self.cleanup_status,
            "asr_execution": False,
            "narration_status": "NOT_SUPPLIED",
        }
        if self.run_failure_code is not None:
            evidence["run_failure_code"] = self.run_failure_code.value
        if self.vision_result is not None:
            evidence["vision_status"] = self.vision_result.status
            evidence["vision_attempt_number"] = self.vision_result.attempt_number
            evidence["vision_repair_attempted"] = self.vision_result.repair_attempted
            if isinstance(self.vision_result, VisionUnderstandingFailureV2):
                evidence["vision_error_code"] = self.vision_result.error_code.value
                evidence["vision_error_detail"] = self.vision_result.error_detail.value
        if self.adapter_wall_clock_ms is not None:
            evidence["adapter_wall_clock_ms"] = self.adapter_wall_clock_ms
        if prompt_protocol_id is not None:
            evidence["prompt_protocol_id"] = prompt_protocol_id
        if prompt_sha256 is not None:
            evidence["prompt_sha256"] = prompt_sha256
        if fixture_id is not None:
            evidence["fixture_id"] = fixture_id
        if source_sha256 is not None:
            evidence["source_sha256"] = source_sha256
        return _validate_safe_evidence(evidence)


def _require_safe_identifier(value: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > _MAX_IDENTIFIER_LENGTH
        or ".." in value
        or any(character not in _SAFE_IDENTIFIER_PATTERN for character in value)
    ):
        raise ValueError("identifier is not safe for evidence")


def _require_sha256(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != _HASH_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256")


_SAFE_EVIDENCE_KEYS = frozenset(
    {
        "contract_name",
        "contract_version",
        "run_id",
        "correlation_id",
        "session_id",
        "status",
        "adapter_call_count",
        "attempt_count",
        "per_attempt_timeout_seconds",
        "total_adapter_cap_seconds",
        "raw_output_max_bytes",
        "ipc_envelope_max_bytes",
        "stdout_max_bytes",
        "stderr_max_bytes",
        "cleanup_status",
        "asr_execution",
        "narration_status",
        "run_failure_code",
        "vision_status",
        "vision_attempt_number",
        "vision_repair_attempted",
        "vision_error_code",
        "vision_error_detail",
        "adapter_wall_clock_ms",
        "prompt_protocol_id",
        "prompt_sha256",
        "fixture_id",
        "source_sha256",
    }
)

_REQUIRED_EVIDENCE_KEYS = frozenset(
    {
        "contract_name",
        "contract_version",
        "run_id",
        "correlation_id",
        "session_id",
        "status",
        "adapter_call_count",
        "attempt_count",
        "per_attempt_timeout_seconds",
        "total_adapter_cap_seconds",
        "raw_output_max_bytes",
        "ipc_envelope_max_bytes",
        "stdout_max_bytes",
        "stderr_max_bytes",
        "cleanup_status",
        "asr_execution",
        "narration_status",
    }
)


def _is_integer(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_closed_token(value: object, allowed: frozenset[str], label: str) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"{label} is not an allowlisted token")


def _validate_safe_evidence(evidence: Mapping[str, object]) -> dict[str, object]:
    if set(evidence) - _SAFE_EVIDENCE_KEYS:
        raise ValueError("evidence contains a non-allowlisted field")
    copied = dict(evidence)
    if _REQUIRED_EVIDENCE_KEYS - set(copied):
        raise ValueError("evidence is missing a required field")
    try:
        encoded = json.dumps(copied, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError("evidence is not JSON-safe") from exc
    if len(encoded.encode("utf-8")) > 64 * 1024:
        raise ValueError("evidence exceeds its fixed bounded envelope")
    if copied["contract_name"] != "Feat018LiveLightningExecutionResultV1":
        raise ValueError("evidence contract name is not allowlisted")
    if copied["contract_version"] != "1.0":
        raise ValueError("evidence contract version is not allowlisted")
    for key in ("run_id", "correlation_id", "session_id", "prompt_protocol_id", "fixture_id"):
        value = copied.get(key)
        if value is not None:
            _require_safe_identifier(cast(str, value))
    for key in ("prompt_sha256", "source_sha256"):
        value = copied.get(key)
        if value is not None:
            _require_sha256(cast(str, value), key)
    _require_closed_token(copied["status"], frozenset({"SUCCEEDED", "FAILED"}), "status")
    _require_closed_token(
        copied["cleanup_status"], frozenset({"SUCCEEDED", "FAILED"}), "cleanup_status"
    )
    if not _is_integer(copied["adapter_call_count"]) or copied["adapter_call_count"] not in {
        0,
        1,
    }:
        raise ValueError("adapter_call_count is outside its fixed range")
    attempt_count = copied["attempt_count"]
    if attempt_count is not None and (
        not _is_integer(attempt_count) or attempt_count not in {0, 1, 2}
    ):
        raise ValueError("attempt_count is outside its fixed range")
    per_attempt_timeout = copied["per_attempt_timeout_seconds"]
    if (
        not isinstance(per_attempt_timeout, (int, float))
        or isinstance(per_attempt_timeout, bool)
        or not math.isfinite(float(per_attempt_timeout))
        or per_attempt_timeout != PER_ATTEMPT_TIMEOUT_SECONDS
    ):
        raise ValueError("per_attempt_timeout_seconds is not the approved value")
    total_adapter_cap = copied["total_adapter_cap_seconds"]
    if not isinstance(total_adapter_cap, (int, float)) or isinstance(total_adapter_cap, bool):
        raise ValueError("total_adapter_cap_seconds is invalid")
    if not math.isfinite(float(total_adapter_cap)) or total_adapter_cap <= 0:
        raise ValueError("total_adapter_cap_seconds is invalid")
    raw_output_max = copied["raw_output_max_bytes"]
    if not _is_integer(raw_output_max) or raw_output_max <= 0:
        raise ValueError("raw_output_max_bytes is invalid")
    ipc_envelope_max = copied["ipc_envelope_max_bytes"]
    if not _is_integer(ipc_envelope_max) or ipc_envelope_max <= 0:
        raise ValueError("ipc_envelope_max_bytes is invalid")
    for key in ("stdout_max_bytes", "stderr_max_bytes"):
        stream_max = copied[key]
        if not _is_integer(stream_max) or stream_max < 0:
            raise ValueError(f"{key} is invalid")
    if copied["asr_execution"] is not False or copied["narration_status"] != "NOT_SUPPLIED":
        raise ValueError("unsupported multimodal evidence state")
    if "run_failure_code" in copied:
        run_failure_token = copied["run_failure_code"]
        if not isinstance(run_failure_token, str):
            raise ValueError("run_failure_code is not allowlisted")
        try:
            LiveLightningExecutionFailureCode(run_failure_token)
        except (TypeError, ValueError):
            raise ValueError("run_failure_code is not allowlisted") from None
    vision_status = copied.get("vision_status")
    if vision_status is not None:
        _require_closed_token(vision_status, frozenset({"SUCCEEDED", "FAILED"}), "vision_status")
        for key in ("vision_attempt_number", "vision_repair_attempted"):
            if key not in copied:
                raise ValueError("vision evidence is incomplete")
        if not _is_integer(copied["vision_attempt_number"]) or copied[
            "vision_attempt_number"
        ] not in {0, 1, 2}:
            raise ValueError("vision_attempt_number is outside its fixed range")
        if not isinstance(copied["vision_repair_attempted"], bool):
            raise ValueError("vision_repair_attempted is invalid")
    elif any(
        key in copied
        for key in (
            "vision_attempt_number",
            "vision_repair_attempted",
            "vision_error_code",
            "vision_error_detail",
        )
    ):
        raise ValueError("vision evidence is incomplete")
    if "vision_error_code" in copied or "vision_error_detail" in copied:
        if vision_status != "FAILED" or not {
            "vision_error_code",
            "vision_error_detail",
        }.issubset(copied):
            raise ValueError("vision failure evidence is incomplete")
        vision_error_code = copied["vision_error_code"]
        vision_error_detail = copied["vision_error_detail"]
        if not isinstance(vision_error_code, str) or not isinstance(vision_error_detail, str):
            raise ValueError("vision failure token is not allowlisted")
        try:
            VisionErrorCode(vision_error_code)
            VisionNonPolicyErrorDetailV2(vision_error_detail)
        except (TypeError, ValueError):
            raise ValueError("vision failure token is not allowlisted") from None
    if "adapter_wall_clock_ms" in copied:
        wall_clock_ms = copied["adapter_wall_clock_ms"]
        if not isinstance(wall_clock_ms, (int, float)) or isinstance(wall_clock_ms, bool):
            raise ValueError("adapter_wall_clock_ms is invalid")
        if not math.isfinite(float(wall_clock_ms)) or wall_clock_ms < 0:
            raise ValueError("adapter_wall_clock_ms is invalid")
    return copied


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _profile_for_request(request: VisionUnderstandingRequestV2) -> VisionProfileV2:
    return vision_profile_catalog_v2().resolve(request.requested_profile_id)


def _typed_failure_for_exception(
    request: VisionUnderstandingRequestV2,
    exception: BaseException,
    *,
    attempt_number: int,
    content_policy: ObservableContentPolicyV1,
    result_clock: Callable[[], datetime],
) -> VisionUnderstandingFailureV2 | None:
    if attempt_number not in {1, 2}:
        return None
    if isinstance(exception, (QwenTimeoutError, TimeoutError)):
        code = VisionErrorCode.VISION_TIMEOUT
        detail = VisionNonPolicyErrorDetailV2.TIMEOUT_BUDGET_EXCEEDED
        retryable = False
    elif isinstance(exception, (QwenModelLoadError, QwenDeviceUnavailableError)):
        code = VisionErrorCode.VISION_MODEL_UNAVAILABLE
        detail = (
            VisionNonPolicyErrorDetailV2.DEVICE_UNAVAILABLE
            if isinstance(exception, QwenDeviceUnavailableError)
            else VisionNonPolicyErrorDetailV2.MODEL_LOAD_FAILED
        )
        retryable = False
    elif isinstance(exception, QwenTransientRuntimeError):
        code = VisionErrorCode.VISION_PROVIDER_FAILURE
        detail = VisionNonPolicyErrorDetailV2.TRANSIENT_RUNTIME_FAILURE
        retryable = True
        if attempt_number != 2:
            return None
    elif isinstance(exception, QwenPermanentRuntimeError):
        code = VisionErrorCode.VISION_PROVIDER_FAILURE
        detail = VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE
        retryable = False
    else:
        return None
    profile = _profile_for_request(request)
    return VisionUnderstandingFailureV2(
        correlation_id=request.correlation_id,
        executed_at=result_clock(),
        source_image_ref=request.source_image_ref,
        profile_id=profile.profile_id,
        profile_catalog_hash=vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
        attempt_number=attempt_number,
        repair_attempted=False,
        content_policy_version=content_policy.content_policy_version,
        policy_match_view_version=content_policy.policy_match_view_version,
        policy_execution_state="NOT_EXECUTED",
        error_code=code,
        error_detail=detail,
        retryable=retryable,
        model_provenance=profile.model_provenance,
    )


def _validate_result_cardinality(
    result: VisionUnderstandingResultV2,
    *,
    runner: Feat018BoundedKillableQwenGenerationRunner | None,
    adapter: VisionUnderstandingPortV2,
) -> None:
    if isinstance(result, VisionUnderstandingFailureV2) and result.error_code is (
        VisionErrorCode.INPUT_NOT_VALIDATED
    ):
        if result.attempt_number != 0 or result.retryable:
            raise _RunnerFailure(LiveLightningExecutionFailureCode.INVALID_CARDINALITY)
        if runner is not None and runner.last_attempt_trace:
            raise _RunnerFailure(LiveLightningExecutionFailureCode.INVALID_CARDINALITY)
        return
    if result.attempt_number not in {1, 2}:
        raise _RunnerFailure(LiveLightningExecutionFailureCode.INVALID_CARDINALITY)
    if runner is not None:
        trace: tuple[GenerationAttemptOutcome, ...] | None = runner.last_attempt_trace
    else:
        candidate_trace = getattr(adapter, "attempt_trace", None)
        trace = candidate_trace if isinstance(candidate_trace, tuple) else None
    if runner is not None and (trace is None or len(trace) != result.attempt_number):
        raise _RunnerFailure(LiveLightningExecutionFailureCode.INVALID_CARDINALITY)
    if result.attempt_number == 2 and (
        trace is None
        or len(trace) != 2
        or trace[0] is not GenerationAttemptOutcome.TRANSIENT_RUNTIME_FAILURE
    ):
        raise _RunnerFailure(LiveLightningExecutionFailureCode.INVALID_CARDINALITY)


def _prompt_guard(
    prompt_text: str | None,
    expected_prompt_sha256: str | None,
    *,
    require_explicit: bool = False,
) -> None:
    if prompt_text is None and expected_prompt_sha256 is None:
        if require_explicit:
            raise PreAdapterRejection(LiveLightningExecutionFailureCode.PROMPT_HASH_MISMATCH)
        return
    if not isinstance(prompt_text, str) or not prompt_text:
        raise PreAdapterRejection(LiveLightningExecutionFailureCode.PROMPT_HASH_MISMATCH)
    if expected_prompt_sha256 is None:
        raise PreAdapterRejection(LiveLightningExecutionFailureCode.PROMPT_HASH_MISMATCH)
    try:
        _require_sha256(expected_prompt_sha256, "prompt_sha256")
    except ValueError:
        raise PreAdapterRejection(LiveLightningExecutionFailureCode.PROMPT_HASH_MISMATCH) from None
    try:
        prompt_digest = sha256(prompt_text.encode("utf-8")).hexdigest()
    except UnicodeError:
        raise PreAdapterRejection(LiveLightningExecutionFailureCode.PROMPT_HASH_MISMATCH) from None
    if prompt_digest != expected_prompt_sha256:
        raise PreAdapterRejection(LiveLightningExecutionFailureCode.PROMPT_HASH_MISMATCH)


def create_qwen_vision_adapter(
    runtime_config: QwenVisionRuntimeConfig,
    *,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    generation_runner: QwenGenerationRunner,
) -> QwenVisionAdapter:
    """Construct the existing adapter only with explicit policy, prompt, and runner inputs."""

    if not isinstance(prompt, str) or not prompt:
        raise ValueError("the live glue boundary requires a non-empty explicit prompt")
    return QwenVisionAdapter(
        runtime_config,
        content_policy=content_policy,
        prompt=prompt,
        generation_runner=generation_runner,
    )


def run_feat018_live_lightning_execution(
    request: VisionUnderstandingRequestV2,
    *,
    adapter: VisionUnderstandingPortV2,
    caps: LiveLightningExecutionCaps,
    runner: Feat018BoundedKillableQwenGenerationRunner | None = None,
    pre_adapter_check: Callable[[], object] | None = None,
    prompt_text: str | None = None,
    expected_prompt_sha256: str | None = None,
    mapper: RawMapper | None = None,
    session_id: str = "feat018-live-smoke",
    content_policy: ObservableContentPolicyV1 | None = None,
    clock: Callable[[], float] = time.monotonic,
    result_clock: Callable[[], datetime] = _utc_now,
    cleanup: ResourceCleanup | None = None,
) -> LiveLightningExecutionResult:
    """Run one adapter call with no outer retry and a finally-enforced cleanup hook."""

    adapter_call_count = 0
    attempt_count: int | None = None
    vision_result: VisionUnderstandingResultV2 | None = None
    mapped_result: object | None = None
    run_failure_code: LiveLightningExecutionFailureCode | None = None
    cleanup_status: Literal["SUCCEEDED", "FAILED"] = "SUCCEEDED"
    adapter_wall_clock_ms: float | None = None
    adapter_start: float | None = None
    total_deadline = clock() + caps.total_adapter_cap_seconds

    try:
        try:
            _require_safe_identifier(request.correlation_id)
            _require_safe_identifier(session_id)
        except ValueError:
            raise PreAdapterRejection() from None
        if pre_adapter_check is not None:
            try:
                if pre_adapter_check() is False:
                    raise PreAdapterRejection()
            except PreAdapterRejection:
                raise
            except Exception:
                raise PreAdapterRejection() from None
        _prompt_guard(
            prompt_text,
            expected_prompt_sha256,
            require_explicit=runner is not None,
        )
        adapter_call_count = 1
        adapter_start = clock()
        try:
            if runner is not None:
                vision_result = runner.run_adapter_call(adapter, request)
            else:
                vision_result = adapter.understand(request)
        except (
            QwenModelLoadError,
            QwenDeviceUnavailableError,
            QwenTimeoutError,
            QwenTransientRuntimeError,
            QwenPermanentRuntimeError,
        ) as exc:
            trace_attempts = len(runner.last_attempt_trace) if runner is not None else 0
            typed_failure = _typed_failure_for_exception(
                request,
                exc,
                attempt_number=trace_attempts,
                content_policy=content_policy,
                result_clock=result_clock,
            ) if content_policy is not None else None
            if typed_failure is not None:
                vision_result = typed_failure
                attempt_count = typed_failure.attempt_number
            else:
                run_failure_code = (
                    runner.last_failure_code
                    if runner is not None and runner.last_failure_code is not None
                    else LiveLightningExecutionFailureCode.ADAPTER_EXCEPTION
                )
        except Exception:
            run_failure_code = LiveLightningExecutionFailureCode.ADAPTER_EXCEPTION
        finally:
            if adapter_start is not None:
                adapter_wall_clock_ms = max(0.0, (clock() - adapter_start) * 1000.0)

        if (
            run_failure_code is None
            and runner is not None
            and runner.last_failure_code
            in {
                LiveLightningExecutionFailureCode.TOTAL_ADAPTER_CAP_EXCEEDED,
                LiveLightningExecutionFailureCode.PER_ATTEMPT_TIMEOUT,
                LiveLightningExecutionFailureCode.MALFORMED_CHILD_RESPONSE,
                LiveLightningExecutionFailureCode.RAW_OUTPUT_TOO_LARGE,
                LiveLightningExecutionFailureCode.IPC_ENVELOPE_TOO_LARGE,
                LiveLightningExecutionFailureCode.STDOUT_TOO_LARGE,
                LiveLightningExecutionFailureCode.STDERR_TOO_LARGE,
                LiveLightningExecutionFailureCode.PROCESS_START_FAILED,
                LiveLightningExecutionFailureCode.PROCESS_TERMINATION_FAILED,
                LiveLightningExecutionFailureCode.CLEANUP_FAILED,
            }
        ):
            run_failure_code = runner.last_failure_code

        if vision_result is not None:
            try:
                if not isinstance(
                    vision_result, (VisionUnderstandingSuccessV2, VisionUnderstandingFailureV2)
                ):
                    raise _RunnerFailure(LiveLightningExecutionFailureCode.ADAPTER_RESULT_MALFORMED)
                _validate_result_cardinality(vision_result, runner=runner, adapter=adapter)
                attempt_count = vision_result.attempt_number
            except _RunnerFailure as exc:
                if run_failure_code is None:
                    run_failure_code = exc.code

        if run_failure_code is None and adapter_start is not None and clock() >= total_deadline:
            run_failure_code = LiveLightningExecutionFailureCode.TOTAL_ADAPTER_CAP_EXCEEDED

        if run_failure_code is None and vision_result is not None and mapper is not None:
            try:
                mapped_result = mapper(
                    vision_result,
                    session_id=session_id,
                    expected_source_sha256=request.source_image_ref.sha256,
                    expected_correlation_id=request.correlation_id,
                    asr_result=None,
                )
            except Exception:
                run_failure_code = LiveLightningExecutionFailureCode.MAPPER_FAILED
    except PreAdapterRejection as exc:
        run_failure_code = exc.code
        adapter_call_count = 0
        attempt_count = None
        vision_result = None
        mapped_result = None
    except Exception:
        run_failure_code = LiveLightningExecutionFailureCode.ADAPTER_EXCEPTION
    finally:
        if cleanup is not None:
            try:
                cleanup()
            except Exception:
                cleanup_status = "FAILED"
                run_failure_code = LiveLightningExecutionFailureCode.CLEANUP_FAILED

    status: Literal["SUCCEEDED", "FAILED"] = (
        "SUCCEEDED"
        if run_failure_code is None
        and isinstance(vision_result, VisionUnderstandingSuccessV2)
        else "FAILED"
    )
    return LiveLightningExecutionResult(
        status=status,
        adapter_call_count=adapter_call_count,
        attempt_count=attempt_count,
        vision_result=vision_result,
        mapped_result=mapped_result,
        run_failure_code=run_failure_code,
        cleanup_status=cleanup_status,
        adapter_wall_clock_ms=adapter_wall_clock_ms,
    )


@dataclass(frozen=True, slots=True)
class Feat018LiveLightningExecutionCoordinator:
    """Reusable coordinator facade with caps and optional bounded runner fixed at construction."""

    caps: LiveLightningExecutionCaps
    runner: Feat018BoundedKillableQwenGenerationRunner | None = None

    def run(
        self,
        request: VisionUnderstandingRequestV2,
        *,
        adapter: VisionUnderstandingPortV2,
        pre_adapter_check: Callable[[], object] | None = None,
        prompt_text: str | None = None,
        expected_prompt_sha256: str | None = None,
        mapper: RawMapper | None = None,
        session_id: str = "feat018-live-smoke",
        content_policy: ObservableContentPolicyV1 | None = None,
        clock: Callable[[], float] = time.monotonic,
        result_clock: Callable[[], datetime] = _utc_now,
        cleanup: ResourceCleanup | None = None,
    ) -> LiveLightningExecutionResult:
        return run_feat018_live_lightning_execution(
            request,
            adapter=adapter,
            caps=self.caps,
            runner=self.runner,
            pre_adapter_check=pre_adapter_check,
            prompt_text=prompt_text,
            expected_prompt_sha256=expected_prompt_sha256,
            mapper=mapper,
            session_id=session_id,
            content_policy=content_policy,
            clock=clock,
            result_clock=result_clock,
            cleanup=cleanup,
        )


def _write_new_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(content)


def write_sanitized_evidence_pair(
    evidence: Mapping[str, object],
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write exactly two bounded, allowlisted artifacts without overwriting either target."""

    safe_evidence = _validate_safe_evidence(evidence)
    for path in (json_path, markdown_path):
        if path.is_absolute():
            raise ValueError("evidence paths must be relative")
        if path == Path.cwd() or Path.cwd() not in path.resolve().parents:
            raise ValueError("evidence path escaped the working directory")
        if path.exists():
            raise FileExistsError("evidence artifact already exists")
    json_text = json.dumps(safe_evidence, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    markdown_lines = ["# FEAT-018 live Lightning execution", ""]
    for key, value in safe_evidence.items():
        markdown_lines.append(
            f"- `{key}`: `{json.dumps(value, ensure_ascii=True, sort_keys=True)}`"
        )
    markdown_text = "\n".join(markdown_lines) + "\n"
    json_created = False
    try:
        _write_new_file(json_path, json_text)
        json_created = True
        _write_new_file(markdown_path, markdown_text)
    except Exception:
        if json_created:
            with suppress(OSError):
                json_path.unlink()
        raise


def write_ignored_incident(
    run_id: str,
    failure_code: LiveLightningExecutionFailureCode,
    *,
    root: Path = Path("tmp"),
) -> Path:
    """Write the sole permitted safe fallback when the evidence pair cannot be completed."""

    _require_safe_identifier(run_id)
    if not isinstance(failure_code, LiveLightningExecutionFailureCode):
        raise ValueError("incident failure code is not allowlisted")
    if root.is_absolute() or root == Path.cwd() or Path.cwd() not in root.resolve().parents:
        raise ValueError("incident root must be a relative child of the working directory")
    incident_dir = root / f"feat018-live-lightning-incident-{run_id}"
    incident_path = incident_dir / "INCIDENT.md"
    if incident_dir.exists() or incident_path.exists():
        raise FileExistsError("incident artifact already exists")
    _write_new_file(
        incident_path,
        "# FEAT-018 live Lightning incident\n\n"
        f"- incident_status: EVIDENCE_NOT_COMPLETED\n"
        f"- failure_code: {failure_code.value}\n"
        "- raw_output: NOT_RECORDED\n"
        "- prompt: NOT_RECORDED\n"
        "- credentials: NOT_RECORDED\n",
    )
    return incident_path


# Compatibility aliases keep the feature-local boundary easy to discover without introducing a
# second implementation or a parallel contract family.
run_live_lightning_smoke = run_feat018_live_lightning_execution


__all__ = [
    "Feat018BoundedKillableQwenGenerationRunner",
    "Feat018LiveLightningExecutionCoordinator",
    "GenerationAttemptOutcome",
    "LiveLightningExecutionCaps",
    "LiveLightningExecutionFailureCode",
    "LiveLightningExecutionResult",
    "PER_ATTEMPT_TIMEOUT_SECONDS",
    "PreAdapterRejection",
    "create_qwen_vision_adapter",
    "run_feat018_live_lightning_execution",
    "run_live_lightning_smoke",
    "write_ignored_incident",
    "write_sanitized_evidence_pair",
]
