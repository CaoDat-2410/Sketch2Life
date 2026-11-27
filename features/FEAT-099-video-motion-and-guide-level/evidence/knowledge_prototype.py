"""FEAT-099 research: can a CPU engine show a fact, not only move the drawing? Three facts on the child's own deer.

Throwaway, not product code. Count (the four legs are numbered as they are counted), cycle (the child's own antlers
fall in late winter and grow back), eating (leaves are brought to the deer and disappear bite by bite). Which part is
which comes from the shapes in the drawing; the facts and their timing are written by hand.

Run from the repository root:
    python features/FEAT-099-video-motion-and-guide-level/evidence/knowledge_prototype.py <drawing.png>
"""

from __future__ import annotations

import math
import random
import subprocess
import sys
import time
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from part_split_prototype import components, morph  # noqa: E402
from walk_prototype import fill_behind, split  # noqa: E402

W, H, FPS, PART = 768, 512, 24, 5.0
BIG = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 24)
NUMBER = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)


def layer(rgb: np.ndarray, mask: np.ndarray) -> Image.Image:
    return Image.fromarray(np.dstack([rgb, (mask * 255).astype(np.uint8)]), "RGBA")


def caption(picture: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(picture)
    width = draw.textlength(text, font=BIG)
    draw.rounded_rectangle(((W - width) / 2 - 16, H - 54, (W + width) / 2 + 16, H - 12), 12, fill=(255, 255, 255))
    draw.text(((W - width) / 2, H - 47), text, font=BIG, fill=(35, 35, 50))


def glow(picture: Image.Image, mask: np.ndarray, strength: float) -> None:
    ring = morph(mask, 11, ImageFilter.MaxFilter) & ~mask
    soft = Image.fromarray((ring * int(255 * strength)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))
    picture.paste(Image.new("RGB", (W, H), (255, 190, 0)), (0, 0), soft)


def ease(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def main(path: str) -> None:
    started = time.perf_counter()
    drawing = Image.open(path).convert("RGB").resize((W, H))
    rgb = np.asarray(drawing)
    mask, trunk, legs = split(rgb)
    antlers = [part for part in components(mask & ~trunk, 2000) if np.nonzero(part)[0].max() < 125]
    print(f"legs {len(legs)}, antlers {len(antlers)}")
    crown = np.zeros_like(mask)
    for part in antlers:
        crown |= part
    paper = Image.fromarray(fill_behind(rgb, morph(mask, 11, ImageFilter.MaxFilter)))
    bare = Image.fromarray(fill_behind(rgb, morph(crown, 11, ImageFilter.MaxFilter)))  # the drawing without antlers
    deer = layer(rgb, mask)

    def count(t: float) -> Image.Image:
        picture = drawing.copy()
        said = min(int((t - 0.8) / 0.85) + 1, len(legs)) if t > 0.8 else 0
        for index in range(said):
            leg = legs[index]
            since = t - 0.8 - 0.85 * index
            glow(picture, leg, 1.0 if since < 0.85 else 0.55)
            rows, cols = np.nonzero(leg)
            x, y = float(cols.mean()), float(rows.max()) - 50
            r = 24 * (1 + 0.35 * max(0.0, 1 - since / 0.25))
            draw = ImageDraw.Draw(picture)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255), outline=(230, 120, 0), width=4)
            draw.text((x, y), str(index + 1), font=NUMBER, fill=(200, 80, 0), anchor="mm")
        words = ["một", "hai", "ba", "bốn"]
        text = "Hươu có mấy cái chân?" if not said else "Chân hươu: " + ", ".join(words[:said])
        caption(picture, "Hươu có bốn chân!" if t > 4.2 else text)
        return picture

    def cycle(t: float) -> Image.Image:
        season = 0 if t < 2.2 else (1 if t < 3.7 else 2)
        picture = bare.copy()
        tint = [(205, 222, 245), (222, 245, 214), (255, 238, 196)][season]
        picture = Image.blend(picture, Image.new("RGB", (W, H), tint), 0.28)
        draw = ImageDraw.Draw(picture)
        if season == 0:
            for k in range(70):  # snow
                jitter = random.Random(k)
                x, y = jitter.randrange(W), (jitter.randrange(H) + 70 * t) % H
                draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 255, 255))
        for index, part in enumerate(antlers):
            piece = layer(rgb, part)
            rows, cols = np.nonzero(part)
            base = (float(cols[rows > rows.max() - 6].mean()), float(rows.max()))
            if season == 0:
                fall = max(0.0, t - 0.8 - 0.35 * index)
                drop = 0.5 * 520 * fall**2  # it falls under gravity and comes to rest on the grass
                drop = min(drop, 470 - base[1])
                turn = (1 if index else -1) * min(95.0, 170 * fall)
                turned = piece.rotate(turn, center=base, resample=Image.BICUBIC)
                side = (1 if index else -1) * int(min(60.0, 90 * fall))
                picture.paste(turned, (side, int(drop)), turned)
            else:  # it grows again from the head upwards
                grown = 0.45 * ease((t - 2.4) / 1.3) + 0.55 * ease((t - 3.7) / 0.9)
                visible = part & (np.mgrid[0:H, 0:W][0] >= rows.max() - grown * (rows.max() - rows.min()))
                bud = layer(rgb, visible)
                picture.paste(bud, (0, 0), bud)
                if season == 2 and t > 4.5:
                    glow(picture, part, 0.8)
        draw = ImageDraw.Draw(picture)
        for k, name in enumerate(["Cuối đông", "Mùa xuân", "Mùa hè"]):
            x = 470 + 100 * k
            draw.ellipse((x - 10, 34, x + 10, 54), fill=(230, 120, 0) if k == season else (190, 190, 190))
            draw.text((x, 70), name, font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 17),
                      fill=(40, 40, 55), anchor="mm")
        caption(picture, ["Cuối mùa đông, sừng hươu rụng xuống.", "Mùa xuân, sừng mới bắt đầu mọc.",
                          "Mùa hè, sừng lớn dần lên."][season])
        return picture

    leaves = []
    jitter = random.Random(5)
    for k in range(16):
        leaves.append((78 + jitter.uniform(-52, 52), 262 + jitter.uniform(-62, 55), jitter.uniform(0, 180), k))
    sprig = Image.new("RGBA", (44, 44), (0, 0, 0, 0))
    pen = ImageDraw.Draw(sprig)
    pen.ellipse((8, 15, 36, 29), fill=(110, 185, 80, 255), outline=(50, 120, 50, 255), width=3)
    pen.line((6, 22, 38, 22), fill=(50, 120, 50, 255), width=2)

    def eat(t: float) -> Image.Image:
        picture = paper.copy()
        draw = ImageDraw.Draw(picture)
        arrive = ease(t / 0.9)
        draw.line([(40, 450), (60, 350), (78, 262)], fill=(130, 90, 50), width=9)
        reach = -70 * ease((t - 1.0) / 1.1)  # the deer steps up to the leaves
        eaten = int(max(0.0, t - 2.1) / 0.26)
        order = sorted(leaves, key=lambda leaf: -leaf[0])  # the nearest leaves go first
        for number, (x, y, turn, k) in enumerate(order):
            if number < eaten:
                continue
            piece = sprig.rotate(turn + 5 * math.sin(2 * math.pi * t + k), resample=Image.BICUBIC)
            picture.paste(piece, (int(x - 22 - 140 * (1 - arrive)), int(y - 22)), piece)
        bob = 3 * abs(math.sin(2 * math.pi * 1.9 * t)) if eaten else 0.0
        picture.paste(deer, (int(reach), int(bob)), deer)
        if 0 < eaten < 11:
            draw = ImageDraw.Draw(picture)
            mouth = (150 + reach, 232 + bob)
            for k in range(5):
                a = 2 * math.pi * k / 5 + t * 7
                draw.ellipse((mouth[0] + 20 * math.cos(a) - 3, mouth[1] + 14 * math.sin(a) - 3,
                              mouth[0] + 20 * math.cos(a) + 3, mouth[1] + 14 * math.sin(a) + 3), fill=(100, 170, 70))
        if 0.9 < t < 2.4:
            draw = ImageDraw.Draw(picture)
            draw.text((78, 165), "lá non", font=BIG, fill=(40, 110, 40), anchor="mm")
            draw.line([(78, 182), (78, 204)], fill=(40, 110, 40), width=4)
        caption(picture, "Hươu thích ăn lá non." if t < 3.6 else "Lá non giúp hươu lớn khỏe.")
        return picture

    writer = subprocess.Popen(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
         f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
         str(HERE / "knowledge_preview.mp4")],
        stdin=subprocess.PIPE,
    )
    for scene in (count, cycle, eat):
        for index in range(int(FPS * PART)):
            writer.stdin.write(scene(index / FPS).tobytes())
    writer.stdin.close()
    writer.wait()
    print(f"15 s of video in {time.perf_counter() - started:.1f} s of CPU")


if __name__ == "__main__":
    main(sys.argv[1])
