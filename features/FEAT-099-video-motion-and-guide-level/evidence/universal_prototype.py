"""FEAT-099 research: one CPU engine with a few motion primitives, tried on four kinds of subject.

Throwaway, not product code. What a vision model would supply (which part is a wheel, a wing, a window) is written by
hand here. Four tiles: vehicle (wheels spin, ground passes), insect (wings flap, floats), space object (launch with
flame and smoke), still object (the drawing appears stroke by stroke, a part is circled while the camera moves in).

Run from backend/:
    PYTHONPATH=src python ../features/FEAT-099-video-motion-and-guide-level/evidence/universal_prototype.py <dir>
where <dir> holds bicycle.png and butterfly.png (synthetic drawings).
"""

from __future__ import annotations

import json
import math
import random
import subprocess
import sys
import time
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from sketch2life.domain.drawing_recipe import parse_recipe

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from part_split_prototype import components, morph  # noqa: E402

SIZE, FPS, SECONDS = 480, 24, 6
RECIPES = Path("src/sketch2life/resources/drawing_recipes")
FONT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)


def paper(colour: tuple[int, int, int] = (246, 244, 238), seed: int = 1) -> Image.Image:
    noise = np.random.default_rng(seed).normal(0, 3, (SIZE, SIZE, 1))
    return Image.fromarray(np.clip(np.array(colour) + noise, 0, 255).astype(np.uint8))


def crayon(draw: ImageDraw.ImageDraw, points, colour, width=5, seed=0) -> None:
    jitter = random.Random(seed)
    for _ in range(3):
        wobbly = [(x + jitter.uniform(-1.4, 1.4), y + jitter.uniform(-1.4, 1.4)) for x, y in points]
        draw.line(wobbly, fill=colour, width=max(1, width - 2), joint="curve")


def label(frame: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle((12, 12, 28 + draw.textlength(text, font=FONT), 48), 8, fill=(255, 255, 255))
    draw.text((20, 18), text, font=FONT, fill=(30, 30, 40))


def layer(rgb: np.ndarray, mask: np.ndarray) -> Image.Image:
    return Image.fromarray(np.dstack([rgb, (mask * 255).astype(np.uint8)]), "RGBA")


def load(path: Path) -> tuple[np.ndarray, np.ndarray]:
    rgb = np.asarray(Image.open(path).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS))
    spread = rgb.max(axis=2).astype(int) - rgb.min(axis=2)
    ink = (spread > 30) | (rgb.max(axis=2) < 180)
    return rgb, morph(morph(ink, 3, ImageFilter.MaxFilter), 3, ImageFilter.MinFilter)


# ------------------------------------------------------------------ vehicle: wheels turn, the road passes
def find_wheel(dark: np.ndarray, guess: tuple[int, int], radius: int) -> tuple[int, int, int, float]:
    """The tyre near a guess (centre, outer radius, share of the ring that is tyre). A low share means "not a wheel"."""

    angles = np.linspace(0, 2 * math.pi, 180, endpoint=False)
    thick = morph(dark, 3, ImageFilter.MaxFilter)
    best = (0.0, guess[0], guess[1], radius)
    for r in range(radius - 14, radius + 17, 2):
        for cx in range(guess[0] - 20, guess[0] + 21, 2):
            for cy in range(guess[1] - 20, guess[1] + 21, 2):
                xs = np.clip((cx + r * np.cos(angles)).astype(int), 0, SIZE - 1)
                ys = np.clip((cy + r * np.sin(angles)).astype(int), 0, SIZE - 1)
                score = float(thick[ys, xs].mean()) + 0.002 * r  # of two good rings the outer one is the tyre
                if score > best[0]:
                    best = (score, cx, cy, r)
    score, cx, cy, r = best
    return cx, cy, r + 5, round(score - 0.002 * r, 2)


def whole_wheel(rgb: np.ndarray, ink: np.ndarray, hidden: np.ndarray, cx: int, cy: int, r: int) -> Image.Image:
    """The wheel alone; what the frame covers is filled from the same distance to the hub elsewhere on the wheel."""

    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    radius, angle = np.hypot(xx - cx, yy - cy), np.arctan2(yy - cy, xx - cx)
    disc = radius <= r + 4
    colour, alpha = rgb.copy(), ink & disc & ~hidden
    todo = disc & hidden
    for step in (1, -1, 2, -2, 3, -3, 4):
        turn = angle + step * math.radians(37)
        sx = np.clip(np.rint(cx + radius * np.cos(turn)).astype(int), 0, SIZE - 1)
        sy = np.clip(np.rint(cy + radius * np.sin(turn)).astype(int), 0, SIZE - 1)
        take = todo & ~hidden[sy, sx]
        colour[take] = rgb[sy[take], sx[take]]
        alpha[take] = ink[sy[take], sx[take]]
        todo &= ~take
    return layer(colour, alpha)


def vehicle(source: Path):
    rgb, mask = load(source)
    bike = components(morph(mask, 5, ImageFilter.MaxFilter), 2000)[0] & mask
    red = (rgb[..., 0].astype(int) - rgb[..., 1] > 70)
    dark = rgb.max(axis=2) < 150
    found = [find_wheel(dark & bike | red & bike, (70, 258), 66), find_wheel(dark & bike | red & bike, (278, 246), 70)]
    wheels = [item[:3] for item in found]
    print({"wheel_ring_share": [item[3] for item in found]})
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    discs = [((xx - cx) ** 2 + (yy - cy) ** 2) <= (r + 4) ** 2 for cx, cy, r in wheels]
    hidden = morph(red, 3, ImageFilter.MaxFilter)
    turning = [whole_wheel(rgb, bike, hidden, cx, cy, r) for cx, cy, r in wheels]
    frame_part = layer(rgb, bike & (hidden | ~(discs[0] | discs[1])))
    ground_y = max(cy + r for cx, cy, r in wheels) + 6
    gate = [ring_agreement(wheel, *circle) for circle, wheel in zip(wheels, turning, strict=True)]
    spin = min(gate) >= 0.75
    print({"wheel_gate": gate, "wheels_turn": spin})
    if not spin:  # a part that fails its gate does not move: the whole bicycle rides, untouched
        turning, frame_part = [], layer(rgb, bike)
    speed = 110.0

    def frame(t: float) -> Image.Image:
        picture = paper((236, 246, 252))
        draw = ImageDraw.Draw(picture)
        for k in range(4):  # far clouds pass slowly
            x = (k * 170 - speed * 0.15 * t) % 620 - 70
            for dx, dy, rr in ((0, 0, 20), (22, -8, 24), (46, 0, 18)):
                draw.ellipse((x + dx - rr, 90 + 18 * (k % 2) + dy - rr, x + dx + rr, 90 + 18 * (k % 2) + dy + rr),
                             fill=(255, 255, 255))
        crayon(draw, [(0, ground_y), (SIZE, ground_y + 2)], (110, 160, 80), 7, 3)
        for k in range(14):  # grass tufts pass at riding speed
            x = (k * 40 - speed * t) % 560 - 40
            crayon(draw, [(x, ground_y + 22), (x + 5, ground_y + 6), (x + 10, ground_y + 22)], (110, 160, 80), 4, k)
        bob = int(round(1.5 * math.sin(2 * math.pi * 3 * t)))
        for (cx, cy, r), wheel in zip(wheels, turning, strict=False):
            turned = wheel.rotate(-math.degrees(speed * t / r), center=(cx, cy), resample=Image.BICUBIC)
            picture.paste(turned, (0, 0), turned)  # angle = distance / radius: the wheel does not slip
        for k in range(7):  # dust behind the rear wheel
            age = (t * 1.7 + k / 7) % 1.0
            x, y, rr = wheels[0][0] - 30 - 90 * age, ground_y - 6 - 22 * age, 4 + 13 * age
            shade = int(205 + 45 * age)
            draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(shade, shade - 8, shade - 22))
        picture.paste(frame_part, (0, bob), frame_part)
        label(picture, "Xe đạp: bánh xe quay" if spin else "Xe đạp: chạy trên đường")
        return picture

    return frame, {"wheels": wheels}


def ring_agreement(wheel: Image.Image, cx: int, cy: int, r: int) -> float:
    """Gate: turned by 40 degrees, does the tyre still lie where the tyre was? Round and well centred: close to 1."""

    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    radius = np.hypot(xx - cx, yy - cy)
    ring = (radius > 0.78 * r) & (radius <= r + 4)
    before = (np.asarray(wheel)[..., 3] > 127) & ring
    after = (np.asarray(wheel.rotate(40, center=(cx, cy), resample=Image.BICUBIC))[..., 3] > 127) & ring
    return round(float((before & after).sum() / max((before | after).sum(), 1)), 2)


# ------------------------------------------------------------------ insect: wings flap, floats
def insect(source: Path):
    rgb, mask = load(source)
    r, g, b = (rgb[..., i].astype(int) for i in range(3))
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    body = mask & (b > g + 45) & (r > g + 15) & (b > r) & (np.abs(xx - SIZE // 2) < 34)
    body |= mask & (yy < 118) & (np.abs(xx - SIZE // 2) < 90) & (b > g + 30)  # feelers
    body = morph(body, 3, ImageFilter.MaxFilter) & mask
    axis = float(np.nonzero(body)[1].mean())
    wings = [layer(rgb, mask & ~body & (xx < axis)), layer(rgb, mask & ~body & (xx >= axis))]
    middle = layer(rgb, body)

    def frame(t: float) -> Image.Image:
        picture = paper((252, 248, 232), 2)
        draw = ImageDraw.Draw(picture)
        for k, x in enumerate(range(40, SIZE, 90)):
            sway = 5 * math.sin(2 * math.pi * 0.5 * t + k)
            crayon(draw, [(x, 478), (x + sway, 436)], (90, 150, 70), 5, k)
            draw.ellipse((x + sway - 11, 424, x + sway + 11, 446), fill=((240, 120, 140), (250, 190, 60))[k % 2])
        beat = abs(math.cos(2 * math.pi * 1.6 * t))
        squeeze = 0.35 + 0.65 * beat  # a wing turning towards the viewer looks narrower
        canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        for side, wing in enumerate(wings):
            lift = (1 - beat) * 0.22 * (1 if side == 0 else -1)
            matrix = (1 / squeeze, 0, axis - axis / squeeze, -lift / squeeze, 1, lift * axis / squeeze)
            moved = wing.transform(wing.size, Image.AFFINE, matrix, resample=Image.BICUBIC)
            canvas.alpha_composite(moved)
        canvas.alpha_composite(middle)
        small = canvas.resize((360, 360), Image.LANCZOS).rotate(
            6 * math.sin(2 * math.pi * 0.35 * t), resample=Image.BICUBIC
        )
        x = 60 + int(48 * math.sin(2 * math.pi * t / SECONDS))
        y = 46 + int(22 * math.sin(2 * math.pi * 0.8 * t) - 7 * beat)
        picture.paste(small, (x, y), small)
        label(picture, "Con bướm: vỗ cánh")
        return picture

    return frame, {"axis": axis}


# ------------------------------------------------------------------ drawings made from the app's own recipes
def recipe_strokes(name: str):
    recipe = parse_recipe(json.loads((RECIPES / f"vi.{name}.simple.json").read_text(encoding="utf-8")))
    return [(step.part, [list(stroke.samples) for stroke in step.strokes]) for step in recipe.steps]


def scaled(points, scale=3.6, dx=60, dy=60):
    return [(dx + x * scale, dy + y * scale) for x, y in points]


def rocket_sprite() -> tuple[Image.Image, Image.Image]:
    colours = {"thân": (225, 232, 240), "cửa sổ": (110, 180, 235), "cánh": (235, 80, 70), "lửa": (250, 150, 40),
               "ống lửa": (120, 120, 130)}
    ship, flame = Image.new("RGBA", (SIZE, SIZE)), Image.new("RGBA", (SIZE, SIZE))
    for index, (part, strokes) in enumerate(recipe_strokes("rocket")):
        target = flame if part == "lửa" else ship
        draw = ImageDraw.Draw(target)
        for stroke in strokes:
            shape = scaled(stroke, 2.6, 110, 90)
            if part in colours and len(shape) > 2:
                draw.polygon(shape, fill=colours[part] + (255,))
            crayon(draw, shape, (40, 60, 130, 255), 5, index)
    return ship, flame


def space():
    ship, flame = rocket_sprite()
    stars = [(random.Random(k).randrange(SIZE), random.Random(k + 99).randrange(SIZE), k) for k in range(60)]

    def frame(t: float) -> Image.Image:
        picture = paper((32, 42, 92), 3)
        draw = ImageDraw.Draw(picture)
        for x, y, k in stars:
            r = 1.2 + 1.6 * (0.5 + 0.5 * math.sin(2 * math.pi * (0.7 * t + k * 0.13)))
            sy = (y + 40 * max(0.0, t - 1.2) ** 1.5) % SIZE
            draw.ellipse((x - r, sy - r, x + r, sy + r), fill=(250, 240, 170))
        rise = 0.5 * 55 * max(0.0, t - 1.2) ** 2  # constant thrust: the height grows with the square of time
        shake = random.Random(int(t * FPS)).uniform(-2, 2) if t < 1.8 else 0.0
        offset = int(min(rise, 80))  # the camera follows once the rocket is high
        draw.arc((-200, 400 + int(rise), 680, 900 + int(rise)), 180, 360, fill=(120, 150, 90), width=60)
        for k in range(18):  # smoke left behind the engine grows and fades
            age = t - 0.12 * k - 0.8
            if 0 < age < 1.6:
                jitter = random.Random(k)
                radius = 8 + 26 * age
                x = 240 + jitter.uniform(-45, 45) * age
                y = 350 + 70 * age + max(0.0, t - 1.2) * 12
                shade = int(235 - 90 * age)
                draw.ellipse((x - radius, y - radius * 0.8, x + radius, y + radius * 0.8),
                             fill=(shade, shade, min(255, shade + 20)))
        if t > 0.8:
            flick = 0.8 + 0.5 * random.Random(int(t * FPS) + 7).random() + (0.3 if t > 1.2 else 0)
            bottom = 90 + 2.6 * 83
            stretched = flame.transform(flame.size, Image.AFFINE, (1, 0, 0, 0, 1 / flick, bottom - bottom / flick),
                                        resample=Image.BICUBIC)
            picture.paste(stretched, (int(shake), -offset), stretched)
        picture.paste(ship, (int(shake), -offset), ship)
        label(picture, "Tên lửa: cất cánh")
        return picture

    return frame, {}


def still():
    steps = recipe_strokes("house")
    strokes = [(part, scaled(stroke, 3.4, 70, 80)) for part, group in steps for stroke in group]
    door = [p for part, shape in strokes if "cửa" in part and "sổ" not in part for p in shape] or strokes[-1][1]
    cx = sum(x for x, _ in door) / len(door)
    cy = sum(y for _, y in door) / len(door)
    reach = max(max(abs(x - cx) for x, _ in door), max(abs(y - cy) for _, y in door)) + 22
    palette = [(200, 90, 60), (60, 90, 170), (70, 140, 80), (150, 80, 160), (220, 140, 40)]

    def frame(t: float) -> Image.Image:
        picture = paper((250, 246, 236), 4)
        draw = ImageDraw.Draw(picture)
        crayon(draw, [(0, 410), (SIZE, 412)], (110, 160, 80), 7, 5)
        total = sum(len(shape) for _, shape in strokes)
        budget = total * min(1.0, t / 2.8)  # the drawing appears stroke by stroke
        for index, (_, shape) in enumerate(strokes):
            count = int(min(len(shape), budget))
            budget -= len(shape)
            if count > 1:
                crayon(draw, shape[:count], palette[index % 5], 6, index)
            if budget <= 0:
                break
        if t > 3.2:  # the named part is circled, as a teacher would
            sweep = min(1.0, (t - 3.2) / 0.8)
            ring = [(cx + reach * math.cos(a), cy + reach * math.sin(a))
                    for a in np.linspace(-1.6, -1.6 + 2 * math.pi * sweep, max(2, int(70 * sweep)))]
            crayon(draw, ring, (240, 60, 60), 8, 9)
        zoom = 1 + 0.35 * (0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, t - 3.6) / 1.8)))
        side = SIZE / zoom
        fx = min(max(240 + (cx - 240) * (zoom - 1) / 0.35 - side / 2, 0), SIZE - side)
        fy = min(max(240 + (cy - 240) * (zoom - 1) / 0.35 - side / 2, 0), SIZE - side)
        picture = picture.resize((SIZE, SIZE), Image.BICUBIC, box=(fx, fy, fx + side, fy + side))
        label(picture, "Ngôi nhà: đây là cửa")
        return picture

    return frame, {}


def main(directory: Path) -> None:
    tiles = [vehicle(directory / "bicycle.png"), insect(directory / "butterfly.png"), space(), still()]
    print({"wheels": tiles[0][1]["wheels"]})
    writer = subprocess.Popen(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
         f"{SIZE * 2}x{SIZE * 2}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p",
         str(HERE / "universal_preview.mp4")],
        stdin=subprocess.PIPE,
    )
    spent = [0.0] * 4
    for index in range(FPS * SECONDS):
        sheet = Image.new("RGB", (SIZE * 2, SIZE * 2))
        for slot, (render, _) in enumerate(tiles):
            started = time.perf_counter()
            sheet.paste(render(index / FPS), ((slot % 2) * SIZE, (slot // 2) * SIZE))
            spent[slot] += time.perf_counter() - started
        writer.stdin.write(sheet.tobytes())
    writer.stdin.close()
    writer.wait()
    names = ["vehicle", "insect", "space", "still"]
    print({name: round(value, 1) for name, value in zip(names, spent, strict=True)}, "seconds for 6 s each at 480x480")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
