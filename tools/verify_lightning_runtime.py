"""Read-only runtime inventory. Never download weights, start servers or run inference."""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def inventory(wan_repo: Path | None = None) -> dict[str, object]:
    packages = ("torch", "diffusers", "transformers", "accelerate", "safetensors")
    gpu_tool = shutil.which("nvidia-smi")
    gpu = "NOT_DETECTED"
    if gpu_tool:
        try:
            result = subprocess.run(
                [gpu_tool, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=15, check=False,
            )
            gpu = result.stdout.strip() if result.returncode == 0 else "QUERY_FAILED"
        except (OSError, subprocess.TimeoutExpired):
            gpu = "QUERY_FAILED"
    wan_revision = "UNVERIFIED"
    if wan_repo is not None and (wan_repo / ".git").exists():
        try:
            result = subprocess.run(
                ["git", "-C", str(wan_repo), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10, check=False,
            )
            if result.returncode == 0:
                wan_revision = result.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    versions: dict[str, str | None] = {}
    for name in packages:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    torch_cuda = False
    if importlib.util.find_spec("torch") is not None:
        try:
            torch = importlib.import_module("torch")
            torch_cuda = bool(torch.cuda.is_available())
        except (AttributeError, ImportError, RuntimeError):  # pragma: no cover - remote runtime
            torch_cuda = False
    return {
        "status": "INVENTORY_ONLY", "inference_executed": False,
        "gpu": gpu, "packages": {name: importlib.util.find_spec(name) is not None
                                   for name in packages},
        "package_versions": versions,
        "torch_cuda_available": torch_cuda,
        "cuda_environment_ready": bool(gpu_tool and torch_cuda and versions["torch"]),
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "wan_generate_present": bool(wan_repo and (wan_repo / "generate.py").is_file()),
        "wan_revision": wan_revision,
        "checkpoint_configured": bool(os.getenv("WAN_CKPT_DIR", "").strip()),
        "real_inference_ready": False,
        "note": "Inventory is not CUDA/model/CLI compatibility or visual acceptance",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("mock", "inventory", "real"), default="mock")
    parser.add_argument("--wan-repo", type=Path)
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    if args.mode == "real":
        print(json.dumps({"status": "BLOCKED", "reason": "REAL_INFERENCE_NOT_AUTHORIZED",
                          "inference_executed": False}))
        return 2
    if args.mode == "mock":
        print(json.dumps({"status": "MOCK_ONLY", "inference_executed": False,
                          "artifact_generated": False}))
        return 0
    report = inventory(args.wan_repo)
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if args.require_cuda and not report["cuda_environment_ready"]:
        print("REQUIRES_LIGHTNINGAI_TEST: CUDA/Torch environment is not ready", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
