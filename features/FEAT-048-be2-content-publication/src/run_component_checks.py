"""Source-pinned BE2-12 component handoff pack; never claims owner integration.

No service/start/install/network activity. Raw receipts stay under ignored runtime.
0=component PASS, 1=FAIL, 2=NOT_RUN. PostgreSQL is a separate authorized pack.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUITES = {
    "tests/contract/test_ai_job_contracts.py": 74,
    "tests/contract/test_ai_job_polling.py": 11,
    "tests/contract/test_content_consumers.py": 25,
    "tests/contract/test_governance_dispatcher.py": 50,
    "tests/contract/test_governance_http.py": 9,
    "tests/contract/test_learning_content_commands.py": 34,
    "tests/contract/test_learning_content_http.py": 33,
    "tests/unit/test_ai_job_lifecycle.py": 25,
    "tests/unit/test_learning_content_c2_runner.py": 8,
    "tests/unit/test_learning_content_commands_service.py": 51,
    "tests/unit/test_learning_content_domain.py": 45,
    "tests/unit/test_learning_content_eligibility.py": 44,
    "tests/unit/test_learning_content_history.py": 24,
    "tests/unit/test_learning_content_persistence_shape.py": 5,
    "tests/unit/test_learning_content_component_runner.py": 16,
}
FOUNDATION_SUITES = frozenset({
    "tests/contract/test_ai_job_contracts.py", "tests/contract/test_ai_job_polling.py",
    "tests/unit/test_ai_job_lifecycle.py",
})
SOURCE_FILES = (
    "application/content_consumer_queries.py", "application/governance_dispatcher.py",
    "application/learning_content_commands.py", "application/learning_content_eligibility.py",
    "application/learning_content_history.py", "application/ports/content_consumers.py",
    "application/ports/learning_content.py", "contracts/schemas/content_consumers.py",
    "contracts/schemas/governance.py", "contracts/schemas/learning_content.py",
    "domain/learning_content/model.py", "infrastructure/learning_content/sql.py",
    "infrastructure/learning_content/tables.py", "interfaces/http/routers/learning_content.py",
)


def source_hashes() -> dict[str, str]:
    # All backend Python source captures transitive imports, not only edited files.
    paths = set((ROOT / "backend/src").rglob("*.py"))
    paths.update(ROOT / "backend" / name for name in SUITES)
    paths.update((ROOT / "backend/alembic").rglob("*.py"))
    paths.update(ROOT / name for name in (
        "backend/tests/conftest.py", "backend/tests/learning_content_fixtures.py",
        "backend/pyproject.toml", "tools/validate_architecture.py", "tools/validate_harness.py",
        "tools/validate_repository_security.py",
        "features/FEAT-048-be2-content-publication/src/run_component_checks.py"))
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def inventory(output: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in output.splitlines()
                 if line.strip().startswith("tests/") and "::" in line)


def valid_inventory(nodes: tuple[str, ...]) -> bool:
    return (len(nodes) == len(set(nodes))
            and Counter(node.split("::", 1)[0] for node in nodes) == SUITES)


def classify(nodes: tuple[str, ...], junit: Path, process_exit: int) -> tuple[str, int]:
    if process_exit:
        return "FAIL", 1
    if not junit.is_file():
        return "NOT_RUN", 2
    try:
        tree = ET.parse(junit)
    except (ET.ParseError, OSError):
        return "FAIL", 1
    if list(tree.iter("failure")) or list(tree.iter("error")):
        return "FAIL", 1
    names = tuple(case.get("classname", "").replace(".", "/") + ".py::"
                  + case.get("name", "") for case in tree.iter("testcase"))
    if len(names) != len(set(names)) or set(names) - set(nodes):
        return "FAIL", 1
    if list(tree.iter("skipped")) or set(names) != set(nodes):
        return "NOT_RUN", 2
    return "PASS", 0


def run(args: list[str], cwd: Path, log: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    return result


def main() -> int:
    missing = [name for name in ("pytest", "ruff", "mypy")
               if importlib.util.find_spec(name) is None]
    if missing:
        print("NOT_RUN: missing existing check dependencies: " + ", ".join(missing))
        return 2
    out = ROOT / ".runtime/learning-content-component" / datetime.now(UTC).strftime(
        "%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", *SUITES]
    collected = run([*command, "--collect-only", "-q"], ROOT / "backend", out / "collection.log")
    nodes = inventory(collected.stdout)
    status, exit_code = "FAIL", 1
    checks: dict[str, int] = {"collection": collected.returncode}
    if not collected.returncode and valid_inventory(nodes):
        junit = out / "junit.xml"
        tested = run([*command, "-q", "--tb=short", f"--junitxml={junit}"],
                     ROOT / "backend", out / "pytest.log")
        checks["pytest"] = tested.returncode
        status, exit_code = classify(nodes, junit, tested.returncode)
        if exit_code == 0:
            owned = ["backend/src/sketch2life/" + path for path in SOURCE_FILES]
            commands = {
                "ruff": [sys.executable, "-m", "ruff", "check", "--config", "pyproject.toml",
                         *("src/sketch2life/" + name for name in SOURCE_FILES),
                         *(name for name in SUITES if name not in FOUNDATION_SUITES),
                         "tests/learning_content_fixtures.py", str(Path(__file__))],
                "mypy": [sys.executable, "-m", "mypy", "--config-file", "backend/pyproject.toml",
                         "--follow-imports=silent", *owned],
                "architecture": [sys.executable, "tools/validate_architecture.py"],
                "harness": [sys.executable, "tools/validate_harness.py"],
                "security": [sys.executable, "tools/validate_repository_security.py"],
                "whitespace": ["git", "diff", "--check"],
            }
            for name, args in commands.items():
                check_cwd = ROOT / "backend" if name == "ruff" else ROOT
                checks[name] = run(args, check_cwd, out / (name + ".log")).returncode
                if checks[name]:
                    status, exit_code = "FAIL", 1
    unchanged = before == source_hashes()
    if not unchanged:
        status, exit_code = "FAIL", 1
    summary = {
        "scope": "BE2_12_SELECTED_COMPONENT_HANDOFF_ONLY", "status": status,
        "cases": len(nodes), "expected_cases": sum(SUITES.values()), "checks": checks,
        "source_sha256": before, "source_unchanged": unchanged,
        "lint_scope": "OWNED_BE2_12_SOURCE_AND_TESTS_ONLY",
        "postgresql": "NOT_RUN_BY_THIS_PACK", "real_owner_integration": "NOT_RUN",
        "full_goal_complete": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{status}: {out}")
    print("Component receipt only; PostgreSQL and real owner adoption remain separate.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
