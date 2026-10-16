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
INTEGRATION_ID = "tests/integration/ai_jobs"  # pytest ids are relative to the backend rootdir
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
    """pytest-style JUnit: ``module`` is a short module name or a ``tests/.../test_x.py`` path;
    class parts of a ``C::t`` test id go into ``classname`` as pytest writes them."""

    body = []
    for module, name, status in cases:
        inner = {"PASS": "", "FAIL": "<failure message='x'/>", "SKIP": "<skipped/>"}[status]
        dotted = (module.removesuffix(".py").replace("/", ".") if "/" in module
                  else f"tests.integration.ai_jobs.{module}")
        *classes, function = name.split("::")
        classname = ".".join([dotted, *classes])
        body.append(f'<testcase classname="{classname}" name="{function}">{inner}</testcase>')
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


def _suite_cases(runner: ModuleType, globs: tuple[str, ...],
                 status: str = "PASS") -> list[tuple[str, str, str]]:
    inventory, detail = runner.suite_inventory(globs)
    assert inventory, detail  # real pytest collection of the running tree
    return [(module, name, status) for module, names in sorted(inventory.items())
            for name in sorted(names)]


def _fixture(tmp_path: Path, *, checks: int = 215, items: int = 20) -> Path:
    path = tmp_path / f"fixture_{len(list(tmp_path.iterdir()))}.json"
    path.write_text(json.dumps({
        "summary": {"PASS": items, "FAIL": 0, "checks": checks, "checks_failed": 0},
        "results_sha256": "d" * 64,
        "results": [{"criterion": f"A-{n:02d}", "status": "PASS"} for n in range(1, items + 1)],
    }), encoding="utf-8")
    return path


def _manifest(runner: ModuleType, tmp_path: Path, *, drop: int = 0,
              tamper: bool = False) -> tuple[Path, str]:
    """Manifest of every Phase B surface file of this tree (optionally incomplete/tampered)."""

    import hashlib

    files = sorted({p.relative_to(REPO).as_posix() for pattern in runner.PHASE_B_SURFACE
                    for p in REPO.glob(pattern) if p.is_file()})[drop:]
    lines = [f"{hashlib.sha256((REPO / rel).read_bytes()).hexdigest()}  {rel}" for rel in files]
    if tamper:
        lines[0] = "0" * 64 + lines[0][64:]
    path = tmp_path / f"manifest_{len(list(tmp_path.iterdir()))}.sha256"
    path.write_bytes("".join(f"{line}\n" for line in lines).encode("utf-8"))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _run(runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *,
         b2_b6: list[tuple[str, str, str]] | None = None,
         phase_a: list[tuple[str, str, str]] | None = None,
         fixture: Path | None = None,
         manifest: tuple[Path, str | None] | None = None) -> tuple[int, dict[str, str]]:
    """main() without services, with complete passing evidence unless a part is overridden."""

    _clear_services(monkeypatch)
    manifest_path, pin = manifest or _manifest(runner, tmp_path)
    junit = _junit(
        tmp_path, b2_b6 if b2_b6 is not None else _suite_cases(runner, runner.SUITE_B2_B6))
    phase_a_junit = _junit(
        tmp_path, phase_a if phase_a is not None else _suite_cases(runner, runner.SUITE_PHASE_A))
    report_path = tmp_path / "report.json"
    argv = ["--report", str(report_path), "--junit", str(junit), "--phase-a-junit",
            str(phase_a_junit), "--fixture-report", str(fixture or _fixture(tmp_path)),
            "--manifest", str(manifest_path)] + (["--manifest-sha256", pin] if pin else [])
    code = runner.main(argv)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    statuses = {row["item"]: row["status"]
                for group in ("gates", "crash_matrix", "acceptance") for row in report[group]}
    return code, statuses


def test_complete_passing_evidence_passes_every_gate_but_not_the_run(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    code, statuses = _run(runner, tmp_path, monkeypatch)
    assert {statuses[g] for g in ("G-01", "G-02", "G-03", "G-04")} == {"PASS"}
    assert all(statuses[f"W{n:02d}"] == "PASS" for n in range(1, 13))
    assert statuses["B-01"] == "PASS" and statuses["B-11"] == "PASS"
    assert statuses["B-10"] == "NOT_RUN"  # durable scenarios did not run here
    assert code == 2  # required durable scenarios still NOT_RUN: no PASS without services


# ------------------------------------------- B6-CR01 regressions (closure review probes)
def test_a_failing_test_that_no_item_maps_fails_the_run(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unmapped = (f"{INTEGRATION_ID}/test_audit_durability.py",
                "test_rolled_back_round_and_foreign_lineage_produce_no_quarantine")
    cases = [(m, n, "FAIL" if (m, n) == unmapped else s)
             for m, n, s in _suite_cases(runner, runner.SUITE_B2_B6)]
    assert any(s == "FAIL" for _, _, s in cases)
    code, statuses = _run(runner, tmp_path, monkeypatch, b2_b6=cases)
    assert statuses["G-01"] == "FAIL" and code == 1


@pytest.mark.parametrize("change", ["drop", "skip"])
def test_missing_or_skipped_suite_tests_are_not_run_never_pass(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    cases = _suite_cases(runner, runner.SUITE_B2_B6)
    recovery = [c for c in cases if c[0] == f"{INTEGRATION_ID}/test_dispatch_recovery.py"][:3]
    assert len(recovery) == 3
    if change == "drop":  # e.g. a -k run or a suite that crashed half way
        cases = [c for c in cases if c not in recovery]
    else:
        cases = [(m, n, "SKIP" if (m, n, s) in recovery else s) for m, n, s in cases]
    code, statuses = _run(runner, tmp_path, monkeypatch, b2_b6=cases)
    assert statuses["G-01"] == "NOT_RUN" and statuses["B-04"] == "NOT_RUN"
    assert "FAIL" not in statuses.values() and code == 2


MIGRATIONS = f"{INTEGRATION_ID}/test_migrations.py"
OPAQUE = "test_contract_valid_opaque_ids_round_trip_all_five_columns"


def test_a_missing_parameter_variant_is_not_run_even_if_a_sibling_ran(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cases = _suite_cases(runner, runner.SUITE_B2_B6)
    dropped = (MIGRATIONS, f"{OPAQUE}[120]", "PASS")  # PostgreSQL case, real collection id
    assert dropped in cases and (MIGRATIONS, f"{OPAQUE}[81]", "PASS") in cases
    code, statuses = _run(runner, tmp_path, monkeypatch, b2_b6=[c for c in cases if c != dropped])
    assert statuses["G-01"] == "NOT_RUN" and statuses["B-11"] == "NOT_RUN"
    assert "FAIL" not in statuses.values() and code == 2


def test_a_missing_phase_a_parameter_variant_is_not_run(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cases = _suite_cases(runner, runner.SUITE_PHASE_A)
    variants: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for case in cases:
        if "[" in case[1]:
            variants.setdefault((case[0], case[1].split("[", 1)[0]), []).append(case)
    family = next(group for group in variants.values() if len(group) >= 2)
    dropped, sibling = family[-1], family[0]
    code, statuses = _run(runner, tmp_path, monkeypatch, phase_a=[c for c in cases if c != dropped])
    assert sibling[1] != dropped[1]
    assert statuses["G-02"] == "NOT_RUN" and statuses["B-11"] == "NOT_RUN"
    assert "FAIL" not in statuses.values() and code == 2


def test_a_failure_wins_over_a_missing_variant(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cases = _suite_cases(runner, runner.SUITE_B2_B6)
    failing = (f"{INTEGRATION_ID}/test_audit_durability.py",
               "test_rolled_back_round_and_foreign_lineage_produce_no_quarantine", "PASS")
    assert failing in cases
    cases = [(m, n, "FAIL") if (m, n, s) == failing else (m, n, s) for m, n, s in cases
             if (m, n) != (MIGRATIONS, f"{OPAQUE}[120]")]
    code, statuses = _run(runner, tmp_path, monkeypatch, b2_b6=cases)
    assert statuses["G-01"] == "FAIL" and code == 1


def test_collection_and_junit_identities_agree_and_keep_variants(runner: ModuleType) -> None:
    assert runner.nodeid_key("tests/unit/test_x.py::C::test_a[1-2]") == (
        "tests/unit/test_x.py", "C::test_a[1-2]")
    assert runner.junit_key("tests.unit.test_x.C", "test_a[1-2]") == (
        "tests/unit/test_x.py", "C::test_a[1-2]")
    assert runner.junit_key("tests.unit.test_x", "test_a[3]") != runner.junit_key(
        "tests.unit.test_x", "test_a[4]")
    assert runner.nodeid_key("3 tests collected in 0.1s") is None


def test_an_incomplete_collection_is_never_a_partial_inventory(
    runner: ModuleType, tmp_path: Path
) -> None:
    assert runner.suite_inventory(("backend/tests/unit/test_absent_*.py",))[0] == {}
    broken = tmp_path / "backend" / "tests" / "unit" / "test_broken_collection.py"
    broken.parent.mkdir(parents=True)
    (tmp_path / "backend" / "pyproject.toml").write_text("[tool.pytest.ini_options]\n",
                                                        encoding="utf-8")
    broken.write_text("def test_ok():\n    pass\n\nraise ImportError('collection fails')\n",
                      encoding="utf-8")
    inventory, detail = runner.suite_inventory(("backend/tests/unit/test_*.py",), tmp_path)
    assert inventory == {} and "collection exit" in detail
    gate = runner.suite_gate("G-01", "x", [], True, (inventory, detail), "test")
    assert gate.status == "FAIL"


def test_a_case_outside_the_suite_inventory_fails(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cases = [*_suite_cases(runner, runner.SUITE_B2_B6), ("test_foreign", "test_other", "PASS")]
    code, statuses = _run(runner, tmp_path, monkeypatch, b2_b6=cases)
    assert statuses["G-01"] == "FAIL" and code == 1


def test_an_arbitrary_phase_a_junit_is_not_phase_a_evidence(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    code, statuses = _run(runner, tmp_path, monkeypatch,
                          phase_a=[("test_ai_job_application", "test_x", "PASS")])
    assert statuses["G-02"] == "FAIL"  # test_x is outside the Phase A inventory
    assert statuses["B-11"] == "FAIL" and code == 1
    one = _suite_cases(runner, runner.SUITE_PHASE_A)[:1]
    code, statuses = _run(runner, tmp_path, monkeypatch, phase_a=one)
    assert statuses["G-02"] == "NOT_RUN" and statuses["B-11"] == "NOT_RUN" and code == 2


@pytest.mark.parametrize("kind", ["zero_checks", "missing_items", "unreadable"])
def test_an_incomplete_fixture_report_fails(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    if kind == "unreadable":
        fixture = tmp_path / "fixture_bad.json"
        fixture.write_text(json.dumps({"summary": {"PASS": 20, "FAIL": 0, "checks": 215,
                                                   "checks_failed": 0}}), encoding="utf-8")
    else:
        fixture = _fixture(tmp_path, checks=0 if kind == "zero_checks" else 215,
                           items=19 if kind == "missing_items" else 20)
    code, statuses = _run(runner, tmp_path, monkeypatch, fixture=fixture)
    assert statuses["G-03"] == "FAIL" and statuses["B-11"] == "FAIL" and code == 1


def test_manifest_gate_needs_a_pinned_complete_matching_manifest(
    runner: ModuleType, tmp_path: Path
) -> None:
    gate = runner.manifest_gate
    good, pin = _manifest(runner, tmp_path)
    assert gate(good, pin).status == "PASS"
    assert gate(None, None).status == "NOT_RUN"
    assert gate(good, None).status == "FAIL"  # not pinned
    assert gate(good, "0" * 64).status == "FAIL"  # pin mismatch
    empty = tmp_path / "empty.sha256"
    empty.write_bytes(b"")
    assert gate(empty, runner.hashlib.sha256(b"").hexdigest()).status == "FAIL"
    assert gate(*_manifest(runner, tmp_path, drop=1)).status == "FAIL"  # surface file unlisted
    assert gate(*_manifest(runner, tmp_path, tamper=True)).status == "FAIL"  # hash mismatch
    broken = tmp_path / "broken.sha256"
    broken.write_bytes(good.read_bytes() + b"not a manifest line\n")
    assert gate(broken, runner.hashlib.sha256(broken.read_bytes()).hexdigest()).status == "FAIL"


def test_an_empty_or_unpinned_manifest_fails_the_run(
    runner: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty.sha256"
    empty.write_bytes(b"")
    code, statuses = _run(runner, tmp_path, monkeypatch, manifest=(empty, None))
    assert statuses["G-04"] == "FAIL" and code == 1
