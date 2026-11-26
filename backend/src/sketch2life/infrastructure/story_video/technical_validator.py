"""Technical validation of the finished Parent video (FEAT-093); implements ``VideoValidatorPort``.

Checks, from ffprobe facts only: one H.264 video stream at 1280x720 and 24 fps, one AAC audio stream, container duration
within one frame of the plan and inside the SRS window (30-90 s), faststart. The vision-based consistency and final-safety
checks run on C2 in a later increment; until then this validator reports ``VIDEO_VISION_CHECKS_PENDING`` as a finding
(``consistency_ok`` / ``safety_ok`` stay True) so the open gap is visible in the job instead of silently assumed.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

from sketch2life.application.video_pipeline.age_profile import FPS
from sketch2life.application.video_pipeline.ports import ValidationReport, VideoPipelineError
from sketch2life.application.video_pipeline.video_plan import VideoPlan

WIDTH: Final = 1280
HEIGHT: Final = 720
MIN_SECONDS: Final = 30.0
MAX_SECONDS: Final = 90.0
DURATION_TOLERANCE: Final = 1 / FPS + 0.05  # one frame plus the audio stream's rounding
Probe = Callable[[Path], dict[str, Any]]


def ffprobe(path: Path, *, executable: str = "ffprobe") -> dict[str, Any]:
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [executable, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
            check=True, capture_output=True, timeout=60,
        )
        return json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        raise VideoPipelineError("VIDEO_VALIDATE_PROBE_FAILED") from None


def _faststart(video: bytes) -> bool:
    """The moov atom sits before mdat."""

    moov, mdat = video.find(b"moov"), video.find(b"mdat")
    return moov != -1 and (mdat == -1 or moov < mdat)


class TechnicalVideoValidator:
    def __init__(self, *, probe: Probe = ffprobe) -> None:
        self._probe = probe

    def validate(self, video: bytes, plan: VideoPlan) -> ValidationReport:
        findings: list[str] = []
        with tempfile.TemporaryDirectory(prefix="s2l-validate-") as directory:
            path = Path(directory) / "video.mp4"
            path.write_bytes(video)
            facts = self._probe(path)
        streams = facts.get("streams") or []
        videos = [s for s in streams if s.get("codec_type") == "video"]
        audios = [s for s in streams if s.get("codec_type") == "audio"]
        if len(videos) != 1 or videos[0].get("codec_name") != "h264":
            findings.append("VIDEO_VALIDATE_VIDEO_STREAM")
        elif (int(videos[0].get("width", 0)), int(videos[0].get("height", 0))) != (WIDTH, HEIGHT):
            findings.append("VIDEO_VALIDATE_RESOLUTION")
        elif videos[0].get("avg_frame_rate") != f"{FPS}/1":
            findings.append("VIDEO_VALIDATE_FRAME_RATE")
        if len(audios) != 1 or audios[0].get("codec_name") != "aac":
            findings.append("VIDEO_VALIDATE_NO_AUDIO")
        try:
            seconds = float(facts.get("format", {}).get("duration", 0))
        except (TypeError, ValueError):
            seconds = 0.0
        if abs(seconds - plan.total_frames / FPS) > DURATION_TOLERANCE:
            findings.append("VIDEO_VALIDATE_DURATION_MISMATCH")
        if not MIN_SECONDS - DURATION_TOLERANCE <= seconds <= MAX_SECONDS + DURATION_TOLERANCE:
            findings.append("VIDEO_VALIDATE_OUTSIDE_SRS_WINDOW")
        if not _faststart(video):
            findings.append("VIDEO_VALIDATE_NOT_FASTSTART")
        if findings:
            return ValidationReport(technical_ok=False, finding_codes=tuple(findings), failure_code=findings[0])
        return ValidationReport(finding_codes=("VIDEO_VISION_CHECKS_PENDING",))


__all__ = ["TechnicalVideoValidator", "ffprobe"]
