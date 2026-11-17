"""Runner safety/classification checks; never activate DB/provider/runtime."""

import importlib.util
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def runner():
    path = Path(__file__).resolve().parents[3] / (
        "features/FEAT-050-be2-knowledge-video/src/run_component_checks.py"
    )
    spec = importlib.util.spec_from_file_location("kv08_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NODE = "tests/unit/test_knowledge_video_domain.py::test_fixture"


def test_windows_paths_normalized_without_changing_escaped_parameter_bytes(runner):
    output = r"tests\unit\test_fixture.py::test_bytes[\xff]"
    assert runner.inventory(output) == (r"tests/unit/test_fixture.py::test_bytes[\xff]",)


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
def test_exact_junit_not_exit_zero_or_test_count_only(runner, tmp_path, mode, expected):
    path = tmp_path / "junit.xml"
    if mode != "missing":
        suite = ET.Element("testsuite", tests="1")
        case = ET.SubElement(
            suite,
            "testcase",
            classname="tests.unit.test_knowledge_video_domain",
            name="test_fixture",
        )
        if mode in {"skip", "failure", "error"}:
            ET.SubElement(case, "skipped" if mode == "skip" else mode)
        if mode in {"duplicate", "extra"}:
            ET.SubElement(
                suite,
                "testcase",
                classname="tests.unit.test_knowledge_video_domain",
                name="test_fixture" if mode == "duplicate" else "extra",
            )
            suite.set("tests", "2")
        ET.ElementTree(suite).write(path, encoding="unicode")
        if mode == "invalid":
            path.write_text("<broken", encoding="utf-8")
    assert runner.helpers().classify((NODE,), path, int(mode == "nonzero")) == expected


@pytest.mark.parametrize(
    "mode", ["empty", "duplicate", "wrong-count", "changed-node", "bool-count"]
)
def test_pinned_collection_fails_closed(runner, mode):
    nodes = (NODE,)
    pin = dict(cases=1, node_sha256=runner.helpers().node_digest(nodes))
    assert runner.valid_pin(nodes, pin)
    if mode == "empty":
        nodes = ()
    elif mode == "duplicate":
        nodes = (NODE, NODE)
    elif mode == "wrong-count":
        pin["cases"] = 2
    elif mode == "changed-node":
        nodes = (NODE + "[changed]",)
    else:
        pin["cases"] = True
    assert not runner.valid_pin(nodes, pin)


def test_source_closure_includes_synthetic_rights_shared_classifier_and_approved_plan(runner):
    hashes = runner.source_hashes()
    for name in (
        "backend/tests/knowledge_video_decoder_fixtures.py",
        "backend/tests/unit/test_knowledge_video_copy.py",
        "backend/src/sketch2life/application/ai_policy_copy_dispatch.py",
        "features/FEAT-049-be2-ai-policy/src/run_component_checks.py",
        "features/FEAT-050-be2-knowledge-video/src/run_component_checks.py",
        "features/FEAT-050-be2-knowledge-video/src/TEST_INVENTORY.json",
        "features/FEAT-050-be2-knowledge-video/approvals/TASK_APPROVAL.md",
    ):
        assert len(hashes[name]) == 64
    assert len(runner.owned_sources()) == 19
    assert not any("evidence/" in name for name in hashes)


def test_pack_suites_exclude_sql_and_do_not_call_other_pack_main(runner):
    owned = runner.suites(("test_knowledge_video_",))
    assert "tests/contract/test_knowledge_video_decoder_pack.py" in owned
    assert "tests/unit/test_knowledge_video_component_runner.py" in owned
    assert not set(owned) & set(runner.SQL)
    assert all(path.startswith(("tests/unit/", "tests/contract/")) for path in owned)


def test_subprocess_cannot_inherit_sql_opt_in_or_leak_environment(runner, monkeypatch, tmp_path):
    monkeypatch.setenv("KV08_TEST_ALLOW_SCHEMA_DDL", "1")
    monkeypatch.setenv("KV08_TEST_DATABASE_URL", "private-test-url")
    captured = []

    def fake(command, **options):
        captured.append(options)
        assert "KV08_TEST_ALLOW_SCHEMA_DDL" not in options["env"]
        assert "KV08_TEST_DATABASE_URL" not in options["env"]
        assert options["timeout"] == 300 and options["check"] is False
        return SimpleNamespace(returncode=0, stdout="safe", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake)
    code, output = runner.run(["fixture"], tmp_path, tmp_path / "process.log")
    assert code == 0 and output == "safe" and captured
    assert "private" not in (tmp_path / "process.log").read_text()


@pytest.mark.parametrize("error", [OSError("private"), subprocess.TimeoutExpired("private", 300)])
def test_process_failure_is_closed_code_not_success_or_raw_secret(
    runner, monkeypatch, tmp_path, error
):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(runner.subprocess, "run", fail)
    code, output = runner.run(["fixture"], tmp_path, tmp_path / "process.log")
    assert code == 124 and output == ""
    assert "private" not in (tmp_path / "process.log").read_text()


@pytest.mark.parametrize("mode", ["pass", "skip", "changed-source", "wrong-pin"])
def test_main_sql_only_collects_and_partial_evidence_cannot_pass(
    runner, monkeypatch, tmp_path, mode
):
    feature = tmp_path / "features/fixture"
    (feature / "approvals").mkdir(parents=True)
    (feature / "src").mkdir()
    (feature / "approvals/TASK_APPROVAL.md").write_text("- Status: APPROVED", encoding="utf-8")
    shared = runner.helpers()
    pin = dict(cases=1, node_sha256=shared.node_digest((NODE,)))
    if mode == "wrong-pin":
        pin["cases"] = 2
    (feature / "src/TEST_INVENTORY.json").write_text(
        json.dumps(dict.fromkeys(("owned", "regression", "sql_collection_only"), pin)),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "FEATURE", feature)
    monkeypatch.setattr(runner, "suites", lambda prefixes: ("tests/unit/fixture.py",))
    monkeypatch.setattr(runner, "owned_sources", lambda: ())
    before = {"features/FEAT-050-be2-knowledge-video/plan/PLAN.md": runner.PLAN_SHA256}
    snapshots = iter(
        (before, before | ({"new-source.py": "a" * 64} if mode == "changed-source" else {}))
    )
    monkeypatch.setattr(runner, "source_hashes", lambda: next(snapshots))
    monkeypatch.setattr(
        runner,
        "helpers",
        lambda: SimpleNamespace(
            inventory=shared.inventory,
            valid_inventory=shared.valid_inventory,
            classify=lambda *args: ("NOT_RUN", 2) if mode == "skip" else ("PASS", 0),
        ),
    )
    commands = []

    def fake_run(command, cwd, log):
        commands.append(command)
        return 0, NODE

    monkeypatch.setattr(runner, "run", fake_run)
    assert runner.main() == (0 if mode == "pass" else 1)
    sql_commands = [command for command in commands if runner.SQL[0] in command]
    # Also appears in Ruff's explicit path list, never as an executed pytest suite.
    sql_pytest = [command for command in sql_commands if "pytest" in command]
    assert len(sql_pytest) == 1 and "--collect-only" in sql_pytest[0]
    summary_file = next((tmp_path / ".runtime").rglob("summary.json"))
    summary = json.loads(summary_file.read_text())
    assert summary["postgresql"] == summary["provider_generation"] == "NOT_RUN"
    assert summary["full_card_complete"] is False
