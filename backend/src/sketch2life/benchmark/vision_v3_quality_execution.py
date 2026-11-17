"""Owner-authorized Phase 8 Qwen execution boundary.

This module is deliberately separate from the local-only quality runner.  It fixes the approved
D-5/D-6/D-7 decisions in code, constructs the real Qwen adapter internally, and enforces the D-8
30-minute wall-clock budget before every model call.  Raw output remains in-memory and is exposed
only to the existing ``CLASSIFY_ONLY`` collector.

Importing and testing this module does not load a model or use CUDA.  A real execution occurs only
when ``run_authorized_v3_quality_pair`` is called without an injected generation runner.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3RawOutputCollector,
    B3RawOutputMode,
)
from sketch2life.benchmark.vision_v3_mapping_validation_study import qwen_v3_adapter_factory
from sketch2life.benchmark.vision_v3_quality_benchmark import (
    MediaValidationFactory,
    V3QualityAcceptanceThresholds,
    V3QualityCollectionThreshold,
    V3QualityExecutionDecisions,
    V3QualityPassReport,
    V3QualityRawOutputMode,
    V3QualityRepeatGate,
    V3QualityVerdict,
    _run_verified_v3_quality_pass,
    evaluate_v3_quality_pair,
    quality_pass_report_to_dict,
)
from sketch2life.infrastructure.ai.qwen_vision import QwenGenerationRunner
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig

_FIXTURE_ROOT = Path(
    "features/FEAT-003-multimodal-understanding/fixtures/vision-v3-quality"
)
_RUNTIME_ROOT = Path("data/runtime/vision-v3-quality-phase8")
_D8_HARD_CAP = timedelta(minutes=30)
_MODEL_CALL_RESERVE = timedelta(seconds=125)


class V3QualityD8AuthorizationError(ValueError):
    """The execution request does not match the owner-approved D-8 boundary."""


class V3QualityD8BudgetExceededError(TimeoutError):
    """The hard cap leaves insufficient time to start another bounded model call."""


@dataclass(frozen=True, slots=True)
class V3QualityD8Authorization:
    """The operator timestamp that anchors the fixed 30-minute Studio budget."""

    studio_started_at: datetime

    def __post_init__(self) -> None:
        if self.studio_started_at.tzinfo is None:
            raise V3QualityD8AuthorizationError("D-8 Studio start time must be timezone-aware")

    @property
    def hard_deadline(self) -> datetime:
        return self.studio_started_at + _D8_HARD_CAP


@dataclass(frozen=True, slots=True)
class V3QualityGpuExecutionReport:
    """Safe Phase 8 pair report; it cannot contain prompt, model, or ground-truth text."""

    contract_name: Literal["VisionV3QualityGpuExecutionReportV1"]
    contract_version: Literal["1.0"]
    studio_started_at: datetime
    hard_cap_seconds: int
    runner_finished_at: datetime
    pass_1: V3QualityPassReport
    repeat_1: V3QualityPassReport
    verdict: V3QualityVerdict


def approved_v3_quality_execution_decisions() -> V3QualityExecutionDecisions:
    """Return exactly the owner-approved D-5, D-6, and D-7 values."""

    return V3QualityExecutionDecisions(
        d5_acceptance_thresholds=V3QualityAcceptanceThresholds(
            collections=(
                V3QualityCollectionThreshold("entities", 0.80, 0.80, None),
                V3QualityCollectionThreshold("actions", 0.80, 0.80, None),
                V3QualityCollectionThreshold("relations", 0.80, 0.80, None),
                V3QualityCollectionThreshold("themes", 0.80, 0.80, None),
                V3QualityCollectionThreshold(
                    "ambiguous_regions",
                    None,
                    None,
                    1.00,
                    maximum_count_rate=1.00,
                ),
            )
        ),
        d6_repeat_gate=V3QualityRepeatGate(
            expected_attempted_runs=8,
            expected_run_records=8,
            minimum_schema_valid_runs=8,
            systemic_truncation_threshold=2,
            repeat_window=timedelta(minutes=15),
            require_same_session=True,
            block_on_input_integrity_failure=True,
            block_on_runtime_or_device_failure=True,
        ),
        d7_raw_output_mode=V3QualityRawOutputMode.CLASSIFY_ONLY,
    )


def _require_gpu_runtime(runtime_config: QwenVisionRuntimeConfig) -> None:
    if runtime_config.device.lower() != "cuda":
        raise V3QualityD8AuthorizationError("Phase 8 D-8 requires the approved CUDA runtime")
    if runtime_config.allow_model_download:
        raise V3QualityD8AuthorizationError("Phase 8 D-8 forbids model downloads")


def _require_time_for_call(
    authorization: V3QualityD8Authorization,
    now: datetime,
) -> None:
    if now.tzinfo is None:
        raise V3QualityD8AuthorizationError("D-8 budget clock must be timezone-aware")
    if now < authorization.studio_started_at:
        raise V3QualityD8AuthorizationError("D-8 budget clock precedes the Studio start time")
    if now + _MODEL_CALL_RESERVE > authorization.hard_deadline:
        raise V3QualityD8BudgetExceededError(
            "Phase 8 D-8 hard cap leaves insufficient time for another bounded model call"
        )


def run_authorized_v3_quality_pair(
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    *,
    authorization: V3QualityD8Authorization,
    fixture_root: Path = _FIXTURE_ROOT,
    runtime_root: Path = _RUNTIME_ROOT,
    generation_runner: QwenGenerationRunner | None = None,
    validate_media: MediaValidationFactory | None = None,
    report_clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    budget_clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> V3QualityGpuExecutionReport:
    """Run the fixed pass/repeat pair once under D-8 and return a safe report.

    ``generation_runner`` and ``validate_media`` are no-GPU test seams.  A Lightning invocation
    omits both.  The Qwen factory is created here rather than accepted from the caller, so the
    public execution boundary cannot be switched to another model adapter.
    """

    _require_gpu_runtime(runtime_config)
    _require_time_for_call(authorization, budget_clock())
    decisions = approved_v3_quality_execution_decisions()
    adapter_factory = qwen_v3_adapter_factory(
        runtime_config,
        content_policy,
        generation_runner=generation_runner,
    )

    def run_pass(
        run_label: Literal["V3_QUALITY_PASS_1", "V3_QUALITY_REPEAT_1"],
        runtime_dir: Path,
    ) -> V3QualityPassReport:
        collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)

        def before_call() -> None:
            _require_time_for_call(authorization, budget_clock())

        if validate_media is None:
            return _run_verified_v3_quality_pass(
                adapter_factory,
                collector,
                run_label=run_label,
                decisions=decisions,
                fixture_root=fixture_root,
                runtime_dir=runtime_dir,
                clock=report_clock,
                before_adapter_call=before_call,
                vram_not_measured_reason="VRAM is not an acceptance metric for Phase 8",
            )
        return _run_verified_v3_quality_pass(
            adapter_factory,
            collector,
            run_label=run_label,
            decisions=decisions,
            fixture_root=fixture_root,
            runtime_dir=runtime_dir,
            validate_media=validate_media,
            clock=report_clock,
            before_adapter_call=before_call,
            vram_not_measured_reason="VRAM is not an acceptance metric for Phase 8",
        )

    pass_1 = run_pass("V3_QUALITY_PASS_1", runtime_root / "pass-1")
    _require_time_for_call(authorization, budget_clock())
    repeat_1 = run_pass("V3_QUALITY_REPEAT_1", runtime_root / "repeat-1")
    finished_at = budget_clock()
    if finished_at > authorization.hard_deadline:
        raise V3QualityD8BudgetExceededError("Phase 8 D-8 hard cap was exceeded")
    verdict = evaluate_v3_quality_pair(
        pass_1,
        repeat_1,
        decisions=decisions,
        same_lightning_session=True,
        fixture_root=fixture_root,
    )
    return V3QualityGpuExecutionReport(
        contract_name="VisionV3QualityGpuExecutionReportV1",
        contract_version="1.0",
        studio_started_at=authorization.studio_started_at,
        hard_cap_seconds=int(_D8_HARD_CAP.total_seconds()),
        runner_finished_at=finished_at,
        pass_1=pass_1,
        repeat_1=repeat_1,
        verdict=verdict,
    )


def quality_gpu_execution_report_to_dict(
    report: V3QualityGpuExecutionReport,
) -> dict[str, object]:
    """Serialize the safe execution envelope without content-bearing fields."""

    return {
        "contract_name": report.contract_name,
        "contract_version": report.contract_version,
        "studio_started_at": report.studio_started_at.isoformat(),
        "hard_cap_seconds": report.hard_cap_seconds,
        "runner_finished_at": report.runner_finished_at.isoformat(),
        "pass_1": quality_pass_report_to_dict(report.pass_1),
        "repeat_1": quality_pass_report_to_dict(report.repeat_1),
        "verdict": {
            "prompt_protocol_id": report.verdict.prompt_protocol_id,
            "prompt_sha256": report.verdict.prompt_sha256,
            "pass_1": {
                "run_label": report.verdict.pass_1.run_label,
                "attempted_runs": report.verdict.pass_1.attempted_runs,
                "run_record_count": report.verdict.pass_1.run_record_count,
                "is_complete": report.verdict.pass_1.is_complete,
                "schema_valid_count": report.verdict.pass_1.schema_valid_count,
                "schema_valid_requirement_met": (
                    report.verdict.pass_1.schema_valid_requirement_met
                ),
                "thresholds_met": report.verdict.pass_1.thresholds_met,
                "truncated_count": report.verdict.pass_1.truncated_count,
            },
            "repeat_1": {
                "run_label": report.verdict.repeat_1.run_label,
                "attempted_runs": report.verdict.repeat_1.attempted_runs,
                "run_record_count": report.verdict.repeat_1.run_record_count,
                "is_complete": report.verdict.repeat_1.is_complete,
                "schema_valid_count": report.verdict.repeat_1.schema_valid_count,
                "schema_valid_requirement_met": (
                    report.verdict.repeat_1.schema_valid_requirement_met
                ),
                "thresholds_met": report.verdict.repeat_1.thresholds_met,
                "truncated_count": report.verdict.repeat_1.truncated_count,
            },
            "repeat_gap_seconds": report.verdict.repeat_gap.total_seconds(),
            "same_lightning_session": report.verdict.same_lightning_session,
            "overall": report.verdict.overall,
            "blocking_reasons": [item.value for item in report.verdict.blocking_reasons],
        },
    }


def write_safe_v3_quality_execution_report(
    report: V3QualityGpuExecutionReport,
    path: Path,
) -> None:
    """Write one new safe report without overwriting prior execution evidence."""

    if path.is_absolute():
        raise V3QualityD8AuthorizationError("Phase 8 report path must be relative")
    cwd = Path.cwd().resolve()
    resolved = path.resolve()
    if resolved == cwd or cwd not in resolved.parents:
        raise V3QualityD8AuthorizationError("Phase 8 report path escaped the working directory")
    if resolved.exists():
        raise FileExistsError("Phase 8 report already exists; automatic reruns cannot overwrite it")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(quality_gpu_execution_report_to_dict(report), indent=2) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "V3QualityD8Authorization",
    "V3QualityD8AuthorizationError",
    "V3QualityD8BudgetExceededError",
    "V3QualityGpuExecutionReport",
    "approved_v3_quality_execution_decisions",
    "quality_gpu_execution_report_to_dict",
    "run_authorized_v3_quality_pair",
    "write_safe_v3_quality_execution_report",
]
