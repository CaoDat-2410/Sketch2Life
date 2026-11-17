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
    C1_PROMPT_V1,
    C1_PROMPT_V2,
    C1_PROMPT_V3,
    C1BlockingReason,
    C1PassReport,
    C1PromptBindingError,
    C1PromptOutOfExperimentScopeError,
    C1PromptProtocol,
    C1RunLabel,
    _resolve_verified_c1_prompt_text,
    c1_prompt_protocol_id,
    c1_prompt_protocol_id_v2,
    c1_prompt_protocol_id_v3,
    c1_prompt_schema_target,
    c1_prompt_sha256,
    c1_prompt_sha256_v2,
    c1_prompt_sha256_v3,
    c1_prompt_text,
    c1_prompt_text_v2,
    c1_prompt_text_v3,
    evaluate_c1_readiness,
    qwen_c1_adapter_factory,
    run_c1_pass,
)
from sketch2life.contracts.schemas.vision import (
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
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
# C1-v2 prompt protocol identity (per the owner-approved local proposal)
# ---------------------------------------------------------------------------

# Golden constant: the exact SHA-256 of the approved v2 text, computed independently of the
# module under test. A future accidental edit to `_C1_PROMPT_LINES_V2` breaks this test loudly.
_C1_PROMPT_SHA256_V2_GOLDEN = (
    "1e880e946dc1f1dcf11731c299702b33ab58e3c098cdda3d6607c080dc8f9fd6"
)


def test_c1_prompt_v2_protocol_identity_is_distinct_from_v1() -> None:
    assert c1_prompt_protocol_id_v2() == "vision-v2-structured-output-prompt-v2"
    assert c1_prompt_protocol_id_v2() != c1_prompt_protocol_id()
    assert c1_prompt_schema_target() == "VisionUnderstandingResultV2"  # unchanged, shared
    assert c1_prompt_text_v2()
    assert c1_prompt_text_v2() != c1_prompt_text()


def test_c1_prompt_v2_sha256_is_deterministic_and_matches_the_text() -> None:
    assert c1_prompt_sha256_v2() == c1_prompt_sha256_v2()
    assert c1_prompt_sha256_v2() == sha256(c1_prompt_text_v2().encode("utf-8")).hexdigest()
    assert c1_prompt_sha256_v2() != c1_prompt_sha256()


def test_c1_prompt_v2_sha256_changes_when_the_text_changes() -> None:
    mutated = c1_prompt_text_v2() + " "

    assert sha256(mutated.encode("utf-8")).hexdigest() != c1_prompt_sha256_v2()


def test_c1_prompt_v2_matches_the_approved_v1_and_repeat_rules_unchanged() -> None:
    """Only rules 6 and 11 (entity label/confidence shape) may differ from v1; the other nine
    lines must be byte-identical, per the owner decision to change exactly Section 2's two rules
    and nothing else.
    """

    v1_lines = c1_prompt_text().split("\n")
    v2_lines = c1_prompt_text_v2().split("\n")
    assert len(v1_lines) == len(v2_lines) == 11
    changed_indices = {5, 10}  # rules 6 and 11, zero-indexed
    for index, (v1_line, v2_line) in enumerate(zip(v1_lines, v2_lines, strict=True)):
        if index in changed_indices:
            assert v1_line != v2_line
        else:
            assert v1_line == v2_line


def test_c1_prompt_v2_sha256_matches_the_golden_constant() -> None:
    """Pins the exact approved v2 text against an independently computed constant."""

    assert c1_prompt_sha256_v2() == _C1_PROMPT_SHA256_V2_GOLDEN


def test_c1_prompt_v1_and_v2_dataclasses_carry_their_own_matching_identity() -> None:
    assert C1_PROMPT_V1.protocol_id == c1_prompt_protocol_id()
    assert C1_PROMPT_V1.prompt_sha256 == c1_prompt_sha256()
    assert C1_PROMPT_V1.prompt_text_provider() == c1_prompt_text()
    assert C1_PROMPT_V2.protocol_id == c1_prompt_protocol_id_v2()
    assert C1_PROMPT_V2.prompt_sha256 == c1_prompt_sha256_v2()
    assert C1_PROMPT_V2.prompt_text_provider() == c1_prompt_text_v2()


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


def test_v2_prompt_dispatches_exactly_v2_text_through_the_real_adapter_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same integration proof as v1's, through the real ``qwen_c1_adapter_factory`` +
    ``QwenVisionAdapter`` (fake generation runner, no GPU), but selecting ``C1_PROMPT_V2``
    explicitly. Proves v2 never silently replaces v1's default and the adapter's own empty
    default prompt is still never reached.
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
        prompt=C1_PROMPT_V2,
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert runner.calls == 8
    assert runner.received_prompts == [c1_prompt_text_v2()] * 8
    assert c1_prompt_text() not in runner.received_prompts
    assert "" not in runner.received_prompts
    assert report.prompt_protocol_id == c1_prompt_protocol_id_v2()
    assert report.prompt_sha256 == c1_prompt_sha256_v2()
    assert report.mapping.schema_valid_count == 8
    assert not (tmp_path / "scratch").exists()


def test_v2_pass_report_carries_v2_identity_not_v1s(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()

    report = run_c1_pass(
        factory,
        collector,
        run_label="C1_PASS_1",
        prompt=C1_PROMPT_V2,
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert factory.received_prompt == c1_prompt_text_v2()
    assert report.prompt_protocol_id == c1_prompt_protocol_id_v2()
    assert report.prompt_protocol_id != c1_prompt_protocol_id()
    assert report.prompt_sha256 == c1_prompt_sha256_v2()
    assert report.prompt_sha256 != c1_prompt_sha256()


def test_v2_pass_report_never_carries_the_prompt_body_or_raw_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    marker = "UNMISTAKABLE_C1_V2_RAW_MARKER"
    collector = B3RawOutputCollector(mode=B3RawOutputMode.CLASSIFY_ONLY)
    outcomes = [_success() for _ in range(8)]
    raw_outputs: list[str | None] = [json.dumps({"note_marker": marker}) for _ in range(8)]
    factory = _RecordingAdapterFactory(outcomes, raw_outputs)

    report = run_c1_pass(
        factory,
        collector,
        run_label="C1_PASS_1",
        prompt=C1_PROMPT_V2,
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
    assert c1_prompt_text_v2() not in serialized
    assert c1_prompt_text() not in serialized


# ---------------------------------------------------------------------------
# Prompt-binding integrity (fix): run_c1_pass verifies a C1PromptProtocol's declared
# identity against its actually-dispatched text before adapter_factory ever runs.
# A caller cannot claim a canonical protocol_id/prompt_sha256 while supplying
# different (or empty) text and have that claim trusted.
# ---------------------------------------------------------------------------


def test_v2_identity_with_empty_text_provider_fails_before_adapter_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()
    forged = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
        prompt_text_provider=lambda: "",
    )

    with pytest.raises(C1PromptBindingError):
        run_c1_pass(
            factory,
            collector,
            run_label="C1_PASS_1",
            prompt=forged,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert factory.calls == 0


def test_v2_identity_with_v1_text_provider_fails_before_adapter_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()
    forged = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
        prompt_text_provider=c1_prompt_text,
    )

    with pytest.raises(C1PromptBindingError):
        run_c1_pass(
            factory,
            collector,
            run_label="C1_PASS_1",
            prompt=forged,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert factory.calls == 0


def test_unknown_protocol_id_with_self_consistent_hash_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()
    text = "an unapproved, self-consistent prompt body"
    forged = C1PromptProtocol(
        protocol_id="unknown-c1-prompt-protocol",
        prompt_sha256=sha256(text.encode("utf-8")).hexdigest(),
        prompt_text_provider=lambda: text,
    )

    with pytest.raises(C1PromptBindingError):
        run_c1_pass(
            factory,
            collector,
            run_label="C1_PASS_1",
            prompt=forged,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert factory.calls == 0


def test_prompt_binding_error_never_leaks_prompt_body_or_raw_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()
    secret = "UNMISTAKABLE_SECRET_PROMPT_BODY_MARKER"
    forged = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
        prompt_text_provider=lambda: secret,
    )

    with pytest.raises(C1PromptBindingError) as excinfo:
        run_c1_pass(
            factory,
            collector,
            run_label="C1_PASS_1",
            prompt=forged,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    message = str(excinfo.value)
    assert secret not in message
    assert c1_prompt_text() not in message
    assert c1_prompt_text_v2() not in message
    assert factory.calls == 0


def test_c1_prompt_binding_error_is_not_exported_but_remains_importable() -> None:
    """Finding 2: an internal binding-integrity signal, not a public module export -- but a
    caller (like these tests) can still import and catch it by name."""

    import sketch2life.benchmark.vision_c1_prompt_mapping_study as c1_module

    assert "C1PromptBindingError" not in c1_module.__all__
    assert c1_module.C1PromptBindingError is C1PromptBindingError


def test_canonical_v1_and_v2_identities_pass_binding_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Canonical protocols never raise ``C1PromptBindingError``; both still dispatch and
    produce a report carrying their own correct identity."""

    monkeypatch.chdir(tmp_path)
    v1_factory, v1_collector = _all_success_scripted()
    v2_factory, v2_collector = _all_success_scripted()

    v1_report = run_c1_pass(
        v1_factory,
        v1_collector,
        run_label="C1_PASS_1",
        prompt=C1_PROMPT_V1,
        fixtures_dir=Path("scratch-v1"),
        sample_vram=False,
    )
    v2_report = run_c1_pass(
        v2_factory,
        v2_collector,
        run_label="C1_PASS_1",
        prompt=C1_PROMPT_V2,
        fixtures_dir=Path("scratch-v2"),
        sample_vram=False,
    )

    assert v1_factory.calls == 1
    assert v1_report.prompt_protocol_id == c1_prompt_protocol_id()
    assert v1_report.prompt_sha256 == c1_prompt_sha256()
    assert v2_factory.calls == 1
    assert v2_report.prompt_protocol_id == c1_prompt_protocol_id_v2()
    assert v2_report.prompt_sha256 == c1_prompt_sha256_v2()


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


# ---------------------------------------------------------------------------
# evaluate_c1_readiness: expected_prompt binding integrity (fix -- readiness bypass)
# ---------------------------------------------------------------------------


def test_unknown_self_consistent_expected_prompt_cannot_produce_mapping_ready() -> None:
    """A directly constructed pair of reports cannot launder an arbitrary, self-consistent
    identity into MAPPING_READY by also passing it as expected_prompt: the expectation itself
    must be a canonical, verified identity, not merely internally consistent."""

    text = "an unapproved, self-consistent expected prompt"
    forged = C1PromptProtocol(
        protocol_id="unknown-c1-expected-prompt",
        prompt_sha256=sha256(text.encode("utf-8")).hexdigest(),
        prompt_text_provider=lambda: text,
    )
    pass_1 = _pass_report(
        "C1_PASS_1",
        _succeeded_and_failed_runs(8),
        prompt_protocol_id=forged.protocol_id,
        prompt_sha256=forged.prompt_sha256,
    )
    repeat_1 = _pass_report(
        "C1_REPEAT_1",
        _succeeded_and_failed_runs(8),
        prompt_protocol_id=forged.protocol_id,
        prompt_sha256=forged.prompt_sha256,
    )

    with pytest.raises(C1PromptBindingError):
        evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=forged)


def test_canonical_v2_expected_prompt_with_empty_provider_fails_closed() -> None:
    forged = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
        prompt_text_provider=lambda: "",
    )
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    with pytest.raises(C1PromptBindingError):
        evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=forged)


def test_canonical_v2_expected_prompt_with_v1_provider_fails_closed() -> None:
    forged = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
        prompt_text_provider=c1_prompt_text,
    )
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    with pytest.raises(C1PromptBindingError):
        evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=forged)


def test_canonical_v1_and_v2_expected_prompts_still_evaluate_normally() -> None:
    v1_pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(7))
    v1_repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(7))

    v1_verdict = evaluate_c1_readiness(v1_pass_1, v1_repeat_1, expected_prompt=C1_PROMPT_V1)

    assert v1_verdict.overall == "MAPPING_READY"
    assert v1_verdict.blocking_reasons == ()

    v2_pass_1 = _pass_report(
        "C1_PASS_1",
        _succeeded_and_failed_runs(7),
        prompt_protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
    )
    v2_repeat_1 = _pass_report(
        "C1_REPEAT_1",
        _succeeded_and_failed_runs(7),
        prompt_protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
    )

    v2_verdict = evaluate_c1_readiness(v2_pass_1, v2_repeat_1, expected_prompt=C1_PROMPT_V2)

    assert v2_verdict.overall == "MAPPING_READY"
    assert v2_verdict.blocking_reasons == ()


def test_expected_prompt_provider_is_called_at_most_once_per_verification() -> None:
    calls = 0

    def counting_provider() -> str:
        nonlocal calls
        calls += 1
        return c1_prompt_text_v2()

    tracked = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
        prompt_text_provider=counting_provider,
    )
    pass_1 = _pass_report(
        "C1_PASS_1",
        _succeeded_and_failed_runs(7),
        prompt_protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
    )
    repeat_1 = _pass_report(
        "C1_REPEAT_1",
        _succeeded_and_failed_runs(7),
        prompt_protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
    )

    evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=tracked)

    assert calls == 1


def test_expected_prompt_binding_error_never_leaks_prompt_body_or_raw_text() -> None:
    secret = "UNMISTAKABLE_EXPECTED_PROMPT_SECRET_MARKER"
    forged = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
        prompt_text_provider=lambda: secret,
    )
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    with pytest.raises(C1PromptBindingError) as excinfo:
        evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=forged)

    message = str(excinfo.value)
    assert secret not in message
    assert c1_prompt_text() not in message
    assert c1_prompt_text_v2() not in message


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


def test_v1_report_evaluated_against_v2_expected_prompt_is_config_drift() -> None:
    """A pass carrying v1's identity, checked against the v2 expectation, must drift -- and vice
    versa -- with no separate v1/v2-specific code path: the existing identity comparison already
    covers it once the expected protocol is a parameter.
    """

    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8))  # v1 identity (default)
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))  # v1 identity too

    verdict = evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=C1_PROMPT_V2)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.CONFIG_DRIFT in verdict.blocking_reasons
    assert verdict.prompt_protocol_id == c1_prompt_protocol_id_v2()


def test_v1_and_v2_reports_mixed_across_passes_is_config_drift() -> None:
    pass_1 = _pass_report(
        "C1_PASS_1",
        _succeeded_and_failed_runs(8),
        prompt_protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
    )
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))  # still v1

    verdict = evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=C1_PROMPT_V2)

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.CONFIG_DRIFT in verdict.blocking_reasons


def test_two_v2_reports_evaluated_against_v2_expected_prompt_is_ready() -> None:
    """Confirms v2 has a genuine ready path too, not just a drift path."""

    pass_1 = _pass_report(
        "C1_PASS_1",
        _succeeded_and_failed_runs(7),
        prompt_protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
    )
    repeat_1 = _pass_report(
        "C1_REPEAT_1",
        _succeeded_and_failed_runs(7),
        prompt_protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
    )

    verdict = evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=C1_PROMPT_V2)

    assert verdict.overall == "MAPPING_READY"
    assert verdict.blocking_reasons == ()


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


# ---------------------------------------------------------------------------
# C1-v3 prompt protocol identity (owner-approved Direction A proposal, Section 2)
#
# v3 is purely additive: v1 and v2 keep their exact text, hashes, defaults, and behavior. The
# only v2 -> v3 difference is one leading generic collection-search sentence on each of rules
# 6-10. No schema, decode, token-budget, timeout, retry, parser, or repair setting is involved.
# ---------------------------------------------------------------------------

# Golden constants: the exact SHA-256 of each approved text, computed independently of the module
# under test. An accidental edit to any approved line tuple breaks these loudly.
_C1_PROMPT_SHA256_V1_GOLDEN = (
    "152ff6c49c657e91b296f60500ef0609b851ad1901fa5291d20e3e30ef65b57e"
)
_C1_PROMPT_SHA256_V3_GOLDEN = (
    "bf8b9cab5df6b2551e627cf0bb92fe977e0dc182fdaae5f3c5face5bc34615f3"
)

# The five approved generic collection-search sentences, transcribed from Section 2 of
# `P2_T3_PHASE_B_B4_DIRECTION_A_PROMPT_V3_PROPOSAL.md`. Keyed by zero-indexed rule position.
_V3_APPROVED_SEARCH_SENTENCES: dict[int, str] = {
    5: (
        "Actively look for every directly observable entity, up to the maximum in rule 3, "
        "before deciding the array is empty."
    ),
    6: "Actively look for a directly observable action before deciding the array is empty.",
    7: (
        "Actively look for a directly observable relation between two entities or actions "
        "before deciding the array is empty."
    ),
    8: (
        "Actively look for a theme suggested by the observed entities, actions, or relations "
        "before deciding the array is empty."
    ),
    9: (
        "Actively look for a visually ambiguous or overlapping region before deciding the "
        "array is empty."
    ),
}


def test_c1_prompt_v3_sha256_matches_the_golden_constant() -> None:
    """Pins the exact approved v3 text against an independently computed constant."""

    assert c1_prompt_sha256_v3() == _C1_PROMPT_SHA256_V3_GOLDEN


def test_c1_prompt_v1_and_v2_text_and_hashes_are_unchanged_by_v3() -> None:
    """v3 is additive only: v1/v2 identities must still match their own golden constants."""

    assert c1_prompt_sha256() == _C1_PROMPT_SHA256_V1_GOLDEN
    assert c1_prompt_sha256_v2() == _C1_PROMPT_SHA256_V2_GOLDEN
    assert c1_prompt_sha256() == sha256(c1_prompt_text().encode("utf-8")).hexdigest()
    assert c1_prompt_sha256_v2() == sha256(c1_prompt_text_v2().encode("utf-8")).hexdigest()
    assert c1_prompt_protocol_id() == "vision-v2-structured-output-prompt-v1"
    assert c1_prompt_protocol_id_v2() == "vision-v2-structured-output-prompt-v2"


def test_c1_prompt_v3_protocol_identity_is_distinct_and_deterministic() -> None:
    assert c1_prompt_protocol_id_v3() == "vision-v2-structured-output-prompt-v3"
    assert c1_prompt_protocol_id_v3() not in {c1_prompt_protocol_id(), c1_prompt_protocol_id_v2()}
    assert c1_prompt_schema_target() == "VisionUnderstandingResultV2"  # unchanged, shared
    assert c1_prompt_text_v3()
    assert c1_prompt_text_v3() not in {c1_prompt_text(), c1_prompt_text_v2()}
    assert c1_prompt_sha256_v3() == c1_prompt_sha256_v3()
    assert c1_prompt_sha256_v3() == sha256(c1_prompt_text_v3().encode("utf-8")).hexdigest()
    assert c1_prompt_sha256_v3() not in {c1_prompt_sha256(), c1_prompt_sha256_v2()}


def test_c1_prompt_v3_sha256_changes_when_the_text_changes() -> None:
    mutated = c1_prompt_text_v3() + " "

    assert sha256(mutated.encode("utf-8")).hexdigest() != c1_prompt_sha256_v3()


def test_exactly_rules_six_to_ten_differ_from_v2_by_the_approved_search_sentences() -> None:
    """The whole bounded v2 -> v3 change, asserted line by line.

    Rules 1-5 and 11 must be byte-identical to v2; rules 6-10 must each be exactly the approved
    generic search sentence, one space, then that rule's unchanged v2 text. Nothing else may
    differ -- no key list, ID pattern, output cap, confidence rule, or JSON-formatting clause.
    """

    v2_lines = c1_prompt_text_v2().split("\n")
    v3_lines = c1_prompt_text_v3().split("\n")
    assert len(v2_lines) == len(v3_lines) == 11

    for index, (v2_line, v3_line) in enumerate(zip(v2_lines, v3_lines, strict=True)):
        if index in _V3_APPROVED_SEARCH_SENTENCES:
            assert v3_line == f"{_V3_APPROVED_SEARCH_SENTENCES[index]} {v2_line}"
        else:
            assert v3_line == v2_line

    assert set(_V3_APPROVED_SEARCH_SENTENCES) == {5, 6, 7, 8, 9}  # rules 6-10, zero-indexed


def test_c1_prompt_v3_dataclass_carries_its_own_matching_identity() -> None:
    assert C1_PROMPT_V3.protocol_id == c1_prompt_protocol_id_v3()
    assert C1_PROMPT_V3.prompt_sha256 == c1_prompt_sha256_v3()
    assert C1_PROMPT_V3.prompt_text_provider() == c1_prompt_text_v3()
    # v1/v2 dataclasses are untouched by v3's addition.
    assert C1_PROMPT_V1.prompt_text_provider() == c1_prompt_text()
    assert C1_PROMPT_V2.prompt_text_provider() == c1_prompt_text_v2()


def test_v3_text_reaches_the_real_qwen_adapter_without_any_c1_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No-GPU proof that the real prompt-injection seam carries the exact v3 text.

    Deliberately does **not** go through ``run_c1_pass``: v3 is out of scope for the C1
    experiment, so this exercises the smallest real seam instead -- the production
    ``qwen_c1_adapter_factory`` building a real ``QwenVisionAdapter`` with a fake generation
    runner -- and produces no ``C1PassReport``, no run label, and no readiness verdict.
    """

    monkeypatch.chdir(tmp_path)
    image_path = tmp_path / "drawing.bin"
    image_bytes = b"synthetic-c1-v3-seam-image"
    image_path.write_bytes(image_bytes)
    runner = _RecordingGenerationRunner([json.dumps(_EMPTY_OBSERVATIONS)])
    factory = qwen_c1_adapter_factory(
        QwenVisionRuntimeConfig(model_dir=Path("local-model")),
        LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
        generation_runner=runner,
    )

    adapter = factory(c1_prompt_text_v3(), lambda _raw: None)
    result = adapter.understand(
        VisionUnderstandingRequestV2(
            correlation_id="c1-v3-seam-check",
            source_image_ref=VisionImageReferenceV1(
                artifact_ref=image_path.name, sha256=sha256(image_bytes).hexdigest()
            ),
            media_validation=VisionMediaValidationProvenanceV1(
                validation_artifact_ref="fixture:vision:c1:validation-pass",
                validation_artifact_sha256="c" * 64,
                decision="PASS",
                validator_policy_version="media-quality-policy-v1",
            ),
            requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        )
    )

    assert isinstance(result, VisionUnderstandingSuccessV2)
    assert runner.calls == 1
    assert runner.received_prompts == [c1_prompt_text_v3()]
    assert c1_prompt_text() not in runner.received_prompts
    assert c1_prompt_text_v2() not in runner.received_prompts
    assert "" not in runner.received_prompts


def test_run_c1_pass_rejects_v3_before_any_factory_fixture_or_scratch_side_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: v3 must never execute as a C1 pass.

    ``run_c1_pass`` only knows ``C1_PASS_1``/``C1_REPEAT_1`` over B3's generated fixtures, while
    v3's approved plan needs its own runner, ``V3_PASS_1``/``V3_REPEAT_1`` labels, and newly
    authored disjoint fixtures. Allowing it here would mint correctly hashed but wrongly scoped
    evidence.
    """

    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()

    with pytest.raises(C1PromptOutOfExperimentScopeError):
        run_c1_pass(
            factory,
            collector,
            run_label="C1_PASS_1",
            prompt=C1_PROMPT_V3,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert factory.calls == 0
    assert factory.built_adapter is None
    assert not (tmp_path / "scratch").exists()
    assert not (tmp_path / "data").exists()


def test_evaluate_c1_readiness_rejects_v3_and_can_never_return_mapping_ready() -> None:
    """Regression: v3 must never reach a C1 ``MAPPING_READY`` verdict, even with perfect runs."""

    pass_1 = _pass_report(
        "C1_PASS_1",
        _succeeded_and_failed_runs(8),
        prompt_protocol_id=c1_prompt_protocol_id_v3(),
        prompt_sha256=c1_prompt_sha256_v3(),
    )
    repeat_1 = _pass_report(
        "C1_REPEAT_1",
        _succeeded_and_failed_runs(8),
        prompt_protocol_id=c1_prompt_protocol_id_v3(),
        prompt_sha256=c1_prompt_sha256_v3(),
    )

    with pytest.raises(C1PromptOutOfExperimentScopeError):
        evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=C1_PROMPT_V3)


def test_v3_scope_rejection_happens_before_the_prompt_provider_is_ever_called(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scope gate reads the declared identity only -- it never invokes caller text."""

    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()
    calls = 0

    def counting_provider() -> str:
        nonlocal calls
        calls += 1
        return c1_prompt_text_v3()

    declared_v3 = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v3(),
        prompt_sha256=c1_prompt_sha256_v3(),
        prompt_text_provider=counting_provider,
    )

    with pytest.raises(C1PromptOutOfExperimentScopeError):
        run_c1_pass(
            factory,
            collector,
            run_label="C1_PASS_1",
            prompt=declared_v3,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert calls == 0
    assert factory.calls == 0


def test_v3_scope_error_never_leaks_a_prompt_body_and_carries_only_safe_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()
    secret = "UNMISTAKABLE_V3_SECRET_PROMPT_BODY_MARKER"
    declared_v3 = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v3(),
        prompt_sha256=c1_prompt_sha256_v3(),
        prompt_text_provider=lambda: secret,
    )

    with pytest.raises(C1PromptOutOfExperimentScopeError) as excinfo:
        run_c1_pass(
            factory,
            collector,
            run_label="C1_PASS_1",
            prompt=declared_v3,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    message = str(excinfo.value)
    assert secret not in message
    assert c1_prompt_text_v3() not in message
    assert c1_prompt_text_v2() not in message
    assert c1_prompt_text() not in message
    # Only the two values already documented as safe to persist may appear.
    assert c1_prompt_protocol_id_v3() in message
    assert c1_prompt_sha256_v3() in message
    assert factory.calls == 0


def test_v3_scope_error_is_not_exported_but_remains_importable() -> None:
    """A module-local benchmark signal, like ``C1PromptBindingError`` -- not public surface."""

    import sketch2life.benchmark.vision_c1_prompt_mapping_study as c1_module

    assert "C1PromptOutOfExperimentScopeError" not in c1_module.__all__
    assert "C1_PROMPT_V3" in c1_module.__all__  # the reviewed identity itself stays exported
    assert c1_module.C1PromptOutOfExperimentScopeError is C1PromptOutOfExperimentScopeError


def test_v3_protocol_id_with_a_non_canonical_hash_still_fails_binding_not_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scope gate is narrow: it never masks a forgery.

    A self-consistent but unapproved text/hash pair merely *claiming* the v3 protocol ID is not
    on the canonical allowlist at all, so it stays a binding-integrity failure exactly as it was
    before the scope gate existed -- the more serious signal is not downgraded.
    """

    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()
    text = "an unapproved, self-consistent prompt body claiming the v3 protocol id"
    forged = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v3(),
        prompt_sha256=sha256(text.encode("utf-8")).hexdigest(),
        prompt_text_provider=lambda: text,
    )

    with pytest.raises(C1PromptBindingError):
        run_c1_pass(
            factory,
            collector,
            run_label="C1_PASS_1",
            prompt=forged,
            fixtures_dir=Path("scratch"),
            sample_vram=False,
        )

    assert factory.calls == 0


def test_canonical_v3_identity_still_passes_binding_verification() -> None:
    """v3 stays a fully reviewed, canonically bound identity -- it is only out of C1's scope.

    Exercises the module-local binding verifier directly, so this proves the binding guarantee
    without executing (or implying) a C1 pass.
    """

    assert _resolve_verified_c1_prompt_text(C1_PROMPT_V3) == c1_prompt_text_v3()
    assert _resolve_verified_c1_prompt_text(C1_PROMPT_V1) == c1_prompt_text()
    assert _resolve_verified_c1_prompt_text(C1_PROMPT_V2) == c1_prompt_text_v2()

    forged_v3 = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v3(),
        prompt_sha256=c1_prompt_sha256_v3(),
        prompt_text_provider=c1_prompt_text_v2,
    )
    with pytest.raises(C1PromptBindingError):
        _resolve_verified_c1_prompt_text(forged_v3)


def test_v3_default_is_never_silently_substituted_for_v1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Adding v3 must not change the default: a call that omits ``prompt`` still runs v1."""

    monkeypatch.chdir(tmp_path)
    factory, collector = _all_success_scripted()

    report = run_c1_pass(
        factory,
        collector,
        run_label="C1_PASS_1",
        fixtures_dir=Path("scratch"),
        sample_vram=False,
    )

    assert factory.received_prompt == c1_prompt_text()
    assert report.prompt_protocol_id == c1_prompt_protocol_id()
    assert report.prompt_sha256 == c1_prompt_sha256()


def test_v2_reports_evaluated_against_a_v3_expectation_are_rejected_not_merely_drifted() -> None:
    """A v3 expectation is refused outright, before any drift/threshold logic can run."""

    pass_1 = _pass_report(
        "C1_PASS_1",
        _succeeded_and_failed_runs(8),
        prompt_protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
    )
    repeat_1 = _pass_report(
        "C1_REPEAT_1",
        _succeeded_and_failed_runs(8),
        prompt_protocol_id=c1_prompt_protocol_id_v2(),
        prompt_sha256=c1_prompt_sha256_v2(),
    )

    with pytest.raises(C1PromptOutOfExperimentScopeError):
        evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=C1_PROMPT_V3)


def test_v3_reports_evaluated_against_the_default_v1_expectation_is_config_drift() -> None:
    pass_1 = _pass_report(
        "C1_PASS_1",
        _succeeded_and_failed_runs(8),
        prompt_protocol_id=c1_prompt_protocol_id_v3(),
        prompt_sha256=c1_prompt_sha256_v3(),
    )
    repeat_1 = _pass_report(
        "C1_REPEAT_1",
        _succeeded_and_failed_runs(8),
        prompt_protocol_id=c1_prompt_protocol_id_v3(),
        prompt_sha256=c1_prompt_sha256_v3(),
    )

    verdict = evaluate_c1_readiness(pass_1, repeat_1)  # default expectation is still v1

    assert verdict.overall == "MAPPING_NOT_READY"
    assert C1BlockingReason.CONFIG_DRIFT in verdict.blocking_reasons
    assert verdict.prompt_protocol_id == c1_prompt_protocol_id()


def test_forged_v3_expected_prompt_is_also_refused_by_readiness() -> None:
    """Whether the v3-declared expectation is canonical or forged, readiness refuses it closed."""

    forged = C1PromptProtocol(
        protocol_id=c1_prompt_protocol_id_v3(),
        prompt_sha256=c1_prompt_sha256_v3(),
        prompt_text_provider=c1_prompt_text_v2,
    )
    pass_1 = _pass_report("C1_PASS_1", _succeeded_and_failed_runs(8))
    repeat_1 = _pass_report("C1_REPEAT_1", _succeeded_and_failed_runs(8))

    with pytest.raises(C1PromptOutOfExperimentScopeError):
        evaluate_c1_readiness(pass_1, repeat_1, expected_prompt=forged)
