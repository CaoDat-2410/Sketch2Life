"""Evidence classifier/inventory/process safety, never actual SQL activation."""

import importlib.util
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

PATH = Path(__file__).resolve().parents[3] / (
    "features/FEAT-052-be2-video-failure-disposition/src/run_component_checks.py"
)
NODE = "tests/unit/test_video_failure_domain.py::test_fixture"


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location("failure_runner", PATH)
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
        ("invalid", ("FAIL", 1)),
        ("nonzero", ("FAIL", 1)),
    ],
)
def test_exact_case_junit_outcome_not_just_exit_or_count(runner, tmp_path, mode, expected):
    path = tmp_path / "junit.xml"
    if mode != "missing":
        root = ET.Element("testsuite", tests="1")
        case = ET.SubElement(
            root, "testcase", classname="tests.unit.test_video_failure_domain", name="test_fixture"
        )
        if mode in {"skip", "failure", "error"}:
            ET.SubElement(case, "skipped" if mode == "skip" else mode)
        if mode in {"duplicate", "extra"}:
            ET.SubElement(
                root,
                "testcase",
                classname="tests.unit.test_video_failure_domain",
                name="test_fixture" if mode == "duplicate" else "test_extra",
            )
            root.set("tests", "2")
        ET.ElementTree(root).write(path, encoding="unicode")
        if mode == "invalid":
            path.write_text("<broken", encoding="utf-8")
    assert (
        runner.helpers().helpers().helpers().classify((NODE,), path, int(mode == "nonzero"))
        == expected
    )


@pytest.mark.parametrize("mode", ["empty", "duplicate", "changed", "wrong-count", "bool-count"])
def test_inventory_pin_fail_closed(runner, mode):
    support = runner.helpers().helpers()
    nodes = (NODE,)
    pin = {"cases": 1, "node_sha256": support.helpers().node_digest(nodes)}
    assert support.valid_pin(nodes, pin)
    if mode == "empty":
        nodes = ()
    elif mode == "duplicate":
        nodes = (NODE, NODE)
    elif mode == "changed":
        nodes = (NODE + "[different]",)
    else:
        pin["cases"] = True if mode == "bool-count" else 2
    assert not support.valid_pin(nodes, pin)


def test_source_closure_and_sql_collection_separate(runner):
    selected = runner.groups()
    assert not set(selected["owned"]) & set(selected["regression"])
    assert selected["sql_collection_only"] == runner.SQL
    assert len(runner.owned_sources()) == 10
    hashes = runner.source_hashes()
    for name in (
        "backend/tests/video_failure_fixtures.py",
        "backend/src/sketch2life/interfaces/http/routers/video_review.py",
        "backend/alembic/versions/20261019_vf_0001_video_failure.py",
        "features/FEAT-052-be2-video-failure-disposition/approvals/TASK_APPROVAL.md",
        "features/FEAT-052-be2-video-failure-disposition/src/TEST_INVENTORY.json",
    ):
        assert len(hashes[name]) == 64
    assert not any("evidence/" in key for key in hashes)


def test_process_cannot_inherit_sql_activation(runner, monkeypatch, tmp_path):
    for name in (
        "VF10_TEST_ALLOW_SCHEMA_DDL",
        "VF10_TEST_DATABASE_URL",
        "VR09_TEST_ALLOW_SCHEMA_DDL",
        "KV08_TEST_DATABASE_URL",
    ):
        monkeypatch.setenv(name, "synthetic_sensitive")

    def fake(command, **kwargs):
        assert kwargs["check"] is False and kwargs["timeout"] == 300
        assert not any(
            k.endswith(("_TEST_ALLOW_SCHEMA_DDL", "_TEST_DATABASE_URL")) for k in kwargs["env"]
        )
        return SimpleNamespace(returncode=0, stdout="safe", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake)
    assert runner.run(["fixture"], tmp_path, tmp_path / "log") == (0, "safe")


@pytest.mark.parametrize("exc", [OSError("private"), subprocess.TimeoutExpired("private", 300)])
def test_process_failure_never_success_or_diagnostic_echo(runner, monkeypatch, tmp_path, exc):
    def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr(runner.subprocess, "run", fail)
    assert runner.run(["fixture"], tmp_path, tmp_path / "log") == (124, "")
    assert "private" not in (tmp_path / "log").read_text()


@pytest.mark.parametrize("mode", ["pass", "skip", "changed-source", "bad-pin"])
def test_whole_pack_never_executes_sql_or_accepts_partial_receipt(
    runner, monkeypatch, tmp_path, mode
):
    feature = tmp_path / "features/FEAT-052-be2-video-failure-disposition"
    (feature / "src").mkdir(parents=True)
    (feature / "approvals").mkdir()
    (feature / "approvals/TASK_APPROVAL.md").write_text("- Status: APPROVED")
    selected = {
        "owned": (NODE,),
        "regression": ("tests/unit/test_video_review_domain.py::test_fixture",),
        "sql_collection_only": (runner.SQL[0] + "::test_sql",),
    }
    helper_module = runner.helpers()
    support = helper_module.helpers()
    monkeypatch.setattr(runner, "helpers", lambda: helper_module)
    pins = {
        name: {"cases": len(nodes), "node_sha256": support.helpers().node_digest(nodes)}
        for name, nodes in selected.items()
    }
    if mode == "bad-pin":
        pins["owned"]["node_sha256"] = "f" * 64
    (feature / "src/TEST_INVENTORY.json").write_text(json.dumps(pins))
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "FEATURE", feature)
    monkeypatch.setattr(runner, "groups", lambda: {k: (k,) for k in selected})
    monkeypatch.setattr(runner, "owned_sources", lambda: ())
    snapshots = [
        {"features/FEAT-052-be2-video-failure-disposition/plan/PLAN.md": runner.PLAN_SHA256}
    ]
    monkeypatch.setattr(runner, "source_hashes", lambda: dict(snapshots[-1]))

    def fake(command, cwd, log):
        if "pytest" in command:
            name = next(name for name in selected if name in command)
            nodes = selected[name]
            if "--collect-only" in command:
                return 0, "\n".join(nodes)
            assert name != "sql_collection_only"
            junit = Path(
                next(arg.split("=", 1)[1] for arg in command if arg.startswith("--junitxml="))
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
