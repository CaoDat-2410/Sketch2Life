from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from sketch2life.benchmark.vision_v3_quality_execution import (
    V3QualityD8Authorization,
    V3QualityD8AuthorizationError,
    V3QualityD8BudgetExceededError,
    approved_v3_quality_execution_decisions,
    quality_gpu_execution_report_to_dict,
    run_authorized_v3_quality_pair,
    write_safe_v3_quality_execution_report,
)
from sketch2life.contracts.schemas.vision import VisionMediaValidationProvenanceV1
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_SOURCE = (
    _REPO_ROOT / "features/FEAT-003-multimodal-understanding/fixtures/vision-v3-quality"
)
_STARTED_AT = datetime(2026, 9, 9, 7, 30, tzinfo=UTC)
_EMPTY_RESULT = json.dumps(
    {
        "entities": [],
        "actions": [],
        "relations": [],
        "themes": [],
        "ambiguous_regions": [],
    }
)


class _StaticGenerationRunner:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, *_args: Any, **_kwargs: Any) -> str:
        self.calls += 1
        return _EMPTY_RESULT


def _validation(
    _fixture_id: str, _image_path: Path, _audio_path: Path
) -> VisionMediaValidationProvenanceV1:
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="test-p2t1",
        validation_artifact_sha256="b" * 64,
        decision="PASS",
        validator_policy_version="test-policy",
    )


def _report_clock() -> Any:
    values = iter(
        (
            _STARTED_AT + timedelta(minutes=1),
            _STARTED_AT + timedelta(minutes=3),
            _STARTED_AT + timedelta(minutes=4),
            _STARTED_AT + timedelta(minutes=6),
            _STARTED_AT + timedelta(minutes=6, seconds=1),
        )
    )
    return lambda: next(values)


def _runtime(tmp_path: Path, **overrides: Any) -> QwenVisionRuntimeConfig:
    values: dict[str, Any] = {
        "model_dir": tmp_path / "model",
        "device": "cuda",
        "allow_model_download": False,
    }
    values.update(overrides)
    return QwenVisionRuntimeConfig(**values)


def _fixture_copy(tmp_path: Path) -> Path:
    root = tmp_path / "vision-v3-quality"
    shutil.copytree(_FIXTURE_SOURCE, root)
    return root


def test_approved_decisions_are_exact_and_classify_only() -> None:
    decisions = approved_v3_quality_execution_decisions()
    assert decisions.d5_acceptance_thresholds is not None
    assert decisions.d6_repeat_gate is not None
    assert decisions.d7_raw_output_mode is not None

    thresholds = decisions.d5_acceptance_thresholds.collections
    observed_thresholds = [
        (item.collection, item.minimum_coverage, item.minimum_accuracy) for item in thresholds
    ]
    assert observed_thresholds == [
        ("entities", 0.8, 0.8),
        ("actions", 0.8, 0.8),
        ("relations", 0.8, 0.8),
        ("themes", 0.8, 0.8),
        ("ambiguous_regions", None, None),
    ]
    assert thresholds[-1].minimum_count_rate == 1.0
    assert thresholds[-1].maximum_count_rate == 1.0
    assert decisions.d6_repeat_gate.expected_attempted_runs == 8
    assert decisions.d6_repeat_gate.expected_run_records == 8
    assert decisions.d6_repeat_gate.minimum_schema_valid_runs == 8
    assert decisions.d6_repeat_gate.repeat_window == timedelta(minutes=15)
    assert decisions.d7_raw_output_mode.value == "CLASSIFY_ONLY"


def test_no_gpu_pair_uses_qwen_mapping_and_returns_safe_quality_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    fixture_root = _fixture_copy(tmp_path)
    runner = _StaticGenerationRunner()
    budget_now = _STARTED_AT + timedelta(seconds=30)

    report = run_authorized_v3_quality_pair(
        _runtime(tmp_path),
        LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
        authorization=V3QualityD8Authorization(_STARTED_AT),
        fixture_root=fixture_root,
        runtime_root=Path("scratch/phase8"),
        generation_runner=runner,
        validate_media=_validation,
        report_clock=_report_clock(),
        budget_clock=lambda: budget_now,
    )

    assert runner.calls == 16
    assert report.hard_cap_seconds == 1800
    assert report.pass_1.attempted_runs == 8
    assert report.pass_1.schema_valid_count == 8
    assert report.repeat_1.attempted_runs == 8
    assert report.repeat_1.schema_valid_count == 8
    assert report.verdict.repeat_gap == timedelta(minutes=1)
    assert report.verdict.overall == "QUALITY_NOT_READY"
    assert not (tmp_path / "scratch/phase8/pass-1").exists()
    assert not (tmp_path / "scratch/phase8/repeat-1").exists()

    payload_text = json.dumps(quality_gpu_execution_report_to_dict(report))
    assert _EMPTY_RESULT not in payload_text
    assert str(tmp_path) not in payload_text
    assert "prompt_text" not in payload_text
    assert "ground_truth_text" not in payload_text

    output = Path("data/runtime/v3-phase8-safe-report.json")
    write_safe_v3_quality_execution_report(report, output)
    assert json.loads(output.read_text(encoding="utf-8"))["verdict"]["overall"] == (
        "QUALITY_NOT_READY"
    )
    with pytest.raises(FileExistsError, match="cannot overwrite"):
        write_safe_v3_quality_execution_report(report, output)


@pytest.mark.parametrize(
    "overrides",
    (
        {"device": "cpu"},
        {"allow_model_download": True},
    ),
)
def test_execution_rejects_unapproved_runtime_before_fixture_or_model_action(
    tmp_path: Path,
    overrides: dict[str, object],
) -> None:
    runner = _StaticGenerationRunner()

    with pytest.raises(V3QualityD8AuthorizationError):
        run_authorized_v3_quality_pair(
            _runtime(tmp_path, **overrides),
            LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
            authorization=V3QualityD8Authorization(_STARTED_AT),
            fixture_root=tmp_path / "missing",
            generation_runner=runner,
            budget_clock=lambda: _STARTED_AT,
        )

    assert runner.calls == 0


def test_execution_stops_before_model_action_when_hard_cap_reserve_is_gone(
    tmp_path: Path,
) -> None:
    runner = _StaticGenerationRunner()

    with pytest.raises(V3QualityD8BudgetExceededError, match="hard cap"):
        run_authorized_v3_quality_pair(
            _runtime(tmp_path),
            LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
            authorization=V3QualityD8Authorization(_STARTED_AT),
            fixture_root=tmp_path / "missing",
            generation_runner=runner,
            budget_clock=lambda: _STARTED_AT + timedelta(minutes=28),
        )

    assert runner.calls == 0


def test_authorization_and_report_paths_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(V3QualityD8AuthorizationError, match="timezone-aware"):
        V3QualityD8Authorization(datetime(2026, 9, 9, 7, 30))

    with pytest.raises(V3QualityD8AuthorizationError, match="relative"):
        write_safe_v3_quality_execution_report(
            None,  # type: ignore[arg-type]
            tmp_path / "report.json",
        )
