"""FEAT-099 research: a throwaway CPU walk of the child's own deer drawing, to judge what rigged motion looks like.

Not product code. Legs are cut with ``part_split_prototype`` and turned about the hip with a four-beat walk: a foot on
the ground stays where it is while the body moves over it (no sliding). Run from the repository root:

    python features/FEAT-099-video-motion-and-guide-level/evidence/walk_prototype.py <drawing.png>
"""

from __future__ import annotations

import math
import subprocess
import sys
import time
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from part_split_prototype import components, morph, subject_mask  # noqa: E402

FPS, SECONDS = 24, 6
PERIOD, DUTY, SWING = 1.5, 0.7, math.radians(11)
# Four-beat walk of a deer facing left, legs ordered from the front of the animal to the back.
PHASES = (0.75, 0.25, 0.5, 0.0)


def split(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    mask = subject_mask(rgb)
    trunk = morph(morph(mask, 33, ImageFilter.MinFilter), 33, ImageFilter.MaxFilter) & mask
    trunk = components(trunk, 200)[0]
    middle = np.nonzero(trunk)[0].mean()
    legs = [part for part in components(mask & ~trunk, 700) if np.nonzero(part)[0].mean() > middle]
    dark = (rgb.max(axis=2) < 150) & (np.ptp(rgb.astype(int), axis=2) < 60)
    for index, leg in enumerate(legs):  # the dark hoof under a leg belongs to it
        rows, cols = np.nonzero(leg)
        box = np.zeros_like(leg)
        box[rows.max() - 8 : rows.max() + 22, cols[rows > rows.max() - 12].min() - 6 : cols[rows > rows.max() - 12].max() + 7] = True
        legs[index] = leg | (box & morph(dark, 5, ImageFilter.MaxFilter))
        mask |= legs[index]
    return mask, trunk, sorted(legs, key=lambda leg: np.nonzero(leg)[1].mean())


def fill_behind(rgb: np.ndarray, hole: np.ndarray) -> np.ndarray:
    """Paint the hole with the pixels beside it in the same row (grass stays grass, paper stays paper)."""

    out = rgb.copy()
    for y in np.nonzero(hole.any(axis=1))[0]:
        free = np.nonzero(~hole[y])[0]
        cols = np.nonzero(hole[y])[0]
        left = cols[0]
        run = free[free < left][-60:] if (free < left).any() else free[:60]
        out[y, cols] = rgb[y, run[(cols - left) % len(run)]]
    return out


def leg_pose(phase: float) -> tuple[float, float]:
    """Angle from vertical (positive: foot forward) and how much the foot is lifted (0 to 1)."""

    if phase < DUTY:  # on the ground: the foot goes back under the body at a steady speed
        return math.atan(math.tan(SWING) * (1 - 2 * phase / DUTY)), 0.0
    s = (phase - DUTY) / (1 - DUTY)
    eased = 0.5 - 0.5 * math.cos(math.pi * s)
    return -SWING + 2 * SWING * eased, math.sin(math.pi * s)


def main(path: str) -> None:
    started = time.perf_counter()
    drawing = Image.open(path).convert("RGB").resize((768, 512))
    rgb = np.asarray(drawing)
    mask, trunk, legs = split(rgb)
    background = Image.fromarray(fill_behind(rgb, morph(mask, 11, ImageFilter.MaxFilter)))
    upper = mask.copy()
    for leg in legs:
        upper &= ~leg
    body = Image.fromarray(np.dstack([rgb, (upper * 255).astype(np.uint8)]), "RGBA")
    rigs, lengths = [], []
    for leg in legs:
        rows, cols = np.nonzero(leg)
        top = rows.min()
        pivot = (float(cols[rows < top + 12].mean()), float(top) + 4)
        root = leg | (morph(leg, 25, ImageFilter.MaxFilter) & trunk)  # overlap so the hip never opens
        sprite = Image.fromarray(np.dstack([rgb, (root * 255).astype(np.uint8)]), "RGBA")
        rigs.append((sprite, pivot))
        lengths.append(rows.max() - pivot[1])
    stride = 2 * float(np.mean(lengths)) * math.tan(SWING)
    speed = stride / (DUTY * PERIOD)  # pixels a second: what keeps a standing foot still
    travel = speed * SECONDS

    writer = subprocess.Popen(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
         "768x512", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
         str(HERE / "walk_preview.mp4")],
        stdin=subprocess.PIPE,
    )
    for index in range(FPS * SECONDS):
        t = index / FPS
        shift = travel / 2 - speed * t  # walks to the left, centred on where the child drew it
        bob = -1.5 * abs(math.sin(2 * math.pi * t / PERIOD))
        frame = background.copy()
        order = (0, 2, 1, 3) if len(legs) == 4 else range(len(legs))
        for rank in order:
            sprite, (px, py) = rigs[rank]
            angle, lift = leg_pose((t / PERIOD + PHASES[rank % 4]) % 1.0)
            # Shear about the hip: the foot moves by the tangent of the angle and keeps its height unless lifted.
            k = math.tan(angle)
            scale = 1 - 0.09 * lift - bob / max(lengths[rank], 1)
            matrix = (1, k / scale, -k * py / scale - shift, 0, 1 / scale, py - (py + bob) / scale)
            turned = sprite.transform(sprite.size, Image.AFFINE, matrix, resample=Image.BICUBIC)
            frame.paste(turned, (0, 0), turned)
        moved = body.transform(body.size, Image.AFFINE, (1, 0, -shift, 0, 1, -bob), resample=Image.BICUBIC)
        frame.paste(moved, (0, 0), moved)
        writer.stdin.write(frame.tobytes())
    writer.stdin.close()
    writer.wait()
    print(f"legs {len(legs)}, travel {travel:.0f} px, {FPS * SECONDS} frames in {time.perf_counter() - started:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1])
