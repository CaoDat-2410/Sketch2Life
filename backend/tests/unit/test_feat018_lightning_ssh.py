"""Synthetic SSH framing and watchdog tests: no SSH, processes, or network."""

from __future__ import annotations

import json
import struct
import subprocess
import threading
from dataclasses import replace
from typing import Callable

import pytest

from sketch2life.contracts.schemas.feat018_live_binding import (
    DevAttemptBudgetsV1,
    DevAttemptControlV1,
    DevAttemptFrameV1,
    DevAttemptIdentityV1,
    DevAttemptSummaryV1,
    DevAttemptVerificationV1,
)
from sketch2life.infrastructure.ai import feat018_lightning_ssh as ssh


PRIVATE = "synthetic-private-token-never-rendered"


def _identity() -> DevAttemptIdentityV1:
    return DevAttemptIdentityV1(
        studio_ref="synthetic-studio", invocation_ref="synthetic-invocation",
        nonce="1" * 64, python_sha256="2" * 64, entry_sha256="3" * 64,
        config_sha256="4" * 64, source_sha256="5" * 64, request_sha256="6" * 64,
    )


def _binding() -> ssh.TrustedSshBinding:
    return ssh.TrustedSshBinding(
        binary_path=f"/synthetic/{PRIVATE}/ssh", identity_file=f"/private/{PRIVATE}/key",
        known_hosts_file=f"/private/{PRIVATE}/known_hosts", remote_python="/opt/dev/python",
        studio_id="synthetic-studio", binary_sha256="7" * 64,
        known_hosts_sha256="8" * 64, host_key_sha256="9" * 64, python_sha256="2" * 64,
    )


def _budgets() -> DevAttemptBudgetsV1:
    return DevAttemptBudgetsV1(work_seconds=2.0, cleanup_seconds=1.0, poll_seconds=0.1)


def _frame(kind: str, sequence: int, **kwargs: object) -> DevAttemptFrameV1:
    return DevAttemptFrameV1(
        kind=kind, binding_sha256=_identity().canonical_sha256(), sequence=sequence, **kwargs,
    )


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


class FakeIo:
    def __init__(self, clock: FakeClock, events: list[ssh.SshPollResult | Exception]) -> None:
        self.clock = clock
        self.events = list(events)
        self.writes: list[DevAttemptControlV1] = []
        self.polls: list[tuple[float, int]] = []
        self.closed = False
        self.advance = True

    def write(self, data: bytes) -> None:
        self.writes.append(DevAttemptControlV1.model_validate_json(data[4:]))

    def poll(self, timeout_seconds: float, max_bytes: int) -> ssh.SshPollResult:
        self.polls.append((timeout_seconds, max_bytes))
        if self.advance:
            self.clock.value += min(timeout_seconds, 0.01)
        event = self.events.pop(0) if self.events else ssh.SshPollResult()
        if isinstance(event, Exception):
            raise event
        return event

    def close(self) -> None:
        self.closed = True


def _exchange(
    events: list[ssh.SshPollResult | Exception],
    *, cancel: Callable[[], bool] = lambda: False,
    accepted: Callable[[DevAttemptFrameV1], None] | None = None,
    local_owner: ssh.LocalSshOwner | None = None,
) -> tuple[DevAttemptSummaryV1, FakeIo]:
    clock = FakeClock()
    channel = FakeIo(clock, events)
    result = ssh.run_offline_ssh_exchange(
        _binding(), _budgets(), DevAttemptControlV1(identity=_identity(), operation="OPEN"),
        io_factory=lambda _: channel, clock=clock, binding_check=lambda _: True,
        local_owner=local_owner or ssh.LocalSshOwner(),
        cancel_requested=cancel, accepted_frame=accepted,
    )
    return result, channel


def _wire(frame: DevAttemptFrameV1) -> ssh.SshPollResult:
    return ssh.SshPollResult(stdout=ssh.encode_attempt_frame(frame))


def test_public_denial_precedes_every_injected_effect() -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        pytest.fail("a public denial invoked an effect")

    result = ssh.run_dev_ssh_attempt(
        _binding(), _budgets(), io_factory=forbidden, clock=forbidden,
        binding_check=forbidden, start=True, authorized=True,
    )
    assert result.outcome == "NOT_AUTHORIZED"
    assert result.adapter_call_count == 0
    assert not result.ownership_retained
    assert not result.live_authorized and not result.studio_release_proven


def test_fixed_argv_is_private_strict_and_has_no_request_data() -> None:
    binding = _binding()
    argv = ssh.build_native_ssh_argv(binding)
    assert PRIVATE not in repr(binding) + str(binding) + repr(argv) + str(argv)
    assert argv[0] == binding.binary_path
    assert argv[-2] == "s_synthetic-studio@ssh.lightning.ai"
    assert argv[-1] == (
        "/opt/dev/python -I -B -m sketch2life.interfaces.cli.feat018_lightning_dev_attempt session"
    )
    for required in (
        "StrictHostKeyChecking=yes", "BatchMode=yes", "ControlMaster=no",
        "ControlPath=none", "ClearAllForwardings=yes", "PermitLocalCommand=no",
        "ForwardAgent=no", "ForwardX11=no", "ProxyCommand=none", "ProxyJump=none",
    ):
        assert required in argv
    assert "-T" in argv and argv[1:3] == ("-F", "none")
    assert _identity().nonce not in " ".join(argv)


@pytest.mark.parametrize("field,value", [
    ("binary_path", "relative/ssh"), ("identity_file", "relative/key"),
    ("known_hosts_file", "/private/hosts\nignored"),
    ("known_hosts_file", "/private/hosts extra_hosts"),
    ("known_hosts_file", "/private/hosts\tignored"),
    ("known_hosts_file", '/private/"hosts"'),
    ("remote_python", "/opt/python;echo private"), ("remote_python", "/opt/../python"),
    ("studio_id", "studio -oProxyCommand=private"), ("binary_sha256", PRIVATE),
])
def test_invalid_binding_error_does_not_echo_values(field: str, value: str) -> None:
    with pytest.raises(ssh.SshBoundaryError) as error:
        ssh.build_native_ssh_argv(replace(_binding(), **{field: value}))
    assert str(error.value) == "SSH_BINDING_INVALID"
    assert value not in str(error.value)


@pytest.mark.parametrize("field", ["binary_path", "identity_file", "known_hosts_file"])
@pytest.mark.parametrize("character", ["%", "$", "~"])
def test_ssh_path_expansion_characters_are_rejected_for_every_bound_file(field, character):
    value = f"/private/{character}/fixture"
    with pytest.raises(ssh.SshBoundaryError, match="SSH_BINDING_INVALID"):
        ssh.build_native_ssh_argv(replace(_binding(), **{field: value}))


def test_incremental_frames_round_trip_through_protected_json_ingress() -> None:
    first = _frame("READY", 0)
    second = _frame("PROGRESS", 1, progress="CONTAINMENT_READY")
    wire = ssh.encode_attempt_frame(first) + ssh.encode_attempt_frame(second)
    decoder = ssh.IncrementalFrameDecoder()
    frames = []
    for value in wire:
        frames.extend(decoder.feed(bytes((value,))))
    decoder.eof()
    assert frames == [first, second]
    assert PRIVATE not in repr(decoder)


@pytest.mark.parametrize("payload", [
    b"{\"private\":\"synthetic-private-token-never-rendered\",",
    json.dumps({"kind": "READY", "sequence": 0, "private": PRIVATE}).encode(),
    b"\xff\xfe",
])
def test_malformed_json_is_closed_and_decoder_cannot_be_reset(payload: bytes) -> None:
    decoder = ssh.IncrementalFrameDecoder()
    with pytest.raises(ssh.SshBoundaryError) as error:
        decoder.feed(struct.pack("!I", len(payload)) + payload)
    assert str(error.value) == "FRAME_INVALID"
    assert PRIVATE not in str(error.value) + repr(error.value)
    with pytest.raises(ssh.SshBoundaryError, match="FRAME_INVALID"):
        decoder.feed(ssh.encode_attempt_frame(_frame("READY", 0)))


@pytest.mark.parametrize("wire", [struct.pack("!I", 0), struct.pack("!I", ssh.MAX_FRAME_BYTES + 1)])
def test_advertised_frame_size_fails_before_payload(wire: bytes) -> None:
    with pytest.raises(ssh.SshBoundaryError, match="FRAME_LIMIT_EXCEEDED"):
        ssh.IncrementalFrameDecoder().feed(wire)


def test_truncated_frame_at_eof_is_rejected() -> None:
    decoder = ssh.IncrementalFrameDecoder()
    decoder.feed(ssh.encode_attempt_frame(_frame("READY", 0))[:-1])
    with pytest.raises(ssh.SshBoundaryError, match="FRAME_INVALID"):
        decoder.eof()


def test_total_wire_limit_is_not_reset_after_a_complete_frame() -> None:
    decoder = ssh.IncrementalFrameDecoder()
    wire = ssh.encode_attempt_frame(_frame("READY", 0))
    with pytest.raises(ssh.SshBoundaryError, match="FRAME_LIMIT_EXCEEDED"):
        for _ in range(ssh.MAX_WIRE_BYTES // len(wire) + 1):
            decoder.feed(wire)


def test_terminal_metadata_is_not_remote_cleanup_proof() -> None:
    accepted = []
    result, io = _exchange([
        _wire(_frame("READY", 0)),
        _wire(_frame("PROGRESS", 1, progress="CONTAINMENT_READY")),
        _wire(_frame("PROGRESS", 2, progress="ADAPTER_STARTED")),
        _wire(_frame("PROGRESS", 3, progress="GENERATION_ATTEMPT_STARTED", attempt_number=1)),
        _wire(_frame("TERMINAL", 4, summary=DevAttemptSummaryV1(
            outcome="FAILED", cleanup="VERIFIED_OFFLINE", adapter_call_count=1, attempt_count=1,
        ))),
    ], accepted=accepted.append)
    assert [item.operation for item in io.writes] == ["OPEN", "START"]
    assert result.outcome == "UNKNOWN" and result.cleanup == "UNKNOWN"
    assert result.failure_codes == ("PROOF_REQUIRED",)
    assert result.adapter_call_count == 1 and result.attempt_count == 1
    assert result.ownership_retained and io.closed
    assert len(accepted) == 5


def test_cancel_before_ready_never_sends_start_or_restarts_identity() -> None:
    result, io = _exchange([_wire(_frame("READY", 0)), ssh.SshPollResult(eof=True)], cancel=lambda: True)
    operations = [item.operation for item in io.writes]
    assert operations.count("CANCEL") == 1 and "START" not in operations
    assert all(item.identity == _identity() for item in io.writes)
    assert result.adapter_call_count == 0 and result.ownership_retained


def test_cancel_ack_and_transport_close_do_not_release_ownership() -> None:
    result, io = _exchange([
        _wire(_frame("CANCEL_ACK", 0, summary=DevAttemptSummaryV1(
            outcome="CANCELLED", cleanup="VERIFIED_OFFLINE", ownership_retained=False,
        ))), ssh.SshPollResult(eof=True),
    ], cancel=lambda: True)
    assert result.cleanup == "UNKNOWN" and result.ownership_retained
    assert io.closed and not result.studio_release_proven


def test_lost_submission_response_does_not_create_another_io_or_start() -> None:
    result, io = _exchange([_wire(_frame("READY", 0)), RuntimeError(PRIVATE)])
    assert [item.operation for item in io.writes] == ["OPEN", "START", "CANCEL"]
    assert result.adapter_call_count is None and result.attempt_count is None
    assert result.ownership_retained and result.failure_codes == ("SSH_IO_FAILED",)
    assert PRIVATE not in result.model_dump_json()


@pytest.mark.parametrize("bad", [
    _frame("READY", 1),
    _frame("READY", 0).model_copy(update={"binding_sha256": "f" * 64}),
    _frame("PROGRESS", 0, progress="ADAPTER_STARTED"),
])
def test_unbound_or_out_of_sequence_frame_never_starts_adapter(bad: DevAttemptFrameV1) -> None:
    result, io = _exchange([_wire(bad)])
    assert "START" not in [item.operation for item in io.writes]
    assert result.ownership_retained and result.cleanup == "UNKNOWN"


def test_repeated_progress_is_rejected_before_callback() -> None:
    accepted = []
    result, io = _exchange([
        _wire(_frame("READY", 0)),
        _wire(_frame("PROGRESS", 1, progress="CONTAINMENT_READY")),
        _wire(_frame("PROGRESS", 2, progress="ADAPTER_STARTED")),
        _wire(_frame("PROGRESS", 3, progress="ADAPTER_STARTED")),
    ], accepted=accepted.append)
    assert len(accepted) == 3
    assert result.failure_codes == ("FRAME_SEQUENCE_INVALID",)
    assert [item.operation for item in io.writes].count("CANCEL") == 1


def test_work_expiry_and_cleanup_watchdog_never_reset() -> None:
    result, io = _exchange([])
    assert result.failure_codes == ("CLEANUP_DEADLINE_EXCEEDED",)
    assert [item.operation for item in io.writes].count("CANCEL") == 1
    assert "START" not in [item.operation for item in io.writes]
    assert io.clock.value <= 3.01
    assert all(0 < duration <= _budgets().poll_seconds for duration, _ in io.polls)


def test_frozen_clock_is_still_bounded_by_poll_limit() -> None:
    clock = FakeClock()
    io = FakeIo(clock, [])
    io.advance = False
    result = ssh.run_offline_ssh_exchange(
        _binding(), _budgets(), DevAttemptControlV1(identity=_identity(), operation="OPEN"),
        io_factory=lambda _: io, clock=clock, binding_check=lambda _: True,
        local_owner=ssh.LocalSshOwner(),
    )
    assert result.failure_codes == ("TRANSPORT_POLL_LIMIT",)
    assert len(io.polls) == ssh.MAX_POLLS and io.closed
    assert result.ownership_retained


@pytest.mark.parametrize("clock_value", [float("nan"), float("inf"), True, "private", 1e100])
def test_invalid_clock_has_no_transport_effect(clock_value: object) -> None:
    called = []
    result = ssh.run_offline_ssh_exchange(
        _binding(), _budgets(), DevAttemptControlV1(identity=_identity(), operation="OPEN"),
        io_factory=lambda argv: called.append(argv), clock=lambda: clock_value,
        binding_check=lambda _: True,
        local_owner=ssh.LocalSshOwner(),
    )
    assert result.failure_codes == ("CLOCK_INVALID",)
    assert not called and not result.ownership_retained


def test_unverified_binding_precedes_io_and_clock() -> None:
    def forbidden() -> float:
        pytest.fail("unverified SSH trust reached clock")

    result = ssh.run_offline_ssh_exchange(
        _binding(), _budgets(), DevAttemptControlV1(identity=_identity(), operation="OPEN"),
        io_factory=lambda _: pytest.fail("unverified SSH trust reached I/O"),
        clock=forbidden, binding_check=lambda _: False,
        local_owner=ssh.LocalSshOwner(),
    )
    assert result.failure_codes == ("SSH_BINDING_UNVERIFIED",)
    assert not result.ownership_retained


def test_stderr_is_bounded_discarded_and_never_echoed() -> None:
    result, io = _exchange([
        ssh.SshPollResult(stderr=(PRIVATE.encode() * 1_000)[:ssh.MAX_FRAME_BYTES]),
        ssh.SshPollResult(stderr=b"x" * ssh.MAX_FRAME_BYTES),
        ssh.SshPollResult(stderr=b"x"),
    ])
    assert result.failure_codes == ("FRAME_LIMIT_EXCEEDED",)
    assert PRIVATE not in result.model_dump_json()
    assert io.closed and result.ownership_retained


def _progress_events() -> list[ssh.SshPollResult]:
    return [
        _wire(_frame("READY", 0)),
        _wire(_frame("PROGRESS", 1, progress="CONTAINMENT_READY")),
        _wire(_frame("PROGRESS", 2, progress="ADAPTER_STARTED")),
        _wire(_frame("PROGRESS", 3, progress="GENERATION_ATTEMPT_STARTED", attempt_number=1)),
    ]


def test_exact_open_ready_start_sequences_and_local_release() -> None:
    owner = ssh.LocalSshOwner()
    result, io = _exchange([
        _wire(_frame("READY", 0)), ssh.SshPollResult(eof=True),
    ], local_owner=owner)
    assert [(item.operation, item.sequence) for item in io.writes] == [
        ("OPEN", 0), ("START", 1), ("CANCEL", 2),
    ]
    assert owner.claimed and not owner.retained
    assert result.ownership_retained and result.failure_codes == ("SSH_EOF",)


@pytest.mark.parametrize("kind", ["STATUS", "CANCEL_ACK", "INSPECTION"])
def test_unsolicited_foreign_exchange_frames_never_reach_callback(kind: str) -> None:
    accepted = []
    result, io = _exchange([_wire(_frame(kind, 0, summary=DevAttemptSummaryV1(
        outcome="UNKNOWN",
    )))], accepted=accepted.append)
    assert result.failure_codes == ("FRAME_SEQUENCE_INVALID",)
    assert not accepted and "START" not in [item.operation for item in io.writes]


def test_terminal_cannot_invent_unobserved_adapter_or_attempt_counts() -> None:
    accepted = []
    result, _ = _exchange([
        _wire(_frame("READY", 0)),
        _wire(_frame("TERMINAL", 1, summary=DevAttemptSummaryV1(
            outcome="FAILED", adapter_call_count=1, attempt_count=2,
        ))),
    ], accepted=accepted.append)
    assert result.failure_codes == ("FRAME_SEQUENCE_INVALID",)
    assert result.adapter_call_count is None and result.attempt_count is None
    assert [item.kind for item in accepted] == ["READY"]


def _verification() -> DevAttemptVerificationV1:
    return DevAttemptVerificationV1(
        v2_status="SUCCEEDED", raw_status="SUCCEEDED", v2_schema_verified=True,
        raw_schema_verified=True, source_matched=True, correlation_matched=True,
        provenance_matched=True, gate_a_required=True, narration_status="NOT_SUPPLIED",
    )


def test_producer_success_and_cleanup_flags_never_supply_independent_proof() -> None:
    accepted = []
    remote_summary = DevAttemptSummaryV1(
        outcome="SUCCEEDED", cleanup="VERIFIED_OFFLINE", adapter_call_count=1,
        attempt_count=1, verification=_verification(), ownership_retained=False,
    )
    result, _ = _exchange(_progress_events() + [
        _wire(_frame("TERMINAL", 4, summary=remote_summary)),
    ], accepted=accepted.append)
    assert accepted[-1].summary == remote_summary
    assert result.outcome == "UNKNOWN" and result.cleanup == "UNKNOWN"
    assert result.failure_codes == ("PROOF_REQUIRED",) and result.ownership_retained
    assert result.verification is None and not result.studio_release_proven


def test_verification_is_received_once_after_accepted_attempt() -> None:
    accepted = []
    verification = DevAttemptSummaryV1(
        outcome="RUNNING", adapter_call_count=1, attempt_count=1, verification=_verification(),
    )
    result, _ = _exchange(_progress_events() + [
        _wire(_frame("VERIFICATION", 4, summary=verification)),
        _wire(_frame("VERIFICATION", 5, summary=verification)),
    ], accepted=accepted.append)
    assert result.failure_codes == ("FRAME_SEQUENCE_INVALID",)
    assert len(accepted) == 5 and accepted[-1].kind == "VERIFICATION"


@pytest.mark.parametrize("count,attempt", [(0, None), (1, None), (1, 2)])
def test_terminal_counts_must_agree_with_accepted_progress(count: int, attempt: int | None) -> None:
    result, _ = _exchange(_progress_events() + [
        _wire(_frame("TERMINAL", 4, summary=DevAttemptSummaryV1(
            outcome="FAILED", adapter_call_count=count, attempt_count=attempt,
        ))),
    ])
    assert result.failure_codes == ("FRAME_SEQUENCE_INVALID",)
    assert result.adapter_call_count == 1 and result.attempt_count == 1


def test_progress_cannot_restart_after_generation_terminal() -> None:
    accepted = []
    result, _ = _exchange(_progress_events() + [
        _wire(_frame("PROGRESS", 4, progress="TERMINAL")),
        _wire(_frame("PROGRESS", 5, progress="GENERATION_ATTEMPT_STARTED", attempt_number=2)),
    ], accepted=accepted.append)
    assert result.failure_codes == ("FRAME_SEQUENCE_INVALID",)
    assert result.attempt_count == 1 and len(accepted) == 5


def test_terminal_followed_by_partial_frame_is_rejected_before_callback() -> None:
    accepted = []
    terminal = _frame("TERMINAL", 4, summary=DevAttemptSummaryV1(
        outcome="FAILED", adapter_call_count=1, attempt_count=1,
    ))
    result, _ = _exchange(_progress_events() + [ssh.SshPollResult(
        stdout=ssh.encode_attempt_frame(terminal) + b"\x00\x00",
    )], accepted=accepted.append)
    assert result.failure_codes == ("FRAME_INVALID",)
    assert len(accepted) == 4


def test_duplicate_cancel_ack_is_rejected_without_resetting_cancel() -> None:
    ack = DevAttemptSummaryV1(outcome="CANCELLED")
    result, io = _exchange([
        _wire(_frame("CANCEL_ACK", 0, summary=ack)),
        _wire(_frame("CANCEL_ACK", 1, summary=ack)),
    ], cancel=lambda: True)
    assert result.failure_codes == ("FRAME_SEQUENCE_INVALID",)
    assert [item.operation for item in io.writes].count("CANCEL") == 1


def test_callback_failure_is_private_and_retains_unknown_ownership() -> None:
    def callback(frame: DevAttemptFrameV1) -> None:
        raise RuntimeError(PRIVATE)

    result, io = _exchange([_wire(_frame("READY", 0))], accepted=callback)
    assert result.failure_codes == ("SSH_IO_FAILED",)
    assert PRIVATE not in result.model_dump_json()
    assert io.closed and result.ownership_retained


def test_failed_fake_channel_close_keeps_actionable_local_owner() -> None:
    clock = FakeClock()

    class FailingClose(FakeIo):
        fail_close = True

        def close(self) -> None:
            if self.fail_close:
                raise RuntimeError(PRIVATE)
            super().close()

    channel = FailingClose(clock, [ssh.SshPollResult(eof=True)])
    owner = ssh.LocalSshOwner()
    result = ssh.run_offline_ssh_exchange(
        _binding(), _budgets(), DevAttemptControlV1(identity=_identity(), operation="OPEN"),
        io_factory=lambda _: channel, clock=clock, binding_check=lambda _: True, local_owner=owner,
    )
    assert result.failure_codes == ("SSH_IO_FAILED",)
    assert owner.retained and result.ownership_retained
    assert PRIVATE not in repr(owner) + result.model_dump_json()
    channel.fail_close = False
    owner.close()
    assert not owner.retained and channel.closed


def test_used_local_owner_cannot_dispatch_another_invocation() -> None:
    owner = ssh.LocalSshOwner()
    _exchange([ssh.SshPollResult(eof=True)], local_owner=owner)
    result = ssh.run_offline_ssh_exchange(
        _binding(), _budgets(), DevAttemptControlV1(identity=_identity(), operation="OPEN"),
        io_factory=lambda _: pytest.fail("reused owner created another channel"),
        clock=lambda: pytest.fail("reused owner observed a clock"),
        binding_check=lambda _: pytest.fail("reused owner reached trust checker"), local_owner=owner,
    )
    assert result.failure_codes == ("FRAME_INVALID",)


class FakeReadPipe:
    def __init__(self, chunks: list[bytes | Exception], *, blocked: bool = False) -> None:
        self.chunks = list(chunks)
        self.entered = threading.Event()
        self.release = threading.Event()
        if not blocked:
            self.release.set()
        self.closed = False

    def read(self, size: int) -> bytes:
        assert size == 4_096
        self.entered.set()
        assert self.release.wait(1.0), "synthetic pipe was not released"
        value = self.chunks.pop(0) if self.chunks else b""
        if isinstance(value, Exception):
            raise value
        return value

    def close(self) -> None:
        self.closed = True
        self.release.set()


class FakeWritePipe:
    def __init__(self, *, blocked: bool = False, limit: int = 3, failure: bool = False) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()
        if not blocked:
            self.release.set()
        self.limit = limit
        self.failure = failure
        self.data = bytearray()
        self.flushes = 0
        self.closed = False

    def write(self, data: memoryview) -> int:
        self.entered.set()
        assert self.release.wait(1.0), "synthetic pipe was not released"
        if self.failure:
            raise RuntimeError(PRIVATE)
        written = min(len(data), self.limit)
        self.data.extend(data[:written])
        return written

    def flush(self) -> None:
        self.flushes += 1

    def close(self) -> None:
        self.closed = True
        self.release.set()


class FakeNativeProcess:
    def __init__(
        self, *, stdout: FakeReadPipe | None = None, stderr: FakeReadPipe | None = None,
        stdin: FakeWritePipe | None = None, terminate_exits: bool = True, kill_exits: bool = True,
    ) -> None:
        self.stdout = stdout or FakeReadPipe([])
        self.stderr = stderr or FakeReadPipe([])
        self.stdin = stdin or FakeWritePipe()
        self.terminate_exits = terminate_exits
        self.kill_exits = kill_exits
        self.returncode: int | None = None
        self.terminations = 0
        self.kills = 0
        self.waits: list[float] = []

    def poll(self) -> int | None:
        return self.returncode

    def _exit(self) -> None:
        self.returncode = 0
        for stream in (self.stdin, self.stdout, self.stderr):
            if stream is not None:
                stream.release.set()

    def terminate(self) -> None:
        self.terminations += 1
        if self.terminate_exits:
            self._exit()

    def kill(self) -> None:
        self.kills += 1
        if self.kill_exits:
            self._exit()

    def wait(self, timeout: float) -> int:
        self.waits.append(timeout)
        if self.returncode is None:
            raise subprocess.TimeoutExpired(PRIVATE, timeout)
        return self.returncode


def _native(
    process: FakeNativeProcess, *, owner: ssh.LocalSshOwner | None = None,
    write_timeout: float = 0.1, close_timeout: float = 0.1,
    clock: FakeClock | None = None,
) -> tuple[ssh.NativeSshProcessIo, ssh.LocalSshOwner, list[dict[str, object]]]:
    local_owner = owner or ssh.LocalSshOwner()
    calls = []

    def launch(argv: tuple[str, ...], **kwargs: object) -> FakeNativeProcess:
        assert argv == ssh.build_native_ssh_argv(_binding())
        assert local_owner.retained
        calls.append(kwargs)
        return process

    channel = ssh.NativeSshProcessIo(
        ssh.build_native_ssh_argv(_binding()), local_owner=local_owner, popen_factory=launch,
        clock=clock or FakeClock(),
        write_timeout_seconds=write_timeout, close_timeout_seconds=close_timeout,
    )
    return channel, local_owner, calls


def test_native_fake_launcher_is_bound_private_and_uses_pipes_without_shell() -> None:
    process = FakeNativeProcess()
    channel, owner, calls = _native(process)
    try:
        assert calls == [dict(
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False, bufsize=0, close_fds=True, env={},
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )]
        assert PRIVATE not in repr(channel) + str(channel) + repr(owner)
    finally:
        owner.close()
    assert not owner.retained and process.terminations == 1
    assert all(stream.closed for stream in (process.stdin, process.stdout, process.stderr))


def test_native_partial_writes_and_concurrent_callers_never_interleave() -> None:
    process = FakeNativeProcess(stdin=FakeWritePipe(limit=1))
    channel, owner, _ = _native(process)
    failures = []

    def write(data: bytes) -> None:
        try:
            channel.write(data)
        except Exception as error:
            failures.append(error)

    threads = [threading.Thread(target=write, args=(data,)) for data in (b"first", b"second")]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=0.5)
        assert not failures and all(not thread.is_alive() for thread in threads)
        assert bytes(process.stdin.data) in (b"firstsecond", b"secondfirst")
        assert process.stdin.flushes == 2
    finally:
        owner.close()


def test_native_stderr_is_serviced_while_stdout_is_blocked() -> None:
    process = FakeNativeProcess(
        stdout=FakeReadPipe([], blocked=True), stderr=FakeReadPipe([PRIVATE.encode()]),
    )
    channel, owner, _ = _native(process)
    try:
        assert process.stdout.entered.wait(0.2)
        received = channel.poll(0.1, ssh.MAX_FRAME_BYTES)
        assert received.stderr == PRIVATE.encode() and not received.stdout and not received.eof
        channel.write(b"cancel")
        assert bytes(process.stdin.data) == b"cancel"
        assert PRIVATE not in repr(received)
    finally:
        owner.close()


def test_native_close_wakes_a_concurrent_poll_without_extending_its_wait() -> None:
    process = FakeNativeProcess(
        stdout=FakeReadPipe([], blocked=True), stderr=FakeReadPipe([], blocked=True),
    )
    channel, owner, _ = _native(process)
    errors = []
    entered = threading.Event()

    def poll() -> None:
        entered.set()
        try:
            channel.poll(5.0, ssh.MAX_FRAME_BYTES)
        except ssh.SshBoundaryError as error:
            errors.append(str(error))

    thread = threading.Thread(target=poll)
    thread.start()
    assert entered.wait(0.2)
    try:
        owner.close()
        thread.join(timeout=0.2)
        assert not thread.is_alive() and errors == ["SSH_IO_FAILED"]
        assert not owner.retained
    finally:
        process._exit()
        thread.join(timeout=0.2)
        if owner.retained:
            owner.close()


def test_native_failed_close_retains_a_blocked_pipe_reader_until_observed_finished() -> None:
    class DetachedPipeProcess(FakeNativeProcess):
        def _exit(self) -> None:
            self.returncode = 0

    process = DetachedPipeProcess(stdout=FakeReadPipe([], blocked=True))
    channel, owner, _ = _native(process, close_timeout=0.02)
    assert process.stdout.entered.wait(0.2)
    try:
        with pytest.raises(ssh.SshBoundaryError, match="SSH_IO_FAILED"):
            owner.close()
        assert owner.retained and process.returncode == 0
        original_deadline = channel._close_deadline
        process.stdout.release.set()
        for thread in channel._threads:
            thread.join(timeout=0.2)
        owner.close()
        assert not owner.retained and channel._close_deadline == original_deadline
    finally:
        process.stdout.release.set()
        for thread in channel._threads:
            thread.join(timeout=0.2)
        if owner.retained:
            owner.close()


@pytest.mark.parametrize("max_bytes", [1_024, ssh.MAX_FRAME_BYTES - 1, ssh.MAX_FRAME_BYTES])
def test_native_large_stream_is_incrementally_bounded_without_data_loss(max_bytes: int) -> None:
    payload = b"a" * 20_480
    process = FakeNativeProcess(stdout=FakeReadPipe([payload[i:i + 4_096] for i in range(0, len(payload), 4_096)]))
    channel, owner, _ = _native(process)
    collected = bytearray()
    try:
        for _ in range(40):
            received = channel.poll(0.1, max_bytes)
            assert len(received.stdout) <= max_bytes and len(received.stderr) <= max_bytes
            collected.extend(received.stdout)
            if received.eof:
                break
        else:
            pytest.fail("finite synthetic stream did not reach EOF")
        assert bytes(collected) == payload
    finally:
        owner.close()


def test_native_blocked_write_times_out_and_close_unblocks_fake_pipe() -> None:
    process = FakeNativeProcess(stdin=FakeWritePipe(blocked=True))
    channel, owner, _ = _native(process, write_timeout=0.02)
    try:
        with pytest.raises(ssh.SshBoundaryError, match="SSH_IO_FAILED"):
            channel.write(PRIVATE.encode())
        assert process.stdin.entered.is_set()
        with pytest.raises(ssh.SshBoundaryError, match="SSH_IO_FAILED"):
            channel.write(b"late-start")
    finally:
        owner.close()
    assert not owner.retained


def test_native_writer_failure_never_echoes_private_exception() -> None:
    process = FakeNativeProcess(stdin=FakeWritePipe(failure=True))
    channel, owner, _ = _native(process)
    try:
        with pytest.raises(ssh.SshBoundaryError) as error:
            channel.write(b"control")
        assert str(error.value) == "SSH_IO_FAILED" and PRIVATE not in repr(error.value)
    finally:
        owner.close()


def test_native_terminate_timeout_escalates_to_kill_within_one_window() -> None:
    process = FakeNativeProcess(terminate_exits=False)
    channel, owner, _ = _native(process)
    owner.close()
    assert process.terminations == 1 and process.kills == 1
    assert len(process.waits) == 2 and all(0 <= value <= 0.1 for value in process.waits)
    assert not owner.retained
    channel.close()
    assert len(process.waits) == 2


def test_native_close_failure_retains_handle_and_original_deadline() -> None:
    clock = FakeClock()
    process = FakeNativeProcess(terminate_exits=False, kill_exits=False)
    channel, owner, _ = _native(process, close_timeout=0.02, clock=clock)
    with pytest.raises(ssh.SshBoundaryError, match="SSH_IO_FAILED"):
        owner.close()
    original_deadline = channel._close_deadline
    assert owner.retained and original_deadline == 0.02
    calls = (process.terminations, process.kills, len(process.waits))
    clock.value = 1.0
    with pytest.raises(ssh.SshBoundaryError, match="SSH_IO_FAILED"):
        owner.close()
    assert (process.terminations, process.kills, len(process.waits)) == calls
    assert channel._close_deadline == original_deadline and owner.retained
    process._exit()
    for thread in channel._threads:
        thread.join(timeout=0.2)
    owner.close()
    assert not owner.retained and channel._close_deadline == original_deadline


def test_native_constructor_failure_preserves_owner_when_fake_cleanup_fails() -> None:
    process = FakeNativeProcess(terminate_exits=False, kill_exits=False)
    process.stderr = None
    owner = ssh.LocalSshOwner()
    with pytest.raises(ssh.SshBoundaryError) as error:
        _native(process, owner=owner, close_timeout=0.02)
    assert str(error.value) == "SSH_IO_FAILED" and PRIVATE not in repr(error.value)
    assert owner.retained
    process._exit()
    owner.close()
    assert not owner.retained


def test_exchange_native_constructor_failure_retains_remote_and_local_ownership() -> None:
    process = FakeNativeProcess(terminate_exits=False, kill_exits=False)
    process.stderr = None
    owner = ssh.LocalSshOwner()
    clock = FakeClock()

    def factory(argv: tuple[str, ...]) -> ssh.NativeSshProcessIo:
        return ssh.NativeSshProcessIo(
            argv, local_owner=owner, clock=clock, popen_factory=lambda *args, **kwargs: process,
            write_timeout_seconds=0.02, close_timeout_seconds=0.02,
        )

    result = ssh.run_offline_ssh_exchange(
        _binding(), _budgets(), DevAttemptControlV1(identity=_identity(), operation="OPEN"),
        io_factory=factory, clock=clock, binding_check=lambda _: True, local_owner=owner,
    )
    assert result.failure_codes == ("SSH_IO_FAILED",)
    assert result.cleanup == "UNKNOWN" and result.ownership_retained
    assert owner.retained and result.adapter_call_count == 0
    process._exit()
    owner.close()
    assert not owner.retained


def test_exchange_concrete_native_fake_process_uses_one_exact_control_transcript() -> None:
    terminal = _frame("TERMINAL", 4, summary=DevAttemptSummaryV1(
        outcome="FAILED", adapter_call_count=1, attempt_count=1,
    ))
    events = _progress_events() + [_wire(terminal)]
    process = FakeNativeProcess(stdout=FakeReadPipe([item.stdout for item in events]))
    owner = ssh.LocalSshOwner()
    clock = FakeClock()
    launches = []

    def launch(*args: object, **kwargs: object) -> FakeNativeProcess:
        launches.append(True)
        return process

    result = ssh.run_offline_ssh_exchange(
        _binding(), _budgets(), DevAttemptControlV1(identity=_identity(), operation="OPEN"),
        io_factory=lambda argv: ssh.NativeSshProcessIo(
            argv, local_owner=owner, clock=clock, popen_factory=launch,
            write_timeout_seconds=0.1, close_timeout_seconds=0.1,
        ),
        clock=clock, binding_check=lambda _: True, local_owner=owner,
    )
    writes = []
    payload = bytes(process.stdin.data)
    while payload:
        length = struct.unpack("!I", payload[:4])[0]
        writes.append(DevAttemptControlV1.model_validate_json(payload[4:length + 4]))
        payload = payload[length + 4:]
    assert launches == [True] and [(item.operation, item.sequence) for item in writes] == [
        ("OPEN", 0), ("START", 1),
    ]
    assert result.failure_codes == ("PROOF_REQUIRED",)
    assert not owner.retained and result.ownership_retained


@pytest.mark.parametrize("clock_value", [True, float("nan"), float("inf"), 1e100, PRIVATE])
def test_invalid_native_clock_precedes_launcher(clock_value: object) -> None:
    owner = ssh.LocalSshOwner()
    with pytest.raises(ssh.SshBoundaryError, match="CLOCK_INVALID"):
        ssh.NativeSshProcessIo(
            ssh.build_native_ssh_argv(_binding()), local_owner=owner, clock=lambda: clock_value,
            popen_factory=lambda *args, **kwargs: pytest.fail("invalid clock launched a process"),
            write_timeout_seconds=0.1, close_timeout_seconds=0.1,
        )
    assert not owner.claimed and not owner.retained


@pytest.mark.parametrize("write_timeout,close_timeout", [
    (0.0, 0.1), (float("nan"), 0.1), (0.1, float("inf")), (True, 0.1), (0.1, 31.0),
])
def test_invalid_native_watchdog_precedes_launcher(write_timeout: object, close_timeout: object) -> None:
    owner = ssh.LocalSshOwner()
    with pytest.raises(ssh.SshBoundaryError, match="SSH_BINDING_INVALID"):
        ssh.NativeSshProcessIo(
            ssh.build_native_ssh_argv(_binding()), local_owner=owner,
            clock=FakeClock(),
            popen_factory=lambda *args, **kwargs: pytest.fail("invalid watchdog launched a process"),
            write_timeout_seconds=write_timeout, close_timeout_seconds=close_timeout,
        )
    assert not owner.claimed and not owner.retained
