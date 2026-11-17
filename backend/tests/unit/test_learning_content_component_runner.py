"""Runner evidence classification, not a replacement for actual component/runtime checks."""

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "features/FEAT-048-be2-content-publication/src/run_component_checks.py"


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location("lc_component_runner", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("mode,expected", [
    ("pass", ("PASS", 0)), ("fail", ("FAIL", 1)), ("error", ("FAIL", 1)),
    ("skip", ("NOT_RUN", 2)), ("missing", ("NOT_RUN", 2)),
    ("duplicate", ("FAIL", 1)), ("extra", ("FAIL", 1)),
    ("wrong_classname", ("FAIL", 1)), ("malformed", ("FAIL", 1)),
    ("nonzero", ("FAIL", 1)), ("no_report", ("NOT_RUN", 2)),
])
def test_actual_case_identity_and_outcomes_are_required(runner, tmp_path, mode, expected):
    nodes = ("tests/unit/test_synthetic.py::test_first",
             "tests/unit/test_synthetic.py::test_second")
    path = tmp_path / "junit.xml"
    root = ET.Element("testsuites")
    suite = ET.SubElement(root, "testsuite")
    for name in ("test_first", "test_second"):
        if mode == "missing" and name == "test_second":
            continue
        case = ET.SubElement(suite, "testcase", classname="tests.unit.test_synthetic", name=name)
        if name == "test_first":
            child = {"fail": "failure", "error": "error", "skip": "skipped"}.get(mode)
            if child:
                ET.SubElement(case, child)
    if mode in {"duplicate", "extra", "wrong_classname"}:
        ET.SubElement(suite, "testcase",
                      classname="tests.unit.wrong" if mode == "wrong_classname"
                      else "tests.unit.test_synthetic",
                      name="test_first" if mode == "duplicate" else "test_unexpected")
    if mode != "no_report":
        ET.ElementTree(root).write(path, encoding="utf-8")
    if mode == "malformed":
        path.write_text("<broken", encoding="utf-8")
    assert runner.classify(nodes, path, 1 if mode == "nonzero" else 0) == expected


@pytest.mark.parametrize("mode,valid", [("complete", True), ("missing", False),
                                       ("duplicate", False), ("extra", False)])
def test_collection_inventory_is_exact(runner, monkeypatch, mode, valid):
    monkeypatch.setattr(runner, "SUITES", {"tests/unit/test_synthetic.py": 2})
    nodes = ("tests/unit/test_synthetic.py::test_first",
             "tests/unit/test_synthetic.py::test_second")
    if mode == "missing":
        nodes = nodes[:1]
    elif mode == "duplicate":
        nodes = (nodes[0], nodes[0])
    elif mode == "extra":
        nodes = (*nodes, "tests/unit/test_unexpected.py::test_extra")
    output = "\n".join(nodes)
    assert runner.inventory(output) == nodes
    assert runner.valid_inventory(nodes) is valid


def test_source_manifest_includes_runner_fixtures_and_imported_production_source(runner):
    hashes = runner.source_hashes()
    assert RUNNER.relative_to(ROOT).as_posix() in hashes
    assert "backend/tests/learning_content_fixtures.py" in hashes
    assert "backend/src/sketch2life/application/governance_dispatcher.py" in hashes
    assert "backend/src/sketch2life/contracts/schemas/ai_contract_candidates.py" in hashes
    assert all(len(value) == 64 for value in hashes.values())
    assert sum(runner.SUITES[name] for name in runner.FOUNDATION_SUITES) == 110
    assert all("learning_content" not in name for name in runner.FOUNDATION_SUITES)
