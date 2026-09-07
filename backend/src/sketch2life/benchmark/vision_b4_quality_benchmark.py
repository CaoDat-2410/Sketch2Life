"""Internal, one-pass B4 held-out quality benchmark.

This module is deliberately not a CLI.  It evaluates only the owner-reviewed local fixture
package, validates every immutable input before constructing an adapter, calls that adapter once
per fixture with the explicitly selected C1-v2 prompt, and returns safe aggregates only.  It never
persists a prompt body, raw provider output, fixture path, or ground-truth text.

Running this module locally does not authorize a model call.  Lightning execution remains a
separate owner gate after GPU-ledger reconciliation and a fresh readiness check.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from math import sin
from pathlib import Path
from struct import pack
from threading import Event, Thread
from typing import Any, Literal
from wave import open as wave_open

from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3RawOutputCollector,
)
from sketch2life.benchmark.vision_c1_prompt_mapping_study import (
    C1_PROMPT_V2,
    C1AdapterFactory,
    C1PromptProtocol,
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

_FIXTURE_COUNT = 8
_COLLECTIONS = (
    "entities",
    "actions",
    "relations",
    "themes",
    "ambiguous_regions",
)
_EXPECTED_TAXONOMY = (
    "simple_entity",
    "multi_entity",
    "action_complete_endpoints",
    "action_null_endpoint",
    "entity_relation",
    "theme_evidence_refs",
    "ambiguous_region",
    "mixed_multi_collection",
)
_DEFAULT_FIXTURE_ROOT = Path("features/FEAT-003-multimodal-understanding/fixtures/vision-b4")
_DEFAULT_RUNTIME_DIRS: Mapping[str, Path] = {
    "B4_PASS_1": Path("data/runtime/vision-b4-pass-1"),
    "B4_REPEAT_1": Path("data/runtime/vision-b4-repeat-1"),
}
_EXPECTED_MANIFEST_STATUS = "OWNER_REVIEW_APPROVED"
_EXPECTED_MANIFEST_VERSION = "vision-b4-manifest-v1"
_EXPECTED_GROUND_TRUTH_VERSION = "vision-b4-ground-truth-v1"
_EXPECTED_RULE_ID = "vision-b4-matching-rule-v1"

type B4RunLabel = Literal["B4_PASS_1", "B4_REPEAT_1"]


class B4FixtureIntegrityError(ValueError):
    """The owner-reviewed B4 package does not match its manifest before inference."""


class B4PromptBindingError(ValueError):
    """The explicitly injected prompt is not the approved C1-v2 protocol."""


class B4RawOutputHookNotWiredError(RuntimeError):
    """A raw-producing typed result arrived without its required safe classification."""


class B4InvalidRunLabelError(ValueError):
    """A B4 pass must use one of the two pre-registered, separate labels."""


@dataclass(frozen=True, slots=True)
class B4CollectionScore:
    """Safe per-fixture or aggregate counts; ``None`` represents ``NOT_MEASURED``."""

    ground_truth_count: int
    predicted_count: int
    matched_count: int
    coverage: float | None
    accuracy: float | None


@dataclass(frozen=True, slots=True)
class B4FixtureRunResult:
    """A fixture's typed outcome and safe quality measurement, never candidates or raw text."""

    fixture_id: str
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
    collection_scores: Mapping[str, B4CollectionScore] | None


@dataclass(frozen=True, slots=True)
class B4QualityPassReport:
    """Evidence-safe result for exactly one B4 pass; pass/repeat are never pooled here."""

    run_label: B4RunLabel
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
    aggregate_collection_scores: Mapping[str, B4CollectionScore]
    runs: tuple[B4FixtureRunResult, ...]


@dataclass(frozen=True, slots=True)
class _FixtureInput:
    fixture_id: str
    image_path: Path
    image_sha256: str
    ground_truth: Mapping[str, Any]


type MediaValidationFactory = Callable[[str, Path, Path], VisionMediaValidationProvenanceV1]


def _sha256_of(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _load_json_object(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise B4FixtureIntegrityError(f"B4 {label} could not be loaded") from error
    if not isinstance(value, dict):
        raise B4FixtureIntegrityError(f"B4 {label} must be a JSON object")
    return value


def _require_relative_file(root: Path, relative_ref: object, *, label: str) -> Path:
    if not isinstance(relative_ref, str):
        raise B4FixtureIntegrityError(f"B4 {label} must be a relative file reference")
    candidate = Path(relative_ref)
    if candidate.is_absolute():
        raise B4FixtureIntegrityError(f"B4 {label} must not be absolute")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if resolved == resolved_root or resolved_root not in resolved.parents or not resolved.is_file():
        raise B4FixtureIntegrityError(f"B4 {label} must resolve to a file inside the package")
    return resolved


def _require_safe_runtime_directory(runtime_dir: Path) -> None:
    """Guard the directory later removed by the runner's unconditional ``finally`` cleanup."""

    if runtime_dir.is_absolute():
        raise B4FixtureIntegrityError("B4 runtime scratch directory must be relative")
    cwd = Path.cwd().resolve()
    resolved = runtime_dir.resolve()
    if resolved == cwd or cwd not in resolved.parents:
        raise B4FixtureIntegrityError(
            "B4 runtime scratch directory must be strictly nested under the current "
            "working directory"
        )


def _require_string(mapping: Mapping[str, Any], key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise B4FixtureIntegrityError(f"B4 {label}.{key} must be a non-empty string")
    return value


def _load_fixture_package(
    fixture_root: Path,
) -> tuple[str, str, str, str, tuple[_FixtureInput, ...]]:
    root = fixture_root.resolve()
    manifest_path = root / "manifest-v1.json"
    manifest = _load_json_object(manifest_path, label="manifest")
    if manifest.get("manifest_version") != _EXPECTED_MANIFEST_VERSION:
        raise B4FixtureIntegrityError("B4 manifest version is not the approved version")
    if manifest.get("status") != _EXPECTED_MANIFEST_STATUS:
        raise B4FixtureIntegrityError("B4 manifest has not recorded owner review approval")

    prompt = manifest.get("prompt_protocol")
    if not isinstance(prompt, dict):
        raise B4FixtureIntegrityError("B4 manifest prompt protocol is missing")
    if (
        prompt.get("protocol_id") != C1_PROMPT_V2.protocol_id
        or prompt.get("sha256") != C1_PROMPT_V2.prompt_sha256
        or prompt.get("schema_target") != c1_prompt_schema_target()
    ):
        raise B4FixtureIntegrityError(
            "B4 manifest does not bind the approved C1-v2 prompt identity"
        )

    ground_truth_metadata = manifest.get("ground_truth")
    matching_rule_metadata = manifest.get("matching_rule")
    if not isinstance(ground_truth_metadata, dict) or not isinstance(matching_rule_metadata, dict):
        raise B4FixtureIntegrityError(
            "B4 manifest ground-truth or matching-rule metadata is missing"
        )
    ground_truth_path = _require_relative_file(
        root, ground_truth_metadata.get("ref"), label="ground_truth.ref"
    )
    matching_rule_path = _require_relative_file(
        root, matching_rule_metadata.get("ref"), label="matching_rule.ref"
    )
    ground_truth_sha256 = _require_string(ground_truth_metadata, "sha256", label="ground_truth")
    matching_rule_sha256 = _require_string(matching_rule_metadata, "sha256", label="matching_rule")
    if _sha256_of(ground_truth_path) != ground_truth_sha256:
        raise B4FixtureIntegrityError("B4 ground-truth SHA-256 does not match the manifest")
    if _sha256_of(matching_rule_path) != matching_rule_sha256:
        raise B4FixtureIntegrityError("B4 matching-rule SHA-256 does not match the manifest")
    if matching_rule_metadata.get("rule_id") != _EXPECTED_RULE_ID:
        raise B4FixtureIntegrityError("B4 matching-rule ID is not the approved version")

    ground_truth = _load_json_object(ground_truth_path, label="ground truth")
    if ground_truth.get("ground_truth_version") != _EXPECTED_GROUND_TRUTH_VERSION:
        raise B4FixtureIntegrityError("B4 ground-truth version is not the approved version")
    ground_truth_fixtures = ground_truth.get("fixtures")
    manifest_fixtures = manifest.get("fixtures")
    if not isinstance(ground_truth_fixtures, list) or not isinstance(manifest_fixtures, list):
        raise B4FixtureIntegrityError("B4 fixture lists are missing")
    if len(manifest_fixtures) != _FIXTURE_COUNT or len(ground_truth_fixtures) != _FIXTURE_COUNT:
        raise B4FixtureIntegrityError(
            "B4 must contain exactly eight manifest and ground-truth fixtures"
        )

    ground_truth_by_id: dict[str, Mapping[str, Any]] = {}
    for item in ground_truth_fixtures:
        if not isinstance(item, dict):
            raise B4FixtureIntegrityError("B4 ground-truth fixture must be an object")
        fixture_id = _require_string(item, "fixture_id", label="ground_truth.fixture")
        if fixture_id in ground_truth_by_id:
            raise B4FixtureIntegrityError("B4 ground truth contains duplicate fixture IDs")
        ground_truth_by_id[fixture_id] = item

    inputs: list[_FixtureInput] = []
    seen_fixture_ids: set[str] = set()
    for item in manifest_fixtures:
        if not isinstance(item, dict):
            raise B4FixtureIntegrityError("B4 manifest fixture must be an object")
        fixture_id = _require_string(item, "fixture_id", label="manifest.fixture")
        if fixture_id in seen_fixture_ids or fixture_id not in ground_truth_by_id:
            raise B4FixtureIntegrityError("B4 manifest fixture IDs must be unique and grounded")
        seen_fixture_ids.add(fixture_id)
        expected_taxonomy = _EXPECTED_TAXONOMY[len(inputs)]
        if item.get("taxonomy") != expected_taxonomy:
            raise B4FixtureIntegrityError("B4 manifest taxonomy is not the approved ordered set")
        image_path = _require_relative_file(root, item.get("image_ref"), label="fixture image_ref")
        image_sha256 = _require_string(item, "image_sha256", label="fixture")
        if _sha256_of(image_path) != image_sha256:
            raise B4FixtureIntegrityError(f"B4 image SHA-256 mismatch for {fixture_id}")
        inputs.append(
            _FixtureInput(
                fixture_id=fixture_id,
                image_path=image_path,
                image_sha256=image_sha256,
                ground_truth=ground_truth_by_id[fixture_id],
            )
        )
    if set(ground_truth_by_id) != seen_fixture_ids:
        raise B4FixtureIntegrityError("B4 ground truth and manifest fixture IDs differ")
    for fixture in inputs:
        _validate_ground_truth_references(fixture.ground_truth)
    return (
        _require_string(manifest, "manifest_version", label="manifest"),
        ground_truth_sha256,
        _require_string(matching_rule_metadata, "rule_id", label="matching_rule"),
        matching_rule_sha256,
        tuple(inputs),
    )


def _validate_ground_truth_references(ground_truth: Mapping[str, Any]) -> None:
    """Reject malformed pre-authored references before the adapter sees any fixture."""

    ids_by_collection: dict[str, set[str]] = {}
    all_ids: set[str] = set()
    for collection in _COLLECTIONS:
        ids: set[str] = set()
        for item in _gt_items(ground_truth, collection):
            item_id = _item_id(item, predicted=False)
            if item_id in all_ids:
                raise B4FixtureIntegrityError("B4 ground truth has duplicate item IDs")
            all_ids.add(item_id)
            ids.add(item_id)
        ids_by_collection[collection] = ids
    entity_ids = ids_by_collection["entities"]
    action_ids = ids_by_collection["actions"]
    for item in _gt_items(ground_truth, "actions"):
        for field in ("actor_ref", "object_ref"):
            reference = item.get(field)
            if reference is not None and reference not in entity_ids:
                raise B4FixtureIntegrityError("B4 action reference must target an entity or null")
    entity_or_action_ids = entity_ids | action_ids
    for item in _gt_items(ground_truth, "relations"):
        if (
            item.get("subject_ref") not in entity_or_action_ids
            or item.get("object_ref") not in entity_or_action_ids
        ):
            raise B4FixtureIntegrityError("B4 relation reference must target an entity or action")
    evidence_ids = entity_or_action_ids | ids_by_collection["relations"]
    for item in _gt_items(ground_truth, "themes"):
        references = item.get("evidence_refs")
        if (
            not isinstance(references, list)
            or not references
            or any(reference not in evidence_ids for reference in references)
        ):
            raise B4FixtureIntegrityError("B4 theme evidence references are invalid")


def _write_companion_audio(path: Path) -> None:
    """Write a deterministic synthetic mono WAV that earns a real P2-T1 PASS.

    A local equivalent of the continuous 220 Hz tone already proven against P2-T1 in
    ``vision_b3_mapping_study._write_b3_companion_audio``: a waveform with zero-valued
    samples between peaks produces no adjacent sign changes, so the validator's
    zero-crossing signal reads as zero and the fixture is rejected as having no speech
    signal.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16_000
    seconds = 1.0
    amplitude = 0.3
    frequency_hz = 220
    samples = (
        int(amplitude * 32767 * sin(2 * 3.14159265 * frequency_hz * index / sample_rate))
        for index in range(int(sample_rate * seconds))
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
            image_artifact_ref=f"vision-b4-{fixture_id}-synthetic-image",
            audio_artifact_ref="vision-b4-synthetic-audio",
        )
    )
    if result.decision is not MediaDecision.PASS:
        raise B4FixtureIntegrityError(f"B4 fixture {fixture_id} did not earn a real P2-T1 PASS")
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref=f"vision-b4-{fixture_id}-p2t1-validation",
        validation_artifact_sha256=_sha256_text(result.model_dump_json()),
        decision="PASS",
        validator_policy_version=result.validator_policy_version,
    )


def _normalize(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFC", value).casefold().strip().replace("-", " ").split()
    )


def _item_label(item: object, collection: str) -> str:
    if collection == "relations":
        return (
            item.predicate.value
            if isinstance(item, RelationCandidateV1)
            else _require_gt_text(item, "predicate")
        )
    if collection == "ambiguous_regions":
        return (
            item.note.value
            if isinstance(item, AmbiguousRegionCandidateV1)
            else _require_gt_text(item, "note")
        )
    return (
        item.label.value
        if isinstance(item, (EntityCandidateV1, ActionCandidateV1, ThemeCandidateV1))
        else _require_gt_text(item, "label")
    )


def _require_gt_text(item: object, key: str) -> str:
    if not isinstance(item, dict):
        raise B4FixtureIntegrityError("B4 ground-truth item must be an object")
    value = item.get(key)
    if not isinstance(value, str):
        raise B4FixtureIntegrityError(f"B4 ground-truth {key} must be text")
    return value


def _item_id(item: object, *, predicted: bool) -> str:
    if predicted:
        value = getattr(item, "observation_id", None)
    elif isinstance(item, dict):
        value = item.get("ground_truth_id")
    else:
        value = None
    if not isinstance(value, str):
        raise B4FixtureIntegrityError("B4 scored item has no stable identifier")
    return value


def _maximum_matching(
    predicted: Sequence[object],
    ground_truth: Sequence[object],
    eligible: Callable[[object, object], bool],
) -> dict[str, str]:
    """Maximum-cardinality matching, deterministically preferring GT then prediction IDs.

    The selected V2 contracts do not enforce the C1 prompt's small output caps, so this avoids
    exhaustive matching enumeration. It first computes maximum cardinality with augmenting paths,
    then chooses the lexicographically earliest feasible assignment in stable ground-truth and
    prediction-ID order.
    """

    ordered_ground_truth = sorted(ground_truth, key=lambda item: _item_id(item, predicted=False))
    ordered_predicted = sorted(predicted, key=lambda item: _item_id(item, predicted=True))
    target_count = _maximum_cardinality(
        ordered_ground_truth, ordered_predicted, eligible, unavailable_prediction_ids=frozenset()
    )
    matches: dict[str, str] = {}
    used_prediction_ids: set[str] = set()
    for index, ground_truth_item in enumerate(ordered_ground_truth):
        remaining_ground_truth = ordered_ground_truth[index + 1 :]
        choices = [
            prediction
            for prediction in ordered_predicted
            if _item_id(prediction, predicted=True) not in used_prediction_ids
            and eligible(prediction, ground_truth_item)
        ]
        for prediction in [*choices, None]:
            proposed_used = set(used_prediction_ids)
            proposed_match_count = len(matches)
            if prediction is not None:
                proposed_id = _item_id(prediction, predicted=True)
                proposed_used.add(proposed_id)
                proposed_match_count += 1
            remaining_capacity = _maximum_cardinality(
                remaining_ground_truth,
                ordered_predicted,
                eligible,
                unavailable_prediction_ids=frozenset(proposed_used),
            )
            if proposed_match_count + remaining_capacity != target_count:
                continue
            if prediction is not None:
                prediction_id = _item_id(prediction, predicted=True)
                matches[prediction_id] = _item_id(ground_truth_item, predicted=False)
                used_prediction_ids.add(prediction_id)
            break
        else:  # pragma: no cover - target cardinality guarantees a feasible choice
            raise AssertionError("maximum matching could not preserve its computed cardinality")
    return matches


def _maximum_cardinality(
    ground_truth: Sequence[object],
    predicted: Sequence[object],
    eligible: Callable[[object, object], bool],
    *,
    unavailable_prediction_ids: frozenset[str],
) -> int:
    """Return bipartite maximum cardinality with polynomial augmenting-path matching."""

    matched_ground_truth_by_prediction: dict[str, object] = {}

    def augment(ground_truth_item: object, visited_prediction_ids: set[str]) -> bool:
        for prediction in predicted:
            prediction_id = _item_id(prediction, predicted=True)
            if (
                prediction_id in unavailable_prediction_ids
                or prediction_id in visited_prediction_ids
                or not eligible(prediction, ground_truth_item)
            ):
                continue
            visited_prediction_ids.add(prediction_id)
            incumbent = matched_ground_truth_by_prediction.get(prediction_id)
            if incumbent is None or augment(incumbent, visited_prediction_ids):
                matched_ground_truth_by_prediction[prediction_id] = ground_truth_item
                return True
        return False

    return sum(augment(item, set()) for item in ground_truth)


def _gt_items(ground_truth: Mapping[str, Any], collection: str) -> tuple[Mapping[str, Any], ...]:
    value = ground_truth.get(collection)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise B4FixtureIntegrityError(f"B4 ground truth {collection} must be an object list")
    return tuple(value)


def _score_collection(
    predicted: Sequence[object],
    ground_truth: Sequence[object],
    matches: Mapping[str, str],
    *,
    ambiguous: bool = False,
) -> B4CollectionScore:
    ground_truth_count = len(ground_truth)
    predicted_count = len(predicted)
    matched_count = len(matches)
    coverage = matched_count / ground_truth_count if ground_truth_count else None
    accuracy = None if ambiguous or not predicted_count else matched_count / predicted_count
    return B4CollectionScore(
        ground_truth_count=ground_truth_count,
        predicted_count=predicted_count,
        matched_count=matched_count,
        coverage=coverage,
        accuracy=accuracy,
    )


def _score_success(
    result: VisionUnderstandingSuccessV2, ground_truth: Mapping[str, Any]
) -> Mapping[str, B4CollectionScore]:
    entities_gt = _gt_items(ground_truth, "entities")
    entity_matches = _maximum_matching(
        result.entities,
        entities_gt,
        lambda predicted, expected: (
            _normalize(_item_label(predicted, "entities"))
            == _normalize(_item_label(expected, "entities"))
        ),
    )

    def action_eligible(predicted: object, expected: object) -> bool:
        if not isinstance(predicted, ActionCandidateV1) or not isinstance(expected, dict):
            return False
        if _normalize(_item_label(predicted, "actions")) != _normalize(
            _item_label(expected, "actions")
        ):
            return False
        return all(
            _endpoint_matches(getattr(predicted, field), expected.get(field), entity_matches)
            for field in ("actor_ref", "object_ref")
        )

    actions_gt = _gt_items(ground_truth, "actions")
    action_matches = _maximum_matching(result.actions, actions_gt, action_eligible)
    resolved = {**entity_matches, **action_matches}

    def relation_eligible(predicted: object, expected: object) -> bool:
        if not isinstance(predicted, RelationCandidateV1) or not isinstance(expected, dict):
            return False
        return (
            _normalize(_item_label(predicted, "relations"))
            == _normalize(_item_label(expected, "relations"))
            and resolved.get(predicted.subject_ref) == expected.get("subject_ref")
            and resolved.get(predicted.object_ref) == expected.get("object_ref")
        )

    relations_gt = _gt_items(ground_truth, "relations")
    relation_matches = _maximum_matching(result.relations, relations_gt, relation_eligible)
    resolved = {**resolved, **relation_matches}

    def theme_eligible(predicted: object, expected: object) -> bool:
        if not isinstance(predicted, ThemeCandidateV1) or not isinstance(expected, dict):
            return False
        expected_refs = expected.get("evidence_refs")
        if not isinstance(expected_refs, list):
            return False
        resolved_refs = tuple(resolved.get(reference) for reference in predicted.evidence_refs)
        return (
            _normalize(_item_label(predicted, "themes"))
            == _normalize(_item_label(expected, "themes"))
            and len(resolved_refs) == len(expected_refs)
            and set(resolved_refs) == set(expected_refs)
        )

    themes_gt = _gt_items(ground_truth, "themes")
    theme_matches = _maximum_matching(result.themes, themes_gt, theme_eligible)
    ambiguous_gt = _gt_items(ground_truth, "ambiguous_regions")
    ambiguous_matches = _maximum_matching(
        result.ambiguous_regions,
        ambiguous_gt,
        lambda predicted, expected: (
            _normalize(_item_label(predicted, "ambiguous_regions"))
            == _normalize(_item_label(expected, "ambiguous_regions"))
        ),
    )
    return {
        "entities": _score_collection(result.entities, entities_gt, entity_matches),
        "actions": _score_collection(result.actions, actions_gt, action_matches),
        "relations": _score_collection(result.relations, relations_gt, relation_matches),
        "themes": _score_collection(result.themes, themes_gt, theme_matches),
        "ambiguous_regions": _score_collection(
            result.ambiguous_regions, ambiguous_gt, ambiguous_matches, ambiguous=True
        ),
    }


def _endpoint_matches(predicted: str | None, expected: object, resolved: Mapping[str, str]) -> bool:
    if expected is None:
        return predicted is None
    return predicted is not None and resolved.get(predicted) == expected


def _aggregate(
    scores: Sequence[Mapping[str, B4CollectionScore]],
) -> Mapping[str, B4CollectionScore]:
    aggregates: dict[str, B4CollectionScore] = {}
    for collection in _COLLECTIONS:
        collection_scores = [score[collection] for score in scores]
        ground_truth_count = sum(item.ground_truth_count for item in collection_scores)
        predicted_count = sum(item.predicted_count for item in collection_scores)
        matched_count = sum(item.matched_count for item in collection_scores)
        aggregates[collection] = B4CollectionScore(
            ground_truth_count=ground_truth_count,
            predicted_count=predicted_count,
            matched_count=matched_count,
            coverage=matched_count / ground_truth_count if ground_truth_count else None,
            accuracy=(
                None
                if collection == "ambiguous_regions" or not predicted_count
                else matched_count / predicted_count
            ),
        )
    return aggregates


class _VramSampler:
    """Best-effort device-wide VRAM sampler; unavailable is never represented as zero."""

    def __init__(self) -> None:
        self._stop = Event()
        self._samples: list[float] = []
        self._thread = Thread(target=self._sample, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop_and_get_peak_mb(self) -> float | None:
        self._stop.set()
        self._thread.join()
        return max(self._samples) if self._samples else None

    def _sample(self) -> None:
        while not self._stop.is_set():
            try:
                output = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                self._samples.extend(
                    float(value.strip()) for value in output.splitlines() if value.strip()
                )
            except (OSError, subprocess.CalledProcessError, ValueError):
                return
            self._stop.wait(0.05)


def _classification_required(result: VisionUnderstandingResultV2) -> bool:
    if isinstance(result, VisionUnderstandingSuccessV2):
        return True
    assert isinstance(result, VisionUnderstandingFailureV2)
    return result.error_code is VisionErrorCode.PROHIBITED_CLAIM_DETECTED or (
        result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID
        and result.error_detail.value
        in {"OUTPUT_MAPPING_FAILED", "DUPLICATE_OBSERVATION_ID", "REFERENCE_INTEGRITY_VIOLATION"}
    )


def _verify_prompt(prompt: C1PromptProtocol) -> str:
    if (prompt.protocol_id, prompt.prompt_sha256) != (
        C1_PROMPT_V2.protocol_id,
        C1_PROMPT_V2.prompt_sha256,
    ):
        raise B4PromptBindingError("B4 requires the exact approved C1-v2 prompt identity")
    text = prompt.prompt_text_provider()
    if _sha256_text(text) != prompt.prompt_sha256:
        raise B4PromptBindingError("B4 prompt text does not match its approved SHA-256")
    return text


def run_b4_quality_pass(
    adapter_factory: C1AdapterFactory,
    collector: B3RawOutputCollector,
    *,
    run_label: B4RunLabel,
    prompt: C1PromptProtocol = C1_PROMPT_V2,
    fixture_root: Path = _DEFAULT_FIXTURE_ROOT,
    runtime_dir: Path | None = None,
    sample_vram: bool = True,
    validate_media: MediaValidationFactory = _real_p2t1_pass,
) -> B4QualityPassReport:
    """Run exactly one locally prepared B4 pass; callers must separately invoke the repeat.

    This verifies all package hashes and all eight P2-T1 PASS provenances before constructing the
    adapter, then makes exactly one call per fixture with no retry.  It cleans only its generated
    companion-audio scratch directory, never the held-out fixture package.
    """

    if run_label not in _DEFAULT_RUNTIME_DIRS:
        raise B4InvalidRunLabelError("B4 run_label must be B4_PASS_1 or B4_REPEAT_1")
    prompt_text = _verify_prompt(prompt)
    manifest_version, gt_hash, rule_id, rule_hash, fixtures = _load_fixture_package(fixture_root)
    resolved_runtime_dir = runtime_dir or _DEFAULT_RUNTIME_DIRS[run_label]
    _require_safe_runtime_directory(resolved_runtime_dir)

    try:
        audio_path = resolved_runtime_dir / "b4-companion.wav"
        _write_companion_audio(audio_path)
        provenances = {
            fixture.fixture_id: validate_media(fixture.fixture_id, fixture.image_path, audio_path)
            for fixture in fixtures
        }
        adapter: VisionUnderstandingPortV2 = adapter_factory(prompt_text, collector.hook)
        runs: list[B4FixtureRunResult] = []
        typed_failures: dict[str, int] = {}
        scores: list[Mapping[str, B4CollectionScore]] = []
        schema_valid_count = lossless_unwrap_recovered_count = 0
        fenced_count = truncated_count = extra_key_count = invalid_enum_count = 0
        for fixture in fixtures:
            request = VisionUnderstandingRequestV2(
                correlation_id=f"vision-{run_label.lower().replace('_', '-')}-{fixture.fixture_id}",
                source_image_ref=VisionImageReferenceV1(
                    artifact_ref=f"vision-b4-{fixture.fixture_id}-synthetic-image",
                    sha256=fixture.image_sha256,
                ),
                media_validation=provenances[fixture.fixture_id],
                requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
            )
            collector.take_latest()
            sampler = _VramSampler() if sample_vram else None
            if sampler is not None:
                sampler.start()
            peak_vram_mb: float | None = None
            try:
                started = time.perf_counter()
                result = adapter.understand(request)
                latency_ms = (time.perf_counter() - started) * 1000.0
            finally:
                if sampler is not None:
                    peak_vram_mb = sampler.stop_and_get_peak_mb()
            classification = collector.take_latest()
            if classification is None and _classification_required(result):
                raise B4RawOutputHookNotWiredError(
                    f"{fixture.fixture_id}: a raw-producing typed result had no safe classification"
                )
            if isinstance(result, VisionUnderstandingSuccessV2):
                error_code = error_detail = None
                collection_scores = _score_success(result, fixture.ground_truth)
                scores.append(collection_scores)
                schema_valid_count += 1
                if result.repair_attempted:
                    lossless_unwrap_recovered_count += 1
            else:
                assert isinstance(result, VisionUnderstandingFailureV2)
                error_code = result.error_code.value
                error_detail = result.error_detail.value
                typed_failures[error_detail] = typed_failures.get(error_detail, 0) + 1
                collection_scores = None
            if classification is not None:
                fenced_count += int(classification.fenced)
                truncated_count += int(classification.truncated)
                extra_key_count += int(classification.extra_key)
                invalid_enum_count += int(classification.invalid_enum)
            runs.append(
                B4FixtureRunResult(
                    fixture_id=fixture.fixture_id,
                    status=result.status,
                    error_code=error_code,
                    error_detail=error_detail,
                    attempt_number=result.attempt_number,
                    repair_attempted=result.repair_attempted,
                    wall_latency_ms=latency_ms,
                    peak_vram_mb=peak_vram_mb,
                    vram_not_measured_reason=(
                        None
                        if sample_vram and peak_vram_mb is not None
                        else (
                            "nvidia-smi was unavailable or returned no sample"
                            if sample_vram
                            else "VRAM sampling was disabled for this call"
                        )
                    ),
                    fenced=classification.fenced if classification is not None else None,
                    truncated=classification.truncated if classification is not None else None,
                    extra_key=classification.extra_key if classification is not None else None,
                    invalid_enum=classification.invalid_enum
                    if classification is not None
                    else None,
                    collection_scores=collection_scores,
                )
            )
    finally:
        shutil.rmtree(resolved_runtime_dir, ignore_errors=True)
        collector.cleanup()

    catalog = vision_profile_catalog_v2()
    return B4QualityPassReport(
        run_label=run_label,
        manifest_version=manifest_version,
        ground_truth_sha256=gt_hash,
        matching_rule_id=rule_id,
        matching_rule_sha256=rule_hash,
        prompt_protocol_id=prompt.protocol_id,
        prompt_sha256=prompt.prompt_sha256,
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
        aggregate_collection_scores=_aggregate(scores),
        runs=tuple(runs),
    )


__all__ = [
    "B4CollectionScore",
    "B4FixtureIntegrityError",
    "B4FixtureRunResult",
    "B4InvalidRunLabelError",
    "B4PromptBindingError",
    "B4QualityPassReport",
    "B4RawOutputHookNotWiredError",
    "run_b4_quality_pass",
]
