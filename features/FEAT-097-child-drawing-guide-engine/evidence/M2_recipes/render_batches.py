"""Draw the phase-2 recipes batch by batch for the owner's review (FEAT-097).

    backend/.venv/Scripts/python.exe features/FEAT-097-child-drawing-guide-engine/evidence/M2_recipes/render_batches.py

For each batch and level it writes one step-by-step sheet, plus one overview of the finished pictures
at both levels. A local drawing of the data, not a screenshot of the app. Start marks follow the app:
dots of a new step are solid and strokes are numbered only when a step has at least two to order.
"""  # noqa: E501 - the command above is one line

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / "M0_recipes"))
sys.path.insert(0, str(ROOT / "backend" / "src"))

from render_recipes import BOLD, DONE, FONT, NEW, SS, TILE, K, dashed, marker  # noqa: E402
from sketch2life.domain.drawing_recipe import check_recipe, parse_recipe  # noqa: E402

BATCHES = {
    "batch1_animals_birds": (
        "cat",
        "deer",
        "elephant",
        "fish",
        "horse",
        "rabbit",
        "dove",
        "duck",
        "owl",
        "parrot",
        "peacock",
        "sparrow",
        "swan",
    ),
    "batch2_insects_plants": (
        "ant",
        "bee",
        "caterpillar",
        "dragonfly",
        "ladybug",
        "flower",
        "snail",
        "tree",
    ),
    "batch3_sea_vehicles": (
        "crab",
        "dolphin",
        "octopus",
        "seahorse",
        "starfish",
        "whale",
        "airplane",
        "ambulance",
        "bicycle",
        "boat",
        "bus",
        "car",
        "scooter",
        "train",
        "truck",
    ),
    "batch4_sky_nature": (
        "leaf",
        "mushroom",
        "rock",
        "cloud",
        "rainbow",
        "pinecone",
        "shell",
        "rocket",
        "planet",
        "moon",
        "star",
        "sun",
        "astronaut",
        "satellite",
        "comet",
        "telescope",
        "raindrop",
        "windmill",
        "puddle",
        "lightning",
        "thermometer",
        "nest",
        "grasshopper",
        "firefly",
        "beetle",
    ),
    "batch5_tales_toys": (
        "castle",
        "dragon",
        "unicorn",
        "fairy",
        "crown",
        "magic_book",
        "carriage",
        "wand",
        "pumpkin",
        "teddy_bear",
        "ball",
        "blocks",
        "kite",
        "spinning_top",
        "puzzle",
        "doll",
    ),
    "batch6_home_kitchen": (
        "cup",
        "chair",
        "lamp",
        "clock",
        "book",
        "fan",
        "pot",
        "vase",
        "pillow",
        "spoon",
        "bowl",
        "plate",
        "chopsticks",
        "kettle",
        "rice_cooker",
        "lunchbox",
        "apron",
        "water_bottle",
    ),
    "batch7_food_school": (
        "banana",
        "mango",
        "orange",
        "watermelon",
        "rice_bowl",
        "bread",
        "egg",
        "carrot",
        "corn",
        "pencil",
        "notebook",
        "backpack",
        "ruler",
        "crayon",
        "blackboard",
        "eraser",
        "desk",
    ),
    "batch8_town_farm": (
        "house",
        "apartment",
        "park_bench",
        "mailbox",
        "streetlight",
        "shop",
        "bridge",
        "traffic_light",
        "market",
        "cow",
        "pig",
        "goat",
        "tractor",
        "barn",
        "hay_bale",
        "watering_can",
    ),
    "batch9_clothes_music": (
        "hat",
        "shirt",
        "trousers",
        "socks",
        "shoes",
        "raincoat",
        "umbrella",
        "scarf",
        "dress",
        "drum",
        "guitar",
        "flute",
        "piano",
        "tambourine",
        "maracas",
        "xylophone",
        "bell",
        "trumpet",
    ),
}
LEVEL_LABELS = {"beginner": "3-5 tuổi", "simple": "6-10 tuổi"}
FOLDER = ROOT / "backend" / "src" / "sketch2life" / "resources" / "drawing_recipes"


def tile(recipe, upto: int) -> Image.Image:
    image = Image.new("RGB", (TILE * SS, TILE * SS), "white")
    draw = ImageDraw.Draw(image)
    for number, step in enumerate(recipe.steps[: upto + 1]):
        marked = [stroke for stroke in step.strokes if stroke.shape != "dot"]
        for stroke in step.strokes:
            points = [(x * K, y * K) for x, y in stroke.samples]
            if number < upto:
                draw.line(points, fill=DONE, width=int(1.8 * K), joint="curve")
            elif stroke.shape == "dot":
                draw.line(points, fill=NEW, width=int(2.2 * K), joint="curve")
            else:
                dashed(draw, points)
                marker(draw, points, marked.index(stroke) + 1 if len(marked) > 1 else None)
    return image.resize((TILE, TILE), Image.Resampling.LANCZOS)


def save(sheet: Image.Image, path: Path) -> None:
    """Few colours are enough for line drawings and keep the evidence small."""

    sheet.quantize(colors=48, method=Image.Quantize.MEDIANCUT).save(path, optimize=True)


def load(subject: str, level: str):
    return parse_recipe(
        json.loads((FOLDER / f"vi.{subject}.{level}.json").read_text(encoding="utf-8"))
    )


def wrapped(draw: ImageDraw.ImageDraw, text: str) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        if current and draw.textlength(f"{current} {word}", font=FONT) > TILE - 6:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    return [*lines, current][:2]


def steps_sheet(batch: str, level: str, subjects: list[str]) -> None:
    recipes = [load(subject, level) for subject in subjects]
    columns = max(len(recipe.steps) for recipe in recipes) + 1
    sheet = Image.new(
        "RGB", (columns * (TILE + 10) + 10, len(recipes) * (TILE + 80) + 6), "#eef1f8"
    )
    draw = ImageDraw.Draw(sheet)
    for row, recipe in enumerate(recipes):
        y = row * (TILE + 80) + 6
        strokes = sum(len(step.strokes) for step in recipe.steps)
        broken = check_recipe(recipe) or "không"
        title = (
            f"{recipe.title} ({LEVEL_LABELS[level]}): "
            f"{len(recipe.steps)} bước, {strokes} nét, lỗi: {broken}"
        )
        draw.text((10, y), title, fill="#111", font=BOLD)
        for index, step in enumerate(recipe.steps):
            x = 10 + index * (TILE + 10)
            sheet.paste(tile(recipe, index), (x, y + 26))
            for number, text in enumerate(wrapped(draw, f"{index + 1}. {step.instruction}")):
                draw.text((x + 2, y + 26 + TILE + 4 + number * 18), text, fill="#222", font=FONT)
        x = 10 + len(recipe.steps) * (TILE + 10)
        sheet.paste(tile(recipe, len(recipe.steps)), (x, y + 26))
        draw.text((x + 2, y + 26 + TILE + 4), "Hình xong", fill="#222", font=FONT)
    save(sheet, HERE / f"{batch}_{level}.png")
    print(batch, level, sheet.size)


def overview(batch: str, subjects: list[str]) -> None:
    pairs = 3
    cell_width, cell_height = TILE * 2 + 16, TILE + 30
    rows = (len(subjects) + pairs - 1) // pairs
    sheet = Image.new(
        "RGB", (pairs * (cell_width + 16) + 16, rows * (cell_height + 10) + 10), "#cfd6e8"
    )
    draw = ImageDraw.Draw(sheet)
    for index, subject in enumerate(subjects):
        x = 16 + (index % pairs) * (cell_width + 16)
        y = 10 + (index // pairs) * (cell_height + 10)
        for position, level in enumerate(LEVEL_LABELS):
            recipe = load(subject, level)
            left = x + position * (TILE + 16)
            draw.text((left, y), f"{recipe.title} ({LEVEL_LABELS[level]})", fill="#111", font=BOLD)
            sheet.paste(tile(recipe, len(recipe.steps)), (left, y + 26))
    save(sheet, HERE / f"{batch}_finished.png")
    print(batch, "finished", sheet.size)


def main() -> None:
    wanted = sys.argv[1:] or list(BATCHES)
    for batch, subjects in BATCHES.items():
        if batch not in wanted:
            continue
        overview(batch, list(subjects))
        for level in LEVEL_LABELS:
            steps_sheet(batch, level, list(subjects))


if __name__ == "__main__":
    main()
