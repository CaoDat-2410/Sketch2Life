"""Local pack exact evidence/environment safety, not actual SQL activation."""

import importlib.util
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

PATH = (
    Path(__file__).resolve().parents[3]
    / "features/FEAT-054-be2-preset-automation/src/run_component_checks.py"
)
NODE = "tests/unit/test_preset_automation_domain.py::test_fixture"


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location("preset_runner", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("pass", ("PASS", 0)),
        ("skip", ("NOT_RUN", 2)),
        ("missing", ("NOT_RUN", 2)),
        ("failure", ("FAIL", 1)),
        ("error", ("FAIL", 1)),
        ("duplicate", ("FAIL", 1)),
        ("extra", ("FAIL", 1)),
        ("nonzero", ("FAIL", 1)),
    ],
)
def test_exact_case_outcome_not_counts_or_exit_zero(runner, tmp_path, mode, expected):
    path = tmp_path / "junit.xml"
    if mode != "missing":
        root = ET.Element("testsuite", tests="1")
        row = ET.SubElement(
            root,
            "testcase",
            classname="tests.unit.test_preset_automation_domain",
            name="test_fixture",
        )
        if mode in {"skip", "failure", "error"}:
            ET.SubElement(row, "skipped" if mode == "skip" else mode)
        if mode in {"extra", "duplicate"}:
            ET.SubElement(
                root,
                "testcase",
                classname="tests.unit.test_preset_automation_domain",
                name="test_fixture" if mode == "duplicate" else "extra",
            )
            root.set("tests", "2")
        ET.ElementTree(root).write(path, encoding="unicode")
    assert runner.evidence().helpers().classify((NODE,), path, int(mode == "nonzero")) == expected


@pytest.mark.parametrize("mode", ["empty", "duplicate", "changed", "bool-count"])
def test_pinned_nodes_fail_closed(runner, mode):
    support = runner.evidence()
    nodes = (NODE,)
    pin = {"cases": 1, "node_sha256": support.helpers().node_digest(nodes)}
    assert support.valid_pin(nodes, pin)
    if mode == "empty":
        nodes = ()
    elif mode == "duplicate":
        nodes = (NODE, NODE)
    elif mode == "changed":
        nodes = (NODE + "[changed]",)
    else:
        pin["cases"] = True
    assert not support.valid_pin(nodes, pin)


def test_source_closure_includes_catalog_assets_and_no_sql_execution_groups(runner):
    selected = runner.groups()
    assert not set(selected["owned"]) & set(selected["regression"])
    assert selected["sql_collection_only"] == runner.SQL
    assert len(runner.owned_sources()) == 11
    hashes = runner.source_hashes()
    assert any(key.startswith("data/activity-catalog/") and key.endswith(".json") for key in hashes)
    assert "backend/tests/preset_automation_fixtures.py" in hashes
    assert "backend/src/sketch2life/interfaces/http/routers/video_review.py" in hashes
    assert not any("evidence/" in key for key in hashes)


def test_process_strips_all_sql_optins_and_safe_failure(runner, monkeypatch, tmp_path):
    monkeypatch.setenv("PA13_TEST_ALLOW_SCHEMA_DDL", "1")
    monkeypatch.setenv("PA13_TEST_DATABASE_URL", "synthetic_sensitive")

    def fake(args, **kwargs):
        assert "PA13_TEST_ALLOW_SCHEMA_DDL" not in kwargs["env"]
        assert "PA13_TEST_DATABASE_URL" not in kwargs["env"]
        assert kwargs["timeout"] == 300 and kwargs["check"] is False
        return SimpleNamespace(returncode=0, stdout="safe", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake)
    assert runner.run(["fixture"], tmp_path, tmp_path / "log") == (0, "safe")

    def fail(*args, **kwargs):
        raise subprocess.TimeoutExpired("synthetic_sensitive", 300)

    monkeypatch.setattr(runner.subprocess, "run", fail)
    assert runner.run(["fixture"], tmp_path, tmp_path / "log") == (124, "")
    assert "synthetic_sensitive" not in (tmp_path / "log").read_text()


@pytest.mark.parametrize("mode", ["pass", "skip", "changed-source", "bad-pin"])
def test_main_sql_only_collects_no_partial_or_drift_pass(runner, monkeypatch, tmp_path, mode):
    feature = tmp_path / "features/FEAT-054-be2-preset-automation"
    (feature / "src").mkdir(parents=True)
    (feature / "approvals").mkdir()
    (feature / "approvals/TASK_APPROVAL.md").write_text("- Status: APPROVED")
    support = runner.evidence()
    selected = {
        "owned": (NODE,),
        "regression": ("tests/unit/test_video_failure_domain.py::test_x",),
        "sql_collection_only": (runner.SQL[0] + "::test_x",),
    }
    pins = {
        name: {"cases": len(nodes), "node_sha256": support.helpers().node_digest(nodes)}
        for name, nodes in selected.items()
    }
    if mode == "bad-pin":
        pins["owned"]["node_sha256"] = "f" * 64
    (feature / "src/TEST_INVENTORY.json").write_text(json.dumps(pins))
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "FEATURE", feature)
    monkeypatch.setattr(runner, "evidence", lambda: support)
    monkeypatch.setattr(runner, "groups", lambda: {key: (key,) for key in selected})
    monkeypatch.setattr(runner, "owned_sources", lambda: ())
    snapshots = [{"features/FEAT-054-be2-preset-automation/plan/PLAN.md": runner.PLAN_SHA256}]
    monkeypatch.setattr(runner, "source_hashes", lambda: dict(snapshots[-1]))

    def fake(args, cwd, log):
        if "pytest" in args:
            name = next(key for key in selected if key in args)
            nodes = selected[name]
            if "--collect-only" in args:
                return 0, "\n".join(nodes)
            assert name != "sql_collection_only"
            junit = Path(
                next(arg.split("=", 1)[1] for arg in args if arg.startswith("--junitxml="))
            )
            root = ET.Element("testsuite", tests="1")
            path, case = nodes[0].split("::", 1)
            row = ET.SubElement(root, "testcase", classname=path[:-3].replace("/", "."), name=case)
            if mode == "skip":
                ET.SubElement(row, "skipped")
            ET.ElementTree(root).write(junit, encoding="unicode")
        if mode == "changed-source":
            snapshots.append({"changed.py": "changed"})
        return 0, ""

    monkeypatch.setattr(runner, "run", fake)
    assert runner.main() == (0 if mode == "pass" else 1)
    summary = json.loads(next((tmp_path / ".runtime").rglob("summary.json")).read_text())
    assert summary["postgresql"] == "NOT_RUN" and not summary["full_card_complete"]
