"""FEAT-018 P2-T2 bounded execution and evidence primitives (offline stage).

Approved scope: see the owner-approved package at
``features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_BOUNDED_RUNNER_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260914.md``
(revision 5) and the "Approved P2-T2 bounded-runner offline implementation addendum" in
``features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md``. This module and its test
file are the exact and only approved implementation surface. It never modifies
``sketch2life.infrastructure.ai.qwen_vision`` or any other FEAT-003/FEAT-017 source; it consumes
``QwenVisionAdapter`` only through its existing ``generation_runner`` injection seam.

Nothing in this module opens a Lightning session, loads a model, uses a GPU, or calls a network
or provider endpoint. Real subprocess/containment code exists here because it is the eventual
live-run mechanism, but it is never exercised by this module's own offline test suite, which
drives every class through injected fakes (fake clocks, fake process launchers, fake containment
backends, fake filesystems). A live run requires a separate, later execution approval that
resolves ``P2T2-LIVE-D1`` through ``P2T2-LIVE-D12``.
"""

from __future__ import annotations

import contextlib
import ctypes
import json
import math
import multiprocessing
import os
import stat
import sys
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol, cast

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.application.services.raw_understanding_mapper import map_vision_result_to_raw
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
)
from sketch2life.infrastructure.ai.qwen_vision import (
    QwenDeviceUnavailableError,
    QwenModelLoadError,
    QwenPermanentRuntimeError,
    QwenTimeoutError,
    QwenVisionAdapter,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig

# --------------------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------------------


class Feat018ProtocolViolationError(Exception):
    """A supervisor IPC frame violated the bounded framing or state-machine contract."""


class Feat018ContainmentError(Exception):
    """Containment could not be created, established, verified, or torn down."""


class Feat018CleanupFailedError(Exception):
    """Cleanup could not confirm the containment (and everything in it) is terminated."""


class Feat018LauncherError(Exception):
    """A bounded generation or adapter process could not be launched."""


class Feat018EvidenceCommitError(Exception):
    """The evidence pair could not reach the authoritative committed state."""


class Feat018FrameTooLargeError(Feat018ProtocolViolationError):
    """A payload exceeded its configured byte ceiling before it was allowed to cross IPC."""


def _positive_finite_float(value: object) -> float | None:
    """Return a duration only when it is a real, finite, strictly positive number."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(converted) or converted <= 0:
        return None
    return converted


_BOUNDED_OPAQUE_ID_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-"
)
_BOUNDED_OPAQUE_ID_MAX_LENGTH = 64


def _is_bounded_opaque_identifier(value: object) -> bool:
    """Accept only safe logical identifiers, never paths, URLs, or secret-bearing text."""

    return (
        isinstance(value, str)
        and 1 <= len(value) <= _BOUNDED_OPAQUE_ID_MAX_LENGTH
        and all(character in _BOUNDED_OPAQUE_ID_CHARACTERS for character in value)
    )


# --------------------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Feat018BoundedRunnerConfig:
    """Every numeric bound this package's design requires to be explicit and positive.

    Nothing here is authorized by this file alone: every value must be named by a future,
    separate live-execution approval resolving ``P2T2-LIVE-D2`` (TTL/budget) and
    ``P2T2-LIVE-D9`` (byte ceilings). This dataclass only proves the bounds are enforceable.
    """

    total_adapter_cap_seconds: float
    raw_output_max_bytes: int
    ipc_envelope_max_bytes: int
    stdout_max_bytes: int = 0
    stderr_max_bytes: int = 0
    cleanup_deadline_seconds: float = 5.0
    containment_setup_timeout_seconds: float = 5.0
    posix_confirmation_timeout_seconds: float = 2.0
    posix_confirmation_retry_interval_seconds: float = 0.02
    per_attempt_timeout_seconds: float = 120.0
    poll_interval_seconds: float = 0.05

    def __post_init__(self) -> None:
        if self.total_adapter_cap_seconds <= 0:
            raise ValueError("total_adapter_cap_seconds must be positive")
        if self.raw_output_max_bytes <= 0:
            raise ValueError("raw_output_max_bytes must be a positive integer (D9)")
        if self.ipc_envelope_max_bytes <= 0:
            raise ValueError("ipc_envelope_max_bytes must be a positive integer (D9)")
        if self.stdout_max_bytes < 0:
            raise ValueError("stdout_max_bytes must be a non-negative integer (D9)")
        if self.stderr_max_bytes < 0:
            raise ValueError("stderr_max_bytes must be a non-negative integer (D9)")
        if self.cleanup_deadline_seconds <= 0:
            raise ValueError("cleanup_deadline_seconds must be positive")
        if self.containment_setup_timeout_seconds <= 0:
            raise ValueError("containment_setup_timeout_seconds must be positive")
        if self.posix_confirmation_timeout_seconds <= 0:
            raise ValueError("posix_confirmation_timeout_seconds must be positive")
        if self.posix_confirmation_retry_interval_seconds <= 0:
            raise ValueError("posix_confirmation_retry_interval_seconds must be positive")
        if self.per_attempt_timeout_seconds <= 0 or self.per_attempt_timeout_seconds > 120.0:
            raise ValueError("per_attempt_timeout_seconds must be in (0, 120.0]")
        if self.poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")


# --------------------------------------------------------------------------------------
# Bounded frame envelope (byte-boundary and receive-side limits)
# --------------------------------------------------------------------------------------


def encode_envelope(payload: Mapping[str, object], *, max_bytes: int) -> bytes:
    """Canonical, size-proven JSON bytes. Raises before any oversized value can be sent.

    This is "proving the envelope fits its exact byte ceiling before sending": the caller
    must call this before ``Connection.send_bytes`` and never send an unbounded value.
    """

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > max_bytes:
        raise Feat018FrameTooLargeError(
            f"envelope of {len(encoded)} bytes exceeds the {max_bytes}-byte ceiling"
        )
    return encoded


def decode_envelope(raw: bytes) -> dict[str, object]:
    """Decode a frame already proven to be within its byte ceiling by the transport."""

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise Feat018ProtocolViolationError("malformed envelope: not valid UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise Feat018ProtocolViolationError("malformed envelope: root is not a JSON object")
    return parsed


class BoundedConnection(Protocol):
    """The bounded supervisor<->worker transport seam, real or fake.

    A real implementation wraps :class:`multiprocessing.connection.Connection`, whose own
    ``recv_bytes(maxlength=...)`` already reads and checks a declared frame length before
    reading or returning any payload byte -- exactly the "validate the declared frame length
    before accepting or decoding the payload" requirement -- so no hand-rolled length header
    is reinvented here.
    """

    def send_frame(self, payload: Mapping[str, object]) -> None: ...

    def recv_frame(self, timeout: float) -> dict[str, object] | None:
        """Return the next frame, or ``None`` if none arrives within ``timeout`` seconds."""

    def close(self) -> None: ...


class _RawConnection(Protocol):
    """The subset of ``multiprocessing.connection.Connection`` this module depends on.

    A structural protocol (rather than the concrete ``Connection`` class) so both the POSIX
    ``Connection`` and the Windows ``PipeConnection`` returned by ``multiprocessing.Pipe``
    satisfy it without a cross-platform generic mismatch.
    """

    def send_bytes(self, buf: bytes) -> None: ...

    def recv_bytes(self, maxlength: int | None = None) -> bytes: ...

    def poll(self, timeout: float | None = None) -> bool: ...

    def close(self) -> None: ...


@dataclass(slots=True)
class MultiprocessingBoundedConnection:
    """Real transport: one :class:`multiprocessing.connection.Connection` end, bounded."""

    connection: _RawConnection
    max_envelope_bytes: int

    def send_frame(self, payload: Mapping[str, object]) -> None:
        self.connection.send_bytes(encode_envelope(payload, max_bytes=self.max_envelope_bytes))

    def recv_frame(self, timeout: float) -> dict[str, object] | None:
        if timeout <= 0 or not self.connection.poll(max(timeout, 0.0)):
            return None
        try:
            raw = self.connection.recv_bytes(maxlength=self.max_envelope_bytes)
        except OSError as exc:
            raise Feat018ProtocolViolationError(
                "declared frame length exceeds the IPC envelope ceiling"
            ) from exc
        except EOFError:
            return None
        return decode_envelope(raw)

    def close(self) -> None:
        with contextlib.suppress(OSError):
            self.connection.close()


# --------------------------------------------------------------------------------------
# Supervisor progress state machine and deadline freeze
# --------------------------------------------------------------------------------------


class ProgressState(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    ADAPTER_STARTED = "ADAPTER_STARTED"
    GENERATION_ATTEMPT_1 = "GENERATION_ATTEMPT_STARTED_1"
    GENERATION_ATTEMPT_2 = "GENERATION_ATTEMPT_STARTED_2"
    TERMINAL = "TERMINAL"
    FROZEN = "FROZEN"


class ProgressEventKind(StrEnum):
    ADAPTER_STARTED = "ADAPTER_STARTED"
    GENERATION_ATTEMPT_STARTED = "GENERATION_ATTEMPT_STARTED"
    TERMINAL = "TERMINAL"


class AcceptanceResult(StrEnum):
    """Every disposition :meth:`Feat018ProgressStateMachine.accept` can return."""

    ACCEPTED = "ACCEPTED"
    REJECTED_DUPLICATE = "REJECTED_DUPLICATE"
    REJECTED_GAP = "REJECTED_GAP"
    REJECTED_INVALID_TRANSITION = "REJECTED_INVALID_TRANSITION"
    REJECTED_DEADLINE = "REJECTED_DEADLINE"
    REJECTED_CLOSED = "REJECTED_CLOSED"


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """One worker-authored, sequenced event. Never carries raw output or prompt text."""

    seq: int
    kind: ProgressEventKind
    attempt_number: int | None = None
    outcome: str | None = None
    raw_status: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.seq, int) or isinstance(self.seq, bool) or self.seq < 1:
            raise ValueError("seq must start at 1")
        if not isinstance(self.kind, ProgressEventKind):
            raise ValueError("kind must be a ProgressEventKind")
        if isinstance(self.attempt_number, bool):
            raise ValueError("attempt_number must be an integer")
        if self.kind is ProgressEventKind.GENERATION_ATTEMPT_STARTED:
            if self.attempt_number not in (1, 2):
                raise ValueError("GENERATION_ATTEMPT_STARTED requires attempt_number in {1, 2}")
        elif self.attempt_number is not None:
            raise ValueError(f"{self.kind} must not carry attempt_number")
        if self.kind is ProgressEventKind.TERMINAL and self.outcome not in ("SUCCEEDED", "FAILED"):
            raise ValueError("TERMINAL requires a bounded outcome")
        if self.kind is not ProgressEventKind.TERMINAL and self.outcome is not None:
            raise ValueError(f"{self.kind} must not carry an outcome")
        if self.raw_status is not None and (
            self.kind is not ProgressEventKind.TERMINAL
            or self.raw_status not in ("SUCCEEDED", "FAILED")
            or self.raw_status != self.outcome
        ):
            raise ValueError("raw_status requires a matching terminal outcome")


_VALID_TRANSITIONS: dict[ProgressState, frozenset[ProgressEventKind]] = {
    ProgressState.NOT_STARTED: frozenset({ProgressEventKind.ADAPTER_STARTED}),
    ProgressState.ADAPTER_STARTED: frozenset(
        {ProgressEventKind.GENERATION_ATTEMPT_STARTED, ProgressEventKind.TERMINAL}
    ),
    ProgressState.GENERATION_ATTEMPT_1: frozenset(
        {ProgressEventKind.GENERATION_ATTEMPT_STARTED, ProgressEventKind.TERMINAL}
    ),
    ProgressState.GENERATION_ATTEMPT_2: frozenset({ProgressEventKind.TERMINAL}),
    ProgressState.TERMINAL: frozenset(),
    ProgressState.FROZEN: frozenset(),
}


class Feat018ProgressStateMachine:
    """The exact, closed acceptance rule from "Supervisor progress state machine..." .

    ``cap_deadline_monotonic`` here is always the *supervisor's own* authoritative deadline
    (see :class:`Feat018AdapterCallSupervisor`), never a worker-advised value.
    """

    def __init__(self, *, cap_deadline_monotonic: float) -> None:
        self._cap_deadline_monotonic = cap_deadline_monotonic
        self._state = ProgressState.NOT_STARTED
        self._last_accepted_seq = 0
        self._attempt_count: int | None = None
        self._terminal_outcome: str | None = None
        self._raw_status: str | None = None

    @property
    def state(self) -> ProgressState:
        return self._state

    @property
    def attempt_count(self) -> int | None:
        return self._attempt_count

    @property
    def terminal_outcome(self) -> str | None:
        return self._terminal_outcome

    @property
    def raw_status(self) -> str | None:
        return self._raw_status

    def force_freeze(self) -> None:
        """Called by the supervisor when its own bounded wait times out with no event at all."""

        if self._state not in (ProgressState.TERMINAL, ProgressState.FROZEN):
            self._state = ProgressState.FROZEN

    def accept(self, event: ProgressEvent, *, acceptance_time: float) -> AcceptanceResult:
        """Apply one event. ``acceptance_time`` must be the supervisor's own clock reading
        captured when the complete, framing-validated frame first became available --
        never when it started arriving, and never recomputed afterward by the caller.
        """

        if self._state in (ProgressState.TERMINAL, ProgressState.FROZEN):
            return AcceptanceResult.REJECTED_CLOSED
        if _positive_finite_float(self._cap_deadline_monotonic - acceptance_time) is None:
            self._state = ProgressState.FROZEN
            return AcceptanceResult.REJECTED_DEADLINE
        if event.seq <= self._last_accepted_seq:
            return AcceptanceResult.REJECTED_DUPLICATE
        if event.seq > self._last_accepted_seq + 1:
            return AcceptanceResult.REJECTED_GAP
        if event.kind not in _VALID_TRANSITIONS[self._state]:
            return AcceptanceResult.REJECTED_INVALID_TRANSITION
        if (
            event.kind is ProgressEventKind.GENERATION_ATTEMPT_STARTED
            and event.attempt_number == 1
            and self._state is not ProgressState.ADAPTER_STARTED
        ):
            return AcceptanceResult.REJECTED_INVALID_TRANSITION
        if (
            event.kind is ProgressEventKind.GENERATION_ATTEMPT_STARTED
            and event.attempt_number == 2
            and self._state is not ProgressState.GENERATION_ATTEMPT_1
        ):
            return AcceptanceResult.REJECTED_INVALID_TRANSITION

        self._last_accepted_seq = event.seq
        if event.kind is ProgressEventKind.ADAPTER_STARTED:
            self._state = ProgressState.ADAPTER_STARTED
        elif event.kind is ProgressEventKind.GENERATION_ATTEMPT_STARTED:
            self._attempt_count = event.attempt_number
            self._state = (
                ProgressState.GENERATION_ATTEMPT_1
                if event.attempt_number == 1
                else ProgressState.GENERATION_ATTEMPT_2
            )
        else:
            self._terminal_outcome = event.outcome
            self._raw_status = event.raw_status
            self._state = ProgressState.TERMINAL
        return AcceptanceResult.ACCEPTED


# --------------------------------------------------------------------------------------
# Containment: race-free CONTAINMENT_READY gate protocol
# --------------------------------------------------------------------------------------


class ProcessHandle(Protocol):
    """The minimal process-control seam the supervisor and containment backends need."""

    @property
    def pid(self) -> int | None: ...

    def is_alive(self) -> bool: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    def join(self, timeout: float | None = None) -> None: ...


class _LaunchProcess(ProcessHandle, Protocol):
    """A process handle before launch, which additionally supports ``start()``."""

    def start(self) -> None: ...


class _MultiprocessingContext(Protocol):
    """The injectable subset of a spawn multiprocessing context used by the launcher."""

    def Pipe(self, duplex: bool = True) -> tuple[_RawConnection, _RawConnection]: ...

    def Process(
        self,
        *,
        target: Callable[..., None],
        args: tuple[object, ...],
        daemon: bool,
    ) -> _LaunchProcess: ...


def _default_spawn_context() -> _MultiprocessingContext:
    return cast(_MultiprocessingContext, multiprocessing.get_context("spawn"))


def _default_bounded_connection_factory(
    connection: _RawConnection, max_envelope_bytes: int
) -> BoundedConnection:
    return MultiprocessingBoundedConnection(
        connection=connection, max_envelope_bytes=max_envelope_bytes
    )


class ContainmentBackend(Protocol):
    """One OS-level containment primitive (POSIX process group, or Windows job object).

    Callers must call :meth:`create` before spawning the worker, then
    :meth:`confirm_worker_contained` before ever releasing it (see
    :class:`Feat018AdapterCallSupervisor`). Cleanup uses :meth:`terminate_all`/:meth:`is_empty`,
    never a PID reported later by the worker.
    """

    def create(self) -> None:
        """Create the containment primitive. Raise :class:`Feat018ContainmentError` on failure."""

    def confirm_worker_contained(
        self, worker: ProcessHandle, *, timeout: float, retry_interval: float
    ) -> bool:
        """Bounded retry/poll confirming ``worker`` is inside this containment.

        Must return within ``timeout`` seconds. A ``False`` return (not an exception) is the
        normal "could not confirm in time" outcome; the caller fails closed on it.
        """

    def terminate_all(self) -> None:
        """Terminate every process in this containment in one action."""

    def is_empty(self) -> bool:
        """Return whether the containment currently has zero live members."""

    def close(self) -> None:
        """Release the containment primitive itself (not its members)."""


def posix_worker_self_contain() -> None:
    """The worker's own first instruction on POSIX: enter a brand-new process group.

    Must be called before any other code in the worker's entry function. Never called on
    Windows, where containment is external (job-object assignment) rather than self-applied.
    """

    setpgrp = getattr(os, "setpgrp", None)
    if setpgrp is not None:
        setpgrp()


def _posix_getpgid(pid: int) -> int:
    """``os.getpgid`` is POSIX-only; this indirection keeps the module importable on Windows."""

    getpgid = getattr(os, "getpgid", None)
    if getpgid is None:
        raise OSError("os.getpgid is unavailable on this platform")
    return int(getpgid(pid))


def _posix_killpg(pgid: int, sig: int) -> None:
    """``os.killpg`` is POSIX-only; this indirection keeps the module importable on Windows."""

    killpg = getattr(os, "killpg", None)
    if killpg is None:
        raise OSError("os.killpg is unavailable on this platform")
    killpg(pgid, sig)


@dataclass(slots=True)
class PosixProcessGroupContainment:
    """POSIX containment: the worker's own new process group, confirmed from outside.

    Correctness depends on :func:`posix_worker_self_contain` running as the worker's first
    instruction; this class only confirms and later terminates that group. Confirmation is a
    bounded retry loop, never a single racy check (independent-audit finding A2-2).
    """

    _group_pid: int | None = field(default=None, init=False)
    _probe: Callable[[int], int] = field(default=_posix_getpgid, repr=False)
    _clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    _sleep: Callable[[float], None] = field(default=time.sleep, repr=False)

    def create(self) -> None:
        return None

    def confirm_worker_contained(
        self, worker: ProcessHandle, *, timeout: float, retry_interval: float
    ) -> bool:
        if worker.pid is None:
            return False
        deadline = self._clock() + timeout
        while True:
            try:
                observed_pgid = self._probe(worker.pid)
            except OSError:
                observed_pgid = None
            if observed_pgid == worker.pid:
                self._group_pid = worker.pid
                return True
            if self._clock() >= deadline:
                return False
            self._sleep(retry_interval)

    def terminate_all(self) -> None:
        if self._group_pid is None:
            return
        with contextlib.suppress(OSError):
            _posix_killpg(self._group_pid, 15)  # SIGTERM

    def is_empty(self) -> bool:
        if self._group_pid is None:
            return True
        try:
            _posix_killpg(self._group_pid, 0)
        except ProcessLookupError:
            return True
        except OSError:
            return False
        return False

    def close(self) -> None:
        return None


_WIN32_HANDLE = ctypes.c_void_p
_WIN32_DWORD = ctypes.c_uint32
_WIN32_BOOL = ctypes.c_int32
_WIN32_LPCWSTR = ctypes.c_wchar_p


class _JobObjectBasicLimitInformation(ctypes.Structure):
    _fields_ = (
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", _WIN32_DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", _WIN32_DWORD),
        ("Affinity", ctypes.c_void_p),
        ("PriorityClass", _WIN32_DWORD),
        ("SchedulingClass", _WIN32_DWORD),
    )


class _JobObjectIoCounters(ctypes.Structure):
    _fields_ = (
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    )


class _JobObjectExtendedLimitInformation(ctypes.Structure):
    _fields_ = (
        ("BasicLimitInformation", _JobObjectBasicLimitInformation),
        ("IoInfo", _JobObjectIoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    )


class _JobObjectBasicAccountingInformation(ctypes.Structure):
    _fields_ = (
        ("TotalUserTime", ctypes.c_int64),
        ("TotalKernelTime", ctypes.c_int64),
        ("ThisPeriodTotalUserTime", ctypes.c_int64),
        ("ThisPeriodTotalKernelTime", ctypes.c_int64),
        ("TotalPageFaultCount", _WIN32_DWORD),
        ("TotalProcesses", _WIN32_DWORD),
        ("ActiveProcesses", _WIN32_DWORD),
        ("TotalTerminatedProcesses", _WIN32_DWORD),
    )


class _Win32JobHandles:
    """Explicitly-bound ctypes surface for job-object containment (F4).

    Every used Kernel32 function is given explicit ``argtypes``/``restype`` using
    pointer-width-safe ``c_void_p``-based HANDLE types -- never a bare PID standing in for a
    handle (independent-review finding A2-1). ``kernel32`` is injectable so tests can exercise
    this exact binding surface, including 64-bit handle values and access-mask bits, against a
    fake Win32 API double instead of the real DLL.
    """

    PROCESS_TERMINATE = 0x0001
    PROCESS_SET_QUOTA = 0x0100
    # Required by IsProcessInJob in addition to the AssignProcessToJobObject rights above.
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    PROCESS_ACCESS_RIGHTS = (
        PROCESS_TERMINATE | PROCESS_SET_QUOTA | PROCESS_QUERY_LIMITED_INFORMATION
    )

    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
    JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS = 1

    def __init__(self, kernel32: Any = None) -> None:
        self._kernel32: Any = kernel32 if kernel32 is not None else ctypes.windll.kernel32
        self._bind_signatures()

    def _bind_signatures(self) -> None:
        k: Any = self._kernel32
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, _WIN32_LPCWSTR]
        k.CreateJobObjectW.restype = _WIN32_HANDLE
        k.SetInformationJobObject.argtypes = [
            _WIN32_HANDLE,
            _WIN32_DWORD,
            ctypes.c_void_p,
            _WIN32_DWORD,
        ]
        k.SetInformationJobObject.restype = _WIN32_BOOL
        k.QueryInformationJobObject.argtypes = [
            _WIN32_HANDLE,
            _WIN32_DWORD,
            ctypes.c_void_p,
            _WIN32_DWORD,
            ctypes.POINTER(_WIN32_DWORD),
        ]
        k.QueryInformationJobObject.restype = _WIN32_BOOL
        k.OpenProcess.argtypes = [_WIN32_DWORD, _WIN32_BOOL, _WIN32_DWORD]
        k.OpenProcess.restype = _WIN32_HANDLE
        k.AssignProcessToJobObject.argtypes = [_WIN32_HANDLE, _WIN32_HANDLE]
        k.AssignProcessToJobObject.restype = _WIN32_BOOL
        k.IsProcessInJob.argtypes = [_WIN32_HANDLE, _WIN32_HANDLE, ctypes.POINTER(_WIN32_BOOL)]
        k.IsProcessInJob.restype = _WIN32_BOOL
        k.TerminateJobObject.argtypes = [_WIN32_HANDLE, ctypes.c_uint32]
        k.TerminateJobObject.restype = _WIN32_BOOL
        k.CloseHandle.argtypes = [_WIN32_HANDLE]
        k.CloseHandle.restype = _WIN32_BOOL

    def create_job_object(self) -> int:
        handle = self._kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise Feat018ContainmentError("CreateJobObjectW failed")
        return int(handle)

    def set_kill_on_close(self, job_handle: int) -> None:
        info = _JobObjectExtendedLimitInformation()
        info.BasicLimitInformation.LimitFlags = self.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        ok = self._kernel32.SetInformationJobObject(
            job_handle,
            self.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
            ctypes.pointer(info),
            ctypes.sizeof(info),
        )
        if not ok:
            raise Feat018ContainmentError("SetInformationJobObject failed")

    def query_active_process_count(self, job_handle: int) -> int:
        """F1: the truthful basis for ``is_empty()`` -- never assumed, always queried."""

        info = _JobObjectBasicAccountingInformation()
        returned = _WIN32_DWORD(0)
        ok = self._kernel32.QueryInformationJobObject(
            job_handle,
            self.JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS,
            ctypes.pointer(info),
            ctypes.sizeof(info),
            ctypes.pointer(returned),
        )
        if not ok:
            raise Feat018ContainmentError("QueryInformationJobObject failed")
        return int(info.ActiveProcesses)

    def open_process(self, pid: int) -> int:
        handle = self._kernel32.OpenProcess(self.PROCESS_ACCESS_RIGHTS, False, pid)
        if not handle:
            raise Feat018ContainmentError("OpenProcess failed")
        return int(handle)

    def assign_process_to_job_object(self, job_handle: int, process_handle: int) -> bool:
        return bool(self._kernel32.AssignProcessToJobObject(job_handle, process_handle))

    def is_process_in_job(self, process_handle: int, job_handle: int) -> bool:
        result = _WIN32_BOOL(0)
        ok = self._kernel32.IsProcessInJob(process_handle, job_handle, ctypes.pointer(result))
        return bool(ok) and bool(result.value)

    def terminate_job_object(self, job_handle: int) -> None:
        if not self._kernel32.TerminateJobObject(job_handle, 1):
            raise Feat018ContainmentError("TerminateJobObject failed")

    def close_handle(self, handle: int) -> None:
        if not self._kernel32.CloseHandle(handle):
            raise Feat018ContainmentError("CloseHandle failed")


@dataclass(slots=True)
class WindowsJobObjectContainment:
    """Windows containment: one job object, a verified process *handle* (not a bare PID)."""

    _job_handle: int | None = field(default=None, init=False)
    _process_handle: int | None = field(default=None, init=False)
    _cleanup_failed: bool = field(default=False, init=False, repr=False)
    _win32: _Win32JobHandles = field(default_factory=lambda: _Win32JobHandles())

    def create(self) -> None:
        self._cleanup_failed = False
        job_handle = self._win32.create_job_object()
        self._job_handle = job_handle
        try:
            self._win32.set_kill_on_close(job_handle)
        except Exception:  # noqa: BLE001 - rollback must not leak the partial job object
            rollback_failed = False
            try:
                self._win32.terminate_job_object(job_handle)
            except Exception:  # noqa: BLE001 - still attempt CloseHandle
                rollback_failed = True
            try:
                self.close()
            except Exception:  # noqa: BLE001 - report the partial cleanup failure below
                rollback_failed = True
            if rollback_failed:
                self._cleanup_failed = True
                raise Feat018ContainmentError(
                    "containment configuration failed and rollback cleanup failed"
                ) from None
            raise Feat018ContainmentError("containment configuration failed") from None

    def confirm_worker_contained(
        self, worker: ProcessHandle, *, timeout: float, retry_interval: float
    ) -> bool:
        if self._job_handle is None or worker.pid is None:
            return False
        try:
            process_handle = self._win32.open_process(worker.pid)
        except Feat018ContainmentError:
            return False
        try:
            assigned = self._win32.assign_process_to_job_object(self._job_handle, process_handle)
            verified = assigned and self._win32.is_process_in_job(
                process_handle, self._job_handle
            )
        except Exception:  # noqa: BLE001 - close the unregistered process handle
            try:
                self._win32.close_handle(process_handle)
            except Exception:  # noqa: BLE001 - assignment already failed; fail closed
                self._cleanup_failed = True
            raise
        if not verified:
            try:
                self._win32.close_handle(process_handle)
            except Exception:  # noqa: BLE001 - verification failed; fail closed
                self._cleanup_failed = True
            return False
        self._process_handle = process_handle
        return True

    def terminate_all(self) -> None:
        if self._job_handle is not None:
            self._win32.terminate_job_object(self._job_handle)

    def is_empty(self) -> bool:
        """F1: truthful, queried emptiness. A query failure fails closed (never ``True``)."""

        if self._job_handle is None:
            return not self._cleanup_failed
        try:
            active_count = self._win32.query_active_process_count(self._job_handle)
        except Feat018ContainmentError:
            self._cleanup_failed = True
            return False
        return active_count == 0

    def close(self) -> None:
        process_handle = self._process_handle
        job_handle = self._job_handle
        self._process_handle = None
        self._job_handle = None
        close_failed = False
        if process_handle is not None:
            try:
                self._win32.close_handle(process_handle)
            except Exception:  # noqa: BLE001 - always continue to the job handle
                close_failed = True
        if job_handle is not None:
            try:
                self._win32.close_handle(job_handle)
            except Exception:  # noqa: BLE001 - report after both handles were attempted
                close_failed = True
        if close_failed:
            self._cleanup_failed = True
            raise Feat018ContainmentError("containment handle cleanup failed")


def create_platform_containment() -> ContainmentBackend:
    """Select the real containment backend for the current OS. Never used by offline tests."""

    if sys.platform == "win32":
        return WindowsJobObjectContainment()
    return PosixProcessGroupContainment()


# --------------------------------------------------------------------------------------
# Process launcher seam (real vs. fake)
# --------------------------------------------------------------------------------------


class ProcessLauncher(Protocol):
    """Creates one child process plus its bounded duplex connection."""

    def launch(
        self, entry: Callable[..., None], args: tuple[object, ...]
    ) -> tuple[ProcessHandle, BoundedConnection]: ...


@dataclass(slots=True)
class MultiprocessingProcessLauncher:
    """Create one non-daemon bounded process with exception-safe ownership cleanup.

    The default context is the real ``spawn`` context, while ``context_factory`` and
    ``connection_factory`` are injectable so every launch failure can be tested without
    creating a real process.
    """

    max_envelope_bytes: int
    context_factory: Callable[[], _MultiprocessingContext] = field(
        default=_default_spawn_context, repr=False
    )
    connection_factory: Callable[[_RawConnection, int], BoundedConnection] = field(
        default=_default_bounded_connection_factory, repr=False
    )

    def launch(
        self, entry: Callable[..., None], args: tuple[object, ...]
    ) -> tuple[ProcessHandle, BoundedConnection]:
        parent_conn: _RawConnection | None = None
        child_conn: _RawConnection | None = None
        child_close_attempted = False
        parent_close_attempted = False
        process: _LaunchProcess | None = None
        process_start_attempted = False
        cleanup_failed = False

        try:
            context = self.context_factory()
            parent_conn, child_conn = context.Pipe(duplex=True)
            bounded_child_conn = self.connection_factory(
                child_conn, self.max_envelope_bytes
            )
            process = context.Process(
                target=entry,
                args=(bounded_child_conn, *args),
                daemon=False,
            )
            process_start_attempted = True
            process.start()

            child_close_attempted = True
            if not _close_owned_ipc_endpoint(child_conn):
                cleanup_failed = True
                raise Feat018CleanupFailedError from None

            bounded_parent_conn = self.connection_factory(
                parent_conn, self.max_envelope_bytes
            )
            return process, bounded_parent_conn
        except Exception:  # noqa: BLE001 - all failures become sanitized typed errors
            if (
                process is not None
                and process_start_attempted
                and not _bounded_terminate_kill_join(
                    process, grace_seconds=1.0, kill_join_seconds=1.0
                )
            ):
                cleanup_failed = True
            if child_conn is not None and not child_close_attempted:
                child_close_attempted = True
                if not _close_owned_ipc_endpoint(child_conn):
                    cleanup_failed = True
            if parent_conn is not None and not parent_close_attempted:
                parent_close_attempted = True
                if not _close_owned_ipc_endpoint(parent_conn):
                    cleanup_failed = True
            if cleanup_failed:
                raise Feat018CleanupFailedError("bounded process launch cleanup failed") from None
            raise Feat018LauncherError("bounded process launch failed") from None


def _close_owned_ipc_endpoint(connection: _RawConnection) -> bool:
    """Close one locally owned raw endpoint without leaking the original exception."""

    try:
        connection.close()
    except Exception:  # noqa: BLE001 - the caller reports a typed cleanup failure
        return False
    return True


def _bounded_terminate_kill_join(
    process: ProcessHandle, *, grace_seconds: float, kill_join_seconds: float
) -> bool:
    """Attempt bounded process cleanup and verify it is no longer alive."""

    cleanup_succeeded = True
    try:
        initially_alive: bool | None = bool(process.is_alive())
    except Exception:  # noqa: BLE001 - unknown liveness must fail closed
        initially_alive = None
        cleanup_succeeded = False

    if initially_alive is not False:
        try:
            process.terminate()
        except Exception:  # noqa: BLE001 - continue to the bounded join and kill attempt
            cleanup_succeeded = False
        try:
            process.join(timeout=grace_seconds)
        except Exception:  # noqa: BLE001 - continue to the bounded kill attempt
            cleanup_succeeded = False

        try:
            alive_after_grace: bool | None = bool(process.is_alive())
        except Exception:  # noqa: BLE001 - unknown liveness requires the kill attempt
            alive_after_grace = None
            cleanup_succeeded = False
        if alive_after_grace is not False:
            try:
                process.kill()
            except Exception:  # noqa: BLE001 - report failure without escaping cleanup
                cleanup_succeeded = False
            try:
                process.join(timeout=kill_join_seconds)
            except Exception:  # noqa: BLE001 - report failure without escaping cleanup
                cleanup_succeeded = False

    try:
        alive_after_cleanup = bool(process.is_alive())
    except Exception:  # noqa: BLE001 - final liveness cannot be verified
        alive_after_cleanup = True
        cleanup_succeeded = False
    if alive_after_cleanup:
        cleanup_succeeded = False
    return cleanup_succeeded


# --------------------------------------------------------------------------------------
# Per-attempt bounded generation runner
# --------------------------------------------------------------------------------------


def _generation_child_entry(
    connection: _RawConnection,
    profile: VisionProfileV2,
    runtime_config: QwenVisionRuntimeConfig,
    image_path: str,
    prompt: str,
    raw_output_max_bytes: int,
    ipc_envelope_max_bytes: int,
) -> None:
    """Real child target: load, generate, and send one bounded envelope. Not offline-tested."""

    from sketch2life.infrastructure.ai.qwen_vision import (  # noqa: PLC0415
        _default_model_factory,
        _generate_from_bundle,
    )

    bounded = MultiprocessingBoundedConnection(
        connection=connection, max_envelope_bytes=ipc_envelope_max_bytes
    )
    try:
        bundle = _default_model_factory(profile, runtime_config)
    except QwenDeviceUnavailableError:
        _try_send(bounded, {"kind": "device_unavailable"})
        return
    except QwenModelLoadError:
        _try_send(bounded, {"kind": "model_load_failed"})
        return
    except Exception:  # noqa: BLE001 - sanitized below
        _try_send(bounded, {"kind": "model_load_failed"})
        return

    try:
        raw_output = _generate_from_bundle(bundle, profile, Path(image_path), prompt)
    except QwenTimeoutError:
        _try_send(bounded, {"kind": "timeout"})
        return
    except Exception:  # noqa: BLE001 - sanitized below
        _try_send(bounded, {"kind": "provider_failure"})
        return

    encoded_length = len(raw_output.encode("utf-8"))
    if encoded_length > raw_output_max_bytes:
        _try_send(bounded, {"kind": "raw_output_overflow"})
        return
    try:
        bounded.send_frame({"kind": "success", "raw_output": raw_output})
    except Feat018FrameTooLargeError:
        _try_send(bounded, {"kind": "ipc_envelope_overflow"})


def _try_send(bounded: MultiprocessingBoundedConnection, payload: Mapping[str, object]) -> None:
    with contextlib.suppress(OSError):
        bounded.send_frame(payload)


@dataclass(slots=True)
class Feat018BoundedKillableQwenGenerationRunner:
    """Implements ``QwenGenerationRunner`` for exactly one attempt per call.

    Constructed fresh per adapter invocation, inside the adapter worker, immediately after
    ``worker_cap_deadline_monotonic`` is known. Never loops or retries internally: the real,
    unmodified ``QwenVisionAdapter.understand()`` owns the retry decision (see the adapter/retry
    compatibility contract in the approval package).
    """

    config: Feat018BoundedRunnerConfig
    worker_cap_deadline_monotonic: float
    launcher: ProcessLauncher
    clock: Callable[[], float] = time.monotonic
    on_attempt_start: Callable[[], None] | None = None

    def generate(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        remaining = self.worker_cap_deadline_monotonic - self.clock()
        positive_remaining = _positive_finite_float(remaining)
        if positive_remaining is None:
            raise QwenPermanentRuntimeError("total adapter cap already exhausted")
        attempt_deadline_seconds = min(self.config.per_attempt_timeout_seconds, positive_remaining)

        if self.on_attempt_start is not None:
            self.on_attempt_start()

        process, connection = self.launcher.launch(
            _generation_child_entry,
            (
                profile,
                runtime_config,
                str(image_path),
                prompt,
                self.config.raw_output_max_bytes,
                self.config.ipc_envelope_max_bytes,
            ),
        )
        frame: dict[str, object] | None = None
        cleanup_succeeded = True
        try:
            try:
                frame = connection.recv_frame(attempt_deadline_seconds)
                remaining_after_wait = self.worker_cap_deadline_monotonic - self.clock()
                if frame is not None and _positive_finite_float(remaining_after_wait) is None:
                    frame = None
            except (Feat018ProtocolViolationError, EOFError, OSError):
                raise QwenPermanentRuntimeError from None
        finally:
            try:
                connection.close()
            except Exception:  # noqa: BLE001 - cleanup must not hide the bounded result
                cleanup_succeeded = False
            if not _bounded_terminate_kill_join(
                process, grace_seconds=1.0, kill_join_seconds=1.0
            ):
                cleanup_succeeded = False

        if not cleanup_succeeded:
            raise QwenPermanentRuntimeError("generation cleanup failed")
        if frame is None:
            raise QwenTimeoutError

        return _interpret_generation_child_frame(frame)


def _interpret_generation_child_frame(frame: Mapping[str, object]) -> str:
    kind = frame.get("kind")
    if kind == "success":
        raw_output = frame.get("raw_output")
        if not isinstance(raw_output, str):
            raise QwenPermanentRuntimeError("malformed success frame")
        return raw_output
    if kind == "model_load_failed":
        raise QwenModelLoadError
    if kind == "device_unavailable":
        raise QwenDeviceUnavailableError
    if kind == "timeout":
        raise QwenTimeoutError
    if kind in ("raw_output_overflow", "ipc_envelope_overflow"):
        raise QwenPermanentRuntimeError("bounded-output violation")
    raise QwenPermanentRuntimeError("malformed generation-child frame")


# --------------------------------------------------------------------------------------
# Outer adapter-call supervisor
# --------------------------------------------------------------------------------------


class CleanupStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    CLEANUP_FAILED = "CLEANUP_FAILED"


class EffectiveOutcome(StrEnum):
    """The only outcome a downstream caller may use as the run's verdict."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CLEANUP_FAILED = "CLEANUP_FAILED"


@dataclass(frozen=True, slots=True)
class SupervisorRunResult:
    """A run result with an authoritative outcome and optional worker diagnostics.

    ``terminal_outcome`` is retained only as the worker's last accepted diagnostic event. It is
    never the run verdict; callers must use ``effective_outcome``.
    """

    final_state: ProgressState
    attempt_count: int | None
    terminal_outcome: str | None
    cleanup_status: CleanupStatus
    effective_outcome: EffectiveOutcome = EffectiveOutcome.FAILED
    stopped_before_containment: bool = False
    primary_failure_reason: str | None = None
    raw_status: str | None = None

    @property
    def worker_terminal_outcome(self) -> str | None:
        """Explicit name for the non-authoritative worker event history."""

        return self.terminal_outcome

    @property
    def verdict(self) -> EffectiveOutcome:
        """Alias for callers that use verdict terminology."""

        return self.effective_outcome

    @property
    def is_success(self) -> bool:
        return self.effective_outcome is EffectiveOutcome.SUCCEEDED


@dataclass(slots=True)
class Feat018AdapterCallSupervisor:
    """Independently supervises the complete adapter-worker invocation.

    Its own ``cap_deadline_monotonic`` is the sole hard authority (see the approval package's
    "One absolute deadline, and it is the sole hard authority"): this class never trusts a
    worker-reported clock or a worker's cooperation for correctness, only for an early-exit
    optimization the worker may or may not perform.

    F2 (independent-review correction): every exit path -- normal completion, a gate failure,
    or an unexpected exception raised anywhere from launch through the progress loop -- runs
    through exactly one cleanup coordinator in a ``finally`` block, so descendant termination
    and bounded cleanup verification are never bypassed. ``CLEANUP_FAILED`` always overrides a
    prior success; a primary lifecycle failure is preserved in ``primary_failure_reason`` rather
    than silently discarded.
    """

    config: Feat018BoundedRunnerConfig
    launcher: ProcessLauncher
    containment_factory: Callable[[], ContainmentBackend]
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep

    def run(
        self, entry: Callable[..., None], worker_args: tuple[object, ...]
    ) -> SupervisorRunResult:
        cap_deadline_monotonic = self.clock() + self.config.total_adapter_cap_seconds

        containment: ContainmentBackend | None = None
        try:
            containment = self.containment_factory()
            containment.create()
        except Exception:  # noqa: BLE001 - containment creation is fail-closed, never raised
            cleanup_status = self._cleanup_partial_containment(containment)
            return SupervisorRunResult(
                final_state=ProgressState.NOT_STARTED,
                attempt_count=None,
                terminal_outcome=None,
                cleanup_status=cleanup_status,
                effective_outcome=(
                    EffectiveOutcome.CLEANUP_FAILED
                    if cleanup_status is CleanupStatus.CLEANUP_FAILED
                    else EffectiveOutcome.FAILED
                ),
                stopped_before_containment=True,
                primary_failure_reason="containment creation failed",
            )
        assert containment is not None

        process: ProcessHandle | None = None
        connection: BoundedConnection | None = None
        stopped_before_containment = False
        primary_failure_reason: str | None = None
        state_machine = Feat018ProgressStateMachine(cap_deadline_monotonic=cap_deadline_monotonic)

        try:
            try:
                process, connection = self.launcher.launch(entry, worker_args)
            except Exception:  # noqa: BLE001 - preserved below, cleanup still runs
                stopped_before_containment = True
                primary_failure_reason = "adapter worker launch failed"
            else:
                gated = self._establish_containment_gate(
                    process, connection, containment, cap_deadline_monotonic
                )
                if not gated.contained:
                    stopped_before_containment = True
                    primary_failure_reason = gated.failure_reason
                else:
                    progress_failure_reason = self._run_progress_loop(
                        process, connection, state_machine, cap_deadline_monotonic
                    )
                    primary_failure_reason = primary_failure_reason or progress_failure_reason
        except Exception:  # noqa: BLE001 - any unforeseen lifecycle failure still cleans up
            primary_failure_reason = primary_failure_reason or "adapter worker lifecycle failure"
            state_machine.force_freeze()
        finally:
            cleanup_failed = False
            if process is not None and not _bounded_terminate_kill_join(
                process, grace_seconds=1.0, kill_join_seconds=1.0
            ):
                cleanup_failed = True
            try:
                containment.terminate_all()
            except Exception:  # noqa: BLE001 - cleanup must continue and report failure
                cleanup_failed = True
            cleanup_status = self._verify_cleanup(containment)
            if cleanup_status is CleanupStatus.CLEANUP_FAILED:
                cleanup_failed = True
            if connection is not None:
                try:
                    connection.close()
                except Exception:  # noqa: BLE001 - containment close must still run
                    cleanup_failed = True
            try:
                containment.close()
            except Exception:  # noqa: BLE001 - cleanup failure is a result, not an escape
                cleanup_failed = True
            if bool(getattr(containment, "_cleanup_failed", False)):
                cleanup_failed = True
            if cleanup_failed:
                cleanup_status = CleanupStatus.CLEANUP_FAILED

        if cleanup_status is CleanupStatus.CLEANUP_FAILED and primary_failure_reason is None:
            primary_failure_reason = "cleanup verification failed"
        effective_outcome = EffectiveOutcome.FAILED
        if cleanup_status is CleanupStatus.CLEANUP_FAILED:
            effective_outcome = EffectiveOutcome.CLEANUP_FAILED
        elif (
            state_machine.state is ProgressState.TERMINAL
            and state_machine.terminal_outcome == "SUCCEEDED"
            and primary_failure_reason is None
        ):
            effective_outcome = EffectiveOutcome.SUCCEEDED

        return SupervisorRunResult(
            final_state=state_machine.state,
            attempt_count=state_machine.attempt_count,
            terminal_outcome=state_machine.terminal_outcome,
            cleanup_status=cleanup_status,
            effective_outcome=effective_outcome,
            stopped_before_containment=stopped_before_containment,
            primary_failure_reason=primary_failure_reason,
            raw_status=state_machine.raw_status,
        )

    def _establish_containment_gate(
        self,
        process: ProcessHandle,
        connection: BoundedConnection,
        containment: ContainmentBackend,
        cap_deadline_monotonic: float,
    ) -> _ContainmentGateResult:
        remaining_for_gate = cap_deadline_monotonic - self.clock()
        if _positive_finite_float(remaining_for_gate) is None:
            return _ContainmentGateResult(
                contained=False, failure_reason="containment gate deadline expired"
            )
        gate_timeout = max(
            0.0, min(self.config.containment_setup_timeout_seconds, remaining_for_gate)
        )
        try:
            contained = containment.confirm_worker_contained(
                process,
                timeout=gate_timeout,
                retry_interval=self.config.posix_confirmation_retry_interval_seconds,
            )
        except Exception:  # noqa: BLE001 - confirmation failure fails closed
            return _ContainmentGateResult(
                contained=False, failure_reason="containment confirmation failed"
            )
        if not contained:
            return _ContainmentGateResult(
                contained=False, failure_reason="containment not confirmed"
            )

        remaining_for_duration = cap_deadline_monotonic - self.clock()
        if _positive_finite_float(remaining_for_duration) is None:
            return _ContainmentGateResult(
                contained=False, failure_reason="containment gate deadline expired"
            )
        try:
            connection.send_frame(
                {
                    "kind": "CONTAINMENT_READY",
                    "remaining_seconds_at_spawn": remaining_for_duration,
                }
            )
        except Exception:  # noqa: BLE001 - failing to release the worker is a gate failure
            return _ContainmentGateResult(
                contained=False, failure_reason="CONTAINMENT_READY send failed"
            )
        return _ContainmentGateResult(contained=True, failure_reason=None)

    def _run_progress_loop(
        self,
        process: ProcessHandle,
        connection: BoundedConnection,
        state_machine: Feat018ProgressStateMachine,
        cap_deadline_monotonic: float,
    ) -> str | None:
        while state_machine.state not in (ProgressState.TERMINAL, ProgressState.FROZEN):
            remaining = cap_deadline_monotonic - self.clock()
            if _positive_finite_float(remaining) is None:
                state_machine.force_freeze()
                return "adapter supervisor deadline exceeded"
            wait = min(remaining, self.config.poll_interval_seconds)
            try:
                raw_frame = connection.recv_frame(wait)
            except Feat018FrameTooLargeError:
                state_machine.force_freeze()
                return "progress frame exceeded the IPC envelope limit"
            except Feat018ProtocolViolationError:
                state_machine.force_freeze()
                return "progress frame failed bounded protocol validation"
            except (EOFError, OSError):
                state_machine.force_freeze()
                return "progress channel closed before terminal event"
            except Exception:  # noqa: BLE001 - never expose transport details
                state_machine.force_freeze()
                return "progress frame receive failed"
            acceptance_time = self.clock()
            if raw_frame is None:
                try:
                    worker_alive = process.is_alive()
                except Exception:  # noqa: BLE001 - liveness failure is fail-closed
                    state_machine.force_freeze()
                    return "adapter worker liveness check failed"
                if not worker_alive:
                    state_machine.force_freeze()
                    return "adapter worker exited before terminal event"
                continue
            if _positive_finite_float(cap_deadline_monotonic - acceptance_time) is None:
                state_machine.force_freeze()
                return "progress event arrived at or after the supervisor deadline"
            event = _progress_event_from_frame(raw_frame)
            if event is None:
                state_machine.force_freeze()
                return "malformed progress frame"
            result = state_machine.accept(event, acceptance_time=acceptance_time)
            if result in (
                AcceptanceResult.REJECTED_DUPLICATE,
                AcceptanceResult.REJECTED_GAP,
                AcceptanceResult.REJECTED_INVALID_TRANSITION,
                AcceptanceResult.REJECTED_DEADLINE,
                AcceptanceResult.REJECTED_CLOSED,
            ):
                state_machine.force_freeze()
                return {
                    AcceptanceResult.REJECTED_DUPLICATE: "duplicate progress sequence",
                    AcceptanceResult.REJECTED_GAP: "gapped progress sequence",
                    AcceptanceResult.REJECTED_INVALID_TRANSITION: "invalid progress transition",
                    AcceptanceResult.REJECTED_DEADLINE: (
                        "progress event missed the supervisor deadline"
                    ),
                    AcceptanceResult.REJECTED_CLOSED: "progress stream was already closed",
                }[result]
        return None

    def _cleanup_partial_containment(
        self, containment: ContainmentBackend | None
    ) -> CleanupStatus:
        """Release a containment object even when its own creation did not finish."""

        if containment is None:
            return CleanupStatus.SUCCEEDED
        cleanup_failed = bool(getattr(containment, "_cleanup_failed", False))
        try:
            containment.terminate_all()
        except Exception:  # noqa: BLE001 - close is still mandatory
            cleanup_failed = True
        if not cleanup_failed and self._verify_cleanup(containment) is CleanupStatus.CLEANUP_FAILED:
            cleanup_failed = True
        try:
            containment.close()
        except Exception:  # noqa: BLE001 - report the cleanup failure
            cleanup_failed = True
        if bool(getattr(containment, "_cleanup_failed", False)):
            cleanup_failed = True
        return (
            CleanupStatus.CLEANUP_FAILED if cleanup_failed else CleanupStatus.SUCCEEDED
        )

    def _verify_cleanup(self, containment: ContainmentBackend) -> CleanupStatus:
        deadline = self.clock() + self.config.cleanup_deadline_seconds
        interval = min(self.config.poll_interval_seconds, 0.01)
        while True:
            try:
                empty = containment.is_empty()
            except Exception:  # noqa: BLE001 - a failing query never reports empty
                return CleanupStatus.CLEANUP_FAILED
            if bool(getattr(containment, "_cleanup_failed", False)):
                return CleanupStatus.CLEANUP_FAILED
            if empty:
                return CleanupStatus.SUCCEEDED
            remaining = deadline - self.clock()
            if _positive_finite_float(remaining) is None:
                return CleanupStatus.CLEANUP_FAILED
            try:
                self.sleep(min(interval, remaining))
            except Exception:  # noqa: BLE001 - a broken wait cannot be considered cleanup
                return CleanupStatus.CLEANUP_FAILED


@dataclass(frozen=True, slots=True)
class _ContainmentGateResult:
    contained: bool
    failure_reason: str | None


# --------------------------------------------------------------------------------------
# Concrete gated adapter-worker entry (F3)
# --------------------------------------------------------------------------------------


def adapter_worker_entry(
    connection: BoundedConnection,
    request: VisionUnderstandingRequestV2,
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    config: Feat018BoundedRunnerConfig,
    session_id: str | None = None,
    *,
    generation_launcher: ProcessLauncher | None = None,
    self_contain: Callable[[], None] = posix_worker_self_contain,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    """The real, gated adapter-worker process entry point (F3).

    ``self_contain`` (real: :func:`posix_worker_self_contain`; on Windows containment is
    external, so the real function is a no-op there) is the very first action, before anything
    else -- including before waiting for release. Nothing that could construct the adapter, the
    generation runner, or a generation child happens before a valid ``CONTAINMENT_READY`` frame
    is accepted: a missing, late, malformed, or oversized release frame leaves this function
    returning before that point, every time.
    """

    self_contain()
    gate_deadline = clock() + config.containment_setup_timeout_seconds

    try:
        release = connection.recv_frame(config.containment_setup_timeout_seconds)
    except Feat018ProtocolViolationError:
        return  # an oversized/malformed frame is rejected before it is ever accepted
    except Exception:  # noqa: BLE001 - a broken gate never reaches adapter construction
        return
    if not isinstance(release, Mapping):
        return
    if (
        set(release) != {"kind", "remaining_seconds_at_spawn"}
        or release.get("kind") != "CONTAINMENT_READY"
    ):
        return  # missing or late: the bounded wait above already enforces the timeout
    if _positive_finite_float(gate_deadline - clock()) is None:
        return  # the release completed at or after the worker's bounded gate deadline
    remaining_raw = release.get("remaining_seconds_at_spawn")
    remaining_seconds = _positive_finite_float(remaining_raw)
    if remaining_seconds is None:
        return

    # Advisory only (see "Cross-process deadline propagation is advisory only" in the approval
    # package): the supervisor's own deadline is the sole hard authority regardless of this
    # value's accuracy or whether this worker uses it at all.
    worker_local_monotonic_origin = clock()
    worker_cap_deadline_monotonic = worker_local_monotonic_origin + remaining_seconds
    if not math.isfinite(worker_cap_deadline_monotonic):
        return

    seq_state = {"value": 0}

    def _next_seq() -> int:
        seq_state["value"] += 1
        return seq_state["value"]

    def _send(kind: str, **extra: object) -> None:
        try:
            connection.send_frame({"seq": _next_seq(), "kind": kind, **extra})
        except Exception:  # noqa: BLE001 - event delivery is a required protocol step
            raise Feat018ProtocolViolationError("worker progress event send failed") from None

    _send("ADAPTER_STARTED")

    attempt_state = {"count": 0}
    attempt_event_send_failed = {"value": False}

    def _on_attempt_start() -> None:
        attempt_state["count"] += 1
        try:
            _send("GENERATION_ATTEMPT_STARTED", attempt_number=attempt_state["count"])
        except Feat018ProtocolViolationError:
            attempt_event_send_failed["value"] = True
            raise

    runner = Feat018BoundedKillableQwenGenerationRunner(
        config=config,
        worker_cap_deadline_monotonic=worker_cap_deadline_monotonic,
        launcher=generation_launcher
        or MultiprocessingProcessLauncher(max_envelope_bytes=config.ipc_envelope_max_bytes),
        clock=clock,
        on_attempt_start=_on_attempt_start,
    )
    adapter = QwenVisionAdapter(
        runtime_config,
        content_policy=content_policy,
        prompt=prompt,
        generation_runner=runner,
    )

    raw_status: str | None = None
    try:
        result = adapter.understand(request)
        if attempt_event_send_failed["value"]:
            raise Feat018ProtocolViolationError("worker attempt event send failed")
        outcome = "SUCCEEDED" if isinstance(result, VisionUnderstandingSuccessV2) else "FAILED"
        if session_id is not None:
            if not _is_bounded_opaque_identifier(session_id):
                raise ValueError("session_id must be a bounded opaque identifier")
            mapped = map_vision_result_to_raw(
                result,
                session_id=session_id,
                expected_source_sha256=request.source_image_ref.sha256,
                expected_correlation_id=request.correlation_id,
            )
            raw_status = mapped.status
    except Exception:  # noqa: BLE001 - never let an adapter-side exception cross the boundary
        if attempt_event_send_failed["value"]:
            raise Feat018ProtocolViolationError("worker attempt event send failed") from None
        outcome = "FAILED"

    if raw_status is None:
        _send("TERMINAL", outcome=outcome)
    else:
        _send("TERMINAL", outcome=outcome, raw_status=raw_status)


def run_bounded_adapter_call(
    request: VisionUnderstandingRequestV2,
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    config: Feat018BoundedRunnerConfig,
    *,
    session_id: str | None = None,
) -> SupervisorRunResult:
    """The one real, production entry point for a live bounded adapter call (F3).

    Always uses :func:`adapter_worker_entry` through :class:`Feat018AdapterCallSupervisor`, so
    a caller cannot bypass the containment gate by substituting an ungated entry through this
    function. This function itself is never invoked by the offline test suite (doing so would
    require a real subprocess); its constituent pieces -- the supervisor, the entry's gate logic,
    and the generation runner -- are each independently tested through injected fakes.
    ``session_id`` is a bounded opaque bootstrap argument. Spawn multiprocessing may serialize
    it across the worker boundary, but it is never placed in progress/event frames or evidence
    payload bodies.
    """

    if session_id is not None and not _is_bounded_opaque_identifier(session_id):
        raise ValueError("session_id must be a bounded opaque identifier")
    launcher = MultiprocessingProcessLauncher(max_envelope_bytes=config.ipc_envelope_max_bytes)
    supervisor = Feat018AdapterCallSupervisor(
        config=config,
        launcher=launcher,
        containment_factory=create_platform_containment,
    )
    return supervisor.run(
        adapter_worker_entry,
        (request, runtime_config, content_policy, prompt, config, session_id),
    )


def _progress_event_from_frame(frame: Mapping[str, object]) -> ProgressEvent | None:
    if not isinstance(frame, Mapping):
        return None
    allowed_keys = {"seq", "kind", "attempt_number", "outcome", "raw_status"}
    if any(not isinstance(key, str) for key in frame) or set(frame) - allowed_keys:
        return None
    seq = frame.get("seq")
    kind_raw = frame.get("kind")
    attempt_number = frame.get("attempt_number")
    outcome = frame.get("outcome")
    raw_status = frame.get("raw_status")
    if (
        not isinstance(seq, int)
        or isinstance(seq, bool)
        or not isinstance(kind_raw, str)
        or isinstance(attempt_number, bool)
    ):
        return None
    if attempt_number is not None and not isinstance(attempt_number, int):
        return None
    if outcome is not None and not isinstance(outcome, str):
        return None
    if raw_status is not None and not isinstance(raw_status, str):
        return None
    try:
        kind = ProgressEventKind(kind_raw)
        return ProgressEvent(
            seq=seq, kind=kind, attempt_number=attempt_number,
            outcome=outcome, raw_status=raw_status,
        )
    except ValueError:
        return None


# --------------------------------------------------------------------------------------
# Evidence commit protocol
# --------------------------------------------------------------------------------------


class FilesystemOps(Protocol):
    """Injectable filesystem seam so crash-injection tests never touch the real disk."""

    def write_new(self, path: Path, content: bytes) -> None: ...

    def rename(self, source: Path, destination: Path) -> None: ...

    def read_bytes(self, path: Path) -> bytes: ...

    def exists(self, path: Path) -> bool: ...

    def remove(self, path: Path) -> None: ...


@dataclass(slots=True)
class RealFilesystemOps:
    def write_new(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(content)

    def rename(self, source: Path, destination: Path) -> None:
        source.rename(destination)

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def exists(self, path: Path) -> bool:
        return path.exists()

    def remove(self, path: Path) -> None:
        path.unlink(missing_ok=True)


@dataclass(frozen=True, slots=True)
class EvidenceCommitResult:
    committed: bool
    run_id: str
    evidence_id: str
    residual_paths: tuple[Path, ...] = ()
    failure_reason: str | None = None


def new_run_id() -> str:
    return uuid.uuid4().hex


def new_evidence_id() -> str:
    return uuid.uuid4().hex


@dataclass(slots=True)
class Feat018EvidenceCommitWriter:
    """The three-state commit protocol: provisional result -> provisional artifacts ->
    authoritative committed pair. The JSON file is the sole designated commit record; its
    rename is the sole commit point. When supplied, ``precommit`` runs for the provisional pair
    and again for the Markdown-final/JSON-temporary pair immediately before that commit point.
    The Markdown never carries a hash of the JSON.
    """

    json_path: Path
    markdown_path: Path
    fs: FilesystemOps = field(default_factory=RealFilesystemOps)

    def commit(
        self,
        *,
        run_id: str,
        evidence_id: str,
        json_fields: Mapping[str, object],
        markdown_body: str,
        precommit: Callable[[Path, Path], bool] | None = None,
    ) -> EvidenceCommitResult:
        markdown_content = _render_markdown(run_id, evidence_id, markdown_body).encode("utf-8")
        markdown_sha256 = sha256(markdown_content).hexdigest()

        json_payload: dict[str, object] = {
            **json_fields,
            "run_id": run_id,
            "evidence_id": evidence_id,
            "companion_markdown_sha256": markdown_sha256,
            "commit_state": "FINAL",
        }
        json_content = json.dumps(json_payload, sort_keys=True, indent=2).encode("utf-8") + b"\n"

        markdown_temp = self.markdown_path.with_name(self.markdown_path.name + f".tmp-{run_id}")
        json_temp = self.json_path.with_name(self.json_path.name + f".tmp-{run_id}")

        try:
            self.fs.write_new(markdown_temp, markdown_content)
        except OSError as exc:
            return EvidenceCommitResult(
                committed=False, run_id=run_id, evidence_id=evidence_id, failure_reason=str(exc)
            )

        try:
            self.fs.write_new(json_temp, json_content)
        except OSError as exc:
            self._safe_remove(markdown_temp)
            return EvidenceCommitResult(
                committed=False, run_id=run_id, evidence_id=evidence_id, failure_reason=str(exc)
            )

        try:
            if not self._verify_precommit(
                json_candidate=json_temp,
                markdown_candidate=markdown_temp,
                json_content=json_content,
                markdown_content=markdown_content,
                precommit=precommit,
                markdown_is_final=False,
            ):
                raise Feat018EvidenceCommitError("precommit verification failed")
        except Exception:  # noqa: BLE001 - an incomplete gate never reaches the commit point
            residual = self._remove_provisional_pair(json_temp, markdown_temp)
            return EvidenceCommitResult(
                committed=False,
                run_id=run_id,
                evidence_id=evidence_id,
                residual_paths=residual,
                failure_reason="precommit verification failed",
            )

        try:
            self.fs.rename(markdown_temp, self.markdown_path)
        except OSError as exc:
            self._safe_remove(markdown_temp)
            self._safe_remove(json_temp)
            return EvidenceCommitResult(
                committed=False, run_id=run_id, evidence_id=evidence_id, failure_reason=str(exc)
            )

        # The first inventory scan is deliberately not the commit boundary. Recheck after the
        # Markdown rename, immediately before the authoritative JSON rename. This closes the
        # ordinary mutation window under the approved quiescent single-writer invariant: the
        # completed cleanup has removed every supervised process/descendant and no runtime writer
        # remains; this finalizer is then the sole authorized writer. It is not filesystem-wide
        # atomicity and does not defend against an unrelated hostile external writer.
        try:
            if not self._verify_precommit(
                json_candidate=json_temp,
                markdown_candidate=self.markdown_path,
                json_content=json_content,
                markdown_content=markdown_content,
                precommit=precommit,
                markdown_is_final=True,
            ):
                raise Feat018EvidenceCommitError("commit-adjacent verification failed")
        except Exception:  # noqa: BLE001 - an incomplete gate never reaches the commit point
            residual = self._remove_provisional_pair(
                json_temp, markdown_temp, self.markdown_path
            )
            return EvidenceCommitResult(
                committed=False,
                run_id=run_id,
                evidence_id=evidence_id,
                residual_paths=residual,
                failure_reason="commit-adjacent verification failed",
            )

        try:
            self.fs.rename(json_temp, self.json_path)
        except OSError as exc:
            residual = self._rollback_after_json_rename_failure(json_temp)
            return EvidenceCommitResult(
                committed=False,
                run_id=run_id,
                evidence_id=evidence_id,
                residual_paths=residual,
                failure_reason=str(exc),
            )

        return EvidenceCommitResult(committed=True, run_id=run_id, evidence_id=evidence_id)

    def _verify_precommit(
        self,
        *,
        json_candidate: Path,
        markdown_candidate: Path,
        json_content: bytes,
        markdown_content: bytes,
        precommit: Callable[[Path, Path], bool] | None,
        markdown_is_final: bool,
    ) -> bool:
        """Run one bounded audit and exact-byte check for a commit transition."""

        if self.fs.exists(self.json_path):
            return False
        if markdown_is_final:
            if not self.fs.exists(self.markdown_path):
                return False
        elif self.fs.exists(self.markdown_path):
            return False

        # Read before and after the callback: a callback may be an injected audit fake, and a
        # changed provisional pair must never be renamed even if that callback returns true.
        if self.fs.read_bytes(json_candidate) != json_content:
            return False
        if self.fs.read_bytes(markdown_candidate) != markdown_content:
            return False
        if precommit is not None and precommit(json_candidate, markdown_candidate) is not True:
            return False
        return (
            self.fs.read_bytes(json_candidate) == json_content
            and self.fs.read_bytes(markdown_candidate) == markdown_content
        )

    def _remove_provisional_pair(self, *paths: Path) -> tuple[Path, ...]:
        residual: list[Path] = []
        for path in paths:
            try:
                self.fs.remove(path)
            except Exception:  # noqa: BLE001 - retain every unverified residual
                residual.append(path)
        return tuple(residual)

    def _rollback_after_json_rename_failure(self, json_temp: Path) -> tuple[Path, ...]:
        residual: list[Path] = []
        try:
            self.fs.remove(self.markdown_path)
        except OSError:
            residual.append(self.markdown_path)
        try:
            self.fs.remove(json_temp)
        except OSError:
            residual.append(json_temp)
        return tuple(residual)

    def _safe_remove(self, path: Path) -> None:
        with contextlib.suppress(OSError):
            self.fs.remove(path)


@dataclass(slots=True)
class Feat018EvidenceFinalizer:
    """Finalize an outcome after cleanup and an explicit provisional-artifact audit.

    The caller supplies the complete session/artifact audit; this class enforces ordering
    and publication failure semantics, not the inventory's completeness. It does not run
    a model or constitute the still-pending complete live smoke coordinator.
    """

    writer: Feat018EvidenceCommitWriter

    def finalize(
        self,
        *,
        run_id: str,
        evidence_id: str,
        runtime_outcome: EffectiveOutcome,
        cleanup: Callable[[], CleanupStatus],
        postflight: Callable[[Path, Path], bool],
    ) -> EvidenceCommitResult:
        try:
            cleanup_status = cleanup()
        except Exception:  # noqa: BLE001 - no exception payload is publishable
            cleanup_status = CleanupStatus.CLEANUP_FAILED

        if not all(_is_bounded_opaque_identifier(value) for value in (run_id, evidence_id)):
            raise ValueError("evidence identities must be bounded opaque lowercase identifiers")
        if not isinstance(runtime_outcome, EffectiveOutcome):
            raise ValueError("runtime_outcome must be an EffectiveOutcome")
        if not callable(postflight):
            raise ValueError("postflight is mandatory")

        # A successful cleanup is the owner-approved quiescent-session invariant: every
        # supervised process and descendant is absent, no runtime writer remains, and this
        # finalizer is the sole authorized evidence writer. Any failed or unverifiable cleanup
        # prevents publication, including FAILED evidence. The future coordinator handles this
        # safe failure through its incident path.
        if cleanup_status is not CleanupStatus.SUCCEEDED:
            return EvidenceCommitResult(
                committed=False,
                run_id=run_id,
                evidence_id=evidence_id,
                failure_reason="cleanup verification failed",
            )

        candidates = (
            self.writer.json_path,
            self.writer.markdown_path,
            self.writer.json_path.with_name(self.writer.json_path.name + f".tmp-{run_id}"),
            self.writer.markdown_path.with_name(self.writer.markdown_path.name + f".tmp-{run_id}"),
        )
        try:
            if any(self.writer.fs.exists(path) for path in candidates):
                raise Feat018EvidenceCommitError("evidence destination already exists")
            result = self.writer.commit(
                run_id=run_id,
                evidence_id=evidence_id,
                json_fields={
                    "status": runtime_outcome.value,
                    "cleanup_status": cleanup_status.value,
                    "postflight_status": "SUCCEEDED",
                },
                markdown_body=(
                    f"status: {runtime_outcome.value}\n"
                    f"cleanup_status: {cleanup_status.value}\npostflight_status: SUCCEEDED"
                ),
                precommit=postflight,
            )
        except Exception:  # noqa: BLE001 - fail closed and expose no filesystem/exception text
            return EvidenceCommitResult(
                committed=False,
                run_id=run_id,
                evidence_id=evidence_id,
                residual_paths=candidates,
                failure_reason="evidence publication failed; residual inventory requires review",
            )
        if result.committed:
            return result
        residual = list(result.residual_paths)
        for path in candidates:
            try:
                remains = self.writer.fs.exists(path)
            except Exception:  # noqa: BLE001 - unverified paths require incident review
                remains = True
            if remains and path not in residual:
                residual.append(path)
        return EvidenceCommitResult(
            committed=False,
            run_id=run_id,
            evidence_id=evidence_id,
            residual_paths=tuple(residual),
            failure_reason="evidence publication failed",
        )


@dataclass(slots=True)
class Feat018ArtifactInventory:
    """Bounded metadata inventory of explicit roots, including ignored files.

    Root selection is approval input. Metadata equality is not a substitute for
    separately verified source/fixture content hashes or session/process teardown. The evidence
    writer invokes :meth:`verify_provisional` once before the Markdown rename and again after
    that rename, immediately before the JSON commit point. This is sufficient only under the
    approved quiescent single-writer invariant; it is not filesystem-wide atomicity or
    protection from an unrelated hostile writer, and it does not defeat timestamp restoration.
    """

    roots: tuple[Path, ...]
    max_entries: int
    _baseline: dict[Path, tuple[int, ...]] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.roots or type(self.max_entries) is not int or self.max_entries < 1:
            raise ValueError("explicit roots and a positive entry budget are required")
        self.roots = tuple(path.absolute() for path in self.roots)
        for index, root in enumerate(self.roots):
            if ".worktrees" in {part.casefold() for part in root.parts}:
                raise ValueError("other worktree inventory is forbidden")
            for other in self.roots[:index]:
                if root.is_relative_to(other) or other.is_relative_to(root):
                    raise ValueError("inventory roots must not overlap")

    @staticmethod
    def _fingerprint(path: Path) -> tuple[int, ...]:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & 0x400:
            raise Feat018EvidenceCommitError("inventory link/reparse point is forbidden")
        identity = (metadata.st_mode, metadata.st_dev, metadata.st_ino)
        if stat.S_ISDIR(metadata.st_mode):
            return identity
        if not stat.S_ISREG(metadata.st_mode):
            raise Feat018EvidenceCommitError("inventory special file is forbidden")
        return (*identity, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns)

    def _scan(self) -> dict[Path, tuple[int, ...]]:
        observed: dict[Path, tuple[int, ...]] = {}
        pending = list(self.roots)
        for root in self.roots:
            for parent in root.parents:
                self._fingerprint(parent)
            if not stat.S_ISDIR(self._fingerprint(root)[0]):
                raise Feat018EvidenceCommitError("inventory root must be a directory")
        while pending:
            path = pending.pop()
            if ".worktrees" in {part.casefold() for part in path.parts}:
                raise Feat018EvidenceCommitError("other worktree inventory is forbidden")
            fingerprint = self._fingerprint(path)
            observed[path] = fingerprint
            if len(observed) > self.max_entries:
                raise Feat018EvidenceCommitError("inventory entry budget exceeded")
            if stat.S_ISDIR(fingerprint[0]):
                with os.scandir(path) as entries:
                    for entry in entries:
                        if len(observed) + len(pending) >= self.max_entries:
                            raise Feat018EvidenceCommitError("inventory entry budget exceeded")
                        pending.append(path / entry.name)
        return observed

    def capture(self) -> None:
        self._baseline = None
        self._baseline = self._scan()

    def verify_provisional(self, json_temp: Path, markdown_temp: Path) -> bool:
        if self._baseline is None:
            return False
        allowed = (json_temp.absolute(), markdown_temp.absolute())
        if allowed[0] == allowed[1] or any(path in self._baseline for path in allowed):
            return False
        try:
            current = self._scan()
            for path in allowed:
                fingerprint = current.pop(path, None)
                if fingerprint is None or not stat.S_ISREG(fingerprint[0]):
                    return False
            return current == self._baseline
        except Exception:  # noqa: BLE001 - no traversal error is a passing audit
            return False


@dataclass(slots=True)
class Feat018IncidentWriter:
    """Write only the approved ignored incident path with no exception/path interpolation.

    The future coordinator must pass a path relative to the repository root and an explicit
    ``git_ignored=True`` result from its preflight. The writer does not infer Git state.
    """

    path: Path
    repository_root: Path | None = None
    git_ignored: bool = False
    fs: FilesystemOps = field(default_factory=RealFilesystemOps)
    _path_was_absolute: bool = field(default=False, init=False, repr=False)
    _path_has_dot_component: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self._path_was_absolute = self.path.is_absolute()
        self._path_has_dot_component = any(part in {".", ".."} for part in self.path.parts)
        root = (self.repository_root or Path.cwd()).absolute()
        self.repository_root = root
        if not self._path_was_absolute:
            self.path = (root / self.path).absolute()

    def _destination_is_approved(self, run_id: str) -> bool:
        if not _is_bounded_opaque_identifier(run_id) or self.git_ignored is not True:
            return False
        if self._path_was_absolute or self.repository_root is None:
            return False
        if self._path_has_dot_component:
            return False
        expected_relative = (
            Path("tmp") / f"feat018-live-lightning-incident-{run_id}" / "INCIDENT.md"
        )
        expected = (self.repository_root / expected_relative).absolute()
        if os.path.normcase(str(self.path)) != os.path.normcase(str(expected)):
            return False
        try:
            if not self.path.is_relative_to(self.repository_root / "tmp"):
                return False
        except ValueError:
            return False
        return self._path_components_are_safe(self.path, self.repository_root)

    @staticmethod
    def _path_components_are_safe(path: Path, root: Path) -> bool:
        current = path
        root_key = os.path.normcase(str(root))
        while True:
            try:
                metadata = current.lstat()
            except FileNotFoundError:
                metadata = None
            except OSError:
                return False
            if metadata is not None and (
                stat.S_ISLNK(metadata.st_mode)
                or bool(getattr(metadata, "st_file_attributes", 0) & 0x400)
            ):
                return False
            if os.path.normcase(str(current)) == root_key:
                return metadata is not None and stat.S_ISDIR(metadata.st_mode)
            parent = current.parent
            if parent == current:
                return False
            current = parent

    def write(self, result: EvidenceCommitResult) -> bool:
        if result.committed:
            return False
        if not self._destination_is_approved(result.run_id):
            return False
        if not _is_bounded_opaque_identifier(result.evidence_id):
            return False
        content = (
            "# FEAT-018 incident\nstatus: FAILED\nevidence_committed: false\n"
            f"run_id: {result.run_id}\nevidence_id: {result.evidence_id}\n"
            f"residual_count: {len(result.residual_paths)}\n"
            "residual_disposition: REQUIRES_LOCAL_REVIEW\n"
        ).encode("ascii")
        try:
            self.fs.write_new(self.path, content)
        except Exception:  # noqa: BLE001 - incident failure is observable without raw details
            return False
        return True


@dataclass(frozen=True, slots=True)
class SmokeFinalizationResult:
    evidence: EvidenceCommitResult
    incident_written: bool


def finalize_smoke_run(
    result: SupervisorRunResult,
    *,
    run_id: str,
    evidence_id: str,
    inventory: Feat018ArtifactInventory,
    cleanup: Callable[[], CleanupStatus],
    writer: Feat018EvidenceCommitWriter,
    incident: Feat018IncidentWriter,
) -> SmokeFinalizationResult:
    """Publish only a mapped, cleaned result with a passing real inventory comparison.

    The inventory baseline must be captured by preflight. The cleanup callback is the
    quiescent-session barrier: it must confirm that every supervised process/descendant is
    absent and that no runtime writer remains before evidence finalization becomes the sole
    authorized writer. This function never recaptures the baseline after runtime changes, never
    claims filesystem-wide atomicity against an unrelated external writer, and never promotes
    worker diagnostics.
    """

    outcome = EffectiveOutcome.FAILED
    if result.cleanup_status is CleanupStatus.CLEANUP_FAILED:
        outcome = EffectiveOutcome.CLEANUP_FAILED
    elif (
        result.effective_outcome is EffectiveOutcome.SUCCEEDED
        and result.raw_status == "SUCCEEDED"
        and result.final_state is ProgressState.TERMINAL
        and result.terminal_outcome == "SUCCEEDED"
        and result.primary_failure_reason is None
    ):
        outcome = EffectiveOutcome.SUCCEEDED

    def cleanup_all() -> CleanupStatus:
        session_status = cleanup()
        if (
            result.cleanup_status is not CleanupStatus.SUCCEEDED
            or session_status is not CleanupStatus.SUCCEEDED
        ):
            return CleanupStatus.CLEANUP_FAILED
        return CleanupStatus.SUCCEEDED

    evidence = Feat018EvidenceFinalizer(writer).finalize(
        run_id=run_id,
        evidence_id=evidence_id,
        runtime_outcome=outcome,
        cleanup=cleanup_all,
        postflight=inventory.verify_provisional,
    )
    return SmokeFinalizationResult(
        evidence=evidence,
        incident_written=incident.write(evidence) if not evidence.committed else False,
    )


def _render_markdown(run_id: str, evidence_id: str, body: str) -> str:
    return f"# P2 live smoke evidence\nrun_id: {run_id}\nevidence_id: {evidence_id}\n\n{body}\n"


class PairVerdict(StrEnum):
    NOT_EVIDENCE = "NOT_EVIDENCE"
    NON_AUTHORITATIVE = "NON_AUTHORITATIVE"
    AUTHORITATIVE = "AUTHORITATIVE"


@dataclass(frozen=True, slots=True)
class PairReadResult:
    verdict: PairVerdict
    reason: str | None = None


_MARKDOWN_RUN_ID_PREFIX = "run_id: "
_MARKDOWN_EVIDENCE_ID_PREFIX = "evidence_id: "


def read_committed_pair(
    json_path: Path, markdown_path: Path, *, fs: FilesystemOps | None = None
) -> PairReadResult:
    """Implements the Revision 5 crash-transition audit table's validity rule as code."""

    ops = fs or RealFilesystemOps()
    if not ops.exists(json_path) or not ops.exists(markdown_path):
        return PairReadResult(PairVerdict.NON_AUTHORITATIVE, "one or both files are absent")

    try:
        json_payload = json.loads(ops.read_bytes(json_path).decode("utf-8"))
    except (OSError, ValueError):
        return PairReadResult(PairVerdict.NON_AUTHORITATIVE, "JSON is unreadable or invalid")
    if not isinstance(json_payload, dict):
        return PairReadResult(PairVerdict.NON_AUTHORITATIVE, "JSON root is not an object")

    if json_payload.get("commit_state") != "FINAL":
        return PairReadResult(PairVerdict.NON_AUTHORITATIVE, "commit_state is not FINAL")

    try:
        markdown_bytes = ops.read_bytes(markdown_path)
    except OSError:
        return PairReadResult(PairVerdict.NON_AUTHORITATIVE, "Markdown is unreadable")

    markdown_run_id, markdown_evidence_id = _extract_markdown_identity(markdown_bytes)
    json_run_id = json_payload.get("run_id")
    json_evidence_id = json_payload.get("evidence_id")
    if markdown_run_id is None or markdown_run_id != json_run_id:
        return PairReadResult(PairVerdict.NON_AUTHORITATIVE, "run_id mismatch")
    if markdown_evidence_id is None or markdown_evidence_id != json_evidence_id:
        return PairReadResult(PairVerdict.NON_AUTHORITATIVE, "evidence_id mismatch")

    expected_hash = sha256(markdown_bytes).hexdigest()
    if json_payload.get("companion_markdown_sha256") != expected_hash:
        return PairReadResult(PairVerdict.NON_AUTHORITATIVE, "companion_markdown_sha256 mismatch")

    return PairReadResult(PairVerdict.AUTHORITATIVE)


def _extract_markdown_identity(markdown_bytes: bytes) -> tuple[str | None, str | None]:
    run_id: str | None = None
    evidence_id: str | None = None
    for line in markdown_bytes.decode("utf-8", errors="replace").splitlines():
        if line.startswith(_MARKDOWN_RUN_ID_PREFIX):
            run_id = line[len(_MARKDOWN_RUN_ID_PREFIX) :].strip()
        elif line.startswith(_MARKDOWN_EVIDENCE_ID_PREFIX):
            evidence_id = line[len(_MARKDOWN_EVIDENCE_ID_PREFIX) :].strip()
    return run_id, evidence_id


__all__ = [
    "SmokeFinalizationResult",
    "finalize_smoke_run",
    "Feat018ArtifactInventory",
    "Feat018IncidentWriter",
    "Feat018EvidenceFinalizer",
    "AcceptanceResult",
    "BoundedConnection",
    "CleanupStatus",
    "ContainmentBackend",
    "EffectiveOutcome",
    "EvidenceCommitResult",
    "Feat018AdapterCallSupervisor",
    "Feat018BoundedKillableQwenGenerationRunner",
    "Feat018BoundedRunnerConfig",
    "Feat018CleanupFailedError",
    "Feat018ContainmentError",
    "Feat018EvidenceCommitError",
    "Feat018EvidenceCommitWriter",
    "Feat018FrameTooLargeError",
    "Feat018LauncherError",
    "Feat018ProgressStateMachine",
    "Feat018ProtocolViolationError",
    "FilesystemOps",
    "MultiprocessingBoundedConnection",
    "MultiprocessingProcessLauncher",
    "PairReadResult",
    "PairVerdict",
    "PosixProcessGroupContainment",
    "ProcessHandle",
    "ProcessLauncher",
    "ProgressEvent",
    "ProgressEventKind",
    "ProgressState",
    "RealFilesystemOps",
    "SupervisorRunResult",
    "WindowsJobObjectContainment",
    "adapter_worker_entry",
    "create_platform_containment",
    "decode_envelope",
    "encode_envelope",
    "new_evidence_id",
    "new_run_id",
    "posix_worker_self_contain",
    "read_committed_pair",
    "run_bounded_adapter_call",
]
