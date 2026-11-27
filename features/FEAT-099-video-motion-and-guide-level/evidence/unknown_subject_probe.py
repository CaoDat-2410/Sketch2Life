"""FEAT-099 research: what can the CPU say and move about a subject it has no rules for?

Throwaway. One generic routine, no knowledge of the subject: find the subject, split off its thin parts (above, beside
or below the trunk) and read its colours. Run on drawings the routine was not written for. Run from the repository root:

    python features/FEAT-099-video-motion-and-guide-level/evidence/unknown_subject_probe.py <drawing.png> ...
"""

from __future__ import annotations

import colorsys
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from part_split_prototype import components, morph  # noqa: E402

W = 480
FONT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 15)
HUES = [(15, "đỏ"), (40, "cam"), (68, "vàng"), (165, "xanh lá"), (255, "xanh dương"), (320, "tím"), (345, "hồng"),
        (361, "đỏ")]


def subject_mask(rgb: np.ndarray) -> np.ndarray:
    paper = np.median(rgb.reshape(-1, 3), axis=0)
    far = np.abs(rgb.astype(int) - paper).sum(axis=2) > 55
    closed = morph(morph(far, 7, ImageFilter.MaxFilter), 7, ImageFilter.MinFilter)
    biggest = components(closed, 400)[0]
    return ~components(~biggest, 1)[0]


def colours(rgb: np.ndarray, mask: np.ndarray) -> list[str]:
    counts: dict[str, int] = {}
    for r, g, b in rgb[mask][::3] / 255.0:
        hue, light, saturation = colorsys.rgb_to_hls(r, g, b)
        if light < 0.22:
            name = "đen"
        elif saturation < 0.25 or light > 0.85:
            continue
        else:
            name = next(label for limit, label in HUES if hue * 360 < limit)
            if name in ("cam", "đỏ") and light < 0.5 and saturation < 0.75:
                name = "nâu"
        counts[name] = counts.get(name, 0) + 1
    total = sum(counts.values()) or 1
    return [name for name, count in sorted(counts.items(), key=lambda kv: -kv[1]) if count / total >= 0.08]


def thin_parts(mask: np.ndarray) -> tuple[np.ndarray, dict[str, list[np.ndarray]]]:
    area = int(mask.sum())
    size = max(9, int(area**0.5 / 6) | 1)  # "thin" is relative to the subject's size
    trunk = morph(morph(mask, size, ImageFilter.MinFilter), size, ImageFilter.MaxFilter) & mask
    pieces = components(trunk, 50)
    if not pieces:
        return mask, {"above": [], "beside": [], "below": []}
    trunk = pieces[0]
    rows, cols = np.nonzero(trunk)
    top, bottom, centre = np.percentile(rows, 20), np.percentile(rows, 80), np.median(cols)
    found: dict[str, list[np.ndarray]] = {"above": [], "beside": [], "below": []}
    for part in components(mask & ~trunk, max(80, area // 120)):
        r, c = np.nonzero(part)
        where = "above" if r.mean() < top else ("below" if r.mean() > bottom else "beside")
        found[where].append(part)
    return trunk, found


def main(paths: list[str]) -> None:
    sheets, report = [], []
    for path in paths:
        started = time.perf_counter()
        image = Image.open(path).convert("RGB")
        image.thumbnail((W, W))
        rgb = np.asarray(image)
        mask = subject_mask(rgb)
        trunk, found = thin_parts(mask)
        names = colours(rgb, mask)
        overlay = rgb.copy()
        overlay[trunk] = (overlay[trunk] * 0.55 + np.array((60, 200, 60)) * 0.45).astype(np.uint8)
        for where, tone in (("above", (40, 90, 230)), ("beside", (240, 150, 0)), ("below", (220, 40, 40))):
            for part in found[where]:
                overlay[part] = (overlay[part] * 0.3 + np.array(tone) * 0.7).astype(np.uint8)
        sheet = Image.new("RGB", (W, W + 46), "white")
        sheet.paste(Image.fromarray(overlay), (0, 0))
        summary = " | ".join(f"{k}: {len(v)}" for k, v in (("trên", found["above"]), ("bên", found["beside"]),
                                                          ("dưới", found["below"])))
        draw = ImageDraw.Draw(sheet)
        draw.text((8, image.height + 4 if image.height < W else W + 4), f"phần mảnh {summary}", font=FONT, fill="black")
        draw.text((8, (image.height if image.height < W else W) + 24), "màu: " + ", ".join(names), font=FONT,
                  fill="black")
        sheets.append(sheet)
        report.append({"drawing": Path(path).name, "colours": names,
                       "thin_parts": {k: len(v) for k, v in found.items()},
                       "subject_share": round(float(mask.mean()), 2),
                       "seconds": round(time.perf_counter() - started, 1)})
    out = Image.new("RGB", (W * len(sheets), W + 46), "white")
    for index, sheet in enumerate(sheets):
        out.paste(sheet, (W * index, 0))
    out.save(HERE / "unknown_probe.png")
    (HERE / "unknown_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in report:
        print(row)


if __name__ == "__main__":
    main(sys.argv[1:])
