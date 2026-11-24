"""Synthetic (no real child data) eval drawings for FEAT-087 G6.

Each drawing is flat crayon-style line art on paper, with a main subject and one secondary
object. ``manifest.json`` records the expected roles and the script outcome used by A4.
"""

import json
import pathlib

from PIL import Image, ImageDraw

PAPER = (246, 240, 228)
OUT = pathlib.Path(__file__).parent


def _canvas():
    image = Image.new("RGB", (1024, 576), PAPER)
    return image, ImageDraw.Draw(image)


def turtle_leaf():
    image, d = _canvas()
    d.ellipse((150, 220, 400, 420), fill=(122, 190, 123), outline=(30, 90, 40), width=5)
    d.ellipse((380, 270, 450, 340), fill=(140, 205, 140), outline=(30, 90, 40), width=5)
    d.rectangle((190, 400, 230, 450), fill=(122, 190, 123), outline=(30, 90, 40), width=5)
    d.rectangle((330, 400, 370, 450), fill=(122, 190, 123), outline=(30, 90, 40), width=5)
    d.polygon([(700, 300), (800, 240), (900, 300), (800, 360)], fill=(230, 120, 80))
    d.line((700, 300, 900, 300), fill=(150, 60, 30), width=3)
    return image


def cat_ball():
    image, d = _canvas()
    d.ellipse((140, 260, 380, 440), fill=(236, 170, 90), outline=(120, 70, 20), width=5)
    d.ellipse((330, 200, 450, 320), fill=(240, 180, 100), outline=(120, 70, 20), width=5)
    d.polygon([(340, 210), (355, 160), (385, 205)], fill=(240, 180, 100), outline=(120, 70, 20))
    d.polygon([(400, 205), (430, 160), (445, 215)], fill=(240, 180, 100), outline=(120, 70, 20))
    d.ellipse((730, 340, 830, 440), fill=(90, 140, 230), outline=(30, 60, 130), width=5)
    return image


def bird_apple():
    image, d = _canvas()
    d.ellipse((180, 180, 380, 320), fill=(240, 210, 70), outline=(150, 110, 10), width=5)
    d.ellipse((350, 150, 430, 230), fill=(245, 220, 90), outline=(150, 110, 10), width=5)
    d.polygon([(425, 185), (470, 195), (425, 210)], fill=(235, 140, 50))
    d.ellipse((690, 330, 800, 440), fill=(215, 60, 60), outline=(110, 20, 20), width=5)
    return image


SET = {
    "turtle_leaf": (turtle_leaf, "turtle", "leaf", "eat the leaf"),
    "cat_ball": (cat_ball, "cat", "ball", "play with the ball"),
    "bird_apple": (bird_apple, "bird", "apple", "peck the apple"),
}

manifest = {}
for name, (draw, main, secondary, script) in SET.items():
    draw().save(OUT / f"{name}.png")
    manifest[name] = {
        "main": main,
        "secondary": [secondary],
        "script": script,
        "a4_expectation": "sprite in K(i) pixel-identical to the original drawing",
    }
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
