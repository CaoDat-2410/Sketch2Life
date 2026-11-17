"""Run only the authorized C2 disposable-PostgreSQL suite; never starts a service.

Missing environment or skipped/missing cases means NOT_RUN/exit 2, not PASS.
Actual logs remain under ignored .runtime, not committed as child/secret data.
"""

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
SUITE = "tests/integration/learning_content/test_content_sql.py"
EXPECTED = {
    "test_upgrade_downgrade_only_owns_its_schema": 1,
    "test_restart_reads_bytes_and_atomic_event_outbox": 1,
    "test_exception_rolls_back_state_receipt_and_events": 1,
    "test_stale_save_is_not_a_second_winner": 1,
    "test_concurrent_updates_have_one_cas_winner": 1,
    "test_edit_creates_version_and_preserves_previous_bytes": 1,
    "test_database_rejects_rewriting_immutable_history": 3,
}


def main() -> int:
    if os.environ.get("LC_TEST_ALLOW_CREATE") != "1" or not os.environ.get("LC_TEST_PG_HOST"):
        print("NOT_RUN: authorized LC_TEST_PG_HOST and LC_TEST_ALLOW_CREATE=1 required")
        return 2
    out = ROOT / ".runtime/learning-content-c2" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    junit = out / "junit.xml"
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", SUITE]
    collected = subprocess.run(
        [*command, "--collect-only", "-q"], cwd=ROOT / "backend",
        text=True, capture_output=True, check=False)
    (out / "collection.log").write_text(collected.stdout + collected.stderr, encoding="utf-8")
    nodes = [line.strip().split("::", 1)[1] for line in collected.stdout.splitlines()
             if line.strip().startswith(SUITE + "::")]
    if (collected.returncode or len(nodes) != len(set(nodes))
            or Counter(node.split("[", 1)[0] for node in nodes) != EXPECTED):
        print(f"FAIL: C2 test inventory/collection mismatch; logs at {out}")
        return 1
    result = subprocess.run(
        [*command, "-q", f"--junitxml={junit}", "--tb=short"],
        cwd=ROOT / "backend", text=True, capture_output=True, check=False)
    (out / "pytest.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    summary: dict[str, object] = {
        "scope": "C2_POSTGRES_ONLY", "status": "FAIL",
        "python": sys.executable, "pytest_exit": result.returncode, "cases": len(nodes),
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [
                Path(__file__), ROOT / "backend" / SUITE,
                ROOT / "backend/tests/integration/learning_content/conftest.py",
                ROOT / "backend/src/sketch2life/infrastructure/learning_content/sql.py",
                ROOT / "backend/src/sketch2life/infrastructure/learning_content/tables.py",
                ROOT / "backend/src/sketch2life/application/ports/learning_content.py",
                ROOT / "backend/src/sketch2life/domain/learning_content/model.py",
                ROOT / "backend/alembic/versions/20261017_lc_0001_content_publication.py",
                ROOT / "backend/alembic/env.py",
            ]}}
    exit_code = 1
    if junit.is_file():
        tree = ET.parse(junit)
        cases = list(tree.iter("testcase"))
        names = [case.get("name", "") for case in cases]
        bad = any(case.find("failure") is not None or case.find("error") is not None
                  for case in cases) or any(True for _ in tree.iter("error"))
        skipped = any(case.find("skipped") is not None for case in cases)
        if (bad or result.returncode or set(names) - set(nodes)
                or len(names) != len(set(names))):
            exit_code = 1
        elif skipped or len(names) != len(nodes) or set(names) != set(nodes):
            summary["status"] = "NOT_RUN"
            exit_code = 2
        else:
            summary["status"] = "PASS"
            exit_code = 0
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{summary['status']}: {out}")
    print("Return summary.json, junit.xml and pytest.log; do not share passwords or .env files.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
