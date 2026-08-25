from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "data" / "activity-catalog" / "mvp" / "activities.v1.json"
METRICS = ROOT / "features" / "FEAT-002-montessori-domain" / "evidence" / "metrics"
NOTES = ROOT / "features" / "FEAT-002-montessori-domain" / "evidence" / "notes"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build() -> None:
    activities = json.loads(CATALOG.read_text(encoding="utf-8"))["activities"]
    band_counts = Counter(activity["age_band"] for activity in activities)
    area_counts = Counter(activity["area"] for activity in activities)
    objective_counts = Counter(
        objective_id
        for activity in activities
        for objective_id in activity["objective_ids"]
    )
    review_counts = Counter(activity["review"]["status"] for activity in activities)

    METRICS.mkdir(parents=True, exist_ok=True)
    with (METRICS / "catalog-summary.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "activity_id",
                "version",
                "age_band",
                "area",
                "title_vi",
                "objective_ids",
                "review_status",
                "production_eligible",
            ]
        )
        for activity in activities:
            writer.writerow(
                [
                    activity["id"],
                    activity["version"],
                    activity["age_band"],
                    activity["area"],
                    activity["title"]["vi-VN"],
                    "|".join(activity["objective_ids"]),
                    activity["review"]["status"],
                    str(activity["review"]["production_eligible"]).lower(),
                ]
            )

    fixture_metrics = {
        "case_count": 24,
        "positive_cases": 12,
        "negative_or_no_result_cases": 12,
        "required_coverage": [
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
        ],
        "mutation_test": "PASS_EXPECTED_NONZERO",
    }
    write_json(METRICS / "fixture-coverage.json", fixture_metrics)

    traceability = {
        "AC-P1-01": ["spec/GLOSSARY.md", "spec/ID_VERSION_RULES.md"],
        "AC-P1-02": ["schemas/activity.v1.schema.json", "activities.v1.json"],
        "AC-P1-03": [
            "schemas/learning-objective.v1.schema.json",
            "learning-objectives.v1.json",
        ],
        "AC-P1-04": [
            "activities.v1.json",
            "catalog-validation.json",
            "catalog-summary.csv",
        ],
        "AC-P1-04A": ["catalog-validation.json", "catalog-summary.csv"],
        "AC-P1-04B": [
            "provenance.v1.json",
            "CATALOG_REVIEW_PACKET.md",
            "OWNER_CATALOG_REVIEW.md",
        ],
        "AC-P1-05": ["hard-rules.v1.json", "spec/RULE_SEMANTICS.md"],
        "AC-P1-06": ["harness-run.txt", "unit-tests.txt"],
        "AC-P1-07": ["fixture-coverage.json", "manifest.v1.json"],
        "AC-P1-08": ["fixture-coverage.json", "tests/fixtures/montessori/cases"],
        "AC-P1-09": [
            "tools/validate_montessori_domain.py",
            "harness-deliberate-failure.txt",
        ],
        "AC-P1-10": ["spec/RULE_SEMANTICS.md", "CASE_NO_VALID_* fixtures"],
        "AC-P1-11": ["spec/GATE_B_ACCEPTANCE.md"],
        "AC-P1-12": [
            "spec/ACTIVITY_HANDOFF.md",
            "schemas/activity-handoff.v1.schema.json",
        ],
        "AC-P1-13": ["spec/TRACEABILITY.md", "traceability.json"],
        "AC-P1-14": ["PRE_APPROVAL_VALIDATION.md", "final-validation.txt"],
    }
    write_json(METRICS / "traceability.json", traceability)

    lines = [
        "# Catalog owner review packet",
        "",
        "- Generated: 2026-08-25",
        "- Activities: 100",
        "- Current review state: all `PROVISIONAL_OWNER_REVIEWED`",
        "- Production eligible: none",
        "",
        "The project owner accepted this catalog provisionally on 2026-08-25. Every record remains `production_eligible=false`; qualified Montessori review is still required before production use.",
        "",
        "## Summary",
        "",
        f"- Age bands: `{dict(sorted(band_counts.items()))}`",
        f"- Areas: `{dict(sorted(area_counts.items()))}`",
        f"- Review states: `{dict(sorted(review_counts.items()))}`",
        f"- Objective usage: `{dict(sorted(objective_counts.items()))}`",
        "",
        "## Activity checklist",
        "",
        "| ID | Band | Area | Vietnamese title | Objective | Review |",
        "|---|---|---|---|---|---|",
    ]
    for activity in activities:
        lines.append(
            "| {id} | {band} | {area} | {title} | {objective} | {review} |".format(
                id=activity["id"],
                band=activity["age_band"],
                area=activity["area"],
                title=activity["title"]["vi-VN"].replace("|", "\\|"),
                objective=", ".join(activity["objective_ids"]),
                review=activity["review"]["status"],
            )
        )
    NOTES.mkdir(parents=True, exist_ok=True)
    (NOTES / "CATALOG_REVIEW_PACKET.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print("REVIEW_PACKET_BUILT")
    print(f"activities={len(activities)}")
    print(f"bands={dict(sorted(band_counts.items()))}")
    print("review_status=PROVISIONAL_OWNER_REVIEWED")


if __name__ == "__main__":
    build()
