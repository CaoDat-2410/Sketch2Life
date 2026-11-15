"""Render the genuine Rev87.22 catalog source and Rev87.23 deterministic chunks."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


EVIDENCE = Path(__file__).resolve().parent
WORKTREE = EVIDENCE.parents[3]
MODAL_DIR = WORKTREE / "deployment" / "modal" / "srs_v23"
SOURCE_RESPONSE = (
    WORKTREE
    / "features"
    / "FEAT-063-system-architecture-rearchitecture"
    / "evidence"
    / "EV-063-118_PARENT_PRIMITIVE_STROKE_RENDERER_20261115"
    / "attempt_003_response.json"
)
OUTPUT = EVIDENCE / "source_atlas"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
sys.path.insert(0, str(MODAL_DIR))

import language_audio_app as worker  # noqa: E402


def _write_svg(path: Path, view_box: str, paths: list[dict[str, object]]) -> None:
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {"viewBox": view_box, "width": "512", "height": "512"},
    )
    for item in paths:
        ET.SubElement(
            root,
            f"{{{SVG_NS}}}path",
            {
                "d": str(item["d"]),
                "fill": str(item.get("fill", "none")),
                "stroke": str(item.get("stroke", "#17243e")),
                "stroke-width": str(item.get("stroke_width", 5)),
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
            },
        )
    path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))


def main() -> None:
    response = json.loads(SOURCE_RESPONSE.read_text(encoding="utf-8"))
    reference = response["reference_illustration"]
    candidate = {
        "parsed_svg": {
            "view_box": reference["view_box"],
            "paths": reference["paths"],
        },
        "asset_id": response["reference_source"]["asset_id"],
        "source_sha256": response["reference_source"]["source_sha256"],
    }
    segments, manifest = worker._segment_openclipart_candidate(candidate)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cards: list[str] = []
    for index, segment in enumerate(segments, start=1):
        name = f"segment_{index:03d}.svg"
        _write_svg(
            OUTPUT / name,
            "0 0 512 512",
            [{"d": segment["d"], "fill": "none", "stroke": "#17243e", "stroke_width": 5}],
        )
        count = len(worker.re.findall(r"[MLCQZ]", segment["d"]))
        cards.append(
            f'<article><h2>P{index:02d} · {html.escape(segment["path_id"])}</h2>'
            f'<img src="{name}" alt="Nét nguồn {index}">'
            f'<p>{html.escape(segment["source_path_id"])} · subpath '
            f'{html.escape(",".join(map(str, segment["source_subpath_indices"])))}</p>'
            f'<p>{count} lệnh vẽ · {segment["source_segment_count"]} đoạn lệnh nguồn</p></article>'
        )

    _write_svg(
        OUTPUT / "source_color_reference.svg",
        reference["view_box"],
        reference["paths"],
    )
    cards.insert(
        0,
        '<article class="source"><h2>Hình màu nguồn thật</h2>'
        '<img src="source_color_reference.svg" alt="Tham chiếu Openclipart CC0"></article>',
    )
    page = (
        "<!doctype html><html lang='vi'><meta charset='utf-8'><title>Rev87.23 source segments</title>"
        "<style>*{box-sizing:border-box}body{margin:0;padding:18px;background:#edf1f6;color:#17243e;"
        "font:15px Arial,sans-serif}.grid{display:grid;grid-template-columns:repeat(4,320px);gap:12px}"
        "article{height:340px;padding:10px;background:#fff;border:1px solid #cbd5e1;border-radius:8px}"
        "h2{height:24px;margin:0 0 6px;font-size:15px}img{width:298px;height:258px;object-fit:contain}"
        "p{margin:4px 0;font-size:12px}.source{grid-column:span 2}.source img{width:620px;height:300px}"
        "</style><main class='grid'>" + "".join(cards) + "</main></html>"
    )
    (OUTPUT / "segment_atlas.html").write_text(page, encoding="utf-8")
    segment_manifest = {
        **manifest,
        "source_asset_id": candidate["asset_id"],
        "source_sha256": candidate["source_sha256"],
        "source_response_sha256": hashlib.sha256(SOURCE_RESPONSE.read_bytes()).hexdigest(),
        "segments": [
            {
                "segment_id": segment["path_id"],
                "source_path_id": segment["source_path_id"],
                "source_subpath_indices": segment["source_subpath_indices"],
                "source_segment_start": segment["source_segment_start"],
                "source_segment_end": segment["source_segment_end"],
                "source_segment_count": segment["source_segment_count"],
                "drawable_command_count": len(worker.re.findall(r"[MLCQZ]", segment["d"])),
                "geometry_sha256": hashlib.sha256(segment["d"].encode("utf-8")).hexdigest(),
            }
            for segment in segments
        ],
    }
    (EVIDENCE / "source_segment_preflight.json").write_text(
        json.dumps(segment_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"segment_count": len(segments), "manifest": segment_manifest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
