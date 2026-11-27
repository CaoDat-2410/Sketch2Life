"""Throwaway mock-up: two drawing-guide styles for one subject (a chicken), to let the owner pick a direction."""

import math
import sys

from PIL import Image, ImageDraw, ImageFont

TILE, K = 300, 3
BOLD = ImageFont.truetype("arialbd.ttf", 20)
FONT = ImageFont.truetype("arial.ttf", 16)
DONE, NEW, DOT = "#27324A", "#2F6BFF", "#18A558"


def ellipse(cx, cy, rx, ry, start=-90, end=270, n=90):
    return [(cx + rx * math.cos(math.radians(start + (end - start) * i / n)),
             cy + ry * math.sin(math.radians(start + (end - start) * i / n))) for i in range(n + 1)]


def curve(p0, p1, p2, n=30):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def line(*points):
    out = []
    for a, b in zip(points, points[1:]):
        out += [(a[0] + (b[0] - a[0]) * i / 20, a[1] + (b[1] - a[1]) * i / 20) for i in range(21)]
    return out


# Style A: build from basic shapes (one shape per step)
SHAPES = [
    ("1. Một hình tròn to", "làm thân gà", [ellipse(135, 175, 70, 62)]),
    ("2. Một hình tròn nhỏ", "làm đầu gà", [ellipse(205, 98, 36, 36, 150, 510)]),
    ("3. Một tam giác", "làm mỏ", [line((238, 88), (268, 100), (238, 112))]),
    ("4. Ba hình tròn bé", "làm mào, chấm mắt", [ellipse(188, 57, 10, 10), ellipse(205, 52, 11, 11), ellipse(222, 57, 10, 10), ellipse(216, 90, 5, 5)]),
    ("5. Hai chân", "mỗi chân ba ngón", [line((115, 235), (115, 268), (100, 276)), line((115, 268), (132, 276)),
                                          line((158, 235), (158, 268), (143, 276)), line((158, 268), (175, 276))]),
    ("6. Cánh và đuôi", "xong rồi!", [curve((100, 165), (135, 225), (172, 165)), curve((70, 150), (30, 120), (38, 92)),
                                       curve((68, 170), (22, 165), (20, 135))]),
]
# Style B: a simple picture in a few long, smooth outline strokes
OUTLINE = [
    ("1. Vẽ lưng và bụng", "một nét cong dài", [curve((75, 140), (40, 250), (140, 250)) + curve((140, 250), (240, 250), (225, 130))[1:]]),
    ("2. Vẽ đầu", "một vòng cung", [curve((225, 130), (265, 55), (200, 55)) + curve((200, 55), (150, 60), (165, 128))[1:]]),
    ("3. Nối lưng", "đến đuôi", [curve((165, 128), (125, 165), (75, 140))]),
    ("4. Đuôi", "ba chiếc lông", [curve((75, 140), (35, 125), (30, 85)), curve((75, 142), (25, 150), (18, 118)), curve((70, 150), (35, 175), (25, 160))]),
    ("5. Mỏ, mào, mắt", "", [line((238, 90), (270, 102), (236, 114)), curve((185, 58), (180, 30), (200, 50)) + curve((200, 50), (212, 25), (222, 58))[1:], ellipse(212, 88, 4, 4)]),
    ("6. Hai chân và cánh", "xong rồi!", [line((125, 248), (122, 280), (140, 280)), line((170, 246), (172, 280), (190, 280)), curve((105, 170), (150, 225), (190, 170))]),
]


def tile(steps, upto):
    image = Image.new("RGB", (TILE * K, TILE * K), "white")
    draw = ImageDraw.Draw(image)
    for number, (_a, _b, strokes) in enumerate(steps[: upto + 1]):
        current = number == upto
        for stroke in strokes:
            pts = [(x * K, y * K) for x, y in stroke]
            if not current:
                draw.line(pts, fill=DONE, width=5 * K, joint="curve")
                continue
            travelled = 0.0
            for a, b in zip(pts, pts[1:]):
                if int(travelled / (11 * K)) % 2 == 0:
                    draw.line([a, b], fill=NEW, width=6 * K)
                travelled += math.dist(a, b)
        if current:
            first = [(x * K, y * K) for x, y in strokes[0]]
            sx, sy = first[0]
            draw.ellipse([sx - 8 * K, sy - 8 * K, sx + 8 * K, sy + 8 * K], fill=DOT)
            at = min(len(first) - 2, max(1, len(first) // 5))
            (ax, ay), (bx, by) = first[at - 1], first[at + 1]
            angle = math.atan2(by - ay, bx - ax)
            tip = (first[at][0] + 12 * K * math.cos(angle), first[at][1] + 12 * K * math.sin(angle))
            wings = [(tip[0] - 16 * K * math.cos(angle + s), tip[1] - 16 * K * math.sin(angle + s)) for s in (0.55, -0.55)]
            draw.polygon([tip, *wings], fill=DOT)
    return image.resize((TILE, TILE), Image.Resampling.LANCZOS)


rows = [("A. Ghép hình khối: mỗi bước một hình quen thuộc", SHAPES), ("B. Nét viền đơn giản: ít nét, nét dài và mượt", OUTLINE)]
sheet = Image.new("RGB", (6 * (TILE + 12) + 12, 2 * (TILE + 100) + 12), "#EEF1F8")
draw = ImageDraw.Draw(sheet)
for r, (title, steps) in enumerate(rows):
    y = r * (TILE + 100) + 10
    draw.text((12, y), title, fill="#111", font=BOLD)
    for i, (head, sub, _s) in enumerate(steps):
        x = 12 + i * (TILE + 12)
        sheet.paste(tile(steps, i), (x, y + 30))
        draw.text((x + 4, y + 30 + TILE + 4), head, fill="#111", font=FONT)
        draw.text((x + 4, y + 30 + TILE + 24), sub, fill="#555", font=FONT)
sheet.save(sys.argv[1])
print(sheet.size)
