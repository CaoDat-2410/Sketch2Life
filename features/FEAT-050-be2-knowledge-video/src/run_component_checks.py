"""One-batch source-pinned08 component proof, NEVER DB/provider/runtime activation."""

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
FEATURE = ROOT / "features/FEAT-050-be2-knowledge-video"
PLAN_SHA256 = "370c6c04573a684c0e51c0ef1c276224d8e1f01ecd701624b2d925751cfa0b04"
FOUNDATION = (
    "tests/unit/test_ai_job_application.py",
    "tests/unit/test_ai_job_review_regressions.py",
    "tests/unit/test_ai_job_q00_followups.py",
)
SQL = ("tests/integration/knowledge_video/test_run_rows_sql.py",)


def helpers():
    """Reuse existing fail-closed exact-node/JUnit classifier, no nested runner."""
    path = ROOT / "features/FEAT-049-be2-ai-policy/src/run_component_checks.py"
    spec = importlib.util.spec_from_file_location("kv08_evidence_helpers", path)
    if spec is None or spec.loader is None:
        raise ValueError("EVIDENCE_HELPER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def suites(prefixes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(ROOT / "backend").as_posix()
            for directory in ("unit", "contract")
            for path in (ROOT / "backend/tests" / directory).glob("test_*.py")
            if path.name.startswith(prefixes)
        )
    )


def owned_sources() -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "backend/src").rglob("*.py")
            if "knowledge_video" in path.parts or path.name.startswith("knowledge_video")
        )
    )


def inventory(output: str) -> tuple[str, ...]:
    # Normalize only filesystem path; backslashes in parameter IDs are test data.
    nodes = []
    for line in output.splitlines():
        path, separator, case = line.strip().partition("::")
        path = path.replace("\\", "/")
        if separator and path.startswith("tests/"):
            nodes.append(path + separator + case)
    return tuple(nodes)


def source_hashes() -> dict[str, str]:
    # Re-enumerate AFTER testing as well, detecting new/deleted source files.
    # Mutable evidence/context/status prose excluded to avoid self-referential proof.
    paths = set()
    for directory in ("backend/src", "backend/tests", "backend/alembic"):
        paths.update((ROOT / directory).rglob("*.py"))
    for feature in (ROOT / "features").glob("*/src"):
        paths.update(feature.rglob("*.py"))
    paths.update(
        ROOT / name
        for name in (
            "AGENTS.md",
            "backend/pyproject.toml",
            "backend/alembic.ini",
            "tools/validate_architecture.py",
            "tools/validate_harness.py",
            "tools/validate_repository_security.py",
        )
    )
    paths.update(
        FEATURE / name
        for name in (
            "plan/PLAN.md",
            "approvals/TASK_APPROVAL.md",
            "src/TEST_INVENTORY.json",
        )
    )
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def valid_pin(nodes: tuple[str, ...], pin: dict[str, object]) -> bool:
    return (
        set(pin) == {"cases", "node_sha256"}
        and type(pin["cases"]) is int
        and isinstance(pin["node_sha256"], str)
        and helpers().valid_inventory(nodes, pin["cases"], pin["node_sha256"])
    )


def run(command: list[str], cwd: Path, log: Path) -> tuple[int, str]:
    # Never echo inherited environment/URLs; this pack cannot opt in SQL writes.
    env = dict(os.environ)
    for name in ("KV08_TEST_ALLOW_SCHEMA_DDL", "KV08_TEST_DATABASE_URL"):
        env.pop(name, None)
    try:
        result = subprocess.run(
            command, cwd=cwd, env=env, text=True, capture_output=True, check=False, timeout=300
        )
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        return result.returncode, result.stdout
    except (OSError, subprocess.TimeoutExpired):
        log.write_text("CHECK_PROCESS_UNAVAILABLE_OR_TIMEOUT\n", encoding="utf-8")
        return 124, ""


def main() -> int:
    out = (
        ROOT / ".runtime/knowledge-video-component" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    )
    out.mkdir(parents=True, exist_ok=False)
    checks: dict[str, object] = {}
    statuses: dict[str, str] = {}
    counts: dict[str, int] = {}
    before = source_hashes()
    plan_ok = before["features/FEAT-050-be2-knowledge-video/plan/PLAN.md"] == PLAN_SHA256
    approval_ok = "- Status: APPROVED" in (FEATURE / "approvals/TASK_APPROVAL.md").read_text()
    checks["plan_approval"] = plan_ok and approval_ok
    pins = json.loads((FEATURE / "src/TEST_INVENTORY.json").read_text())
    groups = {
        "owned": suites(("test_knowledge_video_",)),
        "regression": (*suites(("test_ai_policy_", "test_learning_content_")), *FOUNDATION),
        "sql_collection_only": SQL,
    }
    base = [sys.executable, "-m", "pytest", "-o", "addopts="]
    for name, selection in groups.items():
        code, stdout = run(
            [*base, *selection, "--collect-only", "-q"],
            ROOT / "backend",
            out / f"{name}-collection.log",
        )
        nodes = inventory(stdout)
        counts[name] = len(nodes)
        if (
            not plan_ok
            or not approval_ok
            or not selection
            or code
            or not valid_pin(nodes, pins[name])
        ):
            statuses[name] = "FAIL"
            continue
        if name == "sql_collection_only":
            statuses[name] = "COLLECTED_NOT_RUN"
            continue
        junit = out / f"{name}.xml"
        code, _ = run(
            [*base, *selection, "-q", "--tb=short", f"--junitxml={junit}"],
            ROOT / "backend",
            out / f"{name}.log",
        )
        statuses[name], _ = helpers().classify(nodes, junit, code)
    commands = {
        "ruff": [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--config",
            "pyproject.toml",
            *(path.removeprefix("backend/") for path in owned_sources()),
            *groups["owned"],
            SQL[0],
            "tests/knowledge_video_decoder_fixtures.py",
            str(Path(__file__)),
            "alembic/env.py",
            "alembic/versions/20261018_kv_0001_knowledge_video.py",
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
    for name, command in commands.items():
        cwd = ROOT / "backend" if name == "ruff" else ROOT
        checks[name], _ = run(command, cwd, out / f"{name}.log")
    unchanged = before == source_hashes()
    passed = (
        plan_ok
        and approval_ok
        and unchanged
        and statuses
        == {"owned": "PASS", "regression": "PASS", "sql_collection_only": "COLLECTED_NOT_RUN"}
        and all(checks[name] == 0 for name in commands)
    )
    summary = dict(
        scope="BE2_08_LOCAL_COMPONENT_ONLY",
        status="PASS" if passed else "FAIL",
        statuses=statuses,
        cases=counts,
        checks=checks,
        source_sha256=before,
        source_unchanged=unchanged,
        postgresql="NOT_RUN",
        selected_runtime_decoder="NOT_RUN",
        synthetic_gif_decoder="SEE_OWNED_FIXTURE_TESTS_NOT_PRODUCTION_VIDEO",
        provider_generation="NOT_RUN",
        actual_owner_integration="NOT_RUN",
        actual_copy_deletion="NOT_RUN",
        full_card_complete=False,
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{summary['status']}: {out}", flush=True)
    print(f"Cases: {counts}; source_unchanged={unchanged}", flush=True)
    print("LOCAL COMPONENT ONLY; SQL/provider/selected decoder/adoption NOT_RUN.", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
