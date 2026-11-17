"""Cheap visual guard against charging for repeated whiteboard scene animation.

This is a conservative near-duplicate check, not a semantic scene-quality score.
It compares visible marks with a small spatial tolerance so color changes or a
slightly shifted redraw of the same illustration do not count as a new beat.
"""

from __future__ import annotations

from pathlib import Path


def near_duplicate_scene(previous: str | Path, current: str | Path) -> bool:
    try:
        import numpy as np
        from PIL import Image, ImageFilter
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError("scene comparison requires Pillow and NumPy") from error

    def foreground(path: str | Path):
        with Image.open(path) as source:
            sampled = source.convert("RGB").resize((128, 128), Image.Resampling.LANCZOS)
        pixels = np.asarray(sampled, dtype=np.int16)
        border = np.concatenate((
            pixels[0, :, :], pixels[-1, :, :], pixels[:, 0, :], pixels[:, -1, :]
        ))
        background = np.median(border, axis=0)
        return (np.abs(pixels - background).max(axis=2) > 42)

    def dilate(mask):
        image = Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), "L")
        return np.asarray(image.filter(ImageFilter.MaxFilter(5))) > 0

    before = foreground(previous)
    after = foreground(current)
    if int(before.sum()) < 40 or int(after.sum()) < 40:
        return False
    before_coverage = float((before & dilate(after)).sum()) / float(before.sum())
    after_coverage = float((after & dilate(before)).sum()) / float(after.sum())
    return min(before_coverage, after_coverage) >= 0.94


__all__ = ["near_duplicate_scene"]
