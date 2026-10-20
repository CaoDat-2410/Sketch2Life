"""Source/node-pinned10 local pack. SQL collects only, no activation/provisioning."""

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
FEATURE = ROOT / "features/FEAT-052-be2-video-failure-disposition"
PLAN_SHA256 = "8d0162c6f78b019406910927952c3d85b435a81d50de80874b023fa3a9cfb420"
SQL = ("tests/integration/video_failure/test_owned_sql.py",)


def helpers():
    path = ROOT / "features/FEAT-051-be2-video-review-playback/src/run_component_checks.py"
    spec = importlib.util.spec_from_file_location("failure10_pack_helpers", path)
    if spec is None or spec.loader is None:
        raise ValueError("EVIDENCE_HELPER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def groups() -> dict[str, tuple[str, ...]]:
    support = helpers()
    return {
        "owned": support.suites(("test_video_failure_",)),
        "regression": (
            *support.suites(
                (
                    "test_video_review_",
                    "test_video_playback",
                    "test_knowledge_video_",
                    "test_ai_policy_",
                    "test_learning_content_",
                )
            ),
            *support.FOUNDATION,
        ),
        "sql_collection_only": SQL,
    }


def owned_sources() -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "backend/src").rglob("*.py")
            if "video_failure" in path.parts or path.name.startswith("video_failure")
        )
    )


def source_hashes() -> dict[str, str]:
    hashes = helpers().source_hashes()
    for name in ("plan/PLAN.md", "approvals/TASK_APPROVAL.md", "src/TEST_INVENTORY.json"):
        path = FEATURE / name
        hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def run(command: list[str], cwd: Path, log: Path) -> tuple[int, str]:
    env = dict(os.environ)
    # Do not inherit any card's actual DB opt-in/URL. This pack NEVER executes SQL.
    for name in tuple(env):
        if name.endswith(("_TEST_ALLOW_SCHEMA_DDL", "_TEST_DATABASE_URL")):
            env.pop(name)
    try:
        result = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=300
        )
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        return result.returncode, result.stdout
    except (OSError, subprocess.TimeoutExpired):
        log.write_text("CHECK_PROCESS_UNAVAILABLE_OR_TIMEOUT\n", encoding="utf-8")
        return 124, ""


def main() -> int:
    out = ROOT / ".runtime/video-failure-component" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    approved = before["features/FEAT-052-be2-video-failure-disposition/plan/PLAN.md"] == PLAN_SHA256
    approved = (
        approved and "- Status: APPROVED" in (FEATURE / "approvals/TASK_APPROVAL.md").read_text()
    )
    pins = json.loads((FEATURE / "src/TEST_INVENTORY.json").read_text())
    statuses: dict[str, str] = {}
    counts: dict[str, int] = {}
    selection = groups()
    support = helpers().helpers()
    base = [sys.executable, "-m", "pytest", "-o", "addopts="]
    for name, suites in selection.items():
        code, output = run(
            [*base, *suites, "--collect-only", "-q"],
            ROOT / "backend",
            out / f"{name}-collection.log",
        )
        nodes = support.inventory(output)
        counts[name] = len(nodes)
        if not approved or code or not suites or not support.valid_pin(nodes, pins.get(name, {})):
            statuses[name] = "FAIL"
            continue
        if name == "sql_collection_only":
            statuses[name] = "COLLECTED_NOT_RUN"
            continue
        junit = out / f"{name}.xml"
        code, _ = run(
            [*base, *suites, "-q", "--tb=short", f"--junitxml={junit}"],
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
            *selection["owned"],
            *SQL,
            "tests/video_failure_fixtures.py",
            str(Path(__file__)),
            "alembic/env.py",
            "alembic/versions/20261019_vf_0001_video_failure.py",
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
        name: run(command, ROOT / "backend" if name == "ruff" else ROOT, out / f"{name}.log")[0]
        for name, command in commands.items()
    }
    unchanged = before == source_hashes()
    passed = (
        approved
        and unchanged
        and statuses
        == {"owned": "PASS", "regression": "PASS", "sql_collection_only": "COLLECTED_NOT_RUN"}
        and all(code == 0 for code in checks.values())
    )
    summary = dict(
        scope="BE2_10_LOCAL_COMPONENT_ONLY",
        status="PASS" if passed else "FAIL",
        statuses=statuses,
        cases=counts,
        checks=checks,
        source_sha256=before,
        source_unchanged=unchanged,
        junit_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*.xml"))
        },
        postgresql="NOT_RUN",
        actual_owners="NOT_RUN",
        actual_budget_consumption="NOT_RUN",
        actual_checkpoint="NOT_RUN",
        provider="NOT_RUN",
        full_card_complete=False,
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{summary['status']}: {out}", flush=True)
    print(f"Cases: {counts}; source_unchanged={unchanged}", flush=True)
    print("LOCAL COMPONENT ONLY. Actual SQL/owners/budget/checkpoint/provider NOT_RUN.", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
