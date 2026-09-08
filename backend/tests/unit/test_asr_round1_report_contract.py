"""Regression coverage for the Round-1 report's per-profile-vs-aggregate denominator.

Defect fixed: a profile's `schema_validity_rate`/`total_runs` must be derived from that
profile's own runs only — never the combined run count across both Round-1 profiles.
"""

from __future__ import annotations

from hashlib import sha256

import pytest
from pydantic import ValidationError

from sketch2life.benchmark.asr_readiness import (
    ROUND1_PROFILE_IDS,
    AsrBenchmarkMeasurementV1,
    AsrRound1BenchmarkReportV1,
    AsrRound1BenchmarkSettingsV1,
    AsrRound1MetricSetV1,
    AsrRound1RunOutcome,
    AsrRound1RunResultV1,
    AsrSpeechPresenceOutcome,
    BenchmarkMeasurementStatus,
)
from sketch2life.contracts.schemas.asr import AsrErrorCode, AsrErrorDetail, AsrSpeechDiagnostic
from sketch2life.contracts.schemas.asr_benchmark import AsrFixtureScenario, AsrFixtureSplit

_INT8, _FP16 = ROUND1_PROFILE_IDS


def _measured(value: float) -> AsrBenchmarkMeasurementV1:
    return AsrBenchmarkMeasurementV1(
        status=BenchmarkMeasurementStatus.MEASURED, value=value, reason="test"
    )


def _succeeded_run(run_index: int, profile_id) -> AsrRound1RunResultV1:  # noqa: ANN001
    return AsrRound1RunResultV1(
        run_id=f"asr-round1-{sha256(f'{profile_id}-{run_index}'.encode()).hexdigest()}",
        fixture_id=f"fixture-{run_index}",
        scenario=AsrFixtureScenario.VI_CLEAR,
        split=AsrFixtureSplit.HELD_OUT,
        profile_id=profile_id,
        profile_config_hash="a" * 64,
        outcome=AsrRound1RunOutcome.SUCCEEDED,
        attempt_number=1,
        repair_attempted=False,
        is_cold_start=False,
        inference_latency_ms=100.0,
        speech_diagnostic=AsrSpeechDiagnostic.DETECTED,
        speech_presence_outcome=AsrSpeechPresenceOutcome.MATCH,
    )


def _failed_run(run_index: int, profile_id) -> AsrRound1RunResultV1:  # noqa: ANN001
    return AsrRound1RunResultV1(
        run_id=f"asr-round1-{sha256(f'{profile_id}-{run_index}'.encode()).hexdigest()}",
        fixture_id=f"fixture-{run_index}",
        scenario=AsrFixtureScenario.SILENCE,
        split=AsrFixtureSplit.HELD_OUT,
        profile_id=profile_id,
        profile_config_hash="a" * 64,
        outcome=AsrRound1RunOutcome.FAILED,
        attempt_number=0,
        repair_attempted=False,
        is_cold_start=False,
        error_code=AsrErrorCode.INPUT_NOT_VALIDATED,
        error_detail=AsrErrorDetail.MEDIA_VALIDATION_NOT_PASSED,
    )


def _metrics(total: int, success: int, failure: int) -> AsrRound1MetricSetV1:
    return AsrRound1MetricSetV1(
        total_runs=_measured(float(total)),
        success_count=_measured(float(success)),
        failure_count=_measured(float(failure)),
    )


def _base_kwargs(runs: tuple[AsrRound1RunResultV1, ...], metrics_by_profile: dict) -> dict:  # noqa: ANN001
    return dict(
        report_id="asr-round1-report-" + "b" * 64,
        manifest_version="asr-round1-v1",
        manifest_sha256="c" * 64,
        normalizer_version="vi-asr-normalizer-v1",
        settings=AsrRound1BenchmarkSettingsV1(),
        split=AsrFixtureSplit.HELD_OUT,
        runs=runs,
        metrics_by_profile=metrics_by_profile,
    )


def test_per_profile_total_matches_its_own_runs_not_the_combined_count() -> None:
    # 3 INT8 runs (2 success + 1 failure) and 2 FP16 runs (1 success + 1 failure): 5 total,
    # but each profile's own denominator must reflect only its own runs.
    runs = (
        _succeeded_run(1, _INT8),
        _succeeded_run(2, _INT8),
        _failed_run(3, _INT8),
        _succeeded_run(1, _FP16),
        _failed_run(2, _FP16),
    )
    metrics_by_profile = {
        _INT8: _metrics(total=3, success=2, failure=1),
        _FP16: _metrics(total=2, success=1, failure=1),
    }

    report = AsrRound1BenchmarkReportV1(**_base_kwargs(runs, metrics_by_profile))

    assert len(report.runs) == 5
    int8_runs = [run for run in report.runs if run.profile_id == _INT8]
    fp16_runs = [run for run in report.runs if run.profile_id == _FP16]
    assert len(int8_runs) == 3
    assert len(fp16_runs) == 2
    assert report.metrics_by_profile[_INT8].total_runs.value == 3
    assert report.metrics_by_profile[_FP16].total_runs.value == 2


def test_report_rejects_a_profile_total_runs_borrowed_from_the_aggregate() -> None:
    runs = (
        _succeeded_run(1, _INT8),
        _succeeded_run(2, _INT8),
        _failed_run(3, _INT8),
        _succeeded_run(1, _FP16),
        _failed_run(2, _FP16),
    )
    # INT8 actually has 3 runs, but its metrics wrongly claim the combined 5-run total.
    metrics_by_profile = {
        _INT8: _metrics(total=5, success=2, failure=1),
        _FP16: _metrics(total=2, success=1, failure=1),
    }

    with pytest.raises(ValidationError, match="total_runs does not match its own run count"):
        AsrRound1BenchmarkReportV1(**_base_kwargs(runs, metrics_by_profile))


def test_report_rejects_success_plus_failure_not_equal_to_profile_run_count() -> None:
    runs = (
        _succeeded_run(1, _INT8),
        _succeeded_run(2, _INT8),
        _failed_run(3, _INT8),
        _succeeded_run(1, _FP16),
        _failed_run(2, _FP16),
    )
    # INT8 has 3 real runs (2 success + 1 failure) but metrics claim 2 + 2 = 4.
    metrics_by_profile = {
        _INT8: _metrics(total=3, success=2, failure=2),
        _FP16: _metrics(total=2, success=1, failure=1),
    }

    with pytest.raises(ValidationError, match="success_count \\+ failure_count must equal"):
        AsrRound1BenchmarkReportV1(**_base_kwargs(runs, metrics_by_profile))


def test_report_accepts_not_measured_counts_without_a_denominator_check() -> None:
    runs = (_succeeded_run(1, _INT8), _succeeded_run(1, _FP16))
    metrics_by_profile = {
        _INT8: AsrRound1MetricSetV1(),
        _FP16: AsrRound1MetricSetV1(),
    }

    report = AsrRound1BenchmarkReportV1(**_base_kwargs(runs, metrics_by_profile))

    status = report.metrics_by_profile[_INT8].total_runs.status
    assert status == BenchmarkMeasurementStatus.NOT_MEASURED
