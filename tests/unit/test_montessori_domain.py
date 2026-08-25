from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.validate_montessori_domain import evaluate_case

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "activity-catalog" / "mvp" / "activities.v1.json"


def catalog_by_id() -> dict[str, dict[str, object]]:
    activities = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["activities"]
    return {activity["id"]: activity for activity in activities}


def test_standalone_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_montessori_domain.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "MONTESSORI_DOMAIN_VALID" in result.stdout
    assert "activities=100" in result.stdout


def test_material_mismatch_is_blocked() -> None:
    result = evaluate_case(
        catalog_by_id(),
        {
            "age_months": 48,
            "readiness_tags": ["follows_one_step_direction"],
            "completed_activity_ids": [],
            "available_material_ids": [],
            "supervision_level": "NEARBY",
            "policy_flags": [],
            "candidate_activity_ids": ["ACT-0026"],
        },
    )
    assert result == {
        "status": "NO_VALID_ACTIVITY",
        "allowed_activity_ids": [],
        "blocked": {"ACT-0026": ["BLOCK_MISSING_MATERIAL"]},
    }


def test_zero_to_three_requires_caregiver_and_direct_supervision() -> None:
    activity = catalog_by_id()["ACT-0001"]
    materials = [group["any_of"][0] for group in activity["material_groups"]]
    result = evaluate_case(
        {"ACT-0001": activity},
        {
            "age_months": 12,
            "readiness_tags": ["caregiver_present"],
            "completed_activity_ids": [],
            "available_material_ids": materials,
            "supervision_level": "NONE",
            "policy_flags": [],
            "candidate_activity_ids": ["ACT-0001"],
        },
    )
    assert result["blocked"]["ACT-0001"] == [
        "BLOCK_INSUFFICIENT_SUPERVISION",
        "BLOCK_POLICY_CONSTRAINT",
    ]


def test_catalog_never_claims_owner_or_production_review() -> None:
    activities = catalog_by_id().values()
    assert all(
        activity["review"]["status"] == "PENDING_OWNER_REVIEW"
        for activity in activities
    )
    assert all(
        activity["review"]["production_eligible"] is False for activity in activities
    )
