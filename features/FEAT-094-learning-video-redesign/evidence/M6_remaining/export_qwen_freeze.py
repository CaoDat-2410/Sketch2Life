"""List the package versions of the serving Qwen (vLLM) image so they can be pinned (FEAT-094).

    modal run -e dev features/FEAT-094-learning-video-redesign/evidence/M6_remaining/export_qwen_freeze.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import modal

WORKERS = Path(__file__).resolve().parents[4] / "deployment" / "modal" / "srs_v23" if modal.is_local() else Path("/root")
app = modal.App("sketch2life-feat094-qwen-freeze")

if modal.is_local():
    sys.path.insert(0, str(WORKERS))
    import language_audio_app

    IMAGE = language_audio_app._qwen_vllm_image
else:
    IMAGE = None


@app.function(image=IMAGE, cpu=1.0, timeout=300)
def export() -> str:
    import subprocess

    return subprocess.run(["uv", "pip", "freeze", "--system"], capture_output=True, text=True, check=True).stdout


@app.local_entrypoint()
def main() -> None:
    freeze = export.remote()
    Path(__file__).with_name("qwen_vllm_freeze.txt").write_text(freeze, encoding="utf-8", newline="\n")
    print("RESULT lines", len(freeze.splitlines()))
