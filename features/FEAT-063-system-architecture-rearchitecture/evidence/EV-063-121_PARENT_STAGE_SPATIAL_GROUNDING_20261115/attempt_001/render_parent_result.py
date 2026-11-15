from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

ATTEMPT_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
RESPONSE_PATH = ATTEMPT_DIR / "response.json"
OUT = ATTEMPT_DIR / "rendered_v4"
RENDERER = (
    ROOT
    / "features/FEAT-063-system-architecture-rearchitecture/evidence/"
    / "EV-063-119_PARENT_SOURCE_SEGMENT_GUIDE_20261115/render_rev87_24_svg.ps1"
)
SVG_NS = "http://www.w3.org/2000/svg"
sys.path.insert(0, str(ROOT / "deployment/modal/srs_v23"))

import language_audio_app as worker  # noqa: E402


def render_svg_to_png(svg: bytes, target: Path) -> None:
    source = target.with_suffix(".svg")
    source.write_bytes(svg)
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(RENDERER),
            "-InputSvg",
            str(source),
            "-OutputPng",
            str(target),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def svg_to_png_adapter(*, bytestring: bytes, output_width: int, output_height: int, background_color: str) -> bytes:
    del background_color
    OUT.mkdir(parents=True, exist_ok=True)
    raster_count = len(list(OUT.glob("raster_*.svg")))
    png_path = (
        OUT / "source_color_reference.png"
        if raster_count == 0
        else OUT / f"raster_{raster_count:03d}.png"
    )
    render_svg_to_png(bytestring, png_path)
    with Image.open(png_path) as opened:
        rendered = opened.convert("RGB")
        if rendered.size != (output_width, output_height):
            rendered = rendered.resize((output_width, output_height), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        rendered.save(buffer, format="PNG")
        return buffer.getvalue()


def main() -> None:
    ET.register_namespace("", SVG_NS)
    sys.modules["cairosvg"] = SimpleNamespace(svg2png=svg_to_png_adapter)
    payload = json.loads(RESPONSE_PATH.read_text(encoding="utf-8"))
    ref = payload["reference_illustration"]
    source_paths = [
        {
            "path_id": path["path_id"],
            "d": path["d"],
            "fill": path["fill"],
            "stroke": path["stroke"],
            "stroke_width": path["stroke_width"],
            "stroke_linecap": path.get("stroke_linecap", "round"),
            "stroke_linejoin": path.get("stroke_linejoin", "round"),
        }
        for path in ref["paths"]
    ]
    path_by_id = {path["path_id"]: path for path in payload["document"]["paths"]}
    source_path_by_id = {
        item["derived_path_id"]: item["source_path_ids"][0]
        for item in payload["derivation"]["path_lineage"]
    }
    segments = [
        {
            "path_id": path["path_id"],
            "source_path_id": source_path_by_id[path["path_id"]],
            "d": path["d"],
        }
        for path in sorted(
            payload["document"]["paths"],
            key=lambda item: int(item["path_id"].rsplit("_", 1)[1]),
        )
    ]
    candidate = {
        "asset_id": payload["reference_source"]["asset_id"],
        "parsed_svg": {"view_box": ref["view_box"], "paths": source_paths},
    }
    plan = {
        "stages": [
            {"step_index": stage["step_index"], "path_ids": stage["new_path_ids"]}
            for stage in payload["guide"]["stages"]
        ]
    }
    OUT.mkdir(parents=True, exist_ok=True)
    source_image, atlas = worker._render_openclipart_candidate(
        candidate, atlas_paths=segments, atlas_view_box="0 0 512 512"
    )
    review_sheet, review_manifest = worker._render_openclipart_cumulative_stage_review(
        candidate, segments, plan
    )
    source_image.save(OUT / "source_color_reference.png")
    atlas.save(OUT / "spatial_segment_atlas.png")
    review_sheet.save(OUT / "cumulative_stage_review.png")

    cumulative: list[str] = []
    stage_artifacts = []
    for stage in payload["guide"]["stages"]:
        new_ids = list(stage["new_path_ids"])
        cumulative.extend(new_ids)
        new_id_set = set(new_ids)
        root = ET.Element(
            f"{{{SVG_NS}}}svg",
            {"viewBox": payload["document"]["view_box"], "width": "512", "height": "512"},
        )
        for path_id in cumulative:
            path = path_by_id[path_id]
            ET.SubElement(
                root,
                f"{{{SVG_NS}}}path",
                {
                    "d": path["d"],
                    "fill": "none",
                    "stroke": "#075dff" if path_id in new_id_set else "#aeb8c8",
                    "stroke-width": "8",
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round",
                },
            )
        number = stage["step_index"]
        image_path = OUT / f"cumulative_stage_{number:02d}.png"
        render_svg_to_png(ET.tostring(root, encoding="utf-8"), image_path)
        stage_artifacts.append(
            {
                "step_index": number,
                "instruction_vi": stage["instruction_vi"],
                "new_path_ids": new_ids,
                "new_segment_labels": review_manifest[number - 1]["new_segment_labels"],
                "svg": image_path.with_suffix(".svg").name,
                "png": image_path.name,
                "png_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
            }
        )

    manifest = {
        "request_id": payload["request_id"],
        "modal_call_id": payload["modal_call_id"],
        "asset_id": payload["reference_source"]["asset_id"],
        "declared_source_sha256": payload["reference_source"]["source_sha256"],
        "path_count": len(segments),
        "stage_count": len(stage_artifacts),
        "render_method": "Windows WPF; returned document path data preserved; previous strokes gray, new blue",
        "stage_artifacts": stage_artifacts,
        "atlas_size": list(atlas.size),
        "contact_sheet_size": list(review_sheet.size),
        "provenance_note": "Reference SVG was reconstructed from the route response representation; its serialized hash is not claimed to equal the catalog's raw-source hash.",
    }
    (OUT / "render_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
