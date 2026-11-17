"""Pinned11 local pack, legacy catalog parity and SQL COLLECTION ONLY."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "features/FEAT-053-be2-activity-execution"
PLAN_SHA256 = "09348e0fcafb96370c3c58e99ae5b8a8eaee16d416694066985086ecde09ac1d"
SQL = ("tests/integration/activity_execution/test_owned_sql.py",)
LEGACY = (
    "tests/unit/test_activity_semantics.py",
    "tests/unit/test_catalog_expansion.py",
    "tests/unit/test_lightning_activity_ranker.py",
    "tests/contract/test_activity_preparation_catalog.py",
)


def helpers():
    path = ROOT / "features/FEAT-052-be2-video-failure-disposition/src/run_component_checks.py"
    spec = importlib.util.spec_from_file_location("activity11_helpers", path)
    if spec is None or spec.loader is None:
        raise ValueError("EVIDENCE_HELPER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence():
    return helpers().helpers().helpers()  # 08 exact inventory/JUnit helpers, no nested main.


def groups() -> dict[str, tuple[str, ...]]:
    previous = helpers()
    old = previous.groups()
    return {
        "owned": previous.helpers().suites(("test_activity_execution_",)),
        "regression": (*old["owned"], *old["regression"]),
        "legacy_catalog": LEGACY,
        "sql_collection_only": SQL,
    }


def owned_sources() -> tuple[str, ...]:
    return tuple(
        sorted(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "backend/src").rglob("*.py")
            if "activity_execution" in p.parts
            or p.name.startswith(("activity_execution", "activity_discovery"))
        )
    )


def source_hashes() -> dict[str, str]:
    values = helpers().source_hashes()
    paths = [
        FEATURE / name
        for name in ("plan/PLAN.md", "approvals/TASK_APPROVAL.md", "src/TEST_INVENTORY.json")
    ]
    # Include legacy catalog/config data read by parity suites, not just Python.
    paths.extend((ROOT / "data").rglob("*.json"))
    paths.extend((ROOT / "backend/tools").rglob("*.py"))
    for path in paths:
        values[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def run(args: list[str], cwd: Path, log: Path) -> tuple[int, str]:
    env = dict(os.environ)
    for key in tuple(env):
        if key.endswith(("_TEST_DATABASE_URL", "_TEST_ALLOW_SCHEMA_DDL")):
            env.pop(key)
    try:
        result = subprocess.run(
            args, cwd=cwd, env=env, text=True, capture_output=True, check=False, timeout=300
        )
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        return result.returncode, result.stdout
    except (OSError, subprocess.TimeoutExpired):
        log.write_text("CHECK_PROCESS_UNAVAILABLE_OR_TIMEOUT\n", encoding="utf-8")
        return 124, ""


def main() -> int:
    out = (
        ROOT
        / ".runtime/activity-execution-component"
        / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    )
    out.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    approved = before["features/FEAT-053-be2-activity-execution/plan/PLAN.md"] == PLAN_SHA256
    approved = (
        approved and "- Status: APPROVED" in (FEATURE / "approvals/TASK_APPROVAL.md").read_text()
    )
    pins = json.loads((FEATURE / "src/TEST_INVENTORY.json").read_text())
    selected = groups()
    support = evidence()
    counts: dict[str, int] = {}
    statuses: dict[str, str] = {}
    base = [sys.executable, "-m", "pytest", "-o", "addopts="]
    for name, paths in selected.items():
        code, output = run(
            [*base, *paths, "--collect-only", "-q"],
            ROOT / "backend",
            out / f"{name}-collection.log",
        )
        nodes = support.inventory(output)
        counts[name] = len(nodes)
        if not approved or code or not paths or not support.valid_pin(nodes, pins.get(name, {})):
            statuses[name] = "FAIL"
            continue
        if name == "sql_collection_only":
            statuses[name] = "COLLECTED_NOT_RUN"
            continue
        junit = out / f"{name}.xml"
        code, _ = run(
            [*base, *paths, "-q", "--tb=short", f"--junitxml={junit}"],
            ROOT / "backend",
            out / f"{name}.log",
        )
        statuses[name], _ = support.helpers().classify(nodes, junit, code)
    commands = {
        "ruff": [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--config",
            "pyproject.toml",
            *(p.removeprefix("backend/") for p in owned_sources()),
            *selected["owned"],
            *SQL,
            "tests/activity_execution_fixtures.py",
            str(Path(__file__)),
            "alembic/env.py",
            "alembic/versions/20261019_ae_0001_activity_execution.py",
        ],
        "mypy": [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            "backend/pyproject.toml",
            "--follow-imports=silent",
            *owned_sources(),
        ],
        "architecture": [sys.executable, "tools/validate_architecture.py"],
        "harness": [sys.executable, "tools/validate_harness.py", "--feature", str(FEATURE)],
        "security": [sys.executable, "tools/validate_repository_security.py"],
        "whitespace": ["git", "diff", "--check"],
    }
    checks = {
        name: run(cmd, ROOT / "backend" if name == "ruff" else ROOT, out / f"{name}.log")[0]
        for name, cmd in commands.items()
    }
    unchanged = before == source_hashes()
    passed = (
        approved
        and unchanged
        and statuses
        == {
            "owned": "PASS",
            "regression": "PASS",
            "legacy_catalog": "PASS",
            "sql_collection_only": "COLLECTED_NOT_RUN",
        }
        and all(code == 0 for code in checks.values())
    )
    summary = dict(
        scope="BE2_11_LOCAL_COMPONENT_ONLY",
        status="PASS" if passed else "FAIL",
        cases=counts,
        statuses=statuses,
        checks=checks,
        source_sha256=before,
        source_unchanged=unchanged,
        junit_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*.xml"))
        },
        postgresql="NOT_RUN",
        actual_owner_integration="NOT_RUN",
        actual_outcome_save="NOT_RUN",
        actual_recommendation_provider="NOT_RUN",
        full_card_complete=False,
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{summary['status']}: {out}", flush=True)
    print(f"Cases: {counts}; source_unchanged={unchanged}", flush=True)
    print("LOCAL ONLY: SQL/actual publication/policy/BE1 outcome/provider NOT_RUN.", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
