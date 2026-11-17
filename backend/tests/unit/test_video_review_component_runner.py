"""One-batch runner safety; never opt in SQL or execute providers."""

import importlib.util
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

PATH = Path(__file__).resolve().parents[3] / (
    "features/FEAT-051-be2-video-review-playback/src/run_component_checks.py"
)
NODE = "tests/unit/test_video_review_domain.py::test_fixture"


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location("video_review_runner", PATH)
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
def test_exact_junit_identity_and_outcome_not_exit_zero_only(runner, tmp_path, mode, expected):
    path = tmp_path / "result.xml"
    if mode != "missing":
        suite = ET.Element("testsuite", tests="1")
        case = ET.SubElement(
            suite, "testcase", classname="tests.unit.test_video_review_domain", name="test_fixture"
        )
        if mode in {"skip", "failure", "error"}:
            ET.SubElement(case, "skipped" if mode == "skip" else mode)
        if mode in {"duplicate", "extra"}:
            ET.SubElement(
                suite,
                "testcase",
                classname="tests.unit.test_video_review_domain",
                name="test_fixture" if mode == "duplicate" else "test_extra",
            )
            suite.set("tests", "2")
        ET.ElementTree(suite).write(path, encoding="unicode")
        if mode == "invalid":
            path.write_text("<broken", encoding="utf-8")
    assert runner.helpers().helpers().classify((NODE,), path, int(mode == "nonzero")) == expected


@pytest.mark.parametrize("mode", ["empty", "duplicate", "wrong-count", "changed", "bool-count"])
def test_collection_pin_fail_closed(runner, mode):
    support = runner.helpers()
    nodes = (NODE,)
    pin = {"cases": 1, "node_sha256": support.helpers().node_digest(nodes)}
    assert support.valid_pin(nodes, pin)
    if mode == "empty":
        nodes = ()
    elif mode == "duplicate":
        nodes = (NODE, NODE)
    elif mode == "wrong-count":
        pin["cases"] = 2
    elif mode == "changed":
        nodes = (NODE + "[changed]",)
    else:
        pin["cases"] = True
    assert not support.valid_pin(nodes, pin)


def test_coverage_closure_and_disjoint_collections(runner):
    owned = runner.suites(("test_video_review_", "test_video_playback"))
    assert "tests/contract/test_video_review_http.py" in owned
    assert "tests/unit/test_video_review_component_runner.py" in owned
    assert not set(owned) & set(runner.SQL)
    assert len(runner.owned_sources()) == 17
    hashes = runner.source_hashes()
    for name in (
        "backend/src/sketch2life/contracts/schemas/ai_contract_candidates.py",
        "backend/tests/unit/test_knowledge_video_worker.py",
        "features/FEAT-050-be2-knowledge-video/src/run_component_checks.py",
        "features/FEAT-051-be2-video-review-playback/src/TEST_INVENTORY.json",
        "features/FEAT-051-be2-video-review-playback/approvals/TASK_APPROVAL.md",
    ):
        assert len(hashes[name]) == 64
    assert not any("evidence/" in name for name in hashes)


def test_subprocess_drops_sql_optins_without_exposing_environment(runner, monkeypatch, tmp_path):
    for name in (
        "VR09_TEST_ALLOW_SCHEMA_DDL",
        "VR09_TEST_DATABASE_URL",
        "KV08_TEST_ALLOW_SCHEMA_DDL",
        "KV08_TEST_DATABASE_URL",
    ):
        monkeypatch.setenv(name, "synthetic_sensitive")

    def fake(command, **options):
        assert not any(name.startswith(("VR09_TEST_", "KV08_TEST_")) for name in options["env"])
        assert options["timeout"] == 300 and options["check"] is False
        return SimpleNamespace(returncode=0, stdout="safe", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake)
    assert runner.run(["fixture"], tmp_path, tmp_path / "process.log") == (0, "safe")
    assert "synthetic_sensitive" not in (tmp_path / "process.log").read_text()


@pytest.mark.parametrize(
    "error", [OSError("synthetic_sensitive"), subprocess.TimeoutExpired("synthetic_sensitive", 300)]
)
def test_process_errors_fail_closed(runner, monkeypatch, tmp_path, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(runner.subprocess, "run", fail)
    assert runner.run(["fixture"], tmp_path, tmp_path / "process.log") == (124, "")
    assert "synthetic_sensitive" not in (tmp_path / "process.log").read_text()


@pytest.mark.parametrize("mode", ["pass", "skip", "changed-source", "wrong-pin"])
def test_main_sql_only_collects_and_partial_run_not_pass(runner, monkeypatch, tmp_path, mode):
    feature = tmp_path / "features/FEAT-051-be2-video-review-playback"
    (feature / "src").mkdir(parents=True)
    (feature / "approvals").mkdir()
    (feature / "approvals/TASK_APPROVAL.md").write_text("- Status: APPROVED")
    support = runner.helpers()
    groups = {
        "owned": (NODE,),
        "regression": ("tests/unit/test_knowledge_video_domain.py::test_x",),
        "sql_collection_only": (runner.SQL[0] + "::test_sql",),
    }
    pins = {
        name: {"cases": len(nodes), "node_sha256": support.helpers().node_digest(nodes)}
        for name, nodes in groups.items()
    }
    if mode == "wrong-pin":
        pins["owned"]["node_sha256"] = "f" * 64
    (feature / "src/TEST_INVENTORY.json").write_text(json.dumps(pins))
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "FEATURE", feature)
    monkeypatch.setattr(runner, "helpers", lambda: support)
    monkeypatch.setattr(
        runner,
        "suites",
        lambda prefixes: ("owned",) if prefixes[0] == "test_video_review_" else ("regression",),
    )
    snapshots = [{"features/FEAT-051-be2-video-review-playback/plan/PLAN.md": runner.PLAN_SHA256}]
    monkeypatch.setattr(runner, "source_hashes", lambda: dict(snapshots[-1]))
    monkeypatch.setattr(runner, "owned_sources", lambda: ())

    def fake(command, cwd, log):
        if "-m" in command and "pytest" in command:
            name = (
                "sql_collection_only"
                if runner.SQL[0] in command
                else ("owned" if "owned" in command else "regression")
            )
            nodes = groups[name]
            if "--collect-only" in command:
                return 0, "\n".join(nodes)
            assert name != "sql_collection_only", "SQL execution forbidden"
            path = Path(
                next(arg.split("=", 1)[1] for arg in command if arg.startswith("--junitxml="))
            )
            suite = ET.Element("testsuite", tests="1")
            file, case = nodes[0].split("::", 1)
            row = ET.SubElement(suite, "testcase", classname=file[:-3].replace("/", "."), name=case)
            if mode == "skip":
                ET.SubElement(row, "skipped")
            ET.ElementTree(suite).write(path, encoding="unicode")
        if mode == "changed-source":
            snapshots.append({"new_source.py": "changed"})
        return 0, ""

    monkeypatch.setattr(runner, "run", fake)
    assert runner.main() == (0 if mode == "pass" else 1)
    summary = json.loads(next((tmp_path / ".runtime").rglob("summary.json")).read_text())
    assert summary["postgresql"] == "NOT_RUN" and not summary["full_card_complete"]
