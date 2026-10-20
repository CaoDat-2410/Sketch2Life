"""Pinned13 local pack, prior regression and SQL COLLECTION ONLY."""

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
FEATURE = ROOT / "features/FEAT-054-be2-preset-automation"
PLAN_SHA256 = "601afab84123ee5dd48aa04cf643ea7cd904f53675a0b16a9c007684660e1548"
SQL = ("tests/integration/preset_automation/test_owned_sql.py",)


def helpers():
    path = ROOT / "features/FEAT-053-be2-activity-execution/src/run_component_checks.py"
    spec = importlib.util.spec_from_file_location("preset13_helpers", path)
    if spec is None or spec.loader is None:
        raise ValueError("EVIDENCE_HELPER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence():
    return helpers().evidence()  # Exact inventory/JUnit helpers; never call nested main.


def groups() -> dict[str, tuple[str, ...]]:
    previous = helpers()
    old = previous.groups()
    return {
        "owned": tuple(
            sorted(
                p.relative_to(ROOT / "backend").as_posix()
                for folder in ("unit", "contract")
                for p in (ROOT / "backend/tests" / folder).glob("test_preset_automation_*.py")
            )
        ),
        "regression": (*old["owned"], *old["regression"], *old["legacy_catalog"]),
        "sql_collection_only": SQL,
    }


def owned_sources() -> tuple[str, ...]:
    return tuple(
        sorted(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "backend/src").rglob("*.py")
            if "preset_automation" in p.parts
            or p.name.startswith(("preset_automation", "preset_governance"))
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
        / ".runtime/preset-automation-component"
        / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    )
    out.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    approved = before["features/FEAT-054-be2-preset-automation/plan/PLAN.md"] == PLAN_SHA256
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
            "tests/preset_automation_fixtures.py",
            str(Path(__file__)),
            "alembic/env.py",
            "alembic/versions/20261019_pa_0001_preset_automation.py",
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
            "sql_collection_only": "COLLECTED_NOT_RUN",
        }
        and all(code == 0 for code in checks.values())
    )
    summary = dict(
        scope="BE2_13_LOCAL_COMPONENT_ONLY",
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
        actual_session_config_effect="NOT_RUN",
        actual_scheduler="NOT_RUN",
        full_card_complete=False,
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{summary['status']}: {out}", flush=True)
    print(f"Cases: {counts}; source_unchanged={unchanged}", flush=True)
    print("LOCAL ONLY: SQL/actual preset policy/BE1 effect/scheduler NOT_RUN.", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
