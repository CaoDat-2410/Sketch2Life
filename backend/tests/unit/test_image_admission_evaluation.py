"""FEAT-018 P2-T1 D3 evaluation-harness contract tests."""

from __future__ import annotations

import ctypes
import hashlib
import io
import json
import subprocess
import sys
import zlib
from pathlib import Path
from typing import Any

import pytest

from sketch2life.application.services.image_admission import (
    Feat018AdmissionRequest,
    Feat018ImageAdmission,
)
from sketch2life.benchmark import image_admission_evaluation as module
from sketch2life.benchmark.image_admission_evaluation import (
    ChildFailure,
    ChildRequest,
    DecodeStage,
    ProcessMemorySnapshot,
    TargetStatus,
    WindowsProcessMemoryReader,
    aggregate_profile,
    calibrate_memory_reader,
    classify_memory,
    classify_timing,
    has_order_effect,
    load_evaluation_manifest,
    materialize_cohort_a,
    nearest_rank_percentile,
    run_bounded_process,
    run_child_sample,
    summarize_cohort_a,
    validate_child_output,
)
from sketch2life.infrastructure.media_validation.av_image_decoder import AvImageDecoder

_REPOSITORY_ROOT = Path(__file__).parents[3]
_MANIFEST = (
    _REPOSITORY_ROOT
    / "features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/"
    "evaluation-manifest-v1.json"
)
_MIB = 1024 * 1024


def _memory(current: int, peak: int, private: int = 1) -> ProcessMemorySnapshot:
    return ProcessMemorySnapshot(current, peak, private)


@pytest.mark.parametrize(
    ("before", "after", "expected", "lower", "upper"),
    [
        (_memory(100, 500), _memory(200, 500), TargetStatus.WITHIN_TARGET, 100, 400),
        (
            _memory(100 * _MIB, 200 * _MIB),
            _memory(400 * _MIB, 450 * _MIB),
            TargetStatus.EXCEEDS_TARGET,
            300 * _MIB,
            350 * _MIB,
        ),
        (
            _memory(500 * _MIB, 800 * _MIB),
            _memory(100 * _MIB, 900 * _MIB),
            TargetStatus.INCONCLUSIVE,
            0,
            400 * _MIB,
        ),
    ],
)
def test_memory_bracket_truth_table(
    before: ProcessMemorySnapshot,
    after: ProcessMemorySnapshot,
    expected: TargetStatus,
    lower: int,
    upper: int,
) -> None:
    result = classify_memory(before, after)

    assert result.status is expected
    assert result.lower_bound_bytes == lower
    assert result.upper_bound_bytes == upper


def test_memory_counterexample_cannot_false_pass_from_peak_delta() -> None:
    before = _memory(500 * _MIB, 800 * _MIB)
    after = _memory(100 * _MIB, 900 * _MIB)

    result = classify_memory(before, after)

    assert after.peak_working_set_bytes - before.peak_working_set_bytes == 100 * _MIB
    assert result.status is TargetStatus.INCONCLUSIVE
    assert result.upper_bound_bytes == 400 * _MIB


def test_current_and_private_usage_may_decrease() -> None:
    result = classify_memory(_memory(300, 500, 300), _memory(200, 500, 200))

    assert result.lower_bound_bytes == 0
    assert result.status is TargetStatus.WITHIN_TARGET


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (_memory(0, 1), _memory(1, 1)),
        (_memory(1, 10), _memory(1, 9)),
        (_memory(11, 10), _memory(1, 10)),
        (_memory(1, 10), _memory(11, 10)),
    ],
)
def test_impossible_memory_values_are_invalid(
    before: ProcessMemorySnapshot, after: ProcessMemorySnapshot
) -> None:
    assert classify_memory(before, after).status is TargetStatus.MEASUREMENT_INVALID


def test_unavailable_memory_is_explicitly_not_measured() -> None:
    result = classify_memory(None, None)

    assert result.status is TargetStatus.NOT_MEASURED
    assert result.lower_bound_bytes is None


def test_windows_structure_uses_size_t_for_every_size_field() -> None:
    fields = {field[0]: field[1] for field in module._PROCESS_MEMORY_COUNTERS_EX._fields_}

    assert fields["cb"] is ctypes.c_ulong
    assert fields["PageFaultCount"] is ctypes.c_ulong
    for name in fields.keys() - {"cb", "PageFaultCount"}:
        assert fields[name] is ctypes.c_size_t


def test_windows_reader_sets_cb_and_checks_query_bool() -> None:
    observed_cb = 0

    def query(counters: Any) -> tuple[bool, int]:
        nonlocal observed_cb
        observed_cb = counters.cb
        counters.WorkingSetSize = 10
        counters.PeakWorkingSetSize = 20
        counters.PrivateUsage = 5
        return True, 999

    result = WindowsProcessMemoryReader(query).read()

    assert observed_cb == ctypes.sizeof(module._PROCESS_MEMORY_COUNTERS_EX)
    assert result == ProcessMemorySnapshot(10, 20, 5)


def test_windows_reader_preserves_bounded_last_error_on_false_return() -> None:
    def query(_counters: Any) -> tuple[bool, int]:
        return False, 87

    with pytest.raises(module.MemoryReadError) as raised:
        WindowsProcessMemoryReader(query).read()

    assert raised.value.error_code == 87


@pytest.mark.parametrize(
    ("elapsed", "status"),
    [
        (5_000.0, TargetStatus.WITHIN_TARGET),
        (5_000.001, TargetStatus.EXCEEDS_TARGET),
        (None, TargetStatus.MEASUREMENT_INVALID),
        (-1.0, TargetStatus.MEASUREMENT_INVALID),
    ],
)
def test_timing_classification_uses_only_admission_elapsed(
    elapsed: float | None, status: TargetStatus
) -> None:
    assert classify_timing(elapsed) is status


def test_nearest_rank_p95_and_cohort_summary() -> None:
    values = [float(value) for value in range(1, 21)]

    assert nearest_rank_percentile(values, 0.95) == 19.0
    assert summarize_cohort_a(values) == {
        "sample_count": 20,
        "p50": 10.5,
        "p95": 19.0,
        "maximum": 20.0,
    }


def test_cohort_a_summary_refuses_too_few_samples() -> None:
    with pytest.raises(ValueError, match="at least 20"):
        summarize_cohort_a([1.0] * 19)


def test_order_effect_threshold_is_strictly_greater_than_ten_percent() -> None:
    assert not has_order_effect([100.0] * 5 + [90.0] * 5)
    assert has_order_effect([100.0] * 5 + [89.0] * 5)


def _sample(
    *,
    timing: TargetStatus = TargetStatus.WITHIN_TARGET,
    memory: TargetStatus = TargetStatus.WITHIN_TARGET,
    failure: str | None = None,
) -> dict[str, object]:
    return {
        "admission_elapsed_ms": 10.0,
        "timing_status": timing.value,
        "memory_status": memory.value,
        "measurement_failure": failure,
        "failure": None,
        "exit_code": 0,
    }


def test_profile_aggregate_never_turns_inconclusive_into_pass() -> None:
    samples = [_sample() for _ in range(19)] + [
        _sample(memory=TargetStatus.INCONCLUSIVE)
    ]

    aggregate = aggregate_profile(samples)

    assert aggregate["timing_status"] == "WITHIN_TARGET"
    assert aggregate["memory_status"] == "INCONCLUSIVE"
    assert aggregate["memory_inconclusive_count"] == 1


def test_profile_aggregate_keeps_typed_failure_separate() -> None:
    samples = [_sample() for _ in range(19)] + [
        _sample(failure="MEMORY_API_FAILURE")
    ]

    aggregate = aggregate_profile(samples)

    assert aggregate["memory_status"] == "MEASUREMENT_INVALID"
    assert aggregate["timing_status"] == "WITHIN_TARGET"
    assert aggregate["process_failure_count"] == 0
    assert aggregate["memory_failure_count"] == 1


@pytest.mark.parametrize("bad_elapsed", [True, float("nan"), float("inf")])
def test_profile_aggregate_rejects_non_numeric_or_non_finite_timing(
    bad_elapsed: object,
) -> None:
    samples = [_sample() for _ in range(20)]
    samples[-1]["admission_elapsed_ms"] = bad_elapsed

    aggregate = aggregate_profile(samples)

    assert aggregate["timing_status"] == "MEASUREMENT_INVALID"
    assert aggregate["sample_count"] == 19


def test_profile_aggregate_rejects_spoofed_timing_status() -> None:
    samples = [_sample() for _ in range(20)]
    samples[-1]["admission_elapsed_ms"] = 6_000.0
    samples[-1]["timing_status"] = TargetStatus.WITHIN_TARGET.value

    aggregate = aggregate_profile(samples)

    assert aggregate["timing_status"] == TargetStatus.MEASUREMENT_INVALID.value
    assert aggregate["sample_count"] == 19


def test_known_allocation_calibration_records_wiring_only_scope() -> None:
    class Reader:
        def __init__(self) -> None:
            self.reads = iter([_memory(100, 100), _memory(116, 116)])

        def read(self) -> ProcessMemorySnapshot:
            return next(self.reads)

    result = calibrate_memory_reader(Reader(), allocation_bytes=16, tolerance=0.25)

    assert result["calibrated"] is True
    assert result["scope"] == "adapter-wiring-only"


def test_manifest_is_typed_unique_and_covers_required_groups() -> None:
    profiles = load_evaluation_manifest(_MANIFEST)

    assert len(profiles) == 16
    assert len({profile.fixture_id for profile in profiles}) == 16
    assert {profile.decode_stage for profile in profiles} == set(DecodeStage)
    assert {profile.generator for profile in profiles} == set(module.GENERATORS)


@pytest.mark.parametrize("mutation", ["wrong-version", "extra-key", "partial-profiles"])
def test_manifest_rejects_protocol_or_profile_set_drift(
    tmp_path: Path, mutation: str
) -> None:
    document = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    if mutation == "wrong-version":
        document["contract_version"] = "2.0"
    elif mutation == "extra-key":
        document["unexpected"] = True
    else:
        document["profiles"] = document["profiles"][:-1]
    path = tmp_path / "drifted-manifest.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError):
        load_evaluation_manifest(path)


def test_materialized_sources_are_hash_stable_and_match_d2(
    tmp_path: Path,
) -> None:
    profiles = load_evaluation_manifest(_MANIFEST)
    sources = materialize_cohort_a(profiles, tmp_path / "fixtures")
    service = Feat018ImageAdmission(AvImageDecoder())

    for profile in profiles:
        path, digest = sources[profile.fixture_id]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        result = service.admit(
            Feat018AdmissionRequest(path=path, artifact_ref=f"fixture:{profile.fixture_id}")
        )
        assert result.decision.outcome.value == profile.expected_outcome
        actual_reason = result.decision.reason.value if result.decision.reason else None
        assert actual_reason == profile.expected_reason


def test_input_larger_than_cap_is_rejected_before_spawn() -> None:
    result = run_bounded_process(
        [sys.executable, "-c", "raise SystemExit(99)"],
        b"x" * (module.MAX_PROTOCOL_BYTES + 1),
        timeout_seconds=1,
    )

    assert result.exit_code is None
    assert result.failure is ChildFailure.INVALID_REQUEST


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_child_output_cap_terminates_process(stream: str) -> None:
    code = (
        "import sys,time; "
        f"sys.{stream}.buffer.write(b'x'*70000); sys.{stream}.flush(); time.sleep(10)"
    )
    result = run_bounded_process(
        [sys.executable, "-c", code], b"", timeout_seconds=5
    )

    assert result.failure is ChildFailure.OUTPUT_LIMIT_EXCEEDED
    assert len(result.stdout) <= module.MAX_PROTOCOL_BYTES
    assert len(result.stderr) <= module.MAX_PROTOCOL_BYTES


def test_parent_timeout_terminates_child_and_returns_typed_failure() -> None:
    result = run_bounded_process(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        b"",
        timeout_seconds=0.05,
    )

    assert result.failure is ChildFailure.HARNESS_TIMEOUT
    assert result.exit_code is not None


def test_parent_timeout_is_reached_when_child_does_not_read_stdin() -> None:
    result = run_bounded_process(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        b"x" * module.MAX_PROTOCOL_BYTES,
        timeout_seconds=0.05,
    )

    assert result.failure is ChildFailure.HARNESS_TIMEOUT
    assert result.exit_code is not None


@pytest.mark.parametrize("timeout", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_timeout_is_rejected_before_spawn(timeout: float) -> None:
    result = run_bounded_process([sys.executable], b"", timeout_seconds=timeout)

    assert result.failure is ChildFailure.INVALID_REQUEST
    assert result.exit_code is None


def test_unstoppable_child_is_reported_as_cleanup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnstoppableProcess:
        def __init__(self) -> None:
            self.stdin = io.BytesIO()
            self.stdout = io.BytesIO()
            self.stderr = io.BytesIO()

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            raise OSError("cannot terminate")

        def kill(self) -> None:
            raise OSError("cannot kill")

        def wait(self, timeout: float) -> None:
            del timeout
            raise subprocess.TimeoutExpired("fake", 2)

    monkeypatch.setattr(subprocess, "Popen", lambda *_args, **_kwargs: UnstoppableProcess())

    result = run_bounded_process(["fake"], b"", timeout_seconds=0.01)

    assert result.failure is ChildFailure.PROCESS_CLEANUP_FAILED


def test_spawn_failure_is_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_spawn(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated missing interpreter")

    monkeypatch.setattr(subprocess, "Popen", fail_spawn)

    result = run_bounded_process(["missing"], b"", timeout_seconds=1)

    assert result.failure is ChildFailure.ABNORMAL_EXIT
    assert result.exit_code is None


def test_real_child_is_fresh_typed_and_redacts_source_path(tmp_path: Path) -> None:
    source = tmp_path / "secret-machine-path.png"
    payload = module.GENERATORS["rgb8-png"]()
    source.write_bytes(payload)
    request = ChildRequest(
        sample_id="opaque:sample:1",
        fixture_id="rgb8-png",
        cohort="A",
        repeat_index=0,
        source_path=str(source.resolve()),
        expected_sha256=hashlib.sha256(payload).hexdigest(),
        expected_source_bytes=len(payload),
        commit_identity="test-working-tree",
    )

    result = run_child_sample(request)
    serialized = json.dumps(result, sort_keys=True)

    assert result["exit_code"] == 0
    assert result["outcome"] == "ADMITTED"
    assert result["source_digest_verified"] is True
    assert result["artifact_ref_verified"] is True
    assert result["sample_id"] == "opaque:sample:1"
    assert str(source) not in serialized
    assert "secret-machine-path" not in serialized
    assert "Traceback" not in serialized
    parent_wall = result["parent_wall_ms"]
    admission_elapsed = result["admission_elapsed_ms"]
    assert isinstance(parent_wall, (int, float))
    assert isinstance(admission_elapsed, (int, float))
    assert parent_wall >= admission_elapsed


def test_child_invalid_request_never_emits_traceback() -> None:
    execution = run_bounded_process(
        [
            sys.executable,
            "-m",
            "sketch2life.benchmark.image_admission_evaluation",
            "--child",
        ],
        b"not-json",
        timeout_seconds=5,
    )

    assert execution.exit_code == 2
    assert b"Traceback" not in execution.stdout
    assert b"Traceback" not in execution.stderr
    assert json.loads(execution.stdout)["failure"] == "CHILD_PROTOCOL_FAILURE"


def _valid_child_document(request: ChildRequest) -> dict[str, object]:
    return {
        "protocol_name": module.PROTOCOL_NAME,
        "protocol_version": module.PROTOCOL_VERSION,
        "sample_id": request.sample_id,
        "fixture_id": request.fixture_id,
        "cohort": request.cohort,
        "repeat_index": request.repeat_index,
        "source_sha256": request.expected_sha256,
        "source_digest_verified": True,
        "source_bytes": request.expected_source_bytes,
        "outcome": "ADMITTED",
        "reason": None,
        "metadata": None,
        "artifact_ref_verified": True,
        "limits": {},
        "admission_elapsed_ms": 1.0,
        "timing_status": "WITHIN_TARGET",
        "working_set_before_bytes": 1,
        "working_set_after_bytes": 1,
        "peak_before_bytes": 1,
        "peak_after_bytes": 1,
        "private_usage_before_bytes": 1,
        "private_usage_after_bytes": 1,
        "memory_lower_bound_bytes": 0,
        "memory_upper_bound_bytes": 0,
        "peak_saturated": True,
        "memory_status": "WITHIN_TARGET",
        "measurement_failure": None,
        "measurement_error_code": None,
        "environment": {
            "python": "3.12.0",
            "pyav": "18.1.0",
            "ffmpeg_libraries": {},
            "os": "Windows",
            "os_release": "test",
            "architecture": "AMD64",
            "commit_identity": request.commit_identity,
        },
    }


def test_child_output_validator_rejects_path_and_identity_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "private.png"
    request = ChildRequest(
        "opaque:1", "rgb8-png", "A", 0, str(path), "a" * 64, 1, "abc123"
    )
    valid_keys = _valid_child_document(request)
    valid_keys["sample_id"] = "wrong"

    with pytest.raises(ValueError, match="identity mismatch"):
        validate_child_output(valid_keys, request)

    valid_keys["sample_id"] = request.sample_id
    valid_keys["metadata"] = {"diagnostic": f"prefix:{path}:suffix"}
    with pytest.raises(ValueError, match="source path"):
        validate_child_output(valid_keys, request)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("timing_status", "EXCEEDS_TARGET", "timing classification"),
        ("memory_upper_bound_bytes", 9, "memory classification"),
        ("admission_elapsed_ms", True, "admission time"),
        ("source_digest_verified", False, "source digest"),
        ("source_bytes", 2, "source byte count"),
    ],
)
def test_child_output_validator_recomputes_load_bearing_fields(
    field: str, value: object, message: str
) -> None:
    request = ChildRequest("opaque:1", "rgb8-png", "A", 0, "input.png", "a" * 64, 1, "abc123")
    document = _valid_child_document(request)
    document[field] = value

    with pytest.raises(ValueError, match=message):
        validate_child_output(document, request)


def test_child_output_validator_accepts_failed_after_memory_read() -> None:
    request = ChildRequest("opaque:1", "rgb8-png", "A", 0, "input.png", "a" * 64, 1, "abc123")
    document = _valid_child_document(request)
    document.update(
        {
            "working_set_after_bytes": None,
            "peak_after_bytes": None,
            "private_usage_after_bytes": None,
            "memory_lower_bound_bytes": None,
            "memory_upper_bound_bytes": None,
            "peak_saturated": None,
            "memory_status": "MEASUREMENT_INVALID",
            "measurement_failure": "MEMORY_API_FAILURE",
            "measurement_error_code": 87,
        }
    )

    validate_child_output(document, request)


def test_child_output_validator_only_allows_missing_digest_for_byte_rejection() -> None:
    request = ChildRequest("opaque:1", "rgb8-png", "A", 0, "input.png", "a" * 64, 1, "abc123")
    document = _valid_child_document(request)
    document["source_sha256"] = None
    document["source_digest_verified"] = None

    with pytest.raises(ValueError, match="missing digest"):
        validate_child_output(document, request)


def test_parent_preserves_sanitized_typed_child_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = ChildRequest("opaque:1", "rgb8-png", "A", 0, "input.png", "a" * 64, 1, "abc123")
    encoded = module._encode_json(
        module._bounded_error(ChildFailure.CHILD_PROTOCOL_FAILURE, "child failed")
    )

    def fake_process(*_args: object, **_kwargs: object) -> module.ProcessExecution:
        return module.ProcessExecution(2, encoded, b"", 3.0, ChildFailure.ABNORMAL_EXIT)

    monkeypatch.setattr(module, "run_bounded_process", fake_process)

    result = run_child_sample(request)

    assert result["failure"] == "CHILD_PROTOCOL_FAILURE"
    assert result["exit_code"] == 2


def test_palette_generator_uses_only_declared_palette_indices() -> None:
    payload = module.GENERATORS["palette8-png"]()
    idat = payload.index(b"IDAT")
    length = int.from_bytes(payload[idat - 4 : idat], "big")
    scanlines = zlib.decompress(payload[idat + 4 : idat + 4 + length])

    assert set(scanlines) <= {0}


def test_formal_cohort_rejects_non_commit_identity() -> None:
    with pytest.raises(ValueError, match="exact lowercase commit SHA"):
        module.run_cohort_a(_MANIFEST, commit_identity="working-tree")


def test_order_effect_preserves_and_aggregates_both_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "contract_name": "Feat018ImageAdmissionEvaluationManifestV1",
                "contract_version": "1.0",
                "data_policy": "synthetic-only",
                "profiles": [
                    {
                        "fixture_id": "rgb8-png",
                        "generator": "rgb8-png",
                        "expected_outcome": "ADMITTED",
                        "expected_reason": None,
                        "decode_stage": "ADMITTED",
                        "synthetic_data": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_run(request: ChildRequest, *, timeout_seconds: float) -> dict[str, object]:
        del timeout_seconds
        elapsed = 100.0 if request.repeat_index < 5 else 50.0
        return {
            "sample_id": request.sample_id,
            "fixture_id": request.fixture_id,
            "outcome": "ADMITTED",
            "reason": None,
            "source_sha256": request.expected_sha256,
            "source_digest_verified": True,
            "artifact_ref_verified": True,
            "admission_elapsed_ms": elapsed,
            "timing_status": "WITHIN_TARGET",
            "memory_status": "WITHIN_TARGET",
            "memory_lower_bound_bytes": 0,
            "memory_upper_bound_bytes": 1,
            "measurement_failure": None,
            "failure": None,
            "parent_wall_ms": elapsed + 1,
            "exit_code": 0,
        }

    monkeypatch.setattr(module, "run_child_sample", fake_run)

    monkeypatch.setattr(module, "GENERATORS", {"rgb8-png": module.GENERATORS["rgb8-png"]})

    report = module.run_cohort_a(
        manifest,
        repeats=20,
        commit_identity="a" * 40,
        head_resolver=lambda: "a" * 40,
    )

    assert report["complete"] is True
    assert report["reverse_pass_required"] is True
    passes = report["passes"]
    assert isinstance(passes, list)
    assert [item["pass_id"] for item in passes] == ["forward", "reverse"]
    assert all(
        sample["expected_outcome"] == "ADMITTED"
        for item in passes
        for sample in item["samples"]
    )
    pass_aggregates = report["pass_aggregates"]
    assert isinstance(pass_aggregates, dict)
    assert set(pass_aggregates) == {"forward", "reverse"}


def test_formal_cohort_rejects_declared_commit_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        module.run_cohort_a(
            _MANIFEST,
            commit_identity="a" * 40,
            head_resolver=lambda: "b" * 40,
        )


def test_clean_head_rejects_untracked_worktree(monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        def __init__(self, *, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.returncode = returncode

    calls = iter(
        [
            Result(stdout="a" * 40 + "\n"),
            Result(),
            Result(stdout="?? backend/untracked.py\n"),
        ]
    )

    def fake_run(*_args: object, **_kwargs: object) -> Result:
        return next(calls)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="clean worktree"):
        module._resolve_clean_git_head(_MANIFEST)
