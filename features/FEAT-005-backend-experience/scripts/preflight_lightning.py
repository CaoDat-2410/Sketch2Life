#!/usr/bin/env python3
"""Validate prerequisites for a real Wan2.2 smoke test."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

FEATURE_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(FEATURE_ROOT / "src"))

from learning_video.preflight_support import check_settings  # noqa: E402
from learning_video.settings import load_settings  # noqa: E402


def cuda_available(python_binary: str) -> bool:
    probe = [python_binary, "-c", "import torch; print(torch.cuda.is_available())"]
    try:
        result = subprocess.run(probe, capture_output=True, text=True, timeout=20, check=True)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.stdout.strip().lower() == "true"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    settings = load_settings(args.config)
    problems = check_settings(settings)
    if settings.wan.provider == "wan2.2" and not cuda_available(settings.wan.python_binary):
        problems.append("PyTorch does not report CUDA availability")

    if problems:
        print("PREFLIGHT_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("PREFLIGHT_OK")
    print(f"provider={settings.wan.provider}")
    print(f"checkpoint_dir={settings.wan.checkpoint_dir}")
    print(f"output_dir={settings.wan.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
