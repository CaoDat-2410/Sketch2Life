"""Offline tests for the FEAT-018 P2-T2 bounded-runner package (revision 5, approved scope).

Most tests here use injected fakes: fake clocks, fake process launchers, fake containment backends,
and a fake filesystem. The lifecycle-boundary tests additionally launch synthetic ``spawn`` child
workers whose controller methods deliberately hang or exit; no real provider workload is used.
No test in this file loads a provider or model, touches a GPU, opens Lightning, or uses a network.
Retry and terminal-classification
assertions exercise the real, unmodified ``QwenVisionAdapter.understand()`` with a fake
``QwenGenerationRunner``; fake adapters are used only for the outer-supervisor edge cases, per the
approved package's real-adapter compatibility contract.
"""

from __future__ import annotations

import contextlib
import inspect
import json
import multiprocessing
import os
import signal
import socket
import stat
import struct
import subprocess
import sys
import threading
import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, cast

import pytest

from sketch2life.benchmark.feat018_live_lightning_execution import (
    D9_STDERR_MAX_BYTES,
    D9_STDOUT_MAX_BYTES,
    AcceptanceResult,
    BoundedConnection,
    CleanupStatus,
    D9BoundedByteCapture,
    D9CaptureReport,
    D9ProcessRole,
    D9ProcessStreamCapture,
    D9StreamDisposition,
    D9StreamFailureCode,
    D9StreamName,
    D9StreamObservation,
    D9StreamTerminalCategory,
    EffectiveOutcome,
    EvidenceCommitResult,
    Feat018AdapterCallSupervisor,
    Feat018ArtifactInventory,
    Feat018BoundedKillableQwenGenerationRunner,
    Feat018BoundedRunnerConfig,
    Feat018CleanupFailedError,
    Feat018ContainmentError,
    Feat018EvidenceCommitWriter,
    Feat018EvidenceFinalizer,
    Feat018FrameTooLargeError,
    Feat018IncidentWriter,
    Feat018LauncherError,
    Feat018LifecycleOperationError,
    Feat018LightningLifecycleProcessBoundary,
    Feat018LiveSmokeConfig,
    Feat018LiveSmokeFailureCode,
    Feat018LiveSmokeResult,
    Feat018ProgressStateMachine,
    Feat018ProtocolViolationError,
    LightningCancellationFacts,
    LightningFinalizationFacts,
    LightningLifecycleBoundary,
    LightningLifecycleOperationName,
    LightningOperationHandle,
    LightningPlacementApproval,
    LightningPlacementFacts,
    LightningPreflightFacts,
    LightningProvisionFacts,
    LightningReadyFacts,
    LightningSessionLifecycleFacts,
    LightningSessionReadiness,
    LightningTerminationFacts,
    MultiprocessingBoundedConnection,
    MultiprocessingProcessLauncher,
    PairVerdict,
    PosixProcessGroupContainment,
    ProcessHandle,
    ProgressEvent,
    ProgressEventKind,
    ProgressState,
    SupervisorRunResult,
    WindowsJobObjectContainment,
    _adapter_result_is_accepted_success,  # noqa: PLC2701 - proves the D9-aware success contract
    _bounded_terminate_kill_join,  # noqa: PLC2701 - verifies process resource ownership
    _cancel_lightning_operation,  # noqa: PLC2701 - deterministic inline-boundary test seam
    _cancel_termination_operation,  # noqa: PLC2701 - deterministic inline-boundary test seam
    _generation_child_entry_with_capture,  # noqa: PLC2701 - D9 child IPC seam
    _progress_event_from_frame,  # noqa: PLC2701 - strict internal cleanup marker contract
    _wait_for_lightning_operation,  # noqa: PLC2701 - deterministic inline-boundary test seam
    _Win32JobHandles,  # noqa: PLC2701 - white-box test of the ctypes binding surface (F4)
    adapter_worker_entry,
    decode_envelope,
    encode_envelope,
    finalize_smoke_run,
    new_evidence_id,
    new_run_id,
    posix_worker_self_contain,
    run_bounded_adapter_call,
    read_committed_pair,
    _run_legacy_offline_smoke as run_live_smoke,
)
from sketch2life.contracts.schemas.vision import (
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_v2,
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
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

# ------------------------------------------------------------------------------------------
# Shared fakes
# ------------------------------------------------------------------------------------------


class FakeClock:
    """A settable monotonic clock double."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds

    def set(self, value: float) -> None:
        self._now = value


class BoundaryClock(FakeClock):
    """Clock that jumps exactly on the coordinator's final pre-call read."""

    def __init__(self, start: float = 0.0) -> None:
        super().__init__(start)
        self._reads_until_jump: int | None = None
        self._jump_value = start

    @property
    def raw_now(self) -> float:
        return self._now

    def arm_jump_after_next_read(self, value: float) -> None:
        # The operation wait helper reads the clock once, then the coordinator records
        # ready_finished, and the third read is its final adapter boundary check.
        self._reads_until_jump = 2
        self._jump_value = value

    def __call__(self) -> float:
        if self._reads_until_jump is not None:
            if self._reads_until_jump > 0:
                self._reads_until_jump -= 1
                return self._now
            self._reads_until_jump = None
            self._now = self._jump_value
        return self._now


@dataclass(slots=True)
class FakeProcessHandle:
    """A minimal, fully controllable :class:`ProcessHandle` double."""

    _pid: int | None = 4242
    _alive: bool = True
    started_at_monotonic: float | None = None
    exit_code: int | None = 0
    terminate_calls: int = field(default=0, init=False)
    kill_calls: int = field(default=0, init=False)
    join_calls: list[float | None] = field(default_factory=list, init=False)
    close_calls: int = field(default=0, init=False)
    cleanup_events: list[str] = field(default_factory=list, init=False)
    joined: bool = field(default=False, init=False)
    closed: bool = field(default=False, init=False)
    die_on_terminate: bool = False
    die_on_kill: bool = True
    raise_on_terminate: BaseException | None = None
    raise_on_close: BaseException | None = None

    @property
    def pid(self) -> int | None:
        return self._pid

    @property
    def exitcode(self) -> int | None:
        self.cleanup_events.append("exitcode")
        return self.exit_code if not self._alive and self.joined else None

    def is_alive(self) -> bool:
        self.cleanup_events.append("is_alive")
        return self._alive

    def terminate(self) -> None:
        self.cleanup_events.append("terminate")
        self.terminate_calls += 1
        if self.raise_on_terminate is not None:
            raise self.raise_on_terminate
        if self.die_on_terminate:
            self._alive = False

    def kill(self) -> None:
        self.cleanup_events.append("kill")
        self.kill_calls += 1
        if self.die_on_kill:
            self._alive = False

    def join(self, timeout: float | None = None) -> None:
        self.cleanup_events.append("join")
        self.join_calls.append(timeout)
        if not self._alive:
            self.joined = True

    def close(self) -> None:
        assert not self._alive
        assert self.joined
        assert self.exit_code is not None
        self.cleanup_events.append("close")
        self.close_calls += 1
        if self.raise_on_close is not None:
            raise self.raise_on_close
        self.closed = True

    def mark_dead(self) -> None:
        self._alive = False


@dataclass(slots=True)
class FakeBoundedConnection:
    """A queue-driven :class:`BoundedConnection` double.

    A real ``Connection.poll(timeout)`` blocks for up to ``timeout`` seconds when nothing is
    available. To keep supervisor-loop tests deterministic and hang-free without a real clock,
    an empty inbox advances a bound :class:`FakeClock` by exactly ``timeout`` before returning
    ``None`` -- mirroring the real blocking behavior on a fake clock instead of returning
    instantly, which would otherwise spin the supervisor's polling loop forever.
    """

    inbox: deque[dict[str, object]] = field(default_factory=deque)
    sent: list[dict[str, object]] = field(default_factory=list)
    closed: bool = field(default=False, init=False)
    close_calls: int = field(default=0, init=False)
    max_envelope_bytes: int = 1_000_000
    raise_on_recv: BaseException | None = None
    raise_on_send: BaseException | None = None
    fail_send_kinds: set[str] = field(default_factory=set)
    raise_on_close: BaseException | None = None
    clock: FakeClock | None = None

    def push(self, frame: Mapping[str, object]) -> None:
        self.inbox.append(dict(frame))

    def send_frame(self, payload: Mapping[str, object]) -> None:
        if self.raise_on_send is not None:
            raise self.raise_on_send
        if payload.get("kind") in self.fail_send_kinds:
            raise BrokenPipeError("injected send failure")
        encode_envelope(payload, max_bytes=self.max_envelope_bytes)
        self.sent.append(dict(payload))

    def recv_frame(self, timeout: float) -> dict[str, object] | None:
        if self.raise_on_recv is not None:
            raise self.raise_on_recv
        if not self.inbox:
            if self.clock is not None:
                self.clock.advance(timeout)
            return None
        return self.inbox.popleft()

    def close(self) -> None:
        self.close_calls += 1
        if self.raise_on_close is not None:
            raise self.raise_on_close
        self.closed = True


def _fake_d9_report(
    process_role: D9ProcessRole, *, attempt_number: int | None = None
) -> D9CaptureReport:
    if process_role is D9ProcessRole.INNER_GENERATION_CHILD and attempt_number is None:
        attempt_number = 1
    return D9CaptureReport(
        observations=tuple(
            D9StreamObservation(
                process_role=process_role,
                attempt_number=attempt_number,
                stream=stream,
                bytes_seen=0,
                ceiling=(
                    D9_STDOUT_MAX_BYTES
                    if stream is D9StreamName.STDOUT
                    else D9_STDERR_MAX_BYTES
                ),
                disposition=D9StreamDisposition.ACCEPTED,
                terminal_category=D9StreamTerminalCategory.WITHIN_LIMIT,
            )
            for stream in D9StreamName
        )
    )


@dataclass(slots=True)
class FakeD9Capture:
    process_role: D9ProcessRole
    attempt_number: int | None = None
    finalize_calls: int = field(default=0, init=False)
    quiescence_calls: int = field(default=0, init=False)

    def finalize(self) -> D9CaptureReport:
        self.finalize_calls += 1
        return _fake_d9_report(self.process_role, attempt_number=self.attempt_number)

    def verify_writer_quiescence(self) -> D9CaptureReport:
        self.quiescence_calls += 1
        return _fake_d9_report(self.process_role, attempt_number=self.attempt_number)


def _fake_d9_capture_factory(
    process_role: D9ProcessRole,
    attempt_number: int | None,
    stdout_max_bytes: int,
    stderr_max_bytes: int,
    on_terminal_failure: Callable[[D9StreamFailureCode], None] | None,
) -> FakeD9Capture:
    del on_terminal_failure
    assert stdout_max_bytes == D9_STDOUT_MAX_BYTES
    assert stderr_max_bytes == D9_STDERR_MAX_BYTES
    return FakeD9Capture(process_role, attempt_number)


def _progress_frames(frames: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        frame
        for frame in frames
        if frame.get('kind') not in {'D9_STREAM_OBSERVATION', 'D9_STREAM_FAILURE'}
    ]


@dataclass(slots=True)
class FakeProcessLauncher:
    """Returns pre-built fakes instead of ever spawning a real process."""

    handle: FakeProcessHandle
    connection: FakeBoundedConnection
    launch_calls: list[tuple[Callable[..., None], tuple[object, ...]]] = field(
        default_factory=list, init=False
    )

    def launch(
        self, entry: Callable[..., None], args: tuple[object, ...]
    ) -> tuple[ProcessHandle, FakeBoundedConnection]:
        self.launch_calls.append((entry, args))
        return self.handle, self.connection


def _launcher(clock: FakeClock | None = None) -> FakeProcessLauncher:
    return FakeProcessLauncher(
        handle=FakeProcessHandle(), connection=FakeBoundedConnection(clock=clock)
    )


@dataclass(slots=True)
class FakeContainmentBackend:
    """A fully controllable :class:`ContainmentBackend` double."""

    create_fails: bool = False
    confirm_result: bool = True
    confirm_raises: BaseException | None = None
    confirm_calls: list[tuple[float, float]] = field(default_factory=list, init=False)
    terminate_calls: int = field(default=0, init=False)
    close_calls: int = field(default=0, init=False)
    empty_after_terminate: bool = True
    raise_on_is_empty: BaseException | None = None
    created: bool = field(default=False, init=False)

    def create(self) -> None:
        if self.create_fails:
            raise Feat018ContainmentError("fake containment creation failure")
        self.created = True

    def confirm_worker_contained(
        self, worker: ProcessHandle, *, timeout: float, retry_interval: float
    ) -> bool:
        del worker
        self.confirm_calls.append((timeout, retry_interval))
        if self.confirm_raises is not None:
            raise self.confirm_raises
        return self.confirm_result

    def terminate_all(self, *, cleanup_deadline_monotonic: float | None = None,
                      clock: Callable[[], float] | None = None) -> None:
        self.terminate_calls += 1

    def is_empty(self) -> bool:
        if self.raise_on_is_empty is not None:
            raise self.raise_on_is_empty
        return self.empty_after_terminate

    def close(self) -> None:
        self.close_calls += 1


@dataclass(slots=True)
class FakeLightningOperation:
    """A non-blocking operation double with bounded wait and cancellation evidence."""

    clock: FakeClock
    result: object
    wait_advance_seconds: float = 0.0
    cancel_result: object = field(
        default_factory=lambda: LightningCancellationFacts(cancellation_verified=True)
    )
    cancel_advance_seconds: float = 0.0
    wait_calls: list[float] = field(default_factory=list, init=False)
    cancel_calls: list[float] = field(default_factory=list, init=False)

    @staticmethod
    def _resolve(value: object) -> object:
        return value() if callable(value) else value

    def wait(self, *, timeout_seconds: float) -> object:
        self.wait_calls.append(timeout_seconds)
        self.clock.advance(self.wait_advance_seconds)
        value = self._resolve(self.result)
        if isinstance(value, BaseException):
            raise value
        return value

    def cancel(self, *, timeout_seconds: float) -> LightningCancellationFacts:
        self.cancel_calls.append(timeout_seconds)
        self.clock.advance(self.cancel_advance_seconds)
        value = self._resolve(self.cancel_result)
        if isinstance(value, BaseException):
            raise value
        return cast(LightningCancellationFacts, value)


_UNSET_LIGHTNING_RESULT = object()


@dataclass(slots=True)
class FakeLightningSessionController:
    """An independently cancellable controller double for the host coordinator."""

    clock: FakeClock
    provision_result: object = _UNSET_LIGHTNING_RESULT
    ready_result: object = _UNSET_LIGHTNING_RESULT
    termination_result: object = _UNSET_LIGHTNING_RESULT
    provision_advance_seconds: float = 0.0
    ready_advance_seconds: float = 0.0
    termination_advance_seconds: float = 0.0
    provision_cancel_result: object = field(
        default_factory=lambda: LightningCancellationFacts(cancellation_verified=True)
    )
    ready_cancel_result: object = field(
        default_factory=lambda: LightningCancellationFacts(cancellation_verified=True)
    )
    termination_cancel_result: object = _UNSET_LIGHTNING_RESULT
    provision_calls: int = field(default=0, init=False)
    ready_calls: int = field(default=0, init=False)
    termination_calls: int = field(default=0, init=False)
    provision_operations: list[FakeLightningOperation] = field(default_factory=list, init=False)
    ready_operations: list[FakeLightningOperation] = field(default_factory=list, init=False)
    termination_operations: list[FakeLightningOperation] = field(
        default_factory=list, init=False
    )
    session_identity: str = "provider-session"
    ttl_seconds: int = 30
    placement: LightningPlacementFacts = field(
        default_factory=lambda: LightningPlacementFacts(
            gpu_sku="NVIDIA_L4",
            device_index=0,
            device_count=1,
            vram_mib=24576,
            cuda_available=True,
            bf16_supported=True,
            single_device_visible=True,
            model_device_index=0,
            input_device_index=0,
        )
    )

    def _default_provision_result(self) -> LightningProvisionFacts:
        return LightningProvisionFacts(
            allocation_confirmed=True,
            gpu_minute_budget_start_monotonic=self.clock(),
            session_identity=self.session_identity,
            placement=self.placement,
        )

    def _default_ready_result(self) -> LightningReadyFacts:
        ready_at = self.clock()
        return LightningReadyFacts(
            readiness=LightningSessionReadiness.SESSION_READY,
            lifecycle=LightningSessionLifecycleFacts(
                session_identity=self.session_identity,
                session_ready_at_monotonic=ready_at,
                session_ttl_start_monotonic=ready_at,
                session_ttl_deadline_monotonic=ready_at + self.ttl_seconds,
            ),
        )

    def _default_termination_result(self) -> LightningTerminationFacts:
        return LightningTerminationFacts(
            termination_verified=True,
            cleanup_status=CleanupStatus.SUCCEEDED,
            session_identity=self.session_identity,
            session_cleanup_verified=True,
        )

    def _default_termination_cancel_result(self) -> LightningCancellationFacts:
        return LightningCancellationFacts(
            cancellation_verified=True,
            termination_facts=self._default_termination_result(),
        )

    def provision(self) -> LightningOperationHandle[LightningProvisionFacts]:
        self.provision_calls += 1
        result = (
            self._default_provision_result()
            if self.provision_result is _UNSET_LIGHTNING_RESULT
            else self.provision_result
        )
        operation = FakeLightningOperation(
            self.clock,
            result,
            wait_advance_seconds=self.provision_advance_seconds,
            cancel_result=self.provision_cancel_result,
        )
        self.provision_operations.append(operation)
        return cast(LightningOperationHandle[LightningProvisionFacts], operation)

    def wait_ready(self) -> LightningOperationHandle[LightningReadyFacts]:
        self.ready_calls += 1
        result = (
            self._default_ready_result
            if self.ready_result is _UNSET_LIGHTNING_RESULT
            else self.ready_result
        )
        operation = FakeLightningOperation(
            self.clock,
            result,
            wait_advance_seconds=self.ready_advance_seconds,
            cancel_result=self.ready_cancel_result,
        )
        self.ready_operations.append(operation)
        return cast(LightningOperationHandle[LightningReadyFacts], operation)

    def terminate(self) -> LightningOperationHandle[LightningTerminationFacts]:
        self.termination_calls += 1
        result = (
            self._default_termination_result()
            if self.termination_result is _UNSET_LIGHTNING_RESULT
            else self.termination_result
        )
        cancel_result = (
            self._default_termination_cancel_result()
            if self.termination_cancel_result is _UNSET_LIGHTNING_RESULT
            else self.termination_cancel_result
        )
        operation = FakeLightningOperation(
            self.clock,
            result,
            wait_advance_seconds=self.termination_advance_seconds,
            cancel_result=cancel_result,
        )
        self.termination_operations.append(operation)
        return cast(LightningOperationHandle[LightningTerminationFacts], operation)


def _synthetic_child_hang(marker: Any) -> None:
    marker.set()
    _synthetic_block_forever()


def _synthetic_block_forever() -> None:
    while True:
        time.sleep(1.0)


@dataclass(slots=True)
class _ProcessLifecycleEvents:
    provision_called: Any
    ready_called: Any
    terminate_called: Any
    wait_started: Any
    cancel_started: Any
    descendant_started: Any
    termination_finished: Any
    descendant_pid: Any
    termination_count: Any


@dataclass(slots=True)
class _ProcessLifecycleOperation:
    result: object
    wait_mode: str
    cancel_mode: str
    wait_started: Any
    cancel_started: Any
    cancel_result: object
    wait_delay_seconds: float = 0.0

    def wait(self, *, timeout_seconds: float) -> object:
        del timeout_seconds
        self.wait_started.set()
        if self.wait_mode == "hang":
            _synthetic_child_hang(self.wait_started)
        if self.wait_mode == "die":
            os._exit(91)
        if self.wait_mode == "timeout":
            raise TimeoutError
        if self.wait_delay_seconds > 0:
            time.sleep(self.wait_delay_seconds)
        return self.result

    def cancel(self, *, timeout_seconds: float) -> object:
        del timeout_seconds
        self.cancel_started.set()
        if self.cancel_mode == "hang":
            _synthetic_child_hang(self.cancel_started)
        if self.cancel_mode == "die":
            os._exit(92)
        return self.cancel_result


@dataclass(slots=True)
class _ProcessLightningSessionController:
    """Spawn-picklable synthetic controller used only to prove host preemption."""

    events: _ProcessLifecycleEvents
    provision_mode: str = "success"
    ready_mode: str = "success"
    termination_mode: str = "success"
    provision_wait_mode: str = "success"
    ready_wait_mode: str = "success"
    termination_wait_mode: str = "success"
    provision_cancel_mode: str = "success"
    ready_cancel_mode: str = "success"
    termination_cancel_mode: str = "success"
    provision_wait_delay_seconds: float = 0.0
    ready_wait_delay_seconds: float = 0.0
    termination_wait_delay_seconds: float = 0.0
    session_identity: str = "provider-session"
    ttl_seconds: int = 30
    placement: LightningPlacementFacts = field(
        default_factory=lambda: LightningPlacementFacts(
            gpu_sku="NVIDIA_L4",
            device_index=0,
            device_count=1,
            vram_mib=24576,
            cuda_available=True,
            bf16_supported=True,
            single_device_visible=True,
            model_device_index=0,
            input_device_index=0,
        )
    )

    def _provision_result(self) -> LightningProvisionFacts:
        return LightningProvisionFacts(
            allocation_confirmed=True,
            gpu_minute_budget_start_monotonic=time.monotonic(),
            session_identity=self.session_identity,
            placement=self.placement,
        )

    def _ready_result(self) -> LightningReadyFacts:
        ready_at = time.monotonic()
        return LightningReadyFacts(
            readiness=LightningSessionReadiness.SESSION_READY,
            lifecycle=LightningSessionLifecycleFacts(
                session_identity=self.session_identity,
                session_ready_at_monotonic=ready_at,
                session_ttl_start_monotonic=ready_at,
                session_ttl_deadline_monotonic=ready_at + self.ttl_seconds,
            ),
        )

    def _termination_result(self) -> LightningTerminationFacts:
        return LightningTerminationFacts(
            termination_verified=True,
            cleanup_status=CleanupStatus.SUCCEEDED,
            session_identity=self.session_identity,
            session_cleanup_verified=True,
        )

    def _termination_cancel_result(self) -> LightningCancellationFacts:
        return LightningCancellationFacts(
            cancellation_verified=True,
            termination_facts=self._termination_result(),
        )

    def provision(self) -> object:
        self.events.provision_called.set()
        if self.provision_mode == "hang":
            _synthetic_child_hang(self.events.provision_called)
        if self.provision_mode == "die":
            os._exit(93)
        return _ProcessLifecycleOperation(
            result=self._provision_result(),
            wait_mode=self.provision_wait_mode,
            cancel_mode=self.provision_cancel_mode,
            wait_started=self.events.wait_started,
            cancel_started=self.events.cancel_started,
            cancel_result=LightningCancellationFacts(cancellation_verified=True),
            wait_delay_seconds=self.provision_wait_delay_seconds,
        )

    def wait_ready(self) -> object:
        self.events.ready_called.set()
        if self.ready_mode == "hang":
            _synthetic_child_hang(self.events.ready_called)
        if self.ready_mode == "die":
            os._exit(94)
        return _ProcessLifecycleOperation(
            result=self._ready_result(),
            wait_mode=self.ready_wait_mode,
            cancel_mode=self.ready_cancel_mode,
            wait_started=self.events.wait_started,
            cancel_started=self.events.cancel_started,
            cancel_result=LightningCancellationFacts(cancellation_verified=True),
            wait_delay_seconds=self.ready_wait_delay_seconds,
        )

    def terminate(self) -> object:
        self.events.terminate_called.set()
        self.events.termination_count.value += 1
        if self.termination_mode == "hang_descendant":
            context = multiprocessing.get_context("spawn")
            descendant = context.Process(
                target=_synthetic_child_hang,
                args=(self.events.descendant_started,),
                daemon=False,
            )
            descendant.start()
            self.events.descendant_pid.value = descendant.pid or -1
            _synthetic_block_forever()
        if self.termination_mode == "die":
            os._exit(95)
        return _ProcessLifecycleOperation(
            result=self._termination_result(),
            wait_mode=self.termination_wait_mode,
            cancel_mode=self.termination_cancel_mode,
            wait_started=self.events.wait_started,
            cancel_started=self.events.cancel_started,
            cancel_result=self._termination_cancel_result(),
            wait_delay_seconds=self.termination_wait_delay_seconds,
        )


def _process_lifecycle_events() -> _ProcessLifecycleEvents:
    context = multiprocessing.get_context("spawn")
    return _ProcessLifecycleEvents(
        provision_called=context.Event(),
        ready_called=context.Event(),
        terminate_called=context.Event(),
        wait_started=context.Event(),
        cancel_started=context.Event(),
        descendant_started=context.Event(),
        termination_finished=context.Event(),
        descendant_pid=context.Value("i", 0),
        termination_count=context.Value("i", 0),
    )


@dataclass(slots=True)
class FakeLightningPreflight:
    """All-true preflight by default, with explicit failure injection."""

    result: object = _UNSET_LIGHTNING_RESULT
    calls: list[str] = field(default_factory=list, init=False)

    def verify(self, *, synthetic_session_id: str) -> LightningPreflightFacts:
        self.calls.append(synthetic_session_id)
        value = (
            LightningPreflightFacts(
                synthetic_session_id=synthetic_session_id,
                approval_identity_verified=True,
                checkout_identity_verified=True,
                d4_readiness_verified=True,
                fixture_digest_verified=True,
                prompt_hash_verified=True,
                hardware_placement_verified=True,
                policy_identity_verified=True,
                runtime_inventory_verified=True,
            )
            if self.result is _UNSET_LIGHTNING_RESULT
            else self.result
        )
        if isinstance(value, BaseException):
            raise value
        return cast(LightningPreflightFacts, value)


@dataclass(slots=True)
class FakeLiveSmokeFinalizer:
    """Typed finalization proof double; no evidence is written by offline tests."""

    result: object = _UNSET_LIGHTNING_RESULT
    calls: list[Feat018LiveSmokeResult] = field(default_factory=list, init=False)

    def finalize(self, *, result: Feat018LiveSmokeResult) -> LightningFinalizationFacts:
        self.calls.append(result)
        value = (
            LightningFinalizationFacts(
                finalization_verified=True,
                evidence_pair_verified=True,
                incident_handling_verified=True,
            )
            if self.result is _UNSET_LIGHTNING_RESULT
            else self.result
        )
        if isinstance(value, BaseException):
            raise value
        return cast(LightningFinalizationFacts, value)


@dataclass(slots=True)
class FakeInlineLightningLifecycleBoundary:
    """Deterministic test-only boundary for the pre-existing fake-clock coordinator tests.

    NON-LIVE, TEST-SEAM ONLY (independent-review finding B3-3): this wires the module's
    cooperative-wait helpers (``_wait_for_lightning_operation`` and friends), which trust the
    operation handle to honor its own timeout, directly into a ``LightningLifecycleBoundary``.
    ``run_live_smoke`` never constructs this class and never receives it unless a test explicitly
    passes it as ``lifecycle_boundary=``; the real coordinator always defaults to the killable
    :class:`Feat018LightningLifecycleProcessBoundary`. This double exists only to keep the
    deadline/TTL/GPU-budget/placement coordinator-logic regression suite fast and deterministic
    without real subprocess overhead -- it must never be injected into any live-capable path.
    """

    controller: FakeLightningSessionController
    clock: FakeClock
    cancellation_budget_seconds: float = 2.0

    def invoke(
        self,
        operation: LightningLifecycleOperationName,
        *,
        deadline: float,
        cancellation_deadline: float,
        session_identity: str | None = None,
    ) -> object:
        operation_handle = getattr(self.controller, operation)()
        try:
            return _wait_for_lightning_operation(
                operation_handle,
                deadline=deadline,
                clock=self.clock,
            )
        except TimeoutError:
            if operation == "terminate":
                cancelled = _cancel_termination_operation(
                    operation_handle,
                    deadline=cancellation_deadline,
                    clock=self.clock,
                    session_identity=session_identity,
                )
            else:
                cancelled = _cancel_lightning_operation(
                    operation_handle,
                    deadline=self.clock() + self.cancellation_budget_seconds,
                    clock=self.clock,
                )
            if not cancelled:
                raise Feat018LifecycleOperationError(
                    Feat018LiveSmokeFailureCode.SESSION_TERMINATION_CANCELLATION_FAILED
                    if operation == "terminate"
                    else Feat018LiveSmokeFailureCode.OPERATION_CANCELLATION_FAILED
                ) from None
            raise Feat018LifecycleOperationError(
                Feat018LiveSmokeFailureCode.SESSION_TERMINATION_TIMEOUT
                if operation == "terminate"
                else (
                    Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT
                    if operation == "provision"
                    else Feat018LiveSmokeFailureCode.READY_TIMEOUT
                )
            ) from None
        except Exception:  # noqa: BLE001 - deterministic provider failure mapping
            raise Feat018LifecycleOperationError(
                Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED
                if operation == "terminate"
                else (
                    Feat018LiveSmokeFailureCode.PROVISION_FAILED
                    if operation == "provision"
                    else Feat018LiveSmokeFailureCode.READY_FAILED
                )
            ) from None


def _no_op_entry(*_args: object) -> None:
    return None


@dataclass(slots=True)
class _FakeRawEndpoint:
    """A locally owned multiprocessing endpoint double; it never reaches the OS."""

    name: str
    raise_on_close: BaseException | None = None
    close_calls: int = field(default=0, init=False)
    closed: bool = field(default=False, init=False)

    def send_bytes(self, buf: bytes) -> None:
        del buf

    def recv_bytes(self, maxlength: int | None = None) -> bytes:
        del maxlength
        return b""

    def poll(self, timeout: float | None = None) -> bool:
        del timeout
        return False

    def close(self) -> None:
        self.close_calls += 1
        if self.raise_on_close is not None:
            raise self.raise_on_close
        self.closed = True


@dataclass(slots=True)
class _FakeMultiprocessingProcess:
    """A non-spawning process double with controllable rollback behavior."""

    _pid: int | None = 7777
    alive: bool = False
    start_error: BaseException | None = None
    start_marks_live_before_error: bool = False
    die_on_terminate: bool = True
    die_on_kill: bool = True
    raise_on_terminate: BaseException | None = None
    raise_on_kill: BaseException | None = None
    join_errors: dict[int, BaseException] = field(default_factory=dict)
    raise_on_is_alive: BaseException | None = None
    raise_on_close: BaseException | None = None
    exit_code: int | None = 0
    started: bool = field(default=False, init=False)
    joined: bool = field(default=False, init=False)
    closed: bool = field(default=False, init=False)
    close_calls: int = field(default=0, init=False)
    daemon: bool | None = field(default=None, init=False)
    start_calls: int = field(default=0, init=False)
    terminate_calls: int = field(default=0, init=False)
    kill_calls: int = field(default=0, init=False)
    join_calls: list[float | None] = field(default_factory=list, init=False)
    is_alive_calls: int = field(default=0, init=False)
    cleanup_events: list[str] = field(default_factory=list, init=False)

    @property
    def pid(self) -> int | None:
        return self._pid if self.started else None

    @property
    def exitcode(self) -> int | None:
        self.cleanup_events.append("exitcode")
        return self.exit_code if self.started and not self.alive and self.joined else None

    @property
    def can_spawn_child_processes(self) -> bool:
        return self.daemon is False

    def start(self) -> None:
        self.start_calls += 1
        if self.start_marks_live_before_error:
            self.started = True
            self.alive = True
        if self.start_error is not None:
            raise self.start_error
        self.started = True
        self.alive = True

    def is_alive(self) -> bool:
        self.cleanup_events.append("is_alive")
        self.is_alive_calls += 1
        if self.raise_on_is_alive is not None:
            raise self.raise_on_is_alive
        return self.alive

    def terminate(self) -> None:
        self.cleanup_events.append("terminate")
        self.terminate_calls += 1
        if self.raise_on_terminate is not None:
            raise self.raise_on_terminate
        if self.die_on_terminate:
            self.alive = False

    def kill(self) -> None:
        self.cleanup_events.append("kill")
        self.kill_calls += 1
        if self.raise_on_kill is not None:
            raise self.raise_on_kill
        if self.die_on_kill:
            self.alive = False

    def join(self, timeout: float | None = None) -> None:
        call_number = len(self.join_calls)
        self.cleanup_events.append(f"join_{call_number + 1}")
        self.join_calls.append(timeout)
        if call_number in self.join_errors:
            raise self.join_errors[call_number]
        if not self.alive:
            self.joined = True

    def close(self) -> None:
        assert not self.alive
        assert not self.started or (self.joined and self.exit_code is not None)
        self.cleanup_events.append("close")
        self.close_calls += 1
        if self.raise_on_close is not None:
            raise self.raise_on_close
        self.closed = True


@dataclass(slots=True)
class _FakeSpawnContext:
    """An injectable context double that records construction without spawning."""

    parent: _FakeRawEndpoint = field(default_factory=lambda: _FakeRawEndpoint("parent"))
    child: _FakeRawEndpoint = field(default_factory=lambda: _FakeRawEndpoint("child"))
    process: _FakeMultiprocessingProcess = field(
        default_factory=_FakeMultiprocessingProcess
    )
    pipe_error: BaseException | None = None
    process_error: BaseException | None = None
    pipe_calls: int = field(default=0, init=False)
    process_calls: list[tuple[Callable[..., None], tuple[object, ...], bool]] = field(
        default_factory=list, init=False
    )

    def Pipe(self, duplex: bool = True) -> tuple[_FakeRawEndpoint, _FakeRawEndpoint]:
        self.pipe_calls += 1
        if self.pipe_error is not None:
            raise self.pipe_error
        assert duplex is True
        return self.parent, self.child

    def Process(
        self,
        *,
        target: Callable[..., None],
        args: tuple[object, ...],
        daemon: bool,
    ) -> _FakeMultiprocessingProcess:
        self.process_calls.append((target, args, daemon))
        if self.process_error is not None:
            raise self.process_error
        self.process.daemon = daemon
        return self.process


class _NoStartProcess:
    """Proxy a real stdlib Process while making its start method a no-op."""

    def __init__(self, actual_process: Any) -> None:
        self.actual_process = actual_process
        self.start_calls = 0

    @property
    def pid(self) -> int | None:
        return self.actual_process.pid

    @property
    def exitcode(self) -> int | None:
        return self.actual_process.exitcode

    def is_alive(self) -> bool:
        return bool(self.actual_process.is_alive())

    def terminate(self) -> None:
        self.actual_process.terminate()

    def kill(self) -> None:
        self.actual_process.kill()

    def join(self, timeout: float | None = None) -> None:
        self.actual_process.join(timeout)

    def close(self) -> None:
        self.actual_process.close()

    def start(self) -> None:
        self.start_calls += 1


class _RecordingSpawnContext:
    """Delegate construction to a real spawn context but never start its Process."""

    def __init__(self, real_context: Any) -> None:
        self._real_context = real_context
        self.process_arguments: tuple[
            Callable[..., None], tuple[object, ...], bool
        ] | None = None
        self.actual_process: Any | None = None

    def Pipe(self, duplex: bool = True) -> tuple[Any, Any]:
        return self._real_context.Pipe(duplex=duplex)

    def Process(
        self,
        *,
        target: Callable[..., None],
        args: tuple[object, ...],
        daemon: bool,
    ) -> _NoStartProcess:
        self.process_arguments = (target, args, daemon)
        self.actual_process = self._real_context.Process(
            target=target, args=args, daemon=daemon
        )
        return _NoStartProcess(self.actual_process)


class TestMultiprocessingProcessLauncher:
    def _launcher(
        self,
        context: _FakeSpawnContext,
        *,
        connection_factory: Callable[[Any, int], BoundedConnection] | None = None,
    ) -> MultiprocessingProcessLauncher:
        kwargs: dict[str, object] = {"context_factory": lambda: context}
        if connection_factory is not None:
            kwargs["connection_factory"] = connection_factory
        return MultiprocessingProcessLauncher(max_envelope_bytes=10_000, **kwargs)  # type: ignore[arg-type]

    def test_context_factory_failure_is_sanitized(self) -> None:
        def fail_context() -> _FakeSpawnContext:
            raise RuntimeError("SECRET-context-detail")

        launcher = MultiprocessingProcessLauncher(
            max_envelope_bytes=10_000, context_factory=fail_context
        )
        with pytest.raises(Feat018LauncherError, match="bounded process launch failed"):
            launcher.launch(_no_op_entry, ())

    def test_pipe_creation_failure_has_no_endpoint_to_leak(self) -> None:
        context = _FakeSpawnContext(pipe_error=RuntimeError("SECRET-pipe-detail"))
        with pytest.raises(Feat018LauncherError, match="bounded process launch failed"):
            self._launcher(context).launch(_no_op_entry, ())
        assert context.pipe_calls == 1
        assert context.parent.close_calls == 0
        assert context.child.close_calls == 0
        assert context.process_calls == []

    def test_process_construction_failure_closes_both_pipe_endpoints_once(self) -> None:
        context = _FakeSpawnContext(process_error=RuntimeError("SECRET-process-detail"))
        with pytest.raises(Feat018LauncherError, match="bounded process launch failed"):
            self._launcher(context).launch(_no_op_entry, ())
        assert context.parent.close_calls == 1
        assert context.child.close_calls == 1
        assert context.process.start_calls == 0

    def test_child_wrapper_failure_closes_both_endpoints_without_process_construction(self) -> None:
        context = _FakeSpawnContext()
        wrapper_calls = 0

        def fail_child_wrapper(connection: Any, max_envelope_bytes: int) -> BoundedConnection:
            del connection, max_envelope_bytes
            nonlocal wrapper_calls
            wrapper_calls += 1
            raise RuntimeError("SECRET-child-wrapper-detail")

        with pytest.raises(Feat018LauncherError, match="bounded process launch failed") as exc_info:
            self._launcher(context, connection_factory=fail_child_wrapper).launch(
                _no_op_entry, ()
            )

        assert "SECRET-child-wrapper-detail" not in str(exc_info.value)
        assert wrapper_calls == 1
        assert context.process_calls == []
        assert context.process.start_calls == 0
        assert context.parent.close_calls == 1
        assert context.child.close_calls == 1

    def test_start_failure_before_process_becomes_live_closes_endpoints(self) -> None:
        process = _FakeMultiprocessingProcess(
            start_error=RuntimeError("SECRET-start-detail"),
            start_marks_live_before_error=False,
        )
        context = _FakeSpawnContext(process=process)
        with pytest.raises(Feat018LauncherError, match="bounded process launch failed"):
            self._launcher(context).launch(_no_op_entry, ())
        assert process.start_calls == 1
        assert process.terminate_calls == 0
        assert process.kill_calls == 0
        assert process.alive is False
        assert context.parent.close_calls == 1
        assert context.child.close_calls == 1

    def test_start_failure_after_process_becomes_live_rolls_back_boundedly(self) -> None:
        process = _FakeMultiprocessingProcess(
            start_error=RuntimeError("SECRET-start-after-live-detail"),
            start_marks_live_before_error=True,
            die_on_terminate=False,
        )
        context = _FakeSpawnContext(process=process)
        with pytest.raises(Feat018LauncherError, match="bounded process launch failed"):
            self._launcher(context).launch(_no_op_entry, ())
        assert process.terminate_calls == 1
        assert process.kill_calls == 1
        assert process.join_calls == [1.0, 1.0]
        assert process.alive is False
        assert context.parent.close_calls == 1
        assert context.child.close_calls == 1

    def test_child_endpoint_close_failure_after_start_is_typed_and_rolled_back(self) -> None:
        process = _FakeMultiprocessingProcess()
        context = _FakeSpawnContext(process=process)
        context.child.raise_on_close = OSError("SECRET-child-close-detail")
        with pytest.raises(
            Feat018CleanupFailedError, match="bounded process launch cleanup failed"
        ):
            self._launcher(context).launch(_no_op_entry, ())
        assert context.child.close_calls == 2
        assert context.parent.close_calls == 1
        assert process.terminate_calls == 1
        assert process.alive is False

    def test_parent_wrapper_failure_rolls_back_and_closes_parent_endpoint(self) -> None:
        process = _FakeMultiprocessingProcess()
        context = _FakeSpawnContext(process=process)
        wrapper_calls = 0

        def fail_parent_wrapper(connection: Any, max_envelope_bytes: int) -> BoundedConnection:
            nonlocal wrapper_calls
            wrapper_calls += 1
            if wrapper_calls == 2:
                raise RuntimeError("SECRET-parent-wrapper-detail")
            return MultiprocessingBoundedConnection(
                connection=connection, max_envelope_bytes=max_envelope_bytes
            )

        with pytest.raises(Feat018LauncherError, match="bounded process launch failed"):
            self._launcher(context, connection_factory=fail_parent_wrapper).launch(
                _no_op_entry, ()
            )
        assert wrapper_calls == 2
        assert context.child.close_calls == 1
        assert context.parent.close_calls == 1
        assert process.terminate_calls == 1
        assert process.alive is False

    def test_success_is_non_daemon_and_preserves_the_open_parent_endpoint(self) -> None:
        context = _FakeSpawnContext()
        launcher = self._launcher(context)
        process, parent_connection = launcher.launch(_no_op_entry, ("fixture",))

        assert getattr(process, "process") is context.process
        assert context.process.daemon is False
        assert context.process.can_spawn_child_processes is True
        assert context.process_calls[0][2] is False
        assert context.child.close_calls == 1
        assert context.child.closed is True
        assert context.parent.close_calls == 0
        assert context.parent.closed is False
        assert isinstance(parent_connection, MultiprocessingBoundedConnection)
        assert parent_connection.connection is context.parent

    def test_real_spawn_context_constructs_non_daemon_outer_process_without_starting(self) -> None:
        real_context = multiprocessing.get_context("spawn")
        context = _RecordingSpawnContext(real_context)
        worker_args = ("request", "runtime", "policy", "prompt", _config())
        launcher = MultiprocessingProcessLauncher(
            max_envelope_bytes=10_000,
            context_factory=lambda: context,  # type: ignore[arg-type]
        )
        parent_connection: BoundedConnection | None = None

        try:
            process, parent_connection = launcher.launch(adapter_worker_entry, worker_args)

            assert context.process_arguments is not None
            target, constructed_args, daemon = context.process_arguments
            assert target is adapter_worker_entry
            assert constructed_args[1:] == worker_args
            assert daemon is False
            assert context.actual_process is not None
            assert context.actual_process.daemon is False
            assert getattr(context.actual_process, "_popen", None) is None
            assert isinstance(getattr(process, "process"), _NoStartProcess)
            assert getattr(process, "process").start_calls == 1
        finally:
            if parent_connection is not None:
                parent_connection.close()
            if context.actual_process is not None:
                context.actual_process.close()

    @pytest.mark.parametrize("failure_kind", ("terminate", "grace_join", "kill", "final_join"))
    def test_each_process_rollback_operation_failure_is_typed(
        self, failure_kind: str
    ) -> None:
        process = _FakeMultiprocessingProcess()
        if failure_kind == "terminate":
            process.raise_on_terminate = OSError("SECRET-terminate-detail")
        elif failure_kind == "grace_join":
            process.join_errors = {0: OSError("SECRET-grace-join-detail")}
        elif failure_kind == "kill":
            process.die_on_terminate = False
            process.raise_on_kill = OSError("SECRET-kill-detail")
        else:
            process.die_on_terminate = False
            process.join_errors = {1: OSError("SECRET-final-join-detail")}
        context = _FakeSpawnContext(process=process)
        wrapper_calls = 0

        def fail_parent_wrapper(connection: Any, max_envelope_bytes: int) -> BoundedConnection:
            nonlocal wrapper_calls
            wrapper_calls += 1
            if wrapper_calls == 2:
                raise RuntimeError("SECRET-wrapper-detail")
            return MultiprocessingBoundedConnection(
                connection=connection, max_envelope_bytes=max_envelope_bytes
            )

        with pytest.raises(
            Feat018CleanupFailedError, match="bounded process launch cleanup failed"
        ) as exc_info:
            self._launcher(context, connection_factory=fail_parent_wrapper).launch(
                _no_op_entry, ()
            )

        assert process.cleanup_events.index("terminate") < process.cleanup_events.index("join_1")
        if "kill" in process.cleanup_events:
            assert process.cleanup_events.index("kill") < process.cleanup_events.index("join_2")
        if process.closed:
            assert process.alive is False
            assert process.joined is True
            assert process.cleanup_events[-1] == "close"
        assert "SECRET-" not in str(exc_info.value)
        assert context.child.close_calls == 1
        assert context.parent.close_calls == 1

    def test_parent_endpoint_close_failure_is_typed_after_launch_failure(self) -> None:
        context = _FakeSpawnContext()
        context.parent.raise_on_close = OSError("SECRET-parent-close-detail")
        wrapper_calls = 0

        def fail_parent_wrapper(connection: Any, max_envelope_bytes: int) -> BoundedConnection:
            nonlocal wrapper_calls
            wrapper_calls += 1
            if wrapper_calls == 2:
                raise RuntimeError("SECRET-wrapper-detail")
            return MultiprocessingBoundedConnection(
                connection=connection, max_envelope_bytes=max_envelope_bytes
            )

        with pytest.raises(
            Feat018CleanupFailedError, match="bounded process launch cleanup failed"
        ):
            self._launcher(context, connection_factory=fail_parent_wrapper).launch(
                _no_op_entry, ()
            )
        assert context.parent.close_calls == 1
        assert context.child.close_calls == 1

    def test_process_surviving_rollback_is_a_truthful_cleanup_failure(self) -> None:
        process = _FakeMultiprocessingProcess(die_on_terminate=False, die_on_kill=False)
        context = _FakeSpawnContext(process=process)
        wrapper_calls = 0

        def fail_parent_wrapper(connection: Any, max_envelope_bytes: int) -> BoundedConnection:
            nonlocal wrapper_calls
            wrapper_calls += 1
            if wrapper_calls == 2:
                raise RuntimeError("SECRET-wrapper-detail")
            return MultiprocessingBoundedConnection(
                connection=connection, max_envelope_bytes=max_envelope_bytes
            )

        with pytest.raises(
            Feat018CleanupFailedError, match="bounded process launch cleanup failed"
        ):
            self._launcher(context, connection_factory=fail_parent_wrapper).launch(
                _no_op_entry, ()
            )
        assert process.terminate_calls == 1
        assert process.kill_calls == 1
        assert process.join_calls == [1.0, 1.0]
        assert process.alive is True
        assert context.parent.close_calls == 1
        assert context.child.close_calls == 1

    def test_failed_endpoint_release_stays_owned_until_retry_succeeds(self) -> None:
        context = _FakeSpawnContext()
        context.parent.raise_on_close = OSError("parent close failed")
        wrapper_calls = 0

        def fail_parent_wrapper(connection: Any, max_envelope_bytes: int) -> BoundedConnection:
            nonlocal wrapper_calls
            wrapper_calls += 1
            if wrapper_calls == 2:
                raise RuntimeError("parent wrapper failed")
            return MultiprocessingBoundedConnection(connection, max_envelope_bytes)

        with pytest.raises(Feat018CleanupFailedError) as exc_info:
            self._launcher(context, connection_factory=fail_parent_wrapper).launch(
                _no_op_entry, ()
            )

        failure = exc_info.value
        assert failure.owned_process is None
        assert failure.owned_connections == (context.parent,)
        assert context.process.closed is True
        assert context.parent.closed is False

        context.parent.raise_on_close = None
        assert failure.retry_cleanup(grace_seconds=0.1, kill_join_seconds=0.1)

        assert context.parent.closed is True
        assert failure.owned_connections == ()
        assert context.process.close_calls == 1

    def test_liveness_verification_failure_is_a_sanitized_cleanup_failure(self) -> None:
        process = _FakeMultiprocessingProcess(
            raise_on_is_alive=OSError("SECRET-liveness-detail")
        )
        context = _FakeSpawnContext(process=process)
        wrapper_calls = 0

        def fail_parent_wrapper(connection: Any, max_envelope_bytes: int) -> BoundedConnection:
            nonlocal wrapper_calls
            wrapper_calls += 1
            if wrapper_calls == 2:
                raise RuntimeError("SECRET-wrapper-detail")
            return MultiprocessingBoundedConnection(
                connection=connection, max_envelope_bytes=max_envelope_bytes
            )

        with pytest.raises(
            Feat018CleanupFailedError, match="bounded process launch cleanup failed"
        ):
            self._launcher(context, connection_factory=fail_parent_wrapper).launch(
                _no_op_entry, ()
            )
        assert process.terminate_calls == 1
        assert process.kill_calls == 1
        assert context.parent.close_calls == 1
        assert context.child.close_calls == 1


# ------------------------------------------------------------------------------------------
# Byte-boundary and receive-side limits
# ------------------------------------------------------------------------------------------


class TestEnvelopeFraming:
    def test_encode_accepts_at_exact_ceiling(self) -> None:
        payload = {"kind": "x", "pad": "a" * 10}
        exact = encode_envelope(payload, max_bytes=len(encode_envelope(payload, max_bytes=10_000)))
        assert isinstance(exact, bytes)

    def test_encode_rejects_one_byte_over_ceiling(self) -> None:
        payload = {"kind": "x"}
        exact_size = len(encode_envelope(payload, max_bytes=10_000))
        with pytest.raises(Feat018FrameTooLargeError):
            encode_envelope(payload, max_bytes=exact_size - 1)

    def test_encode_accepts_one_byte_under_ceiling(self) -> None:
        payload = {"kind": "x"}
        exact_size = len(encode_envelope(payload, max_bytes=10_000))
        encode_envelope(payload, max_bytes=exact_size + 1)

    def test_decode_rejects_non_utf8(self) -> None:
        with pytest.raises(Feat018ProtocolViolationError):
            decode_envelope(b"\xff\xfe\xfd")

    def test_decode_rejects_non_object_root(self) -> None:
        with pytest.raises(Feat018ProtocolViolationError):
            decode_envelope(b"[1, 2, 3]")

    def test_decode_round_trips_a_valid_envelope(self) -> None:
        payload = {"kind": "success", "raw_output": "hello"}
        encoded = encode_envelope(payload, max_bytes=10_000)
        assert decode_envelope(encoded) == payload

    def test_multibyte_utf8_boundary_is_enforced_on_encoded_bytes(self) -> None:
        payload = {"kind": "x", "pad": "é" * 5}  # 2 bytes each in UTF-8
        exact_size = len(encode_envelope(payload, max_bytes=10_000))
        encode_envelope(payload, max_bytes=exact_size)
        with pytest.raises(Feat018FrameTooLargeError):
            encode_envelope(payload, max_bytes=exact_size - 1)


class TestBoundedConnectionFraming:
    def test_send_frame_rejects_oversized_payload_before_it_reaches_the_wire(self) -> None:
        connection = FakeBoundedConnection(max_envelope_bytes=10)
        with pytest.raises(Feat018FrameTooLargeError):
            connection.send_frame({"kind": "x", "pad": "a" * 100})
        assert _progress_frames(connection.sent) == []

    def test_real_connection_wrapper_propagates_endpoint_close_failure(self) -> None:
        endpoint = _FakeRawEndpoint("parent", raise_on_close=OSError("close failed"))
        connection = MultiprocessingBoundedConnection(endpoint, max_envelope_bytes=1_000)

        with pytest.raises(OSError, match="close failed"):
            connection.close()

        assert endpoint.close_calls == 1
        assert endpoint.closed is False

    @pytest.mark.parametrize("flag", [False, 1, "true", None])
    def test_terminal_cleanup_flag_rejects_every_value_except_true(self, flag: object) -> None:
        assert _progress_event_from_frame({
            "seq": 2, "kind": "TERMINAL", "outcome": "FAILED", "cleanup_failed": flag,
        }) is None

    @pytest.mark.parametrize("kind", ["ADAPTER_STARTED", "GENERATION_ATTEMPT_STARTED"])
    def test_cleanup_flag_is_rejected_on_nonterminal_progress(self, kind: str) -> None:
        frame: dict[str, object] = {
            "seq": 2, "kind": kind, "cleanup_failed": True,
        }
        if kind == "GENERATION_ATTEMPT_STARTED":
            frame["attempt_number"] = 1
        assert _progress_event_from_frame(frame) is None

    def test_cleanup_flag_rejects_a_success_terminal(self) -> None:
        assert _progress_event_from_frame({
            "seq": 2, "kind": "TERMINAL", "outcome": "SUCCEEDED", "cleanup_failed": True,
        }) is None

    def test_failed_terminal_accepts_the_cleanup_flag(self) -> None:
        event = _progress_event_from_frame({
            "seq": 2, "kind": "TERMINAL", "outcome": "FAILED", "cleanup_failed": True,
        })

        assert event is not None
        assert event.kind is ProgressEventKind.TERMINAL
        assert event.outcome == "FAILED"


class TestProcessCleanupOwnership:
    def test_cleanup_joins_share_the_remaining_absolute_deadline(self) -> None:
        clock = FakeClock(start=10.0)
        deadline = 10.25

        class _TimedProcess(FakeProcessHandle):
            def join(self, timeout: float | None = None) -> None:
                assert timeout is not None
                clock.advance(timeout)
                super().join(timeout)

        process = _TimedProcess()

        assert _bounded_terminate_kill_join(
            process,
            grace_seconds=1.0,
            kill_join_seconds=1.0,
            cleanup_deadline_monotonic=deadline,
            clock=clock,
        )

        assert clock() <= deadline
        assert sum(cast(float, timeout) for timeout in process.join_calls) <= 0.25
        assert process.closed is True

    def test_retained_cleanup_owner_blocks_an_otherwise_successful_result(self) -> None:
        successful = _successful_supervisor_result()
        assert successful.is_success
        assert _adapter_result_is_accepted_success(successful)
        inconsistent = replace(
            successful,
            cleanup_failure=Feat018CleanupFailedError(owned_process=FakeProcessHandle()),
        )

        assert not inconsistent.is_success
        assert not _adapter_result_is_accepted_success(inconsistent)

    @pytest.mark.parametrize("initially_alive", [False, True])
    def test_process_is_reaped_and_exit_observed_before_handle_release(
        self, initially_alive: bool
    ) -> None:
        process = FakeProcessHandle(_alive=initially_alive)

        assert _bounded_terminate_kill_join(
            process, grace_seconds=0.1, kill_join_seconds=0.1
        )

        assert process.joined is True
        assert process.close_calls == 1
        assert process.closed is True
        assert process.cleanup_events.index("join") < process.cleanup_events.index("exitcode")
        assert process.cleanup_events.index("exitcode") < process.cleanup_events.index("close")

    @pytest.mark.parametrize("failure_kind", ["alive", "unobserved_exit", "close"])
    def test_unreleased_process_cannot_report_cleanup_success(self, failure_kind: str) -> None:
        process = FakeProcessHandle()
        if failure_kind == "alive":
            process.die_on_kill = False
        elif failure_kind == "unobserved_exit":
            process.exit_code = None
        else:
            process.raise_on_close = OSError("process close failed")

        assert not _bounded_terminate_kill_join(
            process, grace_seconds=0.1, kill_join_seconds=0.1
        )

        assert process.closed is False
        assert process.close_calls == (1 if failure_kind == "close" else 0)

    def test_unstarted_process_releases_without_invalid_join(self) -> None:
        process = _FakeMultiprocessingProcess()

        assert _bounded_terminate_kill_join(
            process, grace_seconds=0.1, kill_join_seconds=0.1
        )

        assert process.join_calls == []
        assert process.close_calls == 1
        assert process.closed is True


# ------------------------------------------------------------------------------------------
# Supervisor progress state machine and deadline freeze
# ------------------------------------------------------------------------------------------


class TestProgressStateMachine:
    def _machine(self, deadline: float = 100.0) -> Feat018ProgressStateMachine:
        return Feat018ProgressStateMachine(cap_deadline_monotonic=deadline)

    def test_happy_path_one_attempt(self) -> None:
        machine = self._machine()
        assert (
            machine.accept(
                ProgressEvent(seq=1, kind=ProgressEventKind.ADAPTER_STARTED),
                acceptance_time=1.0,
            )
            is AcceptanceResult.ACCEPTED
        )
        assert (
            machine.accept(
                ProgressEvent(
                    seq=2,
                    kind=ProgressEventKind.GENERATION_ATTEMPT_STARTED,
                    attempt_number=1,
                ),
                acceptance_time=2.0,
            )
            is AcceptanceResult.ACCEPTED
        )
        assert (
            machine.accept(
                ProgressEvent(seq=3, kind=ProgressEventKind.TERMINAL, outcome="SUCCEEDED"),
                acceptance_time=3.0,
            )
            is AcceptanceResult.ACCEPTED
        )
        assert machine.state is ProgressState.TERMINAL
        assert machine.attempt_count == 1
        assert machine.terminal_outcome == "SUCCEEDED"

    def test_two_attempts_then_terminal(self) -> None:
        machine = self._machine()
        machine.accept(ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=1.0)
        machine.accept(
            ProgressEvent(2, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=1),
            acceptance_time=2.0,
        )
        machine.accept(
            ProgressEvent(3, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=2),
            acceptance_time=3.0,
        )
        result = machine.accept(
            ProgressEvent(4, ProgressEventKind.TERMINAL, outcome="FAILED"), acceptance_time=4.0
        )
        assert result is AcceptanceResult.ACCEPTED
        assert machine.attempt_count == 2

    def test_duplicate_seq_is_rejected_without_state_change(self) -> None:
        machine = self._machine()
        machine.accept(ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=1.0)
        result = machine.accept(
            ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=2.0
        )
        assert result is AcceptanceResult.REJECTED_DUPLICATE
        assert machine.state is ProgressState.ADAPTER_STARTED

    def test_gapped_seq_is_rejected(self) -> None:
        machine = self._machine()
        machine.accept(ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=1.0)
        result = machine.accept(
            ProgressEvent(
                3, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=1
            ),
            acceptance_time=2.0,
        )
        assert result is AcceptanceResult.REJECTED_GAP
        assert machine.attempt_count is None

    @pytest.mark.parametrize(
        "events",
        [
            [
                ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED),
                ProgressEvent(2, ProgressEventKind.ADAPTER_STARTED),
            ],
            [
                ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED),
                ProgressEvent(
                    2, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=2
                ),
            ],
            [
                ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED),
                ProgressEvent(
                    2, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=1
                ),
                ProgressEvent(
                    3, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=1
                ),
            ],
        ],
    )
    def test_invalid_transitions_are_rejected(self, events: list[ProgressEvent]) -> None:
        machine = self._machine()
        results = [
            machine.accept(event, acceptance_time=float(index))
            for index, event in enumerate(events, start=1)
        ]
        assert results[-1] is AcceptanceResult.REJECTED_INVALID_TRANSITION

    def test_terminal_followed_by_progress_is_rejected(self) -> None:
        machine = self._machine()
        machine.accept(ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=1.0)
        machine.accept(
            ProgressEvent(2, ProgressEventKind.TERMINAL, outcome="SUCCEEDED"),
            acceptance_time=2.0,
        )
        result = machine.accept(
            ProgressEvent(3, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=1),
            acceptance_time=3.0,
        )
        assert result is AcceptanceResult.REJECTED_CLOSED
        assert machine.state is ProgressState.TERMINAL
        assert machine.terminal_outcome == "SUCCEEDED"

    def test_duplicate_success_after_terminal_failure_cannot_flip_the_outcome(self) -> None:
        machine = self._machine()
        machine.accept(ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=1.0)
        machine.accept(
            ProgressEvent(2, ProgressEventKind.TERMINAL, outcome="FAILED"), acceptance_time=2.0
        )
        result = machine.accept(
            ProgressEvent(3, ProgressEventKind.TERMINAL, outcome="SUCCEEDED"),
            acceptance_time=3.0,
        )
        assert result is AcceptanceResult.REJECTED_CLOSED
        assert machine.terminal_outcome == "FAILED"

    def test_exact_deadline_tie_is_rejected_and_freezes(self) -> None:
        machine = self._machine(deadline=10.0)
        result = machine.accept(
            ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=10.0
        )
        assert result is AcceptanceResult.REJECTED_DEADLINE
        assert machine.state is ProgressState.FROZEN

    def test_acceptance_time_one_tick_before_deadline_is_accepted(self) -> None:
        machine = self._machine(deadline=10.0)
        result = machine.accept(
            ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=9.999999
        )
        assert result is AcceptanceResult.ACCEPTED

    def test_frame_completing_after_deadline_uses_completion_time_not_arrival_time(self) -> None:
        machine = self._machine(deadline=10.0)
        # The frame "began arriving" long before the deadline conceptually, but its
        # acceptance_time (completion) is what the caller must pass -- here, after deadline.
        result = machine.accept(
            ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=10.5
        )
        assert result is AcceptanceResult.REJECTED_DEADLINE

    def test_events_after_freeze_are_rejected_closed(self) -> None:
        machine = self._machine(deadline=5.0)
        machine.accept(ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=6.0)
        assert machine.state is ProgressState.FROZEN
        result = machine.accept(
            ProgressEvent(2, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=1),
            acceptance_time=6.1,
        )
        assert result is AcceptanceResult.REJECTED_CLOSED

    def test_force_freeze_is_used_when_no_event_ever_arrives(self) -> None:
        machine = self._machine()
        machine.force_freeze()
        assert machine.state is ProgressState.FROZEN
        assert machine.attempt_count is None

    def test_force_freeze_does_not_override_an_already_terminal_state(self) -> None:
        machine = self._machine()
        machine.accept(ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=1.0)
        machine.accept(
            ProgressEvent(2, ProgressEventKind.TERMINAL, outcome="SUCCEEDED"),
            acceptance_time=2.0,
        )
        machine.force_freeze()
        assert machine.state is ProgressState.TERMINAL

    def test_malformed_event_construction_is_rejected_at_the_type_level(self) -> None:
        with pytest.raises(ValueError, match="attempt_number"):
            ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED, attempt_number=1)
        with pytest.raises(ValueError, match="outcome"):
            ProgressEvent(1, ProgressEventKind.TERMINAL)


# ------------------------------------------------------------------------------------------
# POSIX containment: bounded retry, timeout, fail-closed (independent-audit finding A2-2)
# ------------------------------------------------------------------------------------------


class TestPosixContainmentConfirmation:
    def test_confirms_on_first_successful_probe(self) -> None:
        clock = FakeClock()
        containment = PosixProcessGroupContainment(
            _probe=lambda pid: pid, _clock=clock, _sleep=lambda _s: None
        )
        worker = FakeProcessHandle(_pid=99)
        assert containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.1)

    def test_retries_a_bounded_number_of_times_before_succeeding(self) -> None:
        clock = FakeClock()
        attempts = {"count": 0}

        def probe(pid: int) -> int:
            attempts["count"] += 1
            if attempts["count"] < 3:
                return pid + 1  # wrong group: not yet self-contained
            return pid

        sleeps: list[float] = []

        def fake_sleep(seconds: float) -> None:
            sleeps.append(seconds)
            clock.advance(seconds)

        containment = PosixProcessGroupContainment(_probe=probe, _clock=clock, _sleep=fake_sleep)
        worker = FakeProcessHandle(_pid=7)
        assert containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.05)
        assert attempts["count"] == 3
        assert sleeps == [0.05, 0.05]

    def test_fails_closed_after_the_bounded_timeout_elapses(self) -> None:
        clock = FakeClock()

        def fake_sleep(seconds: float) -> None:
            clock.advance(seconds)

        containment = PosixProcessGroupContainment(
            _probe=lambda pid: pid + 1, _clock=clock, _sleep=fake_sleep
        )
        worker = FakeProcessHandle(_pid=7)
        assert not containment.confirm_worker_contained(worker, timeout=0.2, retry_interval=0.05)

    def test_fails_closed_when_probe_raises_oserror_the_whole_time(self) -> None:
        clock = FakeClock()

        def raising_probe(pid: int) -> int:
            raise OSError("no such process")

        containment = PosixProcessGroupContainment(
            _probe=raising_probe, _clock=clock, _sleep=lambda seconds: clock.advance(seconds)
        )
        worker = FakeProcessHandle(_pid=7)
        assert not containment.confirm_worker_contained(worker, timeout=0.1, retry_interval=0.05)

    def test_fails_closed_when_worker_pid_is_unavailable(self) -> None:
        containment = PosixProcessGroupContainment()
        worker = FakeProcessHandle(_pid=None)
        assert not containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.1)

    def test_terminate_all_is_a_no_op_before_confirmation_ever_succeeded(self) -> None:
        containment = PosixProcessGroupContainment()
        containment.terminate_all()  # must not raise
        assert containment.is_empty()

    def test_is_empty_reflects_whether_the_group_still_has_a_live_member(self) -> None:
        clock = FakeClock()
        containment = PosixProcessGroupContainment(
            _probe=lambda pid: pid, _clock=clock, _sleep=lambda _s: None
        )
        worker = FakeProcessHandle(_pid=55)
        containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.1)

        live_calls = {"n": 0}

        def killpg_stub(pgid: int, sig: int) -> None:
            live_calls["n"] += 1
            if sig == 0 and live_calls["n"] > 2:
                raise ProcessLookupError

        import sketch2life.benchmark.feat018_live_lightning_execution as module

        original = module._posix_killpg
        module._posix_killpg = killpg_stub  # type: ignore[assignment]
        try:
            assert containment.is_empty() is False
            assert containment.is_empty() is False
            assert containment.is_empty() is True
        finally:
            module._posix_killpg = original  # type: ignore[assignment]

    def test_terminate_all_escalates_to_sigkill_when_the_group_ignores_sigterm(self) -> None:
        """B3-1: one SIGTERM is not proof of termination -- a trapped/ignored SIGTERM must
        still be followed by a SIGKILL, which cannot be caught, blocked, or ignored."""

        clock = FakeClock()
        containment = PosixProcessGroupContainment(
            _probe=lambda pid: pid,
            _clock=clock,
            _sleep=lambda seconds: clock.advance(seconds),
            sigkill_grace_seconds=0.1,
            sigkill_poll_interval_seconds=0.02,
        )
        worker = FakeProcessHandle(_pid=41)
        containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.1)

        signals_sent: list[int] = []
        alive = {"value": True}

        def killpg_stub(pgid: int, sig: int) -> None:
            signals_sent.append(sig)
            if sig == 9:
                alive["value"] = False
                return
            if sig == 0 and not alive["value"]:
                raise ProcessLookupError
            # SIGTERM (15), or a liveness probe (0) while still alive: the group ignores it.

        import sketch2life.benchmark.feat018_live_lightning_execution as module

        original = module._posix_killpg
        module._posix_killpg = killpg_stub  # type: ignore[assignment]
        try:
            containment.terminate_all()
            assert signals_sent[0] == 15  # SIGTERM sent first
            assert 9 in signals_sent  # escalated to SIGKILL after the bounded grace window
            assert containment.is_empty() is True  # proven empty only after the SIGKILL
            assert containment._cleanup_failed is False
        finally:
            module._posix_killpg = original  # type: ignore[assignment]

    def test_terminate_all_never_blocks_longer_than_the_configured_grace_window(self) -> None:
        """Even a group that never reports empty (SIGTERM and SIGKILL both silently ignored)
        must not make ``terminate_all`` block past its own bounded grace window -- the caller's
        own ``is_empty`` polling loop, not this method, owns final fail-closed proof."""

        clock = FakeClock()
        sleeps: list[float] = []

        def fake_sleep(seconds: float) -> None:
            sleeps.append(seconds)
            clock.advance(seconds)

        containment = PosixProcessGroupContainment(
            _probe=lambda pid: pid,
            _clock=clock,
            _sleep=fake_sleep,
            sigkill_grace_seconds=0.2,
            sigkill_poll_interval_seconds=0.05,
        )
        worker = FakeProcessHandle(_pid=41)
        containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.1)

        import sketch2life.benchmark.feat018_live_lightning_execution as module

        original = module._posix_killpg
        signals_sent: list[int] = []

        def killpg_stub(pgid: int, sig: int) -> None:
            signals_sent.append(sig)
            # Every signal, including SIGKILL, is silently ignored: the group never empties.

        module._posix_killpg = killpg_stub  # type: ignore[assignment]
        try:
            containment.terminate_all()  # must return, never spin forever
            assert 15 in signals_sent
            assert 9 in signals_sent
            assert sum(sleeps) <= 0.2 + 1e-9
            # The method never lies: it does not claim the group is empty when it is not.
            assert containment.is_empty() is False
        finally:
            module._posix_killpg = original  # type: ignore[assignment]

    def test_terminate_all_reports_cleanup_failed_when_sigkill_itself_errors(self) -> None:
        clock = FakeClock()
        containment = PosixProcessGroupContainment(
            _probe=lambda pid: pid,
            _clock=clock,
            _sleep=lambda seconds: clock.advance(seconds),
            sigkill_grace_seconds=0.05,
            sigkill_poll_interval_seconds=0.01,
        )
        worker = FakeProcessHandle(_pid=41)
        containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.1)

        def killpg_stub(pgid: int, sig: int) -> None:
            if sig == 9:
                raise PermissionError("escalation itself failed")
            # SIGTERM and every liveness probe report the group as still alive.

        import sketch2life.benchmark.feat018_live_lightning_execution as module

        original = module._posix_killpg
        module._posix_killpg = killpg_stub  # type: ignore[assignment]
        try:
            containment.terminate_all()  # must not raise; failure is reported, not thrown
            assert containment._cleanup_failed is True
        finally:
            module._posix_killpg = original  # type: ignore[assignment]

    def test_terminate_all_recovers_via_sigkill_when_sigterm_send_itself_fails(self) -> None:
        """A SIGTERM *send* failure (e.g. a transient permission error, not merely a group that
        ignores a successfully delivered SIGTERM) must not crash ``terminate_all`` or prevent the
        SIGKILL escalation from still running and truthfully cleaning up."""

        clock = FakeClock()
        containment = PosixProcessGroupContainment(
            _probe=lambda pid: pid,
            _clock=clock,
            _sleep=lambda seconds: clock.advance(seconds),
            sigkill_grace_seconds=0.05,
            sigkill_poll_interval_seconds=0.01,
        )
        worker = FakeProcessHandle(_pid=41)
        containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.1)

        alive = {"value": True}

        def killpg_stub(pgid: int, sig: int) -> None:
            if sig == 15:
                raise PermissionError("SIGTERM send itself failed")
            if sig == 9:
                alive["value"] = False
                return
            if sig == 0 and not alive["value"]:
                raise ProcessLookupError
            # sig == 0 while alive: no-op (group still alive)

        import sketch2life.benchmark.feat018_live_lightning_execution as module

        original = module._posix_killpg
        module._posix_killpg = killpg_stub  # type: ignore[assignment]
        try:
            containment.terminate_all()  # must not raise despite the SIGTERM send failure
            assert containment.is_empty() is True  # SIGKILL still ran and truthfully cleaned up
            assert containment._cleanup_failed is False
        finally:
            module._posix_killpg = original  # type: ignore[assignment]

    def test_terminate_all_sigterm_send_failure_never_reports_false_cleanup_success(self) -> None:
        """If the SIGTERM send fails *and* the group survives the SIGKILL escalation too, the
        method must never claim the group is empty -- fail-closed, not fail-open."""

        clock = FakeClock()
        containment = PosixProcessGroupContainment(
            _probe=lambda pid: pid,
            _clock=clock,
            _sleep=lambda seconds: clock.advance(seconds),
            sigkill_grace_seconds=0.05,
            sigkill_poll_interval_seconds=0.01,
        )
        worker = FakeProcessHandle(_pid=41)
        containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.1)

        def killpg_stub(pgid: int, sig: int) -> None:
            if sig == 15:
                raise PermissionError("SIGTERM send itself failed")
            # sig == 0 or sig == 9: the group is unaffected and never reports empty.

        import sketch2life.benchmark.feat018_live_lightning_execution as module

        original = module._posix_killpg
        module._posix_killpg = killpg_stub  # type: ignore[assignment]
        try:
            containment.terminate_all()  # must not raise
            assert containment.is_empty() is False  # never a false success
        finally:
            module._posix_killpg = original  # type: ignore[assignment]


def _posix_sigterm_resistant_descendant_entry(ready: Any) -> None:
    """Real POSIX-only child target: traps SIGTERM, signals readiness, then blocks forever.

    Must only ever run as a real spawned process inside
    ``TestPosixContainmentRealProcessGroupEscalation``; never imported or executed on Windows.
    """

    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    ready.set()
    while True:
        time.sleep(1.0)


def _posix_e2e_worker_entry(descendant_pid: Any, descendant_ready: Any, worker_ready: Any) -> None:
    """Real POSIX-only worker target: becomes its own process group leader (the same first
    instruction the real lifecycle worker uses), spawns a SIGTERM-resistant descendant inside that
    same group, reports the descendant's pid back to the parent test process, then blocks forever
    so the parent can terminate the *whole group* from outside -- exactly the shape
    ``Feat018LightningLifecycleProcessBoundary`` relies on in production.
    """

    posix_worker_self_contain()
    context = multiprocessing.get_context("spawn")
    descendant = context.Process(
        target=_posix_sigterm_resistant_descendant_entry,
        args=(descendant_ready,),
        daemon=False,
    )
    descendant.start()
    descendant_pid.value = descendant.pid or -1
    descendant_ready.wait(timeout=10.0)
    worker_ready.set()
    while True:
        time.sleep(1.0)


class TestPosixContainmentRealProcessGroupEscalation:
    """A genuine POSIX end-to-end proof of ``PosixProcessGroupContainment.terminate_all()``.

    Unlike every other containment test in this file, this test spawns real processes, installs a
    real SIGTERM-ignoring handler in a real descendant, and calls the real (unmodified, not
    monkeypatched) ``terminate_all()``/``is_empty()`` implementation, which issues real
    ``os.killpg`` SIGTERM and SIGKILL signals. It is POSIX-only: ``os.setpgrp``, ``os.getpgid``,
    and ``os.killpg`` do not exist on Windows, so this test is skipped there with an explicit
    reason rather than faked -- a skip must never be reported or treated as a pass.
    """

    @pytest.mark.skipif(
        not (hasattr(os, "setpgrp") and hasattr(os, "getpgid") and hasattr(os, "killpg")),
        reason=(
            "POSIX-only: os.setpgrp/os.getpgid/os.killpg are unavailable on this platform "
            "(e.g. Windows), so real process-group SIGTERM/SIGKILL escalation cannot be "
            "exercised here. This scenario requires a POSIX (Linux/macOS) run."
        ),
    )
    def test_real_process_group_sigterm_ignored_then_sigkilled_leaves_no_orphan(self) -> None:
        context = multiprocessing.get_context("spawn")
        descendant_pid = context.Value("l", 0)
        descendant_ready = context.Event()
        worker_ready = context.Event()
        worker = context.Process(
            target=_posix_e2e_worker_entry,
            args=(descendant_pid, descendant_ready, worker_ready),
            daemon=False,
        )
        containment = PosixProcessGroupContainment(
            sigkill_grace_seconds=2.0,
            sigkill_poll_interval_seconds=0.05,
        )
        try:
            worker.start()
            contained = containment.confirm_worker_contained(
                cast(ProcessHandle, worker), timeout=10.0, retry_interval=0.02
            )
            assert contained is True, "the real worker did not become its own process group"

            assert worker_ready.wait(timeout=10.0), "the descendant never reported readiness"
            child_pid = int(descendant_pid.value)
            assert child_pid > 0
            assert _synthetic_pid_is_alive(child_pid)

            # The real, unmodified terminate_all(): real SIGTERM to the group, bounded grace
            # polling, then real SIGKILL to the group -- no monkeypatched signal function and no
            # fake containment anywhere in this call.
            containment.terminate_all()

            deadline = time.monotonic() + 5.0
            while _synthetic_pid_is_alive(child_pid) and time.monotonic() < deadline:
                time.sleep(0.02)
            assert not _synthetic_pid_is_alive(child_pid), (
                "the SIGTERM-resistant descendant survived real SIGKILL escalation"
            )

            # SIGKILL is delivered to the whole group, including the leader (this worker
            # process) itself. A killed multiprocessing child is a zombie -- still a live PID
            # to killpg's own existence probe -- until this parent reaps it. Production's
            # _bounded_terminate_kill_join() always reaps the worker before polling
            # is_empty() (see _cleanup_resources); mirror that ordering here, or the leader's
            # own unreaped zombie makes is_empty() falsely report a non-empty group forever.
            worker.join(timeout=5.0)
            assert containment.is_empty() is True
            assert containment._cleanup_failed is False
        finally:
            # Safe, unconditional cleanup regardless of assertion outcome: never leak a real
            # process. terminate_all() is idempotent-safe to call again; PID-based SIGKILL is a
            # last-resort backstop if the group somehow was never fully confirmed.
            with contextlib.suppress(Exception):
                containment.terminate_all()
            with contextlib.suppress(Exception):
                if worker.is_alive():
                    worker.kill()
                worker.join(timeout=2.0)
            child_pid_value = int(descendant_pid.value) if descendant_pid.value else 0
            if child_pid_value > 0:
                with contextlib.suppress(ProcessLookupError, OSError):
                    os.kill(child_pid_value, signal.SIGKILL)
            with contextlib.suppress(Exception):
                containment.close()


# ------------------------------------------------------------------------------------------
# F4 -- explicit, pointer-width-safe Win32 ctypes bindings, exercised via a fake Kernel32
# ------------------------------------------------------------------------------------------


class _FakeKernel32:
    """A Win32 API double using plain function attributes.

    ``_Win32JobHandles._bind_signatures`` sets ``.argtypes``/``.restype`` on each function it
    uses; a bound method does not support arbitrary attribute assignment, so each entry here is
    a plain function object (assignable) rather than a class method, exactly mirroring how a
    real ``ctypes.WinDLL`` function pointer behaves.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.job_handle = 0x1_0000_0007  # > 2**32: proves 64-bit handles are not truncated
        self.process_handle = 0x2_0000_0009
        self.assign_result = True
        self.is_process_in_job_result = True
        self.active_process_count = 0
        self.query_information_result = True
        self.open_process_result: int | None = None
        self.create_job_result: int | None = None
        self.set_information_result = True
        self.terminate_job_result = True
        self.close_handle_result = True
        self.failed_close_handles: set[int] = set()

        def create_job_object_w(attrs: object, name: object) -> int:
            self.calls.append(("CreateJobObjectW", (attrs, name)))
            return self.job_handle if self.create_job_result is None else self.create_job_result

        def set_information_job_object(
            job_handle: int, info_class: int, info_ptr: object, info_size: int
        ) -> int:
            self.calls.append(("SetInformationJobObject", (job_handle, info_class, info_size)))
            return 1 if self.set_information_result else 0

        def query_information_job_object(
            job_handle: int, info_class: int, info_ptr: Any, info_size: int, returned_ptr: object
        ) -> int:
            self.calls.append(("QueryInformationJobObject", (job_handle, info_class)))
            if not self.query_information_result:
                return 0
            info_ptr.contents.ActiveProcesses = self.active_process_count
            return 1

        def open_process(access: int, inherit: bool, pid: int) -> int:
            self.calls.append(("OpenProcess", (access, inherit, pid)))
            if self.open_process_result is not None:
                return self.open_process_result
            return self.process_handle

        def assign_process_to_job_object(job_handle: int, process_handle: int) -> int:
            self.calls.append(("AssignProcessToJobObject", (job_handle, process_handle)))
            return 1 if self.assign_result else 0

        def is_process_in_job(process_handle: int, job_handle: int, result_ptr: Any) -> int:
            self.calls.append(("IsProcessInJob", (process_handle, job_handle)))
            result_ptr.contents.value = 1 if self.is_process_in_job_result else 0
            return 1

        def terminate_job_object(job_handle: int, exit_code: int) -> int:
            self.calls.append(("TerminateJobObject", (job_handle, exit_code)))
            return 1 if self.terminate_job_result else 0

        def close_handle(handle: int) -> int:
            self.calls.append(("CloseHandle", (handle,)))
            return 1 if self.close_handle_result and handle not in self.failed_close_handles else 0

        self.CreateJobObjectW = create_job_object_w
        self.SetInformationJobObject = set_information_job_object
        self.QueryInformationJobObject = query_information_job_object
        self.OpenProcess = open_process
        self.AssignProcessToJobObject = assign_process_to_job_object
        self.IsProcessInJob = is_process_in_job
        self.TerminateJobObject = terminate_job_object
        self.CloseHandle = close_handle


class TestWin32JobHandlesBindings:
    def test_argtypes_and_restype_are_declared_for_every_used_function(self) -> None:
        fake = _FakeKernel32()
        _Win32JobHandles(kernel32=fake)
        for name in (
            "CreateJobObjectW",
            "SetInformationJobObject",
            "QueryInformationJobObject",
            "OpenProcess",
            "AssignProcessToJobObject",
            "IsProcessInJob",
            "TerminateJobObject",
            "CloseHandle",
        ):
            bound = getattr(fake, name)
            assert getattr(bound, "argtypes", None), f"{name} has no argtypes declared"
            assert getattr(bound, "restype", None) is not None, f"{name} has no restype declared"

    def test_open_process_requests_all_three_required_access_bits(self) -> None:
        fake = _FakeKernel32()
        win32 = _Win32JobHandles(kernel32=fake)
        win32.open_process(4242)
        (_, (access, _inherit, pid)) = next(c for c in fake.calls if c[0] == "OpenProcess")
        assert pid == 4242
        assert access & _Win32JobHandles.PROCESS_TERMINATE
        assert access & _Win32JobHandles.PROCESS_SET_QUOTA
        assert access & _Win32JobHandles.PROCESS_QUERY_LIMITED_INFORMATION

    def test_handles_round_trip_as_64_bit_values_without_truncation(self) -> None:
        fake = _FakeKernel32()
        win32 = _Win32JobHandles(kernel32=fake)
        job_handle = win32.create_job_object()
        assert job_handle == fake.job_handle
        assert job_handle > 2**32
        process_handle = win32.open_process(1)
        assert process_handle == fake.process_handle
        assert process_handle > 2**32

    def test_assign_process_to_job_object_failure_is_reported(self) -> None:
        fake = _FakeKernel32()
        fake.assign_result = False
        win32 = _Win32JobHandles(kernel32=fake)
        assert win32.assign_process_to_job_object(fake.job_handle, fake.process_handle) is False

    def test_is_process_in_job_query_failure_is_reported(self) -> None:
        fake = _FakeKernel32()
        fake.is_process_in_job_result = False
        win32 = _Win32JobHandles(kernel32=fake)
        assert win32.is_process_in_job(fake.process_handle, fake.job_handle) is False

    def test_close_handle_is_called_for_every_opened_handle(self) -> None:
        fake = _FakeKernel32()
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))
        containment.create()
        worker = FakeProcessHandle(_pid=99)
        assert containment.confirm_worker_contained(worker, timeout=1.0, retry_interval=0.1)
        containment.close()
        closed_handles = {call[1][0] for call in fake.calls if call[0] == "CloseHandle"}
        assert fake.process_handle in closed_handles
        assert fake.job_handle in closed_handles

    def test_query_active_process_count_failure_raises_containment_error(self) -> None:
        fake = _FakeKernel32()
        fake.query_information_result = False
        win32 = _Win32JobHandles(kernel32=fake)
        with pytest.raises(Feat018ContainmentError):
            win32.query_active_process_count(fake.job_handle)

    def test_job_allocation_failure_leaves_no_partial_handle_to_close(self) -> None:
        fake = _FakeKernel32()
        fake.create_job_result = 0
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))

        with pytest.raises(Feat018ContainmentError):
            containment.create()

        assert containment._job_handle is None
        assert [call for call in fake.calls if call[0] == "CloseHandle"] == []

    def test_kill_on_close_configuration_failure_rolls_back_job_once(self) -> None:
        fake = _FakeKernel32()
        fake.set_information_result = False
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))

        with pytest.raises(Feat018ContainmentError, match="configuration failed"):
            containment.create()

        assert containment._job_handle is None
        assert [call for call in fake.calls if call[0] == "TerminateJobObject"] == [
            ("TerminateJobObject", (fake.job_handle, 1))
        ]
        assert [call for call in fake.calls if call[0] == "CloseHandle"] == [
            ("CloseHandle", (fake.job_handle,))
        ]

    def test_partial_job_cleanup_failure_retains_the_handle_for_retry(self) -> None:
        fake = _FakeKernel32()
        fake.set_information_result = False
        fake.close_handle_result = False
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))

        with pytest.raises(Feat018ContainmentError, match="rollback cleanup failed"):
            containment.create()

        assert containment._job_handle == fake.job_handle
        assert containment._cleanup_failed is True
        assert [call for call in fake.calls if call[0] == "CloseHandle"] == [
            ("CloseHandle", (fake.job_handle,))
        ]

        with pytest.raises(Feat018ContainmentError, match="unreleased handles"):
            containment.create()
        assert len([call for call in fake.calls if call[0] == "CreateJobObjectW"]) == 1

        fake.close_handle_result = True
        containment.close()

        assert containment._job_handle is None
        assert [call for call in fake.calls if call[0] == "CloseHandle"] == [
            ("CloseHandle", (fake.job_handle,)),
            ("CloseHandle", (fake.job_handle,)),
        ]

    @pytest.mark.parametrize("failure_stage", ["assignment", "verification"])
    def test_unregistered_open_process_handle_is_retained_when_close_fails(
        self, failure_stage: str
    ) -> None:
        fake = _FakeKernel32()
        if failure_stage == "assignment":
            fake.assign_result = False
        else:
            fake.is_process_in_job_result = False
        fake.failed_close_handles.add(fake.process_handle)
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))
        containment.create()

        assert not containment.confirm_worker_contained(
            FakeProcessHandle(), timeout=1.0, retry_interval=0.1
        )
        assert [call for call in fake.calls if call[0] == "CloseHandle"] == [
            ("CloseHandle", (fake.process_handle,))
        ]
        with pytest.raises(Feat018ContainmentError, match="unreleased process handle"):
            containment.confirm_worker_contained(
                FakeProcessHandle(_pid=100), timeout=1.0, retry_interval=0.1
            )
        assert len([call for call in fake.calls if call[0] == "OpenProcess"]) == 1

        fake.failed_close_handles.clear()
        containment.close()

        released = [call[1][0] for call in fake.calls if call[0] == "CloseHandle"]
        assert released.count(fake.process_handle) == 2
        assert released.count(fake.job_handle) == 1


# ------------------------------------------------------------------------------------------
# F1 -- truthful Windows cleanup verification
# ------------------------------------------------------------------------------------------


class TestWindowsJobObjectContainmentCleanupTruth:
    def _containment(self, fake: _FakeKernel32) -> WindowsJobObjectContainment:
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))
        containment.create()
        return containment

    @pytest.mark.parametrize("failed_handle", ["process", "job", "both"])
    def test_close_attempts_both_handles_and_retries_only_unreleased_handles(
        self, failed_handle: str
    ) -> None:
        fake = _FakeKernel32()
        containment = self._containment(fake)
        assert containment.confirm_worker_contained(
            FakeProcessHandle(), timeout=1.0, retry_interval=0.1
        )
        assert containment.is_empty() is True
        if failed_handle in {"process", "both"}:
            fake.failed_close_handles.add(fake.process_handle)
        if failed_handle in {"job", "both"}:
            fake.failed_close_handles.add(fake.job_handle)
        unreleased = set(fake.failed_close_handles)

        with pytest.raises(Feat018ContainmentError, match="handle cleanup failed"):
            containment.close()

        assert [call[1][0] for call in fake.calls if call[0] == "CloseHandle"] == [
            fake.process_handle, fake.job_handle,
        ]
        assert containment._process_handle == (
            fake.process_handle if fake.process_handle in unreleased else None
        )
        assert containment._job_handle == (
            fake.job_handle if fake.job_handle in unreleased else None
        )

        fake.failed_close_handles.clear()
        containment.close()

        released = [call[1][0] for call in fake.calls if call[0] == "CloseHandle"]
        for handle in (fake.process_handle, fake.job_handle):
            assert released.count(handle) == (2 if handle in unreleased else 1)
        assert containment._process_handle is None
        assert containment._job_handle is None

    def test_supervisor_retains_failed_containment_release_until_retry_succeeds(self) -> None:
        fake = _FakeKernel32()
        fake.failed_close_handles.add(fake.process_handle)
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))
        clock = FakeClock()
        launcher = _launcher(clock)
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        launcher.connection.push(
            {"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1}
        )
        _push_success_d9_frames(launcher.connection)
        launcher.connection.push({"seq": 3, "kind": "TERMINAL", "outcome": "SUCCEEDED"})
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(),
            launcher=launcher,
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )

        result = supervisor.run(_no_op_entry, ())

        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_failure is not None
        assert result.cleanup_failure.owned_containments == (containment,)
        assert containment._process_handle == fake.process_handle
        assert not result.cleanup_failure.retry_cleanup(
            grace_seconds=0.1,
            kill_join_seconds=0.1,
            cleanup_deadline_monotonic=clock() + 0.2,
            clock=clock,
        )
        assert result.cleanup_failure.owned_containments == (containment,)

        fake.failed_close_handles.clear()
        assert result.cleanup_failure.retry_cleanup(
            grace_seconds=0.1,
            kill_join_seconds=0.1,
            cleanup_deadline_monotonic=clock() + 0.2,
            clock=clock,
        )

        assert result.cleanup_failure.owned_containments == ()
        assert containment._process_handle is None
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        released = [call[1][0] for call in fake.calls if call[0] == "CloseHandle"]
        assert released.count(fake.job_handle) == 1
        assert released.count(fake.process_handle) == 3

    def test_lifecycle_cleanup_retains_containment_with_unreleased_job_handle(self) -> None:
        fake = _FakeKernel32()
        fake.failed_close_handles.add(fake.job_handle)
        containment = self._containment(fake)
        clock = FakeClock()
        boundary = Feat018LightningLifecycleProcessBoundary(
            controller=FakeLightningSessionController(clock),
            max_envelope_bytes=10_000,
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )

        failure = boundary._cleanup_resources(None, None, containment)

        assert isinstance(failure, Feat018CleanupFailedError)
        assert failure.owned_containments == (containment,)
        assert containment._job_handle == fake.job_handle

        fake.failed_close_handles.clear()
        assert failure.retry_cleanup(
            grace_seconds=0.1,
            kill_join_seconds=0.1,
            cleanup_deadline_monotonic=clock() + 0.2,
            clock=clock,
        )

        assert failure.owned_containments == ()
        assert containment._job_handle is None

    def test_is_empty_true_when_zero_active_processes(self) -> None:
        fake = _FakeKernel32()
        fake.active_process_count = 0
        assert self._containment(fake).is_empty() is True

    def test_is_empty_false_when_active_processes_remain(self) -> None:
        fake = _FakeKernel32()
        fake.active_process_count = 2
        assert self._containment(fake).is_empty() is False

    def test_is_empty_fails_closed_on_query_failure(self) -> None:
        fake = _FakeKernel32()
        fake.query_information_result = False
        assert self._containment(fake).is_empty() is False

    def test_cleanup_deadline_expiring_while_members_remain_reports_cleanup_failed(self) -> None:
        fake = _FakeKernel32()
        fake.active_process_count = 1  # never reaches zero
        containment = self._containment(fake)
        clock = FakeClock()
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(cleanup_deadline_seconds=0.2),
            launcher=_launcher(),
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )
        assert supervisor._verify_cleanup(containment) is CleanupStatus.CLEANUP_FAILED

    def test_cleanup_failure_overrides_a_previously_successful_terminal_result(self) -> None:
        fake = _FakeKernel32()
        fake.active_process_count = 1  # containment never reports empty
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))
        launcher = _launcher()
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        launcher.connection.push(
            {"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1}
        )
        _push_success_d9_frames(launcher.connection)
        launcher.connection.push({"seq": 3, "kind": "TERMINAL", "outcome": "SUCCEEDED"})
        clock = FakeClock()
        launcher.connection.clock = clock
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(cleanup_deadline_seconds=0.1),
            launcher=launcher,
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )
        result = supervisor.run(_no_op_entry, ())
        assert result.terminal_outcome == "SUCCEEDED"
        assert result.worker_terminal_outcome == "SUCCEEDED"
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.verdict is EffectiveOutcome.CLEANUP_FAILED
        assert result.is_success is False


# ------------------------------------------------------------------------------------------
# Real-adapter compatibility contract (real QwenVisionAdapter, fake QwenGenerationRunner)
# ------------------------------------------------------------------------------------------


@dataclass(slots=True)
class _SingleAttemptFakeRunner:
    """A fake QwenGenerationRunner: exactly one attempt per call, never loops internally."""

    outcomes: deque[object]
    calls: int = field(default=0, init=False)

    def generate(
        self,
        profile: object,
        runtime_config: object,
        image_path: Path,
        prompt: str,
    ) -> str:
        del profile, runtime_config, image_path, prompt
        self.calls += 1
        outcome = self.outcomes.popleft()
        if isinstance(outcome, BaseException):
            raise outcome
        return cast(str, outcome)


def _policy() -> LexicalRegressionContentPolicy:
    return LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())


def _success_payload() -> str:
    import json as _json

    return _json.dumps(
        {
            "entities": [],
            "actions": [],
            "relations": [],
            "themes": [],
            "ambiguous_regions": [],
        }
    )


def _media_validation_pass() -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="fixture:feat018:p2t2:validation-pass",
        validation_artifact_sha256="c" * 64,
        decision="PASS",
        validator_policy_version="media-quality-policy-v1",
    )


def _request(artifact_ref: str, digest: str) -> VisionUnderstandingRequestV2:
    return VisionUnderstandingRequestV2(
        correlation_id="feat018-p2t2-real-adapter-test",
        source_image_ref=VisionImageReferenceV1(artifact_ref=artifact_ref, sha256=digest),
        media_validation=_media_validation_pass(),
        requested_profile_id=vision_profile_catalog_v2().profiles[0].profile_id,
    )


def _real_adapter(runner: _SingleAttemptFakeRunner) -> QwenVisionAdapter:
    runtime_config = QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir"))
    return QwenVisionAdapter(
        runtime_config,
        content_policy=_policy(),
        prompt="fixture prompt",
        generation_runner=runner,
    )


class TestRealAdapterCompatibility:
    """Exercises the real, unmodified QwenVisionAdapter.understand() control flow."""

    @pytest.fixture()
    def image(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
        """A relative artifact_ref (VisionImageReferenceV1 rejects absolute paths)."""

        from hashlib import sha256

        image_path = tmp_path / "fixture.bin"
        image_path.write_bytes(b"feat018-fixture-bytes")
        monkeypatch.chdir(tmp_path)
        digest = sha256(image_path.read_bytes()).hexdigest()
        return image_path.name, digest

    def test_first_transient_permits_a_second_attempt(self, image: tuple[str, str]) -> None:
        artifact_ref, digest = image
        runner = _SingleAttemptFakeRunner(
            outcomes=deque([QwenTransientRuntimeError(), _success_payload()])
        )
        adapter = _real_adapter(runner)
        result = adapter.understand(_request(artifact_ref, digest))
        assert isinstance(result, VisionUnderstandingSuccessV2)
        assert result.attempt_number == 2
        assert runner.calls == 2

    def test_second_transient_stops_at_two_with_no_third_call(
        self, image: tuple[str, str]
    ) -> None:
        artifact_ref, digest = image
        runner = _SingleAttemptFakeRunner(
            outcomes=deque([QwenTransientRuntimeError(), QwenTransientRuntimeError()])
        )
        adapter = _real_adapter(runner)
        result = adapter.understand(_request(artifact_ref, digest))
        assert isinstance(result, VisionUnderstandingFailureV2)
        assert result.attempt_number == 2
        assert runner.calls == 2

    @pytest.mark.parametrize(
        "exception",
        [
            QwenTimeoutError(),
            TimeoutError(),
            QwenModelLoadError(),
            QwenDeviceUnavailableError(),
            QwenPermanentRuntimeError(),
        ],
    )
    def test_terminal_exceptions_never_retry(
        self, image: tuple[str, str], exception: BaseException
    ) -> None:
        artifact_ref, digest = image
        runner = _SingleAttemptFakeRunner(outcomes=deque([exception]))
        adapter = _real_adapter(runner)
        result = adapter.understand(_request(artifact_ref, digest))
        assert isinstance(result, VisionUnderstandingFailureV2)
        assert runner.calls == 1

    def test_wrapper_signalled_overflow_is_treated_as_permanent_failure(
        self, image: tuple[str, str]
    ) -> None:
        artifact_ref, digest = image
        runner = _SingleAttemptFakeRunner(
            outcomes=deque([QwenPermanentRuntimeError("bounded-output violation")])
        )
        adapter = _real_adapter(runner)
        result = adapter.understand(_request(artifact_ref, digest))
        assert isinstance(result, VisionUnderstandingFailureV2)
        assert runner.calls == 1

    def test_fake_runner_never_loops_internally(self, image: tuple[str, str]) -> None:
        artifact_ref, digest = image
        runner = _SingleAttemptFakeRunner(outcomes=deque([_success_payload()]))
        adapter = _real_adapter(runner)
        adapter.understand(_request(artifact_ref, digest))
        assert runner.calls == 1

    def test_classify_transient_remains_the_adapter_default(
        self, image: tuple[str, str]
    ) -> None:
        artifact_ref, digest = image
        runner = _SingleAttemptFakeRunner(outcomes=deque([RuntimeError("generic, not typed")]))
        adapter = _real_adapter(runner)
        result = adapter.understand(_request(artifact_ref, digest))
        assert isinstance(result, VisionUnderstandingFailureV2)
        assert runner.calls == 1


# ------------------------------------------------------------------------------------------
# Feat018BoundedKillableQwenGenerationRunner
# ------------------------------------------------------------------------------------------


class TestBoundedGenerationRunner:
    def _config(self, **overrides: object) -> Feat018BoundedRunnerConfig:
        defaults: dict[str, object] = {
            "total_adapter_cap_seconds": 300.0,
            "raw_output_max_bytes": 1000,
            "ipc_envelope_max_bytes": 2000,
            "stdout_max_bytes": D9_STDOUT_MAX_BYTES,
            "stderr_max_bytes": D9_STDERR_MAX_BYTES,
        }
        defaults.update(overrides)
        return Feat018BoundedRunnerConfig(**defaults)  # type: ignore[arg-type]

    def test_success_frame_returns_raw_output(self) -> None:
        launcher = _launcher()
        launcher.connection.push({"kind": "success", "raw_output": "hello world"})
        clock = FakeClock()
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(),
            worker_cap_deadline_monotonic=clock() + 300.0,
            launcher=launcher,
            clock=clock,
        )
        result = runner.generate(
            cast(object, None), cast(object, None), Path("x.png"), "prompt"
        )  # type: ignore[arg-type]
        assert result == "hello world"

    def test_no_frame_within_the_attempt_deadline_raises_timeout(self) -> None:
        clock = FakeClock()
        receive_timeouts: list[float] = []

        class _RecordingConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                receive_timeouts.append(timeout)
                return super().recv_frame(timeout)

        launcher = _launcher(clock)
        launcher.connection = _RecordingConnection(clock=clock)
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(per_attempt_timeout_seconds=1.0),
            worker_cap_deadline_monotonic=clock() + 300.0,
            launcher=launcher,
            clock=clock,
        )
        with pytest.raises(QwenTimeoutError):
            runner.generate(cast(object, None), cast(object, None), Path("x.png"), "prompt")
        assert receive_timeouts[0] == 1.0
        assert clock() == 1.0
        assert launcher.handle.kill_calls == 1
        assert launcher.connection.closed is True

    @pytest.mark.parametrize(
        ('arrival_seconds', 'accepted'),
        [(119.999, True), (120.0, False), (120.001, False)],
    )
    def test_attempt_boundary_is_checked_after_receive_before_total_cap(
        self, arrival_seconds: float, accepted: bool
    ) -> None:
        clock = FakeClock()
        receive_timeouts: list[float] = []

        class _ArrivalConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                receive_timeouts.append(timeout)
                if timeout > 0:
                    clock.set(arrival_seconds)
                    return {'kind': 'success', 'raw_output': 'within-attempt'}
                return None

        launcher = _launcher(clock)
        launcher.connection = _ArrivalConnection(clock=clock)
        reports: list[D9CaptureReport] = []
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(),
            worker_cap_deadline_monotonic=300.0,
            launcher=launcher,
            clock=clock,
            on_d9_report=reports.append,
        )
        if accepted:
            assert runner.generate(
                cast(object, None), cast(object, None), Path('x.png'), 'prompt'
            ) == 'within-attempt'
        else:
            with pytest.raises(QwenTimeoutError):
                runner.generate(cast(object, None), cast(object, None), Path('x.png'), 'prompt')
        assert receive_timeouts[0] == 120.0
        assert clock() < runner.worker_cap_deadline_monotonic
        assert len(reports) == 1

    def test_total_remaining_budget_wins_over_attempt_deadline(self) -> None:
        clock = FakeClock(start=290.0)
        launcher = _launcher(clock)
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(),
            worker_cap_deadline_monotonic=300.0,
            launcher=launcher,
            clock=clock,
        )
        with pytest.raises(QwenTimeoutError):
            runner.generate(cast(object, None), cast(object, None), Path('x.png'), 'prompt')
        assert clock() == 300.0
        assert len(launcher.launch_calls) == 1

    def test_attempt_uses_post_start_receipt_before_launcher_returns(self) -> None:
        clock = FakeClock(start=10.0)
        handle = FakeProcessHandle(started_at_monotonic=10.0)
        connection = FakeBoundedConnection(clock=clock)

        class _DelayedReturnLauncher:
            def launch(
                self, entry: Callable[..., None], args: tuple[object, ...]
            ) -> tuple[ProcessHandle, BoundedConnection]:
                del entry, args
                clock.advance(30.0)  # post-start endpoint wrapping does not extend the attempt
                return handle, connection

        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(),
            worker_cap_deadline_monotonic=300.0,
            launcher=_DelayedReturnLauncher(),
            clock=clock,
        )
        with pytest.raises(QwenTimeoutError):
            runner.generate(cast(object, None), cast(object, None), Path('x.png'), 'prompt')
        assert clock() == 130.0

    def test_retry_gets_new_attempt_deadline_without_resetting_total_cap(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as execution

        clock = FakeClock()
        receive_timeouts: list[float] = []
        handles: list[FakeProcessHandle] = []

        class _FirstAttemptConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                if timeout <= 0:
                    return None
                receive_timeouts.append(timeout)
                clock.advance(90.0)
                return {'kind': 'provider_failure'}

        class _SecondAttemptConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                if timeout > 0:
                    receive_timeouts.append(timeout)
                return super().recv_frame(timeout)

        class _RetryLauncher:
            def launch(
                self, entry: Callable[..., None], args: tuple[object, ...]
            ) -> tuple[ProcessHandle, BoundedConnection]:
                del entry, args
                handle = FakeProcessHandle(started_at_monotonic=clock())
                handles.append(handle)
                connection = (
                    _FirstAttemptConnection(clock=clock)
                    if len(handles) == 1
                    else _SecondAttemptConnection(clock=clock)
                )
                return handle, connection

        def explicit_transient(frame: Mapping[str, object]) -> str:
            assert frame.get('kind') == 'provider_failure'
            raise QwenTransientRuntimeError

        monkeypatch.setattr(execution, '_interpret_generation_child_frame', explicit_transient)
        monkeypatch.setattr(
            QwenVisionAdapter, '_resolve_verified_input_image', lambda self, request: Path('x.png')
        )
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(total_adapter_cap_seconds=150.0),
            worker_cap_deadline_monotonic=150.0,
            launcher=_RetryLauncher(),
            clock=clock,
        )
        adapter = QwenVisionAdapter(
            QwenVisionRuntimeConfig(model_dir=Path('fixture-model-dir')),
            content_policy=_policy(), prompt='fixture prompt', generation_runner=runner,
        )
        result = adapter.understand(_request('fixture.bin', 'a' * 64))
        assert isinstance(result, VisionUnderstandingFailureV2)
        assert result.attempt_number == 2
        assert result.error_code.value == 'VISION_TIMEOUT'
        assert result.retryable is False
        assert receive_timeouts == [120.0, 60.0]
        assert clock() == 150.0
        assert runner.worker_cap_deadline_monotonic == 150.0
        assert len(handles) == 2

    def test_attempt_timeout_is_terminal_in_the_unchanged_adapter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            QwenVisionAdapter, '_resolve_verified_input_image', lambda self, request: Path('x.png')
        )
        clock = FakeClock()
        launcher = _launcher(clock)
        reports: list[D9CaptureReport] = []
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(per_attempt_timeout_seconds=1.0),
            worker_cap_deadline_monotonic=300.0,
            launcher=launcher,
            clock=clock,
            on_d9_report=reports.append,
        )
        adapter = QwenVisionAdapter(
            QwenVisionRuntimeConfig(model_dir=Path('fixture-model-dir')),
            content_policy=_policy(), prompt='fixture prompt', generation_runner=runner,
        )
        result = adapter.understand(_request('fixture.bin', 'a' * 64))
        assert isinstance(result, VisionUnderstandingFailureV2)
        assert result.error_code.value == 'VISION_TIMEOUT'
        assert result.attempt_number == 1
        assert result.retryable is False
        assert len(launcher.launch_calls) == 1
        assert clock() == 1.0
        assert len(reports) == 1

    @pytest.mark.parametrize('timeout', [float('nan'), float('inf'), 0.0, -1.0, 120.001])
    def test_attempt_timeout_requires_a_finite_positive_bound(self, timeout: float) -> None:
        with pytest.raises(ValueError):
            self._config(per_attempt_timeout_seconds=timeout)

    def test_total_cap_already_exhausted_is_terminal_not_transient(self) -> None:
        clock = FakeClock(start=100.0)
        launcher = _launcher()
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(),
            worker_cap_deadline_monotonic=100.0,  # already at the deadline
            launcher=launcher,
            clock=clock,
        )
        with pytest.raises(QwenPermanentRuntimeError):
            runner.generate(cast(object, None), cast(object, None), Path("x.png"), "prompt")
        assert launcher.launch_calls == []

    def test_late_success_arriving_after_the_worker_deadline_is_discarded(self) -> None:
        launcher = _launcher()
        launcher.connection.push({"kind": "success", "raw_output": "too-late"})
        clock = FakeClock()

        class _LateConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                clock.advance(1000.0)  # simulate time passing past the deadline while waiting
                return super().recv_frame(timeout)

        late_connection = _LateConnection(inbox=launcher.connection.inbox)
        launcher.connection = late_connection
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(),
            worker_cap_deadline_monotonic=clock() + 10.0,
            launcher=launcher,
            clock=clock,
        )
        with pytest.raises(QwenTimeoutError):
            runner.generate(cast(object, None), cast(object, None), Path("x.png"), "prompt")

    def test_model_load_and_device_and_overflow_frames_map_to_typed_exceptions(self) -> None:
        cases: list[tuple[dict[str, object], type[BaseException]]] = [
            ({"kind": "model_load_failed"}, QwenModelLoadError),
            ({"kind": "device_unavailable"}, QwenDeviceUnavailableError),
            ({"kind": "timeout"}, QwenTimeoutError),
            ({"kind": "raw_output_overflow"}, QwenPermanentRuntimeError),
            ({"kind": "ipc_envelope_overflow"}, QwenPermanentRuntimeError),
        ]
        for frame, expected in cases:
            launcher = _launcher()
            launcher.connection.push(frame)
            clock = FakeClock()
            runner = Feat018BoundedKillableQwenGenerationRunner(
                config=self._config(),
                worker_cap_deadline_monotonic=clock() + 300.0,
                launcher=launcher,
                clock=clock,
            )
            with pytest.raises(expected):
                runner.generate(cast(object, None), cast(object, None), Path("x.png"), "prompt")

    def test_generate_calls_on_attempt_start_hook_exactly_once(self) -> None:
        launcher = _launcher()
        launcher.connection.push({"kind": "success", "raw_output": "ok"})
        clock = FakeClock()
        calls = {"n": 0}
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(),
            worker_cap_deadline_monotonic=clock() + 300.0,
            launcher=launcher,
            clock=clock,
            on_attempt_start=lambda: calls.__setitem__("n", calls["n"] + 1),
        )
        runner.generate(cast(object, None), cast(object, None), Path("x.png"), "prompt")
        assert calls["n"] == 1


# ------------------------------------------------------------------------------------------
# Feat018AdapterCallSupervisor
# ------------------------------------------------------------------------------------------


def _config(**overrides: object) -> Feat018BoundedRunnerConfig:
    defaults: dict[str, object] = {
        "total_adapter_cap_seconds": 10.0,
        "raw_output_max_bytes": 1000,
        "ipc_envelope_max_bytes": 2000,
        "stdout_max_bytes": D9_STDOUT_MAX_BYTES,
        "stderr_max_bytes": D9_STDERR_MAX_BYTES,
        "poll_interval_seconds": 1.0,
        "cleanup_deadline_seconds": 1.0,
        "containment_setup_timeout_seconds": 2.0,
    }
    defaults.update(overrides)
    return Feat018BoundedRunnerConfig(**defaults)  # type: ignore[arg-type]


def _supervisor(
    *,
    launcher: FakeProcessLauncher,
    containment: FakeContainmentBackend,
    clock: FakeClock,
    config: Feat018BoundedRunnerConfig | None = None,
) -> Feat018AdapterCallSupervisor:
    # An unreplaced FakeBoundedConnection has no way to represent a real Connection.poll's
    # blocking wait; bind this run's clock so an empty inbox advances it by `timeout` instead
    # of returning instantly, which would otherwise spin the supervisor's polling loop forever.
    if isinstance(launcher.connection, FakeBoundedConnection) and launcher.connection.clock is None:
        launcher.connection.clock = clock
    return Feat018AdapterCallSupervisor(
        config=config or _config(),
        launcher=launcher,
        containment_factory=lambda: containment,
        clock=clock,
        sleep=clock.advance,
    )


class TestD9StreamEnforcement:
    def test_ceiling_configuration_is_explicit_and_owner_bound(self) -> None:
        with pytest.raises(TypeError):
            Feat018BoundedRunnerConfig(
                total_adapter_cap_seconds=1.0,
                raw_output_max_bytes=1,
                ipc_envelope_max_bytes=1,
            )
        for field_name in ('stdout_max_bytes', 'stderr_max_bytes'):
            values = {
                'total_adapter_cap_seconds': 1.0,
                'raw_output_max_bytes': 1,
                'ipc_envelope_max_bytes': 1,
                'stdout_max_bytes': D9_STDOUT_MAX_BYTES,
                'stderr_max_bytes': D9_STDERR_MAX_BYTES,
            }
            values[field_name] = 0
            with pytest.raises(ValueError):
                Feat018BoundedRunnerConfig(**values)
            values[field_name] = 1
            with pytest.raises(ValueError):
                Feat018BoundedRunnerConfig(**values)

        with pytest.raises(ValueError):
            D9ProcessStreamCapture(
                D9ProcessRole.OUTER_ADAPTER_WORKER,
                None,
                1,
                D9_STDERR_MAX_BYTES,
            )

        with pytest.raises(ValueError):
            D9ProcessStreamCapture(
                D9ProcessRole.OUTER_ADAPTER_WORKER,
                1,
                D9_STDOUT_MAX_BYTES,
                D9_STDERR_MAX_BYTES,
            )
        with pytest.raises(ValueError):
            D9ProcessStreamCapture(
                D9ProcessRole.INNER_GENERATION_CHILD,
                None,
                D9_STDOUT_MAX_BYTES,
                D9_STDERR_MAX_BYTES,
            )

    @pytest.mark.parametrize(
        ('stream', 'ceiling'),
        [
            (D9StreamName.STDOUT, D9_STDOUT_MAX_BYTES),
            (D9StreamName.STDERR, D9_STDERR_MAX_BYTES),
        ],
    )
    def test_zero_under_exact_and_first_byte_overflow(
        self, stream: D9StreamName, ceiling: int
    ) -> None:
        zero = D9BoundedByteCapture(D9ProcessRole.OUTER_ADAPTER_WORKER, None, stream, ceiling)
        assert zero.finalize().bytes_seen == 0

        under = D9BoundedByteCapture(D9ProcessRole.OUTER_ADAPTER_WORKER, None, stream, ceiling)
        under.observe_chunk(b'\x00' * (ceiling - 1))
        under_observation = under.finalize()
        assert under_observation.bytes_seen == ceiling - 1
        assert under_observation.disposition is D9StreamDisposition.ACCEPTED

        exact = D9BoundedByteCapture(D9ProcessRole.OUTER_ADAPTER_WORKER, None, stream, ceiling)
        exact.observe_chunk(b'\xff' * ceiling)
        exact_observation = exact.finalize()
        assert exact_observation.bytes_seen == ceiling
        assert exact_observation.disposition is D9StreamDisposition.ACCEPTED

        overflow = D9BoundedByteCapture(D9ProcessRole.OUTER_ADAPTER_WORKER, None, stream, ceiling)
        overflow.observe_chunk(b'\x00' * ceiling)
        overflow.observe_chunk(b'\x80')
        overflow_observation = overflow.finalize()
        assert overflow_observation.bytes_seen == ceiling + 1
        assert overflow_observation.disposition is D9StreamDisposition.FAILED
        assert overflow_observation.failure_code is (
            D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED
            if stream is D9StreamName.STDOUT
            else D9StreamFailureCode.STDERR_LIMIT_EXCEEDED
        )
        assert not hasattr(overflow, 'payload')

    def test_binary_malformed_and_nul_bytes_are_counted_without_decoding(self) -> None:
        capture = D9BoundedByteCapture(
            D9ProcessRole.INNER_GENERATION_CHILD,
            1,
            D9StreamName.STDOUT,
            D9_STDOUT_MAX_BYTES,
        )
        raw_bytes = memoryview(b'\xff\x00\xc3')
        capture.observe_chunk(raw_bytes)
        observation = capture.finalize()
        assert observation.bytes_seen == 3
        assert observation.failure_code is None
        assert 'ff' not in repr(observation).lower()

    def test_forged_over_limit_within_limit_observation_cannot_succeed(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push({'seq': 1, 'kind': 'ADAPTER_STARTED'})
        launcher.connection.push(
            {'seq': 2, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 1}
        )
        _push_success_d9_frames(launcher.connection)
        for frame in launcher.connection.inbox:
            if (
                frame.get('process_role') == D9ProcessRole.OUTER_ADAPTER_WORKER.value
                and frame.get('stream') == D9StreamName.STDOUT.value
            ):
                frame['bytes_seen'] = D9_STDOUT_MAX_BYTES + 1
                break
        launcher.connection.push(
            {'seq': 3, 'kind': 'TERMINAL', 'outcome': 'SUCCEEDED', 'raw_status': 'SUCCEEDED'}
        )

        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )

        assert result.final_state is ProgressState.FROZEN
        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.primary_failure_reason == 'malformed D9 stream observation'
        assert not _adapter_result_is_accepted_success(result)

    @pytest.mark.parametrize(
        ('bytes_seen', 'terminal_category', 'failure_code'),
        [
            (
                D9_STDOUT_MAX_BYTES,
                D9StreamTerminalCategory.LIMIT_EXCEEDED,
                D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED,
            ),
            (
                D9_STDOUT_MAX_BYTES + 1,
                D9StreamTerminalCategory.READ_FAILED,
                D9StreamFailureCode.STDOUT_CAPTURE_READ_FAILED,
            ),
            (
                0,
                D9StreamTerminalCategory.WORKER_DIED_BEFORE_STREAM_FINALIZATION,
                D9StreamFailureCode.STREAM_FINALIZATION_FAILED,
            ),
        ],
    )
    def test_observation_contract_rejects_inconsistent_count_category_pairs(
        self,
        bytes_seen: int,
        terminal_category: D9StreamTerminalCategory,
        failure_code: D9StreamFailureCode,
    ) -> None:
        with pytest.raises(ValueError):
            D9StreamObservation(
                process_role=D9ProcessRole.OUTER_ADAPTER_WORKER,
                attempt_number=None,
                stream=D9StreamName.STDOUT,
                bytes_seen=bytes_seen,
                ceiling=D9_STDOUT_MAX_BYTES,
                disposition=D9StreamDisposition.FAILED,
                terminal_category=terminal_category,
                failure_code=failure_code,
            )

    def test_overflow_triggers_cleanup_before_total_deadline_and_preserves_fact(
        self,
    ) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        config = _config(total_adapter_cap_seconds=10.0)
        launcher.connection.push({'seq': 1, 'kind': 'ADAPTER_STARTED'})
        launcher.connection.push(
            {'seq': 2, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 1}
        )
        frame = _d9_observation_frame_for_test(
            D9ProcessRole.INNER_GENERATION_CHILD, 1, D9StreamName.STDOUT
        )
        frame.update(
            {
                'bytes_seen': D9_STDOUT_MAX_BYTES + 1,
                'disposition': D9StreamDisposition.FAILED.value,
                'terminal_category': D9StreamTerminalCategory.LIMIT_EXCEEDED.value,
                'failure_code': D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED.value,
            }
        )
        launcher.connection.push(frame)

        result = _supervisor(
            launcher=launcher,
            containment=containment,
            clock=clock,
            config=config,
        ).run(_no_op_entry, ())

        assert clock() < config.total_adapter_cap_seconds
        assert launcher.handle.terminate_calls == 1
        assert containment.terminate_calls == 1
        assert result.primary_failure_reason == 'D9 stream enforcement failed'
        assert D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED in result.d9_failure_codes
        assert result.effective_outcome is EffectiveOutcome.FAILED

    def test_inner_failure_signal_stops_generation_without_retry_or_fact_loss(
        self,
    ) -> None:
        launcher = _launcher()
        clock = FakeClock()
        reports: list[D9CaptureReport] = []
        failure_code = D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED
        launcher.connection.push(
            {'kind': 'D9_STREAM_FAILURE', 'failure_code': failure_code.value}
        )
        launcher.connection.push(
            {'kind': 'd9_failure', 'failure_code': failure_code.value}
        )
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=_config(),
            worker_cap_deadline_monotonic=clock() + 10.0,
            launcher=launcher,
            clock=clock,
            on_d9_report=reports.append,
        )

        with pytest.raises(QwenPermanentRuntimeError, match='D9 stream enforcement failed'):
            runner.generate(cast(object, None), cast(object, None), Path('x.png'), 'prompt')

        assert len(launcher.launch_calls) == 1
        assert launcher.handle.terminate_calls == 1
        assert reports[0].failure_codes == (failure_code,)

    def test_generation_child_uses_the_already_bounded_ipc_endpoint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sketch2life.infrastructure.ai.qwen_vision as qwen_module

        def fail_before_model_work(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError

        monkeypatch.setattr(qwen_module, '_default_model_factory', fail_before_model_work)
        connection = FakeBoundedConnection()

        _generation_child_entry_with_capture(
            connection,
            cast(Any, object()),
            cast(Any, object()),
            'fixture.png',
            'fixture prompt',
            1_000,
            1_000_000,
            capture_factory=_fake_d9_capture_factory,
            attempt_number=1,
        )

        assert [frame['kind'] for frame in connection.sent] == [
            'D9_STREAM_OBSERVATION',
            'D9_STREAM_OBSERVATION',
            'model_load_failed',
        ]

    def test_queued_late_failure_after_terminal_invalidates_success(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push({'seq': 1, 'kind': 'ADAPTER_STARTED'})
        launcher.connection.push(
            {'seq': 2, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 1}
        )
        _push_success_d9_frames(launcher.connection)
        launcher.connection.push(
            {'seq': 3, 'kind': 'TERMINAL', 'outcome': 'SUCCEEDED', 'raw_status': 'SUCCEEDED'}
        )
        launcher.connection.push(
            {
                'kind': 'D9_STREAM_FAILURE',
                'failure_code': D9StreamFailureCode.STDOUT_LATE_OUTPUT.value,
            }
        )

        result = _supervisor(
            launcher=launcher,
            containment=containment,
            clock=clock,
        ).run(_no_op_entry, ())

        assert result.final_state is ProgressState.TERMINAL
        assert result.terminal_outcome == 'SUCCEEDED'
        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.primary_failure_reason == 'D9 stream enforcement failed'
        assert D9StreamFailureCode.STDOUT_LATE_OUTPUT in result.d9_failure_codes
        assert not launcher.connection.inbox
        assert not _adapter_result_is_accepted_success(result)

    def test_real_connection_zero_timeout_drains_queued_late_failure(self) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000_000)
        sender = MultiprocessingBoundedConnection(sender_raw, 1_000_000)
        expected = {
            'kind': 'D9_STREAM_FAILURE',
            'failure_code': D9StreamFailureCode.STDOUT_LATE_OUTPUT.value,
        }
        try:
            sender.send_frame(expected)
            assert receiver.recv_frame(0.0) == expected
        finally:
            sender.close()
            receiver.close()

    def test_sustained_output_keeps_bookkeeping_bounded_after_overflow(self) -> None:
        notifications: list[D9StreamFailureCode] = []
        capture = D9BoundedByteCapture(
            D9ProcessRole.OUTER_ADAPTER_WORKER,
            None,
            D9StreamName.STDOUT,
            D9_STDOUT_MAX_BYTES,
            notifications.append,
        )
        capture.observe_chunk(b'x' * (D9_STDOUT_MAX_BYTES + 1))
        for _ in range(10_000):
            capture.observe_chunk(b'x')
        observation = capture.finalize()

        assert observation.bytes_seen == D9_STDOUT_MAX_BYTES + 1
        assert observation.failure_code is D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED
        assert notifications == [D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED]
        assert len(capture.events) <= 8

    def test_real_capture_normal_child_exit_drains_both_streams(self) -> None:
        probe = (
            'import os; '
            'from sketch2life.benchmark.feat018_live_lightning_execution import '
            'D9ProcessRole, D9ProcessStreamCapture, D9_STDERR_MAX_BYTES, D9_STDOUT_MAX_BYTES; '
            'capture = D9ProcessStreamCapture('
            'D9ProcessRole.INNER_GENERATION_CHILD, 1, '
            'D9_STDOUT_MAX_BYTES, D9_STDERR_MAX_BYTES); '
            "os.write(1, b'probe-out'); os.write(2, b'probe-err'); "
            'capture.finalize(); report = capture.verify_writer_quiescence(); '
            'assert not report.failed and all(item.bytes_seen == 9 for item in report.observations)'
        )
        result = subprocess.run(
            [sys.executable, '-c', probe],
            cwd=Path(__file__).parents[2],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout == b''
        assert result.stderr == b''

    def test_real_capture_late_output_before_quiescence_invalidates_success(self) -> None:
        probe = (
            'import json, os, sys; '
            'from sketch2life.benchmark.feat018_live_lightning_execution import '
            'D9ProcessRole, D9ProcessStreamCapture, D9_STDERR_MAX_BYTES, D9_STDOUT_MAX_BYTES; '
            'report_fd = os.dup(1); failures = []; '
            'capture = D9ProcessStreamCapture('
            'D9ProcessRole.INNER_GENERATION_CHILD, 1, '
            'D9_STDOUT_MAX_BYTES, D9_STDERR_MAX_BYTES, failures.append); '
            'initial = capture.finalize(); '
            "late_count = os.write(1, b'late'); "
            "buffered_count = sys.stderr.write('buffered'); "
            'final = capture.verify_writer_quiescence(); '
            "payload = {'initial_failed': initial.failed, 'late_count': late_count, "
            "'buffered_count': buffered_count, 'final_failed': final.failed, "
            "'failure_codes': sorted(item.value for item in failures)}; "
            "os.write(report_fd, (json.dumps(payload) + '\\n').encode('utf-8')); "
            'os.close(report_fd)'
        )
        result = subprocess.run(
            [sys.executable, '-c', probe],
            cwd=Path(__file__).parents[2],
            capture_output=True,
            check=False,
            timeout=5.0,
        )

        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload == {
            'initial_failed': False,
            'late_count': 4,
            'buffered_count': 8,
            'final_failed': True,
            'failure_codes': sorted(
                [
                    D9StreamFailureCode.STDOUT_LATE_OUTPUT.value,
                    D9StreamFailureCode.STDERR_LATE_OUTPUT.value,
                ]
            ),
        }
        assert result.stderr == b''

    @pytest.mark.parametrize(
        ('method_name', 'failure_code'),
        [
            ('mark_read_failed', D9StreamFailureCode.STDOUT_CAPTURE_READ_FAILED),
            (
                'mark_worker_died_before_finalization',
                D9StreamFailureCode.WORKER_DIED_BEFORE_STREAM_FINALIZATION,
            ),
            ('mark_finalization_failed', D9StreamFailureCode.STREAM_FINALIZATION_FAILED),
        ],
    )
    def test_typed_read_death_and_finalization_failures(
        self, method_name: str, failure_code: D9StreamFailureCode
    ) -> None:
        capture = D9BoundedByteCapture(
            D9ProcessRole.OUTER_ADAPTER_WORKER,
            None,
            D9StreamName.STDOUT,
            D9_STDOUT_MAX_BYTES,
        )
        getattr(capture, method_name)()
        observation = capture.finalize()
        assert observation.failure_code is failure_code
        assert observation.disposition is D9StreamDisposition.FAILED

    def test_event_order_and_late_output_are_fail_closed(self) -> None:
        capture = D9BoundedByteCapture(
            D9ProcessRole.OUTER_ADAPTER_WORKER,
            None,
            D9StreamName.STDOUT,
            D9_STDOUT_MAX_BYTES,
        )
        capture.observe_chunk(b'first')
        capture.stop_and_close()
        capture.bounded_drain()
        first = capture.finalize()
        capture.mark_published()
        capture.observe_chunk(b'late')
        second = capture.finalize()
        assert first.disposition is D9StreamDisposition.ACCEPTED
        assert second.failure_code is D9StreamFailureCode.STDOUT_LATE_OUTPUT
        assert capture.events == (
            'capture',
            'stop_close',
            'bounded_drain',
            'finalize',
            'publish',
            'reject_late',
            'finalize',
        )

    def test_both_stream_overflow_publishes_only_typed_metadata(self) -> None:
        stdout = D9BoundedByteCapture(
            D9ProcessRole.OUTER_ADAPTER_WORKER,
            None,
            D9StreamName.STDOUT,
            D9_STDOUT_MAX_BYTES,
        )
        stderr = D9BoundedByteCapture(
            D9ProcessRole.OUTER_ADAPTER_WORKER,
            None,
            D9StreamName.STDERR,
            D9_STDERR_MAX_BYTES,
        )
        stdout.observe_chunk(
            (b'RAW-STDOUT-SECRET' * (D9_STDOUT_MAX_BYTES // 17 + 1))[
                : D9_STDOUT_MAX_BYTES + 1
            ]
        )
        stderr.observe_chunk(
            (b'RAW-STDERR-SECRET' * (D9_STDERR_MAX_BYTES // 17 + 1))[
                : D9_STDERR_MAX_BYTES + 1
            ]
        )
        report = D9CaptureReport((stdout.finalize(), stderr.finalize()))
        assert D9StreamFailureCode.BOTH_STREAM_LIMITS_EXCEEDED in report.failure_codes
        assert all(isinstance(item, D9StreamObservation) for item in report.observations)
        assert 'RAW-STDOUT-SECRET' not in repr(report)
        assert 'RAW-STDERR-SECRET' not in repr(report)

    def test_inner_worker_death_is_typed_and_does_not_retry(self) -> None:
        launcher = _launcher()
        launcher.handle.mark_dead()
        clock = FakeClock()
        reports: list[D9CaptureReport] = []
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=_config(),
            worker_cap_deadline_monotonic=clock() + 10.0,
            launcher=launcher,
            clock=clock,
            on_d9_report=reports.append,
        )
        with pytest.raises(QwenPermanentRuntimeError, match='generation worker died'):
            runner.generate(cast(object, None), cast(object, None), Path('x.png'), 'prompt')
        assert len(launcher.launch_calls) == 1
        assert reports[0].failure_codes == (
            D9StreamFailureCode.WORKER_DIED_BEFORE_STREAM_FINALIZATION,
        )

    def test_supervisor_rejects_success_after_a_stream_limit_failure(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push({'seq': 1, 'kind': 'ADAPTER_STARTED'})
        launcher.connection.push(
            {'seq': 2, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 1}
        )
        _push_success_d9_frames(launcher.connection)
        for frame in launcher.connection.inbox:
            if (
                frame.get('process_role') == D9ProcessRole.OUTER_ADAPTER_WORKER.value
                and frame.get('stream') == D9StreamName.STDOUT.value
            ):
                frame.update(
                    {
                        'bytes_seen': D9_STDOUT_MAX_BYTES + 1,
                        'disposition': D9StreamDisposition.FAILED.value,
                        'terminal_category': D9StreamTerminalCategory.LIMIT_EXCEEDED.value,
                        'failure_code': D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED.value,
                    }
                )
                break
        launcher.connection.push({'seq': 3, 'kind': 'TERMINAL', 'outcome': 'SUCCEEDED'})
        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )
        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert D9StreamFailureCode.STDOUT_LIMIT_EXCEEDED in result.d9_failure_codes
        assert result.primary_failure_reason == 'D9 stream enforcement failed'

    def test_one_attempt_with_stdout_stderr_observations_succeeds(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push({'seq': 1, 'kind': 'ADAPTER_STARTED'})
        launcher.connection.push(
            {'seq': 2, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 1}
        )
        _push_success_d9_frames(launcher.connection, attempt_numbers=(1,))
        launcher.connection.push(
            {'seq': 3, 'kind': 'TERMINAL', 'outcome': 'SUCCEEDED', 'raw_status': 'SUCCEEDED'}
        )
        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )
        assert result.effective_outcome is EffectiveOutcome.SUCCEEDED
        assert result.attempt_count == 1
        assert result.primary_failure_reason is None
        assert len(result.d9_observations) == 4
        assert _adapter_result_is_accepted_success(result)

    def test_two_accepted_attempts_publish_independent_d9_observations_and_succeed(
        self,
    ) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push({'seq': 1, 'kind': 'ADAPTER_STARTED'})
        launcher.connection.push(
            {'seq': 2, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 1}
        )
        for stream in D9StreamName:
            launcher.connection.push(
                _d9_observation_frame_for_test(D9ProcessRole.INNER_GENERATION_CHILD, 1, stream)
            )
        launcher.connection.push(
            {'seq': 3, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 2}
        )
        for stream in D9StreamName:
            launcher.connection.push(
                _d9_observation_frame_for_test(D9ProcessRole.INNER_GENERATION_CHILD, 2, stream)
            )
        for stream in D9StreamName:
            launcher.connection.push(
                _d9_observation_frame_for_test(D9ProcessRole.OUTER_ADAPTER_WORKER, None, stream)
            )
        launcher.connection.push(
            {'seq': 4, 'kind': 'TERMINAL', 'outcome': 'SUCCEEDED', 'raw_status': 'SUCCEEDED'}
        )
        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )

        # The second attempt's inner-child observations must not collide with the first's and
        # must not be misreported as a protocol violation (the confirmed independent-review
        # blocker: deduplication used to key only on (process_role, stream)).
        assert result.primary_failure_reason is None
        assert result.final_state is ProgressState.TERMINAL
        assert result.attempt_count == 2
        assert result.effective_outcome is EffectiveOutcome.SUCCEEDED
        assert len(result.d9_observations) == 6
        inner_attempt_numbers = sorted(
            item.attempt_number
            for item in result.d9_observations
            if item.process_role is D9ProcessRole.INNER_GENERATION_CHILD
        )
        assert inner_attempt_numbers == [1, 1, 2, 2]
        outer_attempt_numbers = {
            item.attempt_number
            for item in result.d9_observations
            if item.process_role is D9ProcessRole.OUTER_ADAPTER_WORKER
        }
        assert outer_attempt_numbers == {None}
        assert _adapter_result_is_accepted_success(result)

    def test_duplicate_observation_within_one_attempt_is_still_rejected(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push({'seq': 1, 'kind': 'ADAPTER_STARTED'})
        launcher.connection.push(
            {'seq': 2, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 1}
        )
        launcher.connection.push(
            _d9_observation_frame_for_test(
                D9ProcessRole.INNER_GENERATION_CHILD, 1, D9StreamName.STDOUT
            )
        )
        launcher.connection.push(
            _d9_observation_frame_for_test(
                D9ProcessRole.INNER_GENERATION_CHILD, 1, D9StreamName.STDOUT
            )
        )
        launcher.connection.push({'seq': 3, 'kind': 'TERMINAL', 'outcome': 'SUCCEEDED'})
        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )
        assert result.final_state is ProgressState.FROZEN
        assert result.primary_failure_reason == 'malformed D9 stream observation'
        assert result.effective_outcome is EffectiveOutcome.FAILED

    def test_observation_claiming_an_unaccepted_attempt_number_is_rejected(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push({'seq': 1, 'kind': 'ADAPTER_STARTED'})
        launcher.connection.push(
            {'seq': 2, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 1}
        )
        launcher.connection.push(
            _d9_observation_frame_for_test(
                D9ProcessRole.INNER_GENERATION_CHILD, 2, D9StreamName.STDOUT
            )
        )
        launcher.connection.push({'seq': 3, 'kind': 'TERMINAL', 'outcome': 'SUCCEEDED'})
        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )
        assert result.final_state is ProgressState.FROZEN
        assert result.primary_failure_reason == 'malformed D9 stream observation'

    def test_runner_assigns_increasing_attempt_numbers_across_two_calls_and_never_retries(
        self,
    ) -> None:
        clock = FakeClock()
        connection_one = FakeBoundedConnection(clock=clock)
        connection_two = FakeBoundedConnection(clock=clock)
        for connection, attempt_number in ((connection_one, 1), (connection_two, 2)):
            for stream in D9StreamName:
                connection.push(
                    _d9_observation_frame_for_test(
                        D9ProcessRole.INNER_GENERATION_CHILD, attempt_number, stream
                    )
                )
            connection.push({'kind': 'success', 'raw_output': f'attempt-{attempt_number}'})

        @dataclass(slots=True)
        class _TwoAttemptLauncher:
            connections: list[FakeBoundedConnection]
            launch_calls: list[tuple[Callable[..., None], tuple[object, ...]]] = field(
                default_factory=list, init=False
            )

            def launch(
                self, entry: Callable[..., None], args: tuple[object, ...]
            ) -> tuple[ProcessHandle, FakeBoundedConnection]:
                index = len(self.launch_calls)
                self.launch_calls.append((entry, args))
                return FakeProcessHandle(), self.connections[index]

        launcher = _TwoAttemptLauncher(connections=[connection_one, connection_two])
        reports: list[D9CaptureReport] = []
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=_config(),
            worker_cap_deadline_monotonic=clock() + 10.0,
            launcher=launcher,
            clock=clock,
            on_d9_report=reports.append,
        )
        first = runner.generate(cast(object, None), cast(object, None), Path('x.png'), 'prompt')
        second = runner.generate(cast(object, None), cast(object, None), Path('x.png'), 'prompt')

        assert first == 'attempt-1'
        assert second == 'attempt-2'
        assert len(launcher.launch_calls) == 2
        assert launcher.launch_calls[0][1][-1] == 1
        assert launcher.launch_calls[1][1][-1] == 2
        assert len(reports) == 2
        assert {item.attempt_number for item in reports[0].observations} == {1}
        assert {item.attempt_number for item in reports[1].observations} == {2}
        assert not reports[0].failed
        assert not reports[1].failed

def _d9_observation_frame_for_test(
    process_role: D9ProcessRole, attempt_number: int | None, stream: D9StreamName
) -> dict[str, object]:
    return {
        'kind': 'D9_STREAM_OBSERVATION',
        'process_role': process_role.value,
        'attempt_number': attempt_number,
        'stream': stream.value,
        'bytes_seen': 0,
        'ceiling': (
            D9_STDOUT_MAX_BYTES if stream is D9StreamName.STDOUT else D9_STDERR_MAX_BYTES
        ),
        'disposition': D9StreamDisposition.ACCEPTED.value,
        'terminal_category': D9StreamTerminalCategory.WITHIN_LIMIT.value,
        'failure_code': None,
    }


def _push_success_d9_frames(
    connection: FakeBoundedConnection, *, attempt_numbers: tuple[int, ...] = (1,)
) -> None:
    """Push one clean outer-worker pair plus one clean inner-child pair per attempt."""

    for stream in D9StreamName:
        connection.push(
            _d9_observation_frame_for_test(D9ProcessRole.OUTER_ADAPTER_WORKER, None, stream)
        )
    for attempt_number in attempt_numbers:
        for stream in D9StreamName:
            connection.push(
                _d9_observation_frame_for_test(
                    D9ProcessRole.INNER_GENERATION_CHILD, attempt_number, stream
                )
            )


def _successful_supervisor_result() -> SupervisorRunResult:
    return SupervisorRunResult(
        final_state=ProgressState.TERMINAL,
        attempt_count=1,
        terminal_outcome="SUCCEEDED",
        cleanup_status=CleanupStatus.SUCCEEDED,
        effective_outcome=EffectiveOutcome.SUCCEEDED,
        raw_status="SUCCEEDED",
        d9_observations=(
            _fake_d9_report(D9ProcessRole.OUTER_ADAPTER_WORKER).observations
            + _fake_d9_report(D9ProcessRole.INNER_GENERATION_CHILD).observations
        ),
    )


@dataclass(slots=True)
class FakeBoundedAdapterCall:
    """A call-shaped double that never enters the real bounded runner."""

    clock: FakeClock
    result: SupervisorRunResult = field(default_factory=_successful_supervisor_result)
    advance_seconds: float = 0.0
    call_times: list[float] = field(default_factory=list, init=False)
    arguments: list[tuple[object, ...]] = field(default_factory=list, init=False)

    def __call__(
        self,
        request: VisionUnderstandingRequestV2,
        runtime_config: QwenVisionRuntimeConfig,
        content_policy: object,
        prompt: str,
        config: Feat018BoundedRunnerConfig,
        *,
        session_id: str | None = None,
    ) -> SupervisorRunResult:
        self.call_times.append(self.clock())
        self.arguments.append(
            (request, runtime_config, content_policy, prompt, config, session_id)
        )
        self.clock.advance(self.advance_seconds)
        return self.result


def _live_smoke_config(**overrides: object) -> Feat018LiveSmokeConfig:
    defaults: dict[str, object] = {
        "bounded_runner_config": _config(total_adapter_cap_seconds=10.0),
        "session_provision_timeout_seconds": 5,
        "session_ttl_seconds": 30,
        "gpu_minute_cap": 1,
        "session_termination_deadline_seconds": 2,
        "placement_approval": LightningPlacementApproval(
            gpu_sku="NVIDIA_L4",
            device_index=0,
            device_count=1,
            minimum_vram_mib=1,
            cuda_required=True,
            bf16_required=True,
            single_device_required=True,
        ),
    }
    defaults.update(overrides)
    return Feat018LiveSmokeConfig(**defaults)  # type: ignore[arg-type]


def _process_live_smoke_config() -> Feat018LiveSmokeConfig:
    return _live_smoke_config(
        session_provision_timeout_seconds=3,
        session_termination_deadline_seconds=2,
        bounded_runner_config=_config(
            total_adapter_cap_seconds=3.0,
            cleanup_deadline_seconds=1.0,
            containment_setup_timeout_seconds=1.0,
        ),
    )


def _run_process_boundary_smoke(
    controller: _ProcessLightningSessionController,
    *,
    config: Feat018LiveSmokeConfig | None = None,
) -> tuple[Feat018LiveSmokeResult, FakeBoundedAdapterCall]:
    adapter = FakeBoundedAdapterCall(FakeClock())
    result = run_live_smoke(
        _request("fixture.bin", "a" * 64),
        QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir")),
        _policy(),
        "fixture prompt",
        controller=controller,
        config=config or _process_live_smoke_config(),
        session_id="synthetic-session",
        preflight=FakeLightningPreflight(),
        finalizer=FakeLiveSmokeFinalizer(),
        adapter_call=adapter,
    )
    return result, adapter


def _synthetic_pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class TestLiveSmokeProvisioningContract:
    def _run(
        self,
        controller: FakeLightningSessionController,
        adapter: FakeBoundedAdapterCall | None,
        *,
        config: Feat018LiveSmokeConfig | None = None,
        preflight: FakeLightningPreflight | None | object = _UNSET_LIGHTNING_RESULT,
        finalizer: FakeLiveSmokeFinalizer | None | object = _UNSET_LIGHTNING_RESULT,
    ) -> Feat018LiveSmokeResult:
        active_config = config or _live_smoke_config()
        controller.ttl_seconds = active_config.session_ttl_seconds
        active_preflight = (
            FakeLightningPreflight()
            if preflight is _UNSET_LIGHTNING_RESULT
            else cast(FakeLightningPreflight | None, preflight)
        )
        active_finalizer = (
            FakeLiveSmokeFinalizer()
            if finalizer is _UNSET_LIGHTNING_RESULT
            else cast(FakeLiveSmokeFinalizer | None, finalizer)
        )
        request = _request("fixture.bin", "a" * 64)
        return run_live_smoke(
            request,
            QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir")),
            _policy(),
            "fixture prompt",
            controller=controller,
            config=active_config,
            session_id="synthetic-session",
            preflight=active_preflight,
            finalizer=active_finalizer,
            adapter_call=adapter,
            lifecycle_boundary=FakeInlineLightningLifecycleBoundary(controller, controller.clock),
            clock=controller.clock,
        )

    def test_successful_provisioning_reaches_session_ready(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.SUCCEEDED
        assert result.session_ready is True
        assert result.adapter_call_count == 1
        assert result.attempt_count == 1
        assert controller.provision_calls == 1
        assert controller.ready_calls == 1
        assert controller.termination_calls == 1

    def test_provision_timeout_is_failed_and_never_calls_adapter(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(
            clock,
            provision_result=TimeoutError(),
            provision_advance_seconds=6.0,
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.failure_code is Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert controller.ready_calls == 0
        assert controller.termination_calls == 1

    def test_wait_ready_timeout_is_failed_and_never_calls_adapter(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(
            clock,
            ready_result=TimeoutError(),
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.failure_code is Feat018LiveSmokeFailureCode.READY_TIMEOUT
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert controller.termination_calls == 1

    def test_provisioning_exception_is_failed_and_never_calls_adapter(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(
            clock,
            provision_result=RuntimeError("SECRET-provider-detail"),
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.failure_code is Feat018LiveSmokeFailureCode.PROVISION_FAILED
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert controller.termination_calls == 1
        assert "SECRET-provider-detail" not in str(result)

    @pytest.mark.parametrize("failure", ["not_ready", "missing_budget", "missing_result"])
    def test_every_pre_ready_failure_attempts_forced_termination_once_and_keeps_counts(
        self, failure: str
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        if failure == "not_ready":
            controller.ready_result = LightningReadyFacts(
                readiness=LightningSessionReadiness.NOT_READY,
                lifecycle=None,
            )
        elif failure == "missing_budget":
            controller.provision_result = LightningProvisionFacts(
                allocation_confirmed=True,
                gpu_minute_budget_start_monotonic=None,
                session_identity="provider-session",
                placement=controller.placement,
            )
        else:
            controller.provision_result = None
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert controller.termination_calls == 1

    @pytest.mark.parametrize(
        ("termination_result", "termination_advance_seconds"),
        [
            (
                LightningTerminationFacts(
                    termination_verified=False,
                    cleanup_status=CleanupStatus.SUCCEEDED,
                    session_identity="provider-session",
                    session_cleanup_verified=False,
                ),
                0.0,
            ),
            (
                LightningTerminationFacts(
                    termination_verified=True,
                    cleanup_status=CleanupStatus.SUCCEEDED,
                    session_identity="provider-session",
                    session_cleanup_verified=True,
                ),
                3.0,
            ),
        ],
        ids=("verification-failure", "termination-timeout"),
    )
    def test_termination_failure_or_timeout_is_cleanup_failed(
        self,
        termination_result: LightningTerminationFacts,
        termination_advance_seconds: float,
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(
            clock,
            termination_result=termination_result,
            termination_advance_seconds=termination_advance_seconds,
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.adapter_call_count == 1
        assert controller.termination_calls == 1
        assert result.failure_code in {
            Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED,
            Feat018LiveSmokeFailureCode.SESSION_TERMINATION_TIMEOUT,
            Feat018LiveSmokeFailureCode.SESSION_TERMINATION_CANCELLATION_FAILED,
        }

    def test_session_ttl_starts_only_at_confirmed_session_ready(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(
            clock,
            provision_advance_seconds=1.0,
            ready_advance_seconds=2.0,
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.session_ready is True
        assert result.ready_at_monotonic == 3.0
        assert result.session_ttl_start_monotonic == result.ready_at_monotonic
        assert result.session_ttl_deadline_monotonic == 33.0
        assert result.session_ttl_start_monotonic != result.provision_start_monotonic

        clock = FakeClock()
        not_ready_controller = FakeLightningSessionController(
            clock,
            ready_result=LightningReadyFacts(
                readiness=LightningSessionReadiness.NOT_READY,
                lifecycle=None,
            ),
        )
        not_ready_result = self._run(not_ready_controller, FakeBoundedAdapterCall(clock))
        assert not_ready_result.session_ready is False
        assert not_ready_result.session_ttl_start_monotonic is None
        assert not_ready_result.session_ttl_deadline_monotonic is None

    def test_total_adapter_cap_starts_immediately_before_adapter_invocation(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(
            clock,
            provision_advance_seconds=2.0,
            ready_advance_seconds=2.0,
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert adapter.call_times == [4.0]
        assert result.adapter_start_monotonic == adapter.call_times[0]
        assert result.total_adapter_cap_deadline_monotonic == 14.0

    def test_cleanup_deadline_includes_session_termination(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(
            clock,
            termination_advance_seconds=2.1,
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.session_termination_deadline_monotonic == 2.0
        assert controller.termination_calls == 1
        assert controller.termination_operations[0].wait_calls == [2.0]

    def test_ready_session_uses_the_existing_bounded_adapter_call_shape_once(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        adapter = FakeBoundedAdapterCall(clock)
        config = _live_smoke_config()

        result = self._run(controller, adapter, config=config)

        assert result.adapter_result is adapter.result
        assert len(adapter.arguments) == 1
        assert adapter.arguments[0][4] is config.bounded_runner_config
        assert adapter.arguments[0][5] == "synthetic-session"
        assert result.adapter_call_count == 1

    @pytest.mark.parametrize(
        "field",
        [
            "session_provision_timeout_seconds",
            "session_ttl_seconds",
            "gpu_minute_cap",
            "session_termination_deadline_seconds",
        ],
    )
    def test_session_budget_fields_are_positive_integers(self, field: str) -> None:
        values: dict[str, object] = {field: 0}
        with pytest.raises(ValueError, match="positive finite integer"):
            _live_smoke_config(**values)


class TestLiveSmokeIndependentReviewBlockers:
    """Offline regression coverage for the independent-review blocker dispositions."""

    def _run(
        self,
        controller: FakeLightningSessionController,
        adapter: FakeBoundedAdapterCall | None,
        *,
        config: Feat018LiveSmokeConfig | None = None,
        preflight: FakeLightningPreflight | None | object = _UNSET_LIGHTNING_RESULT,
        finalizer: FakeLiveSmokeFinalizer | None | object = _UNSET_LIGHTNING_RESULT,
        lifecycle_boundary: LightningLifecycleBoundary | None = None,
    ) -> Feat018LiveSmokeResult:
        active_config = config or _live_smoke_config()
        controller.ttl_seconds = active_config.session_ttl_seconds
        active_preflight = (
            FakeLightningPreflight()
            if preflight is _UNSET_LIGHTNING_RESULT
            else cast(FakeLightningPreflight | None, preflight)
        )
        active_finalizer = (
            FakeLiveSmokeFinalizer()
            if finalizer is _UNSET_LIGHTNING_RESULT
            else cast(FakeLiveSmokeFinalizer | None, finalizer)
        )
        return run_live_smoke(
            _request("fixture.bin", "a" * 64),
            QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir")),
            _policy(),
            "fixture prompt",
            controller=controller,
            config=active_config,
            session_id="synthetic-session",
            preflight=active_preflight,
            finalizer=active_finalizer,
            adapter_call=adapter,
            lifecycle_boundary=lifecycle_boundary
            or FakeInlineLightningLifecycleBoundary(controller, controller.clock),
            clock=controller.clock,
        )

    @staticmethod
    def _all_preflight_facts(**overrides: object) -> LightningPreflightFacts:
        values: dict[str, object] = {
            "synthetic_session_id": "synthetic-session",
            "approval_identity_verified": True,
            "checkout_identity_verified": True,
            "d4_readiness_verified": True,
            "fixture_digest_verified": True,
            "prompt_hash_verified": True,
            "hardware_placement_verified": True,
            "policy_identity_verified": True,
            "runtime_inventory_verified": True,
        }
        values.update(overrides)
        return LightningPreflightFacts(**values)  # type: ignore[arg-type]

    def test_success_requires_typed_preflight_finalization_and_cancellable_handles(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        preflight = FakeLightningPreflight()
        finalizer = FakeLiveSmokeFinalizer()
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(
            controller,
            adapter,
            preflight=preflight,
            finalizer=finalizer,
        )

        assert result.is_success is True
        assert result.preflight_verified is True
        assert result.finalization_verified is True
        assert preflight.calls == ["synthetic-session"]
        assert len(finalizer.calls) == 1
        assert controller.provision_operations[0].wait_calls == [5.0]
        assert controller.ready_operations[0].wait_calls == [5.0]
        assert controller.termination_operations[0].wait_calls == [2.0]
        assert controller.termination_calls == 1

    @pytest.mark.parametrize(
        ("preflight", "expected_code"),
        [
            (None, Feat018LiveSmokeFailureCode.PREFLIGHT_MISSING),
            (
                FakeLightningPreflight(
                    result=RuntimeError("SECRET-preflight-provider-detail")
                ),
                Feat018LiveSmokeFailureCode.PREFLIGHT_FAILED,
            ),
            (
                FakeLightningPreflight(
                    result=_all_preflight_facts(d4_readiness_verified=False)
                ),
                Feat018LiveSmokeFailureCode.PREFLIGHT_NOT_AUTHORIZED,
            ),
        ],
        ids=("missing", "exception", "false-gate"),
    )
    def test_preflight_failure_is_before_provision_and_adapter(
        self,
        preflight: FakeLightningPreflight | None,
        expected_code: Feat018LiveSmokeFailureCode,
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter, preflight=preflight)

        assert result.failure_code is expected_code
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert controller.provision_calls == 0
        assert controller.termination_calls == 0

    def test_missing_adapter_seam_never_uses_a_real_default(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)

        result = self._run(controller, None)

        assert result.failure_code is Feat018LiveSmokeFailureCode.ADAPTER_CALL_MISSING
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert controller.provision_calls == 0
        assert controller.termination_calls == 0

    def test_missing_finalizer_is_rejected_before_provision(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter, finalizer=None)

        assert result.failure_code is Feat018LiveSmokeFailureCode.FINALIZATION_MISSING
        assert result.adapter_call_count == 0
        assert adapter.call_times == []
        assert controller.provision_calls == 0

    @pytest.mark.parametrize(
        "provision_result",
        [None, {"allocation_confirmed": True}, object()],
        ids=("missing", "mapping", "opaque-object"),
    )
    def test_untyped_or_missing_provision_facts_fail_closed_before_adapter(
        self, provision_result: object
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock, provision_result=provision_result)
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert controller.ready_calls == 0
        assert controller.termination_calls == 1

    def test_placement_mismatch_is_rejected_before_readiness_and_adapter(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        controller.placement = LightningPlacementFacts(
            gpu_sku="NVIDIA_A10",
            device_index=0,
            device_count=1,
            vram_mib=24576,
            cuda_available=True,
            bf16_supported=True,
            single_device_visible=True,
            model_device_index=0,
            input_device_index=0,
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.failure_code is Feat018LiveSmokeFailureCode.PLACEMENT_MISMATCH
        assert result.adapter_call_count == 0
        assert controller.ready_calls == 0
        assert adapter.call_times == []

    @pytest.mark.parametrize(
        ("ready_result", "expected_code"),
        [
            (object(), Feat018LiveSmokeFailureCode.READY_FACTS_MISSING),
            (
                LightningReadyFacts(
                    readiness=LightningSessionReadiness.SESSION_READY,
                    lifecycle=LightningSessionLifecycleFacts(
                        session_identity="other-session",
                        session_ready_at_monotonic=0.0,
                        session_ttl_start_monotonic=0.0,
                        session_ttl_deadline_monotonic=30.0,
                    ),
                ),
                Feat018LiveSmokeFailureCode.SESSION_IDENTITY_MISMATCH,
            ),
            (
                LightningReadyFacts(
                    readiness=LightningSessionReadiness.SESSION_READY,
                    lifecycle=LightningSessionLifecycleFacts(
                        session_identity="provider-session",
                        session_ready_at_monotonic=0.0,
                        session_ttl_start_monotonic=0.0,
                        session_ttl_deadline_monotonic=31.0,
                    ),
                ),
                Feat018LiveSmokeFailureCode.LIFECYCLE_FACTS_INVALID,
            ),
        ],
        ids=("missing-lifecycle-facts", "identity-mismatch", "ttl-contradiction"),
    )
    def test_readiness_lifecycle_facts_are_typed_and_bound(
        self,
        ready_result: object,
        expected_code: Feat018LiveSmokeFailureCode,
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock, ready_result=ready_result)
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.failure_code is expected_code
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []

    def test_typed_fact_invariants_reject_missing_placement_lifecycle_and_cleanup_proof(
        self,
    ) -> None:
        with pytest.raises(ValueError, match="placement facts are required"):
            LightningProvisionFacts(
                allocation_confirmed=True,
                gpu_minute_budget_start_monotonic=0.0,
                session_identity="provider-session",
                placement=cast(LightningPlacementFacts, None),
            )
        with pytest.raises(ValueError, match="SESSION_READY requires lifecycle facts"):
            LightningReadyFacts(
                readiness=LightningSessionReadiness.SESSION_READY,
                lifecycle=None,
            )
        with pytest.raises(ValueError, match="cleanup_status must be a CleanupStatus"):
            LightningTerminationFacts(
                termination_verified=True,
                cleanup_status=cast(CleanupStatus, "SUCCEEDED"),
                session_identity="provider-session",
                session_cleanup_verified=True,
            )

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("device_count", 0),
            ("vram_mib", 0),
            ("model_device_index", 1),
        ],
    )
    def test_placement_device_facts_reject_invalid_values(self, field: str, value: int) -> None:
        values: dict[str, object] = {
            "gpu_sku": "NVIDIA_L4",
            "device_index": 0,
            "device_count": 1,
            "vram_mib": 24576,
            "cuda_available": True,
            "bf16_supported": True,
            "single_device_visible": True,
            "model_device_index": 0,
            "input_device_index": 0,
        }
        values[field] = value
        with pytest.raises(ValueError):
            LightningPlacementFacts(**values)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("operation", "expected_code", "cancel_result"),
        [
            ("provision", Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT, None),
            ("ready", Feat018LiveSmokeFailureCode.READY_TIMEOUT, None),
        ],
        ids=("provision-wait-hang", "readiness-wait-hang"),
    )
    def test_provision_and_readiness_waits_are_bounded_and_cancelled(
        self,
        operation: str,
        expected_code: Feat018LiveSmokeFailureCode,
        cancel_result: object,
    ) -> None:
        del cancel_result
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        if operation == "provision":
            controller.provision_result = TimeoutError()
            controller.provision_advance_seconds = 5.0
        else:
            controller.ready_result = TimeoutError()
            controller.ready_advance_seconds = 5.0
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.failure_code is expected_code
        assert result.adapter_call_count == 0
        assert adapter.call_times == []
        assert controller.termination_calls == 1
        if operation == "provision":
            assert controller.provision_operations[0].wait_calls == [5.0]
            assert controller.provision_operations[0].cancel_calls == [2.0]
        else:
            assert controller.ready_operations[0].wait_calls == [5.0]
            assert controller.ready_operations[0].cancel_calls == [2.0]

    def test_active_operation_cancellation_failure_overrides_cleanup(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(
            clock,
            provision_result=TimeoutError(),
            provision_advance_seconds=5.0,
            provision_cancel_result=LightningCancellationFacts(
                cancellation_verified=False
            ),
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.failure_code is Feat018LiveSmokeFailureCode.OPERATION_CANCELLATION_FAILED
        assert controller.termination_calls == 1

    @pytest.mark.parametrize(
        ("termination_result", "termination_advance_seconds", "cancel_result", "expected"),
        [
            (
                TimeoutError(),
                0.0,
                LightningCancellationFacts(
                    cancellation_verified=True,
                    termination_facts=LightningTerminationFacts(
                        termination_verified=True,
                        cleanup_status=CleanupStatus.SUCCEEDED,
                        session_identity="provider-session",
                        session_cleanup_verified=True,
                    ),
                ),
                Feat018LiveSmokeFailureCode.SESSION_TERMINATION_TIMEOUT,
            ),
            (
                TimeoutError(),
                0.0,
                LightningCancellationFacts(cancellation_verified=False),
                Feat018LiveSmokeFailureCode.SESSION_TERMINATION_CANCELLATION_FAILED,
            ),
            (
                TimeoutError(),
                2.0,
                LightningCancellationFacts(cancellation_verified=True),
                Feat018LiveSmokeFailureCode.SESSION_TERMINATION_CANCELLATION_FAILED,
            ),
        ],
        ids=("timeout-cancelled", "cancellation-proof-failed", "deadline-exhausted"),
    )
    def test_termination_wait_and_cancellation_are_bounded(
        self,
        termination_result: object,
        termination_advance_seconds: float,
        cancel_result: object,
        expected: Feat018LiveSmokeFailureCode,
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(
            clock,
            termination_result=termination_result,
            termination_advance_seconds=termination_advance_seconds,
            termination_cancel_result=cancel_result,
        )
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.failure_code is expected
        assert controller.termination_calls == 1
        if termination_advance_seconds == 0.0:
            assert controller.termination_operations[0].cancel_calls == [2.0]
        else:
            assert controller.termination_operations[0].cancel_calls == []

    def test_bare_true_termination_is_not_cleanup_proof(self) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock, termination_result=True)
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter)

        assert result.adapter_call_count == 1
        assert result.attempt_count == 1
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.failure_code is Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED
        assert controller.termination_calls == 1

    @pytest.mark.parametrize(
        ("cap_kind", "expected_code", "session_ttl_seconds"),
        [
            ("ttl", Feat018LiveSmokeFailureCode.SESSION_TTL_EXCEEDED, 30),
            ("gpu", Feat018LiveSmokeFailureCode.GPU_MINUTE_BUDGET_EXCEEDED, 120),
        ],
        ids=("ttl-boundary", "gpu-minute-boundary"),
    )
    def test_caps_are_rechecked_at_the_exact_pre_adapter_boundary(
        self,
        cap_kind: str,
        expected_code: Feat018LiveSmokeFailureCode,
        session_ttl_seconds: int,
    ) -> None:
        clock = BoundaryClock()
        controller = FakeLightningSessionController(clock)

        def ready_result() -> LightningReadyFacts:
            ready_at = clock.raw_now
            boundary = ready_at + (30.0 if cap_kind == "ttl" else 60.0)
            clock.arm_jump_after_next_read(boundary)
            return LightningReadyFacts(
                readiness=LightningSessionReadiness.SESSION_READY,
                lifecycle=LightningSessionLifecycleFacts(
                    session_identity="provider-session",
                    session_ready_at_monotonic=ready_at,
                    session_ttl_start_monotonic=ready_at,
                    session_ttl_deadline_monotonic=ready_at + session_ttl_seconds,
                ),
            )

        controller.ready_result = ready_result
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(
            controller,
            adapter,
            config=_live_smoke_config(session_ttl_seconds=session_ttl_seconds),
        )

        assert result.failure_code is expected_code
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert controller.termination_calls == 1

    @pytest.mark.parametrize(
        "adapter_result",
        [
            SupervisorRunResult(
                final_state=ProgressState.TERMINAL,
                attempt_count=3,
                terminal_outcome="SUCCEEDED",
                cleanup_status=CleanupStatus.SUCCEEDED,
                effective_outcome=EffectiveOutcome.SUCCEEDED,
                raw_status="SUCCEEDED",
            ),
            SupervisorRunResult(
                final_state=ProgressState.FROZEN,
                attempt_count=1,
                terminal_outcome=None,
                cleanup_status=CleanupStatus.SUCCEEDED,
                effective_outcome=EffectiveOutcome.SUCCEEDED,
                raw_status=None,
            ),
        ],
        ids=("attempt-count-out-of-range", "contradictory-success"),
    )
    def test_malformed_supervisor_result_is_rejected_without_copying_attempt_count(
        self, adapter_result: SupervisorRunResult
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        adapter = FakeBoundedAdapterCall(clock, result=adapter_result)

        result = self._run(controller, adapter)

        assert result.failure_code is Feat018LiveSmokeFailureCode.ADAPTER_RESULT_INVALID
        assert result.adapter_call_count == 1
        assert result.attempt_count is None
        assert result.adapter_result is None
        assert result.effective_outcome is EffectiveOutcome.FAILED

    @pytest.mark.parametrize(
        "finalizer",
        [
            FakeLiveSmokeFinalizer(result=RuntimeError("SECRET-finalizer-detail")),
            FakeLiveSmokeFinalizer(
                result=LightningFinalizationFacts(
                    finalization_verified=False,
                    evidence_pair_verified=True,
                    incident_handling_verified=True,
                )
            ),
        ],
        ids=("exception", "unverified"),
    )
    def test_finalization_failure_cannot_report_success(
        self, finalizer: FakeLiveSmokeFinalizer
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        adapter = FakeBoundedAdapterCall(clock)

        result = self._run(controller, adapter, finalizer=finalizer)

        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.failure_code is Feat018LiveSmokeFailureCode.FINALIZATION_FAILED
        assert result.finalization_verified is False
        assert result.adapter_call_count == 1
        assert len(finalizer.calls) == 1

    @pytest.mark.parametrize(
        "failed_operations",
        [("provision",), ("wait_ready",), ("terminate",), ("provision", "terminate")],
    )
    @pytest.mark.parametrize("finalizer_fails", [False, True])
    def test_lifecycle_cleanup_owners_survive_coordinator_finalization(
        self, failed_operations: tuple[str, ...], finalizer_fails: bool
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        adapter = FakeBoundedAdapterCall(clock)
        owned_failures = {
            operation: Feat018CleanupFailedError(
                "unreleased lifecycle process",
                owned_process=FakeProcessHandle(die_on_kill=False),
            )
            for operation in failed_operations
        }

        class _FailingBoundary(FakeInlineLightningLifecycleBoundary):
            def invoke(
                self,
                operation: LightningLifecycleOperationName,
                *,
                deadline: float,
                cancellation_deadline: float,
                session_identity: str | None = None,
            ) -> object:
                if operation in owned_failures:
                    raise Feat018LifecycleOperationError(
                        Feat018LiveSmokeFailureCode.LIFECYCLE_CLEANUP_FAILED,
                        cleanup_failure=owned_failures[operation],
                    )
                return super().invoke(
                    operation,
                    deadline=deadline,
                    cancellation_deadline=cancellation_deadline,
                    session_identity=session_identity,
                )

        finalizer = FakeLiveSmokeFinalizer()
        if finalizer_fails:
            finalizer.result = RuntimeError("finalizer failed")

        result = self._run(
            controller,
            adapter,
            finalizer=finalizer,
            lifecycle_boundary=_FailingBoundary(controller, clock),
        )

        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.finalization_verified is not finalizer_fails
        assert len(finalizer.calls) == 1
        assert result is not finalizer.calls[0]
        expected_failures = tuple(owned_failures.values())
        assert result.cleanup_failures == expected_failures
        assert finalizer.calls[0].cleanup_failures == expected_failures
        for retained, original in zip(result.cleanup_failures, expected_failures, strict=True):
            assert retained is original
            assert retained.owned_process is original.owned_process
            assert retained.owned_process is not None
            assert retained.owned_process.is_alive()
        assert "unreleased lifecycle process" not in repr(result)

    @pytest.mark.parametrize("finalizer_fails", [False, True])
    @pytest.mark.parametrize("failure_source", ["failed_result", "success_looking_result", "exception"])
    def test_adapter_cleanup_owner_survives_coordinator_finalization(
        self, finalizer_fails: bool, failure_source: str
    ) -> None:
        clock = FakeClock()
        controller = FakeLightningSessionController(clock)
        process = FakeProcessHandle(die_on_kill=False)
        cleanup_failure = Feat018CleanupFailedError(
            "unreleased adapter process", owned_process=process
        )
        adapter = FakeBoundedAdapterCall(
            clock,
            result=SupervisorRunResult(
                final_state=ProgressState.FROZEN,
                attempt_count=1,
                terminal_outcome=None,
                cleanup_status=CleanupStatus.CLEANUP_FAILED,
                effective_outcome=EffectiveOutcome.CLEANUP_FAILED,
                cleanup_failure=cleanup_failure,
            ),
        )
        if failure_source == "success_looking_result":
            adapter.result = replace(
                _successful_supervisor_result(), cleanup_failure=cleanup_failure
            )
        elif failure_source == "exception":
            class _CleanupRaisingAdapter(FakeBoundedAdapterCall):
                def __call__(
                    self,
                    request: VisionUnderstandingRequestV2,
                    runtime_config: QwenVisionRuntimeConfig,
                    content_policy: object,
                    prompt: str,
                    config: Feat018BoundedRunnerConfig,
                    *,
                    session_id: str | None = None,
                ) -> SupervisorRunResult:
                    super().__call__(
                        request, runtime_config, content_policy, prompt, config,
                        session_id=session_id,
                    )
                    raise cleanup_failure

            adapter = _CleanupRaisingAdapter(clock)
        finalizer = FakeLiveSmokeFinalizer()
        if finalizer_fails:
            finalizer.result = RuntimeError("finalizer failed")

        result = self._run(controller, adapter, finalizer=finalizer)

        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.finalization_verified is not finalizer_fails
        assert result.cleanup_failures == (cleanup_failure,)
        assert result.cleanup_failures[0] is cleanup_failure
        assert result.cleanup_failures[0].owned_process is process
        assert finalizer.calls[0].cleanup_failures[0] is cleanup_failure
        assert controller.termination_calls == 1
        assert "unreleased adapter process" not in repr(result)
        assert not replace(
            result,
            effective_outcome=EffectiveOutcome.SUCCEEDED,
            cleanup_status=CleanupStatus.SUCCEEDED,
        ).is_success


# ------------------------------------------------------------------------------------------
# B3 -- actual host preemption of the lifecycle boundary
# ------------------------------------------------------------------------------------------


class TestLiveSmokeHostPreemption:
    """Use real synthetic child workers to prove the host can regain control."""

    def test_provision_method_that_never_returns_is_preempted_before_adapter(self) -> None:
        events = _process_lifecycle_events()
        controller = _ProcessLightningSessionController(events, provision_mode="hang")
        started = time.monotonic()

        result, adapter = _run_process_boundary_smoke(controller)

        elapsed = time.monotonic() - started
        assert elapsed < 10.0
        assert result.failure_code is Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT
        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.cleanup_status is CleanupStatus.SUCCEEDED
        assert result.session_ready is False
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert events.provision_called.is_set()
        assert events.terminate_called.is_set()
        assert events.termination_count.value == 1

    def test_readiness_method_that_never_returns_is_preempted_before_adapter(self) -> None:
        events = _process_lifecycle_events()
        controller = _ProcessLightningSessionController(events, ready_mode="hang")
        started = time.monotonic()

        result, adapter = _run_process_boundary_smoke(controller)

        elapsed = time.monotonic() - started
        assert elapsed < 10.0
        assert result.failure_code is Feat018LiveSmokeFailureCode.READY_TIMEOUT
        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.cleanup_status is CleanupStatus.SUCCEEDED
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert events.provision_called.is_set()
        assert events.ready_called.is_set()
        assert events.terminate_called.is_set()
        assert events.termination_count.value == 1

    @pytest.mark.parametrize(
        ("operation", "expected_code"),
        [
            ("provision", Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT),
            ("wait_ready", Feat018LiveSmokeFailureCode.READY_TIMEOUT),
        ],
        ids=("provision-wait", "readiness-wait"),
    )
    def test_operation_wait_that_never_returns_is_host_preempted(
        self,
        operation: str,
        expected_code: Feat018LiveSmokeFailureCode,
    ) -> None:
        events = _process_lifecycle_events()
        controller = _ProcessLightningSessionController(
            events,
            provision_wait_mode="hang" if operation == "provision" else "success",
            ready_wait_mode="hang" if operation == "wait_ready" else "success",
        )
        started = time.monotonic()

        result, adapter = _run_process_boundary_smoke(controller)

        elapsed = time.monotonic() - started
        assert elapsed < 10.0
        assert result.failure_code is expected_code
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert events.wait_started.is_set()
        assert events.terminate_called.is_set()
        assert events.termination_count.value == 1

    def test_operation_cancel_that_never_returns_is_host_preempted_and_fails_closed(
        self,
    ) -> None:
        events = _process_lifecycle_events()
        controller = _ProcessLightningSessionController(
            events,
            provision_wait_mode="timeout",
            provision_cancel_mode="hang",
        )
        started = time.monotonic()

        result, adapter = _run_process_boundary_smoke(controller)

        elapsed = time.monotonic() - started
        assert elapsed < 10.0
        assert result.failure_code is Feat018LiveSmokeFailureCode.OPERATION_CANCELLATION_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert events.wait_started.is_set()
        assert events.cancel_started.is_set()
        assert events.terminate_called.is_set()
        assert events.termination_count.value == 1

    def test_worker_death_before_reply_is_typed_and_does_not_call_adapter(self) -> None:
        events = _process_lifecycle_events()
        controller = _ProcessLightningSessionController(events, provision_mode="die")

        result, adapter = _run_process_boundary_smoke(controller)

        assert result.failure_code is Feat018LiveSmokeFailureCode.LIFECYCLE_WORKER_DIED
        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.cleanup_status is CleanupStatus.SUCCEEDED
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert events.provision_called.is_set()
        assert events.terminate_called.is_set()
        assert events.termination_count.value == 1

    def test_late_operation_result_is_rejected_at_the_host_deadline(self) -> None:
        events = _process_lifecycle_events()
        controller = _ProcessLightningSessionController(
            events, provision_wait_delay_seconds=4.0
        )
        config = _process_live_smoke_config()
        started = time.monotonic()

        result, adapter = _run_process_boundary_smoke(controller, config=config)

        elapsed = time.monotonic() - started
        assert elapsed < 10.0
        assert result.failure_code is Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT
        assert result.adapter_call_count == 0
        assert result.attempt_count is None
        assert adapter.call_times == []
        assert events.terminate_called.is_set()
        assert events.termination_count.value == 1

    def test_termination_hang_is_cleanup_failed_and_descendant_is_removed(self) -> None:
        events = _process_lifecycle_events()
        controller = _ProcessLightningSessionController(
            events, termination_mode="hang_descendant"
        )
        started = time.monotonic()

        result, adapter = _run_process_boundary_smoke(controller)

        elapsed = time.monotonic() - started
        assert elapsed < 10.0
        assert result.failure_code is Feat018LiveSmokeFailureCode.SESSION_TERMINATION_TIMEOUT
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.adapter_call_count == 1
        assert result.attempt_count == 1
        assert adapter.call_times
        assert events.terminate_called.is_set()
        assert events.termination_count.value == 1
        assert events.descendant_started.is_set()
        descendant_pid = int(events.descendant_pid.value)
        deadline = time.monotonic() + 3.0
        while _synthetic_pid_is_alive(descendant_pid) and time.monotonic() < deadline:
            time.sleep(0.02)
        assert not _synthetic_pid_is_alive(descendant_pid)
        assert not events.termination_finished.is_set()

    def test_normal_success_through_process_boundary_preserves_counts_and_facts(self) -> None:
        events = _process_lifecycle_events()
        controller = _ProcessLightningSessionController(events)

        result, adapter = _run_process_boundary_smoke(controller)

        assert result.is_success is True
        assert result.session_ready is True
        assert result.adapter_call_count == 1
        assert result.attempt_count == 1
        assert result.session_identity == "provider-session"
        assert result.placement is not None
        assert adapter.call_times
        assert events.provision_called.is_set()
        assert events.ready_called.is_set()
        assert events.terminate_called.is_set()
        assert events.termination_count.value == 1


# ------------------------------------------------------------------------------------------
# B3-1 -- containment cleanup fail-closed, and cleanup failure overriding a prior success
# ------------------------------------------------------------------------------------------


class TestLightningLifecycleProcessBoundaryCleanupFailure:
    """A containment that can never be proven empty must fail closed (never report success
    while a member remains), and that failure must override an otherwise successfully returned
    lifecycle result (independent-review finding B3-1)."""

    def test_launcher_cleanup_failure_survives_empty_containment(self) -> None:
        clock = FakeClock()
        containment = FakeContainmentBackend()
        cleanup_failure = Feat018CleanupFailedError("launch rollback failed")
        boundary = Feat018LightningLifecycleProcessBoundary(
            controller=FakeLightningSessionController(clock=clock),
            max_envelope_bytes=1_000_000,
            containment_factory=lambda: containment,
            launcher=_RaisingLauncher(cleanup_failure),
            clock=clock,
            sleep=clock.advance,
        )

        with pytest.raises(Feat018LifecycleOperationError) as exc_info:
            boundary.invoke("provision", deadline=5.0, cancellation_deadline=5.0)

        assert exc_info.value.failure_code is Feat018LiveSmokeFailureCode.LIFECYCLE_CLEANUP_FAILED
        assert exc_info.value.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert exc_info.value.cleanup_failure is cleanup_failure
        assert containment.is_empty() is True
        assert containment.close_calls == 1

    def test_cleanup_resources_fails_closed_when_containment_never_proves_empty(self) -> None:
        clock = FakeClock()
        containment = FakeContainmentBackend(empty_after_terminate=False)
        boundary = Feat018LightningLifecycleProcessBoundary(
            controller=FakeLightningSessionController(clock=FakeClock()),
            max_envelope_bytes=1_000_000,
            containment_factory=lambda: containment,
            cleanup_deadline_seconds=0.05,
            confirmation_retry_interval_seconds=0.01,
            clock=clock,
            sleep=lambda seconds: clock.advance(seconds),
        )

        cleanup_failed = boundary._cleanup_resources(None, None, containment)

        assert isinstance(cleanup_failed, Feat018CleanupFailedError)
        assert containment.terminate_calls == 1  # exactly-once cleanup, even on failure
        assert containment.close_calls == 0  # retain the only query/control handle
        assert cleanup_failed.owned_containments == (containment,)

    def test_cleanup_failure_overrides_a_successfully_returned_lifecycle_result(self) -> None:
        """The lifecycle call itself genuinely succeeds (a real worker replies with a valid
        result), but the containment can never be proven empty -- the final outcome must still
        be a typed cleanup failure, never the successful result."""

        events = _process_lifecycle_events()
        controller = _ProcessLightningSessionController(events)
        containment = FakeContainmentBackend(confirm_result=True, empty_after_terminate=False)
        boundary = Feat018LightningLifecycleProcessBoundary(
            controller=controller,
            max_envelope_bytes=1_000_000,
            containment_factory=lambda: containment,
            cleanup_deadline_seconds=0.2,
            containment_setup_timeout_seconds=5.0,
            confirmation_retry_interval_seconds=0.01,
        )
        started = time.monotonic()
        deadline = started + 10.0

        with pytest.raises(Feat018LifecycleOperationError) as exc_info:
            boundary.invoke("provision", deadline=deadline, cancellation_deadline=deadline)

        elapsed = time.monotonic() - started
        assert elapsed < 10.0
        assert exc_info.value.failure_code is Feat018LiveSmokeFailureCode.LIFECYCLE_CLEANUP_FAILED
        assert exc_info.value.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert events.provision_called.is_set()  # the underlying operation genuinely succeeded
        assert containment.terminate_calls == 1  # exactly-once cleanup
        assert containment.close_calls == 0
        assert exc_info.value.cleanup_failure.owned_containments == (containment,)


# ------------------------------------------------------------------------------------------
# B3-2 -- IPC lifecycle-frame parser negative coverage
# ------------------------------------------------------------------------------------------


@dataclass(slots=True)
class _LateArrivalConnection:
    """Wraps a :class:`FakeBoundedConnection`, jumping the shared clock forward the instant the
    scripted terminal frame is popped -- simulating a reply that only arrives well past the host
    deadline, regardless of its (here, deliberately malformed) content."""

    inner: FakeBoundedConnection
    clock: FakeClock
    jump_seconds: float
    jump_on_kind: str
    _jumped: bool = field(default=False, init=False)

    def send_frame(self, payload: Mapping[str, object]) -> None:
        self.inner.send_frame(payload)

    def recv_frame(self, timeout: float) -> dict[str, object] | None:
        frame = self.inner.recv_frame(timeout)
        if frame is not None and frame.get("kind") == self.jump_on_kind and not self._jumped:
            self._jumped = True
            self.clock.advance(self.jump_seconds)
        return frame

    def close(self) -> None:
        self.inner.close()


class TestLightningLifecycleProcessBoundaryMalformedFrames:
    """B3-2: every malformed lifecycle frame shape must fail closed with a typed protocol or
    lifecycle failure, never invoke the adapter (the process boundary has no adapter seam of its
    own to invoke, so this is proven by the boundary never returning a trusted, unvalidated
    fact), and never leave the worker or its containment membership behind."""

    def _boundary(
        self,
        connection: BoundedConnection,
        *,
        clock: FakeClock | None = None,
        process: FakeProcessHandle | None = None,
        containment: FakeContainmentBackend | None = None,
    ) -> tuple[Feat018LightningLifecycleProcessBoundary, FakeProcessHandle, FakeContainmentBackend]:
        clock = clock or FakeClock()
        process = process or FakeProcessHandle()
        containment = containment or FakeContainmentBackend()
        launcher = FakeProcessLauncher(handle=process, connection=connection)
        boundary = Feat018LightningLifecycleProcessBoundary(
            controller=FakeLightningSessionController(clock=FakeClock()),
            max_envelope_bytes=1_000_000,
            containment_factory=lambda: containment,
            cleanup_deadline_seconds=1.0,
            containment_setup_timeout_seconds=1.0,
            confirmation_retry_interval_seconds=0.01,
            launcher=launcher,
            clock=clock,
            sleep=lambda seconds: clock.advance(seconds),
        )
        return boundary, process, containment

    def _assert_failed_closed(
        self,
        boundary: Feat018LightningLifecycleProcessBoundary,
        process: FakeProcessHandle,
        containment: FakeContainmentBackend,
        *,
        expected_code: Feat018LiveSmokeFailureCode,
        deadline: float = 5.0,
    ) -> None:
        with pytest.raises(Feat018LifecycleOperationError) as exc_info:
            boundary.invoke("provision", deadline=deadline, cancellation_deadline=deadline)
        assert exc_info.value.failure_code is expected_code
        # No orphan worker: the direct worker handle was actually killed, not just abandoned.
        assert process.kill_calls == 1
        assert process.is_alive() is False
        assert containment.terminate_calls == 1
        assert containment.close_calls == 1

    def test_missing_required_key_on_result_frame_fails_closed(self) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "LIFECYCLE_CALL_STARTED"})
        connection.push({"kind": "LIFECYCLE_WAIT_STARTED"})
        connection.push({"kind": "LIFECYCLE_OPERATION_RESULT"})  # missing required "fact"
        boundary, process, containment = self._boundary(connection)

        self._assert_failed_closed(
            boundary,
            process,
            containment,
            expected_code=Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED,
        )

    def test_extra_unknown_key_on_started_frame_fails_closed(self) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "LIFECYCLE_CALL_STARTED", "unexpected": "value"})
        boundary, process, containment = self._boundary(connection)

        self._assert_failed_closed(
            boundary,
            process,
            containment,
            expected_code=Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED,
        )

    def test_wrong_field_type_in_result_fact_fails_closed(self) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "LIFECYCLE_CALL_STARTED"})
        connection.push({"kind": "LIFECYCLE_WAIT_STARTED"})
        connection.push(
            {"kind": "LIFECYCLE_OPERATION_RESULT", "fact": "not-a-mapping-at-all"}
        )
        boundary, process, containment = self._boundary(connection)

        self._assert_failed_closed(
            boundary,
            process,
            containment,
            expected_code=Feat018LiveSmokeFailureCode.LIFECYCLE_RESULT_INVALID,
        )

    def test_invalid_enum_value_in_result_fact_fails_closed(self) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "LIFECYCLE_CALL_STARTED"})
        connection.push({"kind": "LIFECYCLE_WAIT_STARTED"})
        connection.push(
            {
                "kind": "LIFECYCLE_OPERATION_RESULT",
                "fact": {
                    "fact_type": "ready",
                    "readiness": "NOT_A_REAL_READINESS_STATE",
                    "lifecycle": None,
                },
            }
        )
        boundary, process, containment = self._boundary(connection)

        self._assert_failed_closed(
            boundary,
            process,
            containment,
            expected_code=Feat018LiveSmokeFailureCode.LIFECYCLE_RESULT_INVALID,
        )

    def test_oversized_frame_fails_closed(self) -> None:
        connection = FakeBoundedConnection(raise_on_recv=Feat018FrameTooLargeError("too big"))
        boundary, process, containment = self._boundary(connection)

        self._assert_failed_closed(
            boundary,
            process,
            containment,
            expected_code=Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED,
        )

    def test_truncated_or_malformed_json_frame_fails_closed(self) -> None:
        connection = FakeBoundedConnection(
            raise_on_recv=Feat018ProtocolViolationError(
                "malformed envelope: not valid UTF-8 JSON"
            )
        )
        boundary, process, containment = self._boundary(connection)

        self._assert_failed_closed(
            boundary,
            process,
            containment,
            expected_code=Feat018LiveSmokeFailureCode.LIFECYCLE_PROTOCOL_FAILED,
        )

    def test_late_malformed_reply_after_deadline_is_rejected_as_timeout_not_content(self) -> None:
        clock = FakeClock()
        inner = FakeBoundedConnection()
        inner.push({"kind": "LIFECYCLE_CALL_STARTED"})
        inner.push({"kind": "LIFECYCLE_WAIT_STARTED"})
        # This frame is itself malformed (an unexpected extra key); the point is that lateness
        # alone must reject it before its content is ever inspected.
        inner.push(
            {
                "kind": "LIFECYCLE_OPERATION_RESULT",
                "fact": {"fact_type": "unknown"},
                "unexpected": "value",
            }
        )
        connection = _LateArrivalConnection(
            inner=inner,
            clock=clock,
            jump_seconds=100.0,
            jump_on_kind="LIFECYCLE_OPERATION_RESULT",
        )
        boundary, process, containment = self._boundary(connection, clock=clock)

        with pytest.raises(Feat018LifecycleOperationError) as exc_info:
            boundary.invoke("provision", deadline=1.0, cancellation_deadline=1.0)

        assert exc_info.value.failure_code is Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT
        assert process.kill_calls == 1
        assert process.is_alive() is False
        assert containment.terminate_calls == 1


# ------------------------------------------------------------------------------------------
# B3-3 -- the cooperative-wait helpers are a documented, non-live test seam only
# ------------------------------------------------------------------------------------------


class TestCooperativeWaitHelpersAreNonLiveOnly:
    """B3-3: ``_wait_for_lightning_operation``/``_cancel_lightning_operation``/
    ``_cancel_termination_operation`` reimplement a cooperative, trust-the-timeout-parameter wait
    -- exactly what the real process boundary above was built to replace. They are retained only
    because ``FakeInlineLightningLifecycleBoundary`` needs a fast, deterministic double for the
    pre-existing fake-clock coordinator-logic regression suite (deadline budgeting, TTL/GPU-minute
    caps, placement checks). This is a static proof, not just a behavioral one, that the live
    coordinator's default path never reaches them and that there is exactly one boundary
    construction path in ``run_live_smoke`` -- never two ambiguous timeout implementations."""

    def test_run_live_smoke_default_boundary_never_uses_the_cooperative_helpers(self) -> None:
        source = inspect.getsource(run_live_smoke)

        assert "Feat018LightningLifecycleProcessBoundary(" in source
        for cooperative_helper in (
            "_wait_for_lightning_operation",
            "_cancel_lightning_operation",
            "_cancel_termination_operation",
        ):
            assert cooperative_helper not in source

    def test_cooperative_helpers_only_caller_is_the_non_live_inline_test_double(self) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as module

        module_source = inspect.getsource(module)
        test_double_source = inspect.getsource(FakeInlineLightningLifecycleBoundary)

        for cooperative_helper in (
            "_wait_for_lightning_operation",
            "_cancel_lightning_operation",
            "_cancel_termination_operation",
        ):
            # Defined exactly once in the production module -- its own definition line, with no
            # in-module caller -- so the only caller anywhere is the non-live test double below.
            assert module_source.count(cooperative_helper) == 1
            assert cooperative_helper in test_double_source


# ------------------------------------------------------------------------------------------
# F3 -- the concrete, gated adapter-worker entry point
# ------------------------------------------------------------------------------------------


class TestAdapterWorkerEntryGate:
    """F3: ``adapter_worker_entry`` never constructs anything before a valid release."""

    @pytest.fixture(autouse=True)
    def _fake_capture(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as module

        monkeypatch.setattr(module, '_default_d9_capture_factory', _fake_d9_capture_factory)

    def _args(
        self, artifact_ref: str = "fixture.bin", digest: str = "a" * 64
    ) -> tuple[
        VisionUnderstandingRequestV2,
        QwenVisionRuntimeConfig,
        LexicalRegressionContentPolicy,
        str,
        Feat018BoundedRunnerConfig,
    ]:
        return (
            _request(artifact_ref, digest),
            QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir")),
            _policy(),
            "fixture prompt",
            _config(total_adapter_cap_seconds=300.0, containment_setup_timeout_seconds=1.0),
        )

    @pytest.fixture()
    def image(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
        from hashlib import sha256

        image_path = tmp_path / "fixture.bin"
        image_path.write_bytes(b"feat018-fixture-bytes")
        monkeypatch.chdir(tmp_path)
        return image_path.name, sha256(image_path.read_bytes()).hexdigest()

    def test_self_contain_runs_before_anything_else(self) -> None:
        calls: list[str] = []
        connection = FakeBoundedConnection()  # never releases

        def self_contain() -> None:
            calls.append("self_contain")

        request, runtime_config, policy, prompt, config = self._args()
        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=_launcher(),
            self_contain=self_contain,
            clock=FakeClock(),
        )
        assert calls == ["self_contain"]

    def test_capture_is_installed_before_self_containment_and_first_write(self) -> None:
        events: list[str] = []
        request, runtime_config, policy, prompt, config = self._args()

        def capture_factory(
            process_role: D9ProcessRole,
            attempt_number: int | None,
            stdout_max_bytes: int,
            stderr_max_bytes: int,
            on_terminal_failure: Callable[[D9StreamFailureCode], None] | None,
        ) -> FakeD9Capture:
            del on_terminal_failure
            events.append('capture')
            return _fake_d9_capture_factory(
                process_role,
                attempt_number,
                stdout_max_bytes,
                stderr_max_bytes,
                None,
            )

        def self_contain() -> None:
            events.append('self_contain')

        adapter_worker_entry(
            FakeBoundedConnection(),
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=_launcher(),
            self_contain=self_contain,
            clock=FakeClock(),
            capture_factory=capture_factory,
        )
        assert events == ['capture', 'self_contain']

    def test_missing_release_frame_prevents_all_construction(self) -> None:
        connection = FakeBoundedConnection()  # empty inbox, no clock bound -> returns None
        generation_launcher = _launcher()
        request, runtime_config, policy, prompt, config = self._args()
        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=FakeClock(),
        )
        assert _progress_frames(connection.sent) == []
        assert generation_launcher.launch_calls == []

    def test_malformed_release_frame_prevents_all_construction(self) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "NOT_CONTAINMENT_READY"})
        generation_launcher = _launcher()
        request, runtime_config, policy, prompt, config = self._args()
        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=FakeClock(),
        )
        assert _progress_frames(connection.sent) == []
        assert generation_launcher.launch_calls == []

    def test_release_frame_missing_duration_prevents_all_construction(self) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "CONTAINMENT_READY"})  # no remaining_seconds_at_spawn
        generation_launcher = _launcher()
        request, runtime_config, policy, prompt, config = self._args()
        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=FakeClock(),
        )
        assert _progress_frames(connection.sent) == []
        assert generation_launcher.launch_calls == []

    @pytest.mark.parametrize(
        "release",
        [
            {"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 0.0},
            {"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": -1.0},
            {"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": float("nan")},
            {"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": float("inf")},
            {"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": -float("inf")},
            {"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": True},
            {"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": "1.0"},
            {"kind": "CONTAINMENT_READY"},
            {
                "kind": "CONTAINMENT_READY",
                "remaining_seconds_at_spawn": 1.0,
                "secret": "SECRET-EARLY-RELEASE-FIELD",
            },
        ],
        ids=(
            "zero",
            "negative",
            "nan",
            "positive-infinity",
            "negative-infinity",
            "bool",
            "string",
            "missing",
            "extra-field",
        ),
    )
    def test_invalid_release_duration_fails_closed_before_any_construction(
        self, release: dict[str, object]
    ) -> None:
        connection = FakeBoundedConnection()
        connection.push(release)
        generation_launcher = _launcher()
        request, runtime_config, policy, prompt, config = self._args()

        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=FakeClock(),
        )

        assert _progress_frames(connection.sent) == []
        assert generation_launcher.launch_calls == []

    def test_release_completing_after_worker_gate_deadline_is_rejected(self) -> None:
        clock = FakeClock()

        class _LateReleaseConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                del timeout
                clock.advance(1.1)
                return self.inbox.popleft()

        connection = _LateReleaseConnection()
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 1.0})
        generation_launcher = _launcher()
        request, runtime_config, policy, prompt, config = self._args()

        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=clock,
        )

        assert _progress_frames(connection.sent) == []
        assert generation_launcher.launch_calls == []

    def test_oversized_release_frame_prevents_all_construction(self) -> None:
        connection = FakeBoundedConnection(
            raise_on_recv=Feat018ProtocolViolationError("declared length exceeds ceiling")
        )
        generation_launcher = _launcher()
        request, runtime_config, policy, prompt, config = self._args()
        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=FakeClock(),
        )
        assert _progress_frames(connection.sent) == []
        assert generation_launcher.launch_calls == []

    def test_valid_release_sends_adapter_started_and_proceeds(
        self, image: tuple[str, str]
    ) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 100.0})
        generation_launcher = _launcher()
        generation_launcher.connection.push({"kind": "success", "raw_output": _success_payload()})
        artifact_ref, digest = image
        request, runtime_config, policy, prompt, config = self._args(artifact_ref, digest)
        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=FakeClock(),
        )
        kinds = [frame['kind'] for frame in _progress_frames(connection.sent)]
        assert kinds[0] == "ADAPTER_STARTED"
        assert "GENERATION_ATTEMPT_STARTED" in kinds
        assert kinds[-1] == "TERMINAL"
        assert connection.sent[-1]["outcome"] == "SUCCEEDED"
        assert generation_launcher.launch_calls  # the generation child was actually launched

    @pytest.mark.parametrize(
        ("session_id", "frame", "outcome", "raw_status"),
        [
            ("synthetic-session", {"kind": "success", "raw_output": _success_payload()},
             "SUCCEEDED", "SUCCEEDED"),
            ("synthetic-session", {"kind": "device_unavailable"}, "FAILED", "FAILED"),
            ("", {"kind": "success", "raw_output": _success_payload()}, "FAILED", None),
            (None, {"kind": "success", "raw_output": _success_payload()}, "SUCCEEDED", None),
        ],
    )
    def test_real_worker_maps_before_terminal_without_transferring_content(
        self, image: tuple[str, str], session_id: str | None,
        frame: dict[str, object], outcome: str, raw_status: str | None,
    ) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 100.0})
        launcher = _launcher()
        launcher.connection.push(frame)
        adapter_worker_entry(
            connection, *self._args(*image), session_id,
            generation_launcher=launcher, self_contain=lambda: None, clock=FakeClock(),
        )
        terminal = connection.sent[-1]
        assert terminal["outcome"] == outcome
        assert terminal.get("raw_status") == raw_status
        assert set(terminal) == (
            {"seq", "kind", "outcome", "raw_status"} if raw_status is not None
            else {"seq", "kind", "outcome"}
        )
        assert "synthetic-session" not in json.dumps(connection.sent)

    @pytest.mark.parametrize("acceptance_time", [2.0, 10.0, 11.0])
    def test_mapper_claim_only_survives_accepted_terminal(self, acceptance_time: float) -> None:
        state = Feat018ProgressStateMachine(cap_deadline_monotonic=10.0)
        state.accept(ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED), acceptance_time=0.0)
        event = ProgressEvent(2, ProgressEventKind.TERMINAL,
                              outcome="SUCCEEDED", raw_status="SUCCEEDED")
        state.accept(event, acceptance_time=acceptance_time)
        assert state.raw_status == ("SUCCEEDED" if acceptance_time < 10.0 else None)

    @pytest.mark.parametrize("raw_status", ["SECRET", "FAILED"])
    def test_invalid_mapper_claim_is_rejected(self, raw_status: str) -> None:
        with pytest.raises(ValueError, match="raw_status"):
            ProgressEvent(1, ProgressEventKind.TERMINAL,
                          outcome="SUCCEEDED", raw_status=raw_status)

    def test_default_inner_launcher_is_constructed_after_containment_release(
        self, image: tuple[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as module

        events: list[str] = []

        class _ReleaseRecordingConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                frame = super().recv_frame(timeout)
                if frame is not None:
                    events.append("CONTAINMENT_READY_RECEIVED")
                return frame

        connection = _ReleaseRecordingConnection()
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 100.0})
        generation_launcher = _launcher()
        generation_launcher.connection.push({"kind": "success", "raw_output": _success_payload()})
        inner_launcher = generation_launcher
        artifact_ref, digest = image
        request, runtime_config, policy, prompt, config = self._args(artifact_ref, digest)

        class _RecordingInnerLauncher:
            def launch(
                self, entry: Callable[..., None], args: tuple[object, ...]
            ) -> tuple[ProcessHandle, FakeBoundedConnection]:
                events.append("GENERATION_CHILD_LAUNCHED")
                return inner_launcher.launch(entry, args)

        def construct_inner_launcher(*, max_envelope_bytes: int) -> _RecordingInnerLauncher:
            assert max_envelope_bytes == config.ipc_envelope_max_bytes
            events.append("INNER_LAUNCHER_CONSTRUCTED")
            return _RecordingInnerLauncher()

        monkeypatch.setattr(module, "MultiprocessingProcessLauncher", construct_inner_launcher)

        # A real nested OS spawn remains a separately approved live-smoke assertion; this test
        # proves only that the production worker constructs its default inner launcher after gate
        # release and before entering the generation-child seam.
        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            self_contain=lambda: None,
            clock=FakeClock(),
        )

        assert events == [
            "CONTAINMENT_READY_RECEIVED",
            "INNER_LAUNCHER_CONSTRUCTED",
            "GENERATION_CHILD_LAUNCHED",
        ]

    def test_terminal_failure_path_emits_correctly_sequenced_events(
        self, image: tuple[str, str]
    ) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 100.0})
        generation_launcher = _launcher()
        generation_launcher.connection.push({"kind": "device_unavailable"})
        artifact_ref, digest = image
        request, runtime_config, policy, prompt, config = self._args(artifact_ref, digest)
        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=FakeClock(),
        )
        kinds = [frame['kind'] for frame in _progress_frames(connection.sent)]
        assert kinds == ["ADAPTER_STARTED", "GENERATION_ATTEMPT_STARTED", "TERMINAL"]
        assert connection.sent[-1]["outcome"] == "FAILED"

    @pytest.mark.parametrize("failure_kind", ["launch", "process_close"])
    @pytest.mark.parametrize("earlier_stream_failure", [False, True])
    @pytest.mark.parametrize("marker_send_fails", [False, True])
    def test_inner_cleanup_failure_reaches_supervisor_through_the_real_adapter(
        self,
        image: tuple[str, str],
        failure_kind: str,
        earlier_stream_failure: bool,
        marker_send_fails: bool,
    ) -> None:
        clock = FakeClock()
        worker_connection = FakeBoundedConnection()
        if marker_send_fails:
            worker_connection.fail_send_kinds.add("GENERATION_CLEANUP_FAILED")
        worker_connection.push(
            {"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 100.0}
        )
        generation_launcher: _RaisingLauncher | FakeProcessLauncher
        if failure_kind == "launch":
            generation_launcher = _RaisingLauncher(
                Feat018CleanupFailedError("generation launch rollback failed")
            )
        else:
            generation_launcher = _launcher()
            generation_launcher.handle.raise_on_close = OSError("process close failed")
            for stream in D9StreamName:
                generation_launcher.connection.push(
                    _d9_observation_frame_for_test(D9ProcessRole.INNER_GENERATION_CHILD, 1, stream)
                )
            generation_launcher.connection.push(
                {"kind": "success", "raw_output": _success_payload()}
            )
        artifact_ref, digest = image
        request, runtime_config, policy, prompt, config = self._args(artifact_ref, digest)

        adapter_worker_entry(
            worker_connection,
            request,
            runtime_config,
            policy,
            prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=clock,
        )

        cleanup_frames = [
            frame for frame in worker_connection.sent
            if frame.get("kind") == "GENERATION_CLEANUP_FAILED"
        ]
        assert cleanup_frames == (
            [] if marker_send_fails else [{"kind": "GENERATION_CLEANUP_FAILED"}]
        )
        assert len([
            frame for frame in worker_connection.sent
            if frame.get("kind") == "GENERATION_ATTEMPT_STARTED"
        ]) == 1
        assert worker_connection.sent[-1]["outcome"] == "FAILED"
        assert worker_connection.sent[-1]["cleanup_failed"] is True

        outer_launcher = _launcher(clock)
        if earlier_stream_failure:
            outer_launcher.connection.push({
                "kind": "D9_STREAM_FAILURE",
                "failure_code": D9StreamFailureCode.STDOUT_CAPTURE_READ_FAILED.value,
            })
        for frame in worker_connection.sent:
            outer_launcher.connection.push(frame)
        result = _supervisor(
            launcher=outer_launcher,
            containment=FakeContainmentBackend(),
            clock=clock,
            config=config,
        ).run(_no_op_entry, ())

        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_failure is not None

    def test_events_never_carry_raw_output_or_prompt_text(self, image: tuple[str, str]) -> None:
        connection = FakeBoundedConnection()
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 100.0})
        generation_launcher = _launcher()
        generation_launcher.connection.push(
            {"kind": "success", "raw_output": "SECRET-RAW-OUTPUT-MARKER"}
        )
        artifact_ref, digest = image
        secret_prompt = "SECRET-PROMPT-MARKER"
        request, runtime_config, policy, _prompt, config = self._args(artifact_ref, digest)
        adapter_worker_entry(
            connection,
            request,
            runtime_config,
            policy,
            secret_prompt,
            config,
            generation_launcher=generation_launcher,
            self_contain=lambda: None,
            clock=FakeClock(),
        )
        seqs = [frame['seq'] for frame in _progress_frames(connection.sent)]
        assert seqs == list(range(1, len(seqs) + 1))
        for frame in connection.sent:
            serialized = str(frame)
            assert "SECRET-RAW-OUTPUT-MARKER" not in serialized
            assert secret_prompt not in serialized

    def test_adapter_started_send_failure_stops_before_adapter_or_child_construction(self) -> None:
        connection = FakeBoundedConnection(fail_send_kinds={"ADAPTER_STARTED"})
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 100.0})
        generation_launcher = _launcher()
        request, runtime_config, policy, prompt, config = self._args()

        with pytest.raises(Feat018ProtocolViolationError, match="progress event send failed"):
            adapter_worker_entry(
                connection,
                request,
                runtime_config,
                policy,
                prompt,
                config,
                generation_launcher=generation_launcher,
                self_contain=lambda: None,
                clock=FakeClock(),
            )

        assert _progress_frames(connection.sent) == []
        assert generation_launcher.launch_calls == []

    def test_attempt_started_send_failure_stops_before_generation_child_launch(
        self, image: tuple[str, str]
    ) -> None:
        connection = FakeBoundedConnection(fail_send_kinds={"GENERATION_ATTEMPT_STARTED"})
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 100.0})
        generation_launcher = _launcher()
        artifact_ref, digest = image
        request, runtime_config, policy, prompt, config = self._args(artifact_ref, digest)

        with pytest.raises(Feat018ProtocolViolationError, match="attempt event send failed"):
            adapter_worker_entry(
                connection,
                request,
                runtime_config,
                policy,
                prompt,
                config,
                generation_launcher=generation_launcher,
                self_contain=lambda: None,
                clock=FakeClock(),
            )

        assert [frame["kind"] for frame in connection.sent] == ["ADAPTER_STARTED"]
        assert generation_launcher.launch_calls == []

    def test_terminal_send_failure_raises_a_sanitized_protocol_error(
        self, image: tuple[str, str]
    ) -> None:
        connection = FakeBoundedConnection(fail_send_kinds={"TERMINAL"})
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 100.0})
        generation_launcher = _launcher()
        generation_launcher.connection.push({"kind": "success", "raw_output": _success_payload()})
        artifact_ref, digest = image
        request, runtime_config, policy, prompt, config = self._args(artifact_ref, digest)

        with pytest.raises(Feat018ProtocolViolationError, match="progress event send failed"):
            adapter_worker_entry(
                connection,
                request,
                runtime_config,
                policy,
                prompt,
                config,
                generation_launcher=generation_launcher,
                self_contain=lambda: None,
                clock=FakeClock(),
            )

        assert generation_launcher.launch_calls
        assert [frame['kind'] for frame in _progress_frames(connection.sent)] == [
            "ADAPTER_STARTED",
            "GENERATION_ATTEMPT_STARTED",
        ]


class TestAdapterCallSupervisorAuthority:
    def test_delayed_first_message_still_terminates_at_the_supervisors_own_deadline(self) -> None:
        launcher = _launcher()  # never pushes CONTAINMENT_READY acknowledgment or any event
        containment = FakeContainmentBackend()
        clock = FakeClock()

        class _AdvancingConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                clock.advance(timeout)
                return None

        launcher.connection = _AdvancingConnection(inbox=launcher.connection.inbox)
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())

        assert result.final_state is ProgressState.FROZEN
        assert result.attempt_count is None
        assert clock() >= 10.0
        assert containment.terminate_calls == 1

    def test_worker_clock_skew_does_not_affect_supervisor_termination_time(self) -> None:
        # The supervisor never reads or trusts any worker-reported clock value at all; a
        # fake worker double that would compute a skewed local deadline has no channel by
        # which that skew could reach the supervisor's own cap_deadline_monotonic.
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()

        class _AdvancingConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                clock.advance(timeout)
                return None

        launcher.connection = _AdvancingConnection(inbox=launcher.connection.inbox)
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.final_state is ProgressState.FROZEN
        assert clock() == pytest.approx(10.0, abs=1.0)

    def test_worker_ignoring_the_budget_is_still_bounded_by_the_supervisor(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push(
            {"seq": 1, "kind": "ADAPTER_STARTED"}
        )  # worker "ignores" its budget and just proceeds; no further events ever arrive

        class _AdvancingConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                frame = super().recv_frame(timeout)
                if frame is None:
                    clock.advance(timeout)
                return frame

        launcher.connection = _AdvancingConnection(inbox=launcher.connection.inbox)
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.final_state is ProgressState.FROZEN
        assert result.attempt_count is None

    def test_late_success_after_deadline_is_discarded_by_the_supervisor(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()

        class _LateSuccessConnection(FakeBoundedConnection):
            served = False

            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                if not self.served:
                    self.served = True
                    clock.set(999.0)  # jump well past the deadline before delivering
                    return {
                        "seq": 1,
                        "kind": "TERMINAL",
                        "outcome": "SUCCEEDED",
                    }
                return None

        launcher.connection = _LateSuccessConnection(inbox=launcher.connection.inbox)
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.final_state is ProgressState.FROZEN
        assert result.terminal_outcome is None

    def test_retry_near_deadline_does_not_extend_the_run(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        launcher.connection.push(
            {"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1}
        )

        class _NearDeadlineConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                frame = super().recv_frame(timeout)
                if frame is None:
                    clock.advance(timeout)
                else:
                    clock.set(9.99)
                if frame is not None and frame.get("attempt_number") == 1:
                    self.inbox.append(
                        {
                            "seq": 3,
                            "kind": "GENERATION_ATTEMPT_STARTED",
                            "attempt_number": 2,
                        }
                    )
                return frame

        launcher.connection = _NearDeadlineConnection(inbox=launcher.connection.inbox)
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.final_state is ProgressState.FROZEN
        assert clock() >= 10.0


class TestSupervisorProgressFailureTruth:
    @pytest.mark.parametrize(
        ("frames", "expected_reason"),
        [
            (
                [{"seq": "1", "kind": "ADAPTER_STARTED"}],
                "malformed progress frame",
            ),
            (
                [
                    {
                        "seq": 1,
                        "kind": "ADAPTER_STARTED",
                        "raw_output": "SECRET-RAW-PROGRESS",
                    }
                ],
                "malformed progress frame",
            ),
            ([{"seq": 1, "kind": "UNKNOWN"}], "malformed progress frame"),
            (
                [
                    {"seq": 1, "kind": "ADAPTER_STARTED"},
                    {"seq": 1, "kind": "ADAPTER_STARTED"},
                ],
                "duplicate progress sequence",
            ),
            (
                [
                    {"seq": 1, "kind": "ADAPTER_STARTED"},
                    {
                        "seq": 3,
                        "kind": "GENERATION_ATTEMPT_STARTED",
                        "attempt_number": 1,
                    },
                ],
                "gapped progress sequence",
            ),
            (
                [
                    {"seq": 2, "kind": "ADAPTER_STARTED"},
                    {"seq": 1, "kind": "ADAPTER_STARTED"},
                ],
                "gapped progress sequence",
            ),
            (
                [
                    {
                        "seq": 1,
                        "kind": "GENERATION_ATTEMPT_STARTED",
                        "attempt_number": 1,
                    }
                ],
                "invalid progress transition",
            ),
            (
                [
                    {"seq": 1, "kind": "ADAPTER_STARTED"},
                    {"seq": 2, "kind": "ADAPTER_STARTED"},
                ],
                "invalid progress transition",
            ),
            (
                [
                    {"seq": 1, "kind": "ADAPTER_STARTED"},
                    {
                        "seq": 2,
                        "kind": "GENERATION_ATTEMPT_STARTED",
                        "attempt_number": 1,
                    },
                    {
                        "seq": 3,
                        "kind": "GENERATION_ATTEMPT_STARTED",
                        "attempt_number": 1,
                    },
                ],
                "invalid progress transition",
            ),
        ],
        ids=(
            "bad-seq-type",
            "extra-secret-field",
            "unknown-kind",
            "duplicate",
            "gap",
            "reordered",
            "attempt-before-adapter",
            "second-adapter",
            "repeated-attempt",
        ),
    )
    def test_progress_protocol_failure_is_explicit_and_non_success(
        self, frames: list[dict[str, object]], expected_reason: str
    ) -> None:
        launcher = _launcher()
        for frame in frames:
            launcher.connection.push(frame)
        containment = FakeContainmentBackend()
        clock = FakeClock()

        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )

        assert result.final_state is ProgressState.FROZEN
        assert result.primary_failure_reason == expected_reason
        assert "SECRET-RAW-PROGRESS" not in result.primary_failure_reason
        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert result.is_success is False

    def test_oversized_progress_frame_is_explicitly_failed(self) -> None:
        launcher = _launcher()
        launcher.connection.raise_on_recv = Feat018FrameTooLargeError(
            "SECRET-oversized-frame-detail"
        )
        containment = FakeContainmentBackend()
        clock = FakeClock()

        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )

        assert result.final_state is ProgressState.FROZEN
        assert result.primary_failure_reason == "progress frame exceeded the IPC envelope limit"
        assert "SECRET-oversized-frame-detail" not in result.primary_failure_reason
        assert result.effective_outcome is EffectiveOutcome.FAILED

    def test_worker_exit_without_terminal_event_exposes_protocol_lifecycle_failure(self) -> None:
        launcher = _launcher()
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        launcher.connection.push(
            {"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1}
        )
        clock = FakeClock()

        class _TerminalSendFailureConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                frame = super().recv_frame(timeout)
                if frame is None:
                    launcher.handle.mark_dead()
                return frame

        launcher.connection = _TerminalSendFailureConnection(inbox=launcher.connection.inbox)
        containment = FakeContainmentBackend()

        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )

        assert result.final_state is ProgressState.FROZEN
        assert result.attempt_count == 1
        assert result.terminal_outcome is None
        assert result.primary_failure_reason == "adapter worker exited before terminal event"
        assert result.effective_outcome is EffectiveOutcome.FAILED


class TestAdapterCallSupervisorContainmentGate:
    def test_containment_assignment_failure_stops_before_execution(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend(confirm_result=False)
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment
        assert launcher.connection.sent == []  # no CONTAINMENT_READY was ever sent
        assert launcher.handle.terminate_calls >= 1

    def test_containment_primitive_creation_failure_never_spawns_the_worker(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend(create_fails=True)
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment
        assert launcher.launch_calls == []
        assert containment.terminate_calls == 1
        assert containment.close_calls == 1
        assert result.primary_failure_reason == "containment creation failed"
        assert result.effective_outcome is EffectiveOutcome.FAILED

    def test_windows_configuration_failure_is_closed_by_supervisor_before_launch(self) -> None:
        fake = _FakeKernel32()
        fake.set_information_result = False
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))
        launcher = _launcher()
        clock = FakeClock()
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(),
            launcher=launcher,
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )

        result = supervisor.run(_no_op_entry, ())

        assert launcher.launch_calls == []
        assert containment._job_handle is None
        assert result.stopped_before_containment is True
        assert result.primary_failure_reason == "containment creation failed"
        assert result.effective_outcome is EffectiveOutcome.FAILED
        assert [call for call in fake.calls if call[0] == "CloseHandle"] == [
            ("CloseHandle", (fake.job_handle,))
        ]

    def test_deadline_during_assignment_terminates_the_worker_at_the_gate(self) -> None:
        launcher = _launcher()
        clock = FakeClock()

        class _SlowContainment(FakeContainmentBackend):
            def confirm_worker_contained(
                self, worker: ProcessHandle, *, timeout: float, retry_interval: float
            ) -> bool:
                # Models a real bounded backend: consuming more wall time than its own
                # timeout budget before confirming means it must report failure, not success.
                clock.advance(timeout + 1.0)
                return False

        containment = _SlowContainment(confirm_result=True)
        supervisor = _supervisor(
            launcher=launcher, containment=containment, clock=clock, config=_config()
        )
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment

    def test_worker_death_before_release_does_not_hang(self) -> None:
        launcher = _launcher()
        launcher.handle.mark_dead()
        containment = FakeContainmentBackend(confirm_result=False)
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment

    def test_successful_gate_sends_containment_ready_with_the_advisory_duration(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend(confirm_result=True)
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        supervisor.run(_no_op_entry, ())
        assert len(launcher.connection.sent) >= 1
        first = launcher.connection.sent[0]
        assert first["kind"] == "CONTAINMENT_READY"
        assert isinstance(first["remaining_seconds_at_spawn"], (int, float))

    @pytest.mark.parametrize(
        "clock_after_confirmation",
        [10.0, float("nan"), float("inf"), -float("inf")],
        ids=("zero-remaining", "nan-remaining", "positive-infinity", "negative-infinity"),
    )
    def test_supervisor_rejects_non_positive_or_non_finite_release_duration(
        self, clock_after_confirmation: float
    ) -> None:
        launcher = _launcher()
        clock = FakeClock()

        class _ClockMovingContainment(FakeContainmentBackend):
            def confirm_worker_contained(
                self, worker: ProcessHandle, *, timeout: float, retry_interval: float
            ) -> bool:
                result = super().confirm_worker_contained(
                    worker, timeout=timeout, retry_interval=retry_interval
                )
                clock.set(clock_after_confirmation)
                return result

        containment = _ClockMovingContainment()
        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )

        assert launcher.launch_calls
        assert launcher.connection.sent == []
        assert result.stopped_before_containment is True
        assert result.primary_failure_reason == "containment gate deadline expired"
        assert result.effective_outcome is (
            EffectiveOutcome.FAILED if clock_after_confirmation == 10.0
            else EffectiveOutcome.CLEANUP_FAILED
        )


class TestAdapterCallSupervisorHangsAndCleanup:
    def test_hang_before_first_generate_terminates_at_deadline_with_null_attempt_count(
        self,
    ) -> None:
        launcher = _launcher()  # ADAPTER_STARTED is never sent
        containment = FakeContainmentBackend()
        clock = FakeClock()

        class _SilentConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                clock.advance(timeout)
                return None

        launcher.connection = _SilentConnection(inbox=launcher.connection.inbox)
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.attempt_count is None
        assert result.final_state is ProgressState.FROZEN

    def test_hang_after_generate_returns_keeps_last_accepted_attempt_number(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend()
        clock = FakeClock()
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        launcher.connection.push(
            {"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1}
        )

        class _HangConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                frame = super().recv_frame(timeout)
                if frame is None:
                    clock.advance(timeout)
                return frame

        launcher.connection = _HangConnection(inbox=launcher.connection.inbox)
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.attempt_count == 1
        assert result.final_state is ProgressState.FROZEN
        assert result.terminal_outcome is None

    def test_cleanup_hang_reports_cleanup_failed(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend(empty_after_terminate=False)
        clock = FakeClock()
        supervisor = _supervisor(
            launcher=launcher,
            containment=containment,
            clock=clock,
            config=_config(cleanup_deadline_seconds=0.2),
        )
        result = supervisor.run(_no_op_entry, ())
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED

    def test_successful_run_reports_cleanup_succeeded(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend(empty_after_terminate=True)
        clock = FakeClock()
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        launcher.connection.push(
            {"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1}
        )
        _push_success_d9_frames(launcher.connection)
        launcher.connection.push({"seq": 3, "kind": "TERMINAL", "outcome": "SUCCEEDED"})
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.cleanup_status is CleanupStatus.SUCCEEDED
        assert result.final_state is ProgressState.TERMINAL
        assert result.attempt_count == 1
        assert result.terminal_outcome == "SUCCEEDED"
        assert result.effective_outcome is EffectiveOutcome.SUCCEEDED
        assert result.is_success is True


# ------------------------------------------------------------------------------------------
# F2 -- exception-safe lifecycle: every exit path still cleans up
# ------------------------------------------------------------------------------------------


@dataclass(slots=True)
class _RaisingLauncher:
    """A launcher whose ``launch`` always raises, never returning a process/connection."""

    exc: BaseException
    launch_calls: int = field(default=0, init=False)

    def launch(
        self, entry: Callable[..., None], args: tuple[object, ...]
    ) -> tuple[ProcessHandle, FakeBoundedConnection]:
        del entry, args
        self.launch_calls += 1
        raise self.exc


class TestSupervisorExceptionSafeLifecycle:
    def test_launcher_cleanup_failure_survives_empty_containment(self) -> None:
        containment = FakeContainmentBackend()
        cleanup_failure = Feat018CleanupFailedError("launch rollback failed")
        clock = FakeClock()
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(),
            launcher=_RaisingLauncher(cleanup_failure),
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )

        result = supervisor.run(_no_op_entry, ())

        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert isinstance(result.cleanup_failure, Feat018CleanupFailedError)
        assert containment.is_empty() is True
        assert containment.close_calls == 1

    def test_rollback_survivor_retains_ownership_until_retry_releases_it(self) -> None:
        process = _FakeMultiprocessingProcess(die_on_terminate=False, die_on_kill=False)
        context = _FakeSpawnContext(process=process)
        wrapper_calls = 0

        def fail_parent_wrapper(connection: Any, max_envelope_bytes: int) -> BoundedConnection:
            nonlocal wrapper_calls
            wrapper_calls += 1
            if wrapper_calls == 2:
                raise RuntimeError("parent wrapper failed")
            return MultiprocessingBoundedConnection(connection, max_envelope_bytes)

        launcher = MultiprocessingProcessLauncher(
            max_envelope_bytes=10_000,
            context_factory=lambda: context,
            connection_factory=fail_parent_wrapper,
        )
        containment = FakeContainmentBackend()
        clock = FakeClock()
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(),
            launcher=launcher,
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )

        result = supervisor.run(_no_op_entry, ())

        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_failure is not None
        assert result.cleanup_failure.owned_process is not None
        assert getattr(result.cleanup_failure.owned_process, "process") is process
        assert process.alive is True
        assert process.close_calls == 0
        assert process.kill_calls >= 2
        assert context.parent.closed and context.child.closed

        process.die_on_kill = True
        assert result.cleanup_failure.retry_cleanup(grace_seconds=0.1, kill_join_seconds=0.1)

        assert process.closed is True
        assert result.cleanup_failure.owned_process is None
        assert result.cleanup_failure.owned_connections == ()
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED

    def test_launch_failure_still_runs_cleanup_and_reports_primary_failure(self) -> None:
        containment = FakeContainmentBackend()
        launcher = _RaisingLauncher(RuntimeError("spawn exploded"))
        clock = FakeClock()
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(),
            launcher=launcher,
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment is True
        assert result.primary_failure_reason == "adapter worker launch failed"
        assert containment.created is True
        assert containment.terminate_calls == 1
        assert containment.close_calls == 1
        assert result.cleanup_status is CleanupStatus.SUCCEEDED
        assert result.effective_outcome is EffectiveOutcome.FAILED

    def test_confirm_worker_contained_exception_fails_closed_and_cleans_up(self) -> None:
        launcher = _launcher()
        containment = FakeContainmentBackend(confirm_raises=RuntimeError("confirm exploded"))
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment is True
        assert result.primary_failure_reason == "containment confirmation failed"
        assert launcher.connection.sent == []  # CONTAINMENT_READY was never sent
        assert launcher.handle.terminate_calls >= 1
        assert containment.terminate_calls == 1
        assert containment.close_calls == 1
        assert result.effective_outcome is EffectiveOutcome.FAILED

    def test_containment_ready_send_failure_fails_closed_and_cleans_up(self) -> None:
        launcher = _launcher()
        launcher.connection.raise_on_send = BrokenPipeError("worker already gone")
        containment = FakeContainmentBackend()
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment is True
        assert result.primary_failure_reason is not None
        assert "CONTAINMENT_READY" in result.primary_failure_reason
        assert containment.terminate_calls == 1
        assert containment.close_calls == 1

    def test_recv_frame_protocol_violation_during_loop_still_cleans_up(self) -> None:
        launcher = _launcher()
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})

        class _ThenRaisingConnection(FakeBoundedConnection):
            served = False

            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                if not self.served:
                    self.served = True
                    return super().recv_frame(timeout)
                raise Feat018ProtocolViolationError("oversized frame")

        launcher.connection = _ThenRaisingConnection(inbox=launcher.connection.inbox)
        containment = FakeContainmentBackend()
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert result.attempt_count is None
        assert result.final_state is ProgressState.FROZEN
        assert containment.terminate_calls == 1
        assert containment.close_calls == 1
        assert result.cleanup_status is CleanupStatus.SUCCEEDED
        assert result.primary_failure_reason == "progress frame failed bounded protocol validation"

    def test_connection_close_failure_does_not_prevent_containment_close(self) -> None:
        launcher = _launcher()
        launcher.connection.raise_on_close = OSError("close failed")
        containment = FakeContainmentBackend()
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())
        assert containment.close_calls == 1
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED

    def test_containment_close_failure_does_not_raise(self) -> None:
        launcher = _launcher()

        class _RaisingCloseContainment(FakeContainmentBackend):
            def close(self) -> None:
                super().close()
                raise OSError("containment close failed")

        containment = _RaisingCloseContainment()
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())  # must not raise
        assert containment.close_calls == 1
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED

    def test_terminate_process_failure_does_not_prevent_containment_termination(self) -> None:
        launcher = _launcher()
        launcher.handle.die_on_terminate = False
        launcher.handle.die_on_kill = False
        launcher.handle.raise_on_terminate = OSError("terminate failed")
        containment = FakeContainmentBackend(confirm_result=False)
        clock = FakeClock()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        result = supervisor.run(_no_op_entry, ())  # must not raise
        assert result.stopped_before_containment is True
        assert containment.terminate_calls == 1
        assert containment.close_calls == 1

    def test_cleanup_coordinator_runs_exactly_once_per_run_regardless_of_failure_point(
        self,
    ) -> None:
        for launcher, containment in (
            (_RaisingLauncher(RuntimeError("boom")), FakeContainmentBackend()),
            (_launcher(), FakeContainmentBackend(confirm_raises=RuntimeError("boom"))),
        ):
            clock = FakeClock()
            supervisor = Feat018AdapterCallSupervisor(
                config=_config(),
                launcher=launcher,
                containment_factory=lambda c=containment: c,
                clock=clock,
                sleep=clock.advance,
            )
            supervisor.run(_no_op_entry, ())
            assert containment.terminate_calls == 1
            assert containment.close_calls == 1

    def test_primary_failure_plus_cleanup_failure_has_cleanup_effective_outcome(self) -> None:
        containment = FakeContainmentBackend(empty_after_terminate=False)
        launcher = _RaisingLauncher(RuntimeError("SECRET-launch-detail"))
        clock = FakeClock()
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(cleanup_deadline_seconds=0.2),
            launcher=launcher,
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )

        result = supervisor.run(_no_op_entry, ())

        assert result.primary_failure_reason == "adapter worker launch failed"
        assert "SECRET-launch-detail" not in result.primary_failure_reason
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.is_success is False

    def test_cleanup_query_failure_cannot_leave_a_successful_effective_outcome(self) -> None:
        launcher = _launcher()
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        launcher.connection.push(
            {"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1}
        )
        _push_success_d9_frames(launcher.connection)
        launcher.connection.push({"seq": 3, "kind": "TERMINAL", "outcome": "SUCCEEDED"})
        containment = FakeContainmentBackend(
            raise_on_is_empty=RuntimeError("SECRET-cleanup-query-detail")
        )
        clock = FakeClock()

        result = _supervisor(launcher=launcher, containment=containment, clock=clock).run(
            _no_op_entry, ()
        )

        assert result.final_state is ProgressState.TERMINAL
        assert result.terminal_outcome == "SUCCEEDED"
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.primary_failure_reason == "cleanup verification failed"
        assert "SECRET-cleanup-query-detail" not in result.primary_failure_reason


# ------------------------------------------------------------------------------------------
# Evidence commit protocol
# ------------------------------------------------------------------------------------------


class _FaultyFilesystemOps:
    """Wraps a real tmp_path-backed filesystem, injecting a failure at one named operation."""

    def __init__(self, fail_on: str | None = None) -> None:
        self._fail_on = fail_on
        self._calls = 0

    def _maybe_fail(self, operation: str) -> None:
        self._calls += 1
        if self._fail_on == operation:
            raise OSError(f"injected failure at {operation}")

    def write_new(self, path: Path, content: bytes) -> None:
        self._maybe_fail(f"write_new:{path.name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(content)

    def rename(self, source: Path, destination: Path) -> None:
        self._maybe_fail(f"rename:{destination.name}")
        source.rename(destination)

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def exists(self, path: Path) -> bool:
        return path.exists()

    def remove(self, path: Path) -> None:
        self._maybe_fail(f"remove:{path.name}")
        path.unlink(missing_ok=True)


class TestEvidenceCommitProtocol:
    def _writer(self, tmp_path: Path, *, fail_on: str | None = None) -> tuple[
        Feat018EvidenceCommitWriter, _FaultyFilesystemOps, Path, Path
    ]:
        json_path = tmp_path / "evidence" / "P2_LIVE_SMOKE_20260914.json"
        markdown_path = tmp_path / "notes" / "P2_LIVE_SMOKE_20260914.md"
        fs = _FaultyFilesystemOps(fail_on=fail_on)
        writer = Feat018EvidenceCommitWriter(
            json_path=json_path, markdown_path=markdown_path, fs=fs  # type: ignore[arg-type]
        )
        return writer, fs, json_path, markdown_path

    def test_successful_commit_produces_an_authoritative_pair(self, tmp_path: Path) -> None:
        writer, _fs, json_path, markdown_path = self._writer(tmp_path)
        run_id = new_run_id()
        evidence_id = new_evidence_id()
        result = writer.commit(
            run_id=run_id,
            evidence_id=evidence_id,
            json_fields={"status": "SUCCEEDED"},
            markdown_body="Smoke run succeeded.",
        )
        assert result.committed
        verdict = read_committed_pair(json_path, markdown_path)
        assert verdict.verdict is PairVerdict.AUTHORITATIVE

    def test_markdown_temp_write_failure_leaves_no_final_path_file(self, tmp_path: Path) -> None:
        writer, _fs, json_path, markdown_path = self._writer(
            tmp_path, fail_on="write_new:P2_LIVE_SMOKE_20260914.md.tmp-run"
        )
        result = writer.commit(
            run_id="run",
            evidence_id="ev",
            json_fields={"status": "FAILED"},
            markdown_body="x",
        )
        assert not result.committed
        assert not json_path.exists()
        assert not markdown_path.exists()

    def test_markdown_temp_written_json_temp_write_fails_g5_1(self, tmp_path: Path) -> None:
        writer, _fs, json_path, markdown_path = self._writer(
            tmp_path, fail_on="write_new:P2_LIVE_SMOKE_20260914.json.tmp-run-g5-1"
        )
        result = writer.commit(
            run_id="run-g5-1",
            evidence_id="ev",
            json_fields={"status": "FAILED"},
            markdown_body="x",
        )
        assert not result.committed
        assert not json_path.exists()
        assert not markdown_path.exists()
        # the lone Markdown temp file was rolled back, not left as provisional garbage
        leftovers = list(tmp_path.rglob("*.tmp-*"))
        assert leftovers == []

    def test_markdown_rename_failure_rolls_back_and_leaves_nothing_at_final_paths(
        self, tmp_path: Path
    ) -> None:
        writer, _fs, json_path, markdown_path = self._writer(
            tmp_path, fail_on="rename:P2_LIVE_SMOKE_20260914.md"
        )
        result = writer.commit(
            run_id="run", evidence_id="ev", json_fields={"status": "FAILED"}, markdown_body="x"
        )
        assert not result.committed
        assert not json_path.exists()
        assert not markdown_path.exists()

    def test_json_rename_failure_rolls_back_markdown_leaving_pair_non_authoritative(
        self, tmp_path: Path
    ) -> None:
        writer, _fs, json_path, markdown_path = self._writer(
            tmp_path, fail_on="rename:P2_LIVE_SMOKE_20260914.json"
        )
        result = writer.commit(
            run_id="run", evidence_id="ev", json_fields={"status": "SUCCEEDED"}, markdown_body="x"
        )
        assert not result.committed
        # rollback should have removed the just-published Markdown
        assert not markdown_path.exists()
        assert not json_path.exists()

    def test_json_rename_failure_with_rollback_failure_reports_residual_artifact(
        self, tmp_path: Path
    ) -> None:
        class _DoubleFaultFs(_FaultyFilesystemOps):
            def rename(self, source: Path, destination: Path) -> None:
                if destination.name == "evidence.json":
                    raise OSError("rename failed")
                super().rename(source, destination)

            def remove(self, path: Path) -> None:
                if path.name == "evidence.md":
                    raise OSError("rollback also failed")
                super().remove(path)

        json_path = tmp_path / "evidence.json"
        markdown_path = tmp_path / "evidence.md"
        fs = _DoubleFaultFs()
        writer = Feat018EvidenceCommitWriter(
            json_path=json_path, markdown_path=markdown_path, fs=fs  # type: ignore[arg-type]
        )
        result = writer.commit(
            run_id="run", evidence_id="ev", json_fields={"status": "SUCCEEDED"}, markdown_body="x"
        )
        assert not result.committed
        assert markdown_path in result.residual_paths
        assert markdown_path.exists()  # truthfully still present, not silently deleted


class TestEvidenceFinalizer:
    @pytest.mark.parametrize("runtime_outcome", list(EffectiveOutcome))
    def test_commit_point_follows_cleanup_and_provisional_audit(
        self, tmp_path: Path, runtime_outcome: EffectiveOutcome
    ) -> None:
        events: list[str] = []

        class RecordingFs(_FaultyFilesystemOps):
            def write_new(self, path: Path, content: bytes) -> None:
                events.append("write:" + path.suffix)
                super().write_new(path, content)

            def rename(self, source: Path, destination: Path) -> None:
                events.append("rename:" + destination.suffix)
                assert "audit" in events
                super().rename(source, destination)

        writer = Feat018EvidenceCommitWriter(
            tmp_path / "result.json", tmp_path / "result.md", RecordingFs()
        )
        audit_paths: list[tuple[Path, Path]] = []

        def cleanup() -> CleanupStatus:
            events.append("cleanup")
            return CleanupStatus.SUCCEEDED

        def audit(provisional_json: Path, provisional_md: Path) -> bool:
            audit_paths.append((provisional_json, provisional_md))
            assert not writer.json_path.exists()
            if provisional_md == writer.markdown_path:
                assert writer.markdown_path.exists()
            else:
                assert not writer.markdown_path.exists()
            assert read_committed_pair(provisional_json, provisional_md).verdict is (
                PairVerdict.AUTHORITATIVE
            )
            assert json.loads(provisional_json.read_bytes())["status"] == runtime_outcome.value
            events.append("audit")
            return True

        result = Feat018EvidenceFinalizer(writer).finalize(
            run_id="run", evidence_id="ev", runtime_outcome=runtime_outcome,
            cleanup=cleanup, postflight=audit,
        )
        assert result.committed
        assert events == ["cleanup", "write:.tmp-run", "write:.tmp-run", "audit",
                          "rename:.md", "audit", "rename:.json"]
        assert len(audit_paths) == 2
        assert audit_paths[0][1].name.endswith(".tmp-run")
        assert audit_paths[1][1] == writer.markdown_path

        if runtime_outcome is EffectiveOutcome.SUCCEEDED:
            late_json = tmp_path / "late-result.json"
            late_markdown = tmp_path / "late-result.md"
            late_writer = Feat018EvidenceCommitWriter(
                late_json, late_markdown, _FaultyFilesystemOps()
            )
            late_inventory = Feat018ArtifactInventory((tmp_path,), max_entries=50)
            late_inventory.capture()
            late_audit_calls = [0]

            def late_audit(json_candidate: Path, markdown_candidate: Path) -> bool:
                late_audit_calls[0] += 1
                if late_audit_calls[0] == 2:
                    (tmp_path / "mutation-immediately-before-json-commit").write_bytes(b"late")
                return late_inventory.verify_provisional(json_candidate, markdown_candidate)

            late_result = Feat018EvidenceFinalizer(late_writer).finalize(
                run_id="late-run", evidence_id="late-ev",
                runtime_outcome=EffectiveOutcome.SUCCEEDED,
                cleanup=lambda: CleanupStatus.SUCCEEDED,
                postflight=late_audit,
            )
            assert not late_result.committed
            assert late_audit_calls[0] == 2
            assert not late_json.exists() and not late_markdown.exists()
        assert json.loads(writer.json_path.read_bytes())["status"] == runtime_outcome.value
        assert f"status: {runtime_outcome.value}" in writer.markdown_path.read_text()
        before = (writer.json_path.read_bytes(), writer.markdown_path.read_bytes())
        assert read_committed_pair(writer.json_path, writer.markdown_path).verdict is (
            PairVerdict.AUTHORITATIVE
        )
        assert before == (writer.json_path.read_bytes(), writer.markdown_path.read_bytes())

    @pytest.mark.parametrize("raises", [False, True])
    def test_cleanup_failure_cannot_publish_success(self, tmp_path: Path, raises: bool) -> None:
        writer, _, jp, mp = TestEvidenceCommitProtocol()._writer(tmp_path)

        def cleanup() -> CleanupStatus:
            if raises:
                raise RuntimeError("SECRET-CLEANUP-DETAIL")
            return CleanupStatus.CLEANUP_FAILED

        def audit(_jp: Path, _mp: Path) -> bool:
            pytest.fail("audit must not run after unverifiable cleanup")

        result = Feat018EvidenceFinalizer(writer).finalize(
            run_id="run", evidence_id="ev", runtime_outcome=EffectiveOutcome.SUCCEEDED,
            cleanup=cleanup, postflight=audit,
        )
        assert not result.committed
        assert "SECRET" not in str(result)
        assert not jp.exists() and not mp.exists()

    @pytest.mark.parametrize("mode", ["false", "exception", "json-mutation", "md-mutation"])
    def test_precommit_gate_cannot_leave_false_pass(self, tmp_path: Path, mode: str) -> None:
        writer, _, jp, mp = TestEvidenceCommitProtocol()._writer(tmp_path)
        inventory: Feat018ArtifactInventory | None = None
        audit_calls = 0
        if mode == "md-mutation":
            writer.json_path.parent.mkdir(parents=True, exist_ok=True)
            writer.markdown_path.parent.mkdir(parents=True, exist_ok=True)
            inventory = Feat018ArtifactInventory((tmp_path,), max_entries=20)
            inventory.capture()

        def audit(provisional_json: Path, provisional_md: Path) -> bool:
            nonlocal audit_calls
            audit_calls += 1
            if mode == "md-mutation":
                assert inventory is not None
                approved = inventory.verify_provisional(provisional_json, provisional_md)
                if audit_calls == 1:
                    (tmp_path / "mutation-after-initial-scan").write_bytes(b"changed")
                    return approved
                # This is the commit-adjacent recheck, immediately before the JSON rename.
                return approved
            if mode == "exception":
                raise RuntimeError("SECRET-AUDIT-DETAIL")
            if mode == "false":
                return False
            target = provisional_json if mode == "json-mutation" else provisional_md
            target.write_bytes(b"SECRET-MUTATED-ARTIFACT")
            return True

        result = Feat018EvidenceFinalizer(writer).finalize(
            run_id="run", evidence_id="ev", runtime_outcome=EffectiveOutcome.SUCCEEDED,
            cleanup=lambda: CleanupStatus.SUCCEEDED, postflight=audit,
        )
        assert not result.committed
        assert "SECRET" not in str(result)
        assert read_committed_pair(jp, mp).verdict is PairVerdict.NON_AUTHORITATIVE
        assert not list(tmp_path.rglob("*.tmp-*"))
        if mode == "md-mutation":
            assert audit_calls == 2

    def test_missing_postflight_cannot_bypass_gate(self, tmp_path: Path) -> None:
        writer, _, jp, mp = TestEvidenceCommitProtocol()._writer(tmp_path)
        with pytest.raises(ValueError, match="postflight is mandatory"):
            Feat018EvidenceFinalizer(writer).finalize(
                run_id="run", evidence_id="ev", runtime_outcome=EffectiveOutcome.SUCCEEDED,
                cleanup=lambda: CleanupStatus.SUCCEEDED,
                postflight=None,  # type: ignore[arg-type]
            )
        assert not jp.exists() and not mp.exists()

    def test_existing_pair_is_preserved(self, tmp_path: Path) -> None:
        writer, _, jp, mp = TestEvidenceCommitProtocol()._writer(tmp_path)
        writer.commit(run_id="old", evidence_id="old", json_fields={"status": "FAILED"},
                      markdown_body="old")
        before = jp.read_bytes(), mp.read_bytes()
        result = Feat018EvidenceFinalizer(writer).finalize(
            run_id="new", evidence_id="new", runtime_outcome=EffectiveOutcome.SUCCEEDED,
            cleanup=lambda: CleanupStatus.SUCCEEDED, postflight=lambda _j, _m: True,
        )
        assert not result.committed
        assert before == (jp.read_bytes(), mp.read_bytes())

    def test_json_rename_failure_is_not_reported_as_success(self, tmp_path: Path) -> None:
        writer, _, jp, mp = TestEvidenceCommitProtocol()._writer(
            tmp_path, fail_on="rename:P2_LIVE_SMOKE_20260914.json"
        )
        result = Feat018EvidenceFinalizer(writer).finalize(
            run_id="run", evidence_id="ev", runtime_outcome=EffectiveOutcome.SUCCEEDED,
            cleanup=lambda: CleanupStatus.SUCCEEDED, postflight=lambda _j, _m: True,
        )
        assert not result.committed
        assert read_committed_pair(jp, mp).verdict is PairVerdict.NON_AUTHORITATIVE

    @pytest.mark.parametrize("identity", ["../outside", "x\nstatus: SUCCEEDED", "x" * 65])
    def test_identity_injection_is_rejected_after_cleanup(
        self, tmp_path: Path, identity: str
    ) -> None:
        writer, _, jp, mp = TestEvidenceCommitProtocol()._writer(tmp_path)
        calls: list[str] = []

        def cleanup() -> CleanupStatus:
            calls.append("cleanup")
            return CleanupStatus.SUCCEEDED

        with pytest.raises(ValueError, match="bounded opaque"):
            Feat018EvidenceFinalizer(writer).finalize(
                run_id=identity, evidence_id="ev", runtime_outcome=EffectiveOutcome.SUCCEEDED,
                cleanup=cleanup, postflight=lambda _j, _m: True,
            )
        assert calls == ["cleanup"]
        assert not jp.exists() and not mp.exists()

    def test_rollback_failure_reports_residuals(self, tmp_path: Path) -> None:
        class FailedRemovalFs(_FaultyFilesystemOps):
            def remove(self, path: Path) -> None:
                raise OSError("SECRET-REMOVE-DETAIL")

        writer = Feat018EvidenceCommitWriter(
            tmp_path / "result.json", tmp_path / "result.md", FailedRemovalFs()
        )
        result = Feat018EvidenceFinalizer(writer).finalize(
            run_id="run", evidence_id="ev", runtime_outcome=EffectiveOutcome.SUCCEEDED,
            cleanup=lambda: CleanupStatus.SUCCEEDED, postflight=lambda _j, _m: False,
        )
        assert not result.committed
        assert len(result.residual_paths) == 2
        assert all(path.exists() for path in result.residual_paths)
        assert "SECRET" not in str(result)
        assert not writer.json_path.exists()


class TestArtifactInventory:
    @pytest.mark.parametrize("change", ["none", "added", "deleted", "modified"])
    def test_exact_baseline_plus_provisional_pair(self, tmp_path: Path, change: str) -> None:
        baseline = tmp_path / "ignored-runtime.cfg"
        baseline.write_bytes(b"original")
        inventory = Feat018ArtifactInventory((tmp_path,), max_entries=20)
        inventory.capture()
        jp, mp = tmp_path / "a.json.tmp-run", tmp_path / "a.md.tmp-run"
        jp.write_bytes(b"json")
        mp.write_bytes(b"markdown")
        if change == "added":
            (tmp_path / "unexpected.log").write_bytes(b"SECRET")
        elif change == "deleted":
            baseline.unlink()
        elif change == "modified":
            baseline.write_bytes(b"changed-config")
        assert inventory.verify_provisional(jp, mp) is (change == "none")

    def test_budget_exhaustion_cannot_be_a_partial_pass(self, tmp_path: Path) -> None:
        (tmp_path / "extra").write_bytes(b"x")
        inventory = Feat018ArtifactInventory((tmp_path,), max_entries=1)
        with pytest.raises(Exception, match="budget"):
            inventory.capture()
        assert not inventory.verify_provisional(tmp_path / "a", tmp_path / "b")

    def test_absent_root_cannot_be_an_empty_baseline(self, tmp_path: Path) -> None:
        inventory = Feat018ArtifactInventory((tmp_path / "missing",), max_entries=10)
        with pytest.raises(OSError):
            inventory.capture()
        assert not inventory.verify_provisional(tmp_path / "a", tmp_path / "b")

    def test_other_worktree_root_is_rejected_lexically(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="worktree"):
            Feat018ArtifactInventory((tmp_path / ".worktrees" / "p2-t4",), max_entries=10)

    def test_reparse_metadata_is_rejected_without_following(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from types import SimpleNamespace

        monkeypatch.setattr(Path, "lstat", lambda _path: SimpleNamespace(
            st_mode=0o100644, st_file_attributes=0x400,
        ))
        with pytest.raises(Exception, match="reparse"):
            Feat018ArtifactInventory._fingerprint(tmp_path / "link")

    def test_provisional_files_must_be_inside_inventory(self, tmp_path: Path) -> None:
        root = tmp_path / "root"
        root.mkdir()
        inventory = Feat018ArtifactInventory((root,), max_entries=10)
        inventory.capture()
        jp, mp = tmp_path / "a", tmp_path / "b"
        jp.write_bytes(b"x")
        mp.write_bytes(b"x")
        assert not inventory.verify_provisional(jp, mp)

    def test_existing_baseline_file_cannot_be_excluded_as_provisional(self, tmp_path: Path) -> None:
        jp, mp = tmp_path / "a", tmp_path / "b"
        jp.write_bytes(b"x")
        mp.write_bytes(b"x")
        inventory = Feat018ArtifactInventory((tmp_path,), max_entries=10)
        inventory.capture()
        assert not inventory.verify_provisional(jp, mp)


class TestIncidentWriter:
    def test_incident_never_interpolates_raw_reason_or_residual_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = EvidenceCommitResult(
            False, "run", "ev", residual_paths=(Path("SECRET-PATH"),),
            failure_reason="SECRET-EXCEPTION",
        )
        writer = Feat018IncidentWriter(
            Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"),
            repository_root=tmp_path,
            git_ignored=True,
        )
        assert writer.write(result)
        content = writer.path.read_bytes()
        assert b"SECRET" not in content
        assert b"residual_count: 1" in content
        assert b"evidence_committed: false" in content
        assert not writer.write(result)  # preserves the prior incident
        assert writer.path.read_bytes() == content

        rejected_destinations = (
            (Path("tmp/feat018-live-lightning-incident-other/INCIDENT.md"), True),
            (Path("tmp/feat018-live-lightning-incident-run/../INCIDENT.md"), True),
            (Path("features/FEAT-018-live-image-canvas-flow/INCIDENT.md"), True),
            (tmp_path / "tmp/feat018-live-lightning-incident-run/INCIDENT.md", True),
            (Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"), False),
        )
        for path, git_ignored in rejected_destinations:
            rejected = Feat018IncidentWriter(
                path, repository_root=tmp_path, git_ignored=git_ignored
            )
            assert not rejected.write(result)

        from types import SimpleNamespace

        link_writer = Feat018IncidentWriter(
            Path("tmp/feat018-live-lightning-incident-link-run/INCIDENT.md"),
            repository_root=tmp_path,
            git_ignored=True,
        )
        original_lstat = Path.lstat

        def fake_link_lstat(path: Path) -> object:
            if path == link_writer.path.parent:
                return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
            return original_lstat(path)

        monkeypatch.setattr(Path, "lstat", fake_link_lstat)
        assert not link_writer.write(result)

        def fake_reparse_lstat(path: Path) -> object:
            if path == link_writer.path.parent:
                return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
            return original_lstat(path)

        monkeypatch.setattr(Path, "lstat", fake_reparse_lstat)
        assert not link_writer.write(result)

    def test_success_is_not_an_incident(self, tmp_path: Path) -> None:
        writer = Feat018IncidentWriter(
            Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"),
            repository_root=tmp_path,
            git_ignored=True,
        )
        assert not writer.write(EvidenceCommitResult(True, "run", "ev"))
        assert not writer.path.exists()


class TestSmokeFinalizationIntegration:
    @pytest.mark.parametrize(
        "mode", ["success", "unmapped", "extra-file", "cleanup-failure", "owned-cleanup-failure"]
    )
    def test_real_inventory_controls_publication(self, tmp_path: Path, mode: str) -> None:
        writer = Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
        incident = Feat018IncidentWriter(
            Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"),
            repository_root=tmp_path,
            git_ignored=True,
        )
        inventory = Feat018ArtifactInventory((tmp_path,), max_entries=20)
        inventory.capture()
        if mode == "extra-file":
            (tmp_path / "unexpected-raw-output").write_bytes(b"SECRET")
        supervisor = SupervisorRunResult(
            final_state=ProgressState.TERMINAL,
            attempt_count=1,
            terminal_outcome="SUCCEEDED",
            cleanup_status=CleanupStatus.SUCCEEDED,
            effective_outcome=EffectiveOutcome.SUCCEEDED,
            raw_status=None if mode == "unmapped" else "SUCCEEDED",
            cleanup_failure=(
                Feat018CleanupFailedError(owned_process=FakeProcessHandle())
                if mode == "owned-cleanup-failure" else None
            ),
        )
        result = finalize_smoke_run(
            supervisor, run_id="run", evidence_id="ev", inventory=inventory,
            cleanup=lambda: (
                CleanupStatus.CLEANUP_FAILED if mode == "cleanup-failure"
                else CleanupStatus.SUCCEEDED
            ),
            writer=writer, incident=incident,
        )
        if mode in {"success", "unmapped"}:
            assert result.evidence.committed
            assert not result.incident_written
            assert json.loads(writer.json_path.read_bytes())["status"] == (
                "SUCCEEDED" if mode == "success" else "FAILED"
            )
        else:
            assert not result.evidence.committed
            assert result.incident_written
            assert not writer.json_path.exists()
            assert "SECRET" not in incident.path.read_text()

    def test_uncaptured_inventory_never_succeeds(self, tmp_path: Path) -> None:
        writer = Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
        result = finalize_smoke_run(
            SupervisorRunResult(ProgressState.TERMINAL, 1, "SUCCEEDED", CleanupStatus.SUCCEEDED,
                                effective_outcome=EffectiveOutcome.SUCCEEDED,
                                raw_status="SUCCEEDED"),
            run_id="run", evidence_id="ev",
            inventory=Feat018ArtifactInventory((tmp_path,), max_entries=20),
            cleanup=lambda: CleanupStatus.SUCCEEDED, writer=writer,
            incident=Feat018IncidentWriter(
                Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"),
                repository_root=tmp_path,
                git_ignored=True,
            ),
        )
        assert not result.evidence.committed
        assert result.incident_written


class TestReadCommittedPairVerdicts:
    def test_missing_files_are_not_evidence(self, tmp_path: Path) -> None:
        result = read_committed_pair(tmp_path / "a.json", tmp_path / "a.md")
        assert result.verdict is PairVerdict.NON_AUTHORITATIVE

    def test_markdown_only_present_is_non_authoritative(self, tmp_path: Path) -> None:
        markdown_path = tmp_path / "a.md"
        markdown_path.write_text("# x\nrun_id: r\nevidence_id: e\n", encoding="utf-8")
        result = read_committed_pair(tmp_path / "a.json", markdown_path)
        assert result.verdict is PairVerdict.NON_AUTHORITATIVE

    def test_commit_state_not_final_is_non_authoritative(self, tmp_path: Path) -> None:
        writer, _fs, json_path, markdown_path = TestEvidenceCommitProtocol()._writer(tmp_path)
        writer.commit(
            run_id="run", evidence_id="ev", json_fields={"status": "SUCCEEDED"}, markdown_body="x"
        )
        payload = json_path.read_text(encoding="utf-8").replace('"FINAL"', '"PROVISIONAL"')
        json_path.write_text(payload, encoding="utf-8")
        result = read_committed_pair(json_path, markdown_path)
        assert result.verdict is PairVerdict.NON_AUTHORITATIVE
        assert result.reason == "commit_state is not FINAL"

    def test_run_id_mismatch_is_non_authoritative(self, tmp_path: Path) -> None:
        writer, _fs, json_path, markdown_path = TestEvidenceCommitProtocol()._writer(tmp_path)
        writer.commit(
            run_id="run-a", evidence_id="ev", json_fields={"status": "SUCCEEDED"}, markdown_body="x"
        )
        payload = json_path.read_text(encoding="utf-8").replace('"run-a"', '"run-b"')
        json_path.write_text(payload, encoding="utf-8")
        result = read_committed_pair(json_path, markdown_path)
        assert result.verdict is PairVerdict.NON_AUTHORITATIVE
        assert result.reason == "run_id mismatch"

    def test_hash_mismatch_is_non_authoritative(self, tmp_path: Path) -> None:
        writer, _fs, json_path, markdown_path = TestEvidenceCommitProtocol()._writer(tmp_path)
        writer.commit(
            run_id="run", evidence_id="ev", json_fields={"status": "SUCCEEDED"}, markdown_body="x"
        )
        markdown_path.write_text(
            markdown_path.read_text(encoding="utf-8") + "tampered", encoding="utf-8"
        )
        result = read_committed_pair(json_path, markdown_path)
        assert result.verdict is PairVerdict.NON_AUTHORITATIVE
        assert result.reason == "companion_markdown_sha256 mismatch"

    def test_markdown_never_needs_to_carry_a_json_hash(self, tmp_path: Path) -> None:
        writer, _fs, json_path, markdown_path = TestEvidenceCommitProtocol()._writer(tmp_path)
        writer.commit(
            run_id="run", evidence_id="ev", json_fields={"status": "SUCCEEDED"}, markdown_body="x"
        )
        markdown_text = markdown_path.read_text(encoding="utf-8")
        assert "companion" not in markdown_text
        assert "sha256" not in markdown_text.lower()


# ------------------------------------------------------------------------------------------
# No live execution guard
# ------------------------------------------------------------------------------------------


def test_module_never_imports_a_live_execution_dependency() -> None:
    import sketch2life.benchmark.feat018_live_lightning_execution as module

    forbidden = ("torch", "transformers", "accelerate", "requests", "httpx")
    for name in forbidden:
        assert name not in module.__dict__


class TestD11LowlevelCleanupDeadlineRegression:
    @pytest.mark.parametrize('late_step', ['empty_query', 'ipc_close'])
    def test_late_local_cleanup_proof_or_release_cannot_restore_supervisor_success(
        self, late_step: str
    ) -> None:
        clock = FakeClock()
        intents: list[float] = []

        class _DelayedContainment(FakeContainmentBackend):
            def is_empty(self) -> bool:
                if late_step == 'empty_query':
                    clock.advance(0.3)
                return True

        class _DelayedConnection(FakeBoundedConnection):
            def close(self) -> None:
                if late_step == 'ipc_close':
                    clock.advance(0.3)
                super().close()

        def cleanup_intent() -> float:
            intents.append(clock())
            return 0.2

        containment = _DelayedContainment()
        launcher = _launcher(clock)
        launcher.connection = _DelayedConnection(clock=clock)
        launcher.connection.push({'seq': 1, 'kind': 'ADAPTER_STARTED'})
        launcher.connection.push(
            {'seq': 2, 'kind': 'GENERATION_ATTEMPT_STARTED', 'attempt_number': 1}
        )
        _push_success_d9_frames(launcher.connection)
        launcher.connection.push({'seq': 3, 'kind': 'TERMINAL', 'outcome': 'SUCCEEDED'})
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(), launcher=launcher, containment_factory=lambda: containment,
            clock=clock, sleep=clock.advance,
            on_cleanup_intent=cleanup_intent, cleanup_deadline=lambda: 0.2,
        )

        result = supervisor.run(_no_op_entry, ())

        assert intents == [0.0]
        assert result.terminal_outcome == 'SUCCEEDED'
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.cleanup_failure is not None
        assert launcher.handle.closed and launcher.connection.closed
        assert containment.close_calls == 1  # safe release remains permitted after expiry
        assert result.cleanup_failure.retry_cleanup(
            grace_seconds=0.1, kill_join_seconds=0.1,
            cleanup_deadline_monotonic=clock() + 1.0, clock=clock,
        )
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert intents == [0.0]

    def test_transient_retirement_uses_work_cap_then_timeout_opens_one_cleanup_window(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as execution

        clock = FakeClock()
        intents: list[float] = []
        grants: list[float] = []
        handles: list[FakeProcessHandle] = []
        join_limits: list[float | None] = []
        receive_limits: list[float] = []

        class _AdvancingProcess(FakeProcessHandle):
            def join(self, timeout: float | None = None) -> None:
                join_limits.append(timeout)
                clock.advance(min(0.2, timeout or 0.0))
                super().join(timeout)

        class _TransientConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                if timeout <= 0:
                    return None
                receive_limits.append(timeout)
                clock.advance(90.0)
                return {'kind': 'provider_failure'}

        class _TimeoutConnection(FakeBoundedConnection):
            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                if timeout > 0:
                    receive_limits.append(timeout)
                return super().recv_frame(timeout)

        class _RetryLauncher:
            def launch(
                self, entry: Callable[..., None], args: tuple[object, ...]
            ) -> tuple[ProcessHandle, BoundedConnection]:
                del entry, args
                handle = _AdvancingProcess(started_at_monotonic=clock())
                handles.append(handle)
                return handle, (
                    _TransientConnection(clock=clock)
                    if len(handles) == 1 else _TimeoutConnection(clock=clock)
                )

        def transient_result(frame: Mapping[str, object]) -> str:
            assert frame.get('kind') == 'provider_failure'
            raise QwenTransientRuntimeError

        def cleanup_intent() -> float:
            intents.append(clock())
            grants.append(clock() + 1.0)
            return grants[0]

        monkeypatch.setattr(execution, '_interpret_generation_child_frame', transient_result)
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=_config(total_adapter_cap_seconds=150.0),
            worker_cap_deadline_monotonic=150.0,
            launcher=_RetryLauncher(), clock=clock,
            on_cleanup_intent=cleanup_intent,
            cleanup_deadline=lambda: grants[0] if grants else None,
        )

        with pytest.raises(QwenTransientRuntimeError):
            runner.generate(cast(object, None), cast(object, None), Path('x.png'), 'prompt')
        assert intents == [] and grants == []
        assert clock() == pytest.approx(90.4)
        assert runner.cleanup_failure is None

        with pytest.raises(QwenTimeoutError):
            runner.generate(cast(object, None), cast(object, None), Path('x.png'), 'prompt')

        assert intents == [150.0]
        assert grants == [151.0]
        assert receive_limits == pytest.approx([120.0, 59.6])
        assert join_limits == pytest.approx([1.0, 1.0, 1.0, 0.8])
        assert clock() == pytest.approx(150.4)
        assert runner.worker_cap_deadline_monotonic == 150.0
        assert runner.cleanup_failure is None
        assert len(handles) == 2 and all(handle.closed for handle in handles)


# D11 fixtures deliberately keep allocation state outside the replaceable SDK worker. A dead
# worker therefore cannot erase an allocation or manufacture an empty reconciliation result.
from sketch2life.benchmark.feat018_live_lightning_execution import (  # noqa: E402
    D11CleanupGrant,
    D11CleanupReport,
    D11CleanupWindow,
    D11OfflineConfig,
    D11OperationContext,
    D11OperationKind,
    D11OperationReceipt,
    D11ResourceObservation,
    LightningOperationRefV1,
    LightningProvisionRefV1,
    LightningSessionRefV1,
    run_offline_live_smoke as run_d11_smoke,
    run_live_smoke as run_unbound_live_smoke,
    _invoke_d11_operation,
    _d11_result_from_payload,
    _d11_result_payload,
    _is_live_attempt_profile_admissible,
)


@dataclass(slots=True)
class _D11AllocationState:
    lock: Any
    provision_token: Any
    resource_identity: Any
    dispatch_token: Any
    operation_journal: Any
    alive: Any
    sealed: Any
    meter_started: Any
    counts: Any
    grant_deadlines: Any
    grant_generations: Any
    grant_count: Any
    close_count: Any

    def text(self, storage: Any) -> str:
        return storage.value.decode("ascii")

    def count(self, kind: D11OperationKind) -> int:
        return self.counts[list(D11OperationKind).index(kind)]

    def retain_operation(self, operation: LightningOperationRefV1, context: D11OperationContext) -> None:
        with self.lock:
            self.counts[list(D11OperationKind).index(operation.kind)] += 1
            journal = self.text(self.operation_journal)
            entry = f"{operation.kind.value}:{operation.token}:{operation.recovery_of or '-'};"
            self.operation_journal.value = (journal + entry).encode("ascii")
            if context.cleanup_grant is not None:
                index = self.grant_count.value
                self.grant_deadlines[index] = context.cleanup_grant.deadline_host_monotonic
                self.grant_generations[index] = context.cleanup_grant.generation
                self.grant_count.value += 1


def _d11_allocation_state() -> _D11AllocationState:
    context = multiprocessing.get_context("spawn")
    return _D11AllocationState(
        lock=context.RLock(),
        provision_token=context.Array("c", 80),
        resource_identity=context.Array("c", 80),
        dispatch_token=context.Array("c", 80),
        operation_journal=context.Array("c", 8192),
        alive=context.Value("b", False),
        sealed=context.Value("b", False),
        meter_started=context.Value("d", 0.0),
        counts=context.Array("i", len(D11OperationKind)),
        grant_deadlines=context.Array("d", 64),
        grant_generations=context.Array("i", 64),
        grant_count=context.Value("i", 0),
        close_count=context.Value("i", 0),
    )


@dataclass(slots=True)
class _D11SyntheticHandle:
    state: _D11AllocationState
    operation: LightningOperationRefV1
    context: D11OperationContext
    behavior: str = "success"
    cleanup_step_seconds: float = 0.0
    observer_identity: str = "fixture-independent-probe"

    def _session(self) -> LightningSessionRefV1 | None:
        identity = self.state.text(self.state.resource_identity)
        return LightningSessionRefV1(self.operation.provision, identity) if identity else None

    def _receipt(self, facts: object = None) -> D11OperationReceipt:
        operation = self.operation
        session = self._session()
        if self.behavior == "wrong_token" and operation.kind is D11OperationKind.PROVISION:
            foreign = LightningProvisionRefV1(operation.provision.run_id, "foreign-token")
            operation = LightningOperationRefV1(foreign, operation.token, operation.kind)
            session = LightningSessionRefV1(foreign, session.resource_identity) if session else None
        if self.behavior == "wrong_session" and operation.kind is D11OperationKind.WAIT_READY:
            session = LightningSessionRefV1(operation.provision, "another-session")
        if self.behavior == "foreign_session_ref" and operation.kind is D11OperationKind.PROVISION:
            foreign = LightningProvisionRefV1(operation.provision.run_id, "foreign-session-provision")
            session = LightningSessionRefV1(foreign, session.resource_identity) if session else None
        return D11OperationReceipt(operation, session, facts)

    @staticmethod
    def _hang() -> None:
        while True:
            time.sleep(0.02)

    def wait(self, *, timeout_seconds: float, emit: Callable[[Mapping[str, object]], object]) -> object:
        kind = self.operation.kind
        if kind is D11OperationKind.PROVISION:
            if self.behavior == "provision_cleanup_intent":
                emit({"kind": "cleanup_intent"})
            placement = FakeLightningSessionController(FakeClock()).placement
            if self.behavior == "invalid_placement":
                placement = replace(placement, gpu_sku="NVIDIA_A10")
            return self._receipt(LightningProvisionFacts(
                allocation_confirmed=True,
                gpu_minute_budget_start_monotonic=self.state.meter_started.value,
                session_identity=self.state.text(self.state.resource_identity),
                placement=placement,
            ))
        if kind is D11OperationKind.WAIT_READY:
            if self.behavior == "ready_cleanup_intent":
                emit({"kind": "cleanup_intent"})
            assert self.operation.session is not None
            assert self.operation.session.resource_identity == self.state.text(self.state.resource_identity)
            now = time.monotonic()
            return self._receipt(LightningReadyFacts(
                readiness=LightningSessionReadiness.SESSION_READY,
                lifecycle=LightningSessionLifecycleFacts(
                    self.operation.session.resource_identity, now, now, now + 30.0,
                ),
            ))
        if kind is D11OperationKind.DISPATCH:
            if self.behavior == "hang_without_progress":
                self._hang()
            if self.behavior == "progress_after_cleanup_intent":
                emit({"kind": "progress", "event": {"seq": 1, "kind": "ADAPTER_STARTED"}})
                emit({"kind": "cleanup_intent"})
                emit({"kind": "progress", "event": {
                    "seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1,
                }})
                return self._receipt(_successful_supervisor_result())
            if self.behavior != "success_without_progress":
                emit({"kind": "progress", "event": {"seq": 1, "kind": "ADAPTER_STARTED"}})
                emit({"kind": "progress", "event": {
                    "seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1,
                }})
            if self.behavior == "hang_after_generation":
                self._hang()
            if self.behavior != "success_without_progress":
                emit({"kind": "progress", "event": {
                    "seq": 3, "kind": "TERMINAL", "outcome": "SUCCEEDED", "raw_status": "SUCCEEDED",
                }})
            if self.behavior == "missing_cleanup_handoff":
                with self.state.lock:
                    self.state.dispatch_token.value = b""
                return self._receipt(_successful_supervisor_result())
            first_grant = emit({"kind": "cleanup_intent"})
            second_grant = emit({"kind": "cleanup_intent"})
            assert isinstance(first_grant, D11CleanupGrant)
            assert isinstance(second_grant, D11CleanupGrant)
            assert first_grant.deadline_host_monotonic == second_grant.deadline_host_monotonic
            assert first_grant.cancellation_operation == second_grant.cancellation_operation
            assert first_grant.cancellation_operation is not None
            assert first_grant.cancellation_operation.recovery_of == self.operation.token
            with self.state.lock:
                self.state.dispatch_token.value = b""
            facts = _successful_supervisor_result()
            if self.behavior == "contradictory_cardinality":
                facts = replace(facts, attempt_count=2)
            return self._receipt(facts)
        if self.cleanup_step_seconds:
            time.sleep(self.cleanup_step_seconds)
        if kind is D11OperationKind.CANCEL:
            assert self.operation.recovery_of is not None
            if self.behavior == "cancel_hang":
                self._hang()
            if self.behavior != "pending_provision_claims_only":
                with self.state.lock:
                    self.state.dispatch_token.value = b""
                    self.state.sealed.value = True
            return self._receipt(LightningCancellationFacts(cancellation_verified=True))
        if kind is D11OperationKind.RECONCILE:
            return self._receipt()
        if kind is D11OperationKind.TERMINATE:
            if self.operation.session is not None:
                assert self.operation.session.resource_identity == self.state.text(self.state.resource_identity)
            if self.behavior not in ("claims_only", "pending_provision_claims_only"):
                with self.state.lock:
                    self.state.alive.value = False
                    self.state.sealed.value = True
                    self.state.dispatch_token.value = b""
            identity = self.state.text(self.state.resource_identity)
            if not identity:
                return self._receipt()
            return self._receipt(LightningTerminationFacts(
                termination_verified=True, cleanup_status=CleanupStatus.SUCCEEDED,
                session_identity=identity, session_cleanup_verified=True,
            ))
        if kind is D11OperationKind.OBSERVE:
            with self.state.lock:
                session = self.state.text(self.state.resource_identity)
                dispatch = self.state.text(self.state.dispatch_token)
                provision = self.operation.provision
                resources = ((session, "active" if self.state.alive.value else "terminated"),) if session else ()
                active_operations = (dispatch,) if dispatch else ()
                observed_at = time.monotonic()
                if self.behavior == "observation_missing_session":
                    resources = (("other-terminated-resource", "terminated"),)
                elif self.behavior == "observation_stale_timestamp":
                    observed_at = max(0.0, observed_at - 10.0)
                elif self.behavior == "observation_future_timestamp":
                    observed_at += 3_600.0
                elif self.behavior == "observation_foreign_provision":
                    provision = LightningProvisionRefV1(provision.run_id, "foreign-provision")
                elif self.behavior == "observation_active_operations":
                    active_operations = ("still-active-operation",)
                return D11ResourceObservation(
                    provision=provision,
                    request_state="sealed" if self.state.sealed.value else "pending",
                    resources=resources,
                    active_operations=active_operations,
                    observed_at_host_monotonic=observed_at,
                    source_identity=self.observer_identity,
                )
        raise AssertionError("unexpected fixture operation")

    def cancel(self, *, operation: LightningOperationRefV1, timeout_seconds: float) -> D11OperationReceipt:
        assert operation.kind is D11OperationKind.CANCEL
        assert operation.recovery_of == self.operation.token
        if self.behavior == "cancel_hang":
            self._hang()
        with self.state.lock:
            self.state.dispatch_token.value = b""
            self.state.sealed.value = True
        return D11OperationReceipt(operation, self._session(), LightningCancellationFacts(True))

    def close(self) -> None:
        with self.state.lock:
            self.state.close_count.value += 1
        if self.behavior == "dispatch_close_failure" and self.operation.kind is D11OperationKind.DISPATCH:
            raise OSError("synthetic SDK handle close failed")


@dataclass(slots=True)
class _D11SyntheticController:
    state: _D11AllocationState
    behavior: str = "success"
    cleanup_step_seconds: float = 0.0

    def _start(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
               inputs: object = None) -> _D11SyntheticHandle:
        self.state.retain_operation(operation, context)
        if operation.kind is D11OperationKind.PROVISION:
            with self.state.lock:
                assert not self.state.text(self.state.provision_token), "duplicate provision was attempted"
                self.state.provision_token.value = operation.provision.token.encode("ascii")
                if self.behavior not in ("pending_provision_response", "pending_provision_claims_only"):
                    self.state.resource_identity.value = f"fixture-session-{os.getpid()}".encode("ascii")
                    self.state.alive.value = True
                    self.state.meter_started.value = time.monotonic()
            if self.behavior in ("lost_provision_response", "pending_provision_response", "pending_provision_claims_only"):
                os._exit(17)
        else:
            assert operation.provision.token == self.state.text(self.state.provision_token)
        return _D11SyntheticHandle(self.state, operation, context, self.behavior, self.cleanup_step_seconds)

    provision = _start
    wait_ready = _start
    cancel = _start
    reconcile = _start
    terminate = _start


@dataclass(slots=True)
class _D11SyntheticDispatch:
    state: _D11AllocationState
    behavior: str = "success"

    def start(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
              inputs: object = None) -> _D11SyntheticHandle:
        self.state.retain_operation(operation, context)
        assert operation.kind is D11OperationKind.DISPATCH
        assert operation.provision.token == self.state.text(self.state.provision_token)
        assert operation.session is not None
        assert operation.session.resource_identity == self.state.text(self.state.resource_identity)
        with self.state.lock:
            assert not self.state.text(self.state.dispatch_token), "duplicate dispatch was attempted"
            self.state.dispatch_token.value = operation.token.encode("ascii")
        if self.behavior == "start_hang":
            _D11SyntheticHandle._hang()
        return _D11SyntheticHandle(self.state, operation, context, self.behavior)


@dataclass(slots=True)
class _D11SyntheticObserver:
    state: _D11AllocationState
    identity: str = "fixture-independent-probe"
    behavior: str = "success"

    def observe(self, *, operation: LightningOperationRefV1, context: D11OperationContext,
                inputs: object = None) -> _D11SyntheticHandle:
        self.state.retain_operation(operation, context)
        assert operation.kind is D11OperationKind.OBSERVE
        return _D11SyntheticHandle(
            self.state, operation, context, self.behavior, observer_identity=self.identity
        )


def _run_d11_fixture(
    *, controller_behavior: str = "success", dispatch_behavior: str = "success",
    cleanup_total_seconds: float = 6.0, cleanup_step_seconds: float = 0.0,
    observer_identity: str = "fixture-independent-probe",
    observer_behavior: str = "success",
) -> tuple[Feat018LiveSmokeResult, _D11AllocationState, FakeLiveSmokeFinalizer]:
    state = _d11_allocation_state()
    finalizer = FakeLiveSmokeFinalizer()
    result = run_d11_smoke(
        _request("fixture.bin", "a" * 64),
        QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir")),
        _policy(), "fixture prompt",
        controller=_D11SyntheticController(state, controller_behavior, cleanup_step_seconds),
        config=_live_smoke_config(
            session_provision_timeout_seconds=3,
            session_termination_deadline_seconds=2,
            bounded_runner_config=_config(total_adapter_cap_seconds=1.5,
                                          containment_setup_timeout_seconds=1.0),
        ),
        session_id="synthetic-session",
        preflight=FakeLightningPreflight(), finalizer=finalizer,
        adapter_dispatch=_D11SyntheticDispatch(state, dispatch_behavior),
        observer=_D11SyntheticObserver(state, observer_identity, observer_behavior),
        d11_config=D11OfflineConfig(cleanup_total_seconds, 1.0, 0.02, "fixture-independent-probe"),
    )
    return result, state, finalizer


class TestD11CleanupWindow:
    def test_receipt_cannot_bind_foreign_session_to_correct_operation(self) -> None:
        provision = LightningProvisionRefV1("run", "provision-token")
        operation = LightningOperationRefV1(provision, "operation-token", D11OperationKind.PROVISION)
        foreign = LightningSessionRefV1(LightningProvisionRefV1("run", "another-provision"), "session")
        with pytest.raises(ValueError):
            D11OperationReceipt(operation, foreign)

    def test_repeated_intents_and_fresh_grants_preserve_original_deadline(self) -> None:
        clock = FakeClock(10.0)
        window = D11CleanupWindow("run", 5.0, 1.0, clock)
        original = window.grant()
        clock.advance(0.75)
        refreshed = window.grant()
        assert window.begin("second_intent") == 15.0
        assert original.deadline_host_monotonic == refreshed.deadline_host_monotonic == 15.0
        assert original.generation == refreshed.generation == 1
        assert window.validate_grant(refreshed)

    def test_delayed_wrong_generation_and_extended_grants_are_rejected(self) -> None:
        clock = FakeClock(10.0)
        window = D11CleanupWindow("run", 5.0, 1.0, clock)
        grant = window.grant()
        assert not window.validate_grant(replace(grant, generation=2))
        assert not window.validate_grant(replace(grant, deadline_host_monotonic=16.0))
        assert not window.validate_grant(replace(grant, issued_at_host_monotonic=10.1))
        clock.advance(1.001)
        assert not window.validate_grant(grant)
        assert window.begin("delayed_intent") == 15.0
        clock.set(15.0)
        assert not window.validate_grant(window.grant())

    @pytest.mark.parametrize("parameter", [0.0, -1.0, float("nan"), float("inf"), True])
    def test_live_cleanup_budget_is_not_invented(self, parameter: object) -> None:
        with pytest.raises(ValueError):
            D11OfflineConfig(parameter, 1.0, 0.02, "fixture-independent-probe")


class TestD11SyntheticCoordinator:
    @staticmethod
    def _pre_adapter_terminal() -> Feat018LiveSmokeResult:
        provision = LightningProvisionRefV1("run", "provision-token")
        operation = LightningOperationRefV1(provision, "operation-token", D11OperationKind.PROVISION)
        observation = D11ResourceObservation(
            provision, "sealed", (("fixture-session", "terminated"),), (), 11.0,
            "fixture-independent-probe",
        )
        report = D11CleanupReport(
            deadline_host_monotonic=20.0, generation=1, operations=(operation,),
            unresolved_operations=(), observation=observation, verification="VERIFIED_OFFLINE",
            failure_codes=(), dispatch_invocation_accepted=False, generation_progress_known=False,
        )
        return Feat018LiveSmokeResult(
            effective_outcome=EffectiveOutcome.FAILED, adapter_call_count=0, attempt_count=None,
            cleanup_status=CleanupStatus.SUCCEEDED, failure_code=Feat018LiveSmokeFailureCode.PROVISION_FAILED,
            preflight_verified=True, d11_report=report,
        )

    def test_verified_pre_adapter_terminal_publishes_zero_unknown_without_fake_supervisor(self, tmp_path: Path) -> None:
        terminal = self._pre_adapter_terminal()
        inventory = Feat018ArtifactInventory((tmp_path,), max_entries=20)
        inventory.capture()
        writer = Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
        result = finalize_smoke_run(
            terminal, run_id="run", evidence_id="ev", inventory=inventory,
            cleanup=lambda: CleanupStatus.SUCCEEDED, writer=writer,
            incident=Feat018IncidentWriter(
                Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"),
                repository_root=tmp_path, git_ignored=True,
            ),
        )
        assert terminal.adapter_result is None
        assert result.evidence.committed
        payload = json.loads(writer.json_path.read_bytes())
        assert payload["status"] == "FAILED"
        assert payload["terminal_kind"] == "PRE_ADAPTER"
        assert payload["adapter_call_count"] == 0 and payload["attempt_count"] is None
        assert payload["generation_progress"] == "UNKNOWN"
        assert payload["cleanup_verification"] == "VERIFIED_OFFLINE"
        assert "provision-token" not in writer.json_path.read_text(encoding="utf-8")
        assert "operation-token" not in writer.markdown_path.read_text(encoding="utf-8")

    @pytest.mark.parametrize("mode", [
        "missing_report", "unverified_report", "verified_label_only", "retained_owner", "cleanup_failed",
    ])
    def test_pre_adapter_finalization_rejects_missing_release_proof_or_retained_owner(self, tmp_path: Path,
                                                                                    mode: str) -> None:
        terminal = self._pre_adapter_terminal()
        assert terminal.d11_report is not None
        if mode == "missing_report":
            terminal = replace(terminal, d11_report=None)
        elif mode == "unverified_report":
            terminal = replace(terminal, d11_report=replace(terminal.d11_report, verification="UNVERIFIED"))
        elif mode == "verified_label_only":
            terminal = replace(terminal, d11_report=replace(terminal.d11_report, observation=None))
        elif mode == "retained_owner":
            terminal = replace(terminal, cleanup_failures=(Feat018CleanupFailedError(
                owned_process=FakeProcessHandle(),
            ),))
        else:
            terminal = replace(terminal, cleanup_status=CleanupStatus.CLEANUP_FAILED,
                               effective_outcome=EffectiveOutcome.CLEANUP_FAILED)
        inventory = Feat018ArtifactInventory((tmp_path,), max_entries=20)
        inventory.capture()
        writer = Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
        result = finalize_smoke_run(
            terminal, run_id="run", evidence_id="ev", inventory=inventory,
            cleanup=lambda: CleanupStatus.SUCCEEDED, writer=writer,
            incident=Feat018IncidentWriter(
                Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"),
                repository_root=tmp_path, git_ignored=True,
            ),
        )
        assert not result.evidence.committed
        assert not writer.json_path.exists()

    @pytest.mark.parametrize("behavior, ready_count", [
        ("provision_cleanup_intent", 0), ("ready_cleanup_intent", 1),
    ])
    def test_early_cleanup_intent_prevents_any_next_ordinary_phase(self, behavior: str, ready_count: int) -> None:
        result, state, _ = _run_d11_fixture(controller_behavior=behavior)
        assert result.effective_outcome is not EffectiveOutcome.SUCCEEDED
        assert result.adapter_call_count == 0 and result.attempt_count is None
        assert state.count(D11OperationKind.PROVISION) == 1
        assert state.count(D11OperationKind.WAIT_READY) == ready_count
        assert state.count(D11OperationKind.DISPATCH) == 0
        assert not state.alive.value
        report = result.d11_report
        assert report is not None
        deadlines = tuple(state.grant_deadlines[:state.grant_count.value])
        assert deadlines and set(deadlines) == {report.deadline_host_monotonic}

    def test_repeated_cleanup_intents_keep_one_parent_cancel_reference(self) -> None:
        result, state, _ = _run_d11_fixture()
        assert result.is_success and state.count(D11OperationKind.DISPATCH) == 1
        report = result.d11_report
        assert report is not None
        dispatch = next(item for item in report.operations if item.kind is D11OperationKind.DISPATCH)
        cancellations = [item for item in report.operations
                         if item.kind is D11OperationKind.CANCEL and item.recovery_of == dispatch.token]
        assert len(cancellations) == 1
        deadlines = tuple(state.grant_deadlines[:state.grant_count.value])
        assert deadlines and set(deadlines) == {report.deadline_host_monotonic}

    def test_dispatch_summary_without_cleanup_handoff_is_rejected(self) -> None:
        result, state, _ = _run_d11_fixture(dispatch_behavior="missing_cleanup_handoff")
        assert result.effective_outcome is not EffectiveOutcome.SUCCEEDED
        assert result.adapter_call_count == 1 and result.attempt_count == 1
        assert state.count(D11OperationKind.DISPATCH) == 1
        assert not state.alive.value

    def test_late_generation_progress_after_cleanup_intent_does_not_fill_unknown_count(self) -> None:
        result, state, _ = _run_d11_fixture(dispatch_behavior="progress_after_cleanup_intent")
        assert result.effective_outcome is not EffectiveOutcome.SUCCEEDED
        assert result.adapter_call_count == 1 and result.attempt_count is None
        assert state.count(D11OperationKind.DISPATCH) == 1
        assert result.d11_report is not None and not result.d11_report.generation_progress_known

    def test_explicit_session_and_parent_operation_references_survive_fresh_workers(self) -> None:
        result, state, finalizer = _run_d11_fixture()
        assert result.is_success
        assert result.adapter_call_count == 1 and result.attempt_count == 1
        assert result.session_identity == state.text(state.resource_identity)
        assert result.session_identity.startswith("fixture-session-")
        assert state.count(D11OperationKind.PROVISION) == state.count(D11OperationKind.DISPATCH) == 1
        assert not state.alive.value and state.sealed.value and not state.text(state.dispatch_token)
        report = result.d11_report
        assert report is not None and report.verification == "VERIFIED_OFFLINE"
        assert report.dispatch_invocation_accepted and report.generation_progress_known
        assert not report.unresolved_operations
        journal = state.text(state.operation_journal)
        retained_tokens = {operation.token for operation in report.operations}
        executed_tokens = {entry.split(":")[1] for entry in journal.split(";") if entry}
        assert executed_tokens <= retained_tokens
        assert len(retained_tokens) == len(report.operations)
        assert finalizer.calls[0].d11_report is report

    def test_allocation_survives_lost_provision_response_and_is_reconciled_without_duplicate(self) -> None:
        result, state, finalizer = _run_d11_fixture(controller_behavior="lost_provision_response")
        assert result.effective_outcome is not EffectiveOutcome.SUCCEEDED
        assert result.adapter_call_count == 0 and result.attempt_count is None
        assert state.count(D11OperationKind.PROVISION) == 1
        assert state.count(D11OperationKind.DISPATCH) == 0
        assert state.meter_started.value > 0 and state.text(state.resource_identity)
        assert state.count(D11OperationKind.RECONCILE) >= 1
        assert state.count(D11OperationKind.TERMINATE) >= 1
        assert not state.alive.value and state.sealed.value
        report = result.d11_report
        assert report is not None
        assert report.observation is not None and report.observation.resources
        assert report.observation.resources[0][1] == "terminated"
        assert finalizer.calls and finalizer.calls[0].adapter_result is None

    @pytest.mark.parametrize("behavior, sealed", [
        ("pending_provision_response", True), ("pending_provision_claims_only", False),
    ])
    def test_empty_lookup_requires_sealing_the_pending_provision_request(self, behavior: str, sealed: bool) -> None:
        result, state, _ = _run_d11_fixture(controller_behavior=behavior)
        assert state.count(D11OperationKind.PROVISION) == 1
        assert state.count(D11OperationKind.DISPATCH) == 0
        assert not state.alive.value and not state.text(state.resource_identity)
        assert bool(state.sealed.value) is sealed
        report = result.d11_report
        assert report is not None and report.observation is not None
        assert report.observation.resources == ()
        if not sealed:
            assert report.observation.request_state == "pending"
            assert report.verification != "VERIFIED_OFFLINE"
            assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        else:
            assert report.observation.request_state == "sealed"
            assert report.verification == "VERIFIED_OFFLINE"

    def test_rejected_placement_retains_the_allocated_session_for_cleanup(self) -> None:
        result, state, _ = _run_d11_fixture(controller_behavior="invalid_placement")
        assert result.adapter_call_count == 0 and result.attempt_count is None
        assert result.effective_outcome is not EffectiveOutcome.SUCCEEDED
        assert not state.alive.value
        report = result.d11_report
        assert report is not None
        termination = next(item for item in report.operations if item.kind is D11OperationKind.TERMINATE)
        assert termination.session is not None
        assert termination.session.resource_identity == state.text(state.resource_identity)

    @pytest.mark.parametrize("behavior, attempts", [
        ("start_hang", None), ("hang_without_progress", None), ("hang_after_generation", 1),
    ])
    def test_dispatch_hang_returns_control_and_recovers_known_operation(self, behavior: str,
                                                                     attempts: int | None) -> None:
        started = time.monotonic()
        result, state, _ = _run_d11_fixture(dispatch_behavior=behavior)
        assert time.monotonic() - started < 15.0
        assert result.effective_outcome is not EffectiveOutcome.SUCCEEDED
        assert result.adapter_call_count == 1 and result.attempt_count == attempts
        assert state.count(D11OperationKind.DISPATCH) == 1
        assert not state.alive.value and not state.text(state.dispatch_token)
        report = result.d11_report
        assert report is not None and report.dispatch_invocation_accepted
        assert report.generation_progress_known is (attempts is not None)
        dispatch = next(item for item in report.operations if item.kind is D11OperationKind.DISPATCH)
        assert any(item.kind is D11OperationKind.CANCEL and item.recovery_of == dispatch.token
                   for item in report.operations)

    @pytest.mark.parametrize("behavior", ["wrong_token", "wrong_session", "foreign_session_ref"])
    def test_foreign_receipts_do_not_replace_the_parent_recovery_target(self, behavior: str) -> None:
        result, state, _ = _run_d11_fixture(controller_behavior=behavior)
        assert result.effective_outcome is not EffectiveOutcome.SUCCEEDED
        assert result.adapter_call_count == 0 and result.attempt_count is None
        assert not state.alive.value
        report = result.d11_report
        assert report is not None
        assert all(item.provision.token == state.text(state.provision_token) for item in report.operations)
        assert all(item.session is None or item.session.resource_identity != "another-session"
                   for item in report.operations)

    def test_success_receipt_without_progress_does_not_prove_generation_cardinality(self) -> None:
        result, state, _ = _run_d11_fixture(dispatch_behavior="success_without_progress")
        assert result.adapter_call_count == 1 and result.attempt_count is None
        assert result.effective_outcome is not EffectiveOutcome.SUCCEEDED
        assert state.count(D11OperationKind.DISPATCH) == 1
        assert result.d11_report is not None and not result.d11_report.generation_progress_known

    def test_terminal_receipt_cannot_override_accepted_attempt_count(self) -> None:
        result, _, _ = _run_d11_fixture(dispatch_behavior="contradictory_cardinality")
        assert result.attempt_count == 1
        assert result.effective_outcome is not EffectiveOutcome.SUCCEEDED

    def test_producer_cleanup_booleans_do_not_overrule_independent_allocation_state(self) -> None:
        result, state, finalizer = _run_d11_fixture(controller_behavior="claims_only")
        assert state.alive.value
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        report = result.d11_report
        assert report is not None and report.verification != "VERIFIED_OFFLINE"
        assert report.observation is not None and report.observation.resources[0][1] == "active"
        assert report.unresolved_operations
        assert finalizer.calls[0].cleanup_status is CleanupStatus.CLEANUP_FAILED

    def test_unbound_observer_identity_cannot_verify_remote_cleanup(self) -> None:
        result, state, _ = _run_d11_fixture(observer_identity="unbound-observer")
        assert not state.alive.value
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.d11_report is not None and result.d11_report.verification != "VERIFIED_OFFLINE"

    def test_sdk_close_failure_reaches_finalizer_and_retains_recovery_reference(self) -> None:
        result, state, finalizer = _run_d11_fixture(dispatch_behavior="dispatch_close_failure")
        assert state.close_count.value > 0
        assert not state.alive.value
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
        assert result.d11_report is not None and result.d11_report.failure_codes
        assert finalizer.calls[0].cleanup_status is CleanupStatus.CLEANUP_FAILED
        assert any(item.kind is D11OperationKind.DISPATCH for item in result.d11_report.operations)

    def test_cancel_hang_uses_cleanup_deadline_and_cannot_create_another_window(self) -> None:
        started = time.monotonic()
        result, state, _ = _run_d11_fixture(
            controller_behavior="cancel_hang", dispatch_behavior="hang_without_progress",
            cleanup_total_seconds=2.0,
        )
        assert time.monotonic() - started < 10.0
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        report = result.d11_report
        assert report is not None and report.unresolved_operations
        deadlines = tuple(state.grant_deadlines[:state.grant_count.value])
        assert deadlines and all(value == report.deadline_host_monotonic for value in deadlines)

    def test_cleanup_steps_share_one_absolute_deadline_even_after_timeout(self) -> None:
        started = time.monotonic()
        result, state, _ = _run_d11_fixture(cleanup_total_seconds=1.0, cleanup_step_seconds=0.6)
        assert time.monotonic() - started < 10.0
        assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
        report = result.d11_report
        assert report is not None and report.unresolved_operations
        deadlines = tuple(state.grant_deadlines[:state.grant_count.value])
        generations = tuple(state.grant_generations[:state.grant_count.value])
        assert deadlines and set(deadlines) == {report.deadline_host_monotonic}
        assert set(generations) == {report.generation}


class TestLiveBindingAndAttemptProfile:
    def test_exact_plan_attempt_bound_is_admissible_only_for_the_live_profile(self) -> None:
        assert _is_live_attempt_profile_admissible(_config(per_attempt_timeout_seconds=120.0))
        assert not _is_live_attempt_profile_admissible(
            _config(per_attempt_timeout_seconds=119.999)
        )
        with pytest.raises(ValueError):
            _config(per_attempt_timeout_seconds=120.001)
        for invalid in (float("nan"), float("inf"), 0.0, -1.0, True):
            with pytest.raises(ValueError):
                _config(per_attempt_timeout_seconds=invalid)

    def test_production_entry_admits_only_exact_120_seconds_before_launch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as module

        events: list[object] = []
        expected = _successful_supervisor_result()

        class FakeLauncher:
            def __init__(self, *, max_envelope_bytes: int) -> None:
                events.append(("launcher", max_envelope_bytes))

        class FakeSupervisor:
            def __init__(self, *, config: object, launcher: object,
                         containment_factory: Callable[[], object]) -> None:
                events.append(("supervisor", config, launcher, containment_factory))

            def run(self, entry: Callable[..., None], args: tuple[object, ...]) -> object:
                events.append(("run", entry, args))
                return expected

        monkeypatch.setattr(module, "MultiprocessingProcessLauncher", FakeLauncher)
        monkeypatch.setattr(module, "Feat018AdapterCallSupervisor", FakeSupervisor)
        request = _request("fixture.bin", "a" * 64)
        runtime = QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir"))
        policy = _policy()

        rejected = run_bounded_adapter_call(
            request, runtime, policy, "fixture prompt",
            _config(per_attempt_timeout_seconds=119.999),
        )

        assert rejected.final_state is ProgressState.NOT_STARTED
        assert rejected.attempt_count is None and rejected.terminal_outcome is None
        assert rejected.stopped_before_containment is True
        assert rejected.primary_failure_reason == "live attempt profile requires exactly 120 seconds"
        assert events == []

        config = _config(per_attempt_timeout_seconds=120.0)
        delegated = run_bounded_adapter_call(
            request, runtime, policy, "fixture prompt", config, session_id="fixture-session",
        )

        assert delegated is expected
        assert [event[0] for event in events] == ["launcher", "supervisor", "run"]
        run_event = events[-1]
        assert run_event[1] is module.adapter_worker_entry  # type: ignore[index]
        assert run_event[2] == (request, runtime, policy, "fixture prompt", config, "fixture-session")  # type: ignore[index]

    def test_public_live_entry_rejects_callable_all_true_unbound_seams_before_effects(self) -> None:
        state = _d11_allocation_state()
        preflight = FakeLightningPreflight()
        finalizer = FakeLiveSmokeFinalizer()
        result = run_unbound_live_smoke(
            _request("fixture.bin", "a" * 64),
            QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir")),
            _policy(),
            "fixture prompt",
            controller=_D11SyntheticController(state),
            config=_live_smoke_config(
                bounded_runner_config=_config(per_attempt_timeout_seconds=120.0),
            ),
            session_id="synthetic-session",
            preflight=preflight,
            finalizer=finalizer,
            adapter_dispatch=_D11SyntheticDispatch(state),
            observer=_D11SyntheticObserver(state),
            d11_config=D11OfflineConfig(3.0, 1.0, 0.02, "fixture-independent-probe"),
        )

        assert result.failure_code is Feat018LiveSmokeFailureCode.NOT_AUTHORIZED
        assert result.adapter_call_count == 0 and result.attempt_count is None
        assert preflight.calls == [] and finalizer.calls == []
        assert all(state.count(kind) == 0 for kind in D11OperationKind)
        assert state.text(state.dispatch_token) == ""


class TestD11ObservationShapeValidation:
    @staticmethod
    def _payload(resources: object) -> dict[str, object]:
        return {
            "type": "observation",
            "run_id": "run",
            "provision_token": "provision-token",
            "request_state": "sealed",
            "resources": resources,
            "active_operations": [],
            "observed_at": 11.0,
            "source_identity": "fixture-independent-probe",
        }

    @pytest.mark.parametrize(
        "resources",
        [
            {"fixture-session": "active", "terminated": "unknown"},
            "fixture-session",
            [["fixture-session"]],
            [["fixture-session", "active", "extra"]],
            [["fixture-session", 1]],
            [["fixture-session", "released"]],
        ],
    )
    def test_ipc_decoder_rejects_noncanonical_resource_entries(self, resources: object) -> None:
        with pytest.raises(ValueError):
            _d11_result_from_payload(self._payload(resources))

    @pytest.mark.parametrize(
        "resources",
        [
            {"fixture-session": "active", "terminated": "unknown"},
            ("fixture-session", "active"),
            (("fixture-session",),),
            (("fixture-session", "active", "extra"),),
            (("fixture-session", 1),),
        ],
    )
    def test_typed_observation_rejects_noncanonical_resource_entries(
        self, resources: object
    ) -> None:
        provision = LightningProvisionRefV1("run", "provision-token")
        with pytest.raises((TypeError, ValueError)):
            D11ResourceObservation(
                provision, "sealed", resources, (), 11.0, "fixture-independent-probe"
            )  # type: ignore[arg-type]

    def test_valid_observation_shape_round_trips_without_coercion(self) -> None:
        parsed = _d11_result_from_payload(
            self._payload([["fixture-session", "terminated"]])
        )
        assert isinstance(parsed, D11ResourceObservation)
        assert parsed.resources == (("fixture-session", "terminated"),)

    @staticmethod
    def _typed_observation(**overrides: object) -> D11ResourceObservation:
        values: dict[str, object] = {
            "provision": LightningProvisionRefV1("run", "provision-token"),
            "request_state": "sealed",
            "resources": (("fixture-session", "terminated"),),
            "active_operations": (),
            "observed_at_host_monotonic": 11.0,
            "source_identity": "fixture-independent-probe",
        }
        values.update(overrides)
        return D11ResourceObservation(**values)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("field_name", "typed_value", "payload_value"),
        [
            ("resources", (("duplicate", "terminated"), ("duplicate", "unknown")),
             [["duplicate", "terminated"], ["duplicate", "unknown"]]),
            ("resources", tuple((f"resource-{i}", "terminated") for i in range(17)),
             [[f"resource-{i}", "terminated"] for i in range(17)]),
            ("active_operations", tuple(f"operation-{i}" for i in range(33)),
             [f"operation-{i}" for i in range(33)]),
            ("active_operations", ("duplicate-operation", "duplicate-operation"),
             ["duplicate-operation", "duplicate-operation"]),
            ("resources", (("bad/token", "terminated"),), [["bad/token", "terminated"]]),
            ("active_operations", ("bad/token",), ["bad/token"]),
            ("observed_at_host_monotonic", -1.0, -1.0),
            ("observed_at_host_monotonic", float("nan"), float("nan")),
            ("observed_at_host_monotonic", float("inf"), float("inf")),
            ("observed_at_host_monotonic", True, True),
            ("request_state", "released", "released"),
            ("source_identity", "bad/source", "bad/source"),
        ],
    )
    def test_typed_and_ipc_observation_validation_rejects_invalid_bounds_and_tokens(
        self, field_name: str, typed_value: object, payload_value: object
    ) -> None:
        with pytest.raises((TypeError, ValueError)):
            self._typed_observation(**{field_name: typed_value})

        payload = self._payload([["fixture-session", "terminated"]])
        payload_key = {
            "observed_at_host_monotonic": "observed_at",
        }.get(field_name, field_name)
        payload[payload_key] = payload_value
        with pytest.raises((TypeError, ValueError)):
            _d11_result_from_payload(payload)

    def test_resource_and_operation_observation_limits_accept_exact_maximum(self) -> None:
        resources = tuple((f"resource-{i}", "terminated") for i in range(16))
        active_operations = tuple(f"operation-{i}" for i in range(32))
        observation = self._typed_observation(
            resources=resources, active_operations=active_operations,
            observed_at_host_monotonic=11.0,
        )

        decoded = _d11_result_from_payload(_d11_result_payload(observation))

        assert decoded == observation

    def test_malformed_provision_token_is_rejected_by_typed_and_ipc_paths(self) -> None:
        with pytest.raises(ValueError):
            LightningProvisionRefV1("run", "bad/token")
        payload = self._payload([])
        payload["provision_token"] = "bad/token"
        with pytest.raises(ValueError):
            _d11_result_from_payload(payload)


@pytest.mark.parametrize(
    ("observer_behavior", "observer_identity", "expected_code"),
    [
        ("observation_missing_session", "fixture-independent-probe", "REMOTE_RELEASE_UNVERIFIED"),
        ("observation_stale_timestamp", "fixture-independent-probe", "OBSERVATION_INVALID"),
        ("observation_future_timestamp", "fixture-independent-probe", "OBSERVATION_INVALID"),
        ("observation_foreign_provision", "fixture-independent-probe", "LIFECYCLE_PROTOCOL_FAILED"),
        ("success", "foreign-observer", "OBSERVATION_INVALID"),
        ("observation_active_operations", "fixture-independent-probe", "REMOTE_RELEASE_UNVERIFIED"),
    ],
)
def test_d11_coordinator_withholds_release_for_invalid_or_incomplete_observations(
    observer_behavior: str, observer_identity: str, expected_code: str
) -> None:
    result, _state, finalizer = _run_d11_fixture(
        observer_behavior=observer_behavior,
        observer_identity=observer_identity,
    )
    assert result.d11_report is not None
    report = result.d11_report

    assert result.cleanup_status is CleanupStatus.CLEANUP_FAILED
    assert result.effective_outcome is EffectiveOutcome.CLEANUP_FAILED
    assert report.resources_released is False
    assert "REMOTE_RELEASE_UNVERIFIED" in report.failure_codes
    assert expected_code in report.failure_codes
    assert report.unresolved_operations == report.operations
    assert report.unresolved_operations
    assert len(finalizer.calls) == 1
    assert finalizer.calls[0].cleanup_status is CleanupStatus.CLEANUP_FAILED
    assert finalizer.calls[0].d11_report is report


class TestCompleteBoundedFrameReceipt:
    @staticmethod
    def _send_raw_pipe_bytes(sender_raw: object, data: bytes) -> socket.socket | None:
        if os.name == "nt":
            sender_raw.send_bytes(data)  # type: ignore[attr-defined]
            return None
        sender_socket = socket.socket(
            family=socket.AF_UNIX, type=socket.SOCK_STREAM,
            fileno=os.dup(sender_raw.fileno()),  # type: ignore[attr-defined]
        )
        sender_socket.sendall(data)
        return sender_socket

    def test_complete_large_multiprocessing_frame_is_received(self) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 100_000)
        sender = MultiprocessingBoundedConnection(sender_raw, 100_000)
        expected = {"kind": "success", "raw_output": "x" * 32_000}
        send_failures: list[BaseException] = []

        def send_large_frame() -> None:
            try:
                sender.send_frame(expected)
            except BaseException as exc:
                send_failures.append(exc)

        sender_thread = threading.Thread(target=send_large_frame, daemon=True)
        try:
            sender_thread.start()
            assert receiver.recv_frame(2.0) == expected
            sender_thread.join(2.0)
            assert not sender_thread.is_alive()
            assert send_failures == []
        finally:
            receiver.close()
            sender.close()
            if sender_thread.ident is not None:
                sender_thread.join(0.5)

    def test_oversized_multiprocessing_frame_is_rejected_before_decode(self) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 100)
        try:
            oversized_payload = b"x" * 101
            if os.name == "nt":
                sender_raw.send_bytes(struct.pack("!i", len(oversized_payload)) + oversized_payload)
            else:
                sender_raw.send_bytes(oversized_payload)
            with pytest.raises(Feat018ProtocolViolationError, match="ceiling"):
                receiver.recv_frame(0.1)
        finally:
            sender_raw.close()
            receiver.close()

    def test_incomplete_frame_uses_one_absolute_receive_deadline(self) -> None:
        clock = FakeClock()
        sleeps: list[float] = []

        def sleep(duration: float) -> None:
            sleeps.append(duration)
            clock.advance(duration)

        connection = MultiprocessingBoundedConnection(
            _FakeRawEndpoint("parent"), 1_000, clock=clock, sleep=sleep,
            frame_probe=lambda: "incomplete",
        )
        with pytest.raises(Feat018ProtocolViolationError, match="deadline"):
            connection.recv_frame(0.012)
        assert clock() == pytest.approx(0.012)
        assert sum(sleeps) == pytest.approx(0.012)
        assert max(sleeps) <= 0.005

    def test_continuously_available_chunks_stop_at_the_absolute_deadline(self) -> None:
        clock = FakeClock()
        payload = {"kind": "success", "raw_output": "x" * 300}
        encoded = encode_envelope(payload, max_bytes=1_000)
        wire = struct.pack("!i", len(encoded)) + encoded
        read_starts: list[float] = []
        offset = 0

        def read_one_byte(_maximum: int) -> bytes:
            nonlocal offset
            read_starts.append(clock())
            chunk = wire[offset:offset + 1]
            offset += len(chunk)
            clock.advance(0.001)
            return chunk

        connection = MultiprocessingBoundedConnection(
            _FakeRawEndpoint("parent"), 1_000, clock=clock, read_chunk=read_one_byte,
        )
        with pytest.raises(Feat018ProtocolViolationError, match="deadline"):
            connection.recv_frame(0.01)

        assert len(read_starts) == 10
        assert all(start < 0.01 for start in read_starts)
        assert offset == 10
        assert offset < len(wire)
        assert wire[offset:]  # the unread payload was not consumed after the deadline
        assert clock() == pytest.approx(0.01)

    def test_zero_timeout_returns_an_already_available_complete_frame(self) -> None:
        expected = {"kind": "success", "raw_output": "ready"}
        encoded = encode_envelope(expected, max_bytes=1_000)
        wire = struct.pack("!i", len(encoded)) + encoded
        offset = 0

        def read_chunk(maximum: int) -> bytes | None:
            nonlocal offset
            if offset == len(wire):
                return None
            chunk = wire[offset:offset + min(maximum, 3)]
            offset += len(chunk)
            return chunk

        connection = MultiprocessingBoundedConnection(
            _FakeRawEndpoint("parent"), 1_000, read_chunk=read_chunk,
        )
        assert connection.recv_frame(0) == expected
        assert offset == len(wire)

    def test_zero_timeout_returns_none_for_an_empty_endpoint(self) -> None:
        connection = MultiprocessingBoundedConnection(
            _FakeRawEndpoint("parent"), 1_000, read_chunk=lambda _maximum: None,
        )
        assert connection.recv_frame(0) is None

    def test_zero_timeout_rejects_incomplete_framing(self) -> None:
        partial = struct.pack("!i", 20) + b"short"
        offset = 0

        def read_chunk(maximum: int) -> bytes | None:
            nonlocal offset
            if offset == len(partial):
                return None
            chunk = partial[offset:offset + min(maximum, 2)]
            offset += len(chunk)
            return chunk

        connection = MultiprocessingBoundedConnection(
            _FakeRawEndpoint("parent"), 1_000, read_chunk=read_chunk,
        )
        with pytest.raises(Feat018ProtocolViolationError):
            connection.recv_frame(0)
        assert offset == len(partial)

    @pytest.mark.parametrize("header_bytes", [1, 2, 3])
    def test_real_transport_stalled_partial_length_header_respects_deadline(
        self, header_bytes: int
    ) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000)
        sender_socket = self._send_raw_pipe_bytes(sender_raw, struct.pack("!i", 20)[:header_bytes])
        try:
            started = time.monotonic()
            with pytest.raises(Feat018ProtocolViolationError, match="deadline"):
                receiver.recv_frame(0.04)
            assert time.monotonic() - started < 0.5
        finally:
            if sender_socket is not None:
                sender_socket.close()
            sender_raw.close()
            receiver.close()

    def test_extended_length_header_round_trips_over_real_transport(self) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000)
        expected = {"kind": "extended-header"}
        payload = encode_envelope(expected, max_bytes=1_000)
        wire = struct.pack("!i", -1) + struct.pack("!Q", len(payload)) + payload
        sender_socket = self._send_raw_pipe_bytes(sender_raw, wire)
        try:
            assert receiver.recv_frame(0.2) == expected
        finally:
            if sender_socket is not None:
                sender_socket.close()
            sender_raw.close()
            receiver.close()

    def test_stalled_incomplete_extended_length_header_respects_deadline(self) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000)
        partial_header = struct.pack("!i", -1) + b"\x00\x00\x01"
        sender_socket = self._send_raw_pipe_bytes(sender_raw, partial_header)
        try:
            started = time.monotonic()
            with pytest.raises(Feat018ProtocolViolationError, match="deadline"):
                receiver.recv_frame(0.04)
            assert time.monotonic() - started < 0.5
        finally:
            if sender_socket is not None:
                sender_socket.close()
            sender_raw.close()
            receiver.close()

    def test_oversized_extended_length_header_is_rejected_before_payload_read(self) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000)
        extended_header = struct.pack("!i", -1) + struct.pack("!Q", 1_001)
        sender_socket = self._send_raw_pipe_bytes(sender_raw, extended_header)
        try:
            with pytest.raises(Feat018ProtocolViolationError, match="ceiling"):
                receiver.recv_frame(0.2)
        finally:
            if sender_socket is not None:
                sender_socket.close()
            sender_raw.close()
            receiver.close()

    @pytest.mark.skipif(os.name == "nt", reason="raw AF_UNIX partial-frame fixture is POSIX-only")
    @pytest.mark.parametrize("partial_payload", [False, True])
    def test_stalled_header_or_partial_payload_never_blocks_past_deadline(
        self, partial_payload: bool
    ) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000)
        sender_socket = socket.socket(
            family=socket.AF_UNIX, type=socket.SOCK_STREAM,
            fileno=os.dup(sender_raw.fileno()),
        )
        try:
            body = b"partial" if partial_payload else b""
            sender_socket.sendall(struct.pack("!i", 100) + body)
            started = time.monotonic()
            with pytest.raises(Feat018ProtocolViolationError, match="deadline|incomplete"):
                receiver.recv_frame(0.05)
            assert time.monotonic() - started < 0.5
        finally:
            sender_socket.close()
            sender_raw.close()
            receiver.close()

    @pytest.mark.skipif(os.name == "nt", reason="raw AF_UNIX truncation fixture is POSIX-only")
    def test_truncated_frame_at_peer_eof_is_rejected(self) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000)
        sender_socket = socket.socket(
            family=socket.AF_UNIX, type=socket.SOCK_STREAM,
            fileno=os.dup(sender_raw.fileno()),
        )
        sender_socket.sendall(struct.pack("!i", 100) + b"short")
        sender_socket.close()
        sender_raw.close()
        try:
            with pytest.raises(
                Feat018ProtocolViolationError, match="truncated IPC frame at peer EOF"
            ):
                receiver.recv_frame(0.05)
        finally:
            receiver.close()

    @pytest.mark.skipif(os.name != "nt", reason="Windows named-pipe framing fixture")
    @pytest.mark.parametrize("partial_payload", [False, True])
    def test_windows_named_pipe_stalled_header_or_partial_payload_is_bounded(
        self, partial_payload: bool
    ) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000)
        frame = struct.pack("!i", 100) + (b"partial" if partial_payload else b"")
        try:
            sender_raw.send_bytes(frame)
            started = time.monotonic()
            with pytest.raises(Feat018ProtocolViolationError, match="deadline"):
                receiver.recv_frame(0.05)
            assert time.monotonic() - started < 0.5
        finally:
            sender_raw.close()
            receiver.close()

    @pytest.mark.skipif(os.name != "nt", reason="Windows named-pipe EOF fixture")
    def test_windows_named_pipe_truncated_frame_at_peer_eof_is_rejected(self) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000)
        sender_raw.send_bytes(struct.pack("!i", 100) + b"short")
        sender_raw.close()
        try:
            with pytest.raises(
                Feat018ProtocolViolationError, match="truncated IPC frame at peer EOF"
            ):
                receiver.recv_frame(0.05)
        finally:
            receiver.close()

    @pytest.mark.skipif(os.name != "nt", reason="Windows named-pipe clean EOF fixture")
    def test_windows_named_pipe_clean_eof_returns_none(self) -> None:
        receiver_raw, sender_raw = multiprocessing.Pipe(duplex=True)
        receiver = MultiprocessingBoundedConnection(receiver_raw, 1_000)
        sender_raw.close()
        try:
            assert receiver.recv_frame(0.1) is None
        finally:
            receiver.close()


class TestBoundedEmptyPollBackoff:
    def test_supervisor_empty_receives_back_off_and_still_cleanup_at_deadline(self) -> None:
        class ImmediateNoneConnection:
            def __init__(self) -> None:
                self.receive_timeouts: list[float] = []
                self.sent: list[dict[str, object]] = []
                self.close_calls = 0

            def send_frame(self, payload: Mapping[str, object]) -> None:
                self.sent.append(dict(payload))

            def recv_frame(self, timeout: float) -> None:
                self.receive_timeouts.append(timeout)
                return None

            def close(self) -> None:
                self.close_calls += 1

        clock = FakeClock()
        connection = ImmediateNoneConnection()
        process = FakeProcessHandle()
        launcher = FakeProcessLauncher(process, cast(FakeBoundedConnection, connection))
        containment = FakeContainmentBackend()
        supervisor = Feat018AdapterCallSupervisor(
            config=_config(total_adapter_cap_seconds=1.0, poll_interval_seconds=0.2),
            launcher=launcher,
            containment_factory=lambda: containment,
            clock=clock,
            sleep=clock.advance,
        )

        result = supervisor.run(lambda: None, ())

        progress_timeouts = [value for value in connection.receive_timeouts if value > 0]
        assert len(progress_timeouts) == 5
        assert all(left >= right for left, right in zip(progress_timeouts, progress_timeouts[1:]))
        assert clock() == pytest.approx(1.0)
        assert result.final_state is ProgressState.FROZEN
        assert result.cleanup_status is CleanupStatus.SUCCEEDED
        assert process.closed and connection.close_calls == 1
        assert containment.close_calls == 1

    def test_d11_empty_receives_back_off_then_terminate_and_reap_worker(self) -> None:
        class ImmediateNoneConnection:
            def __init__(self) -> None:
                self.receive_timeouts: list[float] = []
                self.sent: list[dict[str, object]] = []
                self.close_calls = 0

            def send_frame(self, payload: Mapping[str, object]) -> None:
                self.sent.append(dict(payload))

            def recv_frame(self, timeout: float) -> dict[str, object] | None:
                self.receive_timeouts.append(timeout)
                if len(self.receive_timeouts) == 1:
                    return {"kind": "D11_CALL_STARTED"}
                if len(self.receive_timeouts) == 2:
                    return {"kind": "D11_HANDLE_STARTED"}
                return None

            def close(self) -> None:
                self.close_calls += 1

        clock = FakeClock()
        provision = LightningProvisionRefV1("fixture-run", "fixture-provision")
        window = D11CleanupWindow("fixture-run", 5.0, 1.0, clock)
        operation = window.issue(provision, D11OperationKind.PROVISION)
        context = D11OperationContext(operation, 1.0, 5.0, 1.0, 0.125)
        connection = ImmediateNoneConnection()
        process = FakeProcessHandle()
        launcher = FakeProcessLauncher(process, cast(FakeBoundedConnection, connection))
        containment = FakeContainmentBackend()
        boundary = Feat018LightningLifecycleProcessBoundary(
            controller=cast(object, None),  # the synthetic worker never enters this seam
            max_envelope_bytes=1_000,
            containment_factory=lambda: containment,
            cleanup_deadline_seconds=1.0,
            containment_setup_timeout_seconds=0.5,
            launcher=launcher,
            clock=clock,
            sleep=clock.advance,
        )

        with pytest.raises(Feat018LifecycleOperationError) as exc_info:
            _invoke_d11_operation(boundary, operation, context, None, None, window)

        poll_timeouts = connection.receive_timeouts[2:]
        assert len(poll_timeouts) == 8
        assert all(left >= right for left, right in zip(poll_timeouts, poll_timeouts[1:]))
        assert clock() == pytest.approx(1.0)
        assert exc_info.value.failure_code is Feat018LiveSmokeFailureCode.PROVISION_TIMEOUT
        assert process.closed and connection.close_calls == 1
        assert containment.terminate_calls == 1 and containment.close_calls == 1


def _dev_verified_success():
    from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptVerificationV1
    return DevAttemptVerificationV1(
        v2_status="SUCCEEDED", raw_status="SUCCEEDED", v2_schema_verified=True,
        raw_schema_verified=True, source_matched=True, correlation_matched=True,
        provenance_matched=True, gate_a_required=True, narration_status="NOT_SUPPLIED",
    )


class TestDevelopmentWorkerVerification:
    @pytest.fixture()
    def actual(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from hashlib import sha256
        if os.name == "posix":
            tmp_path.chmod(0o700)
        fixture = tmp_path / "fixture.bin"
        fixture.write_bytes(b"finite-private-synthetic-image")
        monkeypatch.chdir(tmp_path)
        request = _request(fixture.name, sha256(fixture.read_bytes()).hexdigest())
        result = _real_adapter(_SingleAttemptFakeRunner(deque([_success_payload()]))).understand(request)
        assert type(result) is VisionUnderstandingSuccessV2
        return request, result

    def test_actual_v2_and_mapper_result_are_verified_without_bodies(self, actual) -> None:
        from sketch2life.benchmark.feat018_live_lightning_execution import verify_dev_worker_results
        request, result = actual
        summary = verify_dev_worker_results(result, request=request, session_id="private-session", content_policy=_policy())
        assert summary == _dev_verified_success()
        encoded = summary.model_dump_json()
        for private in (request.correlation_id, request.source_image_ref.artifact_ref, "private-session"):
            assert private not in encoded
        assert not {"entities", "labels", "text", "source_image_ref", "model_provenance"} & summary.model_dump().keys()

    @pytest.mark.parametrize("field", [
        "correlation_id", "source_image_ref", "config_hash", "profile_catalog_hash",
        "adapter_version", "content_policy_version", "policy_match_view_version", "model_provenance",
    ])
    def test_schema_valid_identity_or_provenance_drift_is_not_mapping_success(self, actual, field: str) -> None:
        from sketch2life.benchmark.feat018_live_lightning_execution import verify_dev_worker_results
        request, result = actual
        value = "another-private-value"
        if field in ("config_hash", "profile_catalog_hash"):
            value = "b" * 64
        elif field == "source_image_ref":
            value = result.source_image_ref.model_copy(update={"sha256": "b" * 64})
        elif field == "model_provenance":
            value = result.model_provenance.model_copy(update={"model_revision": "b" * 40})
        summary = verify_dev_worker_results(result.model_copy(update={field: value}),
            request=request, session_id="private-session", content_policy=_policy())
        assert summary.v2_status == "SUCCEEDED" and summary.v2_schema_verified is True
        assert summary.raw_status == "NOT_REACHED" and summary.raw_schema_verified is None
        assert summary.failure_codes == (("IDENTITY_MISMATCH",) if field in (
            "correlation_id", "source_image_ref") else ("PROVENANCE_MISMATCH",))
        assert "another-private-value" not in summary.model_dump_json()

    @pytest.mark.parametrize("mutation", ["dict", "contract", "nested", "request"])
    def test_unchecked_objects_are_revalidated(self, actual, mutation: str) -> None:
        from sketch2life.benchmark.feat018_live_lightning_execution import verify_dev_worker_results
        request, result = actual
        if mutation == "dict":
            result = result.model_dump(mode="python")
        elif mutation == "contract":
            result = result.model_copy(update={"contract_version": "private-invalid-version"})
        elif mutation == "nested":
            result = result.model_copy(update={"source_image_ref": result.source_image_ref.model_copy(update={"sha256": "private-invalid-hash"})})
        else:
            request = request.model_copy(update={"contract_version": "private-invalid-version"})
        summary = verify_dev_worker_results(result, request=request, session_id="private-session", content_policy=_policy())
        assert summary.v2_status == "INVALID" and summary.raw_status == "NOT_REACHED"
        assert summary.v2_schema_verified is False and summary.failure_codes == ("V2_INVALID",)
        assert "private-invalid" not in summary.model_dump_json()

    @pytest.mark.parametrize("mutation", ["dict", "session", "source", "correlation", "gate", "provenance", "narration"])
    def test_actual_raw_is_revalidated_and_compared(self, actual, mutation: str, monkeypatch: pytest.MonkeyPatch) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as module
        request, result = actual
        mapper = module.map_vision_result_to_raw
        calls = []

        def changed_mapper(*args, **kwargs):
            calls.append(kwargs)
            raw = mapper(*args, **kwargs)
            if mutation == "dict":
                return raw.model_dump()
            changes = {
                "session": {"session_id": "wrong-session"},
                "source": {"source_image_ref": raw.source_image_ref.model_copy(update={"sha256": "b" * 64})},
                "correlation": {"correlation_id": "wrong-correlation"},
                "gate": {"gate_a_required": False},
                "provenance": {"provenance": raw.provenance.model_copy(update={"config_hash": "b" * 64})},
                "narration": {"narration_status": "RECEIVED"},
            }
            return raw.model_copy(update=changes[mutation])

        monkeypatch.setattr(module, "map_vision_result_to_raw", changed_mapper)
        summary = module.verify_dev_worker_results(result, request=request, session_id="private-session", content_policy=_policy())
        assert len(calls) == 1
        assert summary.v2_status == "SUCCEEDED" and summary.raw_status == "INVALID"
        assert summary.raw_schema_verified is False and summary.failure_codes == ("RAW_INVALID",)

    @pytest.mark.parametrize("failure", [QwenModelLoadError(), QwenTimeoutError(), QwenPermanentRuntimeError()])
    def test_actual_typed_failure_is_verified_as_failure(self, actual, failure: Exception) -> None:
        from sketch2life.benchmark.feat018_live_lightning_execution import verify_dev_worker_results
        request, _ = actual
        result = _real_adapter(_SingleAttemptFakeRunner(deque([failure]))).understand(request)
        assert type(result) is VisionUnderstandingFailureV2
        summary = verify_dev_worker_results(result, request=request, session_id="private-session", content_policy=_policy())
        assert summary.v2_status == summary.raw_status == "FAILED"
        assert summary.v2_schema_verified is summary.raw_schema_verified is True
        assert summary.failure_codes == ("ADAPTER_FAILED",)

    def test_worker_opt_in_emits_actual_verification_and_no_result_body(self, actual, monkeypatch: pytest.MonkeyPatch) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as module
        request, _ = actual

        class Runner:
            cleanup_failure = None

            def __init__(self, **kwargs):
                self.callback = kwargs["on_attempt_start"]

            def generate(self, *_args):
                self.callback()
                return _success_payload()

        monkeypatch.setattr(module, "Feat018BoundedKillableQwenGenerationRunner", Runner)
        connection = FakeBoundedConnection()
        connection.push({"kind": "CONTAINMENT_READY", "remaining_seconds_at_spawn": 300.0})
        adapter_worker_entry(connection, request, QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir")),
            _policy(), "fixture prompt", _config(total_adapter_cap_seconds=300.0), "private-session", True,
            generation_launcher=_launcher(), self_contain=lambda: None, clock=FakeClock(10.0),
            capture_factory=_fake_d9_capture_factory)
        verification = [frame for frame in connection.sent if frame.get("kind") == "DEV_VERIFICATION"]
        assert len(verification) == 1
        assert verification[0]["summary"] == _dev_verified_success().model_dump(mode="json")
        assert connection.sent[-1]["outcome"] == connection.sent[-1]["raw_status"] == "SUCCEEDED"
        text = json.dumps(connection.sent)
        assert "private-session" not in text and request.correlation_id not in text
        assert "source_image_ref" not in text and "entities" not in text


class TestDevelopmentSupervisorHooks:
    @staticmethod
    def frames(connection, *, verification=True):
        connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        connection.push({"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1})
        _push_success_d9_frames(connection)
        if verification:
            connection.push({"kind": "DEV_VERIFICATION", "summary": _dev_verified_success().model_dump(mode="json")})
        connection.push({"seq": 3, "kind": "TERMINAL", "outcome": "SUCCEEDED", "raw_status": "SUCCEEDED"})

    def test_only_accepted_progress_reaches_callback(self) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        self.frames(launcher.connection)
        events = []
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.require_verification = True
        supervisor.on_accepted_progress = events.append
        result = supervisor.run(_no_op_entry, ())
        assert result.is_success and result.verification_summary == _dev_verified_success()
        assert [event.seq for event in events] == [1, 2, 3]
        assert result.attempt_count == 1

    @pytest.mark.parametrize("case", ["omitted", "duplicate", "before-start", "invalid", "contradiction"])
    def test_bad_verification_freezes_success(self, case: str) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        value = _dev_verified_success().model_dump(mode="json")
        if case == "before-start":
            launcher.connection.push({"kind": "DEV_VERIFICATION", "summary": value})
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        launcher.connection.push({"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1})
        _push_success_d9_frames(launcher.connection)
        if case != "omitted":
            if case == "invalid":
                value["private-body"] = "private-diagnostic"
            elif case == "contradiction":
                value = {}
            launcher.connection.push({"kind": "DEV_VERIFICATION", "summary": value})
            if case == "duplicate":
                launcher.connection.push({"kind": "DEV_VERIFICATION", "summary": value})
        launcher.connection.push({"seq": 3, "kind": "TERMINAL", "outcome": "SUCCEEDED"})
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.require_verification = True
        result = supervisor.run(_no_op_entry, ())
        assert not result.is_success and result.final_state is ProgressState.FROZEN
        assert "private-diagnostic" not in repr(result)
        assert launcher.handle.closed and launcher.connection.closed

    @pytest.mark.parametrize("value", [True, 0, 1, None, "private-cancel-value"])
    def test_cancel_or_non_boolean_control_never_releases(self, value: object) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.cancel_requested = lambda: value
        result = supervisor.run(_no_op_entry, ())
        assert not result.is_success and result.stopped_before_containment
        assert not launcher.connection.sent
        assert "private-cancel-value" not in repr(result)

    def test_cancel_during_confirmation_blocks_release(self) -> None:
        cancelled = False
        clock = FakeClock(10.0)
        launcher = _launcher(clock)

        class Containment(FakeContainmentBackend):
            def confirm_worker_contained(self, *args, **kwargs):
                nonlocal cancelled
                cancelled = True
                return super().confirm_worker_contained(*args, **kwargs)

        supervisor = _supervisor(launcher=launcher, containment=Containment(), clock=clock)
        supervisor.cancel_requested = lambda: cancelled
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment and not launcher.connection.sent

    def test_release_guard_does_not_reenter_cancel_lock_and_rechecks_deadline(self) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        self.frames(launcher.connection)
        locked = False

        def cancel():
            assert not locked
            return False

        def guard(release):
            nonlocal locked
            locked = True
            try:
                clock.advance(1.0)
                release()
            finally:
                locked = False

        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.cancel_requested = cancel
        supervisor.release_guard = guard
        supervisor.require_verification = True
        result = supervisor.run(_no_op_entry, ())
        assert result.is_success
        assert launcher.connection.sent[0]["remaining_seconds_at_spawn"] == 9.0

    @pytest.mark.parametrize("failure", ["registration", "guard", "callback", "cancel"])
    def test_private_hook_exception_cleans_up_without_exception_text(self, failure: str) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        self.frames(launcher.connection)
        containment = FakeContainmentBackend()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)

        def explode(*_args):
            raise RuntimeError("private-hook-exception")

        if failure == "registration":
            supervisor.register_launch = explode
        elif failure == "guard":
            supervisor.release_guard = explode
        elif failure == "callback":
            supervisor.on_accepted_progress = explode
        else:
            supervisor.cancel_requested = explode
        result = supervisor.run(_no_op_entry, ())
        assert not result.is_success
        assert containment.terminate_calls == 1 and launcher.handle.closed
        assert "private-hook-exception" not in repr(result)

    def test_trusted_registration_precedes_both_model_release_grants(self) -> None:
        from types import SimpleNamespace
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        connection = launcher.connection
        connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        connection.push({"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1})
        connection.push({"kind": "DEV_REGISTER_GENERATION", "pid": 4243, "attempt_number": 1})
        _push_success_d9_frames(connection)
        connection.push({"kind": "DEV_VERIFICATION", "summary": _dev_verified_success().model_dump(mode="json")})
        connection.push({"seq": 3, "kind": "TERMINAL", "outcome": "SUCCEEDED", "raw_status": "SUCCEEDED"})
        containment = FakeContainmentBackend()
        events = []
        parent = object()
        adapter_birth = object()

        def register(pid, role, parent_birth):
            assert containment.confirm_calls
            events.append((role, pid, parent_birth, len(connection.sent)))
            return SimpleNamespace(birth=adapter_birth if role == "ADAPTER" else object())

        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        supervisor.require_verification = True
        supervisor.register_launch = register
        supervisor.launch_parent_birth = parent
        supervisor.cancel_requested = lambda: False
        supervisor.release_guard = lambda callback: callback()
        result = supervisor.run(_no_op_entry, ())
        assert result.is_success
        assert events == [("ADAPTER", 4242, parent, 0), ("GENERATION", 4243, adapter_birth, 1)]
        assert [frame["kind"] for frame in connection.sent] == ["CONTAINMENT_READY", "DEV_REGISTERED"]

    @pytest.mark.parametrize("case", ["before-attempt", "wrong-attempt", "duplicate", "bad-pid", "after-cleanup"])
    def test_unbound_generation_registration_never_releases_child(self, case: str) -> None:
        from types import SimpleNamespace
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        connection = launcher.connection
        connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        if case != "before-attempt":
            connection.push({"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1})
        if case == "after-cleanup":
            connection.push({"kind": "DEV_CLEANUP_INTENT"})
        frame = {"kind": "DEV_REGISTER_GENERATION", "pid": True if case == "bad-pid" else 4243,
                 "attempt_number": 2 if case == "wrong-attempt" else 1}
        connection.push(frame)
        if case == "duplicate":
            connection.push(frame)
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.require_verification = True
        supervisor.register_launch = lambda *_args: SimpleNamespace(birth=object())
        supervisor.launch_parent_birth = object()
        result = supervisor.run(_no_op_entry, ())
        assert not result.is_success and result.final_state is ProgressState.FROZEN
        grants = [frame for frame in connection.sent if frame["kind"] == "DEV_REGISTERED"]
        assert len(grants) == (1 if case == "duplicate" else 0)

    def test_cleanup_grant_has_one_remote_deadline_and_freezes_future_attempts(self) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        connection = launcher.connection
        connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        connection.push({"kind": "DEV_CLEANUP_INTENT"})
        connection.push({"kind": "DEV_CLEANUP_INTENT"})
        connection.push({"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1})
        calls = []
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.require_verification = True
        supervisor.on_cleanup_intent = lambda: calls.append(clock()) or 11.0
        supervisor.cleanup_deadline = lambda: 11.0
        result = supervisor.run(_no_op_entry, ())
        assert calls == [10.0] and not result.is_success
        grants = [frame["deadline_remote_monotonic"] for frame in connection.sent if frame["kind"] == "DEV_CLEANUP_GRANT"]
        assert grants == [11.0, 11.0]
        assert result.attempt_count is None

    def test_development_entry_requires_complete_binding_before_launcher(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as module

        def forbidden(**_kwargs):
            pytest.fail("unbound entry constructed a launcher")

        monkeypatch.setattr(module, "MultiprocessingProcessLauncher", forbidden)
        result = run_bounded_adapter_call(_request("fixture.bin", "a" * 64),
            QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir")), _policy(), "fixture prompt", _config(),
            session_id="private-session", verify_development_results=True)
        assert result.final_state is ProgressState.NOT_STARTED
        assert result.primary_failure_reason == "development invocation binding incomplete"

    def test_generation_registration_gate_installs_d9_before_model_import(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sketch2life.benchmark.feat018_live_lightning_execution as module
        import sketch2life.infrastructure.ai.qwen_vision as qwen
        events = []

        def capture(*args):
            events.append("capture")
            return _fake_d9_capture_factory(*args)

        class Connection(FakeBoundedConnection):
            def recv_frame(self, timeout):
                assert events == ["capture"]
                events.append("gate")
                return None

        monkeypatch.setattr(qwen, "_default_model_factory", lambda *_args: pytest.fail("model reached without registration"))
        connection = Connection()
        module._dev_registered_generation_child_entry(connection, vision_profile_catalog_v2().profiles[0],
            QwenVisionRuntimeConfig(model_dir=Path("fixture-model-dir")), "fixture.bin", "fixture prompt",
            1000, 2000, capture, 1)
        assert events == ["capture", "gate"]
        assert all("private" not in json.dumps(frame) for frame in connection.sent)

    @pytest.mark.parametrize("status", [None, "FAILED"])
    def test_success_terminal_requires_received_matching_raw_status(self, status) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        self.frames(launcher.connection)
        terminal = launcher.connection.inbox[-1]
        if status is None:
            terminal.pop("raw_status")
        else:
            terminal["raw_status"] = status
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.require_verification = True
        result = supervisor.run(_no_op_entry, ())
        assert not result.is_success and result.final_state is ProgressState.FROZEN

    def test_original_remote_work_deadline_is_not_reanchored(self) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        self.frames(launcher.connection)
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.work_deadline_monotonic = 12.0
        supervisor.require_verification = True
        result = supervisor.run(_no_op_entry, ())
        assert result.is_success
        assert launcher.connection.sent[0]["remaining_seconds_at_spawn"] == 2.0

    @pytest.mark.parametrize("deadline", [10.0, 9.0, True, float("nan"), float("inf")])
    def test_expired_or_invalid_original_deadline_precedes_containment_allocation(self, deadline) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        containment = FakeContainmentBackend()
        supervisor = _supervisor(launcher=launcher, containment=containment, clock=clock)
        supervisor.work_deadline_monotonic = deadline
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment and not result.is_success
        assert not containment.created and not launcher.launch_calls

    def test_expiry_inside_release_guard_does_not_send_stale_duration(self) -> None:
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.work_deadline_monotonic = 11.0

        def guard(release):
            clock.set(11.0)
            release()

        supervisor.release_guard = guard
        result = supervisor.run(_no_op_entry, ())
        assert result.stopped_before_containment and not launcher.connection.sent
        assert launcher.handle.closed and launcher.connection.closed

    def test_inner_registration_requires_received_birth_before_grant(self) -> None:
        from types import SimpleNamespace
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        launcher.connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        launcher.connection.push({"seq": 2, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": 1})
        launcher.connection.push({"kind": "DEV_REGISTER_GENERATION", "pid": 4243, "attempt_number": 1})
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.require_verification = True
        supervisor.register_launch = lambda pid, role, parent: SimpleNamespace(birth=object()) if role == "ADAPTER" else None
        result = supervisor.run(_no_op_entry, ())
        assert not result.is_success
        assert all(frame["kind"] != "DEV_REGISTERED" for frame in launcher.connection.sent)

    def test_second_attempt_keeps_existing_registration_and_progress_policy(self) -> None:
        from types import SimpleNamespace
        clock = FakeClock(10.0)
        launcher = _launcher(clock)
        connection = launcher.connection
        connection.push({"seq": 1, "kind": "ADAPTER_STARTED"})
        for attempt in (1, 2):
            connection.push({"seq": attempt + 1, "kind": "GENERATION_ATTEMPT_STARTED", "attempt_number": attempt})
            connection.push({"kind": "DEV_REGISTER_GENERATION", "pid": 4242 + attempt, "attempt_number": attempt})
        _push_success_d9_frames(connection, attempt_numbers=(1, 2))
        connection.push({"kind": "DEV_VERIFICATION", "summary": _dev_verified_success().model_dump(mode="json")})
        connection.push({"seq": 4, "kind": "TERMINAL", "outcome": "SUCCEEDED", "raw_status": "SUCCEEDED"})
        supervisor = _supervisor(launcher=launcher, containment=FakeContainmentBackend(), clock=clock)
        supervisor.require_verification = True
        registrations = []

        def register(pid, role, parent):
            registrations.append((pid, role))
            return SimpleNamespace(birth=object())

        supervisor.register_launch = register
        result = supervisor.run(_no_op_entry, ())
        assert result.is_success and result.attempt_count == 2
        assert registrations == [(4242, "ADAPTER"), (4243, "GENERATION"), (4244, "GENERATION")]
        assert len([frame for frame in connection.sent if frame["kind"] == "DEV_REGISTERED"]) == 2
