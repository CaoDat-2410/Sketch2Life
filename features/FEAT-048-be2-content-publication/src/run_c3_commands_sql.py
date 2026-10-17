"""Source-pinned C3b PostgreSQL pack; missing/skipped cases never count as PASS."""

from __future__ import annotations

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
SUITE = "tests/integration/learning_content/test_commands_sql.py"
EXPECTED = {
    "test_application_publish_restart_replay_and_recall_are_durable": 1,
    "test_application_receipt_failure_rolls_back_all_sql_writes": 1,
    "test_concurrent_identical_create_recovers_unique_winner": 1,
    "test_conflicting_application_commands_have_one_sql_cas_winner": 3,
    "test_concurrent_duplicate_submit_replays_without_extra_event": 1,
    "test_negative_review_resubmit_preserves_sql_proof_history": 1,
    "test_derived_history_preserves_original_sql_proofs_across_resubmit": 1,
    "test_history_sql_edit_and_recall_do_not_rewrite_old_approval": 2,
    "test_retired_head_edit_requires_fresh_review_without_restoring_old_version": 2,
}
SOURCES = (
    "backend/src/sketch2life/application/learning_content_commands.py",
    "backend/src/sketch2life/application/learning_content_history.py",
    "backend/src/sketch2life/application/learning_content_eligibility.py",
    "backend/src/sketch2life/application/ports/learning_content.py",
    "backend/src/sketch2life/contracts/schemas/learning_content.py",
    "backend/src/sketch2life/contracts/schemas/ai_contract_candidates.py",
    "backend/src/sketch2life/domain/learning_content/model.py",
    "backend/src/sketch2life/infrastructure/learning_content/sql.py",
    "backend/src/sketch2life/infrastructure/learning_content/tables.py",
    "backend/alembic/versions/20261017_lc_0001_content_publication.py",
    "backend/alembic/env.py",
    "backend/tests/learning_content_fixtures.py",
    "backend/tests/integration/learning_content/conftest.py",
    "backend/tests/integration/learning_content/test_content_sql.py",
    "backend/" + SUITE,
    "features/FEAT-048-be2-content-publication/src/run_c3_commands_sql.py",
)


def hashes() -> dict[str, str]:
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def main() -> int:
    if os.environ.get("LC_TEST_ALLOW_CREATE") != "1" or not os.environ.get("LC_TEST_PG_HOST"):
        print("NOT_RUN: authorized disposable PostgreSQL profile required")
        return 2
    out = ROOT / ".runtime/learning-content-c3b" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    before = hashes()
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", SUITE]
    collected = subprocess.run([*command, "--collect-only", "-q"], cwd=ROOT / "backend",
                               text=True, capture_output=True, check=False)
    (out / "collection.log").write_text(collected.stdout + collected.stderr, encoding="utf-8")
    nodes = [line.strip().split("::", 1)[1] for line in collected.stdout.splitlines()
             if line.strip().startswith(SUITE + "::")]
    if (collected.returncode or len(nodes) != len(set(nodes))
            or Counter(node.split("[", 1)[0] for node in nodes) != EXPECTED):
        print(f"FAIL: C3b inventory mismatch; {out}")
        return 1
    junit = out / "junit.xml"
    result = subprocess.run([*command, "-q", "--tb=short", f"--junitxml={junit}"],
                            cwd=ROOT / "backend", text=True, capture_output=True, check=False)
    (out / "pytest.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    status, exit_code = "FAIL", 1
    if junit.is_file():
        tree = ET.parse(junit)
        cases = list(tree.iter("testcase"))
        names = [case.get("name", "") for case in cases]
        bad = any(True for _ in tree.iter("failure")) or any(True for _ in tree.iter("error"))
        skipped = any(True for _ in tree.iter("skipped"))
        if not bad and not result.returncode and before == hashes():
            if set(names) == set(nodes) and len(names) == len(nodes) and not skipped:
                status, exit_code = "PASS", 0
            elif skipped or set(names).issubset(nodes):
                status, exit_code = "NOT_RUN", 2
    summary = {"scope": "C3B_POSTGRES_ASSUMED_OWNER_PORTS", "status": status,
               "pytest_exit": result.returncode, "cases": len(nodes),
               "source_sha256": before, "source_unchanged": before == hashes()}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{status}: {out}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
