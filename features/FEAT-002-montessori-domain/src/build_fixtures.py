from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = ROOT / "data" / "activity-catalog" / "mvp" / "activities.v1.json"
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "montessori"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["activities"]
    by_id = {activity["id"]: activity for activity in catalog}

    inactive = dict(by_id["ACT-0026"])
    inactive.update(
        {
            "id": "ACT-9001",
            "slug": "inactive_test_sentinel",
            "title": {"vi-VN": "Bản ghi kiểm thử trạng thái không hoạt động"},
            "catalog_status": "INACTIVE",
            "source_refs": ["sprint-task-breakdown"],
            "provenance": {
                "authored_by": "FEAT-002",
                "authored_at": "2026-08-25",
                "source_type": "inactive_test_sentinel",
            },
        }
    )
    write_json(FIXTURE_ROOT / "catalog" / "inactive-activity.v1.json", inactive)
    by_id[inactive["id"]] = inactive

    def material_ids(activity_id: str, *, substitutes: bool = False) -> list[str]:
        index = 1 if substitutes else 0
        return [
            group["any_of"][index] for group in by_id[activity_id]["material_groups"]
        ]

    def input_for(
        activity_ids: list[str],
        *,
        age_months: int,
        readiness_tags: list[str],
        completed: list[str] | None = None,
        materials: list[str] | None = None,
        supervision: str = "NEARBY",
        policies: list[str] | None = None,
    ) -> dict[str, Any]:
        default_materials = sorted(
            {
                value
                for activity_id in activity_ids
                for value in material_ids(activity_id)
            }
        )
        return {
            "age_months": age_months,
            "readiness_tags": readiness_tags,
            "completed_activity_ids": completed or [],
            "available_material_ids": default_materials
            if materials is None
            else materials,
            "supervision_level": supervision,
            "policy_flags": policies or [],
            "candidate_activity_ids": activity_ids,
        }

    def case(
        case_id: str,
        description: str,
        input_value: dict[str, Any],
        allowed: list[str],
        blocked: dict[str, list[str]],
        tags: list[str],
    ) -> dict[str, Any]:
        return {
            "id": case_id,
            "description": description,
            "input": input_value,
            "expected": {
                "status": "VALID_CANDIDATES" if allowed else "NO_VALID_ACTIVITY",
                "allowed_activity_ids": allowed,
                "blocked": blocked,
            },
            "coverage_tags": tags,
        }

    cases = [
        case(
            "CASE_VALID_0_3",
            "Valid caregiver-led 0-3 candidate",
            input_for(
                ["ACT-0001"],
                age_months=12,
                readiness_tags=["caregiver_present"],
                supervision="DIRECT",
                policies=["CAREGIVER_PRESENT"],
            ),
            ["ACT-0001"],
            {},
            ["valid", "0-3"],
        ),
        case(
            "CASE_VALID_3_6",
            "Valid 3-6 practical-life candidate",
            input_for(
                ["ACT-0026"],
                age_months=48,
                readiness_tags=["follows_one_step_direction"],
            ),
            ["ACT-0026"],
            {},
            ["valid", "3-6"],
        ),
        case(
            "CASE_VALID_6_9",
            "Valid 6-9 cosmic candidate",
            input_for(
                ["ACT-0051"],
                age_months=84,
                readiness_tags=["reads_simple_instructions"],
            ),
            ["ACT-0051"],
            {},
            ["valid", "6-9"],
        ),
        case(
            "CASE_VALID_9_12",
            "Valid 9-12 mathematics candidate",
            input_for(
                ["ACT-0076"],
                age_months=120,
                readiness_tags=["works_with_multi_step_plan"],
            ),
            ["ACT-0076"],
            {},
            ["valid", "9-12"],
        ),
        case(
            "CASE_VALID_SUBSTITUTES",
            "Approved substitute IDs satisfy material groups",
            input_for(
                ["ACT-0026"],
                age_months=48,
                readiness_tags=["follows_one_step_direction"],
                materials=material_ids("ACT-0026", substitutes=True),
            ),
            ["ACT-0026"],
            {},
            ["valid", "material_substitute"],
        ),
        case(
            "CASE_MULTIPLE_VALID",
            "Multiple same-band candidates remain valid",
            input_for(
                ["ACT-0026", "ACT-0036"],
                age_months=48,
                readiness_tags=["follows_one_step_direction"],
            ),
            ["ACT-0026", "ACT-0036"],
            {},
            ["valid", "multiple_valid"],
        ),
        case(
            "CASE_VALID_PREREQ_0_3",
            "Completed prerequisite permits 0-3 candidate",
            input_for(
                ["ACT-0005"],
                age_months=24,
                readiness_tags=["caregiver_present"],
                completed=["ACT-0004"],
                supervision="DIRECT",
                policies=["CAREGIVER_PRESENT"],
            ),
            ["ACT-0005"],
            {},
            ["valid", "prerequisite", "0-3"],
        ),
        case(
            "CASE_VALID_PREREQ_3_6",
            "Completed prerequisite permits golden-bead activity",
            input_for(
                ["ACT-0050"],
                age_months=60,
                readiness_tags=["follows_one_step_direction"],
                completed=["ACT-0047"],
            ),
            ["ACT-0050"],
            {},
            ["valid", "prerequisite", "3-6"],
        ),
        case(
            "CASE_VALID_PREREQ_6_9",
            "Completed prerequisite permits division material",
            input_for(
                ["ACT-0062"],
                age_months=96,
                readiness_tags=["reads_simple_instructions"],
                completed=["ACT-0061"],
            ),
            ["ACT-0062"],
            {},
            ["valid", "prerequisite", "6-9"],
        ),
        case(
            "CASE_VALID_PREREQ_9_12",
            "Completed prerequisite permits Pythagorean exploration",
            input_for(
                ["ACT-0083"],
                age_months=132,
                readiness_tags=["works_with_multi_step_plan"],
                completed=["ACT-0082"],
            ),
            ["ACT-0083"],
            {},
            ["valid", "prerequisite", "9-12"],
        ),
        case(
            "CASE_VALID_MIN_BOUNDARY",
            "Minimum age is inclusive",
            input_for(
                ["ACT-0026"],
                age_months=36,
                readiness_tags=["follows_one_step_direction"],
            ),
            ["ACT-0026"],
            {},
            ["valid", "age_boundary"],
        ),
        case(
            "CASE_VALID_MAX_BOUNDARY",
            "Maximum age is inclusive",
            input_for(
                ["ACT-0026"],
                age_months=71,
                readiness_tags=["follows_one_step_direction"],
            ),
            ["ACT-0026"],
            {},
            ["valid", "age_boundary"],
        ),
        case(
            "CASE_BLOCK_AGE_BELOW",
            "Candidate blocks below minimum age",
            input_for(
                ["ACT-0026"],
                age_months=35,
                readiness_tags=["follows_one_step_direction"],
            ),
            [],
            {"ACT-0026": ["BLOCK_AGE_BELOW_MINIMUM"]},
            ["blocked", "age"],
        ),
        case(
            "CASE_BLOCK_AGE_ABOVE",
            "Candidate blocks above maximum age",
            input_for(
                ["ACT-0001"],
                age_months=36,
                readiness_tags=["caregiver_present"],
                supervision="DIRECT",
                policies=["CAREGIVER_PRESENT"],
            ),
            [],
            {"ACT-0001": ["BLOCK_AGE_ABOVE_MAXIMUM"]},
            ["blocked", "age"],
        ),
        case(
            "CASE_BLOCK_READINESS",
            "Candidate blocks missing readiness",
            input_for(["ACT-0026"], age_months=48, readiness_tags=[]),
            [],
            {"ACT-0026": ["BLOCK_MISSING_READINESS"]},
            ["blocked", "readiness"],
        ),
        case(
            "CASE_BLOCK_PREREQUISITE",
            "Candidate blocks missing prerequisite",
            input_for(
                ["ACT-0050"],
                age_months=60,
                readiness_tags=["follows_one_step_direction"],
            ),
            [],
            {"ACT-0050": ["BLOCK_MISSING_PREREQUISITE"]},
            ["blocked", "prerequisite"],
        ),
        case(
            "CASE_BLOCK_SUPERVISION",
            "0-3 candidate blocks without direct supervision",
            input_for(
                ["ACT-0001"],
                age_months=12,
                readiness_tags=["caregiver_present"],
                supervision="NEARBY",
                policies=["CAREGIVER_PRESENT"],
            ),
            [],
            {"ACT-0001": ["BLOCK_INSUFFICIENT_SUPERVISION"]},
            ["blocked", "safety"],
        ),
        case(
            "CASE_BLOCK_POLICY",
            "0-3 candidate blocks without caregiver policy",
            input_for(
                ["ACT-0001"],
                age_months=12,
                readiness_tags=["caregiver_present"],
                supervision="DIRECT",
                policies=[],
            ),
            [],
            {"ACT-0001": ["BLOCK_POLICY_CONSTRAINT"]},
            ["blocked", "policy"],
        ),
        case(
            "CASE_BLOCK_MATERIAL",
            "Candidate blocks when required materials are absent",
            input_for(
                ["ACT-0026"],
                age_months=48,
                readiness_tags=["follows_one_step_direction"],
                materials=[],
            ),
            [],
            {"ACT-0026": ["BLOCK_MISSING_MATERIAL"]},
            ["blocked", "material"],
        ),
        case(
            "CASE_BLOCK_INACTIVE",
            "Inactive supplemental catalog record blocks",
            input_for(
                ["ACT-9001"],
                age_months=48,
                readiness_tags=["follows_one_step_direction"],
            ),
            [],
            {"ACT-9001": ["BLOCK_INACTIVE_ACTIVITY"]},
            ["blocked", "inactive"],
        ),
        case(
            "CASE_BLOCK_MULTIPLE_REASONS",
            "All applicable block reasons remain visible",
            input_for(
                ["ACT-0001"],
                age_months=48,
                readiness_tags=[],
                materials=[],
                supervision="NONE",
                policies=[],
            ),
            [],
            {
                "ACT-0001": [
                    "BLOCK_AGE_ABOVE_MAXIMUM",
                    "BLOCK_MISSING_READINESS",
                    "BLOCK_INSUFFICIENT_SUPERVISION",
                    "BLOCK_POLICY_CONSTRAINT",
                    "BLOCK_MISSING_MATERIAL",
                ]
            },
            ["blocked", "multiple_failure"],
        ),
        case(
            "CASE_NO_VALID_MIXED_AGE",
            "Mixed-band candidates can produce no valid result",
            input_for(
                ["ACT-0001", "ACT-0051"],
                age_months=48,
                readiness_tags=[],
                materials=[],
                supervision="NONE",
                policies=[],
            ),
            [],
            {
                "ACT-0001": [
                    "BLOCK_AGE_ABOVE_MAXIMUM",
                    "BLOCK_MISSING_READINESS",
                    "BLOCK_INSUFFICIENT_SUPERVISION",
                    "BLOCK_POLICY_CONSTRAINT",
                    "BLOCK_MISSING_MATERIAL",
                ],
                "ACT-0051": [
                    "BLOCK_AGE_BELOW_MINIMUM",
                    "BLOCK_MISSING_READINESS",
                    "BLOCK_INSUFFICIENT_SUPERVISION",
                    "BLOCK_MISSING_MATERIAL",
                ],
            },
            ["blocked", "no_valid"],
        ),
        case(
            "CASE_NO_VALID_MATERIALS",
            "Multiple otherwise-valid candidates block on materials",
            input_for(
                ["ACT-0026", "ACT-0036"],
                age_months=48,
                readiness_tags=["follows_one_step_direction"],
                materials=[],
            ),
            [],
            {
                "ACT-0026": ["BLOCK_MISSING_MATERIAL"],
                "ACT-0036": ["BLOCK_MISSING_MATERIAL"],
            },
            ["blocked", "material", "no_valid"],
        ),
        case(
            "CASE_NO_VALID_CAREGIVER_GATES",
            "0-3 candidate requires both direct supervision and caregiver policy",
            input_for(
                ["ACT-0001"],
                age_months=12,
                readiness_tags=["caregiver_present"],
                supervision="NONE",
                policies=[],
            ),
            [],
            {"ACT-0001": ["BLOCK_INSUFFICIENT_SUPERVISION", "BLOCK_POLICY_CONSTRAINT"]},
            ["blocked", "safety", "policy", "no_valid"],
        ),
    ]

    case_dir = FIXTURE_ROOT / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for old in case_dir.glob("*.json"):
        old.unlink()
    for fixture in cases:
        write_json(case_dir / f"{fixture['id'].lower()}.json", fixture)

    manifest_entries = []
    for path in sorted(case_dir.glob("*.json")):
        content = path.read_bytes()
        fixture = json.loads(content)
        manifest_entries.append(
            {
                "id": fixture["id"],
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(content).hexdigest(),
                "coverage_tags": fixture["coverage_tags"],
            }
        )
    manifest = {
        "schema_version": 1,
        "generated_at": "2026-08-25",
        "case_count": len(cases),
        "cases": manifest_entries,
    }
    write_json(FIXTURE_ROOT / "manifest.v1.json", manifest)
    print("FIXTURES_BUILT")
    print(f"cases={len(cases)}")
    print(
        f"positive={sum(bool(value['expected']['allowed_activity_ids']) for value in cases)}"
    )
    print(
        f"negative={sum(not value['expected']['allowed_activity_ids'] for value in cases)}"
    )


if __name__ == "__main__":
    build()
