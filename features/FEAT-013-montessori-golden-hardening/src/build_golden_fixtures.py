from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_DIR = ROOT / "data" / "activity-catalog" / "golden" / "v1"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "montessori-golden"
SCHEMA_DIR = ROOT / "packages" / "domain-montessori" / "schemas"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def material_ids(activity_id: str, kind: str) -> list[str]:
    numeric = activity_id.removeprefix("ACT-")
    return [f"GMAT-{numeric}-{kind}"]


def valid_input(
    activity: dict[str, Any], material_kind: str, age: int | None = None
) -> dict[str, Any]:
    return {
        "age_months": age
        if age is not None
        else (activity["age_months"]["min"] + activity["age_months"]["max"]) // 2,
        "readiness_ids": [item["id"] for item in activity["readiness_criteria"]],
        "completed_activity_ids": activity["prerequisite_activity_ids"],
        "available_material_option_ids": material_ids(activity["id"], material_kind),
        "supervision_level": activity["safety"]["minimum_supervision"],
        "policy_flags": activity["policy_constraints"],
        "candidate_status": "ACTIVE_FIXTURE",
    }


def valid_expected(activity_id: str) -> dict[str, Any]:
    return {
        "status": "VALID_CANDIDATE",
        "allowed_activity_ids": [activity_id],
        "blocked": {},
    }


def blocked_expected(activity_id: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "status": "NO_VALID_ACTIVITY",
        "allowed_activity_ids": [],
        "blocked": {activity_id: reasons},
    }


def make_case(
    case_id: str,
    description: str,
    activity_id: str,
    case_input: dict[str, Any],
    expected: dict[str, Any],
    tags: list[str],
) -> dict[str, Any]:
    return {
        "id": case_id,
        "description": description,
        "activity_ref": {"id": activity_id, "version": 2},
        "input": case_input,
        "expected": expected,
        "coverage_tags": tags,
    }


def build_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://sketch2life.local/schemas/montessori/golden-fixture-case.v1.schema.json",
        "title": "Golden Montessori deterministic fixture case v1",
        "type": "object",
        "required": [
            "id",
            "description",
            "activity_ref",
            "input",
            "expected",
            "coverage_tags",
        ],
        "properties": {
            "id": {"type": "string", "pattern": "^GCASE_[A-Z0-9_]+$"},
            "description": {"type": "string", "minLength": 1},
            "activity_ref": {
                "type": "object",
                "required": ["id", "version"],
                "additionalProperties": False,
            },
            "input": {
                "type": "object",
                "required": [
                    "age_months",
                    "readiness_ids",
                    "completed_activity_ids",
                    "available_material_option_ids",
                    "supervision_level",
                    "policy_flags",
                    "candidate_status",
                ],
                "additionalProperties": False,
            },
            "expected": {
                "type": "object",
                "required": ["status", "allowed_activity_ids", "blocked"],
                "additionalProperties": False,
            },
            "coverage_tags": {"type": "array", "minItems": 1, "uniqueItems": True},
        },
        "additionalProperties": False,
    }


def main() -> None:
    activities = read_json(GOLDEN_DIR / "activities.v2.json")["activities"]
    cases: list[dict[str, Any]] = []
    for activity in activities:
        activity_id = activity["id"]
        numeric = activity_id.removeprefix("ACT-")
        band_tag = activity["age_band"]
        cases.append(
            make_case(
                f"GCASE_{numeric}_PRIMARY_VALID",
                f"{activity_id} accepts its concrete primary material",
                activity_id,
                valid_input(activity, "PRIMARY"),
                valid_expected(activity_id),
                ["valid", "primary_material", band_tag, activity_id],
            )
        )
        cases.append(
            make_case(
                f"GCASE_{numeric}_SUBSTITUTE_VALID",
                f"{activity_id} accepts its concrete household substitute",
                activity_id,
                valid_input(activity, "SUBSTITUTE"),
                valid_expected(activity_id),
                ["valid", "household_substitute", band_tag, activity_id],
            )
        )
        blocked_input = valid_input(activity, "PRIMARY")
        blocked_input["readiness_ids"] = []
        cases.append(
            make_case(
                f"GCASE_{numeric}_READINESS_BLOCK",
                f"{activity_id} blocks when observable readiness is absent",
                activity_id,
                blocked_input,
                blocked_expected(activity_id, ["BLOCK_MISSING_READINESS"]),
                ["blocked", "readiness", band_tag, activity_id],
            )
        )

    representatives: dict[str, dict[str, Any]] = {}
    for activity in activities:
        representatives.setdefault(activity["age_band"], activity)
    for band, activity in representatives.items():
        activity_id = activity["id"]
        numeric = activity_id.removeprefix("ACT-")
        below = valid_input(activity, "PRIMARY", activity["age_months"]["min"] - 1)
        cases.append(
            make_case(
                f"GCASE_{numeric}_AGE_BELOW_BLOCK",
                f"{activity_id} blocks below its hardened age guidance",
                activity_id,
                below,
                blocked_expected(activity_id, ["BLOCK_AGE_BELOW_MIN"]),
                ["blocked", "age", "age_below", band],
            )
        )
        for boundary_name, age in (
            ("MIN_BOUNDARY", activity["age_months"]["min"]),
            ("MAX_BOUNDARY", activity["age_months"]["max"]),
        ):
            cases.append(
                make_case(
                    f"GCASE_{numeric}_{boundary_name}_VALID",
                    f"{activity_id} accepts inclusive {boundary_name.lower()}",
                    activity_id,
                    valid_input(activity, "PRIMARY", age),
                    valid_expected(activity_id),
                    ["valid", "age_boundary", band],
                )
            )

    first = activities[0]
    multiple_input = valid_input(first, "PRIMARY")
    multiple_input.update(
        {
            "readiness_ids": [],
            "available_material_option_ids": [],
            "supervision_level": "NONE",
            "policy_flags": [],
        }
    )
    cases.append(
        make_case(
            "GCASE_MULTIPLE_FAILURE_BLOCK",
            "A golden candidate reports all applicable independent hard failures",
            first["id"],
            multiple_input,
            blocked_expected(
                first["id"],
                [
                    "BLOCK_MISSING_READINESS",
                    "BLOCK_INSUFFICIENT_SUPERVISION",
                    "BLOCK_POLICY_CONSTRAINT",
                    "BLOCK_MISSING_MATERIAL",
                ],
            ),
            ["blocked", "multiple_failure", "no_valid"],
        )
    )
    inactive_input = valid_input(activities[5], "PRIMARY")
    inactive_input["candidate_status"] = "INACTIVE"
    cases.append(
        make_case(
            "GCASE_INACTIVE_BLOCK",
            "An inactive golden candidate remains blocked",
            activities[5]["id"],
            inactive_input,
            blocked_expected(activities[5]["id"], ["BLOCK_INACTIVE"]),
            ["blocked", "inactive", "no_valid"],
        )
    )

    case_dir = FIXTURE_DIR / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    manifest_entries: list[dict[str, Any]] = []
    for case in cases:
        filename = f"{case['id'].lower()}.json"
        path = case_dir / filename
        write_json(path, case)
        manifest_entries.append(
            {
                "id": case["id"],
                "path": f"cases/{filename}",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "coverage_tags": case["coverage_tags"],
            }
        )
    manifest = {
        "schema_version": 1,
        "case_count": len(cases),
        "cases": manifest_entries,
    }
    write_json(FIXTURE_DIR / "manifest.v1.json", manifest)
    write_json(SCHEMA_DIR / "golden-fixture-case.v1.schema.json", build_schema())

    positive = sum(bool(case["expected"]["allowed_activity_ids"]) for case in cases)
    print("GOLDEN_FIXTURES_BUILT")
    print(f"cases={len(cases)}")
    print(f"positive={positive}")
    print(f"blocked={len(cases) - positive}")


if __name__ == "__main__":
    main()
