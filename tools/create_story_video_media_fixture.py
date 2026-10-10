"""Create local, non-child drawings and four-scene media smoke fixtures.

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

_GROUP_SCENES = (
    {
        "text": (
            "Trong tranh thử có ba người đang nắm tay nhau trên một lối đi rộng. "
            "Hai người cao hơn đứng hai bên và một người nhỏ hơn ở giữa. "
            "Ta vẽ từng người theo thứ tự, rồi nối những bàn tay để thấy cả nhóm đi cùng nhau."
        ),
        "visual_prompt": (
            "Clean whiteboard drawing of the three source figures holding hands only. "
            "Keep their relative heights and source shirt colors; no named relationships, "
            "new people, objects or words."
        ),
        "focus_box": [0.22, 0.33, 0.65, 0.96],
    },
    {
        "text": (
            "Sau đó ta nhìn cái cây ở bên trái lối đi. "
            "Nét thân cây đi lên, rồi các nhánh mở ra dưới tán lá xanh. "
            "Màu của thân và lá xuất hiện sau các đường viền, không vẽ lại ba người của cảnh trước."
        ),
        "visual_prompt": (
            "Clean whiteboard drawing of the source tree only: brown trunk, green canopy "
            "and black contours on white. No people, house, extra plants or words."
        ),
        "focus_box": [0.02, 0.02, 0.35, 0.68],
    },
    {
        "text": (
            "Tiếp theo, ngôi nhà nhỏ nằm ở phía phải bức tranh hiện ra. "
            "Ta thấy mái đỏ ở trên, những bức tường sáng và các ô cửa màu xanh. "
            "Hình ngôi nhà được vẽ riêng để câu chuyện dễ theo dõi, không lặp lại cảnh cái cây."
        ),
        "visual_prompt": (
            "Clean whiteboard drawing of the source house only, with its red roof and blue "
            "windows. Preserve simple source geometry on white; no figures, tree or words."
        ),
        "focus_box": [0.57, 0.04, 0.98, 0.79],
    },
    {
        "text": (
            "Cuối cùng ta nhìn lại toàn cảnh thử: ba người ở trên đường, "
            "cái cây bên trái, ngôi nhà bên phải và những bông hoa ở phía dưới. "
            "Đây là tranh tổng hợp để thử thứ tự vẽ, màu sắc và lời kể."
        ),
        "visual_prompt": (
            "Complete source-derived whiteboard recap: three unnamed figures holding hands, "
            "tree left, red-roof house right, small flowers below. Preserve source colors "
            "and relative positions; no invented relationships, props or words."
        ),
        "focus_box": [0.0, 0.0, 1.0, 1.0],
    },
)


def _draw_group_fixture(draw) -> None:
    """Draw a generic multi-object test, never a copy of a child's image."""

    ink = (25, 30, 35)
    draw.rectangle((402, 105, 604, 264), outline=ink, width=5)
    draw.polygon(((388, 108), (500, 38), (618, 108)), fill=(225, 65, 75))
    draw.line(((388, 108), (500, 38), (618, 108)), fill=ink, width=5)
    for left in (430, 535):
        draw.rectangle((left, 142, left + 34, 178), fill=(90, 175, 220), outline=ink, width=4)
    draw.rectangle((485, 190, 524, 264), outline=ink, width=4)
    draw.line(((116, 185), (116, 83)), fill=(135, 90, 55), width=13)
    draw.ellipse((49, 29, 183, 137), fill=(95, 180, 75), outline=ink, width=5)

    for x, head_y, size, shirt in (
        (205, 189, 27, (225, 95, 55)),
        (278, 227, 22, (75, 155, 220)),
        (355, 185, 28, (235, 150, 45)),
    ):
        draw.ellipse((x - size, head_y - size, x + size, head_y + size),
                     fill=(245, 205, 170), outline=ink, width=4)
        draw.polygon(((x - size, head_y + size + 6), (x + size, head_y + size + 6),
                      (x + size + 4, head_y + size + 75),
                      (x - size - 4, head_y + size + 75)), fill=shirt)
        draw.line(((x - size, head_y + size + 6), (x + size, head_y + size + 6),
                   (x + size + 4, head_y + size + 75),
                   (x - size - 4, head_y + size + 75),
                   (x - size, head_y + size + 6)), fill=ink, width=4)
        draw.line(((x - 12, head_y + size + 75), (x - 18, 351)), fill=ink, width=6)
        draw.line(((x + 12, head_y + size + 75), (x + 18, 351)), fill=ink, width=6)
    draw.line(((232, 252), (256, 277)), fill=ink, width=5)
    draw.line(((300, 277), (327, 251)), fill=ink, width=5)
    for x in (435, 477, 528, 570):
        draw.line(((x, 307), (x, 348)), fill=(65, 150, 80), width=4)
        draw.ellipse((x - 9, 293, x + 9, 311), fill=(220, 65, 100), outline=ink, width=2)


def create_fixture(directory: Path, *, preset: str = "house") -> Path:
    """Write only two new local files and return the fixture JSON path."""

    from PIL import Image, ImageDraw

    directory = directory.resolve()
    if preset not in {"house", "group"}:
        raise ValueError("preset must be house or group")
    repository_root = Path(__file__).resolve().parents[1]
    if directory.is_relative_to(repository_root):
        raise ValueError("output directory must be outside the Git repository")
    image_path = directory / f"synthetic-{preset}.png"
    fixture_path = directory / f"synthetic-{preset}-story.json"
    if image_path.exists() or fixture_path.exists():
        raise FileExistsError("synthetic fixture already exists; choose an empty output directory")
    directory.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (640, 384), "white")
    draw = ImageDraw.Draw(image)
    if preset == "group":
        _draw_group_fixture(draw)
    else:
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
        for petal in ((532, 245), (555, 234), (578, 245), (578, 270),
                      (555, 281), (532, 270)):
            draw.ellipse((petal[0] - 14, petal[1] - 14, petal[0] + 14, petal[1] + 14),
                         fill=(190, 125, 210), outline=ink, width=3)
        draw.ellipse((543, 247, 567, 269), fill=(250, 205, 45), outline=ink, width=3)
        draw.line(((555, 280), (555, 330)), fill=(70, 145, 75), width=5)
    image.save(image_path)
    fixture_path.write_text(
        json.dumps(
            {"source_image": image_path.name, "locale": "vi-VN",
             "scenes": _GROUP_SCENES if preset == "group" else _SCENES},
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
    parser.add_argument("--preset", choices=("house", "group"), default="house")
    args = parser.parse_args(argv)
    print(create_fixture(args.output_dir.resolve(), preset=args.preset))


if __name__ == "__main__":
    try:
        main()
    except (FileExistsError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
