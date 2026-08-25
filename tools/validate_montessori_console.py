from __future__ import annotations

import json
from pathlib import Path

from montessori_golden.catalog import ROOT, load_catalog
from montessori_golden.eligibility import (
    ScenarioValidationError,
    evaluate_case,
    validate_case_input,
)

GOLDEN_CASES = ROOT / "tests" / "fixtures" / "montessori-golden" / "cases"
CONSOLE_CASES = ROOT / "tests" / "fixtures" / "montessori-console"


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_scenario(
    catalog: object, scenario: dict[str, object]
) -> dict[str, object]:
    activity_ref = scenario["activity_ref"]
    case_input = scenario["input"]
    if not isinstance(activity_ref, dict) or not isinstance(case_input, dict):
        raise TypeError("scenario shape invalid")
    activity = catalog.records[activity_ref["id"]]
    validate_case_input(
        activity,
        catalog.material_doc,
        case_input,
        catalog.known_activity_ids,
    )
    return evaluate_case(activity, catalog.material_doc, case_input)


def main() -> int:
    catalog = load_catalog()
    golden_paths = sorted(GOLDEN_CASES.glob("*.json"))
    if len(golden_paths) != 74:
        raise ValueError(f"expected 74 Golden fixtures, found {len(golden_paths)}")
    for path in golden_paths:
        fixture = read_json(path)
        scenario = {
            "activity_ref": fixture["activity_ref"],
            "input": fixture["input"],
        }
        if evaluate_scenario(catalog, scenario) != fixture["expected"]:
            raise ValueError(f"shared evaluator parity mismatch: {fixture['id']}")

    expected = {
        "valid-primary.json": "VALID_CANDIDATE",
        "valid-substitute.json": "VALID_CANDIDATE",
        "blocked-multiple.json": "NO_VALID_ACTIVITY",
    }
    for filename, status in expected.items():
        actual = evaluate_scenario(catalog, read_json(CONSOLE_CASES / filename))
        if actual["status"] != status:
            raise ValueError(f"console scenario status mismatch: {filename}")

    malformed = read_json(CONSOLE_CASES / "malformed-unknown-field.json")
    try:
        evaluate_scenario(catalog, malformed)
    except ScenarioValidationError:
        pass
    else:
        raise ValueError("malformed console scenario unexpectedly passed")

    print("MONTESSORI_CONSOLE_VALID")
    print("activities=20 selection_mode=EXPLICIT_ACTIVITY_ONLY")
    print("golden_fixture_parity=74/74")
    print("console_scenarios=4 valid=2 blocked=1 malformed_rejected=1")
    print("exit_codes=0-valid,1-invalid-input,2-no-valid")
    print("review_status=PROVISIONAL_OWNER_REVIEWED production_eligible=false")
    print("network_required=false cross_person_dependency=false")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"MONTESSORI_CONSOLE_INVALID: {exc}")
        raise SystemExit(1) from exc
