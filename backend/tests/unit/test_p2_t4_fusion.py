"""P2-T4 offline fusion core: fixture-driven parity and behavioral invariants.

Expected outputs in `expected-v1.json` are hand-authored from the frozen successor contract
(freeze revision 12), not generated from the implementation. The canonical-bytes oracle below
is an independent re-statement of `P2T4-CANONICAL-JSON-V1`, and conflict identifiers are
recomputed from the frozen byte algorithm rather than read from the implementation.

Match-view privacy rule (remediation approval, 2026-09-16): the fixed synthetic non-canonical
`policy_match_view_version` value used by the AC-MV scenarios is constructed only in this
module, in memory. Fixture JSON stores a mutation category only. Every non-disclosure
assertion below is evaluated as a boolean first so that a failure snapshot never prints or
serializes the sentinel.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import re
from datetime import UTC, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from sketch2life.application.services.p2_t4_fusion import (
    P2T4FusionInputError,
    fuse,
    validate_and_fuse,
)
from sketch2life.contracts.schemas import understanding as feat018_live
from sketch2life.contracts.schemas.asr import AsrFailureV1, AsrSuccessV1
from sketch2life.contracts.schemas.media_validation import SourceMediaReferenceV1
from sketch2life.contracts.schemas.p2_t4_fusion import (
    P2T4FusedResultStatus,
    P2T4FusedResultV1,
    P2T4FusionInputRejectionV2,
    P2T4FusionPolicyConfigV1,
    P2T4InputSlot,
    P2T4RejectionCode,
    P2T4RejectionFieldCode,
    P2T4RejectionPhase,
    canonical_bytes,
    canonical_json,
    canonical_projection,
    canonical_sha256,
)
from sketch2life.contracts.schemas.vision import (
    VISION_POLICY_MATCH_VIEW_VERSION,
    VisionErrorCode,
    VisionNonPolicyErrorDetail,
    VisionUnderstandingFailureV1,
    VisionUnderstandingSuccessV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_DIR = (
    _REPO_ROOT / "features" / "FEAT-003-multimodal-understanding" / "fixtures" / "p2-t4-fusion-v1"
)
_TRANSCRIPT_SENTINEL = "RAW-TRANSCRIPT-SENTINEL"
_FORBIDDEN_OUTPUT_FRAGMENTS = (
    _TRANSCRIPT_SENTINEL,
    "ValidationError",
    "Traceback",
    "pydantic",
    "C:\\",
    "D:\\",
    "/Users/",
    "/home/",
    "http://",
    "https://",
    "Bearer ",
    "sk-",
    "api_key",
    "prompt",
)
_ABSOLUTE_PATH_PATTERN = re.compile(r"(?:[A-Za-z]:[\\/])|(?:/(?:Users|home)/)|(?:\\\\)")

# Fixed private synthetic non-canonical match-view value. Constructed only here, in memory, from
# fragments so that the assembled value never appears verbatim in any file; never persisted to
# fixture JSON, output, exception text, snapshots, logs, evidence, or reports.
_MATCH_VIEW_SENTINEL = "-".join(("synthetic", "noncanonical", "match", "view", "sentinel", "v0"))
_MATCH_VIEW_MUTATIONS = frozenset({"SYNTHETIC_NONCANONICAL_SENTINEL", "T4_POLICY_LITERAL"})
_MATCH_VIEW_ACCEPTANCE_IDS = ("AC-MV-1", "AC-MV-2", "AC-MV-3", "AC-MV-4", "AC-MV-5", "AC-MV-6")
_SUPERSEDED_REJECTION_IDENTITY = "P2T4.P2T4FusionInputRejection" + "V1@1.0"
_SUPERSEDED_REJECTION_NAME = "P2T4FusionInputRejection" + "V1"


def _load(name: str) -> dict[str, Any]:
    payload: object = json.loads((_FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return {str(key): value for key, value in payload.items()}


_CASES = _load("cases-v1.json")
_EXPECTED = _load("expected-v1.json")
_MANIFEST = _load("manifest-v1.json")
_CASE_LIST: list[dict[str, Any]] = list(_CASES["cases"])
_CASE_IDS = [case["case_id"] for case in _CASE_LIST]
_ENVELOPE = _CASES["envelope"]
_SHA_A = "a" * 64
_REJECTED_CASE_COUNT = 20
_NON_REJECTED_CASE_COUNT = 27


# --- fixture builders ----------------------------------------------------------------------


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _executed_at() -> datetime:
    return _parse_datetime(_CASES["executed_at"])


def _policy(case: dict[str, Any]) -> P2T4FusionPolicyConfigV1:
    payload = dict(_CASES["policy"])
    payload.update(case.get("policy_overrides", {}))
    payload["negation_cues"] = tuple(tuple(cue) for cue in payload["negation_cues"])
    return P2T4FusionPolicyConfigV1.model_validate(payload)


def _observed_text(value: str, tags: list[str] | None = None) -> dict[str, Any]:
    if tags:
        language = {"status": "DECLARED", "tags": tags, "is_ground_truth": False}
    else:
        language = {"status": "NOT_DETERMINED", "tags": [], "is_ground_truth": False}
    return {"value": value, "language": language}


def _apply_edits(payload: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    payload.update(copy.deepcopy(spec.get("overrides", {})))
    for key in spec.get("remove", []):
        payload.pop(key)
    return payload


def _asr_envelope(spec: dict[str, Any]) -> dict[str, Any]:
    envelope: dict[str, Any] = copy.deepcopy(_ENVELOPE["asr"])
    envelope.pop("segment_timing")
    envelope["correlation_id"] = spec.get("correlation_id", _ENVELOPE["correlation_id"])
    return envelope


def _build_p2_asr(spec: dict[str, Any]) -> dict[str, Any]:
    payload = _asr_envelope(spec)
    if spec["kind"] == "P2_FAILURE":
        for key in ("transcript_raw", "detected_language", "language_probability"):
            payload.pop(key)
        for key in (
            "language_hint_echo",
            "language_hint_applied",
            "input_duration_seconds",
            "vad_enabled",
            "duration_after_vad_seconds",
            "model_identifier",
            "model_revision",
            "adapter_version",
            "runtime_version",
            "config_hash",
            "quality_metadata",
        ):
            payload.pop(key)
        payload["status"] = "FAILED"
        for key in (
            "error_code",
            "error_detail",
            "retryable",
            "attempt_number",
            "repair_attempted",
        ):
            payload[key] = spec[key]
        return _apply_edits(payload, spec)
    timing = _ENVELOPE["asr"]["segment_timing"]
    segments = []
    for segment in spec["segments"]:
        start = segment["index"] * timing["start_seconds_per_index"]
        segments.append(
            {
                "index": segment["index"],
                "start_seconds": start,
                "end_seconds": start + timing["duration_seconds"],
                "text": segment["text"],
                "average_log_probability": None,
                "compression_ratio": None,
                "no_speech_probability": None,
                "words": None,
            }
        )
    payload["status"] = "SUCCEEDED"
    payload["speech_diagnostic"] = "DETECTED" if segments else "NO_SPEECH_SUSPECTED"
    payload["segments"] = segments
    return _apply_edits(payload, spec)


def _match_view_value(mutation: str, policy: P2T4FusionPolicyConfigV1 | None) -> str:
    """Resolve a fixture mutation category to the in-memory observed value; never persisted."""

    assert mutation in _MATCH_VIEW_MUTATIONS
    if mutation == "SYNTHETIC_NONCANONICAL_SENTINEL":
        return _MATCH_VIEW_SENTINEL
    assert policy is not None
    return policy.match_view_version


def _build_p2_vision(
    spec: dict[str, Any], policy: P2T4FusionPolicyConfigV1 | None = None
) -> dict[str, Any]:
    payload = copy.deepcopy(_ENVELOPE["vision"])
    payload["correlation_id"] = spec.get("correlation_id", _ENVELOPE["correlation_id"])
    if "match_view_mutation" in spec:
        payload["policy_match_view_version"] = _match_view_value(
            spec["match_view_mutation"], policy
        )
    if spec["kind"] == "P2_FAILURE":
        payload.pop("adapter_version")
        payload.pop("config_hash")
        payload["status"] = "FAILED"
        for key in (
            "error_code",
            "error_detail",
            "retryable",
            "attempt_number",
            "repair_attempted",
        ):
            payload[key] = spec[key]
        payload["policy_execution_state"] = spec["policy_execution_state"]
        return _apply_edits(payload, spec)
    payload["status"] = "SUCCEEDED"
    payload["policy_execution_state"] = "PASSED"
    payload["entities"] = [
        {
            "observation_id": entity["observation_id"],
            "label": _observed_text(entity["label"], entity.get("language")),
            "confidence": entity["confidence"],
        }
        for entity in spec.get("entities", [])
    ]
    payload["actions"] = [
        {
            "observation_id": action["observation_id"],
            "label": _observed_text(action["label"], action.get("language")),
            "actor_ref": action.get("actor_ref"),
            "object_ref": action.get("object_ref"),
            "confidence": action["confidence"],
        }
        for action in spec.get("actions", [])
    ]
    payload["relations"] = [
        {
            "observation_id": relation["observation_id"],
            "predicate": _observed_text(relation["predicate"], relation.get("language")),
            "subject_ref": relation["subject_ref"],
            "object_ref": relation["object_ref"],
            "confidence": relation["confidence"],
        }
        for relation in spec.get("relations", [])
    ]
    payload["themes"] = [
        {
            "observation_id": theme["observation_id"],
            "label": _observed_text(theme["label"], theme.get("language")),
            "evidence_refs": list(theme["evidence_refs"]),
            "confidence": theme["confidence"],
        }
        for theme in spec.get("themes", [])
    ]
    payload["ambiguous_regions"] = [
        {"observation_id": region["observation_id"], "note": _observed_text(region["note"])}
        for region in spec.get("ambiguous_regions", [])
    ]
    return _apply_edits(payload, spec)


def _feat018_provenance() -> feat018_live.ModelProvenanceV1:
    return feat018_live.ModelProvenanceV1(
        provider="fixture", model="fixture-live", adapter_version="v1", config_version="v1"
    )


def _feat018_source(ref: str) -> SourceMediaReferenceV1:
    return SourceMediaReferenceV1(artifact_ref=ref, sha256=_SHA_A)


def _build_typed_input(spec: dict[str, Any]) -> object:
    kind = spec["kind"]
    if kind == "FEAT018_LIVE_ASR_MODEL":
        return feat018_live.AsrResultV1(
            status="SUCCEEDED",
            source_audio=_feat018_source("fixture:feat018:audio.wav"),
            transcript="",
            quality=feat018_live.AsrQualityV1(segment_count=0),
            provenance=_feat018_provenance(),
        )
    if kind == "FEAT018_LIVE_VISION_MODEL":
        return feat018_live.VisionUnderstandingResultV1(
            status="FAILED",
            source_image=_feat018_source("fixture:feat018:image.png"),
            uncertainty=1.0,
            provenance=_feat018_provenance(),
            failure=feat018_live.AdapterFailureV1(
                code="TIMEOUT", message="fixture timeout", retryable=True
            ),
        )
    if kind == "P2_VISION_V2_MODEL":
        return VisionUnderstandingFailureV2(
            correlation_id=_ENVELOPE["correlation_id"],
            executed_at=_parse_datetime(_ENVELOPE["vision"]["executed_at"]),
            source_image_ref=_ENVELOPE["vision"]["source_image_ref"],
            profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
            profile_catalog_hash=_ENVELOPE["vision"]["profile_catalog_hash"],
            attempt_number=0,
            repair_attempted=False,
            content_policy_version="fixture-content-policy-v1",
            policy_match_view_version="vision-policy-match-view-v2",
            policy_execution_state="NOT_EXECUTED",
            error_code=VisionErrorCode.INPUT_NOT_VALIDATED,
            error_detail=VisionNonPolicyErrorDetailV2.MEDIA_VALIDATION_NOT_PASSED,
            retryable=False,
        )
    if kind == "P2_VISION_V1_MODEL_IN_ASR_SLOT":
        return VisionUnderstandingSuccessV1.model_validate(
            _build_p2_vision({"kind": "P2_SUCCESS", "entities": []})
        )
    if kind == "UNKNOWN_OBJECT":
        return "not-a-result"
    raise AssertionError(f"unknown fixture input kind: {kind}")


def _build_input(spec: dict[str, Any], slot: str, policy: P2T4FusionPolicyConfigV1) -> object:
    kind = spec["kind"]
    if kind == "RAW":
        return copy.deepcopy(spec["value"])
    if kind in ("P2_SUCCESS", "P2_FAILURE"):
        return _build_p2_asr(spec) if slot == "asr" else _build_p2_vision(spec, policy)
    return _build_typed_input(spec)


def _run_case(case: dict[str, Any]) -> P2T4FusedResultV1 | P2T4FusionInputRejectionV2:
    policy = _policy(case)
    return validate_and_fuse(
        _build_input(case["asr"], "asr", policy),
        _build_input(case["vision"], "vision", policy),
        policy,
        _executed_at(),
    )


def _case(case_id: str) -> dict[str, Any]:
    return next(case for case in _CASE_LIST if case["case_id"] == case_id)


def _typed_success_pair(case_id: str) -> tuple[AsrSuccessV1, VisionUnderstandingSuccessV1]:
    case = _case(case_id)
    asr = AsrSuccessV1.model_validate(_build_p2_asr(case["asr"]))
    vision = VisionUnderstandingSuccessV1.model_validate(
        _build_p2_vision(case["vision"], _policy(case))
    )
    return asr, vision


def _discloses_sentinel(*texts: str) -> bool:
    """Boolean-only non-disclosure probe: callers assert on the result, never on the text."""

    return any(_MATCH_VIEW_SENTINEL in text for text in texts)


def _is_private_match_view(value: str) -> bool:
    """Closed boolean probe: keeps the sentinel out of assertion-rewrite diagnostics."""

    return hmac.compare_digest(value, _MATCH_VIEW_SENTINEL)


def _rejection_texts(rejection: P2T4FusionInputRejectionV2) -> tuple[str, ...]:
    return (canonical_json(rejection), repr(rejection), str(rejection))


def _assert_vision_match_view_form(rejection: object) -> P2T4FusionInputRejectionV2:
    assert isinstance(rejection, P2T4FusionInputRejectionV2)
    assert rejection.contract_name == "P2T4FusionInputRejectionV2"
    assert rejection.contract_version == "2.0"
    assert rejection.input_slot is P2T4InputSlot.VISION
    assert rejection.phase is P2T4RejectionPhase.ADMISSIBILITY
    assert rejection.code is P2T4RejectionCode.INVALID_STRUCTURE
    assert rejection.expected_identity.value == "P2.VisionUnderstandingResultV1@1.0"
    assert rejection.observed_identity.value == "P2.VisionUnderstandingResultV1@1.0"
    assert rejection.observed_status is not None
    assert rejection.observed_status.value == "SUCCEEDED"
    assert rejection.field_code is P2T4RejectionFieldCode.POLICY_MATCH_VIEW_VERSION
    assert not _discloses_sentinel(*_rejection_texts(rejection))
    return rejection


def _assert_asr_duplicate_index_form(rejection: object) -> P2T4FusionInputRejectionV2:
    assert isinstance(rejection, P2T4FusionInputRejectionV2)
    assert rejection.contract_version == "2.0"
    assert rejection.input_slot is P2T4InputSlot.ASR
    assert rejection.phase is P2T4RejectionPhase.ADMISSIBILITY
    assert rejection.code is P2T4RejectionCode.INVALID_STRUCTURE
    assert rejection.field_code is P2T4RejectionFieldCode.DUPLICATE_SEGMENT_INDEX
    assert not _discloses_sentinel(*_rejection_texts(rejection))
    return rejection


# --- independent canonical-bytes oracle ---------------------------------------------------


def _oracle_normalize(value: object) -> object:
    if value is None or isinstance(value, bool | int | str):
        return value.value if isinstance(value, Enum) else value
    if isinstance(value, float):
        assert value == value and value not in (float("inf"), float("-inf"))
        return value
    if isinstance(value, datetime):
        assert value.tzinfo is not None
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, tuple | list):
        return [_oracle_normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _oracle_normalize(item) for key, item in value.items()}
    raise AssertionError(f"unexpected canonical value type: {type(value).__name__}")


def _oracle_canonical_bytes(model: BaseModel) -> bytes:
    projection = _oracle_normalize(model.model_dump(mode="python"))
    return json.dumps(
        projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _oracle_conflict_id(reason_code: str, observation_id: str) -> str:
    payload = reason_code.encode("utf-8") + b"\x00" + observation_id.encode("utf-8")
    return "P2T4-CONFLICT-" + hashlib.sha256(payload).hexdigest()


# --- fixture binding ----------------------------------------------------------------------


def test_fixture_files_bind_the_same_case_set() -> None:
    manifest_ids = [entry["case_id"] for entry in _MANIFEST["cases"]]
    assert manifest_ids == _CASE_IDS
    assert list(_EXPECTED["cases"]) == _CASE_IDS
    assert len(set(_CASE_IDS)) == len(_CASE_IDS)
    assert _MANIFEST["target_contract"] == "P2T4.P2T4FusedResultV1@1.0"
    assert _CASES["target_contract"] == "P2T4.P2T4FusedResultV1@1.0"
    assert _EXPECTED["target_contract"] == "P2T4.P2T4FusedResultV1@1.0"
    assert _MANIFEST["rejection_contract"] == "P2T4.P2T4FusionInputRejectionV2@2.0"
    assert _MANIFEST["synthetic_data"] is True
    for entry in _MANIFEST["cases"]:
        assert entry["expected_outcome"] == _EXPECTED["cases"][entry["case_id"]]["outcome"]
        assert entry["coverage"] == _case(entry["case_id"])["coverage"]
    outcomes = [expected["outcome"] for expected in _EXPECTED["cases"].values()]
    assert outcomes.count("REJECTED") == _REJECTED_CASE_COUNT
    assert len(outcomes) - outcomes.count("REJECTED") == _NON_REJECTED_CASE_COUNT
    assert len(outcomes) == _REJECTED_CASE_COUNT + _NON_REJECTED_CASE_COUNT


def test_manifest_binds_the_corrected_successor_identities_and_approval() -> None:
    binding = _MANIFEST["binding"]
    assert binding["remediation_approval_commit"] == "dc107cd45a21ccb47031a58cb7c782084624bff4"
    assert binding["successor_freeze"]["revision"] == 12
    assert binding["successor_freeze"]["source_commit"] == (
        "5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2"
    )
    assert binding["successor_package"]["revision"] == 16
    assert binding["successor_package"]["source_commit"] == (
        "5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2"
    )
    assert binding["predecessor_freeze"]["source_commit"] == (
        "18d0c33d35431ca96a76692a68c6b992098699e7"
    )
    for artifact in ("successor_freeze", "successor_package", "predecessor_freeze"):
        for digest in ("raw_sha256", "normalized_sha256"):
            assert _HEX_PATTERN.match(binding[artifact][digest])
        assert re.match(r"^[a-f0-9]{40}$", binding[artifact]["git_blob_id"])


def test_manifest_coverage_declares_every_required_scenario() -> None:
    declared = {tag for case in _CASE_LIST for tag in case["coverage"]}
    assert set(_MANIFEST["required_coverage"]) <= declared


def test_every_expected_rejection_uses_the_v2_identity_only() -> None:
    for case_id, expected in _EXPECTED["cases"].items():
        result = expected["result"]
        if expected["outcome"] == "REJECTED":
            assert result["contract_name"] == "P2T4FusionInputRejectionV2", case_id
            assert result["contract_version"] == "2.0", case_id
            assert result["status"] == "REJECTED", case_id
        else:
            assert result["contract_name"] == "P2T4FusedResultV1", case_id
            assert result["contract_version"] == "1.0", case_id


def test_expected_canonical_hashes_were_authored_from_the_byte_algorithm() -> None:
    """Every `canonical_sha256` is SHA-256 of the compact sorted UTF-8 JSON of `result`."""

    for expected in _EXPECTED["cases"].values():
        text = json.dumps(
            expected["result"],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        assert expected["canonical_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- match-view scenario binding and privacy (AC-MV-1..AC-MV-6) ---------------------------


def test_match_view_scenarios_are_bound_consistently_across_fixture_files() -> None:
    coverage = _MANIFEST["match_view_coverage"]
    assert tuple(coverage) == _MATCH_VIEW_ACCEPTANCE_IDS
    expected_outcomes = {
        "AC-MV-1": ("REJECTED", "vision-match-view-admissibility-rejection"),
        "AC-MV-2": ("REJECTED", "policy-literal-is-not-the-upstream-token"),
        "AC-MV-3": ("REJECTED", "asr-admissibility-precedes-vision-admissibility"),
        "AC-MV-4": ("REJECTED", "vision-admissibility-precedes-correlation"),
        "AC-MV-5": ("UPSTREAM_FAILURE", "noncanonical-match-view-failure-unaffected"),
        "AC-MV-6": ("REJECTED", "strict-validation-precedes-match-view-admissibility"),
    }
    seen: set[str] = set()
    for acceptance_id, entry in coverage.items():
        case_id = entry["case_id"]
        outcome, tag = expected_outcomes[acceptance_id]
        case = _case(case_id)
        assert tag in case["coverage"]
        assert tag in _MANIFEST["required_coverage"]
        assert _EXPECTED["cases"][case_id]["outcome"] == outcome
        assert entry["mutation"] in _MATCH_VIEW_MUTATIONS
        assert case["vision"]["match_view_mutation"] == entry["mutation"]
        seen.add(case_id)
    assert len(seen) == 6
    assert coverage["AC-MV-6"]["case_id"] == "strict-asr-before-strict-vision"


def test_fixture_json_stores_mutation_categories_only() -> None:
    for case in _CASE_LIST:
        for slot in ("asr", "vision"):
            spec = case[slot]
            assert "policy_match_view_version" not in spec.get("overrides", {})
            if slot == "vision" and "match_view_mutation" in spec:
                assert spec["match_view_mutation"] in _MATCH_VIEW_MUTATIONS
                assert spec["kind"] in ("P2_SUCCESS", "P2_FAILURE")
    envelope_token = _ENVELOPE["vision"]["policy_match_view_version"]
    assert envelope_token == VISION_POLICY_MATCH_VIEW_VERSION
    assert _CASES["policy"]["match_view_version"] != VISION_POLICY_MATCH_VIEW_VERSION


def test_fixture_files_never_contain_the_sentinel_or_the_superseded_identity() -> None:
    for name in ("manifest-v1.json", "cases-v1.json", "expected-v1.json"):
        text = (_FIXTURE_DIR / name).read_text(encoding="utf-8")
        assert not _discloses_sentinel(text), name
        assert _SUPERSEDED_REJECTION_NAME not in text, name
        assert _SUPERSEDED_REJECTION_IDENTITY not in text, name
        assert "POLICY_MATCH_VIEW_VERSION" in text or name == "cases-v1.json", name


def test_sentinel_is_a_strictly_valid_non_canonical_vision_value() -> None:
    """The sentinel exercises T4 admissibility, not upstream strict validation."""

    assert not _is_private_match_view(VISION_POLICY_MATCH_VIEW_VERSION)
    assert not _is_private_match_view(_CASES["policy"]["match_view_version"])
    assert _CASES["policy"]["match_view_version"] != VISION_POLICY_MATCH_VIEW_VERSION
    case = _case("vision-noncanonical-match-view-rejection")
    payload = _build_p2_vision(case["vision"], _policy(case))
    assert _is_private_match_view(payload["policy_match_view_version"])
    validated = VisionUnderstandingSuccessV1.model_validate(payload)
    assert _is_private_match_view(validated.policy_match_view_version)


def test_ac_mv_1_noncanonical_vision_success_is_rejected_at_admissibility() -> None:
    case = _case("vision-noncanonical-match-view-rejection")
    rejection = _assert_vision_match_view_form(_run_case(case))
    assert canonical_projection(rejection) == _EXPECTED["cases"][case["case_id"]]["result"]
    assert "1.0" not in canonical_projection(rejection).values()
    with_canonical_token = copy.deepcopy(case)
    del with_canonical_token["vision"]["match_view_mutation"]
    fused = _run_case(with_canonical_token)
    assert isinstance(fused, P2T4FusedResultV1)
    assert fused.status is P2T4FusedResultStatus.FUSED


def test_ac_mv_2_policy_literal_as_observed_vision_value_is_rejected() -> None:
    case = _case("vision-policy-literal-match-view-rejection")
    policy = _policy(case)
    payload = _build_p2_vision(case["vision"], policy)
    assert payload["policy_match_view_version"] == policy.match_view_version
    assert payload["policy_match_view_version"] != VISION_POLICY_MATCH_VIEW_VERSION
    rejection = _assert_vision_match_view_form(_run_case(case))
    assert canonical_projection(rejection) == _EXPECTED["cases"][case["case_id"]]["result"]
    assert policy.match_view_version not in canonical_json(rejection)


def test_ac_mv_3_asr_duplicate_index_wins_over_vision_match_view() -> None:
    case = _case("asr-duplicate-index-before-vision-match-view")
    rejection = _assert_asr_duplicate_index_form(_run_case(case))
    assert canonical_projection(rejection) == _EXPECTED["cases"][case["case_id"]]["result"]
    vision_alone = copy.deepcopy(case)
    vision_alone["asr"]["segments"] = [{"index": 0, "text": "a dog"}]
    _assert_vision_match_view_form(_run_case(vision_alone))


def test_ac_mv_4_vision_match_view_wins_over_correlation_mismatch() -> None:
    case = _case("vision-match-view-before-correlation")
    assert case["asr"]["correlation_id"] != _ENVELOPE["correlation_id"]
    rejection = _assert_vision_match_view_form(_run_case(case))
    assert canonical_projection(rejection) == _EXPECTED["cases"][case["case_id"]]["result"]
    correlation_only = copy.deepcopy(case)
    del correlation_only["vision"]["match_view_mutation"]
    outcome = _run_case(correlation_only)
    assert isinstance(outcome, P2T4FusionInputRejectionV2)
    assert outcome.phase is P2T4RejectionPhase.CORRELATION


def test_vision_match_view_wins_over_typed_asr_failure_status() -> None:
    asr_failure = _case("asr-failure")
    vision_case = _case("vision-noncanonical-match-view-rejection")
    policy = _policy(vision_case)
    outcome = validate_and_fuse(
        _build_p2_asr(asr_failure["asr"]),
        _build_p2_vision(vision_case["vision"], policy),
        policy,
        _executed_at(),
    )
    _assert_vision_match_view_form(outcome)


def test_ac_mv_5_noncanonical_vision_failure_remains_upstream_failure() -> None:
    case = _case("vision-failure-noncanonical-match-view")
    outcome = _run_case(case)
    assert isinstance(outcome, P2T4FusedResultV1)
    assert outcome.status is P2T4FusedResultStatus.UPSTREAM_FAILURE
    assert outcome.upstream_failure is not None
    assert outcome.upstream_failure.vision_failure_ref is not None
    assert outcome.upstream_failure.vision_failure_ref.policy_execution_state == "BLOCKED"
    assert canonical_projection(outcome) == _EXPECTED["cases"][case["case_id"]]["result"]
    assert not _discloses_sentinel(canonical_json(outcome), repr(outcome))
    canonical = _run_case(_case("vision-failure-prohibited-claim"))
    assert isinstance(canonical, P2T4FusedResultV1)
    assert (
        outcome.source_vision_result_ref.result_sha256
        != canonical.source_vision_result_ref.result_sha256
    )
    assert outcome.source_asr_result_ref == canonical.source_asr_result_ref
    assert (
        outcome.model_copy(
            update={
                "source_vision_result_ref": canonical.source_vision_result_ref,
                "upstream_failure": canonical.upstream_failure,
            }
        )
        == canonical
    )


def test_ac_mv_6_strict_validation_precedes_match_view_admissibility() -> None:
    case = _case("strict-asr-before-strict-vision")
    assert case["vision"]["match_view_mutation"] == "SYNTHETIC_NONCANONICAL_SENTINEL"
    outcome = _run_case(case)
    assert isinstance(outcome, P2T4FusionInputRejectionV2)
    assert outcome.input_slot is P2T4InputSlot.ASR
    assert outcome.phase is P2T4RejectionPhase.STRICT_VALIDATION
    assert canonical_projection(outcome) == _EXPECTED["cases"][case["case_id"]]["result"]
    assert not _discloses_sentinel(*_rejection_texts(outcome))
    # Strictly valid non-canonical Vision success behind a strictly invalid ASR: ASR strict wins.
    strict_asr = copy.deepcopy(case)
    strict_asr["vision"].pop("remove")
    outcome = _run_case(strict_asr)
    assert isinstance(outcome, P2T4FusionInputRejectionV2)
    assert outcome.input_slot is P2T4InputSlot.ASR
    assert outcome.phase is P2T4RejectionPhase.STRICT_VALIDATION
    # Strictly invalid non-canonical Vision behind a valid ASR: Vision strict, not admissibility.
    strict_vision = copy.deepcopy(case)
    strict_vision["asr"].pop("overrides")
    outcome = _run_case(strict_vision)
    assert isinstance(outcome, P2T4FusionInputRejectionV2)
    assert outcome.input_slot is P2T4InputSlot.VISION
    assert outcome.phase is P2T4RejectionPhase.STRICT_VALIDATION
    assert outcome.field_code is P2T4RejectionFieldCode.SOURCE_REFERENCE
    assert not _discloses_sentinel(*_rejection_texts(outcome))


def test_match_view_comparison_is_exact_byte_equality() -> None:
    case = _case("vision-noncanonical-match-view-rejection")
    policy = _policy(case)
    canonical = VISION_POLICY_MATCH_VIEW_VERSION
    for variant in (canonical.upper(), canonical + " ", " " + canonical, canonical + "\u200b"):
        assert variant != canonical
        payload = _build_p2_vision({"kind": "P2_SUCCESS", "entities": []}, policy)
        payload["policy_match_view_version"] = variant
        outcome = validate_and_fuse(
            _build_p2_asr({"kind": "P2_SUCCESS", "segments": []}), payload, policy, _executed_at()
        )
        rejection = _assert_vision_match_view_form(outcome)
        assert variant not in canonical_json(rejection)


def test_typed_fuse_raises_a_closed_error_for_noncanonical_match_view() -> None:
    asr, vision = _typed_success_pair("vision-noncanonical-match-view-rejection")
    assert _is_private_match_view(vision.policy_match_view_version)
    policy = _policy(_case("vision-noncanonical-match-view-rejection"))
    with pytest.raises(P2T4FusionInputError) as info:
        fuse(asr, vision, policy, _executed_at())
    assert str(info.value) == "INVALID_STRUCTURE"
    assert info.value.args == ("INVALID_STRUCTURE",)
    rejection = _assert_vision_match_view_form(info.value.rejection)
    assert (
        canonical_projection(rejection)
        == (_EXPECTED["cases"]["vision-noncanonical-match-view-rejection"]["result"])
    )
    assert not _discloses_sentinel(str(info.value), repr(info.value), repr(info.value.args))
    failure = VisionUnderstandingFailureV1.model_validate(
        _build_p2_vision(_case("vision-failure-noncanonical-match-view")["vision"], policy)
    )
    assert _is_private_match_view(failure.policy_match_view_version)
    typed = fuse(asr, failure, policy, _executed_at())
    assert typed.status is P2T4FusedResultStatus.UPSTREAM_FAILURE
    assert not _discloses_sentinel(canonical_json(typed))


# --- fixture-driven parity ----------------------------------------------------------------


@pytest.mark.parametrize("case", _CASE_LIST, ids=_CASE_IDS)
def test_case_matches_hand_authored_expected_output(case: dict[str, Any]) -> None:
    expected = _EXPECTED["cases"][case["case_id"]]
    outcome = _run_case(case)
    if expected["outcome"] == "REJECTED":
        assert isinstance(outcome, P2T4FusionInputRejectionV2)
    else:
        assert isinstance(outcome, P2T4FusedResultV1)
        assert outcome.status.value == expected["outcome"]
    assert canonical_projection(outcome) == expected["result"]
    assert json.loads(canonical_json(outcome)) == expected["result"]
    assert canonical_sha256(outcome) == expected["canonical_sha256"]


@pytest.mark.parametrize("case", _CASE_LIST, ids=_CASE_IDS)
def test_canonical_bytes_match_the_independent_oracle(case: dict[str, Any]) -> None:
    outcome = _run_case(case)
    assert canonical_bytes(outcome) == _oracle_canonical_bytes(outcome)
    assert canonical_bytes(_run_case(case)) == canonical_bytes(outcome)
    assert canonical_sha256(outcome) == hashlib.sha256(_oracle_canonical_bytes(outcome)).hexdigest()


_FIXED_OUTPUT_VOCABULARY = frozenset(
    {
        "P2T4FusedResultV1",
        "P2T4FusionInputRejectionV2",
        "P2T4UpstreamFailureRefV1",
        "1.0",
        "2.0",
        "FUSED",
        "UPSTREAM_FAILURE",
        "REJECTED",
        "SUCCEEDED",
        "FAILED",
        "UNKNOWN",
        "NONE",
        "AGREEMENT_WEIGHTED_V1",
        "2026-09-15T12:00:00.000000Z",
        "P2.AsrResultV1@1.0",
        "P2.VisionUnderstandingResultV1@1.0",
        "P2.VisionUnderstandingResultV2@2.0",
        "FEAT018.LiveAsrResultV1@1.0",
        "FEAT018.LiveVisionUnderstandingResultV1@1.0",
        "DECLARED",
        "MIXED",
        "NOT_DETERMINED",
    }
)
_CLOSED_VOCABULARY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+$")
_HEX_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_CONFLICT_ID_PATTERN = re.compile(r"^P2T4-CONFLICT-[a-f0-9]{64}$")


def _string_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for element in value for item in _string_values(element)]
    if isinstance(value, dict):
        return [item for element in value.values() for item in _string_values(element)]
    return []


def _vision_sourced_strings(case: dict[str, Any]) -> set[str]:
    """Strings that may legitimately be copied from the validated Vision source."""

    spec = case["vision"]
    if spec["kind"] != "P2_SUCCESS":
        return set()
    allowed: set[str] = set()
    for collection in ("entities", "actions", "themes"):
        for candidate in spec.get(collection, []):
            allowed.add(candidate["observation_id"])
            allowed.add(candidate["label"])
            allowed.update(candidate.get("language", []))
            allowed.update(candidate.get("evidence_refs", []))
            for key in ("actor_ref", "object_ref"):
                if candidate.get(key):
                    allowed.add(candidate[key])
    for relation in spec.get("relations", []):
        allowed.update(
            {
                relation["observation_id"],
                relation["predicate"],
                relation["subject_ref"],
                relation["object_ref"],
            }
        )
    return allowed


@pytest.mark.parametrize("case", _CASE_LIST, ids=_CASE_IDS)
def test_outputs_carry_only_closed_tokens_ids_digests_and_vision_text(case: dict[str, Any]) -> None:
    """Positive allowlist: every output string is a closed token, an ID, a digest, or Vision text.

    ASR segment text, `transcript_raw`, raw inputs, exception text, paths, and provider
    material can therefore never appear, and a rejection can never echo a candidate label.
    """

    outcome = _run_case(case)
    text = canonical_json(outcome)
    for fragment in _FORBIDDEN_OUTPUT_FRAGMENTS:
        assert fragment not in text
    assert not _discloses_sentinel(text, repr(outcome))
    assert _SUPERSEDED_REJECTION_NAME not in text
    assert not _ABSOLUTE_PATH_PATTERN.search(text)
    allowed = _FIXED_OUTPUT_VOCABULARY | {_ENVELOPE["correlation_id"]}
    if isinstance(outcome, P2T4FusedResultV1):
        allowed |= _vision_sourced_strings(case)
    for value in _string_values(json.loads(text)):
        assert (
            value in allowed
            or _CLOSED_VOCABULARY_PATTERN.match(value)
            or _HEX_PATTERN.match(value)
            or _CONFLICT_ID_PATTERN.match(value)
        ), value
    if case["asr"]["kind"] == "P2_SUCCESS":
        for segment in case["asr"]["segments"]:
            assert f'"{segment["text"]}"' not in text or segment["text"] in allowed


def test_fixture_files_contain_no_paths_secrets_or_provider_material() -> None:
    for name in ("manifest-v1.json", "cases-v1.json", "expected-v1.json"):
        text = (_FIXTURE_DIR / name).read_text(encoding="utf-8")
        assert not _ABSOLUTE_PATH_PATTERN.search(text), name
        for fragment in ("http://", "https://", "Bearer ", "sk-", "api_key", "password"):
            assert fragment not in text, name


# --- conflict identifiers, digests, and canonical form ------------------------------------


def test_conflict_id_uses_exact_nul_delimited_sha256_bytes() -> None:
    outcome = _run_case(_case("entity-negation-contradiction"))
    assert isinstance(outcome, P2T4FusedResultV1)
    (conflict,) = outcome.conflicts
    assert conflict.conflict_id == _oracle_conflict_id("ENTITY_ATTRIBUTE_CONTRADICTION", "e-house")
    assert conflict.conflict_id == (
        "P2T4-CONFLICT-" + hashlib.sha256(b"ENTITY_ATTRIBUTE_CONTRADICTION\x00e-house").hexdigest()
    )


def test_expected_conflict_ids_were_authored_from_the_byte_algorithm() -> None:
    for expected in _EXPECTED["cases"].values():
        for conflict in expected["result"].get("conflicts", []):
            assert conflict["conflict_id"] == _oracle_conflict_id(
                conflict["reason_code"], conflict["vision_claim_ref"]
            )


def test_source_digest_binds_the_complete_source_but_transcript_never_matches() -> None:
    case = copy.deepcopy(_case("agreement-all-kinds"))
    baseline = _run_case(case)
    case["asr"]["overrides"] = {"transcript_raw": "house child draws"}
    changed = _run_case(case)
    assert isinstance(baseline, P2T4FusedResultV1)
    assert isinstance(changed, P2T4FusedResultV1)
    assert (
        baseline.source_asr_result_ref.result_sha256 != changed.source_asr_result_ref.result_sha256
    )
    assert baseline.source_vision_result_ref == changed.source_vision_result_ref
    assert (
        baseline.model_copy(update={"source_asr_result_ref": changed.source_asr_result_ref})
        == changed
    )


def test_transcript_raw_is_not_a_matching_source() -> None:
    case = copy.deepcopy(_case("vision-only-empty-transcript"))
    case["asr"]["overrides"] = {"transcript_raw": "the house"}
    outcome = _run_case(case)
    assert isinstance(outcome, P2T4FusedResultV1)
    assert outcome.entities[0].narration_support_applied is False


def test_policy_hash_retains_the_exact_increment_string() -> None:
    policy = _policy(_case("agreement-all-kinds"))
    text = canonical_json(policy)
    assert '"corroboration_increment":"0.10"' in text
    assert (
        '"negation_cues":[["not"],["no"],["never"],["isn","t"],["doesn","t"],["didn","t"]]' in text
    )
    assert (
        canonical_sha256(policy)
        == _EXPECTED["cases"]["agreement-all-kinds"]["result"]["fusion_policy_config_hash"]
    )


def test_executed_at_offsets_are_normalized_to_utc_in_canonical_json() -> None:
    asr, vision = _typed_success_pair("agreement-all-kinds")
    policy = _policy(_case("agreement-all-kinds"))
    offset = datetime(2026, 9, 15, 19, 0, 0, tzinfo=timezone(timedelta(hours=7)))
    result = fuse(asr, vision, policy, offset)
    assert '"executed_at":"2026-09-15T12:00:00.000000Z"' in canonical_json(result)
    assert canonical_bytes(result) == canonical_bytes(fuse(asr, vision, policy, _executed_at()))


def test_vision_source_order_never_changes_evidence_ranking_or_conflicts() -> None:
    case = copy.deepcopy(_case("group-ranking-and-cap"))
    baseline = _run_case(case)
    case["vision"]["entities"] = list(reversed(case["vision"]["entities"]))
    permuted = _run_case(case)
    assert isinstance(baseline, P2T4FusedResultV1)
    assert isinstance(permuted, P2T4FusedResultV1)
    assert permuted.uncertainty == baseline.uncertainty
    assert permuted.conflicts == baseline.conflicts
    assert [entity.fused_observation_id for entity in permuted.entities] == list(
        reversed([entity.fused_observation_id for entity in baseline.entities])
    )
    assert {e.fused_observation_id for e in permuted.entities if e.primary_interpretation} == {
        e.fused_observation_id for e in baseline.entities if e.primary_interpretation
    }


def test_adjustment_never_feeds_back_into_low_confidence_classification() -> None:
    outcome = _run_case(_case("confidence-floor-boundaries"))
    assert isinstance(outcome, P2T4FusedResultV1)
    fish = next(entity for entity in outcome.entities if entity.fused_observation_id == "e-fish")
    assert fish.narration_support_applied is True
    assert fish.primary_interpretation is False
    assert any(
        conflict.vision_claim_ref == "e-fish"
        and conflict.reason_code.value == "LOW_CONFIDENCE_EVIDENCE"
        and conflict.narration_claim_ref is not None
        for conflict in outcome.conflicts
    )
    row = next(row for row in outcome.uncertainty.per_observation if row.observation_id == "e-fish")
    assert row.certainty_status.value == "NOT_APPLICABLE_CONFLICTING"
    assert row.certainty is None


# --- pure typed boundary ------------------------------------------------------------------


def test_typed_fuse_raises_a_closed_error_for_duplicate_segment_indexes() -> None:
    case = _case("duplicate-segment-index-rejection")
    asr = AsrSuccessV1.model_validate(_build_p2_asr(case["asr"]))
    vision = VisionUnderstandingSuccessV1.model_validate(
        _build_p2_vision(case["vision"], _policy(case))
    )
    with pytest.raises(P2T4FusionInputError) as info:
        fuse(asr, vision, _policy(case), _executed_at())
    assert str(info.value) == "INVALID_STRUCTURE"
    assert (
        canonical_projection(info.value.rejection) == _EXPECTED["cases"][case["case_id"]]["result"]
    )
    assert "a dog" not in str(info.value) and "a cat" not in str(info.value)


def test_typed_fuse_raises_a_closed_error_for_correlation_mismatch() -> None:
    case = _case("correlation-mismatch-before-status")
    asr = AsrSuccessV1.model_validate(_build_p2_asr(case["asr"]))
    vision = VisionUnderstandingFailureV1.model_validate(
        _build_p2_vision(case["vision"], _policy(case))
    )
    with pytest.raises(P2T4FusionInputError) as info:
        fuse(asr, vision, _policy(case), _executed_at())
    assert info.value.rejection.input_slot is P2T4InputSlot.BOTH
    assert info.value.rejection.code is P2T4RejectionCode.CORRELATION_MISMATCH
    assert "corr-p2t4" not in str(info.value)


def test_typed_fuse_requires_timezone_aware_execution_time() -> None:
    asr, vision = _typed_success_pair("agreement-all-kinds")
    with pytest.raises(ValueError, match="timezone aware"):
        fuse(asr, vision, _policy(_case("agreement-all-kinds")), datetime(2026, 9, 15, 12, 0))


def test_typed_fuse_has_no_object_or_provider_shaped_overload() -> None:
    asr, vision = _typed_success_pair("agreement-all-kinds")
    policy = _policy(_case("agreement-all-kinds"))
    with pytest.raises(TypeError):
        fuse(asr.model_dump(), vision, policy, _executed_at())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        fuse(asr, vision.model_dump(), policy, _executed_at())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        fuse(asr, vision, policy.model_dump(), _executed_at())  # type: ignore[arg-type]


def test_typed_fuse_accepts_typed_failures_and_matches_the_outer_boundary() -> None:
    case = _case("both-failures")
    asr = AsrFailureV1.model_validate(_build_p2_asr(case["asr"]))
    vision = VisionUnderstandingFailureV1.model_validate(
        _build_p2_vision(case["vision"], _policy(case))
    )
    typed = fuse(asr, vision, _policy(case), _executed_at())
    assert canonical_bytes(typed) == canonical_bytes(_run_case(case))
    assert typed.upstream_failure is not None
    assert typed.upstream_failure.vision_failure_ref is not None
    assert typed.upstream_failure.vision_failure_ref.error_detail is (
        VisionNonPolicyErrorDetail.OUTPUT_MAPPING_FAILED
    )


# --- strict validation edge cases that JSON fixtures cannot encode -------------------------


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_confidence_is_a_strict_validation_rejection(value: float) -> None:
    case = copy.deepcopy(_case("asr-only-narration"))
    vision = _build_p2_vision(case["vision"], _policy(case))
    vision["entities"][0]["confidence"] = value
    outcome = validate_and_fuse(_build_p2_asr(case["asr"]), vision, _policy(case), _executed_at())
    assert isinstance(outcome, P2T4FusionInputRejectionV2)
    assert outcome.input_slot is P2T4InputSlot.VISION
    assert outcome.phase is P2T4RejectionPhase.STRICT_VALIDATION
    assert outcome.code is P2T4RejectionCode.INVALID_STRUCTURE
    assert outcome.field_code is P2T4RejectionFieldCode.NONE
    assert "nan" not in canonical_json(outcome).lower()


def test_naive_upstream_datetime_is_a_strict_validation_rejection() -> None:
    case = copy.deepcopy(_case("asr-only-narration"))
    asr = _build_p2_asr(case["asr"])
    asr["executed_at"] = datetime(2026, 9, 15, 0, 0, 1)
    outcome = validate_and_fuse(
        asr, _build_p2_vision(case["vision"], _policy(case)), _policy(case), _executed_at()
    )
    assert isinstance(outcome, P2T4FusionInputRejectionV2)
    assert outcome.input_slot is P2T4InputSlot.ASR
    assert outcome.phase is P2T4RejectionPhase.STRICT_VALIDATION
    assert outcome.code is P2T4RejectionCode.INVALID_STRUCTURE


def test_extra_fields_are_a_strict_validation_rejection() -> None:
    case = copy.deepcopy(_case("asr-only-narration"))
    asr = _build_p2_asr(case["asr"])
    asr["provider_payload"] = {"raw": "never copied"}
    outcome = validate_and_fuse(
        asr, _build_p2_vision(case["vision"], _policy(case)), _policy(case), _executed_at()
    )
    assert isinstance(outcome, P2T4FusionInputRejectionV2)
    assert outcome.code is P2T4RejectionCode.INVALID_STRUCTURE
    assert "never copied" not in canonical_json(outcome)


def test_policy_rejects_altered_cues_and_non_finite_floor() -> None:
    payload = dict(_CASES["policy"])
    payload["negation_cues"] = [["not"], ["no"]]
    with pytest.raises(ValidationError):
        P2T4FusionPolicyConfigV1.model_validate(payload)
    payload = dict(_CASES["policy"])
    payload["confidence_floor"] = float("nan")
    with pytest.raises(ValidationError):
        P2T4FusionPolicyConfigV1.model_validate(payload)
    payload = dict(_CASES["policy"])
    payload["corroboration_increment"] = "0.1"
    with pytest.raises(ValidationError):
        P2T4FusionPolicyConfigV1.model_validate(payload)
