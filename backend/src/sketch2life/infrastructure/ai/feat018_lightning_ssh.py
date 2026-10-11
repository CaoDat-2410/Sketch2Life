"""Fixed native SSH development transport, exercised only with explicit offline I/O.

The public entry never starts SSH and denies live effects. The offline
exchange can assess transport continuity, but cannot prove remote task or Studio
cleanup from a peer's terminal label.
"""

from __future__ import annotations

import math
import queue
import re
import struct
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Protocol

from sketch2life.contracts.schemas.feat018_live_binding import (
    DevAttemptBudgetsV1,
    DevAttemptControlV1,
    DevAttemptFrameV1,
    DevAttemptSummaryV1,
)


MAX_FRAME_BYTES = 16_384
MAX_WIRE_BYTES = 98_304
MAX_STDERR_BYTES = 32_768
MAX_POLLS = 1_024
_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_STUDIO_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_REMOTE_PYTHON = re.compile(r"^/[A-Za-z0-9_./-]{1,255}$")
_REMOTE_MODULE = "sketch2life.interfaces.cli.feat018_lightning_dev_attempt"


class SshBoundaryError(ValueError):
    """Only a closed failure code is exposed; private transport values stay local."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class PrivateSshArgv(tuple):
    """Native arguments remain available to the trusted launcher, not repr/logs."""

    def __repr__(self) -> str:
        return "PrivateSshArgv(<private>)"

    def __str__(self) -> str:
        return "PrivateSshArgv(<private>)"


@dataclass(frozen=True, slots=True, repr=False)
class TrustedSshBinding:
    """Private immutable configuration; hashes require an explicit trusted checker."""

    binary_path: str
    identity_file: str
    known_hosts_file: str
    remote_python: str
    studio_id: str
    binary_sha256: str
    known_hosts_sha256: str
    host_key_sha256: str
    python_sha256: str

    def __repr__(self) -> str:
        return "TrustedSshBinding(<private>)"


def _validated_binding(binding: TrustedSshBinding) -> TrustedSshBinding:
    if type(binding) is not TrustedSshBinding:
        raise SshBoundaryError("SSH_BINDING_INVALID")
    for path in (binding.binary_path, binding.identity_file, binding.known_hosts_file):
        if (
            type(path) is not str
            or not 1 <= len(path) <= 4_096
            or any(character in path for character in "\x00\r\n%$~")
            or not (PurePosixPath(path).is_absolute() or PureWindowsPath(path).is_absolute())
        ):
            raise SshBoundaryError("SSH_BINDING_INVALID")
    if any(character.isspace() or character in "\"'" for character in binding.known_hosts_file):
        # OpenSSH parses this option as a list of paths. Bind exactly one file.
        raise SshBoundaryError("SSH_BINDING_INVALID")
    if (
        type(binding.studio_id) is not str
        or _STUDIO_ID.fullmatch(binding.studio_id) is None
        or type(binding.remote_python) is not str
        or _REMOTE_PYTHON.fullmatch(binding.remote_python) is None
        or ".." in PurePosixPath(binding.remote_python).parts
    ):
        raise SshBoundaryError("SSH_BINDING_INVALID")
    for value in (
        binding.binary_sha256, binding.known_hosts_sha256,
        binding.host_key_sha256, binding.python_sha256,
    ):
        if type(value) is not str or _DIGEST.fullmatch(value) is None:
            raise SshBoundaryError("SSH_BINDING_INVALID")
    return binding


def build_native_ssh_argv(binding: TrustedSshBinding) -> tuple[str, ...]:
    """Build a private argv tuple without reading keys, config, or launching a process."""
    checked = _validated_binding(binding)
    options = (
        "BatchMode=yes", "StrictHostKeyChecking=yes",
        f"UserKnownHostsFile={checked.known_hosts_file}", "GlobalKnownHostsFile=none",
        "IdentitiesOnly=yes", "IdentityAgent=none", "ForwardAgent=no",
        "ForwardX11=no", "ClearAllForwardings=yes", "ControlMaster=no",
        "ControlPath=none", "ControlPersist=no", "PermitLocalCommand=no",
        "ProxyCommand=none", "ProxyJump=none", "RemoteCommand=none",
        "RequestTTY=no", "NumberOfPasswordPrompts=0",
        "UpdateHostKeys=no",
    )
    argv = [checked.binary_path, "-F", "none", "-T", "-i", checked.identity_file]
    for option in options:
        argv.extend(("-o", option))
    argv.extend((
        f"s_{checked.studio_id}@ssh.lightning.ai",
        f"{checked.remote_python} -I -B -m {_REMOTE_MODULE} session",
    ))
    return PrivateSshArgv(argv)


def _encode(value: DevAttemptControlV1 | DevAttemptFrameV1) -> bytes:
    try:
        payload = value.revalidated().canonical_bytes()
    except Exception:
        raise SshBoundaryError("FRAME_INVALID") from None
    if not 1 <= len(payload) <= MAX_FRAME_BYTES:
        raise SshBoundaryError("FRAME_LIMIT_EXCEEDED")
    return struct.pack("!I", len(payload)) + payload


def encode_control_frame(control: DevAttemptControlV1) -> bytes:
    if type(control) is not DevAttemptControlV1:
        raise SshBoundaryError("FRAME_INVALID")
    return _encode(control)


def encode_attempt_frame(frame: DevAttemptFrameV1) -> bytes:
    if type(frame) is not DevAttemptFrameV1:
        raise SshBoundaryError("FRAME_INVALID")
    return _encode(frame)


class IncrementalFrameDecoder:
    """A bounded, non-resettable stream decoder using protected JSON ingress."""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self._wire_bytes = 0
        self._failure: str | None = None

    def __repr__(self) -> str:
        return "IncrementalFrameDecoder(<private>)"

    def _fail(self, code: str) -> None:
        self._buffer.clear()
        self._failure = code
        raise SshBoundaryError(code)

    def feed(self, data: bytes) -> tuple[DevAttemptFrameV1, ...]:
        if self._failure is not None:
            raise SshBoundaryError(self._failure)
        if type(data) is not bytes:
            self._fail("FRAME_INVALID")
        self._wire_bytes += len(data)
        if self._wire_bytes > MAX_WIRE_BYTES:
            self._fail("FRAME_LIMIT_EXCEEDED")
        self._buffer.extend(data)
        frames = []
        while len(self._buffer) >= 4:
            length = struct.unpack("!I", self._buffer[:4])[0]
            if not 1 <= length <= MAX_FRAME_BYTES:
                self._fail("FRAME_LIMIT_EXCEEDED")
            if len(self._buffer) < length + 4:
                break
            payload = bytes(self._buffer[4:length + 4])
            del self._buffer[:length + 4]
            try:
                frame = DevAttemptFrameV1.model_validate_json(payload)
            except Exception:
                self._fail("FRAME_INVALID")
            frames.append(frame)
        return tuple(frames)

    def eof(self) -> None:
        if self._failure is not None:
            raise SshBoundaryError(self._failure)
        if self._buffer:
            self._fail("FRAME_INVALID")


@dataclass(frozen=True, slots=True, repr=False)
class SshPollResult:
    stdout: bytes = b""
    stderr: bytes = b""
    eof: bool = False

    def __repr__(self) -> str:
        return "SshPollResult(<private>)"


class NativeSshIo(Protocol):
    """Explicit offline double: multiplexes stdout/stderr while writes remain serviced."""

    def write(self, data: bytes) -> None: ...
    def poll(self, timeout_seconds: float, max_bytes: int) -> SshPollResult: ...
    def close(self) -> None: ...


class LocalSshOwner:
    """Caller-owned private channel; failed local cleanup never drops its handle."""

    def __init__(self) -> None:
        self._channel: NativeSshIo | None = None
        self._claimed = False
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return "LocalSshOwner(<private>)"

    @property
    def claimed(self) -> bool:
        with self._lock:
            return self._claimed

    @property
    def retained(self) -> bool:
        with self._lock:
            return self._channel is not None

    def claim(self, channel: NativeSshIo) -> None:
        with self._lock:
            if self._claimed and self._channel is not channel:
                raise SshBoundaryError("SSH_IO_FAILED")
            self._channel = channel
            self._claimed = True

    def close(self) -> None:
        with self._lock:
            if self._channel is None:
                return
            try:
                self._channel.close()
            except Exception:
                raise SshBoundaryError("SSH_IO_FAILED") from None
            self._channel = None


class NativeSshProcessIo:
    """Concrete pipe transport with an explicit launcher and finite local watchdogs.

    There is no default launcher. Tests supply a fake process; public entries
    cannot reach this class. Stopping this local process proves no remote cleanup.
    """

    def __init__(
        self,
        argv: tuple[str, ...],
        *,
        local_owner: LocalSshOwner,
        clock: Callable[[], float],
        popen_factory: Callable[..., object],
        write_timeout_seconds: float,
        close_timeout_seconds: float,
    ) -> None:
        self._process: object | None = None
        self._closed = False
        self._stop = threading.Event()
        self._read_events: queue.Queue[tuple[str, bytes | None]] = queue.Queue(maxsize=8)
        self._write_events: queue.Queue[tuple[bytes, threading.Event]] = queue.Queue(maxsize=2)
        self._threads: list[threading.Thread] = []
        self._eof_streams: set[str] = set()
        self._pending = {"stdout": bytearray(), "stderr": bytearray()}
        self._error = False
        self._write_lock = threading.Lock()
        self._poll_lock = threading.Lock()
        self._close_lock = threading.Lock()
        self._close_failed = False
        self._close_deadline: float | None = None
        self._clock = clock
        self._clock_lock = threading.Lock()
        self._last_clock: float | None = None
        for value in (write_timeout_seconds, close_timeout_seconds):
            if type(value) is not float or not math.isfinite(value) or not 0 < value <= 30.0:
                raise SshBoundaryError("SSH_BINDING_INVALID")
        if (
            type(argv) is not PrivateSshArgv or type(local_owner) is not LocalSshOwner
            or local_owner.claimed
        ):
            raise SshBoundaryError("SSH_BINDING_INVALID")
        self._write_timeout = write_timeout_seconds
        self._close_timeout = close_timeout_seconds
        initial_time = self._now()
        if (
            not math.isfinite(initial_time + self._close_timeout)
            or initial_time + min(self._close_timeout, self._write_timeout) <= initial_time
        ):
            raise SshBoundaryError("CLOCK_INVALID")
        local_owner.claim(self)
        try:
            self._process = popen_factory(
                argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False, bufsize=0, close_fds=True, env={},
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            for stream in ("stdin", "stdout", "stderr"):
                if getattr(self._process, stream, None) is None:
                    raise SshBoundaryError("SSH_IO_FAILED")
            for name in ("stdout", "stderr"):
                thread = threading.Thread(target=self._read_stream, args=(name,), daemon=True)
                self._threads.append(thread)
                thread.start()
            writer = threading.Thread(target=self._write_stream, daemon=True)
            self._threads.append(writer)
            writer.start()
        except Exception:
            try:
                local_owner.close()
            except Exception:
                pass
            raise SshBoundaryError("SSH_IO_FAILED") from None

    def __repr__(self) -> str:
        return "NativeSshProcessIo(<private>)"

    def _now(self) -> float:
        with self._clock_lock:
            try:
                value = self._clock()
            except Exception:
                raise SshBoundaryError("CLOCK_INVALID") from None
            if (
                type(value) not in (int, float) or not math.isfinite(value)
                or (self._last_clock is not None and value < self._last_clock)
            ):
                raise SshBoundaryError("CLOCK_INVALID")
            self._last_clock = float(value)
            return self._last_clock

    def _offer_read(self, name: str, value: bytes | None) -> None:
        while not self._stop.is_set():
            try:
                self._read_events.put((name, value), timeout=0.01)
                return
            except queue.Full:
                continue

    def _read_stream(self, name: str) -> None:
        try:
            stream = getattr(self._process, name)
            while not self._stop.is_set():
                chunk = stream.read(4_096)
                if type(chunk) is not bytes or len(chunk) > 4_096:
                    self._error = True
                    return
                if not chunk:
                    self._offer_read(name, None)
                    return
                self._offer_read(name, chunk)
        except Exception:
            self._error = True

    def _write_stream(self) -> None:
        while not self._stop.is_set():
            try:
                data, completed = self._write_events.get(timeout=0.01)
            except queue.Empty:
                continue
            try:
                stream = getattr(self._process, "stdin")
                offset = 0
                while offset < len(data) and not self._stop.is_set():
                    written = stream.write(memoryview(data)[offset:])
                    if type(written) is not int or not 1 <= written <= len(data) - offset:
                        raise SshBoundaryError("SSH_IO_FAILED")
                    offset += written
                if offset != len(data):
                    raise SshBoundaryError("SSH_IO_FAILED")
                stream.flush()
            except Exception:
                self._error = True
            finally:
                completed.set()

    def write(self, data: bytes) -> None:
        if self._closed or self._error:
            raise SshBoundaryError("SSH_IO_FAILED")
        if type(data) is not bytes or not 1 <= len(data) <= MAX_FRAME_BYTES + 4:
            raise SshBoundaryError("FRAME_LIMIT_EXCEEDED")
        deadline = self._now() + self._write_timeout
        if not self._write_lock.acquire(timeout=self._write_timeout):
            raise SshBoundaryError("SSH_IO_FAILED")
        try:
            if self._closed or self._error:
                raise SshBoundaryError("SSH_IO_FAILED")
            completed = threading.Event()
            try:
                self._write_events.put((data, completed), timeout=max(0.0, deadline - self._now()))
            except queue.Full:
                self._error = True
                raise SshBoundaryError("SSH_IO_FAILED") from None
            if (
                not completed.wait(max(0.0, deadline - self._now()))
                or self._closed or self._error
            ):
                self._error = True
                raise SshBoundaryError("SSH_IO_FAILED")
        finally:
            self._write_lock.release()

    def poll(self, timeout_seconds: float, max_bytes: int) -> SshPollResult:
        if self._closed or self._error:
            raise SshBoundaryError("SSH_IO_FAILED")
        if (
            type(timeout_seconds) is not float or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= 86_400
            or type(max_bytes) is not int or not 1 <= max_bytes <= MAX_FRAME_BYTES
        ):
            raise SshBoundaryError("FRAME_INVALID")
        deadline = self._now() + timeout_seconds
        if not self._poll_lock.acquire(timeout=timeout_seconds):
            raise SshBoundaryError("SSH_IO_FAILED")
        try:
            if self._closed or self._error:
                raise SshBoundaryError("SSH_IO_FAILED")
            return self._poll_locked(max(0.0, deadline - self._now()), max_bytes)
        finally:
            self._poll_lock.release()

    def _poll_locked(self, timeout_seconds: float, max_bytes: int) -> SshPollResult:
        if not any(self._pending.values()) and len(self._eof_streams) < 2:
            try:
                name, data = self._read_events.get(timeout=timeout_seconds)
            except queue.Empty:
                return SshPollResult()
            self._accept_read(name, data)
        # Draining a finite queue services both streams without waiting for one to end.
        for _ in range(8):
            if any(
                len(pending) >= max_bytes or len(pending) > MAX_FRAME_BYTES - 4_096
                for pending in self._pending.values()
            ):
                break
            try:
                name, data = self._read_events.get_nowait()
            except queue.Empty:
                break
            self._accept_read(name, data)
        if self._closed or self._error:
            raise SshBoundaryError("SSH_IO_FAILED")
        stdout = bytes(self._pending["stdout"][:max_bytes])
        stderr = bytes(self._pending["stderr"][:max_bytes])
        del self._pending["stdout"][:max_bytes]
        del self._pending["stderr"][:max_bytes]
        return SshPollResult(
            stdout=stdout, stderr=stderr,
            eof=len(self._eof_streams) == 2 and not any(self._pending.values()),
        )

    def _accept_read(self, name: str, data: bytes | None) -> None:
        if data is None:
            self._eof_streams.add(name)
            return
        pending = self._pending[name]
        if len(pending) + len(data) > MAX_FRAME_BYTES:
            raise SshBoundaryError("FRAME_LIMIT_EXCEEDED")
        pending.extend(data)

    def close(self) -> None:
        timestamp = self._now()
        deadline = self._close_deadline or timestamp + self._close_timeout
        if not self._close_lock.acquire(timeout=max(0.0, deadline - self._now())):
            raise SshBoundaryError("SSH_IO_FAILED")
        try:
            if self._close_deadline is not None:
                deadline = self._close_deadline
            if self._closed:
                if self._close_failed:
                    # A later observation may establish exit; it grants no new
                    # termination or waiting budget beyond the original window.
                    self._close_process(deadline, inspect_only=self._now() >= deadline)
                return
            self._close_deadline = deadline
            self._closed = True
            self._stop.set()
            try:
                self._read_events.put_nowait(("stdout", None))
            except queue.Full:
                pass
            try:
                self._close_process(deadline)
            except Exception:
                self._close_failed = True
                raise SshBoundaryError("SSH_IO_FAILED") from None
        finally:
            self._close_lock.release()

    def _close_process(self, deadline: float, *, inspect_only: bool = False) -> None:
        def remaining() -> float:
            return min(self._close_timeout, max(0.0, deadline - self._now()))

        failed = False
        if self._process is not None:
            try:
                if self._process.poll() is None:
                    if inspect_only:
                        raise SshBoundaryError("SSH_IO_FAILED")
                    self._process.terminate()
                if not inspect_only:
                    try:
                        self._process.wait(timeout=remaining() / 2)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                        self._process.wait(timeout=remaining())
                if self._process.poll() is None:
                    raise SshBoundaryError("SSH_IO_FAILED")
            except Exception:
                failed = True
        for thread in self._threads:
            if thread.ident is not None:
                thread.join(timeout=remaining())
        if any(thread.is_alive() for thread in self._threads):
            failed = True
        else:
            for name in ("stdin", "stdout", "stderr"):
                stream = getattr(self._process, name, None)
                if stream is not None:
                    try:
                        stream.close()
                    except Exception:
                        failed = True
        if self._poll_lock.acquire(timeout=remaining()):
            try:
                for pending in self._pending.values():
                    pending.clear()
            finally:
                self._poll_lock.release()
        else:
            failed = True
        for events in (self._read_events, self._write_events):
            while True:
                try:
                    item = events.get_nowait()
                except queue.Empty:
                    break
                if events is self._write_events:
                    item[1].set()
        self._close_failed = failed
        if failed:
            raise SshBoundaryError("SSH_IO_FAILED")


def run_dev_ssh_attempt(*args: object, **kwargs: object) -> DevAttemptSummaryV1:
    """Public effects remain disabled regardless of caller identities or injections."""
    return DevAttemptSummaryV1(
        outcome="NOT_AUTHORIZED", cleanup="NOT_REACHED", adapter_call_count=0,
        attempt_count=None, ownership_retained=False, failure_codes=("NOT_AUTHORIZED",),
    )


def run_offline_ssh_exchange(
    binding: TrustedSshBinding,
    budgets: DevAttemptBudgetsV1,
    control: DevAttemptControlV1,
    *,
    io_factory: Callable[[tuple[str, ...]], NativeSshIo],
    clock: Callable[[], float],
    binding_check: Callable[[TrustedSshBinding], bool],
    local_owner: LocalSshOwner,
    cancel_requested: Callable[[], bool] = lambda: False,
    accepted_frame: Callable[[DevAttemptFrameV1], None] | None = None,
) -> DevAttemptSummaryV1:
    """One synthetic channel; ambiguous submission retains the original invocation.

    The injected checker and I/O are fixture seams, not approval or remote trust
    evidence. A peer's VERIFIED_OFFLINE field never becomes independent proof.
    """
    io: NativeSshIo | None = None
    ownership = False
    started = False
    containment_ready = False
    adapter_started = False
    generation_terminal = False
    verification_received = False
    cancel_acknowledged = False
    attempt_count: int | None = None
    last_time: float | None = None
    last_sequence = -1
    status_pending = 0
    outgoing_sequence = 0
    cancel_sent = False
    cleanup_deadline: float | None = None
    work_deadline = 0.0
    total_deadline = 0.0
    stderr_bytes = 0
    failure: str | None = None
    decoder = IncrementalFrameDecoder()

    def summary(code: str) -> DevAttemptSummaryV1:
        nonlocal io
        if io is not None:
            if code in ("SSH_EOF", "CLEANUP_DEADLINE_EXCEEDED", "TRANSPORT_POLL_LIMIT"):
                try:
                    send("CANCEL")
                except Exception:
                    code = "SSH_IO_FAILED"
            try:
                local_owner.close()
            except Exception:
                code = "SSH_IO_FAILED"
            io = None
        return DevAttemptSummaryV1(
            outcome="UNKNOWN", cleanup="UNKNOWN" if ownership else "NOT_REACHED",
            adapter_call_count=1 if adapter_started else (None if started else 0),
            attempt_count=attempt_count, ownership_retained=ownership, failure_codes=(code,),
        )

    def now() -> float:
        nonlocal last_time
        value = clock()
        if (
            type(value) not in (int, float) or not math.isfinite(value)
            or (last_time is not None and value < last_time)
        ):
            raise SshBoundaryError("CLOCK_INVALID")
        last_time = float(value)
        return last_time

    def send(operation: str) -> None:
        nonlocal outgoing_sequence, cancel_sent, status_pending
        assert io is not None
        if operation == "CANCEL":
            if cancel_sent:
                return
            cancel_sent = True
        if outgoing_sequence > 1_024:
            raise SshBoundaryError("TRANSPORT_POLL_LIMIT")
        message = DevAttemptControlV1(
            identity=checked_control.identity, operation=operation, sequence=outgoing_sequence,
        )
        outgoing_sequence += 1
        io.write(encode_control_frame(message))
        if operation == "STATUS":
            status_pending += 1

    def begin_cleanup(code: str, timestamp: float) -> None:
        nonlocal cleanup_deadline, failure
        if failure is None:
            failure = code
        if cleanup_deadline is None:
            cleanup_deadline = min(total_deadline, timestamp + checked_budgets.cleanup_seconds)
            try:
                send("CANCEL")
            except Exception:
                failure = "SSH_IO_FAILED"

    try:
        if (
            type(budgets) is not DevAttemptBudgetsV1 or type(control) is not DevAttemptControlV1
            or type(local_owner) is not LocalSshOwner or local_owner.claimed
        ):
            return summary("FRAME_INVALID")
        checked_budgets = budgets.revalidated()
        checked_control = control.revalidated()
        checked_binding = _validated_binding(binding)
        if (
            checked_control.operation != "OPEN" or checked_control.sequence != 0
            or checked_binding.python_sha256 != checked_control.identity.python_sha256
            or checked_binding.studio_id != checked_control.identity.studio_ref
        ):
            return summary("IDENTITY_MISMATCH")
        if binding_check(checked_binding) is not True:
            return summary("SSH_BINDING_UNVERIFIED")
        initial_time = now()
        work_deadline = initial_time + checked_budgets.work_seconds
        total_deadline = work_deadline + checked_budgets.cleanup_seconds
        if (
            not math.isfinite(total_deadline) or work_deadline <= initial_time
            or total_deadline <= work_deadline
        ):
            return summary("CLOCK_INVALID")
        ownership = True
        io = io_factory(build_native_ssh_argv(checked_binding))
        local_owner.claim(io)
        send("OPEN")
        for _ in range(MAX_POLLS):
            timestamp = now()
            if cleanup_deadline is None:
                cancelled = cancel_requested()
                if type(cancelled) is not bool:
                    raise SshBoundaryError("FRAME_INVALID")
                if cancelled:
                    begin_cleanup("CANCELLED", timestamp)
                elif timestamp >= work_deadline:
                    begin_cleanup("WORK_DEADLINE_EXCEEDED", timestamp)
            deadline = cleanup_deadline if cleanup_deadline is not None else work_deadline
            if timestamp >= deadline:
                return summary("CLEANUP_DEADLINE_EXCEEDED")
            received = io.poll(min(checked_budgets.poll_seconds, deadline - timestamp), MAX_FRAME_BYTES)
            observed_at = now()
            if type(received) is not SshPollResult:
                raise SshBoundaryError("FRAME_INVALID")
            if (
                type(received.stdout) is not bytes or type(received.stderr) is not bytes
                or type(received.eof) is not bool
                or len(received.stdout) > MAX_FRAME_BYTES or len(received.stderr) > MAX_FRAME_BYTES
            ):
                raise SshBoundaryError("FRAME_LIMIT_EXCEEDED")
            stderr_bytes += len(received.stderr)
            if stderr_bytes > MAX_STDERR_BYTES:
                raise SshBoundaryError("FRAME_LIMIT_EXCEEDED")
            if observed_at >= deadline:
                if cleanup_deadline is not None:
                    return summary("CLEANUP_DEADLINE_EXCEEDED")
                begin_cleanup("WORK_DEADLINE_EXCEEDED", observed_at)
                continue
            received_frames = decoder.feed(received.stdout)
            for frame_index, frame in enumerate(received_frames):
                if frame.binding_sha256 != checked_control.identity.canonical_sha256():
                    raise SshBoundaryError("IDENTITY_MISMATCH")
                if frame.sequence != last_sequence + 1:
                    raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                last_sequence = frame.sequence
                if frame.summary is not None and (
                    (frame.summary.adapter_call_count == 1 and not adapter_started)
                    or (adapter_started and frame.summary.adapter_call_count != 1)
                    or (frame.summary.attempt_count is not None and frame.summary.attempt_count != attempt_count)
                    or (attempt_count is not None and frame.summary.attempt_count != attempt_count)
                ):
                    raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                if frame.kind == "READY":
                    if started or last_sequence != 0 or frame.summary is not None:
                        raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                    if cleanup_deadline is None:
                        ready_cancelled = cancel_requested()
                        if type(ready_cancelled) is not bool:
                            raise SshBoundaryError("FRAME_INVALID")
                        if ready_cancelled:
                            begin_cleanup("CANCELLED", observed_at)
                        else:
                            started = True
                            send("START")
                elif frame.kind == "PROGRESS":
                    if not started or cleanup_deadline is not None or generation_terminal:
                        raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                    if frame.progress == "CONTAINMENT_READY":
                        if containment_ready or adapter_started:
                            raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                        containment_ready = True
                    elif frame.progress == "ADAPTER_STARTED":
                        if adapter_started or not containment_ready:
                            raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                        adapter_started = True
                    elif frame.progress == "GENERATION_ATTEMPT_STARTED":
                        if not adapter_started or frame.attempt_number != (attempt_count or 0) + 1:
                            raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                        attempt_count = frame.attempt_number
                    elif frame.progress == "TERMINAL":
                        if attempt_count is None:
                            raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                        generation_terminal = True
                elif frame.kind == "VERIFICATION":
                    if (
                        not started or attempt_count is None or cleanup_deadline is not None
                        or frame.summary is None or frame.summary.verification is None
                        or frame.summary.outcome not in ("RUNNING", "FAILED", "UNKNOWN")
                        or verification_received
                    ):
                        raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                    verification_received = True
                elif frame.kind == "CANCEL_ACK":
                    if not cancel_sent or cancel_acknowledged:
                        raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                    cancel_acknowledged = True
                elif frame.kind == "STATUS":
                    if status_pending < 1:
                        raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                    status_pending -= 1
                elif frame.kind == "INSPECTION":
                    # Inspection is a distinct independently owned exchange, not this stream.
                    raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                elif frame.kind == "TERMINAL":
                    if (
                        frame_index != len(received_frames) - 1
                        or frame.summary.outcome in ("RUNNING", "NOT_AUTHORIZED")
                    ):
                        raise SshBoundaryError("FRAME_SEQUENCE_INVALID")
                    decoder.eof()
                elif frame.kind == "ERROR":
                    begin_cleanup("PROTOCOL_FAILED", observed_at)
                if accepted_frame is not None:
                    accepted_frame(frame)
                if frame.kind == "TERMINAL":
                    return summary(failure or "PROOF_REQUIRED")
            if received.eof:
                decoder.eof()
                return summary("SSH_EOF")
            if cleanup_deadline is not None:
                send("STATUS")
        return summary("TRANSPORT_POLL_LIMIT")
    except SshBoundaryError as error:
        if io is not None and ownership:
            try:
                send("CANCEL")
            except Exception:
                pass
        return summary(error.code)
    except Exception:
        if io is not None and ownership:
            try:
                send("CANCEL")
            except Exception:
                pass
        return summary("SSH_IO_FAILED")
    finally:
        if io is not None:
            try:
                local_owner.close()
            except Exception:
                pass
