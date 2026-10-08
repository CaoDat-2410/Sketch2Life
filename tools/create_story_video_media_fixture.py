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
            "Đây là bức tranh thử nghiệm về một ngôi nhà nhỏ và một cái cây. "
            "Ngôi nhà nằm bên trái, cái cây ở bên phải. "
            "Chúng ta sẽ nhìn từng nét mực xuất hiện trên bảng trắng để nhận ra hai hình quen thuộc."
        ),
        "visual_prompt": (
            "Black ink whiteboard line art of the same simple house on the left and "
            "tree on the right from the source drawing. Introduce their outlines. "
            "Plain white background; no people, words, new objects, or color."
        ),
    },
    {
        "text": (
            "Trước tiên, nét bút vẽ hai bức tường thẳng và nền của ngôi nhà. "
            "Hai đường xiên gặp nhau để tạo thành mái. "
            "Khi thêm cửa ra vào và ô cửa sổ, hình ngôi nhà dần hoàn chỉnh mà không đổi vị trí."
        ),
        "visual_prompt": (
            "Black ink whiteboard line art of the same source house on the left, "
            "emphasizing its walls, triangular roof, door and window. "
            "Keep the source tree on the right; no people, words, new objects, or color."
        ),
    },
    {
        "text": (
            "Bây giờ, chúng ta nhìn sang cái cây ở bên phải ngôi nhà. "
            "Thân cây đi lên từ mặt đất rồi chia thành các cành đơn giản. "
            "Những nét cong tạo nên tán lá, trong khi ngôi nhà vẫn đứng đúng chỗ cũ."
        ),
        "visual_prompt": (
            "Black ink whiteboard line art of the same source tree on the right, "
            "emphasizing trunk, branches and round canopy. Keep the same house "
            "on the left; no people, words, new objects, or color."
        ),
    },
    {
        "text": (
            "Cuối cùng, toàn bộ bức tranh đã hiện ra trên bảng trắng. "
            "Ngôi nhà ở bên trái và cái cây ở bên phải, giống như lúc bắt đầu. "
            "Đây chỉ là ví dụ tổng hợp để kiểm tra tiếng kể, phụ đề và cách các nét vẽ nối tiếp nhau."
        ),
        "visual_prompt": (
            "Completed black ink whiteboard line art of the same source house "
            "on the left and tree on the right. Simple, consistent composition "
            "on white; no people, words, new objects, or color."
        ),
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
    draw.line(((60, 173), (185, 68), (310, 173)), fill=ink, width=7, joint="curve")
    draw.rectangle((165, 240, 215, 326), outline=ink, width=5)
    draw.rectangle((98, 200, 143, 238), outline=ink, width=5)
    draw.line(((375, 326), (375, 185)), fill=ink, width=12)
    draw.line(((375, 240), (325, 198)), fill=ink, width=7)
    draw.line(((375, 215), (425, 166)), fill=ink, width=7)
    draw.ellipse((310, 66, 445, 205), outline=ink, width=7)
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
