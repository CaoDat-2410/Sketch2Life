"""Source-pinned BE2-14 PostgreSQL lifecycle pack; never starts/downloads a server."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUITE = "tests/integration/ai_policy/test_policy_sql.py"
EXPECTED = {
    "test_module_upgrade_downgrade_isolated": 1,
    "test_child_process_restart_reads_committed_policy_and_scoped_outbox": 1,
    "test_transaction_failure_rolls_back_lifecycle_receipt_event_outbox": 1,
    "test_concurrent_writers_have_one_record_cas_winner": 1,
    "test_duplicate_receipt_rolls_back_second_command": 1,
    "test_raw_sql_cannot_rewrite_version_or_history": 6,
    "test_replacing_review_dimension_roundtrips_order_and_preserves_all_proofs": 1,
    "test_review_history_survives_resubmission": 1,
    "test_old_published_version_recall_does_not_replace_new_head": 1,
    "test_repository_rejects_rewritten_body_and_rolls_back": 1,
}
ACTIVATION_SUITE = "tests/integration/ai_policy/test_activation_sql.py"
ACTIVATION_EXPECTED = {
    "test_actual_commands_publish_disable_and_restart_effective_pin": 1,
    "test_actual_scope_and_lifecycle_rollback_if_receipt_insert_fails": 1,
    "test_concurrent_publications_serialize_to_one_effective_pin": 1,
    "test_recall_of_old_pin_racing_replacement_does_not_disable_new_pin": 1,
}


def source_hashes() -> dict[str, str]:
    paths = set((ROOT / "backend/src").rglob("*.py"))
    paths.update((ROOT / "backend/alembic").rglob("*.py"))
    paths.update((ROOT / "backend/tests/integration/ai_policy").rglob("*.py"))
    paths.update(ROOT / name for name in (
        "backend/tests/conftest.py", "backend/tests/unit/test_ai_policy_domain.py",
        "backend/tests/ai_policy_fixtures.py", "backend/tests/unit/test_ai_policy_compatibility.py",
        "backend/tests/contract/test_ai_policy_contracts.py",
        "backend/pyproject.toml", "backend/alembic.ini",
        "features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py"))
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def inventory(output: str, suite: str = SUITE) -> tuple[str, ...]:
    return tuple(line.strip() for line in output.splitlines()
                 if line.strip().startswith(suite + "::"))


def valid_inventory(nodes: tuple[str, ...], expected: dict[str, int] | None = None) -> bool:
    return (len(nodes) == len(set(nodes))
            and Counter(node.split("::", 1)[1].split("[", 1)[0] for node in nodes)
            == (EXPECTED if expected is None else expected))


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


def run(args: list[str], out: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=ROOT / "backend", text=True,
                            capture_output=True, check=False)
    out.write_text(result.stdout + result.stderr, encoding="utf-8")
    return result


def main(*, activation: bool = False) -> int:
    if os.environ.get("AP_TEST_ALLOW_CREATE") != "1" or not os.environ.get("AP_TEST_PG_HOST"):
        print("NOT_RUN: explicit authorized BE2-14 disposable PostgreSQL profile required")
        return 2
    out = ROOT / ".runtime/ai-policy-c2" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    suite = ACTIVATION_SUITE if activation else SUITE
    expected = ACTIVATION_EXPECTED if activation else EXPECTED
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", suite]
    collected = run([*command, "--collect-only", "-q"], out / "collection.log")
    nodes = inventory(collected.stdout, suite)
    status, exit_code = "FAIL", 1
    if collected.returncode == 0 and valid_inventory(nodes, expected):
        junit = out / "junit.xml"
        tested = run([*command, "-q", "--tb=short", f"--junitxml={junit}"], out / "pytest.log")
        status, exit_code = classify(nodes, junit, tested.returncode)
    unchanged = before == source_hashes()
    if not unchanged:
        status, exit_code = "FAIL", 1
    summary = dict(scope="BE2_14_C3B_ACTIVATION_SQL" if activation else "BE2_14_OWNED_C2_SQL_ONLY",
                   status=status, expected_cases=sum(expected.values()), cases=len(nodes),
                   source_sha256=before, source_unchanged=unchanged,
                   real_owner_integration="NOT_RUN", full_goal_complete=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{status}: {out}")
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation", action="store_true")
    raise SystemExit(main(activation=parser.parse_args().activation))
