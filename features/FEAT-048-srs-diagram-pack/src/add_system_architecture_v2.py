"""Append a Draw.io-native, SRS-grounded architecture comparison page."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import quote, unquote
from xml.etree.ElementTree import Element, ElementTree, SubElement, fromstring, parse, tostring
import os

from build_drawio import edge, page, send_edges_behind_vertices, vertex


FEATURE = Path(__file__).resolve().parents[1]
OUT = FEATURE / "artifacts" / "Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio"
PAGE_NAME = "System Architecture v2"
PAGE_ID = "khoa-system-architecture-v2-v31"
ICON_DIR = FEATURE / "assets" / "icons" / "lucide-v1.61.0"
ICON_STROKE = "#42566B"

TITLE = (
    "text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
    "strokeColor=none;fillColor=none;fontSize=24;fontStyle=1;fontColor=#243247;"
)
SUBTITLE = (
    "text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
    "strokeColor=none;fillColor=none;fontSize=13;fontColor=#52647A;"
)
LEGEND = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#F7F9FC;strokeColor=#C8D2DE;"
    "fontColor=#34475C;fontSize=11;align=left;verticalAlign=middle;spacing=8;"
)
FRAME = (
    "swimlane;html=1;startSize=38;rounded=0;fillColor=#FFFFFF;"
    "swimlaneFillColor=#E8EEF5;strokeColor=#73849A;fontColor=#24364A;"
    "fontStyle=1;fontSize=15;horizontal=1;"
)
CLIENT_FRAME = FRAME.replace("swimlaneFillColor=#E8EEF5", "swimlaneFillColor=#EAF0F6")
BACKEND_FRAME = FRAME.replace("swimlaneFillColor=#E8EEF5", "swimlaneFillColor=#E5EDF5")
EXTERNAL_FRAME = FRAME.replace("swimlaneFillColor=#E8EEF5", "swimlaneFillColor=#EEF1F4")
SUBFRAME = (
    "swimlane;html=1;startSize=34;rounded=0;fillColor=#FFFFFF;"
    "swimlaneFillColor=#F1F4F7;strokeColor=#A2AFBC;fontColor=#2E4055;"
    "fontStyle=1;fontSize=13;horizontal=1;"
)
COMPONENT = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#718096;"
    "fontColor=#24364A;fontSize=12;align=center;verticalAlign=middle;spacing=7;"
)
CONFIRMED = COMPONENT.replace("fillColor=#FFFFFF", "fillColor=#EDF6F0").replace(
    "strokeColor=#718096", "strokeColor=#55836A"
)
CANDIDATE = COMPONENT.replace("fillColor=#FFFFFF", "fillColor=#FFF8EA").replace(
    "strokeColor=#718096", "strokeColor=#B18B4B"
) + "dashed=1;"
PROPOSED = COMPONENT.replace("fillColor=#FFFFFF", "fillColor=#F1F6FB").replace(
    "strokeColor=#718096", "strokeColor=#718CA8"
) + "dashed=1;"
TBD = COMPONENT.replace("fillColor=#FFFFFF", "fillColor=#F2F4F7").replace(
    "strokeColor=#718096", "strokeColor=#8995A3"
)
POLICY = COMPONENT.replace("fillColor=#FFFFFF", "fillColor=#F0F3F6").replace(
    "strokeColor=#718096", "strokeColor=#586A7D"
)
ACTOR = (
    "rounded=0;html=1;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=#61758B;"
    "fontColor=#26384B;fontSize=12;align=center;verticalAlign=bottom;spacing=6;spacingBottom=8;"
)
DATABASE = (
    "shape=cylinder3;size=15;whiteSpace=wrap;html=1;fillColor=#FFF8EA;"
    "strokeColor=#B18B4B;fontColor=#5B4828;fontSize=11;align=center;"
    "verticalAlign=middle;spacing=5;dashed=1;"
)
OBJECT_STORE = DATABASE.replace("fillColor=#FFF8EA", "fillColor=#F2F6FA").replace(
    "strokeColor=#B18B4B", "strokeColor=#7E94AA"
).replace("fontColor=#5B4828", "fontColor=#354A60")
QUEUE = (
    "shape=hexagon;perimeter=hexagonPerimeter;whiteSpace=wrap;html=1;"
    "fillColor=#FFF8EA;strokeColor=#B18B4B;fontColor=#5B4828;fontSize=11;"
    "align=center;verticalAlign=middle;spacing=5;dashed=1;"
)
NOTE = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#F7F9FC;strokeColor=#CCD5DF;"
    "fontColor=#46586D;fontSize=11;align=left;verticalAlign=middle;spacing=8;"
)
ASYNC_NOTE = NOTE.replace("fillColor=#F7F9FC", "fillColor=#FFF9EC").replace(
    "strokeColor=#CCD5DF", "strokeColor=#D8BE84"
)
ANCHOR = "ellipse;fillColor=none;strokeColor=none;opacity=0;"

RUNTIME = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
    "endArrow=block;endFill=1;strokeColor=#53677E;strokeWidth=1.5;"
    "fontSize=10;fontColor=#3D5066;labelBackgroundColor=#FFFFFF;"
)
DEPENDENCY = RUNTIME + "dashed=1;strokeColor=#B47A25;"
PROPOSED_FLOW = RUNTIME + "dashed=1;strokeColor=#547F9E;"


def add_box(root: Element, ids: dict[str, str], key: str, label: str,
            x: int, y: int, w: int, h: int, style: str) -> str:
    return vertex(root, ids, key, label, x, y, w, h, style)


def with_icon_label(style: str, left_padding: int = 42) -> str:
    tokens = [token for token in style.split(";") if token and not token.startswith(("align=", "spacingLeft="))]
    tokens.extend(("align=left", f"spacingLeft={left_padding}"))
    return ";".join(tokens) + ";"


def add_icon(root: Element, name: str, key: str, x: int, y: int, size: int = 24) -> None:
    source = ICON_DIR / f"{name}.svg"
    svg = source.read_text(encoding="utf-8").replace('stroke="currentColor"', f'stroke="{ICON_STROKE}"')
    # Draw.io styles are semicolon-delimited, so a `;base64` data URI is parsed
    # as two style tokens. Percent-encode the SVG payload and use a non-base64 URI.
    encoded = quote(svg, safe="")
    cell = SubElement(root, "mxCell", {
        "id": f"lucide-{key}", "value": "",
        "style": f"shape=image;image=data:image/svg+xml,{encoded};aspect=fixed;",
        "vertex": "1", "parent": "1",
    })
    SubElement(cell, "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(size), "height": str(size), "as": "geometry",
    })


def add_architecture_page() -> Element:
    width, height = 2240, 1360
    diagram, root, ids = page(PAGE_NAME, PAGE_ID, width, height)
    icon_specs: list[tuple[str, str, int, int, int]] = []

    add_box(root, ids, "title", "System Architecture v2 — Sketch2Life SRS v3.1", 40, 18, 1700, 38, TITLE)
    add_box(
        root, ids, "subtitle",
        "Draw.io-native comparison page · logical architecture with named SRS candidates · no AWS deployment is implied",
        42, 58, 1880, 25, SUBTITLE,
    )
    add_box(
        root, ids, "legend",
        "<b>SHAPES</b>  role card = person · rectangle = component/interface · swimlane = boundary · cylinder = durable store · hexagon = queue &nbsp;&nbsp; "
        "<b>STATUS</b>  green + CONFIRMED · amber dashed + CANDIDATE · blue dashed + PROPOSED · gray + TBD / policy note &nbsp;&nbsp; "
        "<b>ICON</b>  Lucide outline = role only, not status &nbsp;&nbsp; "
        "<b>ARROWS</b>  solid = runtime data flow · dashed amber, adapters → ports = implementation dependency · dashed blue = proposed transport",
        40, 91, 2160, 58, LEGEND,
    )

    # Logical boundaries are deliberately generic; the SRS has not selected a cloud deployment.
    add_box(root, ids, "clients_frame", "People and client surfaces", 40, 190, 420, 1060, CLIENT_FRAME)
    add_box(root, ids, "backend_frame", "Sketch2Life backend — logical boundary · deployment topology TBD", 500, 190, 1170, 1060, BACKEND_FRAME)
    add_box(root, ids, "external_frame", "External persistence and provider boundaries", 1710, 190, 490, 1060, EXTERNAL_FRAME)

    # People and client applications.
    client_rows = [
        ("child", "Child", "child_app", "Child Android app<br/>React Native / TypeScript<br/><b>CONFIRMED</b>", 300, CONFIRMED, "smartphone"),
        ("teacher", "Teacher", "teacher_ui", "Teacher Desktop surface — CONFIRMED<br/>UI framework — TBD", 535, COMPONENT, "monitor"),
        ("admin", "Super Admin", "admin_ui", "Super Admin surface — CONFIRMED<br/>UI framework — TBD", 770, COMPONENT, "monitor"),
    ]
    for actor_key, actor_label, app_key, app_label, y, app_style, app_icon in client_rows:
        actor_y = y + 43
        add_box(root, ids, f"{actor_key}_actor", actor_label, 82, actor_y, 88, 86, ACTOR)
        add_box(root, ids, app_key, app_label, 205, y + 34, 220, 104, with_icon_label(app_style, 43))
        icon_specs.extend((("user-round", f"actor-{actor_key}", 113, actor_y + 9, 26),
                           (app_icon, f"client-{actor_key}", 216, y + 73, 26)))
        edge(root, ids, f"{actor_key}_uses", f"{actor_key}_actor", app_key, "uses", RUNTIME)
    add_box(
        root, ids, "client_note",
        "<b>Shared backend authorization</b><br/>Teacher and Super Admin surfaces use the same backend authorization boundary.<br/><br/>Canvas / presence WebSocket remains PROPOSED.",
        68, 1000, 366, 148, NOTE,
    )

    # Request handling and the nine B8 logical groupings.
    add_box(root, ids, "api", "FastAPI / Python<br/><b>CONFIRMED</b><br/>REST commands and queries", 565, 385, 250, 135, with_icon_label(CONFIRMED, 42))
    add_box(root, ids, "application", "Application services<br/>use cases · authorization<br/><i>logical split from B8</i>", 870, 385, 270, 135, with_icon_label(COMPONENT, 42))
    add_box(root, ids, "domain_frame", "Domain — B8 context groupings · PROPOSED", 1200, 250, 430, 350, with_icon_label(SUBFRAME, 38))
    icon_specs.extend((("server", "fastapi", 576, 440, 26),
                       ("list-checks", "application", 882, 440, 26),
                       ("layers", "domain-boundary", 1207, 256, 22)))
    contexts = [
        ("context_identity", "Identity / Consent"), ("context_classroom", "Classroom"), ("context_session", "Session / Groups"),
        ("context_drawing", "Drawing / Collaboration"), ("context_ai", "AI Assistance"), ("context_knowledge", "Knowledge / Media"),
        ("context_activities", "Activities"), ("context_portfolio", "Portfolio / Assessment"), ("context_governance", "Governance / Audit"),
    ]
    context_style = PROPOSED.replace("fontSize=12", "fontSize=11").replace("spacing=7", "spacing=4")
    for i, (key, label) in enumerate(contexts):
        col, row = i % 3, i // 3
        add_box(root, ids, key, label, 1215 + col * 134, 305 + row * 66, 126, 52, context_style)
    add_box(
        root, ids, "canvas_policy",
        "Domain contexts are framework-independent and proposed.<br/>Canvas sync: server-authoritative ordered operations + checkpoints are a pilot proposal; CRDT is not selected.",
        1215, 515, 400, 48, NOTE,
    )

    # Application-owned ports and the matching adapter layer.
    add_box(root, ids, "ports_frame", "Application-owned outbound ports", 850, 645, 290, 370, with_icon_label(SUBFRAME, 38))
    add_box(root, ids, "adapters_frame", "Backend adapter implementations", 1210, 645, 430, 370, SUBFRAME)
    icon_specs.append(("plug", "ports-boundary", 858, 651, 22))
    port_labels = [
        ("port_repository", "Repository port"), ("port_artifact", "Artifact port"), ("port_job", "Job port"),
        ("port_identity", "Identity port"), ("port_model", "Model port"), ("port_realtime", "Realtime / presence port"),
    ]
    adapters = [
        ("adapter_repository", "Persistence adapter · candidate", CANDIDATE),
        ("adapter_artifact", "Artifact adapter · candidate", CANDIDATE),
        ("adapter_job", "Job / queue adapter · candidate", CANDIDATE),
        ("adapter_identity", "Adult identity adapter · implementation TBD", TBD),
        ("adapter_model", "AI provider adapter · backend only", PROPOSED),
        ("adapter_realtime", "Realtime / presence adapter · proposed", PROPOSED),
    ]
    row_y = [715, 765, 815, 865, 915, 965]
    for (port_key, port_label), (adapter_key, adapter_label, adapter_style), y in zip(port_labels, adapters, row_y):
        add_box(root, ids, port_key, port_label, 868, y, 245, 38, COMPONENT)
        if adapter_key == "adapter_artifact":
            adapter_style = with_icon_label(adapter_style, 40)
            icon_specs.append(("package", "artifact-adapter", 1236, y + 8, 22))
        add_box(root, ids, adapter_key, adapter_label, 1228, y, 392, 38, adapter_style)
        edge(root, ids, f"runtime_{port_key}", port_key, adapter_key, "", RUNTIME)

    # A single reverse arrow shows the dependency direction; row arrows above show runtime calls.
    add_box(root, ids, "dependency_adapter_anchor", "", 1207, 699, 2, 2, ANCHOR)
    add_box(root, ids, "dependency_port_anchor", "", 1140, 699, 2, 2, ANCHOR)
    edge(root, ids, "adapter_implements_ports", "dependency_adapter_anchor", "dependency_port_anchor", "", DEPENDENCY)
    add_box(root, ids, "adapter_rule_note", "Adapters implement application-owned port contracts (dependency points left).", 1228, 680, 392, 24, SUBTITLE)

    # External capability choices remain explicitly qualified.
    add_box(
        root, ids, "external_note",
        "<b>Provider / deployment boundary</b><br/>Calls originate from backend adapters only.<br/>No provider credentials or storage endpoints live in mobile clients.<br/><br/>Record a vendor choice and transmitted data in Report 4 only after an ADR decision.",
        1740, 275, 430, 170, NOTE,
    )
    add_box(root, ids, "external_services_frame", "SRS-named capabilities and policy boundary", 1730, 645, 450, 370, SUBFRAME)
    services = [
        ("service_postgres", "PostgreSQL · CANDIDATE", DATABASE, "database"),
        ("service_object_store", "S3-compatible object storage · CANDIDATE", OBJECT_STORE, "hard-drive"),
        ("service_queue", "Redis / RQ queue · CANDIDATE", QUEUE, "list-ordered"),
        ("service_firebase", "Firebase Authentication · adult identity only", POLICY, "shield-check"),
        ("service_ai", "AI provider API · TBD", TBD, "sparkles"),
        ("service_websocket", "WebSocket transport · PROPOSED", PROPOSED, "radio-tower"),
    ]
    for (service_key, service_label, service_style, service_icon), y, (adapter_key, _, _) in zip(services, row_y, adapters):
        add_box(root, ids, service_key, service_label, 1748, y, 414, 38, with_icon_label(service_style, 40))
        icon_specs.append((service_icon, service_key, 1756, y + 8, 22))
        edge(root, ids, f"connect_{service_key}", adapter_key, service_key,
             {"service_postgres": "records", "service_object_store": "store artifacts",
              "service_queue": "enqueue job", "service_firebase": "adult auth",
              "service_ai": "AI request", "service_websocket": "events"}[service_key], RUNTIME)
    add_box(
        root, ids, "firebase_constraint_note",
        "Repository policy: Firebase Authentication only. Firestore, Firebase Storage, and Realtime Database are prohibited.",
        1740, 1060, 430, 90, NOTE,
    )

    # The worker is a separate process. These small flow-detail nodes refer to the mapped
    # queue/adapter/provider rows above and below; the note makes that relationship explicit.
    add_box(
        root, ids, "async_flow",
        "<b>ASYNC JOB FLOW · PROPOSED</b> — flow detail for the same queue, adapter, and provider components mapped above",
        530, 1070, 1110, 125, with_icon_label(ASYNC_NOTE, 40),
    )
    add_box(root, ids, "async_queue", "Redis / RQ queue<br/><b>CANDIDATE</b>", 550, 1110, 220, 52, with_icon_label(CANDIDATE, 38))
    add_box(root, ids, "async_worker", "Async worker process<br/><b>separate process · PROPOSED</b>", 820, 1104, 220, 64, with_icon_label(PROPOSED, 40))
    add_box(root, ids, "async_ai_adapter", "AI adapter<br/><b>backend only</b>", 1090, 1110, 190, 52, PROPOSED)
    add_box(root, ids, "async_ai_provider", "AI provider API<br/><b>TBD</b>", 1330, 1110, 275, 52, TBD)
    edge(root, ids, "async_claim", "async_queue", "async_worker", "claim", RUNTIME)
    edge(root, ids, "async_call", "async_worker", "async_ai_adapter", "task", RUNTIME)
    edge(root, ids, "async_provider_call", "async_ai_adapter", "async_ai_provider", "call", RUNTIME)
    add_box(
        root, ids, "async_result_note",
        "Typed result / status returns for Application scope and version checks · never call AI on each pointer event.",
        550, 1171, 1050, 20, SUBTITLE,
    )
    add_box(root, ids, "footer", "Source: canonical SRS v3.1 B8 + repository rules · Lucide icons v1.61.0 (ISC; database/monitor/server/smartphone also MIT) · no deployment topology is adopted.", 40, 1292, 2160, 24, SUBTITLE)

    # Main request/port flow, then service calls. Edges are placed behind all shapes below.
    add_box(root, ids, "client_rest_anchor", "", 454, 450, 2, 2, ANCHOR)
    add_box(root, ids, "client_ws_anchor", "", 454, 484, 2, 2, ANCHOR)
    edge(root, ids, "client_rest", "client_rest_anchor", "api", "REST commands / queries", RUNTIME,
         ((480, 450), (535, 450)))
    edge(root, ids, "client_ws", "client_ws_anchor", "api", "WS proposed", PROPOSED_FLOW,
         ((482, 484), (540, 484)))
    edge(root, ids, "api_to_application", "api", "application", "request", RUNTIME)
    edge(root, ids, "application_to_domain", "application", "domain_frame", "rules", RUNTIME)
    edge(root, ids, "application_uses_ports", "application", "ports_frame", "uses ports", RUNTIME)

    icon_specs.extend((("workflow", "async-flow", 540, 1077, 22),
                       ("list-ordered", "async-queue", 558, 1125, 22),
                       ("cpu", "async-worker", 829, 1124, 24)))
    for icon_name, key, x, y, size in icon_specs:
        add_icon(root, icon_name, key, x, y, size)

    send_edges_behind_vertices(root)
    return diagram


def page_fingerprint(diagram: Element) -> str:
    canonical = __import__("xml.etree.ElementTree", fromlist=["canonicalize"]).canonicalize(
        xml_data=tostring(diagram, encoding="unicode")
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def validate_page(diagram: Element) -> None:
    cells = [cell for cell in diagram.iter("mxCell") if cell.get("id") not in {"0", "1"}]
    cell_ids = [cell.get("id") for cell in cells]
    if len(cell_ids) != len(set(cell_ids)):
        raise ValueError("Duplicate cell ID in System Architecture v2")
    all_ids = set(cell_ids) | {"0", "1"}
    missing = [
        (cell.get("id"), endpoint)
        for cell in cells if cell.get("edge") == "1"
        for endpoint in (cell.get("source"), cell.get("target"))
        if endpoint not in all_ids
    ]
    if missing:
        raise ValueError(f"Unresolved connector endpoints in v2 page: {missing}")
    icon_cells = [cell for cell in cells if cell.get("id", "").startswith("lucide-")]
    for cell in icon_cells:
        style = cell.get("style", "")
        image_value = next((token[len("image="):] for token in style.split(";") if token.startswith("image=")), "")
        if not image_value.startswith("data:image/svg+xml,"):
            raise ValueError(f"Icon cell {cell.get('id')} has an invalid or external image URI")
        try:
            svg = unquote(image_value.partition(",")[2])
            if fromstring(svg).tag.rsplit("}", 1)[-1] != "svg":
                raise ValueError("decoded root element is not <svg>")
        except Exception as error:
            raise ValueError(f"Icon cell {cell.get('id')} contains invalid SVG data: {error}") from error
    if not icon_cells:
        raise ValueError("No embedded Lucide icon cells found on System Architecture v2")
    if len(cells) < 50:
        raise ValueError(f"Unexpectedly sparse v2 page: {len(cells)} cells")


def main() -> None:
    if not OUT.exists():
        raise FileNotFoundError(f"Expected existing Draw.io artifact: {OUT}")
    mxfile = parse(OUT).getroot()
    original = {diagram.get("name"): diagram for diagram in mxfile.findall("diagram")}
    required = {"ERD", "System Architecture", "Package Diagram"}
    missing_pages = required - original.keys()
    if missing_pages:
        raise ValueError(f"Missing original pages; refusing to rewrite: {sorted(missing_pages)}")

    protected = {name: page_fingerprint(original[name]) for name in required}
    previous_variant = next((d for d in mxfile.findall("diagram") if d.get("name") == PAGE_NAME), None)
    if previous_variant is not None:
        mxfile.remove(previous_variant)
    variant = add_architecture_page()
    validate_page(variant)
    mxfile.append(variant)
    for name, fingerprint in protected.items():
        current = next(d for d in mxfile.findall("diagram") if d.get("name") == name)
        if page_fingerprint(current) != fingerprint:
            raise ValueError(f"Original page changed unexpectedly: {name}")

    mxfile.set("pages", str(len(mxfile.findall("diagram"))))
    mxfile.set("modified", datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"))
    mxfile.set("agent", "Codex")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("wb", suffix=".drawio.tmp", dir=OUT.parent, delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        ElementTree(mxfile).write(tmp_path, encoding="utf-8", xml_declaration=True)
        reparsed = parse(tmp_path).getroot()
        if len(reparsed.findall("diagram")) != 4:
            raise ValueError("Expected three original pages plus one architecture comparison page")
        os.replace(tmp_path, OUT)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    print(f"Updated {OUT}")
    print(f"Pages: {[(d.get('name'), len(list(d.iter('mxCell')))) for d in parse(OUT).getroot().findall('diagram')]}")
    print("Original ERD, System Architecture, and Package Diagram page fingerprints preserved.")


if __name__ == "__main__":
    main()
