from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE_DIR = Path(__file__).resolve().parent
ATTEMPT_NAME = os.environ.get("REV87_29_ATTEMPT", "")
if ATTEMPT_NAME not in {"attempt_elephant", "attempt_fish"}:
    raise RuntimeError("REV87_29_RENDER_ATTEMPT_OUT_OF_BOUNDS")
ATTEMPT_DIR = EVIDENCE_DIR / ATTEMPT_NAME
RESPONSE_PATH = ATTEMPT_DIR / "response.json"
RENDERED_DIR = ATTEMPT_DIR / "rendered"
RENDERER_SCRIPT = (
    ROOT
    / "features/FEAT-063-system-architecture-rearchitecture/evidence/"
    / "EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/attempt_003/render_parent_result.py"
)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    payload = json.loads(RESPONSE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload.get("document"), dict) or not isinstance(
        payload.get("guide"), dict
    ):
        raise RuntimeError("GENUINE_PARENT_RESPONSE_HAS_NO_RENDERABLE_GUIDE")
    spec = importlib.util.spec_from_file_location("saved_parent_result_renderer", RENDERER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("SAVED_RESPONSE_RENDERER_UNAVAILABLE")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    renderer.RESPONSE_PATH = RESPONSE_PATH
    renderer.OUT = RENDERED_DIR
    renderer.main()


if __name__ == "__main__":
    main()
