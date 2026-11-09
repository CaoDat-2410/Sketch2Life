from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
OUTPUT_DIR = (
    FEATURE
    / "evidence"
    / "assets"
    / "ai_nonvideo_ai_end_to_end_20261105"
    / "speech_retest_13"
)
SCRIPT_DIR = SCRIPT.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_speech_nonvideo_retest_20261104 as speech


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main() -> int:
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise SystemExit("Retest evidence exists; refusing duplicate dispatch.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "run_metadata.json").write_text(
        json.dumps(
            {
                "plan": "PLAN_REV45_NONVIDEO_AI_END_TO_END_20261105.md",
                "started_at": _now(),
                "synthetic_only": True,
                "workloads": ["tts.narration.generate", "asr.transcribe"],
                "video_called": False,
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    speech.OUTPUT_DIR = OUTPUT_DIR
    speech.main()
    summary_path = OUTPUT_DIR / "speech_roundtrip_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["started_at"] = json.loads(
        (OUTPUT_DIR / "run_metadata.json").read_text(encoding="utf-8")
    )["started_at"]
    summary["ended_at"] = _now()
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
