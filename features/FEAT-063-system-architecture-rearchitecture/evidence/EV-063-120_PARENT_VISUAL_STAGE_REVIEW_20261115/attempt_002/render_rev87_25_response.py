"""Render cumulative SVG stages from the real synthetic route response."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
RESPONSE_PATH = HERE / "response.json"
SOURCE_DIR = HERE.parent.parent / "EV-063-119_PARENT_SOURCE_SEGMENT_GUIDE_20261115"
SOURCE_SVG = SOURCE_DIR / "source_atlas_rev87_24" / "source_color_reference.svg"
SOURCE_PNG = SOURCE_DIR / "source_atlas_rev87_24" / "source_color_reference.png"
RENDERER = SOURCE_DIR / "render_rev87_24_svg.ps1"
SVG_NS = "http://www.w3.org/2000/svg"


def main() -> None:
    ET.register_namespace("", SVG_NS)
    response = json.loads(RESPONSE_PATH.read_text(encoding="utf-8"))
    paths = response["document"]["paths"]
    path_by_id = {path["path_id"]: path for path in paths}
    stages = response["guide"]["stages"]
    output: list[dict[str, object]] = []
    cumulative: list[str] = []

    for stage in stages:
        new_ids = list(stage["new_path_ids"])
        if any(path_id not in path_by_id for path_id in new_ids):
            raise ValueError("response stage contains unknown geometry id")
        cumulative.extend(new_ids)
        root = ET.Element(
            f"{{{SVG_NS}}}svg",
            {"viewBox": response["document"]["view_box"], "width": "512", "height": "512"},
        )
        new_id_set = set(new_ids)
        for path in paths:
            if path["path_id"] not in cumulative:
                continue
            ET.SubElement(
                root,
                f"{{{SVG_NS}}}path",
                {
                    "d": path["d"],
                    "fill": "none",
                    "stroke": "#1769ff" if path["path_id"] in new_id_set else "#aeb8c8",
                    "stroke-width": "8",
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round",
                },
            )
        svg_path = HERE / f"cumulative_stage_{stage['step_index']:02d}.svg"
        png_path = HERE / f"cumulative_stage_{stage['step_index']:02d}.png"
        svg_path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(RENDERER),
                "-InputSvg",
                str(svg_path),
                "-OutputPng",
                str(png_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        output.append(
            {
                "step_index": stage["step_index"],
                "label_vi": stage["instruction_vi"],
                "new_path_ids": new_ids,
                "cumulative_path_ids": list(cumulative),
                "svg": svg_path.name,
                "png": png_path.name,
            }
        )

    shutil.copy2(SOURCE_PNG, HERE / "source_color_reference.png")
    source_hash = hashlib.sha256(SOURCE_SVG.read_bytes()).hexdigest()
    manifest = {
        "status": response["status"],
        "request_id": response["request_id"],
        "modal_call_id": response["modal_call_id"],
        "source_asset_id": response["reference_source"]["asset_id"],
        "source_sha256": response["reference_source"]["source_sha256"],
        "evidence_source_svg_sha256": source_hash,
        "source_sha256_matches_evidence_svg": (
            source_hash == response["reference_source"]["source_sha256"]
        ),
        "path_count": len(paths),
        "stage_count": len(stages),
        "stages": output,
        "source_color_png": "source_color_reference.png",
        "render_method": "Windows WPF; API path d preserved; prior strokes gray; new strokes blue",
    }
    (HERE / "render_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    tile_width, tile_height = 340, 388
    columns = 4
    rows = 2
    sheet = Image.new("RGB", (tile_width * columns, tile_height * rows), "#e9edf4")
    draw = ImageDraw.Draw(sheet)
    font_path = Path(r"C:\Windows\Fonts\arial.ttf")
    title_font = ImageFont.truetype(str(font_path), 18) if font_path.exists() else ImageFont.load_default()
    body_font = ImageFont.truetype(str(font_path), 15) if font_path.exists() else ImageFont.load_default()

    panels: list[tuple[str, Path, str]] = [
        (f"BƯỚC {item['step_index']}", HERE / str(item["png"]), str(item["label_vi"]))
        for item in output
    ]
    panels.append(("ẢNH MÀU NGUỒN", HERE / "source_color_reference.png", "Hình gốc dùng làm chuẩn nhận diện."))
    for index, (heading, image_path, caption) in enumerate(panels):
        col, row = index % columns, index // columns
        left, top = col * tile_width, row * tile_height
        draw.rounded_rectangle(
            (left + 5, top + 5, left + tile_width - 6, top + tile_height - 6),
            radius=10,
            fill="white",
            outline="#cbd3df",
            width=2,
        )
        draw.text((left + 16, top + 12), heading, fill="#2449a7", font=title_font)
        with Image.open(image_path) as opened:
            panel = opened.convert("RGB")
        panel.thumbnail((304, 304), Image.Resampling.LANCZOS)
        sheet.paste(
            panel,
            (left + (tile_width - panel.width) // 2, top + 40),
        )
        caption_lines = textwrap.wrap(caption, width=42)
        caption_y = top + 350
        for line in caption_lines[:2]:
            draw.text((left + 16, caption_y), line, fill="#253248", font=body_font)
            caption_y += 18

    sheet.save(HERE / "cumulative_stage_review.png", optimize=True)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
