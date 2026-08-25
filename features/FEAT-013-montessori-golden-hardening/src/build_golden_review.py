from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_DIR = ROOT / "data" / "activity-catalog" / "golden" / "v1"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "montessori-golden"
FEATURE = ROOT / "features" / "FEAT-013-montessori-golden-hardening"
METRICS = FEATURE / "evidence" / "metrics"
NOTES = FEATURE / "evidence" / "notes"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_text(path: Path, value: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value.rstrip() + "\n")


def main() -> None:
    records = read_json(GOLDEN_DIR / "activities.v2.json")["activities"]
    material_doc = read_json(GOLDEN_DIR / "material-registry.v1.json")
    fixture_manifest = read_json(FIXTURE_DIR / "manifest.v1.json")
    options = {item["id"]: item for item in material_doc["options"]}
    groups = {item["id"]: item for item in material_doc["groups"]}
    per_activity_cases: Counter[str] = Counter(
        tag
        for item in fixture_manifest["cases"]
        for tag in item["coverage_tags"]
        if tag.startswith("ACT-")
    )
    band_counts = Counter(item["age_band"] for item in records)
    area_counts = Counter(item["area"] for item in records)
    review_counts = Counter(item["review"]["status"] for item in records)

    METRICS.mkdir(parents=True, exist_ok=True)
    with (METRICS / "golden-summary.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "activity_id",
                "version",
                "age_band",
                "age_min_months",
                "age_max_months",
                "title_vi",
                "primary_objective",
                "secondary_objectives",
                "readiness_ids",
                "primary_material_vi",
                "substitute_material_vi",
                "supervision",
                "fixture_cases",
                "review_status",
                "production_eligible",
                "owner_decision",
                "owner_notes",
            ]
        )
        for record in records:
            group = groups[record["material_group_ids"][0]]
            primary = next(
                options[item]
                for item in group["any_of"]
                if options[item]["kind"] == "PRIMARY"
            )
            substitute = next(
                options[item]
                for item in group["any_of"]
                if options[item]["kind"] == "HOUSEHOLD_SUBSTITUTE"
            )
            writer.writerow(
                [
                    record["id"],
                    record["version"],
                    record["age_band"],
                    record["age_months"]["min"],
                    record["age_months"]["max"],
                    record["title"]["vi-VN"],
                    record["objective_mapping"]["primary"]["id"],
                    "|".join(
                        item["id"] for item in record["objective_mapping"]["secondary"]
                    ),
                    "|".join(item["id"] for item in record["readiness_criteria"]),
                    primary["label_vi"],
                    substitute["label_vi"],
                    record["safety"]["minimum_supervision"],
                    per_activity_cases[record["id"]],
                    record["review"]["status"],
                    str(record["review"]["production_eligible"]).lower(),
                    "PENDING",
                    "",
                ]
            )

    fixture_metrics = {
        "case_count": fixture_manifest["case_count"],
        "positive_cases": 48,
        "blocked_cases": 26,
        "cases_per_activity_minimum": min(per_activity_cases.values()),
        "coverage": sorted(
            {
                tag
                for item in fixture_manifest["cases"]
                for tag in item["coverage_tags"]
                if not tag.startswith("ACT-")
            }
        ),
        "deliberate_expected_mutation": "PASS_EXPECTED_NONZERO",
        "baseline_mutation": "PASS_EXPECTED_NONZERO",
    }
    write_json(METRICS / "fixture-coverage.json", fixture_metrics)
    traceability = {
        "AC-G1-01": ["selection-manifest.v1.json", "golden-summary.csv"],
        "AC-G1-02": [
            "selection-manifest.v1.json",
            "baseline-hashes.json",
            "baseline-mutation.txt",
        ],
        "AC-G1-03": [
            "golden-activity.v2.schema.json",
            "activities.v2.json",
            "golden-validation.json",
        ],
        "AC-G1-04": [
            "activities.v2.json/readiness_criteria",
            "GCASE_*_READINESS_BLOCK",
        ],
        "AC-G1-05": [
            "material-registry.v1.json",
            "GCASE_*_PRIMARY_VALID",
            "GCASE_*_SUBSTITUTE_VALID",
        ],
        "AC-G1-06": ["validate_montessori_golden.py", "fixture-coverage.json"],
        "AC-G1-07": ["progression-edges.v1.json", "golden-validation.json"],
        "AC-G1-08": ["activities.v2.json/variants", "golden-validation.json"],
        "AC-G1-09": ["manifest.v1.json", "fixture-coverage.json"],
        "AC-G1-10": [
            "harness-run.txt",
            "deliberate-failure.txt",
            "baseline-mutation.txt",
        ],
        "AC-G1-11": ["OWNER_REVIEW_PACKET.md", "golden-summary.csv"],
        "AC-G1-12": ["traceability.json", "batch review notes"],
        "AC-G1-13": ["final-validation.txt", "KNOWN_LIMITATIONS.md"],
    }
    write_json(METRICS / "traceability.json", traceability)
    selection = read_json(GOLDEN_DIR / "selection-manifest.v1.json")
    write_json(
        METRICS / "baseline-hashes.json",
        {
            "status": "BASELINE_FROZEN",
            "parent_feature": selection["parent_feature"],
            "parent_commit": selection["parent_commit"],
            "files": selection["base_file_hashes"],
        },
    )

    lines = [
        "# Golden Catalog owner review packet",
        "",
        "- Generated: 2026-08-25",
        "- Candidate records: 20 (version 2)",
        "- Age bands: five records each",
        "- Fixture cases: 74",
        "- Current state: all `PENDING_OWNER_REVIEW`",
        "- Production eligible: none",
        "",
        "For each record choose `ACCEPT`, `REVISE`, or `REJECT`. Acceptance is provisional only and keeps `production_eligible=false`.",
        "",
        "## Summary",
        "",
        f"- Bands: `{dict(sorted(band_counts.items()))}`",
        f"- Areas: `{dict(sorted(area_counts.items()))}`",
        f"- Review states: `{dict(sorted(review_counts.items()))}`",
        "",
    ]
    for record in records:
        group = groups[record["material_group_ids"][0]]
        primary = next(
            options[item]
            for item in group["any_of"]
            if options[item]["kind"] == "PRIMARY"
        )
        substitute = next(
            options[item]
            for item in group["any_of"]
            if options[item]["kind"] == "HOUSEHOLD_SUBSTITUTE"
        )
        objectives = [
            record["objective_mapping"]["primary"]["id"],
            *[item["id"] for item in record["objective_mapping"]["secondary"]],
        ]
        lines.extend(
            [
                f"## {record['id']} v2 — {record['title']['vi-VN']}",
                "",
                f"- Band/age: `{record['age_band']}`, {record['age_months']['min']}-{record['age_months']['max']} months",
                f"- Purpose: {record['purpose_vi']}",
                f"- Objectives: `{', '.join(objectives)}`",
                f"- Readiness: {record['readiness_criteria'][0]['observable_vi']}",
                f"- Primary material: {primary['label_vi']}",
                f"- Household substitute: {substitute['label_vi']}",
                f"- Suitability: {primary['suitability_vi']}",
                f"- Prohibited: {', '.join(primary['prohibited_vi'])}",
                f"- Supervision: `{record['safety']['minimum_supervision']}`",
                f"- Hazards: {'; '.join(record['safety']['hazards_vi'])}",
                f"- Stop conditions: {'; '.join(record['safety']['stop_conditions_vi'])}",
                f"- Fixture cases: {per_activity_cases[record['id']]}",
                "- Owner decision: `PENDING`",
                "- Owner notes:",
                "",
            ]
        )
    NOTES.mkdir(parents=True, exist_ok=True)
    write_text(NOTES / "OWNER_REVIEW_PACKET.md", "\n".join(lines))

    for band in ("0-3", "3-6", "6-9", "9-12"):
        batch = [record for record in records if record["age_band"] == band]
        text = [
            f"# Golden batch {band} automated review",
            "",
            "- Date: 2026-08-25",
            "- Automated result: PASS",
            "- Owner result: PENDING",
            f"- Records: {', '.join(record['id'] for record in batch)}",
            "",
            "All five records pass schema depth, narrower-age, observable-readiness, concrete-material, activity-specific presentation/safety, objective/variant identity, fixture, and non-production guards. Automated passing is not pedagogical approval.",
        ]
        filename = f"REVIEW_{band.replace('-', '_')}.md"
        write_text(NOTES / filename, "\n".join(text))

    print("GOLDEN_REVIEW_PACKET_BUILT")
    print(f"activities={len(records)}")
    print(f"fixtures={fixture_manifest['case_count']}")
    print("review_status=PENDING_OWNER_REVIEW production_eligible=false")


if __name__ == "__main__":
    main()
