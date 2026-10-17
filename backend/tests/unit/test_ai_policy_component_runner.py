"""Consolidated local proof validator; never executes providers or PostgreSQL."""

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


@pytest.fixture
def runner():
    path = (
        Path(__file__).resolve().parents[3]
        / "features/FEAT-049-be2-ai-policy/src/run_component_checks.py"
    )
    spec = importlib.util.spec_from_file_location("policy_component_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NODE = "tests/unit/test_ai_policy_domain.py::test_fixture"


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("pass", ("PASS", 0)),
        ("missing", ("NOT_RUN", 2)),
        ("invalid", ("FAIL", 1)),
        ("nonzero", ("FAIL", 1)),
        ("failure", ("FAIL", 1)),
        ("error", ("FAIL", 1)),
        ("skip", ("NOT_RUN", 2)),
        ("missing-case", ("NOT_RUN", 2)),
        ("duplicate", ("FAIL", 1)),
        ("extra", ("FAIL", 1)),
        ("declared-failure", ("FAIL", 1)),
        ("declared-skip", ("NOT_RUN", 2)),
        ("bad-count", ("FAIL", 1)),
    ],
)
def test_junit_outcomes_fail_closed(runner, tmp_path, mode, expected):
    path = tmp_path / "junit.xml"
    if mode == "invalid":
        path.write_text("<broken", encoding="utf-8")
    elif mode != "missing":
        suite = ET.Element("testsuite", failures="0", errors="0", skipped="0")
        if mode != "missing-case":
            case = ET.SubElement(
                suite, "testcase", classname="tests.unit.test_ai_policy_domain", name="test_fixture"
            )
            if mode in {"failure", "error", "skip"}:
                ET.SubElement(case, "skipped" if mode == "skip" else mode)
        if mode in {"duplicate", "extra"}:
            ET.SubElement(
                suite,
                "testcase",
                classname="tests.unit.test_ai_policy_domain",
                name="test_fixture" if mode == "duplicate" else "extra",
            )
        if mode.startswith("declared-"):
            suite.set("failures" if mode == "declared-failure" else "skipped", "1")
        if mode == "bad-count":
            suite.set("failures", "invalid")
        suite.set("tests", str(len(list(suite.iter("testcase")))))
        ET.ElementTree(suite).write(path, encoding="unicode")
    assert runner.classify((NODE,), path, 1 if mode == "nonzero" else 0) == expected


def test_exact_node_digest_not_just_count_or_order(runner):
    nodes = (NODE, NODE + "[fixture]")
    digest = runner.node_digest(nodes)
    assert runner.valid_inventory(nodes[::-1], 2, digest)
    for candidate in ((), nodes[:-1], (NODE, NODE), (NODE, NODE + "changed")):
        assert not runner.valid_inventory(candidate, 2, digest)
    assert not runner.valid_inventory(nodes, 3, digest)


def test_collection_normalization_and_source_closure(runner):
    assert runner.inventory(
        "warning\ntests\\unit\\test_ai_policy_domain.py::test_fixture\n1 test collected"
    ) == (NODE,)
    paths = runner.source_hashes()
    for name in (
        "backend/tests/unit/test_ai_policy_copy_report.py",
        "backend/tests/ai_policy_copy_inventory_fixtures.py",
        "backend/src/sketch2life/interfaces/http/routers/learning_content.py",
        "backend/alembic/versions/20261018_ap_0009_copy_resolution.py",
        "features/FEAT-049-be2-ai-policy/approvals/TASK_APPROVAL.md",
        "features/FEAT-049-be2-ai-policy/src/run_component_checks.py",
    ):
        assert name in paths and len(paths[name]) == 64
    assert len(runner.owned_sources()) == 61


@pytest.mark.parametrize("mode", ["empty-selection", "wrong-root", "wrong-total"])
def test_vacuous_or_inconsistent_junit_cannot_pass(runner, tmp_path, mode):
    root = ET.Element("unknown" if mode == "wrong-root" else "testsuite", tests="0")
    if mode != "empty-selection":
        ET.SubElement(
            root, "testcase", classname="tests.unit.test_ai_policy_domain", name="test_fixture"
        )
    path = tmp_path / "junit.xml"
    ET.ElementTree(root).write(path, encoding="unicode")
    assert runner.classify(() if mode == "empty-selection" else (NODE,), path, 0) == ("FAIL", 1)
