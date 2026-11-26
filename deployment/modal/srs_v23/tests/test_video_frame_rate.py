"""FEAT-094: a clip keeps 24 frames per second on every ffmpeg version.

ffmpeg 7.1 (the image built in the new Modal workspace) forgets the frame rate after ``setpts`` and writes 25 frames per
second unless the output rate is named, so every scene failed its own profile check.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))


def _video_app() -> Any:
    spec = importlib.util.spec_from_file_location("sketch2life_video_app_rate", MODAL_DIR / "video_app.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_normalised_clip_names_its_output_frame_rate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app = _video_app()
    commands: list[list[str]] = []
    destination = tmp_path / "clip.mp4"

    def run(command: list[str], **_options: Any) -> Any:
        commands.append(command)
        destination.write_bytes(b"x")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(app.subprocess, "run", run)

    app._normalize_silent_clip(tmp_path / "raw.mp4", destination, target_duration=6.0, generated_frame_count=145)

    command = commands[0]
    output_options = command[command.index("-vf") + 2 :]
    assert output_options[output_options.index("-r") + 1] == "24"


def test_the_assembled_story_names_its_output_frame_rate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app = _video_app()
    commands: list[list[str]] = []
    output = tmp_path / "story.mp4"

    def run(command: list[str], **_options: Any) -> Any:
        commands.append(command)
        output.write_bytes(b"x")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(app.subprocess, "run", run)

    app._assemble_silent_story(tmp_path / "list.txt", output, target_duration=30.0)

    command = commands[0]
    output_options = command[command.index("-vf") + 2 :]
    assert output_options[output_options.index("-r") + 1] == "24"


def test_the_speed_module_is_mounted_last_so_the_pinned_image_layers_are_kept() -> None:
    # A new file in an early layer rebuilds everything after it, including the unlocked dependency resolve that
    # brought in a different ffmpeg.
    source = (MODAL_DIR / "video_app.py").read_text(encoding="utf-8")
    base = source[source.index("_worker_base_image = (") : source.index("_download_image = ")]

    assert "_ltx_speed_file" not in base
    assert source.count("image=_with_speed_module(") == source.count("    image=")
