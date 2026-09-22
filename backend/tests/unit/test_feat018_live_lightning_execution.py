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
import stat
import subprocess
import sys
import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
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
    _cancel_lightning_operation,  # noqa: PLC2701 - deterministic inline-boundary test seam
    _cancel_termination_operation,  # noqa: PLC2701 - deterministic inline-boundary test seam
    _wait_for_lightning_operation,  # noqa: PLC2701 - deterministic inline-boundary test seam
    _Win32JobHandles,  # noqa: PLC2701 - white-box test of the ctypes binding surface (F4)
    adapter_worker_entry,
    decode_envelope,
    encode_envelope,
    finalize_smoke_run,
    new_evidence_id,
    new_run_id,
    posix_worker_self_contain,
    read_committed_pair,
    run_live_smoke,
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
    terminate_calls: int = field(default=0, init=False)
    kill_calls: int = field(default=0, init=False)
    join_calls: list[float | None] = field(default_factory=list, init=False)
    die_on_terminate: bool = False
    die_on_kill: bool = True
    raise_on_terminate: BaseException | None = None

    @property
    def pid(self) -> int | None:
        return self._pid

    def is_alive(self) -> bool:
        return self._alive

    def terminate(self) -> None:
        self.terminate_calls += 1
        if self.raise_on_terminate is not None:
            raise self.raise_on_terminate
        if self.die_on_terminate:
            self._alive = False

    def kill(self) -> None:
        self.kill_calls += 1
        if self.die_on_kill:
            self._alive = False

    def join(self, timeout: float | None = None) -> None:
        self.join_calls.append(timeout)

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

    def finalize(self) -> D9CaptureReport:
        self.finalize_calls += 1
        return _fake_d9_report(self.process_role, attempt_number=self.attempt_number)


def _fake_d9_capture_factory(
    process_role: D9ProcessRole,
    attempt_number: int | None,
    stdout_max_bytes: int,
    stderr_max_bytes: int,
) -> FakeD9Capture:
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

    def terminate_all(self) -> None:
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
    daemon: bool | None = field(default=None, init=False)
    start_calls: int = field(default=0, init=False)
    terminate_calls: int = field(default=0, init=False)
    kill_calls: int = field(default=0, init=False)
    join_calls: list[float | None] = field(default_factory=list, init=False)
    is_alive_calls: int = field(default=0, init=False)
    cleanup_events: list[str] = field(default_factory=list, init=False)

    @property
    def pid(self) -> int | None:
        return self._pid

    @property
    def can_spawn_child_processes(self) -> bool:
        return self.daemon is False

    def start(self) -> None:
        self.start_calls += 1
        if self.start_marks_live_before_error:
            self.alive = True
        if self.start_error is not None:
            raise self.start_error
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

    def is_alive(self) -> bool:
        return bool(self.actual_process.is_alive())

    def terminate(self) -> None:
        self.actual_process.terminate()

    def kill(self) -> None:
        self.actual_process.kill()

    def join(self, timeout: float | None = None) -> None:
        self.actual_process.join(timeout)

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
        assert context.child.close_calls == 1
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

        assert process is context.process
        assert process.daemon is False
        assert process.can_spawn_child_processes is True
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
            assert isinstance(process, _NoStartProcess)
            assert process.start_calls == 1  # launcher invoked only the no-op proxy method
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

        expected_cleanup_events = {
            "terminate": [
                "is_alive",
                "terminate",
                "join_1",
                "is_alive",
                "kill",
                "join_2",
                "is_alive",
            ],
            "grace_join": [
                "is_alive",
                "terminate",
                "join_1",
                "is_alive",
                "is_alive",
            ],
            "kill": [
                "is_alive",
                "terminate",
                "join_1",
                "is_alive",
                "kill",
                "join_2",
                "is_alive",
            ],
            "final_join": [
                "is_alive",
                "terminate",
                "join_1",
                "is_alive",
                "kill",
                "join_2",
                "is_alive",
            ],
        }
        assert process.cleanup_events == expected_cleanup_events[failure_kind]
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
            return 1 if self.close_handle_result else 0

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

    def test_partial_job_cleanup_failure_is_reported_without_retaining_handle(self) -> None:
        fake = _FakeKernel32()
        fake.set_information_result = False
        fake.close_handle_result = False
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))

        with pytest.raises(Feat018ContainmentError, match="rollback cleanup failed"):
            containment.create()

        assert containment._job_handle is None
        assert containment.is_empty() is False
        assert [call for call in fake.calls if call[0] == "CloseHandle"] == [
            ("CloseHandle", (fake.job_handle,))
        ]


# ------------------------------------------------------------------------------------------
# F1 -- truthful Windows cleanup verification
# ------------------------------------------------------------------------------------------


class TestWindowsJobObjectContainmentCleanupTruth:
    def _containment(self, fake: _FakeKernel32) -> WindowsJobObjectContainment:
        containment = WindowsJobObjectContainment(_win32=_Win32JobHandles(kernel32=fake))
        containment.create()
        return containment

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
        containment = self._containment(fake)
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
        launcher = _launcher()  # never pushes a frame
        clock = FakeClock()
        runner = Feat018BoundedKillableQwenGenerationRunner(
            config=self._config(per_attempt_timeout_seconds=1.0),
            worker_cap_deadline_monotonic=clock() + 300.0,
            launcher=launcher,
            clock=clock,
        )
        with pytest.raises(QwenTimeoutError):
            runner.generate(cast(object, None), cast(object, None), Path("x.png"), "prompt")

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

    def test_real_capture_normal_child_exit_drains_both_streams(self) -> None:
        probe = (
            'import os; '
            'from sketch2life.benchmark.feat018_live_lightning_execution import '
            'D9ProcessRole, D9ProcessStreamCapture, D9_STDERR_MAX_BYTES, D9_STDOUT_MAX_BYTES; '
            'capture = D9ProcessStreamCapture('
            'D9ProcessRole.INNER_GENERATION_CHILD, 1, '
            'D9_STDOUT_MAX_BYTES, D9_STDERR_MAX_BYTES); '
            "os.write(1, b'probe-out'); os.write(2, b'probe-err'); "
            'report = capture.finalize(); '
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
            lifecycle_boundary=FakeInlineLightningLifecycleBoundary(controller, controller.clock),
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

        assert cleanup_failed is True
        assert containment.terminate_calls == 1  # exactly-once cleanup, even on failure
        assert containment.close_calls == 1

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
        assert containment.close_calls == 1


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
        ) -> FakeD9Capture:
            events.append('capture')
            return _fake_d9_capture_factory(
                process_role, attempt_number, stdout_max_bytes, stderr_max_bytes
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
        assert result.effective_outcome is EffectiveOutcome.FAILED


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
    @pytest.mark.parametrize("mode", ["success", "unmapped", "extra-file", "cleanup-failure"])
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
