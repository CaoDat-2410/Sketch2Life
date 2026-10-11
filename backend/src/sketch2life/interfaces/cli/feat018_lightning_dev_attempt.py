"""Owner-managed Studio invocation controls; public entry points remain denied.

The offline composer has no default transport, process launcher, adapter or inspector.
Its injected adapter is the existing bounded entry, never a second execution runner.
Invocation cleanup cannot establish Studio/provider resource release.
"""

from __future__ import annotations

import contextlib
import math
import os
import select
import socket
import stat
import struct
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal, Protocol

from sketch2life.benchmark.feat018_live_lightning_execution import (
    AcceptanceResult,
    CleanupStatus,
    EffectiveOutcome,
    Feat018ProgressStateMachine,
    ProgressEvent,
    ProgressEventKind,
    SupervisorRunResult,
    Feat018BoundedRunnerConfig,
    run_bounded_adapter_call,
)
from sketch2life.contracts.schemas.vision_v2 import VisionUnderstandingRequestV2
from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.ai.feat018_lightning_ssh import encode_attempt_frame
from sketch2life.contracts.schemas.feat018_live_binding import (
    DevAttemptBudgetsV1,
    DevAttemptControlV1,
    DevAttemptFailureCode,
    DevAttemptFrameV1,
    DevAttemptIdentityV1,
    DevAttemptSummaryV1,
)

MAX_CONTROL_BYTES = 8192
MAX_CONTROL_POLLS = 1024
MAX_CONTROL_WIRE_BYTES = 1024 * 1024


class DevAttemptControlError(ValueError):
    """A fixed diagnostic, without private control input."""


def _denied() -> DevAttemptSummaryV1:
    return DevAttemptSummaryV1(outcome="NOT_AUTHORIZED", failure_codes=("NOT_AUTHORIZED",))


def run_dev_attempt_host(*args: object, **kwargs: object) -> DevAttemptSummaryV1:
    return _denied()


def run_dev_attempt_session(*args: object, **kwargs: object) -> DevAttemptSummaryV1:
    return _denied()


def run_dev_attempt_control(*args: object, **kwargs: object) -> DevAttemptSummaryV1:
    return _denied()


def _private_path(path: Path, directory: bool) -> None:
    facts = path.lstat()
    if os.name != "posix" or stat.S_ISLNK(facts.st_mode):
        raise DevAttemptControlError("private channel permissions unavailable")
    if facts.st_uid != os.getuid() or facts.st_mode & 0o077:
        raise DevAttemptControlError("private channel ownership invalid")
    if directory:
        if not stat.S_ISDIR(facts.st_mode):
            raise DevAttemptControlError("private channel root invalid")
    elif not stat.S_ISREG(facts.st_mode) or facts.st_nlink != 1:
        raise DevAttemptControlError("private claim is not an exclusive file")


@contextlib.contextmanager
def _native_file_lock(fd: int) -> Iterator[None]:
    if os.name == "posix":
        import fcntl

        # A stuck holder cannot suspend the authoritative work/cleanup deadline.
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    elif os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        raise DevAttemptControlError("private claim lock unavailable")


@dataclass(slots=True)
class PrivateInvocationGate:
    """One cross-process START/CANCEL authority, retained after completion.

    CANCEL may create a tombstone before OPEN. The persistent state is never deleted,
    so a reconnect cannot reopen or launch that invocation again.
    """

    root: Path = field(repr=False)
    identity: DevAttemptIdentityV1 = field(repr=False)
    check_path: Callable[[Path, bool], None] = field(default=_private_path, repr=False)
    lock_file: Callable[[int], contextlib.AbstractContextManager[None]] = field(
        default=_native_file_lock, repr=False
    )
    directory: Path = field(init=False, repr=False)
    claim_path: Path = field(init=False, repr=False)
    _root_inode: tuple[int, int] = field(init=False, repr=False)
    _directory_inode: tuple[int, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.identity = self.identity.revalidated()
        self.root = Path(self.root)
        if not self.root.is_absolute():
            raise DevAttemptControlError("private root must be explicitly absolute")
        # Check every existing path component for link substitution. Permissions of
        # ordinary ancestors may differ; the selected root itself must be private.
        for component in (self.root, *self.root.parents):
            facts = component.lstat()
            if stat.S_ISLNK(facts.st_mode) or not stat.S_ISDIR(facts.st_mode):
                raise DevAttemptControlError("private root contains a link")
        self.check_path(self.root, True)
        root_facts = self.root.lstat()
        self._root_inode = (root_facts.st_dev, root_facts.st_ino)
        self.directory = self.root / self.identity.invocation_ref
        try:
            self.directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        self.check_path(self.directory, True)
        directory_facts = self.directory.lstat()
        self._directory_inode = (directory_facts.st_dev, directory_facts.st_ino)
        self.claim_path = self.directory / "claim.json"

    def _open(self, *, create: bool) -> tuple[int, bool]:
        self.check_path(self.root, True)
        self.check_path(self.directory, True)
        for path, expected in ((self.root, self._root_inode), (self.directory, self._directory_inode)):
            facts = path.lstat()
            if (facts.st_dev, facts.st_ino) != expected:
                raise DevAttemptControlError("private directory identity changed")
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        flags = os.O_RDWR | nofollow | getattr(os, "O_BINARY", 0)
        created = False
        directory_fd = None
        # On the real POSIX path, resolve the claim relative to the verified open
        # directory handle, so parent-path replacement cannot redirect the open.
        if os.open in os.supports_dir_fd:
            directory_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | nofollow)
            facts = os.fstat(directory_fd)
            if (facts.st_dev, facts.st_ino) != self._directory_inode:
                os.close(directory_fd)
                raise DevAttemptControlError("private directory handle changed")
        try:
            target = "claim.json" if directory_fd is not None else self.claim_path
            options = {"dir_fd": directory_fd} if directory_fd is not None else {}
            if create:
                try:
                    fd = os.open(target, flags | os.O_CREAT | os.O_EXCL, 0o600, **options)
                    created = True
                except FileExistsError:
                    self.check_path(self.claim_path, False)
                    fd = os.open(target, flags, **options)
            else:
                self.check_path(self.claim_path, False)
                fd = os.open(target, flags, **options)
        finally:
            if directory_fd is not None:
                os.close(directory_fd)
        facts = os.fstat(fd)
        current = self.claim_path.lstat()
        if (
            not stat.S_ISREG(facts.st_mode) or facts.st_nlink != 1
            or (facts.st_dev, facts.st_ino) != (current.st_dev, current.st_ino)
        ):
            os.close(fd)
            raise DevAttemptControlError("private claim identity changed")
        if not created:
            self.check_path(self.claim_path, False)
        return fd, created

    def transition(self, control: DevAttemptControlV1) -> str:
        checked = control.revalidated()
        if checked.identity != self.identity:
            raise DevAttemptControlError("private control identity mismatch")
        create = checked.operation in ("OPEN", "CANCEL", "EOF")
        fd, created = self._open(create=create)
        try:
            with self.lock_file(fd):
                if created:
                    if checked.operation == "OPEN":
                        state = checked
                    else:
                        state = DevAttemptControlV1(
                            identity=self.identity, operation="CANCEL", sequence=checked.sequence
                        )
                    self._write(fd, state)
                    return state.operation
                os.lseek(fd, 0, os.SEEK_SET)
                raw = os.read(fd, MAX_CONTROL_BYTES + 1)
                if not raw or len(raw) > MAX_CONTROL_BYTES:
                    raise DevAttemptControlError("private claim state invalid")
                state = DevAttemptControlV1.model_validate_json(raw)
                if state.identity != self.identity:
                    raise DevAttemptControlError("private claim identity mismatch")
                if checked.operation == "OPEN":
                    raise DevAttemptControlError("private invocation claim already exists")
                if checked.operation == "START":
                    if state.operation != "OPEN":
                        raise DevAttemptControlError("private invocation start already sealed")
                    self._write(fd, checked)
                    return "START"
                if checked.operation in ("CANCEL", "EOF"):
                    state = DevAttemptControlV1(
                        identity=self.identity, operation="CANCEL", sequence=checked.sequence
                    )
                    self._write(fd, state)
                return state.operation
        except Exception as error:
            if isinstance(error, DevAttemptControlError):
                raise
            raise DevAttemptControlError("private claim validation failed") from None
        finally:
            os.close(fd)

    @staticmethod
    def _write(fd: int, state: DevAttemptControlV1) -> None:
        data = state.model_dump_json().encode("utf-8")
        if len(data) > MAX_CONTROL_BYTES:
            raise DevAttemptControlError("private claim exceeds limit")
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        written = os.write(fd, data)
        if written != len(data):
            raise DevAttemptControlError("private claim write incomplete")
        os.fsync(fd)

    def state(self) -> str:
        return self.transition(DevAttemptControlV1(identity=self.identity, operation="STATUS"))

    def release_guard(self, release: Callable[[], None]) -> None:
        """Serialize the final model release with every persistent CANCEL writer."""
        fd, _ = self._open(create=False)
        try:
            with self.lock_file(fd):
                os.lseek(fd, 0, os.SEEK_SET)
                raw = os.read(fd, MAX_CONTROL_BYTES + 1)
                if not raw or len(raw) > MAX_CONTROL_BYTES:
                    raise DevAttemptControlError("private release claim invalid")
                state = DevAttemptControlV1.model_validate_json(raw)
                if state.identity != self.identity or state.operation != "START":
                    raise DevAttemptControlError("private release is cancelled")
                release()
        except Exception:
            raise DevAttemptControlError("private release guard failed") from None
        finally:
            os.close(fd)

    def seal(self) -> None:
        """Persist terminal admission closure without declaring cancellation."""
        fd, _ = self._open(create=False)
        try:
            with self.lock_file(fd):
                os.lseek(fd, 0, os.SEEK_SET)
                raw = os.read(fd, MAX_CONTROL_BYTES + 1)
                if not raw or len(raw) > MAX_CONTROL_BYTES:
                    raise DevAttemptControlError("private seal claim invalid")
                state = DevAttemptControlV1.model_validate_json(raw)
                if state.identity != self.identity:
                    raise DevAttemptControlError("private seal identity invalid")
                if state.operation not in ("CANCEL", "EOF"):
                    self._write(fd, DevAttemptControlV1(identity=self.identity, operation="EOF", sequence=state.sequence))
        except Exception:
            raise DevAttemptControlError("private admission seal failed") from None
        finally:
            os.close(fd)


class ControlSource(Protocol):
    def poll(self, timeout_seconds: float) -> DevAttemptControlV1 | bytes | None: ...
    def eof(self) -> bool: ...
    def send(self, frame: DevAttemptFrameV1) -> None: ...


@dataclass(slots=True)
class PrivateControlSocket:
    """Private AF_UNIX control endpoint; protocol input uses protected JSON ingress."""

    gate: PrivateInvocationGate
    socket_factory: Callable[..., socket.socket] = field(default=socket.socket, repr=False)
    select_ready: Callable[..., object] = field(default=select.select, repr=False)
    _listener: socket.socket | None = field(default=None, init=False, repr=False)
    _peer: socket.socket | None = field(default=None, init=False, repr=False)
    _buffer: bytearray = field(default_factory=bytearray, init=False, repr=False)
    _eof: bool = field(default=False, init=False)
    _received_bytes: int = field(default=0, init=False)
    _sent_bytes: int = field(default=0, init=False)
    _secondary: dict[socket.socket, bytearray] = field(default_factory=dict, init=False, repr=False)
    _reply_peer: socket.socket | None = field(default=None, init=False, repr=False)
    secondary_control: bool = field(default=False, init=False)
    _secondary_sequences: dict[socket.socket, int] = field(default_factory=dict, init=False, repr=False)

    def _frame_available(self, buffer: bytearray | None = None) -> bool:
        buffer = self._buffer if buffer is None else buffer
        if len(buffer) < 4:
            return False
        size = struct.unpack("!I", buffer[:4])[0]
        if not 0 < size <= MAX_CONTROL_BYTES:
            raise DevAttemptControlError("private control frame exceeds limit")
        return len(buffer) >= size + 4

    def open(self) -> None:
        if self._listener is not None or self.gate.state() != "OPEN":
            raise DevAttemptControlError("private socket admission failed")
        if os.name != "posix" or not hasattr(socket, "AF_UNIX"):
            raise DevAttemptControlError("private socket trust unavailable")
        self.gate.check_path(self.gate.directory, True)
        path = self.gate.directory / "control.sock"
        if path.exists() or path.is_symlink():
            raise DevAttemptControlError("private socket cannot be reused")
        listener = self.socket_factory(socket.AF_UNIX, socket.SOCK_STREAM)
        self._listener = listener
        try:
            listener.bind(str(path))
            os.chmod(path, 0o600)
            facts = path.lstat()
            if not stat.S_ISSOCK(facts.st_mode) or facts.st_uid != os.getuid() or facts.st_mode & 0o077:
                raise DevAttemptControlError("private socket permissions invalid")
            listener.listen(4)
            listener.setblocking(False)
        except Exception:
            listener.close()
            self._listener = None
            raise DevAttemptControlError("private socket creation failed") from None

    def poll(self, timeout_seconds: float) -> DevAttemptControlV1 | None:
        if not math.isfinite(timeout_seconds) or timeout_seconds < 0 or self._listener is None:
            raise DevAttemptControlError("invalid bounded control poll")
        peers = [(self._peer, self._buffer)] if self._peer is not None else []
        peers.extend(self._secondary.items())
        framed = [(peer, buffer) for peer, buffer in peers if self._frame_available(buffer)]
        if not framed:
            inputs = [self._listener, *(peer for peer, _ in peers)]
            ready, _, _ = self.select_ready(inputs, [], [], timeout_seconds)  # type: ignore[misc]
            if self._listener in ready:
                peer, _ = self._listener.accept()
                peer.setblocking(False)
                if not hasattr(socket, "SO_PEERCRED"):
                    peer.close()
                    raise DevAttemptControlError("private peer identity unavailable")
                credentials = peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
                _, uid, _ = struct.unpack("3i", credentials)
                if uid != os.getuid():
                    peer.close()
                    raise DevAttemptControlError("private peer ownership mismatch")
                if self._peer is None and not self._eof:
                    self._peer = peer
                elif len(self._secondary) < 3:
                    self._secondary[peer] = bytearray()
                else:
                    peer.close()
                    raise DevAttemptControlError("private peer limit exceeded")
            for peer, buffer in peers:
                if peer not in ready:
                    continue
                data = peer.recv(MAX_CONTROL_BYTES + 4)
                if not data:
                    if buffer:
                        raise DevAttemptControlError("private control frame truncated")
                    if peer is self._peer:
                        self._eof = True
                    else:
                        self._secondary.pop(peer, None)
                        self._secondary_sequences.pop(peer, None)
                        peer.close()
                    continue
                buffer.extend(data)
                self._received_bytes += len(data)
                if self._received_bytes > MAX_CONTROL_WIRE_BYTES:
                    raise DevAttemptControlError("private control wire exceeds limit")
                if self._frame_available(buffer):
                    framed.append((peer, buffer))
        if not framed:
            return None
        peer, buffer = framed[0]
        size = struct.unpack("!I", buffer[:4])[0]
        line = bytes(buffer[4:4 + size])
        del buffer[:4 + size]
        try:
            control = DevAttemptControlV1.model_validate_json(line)
            self.secondary_control = peer is not self._peer
            if self.secondary_control and control.operation not in ("STATUS", "CANCEL", "EOF"):
                raise DevAttemptControlError("secondary private operation unavailable")
            self._reply_peer = peer
            return control
        except Exception:
            raise DevAttemptControlError("private control frame invalid") from None

    def eof(self) -> bool:
        return self._eof

    def discard_reply_peer(self) -> None:
        """Route the next lifecycle frame to the primary invocation peer."""
        self._reply_peer = None

    def send(self, frame: DevAttemptFrameV1) -> None:
        checked = frame.revalidated()
        peer = self._reply_peer or self._peer
        self._reply_peer = None
        if peer is None or checked.binding_sha256 != self.gate.identity.canonical_sha256():
            raise DevAttemptControlError("private output binding unavailable")
        if peer is not self._peer:
            sequence = self._secondary_sequences.get(peer, 0)
            checked = checked.model_copy(update={"sequence": sequence}).revalidated()
            self._secondary_sequences[peer] = sequence + 1
        data = encode_attempt_frame(checked)
        if len(data) > MAX_CONTROL_BYTES + 4:
            raise DevAttemptControlError("private output frame exceeds limit")
        if self._sent_bytes + len(data) > MAX_CONTROL_WIRE_BYTES:
            raise DevAttemptControlError("private output wire exceeds limit")
        # Every write is nonblocking; a bounded number of immediate attempts cannot
        # suspend the authoritative remote clock on a stalled reader.
        offset = 0
        for _ in range(MAX_CONTROL_BYTES + 4):
            try:
                sent = peer.send(data[offset:])
            except BlockingIOError:
                raise DevAttemptControlError("private output reader unavailable") from None
            if sent <= 0:
                raise DevAttemptControlError("private output frame incomplete")
            offset += sent
            if offset == len(data):
                self._sent_bytes += offset
                return
        raise DevAttemptControlError("private output frame incomplete")

    def close(self) -> None:
        for endpoint in (self._peer, self._listener, *self._secondary):
            if endpoint is not None:
                endpoint.close()
        self._peer = None
        self._listener = None
        self._secondary.clear()
        self._secondary_sequences.clear()
        self._buffer.clear()


@dataclass(frozen=True, slots=True)
class ProcessBirth:
    pid: int
    boot_id: str
    start_ticks: int

    def __post_init__(self) -> None:
        if type(self.pid) is not int or self.pid < 1 or type(self.start_ticks) is not int or self.start_ticks < 1:
            raise DevAttemptControlError("trusted process birth invalid")
        if type(self.boot_id) is not str or not self.boot_id or len(self.boot_id) > 128 or not self.boot_id.isascii() or not all(
            character.isalnum() or character == "-" for character in self.boot_id
        ):
            raise DevAttemptControlError("trusted boot identity unavailable")


@dataclass(frozen=True, slots=True)
class TrustedRegistration:
    birth: ProcessBirth
    role: Literal["SUPERVISOR", "ADAPTER", "GENERATION"]
    containment_identity: str
    parent_birth: ProcessBirth | None


@dataclass(frozen=True, slots=True)
class TrustedContainmentCapability:
    """Independently bound runtime facts; a cgroup directory cannot supply these."""

    identity: str
    kind: Literal["CGROUP_V2", "WINDOWS_JOB"]
    registration_authority_birth: ProcessBirth
    delegation_bound: bool
    prevents_escape: bool
    registration_isolated: bool

    def __post_init__(self) -> None:
        if self.kind not in ("CGROUP_V2", "WINDOWS_JOB") or type(self.registration_authority_birth) is not ProcessBirth:
            raise DevAttemptControlError("trusted containment capability invalid")


class KernelInspectionOps(Protocol):
    def birth(self, pid: int) -> ProcessBirth | None: ...
    def parent_birth(self, birth: ProcessBirth) -> ProcessBirth | None: ...
    def containment_capability(self, identity: str) -> TrustedContainmentCapability | None: ...
    def containment_members(self, identity: str) -> tuple[ProcessBirth, ...] | None: ...
    def contained(self, birth: ProcessBirth, identity: str) -> bool | None: ...
    def containment_kind(self, identity: str) -> str: ...
    def containment_births(self, identity: str) -> tuple[ProcessBirth, ...] | None: ...


@dataclass(slots=True)
class TrustedLaunchRegistry:
    """Parent-owned registration, independent of worker frames and PID declarations."""

    containment_identity: str = field(repr=False)
    ops: KernelInspectionOps = field(repr=False)
    invocation_identity: DevAttemptIdentityV1 = field(repr=False)
    registrations: list[TrustedRegistration] = field(default_factory=list, init=False, repr=False)
    invalid: bool = field(default=False, init=False)
    launches_sealed: bool = field(default=False, init=False)
    capability: TrustedContainmentCapability | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.invocation_identity = self.invocation_identity.revalidated()

    def _capability_valid(self) -> bool:
        actual = self.ops.containment_capability(self.containment_identity)
        if type(actual) is not TrustedContainmentCapability or (
            actual.identity != self.containment_identity
            or actual.kind != self.ops.containment_kind(self.containment_identity)
            or actual.delegation_bound is not True or actual.prevents_escape is not True
            or actual.registration_isolated is not True
            or self.ops.birth(actual.registration_authority_birth.pid) != actual.registration_authority_birth
            or self.ops.contained(actual.registration_authority_birth, self.containment_identity) is not False
        ):
            return False
        if self.capability is None:
            self.capability = actual
        return actual == self.capability

    def register(self, pid: int, role: Literal["SUPERVISOR", "ADAPTER", "GENERATION"],
                 parent_birth: ProcessBirth | None = None) -> TrustedRegistration:
        if self.launches_sealed or self.invalid or not self._capability_valid():
            self.invalid = True
            raise DevAttemptControlError("trusted containment capability unavailable")
        actual = self.ops.birth(pid)
        if type(actual) is not ProcessBirth or self.ops.contained(actual, self.containment_identity) is not True:
            self.invalid = True
            raise DevAttemptControlError("trusted launch registration unavailable")
        if any(item.birth.pid == pid for item in self.registrations):
            self.invalid = True
            raise DevAttemptControlError("trusted process birth reused")
        parent = next((item for item in self.registrations if item.birth == parent_birth), None)
        if role not in ("SUPERVISOR", "ADAPTER", "GENERATION") or (
            role == "SUPERVISOR" and (parent_birth is not None or any(item.role == role for item in self.registrations))
        ) or (
            role == "ADAPTER" and (parent is None or parent.role != "SUPERVISOR" or any(item.role == role for item in self.registrations))
        ) or (
            role == "GENERATION" and (parent is None or parent.role != "ADAPTER" or len([item for item in self.registrations if item.role == role]) >= 2)
        ):
            self.invalid = True
            raise DevAttemptControlError("trusted process parent unavailable")
        if parent is not None and (
            self.ops.birth(parent.birth.pid) != parent.birth
            or self.ops.contained(parent.birth, self.containment_identity) is not True
            or self.ops.parent_birth(actual) != parent.birth
            or self.ops.birth(pid) != actual
        ):
            self.invalid = True
            raise DevAttemptControlError("trusted kernel parent lineage unavailable")
        registration = TrustedRegistration(actual, role, self.containment_identity, parent_birth)
        self.registrations.append(registration)
        return registration

    def may_start(self) -> bool:
        try:
            supervisors = [item for item in self.registrations if item.role == "SUPERVISOR"]
            valid = (
                not self.invalid and not self.launches_sealed and self._capability_valid()
                and len(supervisors) == 1
                and self.ops.birth(supervisors[0].birth.pid) == supervisors[0].birth
                and self.ops.contained(supervisors[0].birth, self.containment_identity) is True
            )
        except Exception:
            valid = False
        if not valid:
            self.invalid = True
        return valid

    def live_failure(self, *, require_coverage: bool = True) -> DevAttemptFailureCode | None:
        """Read trusted coverage while releases remain possible, before cleanup."""
        if self.invalid or not self._capability_valid():
            return "REGISTRATION_INVALID"
        registered = {item.birth for item in self.registrations}
        if require_coverage:
            members = self.ops.containment_members(self.containment_identity)
            if members is None or not set(members) <= registered:
                self.invalid = True
                return "INSPECTION_INCOMPLETE"
        for item in self.registrations:
            actual = self.ops.birth(item.birth.pid)
            if actual is not None and actual != item.birth:
                self.invalid = True
                return "BIRTH_REUSED"
            if item.role == "SUPERVISOR" and actual is None:
                self.invalid = True
                return "SUPERVISOR_LOST"
            if actual is not None and self.ops.contained(actual, self.containment_identity) is not True:
                self.invalid = True
                return "CONTAINMENT_ESCAPE"
        return None


@dataclass(frozen=True, slots=True)
class InvocationInspection:
    outcome: Literal["VERIFIED_OFFLINE", "UNKNOWN", "FAILED"]
    failure_codes: tuple[DevAttemptFailureCode, ...]
    observed_at: float


@dataclass(slots=True)
class SeparateInvocationInspector:
    """An explicitly separate launch, outside the registered task containment."""

    ops: KernelInspectionOps = field(repr=False)
    inspector_birth: ProcessBirth = field(repr=False)
    clock: Callable[[], float] = field(repr=False)
    current_pid: Callable[[], int] = field(default=os.getpid, repr=False)
    gate: PrivateInvocationGate | None = field(default=None, repr=False)

    def inspect(self, registry: TrustedLaunchRegistry, deadline: float,
                expected_attempts: int | None = None) -> InvocationInspection:
        now = self.clock()
        codes: list[DevAttemptFailureCode] = []
        if type(now) not in (int, float) or not math.isfinite(now):
            return InvocationInspection("FAILED", ("CLOCK_INVALID",), 0.0)
        if not math.isfinite(deadline) or now >= deadline:
            return InvocationInspection("FAILED", ("CLEANUP_DEADLINE",), now)
        identity = registry.containment_identity
        if self.gate is not None and self.gate.identity != registry.invocation_identity:
            codes.append("IDENTITY_MISMATCH")
        if self.gate is None or self.gate.identity != registry.invocation_identity or not registry.launches_sealed:
            codes.append("INSPECTION_INCOMPLETE")
        else:
            try:
                if self.gate.state() not in ("EOF", "CANCEL"):
                    codes.append("INSPECTION_INCOMPLETE")
            except Exception:
                codes.append("PRIVATE_CHANNEL_UNSAFE")
        if self.current_pid() != self.inspector_birth.pid or self.ops.birth(self.inspector_birth.pid) != self.inspector_birth or (
            self.ops.contained(self.inspector_birth, identity) is not False
        ):
            codes.append("INSPECTION_INVALID")
        if registry.invalid or not registry.registrations:
            codes.append("REGISTRATION_INVALID")
        if not registry._capability_valid() or self.ops.containment_capability(identity) != registry.capability:
            codes.append("CONTAINMENT_UNAVAILABLE")
        members = self.ops.containment_members(identity)
        if members is None:
            codes.append("INSPECTION_INCOMPLETE")
        elif members:
            codes.append("CLEANUP_FAILED")
        history = self.ops.containment_births(identity)
        registered = tuple(item.birth for item in registry.registrations)
        if history is None or set(history) != set(registered) or len(registered) != len(set(registered)):
            codes.append("INSPECTION_INCOMPLETE")
        roles = {item.role for item in registry.registrations}
        if not {"SUPERVISOR", "ADAPTER"} <= roles:
            codes.append("INSPECTION_INCOMPLETE")
        if expected_attempts is None or len([
            item for item in registry.registrations if item.role == "GENERATION"
        ]) != expected_attempts:
            codes.append("INSPECTION_INCOMPLETE")
        for registration in registry.registrations:
            actual = self.ops.birth(registration.birth.pid)
            if actual is not None and actual != registration.birth:
                codes.append("BIRTH_REUSED")
            elif actual is not None:
                if self.ops.contained(actual, identity) is not True:
                    codes.append("CONTAINMENT_ESCAPE")
                else:
                    codes.append("CLEANUP_FAILED")
        observed = self.clock()
        if type(observed) not in (int, float) or not math.isfinite(observed) or observed < now:
            codes.append("CLOCK_INVALID")
            observed = now
        elif observed >= deadline:
            codes.append("CLEANUP_DEADLINE")
        unique = tuple(dict.fromkeys(codes))
        return InvocationInspection("FAILED" if unique else "VERIFIED_OFFLINE", unique, observed)


@dataclass(slots=True)
class LinuxKernelInspectionOps:
    """Read kernel birth and an explicitly selected cgroup; no PGID-only proof."""

    cgroup_path: Path = field(repr=False)
    expected_inode: tuple[int, int]
    read_text: Callable[[Path], str] = field(default=lambda path: path.read_text(encoding="ascii"), repr=False)
    trusted_capability_check: Callable[[Path, tuple[int, int]], TrustedContainmentCapability | None] | None = field(default=None, repr=False)
    trusted_birth_history: Callable[[Path, tuple[int, int]], tuple[ProcessBirth, ...] | None] | None = field(default=None, repr=False)

    def birth(self, pid: int) -> ProcessBirth | None:
        if type(pid) is not int or pid < 1:
            raise DevAttemptControlError("kernel process target invalid")
        try:
            boot = self.read_text(Path("/proc/sys/kernel/random/boot_id")).strip()
        except OSError:
            raise DevAttemptControlError("kernel boot identity unavailable") from None
        try:
            status = self.read_text(Path(f"/proc/{pid}/stat"))
        except FileNotFoundError:
            return None
        if not status.startswith(f"{pid} (") or ")" not in status:
            raise DevAttemptControlError("kernel process identity unavailable")
        suffix = status[status.rfind(")") + 2:].split()
        try:
            return ProcessBirth(pid, boot, int(suffix[19]))
        except (IndexError, ValueError):
            raise DevAttemptControlError("kernel process birth unavailable") from None

    def _valid_cgroup(self, identity: str) -> bool:
        if identity != str(self.cgroup_path) or not self.cgroup_path.is_absolute():
            return False
        try:
            facts = self.cgroup_path.lstat()
            if stat.S_ISLNK(facts.st_mode) or not stat.S_ISDIR(facts.st_mode):
                return False
            if (facts.st_dev, facts.st_ino) != self.expected_inode:
                return False
            return "populated " in self.read_text(self.cgroup_path / "cgroup.events")
        except OSError:
            return False

    def parent_birth(self, birth: ProcessBirth) -> ProcessBirth | None:
        if self.birth(birth.pid) != birth:
            return None
        try:
            status = self.read_text(Path(f"/proc/{birth.pid}/stat"))
            suffix = status[status.rfind(")") + 2:].split()
            parent = self.birth(int(suffix[1]))
            return parent if self.birth(birth.pid) == birth else None
        except (OSError, IndexError, ValueError):
            return None

    def containment_capability(self, identity: str) -> TrustedContainmentCapability | None:
        if not self._valid_cgroup(identity) or self.trusted_capability_check is None:
            return None
        capability = self.trusted_capability_check(self.cgroup_path, self.expected_inode)
        if type(capability) is not TrustedContainmentCapability or capability.identity != identity:
            return None
        return capability

    def containment_kind(self, identity: str) -> str:
        # Directory existence is not delegation, escape prevention or isolated
        # trusted-parent registration. No concrete runtime capability is bound here.
        capability = self.containment_capability(identity)
        return "CGROUP_V2" if capability is not None and capability.kind == "CGROUP_V2" else "UNBOUND"

    def containment_births(self, identity: str) -> tuple[ProcessBirth, ...] | None:
        if not self._valid_cgroup(identity) or self.trusted_birth_history is None:
            return None
        history = self.trusted_birth_history(self.cgroup_path, self.expected_inode)
        return history if type(history) is tuple and all(type(item) is ProcessBirth for item in history) else None

    def containment_members(self, identity: str) -> tuple[ProcessBirth, ...] | None:
        if not self._valid_cgroup(identity):
            return None
        # An empty parent cgroup.procs is insufficient: cgroup.events populated
        # includes child cgroups. Refuse populated hierarchy even if this file is empty.
        events = dict(line.split() for line in self.read_text(self.cgroup_path / "cgroup.events").splitlines())
        pids = self.read_text(self.cgroup_path / "cgroup.procs").split()
        if events.get("populated") != "0":
            # cgroup.procs lists this group only. A populated hierarchy cannot be
            # called complete without a separately bound recursive census.
            return None
        if pids:
            return None
        if not self._valid_cgroup(identity) or dict(
            line.split() for line in self.read_text(self.cgroup_path / "cgroup.events").splitlines()
        ).get("populated") != "0":
            return None
        return ()

    def contained(self, birth: ProcessBirth, identity: str) -> bool | None:
        if not self._valid_cgroup(identity) or self.birth(birth.pid) != birth:
            return None
        lines = self.read_text(Path(f"/proc/{birth.pid}/cgroup")).splitlines()
        try:
            selected = self.cgroup_path.relative_to(Path("/sys/fs/cgroup")).as_posix()
        except ValueError:
            return None
        expected = "/" + selected
        memberships = [line[3:] for line in lines if line.startswith("0::")]
        return any(value == expected or value.startswith(expected + "/") for value in memberships)


class BoundedAdapterInvocation(Protocol):
    def __call__(self, *, on_accepted_progress: Callable[[ProgressEvent], None],
                 cancel_requested: Callable[[], bool], on_cleanup_intent: Callable[[], float],
                 cleanup_deadline: Callable[[], float | None],
                 register_launch: Callable[..., TrustedRegistration],
                 launch_parent_birth: ProcessBirth, release_guard: Callable[[Callable[[], None]], None],
                 work_deadline: float) -> SupervisorRunResult: ...


@dataclass(slots=True)
class ExistingBoundedAdapterInvocation:
    """Bind one existing bounded adapter entry; no second runner or retry owner."""

    request: VisionUnderstandingRequestV2 = field(repr=False)
    runtime_config: QwenVisionRuntimeConfig = field(repr=False)
    content_policy: ObservableContentPolicyV1 = field(repr=False)
    prompt: str = field(repr=False)
    config: Feat018BoundedRunnerConfig
    session_id: str = field(repr=False)
    clock: Callable[[], float] = field(repr=False)
    sleep: Callable[[float], None] = field(repr=False)
    _invoked: bool = field(default=False, init=False)

    def __call__(self, *, on_accepted_progress: Callable[[ProgressEvent], None],
                 cancel_requested: Callable[[], bool], on_cleanup_intent: Callable[[], float],
                 cleanup_deadline: Callable[[], float | None],
                 register_launch: Callable[..., TrustedRegistration],
                 launch_parent_birth: ProcessBirth, release_guard: Callable[[Callable[[], None]], None],
                 work_deadline: float) -> SupervisorRunResult:
        if self._invoked:
            raise DevAttemptControlError("bounded adapter invocation already used")
        remaining = work_deadline - self.clock()
        if not math.isfinite(remaining) or remaining <= 0:
            raise DevAttemptControlError("bounded adapter work deadline expired")
        self._invoked = True
        config = replace(self.config, total_adapter_cap_seconds=min(
            self.config.total_adapter_cap_seconds, remaining,
        ))
        return run_bounded_adapter_call(
            self.request, self.runtime_config, self.content_policy, self.prompt, config,
            session_id=self.session_id, verify_development_results=True,
            cancel_requested=cancel_requested, on_accepted_progress=on_accepted_progress,
            on_cleanup_intent=on_cleanup_intent, cleanup_deadline=cleanup_deadline,
            register_launch=register_launch, launch_parent_birth=launch_parent_birth,
            release_guard=release_guard, clock=self.clock, sleep=self.sleep,
            work_deadline_monotonic=work_deadline,
        )


@dataclass(slots=True)
class OfflineDevAttemptCoordinator:
    """Compose one injected existing bounded call; no default real effects."""

    identity: DevAttemptIdentityV1 = field(repr=False)
    budgets: DevAttemptBudgetsV1
    gate: PrivateInvocationGate = field(repr=False)
    controls: ControlSource = field(repr=False)
    bounded_adapter: BoundedAdapterInvocation = field(repr=False)
    registry: TrustedLaunchRegistry = field(repr=False)
    inspector: SeparateInvocationInspector | None = field(repr=False)
    clock: Callable[[], float] = field(repr=False)
    max_polls: int = MAX_CONTROL_POLLS
    work_deadline: float | None = field(default=None, init=False)
    terminal_cleanup_deadline: float | None = field(default=None, init=False)
    _cancelled: bool = field(default=False, init=False)
    _invoked: bool = field(default=False, init=False)
    _adapter_count: int | None = field(default=0, init=False)
    _sequence: int = field(default=-1, init=False)
    _last_control_sequence: int = field(default=-1, init=False)
    _received_control_frames: int = field(default=0, init=False)
    _idle_polls_without_clock_progress: int = field(default=0, init=False)
    _codes: list[DevAttemptFailureCode] = field(default_factory=list, init=False, repr=False)
    _machine: Feat018ProgressStateMachine | None = field(default=None, init=False, repr=False)
    _containment_sent: bool = field(default=False, init=False)
    _last_time: float | None = field(default=None, init=False)
    retained_supervisor_result: SupervisorRunResult | None = field(default=None, init=False, repr=False)
    retained_cleanup_error: Exception | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.identity = self.identity.revalidated()
        self.budgets = self.budgets.revalidated()
        if self.identity != self.gate.identity or self.identity != self.registry.invocation_identity or (
            self.inspector is not None and (self.inspector.gate is None or self.inspector.gate.identity != self.identity)
        ) or not 1 <= self.max_polls <= MAX_CONTROL_POLLS:
            raise DevAttemptControlError("offline invocation binding invalid")

    def begin_cleanup(self) -> float:
        if self.terminal_cleanup_deadline is None:
            now = self._now()
            anchor = min(now, self.work_deadline) if self.work_deadline is not None else now
            self.terminal_cleanup_deadline = anchor + self.budgets.cleanup_seconds
            if not math.isfinite(self.terminal_cleanup_deadline) or self.terminal_cleanup_deadline <= anchor:
                self.terminal_cleanup_deadline = 0.0
                raise DevAttemptControlError("remote cleanup deadline invalid")
            self.registry.launches_sealed = True
            try:
                self.gate.seal()
            except FileNotFoundError:
                if self._invoked:
                    self.registry.invalid = True
                    self._codes.append("PRIVATE_CHANNEL_UNSAFE")
            except Exception:
                self.registry.invalid = True
                self._codes.append("PRIVATE_CHANNEL_UNSAFE")
        return self.terminal_cleanup_deadline

    def _now(self) -> float:
        try:
            now = self.clock()
        except Exception:
            raise DevAttemptControlError("remote monotonic clock unavailable") from None
        if type(now) not in (int, float) or not math.isfinite(now) or (
            self._last_time is not None and now < self._last_time
        ):
            raise DevAttemptControlError("remote monotonic clock invalid")
        self._last_time = float(now)
        return self._last_time

    def release_guard(self, release: Callable[[], None]) -> None:
        if self.cancel_requested() or self.terminal_cleanup_deadline is not None:
            raise DevAttemptControlError("invocation release frozen")
        failure = self.registry.live_failure()
        if failure is not None:
            self._freeze(failure)
            raise DevAttemptControlError("trusted invocation release unavailable")
        self.gate.release_guard(release)
        if not self._containment_sent:
            self._containment_sent = True
            self._send("PROGRESS", progress="CONTAINMENT_READY")

    def _send(self, kind: str, *, summary: DevAttemptSummaryV1 | None = None,
              progress: str | None = None, attempt_number: int | None = None) -> None:
        if kind not in ("STATUS", "CANCEL_ACK"):
            self._discard_control_reply_peer()
        secondary_reply = (
            isinstance(self.controls, PrivateControlSocket)
            and self.controls._reply_peer is not None
            and self.controls._reply_peer is not self.controls._peer
        )
        if not secondary_reply:
            self._sequence += 1
        self.controls.send(DevAttemptFrameV1(
            kind=kind, binding_sha256=self.identity.canonical_sha256(), sequence=0 if secondary_reply else self._sequence,
            summary=summary, progress=progress, attempt_number=attempt_number,
        ))

    def _freeze(self, code: DevAttemptFailureCode) -> None:
        self._cancelled = True
        if code not in self._codes:
            self._codes.append(code)
        try:
            self.begin_cleanup()
        except DevAttemptControlError:
            if "CLOCK_INVALID" not in self._codes:
                self._codes.append("CLOCK_INVALID")
            self.terminal_cleanup_deadline = 0.0
            self.registry.launches_sealed = True
        if self._machine is not None:
            self._machine.force_freeze()
        try:
            self.gate.transition(DevAttemptControlV1(identity=self.identity, operation="CANCEL"))
        except Exception:
            if "PRIVATE_CHANNEL_UNSAFE" not in self._codes:
                self._codes.append("PRIVATE_CHANNEL_UNSAFE")
            if "CANCEL_FAILED" not in self._codes:
                self._codes.append("CANCEL_FAILED")

    def _discard_control_reply_peer(self) -> None:
        if isinstance(self.controls, PrivateControlSocket):
            self.controls.discard_reply_peer()

    def _poll(self) -> DevAttemptControlV1 | None:
        try:
            deadline = self.terminal_cleanup_deadline if self.terminal_cleanup_deadline is not None else self.work_deadline
            before_poll = self._now()
            remaining = max(0.0, deadline - before_poll) if deadline is not None else 0.0
            raw = self.controls.poll(max(0.0, min(self.budgets.poll_seconds, remaining)))
            after_poll = self._now()
            if raw is None:
                if after_poll <= before_poll:
                    self._idle_polls_without_clock_progress += 1
                    if self._idle_polls_without_clock_progress > self.max_polls:
                        self._freeze("FRAME_LIMIT")
                else:
                    self._idle_polls_without_clock_progress = 0
            else:
                self._idle_polls_without_clock_progress = 0
                self._received_control_frames += 1
                if self._received_control_frames > self.max_polls:
                    self._freeze("FRAME_LIMIT")
                    return None
            if self.controls.eof():
                self._freeze("CONTROL_EOF")
                return None
            if raw is None:
                return None
            control = (DevAttemptControlV1.model_validate_json(raw) if isinstance(raw, bytes)
                       else raw.revalidated())
            secondary = isinstance(self.controls, PrivateControlSocket) and self.controls.secondary_control
            if control.identity != self.identity or (not secondary and control.sequence <= self._last_control_sequence):
                self._discard_control_reply_peer()
                self._freeze("IDENTITY_MISMATCH" if control.identity != self.identity else "CONTROL_INVALID")
                return None
            if not secondary:
                self._last_control_sequence = control.sequence
            if control.operation in ("CANCEL", "EOF"):
                self.gate.transition(control)
                self._freeze("CANCELLED" if control.operation == "CANCEL" else "CONTROL_EOF")
                self._send("CANCEL_ACK", summary=DevAttemptSummaryV1(
                    outcome="CANCELLED", adapter_call_count=self._adapter_count,
                    attempt_count=self._machine.attempt_count if self._machine else None,
                    ownership_retained=self._invoked,
                ))
            elif control.operation == "STATUS":
                self._send("STATUS", summary=self._running_summary())
            elif control.operation == "START" and self._invoked:
                self._freeze("START_REUSED")
            elif self._invoked and control.operation in ("OPEN", "INSPECT"):
                self._discard_control_reply_peer()
                self._freeze("CONTROL_INVALID")
            return control
        except Exception:
            self._discard_control_reply_peer()
            self._freeze("CONTROL_INVALID")
            return None

    def _running_summary(self) -> DevAttemptSummaryV1:
        return DevAttemptSummaryV1(
            outcome="RUNNING", adapter_call_count=self._adapter_count,
            attempt_count=self._machine.attempt_count if self._machine else None,
            ownership_retained=self._invoked,
        )

    def cancel_requested(self) -> bool:
        try:
            now = self._now()
        except DevAttemptControlError:
            self._freeze("CLOCK_INVALID")
            return True
        if self.work_deadline is None or now >= self.work_deadline:
            self._freeze("WORK_DEADLINE")
        if self.terminal_cleanup_deadline is None or now < self.terminal_cleanup_deadline:
            self._poll()
        try:
            if self.gate.state() == "CANCEL" and not self._cancelled:
                self._freeze("CANCELLED")
        except Exception:
            self._freeze("PRIVATE_CHANNEL_UNSAFE")
        if self.terminal_cleanup_deadline is None:
            try:
                failure = self.registry.live_failure(require_coverage=False)
            except Exception:
                failure = "REGISTRATION_INVALID"
            if failure is not None:
                self._freeze(failure)
        return self._cancelled

    def accepted_progress(self, event: ProgressEvent) -> None:
        if self._machine is None or self._cancelled or (
            self.terminal_cleanup_deadline is not None and (
                event.kind is not ProgressEventKind.TERMINAL or self._now() >= self.terminal_cleanup_deadline
            )
        ):
            raise DevAttemptControlError("progress after invocation freeze")
        if not self._containment_sent:
            self._freeze("PROTOCOL_FAILED")
            raise DevAttemptControlError("progress before trusted release")
        if self._machine.accept(event, acceptance_time=self._now()) is not AcceptanceResult.ACCEPTED:
            self._freeze("PROTOCOL_FAILED")
            raise DevAttemptControlError("progress rejected")
        if event.kind is ProgressEventKind.ADAPTER_STARTED:
            self._adapter_count = 1
        self._send("PROGRESS", progress=event.kind.value, attempt_number=event.attempt_number)

    def run(self) -> DevAttemptSummaryV1:
        if self.identity != self.gate.identity or self.identity != self.registry.invocation_identity or (
            self.inspector is not None and (self.inspector.gate is None or self.inspector.gate.identity != self.identity)
        ):
            return DevAttemptSummaryV1(outcome="UNKNOWN", cleanup="UNKNOWN", ownership_retained=True,
                                       adapter_call_count=self._adapter_count, failure_codes=("IDENTITY_MISMATCH",))
        if self.work_deadline is not None:
            return DevAttemptSummaryV1(
                outcome="UNKNOWN", cleanup="UNKNOWN", adapter_call_count=self._adapter_count,
                ownership_retained=True, failure_codes=("CLAIM_REUSED",),
            )
        try:
            initial = self._now()
            deadline = initial + self.budgets.work_seconds
            if not math.isfinite(deadline) or deadline <= initial:
                raise DevAttemptControlError("remote work deadline invalid")
            self.work_deadline = deadline
        except DevAttemptControlError:
            return DevAttemptSummaryV1(outcome="UNKNOWN", failure_codes=("CLOCK_INVALID",))
        self._machine = Feat018ProgressStateMachine(cap_deadline_monotonic=self.work_deadline)
        result: SupervisorRunResult | None = None
        try:
            opened = False
            while not self._cancelled and self._now() < self.work_deadline:
                control = self._poll()
                if control is not None and control.operation == "OPEN" and not opened:
                    if isinstance(self.controls, PrivateControlSocket) and self.controls.gate is self.gate:
                        if self.controls._listener is None or self.gate.state() != "OPEN":
                            raise DevAttemptControlError("private socket not admitted")
                    else:
                        self.gate.transition(control)
                    opened = True
                    self._send("READY")
                    continue
                if control is not None and control.operation == "START":
                    if not opened or not self.registry.may_start():
                        self._freeze("CONTAINMENT_UNAVAILABLE")
                        break
                    self.gate.transition(control)
                    self._invoked = True
                    # Starting transport/call ownership is distinct from receiving an
                    # accepted ADAPTER_STARTED event. A lost event is UNKNOWN, not zero.
                    self._adapter_count = None
                    result = self.bounded_adapter(
                        on_accepted_progress=self.accepted_progress,
                        cancel_requested=self.cancel_requested,
                        on_cleanup_intent=self.begin_cleanup,
                        cleanup_deadline=lambda: self.terminal_cleanup_deadline,
                        register_launch=self.registry.register,
                        launch_parent_birth=next(item.birth for item in self.registry.registrations if item.role == "SUPERVISOR"),
                        release_guard=self.release_guard, work_deadline=self.work_deadline,
                    )
                    break
                if control is not None and control.operation not in ("STATUS", "CANCEL", "EOF"):
                    self._freeze("CONTROL_INVALID")
            if not self._invoked and not self._cancelled:
                self._freeze("WORK_DEADLINE")
        except Exception as error:
            if self._invoked:
                self.retained_cleanup_error = error
            self._freeze("CLAIM_REUSED" if self._adapter_count == 0 else "ADAPTER_FAILED")
        if result is not None and type(result) is not SupervisorRunResult:
            self._freeze("PROTOCOL_FAILED")
            result = None
        if self._invoked:
            self.retained_supervisor_result = result
        try:
            deadline = self.begin_cleanup()
        except DevAttemptControlError:
            self._freeze("CLOCK_INVALID")
            deadline = self.terminal_cleanup_deadline if self.terminal_cleanup_deadline is not None else 0.0
        codes = list(self._codes)
        inspection = None
        if self._invoked and self.inspector is not None:
            try:
                inspection = self.inspector.inspect(
                    self.registry, deadline,
                    self._machine.attempt_count if self._machine else None,
                )
            except Exception:
                codes.append("INSPECTION_INVALID")
        elif self._invoked:
            codes.append("INSPECTION_MISSING")
        if inspection is not None:
            codes.extend(inspection.failure_codes)
        try:
            cleanup_expired = self._now() >= deadline
        except DevAttemptControlError:
            cleanup_expired = True
            codes.append("CLOCK_INVALID")
        if cleanup_expired:
            codes.append("CLEANUP_DEADLINE")
        verified = inspection is not None and inspection.outcome == "VERIFIED_OFFLINE"
        if result is not None and result.cleanup_status is not CleanupStatus.SUCCEEDED:
            codes.append("CLEANUP_FAILED")
            verified = False
        if self._invoked and result is None:
            codes.append("SUPERVISOR_LOST")
            verified = False
        attempt_count = self._machine.attempt_count if self._machine else None
        verification = getattr(result, "verification_summary", None) if result is not None else None
        if result is not None and (
            result.attempt_count != attempt_count
            or result.effective_outcome is not EffectiveOutcome.SUCCEEDED
            or verification is None
        ):
            codes.append("ADAPTER_FAILED")
        if verification is not None:
            try:
                verification = verification.revalidated()
            except Exception:
                verification = None
                codes.append("PROTOCOL_FAILED")
                verified = False
        if result is not None and self._machine is not None and (
            result.final_state is not self._machine.state
            or result.terminal_outcome != self._machine.terminal_outcome
            or result.raw_status != self._machine.raw_status
            or result.attempt_count != attempt_count
        ):
            codes.append("PROTOCOL_FAILED")
            verified = False
        if result is not None and result.effective_outcome is EffectiveOutcome.SUCCEEDED and (
            self._machine is None or self._machine.terminal_outcome != "SUCCEEDED"
            or self._machine.raw_status != "SUCCEEDED" or verification is None
            or verification.v2_status != "SUCCEEDED" or verification.raw_status != "SUCCEEDED"
        ):
            codes.append("PROTOCOL_FAILED")
            verified = False
        if not self._invoked:
            # Cancellation without a START owns a sealed identity but no launched resource.
            retained = self.registry.invalid or "CLAIM_REUSED" in codes
            cleanup = "UNKNOWN" if retained else "NOT_REACHED"
            outcome = "CANCELLED" if self._cancelled and not retained else "UNKNOWN"
            if "CANCELLED" in codes:
                codes[codes.index("CANCELLED")] = "CANCELLED_BEFORE_START"
        else:
            cleanup = "VERIFIED_OFFLINE" if verified else "UNKNOWN"
            retained = not verified
            cleanup_failed = result is not None and result.cleanup_status is CleanupStatus.CLEANUP_FAILED
            outcome = "FAILED" if cleanup_failed else (
                "SUCCEEDED" if verified and not codes else "CANCELLED" if self._cancelled else "FAILED"
            )
        summary = DevAttemptSummaryV1(
            outcome=outcome, cleanup=cleanup, adapter_call_count=self._adapter_count,
            attempt_count=attempt_count, verification=verification,
            ownership_retained=retained, failure_codes=tuple(dict.fromkeys(codes))[:16],
        )
        if retained:
            self.retained_supervisor_result = result
        else:
            self.retained_supervisor_result = None
            self.retained_cleanup_error = None
        try:
            self._send("TERMINAL", summary=summary)
        except Exception:
            if self._invoked:
                self.retained_supervisor_result = result
                return DevAttemptSummaryV1(
                    outcome="UNKNOWN", cleanup="UNKNOWN", adapter_call_count=self._adapter_count,
                    attempt_count=attempt_count, verification=verification,
                    ownership_retained=True, failure_codes=tuple(dict.fromkeys((*codes, "TRANSPORT_LOST")))[:16],
                )
        return summary


def main() -> int:
    # No parser or argument may turn the public CLI into a live authorization gate.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
