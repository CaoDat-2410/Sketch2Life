"""Render the genuine Rev87.22 Parent API response for visual inspection."""

from __future__ import annotations

import json
import html
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
RESPONSE = ROOT / "attempt_003_response.json"
OUTPUT = ROOT / "renders"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def svg_document(view_box: str, paths: list[dict[str, object]]) -> bytes:
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {"viewBox": view_box, "width": "1024", "height": "1024"},
    )
    for path in paths:
        attributes = {
            "id": str(path["path_id"]),
            "d": str(path["d"]),
            "fill": str(path.get("fill", "none")),
            "stroke": str(path.get("stroke", "#202938")),
            "stroke-width": str(path.get("stroke_width", 6)),
            "stroke-linecap": str(path.get("stroke_linecap", "round")),
            "stroke-linejoin": str(path.get("stroke_linejoin", "round")),
        }
        if "stroke_miterlimit" in path:
            attributes["stroke-miterlimit"] = str(path["stroke_miterlimit"])
        ET.SubElement(root, f"{{{SVG_NS}}}path", attributes)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main() -> None:
    data = json.loads(RESPONSE.read_text(encoding="utf-8"))
    OUTPUT.mkdir(exist_ok=True)
    document = data["document"]
    path_by_id = {path["path_id"]: path for path in document["paths"]}
    cumulative: list[str] = []
    cards: list[str] = []
    for stage in data["guide"]["stages"]:
        cumulative.extend(stage["new_path_ids"])
        paths = [path_by_id[path_id] for path_id in cumulative]
        svg_name = f"guide_stage_{stage['step_index']:02d}.svg"
        (OUTPUT / svg_name).write_bytes(svg_document(document["view_box"], paths))
        instruction = html.escape(str(stage["instruction_vi"]))
        cards.append(
            f'<article><h2>Bước {stage["step_index"]}</h2>'
            f'<img src="{svg_name}" alt="Nét tích lũy đến bước {stage["step_index"]}">'
            f'<p>{instruction}</p></article>'
        )

    reference = data["reference_illustration"]
    reference_name = "source_color_reference.svg"
    (OUTPUT / reference_name).write_bytes(
        svg_document(reference["view_box"], reference["paths"])
    )
    cards.append(
        f'<article><h2>Ảnh màu nguồn</h2><img src="{reference_name}" '
        'alt="Ảnh màu nguồn từ catalog"></article>'
    )
    gallery = """<!doctype html>
<html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Rev87.22 · SVG render thật</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:16px;background:#eef1f5;color:#17243e;
font:16px Arial,sans-serif}.grid{display:grid;grid-template-columns:repeat(3,500px);gap:16px}
article{height:580px;padding:12px;background:#fff;border:1px solid #d7dee8;border-radius:12px}
h2{height:28px;margin:0 0 6px;font-size:20px}img{display:block;width:474px;height:474px;object-fit:contain;
background:#fff}p{margin:6px 0 0;line-height:1.25;font-size:14px}
</style><main class="grid">""" + "".join(cards) + "</main></html>"
    (OUTPUT / "visual_review.html").write_text(gallery, encoding="utf-8")
    print(json.dumps({
        "stage_svgs": [f"guide_stage_{i:02d}.svg" for i in range(1, len(data["guide"]["stages"]) + 1)],
        "reference_svg": reference_name,
        "gallery_html": "visual_review.html",
        "source_asset_id": data["reference_source"]["asset_id"],
        "document_sha256": data["document_sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
