"""CPU check of the rebuilt video image (FEAT-094 phase 2): both Python environments, before any GPU time.

    modal run -e dev features/FEAT-094-learning-video-redesign/evidence/M4_two_containers/check_image.py

Compares the renderer environment with the package list exported before the rebuild, imports what the preparation child
imports, and runs one preparation request on the paper fallback.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import modal

WORKERS = Path(__file__).resolve().parents[4] / "deployment" / "modal" / "srs_v23" if modal.is_local() else Path("/root")
app = modal.App("sketch2life-feat094-image-check")

if modal.is_local():
    sys.path.insert(0, str(WORKERS))
    import video_app

    IMAGE = video_app._with_runtime_modules(video_app._inference_image).add_local_file(
        str(WORKERS / "video_app.py"), "/root/video_app.py"
    )
else:
    IMAGE = None


@app.function(image=IMAGE, cpu=4.0, memory=8_192, timeout=900)
def check() -> dict[str, Any]:
    import os
    import subprocess
    import tempfile

    import scene_prepare_host as host

    child_env = host.child_environment(dict(os.environ))  # the container PYTHONPATH points at the renderer

    def output(*command: str, env: dict[str, str] | None = None) -> str:
        done = subprocess.run(command, capture_output=True, text=True, env=env)
        return done.stdout if done.returncode == 0 else f"FAILED {done.stderr[-1500:]}"

    imports = output(
        "/opt/prep-venv/bin/python",
        "-c",
        "import sys; sys.path.insert(0, '/root'); import torch, diffusers, transformers, numpy; "
        "from diffusers import ModularPipeline; from sam2.build_sam import build_sam2; "
        "import scene_prepare_server; print(torch.__version__, diffusers.__version__, transformers.__version__)",
        env=child_env,
    )
    worker = host.PrepWorker(
        ["/opt/prep-venv/bin/python", "/root/scene_prepare_server.py"], env=child_env
    )
    with tempfile.TemporaryDirectory() as directory:
        from PIL import Image, ImageDraw

        drawing = Image.new("RGB", (800, 600), "white")
        ImageDraw.Draw(drawing).ellipse((250, 180, 550, 420), fill=(200, 40, 40))
        drawing.save(Path(directory) / "drawing.png")
        request = {
            "scene_index": 1,
            "main": {"entity_id": "e1", "label": "ball", "box": [300, 300, 700, 700]},
            "secondaries": [],
            "staging": {},
            "plate_prompt": "A park.",
            "source_facing": "right",
        }
        try:
            prepared = worker.request("prepare", {"directory": directory, "request": request}, timeout=600)
        except host.PrepWorkerError as error:
            prepared = {"error": str(error)}
        worker.stop()
    return {
        "renderer_freeze": output("uv", "pip", "freeze", "--python", "/opt/LTX-2/.venv/bin/python"),
        "lock_sha256": Path("/opt/LTX-2/LTX_UV_LOCK_SHA256").read_text().strip(),
        "ffmpeg": output("ffmpeg", "-version").splitlines()[0],
        "prepare_imports": imports.strip(),
        "prepare_request": prepared,
    }


@app.local_entrypoint()
def main() -> None:
    result = check.remote()
    before = Path(__file__).with_name("ltx_venv_freeze.txt").read_text(encoding="utf-8").split()
    after = result.pop("renderer_freeze").split()
    print("RESULT renderer_packages", len(after), "removed", sorted(set(before) - set(after)), "added", sorted(set(after) - set(before)))
    for name, value in result.items():
        print("RESULT", name, value)
