"""Receipt classification, not a substitute for actual SQL execution."""

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[3] / (
    "features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py")


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location("ai_policy_c2_runner", PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("mode,expected", [
    ("pass", ("PASS", 0)), ("failure", ("FAIL", 1)), ("error", ("FAIL", 1)),
    ("skipped", ("NOT_RUN", 2)), ("missing", ("NOT_RUN", 2)),
    ("duplicate", ("FAIL", 1)), ("extra", ("FAIL", 1)), ("nonzero", ("FAIL", 1)),
])
def test_exact_cases_and_outcomes_required(runner, tmp_path, mode, expected):
    nodes = (runner.SUITE + "::test_first", runner.SUITE + "::test_second")
    path = tmp_path / "junit.xml"
    root = ET.Element("testsuites")
    suite = ET.SubElement(root, "testsuite")
    for name in ("test_first", "test_second"):
        if mode == "missing" and name == "test_second":
            continue
        case = ET.SubElement(suite, "testcase",
                              classname="tests.integration.ai_policy.test_policy_sql", name=name)
        if name == "test_first" and mode in {"failure", "error", "skipped"}:
            ET.SubElement(case, mode)
    if mode in {"duplicate", "extra"}:
        ET.SubElement(suite, "testcase", classname="tests.integration.ai_policy.test_policy_sql",
                      name="test_first" if mode == "duplicate" else "test_extra")
    ET.ElementTree(root).write(path, encoding="utf-8")
    assert runner.classify(nodes, path, 1 if mode == "nonzero" else 0) == expected


def test_runner_requires_card_specific_explicit_opt_in(runner, monkeypatch):
    monkeypatch.delenv("AP_TEST_ALLOW_CREATE", raising=False)
    monkeypatch.delenv("AP_TEST_PG_HOST", raising=False)
    monkeypatch.setenv("LC_TEST_ALLOW_CREATE", "1")
    assert runner.main() == 2


def test_runner_inventory_and_transitive_source_pin(runner):
    assert sum(runner.EXPECTED.values()) == 15
    nodes = tuple(runner.SUITE + "::" + name + (f"[{index}]" if count > 1 else "")
                  for name, count in runner.EXPECTED.items() for index in range(count))
    assert runner.valid_inventory(nodes)
    assert not runner.valid_inventory(nodes[:-1])
    assert not runner.valid_inventory((*nodes, nodes[0]))
    hashes = runner.source_hashes()
    assert "backend/tests/unit/test_ai_policy_domain.py" in hashes
    assert "backend/src/sketch2life/infrastructure/ai_policy/sql.py" in hashes
    assert "backend/alembic/versions/20261017_ap_0001_policy_lifecycle.py" in hashes


def test_activation_inventory_is_separate_and_pins_its_test_dependencies(runner):
    nodes = tuple(runner.ACTIVATION_SUITE + "::" + name for name in runner.ACTIVATION_EXPECTED)
    assert len(nodes) == 10
    assert runner.inventory("\n".join(nodes), runner.ACTIVATION_SUITE) == nodes
    assert runner.valid_inventory(nodes, runner.ACTIVATION_EXPECTED)
    assert not runner.valid_inventory(nodes)
    hashes = runner.source_hashes()
    assert "backend/tests/ai_policy_fixtures.py" in hashes
    assert "backend/tests/unit/test_ai_policy_compatibility.py" in hashes
    assert "backend/tests/unit/test_ai_policy_use.py" in hashes
    assert "backend/alembic/versions/20261017_ap_0002_effective_scope.py" in hashes


def test_accounting_inventory_and_source_are_separate_from_older_sql_packs(runner):
    nodes = tuple(runner.ACCOUNTING_SUITE + "::" + name + (f"[{i}]" if count > 1 else "")
                  for name, count in runner.ACCOUNTING_EXPECTED.items() for i in range(count))
    assert len(nodes) == 17
    assert runner.inventory("\n".join(nodes), runner.ACCOUNTING_SUITE) == nodes
    assert runner.valid_inventory(nodes, runner.ACCOUNTING_EXPECTED)
    assert not runner.valid_inventory(nodes[:-1], runner.ACCOUNTING_EXPECTED)
    assert not runner.valid_inventory(nodes, runner.ACTIVATION_EXPECTED)
    hashes = runner.source_hashes()
    assert "backend/tests/integration/ai_policy/test_accounting_sql.py" in hashes
    assert "backend/src/sketch2life/infrastructure/ai_policy/accounting_sql.py" in hashes
    assert "backend/alembic/versions/20261017_ap_0003_resource_ledger.py" in hashes


def test_accounting_runner_also_requires_explicit_card_opt_in(runner, monkeypatch):
    monkeypatch.delenv("AP_TEST_ALLOW_CREATE", raising=False)
    monkeypatch.delenv("AP_TEST_PG_HOST", raising=False)
    assert runner.main(accounting=True) == 2
    with pytest.raises(ValueError, match="exactly one"):
        runner.main(activation=True, accounting=True)
