from __future__ import annotations

import json
import sys
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ATTEMPT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
OUT = ATTEMPT / "curated_source_sequence"
sys.path.insert(0, str(ROOT / "deployment/modal/srs_v23"))

import language_audio_app as worker  # noqa: E402
from render_parent_result import render_svg_to_png  # noqa: E402


def main() -> None:
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    OUT.mkdir(parents=True, exist_ok=True)
    response = json.loads((ATTEMPT / "response.json").read_text(encoding="utf-8"))
    doc_paths = {path["path_id"]: path for path in response["document"]["paths"]}
    source_path_by_id = {
        item["derived_path_id"]: item["source_path_ids"][0]
        for item in response["derivation"]["path_lineage"]
    }
    segments = [
        {
            "path_id": f"source_segment_{index:03d}",
            "source_path_id": source_path_by_id[f"guide_stroke_{index:02d}"],
            "d": doc_paths[f"guide_stroke_{index:02d}"]["d"],
        }
        for index in range(1, 21)
    ]
    source = response["reference_illustration"]
    candidate = {
        "asset_id": response["reference_source"]["asset_id"],
        "source_sha256": response["reference_source"]["source_sha256"],
        "parsed_svg": {"view_box": source["view_box"], "paths": source["paths"]},
    }
    plan = worker._curated_openclipart_source_plan(
        candidate,
        segments,
        first_step_segment_ids=["source_segment_005", "source_segment_006"],
    )
    if plan is None:
        raise RuntimeError("CURATED_PLAN_NOT_SELECTED_FOR_PINNED_SOURCE")
    guide, _ = worker._build_openclipart_segment_guide(candidate, segments, plan)

    stroke_by_id = {stroke["path_id"]: stroke for stroke in guide["strokes"]}
    cumulative: list[str] = []
    manifest_stages = []
    for stage in guide["stages"]:
        new_ids = list(stage["stroke_ids"])
        cumulative.extend(new_ids)
        root = ET.Element(
            "{http://www.w3.org/2000/svg}svg",
            {
                "viewBox": response["document"]["view_box"],
                "width": "512",
                "height": "512",
            },
        )
        for path_id in cumulative:
            ET.SubElement(
                root,
                "{http://www.w3.org/2000/svg}path",
                {
                    "d": stroke_by_id[path_id]["d"],
                    "fill": "none",
                    "stroke": "#075dff" if path_id in new_ids else "#aeb8c8",
                    "stroke-width": "8",
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round",
                },
            )
        target = OUT / f"cumulative_stage_{stage['step_index']:02d}.png"
        render_svg_to_png(ET.tostring(root, encoding="utf-8"), target)
        manifest_stages.append(
            {
                "step_index": stage["step_index"],
                "label_vi": stage["label_vi"],
                "instruction_vi": stage["instruction_vi"],
                "stroke_ids": new_ids,
                "png": target.name,
            }
        )

    card_w, card_h = 512, 620
    sheet = Image.new("RGB", (card_w * 2, card_h * 4), "#f1f4f8")
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 18)
    copy_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 14)
    for index, stage in enumerate(manifest_stages):
        x, y = (index % 2) * card_w, (index // 2) * card_h
        draw.rounded_rectangle((x + 6, y + 6, x + card_w - 6, y + card_h - 6), 14, fill="white", outline="#cbd5e1", width=2)
        draw.text((x + 22, y + 18), f"BƯỚC {stage['step_index']} · {stage['label_vi']}", fill="#172554", font=title_font)
        draw.multiline_text(
            (x + 22, y + 48),
            textwrap.fill(stage["instruction_vi"], width=48),
            fill="#334155",
            font=copy_font,
            spacing=3,
        )
        with Image.open(OUT / stage["png"]) as opened:
            art = opened.convert("RGB")
            art.thumbnail((460, 480), Image.Resampling.LANCZOS)
        sheet.paste(art, (x + (card_w - art.width) // 2, y + 112))
    sheet.save(OUT / "cumulative_stage_review.png")
    (OUT / "render_manifest.json").write_text(
        json.dumps(
            {
                "request_id": response["request_id"],
                "source_asset_id": candidate["asset_id"],
                "source_sha256": candidate["source_sha256"],
                "stage_count": len(manifest_stages),
                "source_segment_count": len(segments),
                "render_mode": "local reconstruction from the genuine prior synthetic route response; curated source sequence; no model call",
                "stages": manifest_stages,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "stages": len(manifest_stages), "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
