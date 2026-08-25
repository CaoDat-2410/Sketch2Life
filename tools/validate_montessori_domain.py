from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "data" / "activity-catalog" / "mvp"
DOMAIN_DIR = ROOT / "packages" / "domain-montessori"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "montessori"

ACTIVITY_ID = re.compile(r"^ACT-[0-9]{4}$")
OBJECTIVE_ID = re.compile(r"^OBJ_[A-Z0-9_]+$")
AGE_BANDS = {"0-3": (0, 35), "3-6": (36, 71), "6-9": (72, 107), "9-12": (108, 155)}
SUPERVISION = {"NONE": 0, "NEARBY": 1, "DIRECT": 2}
REQUIRED_COVERAGE = {
    "valid",
    "0-3",
    "3-6",
    "6-9",
    "9-12",
    "multiple_valid",
    "age_boundary",
    "age",
    "readiness",
    "prerequisite",
    "safety",
    "policy",
    "material",
    "inactive",
    "multiple_failure",
    "no_valid",
    "material_substitute",
}


def fail(message: str) -> None:
    raise SystemExit(f"MONTESSORI_DOMAIN_INVALID: {message}")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read valid JSON from {path.relative_to(ROOT).as_posix()}: {exc}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def legacy_fixture_manifest_sha256(path: Path) -> str:
    """Match v1 manifest hashes without depending on checkout line endings."""
    normalized_lf = (
        path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    )
    legacy_crlf = normalized_lf.replace("\n", "\r\n").encode("utf-8")
    return hashlib.sha256(legacy_crlf).hexdigest()


def validate_contract_files() -> None:
    required = [
        DOMAIN_DIR / "spec" / "GLOSSARY.md",
        DOMAIN_DIR / "spec" / "ID_VERSION_RULES.md",
        DOMAIN_DIR / "spec" / "RULE_SEMANTICS.md",
        DOMAIN_DIR / "spec" / "GATE_B_ACCEPTANCE.md",
        DOMAIN_DIR / "spec" / "ACTIVITY_HANDOFF.md",
        DOMAIN_DIR / "schemas" / "activity.v1.schema.json",
        DOMAIN_DIR / "schemas" / "learning-objective.v1.schema.json",
        DOMAIN_DIR / "schemas" / "fixture-case.v1.schema.json",
        DOMAIN_DIR / "schemas" / "activity-handoff.v1.schema.json",
    ]
    missing = [
        path.relative_to(ROOT).as_posix() for path in required if not path.is_file()
    ]
    require(not missing, f"missing contract files: {missing}")
    for path in required:
        if path.suffix == ".json":
            schema = read_json(path)
            require(
                schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
                f"schema declaration missing in {path.name}",
            )
            require(
                schema.get("type") == "object",
                f"top-level schema type must be object in {path.name}",
            )


def validate_catalog() -> tuple[dict[str, dict[str, Any]], set[str], dict[str, int]]:
    catalog = read_json(CATALOG_DIR / "activities.v1.json")
    objective_doc = read_json(CATALOG_DIR / "learning-objectives.v1.json")
    provenance = read_json(CATALOG_DIR / "provenance.v1.json")
    hard_rules = read_json(CATALOG_DIR / "hard-rules.v1.json")
    activities = catalog.get("activities", [])
    objectives = objective_doc.get("objectives", [])

    require(
        catalog.get("schema_version") == 1, "activity catalog schema version must be 1"
    )
    require(
        len(activities) == 100,
        f"expected exactly 100 baseline activities, found {len(activities)}",
    )
    require(
        len(objectives) == 20,
        f"expected exactly 20 objectives, found {len(objectives)}",
    )

    objective_ids: set[str] = set()
    for objective in objectives:
        objective_id = objective.get("id", "")
        require(
            bool(OBJECTIVE_ID.fullmatch(objective_id)),
            f"invalid objective ID: {objective_id}",
        )
        require(
            objective_id not in objective_ids, f"duplicate objective ID: {objective_id}"
        )
        require(
            objective.get("version") == 1,
            f"objective version must be 1: {objective_id}",
        )
        require(
            bool(objective.get("title", {}).get("vi-VN")),
            f"missing vi-VN objective title: {objective_id}",
        )
        require(
            objective.get("status") == "PROVISIONAL_OWNER_REVIEWED",
            f"objective must retain provisional owner review: {objective_id}",
        )
        require(
            objective.get("reviewer_role") == "PROJECT_OWNER"
            and bool(objective.get("reviewed_at")),
            f"objective owner-review provenance missing: {objective_id}",
        )
        require(
            objective.get("production_eligible") is False,
            f"objective cannot be production eligible: {objective_id}",
        )
        objective_ids.add(objective_id)

    source_ids = set(provenance.get("source_register_ids", []))
    require(source_ids, "provenance source register IDs are empty")
    review_policy = provenance.get("review_policy", {})
    require(
        review_policy.get("current_status") == "PROVISIONAL_OWNER_REVIEWED",
        "provenance must record provisional owner review",
    )
    require(
        review_policy.get("reviewed_activity_count") == 100
        and review_policy.get("reviewed_objective_count") == 20
        and bool(review_policy.get("owner_reviewed_at")),
        "provenance owner-review scope is incomplete",
    )
    by_id: dict[str, dict[str, Any]] = {}
    band_counts: Counter[str] = Counter()
    slugs: set[str] = set()
    for activity in activities:
        activity_id = activity.get("id", "")
        require(
            bool(ACTIVITY_ID.fullmatch(activity_id)),
            f"invalid activity ID: {activity_id}",
        )
        require(activity_id not in by_id, f"duplicate activity ID: {activity_id}")
        slug = activity.get("slug", "")
        require(
            bool(re.fullmatch(r"[a-z0-9_]+", slug)), f"invalid slug for {activity_id}"
        )
        require(slug not in slugs, f"duplicate activity slug: {slug}")
        slugs.add(slug)
        require(
            activity.get("version") == 1, f"activity version must be 1: {activity_id}"
        )
        require(
            bool(activity.get("title", {}).get("vi-VN")),
            f"missing vi-VN title: {activity_id}",
        )
        band = activity.get("age_band")
        require(band in AGE_BANDS, f"invalid age band for {activity_id}: {band}")
        require(
            (
                activity.get("age_months", {}).get("min"),
                activity.get("age_months", {}).get("max"),
            )
            == AGE_BANDS[band],
            f"age range does not match band for {activity_id}",
        )
        band_counts[band] += 1
        refs = activity.get("objective_ids", [])
        require(
            bool(refs) and set(refs) <= objective_ids,
            f"broken objective reference in {activity_id}",
        )
        require(
            len(activity.get("steps_vi", [])) >= 3,
            f"insufficient steps for {activity_id}",
        )
        require(
            activity.get("catalog_status") == "ACTIVE_FIXTURE",
            f"baseline activity must be ACTIVE_FIXTURE: {activity_id}",
        )
        review = activity.get("review", {})
        require(
            review.get("status") == "PROVISIONAL_OWNER_REVIEWED",
            f"activity must retain provisional owner review: {activity_id}",
        )
        require(
            review.get("reviewer_role") == "PROJECT_OWNER"
            and bool(review.get("reviewed_at")),
            f"activity owner-review provenance missing: {activity_id}",
        )
        require(
            review.get("production_eligible") is False,
            f"activity cannot be production eligible: {activity_id}",
        )
        require(
            bool(activity.get("source_refs"))
            and set(activity["source_refs"]) <= source_ids,
            f"invalid source refs in {activity_id}",
        )
        require(
            bool(activity.get("readiness_tags")),
            f"readiness tags missing in {activity_id}",
        )
        material_groups = activity.get("material_groups", [])
        require(bool(material_groups), f"material groups missing in {activity_id}")
        for group in material_groups:
            require(
                group.get("required") is True,
                f"baseline material group must be required in {activity_id}",
            )
            require(
                len(group.get("any_of", [])) >= 2,
                f"primary and approved substitute IDs required in {activity_id}",
            )
            require(
                bool(group.get("home_substitute_vi")),
                f"substitute guidance missing in {activity_id}",
            )
        safety = activity.get("safety", {})
        require(
            safety.get("minimum_supervision") in SUPERVISION,
            f"invalid supervision in {activity_id}",
        )
        require(
            bool(safety.get("hazards_vi")) and bool(safety.get("stop_conditions_vi")),
            f"safety fields missing in {activity_id}",
        )
        if band == "0-3":
            require(
                safety["minimum_supervision"] == "DIRECT",
                f"0-3 activity requires DIRECT supervision: {activity_id}",
            )
            require(
                "CAREGIVER_PRESENT" in activity.get("policy_constraints", []),
                f"0-3 caregiver policy missing: {activity_id}",
            )
        by_id[activity_id] = activity

    require(
        dict(band_counts) == {band: 25 for band in AGE_BANDS},
        f"age-band counts must be 25 each: {dict(band_counts)}",
    )
    for activity_id, activity in by_id.items():
        prereqs = activity.get("prerequisite_activity_ids", [])
        require(activity_id not in prereqs, f"self prerequisite in {activity_id}")
        require(
            set(prereqs) <= set(by_id),
            f"broken prerequisite reference in {activity_id}",
        )

    rules = hard_rules.get("rules", [])
    require(len(rules) == 8, f"expected 8 hard rules, found {len(rules)}")
    require(len({rule["id"] for rule in rules}) == len(rules), "duplicate hard-rule ID")
    require(
        len({rule["reason_code"] for rule in rules}) == len(rules),
        "duplicate hard-rule reason code",
    )
    require(
        [rule["priority"] for rule in rules]
        == sorted(rule["priority"] for rule in rules),
        "hard-rule priorities must be ordered",
    )
    require(
        hard_rules.get("no_result_status") == "NO_VALID_ACTIVITY",
        "no-result policy missing",
    )
    return by_id, objective_ids, dict(band_counts)


def reasons_for(activity: dict[str, Any], case_input: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if activity["catalog_status"] != "ACTIVE_FIXTURE":
        reasons.append("BLOCK_INACTIVE_ACTIVITY")
    age = case_input["age_months"]
    if age < activity["age_months"]["min"]:
        reasons.append("BLOCK_AGE_BELOW_MINIMUM")
    if age > activity["age_months"]["max"]:
        reasons.append("BLOCK_AGE_ABOVE_MAXIMUM")
    if not set(activity["readiness_tags"]) <= set(case_input["readiness_tags"]):
        reasons.append("BLOCK_MISSING_READINESS")
    if not set(activity["prerequisite_activity_ids"]) <= set(
        case_input["completed_activity_ids"]
    ):
        reasons.append("BLOCK_MISSING_PREREQUISITE")
    required_supervision = activity["safety"]["minimum_supervision"]
    if SUPERVISION[case_input["supervision_level"]] < SUPERVISION[required_supervision]:
        reasons.append("BLOCK_INSUFFICIENT_SUPERVISION")
    if not set(activity["policy_constraints"]) <= set(case_input["policy_flags"]):
        reasons.append("BLOCK_POLICY_CONSTRAINT")
    available = set(case_input["available_material_ids"])
    if any(
        group["required"] and not (set(group["any_of"]) & available)
        for group in activity["material_groups"]
    ):
        reasons.append("BLOCK_MISSING_MATERIAL")
    return reasons


def evaluate_case(
    activities: dict[str, dict[str, Any]], case_input: dict[str, Any]
) -> dict[str, Any]:
    allowed: list[str] = []
    blocked: dict[str, list[str]] = {}
    for activity_id in sorted(case_input["candidate_activity_ids"]):
        require(activity_id in activities, f"unknown fixture candidate: {activity_id}")
        reasons = reasons_for(activities[activity_id], case_input)
        if reasons:
            blocked[activity_id] = reasons
        else:
            allowed.append(activity_id)
    return {
        "status": "VALID_CANDIDATES" if allowed else "NO_VALID_ACTIVITY",
        "allowed_activity_ids": allowed,
        "blocked": blocked,
    }


def validate_fixtures(
    activities: dict[str, dict[str, Any]], fixture_dir: Path = FIXTURE_DIR
) -> tuple[int, int, int, list[str]]:
    supplemental = fixture_dir / "catalog" / "inactive-activity.v1.json"
    inactive = read_json(supplemental)
    require(
        inactive.get("catalog_status") == "INACTIVE",
        "inactive sentinel must be INACTIVE",
    )
    require(
        inactive.get("review", {}).get("production_eligible") is False,
        "inactive sentinel cannot be production eligible",
    )
    activities = {**activities, inactive["id"]: inactive}

    manifest = read_json(fixture_dir / "manifest.v1.json")
    case_paths = sorted((fixture_dir / "cases").glob("*.json"))
    require(
        len(case_paths) >= 20,
        f"at least 20 fixture cases required, found {len(case_paths)}",
    )
    require(
        manifest.get("case_count") == len(case_paths), "fixture manifest count mismatch"
    )
    manifest_by_id = {entry["id"]: entry for entry in manifest.get("cases", [])}
    positive = 0
    negative = 0
    coverage: set[str] = set()
    for path in case_paths:
        fixture = read_json(path)
        required = {"id", "description", "input", "expected", "coverage_tags"}
        require(set(fixture) == required, f"fixture keys mismatch in {path.name}")
        case_id = fixture["id"]
        require(
            bool(re.fullmatch(r"CASE_[A-Z0-9_]+", case_id)),
            f"invalid case ID: {case_id}",
        )
        require(case_id in manifest_by_id, f"fixture missing from manifest: {case_id}")
        digest = legacy_fixture_manifest_sha256(path)
        require(
            digest == manifest_by_id[case_id]["sha256"],
            f"fixture checksum mismatch: {case_id}",
        )
        actual = evaluate_case(activities, fixture["input"])
        require(
            actual == fixture["expected"],
            f"fixture result mismatch for {case_id}: expected={fixture['expected']} actual={actual}",
        )
        if actual["allowed_activity_ids"]:
            positive += 1
        else:
            negative += 1
        coverage.update(fixture["coverage_tags"])

    require(positive >= 8, f"at least 8 positive cases required, found {positive}")
    require(
        negative >= 10,
        f"at least 10 blocked/no-result cases required, found {negative}",
    )
    require(
        REQUIRED_COVERAGE <= coverage,
        f"fixture coverage missing: {sorted(REQUIRED_COVERAGE - coverage)}",
    )
    return len(case_paths), positive, negative, sorted(coverage)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the standalone Montessori domain fixture package"
    )
    parser.add_argument("--report", type=Path, help="Optional JSON metrics output path")
    parser.add_argument(
        "--fixture-root",
        type=Path,
        help="Optional fixture root for negative/mutation tests",
    )
    args = parser.parse_args()

    validate_contract_files()
    activities, objectives, band_counts = validate_catalog()
    fixture_root = args.fixture_root or FIXTURE_DIR
    if not fixture_root.is_absolute():
        fixture_root = ROOT / fixture_root
    fixture_count, positive, negative, coverage = validate_fixtures(
        activities, fixture_root
    )
    report = {
        "status": "MONTESSORI_DOMAIN_VALID",
        "activities": len(activities),
        "learning_objectives": len(objectives),
        "age_band_counts": band_counts,
        "fixture_cases": fixture_count,
        "positive_cases": positive,
        "negative_cases": negative,
        "coverage_tags": coverage,
        "review_status": "PROVISIONAL_OWNER_REVIEWED",
        "production_eligible": False,
        "network_required": False,
    }
    if args.report:
        report_path = args.report if args.report.is_absolute() else ROOT / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print("MONTESSORI_DOMAIN_VALID")
    print(f"activities={report['activities']}")
    print(f"learning_objectives={report['learning_objectives']}")
    print(f"age_bands={report['age_band_counts']}")
    print(f"fixtures={fixture_count} positive={positive} negative={negative}")
    print("review_status=PROVISIONAL_OWNER_REVIEWED production_eligible=false")
    print("network_required=false")


if __name__ == "__main__":
    main()
