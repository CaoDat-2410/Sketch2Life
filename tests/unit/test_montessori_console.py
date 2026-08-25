from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.montessori_golden.catalog import load_catalog
from tools.montessori_golden.eligibility import evaluate_case, validate_case_input
from tools.montessori_golden.evidence import EvidenceWriteError, record_evidence
from tools.montessori_golden.presentation import build_evaluation_document

ROOT = Path(__file__).resolve().parents[2]
CONSOLE = ROOT / "tools" / "montessori_golden_console.py"
CONSOLE_VALIDATOR = ROOT / "tools" / "validate_montessori_console.py"
SCENARIOS = ROOT / "tests" / "fixtures" / "montessori-console"
GOLDEN_CASES = ROOT / "tests" / "fixtures" / "montessori-golden" / "cases"


def run_console(
    *args: str, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CONSOLE), *args],
        cwd=ROOT,
        input=input_text,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_standalone_console_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(CONSOLE_VALIDATOR)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "MONTESSORI_CONSOLE_VALID" in result.stdout
    assert "golden_fixture_parity=74/74" in result.stdout


def test_shared_evaluator_has_exact_parity_with_all_74_golden_fixtures() -> None:
    catalog = load_catalog()
    case_paths = sorted(GOLDEN_CASES.glob("*.json"))
    assert len(case_paths) == 74
    for path in case_paths:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        activity = catalog.records[fixture["activity_ref"]["id"]]
        validate_case_input(
            activity,
            catalog.material_doc,
            fixture["input"],
            catalog.known_activity_ids,
        )
        assert (
            evaluate_case(activity, catalog.material_doc, fixture["input"])
            == fixture["expected"]
        ), fixture["id"]


def test_list_is_complete_explicit_and_never_recommends() -> None:
    result = run_console("list", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["count"] == 20
    assert len(payload["activities"]) == 20
    assert payload["selection_mode"] == "EXPLICIT_ACTIVITY_ONLY"
    assert payload["production_eligible"] is False
    assert "recommend" not in result.stdout.casefold()


@pytest.mark.parametrize("scenario", ["valid-primary.json", "valid-substitute.json"])
def test_primary_and_substitute_replays_are_valid(scenario: str) -> None:
    result = run_console(
        "replay",
        f"tests/fixtures/montessori-console/{scenario}",
        "--json",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["result"]["status"] == "VALID_CANDIDATE"
    assert payload["review_status"] == "PROVISIONAL_OWNER_REVIEWED"
    assert payload["production_eligible"] is False


def test_blocked_replay_returns_exit_two_and_all_ordered_reasons() -> None:
    result = run_console(
        "replay",
        "tests/fixtures/montessori-console/blocked-multiple.json",
        "--json",
    )
    assert result.returncode == 2, result.stderr
    payload = json.loads(result.stdout)
    assert payload["result"]["blocked"]["ACT-0004"] == [
        "BLOCK_MISSING_READINESS",
        "BLOCK_INSUFFICIENT_SUPERVISION",
        "BLOCK_POLICY_CONSTRAINT",
        "BLOCK_MISSING_MATERIAL",
    ]


def test_unknown_child_field_fails_closed() -> None:
    result = run_console(
        "replay",
        "tests/fixtures/montessori-console/malformed-unknown-field.json",
    )
    assert result.returncode == 1
    assert "input fields mismatch" in result.stderr
    assert "child_name" in result.stderr


def test_cross_activity_material_fails_as_invalid_input() -> None:
    result = run_console(
        "evaluate",
        "--activity",
        "ACT-0004",
        "--age-months",
        "16",
        "--readiness",
        "READY_SEARCH_PARTLY_HIDDEN",
        "--material",
        "GMAT-0016-PRIMARY",
        "--supervision",
        "DIRECT",
        "--policy",
        "CAREGIVER_PRESENT",
    )
    assert result.returncode == 1
    assert "cross-activity material IDs" in result.stderr


@pytest.mark.parametrize(
    ("extra_args", "message"),
    [
        (("--activity", "ACT-9999"), "unknown Golden activity ID"),
        (("--version", "1"), "version must be 2"),
        (("--candidate-status", "UNKNOWN"), "invalid candidate_status"),
    ],
)
def test_identity_version_and_enum_fail_closed(
    extra_args: tuple[str, ...], message: str
) -> None:
    args = [
        "evaluate",
        "--activity",
        "ACT-0004",
        "--age-months",
        "16",
        "--readiness",
        "READY_SEARCH_PARTLY_HIDDEN",
        "--material",
        "GMAT-0004-PRIMARY",
        "--supervision",
        "DIRECT",
        "--policy",
        "CAREGIVER_PRESENT",
        *extra_args,
    ]
    result = run_console(*args)
    assert result.returncode == 1
    assert message in result.stderr


def test_replay_path_cannot_escape_committed_scenario_directory() -> None:
    result = run_console("replay", "../outside.json")
    assert result.returncode == 1
    assert "must stay under tests/fixtures/montessori-console" in result.stderr


def test_guided_mode_matches_scriptable_valid_result() -> None:
    guided_input = (
        "ACT-0004\n"
        "16\n"
        "READY_SEARCH_PARTLY_HIDDEN\n"
        "\n"
        "GMAT-0004-PRIMARY\n"
        "DIRECT\n"
        "CAREGIVER_PRESENT\n"
        "\n"
    )
    result = run_console("interactive", "--json", input_text=guided_input)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["result"]["status"] == "VALID_CANDIDATE"
    assert payload["activity_ref"] == {"id": "ACT-0004", "version": 2}


def test_json_output_is_stable_for_identical_input() -> None:
    command = (
        "replay",
        "tests/fixtures/montessori-console/valid-primary.json",
        "--json",
    )
    first = run_console(*command)
    second = run_console(*command)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout


def test_evidence_writer_is_sanitized_confined_and_non_overwriting(
    tmp_path: Path,
) -> None:
    catalog = load_catalog()
    activity = catalog.records["ACT-0004"]
    case_input = json.loads((SCENARIOS / "valid-primary.json").read_text())["input"]
    document = build_evaluation_document(
        activity,
        case_input,
        evaluate_case(activity, catalog.material_doc, case_input),
    )
    runs_dir = tmp_path / "runs"
    path = record_evidence(
        "valid-primary-test",
        document,
        runs_dir=runs_dir,
        recorded_at="2026-08-25T00:00:00+00:00",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.parent == runs_dir
    assert payload["run_id"] == "valid-primary-test"
    assert str(ROOT) not in path.read_text(encoding="utf-8")
    with pytest.raises(EvidenceWriteError, match="already exists"):
        record_evidence("valid-primary-test", document, runs_dir=runs_dir)


@pytest.mark.parametrize("run_id", ["../escape", "/absolute", "C:path", "UPPER"])
def test_evidence_writer_rejects_unsafe_run_ids(tmp_path: Path, run_id: str) -> None:
    with pytest.raises(EvidenceWriteError, match="run ID"):
        record_evidence(run_id, {}, runs_dir=tmp_path / "runs")
    assert list(tmp_path.rglob("*.json")) == []


def test_console_modules_do_not_import_network_or_provider_clients() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [CONSOLE, *(ROOT / "tools" / "montessori_golden").glob("*.py")]
    )
    for forbidden in ("import requests", "import httpx", "import socket", "urllib"):
        assert forbidden not in sources
