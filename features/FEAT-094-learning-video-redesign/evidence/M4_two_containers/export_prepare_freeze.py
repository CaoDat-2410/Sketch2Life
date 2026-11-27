"""List the package versions of the image that prepared scene frames until now (FEAT-094 phase 2).

    modal run -e dev features/FEAT-094-learning-video-redesign/evidence/M4_two_containers/export_prepare_freeze.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import modal

WORKERS = Path(__file__).resolve().parents[4] / "deployment" / "modal" / "srs_v23" if modal.is_local() else Path("/root")
app = modal.App("sketch2life-feat094-freeze-export")

if modal.is_local():
    sys.path.insert(0, str(WORKERS))
    import language_audio_app

    IMAGE = language_audio_app._story_text_image
else:
    IMAGE = None


@app.function(image=IMAGE, cpu=1.0, timeout=300)
def export() -> str:
    import subprocess

    return subprocess.run(["python", "-m", "pip", "freeze"], capture_output=True, text=True, check=True).stdout


@app.local_entrypoint()
def main() -> None:
    freeze = export.remote()
    Path(__file__).with_name("text_image_freeze.txt").write_text(freeze, encoding="utf-8", newline="\n")
    print("RESULT lines", len(freeze.splitlines()))
