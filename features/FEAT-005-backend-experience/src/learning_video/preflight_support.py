"""Testable prerequisite checks used by the Lightning preflight script."""

from __future__ import annotations

import shutil

from .settings import AppSettings


def check_settings(settings: AppSettings) -> list[str]:
    problems: list[str] = []
    if settings.wan.provider != "wan2.2":
        problems.append(f"provider is {settings.wan.provider!r}; use wan2.2 for a real smoke test")
    if shutil.which(settings.wan.python_binary) is None:
        problems.append(f"Python binary not found: {settings.wan.python_binary}")
    if not settings.wan.inference_script.is_file():
        problems.append(f"Wan2.2 inference script not found: {settings.wan.inference_script}")
    if not settings.wan.checkpoint_dir.is_dir():
        problems.append(f"Wan2.2 checkpoint directory not found: {settings.wan.checkpoint_dir}")
    for binary in ("ffmpeg", "ffprobe"):
        if shutil.which(binary) is None:
            problems.append(f"Required media binary not found: {binary}")
    if settings.wan.output_dir.exists() and not settings.wan.output_dir.is_dir():
        problems.append(f"Output path is not a directory: {settings.wan.output_dir}")
    return problems
