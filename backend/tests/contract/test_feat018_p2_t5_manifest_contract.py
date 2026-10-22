"""Freeze the approved offline fixture protocol without crediting held requirements."""

from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from sketch2life.benchmark.feat018_p2_t5_evaluation import load_manifest

ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / (
    "features/FEAT-018-live-image-canvas-flow/fixtures/"
    "feat018-p2-t5-evaluation-manifest-v1.json"
)
T4_SOURCE = "tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json"
PILOTS = (
    "ACT-0004", "ACT-0016", "ACT-0019", "ACT-0020", "ACT-0023",
    "ACT-0026", "ACT-0030", "ACT-0033", "ACT-0039", "ACT-0046",
    "ACT-0055", "ACT-0058", "ACT-0061", "ACT-0067", "ACT-0074",
    "ACT-0085", "ACT-0087", "ACT-0091", "ACT-0097", "ACT-0099",
)
FAMILIES = ("exact", "ambiguous", "no-match", "conflict", "low", "adult-correction")
CONTRACT_LOCKS = {
    (
        "VisionUnderstandingResultV2", "2.0",
        "backend/src/sketch2life/contracts/schemas/vision_v2.py",
        "BEA0511C400B452B86FF32A90CB5F65DF4C191A72A857B1024C30A65628CD0D8",
    ),
    (
        "RawUnderstandingResultV1", "1.0",
        "backend/src/sketch2life/contracts/schemas/raw_understanding.py",
        "9A5350A7A6913C2FC4F9F3008AA3BCEBA652D90CD25F3CFE76F598B053A57E0B",
    ),
    (
        "AsrResultV1", "1.0",
        "backend/src/sketch2life/contracts/schemas/asr.py",
        "1DCF8DB144EBFD080266F05B8E75AE404EC230EDC7983937A0E598E48C0B9B22",
    ),
}


def _write_candidate(tmp_path: Path, manifest: dict[str, Any]) -> Path:
    candidate = tmp_path / "candidate-manifest.json"
    candidate.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return candidate


def test_manifest_pins_the_selected_contracts_and_asr_port() -> None:
    manifest = load_manifest(MANIFEST_PATH, ROOT)
    actual = {
        (lock["contract"], lock["version"], lock["path"], lock["sha256"].upper())
        for lock in manifest["contract_locks"]
    }
    assert actual == CONTRACT_LOCKS
    assert {
        "path": "backend/src/sketch2life/application/ports/asr.py",
        "sha256": "92E9E68AA7C428A72CC366FF540F4D5F1BF3BFA2605AEC059B9DC20E9E84F9D6",
    } in manifest["source_locks"]
    assert manifest["provider_execution"] == "NOT_EXECUTED"
    assert manifest["live_metrics"] == "NOT_MEASURED"
    assert manifest["full_task_status"] == "OPEN"


def test_all_pilots_have_six_qualified_slots_and_only_recipe_reuse() -> None:
    manifest = load_manifest(MANIFEST_PATH, ROOT)
    expected = {
        f"feat018-p2-t5-{activity_id.lower()}-{family}"
        for activity_id in PILOTS for family in FAMILIES
    }
    profiles = manifest["profiles"]
    assert len(profiles) == 120
    assert {row["fixture_id"] for row in profiles} == expected
    assert Counter(row["activity_id"] for row in profiles) == dict.fromkeys(PILOTS, 6)
    assert Counter(row["family"] for row in profiles) == dict.fromkeys(FAMILIES, 20)
    t4 = json.loads((ROOT / T4_SOURCE).read_text(encoding="utf-8"))
    recipes = {
        case["activity_id"]: case["profile"]["exact_phrase"]
        for case in t4["primary_cases"] if case["family"] == "EXACT"
    }
    for row in profiles:
        assert row["activity_version"] == 2
        assert row["recipe"]["exact_phrase"] == recipes[row["activity_id"]]
        assert row["recipe"]["activity_version"] == 2
        assert row["planning_source_case_id"] == (
            f"{T4_SOURCE}#feat018-p2-t4-{row['activity_id'].lower()}-{row['family']}"
        )
        assert row["evidence_id"] == f"P2T5:{row['fixture_id']}"
        assert "T5-A2" in row["acceptance_ids"]
        assert not {"B1", "B2", "B3", "result", "execution_status"} & row.keys()


def test_held_and_partial_cells_preserve_separate_subprobe_expectations() -> None:
    manifest = load_manifest(MANIFEST_PATH, ROOT)
    for row in manifest["profiles"]:
        family = row["family"]
        assert row["requirement_status"] == ("OPEN" if family == "exact" else "HELD")
        if family == "adult-correction":
            assert row["expected_execution_status"] == "NOT_EXECUTED"
            assert row["held_reasons"]
            assert row["subprobes"][0]["expected_outcome"] == "NOT_EXECUTED"
            assert row["subprobes"][0]["requirement_status"] == "HELD"
        else:
            assert row["expected_execution_status"] == "EXECUTE"
            assert all(probe["requirement_status"] == "OPEN" for probe in row["subprobes"])
        if family == "conflict":
            assert {probe["kind"] for probe in row["subprobes"]} == {
                "map_asr_present", "raw_conflict_schema",
            }
        if family == "low":
            assert {probe["kind"] for probe in row["subprobes"]} == {
                "map_low_confidence", "reject_null_confidence",
            }


def test_supplemental_reference_and_characterization_do_not_replace_held_proofs() -> None:
    manifest = load_manifest(MANIFEST_PATH, ROOT)
    cases = {
        row["subprobes"][0]["kind"]: row for row in manifest["supplemental_cases"]
    }
    for kind in ("quality_valid", "quality_dark", "quality_blur", "quality_crop"):
        assert cases[kind]["family"] == "quality-reference"
        assert cases[kind]["expected_execution_status"] == "EXECUTE"
    for kind in (
        "admission_valid", "admission_corrupt", "admission_unsupported", "admission_oversized",
    ):
        assert cases[kind]["family"] == "image-admission"
        assert cases[kind]["expected_execution_status"] == "EXECUTE"
        assert cases[kind]["requirement_status"] == "OPEN"
        assert cases[kind]["subprobes"][0]["expected_outcome"] == kind.upper()
        assert "T5-A1" in cases[kind]["acceptance_ids"]
    for kind in ("rate_limit_characterization", "provider_error_characterization"):
        assert cases[kind]["requirement_status"] == "HELD"
        assert cases[kind]["subprobes"][0]["requirement_status"] == "OPEN"
        assert cases[kind]["held_reasons"]
    for kind in (
        "orientation_held", "os_error_held", "stale_session_held",
        "mobile_bundle_held", "live_run_held",
    ):
        assert cases[kind]["requirement_status"] == "HELD"
        assert cases[kind]["expected_execution_status"] == "NOT_EXECUTED"
        assert cases[kind]["subprobes"][0]["expected_outcome"] == "NOT_EXECUTED"


@pytest.mark.parametrize("mutation", [
    "wrong_contract_hash", "wrong_contract_version", "duplicate_fixture", "missing_fixture",
    "unknown_pilot", "unknown_family", "execute_adult", "credit_held", "held_coverage_spoof",
    "source_hash_drift", "source_path_escape", "unknown_probe", "wrong_expected_outcome",
    "provider_execution_spoof",
])
def test_manifest_rejects_drift_or_coverage_spoofing(tmp_path: Path, mutation: str) -> None:
    manifest = deepcopy(load_manifest(MANIFEST_PATH, ROOT))
    profiles = manifest["profiles"]
    adult = next(row for row in profiles if row["family"] == "adult-correction")
    if mutation == "wrong_contract_hash":
        manifest["contract_locks"][0]["sha256"] = "0" * 64
    elif mutation == "wrong_contract_version":
        manifest["contract_locks"][0]["version"] = "1.0"
    elif mutation == "duplicate_fixture":
        profiles[-1] = deepcopy(profiles[0])
    elif mutation == "missing_fixture":
        profiles.pop()
    elif mutation == "unknown_pilot":
        profiles[0]["activity_id"] = "ACT-9999"
    elif mutation == "unknown_family":
        profiles[0]["family"] = "live"
    elif mutation == "execute_adult":
        adult["expected_execution_status"] = "EXECUTE"
    elif mutation == "credit_held":
        adult["requirement_status"] = "SATISFIED"
    elif mutation == "held_coverage_spoof":
        adult["coverage_credit"] = True
    elif mutation == "source_hash_drift":
        manifest["source_locks"][0]["sha256"] = "0" * 64
    elif mutation == "source_path_escape":
        manifest["source_locks"][0]["path"] = "../outside-repository.py"
    elif mutation == "unknown_probe":
        profiles[0]["subprobes"][0]["kind"] = "live_model"
    elif mutation == "wrong_expected_outcome":
        profiles[0]["subprobes"][0]["expected_outcome"] = "PASS"
    elif mutation == "provider_execution_spoof":
        manifest["provider_execution"] = "EXECUTED"
    else:
        raise AssertionError(f"missing mutation: {mutation}")
    with pytest.raises(ValueError):
        load_manifest(_write_candidate(tmp_path, manifest), ROOT)


@pytest.mark.parametrize(("mutation", "expected_error"), [
    ("approved_plan_hash", "APPROVAL_IDENTITY_MISMATCH"),
    ("recipe_phrase", "PILOT_RECIPE_MISMATCH"),
    ("qualified_planning_source", "PLANNING_SOURCE_IDENTITY_MISMATCH"),
    ("valid_probe_wrong_family", "FAMILY_SUBPROBE_MISMATCH"),
    ("nonadult_held_to_open", "PRIMARY_DISPOSITION_CHANGED"),
    ("missing_supplemental", "INCOMPLETE_SUPPLEMENTALS"),
])
def test_manifest_rejects_approval_recipe_or_disposition_drift(
    tmp_path: Path, mutation: str, expected_error: str,
) -> None:
    manifest = deepcopy(load_manifest(MANIFEST_PATH, ROOT))
    exact = next(row for row in manifest["profiles"] if row["family"] == "exact")
    if mutation == "approved_plan_hash":
        manifest["approved_source_plan_sha256"] = "0" * 64
    elif mutation == "recipe_phrase":
        exact["recipe"]["exact_phrase"] = "synthetic phrase absent from the locked recipe"
    elif mutation == "qualified_planning_source":
        exact["planning_source_case_id"] = (
            f"{T4_SOURCE}#feat018-p2-t4-{exact['activity_id'].lower()}-ambiguous"
        )
    elif mutation == "valid_probe_wrong_family":
        probe = exact["subprobes"][0]
        probe["kind"] = "map_ambiguous"
        probe["probe_id"] = f"{exact['fixture_id']}:map_ambiguous"
        probe["expected_outcome"] = "MAP_AMBIGUOUS"
    elif mutation == "nonadult_held_to_open":
        ambiguous = next(row for row in manifest["profiles"] if row["family"] == "ambiguous")
        ambiguous["requirement_status"] = "OPEN"
    elif mutation == "missing_supplemental":
        manifest["supplemental_cases"].pop()
    else:
        raise AssertionError(f"missing mutation: {mutation}")
    with pytest.raises(ValueError, match=f"^{expected_error}$"):
        load_manifest(_write_candidate(tmp_path, manifest), ROOT)
