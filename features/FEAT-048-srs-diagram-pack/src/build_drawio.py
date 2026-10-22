from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, parse


OUT = Path(__file__).resolve().parents[1] / "artifacts" / "Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio"


def page(name: str, page_id: str, width: int, height: int) -> tuple[Element, Element, dict[str, str]]:
    diagram = Element("diagram", {"id": page_id, "name": name})
    model = SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": str(width), "dy": str(height), "grid": "0", "gridSize": "10",
            "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
            "fold": "1", "page": "1", "pageScale": "1", "pageWidth": str(width),
            "pageHeight": str(height), "background": "#FFFFFF", "math": "0", "shadow": "0",
        },
    )
    root = SubElement(model, "root")
    SubElement(root, "mxCell", {"id": "0"})
    SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    return diagram, root, {}


def vertex(root: Element, ids: dict[str, str], key: str, label: str, x: int, y: int,
           w: int, h: int, style: str, parent: str = "1") -> str:
    cell_id = str(len(ids) + 2)
    ids[key] = cell_id
    cell = SubElement(root, "mxCell", {
        "id": cell_id, "value": label, "style": style, "vertex": "1", "parent": parent,
    })
    SubElement(cell, "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry",
    })
    return cell_id


def edge(root: Element, ids: dict[str, str], key: str, source: str, target: str,
         label: str, style: str,
         points: tuple[tuple[int, int], ...] | None = None) -> None:
    cell_id = str(len(ids) + 100)
    ids[key] = cell_id
    cell = SubElement(root, "mxCell", {
        "id": cell_id, "value": label, "style": style, "edge": "1", "parent": "1",
        "source": ids[source], "target": ids[target],
    })
    geometry = SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    if points:
        point_list = SubElement(geometry, "Array", {"as": "points"})
        for x, y in points:
            SubElement(point_list, "mxPoint", {"x": str(x), "y": str(y)})


TITLE = "text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;strokeColor=none;fillColor=none;fontSize=23;fontStyle=1;fontColor=#243247;"
SUBTITLE = "text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;strokeColor=none;fillColor=none;fontSize=13;fontColor=#64748B;"
NOTE = "rounded=0;whiteSpace=wrap;html=1;fillColor=#F7F9FC;strokeColor=#D7DEE8;fontColor=#46556A;fontSize=12;align=left;verticalAlign=middle;spacing=8;"
CONFIRMED = "rounded=0;whiteSpace=wrap;html=1;fillColor=#F0F6F4;strokeColor=#77988E;fontColor=#273F39;fontSize=13;align=left;verticalAlign=middle;spacing=8;"
PROPOSED = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFF9EC;strokeColor=#B79A5B;fontColor=#51452A;fontSize=13;align=left;verticalAlign=middle;spacing=8;dashed=1;"
BOX = "rounded=0;whiteSpace=wrap;html=1;fillColor=#F3F6FA;strokeColor=#8290A3;fontColor=#263448;fontSize=14;align=center;verticalAlign=middle;spacing=8;"
PKG = "swimlane;html=1;startSize=30;rounded=0;fillColor=#FFFFFF;swimlaneFillColor=#E9EEF4;strokeColor=#8794A5;fontColor=#253247;fontStyle=1;fontSize=14;horizontal=1;"
PACKAGE = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#8C98A8;fontColor=#2E3B4F;fontSize=12;align=center;verticalAlign=middle;spacing=5;"
ARROW = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#697789;fontSize=11;labelBackgroundColor=#FFFFFF;"
DASHED_ARROW = ARROW + "dashed=1;strokeColor=#A78B4D;"
REL = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;startArrow=ERone;startFill=0;endArrow=ERzeroToMany;endFill=0;strokeColor=#8993A0;strokeWidth=1;fontSize=10;fontColor=#4F5D6D;labelBackgroundColor=#FFFFFF;"


def add_page_heading(root: Element, ids: dict[str, str], title: str, subtitle: str,
                     width: int, note: str) -> None:
    vertex(root, ids, "title", title, 38, 18, width - 76, 38, TITLE)
    vertex(root, ids, "subtitle", subtitle, 40, 56, width - 80, 26, SUBTITLE)
    vertex(root, ids, "legend", note, 40, 88, width - 80, 38, NOTE)


def send_edges_behind_vertices(root: Element) -> None:
    children = list(root)
    base = children[:2]
    edges = [cell for cell in children[2:] if cell.get("edge") == "1"]
    vertices = [cell for cell in children[2:] if cell.get("edge") != "1"]
    containers = [cell for cell in vertices if "swimlane" in cell.get("style", "")]
    foreground = [cell for cell in vertices if cell not in containers]
    for cell in children:
        root.remove(cell)
    for cell in base + containers + edges + foreground:
        root.append(cell)


def build_erd() -> Element:
    width, height = 3400, 2050
    diagram, root, ids = page("ERD", "khoa-erd-v31", width, height)
    erd_title = TITLE
    erd_subtitle = SUBTITLE
    erd_note = NOTE
    vertex(root, ids, "title", "ERD — Sketch2Life SRS v3.1", 38, 18, width - 76, 38, erd_title)
    vertex(root, ids, "subtitle", "Chen notation • B7.1 core + selected B21.5 relationships • logical proposal, not a physical database migration", 40, 56, width - 80, 26, erd_subtitle)
    entity_style = "rounded=0;whiteSpace=wrap;html=1;fillColor=#E9F3E4;strokeColor=#6F9466;fontColor=#243527;fontSize=18;fontStyle=1;align=center;verticalAlign=middle;spacing=6;"
    relation_style = "rhombus;whiteSpace=wrap;html=1;fillColor=#E8EDFA;strokeColor=#7888B4;fontColor=#29334D;fontSize=16;align=center;verticalAlign=middle;spacing=4;"
    attribute_style = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#FFF0F1;strokeColor=#C98186;fontColor=#352B2D;fontSize=15;align=center;verticalAlign=middle;spacing=3;"
    key_attribute_style = attribute_style.replace("strokeColor=#C98186", "strokeColor=#AA5360").replace("fontSize=15", "fontSize=15;fontStyle=1")
    proposed_key_style = key_attribute_style.replace("strokeColor=#AA5360", "strokeColor=#B79A5B") + "dashed=1;"
    legend_text_style = "text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;strokeColor=none;fillColor=none;fontSize=12;fontColor=#46556A;"
    small_entity_style = entity_style.replace("fontSize=18", "fontSize=12")
    small_relation_style = relation_style.replace("fontSize=16", "fontSize=12")
    small_attribute_style = attribute_style.replace("fontSize=15", "fontSize=12")
    small_key_style = key_attribute_style.replace("fontSize=15", "fontSize=12")

    # Draw a visual symbol key instead of making readers decode a long sentence.
    vertex(root, ids, "legend_entity", "Entity", 40, 101, 90, 34, small_entity_style)
    vertex(root, ids, "legend_relationship", "", 155, 96, 58, 44, small_relation_style)
    vertex(root, ids, "legend_relationship_label", "Relationship", 220, 98, 100, 40, legend_text_style)
    vertex(root, ids, "legend_attribute", "Attribute", 325, 101, 104, 34, small_attribute_style)
    vertex(root, ids, "legend_key", "<u>id</u>", 445, 101, 62, 34, small_key_style)
    vertex(root, ids, "legend_key_label", "Key", 512, 98, 38, 40, legend_text_style)
    vertex(root, ids, "legend_cardinality", "<b>1</b> — ◇ — <b>0..N</b>", 565, 96, 190, 44, legend_text_style)
    vertex(root, ids, "legend_cardinality_label", "B7.1 endpoints", 760, 98, 115, 40, legend_text_style)
    vertex(
        root, ids, "legend_scope",
        "Scope: 16 B7.1 entities + OrganizationScope + selected B21.5 links (not all 34 B7 entities).<br/>Enrollment cardinality: TBD; GroupMembership episode key: proposed; CanvasDocument owner: group XOR participant; contributorRef: optional; DATA-24 review target_kind also includes knowledge_video and learning_content.",
        895, 90, width - 935, 60, erd_note,
    )
    plain_edge = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;startArrow=none;endArrow=none;strokeColor=#77818D;strokeWidth=1;fontSize=13;fontColor=#46515E;labelBackgroundColor=#FFFFFF;"
    attribute_edge = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;startArrow=none;endArrow=none;strokeColor=#A5ADB7;strokeWidth=1;"

    entities = {
        "organization": ("OrganizationScope", 1020, 220),
        "account": ("AdultAccount", 100, 570),
        "assignment": ("TeacherAssignment", 560, 570),
        "class": ("Class", 1020, 570),
        "enrollment": ("Enrollment", 1480, 570),
        "student": ("StudentProfile", 1940, 570),
        "portfolio": ("PortfolioEntry", 2480, 570),
        "consent": ("ConsentRecord", 3140, 1170),
        "session": ("ClassroomSession", 1020, 1170),
        "group": ("SessionGroup", 1480, 1170),
        "membership": ("GroupMembership", 1480, 1640),
        "participant": ("ChildParticipant", 1940, 880),
        "document": ("CanvasDocument", 2220, 1170),
        "operation": ("CanvasOperation", 2680, 1170),
        "snapshot": ("CanvasSnapshot", 2220, 1640),
        "proposal": ("SketchProposal", 2680, 1640),
        "review": ("TeacherReview", 3140, 1640),
    }
    entity_w, entity_h = 190, 70
    for key, (name, x, y) in entities.items():
        vertex(root, ids, key, name, x, y, entity_w, entity_h, entity_style)

    attributes = [
        ("a_organization_id", "organization", "<u>id</u>", 820, 215),
        ("a_organization_name", "organization", "name", 1220, 215),
        ("a_account_id", "account", "<u>id</u>", 115, 360), ("a_account_role", "account", "role", 115, 700),
        ("a_assignment_id", "assignment", "<u>id</u>", 575, 360), ("a_assignment_scope", "assignment", "scope", 575, 700),
        ("a_class_id", "class", "<u>id</u>", 1235, 335), ("a_class_name", "class", "name", 1235, 405),
        ("a_enrollment_id", "enrollment", "<u>id</u>", 1495, 360), ("a_enrollment_validity", "enrollment", "validity", 1495, 700),
        ("a_student_id", "student", "<u>id</u>", 1945, 355), ("a_student_alias", "student", "alias", 2075, 410),
        ("a_portfolio_id", "portfolio", "<u>id</u>", 2490, 360), ("a_portfolio_attribution", "portfolio", "attributionQuality", 2490, 700),
        ("a_consent_id", "consent", "<u>id</u>", 3140, 1270), ("a_consent_purposes", "consent", "purposes", 3140, 1350),
        ("a_session_id", "session", "<u>id</u>", 1060, 1280), ("a_session_lifecycle", "session", "lifecycle", 1060, 1360),
        ("a_group_id", "group", "<u>id</u>", 1480, 930), ("a_group_progress", "group", "progress", 1645, 970),
        ("a_member_id", "membership", "<u>membershipId*</u>", 1290, 1660),
        ("a_member_participant", "membership", "participantRef", 1695, 1490),
        ("a_member_group", "membership", "groupRef", 1695, 1570), ("a_member_validity", "membership", "validity", 1695, 1650),
        ("a_participant_id", "participant", "<u>id</u>", 1775, 810), ("a_participant_admission", "participant", "admissionState", 1985, 810),
        ("a_document_id", "document", "<u>id</u>", 2200, 930), ("a_document_revision", "document", "revision", 2365, 970),
        ("a_operation_id", "operation", "<u>id</u>", 2900, 930), ("a_operation_seq", "operation", "serverSeq", 2695, 1280),
        ("a_snapshot_id", "snapshot", "<u>id</u>", 2200, 1770), ("a_snapshot_hash", "snapshot", "hash", 2365, 1810),
        ("a_proposal_id", "proposal", "<u>id</u>", 2695, 1430), ("a_proposal_safety", "proposal", "safetyResult", 2850, 1470),
        ("a_review_id", "review", "<u>id</u>", 3110, 1430), ("a_review_decision", "review", "decision", 3235, 1550),
        ("a_review_reviewer", "review", "reviewerRef → AdultAccount", 3140, 1750),
    ]
    for key, owner, label, x, y in attributes:
        style = proposed_key_style if key == "a_member_id" else (key_attribute_style if "<u>" in label else attribute_style)
        if key == "a_consent_purposes":
            vertex(root, ids, key, label, x, y, 155, 52, style)
            double_style = style.replace("fillColor=#FFF0F1", "fillColor=none;")
            vertex(root, ids, f"{key}_inner", "", x + 6, y + 5, 143, 42, double_style)
            edge(root, ids, f"{key}_link", owner, key, "", attribute_edge)
            continue
        vertex(root, ids, key, label, x, y, 155, 52, style)
        edge(root, ids, f"{key}_link", owner, key, "", attribute_edge)

    relationships = [
        ("rel_scope_class", "governs", "organization", "class", 1045, 390, "1", "0..N"),
        ("rel_receives", "receives", "account", "assignment", 370, 560, "1", "0..N"),
        ("rel_authorizes", "authorizes", "class", "assignment", 830, 560, "1", "0..N"),
        ("rel_contains_enrollment", "contains", "class", "enrollment", 1290, 560, "1", "0..N"),
        ("rel_joins", "joins", "student", "enrollment", 1750, 560, "1", "0..N"),
        ("rel_collects", "collects", "student", "portfolio", 2220, 560, "1", "0..N"),
        ("rel_protected", "protected", "student", "consent", 2670, 850, "1", "0..N"),
        ("rel_hosts", "hosts", "class", "session", 1050, 850, "1", "0..N"),
        ("rel_session_group", "contains", "session", "group", 1290, 1150, "1", "0..N"),
        ("rel_admits", "admits", "session", "participant", 1280, 960, "1", "0..N"),
        ("rel_group_membership", "has", "group", "membership", 1510, 1390, "1", "0..N"),
        ("rel_belongs", "belongs", "participant", "membership", 1710, 1270, "1", "0..N"),
        ("rel_owns_document", "owns", "session", "document", 1870, 1480, "1", "0..N"),
        ("rel_records", "records", "document", "operation", 2440, 1150, "1", "0..N"),
        ("rel_checkpoints", "checkpoints", "document", "snapshot", 2250, 1390, "1", "0..N"),
        ("rel_grounds", "grounds", "snapshot", "proposal", 2440, 1610, "1", "0..N"),
        ("rel_reviewed", "reviewed", "proposal", "review", 2900, 1610, "1", "0..N"),
        ("rel_student_participant", "participates", "student", "participant", 1965, 700, "1", "0..N"),
        ("rel_group_canvas", "shared canvas", "group", "document", 1810, 1010, "0..N", "0..1"),
        ("rel_personal_canvas", "personal canvas", "participant", "document", 2090, 1010, "0..N", "0..1"),
        ("rel_contributor", "attributed to", "participant", "operation", 2500, 850, "0..N", "0..1"),
    ]
    for key, label, source, target, x, y, source_cardinality, target_cardinality in relationships:
        vertex(root, ids, key, label, x, y, 140, 90, relation_style)
        if key == "rel_owns_document":
            # Route around SessionGroup/GroupMembership so the B7.1 link reads as Session–CanvasDocument.
            edge(root, ids, f"{key}_source_cardinality", source, key, source_cardinality, plain_edge,
                 ((1115, 1375), (1940, 1375)))
            edge(root, ids, f"{key}_target_cardinality", target, key, target_cardinality, plain_edge,
                 ((2180, 1205), (2180, 1510), (2030, 1510)))
        else:
            edge(root, ids, f"{key}_source_cardinality", source, key, source_cardinality, plain_edge)
            edge(root, ids, f"{key}_target_cardinality", target, key, target_cardinality, plain_edge)

    send_edges_behind_vertices(root)
    return diagram


def build_architecture() -> Element:
    width, height = 1800, 1320
    diagram, root, ids = page("System Architecture", "khoa-system-architecture-v31", width, height)
    add_page_heading(
        root, ids, "System Architecture — Sketch2Life SRS v3.1",
        "Logical target architecture • solid arrows = request / inward dependency • dashed orange arrows = proposed adapters implement ports",
        width,
        "CONFIRMED: Android / React Native, FastAPI, Teacher and Super Admin surfaces. PROPOSED: context groupings, contracts, realtime, workers and infrastructure. AI credentials/endpoints stay on backend.",
    )

    actor_y, actor_w, actor_h = 155, 360, 64
    actors = [
        ("child", "Child", 120),
        ("teacher", "Teacher", 720),
        ("admin", "Super Admin", 1320),
    ]
    for key, label, x in actors:
        vertex(root, ids, key, f"<b>{label}</b><br/>Role-scoped user", x, actor_y, actor_w, actor_h, CONFIRMED)

    client_y = 255
    vertex(root, ids, "android", "<b>Child Android app</b><br/>React Native / TypeScript • confirmed", 120, client_y, 360, 82, CONFIRMED)
    vertex(root, ids, "teacherUi", "<b>Teacher Desktop</b><br/>Surface confirmed • framework TBD", 720, client_y, 360, 82, CONFIRMED)
    vertex(root, ids, "adminUi", "<b>Super Admin surface</b><br/>Scope confirmed • framework TBD", 1320, client_y, 360, 82, CONFIRMED)

    vertex(root, ids, "api", "<b>FastAPI / Python backend</b><br/>Authentication boundary • commands / queries • confirmed", 80, 385, 1500, 88, CONFIRMED)

    app_frame = "swimlane;html=1;startSize=34;rounded=0;fillColor=#FFFFFF;swimlaneFillColor=#E9EEF4;strokeColor=#8794A5;fontColor=#253247;fontStyle=1;fontSize=14;horizontal=1;"
    domain_frame = "swimlane;html=1;startSize=38;rounded=0;fillColor=#FFFFFF;swimlaneFillColor=#EEF2F5;strokeColor=#A2AFBD;fontColor=#253247;fontStyle=1;fontSize=14;horizontal=1;"
    vertex(root, ids, "application_frame", "APPLICATION LAYER", 320, 535, 1380, 150, app_frame)
    vertex(root, ids, "usecases", "<b>Application use cases</b><br/>Orchestration • authorization checks", 355, 577, 950, 78, BOX)
    vertex(root, ids, "ports", "<b>Outbound ports</b><br/>Repository • artifact • job<br/>model • identity • realtime", 1360, 577, 300, 78, BOX)

    vertex(root, ids, "domain_frame", "DOMAIN LAYER — framework independent • context groupings proposed", 80, 735, 1240, 430, domain_frame)
    contexts = [
        ("c1", "Identity / Consent"), ("c2", "Classroom"), ("c3", "Session / Groups"),
        ("c4", "Drawing / Collaboration"), ("c5", "AI Assistance"), ("c6", "Knowledge / Media"),
        ("c7", "Activities"), ("c8", "Portfolio / Assessment"), ("c9", "Governance / Audit"),
    ]
    cx0, cy, cw, ch, xgap, ygap = 105, 795, 355, 76, 25, 105
    for i, (key, label) in enumerate(contexts):
        col, row = i % 3, i // 3
        context_style = PROPOSED.replace("fontSize=13", "fontSize=12").replace("spacing=8", "spacing=5")
        vertex(root, ids, key, f"<b>{label}</b>", cx0 + col * (cw + xgap), cy + row * ygap, cw, ch, context_style)

    vertex(
        root, ids, "infra",
        "<b>Infrastructure adapters — candidates</b><br/><br/>Relational database<br/>Object storage<br/>Queue / worker<br/>Realtime / presence<br/>AI provider (backend only)<br/><br/>Credentials and provider endpoints stay on the backend.",
        1360, 770, 300, 265, PROPOSED,
    )

    edge(root, ids, "e1", "child", "android", "uses", ARROW)
    edge(root, ids, "e2", "teacher", "teacherUi", "uses", ARROW)
    edge(root, ids, "e3", "admin", "adminUi", "uses", ARROW)
    edge(root, ids, "e4", "android", "api", "HTTPS", ARROW + "entryX=0.147;entryY=0;entryDx=0;entryDy=0;")
    edge(root, ids, "e5", "teacherUi", "api", "HTTPS", ARROW + "entryX=0.547;entryY=0;entryDx=0;entryDy=0;")
    edge(root, ids, "e6", "adminUi", "api", "HTTPS", ARROW + "entryX=0.947;entryY=0;entryDx=0;entryDy=0;")
    edge(root, ids, "e7", "api", "usecases", "validated requests", ARROW)
    edge(root, ids, "e8", "usecases", "domain_frame", "invokes policies", ARROW + "entryX=0.601;entryY=0;entryDx=0;entryDy=0;")
    edge(root, ids, "e10", "usecases", "ports", "uses", ARROW)
    edge(root, ids, "e11", "infra", "ports", "implements outbound ports • proposed", DASHED_ARROW)
    send_edges_behind_vertices(root)
    return diagram

def build_packages() -> Element:
    width, height = 1600, 1100
    diagram, root, ids = page("Package Diagram", "khoa-package-diagram-v31", width, height)
    add_page_heading(
        root, ids, "Package Diagram — Sketch2Life SRS v3.1",
        "Package boundaries and dependency direction • bounded contexts are proposed in B8",
        width,
        "Dependency direction: interface adapters → application → domain. Infrastructure implements inward ports; cross-feature behavior uses versioned contracts.",
    )

    # Top-level package containers.
    vertex(root, ids, "presentationPkg", "presentation", 40, 175, 320, 225, PKG)
    vertex(root, ids, "interfacePkg", "inbound_adapters", 410, 175, 320, 225, PKG)
    vertex(root, ids, "applicationPkg", "application", 780, 175, 320, 225, PKG)
    vertex(root, ids, "domainPkg", "domain", 1170, 175, 390, 650, PKG)
    vertex(root, ids, "infraPkg", "infrastructure", 410, 465, 690, 350, PKG)

    # Leaf packages; intentionally keep dependency arrows between outer and inner layers.
    vertex(root, ids, "pAndroid", "child_android · React Native", 58, 230, 284, 42, PACKAGE)
    vertex(root, ids, "pTeacher", "teacher_desktop", 58, 285, 284, 42, PACKAGE)
    vertex(root, ids, "pAdmin", "super_admin_ui", 58, 340, 284, 42, PACKAGE)

    vertex(root, ids, "pHttp", "http_api · FastAPI", 428, 235, 284, 48, PACKAGE)
    vertex(root, ids, "pRealtime", "realtime_adapter · proposed", 428, 305, 284, 48, PROPOSED)
    vertex(root, ids, "pUsecases", "use_cases", 798, 235, 284, 48, PACKAGE)
    vertex(root, ids, "pPorts", "ports / versioned_contracts", 798, 305, 284, 48, PACKAGE)

    domain_leafs = [
        ("d1", "identity_consent"), ("d2", "classroom"), ("d3", "session_groups"),
        ("d4", "drawing_collaboration"), ("d5", "ai_assistance"), ("d6", "knowledge_media"),
        ("d7", "activities"), ("d8", "portfolio_assessment"), ("d9", "governance_audit"),
    ]
    for i, (key, label) in enumerate(domain_leafs):
        col, row = i % 2, i // 2
        small_proposal = PROPOSED.replace("fontSize=13", "fontSize=11").replace("spacing=8", "spacing=5")
        vertex(root, ids, key, f"{label.replace('_', '<br/>')}<br/><i>proposed</i>",
               1188 + col * 181, 225 + row * 112, 164, 72, small_proposal)

    infra_leafs = [
        ("iIdentity", "identity adapter<br/>provider TBD"),
        ("iPersistence", "persistence adapter<br/>database candidate"),
        ("iArtifact", "artifact storage<br/>object-store candidate"),
        ("iWorker", "worker / queue<br/>candidate"),
        ("iAi", "AI provider adapter<br/>backend only"),
        ("iRealtime", "realtime transport<br/>proposed"),
    ]
    for i, (key, label) in enumerate(infra_leafs):
        col, row = i % 3, i // 3
        vertex(root, ids, key, label, 428 + col * 218, 525 + row * 112, 200, 78,
               PROPOSED if key in {"iWorker", "iRealtime", "iPersistence", "iArtifact"} else PACKAGE)

    vertex(root, ids, "rule", "<b>Architecture rule</b><br/>Domain packages depend on no UI, framework, storage or provider package.<br/>Versioned contracts mediate cross-feature behavior.", 410, 860, 1150, 100, NOTE)

    edge(root, ids, "dapi", "presentationPkg", "interfacePkg", "uses", ARROW)
    edge(root, ids, "dapp", "interfacePkg", "applicationPkg", "calls", ARROW)
    edge(root, ids, "ddomain", "applicationPkg", "domainPkg", "depends inward", ARROW)
    edge(root, ids, "dports", "infraPkg", "pPorts", "implements port contracts", DASHED_ARROW)
    edge(root, ids, "drealtime", "presentationPkg", "pRealtime", "proposed stream", DASHED_ARROW)
    send_edges_behind_vertices(root)
    return diagram


def main() -> None:
    modified = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    if OUT.exists():
        # Preserve owner-authored ERD and Package edits; this task rebuilds only Architecture.
        mxfile = parse(OUT).getroot()
        existing_pages = {diagram.get("name"): diagram for diagram in mxfile.findall("diagram")}
        required_pages = {"ERD", "System Architecture", "Package Diagram"}
        missing = required_pages - existing_pages.keys()
        if missing:
            raise ValueError(f"Existing diagram file is missing required pages: {sorted(missing)}")
        architecture = build_architecture()
        old_architecture = existing_pages["System Architecture"]
        index = list(mxfile).index(old_architecture)
        mxfile.remove(old_architecture)
        mxfile.insert(index, architecture)
        mxfile.set("modified", modified)
        mxfile.set("agent", "Codex")
    else:
        mxfile = Element("mxfile", {
            "host": "app.diagrams.net", "modified": modified,
            "agent": "Codex", "version": "24.7.17", "type": "device",
        })
        mxfile.append(build_erd())
        mxfile.append(build_architecture())
        mxfile.append(build_packages())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ElementTree(mxfile).write(OUT, encoding="utf-8", xml_declaration=True)
    print(OUT)


if __name__ == "__main__":
    main()
