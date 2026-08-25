from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = ROOT / "data" / "activity-catalog" / "golden" / "v1"
DEFAULT_BASE_DIR = ROOT / "data" / "activity-catalog" / "mvp"
DEFAULT_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "montessori-golden"
OWNER_REVIEW_PATH = (
    ROOT
    / "features"
    / "FEAT-013-montessori-golden-hardening"
    / "approvals"
    / "OWNER_CONTENT_REVIEW.v1.json"
)
SUPERVISION_RANK = {"NONE": 0, "NEARBY": 1, "DIRECT": 2}
AGE_BANDS = {"0-3": (0, 35), "3-6": (36, 71), "6-9": (72, 107), "9-12": (108, 155)}
REQUIRED_TAGS = {
    "valid",
    "blocked",
    "primary_material",
    "household_substitute",
    "readiness",
    "age",
    "age_boundary",
    "multiple_failure",
    "inactive",
    "no_valid",
    "0-3",
    "3-6",
    "6-9",
    "9-12",
}


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_value(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_baseline(
    base_dir: Path, selection: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    for filename, expected in selection["base_file_hashes"].items():
        path = base_dir / filename
        require(path.is_file(), f"baseline file missing: {filename}")
        require(
            sha256_file(path) == expected,
            f"baseline hash mismatch: {filename}",
        )
    base_doc = read_json(base_dir / "activities.v1.json")
    base_by_id = {item["id"]: item for item in base_doc["activities"]}
    require(selection["selection_count"] == 20, "selection must contain 20 records")
    require(len(selection["selections"]) == 20, "selection entry count mismatch")
    for item in selection["selections"]:
        activity_id = item["activity_id"]
        require(
            activity_id in base_by_id, f"selected base record missing: {activity_id}"
        )
        require(item["base_version"] == 1, f"base version must be 1: {activity_id}")
        require(
            item["candidate_version"] == 2,
            f"candidate version must be 2: {activity_id}",
        )
        require(
            sha256_value(base_by_id[activity_id]) == item["base_record_sha256"],
            f"base record hash mismatch: {activity_id}",
        )
    return base_by_id


def validate_progression(
    records: dict[str, dict[str, Any]], edges: list[dict[str, str]]
) -> None:
    all_ids = set(records)
    edge_pairs = {(edge["from_activity_id"], edge["to_activity_id"]) for edge in edges}
    require(len(edge_pairs) == len(edges), "duplicate progression edge")
    for source, target in edge_pairs:
        require(
            source in all_ids and target in all_ids,
            f"broken progression edge: {source}->{target}",
        )
        require(source != target, f"self progression edge: {source}")
        require(
            target in records[source]["progression_successor_ids"],
            f"record/edge mismatch: {source}->{target}",
        )

    adjacency = {activity_id: [] for activity_id in all_ids}
    for source, target in edge_pairs:
        adjacency[source].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        require(node not in visiting, f"progression cycle detected at {node}")
        if node in visited:
            return
        visiting.add(node)
        for target in adjacency[node]:
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for activity_id in all_ids:
        visit(activity_id)


def validate_catalog(
    base_dir: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    required_files = [
        GOLDEN_DIR / "selection-manifest.v1.json",
        GOLDEN_DIR / "activities.v2.json",
        GOLDEN_DIR / "material-registry.v1.json",
        GOLDEN_DIR / "progression-edges.v1.json",
        GOLDEN_DIR / "provenance.v1.json",
        ROOT / "packages/domain-montessori/schemas/golden-activity.v2.schema.json",
        ROOT / "packages/domain-montessori/schemas/golden-fixture-case.v1.schema.json",
        ROOT / "packages/domain-montessori/spec/GOLDEN_ACTIVITY_FIELD_GUIDE.md",
        ROOT / "packages/domain-montessori/spec/GOLDEN_REVIEW_RULES.md",
        OWNER_REVIEW_PATH,
    ]
    missing = [
        path.relative_to(ROOT).as_posix()
        for path in required_files
        if not path.is_file()
    ]
    require(not missing, f"missing golden artifacts: {missing}")

    selection = read_json(GOLDEN_DIR / "selection-manifest.v1.json")
    base_by_id = validate_baseline(base_dir, selection)
    golden_doc = read_json(GOLDEN_DIR / "activities.v2.json")
    material_doc = read_json(GOLDEN_DIR / "material-registry.v1.json")
    progression_doc = read_json(GOLDEN_DIR / "progression-edges.v1.json")
    provenance = read_json(GOLDEN_DIR / "provenance.v1.json")
    owner_review = read_json(OWNER_REVIEW_PATH)
    objective_doc = read_json(base_dir / "learning-objectives.v1.json")
    objective_ids = {item["id"] for item in objective_doc["objectives"]}
    records_list = golden_doc["activities"]
    require(
        golden_doc["schema_version"] == 2, "golden catalog schema version must be 2"
    )
    require(
        len(records_list) == 20,
        f"expected 20 golden records, found {len(records_list)}",
    )
    records = {item["id"]: item for item in records_list}
    require(len(records) == 20, "duplicate golden activity ID")
    selection_ids = {item["activity_id"] for item in selection["selections"]}
    require(
        set(records) == selection_ids, "golden records do not match frozen selection"
    )
    owner_decisions = {item["activity_id"]: item for item in owner_review["decisions"]}
    require(
        len(owner_review["decisions"]) == 20 and set(owner_decisions) == selection_ids,
        "owner review ledger does not match golden selection",
    )
    require(
        all(
            item["activity_version"] == 2 and item["decision"] == "ACCEPT"
            for item in owner_review["decisions"]
        ),
        "owner review ledger must explicitly accept every v2 record",
    )
    require(
        owner_review["reviewer_role"] == "PROJECT_OWNER"
        and bool(owner_review["reviewed_at"]),
        "owner review provenance is incomplete",
    )
    require(
        owner_review["production_eligible"] is False,
        "owner review cannot authorize production eligibility",
    )

    groups = {item["id"]: item for item in material_doc["groups"]}
    options = {item["id"]: item for item in material_doc["options"]}
    require(len(groups) == 20, "expected one material group per golden activity")
    require(
        len(options) == 40, "expected primary and substitute option per golden activity"
    )

    band_counts: Counter[str] = Counter()
    presentation_blocks: set[tuple[str, ...]] = set()
    safety_blocks: set[tuple[str, ...]] = set()
    readiness_texts: set[str] = set()
    material_labels: set[str] = set()
    all_base_ids = set(base_by_id)

    for activity_id, record in records.items():
        base = base_by_id[activity_id]
        require(record["version"] == 2, f"candidate version must be 2: {activity_id}")
        require(
            record["base_ref"]["activity_id"] == activity_id,
            f"base identity mismatch: {activity_id}",
        )
        require(
            record["base_ref"]["version"] == 1, f"base version mismatch: {activity_id}"
        )
        require(
            record["base_ref"]["record_sha256"] == sha256_value(base),
            f"base provenance mismatch: {activity_id}",
        )
        band = record["age_band"]
        require(
            band == base["age_band"] and band in AGE_BANDS,
            f"age band mismatch: {activity_id}",
        )
        band_counts[band] += 1
        band_min, band_max = AGE_BANDS[band]
        age_min = record["age_months"]["min"]
        age_max = record["age_months"]["max"]
        require(
            band_min <= age_min <= age_max <= band_max,
            f"age guidance outside band: {activity_id}",
        )
        require(
            age_min > band_min or age_max < band_max,
            f"age guidance was not narrowed: {activity_id}",
        )
        require(
            len(record["purpose_vi"]) >= 20 and len(record["direct_aim_vi"]) >= 20,
            f"aim text too short: {activity_id}",
        )
        require(
            len(record["indirect_aims_vi"]) >= 1,
            f"indirect aims missing: {activity_id}",
        )
        readiness = record["readiness_criteria"]
        require(readiness, f"readiness missing: {activity_id}")
        for criterion in readiness:
            require(
                bool(re.fullmatch(r"READY_[A-Z0-9_]+", criterion["id"])),
                f"invalid readiness ID: {activity_id}",
            )
            text = criterion["observable_vi"]
            require(len(text) >= 20, f"readiness observation too short: {activity_id}")
            require(
                text not in readiness_texts,
                f"duplicate readiness wording: {activity_id}",
            )
            readiness_texts.add(text)
        objectives = [
            record["objective_mapping"]["primary"],
            *record["objective_mapping"]["secondary"],
        ]
        require(
            1 <= len(objectives) <= 3, f"objective count outside 1-3: {activity_id}"
        )
        require(
            len({item["id"] for item in objectives}) == len(objectives),
            f"duplicate objective: {activity_id}",
        )
        require(
            all(
                item["id"] in objective_ids and item["version"] == 1
                for item in objectives
            ),
            f"invalid objective reference: {activity_id}",
        )
        require(
            set(record["prerequisite_activity_ids"]) <= all_base_ids,
            f"invalid prerequisite: {activity_id}",
        )
        require(
            set(record["progression_successor_ids"]) <= set(records),
            f"invalid successor: {activity_id}",
        )
        require(
            activity_id not in record["prerequisite_activity_ids"],
            f"self prerequisite: {activity_id}",
        )
        require(
            len(record["presentation_steps_vi"]) >= 4,
            f"presentation steps missing: {activity_id}",
        )
        block = tuple(record["presentation_steps_vi"])
        require(
            block not in presentation_blocks,
            f"duplicate presentation block: {activity_id}",
        )
        presentation_blocks.add(block)
        require(
            len(record["child_work_cycle_vi"]) >= 3,
            f"child work cycle missing: {activity_id}",
        )
        require(
            len(record["restoration_steps_vi"]) >= 2,
            f"restoration missing: {activity_id}",
        )
        require(
            len(record["isolation_of_difficulty_vi"]) >= 20,
            f"isolation text missing: {activity_id}",
        )
        require(
            len(record["control_of_error_vi"]) >= 20,
            f"control-of-error missing: {activity_id}",
        )
        require(
            record["duration_minutes"]["min"] > 0,
            f"duration minimum invalid: {activity_id}",
        )
        require(
            record["duration_minutes"]["min"]
            <= record["duration_minutes"]["max"]
            <= 90,
            f"duration range invalid: {activity_id}",
        )
        safety = record["safety"]
        require(
            safety["minimum_supervision"] in SUPERVISION_RANK,
            f"invalid supervision: {activity_id}",
        )
        require(
            len(safety["hazards_vi"]) >= 2 and len(safety["stop_conditions_vi"]) >= 3,
            f"activity-specific safety incomplete: {activity_id}",
        )
        require(
            safety["prohibited_substitutions_vi"],
            f"prohibited substitutions missing: {activity_id}",
        )
        safety_block = (*safety["hazards_vi"], *safety["stop_conditions_vi"])
        require(
            safety_block not in safety_blocks, f"duplicate safety block: {activity_id}"
        )
        safety_blocks.add(safety_block)
        if band == "0-3":
            require(
                safety["minimum_supervision"] == "DIRECT",
                f"0-3 requires direct supervision: {activity_id}",
            )
            require(
                "CAREGIVER_PRESENT" in record["policy_constraints"],
                f"0-3 caregiver policy missing: {activity_id}",
            )
        require(
            record["catalog_status"] == "ACTIVE_FIXTURE",
            f"golden record must be active: {activity_id}",
        )
        require(
            record["review"]["status"] == "PROVISIONAL_OWNER_REVIEWED",
            f"golden review status invalid: {activity_id}",
        )
        require(
            record["review"]["reviewer_role"] == owner_review["reviewer_role"]
            and record["review"]["reviewed_at"] == owner_review["reviewed_at"],
            f"golden owner-review provenance invalid: {activity_id}",
        )
        require(
            record["review"]["production_eligible"] is False,
            f"golden record cannot be production eligible: {activity_id}",
        )
        require(len(record["variants"]) == 3, f"three variants required: {activity_id}")
        expected_kinds = {"SUPPORT", "STANDARD", "EXTENSION"}
        require(
            {item["kind"] for item in record["variants"]} == expected_kinds,
            f"variant kinds incomplete: {activity_id}",
        )
        objective_identity = [item["id"] for item in objectives]
        for variant in record["variants"]:
            require(
                variant["activity_id"] == activity_id
                and variant["activity_version"] == 2,
                f"variant activity identity drift: {activity_id}",
            )
            require(
                variant["objective_ids"] == objective_identity,
                f"variant objective identity drift: {activity_id}",
            )
        require(
            record["material_group_ids"]
            == [f"GMG-{activity_id.removeprefix('ACT-')}-01"],
            f"material group identity mismatch: {activity_id}",
        )
        group = groups[record["material_group_ids"][0]]
        require(
            group["activity_id"] == activity_id and group["required"] is True,
            f"material group invalid: {activity_id}",
        )
        require(
            len(group["any_of"]) == 2,
            f"primary/substitute pair required: {activity_id}",
        )
        kinds = {options[option_id]["kind"] for option_id in group["any_of"]}
        require(
            kinds == {"PRIMARY", "HOUSEHOLD_SUBSTITUTE"},
            f"material kinds invalid: {activity_id}",
        )
        for option_id in group["any_of"]:
            option = options[option_id]
            require(
                option["activity_id"] == activity_id,
                f"material activity mismatch: {option_id}",
            )
            label = option["label_vi"]
            lowered = label.casefold()
            require(
                "approved_substitute" not in lowered
                and "vật liệu tương đương" not in lowered,
                f"placeholder substitute text: {option_id}",
            )
            require(
                len(label) >= 20 and len(option["suitability_vi"]) >= 20,
                f"material detail incomplete: {option_id}",
            )
            require(
                option["prohibited_vi"], f"material prohibition missing: {option_id}"
            )
            require(
                label not in material_labels,
                f"duplicate concrete material label: {option_id}",
            )
            material_labels.add(label)
            require(
                option["review_status"] == "PROVISIONAL_OWNER_REVIEWED"
                and option["production_eligible"] is False,
                f"material review guard invalid: {option_id}",
            )

    require(
        dict(band_counts) == {band: 5 for band in AGE_BANDS},
        f"expected five records per band: {dict(band_counts)}",
    )
    validate_progression(records, progression_doc["edges"])
    require(
        provenance["review_status"] == "PROVISIONAL_OWNER_REVIEWED",
        "golden provenance review status invalid",
    )
    require(
        provenance["owner_reviewed_at"] == owner_review["reviewed_at"]
        and provenance["reviewed_activity_count"] == 20,
        "golden provenance owner-review scope invalid",
    )
    require(
        provenance["production_eligible"] is False,
        "golden provenance cannot be production eligible",
    )
    require(
        provenance["network_required"] is False, "golden domain must remain offline"
    )
    return records, material_doc


def evaluate_case(
    activity: dict[str, Any], material_doc: dict[str, Any], case_input: dict[str, Any]
) -> dict[str, Any]:
    reasons: list[str] = []
    if case_input["candidate_status"] != "ACTIVE_FIXTURE":
        reasons.append("BLOCK_INACTIVE")
    if case_input["age_months"] < activity["age_months"]["min"]:
        reasons.append("BLOCK_AGE_BELOW_MIN")
    if case_input["age_months"] > activity["age_months"]["max"]:
        reasons.append("BLOCK_AGE_ABOVE_MAX")
    required_readiness = {item["id"] for item in activity["readiness_criteria"]}
    if not required_readiness <= set(case_input["readiness_ids"]):
        reasons.append("BLOCK_MISSING_READINESS")
    if not set(activity["prerequisite_activity_ids"]) <= set(
        case_input["completed_activity_ids"]
    ):
        reasons.append("BLOCK_MISSING_PREREQUISITE")
    if (
        SUPERVISION_RANK[case_input["supervision_level"]]
        < SUPERVISION_RANK[activity["safety"]["minimum_supervision"]]
    ):
        reasons.append("BLOCK_INSUFFICIENT_SUPERVISION")
    if not set(activity["policy_constraints"]) <= set(case_input["policy_flags"]):
        reasons.append("BLOCK_POLICY_CONSTRAINT")
    groups = {item["id"]: item for item in material_doc["groups"]}
    available = set(case_input["available_material_option_ids"])
    if any(
        not (set(groups[group_id]["any_of"]) & available)
        for group_id in activity["material_group_ids"]
    ):
        reasons.append("BLOCK_MISSING_MATERIAL")
    if reasons:
        return {
            "status": "NO_VALID_ACTIVITY",
            "allowed_activity_ids": [],
            "blocked": {activity["id"]: reasons},
        }
    return {
        "status": "VALID_CANDIDATE",
        "allowed_activity_ids": [activity["id"]],
        "blocked": {},
    }


def validate_fixtures(
    records: dict[str, dict[str, Any]], material_doc: dict[str, Any], fixture_dir: Path
) -> tuple[int, int, int, list[str]]:
    manifest = read_json(fixture_dir / "manifest.v1.json")
    case_paths = sorted((fixture_dir / "cases").glob("*.json"))
    require(
        len(case_paths) >= 60,
        f"at least 60 golden fixtures required, found {len(case_paths)}",
    )
    require(
        manifest["case_count"] == len(case_paths),
        "golden fixture manifest count mismatch",
    )
    manifest_by_id = {item["id"]: item for item in manifest["cases"]}
    positive = 0
    blocked = 0
    coverage: set[str] = set()
    per_activity: Counter[str] = Counter()
    for path in case_paths:
        case = read_json(path)
        case_id = case["id"]
        require(
            bool(re.fullmatch(r"GCASE_[A-Z0-9_]+", case_id)),
            f"invalid golden case ID: {case_id}",
        )
        require(
            case_id in manifest_by_id, f"case missing from golden manifest: {case_id}"
        )
        require(
            sha256_file(path) == manifest_by_id[case_id]["sha256"],
            f"golden fixture checksum mismatch: {case_id}",
        )
        activity_id = case["activity_ref"]["id"]
        require(
            activity_id in records and case["activity_ref"]["version"] == 2,
            f"invalid activity ref: {case_id}",
        )
        actual = evaluate_case(records[activity_id], material_doc, case["input"])
        require(
            actual == case["expected"],
            f"golden fixture mismatch {case_id}: expected={case['expected']} actual={actual}",
        )
        coverage.update(case["coverage_tags"])
        per_activity[activity_id] += 1
        if actual["allowed_activity_ids"]:
            positive += 1
        else:
            blocked += 1
    require(
        all(per_activity[activity_id] >= 3 for activity_id in records),
        "every golden activity requires at least three fixtures",
    )
    require(
        REQUIRED_TAGS <= coverage,
        f"golden fixture coverage missing: {sorted(REQUIRED_TAGS - coverage)}",
    )
    return len(case_paths), positive, blocked, sorted(coverage)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate FEAT-013 Montessori golden catalog"
    )
    parser.add_argument("--report", type=Path, help="Optional JSON metrics output")
    parser.add_argument(
        "--fixture-root", type=Path, help="Optional fixture root for mutation tests"
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        help="Optional FEAT-002 baseline directory for mutation tests",
    )
    args = parser.parse_args()
    base_dir = args.baseline_dir or DEFAULT_BASE_DIR
    fixture_dir = args.fixture_root or DEFAULT_FIXTURE_DIR
    if not base_dir.is_absolute():
        base_dir = ROOT / base_dir
    if not fixture_dir.is_absolute():
        fixture_dir = ROOT / fixture_dir
    records, material_doc = validate_catalog(base_dir)
    case_count, positive, blocked, coverage = validate_fixtures(
        records, material_doc, fixture_dir
    )
    report = {
        "status": "MONTESSORI_GOLDEN_VALID",
        "activities": len(records),
        "age_band_counts": dict(Counter(item["age_band"] for item in records.values())),
        "material_options": len(material_doc["options"]),
        "fixture_cases": case_count,
        "positive_cases": positive,
        "blocked_cases": blocked,
        "coverage_tags": coverage,
        "review_status": "PROVISIONAL_OWNER_REVIEWED",
        "production_eligible": False,
        "baseline_unchanged": True,
        "network_required": False,
    }
    if args.report:
        report_path = args.report if args.report.is_absolute() else ROOT / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("MONTESSORI_GOLDEN_VALID")
    print(f"activities={report['activities']} age_bands={report['age_band_counts']}")
    print(f"material_options={report['material_options']}")
    print(f"fixtures={case_count} positive={positive} blocked={blocked}")
    print("review_status=PROVISIONAL_OWNER_REVIEWED production_eligible=false")
    print("baseline_unchanged=true network_required=false")


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValidationError) as exc:
        print(f"MONTESSORI_GOLDEN_INVALID: {exc}")
        raise SystemExit(1) from exc
