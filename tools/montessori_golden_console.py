from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TextIO

from montessori_golden.catalog import (
    CatalogError,
    GoldenCatalog,
    list_activity_summaries,
    load_catalog,
)
from montessori_golden.eligibility import (
    ScenarioValidationError,
    evaluate_case,
    validate_case_input,
)
from montessori_golden.evidence import EvidenceWriteError, record_evidence
from montessori_golden.presentation import (
    WARNING,
    build_evaluation_document,
    format_activity_list,
    format_evaluation,
)

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "tests" / "fixtures" / "montessori-console"
SCENARIO_FIELDS = {"activity_ref", "input"}
ACTIVITY_REF_FIELDS = {"id", "version"}


class ConsoleInputError(ValueError):
    """Raised for invalid commands, scenario structure, or references."""


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_scenario(
    catalog: GoldenCatalog, scenario: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(scenario, dict) or set(scenario) != SCENARIO_FIELDS:
        actual = (
            sorted(scenario) if isinstance(scenario, dict) else type(scenario).__name__
        )
        raise ConsoleInputError(
            f"scenario fields mismatch: expected={sorted(SCENARIO_FIELDS)} actual={actual}"
        )
    activity_ref = scenario["activity_ref"]
    if not isinstance(activity_ref, dict) or set(activity_ref) != ACTIVITY_REF_FIELDS:
        raise ConsoleInputError("activity_ref must contain only id and version")
    activity_id = activity_ref["id"]
    if not isinstance(activity_id, str) or activity_id not in catalog.records:
        raise ConsoleInputError(f"unknown Golden activity ID: {activity_id}")
    if activity_ref["version"] != 2:
        raise ConsoleInputError("Golden activity version must be 2")
    activity = catalog.records[activity_id]
    case_input = scenario["input"]
    validate_case_input(
        activity,
        catalog.material_doc,
        case_input,
        catalog.known_activity_ids,
    )
    return activity, case_input


def _emit_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def run_scenario(
    catalog: GoldenCatalog,
    scenario: dict[str, Any],
    *,
    json_output: bool,
    evidence_run_id: str | None,
) -> int:
    activity, case_input = validate_scenario(catalog, scenario)
    result = evaluate_case(activity, catalog.material_doc, case_input)
    document = build_evaluation_document(activity, case_input, result)
    evidence_path = (
        record_evidence(evidence_run_id, document) if evidence_run_id else None
    )
    if json_output:
        _emit_json(document)
    else:
        print(format_evaluation(document))
    if evidence_path:
        print(
            "evidence=" + evidence_path.relative_to(ROOT).as_posix(),
            file=sys.stderr if json_output else sys.stdout,
        )
    return 0 if result["status"] == "VALID_CANDIDATE" else 2


def _scenario_from_evaluate_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "activity_ref": {"id": args.activity, "version": args.version},
        "input": {
            "age_months": args.age_months,
            "readiness_ids": args.readiness,
            "completed_activity_ids": args.completed,
            "available_material_option_ids": args.material,
            "supervision_level": args.supervision,
            "policy_flags": args.policy,
            "candidate_status": args.candidate_status,
        },
    }


def _load_replay(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    allowed_root = SCENARIO_DIR.resolve()
    if not path.is_relative_to(allowed_root):
        raise ConsoleInputError(
            "replay file must stay under tests/fixtures/montessori-console"
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConsoleInputError(
            f"cannot read valid replay scenario: {path.name}"
        ) from exc


def _prompt(
    label: str,
    input_fn: Callable[[str], str],
    *,
    default: str | None = None,
) -> str:
    suffix = f" [{default}]" if default is not None else ""
    print(f"{label}{suffix}: ", end="", file=sys.stderr)
    value = input_fn("").strip()
    return value or (default or "")


def _interactive_scenario(
    catalog: GoldenCatalog,
    input_fn: Callable[[str], str] = input,
    output_stream: TextIO = sys.stdout,
) -> dict[str, Any]:
    summaries = list_activity_summaries(catalog)
    print(format_activity_list(summaries), file=output_stream)
    activity_id = _prompt("activity ID", input_fn)
    if activity_id not in catalog.records:
        raise ConsoleInputError(f"unknown Golden activity ID: {activity_id}")
    activity = catalog.records[activity_id]
    groups = {item["id"]: item for item in catalog.material_doc["groups"]}
    allowed_materials = [
        option_id
        for group_id in activity["material_group_ids"]
        for option_id in groups[group_id]["any_of"]
    ]
    readiness = [item["id"] for item in activity["readiness_criteria"]]
    print(f"allowed readiness IDs: {','.join(readiness)}", file=output_stream)
    print(f"allowed material IDs: {','.join(allowed_materials)}", file=output_stream)
    try:
        age_months = int(_prompt("age months", input_fn))
    except ValueError as exc:
        raise ConsoleInputError("age months must be an integer") from exc
    return {
        "activity_ref": {"id": activity_id, "version": 2},
        "input": {
            "age_months": age_months,
            "readiness_ids": _parse_csv(_prompt("readiness IDs", input_fn)),
            "completed_activity_ids": _parse_csv(
                _prompt("completed activity IDs", input_fn, default="")
            ),
            "available_material_option_ids": _parse_csv(
                _prompt("material IDs", input_fn)
            ),
            "supervision_level": _prompt(
                "supervision NONE/NEARBY/DIRECT", input_fn
            ).upper(),
            "policy_flags": _parse_csv(_prompt("policy flags", input_fn, default="")),
            "candidate_status": _prompt(
                "candidate status", input_fn, default="ACTIVE_FIXTURE"
            ).upper(),
        },
    }


def _add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit stable compact JSON")
    parser.add_argument(
        "--record-evidence",
        metavar="RUN_ID",
        help="Write one sanitized non-overwriting FEAT-014 evidence run",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline activity-explicit Montessori Golden test console"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_parser = subparsers.add_parser(
        "list", help="List 20 Golden records without selecting or ranking"
    )
    list_parser.add_argument("--json", action="store_true")

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Evaluate one explicitly selected activity"
    )
    evaluate_parser.add_argument("--activity", required=True)
    evaluate_parser.add_argument("--version", type=int, default=2)
    evaluate_parser.add_argument("--age-months", required=True, type=int)
    evaluate_parser.add_argument("--readiness", action="append", default=[])
    evaluate_parser.add_argument("--completed", action="append", default=[])
    evaluate_parser.add_argument("--material", action="append", default=[])
    evaluate_parser.add_argument("--supervision", required=True)
    evaluate_parser.add_argument("--policy", action="append", default=[])
    evaluate_parser.add_argument("--candidate-status", default="ACTIVE_FIXTURE")
    _add_output_options(evaluate_parser)

    replay_parser = subparsers.add_parser(
        "replay", help="Replay a committed synthetic console scenario"
    )
    replay_parser.add_argument("scenario")
    _add_output_options(replay_parser)

    interactive_parser = subparsers.add_parser(
        "interactive", help="Prompt for one explicit synthetic scenario"
    )
    _add_output_options(interactive_parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog()
        if args.command == "list":
            summaries = list_activity_summaries(catalog)
            if args.json:
                _emit_json(
                    {
                        "console_schema_version": 1,
                        "count": len(summaries),
                        "selection_mode": "EXPLICIT_ACTIVITY_ONLY",
                        "activities": summaries,
                        "review_status": "PROVISIONAL_OWNER_REVIEWED",
                        "production_eligible": False,
                        "warning": WARNING,
                    }
                )
            else:
                print(format_activity_list(summaries))
            return 0
        if args.command == "evaluate":
            scenario = _scenario_from_evaluate_args(args)
        elif args.command == "replay":
            scenario = _load_replay(args.scenario)
        else:
            scenario = _interactive_scenario(
                catalog, output_stream=sys.stderr if args.json else sys.stdout
            )
        return run_scenario(
            catalog,
            scenario,
            json_output=args.json,
            evidence_run_id=args.record_evidence,
        )
    except (
        CatalogError,
        ConsoleInputError,
        ScenarioValidationError,
        EvidenceWriteError,
    ) as exc:
        print(f"MONTESSORI_CONSOLE_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
