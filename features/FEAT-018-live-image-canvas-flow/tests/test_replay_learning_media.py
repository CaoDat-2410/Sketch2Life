import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[3]
SCRIPT = ROOT / "scripts/replay_learning_media.py"


def test_replay_outputs_sanitized_results_for_every_scenario() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, check=True)
    report = json.loads(result.stdout)

    assert report["report_type"] == "P4_REPLAY_SANITIZED"
    assert len(report["scenarios"]) == 5
    assert all(row["generation_called"] is False for row in report["scenarios"])
    assert all(row["identity_preserved"] is True for row in report["scenarios"])
