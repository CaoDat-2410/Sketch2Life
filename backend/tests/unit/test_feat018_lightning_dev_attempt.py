"""Synthetic control/kernel/adapter tests; no Studio, model or process launch."""

from __future__ import annotations

import contextlib
import os
import stat
import socket
import struct
import queue
import threading
from collections import deque
from dataclasses import replace
from pathlib import Path
from threading import RLock
from unittest.mock import Mock
from sketch2life.benchmark import feat018_live_lightning_execution as execution
from sketch2life.interfaces.cli import feat018_lightning_dev_attempt as dev
from sketch2life.infrastructure.ai import feat018_lightning_ssh as ssh

import pytest

from sketch2life.benchmark.feat018_live_lightning_execution import (
    CleanupStatus,
    EffectiveOutcome,
    ProgressEvent,
    ProgressEventKind,
    ProgressState,
    SupervisorRunResult,
)
from sketch2life.contracts.schemas.feat018_live_binding import (
    DevAttemptBudgetsV1,
    DevAttemptControlV1,
    DevAttemptIdentityV1,
    DevAttemptVerificationV1,
)
from sketch2life.interfaces.cli.feat018_lightning_dev_attempt import (
    DevAttemptControlError,
    LinuxKernelInspectionOps,
    OfflineDevAttemptCoordinator,
    PrivateControlSocket,
    PrivateInvocationGate,
    ProcessBirth,
    SeparateInvocationInspector,
    TrustedLaunchRegistry,
    TrustedContainmentCapability,
    ExistingBoundedAdapterInvocation,
    main,
    run_dev_attempt_control,
    run_dev_attempt_host,
    run_dev_attempt_session,
)


def identity(ref: str = "invocation-fixture") -> DevAttemptIdentityV1:
    return DevAttemptIdentityV1(
        studio_ref="studio-fixture", invocation_ref=ref, nonce="a" * 64,
        python_sha256="b" * 64, entry_sha256="c" * 64, config_sha256="d" * 64,
        source_sha256="e" * 64, request_sha256="f" * 64,
    )


def synthetic_path_check(path: Path, directory: bool) -> None:
    # This is an explicit fake permission/ACL boundary on Windows. Link, type and
    # exclusive-file checks still inspect the private pytest temporary fixture.
    facts = path.lstat()
    if stat.S_ISLNK(facts.st_mode) or directory != stat.S_ISDIR(facts.st_mode):
        raise DevAttemptControlError("synthetic private path invalid")
    if not directory and (not stat.S_ISREG(facts.st_mode) or facts.st_nlink != 1):
        raise DevAttemptControlError("synthetic claim links invalid")


@pytest.fixture
def gate(tmp_path: Path) -> PrivateInvocationGate:
    lock = RLock()

    @contextlib.contextmanager
    def lock_file(fd: int):
        with lock:
            yield

    return PrivateInvocationGate(tmp_path, identity(), synthetic_path_check, lock_file)


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


class Controls:
    def __init__(self, clock, messages):
        self.clock = clock
        self.messages = deque(messages)
        self.frames = []
        self.lost = False
        self.poll_count = 0

    def poll(self, timeout_seconds):
        self.poll_count += 1
        self.clock.now += timeout_seconds
        return self.messages.popleft() if self.messages else None

    def eof(self):
        return self.lost

    def send(self, frame):
        self.frames.append(frame)


class Kernel:
    def __init__(self):
        self.births = {10: ProcessBirth(10, "boot-fixture", 100), 90: ProcessBirth(90, "boot-fixture", 900)}
        self.members = {10}
        self.kind = "CGROUP_V2"
        self.complete = True
        self.history_complete = True
        self.history = {self.births[10]}
        self.capability = TrustedContainmentCapability(
            "containment-fixture", "CGROUP_V2", self.births[90], True, True, True,
        )

    def parent_birth(self, birth):
        return self.births.get({11: 10, 12: 11, 13: 11}.get(birth.pid))

    def containment_capability(self, selected):
        return self.capability

    def containment_births(self, selected):
        return tuple(self.history) if self.history_complete else None

    def birth(self, pid):
        if pid in self.members:
            self.history.add(self.births[pid])
        return self.births.get(pid)

    def containment_members(self, selected):
        return tuple(self.births[pid] for pid in self.members) if self.complete else None

    def contained(self, birth, selected):
        return birth.pid in self.members

    def containment_kind(self, selected):
        return self.kind


def successful_verification():
    return DevAttemptVerificationV1(
        v2_status="SUCCEEDED", raw_status="SUCCEEDED", v2_schema_verified=True,
        raw_schema_verified=True, source_matched=True, correlation_matched=True,
        provenance_matched=True, gate_a_required=True, narration_status="NOT_SUPPLIED",
    )


def setup_coordinator(gate, messages=None, adapter=None):
    clock = Clock()
    transcript = [DevAttemptControlV1(identity=gate.identity, operation="OPEN", sequence=0)]
    transcript.extend(messages or [DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1)])
    controls = Controls(clock, transcript)
    kernel = Kernel()
    registry = TrustedLaunchRegistry("containment-fixture", kernel, gate.identity)
    registry.register(10, "SUPERVISOR")
    inspector = SeparateInvocationInspector(kernel, kernel.births[90], clock, lambda: 90, gate)
    calls = []

    def successful_adapter(**hooks):
        calls.append(hooks)
        kernel.births[11] = ProcessBirth(11, "boot-fixture", 110)
        kernel.members.add(11)
        worker = hooks["register_launch"](11, "ADAPTER", kernel.births[10])
        kernel.births[12] = ProcessBirth(12, "boot-fixture", 120)
        kernel.members.add(12)
        hooks["register_launch"](12, "GENERATION", worker.birth)
        hooks["release_guard"](lambda: None)
        hooks["on_accepted_progress"](ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED))
        hooks["on_accepted_progress"](ProgressEvent(2, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=1))
        hooks["on_accepted_progress"](ProgressEvent(3, ProgressEventKind.TERMINAL, outcome="SUCCEEDED", raw_status="SUCCEEDED"))
        hooks["on_cleanup_intent"]()
        kernel.members.clear()
        for pid in (10, 11, 12):
            kernel.births.pop(pid)
        return SupervisorRunResult(
            final_state=ProgressState.TERMINAL, attempt_count=1, terminal_outcome="SUCCEEDED",
            cleanup_status=CleanupStatus.SUCCEEDED, effective_outcome=EffectiveOutcome.SUCCEEDED,
            raw_status="SUCCEEDED", verification_summary=successful_verification(),
        )

    coordinator = OfflineDevAttemptCoordinator(
        gate.identity, DevAttemptBudgetsV1(work_seconds=10.0, cleanup_seconds=2.0, poll_seconds=0.1),
        gate, controls, adapter or successful_adapter, registry, inspector, clock,
    )
    return coordinator, controls, kernel, calls


@pytest.mark.parametrize("entry", [run_dev_attempt_host, run_dev_attempt_session, run_dev_attempt_control])
def test_public_entries_deny_before_argument_or_io_effects(entry):
    hostile = Mock()
    hostile.identity.side_effect = AssertionError("must not access arguments")
    result = entry(hostile, start=True, live=True, io=hostile, authorization=identity())
    assert result.outcome == "NOT_AUTHORIZED"
    assert result.adapter_call_count == 0 and result.cleanup == "NOT_REACHED"
    assert result.live_authorized is False and result.studio_release_proven is False
    assert hostile.mock_calls == []


def test_cli_main_is_denied():
    assert main() == 2


def test_one_exclusive_claim_and_start(gate):
    assert gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN")) == "OPEN"
    assert gate.transition(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1)) == "START"
    with pytest.raises(DevAttemptControlError, match="already sealed"):
        gate.transition(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=2))
    with pytest.raises(DevAttemptControlError, match="already exists"):
        gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    assert gate.claim_path.exists()


def test_cancel_before_open_seals_invocation(gate):
    assert gate.transition(DevAttemptControlV1(identity=gate.identity, operation="CANCEL")) == "CANCEL"
    with pytest.raises(DevAttemptControlError):
        gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    with pytest.raises(DevAttemptControlError):
        gate.transition(DevAttemptControlV1(identity=gate.identity, operation="START"))
    assert gate.state() == "CANCEL"


def test_other_gate_instance_observes_cancel_authority(gate):
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    other = PrivateInvocationGate(gate.root, gate.identity, gate.check_path, gate.lock_file)
    other.transition(DevAttemptControlV1(identity=gate.identity, operation="CANCEL"))
    with pytest.raises(DevAttemptControlError):
        gate.transition(DevAttemptControlV1(identity=gate.identity, operation="START"))


def test_foreign_identity_cannot_touch_claim(gate):
    with pytest.raises(DevAttemptControlError, match="identity mismatch"):
        gate.transition(DevAttemptControlV1(identity=identity("other-fixture"), operation="CANCEL"))
    assert not gate.claim_path.exists()


def test_claim_rejects_corrupt_and_untrusted_json_without_input(gate):
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    private = b'PRIVATE-UNTRUSTED-FIXTURE'
    gate.claim_path.write_bytes(private)
    with pytest.raises(DevAttemptControlError) as caught:
        gate.state()
    assert private.decode() not in str(caught.value)


def test_claim_rejects_hard_link(gate, tmp_path):
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    os.link(gate.claim_path, tmp_path / "alias")
    with pytest.raises(DevAttemptControlError):
        gate.state()


def test_socket_has_no_effect_before_claim(gate):
    factory = Mock(side_effect=AssertionError("no socket before OPEN"))
    endpoint = PrivateControlSocket(gate, socket_factory=factory)
    with pytest.raises((DevAttemptControlError, FileNotFoundError)):
        endpoint.open()
    factory.assert_not_called()


def test_success_uses_existing_adapter_once_and_only_metadata(gate):
    coordinator, controls, _, calls = setup_coordinator(gate)
    result = coordinator.run()
    assert result.outcome == "SUCCEEDED" and result.cleanup == "VERIFIED_OFFLINE"
    assert result.adapter_call_count == 1 and result.attempt_count == 1
    assert result.ownership_retained is False and result.studio_release_proven is False
    assert len(calls) == 1
    assert [frame.kind for frame in controls.frames] == ["READY", "PROGRESS", "PROGRESS", "PROGRESS", "PROGRESS", "TERMINAL"]
    assert [frame.sequence for frame in controls.frames] == [0, 1, 2, 3, 4, 5]
    encoded = "".join(frame.model_dump_json() for frame in controls.frames)
    assert gate.identity.nonce not in encoded and gate.identity.studio_ref not in encoded
    assert "entities" not in encoded and "labels" not in encoded
    assert coordinator.run().outcome == "UNKNOWN" and len(calls) == 1


def test_cancel_before_start_invokes_no_adapter(gate):
    coordinator, _, _, calls = setup_coordinator(gate, [DevAttemptControlV1(identity=gate.identity, operation="CANCEL", sequence=1)])
    result = coordinator.run()
    assert result.outcome == "CANCELLED" and result.cleanup == "NOT_REACHED"
    assert result.adapter_call_count == 0 and calls == []
    assert "CANCELLED_BEFORE_START" in result.failure_codes
    assert gate.state() == "CANCEL"


def test_eof_during_existing_supervisor_poll_cancels_and_retains(gate):
    captured = {}

    def adapter(**hooks):
        captured.update(hooks)
        controls.lost = True
        assert hooks["cancel_requested"]() is True
        return SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    coordinator, controls, _, _ = setup_coordinator(gate, adapter=adapter)
    result = coordinator.run()
    assert result.outcome == "FAILED" and result.ownership_retained is True
    assert result.adapter_call_count is None and result.attempt_count is None
    assert "CONTROL_EOF" in result.failure_codes
    original = coordinator.terminal_cleanup_deadline
    coordinator.clock.now += 0.5
    assert captured["on_cleanup_intent"]() == original


def test_status_and_cancel_are_serviced_inside_bound_call(gate):
    def adapter(**hooks):
        assert hooks["cancel_requested"]() is False
        assert hooks["cancel_requested"]() is True
        return SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    messages = [
        DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1),
        DevAttemptControlV1(identity=gate.identity, operation="STATUS", sequence=2),
        DevAttemptControlV1(identity=gate.identity, operation="CANCEL", sequence=3),
    ]
    coordinator, controls, _, _ = setup_coordinator(gate, messages, adapter)
    result = coordinator.run()
    assert result.outcome == "FAILED" and result.ownership_retained
    assert any(frame.kind == "STATUS" for frame in controls.frames)


def test_duplicate_start_never_invokes_second_adapter(gate):
    def adapter(**hooks):
        assert hooks["cancel_requested"]() is True
        return SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    coordinator, _, _, _ = setup_coordinator(gate, [
        DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1),
        DevAttemptControlV1(identity=gate.identity, operation="START", sequence=2),
    ], adapter)
    result = coordinator.run()
    assert "START_REUSED" in result.failure_codes and result.adapter_call_count is None


@pytest.mark.parametrize("operation", ["OPEN", "INSPECT"])
def test_post_start_open_or_inspect_freezes_without_accepting_more_work(gate, operation):
    invocations = []

    def adapter(**hooks):
        invocations.append(True)
        assert hooks["cancel_requested"]() is True
        return SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    coordinator, _, _, _ = setup_coordinator(gate, [
        DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1),
        DevAttemptControlV1(identity=gate.identity, operation=operation, sequence=2),
    ], adapter)
    result = coordinator.run()
    assert len(invocations) == 1 and "CONTROL_INVALID" in result.failure_codes
    assert result.outcome != "SUCCEEDED" and result.ownership_retained
    assert result.adapter_call_count is None and result.attempt_count is None


def test_frozen_clock_control_poll_is_finite(gate):
    coordinator, controls, _, calls = setup_coordinator(gate)
    controls.poll = lambda timeout_seconds: None
    coordinator.max_polls = 3
    result = coordinator.run()
    assert result.adapter_call_count == 0 and calls == []
    assert "FRAME_LIMIT" in result.failure_codes


def test_work_deadline_still_freezes_during_timed_idle_control_polls(gate):
    coordinator, controls, _, calls = setup_coordinator(gate)
    controls.messages = deque([DevAttemptControlV1(identity=gate.identity, operation="OPEN", sequence=0)])
    result = coordinator.run()
    assert calls == [] and result.adapter_call_count == 0
    assert "WORK_DEADLINE" in result.failure_codes


def test_received_control_frame_limit_still_freezes(gate):
    def adapter(**hooks):
        assert hooks["cancel_requested"]() is True
        return SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    coordinator, _, _, _ = setup_coordinator(gate, [
        DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1),
        DevAttemptControlV1(identity=gate.identity, operation="STATUS", sequence=2),
    ], adapter)
    coordinator.max_polls = 2
    result = coordinator.run()
    assert "FRAME_LIMIT" in result.failure_codes and result.ownership_retained
    assert result.adapter_call_count is None and result.attempt_count is None


@pytest.mark.parametrize("fault,code", [
    ("incomplete", "INSPECTION_INCOMPLETE"),
    ("group_only", "CONTAINMENT_UNAVAILABLE"),
    ("birth_reuse", "BIRTH_REUSED"),
    ("escaped", "CONTAINMENT_ESCAPE"),
    ("inspector_inside", "INSPECTION_INVALID"),
])
def test_independent_inspection_never_promotes_ambiguous_cleanup(gate, fault, code):
    coordinator, _, kernel, _ = setup_coordinator(gate)
    registry = coordinator.registry
    kernel.births[11] = ProcessBirth(11, "boot-fixture", 110)
    kernel.members.add(11)
    registry.register(11, "ADAPTER", kernel.births[10])
    original_worker = kernel.births[11]
    kernel.births.pop(10)
    kernel.births.pop(11)
    kernel.members.clear()
    if fault == "incomplete":
        kernel.complete = False
    elif fault == "group_only":
        kernel.kind = "POSIX_PGID"
    elif fault == "birth_reuse":
        kernel.births[11] = replace(original_worker, start_ticks=999)
    elif fault == "escaped":
        kernel.births[11] = original_worker
    else:
        kernel.members.add(90)
    proof = coordinator.inspector.inspect(registry, coordinator.clock() + 1.0)
    assert proof.outcome != "VERIFIED_OFFLINE" and code in proof.failure_codes


def test_inspection_deadline_does_not_reset(gate):
    coordinator, _, _, _ = setup_coordinator(gate)
    deadline = coordinator.begin_cleanup()
    coordinator.clock.now = deadline
    assert coordinator.begin_cleanup() == deadline
    assert coordinator.inspector.inspect(coordinator.registry, deadline).failure_codes == ("CLEANUP_DEADLINE",)


def test_missing_inspector_retains_ownership_even_after_worker_success(gate):
    coordinator, _, _, _ = setup_coordinator(gate)
    coordinator.inspector = None
    result = coordinator.run()
    assert result.cleanup == "UNKNOWN" and result.ownership_retained
    assert "INSPECTION_MISSING" in result.failure_codes


def test_kernel_birth_uses_boot_and_start_ticks_not_pid(gate):
    values = {
        "/proc/sys/kernel/random/boot_id": "boot-fixture\n",
        "/proc/12/stat": "12 (name with spaces) " + " ".join(["S"] + ["0"] * 18 + ["1234"]),
    }
    kernel = LinuxKernelInspectionOps(Path("/sys/fs/cgroup/task-fixture"), (1, 1), lambda path: values[str(path).replace("\\", "/")])
    assert kernel.birth(12) == ProcessBirth(12, "boot-fixture", 1234)


def test_kernel_missing_process_is_not_a_reused_pid():
    def absent(path):
        if "boot_id" in str(path):
            return "boot-fixture"
        raise FileNotFoundError

    kernel = LinuxKernelInspectionOps(Path("/sys/fs/cgroup/task-fixture"), (1, 1), absent)
    assert kernel.birth(12) is None


def test_kernel_cgroup_population_includes_child_groups(gate, tmp_path):
    selected = tmp_path / "cgroup-fixture"
    selected.mkdir()
    inode = selected.stat()
    values = {"cgroup.events": "populated 1\nfrozen 0\n", "cgroup.procs": ""}
    kernel = LinuxKernelInspectionOps(selected, (inode.st_dev, inode.st_ino), lambda path: values[path.name])
    assert kernel.containment_members(str(selected)) is None
    values["cgroup.events"] = "populated 0\nfrozen 0\n"
    assert kernel.containment_members(str(selected)) == ()


@pytest.mark.parametrize("fault", ["missing", "reuse", "escape", "capability"])
def test_fresh_supervisor_and_capability_are_required_before_adapter(gate, fault):
    coordinator, _, kernel, calls = setup_coordinator(gate)
    if fault == "missing":
        kernel.births.pop(10)
        kernel.members.clear()
    elif fault == "reuse":
        kernel.births[10] = replace(kernel.births[10], start_ticks=101)
    elif fault == "escape":
        kernel.members.clear()
    else:
        kernel.capability = replace(kernel.capability, prevents_escape=False)
    result = coordinator.run()
    assert calls == [] and result.adapter_call_count == 0
    assert result.ownership_retained and result.cleanup == "UNKNOWN"
    assert "CONTAINMENT_UNAVAILABLE" in result.failure_codes


@pytest.mark.parametrize("fault", ["wrong_parent", "reused_parent", "escaped_parent", "stale_child"])
def test_registration_requires_fresh_kernel_parent_lineage(gate, fault):
    coordinator, _, kernel, _ = setup_coordinator(gate)
    kernel.births[11] = ProcessBirth(11, "boot-fixture", 110)
    kernel.members.add(11)
    expected_parent = kernel.births[10]
    if fault == "wrong_parent":
        kernel.parent_birth = lambda child: kernel.births[90]
    elif fault == "reused_parent":
        kernel.births[10] = replace(expected_parent, start_ticks=101)
    elif fault == "escaped_parent":
        kernel.members.remove(10)
    else:
        original_birth = kernel.birth
        reads = []

        def changing_birth(pid):
            if pid == 11:
                reads.append(pid)
                if len(reads) > 1:
                    return replace(kernel.births[11], start_ticks=999)
            return original_birth(pid)

        kernel.birth = changing_birth
    with pytest.raises(DevAttemptControlError, match="parent lineage"):
        coordinator.registry.register(11, "ADAPTER", expected_parent)
    assert coordinator.registry.invalid


def test_pending_gated_process_is_checked_at_release_after_registration(gate):
    coordinator, _, kernel, _ = setup_coordinator(gate)
    kernel.births[11] = ProcessBirth(11, "boot-fixture", 110)
    kernel.members.add(11)
    assert coordinator.registry.live_failure(require_coverage=False) is None
    worker = coordinator.registry.register(11, "ADAPTER", kernel.births[10])
    assert worker.birth == kernel.births[11]
    assert coordinator.registry.live_failure() is None


@pytest.mark.parametrize("omission", ["history_unavailable", "vanished_descendant", "missing_generation"])
def test_inspection_requires_complete_historical_birth_coverage(gate, omission):
    coordinator, _, kernel, _ = setup_coordinator(gate)
    kernel.births[11] = ProcessBirth(11, "boot-fixture", 110)
    kernel.members.add(11)
    coordinator.registry.register(11, "ADAPTER", kernel.births[10])
    if omission == "history_unavailable":
        kernel.history_complete = False
    elif omission == "vanished_descendant":
        kernel.history.add(ProcessBirth(15, "boot-fixture", 150))
    kernel.births.pop(10)
    kernel.births.pop(11)
    kernel.members.clear()
    proof = coordinator.inspector.inspect(coordinator.registry, coordinator.clock() + 1, 1 if omission == "missing_generation" else 0)
    assert proof.outcome == "FAILED" and "INSPECTION_INCOMPLETE" in proof.failure_codes


def test_cgroup_directory_or_boolean_capability_does_not_bind_runtime(tmp_path):
    selected = tmp_path / "cgroup-fixture"
    selected.mkdir()
    facts = selected.stat()
    kernel = LinuxKernelInspectionOps(selected, (facts.st_dev, facts.st_ino), lambda path: "populated 0\n")
    assert kernel.containment_kind(str(selected)) == "UNBOUND"
    assert kernel.containment_births(str(selected)) is None
    kernel.trusted_capability_check = lambda *args: True
    assert kernel.containment_kind(str(selected)) == "UNBOUND"


def test_populated_parent_cgroup_is_not_complete_descendant_census(tmp_path):
    selected = tmp_path / "cgroup-fixture"
    selected.mkdir()
    facts = selected.stat()
    values = {"cgroup.events": "populated 1\n", "cgroup.procs": "10\n"}
    kernel = LinuxKernelInspectionOps(selected, (facts.st_dev, facts.st_ino), lambda path: values[path.name])
    assert kernel.containment_members(str(selected)) is None


def test_kernel_boot_read_failure_cannot_prove_process_absence():
    def missing(path):
        raise FileNotFoundError

    kernel = LinuxKernelInspectionOps(Path("/sys/fs/cgroup/task-fixture"), (1, 1), missing)
    with pytest.raises(DevAttemptControlError, match="boot identity"):
        kernel.birth(12)


def test_cancel_wins_same_lock_before_release(gate):
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1))
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="CANCEL", sequence=2))
    released = []
    with pytest.raises(DevAttemptControlError):
        gate.release_guard(lambda: released.append(True))
    assert released == []


def test_private_release_callback_runs_inside_nonreentrant_authoritative_lock(gate):
    inside = []

    @contextlib.contextmanager
    def lock(fd):
        assert not inside, "release attempted recursive claim acquisition"
        inside.append(True)
        try:
            yield
        finally:
            inside.pop()

    gate.lock_file = lock
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1))
    observed = []
    gate.release_guard(lambda: observed.append(bool(inside)))
    assert observed == [True] and inside == []


def test_failed_cancel_write_retains_ownership_and_original_cleanup_window(gate):
    def adapter(**hooks):
        controls.lost = True
        gate.claim_path.write_bytes(b"corrupt")
        assert hooks["cancel_requested"]()
        original = hooks["on_cleanup_intent"]()
        coordinator.clock.now += 0.5
        assert hooks["on_cleanup_intent"]() == original
        return SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    coordinator, controls, _, _ = setup_coordinator(gate, adapter=adapter)
    result = coordinator.run()
    assert result.ownership_retained and result.cleanup == "UNKNOWN"
    assert "CANCEL_FAILED" in result.failure_codes


def test_late_work_expiry_cannot_extend_cleanup_window(gate):
    coordinator, _, _, _ = setup_coordinator(gate)
    coordinator.work_deadline = 20.0
    coordinator.clock.now = 25.0
    assert coordinator.begin_cleanup() == 22.0
    coordinator.clock.now = 30.0
    assert coordinator.begin_cleanup() == 22.0


@pytest.mark.parametrize("now", [float("nan"), float("inf"), True, "private"])
def test_invalid_remote_clock_rejects_before_claim_or_adapter(gate, now):
    coordinator, _, _, calls = setup_coordinator(gate)
    coordinator.clock = lambda: now
    result = coordinator.run()
    assert result.failure_codes == ("CLOCK_INVALID",)
    assert calls == [] and not gate.claim_path.exists()


class Peer:
    def __init__(self, chunks=(), send_chunk=None):
        self.chunks = deque(chunks)
        self.sent = bytearray()
        self.closed = False
        self.send_chunk = send_chunk

    def recv(self, limit):
        data = self.chunks.popleft()
        assert len(data) <= limit
        return data

    def send(self, data):
        size = min(len(data), self.send_chunk or len(data))
        self.sent.extend(data[:size])
        return size

    def close(self):
        self.closed = True


def socket_fixture(gate, primary=None, secondaries=()):
    listener = Mock()
    endpoint = PrivateControlSocket(gate, select_ready=lambda inputs, *_: ([peer for peer in inputs if peer is not listener and peer.chunks], [], []))
    endpoint._listener = listener
    endpoint._peer = primary or Peer()
    endpoint._secondary.update({peer: bytearray() for peer in secondaries})
    return endpoint


def test_private_socket_uses_same_bounded_ssh_framing_and_partial_writes(gate):
    wire = ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    primary = Peer([wire[:3], wire[3:]], send_chunk=7)
    endpoint = socket_fixture(gate, primary)
    assert endpoint.poll(0.1) is None
    assert endpoint.poll(0.1).operation == "OPEN"
    frame = dev.DevAttemptFrameV1(kind="READY", sequence=0, binding_sha256=gate.identity.canonical_sha256())
    endpoint.send(frame)
    assert bytes(primary.sent) == ssh.encode_attempt_frame(frame)


def test_secondary_status_eof_does_not_end_primary_invocation(gate):
    secondary = Peer([ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="STATUS")), b""])
    endpoint = socket_fixture(gate, secondaries=(secondary,))
    assert endpoint.poll(0.1).operation == "STATUS" and endpoint.secondary_control
    assert endpoint.poll(0.1) is None
    assert not endpoint.eof() and secondary.closed
    endpoint._peer.chunks.append(b"")
    assert endpoint.poll(0.1) is None and endpoint.eof()


def test_secondary_peer_cannot_issue_new_start(gate):
    secondary = Peer([ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="START"))])
    endpoint = socket_fixture(gate, secondaries=(secondary,))
    with pytest.raises(DevAttemptControlError, match="invalid"):
        endpoint.poll(0.1)


@pytest.mark.parametrize("wire", [struct.pack("!I", 0), struct.pack("!I", dev.MAX_CONTROL_BYTES + 1)])
def test_socket_rejects_size_before_payload(gate, wire):
    endpoint = socket_fixture(gate, Peer([wire]))
    with pytest.raises(DevAttemptControlError, match="exceeds limit"):
        endpoint.poll(0.1)


def test_secondary_reply_does_not_consume_primary_progress_sequence(gate):
    coordinator, _, _, _ = setup_coordinator(gate)
    primary = Peer()
    secondary = Peer()
    endpoint = socket_fixture(gate, primary, (secondary,))
    coordinator.controls = endpoint
    coordinator._send("READY")
    endpoint._reply_peer = secondary
    coordinator._send("STATUS", summary=coordinator._running_summary())
    coordinator._send("PROGRESS", progress="CONTAINMENT_READY")
    primary_frames = ssh.IncrementalFrameDecoder().feed(bytes(primary.sent))
    secondary_frames = ssh.IncrementalFrameDecoder().feed(bytes(secondary.sent))
    assert [frame.sequence for frame in primary_frames] == [0, 1]
    assert [frame.sequence for frame in secondary_frames] == [0]


def test_independent_inspection_rejects_unsealed_start_even_if_every_pid_absent(gate):
    coordinator, _, kernel, _ = setup_coordinator(gate)
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1))
    kernel.births[11] = ProcessBirth(11, "boot-fixture", 110)
    kernel.members.add(11)
    coordinator.registry.register(11, "ADAPTER", kernel.births[10])
    kernel.members.clear()
    for pid in (10, 11):
        kernel.births.pop(pid)
    coordinator.registry.launches_sealed = True
    proof = coordinator.inspector.inspect(coordinator.registry, coordinator.clock() + 1, 0)
    assert proof.outcome == "FAILED" and "INSPECTION_INCOMPLETE" in proof.failure_codes
    gate.seal()
    proof = coordinator.inspector.inspect(coordinator.registry, coordinator.clock() + 1, 0)
    assert proof.outcome == "VERIFIED_OFFLINE" and gate.state() == "EOF"
    with pytest.raises(DevAttemptControlError):
        gate.release_guard(lambda: pytest.fail("sealed admission released work"))


def bounded_fixture_config():
    return execution.Feat018BoundedRunnerConfig(
        total_adapter_cap_seconds=9.0, raw_output_max_bytes=1000,
        ipc_envelope_max_bytes=8192, stdout_max_bytes=execution.D9_STDOUT_MAX_BYTES,
        stderr_max_bytes=execution.D9_STDERR_MAX_BYTES, cleanup_deadline_seconds=2.0,
        poll_interval_seconds=0.01,
    )


class HeldAdapterProcess:
    pid = 11
    started_at_monotonic = None

    def __init__(self):
        self.alive = True
        self.joined = False
        self.closed = False

    @property
    def exitcode(self):
        return 0 if not self.alive and self.joined else None

    def is_alive(self):
        return self.alive

    def terminate(self):
        self.alive = False

    def kill(self):
        self.alive = False

    def join(self, timeout):
        self.joined = not self.alive

    def close(self):
        assert self.joined
        self.closed = True


class HeldAdapterConnection:
    """Finite fake IPC exercising the real supervisor's registration protocol."""

    def __init__(self, kernel, clock, *, fault=None, attempts=(1,), idle_after_attempt=None,
                 idle_seconds=0.0):
        self.kernel = kernel
        self.clock = clock
        self.fault = fault
        self.closed = False
        self.sent = []
        self.idle_polls = 0
        self.pending_registration_pid = None
        self.inbox = deque([{"seq": 1, "kind": "ADAPTER_STARTED"}])
        for attempt_number in attempts:
            self.inbox.append({
                "seq": attempt_number + 1, "kind": "GENERATION_ATTEMPT_STARTED",
                "attempt_number": attempt_number,
            })
            self.inbox.append({
                "kind": "DEV_REGISTER_GENERATION", "pid": 11 + attempt_number,
                "attempt_number": attempt_number,
            })
            if idle_after_attempt == attempt_number:
                self.inbox.append({
                    "kind": "_IDLE_FOR", "seconds": idle_seconds, "deadline": None,
                })
        for role, attempt in [(execution.D9ProcessRole.OUTER_ADAPTER_WORKER, None)] + [
            (execution.D9ProcessRole.INNER_GENERATION_CHILD, value) for value in attempts
        ]:
            for stream in execution.D9StreamName:
                self.inbox.append({
                    "kind": "D9_STREAM_OBSERVATION", "process_role": role.value,
                    "attempt_number": attempt, "stream": stream.value, "bytes_seen": 0,
                    "ceiling": execution.D9_STDOUT_MAX_BYTES if stream is execution.D9StreamName.STDOUT else execution.D9_STDERR_MAX_BYTES,
                    "disposition": "ACCEPTED", "terminal_category": "WITHIN_LIMIT", "failure_code": None,
                })
        self.inbox.append({"kind": "DEV_CLEANUP_INTENT"})
        self.inbox.extend([
            {"kind": "DEV_VERIFICATION", "summary": successful_verification().model_dump(mode="json")},
            {"seq": len(attempts) + 2, "kind": "TERMINAL", "outcome": "SUCCEEDED", "raw_status": "SUCCEEDED"},
        ])

    def send_frame(self, frame):
        self.sent.append(dict(frame))
        if frame["kind"] == "CONTAINMENT_READY":
            assert self.kernel.births[11] in self.kernel.history
        if frame["kind"] == "DEV_REGISTERED":
            assert self.kernel.births[self.pending_registration_pid] in self.kernel.history
            self.pending_registration_pid = None

    def recv_frame(self, timeout):
        if not self.inbox:
            return None
        if self.inbox[0]["kind"] == "_IDLE_FOR":
            marker = self.inbox[0]
            if marker["deadline"] is None:
                marker["deadline"] = self.clock.now + marker["seconds"]
            deadline = marker["deadline"]
            if self.clock.now < deadline:
                self.idle_polls += 1
                self.clock.now += min(timeout, deadline - self.clock.now)
                return None
            self.inbox.popleft()
            return self.recv_frame(timeout)
        frame = self.inbox.popleft()
        if frame["kind"] == "GENERATION_ATTEMPT_STARTED" and frame["attempt_number"] > 1:
            for pid in tuple(self.kernel.members):
                if pid >= 12:
                    self.kernel.members.discard(pid)
                    self.kernel.births.pop(pid, None)
        if frame["kind"] == "DEV_REGISTER_GENERATION":
            pid = frame["pid"]
            self.pending_registration_pid = pid
            self.kernel.births[pid] = ProcessBirth(pid, "boot-fixture", pid * 10)
            self.kernel.members.add(pid)
            if self.fault == "generation_parent":
                self.kernel.parent_birth = lambda child: self.kernel.births[90]
        return frame

    def close(self):
        self.closed = True


def bind_actual_composer(monkeypatch, coordinator, kernel, *, fault=None, attempts=(1,),
                         idle_after_attempt=None, idle_seconds=0.0, total_adapter_cap_seconds=9.0):
    process = HeldAdapterProcess()
    connection = HeldAdapterConnection(
        kernel, coordinator.clock, fault=fault, attempts=attempts,
        idle_after_attempt=idle_after_attempt, idle_seconds=idle_seconds,
    )
    launches = []

    class Launcher:
        def launch(self, entry, args):
            assert entry is execution.adapter_worker_entry
            launches.append((entry, args))
            kernel.births[11] = ProcessBirth(11, "boot-fixture", 110)
            kernel.members.add(11)
            return process, connection

    class Containment:
        def create(self):
            pass

        def confirm_worker_contained(self, worker, **options):
            assert worker is process
            return True

        def terminate_all(self, **options):
            for pid in tuple(kernel.members):
                kernel.births.pop(pid, None)
            kernel.members.clear()

        def is_empty(self):
            return not kernel.members

        def close(self):
            assert self.is_empty()

    monkeypatch.setattr(execution, "MultiprocessingProcessLauncher", lambda **kwargs: Launcher())
    monkeypatch.setattr(execution, "create_platform_containment", Containment)
    coordinator.bounded_adapter = ExistingBoundedAdapterInvocation(
        Mock(), Mock(), Mock(), "synthetic prompt",
        replace(bounded_fixture_config(), total_adapter_cap_seconds=total_adapter_cap_seconds),
        "session-fixture", coordinator.clock, lambda duration: setattr(coordinator.clock, "now", coordinator.clock.now + duration),
    )
    return launches, process, connection


def test_existing_composer_uses_real_bounded_supervisor_and_registration_gates(gate, monkeypatch):
    coordinator, controls, kernel, _ = setup_coordinator(gate)
    lock_held = []

    @contextlib.contextmanager
    def exclusive(fd):
        assert not lock_held, "claim lock must not be reentered by release callbacks"
        lock_held.append(True)
        try:
            yield
        finally:
            lock_held.pop()

    gate.lock_file = exclusive
    launches, process, connection = bind_actual_composer(monkeypatch, coordinator, kernel)
    result = coordinator.run()
    assert result.outcome == "SUCCEEDED" and result.cleanup == "VERIFIED_OFFLINE"
    assert result.adapter_call_count == 1 and result.attempt_count == 1
    assert not result.ownership_retained and len(launches) == 1
    assert launches[0][1][-1] is True
    assert process.closed and connection.closed
    assert [frame["kind"] for frame in connection.sent] == ["CONTAINMENT_READY", "DEV_REGISTERED", "DEV_CLEANUP_GRANT"]
    assert [frame.progress for frame in controls.frames if frame.kind == "PROGRESS"] == ["CONTAINMENT_READY", "ADAPTER_STARTED", "GENERATION_ATTEMPT_STARTED", "TERMINAL"]
    assert gate.state() == "EOF"


def test_real_bounded_supervisor_allows_120_second_retry_after_more_than_1024_timed_polls(gate, monkeypatch):
    coordinator, controls, kernel, _ = setup_coordinator(gate)
    coordinator.budgets = coordinator.budgets.model_copy(update={"work_seconds": 130.0, "poll_seconds": 0.05})
    launches, process, connection = bind_actual_composer(
        monkeypatch, coordinator, kernel, attempts=(1, 2), idle_after_attempt=2,
        idle_seconds=120.0, total_adapter_cap_seconds=125.0,
    )
    result = coordinator.run()
    assert result.outcome == "SUCCEEDED" and result.cleanup == "VERIFIED_OFFLINE"
    assert result.adapter_call_count == 1 and result.attempt_count == 2
    assert controls.poll_count > 1024 and connection.idle_polls > 0
    assert coordinator._received_control_frames <= coordinator.max_polls
    assert len(launches) == 1 and process.closed and connection.closed


def test_existing_composer_rejects_bad_generation_parent_before_release(gate, monkeypatch):
    coordinator, _, kernel, _ = setup_coordinator(gate)
    launches, _, connection = bind_actual_composer(monkeypatch, coordinator, kernel, fault="generation_parent")
    result = coordinator.run()
    assert len(launches) == 1 and result.ownership_retained
    assert result.outcome != "SUCCEEDED" and result.cleanup == "UNKNOWN"
    assert "DEV_REGISTERED" not in [frame["kind"] for frame in connection.sent]


def test_existing_composer_cannot_be_called_twice(gate, monkeypatch):
    coordinator, _, kernel, _ = setup_coordinator(gate)
    launches, _, _ = bind_actual_composer(monkeypatch, coordinator, kernel)
    assert coordinator.run().outcome == "SUCCEEDED"
    hooks = dict(
        on_accepted_progress=coordinator.accepted_progress, cancel_requested=coordinator.cancel_requested,
        on_cleanup_intent=coordinator.begin_cleanup, cleanup_deadline=lambda: coordinator.terminal_cleanup_deadline,
        register_launch=coordinator.registry.register, launch_parent_birth=coordinator.registry.registrations[0].birth,
        release_guard=coordinator.release_guard, work_deadline=coordinator.work_deadline,
    )
    with pytest.raises(DevAttemptControlError, match="already used"):
        coordinator.bounded_adapter(**hooks)
    assert len(launches) == 1


def test_supervisor_loss_retains_registered_invocation_even_after_all_pids_disappear(gate):
    def lost(**hooks):
        kernel.births[11] = ProcessBirth(11, "boot-fixture", 110)
        kernel.members.add(11)
        hooks["register_launch"](11, "ADAPTER", kernel.births[10])
        hooks["release_guard"](lambda: None)
        hooks["on_accepted_progress"](ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED))
        hooks["on_cleanup_intent"]()
        kernel.members.clear()
        for pid in (10, 11):
            kernel.births.pop(pid)
        raise RuntimeError("synthetic private supervisor failure")

    coordinator, _, kernel, _ = setup_coordinator(gate, adapter=lost)
    result = coordinator.run()
    assert result.ownership_retained and result.cleanup == "UNKNOWN"
    assert "SUPERVISOR_LOST" in result.failure_codes
    assert "synthetic private" not in result.model_dump_json()


@pytest.mark.parametrize("result_value", [object(), {"success": True}, "synthetic private"])
def test_invalid_supervisor_result_cannot_be_cleanup_proof(gate, result_value):
    coordinator, _, _, _ = setup_coordinator(gate, adapter=lambda **hooks: result_value)
    result = coordinator.run()
    assert result.ownership_retained and result.cleanup == "UNKNOWN"
    assert "PROTOCOL_FAILED" in result.failure_codes


def test_ssh_exchange_and_actual_remote_composer_interoperate_without_clock_equivalence(gate, monkeypatch):
    coordinator, _, kernel, _ = setup_coordinator(gate)
    launches, process, connection = bind_actual_composer(monkeypatch, coordinator, kernel)
    incoming = queue.Queue()
    outgoing = queue.Queue()
    host_clock = Clock()
    host_clock.now = 500.0
    remote_summaries = []
    remote_frames = []
    transport_closed = threading.Event()

    class RemoteControls:
        def poll(self, timeout_seconds):
            coordinator.clock.now += min(timeout_seconds, 0.001)
            try:
                return incoming.get(timeout=0.01)
            except queue.Empty:
                return None

        def eof(self):
            return transport_closed.is_set()

        def send(self, frame):
            remote_frames.append(frame)
            outgoing.put(ssh.encode_attempt_frame(frame))

    class HostIo:
        def __init__(self):
            self.writes = []
            self.closed = False

        def write(self, data):
            assert struct.unpack("!I", data[:4])[0] == len(data) - 4
            self.writes.append(DevAttemptControlV1.model_validate_json(data[4:]))
            incoming.put(data[4:])

        def poll(self, timeout_seconds, max_bytes):
            host_clock.now += min(timeout_seconds, 0.001)
            try:
                payload = outgoing.get(timeout=0.05)
            except queue.Empty:
                return ssh.SshPollResult()
            assert len(payload) <= max_bytes
            return ssh.SshPollResult(stdout=payload)

        def close(self):
            self.closed = True
            transport_closed.set()

    coordinator.controls = RemoteControls()
    io = HostIo()
    thread = threading.Thread(target=lambda: remote_summaries.append(coordinator.run()), daemon=True)
    thread.start()
    binding = ssh.TrustedSshBinding(
        binary_path="/fixture/ssh", identity_file="/fixture/key", known_hosts_file="/fixture/known-hosts",
        remote_python="/fixture/python", studio_id=gate.identity.studio_ref,
        binary_sha256="1" * 64, known_hosts_sha256="2" * 64, host_key_sha256="3" * 64,
        python_sha256=gate.identity.python_sha256,
    )
    owner = ssh.LocalSshOwner()
    accepted = []
    try:
        result = ssh.run_offline_ssh_exchange(
            binding, coordinator.budgets, DevAttemptControlV1(identity=gate.identity, operation="OPEN"),
            io_factory=lambda argv: io, clock=host_clock, binding_check=lambda selected: True,
            local_owner=owner, accepted_frame=accepted.append,
        )
    finally:
        thread.join(timeout=2.0)
    assert not thread.is_alive()
    assert [control.operation for control in io.writes] == ["OPEN", "START"]
    assert remote_summaries[0].outcome == "SUCCEEDED"
    assert result.outcome == "UNKNOWN" and result.failure_codes == ("PROOF_REQUIRED",)
    assert result.ownership_retained and not result.studio_release_proven
    assert result.adapter_call_count == 1 and result.attempt_count == 1
    assert accepted == remote_frames and len(launches) == 1
    assert coordinator.work_deadline < 100.0 and host_clock() > 500.0
    assert process.closed and connection.closed and io.closed and not owner.retained


def test_foreign_sealed_gate_cannot_supply_this_invocations_cleanup_proof(gate):
    coordinator, _, kernel, calls = setup_coordinator(gate)
    other = PrivateInvocationGate(gate.root, identity("other-invocation"), gate.check_path, gate.lock_file)
    other.transition(DevAttemptControlV1(identity=other.identity, operation="OPEN"))
    other.seal()
    coordinator.inspector.gate = other
    result = coordinator.run()
    assert result.failure_codes == ("IDENTITY_MISMATCH",) and result.ownership_retained
    assert calls == [] and not gate.claim_path.exists()
    proof = coordinator.inspector.inspect(coordinator.registry, coordinator.clock() + 1, 0)
    assert "IDENTITY_MISMATCH" in proof.failure_codes and proof.outcome == "FAILED"


def test_private_socket_coordinator_services_secondary_status_without_freezing_or_sequence_gap(gate):
    coordinator, _, _, calls = setup_coordinator(gate)
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    primary = Peer([
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="OPEN", sequence=0)),
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1)),
    ])
    secondary = Peer([ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="STATUS", sequence=0)), b""])
    endpoint = socket_fixture(gate, primary, (secondary,))
    coordinator.controls = endpoint
    result = coordinator.run()
    assert result.outcome == "SUCCEEDED" and len(calls) == 1
    assert not endpoint.eof()
    frames = ssh.IncrementalFrameDecoder().feed(bytes(primary.sent))
    replies = ssh.IncrementalFrameDecoder().feed(bytes(secondary.sent))
    assert [frame.sequence for frame in frames] == list(range(len(frames)))
    assert [frame.kind for frame in replies] == ["STATUS"] and replies[0].sequence == 0


def test_wrong_identity_from_secondary_freezes_and_routes_terminal_to_primary(gate):
    secondary = Peer()

    def adapter(**hooks):
        secondary.chunks.append(ssh.encode_control_frame(DevAttemptControlV1(
            identity=identity("foreign-invocation"), operation="STATUS", sequence=0,
        )))
        assert hooks["cancel_requested"]() is True
        return SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    coordinator, _, _, _ = setup_coordinator(gate, adapter=adapter)
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    primary = Peer([
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="OPEN", sequence=0)),
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1)),
    ])
    endpoint = socket_fixture(gate, primary, (secondary,))
    coordinator.controls = endpoint
    result = coordinator.run()
    primary_frames = ssh.IncrementalFrameDecoder().feed(bytes(primary.sent))
    secondary_frames = ssh.IncrementalFrameDecoder().feed(bytes(secondary.sent))
    assert "IDENTITY_MISMATCH" in result.failure_codes and result.ownership_retained
    assert [frame.kind for frame in primary_frames] == ["READY", "TERMINAL"]
    assert [frame.sequence for frame in primary_frames] == [0, 1]
    assert secondary_frames == ()


def test_bounded_composer_passes_original_remote_deadline_without_reanchoring(gate, monkeypatch):
    coordinator, _, _, _ = setup_coordinator(gate)
    captured = []

    def existing_entry(*args, **hooks):
        captured.append((args, hooks))
        return SupervisorRunResult(ProgressState.NOT_STARTED, None, None, CleanupStatus.SUCCEEDED)

    monkeypatch.setattr(dev, "run_bounded_adapter_call", existing_entry)
    invocation = ExistingBoundedAdapterInvocation(
        Mock(), Mock(), Mock(), "synthetic prompt", bounded_fixture_config(), "session-fixture",
        coordinator.clock, lambda seconds: None,
    )
    invocation(
        on_accepted_progress=coordinator.accepted_progress, cancel_requested=coordinator.cancel_requested,
        on_cleanup_intent=coordinator.begin_cleanup, cleanup_deadline=lambda: coordinator.terminal_cleanup_deadline,
        register_launch=coordinator.registry.register, launch_parent_birth=coordinator.registry.registrations[0].birth,
        release_guard=coordinator.release_guard, work_deadline=13.0,
    )
    args, hooks = captured[0]
    assert args[4].total_adapter_cap_seconds == 3.0
    assert args[4].per_attempt_timeout_seconds == 120.0
    assert hooks["work_deadline_monotonic"] == 13.0
    assert hooks["clock"] is coordinator.clock and hooks["verify_development_results"] is True


def test_cleanup_failure_retains_actionable_original_resources_privately(gate):
    process = Mock()
    failure = execution.Feat018CleanupFailedError(owned_process=process)
    supervisor_result = SupervisorRunResult(
        ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED,
        cleanup_failure=failure,
    )
    coordinator, _, _, _ = setup_coordinator(gate, adapter=lambda **hooks: supervisor_result)
    result = coordinator.run()
    assert result.ownership_retained and result.outcome == "FAILED"
    assert coordinator.retained_supervisor_result is supervisor_result
    assert coordinator.retained_supervisor_result.cleanup_failure.owned_process is process
    assert "owned_process" not in result.model_dump_json() + repr(coordinator)


def test_lost_supervisor_cleanup_error_reference_is_retained_privately(gate):
    process = Mock()
    failure = execution.Feat018CleanupFailedError(owned_process=process)

    def lost(**hooks):
        raise failure

    coordinator, _, _, _ = setup_coordinator(gate, adapter=lost)
    result = coordinator.run()
    assert result.ownership_retained and coordinator.retained_cleanup_error is failure
    assert "owned_process" not in result.model_dump_json() + repr(coordinator)


@pytest.mark.parametrize("fault", ["nan", "backward", "raises"])
def test_remote_clock_loss_during_invocation_is_closed_and_retains(gate, fault):
    def adapter(**hooks):
        if fault == "raises":
            coordinator.clock = lambda: (_ for _ in ()).throw(RuntimeError("synthetic private clock"))
        else:
            coordinator.clock.now = float("nan") if fault == "nan" else 1.0
        assert hooks["cancel_requested"]() is True
        return SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    coordinator, _, _, _ = setup_coordinator(gate, adapter=adapter)
    result = coordinator.run()
    assert result.ownership_retained and result.cleanup == "UNKNOWN"
    assert "CLOCK_INVALID" in result.failure_codes
    assert "synthetic private clock" not in result.model_dump_json()


@pytest.mark.parametrize("fault", ["missing_terminal", "failed_terminal", "raw_status", "final_state", "attempt_count"])
def test_producer_result_cannot_overrule_accepted_progress_facts(gate, fault):
    def adapter(**hooks):
        kernel.births[11] = ProcessBirth(11, "boot-fixture", 110)
        kernel.members.add(11)
        worker = hooks["register_launch"](11, "ADAPTER", kernel.births[10])
        hooks["release_guard"](lambda: None)
        hooks["on_accepted_progress"](ProgressEvent(1, ProgressEventKind.ADAPTER_STARTED))
        kernel.births[12] = ProcessBirth(12, "boot-fixture", 120)
        kernel.members.add(12)
        hooks["register_launch"](12, "GENERATION", worker.birth)
        hooks["on_accepted_progress"](ProgressEvent(2, ProgressEventKind.GENERATION_ATTEMPT_STARTED, attempt_number=1))
        if fault != "missing_terminal":
            status = "FAILED" if fault == "failed_terminal" else "SUCCEEDED"
            hooks["on_accepted_progress"](ProgressEvent(3, ProgressEventKind.TERMINAL, outcome=status, raw_status=status))
        hooks["on_cleanup_intent"]()
        kernel.members.clear()
        for pid in (10, 11, 12):
            kernel.births.pop(pid)
        return SupervisorRunResult(
            ProgressState.FROZEN if fault == "final_state" else ProgressState.TERMINAL,
            2 if fault == "attempt_count" else 1, "SUCCEEDED", CleanupStatus.SUCCEEDED,
            effective_outcome=EffectiveOutcome.SUCCEEDED,
            raw_status="FAILED" if fault == "raw_status" else "SUCCEEDED",
            verification_summary=successful_verification(),
        )

    coordinator, _, kernel, _ = setup_coordinator(gate, adapter=adapter)
    result = coordinator.run()
    assert result.outcome == "FAILED" and result.ownership_retained
    assert result.cleanup == "UNKNOWN" and "PROTOCOL_FAILED" in result.failure_codes


def test_clock_exception_after_bounded_return_retains_original_result(gate):
    failed = SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    def adapter(**hooks):
        coordinator.clock = lambda: (_ for _ in ()).throw(RuntimeError("synthetic private final clock"))
        return failed

    coordinator, _, _, _ = setup_coordinator(gate, adapter=adapter)
    result = coordinator.run()
    assert result.outcome == "FAILED" and result.ownership_retained
    assert "CLOCK_INVALID" in result.failure_codes
    assert coordinator.retained_supervisor_result is failed
    assert "synthetic private final clock" not in result.model_dump_json()


def _r3_decode_peer_frames(peer):
    # Each socket reply is independently bounded; the 1022-reply regression
    # exceeds the host decoder's single-exchange cumulative wire ceiling.
    wire = bytes(peer.sent)
    offset = 0
    frames = []
    while offset < len(wire):
        assert len(wire) - offset >= 4
        size = struct.unpack("!I", wire[offset:offset + 4])[0]
        assert 0 < size <= dev.MAX_CONTROL_BYTES
        end = offset + 4 + size
        assert end <= len(wire)
        decoder = ssh.IncrementalFrameDecoder()
        decoded = decoder.feed(wire[offset:end])
        decoder.eof()
        assert len(decoded) == 1
        frames.extend(decoded)
        offset = end
    return tuple(frames)


def test_r3_secondary_frame_overflow_keeps_terminal_on_primary(gate):
    secondary = Peer()
    failed = SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    def adapter(**hooks):
        for sequence in range(1022):
            secondary.chunks.append(ssh.encode_control_frame(DevAttemptControlV1(
                identity=gate.identity, operation="STATUS", sequence=sequence,
            )))
            assert hooks["cancel_requested"]() is False
        assert coordinator._received_control_frames == 1024
        secondary.chunks.append(ssh.encode_control_frame(DevAttemptControlV1(
            identity=identity("foreign-invocation"), operation="STATUS", sequence=1022,
        )))
        assert hooks["cancel_requested"]() is True
        return failed

    coordinator, _, _, _ = setup_coordinator(gate, adapter=adapter)
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    primary = Peer([
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="OPEN", sequence=0)),
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1)),
    ])
    endpoint = socket_fixture(gate, primary, (secondary,))
    coordinator.controls = endpoint
    result = coordinator.run()
    primary_frames = _r3_decode_peer_frames(primary)
    secondary_frames = _r3_decode_peer_frames(secondary)
    assert coordinator._received_control_frames == 1025
    assert result.failure_codes[0] == "FRAME_LIMIT"
    assert "IDENTITY_MISMATCH" not in result.failure_codes
    assert result.ownership_retained and result.cleanup == "UNKNOWN"
    assert coordinator.retained_supervisor_result is failed
    assert [frame.kind for frame in primary_frames] == ["READY", "TERMINAL"]
    assert [frame.sequence for frame in primary_frames] == [0, 1]
    assert len(secondary_frames) == 1022
    assert all(frame.kind == "STATUS" for frame in secondary_frames)
    assert [frame.sequence for frame in secondary_frames] == list(range(1022))


@pytest.mark.parametrize("primary_writable", [True, False])
def test_r3_primary_eof_with_secondary_control_never_redirects_terminal(gate, primary_writable):
    secondary = Peer()
    failed = SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    def adapter(**hooks):
        primary.chunks.append(b"")
        secondary.chunks.append(ssh.encode_control_frame(DevAttemptControlV1(
            identity=identity("foreign-invocation"), operation="STATUS", sequence=0,
        )))
        if not primary_writable:
            primary.send = Mock(side_effect=BrokenPipeError("synthetic private terminal delivery"))
        assert hooks["cancel_requested"]() is True
        assert endpoint.eof()
        return failed

    coordinator, _, _, _ = setup_coordinator(gate, adapter=adapter)
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    primary = Peer([
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="OPEN", sequence=0)),
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1)),
    ])
    endpoint = socket_fixture(gate, primary, (secondary,))
    coordinator.controls = endpoint
    result = coordinator.run()
    frames = _r3_decode_peer_frames(primary)
    assert coordinator._received_control_frames == 3
    assert result.failure_codes[0] == "CONTROL_EOF"
    assert "IDENTITY_MISMATCH" not in result.failure_codes
    assert result.ownership_retained and result.cleanup == "UNKNOWN"
    assert coordinator.retained_supervisor_result is failed
    assert _r3_decode_peer_frames(secondary) == ()
    assert coordinator._sequence == 1
    if primary_writable:
        assert [frame.kind for frame in frames] == ["READY", "TERMINAL"]
        assert [frame.sequence for frame in frames] == [0, 1]
        assert "TRANSPORT_LOST" not in result.failure_codes
    else:
        assert [frame.kind for frame in frames] == ["READY"]
        assert [frame.sequence for frame in frames] == [0]
        assert result.outcome == "UNKNOWN" and "TRANSPORT_LOST" in result.failure_codes
        assert primary.send.call_count == 1
        assert "synthetic private terminal delivery" not in result.model_dump_json()


def test_r3_valid_secondary_cancel_preserves_ack_and_primary_terminal(gate):
    secondary = Peer()
    failed = SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)
    cleanup_deadlines = []

    def adapter(**hooks):
        secondary.chunks.append(ssh.encode_control_frame(DevAttemptControlV1(
            identity=gate.identity, operation="CANCEL", sequence=0,
        )))
        assert hooks["cancel_requested"]() is True
        cleanup_deadlines.append(hooks["on_cleanup_intent"]())
        coordinator.clock.now += 0.5
        assert hooks["on_cleanup_intent"]() == cleanup_deadlines[0]
        return failed

    coordinator, _, _, _ = setup_coordinator(gate, adapter=adapter)
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    primary = Peer([
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="OPEN", sequence=0)),
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1)),
    ])
    endpoint = socket_fixture(gate, primary, (secondary,))
    coordinator.controls = endpoint
    result = coordinator.run()
    primary_frames = _r3_decode_peer_frames(primary)
    secondary_frames = _r3_decode_peer_frames(secondary)
    assert result.failure_codes[0] == "CANCELLED" and result.ownership_retained
    assert coordinator.terminal_cleanup_deadline == cleanup_deadlines[0] == 12.0
    assert coordinator.registry.launches_sealed and gate.state() == "CANCEL"
    assert coordinator.retained_supervisor_result is failed
    assert [frame.kind for frame in primary_frames] == ["READY", "TERMINAL"]
    assert [frame.sequence for frame in primary_frames] == [0, 1]
    assert [frame.kind for frame in secondary_frames] == ["CANCEL_ACK"]
    assert [frame.sequence for frame in secondary_frames] == [0]


@pytest.mark.parametrize("fault,code", [
    ("idle_overflow", "FRAME_LIMIT"),
    ("selector_exception", "CONTROL_INVALID"),
    ("after_poll_clock", "CONTROL_INVALID"),
    ("clock_invalid", "CLOCK_INVALID"),
    ("gate_state", "PRIVATE_CHANNEL_UNSAFE"),
    ("registry_exception", "REGISTRATION_INVALID"),
    ("status_reply_failure", "CONTROL_INVALID"),
    ("cancel_transition_failure", "CONTROL_INVALID"),
    ("adapter_exception", "ADAPTER_FAILED"),
])
def test_r3_stale_secondary_reply_cannot_leak_on_rejection_or_exception(gate, monkeypatch, fault, code):
    secondary = Peer()
    failed = SupervisorRunResult(ProgressState.FROZEN, None, None, CleanupStatus.CLEANUP_FAILED)

    def unavailable(*args, **kwargs):
        raise RuntimeError("synthetic private stale reply fault")

    def adapter(**hooks):
        endpoint._reply_peer = secondary
        if fault == "idle_overflow":
            coordinator._idle_polls_without_clock_progress = coordinator.max_polls
        elif fault == "selector_exception":
            endpoint.select_ready = unavailable
        elif fault == "after_poll_clock":
            def invalidate_clock(*args):
                coordinator.clock.now = float("nan")
                return [], [], []
            endpoint.select_ready = invalidate_clock
        elif fault == "clock_invalid":
            coordinator.clock.now = float("nan")
        elif fault == "gate_state":
            monkeypatch.setattr(PrivateInvocationGate, "state", unavailable)
        elif fault == "registry_exception":
            monkeypatch.setattr(TrustedLaunchRegistry, "live_failure", unavailable)
        elif fault == "status_reply_failure":
            secondary.chunks.append(ssh.encode_control_frame(DevAttemptControlV1(
                identity=gate.identity, operation="STATUS", sequence=0,
            )))
            secondary.send = Mock(side_effect=BlockingIOError("synthetic private reply delivery"))
        elif fault == "cancel_transition_failure":
            secondary.chunks.append(ssh.encode_control_frame(DevAttemptControlV1(
                identity=gate.identity, operation="CANCEL", sequence=0,
            )))
            monkeypatch.setattr(PrivateInvocationGate, "transition", unavailable)
        else:
            unavailable()
        assert hooks["cancel_requested"]() is True
        return failed

    coordinator, _, _, _ = setup_coordinator(gate, adapter=adapter)
    gate.transition(DevAttemptControlV1(identity=gate.identity, operation="OPEN"))
    primary = Peer([
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="OPEN", sequence=0)),
        ssh.encode_control_frame(DevAttemptControlV1(identity=gate.identity, operation="START", sequence=1)),
    ])
    endpoint = socket_fixture(gate, primary, (secondary,))
    coordinator.controls = endpoint
    result = coordinator.run()
    primary_frames = _r3_decode_peer_frames(primary)
    assert result.failure_codes[0] == code
    assert result.ownership_retained and result.cleanup == "UNKNOWN"
    assert [frame.kind for frame in primary_frames] == ["READY", "TERMINAL"]
    assert [frame.sequence for frame in primary_frames] == [0, 1]
    assert _r3_decode_peer_frames(secondary) == ()
    assert endpoint._reply_peer is None
    assert coordinator._sequence == 1
    if fault == "adapter_exception":
        assert isinstance(coordinator.retained_cleanup_error, RuntimeError)
    else:
        assert coordinator.retained_supervisor_result is failed
    assert "synthetic private" not in result.model_dump_json()


@pytest.mark.parametrize("kind", ["READY", "PROGRESS", "VERIFICATION", "TERMINAL", "INSPECTION", "ERROR"])
def test_r3_every_lifecycle_kind_uses_primary_sequence_despite_stale_reply(gate, kind):
    coordinator, _, _, _ = setup_coordinator(gate)
    primary = Peer()
    secondary = Peer()
    endpoint = socket_fixture(gate, primary, (secondary,))
    coordinator.controls = endpoint
    coordinator._send("READY")
    endpoint._reply_peer = secondary
    if kind == "READY":
        coordinator._send(kind)
    elif kind == "PROGRESS":
        coordinator._send(kind, progress="CONTAINMENT_READY")
    else:
        coordinator._send(kind, summary=dev.DevAttemptSummaryV1(
            outcome="RUNNING", verification=successful_verification(),
        ))
    frames = _r3_decode_peer_frames(primary)
    assert [frame.kind for frame in frames] == ["READY", kind]
    assert [frame.sequence for frame in frames] == [0, 1]
    assert _r3_decode_peer_frames(secondary) == ()
    assert endpoint._reply_peer is None and coordinator._sequence == 1


@pytest.mark.parametrize("kind", ["STATUS", "CANCEL_ACK"])
def test_r3_valid_replies_keep_each_secondary_sequence_distinct_from_primary(gate, kind):
    coordinator, _, _, _ = setup_coordinator(gate)
    primary = Peer()
    first = Peer()
    second = Peer()
    endpoint = socket_fixture(gate, primary, (first, second))
    coordinator.controls = endpoint
    coordinator._send("READY")
    summary = dev.DevAttemptSummaryV1(outcome="RUNNING" if kind == "STATUS" else "CANCELLED")
    for peer in (first, second, first):
        endpoint._reply_peer = peer
        coordinator._send(kind, summary=summary)
    coordinator._send("PROGRESS", progress="CONTAINMENT_READY")
    primary_frames = _r3_decode_peer_frames(primary)
    first_frames = _r3_decode_peer_frames(first)
    second_frames = _r3_decode_peer_frames(second)
    assert [frame.kind for frame in primary_frames] == ["READY", "PROGRESS"]
    assert [frame.sequence for frame in primary_frames] == [0, 1]
    assert [frame.kind for frame in first_frames] == [kind, kind]
    assert [frame.sequence for frame in first_frames] == [0, 1]
    assert [frame.kind for frame in second_frames] == [kind]
    assert [frame.sequence for frame in second_frames] == [0]
