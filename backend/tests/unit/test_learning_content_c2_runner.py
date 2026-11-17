"""C2 runner classification tests only; mocked subprocess is not PostgreSQL proof."""

from __future__ import annotations

import importlib.util
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "features/FEAT-048-be2-content-publication/src/run_c2_sql_checks.py"


@pytest.fixture
def runner(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("lc_c2_runner", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    local = tmp_path / "features/FEAT-048-be2-content-publication/src/run_c2_sql_checks.py"
    local.parent.mkdir(parents=True)
    local.write_text("# synthetic runner")
    monkeypatch.setattr(module, "__file__", str(local))
    for relative in (
        "backend/" + module.SUITE,
        "backend/tests/integration/learning_content/conftest.py",
        "backend/src/sketch2life/infrastructure/learning_content/sql.py",
        "backend/src/sketch2life/infrastructure/learning_content/tables.py",
        "backend/src/sketch2life/application/ports/learning_content.py",
        "backend/src/sketch2life/domain/learning_content/model.py",
        "backend/alembic/versions/20261017_lc_0001_content_publication.py",
        "backend/alembic/env.py",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# synthetic source")
    monkeypatch.setenv("LC_TEST_PG_HOST", "synthetic-not-connected")
    monkeypatch.setenv("LC_TEST_ALLOW_CREATE", "1")
    return module


@pytest.mark.parametrize(("mode", "expected"), [
    ("pass", 0), ("skipped", 2), ("missing", 2), ("extra", 1),
    ("failed", 1), ("collection_error", 1), ("missing_collection_variant", 1),
])
def test_runner_fails_closed_without_complete_matching_cases(
    runner, monkeypatch, mode: str, expected: int,
) -> None:
    names = [name if count == 1 else f"{name}[{index}]"
             for name, count in runner.EXPECTED.items() for index in range(count)]

    def fake_run(command, **kwargs):
        if "--collect-only" in command:
            collected = names[:-1] if mode == "missing_collection_variant" else names
            return subprocess.CompletedProcess(
                command, 1 if mode == "collection_error" else 0,
                stdout="\n".join(runner.SUITE + "::" + name for name in collected), stderr="")
        path = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("--junitxml=")))
        root = ET.Element("testsuites")
        suite = ET.SubElement(root, "testsuite")
        written = names[:-1] if mode == "missing" else list(names)
        if mode == "extra":
            written.append("unmapped_case")
        for index, name in enumerate(written):
            case = ET.SubElement(suite, "testcase", name=name)
            if index == 0 and mode in {"skipped", "failed"}:
                ET.SubElement(case, "skipped" if mode == "skipped" else "failure")
        ET.ElementTree(root).write(path)
        return subprocess.CompletedProcess(command, 1 if mode == "failed" else 0,
                                           stdout="synthetic subprocess", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    assert runner.main() == expected


def test_runner_without_explicit_environment_does_not_start_subprocess(runner, monkeypatch) -> None:
    monkeypatch.delenv("LC_TEST_ALLOW_CREATE")

    def forbidden(*args, **kwargs):
        raise AssertionError("must not execute")

    monkeypatch.setattr(runner.subprocess, "run", forbidden)
    assert runner.main() == 2
