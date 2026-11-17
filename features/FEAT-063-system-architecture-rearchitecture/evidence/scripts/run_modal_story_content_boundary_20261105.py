"""One-shot synthetic dispatcher for the Parent story content-boundary check."""

from __future__ import annotations

from pathlib import Path

import run_modal_story_parser_alignment_20261105 as runner

ASSET_DIR = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "modal_story_content_boundary_20261105"
)
runner.ASSET_DIR = ASSET_DIR
runner.INTENT_PATH = ASSET_DIR / "story_dispatch_intent.json"
runner.RESULT_PATH = ASSET_DIR / "story_result.json"
runner.LOG_PATH = ASSET_DIR / "modal_function_logs.txt"


if __name__ == "__main__":
    raise SystemExit(runner.main())
