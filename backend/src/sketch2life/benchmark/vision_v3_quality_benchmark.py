"""Local-only Phase 8 prompt-v3 held-out quality runner and scorer.

This module is a separate experiment boundary from the C1 mapping study, the immutable B4
benchmark, and the prompt-v3 mapping-validation runner.  It has its own fixture identity, run
labels, scoring types, and quality verdict vocabulary.  It never reads a prior benchmark report
and it cannot produce a mapping-readiness verdict.

The tracked Phase 8 package is intentionally still review-gated.  The package loader therefore
requires the owner-approved manifest state before an adapter factory can be constructed.  D-5
and D-6 remain explicit caller-supplied decisions; unresolved values fail closed instead of
receiving defaults.  D-7 is fixed to ``CLASSIFY_ONLY`` at this boundary: neither a decision value
nor a B3 collector configured for ``EPHEMERAL_CAPTURE`` can override it.  The adapter is injected
at the boundary, so importing or testing this module does not import a model provider, load
weights, use CUDA, or contact a provider.  The execution entry point accepts only the concrete
static local-fake factory defined below; a model/provider factory cannot satisfy that boundary.  A
future model run, if separately approved, must be implemented in a different execution module and
cannot be enabled by a caller flag here.

Only safe identity values, closed outcome tokens, counts, and aggregate scores appear in the
report dataclasses.  Prompt text, raw provider output, predicted text, ground-truth text, local
paths, credentials, and endpoints never enter a report or a persisted serializer.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from math import sin
from pathlib import Path
from struct import pack, unpack
from typing import Any, Literal
from wave import open as wave_open

from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.benchmark import vision_v3_quality_fixtures as _fixture_authoring
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3RawOutputClassification,
    B3RawOutputCollector,
    B3RawOutputMode,
)
from sketch2life.benchmark.vision_c1_prompt_mapping_study import (
    C1_PROMPT_V3,
    c1_prompt_schema_target,
)
from sketch2life.contracts.schemas.vision import (
    ActionCandidateV1,
    AmbiguousRegionCandidateV1,
    EntityCandidateV1,
    RelationCandidateV1,
    ThemeCandidateV1,
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)
from sketch2life.domain.understanding.media_quality import MediaDecision
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector

_COLLECTIONS = (
    "entities",
    "actions",
    "relations",
    "themes",
    "ambiguous_regions",
)
_FIXTURE_COUNT = 8
_EXPECTED_DIMENSION = 256
_EXPECTED_CONTRACT_NAME = "VisionV3QualityFixtureManifestV1"
_EXPECTED_MANIFEST_VERSION = "vision-v3-quality-manifest-v1"
_EXPECTED_GROUND_TRUTH_VERSION = "vision-v3-quality-ground-truth-v1"
_EXPECTED_STATUS = "OWNER_REVIEW_APPROVED"
_EXPECTED_PURPOSE = "QUALITY_BENCHMARK"
_EXPECTED_SCOPE = "S3_FULL_SCORING_WITH_DIAGNOSTIC_SPLIT"
_EXPECTED_RULE_ID = "vision-v3-quality-matching-rule-v1"
_EXPECTED_RECIPE_REF = "backend/src/sketch2life/benchmark/vision_v3_quality_fixtures.py"
_EXPECTED_PROMPT_PROTOCOL_ID = "vision-v2-structured-output-prompt-v3"
_EXPECTED_PROMPT_SHA256 = "bf8b9cab5df6b2551e627cf0bb92fe977e0dc182fdaae5f3c5face5bc34615f3"
_EXPECTED_SCHEMA_TARGET = "VisionUnderstandingResultV2"
_DEFAULT_FIXTURE_ROOT = Path(
    "features/FEAT-003-multimodal-understanding/fixtures/vision-v3-quality"
)
_DEFAULT_RUNTIME_DIRS: Mapping[str, Path] = {
    "V3_QUALITY_PASS_1": Path("data/runtime/vision-v3-quality-pass-1"),
    "V3_QUALITY_REPEAT_1": Path("data/runtime/vision-v3-quality-repeat-1"),
}
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_GROUND_TRUTH_ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
_WINDOWS_DRIVE_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")

type V3QualityRunLabel = Literal["V3_QUALITY_PASS_1", "V3_QUALITY_REPEAT_1"]
type MediaValidationFactory = Callable[[str, Path, Path], VisionMediaValidationProvenanceV1]


class V3QualityFixtureIntegrityError(ValueError):
    """The owner-approved Phase 8 package failed a closed integrity check."""


class V3QualityDecisionRequiredError(ValueError):
    """One or more owner decisions required before scoring/execution are unresolved."""


class V3QualityPromptBindingError(ValueError):
    """The frozen prompt-v3 identity or text/hash pairing failed closed verification."""


class V3QualityUnsafeScratchDirectoryError(ValueError):
    """A generated scratch target is unsafe for scoped cleanup."""


class V3QualityNoRealP2T1PassAvailableError(RuntimeError):
    """A fixture did not earn a fresh real P2-T1 PASS before adapter construction."""


class V3QualityRawOutputHookNotWiredError(RuntimeError):
    """A typed result that requires raw-output classification arrived without one."""


class V3QualityInvalidRunLabelError(ValueError):
    """The pass/repeat label is outside the separately registered quality experiment."""


class V3QualityLocalOnlyBoundaryError(TypeError):
    """The local-only runner received something other than its concrete static fake factory."""


class V3QualityRawOutputMode(StrEnum):
    """Phase 8 accepts only ``CLASSIFY_ONLY``; the other token is rejected fail-closed."""

    CLASSIFY_ONLY = "CLASSIFY_ONLY"
    EPHEMERAL_CAPTURE = "EPHEMERAL_CAPTURE"


class _V3QualityLocalFakeAdapter:
    """Static typed-result adapter used only by no-GPU local tests."""

    __slots__ = ("_emit_raw_output", "_hook", "_outcomes", "_raw_output", "calls", "requests")

    def __init__(
        self,
        outcomes: tuple[VisionUnderstandingResultV2, ...],
        hook: Callable[[str], None],
        *,
        emit_raw_output: bool,
        raw_output: str,
    ) -> None:
        self._outcomes = outcomes
        self._hook = hook
        self._emit_raw_output = emit_raw_output
        self._raw_output = raw_output
        self.calls = 0
        self.requests: list[VisionUnderstandingRequestV2] = []

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2:
        if self.calls >= len(self._outcomes):
            raise RuntimeError("local fake adapter received more calls than its static outcomes")
        self.requests.append(request)
        if self._emit_raw_output:
            self._hook(self._raw_output)
        result = self._outcomes[self.calls]
        self.calls += 1
        return result


class V3QualityLocalFakeAdapterFactory:
    """Concrete static adapter factory; it has no model/provider execution capability.

    The quality runner checks for this exact concrete type before loading the package or creating
    scratch state.  Future owner-authorized model execution must not reuse this entry point.
    """

    __slots__ = (
        "_emit_raw_output",
        "_outcomes",
        "_raw_output",
        "adapter",
        "calls",
        "received_prompts",
    )

    def __init__(
        self,
        outcomes: Sequence[VisionUnderstandingResultV2],
        *,
        emit_raw_output: bool = True,
        raw_output: str = "{}",
    ) -> None:
        self._outcomes = tuple(outcomes)
        if not self._outcomes:
            raise ValueError("the local fake factory requires at least one typed outcome")
        self._emit_raw_output = emit_raw_output
        self._raw_output = raw_output
        self.calls = 0
        self.received_prompts: list[str] = []
        self.adapter: _V3QualityLocalFakeAdapter | None = None

    def __call__(self, prompt: str, hook: Callable[[str], None]) -> VisionUnderstandingPortV2:
        self.calls += 1
        self.received_prompts.append(prompt)
        self.adapter = _V3QualityLocalFakeAdapter(
            self._outcomes,
            hook,
            emit_raw_output=self._emit_raw_output,
            raw_output=self._raw_output,
        )
        return self.adapter


class V3QualityDiagnosticCategory(StrEnum):
    """The closed S3 diagnostic vocabulary; values contain no model or ground-truth text."""

    EXPECTED_COLLECTION_PREDICTED_EMPTY = "EXPECTED_COLLECTION_PREDICTED_EMPTY"
    ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH = "ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH"
    ACTION_NO_FULL_LABEL_OR_ENDPOINT_MATCH = "ACTION_NO_FULL_LABEL_OR_ENDPOINT_MATCH"
    RELATION_NO_FULL_PREDICATE_OR_ENDPOINT_MATCH = "RELATION_NO_FULL_PREDICATE_OR_ENDPOINT_MATCH"
    THEME_NO_FULL_LABEL_OR_EVIDENCE_REF_MATCH = "THEME_NO_FULL_LABEL_OR_EVIDENCE_REF_MATCH"


class V3QualityBlockingReason(StrEnum):
    """Closed reasons for a quality pair that cannot be accepted."""

    QUALITY_BELOW_THRESHOLD = "QUALITY_BELOW_THRESHOLD"
    SYSTEMIC_TRUNCATION = "SYSTEMIC_TRUNCATION"
    CONFIG_DRIFT = "CONFIG_DRIFT"
    FIXTURE_PACKAGE_MISMATCH = "FIXTURE_PACKAGE_MISMATCH"
    INPUT_INTEGRITY_FAILURE = "INPUT_INTEGRITY_FAILURE"
    RUNTIME_OR_DEVICE_FAILURE = "RUNTIME_OR_DEVICE_FAILURE"
    INCOMPLETE_RUN_SET = "INCOMPLETE_RUN_SET"
    SCHEMA_VALIDITY_REQUIREMENT_NOT_MET = "SCHEMA_VALIDITY_REQUIREMENT_NOT_MET"
    REPEAT_WINDOW_EXCEEDED = "REPEAT_WINDOW_EXCEEDED"
    SESSION_RESET_DECLARED = "SESSION_RESET_DECLARED"


@dataclass(frozen=True, slots=True)
class V3QualityCollectionThreshold:
    """One explicit D-5 threshold; no production recommendation is encoded here."""

    collection: str
    minimum_coverage: float | None
    minimum_accuracy: float | None
    minimum_count_rate: float | None
    maximum_count_rate: float | None = None

    def __post_init__(self) -> None:
        if self.collection not in _COLLECTIONS:
            raise ValueError("D-5 threshold names an unknown collection")
        if (
            self.minimum_coverage is None
            and self.minimum_accuracy is None
            and self.minimum_count_rate is None
        ):
            raise ValueError("D-5 threshold must define at least one metric")
        for value in (self.minimum_coverage, self.minimum_accuracy):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError("D-5 coverage and accuracy metrics must be between 0 and 1")
        for value in (self.minimum_count_rate, self.maximum_count_rate):
            if value is not None and value < 0.0:
                raise ValueError("D-5 count-rate metrics must not be negative")
        if (
            self.minimum_count_rate is not None
            and self.maximum_count_rate is not None
            and self.minimum_count_rate > self.maximum_count_rate
        ):
            raise ValueError("D-5 count-rate minimum must not exceed its maximum")


@dataclass(frozen=True, slots=True)
class V3QualityAcceptanceThresholds:
    """Explicit D-5 values supplied by an owner-approved future execution record."""

    collections: tuple[V3QualityCollectionThreshold, ...]

    def __post_init__(self) -> None:
        names = tuple(item.collection for item in self.collections)
        if names != _COLLECTIONS:
            raise ValueError("D-5 thresholds must cover the five collections in fixed order")

    def for_collection(self, collection: str) -> V3QualityCollectionThreshold:
        for threshold in self.collections:
            if threshold.collection == collection:
                return threshold
        raise KeyError(collection)


@dataclass(frozen=True, slots=True)
class V3QualityRepeatGate:
    """Explicit D-6 repeat/blocker policy; all fields are required and have no defaults."""

    expected_attempted_runs: int
    expected_run_records: int
    minimum_schema_valid_runs: int
    systemic_truncation_threshold: int
    repeat_window: timedelta
    require_same_session: bool
    block_on_input_integrity_failure: bool
    block_on_runtime_or_device_failure: bool

    def __post_init__(self) -> None:
        if self.expected_attempted_runs <= 0 or self.expected_run_records <= 0:
            raise ValueError("D-6 run counts must be positive")
        if self.minimum_schema_valid_runs <= 0:
            raise ValueError("D-6 minimum schema-valid run count must be positive")
        if self.minimum_schema_valid_runs > self.expected_run_records:
            raise ValueError("D-6 schema-valid requirement cannot exceed expected run records")
        if self.systemic_truncation_threshold < 0:
            raise ValueError("D-6 truncation threshold must not be negative")
        if self.repeat_window <= timedelta(0):
            raise ValueError("D-6 repeat window must be positive")


@dataclass(frozen=True, slots=True)
class V3QualityExecutionDecisions:
    """D-5/D-6 remain unresolved-capable; Phase 8 D-7 is fixed to ``CLASSIFY_ONLY``."""

    d5_acceptance_thresholds: V3QualityAcceptanceThresholds | None = None
    d6_repeat_gate: V3QualityRepeatGate | None = None
    d7_raw_output_mode: V3QualityRawOutputMode | None = None

    def require_resolved(self) -> None:
        unresolved = tuple(
            label
            for label, value in (
                ("D-5", self.d5_acceptance_thresholds),
                ("D-6", self.d6_repeat_gate),
                ("D-7", self.d7_raw_output_mode),
            )
            if value is None
        )
        if unresolved:
            raise V3QualityDecisionRequiredError(
                "unresolved owner decisions: " + ", ".join(unresolved)
            )

    def require_phase8_classify_only(self) -> None:
        """Require the resolved Phase 8 D-7 decision selected by the owner."""

        self.require_resolved()
        if self.d7_raw_output_mode is not V3QualityRawOutputMode.CLASSIFY_ONLY:
            raise V3QualityDecisionRequiredError(
                "Phase 8 D-7 is fixed to CLASSIFY_ONLY; EPHEMERAL_CAPTURE is not accepted"
            )


@dataclass(frozen=True, slots=True)
class V3QualityCollectionScore:
    """Safe counts/rates only; ``None`` is an explicit NOT_MEASURED value."""

    ground_truth_count: int
    predicted_count: int
    matched_count: int
    coverage: float | None
    accuracy: float | None
    count_rate: float | None


@dataclass(frozen=True, slots=True)
class V3QualityScore:
    """Per-success score and closed diagnostic counts, with no candidate payloads."""

    collection_scores: Mapping[str, V3QualityCollectionScore]
    diagnostic_category_counts: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class V3QualityVerifiedFixture:
    fixture_id: str
    image_path: Path
    image_sha256: str
    ground_truth: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class V3QualityFixturePackage:
    manifest_version: str
    ground_truth_sha256: str
    matching_rule_id: str
    matching_rule_sha256: str
    fixtures: tuple[V3QualityVerifiedFixture, ...]


@dataclass(frozen=True, slots=True)
class V3QualityFixtureRunResult:
    """One safe result bound to the Phase 8 fixture identity."""

    fixture_id: str
    fixture_sha256: str
    status: str
    error_code: str | None
    error_detail: str | None
    attempt_number: int
    repair_attempted: bool
    wall_latency_ms: float
    peak_vram_mb: float | None
    vram_not_measured_reason: str | None
    fenced: bool | None
    truncated: bool | None
    extra_key: bool | None
    invalid_enum: bool | None
    collection_scores: Mapping[str, V3QualityCollectionScore] | None
    diagnostic_category_counts: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class V3QualityPassReport:
    """One independent Phase 8 pass; pass/repeat results are never pooled."""

    run_label: V3QualityRunLabel
    manifest_version: str
    ground_truth_sha256: str
    matching_rule_id: str
    matching_rule_sha256: str
    prompt_protocol_id: str
    prompt_sha256: str
    profile_id: str
    profile_catalog_hash: str
    raw_output_mode: str
    attempted_runs: int
    schema_valid_count: int
    typed_failure_counts: Mapping[str, int]
    lossless_unwrap_recovered_count: int
    fenced_raw_output_count: int
    truncated_count: int
    extra_key_count: int
    invalid_enum_count: int
    known_policy_trigger_rate: Literal["NOT_APPLICABLE"]
    aggregate_collection_scores: Mapping[str, V3QualityCollectionScore]
    aggregate_diagnostic_category_counts: Mapping[str, int]
    runs: tuple[V3QualityFixtureRunResult, ...]
    started_at: datetime
    completed_at: datetime


@dataclass(frozen=True, slots=True)
class V3QualityPassEvaluation:
    run_label: V3QualityRunLabel
    attempted_runs: int
    run_record_count: int
    is_complete: bool
    schema_valid_count: int
    schema_valid_requirement_met: bool
    thresholds_met: bool
    truncated_count: int


@dataclass(frozen=True, slots=True)
class V3QualityVerdict:
    """A quality-only pair verdict; it has no mapping-readiness status."""

    prompt_protocol_id: str
    prompt_sha256: str
    pass_1: V3QualityPassEvaluation
    repeat_1: V3QualityPassEvaluation
    repeat_gap: timedelta
    same_lightning_session: bool
    overall: Literal["QUALITY_READY", "QUALITY_NOT_READY", "NON_COMPARABLE"]
    blocking_reasons: tuple[V3QualityBlockingReason, ...]


def _sha256_of(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _is_absolute_machine_path(path: Path) -> bool:
    value = str(path)
    return value.startswith(("/", "\\")) or bool(_WINDOWS_DRIVE_ABSOLUTE_PATTERN.match(value))


def _load_json_object(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise V3QualityFixtureIntegrityError(f"Phase 8 {label} could not be loaded") from error
    if not isinstance(value, dict):
        raise V3QualityFixtureIntegrityError(f"Phase 8 {label} must be a JSON object")
    return value


def _require_relative_file(root: Path, reference: object, *, label: str) -> Path:
    if (
        not isinstance(reference, str)
        or not reference
        or _is_absolute_machine_path(Path(reference))
    ):
        raise V3QualityFixtureIntegrityError(f"Phase 8 {label} must be a relative file reference")
    root_resolved = root.resolve()
    resolved = (root / reference).resolve()
    if resolved == root_resolved or root_resolved not in resolved.parents or not resolved.is_file():
        raise V3QualityFixtureIntegrityError(f"Phase 8 {label} must resolve inside the package")
    return resolved


def _require_string(mapping: Mapping[str, Any], key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise V3QualityFixtureIntegrityError(f"Phase 8 {label}.{key} must be non-empty text")
    return value


def _require_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise V3QualityFixtureIntegrityError(f"Phase 8 {label} must be a lowercase SHA-256")
    return value


def _read_png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise V3QualityFixtureIntegrityError("a declared Phase 8 image is not a valid PNG")
    width, height = unpack(">II", data[16:24])
    return int(width), int(height)


def _ground_truth_items(
    fixture: Mapping[str, Any], collection: str
) -> tuple[Mapping[str, Any], ...]:
    value = fixture.get(collection)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise V3QualityFixtureIntegrityError(
            "Phase 8 ground truth collection is not an object list"
        )
    return tuple(value)


def _validate_ground_truth_fixture(fixture: Mapping[str, Any]) -> None:
    fixture_id = _require_string(fixture, "fixture_id", label="ground_truth.fixture")
    all_ids: set[str] = set()
    allowed_keys = {
        "entities": {"ground_truth_id", "label"},
        "actions": {"ground_truth_id", "label", "actor_ref", "object_ref"},
        "relations": {"ground_truth_id", "predicate", "subject_ref", "object_ref"},
        "themes": {"ground_truth_id", "label", "evidence_refs"},
        "ambiguous_regions": {"ground_truth_id", "note"},
    }
    ids_by_collection: dict[str, set[str]] = {}
    for collection in _COLLECTIONS:
        ids: set[str] = set()
        for item in _ground_truth_items(fixture, collection):
            if not set(item).issubset(allowed_keys[collection]):
                raise V3QualityFixtureIntegrityError(
                    f"{fixture_id}: ground-truth item contains an unknown field"
                )
            item_id = item.get("ground_truth_id")
            if not isinstance(item_id, str) or _GROUND_TRUTH_ID_PATTERN.fullmatch(item_id) is None:
                raise V3QualityFixtureIntegrityError(
                    f"{fixture_id}: ground-truth item ID is invalid"
                )
            if item_id in all_ids:
                raise V3QualityFixtureIntegrityError(
                    f"{fixture_id}: ground-truth item IDs must be globally unique"
                )
            all_ids.add(item_id)
            ids.add(item_id)
            if collection in {"entities", "actions", "themes"} and (
                not isinstance(item.get("label"), str) or not item["label"].strip()
            ):
                raise V3QualityFixtureIntegrityError(
                    f"{fixture_id}: ground-truth label is invalid"
                )
            if collection == "relations" and (
                not isinstance(item.get("predicate"), str) or not item["predicate"].strip()
            ):
                raise V3QualityFixtureIntegrityError(
                    f"{fixture_id}: ground-truth predicate is invalid"
                )
            if collection == "ambiguous_regions" and "note" in item and (
                not isinstance(item["note"], str) or not item["note"].strip()
            ):
                raise V3QualityFixtureIntegrityError(
                    f"{fixture_id}: ambiguous-region note is invalid"
                )
        ids_by_collection[collection] = ids

    for item in _ground_truth_items(fixture, "actions"):
        for field in ("actor_ref", "object_ref"):
            reference = item.get(field)
            if reference is not None and reference not in ids_by_collection["entities"]:
                raise V3QualityFixtureIntegrityError(
                    f"{fixture_id}: action endpoint must target an entity or null"
                )
    entity_or_action = ids_by_collection["entities"] | ids_by_collection["actions"]
    for item in _ground_truth_items(fixture, "relations"):
        if (
            item.get("subject_ref") not in entity_or_action
            or item.get("object_ref") not in entity_or_action
        ):
            raise V3QualityFixtureIntegrityError(
                f"{fixture_id}: relation endpoint has an invalid target"
            )
    evidence_ids = entity_or_action | ids_by_collection["relations"]
    for item in _ground_truth_items(fixture, "themes"):
        refs = item.get("evidence_refs")
        if (
            not isinstance(refs, list)
            or not refs
            or not all(
                isinstance(reference, str) and reference in evidence_ids for reference in refs
            )
        ):
            raise V3QualityFixtureIntegrityError(
                f"{fixture_id}: theme evidence references are invalid"
            )


def _verify_ground_truth(
    path: Path, *, expected_sha256: str, expected_ids: tuple[str, ...]
) -> Mapping[str, Any]:
    if _sha256_of(path) != expected_sha256:
        raise V3QualityFixtureIntegrityError("Phase 8 ground-truth SHA-256 does not match manifest")
    ground_truth = _load_json_object(path, label="ground truth")
    if ground_truth.get("contract_name") != "VisionV3QualityGroundTruthV1":
        raise V3QualityFixtureIntegrityError("unexpected Phase 8 ground-truth contract")
    if ground_truth.get("ground_truth_version") != _EXPECTED_GROUND_TRUTH_VERSION:
        raise V3QualityFixtureIntegrityError("unexpected Phase 8 ground-truth version")
    if ground_truth.get("data_policy") != "synthetic-only":
        raise V3QualityFixtureIntegrityError("Phase 8 ground truth must be synthetic-only")
    fixtures = ground_truth.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) != _FIXTURE_COUNT:
        raise V3QualityFixtureIntegrityError("Phase 8 ground truth must contain eight fixtures")
    fixture_ids: list[str] = []
    by_id: dict[str, Mapping[str, Any]] = {}
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            raise V3QualityFixtureIntegrityError("Phase 8 ground-truth fixture is not an object")
        fixture_id = _require_string(fixture, "fixture_id", label="ground_truth.fixture")
        if fixture_id in by_id:
            raise V3QualityFixtureIntegrityError(
                "Phase 8 ground truth contains duplicate fixture IDs"
            )
        fixture_ids.append(fixture_id)
        by_id[fixture_id] = fixture
        _validate_ground_truth_fixture(fixture)
    if tuple(fixture_ids) != expected_ids:
        raise V3QualityFixtureIntegrityError("Phase 8 ground-truth fixture order is not approved")
    return ground_truth


def _current_recipe_sha256() -> str:
    source_ref = _fixture_authoring.__file__
    if source_ref is None:
        raise V3QualityFixtureIntegrityError("Phase 8 fixture recipe source is unavailable")
    return _sha256_of(Path(source_ref).resolve())


def load_and_verify_v3_quality_fixture_package(
    fixture_root: Path = _DEFAULT_FIXTURE_ROOT,
) -> V3QualityFixturePackage:
    """Verify the owner-approved Phase 8 package before any adapter/provider action."""

    root = fixture_root.resolve()
    manifest = _load_json_object(root / "manifest-v1.json", label="manifest")
    if manifest.get("contract_name") != _EXPECTED_CONTRACT_NAME:
        raise V3QualityFixtureIntegrityError("unexpected Phase 8 manifest contract")
    if manifest.get("manifest_version") != _EXPECTED_MANIFEST_VERSION:
        raise V3QualityFixtureIntegrityError("unexpected Phase 8 manifest version")
    if manifest.get("status") != _EXPECTED_STATUS:
        raise V3QualityFixtureIntegrityError("Phase 8 fixture package is not owner-approved")
    if manifest.get("split") != "HELD_OUT" or manifest.get("purpose") != _EXPECTED_PURPOSE:
        raise V3QualityFixtureIntegrityError("Phase 8 package is not a held-out quality package")
    if manifest.get("has_ground_truth") is not True or manifest.get("scope") != _EXPECTED_SCOPE:
        raise V3QualityFixtureIntegrityError("Phase 8 package quality scope is not approved")
    if manifest.get("data_policy") != "synthetic-only":
        raise V3QualityFixtureIntegrityError("Phase 8 manifest must be synthetic-only")

    prompt = manifest.get("prompt_protocol")
    if not isinstance(prompt, Mapping) or (
        prompt.get("protocol_id") != _EXPECTED_PROMPT_PROTOCOL_ID
        or prompt.get("sha256") != _EXPECTED_PROMPT_SHA256
        or prompt.get("schema_target") != _EXPECTED_SCHEMA_TARGET
        or prompt.get("protocol_id") != C1_PROMPT_V3.protocol_id
        or prompt.get("sha256") != C1_PROMPT_V3.prompt_sha256
        or prompt.get("schema_target") != c1_prompt_schema_target()
    ):
        raise V3QualityFixtureIntegrityError(
            "Phase 8 prompt identity is not the approved v3 identity"
        )

    image_generation = manifest.get("image_generation")
    if not isinstance(image_generation, Mapping) or (
        image_generation.get("recipe_module_ref") != _EXPECTED_RECIPE_REF
        or image_generation.get("recipe_module_sha256") != _current_recipe_sha256()
        or image_generation.get("deterministic") is not True
    ):
        raise V3QualityFixtureIntegrityError("Phase 8 recipe identity is not current")
    dimensions = image_generation.get("dimensions")
    if not isinstance(dimensions, Mapping) or (
        dimensions.get("width") != _EXPECTED_DIMENSION
        or dimensions.get("height") != _EXPECTED_DIMENSION
    ):
        raise V3QualityFixtureIntegrityError("Phase 8 package dimensions are not approved")

    local_validation = manifest.get("local_authoring_validation")
    if not isinstance(local_validation, Mapping) or (
        local_validation.get("p2t1_result") != "PASS_FOR_ALL_8_FIXTURES"
        or local_validation.get("scratch_cleanup") != "CONFIRMED"
        or local_validation.get("model_or_gpu_called") is not False
    ):
        raise V3QualityFixtureIntegrityError("Phase 8 authoring validation is not complete")
    disjointness = manifest.get("disjointness")
    if not isinstance(disjointness, Mapping) or any(
        disjointness.get(key) != "VERIFIED_NO_OVERLAP"
        for key in (
            "b3_regenerated_hash_comparison_status",
            "b4_manifest_hash_comparison_status",
            "v3_map_manifest_hash_comparison_status",
        )
    ):
        raise V3QualityFixtureIntegrityError("Phase 8 disjointness proof is incomplete")

    expected_ids = tuple(spec.fixture_id for spec in _fixture_authoring.TAXONOMY)
    expected_tokens = {spec.fixture_id: spec.taxonomy_token for spec in _fixture_authoring.TAXONOMY}
    manifest_fixtures = manifest.get("fixtures")
    if not isinstance(manifest_fixtures, list) or len(manifest_fixtures) != _FIXTURE_COUNT:
        raise V3QualityFixtureIntegrityError("Phase 8 manifest must contain eight fixtures")
    declared_ids = tuple(
        item.get("fixture_id") if isinstance(item, Mapping) else None for item in manifest_fixtures
    )
    if declared_ids != expected_ids:
        raise V3QualityFixtureIntegrityError("Phase 8 manifest fixture order is not approved")

    ground_truth_metadata = manifest.get("ground_truth")
    matching_rule_metadata = manifest.get("matching_rule")
    if not isinstance(ground_truth_metadata, Mapping) or not isinstance(
        matching_rule_metadata, Mapping
    ):
        raise V3QualityFixtureIntegrityError("Phase 8 ground-truth/rule metadata is missing")
    ground_truth_sha256 = _require_sha256(
        ground_truth_metadata.get("sha256"), label="ground_truth.sha256"
    )
    matching_rule_sha256 = _require_sha256(
        matching_rule_metadata.get("sha256"), label="matching_rule.sha256"
    )
    if matching_rule_metadata.get("rule_id") != _EXPECTED_RULE_ID:
        raise V3QualityFixtureIntegrityError("Phase 8 matching-rule ID is not approved")
    ground_truth_path = _require_relative_file(
        root, ground_truth_metadata.get("ref"), label="ground_truth.ref"
    )
    matching_rule_path = _require_relative_file(
        root, matching_rule_metadata.get("ref"), label="matching_rule.ref"
    )
    if _sha256_of(matching_rule_path) != matching_rule_sha256:
        raise V3QualityFixtureIntegrityError(
            "Phase 8 matching-rule SHA-256 does not match manifest"
        )
    _verify_ground_truth(
        ground_truth_path, expected_sha256=ground_truth_sha256, expected_ids=expected_ids
    )

    fixtures: list[V3QualityVerifiedFixture] = []
    ground_truth = _load_json_object(ground_truth_path, label="ground truth")
    ground_truth_by_id = {
        fixture["fixture_id"]: fixture
        for fixture in ground_truth["fixtures"]
        if isinstance(fixture, Mapping)
    }
    seen_hashes: set[str] = set()
    for item, fixture_id in zip(manifest_fixtures, expected_ids, strict=True):
        if not isinstance(item, Mapping):
            raise V3QualityFixtureIntegrityError("Phase 8 manifest fixture is not an object")
        declared_hash = _require_sha256(item.get("image_sha256"), label="fixture.image_sha256")
        if declared_hash in seen_hashes:
            raise V3QualityFixtureIntegrityError("Phase 8 image hashes must be unique")
        seen_hashes.add(declared_hash)
        if item.get("image_ref") != f"images/{fixture_id}.png":
            raise V3QualityFixtureIntegrityError("Phase 8 image reference is not approved")
        if (
            item.get("taxonomy_token") != expected_tokens[fixture_id]
            or item.get("p2t1_pass") is not True
        ):
            raise V3QualityFixtureIntegrityError("Phase 8 fixture metadata is not approved")
        declared_dimensions = item.get("dimensions")
        if not isinstance(declared_dimensions, Mapping) or (
            declared_dimensions.get("width") != _EXPECTED_DIMENSION
            or declared_dimensions.get("height") != _EXPECTED_DIMENSION
        ):
            raise V3QualityFixtureIntegrityError("Phase 8 fixture dimensions are not approved")
        image_path = _require_relative_file(root, item.get("image_ref"), label="fixture.image_ref")
        if _sha256_of(image_path) != declared_hash:
            raise V3QualityFixtureIntegrityError("Phase 8 image SHA-256 does not match manifest")
        if _read_png_dimensions(image_path) != (_EXPECTED_DIMENSION, _EXPECTED_DIMENSION):
            raise V3QualityFixtureIntegrityError("Phase 8 image dimensions do not match manifest")
        ground_truth_fixture = ground_truth_by_id.get(fixture_id)
        if ground_truth_fixture is None:
            raise V3QualityFixtureIntegrityError("Phase 8 fixture has no ground truth")
        fixtures.append(
            V3QualityVerifiedFixture(
                fixture_id=fixture_id,
                image_path=image_path,
                image_sha256=declared_hash,
                ground_truth=ground_truth_fixture,
            )
        )

    return V3QualityFixturePackage(
        manifest_version=_EXPECTED_MANIFEST_VERSION,
        ground_truth_sha256=ground_truth_sha256,
        matching_rule_id=_EXPECTED_RULE_ID,
        matching_rule_sha256=matching_rule_sha256,
        fixtures=tuple(fixtures),
    )


def _verified_v3_prompt_text() -> str:
    if (
        C1_PROMPT_V3.protocol_id != _EXPECTED_PROMPT_PROTOCOL_ID
        or C1_PROMPT_V3.prompt_sha256 != _EXPECTED_PROMPT_SHA256
    ):
        raise V3QualityPromptBindingError("Phase 8 prompt identity is not the frozen v3 identity")
    prompt_text = C1_PROMPT_V3.prompt_text_provider()
    if _sha256_text(prompt_text) != _EXPECTED_PROMPT_SHA256:
        raise V3QualityPromptBindingError("Phase 8 prompt text/hash self-check failed")
    return prompt_text


def _require_safe_scratch_target(runtime_dir: Path) -> Path:
    if _is_absolute_machine_path(runtime_dir):
        raise V3QualityUnsafeScratchDirectoryError("Phase 8 runtime scratch must be relative")
    cwd = Path.cwd().resolve()
    resolved = runtime_dir.resolve()
    if resolved == cwd or cwd not in resolved.parents:
        raise V3QualityUnsafeScratchDirectoryError(
            "Phase 8 runtime scratch must be strictly nested under the current directory"
        )
    if resolved.exists():
        raise V3QualityUnsafeScratchDirectoryError(
            "Phase 8 runtime scratch must not already exist before the pass"
        )
    return resolved


def _write_companion_audio(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16_000
    sample_count = sample_rate
    samples = (
        int(0.3 * 32767 * sin(2 * 3.14159265 * 220 * index / sample_rate))
        for index in range(sample_count)
    )
    with wave_open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(b"".join(pack("<h", sample) for sample in samples))


def _real_p2t1_pass(
    fixture_id: str, image_path: Path, audio_path: Path
) -> VisionMediaValidationProvenanceV1:
    result = DeterministicMediaValidator(FileMediaSignalInspector()).validate(
        MediaValidationRequest(
            image_path=image_path,
            audio_path=audio_path,
            image_artifact_ref=f"vision-v3-quality-{fixture_id}-synthetic-image",
            audio_artifact_ref="vision-v3-quality-synthetic-audio",
        )
    )
    if result.decision is not MediaDecision.PASS:
        raise V3QualityNoRealP2T1PassAvailableError(f"{fixture_id} did not earn a real P2-T1 PASS")
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref=f"vision-v3-quality-{fixture_id}-p2t1-validation",
        validation_artifact_sha256=_sha256_text(result.model_dump_json()),
        decision="PASS",
        validator_policy_version=result.validator_policy_version,
    )


def _relative_artifact_ref(path: Path) -> str:
    value = Path(os.path.relpath(path, Path.cwd())).as_posix()
    if _is_absolute_machine_path(Path(value)):
        raise V3QualityFixtureIntegrityError("Phase 8 adapter reference became absolute")
    return value


def _item_id(item: object, *, predicted: bool) -> str:
    value = (
        getattr(item, "observation_id", None)
        if predicted
        else (item.get("ground_truth_id") if isinstance(item, Mapping) else None)
    )
    if not isinstance(value, str) or not value:
        raise V3QualityFixtureIntegrityError("Phase 8 scored item has no stable ID")
    return value


def _item_label(item: object, collection: str) -> str:
    if collection == "relations":
        value = (
            item.predicate.value
            if isinstance(item, RelationCandidateV1)
            else (item.get("predicate") if isinstance(item, Mapping) else None)
        )
    elif collection == "ambiguous_regions":
        value = (
            item.note.value
            if isinstance(item, AmbiguousRegionCandidateV1)
            else (item.get("note") if isinstance(item, Mapping) else None)
        )
    else:
        value = (
            item.label.value
            if isinstance(item, (EntityCandidateV1, ActionCandidateV1, ThemeCandidateV1))
            else (item.get("label") if isinstance(item, Mapping) else None)
        )
    if not isinstance(value, str):
        raise V3QualityFixtureIntegrityError("Phase 8 scored text field is invalid")
    return value


def _normalize(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFC", value).casefold().strip().replace("-", " ").split()
    )


def _maximum_cardinality(
    ground_truth: Sequence[object],
    predicted: Sequence[object],
    eligible: Callable[[object, object], bool],
    *,
    unavailable_prediction_ids: frozenset[str],
) -> int:
    matched_by_prediction: dict[str, object] = {}

    def augment(expected: object, visited: set[str]) -> bool:
        for candidate in predicted:
            candidate_id = _item_id(candidate, predicted=True)
            if (
                candidate_id in unavailable_prediction_ids
                or candidate_id in visited
                or not eligible(candidate, expected)
            ):
                continue
            visited.add(candidate_id)
            incumbent = matched_by_prediction.get(candidate_id)
            if incumbent is None or augment(incumbent, visited):
                matched_by_prediction[candidate_id] = expected
                return True
        return False

    return sum(augment(expected, set()) for expected in ground_truth)


def _maximum_matching(
    predicted: Sequence[object],
    ground_truth: Sequence[object],
    eligible: Callable[[object, object], bool],
) -> dict[str, str]:
    ordered_gt = sorted(ground_truth, key=lambda item: _item_id(item, predicted=False))
    ordered_predicted = sorted(predicted, key=lambda item: _item_id(item, predicted=True))
    target_count = _maximum_cardinality(
        ordered_gt, ordered_predicted, eligible, unavailable_prediction_ids=frozenset()
    )
    matches: dict[str, str] = {}
    used_prediction_ids: set[str] = set()
    for index, expected in enumerate(ordered_gt):
        choices = [
            candidate
            for candidate in ordered_predicted
            if _item_id(candidate, predicted=True) not in used_prediction_ids
            and eligible(candidate, expected)
        ]
        for candidate in [*choices, None]:
            proposed_used = set(used_prediction_ids)
            proposed_count = len(matches)
            if candidate is not None:
                candidate_id = _item_id(candidate, predicted=True)
                proposed_used.add(candidate_id)
                proposed_count += 1
            remaining = _maximum_cardinality(
                ordered_gt[index + 1 :],
                ordered_predicted,
                eligible,
                unavailable_prediction_ids=frozenset(proposed_used),
            )
            if proposed_count + remaining != target_count:
                continue
            if candidate is not None:
                candidate_id = _item_id(candidate, predicted=True)
                matches[candidate_id] = _item_id(expected, predicted=False)
                used_prediction_ids.add(candidate_id)
            break
        else:  # pragma: no cover - target cardinality guarantees a choice
            raise AssertionError("Phase 8 maximum matching lost its cardinality")
    return matches


def _endpoint_matches(predicted: str | None, expected: object, resolved: Mapping[str, str]) -> bool:
    if expected is None:
        return predicted is None
    return predicted is not None and resolved.get(predicted) == expected


def _score_collection(
    *,
    ground_truth_count: int,
    predicted_count: int,
    matched_count: int,
    ambiguous: bool = False,
) -> V3QualityCollectionScore:
    return V3QualityCollectionScore(
        ground_truth_count=ground_truth_count,
        predicted_count=predicted_count,
        matched_count=matched_count,
        coverage=(matched_count / ground_truth_count if ground_truth_count else None),
        accuracy=(None if ambiguous or not predicted_count else matched_count / predicted_count),
        count_rate=(
            predicted_count / ground_truth_count if ambiguous and ground_truth_count else None
        ),
    )


def _diagnostic_counts(
    collection: str,
    predicted: Sequence[object],
    ground_truth: Sequence[object],
    matches: Mapping[str, str],
) -> Mapping[str, int]:
    category_by_collection = {
        "entities": V3QualityDiagnosticCategory.ENTITY_NO_EXACT_CANONICAL_LABEL_MATCH,
        "actions": V3QualityDiagnosticCategory.ACTION_NO_FULL_LABEL_OR_ENDPOINT_MATCH,
        "relations": V3QualityDiagnosticCategory.RELATION_NO_FULL_PREDICATE_OR_ENDPOINT_MATCH,
        "themes": V3QualityDiagnosticCategory.THEME_NO_FULL_LABEL_OR_EVIDENCE_REF_MATCH,
    }
    if collection == "ambiguous_regions":
        return {}
    matched_ground_truth_ids = set(matches.values())
    category = category_by_collection[collection]
    counts: dict[str, int] = {}
    for expected in ground_truth:
        if _item_id(expected, predicted=False) in matched_ground_truth_ids:
            continue
        key = (
            V3QualityDiagnosticCategory.EXPECTED_COLLECTION_PREDICTED_EMPTY.value
            if not predicted
            else category.value
        )
        counts[key] = counts.get(key, 0) + 1
    return counts


def score_v3_quality_success(
    result: VisionUnderstandingSuccessV2, ground_truth: Mapping[str, Any]
) -> V3QualityScore:
    """Score one schema-valid success under the frozen Phase 8 exact-match rule."""

    entities_gt = _ground_truth_items(ground_truth, "entities")
    entity_matches = _maximum_matching(
        result.entities,
        entities_gt,
        lambda candidate, expected: (
            _normalize(_item_label(candidate, "entities"))
            == _normalize(_item_label(expected, "entities"))
        ),
    )

    def action_eligible(candidate: object, expected: object) -> bool:
        if not isinstance(candidate, ActionCandidateV1) or not isinstance(expected, Mapping):
            return False
        if _normalize(_item_label(candidate, "actions")) != _normalize(
            _item_label(expected, "actions")
        ):
            return False
        return all(
            _endpoint_matches(getattr(candidate, field), expected.get(field), entity_matches)
            for field in ("actor_ref", "object_ref")
        )

    actions_gt = _ground_truth_items(ground_truth, "actions")
    action_matches = _maximum_matching(result.actions, actions_gt, action_eligible)
    resolved = {**entity_matches, **action_matches}

    def relation_eligible(candidate: object, expected: object) -> bool:
        if not isinstance(candidate, RelationCandidateV1) or not isinstance(expected, Mapping):
            return False
        return (
            _normalize(_item_label(candidate, "relations"))
            == _normalize(_item_label(expected, "relations"))
            and resolved.get(candidate.subject_ref) == expected.get("subject_ref")
            and resolved.get(candidate.object_ref) == expected.get("object_ref")
        )

    relations_gt = _ground_truth_items(ground_truth, "relations")
    relation_matches = _maximum_matching(result.relations, relations_gt, relation_eligible)
    resolved = {**resolved, **relation_matches}

    def theme_eligible(candidate: object, expected: object) -> bool:
        if not isinstance(candidate, ThemeCandidateV1) or not isinstance(expected, Mapping):
            return False
        expected_refs = expected.get("evidence_refs")
        if not isinstance(expected_refs, list):
            return False
        resolved_refs = tuple(resolved.get(reference) for reference in candidate.evidence_refs)
        return (
            _normalize(_item_label(candidate, "themes"))
            == _normalize(_item_label(expected, "themes"))
            and len(resolved_refs) == len(expected_refs)
            and set(resolved_refs) == set(expected_refs)
        )

    themes_gt = _ground_truth_items(ground_truth, "themes")
    theme_matches = _maximum_matching(result.themes, themes_gt, theme_eligible)
    ambiguous_gt = _ground_truth_items(ground_truth, "ambiguous_regions")
    # Phase 8 deliberately has no geometry/evidence target for this collection.  Its metric is
    # count/rate only: count overlap is reported as coverage, count rate exposes overprediction,
    # and accuracy remains NOT_MEASURED.  No note text is inferred or compared.
    ambiguous_matched_count = min(len(result.ambiguous_regions), len(ambiguous_gt))

    matches_by_collection = {
        "entities": entity_matches,
        "actions": action_matches,
        "relations": relation_matches,
        "themes": theme_matches,
    }
    diagnostics: dict[str, int] = {}
    for collection, matches in matches_by_collection.items():
        collection_counts = _diagnostic_counts(
            collection,
            getattr(result, collection),
            _ground_truth_items(ground_truth, collection),
            matches,
        )
        for key, count in collection_counts.items():
            diagnostics[key] = diagnostics.get(key, 0) + count

    return V3QualityScore(
        collection_scores={
            "entities": _score_collection(
                ground_truth_count=len(entities_gt),
                predicted_count=len(result.entities),
                matched_count=len(entity_matches),
            ),
            "actions": _score_collection(
                ground_truth_count=len(actions_gt),
                predicted_count=len(result.actions),
                matched_count=len(action_matches),
            ),
            "relations": _score_collection(
                ground_truth_count=len(relations_gt),
                predicted_count=len(result.relations),
                matched_count=len(relation_matches),
            ),
            "themes": _score_collection(
                ground_truth_count=len(themes_gt),
                predicted_count=len(result.themes),
                matched_count=len(theme_matches),
            ),
            "ambiguous_regions": _score_collection(
                ground_truth_count=len(ambiguous_gt),
                predicted_count=len(result.ambiguous_regions),
                matched_count=ambiguous_matched_count,
                ambiguous=True,
            ),
        },
        diagnostic_category_counts=diagnostics,
    )


def _aggregate_scores(
    scores: Sequence[Mapping[str, V3QualityCollectionScore]],
) -> Mapping[str, V3QualityCollectionScore]:
    aggregates: dict[str, V3QualityCollectionScore] = {}
    for collection in _COLLECTIONS:
        items = [score[collection] for score in scores]
        ground_truth_count = sum(item.ground_truth_count for item in items)
        predicted_count = sum(item.predicted_count for item in items)
        matched_count = sum(item.matched_count for item in items)
        aggregates[collection] = _score_collection(
            ground_truth_count=ground_truth_count,
            predicted_count=predicted_count,
            matched_count=matched_count,
            ambiguous=collection == "ambiguous_regions",
        )
    return aggregates


def _aggregate_diagnostics(
    diagnostics: Sequence[Mapping[str, int]],
) -> Mapping[str, int]:
    aggregate: dict[str, int] = {}
    for counts in diagnostics:
        for category, count in counts.items():
            aggregate[category] = aggregate.get(category, 0) + count
    return aggregate


def _classification_required(result: VisionUnderstandingResultV2) -> bool:
    if isinstance(result, VisionUnderstandingSuccessV2):
        return True
    assert isinstance(result, VisionUnderstandingFailureV2)
    if result.error_code is VisionErrorCode.PROHIBITED_CLAIM_DETECTED:
        return True
    return (
        result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
        and result.error_detail.value
        in {
            "OUTPUT_MAPPING_FAILED",
            "DUPLICATE_OBSERVATION_ID",
            "REFERENCE_INTEGRITY_VIOLATION",
        }
    )


def _copy_images_to_scratch(
    fixtures: Sequence[V3QualityVerifiedFixture], runtime_dir: Path
) -> tuple[Path, ...]:
    images_dir = runtime_dir / "images"
    copied: list[Path] = []
    for fixture in fixtures:
        target = images_dir / f"{fixture.fixture_id}.png"
        images_root = images_dir.resolve()
        if target.resolve() == images_root or images_root not in target.resolve().parents:
            raise V3QualityUnsafeScratchDirectoryError("Phase 8 image copy escaped scratch")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fixture.image_path, target)
        if _sha256_of(target) != fixture.image_sha256:
            raise V3QualityFixtureIntegrityError("Phase 8 scratch image hash changed during copy")
        copied.append(target)
    return tuple(copied)


def run_v3_quality_pass(
    adapter_factory: V3QualityLocalFakeAdapterFactory,
    collector: B3RawOutputCollector,
    *,
    run_label: V3QualityRunLabel,
    decisions: V3QualityExecutionDecisions,
    fixture_root: Path = _DEFAULT_FIXTURE_ROOT,
    runtime_dir: Path | None = None,
    sample_vram: bool = False,
    validate_media: MediaValidationFactory = _real_p2t1_pass,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> V3QualityPassReport:
    """Run one local-only pass through the concrete static typed-result fake boundary.

    This entry point cannot accept a model/provider factory.  A future real-model run, if approved
    separately, must use a different module and authorization path after D-8; no caller argument
    here can turn this local preparation runner into a model runner.
    """

    if run_label not in _DEFAULT_RUNTIME_DIRS:
        raise V3QualityInvalidRunLabelError("Phase 8 run label is not registered")
    decisions.require_phase8_classify_only()
    if collector.mode is not B3RawOutputMode.CLASSIFY_ONLY:
        raise V3QualityDecisionRequiredError(
            "Phase 8 D-7 requires the B3 collector mode CLASSIFY_ONLY"
        )
    if sample_vram:
        raise V3QualityLocalOnlyBoundaryError(
            "Phase 8 local preparation cannot sample GPU memory"
        )
    if type(adapter_factory) is not V3QualityLocalFakeAdapterFactory:
        raise V3QualityLocalOnlyBoundaryError(
            "Phase 8 local preparation accepts only V3QualityLocalFakeAdapterFactory"
        )

    prompt_text = _verified_v3_prompt_text()
    package = load_and_verify_v3_quality_fixture_package(fixture_root)
    resolved_runtime_dir = _require_safe_scratch_target(
        runtime_dir or _DEFAULT_RUNTIME_DIRS[run_label]
    )

    try:
        image_paths = _copy_images_to_scratch(package.fixtures, resolved_runtime_dir)
        audio_path = resolved_runtime_dir / "companion.wav"
        _write_companion_audio(audio_path)
        provenances: list[VisionMediaValidationProvenanceV1] = []
        for fixture, image_path in zip(package.fixtures, image_paths, strict=True):
            provenance = validate_media(fixture.fixture_id, image_path, audio_path)
            if provenance.decision != "PASS":
                raise V3QualityNoRealP2T1PassAvailableError(
                    f"{fixture.fixture_id} did not earn a real P2-T1 PASS"
                )
            provenances.append(provenance)

        started_at = clock()
        adapter = adapter_factory(prompt_text, collector.hook)
        runs: list[V3QualityFixtureRunResult] = []
        scores: list[Mapping[str, V3QualityCollectionScore]] = []
        diagnostics: list[Mapping[str, int]] = []
        typed_failures: dict[str, int] = {}
        schema_valid_count = 0
        lossless_unwrap_recovered_count = 0
        fenced_count = truncated_count = extra_key_count = invalid_enum_count = 0

        for _index, (fixture, image_path, provenance) in enumerate(
            zip(package.fixtures, image_paths, provenances, strict=True)
        ):
            request = VisionUnderstandingRequestV2(
                correlation_id=f"vision-{run_label.lower().replace('_', '-')}-{fixture.fixture_id}",
                source_image_ref=VisionImageReferenceV1(
                    artifact_ref=_relative_artifact_ref(image_path),
                    sha256=fixture.image_sha256,
                ),
                media_validation=provenance,
                requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
            )
            collector.take_latest()
            call_started = time.perf_counter()
            result = adapter.understand(request)
            latency_ms = (time.perf_counter() - call_started) * 1000.0
            classification: B3RawOutputClassification | None = collector.take_latest()
            if classification is None and _classification_required(result):
                raise V3QualityRawOutputHookNotWiredError(
                    f"{fixture.fixture_id}: safe raw-output classification was not observed"
                )

            peak_vram_mb: float | None = None
            collection_scores: Mapping[str, V3QualityCollectionScore] | None = None
            diagnostic_counts: Mapping[str, int] = {}
            if isinstance(result, VisionUnderstandingSuccessV2):
                scored = score_v3_quality_success(result, fixture.ground_truth)
                collection_scores = scored.collection_scores
                diagnostic_counts = scored.diagnostic_category_counts
                scores.append(collection_scores)
                diagnostics.append(diagnostic_counts)
                schema_valid_count += 1
                lossless_unwrap_recovered_count += int(result.repair_attempted)
                error_code = error_detail = None
            else:
                assert isinstance(result, VisionUnderstandingFailureV2)
                error_code = result.error_code.value
                error_detail = result.error_detail.value
                typed_failures[error_detail] = typed_failures.get(error_detail, 0) + 1

            if classification is not None:
                fenced_count += int(classification.fenced)
                truncated_count += int(classification.truncated)
                extra_key_count += int(classification.extra_key)
                invalid_enum_count += int(classification.invalid_enum)
            runs.append(
                V3QualityFixtureRunResult(
                    fixture_id=fixture.fixture_id,
                    fixture_sha256=fixture.image_sha256,
                    status=result.status,
                    error_code=error_code,
                    error_detail=error_detail,
                    attempt_number=result.attempt_number,
                    repair_attempted=result.repair_attempted,
                    wall_latency_ms=latency_ms,
                    peak_vram_mb=peak_vram_mb,
                    vram_not_measured_reason=(
                        "VRAM sampling unavailable in local-only preparation"
                    ),
                    fenced=classification.fenced if classification is not None else None,
                    truncated=classification.truncated if classification is not None else None,
                    extra_key=classification.extra_key if classification is not None else None,
                    invalid_enum=classification.invalid_enum
                    if classification is not None
                    else None,
                    collection_scores=collection_scores,
                    diagnostic_category_counts=diagnostic_counts,
                )
            )
        completed_at = clock()
    except Exception:
        shutil.rmtree(resolved_runtime_dir, ignore_errors=True)
        collector.cleanup()
        raise
    else:
        shutil.rmtree(resolved_runtime_dir, ignore_errors=True)
        collector.cleanup()

    catalog = vision_profile_catalog_v2()
    return V3QualityPassReport(
        run_label=run_label,
        manifest_version=package.manifest_version,
        ground_truth_sha256=package.ground_truth_sha256,
        matching_rule_id=package.matching_rule_id,
        matching_rule_sha256=package.matching_rule_sha256,
        prompt_protocol_id=C1_PROMPT_V3.protocol_id,
        prompt_sha256=C1_PROMPT_V3.prompt_sha256,
        profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1.value,
        profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
        raw_output_mode=collector.mode.value,
        attempted_runs=len(runs),
        schema_valid_count=schema_valid_count,
        typed_failure_counts=dict(typed_failures),
        lossless_unwrap_recovered_count=lossless_unwrap_recovered_count,
        fenced_raw_output_count=fenced_count,
        truncated_count=truncated_count,
        extra_key_count=extra_key_count,
        invalid_enum_count=invalid_enum_count,
        known_policy_trigger_rate="NOT_APPLICABLE",
        aggregate_collection_scores=_aggregate_scores(scores),
        aggregate_diagnostic_category_counts=_aggregate_diagnostics(diagnostics),
        runs=tuple(runs),
        started_at=started_at,
        completed_at=completed_at,
    )


def _thresholds_met(report: V3QualityPassReport, thresholds: V3QualityAcceptanceThresholds) -> bool:
    for threshold in thresholds.collections:
        score = report.aggregate_collection_scores[threshold.collection]
        if threshold.minimum_coverage is not None and (
            score.coverage is None or score.coverage < threshold.minimum_coverage
        ):
            return False
        if threshold.minimum_accuracy is not None and (
            score.accuracy is None or score.accuracy < threshold.minimum_accuracy
        ):
            return False
        if threshold.minimum_count_rate is not None and (
            score.count_rate is None or score.count_rate < threshold.minimum_count_rate
        ):
            return False
        if threshold.maximum_count_rate is not None and (
            score.count_rate is None or score.count_rate > threshold.maximum_count_rate
        ):
            return False
    return True


def _evaluate_quality_pass(
    report: V3QualityPassReport,
    thresholds: V3QualityAcceptanceThresholds,
    gate: V3QualityRepeatGate,
) -> V3QualityPassEvaluation:
    is_complete = (
        report.attempted_runs == gate.expected_attempted_runs
        and len(report.runs) == gate.expected_run_records
    )
    observed_schema_valid_count = sum(
        run.status == "SUCCEEDED" and run.collection_scores is not None for run in report.runs
    )
    schema_valid_requirement_met = (
        report.schema_valid_count == observed_schema_valid_count
        and observed_schema_valid_count >= gate.minimum_schema_valid_runs
    )
    return V3QualityPassEvaluation(
        run_label=report.run_label,
        attempted_runs=report.attempted_runs,
        run_record_count=len(report.runs),
        is_complete=is_complete,
        schema_valid_count=report.schema_valid_count,
        schema_valid_requirement_met=schema_valid_requirement_met,
        thresholds_met=_thresholds_met(report, thresholds),
        truncated_count=report.truncated_count,
    )


def _has_error_detail(report: V3QualityPassReport, details: frozenset[str]) -> bool:
    return any(run.error_detail in details for run in report.runs if run.error_detail is not None)


def evaluate_v3_quality_pair(
    pass_1: V3QualityPassReport,
    repeat_1: V3QualityPassReport,
    *,
    decisions: V3QualityExecutionDecisions,
    same_lightning_session: bool,
    fixture_root: Path,
) -> V3QualityVerdict:
    """Evaluate two independent quality passes against a freshly verified package identity."""

    decisions.require_phase8_classify_only()
    assert decisions.d5_acceptance_thresholds is not None
    assert decisions.d6_repeat_gate is not None
    assert decisions.d7_raw_output_mode is not None
    if pass_1.run_label != "V3_QUALITY_PASS_1" or repeat_1.run_label != "V3_QUALITY_REPEAT_1":
        raise ValueError("quality pair labels must be V3_QUALITY_PASS_1 and V3_QUALITY_REPEAT_1")

    package = load_and_verify_v3_quality_fixture_package(fixture_root)
    catalog = vision_profile_catalog_v2()
    expected_profile_id = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1.value
    expected_profile_catalog_hash = vision_profile_catalog_hash_v2(catalog)

    def report_matches_package(report: V3QualityPassReport) -> bool:
        expected_fixture_identity = tuple(
            (fixture.fixture_id, fixture.image_sha256) for fixture in package.fixtures
        )
        report_fixture_identity = tuple(
            (run.fixture_id, run.fixture_sha256) for run in report.runs
        )
        return (
            report.manifest_version == package.manifest_version
            and report.ground_truth_sha256 == package.ground_truth_sha256
            and report.matching_rule_id == package.matching_rule_id
            and report.matching_rule_sha256 == package.matching_rule_sha256
            and report.prompt_protocol_id == _EXPECTED_PROMPT_PROTOCOL_ID
            and report.prompt_sha256 == _EXPECTED_PROMPT_SHA256
            and report.profile_id == expected_profile_id
            and report.profile_catalog_hash == expected_profile_catalog_hash
            and report_fixture_identity == expected_fixture_identity
        )

    pass_matches_package = report_matches_package(pass_1)
    repeat_matches_package = report_matches_package(repeat_1)
    thresholds = decisions.d5_acceptance_thresholds
    gate = decisions.d6_repeat_gate
    pass_evaluation = _evaluate_quality_pass(pass_1, thresholds, gate)
    repeat_evaluation = _evaluate_quality_pass(repeat_1, thresholds, gate)
    repeat_gap = repeat_1.started_at - pass_1.completed_at
    config_drift = any(
        (
            pass_1.prompt_protocol_id != _EXPECTED_PROMPT_PROTOCOL_ID,
            repeat_1.prompt_protocol_id != _EXPECTED_PROMPT_PROTOCOL_ID,
            pass_1.prompt_sha256 != _EXPECTED_PROMPT_SHA256,
            repeat_1.prompt_sha256 != _EXPECTED_PROMPT_SHA256,
            pass_1.profile_id != expected_profile_id,
            repeat_1.profile_id != expected_profile_id,
            pass_1.profile_catalog_hash != expected_profile_catalog_hash,
            repeat_1.profile_catalog_hash != expected_profile_catalog_hash,
            pass_1.profile_id != repeat_1.profile_id,
            pass_1.profile_catalog_hash != repeat_1.profile_catalog_hash,
            pass_1.raw_output_mode != V3QualityRawOutputMode.CLASSIFY_ONLY.value,
            repeat_1.raw_output_mode != V3QualityRawOutputMode.CLASSIFY_ONLY.value,
        )
    )
    package_mismatch = any(
        (
            pass_1.manifest_version != _EXPECTED_MANIFEST_VERSION,
            repeat_1.manifest_version != _EXPECTED_MANIFEST_VERSION,
            pass_1.ground_truth_sha256 != repeat_1.ground_truth_sha256,
            pass_1.matching_rule_id != _EXPECTED_RULE_ID,
            repeat_1.matching_rule_id != _EXPECTED_RULE_ID,
            pass_1.matching_rule_sha256 != repeat_1.matching_rule_sha256,
            not pass_matches_package,
            not repeat_matches_package,
        )
    )
    window_exceeded = repeat_gap < timedelta(0) or repeat_gap > gate.repeat_window
    session_reset = gate.require_same_session and not same_lightning_session
    input_failure_details = frozenset(
        {
            VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_NOT_PASSED.value,
            VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_PROVENANCE_MISSING.value,
            VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE.value,
            VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH.value,
            VisionNonPolicyErrorDetailV2.PROFILE_NOT_RESOLVABLE.value,
        }
    )
    runtime_error_codes = frozenset(
        {
            VisionErrorCode.VISION_MODEL_UNAVAILABLE.value,
            VisionErrorCode.VISION_TIMEOUT.value,
            VisionErrorCode.VISION_PROVIDER_FAILURE.value,
        }
    )
    input_failure = _has_error_detail(pass_1, input_failure_details) or _has_error_detail(
        repeat_1, input_failure_details
    )
    runtime_failure = any(
        run.error_code in runtime_error_codes
        for report in (pass_1, repeat_1)
        for run in report.runs
    )
    incomplete = not pass_evaluation.is_complete or not repeat_evaluation.is_complete
    systemic_truncation = (
        pass_1.truncated_count >= gate.systemic_truncation_threshold
        or repeat_1.truncated_count >= gate.systemic_truncation_threshold
    )

    blocking: list[V3QualityBlockingReason] = []
    if config_drift:
        blocking.append(V3QualityBlockingReason.CONFIG_DRIFT)
    if package_mismatch:
        blocking.append(V3QualityBlockingReason.FIXTURE_PACKAGE_MISMATCH)
    if window_exceeded:
        blocking.append(V3QualityBlockingReason.REPEAT_WINDOW_EXCEEDED)
    if session_reset:
        blocking.append(V3QualityBlockingReason.SESSION_RESET_DECLARED)
    if incomplete:
        blocking.append(V3QualityBlockingReason.INCOMPLETE_RUN_SET)
    if (
        not pass_evaluation.schema_valid_requirement_met
        or not repeat_evaluation.schema_valid_requirement_met
    ):
        blocking.append(V3QualityBlockingReason.SCHEMA_VALIDITY_REQUIREMENT_NOT_MET)
    if systemic_truncation:
        blocking.append(V3QualityBlockingReason.SYSTEMIC_TRUNCATION)
    if gate.block_on_input_integrity_failure and input_failure:
        blocking.append(V3QualityBlockingReason.INPUT_INTEGRITY_FAILURE)
    if gate.block_on_runtime_or_device_failure and runtime_failure:
        blocking.append(V3QualityBlockingReason.RUNTIME_OR_DEVICE_FAILURE)
    comparable = not any(
        reason
        for reason in blocking
        if reason
        in {
            V3QualityBlockingReason.CONFIG_DRIFT,
            V3QualityBlockingReason.FIXTURE_PACKAGE_MISMATCH,
            V3QualityBlockingReason.REPEAT_WINDOW_EXCEEDED,
            V3QualityBlockingReason.SESSION_RESET_DECLARED,
        }
    )
    if comparable and (not pass_evaluation.thresholds_met or not repeat_evaluation.thresholds_met):
        blocking.append(V3QualityBlockingReason.QUALITY_BELOW_THRESHOLD)

    if not comparable:
        overall: Literal["QUALITY_READY", "QUALITY_NOT_READY", "NON_COMPARABLE"] = "NON_COMPARABLE"
    elif blocking:
        overall = "QUALITY_NOT_READY"
    else:
        overall = "QUALITY_READY"
    return V3QualityVerdict(
        prompt_protocol_id=_EXPECTED_PROMPT_PROTOCOL_ID,
        prompt_sha256=_EXPECTED_PROMPT_SHA256,
        pass_1=pass_evaluation,
        repeat_1=repeat_evaluation,
        repeat_gap=repeat_gap,
        same_lightning_session=same_lightning_session,
        overall=overall,
        blocking_reasons=tuple(blocking),
    )


def _score_to_dict(score: V3QualityCollectionScore) -> dict[str, object]:
    return {
        "ground_truth_count": score.ground_truth_count,
        "predicted_count": score.predicted_count,
        "matched_count": score.matched_count,
        "coverage": score.coverage,
        "accuracy": score.accuracy,
        "count_rate": score.count_rate,
    }


def quality_pass_report_to_dict(report: V3QualityPassReport) -> dict[str, object]:
    """Serialize only the safe Phase 8 report fields; no model/ground-truth text is available."""

    return {
        "run_label": report.run_label,
        "manifest_version": report.manifest_version,
        "ground_truth_sha256": report.ground_truth_sha256,
        "matching_rule_id": report.matching_rule_id,
        "matching_rule_sha256": report.matching_rule_sha256,
        "prompt_protocol_id": report.prompt_protocol_id,
        "prompt_sha256": report.prompt_sha256,
        "profile_id": report.profile_id,
        "profile_catalog_hash": report.profile_catalog_hash,
        "raw_output_mode": report.raw_output_mode,
        "attempted_runs": report.attempted_runs,
        "schema_valid_count": report.schema_valid_count,
        "typed_failure_counts": dict(report.typed_failure_counts),
        "lossless_unwrap_recovered_count": report.lossless_unwrap_recovered_count,
        "fenced_raw_output_count": report.fenced_raw_output_count,
        "truncated_count": report.truncated_count,
        "extra_key_count": report.extra_key_count,
        "invalid_enum_count": report.invalid_enum_count,
        "known_policy_trigger_rate": report.known_policy_trigger_rate,
        "aggregate_collection_scores": {
            collection: _score_to_dict(score)
            for collection, score in report.aggregate_collection_scores.items()
        },
        "aggregate_diagnostic_category_counts": dict(report.aggregate_diagnostic_category_counts),
        "runs": [
            {
                "fixture_id": run.fixture_id,
                "fixture_sha256": run.fixture_sha256,
                "status": run.status,
                "error_code": run.error_code,
                "error_detail": run.error_detail,
                "attempt_number": run.attempt_number,
                "repair_attempted": run.repair_attempted,
                "wall_latency_ms": run.wall_latency_ms,
                "peak_vram_mb": run.peak_vram_mb,
                "vram_not_measured_reason": run.vram_not_measured_reason,
                "fenced": run.fenced,
                "truncated": run.truncated,
                "extra_key": run.extra_key,
                "invalid_enum": run.invalid_enum,
                "collection_scores": (
                    {
                        collection: _score_to_dict(score)
                        for collection, score in run.collection_scores.items()
                    }
                    if run.collection_scores is not None
                    else None
                ),
                "diagnostic_category_counts": dict(run.diagnostic_category_counts),
            }
            for run in report.runs
        ],
        "started_at": report.started_at.isoformat(),
        "completed_at": report.completed_at.isoformat(),
    }


__all__ = [
    "V3QualityAcceptanceThresholds",
    "V3QualityBlockingReason",
    "V3QualityCollectionScore",
    "V3QualityCollectionThreshold",
    "V3QualityDecisionRequiredError",
    "V3QualityDiagnosticCategory",
    "V3QualityExecutionDecisions",
    "V3QualityFixtureIntegrityError",
    "V3QualityFixturePackage",
    "V3QualityFixtureRunResult",
    "V3QualityInvalidRunLabelError",
    "V3QualityLocalFakeAdapterFactory",
    "V3QualityLocalOnlyBoundaryError",
    "V3QualityNoRealP2T1PassAvailableError",
    "V3QualityPassEvaluation",
    "V3QualityPassReport",
    "V3QualityPromptBindingError",
    "V3QualityRawOutputHookNotWiredError",
    "V3QualityRawOutputMode",
    "V3QualityRepeatGate",
    "V3QualityRunLabel",
    "V3QualityScore",
    "V3QualityUnsafeScratchDirectoryError",
    "V3QualityVerdict",
    "evaluate_v3_quality_pair",
    "load_and_verify_v3_quality_fixture_package",
    "quality_pass_report_to_dict",
    "run_v3_quality_pass",
    "score_v3_quality_success",
]
