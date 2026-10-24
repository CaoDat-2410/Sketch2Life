"""Build a multi-page, editable Draw.io file from the Rev9 Mermaid diagrams.

The Mermaid files remain the source of state/transition content. Draw.io CLI
imports were captured separately; this builder applies a report-friendly
layout to the imported concepts and emits native mxGraph shapes/connectors.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FEATURE = Path(__file__).resolve().parents[3]
OUTPUT = FEATURE / "artifacts" / "diagrams" / "rev9" / "drawio" / "Sketch2Life-Review2-State-and-Activity.drawio"

COLORS = {
    "ink": "#263746",
    "line": "#526579",
    "state_fill": "#EAF1FB",
    "state_stroke": "#496F9D",
    "teacher_fill": "#EAF2FF",
    "teacher_stroke": "#4876A8",
    "child_fill": "#E8F4EA",
    "child_stroke": "#3F7F51",
    "runtime_fill": "#F1ECFF",
    "runtime_stroke": "#7556A5",
    "decision_fill": "#FFF3D6",
    "decision_stroke": "#B88722",
    "terminal_fill": "#E8F4EA",
    "terminal_stroke": "#4D865B",
    "note_fill": "#FFF7D8",
    "note_stroke": "#B7A24B",
    "error_fill": "#FCEAEA",
    "error_stroke": "#B65454",
}


@dataclass(frozen=True)
class Node:
    key: str
    label: str
    x: int
    y: int
    w: int
    h: int
    kind: str = "state"


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    label: str = ""
    points: tuple[tuple[int, int], ...] = ()
    dashed: bool = False
    anchors: tuple[float, float, float, float] | None = None


def graph_model(width: int, height: int) -> tuple[ET.Element, ET.Element]:
    model = ET.Element(
        "mxGraphModel",
        {
            "dx": str(width),
            "dy": str(height),
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(width),
            "pageHeight": str(height),
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    return model, root


def cell_style(kind: str) -> str:
    common = "whiteSpace=wrap;html=1;fontFamily=Arial;fontColor={};fontSize=16;spacing=5;".format(COLORS["ink"])
    if kind == "state":
        return common + f"rounded=1;arcSize=12;fillColor={COLORS['state_fill']};strokeColor={COLORS['state_stroke']};strokeWidth=1.5;align=center;verticalAlign=middle;"
    if kind == "teacher":
        return common + f"rounded=1;arcSize=12;fillColor={COLORS['teacher_fill']};strokeColor={COLORS['teacher_stroke']};strokeWidth=1.5;align=center;verticalAlign=middle;"
    if kind == "child":
        return common + f"rounded=1;arcSize=12;fillColor={COLORS['child_fill']};strokeColor={COLORS['child_stroke']};strokeWidth=1.5;align=center;verticalAlign=middle;"
    if kind == "runtime":
        return common + f"rounded=1;arcSize=12;fillColor={COLORS['runtime_fill']};strokeColor={COLORS['runtime_stroke']};strokeWidth=1.5;align=center;verticalAlign=middle;"
    if kind == "decision":
        return common + f"rhombus;fillColor={COLORS['decision_fill']};strokeColor={COLORS['decision_stroke']};strokeWidth=1.5;align=center;verticalAlign=middle;fontSize=15;"
    if kind == "terminal":
        return common + f"rounded=1;arcSize=12;fillColor={COLORS['terminal_fill']};strokeColor={COLORS['terminal_stroke']};strokeWidth=1.5;align=center;verticalAlign=middle;"
    if kind == "error":
        return common + f"rounded=1;arcSize=12;fillColor={COLORS['error_fill']};strokeColor={COLORS['error_stroke']};strokeWidth=1.5;align=center;verticalAlign=middle;fontSize=14;"
    if kind == "note":
        return f"shape=note;whiteSpace=wrap;html=1;fillColor={COLORS['note_fill']};strokeColor={COLORS['note_stroke']};strokeWidth=1.2;fontFamily=Arial;fontColor={COLORS['ink']};fontSize=13;align=left;verticalAlign=middle;spacing=8;"
    if kind == "title":
        return f"text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;strokeColor=none;fillColor=none;fontFamily=Arial;fontColor={COLORS['ink']};fontSize=21;fontStyle=1;"
    if kind == "initial":
        return "ellipse;aspect=fixed;html=1;fillColor=#263746;strokeColor=#263746;strokeWidth=1.2;"
    return common + f"rounded=1;fillColor={COLORS['state_fill']};strokeColor={COLORS['state_stroke']};align=center;verticalAlign=middle;"


def add_node(root: ET.Element, node: Node) -> None:
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": node.key,
            "value": node.label,
            "style": cell_style(node.kind),
            "vertex": "1",
            "parent": "1",
        },
    )
    ET.SubElement(
        cell,
        "mxGeometry",
        {"x": str(node.x), "y": str(node.y), "width": str(node.w), "height": str(node.h), "as": "geometry"},
    )


def add_edge(root: ET.Element, key: str, edge: Edge) -> None:
    style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
        f"strokeColor={COLORS['line']};strokeWidth=1.4;endArrow=block;endFill=1;"
        f"fontFamily=Arial;fontColor={COLORS['ink']};fontSize=13;labelBackgroundColor=#FFFFFF;"
    )
    if edge.dashed:
        style += "dashed=1;dashPattern=4 4;"
    if edge.anchors:
        exit_x, exit_y, entry_x, entry_y = edge.anchors
        style += f"exitX={exit_x};exitY={exit_y};entryX={entry_x};entryY={entry_y};exitPerimeter=1;entryPerimeter=1;"
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": key,
            "value": edge.label,
            "style": style,
            "edge": "1",
            "parent": "1",
            "source": edge.source,
            "target": edge.target,
        },
    )
    geom = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    if edge.points:
        arr = ET.SubElement(geom, "Array", {"as": "points"})
        for x, y in edge.points:
            ET.SubElement(arr, "mxPoint", {"x": str(x), "y": str(y)})


def add_page(mxfile: ET.Element, name: str, width: int, height: int, nodes: Iterable[Node], edges: Iterable[Edge], notes: Iterable[Node] = ()) -> None:
    page_id = name.lower().replace(" ", "-").replace("&", "and")
    diagram = ET.SubElement(mxfile, "diagram", {"id": page_id, "name": name})
    model, root = graph_model(width, height)
    ET.SubElement(
        root,
        "mxCell",
        {"id": "title", "value": name, "style": cell_style("title"), "vertex": "1", "parent": "1"},
    )
    title_geo = root[-1]
    ET.SubElement(title_geo, "mxGeometry", {"x": "32", "y": "14", "width": str(width - 64), "height": "34", "as": "geometry"})
    for node in nodes:
        add_node(root, node)
    for node in notes:
        add_node(root, node)
    for index, edge in enumerate(edges, start=1):
        add_edge(root, f"edge-{index}", edge)
    diagram.append(model)


def build() -> None:
    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "modified": "2026-10-24T00:00:00.000Z", "agent": "Sketch2Life Review 2 Rev9"})

    # State machine 1a: main session progression; exception transitions are
    # split across companion pages to keep the state graph readable.
    session_nodes = [
        Node("s_start", "", 40, 170, 16, 16, "initial"),
        Node("s_draft", "Draft", 90, 152, 120, 52),
        Node("s_scheduled", "Scheduled", 290, 152, 135, 52),
        Node("s_lobby", "Lobby", 510, 152, 120, 52),
        Node("s_active", "Active", 720, 152, 120, 52),
        Node("s_completing", "Completing", 930, 152, 145, 52),
        Node("s_completed", "Completed", 1160, 152, 135, 52, "terminal"),
        Node("s_cancelled", "Cancelled", 300, 340, 135, 52, "terminal"),
    ]
    session_edges = [
        Edge("s_start", "s_draft", anchors=(0.5, 0.5, 0, 0.5)),
        Edge("s_draft", "s_scheduled"),
        Edge("s_draft", "s_lobby", "open lobby", ((150, 115), (570, 115)), anchors=(0.5, 0, 0.5, 0)),
        Edge("s_scheduled", "s_lobby"),
        Edge("s_draft", "s_cancelled", "cancel", ((150, 255), (270, 255)), anchors=(0.5, 1, 0, 0.5)),
        Edge("s_scheduled", "s_cancelled", "cancel", ((357, 255), (357, 315)), anchors=(0.5, 1, 0.5, 0)),
        Edge("s_lobby", "s_cancelled", "cancel", ((570, 255), (470, 255), (470, 365)), anchors=(0.5, 1, 1, 0.5)),
        Edge("s_lobby", "s_active"),
        Edge("s_active", "s_completing"),
        Edge("s_completing", "s_completed"),
    ]
    session_notes = [
        Node(
            "s_note",
            "Schedule is optional. Draft, Scheduled and Lobby may be cancelled before Start. Session pause/recovery and early termination are shown on companion pages. Completion requires durable results. Completed and Cancelled are terminal.",
            40,
            455,
            1250,
            62,
            "note",
        )
    ]
    add_page(mxfile, "Session Lifecycle", 1360, 550, session_nodes, session_edges, session_notes)

    # State machine 1b: pause/resume and failure recovery transitions.
    recovery_nodes = [
        Node("r_active", "Active", 180, 145, 150, 58),
        Node("r_paused", "Paused", 800, 145, 150, 58),
        Node("r_recovering", "Recovering", 490, 395, 170, 58),
    ]
    recovery_edges = [
        Edge("r_active", "r_paused", "pause"),
        Edge("r_paused", "r_active", "resume", ((875, 105), (255, 105)), anchors=(0.5, 0, 0.5, 0)),
        Edge("r_active", "r_recovering", "failure", ((255, 295), (535, 295)), anchors=(0.5, 1, 0.25, 0)),
        Edge("r_paused", "r_recovering", "failure", ((875, 335), (620, 335)), anchors=(0.5, 1, 0.75, 0)),
        Edge("r_recovering", "r_active", "recover", ((490, 424), (85, 424), (85, 270), (255, 270)), anchors=(0, 0.5, 0.5, 1)),
        Edge("r_recovering", "r_paused", "recover", ((660, 424), (1060, 424), (1060, 270), (875, 270)), anchors=(1, 0.5, 0.5, 1)),
    ]
    recovery_notes = [
        Node("r_note", "Recovery returns to the last valid lifecycle state; the concrete recovery receipt and durable boundary remain subject to contract adoption and database-backed acceptance.", 50, 545, 1120, 62, "note")
    ]
    add_page(mxfile, "Session Pause and Recovery", 1240, 650, recovery_nodes, recovery_edges, recovery_notes)

    # State machine 1c: early termination from the allowed session states.
    early_nodes = [
        Node("e_lobby", "Lobby", 100, 100, 145, 54),
        Node("e_active", "Active", 100, 220, 145, 54),
        Node("e_paused", "Paused", 100, 340, 145, 54),
        Node("e_recovering", "Recovering", 100, 460, 145, 54),
        Node("e_ended", "Ended early", 830, 280, 190, 66, "terminal"),
    ]
    early_edges = [
        Edge("e_lobby", "e_ended", "end early", ((430, 127), (430, 200), (925, 200)), anchors=(1, 0.5, 0.5, 0)),
        Edge("e_active", "e_ended", "end early", ((450, 247), (450, 260), (925, 260)), anchors=(1, 0.5, 0.5, 0)),
        Edge("e_paused", "e_ended", "end early", ((450, 367), (450, 390), (925, 390)), anchors=(1, 0.5, 0.5, 1)),
        Edge("e_recovering", "e_ended", "end early", ((430, 487), (430, 500), (925, 500)), anchors=(1, 0.5, 0.5, 1)),
    ]
    early_notes = [
        Node("e_note", "An early end requires a reason category. It is distinct from successful completion, which records the required durable results.", 100, 570, 980, 60, "note")
    ]
    add_page(mxfile, "Session Early Termination", 1160, 660, early_nodes, early_edges, early_notes)

    # State machine 2: participant admission states and Start boundary.
    admission_nodes = [
        Node("a_start", "", 38, 250, 16, 16, "initial"),
        Node("a_pending", "Pending", 110, 232, 130, 52),
        Node("a_admitted", "Admitted", 400, 232, 135, 52),
        Node("a_denied", "Denied", 400, 365, 125, 52, "terminal"),
        Node("a_revoked", "Revoked", 400, 92, 125, 52, "terminal"),
        Node("a_removed", "Removed", 720, 125, 125, 52, "terminal"),
        Node("a_left", "Left", 720, 235, 125, 52, "terminal"),
        Node("a_expired", "Expired", 720, 345, 125, 52, "terminal"),
    ]
    admission_edges = [
        Edge("a_start", "a_pending"),
        Edge("a_pending", "a_admitted"),
        Edge("a_pending", "a_denied", "", ((175, 300), (330, 300), (330, 390))),
        Edge("a_pending", "a_revoked", "", ((175, 215), (330, 215), (330, 118))),
        Edge("a_admitted", "a_removed", "", ((535, 250), (620, 250), (620, 151))),
        Edge("a_admitted", "a_left"),
        Edge("a_admitted", "a_expired", "", ((535, 266), (620, 266), (620, 371))),
    ]
    admission_notes = [
        Node(
            "a_note",
            "Pending is not admitted and has no roster/art access. Successful Start revokes every still-pending request. Already-admitted grants remain; new join requests are rejected after Start.",
            45,
            475,
            910,
            72,
            "note",
        )
    ]
    add_page(mxfile, "Participant Admission", 1000, 575, admission_nodes, admission_edges, admission_notes)

    # State machine 3a: device connection lifecycle.
    connection_nodes = [
        Node("c_start", "", 36, 205, 16, 16, "initial"),
        Node("c_connecting", "Connecting", 90, 187, 135, 52),
        Node("c_auth", "Authenticated", 285, 187, 145, 52),
        Node("c_resync", "Resyncing", 495, 187, 135, 52),
        Node("c_connected", "Connected", 695, 187, 130, 52),
        Node("c_disconnected", "Disconnected", 850, 330, 145, 52),
    ]
    connection_edges = [
        Edge("c_start", "c_connecting", anchors=(0.5, 0.5, 0, 0.5)),
        Edge("c_connecting", "c_auth"),
        Edge("c_auth", "c_resync"),
        Edge("c_resync", "c_connected"),
        Edge("c_connected", "c_disconnected", anchors=(1, 0.5, 0.5, 0)),
        Edge("c_disconnected", "c_connecting", "reconnect", ((920, 410), (155, 410), (155, 250)), anchors=(0.5, 1, 0.5, 1)),
    ]
    connection_notes = [
        Node(
            "c_note",
            "Connected follows authoritative resync and acknowledgement. Grant revocation from Authenticated, Resyncing, Connected or Disconnected ends in Revoked; see the companion revocation page.",
            80,
            500,
            900,
            58,
            "note",
        )
    ]
    add_page(mxfile, "Device Connection", 1080, 590, connection_nodes, connection_edges, connection_notes)

    # State machine 3b: explicit grant revocation from authenticated device states.
    revoke_nodes = [
        Node("v_auth", "Authenticated", 90, 105, 180, 54),
        Node("v_resync", "Resyncing", 90, 220, 180, 54),
        Node("v_connected", "Connected", 90, 335, 180, 54),
        Node("v_disconnected", "Disconnected", 90, 450, 180, 54),
        Node("v_revoked", "Revoked", 800, 265, 170, 62, "terminal"),
    ]
    revoke_edges = [
        Edge("v_auth", "v_revoked", "revoke", ((400, 132), (400, 200), (885, 200)), anchors=(1, 0.5, 0.5, 0)),
        Edge("v_resync", "v_revoked", "revoke", ((450, 247), (450, 250), (885, 250)), anchors=(1, 0.5, 0.5, 0)),
        Edge("v_connected", "v_revoked", "revoke", ((450, 362), (450, 370), (885, 370)), anchors=(1, 0.5, 0.5, 1)),
        Edge("v_disconnected", "v_revoked", "revoke", ((400, 477), (400, 500), (885, 500)), anchors=(1, 0.5, 0.5, 1)),
    ]
    revoke_notes = [
        Node("v_note", "Revoked devices cannot refresh or replay a grant. This is a design transition; device-level acceptance is not yet evidenced.", 90, 555, 900, 58, "note")
    ]
    add_page(mxfile, "Device Grant Revocation", 1120, 635, revoke_nodes, revoke_edges, revoke_notes)

    # Activity diagram: Teacher lobby, Child admission, and session start.
    activity_nodes = [
        Node("w_start", "", 40, 88, 18, 18, "initial"),
        Node("w_select", "Teacher selects<br>assigned class", 82, 68, 140, 58, "teacher"),
        Node("w_open", "Teacher opens<br>session lobby", 260, 68, 150, 58, "teacher"),
        Node("w_code", "Runtime issues<br>QR and six-digit code", 450, 68, 175, 58, "runtime"),
        Node("w_request", "Child submits<br>join request", 665, 68, 155, 58, "child"),
        Node("w_valid", "Lobby open and<br>request valid?", 845, 52, 130, 90, "decision"),
        Node("w_reject", "Generic rejection;<br>persistent source-IP limit", 970, 175, 185, 68, "error"),
        Node("w_pending", "Create pending<br>request", 835, 280, 165, 60, "runtime"),
        Node("w_review", "Teacher reviews roster,<br>profile and consent", 620, 280, 185, 60, "teacher"),
        Node("w_admit", "Teacher<br>admits?", 445, 265, 125, 90, "decision"),
        Node("w_grant", "Create scoped<br>admitted grant", 250, 280, 160, 60, "runtime"),
        Node("w_denied", "Mark request<br>denied", 250, 380, 160, 58, "error"),
        Node("w_start_now", "Teacher starts<br>session now?", 65, 265, 135, 90, "decision"),
        Node("w_keep_lobby", "Keep lobby<br>open", 52, 382, 165, 58, "teacher"),
        Node("w_atomic", "Close new admission;<br>revoke pending requests", 65, 510, 235, 66, "runtime"),
        Node("w_preserve", "Keep already-<br>admitted grants", 340, 510, 195, 66, "runtime"),
        Node("w_active", "Session<br>active", 575, 510, 145, 66, "terminal"),
        Node("w_late", "Reject new joins<br>after Start", 775, 510, 205, 66, "error"),
    ]
    activity_edges = [
        Edge("w_start", "w_select"),
        Edge("w_select", "w_open"),
        Edge("w_open", "w_code"),
        Edge("w_code", "w_request"),
        Edge("w_request", "w_valid"),
        Edge("w_valid", "w_pending", "Yes", ((910, 160), (910, 280))),
        Edge("w_valid", "w_reject", "No"),
        Edge("w_pending", "w_review"),
        Edge("w_review", "w_admit"),
        Edge("w_admit", "w_grant", "Yes"),
        Edge("w_admit", "w_denied", "No", ((505, 365), (505, 409), (410, 409))),
        Edge("w_grant", "w_start_now"),
        Edge("w_denied", "w_start_now", "", ((250, 410), (210, 410), (210, 310))),
        Edge("w_start_now", "w_keep_lobby", "No"),
        Edge("w_start_now", "w_atomic", "Yes"),
        Edge("w_pending", "w_atomic", "still pending at Start", ((915, 360), (915, 470), (185, 470)), True),
        Edge("w_atomic", "w_preserve"),
        Edge("w_preserve", "w_active"),
        Edge("w_active", "w_late"),
    ]
    activity_notes = [
        Node(
            "w_note",
            "Design workflow from SRS v3.3/B28; local checks do not establish a PostgreSQL-backed end-to-end run.",
            585,
            605,
            395,
            52,
            "note",
        )
    ]
    add_page(mxfile, "Teacher Lobby and Session Start", 1160, 680, activity_nodes, activity_edges, activity_notes)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(mxfile, space="  ")
    ET.ElementTree(mxfile).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(OUTPUT)


if __name__ == "__main__":
    build()
