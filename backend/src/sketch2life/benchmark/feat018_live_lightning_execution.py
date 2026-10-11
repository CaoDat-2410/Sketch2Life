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
live-run mechanism. The offline test suite drives the adapter runner through injected fakes and
uses only synthetic child processes for the lifecycle preemption proof. A live run requires a
separate, later execution approval that resolves ``P2T2-LIVE-D1`` through ``P2T2-LIVE-D12``.
"""

from __future__ import annotations

import contextlib
import ctypes
import json
import math
import multiprocessing
import os
import socket
import stat
import struct
import sys
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, Protocol, TypeVar, cast

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.application.services.raw_understanding_mapper import map_vision_result_to_raw
from sketch2life.contracts.schemas.feat018_live_binding import (
    BindingArtifactInventorySummaryV1,
    BindingTerminalMetadataV1,
    DevAttemptVerificationV1,
)
from sketch2life.contracts.schemas.raw_understanding import (
    RawUnderstandingFailureV1,
    RawUnderstandingSuccessV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai.qwen_vision import (
    QwenDeviceUnavailableError,
    QwenModelLoadError,
    QwenPermanentRuntimeError,
    QwenTimeoutError,
    QwenTransientRuntimeError,
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

    def __init__(
        self,
        message: str = "bounded cleanup failed",
        *,
        owned_process: ProcessHandle | None = None,
        owned_connections: tuple[BoundedConnection | _RawConnection, ...] = (),
        owned_containments: tuple[ContainmentBackend, ...] = (),
    ) -> None:
        super().__init__(message)
        self.owned_process = owned_process
        self.owned_connections = owned_connections
        self.owned_containments = owned_containments

    def retry_cleanup(
        self,
        *,
        grace_seconds: float,
        kill_join_seconds: float,
        cleanup_deadline_monotonic: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> bool:
        """Retain unresolved resources even when a later bounded cleanup also fails."""

        if self.owned_process is not None and _bounded_terminate_kill_join(
            self.owned_process,
            grace_seconds=grace_seconds,
            kill_join_seconds=kill_join_seconds,
            cleanup_deadline_monotonic=cleanup_deadline_monotonic,
            clock=clock,
        ):
            self.owned_process = None
        self.owned_connections = tuple(
            connection
            for connection in self.owned_connections
            if not _close_owned_ipc_endpoint(connection)
        )
        unresolved_containments: list[ContainmentBackend] = []
        for containment in self.owned_containments:
            try:
                _terminate_owned_containment(
                    containment,
                    cleanup_deadline_monotonic=cleanup_deadline_monotonic,
                    clock=clock,
                )
                if not containment.is_empty():
                    unresolved_containments.append(containment)
                    continue
                containment.close()
            except Exception:  # noqa: BLE001 - retain the handle for a later bounded retry
                unresolved_containments.append(containment)
        self.owned_containments = tuple(unresolved_containments)
        return (
            self.owned_process is None
            and not self.owned_connections
            and not self.owned_containments
        )


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
# D9 bounded stdout/stderr capture
# --------------------------------------------------------------------------------------


D9_STDOUT_MAX_BYTES = 16_384
D9_STDERR_MAX_BYTES = 32_768


class D9ProcessRole(StrEnum):
    OUTER_ADAPTER_WORKER = 'outer_adapter_worker'
    INNER_GENERATION_CHILD = 'inner_generation_child'


class D9StreamName(StrEnum):
    STDOUT = 'stdout'
    STDERR = 'stderr'


class D9StreamDisposition(StrEnum):
    ACCEPTED = 'ACCEPTED'
    FAILED = 'FAILED'


class D9StreamTerminalCategory(StrEnum):
    WITHIN_LIMIT = 'WITHIN_LIMIT'
    LIMIT_EXCEEDED = 'LIMIT_EXCEEDED'
    READ_FAILED = 'READ_FAILED'
    LATE_OUTPUT = 'LATE_OUTPUT'
    WORKER_DIED_BEFORE_STREAM_FINALIZATION = 'WORKER_DIED_BEFORE_STREAM_FINALIZATION'
    STREAM_FINALIZATION_FAILED = 'STREAM_FINALIZATION_FAILED'


class D9StreamFailureCode(StrEnum):
    STDOUT_LIMIT_EXCEEDED = 'STDOUT_LIMIT_EXCEEDED'
    STDERR_LIMIT_EXCEEDED = 'STDERR_LIMIT_EXCEEDED'
    BOTH_STREAM_LIMITS_EXCEEDED = 'BOTH_STREAM_LIMITS_EXCEEDED'
    STDOUT_CAPTURE_READ_FAILED = 'STDOUT_CAPTURE_READ_FAILED'
    STDERR_CAPTURE_READ_FAILED = 'STDERR_CAPTURE_READ_FAILED'
    STDOUT_LATE_OUTPUT = 'STDOUT_LATE_OUTPUT'
    STDERR_LATE_OUTPUT = 'STDERR_LATE_OUTPUT'
    WORKER_DIED_BEFORE_STREAM_FINALIZATION = 'WORKER_DIED_BEFORE_STREAM_FINALIZATION'
    STREAM_FINALIZATION_FAILED = 'STREAM_FINALIZATION_FAILED'


_D9_STREAM_LIMIT_CODES = {
    D9StreamName.STDOUT: D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED,
    D9StreamName.STDERR: D9StreamFailureCode.STDERR_LIMIT_EXCEEDED,
}
_D9_STREAM_READ_CODES = {
    D9StreamName.STDOUT: D9StreamFailureCode.STDOUT_CAPTURE_READ_FAILED,
    D9StreamName.STDERR: D9StreamFailureCode.STDERR_CAPTURE_READ_FAILED,
}
_D9_STREAM_LATE_CODES = {
    D9StreamName.STDOUT: D9StreamFailureCode.STDOUT_LATE_OUTPUT,
    D9StreamName.STDERR: D9StreamFailureCode.STDERR_LATE_OUTPUT,
}
_D9_STREAM_CEILINGS = {
    D9StreamName.STDOUT: D9_STDOUT_MAX_BYTES,
    D9StreamName.STDERR: D9_STDERR_MAX_BYTES,
}


def _d9_failure_category(code: D9StreamFailureCode) -> D9StreamTerminalCategory:
    if code in _D9_STREAM_LIMIT_CODES.values():
        return D9StreamTerminalCategory.LIMIT_EXCEEDED
    if code in _D9_STREAM_READ_CODES.values():
        return D9StreamTerminalCategory.READ_FAILED
    if code in _D9_STREAM_LATE_CODES.values():
        return D9StreamTerminalCategory.LATE_OUTPUT
    if code is D9StreamFailureCode.WORKER_DIED_BEFORE_STREAM_FINALIZATION:
        return D9StreamTerminalCategory.WORKER_DIED_BEFORE_STREAM_FINALIZATION
    return D9StreamTerminalCategory.STREAM_FINALIZATION_FAILED


def _d9_failure_code_for_stream(
    code: D9StreamFailureCode, stream: D9StreamName
) -> D9StreamFailureCode:
    if code is D9StreamFailureCode.BOTH_STREAM_LIMITS_EXCEEDED:
        return _D9_STREAM_LIMIT_CODES[stream]
    if code in (
        _D9_STREAM_LIMIT_CODES[stream],
        _D9_STREAM_READ_CODES[stream],
        _D9_STREAM_LATE_CODES[stream],
        D9StreamFailureCode.WORKER_DIED_BEFORE_STREAM_FINALIZATION,
        D9StreamFailureCode.STREAM_FINALIZATION_FAILED,
    ):
        return code
    return D9StreamFailureCode.STREAM_FINALIZATION_FAILED

@dataclass(frozen=True, slots=True)
class D9StreamObservation:
    """Metadata-only result for one captured process/stream observation.

    ``attempt_number`` identifies which accepted generation attempt an
    ``INNER_GENERATION_CHILD`` observation belongs to (populated only from an
    already-accepted ``GENERATION_ATTEMPT_STARTED`` count, never inferred from
    role, stream, timing, or list position). ``OUTER_ADAPTER_WORKER``
    observations span the whole worker lifetime, not one attempt, and always
    carry ``None``.
    """

    process_role: D9ProcessRole
    attempt_number: int | None
    stream: D9StreamName
    bytes_seen: int
    ceiling: int
    disposition: D9StreamDisposition
    terminal_category: D9StreamTerminalCategory
    failure_code: D9StreamFailureCode | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.process_role, D9ProcessRole):
            raise ValueError('process_role must be a D9ProcessRole')
        if self.process_role is D9ProcessRole.OUTER_ADAPTER_WORKER:
            if self.attempt_number is not None:
                raise ValueError('outer adapter worker observations carry no attempt number')
        elif type(self.attempt_number) is not int or self.attempt_number < 1:
            raise ValueError(
                'inner generation-child observations require a positive attempt number'
            )
        if not isinstance(self.stream, D9StreamName):
            raise ValueError('stream must be a D9StreamName')
        if type(self.bytes_seen) is not int or self.bytes_seen < 0:
            raise ValueError('bytes_seen must be a non-negative integer')
        expected_ceiling = _D9_STREAM_CEILINGS[self.stream]
        if self.ceiling != expected_ceiling:
            raise ValueError('D9 stream ceiling is not owner-approved')
        if self.bytes_seen > self.ceiling + 1:
            raise ValueError('bytes_seen exceeds bounded accounting')
        if not isinstance(self.disposition, D9StreamDisposition):
            raise ValueError('disposition must be a D9StreamDisposition')
        if not isinstance(self.terminal_category, D9StreamTerminalCategory):
            raise ValueError('terminal_category must be a D9StreamTerminalCategory')
        if self.terminal_category is D9StreamTerminalCategory.WITHIN_LIMIT:
            if (
                self.bytes_seen > self.ceiling
                or self.disposition is not D9StreamDisposition.ACCEPTED
                or self.failure_code is not None
            ):
                raise ValueError('WITHIN_LIMIT must be an accepted observation')
        else:
            if self.disposition is not D9StreamDisposition.FAILED or self.failure_code is None:
                raise ValueError('failed D9 observations require a typed failure')
            expected_code = {
                D9StreamTerminalCategory.LIMIT_EXCEEDED: _D9_STREAM_LIMIT_CODES[self.stream],
                D9StreamTerminalCategory.READ_FAILED: _D9_STREAM_READ_CODES[self.stream],
                D9StreamTerminalCategory.LATE_OUTPUT: _D9_STREAM_LATE_CODES[self.stream],
                D9StreamTerminalCategory.WORKER_DIED_BEFORE_STREAM_FINALIZATION: (
                    D9StreamFailureCode.WORKER_DIED_BEFORE_STREAM_FINALIZATION
                ),
                D9StreamTerminalCategory.STREAM_FINALIZATION_FAILED: (
                    D9StreamFailureCode.STREAM_FINALIZATION_FAILED
                ),
            }[self.terminal_category]
            if self.failure_code is not expected_code:
                raise ValueError('D9 stream failure code does not match the stream')
            if (
                self.terminal_category is D9StreamTerminalCategory.LIMIT_EXCEEDED
                and self.bytes_seen != self.ceiling + 1
            ):
                raise ValueError('LIMIT_EXCEEDED requires a saturated ceiling + 1 count')
            if (
                self.terminal_category is not D9StreamTerminalCategory.LIMIT_EXCEEDED
                and self.bytes_seen > self.ceiling
            ):
                raise ValueError('only LIMIT_EXCEEDED may carry an over-limit count')

    @property
    def category(self) -> D9StreamTerminalCategory:
        return self.terminal_category

    @property
    def failed(self) -> bool:
        return self.disposition is D9StreamDisposition.FAILED


@dataclass(frozen=True, slots=True)
class D9CaptureReport:
    '''Bounded, typed capture facts; raw stream payloads never enter this object.'''

    observations: tuple[D9StreamObservation, ...]
    failure_codes: tuple[D9StreamFailureCode, ...] = ()

    def __post_init__(self) -> None:
        observations = tuple(self.observations)
        if any(not isinstance(item, D9StreamObservation) for item in observations):
            raise ValueError('D9 reports may contain observations only')
        keys = [(item.attempt_number, item.process_role, item.stream) for item in observations]
        if len(keys) != len(set(keys)):
            raise ValueError('D9 reports may not duplicate an attempt/process/stream observation')
        failures: list[D9StreamFailureCode] = []
        for code in self.failure_codes:
            if not isinstance(code, D9StreamFailureCode):
                raise ValueError('D9 reports may contain typed failure codes only')
            if code not in failures:
                failures.append(code)
        for observation in observations:
            if observation.failure_code is not None and observation.failure_code not in failures:
                failures.append(observation.failure_code)
        limit_streams = {
            observation.stream
            for observation in observations
            if observation.failure_code in _D9_STREAM_LIMIT_CODES.values()
        }
        if limit_streams == set(D9StreamName) and (
            D9StreamFailureCode.BOTH_STREAM_LIMITS_EXCEEDED not in failures
        ):
            failures.append(D9StreamFailureCode.BOTH_STREAM_LIMITS_EXCEEDED)
        object.__setattr__(self, 'observations', observations)
        object.__setattr__(self, 'failure_codes', tuple(failures))

    @property
    def failed(self) -> bool:
        return bool(self.failure_codes) or any(item.failed for item in self.observations)

    @classmethod
    def failure(
        cls,
        process_role: D9ProcessRole,
        code: D9StreamFailureCode,
        *,
        attempt_number: int | None,
    ) -> D9CaptureReport:
        observations: list[D9StreamObservation] = []
        for stream in D9StreamName:
            stream_code = _d9_failure_code_for_stream(code, stream)
            ceiling = _D9_STREAM_CEILINGS[stream]
            observations.append(
                D9StreamObservation(
                    process_role=process_role,
                    attempt_number=attempt_number,
                    stream=stream,
                    bytes_seen=(
                        ceiling + 1
                        if stream_code is _D9_STREAM_LIMIT_CODES[stream]
                        else 0
                    ),
                    ceiling=ceiling,
                    disposition=D9StreamDisposition.FAILED,
                    terminal_category=_d9_failure_category(stream_code),
                    failure_code=stream_code,
                )
            )
        return cls(observations=tuple(observations), failure_codes=(code,))


_D9_CAPTURE_EVENT_CAPACITY = 8
D9TerminalFailureCallback = Callable[[D9StreamFailureCode], None]


@dataclass(slots=True)
class D9BoundedByteCapture:
    '''Thread-safe raw-byte counter that never retains the observed payload.'''

    process_role: D9ProcessRole
    attempt_number: int | None
    stream: D9StreamName
    ceiling: int
    on_terminal_failure: D9TerminalFailureCallback | None = field(default=None, repr=False)
    _bytes_seen: int = field(default=0, init=False, repr=False)
    _failure_code: D9StreamFailureCode | None = field(default=None, init=False, repr=False)
    _finalized: bool = field(default=False, init=False, repr=False)
    _terminal_failure_notified: bool = field(default=False, init=False, repr=False)
    _events: deque[str] = field(
        default_factory=lambda: deque(maxlen=_D9_CAPTURE_EVENT_CAPACITY),
        init=False,
        repr=False,
    )
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.ceiling != _D9_STREAM_CEILINGS.get(self.stream):
            raise ValueError('D9 stream ceiling is not owner-approved')
        if self.process_role is D9ProcessRole.OUTER_ADAPTER_WORKER:
            if self.attempt_number is not None:
                raise ValueError('outer adapter worker capture carries no attempt number')
        elif type(self.attempt_number) is not int or self.attempt_number < 1:
            raise ValueError(
                'inner generation-child capture requires a positive attempt number'
            )

    def observe_chunk(self, raw_bytes: bytes | bytearray | memoryview) -> None:
        '''Count raw bytes before any decoding, normalization, or logging.'''

        try:
            view = memoryview(raw_bytes)
            length = view.nbytes
            view.release()
        except (TypeError, ValueError):
            self.mark_read_failed()
            return
        notification: tuple[D9TerminalFailureCallback, D9StreamFailureCode] | None = None
        with self._lock:
            if self._finalized:
                notification = self._set_terminal_failure_locked(
                    _D9_STREAM_LATE_CODES[self.stream]
                )
                self._events.append('reject_late')
            else:
                self._events.append('capture')
                if self._failure_code is None:
                    if self._bytes_seen + length > self.ceiling:
                        self._bytes_seen = self.ceiling + 1
                        notification = self._set_terminal_failure_locked(
                            _D9_STREAM_LIMIT_CODES[self.stream]
                        )
                    else:
                        self._bytes_seen += length
        self._dispatch_terminal_failure(notification)

    def stop_and_close(self) -> None:
        with self._lock:
            self._events.append('stop_close')

    def bounded_drain(self) -> None:
        with self._lock:
            self._events.append('bounded_drain')

    def mark_read_failed(self) -> None:
        notification: tuple[D9TerminalFailureCallback, D9StreamFailureCode] | None = None
        with self._lock:
            if self._finalized:
                notification = self._set_terminal_failure_locked(
                    _D9_STREAM_LATE_CODES[self.stream]
                )
                self._events.append('reject_late')
            else:
                notification = self._set_terminal_failure_locked(
                    _D9_STREAM_READ_CODES[self.stream]
                )
                self._events.append('read_failed')
        self._dispatch_terminal_failure(notification)

    def mark_late_output(self) -> None:
        notification: tuple[D9TerminalFailureCallback, D9StreamFailureCode] | None
        with self._lock:
            notification = self._set_terminal_failure_locked(
                _D9_STREAM_LATE_CODES[self.stream]
            )
            self._events.append('reject_late')
        self._dispatch_terminal_failure(notification)

    def mark_worker_died_before_finalization(self) -> None:
        notification: tuple[D9TerminalFailureCallback, D9StreamFailureCode] | None
        with self._lock:
            notification = self._set_terminal_failure_locked(
                D9StreamFailureCode.WORKER_DIED_BEFORE_STREAM_FINALIZATION
            )
            self._events.append('worker_died')
        self._dispatch_terminal_failure(notification)

    def mark_finalization_failed(self) -> None:
        notification: tuple[D9TerminalFailureCallback, D9StreamFailureCode] | None
        with self._lock:
            notification = self._set_terminal_failure_locked(
                D9StreamFailureCode.STREAM_FINALIZATION_FAILED
            )
            self._events.append('finalization_failed')
        self._dispatch_terminal_failure(notification)

    def _set_terminal_failure_locked(
        self, code: D9StreamFailureCode
    ) -> tuple[D9TerminalFailureCallback, D9StreamFailureCode] | None:
        if self._failure_code is None:
            self._failure_code = code
        if self._terminal_failure_notified or self.on_terminal_failure is None:
            return None
        self._terminal_failure_notified = True
        return self.on_terminal_failure, self._failure_code

    @staticmethod
    def _dispatch_terminal_failure(
        notification: tuple[D9TerminalFailureCallback, D9StreamFailureCode] | None,
    ) -> None:
        if notification is None:
            return
        callback, code = notification
        with contextlib.suppress(Exception):
            callback(code)

    def finalize(self) -> D9StreamObservation:
        with self._lock:
            self._finalized = True
            self._events.append('finalize')
            failure_code = self._failure_code
            if failure_code is None:
                return D9StreamObservation(
                    process_role=self.process_role,
                    attempt_number=self.attempt_number,
                    stream=self.stream,
                    bytes_seen=self._bytes_seen,
                    ceiling=self.ceiling,
                    disposition=D9StreamDisposition.ACCEPTED,
                    terminal_category=D9StreamTerminalCategory.WITHIN_LIMIT,
                )
            return D9StreamObservation(
                process_role=self.process_role,
                attempt_number=self.attempt_number,
                stream=self.stream,
                bytes_seen=self._bytes_seen,
                ceiling=self.ceiling,
                disposition=D9StreamDisposition.FAILED,
                terminal_category=_d9_failure_category(failure_code),
                failure_code=failure_code,
            )

    def mark_published(self) -> None:
        with self._lock:
            self._events.append('publish')

    @property
    def events(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._events)


class D9Capture(Protocol):
    def finalize(self) -> D9CaptureReport: ...

    def verify_writer_quiescence(self) -> D9CaptureReport: ...


def _d9_observation_frame(observation: D9StreamObservation) -> dict[str, object]:
    return {
        'kind': 'D9_STREAM_OBSERVATION',
        'process_role': observation.process_role.value,
        'attempt_number': observation.attempt_number,
        'stream': observation.stream.value,
        'bytes_seen': observation.bytes_seen,
        'ceiling': observation.ceiling,
        'disposition': observation.disposition.value,
        'terminal_category': observation.terminal_category.value,
        'failure_code': observation.failure_code.value if observation.failure_code else None,
    }


def _d9_failure_frame(code: D9StreamFailureCode) -> dict[str, object]:
    return {'kind': 'D9_STREAM_FAILURE', 'failure_code': code.value}


def _d9_report_frames(report: D9CaptureReport) -> tuple[dict[str, object], ...]:
    frames = [_d9_observation_frame(item) for item in report.observations]
    frames.extend(_d9_failure_frame(code) for code in report.failure_codes)
    return tuple(frames)


def _send_d9_report(
    send_frame: Callable[[Mapping[str, object]], None], report: D9CaptureReport
) -> None:
    for frame in _d9_report_frames(report):
        send_frame(frame)


def _try_send_d9_report(
    send_frame: Callable[[Mapping[str, object]], None], report: D9CaptureReport
) -> None:
    with contextlib.suppress(Exception):
        _send_d9_report(send_frame, report)


def _d9_observation_from_frame(frame: Mapping[str, object]) -> D9StreamObservation | None:
    allowed = {
        'kind',
        'process_role',
        'attempt_number',
        'stream',
        'bytes_seen',
        'ceiling',
        'disposition',
        'terminal_category',
        'failure_code',
    }
    if not isinstance(frame, Mapping) or set(frame) != allowed:
        return None
    try:
        process_role_raw = frame['process_role']
        attempt_number_raw = frame['attempt_number']
        stream_raw = frame['stream']
        disposition_raw = frame['disposition']
        category_raw = frame['terminal_category']
        failure_raw = frame['failure_code']
        if (
            not isinstance(process_role_raw, str)
            or not isinstance(stream_raw, str)
            or not isinstance(disposition_raw, str)
            or not isinstance(category_raw, str)
        ):
            return None
        if attempt_number_raw is not None and type(attempt_number_raw) is not int:
            return None
        if failure_raw is None:
            failure_code = None
        elif isinstance(failure_raw, str):
            failure_code = D9StreamFailureCode(failure_raw)
        else:
            return None
        return D9StreamObservation(
            process_role=D9ProcessRole(process_role_raw),
            attempt_number=attempt_number_raw,
            stream=D9StreamName(stream_raw),
            bytes_seen=frame['bytes_seen'],  # type: ignore[arg-type]
            ceiling=frame['ceiling'],  # type: ignore[arg-type]
            disposition=D9StreamDisposition(disposition_raw),
            terminal_category=D9StreamTerminalCategory(category_raw),
            failure_code=failure_code,
        )
    except (TypeError, ValueError, KeyError):
        return None


def _d9_failure_from_frame(frame: Mapping[str, object]) -> D9StreamFailureCode | None:
    if not isinstance(frame, Mapping) or set(frame) != {'kind', 'failure_code'}:
        return None
    try:
        failure_raw = frame['failure_code']
        if not isinstance(failure_raw, str):
            return None
        return D9StreamFailureCode(failure_raw)
    except (TypeError, ValueError, KeyError):
        return None


def _d9_record_observation(
    observations: list[D9StreamObservation], observation: D9StreamObservation
) -> bool:
    key = (observation.attempt_number, observation.process_role, observation.stream)
    if any(
        (item.attempt_number, item.process_role, item.stream) == key for item in observations
    ):
        return False
    observations.append(observation)
    return True


def _d9_expected_streams(
    attempt_count: int | None,
) -> set[tuple[int | None, D9ProcessRole, D9StreamName]]:
    """Every D9 observation a run with ``attempt_count`` accepted attempts must publish.

    The outer adapter worker spans the whole worker lifetime -- one observation pair with
    ``attempt_number=None`` -- independent of how many generation attempts occurred inside
    it. Each accepted generation attempt (1 or 2, per the existing cardinality contract)
    contributes its own, separately keyed inner-child pair.
    """

    expected: set[tuple[int | None, D9ProcessRole, D9StreamName]] = {
        (None, D9ProcessRole.OUTER_ADAPTER_WORKER, stream) for stream in D9StreamName
    }
    for attempt_number in range(1, (attempt_count or 0) + 1):
        expected.update(
            (attempt_number, D9ProcessRole.INNER_GENERATION_CHILD, stream)
            for stream in D9StreamName
        )
    return expected


def _d9_fill_missing(
    observations: list[D9StreamObservation],
    failure_codes: list[D9StreamFailureCode],
    *,
    worker_died: bool,
    attempt_count: int | None,
) -> None:
    missing_code = (
        D9StreamFailureCode.WORKER_DIED_BEFORE_STREAM_FINALIZATION
        if worker_died
        else D9StreamFailureCode.STREAM_FINALIZATION_FAILED
    )
    missing_category = _d9_failure_category(missing_code)
    seen = {(item.attempt_number, item.process_role, item.stream) for item in observations}
    missing_found = False
    for attempt_number, process_role, stream in sorted(
        _d9_expected_streams(attempt_count),
        key=lambda item: (item[0] or 0, item[1].value, item[2].value),
    ):
        if (attempt_number, process_role, stream) in seen:
            continue
        missing_found = True
        observations.append(
            D9StreamObservation(
                process_role=process_role,
                attempt_number=attempt_number,
                stream=stream,
                bytes_seen=0,
                ceiling=_D9_STREAM_CEILINGS[stream],
                disposition=D9StreamDisposition.FAILED,
                terminal_category=missing_category,
                failure_code=missing_code,
            )
        )
    if missing_found and missing_code not in failure_codes:
        failure_codes.append(missing_code)


def _d9_success_contract(
    observations: tuple[D9StreamObservation, ...],
    failure_codes: tuple[D9StreamFailureCode, ...],
    *,
    attempt_count: int | None,
) -> bool:
    expected = _d9_expected_streams(attempt_count)
    if failure_codes or len(observations) != len(expected):
        return False
    observed = {(item.attempt_number, item.process_role, item.stream) for item in observations}
    return observed == expected and all(
        item.disposition is D9StreamDisposition.ACCEPTED
        and item.terminal_category is D9StreamTerminalCategory.WITHIN_LIMIT
        and item.failure_code is None
        and item.bytes_seen <= item.ceiling
        for item in observations
    )




@dataclass(slots=True)
class D9ProcessStreamCapture:
    '''Capture both process streams without retaining or decoding their payloads.'''

    process_role: D9ProcessRole
    attempt_number: int | None
    stdout_max_bytes: int
    stderr_max_bytes: int
    on_terminal_failure: D9TerminalFailureCallback | None = field(default=None, repr=False)
    _counters: dict[D9StreamName, D9BoundedByteCapture] = field(init=False)
    _read_fds: dict[D9StreamName, int] = field(default_factory=dict, init=False, repr=False)
    _saved_fds: dict[D9StreamName, int] = field(default_factory=dict, init=False, repr=False)
    _threads: dict[D9StreamName, threading.Thread] = field(
        default_factory=dict, init=False, repr=False
    )
    _late_read_fds: dict[D9StreamName, int] = field(
        default_factory=dict, init=False, repr=False
    )
    _late_threads: dict[D9StreamName, threading.Thread] = field(
        default_factory=dict, init=False, repr=False
    )
    _finalized: bool = field(default=False, init=False, repr=False)
    _quiescence_verified: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.stdout_max_bytes != D9_STDOUT_MAX_BYTES:
            raise ValueError('stdout D9 ceiling is not owner-approved')
        if self.stderr_max_bytes != D9_STDERR_MAX_BYTES:
            raise ValueError('stderr D9 ceiling is not owner-approved')
        self._counters = {
            D9StreamName.STDOUT: D9BoundedByteCapture(
                self.process_role,
                self.attempt_number,
                D9StreamName.STDOUT,
                self.stdout_max_bytes,
                self._handle_terminal_failure,
            ),
            D9StreamName.STDERR: D9BoundedByteCapture(
                self.process_role,
                self.attempt_number,
                D9StreamName.STDERR,
                self.stderr_max_bytes,
                self._handle_terminal_failure,
            ),
        }
        self._install()

    def _handle_terminal_failure(self, code: D9StreamFailureCode) -> None:
        if self.on_terminal_failure is not None:
            self.on_terminal_failure(code)

    def _install(self) -> None:
        try:
            for stream, fd in ((D9StreamName.STDOUT, 1), (D9StreamName.STDERR, 2)):
                read_fd, write_fd = os.pipe()
                saved_fd = os.dup(fd)
                os.set_inheritable(read_fd, False)
                os.set_inheritable(write_fd, False)
                os.dup2(write_fd, fd)
                os.set_inheritable(fd, False)
                os.close(write_fd)
                self._read_fds[stream] = read_fd
                self._saved_fds[stream] = saved_fd
                reader = threading.Thread(
                    target=self._reader,
                    args=(stream, read_fd),
                    daemon=True,
                )
                self._threads[stream] = reader
                reader.start()
        except BaseException:
            self._close_standard_writers()
            for fd in (*self._read_fds.values(), *self._saved_fds.values()):
                with contextlib.suppress(OSError):
                    os.close(fd)
            raise

    def _reader(self, stream: D9StreamName, read_fd: int) -> None:
        counter = self._counters[stream]
        try:
            while True:
                raw_bytes = os.read(read_fd, 4096)
                if not raw_bytes:
                    break
                counter.observe_chunk(raw_bytes)
        except Exception:  # noqa: BLE001 - only a typed read failure may cross the seam
            counter.mark_read_failed()

    def _late_reader(self, stream: D9StreamName, read_fd: int) -> None:
        counter = self._counters[stream]
        try:
            while True:
                raw_bytes = os.read(read_fd, 4096)
                if not raw_bytes:
                    break
                counter.mark_late_output()
        except Exception:  # noqa: BLE001 - only typed finalization state is retained
            counter.mark_finalization_failed()

    @staticmethod
    def _close_standard_writers() -> None:
        for fd in (1, 2):
            with contextlib.suppress(OSError):
                os.close(fd)

    def _flush_standard_writers(self) -> None:
        for stream, writer in (
            (D9StreamName.STDOUT, sys.stdout),
            (D9StreamName.STDERR, sys.stderr),
        ):
            try:
                writer.flush()
            except Exception:  # noqa: BLE001 - buffered failures remain typed
                self._counters[stream].mark_finalization_failed()

    def _switch_to_late_detection(self) -> None:
        for stream, fd in ((D9StreamName.STDOUT, 1), (D9StreamName.STDERR, 2)):
            read_fd: int | None = None
            write_fd: int | None = None
            try:
                read_fd, write_fd = os.pipe()
                os.set_inheritable(read_fd, False)
                os.set_inheritable(write_fd, False)
                os.dup2(write_fd, fd)
                os.set_inheritable(fd, False)
                os.close(write_fd)
                write_fd = None
                self._late_read_fds[stream] = read_fd
                reader = threading.Thread(
                    target=self._late_reader,
                    args=(stream, read_fd),
                    daemon=True,
                )
                self._late_threads[stream] = reader
                reader.start()
            except BaseException:
                self._counters[stream].mark_finalization_failed()
                if read_fd is not None:
                    with contextlib.suppress(OSError):
                        os.close(read_fd)
                if write_fd is not None:
                    with contextlib.suppress(OSError):
                        os.close(write_fd)
                with contextlib.suppress(OSError):
                    os.close(fd)

    def finalize(self) -> D9CaptureReport:
        if self._finalized:
            return D9CaptureReport(
                observations=tuple(counter.finalize() for counter in self._counters.values())
            )
        self._finalized = True
        self._flush_standard_writers()
        for stream in D9StreamName:
            self._counters[stream].stop_and_close()
        self._switch_to_late_detection()
        for stream, reader in self._threads.items():
            reader.join(timeout=1.0)
            if reader.is_alive():
                self._counters[stream].mark_finalization_failed()
        for counter in self._counters.values():
            counter.bounded_drain()
        for fd in (*self._read_fds.values(), *self._saved_fds.values()):
            try:
                os.close(fd)
            except OSError:
                for counter in self._counters.values():
                    counter.mark_finalization_failed()
        return D9CaptureReport(
            observations=tuple(counter.finalize() for counter in self._counters.values())
        )

    def verify_writer_quiescence(self) -> D9CaptureReport:
        if not self._finalized:
            self.finalize()
        if self._quiescence_verified:
            return D9CaptureReport(
                observations=tuple(counter.finalize() for counter in self._counters.values())
            )
        self._quiescence_verified = True
        self._flush_standard_writers()
        self._close_standard_writers()
        for stream, reader in self._late_threads.items():
            reader.join(timeout=1.0)
            if reader.is_alive():
                self._counters[stream].mark_finalization_failed()
        for fd in self._late_read_fds.values():
            with contextlib.suppress(OSError):
                os.close(fd)
        return D9CaptureReport(
            observations=tuple(counter.finalize() for counter in self._counters.values())
        )


D9CaptureFactory = Callable[
    [D9ProcessRole, int | None, int, int, D9TerminalFailureCallback | None], D9Capture
]


def _default_d9_capture_factory(
    process_role: D9ProcessRole,
    attempt_number: int | None,
    stdout_max_bytes: int,
    stderr_max_bytes: int,
    on_terminal_failure: D9TerminalFailureCallback | None,
) -> D9Capture:
    return D9ProcessStreamCapture(
        process_role,
        attempt_number,
        stdout_max_bytes,
        stderr_max_bytes,
        on_terminal_failure,
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
    stdout_max_bytes: int
    stderr_max_bytes: int
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
        if self.stdout_max_bytes != D9_STDOUT_MAX_BYTES:
            raise ValueError('stdout_max_bytes must equal the owner-approved D9 ceiling')
        if self.stderr_max_bytes != D9_STDERR_MAX_BYTES:
            raise ValueError('stderr_max_bytes must equal the owner-approved D9 ceiling')
        if self.cleanup_deadline_seconds <= 0:
            raise ValueError("cleanup_deadline_seconds must be positive")
        if self.containment_setup_timeout_seconds <= 0:
            raise ValueError("containment_setup_timeout_seconds must be positive")
        if self.posix_confirmation_timeout_seconds <= 0:
            raise ValueError("posix_confirmation_timeout_seconds must be positive")
        if self.posix_confirmation_retry_interval_seconds <= 0:
            raise ValueError("posix_confirmation_retry_interval_seconds must be positive")
        if (
            _positive_finite_float(self.per_attempt_timeout_seconds) is None
            or self.per_attempt_timeout_seconds > 120.0
        ):
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

    def fileno(self) -> int: ...

    def close(self) -> None: ...


class _WindowsNamedPipeAPI:
    """Private, correctly typed Kernel32 bindings for bounded named-pipe reads."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError("Windows named-pipe APIs are available only on Windows")
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32 = kernel32
        self._set_named_pipe_handle_state = kernel32.SetNamedPipeHandleState
        self._set_named_pipe_handle_state.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
        ]
        self._set_named_pipe_handle_state.restype = ctypes.c_int
        self._peek_named_pipe = kernel32.PeekNamedPipe
        self._peek_named_pipe.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
        ]
        self._peek_named_pipe.restype = ctypes.c_int

    def set_byte_read_mode(self, handle: ctypes.c_void_p) -> int | None:
        mode = ctypes.c_uint32(0)  # PIPE_READMODE_BYTE | PIPE_WAIT
        if self._set_named_pipe_handle_state(handle, ctypes.byref(mode), None, None):
            return None
        error_code = ctypes.get_last_error()
        return error_code

    def peek_available(self, handle: ctypes.c_void_p) -> tuple[int | None, int | None]:
        available = ctypes.c_uint32()
        if self._peek_named_pipe(handle, None, 0, None, ctypes.byref(available), None):
            return int(available.value), None
        error_code = ctypes.get_last_error()
        return None, error_code


_WINDOWS_NAMED_PIPE_API = _WindowsNamedPipeAPI() if os.name == "nt" else None


@dataclass(slots=True)
class MultiprocessingBoundedConnection:
    """Length-bounded, deadline-driven transport with no blocking helper reader."""

    connection: _RawConnection
    max_envelope_bytes: int
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    sleep: Callable[[float], None] = field(default=time.sleep, repr=False)
    frame_probe: Callable[[], str] | None = field(default=None, repr=False)
    read_chunk: Callable[[int], bytes | None] | None = field(default=None, repr=False)
    _receive_buffer: bytearray = field(default_factory=bytearray, init=False, repr=False)
    _socket_reader: socket.socket | None = field(default=None, init=False, repr=False)
    _windows_byte_mode_initialized: bool = field(default=False, init=False, repr=False)

    def send_frame(self, payload: Mapping[str, object]) -> None:
        encoded = encode_envelope(payload, max_bytes=self.max_envelope_bytes)
        # Windows PipeConnection transports one message without Connection's POSIX length
        # prefix. Add the same bounded frame header there so byte-mode incremental reads retain
        # an explicit frame boundary even when a large write exceeds the named-pipe buffer.
        if os.name == "nt":
            encoded = struct.pack("!i", len(encoded)) + encoded
        self.connection.send_bytes(encoded)

    def recv_frame(self, timeout: float) -> dict[str, object] | None:
        if not _is_finite_number(timeout) or timeout < 0:
            raise ValueError("receive timeout must be finite and non-negative")
        deadline = self.clock() + timeout
        if not math.isfinite(deadline):
            raise ValueError("receive deadline must be finite")
        if self.frame_probe is not None:
            return self._recv_using_probe(timeout, deadline)
        return self._recv_incrementally(timeout, deadline)

    def _recv_using_probe(self, timeout: float, deadline: float) -> dict[str, object] | None:
        """Deterministic fixture seam for deadline edge tests; production reads incrementally."""
        assert self.frame_probe is not None
        first_probe = True
        while True:
            state = self.frame_probe()
            if state == "complete":
                raw = self.connection.recv_bytes(maxlength=self.max_envelope_bytes)
                if timeout > 0 and self.clock() >= deadline:
                    raise Feat018ProtocolViolationError("IPC frame completed after its receive deadline")
                payload = decode_envelope(raw)
                if timeout > 0 and self.clock() >= deadline:
                    raise Feat018ProtocolViolationError("IPC frame decoding exceeded its receive deadline")
                return payload
            if state == "eof":
                return None
            if state not in {"empty", "incomplete"}:
                raise Feat018ProtocolViolationError("invalid IPC frame probe state")

            now = self.clock()
            if not first_probe and now >= deadline:
                if state == "incomplete":
                    raise Feat018ProtocolViolationError("IPC frame was truncated at its receive deadline")
                return None
            if timeout == 0:
                if state == "incomplete":
                    raise Feat018ProtocolViolationError("IPC frame was incomplete at a non-blocking read")
                return None
            first_probe = False
            remaining = deadline - now
            if remaining <= 0:
                if state == "incomplete":
                    raise Feat018ProtocolViolationError("IPC frame was truncated at its receive deadline")
                return None
            self.sleep(min(0.005, remaining))

    def _recv_incrementally(self, timeout: float, deadline: float) -> dict[str, object] | None:
        while True:
            frame_size = self._expected_frame_size()
            if frame_size is not None and len(self._receive_buffer) >= frame_size:
                header_size = 12 if self._receive_buffer[:4] == b"\xff\xff\xff\xff" else 4
                payload = bytes(self._receive_buffer[header_size:frame_size])
                del self._receive_buffer[:frame_size]
                if timeout > 0 and self.clock() >= deadline:
                    raise Feat018ProtocolViolationError("IPC frame completed after its receive deadline")
                decoded = decode_envelope(payload)
                if timeout > 0 and self.clock() >= deadline:
                    raise Feat018ProtocolViolationError("IPC frame decoding exceeded its receive deadline")
                return decoded

            if frame_size is None:
                needed = (12 if self._receive_buffer[:4] == b"\xff\xff\xff\xff" else 4)
                needed -= len(self._receive_buffer)
            else:
                needed = frame_size - len(self._receive_buffer)

            if timeout > 0 and self.clock() >= deadline:
                if self._receive_buffer:
                    raise Feat018ProtocolViolationError(
                        "IPC frame was truncated at its receive deadline"
                    )
                return None
            chunk = self._read_available(needed)
            if chunk == b"":
                if self._receive_buffer:
                    raise Feat018ProtocolViolationError("truncated IPC frame at peer EOF")
                return None
            if chunk:
                self._receive_buffer.extend(chunk)
                if timeout > 0 and self.clock() >= deadline:
                    completed_size = self._expected_frame_size()
                    if completed_size is not None and len(self._receive_buffer) >= completed_size:
                        raise Feat018ProtocolViolationError(
                            "IPC frame completed after its receive deadline"
                        )
                    raise Feat018ProtocolViolationError(
                        "IPC frame was truncated at its receive deadline"
                    )
                continue

            now = self.clock()
            if now >= deadline:
                if self._receive_buffer:
                    raise Feat018ProtocolViolationError("IPC frame was truncated at its receive deadline")
                return None
            if timeout == 0:
                if self._receive_buffer:
                    raise Feat018ProtocolViolationError("IPC frame was incomplete at a non-blocking read")
                return None
            self.sleep(min(0.005, deadline - now))

    def _expected_frame_size(self) -> int | None:
        if len(self._receive_buffer) < 4:
            return None
        payload_size = struct.unpack("!i", self._receive_buffer[:4])[0]
        header_size = 4
        if payload_size == -1:
            if len(self._receive_buffer) < 12:
                return None
            payload_size = struct.unpack("!Q", self._receive_buffer[4:12])[0]
            header_size = 12
        elif payload_size < 0:
            raise Feat018ProtocolViolationError("invalid IPC frame length")
        if payload_size > self.max_envelope_bytes:
            raise Feat018ProtocolViolationError("declared frame length exceeds the IPC envelope ceiling")
        return header_size + payload_size

    def _read_available(self, maximum: int) -> bytes | None:
        if maximum <= 0:
            raise Feat018ProtocolViolationError("invalid IPC read remainder")
        if self.read_chunk is not None:
            return self.read_chunk(maximum)
        if os.name == "nt":
            api = _WINDOWS_NAMED_PIPE_API
            if api is None:
                raise Feat018ProtocolViolationError("Windows IPC API is unavailable")
            handle = ctypes.c_void_p(self.connection.fileno())
            if not self._windows_byte_mode_initialized:
                error_code = api.set_byte_read_mode(handle)
                if error_code is not None:
                    cause = OSError(error_code, "SetNamedPipeHandleState failed")
                    raise Feat018ProtocolViolationError(
                        "Windows IPC byte-stream mode could not be established"
                    ) from cause
                self._windows_byte_mode_initialized = True
            available, error_code = api.peek_available(handle)
            if error_code is not None:
                if error_code in {109, 232}:
                    return b""
                cause = OSError(error_code, "PeekNamedPipe failed")
                raise Feat018ProtocolViolationError(
                    "Windows IPC availability probe failed"
                ) from cause
            assert available is not None
            if available == 0:
                return None
            try:
                return self.connection.recv_bytes(maxlength=min(maximum, available))
            except EOFError:
                return b""
            except OSError as exc:
                raise Feat018ProtocolViolationError("Windows IPC bounded read failed") from exc

        if self._socket_reader is None:
            try:
                self._socket_reader = socket.socket(
                    family=socket.AF_UNIX, type=socket.SOCK_STREAM,
                    fileno=os.dup(self.connection.fileno()),
                )
            except OSError as exc:
                raise Feat018ProtocolViolationError("IPC endpoint cannot be safely read") from exc
        try:
            return self._socket_reader.recv(maximum, socket.MSG_DONTWAIT)
        except BlockingIOError:
            return None
        except OSError as exc:
            raise Feat018ProtocolViolationError("IPC non-blocking read failed") from exc

    def close(self) -> None:
        close_error: Exception | None = None
        socket_reader = self._socket_reader
        self._socket_reader = None
        if socket_reader is not None:
            try:
                socket_reader.close()
            except Exception as exc:  # noqa: BLE001 - always attempt the owned raw endpoint too
                close_error = exc
        try:
            self.connection.close()
        except Exception as exc:  # noqa: BLE001 - surface the actual endpoint close failure
            if close_error is None:
                close_error = exc
        if close_error is not None:
            raise close_error


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

    @property
    def exitcode(self) -> int | None: ...

    def is_alive(self) -> bool: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    def join(self, timeout: float | None = None) -> None: ...

    def close(self) -> None: ...


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

    def terminate_all(
        self,
        *,
        cleanup_deadline_monotonic: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        """Terminate every process in this containment in one action."""

    def is_empty(self) -> bool:
        """Return whether the containment currently has zero live members."""

    def close(self) -> None:
        """Release the containment primitive itself (not its members)."""


def _terminate_owned_containment(
    containment: ContainmentBackend,
    *,
    cleanup_deadline_monotonic: float | None,
    clock: Callable[[], float],
) -> None:
    if cleanup_deadline_monotonic is None:
        containment.terminate_all()
    else:
        containment.terminate_all(
            cleanup_deadline_monotonic=cleanup_deadline_monotonic, clock=clock
        )


def _close_verified_empty_containment(containment: ContainmentBackend) -> None:
    """Retain the query/control handle while live membership remains unverified."""

    if not containment.is_empty():
        raise Feat018ContainmentError('containment release requires observed emptiness')
    containment.close()


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
    sigkill_grace_seconds: float = 1.0
    sigkill_poll_interval_seconds: float = 0.02
    _cleanup_failed: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        for value, label in (
            (self.sigkill_grace_seconds, "sigkill_grace_seconds"),
            (self.sigkill_poll_interval_seconds, "sigkill_poll_interval_seconds"),
        ):
            if _positive_finite_float(value) is None:
                raise ValueError(f"{label} must be positive and finite")

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

    def _group_is_empty(self) -> bool:
        if self._group_pid is None:
            return True
        try:
            _posix_killpg(self._group_pid, 0)
        except ProcessLookupError:
            return True
        except OSError:
            return False
        return False

    def terminate_all(
        self,
        *,
        cleanup_deadline_monotonic: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        """Bounded SIGTERM-then-SIGKILL escalation against the whole process group.

        One SIGTERM is not proof of termination: any member of the group may install a handler
        that traps or ignores it (independent-review finding B3-1). This sends SIGTERM, then polls
        for emptiness for only ``sigkill_grace_seconds``, then escalates to SIGKILL -- which cannot
        be caught, blocked, or ignored on POSIX -- if any member is still alive. This method never
        blocks longer than ``sigkill_grace_seconds`` plus one bounded poll interval; final proof of
        an empty group is still the caller's own bounded ``is_empty()`` polling loop, never this
        method's return alone.
        """

        if self._group_pid is None:
            return
        with contextlib.suppress(OSError):
            _posix_killpg(self._group_pid, 15)  # SIGTERM
        if self._group_is_empty():
            return
        cleanup_clock = clock or self._clock
        deadline = cleanup_clock() + self.sigkill_grace_seconds
        if cleanup_deadline_monotonic is not None:
            deadline = min(deadline, cleanup_deadline_monotonic)
        while cleanup_clock() < deadline:
            if self._group_is_empty():
                return
            remaining = max(0.0, deadline - cleanup_clock())
            try:
                self._sleep(min(self.sigkill_poll_interval_seconds, remaining))
            except Exception:  # noqa: BLE001 - a broken wait still proceeds to SIGKILL
                break
        if self._group_is_empty():
            return
        try:
            _posix_killpg(self._group_pid, 9)  # SIGKILL: cannot be caught, blocked, or ignored
        except ProcessLookupError:
            return
        except OSError:
            # The escalation attempt itself failed; never claim success while unproven. The
            # caller's is_empty() polling loop still owns the final fail-closed verdict.
            self._cleanup_failed = True

    def is_empty(self) -> bool:
        """F1-equivalent for POSIX: truthful, queried emptiness. Never assumed true."""

        return self._group_is_empty()

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
    _empty_verified: bool = field(default=False, init=False, repr=False)
    _win32: _Win32JobHandles = field(default_factory=lambda: _Win32JobHandles())

    def create(self) -> None:
        if self._job_handle is not None or self._process_handle is not None:
            raise Feat018ContainmentError("containment still owns unreleased handles")
        self._cleanup_failed = False
        job_handle = self._win32.create_job_object()
        self._job_handle = job_handle
        self._empty_verified = True
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
        if self._process_handle is not None:
            raise Feat018ContainmentError("containment still owns an unreleased process handle")
        try:
            process_handle = self._win32.open_process(worker.pid)
        except Feat018ContainmentError:
            return False
        self._process_handle = process_handle
        self._empty_verified = False
        try:
            assigned = self._win32.assign_process_to_job_object(self._job_handle, process_handle)
            verified = assigned and self._win32.is_process_in_job(
                process_handle, self._job_handle
            )
        except Exception:  # noqa: BLE001 - close the unregistered process handle
            try:
                self._win32.close_handle(process_handle)
                self._process_handle = None
            except Exception:  # noqa: BLE001 - assignment already failed; fail closed
                self._cleanup_failed = True
            raise
        if not verified:
            try:
                self._win32.close_handle(process_handle)
                self._process_handle = None
            except Exception:  # noqa: BLE001 - verification failed; fail closed
                self._cleanup_failed = True
            return False
        return True

    def terminate_all(
        self,
        *,
        cleanup_deadline_monotonic: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        del cleanup_deadline_monotonic, clock
        if self._job_handle is not None:
            self._win32.terminate_job_object(self._job_handle)

    def is_empty(self) -> bool:
        """F1: truthful, queried emptiness. A query failure fails closed (never ``True``)."""

        if self._job_handle is None:
            return self._empty_verified
        try:
            active_count = self._win32.query_active_process_count(self._job_handle)
        except Feat018ContainmentError:
            self._cleanup_failed = True
            self._empty_verified = False
            return False
        self._empty_verified = active_count == 0
        return self._empty_verified

    def close(self) -> None:
        process_handle = self._process_handle
        job_handle = self._job_handle
        close_failed = False
        if process_handle is not None:
            try:
                self._win32.close_handle(process_handle)
                self._process_handle = None
            except Exception:  # noqa: BLE001 - always continue to the job handle
                close_failed = True
        if job_handle is not None:
            try:
                self._win32.close_handle(job_handle)
                self._job_handle = None
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
class _OwnedProcessHandle:
    """Own the stdlib handle and preserve launch/exit facts after releasing it."""

    process: _LaunchProcess
    started_at_monotonic: float | None = None
    closed: bool = field(default=False, init=False)
    _closed_pid: int | None = field(default=None, init=False, repr=False)
    _closed_exitcode: int | None = field(default=None, init=False, repr=False)

    @property
    def pid(self) -> int | None:
        return self._closed_pid if self.closed else self.process.pid

    @property
    def exitcode(self) -> int | None:
        return self._closed_exitcode if self.closed else self.process.exitcode

    def is_alive(self) -> bool:
        return False if self.closed else self.process.is_alive()

    def terminate(self) -> None:
        if not self.closed:
            self.process.terminate()

    def kill(self) -> None:
        if not self.closed:
            self.process.kill()

    def join(self, timeout: float | None = None) -> None:
        if not self.closed:
            self.process.join(timeout)

    def close(self) -> None:
        if self.closed:
            return
        self._closed_pid = self.process.pid
        self._closed_exitcode = self.process.exitcode
        self.process.close()
        self.closed = True


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
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    cleanup_deadline: Callable[[], float | None] | None = field(default=None, repr=False)

    def launch(
        self, entry: Callable[..., None], args: tuple[object, ...]
    ) -> tuple[ProcessHandle, BoundedConnection]:
        parent_conn: _RawConnection | None = None
        child_conn: _RawConnection | None = None
        process: _OwnedProcessHandle | None = None
        cleanup_failed = False

        try:
            context = self.context_factory()
            parent_conn, child_conn = context.Pipe(duplex=True)
            bounded_child_conn = self.connection_factory(
                child_conn, self.max_envelope_bytes
            )
            process = _OwnedProcessHandle(
                context.Process(
                    target=entry,
                    args=(bounded_child_conn, *args),
                    daemon=False,
                )
            )
            process.process.start()
            process.started_at_monotonic = self.clock()

            if not _close_owned_ipc_endpoint(child_conn):
                cleanup_failed = True
                raise Feat018CleanupFailedError from None
            child_conn = None

            bounded_parent_conn = self.connection_factory(
                parent_conn, self.max_envelope_bytes
            )
            return process, bounded_parent_conn
        except Exception:  # noqa: BLE001 - all failures become sanitized typed errors
            cleanup_deadline_monotonic: float | None = None
            if self.cleanup_deadline is not None:
                try:
                    cleanup_deadline_monotonic = self.cleanup_deadline()
                except Exception:  # noqa: BLE001 - a missing grant cannot extend cleanup
                    cleanup_failed = True
                    cleanup_deadline_monotonic = 0.0
            if (
                process is not None
                and not _bounded_terminate_kill_join(
                    process,
                    grace_seconds=1.0,
                    kill_join_seconds=1.0,
                    cleanup_deadline_monotonic=cleanup_deadline_monotonic,
                    clock=self.clock,
                )
            ):
                cleanup_failed = True
            if child_conn is not None:
                if not _close_owned_ipc_endpoint(child_conn):
                    cleanup_failed = True
                else:
                    child_conn = None
            if parent_conn is not None:
                if not _close_owned_ipc_endpoint(parent_conn):
                    cleanup_failed = True
                else:
                    parent_conn = None
            if cleanup_failed:
                raise Feat018CleanupFailedError(
                    "bounded process launch cleanup failed",
                    owned_process=process if process is not None and not process.closed else None,
                    owned_connections=tuple(
                        connection
                        for connection in (child_conn, parent_conn)
                        if connection is not None
                    ),
                ) from None
            raise Feat018LauncherError("bounded process launch failed") from None


def _close_owned_ipc_endpoint(connection: BoundedConnection | _RawConnection) -> bool:
    """Close one locally owned raw endpoint without leaking the original exception."""

    try:
        connection.close()
    except Exception:  # noqa: BLE001 - the caller reports a typed cleanup failure
        return False
    return True


def _bounded_terminate_kill_join(
    process: ProcessHandle,
    *,
    grace_seconds: float,
    kill_join_seconds: float,
    cleanup_deadline_monotonic: float | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> bool:
    """Stop and reap the process before releasing its locally owned handle."""

    if isinstance(process, _OwnedProcessHandle) and process.closed:
        return True

    cleanup_succeeded = True

    def join_timeout(phase_limit: float) -> float:
        nonlocal cleanup_succeeded
        if cleanup_deadline_monotonic is None:
            return phase_limit
        try:
            remaining = cleanup_deadline_monotonic - clock()
        except Exception:  # noqa: BLE001 - unavailable clocks cannot permit a blocking wait
            cleanup_succeeded = False
            return 0.0
        if not math.isfinite(remaining):
            cleanup_succeeded = False
            return 0.0
        return min(phase_limit, max(0.0, remaining))
    try:
        initially_alive: bool | None = bool(process.is_alive())
    except Exception:  # noqa: BLE001 - unknown liveness must fail closed
        initially_alive = None
        cleanup_succeeded = False

    try:
        was_started = process.pid is not None
    except Exception:  # noqa: BLE001 - unknown launch state cannot authorize handle close
        was_started = True
        cleanup_succeeded = False

    reaped = not was_started and initially_alive is False
    if initially_alive is not False:
        try:
            process.terminate()
        except Exception:  # noqa: BLE001 - continue to the bounded join and kill attempt
            cleanup_succeeded = False
        try:
            process.join(timeout=join_timeout(grace_seconds))
        except Exception:  # noqa: BLE001 - continue to the bounded kill attempt
            cleanup_succeeded = False
        else:
            reaped = True

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
                process.join(timeout=join_timeout(kill_join_seconds))
            except Exception:  # noqa: BLE001 - report failure without escaping cleanup
                cleanup_succeeded = False
                reaped = False
            else:
                reaped = True
    elif was_started:
        try:
            process.join(timeout=join_timeout(grace_seconds))
        except Exception:  # noqa: BLE001 - a stopped but unreaped handle stays owned
            cleanup_succeeded = False
        else:
            reaped = True

    try:
        alive_after_cleanup = bool(process.is_alive())
    except Exception:  # noqa: BLE001 - final liveness cannot be verified
        alive_after_cleanup = True
        cleanup_succeeded = False
    if alive_after_cleanup:
        cleanup_succeeded = False
    if was_started:
        try:
            reaped = reaped and process.exitcode is not None
        except Exception:  # noqa: BLE001 - unknown exit status retains handle ownership
            reaped = False
    if not alive_after_cleanup and reaped:
        try:
            process.close()
        except Exception:  # noqa: BLE001 - close failure leaves the handle owned
            cleanup_succeeded = False
    else:
        cleanup_succeeded = False
    return cleanup_succeeded


def _cleanup_deadline_from_hooks(
    *,
    on_cleanup_intent: Callable[[], float] | None,
    cleanup_deadline: Callable[[], float | None] | None,
    work_deadline_monotonic: float | None = None,
) -> float | None:
    deadline = work_deadline_monotonic
    if on_cleanup_intent is not None:
        deadline = on_cleanup_intent()
        if deadline is None:
            raise Feat018CleanupFailedError('cleanup deadline grant was absent')
    supplied = cleanup_deadline() if cleanup_deadline is not None else None
    for grant in (deadline, supplied):
        if grant is not None and (
            isinstance(grant, bool)
            or not isinstance(grant, (int, float))
            or not math.isfinite(grant)
        ):
            raise Feat018CleanupFailedError('cleanup deadline grant was invalid')
    if supplied is not None:
        deadline = supplied if deadline is None else min(deadline, supplied)
    return deadline


# --------------------------------------------------------------------------------------
# Per-attempt bounded generation runner
# --------------------------------------------------------------------------------------


def _generation_child_entry(
    connection: BoundedConnection,
    profile: VisionProfileV2,
    runtime_config: QwenVisionRuntimeConfig,
    image_path: str,
    prompt: str,
    raw_output_max_bytes: int,
    ipc_envelope_max_bytes: int,
    capture_factory: D9CaptureFactory | None = None,
    attempt_number: int = 1,
) -> None:
    """Real child target: load, generate, and send one bounded envelope. Not offline-tested."""

    return _generation_child_entry_with_capture(
        connection,
        profile,
        runtime_config,
        image_path,
        prompt,
        raw_output_max_bytes,
        ipc_envelope_max_bytes,
        capture_factory=capture_factory or _default_d9_capture_factory,
        attempt_number=attempt_number,
    )


def _dev_registered_generation_child_entry(
    connection: BoundedConnection, profile: VisionProfileV2,
    runtime_config: QwenVisionRuntimeConfig, image_path: str, prompt: str,
    raw_output_max_bytes: int, ipc_envelope_max_bytes: int,
    capture_factory: D9CaptureFactory | None, attempt_number: int,
) -> None:
    """Install existing D9 capture before waiting for trusted model release."""
    _generation_child_entry_with_capture(
        connection, profile, runtime_config, image_path, prompt,
        raw_output_max_bytes, ipc_envelope_max_bytes,
        capture_factory=capture_factory or _default_d9_capture_factory,
        attempt_number=attempt_number, require_registration=True,
    )

def _generation_child_entry_with_capture(
    connection: BoundedConnection,
    profile: VisionProfileV2,
    runtime_config: QwenVisionRuntimeConfig,
    image_path: str,
    prompt: str,
    raw_output_max_bytes: int,
    ipc_envelope_max_bytes: int,
    *,
    capture_factory: D9CaptureFactory,
    attempt_number: int,
    require_registration: bool = False,
) -> None:
    # The process launcher applies this ceiling before the endpoint crosses the spawn
    # boundary. Re-wrapping that bounded endpoint would hide its send_frame API behind
    # a nonexistent raw send_bytes method.
    del ipc_envelope_max_bytes
    bounded = connection
    send_frame = _synchronized_frame_sender(bounded.send_frame)

    def _notify_terminal_failure(code: D9StreamFailureCode) -> None:
        _try_send_d9_failure(send_frame, code)

    try:
        capture = capture_factory(
            D9ProcessRole.INNER_GENERATION_CHILD,
            attempt_number,
            D9_STDOUT_MAX_BYTES,
            D9_STDERR_MAX_BYTES,
            _notify_terminal_failure,
        )
    except Exception:  # noqa: BLE001 - only a typed D9 failure crosses the boundary
        report = D9CaptureReport.failure(
            D9ProcessRole.INNER_GENERATION_CHILD,
            D9StreamFailureCode.STREAM_FINALIZATION_FAILED,
            attempt_number=attempt_number,
        )
        _try_send_d9_report(send_frame, report)
        _try_send(send_frame, {'kind': 'd9_failure', 'failure_code': report.failure_codes[0].value})
        return

    outcome_frame: dict[str, object] = {'kind': 'provider_failure'}
    try:
        if require_registration:
            try:
                release = bounded.recv_frame(min(profile.timeout_seconds, 5.0))
            except Exception:
                return
            if release != {'kind': 'DEV_GENERATION_READY'}:
                return
        from sketch2life.infrastructure.ai.qwen_vision import (  # noqa: PLC0415
            _default_model_factory,
            _generate_from_bundle,
        )

        try:
            bundle = _default_model_factory(profile, runtime_config)
        except QwenDeviceUnavailableError:
            outcome_frame = {'kind': 'device_unavailable'}
        except QwenModelLoadError:
            outcome_frame = {'kind': 'model_load_failed'}
        except Exception:  # noqa: BLE001 - sanitized below
            outcome_frame = {'kind': 'model_load_failed'}
        else:
            try:
                raw_output = _generate_from_bundle(bundle, profile, Path(image_path), prompt)
            except QwenTimeoutError:
                outcome_frame = {'kind': 'timeout'}
            except Exception:  # noqa: BLE001 - sanitized below
                outcome_frame = {'kind': 'provider_failure'}
            else:
                if not isinstance(raw_output, str):
                    outcome_frame = {'kind': 'provider_failure'}
                elif len(raw_output.encode('utf-8')) > raw_output_max_bytes:
                    outcome_frame = {'kind': 'raw_output_overflow'}
                else:
                    outcome_frame = {'kind': 'success', 'raw_output': raw_output}
    except Exception:  # noqa: BLE001 - import/runtime details never cross the boundary
        outcome_frame = {'kind': 'provider_failure'}
    finally:
        try:
            capture.finalize()
            report = capture.verify_writer_quiescence()
        except Exception:  # noqa: BLE001 - finalization is fail-closed and typed
            report = D9CaptureReport.failure(
                D9ProcessRole.INNER_GENERATION_CHILD,
                D9StreamFailureCode.STREAM_FINALIZATION_FAILED,
                attempt_number=attempt_number,
            )
        _try_send_d9_report(send_frame, report)
        if report.failed:
            outcome_frame = {
                'kind': 'd9_failure',
                'failure_code': report.failure_codes[0].value,
            }
        try:
            send_frame(outcome_frame)
        except Feat018FrameTooLargeError:
            _try_send(send_frame, {'kind': 'ipc_envelope_overflow'})


def _synchronized_frame_sender(
    send_frame: Callable[[Mapping[str, object]], None],
) -> Callable[[Mapping[str, object]], None]:
    send_lock = threading.Lock()

    def _send(payload: Mapping[str, object]) -> None:
        with send_lock:
            send_frame(payload)

    return _send


def _try_send(
    send_frame: Callable[[Mapping[str, object]], None],
    payload: Mapping[str, object],
) -> None:
    with contextlib.suppress(OSError):
        send_frame(payload)


def _try_send_d9_failure(
    send_frame: Callable[[Mapping[str, object]], None], code: D9StreamFailureCode
) -> None:
    with contextlib.suppress(Exception):
        send_frame(_d9_failure_frame(code))


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
    on_d9_report: Callable[[D9CaptureReport], None] | None = None
    on_cleanup_failure: Callable[[Feat018CleanupFailedError], None] | None = None
    capture_factory: D9CaptureFactory = _default_d9_capture_factory
    _attempt_number: int = field(default=0, init=False, repr=False)
    cleanup_failure: Feat018CleanupFailedError | None = field(
        default=None, init=False, repr=False
    )
    cleanup_deadline: Callable[[], float | None] | None = field(default=None, repr=False)
    on_cleanup_intent: Callable[[], float] | None = field(default=None, repr=False)
    register_generation: Callable[[ProcessHandle], None] | None = field(default=None, repr=False)

    def _record_cleanup_failure(self, failure: Feat018CleanupFailedError) -> None:
        self.cleanup_failure = failure
        if self.on_cleanup_failure is not None:
            with contextlib.suppress(Exception):
                self.on_cleanup_failure(failure)

    def generate(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        return self._generate_once_with_d9(profile, runtime_config, image_path, prompt)

    def _generate_once_with_d9(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        if self.cleanup_failure is not None:
            raise QwenPermanentRuntimeError('generation cleanup failed')
        remaining = self.worker_cap_deadline_monotonic - self.clock()
        positive_remaining = _positive_finite_float(remaining)
        if positive_remaining is None:
            raise QwenPermanentRuntimeError('total adapter cap already exhausted')
        self._attempt_number += 1
        attempt_number = self._attempt_number
        if self.on_attempt_start is not None:
            self.on_attempt_start()
        try:
            process, connection = self.launcher.launch(
                _dev_registered_generation_child_entry if self.register_generation is not None
                else _generation_child_entry,
                (
                    profile,
                    runtime_config,
                    str(image_path),
                    prompt,
                    self.config.raw_output_max_bytes,
                    self.config.ipc_envelope_max_bytes,
                    self.capture_factory,
                    attempt_number,
                ),
            )
        except Feat018CleanupFailedError as error:
            self._record_cleanup_failure(error)
            try:
                cleanup_deadline_monotonic = _cleanup_deadline_from_hooks(
                    on_cleanup_intent=self.on_cleanup_intent,
                    cleanup_deadline=self.cleanup_deadline,
                )
            except Exception:  # noqa: BLE001 - a missing grant allows only non-blocking cleanup
                cleanup_deadline_monotonic = 0.0
            error.retry_cleanup(
                grace_seconds=1.0,
                kill_join_seconds=1.0,
                cleanup_deadline_monotonic=cleanup_deadline_monotonic,
                clock=self.clock,
            )
            raise QwenPermanentRuntimeError('generation cleanup failed') from None
        frame: dict[str, object] | None = None
        observations: list[D9StreamObservation] = []
        failure_codes: list[D9StreamFailureCode] = []
        worker_died = False
        cleanup_succeeded = True
        outcome_received = False
        post_cleanup_protocol_valid = True
        deadline_expired = False
        effective_deadline = self.worker_cap_deadline_monotonic
        decoded_raw_output: str | None = None
        decoded_failure: Exception | None = None
        try:
            try:
                if self.register_generation is not None:
                    self.register_generation(process)
                    connection.send_frame({'kind': 'DEV_GENERATION_READY'})
                attempt_started_at = getattr(process, 'started_at_monotonic', None)
                if attempt_started_at is None:
                    # Injected synthetic launchers may use the runner's clock at launch return.
                    attempt_started_at = self.clock()
                attempt_deadline = attempt_started_at + self.config.per_attempt_timeout_seconds
                effective_deadline = min(attempt_deadline, self.worker_cap_deadline_monotonic)
                while True:
                    remaining = effective_deadline - self.clock()
                    if _positive_finite_float(remaining) is None:
                        deadline_expired = True
                        frame = None
                        break
                    frame = connection.recv_frame(remaining)
                    if frame is None:
                        deadline_expired = self.clock() >= effective_deadline
                        try:
                            worker_died = not process.is_alive()
                        except Exception:  # noqa: BLE001 - unknown liveness fails closed
                            worker_died = True
                        break
                    if _positive_finite_float(
                        effective_deadline - self.clock()
                    ) is None:
                        deadline_expired = True
                        frame = None
                        break
                    if frame.get('kind') == 'D9_STREAM_OBSERVATION':
                        observation = _d9_observation_from_frame(frame)
                        if (
                            observation is None
                            or observation.process_role is not D9ProcessRole.INNER_GENERATION_CHILD
                            or observation.attempt_number != attempt_number
                            or observation.stream
                            in {item.stream for item in observations}
                        ):
                            raise Feat018ProtocolViolationError('malformed D9 stream observation')
                        observations.append(observation)
                        if observation.failed:
                            assert observation.failure_code is not None
                            if observation.failure_code not in failure_codes:
                                failure_codes.append(observation.failure_code)
                            break
                        continue
                    if frame.get('kind') == 'D9_STREAM_FAILURE':
                        code = _d9_failure_from_frame(frame)
                        if code is None:
                            raise Feat018ProtocolViolationError('malformed D9 stream failure')
                        if code not in failure_codes:
                            failure_codes.append(code)
                        break
                    outcome_received = True
                    break
            except (Feat018ProtocolViolationError, EOFError, OSError):
                raise QwenPermanentRuntimeError from None
            if frame is not None and not failure_codes:
                try:
                    decoded_raw_output = _interpret_generation_child_frame(frame)
                except Exception as error:  # noqa: BLE001 - retain the typed adapter decision
                    decoded_failure = error
        finally:
            owned_process: ProcessHandle | None = None
            owned_connections: tuple[BoundedConnection, ...] = ()
            cleanup_deadline_monotonic: float | None = None
            cleanup_intent_started = False

            def begin_failure_cleanup() -> None:
                nonlocal cleanup_deadline_monotonic, cleanup_intent_started
                if cleanup_intent_started or self.on_cleanup_intent is None:
                    return
                cleanup_intent_started = True
                try:
                    cleanup_deadline_monotonic = _cleanup_deadline_from_hooks(
                        on_cleanup_intent=self.on_cleanup_intent,
                        cleanup_deadline=self.cleanup_deadline,
                    )
                except Exception:  # noqa: BLE001 - missing grants allow no extra wait
                    cleanup_deadline_monotonic = 0.0

            if self.on_cleanup_intent is not None or self.cleanup_deadline is not None:
                terminal_cleanup = (
                    deadline_expired
                    or worker_died
                    or bool(failure_codes)
                    or frame is None
                    or (
                        decoded_failure is not None
                        and not isinstance(decoded_failure, QwenTransientRuntimeError)
                    )
                    or sys.exc_info()[0] is not None
                )
                cleanup_intent_started = terminal_cleanup
                try:
                    cleanup_deadline_monotonic = _cleanup_deadline_from_hooks(
                        on_cleanup_intent=self.on_cleanup_intent if terminal_cleanup else None,
                        cleanup_deadline=self.cleanup_deadline,
                        work_deadline_monotonic=effective_deadline,
                    )
                except Exception:  # noqa: BLE001 - never reset after a missing cleanup handoff
                    cleanup_deadline_monotonic = 0.0
                    cleanup_succeeded = False
            if not _bounded_terminate_kill_join(
                process,
                grace_seconds=1.0,
                kill_join_seconds=1.0,
                cleanup_deadline_monotonic=cleanup_deadline_monotonic,
                clock=self.clock,
            ):
                cleanup_succeeded = False
                begin_failure_cleanup()
                if not bool(getattr(process, 'closed', False)):
                    owned_process = process
            post_cleanup_protocol_valid = self._drain_post_cleanup_d9(
                connection,
                observations,
                failure_codes,
                attempt_number=attempt_number,
                outcome_received=outcome_received,
            )
            if not post_cleanup_protocol_valid:
                begin_failure_cleanup()
            try:
                connection.close()
            except Exception:  # noqa: BLE001 - cleanup must not hide the bounded result
                cleanup_succeeded = False
                begin_failure_cleanup()
                owned_connections = (connection,)
            if (
                cleanup_deadline_monotonic is not None
                and self.clock() >= cleanup_deadline_monotonic
            ):
                cleanup_succeeded = False
                begin_failure_cleanup()
            if not cleanup_succeeded:
                self._record_cleanup_failure(
                    Feat018CleanupFailedError(
                        'generation cleanup failed',
                        owned_process=owned_process,
                        owned_connections=owned_connections,
                    )
                )

        if not post_cleanup_protocol_valid and (
            D9StreamFailureCode.STREAM_FINALIZATION_FAILED not in failure_codes
        ):
            failure_codes.append(D9StreamFailureCode.STREAM_FINALIZATION_FAILED)

        if worker_died:
            report = D9CaptureReport.failure(
                D9ProcessRole.INNER_GENERATION_CHILD,
                D9StreamFailureCode.WORKER_DIED_BEFORE_STREAM_FINALIZATION,
                attempt_number=attempt_number,
            )
        elif frame is None:
            report = D9CaptureReport.failure(
                D9ProcessRole.INNER_GENERATION_CHILD,
                D9StreamFailureCode.STREAM_FINALIZATION_FAILED,
                attempt_number=attempt_number,
            )
        else:
            report = D9CaptureReport(tuple(observations), tuple(failure_codes))
        if self.cleanup_failure is not None:
            raise QwenPermanentRuntimeError('generation cleanup failed')
        if self.on_d9_report is not None:
            self.on_d9_report(report)
        if worker_died:
            raise QwenPermanentRuntimeError('generation worker died before stream finalization')
        if frame is None:
            if deadline_expired:
                raise QwenTimeoutError
            if report.failed and self.on_d9_report is not None:
                raise QwenPermanentRuntimeError('D9 stream enforcement failed')
            raise QwenTimeoutError
        if report.failed:
            raise QwenPermanentRuntimeError('D9 stream enforcement failed')
        if decoded_failure is not None:
            raise decoded_failure
        assert decoded_raw_output is not None
        return decoded_raw_output

    @staticmethod
    def _drain_post_cleanup_d9(
        connection: BoundedConnection,
        observations: list[D9StreamObservation],
        failure_codes: list[D9StreamFailureCode],
        *,
        attempt_number: int,
        outcome_received: bool,
    ) -> bool:
        protocol_valid = True
        for _ in range(32):
            try:
                frame = connection.recv_frame(0.0)
            except Exception:  # noqa: BLE001 - post-cleanup transport detail is sanitized
                return False
            if frame is None:
                return protocol_valid
            if frame.get('kind') == 'D9_STREAM_OBSERVATION':
                observation = _d9_observation_from_frame(frame)
                if (
                    observation is None
                    or observation.process_role is not D9ProcessRole.INNER_GENERATION_CHILD
                    or observation.attempt_number != attempt_number
                    or observation.stream in {item.stream for item in observations}
                ):
                    protocol_valid = False
                    continue
                observations.append(observation)
                if outcome_received and not observation.failed:
                    protocol_valid = False
                if observation.failed:
                    assert observation.failure_code is not None
                    if observation.failure_code not in failure_codes:
                        failure_codes.append(observation.failure_code)
                continue
            if frame.get('kind') == 'D9_STREAM_FAILURE':
                code = _d9_failure_from_frame(frame)
                if code is None:
                    protocol_valid = False
                elif code not in failure_codes:
                    failure_codes.append(code)
                continue
            if frame.get('kind') == 'd9_failure':
                code = _d9_failure_from_frame(frame)
                if code is None:
                    protocol_valid = False
                elif code not in failure_codes:
                    failure_codes.append(code)
                continue
            protocol_valid = False
        try:
            return connection.recv_frame(0.0) is None and protocol_valid
        except Exception:  # noqa: BLE001 - post-cleanup transport detail is sanitized
            return False

def _interpret_generation_child_frame(frame: Mapping[str, object]) -> str:
    kind = frame.get("kind")
    if kind == 'd9_failure':
        raise QwenPermanentRuntimeError('D9 stream enforcement failed')
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
    d9_observations: tuple[D9StreamObservation, ...] = ()
    d9_failure_codes: tuple[D9StreamFailureCode, ...] = ()
    cleanup_failure: Feat018CleanupFailedError | None = field(
        default=None, repr=False, compare=False
    )
    verification_summary: DevAttemptVerificationV1 | None = None

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
        return (
            self.effective_outcome is EffectiveOutcome.SUCCEEDED
            and self.cleanup_failure is None
        )


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
    cleanup_deadline: Callable[[], float | None] | None = field(default=None, repr=False)
    on_cleanup_intent: Callable[[], float] | None = field(default=None, repr=False)
    cancel_requested: Callable[[], bool] | None = field(default=None, repr=False)
    on_accepted_progress: Callable[[ProgressEvent], None] | None = field(default=None, repr=False)
    require_verification: bool = False
    _verification_summary: DevAttemptVerificationV1 | None = field(default=None, init=False, repr=False)
    register_launch: Callable[[int, str, object | None], object] | None = field(default=None, repr=False)
    launch_parent_birth: object | None = field(default=None, repr=False)
    release_guard: Callable[[Callable[[], None]], None] | None = field(default=None, repr=False)
    _adapter_registration: object | None = field(default=None, init=False, repr=False)
    _terminal_cleanup_deadline: float | None = field(default=None, init=False, repr=False)
    _registered_generation_attempts: set[int] = field(default_factory=set, init=False, repr=False)
    work_deadline_monotonic: float | None = field(default=None, repr=False)

    def run(
        self, entry: Callable[..., None], worker_args: tuple[object, ...]
    ) -> SupervisorRunResult:
        self._verification_summary = None
        self._adapter_registration = None
        self._terminal_cleanup_deadline = None
        self._registered_generation_attempts.clear()
        cap_deadline_monotonic = self.clock() + self.config.total_adapter_cap_seconds
        if self.work_deadline_monotonic is not None:
            if type(self.work_deadline_monotonic) not in (int, float) or not math.isfinite(self.work_deadline_monotonic):
                return SupervisorRunResult(
                    final_state=ProgressState.NOT_STARTED, attempt_count=None, terminal_outcome=None,
                    cleanup_status=CleanupStatus.SUCCEEDED, stopped_before_containment=True,
                    primary_failure_reason='development work deadline invalid',
                )
            cap_deadline_monotonic = min(cap_deadline_monotonic, self.work_deadline_monotonic)
            if _positive_finite_float(cap_deadline_monotonic - self.clock()) is None:
                return SupervisorRunResult(
                    final_state=ProgressState.NOT_STARTED, attempt_count=None, terminal_outcome=None,
                    cleanup_status=CleanupStatus.SUCCEEDED, stopped_before_containment=True,
                    primary_failure_reason='development work deadline expired',
                )
        cleanup_deadline_monotonic: float | None = None
        cleanup_failures: list[Feat018CleanupFailedError] = []

        def begin_cleanup() -> float:
            nonlocal cleanup_deadline_monotonic
            if cleanup_deadline_monotonic is None:
                try:
                    cleanup_deadline_monotonic = _cleanup_deadline_from_hooks(
                        on_cleanup_intent=self.on_cleanup_intent,
                        cleanup_deadline=self.cleanup_deadline,
                    )
                    if cleanup_deadline_monotonic is None:
                        if self.on_cleanup_intent is not None or self.cleanup_deadline is not None:
                            raise Feat018CleanupFailedError('cleanup deadline grant was absent')
                        cleanup_deadline_monotonic = (
                            self.clock() + self.config.cleanup_deadline_seconds
                        )
                except Exception:  # noqa: BLE001 - an absent grant cannot reset the deadline
                    cleanup_deadline_monotonic = 0.0
                    cleanup_failures.append(Feat018CleanupFailedError())
            self._terminal_cleanup_deadline = cleanup_deadline_monotonic
            return cleanup_deadline_monotonic

        containment: ContainmentBackend | None = None
        try:
            containment = self.containment_factory()
            containment.create()
        except Exception:  # noqa: BLE001 - containment creation is fail-closed, never raised
            cleanup_status = self._cleanup_partial_containment(
                containment,
                cleanup_deadline_monotonic=begin_cleanup(),
                cleanup_failures=cleanup_failures,
            )
            if cleanup_failures:
                cleanup_status = CleanupStatus.CLEANUP_FAILED
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
                cleanup_failure=(
                    Feat018CleanupFailedError(owned_containments=(containment,))
                    if containment is not None and cleanup_status is CleanupStatus.CLEANUP_FAILED
                    else (cleanup_failures[0] if cleanup_failures else None)
                ),
            )
        assert containment is not None

        process: ProcessHandle | None = None
        connection: BoundedConnection | None = None
        stopped_before_containment = False
        primary_failure_reason: str | None = None
        state_machine = Feat018ProgressStateMachine(cap_deadline_monotonic=cap_deadline_monotonic)
        d9_observations: list[D9StreamObservation] = []
        d9_failure_codes: list[D9StreamFailureCode] = []
        d9_capture_expected = False
        worker_died_before_cleanup = False

        try:
            try:
                process, connection = self.launcher.launch(entry, worker_args)
            except Feat018CleanupFailedError as failure:
                stopped_before_containment = True
                primary_failure_reason = "adapter worker launch cleanup failed"
                cleanup_failures.append(failure)
                failure.retry_cleanup(
                    grace_seconds=1.0,
                    kill_join_seconds=1.0,
                    cleanup_deadline_monotonic=begin_cleanup(),
                    clock=self.clock,
                )
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
                    d9_capture_expected = True
                    progress_failure_reason = self._run_progress_loop(
                        process,
                        connection,
                        state_machine,
                        cap_deadline_monotonic,
                        d9_observations,
                        d9_failure_codes,
                        cleanup_failures,
                        begin_cleanup,
                    )
                    primary_failure_reason = primary_failure_reason or progress_failure_reason
                    try:
                        worker_died_before_cleanup = not process.is_alive()
                    except Exception:  # noqa: BLE001 - unknown liveness fails closed
                        worker_died_before_cleanup = True
        except Exception:  # noqa: BLE001 - any unforeseen lifecycle failure still cleans up
            primary_failure_reason = primary_failure_reason or "adapter worker lifecycle failure"
            state_machine.force_freeze()
        finally:
            cleanup_deadline_monotonic = begin_cleanup()
            cleanup_failed = bool(cleanup_failures)
            if process is not None and not _bounded_terminate_kill_join(
                process,
                grace_seconds=1.0,
                kill_join_seconds=1.0,
                cleanup_deadline_monotonic=cleanup_deadline_monotonic,
                clock=self.clock,
            ):
                cleanup_failed = True
                cleanup_failures.append(
                    Feat018CleanupFailedError(
                        owned_process=(
                            process if not bool(getattr(process, 'closed', False)) else None
                        )
                    )
                )
            containment_cleanup_failed = False
            try:
                _terminate_owned_containment(
                    containment,
                    cleanup_deadline_monotonic=cleanup_deadline_monotonic,
                    clock=self.clock,
                )
            except Exception:  # noqa: BLE001 - cleanup must continue and report failure
                cleanup_failed = True
                containment_cleanup_failed = True
            cleanup_status = self._verify_cleanup(
                containment, cleanup_deadline_monotonic=cleanup_deadline_monotonic
            )
            containment_cleanup_failed = (
                containment_cleanup_failed or cleanup_status is CleanupStatus.CLEANUP_FAILED
            )
            if cleanup_status is CleanupStatus.CLEANUP_FAILED:
                cleanup_failed = True
            if connection is not None:
                if d9_capture_expected:
                    post_cleanup_failure = self._drain_post_cleanup_d9(
                        connection,
                        state_machine,
                        d9_observations,
                        d9_failure_codes,
                        cleanup_failures,
                    )
                    primary_failure_reason = (
                        primary_failure_reason or post_cleanup_failure
                    )
                try:
                    connection.close()
                except Exception:  # noqa: BLE001 - containment close must still run
                    cleanup_failed = True
                    cleanup_failures.append(
                        Feat018CleanupFailedError(owned_connections=(connection,))
                    )
            try:
                _close_verified_empty_containment(containment)
            except Exception:  # noqa: BLE001 - cleanup failure is a result, not an escape
                cleanup_failed = True
                containment_cleanup_failed = True
            if bool(getattr(containment, "_cleanup_failed", False)):
                cleanup_failed = True
                containment_cleanup_failed = True
            if self.clock() >= cleanup_deadline_monotonic:
                cleanup_failed = True
                cleanup_failures.append(Feat018CleanupFailedError('cleanup deadline expired'))
            if containment_cleanup_failed:
                cleanup_failures.append(
                    Feat018CleanupFailedError(owned_containments=(containment,))
                )
            if cleanup_failed or cleanup_failures:
                cleanup_status = CleanupStatus.CLEANUP_FAILED

        if d9_capture_expected:
            _d9_fill_missing(
                d9_observations,
                d9_failure_codes,
                worker_died=(
                    worker_died_before_cleanup
                    and state_machine.state is not ProgressState.TERMINAL
                ),
                attempt_count=state_machine.attempt_count,
            )
            if d9_failure_codes or any(item.failed for item in d9_observations):
                primary_failure_reason = (
                    primary_failure_reason or 'D9 stream enforcement failed'
                )

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
            verification_summary=self._verification_summary,
            d9_observations=tuple(d9_observations),
            d9_failure_codes=tuple(d9_failure_codes),
            cleanup_failure=(
                Feat018CleanupFailedError(
                    owned_process=next(
                        (
                            failure.owned_process
                            for failure in cleanup_failures
                            if failure.owned_process is not None
                        ),
                        None,
                    ),
                    owned_connections=tuple(
                        connection
                        for failure in cleanup_failures
                        for connection in failure.owned_connections
                    ),
                    owned_containments=tuple(
                        owned_containment
                        for failure in cleanup_failures
                        for owned_containment in failure.owned_containments
                    ),
                )
                if cleanup_failures
                else None
            ),
        )

    def _establish_containment_gate(
        self,
        process: ProcessHandle,
        connection: BoundedConnection,
        containment: ContainmentBackend,
        cap_deadline_monotonic: float,
    ) -> _ContainmentGateResult:
        if self.cancel_requested is not None:
            try:
                requested = self.cancel_requested()
                if type(requested) is not bool or requested:
                    return _ContainmentGateResult(
                        contained=False, failure_reason="adapter invocation cancelled before gate"
                    )
            except Exception:
                return _ContainmentGateResult(
                    contained=False, failure_reason="adapter cancellation control failed"
                )

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

        if self.register_launch is not None:
            try:
                if type(process.pid) is not int or process.pid < 1:
                    raise ValueError
                self._adapter_registration = self.register_launch(
                    process.pid, 'ADAPTER', self.launch_parent_birth,
                )
                if getattr(self._adapter_registration, 'birth', None) is None:
                    raise ValueError
            except Exception:
                return _ContainmentGateResult(
                    contained=False, failure_reason="trusted adapter registration failed"
                )

        if self.cancel_requested is not None:
            try:
                requested = self.cancel_requested()
                if type(requested) is not bool or requested:
                    return _ContainmentGateResult(
                        contained=False, failure_reason="adapter invocation cancelled before release"
                    )
            except Exception:
                return _ContainmentGateResult(
                    contained=False, failure_reason="adapter cancellation control failed"
                )

        remaining_for_duration = cap_deadline_monotonic - self.clock()
        if _positive_finite_float(remaining_for_duration) is None:
            return _ContainmentGateResult(
                contained=False, failure_reason="containment gate deadline expired"
            )
        try:
            def release() -> None:
                # The guard owns the authoritative START/CANCEL lock. Polling the
                # control source here could recursively acquire that same lock.
                remaining = cap_deadline_monotonic - self.clock()
                if _positive_finite_float(remaining) is None:
                    raise Feat018ProtocolViolationError('adapter release deadline expired')
                connection.send_frame({
                    "kind": "CONTAINMENT_READY",
                    "remaining_seconds_at_spawn": remaining,
                })

            if self.release_guard is not None:
                self.release_guard(release)
            else:
                release()
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
        d9_observations: list[D9StreamObservation],
        d9_failure_codes: list[D9StreamFailureCode],
        cleanup_failures: list[Feat018CleanupFailedError],
        begin_cleanup: Callable[[], float] | None = None,
    ) -> str | None:
        while state_machine.state not in (ProgressState.TERMINAL, ProgressState.FROZEN):
            if self.cancel_requested is not None:
                try:
                    requested = self.cancel_requested()
                except Exception:
                    state_machine.force_freeze()
                    return "adapter cancellation control failed"
                if type(requested) is not bool or requested:
                    state_machine.force_freeze()
                    return "adapter invocation cancelled"
            effective_deadline = min(cap_deadline_monotonic, self._terminal_cleanup_deadline) if (
                self._terminal_cleanup_deadline is not None
            ) else cap_deadline_monotonic
            remaining = effective_deadline - self.clock()
            if _positive_finite_float(remaining) is None:
                state_machine.force_freeze()
                return "adapter supervisor deadline exceeded"
            try:
                raw_frame = connection.recv_frame(
                    min(remaining, self.config.poll_interval_seconds)
                    if self.cancel_requested is not None else remaining
                )
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
            if self.cancel_requested is not None:
                try:
                    requested = self.cancel_requested()
                except Exception:
                    requested = True
                if type(requested) is not bool or requested:
                    state_machine.force_freeze()
                    return "adapter invocation cancelled"
            if raw_frame is None:
                try:
                    worker_alive = process.is_alive()
                except Exception:  # noqa: BLE001 - liveness failure is fail-closed
                    state_machine.force_freeze()
                    return "adapter worker liveness check failed"
                if not worker_alive:
                    state_machine.force_freeze()
                    return "adapter worker exited before terminal event"
                remaining_after_receive = cap_deadline_monotonic - self.clock()
                if _positive_finite_float(remaining_after_receive) is None:
                    state_machine.force_freeze()
                    return "adapter supervisor deadline exceeded"
                self.sleep(min(self.config.poll_interval_seconds, remaining_after_receive))
                continue
            if raw_frame.get('kind') == 'GENERATION_CLEANUP_FAILED':
                state_machine.force_freeze()
                if set(raw_frame) != {'kind'}:
                    return 'malformed generation cleanup frame'
                cleanup_failures.append(Feat018CleanupFailedError('generation cleanup failed'))
                return 'generation cleanup failed'
            if (
                raw_frame.get('cleanup_failed') is True
                and _progress_event_from_frame(raw_frame) is not None
            ):
                cleanup_failures.append(Feat018CleanupFailedError('generation cleanup failed'))
            if _positive_finite_float(effective_deadline - acceptance_time) is None:
                state_machine.force_freeze()
                return "progress event arrived at or after the supervisor deadline"
            if raw_frame.get('kind') == 'DEV_REGISTER_GENERATION':
                if (
                    not self.require_verification or self.register_launch is None
                    or self._adapter_registration is None
                    or set(raw_frame) != {'kind', 'pid', 'attempt_number'}
                    or type(raw_frame.get('pid')) is not int or raw_frame['pid'] < 1
                    or type(raw_frame.get('attempt_number')) is not int
                    or raw_frame['attempt_number'] != state_machine.attempt_count
                    or raw_frame['attempt_number'] not in (1, 2)
                    or raw_frame['attempt_number'] in self._registered_generation_attempts
                    or self._terminal_cleanup_deadline is not None
                ):
                    state_machine.force_freeze()
                    return 'invalid development generation registration'
                try:
                    registration = self.register_launch(
                        raw_frame['pid'], 'GENERATION', getattr(self._adapter_registration, 'birth'),
                    )
                    if getattr(registration, 'birth', None) is None:
                        raise Feat018ProtocolViolationError('generation registration missing birth')

                    def release_generation() -> None:
                        if _positive_finite_float(cap_deadline_monotonic - self.clock()) is None:
                            raise Feat018ProtocolViolationError('generation release deadline expired')
                        connection.send_frame({'kind': 'DEV_REGISTERED'})

                    if self.release_guard is not None:
                        self.release_guard(release_generation)
                    else:
                        release_generation()
                    self._registered_generation_attempts.add(raw_frame['attempt_number'])
                except Exception:
                    state_machine.force_freeze()
                    return 'trusted generation registration failed'
                continue
            if raw_frame.get('kind') == 'DEV_CLEANUP_INTENT':
                if not self.require_verification or set(raw_frame) != {'kind'} or begin_cleanup is None:
                    state_machine.force_freeze()
                    return 'invalid development cleanup intent'
                deadline = begin_cleanup()
                try:
                    connection.send_frame({
                        'kind': 'DEV_CLEANUP_GRANT',
                        # These two processes share the bound session's OS monotonic clock;
                        # no host timestamp crosses the SSH boundary.
                        'deadline_remote_monotonic': deadline,
                    })
                except Exception:
                    state_machine.force_freeze()
                    return 'development cleanup grant delivery failed'
                continue
            if raw_frame.get('kind') == 'DEV_VERIFICATION':
                if (
                    not self.require_verification or self._verification_summary is not None
                    or set(raw_frame) != {'kind', 'summary'}
                    or state_machine.state in (ProgressState.NOT_STARTED, ProgressState.FROZEN)
                ):
                    state_machine.force_freeze()
                    return 'invalid development verification sequence'
                try:
                    self._verification_summary = DevAttemptVerificationV1.model_validate_json(
                        json.dumps(raw_frame['summary'], allow_nan=False)
                    ).revalidated()
                except Exception:
                    state_machine.force_freeze()
                    return 'invalid development verification metadata'
                continue
            if raw_frame.get('kind') == 'D9_STREAM_OBSERVATION':
                observation = _d9_observation_from_frame(raw_frame)
                if (
                    observation is None
                    or (
                        observation.attempt_number is not None
                        and observation.attempt_number > (state_machine.attempt_count or 0)
                    )
                    or not _d9_record_observation(d9_observations, observation)
                ):
                    state_machine.force_freeze()
                    return 'malformed D9 stream observation'
                if observation.failed and observation.failure_code not in d9_failure_codes:
                    assert observation.failure_code is not None
                    d9_failure_codes.append(observation.failure_code)
                if observation.failed:
                    state_machine.force_freeze()
                    return 'D9 stream enforcement failed'
                continue
            if raw_frame.get('kind') == 'D9_STREAM_FAILURE':
                code = _d9_failure_from_frame(raw_frame)
                if code is None:
                    state_machine.force_freeze()
                    return 'malformed D9 stream failure'
                if code not in d9_failure_codes:
                    d9_failure_codes.append(code)
                state_machine.force_freeze()
                return 'D9 stream enforcement failed'
            event = _progress_event_from_frame(raw_frame)
            if event is None:
                state_machine.force_freeze()
                return "malformed progress frame"
            if self._terminal_cleanup_deadline is not None and event.kind is ProgressEventKind.GENERATION_ATTEMPT_STARTED:
                state_machine.force_freeze()
                return 'generation start after terminal cleanup intent'
            if event.kind is ProgressEventKind.TERMINAL and self.require_verification:
                if self._verification_summary is None:
                    state_machine.force_freeze()
                    return 'development terminal omitted verification'
                if event.raw_status is not None and event.raw_status != self._verification_summary.raw_status:
                    state_machine.force_freeze()
                    return 'development terminal contradicts Raw verification'
                if event.outcome == 'SUCCEEDED' and (
                    self._verification_summary.raw_status != 'SUCCEEDED'
                    or self._verification_summary.failure_codes
                    or event.raw_status != 'SUCCEEDED'
                ):
                    state_machine.force_freeze()
                    return 'development terminal contradicts verification'
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
            if self.on_accepted_progress is not None:
                try:
                    self.on_accepted_progress(event)
                except Exception:
                    state_machine.force_freeze()
                    return 'accepted progress delivery failed'
        return None

    @staticmethod
    def _drain_post_cleanup_d9(
        connection: BoundedConnection,
        state_machine: Feat018ProgressStateMachine,
        d9_observations: list[D9StreamObservation],
        d9_failure_codes: list[D9StreamFailureCode],
        cleanup_failures: list[Feat018CleanupFailedError],
    ) -> str | None:
        failure_reason: str | None = None
        for _ in range(32):
            try:
                frame = connection.recv_frame(0.0)
            except Exception:  # noqa: BLE001 - post-cleanup transport detail is sanitized
                return failure_reason or 'post-cleanup D9 frame receive failed'
            if frame is None:
                return failure_reason
            if frame.get('kind') == 'GENERATION_CLEANUP_FAILED':
                if set(frame) != {'kind'}:
                    failure_reason = failure_reason or 'malformed generation cleanup frame'
                    continue
                cleanup_failures.append(Feat018CleanupFailedError('generation cleanup failed'))
                failure_reason = failure_reason or 'generation cleanup failed'
                continue
            if (
                frame.get('cleanup_failed') is True
                and _progress_event_from_frame(frame) is not None
            ):
                cleanup_failures.append(Feat018CleanupFailedError('generation cleanup failed'))
                failure_reason = failure_reason or 'generation cleanup failed'
                continue
            if frame.get('kind') == 'D9_STREAM_OBSERVATION':
                observation = _d9_observation_from_frame(frame)
                if (
                    observation is None
                    or (
                        observation.attempt_number is not None
                        and observation.attempt_number > (state_machine.attempt_count or 0)
                    )
                    or not _d9_record_observation(d9_observations, observation)
                ):
                    failure_reason = failure_reason or 'malformed D9 stream observation'
                    continue
                if (
                    state_machine.state is ProgressState.TERMINAL
                    and not observation.failed
                ):
                    failure_reason = failure_reason or 'D9 frame arrived after terminal event'
                if observation.failed:
                    assert observation.failure_code is not None
                    if observation.failure_code not in d9_failure_codes:
                        d9_failure_codes.append(observation.failure_code)
                    failure_reason = failure_reason or 'D9 stream enforcement failed'
                continue
            if frame.get('kind') == 'D9_STREAM_FAILURE':
                code = _d9_failure_from_frame(frame)
                if code is None:
                    failure_reason = failure_reason or 'malformed D9 stream failure'
                else:
                    if code not in d9_failure_codes:
                        d9_failure_codes.append(code)
                    failure_reason = failure_reason or 'D9 stream enforcement failed'
                continue
            failure_reason = failure_reason or 'unexpected post-cleanup progress frame'
        try:
            if connection.recv_frame(0.0) is not None:
                return failure_reason or 'post-cleanup D9 frame limit exceeded'
        except Exception:  # noqa: BLE001 - post-cleanup transport detail is sanitized
            return failure_reason or 'post-cleanup D9 frame receive failed'
        return failure_reason

    def _cleanup_partial_containment(
        self,
        containment: ContainmentBackend | None,
        *,
        cleanup_deadline_monotonic: float | None = None,
        cleanup_failures: list[Feat018CleanupFailedError] | None = None,
    ) -> CleanupStatus:
        """Release a containment object even when its own creation did not finish."""

        if containment is None:
            return CleanupStatus.SUCCEEDED
        if cleanup_deadline_monotonic is None:
            cleanup_deadline_monotonic = self.clock() + self.config.cleanup_deadline_seconds
        cleanup_failed = bool(getattr(containment, "_cleanup_failed", False))
        try:
            _terminate_owned_containment(
                containment,
                cleanup_deadline_monotonic=cleanup_deadline_monotonic,
                clock=self.clock,
            )
        except Exception:  # noqa: BLE001 - close is still mandatory
            cleanup_failed = True
        if self._verify_cleanup(
            containment, cleanup_deadline_monotonic=cleanup_deadline_monotonic
        ) is CleanupStatus.CLEANUP_FAILED:
            cleanup_failed = True
        try:
            _close_verified_empty_containment(containment)
        except Exception:  # noqa: BLE001 - report the cleanup failure
            cleanup_failed = True
        if bool(getattr(containment, "_cleanup_failed", False)):
            cleanup_failed = True
        if self.clock() >= cleanup_deadline_monotonic:
            cleanup_failed = True
        if cleanup_failed and cleanup_failures is not None:
            cleanup_failures.append(Feat018CleanupFailedError(owned_containments=(containment,)))
        return (
            CleanupStatus.CLEANUP_FAILED if cleanup_failed else CleanupStatus.SUCCEEDED
        )

    def _verify_cleanup(
        self,
        containment: ContainmentBackend,
        *,
        cleanup_deadline_monotonic: float | None = None,
    ) -> CleanupStatus:
        deadline = (
            self.clock() + self.config.cleanup_deadline_seconds
            if cleanup_deadline_monotonic is None
            else cleanup_deadline_monotonic
        )
        interval = min(self.config.poll_interval_seconds, 0.01)
        while True:
            if (
                cleanup_deadline_monotonic is not None
                and self.clock() >= deadline
            ):
                return CleanupStatus.CLEANUP_FAILED
            try:
                empty = containment.is_empty()
            except Exception:  # noqa: BLE001 - a failing query never reports empty
                return CleanupStatus.CLEANUP_FAILED
            if bool(getattr(containment, "_cleanup_failed", False)):
                return CleanupStatus.CLEANUP_FAILED
            if (
                cleanup_deadline_monotonic is not None
                and self.clock() >= deadline
            ):
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


def verify_dev_worker_results(
    result: object, *, request: VisionUnderstandingRequestV2, session_id: str,
    content_policy: ObservableContentPolicyV1,
) -> DevAttemptVerificationV1:
    """Validate actual worker objects and map once; return no observation bodies.

    The expected profile/catalog are the existing V2 catalog. This verifies the
    result's provenance declaration, not installed packages or GPU capabilities.
    Failures are fixed codes; upstream validation exceptions remain worker-local.
    """
    try:
        if type(request) is not VisionUnderstandingRequestV2:
            raise ValueError
        checked_request = VisionUnderstandingRequestV2.model_validate(
            request.model_dump(mode='python', warnings='error')
        )
        if type(result) not in (VisionUnderstandingSuccessV2, VisionUnderstandingFailureV2):
            raise ValueError
        checked = type(result).model_validate(result.model_dump(mode='python', warnings='error'))
        profile = vision_profile_catalog_v2().resolve(checked_request.requested_profile_id)
        source_ok = checked.source_image_ref == checked_request.source_image_ref
        correlation_ok = checked.correlation_id == checked_request.correlation_id
        provenance_ok = (
            checked.profile_id == profile.profile_id
            and checked.profile_catalog_hash == vision_profile_catalog_hash_v2(vision_profile_catalog_v2())
            and checked.content_policy_version == getattr(content_policy, 'content_policy_version', None)
            and checked.policy_match_view_version == getattr(content_policy, 'policy_match_view_version', None)
            and (checked.model_provenance is None or checked.model_provenance == profile.model_provenance)
        )
        if type(checked) is VisionUnderstandingSuccessV2:
            provenance_ok = provenance_ok and (
                checked.adapter_version == profile.adapter_version
                and checked.config_hash == vision_profile_config_hash_v2(profile)
                and checked.model_provenance == profile.model_provenance
            )
    except Exception:
        return DevAttemptVerificationV1(
            v2_status='INVALID', v2_schema_verified=False, failure_codes=('V2_INVALID',),
        )
    v2_fields = dict(
        v2_status=checked.status, v2_schema_verified=True,
        source_matched=source_ok, correlation_matched=correlation_ok,
        provenance_matched=provenance_ok,
    )
    if not source_ok or not correlation_ok or not provenance_ok:
        return DevAttemptVerificationV1(
            **v2_fields,
            failure_codes=('IDENTITY_MISMATCH',) if not source_ok or not correlation_ok
            else ('PROVENANCE_MISMATCH',),
        )
    try:
        if not _is_bounded_opaque_identifier(session_id):
            raise ValueError
        mapped = map_vision_result_to_raw(
            checked, session_id=session_id,
            expected_source_sha256=checked_request.source_image_ref.sha256,
            expected_correlation_id=checked_request.correlation_id,
        )
        if type(mapped) not in (RawUnderstandingSuccessV1, RawUnderstandingFailureV1):
            raise ValueError
        raw = type(mapped).model_validate(mapped.model_dump(mode='python', warnings='error'))
        if (
            raw.session_id != session_id or raw.source_image_ref != checked_request.source_image_ref
            or raw.correlation_id != checked_request.correlation_id
            or raw.gate_a_required is not True or raw.status != checked.status
        ):
            raise ValueError
        if checked.model_provenance is None:
            # Pre-load typed failures legitimately have no model provenance.
            if raw.provenance is not None:
                raise ValueError
        elif raw.provenance is None or (
            raw.provenance.upstream_contract != checked.contract_name
            or raw.provenance.upstream_contract_version != checked.contract_version
            or raw.provenance.profile_id != checked.profile_id
            or raw.provenance.profile_catalog_hash != checked.profile_catalog_hash
            or raw.provenance.model_provenance != checked.model_provenance
        ):
            raise ValueError
        if type(raw) is RawUnderstandingSuccessV1 and (
            raw.provenance.adapter_version != checked.adapter_version
            or raw.provenance.config_hash != checked.config_hash
            or raw.narration_status.value != 'NOT_SUPPLIED'
            or raw.asr_claims or raw.asr_failure is not None
        ):
            raise ValueError
    except Exception:
        return DevAttemptVerificationV1(
            **v2_fields, raw_status='INVALID', raw_schema_verified=False,
            failure_codes=('RAW_INVALID',),
        )
    return DevAttemptVerificationV1(
        **v2_fields, raw_status=raw.status, raw_schema_verified=True,
        gate_a_required=True,
        narration_status='NOT_SUPPLIED' if type(raw) is RawUnderstandingSuccessV1 else 'NOT_REACHED',
        failure_codes=() if raw.status == 'SUCCEEDED' else ('ADAPTER_FAILED',),
    )


def adapter_worker_entry(
    connection: BoundedConnection,
    request: VisionUnderstandingRequestV2,
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    config: Feat018BoundedRunnerConfig,
    session_id: str | None = None,
    verify_development_results: bool = False,
    *,
    generation_launcher: ProcessLauncher | None = None,
    self_contain: Callable[[], None] = posix_worker_self_contain,
    clock: Callable[[], float] = time.monotonic,
    capture_factory: D9CaptureFactory | None = None,
) -> None:
    """The real, gated adapter-worker process entry point (F3).

    The D9 capture factory is the first action, before any possible worker write. Then
    ``self_contain`` (real: :func:`posix_worker_self_contain`; on Windows containment is
    external, so the real function is a no-op there) runs before waiting for release. Nothing
    that could construct the adapter, generation runner, or generation child happens before a
    valid ``CONTAINMENT_READY`` frame is accepted: a missing, late, malformed, or oversized
    release frame leaves this function returning before that point, every time.
    """

    return _adapter_worker_entry_with_d9(
        connection,
        request,
        runtime_config,
        content_policy,
        prompt,
        config,
        session_id,
        verify_development_results,
        generation_launcher=generation_launcher,
        self_contain=self_contain,
        clock=clock,
        capture_factory=capture_factory or _default_d9_capture_factory,
    )

def _adapter_worker_entry_with_d9(
    connection: BoundedConnection,
    request: VisionUnderstandingRequestV2,
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    config: Feat018BoundedRunnerConfig,
    session_id: str | None,
    verify_development_results: bool = False,
    *,
    generation_launcher: ProcessLauncher | None,
    self_contain: Callable[[], None],
    clock: Callable[[], float],
    capture_factory: D9CaptureFactory,
) -> None:
    send_frame = _synchronized_frame_sender(connection.send_frame)

    def _notify_terminal_failure(code: D9StreamFailureCode) -> None:
        _try_send_d9_failure(send_frame, code)

    try:
        capture = capture_factory(
            D9ProcessRole.OUTER_ADAPTER_WORKER,
            None,
            config.stdout_max_bytes,
            config.stderr_max_bytes,
            _notify_terminal_failure,
        )
    except Exception:  # noqa: BLE001 - capture setup fails closed with typed metadata
        report = D9CaptureReport.failure(
            D9ProcessRole.OUTER_ADAPTER_WORKER,
            D9StreamFailureCode.STREAM_FINALIZATION_FAILED,
            attempt_number=None,
        )
        _try_send_d9_report(connection.send_frame, report)
        return

    terminal_ready = False
    protocol_failure = False
    outcome = 'FAILED'
    raw_status: str | None = None
    verification_summary: DevAttemptVerificationV1 | None = None
    runner: Feat018BoundedKillableQwenGenerationRunner | None = None
    cleanup_marker_sent = False

    def _publish_d9(report: D9CaptureReport) -> None:
        try:
            _send_d9_report(send_frame, report)
        except Exception:  # noqa: BLE001 - raw transport details never cross the seam
            raise Feat018ProtocolViolationError('worker D9 report send failed') from None

    try:
        self_contain()
        gate_deadline = clock() + config.containment_setup_timeout_seconds
        try:
            release = connection.recv_frame(config.containment_setup_timeout_seconds)
        except Feat018ProtocolViolationError:
            return
        except Exception:  # noqa: BLE001 - a broken gate never constructs the adapter
            return
        if not isinstance(release, Mapping):
            return
        if (
            set(release) != {'kind', 'remaining_seconds_at_spawn'}
            or release.get('kind') != 'CONTAINMENT_READY'
        ):
            return
        if _positive_finite_float(gate_deadline - clock()) is None:
            return
        remaining_seconds = _positive_finite_float(release.get('remaining_seconds_at_spawn'))
        if remaining_seconds is None:
            return
        worker_cap_deadline_monotonic = clock() + remaining_seconds
        if not math.isfinite(worker_cap_deadline_monotonic):
            return

        seq_state = {'value': 0}

        def _next_seq() -> int:
            seq_state['value'] += 1
            return seq_state['value']

        def _send(kind: str, **extra: object) -> None:
            try:
                send_frame({'seq': _next_seq(), 'kind': kind, **extra})
            except Exception:  # noqa: BLE001 - progress delivery is a typed protocol step
                raise Feat018ProtocolViolationError(
                    'worker progress event send failed'
                ) from None

        def _send_d9(report: D9CaptureReport) -> None:
            try:
                _send_d9_report(send_frame, report)
            except Exception:  # noqa: BLE001 - raw transport details never cross the seam
                raise Feat018ProtocolViolationError('worker D9 report send failed') from None

        _send('ADAPTER_STARTED')
        terminal_ready = True
        attempt_state = {'count': 0}
        attempt_event_send_failed = {'value': False}

        def _on_attempt_start() -> None:
            attempt_state['count'] += 1
            try:
                _send('GENERATION_ATTEMPT_STARTED', attempt_number=attempt_state['count'])
            except Feat018ProtocolViolationError:
                attempt_event_send_failed['value'] = True
                raise

        def _on_d9_report(report: D9CaptureReport) -> None:
            _send_d9(report)

        def _on_cleanup_failure(failure: Feat018CleanupFailedError) -> None:
            nonlocal cleanup_marker_sent
            del failure
            send_frame({'kind': 'GENERATION_CLEANUP_FAILED'})
            cleanup_marker_sent = True

        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=config,
            worker_cap_deadline_monotonic=worker_cap_deadline_monotonic,
            launcher=generation_launcher
            or MultiprocessingProcessLauncher(max_envelope_bytes=config.ipc_envelope_max_bytes),
            clock=clock,
            on_attempt_start=_on_attempt_start,
            on_d9_report=_on_d9_report,
            on_cleanup_failure=_on_cleanup_failure,
        )
        if verify_development_results:
            child_cleanup_deadline: float | None = None

            def child_cleanup_intent() -> float:
                nonlocal child_cleanup_deadline
                if child_cleanup_deadline is not None:
                    return child_cleanup_deadline
                send_frame({'kind': 'DEV_CLEANUP_INTENT'})
                grant = connection.recv_frame(config.cleanup_deadline_seconds)
                if not isinstance(grant, Mapping) or set(grant) != {
                    'kind', 'deadline_remote_monotonic'
                } or grant.get('kind') != 'DEV_CLEANUP_GRANT':
                    raise Feat018ProtocolViolationError('development cleanup grant unavailable')
                deadline = _positive_finite_float(grant.get('deadline_remote_monotonic'))
                if deadline is None or deadline <= clock():
                    raise Feat018ProtocolViolationError('development cleanup grant expired')
                child_cleanup_deadline = deadline
                return deadline

            runner.on_cleanup_intent = child_cleanup_intent
            runner.cleanup_deadline = lambda: child_cleanup_deadline

            def register_generation(process: ProcessHandle) -> None:
                if type(process.pid) is not int or process.pid < 1:
                    raise Feat018ProtocolViolationError('generation registration unavailable')
                send_frame({
                    'kind': 'DEV_REGISTER_GENERATION', 'pid': process.pid,
                    'attempt_number': attempt_state['count'],
                })
                grant = connection.recv_frame(min(config.containment_setup_timeout_seconds, remaining_seconds))
                if grant != {'kind': 'DEV_REGISTERED'} or clock() >= worker_cap_deadline_monotonic:
                    raise Feat018ProtocolViolationError('generation registration grant unavailable')

            runner.register_generation = register_generation
        adapter = QwenVisionAdapter(
            runtime_config,
            content_policy=content_policy,
            prompt=prompt,
            generation_runner=runner,
        )
        try:
            result = adapter.understand(request)
            if attempt_event_send_failed['value']:
                raise Feat018ProtocolViolationError('worker attempt event send failed')
            if runner.cleanup_failure is not None:
                outcome = 'FAILED'
                return
            outcome = 'SUCCEEDED' if isinstance(result, VisionUnderstandingSuccessV2) else 'FAILED'
            if verify_development_results:
                verification_summary = verify_dev_worker_results(
                    result, request=request, session_id=session_id or '', content_policy=content_policy,
                )
                outcome = 'SUCCEEDED' if verification_summary.raw_status == 'SUCCEEDED' else 'FAILED'
                raw_status = verification_summary.raw_status if verification_summary.raw_status in (
                    'SUCCEEDED', 'FAILED'
                ) else None
            elif session_id is not None:
                if not _is_bounded_opaque_identifier(session_id):
                    raise ValueError('session_id must be a bounded opaque identifier')
                mapped = map_vision_result_to_raw(
                    result,
                    session_id=session_id,
                    expected_source_sha256=request.source_image_ref.sha256,
                    expected_correlation_id=request.correlation_id,
                )
                raw_status = mapped.status
        except Feat018ProtocolViolationError:
            protocol_failure = True
            raise
        except Exception:  # noqa: BLE001 - adapter details never cross the seam
            if attempt_event_send_failed['value']:
                protocol_failure = True
                raise Feat018ProtocolViolationError(
                    'worker attempt event send failed'
                ) from None
            outcome = 'FAILED'
    except Feat018ProtocolViolationError:
        protocol_failure = True
        raise
    finally:
        try:
            capture.finalize()
            report = capture.verify_writer_quiescence()
        except Exception:  # noqa: BLE001 - finalization is typed and fail-closed
            report = D9CaptureReport.failure(
                D9ProcessRole.OUTER_ADAPTER_WORKER,
                D9StreamFailureCode.STREAM_FINALIZATION_FAILED,
                attempt_number=None,
            )
        if report.failed:
            outcome = 'FAILED'
            raw_status = None
        generation_cleanup_failed = runner is not None and runner.cleanup_failure is not None
        if generation_cleanup_failed:
            outcome = 'FAILED'
            raw_status = None
            if not cleanup_marker_sent:
                with contextlib.suppress(Exception):
                    send_frame({'kind': 'GENERATION_CLEANUP_FAILED'})
                    cleanup_marker_sent = True
        if not protocol_failure:
            _publish_d9(report)
        if terminal_ready and not protocol_failure:
            if verify_development_results:
                verification_summary = verification_summary or DevAttemptVerificationV1()
                send_frame({'kind': 'DEV_VERIFICATION', 'summary': verification_summary.model_dump(mode='json')})
            if generation_cleanup_failed:
                _send('TERMINAL', outcome='FAILED', cleanup_failed=True)
            elif raw_status is None:
                _send('TERMINAL', outcome=outcome)
            else:
                _send('TERMINAL', outcome=outcome, raw_status=raw_status)


def run_bounded_adapter_call(
    request: VisionUnderstandingRequestV2,
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    config: Feat018BoundedRunnerConfig,
    *,
    session_id: str | None = None,
    verify_development_results: bool = False,
    cancel_requested: Callable[[], bool] | None = None,
    on_accepted_progress: Callable[[ProgressEvent], None] | None = None,
    on_cleanup_intent: Callable[[], float] | None = None,
    cleanup_deadline: Callable[[], float | None] | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    register_launch: Callable[[int, str, object | None], object] | None = None,
    launch_parent_birth: object | None = None,
    release_guard: Callable[[Callable[[], None]], None] | None = None,
    work_deadline_monotonic: float | None = None,
) -> SupervisorRunResult:
    """The one real, production entry point for a live bounded adapter call (F3).

    Enforces the exact D1 attempt profile before constructing a launcher, then uses
    :func:`adapter_worker_entry` through :class:`Feat018AdapterCallSupervisor`, so a caller
    cannot bypass the containment gate by substituting an ungated entry through this function.
    Offline tests replace the launcher and supervisor constructors with local fakes.
    ``session_id`` is a bounded opaque bootstrap argument. Spawn multiprocessing may serialize
    it across the worker boundary, but it is never placed in progress/event frames or evidence
    payload bodies.
    """

    if session_id is not None and not _is_bounded_opaque_identifier(session_id):
        raise ValueError("session_id must be a bounded opaque identifier")
    if type(verify_development_results) is not bool:
        raise ValueError('development verification requires an exact boolean')
    if verify_development_results and (
        any(not callable(hook) for hook in (
            register_launch, release_guard, cancel_requested, on_cleanup_intent,
            cleanup_deadline, on_accepted_progress,
        )) or launch_parent_birth is None
        or session_id is None
    ):
        return SupervisorRunResult(
            final_state=ProgressState.NOT_STARTED, attempt_count=None, terminal_outcome=None,
            cleanup_status=CleanupStatus.SUCCEEDED, stopped_before_containment=True,
            primary_failure_reason='development invocation binding incomplete',
        )
    if not _is_live_attempt_profile_admissible(config):
        return SupervisorRunResult(
            final_state=ProgressState.NOT_STARTED,
            attempt_count=None,
            terminal_outcome=None,
            cleanup_status=CleanupStatus.SUCCEEDED,
            effective_outcome=EffectiveOutcome.FAILED,
            stopped_before_containment=True,
            primary_failure_reason="live attempt profile requires exactly 120 seconds",
        )
    launcher = MultiprocessingProcessLauncher(max_envelope_bytes=config.ipc_envelope_max_bytes)
    supervisor_options: dict[str, Any] = dict(
        config=config,
        launcher=launcher,
        containment_factory=create_platform_containment,
    )
    if verify_development_results or any(hook is not None for hook in (
        cancel_requested, on_accepted_progress, on_cleanup_intent, cleanup_deadline,
        register_launch, launch_parent_birth, release_guard,
    )) or clock is not time.monotonic or sleep is not time.sleep or work_deadline_monotonic is not None:
        supervisor_options.update(
            require_verification=verify_development_results,
            cancel_requested=cancel_requested, on_accepted_progress=on_accepted_progress,
            on_cleanup_intent=on_cleanup_intent, cleanup_deadline=cleanup_deadline,
            clock=clock, sleep=sleep,
            register_launch=register_launch, launch_parent_birth=launch_parent_birth,
            release_guard=release_guard,
            work_deadline_monotonic=work_deadline_monotonic,
        )
    supervisor = Feat018AdapterCallSupervisor(**supervisor_options)
    worker_args: tuple[object, ...] = (
        request, runtime_config, content_policy, prompt, config, session_id,
    )
    if verify_development_results:
        worker_args += (True,)
    return supervisor.run(
        adapter_worker_entry,
        worker_args,
    )


# --------------------------------------------------------------------------------------
# Host-side Lightning session provisioning coordinator
# --------------------------------------------------------------------------------------


class Feat018LiveSmokeFailureCode(StrEnum):
    """Closed failure tokens for the host-side session/adapter coordinator."""

    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    PREFLIGHT_MISSING = "PREFLIGHT_MISSING"
    PREFLIGHT_FAILED = "PREFLIGHT_FAILED"
    PREFLIGHT_NOT_AUTHORIZED = "PREFLIGHT_NOT_AUTHORIZED"
    FINALIZATION_MISSING = "FINALIZATION_MISSING"
    FINALIZATION_FAILED = "FINALIZATION_FAILED"
    CONTROLLER_MISSING = "CONTROLLER_MISSING"
    ADAPTER_CALL_MISSING = "ADAPTER_CALL_MISSING"
    PROVISION_TIMEOUT = "PROVISION_TIMEOUT"
    PROVISION_FAILED = "PROVISION_FAILED"
    PROVISION_FACTS_MISSING = "PROVISION_FACTS_MISSING"
    PLACEMENT_FACTS_MISSING = "PLACEMENT_FACTS_MISSING"
    PLACEMENT_MISMATCH = "PLACEMENT_MISMATCH"
    LIFECYCLE_FACTS_MISSING = "LIFECYCLE_FACTS_MISSING"
    LIFECYCLE_FACTS_INVALID = "LIFECYCLE_FACTS_INVALID"
    SESSION_IDENTITY_MISMATCH = "SESSION_IDENTITY_MISMATCH"
    READY_TIMEOUT = "READY_TIMEOUT"
    READY_FAILED = "READY_FAILED"
    READY_FACTS_MISSING = "READY_FACTS_MISSING"
    SESSION_NOT_READY = "SESSION_NOT_READY"
    GPU_MINUTE_BUDGET_EXCEEDED = "GPU_MINUTE_BUDGET_EXCEEDED"
    SESSION_TTL_EXCEEDED = "SESSION_TTL_EXCEEDED"
    ADAPTER_CAP_EXCEEDED = "ADAPTER_CAP_EXCEEDED"
    ADAPTER_CALL_FAILED = "ADAPTER_CALL_FAILED"
    ADAPTER_RESULT_INVALID = "ADAPTER_RESULT_INVALID"
    ADAPTER_FAILED = "ADAPTER_FAILED"
    ADAPTER_CLEANUP_FAILED = "ADAPTER_CLEANUP_FAILED"
    OPERATION_CANCELLATION_FAILED = "OPERATION_CANCELLATION_FAILED"
    SESSION_TERMINATION_TIMEOUT = "SESSION_TERMINATION_TIMEOUT"
    SESSION_TERMINATION_FAILED = "SESSION_TERMINATION_FAILED"
    SESSION_TERMINATION_CANCELLATION_FAILED = "SESSION_TERMINATION_CANCELLATION_FAILED"
    LIFECYCLE_WORKER_LAUNCH_FAILED = "LIFECYCLE_WORKER_LAUNCH_FAILED"
    LIFECYCLE_WORKER_DIED = "LIFECYCLE_WORKER_DIED"
    LIFECYCLE_PROTOCOL_FAILED = "LIFECYCLE_PROTOCOL_FAILED"
    LIFECYCLE_RESULT_INVALID = "LIFECYCLE_RESULT_INVALID"
    LIFECYCLE_CONTAINMENT_FAILED = "LIFECYCLE_CONTAINMENT_FAILED"
    LIFECYCLE_CLEANUP_FAILED = "LIFECYCLE_CLEANUP_FAILED"


class LightningSessionReadiness(StrEnum):
    """The only readiness value that can start the session TTL."""

    NOT_READY = "NOT_READY"
    SESSION_READY = "SESSION_READY"


_BOUNDED_FACT_ID_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
)


def _is_bounded_fact_token(value: object) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= _BOUNDED_OPAQUE_ID_MAX_LENGTH
        and all(character in _BOUNDED_FACT_ID_CHARACTERS for character in value)
    )


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _validate_non_negative_timestamp(value: object, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite non-negative timestamp")
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        raise ValueError(f"{label} must be a finite non-negative timestamp") from None
    if not math.isfinite(converted) or converted < 0:
        raise ValueError(f"{label} must be a finite non-negative timestamp")


def _timestamps_match(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-6)


def _add_finite_deadline(start: float, duration: float) -> float | None:
    try:
        deadline = float(start) + float(duration)
    except (OverflowError, ValueError):
        return None
    return deadline if math.isfinite(deadline) else None


@dataclass(frozen=True, slots=True)
class LightningPlacementFacts:
    """Provider-owned GPU and model/input placement facts."""

    gpu_sku: str
    device_index: int
    device_count: int
    vram_mib: int
    cuda_available: bool
    bf16_supported: bool
    single_device_visible: bool
    model_device_index: int
    input_device_index: int

    def __post_init__(self) -> None:
        if not _is_bounded_fact_token(self.gpu_sku):
            raise ValueError("gpu_sku must be a bounded fact token")
        for value, label in (
            (self.device_index, "device_index"),
            (self.device_count, "device_count"),
            (self.vram_mib, "vram_mib"),
            (self.model_device_index, "model_device_index"),
            (self.input_device_index, "input_device_index"),
        ):
            if type(value) is not int:
                raise ValueError(f"{label} must be an integer")
        if self.device_count <= 0 or self.vram_mib <= 0:
            raise ValueError("device_count and vram_mib must be positive")
        if not 0 <= self.device_index < self.device_count:
            raise ValueError("device_index must be within device_count")
        for value, label in (
            (self.model_device_index, "model_device_index"),
            (self.input_device_index, "input_device_index"),
        ):
            if not 0 <= value < self.device_count:
                raise ValueError(f"{label} must be within device_count")
        for value, label in (
            (self.cuda_available, "cuda_available"),
            (self.bf16_supported, "bf16_supported"),
            (self.single_device_visible, "single_device_visible"),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"{label} must be boolean")


@dataclass(frozen=True, slots=True)
class LightningSessionLifecycleFacts:
    """Controller-owned session identity, readiness, and TTL anchors."""

    session_identity: str
    session_ready_at_monotonic: float
    session_ttl_start_monotonic: float
    session_ttl_deadline_monotonic: float

    def __post_init__(self) -> None:
        if not _is_bounded_fact_token(self.session_identity):
            raise ValueError("session_identity must be a bounded fact token")
        _validate_non_negative_timestamp(
            self.session_ready_at_monotonic, "session_ready_at_monotonic"
        )
        _validate_non_negative_timestamp(
            self.session_ttl_start_monotonic, "session_ttl_start_monotonic"
        )
        _validate_non_negative_timestamp(
            self.session_ttl_deadline_monotonic, "session_ttl_deadline_monotonic"
        )
        if not _timestamps_match(
            self.session_ready_at_monotonic, self.session_ttl_start_monotonic
        ):
            raise ValueError("session TTL must start at session readiness")
        if self.session_ttl_deadline_monotonic <= self.session_ttl_start_monotonic:
            raise ValueError("session_ttl_deadline_monotonic must be after TTL start")


@dataclass(frozen=True, slots=True)
class LightningProvisionFacts:
    """Provider-owned facts returned after a bounded allocation attempt.

    ``gpu_minute_budget_start_monotonic`` is captured by the injected controller at its
    provider-confirmed allocation/billing point. The coordinator never substitutes the
    host's request-start time for this fact.
    """

    allocation_confirmed: bool
    gpu_minute_budget_start_monotonic: float | None
    session_identity: str
    placement: LightningPlacementFacts

    def __post_init__(self) -> None:
        if not isinstance(self.allocation_confirmed, bool):
            raise ValueError("allocation_confirmed must be boolean")
        if not _is_bounded_fact_token(self.session_identity):
            raise ValueError("session_identity must be a bounded fact token")
        if not isinstance(self.placement, LightningPlacementFacts):
            raise ValueError("placement facts are required")
        if self.gpu_minute_budget_start_monotonic is not None:
            value = self.gpu_minute_budget_start_monotonic
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not _is_finite_number(value)
                or value < 0
            ):
                raise ValueError(
                    "gpu_minute_budget_start_monotonic must be finite and non-negative"
                )


@dataclass(frozen=True, slots=True)
class LightningReadyFacts:
    """Provider-owned readiness state returned by a bounded readiness wait."""

    readiness: LightningSessionReadiness
    lifecycle: LightningSessionLifecycleFacts | None

    def __post_init__(self) -> None:
        if not isinstance(self.readiness, LightningSessionReadiness):
            raise ValueError("readiness must be a LightningSessionReadiness")
        if self.readiness is LightningSessionReadiness.SESSION_READY and not isinstance(
            self.lifecycle, LightningSessionLifecycleFacts
        ):
            raise ValueError("SESSION_READY requires lifecycle facts")
        if self.readiness is LightningSessionReadiness.NOT_READY and self.lifecycle is not None:
            raise ValueError("NOT_READY cannot carry lifecycle facts")


@dataclass(frozen=True, slots=True)
class LightningTerminationFacts:
    """Provider/controller proof that session termination was verified."""

    termination_verified: bool
    cleanup_status: CleanupStatus
    session_identity: str
    session_cleanup_verified: bool

    def __post_init__(self) -> None:
        if not isinstance(self.termination_verified, bool):
            raise ValueError("termination_verified must be boolean")
        if not isinstance(self.cleanup_status, CleanupStatus):
            raise ValueError("cleanup_status must be a CleanupStatus")
        if not _is_bounded_fact_token(self.session_identity):
            raise ValueError("session_identity must be a bounded fact token")
        if not isinstance(self.session_cleanup_verified, bool):
            raise ValueError("session_cleanup_verified must be boolean")


@dataclass(frozen=True, slots=True)
class LightningCancellationFacts:
    """Typed proof that a controller operation stopped its provider operation."""

    cancellation_verified: bool
    termination_facts: LightningTerminationFacts | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.cancellation_verified, bool):
            raise ValueError("cancellation_verified must be boolean")
        if self.termination_facts is not None and not isinstance(
            self.termination_facts, LightningTerminationFacts
        ):
            raise ValueError("termination_facts must be typed when supplied")


@dataclass(frozen=True, slots=True)
class LightningPlacementApproval:
    """Explicit D10 approval values used to validate provider placement facts."""

    gpu_sku: str
    device_index: int
    device_count: int
    minimum_vram_mib: int
    cuda_required: bool
    bf16_required: bool
    single_device_required: bool

    def __post_init__(self) -> None:
        if not _is_bounded_fact_token(self.gpu_sku):
            raise ValueError("gpu_sku must be a bounded fact token")
        for value, label in (
            (self.device_index, "device_index"),
            (self.device_count, "device_count"),
            (self.minimum_vram_mib, "minimum_vram_mib"),
        ):
            if type(value) is not int:
                raise ValueError(f"{label} must be an integer")
        if self.device_count <= 0 or self.minimum_vram_mib <= 0:
            raise ValueError("device_count and minimum_vram_mib must be positive")
        if not 0 <= self.device_index < self.device_count:
            raise ValueError("device_index must be within device_count")
        for value, label in (
            (self.cuda_required, "cuda_required"),
            (self.bf16_required, "bf16_required"),
            (self.single_device_required, "single_device_required"),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"{label} must be boolean")


@dataclass(frozen=True, slots=True)
class LightningPreflightFacts:
    """Validated proof that every pre-adapter approval gate has passed."""

    synthetic_session_id: str
    approval_identity_verified: bool
    checkout_identity_verified: bool
    d4_readiness_verified: bool
    fixture_digest_verified: bool
    prompt_hash_verified: bool
    hardware_placement_verified: bool
    policy_identity_verified: bool
    runtime_inventory_verified: bool

    def __post_init__(self) -> None:
        if not _is_bounded_opaque_identifier(self.synthetic_session_id):
            raise ValueError("synthetic_session_id must be a bounded opaque identifier")
        for value, label in (
            (self.approval_identity_verified, "approval_identity_verified"),
            (self.checkout_identity_verified, "checkout_identity_verified"),
            (self.d4_readiness_verified, "d4_readiness_verified"),
            (self.fixture_digest_verified, "fixture_digest_verified"),
            (self.prompt_hash_verified, "prompt_hash_verified"),
            (self.hardware_placement_verified, "hardware_placement_verified"),
            (self.policy_identity_verified, "policy_identity_verified"),
            (self.runtime_inventory_verified, "runtime_inventory_verified"),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"{label} must be boolean")


@dataclass(frozen=True, slots=True)
class LightningFinalizationFacts:
    """Typed proof that evidence finalization and sanitized incident handling ran."""

    finalization_verified: bool
    evidence_pair_verified: bool
    incident_handling_verified: bool

    def __post_init__(self) -> None:
        for value, label in (
            (self.finalization_verified, "finalization_verified"),
            (self.evidence_pair_verified, "evidence_pair_verified"),
            (self.incident_handling_verified, "incident_handling_verified"),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"{label} must be boolean")


T_co = TypeVar("T_co", covariant=True)


class LightningOperationHandle(Protocol[T_co]):
    """Non-blocking controller operation with independently bounded wait/cancel."""

    def wait(self, *, timeout_seconds: float) -> T_co: ...

    def cancel(self, *, timeout_seconds: float) -> LightningCancellationFacts: ...


class LightningPreflight(Protocol):
    """Host-side approval/checkout/inventory gate owned by the future live harness."""

    def verify(self, *, synthetic_session_id: str) -> LightningPreflightFacts: ...


class LightningSmokeFinalizer(Protocol):
    """Finalization seam that must delegate to ``finalize_smoke_run`` and incident handling."""

    def finalize(self, *, result: Feat018LiveSmokeResult) -> LightningFinalizationFacts: ...


class LightningSessionController(Protocol):
    """Non-blocking controller seam owned by the actual Lightning integration.

    Each method must return an operation handle promptly; the handle's ``wait`` and ``cancel``
    methods independently bound and stop the provider operation. The coordinator only trusts
    typed facts returned by the handle and its host monotonic clock. The controller owns provider
    session identity, lifecycle/TTL facts, placement, allocation/billing facts, and forced
    termination/cleanup. No provider implementation is imported by this module.
    """

    def provision(self) -> LightningOperationHandle[LightningProvisionFacts]: ...

    def wait_ready(self) -> LightningOperationHandle[LightningReadyFacts]: ...

    def terminate(self) -> LightningOperationHandle[LightningTerminationFacts]: ...


class BoundedAdapterCall(Protocol):
    """The unchanged ``run_bounded_adapter_call`` callable shape."""

    def __call__(
        self,
        request: VisionUnderstandingRequestV2,
        runtime_config: QwenVisionRuntimeConfig,
        content_policy: ObservableContentPolicyV1,
        prompt: str,
        config: Feat018BoundedRunnerConfig,
        *,
        session_id: str | None = None,
    ) -> SupervisorRunResult: ...


def _positive_finite_integer(value: object, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} must be a positive finite integer")
    return value


@dataclass(frozen=True, slots=True)
class Feat018LiveSmokeConfig:
    """Explicit host-side session budgets around one unchanged bounded adapter call."""

    bounded_runner_config: Feat018BoundedRunnerConfig
    session_provision_timeout_seconds: int
    session_ttl_seconds: int
    gpu_minute_cap: int
    session_termination_deadline_seconds: int
    placement_approval: LightningPlacementApproval

    def __post_init__(self) -> None:
        if not isinstance(self.bounded_runner_config, Feat018BoundedRunnerConfig):
            raise ValueError("bounded_runner_config is required")
        _positive_finite_integer(
            self.session_provision_timeout_seconds, "session_provision_timeout_seconds"
        )
        _positive_finite_integer(self.session_ttl_seconds, "session_ttl_seconds")
        _positive_finite_integer(self.gpu_minute_cap, "gpu_minute_cap")
        _positive_finite_integer(
            self.session_termination_deadline_seconds,
            "session_termination_deadline_seconds",
        )
        if not isinstance(self.placement_approval, LightningPlacementApproval):
            raise ValueError("placement_approval is required")


@dataclass(frozen=True, slots=True)
class Feat018LiveSmokeResult:
    """Truthful host-side result with no fabricated pre-ready session facts."""

    effective_outcome: EffectiveOutcome
    adapter_call_count: int
    attempt_count: int | None
    cleanup_status: CleanupStatus
    failure_code: Feat018LiveSmokeFailureCode | None = None
    session_ready: bool = False
    provision_start_monotonic: float | None = None
    ready_deadline_monotonic: float | None = None
    gpu_minute_budget_start_monotonic: float | None = None
    ready_at_monotonic: float | None = None
    session_ttl_start_monotonic: float | None = None
    session_ttl_deadline_monotonic: float | None = None
    adapter_start_monotonic: float | None = None
    total_adapter_cap_deadline_monotonic: float | None = None
    session_termination_deadline_monotonic: float | None = None
    adapter_result: SupervisorRunResult | None = None
    session_identity: str | None = None
    session_ready_at_monotonic: float | None = None
    placement: LightningPlacementFacts | None = None
    cleanup_failures: tuple[Feat018CleanupFailedError, ...] = field(
        default=(), repr=False, compare=False
    )
    preflight_verified: bool = False
    finalization_verified: bool = False
    d11_report: D11CleanupReport | None = field(default=None, repr=False)

    @property
    def is_success(self) -> bool:
        return (
            self.effective_outcome is EffectiveOutcome.SUCCEEDED
            and self.preflight_verified
            and self.finalization_verified
            and not self.cleanup_failures
            and (self.d11_report is None or self.d11_report.resources_released)
        )


def _termination_was_verified(value: object) -> bool:
    return (
        isinstance(value, LightningTerminationFacts)
        and value.termination_verified is True
        and value.cleanup_status is CleanupStatus.SUCCEEDED
        and value.session_cleanup_verified is True
    )


def _termination_matches_session(value: object, session_identity: str | None) -> bool:
    return _termination_was_verified(value) and (
        session_identity is None
        or (
            isinstance(value, LightningTerminationFacts)
            and value.session_identity == session_identity
        )
    )


def _termination_cancellation_was_verified(
    value: object, session_identity: str | None
) -> bool:
    return (
        isinstance(value, LightningCancellationFacts)
        and value.cancellation_verified is True
        and _termination_matches_session(value.termination_facts, session_identity)
    )


def _preflight_was_verified(value: object, synthetic_session_id: str) -> bool:
    if not isinstance(value, LightningPreflightFacts):
        return False
    if value.synthetic_session_id != synthetic_session_id:
        return False
    return all(
        value_field is True
        for value_field in (
            value.approval_identity_verified,
            value.checkout_identity_verified,
            value.d4_readiness_verified,
            value.fixture_digest_verified,
            value.prompt_hash_verified,
            value.hardware_placement_verified,
            value.policy_identity_verified,
            value.runtime_inventory_verified,
        )
    )


def _placement_matches_approval(
    value: object, approval: LightningPlacementApproval
) -> bool:
    if not isinstance(value, LightningPlacementFacts):
        return False
    return (
        value.gpu_sku == approval.gpu_sku
        and value.device_index == approval.device_index
        and value.device_count == approval.device_count
        and value.vram_mib >= approval.minimum_vram_mib
        and (not approval.cuda_required or value.cuda_available)
        and (not approval.bf16_required or value.bf16_supported)
        and (not approval.single_device_required or value.single_device_visible)
        and value.model_device_index == approval.device_index
        and value.input_device_index == approval.device_index
    )


def _lifecycle_failure_code(
    value: object,
    *,
    provision_facts: LightningProvisionFacts,
    provision_start: float,
    ready_finished: float,
    ready_deadline: float,
    session_ttl_seconds: int,
) -> Feat018LiveSmokeFailureCode | None:
    if not isinstance(value, LightningSessionLifecycleFacts):
        return Feat018LiveSmokeFailureCode.LIFECYCLE_FACTS_MISSING
    if value.session_identity != provision_facts.session_identity:
        return Feat018LiveSmokeFailureCode.SESSION_IDENTITY_MISMATCH
    if not (
        provision_start <= value.session_ready_at_monotonic <= ready_finished
        and value.session_ready_at_monotonic < ready_deadline
    ):
        return Feat018LiveSmokeFailureCode.LIFECYCLE_FACTS_INVALID
    expected_ttl_deadline = _add_finite_deadline(
        value.session_ttl_start_monotonic, float(session_ttl_seconds)
    )
    if expected_ttl_deadline is None or not _timestamps_match(
        expected_ttl_deadline, value.session_ttl_deadline_monotonic
    ):
        return Feat018LiveSmokeFailureCode.LIFECYCLE_FACTS_INVALID
    return None


def _active_cap_failure_code(
    now: float, *, ttl_deadline: float, gpu_budget_deadline: float
) -> Feat018LiveSmokeFailureCode | None:
    if now >= ttl_deadline:
        return Feat018LiveSmokeFailureCode.SESSION_TTL_EXCEEDED
    if now >= gpu_budget_deadline:
        return Feat018LiveSmokeFailureCode.GPU_MINUTE_BUDGET_EXCEEDED
    return None


LightningLifecycleOperationName = Literal["provision", "wait_ready", "terminate"]


class Feat018LifecycleOperationError(Exception):
    """A sanitized, typed result from the host-side lifecycle process boundary."""

    def __init__(
        self,
        failure_code: Feat018LiveSmokeFailureCode,
        *,
        cleanup_status: CleanupStatus = CleanupStatus.SUCCEEDED,
        cleanup_failure: Feat018CleanupFailedError | None = None,
    ) -> None:
        super().__init__(failure_code.value)
        self.failure_code = failure_code
        self.cleanup_status = (
            CleanupStatus.CLEANUP_FAILED if cleanup_failure is not None else cleanup_status
        )
        self.cleanup_failure = cleanup_failure


class LightningLifecycleBoundary(Protocol):
    """Host-enforceable boundary for one controller lifecycle operation."""

    def invoke(
        self,
        operation: LightningLifecycleOperationName,
        *,
        deadline: float,
        cancellation_deadline: float,
        session_identity: str | None = None,
    ) -> object: ...


def _lifecycle_timeout_code(
    operation: LightningLifecycleOperationName,
) -> Feat018LiveSmokeFailureCode:
    return {
        "provision": Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT,
        "wait_ready": Feat018LiveSmokeFailureCode.READY_TIMEOUT,
        "terminate": Feat018LiveSmokeFailureCode.SESSION_TERMINATION_TIMEOUT,
    }[operation]


def _lifecycle_failed_code(
    operation: LightningLifecycleOperationName,
) -> Feat018LiveSmokeFailureCode:
    return {
        "provision": Feat018LiveSmokeFailureCode.PROVISION_FAILED,
        "wait_ready": Feat018LiveSmokeFailureCode.READY_FAILED,
        "terminate": Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED,
    }[operation]


def _lifecycle_cancellation_failed_code(
    operation: LightningLifecycleOperationName,
) -> Feat018LiveSmokeFailureCode:
    if operation == "terminate":
        return Feat018LiveSmokeFailureCode.SESSION_TERMINATION_CANCELLATION_FAILED
    return Feat018LiveSmokeFailureCode.OPERATION_CANCELLATION_FAILED


def _lifecycle_worker_dead_code(
    operation: LightningLifecycleOperationName,
) -> Feat018LiveSmokeFailureCode:
    if operation == "terminate":
        return Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED
    return Feat018LiveSmokeFailureCode.LIFECYCLE_WORKER_DIED


def _payload_mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        return None
    return cast(Mapping[str, object], value)


def _payload_has_exact_keys(value: Mapping[str, object], keys: set[str]) -> bool:
    return set(value) == keys


def _placement_to_payload(value: LightningPlacementFacts) -> dict[str, object]:
    return {
        "fact_type": "placement",
        "gpu_sku": value.gpu_sku,
        "device_index": value.device_index,
        "device_count": value.device_count,
        "vram_mib": value.vram_mib,
        "cuda_available": value.cuda_available,
        "bf16_supported": value.bf16_supported,
        "single_device_visible": value.single_device_visible,
        "model_device_index": value.model_device_index,
        "input_device_index": value.input_device_index,
    }


def _termination_to_payload(value: LightningTerminationFacts) -> dict[str, object]:
    return {
        "fact_type": "termination",
        "termination_verified": value.termination_verified,
        "cleanup_status": value.cleanup_status.value,
        "session_identity": value.session_identity,
        "session_cleanup_verified": value.session_cleanup_verified,
    }


def _lightning_fact_to_payload(value: object) -> dict[str, object] | None:
    """Serialize only the closed typed lifecycle fact set across bounded JSON IPC."""

    if isinstance(value, LightningPlacementFacts):
        return _placement_to_payload(value)
    if isinstance(value, LightningProvisionFacts):
        return {
            "fact_type": "provision",
            "allocation_confirmed": value.allocation_confirmed,
            "gpu_minute_budget_start_monotonic": value.gpu_minute_budget_start_monotonic,
            "session_identity": value.session_identity,
            "placement": _placement_to_payload(value.placement),
        }
    if isinstance(value, LightningSessionLifecycleFacts):
        return {
            "fact_type": "lifecycle",
            "session_identity": value.session_identity,
            "session_ready_at_monotonic": value.session_ready_at_monotonic,
            "session_ttl_start_monotonic": value.session_ttl_start_monotonic,
            "session_ttl_deadline_monotonic": value.session_ttl_deadline_monotonic,
        }
    if isinstance(value, LightningReadyFacts):
        return {
            "fact_type": "ready",
            "readiness": value.readiness.value,
            "lifecycle": (
                None
                if value.lifecycle is None
                else _lightning_fact_to_payload(value.lifecycle)
            ),
        }
    if isinstance(value, LightningTerminationFacts):
        return _termination_to_payload(value)
    if isinstance(value, LightningCancellationFacts):
        return {
            "fact_type": "cancellation",
            "cancellation_verified": value.cancellation_verified,
            "termination_facts": (
                None
                if value.termination_facts is None
                else _termination_to_payload(value.termination_facts)
            ),
        }
    return None


def _lightning_fact_from_payload(value: object) -> object | None:
    """Deserialize and revalidate every typed fact received from a lifecycle worker."""

    payload = _payload_mapping(value)
    if payload is None:
        return None
    fact_type = payload.get("fact_type")
    try:
        if fact_type == "placement":
            if not _payload_has_exact_keys(
                payload,
                {
                    "fact_type",
                    "gpu_sku",
                    "device_index",
                    "device_count",
                    "vram_mib",
                    "cuda_available",
                    "bf16_supported",
                    "single_device_visible",
                    "model_device_index",
                    "input_device_index",
                },
            ):
                return None
            return LightningPlacementFacts(
                gpu_sku=payload["gpu_sku"],  # type: ignore[arg-type]
                device_index=payload["device_index"],  # type: ignore[arg-type]
                device_count=payload["device_count"],  # type: ignore[arg-type]
                vram_mib=payload["vram_mib"],  # type: ignore[arg-type]
                cuda_available=payload["cuda_available"],  # type: ignore[arg-type]
                bf16_supported=payload["bf16_supported"],  # type: ignore[arg-type]
                single_device_visible=payload["single_device_visible"],  # type: ignore[arg-type]
                model_device_index=payload["model_device_index"],  # type: ignore[arg-type]
                input_device_index=payload["input_device_index"],  # type: ignore[arg-type]
            )
        if fact_type == "provision":
            if not _payload_has_exact_keys(
                payload,
                {
                    "fact_type",
                    "allocation_confirmed",
                    "gpu_minute_budget_start_monotonic",
                    "session_identity",
                    "placement",
                },
            ):
                return None
            placement = _lightning_fact_from_payload(payload["placement"])
            if not isinstance(placement, LightningPlacementFacts):
                return None
            return LightningProvisionFacts(
                allocation_confirmed=payload["allocation_confirmed"],  # type: ignore[arg-type]
                gpu_minute_budget_start_monotonic=payload[
                    "gpu_minute_budget_start_monotonic"
                ],  # type: ignore[arg-type]
                session_identity=payload["session_identity"],  # type: ignore[arg-type]
                placement=placement,
            )
        if fact_type == "lifecycle":
            if not _payload_has_exact_keys(
                payload,
                {
                    "fact_type",
                    "session_identity",
                    "session_ready_at_monotonic",
                    "session_ttl_start_monotonic",
                    "session_ttl_deadline_monotonic",
                },
            ):
                return None
            return LightningSessionLifecycleFacts(
                session_identity=payload["session_identity"],  # type: ignore[arg-type]
                session_ready_at_monotonic=payload["session_ready_at_monotonic"],  # type: ignore[arg-type]
                session_ttl_start_monotonic=payload["session_ttl_start_monotonic"],  # type: ignore[arg-type]
                session_ttl_deadline_monotonic=payload["session_ttl_deadline_monotonic"],  # type: ignore[arg-type]
            )
        if fact_type == "ready":
            if not _payload_has_exact_keys(payload, {"fact_type", "readiness", "lifecycle"}):
                return None
            lifecycle_payload = payload["lifecycle"]
            lifecycle = (
                None
                if lifecycle_payload is None
                else _lightning_fact_from_payload(lifecycle_payload)
            )
            if lifecycle is not None and not isinstance(
                lifecycle, LightningSessionLifecycleFacts
            ):
                return None
            return LightningReadyFacts(
                readiness=LightningSessionReadiness(payload["readiness"]),  # type: ignore[arg-type]
                lifecycle=lifecycle,
            )
        if fact_type == "termination":
            if not _payload_has_exact_keys(
                payload,
                {
                    "fact_type",
                    "termination_verified",
                    "cleanup_status",
                    "session_identity",
                    "session_cleanup_verified",
                },
            ):
                return None
            return LightningTerminationFacts(
                termination_verified=payload["termination_verified"],  # type: ignore[arg-type]
                cleanup_status=CleanupStatus(payload["cleanup_status"]),  # type: ignore[arg-type]
                session_identity=payload["session_identity"],  # type: ignore[arg-type]
                session_cleanup_verified=payload["session_cleanup_verified"],  # type: ignore[arg-type]
            )
        if fact_type == "cancellation":
            if not _payload_has_exact_keys(
                payload, {"fact_type", "cancellation_verified", "termination_facts"}
            ):
                return None
            termination_payload = payload["termination_facts"]
            termination = (
                None
                if termination_payload is None
                else _lightning_fact_from_payload(termination_payload)
            )
            if termination is not None and not isinstance(
                termination, LightningTerminationFacts
            ):
                return None
            return LightningCancellationFacts(
                cancellation_verified=payload["cancellation_verified"],  # type: ignore[arg-type]
                termination_facts=termination,
            )
    except (TypeError, ValueError):
        return None
    return None


def _send_lifecycle_frame(
    connection: BoundedConnection, payload: Mapping[str, object]
) -> bool:
    try:
        connection.send_frame(payload)
    except Exception:  # noqa: BLE001 - worker failure is reported by bounded process death
        return False
    return True


def _lightning_lifecycle_worker_entry(
    connection: BoundedConnection,
    controller: LightningSessionController,
    operation: LightningLifecycleOperationName,
    wait_timeout_seconds: float,
    cancel_timeout_seconds: float,
    gate_timeout_seconds: float,
) -> None:
    """Invoke one controller operation behind the externally killable process boundary."""

    posix_worker_self_contain()
    try:
        release = connection.recv_frame(gate_timeout_seconds)
    except Exception:  # noqa: BLE001 - a failed gate never invokes the controller
        return
    if not isinstance(release, Mapping) or not _payload_has_exact_keys(
        cast(Mapping[str, object], release), {"kind", "remaining_seconds_at_spawn"}
    ):
        return
    if release.get("kind") != "CONTAINMENT_READY" or _positive_finite_float(
        release.get("remaining_seconds_at_spawn")
    ) is None:
        return

    if operation not in ("provision", "wait_ready", "terminate"):
        _send_lifecycle_frame(
            connection,
            {
                "kind": "LIFECYCLE_OPERATION_FAILED",
                "failure_kind": "call_failed",
                "cancellation": None,
            },
        )
        return
    if not _send_lifecycle_frame(connection, {"kind": "LIFECYCLE_CALL_STARTED"}):
        return

    operation_handle: object | None = None
    try:
        method = getattr(controller, operation)
        operation_handle = method()
        wait_method = cast(LightningOperationHandle[object], operation_handle).wait
    except Exception:  # noqa: BLE001 - controller/provider details stay out of IPC
        _send_lifecycle_frame(
            connection,
            {
                "kind": "LIFECYCLE_OPERATION_FAILED",
                "failure_kind": "call_failed",
                "cancellation": None,
            },
        )
        return

    if not _send_lifecycle_frame(connection, {"kind": "LIFECYCLE_WAIT_STARTED"}):
        return
    failure_kind = "failed"
    try:
        result = wait_method(timeout_seconds=wait_timeout_seconds)
    except TimeoutError:
        failure_kind = "timeout"
    except Exception:  # noqa: BLE001 - controller/provider details stay out of IPC
        failure_kind = "failed"
    else:
        payload = _lightning_fact_to_payload(result)
        _send_lifecycle_frame(
            connection,
            {
                "kind": "LIFECYCLE_OPERATION_RESULT",
                "fact": payload or {"fact_type": "unknown"},
            },
        )
        return

    try:
        cancel_method = cast(LightningOperationHandle[object], operation_handle).cancel
    except Exception:  # noqa: BLE001 - cancellation proof must be explicit
        cancel_method = None
    if not _send_lifecycle_frame(connection, {"kind": "LIFECYCLE_CANCEL_STARTED"}):
        return
    cancellation_payload: dict[str, object] | None = None
    if cancel_method is not None and _positive_finite_float(cancel_timeout_seconds) is not None:
        try:
            cancellation = cancel_method(timeout_seconds=cancel_timeout_seconds)
        except Exception:  # noqa: BLE001 - cancellation details stay out of IPC
            cancellation = None
        cancellation_payload = _lightning_fact_to_payload(cancellation)
    _send_lifecycle_frame(
        connection,
        {
            "kind": "LIFECYCLE_OPERATION_FAILED",
            "failure_kind": failure_kind
            if cancellation_payload is not None
            else "cancel_failed",
            "cancellation": cancellation_payload,
        },
    )


@dataclass(slots=True)
class Feat018LightningLifecycleProcessBoundary:
    """Run each controller lifecycle call in a killable, contained worker process.

    The controller and its operation handle never execute in the coordinator process. The
    coordinator's host clock bounds the receive loop; if ``controller.*``, ``operation.wait()``,
    or ``operation.cancel()`` ignores its timeout and never returns, the parent terminates and
    kills this worker and asks the same OS containment primitive to remove all descendants.
    """

    controller: LightningSessionController
    max_envelope_bytes: int
    containment_factory: Callable[[], ContainmentBackend]
    cleanup_deadline_seconds: float = 5.0
    containment_setup_timeout_seconds: float = 5.0
    confirmation_retry_interval_seconds: float = 0.02
    launcher: ProcessLauncher | None = field(default=None, repr=False)
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    sleep: Callable[[float], None] = field(default=time.sleep, repr=False)

    def invoke_reference(
        self,
        operation: LightningOperationRefV1,
        context: D11OperationContext,
        *,
        inputs: D11DispatchInputs | None = None,
        on_progress: Callable[[Mapping[str, object]], None] | None = None,
        window: D11CleanupWindow,
    ) -> D11OperationReceipt | D11ResourceObservation:
        return _invoke_d11_operation(self, operation, context, inputs, on_progress, window)

    def __post_init__(self) -> None:
        if type(self.max_envelope_bytes) is not int or self.max_envelope_bytes <= 0:
            raise ValueError("max_envelope_bytes must be a positive integer")
        for value, label in (
            (self.cleanup_deadline_seconds, "cleanup_deadline_seconds"),
            (self.containment_setup_timeout_seconds, "containment_setup_timeout_seconds"),
            (self.confirmation_retry_interval_seconds, "confirmation_retry_interval_seconds"),
        ):
            if _positive_finite_float(value) is None:
                raise ValueError(f"{label} must be positive and finite")

    def invoke(
        self,
        operation: LightningLifecycleOperationName,
        *,
        deadline: float,
        cancellation_deadline: float,
        session_identity: str | None = None,
    ) -> object:
        if operation not in ("provision", "wait_ready", "terminate"):
            raise Feat018LifecycleOperationError(
                Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
            )
        if session_identity is not None and not _is_bounded_fact_token(session_identity):
            raise Feat018LifecycleOperationError(
                Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
            )

        failure: Feat018LifecycleOperationError | None = None
        result: object | None = None
        result_received = False
        containment: ContainmentBackend | None = None
        process: ProcessHandle | None = None
        connection: BoundedConnection | None = None
        phase = "call"
        active_deadline = deadline
        launch_cleanup_failure: Feat018CleanupFailedError | None = None

        try:
            started = self.clock()
            if _positive_finite_float(deadline - started) is None:
                failure = Feat018LifecycleOperationError(_lifecycle_timeout_code(operation))
            elif _positive_finite_float(cancellation_deadline - started) is None:
                failure = Feat018LifecycleOperationError(
                    _lifecycle_cancellation_failed_code(operation)
                )
            else:
                try:
                    containment = self.containment_factory()
                    containment.create()
                except Exception:  # noqa: BLE001 - containment is a typed fail-closed gate
                    failure = Feat018LifecycleOperationError(
                        Feat018LiveSmokeFailureCode.LIFECYCLE_CONTAINMENT_FAILED,
                        cleanup_status=CleanupStatus.CLEANUP_FAILED,
                    )
                else:
                    remaining = _positive_finite_float(deadline - self.clock())
                    if remaining is None:
                        failure = Feat018LifecycleOperationError(
                            _lifecycle_timeout_code(operation)
                        )
                    else:
                        launcher = self.launcher or MultiprocessingProcessLauncher(
                            max_envelope_bytes=self.max_envelope_bytes
                        )
                        process, connection = launcher.launch(
                            _lightning_lifecycle_worker_entry,
                            (
                                self.controller,
                                operation,
                                remaining,
                                max(0.0, cancellation_deadline - self.clock()),
                                min(self.containment_setup_timeout_seconds, remaining),
                            ),
                        )
                        gate_remaining = _positive_finite_float(deadline - self.clock())
                        if gate_remaining is None:
                            failure = Feat018LifecycleOperationError(
                                _lifecycle_timeout_code(operation)
                            )
                        else:
                            try:
                                contained = containment.confirm_worker_contained(
                                    process,
                                    timeout=min(
                                        self.containment_setup_timeout_seconds, gate_remaining
                                    ),
                                    retry_interval=self.confirmation_retry_interval_seconds,
                                )
                            except Exception:  # noqa: BLE001 - fail closed
                                contained = False
                            if not contained:
                                failure = Feat018LifecycleOperationError(
                                    Feat018LiveSmokeFailureCode.LIFECYCLE_CONTAINMENT_FAILED,
                                    cleanup_status=CleanupStatus.CLEANUP_FAILED,
                                )
                            else:
                                release_remaining = _positive_finite_float(
                                    deadline - self.clock()
                                )
                                if release_remaining is None:
                                    failure = Feat018LifecycleOperationError(
                                        _lifecycle_timeout_code(operation)
                                    )
                                else:
                                    try:
                                        connection.send_frame(
                                            {
                                                "kind": "CONTAINMENT_READY",
                                                "remaining_seconds_at_spawn": release_remaining,
                                            }
                                        )
                                    except Exception:  # noqa: BLE001 - bounded IPC failure
                                        failure = Feat018LifecycleOperationError(
                                            Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                        )
                                    else:
                                        while failure is None and not result_received:
                                            remaining = _positive_finite_float(
                                                active_deadline - self.clock()
                                            )
                                            if remaining is None:
                                                failure = Feat018LifecycleOperationError(
                                                    _lifecycle_cancellation_failed_code(operation)
                                                    if phase == "cancel"
                                                    else _lifecycle_timeout_code(operation)
                                                )
                                                break
                                            try:
                                                frame = connection.recv_frame(remaining)
                                            except (
                                                Feat018FrameTooLargeError,
                                                Feat018ProtocolViolationError,
                                            ):
                                                failure = Feat018LifecycleOperationError(
                                                    Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                                )
                                                break
                                            except EOFError:
                                                failure = Feat018LifecycleOperationError(
                                                    _lifecycle_worker_dead_code(operation),
                                                    cleanup_status=(
                                                        CleanupStatus.CLEANUP_FAILED
                                                        if operation == "terminate"
                                                        else CleanupStatus.SUCCEEDED
                                                    ),
                                                )
                                                break
                                            except OSError:
                                                with contextlib.suppress(Exception):
                                                    process.join(timeout=0.05)
                                                try:
                                                    worker_alive = process.is_alive()
                                                except Exception:  # noqa: BLE001 - fail closed
                                                    worker_alive = True
                                                failure = Feat018LifecycleOperationError(
                                                    _lifecycle_worker_dead_code(operation)
                                                    if not worker_alive
                                                    else (
                                                        Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                                    ),
                                                    cleanup_status=(
                                                        CleanupStatus.CLEANUP_FAILED
                                                        if not worker_alive
                                                        and operation == "terminate"
                                                        else CleanupStatus.SUCCEEDED
                                                    ),
                                                )
                                                break
                                            except Exception:  # noqa: BLE001 - transport is typed
                                                failure = Feat018LifecycleOperationError(
                                                    Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                                )
                                                break

                                            observed = self.clock()
                                            if frame is None:
                                                try:
                                                    worker_alive = process.is_alive()
                                                except Exception:  # noqa: BLE001 - fail closed
                                                    worker_alive = False
                                                if not worker_alive:
                                                    failure = Feat018LifecycleOperationError(
                                                        _lifecycle_worker_dead_code(operation),
                                                        cleanup_status=(
                                                            CleanupStatus.CLEANUP_FAILED
                                                            if operation == "terminate"
                                                            else CleanupStatus.SUCCEEDED
                                                        ),
                                                    )
                                                    break
                                                if observed >= active_deadline:
                                                    failure = Feat018LifecycleOperationError(
                                                        _lifecycle_cancellation_failed_code(operation)
                                                        if phase == "cancel"
                                                        else _lifecycle_timeout_code(operation)
                                                    )
                                                continue
                                            if observed >= active_deadline:
                                                failure = Feat018LifecycleOperationError(
                                                    _lifecycle_cancellation_failed_code(operation)
                                                    if phase == "cancel"
                                                    else _lifecycle_timeout_code(operation)
                                                )
                                                break
                                            frame_mapping = _payload_mapping(frame)
                                            if frame_mapping is None:
                                                failure = Feat018LifecycleOperationError(
                                                    Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                                )
                                                break
                                            kind = frame_mapping.get("kind")
                                            if kind in (
                                                "LIFECYCLE_CALL_STARTED",
                                                "LIFECYCLE_WAIT_STARTED",
                                                "LIFECYCLE_CANCEL_STARTED",
                                            ):
                                                if not _payload_has_exact_keys(
                                                    frame_mapping, {"kind"}
                                                ):
                                                    failure = Feat018LifecycleOperationError(
                                                        Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                                    )
                                                    break
                                                if kind == "LIFECYCLE_CANCEL_STARTED":
                                                    phase = "cancel"
                                                    active_deadline = cancellation_deadline
                                                elif kind == "LIFECYCLE_WAIT_STARTED":
                                                    phase = "wait"
                                                continue
                                            if kind == "LIFECYCLE_OPERATION_RESULT":
                                                if not _payload_has_exact_keys(
                                                    frame_mapping, {"kind", "fact"}
                                                ):
                                                    failure = Feat018LifecycleOperationError(
                                                        Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                                    )
                                                    break
                                                result = _lightning_fact_from_payload(
                                                    frame_mapping["fact"]
                                                )
                                                if result is None:
                                                    failure = Feat018LifecycleOperationError(
                                                        Feat018LiveSmokeFailureCode.LIFECYCLE_RESULT_INVALID
                                                    )
                                                else:
                                                    result_received = True
                                                break
                                            if kind == "LIFECYCLE_OPERATION_FAILED":
                                                if not _payload_has_exact_keys(
                                                    frame_mapping,
                                                    {"kind", "failure_kind", "cancellation"},
                                                ):
                                                    failure = Feat018LifecycleOperationError(
                                                        Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                                    )
                                                    break
                                                failure_kind = frame_mapping["failure_kind"]
                                                if failure_kind == "call_failed":
                                                    if frame_mapping["cancellation"] is not None:
                                                        failure = Feat018LifecycleOperationError(
                                                            Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                                        )
                                                    else:
                                                        failure = Feat018LifecycleOperationError(
                                                            _lifecycle_failed_code(operation)
                                                        )
                                                    break
                                                cancellation = _lightning_fact_from_payload(
                                                    frame_mapping["cancellation"]
                                                )
                                                cancellation_verified = (
                                                    isinstance(
                                                        cancellation, LightningCancellationFacts
                                                    )
                                                    and cancellation.cancellation_verified is True
                                                )
                                                if operation == "terminate":
                                                    cancellation_verified = (
                                                        _termination_cancellation_was_verified(
                                                            cancellation, session_identity
                                                        )
                                                    )
                                                if not cancellation_verified or failure_kind == (
                                                    "cancel_failed"
                                                ):
                                                    failure = Feat018LifecycleOperationError(
                                                        _lifecycle_cancellation_failed_code(operation)
                                                    )
                                                elif failure_kind == "timeout":
                                                    failure = Feat018LifecycleOperationError(
                                                        _lifecycle_timeout_code(operation)
                                                    )
                                                elif failure_kind == "failed":
                                                    failure = Feat018LifecycleOperationError(
                                                        _lifecycle_failed_code(operation)
                                                    )
                                                else:
                                                    failure = Feat018LifecycleOperationError(
                                                        Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                                    )
                                                break
                                            failure = Feat018LifecycleOperationError(
                                                Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
                                            )
        except Feat018LifecycleOperationError as exc:
            failure = exc
        except Feat018CleanupFailedError as exc:
            launch_cleanup_failure = exc
            failure = Feat018LifecycleOperationError(
                Feat018LiveSmokeFailureCode.LIFECYCLE_CLEANUP_FAILED,
                cleanup_status=CleanupStatus.CLEANUP_FAILED,
                cleanup_failure=exc,
            )
            exc.retry_cleanup(grace_seconds=1.0, kill_join_seconds=1.0)
        except Feat018LauncherError:
            failure = Feat018LifecycleOperationError(
                Feat018LiveSmokeFailureCode.LIFECYCLE_WORKER_LAUNCH_FAILED
            )
        except Exception:  # noqa: BLE001 - no controller or provider detail escapes
            failure = Feat018LifecycleOperationError(
                Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
            )
        finally:
            resource_cleanup_failure = self._cleanup_resources(process, connection, containment)

        if resource_cleanup_failure is not None or launch_cleanup_failure is not None:
            raise Feat018LifecycleOperationError(
                Feat018LiveSmokeFailureCode.LIFECYCLE_CLEANUP_FAILED,
                cleanup_status=CleanupStatus.CLEANUP_FAILED,
                cleanup_failure=launch_cleanup_failure or resource_cleanup_failure,
            )
        if failure is not None:
            raise failure
        if not result_received:
            raise Feat018LifecycleOperationError(
                Feat018LiveSmokeFailureCode.LIFECYCLE_RESULT_INVALID
            )
        assert result is not None
        return result

    def _cleanup_resources(
        self,
        process: ProcessHandle | None,
        connection: BoundedConnection | None,
        containment: ContainmentBackend | None,
        *,
        cleanup_deadline_monotonic: float | None = None,
    ) -> Feat018CleanupFailedError | None:
        cleanup_failed = (
            cleanup_deadline_monotonic is not None
            and self.clock() >= cleanup_deadline_monotonic
        )
        owned_process: ProcessHandle | None = None
        owned_connections: tuple[BoundedConnection | _RawConnection, ...] = ()
        owned_containments: tuple[ContainmentBackend, ...] = ()
        cleanup_budget = _positive_finite_float(self.cleanup_deadline_seconds) or 0.001
        cleanup_start = self.clock()
        cleanup_deadline = (
            cleanup_start + cleanup_budget
            if cleanup_deadline_monotonic is None
            else cleanup_deadline_monotonic
        )
        join_budget = max(0.001, min(1.0, cleanup_budget / 3.0))

        if containment is not None:
            try:
                _terminate_owned_containment(
                    containment,
                    cleanup_deadline_monotonic=cleanup_deadline,
                    clock=self.clock,
                )
            except Exception:  # noqa: BLE001 - process cleanup still proceeds
                cleanup_failed = True
                owned_containments = (containment,)
        if process is not None and not _bounded_terminate_kill_join(
            process,
            grace_seconds=join_budget,
            kill_join_seconds=join_budget,
            cleanup_deadline_monotonic=cleanup_deadline,
            clock=self.clock,
        ):
            cleanup_failed = True
            if not bool(getattr(process, 'closed', False)):
                owned_process = process

        if containment is not None:
            interval = min(self.confirmation_retry_interval_seconds, 0.01)
            while True:
                try:
                    empty = containment.is_empty()
                except Exception:  # noqa: BLE001 - unknown descendants fail closed
                    cleanup_failed = True
                    owned_containments = (containment,)
                    break
                if bool(getattr(containment, "_cleanup_failed", False)):
                    cleanup_failed = True
                    owned_containments = (containment,)
                if (
                    cleanup_deadline_monotonic is not None
                    and self.clock() >= cleanup_deadline
                ):
                    cleanup_failed = True
                if empty:
                    break
                remaining = cleanup_deadline - self.clock()
                if _positive_finite_float(remaining) is None:
                    cleanup_failed = True
                    owned_containments = (containment,)
                    break
                try:
                    self.sleep(min(interval, remaining))
                except Exception:  # noqa: BLE001 - a broken wait is cleanup failure
                    cleanup_failed = True
                    owned_containments = (containment,)
                    break
            try:
                _close_verified_empty_containment(containment)
            except Exception:  # noqa: BLE001 - close failure is surfaced by the result
                cleanup_failed = True
                owned_containments = (containment,)
            if bool(getattr(containment, "_cleanup_failed", False)):
                cleanup_failed = True
                owned_containments = (containment,)

        if connection is not None:
            try:
                connection.close()
            except Exception:  # noqa: BLE001 - close failure is surfaced by the result
                cleanup_failed = True
                owned_connections = (connection,)
        if (
            cleanup_deadline_monotonic is not None
            and self.clock() >= cleanup_deadline
        ):
            cleanup_failed = True
        if cleanup_failed:
            return Feat018CleanupFailedError(
                owned_process=owned_process,
                owned_connections=owned_connections,
                owned_containments=owned_containments,
            )
        return None


# --------------------------------------------------------------------------------------
# NON-LIVE, TEST-SEAM-ONLY cooperative-wait helpers (independent-review finding B3-3)
#
# The three functions below call ``operation.wait()``/``operation.cancel()`` directly in the
# caller's own process, trusting the operation handle to honor its ``timeout_seconds`` argument.
# That cooperative-timeout pattern is exactly what the real host-preemption boundary
# (:class:`Feat018LightningLifecycleProcessBoundary`, above) exists to replace: a controller or
# provider operation that ignores its timeout and never returns cannot be regained here, because
# nothing calls these helpers from inside a killable child process.
#
# ``run_live_smoke`` never calls these helpers and never passes anything but the default,
# process-isolated boundary unless a caller explicitly injects ``lifecycle_boundary=``; see
# ``test_run_live_smoke_default_boundary_is_the_real_process_boundary_not_the_cooperative_helpers``
# for a static proof that this stays true. The only caller of these helpers today is the
# deterministic, fake-clock-only ``FakeInlineLightningLifecycleBoundary`` test double, which keeps
# the pre-existing coordinator-logic regression suite (deadline budgeting, TTL/GPU-minute caps,
# placement/session-identity checks) fast and free of real subprocess overhead. They must never be
# wired into a live coordinator, a default parameter, or any code path that can run against a real
# Lightning/provider session; doing so would silently reintroduce the exact non-preemptive hang
# this module's B3 remediation closed.
# --------------------------------------------------------------------------------------


def _wait_for_lightning_operation[TLightOperation](
    operation: LightningOperationHandle[TLightOperation],
    *,
    deadline: float,
    clock: Callable[[], float],
) -> TLightOperation:
    """TEST-SEAM ONLY -- cooperative, in-process wait. Never call this from a live coordinator."""

    remaining = _positive_finite_float(deadline - clock())
    if remaining is None:
        raise TimeoutError
    result = operation.wait(timeout_seconds=remaining)
    if clock() >= deadline:
        raise TimeoutError
    return result


def _cancel_lightning_operation(
    operation: LightningOperationHandle[object],
    *,
    deadline: float,
    clock: Callable[[], float],
) -> bool:
    """TEST-SEAM ONLY -- cooperative, in-process cancel. Never call this from a live coordinator."""

    remaining = _positive_finite_float(deadline - clock())
    if remaining is None:
        return False
    try:
        result = operation.cancel(timeout_seconds=remaining)
    except Exception:  # noqa: BLE001 - cancellation proof must be explicit
        return False
    return clock() < deadline and isinstance(result, LightningCancellationFacts) and (
        result.cancellation_verified is True
    )


def _cancel_termination_operation(
    operation: LightningOperationHandle[LightningTerminationFacts],
    *,
    deadline: float,
    clock: Callable[[], float],
    session_identity: str | None,
) -> bool:
    """TEST-SEAM ONLY -- cooperative, in-process cancel. Never call this from a live coordinator."""

    remaining = _positive_finite_float(deadline - clock())
    if remaining is None:
        return False
    cancellation: object = None
    try:
        cancellation = operation.cancel(timeout_seconds=remaining)
    except Exception:  # noqa: BLE001 - cancellation proof must be explicit
        return False
    return _termination_cancellation_was_verified(cancellation, session_identity) and (
        clock() < deadline
    )


def _supervisor_result_is_valid(value: object) -> bool:
    if not isinstance(value, SupervisorRunResult):
        return False
    if value.attempt_count is not None and (
        type(value.attempt_count) is not int or not 0 <= value.attempt_count <= 2
    ):
        return False
    if value.raw_status is not None and value.raw_status not in ("SUCCEEDED", "FAILED"):
        return False
    if value.raw_status is not None and value.raw_status != value.terminal_outcome:
        return False
    if (
        value.final_state is ProgressState.TERMINAL
        and value.terminal_outcome not in ("SUCCEEDED", "FAILED")
    ):
        return False
    if (
        value.final_state is not ProgressState.TERMINAL
        and (value.terminal_outcome is not None or value.raw_status is not None)
    ):
        return False
    if value.cleanup_status is CleanupStatus.CLEANUP_FAILED and (
        value.effective_outcome is EffectiveOutcome.SUCCEEDED
    ):
        return False
    if value.cleanup_failure is not None and (
        value.cleanup_status is not CleanupStatus.CLEANUP_FAILED
        or value.effective_outcome is not EffectiveOutcome.CLEANUP_FAILED
    ):
        return False
    success_contract = (
        value.final_state is ProgressState.TERMINAL
        and value.terminal_outcome == "SUCCEEDED"
        and value.raw_status == "SUCCEEDED"
        and value.attempt_count in (1, 2)
        and value.cleanup_status is CleanupStatus.SUCCEEDED
        and value.cleanup_failure is None
        and value.effective_outcome is EffectiveOutcome.SUCCEEDED
        and value.primary_failure_reason is None
        and _d9_success_contract(
            value.d9_observations, value.d9_failure_codes, attempt_count=value.attempt_count
        )
    )
    if value.terminal_outcome == "SUCCEEDED" and not success_contract:
        return False
    return value.effective_outcome is not EffectiveOutcome.SUCCEEDED or success_contract


def _finalization_was_verified(value: object) -> bool:
    return (
        isinstance(value, LightningFinalizationFacts)
        and value.finalization_verified is True
        and value.evidence_pair_verified is True
        and value.incident_handling_verified is True
    )


def _adapter_result_is_accepted_success(value: SupervisorRunResult) -> bool:
    return (
        value.final_state is ProgressState.TERMINAL
        and value.terminal_outcome == "SUCCEEDED"
        and value.raw_status == "SUCCEEDED"
        and value.cleanup_status is CleanupStatus.SUCCEEDED
        and value.cleanup_failure is None
        and value.effective_outcome is EffectiveOutcome.SUCCEEDED
        and value.attempt_count in (1, 2)
        and value.primary_failure_reason is None
        and _d9_success_contract(
            value.d9_observations, value.d9_failure_codes, attempt_count=value.attempt_count
        )
    )


def _run_legacy_offline_smoke(
    request: VisionUnderstandingRequestV2,
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    *,
    controller: LightningSessionController | None = None,
    config: Feat018LiveSmokeConfig | None = None,
    session_id: str | None = None,
    preflight: LightningPreflight | None = None,
    finalizer: LightningSmokeFinalizer | None = None,
    adapter_call: BoundedAdapterCall | None = None,
    lifecycle_boundary: LightningLifecycleBoundary | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Feat018LiveSmokeResult:
    """Historical NON-LIVE TEST-SEAM ONLY coordinator for pre-D11 regressions.

    Every live-capable dependency is injected. Missing preflight, finalization, controller, or
    adapter seams return a typed ``NOT_AUTHORIZED`` result before provisioning, and the adapter
    has no real default. Controller methods execute through the default host-killable lifecycle
    process boundary; ``clock`` is the host-side monotonic watchdog clock and is never supplied
    by the provider. A test may inject a deterministic boundary explicitly.
    """

    if not _is_bounded_opaque_identifier(session_id):
        return Feat018LiveSmokeResult(
            effective_outcome=EffectiveOutcome.FAILED,
            adapter_call_count=0,
            attempt_count=None,
            cleanup_status=CleanupStatus.SUCCEEDED,
            failure_code=Feat018LiveSmokeFailureCode.NOT_AUTHORIZED,
        )
    assert isinstance(session_id, str)
    if not isinstance(config, Feat018LiveSmokeConfig):
        return Feat018LiveSmokeResult(
            effective_outcome=EffectiveOutcome.FAILED,
            adapter_call_count=0,
            attempt_count=None,
            cleanup_status=CleanupStatus.SUCCEEDED,
            failure_code=Feat018LiveSmokeFailureCode.NOT_AUTHORIZED,
        )
    if controller is None:
        return Feat018LiveSmokeResult(
            effective_outcome=EffectiveOutcome.FAILED,
            adapter_call_count=0,
            attempt_count=None,
            cleanup_status=CleanupStatus.SUCCEEDED,
            failure_code=Feat018LiveSmokeFailureCode.CONTROLLER_MISSING,
        )
    if preflight is None:
        return Feat018LiveSmokeResult(
            effective_outcome=EffectiveOutcome.FAILED,
            adapter_call_count=0,
            attempt_count=None,
            cleanup_status=CleanupStatus.SUCCEEDED,
            failure_code=Feat018LiveSmokeFailureCode.PREFLIGHT_MISSING,
        )
    if finalizer is None:
        return Feat018LiveSmokeResult(
            effective_outcome=EffectiveOutcome.FAILED,
            adapter_call_count=0,
            attempt_count=None,
            cleanup_status=CleanupStatus.SUCCEEDED,
            failure_code=Feat018LiveSmokeFailureCode.FINALIZATION_MISSING,
        )
    if adapter_call is None:
        return Feat018LiveSmokeResult(
            effective_outcome=EffectiveOutcome.FAILED,
            adapter_call_count=0,
            attempt_count=None,
            cleanup_status=CleanupStatus.SUCCEEDED,
            failure_code=Feat018LiveSmokeFailureCode.ADAPTER_CALL_MISSING,
        )

    try:
        preflight_facts = preflight.verify(synthetic_session_id=session_id)
    except Exception:  # noqa: BLE001 - preflight detail never crosses this boundary
        return Feat018LiveSmokeResult(
            effective_outcome=EffectiveOutcome.FAILED,
            adapter_call_count=0,
            attempt_count=None,
            cleanup_status=CleanupStatus.SUCCEEDED,
            failure_code=Feat018LiveSmokeFailureCode.PREFLIGHT_FAILED,
        )
    if not _preflight_was_verified(preflight_facts, session_id):
        return Feat018LiveSmokeResult(
            effective_outcome=EffectiveOutcome.FAILED,
            adapter_call_count=0,
            attempt_count=None,
            cleanup_status=CleanupStatus.SUCCEEDED,
            failure_code=Feat018LiveSmokeFailureCode.PREFLIGHT_NOT_AUTHORIZED,
        )

    boundary = lifecycle_boundary or Feat018LightningLifecycleProcessBoundary(
        controller=controller,
        max_envelope_bytes=config.bounded_runner_config.ipc_envelope_max_bytes,
        containment_factory=create_platform_containment,
        cleanup_deadline_seconds=config.bounded_runner_config.cleanup_deadline_seconds,
        containment_setup_timeout_seconds=(
            config.bounded_runner_config.containment_setup_timeout_seconds
        ),
        confirmation_retry_interval_seconds=(
            config.bounded_runner_config.posix_confirmation_retry_interval_seconds
        ),
        clock=clock,
    )

    adapter_call_count = 0
    attempt_count: int | None = None
    cleanup_status = CleanupStatus.SUCCEEDED
    effective_outcome = EffectiveOutcome.FAILED
    failure_code: Feat018LiveSmokeFailureCode | None = None
    adapter_result: SupervisorRunResult | None = None
    provision_started = False
    session_ready = False
    provision_start: float | None = None
    ready_deadline: float | None = None
    gpu_budget_start: float | None = None
    ready_at: float | None = None
    ttl_start: float | None = None
    ttl_deadline: float | None = None
    adapter_start: float | None = None
    adapter_deadline: float | None = None
    termination_deadline: float | None = None
    session_identity: str | None = None
    session_ready_at: float | None = None
    placement: LightningPlacementFacts | None = None
    cleanup_failures: list[Feat018CleanupFailedError] = []

    def record_lifecycle_error(error: Feat018LifecycleOperationError) -> None:
        nonlocal cleanup_status, effective_outcome, failure_code
        if error.cleanup_failure is not None:
            cleanup_failures.append(error.cleanup_failure)
        failure_code = error.failure_code
        if error.cleanup_status is CleanupStatus.CLEANUP_FAILED or error.failure_code in {
            Feat018LiveSmokeFailureCode.OPERATION_CANCELLATION_FAILED,
        }:
            cleanup_status = CleanupStatus.CLEANUP_FAILED
            effective_outcome = EffectiveOutcome.CLEANUP_FAILED

    try:
        # This assignment is immediately followed by the host-bounded provision invocation.
        provision_started = True
        provision_start = clock()
        provision_candidate: object | None = None
        ready_deadline = _add_finite_deadline(
            provision_start, float(config.session_provision_timeout_seconds)
        )
        if ready_deadline is None:
            failure_code = Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT
        else:
            cancellation_deadline = _add_finite_deadline(
                clock(), float(config.session_termination_deadline_seconds)
            )
            if cancellation_deadline is None:
                failure_code = Feat018LiveSmokeFailureCode.OPERATION_CANCELLATION_FAILED
            else:
                try:
                    provision_candidate = boundary.invoke(
                        "provision",
                        deadline=ready_deadline,
                        cancellation_deadline=cancellation_deadline,
                    )
                except Feat018LifecycleOperationError as error:
                    record_lifecycle_error(error)
                except Exception:  # noqa: BLE001 - provider details never cross this boundary
                    failure_code = Feat018LiveSmokeFailureCode.PROVISION_FAILED
        if failure_code is None:
            assert ready_deadline is not None
            provision_finished = clock()
            if provision_finished >= ready_deadline:
                failure_code = Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT
            elif not isinstance(provision_candidate, LightningProvisionFacts) or not (
                provision_candidate.allocation_confirmed
            ):
                failure_code = Feat018LiveSmokeFailureCode.PROVISION_FACTS_MISSING
            elif not _placement_matches_approval(
                provision_candidate.placement, config.placement_approval
            ):
                failure_code = Feat018LiveSmokeFailureCode.PLACEMENT_MISMATCH
            else:
                candidate_budget_start = provision_candidate.gpu_minute_budget_start_monotonic
                if candidate_budget_start is None or (
                    candidate_budget_start < provision_start
                    or candidate_budget_start > provision_finished
                    or not _is_finite_number(candidate_budget_start)
                ):
                    failure_code = Feat018LiveSmokeFailureCode.PROVISION_FACTS_MISSING
                else:
                    session_identity = provision_candidate.session_identity
                    placement = provision_candidate.placement
                    gpu_budget_start = candidate_budget_start
                    gpu_budget_deadline = _add_finite_deadline(
                        gpu_budget_start, float(config.gpu_minute_cap) * 60.0
                    )
                    if gpu_budget_deadline is None:
                        failure_code = Feat018LiveSmokeFailureCode.PROVISION_FACTS_MISSING
                    elif provision_finished >= gpu_budget_deadline:
                        failure_code = Feat018LiveSmokeFailureCode.GPU_MINUTE_BUDGET_EXCEEDED
                    else:
                        remaining_ready_seconds = ready_deadline - clock()
                        if _positive_finite_float(remaining_ready_seconds) is None:
                            failure_code = Feat018LiveSmokeFailureCode.READY_TIMEOUT
                        else:
                            ready_candidate: object | None = None
                            ready_cancellation_deadline = _add_finite_deadline(
                                clock(),
                                float(config.session_termination_deadline_seconds),
                            )
                            if ready_cancellation_deadline is None:
                                failure_code = (
                                    Feat018LiveSmokeFailureCode.OPERATION_CANCELLATION_FAILED
                                )
                            else:
                                try:
                                    ready_candidate = boundary.invoke(
                                        "wait_ready",
                                        deadline=ready_deadline,
                                        cancellation_deadline=ready_cancellation_deadline,
                                    )
                                except Feat018LifecycleOperationError as error:
                                    record_lifecycle_error(error)
                                except Exception:  # noqa: BLE001 - provider details stay local
                                    failure_code = Feat018LiveSmokeFailureCode.READY_FAILED
                            if failure_code is None:
                                ready_finished = clock()
                                if ready_finished >= ready_deadline:
                                    failure_code = Feat018LiveSmokeFailureCode.READY_TIMEOUT
                                elif not isinstance(ready_candidate, LightningReadyFacts):
                                    failure_code = Feat018LiveSmokeFailureCode.READY_FACTS_MISSING
                                elif (
                                    ready_candidate.readiness
                                    is not LightningSessionReadiness.SESSION_READY
                                ):
                                    failure_code = Feat018LiveSmokeFailureCode.SESSION_NOT_READY
                                else:
                                    lifecycle_failure = _lifecycle_failure_code(
                                        ready_candidate.lifecycle,
                                        provision_facts=provision_candidate,
                                        provision_start=provision_start,
                                        ready_finished=ready_finished,
                                        ready_deadline=ready_deadline,
                                        session_ttl_seconds=config.session_ttl_seconds,
                                    )
                                    if lifecycle_failure is not None:
                                        failure_code = lifecycle_failure
                                    else:
                                        assert ready_candidate.lifecycle is not None
                                        # The TTL is taken from controller-owned lifecycle facts,
                                        # never inferred from a readiness enum or host placeholder.
                                        session_ready = True
                                        ready_at = ready_finished
                                        session_ready_at = (
                                            ready_candidate.lifecycle.session_ready_at_monotonic
                                        )
                                        ttl_start = (
                                            ready_candidate.lifecycle.session_ttl_start_monotonic
                                        )
                                        ttl_deadline = (
                                            ready_candidate.lifecycle.session_ttl_deadline_monotonic
                                        )
                                        if ready_finished >= gpu_budget_deadline:
                                            failure_code = (
                                                Feat018LiveSmokeFailureCode.GPU_MINUTE_BUDGET_EXCEEDED
                                            )
                                        elif ready_finished >= ttl_deadline:
                                            failure_code = (
                                                Feat018LiveSmokeFailureCode.SESSION_TTL_EXCEEDED
                                            )
                                        else:
                                            # This timestamp is the final host check before the
                                            # call count increment and sole adapter invocation.
                                            adapter_boundary_now = clock()
                                            failure_code = _active_cap_failure_code(
                                                adapter_boundary_now,
                                                ttl_deadline=ttl_deadline,
                                                gpu_budget_deadline=gpu_budget_deadline,
                                            )
                                            if failure_code is None:
                                                adapter_start = adapter_boundary_now
                                                adapter_deadline = _add_finite_deadline(
                                                    adapter_start,
                                                    config.bounded_runner_config.total_adapter_cap_seconds,
                                                )
                                                if adapter_deadline is None:
                                                    failure_code = (
                                                        Feat018LiveSmokeFailureCode.ADAPTER_CAP_EXCEEDED
                                                    )
                                                else:
                                                    adapter_call_count = 1
                                                    try:
                                                        adapter_candidate = adapter_call(
                                                            request,
                                                            runtime_config,
                                                            content_policy,
                                                            prompt,
                                                            config.bounded_runner_config,
                                                            session_id=session_id,
                                                        )
                                                    except Feat018CleanupFailedError as error:
                                                        cleanup_failures.append(error)
                                                        cleanup_status = CleanupStatus.CLEANUP_FAILED
                                                        failure_code = (
                                                            Feat018LiveSmokeFailureCode.ADAPTER_CLEANUP_FAILED
                                                        )
                                                    except Exception:  # noqa: BLE001 - no adapter detail escapes
                                                            failure_code = (
                                                                _active_cap_failure_code(
                                                                    clock(),
                                                                    ttl_deadline=ttl_deadline,
                                                                    gpu_budget_deadline=gpu_budget_deadline,
                                                                )
                                                                or (
                                                                    Feat018LiveSmokeFailureCode.ADAPTER_CALL_FAILED
                                                                )
                                                            )
                                                    else:
                                                        if (
                                                            isinstance(adapter_candidate, SupervisorRunResult)
                                                            and adapter_candidate.cleanup_failure is not None
                                                        ):
                                                            cleanup_failures.append(
                                                                adapter_candidate.cleanup_failure
                                                            )
                                                            cleanup_status = CleanupStatus.CLEANUP_FAILED
                                                            effective_outcome = EffectiveOutcome.CLEANUP_FAILED
                                                            failure_code = (
                                                                Feat018LiveSmokeFailureCode.ADAPTER_CLEANUP_FAILED
                                                            )
                                                        if not _supervisor_result_is_valid(
                                                            adapter_candidate
                                                        ):
                                                            if cleanup_status is not CleanupStatus.CLEANUP_FAILED:
                                                                failure_code = (
                                                                    Feat018LiveSmokeFailureCode.ADAPTER_RESULT_INVALID
                                                                )
                                                        else:
                                                            adapter_result = adapter_candidate
                                                            attempt_count = (
                                                                adapter_candidate.attempt_count
                                                            )
                                                            adapter_cleanup_failed = (
                                                                adapter_candidate.cleanup_status
                                                                is CleanupStatus.CLEANUP_FAILED
                                                            ) or (
                                                                adapter_candidate.effective_outcome
                                                                is EffectiveOutcome.CLEANUP_FAILED
                                                            )
                                                            if adapter_cleanup_failed:
                                                                cleanup_status = (
                                                                    CleanupStatus.CLEANUP_FAILED
                                                                )
                                                                failure_code = (
                                                                    Feat018LiveSmokeFailureCode.ADAPTER_CLEANUP_FAILED
                                                                )
                                                            else:
                                                                adapter_finished = clock()
                                                                adapter_result_success = (
                                                                    _adapter_result_is_accepted_success(
                                                                        adapter_candidate
                                                                    )
                                                                )
                                                                if (
                                                                    adapter_finished
                                                                    >= adapter_deadline
                                                                ):
                                                                    failure_code = (
                                                                        Feat018LiveSmokeFailureCode.ADAPTER_CAP_EXCEEDED
                                                                    )
                                                                elif (
                                                                    adapter_finished
                                                                    >= ttl_deadline
                                                                ):
                                                                    failure_code = (
                                                                        Feat018LiveSmokeFailureCode.SESSION_TTL_EXCEEDED
                                                                    )
                                                                elif (
                                                                    adapter_finished
                                                                    >= gpu_budget_deadline
                                                                ):
                                                                    failure_code = (
                                                                        Feat018LiveSmokeFailureCode.GPU_MINUTE_BUDGET_EXCEEDED
                                                                    )
                                                                elif adapter_result_success:
                                                                    effective_outcome = (
                                                                        EffectiveOutcome.SUCCEEDED
                                                                    )
                                                                else:
                                                                    failure_code = (
                                                                        Feat018LiveSmokeFailureCode.ADAPTER_FAILED
                                                                    )
    except Exception:  # noqa: BLE001 - lifecycle failures remain fixed-code and cleanup continues
        if failure_code is None:
            failure_code = Feat018LiveSmokeFailureCode.PROVISION_FAILED
    finally:
        if provision_started:
            cleanup_failed = False
            cleanup_failure_code: Feat018LiveSmokeFailureCode | None = None
            try:
                cleanup_start = clock()
                termination_deadline = _add_finite_deadline(
                    cleanup_start, float(config.session_termination_deadline_seconds)
                )
                if termination_deadline is None:
                    cleanup_failed = True
                    cleanup_failure_code = Feat018LiveSmokeFailureCode.SESSION_TERMINATION_TIMEOUT
                else:
                    try:
                        termination_candidate = boundary.invoke(
                            "terminate",
                            deadline=termination_deadline,
                            cancellation_deadline=termination_deadline,
                            session_identity=session_identity,
                        )
                    except Feat018LifecycleOperationError as error:
                        cleanup_failed = True
                        cleanup_failure_code = error.failure_code
                        if error.cleanup_failure is not None:
                            cleanup_failures.append(error.cleanup_failure)
                    else:
                        if not _termination_matches_session(
                            termination_candidate, session_identity
                        ):
                            cleanup_failed = True
                            cleanup_failure_code = (
                                Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED
                            )
            except Exception:  # noqa: BLE001 - cleanup failure must still produce a typed result
                cleanup_failed = True
                cleanup_failure_code = Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED

            if cleanup_failed:
                cleanup_status = CleanupStatus.CLEANUP_FAILED
                effective_outcome = EffectiveOutcome.CLEANUP_FAILED
                failure_code = cleanup_failure_code or (
                    Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED
                )

    if cleanup_status is CleanupStatus.CLEANUP_FAILED:
        effective_outcome = EffectiveOutcome.CLEANUP_FAILED
    elif effective_outcome is EffectiveOutcome.SUCCEEDED and failure_code is not None:
        effective_outcome = EffectiveOutcome.FAILED
    elif effective_outcome is not EffectiveOutcome.SUCCEEDED and failure_code is None:
        failure_code = Feat018LiveSmokeFailureCode.ADAPTER_FAILED

    result = Feat018LiveSmokeResult(
        effective_outcome=effective_outcome,
        adapter_call_count=adapter_call_count,
        attempt_count=attempt_count,
        cleanup_status=cleanup_status,
        failure_code=failure_code,
        session_ready=session_ready,
        provision_start_monotonic=provision_start,
        ready_deadline_monotonic=ready_deadline,
        gpu_minute_budget_start_monotonic=gpu_budget_start,
        ready_at_monotonic=ready_at,
        session_ttl_start_monotonic=ttl_start,
        session_ttl_deadline_monotonic=ttl_deadline,
        adapter_start_monotonic=adapter_start,
        total_adapter_cap_deadline_monotonic=adapter_deadline,
        session_termination_deadline_monotonic=termination_deadline,
        adapter_result=adapter_result,
        session_identity=session_identity,
        session_ready_at_monotonic=session_ready_at,
        placement=placement,
        cleanup_failures=tuple(cleanup_failures),
        preflight_verified=True,
    )

    try:
        finalization_candidate = finalizer.finalize(result=result)
    except Exception:  # noqa: BLE001 - finalization details never cross this boundary
        finalization_candidate = None
    if not _finalization_was_verified(finalization_candidate):
        return replace(
            result,
            effective_outcome=(
                EffectiveOutcome.CLEANUP_FAILED
                if result.cleanup_status is CleanupStatus.CLEANUP_FAILED
                else EffectiveOutcome.FAILED
            ),
            failure_code=Feat018LiveSmokeFailureCode.FINALIZATION_FAILED,
            finalization_verified=False,
        )
    return replace(result, finalization_verified=True)


def _progress_event_from_frame(frame: Mapping[str, object]) -> ProgressEvent | None:
    if not isinstance(frame, Mapping):
        return None
    allowed_keys = {"seq", "kind", "attempt_number", "outcome", "raw_status", "cleanup_failed"}
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
    if "cleanup_failed" in frame and (
        frame["cleanup_failed"] is not True
        or kind_raw != ProgressEventKind.TERMINAL.value
        or outcome != 'FAILED'
    ):
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
        terminal_result: Feat018LiveSmokeResult | None = None,
        binding_metadata: BindingTerminalMetadataV1 | None = None,
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

        if terminal_result is not None:
            try:
                _validate_terminal_publication_privacy(terminal_result, (run_id, evidence_id))
            except Exception:  # noqa: BLE001 - unsafe identities cannot enter public failures
                return EvidenceCommitResult(
                    committed=False,
                    run_id="redacted",
                    evidence_id="redacted",
                    failure_reason="evidence identity verification failed",
                )

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
            terminal_fields: dict[str, object] = (
                {} if terminal_result is None else _d11_terminal_evidence_fields(
                    terminal_result, runtime_outcome=runtime_outcome,
                )
            )
            evidence_fields = dict(terminal_fields)
            if binding_metadata is not None:
                if terminal_result is None:
                    raise Feat018EvidenceCommitError("binding metadata requires a typed terminal")
                evidence_fields.update(_binding_terminal_evidence_fields(
                    binding_metadata, terminal_result, runtime_outcome=runtime_outcome,
                    terminal_fields=terminal_fields,
                    publication_ids=(run_id, evidence_id),
                ))
            markdown_body = (
                f"status: {runtime_outcome.value}\n"
                f"cleanup_status: {cleanup_status.value}\npostflight_status: SUCCEEDED"
            )
            if evidence_fields:
                markdown_body += "\n\n```json\n" + json.dumps(
                    evidence_fields, sort_keys=True, indent=2, allow_nan=False,
                ) + "\n```"
            json_fields = {
                "status": runtime_outcome.value,
                "cleanup_status": cleanup_status.value,
                "postflight_status": "SUCCEEDED",
                **evidence_fields,
            }
            if terminal_result is not None:
                _validate_terminal_publication_privacy(terminal_result, {
                    **json_fields,
                    "run_id": run_id,
                    "evidence_id": evidence_id,
                    "commit_state": "FINAL",
                    "companion_markdown_sha256": sha256(
                        _render_markdown(run_id, evidence_id, markdown_body).encode("utf-8")
                    ).hexdigest(),
                })
            result = self.writer.commit(
                run_id=run_id,
                evidence_id=evidence_id,
                json_fields=json_fields,
                markdown_body=markdown_body,
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

    def binding_summary(self) -> BindingArtifactInventorySummaryV1:
        """Summarize the captured baseline without publishing paths or future observations."""
        if self._baseline is None:
            raise Feat018EvidenceCommitError("inventory baseline has not been captured")
        files = sum(stat.S_ISREG(fingerprint[0]) for fingerprint in self._baseline.values())
        directories = sum(stat.S_ISDIR(fingerprint[0]) for fingerprint in self._baseline.values())
        return BindingArtifactInventorySummaryV1(
            baseline_entry_count=len(self._baseline), baseline_file_count=files,
            baseline_directory_count=directories, explicit_root_count=len(self.roots),
            max_entries=self.max_entries, expected_evidence_file_count=2,
        )

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
    result: SupervisorRunResult | Feat018LiveSmokeResult,
    *,
    run_id: str,
    evidence_id: str,
    inventory: Feat018ArtifactInventory,
    cleanup: Callable[[], CleanupStatus],
    writer: Feat018EvidenceCommitWriter,
    incident: Feat018IncidentWriter,
    binding_metadata: BindingTerminalMetadataV1 | None = None,
) -> SmokeFinalizationResult:
    """Publish only a mapped, cleaned result with a passing real inventory comparison.

    The inventory baseline must be captured by preflight. The cleanup callback is the
    quiescent-session barrier: it must confirm that every supervised process/descendant is
    absent and that no runtime writer remains before evidence finalization becomes the sole
    authorized writer. This function never recaptures the baseline after runtime changes, never
    claims filesystem-wide atomicity against an unrelated external writer, and never promotes
    worker diagnostics.
    """

    live_result = result if isinstance(result, Feat018LiveSmokeResult) else None
    adapter_result = result.adapter_result if live_result is not None else result
    outcome = EffectiveOutcome.FAILED
    owned_failures = (live_result.cleanup_failures if live_result is not None else
                      (() if result.cleanup_failure is None else (result.cleanup_failure,)))
    live_cleanup_valid = live_result is None or (
        live_result.preflight_verified and live_result.d11_report is not None
        and live_result.d11_report.resources_released
    )
    if result.cleanup_status is CleanupStatus.CLEANUP_FAILED or owned_failures or not live_cleanup_valid:
        outcome = EffectiveOutcome.CLEANUP_FAILED
    elif adapter_result is not None and (
        result.effective_outcome is EffectiveOutcome.SUCCEEDED
        and (_adapter_result_is_accepted_success(adapter_result) if live_result is not None else (
            adapter_result.raw_status == 'SUCCEEDED'
            and adapter_result.final_state is ProgressState.TERMINAL
            and adapter_result.terminal_outcome == 'SUCCEEDED'
            and adapter_result.primary_failure_reason is None
        ))
        and (live_result is None or (
            live_result.adapter_call_count == 1
            and live_result.attempt_count == adapter_result.attempt_count
            and live_result.failure_code is None
        ))
    ):
        outcome = EffectiveOutcome.SUCCEEDED

    # Metadata describes the captured baseline; the two existing provisional audits
    # still observe the actual pair. No future postflight count is fabricated here.
    metadata_matches_inventory = True
    if binding_metadata is not None:
        try:
            checked_metadata = binding_metadata.revalidated()
            metadata_matches_inventory = (
                checked_metadata.preflight.artifact_inventory_summary == inventory.binding_summary()
            )
        except Exception:  # noqa: BLE001 - a malformed carrier never bypasses cleanup
            metadata_matches_inventory = False

    def cleanup_all() -> CleanupStatus:
        session_status = cleanup()
        if (
            result.cleanup_status is not CleanupStatus.SUCCEEDED
            or owned_failures or not live_cleanup_valid
            or session_status is not CleanupStatus.SUCCEEDED
        ):
            return CleanupStatus.CLEANUP_FAILED
        return CleanupStatus.SUCCEEDED

    def verify_postflight(json_temp: Path, markdown_temp: Path) -> bool:
        return metadata_matches_inventory and inventory.verify_provisional(json_temp, markdown_temp)

    evidence = Feat018EvidenceFinalizer(writer).finalize(
        run_id=run_id,
        evidence_id=evidence_id,
        runtime_outcome=outcome,
        cleanup=cleanup_all,
        postflight=verify_postflight,
        terminal_result=live_result,
        binding_metadata=binding_metadata,
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


class D11OperationKind(StrEnum):
    PROVISION = 'provision'
    WAIT_READY = 'wait_ready'
    DISPATCH = 'dispatch'
    CANCEL = 'cancel'
    RECONCILE = 'reconcile'
    TERMINATE = 'terminate'
    OBSERVE = 'observe'


@dataclass(frozen=True, slots=True)
class LightningProvisionRefV1:
    """Recovery key for a provisioning request, including allocation with a lost response."""

    run_id: str
    token: str

    def __post_init__(self) -> None:
        if not all(_is_bounded_opaque_identifier(value) for value in (self.run_id, self.token)):
            raise ValueError('bounded run/provision references required')


@dataclass(frozen=True, slots=True)
class LightningSessionRefV1:
    provision: LightningProvisionRefV1
    resource_identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.provision, LightningProvisionRefV1) or not (
            _is_bounded_fact_token(self.resource_identity)
        ):
            raise ValueError('typed session reference required')


@dataclass(frozen=True, slots=True)
class LightningOperationRefV1:
    provision: LightningProvisionRefV1
    token: str
    kind: D11OperationKind
    session: LightningSessionRefV1 | None = None
    recovery_of: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provision, LightningProvisionRefV1) or not (
            _is_bounded_opaque_identifier(self.token) and isinstance(self.kind, D11OperationKind)
        ):
            raise ValueError('typed parent-created operation reference required')
        if self.session is not None and self.session.provision != self.provision:
            raise ValueError('session belongs to another provision request')
        if self.recovery_of is not None and not _is_bounded_opaque_identifier(self.recovery_of):
            raise ValueError('bounded recovery operation reference required')
        if self.kind in (D11OperationKind.WAIT_READY, D11OperationKind.DISPATCH) and self.session is None:
            raise ValueError('known session required')
        if self.kind is D11OperationKind.CANCEL and self.recovery_of is None:
            raise ValueError('cancel recovery target required')


@dataclass(frozen=True, slots=True)
class D11CleanupGrant:
    run_id: str
    generation: int
    issued_at_host_monotonic: float
    deadline_host_monotonic: float
    cancellation_operation: LightningOperationRefV1 | None = None

    def __post_init__(self) -> None:
        if not _is_bounded_opaque_identifier(self.run_id) or type(self.generation) is not int or self.generation < 1:
            raise ValueError('invalid cleanup generation')
        _validate_non_negative_timestamp(self.issued_at_host_monotonic, 'grant issue time')
        if _positive_finite_float(self.deadline_host_monotonic) is None:
            raise ValueError('invalid grant deadline')

    def remaining(self, now: float) -> float:
        return max(0.0, self.deadline_host_monotonic - now)


@dataclass(slots=True)
class D11CleanupWindow:
    """One parent-owned window; grant refresh never refreshes the absolute deadline.

    The bridge runs on the host. A remote transport must send remaining duration, not interpret
    host monotonic timestamps in the session's clock domain. Numeric live budgets are unbound.
    """

    run_id: str
    budget_seconds: float
    grant_max_age_seconds: float
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    deadline: float | None = field(default=None, init=False)
    started_at: float | None = field(default=None, init=False)
    generation: int = field(default=1, init=False)
    operations: list[LightningOperationRefV1] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if not _is_bounded_opaque_identifier(self.run_id):
            raise ValueError('bounded run identity required')
        for value in (self.budget_seconds, self.grant_max_age_seconds):
            if _positive_finite_float(value) is None:
                raise ValueError('explicit finite positive cleanup parameters required')

    def begin(self, reason: str = 'cleanup_intent') -> float:
        if self.deadline is None:
            self.started_at = self.clock()
            self.deadline = _add_finite_deadline(self.started_at, self.budget_seconds)
            if self.deadline is None:
                raise ValueError('invalid cleanup deadline')
        return self.deadline

    def issue(
        self, provision: LightningProvisionRefV1, kind: D11OperationKind,
        session: LightningSessionRefV1 | None = None, recovery_of: str | None = None,
    ) -> LightningOperationRefV1:
        if provision.run_id != self.run_id:
            raise ValueError('run reference mismatch')
        operation = LightningOperationRefV1(provision, uuid.uuid4().hex, kind, session, recovery_of)
        self.operations.append(operation)  # retained before any worker launch/provider call
        return operation

    def grant(self, cancellation_operation: LightningOperationRefV1 | None = None) -> D11CleanupGrant:
        deadline = self.begin()
        return D11CleanupGrant(self.run_id, self.generation, self.clock(), deadline, cancellation_operation)

    def validate_grant(self, grant: D11CleanupGrant) -> bool:
        now = self.clock()
        return (
            isinstance(grant, D11CleanupGrant)
            and grant.run_id == self.run_id and type(grant.generation) is int
            and grant.generation == self.generation and self.deadline is not None
            and grant.deadline_host_monotonic == self.deadline
            and _is_finite_number(grant.issued_at_host_monotonic)
            and 0 <= now - grant.issued_at_host_monotonic <= self.grant_max_age_seconds
            and now < self.deadline
        )


@dataclass(frozen=True, slots=True)
class D11OperationContext:
    operation: LightningOperationRefV1
    work_deadline_host_monotonic: float
    cleanup_budget_seconds: float
    grant_max_age_seconds: float
    poll_interval_seconds: float
    cleanup_grant: D11CleanupGrant | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operation, LightningOperationRefV1):
            raise ValueError('operation reference required')
        for value in (self.work_deadline_host_monotonic, self.cleanup_budget_seconds,
                      self.grant_max_age_seconds, self.poll_interval_seconds):
            if _positive_finite_float(value) is None:
                raise ValueError('explicit finite positive operation parameters required')


@dataclass(frozen=True, slots=True)
class D11OperationReceipt:
    operation: LightningOperationRefV1
    session: LightningSessionRefV1 | None = None
    facts: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operation, LightningOperationRefV1) or (
            self.session is not None and (
                not isinstance(self.session, LightningSessionRefV1)
                or self.session.provision != self.operation.provision
            )
        ):
            raise ValueError('receipt reference mismatch')


@dataclass(frozen=True, slots=True)
class D11ResourceObservation:
    """Independent probe results, not a producer verification label or cancel acknowledgement.

    sealed means the provisioning request can no longer allocate another resource; an empty
    lookup while the request is pending/unknown proves no release. resources must cover every
    allocation under this provision key; active_operations includes outstanding remote work.
    Those capabilities require a concrete observer binding before live use.
    """

    provision: LightningProvisionRefV1
    request_state: Literal['sealed', 'pending', 'unknown']
    resources: tuple[tuple[str, str], ...]
    active_operations: tuple[str, ...]
    observed_at_host_monotonic: float
    source_identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.provision, LightningProvisionRefV1) or self.request_state not in (
            'sealed', 'pending', 'unknown'
        ):
            raise ValueError('invalid observation target/state')
        if type(self.resources) is not tuple or any(
            type(item) is not tuple or len(item) != 2
            or not isinstance(item[0], str) or not isinstance(item[1], str)
            for item in self.resources
        ):
            raise ValueError('resource observations must be exact identity/state pairs')
        identities = [identity for identity, _state in self.resources]
        if len(set(identities)) != len(identities) or len(identities) > 16:
            raise ValueError('bounded unique resource observations required')
        if any(not _is_bounded_fact_token(identity) or state not in ('active', 'terminated', 'unknown')
               for identity, state in self.resources):
            raise ValueError('invalid resource observation')
        if (
            type(self.active_operations) is not tuple
            or len(self.active_operations) > 32
            or any(
                not isinstance(token, str)
                or not _is_bounded_opaque_identifier(token)
                for token in self.active_operations
            )
            or len(set(self.active_operations)) != len(self.active_operations)
        ):
            raise ValueError('invalid operation observations')
        _validate_non_negative_timestamp(self.observed_at_host_monotonic, 'observation time')
        if not _is_bounded_fact_token(self.source_identity):
            raise ValueError('observer identity required')


@dataclass(frozen=True, slots=True)
class D11OfflineConfig:
    cleanup_total_seconds: float
    grant_max_age_seconds: float
    poll_interval_seconds: float
    observer_identity: str

    def __post_init__(self) -> None:
        for value in (self.cleanup_total_seconds, self.grant_max_age_seconds, self.poll_interval_seconds):
            if _positive_finite_float(value) is None:
                raise ValueError('explicit finite positive offline parameters required')
        if not _is_bounded_fact_token(self.observer_identity):
            raise ValueError('explicit independent fixture observer identity required')


@dataclass(frozen=True, slots=True)
class D11DispatchInputs:
    request: VisionUnderstandingRequestV2
    runtime_config: QwenVisionRuntimeConfig
    content_policy: ObservableContentPolicyV1
    prompt: str
    config: Feat018BoundedRunnerConfig
    synthetic_session_id: str


class D11SDKOperationHandle(Protocol):
    """Owned by the worker from start until close returns.

    wait emits accepted supervisor metadata and requests a grant BEFORE terminal cleanup,
    including inner terminal cleanup. It must not run the session supervisor inside this host
    bridge. cancel requires a parent-issued reference. Lost handle/response leaves that
    reference owned by the parent for fresh cancel/reconcile; close alone proves no remote exit.
    wait/cancel/close belong to the original referenced operation. close releases the SDK
    handle only; a close failure keeps residual ownership and prevents successful finalization.
    """

    def wait(self, *, timeout_seconds: float, emit: Callable[[Mapping[str, object]], object]) -> object: ...
    def cancel(self, *, operation: LightningOperationRefV1, timeout_seconds: float) -> object: ...
    def close(self) -> None: ...


class LightningSessionControllerV1(Protocol):
    """Executor retains allocation/operation state independently of a disposable SDK worker.

    Provision and dispatch recovery keys must be honored without duplicate side effects.
    cancel targets recovery_of, reconcile discovers all allocation under the provision key,
    and terminate accepts a known session or a pending provision key. Sealing pending requests
    and independent complete observation are provider capabilities, currently UNKNOWN/UNBOUND.
    A receipt reports facts; it does not independently prove remote cleanup.
    """
    def provision(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
                  inputs: D11DispatchInputs | None) -> D11SDKOperationHandle: ...
    def wait_ready(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
                   inputs: D11DispatchInputs | None) -> D11SDKOperationHandle: ...
    def reconcile(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
                  inputs: D11DispatchInputs | None) -> D11SDKOperationHandle: ...
    def terminate(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
                  inputs: D11DispatchInputs | None) -> D11SDKOperationHandle: ...
    def cancel(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
               inputs: D11DispatchInputs | None) -> D11SDKOperationHandle: ...


class LightningAdapterDispatchV1(Protocol):
    """Start one referenced session operation; retries never create another dispatch key."""
    def start(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
              inputs: D11DispatchInputs | None) -> D11SDKOperationHandle: ...


class LightningResourceObserverV1(Protocol):
    def observe(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
                inputs: D11DispatchInputs | None) -> D11SDKOperationHandle: ...


@dataclass(frozen=True, slots=True)
class D11CleanupReport:
    deadline_host_monotonic: float
    generation: int
    operations: tuple[LightningOperationRefV1, ...]
    unresolved_operations: tuple[LightningOperationRefV1, ...]
    observation: D11ResourceObservation | None
    verification: Literal['VERIFIED_OFFLINE', 'UNVERIFIED', 'UNKNOWN']
    failure_codes: tuple[str, ...]
    dispatch_invocation_accepted: bool
    generation_progress_known: bool

    @property
    def resources_released(self) -> bool:
        # The observer is a separately injected read seam. A producer receipt, verified label,
        # cancel ACK or absent session reference cannot satisfy this predicate.
        return (
            self.observation is not None
            and self.verification == 'VERIFIED_OFFLINE'
            and not self.unresolved_operations and not self.failure_codes
            and self.observation.request_state == 'sealed'
            and not self.observation.active_operations
            and all(state == 'terminated' for _, state in self.observation.resources)
        )


def _d11_ref_payload(operation: LightningOperationRefV1) -> dict[str, object]:
    return {'run_id': operation.provision.run_id, 'provision_token': operation.provision.token,
            'operation_token': operation.token, 'operation_kind': operation.kind.value,
            'resource_identity': operation.session.resource_identity if operation.session else None,
            'recovery_of': operation.recovery_of}


def _d11_ref_from_payload(value: object) -> LightningOperationRefV1:
    payload = _payload_mapping(value)
    if payload is None or not _payload_has_exact_keys(payload, {
        'run_id', 'provision_token', 'operation_token', 'operation_kind', 'resource_identity', 'recovery_of'
    }):
        raise ValueError('invalid operation reference')
    provision = LightningProvisionRefV1(payload['run_id'], payload['provision_token'])
    session = (None if payload['resource_identity'] is None else
               LightningSessionRefV1(provision, payload['resource_identity']))
    return LightningOperationRefV1(provision, payload['operation_token'],
                                  D11OperationKind(payload['operation_kind']), session, payload['recovery_of'])


def _d11_result_payload(value: object) -> dict[str, object]:
    if isinstance(value, D11ResourceObservation):
        return {'type': 'observation', 'run_id': value.provision.run_id,
                'provision_token': value.provision.token, 'request_state': value.request_state,
                'resources': [list(item) for item in value.resources],
                'active_operations': list(value.active_operations),
                'observed_at': value.observed_at_host_monotonic, 'source_identity': value.source_identity}
    if not isinstance(value, D11OperationReceipt):
        raise ValueError('typed D11 receipt required')
    value.__post_init__()  # do not normalize a foreign session target during IPC encoding
    facts = value.facts
    if isinstance(facts, SupervisorRunResult):
        fact_payload = {'fact_type': 'supervisor', 'state': facts.final_state.value,
                        'attempt_count': facts.attempt_count, 'terminal': facts.terminal_outcome,
                        'cleanup': facts.cleanup_status.value, 'outcome': facts.effective_outcome.value,
                        'raw_status': facts.raw_status, 'failed': facts.primary_failure_reason is not None,
                        'cleanup_failed': facts.cleanup_failure is not None,
                        'd9_observations': [_d9_observation_frame(item) for item in facts.d9_observations],
                        'd9_failures': [item.value for item in facts.d9_failure_codes]}
    else:
        fact_payload = None if facts is None else _lightning_fact_to_payload(facts)
        if facts is not None and fact_payload is None:
            raise ValueError('unsupported receipt facts')
    return {'type': 'receipt', 'operation': _d11_ref_payload(value.operation),
            'session': value.session.resource_identity if value.session else None, 'facts': fact_payload}


def _d11_result_from_payload(value: object) -> D11OperationReceipt | D11ResourceObservation:
    payload = _payload_mapping(value)
    if payload is None:
        raise ValueError('invalid D11 result')
    if payload.get('type') == 'observation' and _payload_has_exact_keys(payload, {
        'type', 'run_id', 'provision_token', 'request_state', 'resources', 'active_operations',
        'observed_at', 'source_identity'
    }):
        if not isinstance(payload['resources'], list) or not isinstance(payload['active_operations'], list):
            raise ValueError('invalid observation collection')
        resources = payload['resources']
        active_operations = payload['active_operations']
        if any(
            type(item) is not list or len(item) != 2
            or not isinstance(item[0], str) or not isinstance(item[1], str)
            for item in resources
        ) or any(not isinstance(token, str) for token in active_operations):
            raise ValueError('invalid observation entry')
        return D11ResourceObservation(LightningProvisionRefV1(payload['run_id'], payload['provision_token']),
            payload['request_state'], tuple((item[0], item[1]) for item in resources),
            tuple(active_operations), payload['observed_at'], payload['source_identity'])
    if not _payload_has_exact_keys(payload, {'type', 'operation', 'session', 'facts'}) or payload['type'] != 'receipt':
        raise ValueError('invalid receipt keys')
    operation = _d11_ref_from_payload(payload['operation'])
    session = (None if payload['session'] is None else
               LightningSessionRefV1(operation.provision, payload['session']))
    facts_payload = payload['facts']
    facts = None
    if isinstance(facts_payload, dict) and facts_payload.get('fact_type') == 'supervisor':
        if not _payload_has_exact_keys(facts_payload, {'fact_type', 'state', 'attempt_count', 'terminal',
            'cleanup', 'outcome', 'raw_status', 'failed', 'cleanup_failed', 'd9_observations', 'd9_failures'}):
            raise ValueError('invalid supervisor keys')
        if type(facts_payload['failed']) is not bool or type(facts_payload['cleanup_failed']) is not bool:
            raise ValueError('invalid supervisor flags')
        observations = tuple(_d9_observation_from_frame(item) for item in facts_payload['d9_observations'])
        if any(item is None for item in observations):
            raise ValueError('invalid D9 observation')
        facts = SupervisorRunResult(final_state=ProgressState(facts_payload['state']),
            attempt_count=facts_payload['attempt_count'], terminal_outcome=facts_payload['terminal'],
            cleanup_status=CleanupStatus(facts_payload['cleanup']),
            effective_outcome=EffectiveOutcome(facts_payload['outcome']), raw_status=facts_payload['raw_status'],
            primary_failure_reason='remote executor failed' if facts_payload['failed'] else None,
            d9_observations=observations,
            d9_failure_codes=tuple(D9StreamFailureCode(item) for item in facts_payload['d9_failures']))
        if facts_payload['cleanup_failed']:
            facts = replace(facts, cleanup_status=CleanupStatus.CLEANUP_FAILED,
                            effective_outcome=EffectiveOutcome.CLEANUP_FAILED)
    elif facts_payload is not None:
        facts = _lightning_fact_from_payload(facts_payload)
        if facts is None:
            raise ValueError('invalid receipt facts')
    return D11OperationReceipt(operation, session, facts)


def _d11_grant_payload(grant: D11CleanupGrant) -> dict[str, object]:
    return {
        'run_id': grant.run_id, 'generation': grant.generation,
        'issued_at': grant.issued_at_host_monotonic, 'deadline': grant.deadline_host_monotonic,
        'cancel': None if grant.cancellation_operation is None else
        _d11_ref_payload(grant.cancellation_operation),
    }


def _d11_grant_from_payload(value: object, context: D11OperationContext) -> D11CleanupGrant:
    payload = _payload_mapping(value)
    if payload is None or not _payload_has_exact_keys(
        payload, {'run_id', 'generation', 'issued_at', 'deadline', 'cancel'}
    ):
        raise ValueError('invalid cleanup grant')
    grant = D11CleanupGrant(
        payload['run_id'], payload['generation'], payload['issued_at'], payload['deadline'],
        None if payload['cancel'] is None else _d11_ref_from_payload(payload['cancel']),
    )
    now = time.monotonic()
    if (
        grant.run_id != context.operation.provision.run_id or type(grant.generation) is not int
        or grant.generation != 1 or not _is_finite_number(grant.issued_at_host_monotonic)
        or not _is_finite_number(grant.deadline_host_monotonic)
        or not 0 <= now - grant.issued_at_host_monotonic <= context.grant_max_age_seconds
        or now >= grant.deadline_host_monotonic
    ):
        raise ValueError('stale cleanup grant')
    if context.cleanup_grant is not None and (
        grant.deadline_host_monotonic != context.cleanup_grant.deadline_host_monotonic
        or grant.generation != context.cleanup_grant.generation
    ):
        raise ValueError('cleanup grant extends existing window')
    cancel = grant.cancellation_operation
    if cancel is not None and (
        cancel.kind is not D11OperationKind.CANCEL or cancel.provision != context.operation.provision
        or cancel.recovery_of != context.operation.token
    ):
        raise ValueError('cancel grant target mismatch')
    return grant


def _d11_operation_worker_entry(
    connection: BoundedConnection,
    seam: object,
    operation: LightningOperationRefV1,
    context: D11OperationContext,
    inputs: D11DispatchInputs | None,
    gate_timeout: float,
) -> None:
    """Contained SDK bridge only. Remote execution owns its own supervisor/containment."""
    posix_worker_self_contain()
    handle: D11SDKOperationHandle | None = None
    result: object | None = None
    failure = False
    close_failed = False
    grant = context.cleanup_grant

    def emit(event: Mapping[str, object]) -> object:
        nonlocal grant
        if event.get('kind') == 'progress' and set(event) == {'kind', 'event'}:
            connection.send_frame({'kind': 'D11_PROGRESS', 'event': event['event']})
            return None
        if event.get('kind') != 'cleanup_intent' or set(event) != {'kind'}:
            raise Feat018ProtocolViolationError('invalid D11 callback event')
        connection.send_frame({'kind': 'D11_CLEANUP_INTENT'})
        # This handshake is before SDK/remote terminal cleanup. The host still preempts a
        # noncooperative wait/cancel. No response means no verified remote release.
        limit = grant.deadline_host_monotonic if grant else context.work_deadline_host_monotonic
        remaining = max(0.0, limit - time.monotonic())
        response = connection.recv_frame(remaining)
        if not isinstance(response, dict) or set(response) != {'kind', 'grant'} or (
            response['kind'] != 'D11_CLEANUP_GRANT'
        ):
            raise Feat018ProtocolViolationError('missing cleanup grant')
        candidate = _d11_grant_from_payload(response['grant'], context)
        if grant is not None and candidate.deadline_host_monotonic != grant.deadline_host_monotonic:
            raise Feat018ProtocolViolationError('repeated cleanup intent changed deadline')
        grant = candidate
        return grant

    try:
        release = connection.recv_frame(gate_timeout)
        if not isinstance(release, dict) or set(release) != {'kind'} or release['kind'] != 'CONTAINMENT_READY':
            return
        if time.monotonic() >= context.work_deadline_host_monotonic:
            return
        if grant is not None:
            grant = _d11_grant_from_payload(_d11_grant_payload(grant), context)
        connection.send_frame({'kind': 'D11_CALL_STARTED'})
        method_name = 'start' if operation.kind is D11OperationKind.DISPATCH else operation.kind.value
        handle = getattr(seam, method_name)(operation=operation, context=context, inputs=inputs)
        if handle is not None:
            connection.send_frame({'kind': 'D11_HANDLE_STARTED'})
        if not all(callable(getattr(handle, name, None)) for name in ('wait', 'cancel', 'close')):
            raise Feat018ProtocolViolationError('SDK handle lifecycle missing')
        result = handle.wait(
            timeout_seconds=max(0.0, context.work_deadline_host_monotonic - time.monotonic()),
            emit=emit,
        )
    except Exception:
        failure = True
        if handle is not None:
            try:
                cancellation_grant = cast(D11CleanupGrant, emit({'kind': 'cleanup_intent'}))
                if cancellation_grant.cancellation_operation is None:
                    raise ValueError('parent cancel reference missing')
                handle.cancel(
                    operation=cancellation_grant.cancellation_operation,
                    timeout_seconds=cancellation_grant.remaining(time.monotonic()),
                )
            except Exception:
                close_failed = True
    finally:
        if handle is not None:
            try:
                handle.close()
            except Exception:
                close_failed = True
        try:
            if failure or close_failed:
                connection.send_frame({'kind': 'D11_FAILED', 'close_failed': close_failed})
            elif result is not None:
                connection.send_frame({'kind': 'D11_RESULT', 'result': _d11_result_payload(result)})
        except Exception:
            pass  # parent retains operation reference on EOF/missing/malformed receipt


def _invoke_d11_operation(
    boundary: Feat018LightningLifecycleProcessBoundary,
    operation: LightningOperationRefV1,
    context: D11OperationContext,
    inputs: D11DispatchInputs | None,
    on_progress: Callable[[Mapping[str, object]], None] | None,
    window: D11CleanupWindow,
) -> D11OperationReceipt | D11ResourceObservation:
    if context.operation != operation or operation not in window.operations:
        raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED)
    if window.deadline is not None:
        context = replace(context, work_deadline_host_monotonic=min(
            context.work_deadline_host_monotonic, window.deadline,
        ))
    containment: ContainmentBackend | None = None
    process: ProcessHandle | None = None
    connection: BoundedConnection | None = None
    result: D11OperationReceipt | D11ResourceObservation | None = None
    failure_code: Feat018LiveSmokeFailureCode | None = None
    owned_failure: Feat018CleanupFailedError | None = None
    cleanup_started_for_operation = context.cleanup_grant is not None
    try:
        remaining = context.work_deadline_host_monotonic - boundary.clock()
        if _positive_finite_float(remaining) is None:
            raise TimeoutError
        if context.cleanup_grant is not None and not window.validate_grant(context.cleanup_grant):
            raise ValueError('stale cleanup context')
        containment = boundary.containment_factory()
        containment.create()
        launcher = boundary.launcher or MultiprocessingProcessLauncher(
            max_envelope_bytes=boundary.max_envelope_bytes, clock=boundary.clock,
            cleanup_deadline=lambda: window.begin('launch_failure'),
        )
        process, connection = launcher.launch(
            _d11_operation_worker_entry,
            (boundary.controller, operation, context, inputs,
             min(boundary.containment_setup_timeout_seconds, remaining)),
        )
        remaining = context.work_deadline_host_monotonic - boundary.clock()
        if _positive_finite_float(remaining) is None:
            raise TimeoutError
        if not containment.confirm_worker_contained(
            process, timeout=min(boundary.containment_setup_timeout_seconds, remaining),
            retry_interval=boundary.confirmation_retry_interval_seconds,
        ):
            raise Feat018ContainmentError('D11 containment gate failed')
        connection.send_frame({'kind': 'CONTAINMENT_READY'})
        active_deadline = min(context.work_deadline_host_monotonic, window.deadline) if (
            window.deadline is not None
        ) else context.work_deadline_host_monotonic
        call_started = False
        handle_started = False
        cancel: LightningOperationRefV1 | None = None
        intent_count = 0
        while True:
            remaining = active_deadline - boundary.clock()
            if _positive_finite_float(remaining) is None:
                raise TimeoutError
            frame = connection.recv_frame(remaining)
            if frame is None:
                if not process.is_alive():
                    raise EOFError
                remaining_after_receive = active_deadline - boundary.clock()
                if _positive_finite_float(remaining_after_receive) is None:
                    raise TimeoutError
                boundary.sleep(min(context.poll_interval_seconds, remaining_after_receive))
                continue
            if boundary.clock() >= active_deadline:
                raise TimeoutError
            kind = frame.get('kind')
            if kind == 'D11_CALL_STARTED' and set(frame) == {'kind'} and not call_started:
                call_started = True
            elif kind == 'D11_HANDLE_STARTED' and set(frame) == {'kind'} and call_started and not handle_started:
                handle_started = True
            elif kind == 'D11_PROGRESS' and set(frame) == {'kind', 'event'} and handle_started:
                if operation.kind is not D11OperationKind.DISPATCH or on_progress is None:
                    raise ValueError('unexpected progress')
                if not isinstance(frame['event'], Mapping):
                    raise ValueError('invalid progress')
                on_progress(frame['event'])
            elif kind == 'D11_CLEANUP_INTENT' and set(frame) == {'kind'} and handle_started:
                intent_count += 1
                if intent_count > 16:
                    raise ValueError('cleanup intent protocol limit exceeded')
                cleanup_started_for_operation = True
                deadline = window.begin('worker_cleanup_intent')
                if cancel is None:
                    cancel = window.issue(operation.provision, D11OperationKind.CANCEL,
                                          operation.session, operation.token)
                grant = window.grant(cancel)
                connection.send_frame({'kind': 'D11_CLEANUP_GRANT', 'grant': _d11_grant_payload(grant)})
                # A work-to-cleanup handoff may consume the cleanup window. An operation
                # already doing cleanup also retains its earlier phase cap.
                active_deadline = (min(active_deadline, deadline)
                                   if context.cleanup_grant is not None else deadline)
            elif kind == 'D11_RESULT' and set(frame) == {'kind', 'result'} and handle_started:
                if operation.kind is D11OperationKind.DISPATCH and not cleanup_started_for_operation:
                    raise ValueError('dispatch terminal cleanup handoff missing')
                result = _d11_result_from_payload(frame['result'])
                if isinstance(result, D11OperationReceipt) and (
                    result.operation != operation or (
                        operation.session is not None and result.session != operation.session
                    )
                ):
                    raise ValueError('receipt reference mismatch')
                if isinstance(result, D11ResourceObservation) and (
                    operation.kind is not D11OperationKind.OBSERVE or result.provision != operation.provision
                ):
                    raise ValueError('observation reference mismatch')
                break
            elif kind == 'D11_FAILED' and set(frame) == {'kind', 'close_failed'} and type(frame['close_failed']) is bool:
                failure_code = Feat018LiveSmokeFailureCode.LIFECYCLE_RESULT_INVALID
                if frame['close_failed']:
                    owned_failure = Feat018CleanupFailedError('SDK handle cleanup failed')
                break
            else:
                raise ValueError('D11 protocol failed')
    except Feat018CleanupFailedError as error:
        owned_failure = error
        failure_code = Feat018LiveSmokeFailureCode.LIFECYCLE_CLEANUP_FAILED
    except TimeoutError:
        failure_code = {
            D11OperationKind.PROVISION: Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT,
            D11OperationKind.WAIT_READY: Feat018LiveSmokeFailureCode.READY_TIMEOUT,
            D11OperationKind.DISPATCH: Feat018LiveSmokeFailureCode.ADAPTER_CAP_EXCEEDED,
        }.get(operation.kind, Feat018LiveSmokeFailureCode.SESSION_TERMINATION_TIMEOUT)
    except EOFError:
        failure_code = Feat018LiveSmokeFailureCode.LIFECYCLE_WORKER_DIED
    except Exception:
        failure_code = Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
    finally:
        if failure_code is not None or owned_failure is not None or cleanup_started_for_operation:
            cleanup_deadline = window.begin('operation_unwind')
        else:
            # Successful intermediate retirement consumes the current work deadline.
            cleanup_deadline = context.work_deadline_host_monotonic
        resource_error = boundary._cleanup_resources(
            process, connection, containment, cleanup_deadline_monotonic=cleanup_deadline,
        )
        if resource_error is not None:
            window.begin('resource_cleanup_failed')
            if owned_failure is None:
                owned_failure = resource_error
            else:
                owned_failure.owned_connections += resource_error.owned_connections
                owned_failure.owned_containments += resource_error.owned_containments
                if owned_failure.owned_process is None:
                    owned_failure.owned_process = resource_error.owned_process
        if boundary.clock() >= cleanup_deadline:
            owned_failure = owned_failure or Feat018CleanupFailedError('cleanup deadline exhausted')
    if owned_failure is not None:
        raise Feat018LifecycleOperationError(
            failure_code or Feat018LiveSmokeFailureCode.LIFECYCLE_CLEANUP_FAILED,
            cleanup_failure=owned_failure,
        )
    if failure_code is not None or result is None:
        raise Feat018LifecycleOperationError(
            failure_code or Feat018LiveSmokeFailureCode.LIFECYCLE_RESULT_INVALID
        )
    return result


def run_offline_live_smoke(
    request: VisionUnderstandingRequestV2,
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    *,
    controller: LightningSessionControllerV1 | None = None,
    config: Feat018LiveSmokeConfig | None = None,
    session_id: str | None = None,
    preflight: LightningPreflight | None = None,
    finalizer: LightningSmokeFinalizer | None = None,
    adapter_dispatch: LightningAdapterDispatchV1 | None = None,
    observer: LightningResourceObserverV1 | None = None,
    d11_config: D11OfflineConfig | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Feat018LiveSmokeResult:
    """Offline fixture coordinator with explicit references and a contained SDK bridge.

    This implementation binds no provider capability, credentials or live numeric budgets.
    D11OfflineConfig supplies finite fixture parameters; its observation verdict is offline.
    There is no legacy synchronous callback fallback. Only bounded metadata leaves SDK workers.

    adapter_call_count accepts 1 when the parent invokes the one dispatch boundary (including
    launch/input rejection); attempt_count accepts 1/2 only through supervisor progress received
    before the work deadline and first cleanup intent. None means no accepted progress and is
    UNKNOWN about actual remote generation. A receipt never fills missing counters.
    """
    rejected = Feat018LiveSmokeResult(
        effective_outcome=EffectiveOutcome.FAILED, adapter_call_count=0, attempt_count=None,
        cleanup_status=CleanupStatus.SUCCEEDED, failure_code=Feat018LiveSmokeFailureCode.NOT_AUTHORIZED,
    )
    if not (
        _is_bounded_opaque_identifier(session_id) and isinstance(config, Feat018LiveSmokeConfig)
        and isinstance(d11_config, D11OfflineConfig)
        and all(callable(getattr(controller, name, None)) for name in (
            'provision', 'wait_ready', 'cancel', 'reconcile', 'terminate'
        ))
        and callable(getattr(adapter_dispatch, 'start', None))
        and callable(getattr(observer, 'observe', None)) and observer is not controller
        and observer is not adapter_dispatch
        and callable(getattr(preflight, 'verify', None)) and callable(getattr(finalizer, 'finalize', None))
    ):
        return rejected
    assert config is not None and d11_config is not None and isinstance(session_id, str)
    if any(_positive_finite_float(value) is None for value in (
        config.session_provision_timeout_seconds, config.session_ttl_seconds,
        config.gpu_minute_cap, config.session_termination_deadline_seconds,
        config.bounded_runner_config.total_adapter_cap_seconds,
        config.bounded_runner_config.containment_setup_timeout_seconds,
        config.bounded_runner_config.posix_confirmation_retry_interval_seconds,
    )):
        return rejected
    try:
        if not _preflight_was_verified(preflight.verify(synthetic_session_id=session_id), session_id):
            return replace(rejected, failure_code=Feat018LiveSmokeFailureCode.PREFLIGHT_NOT_AUTHORIZED)
        window = D11CleanupWindow(session_id, d11_config.cleanup_total_seconds,
                                  d11_config.grant_max_age_seconds, clock)
        provision = LightningProvisionRefV1(session_id, uuid.uuid4().hex)
        # Construction is before the authorized transition; no provider effects here.
        boundaries = {}
        for kind, seam in (('controller', controller), ('dispatch', adapter_dispatch), ('observer', observer)):
            boundaries[kind] = Feat018LightningLifecycleProcessBoundary(
                controller=cast(Any, seam),
                max_envelope_bytes=config.bounded_runner_config.ipc_envelope_max_bytes,
                containment_factory=create_platform_containment,
                cleanup_deadline_seconds=d11_config.cleanup_total_seconds,
                containment_setup_timeout_seconds=config.bounded_runner_config.containment_setup_timeout_seconds,
                confirmation_retry_interval_seconds=config.bounded_runner_config.posix_confirmation_retry_interval_seconds,
                clock=clock,
            )
    except Exception:
        return replace(rejected, failure_code=Feat018LiveSmokeFailureCode.PREFLIGHT_FAILED)

    cleanup_failures: list[Feat018CleanupFailedError] = []
    cleanup_codes: list[str] = []
    completed: set[str] = set()
    session: LightningSessionRefV1 | None = None
    placement: LightningPlacementFacts | None = None
    observation: D11ResourceObservation | None = None
    adapter_result: SupervisorRunResult | None = None
    machine: Feat018ProgressStateMachine | None = None
    adapter_count = 0
    ready = False
    ready_at: float | None = None
    failure_code: Feat018LiveSmokeFailureCode | None = None
    provision_started = clock()
    ready_deadline = _add_finite_deadline(provision_started, float(config.session_provision_timeout_seconds))
    gpu_start: float | None = None
    gpu_deadline: float | None = None
    ttl_start: float | None = None
    ttl_deadline: float | None = None
    adapter_start: float | None = None
    adapter_deadline: float | None = None
    dispatch_ref: LightningOperationRefV1 | None = None

    def invoke(
        kind: D11OperationKind, deadline: float,
        target: LightningSessionRefV1 | None = None, recovery_of: str | None = None,
    ) -> D11OperationReceipt | D11ResourceObservation:
        operation = window.issue(provision, kind, target, recovery_of)
        grant = window.grant() if window.deadline is not None else None
        context = D11OperationContext(operation, deadline, d11_config.cleanup_total_seconds,
                                      d11_config.grant_max_age_seconds, d11_config.poll_interval_seconds, grant)
        key = 'observer' if kind is D11OperationKind.OBSERVE else 'controller'
        result = boundaries[key].invoke_reference(operation, context, window=window)
        completed.add(operation.token)
        return result

    def record_error(error: Feat018LifecycleOperationError, *, cleanup: bool) -> None:
        nonlocal failure_code
        if failure_code is None:
            failure_code = error.failure_code
        if error.cleanup_failure is not None:
            cleanup_failures.append(error.cleanup_failure)
        if cleanup or error.cleanup_status is CleanupStatus.CLEANUP_FAILED:
            cleanup_codes.append(error.failure_code.value)

    def accept_progress(frame: Mapping[str, object]) -> None:
        assert machine is not None
        # Cleanup handoff seals cardinality, independently of any remote receipt summary.
        if window.deadline is not None:
            return
        event = _progress_event_from_frame(frame)
        if event is None or machine.accept(event, acceptance_time=clock()) is not AcceptanceResult.ACCEPTED:
            raise Feat018ProtocolViolationError('D11 progress transition rejected')

    # AUTHORIZED_RUN_ATTEMPT_BEGINS. All operations below are recorded before launch.
    try:
        if ready_deadline is None:
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT)
        receipt = invoke(D11OperationKind.PROVISION, ready_deadline)
        if not isinstance(receipt, D11OperationReceipt) or receipt.session is None:
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.PROVISION_FACTS_MISSING)
        # Preserve a target for cleanup before placement/billing admission checks.
        session = receipt.session
        if window.deadline is not None:
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.PROVISION_FAILED)
        facts = receipt.facts
        if not isinstance(facts, LightningProvisionFacts) or not facts.allocation_confirmed or (
            facts.session_identity != session.resource_identity
        ):
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.PROVISION_FACTS_MISSING)
        placement = facts.placement
        if not _placement_matches_approval(placement, config.placement_approval):
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.PLACEMENT_MISMATCH)
        gpu_start = facts.gpu_minute_budget_start_monotonic
        if gpu_start is None or not provision_started <= gpu_start <= clock():
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.PROVISION_FACTS_MISSING)
        gpu_deadline = _add_finite_deadline(gpu_start, float(config.gpu_minute_cap) * 60)
        if gpu_deadline is None:
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.PROVISION_FACTS_MISSING)
        ready_receipt = invoke(D11OperationKind.WAIT_READY, min(ready_deadline, gpu_deadline), session)
        if window.deadline is not None:
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.READY_FAILED)
        if not isinstance(ready_receipt, D11OperationReceipt) or not isinstance(ready_receipt.facts, LightningReadyFacts):
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.READY_FACTS_MISSING)
        ready_facts = ready_receipt.facts
        if ready_facts.readiness is not LightningSessionReadiness.SESSION_READY:
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.SESSION_NOT_READY)
        lifecycle_code = _lifecycle_failure_code(
            ready_facts.lifecycle, provision_facts=facts, provision_start=provision_started,
            ready_finished=clock(), ready_deadline=ready_deadline,
            session_ttl_seconds=config.session_ttl_seconds,
        )
        if lifecycle_code is not None:
            raise Feat018LifecycleOperationError(lifecycle_code)
        assert ready_facts.lifecycle is not None
        ready = True
        ready_at = ready_facts.lifecycle.session_ready_at_monotonic
        ttl_start = ready_facts.lifecycle.session_ttl_start_monotonic
        ttl_deadline = ready_facts.lifecycle.session_ttl_deadline_monotonic
        cap_code = _active_cap_failure_code(clock(), ttl_deadline=ttl_deadline, gpu_budget_deadline=gpu_deadline)
        if cap_code is not None:
            raise Feat018LifecycleOperationError(cap_code)
        adapter_start = clock()
        adapter_deadline = _add_finite_deadline(adapter_start, config.bounded_runner_config.total_adapter_cap_seconds)
        if adapter_deadline is None:
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.ADAPTER_CAP_EXCEEDED)
        work_deadline = min(adapter_deadline, ttl_deadline, gpu_deadline)
        machine = Feat018ProgressStateMachine(cap_deadline_monotonic=work_deadline)
        dispatch_ref = window.issue(provision, D11OperationKind.DISPATCH, session)
        context = D11OperationContext(dispatch_ref, work_deadline, d11_config.cleanup_total_seconds,
                                      d11_config.grant_max_age_seconds, d11_config.poll_interval_seconds)
        inputs = D11DispatchInputs(request, runtime_config, content_policy, prompt,
                                   config.bounded_runner_config, session_id)
        adapter_count = 1  # one dispatch-boundary invocation; no outer retry
        candidate = boundaries['dispatch'].invoke_reference(
            dispatch_ref, context, inputs=inputs, on_progress=accept_progress, window=window,
        )
        completed.add(dispatch_ref.token)
        if not isinstance(candidate, D11OperationReceipt) or not _supervisor_result_is_valid(candidate.facts):
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.ADAPTER_RESULT_INVALID)
        adapter_result = cast(SupervisorRunResult, candidate.facts)
        if adapter_result.cleanup_status is CleanupStatus.CLEANUP_FAILED:
            cleanup_codes.append(Feat018LiveSmokeFailureCode.ADAPTER_CLEANUP_FAILED.value)
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.ADAPTER_CLEANUP_FAILED)
        if (
            machine.state is not ProgressState.TERMINAL
            or adapter_result.attempt_count != machine.attempt_count
            or adapter_result.terminal_outcome != machine.terminal_outcome
            or adapter_result.raw_status != machine.raw_status
        ):
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.ADAPTER_RESULT_INVALID)
        if not _adapter_result_is_accepted_success(adapter_result):
            raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.ADAPTER_FAILED)
    except Feat018LifecycleOperationError as error:
        record_error(error, cleanup=False)
    except Exception:
        failure_code = failure_code or Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED
    finally:
        deadline = window.begin('coordinator_terminal')
        # Fresh operations use parent references even if SDK start/handle/response was lost.
        outstanding = tuple(operation for operation in window.operations
                            if operation.token not in completed and operation.kind in (
                                D11OperationKind.PROVISION, D11OperationKind.WAIT_READY, D11OperationKind.DISPATCH
                            ))
        for operation in outstanding:
            try:
                invoke(D11OperationKind.CANCEL, deadline, operation.session, operation.token)
            except Feat018LifecycleOperationError as error:
                record_error(error, cleanup=True)
        try:
            reconciled = invoke(D11OperationKind.RECONCILE, deadline, session)
            if isinstance(reconciled, D11OperationReceipt) and reconciled.session is not None:
                if session is not None and reconciled.session != session:
                    raise Feat018LifecycleOperationError(Feat018LiveSmokeFailureCode.SESSION_IDENTITY_MISMATCH)
                session = reconciled.session
        except Feat018LifecycleOperationError as error:
            record_error(error, cleanup=True)
        try:
            invoke(D11OperationKind.TERMINATE, min(deadline, clock() + config.session_termination_deadline_seconds), session)
        except Feat018LifecycleOperationError as error:
            record_error(error, cleanup=True)
        observation_start = clock()
        try:
            observed = invoke(D11OperationKind.OBSERVE, deadline, session)
            if isinstance(observed, D11ResourceObservation) and (
                observed.provision == provision and observed.source_identity == d11_config.observer_identity
                and observation_start <= observed.observed_at_host_monotonic <= clock() < deadline
            ):
                observation = observed
            else:
                cleanup_codes.append('OBSERVATION_INVALID')
        except Feat018LifecycleOperationError as error:
            record_error(error, cleanup=True)
        for error in cleanup_failures:
            error.retry_cleanup(grace_seconds=0.1, kill_join_seconds=0.1,
                                cleanup_deadline_monotonic=deadline, clock=clock)

    released = observation is not None and observation.request_state == 'sealed' and (
        not observation.active_operations and all(state == 'terminated' for _, state in observation.resources)
        and (session is None or any(identity == session.resource_identity for identity, _ in observation.resources))
    )
    if not released:
        cleanup_codes.append('REMOTE_RELEASE_UNVERIFIED')
    if cleanup_failures:
        cleanup_codes.append('LOCAL_RELEASE_FAILED')
    if clock() >= deadline:
        cleanup_codes.append('CLEANUP_DEADLINE_EXHAUSTED')
    unresolved = () if released and not cleanup_codes and not cleanup_failures else tuple(window.operations)
    report = D11CleanupReport(deadline, window.generation, tuple(window.operations), unresolved,
        observation, 'VERIFIED_OFFLINE' if released else ('UNKNOWN' if observation is None else 'UNVERIFIED'),
        tuple(dict.fromkeys(cleanup_codes)), adapter_count == 1,
        machine is not None and machine.attempt_count is not None)
    cleanup_status = CleanupStatus.SUCCEEDED if report.resources_released else CleanupStatus.CLEANUP_FAILED
    if cleanup_status is CleanupStatus.CLEANUP_FAILED and failure_code is None:
        failure_code = Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED
    outcome = (EffectiveOutcome.CLEANUP_FAILED if cleanup_status is CleanupStatus.CLEANUP_FAILED else
               EffectiveOutcome.SUCCEEDED if failure_code is None else EffectiveOutcome.FAILED)
    result = Feat018LiveSmokeResult(
        effective_outcome=outcome, adapter_call_count=adapter_count,
        attempt_count=machine.attempt_count if machine else None,
        cleanup_status=cleanup_status, failure_code=failure_code, session_ready=ready,
        provision_start_monotonic=provision_started, ready_deadline_monotonic=ready_deadline,
        ready_at_monotonic=ready_at, session_ready_at_monotonic=ready_at,
        gpu_minute_budget_start_monotonic=gpu_start, session_ttl_start_monotonic=ttl_start,
        session_ttl_deadline_monotonic=ttl_deadline, adapter_start_monotonic=adapter_start,
        total_adapter_cap_deadline_monotonic=adapter_deadline, session_termination_deadline_monotonic=deadline,
        adapter_result=adapter_result, session_identity=session.resource_identity if session else None,
        placement=placement, cleanup_failures=tuple(cleanup_failures), preflight_verified=True,
        d11_report=report,
    )
    try:
        finalization = finalizer.finalize(result=result)
        verified = _finalization_was_verified(finalization)
    except Exception:
        verified = False
    return replace(result, finalization_verified=verified,
        effective_outcome=outcome if verified or outcome is EffectiveOutcome.CLEANUP_FAILED else EffectiveOutcome.FAILED,
        failure_code=failure_code if verified else Feat018LiveSmokeFailureCode.FINALIZATION_FAILED)


def _is_live_attempt_profile_admissible(config: Feat018BoundedRunnerConfig) -> bool:
    """The D1 live profile requires the plan's exact 120-second per-attempt value."""
    return (
        isinstance(config, Feat018BoundedRunnerConfig)
        and type(config.per_attempt_timeout_seconds) in (int, float)
        and math.isfinite(float(config.per_attempt_timeout_seconds))
        and config.per_attempt_timeout_seconds == 120.0
    )


def run_live_smoke(
    request: VisionUnderstandingRequestV2,
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    *,
    controller: LightningSessionControllerV1 | None = None,
    config: Feat018LiveSmokeConfig | None = None,
    session_id: str | None = None,
    preflight: LightningPreflight | None = None,
    finalizer: LightningSmokeFinalizer | None = None,
    adapter_dispatch: LightningAdapterDispatchV1 | None = None,
    observer: LightningResourceObserverV1 | None = None,
    d11_config: D11OfflineConfig | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Feat018LiveSmokeResult:
    """Fail-closed live entry until immutable runtime/seam bindings are approved."""
    del request, runtime_config, content_policy, prompt, controller, session_id
    del preflight, finalizer, adapter_dispatch, observer, d11_config, clock
    del config
    return Feat018LiveSmokeResult(
        effective_outcome=EffectiveOutcome.FAILED,
        adapter_call_count=0,
        attempt_count=None,
        cleanup_status=CleanupStatus.SUCCEEDED,
        failure_code=Feat018LiveSmokeFailureCode.NOT_AUTHORIZED,
    )


def _validated_terminal_cleanup_report(result: Feat018LiveSmokeResult) -> D11CleanupReport:
    report = result.d11_report
    if type(report) is not D11CleanupReport or (
        type(report.operations) is not tuple or not report.operations
        or type(report.unresolved_operations) is not tuple or report.unresolved_operations
        or type(report.failure_codes) is not tuple or report.failure_codes
        or type(report.verification) is not str or report.verification != 'VERIFIED_OFFLINE'
    ):
        raise ValueError('D11 resource release unverified')
    deadline = _positive_finite_float(report.deadline_host_monotonic)
    if deadline is None:
        raise ValueError('D11 cleanup deadline must be finite and positive')

    provision: LightningProvisionRefV1 | None = None
    known_sessions: set[str] = set()
    for operation in report.operations:
        if type(operation) is not LightningOperationRefV1 or (
            type(operation.provision) is not LightningProvisionRefV1
        ):
            raise ValueError('D11 cleanup operations must contain typed references')
        LightningProvisionRefV1.__post_init__(operation.provision)
        if provision is None:
            provision = operation.provision
        elif operation.provision != provision:
            raise ValueError('D11 cleanup operations belong to different provisions')
        if operation.session is not None:
            if type(operation.session) is not LightningSessionRefV1 or (
                type(operation.session.provision) is not LightningProvisionRefV1
            ):
                raise ValueError('D11 cleanup session reference must be typed')
            LightningSessionRefV1.__post_init__(operation.session)
            known_sessions.add(operation.session.resource_identity)
        LightningOperationRefV1.__post_init__(operation)

    observation = report.observation
    if type(observation) is not D11ResourceObservation or (
        type(observation.provision) is not LightningProvisionRefV1
    ):
        raise ValueError('D11 cleanup observation must contain a typed provision')
    LightningProvisionRefV1.__post_init__(observation.provision)
    D11ResourceObservation.__post_init__(observation)
    if observation.provision != provision or (
        observation.request_state != 'sealed' or observation.active_operations
        or any(state != 'terminated' for _, state in observation.resources)
    ):
        raise ValueError('D11 cleanup observation does not prove release for the provision')
    if result.session_identity is not None:
        if not _is_bounded_fact_token(result.session_identity):
            raise ValueError('terminal session identity must be bounded')
        known_sessions.add(result.session_identity)
    if not known_sessions <= {identity for identity, _ in observation.resources}:
        raise ValueError('D11 cleanup observation omits a known session')
    observed_at = float(observation.observed_at_host_monotonic)
    if observed_at >= deadline:
        raise ValueError('D11 cleanup observation is outside its deadline')
    terminal_deadline = result.session_termination_deadline_monotonic
    if terminal_deadline is not None and (
        _positive_finite_float(terminal_deadline) is None
        or not _timestamps_match(deadline, terminal_deadline)
    ):
        raise ValueError('D11 cleanup deadline contradicts the terminal deadline')
    for started_at in (
        result.provision_start_monotonic,
        result.gpu_minute_budget_start_monotonic,
        result.session_ttl_start_monotonic,
        result.adapter_start_monotonic,
    ):
        if started_at is not None:
            _validate_non_negative_timestamp(started_at, 'terminal start')
            if float(started_at) > observed_at:
                raise ValueError('D11 cleanup observation precedes a supplied terminal start')
    return report


def _validate_terminal_publication_privacy(result: Feat018LiveSmokeResult, value: object) -> None:
    private_ids: set[str] = set()

    def add_identifier(identifier: object) -> None:
        if isinstance(identifier, str) and identifier:
            private_ids.add(identifier)

    def add_provision(provision: object) -> None:
        if isinstance(provision, LightningProvisionRefV1):
            add_identifier(provision.token)

    if isinstance(result, Feat018LiveSmokeResult):
        add_identifier(result.session_identity)
        report = result.d11_report
        if isinstance(report, D11CleanupReport):
            for operations in (report.operations, report.unresolved_operations):
                if isinstance(operations, (tuple, list)):
                    for operation in operations:
                        if isinstance(operation, LightningOperationRefV1):
                            add_provision(operation.provision)
                            add_identifier(operation.token)
                            add_identifier(operation.recovery_of)
                            if isinstance(operation.session, LightningSessionRefV1):
                                add_provision(operation.session.provision)
                                add_identifier(operation.session.resource_identity)
            observation = report.observation
            if isinstance(observation, D11ResourceObservation):
                add_provision(observation.provision)
                if isinstance(observation.resources, (tuple, list)):
                    for resource in observation.resources:
                        if isinstance(resource, (tuple, list)) and resource:
                            add_identifier(resource[0])
                if isinstance(observation.active_operations, (tuple, list)):
                    for token in observation.active_operations:
                        add_identifier(token)

    def contains_private_id(candidate: object) -> bool:
        if isinstance(candidate, str):
            return any(identifier in candidate for identifier in private_ids)
        if isinstance(candidate, Mapping):
            return any(contains_private_id(key) or contains_private_id(item)
                       for key, item in candidate.items())
        if isinstance(candidate, (list, tuple)):
            return any(contains_private_id(item) for item in candidate)
        return False

    if contains_private_id(value):
        raise ValueError('private recovery identifiers cannot enter published evidence')


def _d11_terminal_evidence_fields(
    result: Feat018LiveSmokeResult, *, runtime_outcome: EffectiveOutcome,
) -> dict[str, object]:
    if (
        type(result) is not Feat018LiveSmokeResult
        or result.effective_outcome is not runtime_outcome
    ):
        raise ValueError('runtime outcome contradicts the typed terminal')
    if result.preflight_verified is not True:
        raise ValueError('terminal preflight remains unverified')
    if result.cleanup_status is not CleanupStatus.SUCCEEDED or result.cleanup_failures:
        raise ValueError('terminal cleanup remains unverified')
    if (
        type(result.adapter_call_count) is not int or result.adapter_call_count not in (0, 1)
        or (result.attempt_count is not None and (
            type(result.attempt_count) is not int or result.attempt_count not in (1, 2)
        ))
    ):
        raise ValueError('invalid terminal cardinality')
    if result.adapter_call_count == 0 and (result.attempt_count is not None or result.adapter_result is not None):
        raise ValueError('pre-adapter terminal cannot claim generation')
    if result.adapter_call_count == 1 and result.session_ready is not True:
        raise ValueError('dispatch contradicts the accepted session readiness marker')
    report = _validated_terminal_cleanup_report(result)
    if (
        type(report.generation) is not int or report.generation <= 0
        or type(report.dispatch_invocation_accepted) is not bool
        or type(report.generation_progress_known) is not bool
    ):
        raise ValueError('D11 release generation and acceptance events must be typed')
    if (report.dispatch_invocation_accepted != (result.adapter_call_count == 1)
            or report.generation_progress_known != (result.attempt_count is not None)):
        raise ValueError('terminal acceptance events do not match cardinality')
    # The harness failure code comes only from the actual terminal's closed enum.
    if result.failure_code is not None and not isinstance(result.failure_code, Feat018LiveSmokeFailureCode):
        raise ValueError('terminal failure code must be a typed coordinator code')
    adapter = result.adapter_result
    if adapter is not None and (
        not _supervisor_result_is_valid(adapter)
        or adapter.cleanup_status is not CleanupStatus.SUCCEEDED or adapter.cleanup_failure is not None
    ):
        raise ValueError('terminal adapter result is invalid or retains cleanup ownership')
    if runtime_outcome is EffectiveOutcome.SUCCEEDED:
        if (
            result.failure_code is not None or result.adapter_call_count != 1 or adapter is None
            or not _adapter_result_is_accepted_success(adapter)
            or result.attempt_count != adapter.attempt_count
        ):
            raise ValueError('terminal cannot promote an unaccepted runtime result')
    elif runtime_outcome is not EffectiveOutcome.FAILED or result.failure_code is None:
        raise ValueError('failed terminal requires a typed coordinator failure code')
    return {
        'terminal_kind': 'PRE_ADAPTER' if result.adapter_call_count == 0 else 'DISPATCHED',
        'adapter_call_count': result.adapter_call_count,
        'attempt_count': result.attempt_count,
        'run_failure_code': None if result.failure_code is None else result.failure_code.value,
        'generation_progress': 'ACCEPTED' if report.generation_progress_known else 'UNKNOWN',
        'cleanup_verification': report.verification,
        'cleanup_generation': report.generation,
        'unresolved_operation_count': len(report.unresolved_operations),
    }


def _binding_terminal_evidence_fields(
    metadata: BindingTerminalMetadataV1,
    result: Feat018LiveSmokeResult,
    *,
    runtime_outcome: EffectiveOutcome,
    terminal_fields: Mapping[str, object],
    publication_ids: tuple[str, ...] = (),
) -> dict[str, object]:
    """Validate the offline hand-off against the actual terminal before publication.

    Identity equality and synthetic observations are never live authorization or remote
    cleanup proof. The existing D11 release/quiescence gates remain independently mandatory.
    """
    if type(metadata) is not BindingTerminalMetadataV1:
        raise ValueError('typed offline binding metadata required')
    checked = metadata.revalidated()
    checked.validate_for_terminal(
        adapter_call_count=result.adapter_call_count,
        attempt_count=result.attempt_count,
        outcome=runtime_outcome.value,
        failure_code=None if result.failure_code is None else result.failure_code.value,
        session_ready=result.session_ready,
    )
    received = checked.result
    adapter = result.adapter_result
    if adapter is None:
        if received.v2_state == 'OBSERVED' or received.raw_state == 'OBSERVED':
            raise ValueError('absent adapter result cannot supply typed result observations')
    else:
        if received.raw_state == 'OBSERVED' and received.raw_status != adapter.raw_status:
            raise ValueError('received Raw status contradicts the accepted adapter result')
        if (
            received.v2_state == 'OBSERVED' and adapter.attempt_count is not None
            and received.v2_attempt_number != adapter.attempt_count
        ):
            raise ValueError('received local attempt number contradicts the adapter receipt')
    runtime = checked.session.runtime
    runtime_received = runtime.state in ('OBSERVED', 'OBSERVED_MISMATCH')
    if runtime_received and result.placement is None:
        raise ValueError('received runtime hardware facts require the actual accepted placement')
    if runtime_received:
        placement = result.placement
        assert placement is not None
        manifest = runtime.manifest
        if manifest is None or any(actual != observed for actual, observed in (
            (placement.gpu_sku, manifest.gpu.sku),
            (placement.device_index, manifest.gpu.device_index),
            (placement.device_count, manifest.cuda.device_count),
            (placement.vram_mib, manifest.gpu.vram_mib),
            (placement.cuda_available, manifest.cuda.available),
            (placement.bf16_supported, manifest.gpu.bf16_supported),
            (placement.single_device_visible, runtime.single_device_visible),
        )):
            raise ValueError('received hardware facts contradict accepted placement')
        if runtime.post_load_model_device_index is not None and (
            runtime.post_load_model_device_index != placement.model_device_index
            or runtime.post_load_input_device_index != placement.input_device_index
        ):
            raise ValueError('received post-load facts contradict accepted placement')
    fields = checked.evidence_fields()
    reserved = {
        'status', 'cleanup_status', 'postflight_status', 'run_id', 'evidence_id',
        'companion_markdown_sha256', 'commit_state', 'run_failure_code',
        *terminal_fields,
    }
    if set(fields) & reserved:
        raise ValueError('binding metadata cannot override terminal or commit facts')

    def contains_key(value: object, key: str) -> bool:
        if isinstance(value, Mapping):
            return key in value or any(contains_key(item, key) for item in value.values())
        if isinstance(value, (list, tuple)):
            return any(contains_key(item, key) for item in value)
        return False

    if contains_key(fields, 'observer_ref'):
        raise ValueError('local observation provenance cannot enter published evidence')
    _validate_terminal_publication_privacy(result, (fields, publication_ids))
    return fields


__all__ = [
    'D11CleanupGrant', 'D11CleanupWindow', 'D11OperationContext', 'D11OperationKind',
    'D11OperationReceipt', 'D11ResourceObservation', 'D11OfflineConfig', 'D11DispatchInputs',
    'D11SDKOperationHandle', 'D11CleanupReport', 'LightningProvisionRefV1', 'LightningSessionRefV1',
    'LightningOperationRefV1', 'LightningSessionControllerV1', 'LightningAdapterDispatchV1',
    'LightningResourceObserverV1',
    'run_offline_live_smoke',
    'D9_STDERR_MAX_BYTES',
    'D9_STDOUT_MAX_BYTES',
    'D9BoundedByteCapture',
    'D9Capture',
    'D9CaptureFactory',
    'D9CaptureReport',
    'D9ProcessRole',
    'D9ProcessStreamCapture',
    'D9StreamDisposition',
    'D9StreamFailureCode',
    'D9StreamName',
    'D9StreamObservation',
    'D9StreamTerminalCategory',
    "SmokeFinalizationResult",
    "finalize_smoke_run",
    "Feat018ArtifactInventory",
    "Feat018IncidentWriter",
    "Feat018LiveSmokeConfig",
    "Feat018LiveSmokeFailureCode",
    "Feat018LiveSmokeResult",
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
    "Feat018LifecycleOperationError",
    "Feat018LightningLifecycleProcessBoundary",
    "Feat018ProgressStateMachine",
    "Feat018ProtocolViolationError",
    "FilesystemOps",
    "BoundedAdapterCall",
    "LightningCancellationFacts",
    "LightningFinalizationFacts",
    "LightningLifecycleBoundary",
    "LightningLifecycleOperationName",
    "LightningOperationHandle",
    "LightningPlacementApproval",
    "LightningPlacementFacts",
    "LightningPreflight",
    "LightningPreflightFacts",
    "LightningProvisionFacts",
    "LightningReadyFacts",
    "LightningSessionLifecycleFacts",
    "LightningSessionController",
    "LightningSessionReadiness",
    "LightningSmokeFinalizer",
    "LightningTerminationFacts",
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
    "run_live_smoke",
]
