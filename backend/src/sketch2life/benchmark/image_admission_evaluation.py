"""FEAT-018 P2-T1 D3 offline image-admission evaluation harness.

This module is deliberately separate from production admission.  It measures one D2
``admit`` call in a fresh child process and emits only bounded, path-free diagnostics.
The parent timeout is cleanup for the benchmark; it is not a production guarantee.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import hashlib
import io
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from struct import pack
from typing import BinaryIO, Protocol, TypeGuard, cast
from zlib import compress, crc32

from sketch2life.application.services.image_admission import (
    Feat018AdmissionRequest,
    Feat018ImageAdmission,
)
from sketch2life.domain.understanding.image_admission import (
    AdmissionOutcome,
    AdmissionReason,
    Feat018AdmissionLimits,
    outcome_for_reason,
)

PROTOCOL_NAME = "Feat018ImageAdmissionEvaluationV1"
PROTOCOL_VERSION = "1.0"
MAX_PROTOCOL_BYTES = 64 * 1024
MEMORY_TARGET_BYTES = 256 * 1024 * 1024
TIMING_TARGET_MS = 5_000.0
DEFAULT_CHILD_TIMEOUT_SECONDS = 30.0
_OPAQUE_ID_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_:.")


class TargetStatus(StrEnum):
    WITHIN_TARGET = "WITHIN_TARGET"
    EXCEEDS_TARGET = "EXCEEDS_TARGET"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_MEASURED = "NOT_MEASURED"
    MEASUREMENT_INVALID = "MEASUREMENT_INVALID"


class ChildFailure(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    MEMORY_API_FAILURE = "MEMORY_API_FAILURE"
    CHILD_PROTOCOL_FAILURE = "CHILD_PROTOCOL_FAILURE"
    ABNORMAL_EXIT = "ABNORMAL_EXIT"
    HARNESS_TIMEOUT = "HARNESS_TIMEOUT"
    OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"
    PROCESS_CLEANUP_FAILED = "PROCESS_CLEANUP_FAILED"


class DecodeStage(StrEnum):
    ADMITTED = "ADMITTED"
    PRE_DECODE_REJECTION = "PRE_DECODE_REJECTION"
    DECODE_ATTEMPTED_REJECTION = "DECODE_ATTEMPTED_REJECTION"


@dataclass(frozen=True, slots=True)
class ProcessMemorySnapshot:
    working_set_bytes: int
    peak_working_set_bytes: int
    private_usage_bytes: int


@dataclass(frozen=True, slots=True)
class MemoryEvaluation:
    lower_bound_bytes: int | None
    upper_bound_bytes: int | None
    peak_saturated: bool | None
    status: TargetStatus
    failure: ChildFailure | None = None
    error_code: int | None = None


@dataclass(frozen=True, slots=True)
class EvaluationProfile:
    fixture_id: str
    generator: str
    expected_outcome: str
    expected_reason: str | None
    decode_stage: DecodeStage


@dataclass(frozen=True, slots=True)
class CohortBCandidate:
    """One entry of the local, git-ignored Cohort B candidate manifest (D3-R2 section 6)."""

    fixture_id: str
    filename: str
    declared_format: str
    declared_sha256: str


@dataclass(frozen=True, slots=True)
class CohortBValidatedSource:
    """Facts re-derived from the actual local file, never trusted from the manifest alone."""

    fixture_id: str
    filename: str
    format: str
    mime: str
    sha256: str
    byte_count: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class ChildRequest:
    sample_id: str
    fixture_id: str
    cohort: str
    repeat_index: int
    source_path: str
    expected_sha256: str
    expected_source_bytes: int
    commit_identity: str


@dataclass(frozen=True, slots=True)
class ProcessExecution:
    exit_code: int | None
    stdout: bytes
    stderr: bytes
    parent_wall_ms: float
    failure: ChildFailure | None


class MemoryReadError(RuntimeError):
    def __init__(self, error_code: int) -> None:
        super().__init__(f"Windows process-memory query failed ({error_code})")
        self.error_code = max(0, int(error_code))


class MemoryReader(Protocol):
    def read(self) -> ProcessMemorySnapshot: ...


class _PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


class WindowsProcessMemoryReader:
    """Native current/lifetime-peak/commit metrics for the current process."""

    def __init__(
        self,
        query: Callable[[_PROCESS_MEMORY_COUNTERS_EX], tuple[bool, int]] | None = None,
    ) -> None:
        self._query = query or self._load_query()

    @staticmethod
    def _load_query() -> Callable[[_PROCESS_MEMORY_COUNTERS_EX], tuple[bool, int]]:
        if os.name != "nt":
            raise OSError("Windows process-memory API is unavailable")
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_current_process = kernel32.GetCurrentProcess
        get_current_process.argtypes = []
        get_current_process.restype = wintypes.HANDLE
        handle = get_current_process()
        try:
            query_fn = kernel32.K32GetProcessMemoryInfo
        except AttributeError:
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            query_fn = psapi.GetProcessMemoryInfo
        query_fn.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(_PROCESS_MEMORY_COUNTERS_EX),
            wintypes.DWORD,
        ]
        query_fn.restype = wintypes.BOOL

        def query(counters: _PROCESS_MEMORY_COUNTERS_EX) -> tuple[bool, int]:
            ctypes.set_last_error(0)
            ok = bool(query_fn(handle, ctypes.byref(counters), counters.cb))
            return ok, int(ctypes.get_last_error())

        return query

    def read(self) -> ProcessMemorySnapshot:
        counters = _PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS_EX)
        ok, error_code = self._query(counters)
        if not ok:
            raise MemoryReadError(error_code)
        snapshot = ProcessMemorySnapshot(
            working_set_bytes=int(counters.WorkingSetSize),
            peak_working_set_bytes=int(counters.PeakWorkingSetSize),
            private_usage_bytes=int(counters.PrivateUsage),
        )
        if min(
            snapshot.working_set_bytes,
            snapshot.peak_working_set_bytes,
            snapshot.private_usage_bytes,
        ) <= 0:
            raise MemoryReadError(0)
        return snapshot


def classify_memory(
    before: ProcessMemorySnapshot | None,
    after: ProcessMemorySnapshot | None,
    *,
    target_bytes: int = MEMORY_TARGET_BYTES,
    failure: ChildFailure | None = None,
    error_code: int | None = None,
) -> MemoryEvaluation:
    if target_bytes < 0:
        raise ValueError("memory target must be non-negative")
    if before is None or after is None:
        status = TargetStatus.NOT_MEASURED if failure is None else TargetStatus.MEASUREMENT_INVALID
        return MemoryEvaluation(None, None, None, status, failure, error_code)
    if (
        min(
            before.working_set_bytes,
            before.peak_working_set_bytes,
            before.private_usage_bytes,
            after.working_set_bytes,
            after.peak_working_set_bytes,
            after.private_usage_bytes,
        )
        <= 0
        or before.peak_working_set_bytes < before.working_set_bytes
        or after.peak_working_set_bytes < after.working_set_bytes
        or after.peak_working_set_bytes < before.peak_working_set_bytes
    ):
        return MemoryEvaluation(
            None,
            None,
            None,
            TargetStatus.MEASUREMENT_INVALID,
            ChildFailure.MEMORY_API_FAILURE,
            error_code,
        )
    lower = max(0, after.working_set_bytes - before.working_set_bytes)
    upper = max(0, after.peak_working_set_bytes - before.working_set_bytes)
    if upper <= target_bytes:
        status = TargetStatus.WITHIN_TARGET
    elif lower > target_bytes:
        status = TargetStatus.EXCEEDS_TARGET
    else:
        status = TargetStatus.INCONCLUSIVE
    return MemoryEvaluation(
        lower, upper, after.peak_working_set_bytes == before.peak_working_set_bytes, status
    )


def classify_timing(elapsed_ms: float | None) -> TargetStatus:
    if elapsed_ms is None or not math.isfinite(elapsed_ms) or elapsed_ms < 0:
        return TargetStatus.MEASUREMENT_INVALID
    return (
        TargetStatus.WITHIN_TARGET
        if elapsed_ms <= TIMING_TARGET_MS
        else TargetStatus.EXCEEDS_TARGET
    )


def nearest_rank_percentile(values: Sequence[float], percentile: float) -> float:
    if not values or not 0 < percentile <= 1:
        raise ValueError("values must be non-empty and percentile must be in (0, 1]")
    ordered = sorted(values)
    return ordered[math.ceil(percentile * len(ordered)) - 1]


def summarize_cohort_a(values: Sequence[float]) -> Mapping[str, float | int]:
    if len(values) < 20:
        raise ValueError("Cohort A requires at least 20 valid homogeneous observations")
    return {
        "sample_count": len(values),
        "p50": float(statistics.median(values)),
        "p95": nearest_rank_percentile(values, 0.95),
        "maximum": max(values),
    }


def summarize_cohort_b(values: Sequence[float]) -> Mapping[str, float | int]:
    """Cohort B reporting rule (D3-U2): minimum/median/maximum only, never p95 from 3 repeats."""

    if not values:
        raise ValueError("Cohort B summary requires at least one valid observation")
    return {
        "sample_count": len(values),
        "minimum": min(values),
        "median": float(statistics.median(values)),
        "maximum": max(values),
    }


def has_order_effect(values: Sequence[float]) -> bool:
    if len(values) < 10:
        raise ValueError("order-effect detection requires at least 10 valid observations")
    first = statistics.median(values[:5])
    last = statistics.median(values[-5:])
    denominator = max(first, last)
    return denominator > 0 and abs(first - last) / denominator > 0.10


def aggregate_profile(samples: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    """Aggregate one homogeneous Cohort A profile without hiding typed failures."""

    if len(samples) < 20:
        raise ValueError("Cohort A requires at least 20 samples per profile")
    def finite_number(value: object) -> TypeGuard[int | float]:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )

    elapsed = [
        float(value)
        for sample in samples
        if finite_number(value := sample.get("admission_elapsed_ms"))
        and sample.get("timing_status") == classify_timing(float(value)).value
    ]
    timing_statuses = [sample.get("timing_status") for sample in samples]
    memory_statuses = [sample.get("memory_status") for sample in samples]
    lower_bounds = [
        float(value)
        for sample in samples
        if finite_number(value := sample.get("memory_lower_bound_bytes"))
    ]
    upper_bounds = [
        float(value)
        for sample in samples
        if finite_number(value := sample.get("memory_upper_bound_bytes"))
    ]
    parent_wall = [
        float(value)
        for sample in samples
        if finite_number(value := sample.get("parent_wall_ms"))
    ]
    process_failure_count = sum(
        1
        for sample in samples
        if sample.get("failure") is not None
        or sample.get("exit_code") != 0
    )
    memory_failure_count = sum(
        1 for sample in samples if sample.get("measurement_failure") is not None
    )
    if process_failure_count or len(elapsed) != len(samples):
        timing_status = TargetStatus.MEASUREMENT_INVALID
    elif TargetStatus.EXCEEDS_TARGET.value in timing_statuses:
        timing_status = TargetStatus.EXCEEDS_TARGET
    elif all(status == TargetStatus.WITHIN_TARGET.value for status in timing_statuses):
        timing_status = TargetStatus.WITHIN_TARGET
    else:
        timing_status = TargetStatus.MEASUREMENT_INVALID

    if (
        process_failure_count
        or memory_failure_count
        or TargetStatus.MEASUREMENT_INVALID.value in memory_statuses
    ):
        memory_status = TargetStatus.MEASUREMENT_INVALID
    elif TargetStatus.EXCEEDS_TARGET.value in memory_statuses:
        memory_status = TargetStatus.EXCEEDS_TARGET
    elif TargetStatus.INCONCLUSIVE.value in memory_statuses:
        memory_status = TargetStatus.INCONCLUSIVE
    elif TargetStatus.NOT_MEASURED.value in memory_statuses:
        memory_status = TargetStatus.NOT_MEASURED
    elif all(status == TargetStatus.WITHIN_TARGET.value for status in memory_statuses):
        memory_status = TargetStatus.WITHIN_TARGET
    else:
        memory_status = TargetStatus.MEASUREMENT_INVALID

    statistics_fields = (
        summarize_cohort_a(elapsed)
        if len(elapsed) >= 20
        else {"sample_count": len(elapsed)}
    )
    return {
        **statistics_fields,
        "first_sample_ms": elapsed[0] if elapsed else None,
        "later_sample_count": max(0, len(elapsed) - 1),
        "timing_status": timing_status.value,
        "memory_status": memory_status.value,
        "process_failure_count": process_failure_count,
        "memory_failure_count": memory_failure_count,
        "memory_inconclusive_count": memory_statuses.count(TargetStatus.INCONCLUSIVE.value),
        "memory_not_measured_count": memory_statuses.count(TargetStatus.NOT_MEASURED.value),
        "memory_invalid_count": memory_statuses.count(TargetStatus.MEASUREMENT_INVALID.value),
        "memory_lower_bound_max_bytes": max(lower_bounds) if lower_bounds else None,
        "memory_upper_bound_max_bytes": max(upper_bounds) if upper_bounds else None,
        "memory_upper_bound_p95_bytes": (
            nearest_rank_percentile(upper_bounds, 0.95)
            if len(upper_bounds) >= 20
            else None
        ),
        "parent_wall_p50_ms": statistics.median(parent_wall) if parent_wall else None,
        "parent_wall_max_ms": max(parent_wall) if parent_wall else None,
    }


def aggregate_cohort_b_group(
    samples: Sequence[Mapping[str, object]], *, required_count: int
) -> Mapping[str, object]:
    """Aggregate one Cohort B group: one image's 3 repeats, or the whole 24-sample cohort.

    Mirrors `aggregate_profile`'s never-trust-a-spoofed-field recomputation, but reports
    only minimum/median/maximum (D3-U2) and requires an exact sample count rather than
    Cohort A's ``>= 20`` floor.
    """

    if required_count <= 0:
        raise ValueError("required_count must be positive")
    if len(samples) != required_count:
        raise ValueError(f"Cohort B group requires exactly {required_count} samples")

    def finite_number(value: object) -> TypeGuard[int | float]:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )

    elapsed = [
        float(value)
        for sample in samples
        if finite_number(value := sample.get("admission_elapsed_ms"))
        and sample.get("timing_status") == classify_timing(float(value)).value
    ]
    timing_statuses = [sample.get("timing_status") for sample in samples]
    memory_statuses = [sample.get("memory_status") for sample in samples]
    lower_bounds = [
        float(value)
        for sample in samples
        if finite_number(value := sample.get("memory_lower_bound_bytes"))
    ]
    upper_bounds = [
        float(value)
        for sample in samples
        if finite_number(value := sample.get("memory_upper_bound_bytes"))
    ]
    parent_wall = [
        float(value)
        for sample in samples
        if finite_number(value := sample.get("parent_wall_ms"))
    ]
    process_failure_count = sum(
        1
        for sample in samples
        if sample.get("failure") is not None or sample.get("exit_code") != 0
    )
    memory_failure_count = sum(
        1 for sample in samples if sample.get("measurement_failure") is not None
    )
    if process_failure_count or len(elapsed) != len(samples):
        timing_status = TargetStatus.MEASUREMENT_INVALID
    elif TargetStatus.EXCEEDS_TARGET.value in timing_statuses:
        timing_status = TargetStatus.EXCEEDS_TARGET
    elif all(status == TargetStatus.WITHIN_TARGET.value for status in timing_statuses):
        timing_status = TargetStatus.WITHIN_TARGET
    else:
        timing_status = TargetStatus.MEASUREMENT_INVALID

    if (
        process_failure_count
        or memory_failure_count
        or TargetStatus.MEASUREMENT_INVALID.value in memory_statuses
    ):
        memory_status = TargetStatus.MEASUREMENT_INVALID
    elif TargetStatus.EXCEEDS_TARGET.value in memory_statuses:
        memory_status = TargetStatus.EXCEEDS_TARGET
    elif TargetStatus.INCONCLUSIVE.value in memory_statuses:
        memory_status = TargetStatus.INCONCLUSIVE
    elif TargetStatus.NOT_MEASURED.value in memory_statuses:
        memory_status = TargetStatus.NOT_MEASURED
    elif all(status == TargetStatus.WITHIN_TARGET.value for status in memory_statuses):
        memory_status = TargetStatus.WITHIN_TARGET
    else:
        memory_status = TargetStatus.MEASUREMENT_INVALID

    statistics_fields = summarize_cohort_b(elapsed) if elapsed else {"sample_count": 0}
    return {
        **statistics_fields,
        "timing_status": timing_status.value,
        "memory_status": memory_status.value,
        "process_failure_count": process_failure_count,
        "memory_failure_count": memory_failure_count,
        "memory_inconclusive_count": memory_statuses.count(TargetStatus.INCONCLUSIVE.value),
        "memory_not_measured_count": memory_statuses.count(TargetStatus.NOT_MEASURED.value),
        "memory_invalid_count": memory_statuses.count(TargetStatus.MEASUREMENT_INVALID.value),
        "memory_lower_bound_max_bytes": max(lower_bounds) if lower_bounds else None,
        "memory_upper_bound_max_bytes": max(upper_bounds) if upper_bounds else None,
        "parent_wall_median_ms": statistics.median(parent_wall) if parent_wall else None,
        "parent_wall_max_ms": max(parent_wall) if parent_wall else None,
    }


def calibrate_memory_reader(
    reader: MemoryReader,
    *,
    allocation_bytes: int = 16 * 1024 * 1024,
    tolerance: float = 0.50,
) -> Mapping[str, object]:
    """Page-touch a known allocation to validate wiring, not decoder accounting."""

    if allocation_bytes <= 0 or not 0 <= tolerance < 1:
        raise ValueError("invalid calibration parameters")
    before = reader.read()
    allocation = bytearray(allocation_bytes)
    for offset in range(0, allocation_bytes, 4096):
        allocation[offset] = 1
    after = reader.read()
    observed = max(0, after.working_set_bytes - before.working_set_bytes)
    minimum = math.floor(allocation_bytes * (1 - tolerance))
    calibrated = (
        observed >= minimum
        and after.peak_working_set_bytes >= before.peak_working_set_bytes
    )
    # Keep the page-touched buffer alive until both native readings have completed.
    assert allocation[0] == 1
    return {
        "allocation_bytes": allocation_bytes,
        "observed_working_set_growth_bytes": observed,
        "tolerance": tolerance,
        "minimum_expected_growth_bytes": minimum,
        "calibrated": calibrated,
        "scope": "adapter-wiring-only",
    }


def _require_opaque_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise ValueError(f"{label} must be a non-empty bounded string")
    if any(char not in _OPAQUE_ID_CHARS for char in value):
        raise ValueError(f"{label} contains a forbidden character")
    return value


def _parse_child_request(payload: bytes) -> ChildRequest:
    if len(payload) > MAX_PROTOCOL_BYTES:
        raise ValueError("request exceeds protocol limit")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("request must be an object")
    required = {
        "protocol_name",
        "protocol_version",
        "sample_id",
        "fixture_id",
        "cohort",
        "repeat_index",
        "source_path",
        "expected_sha256",
        "expected_source_bytes",
        "commit_identity",
    }
    if set(parsed) != required:
        raise ValueError("request fields do not match the protocol")
    if parsed["protocol_name"] != PROTOCOL_NAME or parsed["protocol_version"] != PROTOCOL_VERSION:
        raise ValueError("unsupported protocol identity")
    repeat_index = parsed["repeat_index"]
    if not isinstance(repeat_index, int) or isinstance(repeat_index, bool) or repeat_index < 0:
        raise ValueError("repeat_index must be a non-negative integer")
    source_path = parsed["source_path"]
    digest = parsed["expected_sha256"]
    expected_source_bytes = parsed["expected_source_bytes"]
    commit = parsed["commit_identity"]
    if not isinstance(source_path, str) or not source_path or len(source_path) > 4096:
        raise ValueError("source_path must be a bounded string")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(c not in "0123456789abcdef" for c in digest)
    ):
        raise ValueError("expected_sha256 must be lowercase SHA-256")
    if (
        not isinstance(expected_source_bytes, int)
        or isinstance(expected_source_bytes, bool)
        or expected_source_bytes < 0
    ):
        raise ValueError("expected_source_bytes must be a non-negative integer")
    commit = _require_opaque_id(commit, "commit_identity")
    return ChildRequest(
        sample_id=_require_opaque_id(parsed["sample_id"], "sample_id"),
        fixture_id=_require_opaque_id(parsed["fixture_id"], "fixture_id"),
        cohort=_require_opaque_id(parsed["cohort"], "cohort"),
        repeat_index=repeat_index,
        source_path=source_path,
        expected_sha256=digest,
        expected_source_bytes=expected_source_bytes,
        commit_identity=commit,
    )


def _environment_identity(commit_identity: str) -> Mapping[str, object]:
    import av

    versions = {
        str(name): ".".join(str(part) for part in version)
        for name, version in sorted(av.library_versions.items())
    }
    return {
        "python": platform.python_version(),
        "pyav": av.__version__,
        "ffmpeg_libraries": versions,
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "commit_identity": commit_identity,
    }


def _child_result(request: ChildRequest, reader: MemoryReader | None = None) -> dict[str, object]:
    from sketch2life.infrastructure.media_validation.av_image_decoder import AvImageDecoder

    memory_reader = reader
    memory_failure: ChildFailure | None = None
    memory_error_code: int | None = None
    if memory_reader is None:
        try:
            memory_reader = WindowsProcessMemoryReader()
        except OSError:
            memory_reader = None

    service = Feat018ImageAdmission(AvImageDecoder())
    source_bytes = Path(request.source_path).stat().st_size
    if source_bytes != request.expected_source_bytes:
        raise ValueError("source byte count changed before admission")
    before: ProcessMemorySnapshot | None = None
    after: ProcessMemorySnapshot | None = None
    if memory_reader is not None:
        try:
            before = memory_reader.read()
        except MemoryReadError as exc:
            memory_failure, memory_error_code = ChildFailure.MEMORY_API_FAILURE, exc.error_code
    started = time.perf_counter_ns()
    result = service.admit(
        Feat018AdmissionRequest(path=Path(request.source_path), artifact_ref=request.sample_id)
    )
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    if memory_reader is not None and before is not None:
        try:
            after = memory_reader.read()
        except MemoryReadError as exc:
            memory_failure, memory_error_code = ChildFailure.MEMORY_API_FAILURE, exc.error_code
    memory = classify_memory(
        before,
        after,
        failure=memory_failure,
        error_code=memory_error_code,
    )
    decision = result.decision
    metadata = asdict(decision.metadata) if decision.metadata is not None else None
    actual_digest = decision.digest
    digest_verified = (
        actual_digest == request.expected_sha256 if actual_digest is not None else None
    )
    limits = Feat018AdmissionLimits()
    return {
        "protocol_name": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "sample_id": request.sample_id,
        "fixture_id": request.fixture_id,
        "cohort": request.cohort,
        "repeat_index": request.repeat_index,
        "source_sha256": actual_digest,
        "source_digest_verified": digest_verified,
        "source_bytes": source_bytes,
        "outcome": decision.outcome.value,
        "reason": decision.reason.value if decision.reason is not None else None,
        "metadata": metadata,
        "artifact_ref_verified": result.source is None
        or result.source.artifact_ref == request.sample_id,
        "limits": {
            "max_file_bytes": limits.max_file_bytes,
            "max_pixels": limits.max_pixels,
            "max_longest_edge": limits.max_longest_edge,
            "max_frames": limits.max_frames,
            "allowed_containers": sorted(limits.allowed_containers),
            "allowed_codecs": sorted(limits.allowed_codecs),
            "allowed_pixel_formats": sorted(limits.allowed_pixel_formats),
        },
        "admission_elapsed_ms": elapsed_ms,
        "timing_status": classify_timing(elapsed_ms).value,
        "working_set_before_bytes": before.working_set_bytes if before else None,
        "working_set_after_bytes": after.working_set_bytes if after else None,
        "peak_before_bytes": before.peak_working_set_bytes if before else None,
        "peak_after_bytes": after.peak_working_set_bytes if after else None,
        "private_usage_before_bytes": before.private_usage_bytes if before else None,
        "private_usage_after_bytes": after.private_usage_bytes if after else None,
        "memory_lower_bound_bytes": memory.lower_bound_bytes,
        "memory_upper_bound_bytes": memory.upper_bound_bytes,
        "peak_saturated": memory.peak_saturated,
        "memory_status": memory.status.value,
        "measurement_failure": memory.failure.value if memory.failure else None,
        "measurement_error_code": memory.error_code,
        "environment": _environment_identity(request.commit_identity),
    }


def _bounded_error(failure: ChildFailure, detail: str) -> dict[str, object]:
    return {
        "protocol_name": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "failure": failure.value,
        "detail": detail[:160],
    }


def _encode_json(document: Mapping[str, object]) -> bytes:
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_PROTOCOL_BYTES:
        raise ValueError("serialized result exceeds protocol limit")
    return encoded


def validate_child_output(
    document: Mapping[str, object], request: ChildRequest
) -> None:
    """Fail closed on malformed, mismatched, or path-bearing child output."""

    required = {
        "protocol_name",
        "protocol_version",
        "sample_id",
        "fixture_id",
        "cohort",
        "repeat_index",
        "source_sha256",
        "source_digest_verified",
        "source_bytes",
        "outcome",
        "reason",
        "metadata",
        "artifact_ref_verified",
        "limits",
        "admission_elapsed_ms",
        "timing_status",
        "working_set_before_bytes",
        "working_set_after_bytes",
        "peak_before_bytes",
        "peak_after_bytes",
        "private_usage_before_bytes",
        "private_usage_after_bytes",
        "memory_lower_bound_bytes",
        "memory_upper_bound_bytes",
        "peak_saturated",
        "memory_status",
        "measurement_failure",
        "measurement_error_code",
        "environment",
    }
    if set(document) != required:
        raise ValueError("child output fields do not match the protocol")
    identities = (
        document.get("protocol_name") == PROTOCOL_NAME,
        document.get("protocol_version") == PROTOCOL_VERSION,
        document.get("sample_id") == request.sample_id,
        document.get("fixture_id") == request.fixture_id,
        document.get("cohort") == request.cohort,
        document.get("repeat_index") == request.repeat_index,
    )
    if not all(identities):
        raise ValueError("child output identity mismatch")

    def string_values(value: object) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, Mapping):
            return [item for child in value.values() for item in string_values(child)]
        if isinstance(value, (list, tuple)):
            return [item for child in value for item in string_values(child)]
        return []

    source_spellings = {
        request.source_path.casefold(),
        request.source_path.replace("\\", "/").casefold(),
    }
    output_strings = string_values(document)
    if "source_path" in document or any(
        spelling and spelling in value.replace("\\", "/").casefold()
        for spelling in source_spellings
        for value in output_strings
    ):
        raise ValueError("child output contains source path")
    if document.get("artifact_ref_verified") is not True:
        raise ValueError("child used a non-opaque artifact reference")

    outcome = document.get("outcome")
    if not isinstance(outcome, str):
        raise ValueError("child outcome is not a string")
    typed_outcome = AdmissionOutcome(outcome)
    reason_raw = document.get("reason")
    typed_reason: AdmissionReason | None = None
    if reason_raw is not None:
        if not isinstance(reason_raw, str):
            raise ValueError("child reason is not a string")
        typed_reason = AdmissionReason(reason_raw)
    if (typed_outcome is AdmissionOutcome.ADMITTED) != (typed_reason is None):
        raise ValueError("child outcome/reason mismatch")
    if typed_reason is not None and outcome_for_reason(typed_reason) is not typed_outcome:
        raise ValueError("child reason belongs to another outcome")

    source_bytes = document.get("source_bytes")
    if (
        not isinstance(source_bytes, int)
        or isinstance(source_bytes, bool)
        or source_bytes != request.expected_source_bytes
    ):
        raise ValueError("child source byte count mismatch")
    source_sha256 = document.get("source_sha256")
    digest_verified = document.get("source_digest_verified")
    source_bytes_value = source_bytes
    if source_sha256 is None:
        if digest_verified is not None or not (
            typed_outcome is AdmissionOutcome.REJECTED
            and typed_reason is AdmissionReason.FILE_BYTES_EXCEEDED
            and source_bytes_value > Feat018AdmissionLimits().max_file_bytes
        ):
            raise ValueError("missing digest is only valid for byte-budget rejection")
    elif (
        not isinstance(source_sha256, str)
        or source_sha256 != request.expected_sha256
        or digest_verified is not True
    ):
        raise ValueError("child source digest mismatch")

    elapsed = document.get("admission_elapsed_ms")
    if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool):
        raise ValueError("child admission time is not numeric")
    timing_status = document.get("timing_status")
    if timing_status != classify_timing(float(elapsed)).value:
        raise ValueError("child timing classification mismatch")

    def memory_snapshot(suffix: str) -> ProcessMemorySnapshot | None:
        values = [
            document.get(f"working_set_{suffix}_bytes"),
            document.get(f"peak_{suffix}_bytes"),
            document.get(f"private_usage_{suffix}_bytes"),
        ]
        if all(value is None for value in values):
            return None
        if not all(
            isinstance(value, int) and not isinstance(value, bool) for value in values
        ):
            raise ValueError(f"child {suffix} memory snapshot is partial or non-integer")
        return ProcessMemorySnapshot(
            cast(int, values[0]), cast(int, values[1]), cast(int, values[2])
        )

    before = memory_snapshot("before")
    after = memory_snapshot("after")
    failure_raw = document.get("measurement_failure")
    if failure_raw is not None and failure_raw != ChildFailure.MEMORY_API_FAILURE.value:
        raise ValueError("child memory failure is invalid")
    error_code = document.get("measurement_error_code")
    if error_code is not None and (
        not isinstance(error_code, int) or isinstance(error_code, bool) or error_code < 0
    ):
        raise ValueError("child memory error code is invalid")
    memory = classify_memory(
        before,
        after,
        failure=ChildFailure.MEMORY_API_FAILURE if failure_raw is not None else None,
        error_code=error_code,
    )
    expected_memory = {
        "memory_lower_bound_bytes": memory.lower_bound_bytes,
        "memory_upper_bound_bytes": memory.upper_bound_bytes,
        "peak_saturated": memory.peak_saturated,
        "memory_status": memory.status.value,
        "measurement_failure": memory.failure.value if memory.failure else None,
        "measurement_error_code": memory.error_code,
    }
    if any(document.get(name) != value for name, value in expected_memory.items()):
        raise ValueError("child memory classification mismatch")

    environment = document.get("environment")
    if not isinstance(environment, Mapping) or set(environment) != {
        "python",
        "pyav",
        "ffmpeg_libraries",
        "os",
        "os_release",
        "architecture",
        "commit_identity",
    } or environment.get("commit_identity") != request.commit_identity:
        raise ValueError("child environment identity mismatch")


def child_main() -> int:
    try:
        payload = sys.stdin.buffer.read(MAX_PROTOCOL_BYTES + 1)
        if len(payload) > MAX_PROTOCOL_BYTES:
            output = _bounded_error(ChildFailure.INVALID_REQUEST, "request exceeds protocol limit")
            sys.stdout.buffer.write(_encode_json(output))
            return 2
        request = _parse_child_request(payload)
        sys.stdout.buffer.write(_encode_json(_child_result(request)))
        return 0
    except Exception:  # noqa: BLE001 - protocol boundary must never emit a traceback
        with contextlib.suppress(Exception):
            sys.stdout.buffer.write(
                _encode_json(_bounded_error(ChildFailure.CHILD_PROTOCOL_FAILURE, "child failed"))
            )
        return 2


def _typed_child_error(payload: bytes) -> dict[str, object] | None:
    try:
        parsed = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(parsed, dict) or set(parsed) != {
        "protocol_name",
        "protocol_version",
        "failure",
        "detail",
    }:
        return None
    if parsed.get("protocol_name") != PROTOCOL_NAME or parsed.get("protocol_version") != (
        PROTOCOL_VERSION
    ):
        return None
    failure_raw = parsed.get("failure")
    if not isinstance(failure_raw, str):
        return None
    try:
        failure = ChildFailure(failure_raw)
    except (TypeError, ValueError):
        return None
    if failure not in {ChildFailure.INVALID_REQUEST, ChildFailure.CHILD_PROTOCOL_FAILURE}:
        return None
    detail = parsed.get("detail")
    if not isinstance(detail, str) or len(detail) > 160 or "Traceback" in detail:
        return None
    return cast(dict[str, object], parsed)


def _read_stream_bounded(
    stream: BinaryIO, cap: int, output: bytearray, overflow: threading.Event
) -> None:
    while True:
        chunk = stream.read(min(4096, cap + 1 - len(output)))
        if not chunk:
            return
        output.extend(chunk)
        if len(output) > cap:
            overflow.set()
            return


def _stop_process(process: subprocess.Popen[bytes]) -> bool:
    if process.poll() is not None:
        return True
    try:
        process.terminate()
        process.wait(timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        with contextlib.suppress(OSError):
            process.kill()
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            process.wait(timeout=2)
    return process.poll() is not None


def run_bounded_process(
    args: Sequence[str], request: bytes, *, timeout_seconds: float
) -> ProcessExecution:
    if (
        not args
        or len(request) > MAX_PROTOCOL_BYTES
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        return ProcessExecution(None, b"", b"", 0.0, ChildFailure.INVALID_REQUEST)
    started = time.perf_counter_ns()
    try:
        process = subprocess.Popen(
            list(args), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except OSError:
        return ProcessExecution(
            None,
            b"",
            b"",
            (time.perf_counter_ns() - started) / 1_000_000,
            ChildFailure.ABNORMAL_EXIT,
        )
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None
    stdout, stderr = bytearray(), bytearray()
    overflow = threading.Event()
    readers = [
        threading.Thread(
            target=_read_stream_bounded,
            args=(process.stdout, MAX_PROTOCOL_BYTES, stdout, overflow),
            daemon=True,
        ),
        threading.Thread(
            target=_read_stream_bounded,
            args=(process.stderr, MAX_PROTOCOL_BYTES, stderr, overflow),
            daemon=True,
        ),
    ]
    for reader in readers:
        reader.start()
    writer_error: list[BaseException] = []
    writer_done = threading.Event()
    stdin = process.stdin
    assert stdin is not None

    def write_request() -> None:
        try:
            stdin.write(request)
            stdin.close()
        except (OSError, ValueError) as exc:
            writer_error.append(exc)
        finally:
            writer_done.set()

    writer = threading.Thread(target=write_request, daemon=True)
    writer.start()
    try:
        deadline = time.monotonic() + timeout_seconds
        failure: ChildFailure | None = None
        while process.poll() is None:
            if writer_error:
                failure = ChildFailure.ABNORMAL_EXIT
                if not _stop_process(process):
                    failure = ChildFailure.PROCESS_CLEANUP_FAILED
                break
            if overflow.is_set():
                failure = ChildFailure.OUTPUT_LIMIT_EXCEEDED
                if not _stop_process(process):
                    failure = ChildFailure.PROCESS_CLEANUP_FAILED
                break
            if time.monotonic() >= deadline:
                failure = ChildFailure.HARNESS_TIMEOUT
                if not _stop_process(process):
                    failure = ChildFailure.PROCESS_CLEANUP_FAILED
                break
            time.sleep(0.005)
        writer.join(timeout=2)
        for reader in readers:
            reader.join(timeout=2)
        if not writer_done.is_set() or any(reader.is_alive() for reader in readers):
            failure = ChildFailure.PROCESS_CLEANUP_FAILED
        if overflow.is_set() and failure is not ChildFailure.PROCESS_CLEANUP_FAILED:
            failure = ChildFailure.OUTPUT_LIMIT_EXCEEDED
        exit_code = process.poll()
        if failure is None and exit_code != 0:
            failure = ChildFailure.ABNORMAL_EXIT
        return ProcessExecution(
            exit_code,
            bytes(stdout[:MAX_PROTOCOL_BYTES]),
            bytes(stderr[:MAX_PROTOCOL_BYTES]),
            (time.perf_counter_ns() - started) / 1_000_000,
            failure,
        )
    finally:
        _stop_process(process)


def run_child_sample(
    request: ChildRequest, *, timeout_seconds: float = DEFAULT_CHILD_TIMEOUT_SECONDS
) -> dict[str, object]:
    document = {
        "protocol_name": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        **asdict(request),
    }
    execution = run_bounded_process(
        [sys.executable, "-m", "sketch2life.benchmark.image_admission_evaluation", "--child"],
        _encode_json(document),
        timeout_seconds=timeout_seconds,
    )
    if execution.failure is not None:
        child_error = (
            _typed_child_error(execution.stdout)
            if execution.failure is ChildFailure.ABNORMAL_EXIT
            else None
        )
        return {
            **(
                child_error
                or _bounded_error(
                    execution.failure, "fresh child did not return a valid sample"
                )
            ),
            "parent_wall_ms": execution.parent_wall_ms,
            "exit_code": execution.exit_code,
        }
    try:
        parsed = json.loads(execution.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        parsed = _bounded_error(ChildFailure.CHILD_PROTOCOL_FAILURE, "malformed child output")
    if not isinstance(parsed, dict):
        parsed = _bounded_error(ChildFailure.CHILD_PROTOCOL_FAILURE, "non-object child output")
    else:
        try:
            validate_child_output(parsed, request)
        except (TypeError, ValueError):
            parsed = _bounded_error(
                ChildFailure.CHILD_PROTOCOL_FAILURE, "invalid child output schema"
            )
    parsed["parent_wall_ms"] = execution.parent_wall_ms
    parsed["exit_code"] = execution.exit_code
    return cast(dict[str, object], parsed)


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return pack(">I", len(data)) + kind + data + pack(">I", crc32(kind + data) & 0xFFFFFFFF)


def _png(
    width: int,
    height: int,
    *,
    bit_depth: int = 8,
    color_type: int = 2,
    raw: bytes | None = None,
    palette: bytes | None = None,
    pad_to_bytes: int | None = None,
) -> bytes:
    channels = {0: 1, 2: 3, 3: 1, 6: 4}[color_type]
    if raw is None:
        stride = (width * bit_depth * channels + 7) // 8
        fill = 0xFF if bit_depth == 1 else 0x00 if color_type == 3 else 0x40
        row = bytes([fill]) * stride
        raw = b"".join(b"\x00" + row for _ in range(height))
    header = pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0)
    extra = _png_chunk(b"PLTE", palette) if palette is not None else b""
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + extra
        + _png_chunk(b"IDAT", compress(raw))
        + _png_chunk(b"IEND", b"")
    )
    if pad_to_bytes is not None:
        overhead = 20
        padding = pad_to_bytes - len(payload) - overhead
        if padding < 0:
            raise ValueError("target size is smaller than PNG")
        chunk = _png_chunk(b"tEXt", b"Comment\x00" + b"a" * padding)
        iend = payload.index(b"IEND") - 4
        payload = payload[:iend] + chunk + payload[iend:]
    return payload


def _jpeg(width: int = 64, height: int = 64, frames: int = 1) -> bytes:
    import av

    buffer = io.BytesIO()
    with av.open(buffer, mode="w", format="mjpeg") as container:
        stream = container.add_stream("mjpeg", rate=1)
        stream.width, stream.height, stream.pix_fmt = width, height, "yuvj420p"
        raw = bytes([128, 128, 128, 255]) * (width * height)
        for _ in range(frames):
            frame = av.VideoFrame.from_bytes(raw, width, height, format="rgba")
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return buffer.getvalue()


def _garbage_png() -> bytes:
    good = _png(64, 64)
    start = good.index(b"IDAT") - 4
    return good[:start] + _png_chunk(b"IDAT", b"\x99" * 200) + _png_chunk(b"IEND", b"")


def _rgb16_png() -> bytes:
    raw = b"".join(b"\x00" + b"\x00\x40" * (32 * 3) for _ in range(32))
    return _png(32, 32, bit_depth=16, raw=raw)


GENERATORS: Mapping[str, Callable[[], bytes]] = {
    "rgb8-png": lambda: _png(64, 64),
    "rgba8-png": lambda: _png(64, 64, color_type=6),
    "gray8-png": lambda: _png(64, 64, color_type=0),
    "palette8-png": lambda: _png(
        64, 64, color_type=3, palette=bytes([255, 255, 255, 0, 0, 0])
    ),
    "mono1-png": lambda: _png(64, 64, bit_depth=1, color_type=0),
    "baseline-jpeg": _jpeg,
    "near-byte-limit-png": lambda: _png(64, 64, pad_to_bytes=5_000_000),
    "pixel-limit-png": lambda: _png(2000, 2000),
    "edge-limit-png": lambda: _png(4096, 900),
    "over-byte-limit": lambda: b"x" * 5_000_001,
    "over-pixel-limit": lambda: _png(2000, 2001),
    "over-edge-limit": lambda: _png(4200, 900),
    "truncated-png": lambda: _png(64, 64)[: len(_png(64, 64)) // 2],
    "garbage-idat-png": _garbage_png,
    "unsupported-rgb16": _rgb16_png,
    "multi-frame-jpeg": lambda: _jpeg(frames=2),
}


def load_evaluation_manifest(path: Path) -> tuple[EvaluationProfile, ...]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or set(document) != {
            "contract_name",
            "contract_version",
            "data_policy",
            "profiles",
        }
        or document.get("contract_name")
        != "Feat018ImageAdmissionEvaluationManifestV1"
        or document.get("contract_version") != "1.0"
        or document.get("data_policy") != "synthetic-only"
    ):
        raise ValueError("unexpected evaluation manifest")
    profiles = document.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("manifest profiles must be a non-empty list")
    parsed: list[EvaluationProfile] = []
    seen: set[str] = set()
    for item in profiles:
        if not isinstance(item, dict) or set(item) != {
            "fixture_id",
            "generator",
            "expected_outcome",
            "expected_reason",
            "decode_stage",
            "synthetic_data",
        }:
            raise ValueError("invalid manifest profile fields")
        fixture_id = _require_opaque_id(item["fixture_id"], "fixture_id")
        generator = item["generator"]
        if fixture_id in seen or not isinstance(generator, str) or generator not in GENERATORS:
            raise ValueError("duplicate fixture or unknown generator")
        if item["synthetic_data"] is not True:
            raise ValueError("Cohort A must be synthetic")
        outcome_raw, reason_raw = item["expected_outcome"], item["expected_reason"]
        try:
            outcome = AdmissionOutcome(outcome_raw)
            reason = AdmissionReason(reason_raw) if reason_raw is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid expected outcome/reason") from exc
        if (outcome is AdmissionOutcome.ADMITTED) != (reason is None):
            raise ValueError("expected outcome/reason are inconsistent")
        if reason is not None and outcome_for_reason(reason) is not outcome:
            raise ValueError("expected reason belongs to another outcome")
        parsed.append(
            EvaluationProfile(
                fixture_id,
                generator,
                outcome.value,
                reason.value if reason is not None else None,
                DecodeStage(item["decode_stage"]),
            )
        )
        seen.add(fixture_id)
    generator_names = [profile.generator for profile in parsed]
    if len(generator_names) != len(set(generator_names)) or set(generator_names) != set(
        GENERATORS
    ):
        raise ValueError("manifest must reference every approved generator exactly once")
    return tuple(parsed)


def materialize_cohort_a(
    profiles: Sequence[EvaluationProfile], directory: Path
) -> Mapping[str, tuple[Path, str]]:
    directory.mkdir(parents=True, exist_ok=False)
    result: dict[str, tuple[Path, str]] = {}
    for profile in profiles:
        payload = GENERATORS[profile.generator]()
        digest = hashlib.sha256(payload).hexdigest()
        path = directory / f"{profile.fixture_id}.bin"
        path.write_bytes(payload)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError("fixture hash changed after write")
        result[profile.fixture_id] = (path, digest)
    return result


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_frozen_source(path: Path, expected_sha256: str, expected_bytes: int) -> None:
    if path.stat().st_size != expected_bytes or _sha256_of(path) != expected_sha256:
        raise RuntimeError("fixture changed after Cohort A materialization")


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_JPEG_SIGNATURE = b"\xff\xd8\xff"
_COHORT_B_MIME_BY_FORMAT: Mapping[str, str] = {"JPEG": "image/jpeg", "PNG": "image/png"}
_COHORT_B_EXTENSIONS_BY_FORMAT: Mapping[str, tuple[str, ...]] = {
    "JPEG": (".jpg", ".jpeg"),
    "PNG": (".png",),
}
_COHORT_B_EXPECTED_FIXTURE_IDS: tuple[str, ...] = tuple(f"B0{index}" for index in range(1, 9))


def _sniff_image_format(prefix: bytes) -> str | None:
    if prefix.startswith(_PNG_SIGNATURE):
        return "PNG"
    if prefix.startswith(_JPEG_SIGNATURE):
        return "JPEG"
    return None


def load_cohort_b_manifest(path: Path) -> tuple[CohortBCandidate, ...]:
    """Load and structurally validate the local, git-ignored Cohort B candidate manifest.

    This manifest and the raw images beside it never enter Git (D3-R2 section 6); only the
    derived, redacted facts computed by `validate_cohort_b_source` may reach tracked evidence.
    """

    document = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or set(document)
        != {
            "feature",
            "cohort",
            "owner_reviewed",
            "owner_review_date",
            "execution_authorized",
            "files",
        }
        or document.get("feature") != "FEAT-018"
        or document.get("cohort") != "B"
        or document.get("owner_reviewed") is not True
        or document.get("execution_authorized") is not True
        or not isinstance(document.get("owner_review_date"), str)
        or not document.get("owner_review_date")
    ):
        raise ValueError("Cohort B manifest is missing required owner-approval fields")
    files = document.get("files")
    if not isinstance(files, list) or len(files) != 8:
        raise ValueError("Cohort B manifest must declare exactly 8 files")
    candidates: list[CohortBCandidate] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    seen_hashes: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or set(item) != {"id", "path", "format", "sha256"}:
            raise ValueError("Cohort B manifest entry has unexpected fields")
        fixture_id, filename = item["id"], item["path"]
        declared_format, digest = item["format"], item["sha256"]
        if fixture_id not in _COHORT_B_EXPECTED_FIXTURE_IDS or fixture_id in seen_ids:
            raise ValueError("Cohort B manifest entry has a duplicate or unapproved id")
        if (
            not isinstance(filename, str)
            or not filename
            or "/" in filename
            or "\\" in filename
            or filename in seen_paths
        ):
            raise ValueError("Cohort B manifest entry has an invalid or duplicate filename")
        if declared_format not in _COHORT_B_MIME_BY_FORMAT:
            raise ValueError("Cohort B manifest entry has an unsupported declared format")
        if not isinstance(digest, str):
            raise ValueError("Cohort B manifest entry has an invalid SHA-256 digest value")
        if len(digest) != 64:
            raise ValueError(
                "Cohort B manifest entry has an invalid SHA-256 digest length "
                f"(expected 64 hexadecimal characters, got {len(digest)})"
            )
        if any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(
                "Cohort B manifest entry has an invalid SHA-256 digest value "
                "(expected lowercase hexadecimal)"
            )
        if digest in seen_hashes:
            raise ValueError("Cohort B manifest entry has a duplicate SHA-256 digest")
        seen_ids.add(fixture_id)
        seen_paths.add(filename)
        seen_hashes.add(digest)
        candidates.append(CohortBCandidate(fixture_id, filename, declared_format, digest))
    if seen_ids != set(_COHORT_B_EXPECTED_FIXTURE_IDS):
        raise ValueError("Cohort B manifest must cover exactly the approved B01-B08 identities")
    if (
        sum(candidate.declared_format == "JPEG" for candidate in candidates) != 4
        or sum(candidate.declared_format == "PNG" for candidate in candidates) != 4
    ):
        raise ValueError("Cohort B manifest must declare exactly 4 JPEG and 4 PNG files")
    return tuple(sorted(candidates, key=lambda candidate: candidate.fixture_id))


def _probe_declared_dimensions(path: Path) -> tuple[int, int]:
    """Header-only dimension probe, mirroring D1 section 3 step 5: no full decode, no policy."""

    import av

    with av.open(str(path)) as container:
        streams = container.streams.video
        if not streams:
            raise ValueError("source has no video stream")
        width, height = int(streams[0].width), int(streams[0].height)
    if width < 1 or height < 1:
        raise ValueError("source declares invalid dimensions")
    return width, height


def validate_cohort_b_source(
    directory: Path, candidate: CohortBCandidate
) -> CohortBValidatedSource:
    """Fail closed on any mismatch between the manifest and the actual local file.

    Independently re-derives format, MIME, byte count, dimensions and SHA-256 from the file
    itself and never trusts a manifest-declared value without checking it against the bytes
    on disk (D3-2 "hash drift" / "version drift" stop condition).
    """

    path = directory / candidate.filename
    if not path.is_file():
        raise FileNotFoundError(f"Cohort B source file is missing: {candidate.fixture_id}")
    extensions = _COHORT_B_EXTENSIONS_BY_FORMAT[candidate.declared_format]
    if not candidate.filename.lower().endswith(extensions):
        raise ValueError(f"{candidate.fixture_id} filename does not match its declared format")
    with path.open("rb") as source:
        prefix = source.read(16)
    sniffed_format = _sniff_image_format(prefix)
    if sniffed_format != candidate.declared_format:
        raise ValueError(f"{candidate.fixture_id} signature does not match its declared format")
    actual_sha256 = _sha256_of(path)
    if actual_sha256 != candidate.declared_sha256:
        raise ValueError(f"{candidate.fixture_id} SHA-256 does not match the approved manifest")
    byte_count = path.stat().st_size
    width, height = _probe_declared_dimensions(path)
    return CohortBValidatedSource(
        fixture_id=candidate.fixture_id,
        filename=candidate.filename,
        format=sniffed_format,
        mime=_COHORT_B_MIME_BY_FORMAT[sniffed_format],
        sha256=actual_sha256,
        byte_count=byte_count,
        width=width,
        height=height,
    )


def _sample_matches_profile(
    sample: Mapping[str, object], profile: EvaluationProfile
) -> bool:
    digest_is_valid = sample.get("source_digest_verified") is True
    if profile.expected_reason == AdmissionReason.FILE_BYTES_EXCEEDED.value:
        digest_is_valid = (
            sample.get("source_sha256") is None
            and sample.get("source_digest_verified") is None
        )
    return (
        sample.get("exit_code") == 0
        and sample.get("failure") is None
        and sample.get("outcome") == profile.expected_outcome
        and sample.get("reason") == profile.expected_reason
        and sample.get("artifact_ref_verified") is True
        and digest_is_valid
        and sample.get("measurement_failure") is None
        and sample.get("memory_status")
        not in {None, TargetStatus.MEASUREMENT_INVALID.value}
    )


def _resolve_clean_git_head(manifest_path: Path) -> str:
    repository_root = next(
        (
            candidate
            for candidate in manifest_path.resolve().parents
            if (candidate / ".git").exists()
        ),
        None,
    )
    if repository_root is None:
        raise RuntimeError("evaluation manifest is not inside a Git worktree")
    head = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    clean = subprocess.run(
        ["git", "-C", str(repository_root), "diff", "--quiet", "HEAD", "--"],
        check=False,
        timeout=5,
    )
    if clean.returncode != 0:
        raise RuntimeError("formal Cohort A execution requires a clean tracked worktree")
    status = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if status.stdout.strip():
        raise RuntimeError("formal Cohort A execution requires a clean worktree")
    return head


def _find_repository_root(start: Path) -> Path:
    root = next(
        (
            candidate
            for candidate in start.resolve().parents
            if (candidate / ".git").exists()
        ),
        None,
    )
    if root is None:
        raise RuntimeError("path is not inside a Git worktree")
    return root


_D2_IMPLEMENTATION_PATHS: tuple[str, ...] = (
    "backend/pyproject.toml",
    "backend/src/sketch2life/contracts/schemas/media_validation.py",
    "backend/src/sketch2life/domain/understanding/image_admission.py",
    "backend/src/sketch2life/domain/understanding/media_quality.py",
    "backend/src/sketch2life/application/ports/image_decoder.py",
    "backend/src/sketch2life/application/services/image_admission.py",
    "backend/src/sketch2life/infrastructure/media_validation/av_image_decoder.py",
    "backend/tests/unit/test_image_admission.py",
    "backend/tests/unit/feat018_admission_manifest.py",
    "features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/manifest-v1.json",
)


def _resolve_backend_clean_head(
    manifest_path: Path, *, code_paths: Sequence[str] = _D2_IMPLEMENTATION_PATHS
) -> str:
    """Resolve HEAD and require the reviewed D2 implementation to match it exactly.

    Cohort B's own local candidate manifest, this D3 benchmark harness and its tests, and
    the surrounding approval/evidence documentation are legitimately edited in the same
    working session that implements and runs this evaluation -- unlike Cohort A's later,
    fully committed formal run, which is why this does not reuse `_resolve_clean_git_head`.
    Only the reviewed D2 admission implementation actually being timed (never this harness)
    must be uncommitted-change-free, so the measurement stays attributable to a known,
    owner-accepted commit. `run_cohort_b` treats this as the single exact-commit preflight
    decision for the entire formal run, before source validation and the sample loop. It is
    intentionally not a concurrent-change detector; rechecking per sample would alter the
    benchmark's timing semantics.
    """

    repository_root = _find_repository_root(manifest_path)
    head = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    clean = subprocess.run(
        ["git", "-C", str(repository_root), "diff", "--quiet", "HEAD", "--", *code_paths],
        check=False,
        timeout=5,
    )
    if clean.returncode != 0:
        raise RuntimeError(
            "formal Cohort B execution requires the reviewed D2 implementation to be clean"
        )
    status = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            *code_paths,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if status.stdout.strip():
        raise RuntimeError(
            "formal Cohort B execution requires the reviewed D2 implementation to be clean"
        )
    return head


def run_cohort_a(
    manifest_path: Path,
    *,
    repeats: int = 20,
    commit_identity: str,
    timeout_seconds: float = DEFAULT_CHILD_TIMEOUT_SECONDS,
    head_resolver: Callable[[], str] | None = None,
) -> dict[str, object]:
    if repeats != 20:
        raise ValueError("formal Cohort A execution requires exactly 20 repeats")
    if len(commit_identity) != 40 or any(
        character not in "0123456789abcdef" for character in commit_identity
    ):
        raise ValueError("formal Cohort A execution requires an exact lowercase commit SHA")
    actual_head = head_resolver() if head_resolver is not None else _resolve_clean_git_head(
        manifest_path
    )
    if actual_head != commit_identity:
        raise ValueError("declared commit identity does not match the clean worktree HEAD")
    profiles = load_evaluation_manifest(manifest_path)
    manifest_sha256 = _sha256_of(manifest_path)
    with tempfile.TemporaryDirectory(prefix="feat018-d3-") as scratch:
        fixtures = materialize_cohort_a(profiles, Path(scratch) / "cohort-a")
        passes: list[dict[str, object]] = []
        samples: list[dict[str, object]] = []
        order = list(profiles)
        for profile in order:
            path, digest = fixtures[profile.fixture_id]
            source_bytes = path.stat().st_size
            for repeat in range(repeats):
                _verify_frozen_source(path, digest, source_bytes)
                sample_id = f"cohort-a:{profile.fixture_id}:{repeat}"
                sample = run_child_sample(
                    ChildRequest(
                        sample_id,
                        profile.fixture_id,
                        "A",
                        repeat,
                        str(path),
                        digest,
                        source_bytes,
                        commit_identity,
                    ),
                    timeout_seconds=timeout_seconds,
                )
                sample["expected_outcome"] = profile.expected_outcome
                sample["expected_reason"] = profile.expected_reason
                sample["decode_stage"] = profile.decode_stage.value
                samples.append(sample)
        passes.append(
            {
                "pass_id": "forward",
                "profile_order": [p.fixture_id for p in order],
                "samples": samples,
            }
        )
        by_profile: dict[str, list[float]] = {p.fixture_id: [] for p in profiles}
        for sample in samples:
            elapsed = sample.get("admission_elapsed_ms")
            fixture_id = sample.get("fixture_id")
            if isinstance(elapsed, (int, float)) and isinstance(fixture_id, str):
                by_profile[fixture_id].append(float(elapsed))
        reverse_needed = repeats >= 10 and any(
            len(values) >= 10 and has_order_effect(values) for values in by_profile.values()
        )
        if reverse_needed:
            reverse_samples: list[dict[str, object]] = []
            for profile in reversed(order):
                path, digest = fixtures[profile.fixture_id]
                source_bytes = path.stat().st_size
                for repeat in range(repeats):
                    _verify_frozen_source(path, digest, source_bytes)
                    sample_id = f"cohort-a-reverse:{profile.fixture_id}:{repeat}"
                    sample = run_child_sample(
                        ChildRequest(
                            sample_id,
                            profile.fixture_id,
                            "A",
                            repeat,
                            str(path),
                            digest,
                            source_bytes,
                            commit_identity,
                        ),
                        timeout_seconds=timeout_seconds,
                    )
                    sample["expected_outcome"] = profile.expected_outcome
                    sample["expected_reason"] = profile.expected_reason
                    sample["decode_stage"] = profile.decode_stage.value
                    reverse_samples.append(sample)
            passes.append(
                {
                    "pass_id": "reverse",
                    "profile_order": [p.fixture_id for p in reversed(order)],
                    "samples": reverse_samples,
                }
            )
        profile_samples = {
            profile.fixture_id: [
                sample for sample in samples if sample.get("fixture_id") == profile.fixture_id
            ]
            for profile in profiles
        }
        aggregates = {
            profile.fixture_id: aggregate_profile(profile_samples[profile.fixture_id])
            for profile in profiles
            if len(profile_samples[profile.fixture_id]) >= 20
        }
        pass_aggregates: dict[str, dict[str, Mapping[str, object]]] = {}
        for run_pass in passes:
            pass_id = cast(str, run_pass["pass_id"])
            pass_samples = cast(list[dict[str, object]], run_pass["samples"])
            pass_aggregates[pass_id] = {
                profile.fixture_id: aggregate_profile(
                    [
                        sample
                        for sample in pass_samples
                        if sample.get("fixture_id") == profile.fixture_id
                    ]
                )
                for profile in profiles
                if sum(
                    sample.get("fixture_id") == profile.fixture_id
                    for sample in pass_samples
                )
                >= 20
            }

        complete = all(
            all(
                len(
                    matching := [
                        sample
                        for sample in cast(list[dict[str, object]], run_pass["samples"])
                        if sample.get("fixture_id") == profile.fixture_id
                    ]
                )
                == repeats
                and all(_sample_matches_profile(sample, profile) for sample in matching)
                for profile in profiles
            )
            for run_pass in passes
        )
        groups_by_pass = {
            cast(str, run_pass["pass_id"]): {
                stage.value: sum(
                    sample.get("decode_stage") == stage.value
                    for sample in cast(list[dict[str, object]], run_pass["samples"])
                )
                for stage in DecodeStage
            }
            for run_pass in passes
        }
        return {
            "schema": "Feat018ImageAdmissionEvaluationReportV1",
            "cohort": "A",
            "commit_identity": commit_identity,
            "manifest_sha256": manifest_sha256,
            "complete": complete,
            "repeats": repeats,
            "reverse_pass_required": reverse_needed,
            "passes": passes,
            "aggregates": aggregates,
            "pass_aggregates": pass_aggregates,
            "decode_stage_sample_counts_by_pass": groups_by_pass,
        }


def _sample_is_valid_cohort_b(sample: Mapping[str, object]) -> bool:
    return (
        sample.get("exit_code") == 0
        and sample.get("failure") is None
        and sample.get("artifact_ref_verified") is True
        and sample.get("source_digest_verified") is True
        and sample.get("measurement_failure") is None
    )


def run_cohort_b(
    manifest_path: Path,
    *,
    repeats: int = 3,
    commit_identity: str,
    timeout_seconds: float = DEFAULT_CHILD_TIMEOUT_SECONDS,
    head_resolver: Callable[[], str] | None = None,
) -> dict[str, object]:
    """Formal Cohort B execution (D3-R2 section 6, D3-U1/D3-U2).

    Eight owner-approved local photographs (4 JPEG + 4 PNG), 3 fresh-process repeats each,
    minimum/median/maximum reporting only, never p95. Unlike Cohort A, the manifest and
    source images are local and git-ignored (`manifest_path.parent`); only sanitized results
    (opaque IDs, formats, bounded metadata, hashes, timings, memory classifications) may
    enter the returned report, which is the only thing a caller may write to tracked
    evidence.
    """

    if repeats != 3:
        raise ValueError("formal Cohort B execution requires exactly 3 repeats per image")
    if len(commit_identity) != 40 or any(
        character not in "0123456789abcdef" for character in commit_identity
    ):
        raise ValueError("formal Cohort B execution requires an exact lowercase commit SHA")
    # This is the single-run exact-commit preflight guard. It deliberately remains outside
    # the formal sample loop, so the benchmark does not claim protection against edits made
    # concurrently after this check returns or change the measured admit() interval.
    actual_head = (
        head_resolver() if head_resolver is not None else _resolve_backend_clean_head(manifest_path)
    )
    if actual_head != commit_identity:
        raise ValueError(
            "declared commit identity does not match the reviewed D2 implementation's HEAD"
        )

    candidates = load_cohort_b_manifest(manifest_path)
    manifest_sha256 = _sha256_of(manifest_path)
    source_directory = manifest_path.parent
    validated = {
        candidate.fixture_id: validate_cohort_b_source(source_directory, candidate)
        for candidate in candidates
    }

    samples: list[dict[str, object]] = []
    per_image: dict[str, dict[str, object]] = {}
    for candidate in candidates:
        source = validated[candidate.fixture_id]
        path = source_directory / source.filename
        image_samples: list[dict[str, object]] = []
        for repeat in range(repeats):
            _verify_frozen_source(path, source.sha256, source.byte_count)
            sample_id = f"cohort-b:{candidate.fixture_id}:{repeat}"
            sample = run_child_sample(
                ChildRequest(
                    sample_id,
                    candidate.fixture_id,
                    "B",
                    repeat,
                    str(path),
                    source.sha256,
                    source.byte_count,
                    commit_identity,
                ),
                timeout_seconds=timeout_seconds,
            )
            image_samples.append(sample)
        samples.extend(image_samples)
        per_image[candidate.fixture_id] = {
            "format": source.format,
            "mime": source.mime,
            "sha256": source.sha256,
            "byte_count": source.byte_count,
            "declared_width": source.width,
            "declared_height": source.height,
            "outcomes_observed": sorted(
                {str(sample.get("outcome")) for sample in image_samples}
            ),
            "reasons_observed": sorted(
                {
                    str(sample.get("reason"))
                    for sample in image_samples
                    if sample.get("reason") is not None
                }
            ),
            "aggregate": aggregate_cohort_b_group(image_samples, required_count=repeats),
        }

    expected_total = len(candidates) * repeats
    complete = len(samples) == expected_total and all(
        _sample_is_valid_cohort_b(sample) for sample in samples
    )
    jpeg_count = sum(1 for source in validated.values() if source.format == "JPEG")
    png_count = sum(1 for source in validated.values() if source.format == "PNG")

    return {
        "schema": "Feat018ImageAdmissionEvaluationReportV1",
        "cohort": "B",
        "commit_identity": commit_identity,
        "manifest_sha256": manifest_sha256,
        "execution_occurred": True,
        "complete": complete,
        "repeats_per_image": repeats,
        "expected_image_count": len(candidates),
        "sample_count": len(samples),
        "composition": {"jpeg_count": jpeg_count, "png_count": png_count},
        "per_image": per_image,
        "aggregate": aggregate_cohort_b_group(samples, required_count=expected_total),
        "samples": samples,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    args = parser.parse_args(argv)
    if args.child:
        return child_main()
    parser.error("parent execution is available through run_cohort_a()")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ChildFailure",
    "ChildRequest",
    "CohortBCandidate",
    "CohortBValidatedSource",
    "DecodeStage",
    "EvaluationProfile",
    "GENERATORS",
    "MAX_PROTOCOL_BYTES",
    "MEMORY_TARGET_BYTES",
    "MemoryEvaluation",
    "ProcessMemorySnapshot",
    "TargetStatus",
    "WindowsProcessMemoryReader",
    "aggregate_cohort_b_group",
    "aggregate_profile",
    "calibrate_memory_reader",
    "classify_memory",
    "classify_timing",
    "has_order_effect",
    "load_cohort_b_manifest",
    "load_evaluation_manifest",
    "materialize_cohort_a",
    "nearest_rank_percentile",
    "run_bounded_process",
    "run_child_sample",
    "run_cohort_a",
    "run_cohort_b",
    "summarize_cohort_a",
    "summarize_cohort_b",
    "validate_child_output",
    "validate_cohort_b_source",
]
