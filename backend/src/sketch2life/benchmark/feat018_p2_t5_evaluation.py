"""Bounded FEAT-018 offline diagnostics; these results never close full Task 5.

Only synthetic contract values and injected transports are used. Network guards are
process-level tripwires, not an OS sandbox. No model, provider or Git command runs.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
from collections import Counter
from collections.abc import Iterator, Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from email.message import Message
from hashlib import sha256
from pathlib import Path
from struct import pack
from typing import Any
from unittest.mock import patch
from urllib.error import HTTPError
from zlib import compress, crc32

from pydantic import ValidationError

from sketch2life.application.services.image_admission import (
    Feat018AdmissionRequest,
    Feat018ImageAdmission,
)
from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.application.services.raw_understanding_mapper import (
    RawUnderstandingMappingError,
    map_vision_result_to_raw,
)
from sketch2life.contracts.schemas.asr import (
    AsrAudioReferenceV1,
    AsrErrorCode,
    AsrErrorDetail,
    AsrFailureV1,
    AsrProfileId,
    AsrQualityMetadataV1,
    AsrRequestV1,
    AsrSegmentV1,
    AsrSpeechDiagnostic,
    AsrSuccessV1,
    MediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.raw_understanding import (
    RawConflictCode,
    RawConflictV1,
    RawNarrationStatus,
    RawUnderstandingFailureV1,
    RawUnderstandingSuccessV1,
)
from sketch2life.contracts.schemas.vision import (
    VISION_POLICY_MATCH_VIEW_VERSION,
    AmbiguousRegionCandidateV1,
    EntityCandidateV1,
    ObservedTextV1,
    TextLanguageDeclarationV1,
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
    VisionProhibitedClaimCategory,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.domain.understanding.media_quality import (
    AudioQualitySignals,
    ImageQualitySignals,
)
from sketch2life.infrastructure.ai.lightning_client import (
    LightningAsrV2Adapter,
    LightningProviderError,
    UrllibJsonTransport,
)
from sketch2life.infrastructure.ai.lightning_vision_v2 import LightningVisionV2Adapter
from sketch2life.infrastructure.media_validation.av_image_decoder import AvImageDecoder

_FEATURE = "features/FEAT-018-live-image-canvas-flow"
_PILOTS = frozenset(
    f"ACT-{number:04d}"
    for number in (4, 16, 19, 20, 23, 26, 30, 33, 39, 46, 55, 58, 61, 67, 74, 85, 87, 91, 97, 99)
)
FAMILIES = ("exact", "ambiguous", "no-match", "conflict", "low", "adult-correction")
HELD_KINDS = frozenset(
    {"adult_correction_held", "orientation_held", "os_error_held", "stale_session_held",
     "mobile_bundle_held", "live_run_held"}
)
PROBE_KINDS = frozenset(
    {"map_exact", "map_ambiguous", "map_unknown_label", "map_asr_present",
     "raw_conflict_schema", "map_low_confidence", "reject_null_confidence",
     "asr_missing", "asr_failure", "asr_only_contract", "reject_malformed",
     "reject_prohibited", "reject_extra_field", "reject_missing_provenance",
     "reject_source_hash", "reject_dangling_reference", "vision_timeout",
     "vision_terminal_retry_fixture", "rate_limit_characterization",
     "provider_error_characterization", "quality_valid", "quality_dark",
     "quality_blur", "quality_crop", "admission_valid", "admission_corrupt",
     "admission_unsupported", "admission_oversized"}
) | HELD_KINDS
_FAMILY_PROBES = {
    "exact": {"map_exact"}, "ambiguous": {"map_ambiguous"},
    "no-match": {"map_unknown_label"},
    "conflict": {"map_asr_present", "raw_conflict_schema"},
    "low": {"map_low_confidence", "reject_null_confidence"},
    "adult-correction": {"adult_correction_held"},
}
_SUPPLEMENTAL_KINDS = PROBE_KINDS - frozenset().union(*_FAMILY_PROBES.values())
_PARTIAL_SUPPLEMENTALS = HELD_KINDS | {
    "asr_only_contract", "vision_terminal_retry_fixture", "rate_limit_characterization",
    "provider_error_characterization",
}
_LOCKS = {
    "backend/src/sketch2life/contracts/schemas/vision_v2.py":
        ("VisionUnderstandingResultV2", "2.0",
         "bea0511c400b452b86ff32a90cb5f65df4c191a72a857b1024c30a65628cd0d8"),
    "backend/src/sketch2life/contracts/schemas/raw_understanding.py":
        ("RawUnderstandingResultV1", "1.0",
         "9a5350a7a6913c2fc4f9f3008aa3bceba652d90cd25f3cfe76f598b053a57e0b"),
    "backend/src/sketch2life/contracts/schemas/asr.py":
        ("AsrResultV1", "1.0",
         "1dcf8db144ebfd080266f05b8e75ae404ec230edc7983937a0e598e48c0b9b22"),
}
_ASR_PORT = "backend/src/sketch2life/application/ports/asr.py"
_ASR_PORT_SHA = "92e9e68aa7c428a72cc366ff540f4d5f1bf3bfa2605aec059b9dc20e9e84f9d6"
_SOURCE_LOCKS = {
    _ASR_PORT: _ASR_PORT_SHA,
    f"{_FEATURE}/plan/ACTIVITY_PILOT_MATRIX.md":
        "85562043a694d72a6aa1f8510618ebf4548b05308f9ad1457f8321199895ef12",
    "tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json":
        "1ba728ca3b02646bafd6b75d27b6c70461957ceb8628ec8e75f11e3aea62bd5a",
}
_CODE_PATHS = (
    "backend/src/sketch2life/benchmark/feat018_p2_t5_evaluation.py",
    "backend/tests/unit/test_feat018_p2_t5_evaluation.py",
    "backend/tests/contract/test_feat018_p2_t5_manifest_contract.py",
    "backend/tests/contract/test_live_image_demo_api.py",
    "backend/src/sketch2life/application/services/raw_understanding_mapper.py",
    "backend/src/sketch2life/application/services/media_validation.py",
    "backend/src/sketch2life/application/services/image_admission.py",
    "backend/src/sketch2life/domain/understanding/image_admission.py",
    "backend/src/sketch2life/domain/understanding/media_quality.py",
    "backend/src/sketch2life/contracts/schemas/vision.py",
    "backend/src/sketch2life/infrastructure/ai/lightning_client.py",
    "backend/src/sketch2life/infrastructure/ai/lightning_vision_v2.py",
    "backend/src/sketch2life/infrastructure/media_validation/av_image_decoder.py",
)
_TIME = datetime(2026, 10, 22, 0, 0, tzinfo=UTC)
_IMAGE = b"\x89PNG\r\n\x1a\nfeat018-offline-synthetic-only"
_AUDIO = b"feat018-offline-synthetic-audio-only"
_SHA = sha256(_IMAGE).hexdigest()
_CORRELATION = "feat018-p2-t5-synthetic"


class ManifestError(ValueError):
    """A sanitized, fail-closed source or manifest rejection."""


class OfflineAccessError(RuntimeError):
    """An unexpected network/process/provider route was attempted."""


@dataclass
class OfflineGuard:
    blocked_attempts: int = 0

    def refuse(self, *_args: Any, **_kwargs: Any) -> Any:
        self.blocked_attempts += 1
        raise OfflineAccessError("OFFLINE_ACCESS_REFUSED")


@contextmanager
def offline_guards() -> Iterator[OfflineGuard]:
    """Trip at common egress and subprocess seams, including transport's imported alias."""
    guard = OfflineGuard()
    targets = (
        "socket.socket.connect", "socket.socket.connect_ex", "socket.create_connection",
        "socket.getaddrinfo", "urllib.request.urlopen", "subprocess.Popen",
        "sketch2life.infrastructure.ai.lightning_client.urlopen",
    )
    with ExitStack() as stack:
        for target in targets:
            stack.enter_context(patch(target, guard.refuse))
        yield guard


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _source_path(repo_root: Path, value: Any) -> Path:
    if not isinstance(value, str) or "\\" in value or ":" in value:
        raise ManifestError("INVALID_SOURCE_PATH")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ManifestError("INVALID_SOURCE_PATH")
    resolved = (repo_root / relative).resolve()
    if not resolved.is_relative_to(repo_root.resolve()) or not resolved.is_file():
        raise ManifestError("SOURCE_NOT_AVAILABLE")
    return resolved


def _mapping(value: Any, error: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(error)
    return value


def _array(value: Any, error: str) -> list[Any]:
    if not isinstance(value, list):
        raise ManifestError(error)
    return value


def load_manifest(path: Path, repo_root: Path) -> dict[str, Any]:
    """Validate identity, every source lock and all 120 slots before any probe executes."""
    try:
        manifest = _mapping(json.loads(path.read_text(encoding="utf-8")), "INVALID_MANIFEST")
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ManifestError("MANIFEST_NOT_READABLE") from None
    if manifest.get("schema_version") != "1.0":
        raise ManifestError("UNSUPPORTED_MANIFEST_VERSION")
    if (manifest.get("approval_id") != "FEAT018_P2T5_BOUNDED_OFFLINE_APPROVAL_01" or
            manifest.get("approved_source_plan_revision") != "0.9" or
            manifest.get("approved_source_plan_sha256") !=
            "6E9550A045D9FC382F83FEACC0ACAF9B55A4423A5DE99C30E437C48071A1951E" or
            manifest.get("baseline_head") != "b11bc7b870f615e493afb1bc723b888befdb58c9"):
        raise ManifestError("APPROVAL_IDENTITY_MISMATCH")
    if (manifest.get("provider_execution") != "NOT_EXECUTED" or
            manifest.get("live_metrics") != "NOT_MEASURED" or
            manifest.get("full_task_status") != "OPEN"):
        raise ManifestError("UNSUPPORTED_EXECUTION_OR_CLOSURE_CLAIM")
    locks = _array(manifest.get("contract_locks"), "INVALID_CONTRACT_LOCKS")
    found: set[str] = set()
    for item in locks:
        lock = _mapping(item, "INVALID_CONTRACT_LOCK")
        source = lock.get("path")
        if not isinstance(source, str) or source not in _LOCKS or source in found:
            raise ManifestError("INVALID_CONTRACT_SET")
        expected_contract, version, digest = _LOCKS[source]
        if (lock.get("contract"), lock.get("version")) != (expected_contract, version):
            raise ManifestError("CONTRACT_IDENTITY_MISMATCH")
        if str(lock.get("sha256", "")).lower() != digest:
            raise ManifestError("CONTRACT_LOCK_MISMATCH")
        if _digest(_source_path(repo_root, source)) != digest:
            raise ManifestError("CONTRACT_SOURCE_CHANGED")
        found.add(source)
    if found != set(_LOCKS):
        raise ManifestError("INCOMPLETE_CONTRACT_LOCKS")
    source_locks = _array(manifest.get("source_locks"), "INVALID_SOURCE_LOCKS")
    seen_sources: set[str] = set()
    for item in source_locks:
        lock = _mapping(item, "INVALID_SOURCE_LOCK")
        source = lock.get("path")
        if not isinstance(source, str) or source in seen_sources or source not in _SOURCE_LOCKS:
            raise ManifestError("DUPLICATE_SOURCE_LOCK")
        actual = _digest(_source_path(repo_root, source))
        if actual != str(lock.get("sha256", "")).lower() or actual != _SOURCE_LOCKS[source]:
            raise ManifestError("PLANNING_SOURCE_CHANGED")
        if source == _ASR_PORT and actual != _ASR_PORT_SHA:
            raise ManifestError("ASR_PORT_SOURCE_CHANGED")
        seen_sources.add(source)
    if seen_sources != set(_SOURCE_LOCKS):
        raise ManifestError("MISSING_REQUIRED_SOURCE_LOCK")
    recipe_path = _source_path(
        repo_root, "tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json")
    recipe_source = json.loads(recipe_path.read_text(encoding="utf-8"))
    source_phrases = {case["activity_id"]: case["profile"]["exact_phrase"]
                      for case in recipe_source["primary_cases"] if case["family"] == "EXACT"}
    pilots = _array(manifest.get("pilots"), "INVALID_PILOTS")
    pilot_ids = [str(_mapping(p, "INVALID_PILOT").get("activity_id")) for p in pilots]
    if len(pilot_ids) != 20 or set(pilot_ids) != _PILOTS:
        raise ManifestError("INVALID_PILOT_SET")
    if any(p.get("activity_version") != 2 for p in pilots):
        raise ManifestError("PILOT_VERSION_MISMATCH")
    if any(p.get("exact_phrase") != source_phrases[p["activity_id"]] for p in pilots):
        raise ManifestError("PILOT_RECIPE_MISMATCH")
    profiles = _array(manifest.get("profiles"), "INVALID_PROFILES")
    if len(profiles) != 120:
        raise ManifestError("INVALID_SLOT_COUNT")
    identities: set[str] = set()
    cells: set[tuple[str, str]] = set()
    supplemental_kinds: set[str] = set()
    all_rows = profiles + _array(manifest.get("supplemental_cases"), "INVALID_SUPPLEMENTALS")
    for row_value in all_rows:
        row = _mapping(row_value, "INVALID_PROFILE")
        fixture_id = row.get("fixture_id")
        if (not isinstance(fixture_id, str) or
                not re.fullmatch(r"feat018-p2-t5-[a-z0-9-]+", fixture_id) or
                fixture_id in identities):
            raise ManifestError("INVALID_OR_DUPLICATE_FIXTURE_ID")
        identities.add(fixture_id)
        if row.get("evidence_id") != f"P2T5:{fixture_id}":
            raise ManifestError("EVIDENCE_IDENTITY_MISMATCH")
        if row in profiles:
            activity, family = row.get("activity_id"), row.get("family")
            if (not isinstance(activity, str) or not isinstance(family, str) or
                    activity not in _PILOTS or family not in FAMILIES):
                raise ManifestError("INVALID_MATRIX_CELL")
            if fixture_id != f"feat018-p2-t5-{activity.lower()}-{family}":
                raise ManifestError("FIXTURE_IDENTITY_MISMATCH")
            cell = (str(activity), str(family))
            if cell in cells:
                raise ManifestError("DUPLICATE_MATRIX_CELL")
            cells.add(cell)
            recipe = _mapping(row.get("recipe"), "INVALID_RECIPE")
            if recipe.get("activity_version") != 2:
                raise ManifestError("PILOT_VERSION_MISMATCH")
            if not isinstance(recipe.get("exact_phrase"), str) or not recipe["exact_phrase"]:
                raise ManifestError("MISSING_SYNTHETIC_RECIPE")
            if recipe["exact_phrase"] != source_phrases[activity]:
                raise ManifestError("PILOT_RECIPE_MISMATCH")
            source_case = ("tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json"
                           f"#feat018-p2-t4-{activity.lower()}-{family}")
            if row.get("planning_source_case_id") != source_case:
                raise ManifestError("PLANNING_SOURCE_IDENTITY_MISMATCH")
            if row.get("requirement_status") != ("OPEN" if family == "exact" else "HELD"):
                raise ManifestError("PRIMARY_DISPOSITION_CHANGED")
        if row.get("requirement_status") not in {"OPEN", "HELD"}:
            raise ManifestError("UNSUPPORTED_REQUIREMENT_CLAIM")
        if row.get("coverage_credit") is not None and row.get("coverage_credit") is not False:
            raise ManifestError("UNSUPPORTED_COVERAGE_CLAIM")
        acceptance_ids = _array(row.get("acceptance_ids"), "INVALID_ACCEPTANCE_IDS")
        if not acceptance_ids or any(not isinstance(item, str) or
                                      not re.fullmatch(r"T5-A[1-9]", item)
                                      for item in acceptance_ids):
            raise ManifestError("INVALID_ACCEPTANCE_IDS")
        expected_execution = row.get("expected_execution_status")
        if expected_execution not in {"EXECUTE", "NOT_EXECUTED"}:
            raise ManifestError("INVALID_EXECUTION_EXPECTATION")
        probes = _array(row.get("subprobes"), "INVALID_SUBPROBES")
        if not probes:
            raise ManifestError("MISSING_SUBPROBES")
        probe_ids: set[str] = set()
        for probe_value in probes:
            probe = _mapping(probe_value, "INVALID_SUBPROBE")
            kind, probe_id = probe.get("kind"), probe.get("probe_id")
            if kind not in PROBE_KINDS:
                raise ManifestError("UNSUPPORTED_PROBE")
            if not isinstance(probe_id, str) or probe_id != f"{fixture_id}:{kind}":
                raise ManifestError("INVALID_PROBE_ID")
            if probe_id in probe_ids:
                raise ManifestError("DUPLICATE_PROBE_ID")
            probe_ids.add(probe_id)
            expected = "NOT_EXECUTED" if kind in HELD_KINDS else str(kind).upper()
            if probe.get("expected_outcome") != expected:
                raise ManifestError("UNSUPPORTED_EXPECTED_OUTCOME")
            if probe.get("requirement_status") not in {"OPEN", "HELD"}:
                raise ManifestError("UNSUPPORTED_SUBPROBE_REQUIREMENT")
            if kind in HELD_KINDS and probe.get("requirement_status") != "HELD":
                raise ManifestError("HELD_PROBE_CANNOT_BE_COVERAGE")
            if kind not in HELD_KINDS and probe.get("requirement_status") != "OPEN":
                raise ManifestError("SUBPROBE_DISPOSITION_CHANGED")
        kinds = {probe["kind"] for probe in probes}
        if row in profiles:
            if kinds != _FAMILY_PROBES[row["family"]]:
                raise ManifestError("FAMILY_SUBPROBE_MISMATCH")
        else:
            if len(probes) != 1 or not kinds.issubset(_SUPPLEMENTAL_KINDS):
                raise ManifestError("INVALID_SUPPLEMENTAL_SET")
            only_kind = probes[0]["kind"]
            if only_kind in supplemental_kinds:
                raise ManifestError("DUPLICATE_SUPPLEMENTAL")
            supplemental_kinds.add(only_kind)
            if fixture_id != f"feat018-p2-t5-supplemental-{only_kind.replace('_', '-')}":
                raise ManifestError("SUPPLEMENTAL_IDENTITY_MISMATCH")
            expected_requirement = "HELD" if only_kind in _PARTIAL_SUPPLEMENTALS else "OPEN"
            if row["requirement_status"] != expected_requirement:
                raise ManifestError("SUPPLEMENTAL_DISPOSITION_CHANGED")
        all_held = all(probe["kind"] in HELD_KINDS for probe in probes)
        if (expected_execution == "NOT_EXECUTED") != all_held:
            raise ManifestError("EXECUTION_EXPECTATION_MISMATCH")
        if row.get("family") == "adult-correction":
            if expected_execution != "NOT_EXECUTED" or row["requirement_status"] != "HELD":
                raise ManifestError("ADULT_CORRECTION_MUST_REMAIN_HELD")
            if any(p["kind"] != "adult_correction_held" for p in probes):
                raise ManifestError("ADULT_BOUNDARY_NOT_APPROVED")
    if cells != {(pilot, family) for pilot in _PILOTS for family in FAMILIES}:
        raise ManifestError("INCOMPLETE_MATRIX")
    if supplemental_kinds != _SUPPLEMENTAL_KINDS:
        raise ManifestError("INCOMPLETE_SUPPLEMENTALS")
    return manifest


def _text(value: str) -> ObservedTextV1:
    return ObservedTextV1(value=value, language=TextLanguageDeclarationV1(status="NOT_DETERMINED"))


def _success(label: str = "synthetic observation", *, confidence: float | None = 0.85,
             ambiguous: bool = False) -> VisionUnderstandingSuccessV2:
    catalog = vision_profile_catalog_v2()
    profile = catalog.profiles[0]
    return VisionUnderstandingSuccessV2(
        correlation_id=_CORRELATION, executed_at=_TIME,
        source_image_ref=VisionImageReferenceV1(artifact_ref="synthetic:image", sha256=_SHA),
        profile_id=profile.profile_id, profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
        attempt_number=1, repair_attempted=False,
        content_policy_version="synthetic-policy-v1",
        policy_match_view_version=VISION_POLICY_MATCH_VIEW_VERSION,
        policy_execution_state="PASSED", adapter_version=profile.adapter_version,
        config_hash=vision_profile_config_hash_v2(profile),
        model_provenance=profile.model_provenance,
        entities=(EntityCandidateV1(observation_id="entity-1", label=_text(label),
                                    confidence=confidence),),
        actions=(), relations=(), themes=(),
        ambiguous_regions=(AmbiguousRegionCandidateV1(observation_id="ambiguous-1",
                            note=_text("synthetic ambiguous observation")),) if ambiguous else (),
    )


def _map(result: VisionUnderstandingSuccessV2 | VisionUnderstandingFailureV2,
         asr: AsrSuccessV1 | AsrFailureV1 | None = None,
         *, expected_hash: str = _SHA) -> RawUnderstandingSuccessV1 | RawUnderstandingFailureV1:
    return map_vision_result_to_raw(result, session_id="synthetic-session",
                                   expected_source_sha256=expected_hash,
                                   expected_correlation_id=_CORRELATION, asr_result=asr)


def _asr_success() -> AsrSuccessV1:
    return AsrSuccessV1(
        correlation_id=_CORRELATION, executed_at=_TIME,
        source_audio_ref=AsrAudioReferenceV1(artifact_ref="synthetic:audio",
                                           sha256=sha256(_AUDIO).hexdigest()),
        profile_id=AsrProfileId.FAKE_DETERMINISTIC_V1, attempt_number=1, repair_attempted=False,
        transcript_raw="synthetic narration", speech_diagnostic=AsrSpeechDiagnostic.DETECTED,
        detected_language="en", segments=(AsrSegmentV1(index=0, start_seconds=0,
        end_seconds=1, text="synthetic narration"),), input_duration_seconds=1,
        vad_enabled=False, model_identifier="synthetic-fixture", model_revision="fixture-v1",
        adapter_version="fixture-v1", runtime_version="none", config_hash="c" * 64,
        quality_metadata=AsrQualityMetadataV1(media_validation_artifact_ref="synthetic:validation",
                                              media_validation_artifact_sha256="d" * 64),
    )


def _asr_failure() -> AsrFailureV1:
    return AsrFailureV1(
        correlation_id=_CORRELATION, executed_at=_TIME,
        source_audio_ref=_asr_success().source_audio_ref,
        profile_id=AsrProfileId.FAKE_DETERMINISTIC_V1, attempt_number=1,
        repair_attempted=False, error_code=AsrErrorCode.ASR_TIMEOUT,
        error_detail=AsrErrorDetail.TIMEOUT_BUDGET_EXCEEDED, retryable=False,
    )


def _asr_metadata(result: AsrSuccessV1 | AsrFailureV1) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "source_audio_sha256": result.source_audio_ref.sha256,
        "asr_profile_id": result.profile_id.value,
        "asr_result_sha256": sha256(json.dumps(
            result.model_dump(mode="json"), ensure_ascii=True,
            sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "full_asr_provenance_proven_from_raw": False,
    }
    if isinstance(result, AsrSuccessV1):
        metadata["asr_config_hash"] = result.config_hash
    return metadata


def _vision_request() -> VisionUnderstandingRequestV2:
    success = _success()
    return VisionUnderstandingRequestV2(
        correlation_id=_CORRELATION, source_image_ref=success.source_image_ref,
        requested_profile_id=success.profile_id,
        media_validation=VisionMediaValidationProvenanceV1(
            validation_artifact_ref="synthetic:validation",
            validation_artifact_sha256="d" * 64, decision="PASS",
            validator_policy_version="synthetic-v1"),
    )


def _asr_request() -> AsrRequestV1:
    return AsrRequestV1(
        correlation_id=_CORRELATION, source_audio_ref=_asr_success().source_audio_ref,
        requested_profile_id=AsrProfileId.FAKE_DETERMINISTIC_V1,
        media_validation=MediaValidationProvenanceV1(
            validation_artifact_ref="synthetic:validation",
            validation_artifact_sha256="d" * 64, decision="PASS",
            validator_policy_version="synthetic-v1"),
    )


class _ErrorTransport:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls = 0

    def post_json(self, _path: str, _payload: Mapping[str, object]) -> Mapping[str, object]:
        self.calls += 1
        raise self.error


def _require(condition: bool, diagnostic: str) -> None:
    if not condition:
        raise AssertionError(diagnostic)


def _expect_rejection(action: Any) -> None:
    try:
        action()
    except (ValidationError, RawUnderstandingMappingError, json.JSONDecodeError):
        return
    raise AssertionError("EXPECTED_REJECTION_NOT_OBSERVED")


def _assert_gate_a(raw: RawUnderstandingSuccessV1) -> None:
    _require(raw.gate_a_required is True, "GATE_A_REQUIRED")
    for field, value in (("gate_a_required", False), ("gate_b", {}), ("eligibility", True)):
        data = raw.model_dump(mode="json")
        data[field] = value
        _expect_rejection(lambda data=data: RawUnderstandingSuccessV1.model_validate(data))


def _mapping_probe(kind: str, phrase: str) -> dict[str, Any]:
    label = "synthetic-unknown-label" if kind == "map_unknown_label" else phrase
    confidence = 0.05 if kind == "map_low_confidence" else 0.85
    visual = _success(label, confidence=confidence, ambiguous=kind == "map_ambiguous")
    narration = _asr_success() if kind in {"map_asr_present", "raw_conflict_schema"} else None
    raw = _map(visual, narration)
    _require(isinstance(raw, RawUnderstandingSuccessV1), "EXPECTED_RAW_SUCCESS")
    assert isinstance(raw, RawUnderstandingSuccessV1)
    _require(raw.entities[0].label == visual.entities[0].label, "LABEL_NOT_PRESERVED")
    _require(raw.entities[0].confidence == confidence, "CONFIDENCE_NOT_PRESERVED")
    _require(raw.entities[0].source == "VISION", "VISION_SOURCE_NOT_PRESERVED")
    _require(raw.source_image_ref == visual.source_image_ref, "SOURCE_NOT_PRESERVED")
    _require(raw.provenance.config_hash == visual.config_hash, "PROVENANCE_NOT_PRESERVED")
    _assert_gate_a(raw)
    if kind == "map_ambiguous":
        _require(raw.ambiguous_regions[0].note == visual.ambiguous_regions[0].note,
                 "AMBIGUITY_NOT_PRESERVED")
    if narration is not None:
        _require(raw.narration_status == RawNarrationStatus.ASR_SUCCEEDED, "ASR_STATUS")
        _require(raw.asr_claims[0].source == "ASR", "ASR_SOURCE")
        _require(raw.asr_claims[0].text == narration.segments[0].text, "ASR_TEXT")
        _require(raw.asr_claims[0].confidence is None, "ASR_CONFIDENCE_FABRICATED")
    if kind == "raw_conflict_schema":
        data = raw.model_dump(mode="json")
        conflict = RawConflictV1(conflict_id="conflict-explicit",
                                claim_refs=("entity-1", "asr-0"),
                                code=RawConflictCode.SOURCE_DISAGREEMENT)
        data["conflicts"] = [conflict.model_dump(mode="json")]
        checked = RawUnderstandingSuccessV1.model_validate(data)
        _require(len(checked.conflicts) == 1, "CONFLICT_NOT_PRESERVED")
        data["conflicts"][0]["claim_refs"] = ["entity-1", "missing-ref"]
        _expect_rejection(lambda: RawUnderstandingSuccessV1.model_validate(data))
    metadata = {"source_sha256": _SHA, "gate_a_required": True,
                "vision_observation_count": len(raw.entities),
                "asr_claim_count": len(raw.asr_claims), "observed_confidence": confidence,
                "numeric_confidence_preserved": True, "eligibility_computed": False}
    if narration is not None:
        metadata.update(_asr_metadata(narration))
    return metadata


def _negative_probe(kind: str) -> dict[str, Any]:
    if kind == "reject_malformed":
        _expect_rejection(lambda: VisionUnderstandingSuccessV2.model_validate_json("{"))
    elif kind == "reject_source_hash":
        _expect_rejection(lambda: _map(_success(), expected_hash="0" * 64))
    elif kind == "reject_null_confidence":
        _expect_rejection(lambda: _map(_success(confidence=None)))
    else:
        data = _map(_success()).model_dump(mode="json")
        if kind == "reject_missing_provenance":
            data.pop("provenance")
        elif kind == "reject_dangling_reference":
            data["conflicts"] = [{"conflict_id": "bad-ref", "claim_refs": ["entity-1", "absent"],
                                  "code": "SOURCE_DISAGREEMENT"}]
        else:
            data["eligibility" if kind == "reject_prohibited" else "unexpected"] = True
        _expect_rejection(lambda: RawUnderstandingSuccessV1.model_validate(data))
    metadata: dict[str, Any] = {
        "rejection_observed": True, "default_confidence_fabricated": False,
    }
    if kind == "reject_prohibited":
        for category in VisionProhibitedClaimCategory:
            failure_data = _success().model_dump(mode="json")
            for field in ("entities", "actions", "relations", "themes", "ambiguous_regions",
                          "adapter_version", "config_hash"):
                failure_data.pop(field)
            failure_data.update(
                status="FAILED", error_code="PROHIBITED_CLAIM_DETECTED",
                error_detail=category.value, retryable=False, policy_execution_state="BLOCKED",
            )
            typed_failure = VisionUnderstandingFailureV2.model_validate(failure_data)
            mapped = _map(typed_failure)
            _require(isinstance(mapped, RawUnderstandingFailureV1), "POLICY_TYPED_FAILURE")
            assert isinstance(mapped, RawUnderstandingFailureV1)
            _require(mapped.failure.code.value == "PROHIBITED_FIELD" and
                     mapped.failure.upstream_detail == "PROHIBITED_CLAIM" and
                     not mapped.failure.retryable, "POLICY_FAILURE_MAPPING_CHANGED")
        metadata.update(
            typed_policy_fixture_count=len(VisionProhibitedClaimCategory),
            raw_failure_code="PROHIBITED_FIELD", raw_detail="PROHIBITED_CLAIM",
            policy_execution_proven=False,
        )
    return metadata


def _characterize(kind: str) -> dict[str, Any]:
    code = "RATE_LIMITED" if kind == "rate_limit_characterization" else "PROVIDER_ERROR"
    status = 429 if code == "RATE_LIMITED" else 503
    shared_error: LightningProviderError | None = None
    headers: Message[str, str] = Message()
    with patch("sketch2life.infrastructure.ai.lightning_client.urlopen",
               side_effect=HTTPError("http://127.0.0.1/offline", status,
                                     "synthetic", headers, None)) as fake_open:
        try:
            UrllibJsonTransport("http://127.0.0.1", "").post_json("/offline", {})
        except LightningProviderError as exc:
            shared_error = exc
    _require(shared_error is not None and shared_error.code == code and shared_error.retryable,
             "SHARED_HTTP_MAPPING_CHANGED")
    _require(fake_open.call_count == 1, "SHARED_TRANSPORT_NO_RETRY")
    vision_transport = _ErrorTransport(LightningProviderError(code, "synthetic failure", True))
    asr_transport = _ErrorTransport(LightningProviderError(code, "synthetic failure", True))
    vision = LightningVisionV2Adapter(transport=vision_transport,
                                     artifact_loader=lambda _ref: _IMAGE, clock=lambda: _TIME)
    asr = LightningAsrV2Adapter(transport=asr_transport, artifact_loader=lambda _ref: _AUDIO)
    visual_result, asr_result = vision.understand(_vision_request()), asr.transcribe(_asr_request())
    _require(isinstance(visual_result, VisionUnderstandingFailureV2), "VISION_FAILURE_REQUIRED")
    _require(isinstance(asr_result, AsrFailureV1), "ASR_FAILURE_REQUIRED")
    assert isinstance(visual_result, VisionUnderstandingFailureV2)
    assert isinstance(asr_result, AsrFailureV1)
    _require(visual_result.error_code == VisionErrorCode.VISION_PROVIDER_FAILURE and
             visual_result.error_detail == VisionNonPolicyErrorDetailV2.PERMANENT_RUNTIME_FAILURE
             and not visual_result.retryable, "VISION_CHARACTERIZATION_CHANGED")
    _require(asr_result.error_code == AsrErrorCode.ASR_PROVIDER_FAILURE and
             asr_result.error_detail == AsrErrorDetail.TRANSIENT_RUNTIME_FAILURE and
             asr_result.retryable, "ASR_CHARACTERIZATION_CHANGED")
    raw_vision, raw_asr = _map(visual_result), _map(_success(), asr_result)
    assert isinstance(raw_vision, RawUnderstandingFailureV1)
    assert isinstance(raw_asr, RawUnderstandingSuccessV1)
    _require(raw_asr.asr_failure is not None, "ASR_FAILURE_NOT_MAPPED")
    assert raw_asr.asr_failure is not None
    _require(not raw_vision.failure.retryable and
             raw_vision.failure.upstream_detail == visual_result.error_detail.value,
             "VISION_RAW_FAILURE_NOT_PRESERVED")
    _require(raw_asr.asr_failure.retryable and
             raw_asr.asr_failure.detail == asr_result.error_detail.value,
             "ASR_RAW_FAILURE_NOT_PRESERVED")
    _require(vision_transport.calls == 1 and asr_transport.calls == 1, "NO_AUTOMATIC_RETRY")
    return {"injected_http_status": status, "shared_error_code": code,
            "injected_error_code": code, "vision_error_code": visual_result.error_code.value,
            "vision_detail": visual_result.error_detail.value, "vision_retryable": False,
            "asr_error_code": asr_result.error_code.value,
            "asr_detail": asr_result.error_detail.value, "asr_retryable": True,
            "raw_vision_code": raw_vision.failure.code.value,
            "raw_asr_code": raw_asr.asr_failure.code.value,
            "raw_vision_retryable": raw_vision.failure.retryable,
            "raw_vision_detail": raw_vision.failure.upstream_detail,
            "raw_asr_retryable": raw_asr.asr_failure.retryable,
            "raw_asr_detail": raw_asr.asr_failure.detail,
            "vision_attempt_number": visual_result.attempt_number,
            "asr_attempt_number": asr_result.attempt_number,
            "fake_transport_calls": 2, "injected_http_calls": 1, "real_provider_calls": 0,
            "task_acceptance_resolved": False}


class _QualityInspector:
    def __init__(self, kind: str) -> None:
        self.kind = kind

    def inspect_image(self, _path: Path) -> ImageQualitySignals:
        signal = ImageQualitySignals(160, 160, 160.0, 35.0, 5.0, 0.1)
        if self.kind == "quality_dark":
            return replace(signal, mean_luminance=10.0)
        if self.kind == "quality_blur":
            return replace(signal, edge_strength=0.0)
        if self.kind == "quality_crop":
            return replace(signal, border_ink_ratio=0.9)
        return signal

    def inspect_audio(self, _path: Path) -> AudioQualitySignals:
        return AudioQualitySignals(1.0, 16000, 1, 0.3, 0.0, 0.5, 0.1)


def _quality_probe(kind: str, scratch_dir: Path) -> dict[str, Any]:
    scratch_dir.mkdir(parents=True, exist_ok=True)
    image, audio = scratch_dir / "synthetic-image.fixture", scratch_dir / "synthetic-audio.fixture"
    for path, data in ((image, _IMAGE), (audio, _AUDIO)):
        if path.exists() and path.read_bytes() != data:
            raise ManifestError("SCRATCH_COLLISION")
        path.write_bytes(data)
    result = DeterministicMediaValidator(_QualityInspector(kind)).validate(
        MediaValidationRequest(image, audio, "synthetic:image", "synthetic:audio"))
    reasons = [reason.value for reason in result.recapture_reasons]
    expected = {"quality_valid": [], "quality_dark": ["IMAGE_TOO_DARK"],
                "quality_blur": ["IMAGE_BLURRY"], "quality_crop": ["IMAGE_FRAMING_RISK"]}[kind]
    _require(reasons == expected, "QUALITY_REFERENCE_CHANGED")
    _require(result.image.sha256 == _SHA, "QUALITY_SOURCE_HASH_NOT_PRESERVED")
    return {"evidence_boundary": "QUALITY_VALIDATOR_REFERENCE_WITH_INJECTED_SIGNALS",
            "decision": result.decision.value, "reason_codes": reasons,
            "image_sha256": result.image.sha256,
            "http_admission_proven": False, "decoder_quality_proven": False}


def _synthetic_png() -> bytes:
    """Small RGB PNG synthesized here, with no copied image or child content."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return pack(">I", len(data)) + kind + data + pack(">I", crc32(kind + data) & 0xFFFFFFFF)

    pixels = b"".join(
        b"\x00" + bytes(channel for x in range(160)
                         for channel in ((20, 20, 20) if (x + y) % 10 < 5 else (240, 240, 240)))
        for y in range(160)
    )
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", pack(">IIBBBBB", 160, 160, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", compress(pixels)) + chunk(b"IEND", b""))


def _admission_probe(kind: str, scratch_dir: Path) -> dict[str, Any]:
    scratch_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "admission_valid": _synthetic_png(),
        "admission_corrupt": b"not-an-image-synthetic-fixture",
        "admission_unsupported": base64.b64decode(
            "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"),
        "admission_oversized": b"0" * 5_000_001,
    }
    payload = payloads[kind]
    path = scratch_dir / f"{kind}.fixture"
    if path.exists() and path.read_bytes() != payload:
        raise ManifestError("SCRATCH_COLLISION")
    path.write_bytes(payload)
    before = _digest(path)
    result = Feat018ImageAdmission(AvImageDecoder()).admit(
        Feat018AdmissionRequest(path, "synthetic:admission"))
    expected = {
        "admission_valid": ("ADMITTED", None),
        "admission_corrupt": ("INVALID_SOURCE", "NOT_AN_IMAGE"),
        "admission_unsupported": ("UNSUPPORTED", "UNSUPPORTED_CONTAINER"),
        "admission_oversized": ("REJECTED", "FILE_BYTES_EXCEEDED"),
    }[kind]
    actual = (result.decision.outcome.value,
              result.decision.reason.value if result.decision.reason else None)
    _require(actual == expected, "ADMISSION_OUTCOME_CHANGED")
    _require(before == _digest(path), "SOURCE_MUTATED")
    _require((result.source is not None) == (kind == "admission_valid"), "ADMISSION_SOURCE")
    return {"evidence_boundary": "IMAGE_ADMISSION_SERVICE_WITH_PYAV",
            "outcome": actual[0], "reason_code": actual[1], "input_sha256": before,
            "admitted_source_sha256": result.source.sha256 if result.source else None,
            "source_preserved": True, "http_admission_proven": False,
            "quality_validation_proven": False, "provider_calls": 0}


def _probe(kind: str, phrase: str, scratch_dir: Path) -> dict[str, Any]:
    if kind.startswith("map_") or kind == "raw_conflict_schema":
        return _mapping_probe(kind, phrase)
    if kind.startswith("reject_"):
        return _negative_probe(kind)
    if kind in {"rate_limit_characterization", "provider_error_characterization"}:
        return _characterize(kind)
    if kind.startswith("quality_"):
        return _quality_probe(kind, scratch_dir)
    if kind.startswith("admission_"):
        return _admission_probe(kind, scratch_dir)
    if kind == "asr_only_contract":
        asr_only_result = AsrSuccessV1.model_validate(_asr_success().model_dump(mode="json"))
        return {"contract_version": asr_only_result.contract_version, "product_flow_proven": False,
                "fake_asr_result_count": 1, "asr_provider_calls": 0,
                **_asr_metadata(asr_only_result)}
    if kind in {"asr_missing", "asr_failure"}:
        narration = _asr_failure() if kind == "asr_failure" else None
        raw_narration = _map(_success(), narration)
        assert isinstance(raw_narration, RawUnderstandingSuccessV1)
        expected = (RawNarrationStatus.ASR_FAILED if kind == "asr_failure"
                    else RawNarrationStatus.NOT_SUPPLIED)
        _require(raw_narration.narration_status == expected and not raw_narration.asr_claims,
                 "ASR_TRUTHFULNESS")
        _require((raw_narration.asr_failure is not None) == (kind == "asr_failure"),
                 "ASR_FAILURE_METADATA")
        return {"narration_status": raw_narration.narration_status.value, "asr_claim_count": 0,
                "fabricated_text": False,
                **(_asr_metadata(narration) if narration is not None else {})}
    if kind == "vision_timeout":
        transport = _ErrorTransport(TimeoutError())
        result = LightningVisionV2Adapter(transport=transport, artifact_loader=lambda _ref: _IMAGE,
                                         clock=lambda: _TIME).understand(_vision_request())
        _require(isinstance(result, VisionUnderstandingFailureV2), "EXPECTED_TIMEOUT_FAILURE")
        assert isinstance(result, VisionUnderstandingFailureV2)
        raw = _map(result)
        assert isinstance(raw, RawUnderstandingFailureV1)
        _require(raw.failure.code.value == "TIMEOUT" and not raw.failure.retryable,
                 "TIMEOUT_MAPPING_CHANGED")
        _require(transport.calls == 1, "NO_AUTOMATIC_RETRY")
        return {"raw_failure_code": "TIMEOUT", "retryable": False, "fake_transport_calls": 1}
    if kind == "vision_terminal_retry_fixture":
        data = _success().model_dump(mode="json")
        for field in ("entities", "actions", "relations", "themes", "ambiguous_regions",
                      "adapter_version", "config_hash"):
            data.pop(field)
        data.update(status="FAILED", attempt_number=2, policy_execution_state="NOT_EXECUTED",
                    error_code="VISION_PROVIDER_FAILURE", error_detail="TRANSIENT_RUNTIME_FAILURE",
                    retryable=True)
        failure = VisionUnderstandingFailureV2.model_validate(data)
        mapped = _map(failure)
        assert isinstance(mapped, RawUnderstandingFailureV1)
        _require(mapped.failure.retryable, "TERMINAL_FIXTURE_RETRYABILITY")
        return {"attempt_number": 2, "fixture_only": True, "retry_execution_proven": False,
                "fake_transport_calls": 0}
    raise ManifestError("UNSUPPORTED_PROBE")


def evaluate_manifest(manifest_path: Path, *, repo_root: Path, source_head: str, run_id: str,
                      source_state: str = "candidate", scratch_dir: Path | None = None
                      ) -> dict[str, Any]:
    """Execute supported diagnostics and preserve requirement holds independently."""
    if not re.fullmatch(r"[a-f0-9]{40}", source_head):
        raise ManifestError("INVALID_BASELINE_HEAD")
    if not re.fullmatch(r"feat018-p2-t5-offline-[a-z0-9-]+", run_id) or source_state != "candidate":
        raise ManifestError("INVALID_CANDIDATE_IDENTITY")
    manifest = load_manifest(manifest_path, repo_root)
    if manifest.get("baseline_head") != source_head:
        raise ManifestError("BASELINE_HEAD_MISMATCH")
    scratch = scratch_dir or repo_root / "backend/.pytest-tmp-feat018-p2t5-runner-r1"
    scratch = scratch.resolve()
    backend = (repo_root / "backend").resolve()
    if (not scratch.is_relative_to(backend) or
            not scratch.name.startswith(".pytest-tmp-feat018-p2t5-")):
        raise ManifestError("INVALID_SCRATCH_DIRECTORY")
    rows: list[dict[str, Any]] = []
    with offline_guards() as guard:
        for category, cases in (("PRIMARY", manifest["profiles"]),
                                ("SUPPLEMENTAL", manifest["supplemental_cases"])):
            for case in cases:
                observations: list[dict[str, Any]] = []
                phrase = case.get("recipe", {}).get("exact_phrase", "synthetic observation")
                for probe in case["subprobes"]:
                    kind = probe["kind"]
                    observation: dict[str, Any] = {
                        "probe_id": probe["probe_id"], "kind": kind,
                        "expected_outcome": probe["expected_outcome"],
                        "requirement_status": probe["requirement_status"],
                    }
                    if kind in HELD_KINDS:
                        observation.update(execution_status="NOT_EXECUTED",
                                           observed_outcome="NOT_EXECUTED")
                    else:
                        try:
                            metadata = _probe(kind, phrase, scratch)
                            observation.update(execution_status="SUCCEEDED",
                                               observed_outcome=kind.upper(),
                                               metadata=metadata)
                        except OfflineAccessError:
                            observation.update(execution_status="FAILED",
                                               observed_outcome="OFFLINE_ACCESS_REFUSED")
                        except (AssertionError, ValidationError,
                                RawUnderstandingMappingError, ManifestError):
                            observation.update(execution_status="FAILED",
                                               observed_outcome="DIAGNOSTIC_MISMATCH")
                        except Exception:  # noqa: BLE001 - sanitized diagnostic, never raw content
                            observation.update(execution_status="INTERNAL_ERROR",
                                               observed_outcome="INTERNAL_ERROR")
                    observations.append(observation)
                statuses = {item["execution_status"] for item in observations}
                execution = "INTERNAL_ERROR" if "INTERNAL_ERROR" in statuses else (
                    "FAILED" if "FAILED" in statuses else (
                    "SUCCEEDED" if "SUCCEEDED" in statuses else "NOT_EXECUTED")
                )
                rows.append({"fixture_id": case["fixture_id"],
                             "evidence_id": f"P2T5:{case['fixture_id']}",
                             "category": category, "activity_id": case.get("activity_id"),
                             "family": case.get("family"), "acceptance_ids": case["acceptance_ids"],
                             "execution_status": execution,
                             "requirement_status": case["requirement_status"],
                             "held_reason_codes": ["PARTIAL_OR_HELD_BOUNDARY"]
                             if case["requirement_status"] == "HELD" else [],
                             "fixture_recipe_sha256": sha256(json.dumps(
                                 case.get("recipe", {}), sort_keys=True,
                                 ensure_ascii=True).encode("utf-8")).hexdigest(),
                             "planning_source_case_id": case.get("planning_source_case_id"),
                             "subprobes": observations})
    counts = Counter(row["execution_status"] for row in rows)
    primary_counts = Counter(row["execution_status"] for row in rows
                             if row["category"] == "PRIMARY")
    report = {
        "schema_version": "1.0", "run_id": run_id, "source_head": source_head,
        "source_state": "candidate", "source_identity_type": "BASELINE_HEAD_PLUS_CANDIDATE_DIGESTS",
        "manifest_sha256": _digest(manifest_path), "synthetic_data": True,
        "provider_execution": "NOT_EXECUTED", "live_metrics": "NOT_MEASURED",
        "model_execution": "NOT_EXECUTED", "task_status": "OPEN",
        "source_locks": manifest["source_locks"], "contract_locks": manifest["contract_locks"],
        "candidate_file_digests": [{"path": path, "sha256": _digest(_source_path(repo_root, path))}
                                   for path in _CODE_PATHS],
        "guard": {"scope": "PROCESS_TRIPWIRES_NOT_OS_SANDBOX",
                  "blocked_attempts": guard.blocked_attempts},
        "execution_status": "FAILED" if (counts["FAILED"] or counts["INTERNAL_ERROR"] or
                                            guard.blocked_attempts) else "SUCCEEDED",
        "summary": {"primary_slots": 120, "primary_execution_counts": dict(primary_counts),
                    "execution_counts": dict(counts), "satisfied_full_acceptance_count": 0,
                    "held_counted_as_coverage": 0},
        "requirements": {f"T5-A{number}": "OPEN" for number in range(1, 10)},
        "results": rows,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("manifest", "run-id", "source-head", "source-state", "scratch-dir",
                 "metrics-output", "status-output"):
        parser.add_argument(f"--{flag}", required=True)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[4]
    metrics, status = Path(args.metrics_output).resolve(), Path(args.status_output).resolve()
    expected_metrics = (repo_root /
                        f"{_FEATURE}/evidence/metrics/P2_T5_OFFLINE_EVALUATION_20261022.json")
    expected_status = repo_root / f"{_FEATURE}/evidence/notes/P2_T5_OFFLINE_STATUS_20261022.txt"
    if metrics != expected_metrics.resolve() or status != expected_status.resolve():
        parser.error("outputs must match the approved evidence paths")
    try:
        report = evaluate_manifest(Path(args.manifest), repo_root=repo_root,
                                   source_head=args.source_head, run_id=args.run_id,
                                   source_state=args.source_state,
                                   scratch_dir=Path(args.scratch_dir))
    except ManifestError as exc:
        print(str(exc))
        return 2
    for target in (metrics, status):
        target.parent.mkdir(parents=True, exist_ok=True)
    metrics.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    lines = [f"run_id={report['run_id']}", f"execution_status={report['execution_status']}",
             "provider_execution=NOT_EXECUTED", "live_metrics=NOT_MEASURED", "Task5=OPEN",
             "HELD_counted_as_coverage=0", "full_acceptance_satisfied=0",
             f"primary_slots={report['summary']['primary_slots']}",
             f"blocked_access_attempts={report['guard']['blocked_attempts']}"]
    status.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OFFLINE_DIAGNOSTICS_{report['execution_status']}; TASK5_OPEN")
    return 0 if report["execution_status"] == "SUCCEEDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
