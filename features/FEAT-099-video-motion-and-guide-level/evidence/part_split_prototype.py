"""FEAT-099 research: can the legs of a drawn four-legged animal be cut and turned about the hip on the CPU?

A throwaway feasibility check on the synthetic deer drawing, not product code. The subject mask here is a colour
heuristic (the worker has a SAM mask). Run from the repository root:

    python features/FEAT-099-video-motion-and-guide-level/evidence/part_split_prototype.py <drawing.png>
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent


def components(mask: np.ndarray, minimum: int) -> list[np.ndarray]:
    seen = np.zeros_like(mask)
    found = []
    for y, x in zip(*np.nonzero(mask), strict=True):
        if seen[y, x]:
            continue
        queue, pixels = deque([(y, x)]), []
        seen[y, x] = True
        while queue:
            cy, cx = queue.popleft()
            pixels.append((cy, cx))
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        if len(pixels) >= minimum:
            part = np.zeros_like(mask)
            rows, cols = zip(*pixels, strict=True)
            part[list(rows), list(cols)] = True
            found.append(part)
    return sorted(found, key=lambda part: -int(part.sum()))


def morph(mask: np.ndarray, size: int, kind: type) -> np.ndarray:
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(kind(size))) > 127


def subject_mask(rgb: np.ndarray) -> np.ndarray:
    r, g, b = (rgb[..., i].astype(int) for i in range(3))
    brown = (r - g > 18) & (r - b > 28)
    dark = (r < 95) & (g < 95) & (b < 95)
    # Light crayon (muzzle, belly) and pencil outlines count too; grass and leaves do not.
    spread = rgb.max(axis=2).astype(int) - rgb.min(axis=2).astype(int)
    ink = ((spread > 24) | (rgb.max(axis=2) < 170)) & ~(g > r + 6)
    seed = morph(morph(brown | dark | ink, 7, ImageFilter.MaxFilter), 5, ImageFilter.MinFilter)
    body = components(seed, 500)[0]
    outside = components(~body, 1)[0]  # the page around the subject; what it does not reach is inside it
    return ~outside


def main(path: str) -> None:
    drawing = Image.open(path).convert("RGB").resize((768, 512))
    rgb = np.asarray(drawing)
    mask = subject_mask(rgb)
    # Opening removes what is thinner than the filter: the legs (and antlers). The rest is trunk, neck and head.
    trunk = morph(morph(mask, 33, ImageFilter.MinFilter), 33, ImageFilter.MaxFilter) & mask
    trunk = components(trunk, 200)[0]
    thin = mask & ~trunk
    middle = np.nonzero(trunk)[0].mean()
    legs = []
    for part in components(thin, 700):
        rows, cols = np.nonzero(part)
        if rows.mean() > middle and (rows.max() - rows.min()) > 1.4 * (cols.max() - cols.min()) * 0.7:
            legs.append(part)
    print(f"subject pixels {int(mask.sum())}, leg parts found {len(legs)}")

    overlay = rgb.copy()
    colours = [(220, 40, 40), (40, 90, 220), (240, 160, 0), (150, 40, 200), (0, 160, 120), (90, 90, 90)]
    overlay[trunk] = (overlay[trunk] * 0.5 + np.array((60, 200, 60)) * 0.5).astype(np.uint8)
    for index, leg in enumerate(legs):
        overlay[leg] = (overlay[leg] * 0.3 + np.array(colours[index % 6]) * 0.7).astype(np.uint8)

    # Poses: each leg turns about its hip (middle of its top rows); the trunk is drawn over the hips.
    paper = tuple(int(v) for v in np.median(rgb[~mask], axis=0))
    clean = rgb.copy()
    clean[morph(mask, 9, ImageFilter.MaxFilter)] = paper
    order = sorted(range(len(legs)), key=lambda i: np.nonzero(legs[i])[1].mean())
    poses = []
    for angles in ((14, -12, 12, -14), (-12, 14, -14, 12)):
        frame = Image.fromarray(clean.copy())
        for rank, index in enumerate(order):
            leg = legs[index]
            rows, cols = np.nonzero(leg)
            top = rows.min()
            pivot = (float(cols[rows < top + 12].mean()), float(top))
            root = leg | (morph(leg, 25, ImageFilter.MaxFilter) & trunk)  # overlap so the hip does not open
            sprite = Image.fromarray(np.dstack([rgb, (root * 255).astype(np.uint8)]), "RGBA")
            turned = sprite.rotate(angles[rank % 4], resample=Image.BICUBIC, center=pivot)
            frame.paste(turned, (0, 0), turned)
        upper = mask.copy()
        for leg in legs:
            upper &= ~leg
        frame.paste(drawing, (0, 0), Image.fromarray((upper * 255).astype(np.uint8)))
        poses.append(frame)

    sheet = Image.new("RGB", (768 * 4, 512), "white")
    for index, picture in enumerate([drawing, Image.fromarray(overlay), *poses]):
        sheet.paste(picture, (768 * index, 0))
        ImageDraw.Draw(sheet).text((768 * index + 10, 8), ["drawing", "parts", "pose A", "pose B"][index], fill="black")
    sheet.resize((1536, 256)).save(HERE / "part_split_small.png")
    sheet.save(HERE / "part_split.png")


if __name__ == "__main__":
    main(sys.argv[1])
