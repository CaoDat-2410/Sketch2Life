"""Build review-ready, editable Draw.io diagrams and matching PNG evidence."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
FEATURE = HERE.parents[2]
SOURCES = FEATURE / "artifacts" / "diagrams" / "rev10" / "mermaid"
OUTPUT = HERE / "drawio"
PREVIEWS = FEATURE / "evidence" / "render" / "rev11" / "diagrams"
ELK_SCRIPT = HERE / "layout_rev11.mjs"
NODE = shutil.which("node") or "node"
ELK_NODE_MODULES = HERE / "node_modules"
ELK_MODULE_PATH = ELK_NODE_MODULES / "elkjs" / "lib" / "main.js"


def find_font(*names: str) -> Path:
    roots = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype/liberation"),
        Path("/Library/Fonts"),
    ]
    for root in roots:
        for name in names:
            candidate = root / name
            if candidate.exists():
                return candidate
    raise FileNotFoundError(f"Could not locate a usable font: {', '.join(names)}")


FONT_REGULAR = find_font("arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf")
FONT_BOLD = find_font("arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf")

PAGE_NAMES = [
    "Session-Lifecycle", "Session-Pause-Recovery-Companion", "Session-Early-Termination-Companion",
    "Shared-Learning-Stage-Lifecycle", "Group-Progress-Lifecycle", "Participant-Admission",
    "Device-Connection", "Device-Grant-Revocation-Companion", "Draft-Sync-Lifecycle",
    "Sketch-Pipeline-Lifecycle", "Child-Suggestion-Response-Lifecycle", "Knowledge-Editorial-Lifecycle",
    "AI-Media-Job", "Video-Delivery", "Activity-Execution-Lifecycle", "Observation-Lifecycle",
    "Content-Publication-Lifecycle", "Data-Request-Lifecycle", "WF-01-Prepare-Admit",
    "WF-02-Collaborative-Drawing", "WF-03-AI-Sketch-Review", "WF-04-Reviewed-Learning-Close",
]

TITLE_BY_FILE = {
    "Session-Lifecycle": "Session Lifecycle",
    "Session-Pause-Recovery-Companion": "Session Pause and Recovery",
    "Session-Early-Termination-Companion": "Session Early Termination",
    "Shared-Learning-Stage-Lifecycle": "Shared Learning Stage Lifecycle",
    "Group-Progress-Lifecycle": "Group Progress Lifecycle",
    "Participant-Admission": "Participant Admission Lifecycle",
    "Device-Connection": "Device Connection Lifecycle",
    "Device-Grant-Revocation-Companion": "Device Grant Revocation",
    "Draft-Sync-Lifecycle": "Draft Synchronization Lifecycle",
    "Sketch-Pipeline-Lifecycle": "Sketch Pipeline Lifecycle",
    "Child-Suggestion-Response-Lifecycle": "Child Suggestion Response Lifecycle",
    "Knowledge-Editorial-Lifecycle": "Knowledge Editorial Lifecycle",
    "AI-Media-Job": "AI and Media Job Lifecycle",
    "Video-Delivery": "Video Delivery Lifecycle",
    "Activity-Execution-Lifecycle": "Activity Execution Lifecycle",
    "Observation-Lifecycle": "Observation Lifecycle",
    "Content-Publication-Lifecycle": "Content Publication Lifecycle",
    "Data-Request-Lifecycle": "Data Request Lifecycle",
    "WF-01-Prepare-Admit": "WF-01 Prepare and Admit",
    "WF-02-Collaborative-Drawing": "WF-02 Collaborative Drawing and Recovery",
    "WF-03-AI-Sketch-Review": "WF-03 Request and Review AI Sketch",
    "WF-04-Reviewed-Learning-Close": "WF-04 Reviewed Learning and Session Close",
}

EDGE_PATTERN = re.compile(
    r"^\s*(?P<left>\[\*\]|[A-Za-z0-9_]+)(?:\[(?P<left_label>[^\]]*)\])?\s*"
    r"(?P<arrow>-\.(?P<dashed_label>[^.]*)\.->|-->)\s*"
    r"(?:\|(?P<pipe_label>[^|]*)\|\s*)?"
    r"(?P<right>\[\*\]|[A-Za-z0-9_]+)(?:\[(?P<right_label>[^\]]*)\])?"
    r"(?:\s*:\s*(?P<colon_label>.+))?\s*$"
)


def wrap_chars(text: str, limit: int) -> list[str]:
    return textwrap.wrap(text, width=limit, break_long_words=True, break_on_hyphens=False) or [""]


def spaced_state_name(text: str) -> str:
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    words = text.replace("_", " ").split()
    return " ".join(word[:1].upper() + word[1:] for word in words)


def measured_line_count(text: str, font_path: Path, size: int, max_width: int) -> int:
    ft = ImageFont.truetype(str(font_path), size=size)
    words = text.split()
    if not words:
        return 1
    lines = 1
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and ft.getlength(candidate) > max_width:
            lines += 1
            current = word
        else:
            current = candidate
    return lines


def dimensions(label: str, kind: str, category: str) -> tuple[int, int]:
    if kind == "start":
        return (24, 24)
    if kind == "note":
        width = 310
        lines = measured_line_count(label, FONT_REGULAR, 17, width - 24)
        return (width, max(78, 24 + 22 * lines))
    if category == "activity":
        width = 244
        lines = measured_line_count(label, FONT_REGULAR, 20, width - 24)
        return (width, max(72, 24 + 23 * lines))
    lines = wrap_chars(label, 15)
    widest = max(map(len, lines), default=1)
    width = max(156, min(244, 48 + 12 * widest))
    line_count = measured_line_count(label, FONT_REGULAR, 21, width - 24)
    return (width, 58 + max(0, line_count - 1) * 26)


def edge_label_size(label: str, category: str) -> tuple[int, int]:
    limit = 25 if category == "activity" else 20
    lines = wrap_chars(label, limit)
    widest = min(limit, max(map(len, lines), default=0))
    return (max(82, min(280, 16 + 10 * widest)), max(28, 8 + 22 * len(lines)))


def parse_mermaid(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    category = "activity" if source.lstrip().startswith("flowchart") else "state"
    title = TITLE_BY_FILE[path.stem]
    diagram_type = "Activity Diagram" if category == "activity" else "State Machine Diagram"
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def register_node(raw_id: str, label: str | None = None, kind: str | None = None) -> str:
        if raw_id == "[*]":
            key = "__start"
            label, kind = "", "start"
        else:
            key = raw_id
            if kind is None:
                kind = "process" if category == "activity" else "state"
        item = nodes.setdefault(key, {"id": key, "label": label or raw_id, "kind": kind})
        if label:
            item["label"] = label
        if kind:
            item["kind"] = kind
        return key

    edge_count = 0
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("stateDiagram", "flowchart")):
            continue
        note = re.match(r"note\s+right\s+of\s+([A-Za-z0-9_]+)\s*:\s*(.+)$", stripped)
        if note:
            target = register_node(note.group(1))
            note_id = "__note"
            nodes[note_id] = {"id": note_id, "label": note.group(2).strip(), "kind": "note"}
            edges.append({"id": f"e{edge_count:02d}", "source": target, "target": note_id, "label": "", "relation": True})
            edge_count += 1
            continue
        match = EDGE_PATTERN.match(stripped)
        if not match:
            raise ValueError(f"Unparsed Mermaid line in {path.name}: {stripped}")
        left = register_node(match.group("left"), match.group("left_label"))
        right = register_node(match.group("right"), match.group("right_label"))
        label = (match.group("pipe_label") or match.group("dashed_label") or match.group("colon_label") or "").strip()
        dashed = match.group("arrow").startswith("-.")
        width, height = edge_label_size(label, category) if label else (0, 0)
        edges.append({
            "id": f"e{edge_count:02d}", "source": left, "target": right,
            "label": label, "labelWidth": width, "labelHeight": height,
            "dashed": dashed, "relation": False,
        })
        edge_count += 1
    if not nodes or not edges:
        raise ValueError(f"No graph content in {path}")
    prepared_nodes = []
    for node in nodes.values():
        if node["kind"] == "state":
            node["label"] = spaced_state_name(node["label"])
        width, height = dimensions(node["label"], node["kind"], category)
        prepared_nodes.append({**node, "width": width, "height": height})
    return {
        "source": path.name,
        "kind": category,
        "title": title,
        "diagramType": diagram_type,
        "nodes": prepared_nodes,
        "edges": edges,
    }


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def fit_lines(draw: ImageDraw.ImageDraw, text: str, ft: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=ft)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def node_colors(node: dict, category: str) -> tuple[str, str]:
    if node["kind"] == "start":
        return ("#1F2937", "#1F2937")
    if node["kind"] == "note":
        return ("#FFF6D7", "#C99A20")
    if category == "state":
        return ("#FFFFFF", "#456A9C")
    prefix = node["id"][:1].upper()
    return {
        "T": ("#EAF2FF", "#4777B5"),
        "C": ("#E8F5EE", "#47845C"),
        "B": ("#F1EDFF", "#7359A5"),
        "W": ("#FFF1E7", "#C47736"),
        "M": ("#FFF6D7", "#B28A28"),
    }.get(prefix, ("#F3F5F8", "#6B7280"))


def parse_layout(diagram: dict) -> dict:
    return diagram["layout"]


def render_preview(diagram: dict, image_path: Path) -> None:
    graph = parse_layout(diagram)
    x_margin, y_header, scale = 46, 124, 2
    graph_w, graph_h = math.ceil(graph["width"]), math.ceil(graph["height"])
    width = max(960, graph_w + 2 * x_margin)
    height = max(680, graph_h + y_header + 36)
    image = Image.new("RGB", (width * scale, height * scale), "#F5F7FB")
    draw = ImageDraw.Draw(image)
    title_font = font(FONT_BOLD, 27 * scale)
    type_font = font(FONT_BOLD, 15 * scale)
    node_font = font(FONT_REGULAR, 21 * scale if diagram["kind"] == "state" else 20 * scale)
    edge_font = font(FONT_REGULAR, 16 * scale)
    note_font = font(FONT_REGULAR, 17 * scale)

    def sc(point: dict) -> tuple[int, int]:
        return (round((x_margin + point["x"]) * scale), round((y_header + point["y"]) * scale))

    # Page title and diagram-type marker are part of every diagram canvas.
    draw.rounded_rectangle((20 * scale, 16 * scale, width * scale - 20 * scale, 104 * scale), radius=16 * scale, fill="#FFFFFF", outline="#DFE5EE", width=2 * scale)
    draw.rounded_rectangle((36 * scale, 30 * scale, 282 * scale, 62 * scale), radius=14 * scale, fill="#E8F0FB", outline="#D1DEEF", width=1 * scale)
    type_text = diagram["diagramType"].upper()
    tbox = draw.textbbox((0, 0), type_text, font=type_font)
    draw.text((159 * scale - (tbox[2] - tbox[0]) / 2, 36 * scale), type_text, font=type_font, fill="#345B89")
    draw.text((38 * scale, 66 * scale), diagram["title"], font=title_font, fill="#1F2937")

    nodes = {node["id"]: node for node in diagram["nodes"]}
    laid_nodes = {node["id"]: node for node in graph["children"]}

    # Orthogonal edges first so nodes and labels sit above the strokes.
    for index, edge in enumerate(graph["edges"]):
        for section in edge.get("sections", []):
            points = [section["startPoint"], *section.get("bendPoints", []), section["endPoint"]]
            points = [sc(point) for point in points]
            if len(points) >= 2:
                if edge.get("id", "") in {item["id"] for item in diagram["edges"] if item.get("relation")}:
                    # Notes use a light dashed association without an arrow.
                    for a, b in zip(points, points[1:]):
                        draw_dashed_line(draw, a, b, fill="#C9A23A", width=2 * scale, dash=9 * scale, gap=7 * scale)
                else:
                    stroke = "#566579"
                    for a, b in zip(points, points[1:]):
                        if next((item for item in diagram["edges"] if item["id"] == edge["id"]), {}).get("dashed"):
                            draw_dashed_line(draw, a, b, fill=stroke, width=2 * scale, dash=9 * scale, gap=7 * scale)
                        else:
                            draw.line((a, b), fill=stroke, width=2 * scale, joint="curve")
                    draw_arrowhead(draw, points[-2], points[-1], stroke, 11 * scale)
        for label in edge.get("labels", []):
            x, y = round((x_margin + label["x"]) * scale), round((y_header + label["y"]) * scale)
            w, h = round(label["width"] * scale), round(label["height"] * scale)
            draw.rounded_rectangle((x - 6 * scale, y - 3 * scale, x + w + 6 * scale, y + h + 3 * scale), radius=6 * scale, fill="#FFFFFF", outline="#E6EAF0", width=1 * scale)
            lines = fit_lines(draw, label["text"], edge_font, w)
            line_height = 19 * scale
            total_h = len(lines) * line_height
            y0 = y + (h - total_h) // 2
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=edge_font)
                draw.text((x + (w - (bbox[2] - bbox[0])) // 2, y0), line, font=edge_font, fill="#263445")
                y0 += line_height

    for crossing in route_crossing_details(graph):
        if diagram["title"] != "Data Request Lifecycle" or frozenset(crossing["edges"]) != frozenset(("e08", "e12")):
            continue
        cx = round((x_margin + crossing["x"]) * scale)
        cy = round((y_header + crossing["y"]) * scale)
        radius = 11 * scale
        draw.rectangle((cx - radius, cy - radius, cx + radius, cy + radius), fill="#F5F7FB")
        draw.line((cx - radius, cy, cx + radius, cy), fill="#566579", width=2 * scale)
        bridge = [
            (cx, cy - radius), (cx + 4 * scale, cy - 9 * scale),
            (cx + 7 * scale, cy - 5 * scale), (cx + 8 * scale, cy),
            (cx + 7 * scale, cy + 5 * scale), (cx + 4 * scale, cy + 9 * scale),
            (cx, cy + radius),
        ]
        draw.line(bridge, fill="#566579", width=2 * scale, joint="curve")

    # Nodes are drawn over their incoming/outgoing lines.
    for node in diagram["nodes"]:
        placed = laid_nodes[node["id"]]
        x, y = sc(placed)
        w, h = round(placed["width"] * scale), round(placed["height"] * scale)
        fill, stroke = node_colors(node, diagram["kind"])
        if node["kind"] == "start":
            cx, cy = x + w // 2, y + h // 2
            draw.ellipse((cx - 9 * scale, cy - 9 * scale, cx + 9 * scale, cy + 9 * scale), fill=fill, outline=stroke)
            continue
        radius = 16 * scale if diagram["kind"] == "state" else 12 * scale
        draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=stroke, width=2 * scale)
        ft = note_font if node["kind"] == "note" else node_font
        lines = fit_lines(draw, node["label"], ft, w - 24 * scale)
        line_height = (22 if node["kind"] == "note" else 24 if diagram["kind"] == "state" else 22) * scale
        text_h = len(lines) * line_height
        ty = y + (h - text_h) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=ft)
            draw.text((x + (w - (bbox[2] - bbox[0])) // 2, ty), line, font=ft, fill="#263445")
            ty += line_height

    image = image.resize((width, height), Image.Resampling.LANCZOS)
    image.save(image_path, format="PNG", optimize=True)


def draw_dashed_line(draw: ImageDraw.ImageDraw, a: tuple[int, int], b: tuple[int, int], *, fill: str, width: int, dash: int, gap: int) -> None:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    cursor = 0.0
    while cursor < length:
        end = min(length, cursor + dash)
        draw.line((round(a[0] + ux * cursor), round(a[1] + uy * cursor), round(a[0] + ux * end), round(a[1] + uy * end)), fill=fill, width=width)
        cursor = end + gap


def draw_arrowhead(draw: ImageDraw.ImageDraw, a: tuple[int, int], b: tuple[int, int], color: str, size: int) -> None:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = max(1, math.hypot(dx, dy))
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    base = (b[0] - size * ux, b[1] - size * uy)
    points = [b, (round(base[0] + size * 0.55 * px), round(base[1] + size * 0.55 * py)), (round(base[0] - size * 0.55 * px), round(base[1] - size * 0.55 * py))]
    draw.polygon(points, fill=color)


def add_text_cell(root: ET.Element, *, cell_id: str, value: str, x: float, y: float, w: float, h: float, style: str) -> None:
    cell = ET.SubElement(root, "mxCell", {"id": cell_id, "value": value, "style": style, "vertex": "1", "parent": "1"})
    ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"})


def build_drawio(diagrams: list[dict]) -> None:
    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "modified": "2026-10-24T00:00:00.000Z", "agent": "Sketch2Life Review 2 Rev11", "version": "32.6.1"})
    for page_number, diagram in enumerate(diagrams, start=1):
        graph = diagram["layout"]
        header = 124
        pad_x = 46
        page_w = max(960, math.ceil(graph["width"] + 2 * pad_x))
        page_h = max(680, math.ceil(graph["height"] + header + 36))
        page_name = f"{diagram['diagramType']} — {diagram['title']}"
        page = ET.SubElement(mxfile, "diagram", {"id": f"rev11-page-{page_number:02d}", "name": page_name})
        model = ET.SubElement(page, "mxGraphModel", {"grid": "0", "gridSize": "10", "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1", "fold": "0", "page": "1", "pageScale": "1", "pageWidth": str(page_w), "pageHeight": str(page_h), "math": "0", "shadow": "0"})
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
        add_text_cell(root, cell_id="type", value=diagram["diagramType"].upper(), x=pad_x, y=24, w=260, h=30, style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#E8F0FB;strokeColor=#D1DEEF;fontColor=#345B89;fontStyle=1;fontSize=14;align=center;verticalAlign=middle;")
        add_text_cell(root, cell_id="title", value=diagram["title"], x=pad_x, y=64, w=page_w - 2 * pad_x, h=44, style="text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;fontColor=#1F2937;fontStyle=1;fontSize=25;align=left;verticalAlign=middle;")
        node_map = {node["id"]: node for node in diagram["nodes"]}
        placed_nodes = {node["id"]: node for node in graph["children"]}
        for idx, node in enumerate(diagram["nodes"], start=1):
            placed = placed_nodes[node["id"]]
            fill, stroke = node_colors(node, diagram["kind"])
            x, y = pad_x + placed["x"], header + placed["y"]
            w, h = placed["width"], placed["height"]
            if node["kind"] == "start":
                style = f"ellipse;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=1;"
                cell = ET.SubElement(root, "mxCell", {"id": f"n{idx}", "value": "", "style": style, "vertex": "1", "parent": "1"})
            else:
                radius = "rounded=1;arcSize=10;" if node["kind"] != "note" else "shape=note;size=16;"
                style = f"{radius}html=1;whiteSpace=wrap;align=center;verticalAlign=middle;strokeWidth=1.6;fillColor={fill};strokeColor={stroke};fontColor=#263445;fontFamily=Arial;fontSize={16 if node['kind'] != 'note' else 14};"
                cell = ET.SubElement(root, "mxCell", {"id": f"n{idx}", "value": node["label"], "style": style, "vertex": "1", "parent": "1"})
            ET.SubElement(cell, "mxGeometry", {"x": f"{x:.1f}", "y": f"{y:.1f}", "width": f"{w:.1f}", "height": f"{h:.1f}", "as": "geometry"})
            node["drawioId"] = f"n{idx}"
        edge_by_id = {edge["id"]: edge for edge in diagram["edges"]}
        edge_idx = 1
        for edge in graph["edges"]:
            source = edge_by_id[edge["id"]]
            section = (edge.get("sections") or [None])[0]
            if section is None:
                continue
            cell_id = f"e{edge_idx}"
            edge_idx += 1
            is_relation = source.get("relation", False)
            dashed = is_relation or source.get("dashed", False)
            label = source.get("label", "") if not is_relation else ""
            style = "edgeStyle=orthogonalEdgeStyle;orthogonalLoop=1;jettySize=auto;rounded=1;html=1;strokeColor=#566579;strokeWidth=1.4;endArrow=block;endFill=1;"
            if diagram["title"] == "Data Request Lifecycle" and source["id"] == "e08":
                style += "jumpStyle=arc;jumpSize=8;"
            if dashed:
                style += "dashed=1;dashPattern=6 5;"
            if is_relation:
                style += "endArrow=none;strokeColor=#C9A23A;"
            cell = ET.SubElement(root, "mxCell", {"id": cell_id, "value": label, "style": style + "fontColor=#263445;fontFamily=Arial;fontSize=13;labelBackgroundColor=#FFFFFF;whiteSpace=wrap;", "edge": "1", "parent": "1", "source": node_map[source["source"]]["drawioId"], "target": node_map[source["target"]]["drawioId"]})
            geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            bend_points = section.get("bendPoints", [])
            if bend_points:
                array = ET.SubElement(geometry, "Array", {"as": "points"})
                for point in bend_points:
                    ET.SubElement(array, "mxPoint", {"x": f"{pad_x + point['x']:.1f}", "y": f"{header + point['y']:.1f}"})
            labels = edge.get("labels", [])
            if label and labels:
                label_box = labels[0]
                path_points = [section["startPoint"], *section.get("bendPoints", []), section["endPoint"]]
                mid_x, mid_y = polyline_midpoint(path_points)
                offset_x = label_box["x"] + label_box["width"] / 2 - mid_x
                offset_y = label_box["y"] + label_box["height"] / 2 - mid_y
                offset = ET.SubElement(geometry, "mxPoint", {"x": f"{offset_x:.1f}", "y": f"{offset_y:.1f}", "as": "offset"})
        ET.indent(model, space="  ")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ET.indent(mxfile, space="  ")
    ET.ElementTree(mxfile).write(OUTPUT / "Sketch2Life-Review2-State-and-Activity.drawio", encoding="utf-8", xml_declaration=True)


def correct_cyclic_start_layout(diagram: dict) -> None:
    """Keep the initial marker attached to Draft in the cyclic publication graph."""
    if diagram["title"] != "Content Publication Lifecycle":
        return
    graph = diagram["layout"]
    placed = {node["id"]: node for node in graph["children"]}
    start, draft = placed["__start"], placed["Draft"]
    # Put the initial marker to the right of Draft. A vertical line above Draft
    # would cross the long “revised version only” transition label in this graph.
    start["x"] = draft["x"] + draft["width"] + 70
    start["y"] = draft["y"] + (draft["height"] - start["height"]) / 2
    initial = next(edge for edge in graph["edges"] if edge["sources"] == ["__start"] and edge["targets"] == ["Draft"])
    section = initial["sections"][0]
    section["startPoint"] = {"x": start["x"], "y": draft["y"] + draft["height"] / 2}
    section["endPoint"] = {"x": draft["x"] + draft["width"], "y": draft["y"] + draft["height"] / 2}
    section.pop("bendPoints", None)


def set_edge_route(graph: dict, edge_id: str, points: list[tuple[float, float]]) -> None:
    edge = next(edge for edge in graph["edges"] if edge["id"] == edge_id)
    if len(points) < 2:
        raise ValueError(f"A route needs at least two points: {edge_id}")
    section = (edge.get("sections") or [None])[0]
    if section is None:
        raise ValueError(f"ELK did not return a route for {edge_id}")
    section["startPoint"] = {"x": points[0][0], "y": points[0][1]}
    section["endPoint"] = {"x": points[-1][0], "y": points[-1][1]}
    bends = [{"x": x, "y": y} for x, y in points[1:-1]]
    if bends:
        section["bendPoints"] = bends
    else:
        section.pop("bendPoints", None)


def apply_reviewed_layout_fixes(diagram: dict) -> None:
    """Keep the dense device revocation route outside the reconnect loop."""
    graph = diagram["layout"]
    placed = {node["id"]: node for node in graph["children"]}

    if diagram["title"] == "Device Connection Lifecycle":
        # Take the Authenticated -> Revoked transition around the right perimeter.
        # Its previous vertical lane crossed the reconnect loop from Disconnected.
        authenticated, revoked = placed["Authenticated"], placed["Revoked"]
        start = (authenticated["x"] + authenticated["width"], authenticated["y"] + authenticated["height"] / 2)
        end = (revoked["x"] + revoked["width"], revoked["y"] + revoked["height"] / 2)
        outer_x = max(graph["width"] + 32, end[0] + 90)
        set_edge_route(graph, "e06", [start, (outer_x, start[1]), (outer_x, end[1]), end])
        graph["width"] = max(graph["width"], outer_x + 24)
        label = next(edge for edge in graph["edges"] if edge["id"] == "e06").get("labels", [])
        if label:
            box = label[0]
            box["x"] = outer_x - box["width"] / 2
            box["y"] = (start[1] + end[1] - box["height"]) / 2

def _rect_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > 1 and min(a[3], b[3]) - max(a[1], b[1]) > 1


def route_crossing_details(graph: dict) -> list[dict]:
    routes = []
    for edge in graph["edges"]:
        section = (edge.get("sections") or [None])[0]
        if not section:
            continue
        points = [section["startPoint"], *section.get("bendPoints", []), section["endPoint"]]
        routes.append((edge["id"], list(zip(points, points[1:]))))
    crossings = []
    for index, (edge_a, segments_a) in enumerate(routes):
        for edge_b, segments_b in routes[index + 1:]:
            for a, b in segments_a:
                for c, d in segments_b:
                    if abs(a["x"] - b["x"]) < 1 and abs(c["y"] - d["y"]) < 1:
                        if min(a["y"], b["y"]) + 1 < c["y"] < max(a["y"], b["y"]) - 1 and min(c["x"], d["x"]) + 1 < a["x"] < max(c["x"], d["x"]) - 1:
                            crossings.append({"edges": [edge_a, edge_b], "x": a["x"], "y": c["y"], "vertical_edge": edge_a, "horizontal_edge": edge_b})
                    elif abs(a["y"] - b["y"]) < 1 and abs(c["x"] - d["x"]) < 1:
                        if min(a["x"], b["x"]) + 1 < c["x"] < max(a["x"], b["x"]) - 1 and min(c["y"], d["y"]) + 1 < a["y"] < max(c["y"], d["y"]) - 1:
                            crossings.append({"edges": [edge_a, edge_b], "x": c["x"], "y": a["y"], "vertical_edge": edge_b, "horizontal_edge": edge_a})
    return crossings


def validate_layout_quality(diagrams: list[dict]) -> dict:
    """Fail the build if text, nodes, or orthogonal routes collide."""
    issues = []
    page_rows = []
    for page, diagram in enumerate(diagrams, start=1):
        graph = diagram["layout"]
        nodes = {node["id"]: node for node in graph["children"]}
        edge_meta = {edge["id"]: edge for edge in diagram["edges"]}
        labels = []
        routes = []
        for edge in graph["edges"]:
            meta = edge_meta[edge["id"]]
            section = (edge.get("sections") or [None])[0]
            if section:
                points = [section["startPoint"], *section.get("bendPoints", []), section["endPoint"]]
                routes.append((edge["id"], meta, list(zip(points, points[1:]))))
            for label in edge.get("labels", []):
                labels.append((edge["id"], (
                    label["x"] - 6,
                    label["y"] - 3,
                    label["x"] + label["width"] + 6,
                    label["y"] + label["height"] + 3,
                )))

        counts = {"label_overlaps": 0, "label_node_overlaps": 0, "node_overlaps": 0, "route_node_collisions": 0, "route_label_collisions": 0, "route_crossings": 0, "bridged_crossings": 0}
        for index, (edge_a, rect_a) in enumerate(labels):
            for edge_b, rect_b in labels[index + 1:]:
                if _rect_overlap(rect_a, rect_b):
                    counts["label_overlaps"] += 1
                    issues.append({"page": page, "title": diagram["title"], "kind": "label-label", "edges": [edge_a, edge_b]})
            for node_id, node in nodes.items():
                if _rect_overlap(rect_a, (node["x"], node["y"], node["x"] + node["width"], node["y"] + node["height"])):
                    counts["label_node_overlaps"] += 1
                    issues.append({"page": page, "title": diagram["title"], "kind": "label-node", "edge": edge_a, "node": node_id})
        for index, node_a in enumerate(graph["children"]):
            rect_a = (node_a["x"], node_a["y"], node_a["x"] + node_a["width"], node_a["y"] + node_a["height"])
            for node_b in graph["children"][index + 1:]:
                rect_b = (node_b["x"], node_b["y"], node_b["x"] + node_b["width"], node_b["y"] + node_b["height"])
                if _rect_overlap(rect_a, rect_b):
                    counts["node_overlaps"] += 1
                    issues.append({"page": page, "title": diagram["title"], "kind": "node-node", "nodes": [node_a["id"], node_b["id"]]})
        for edge_id, meta, segments in routes:
            endpoints = {meta["source"], meta["target"]}
            for node_id, node in nodes.items():
                if node_id in endpoints:
                    continue
                rect = (node["x"], node["y"], node["x"] + node["width"], node["y"] + node["height"])
                for a, b in segments:
                    if abs(a["x"] - b["x"]) < 1:
                        hit = rect[0] < a["x"] < rect[2] and max(min(a["y"], b["y"]), rect[1]) < min(max(a["y"], b["y"]), rect[3])
                    else:
                        hit = rect[1] < a["y"] < rect[3] and max(min(a["x"], b["x"]), rect[0]) < min(max(a["x"], b["x"]), rect[2])
                    if hit:
                        counts["route_node_collisions"] += 1
                        issues.append({"page": page, "title": diagram["title"], "kind": "route-node", "edge": edge_id, "node": node_id})
            for label_edge, rect in labels:
                if label_edge == edge_id:
                    continue
                for a, b in segments:
                    if abs(a["x"] - b["x"]) < 1:
                        hit = rect[0] < a["x"] < rect[2] and max(min(a["y"], b["y"]), rect[1]) < min(max(a["y"], b["y"]), rect[3])
                    else:
                        hit = rect[1] < a["y"] < rect[3] and max(min(a["x"], b["x"]), rect[0]) < min(max(a["x"], b["x"]), rect[2])
                    if hit:
                        counts["route_label_collisions"] += 1
                        issues.append({"page": page, "title": diagram["title"], "kind": "route-label", "edge": edge_id, "label_edge": label_edge})
        crossings = route_crossing_details(graph)
        counts["route_crossings"] = len(crossings)
        for crossing in crossings:
            pair = frozenset(crossing["edges"])
            is_bridged = diagram["title"] == "Data Request Lifecycle" and pair == frozenset(("e08", "e12"))
            if is_bridged:
                counts["bridged_crossings"] += 1
            else:
                issues.append({"page": page, "title": diagram["title"], "kind": "route-crossing", **crossing})
        page_rows.append({"page": page, "type": diagram["diagramType"], "title": diagram["title"], **counts})
    if issues:
        raise ValueError("Diagram layout QA failed: " + json.dumps(issues, ensure_ascii=False))
    return {"diagram_count": len(diagrams), "pages": page_rows, "all_collision_counts": {key: sum(row[key] for row in page_rows) for key in page_rows[0] if key not in {"page", "type", "title"}}, "result": "pass"}


def polyline_midpoint(points: list[dict]) -> tuple[float, float]:
    if len(points) < 2:
        return (0.0, 0.0)
    lengths = [math.hypot(b["x"] - a["x"], b["y"] - a["y"]) for a, b in zip(points, points[1:])]
    total = sum(lengths)
    target = total / 2
    for (a, b), length in zip(zip(points, points[1:]), lengths):
        if target <= length:
            ratio = target / max(1, length)
            return (a["x"] + (b["x"] - a["x"]) * ratio, a["y"] + (b["y"] - a["y"]) * ratio)
        target -= length
    return (points[-1]["x"], points[-1]["y"])


def main() -> None:
    diagrams = [parse_mermaid(SOURCES / f"{name}.mmd") for name in PAGE_NAMES]
    # This edge ordering lets ELK place the interruption and skip branches
    # without crossing two unrelated transitions.
    next(item for item in diagrams if item["title"] == "Activity Execution Lifecycle")["edges"].reverse()
    env = dict(__import__("os").environ)
    env["NODE_PATH"] = str(ELK_NODE_MODULES)
    env["ELK_MODULE_PATH"] = str(ELK_MODULE_PATH)
    with tempfile.TemporaryDirectory(prefix="sketch2life-rev11-layout-") as temporary_directory:
        input_path = Path(temporary_directory) / "layout-input.json"
        output_path = Path(temporary_directory) / "layout-output.json"
        input_path.write_text(json.dumps(diagrams, ensure_ascii=False), encoding="utf-8")
        subprocess.run([NODE, str(ELK_SCRIPT), str(input_path), str(output_path)], check=True, env=env, cwd=HERE)
        layout = json.loads(output_path.read_text(encoding="utf-8"))
    for number, diagram in enumerate(layout, start=1):
        correct_cyclic_start_layout(diagram)
        apply_reviewed_layout_fixes(diagram)
    quality = validate_layout_quality(layout)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    (PREVIEWS / "layout-qa.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for number, diagram in enumerate(layout, start=1):
        PREVIEWS.mkdir(parents=True, exist_ok=True)
        render_preview(diagram, PREVIEWS / f"page-{number:02d}.png")
    build_drawio(layout)
    (HERE / "page-index.json").write_text(json.dumps([
        {"page": index, "type": item["diagramType"], "title": item["title"], "source": item["source"]}
        for index, item in enumerate(layout, start=1)
    ], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built {len(layout)} editable pages and previews in {PREVIEWS}")


if __name__ == "__main__":
    main()
