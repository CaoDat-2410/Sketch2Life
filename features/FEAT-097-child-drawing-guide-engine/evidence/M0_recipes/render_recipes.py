"""Draw every stored recipe step by step, the way the app shows it, for the owner's review (FEAT-097).

    backend/.venv/Scripts/python.exe features/FEAT-097-child-drawing-guide-engine/evidence/M0_recipes/render_recipes.py

Writes one picture per level beside this script. A local drawing of the data, not a screenshot of the app.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from sketch2life.domain.drawing_recipe import check_recipe, parse_recipe  # noqa: E402

TILE, SS = 260, 3
K = TILE * SS / 100
DONE, NEW, DOT = "#17243e", "#3867f6", "#12924f"
FONT = ImageFont.truetype("arial.ttf", 14)
BOLD = ImageFont.truetype("arialbd.ttf", 17)


def dashed(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]]) -> None:
    travelled = 0.0
    for a, b in zip(points, points[1:], strict=False):
        if int(travelled / (3.0 * K)) % 2 == 0:
            draw.line([a, b], fill=NEW, width=int(2.2 * K))
        travelled += math.dist(a, b)


def marker(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], number: int | None) -> None:
    total = sum(math.dist(a, b) for a, b in zip(points, points[1:], strict=False))
    target, travelled, index = min(total * 0.45, 9 * K), 0.0, 1
    for index in range(1, len(points)):
        travelled += math.dist(points[index - 1], points[index])
        if travelled >= target:
            break
    (ax, ay), (bx, by) = points[index - 1], points[index]
    angle = math.atan2(by - ay, bx - ax)
    tip = (bx + 2.2 * K * math.cos(angle), by + 2.2 * K * math.sin(angle))
    wings = [(tip[0] - 4 * K * math.cos(angle + s), tip[1] - 4 * K * math.sin(angle + s)) for s in (0.55, -0.55)]
    draw.polygon([tip, *wings], fill=DOT)
    x, y = points[0]
    r = 2.6 * K
    draw.ellipse([x - r, y - r, x + r, y + r], fill=DOT)
    if number is not None:
        draw.text((x, y), str(number), fill="white", anchor="mm", font=ImageFont.truetype("arialbd.ttf", int(3.8 * K)))


def tile(recipe, upto: int) -> Image.Image:
    image = Image.new("RGB", (TILE * SS, TILE * SS), "white")
    draw = ImageDraw.Draw(image)
    for number, step in enumerate(recipe.steps[: upto + 1]):
        for position, stroke in enumerate(step.strokes, start=1):
            points = [(x * K, y * K) for x, y in stroke.samples]
            if number < upto:
                draw.line(points, fill=DONE, width=int(1.8 * K), joint="curve")
            else:
                dashed(draw, points)
                if stroke.shape != "dot":
                    marker(draw, points, position if len(step.strokes) > 1 else None)
    return image.resize((TILE, TILE), Image.Resampling.LANCZOS)


def main() -> None:
    folder = ROOT / "backend" / "src" / "sketch2life" / "resources" / "drawing_recipes"
    for level in ("beginner", "simple"):
        recipes = [parse_recipe(json.loads(p.read_text(encoding="utf-8"))) for p in sorted(folder.glob(f"*.{level}.json"))]
        columns = max(len(recipe.steps) for recipe in recipes) + 1
        sheet = Image.new("RGB", (columns * (TILE + 10) + 10, len(recipes) * (TILE + 80) + 6), "#eef1f8")
        draw = ImageDraw.Draw(sheet)
        for row, recipe in enumerate(recipes):
            y = row * (TILE + 80) + 6
            strokes = sum(len(step.strokes) for step in recipe.steps)
            title = f"{recipe.title} ({level}): {len(recipe.steps)} bước, {strokes} nét, lỗi: {check_recipe(recipe) or 'không'}"
            draw.text((10, y), title, fill="#111", font=BOLD)
            for index, step in enumerate(recipe.steps):
                x = 10 + index * (TILE + 10)
                sheet.paste(tile(recipe, index), (x, y + 26))
                words, line, lines = step.instruction.split(), "", []
                for word in words:
                    if draw.textlength(f"{line} {word}", font=FONT) > TILE - 6 and line:
                        lines.append(line)
                        line = word
                    else:
                        line = f"{line} {word}".strip()
                for n, text in enumerate([*lines, line][:2]):
                    draw.text((x + 2, y + 26 + TILE + 4 + n * 18), f"{index + 1}. {text}" if n == 0 else text, fill="#222", font=FONT)
            x = 10 + len(recipe.steps) * (TILE + 10)
            sheet.paste(tile(recipe, len(recipe.steps)), (x, y + 26))
            draw.text((x + 2, y + 26 + TILE + 4), "Hình xong", fill="#222", font=FONT)
        sheet.save(HERE / f"recipes_{level}.png")
        print(level, sheet.size)


if __name__ == "__main__":
    main()
