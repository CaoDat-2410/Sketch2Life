"""Independent integrity checks for the approved synthetic mapping diagnostic inputs."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import RFC_4122, UUID

import pytest

from sketch2life.contracts.schemas.vision_v2 import VisionProfileIdV2

ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / "tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json"
PROFILE_PATH = "data/activity-catalog/golden/v1/semantic-anchor-profiles.v1.json"
ACTIVITY_PATH = "data/activity-catalog/golden/v1/activities.v2.json"
PILOT_PATH = "features/FEAT-018-live-image-canvas-flow/plan/ACTIVITY_PILOT_MATRIX.md"
PILOT_IDS = (
    "ACT-0004", "ACT-0016", "ACT-0019", "ACT-0020", "ACT-0023",
    "ACT-0026", "ACT-0030", "ACT-0033", "ACT-0039", "ACT-0046",
    "ACT-0055", "ACT-0058", "ACT-0061", "ACT-0067", "ACT-0074",
    "ACT-0085", "ACT-0087", "ACT-0091", "ACT-0097", "ACT-0099",
)
FAMILIES = ("EXACT", "AMBIGUOUS", "NO_MATCH", "CONFLICT", "LOW", "ADULT_CORRECTION")
SUPPLEMENTAL_SCENARIOS = (
    "VISION_NULL_CONFIDENCE",
    "ASR_NULL_CONFIDENCE",
    "UNCERTAINTY_NOT_PROVIDED",
    "UNCERTAINTY_UPSTREAM_PROVIDED",
    "UNCERTAINTY_STATUS_MISMATCH",
    "AMBIGUOUS_REGION_ONLY",
    "TEXT_TYPED_CONFLICT",
    "NARRATION_SOURCE_STATUS_MISMATCH",
    "DUPLICATE_CLAIM_ID",
    "DANGLING_CONFLICT_REF",
    "SOURCE_HASH_MISMATCH",
    "CORRELATION_MISMATCH",
    "UNKNOWN_CONFIRMED_CLAIM",
    "STALE_SESSION_VERSION",
    "V1_ADULT_CORRECTION",
    "SUCCESSIVE_MEANING_VERSIONS",
    "V2_MISSING_ADULT_LABEL",
    "NON_DEMO_ACTOR",
    "AMBIGUOUS_TARGET_ONLY",
    "ADULT_EMPTY_CONFIRMED",
    "SWALLOWED_AUTORIG_CALL",
    "V2_WORD_BOUNDARY",
    "V2_WHITESPACE",
)
APPROVAL = {
    "source_commit": "b39a9f2f56509b0543184876eb538fc9faf0e1aa",
    "plan_sha256": "1482c047476049e44ecd515178d64b2d4c9e60d13511c92aa8112fd5269d2d66",
    "input_sha256": "98dade81e57045efd8f6a38101e4d80e01a8518e505c1f44e7d33a0acf1575a2",
}


@pytest.fixture
def manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _assert_source_bindings(manifest: dict[str, Any]) -> dict[str, Any]:
    sources = manifest["source_files"]
    paths = [source["path"] for source in sources]
    assert len(paths) == len(set(paths)) == 3, "source file inventory"
    assert set(paths) == {PROFILE_PATH, ACTIVITY_PATH, PILOT_PATH}, "source file inventory"
    for source in sources:
        assert set(source) == {"path", "sha256"}, "source file fields"
        actual_digest = hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest()
        assert source["sha256"] == actual_digest, "source file digest"

    golden = json.loads((ROOT / ACTIVITY_PATH).read_text(encoding="utf-8"))
    assert Counter((row["id"], row["version"]) for row in golden["activities"]) == Counter(
        (activity_id, 2) for activity_id in PILOT_IDS
    ), "golden activity identities"
    golden_table = (ROOT / PILOT_PATH).read_text(encoding="utf-8").split("## MVP 100")[0]
    assert re.findall(r"^\| (ACT-\d{4}) \| 2 \|", golden_table, re.MULTILINE) == list(
        PILOT_IDS
    ), "approved pilot order"

    profiles = json.loads((ROOT / PROFILE_PATH).read_text(encoding="utf-8"))["profiles"]
    assert len(profiles) == 100
    assert len({profile["activity_id"] for profile in profiles}) == 100
    return {profile["activity_id"]: profile for profile in profiles}


def _assert_primary_recipe(case: dict[str, Any], profiles: dict[str, Any]) -> None:
    activity_id, family = case["activity_id"], case["family"]
    assert activity_id in PILOT_IDS and family in FAMILIES, "primary coverage identity"
    case_id = f"feat018-p2-t4-{activity_id.lower()}-{family.lower().replace('_', '-')}"
    assert case["case_id"] == case_id, "primary case identity"
    assert case["activity_version"] == 2, "golden activity version"
    profile = profiles[activity_id]
    assert case["profile"] == {
        "id": profile["profile_id"],
        "version": profile["profile_version"],
        "activity_version": profile["activity_version"],
        "provenance_sha256": profile["provenance_sha256"],
        "exact_phrase": profile["exact_phrases_vi"][0],
        "fallback_tier": profile["fallback_tier"],
    }, "legacy profile identity and reviewed vocabulary"
    assert case["profile"]["version"] == case["profile"]["activity_version"] == 1

    assert case["source_image_ref"] == {
        "artifact_ref": f"fixture:feat018-p2-t4:{case_id}",
        "sha256": hashlib.sha256(f"synthetic-fixture-image:{case_id}".encode()).hexdigest(),
    }, "synthetic source identity"
    assert case["correlation_id"] == case_id, "correlation identity"
    session_id = UUID(case["session_id"])
    assert session_id.version == 4 and session_id.variant == RFC_4122, "UUIDv4 session identity"

    partner_id = PILOT_IDS[(PILOT_IDS.index(activity_id) + 1) % len(PILOT_IDS)]
    partner_phrase = profiles[partner_id]["exact_phrases_vi"][0]
    target_phrase = (
        "zzfixture-no-reviewed-match-018" if family == "NO_MATCH"
        else profile["exact_phrases_vi"][0]
    )
    entities = [{
        "observation_id": "vision-target",
        "label": target_phrase,
        "confidence": 0.05 if family == "LOW" else 0.90,
    }]
    if family == "AMBIGUOUS":
        entities.append({
            "observation_id": "vision-partner", "label": partner_phrase, "confidence": 0.90,
        })
    assert case["entities"] == entities, "Vision recipe and numeric confidence"
    if family == "CONFLICT":
        assert case["asr_claims"] == [{
            "claim_id": "narration-partner", "text": partner_phrase,
            "confidence": None, "source": "ASR",
        }], "ASR modality and nullable confidence"
        assert case["narration_status"] == "ASR_SUCCEEDED", "narration source/status"
        assert case["narration_text"] == partner_phrase, "bound narration text"
    else:
        assert case["asr_claims"] == [], "unexpected ASR claim"
        assert case["narration_status"] == "NOT_SUPPLIED", "narration source/status"
        assert case["narration_text"] == "", "absent narration text"

    conflicts = []
    if family in {"AMBIGUOUS", "CONFLICT"}:
        conflicts = [{
            "conflict_id": "conflict-primary",
            "claim_refs": [
                "vision-target", "vision-partner" if family == "AMBIGUOUS"
                else "narration-partner",
            ],
            "code": "UNRESOLVED_AMBIGUITY" if family == "AMBIGUOUS"
            else "SOURCE_DISAGREEMENT",
        }]
    assert case["conflicts"] == conflicts, "explicit conflict references"

    adult = family == "ADULT_CORRECTION"
    assert case["confirmation"] == {
        "version": 2 if adult else 1,
        "actor_ref": "demo:local",
        "confirmed_claim_ids": ["vision-target", "vision-partner"] if family == "AMBIGUOUS"
        else ["vision-target"],
        "primary_anchor_id": None if adult else "vision-target",
        "meaning_version": 2 if adult else 1,
        "adult_subject_label": f"nhãn người lớn thử nghiệm {activity_id}" if adult else None,
        "correction": None,
    }, "explicit confirmation recipe and attribution"

    expected_mode = "EXACT"
    if family == "ADULT_CORRECTION":
        expected_mode = "OBSERVE"
        expected_v2_mode = "OBSERVE_ONLY"
    elif family == "NO_MATCH":
        expected_mode = "SAFE_FALLBACK" if profile["fallback_tier"] != "NONE" else "NONE"
        expected_v2_mode = "NO_PERSONALIZED_MATCH"
    else:
        expected_v2_mode = "PERSONALIZED_EXACT"
    assert case["expected"]["target_v1_mode"] == expected_mode, "boundary-specific expectation"
    assert case["expected"]["target_v2_mode"] == expected_v2_mode, (
        "V2 matcher boundary-specific expectation"
    )
    assert isinstance(case["expected"]["notes"], str) and case["expected"]["notes"].strip()


def _assert_supplemental_inventory(manifest: dict[str, Any], profiles: dict[str, Any]) -> None:
    supplemental = manifest["supplemental_cases"]
    assert len(supplemental) == 43, "supplemental inventory count"
    b1_outcomes = {
        "VISION_NULL_CONFIDENCE": "REJECT_INVALID_VISION_CONFIDENCE",
        "ASR_NULL_CONFIDENCE": "ACCEPT_NULL_ASR_CONFIDENCE",
        "UNCERTAINTY_NOT_PROVIDED": "ACCEPT_NOT_PROVIDED_UNCERTAINTY",
        "UNCERTAINTY_UPSTREAM_PROVIDED": "PRESERVE_UPSTREAM_UNCERTAINTY",
        "UNCERTAINTY_STATUS_MISMATCH": "REJECT_INCONSISTENT_UNCERTAINTY",
        "AMBIGUOUS_REGION_ONLY": "PRESERVE_NON_SELECTABLE_AMBIGUITY",
        "TEXT_TYPED_CONFLICT": "PRESERVE_TYPED_TEXT_CONFLICT",
        "NARRATION_SOURCE_STATUS_MISMATCH": "OBSERVE_ACCEPTED_SOURCE_STATUS_GAP",
        "DUPLICATE_CLAIM_ID": "REJECT_DUPLICATE_CLAIM_ID",
        "DANGLING_CONFLICT_REF": "REJECT_DANGLING_CONFLICT_REFERENCE",
        "SOURCE_HASH_MISMATCH": "REJECT_SOURCE_HASH_MISMATCH",
        "CORRELATION_MISMATCH": "REJECT_CORRELATION_MISMATCH",
    }
    b2_outcomes = {
        "UNKNOWN_CONFIRMED_CLAIM": "REJECT_UNKNOWN_CONFIRMED_CLAIM",
        "STALE_SESSION_VERSION": "REJECT_STALE_SESSION_VERSION",
        "V1_ADULT_CORRECTION": "OBSERVE_CORRECTION_PROVENANCE",
        "SUCCESSIVE_MEANING_VERSIONS": "OBSERVE_MEANING_AND_ANCHOR_VERSIONS",
        "V2_MISSING_ADULT_LABEL": "REJECT_MISSING_ADULT_LABEL",
        "NON_DEMO_ACTOR": "REJECT_NON_DEMO_ACTOR",
        "AMBIGUOUS_TARGET_ONLY": "OBSERVE_AMBIGUOUS_TARGET_ONLY_CONFIRMATION",
        "ADULT_EMPTY_CONFIRMED": "OBSERVE_EMPTY_ADULT_CONFIRMATION",
        "SWALLOWED_AUTORIG_CALL": "OBSERVE_INJECTED_AUTORIG_CALL_COUNT",
    }
    expected_requirement_status = {
        "VISION_NULL_CONFIDENCE": "EXPECTED_BLOCKED",
        "ASR_NULL_CONFIDENCE": "SATISFIED",
        "UNCERTAINTY_NOT_PROVIDED": "SATISFIED",
        "UNCERTAINTY_UPSTREAM_PROVIDED": "SATISFIED",
        "UNCERTAINTY_STATUS_MISMATCH": "EXPECTED_BLOCKED",
        "AMBIGUOUS_REGION_ONLY": "SATISFIED",
        "TEXT_TYPED_CONFLICT": "SATISFIED",
        "NARRATION_SOURCE_STATUS_MISMATCH": "UNRESOLVED",
        "DUPLICATE_CLAIM_ID": "EXPECTED_BLOCKED",
        "DANGLING_CONFLICT_REF": "EXPECTED_BLOCKED",
        "SOURCE_HASH_MISMATCH": "EXPECTED_BLOCKED",
        "CORRELATION_MISMATCH": "EXPECTED_BLOCKED",
        "UNKNOWN_CONFIRMED_CLAIM": "EXPECTED_BLOCKED",
        "STALE_SESSION_VERSION": "EXPECTED_BLOCKED",
        "V1_ADULT_CORRECTION": "UNRESOLVED",
        "SUCCESSIVE_MEANING_VERSIONS": "UNRESOLVED",
        "V2_MISSING_ADULT_LABEL": "EXPECTED_BLOCKED",
        "NON_DEMO_ACTOR": "EXPECTED_BLOCKED",
        "AMBIGUOUS_TARGET_ONLY": "SATISFIED",
        "ADULT_EMPTY_CONFIRMED": "SATISFIED",
        "SWALLOWED_AUTORIG_CALL": "SATISFIED",
        "V2_WORD_BOUNDARY": "SATISFIED",
        "V2_WHITESPACE": "SATISFIED",
        "REVIEWED_ALIAS": "SATISFIED",
    }
    expected = {
        f"feat018-p2-t4-supp-{scenario.lower().replace('_', '-')}": {
            "scenario": scenario, "activity_id": "ACT-0004",
            "expected": {
                **({"boundary": "B1", "outcome": b1_outcomes[scenario]}
                         if scenario in b1_outcomes else
                         {"boundary": "B2", "outcome": b2_outcomes[scenario]}
                         if scenario in b2_outcomes else
                         {"boundary": "B3", "target_modes": {
                             "V1_MATCH": ["EXACT"],
                             "V2_MATCH_SCENE": ["NO_PERSONALIZED_MATCH"],
                         }} if scenario == "V2_WORD_BOUNDARY" else
                         {"boundary": "B3", "input_channel": "NARRATION",
                          "target_modes": {"V2_MATCH_SCENE": ["PERSONALIZED_EXACT"]}}),
                "requirement_status": expected_requirement_status[scenario],
            },
        }
        for scenario in SUPPLEMENTAL_SCENARIOS
    }
    for activity_id in PILOT_IDS:
        expected[f"feat018-p2-t4-{activity_id.lower()}-alias"] = {
            "scenario": "REVIEWED_ALIAS", "activity_id": activity_id,
            "label": profiles[activity_id]["aliases_vi"][0],
            "expected": {"boundary": "B3", "requirement_status": "SATISFIED",
                          "target_modes": {
                              "V1_MATCH": ["ALIAS"],
                              "V2_MATCH_SCENE": ["PERSONALIZED_ALIAS"],
                          }},
        }
    observed = {}
    for case in supplemental:
        case_id = case["case_id"]
        assert case_id not in observed, "duplicate supplemental case"
        observed[case_id] = {key: value for key, value in case.items() if key != "case_id"}
    assert observed == expected, "separate named supplemental scenarios and reviewed aliases"
    assert set(observed).isdisjoint(case["case_id"] for case in manifest["primary_cases"])


def _assert_manifest_contract(manifest: dict[str, Any]) -> None:
    assert manifest["schema_name"] == "FEAT018P2T4MappingManifest", "manifest schema identity"
    assert manifest["schema_version"] == 1, "manifest schema version"
    assert manifest["construction_revision"] == "feat018-p2-t4-r3-v1", "construction revision"
    assert manifest["provenance_kind"] == "SYNTHETIC_FIXTURE", "synthetic provenance"
    assert manifest["provider_execution"] == "NOT_EXECUTED", "provider execution exclusion"
    assert manifest["upstream_profile_id"] == (
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1.value
    ), "contract-required model identity"
    assert manifest["approval"] == APPROVAL, "approved source commit and original document digests"
    assert manifest["pilot_ids"] == list(PILOT_IDS), "exact ordered 20-pilot inventory"
    profiles = _assert_source_bindings(manifest)
    primary = manifest["primary_cases"]
    assert len(primary) == 120, "120 primary cases"
    assert Counter((case["activity_id"], case["family"]) for case in primary) == Counter(
        (activity_id, family) for activity_id in PILOT_IDS for family in FAMILIES
    ), "one primary case for each pilot/family"
    assert len({case["case_id"] for case in primary}) == 120, "unique primary case IDs"
    assert len({case["session_id"] for case in primary}) == 120, "distinct synthetic sessions"
    for case in primary:
        _assert_primary_recipe(case, profiles)
    assert {
        case["activity_id"] for case in primary if case["profile"]["fallback_tier"] != "NONE"
    } == {"ACT-0026", "ACT-0055", "ACT-0085"}, "three pilot fallback profiles"
    _assert_supplemental_inventory(manifest, profiles)


def test_approved_manifest_has_complete_independently_attributed_inputs(
    manifest: dict[str, Any],
) -> None:
    _assert_manifest_contract(manifest)


def test_synthetic_execution_marker_is_separate_from_required_model_enum(
    manifest: dict[str, Any],
) -> None:
    assert VisionProfileIdV2(manifest["upstream_profile_id"]) is (
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1
    )
    assert manifest["provenance_kind"] == "SYNTHETIC_FIXTURE"
    assert manifest["provider_execution"] == "NOT_EXECUTED"
    with pytest.raises(ValueError):
        VisionProfileIdV2(manifest["provenance_kind"])


@pytest.mark.parametrize("mutation", [
    "missing-pilot", "duplicate-pilot", "extra-pilot", "missing-family", "duplicate-family",
    "extra-family", "missing-source", "duplicate-source", "wrong-source-digest",
    "duplicate-session", "missing-supplemental", "duplicate-supplemental",
    "primary-as-supplemental", "missing-supplemental-expectation",
    "wrong-supplemental-outcome", "wrong-target-v1-mode",
])
def test_manifest_rejects_broken_inventories(manifest: dict[str, Any], mutation: str) -> None:
    broken = deepcopy(manifest)
    if mutation == "missing-pilot":
        broken["pilot_ids"].pop()
    elif mutation == "duplicate-pilot":
        broken["pilot_ids"][-1] = broken["pilot_ids"][0]
    elif mutation == "extra-pilot":
        broken["pilot_ids"].append("ACT-0001")
    elif mutation == "missing-family":
        broken["primary_cases"].pop()
    elif mutation == "duplicate-family":
        broken["primary_cases"][-1] = deepcopy(broken["primary_cases"][0])
    elif mutation == "extra-family":
        broken["primary_cases"].append(deepcopy(broken["primary_cases"][0]))
    elif mutation == "missing-source":
        broken["source_files"].pop()
    elif mutation == "duplicate-source":
        broken["source_files"][-1] = deepcopy(broken["source_files"][0])
    elif mutation == "wrong-source-digest":
        broken["source_files"][0]["sha256"] = "0" * 64
    elif mutation == "duplicate-session":
        broken["primary_cases"][-1]["session_id"] = broken["primary_cases"][0]["session_id"]
    elif mutation == "missing-supplemental":
        broken["supplemental_cases"].pop()
    elif mutation == "duplicate-supplemental":
        broken["supplemental_cases"][-1] = deepcopy(broken["supplemental_cases"][0])
    elif mutation == "missing-supplemental-expectation":
        del broken["supplemental_cases"][0]["expected"]
    elif mutation == "wrong-supplemental-outcome":
        broken["supplemental_cases"][0]["expected"]["outcome"] = "ACCEPT_NULL_ASR_CONFIDENCE"
    elif mutation == "wrong-target-v1-mode":
        next(case for case in broken["primary_cases"] if case["family"] == "EXACT")[
            "expected"]["target_v1_mode"
        ] = "OBSERVE"
    else:
        broken["supplemental_cases"][-1]["case_id"] = broken["primary_cases"][0]["case_id"]
    with pytest.raises(AssertionError):
        _assert_manifest_contract(broken)


@pytest.mark.parametrize(("path", "replacement", "reason"), [
    (("schema_version",), 2, "manifest schema version"),
    (("construction_revision",), "unapproved", "construction revision"),
    (("provenance_kind",), "MODEL_EXECUTION", "synthetic provenance"),
    (("provider_execution",), "EXECUTED", "provider execution exclusion"),
    (("upstream_profile_id",), "SYNTHETIC_FIXTURE", "contract-required model identity"),
    (("approval", "source_commit"), "0" * 40, "approved source commit"),
    (("approval", "plan_sha256"), "0" * 64, "approved source commit"),
    (("approval", "input_sha256"), "0" * 64, "approved source commit"),
])
def test_manifest_rejects_unapproved_identity(
    manifest: dict[str, Any], path: tuple[str, ...], replacement: Any, reason: str,
) -> None:
    broken = deepcopy(manifest)
    target = broken
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(AssertionError, match=reason):
        _assert_manifest_contract(broken)


@pytest.mark.parametrize(("family", "path", "replacement", "reason"), [
    ("EXACT", ("activity_version",), 1, "golden activity version"),
    ("EXACT", ("profile", "id"), "SAP-ACT-0001-V1", "legacy profile identity"),
    ("EXACT", ("profile", "version"), 2, "legacy profile identity"),
    ("EXACT", ("profile", "activity_version"), 2, "legacy profile identity"),
    ("EXACT", ("profile", "provenance_sha256"), "0" * 64, "legacy profile identity"),
    ("EXACT", ("profile", "exact_phrase"), "English pilot seed", "reviewed vocabulary"),
    ("EXACT", ("source_image_ref", "sha256"), "0" * 64, "synthetic source identity"),
    ("EXACT", ("source_image_ref", "artifact_ref"), "fixture:other", "synthetic source identity"),
    ("EXACT", ("correlation_id",), "stale-request", "correlation identity"),
    ("EXACT", ("session_id",), "00000000-0000-1000-8000-000000000001", "UUIDv4"),
    ("EXACT", ("confirmation", "actor_ref"), "", "confirmation recipe"),
    ("EXACT", ("confirmation", "actor_ref"), "demo:other", "confirmation recipe"),
    ("EXACT", ("confirmation", "meaning_version"), 2, "confirmation recipe"),
    ("EXACT", ("confirmation", "version"), 2, "confirmation recipe"),
    ("EXACT", ("confirmation", "correction"), "changed", "confirmation recipe"),
    ("EXACT", ("confirmation", "confirmed_claim_ids"), ["unknown"], "confirmation recipe"),
    (
        "AMBIGUOUS", ("confirmation", "confirmed_claim_ids"), ["vision-target"],
        "confirmation recipe",
    ),
    (
        "AMBIGUOUS", ("conflicts", 0, "claim_refs"), ["vision-target", "dangling"],
        "conflict references",
    ),
    ("AMBIGUOUS", ("conflicts", 0, "claim_refs"), ["vision-target"] * 2, "conflict references"),
    ("CONFLICT", ("asr_claims", 0, "source"), "TEXT_TYPED", "ASR modality"),
    ("CONFLICT", ("asr_claims", 0, "confidence"), 0.90, "nullable confidence"),
    ("CONFLICT", ("narration_status",), "TEXT_SUPPLIED", "narration source/status"),
    ("CONFLICT", ("narration_text",), "", "bound narration text"),
    ("CONFLICT", ("narration_text",), "different transcript", "bound narration text"),
    ("LOW", ("entities", 0, "confidence"), None, "numeric confidence"),
    ("LOW", ("entities", 0, "confidence"), 0.90, "numeric confidence"),
    ("ADULT_CORRECTION", ("confirmation", "confirmed_claim_ids"), [], "confirmation recipe"),
    (
        "ADULT_CORRECTION", ("confirmation", "primary_anchor_id"), "vision-target",
        "confirmation recipe",
    ),
    ("ADULT_CORRECTION", ("confirmation", "adult_subject_label"), " ", "confirmation recipe"),
    ("ADULT_CORRECTION", ("confirmation", "meaning_version"), 1, "confirmation recipe"),
    ("NO_MATCH", ("entities", 0, "label"), "English seed", "Vision recipe"),
    ("NO_MATCH", ("expected", "target_v1_mode"), "EXACT", "boundary-specific expectation"),
    ("EXACT", ("expected", "target_v2_mode"), "OBSERVE_ONLY", "V2 matcher boundary-specific"),
])
def test_manifest_rejects_invalid_primary_recipes(
    manifest: dict[str, Any], family: str, path: tuple[str | int, ...],
    replacement: Any, reason: str,
) -> None:
    broken = deepcopy(manifest)
    case = next(case for case in broken["primary_cases"] if case["family"] == family)
    target = case
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(AssertionError, match=reason):
        _assert_manifest_contract(broken)
