"""Internal, non-CLI B4 Step 2 controlled live diagnostic runner.

This is the local implementation of Step 2 in the owner's three-step B4 quality-diagnostic plan.
It exists to answer *why* the completed B4 run matched nothing, and it is deliberately **not** a
B4 quality pass:

- It never calls, wraps, replaces, or re-scores :func:`~sketch2life.benchmark.
  vision_b4_quality_benchmark.run_b4_quality_pass`, and it cannot produce a
  ``B4_PASS_1``/``B4_REPEAT_1`` label -- :data:`_DIAGNOSTIC_RUN_LABEL` is a fixed module constant,
  not a parameter, so no caller can relabel a diagnostic as a benchmark pass, repeat, or new
  held-out quality result.
- It reuses the frozen B4 package exactly as-is: the same eight owner-approved held-out fixtures,
  the same manifest/ground-truth/matching-rule hash gates, the same real P2-T1 provenance gate,
  the same C1-v2 prompt identity check, the same one-call-per-fixture-no-retry loop, and the same
  frozen ``QWEN3_VL_8B_INSTRUCT_BF16_V1`` profile. Nothing here changes the scorer, matching rule,
  ground truth, fixture images, taxonomy, prompt text/hash, decode settings, token budget,
  timeout, parser, repair rule, or the previously recorded B4 result.

Raw-output handling is the one capability this module adds over ``run_b4_quality_pass``, and it is
gated closed:

- A caller must inject an explicit :data:`B4DiagnosticReviewGate`. There is no default gate, no
  ``input()``, and no interactive fallback; a caller that omits it fails with
  :class:`B4DiagnosticReviewGateRequiredError` before the fixture package is read, before the
  adapter factory is called, and therefore before any provider action.
- Raw provider text is written to a guarded scratch file that exists **only** while the injected
  gate runs, and is removed in a ``finally`` that also runs when the gate, the adapter, or the
  classifier raises. The scratch directory itself is removed in the runner's own ``finally``.
- The gate receives the temporary :class:`~pathlib.Path` in memory so the owner can inspect the
  text out-of-band. That path -- like the raw text, the prompt body, predicted values, and
  ground-truth values -- never reaches an exception message, this module's report, a log, or any
  serialized object.
- The real ``QwenVisionAdapter`` deliberately runs ``on_raw_output`` under
  ``contextlib.suppress(Exception)`` (its own fail-safe: a diagnostic hook must never turn a
  successful understanding call into an uncaught exception), so
  :class:`B4EphemeralReviewCollector` ``.hook`` itself never raises -- capture-write, review-gate,
  and classification failures are each caught inside ``.hook`` and recorded only as a closed,
  module-private :class:`_HookFailureKind` token, never the exception object, never
  raw/prompt/predicted/path text. ``run_b4_step2_diagnostic`` reads that token immediately after
  ``adapter.understand`` returns -- outside the adapter's suppression boundary, and with no
  exception in flight -- and raises the corresponding sanitized error from there:
  :class:`B4DiagnosticReviewGateError` for a review-gate failure (with both ``__cause__`` and
  ``__context__`` ``None``, since the original exception was already fully handled and cleared
  inside ``.hook`` before this raise), or :class:`B4DiagnosticRawOutputNotReviewedError` for a
  capture-write or classification failure.

Only closed, safe aggregate tokens and counts persist: :class:`B4DiagnosticCategory` members plus
integer counts, the already-approved raw-output buckets, typed failure details, and the identity
hashes the B4 report already carries. A category states only that the frozen matching rule found
no full match for an item -- never what the item said, never a normalized form of it, never a
semantic guess, and never a claim that a non-match is or is not semantically equivalent.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3RawOutputClassification,
    classify_raw_output,
)
from sketch2life.benchmark.vision_b4_quality_benchmark import (
    _COLLECTIONS,
    _DEFAULT_FIXTURE_ROOT,
    B4CollectionScore,
    MediaValidationFactory,
    _classification_required,
    _load_fixture_package,
    _real_p2t1_pass,
    _relative_artifact_ref,
    _require_safe_runtime_directory,
    _score_success,
    _verify_prompt,
    _write_companion_audio,
)
from sketch2life.benchmark.vision_c1_prompt_mapping_study import (
    C1_PROMPT_V2,
    C1AdapterFactory,
    C1PromptProtocol,
)
from sketch2life.contracts.schemas.vision import VisionImageReferenceV1
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)

type B4DiagnosticRunLabel = Literal["B4_STEP2_DIAGNOSTIC_1"]

_DIAGNOSTIC_RUN_LABEL: B4DiagnosticRunLabel = "B4_STEP2_DIAGNOSTIC_1"
"""Fixed, non-parameterizable label. A diagnostic can never claim a B4 pass/repeat identity."""

_DEFAULT_RUNTIME_DIR = Path("data/runtime/vision-b4-step2-diagnostic")
_CAPTURE_DIR_NAME = "raw-review"
_CAPTURE_FILE_NAME = "b4-step2-raw-review.txt"
_COMPANION_AUDIO_NAME = "b4-step2-companion.wav"

B4DiagnosticReviewGate = Callable[[Path], None]
"""Owner-injected ephemeral raw-output review gate.

Called once per raw-producing fixture with the temporary capture path, while -- and only while --
that file exists. Whatever the gate does with the text is the owner's out-of-band decision; this
module never reads, returns, logs, or reports it, and the path never leaves the gate call.
"""


class B4DiagnosticReviewGateRequiredError(ValueError):
    """No explicit review gate was injected, so ephemeral capture cannot be authorized."""


class B4DiagnosticReviewGateError(RuntimeError):
    """The injected review gate raised for one fixture.

    Raised by :func:`run_b4_step2_diagnostic` itself, immediately after ``adapter.understand``
    returns -- never from inside :meth:`B4EphemeralReviewCollector.hook`, and never while the
    gate's original exception is still being handled, since that exception was already fully
    caught and discarded inside ``.hook`` (which never re-raises: the real ``QwenVisionAdapter``
    runs ``on_raw_output`` under ``contextlib.suppress(Exception)``, so a hook that raised would
    have that failure silently swallowed and never reach this diagnostic at all). This is what
    keeps both ``__cause__`` and ``__context__`` ``None`` here, and it is also why the message
    below carries only the closed ``fixture_id`` -- never raw text, prompt text, predicted text,
    ground-truth text, or the ephemeral capture path.
    """


class B4DiagnosticRawOutputNotReviewedError(RuntimeError):
    """A raw-producing typed result was not successfully reviewed for one fixture.

    Covers every closed reason a fixture's raw output ends up unreviewed: the diagnostic hook was
    never wired as ``on_raw_output`` at all, ephemeral capture-writing failed, or in-memory
    classification failed after a successful review-gate call. A review-gate failure itself is
    reported separately as :class:`B4DiagnosticReviewGateError`. Mirrors ``run_b4_quality_pass``'s
    own fail-closed guard: otherwise the diagnostic's counts could silently understate what the
    model actually produced.
    """


class B4DiagnosticCategory(StrEnum):
    """The closed set of safe diagnostic tokens this module may emit.

    Each token reports only the outcome of the frozen ``vision-b4-matching-rule-v1`` comparison.
    None of them describes, normalizes, paraphrases, or semantically judges any value, and none
    of them asserts that an unmatched item is (or is not) semantically equivalent to ground truth.
    """

    EXPECTED_COLLECTION_PREDICTED_EMPTY = "EXPECTED_COLLECTION_PREDICTED_EMPTY"
    ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH = "ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH"
    ACTION_NO_FULL_LABEL_OR_ENDPOINT_MATCH = "ACTION_NO_FULL_LABEL_OR_ENDPOINT_MATCH"
    RELATION_NO_FULL_PREDICATE_OR_ENDPOINT_MATCH = "RELATION_NO_FULL_PREDICATE_OR_ENDPOINT_MATCH"
    THEME_NO_FULL_LABEL_OR_EVIDENCE_REF_MATCH = "THEME_NO_FULL_LABEL_OR_EVIDENCE_REF_MATCH"


_NO_MATCH_CATEGORY_BY_COLLECTION: Mapping[str, B4DiagnosticCategory] = {
    "entities": B4DiagnosticCategory.ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH,
    "actions": B4DiagnosticCategory.ACTION_NO_FULL_LABEL_OR_ENDPOINT_MATCH,
    "relations": B4DiagnosticCategory.RELATION_NO_FULL_PREDICATE_OR_ENDPOINT_MATCH,
    "themes": B4DiagnosticCategory.THEME_NO_FULL_LABEL_OR_EVIDENCE_REF_MATCH,
}
"""``ambiguous_regions`` is deliberately absent: matching-rule rule 9 reports count/rate only for
that collection, so this module never emits a per-item match verdict for it."""


@dataclass(frozen=True, slots=True)
class B4DiagnosticFixtureResult:
    """One fixture's typed outcome plus safe category counts; never candidates or raw text."""

    fixture_id: str
    status: str
    error_code: str | None
    error_detail: str | None
    attempt_number: int
    repair_attempted: bool
    raw_output_reviewed: bool
    fenced: bool | None
    truncated: bool | None
    extra_key: bool | None
    invalid_enum: bool | None
    category_counts: Mapping[B4DiagnosticCategory, int]


@dataclass(frozen=True, slots=True)
class B4DiagnosticReport:
    """Evidence-safe Step 2 diagnostic result.

    ``run_label`` is always :data:`_DIAGNOSTIC_RUN_LABEL` and ``quality_score_authority`` is
    always ``NONE_DIAGNOSTIC_ONLY``: this report never supersedes, rescores, or pools with the
    recorded B4 quality result.
    """

    run_label: B4DiagnosticRunLabel
    quality_score_authority: Literal["NONE_DIAGNOSTIC_ONLY"]
    manifest_version: str
    ground_truth_sha256: str
    matching_rule_id: str
    matching_rule_sha256: str
    prompt_protocol_id: str
    prompt_sha256: str
    profile_id: str
    profile_catalog_hash: str
    raw_output_mode: Literal["EPHEMERAL_REVIEW_GATE"]
    attempted_runs: int
    schema_valid_count: int
    reviewed_raw_output_count: int
    typed_failure_counts: Mapping[str, int]
    fenced_count: int
    truncated_count: int
    extra_key_count: int
    invalid_enum_count: int
    aggregate_category_counts: Mapping[B4DiagnosticCategory, int]
    runs: tuple[B4DiagnosticFixtureResult, ...]


class _HookFailureKind(StrEnum):
    """Closed, module-private safe state for a ``.hook`` call that could not complete review.

    Never exposed outside this module and never carries the causing exception, raw output, prompt
    text, predicted text, or the capture path -- only which closed stage failed.
    """

    REVIEW_GATE_FAILED = "REVIEW_GATE_FAILED"
    CAPTURE_OR_CLASSIFICATION_FAILED = "CAPTURE_OR_CLASSIFICATION_FAILED"


class B4EphemeralReviewCollector:
    """Owns the adapter's ``on_raw_output`` seam for one Step 2 diagnostic run.

    B4-local by design: it does not change :class:`~sketch2life.benchmark.
    vision_b3_mapping_study.B3RawOutputCollector`'s semantics for B3/C1, and reuses only that
    module's pure, in-memory :func:`~sketch2life.benchmark.vision_b3_mapping_study.
    classify_raw_output`.

    ``.hook`` itself never raises, matching the real ``QwenVisionAdapter``'s own
    ``contextlib.suppress(Exception)`` around ``on_raw_output`` -- if it did raise, that adapter
    would silently swallow the failure and this diagnostic would never learn a review was missed.
    Every internal stage (capture-write, the injected gate, in-memory classification) is caught
    independently and recorded only as a closed :class:`_HookFailureKind` token via
    :meth:`take_failure`, which :func:`run_b4_step2_diagnostic` reads immediately after
    ``adapter.understand`` returns -- outside any adapter-level suppression, and with no exception
    in flight -- to raise the sanitized, fixture-scoped error itself.
    """

    def __init__(self, review_gate: B4DiagnosticReviewGate, capture_dir: Path) -> None:
        _require_safe_runtime_directory(capture_dir)
        self._review_gate = review_gate
        self._capture_dir = capture_dir
        self._latest: B3RawOutputClassification | None = None
        self._failure: _HookFailureKind | None = None
        self.reviewed_count = 0

    def hook(self, raw_output: str) -> None:
        """Capture, review, delete, then classify -- in that order, never raising.

        The capture file exists only for the duration of the gate call: it is unlinked
        immediately after the gate call returns or raises, before classification is attempted.
        """

        self._latest = None
        self._failure = None
        capture_path = self._capture_dir / _CAPTURE_FILE_NAME
        try:
            self._capture_dir.mkdir(parents=True, exist_ok=True)
            capture_path.write_text(raw_output, encoding="utf-8")
        except Exception:
            self._failure = _HookFailureKind.CAPTURE_OR_CLASSIFICATION_FAILED
            capture_path.unlink(missing_ok=True)
            return

        try:
            self._review_gate(capture_path)
        except Exception:
            self._failure = _HookFailureKind.REVIEW_GATE_FAILED
            capture_path.unlink(missing_ok=True)
            return
        capture_path.unlink(missing_ok=True)

        try:
            self._latest = classify_raw_output(raw_output)
        except Exception:
            self._latest = None
            self._failure = _HookFailureKind.CAPTURE_OR_CLASSIFICATION_FAILED
            return
        self.reviewed_count += 1

    def take_latest(self) -> B3RawOutputClassification | None:
        latest = self._latest
        self._latest = None
        return latest

    def take_failure(self) -> _HookFailureKind | None:
        failure = self._failure
        self._failure = None
        return failure

    def cleanup(self) -> None:
        shutil.rmtree(self._capture_dir, ignore_errors=True)


def _diagnostic_categories(
    scores: Mapping[str, B4CollectionScore],
) -> Mapping[B4DiagnosticCategory, int]:
    """Translate the frozen scorer's own counts into closed tokens; never re-score anything."""

    counts: dict[B4DiagnosticCategory, int] = {}
    for collection in _COLLECTIONS:
        score = scores[collection]
        if score.ground_truth_count and not score.predicted_count:
            key = B4DiagnosticCategory.EXPECTED_COLLECTION_PREDICTED_EMPTY
            counts[key] = counts.get(key, 0) + 1
        category = _NO_MATCH_CATEGORY_BY_COLLECTION.get(collection)
        unmatched_predictions = score.predicted_count - score.matched_count
        if category is not None and unmatched_predictions > 0:
            counts[category] = counts.get(category, 0) + unmatched_predictions
    return counts


def _merge_category_counts(
    aggregate: dict[B4DiagnosticCategory, int], addition: Mapping[B4DiagnosticCategory, int]
) -> None:
    for category, count in addition.items():
        aggregate[category] = aggregate.get(category, 0) + count


def run_b4_step2_diagnostic(
    adapter_factory: C1AdapterFactory,
    *,
    review_gate: B4DiagnosticReviewGate | None = None,
    prompt: C1PromptProtocol = C1_PROMPT_V2,
    fixture_root: Path = _DEFAULT_FIXTURE_ROOT,
    runtime_dir: Path = _DEFAULT_RUNTIME_DIR,
    validate_media: MediaValidationFactory = _real_p2t1_pass,
) -> B4DiagnosticReport:
    """Run one Step 2 diagnostic: eight B4 fixtures, one adapter call each, no retry.

    Fails closed -- before the fixture package is read, before ``adapter_factory`` is called, and
    therefore before any provider action -- when ``review_gate`` is omitted, and before the
    factory when the prompt identity, the package hashes, the scratch layout, or a fixture's real
    P2-T1 ``PASS`` does not hold. Cleans its own scratch directory (and the capture directory
    inside it) in a ``finally`` covering every one of those paths as well as adapter, gate, and
    classifier exceptions.

    Running this function locally does not authorize a model call: a real Lightning invocation
    remains a separate owner gate, exactly as it is for ``run_b4_quality_pass``.
    """

    if review_gate is None:
        raise B4DiagnosticReviewGateRequiredError(
            "B4 Step 2 ephemeral raw-output review requires an explicitly injected review gate; "
            "there is no default, interactive, or implicit capture mode"
        )
    prompt_text = _verify_prompt(prompt)
    manifest_version, gt_hash, rule_id, rule_hash, fixtures = _load_fixture_package(fixture_root)
    _require_safe_runtime_directory(runtime_dir)
    collector = B4EphemeralReviewCollector(review_gate, runtime_dir / _CAPTURE_DIR_NAME)

    try:
        audio_path = runtime_dir / _COMPANION_AUDIO_NAME
        _write_companion_audio(audio_path)
        provenances = {
            fixture.fixture_id: validate_media(fixture.fixture_id, fixture.image_path, audio_path)
            for fixture in fixtures
        }
        adapter: VisionUnderstandingPortV2 = adapter_factory(prompt_text, collector.hook)
        runs: list[B4DiagnosticFixtureResult] = []
        typed_failures: dict[str, int] = {}
        aggregate_categories: dict[B4DiagnosticCategory, int] = {}
        schema_valid_count = 0
        fenced_count = truncated_count = extra_key_count = invalid_enum_count = 0
        for fixture in fixtures:
            request = VisionUnderstandingRequestV2(
                correlation_id=f"vision-b4-step2-diagnostic-{fixture.fixture_id}",
                source_image_ref=VisionImageReferenceV1(
                    artifact_ref=_relative_artifact_ref(fixture.image_path),
                    sha256=fixture.image_sha256,
                ),
                media_validation=provenances[fixture.fixture_id],
                requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
            )
            collector.take_latest()
            collector.take_failure()
            result = adapter.understand(request)
            classification = collector.take_latest()
            failure = collector.take_failure()
            # Read *after* ``adapter.understand`` has returned: the real ``QwenVisionAdapter``
            # already ran ``collector.hook`` to completion (under its own
            # ``contextlib.suppress(Exception)``, which is a no-op here because ``.hook`` never
            # raises), so no exception is in flight in this frame -- a fresh raise below is
            # guaranteed ``__cause__``/``__context__`` ``None``.
            if failure is _HookFailureKind.REVIEW_GATE_FAILED:
                raise B4DiagnosticReviewGateError(
                    f"{fixture.fixture_id}: the injected B4 Step 2 review gate raised; this "
                    "error carries no raw output, prompt text, predicted text, or capture path"
                )
            if failure is _HookFailureKind.CAPTURE_OR_CLASSIFICATION_FAILED:
                raise B4DiagnosticRawOutputNotReviewedError(
                    f"{fixture.fixture_id}: ephemeral capture or in-memory classification failed "
                    "before review could complete"
                )
            if classification is None and _classification_required(result):
                raise B4DiagnosticRawOutputNotReviewedError(
                    f"{fixture.fixture_id}: a raw-producing typed result had no safe "
                    "classification"
                )
            if isinstance(result, VisionUnderstandingSuccessV2):
                error_code = error_detail = None
                categories = _diagnostic_categories(_score_success(result, fixture.ground_truth))
                _merge_category_counts(aggregate_categories, categories)
                schema_valid_count += 1
            else:
                assert isinstance(result, VisionUnderstandingFailureV2)
                error_code = result.error_code.value
                error_detail = result.error_detail.value
                typed_failures[error_detail] = typed_failures.get(error_detail, 0) + 1
                categories = {}
            if classification is not None:
                fenced_count += int(classification.fenced)
                truncated_count += int(classification.truncated)
                extra_key_count += int(classification.extra_key)
                invalid_enum_count += int(classification.invalid_enum)
            runs.append(
                B4DiagnosticFixtureResult(
                    fixture_id=fixture.fixture_id,
                    status=result.status,
                    error_code=error_code,
                    error_detail=error_detail,
                    attempt_number=result.attempt_number,
                    repair_attempted=result.repair_attempted,
                    raw_output_reviewed=classification is not None,
                    fenced=classification.fenced if classification is not None else None,
                    truncated=classification.truncated if classification is not None else None,
                    extra_key=classification.extra_key if classification is not None else None,
                    invalid_enum=(
                        classification.invalid_enum if classification is not None else None
                    ),
                    category_counts=categories,
                )
            )
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)
        collector.cleanup()

    catalog = vision_profile_catalog_v2()
    return B4DiagnosticReport(
        run_label=_DIAGNOSTIC_RUN_LABEL,
        quality_score_authority="NONE_DIAGNOSTIC_ONLY",
        manifest_version=manifest_version,
        ground_truth_sha256=gt_hash,
        matching_rule_id=rule_id,
        matching_rule_sha256=rule_hash,
        prompt_protocol_id=prompt.protocol_id,
        prompt_sha256=prompt.prompt_sha256,
        profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1.value,
        profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
        raw_output_mode="EPHEMERAL_REVIEW_GATE",
        attempted_runs=len(runs),
        schema_valid_count=schema_valid_count,
        reviewed_raw_output_count=collector.reviewed_count,
        typed_failure_counts=dict(typed_failures),
        fenced_count=fenced_count,
        truncated_count=truncated_count,
        extra_key_count=extra_key_count,
        invalid_enum_count=invalid_enum_count,
        aggregate_category_counts=dict(aggregate_categories),
        runs=tuple(runs),
    )


__all__ = [
    "B4DiagnosticCategory",
    "B4DiagnosticFixtureResult",
    "B4DiagnosticRawOutputNotReviewedError",
    "B4DiagnosticReport",
    "B4DiagnosticReviewGate",
    "B4DiagnosticReviewGateError",
    "B4DiagnosticReviewGateRequiredError",
    "B4EphemeralReviewCollector",
    "run_b4_step2_diagnostic",
]
