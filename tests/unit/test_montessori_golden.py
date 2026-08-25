from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from tools.validate_montessori_golden import (
    DEFAULT_BASE_DIR,
    GOLDEN_DIR,
    evaluate_case,
    sha256_file,
    validate_catalog,
)

ROOT = Path(__file__).resolve().parents[2]


def test_golden_standalone_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_montessori_golden.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "MONTESSORI_GOLDEN_VALID" in result.stdout
    assert "activities=20" in result.stdout
    assert "fixtures=74" in result.stdout


def test_frozen_baseline_hashes_match() -> None:
    selection = json.loads(
        (GOLDEN_DIR / "selection-manifest.v1.json").read_text(encoding="utf-8")
    )
    for filename, expected in selection["base_file_hashes"].items():
        assert sha256_file(DEFAULT_BASE_DIR / filename) == expected


def test_primary_and_substitute_paths_are_valid() -> None:
    records, material_doc = validate_catalog(DEFAULT_BASE_DIR)
    activity = records["ACT-0004"]
    common = {
        "age_months": 12,
        "readiness_ids": ["READY_SEARCH_PARTLY_HIDDEN"],
        "completed_activity_ids": [],
        "supervision_level": "DIRECT",
        "policy_flags": ["CAREGIVER_PRESENT"],
        "candidate_status": "ACTIVE_FIXTURE",
    }
    for option in ("GMAT-0004-PRIMARY", "GMAT-0004-SUBSTITUTE"):
        result = evaluate_case(
            activity,
            material_doc,
            {**common, "available_material_option_ids": [option]},
        )
        assert result["status"] == "VALID_CANDIDATE"


def test_multiple_hard_failures_are_all_preserved() -> None:
    records, material_doc = validate_catalog(DEFAULT_BASE_DIR)
    activity = records["ACT-0004"]
    result = evaluate_case(
        activity,
        material_doc,
        {
            "age_months": 12,
            "readiness_ids": [],
            "completed_activity_ids": [],
            "available_material_option_ids": [],
            "supervision_level": "NONE",
            "policy_flags": [],
            "candidate_status": "ACTIVE_FIXTURE",
        },
    )
    assert result["blocked"]["ACT-0004"] == [
        "BLOCK_MISSING_READINESS",
        "BLOCK_INSUFFICIENT_SUPERVISION",
        "BLOCK_POLICY_CONSTRAINT",
        "BLOCK_MISSING_MATERIAL",
    ]


def test_golden_records_retain_provisional_nonproduction_guard() -> None:
    records, material_doc = validate_catalog(DEFAULT_BASE_DIR)
    assert all(
        record["review"]["status"] == "PROVISIONAL_OWNER_REVIEWED"
        and record["review"]["reviewer_role"] == "PROJECT_OWNER"
        and record["review"]["reviewed_at"]
        and record["review"]["production_eligible"] is False
        for record in records.values()
    )
    assert all(
        option["review_status"] == "PROVISIONAL_OWNER_REVIEWED"
        and option["production_eligible"] is False
        for option in material_doc["options"]
    )


def test_mutated_fixture_is_rejected_by_checksum(tmp_path: Path) -> None:
    fixture_root = tmp_path / "montessori-golden"
    shutil.copytree(ROOT / "tests" / "fixtures" / "montessori-golden", fixture_root)
    case_path = fixture_root / "cases" / "gcase_0004_primary_valid.json"
    case = json.loads(case_path.read_text(encoding="utf-8"))
    case["expected"]["allowed_activity_ids"] = []
    case_path.write_text(
        json.dumps(case, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_montessori_golden.py"),
            "--fixture-root",
            str(fixture_root),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "golden fixture checksum mismatch: GCASE_0004_PRIMARY_VALID" in result.stdout


def test_mutated_parent_baseline_is_rejected(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "mvp"
    shutil.copytree(DEFAULT_BASE_DIR, baseline_dir)
    activities_path = baseline_dir / "activities.v1.json"
    activities = json.loads(activities_path.read_text(encoding="utf-8"))
    activities["mutation_probe"] = True
    activities_path.write_text(
        json.dumps(activities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_montessori_golden.py"),
            "--baseline-dir",
            str(baseline_dir),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "baseline hash mismatch: activities.v1.json" in result.stdout
