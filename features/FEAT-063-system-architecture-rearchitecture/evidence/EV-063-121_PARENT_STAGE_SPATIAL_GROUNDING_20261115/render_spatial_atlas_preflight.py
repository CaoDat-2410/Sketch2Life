from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from io import BytesIO

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
RESPONSE_PATH = (
    ROOT
    / "features/FEAT-063-system-architecture-rearchitecture/evidence/"
    / "EV-063-120_PARENT_VISUAL_STAGE_REVIEW_20261115/attempt_002/response.json"
)
OUT = Path(__file__).resolve().parent / "local_preflight_v2"
RENDERER = (
    ROOT
    / "features/FEAT-063-system-architecture-rearchitecture/evidence/"
    / "EV-063-119_PARENT_SOURCE_SEGMENT_GUIDE_20261115/render_rev87_24_svg.ps1"
)
sys.path.insert(0, str(ROOT / "deployment/modal/srs_v23"))

import language_audio_app as worker  # noqa: E402


def _render_svg_with_wpf(*, bytestring: bytes, output_width: int, output_height: int, background_color: str) -> bytes:
    del background_color  # The approved evidence renderer uses a white canvas.
    OUT.mkdir(parents=True, exist_ok=True)
    call_index = len(list(OUT.glob("raster_*.svg")))
    svg_path = (
        OUT / "source_color_reference.svg"
        if call_index == 0
        else OUT / f"raster_{call_index:03d}.svg"
    )
    png_path = OUT / f"raster_{call_index:03d}.png"
    svg_path.write_bytes(bytestring)
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
    with Image.open(png_path) as opened:
        rendered = opened.convert("RGB")
        if rendered.size != (output_width, output_height):
            rendered = rendered.resize((output_width, output_height), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        rendered.save(buffer, format="PNG")
        return buffer.getvalue()


def main() -> None:
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    sys.modules["cairosvg"] = SimpleNamespace(svg2png=_render_svg_with_wpf)
    payload = json.loads(RESPONSE_PATH.read_text(encoding="utf-8"))
    ref = payload["reference_illustration"]
    source_paths = []
    for path in ref["paths"]:
        source_paths.append(
            {
                "path_id": path["path_id"],
                "d": path["d"],
                "fill": path["fill"],
                "stroke": path["stroke"],
                "stroke_width": path["stroke_width"],
                "stroke_linecap": path.get("stroke_linecap", "round"),
                "stroke_linejoin": path.get("stroke_linejoin", "round"),
            }
        )
    lineage_by_id = {
        item["derived_path_id"]: item["source_path_ids"][0]
        for item in payload["derivation"]["path_lineage"]
    }
    segments = [
        {
            "path_id": path["path_id"],
            "source_path_id": lineage_by_id[path["path_id"]],
            "d": path["d"],
        }
        for path in payload["document"]["paths"]
    ]
    plan = {
        "stages": [
            {"step_index": stage["step_index"], "path_ids": stage["new_path_ids"]}
            for stage in payload["guide"]["stages"]
        ]
    }
    OUT.mkdir(parents=True, exist_ok=True)
    candidate = {
        "asset_id": payload["reference_source"]["asset_id"],
        "parsed_svg": {"view_box": ref["view_box"], "paths": source_paths},
    }
    source_image, atlas = worker._render_openclipart_candidate(
        candidate, atlas_paths=segments, atlas_view_box="0 0 512 512"
    )
    sheet, manifest = worker._render_openclipart_cumulative_stage_review(
        candidate, segments, plan
    )
    source_image.save(OUT / "source_color_reference.png")
    atlas.save(OUT / "spatial_segment_atlas.png")
    sheet.save(OUT / "cumulative_stage_review.png")
    outputs = {}
    for name in ("source_color_reference.png", "spatial_segment_atlas.png", "cumulative_stage_review.png"):
        path = OUT / name
        with Image.open(path) as image:
            outputs[name] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size": list(image.size),
            }
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "source_response": str(RESPONSE_PATH.relative_to(ROOT)),
                "request_id": payload["request_id"],
                "modal_call_id": payload["modal_call_id"],
                "asset_id": payload["reference_source"]["asset_id"],
                "declared_source_sha256": payload["reference_source"]["source_sha256"],
                "path_count": len(segments),
                "atlas_labels": [f"P{index:02d}" for index in range(1, len(segments) + 1)],
                "stage_manifest": manifest,
                "outputs": outputs,
                "note": "Local renderer preflight from a prior synthetic response; no model call.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"out": str(OUT), "outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
