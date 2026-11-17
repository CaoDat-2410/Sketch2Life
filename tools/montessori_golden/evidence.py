from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_DIR = (
    ROOT / "features" / "FEAT-014-montessori-offline-test-console" / "evidence" / "runs"
)
RUN_ID = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62})$")


class EvidenceWriteError(ValueError):
    """Raised when an evidence run ID/path violates the confined write policy."""


def record_evidence(
    run_id: str,
    document: dict[str, Any],
    runs_dir: Path = DEFAULT_RUNS_DIR,
    recorded_at: str | None = None,
) -> Path:
    if not RUN_ID.fullmatch(run_id):
        raise EvidenceWriteError(
            "run ID must use 1-63 lowercase letters, digits, or internal hyphens"
        )
    runs_dir.mkdir(parents=True, exist_ok=True)
    root = runs_dir.resolve()
    path = (root / f"{run_id}.json").resolve()
    if path.parent != root:
        raise EvidenceWriteError("evidence path escaped the feature runs directory")
    if path.exists():
        raise EvidenceWriteError(f"evidence run already exists: {run_id}")
    evidence = {
        "evidence_schema_version": 1,
        "run_id": run_id,
        "recorded_at": recorded_at or datetime.now(UTC).isoformat(),
        "reviewer": "LOCAL_CONSOLE_OPERATOR",
        "environment": "OFFLINE_STANDARD_LIBRARY",
        **document,
    }
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    return path
