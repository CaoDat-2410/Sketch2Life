"""Rasterise the current Parent drawing guides stage by stage (PIL only), styled like the app."""

import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "backend" / "src"))
from sketch2life.infrastructure.svg.arcadia_gallus_guide import build_arcadia_gallus_guide  # noqa: E402
from sketch2life.infrastructure.svg.openclipart_guide import build_openclipart_guide  # noqa: E402
from sketch2life.infrastructure.svg.openmoji_guide import build_openmoji_guide  # noqa: E402

PIECE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
COUNT = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def arc(p0, rx, ry, phi, large, sweep, p1, n=40):
    if p0 == p1 or rx == 0 or ry == 0:
        return [p1]
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x, y = c * dx + s * dy, -s * dx + c * dy
    rx, ry = abs(rx), abs(ry)
    lam = x * x / rx**2 + y * y / ry**2
    if lam > 1:
        rx, ry = rx * lam**0.5, ry * lam**0.5
    num = max(0.0, rx**2 * ry**2 - rx**2 * y * y - ry**2 * x * x)
    coef = (num / (rx**2 * y * y + ry**2 * x * x)) ** 0.5 * (-1 if large == sweep else 1)
    cx, cy = coef * rx * y / ry, -coef * ry * x / rx
    ox, oy = c * cx - s * cy + (p0[0] + p1[0]) / 2, s * cx + c * cy + (p0[1] + p1[1]) / 2
    a0 = math.atan2((y - cy) / ry, (x - cx) / rx)
    d = math.atan2((-y - cy) / ry, (-x - cx) / rx) - a0
    if not sweep and d > 0:
        d -= 2 * math.pi
    if sweep and d < 0:
        d += 2 * math.pi
    return [
        (ox + rx * math.cos(a0 + d * i / n) * c - ry * math.sin(a0 + d * i / n) * s,
         oy + rx * math.cos(a0 + d * i / n) * s + ry * math.sin(a0 + d * i / n) * c)
        for i in range(1, n + 1)
    ]


def bezier(points, n=24):
    out = []
    for i in range(1, n + 1):
        t = i / n
        p = list(points)
        while len(p) > 1:
            p = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]) for a, b in zip(p, p[1:])]
        out.append(p[0])
    return out


def polylines(d):
    tokens = PIECE.findall(d)
    i, cmd, cur, start, lines, line, ctrl, prev = 0, None, (0, 0), (0, 0), [], [], None, ""
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
        up, rel = cmd.upper(), cmd.islower()
        n = COUNT[up]
        v = [float(t) for t in tokens[i : i + n]]
        i += n
        base = cur if rel else (0, 0)
        pt = lambda k: (base[0] + v[k], base[1] + v[k + 1])  # noqa: E731
        if up == "Z":
            line.append(start)
            cur = start
        elif up == "M":
            if len(line) > 1:
                lines.append(line)
            cur = start = pt(0)
            line = [cur]
            cmd = "l" if rel else "L"
        elif up in "LT" and up == "L":
            cur = pt(0)
            line.append(cur)
        elif up == "H":
            cur = (base[0] + v[0], cur[1])
            line.append(cur)
        elif up == "V":
            cur = (cur[0], (cur[1] if rel else 0) + v[0])
            line.append(cur)
        elif up in "CS":
            c1 = pt(0) if up == "C" else ((2 * cur[0] - ctrl[0], 2 * cur[1] - ctrl[1]) if prev in "CS" and ctrl else cur)
            c2 = pt(2) if up == "C" else pt(0)
            end = pt(4) if up == "C" else pt(2)
            line += bezier([cur, c1, c2, end])
            cur, ctrl = end, c2
        elif up in "QT":
            c1 = pt(0) if up == "Q" else ((2 * cur[0] - ctrl[0], 2 * cur[1] - ctrl[1]) if prev in "QT" and ctrl else cur)
            end = pt(2) if up == "Q" else pt(0)
            line += bezier([cur, c1, end])
            cur, ctrl = end, c1
        elif up == "A":
            end = pt(5)
            line += arc(cur, v[0], v[1], v[2], int(v[3]), int(v[4]), end)
            cur = end
        prev = up
    if len(line) > 1:
        lines.append(line)
    return lines


FONT = ImageFont.truetype("arial.ttf", 15)
BOLD = ImageFont.truetype("arialbd.ttf", 18)
TILE, SCALE = 300, 3


def render(generated, upto):
    view = [float(x) for x in generated.document.view_box.split()]
    size = TILE * SCALE
    k = size * 0.94 / max(view[2], view[3])
    off = ((size - view[2] * k) / 2 - view[0] * k, (size - view[3] * k) / 2 - view[1] * k)
    image = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(image)
    paths = {p.path_id: p for p in generated.document.paths}
    for number, stage in enumerate(generated.stages[: upto + 1]):
        for path_id in stage.new_path_ids:
            p = paths[path_id]
            colour = "#3867F6" if number == upto else "#17243E"
            width = max(1, int((p.stroke_width + (0.5 if number == upto else 0)) * k))
            for line in polylines(p.d):
                pts = [(off[0] + x * k, off[1] + y * k) for x, y in line]
                draw.line(pts, fill=colour, width=width, joint="curve")
    return image.resize((TILE, TILE), Image.Resampling.LANCZOS)


def wrap(draw, text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if draw.textlength(f"{cur} {w}", font=FONT) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return [*lines, cur]


out = Path(sys.argv[1])
sets = {
    "guides_openmoji": [("OpenMoji", build_openmoji_guide, t) for t in ("con rùa", "con bướm", "con chó")],
    "guides_others": [("Openclipart", build_openclipart_guide, "con bướm"), ("Openclipart", build_openclipart_guide, "con rùa"),
                      ("Arcadia", build_arcadia_gallus_guide, "con gà")],
}
for name, items in sets.items():
    built = [(label, topic, builder(topic)) for label, builder, topic in items]
    columns = max(len(g.generated.stages) for _l, _t, g in built if g)
    sheet = Image.new("RGB", (columns * (TILE + 12) + 12, len(built) * (TILE + 96) + 8), "#EEF1F8")
    draw = ImageDraw.Draw(sheet)
    for row, (label, topic, guide) in enumerate(built):
        if guide is None:
            continue
        g = guide.generated
        y = row * (TILE + 96) + 8
        draw.text((12, y), f"{label}: {topic} — {len(g.document.paths)} nét, {len(g.stages)} bước", fill="#111", font=BOLD)
        for i, stage in enumerate(g.stages):
            x = 12 + i * (TILE + 12)
            sheet.paste(render(g, i), (x, y + 28))
            for n, text in enumerate(wrap(draw, f"{i + 1}. {stage.instruction_vi} ({len(stage.new_path_ids)} nét)", TILE)[:3]):
                draw.text((x, y + 28 + TILE + 4 + n * 18), text, fill="#222", font=FONT)
    sheet.save(out / f"{name}.png")
    print(name, sheet.size)
