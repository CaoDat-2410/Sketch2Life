from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import build_srs_doc as base


def wrap_lines(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        elif paragraph == "":
            lines.append("")
    return lines or [""]


def save_end_to_end_flow():
    path = base.FIGURE_DIR / "end_to_end_flow.png"
    img = base.Image.new("RGB", (1850, 1220), "F7FAFC")
    draw = base.ImageDraw.Draw(img)
    base.label(draw, (50, 30), "Sketch2Life end-to-end experience flow", 34, base.NAVY, True)
    base.label(draw, (50, 78), "The current fixture flow proves the sequence; capture, persistence, auth, provider jobs and full mobile wiring remain open for integration.", 20, base.TEXT)
    boxes = [
        (60, 180, 360, 340, "1  Capture\ndrawing + narration", base.TEAL),
        (455, 180, 755, 340, "2  Validate\nimage + audio", base.BLUE),
        (850, 180, 1170, 340, "3  ASR + Vision\nproposal", base.NAVY),
        (1265, 180, 1585, 340, "4  Gate A\nconfirm meaning", "4B5563"),
        (160, 520, 500, 690, "5  P1\nhard rules + fit", base.BLUE),
        (700, 520, 1040, 690, "6  Gate B\napprove identity", "4B5563"),
        (1240, 520, 1610, 690, "7  Experience\nP3 art + P4 media", base.TEAL),
        (360, 890, 700, 1060, "8  Activity handoff\noff-screen", base.GREEN),
        (980, 890, 1320, 1060, "9  Feedback\nrecorded", base.GREEN),
    ]
    for x1, y1, x2, y2, text, color in boxes:
        base.rounded_box(draw, (x1, y1, x2, y2), text, color, font_size=24)
    base.arrow(draw, (360, 260), (455, 260))
    base.arrow(draw, (755, 260), (850, 260))
    base.arrow(draw, (1170, 260), (1265, 260))
    base.arrow(draw, (1425, 340), (330, 520))
    base.arrow(draw, (500, 605), (700, 605))
    base.arrow(draw, (1040, 605), (1240, 605))
    base.arrow(draw, (1425, 690), (530, 890))
    base.arrow(draw, (700, 975), (980, 975))
    base.label(draw, (65, 715), "recapture if invalid", 19, base.RED, True)
    base.arrow(draw, (605, 340), (280, 755), base.RED, width=4)
    base.rounded_box(draw, (60, 755, 500, 885), "Recapture\nno AI call", base.RED, font_size=25)
    base.label(draw, (80, 1125), "Failure rule: media/provider failure may change media status or apply typed fallback, but must preserve the off-screen activity handoff.", 20, base.TEXT)
    img.save(path)
    return path


base.wrap_lines = wrap_lines
base.save_end_to_end_flow = save_end_to_end_flow
base.build_document()
