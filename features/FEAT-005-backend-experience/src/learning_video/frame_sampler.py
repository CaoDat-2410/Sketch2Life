"""FFmpeg media-integrity checks and representative frame sampling."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .schemas import FrameSamplingResult, ValidationStatus


class FrameSampler:
    sample_percentages = (0, 25, 50, 75, 100)

    def __init__(
        self,
        ffmpeg_binary: str = "ffmpeg",
        ffprobe_binary: str = "ffprobe",
        timeout_sec: int = 60,
    ) -> None:
        self._ffmpeg = ffmpeg_binary
        self._ffprobe = ffprobe_binary
        self._timeout_sec = timeout_sec

    def sample(self, video_path: Path, output_dir: Path) -> FrameSamplingResult:
        if not video_path.is_file():
            return self._failure(video_path, "VIDEO_FILE_NOT_FOUND")

        try:
            duration = self._probe_duration(video_path)
        except (OSError, ValueError, subprocess.SubprocessError):
            return self._failure(video_path, "VIDEO_NOT_DECODABLE")

        if not 5 <= duration <= 10:
            return FrameSamplingResult(
                status=ValidationStatus.BLOCK,
                video_path=video_path.as_posix(),
                duration_sec=duration,
                sample_percentages=list(self.sample_percentages),
                reason_codes=["DURATION_OUT_OF_BOUNDS"],
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        frame_paths: list[str] = []
        for percentage in self.sample_percentages:
            timestamp = min(duration - 0.001, duration * percentage / 100)
            frame_path = output_dir / f"frame_{percentage:03d}.jpg"
            try:
                self._extract_frame(video_path, frame_path, timestamp)
            except (OSError, subprocess.SubprocessError):
                return FrameSamplingResult(
                    status=ValidationStatus.BLOCK,
                    video_path=video_path.as_posix(),
                    duration_sec=duration,
                    sampled_frame_paths=frame_paths,
                    sample_percentages=list(self.sample_percentages),
                    reason_codes=["FRAME_SAMPLING_FAILED"],
                )
            frame_paths.append(frame_path.as_posix())

        return FrameSamplingResult(
            status=ValidationStatus.PASS,
            video_path=video_path.as_posix(),
            duration_sec=duration,
            sampled_frame_paths=frame_paths,
            sample_percentages=list(self.sample_percentages),
        )

    def _probe_duration(self, video_path: Path) -> float:
        completed = subprocess.run(
            [
                self._ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=self._timeout_sec,
        )
        duration = float(completed.stdout.strip())
        if duration <= 0:
            raise ValueError("video duration must be positive")
        return duration

    def _extract_frame(self, video_path: Path, frame_path: Path, timestamp: float) -> None:
        subprocess.run(
            [
                self._ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(frame_path),
            ],
            check=True,
            capture_output=True,
            timeout=self._timeout_sec,
        )
        if not frame_path.is_file():
            raise subprocess.CalledProcessError(1, self._ffmpeg)

    @staticmethod
    def _failure(video_path: Path, reason_code: str) -> FrameSamplingResult:
        return FrameSamplingResult(
            status=ValidationStatus.BLOCK,
            video_path=video_path.as_posix(),
            reason_codes=[reason_code],
        )
