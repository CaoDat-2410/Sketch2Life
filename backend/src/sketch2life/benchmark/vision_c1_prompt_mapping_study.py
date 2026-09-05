"""Internal (non-CLI) P2-T3 Phase B B3 Follow-up (C1): reviewed structured-output prompt.

C1 stays inside the already-approved B1-B5 Phase B scope: B3 is defined as the "structured-
output mapping study" in ``approvals/TASK_APPROVAL.md``, and ``QwenVisionAdapter`` has always
supported an explicit ``prompt``/``prompt_builder`` constructor seam
(``qwen_vision.py:_default_prompt_builder`` returns ``""`` precisely so a caller injects the
reviewed prompt explicitly). C1's only change from B3-C0 is exercising that existing seam with
one owner-reviewed static prompt; every frozen B1/B2/B3 constraint (single candidate profile,
greedy decoding, ``max_new_tokens=512``, 120-second ``NEVER_RETRY`` timeout, lossless-fence-
unwrap-only repair, ``CLASSIFY_ONLY``-default raw handling) is unchanged here.

The reviewed prompt is a **benchmark protocol configuration artifact**, never a
``VisionProfileV2`` field: it is injected explicitly per call by whatever constructs the real
``QwenVisionAdapter`` for a C1 run, and ``qwen_vision.py``'s ``_default_prompt_builder`` is never
touched by this module, so the adapter's default construction path stays exactly as empty as it
was for B3-C0.

Prompt-binding integrity is structural, not a documentation promise: :func:`run_c1_pass` never
accepts an already-built adapter. It accepts a :data:`C1AdapterFactory` -- a
``(prompt, on_raw_output) -> VisionUnderstandingPortV2`` callable -- and is the *only* caller of
that factory, always with ``c1_prompt_text()`` and ``collector.hook`` as the arguments. There is
no parameter through which a caller can hand ``run_c1_pass`` a pre-built adapter (whatever prompt
it happens to carry) and have it labeled with C1's prompt identity; the identity on
:class:`C1PassReport` is always the identity of the exact text the factory was actually called
with. :func:`qwen_c1_adapter_factory` is the real production factory, constructing
``QwenVisionAdapter`` with the dispatched prompt injected explicitly -- ``_default_prompt_builder``
is never reached on this path.

Only :func:`c1_prompt_protocol_id`, :func:`c1_prompt_schema_target`, and
:func:`c1_prompt_sha256` are safe to place in a report, log, or evidence artifact. The prompt
body itself is returned only by :func:`c1_prompt_text`, which exists to be passed to an adapter
constructor -- never serialized, logged, or embedded in any dataclass defined below.

C1 reuses :func:`sketch2life.benchmark.vision_b3_mapping_study.run_b3_mapping_study` unchanged,
including its own default eight-fixture builder (the same eight deterministic geometric
synthetic B3 fixtures -- never B4's separate, still-unpopulated held-out set), its real
per-fixture P2-T1 gate, its one-call-per-fixture-no-retry loop, its ``CLASSIFY_ONLY``-default
raw-output collector, and its scratch cleanup. This module only adds the C1 prompt-identity
wrapper (:func:`run_c1_pass`) and the pre-registered, owner-confirmed mapping-readiness gate
(:func:`evaluate_c1_readiness`) applied to two independent passes (``C1_PASS_1``,
``C1_REPEAT_1``) -- never pooled into a combined denominator, matching this project's standing
no-pooling rule for distinct benchmark runs (B3-C0 vs. C1; ASR Round-1 vs. its repeat run).

Gate rule (owner-confirmed before any GPU execution, not derived from output after the fact):

- ``mapping-valid`` = ``SUCCEEDED`` or ``PROHIBITED_CLAIM_DETECTED`` (both prove the raw output
  mapped onto the strict V2 JSON contract; a policy block is a content decision made *after*
  successful mapping, not a mapping failure).
- Each pass independently needs ``>=7/8`` mapping-valid results.
- Systemic truncation is ``truncated_count >= 2/8`` in either pass.
- Config drift (mismatched profile/catalog/prompt identity between the two passes, or either
  pass not carrying the expected C1 protocol), an input-integrity failure, or a runtime/device
  failure in either pass blocks readiness outright, independent of the numeric threshold.
- Systemic truncation blocks readiness too, but must never be read as license to widen
  ``max_new_tokens`` or the repair/parser rule here: that needs its own separately approved
  amendment after a static token-budget analysis, never a silent in-place patch mid-run.
- Each pass must establish *exactly* eight attempted runs and exactly eight run records before
  any numeric readiness logic applies at all. A malformed/partial report (e.g. seven attempted
  runs, or ``attempted_runs`` disagreeing with the number of run records) can never pass on the
  strength of a numerator alone -- it is rejected with ``C1BlockingReason.INCOMPLETE_RUN_SET``,
  a module-local reason, never a new public V1/V2 token.

This module never runs a GPU/model/provider call, installs a dependency, touches
``.vision.env``, changes a V1/V2 public contract, changes decoding/timeout/retry/repair/parsing,
or reads/writes B4's held-out fixtures.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Literal

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3MappingStudyReport,
    B3RawOutputCollector,
    run_b3_mapping_study,
)
from sketch2life.contracts.schemas.vision import VisionErrorCode
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileIdV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)
from sketch2life.infrastructure.ai.qwen_vision import (
    QwenGenerationRunner,
    QwenVisionAdapter,
    RawOutputHook,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig

C1RunLabel = Literal["C1_PASS_1", "C1_REPEAT_1"]

C1AdapterFactory = Callable[[str, RawOutputHook], VisionUnderstandingPortV2]
"""Builds the adapter for one C1 pass from an explicit prompt and raw-output hook.

``run_c1_pass`` is the only caller of a ``C1AdapterFactory`` and always supplies
``c1_prompt_text()`` and ``collector.hook`` as its two arguments -- there is no other way to
produce a :class:`C1PassReport`. A test fake matching this signature can observe and assert the
exact prompt/hook it was dispatched, which is what ties a report's prompt identity to what the
adapter actually received rather than to an unverified caller claim.
"""

_C1_PROMPT_PROTOCOL_ID = "vision-v2-structured-output-prompt-v1"
_C1_PROMPT_SCHEMA_TARGET = "VisionUnderstandingResultV2"

_C1_PROMPT_LINES: tuple[str, ...] = (
    "Return exactly one compact JSON object and nothing else. Describe only directly "
    "observable visual content; do not infer personality, emotion, intent, "
    "symbolic/story/canonical meaning.",
    "Root keys must be exactly entities, actions, relations, themes, ambiguous_regions; "
    "all are arrays and no other keys exist.",
    "Use [] when empty. Maximum: 3 entities, 1 action, 1 relation, 1 theme, 1 ambiguous "
    "region. Prefer fewer. Text values are 1-3 lower-case English words. Every confidence "
    "is null.",
    "IDs are globally unique and match ^[a-z0-9-]+$.",
    'Every label/predicate/note is {"value":"...","language":{"status":"DECLARED",'
    '"tags":["en"]}}.',
    "Entity keys: observation_id,label,confidence.",
    "Action keys: observation_id,label,actor_ref,object_ref,confidence; refs are entity "
    "IDs or null.",
    "Relation keys: observation_id,predicate,subject_ref,object_ref,confidence; refs are "
    "distinct entity/action IDs.",
    "Theme keys: observation_id,label,evidence_refs,confidence; evidence_refs contains "
    ">=1 entity/action/relation ID.",
    "Ambiguous-region keys: observation_id,note only; it is never referenced and has no "
    "confidence/geometry.",
    "Prefer unfenced compact JSON. No prose, comments, duplicate keys, metadata, "
    "type/kind/description/bbox/geometry fields, trailing commas, or non-JSON values.",
)

_C1_PROMPT_TEXT = "\n".join(_C1_PROMPT_LINES)

_MIN_MAPPING_VALID_COUNT = 7
_SYSTEMIC_TRUNCATION_THRESHOLD = 2
_EXPECTED_ATTEMPTED_RUNS = 8

_RUNTIME_OR_DEVICE_ERROR_CODES = frozenset(
    {
        VisionErrorCode.VISION_MODEL_UNAVAILABLE.value,
        VisionErrorCode.VISION_TIMEOUT.value,
        VisionErrorCode.VISION_PROVIDER_FAILURE.value,
    }
)
_INPUT_INTEGRITY_ERROR_DETAILS = frozenset(
    {
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE.value,
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH.value,
    }
)

_DEFAULT_C1_FIXTURES_DIR: dict[C1RunLabel, Path] = {
    "C1_PASS_1": Path("data/runtime/vision-c1-pass-1"),
    "C1_REPEAT_1": Path("data/runtime/vision-c1-repeat-1"),
}


def c1_prompt_protocol_id() -> str:
    """Safe identifier: fine for any report, log, or evidence artifact."""

    return _C1_PROMPT_PROTOCOL_ID


def c1_prompt_schema_target() -> str:
    """The V2 result contract this prompt is written against. Safe to persist."""

    return _C1_PROMPT_SCHEMA_TARGET


def c1_prompt_sha256() -> str:
    """SHA-256 of the canonical prompt text. Safe to persist; the text itself is not."""

    return sha256(_C1_PROMPT_TEXT.encode("utf-8")).hexdigest()


def c1_prompt_text() -> str:
    """The reviewed static C1 prompt body, for adapter-construction injection only.

    This is the one function in this module that returns the prompt body. Callers must pass it
    straight into ``QwenVisionAdapter(..., prompt=c1_prompt_text())`` (or an equivalent fake for
    tests) and must never place its return value into a dataclass, report, or log defined here.
    """

    return _C1_PROMPT_TEXT


def qwen_c1_adapter_factory(
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    *,
    generation_runner: QwenGenerationRunner | None = None,
) -> C1AdapterFactory:
    """The real production :data:`C1AdapterFactory` for a Lightning C1 run.

    Returns a closure matching ``C1AdapterFactory``: called by ``run_c1_pass`` with the exact
    ``c1_prompt_text()`` and ``collector.hook``, it constructs a fresh ``QwenVisionAdapter`` with
    ``prompt``/``on_raw_output`` set to exactly those two values. ``QwenVisionAdapter``'s own
    default (empty) ``_default_prompt_builder`` is never reached through this factory --
    ``prompt=`` is always supplied explicitly, once per call. ``generation_runner`` exists only so
    tests can inject a fake generation seam without a GPU; a real Lightning run omits it and gets
    the adapter's own default killable-subprocess runner.
    """

    def factory(prompt: str, on_raw_output: RawOutputHook) -> VisionUnderstandingPortV2:
        return QwenVisionAdapter(
            runtime_config,
            content_policy=content_policy,
            prompt=prompt,
            generation_runner=generation_runner,
            on_raw_output=on_raw_output,
        )

    return factory


@dataclass(frozen=True, slots=True)
class C1PassReport:
    """One C1 pass's safe report: prompt identity plus the reused B3 mapping report.

    Never carries the prompt body, raw model output, or a local path -- only what
    :class:`~sketch2life.benchmark.vision_b3_mapping_study.B3MappingStudyReport` already
    guarantees, plus the C1 prompt's safe identifiers.
    """

    run_label: C1RunLabel
    prompt_protocol_id: str
    prompt_sha256: str
    mapping: B3MappingStudyReport


def run_c1_pass(
    adapter_factory: C1AdapterFactory,
    collector: B3RawOutputCollector,
    *,
    run_label: C1RunLabel,
    profile_id: VisionProfileIdV2 = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
    sample_vram: bool = True,
    fixtures_dir: Path | None = None,
) -> C1PassReport:
    """Execute one C1 pass: the existing eight B3 fixtures, one adapter call each, no retry.

    ``adapter_factory`` is called exactly once, here, with ``c1_prompt_text()`` and
    ``collector.hook`` -- never with anything else -- to build the adapter that
    ``run_b3_mapping_study`` then drives. There is no way to obtain a :class:`C1PassReport` from
    an already-built adapter: the factory is the only construction seam, so the prompt identity
    stamped on the returned report always matches what the factory actually received, not an
    unverified caller claim. This function never touches ``qwen_vision.py``'s default (empty)
    prompt builder itself -- see :func:`qwen_c1_adapter_factory` for the real production factory.

    Delegates entirely to ``run_b3_mapping_study`` -- including that function's own default
    eight-fixture builder, real P2-T1 gate, one-call-per-fixture-no-retry loop, and scratch
    cleanup -- and adds only the C1 prompt-dispatch/identity wrapper and a distinct default
    scratch directory per ``run_label`` so ``C1_PASS_1`` and ``C1_REPEAT_1`` never collide when
    run in the same working directory.
    """

    adapter = adapter_factory(c1_prompt_text(), collector.hook)
    resolved_fixtures_dir = fixtures_dir or _DEFAULT_C1_FIXTURES_DIR[run_label]
    mapping = run_b3_mapping_study(
        adapter,
        collector,
        profile_id=profile_id,
        correlation_id_prefix=f"vision-{run_label.lower().replace('_', '-')}",
        sample_vram=sample_vram,
        fixtures_dir=resolved_fixtures_dir,
    )
    return C1PassReport(
        run_label=run_label,
        prompt_protocol_id=c1_prompt_protocol_id(),
        prompt_sha256=c1_prompt_sha256(),
        mapping=mapping,
    )


class C1BlockingReason(StrEnum):
    """Closed set of reasons :func:`evaluate_c1_readiness` may cite for a non-ready verdict."""

    MAPPING_VALID_BELOW_THRESHOLD = "MAPPING_VALID_BELOW_THRESHOLD"
    SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS = (
        "SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS"
    )
    CONFIG_DRIFT = "CONFIG_DRIFT"
    INPUT_INTEGRITY_FAILURE = "INPUT_INTEGRITY_FAILURE"
    RUNTIME_OR_DEVICE_FAILURE = "RUNTIME_OR_DEVICE_FAILURE"
    INCOMPLETE_RUN_SET = "INCOMPLETE_RUN_SET"


@dataclass(frozen=True, slots=True)
class C1PassEvaluation:
    """Derived, safe-only figures for one pass; never carries raw text or a path.

    ``is_complete`` is ``True`` only when both ``attempted_runs`` and ``run_record_count`` equal
    exactly eight; ``mapping_valid_ok`` is structurally forced ``False`` whenever the pass is
    incomplete, so a malformed report (e.g. a partial 7/7 run, or ``attempted_runs`` disagreeing
    with the number of run records) can never satisfy the numeric threshold on the strength of a
    numerator alone.
    """

    run_label: C1RunLabel
    attempted_runs: int
    run_record_count: int
    is_complete: bool
    mapping_valid_count: int
    truncated_count: int
    mapping_valid_ok: bool
    systemic_truncation: bool


@dataclass(frozen=True, slots=True)
class C1ReadinessVerdict:
    """The pre-registered C1 mapping-readiness gate applied to two independent passes.

    Never pools ``pass_1``/``repeat_1`` into a combined denominator: each must independently
    satisfy the mapping-valid threshold, matching the project's standing no-pooling rule for
    distinct benchmark runs.
    """

    prompt_protocol_id: str
    prompt_sha256: str
    pass_1: C1PassEvaluation
    repeat_1: C1PassEvaluation
    overall: Literal["MAPPING_READY", "MAPPING_NOT_READY"]
    blocking_reasons: tuple[C1BlockingReason, ...]


def _mapping_valid_count(report: B3MappingStudyReport) -> int:
    """``SUCCEEDED`` or ``PROHIBITED_CLAIM_DETECTED`` both count as mapping-valid for C1.

    Both outcomes prove the model's raw output mapped onto the strict V2 JSON contract; a
    policy block is a content decision made *after* successful mapping, not a mapping failure.
    """

    return sum(
        1
        for run in report.runs
        if run.status == "SUCCEEDED"
        or run.error_code == VisionErrorCode.PROHIBITED_CLAIM_DETECTED.value
    )


def _has_runtime_or_device_failure(report: B3MappingStudyReport) -> bool:
    return any(run.error_code in _RUNTIME_OR_DEVICE_ERROR_CODES for run in report.runs)


def _has_input_integrity_failure(report: B3MappingStudyReport) -> bool:
    return any(run.error_detail in _INPUT_INTEGRITY_ERROR_DETAILS for run in report.runs)


def _evaluate_pass(pass_report: C1PassReport) -> C1PassEvaluation:
    mapping = pass_report.mapping
    valid_count = _mapping_valid_count(mapping)
    run_record_count = len(mapping.runs)
    is_complete = (
        mapping.attempted_runs == _EXPECTED_ATTEMPTED_RUNS
        and run_record_count == _EXPECTED_ATTEMPTED_RUNS
    )
    return C1PassEvaluation(
        run_label=pass_report.run_label,
        attempted_runs=mapping.attempted_runs,
        run_record_count=run_record_count,
        is_complete=is_complete,
        mapping_valid_count=valid_count,
        truncated_count=mapping.truncated_count,
        mapping_valid_ok=is_complete and valid_count >= _MIN_MAPPING_VALID_COUNT,
        systemic_truncation=mapping.truncated_count >= _SYSTEMIC_TRUNCATION_THRESHOLD,
    )


def evaluate_c1_readiness(pass_1: C1PassReport, repeat_1: C1PassReport) -> C1ReadinessVerdict:
    """Apply the pre-registered C1 mapping-readiness gate to two independent passes.

    See the module docstring for the full gate rule. This function does not detect whether raw
    output was ever persisted -- that guarantee is structural, enforced by
    ``B3RawOutputCollector``/``run_b3_mapping_study`` and covered by their own tests, not
    re-derived from a report here.
    """

    if pass_1.run_label == repeat_1.run_label:
        raise ValueError("pass_1 and repeat_1 must carry distinct run labels")

    expected_catalog_hash = vision_profile_catalog_hash_v2(vision_profile_catalog_v2())
    expected_profile_id = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1.value
    expected_prompt_sha256 = c1_prompt_sha256()
    expected_protocol_id = c1_prompt_protocol_id()

    config_drift = (
        pass_1.mapping.profile_id != expected_profile_id
        or repeat_1.mapping.profile_id != expected_profile_id
        or pass_1.mapping.profile_catalog_hash != expected_catalog_hash
        or repeat_1.mapping.profile_catalog_hash != expected_catalog_hash
        or pass_1.prompt_protocol_id != expected_protocol_id
        or repeat_1.prompt_protocol_id != expected_protocol_id
        or pass_1.prompt_sha256 != expected_prompt_sha256
        or repeat_1.prompt_sha256 != expected_prompt_sha256
    )
    integrity_failure = _has_input_integrity_failure(
        pass_1.mapping
    ) or _has_input_integrity_failure(repeat_1.mapping)
    runtime_failure = _has_runtime_or_device_failure(
        pass_1.mapping
    ) or _has_runtime_or_device_failure(repeat_1.mapping)

    pass_1_evaluation = _evaluate_pass(pass_1)
    repeat_1_evaluation = _evaluate_pass(repeat_1)

    incomplete = not pass_1_evaluation.is_complete or not repeat_1_evaluation.is_complete
    mapping_valid_ok = pass_1_evaluation.mapping_valid_ok and repeat_1_evaluation.mapping_valid_ok
    systemic_truncation = (
        pass_1_evaluation.systemic_truncation or repeat_1_evaluation.systemic_truncation
    )

    blocking: list[C1BlockingReason] = []
    if config_drift:
        blocking.append(C1BlockingReason.CONFIG_DRIFT)
    if integrity_failure:
        blocking.append(C1BlockingReason.INPUT_INTEGRITY_FAILURE)
    if runtime_failure:
        blocking.append(C1BlockingReason.RUNTIME_OR_DEVICE_FAILURE)
    if incomplete:
        # A malformed/partial run set makes the numeric threshold meaningless -- cite this
        # reason instead of (never in addition to) MAPPING_VALID_BELOW_THRESHOLD below.
        blocking.append(C1BlockingReason.INCOMPLETE_RUN_SET)
    if systemic_truncation:
        blocking.append(C1BlockingReason.SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS)
    if not incomplete and not mapping_valid_ok:
        blocking.append(C1BlockingReason.MAPPING_VALID_BELOW_THRESHOLD)

    overall: Literal["MAPPING_READY", "MAPPING_NOT_READY"] = (
        "MAPPING_NOT_READY" if blocking else "MAPPING_READY"
    )

    return C1ReadinessVerdict(
        prompt_protocol_id=expected_protocol_id,
        prompt_sha256=expected_prompt_sha256,
        pass_1=pass_1_evaluation,
        repeat_1=repeat_1_evaluation,
        overall=overall,
        blocking_reasons=tuple(blocking),
    )


__all__ = [
    "C1AdapterFactory",
    "C1BlockingReason",
    "C1PassEvaluation",
    "C1PassReport",
    "C1ReadinessVerdict",
    "C1RunLabel",
    "c1_prompt_protocol_id",
    "c1_prompt_schema_target",
    "c1_prompt_sha256",
    "c1_prompt_text",
    "evaluate_c1_readiness",
    "qwen_c1_adapter_factory",
    "run_c1_pass",
]
