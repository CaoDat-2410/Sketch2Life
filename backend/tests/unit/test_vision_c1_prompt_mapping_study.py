from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from sketch2life.benchmark.vision_b3_mapping_study import (
    B3FixtureRunResult,
    B3MappingStudyReport,
    B3RawOutputCollector,
    B3RawOutputMode,
)
from sketch2life.benchmark.vision_c1_prompt_mapping_study import (
    C1BlockingReason,
    C1PassReport,
    C1RunLabel,
    c1_prompt_protocol_id,
    c1_prompt_schema_target,
    c1_prompt_sha256,
    c1_prompt_text,
    evaluate_c1_readiness,
    qwen_c1_adapter_factory,
    run_c1_pass,
)
from sketch2life.contracts.schemas.vision import VisionErrorCode, VisionImageReferenceV1
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionProfileV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

_SOURCE_REF = VisionImageReferenceV1(artifact_ref="fixture:vision:c1:drawing.bin", sha256="a" * 64)
_EXECUTED_AT = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
_EXPECTED_PROFILE_ID = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1.value
_EXPECTED_CATALOG_HASH = vision_profile_catalog_hash_v2(vision_profile_catalog_v2())
_EMPTY_OBSERVATIONS = {
    "entities": [],
    "actions": [],
    "relations": [],
    "themes": [],
    "ambiguous_regions": [],
}


def _success(**overrides: Any) -> VisionUnderstandingSuccessV2:
    profile = vision_profile_catalog_v2().profiles[0]
    values: dict[str, Any] = {
        "correlation_id": "c1-mapping-study-test",
        "executed_at": _EXECUTED_AT,
        "source_image_ref": _SOURCE_REF,
        "profile_id": profile.profile_id,
        "profile_catalog_hash": _EXPECTED_CATALOG_HASH,
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": "vision-prohibited-lexicon-fixture-v1",
        "policy_match_view_version": "vision-policy-match-view-v2",
        "policy_execution_state": "PASSED",
        "adapter_version": profile.adapter_version,
        "config_hash": vision_profile_config_hash_v2(profile),
        "model_provenance": profile.model_provenance,
        **_EMPTY_OBSERVATIONS,
    }
    values.update(overrides)
    return VisionUnderstandingSuccessV2(**values)


class _ScriptedAdapter:
    """Mirrors ``vision_b3_mapping_study``'s own test double: a fixed outcome/raw-output pair
    per call, invoking the caller-supplied hook only when raw output was actually produced.
    """

    def __init__(
        self,
        outcomes: list[VisionUnderstandingResultV2],
        raw_outputs: list[str | None],
        hook: Any,
    ) -> None:
        assert len(outcomes) == len(raw_outputs)
        self._outcomes = outcomes
        self._raw_outputs = raw_outputs
        self._hook = hook
        self.calls = 0

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
        index = self.calls
        self.calls += 1
        raw = self._raw_outputs[index]
        if raw is not None:
            self._hook(raw)
        return self._outcomes[index]


class _RecordingAdapterFactory:
    """A fake ``C1AdapterFactory``: records the exact prompt/hook it received and returns a
    freshly built scripted adapter wired to that hook -- mirroring how the real
    ``qwen_c1_adapter_factory`` wires ``on_raw_output`` into ``QwenVisionAdapter``. This is the
    only way these tests can construct a ``C1PassReport``: there is no parameter on
    ``run_c1_pass`` that accepts an already-built adapter directly.
    """

    def __init__(
        self, outcomes: list[VisionUnderstandingResultV2], raw_outputs: list[str | None]
    ) -> None:
        self._outcomes = outcomes
        self._raw_outputs = raw_outputs
        self.calls = 0
        self.received_prompt: str | None = None
        self.received_hook: Any = None
        self.built_adapter: _ScriptedAdapter | None = None

    def __call__(self, prompt: str, on_raw_output: Any) -> _ScriptedAdapter:
        self.calls += 1
        self.received_prompt = prompt
        self.received_hook = on_raw_output
        self.built_adapter = _ScriptedAdapter(self._outcomes, self._raw_outputs, on_raw_output)
        return self.built_adapter


class _RecordingGenerationRunner:
    """A ``QwenGenerationRunner`` fake: records every prompt it receives and returns a fixed
    valid V2 JSON payload per call, so the real ``QwenVisionAdapter`` maps to ``SUCCEEDED``
    without a GPU. Used to prove the real ``qwen_c1_adapter_factory`` path never lets the
    adapter's empty default prompt reach generation.
    """

    def __init__(self, outcomes: list[str]) -> None:
        self._outcomes = list(outcomes)
        self.calls = 0
        self.received_prompts: list[str] = []

    def generate(
        self,
        profile: VisionProfileV2,
        runtime_config: QwenVisionRuntimeConfig,
        image_path: Path,
        prompt: str,
    ) -> str:
        del profile, runtime_config, image_path
        self.calls += 1
        self.received_prompts.append(prompt)
        return self._outcomes[self.calls - 1]


def _all_success_scripted() -> tuple[_RecordingAdapterFactory, B3RawOutputCollector]:
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    outcomes = [_success() for _ in range(8)]
    raw_outputs: list[str | None] = [json.dumps(_EMPTY_OBSERVATIONS) for _ in range(8)]
    return _RecordingAdapterFactory(outcomes, raw_outputs), collector


# ---------------------------------------------------------------------------
# Prompt protocol identity
# ---------------------------------------------------------------------------


def test_c1_prompt_sha256_is_deterministic_and_matches_the_text() -> None:
    assert c1_prompt_sha256() == c1_prompt_sha256()
    assert c1_prompt_sha256() == sha256(c1_prompt_text().encode("utf-8")).hexdigest()


def test_c1_prompt_sha256_changes_when_the_text_changes() -> None:
    mutated = c1_prompt_text() + " "

    assert sha256(mutated.encode("utf-8")).hexdigest() != c1_prompt_sha256()


def test_c1_prompt_protocol_identity_is_stable_and_the_text_is_non_empty() -> None:
    assert c1_prompt_protocol_id() == "vision-v2-structured-output-prompt-v1"
    assert c1_prompt_schema_target() == "VisionUnderstandingResultV2"
    assert c1_prompt_text()


# ---------------------------------------------------------------------------
# run_c1_pass: delegates to run_b3_mapping_study, reuses the same eight fixtures
# ---------------------------------------------------------------------------


def test_run_c1_pass_calls_the_adapter_eight_times_and_reports_prompt_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()

    report = run_c1_pass(
        factory,
        collector,
        run_label="C1_PASS_1",
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert factory.calls == 1
    assert factory.built_adapter is not None
    assert factory.built_adapter.calls == 8
    assert factory.received_prompt == c1_prompt_text()
    assert report.run_label == "C1_PASS_1"
    assert report.prompt_protocol_id == c1_prompt_protocol_id()
    assert report.prompt_sha256 == c1_prompt_sha256()
    assert report.mapping.attempted_runs == 8
    assert report.mapping.schema_valid_count == 8
    assert not (tmp_path / "scratch").exists()


def test_c1_pass_report_never_carries_the_prompt_body_or_raw_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    marker = "UNMISTAKABLE_C1_RAW_MARKER"
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    outcomes = [_success() for _ in range(8)]
    raw_outputs: list[str | None] = [json.dumps({"note_marker": marker}) for _ in range(8)]
    factory = _RecordingAdapterFactory(outcomes, raw_outputs)

    report = run_c1_pass(
        factory,
        collector,
        run_label="C1_PASS_1",
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    serialized = json.dumps(
        {
            "run_label": report.run_label,
            "prompt_protocol_id": report.prompt_protocol_id,
            "prompt_sha256": report.prompt_sha256,
            "mapping": dataclasses.asdict(report.mapping),
        },
        default=str,
    )
    assert marker not in serialized
    assert c1_prompt_text() not in serialized


def test_pass_1_and_repeat_1_use_distinct_default_scratch_dirs_and_both_clean_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory_1, collector_1 = _all_success_scripted()
    factory_2, collector_2 = _all_success_scripted()

    pass_1 = run_c1_pass(factory_1, collector_1, run_label="C1_PASS_1", sample_vram=False)
    repeat_1 = run_c1_pass(factory_2, collector_2, run_label="C1_REPEAT_1", sample_vram=False)

    assert pass_1.run_label != repeat_1.run_label
    assert pass_1.mapping.attempted_runs == 8
    assert repeat_1.mapping.attempted_runs == 8
    assert not (tmp_path / "data" / "runtime" / "vision-c1-pass-1").exists()
    assert not (tmp_path / "data" / "runtime" / "vision-c1-repeat-1").exists()


# ---------------------------------------------------------------------------
# Prompt-binding integrity (P1 fix): run_c1_pass dispatches through a factory it
# calls itself -- there is no parameter for an already-built, unverified adapter.
# ---------------------------------------------------------------------------


def test_c1_dispatch_sends_exactly_the_canonical_prompt_through_the_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()

    run_c1_pass(
        factory,
        collector,
        run_label="C1_PASS_1",
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert factory.calls == 1
    assert factory.received_prompt == c1_prompt_text()


def test_c1_dispatch_wires_the_collector_hook_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()

    report = run_c1_pass(
        factory,
        collector,
        run_label="C1_PASS_1",
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert factory.received_hook == collector.hook
    # Wiring is proven end to end, not just by identity: every SUCCEEDED run carries a real
    # classification, which only happens if the hook the factory received was actually invoked.
    assert len(report.mapping.runs) == 8
    assert all(run.fenced is not None for run in report.mapping.runs)


def test_c1_report_identity_matches_the_prompt_actually_dispatched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()

    report = run_c1_pass(
        factory,
        collector,
        run_label="C1_PASS_1",
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert factory.received_prompt is not None
    assert report.prompt_protocol_id == c1_prompt_protocol_id()
    assert report.prompt_sha256 == sha256(factory.received_prompt.encode("utf-8")).hexdigest()


def test_default_empty_prompt_is_never_used_by_the_real_c1_factory_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Integration proof, through the real ``qwen_c1_adapter_factory`` + ``QwenVisionAdapter``,
    that a normal C1 execution path never lets ``_default_prompt_builder``'s empty string reach
    generation -- only a fake generation seam is injected; the prompt-dispatch path is real.
    """

    monkeypatch.chdir(tmp_path)
    runner = _RecordingGenerationRunner([json.dumps(_EMPTY_OBSERVATIONS) for _ in range(8)])
    factory = qwen_c1_adapter_factory(
        QwenVisionRuntimeConfig(model_dir=Path("local-model")),
        LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
        generation_runner=runner,
    )
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)

    report = run_c1_pass(
        factory,
        collector,
        run_label="C1_PASS_1",
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert runner.calls == 8
    assert runner.received_prompts == [c1_prompt_text()] * 8
    assert "" not in runner.received_prompts
    assert report.mapping.schema_valid_count == 8
    assert not (tmp_path / "scratch").exists()


# ---------------------------------------------------------------------------
# evaluate_c1_readiness: the pre-registered mapping-readiness gate
# ---------------------------------------------------------------------------


def _run_result(
    status: str, *, error_code: str | None = None, error_detail: str | None = None
) -> B3FixtureRunResult:
    return B3FixtureRunResult(
        fixture_id="c1-fixture-01",
        status=status,
        error_code=error_code,
        error_detail=error_detail,
        attempt_number=1,
        repair_attempted=False,
        wall_latency_ms=10.0,
        peak_vram_mb=None,
        vram_not_measured_reason="VRAM sampling was disabled for this call",
        fenced=False,
        truncated=False,
        extra_key=False,
        invalid_enum=False,
    )


def _succeeded_and_failed_runs(
    succeeded: int, total: int = 8
) -> tuple[B3FixtureRunResult, ...]:
    good = tuple(_run_result("SUCCEEDED") for _ in range(succeeded))
    bad = tuple(
        _run_result(
            "FAILED",
            error_code=VisionErrorCode.VISION_SCHEMA_INVALID.value,
            error_detail="OUTPUT_MAPPING_FAILED",
        )
        for _ in range(total - succeeded)
    )
    return good + bad


def _mapping_report(
    runs: tuple[B3FixtureRunResult, ...],
    *,
    truncated_count: int = 0,
    profile_id: str = _EXPECTED_PROFILE_ID,
    profile_catalog_hash: str = _EXPECTED_CATALOG_HASH,
    attempted_runs: int | None = None,
) -> B3MappingStudyReport:
    return B3MappingStudyReport(
        profile_id=profile_id,
        profile_catalog_hash=profile_catalog_hash,
        raw_output_mode="CLASSIFY_ONLY",
        attempted_runs=attempted_runs if attempted_runs is not None else len(runs),
        schema_valid_count=sum(1 for run in runs if run.status == "SUCCEEDED"),
        typed_failure_counts={},
        lossless_unwrap_recovered_count=0,
        fenced_count=0,
        truncated_count=truncated_count,
        extra_key_count=0,
        invalid_enum_count=0,
        runs=runs,
    )


def _pass_report(
    run_label: C1RunLabel,
    runs: tuple[B3FixtureRunResult, ...],
    *,
    truncated_count: int = 0,
    prompt_sha256: str | None = None,
    prompt_protocol_id: str | None = None,
    profile_id: str = _EXPECTED_PROFILE_ID,
    profile_catalog_hash: str = _EXPECTED_CATALOG_HASH,
    attempted_runs: int | None = None,
) -> C1PassReport:
    return C1PassReport(
        run_label=run_label,
        prompt_protocol_id=prompt_protocol_id or c1_prompt_protocol_id(),
        prompt_sha256=prompt_sha256 or c1_prompt_sha256(),
        mapping=_mapping_report(
            runs,
            truncated_count=truncated_count,
            profile_id=profile_id,
            profile_catalog_hash=profile_catalog_hash,
            attempted_runs=attempted_runs,
        ),
    )


def test_seven_of_eight_mapping_valid_in_both_passes_is_ready() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(7))
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(7))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_READY"
    assert verdict.blocking_reasons == ()
    assert verdict.pass_1.mapping_valid_count == 7
    assert verdict.repeat_1.mapping_valid_count == 7


def test_six_of_eight_mapping_valid_is_not_ready() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(6))
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(7))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.MAPPING_VALID_BELOW_THRESHOLD in verdict.blocking_reasons


def test_repeat_must_independently_pass_and_is_never_pooled_with_pass_1() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(6))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.MAPPING_VALID_BELOW_THRESHOLD in verdict.blocking_reasons
    assert verdict.pass_1.mapping_valid_ok is True
    assert verdict.repeat_1.mapping_valid_ok is False


def test_prohibited_claim_detected_counts_as_mapping_valid_not_a_failure() -> None:
    runs = (
        _succeeded_and_failed_runs(5, total=5)
        + tuple(
            _run_result(
                "FAILED",
                error_code=VisionErrorCode.PROHIBITED_CLAIM_DETECTED.value,
                error_detail="SYNTHETIC_FIXTURE_CATEGORY",
            )
            for _ in range(2)
        )
        + (
            _run_result(
                "FAILED",
                error_code=VisionErrorCode.VISION_SCHEMA_INVALID.value,
                error_detail="OUTPUT_MAPPING_FAILED",
            ),
        )
    )
    pass_1 = _pass_report("C1_PASS_1", runs)
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(7))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.pass_1.mapping_valid_count == 7
    assert verdict.overall == "MAPPING_READY"


def test_systemic_truncation_at_two_of_eight_is_not_ready() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8), truncated_count=2)
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert (
        C1BlockingReason.SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS
        in verdict.blocking_reasons
    )


def test_one_of_eight_truncation_is_not_systemic() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8), truncated_count=1)
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_READY"


def test_mismatched_prompt_hash_between_passes_is_config_drift() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report(
        "C1_REPEAT_1", _succeeded_and_failed_runs(8), prompt_sha256="0" * 64
    )

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.CONFIG_DRIFT in verdict.blocking_reasons


def test_unexpected_profile_catalog_hash_is_config_drift() -> None:
    pass_1 = _pass_report(
        "C1_PASS_1", _succeeded_and_failed_runs(8), profile_catalog_hash="0" * 64
    )
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.CONFIG_DRIFT in verdict.blocking_reasons


def test_input_integrity_failure_blocks_readiness_despite_high_mapping_valid_count() -> None:
    runs = _succeeded_and_failed_runs(7, total=7) + (
        _run_result(
            "FAILED",
            error_code=VisionErrorCode.INPUT_NOT_VALIDATED.value,
            error_detail="SOURCE_IMAGE_HASH_MISMATCH",
        ),
    )
    pass_1 = _pass_report("C1_PASS_1", runs)
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.INPUT_INTEGRITY_FAILURE in verdict.blocking_reasons


def test_runtime_or_device_failure_blocks_readiness_despite_high_mapping_valid_count() -> None:
    runs = _succeeded_and_failed_runs(7, total=7) + (
        _run_result(
            "FAILED",
            error_code=VisionErrorCode.VISION_TIMEOUT.value,
            error_detail="TIMEOUT_BUDGET_EXCEEDED",
        ),
    )
    pass_1 = _pass_report("C1_PASS_1", runs)
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.RUNTIME_OR_DEVICE_FAILURE in verdict.blocking_reasons


def test_evaluate_c1_readiness_rejects_matching_run_labels() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8))
    duplicate = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8))

    with pytest.raises(ValueError, match="distinct run labels"):
        evaluate_c1_readiness(pass_1, duplicate)


# ---------------------------------------------------------------------------
# Full-eight-run gate integrity (P1 fix): numeric readiness never applies to a
# malformed/partial run set.
# ---------------------------------------------------------------------------


def test_partial_seven_of_seven_report_fails_the_gate_via_incomplete_run_set() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(7, total=7))
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.INCOMPLETE_RUN_SET in verdict.blocking_reasons
    assert C1BlockingReason.MAPPING_VALID_BELOW_THRESHOLD not in verdict.blocking_reasons
    assert verdict.pass_1.is_complete is False
    assert verdict.pass_1.attempted_runs == 7
    assert verdict.pass_1.run_record_count == 7
    assert verdict.pass_1.mapping_valid_ok is False


def test_attempted_runs_and_run_record_count_disagreement_fails_the_gate() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8), attempted_runs=7)
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.INCOMPLETE_RUN_SET in verdict.blocking_reasons
    assert verdict.pass_1.attempted_runs == 7
    assert verdict.pass_1.run_record_count == 8
    assert verdict.pass_1.is_complete is False


def test_valid_eight_run_seven_of_eight_still_passes_after_the_integrity_fix() -> None:
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(7))
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(7))

    verdict = evaluate_c1_readiness(pass_1, repeat_1)

    assert verdict.overall == "MAPPING_READY"
    assert verdict.pass_1.is_complete is True
    assert verdict.pass_1.run_record_count == 8
    assert verdict.pass_1.attempted_runs == 8
