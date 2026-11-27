"""Copy the dependency lock out of the built LTX image so that later builds reuse it (FEAT-094 phase 2).

    modal run -e dev features/FEAT-094-learning-video-redesign/evidence/M4_two_containers/export_ltx_lock.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import modal

REPOSITORY = Path(__file__).resolve().parents[4] if modal.is_local() else Path("/root")
WORKERS = REPOSITORY / "deployment" / "modal" / "srs_v23" if modal.is_local() else Path("/root")
app = modal.App("sketch2life-feat094-lock-export")

if modal.is_local():
    sys.path.insert(0, str(WORKERS))
    import video_app

    IMAGE = video_app._with_runtime_modules(video_app._inference_image).add_local_file(
        str(WORKERS / "video_app.py"), "/root/video_app.py"
    )
else:
    IMAGE = None


@app.function(image=IMAGE, cpu=1.0, timeout=300)
def export() -> dict[str, str]:
    import subprocess

    lock = Path("/opt/LTX-2/uv.lock").read_text(encoding="utf-8")
    freeze = subprocess.run(
        ["uv", "pip", "freeze", "--python", "/opt/LTX-2/.venv/bin/python"], capture_output=True, text=True, check=True
    ).stdout
    recorded = Path("/opt/LTX-2/LTX_UV_LOCK_SHA256").read_text(encoding="utf-8").strip()
    return {"lock": lock, "freeze": freeze, "recorded_sha256": recorded}


@app.local_entrypoint()
def main() -> None:
    result = export.remote()
    data = result["lock"].encode("utf-8")
    target = REPOSITORY / "deployment" / "modal" / "srs_v23" / "locks" / "ltx-2.5-v1.6.2.uv.lock"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    Path(__file__).with_name("ltx_venv_freeze.txt").write_text(result["freeze"], encoding="utf-8", newline="\n")
    print("RESULT sha256", hashlib.sha256(data).hexdigest(), "recorded", result["recorded_sha256"], "bytes", len(data))
