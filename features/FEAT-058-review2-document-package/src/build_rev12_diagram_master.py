"""Build a clean, editable 46-page Draw.io master without changing supplied originals."""

from __future__ import annotations

import copy
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


FEATURE = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path.home() / "Downloads"
SOURCE_EXPORTS = FEATURE / "evidence" / "render" / "rev11" / "supplied-diagrams"
CLEAN_EXPORTS = FEATURE / "evidence" / "render" / "rev12" / "supplied-diagrams-clean"
DIAGRAM_DIR = FEATURE / "artifacts" / "diagrams" / "rev12" / "drawio"
GENERATED_MASTER = DIAGRAM_DIR / "Sketch2Life-Review2-State-and-Activity.drawio"
FULL_MASTER = DIAGRAM_DIR / "Sketch2Life-Review2-Diagram-Master.drawio"
QA_PATH = FEATURE / "evidence" / "diagram-master-qa-rev12.json"

SOURCE_GROUPS = [
    (
        "Sketch2Life-Context.drawio",
        "context",
        [
            ("D01", "Business Context", "Context Diagram"),
            ("D02", "C4 System Context", "C4 System Context Diagram"),
        ],
    ),
    (
        "Sketch2Life-Use-Cases.drawio",
        "usecases",
        [(f"D{index:02d}", f"Use Case Details — page {index - 2}" if index > 3 else "Use Case Overview", "UML Use Case Diagram") for index in range(3, 15)],
    ),
    (
        "Sketch2Life-Main-Session-Sequence.drawio",
        "sequence",
        [
            ("D15", "Main Session Sequence", "UML Sequence Diagram"),
            ("D16", "Detailed Session Sequence", "UML Sequence Diagram"),
        ],
    ),
    (
        "THieuDiagram.drawio",
        "thieu",
        [
            ("D17", "Screen Flow", "Screen Flow Diagram"),
            ("D18", "Class Diagram", "UML Class Diagram"),
            ("D19", "Logical ERD", "Logical Entity-Relationship Diagram"),
        ],
    ),
    (
        "Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio",
        "khoa",
        [
            ("D20", "Khoa ERD", "Entity-Relationship Diagram"),
            ("D21", "System Architecture", "System Architecture Diagram"),
            ("D22", "Package Diagram", "UML Package Diagram"),
        ],
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remove_source_footnotes(diagram: ET.Element) -> list[ET.Element]:
    parents = {child: parent for parent in diagram.iter() for child in parent}
    removed = []
    for cell in list(diagram.iter("mxCell")):
        value = (cell.get("value") or "").strip()
        if value.casefold().startswith("nguồn:"):
            parent = parents.get(cell)
            if parent is None:
                raise ValueError(f"Cannot locate parent for attribution cell {cell.get('id')}")
            parent.remove(cell)
            removed.append(cell)
    return removed


def clean_export(image_path: Path, model: ET.Element, source_page: str) -> dict | None:
    candidates = [cell for cell in model.iter("mxCell") if (cell.get("value") or "").strip().casefold().startswith("nguồn:")]
    if not candidates:
        image_path_out = CLEAN_EXPORTS / image_path.name
        image_path_out.parent.mkdir(parents=True, exist_ok=True)
        image_path_out.write_bytes(image_path.read_bytes())
        return None
    if len(candidates) != 1:
        raise ValueError(f"{source_page}: expected one source attribution cell, found {len(candidates)}")
    cell = candidates[0]
    geometry = cell.find("mxGeometry")
    graph = model.find("mxGraphModel")
    if geometry is None or graph is None:
        raise ValueError(f"{source_page}: source cell or page geometry is missing")
    page_w = float(graph.get("pageWidth", "0"))
    page_h = float(graph.get("pageHeight", "0"))
    x, y = (float(geometry.get(key, "0")) for key in ("x", "y"))
    w, h = (float(geometry.get(key, "0")) for key in ("width", "height"))
    if min(page_w, page_h, w, h) <= 0:
        raise ValueError(f"{source_page}: invalid page or source-cell dimensions")

    with Image.open(image_path) as source_image:
        image = source_image.convert("RGB")
    scale_x = image.width / page_w
    scale_y = image.height / page_h
    # Draw.io's PNG export clips close to the page boundary; allow enough room
    # to clear antialiased footer glyphs that sit on the bottom edge.
    padding_x = max(6, round(8 * scale_x))
    padding_y = max(12, round(16 * scale_y))
    box = (
        max(0, round(x * scale_x) - padding_x),
        max(0, round(y * scale_y) - padding_y),
        min(image.width, round((x + w) * scale_x) + padding_x),
        min(image.height, round((y + h) * scale_y) + padding_y),
    )
    ImageDraw.Draw(image).rectangle(box, fill=(255, 255, 255))
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path_out = CLEAN_EXPORTS / image_path.name
    image.save(image_path_out, optimize=True)
    return {
        "source_page": source_page,
        "cell_id": cell.get("id"),
        "cell_text": cell.get("value"),
        "rendered_image": image_path.name,
        "cleared_pixel_box": list(box),
    }


def main() -> None:
    CLEAN_EXPORTS.mkdir(parents=True, exist_ok=True)
    for old in CLEAN_EXPORTS.glob("*_page*.png"):
        old.unlink()
    master = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "agent": "Sketch2Life Review 2 Rev12",
            "version": "32.6.1",
        },
    )
    original_records = []
    removed_attributions = []
    source_page_number = 0

    for filename, export_prefix, page_specs in SOURCE_GROUPS:
        source_path = SOURCE_DIR / filename
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        source_root = ET.parse(source_path).getroot()
        source_pages = source_root.findall("diagram")
        if len(source_pages) != len(page_specs):
            raise ValueError(f"{filename}: expected {len(page_specs)} pages, found {len(source_pages)}")
        original_records.append({"file": filename, "sha256": sha256(source_path), "pages": len(source_pages)})

        for page_index, (diagram, (figure_id, title, diagram_type)) in enumerate(zip(source_pages, page_specs), start=1):
            source_page_number += 1
            if diagram.find("mxGraphModel") is None:
                raise ValueError(f"{filename}: page {page_index} is compressed or has no editable graph model")
            image_path = SOURCE_EXPORTS / f"{export_prefix}_page{page_index:02d}.png"
            if not image_path.is_file():
                raise FileNotFoundError(image_path)
            clean_export(image_path, diagram, f"{figure_id} {title}")

            clean_page = copy.deepcopy(diagram)
            removed = remove_source_footnotes(clean_page)
            for cell in removed:
                removed_attributions.append({
                    "figure": figure_id,
                    "title": title,
                    "diagram_type": diagram_type,
                    "source_file": filename,
                    "cell_id": cell.get("id"),
                })
            clean_page.set("id", f"rev12-source-page-{source_page_number:02d}")
            clean_page.set("name", f"{figure_id} · {diagram_type} — {title}")
            master.append(clean_page)

    generated_root = ET.parse(GENERATED_MASTER).getroot()
    generated_pages = generated_root.findall("diagram")
    if len(generated_pages) != 24:
        raise ValueError(f"Generated state/activity master must have 24 pages, found {len(generated_pages)}")
    for offset, source_page in enumerate(generated_pages, start=23):
        page = copy.deepcopy(source_page)
        page.set("id", f"rev12-generated-page-{offset:02d}")
        page.set("name", f"D{offset:02d} · {source_page.get('name', '')}")
        master.append(page)

    DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    ET.indent(master, space="  ")
    ET.ElementTree(master).write(FULL_MASTER, encoding="utf-8", xml_declaration=True)
    xml_root = ET.parse(FULL_MASTER).getroot()
    if len(xml_root.findall("diagram")) != 46:
        raise ValueError("Final master does not contain exactly 46 pages")
    visible_attributions = [
        cell.get("value")
        for cell in xml_root.iter("mxCell")
        if (cell.get("value") or "").strip().casefold().startswith("nguồn:")
    ]
    if visible_attributions:
        raise ValueError(f"Source attributions remain in the final master: {visible_attributions}")

    qa = {
        "revision": "Rev12",
        "master": FULL_MASTER.name,
        "page_count": 46,
        "supplied_pages": 22,
        "new_state_machine_pages": 20,
        "new_activity_pages": 4,
        "source_files": original_records,
        "source_cells_removed_from_derived_master": removed_attributions,
        "source_files_modified": False,
        "output_sha256": sha256(FULL_MASTER),
        "remaining_attribution_cells": 0,
    }
    QA_PATH.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(xml_root.findall('diagram'))} editable pages; removed {len(removed_attributions)} source footnotes from the derived master.")
    print(f"Master: {FULL_MASTER}")
    print(f"QA: {QA_PATH}")


if __name__ == "__main__":
    main()
