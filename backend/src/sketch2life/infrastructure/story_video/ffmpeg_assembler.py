"""CPU assembler of the Parent video (FEAT-093): scene clips + narration chunks -> one MP4 on the master clock.

Each LTX clip fills a 1280x720 (16:9) frame at 24 fps, cut to its planned frames and extended by holding its last frame when
the narration needs more time. Narration chunks are trimmed to their speech and placed at their start times on a 48 kHz
track that is loudness-normalised. The container is faststart. Commands run through an injected runner, so the structure is
unit-tested without ffmpeg; the real runner calls the executable without a shell.
"""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Final

from sketch2life.application.video_pipeline.age_profile import FPS
from sketch2life.application.video_pipeline.ports import AssembleJob, VideoPipelineError

WIDTH: Final = 1280
HEIGHT: Final = 720
SAMPLE_RATE: Final = 48_000
TARGET_LUFS: Final = -16
Runner = Callable[[Sequence[str]], None]


def subprocess_runner(command: Sequence[str]) -> None:
    try:
        subprocess.run(  # noqa: S603 - fixed argv, no shell, paths are ours
            list(command), check=True, capture_output=True, timeout=600
        )
    except (OSError, subprocess.SubprocessError):
        raise VideoPipelineError("VIDEO_ASSEMBLE_FFMPEG_FAILED") from None


class FfmpegAssembler:
    def __init__(self, *, executable: str = "ffmpeg", runner: Runner = subprocess_runner) -> None:
        self._exe = executable
        self._run = runner

    def assemble(self, job: AssembleJob) -> bytes:
        plan = job.plan
        clips = {clip.scene_index: clip for clip in job.clips}
        if [scene.index for scene in plan.scenes] != sorted(clips):
            raise VideoPipelineError("VIDEO_ASSEMBLE_CLIPS_INCOMPLETE")
        with tempfile.TemporaryDirectory(prefix="s2l-assemble-") as directory:
            work = Path(directory)
            normalised: list[Path] = []
            for scene in plan.scenes:
                source = work / f"clip-{scene.index}.mp4"
                source.write_bytes(clips[scene.index].video)
                target = work / f"scene-{scene.index}.mp4"
                self._run(self._scene_command(source, target, scene.target_frames, scene.hold_frames))
                normalised.append(target)
            listing = work / "scenes.txt"
            listing.write_text("".join(f"file '{path.name}'\n" for path in normalised), encoding="utf-8")
            silent = work / "silent.mp4"
            self._run([self._exe, "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(silent)])
            output = work / "final.mp4"
            self._run(self._mux_command(work, silent, output, job, plan.total_frames))
            if not output.is_file() or output.stat().st_size == 0:
                raise VideoPipelineError("VIDEO_ASSEMBLE_OUTPUT_MISSING")
            return output.read_bytes()

    def _scene_command(self, source: Path, target: Path, frames: int, hold: int) -> list[str]:
        filters = [
            f"fps={FPS}",
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase",
            f"crop={WIDTH}:{HEIGHT}",
            "setsar=1",
            f"trim=end_frame={frames}",
            "setpts=PTS-STARTPTS",
        ]
        if hold > 0:
            filters.append(f"tpad=stop_mode=clone:stop={hold}")
        return [
            self._exe, "-y", "-i", str(source), "-an", "-vf", ",".join(filters),
            "-frames:v", str(frames + max(hold, 0)), "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(target),
        ]

    def _mux_command(self, work: Path, silent: Path, output: Path, job: AssembleJob, total_frames: int) -> list[str]:
        total_seconds = f"{total_frames / FPS:.3f}"
        command = [self._exe, "-y", "-i", str(silent)]
        graph: list[str] = []
        labels: list[str] = []
        for index, chunk in enumerate(job.chunks):
            path = work / f"chunk-{index}.wav"
            path.write_bytes(chunk.wav)
            command += ["-i", str(path)]
            label = f"c{index}"
            head = chunk.trim_head_ms / 1000
            length = chunk.duration_ms / 1000
            graph.append(
                f"[{index + 1}:a]aresample={SAMPLE_RATE},aformat=channel_layouts=mono,"
                f"atrim=start={head:.3f}:duration={length:.3f},asetpts=PTS-STARTPTS,"
                f"adelay={chunk.start_ms}:all=1[{label}]"
            )
            labels.append(f"[{label}]")
        if labels:
            graph.append(
                "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,"
                f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11,apad=whole_dur={total_seconds}[aout]"
            )
            command += ["-filter_complex", ";".join(graph), "-map", "0:v", "-map", "[aout]"]
        else:
            raise VideoPipelineError("VIDEO_ASSEMBLE_NO_NARRATION")
        command += [
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ar", str(SAMPLE_RATE), "-ac", "1",
            "-t", total_seconds, "-movflags", "+faststart", str(output),
        ]
        return command


__all__ = ["FfmpegAssembler", "subprocess_runner"]
