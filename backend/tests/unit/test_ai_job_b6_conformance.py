"""BE2-01 Phase B batch B6 offline checks of the durable conformance runner's decision logic.

No database, broker or provider: these prove how the runner classifies evidence (JUnit
resolution, crash-window and acceptance mapping, exit codes, NOT_RUN without services). The
durable scenarios themselves only run on the Studio services.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO = Path(__file__).resolve().parents[3]
RUNNER_PATH = REPO / "features/FEAT-044-be2-ai-job-foundation/src/run_durable_conformance.py"
INTEGRATION = REPO / "backend/tests/integration/ai_jobs"


@pytest.fixture(scope="module")
def runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("b6_durable_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _junit(tmp_path: Path, cases: list[tuple[str, str, str]]) -> Path:
    body = []
    for module, name, status in cases:
        inner = {"PASS": "", "FAIL": "<failure message='x'/>", "SKIP": "<skipped/>"}[status]
        body.append(f'<testcase classname="tests.integration.ai_jobs.{module}" name="{name}">'
                    f"{inner}</testcase>")
    path = tmp_path / f"junit_{len(list(tmp_path.iterdir()))}.xml"
    path.write_text(f"<testsuites><testsuite>{''.join(body)}</testsuite></testsuites>",
                    encoding="utf-8")
    return path


def test_junit_resolution_never_turns_skips_or_missing_tests_into_pass(
    runner: ModuleType, tmp_path: Path
) -> None:
    path = _junit(tmp_path, [("test_a", "test_one", "PASS"), ("test_a", "test_two[x]", "PASS"),
                             ("test_b", "test_skip", "SKIP"), ("test_c", "test_bad", "FAIL")])
    outcomes, missing = runner.read_junit([path, tmp_path / "absent.xml"])
    assert missing == ["absent.xml"]
    resolve = runner.resolve_tests
    assert resolve(outcomes, ["test_a.py::test_*"])[0] == "PASS"
    assert resolve(outcomes, ["test_a.py::test_two*"])[0] == "PASS"
    assert resolve(outcomes, ["test_b.py::test_skip"])[0] == "NOT_RUN"
    assert resolve(outcomes, ["test_a.py::test_one", "test_z.py::test_*"])[0] == "NOT_RUN"
    assert resolve(outcomes, ["test_c.py::test_bad", "test_b.py::test_skip"])[0] == "FAIL"


def _defined_tests() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for path in INTEGRATION.glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found[path.name] = {node.name for node in tree.body
                            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
    return found


def test_every_mapped_pattern_names_an_existing_integration_test(runner: ModuleType) -> None:
    import fnmatch

    defined = _defined_tests()
    patterns = [p for w in runner.CRASH_WINDOWS for p in w.tests]
    patterns += [p for a in runner.ACCEPTANCE for p in a.tests]
    for pattern in patterns:
        module, _, name = pattern.partition("::")
        assert module in defined, pattern
        base = name.split("[")[0]
        assert any(fnmatch.fnmatchcase(test, base) or fnmatch.fnmatchcase(test, name)
                   for test in defined[module]), pattern


def test_plan_crash_windows_and_acceptance_are_all_mapped(runner: ModuleType) -> None:
    windows = [w.window_id for w in runner.CRASH_WINDOWS]
    assert windows == [f"W{n:02d}" for n in range(1, 13)]
    assert all(w.tests for w in runner.CRASH_WINDOWS)
    bounded = [w for w in runner.CRASH_WINDOWS if w.bounded]
    assert [w.window_id for w in bounded] == ["W07"]  # provider/completion window only
    assert [a.item for a in runner.ACCEPTANCE] == [f"B-{n:02d}" for n in range(1, 12)]
    assert {h["owner"] for h in runner.B12_HANDOFF} >= {"P2 / BE1 (Q2/Q3/Q8)", "BE2-14"}


def test_exit_codes_separate_fail_required_not_run_and_optional(runner: ModuleType) -> None:
    R = runner.Result
    ok = R("A-03", "x", runner.REQUIRED)
    optional_missing = R("A-17-http", "x", runner.OPTIONAL).mark(runner.NOT_RUN, "no fastapi")
    deferred = R("A-18", "x", runner.DEFERRED, runner.DEFERRED_STATUS)
    handoff = R("B-12", "x", runner.HANDOFF, runner.HANDOFF_STATUS)
    assert runner.exit_code([ok, optional_missing, deferred, handoff]) == 0
    missing = R("A-05", "x", runner.REQUIRED).mark(runner.NOT_RUN, "no PostgreSQL")
    assert runner.exit_code([ok, missing]) == 2
    failed = R("A-06", "x", runner.REQUIRED)
    failed.check("broken", False)
    assert runner.exit_code([ok, missing, failed]) == 1
    optional_failed = R("A-17-http", "x", runner.OPTIONAL)
    optional_failed.check("route", False)
    assert runner.exit_code([ok, optional_failed]) == 1  # a run that fails is never hidden


def _clear_services(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("BE2_TEST_PG_HOST", "BE2_TEST_PG_PASSWORD_FILE", "BE2_TEST_REDIS_HOST"):
        monkeypatch.delenv(name, raising=False)


def test_without_services_required_items_are_not_run_and_nothing_falls_back(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_services(monkeypatch)
    report_path = tmp_path / "report.json"
    assert runner.main(["--report", str(report_path)]) == 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    scenarios = {item["item"]: item for item in report["scenarios"]}
    assert sorted(scenarios) == sorted([f"A-{n:02d}" for n in range(1, 21)] + ["A-17-http"])
    for item, entry in scenarios.items():
        expected = {"A-02": "NOT_APPLICABLE", "A-19": "NOT_APPLICABLE",
                    "A-20": "NOT_APPLICABLE", "A-18": "DEFERRED"}.get(item, "NOT_RUN")
        assert entry["status"] == expected, item
        assert entry["checks"] == []  # nothing was executed on a substitute
    assert all(row["status"] == "NOT_RUN" for row in report["crash_matrix"])
    statuses = {row["item"]: row["status"] for row in report["acceptance"]}
    assert statuses["B-12"] == "HANDOFF" and "PASS" not in statuses.values()
    assert report["summary"]["exit_code"] == 2 and report["summary"]["overall"]["failed"] == []
    assert any("BE2_TEST_PG_HOST" in reason for reason in report["not_run_reasons"])


def test_passing_junit_alone_cannot_make_the_run_pass(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_services(monkeypatch)
    cases = [(module.removesuffix(".py"), name, "PASS")
             for module, names in _defined_tests().items() for name in names]
    junit = _junit(tmp_path, cases)
    phase_a = _junit(tmp_path, [("test_ai_job_application", "test_x", "PASS")])
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({"summary": {"PASS": 20, "FAIL": 0, "checks": 215,
                                               "checks_failed": 0},
                                   "results_sha256": "d17f58a3"}), encoding="utf-8")
    report_path = tmp_path / "report.json"
    code = runner.main(["--report", str(report_path), "--junit", str(junit),
                        "--phase-a-junit", str(phase_a), "--fixture-report", str(fixture)])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert all(row["status"] == "PASS" for row in report["crash_matrix"])
    statuses = {row["item"]: row["status"] for row in report["acceptance"]}
    assert statuses["B-01"] == "PASS" and statuses["B-11"] == "PASS"
    assert statuses["B-10"] == "NOT_RUN"  # durable scenarios did not run here
    assert code == 2  # required durable scenarios still NOT_RUN: no PASS without services
