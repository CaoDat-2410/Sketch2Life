"""Consolidated source-pinned local BE2-14 proof; no runtime/provider activation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "features/FEAT-049-be2-ai-policy"
EXPECTED_CASES = 1061
EXPECTED_NODE_SHA256 = "a045b0e24ddeb250a5358ef3d1ef29ef98bbe61e000078bd60c9d11b0c4d068f"
FOUNDATION_NODE_SHA256 = "858bcea4b0723c0c34250415be51611a385d0658d1d97e094f6b86c294b6a60b"
FOUNDATION = (
    "tests/unit/test_ai_job_application.py",
    "tests/unit/test_ai_job_review_regressions.py",
    "tests/unit/test_ai_job_q00_followups.py",
)


def suites() -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(ROOT / "backend").as_posix()
            for directory in ("unit", "contract")
            for path in (ROOT / "backend/tests" / directory).glob("test_ai_policy_*.py")
        )
    )


def owned_sources() -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "backend/src/sketch2life").rglob("*.py")
            if "ai_policy" in path.parts or path.name.startswith("ai_policy")
        )
    )


def source_hashes() -> dict[str, str]:
    paths = set()
    for directory in ("backend/src", "backend/tests", "backend/alembic"):
        paths.update((ROOT / directory).rglob("*.py"))
    paths.update(path for path in FEATURE.rglob("*") if path.suffix in {".py", ".md"})
    paths.update(
        ROOT / name
        for name in (
            "backend/pyproject.toml",
            "backend/alembic.ini",
            "features/FEAT-048-be2-content-publication/src/run_component_checks.py",
            "tools/validate_architecture.py",
            "tools/validate_harness.py",
            "tools/validate_repository_security.py",
        )
    )
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def inventory(output: str) -> tuple[str, ...]:
    return tuple(
        line.strip().replace("\\", "/")
        for line in output.splitlines()
        if line.strip().replace("\\", "/").startswith("tests/") and "::" in line
    )


def node_digest(nodes: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(sorted(nodes)).encode("utf-8")).hexdigest()


def valid_inventory(nodes: tuple[str, ...], count: int, digest: str) -> bool:
    return bool(nodes) and len(nodes) == len(set(nodes)) == count and node_digest(nodes) == digest


def classify(nodes: tuple[str, ...], junit: Path, process_exit: int) -> tuple[str, int]:
    if process_exit or not nodes or len(nodes) != len(set(nodes)):
        return "FAIL", 1
    if not junit.is_file():
        return "NOT_RUN", 2
    try:
        tree = ET.parse(junit)
        suite_elements = list(tree.iter("testsuite"))
        if tree.getroot().tag not in {"testsuite", "testsuites"} or not suite_elements:
            return "FAIL", 1
        for suite in suite_elements:
            if int(suite.get("tests", "-1")) != len(list(suite.iter("testcase"))):
                return "FAIL", 1
            counts = [int(suite.get(key, "0")) for key in ("failures", "errors", "skipped")]
            if any(value < 0 for value in counts):
                return "FAIL", 1
            if counts[0] or counts[1]:
                return "FAIL", 1
            if counts[2]:
                return "NOT_RUN", 2
        names = tuple(
            case.get("classname", "").replace(".", "/") + ".py::" + case.get("name", "")
            for case in tree.iter("testcase")
        )
    except (ET.ParseError, OSError, ValueError):
        return "FAIL", 1
    if list(tree.iter("failure")) or list(tree.iter("error")):
        return "FAIL", 1
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
    out = ROOT / ".runtime/ai-policy-component" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    checks: dict[str, int] = {}
    base = [sys.executable, "-m", "pytest", "-o", "addopts="]
    collection = run(
        [*base, *suites(), "--collect-only", "-q"], ROOT / "backend", out / "collection.log"
    )
    nodes = inventory(collection.stdout)
    checks["collection"] = collection.returncode
    status, exit_code = "FAIL", 1
    if not collection.returncode and valid_inventory(nodes, EXPECTED_CASES, EXPECTED_NODE_SHA256):
        junit = out / "component.xml"
        tested = run(
            [*base, *suites(), "-q", "--tb=short", f"--junitxml={junit}"],
            ROOT / "backend",
            out / "pytest.log",
        )
        checks["pytest"] = tested.returncode
        status, exit_code = classify(nodes, junit, tested.returncode)
        if exit_code == 0:
            foundation_collection = run(
                [*base, *FOUNDATION, "--collect-only", "-q"],
                ROOT / "backend",
                out / "foundation-collection.log",
            )
            foundation_nodes = inventory(foundation_collection.stdout)
            checks["foundation_collection"] = foundation_collection.returncode
            if foundation_collection.returncode or not valid_inventory(
                foundation_nodes, 114, FOUNDATION_NODE_SHA256
            ):
                status, exit_code = "FAIL", 1
            else:
                receipt = out / "foundation.xml"
                tested = run(
                    [*base, *FOUNDATION, "-q", "--tb=short", f"--junitxml={receipt}"],
                    ROOT / "backend",
                    out / "foundation.log",
                )
                _, code = classify(foundation_nodes, receipt, tested.returncode)
                checks["foundation"] = code
                if code:
                    status, exit_code = "FAIL", 1
            commands = {
                "ruff": [
                    sys.executable,
                    "-m",
                    "ruff",
                    "check",
                    "--config",
                    "pyproject.toml",
                    *(path.removeprefix("backend/") for path in owned_sources()),
                    str(Path(__file__)),
                    "tests/unit/test_ai_policy_component_runner.py",
                ],
                "mypy": [
                    sys.executable,
                    "-m",
                    "mypy",
                    "--config-file",
                    "backend/pyproject.toml",
                    *owned_sources(),
                ],
                "regression477": [
                    sys.executable,
                    "features/FEAT-048-be2-content-publication/src/run_component_checks.py",
                ],
                "architecture": [sys.executable, "tools/validate_architecture.py"],
                "harness": [sys.executable, "tools/validate_harness.py"],
                "security": [sys.executable, "tools/validate_repository_security.py"],
                "whitespace": ["git", "diff", "--check"],
            }
            for name, command in commands.items():
                cwd = ROOT / "backend" if name == "ruff" else ROOT
                checks[name] = run(command, cwd, out / f"{name}.log").returncode
                if checks[name]:
                    status, exit_code = "FAIL", 1
    unchanged = before == source_hashes()
    if not unchanged:
        status, exit_code = "FAIL", 1
    summary = dict(
        scope="BE2_14_LOCAL_COMPONENT_ONLY",
        status=status,
        cases=len(nodes),
        expected_cases=EXPECTED_CASES,
        node_sha256=node_digest(nodes),
        checks=checks,
        source_sha256=before,
        source_unchanged=unchanged,
        postgresql="NOT_RUN_BY_THIS_PACK",
        real_owner_integration="NOT_RUN",
        provider_integration="NOT_RUN",
        full_goal_complete=False,
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{status}: {out}")
    print("Local component only; PostgreSQL/provider/current-owner adoption remain separate.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
