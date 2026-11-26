"""Build the synthetic experiment inputs and the speed specs (FEAT-094 phase 1).

Usage: python make_inputs.py <bike_keyframe.png> <chick_drawing.jpg>
Both sources are synthetic drawings made for this project; no child data is used.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from prompts import BIKE, CHICK, motion_prompt

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
CANVAS = (1280, 768)

def bike_keyframe(source: Path) -> Image.Image:
    """A frame of the FEAT-093 live video: replace its white bands with the neighbouring rows."""

    pixels = np.asarray(Image.open(source).convert("RGB").resize(CANVAS)).copy()
    pixels[:25] = pixels[25]
    pixels[-25:] = pixels[-26]
    return Image.fromarray(pixels)


def paper_canvas(source: Path, shift: tuple[int, int] = (0, 0)) -> Image.Image:
    """The drawing fitted on its own paper colour; ``shift`` moves the chick (not the sun or the grass)."""

    drawing = Image.open(source).convert("RGB")
    drawing.thumbnail((CANVAS[0] - 96, CANVAS[1] - 48), Image.Resampling.LANCZOS)
    paper = tuple(int(v) for v in np.median(np.asarray(drawing)[:20, -20:].reshape(-1, 3), axis=0))
    canvas = Image.new("RGB", CANVAS, paper)
    origin = ((CANVAS[0] - drawing.width) // 2, (CANVAS[1] - drawing.height) // 2)
    canvas.paste(drawing, origin)
    if shift == (0, 0):
        return canvas
    scale = drawing.width / 1200
    pixels = np.asarray(canvas).astype(np.int16)
    yy, xx = np.mgrid[0:CANVAS[1], 0:CANVAS[0]]
    sx, sy = (xx - origin[0]) / scale, (yy - origin[1]) / scale  # source drawing coordinates
    ink = np.abs(pixels - np.array(paper)).sum(axis=2) > 24
    # Body, head and tail above the grass, without the sun in the top-left corner.
    body = (sx >= 90) & (sx < 1000) & (sy >= 180) & (sy < 955) & ~((sx < 320) & (sy < 300))
    # The legs reach into the grass: take only their orange pixels there.
    orange = (pixels[..., 0] > 190) & (pixels[..., 1] > 100) & (pixels[..., 1] < 200) & (pixels[..., 2] < 130)
    legs = (sx >= 400) & (sx < 700) & (sy >= 955) & (sy < 1065) & orange
    chick = ink & (body | legs)
    moved = pixels.copy()
    # Erase a slightly wider area so no pale outline stays behind; the grass keeps its green pixels.
    wider = np.asarray(Image.fromarray(chick.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))) > 0
    green = (pixels[..., 1] > pixels[..., 0] + 25) & (pixels[..., 1] > pixels[..., 2] + 10)
    moved[wider & ~green] = paper
    ys, xs = np.nonzero(chick)
    moved[ys + shift[1], xs + shift[0]] = pixels[ys, xs]
    return Image.fromarray(moved.astype(np.uint8))


def main(bike: str, chick: str) -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    bike_keyframe(Path(bike)).save(INPUTS / "bike_start.png")
    paper_canvas(Path(chick)).save(INPUTS / "chick_start.png")
    paper_canvas(Path(chick), shift=(130, -40)).save(INPUTS / "chick_end.png")

    scene = {"image": "chick_start.png", "prompt": motion_prompt(CHICK), "seed": 940101}
    speed = [
        {**scene, "name": "warm-6s", "seconds": 6.0},
        {**scene, "name": "again-6s", "seconds": 6.0, "image": "bike_start.png", "prompt": motion_prompt(BIKE)},
        {**scene, "name": "long-10s", "seconds": 10.0},
    ]
    profiles = {
        "baseline": {"offload": "cpu"},
        "resident": {"offload": "none", "resident": True, "prompt_cache": True},
        "compile": {"offload": "none", "resident": True, "prompt_cache": True, "compile": True},
    }
    for name, profile in profiles.items():
        spec = {"profile": profile, "scenes": speed}
        (INPUTS / f"speed_{name}.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print("inputs written to", INPUTS)


if __name__ == "__main__":
    main(*sys.argv[1:3])
