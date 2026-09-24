"""Local runtime callbacks for the provider-backed whiteboard MVP."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class WhiteboardLearningThreadScripts:
    """Read bounded, feature-local learning-thread scripts from JSON."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def script_for(self, learning_thread_ref: str) -> str:
        if not learning_thread_ref:
            raise ValueError("learning thread reference is required")
        try:
            payload: Any = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("learning thread script fixture is unavailable") from error
        script = payload.get(learning_thread_ref) if isinstance(payload, dict) else None
        if not isinstance(script, str) or not script.strip():
            raise ValueError("learning thread script is unavailable")
        return script.strip()


class EspeakVietnameseTts:
    """Generate an independent Vietnamese WAV narration using eSpeak."""

    def __init__(self, executable: str = "espeak-ng") -> None:
        self._executable = executable

    def synthesize(self, script: str, output_path: str | Path) -> None:
        executable = shutil.which(self._executable)
        if executable is None:
            raise RuntimeError(f"TTS executable is unavailable: {self._executable}")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        command = [
            executable,
            "-v",
            "vi",
            "-s",
            "145",
            "-w",
            str(output),
            script,
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=20)
        if completed.returncode != 0 or not output.is_file() or output.stat().st_size <= 0:
            raise RuntimeError("eSpeak did not produce a narration artifact")


class FfmpegWhiteboardEncoder:
    """Mux the rendered H.264 video and independent narration into MP4."""

    def __init__(self, executable: str = "ffmpeg") -> None:
        self._executable = executable

    def encode(self, render_ref: str, tts_ref: str, output_path: str | Path) -> None:
        executable = shutil.which(self._executable)
        if executable is None:
            raise RuntimeError(f"FFmpeg executable is unavailable: {self._executable}")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        command = [
            executable,
            "-y",
            "-i",
            render_ref,
            "-i",
            tts_ref,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-b:a",
            "128k",
            "-t",
            "8.0",
            str(output),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=45)
        if completed.returncode != 0 or not output.is_file() or output.stat().st_size <= 0:
            raise RuntimeError("FFmpeg did not produce a whiteboard MP4")

    def inspect(self, path: str | Path) -> tuple[float, str, int]:
        executable = shutil.which("ffprobe")
        if executable is None:
            raise RuntimeError("ffprobe executable is unavailable")
        command = [
            executable,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_name,profile,level,codec_type",
            "-of",
            "json",
            str(path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=20)
        if completed.returncode != 0:
            raise RuntimeError("FFprobe could not inspect the MP4")
        payload = json.loads(completed.stdout)
        streams = payload.get("streams", [])
        video = next(
            (item for item in streams if item.get("codec_type") == "video"), None
        )
        duration = float(payload.get("format", {}).get("duration", 0.0))
        if not isinstance(video, dict) or video.get("codec_name") != "h264":
            raise ValueError("MP4 video stream is not H.264")
        profile = str(video.get("profile", "")).replace(" ", "_").upper()
        level = int(video.get("level", 0))
        codec = (
            "H264_AVC_HIGH_L4_1"
            if profile == "HIGH" and level == 41
            else f"H264_{profile}_L{level / 10:.1f}"
        )
        return duration, codec, Path(path).stat().st_size


__all__ = [
    "EspeakVietnameseTts",
    "FfmpegWhiteboardEncoder",
    "WhiteboardLearningThreadScripts",
]
