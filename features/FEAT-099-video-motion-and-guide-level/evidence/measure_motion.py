"""FEAT-099: how far does a scene move from its first frame, does it come back, and does the camera drift (CPU only).

Run from the repository root with the backend virtual environment:

    python features/FEAT-099-video-motion-and-guide-level/evidence/measure_motion.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np

FEATURES = Path(__file__).resolve().parents[2]
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
WIDTH, HEIGHT, FPS = 320, 180, 24
F94 = FEATURES / "FEAT-094-learning-video-redesign" / "evidence"
F98 = FEATURES / "FEAT-098-video-narration-and-speed" / "evidence"
# (name, file, scene starts in seconds or None for a single clip, end guide)
CLIPS = [
    ("app run, deer", F98 / "app_run" / "app_run.mp4", [0, 10, 20, 30, 40], "first frame"),
    ("run 4, chick", F94 / "M6_remaining" / "learning_run4.mp4", [0, 10, 20, 30, 40], "first frame"),
    ("benchmark base, chick", F98 / "benchmark" / "base-2.mp4", None, "none"),
    ("E1, chick", F94 / "M1_experiments" / "quality" / "chick-e1-new-prompt.mp4", None, "none"),
    ("E1, bicycle", F94 / "M1_experiments" / "quality" / "bike-e1-new-prompt.mp4", None, "none"),
]


def frames(path: Path) -> np.ndarray:
    raw = subprocess.run(
        [FFMPEG, "-loglevel", "error", "-i", str(path), "-vf", f"scale={WIDTH}:{HEIGHT},format=gray",
         "-f", "rawvideo", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, HEIGHT, WIDTH).astype(np.float32)


def shift(first: np.ndarray, last: np.ndarray) -> float:
    """Median movement (pixels at 320 wide) of eight blocks along the border: a moving camera moves most of them."""

    size = 64
    lefts, tops = (0, (WIDTH - size) // 2, WIDTH - size), (0, (HEIGHT - size) // 2, HEIGHT - size)
    moves = []
    for top in tops:
        for left in lefts:
            if (left, top) == (lefts[1], tops[1]):
                continue
            a = first[top : top + size, left : left + size]
            b = last[top : top + size, left : left + size]
            if a.std() < 8:  # a flat block (paper, sky) says nothing about movement
                continue
            cross = np.fft.fft2(a - a.mean()) * np.conj(np.fft.fft2(b - b.mean()))
            peak = np.unravel_index(np.argmax(np.abs(np.fft.ifft2(cross / (np.abs(cross) + 1e-6)))), a.shape)
            dy, dx = (p if p <= s // 2 else p - s for p, s in zip(peak, a.shape, strict=True))
            moves.append(float(np.hypot(dx, dy)))
    return round(float(np.median(moves)), 1) if moves else -1.0


def main() -> None:
    rows = []
    for name, path, starts, guide in CLIPS:
        video = frames(path)
        parts = [video] if starts is None else [video[s * FPS : (s + 10) * FPS] for s in starts]
        for index, scene in enumerate(parts, start=1):
            if len(scene) < FPS:
                continue
            distance = np.abs(scene - scene[0]).mean(axis=(1, 2))
            peak = float(distance.max())
            end = float(distance[-6:].mean())
            rows.append(
                {
                    "clip": name,
                    "scene": index,
                    "end_guide": guide,
                    "peak_change": round(peak, 1),
                    "end_change": round(end, 1),
                    "end_over_peak": round(end / peak, 2) if peak else 0.0,
                    "camera_shift_px": shift(scene[0], scene[-1]),
                }
            )
    out = Path(__file__).with_name("motion_measure.json")
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
