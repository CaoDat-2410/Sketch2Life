from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, Cm, RGBColor
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "features" / "FEAT-058-review2-document-package"
ARTIFACTS = FEATURE / "artifacts"
DOC_REVISION = int(os.environ.get("FEAT058_DOC_REVISION", "6"))
OUT = ARTIFACTS / f"submission_r2_rev{DOC_REVISION}"
DIAGRAMS = ARTIFACTS / "diagrams"
SRS = ROOT / "features/FEAT-039-collaborative-learning-scope/artifacts/Collaborative_Learning_SRS_v3.1.md"
REGISTRATION = Path.home() / 'Downloads' / 'Phieu_FA26SE225_v1.2 (1).docx'
BM01_SOURCE = ARTIFACTS / "SWP490_FA26SE225_R2_DesignBrief.docx"
BM02_TEMPLATE = Path.home() / 'Downloads' / 'SWP490_R2_BM04_Review2-Document' / 'SWP490_R2_BM02_Self_Review_Report_1.docx'
BM03_TEMPLATE = Path.home() / 'Downloads' / 'SWP490_R2_BM04_Review2-Document' / 'SWP490_R2_BM03_Record_of_Changes_1.docx'
REPORT_SOURCE = ARTIFACTS / "SWP490_FA26SE225_R2_Reports1-5_Tracking.docx"
NAVY = "14243D"
TEAL = "197C78"
LIGHT = "EEF2F8"
PALE = "EAF2F4"
ORANGE = "E68B35"
GRAY = "566170"
WHITE = "FFFFFF"
FONT_PATH = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_BOLD_PATH = Path(r"C:\Windows\Fonts\arialbd.ttf")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_cell(cell, value, *, bold=False, color=None, size=8.5):
    cell.text = str(value)
    for para in cell.paragraphs:
        para.paragraph_format.space_after = Pt(1)
        para.paragraph_format.space_before = Pt(0)
        for run in para.runs:
            run.font.name = "Arial"
            run.font.size = Pt(size)
            run.bold = bold
            if color:
                run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = 1


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def fit_table_widths(table, widths, max_width=6.0):
    widths = [float(width) for width in widths]
    total = sum(widths)
    if total > max_width:
        widths = [width * max_width / total for width in widths]
    twips = [round(width * 1440) for width in widths]
    max_twips = round(max_width * 1440)
    if sum(twips) > max_twips:
        twips[-1] -= sum(twips) - max_twips
    for grid_col, width_twips in zip(table._tbl.tblGrid.gridCol_lst, twips):
        grid_col.set(qn("w:w"), str(width_twips))
    for row in table.rows:
        if len(row.cells) == len(twips):
            for cell, width_twips in zip(row.cells, twips):
                cell.width = Inches(width_twips / 1440)
    tbl_pr = table._tbl.tblPr
    tbl_width = tbl_pr.find(qn("w:tblW"))
    if tbl_width is None:
        tbl_width = OxmlElement("w:tblW")
        tbl_pr.append(tbl_width)
    tbl_width.set(qn("w:type"), "dxa")
    tbl_width.set(qn("w:w"), str(sum(twips)))
    table_indent = tbl_pr.find(qn("w:tblInd"))
    if table_indent is not None:
        table_indent.set(qn("w:type"), "dxa")
        table_indent.set(qn("w:w"), "0")
    return [width / 1440 for width in twips]


def format_table(table, widths=None, size=8.2):
    try:
        table.style = "Table Grid"
    except KeyError:
        pass
    table.autofit = False
    table.alignment = 1
    for i, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_alignment = 1
            if i == 0:
                shade(cell, NAVY)
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(1)
                para.paragraph_format.space_before = Pt(0)
                for run in para.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(size)
                    if i == 0:
                        run.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
    if widths:
        fit_table_widths(table, widths, max_width=6.0)


def add_table_before(doc, ref, headers, rows, widths=None, size=8.0):
    table = doc.add_table(rows=1, cols=len(headers))
    for i, value in enumerate(headers):
        set_cell(table.rows[0].cells[i], value, bold=True, color=WHITE, size=size)
        shade(table.rows[0].cells[i], NAVY)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell(cells[i], value, size=size)
    table._tbl.getparent().remove(table._tbl)
    ref._p.addprevious(table._tbl)
    format_table(table, widths, size)
    return table


def add_para_before(ref, text, style="Normal", *, bold_lead=None, page_break=False):
    para = ref.insert_paragraph_before(style=style)
    if page_break:
        para.paragraph_format.page_break_before = True
    if bold_lead and text.startswith(bold_lead):
        r = para.add_run(bold_lead)
        r.bold = True
        para.add_run(text[len(bold_lead):])
    else:
        para.add_run(text)
    return para


def add_heading_before(ref, text, level=2, page_break=False):
    return add_para_before(ref, text, f"Heading {level}", page_break=page_break)


def insert_image_before(doc, ref, image_path, caption):
    p = ref.insert_paragraph_before()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run()
    r.add_picture(str(image_path), width=Inches(6.35))
    c = ref.insert_paragraph_before(caption)
    if "Caption" in [style.name for style in doc.styles]:
        c.style = doc.styles["Caption"]
    else:
        c.style = doc.styles["Normal"]
        for run in c.runs:
            run.italic = True
            run.font.size = Pt(8)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6)


def ref_heading(doc, text):
    for p in doc.paragraphs:
        if p.style.name == "Heading 1" and p.text.strip() == text:
            return p
    raise ValueError(f"missing report section: {text}")


def write_mmd(name, body):
    path = DIAGRAMS / f"{name}.mmd"
    path.write_text(body.strip() + "\n", encoding="utf-8")
    return path


def activity_png(filename, title, subtitle, lanes, nodes, edges):
    width, height = 1800, 1160
    im = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(im)
    try:
        f_title = ImageFont.truetype(str(FONT_BOLD_PATH), 42)
        f_body = ImageFont.truetype(str(FONT_PATH), 23)
        f_lane = ImageFont.truetype(str(FONT_BOLD_PATH), 23)
        f_sub = ImageFont.truetype(str(FONT_PATH), 20)
    except OSError:
        f_title = f_lane = f_body = f_sub = ImageFont.load_default()
    d.rectangle((0, 0, width, 138), fill=f"#{NAVY}")
    d.text((54, 24), title, font=f_title, fill="white")
    d.text((57, 84), subtitle, font=f_sub, fill="#D9E3EF")
    left, right, top, bottom = 65, width - 65, 180, height - 75
    lane_w = (right - left) / len(lanes)
    lane_fill = ["F7F9FC", "F1F5F7", "F7F9FC", "F1F5F7"]
    for i, lane in enumerate(lanes):
        x1 = int(left + i * lane_w)
        x2 = int(left + (i + 1) * lane_w)
        d.rectangle((x1, top, x2, bottom), fill=f"#{lane_fill[i % len(lane_fill)]}", outline="#CDD6E0", width=2)
        d.rectangle((x1, top, x2, top + 54), fill=f"#{NAVY}")
        box = d.textbbox((0, 0), lane, font=f_lane)
        d.text((x1 + (x2 - x1 - (box[2] - box[0])) / 2, top + 13), lane, font=f_lane, fill="white")
    rects = {}
    box_w = int(lane_w - 76)
    box_h = 100
    for key, lane_idx, row, label, kind in nodes:
        x1 = int(left + lane_idx * lane_w + 38)
        y1 = top + 92 + row * 145
        x2, y2 = x1 + box_w, y1 + box_h
        fill = "EAF2F4" if kind == "normal" else "FBF1E7" if kind == "exception" else "EEF2F8"
        outline = TEAL if kind == "normal" else ORANGE if kind == "exception" else NAVY
        d.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=f"#{fill}", outline=f"#{outline}", width=3)
        words = label.split()
        lines, line = [], ""
        for word in words:
            trial = word if not line else line + " " + word
            if d.textbbox((0, 0), trial, font=f_body)[2] <= box_w - 28:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        line_h = 29
        y = y1 + (box_h - len(lines) * line_h) / 2
        for line in lines:
            bbox = d.textbbox((0, 0), line, font=f_body)
            d.text((x1 + (box_w - (bbox[2] - bbox[0])) / 2, y), line, font=f_body, fill=f"#{NAVY}")
            y += line_h
        rects[key] = (x1, y1, x2, y2)
    for a, b, label in edges:
        ax1, ay1, ax2, ay2 = rects[a]
        bx1, by1, bx2, by2 = rects[b]
        acx, acy = (ax1 + ax2) / 2, (ay1 + ay2) / 2
        bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
        if abs(bcx - acx) > abs(bcy - acy):
            start = (ax2 if bcx > acx else ax1, acy)
            end = (bx1 if bcx > acx else bx2, bcy)
        else:
            start = (acx, ay2 if bcy > acy else ay1)
            end = (bcx, by1 if bcy > acy else by2)
        d.line((start, end), fill=f"#{TEAL}", width=4)
        theta = __import__("math").atan2(end[1] - start[1], end[0] - start[0])
        import math
        head = 14
        p2 = (end[0] - head * math.cos(theta - .52), end[1] - head * math.sin(theta - .52))
        p3 = (end[0] - head * math.cos(theta + .52), end[1] - head * math.sin(theta + .52))
        d.polygon([end, p2, p3], fill=f"#{TEAL}")
        if label:
            mx, my = int((start[0] + end[0]) / 2), int((start[1] + end[1]) / 2)
            d.rounded_rectangle((mx - 72, my - 22, mx + 72, my + 4), radius=5, fill="white")
            d.text((mx - 67, my - 20), label, font=f_sub, fill=f"#{TEAL}")
    d.text((65, height - 52), "Solid arrows show the business sequence; amber boxes show exception handling. Proposed provider or storage edges are labeled in the SDD.", font=f_sub, fill=f"#{GRAY}")
    path = OUT / "diagrams" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def logical_erd_png():
    width, height = 1800, 1040
    im = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(im)
    try:
        title_font = ImageFont.truetype(str(FONT_BOLD_PATH), 40)
        body_font = ImageFont.truetype(str(FONT_PATH), 20)
        cap_font = ImageFont.truetype(str(FONT_BOLD_PATH), 22)
    except OSError:
        title_font = body_font = cap_font = ImageFont.load_default()
    d.rectangle((0, 0, width, 142), fill=f"#{NAVY}")
    d.text((55, 24), "Logical domain ERD", font=title_font, fill="white")
    d.text((58, 84), "Target entity relationships from SRS v3.1; physical implementation is cross-referenced separately", font=body_font, fill="#D9E3EF")
    groups = [("Classroom and identity", 40), ("Drawing and AI review", 620), ("Learning and governance", 1200)]
    for label, x in groups:
        d.rounded_rectangle((x, 175, x+540, 945), radius=18, fill="#F7F9FC", outline="#CDD6E0", width=2)
        d.text((x+20, 190), label, font=cap_font, fill=f"#{NAVY}")
    specs = {
        "org": (0,0,"OrganizationScope\npolicy + school boundary"), "class": (0,1,"Class / Enrollment\nassignment + managed profile"),
        "session": (0,2,"ClassroomSession\nversion + teacher lifecycle"), "group": (0,3,"SessionGroup / Membership\nindependent progress"),
        "participant": (0,4,"ChildParticipant / Device\nmanaged admission capability"),
        "canvas": (1,0,"CanvasDocument / Region\nscope + permission + epoch"), "operation": (1,1,"CanvasOperation\nprincipal + contributor + sequence"),
        "snapshot": (1,2,"CanvasSnapshot / ArtworkShare\nimmutable hash + provenance"), "job": (1,3,"Vision / AI Job\nsource + context + typed status"),
        "proposal": (1,4,"SketchProposal / TeacherReview\nseparate version + human gate"), "response": (1,5,"ChildResponse\nview / hide / decline"),
        "knowledge": (2,0,"KnowledgeBundle / VideoJob\nsource + script + attempt"), "video": (2,1,"ReviewedVideo\nexact version + approval"),
        "activity": (2,2,"ActivityDefinition / Assignment\nreview + class/group scope"), "learning": (2,3,"Observation / Reflection\nevidence + descriptive context"),
        "portfolio": (2,4,"PortfolioEntry\nlineage + attribution"), "consent": (2,5,"Consent / Audit / Retention\npurpose + lifecycle evidence"),
    }
    boxes = {}
    col_x = [55, 635, 1215]
    for key, (col, row, label) in specs.items():
        x1 = col_x[col] + 25
        y1 = 245 + row * 108
        x2, y2 = x1 + 490, y1 + 78
        fill = "EAF2F4" if col == 0 else "EEF2F8" if col == 1 else "FBF1E7"
        edge = TEAL if col == 0 else NAVY if col == 1 else ORANGE
        d.rounded_rectangle((x1,y1,x2,y2), radius=12, fill=f"#{fill}", outline=f"#{edge}", width=2)
        for j, line in enumerate(label.split("\n")):
            bb = d.textbbox((0,0),line,font=body_font)
            d.text((x1+(490-(bb[2]-bb[0]))/2,y1+15+j*27),line,font=body_font,fill=f"#{NAVY}")
        boxes[key]=(x1,y1,x2,y2)
    edges=[("org","class"),("class","session"),("session","group"),("group","participant"),("session","canvas"),("canvas","operation"),("operation","snapshot"),("snapshot","job"),("job","proposal"),("proposal","response"),("knowledge","video"),("session","activity"),("activity","learning"),("learning","portfolio"),("class","consent")]
    for a,b in edges:
        a1,b1,a2,b2=boxes[a]; c1,d1,c2,d2=boxes[b]
        if a2 <= c1:
            start=(a2,(b1+b2)/2); end=(c1,(d1+d2)/2)
        elif b1 > b2:
            start=((a1+a2)/2,b2); end=((c1+c2)/2,d1)
        else:
            start=((a1+a2)/2,b2); end=((c1+c2)/2,d1)
        d.line((start,end),fill=f"#{TEAL}",width=3)
        theta=__import__("math").atan2(end[1]-start[1],end[0]-start[0])
        import math
        head=12
        p2=(end[0]-head*math.cos(theta-.5),end[1]-head*math.sin(theta-.5))
        p3=(end[0]-head*math.cos(theta+.5),end[1]-head*math.sin(theta+.5))
        d.polygon([end,p2,p3],fill=f"#{TEAL}")
    d.text((55, 975), "Relationship arrows are logical target references. Only foreign keys enumerated in the migration register are physical database constraints.", font=body_font, fill=f"#{GRAY}")
    path=OUT/"diagrams"/"D19_logical_domain_erd.png"
    path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path)
    return path


WORKFLOWS = [
    ("D15_WF01_prepare_admit_activity", "WF-01 Prepare and admit a class session", "Teacher admission and durable class/session state; code and consent failures return to the Teacher.",
     ["Teacher", "Backend", "Child"],
     [("a",0,0,"Configure class, topic, groups and tools","normal"),("b",1,0,"Validate assignment, age and session configuration","normal"),("c",0,1,"Open lobby and display QR or session code","normal"),("d",2,1,"Join with a Teacher-managed profile","normal"),("e",1,2,"Check code, roster, profile and effective consent","normal"),("f",0,3,"Review the request and explicitly admit","normal"),("g",1,4,"Persist membership and scoped device grant","normal"),("h",0,5,"Explicitly start or reject the session","normal"),("i",1,6,"Persist Active state before serving admission","normal"),("x",2,3,"Invalid, expired or unauthorized join is denied","exception")],
     [("a","b",""),("b","c","valid"),("c","d",""),("d","e",""),("e","f","eligible"),("f","g","admit"),("g","h",""),("h","i","start"),("e","x","reject")]),
    ("D16_WF02_collaborative_drawing_activity", "WF-02 Draw and recover a collaborative canvas", "Accepted operation, contributor attribution and reconnect behavior; unacknowledged changes are never reported as durable.",
     ["Child / Device", "Backend", "Teacher / Peer"],
     [("a",0,0,"Open permitted personal or shared canvas","normal"),("b",0,1,"Submit operation with verified principal and selected contributor","normal"),("c",1,2,"Check membership, scope, epoch and idempotency","normal"),("d",1,3,"Commit operation and durable receipt","normal"),("e",2,4,"Render accepted sequence to connected peers","normal"),("f",2,5,"Teacher monitors progress and controls pause/resume","normal"),("x",0,3,"Disconnect, retain pending work and reconnect","exception"),("y",1,4,"Return checkpoint and replay accepted sequence","normal"),("z",1,5,"Reject stale/conflicting op without mutation","exception")],
     [("a","b",""),("b","c",""),("c","d","accepted"),("d","e",""),("e","f",""),("b","x","offline"),("x","y","reconnect"),("y","c","replay"),("c","z","invalid")]),
    ("D17_WF03_ai_sketch_review_activity", "WF-03 Request and review an AI sketch", "The Teacher approves an exact version before the Child may see it; the source drawing remains separate and unchanged.",
     ["Child / Teacher", "Backend", "Worker / Modal"],
     [("a",0,0,"Child requests optional assistance","normal"),("b",1,1,"Check purpose, scope, consent and source version","normal"),("c",1,2,"Create immutable snapshot and queued job","normal"),("d",2,3,"Run provider adapter; Modal deployment remains TBD","review"),("e",1,4,"Validate typed result, safety and freshness","normal"),("f",0,5,"Teacher reviews exact proposal; edit, approve or reject","normal"),("g",1,6,"Record versioned review and provenance","normal"),("h",0,7,"Child may view, hide or decline approved suggestion","normal"),("x",2,5,"Unsafe, stale or failed job stays unavailable","exception")],
     [("a","b",""),("b","c","eligible"),("c","d",""),("d","e","result"),("e","f","safe"),("f","g","decision"),("g","h","approved"),("d","x","error"),("x","f","status")]),
    ("D18_WF04_reviewed_learning_and_close_activity", "WF-04 Present reviewed learning and close the session", "Exact-version media review, explicit failure disposition, off-screen activity and durable session outcome.",
     ["Teacher / Child", "Backend", "Worker / Storage"],
     [("a",0,0,"Teacher selects reviewed knowledge/video version","normal"),("b",1,1,"Check source, audience, version and review status","normal"),("c",2,2,"Prepare media and report true generation state","review"),("d",0,3,"Teacher reviews exact item and explicitly starts playback","normal"),("e",0,4,"After exhausted retries choose retry, skip or end","exception"),("f",0,5,"Assign reviewed class or group activity","normal"),("g",0,6,"Children do off-screen activity and reflect","normal"),("h",1,7,"Persist observation and session outcome","normal"),("i",2,8,"Confirm durable save before Completed state","normal"),("x",1,5,"Skip is recorded; video is not marked played","exception")],
     [("a","b",""),("b","c","generation"),("b","d","library"),("c","d","ready"),("c","e","exhausted"),("e","c","retry"),("e","x","skip"),("d","f",""),("f","g",""),("g","h",""),("h","i","saved")]),
]


def render_workflow_diagrams():
    rendered = {}
    for name, title, subtitle, lanes, nodes, edges in WORKFLOWS:
        source_file = DIAGRAMS / f"{name}.mmd"
        rendered[name] = OUT / "diagrams" / f"{name}.png"
        if not source_file.exists():
            raise FileNotFoundError(source_file)
        activity_png(rendered[name].name, title, subtitle, lanes, nodes, edges)
    rendered["D19_logical_domain_erd"] = logical_erd_png()
    return rendered


MODULES = [
    ("M01", "Identity, roles and permissions", "Adult authentication, verified principal, scoped authorization and capability grants."),
    ("M02", "Class and student management", "Teacher assignments, managed profiles, enrollment and adult-confirmed age context."),
    ("M03", "Session lifecycle and orchestration", "Teacher-controlled lobby, start, pause, resume, stage, close and recovery."),
    ("M04", "Group management", "Manual grouping, membership history and independent group progress."),
    ("M05", "Collaborative drawing canvas", "Personal/shared canvas, operations, turn attribution, snapshots and reconnect."),
    ("M06", "AI Vision and adaptive sketch", "Contextual understanding, uncertainty, separate proposal, moderation and review."),
    ("M07", "Artwork gallery and sharing", "Teacher-selected snapshot, ordering, classroom presentation and audience scope."),
    ("M08", "Knowledge and video", "Knowledge sources, script/media version, generation status, exact-version review and playback."),
    ("M09", "Off-screen activity library", "Reviewed age/material/safety instructions and class/group assignment."),
    ("M10", "Assessment and learning portfolio", "Reflection, evidence-linked observations and non-ranking progress history."),
    ("M11", "Teacher dashboard and automation", "Class/group monitoring, help queue, presets and explicit Teacher override."),
    ("M12", "Super Admin console", "Adult accounts, roles, content, policies, scoped requests and operational health."),
    ("M13", "Privacy, consent and audit", "School-mediated purpose evidence, data requests, retention, delete/export and audit."),
    ("M14", "Recovery and exception handling", "Idempotency, stale work, reconnect, retries, typed errors and durable receipts."),
]

USE_CASES = [
    ("UC-001", "Adult sign-in and scoped authorization", "Teacher / Super Admin", "FR001, FR005"),
    ("UC-002", "Manage class, child profile and enrollment", "Teacher", "FR004"),
    ("UC-003", "Record, verify and revoke purpose consent", "Authorized Teacher / Admin", "FR006"),
    ("UC-004", "Configure session, open Lobby and explicitly start", "Teacher", "FR007, FR010"),
    ("UC-005", "Create and edit groups", "Teacher", "FR008"),
    ("UC-006", "Propose automated grouping (Phase 2)", "Teacher", "FR065"),
    ("UC-007", "Join by QR/code and Teacher admission", "Child / Teacher", "FR002"),
    ("UC-008", "Shared tablet and turn contributor selection", "Child / Teacher", "FR003, FR066"),
    ("UC-009", "Track independent group progress", "Child / Teacher", "FR009"),
    ("UC-010", "Pause, resume, advance and end early", "Teacher", "FR010, FR013"),
    ("UC-011", "Close session and save outcome", "Teacher", "FR011"),
    ("UC-012", "Move participant or leave a group", "Teacher", "FR012"),
    ("UC-013", "Open canvas and draw with permitted tools", "Child", "FR014, FR015, FR020"),
    ("UC-014", "Request help, lock region and recover canvas", "Child / Teacher", "FR016"),
    ("UC-015", "Scoped undo, history and replay", "Child / Teacher", "FR018, FR021"),
    ("UC-016", "Disconnect, resync and recover session/canvas", "Child / Teacher", "FR017, FR060, FR063"),
    ("UC-017", "Keep AI overlay separate from child strokes", "Child / Teacher", "FR019, FR028"),
    ("UC-018", "Vision and confirm/correct meaning", "Child / Teacher", "FR022, FR023"),
    ("UC-019", "Request and prepare sketch proposal", "Child / Teacher", "FR024, FR025, FR030"),
    ("UC-020", "Moderate and review each sketch", "Teacher", "FR026, FR029, FR061"),
    ("UC-021", "Child views, hides or declines sketch", "Child", "FR027"),
    ("UC-022", "Gallery, presentation and scoped sharing", "Teacher / Child", "FR031, FR032, FR033"),
    ("UC-023", "Prepare knowledge/script and select/create video", "Teacher", "FR034, FR035, FR040"),
    ("UC-024", "Review exact video version before playback", "Teacher", "FR036"),
    ("UC-025", "Show true video-generation state and wait", "Teacher / Child", "FR037, FR038"),
    ("UC-026", "Choose disposition after video failure", "Teacher", "FR039"),
    ("UC-027", "Select/edit activity and confirm safety", "Teacher", "FR041, FR042, FR043"),
    ("UC-028", "Record off-screen participation and reflection", "Child / Teacher", "FR044"),
    ("UC-029", "Record age-aware descriptive observation", "Teacher", "FR045, FR049, FR050"),
    ("UC-030", "Persist history and portfolio", "Teacher", "FR047"),
    ("UC-031", "Report progress and export under permission", "Teacher", "FR046, FR048"),
    ("UC-032", "Monitor class dashboard and help queue", "Teacher", "FR051, FR054"),
    ("UC-033", "Use preset, automation and Teacher override", "Teacher", "FR052, FR053"),
    ("UC-034", "Provision, authorize and suspend accounts", "Super Admin", "FR055, FR058"),
    ("UC-035", "Author, review, publish and recall content", "Teacher / Super Admin", "FR056, FR062"),
    ("UC-036", "Version AI policy/configuration", "Super Admin", "FR056"),
    ("UC-037", "Monitor, audit and handle scoped incidents", "Authorized Super Admin", "FR057"),
    ("UC-038", "Retention, export/delete request and verify purge", "Authorized actor / Admin", "FR059, FR064"),
]

ENTITIES = [
    ("OrganizationScope", "School boundary, identity and policy reference", "A pilot target covers one school; the wider tenant topology is not frozen."),
    ("AdultAccount", "Adult identity, role and status", "Verified identity is separate from client-supplied role claims."),
    ("StudentProfile", "Managed alias, adult-confirmed age and policy", "Not a separate child login; do not infer age from artwork."),
    ("TeacherAssignment", "Teacher/class scope and validity", "Every Teacher action checks the current assignment."),
    ("Class / Enrollment", "School class, profile membership and validity", "Enrollment does not create legal-representative consent."),
    ("ConsentRecord", "Subject, representative evidence, purpose and policy version", "School-mediated; evidence and authority verification remain open."),
    ("ClassroomSession", "Class/topic, preset version, revision and lifecycle", "Teacher controls stage; close only after durable outcome handling."),
    ("SessionGroup / Membership", "Independent progress and participant history", "Move/leave must preserve contribution history."),
    ("ChildParticipant", "Managed profile admitted to one session", "The pilot does not add anonymous guest participants."),
    ("DeviceConnection", "Device, participant capability and connection state", "One shared device may have several participants; contributor is explicit."),
    ("CanvasDocument / Region", "Personal/shared scope, epoch and region permissions", "Server enforces edits and locks; UI state alone is not authority."),
    ("CanvasOperation", "Operation, principal, contributor, device and sequence", "Principal proves authority; contributor records the selected author context."),
    ("CanvasSnapshot", "Immutable revision, hash, watermark and provenance", "AI and portfolio reference source versions rather than overwrite them."),
    ("ArtworkShare", "Teacher-selected snapshot, order and audience scope", "No public gallery by default."),
    ("VisionObservation / MeaningConfirmation", "Candidates, uncertainty, source context and correction", "AI observation and confirmed child/Teacher meaning stay distinct."),
    ("AssistanceRequest / SketchProposal", "Explicit trigger, support level, result version and safety", "Suggestion is a derivative; Teacher review gates Child visibility."),
    ("TeacherReview / ChildResponse", "Exact content version, reviewer decision and view/hide/decline", "A child can decline without losing access to drawing."),
    ("KnowledgeBundle / VideoJob / ReviewedVideo", "Sources, script, generation attempt, status and artifact hash", "Only the exact approved version may play; failed jobs require a Teacher decision."),
    ("ActivityDefinition / Assignment", "Reviewed version, age, materials, steps and safety", "Teacher edits and class/group assignment keep provenance."),
    ("ObservationRecord / ReflectionRecord", "Evidence, context, author and descriptive outcome", "Not observed is not interpreted as a lack of ability."),
    ("PortfolioEntry", "Evidence references, attribution and approved summary", "Lineage distinguishes direct work, observation and AI output."),
    ("PresetVersion / ContentPublication", "Effective settings and publication/recall state", "Changes create versions; recalled content is excluded from new sessions."),
    ("AuditEvent / RetentionPolicy", "Actor/purpose/action plus data-class lifecycle", "Audit excludes raw media and credentials; class-specific durations remain open."),
]

RISK_ROWS = [
    ("R-01", "UI-to-service integration remains incomplete", "Classroom workflow stops at fixtures/stubs or mismatched API contracts.", "Freeze versioned contracts; integrate and evidence one workflow at a time.", "Đạt; Bảo", "Before staged workflow acceptance"),
    ("R-02", "Migration graph has multiple schema roots", "Fresh environments may not reproduce the same schema or safe upgrade order.", "Approve module ownership/order; rehearse each supported head on an empty disposable database.", "Khoa", "Before staging"),
    ("R-03", "Consent and data lifecycle are not fully operationalized", "Child processing, deletion or retention may be blocked or incomplete.", "Keep fail-closed behavior; agree purpose catalogue, copy inventory and purge evidence before any pilot.", "Đạt; Khoa", "Before child-data pilot"),
    ("R-04", "Modal profile is incomplete", "Model quality, latency, cost and capacity cannot be claimed.", "Record endpoint/model/GPU/region/scale/timeout/budget, then run bounded synthetic acceptance.", "Hiếu", "Before AI acceptance"),
    ("R-05", "No full staging/E2E evidence", "Cross-surface defects may be found late; class-size target is unproven.", "Build repeatable synthetic data, workflow scripts and recovery/load checks in isolated staging.", "Đạt; all", "W12-W13 proposal"),
    ("R-06", "Age/safety review workload", "Content or tool may be unsuitable for an age band or classroom setting.", "Use age-banded review, Teacher gate, safety checklist and explicit reject/recall path.", "Hiếu; Bảo", "Before content release"),
    ("R-07", "Scope and calendar remain unsettled", "Estimate variance and course-gate risk cannot be compared to fixed dates.", "Confirm official class/code/calendar and available capacity at weekly review.", "Đạt; supervisor", "At Review 2"),
    ("R-08", "State and ownership contracts differ across modules", "Stale jobs or UI transitions may report false readiness or overwrite attribution.", "Publish state registry, transition owner and contract-negative tests before integration.", "Khoa; Hiếu", "Before integration freeze"),
]

MANAGEMENT_EXTRA = [
    ("Process", "Feature-based iterative delivery: backlog item → testable acceptance → feature plan/approval → vertical slice → review/CI → integration evidence → weekly adaptation. This is not a declaration of formal Scrum."),
    ("Scope baseline", "The supplied registration v1.2 is the authority. A requirement change updates its linked SRS, SDD, tests, schedule and BM01; after Review 2, scope is frozen by the course commitment."),
    ("Estimate method", "The 252 person-day WBS is a bottom-up planning proposal using relative complexity and task decomposition. It excludes no hidden vendor spend and is not a time sheet; team capacity and calendar dates were not supplied."),
    ("Schedule method", "15 relative weeks use the SEP490 phase sequence inside September 2026–March 2027. Dependencies are gates, not dates; the official course calendar must be inserted before the baseline is approved."),
    ("Exit gates", "Do not enter staging until contracts and migration order are agreed. Do not use child data until school-mediated consent, purpose, retention, deletion and research controls are approved. Do not claim AI acceptance before the Modal profile and tests exist."),
    ("Quality ownership", "Requirement owner writes acceptance criteria; feature owner supplies unit/contract evidence; integrator checks cross-surface behavior; team reviews CI weekly. Blocked evidence is recorded as blocked rather than passed."),
    ("Capacity and cost", "Availability by member, paid service budget and Modal spending cap are TBD. No paid provider call or production spend is included in this estimate."),
]

EXCEPTION_ROWS = [
    ("Join", "Wrong/expired code, wrong class, duplicate admission, revoked assignment or pending consent", "Deny without creating access; return safe typed reason; record scoped audit event."),
    ("Drawing", "Duplicate idempotency key with different body, stale epoch or unauthorized region", "Reject; do not mutate the accepted canvas; client reloads current checkpoint."),
    ("Reconnect", "Lost acknowledgement or sequence gap", "Return durable checkpoint/sequence; replay only unacknowledged operations; deduplicate by key."),
    ("AI request", "Purpose revoked, stale source, rate limit or provider unavailable", "Do not start or accept stale work; preserve source snapshot; report typed pending/failure state."),
    ("AI result", "Unsafe or malformed output, uncertain meaning or stale completion", "Quarantine or reject result; never expose to Child before exact Teacher review."),
    ("Video", "Generation retry budget exhausted", "Teacher explicitly chooses retry, skip or early end; skip is not recorded as successful playback."),
    ("Session close", "Durable save/outbox/persistence failure", "Do not report Completed; retain recovery action and truthful incomplete outcome."),
    ("Group transfer", "Member moves while operations are pending", "Revoke old capability, checkpoint, preserve attribution/history, issue new scoped membership."),
    ("Data request", "Deletion/export spans shared artifact or provider copy", "Track each copy and dependency; protect other contributors; record incomplete external purge."),
    ("Admin access", "Role is valid but purpose/resource scope is absent", "Deny data access; administrative role alone is not consent or authority to read child content."),
]

TECH_ROWS = [
    ("Child Android", "apps/child-ui; Expo SDK 55, React Native 0.83.10, React 19", "Current UI prototype; API client/session verifier use local stub/fixture. No connected backend flow is established."),
    ("Teacher Desktop", "apps/teacher-ui; React/TypeScript/Vite family", "Current screens and service modules use fixtures; runtime and final browser packaging are not accepted."),
    ("Super Admin", "apps/admin-ui; React/TypeScript/Vite family", "Current sign-in returns a mock token; production identity and service integration are not established."),
    ("Backend", "Python 3.12 project; FastAPI, Pydantic, SQLAlchemy and Alembic", "Durable BE1 routes/adapters exist alongside legacy/demo composition. Database availability is required for BE1 readiness."),
    ("Database", "PostgreSQL; module-owned Alembic schemas", "BE1/core/BE2/module schemas have separate roots; release migration order remains open."),
    ("Adult identity", "Firebase Authentication", "Authentication only; authorization and child/class scope are backend-owned. Firebase data products are prohibited."),
    ("AI hosting", "Modal selected by owner", "Application/environment, endpoint, model, GPU, region, scale, timeout, secrets and spending cap TBD; no product endpoint or latency measurement."),
    ("Artifact storage / queue", "Filesystem/local adapters and job/outbox slices are present", "Staging/production object store, queue topology, copy inventory and rollback procedure are TBD."),
    ("Source and CI", "GitHub, feature branches, local dev and repository CI/configuration", "Local dev is 726 commits ahead of origin and has uncommitted files; review-2 tag does not exist."),
    ("AI-assisted work", "Codex/ChatGPT for requirements, design, coding/document drafting and review assistance", "Members remain accountable; synthetic data only; generated output is reviewed/tested before adoption."),
]

API_FAMILIES = [
    ("Identity / adult scope", "Verify adult token; derive principal and scoped assignments", "Firebase Authentication adapter + BE1 HTTP boundary", "Live Firebase project verification not evidenced"),
    ("Class/profile/enrollment", "Create/read assigned class, managed profile and enrollment", "BE1 durable routes / PostgreSQL models", "Consent and age-policy gates remain bounded"),
    ("Session / group", "Configure, admit, control stages, move members and close", "Versioned BE1 commands and persistence", "Target UI not fully connected"),
    ("Device / contributor", "Issue scoped device grant and explicit turn/contributor context", "BE1 device grants and durable canvas contract", "Must preserve principal/contributor distinction"),
    ("Canvas / snapshots", "Submit idempotent operation, checkpoint, snapshot and recover", "Core persistence ports, receipts and outbox", "Cross-surface realtime contract still needs acceptance"),
    ("AI jobs", "Create job, claim attempt, record command/result and reject stale completion", "BE2 job/attempt/receipt schema and adapter ports", "Provider integration/profile not deployed"),
    ("Knowledge / video", "Prepare content, report generation state, review exact version and disposition failure", "Separate content/video modules and schemas", "Composition and end-to-end video acceptance open"),
    ("Activity / learning record", "Assign reviewed activity; record reflection, observation and portfolio evidence", "Module schemas and feature services", "Cross-system UI and retention evidence incomplete"),
    ("Governance / data request", "Consent, audit, retention, export/delete and incident controls", "BE1 lifecycle records plus separate policy/copy schemas", "Purpose catalogue and external-copy completion policy TBD"),
    ("Realtime/events", "Versioned outbox/event and future collaborative updates", "Application-owned contract; no implicit DB coupling", "Full event delivery topology and retry targets TBD"),
]

STATE_TRANSITIONS = {
    "ClassroomSession": [
        ("Draft", "Lobby", "Teacher configures valid session"), ("Lobby", "Active", "Teacher explicitly starts"),
        ("Active", "Paused", "Teacher pauses"), ("Paused", "Active", "Teacher resumes"),
        ("Active", "Completed", "Teacher closes after save"), ("Active", "EndedEarly", "Teacher ends early"),
        ("Paused", "EndedEarly", "Teacher ends early"),
    ],
    "ParticipantMembership": [
        ("PendingRequest", "Admitted", "Teacher verifies roster"), ("Admitted", "GroupAssigned", "Teacher assigns group"),
        ("GroupAssigned", "Active", "Session starts"), ("Active", "MovedOrLeft", "Teacher moves or child leaves"),
        ("Active", "Revoked", "Assignment/enrollment/consent policy revokes access"),
        ("MovedOrLeft", "Active", "Teacher re-admits under current scope"),
    ],
    "AIJob": [
        ("queued", "running", "Worker claims job"), ("running", "succeeded", "Typed result accepted"),
        ("running", "failed_retryable", "Transient failure"), ("failed_retryable", "running", "Retry is eligible"),
        ("failed_retryable", "failed_exhausted", "Retry budget exhausted"), ("running", "blocked_unsafe", "Safety policy blocks output"),
        ("queued", "cancelled", "Authorized cancellation"), ("running", "cancelled", "Cancellation wins before result commit"),
    ],
    "VideoReview": [
        ("Draft", "Generating", "Teacher requests generation"), ("Generating", "ReadyForReview", "Generation succeeds"),
        ("ReadyForReview", "Approved", "Teacher approves exact version"), ("Approved", "Playing", "Teacher starts playback"),
        ("Generating", "Failed", "Retry budget exhausted"), ("Failed", "Generating", "Teacher explicitly retries"),
        ("Failed", "SkippedByTeacher", "Teacher explicitly skips"), ("Failed", "EndedEarly", "Teacher ends session"),
    ],
}


def test_case_rows():
    rows = []
    def add(trace, case, actor, setup, expected, owner, method="Automated target"):
        rows.append((f"TC-{len(rows)+1:03d}", trace, f"{case} ({actor}; owner {owner})", setup, expected, method, "Not run"))
    feature_cases = [
        ("MF-01 / FR002/004", "Valid roster join", "Teacher, Child", "Active enrollment, valid code, effective policy", "Member becomes admitted once; safe result is visible to both surfaces", "Khoa"),
        ("MF-01 / FR002", "Invalid/expired join code", "Child", "Code expired or belongs to another class", "Denied; no membership/grant is written", "Khoa"),
        ("MF-01 / FR001/006", "Unauthorized or pending-consent join", "Child, Teacher", "Role, class assignment or effective consent check fails", "Access denied; no child resource is served; audit is scoped", "Khoa"),
        ("MF-02 / FR007-013", "Teacher starts and controls a session", "Teacher, Child", "Configured session is in Lobby", "Only explicit Teacher action changes lifecycle; state persists", "Khoa"),
        ("MF-02 / FR009", "Groups progress independently", "Teacher, Child", "Two groups are active; one reports Ready", "Shared class stage does not auto-advance; other group continues", "Khoa"),
        ("MF-02 / FR010/013", "Invalid stage transition is rejected", "Child or unauthorized adult", "Wrong role or expected revision is supplied", "No state change; safe conflict/authorization response", "Khoa"),
        ("MF-03 / FR014-021", "Personal and shared drawing", "Child, Teacher", "Admitted member has permitted canvas", "Accepted operations update the correct scope and sequence", "Bảo"),
        ("MF-03 / FR003/066", "Turn attribution is immutable", "Two children on shared device", "Teacher changes selected contributor between operations", "New operation uses new contributor; prior attribution is unchanged", "Bảo"),
        ("MF-03 / FR017/060", "Reconnect restores acknowledged work once", "Child, Backend", "Disconnect after a persisted acknowledgement", "Checkpoint and sequence recover; no duplicate operation", "Bảo"),
        ("MF-04 / FR022-030", "Teacher approves exact AI proposal", "Child, Teacher, Worker", "Synthetic safe result refers to current source snapshot", "Only exact approved version becomes visible; source remains unchanged", "Hiếu"),
        ("MF-04 / FR026/029/061", "Unsafe or stale proposal is blocked", "Worker, Teacher, Child", "Result is unsafe or source version is stale", "Never served to Child; status and decision remain traceable", "Hiếu"),
        ("MF-04 / FR027/028", "Child hides or declines proposal", "Child", "Teacher-approved version is available", "Child choice is stored; drawing continues unchanged", "Hiếu"),
        ("MF-05 / FR034-040", "Exact reviewed video plays", "Teacher, Child, Worker", "Version is ready and approved", "Teacher starts exact version; playback is recorded truthfully", "Hiếu"),
        ("MF-05 / FR037-039", "Exhausted video failure has explicit disposition", "Teacher", "Retry budget is exhausted", "Teacher chooses retry, skip or end; no automatic success/skip", "Hiếu"),
        ("MF-05 / FR036/040", "Edited/recalled version cannot reuse stale approval", "Teacher, Child", "Underlying content version changes or is recalled", "Old review does not authorize changed content or new audience", "Hiếu"),
        ("MF-06 / FR041-044", "Teacher assigns reviewed activity", "Teacher, Child", "Activity version is suitable and reviewed", "Class/group assignment starts with safety/material context", "Đạt"),
        ("MF-06 / FR045-050", "Observation is descriptive and evidence-linked", "Teacher", "Observation includes context and evidence", "Portfolio keeps attribution; no peer ranking or diagnosis is created", "Đạt"),
        ("MF-06 / FR047/059/064", "Data request preserves lineage and audit", "Authorized Teacher/Admin", "Synthetic records include a shared artifact and derived copy", "Each in-scope copy disposition is tracked; unrelated child data stays scoped", "Đạt"),
    ]
    for x in feature_cases: add(*x)
    workflow_cases = [
        ("WF-01", "Prepare and admit class session end-to-end", "Teacher, Child, Backend", "Synthetic class, profile and code", "Active session and admitted membership are durable", "Khoa"),
        ("WF-02", "Draw, change turn and recover", "Child, Teacher, Backend", "Two synthetic clients and shared canvas", "Accepted operations and attribution survive reconnect", "Bảo"),
        ("WF-03", "Request, review and respond to sketch", "Child, Teacher, AI worker", "Synthetic snapshot and fixture result", "Teacher review gates Child access; hide/decline recorded", "Hiếu"),
        ("WF-04", "Review media, run activity and close", "Teacher, Child, Backend", "Reviewed content and synthetic activity", "Outcome saves before completed state; exceptions remain truthful", "Đạt"),
    ]
    for x in workflow_cases: add(*x, method="Automated E2E target")
    for entity, transitions in STATE_TRANSITIONS.items():
        for source, target, trigger in transitions:
            owner = "Khoa" if entity in ("ClassroomSession", "ParticipantMembership") else "Hiếu"
            add(f"STATE / {entity}", f"Legal transition {source} → {target}", "Authorized actor / worker", f"Entity is {source}; trigger: {trigger}", f"Transition to {target} occurs once and is versioned/audited", owner)
    for entity in STATE_TRANSITIONS:
        owner = "Khoa" if entity in ("ClassroomSession", "ParticipantMembership") else "Hiếu"
        add(f"STATE / {entity}", "Illegal transition is rejected", "Unauthorized or stale caller", f"Entity is in a state with no matching legal transition", "State is unchanged; typed denial/conflict is returned and recorded", owner)
    nfr_cases = [
        ("NFR-01", "Accepted operation acknowledgement p95 ≤500 ms at 40 synthetic clients", "Backend / Child", "Isolated load fixture; timer starts at submit and ends at durable acknowledgement", "Measured p95 meets candidate threshold; no claimed result until run", "Khoa"),
        ("NFR-02", "Accepted peer update visible p95 ≤1 s at 40 synthetic clients", "Child clients", "Two or more isolated clients, same accepted sequence", "Measured p95 meets candidate threshold; no claimed result until run", "Bảo"),
        ("NFR-03", "Authorization negative suite denies 100% and leaks zero records", "All roles", "Cross-class, wrong purpose, revoked grant and forged role fixtures", "Every unauthorized request denied; response contains no protected record", "Khoa"),
        ("NFR-04", "Every acknowledged operation restores exactly once", "Child / Backend", "Restart and reconnect after durable receipt; unique operation IDs", "No acknowledged op lost or duplicated; RPO/RTO remain TBD until approved", "Bảo"),
        ("NFR-05", "Zero pending/stale/unsafe/unapproved content served to Child", "AI and content services", "Negative result/review/version fixture suite", "Zero forbidden content reaches Child surface", "Hiếu"),
        ("NFR-06", "Session/artwork data purge completes by 90 days after session end", "Lifecycle worker / Admin", "Clock-controlled synthetic lifecycle and copy inventory", "Eligible records/copies are purged or explicit external exception is audited", "Đạt"),
    ]
    for x in nfr_cases: add(*x, method="Automated measurement target")
    assert len(rows) == 61, len(rows)
    return rows


def migration_inventory():
    rows = []
    pattern = re.compile(r"op\.create_table\(\s*['\"]([^'\"]+)['\"]", re.S)
    rev_pattern = re.compile(r"^revision\s*=\s*['\"]([^'\"]+)", re.M)
    down_pattern = re.compile(r"^down_revision\s*=\s*(.+)$", re.M)
    family_pattern = re.compile(r"_(core|be1|ai|ap|lc|kv|vr|ae|pa|vf)_")
    for path in sorted((ROOT / "backend/alembic/versions").glob("*.py")):
        raw = path.read_text(encoding="utf-8")
        rev = rev_pattern.search(raw)
        down = down_pattern.search(raw)
        tables = pattern.findall(raw)
        if not rev:
            continue
        family = family_pattern.search(path.name)
        module = family.group(1) if family else "module"
        rows.append((module, path.name, rev.group(1), (down.group(1).strip() if down else ""), ", ".join(tables) or "No direct create_table call"))
    return rows


def clear_table_rows(table):
    for row in list(table.rows)[1:]:
        table._tbl.remove(row._tr)


def replace_table_rows(table, headers, rows, widths=None, size=8.0):
    clear_table_rows(table)
    for i, value in enumerate(headers):
        set_cell(table.rows[0].cells[i], value, bold=True, color=WHITE, size=size)
        shade(table.rows[0].cells[i], NAVY)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell(cells[i], value, size=size)
    format_table(table, widths, size)


def add_report1(doc):
    ref = ref_heading(doc, "II. Project Management Plan")
    add_heading_before(ref, "7. Stakeholders and Classroom Setting", 2, page_break=True)
    add_para_before(ref, "The primary setting is a teacher-led classroom pilot at one school, with one class targeting up to 40 unique admitted children. The number 40 is a product planning target, not a measured load limit. A connected device may serve more than one participant, so the capacity measure is unique admitted children, not sockets or tablets.")
    add_table_before(doc, ref, ["Stakeholder", "Need", "Decision / boundary"], [
        ("Child participant", "Express an idea, draw alone or together, request optional support, explore reviewed media and do an off-screen activity.", "Uses a Teacher-managed profile; no independent login; may hide or decline an AI suggestion."),
        ("Teacher", "Prepare class, manage groups and pace, review content and observe learning.", "Acts only within current school/class assignment; final review and session decisions remain explicit."),
        ("School / representative", "Collect and govern legal-representative permission and classroom participation.", "School collects consent; authorized Teacher/Admin records evidence and purpose; jurisdiction and verification process remain open."),
        ("Super Admin", "Manage adult accounts, policies, approved content, data requests and service health.", "Administrative role alone does not authorize reading child content or establish consent."),
        ("AI/media workers", "Prepare typed candidate analysis or media derivatives.", "Backend-owned service; outputs are untrusted until validation and exact Teacher review."),
    ], [1.15, 2.45, 2.8], 8.4)
    add_heading_before(ref, "8. Product Boundary and Success Evidence", 2)
    add_para_before(ref, "The product combines three surfaces and one backend boundary: Child Android, Teacher Desktop, Super Admin Console, and a FastAPI modular backend. The product succeeds only when a complete classroom workflow preserves child agency, contribution history, age-appropriate review, durable state and off-screen learning. A screen mock, endpoint inventory, local unit test or AI output alone does not prove the workflow.")
    add_table_before(doc, ref, ["Outcome", "Evidence required before claiming it"], [
        ("Classroom participation", "Valid managed-profile admission, teacher-controlled group/session transitions, and denial of wrong-class or unauthorized requests."),
        ("Creative collaboration", "Accepted operations have durable receipts, correct contributor context, replay/reconnect behavior and no silent overwrite."),
        ("Safe AI assistance", "Pinned source, typed result, safety/freshness checks, exact-version Teacher review and recorded Child choice."),
        ("Reviewed learning", "Exact knowledge/video and activity versions have review, audience, failure disposition and outcome lineage."),
        ("Responsible data handling", "Effective purpose checks, scoped access, audit, class-specific retention, export/delete and copy/purge evidence."),
    ], [1.7, 4.7], 8.4)


def add_report2(doc):
    import sys
    sys.path.insert(0, str(FEATURE / "src"))
    from report2_data import WBS_ROWS, SCHEDULE_ROWS, DELIVERABLE_ROWS, RACI_ROWS, TRAINING_ROWS, COMMUNICATION_ROWS, TOOLS_ROWS, TOTAL_EFFORT
    ref = ref_heading(doc, "III. Software Requirements Specification")
    add_heading_before(ref, "7. Detailed Work Breakdown and Estimate", 2, page_break=True)
    add_para_before(ref, f"The WBS decomposes the registered product into implementable packages. The estimate totals {TOTAL_EFFORT} preliminary person-days. Category totals are planning allocations, not actual effort or confirmed capacity. Complexity guides refinement; the owner and team must re-estimate from available hours and accepted contracts before baselining.")
    wbs = [(code, name, complexity or "Work package subtotal", f"{days} person-days") for code, name, complexity, days in WBS_ROWS]
    wbs.append(("TOTAL", "All product work packages", "Proposed baseline", f"{TOTAL_EFFORT} person-days"))
    add_table_before(doc, ref, ["WBS", "Work package", "Complexity", "Effort"], wbs, [0.5, 3.0, 1.35, 1.15], 7.8)
    add_heading_before(ref, "8. Relative Schedule, Dependencies and Gates", 2, page_break=True)
    add_para_before(ref, "The 15-week sequence follows the school sample's phases. It is relative to kickoff within the registered September 2026–March 2027 envelope. Exact dates, course milestones and member availability were not supplied; every window remains a proposal until the supervisor confirms the calendar.")
    schedule = [(a, b, c, d, e, f) for a, b, c, d, e, f in SCHEDULE_ROWS]
    add_table_before(doc, ref, ["Window", "Stage", "Depends on", "Lead", "Output gate", "Current status"], schedule, [0.65, 1.0, 0.85, 0.75, 1.35, 1.55], 7.0)
    add_heading_before(ref, "9. Deliverable Register", 2)
    add_table_before(doc, ref, ["No.", "Deliverable", "Window", "Status / evidence boundary"], DELIVERABLE_ROWS, [0.4, 2.0, 0.65, 3.2], 7.7)
    add_heading_before(ref, "10. Risk Register and Response", 2, page_break=True)
    add_table_before(doc, ref, ["ID", "Risk", "Effect", "Response", "Owner", "Gate"], RISK_ROWS, [0.4, 0.9, 1.0, 1.65, 0.75, 1.25], 7.2)
    add_heading_before(ref, "11. Process, Quality and Team Communication", 2)
    add_table_before(doc, ref, ["Control", "Project rule"], MANAGEMENT_EXTRA, [1.25, 4.95], 8.0)
    comm = [(a, b, c, d, e) for a, b, c, d, e in COMMUNICATION_ROWS]
    add_table_before(doc, ref, ["Event", "Participants", "Purpose", "Cadence", "Record"], comm, [0.9, 1.0, 1.75, 0.7, 1.8], 7.0)
    add_heading_before(ref, "12. Training and Responsibility Assignments", 2)
    add_table_before(doc, ref, ["Training", "Participants", "Window", "Completion evidence"], TRAINING_ROWS, [1.5, 1.1, 0.75, 2.4], 7.6)
    add_table_before(doc, ref, ["Work / workflow", "Đạt", "Hiếu", "Bảo", "Khoa"], RACI_ROWS, [3.45, 0.55, 0.55, 0.55, 0.55], 7.4)
    add_heading_before(ref, "13. Configuration, Tools and Deployment Controls", 2)
    add_table_before(doc, ref, ["Area", "Current declaration and limitation"], TOOLS_ROWS, [1.2, 4.95], 7.8)


def add_report3(doc):
    ref = ref_heading(doc, "IV. Software Design Description")
    for table in doc.tables:
        header = [c.text.strip() for c in table.rows[0].cells]
        if len(header) >= 4 and header[0] == "ID" and header[1].lower().startswith("use case"):
            table._tbl.getparent().remove(table._tbl)
            break
    rename = {
        "UC01 Prepare and admit": "UC-004 and UC-007 Prepare and admit",
        "UC02 Collaborative drawing": "UC-008 and UC-013 Collaborative drawing",
        "UC05 Review an AI sketch": "UC-019 and UC-020 Review an AI sketch",
        "UC08 Resolve failed video": "UC-026 Resolve failed video",
        "UC10 Recover a session": "UC-016 Recover session and canvas",
        "UC12 Handle data request": "UC-038 Handle a data request",
    }
    for p in doc.paragraphs:
        if p.text in rename:
            p.text = rename[p.text]
    add_heading_before(ref, "5. Complete Product Module and Actor Model", 2, page_break=True)
    add_table_before(doc, ref, ["ID", "Module", "Responsibility and rules"], MODULES, [0.5, 1.65, 4.05], 7.9)
    add_heading_before(ref, "6. Full Use Case Catalog UC-001 to UC-038", 2, page_break=True)
    add_para_before(ref, "The catalog retains the full SRS v3.1 scope. A use case identifies the main actor and the functional requirements it elaborates; actor role never grants data access without resource, purpose and current assignment checks. Phase 2 cases remain identified as deferred rather than silently included in the pilot.")
    uc_rows = [(id_, name, actor, fr) for id_, name, actor, fr in USE_CASES]
    add_table_before(doc, ref, ["ID", "Use case", "Primary actor", "Requirement trace"], uc_rows, [0.55, 2.2, 1.2, 2.2], 7.3)
    add_heading_before(ref, "7. Logical Data Dictionary and Invariants", 2, page_break=True)
    add_para_before(ref, "The logical model below is the target domain view from SRS v3.1. It is not a claim that every entity has already been migrated. Report 4 maps each logical area to current module schemas and flags opaque identifiers, missing deployment order and future entities.")
    add_table_before(doc, ref, ["Logical entity", "Key concepts", "Invariant / relationship"], ENTITIES, [1.3, 2.1, 2.75], 7.1)
    add_heading_before(ref, "8. Business Rules and Authorization", 2, page_break=True)
    rules = [
        ("BR-01", "The Child has a Teacher-managed profile and no independent login."),
        ("BR-02", "Adult identity is verified by the backend; client role or class claims are never trusted."),
        ("BR-03", "A Teacher action is constrained by a current school/class assignment and resource scope."),
        ("BR-04", "Enrollment is not consent. The school collects legal-representative consent; authorized roles record evidence and allowed purpose."),
        ("BR-05", "Teacher controls session stages and each group's progress remains independent."),
        ("BR-06", "Verified principal and selected contributor are separate; turn changes apply only to new operations."),
        ("BR-07", "Original drawings are immutable; AI proposals, snapshots, edits and shared outputs are separately versioned with provenance."),
        ("BR-08", "No Child sees a pending, unsafe, stale, recalled or unreviewed AI/media version."),
        ("BR-09", "Teacher approval binds the exact content hash/version; editing invalidates prior review."),
        ("BR-10", "After video failure the Teacher explicitly retries, skips or ends; a skip is not successful playback."),
        ("BR-11", "Observation records describe observed context; absence of evidence is not an ability judgment."),
        ("BR-12", "A completion result requires a durable persistence confirmation; queued work or local draft is not completion."),
        ("BR-13", "The school pilot target is up to 40 unique admitted children; device count does not define capacity."),
        ("BR-14", "Session and artwork default retention is 90 days after session end; other data classes need separate policy."),
    ]
    add_table_before(doc, ref, ["Rule", "Normative behavior"], rules, [0.6, 5.55], 8.0)
    add_heading_before(ref, "9. Exceptions and Recovery Outcomes", 2, page_break=True)
    add_table_before(doc, ref, ["Flow", "Failure or exception", "Required system outcome"], EXCEPTION_ROWS, [0.9, 2.2, 3.05], 7.4)


def add_report4(doc, rendered):
    ref = ref_heading(doc, "V. Software Testing Documentation")
    add_heading_before(ref, "5. Current, Target and Integration Architecture", 2, page_break=True)
    add_para_before(ref, "ADR-0019 records the owner-selected classroom-first durable runtime as the target product composition. The current checkout is not yet that finished product: BE1 persistence is present, but the HTTP app still includes legacy/demo routers, and the current three UI clients use fixtures or stubs. The diagram uses dashed links for proposed or unverified integration. Separate demo composition is a design target, not a claim that the cleanup has already been implemented.")
    add_table_before(doc, ref, ["Boundary", "Current source", "Target and constraint"], [
        ("Client surfaces", "apps/child-ui, apps/teacher-ui, apps/admin-ui", "Android Child, Teacher Desktop and Super Admin remain separate; no current UI-to-service E2E is proven."),
        ("HTTP composition", "FastAPI routers include durable BE1 plus legacy/demo paths", "Classroom routes become the default product entrypoint; demo stores use separate composition."),
        ("Application/domain", "Use cases, policies, ports and versioned contracts exist in backend", "Dependencies point inward; framework/provider/storage rules stay outside domain."),
        ("Persistence", "PostgreSQL adapters and module-specific schemas/migrations", "Agree module heads, upgrade order, rollback and copy lifecycle before staging."),
        ("AI worker", "BE2 job/attempt/receipt slices and research adapters", "Backend owns calls, secrets, idempotency, retries, stale-result checks and review gate."),
        ("External identity", "Firebase Authentication adapter boundary", "Adult identity only; Firebase Storage/Firestore/Realtime Database are prohibited."),
        ("AI hosting", "Modal selected; no product deployment receipt", "Profile values must be supplied and tested; no GPU, latency or capacity claim."),
    ], [1.15, 2.25, 2.75], 7.7)
    add_heading_before(ref, "6. Technology, Third-Party Services and Environments", 2, page_break=True)
    add_table_before(doc, ref, ["Area", "Declared technology / service", "Purpose, data and state"], TECH_ROWS, [1.0, 2.35, 2.8], 7.4)
    add_para_before(ref, "No AI provider secret or endpoint belongs in a mobile app. Modal selection does not define a model license, GPU, region, scale, timeout, spending limit, endpoint shape or measured result. Firebase is authentication-only; use of Firebase data products is disallowed by repository policy. Dev is a local, unpushed checkout; staging and production hosts, secret injection, rollout and rollback are TBD.")
    add_heading_before(ref, "7. API, Event and Service Contract Families", 2, page_break=True)
    add_para_before(ref, "The BE1 contract inventory records 47 operations across 42 paths at its historical API snapshot. The current route composition receipt records 76 paths and 83 route/method pairs on a later uncommitted tree. These are inventories, not proof that every UI call is mounted, that every endpoint is production-ready, or that all product flows are connected.")
    add_table_before(doc, ref, ["Contract family", "Operations", "Current implementation boundary", "Open verification"], API_FAMILIES, [1.0, 1.7, 2.0, 1.5], 7.2)
    add_para_before(ref, "Every command should carry a versioned contract, authenticated principal, resource scope, request/operation ID and expected aggregate revision where applicable. Typed failures include authentication/authorization denial, validation, not found, conflict/stale version, consent not effective, policy block, provider unavailable and persistence failure. A worker completion is revalidated against source version and current purpose before commit.")
    add_heading_before(ref, "8. Logical Data Model and Physical Database Inventory", 2, page_break=True)
    add_para_before(ref, "The logical data dictionary in Report 3 is the target model. The current physical database is split into independently owned schema families. The migration register below is extracted from repository Alembic sources; it documents each revision and created tables so reviewers can compare the ERD with actual scripts. No cross-schema relationship is drawn as a physical foreign key unless the migration defines it.")
    inv = migration_inventory()
    add_table_before(doc, ref, ["Schema family", "Migration file", "Revision", "Parent revision", "Tables created"], inv, [0.65, 1.2, 0.9, 1.05, 2.4], 6.9)
    add_table_before(doc, ref, ["Logical area", "Current physical representation", "Known limitation"], [
        ("Class, adult, managed profile, enrollment, consent, session, group and lifecycle requests", "be1_core: be1_organizations, be1_adult_identities, be1_organization_assignments, be1_classrooms, be1_managed_profiles, be1_enrollments, be1_consent_records, be1_device_grants, be1_sessions, be1_session_memberships, be1_session_groups, be1_child_turns, be1_gallery_snapshots, be1_observations, be1_data_lifecycle_requests", "Current consent is fail-closed; class-specific retention/purge and representative verification are not fully accepted."),
        ("Canvas operation and durability", "core schema: aggregate revisions, operations, idempotency receipts, checkpoints, assets, audit, outbox and consumer receipts", "Durable core is a bounded slice; complete real-time/client integration is not established."),
        ("AI job lifecycle", "ai_jobs schema: job, attempt, command/result receipt and outbox records", "Session/group identifiers are opaque; no cross-schema foreign key is inferred."),
        ("Consent/copy lifecycle and content modules", "ap, lc, kv, vr, ae, pa and vf schema families with separate migration chains", "No single deploy order is approved; derived-copy/provider cleanup requires evidence."),
        ("Target entities not yet represented end-to-end", "Knowledge/story/portfolio, reviewed media, activity assignment, reporting and deletion can span isolated models/services", "Map each canonical entity and field to an approved migration before claiming ERD/script parity."),
    ], [1.25, 3.0, 1.95], 7.1)
    insert_image_before(doc, ref, rendered["D19_logical_domain_erd"], "Figure 14. Logical domain ERD; arrows show target relationships, while the physical FK subset is identified in the migration inventory and D07.")
    add_heading_before(ref, "9. Main State Models and Current Enum Mapping", 2, page_break=True)
    add_para_before(ref, "The diagrams D10–D13 describe the proposed classroom domain lifecycle. Current persisted values are reported separately so conceptual labels are not confused with wire enums. Before integration, each accepted command must map to one legal transition; all other transitions leave state unchanged and return a typed conflict or authorization error.")
    transition_rows = []
    for entity, items in STATE_TRANSITIONS.items():
        for src, dst, trigger in items:
            transition_rows.append((entity, f"{src} → {dst}", trigger, "Proposed; needs contract and transition test"))
    add_table_before(doc, ref, ["Aggregate", "Transition", "Trigger", "Verification status"], transition_rows, [1.0, 1.15, 2.35, 1.7], 7.0)
    add_table_before(doc, ref, ["State model", "Current code evidence", "Target reconciliation"], [
        ("Session", "Persisted BE1 wire state: configured, lobby, active, paused, finished.", "Diagram Draft/Lobby/Active/Paused/Completed/EndedEarly is a target. Map configured→Lobby, finished→Completed/EndedEarly only with persisted disposition; add explicit domain contract and tests."),
        ("Membership/admission", "BE1 has session membership, enrollment and device-grant states; admission is Teacher-controlled.", "Separate request, roster admission, group assignment, active membership, move/leave and revoke; avoid conflating profile, participant and device identity."),
        ("AI job", "BE2 job/attempt/receipt state machine is persisted in its module schema.", "A successful worker job is not an approved sketch. Safety, freshness and Teacher review remain separate states."),
        ("Video", "Separate knowledge, video, review and failure migrations exist.", "Generation, exact-version approval, playback and retry/skip/end stay distinct."),
    ], [0.95, 2.15, 2.8], 7.0)
    add_heading_before(ref, "10. Activity Diagrams for the Four Main Workflows", 2)
    add_para_before(ref, "The four workflow owners map to four end-to-end activity diagrams. The diagrams show actor participation and business outcomes without prescribing internal code-level algorithms. Editable Mermaid sources D15–D18 are kept in the repository next to D01–D14.")
    for i, (name, title, subtitle, *_rest) in enumerate(WORKFLOWS):
        insert_image_before(doc, ref, rendered[name], f"Figure {i+15}. {title}; proposal and current implementation boundaries are identified in the diagram and text.")
    add_heading_before(ref, "11. Security, Privacy and Data Lineage", 2, page_break=True)
    security = [
        ("Authentication", "Verify adult identity at the backend; client role claims are not authoritative."),
        ("Authorization", "Check actor, organization, class, session, group, artifact, purpose, current assignment and capability at each operation."),
        ("Child data", "Use synthetic data in development. No real child media, names, credentials, tokens or service-account files in source control or AI prompts."),
        ("Consent", "School collects representative consent; authorized users record evidence/purpose. Pending consent blocks child-data flows; enrollment is not consent."),
        ("AI boundary", "Mobile sends application requests only; provider credentials and provider-specific APIs remain backend-only. Validate untrusted output and stale versions."),
        ("Provenance", "Preserve original drawing; derived snapshot/proposal/media has immutable source reference, version, actor, reason, model/config and timestamp."),
        ("Retention and deletion", "90-day default applies to session/artwork after session end. Other data classes, backups, provider copies and exceptions need policy and purge evidence."),
        ("Audit and observability", "Record scoped decisions and safe correlation IDs. Do not log raw media, full prompts, tokens, signed URLs or provider headers."),
    ]
    add_table_before(doc, ref, ["Control", "Design requirement and current status"], security, [1.15, 5.05], 7.8)
    add_heading_before(ref, "12. Runtime, Rollback and Failure Handling", 2)
    add_para_before(ref, "Current deployment target, staging host, runtime secrets, network policy, object store, queue, database recovery point, backup/restore rehearsal, rolling upgrade and rollback command are not specified. Before a staging gate, document environment-specific configuration, health probes, migration preflight, backup verification, version rollback boundaries, queued-job disposition and provider fallback behavior. Never use an in-memory demo router as an automatic production fallback.")


def add_report5(doc):
    ref = ref_heading(doc, "VI. Project Tracking")
    for table in list(doc.tables):
        header = [c.text.strip().lower() for c in table.rows[0].cells]
        if header[:3] == ["id", "scenario", "pass condition"]:
            table._tbl.getparent().remove(table._tbl)
            break
    add_heading_before(ref, "6. Expanded Verification Strategy and Case Register", 2, page_break=True)
    add_para_before(ref, "The Review 2 minimum count is derived from the current proposal: six mandatory features × three cases (18), four main workflows × one end-to-end case (4), 29 legal transitions across four main state machines (29), four explicit illegal-transition rejection cases (4), and six measurable candidate NFRs (6), for 61 planned cases. At least 31 must be automated in CI to meet the 50% course threshold. This is a proposed test target, not a committed count of existing tests or a passing result.")
    add_table_before(doc, ref, ["Case ID", "Trace", "Scenario / actor / owner", "Setup and data", "Pass condition", "Execution", "Actual"], test_case_rows(), [0.45, 0.75, 1.35, 1.1, 1.6, 0.55, 0.4], 6.6)
    add_heading_before(ref, "7. Test Levels, Environments and Evidence", 2, page_break=True)
    test_levels = [
        ("Unit / domain", "State invariants, age/material rules, authorization policy, idempotency and error mapping", "Feature owner; synthetic fixtures", "Unit test receipt and trace IDs"),
        ("Adapter / persistence", "PostgreSQL transaction, migration, copy inventory, outbox and restart recovery", "Khoa / module owners; disposable database", "Migration heads and schema verification"),
        ("Contract", "OpenAPI/event schema, required fields, versioning, stale-revision and negative authorization", "Interface owners; generated synthetic requests", "Contract suite on each PR"),
        ("UI component", "Screen state, fixture boundaries, accessible controls and safe error presentation", "Bảo / UI owners; local fixtures", "Component/unit receipt; does not prove backend integration"),
        ("End-to-end", "Four main workflows including expected and exception cases across surfaces", "Đạt coordinates; all owners present", "Staging, exact commit, synthetic seed and replayable result"),
        ("Security/privacy", "Cross-class access denial, consent, purpose revocation, audit redaction, export/delete and retention", "Khoa / Đạt; isolated synthetic data", "Threat/control case evidence before pilot"),
        ("Performance/recovery", "40 unique synthetic participants, ack/update latency, reconnect, load shed and worker retry", "All owners; isolated provider-free profile first", "Measured p95, loss/duplication counts and resource limits"),
        ("AI quality/safety", "Pinned model/config, uncertainty, unsafe output, stale completion and Teacher gate", "Hiếu; approved Modal profile and synthetic fixtures", "Separate model-quality and workflow acceptance reports"),
    ]
    add_table_before(doc, ref, ["Level", "Coverage", "Owner / environment", "Evidence"], test_levels, [0.9, 2.2, 1.65, 1.45], 7.2)
    add_heading_before(ref, "8. Test Data, CI and Acceptance Thresholds", 2)
    add_para_before(ref, "Development and CI use synthetic child/class/session identifiers only. Staging requires disposable PostgreSQL, an agreed migration upgrade path, isolated artifact/queue services, deterministic AI adapters or a separately approved Modal profile, scoped adult test principals and reproducible session codes. Never use production or partner data in test fixtures.")
    add_table_before(doc, ref, ["Gate", "Proposed exit condition", "Current status"], [
        ("Functional count", "At least 61 committed functional cases; at least 31 automated in CI.", "Target only; IDs TC-001–TC-061 are not all implemented or run."),
        ("Main workflows", "100% of four agreed workflows complete end-to-end on staging.", "No full staging E2E receipt."),
        ("Exception scenarios", "All main cases and at least 80% of exception cases pass.", "Target only; no measured result."),
        ("Total pass rate", "At least 90% of committed cases pass; every mandatory feature main path passes.", "Target only; baseline not computed."),
        ("Defects", "No open Critical or High defect at Defense 1.1; all known gaps have owner/evidence.", "No consolidated defect register in this snapshot."),
        ("NFRs", "Run each agreed metric with fixed environment/profile and preserve raw result.", "Latency, recovery and 40-child capacity remain unmeasured."),
    ], [1.05, 2.85, 2.1], 7.6)
    add_heading_before(ref, "9. Historical Test Reports and Limits", 2, page_break=True)
    add_table_before(doc, ref, ["Receipt", "Historical result", "What it demonstrates", "What it does not demonstrate"], [
        ("FEAT-047 BE1 backend, 2026-10-15", "2,173 backend tests, six skipped; three PostgreSQL acceptance tests; local API smoke.", "Bounded durable BE1 tests, status/error contracts, consent fail-closed and persistence checks on that source snapshot.", "No full UI workflow, real Firebase project, staging, production or class pilot."),
        ("FEAT-057 offline BE2 seam, 2026-10-22", "Nine PostgreSQL-backed tests, zero failures/errors/skips on recorded bounded path.", "A narrow synthetic BE2-07 → BE1 → BE2-08 integration seam.", "No complete BE2 graph adoption, provider, deployed Modal endpoint or cross-surface acceptance."),
        ("FEAT-057 Modal CPU package, 2026-10-20", "296 tests; 2 CPU cores / 4 GiB; no GPU inference.", "Selected offline package tests ran on a Modal CPU environment in that receipt.", "No GPU endpoint, model quality, product latency/capacity or live app call."),
        ("FEAT-059 local cleanup, recorded earlier", "24 UI tests and 9 backend tests; route composition snapshot 76 paths / 83 operations.", "Bounded local structure-cleanup checks on a dirty working tree.", "No current clean tag, all-app test suite, staging E2E or post-merge production acceptance."),
    ], [1.1, 1.3, 1.8, 1.75], 7.1)
    add_para_before(ref, "The review-document task did not rerun application tests. Each receipt is historical, scoped to its recorded commit/environment, and must not be combined into a claim that the current branch passed the 61-case target.")


def add_tracking(doc):
    ref = None
    for p in reversed(doc.paragraphs):
        if p.style.name == "Heading 1" and p.text.strip() == "References":
            ref = p
            break
    if ref is None:
        ref = doc.add_paragraph("References", style="Heading 1")
        add_para_before(ref, "Current source and course authorities are listed here; branch/source and template originals remain unchanged.")
    add_heading_before(ref, "5. Current Workstream and Integration Status", 2, page_break=True)
    status = [
        ("Registration and SRS/SDD", "Draft documents trace v1.2 registration, SRS v3.1, 66 FR and 38 use cases.", "Review 2 decision and code/class confirmation remain pending.", "Đạt / all"),
        ("BE1 durable classroom foundation", "Versioned API contract, PostgreSQL persistence, classes/profiles/sessions/groups/turns and lifecycle records exist.", "Full product flow and all consent/retention policies are not complete.", "Khoa"),
        ("BE2 AI/media", "Job/attempt/receipt, content/video and worker-oriented module source exists in merged local dev.", "Deployment profile and complete cross-feature composition are not accepted.", "Hiếu"),
        ("Child Android", "apps/child-ui source is present (Expo SDK 55 / React Native 0.83.10).", "Local fixture session verification and stub API; no service integration evidence.", "Bảo"),
        ("Teacher Desktop", "UI and service source is present.", "Fixture-based modules; complete live classroom API path is not proven.", "Bảo / Đạt"),
        ("Super Admin Console", "UI source includes account/content/policy/audit/data-request views.", "Mock token/auth and fixture-backed paths are not production identity/integration.", "Đạt / Bảo"),
        ("Database deployment", "Nine module migration families/roots are represented in Alembic sources.", "Upgrade order, consolidated bootstrap, rollback and all-schema staging rehearsal are open.", "Khoa"),
        ("Modal / AI evaluation", "Owner selected Modal as intended AI host.", "App, endpoint, model, GPU, region, scale, timeout, budget and measured inference remain TBD.", "Hiếu"),
        ("Cross-surface verification", "Bounded historical receipts exist for BE1, a BE2 seam and cleanup.", "The 61-case target, full staging E2E, 40-client capacity and child pilot are not run.", "Đạt / all"),
    ]
    add_table_before(doc, ref, ["Workstream", "Present source evidence", "Open gate / limitation", "Owner"], status, [1.1, 1.9, 2.4, 0.75], 7.1)
    add_heading_before(ref, "6. Owner Decisions and Closure Conditions", 2, page_break=True)
    add_table_before(doc, ref, ["Decision / task", "Owner", "Required evidence", "Target window / due"], [
        ("Confirm class/project code and Review 2 registration disposition", "Đạt + supervisor", "Signed form or written correction; class/code no longer inferred.", "Before submission; calendar date TBD"),
        ("Agree versioned FE/UI ↔ backend contracts and select release UI baseline", "Bảo + Khoa + Đạt", "Contract version, mounted route list, integration receipt for each WF.", "W4-W7 proposal"),
        ("Approve classroom-first runtime composition and demo isolation", "Đạt + Khoa", "Feature approval, route inventory and regression receipt.", "Before staging"),
        ("Map logical entities/states to migrations and approve nine-head order", "Khoa + Hiếu", "Schema crosswalk, clean-database upgrade/rollback report.", "W4-W5 proposal"),
        ("Complete consent purpose, copy inventory, retention and deletion rules", "Đạt + Khoa + supervisor", "Policy version, fail-closed tests, purge evidence and school process.", "Before child-data pilot"),
        ("Provide Modal deployment and spending profile", "Hiếu + owner", "Model/GPU/endpoint/region/scale/timeouts/secrets/budget and synthetic acceptance.", "Before AI acceptance"),
        ("Complete 61 case target, CI coverage and staging E2E", "All; Đạt coordinates", "31+ automated, 100% main workflow gates, defect register and NFR measurements.", "W12-W13 proposal"),
        ("Create and verify Review 2 tag after approval", "Đạt / release owner", "Course-approved SHA, security scan receipt, tag points to exact clean commit.", "After Review 2 decision"),
    ], [1.9, 1.1, 2.2, 1.0], 7.2)
    add_heading_before(ref, "7. Branch, Change and Evidence Record", 2)
    add_para_before(ref, "Document source baseline: local dev@0a7ce768c153f2104cff930569c3eda6e484532c, including refreshed origin/FE_UI_Child@ca3779869dfc1385cbbc7b8ca730f780386af7b2. The local branch is 726 commits ahead of origin/dev and has uncommitted user changes, including FEAT-059 cleanup. This document is not a tagged release, has not been pushed, and does not create the review-2 tag. Individual merge commits and branch snapshot evidence are preserved under evidence/notes/BRANCH_MERGE_RESULT_20261023.md.")
    add_para_before(ref, "Record changes only through feature plans, decisions, approvals, commit evidence, migration receipts and rendered dossier revisions. The course's review-2 tag and Report 5 test results remain release gates; generated reports cannot replace code, SQL, CI or test evidence.")


def add_references(doc):
    h = next((p for p in doc.paragraphs if p.style.name == "Heading 1" and p.text.strip() == "References"), None)
    if h is None:
        h = doc.add_paragraph("References", style="Heading 1")
    refs = [
        "[1] Project registration form, Sketch2Life, version 1.2, supplied 22 October 2026. Scope authority for this Review 2 draft; form class and project code fields are blank.",
        "[2] Collaborative Learning SRS v3.1, FEAT-039, repository artifact. Canonical detailed actor, functional, data, state, API and privacy source.",
        "[3] Sketch2Life repository at local dev commit 0a7ce768c153f2104cff930569c3eda6e484532c; working tree contains uncommitted changes and is not tag review-2.",
        "[4] ADR-0019, Classroom runtime composition and Modal hosting direction, accepted for target documentation; code implementation remains separately scoped.",
        "[5] SWP490 Review 2 preparation guide v1.0 and BM01-BM04 forms, course-supplied October 2026.",
        "[6] FPT University SEP490 Student Guide, Fall 2023; Report 2 Project Management Plan and sample schedule. Schedule dates in the sample are not reused.",
        "[7] Agile Manifesto, Principles behind the Agile Manifesto, https://agilemanifesto.org/principles (accessed 23 October 2026). Used for iterative feedback only.",
        "[8] Ken Schwaber and Jeff Sutherland, The Scrum Guide, November 2020, https://scrumguides.org/scrum-guide.html (accessed 23 October 2026). Used to distinguish feature-based cadence from formal Scrum adoption.",
        "[9] GitHub Docs, About Projects, https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects (accessed 23 October 2026). A configured project board is not verified.",
    ]
    for item in refs:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(5)


FINDINGS = [
    ("SR-01", "Flows", "apps/child-ui/src/services/apiClient.ts; apps/child-ui/src/services/sessionClient.ts", "The registered join/drawing workflows are not connected end-to-end: the Child API client returns a stub success and session verification uses a local fixture. The UI source therefore does not prove admission, persistence or recovery against BE1.", "High", "Source code shows stubbed API/session behavior; BE1 durable APIs exist separately in backend. Proposed response: Planned — Bảo owns Child adapter; Đạt coordinates contract/E2E; target W6-W9, dates TBD."),
    ("SR-02", "Architecture", "backend/src/sketch2life/interfaces/http/app.py; ADR-0019", "The current HTTP composition still includes durable classroom routes alongside legacy/demo routers and process-local stores. The accepted classroom-first product composition with isolated demo entrypoints is not fully implemented.", "High", "App composition imports/mounts both route families. ADR-0019 explicitly separates target documentation from runtime implementation. Proposed response: Planned — Đạt, with Khoa; before staging, calendar TBD."),
    ("SR-03", "Data", "Report 4 §8; backend/alembic/versions; backend/alembic/README.md", "The logical target model contains classroom, privacy, learning-content and portfolio entities that do not all have a single accepted end-to-end physical mapping. The database is split across nine module migration roots; the Report 4 ERD is an excerpt and no unified release order is approved.", "High", "Repository migrations show separate be1_core, ai_jobs, ap, lc, kv, vr, ae, pa and vf roots; README warns that plain upgrade head is ambiguous. Proposed response: Planned — Khoa; approve crosswalk and fresh-database upgrade/rollback before staging."),
    ("SR-04", "States", "D10_state_session.mmd; backend/src/sketch2life/infrastructure/persistence/be1_models.py", "The target session state model uses Draft/Lobby/Active/Paused/Completed/EndedEarly, while the persisted BE1 session status uses configured/lobby/active/paused/finished. Mapping finished to Completed versus EndedEarly and invalid-transition handling are not yet accepted in a versioned contract.", "High", "The state diagram and ORM enum names differ. Proposed response: Planned — Khoa; define explicit state mapping and transition-negative tests before integration freeze."),
    ("SR-05", "Data / privacy", "Phieu_FA26SE225_v1.2; backend/src/sketch2life/infrastructure/persistence/be1_models.py; FEAT-047 consent receipt", "The registration sets a 90-day session/artwork retention default and school-mediated purpose consent. Current BE1 records consent and fails closed for pending consent, but the full purpose catalogue, representative verification and purge of all derivatives/copies are not demonstrated.", "High", "Registration and SRS data lifecycle require scope/copy-specific handling; BE1 receipt reports CONSENT_NOT_EFFECTIVE for pending consent and bounds purge evidence. Proposed response: Planned — Đạt and Khoa; approve policy and purge tests before any child-data pilot."),
    ("SR-06", "Flows / testing", "Report 5 §6; FEAT-059 receipts; Project Tracking", "None of the four main workflows has a current staging E2E receipt in this snapshot, and the target of one class with up to 40 unique children has no measured capacity result. Historical unit/contract/cleanup receipts do not close the workflow gate.", "High", "Recorded FEAT-059 checks were bounded local tests; no staging/classroom/load receipt is registered. Proposed response: Planned — Đạt coordinates all owners; W12-W13 proposal, dates TBD."),
    ("SR-07", "Architecture / third-party service", "ADR-0019; Report 4 §6; Modal configuration", "Modal is selected but its application/environment, model, GPU, endpoint, region, scale, timeout, secret policy, spending cap and inference measurements are unspecified. AI request speed and product availability cannot be verified.", "High", "Owner selected Modal and deferred deployment values; repository has no product endpoint receipt. Proposed response: Planned — Hiếu with owner; before AI acceptance, dates TBD."),
    ("SR-08", "Requirements / NFR", "SRS v3.1 B11; Report 3 candidate NFR table; Report 5", "Some quality constraints remain qualitative or have candidate thresholds only. RPO/RTO, AI quality, age/safety review, cost and non-session data retention have no approved measurement profile.", "Medium", "SRS labels these values proposed/TBD; candidate latency and purge checks are explicitly not measured. Proposed response: Planned — owners propose metrics at weekly review; supervisor approval pending."),
    ("SR-09", "Scope / metadata", "Phieu_FA26SE225_v1.2.docx; BM01 header", "The form body leaves class and project code blank. FA26SE225 is inferred from the filename and must not be treated as a confirmed class/project identifier.", "Medium", "The supplied form body has an empty Class field and no project-code field value. Proposed response: Planned — Đạt confirms from the official course record before submission."),
    ("SR-10", "Design vs code", "apps/admin-ui/src/services/authService.ts; apps/teacher-ui/src/services; apps/child-ui/src/services", "The Admin login currently returns a mock token and the Teacher/Child services use fixtures or stubs. The review documents their prototype status, but live adult identity and integrated UI requests cannot be verified from those service modules.", "Low", "Mock token and fixture service code are visible in repository; no production identity receipt is claimed. Proposed response: Kept for this draft because these surfaces are prototypes; integrate through the approved contracts before staging."),
]


def fill_meta_table(table, pairs):
    for i, (key, value) in enumerate(pairs):
        if i >= len(table.rows):
            table.add_row()
        set_cell(table.rows[i].cells[0], key, bold=True, size=8.5)
        set_cell(table.rows[i].cells[1], value, size=8.5)


def build_bm02():
    doc = Document(BM02_TEMPLATE)
    for p in list(doc.paragraphs):
        if p.text.startswith("Form BM02.") or p.text.startswith("Use this prompt without modification.") or p.text.startswith("Team response:") or p.text.startswith("Every High finding"):
            p._element.getparent().remove(p._element)
    fill_meta_table(doc.tables[0], [
        ("Project code", "FA26SE225 (inferred from filename; confirm)"),
        ("Project name", "Sketch2Life: Collaborative Creative Learning with AI for Children"),
        ("Team", "Đỗ Cao Đạt SE193713; Phạm Tấn Hiếu SE184252; Vũ Chí Bảo SE182733; Lý Anh Khoa SE182682"),
        ("Supervisor", "Lâm Hữu Khánh Phương"),
        ("AI tool and model", "OpenAI Codex desktop coding agent, GPT-6"),
        ("Run date", "23 October 2026"),
        ("Repository tag / commit", "No review-2 tag exists. Local dev HEAD 0a7ce768c153f2104cff930569c3eda6e484532c; working tree has uncommitted user changes and was included in source review."),
        ("Registration form version used", "Phieu_FA26SE225_v1.2"),
        ("Version", "Draft self-review v1.0; not a tagged-baseline course run"),
        ("Date", "23 October 2026"),
    ])
    # Keep the prompt table copied unchanged from the official form.
    prompt_before = "\n".join(c.text for row in doc.tables[1].rows for c in row.cells)
    findings_rows = [(a,b,c,d,e,f) for a,b,c,d,e,f in FINDINGS]
    replace_table_rows(doc.tables[2], ["ID", "Category", "Location", "Finding", "Severity", "Evidence", "Team response"], findings_rows,
                       [0.4, 0.65, 0.95, 1.65, 0.5, 1.05, 1.35], 6.5)
    for row in doc.tables[2].rows:
        tr_pr = row._tr.get_or_add_trPr()
        if tr_pr.find(qn("w:cantSplit")) is None:
            tr_pr.append(OxmlElement("w:cantSplit"))
    top_ids = ["SR-01", "SR-02", "SR-03", "SR-04", "SR-05"]
    top_rows = []
    for i, id_ in enumerate(top_ids, 1):
        f = next(x for x in FINDINGS if x[0] == id_)
        top_rows.append((str(i), id_, f[3].split(".")[0]))
    replace_table_rows(doc.tables[3], ["#", "Finding ID", "Summary"], top_rows, [0.45, 0.85, 5.4], 7.6)
    counts = {sev: sum(1 for x in FINDINGS if x[4] == sev) for sev in ("High", "Medium", "Low")}
    summary = []
    for sev in ("High", "Medium", "Low"):
        fixed = sum(1 for x in FINDINGS if x[4] == sev and x[5].startswith("Fixed"))
        kept = sum(1 for x in FINDINGS if x[4] == sev and x[5].startswith("Kept"))
        planned = sum(1 for x in FINDINGS if x[4] == sev and x[5].startswith("Planned"))
        summary.append((sev, str(counts[sev]), str(fixed), str(kept), str(planned)))
    replace_table_rows(doc.tables[4], ["Severity", "Total", "Fixed", "Kept", "Planned"], summary, [1.0, 0.7, 0.7, 0.7, 0.7], 8.0)
    for para in doc.paragraphs:
        if para.text.strip() == "3. Findings and Team Response":
            para.paragraph_format.page_break_before = True
            break
    end = doc.add_paragraph("Summary. The static source review reports 7 High, 2 Medium and 1 Low finding. Team responses are proposed for owner confirmation; no issue is recorded Fixed because this documentation pass did not modify application code. The review-2 tag is absent and the checkout was dirty, so this draft does not satisfy the guide's exact tagged-baseline run requirement. No application test was run for this review.")
    end.paragraph_format.space_before = Pt(6)
    end.paragraph_format.space_after = Pt(6)
    # Integrity check: standard prompt text remains byte-for-byte at the paragraph text level.
    original_prompt = Document(BM02_TEMPLATE).tables[1].cell(0, 0).text
    current_prompt = doc.tables[1].cell(0, 0).text
    if original_prompt != current_prompt:
        raise ValueError("BM02 standard prompt was modified")
    out = OUT / "SWP490_FA26SE225_R2_SelfReview.docx"
    doc.save(out)
    return out, hashlib.sha256(original_prompt.encode("utf-8")).hexdigest()


def build_bm01():
    doc = Document(BM01_SOURCE)
    for table in doc.tables:
        header = [c.text.strip() for c in table.rows[0].cells]
        if len(header) >= 3 and header[0] == "ID" and header[1] == "Known gap":
            gaps = [
                ("G1", "Class and code fields are blank; FA26SE225 is inferred.", "Đạt confirms with course/supervisor before submission; field remains TBD until verified."),
                ("G2", "Child/Teacher/Admin services use fixtures or stubs; no integrated workflow is established. [SR-01, SR-10]", "Bảo owns UI adapters; Đạt coordinates four contract-based E2E paths before staging."),
                ("G3", "Current HTTP composition still includes demo/legacy routes; classroom-first target composition is not implemented. [SR-02]", "Đạt and Khoa isolate runtime composition under an approved cleanup feature before staging."),
                ("G4", "Target logical entities and state labels do not yet have a complete approved physical/state mapping; nine migration roots need an order. [SR-03, SR-04]", "Khoa publishes schema/state crosswalk and clean-database upgrade tests before integration freeze."),
                ("G5", "Consent/purpose and 90-day session/artwork retention do not yet have end-to-end copy/purge evidence. [SR-05]", "Đạt and Khoa confirm school process, purpose policy and synthetic purge evidence before child-data pilot."),
                ("G6", "Modal is unconfigured; 61 target tests, staging workflows and 40-child capacity are unmeasured. [SR-06–SR-08]", "Hiếu supplies Modal profile; Đạt coordinates 31+ CI tests and staged measurement; all owners review."),
            ]
            replace_table_rows(table, ["ID", "Known gap", "Action / owner / gate"], gaps, [0.5, 3.0, 2.9], 7.0)
        if len(header) >= 4 and header[0] == "Source" and header[1] == "Count":
            formula = [
                ("Mandatory features", "6", "3", "18"),
                ("Main workflows", "4", "1", "4"),
                ("Legal main-entity transitions", "29", "1", "29"),
                ("Illegal transition rejection", "4", "1", "4"),
                ("Measurable candidate NFRs", "6", "1", "6"),
                ("Minimum planned case total", "", "", "61"),
                ("Automated in CI minimum", "At least 50%", "round up", "31"),
            ]
            replace_table_rows(table, ["Source", "Count", "Minimum per item", "Subtotal / target"], formula, [2.0, 1.0, 1.5, 2.2], 7.5)
    for p in doc.paragraphs:
        if p.text.startswith("Minimum target:"):
            p.text = "Minimum proposed target: 61 committed functional cases; at least 31 must run automatically in CI. The count is 18 mandatory-feature cases + 4 workflow cases + 29 legal main-state transitions + 4 explicit illegal-transition rejection cases + 6 measurable candidate NFR cases. The Review 2 team and reviewers must confirm the final commitment. These cases have not been run against staging."
    out = OUT / "SWP490_FA26SE225_R2_DesignBrief.docx"
    doc.save(out)
    return out


def build_registration_bundle():
    registration = Document(REGISTRATION)
    bm03 = Document(BM03_TEMPLATE)
    fill_meta_table(bm03.tables[0], [
        ("Project code", "FA26SE225 (inferred from filename; confirm)"),
        ("Project name", "Sketch2Life: Collaborative Creative Learning with AI for Children"),
        ("Team", "Đỗ Cao Đạt SE193713; Phạm Tấn Hiếu SE184252; Vũ Chí Bảo SE182733; Lý Anh Khoa SE182682"),
        ("Supervisor", "Lâm Hữu Khánh Phương"),
        ("Current registration version", "1.2"),
        ("Proposed version", "1.2 (No changes proposed)"),
        ("Version", "BM03 v1.0"),
        ("Date", "23 October 2026"),
    ])
    replace_table_rows(bm03.tables[1], ["No.", "Section", "Current content", "Proposed content", "Reason", "Proposed by"], [
        ("—", "All sections", "Supplied registration v1.2", "No changes", "Owner has not requested a scope change; v1.2 remains the authority for the Review 2 draft.", "Project owner")
    ], [0.35, 0.8, 1.45, 1.35, 1.8, 0.75], 7.5)
    for p in list(bm03.paragraphs):
        if p.text.startswith("Form BM03.") or p.text.startswith("Accepted reasons:"):
            p._element.getparent().remove(p._element)
        elif "No changes to the current registration form" in p.text:
            p.text = "☒ No changes to the current registration form"
    # The reviewer decision table intentionally remains blank for the Review 2 meeting.
    bm03_sec = bm03.sections[0]
    section = registration.add_section(WD_SECTION.NEW_PAGE)
    section.page_width = bm03_sec.page_width
    section.page_height = bm03_sec.page_height
    section.top_margin = bm03_sec.top_margin
    section.bottom_margin = bm03_sec.bottom_margin
    section.left_margin = bm03_sec.left_margin
    section.right_margin = bm03_sec.right_margin
    for element in list(bm03.element.body):
        if element.tag == qn("w:sectPr"):
            continue
        registration.element.body.insert(len(registration.element.body) - 1, copy.deepcopy(element))
    out = OUT / "SWP490_FA26SE225_R2_Registration.docx"
    registration.save(out)
    return out


def build_report():
    doc = Document(REPORT_SOURCE)
    add_report1(doc)
    add_report2(doc)
    add_report3(doc)
    rendered = render_workflow_diagrams()
    add_report4(doc, rendered)
    add_report5(doc)
    add_tracking(doc)
    add_references(doc)
    # Remove the source template's duplicate page break before the first report
    # heading; the break lives in an otherwise empty paragraph.
    for index, paragraph in enumerate(doc.paragraphs):
        if paragraph.text.strip() or not paragraph._p.xpath('.//w:br[@w:type="page"]'):
            continue
        following = next((p.text.strip() for p in doc.paragraphs[index + 1:] if p.text.strip()), "")
        if following == "I. Project Introduction":
            paragraph._element.getparent().remove(paragraph._element)
            break
    out = OUT / "SWP490_FA26SE225_R2_Report1-5_Tracking.docx"
    doc.save(out)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diagrams").mkdir(exist_ok=True)
    from build_bm01_rev6 import build_bm01_formatted
    built = [build_registration_bundle(), build_report(), build_bm02()[0], build_bm01_formatted()]
    for path in built:
        print(f"DOCX {path} {path.stat().st_size} bytes sha256={sha(path)}")
    print(f"BM02_FINDINGS {len(FINDINGS)}; severity={{'High': 7, 'Medium': 2, 'Low': 1}}; prompt_preserved=true")
    print(f"TEST_CASE_TARGET {len(test_case_rows())}; automated_minimum=31")
    print(f"MIGRATION_ROWS {len(migration_inventory())}")


if __name__ == "__main__":
    main()




