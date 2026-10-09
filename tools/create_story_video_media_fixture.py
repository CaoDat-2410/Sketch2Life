"""Create a local, non-child house drawing and four-scene media smoke fixture.

The output is for provider testing only, not a reviewed story or Gate B artifact.
It refuses to replace existing files; keep the generated media outside Git.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.story_video_media_smoke import load_fixture

_SCENES = (
    {
        "text": (
            "Trước tiên, ta nhìn ngôi nhà nhỏ ở bên trái bức tranh. "
            "Hai nét mái nghiêng gặp nhau phía trên những bức tường thẳng. "
            "Cánh cửa, ô cửa sổ và mái vàng hiện ra lần lượt, để hình ngôi nhà trở nên rõ ràng."
        ),
        "visual_prompt": (
            "Clean hand-drawn whiteboard line art of the source house only. "
            "Draw the black walls, door and window, then retain the source yellow roof. "
            "White background; no new objects or words."
        ),
        "focus_box": [0.06, 0.10, 0.49, 0.91],
    },
    {
        "text": (
            "Tiếp theo, ta chuyển sang cái cây ở giữa bức tranh. "
            "Thân cây màu nâu đi lên rồi chia thành những cành đơn giản. "
            "Các nét cong bao quanh tán lá xanh, tạo thành một hình mới chứ không vẽ lại ngôi nhà."
        ),
        "visual_prompt": (
            "Clean hand-drawn whiteboard line art of the source tree only. "
            "Retain its brown trunk and green canopy. White background; "
            "do not redraw the house, add people or add words."
        ),
        "focus_box": [0.47, 0.10, 0.73, 0.91],
    },
    {
        "text": (
            "Ở phía bên phải, mặt trời vàng và bông hoa tím làm bức tranh vui hơn. "
            "Trước hết các tia nắng xuất hiện quanh hình tròn. "
            "Sau đó những cánh hoa mở ra quanh nhụy, rồi màu được tô vào đúng hình đã vẽ."
        ),
        "visual_prompt": (
            "Clean hand-drawn whiteboard line art of the source yellow sun and "
            "purple flower only. Retain their source colors, with simple black "
            "outlines on white. Do not redraw the house or tree; no words."
        ),
        "focus_box": [0.73, 0.06, 0.98, 0.93],
    },
    {
        "text": (
            "Cuối cùng, ta nhìn lại toàn bộ bức tranh. "
            "Ngôi nhà nằm bên trái, cái cây ở giữa, còn mặt trời và bông hoa ở bên phải. "
            "Đây là tranh thử để kiểm tra bốn cảnh khác nhau, lời kể, nét vẽ và màu sắc đi cùng nhau."
        ),
        "visual_prompt": (
            "Complete clean hand-drawn whiteboard recap of the source drawing: "
            "yellow-roof house left, brown-trunk green tree center, yellow sun "
            "and purple flower right. Preserve all source positions and colors "
            "on white; no new objects or words."
        ),
        "focus_box": [0.0, 0.0, 1.0, 1.0],
    },
)


def create_fixture(directory: Path) -> Path:
    """Write only two new local files and return the fixture JSON path."""

    from PIL import Image, ImageDraw

    directory = directory.resolve()
    repository_root = Path(__file__).resolve().parents[1]
    if directory.is_relative_to(repository_root):
        raise ValueError("output directory must be outside the Git repository")
    image_path = directory / "synthetic-house.png"
    fixture_path = directory / "synthetic-house-story.json"
    if image_path.exists() or fixture_path.exists():
        raise FileExistsError("synthetic fixture already exists; choose an empty output directory")
    directory.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (640, 384), "white")
    draw = ImageDraw.Draw(image)
    ink = (20, 25, 30)
    draw.rectangle((80, 170, 290, 326), outline=ink, width=6)
    draw.polygon(((60, 173), (185, 68), (310, 173)), fill=(245, 210, 55))
    draw.line(((60, 173), (185, 68), (310, 173)), fill=ink, width=7, joint="curve")
    draw.rectangle((165, 240, 215, 326), outline=ink, width=5)
    draw.rectangle((98, 200, 143, 238), fill=(85, 190, 225), outline=ink, width=5)
    draw.line(((375, 326), (375, 185)), fill=(135, 85, 45), width=12)
    draw.line(((375, 240), (325, 198)), fill=(135, 85, 45), width=7)
    draw.line(((375, 215), (425, 166)), fill=(135, 85, 45), width=7)
    draw.ellipse((310, 66, 445, 205), fill=(125, 190, 85), outline=ink, width=7)
    draw.ellipse((515, 55, 575, 115), fill=(250, 205, 45), outline=ink, width=5)
    for ray in (((545, 30), (545, 47)), ((545, 123), (545, 140)),
                ((489, 85), (506, 85)), ((584, 85), (601, 85))):
        draw.line(ray, fill=(245, 185, 35), width=5)
    for petal in ((532, 245), (555, 234), (578, 245), (578, 270), (555, 281), (532, 270)):
        draw.ellipse((petal[0] - 14, petal[1] - 14, petal[0] + 14, petal[1] + 14),
                     fill=(190, 125, 210), outline=ink, width=3)
    draw.ellipse((543, 247, 567, 269), fill=(250, 205, 45), outline=ink, width=3)
    draw.line(((555, 280), (555, 330)), fill=(70, 145, 75), width=5)
    image.save(image_path)
    fixture_path.write_text(
        json.dumps(
            {"source_image": image_path.name, "locale": "vi-VN", "scenes": _SCENES},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    load_fixture(fixture_path)
    return fixture_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(create_fixture(args.output_dir.resolve()))


if __name__ == "__main__":
    try:
        main()
    except (FileExistsError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
