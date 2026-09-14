"""Offline tests for the FEAT-018 P2-T2 bounded-runner package (revision 5, approved scope).

Every test here uses injected fakes only: fake clocks, fake process launchers, fake containment
backends, and a fake filesystem. No test in this file loads a provider or model, touches a GPU,
opens Lightning, uses a network, or launches a real subprocess. Retry and terminal-classification
assertions exercise the real, unmodified ``QwenVisionAdapter.understand()`` with a fake
``QwenGenerationRunner``; fake adapters are used only for the outer-supervisor edge cases, per the
approved package's real-adapter compatibility contract.
"""

from __future__ import annotations

import multiprocessing
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import pytest

from sketch2life.benchmark.feat018_live_lightning_execution import (
    AcceptanceResult,
    BoundedConnection,
    CleanupStatus,
    EffectiveOutcome,
    Feat018AdapterCallSupervisor,
    Feat018BoundedKillableQwenGenerationRunner,
    Feat018BoundedRunnerConfig,
    Feat018CleanupFailedError,
    Feat018ContainmentError,
    Feat018EvidenceCommitWriter,
    Feat018FrameTooLargeError,
    Feat018LauncherError,
    Feat018ProgressStateMachine,
    Feat018ProtocolViolationError,
    MultiprocessingBoundedConnection,
    MultiprocessingProcessLauncher,
    PairVerdict,
    PosixProcessGroupContainment,
    ProcessHandle,
    ProgressEvent,
    ProgressEventKind,
    ProgressState,
    WindowsJobObjectContainment,
    _Win32JobHandles,  # noqa: PLC2701 - white-box test of the ctypes binding surface (F4)
    adapter_worker_entry,
    decode_envelope,
    encode_envelope,
    new_evidence_id,
    new_run_id,
    read_committed_pair,
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
        assert connection.sent == []


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


# ------------------------------------------------------------------------------------------
# F3 -- the concrete, gated adapter-worker entry point
# ------------------------------------------------------------------------------------------


class TestAdapterWorkerEntryGate:
    """F3: ``adapter_worker_entry`` never constructs anything before a valid release."""

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
        assert connection.sent == []
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
        assert connection.sent == []
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
        assert connection.sent == []
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

        assert connection.sent == []
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

        assert connection.sent == []
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
        assert connection.sent == []
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
        kinds = [frame["kind"] for frame in connection.sent]
        assert kinds[0] == "ADAPTER_STARTED"
        assert "GENERATION_ATTEMPT_STARTED" in kinds
        assert kinds[-1] == "TERMINAL"
        assert connection.sent[-1]["outcome"] == "SUCCEEDED"
        assert generation_launcher.launch_calls  # the generation child was actually launched

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
        kinds = [frame["kind"] for frame in connection.sent]
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
        seqs = [frame["seq"] for frame in connection.sent]
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

        assert connection.sent == []
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
        assert [frame["kind"] for frame in connection.sent] == [
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
