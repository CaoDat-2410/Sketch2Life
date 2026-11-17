"""Fill the supplied SEP490 Report 2 template with Sketch2Life's current plan."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.text.paragraph import Paragraph

from build_deliverables import PICTURES, flow_image, write_mmd
from report2_data import (
    COMMUNICATION_ROWS,
    DELIVERABLE_ROWS,
    RACI_ROWS,
    SCHEDULE_ROWS,
    TOOLS_ROWS,
    TOTAL_EFFORT,
    TRAINING_ROWS,
    WBS_ROWS,
)


ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "features" / "FEAT-058-review2-document-package"
SOURCE_TEMPLATE = FEATURE / "evidence" / "local" / "Report2_Project Management Plan.docx"
OUT = FEATURE / "artifacts" / "SWP490_FA26SE225_R2_Report2_Project_Management_Plan.docx"
EXPECTED_TEMPLATE_SHA256 = "f59a4ce96d99f2f772f4c0ef07828812674aee4b8795aac475d5a395a8401be5"

BLACK = "111111"
NAVY = "14243D"
PALE_ALT = "F2F4F7"
PALE_TOTAL = "E8EDF4"
GRID = "CBD2DC"
WHITE = "FFFFFF"
BODY_FONT = "Calibri"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def set_run(run, *, size=9.5, bold=False, color=BLACK, italic=False, name=BODY_FONT):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def replace_paragraph(paragraph, text: str, *, size=9.6, bold=False, color=BLACK, italic=False, align=None):
    paragraph.clear()
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.03
    if align is not None:
        paragraph.alignment = align
    if text:
        set_run(paragraph.add_run(text), size=size, bold=bold, italic=italic, color=color)
    return paragraph


def set_style_font(style, *, size, color=BLACK, bold=False, name=BODY_FONT):
    style.font.name = name
    rpr = style._element.get_or_add_rPr()
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:eastAsia"), name)
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor.from_string(color)
    style.font.bold = bold


def set_document_theme(doc):
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.header_distance = Inches(0.45)
    section.footer_distance = Inches(0.45)
    section.different_first_page_header_footer = True

    normal = doc.styles["Normal"]
    set_style_font(normal, size=10.0)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.08

    heading_specs = {
        "Heading 1": (16.0, 12, 6),
        "Heading 2": (12.5, 8, 4),
        "Heading 3": (11.5, 6, 3),
    }
    for style_name, (size, before, after) in heading_specs.items():
        style = doc.styles[style_name]
        set_style_font(style, size=size, color=NAVY, bold=True)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.keep_together = True

    for style_name, size, color, bold in (
        ("TOC Heading", 16.0, NAVY, True),
        ("TOC 1", 10.0, BLACK, False),
        ("TOC 2", 9.5, BLACK, False),
        ("TOC 3", 9.0, BLACK, False),
    ):
        if style_name in doc.styles:
            style = doc.styles[style_name]
            set_style_font(style, size=size, color=color, bold=bold)
            style.paragraph_format.space_after = Pt(3)
            style.paragraph_format.keep_together = True

    for style_name in ("Header", "Footer"):
        if style_name in doc.styles:
            set_style_font(doc.styles[style_name], size=8.0, color="5D6878")


def add_word_field(paragraph, instruction):
    for kind, element_name, payload in (
        ("begin", "w:fldChar", None),
        (None, "w:instrText", f" {instruction} "),
        ("separate", "w:fldChar", None),
        (None, "w:t", "1"),
        ("end", "w:fldChar", None),
    ):
        run = paragraph.add_run()
        set_run(run, size=8.0, color="5D6878")
        element = OxmlElement(element_name)
        if kind:
            element.set(qn("w:fldCharType"), kind)
        if element_name == "w:instrText":
            element.set(qn("xml:space"), "preserve")
        if payload is not None:
            element.text = payload
        run._r.append(element)


def set_footer_paragraph(paragraph, *, branded=False):
    paragraph.clear()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    label = "Sketch2Life | Review 2 | " if branded else ""
    if label:
        set_run(paragraph.add_run(label), size=8.0, color="5D6878")
    add_word_field(paragraph, "PAGE")


def set_document_footers(doc):
    section = doc.sections[0]
    set_footer_paragraph(section.first_page_footer.paragraphs[0], branded=True)
    set_footer_paragraph(section.footer.paragraphs[0], branded=False)
    section.first_page_header.paragraphs[0].clear()
    section.header.paragraphs[0].clear()


def apply_table_borders(table, color=GRID, size="4"):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        element = borders.find(tag)
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def paragraph_after(reference: Paragraph, text="", *, style="Normal", size=9.4, bold=False, color=BLACK):
    element = OxmlElement("w:p")
    reference._p.addnext(element)
    paragraph = Paragraph(element, reference._parent)
    paragraph.style = style
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.03
    if text:
        set_run(paragraph.add_run(text), size=size, bold=bold, color=color)
    return paragraph


def remove_paragraph(paragraph: Paragraph):
    parent = paragraph._p.getparent()
    if parent is not None:
        parent.remove(paragraph._p)


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=65, start=75, bottom=65, end=75):
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn("w:" + side))
        if node is None:
            node = OxmlElement("w:" + side)
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def mark_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def prevent_row_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    tr_pr.append(cant)


def set_cell(cell, value, *, header=False, size=8.0, fill=None, bold=False, align=None, color=BLACK):
    cell.text = ""
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_margins(cell)
    tc_pr = cell._tc.get_or_add_tcPr()
    for orientation in list(tc_pr.findall(qn("w:textDirection"))):
        tc_pr.remove(orientation)
    if header:
        fill = NAVY
        color = WHITE
    if fill:
        set_cell_shading(cell, fill)
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run(str(value))
    set_run(run, size=size, bold=bold or header, color=color)


def format_table(table, headers, rows, widths, *, body_size=7.8, header_size=8.0, bold_first=False, center_columns=()):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    if len(table.columns) != len(headers):
        raise ValueError(f"Table has {len(table.columns)} columns; expected {len(headers)}")
    for index, width in enumerate(widths):
        table.columns[index].width = Inches(width)
    while len(table.rows) > 1:
        table._tbl.remove(table.rows[-1]._tr)
    for row_values in rows:
        if len(row_values) != len(headers):
            raise ValueError(f"Row has {len(row_values)} cells; expected {len(headers)}: {row_values}")
        table.add_row()
    for column, title in enumerate(headers):
        cell = table.rows[0].cells[column]
        cell.width = Inches(widths[column])
        set_cell(cell, title, header=True, size=header_size, align=WD_ALIGN_PARAGRAPH.LEFT)
    mark_repeat_header(table.rows[0])
    prevent_row_split(table.rows[0])
    for row_index, row_values in enumerate(rows, 1):
        row = table.rows[row_index]
        for column, value in enumerate(row_values):
            cell = row.cells[column]
            cell.width = Inches(widths[column])
            align = WD_ALIGN_PARAGRAPH.CENTER if column in center_columns else None
            row_fill = PALE_ALT if row_index % 2 == 0 else None
            group_bold = bool(bold_first and column == 0)
            set_cell(cell, value, size=body_size, fill=row_fill, bold=group_bold, align=align)
        prevent_row_split(row)
    apply_table_borders(table)
    return table


def set_existing_table(table, headers, rows, widths, *, body_size=7.8, header_size=8.0, bold_first=False, center_columns=()):
    # Preserve the official table header row and grid/border formatting.
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for index, width in enumerate(widths):
        table.columns[index].width = Inches(width)
    for title_index, title in enumerate(headers):
        table.rows[0].cells[title_index].width = Inches(widths[title_index])
        set_cell(table.rows[0].cells[title_index], title, header=True, size=header_size, align=WD_ALIGN_PARAGRAPH.LEFT)
    header_properties = table.rows[0]._tr.get_or_add_trPr()
    for fixed_height in list(header_properties.findall(qn("w:trHeight"))):
        header_properties.remove(fixed_height)
    mark_repeat_header(table.rows[0])
    while len(table.rows) > 1:
        table._tbl.remove(table.rows[-1]._tr)
    for _ in rows:
        table.add_row()
    for row_index, row_values in enumerate(rows, 1):
        row = table.rows[row_index]
        for column, value in enumerate(row_values):
            cell = row.cells[column]
            cell.width = Inches(widths[column])
            align = WD_ALIGN_PARAGRAPH.CENTER if column in center_columns else None
            group_bold = bool(bold_first and column == 0)
            set_cell(cell, value, size=body_size, fill=PALE_ALT if row_index % 2 == 0 else None, bold=group_bold, align=align)
        prevent_row_split(row)
    prevent_row_split(table.rows[0])
    apply_table_borders(table)
    return table


def append_table(doc, headers, rows, widths, *, body_size=7.2, header_size=7.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    format_table(table, headers, rows, widths, body_size=body_size, header_size=header_size)
    return table


def add_process_diagram():
    source = """flowchart LR
  A[Feature backlog and dependencies] --> B[Testable acceptance criteria and approved feature plan]
  B --> C[Implement a small vertical slice with tests]
  C --> D[Pull request review and CI]
  D --> E[Integrate versioned contracts and collect feature evidence]
  E --> F[Weekly review and update backlog and time plan]
"""
    write_mmd("D14_feature_delivery_process", source)
    nodes = {
        "a": (45, 300, 340, 565, "Feature backlog\nand dependencies"),
        "b": (390, 300, 685, 565, "Testable acceptance\nand approved plan"),
        "c": (735, 300, 1030, 565, "Implement small slice\nand tests"),
        "d": (1080, 300, 1375, 565, "Pull request review\nand CI"),
        "e": (1425, 300, 1720, 565, "Integrate contracts\nand collect evidence"),
        "f": (1770, 300, 2065, 565, "Weekly review and\nplan adaptation"),
    }
    edges = [("a", "b", ""), ("b", "c", ""), ("c", "d", ""), ("d", "e", ""), ("e", "f", "")]
    return flow_image(
        "D14_feature_delivery_process.png",
        "Feature-Based Delivery and Quality Loop",
        "Owner-confirmed: weekly review and CI; exact calendar cadence beyond weekly review is not set",
        nodes,
        edges,
        width=2110,
        height=860,
    )


def insert_cover_metadata(doc):
    paragraphs = doc.paragraphs
    title = next(p for p in paragraphs if "Report 2" in p.text and "Project Management Plan" in p.text)
    date_line = next(p for p in paragraphs if "Hanoi" in p.text and "2019" in p.text)
    title_index = paragraphs.index(title)
    date_index = paragraphs.index(date_line)
    for paragraph in paragraphs[title_index + 1:date_index]:
        if not paragraph.text.strip():
            remove_paragraph(paragraph)
    replace_paragraph(title, "Report 2 – Project Management Plan", size=18.0, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER)
    cover_title = next(p for p in doc.paragraphs if p.text.strip() == "Capstone Project Report")
    replace_paragraph(cover_title, "CAPSTONE PROJECT REPORT", size=22.0, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER)
    cover_title.paragraph_format.space_after = Pt(5)
    title.paragraph_format.space_before = Pt(0)
    title.paragraph_format.space_after = Pt(16)
    title.paragraph_format.keep_with_next = True

    logo_paragraph = next((p for p in doc.paragraphs if any(node.tag == qn("w:drawing") for node in p._p.iter())), None)
    if logo_paragraph is not None:
        logo_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        logo_paragraph.paragraph_format.space_after = Pt(38)
        paragraphs = list(doc.paragraphs)
        logo_index = next(index for index, paragraph in enumerate(paragraphs) if paragraph._p is logo_paragraph._p)
        title_index = next(index for index, paragraph in enumerate(paragraphs) if paragraph._p is cover_title._p)
        for blank in paragraphs[logo_index + 1:title_index]:
            if not blank.text.strip():
                remove_paragraph(blank)

    table = doc.add_table(rows=6, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(1.65)
    table.columns[1].width = Inches(4.62)
    table.cell(0, 0).merge(table.cell(0, 1))
    metadata_rows = [
        ("Sketch2Life: Collaborative Creative Learning with AI for Children", ""),
        ("Group Members", "Đỗ Cao Đạt | SE193713 | Leader, Fullstack\nPhạm Tấn Hiếu | SE184252 | BE2\nVũ Chí Bảo | SE182733 | FE\nLý Anh Khoa | SE182682 | BE1"),
        ("Supervisor", "Lâm Hữu Khánh Phương"),
        ("External Supervisor", "N/A"),
        ("Capstone Project code", "FA26SE225 (inferred) | Class: TBD"),
        ("Project Period / Document", "09/2026–03/2027 | Draft v1.0 | 23 October 2026"),
    ]
    for index, (label, value) in enumerate(metadata_rows):
        row = table.rows[index]
        for cell, width in zip(row.cells, (1.65, 4.62)):
            cell.width = Inches(width)
        if index == 0:
            set_cell(row.cells[0], label, size=12.0, bold=True, color=NAVY, fill=PALE_TOTAL)
            row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
            row.cells[0].paragraphs[0].paragraph_format.space_after = Pt(2)
            continue
        set_cell(row.cells[0], label, size=9.5, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row.cells[1], value, size=9.2)
    apply_table_borders(table, color=GRID, size="5")
    date_line._p.addprevious(table._tbl)
    replace_paragraph(date_line, "Ho Chi Minh City, October 2026", size=9.5, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER)
    date_line.paragraph_format.space_before = Pt(9)
    date_line.paragraph_format.space_after = Pt(0)


def move_toc_to_its_own_page(doc):
    toc_control = next(
        (
            node for node in doc._body._element.iter(qn("w:sdt"))
            if any(
                instruction.text and instruction.text.strip().startswith("TOC ")
                for instruction in node.iter(qn("w:instrText"))
            )
        ),
        None,
    )
    if toc_control is None:
        raise RuntimeError("Could not locate the official template's Table of Contents control")
    page_break = OxmlElement("w:p")
    run = OxmlElement("w:r")
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    run.append(br)
    page_break.append(run)
    toc_control.addprevious(page_break)


def populate_content_paragraphs(doc):
    replacements = {
        "[Create/Provide": "The WBS estimates the registered product scope from requirements through verification. Complexity is a relative planning label. All estimates are preliminary person-days, not time sheets or member commitments; confirm team capacity and re-estimate at weekly reviews.",
        "[Provide the overall": "Overall objective: deliver a Teacher-led collaborative creative-learning system for children aged 36–155 months, with separate product surfaces, reviewed AI/content, classroom controls, privacy safeguards and reproducible verification. The targets below are future acceptance objectives, not measured results.",
        "[List out the details": "The following risks are assessed for the current source and integration baseline. Probability and impact are qualitative until the team adopts a risk scoring scale.",
        "[Describe the approach": "Use an iterative, feature-based workflow that keeps requirements, implementation, verification and evidence attached to an approved feature plan. Review scope and risks weekly and adjust estimates from observed progress.",
        "[Draw and describe": "The team uses a feature delivery loop rather than a declared Scrum framework. Work moves from a prioritized feature and its dependencies to testable acceptance criteria, approved plan, implementation, pull-request review, CI, integration evidence and weekly plan adaptation. If a gate fails, update the feature and repeat the relevant checks.",
        "[Provide the approach": "Quality is built into each approved feature. Acceptance criteria are linked to tests; test counts below are goals and current result fields remain unmeasured unless a named receipt is available.",
        "[You need to plan": "Training is scheduled before the related work gate. Attendance, artifacts and demonstrations should be recorded in the project feature evidence; child data and paid provider calls remain prohibited until their controls are approved.",
        "[Given the main": "Deliverables are staged through the 15-week relative plan below. The SEP490 registration gives the overall period as September 2026–March 2027; official calendar dates and submission deadlines must be confirmed with the course. The sample schedule's 2021 dates are not reused.",
        "[Describe the main": "The matrix assigns a delivery lead/reviewer/support role for major outputs and one accountable workflow owner per main workflow. Detailed sprint assignments are updated in the weekly feature review.",
        "[Describe how you would manage project documents": "Keep supplied registration forms, school templates and canonical requirement sources unchanged. Maintain editable report files and diagram sources in the FEAT-058 package; record each revision, input/output hash, decision, approval and page-render evidence. Any scope change requires the owner and supervisor to reconcile registration, SRS, SDD and Report 5.",
        "[Describe how you would manage project source codes": "Use feature branches and pull requests against the local dev integration baseline. Require the feature plan/acceptance/approval/evidence workflow, review the relevant owner contract, and make CI checks pass before merging. Never commit credentials, provider tokens, signing keys or real child data. Run the repository security validator before every commit or push. The current dev snapshot is local and unpushed; the cleanup worktree is uncommitted.",
    }
    paragraphs = list(doc.paragraphs)
    for index, paragraph in enumerate(paragraphs):
        text = paragraph.text.strip()
        replacement = next((value for prefix, value in replacements.items() if text.startswith(prefix)), None)
        if replacement is not None:
            replace_paragraph(paragraph, replacement, size=9.6)
            continue
        if text == "Quality":
            replace_paragraph(paragraph, "Quality targets and current evidence", size=9.7, bold=True, color=NAVY)
        elif text.startswith("Milestone Timeliness"):
            replace_paragraph(paragraph, "Milestone timeliness: target 100% of approved gates by their confirmed due dates. Calendar dates are not yet supplied; track variance weekly after the course calendar is confirmed.", size=9.5)
        elif text.startswith("Allocated Effort"):
            replace_paragraph(paragraph, "Allocated effort: preliminary total 252 person-days across the product WBS. Planning distribution: requirements 33; design 38; implementation 111; testing 45; project management/documentation/training 25 person-days. Validate capacity before baseline approval.", size=9.5)
        elif text == "]" or text == "[":
            previous = paragraphs[index - 1].text.strip() if index > 0 else ""
            if previous.startswith("Allocated effort:"):
                replace_paragraph(paragraph, "Cost control: Modal is selected but its model, GPU, usage profile and spending cap are TBD. No paid provider use is planned before an approved budget; target spend is at or below the later approved cap.", size=9.5)
            else:
                replace_paragraph(paragraph, "")
        elif text == "Defect Prevention":
            replace_paragraph(paragraph, "Defect prevention: refine each requirement into a testable acceptance condition; keep domain decisions framework-independent and use synthetic data.", size=9.4)
        elif text == "Reviewing":
            replace_paragraph(paragraph, "Reviewing: review feature plans and PRs against contracts, migrations, privacy boundaries and acceptance evidence; do not treat UI fixtures as service integration.", size=9.4)
        elif text in {"Unit Test", "Unit Testing"}:
            replace_paragraph(paragraph, "Unit tests: cover domain rules, authorization decisions, lifecycle transitions and error mapping for each owned feature.", size=9.4)
        elif text == "Integration Testing":
            replace_paragraph(paragraph, "Integration tests: verify versioned API contracts, database migration/recovery behavior and cross-service handoffs with isolated synthetic fixtures.", size=9.4)
        elif text == "System Testing":
            replace_paragraph(paragraph, "System and acceptance tests: execute each main workflow, role denial, stale result, reconnect and data-retention path in staging; record actual values and defects in Report 5.", size=9.4)
    # Replace the original title and location line while preserving the template style.
    for paragraph in doc.paragraphs:
        if paragraph.text.strip() == "D~Do; R~Review; S~Support; I~Informed; <blank>- Omitted":
            replace_paragraph(paragraph, "D = Do; R = Review; S = Support; I = Informed; blank = not assigned.", size=9.0, italic=True)
            break


def insert_process_figure(doc, image_path):
    process_para = next(p for p in doc.paragraphs if p.style.name == "Normal" and p.text.startswith("The team uses a feature delivery loop"))
    next_heading = next(p for p in doc.paragraphs if p.text.strip() == "2.2 Quality Management")
    image_para = doc.add_paragraph()
    image_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    image_para.paragraph_format.space_before = Pt(3)
    image_para.paragraph_format.space_after = Pt(0)
    image_para.add_run().add_picture(str(image_path), width=Inches(6.25))
    next_heading._p.addprevious(image_para._p)
    caption = doc.add_paragraph()
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.space_before = Pt(1)
    caption.paragraph_format.space_after = Pt(5)
    set_run(caption.add_run("Figure 1. Feature-based delivery process; weekly review returns work to the prioritized backlog."), size=8.8, italic=True, color="5D6878")
    next_heading._p.addprevious(caption._p)
    process_para.paragraph_format.keep_with_next = True
    process_para.paragraph_format.keep_together = True


def insert_time_plan(doc, deliverables_table):
    heading_one = doc.add_paragraph("3.1 Project Schedule and Time Plan", style="Heading 3")
    heading_one.paragraph_format.keep_with_next = True
    schedule = append_table(
        doc,
        ["Relative window", "Work / phase", "Dependency", "Lead", "Output / exit gate", "Status"],
        SCHEDULE_ROWS,
        [0.80, 1.23, 0.82, 0.87, 1.50, 1.03],
        body_size=7.0,
        header_size=7.2,
    )
    heading_two = doc.add_paragraph("3.2 Deliverable Register", style="Heading 3")
    heading_two.paragraph_format.keep_with_next = True
    deliverables_table._tbl.addprevious(heading_one._p)
    deliverables_table._tbl.addprevious(schedule._tbl)
    deliverables_table._tbl.addprevious(heading_two._p)


def add_references(doc):
    doc.add_page_break()
    heading = doc.add_heading("III. References", level=1)
    heading.paragraph_format.keep_with_next = True
    references = [
        "[1] FPT University. SEP490 Student Guide, Fall 2023; Report 2 Project Management Plan template and Report2 Sample Project Schedule (course-provided local materials). The 2021 dates are used as a sequence example only.",
        "[2] Agile Manifesto. Principles behind the Agile Manifesto. https://agilemanifesto.org/principles (accessed 23 October 2026). Used as a basis for short feedback cycles, frequent review and adaptation.",
        "[3] Ken Schwaber and Jeff Sutherland. The Scrum Guide, November 2020. https://scrumguides.org/scrum-guide.html (accessed 23 October 2026). Reference for distinguishing the team's feature-based workflow from a formal Scrum adoption.",
        "[4] GitHub Docs. About Projects. https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects (accessed 23 October 2026). Supports the proposed use of issue, board and timeline views; no configured board is claimed.",
    ]
    for text in references:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.22)
        paragraph.paragraph_format.first_line_indent = Inches(-0.22)
        paragraph.paragraph_format.space_after = Pt(6)
        paragraph.paragraph_format.keep_together = True
        set_run(paragraph.add_run(text), size=9.2, color=BLACK)


def build():
    if not SOURCE_TEMPLATE.exists():
        raise FileNotFoundError(SOURCE_TEMPLATE)
    template_hash = sha256(SOURCE_TEMPLATE)
    if template_hash != EXPECTED_TEMPLATE_SHA256:
        raise RuntimeError(f"Report 2 template hash mismatch: {template_hash}")
    doc = Document(str(SOURCE_TEMPLATE))
    set_document_theme(doc)
    set_document_footers(doc)
    move_toc_to_its_own_page(doc)
    original_tables = list(doc.tables)
    if len(original_tables) != 9:
        raise RuntimeError(f"Expected 9 official Report 2 template tables; found {len(original_tables)}")
    change_log, wbs, quality, risks, training, deliverables, responsibility, communication, tools = original_tables

    doc.core_properties.title = "Sketch2Life Report 2 - Project Management Plan"
    doc.core_properties.subject = "SEP490 Project Management Plan and relative 15-week time plan"
    doc.core_properties.author = "Sketch2Life Team"
    doc.core_properties.keywords = "Sketch2Life, SEP490, Project Management Plan, WBS, time plan"
    insert_cover_metadata(doc)
    populate_content_paragraphs(doc)
    responsibility_heading = next(p for p in doc.paragraphs if p.text.strip() == "4. Responsibility Assignments")
    responsibility_heading.paragraph_format.page_break_before = True
    configuration_heading = next(p for p in doc.paragraphs if p.text.strip() == "6. Configuration Management")
    configuration_heading.paragraph_format.page_break_before = True

    set_existing_table(
        change_log,
        ["Date", "A/M/D", "In charge", "Change Description"],
        [("23/10/2026", "M", "Đỗ Cao Đạt", "Align Report 2 to the supplied course template; add current WBS, planning estimates, risks, ownership and relative time plan."),
         ("23/10/2026", "A", "Sketch2Life Team", "Add a standalone Report 2 draft and primary references for the proposed feature-based management approach.")],
        [0.78, 0.55, 1.15, 3.75],
        body_size=8.5,
        header_size=8.5,
    )

    wbs_rows = list(WBS_ROWS) + [("", "Total Estimated Effort (person-days)", "", str(TOTAL_EFFORT))]
    set_existing_table(wbs, ["#", "WBS Item", "Complexity", "Est. Effort\n(person-days)"], wbs_rows,
                       [0.44, 3.78, 1.00, 1.01], body_size=8.2, header_size=8.2, bold_first=True)
    for row_index, item in enumerate(wbs_rows[:-1], 1):
        if not item[2]:
            set_cell(wbs.rows[row_index].cells[1], item[1], size=8.2, bold=True)
    total_row = wbs.rows[-1]
    total_row.cells[0].merge(total_row.cells[2])
    set_cell(total_row.cells[0], "Total Estimated Effort (person-days)", size=8.2, bold=True, fill=PALE_TOTAL)
    set_cell(total_row.cells[3], str(TOTAL_EFFORT), size=8.2, bold=True, fill=PALE_TOTAL, align=WD_ALIGN_PARAGRAPH.CENTER)

    quality_rows = [
        ("1", "Reviewing", "100% of mandatory FRs and material contract/design changes reviewed", "TBD", "TBD", "Plan target; actual review/defect count not consolidated."),
        ("2", "Unit Test", "Critical domain rules, access decisions and main state transitions covered", "TBD", "TBD", "Target; no global coverage percentage claimed."),
        ("3", "Integration Test", "All versioned contracts, migration path and cross-service handoffs", "TBD", "TBD", "Requires agreed contract and migration order."),
        ("4", "System Test", "All four main workflows plus permission, recovery and failure paths", "TBD", "TBD", "Requires a repeatable staging environment."),
        ("5", "Acceptance Test", "At least 90% overall pass; 100% mandatory main flows; zero open Critical/High", "TBD", "TBD", "Course target for Defense readiness; not a current result."),
    ]
    set_existing_table(quality, ["#", "Testing Stage", "Test Coverage / Target", "No. of Defects", "% of Defect", "Notes"], quality_rows,
                       [0.32, 0.87, 2.23, 0.65, 0.62, 1.54], body_size=7.4, header_size=7.4)

    risk_rows = [
        ("1", "UI prototypes and service stubs lack one frozen shared contract; integration rework is likely.", "High", "High", "Freeze versioned API acceptance by W4-W5; run a contract test at each PR. Owner: Đạt."),
        ("2", "Independent Alembic heads do not yet have one approved deployment order; fresh staging may fail.", "High", "Medium", "Confirm schema owners and migration sequence; rehearse from an empty staging database before E2E. Owner: Khoa."),
        ("3", "Modal has no confirmed model, GPU, endpoint, region, scale, timeout or spend cap.", "High", "High", "Record profile and budget; use offline fixtures until approved provider tests are available. Owner: Hiếu."),
        ("4", "Child consent, data-purpose and retention evidence is incomplete across all product surfaces.", "High", "Medium", "Use synthetic data; obtain school procedure and test scope, audit, export/delete and 90-day session/artwork retention before pilot. Owner: Đạt/Khoa."),
        ("5", "252 person-day planning estimate has not been checked against four members' availability.", "High", "Medium", "Confirm capacity with each member and supervisor; inspect estimate variance weekly and request an approved schedule adjustment if needed. Owner: Đạt."),
    ]
    set_existing_table(risks, ["#", "Risk Description", "Impact", "Possibility", "Response Plans / Owner"], risk_rows,
                       [0.32, 1.72, 0.66, 0.78, 2.75], body_size=7.6, header_size=7.8)

    set_existing_table(training, ["Training Area", "Participants", "When / Duration", "Waiver Criteria / Evidence"], TRAINING_ROWS,
                       [1.65, 1.25, 1.42, 1.91], body_size=7.8, header_size=8.0)

    set_existing_table(deliverables, ["#", "Deliverable", "Due Window", "Notes"], DELIVERABLE_ROWS,
                       [0.34, 1.95, 0.82, 3.12], body_size=7.9, header_size=8.1)
    insert_time_plan(doc, deliverables)

    # The sample matrix has five member columns; the current registered team has four.
    for row in responsibility.rows:
        cells = row._tr.tc_lst
        if len(cells) == 6:
            row._tr.remove(cells[-1])
    grid_columns = responsibility._tbl.tblGrid.gridCol_lst
    if len(grid_columns) == 6:
        responsibility._tbl.tblGrid.remove(grid_columns[-1])
    set_existing_table(
        responsibility,
        ["Responsibility / Workflow", "Đạt\nSE193713", "Hiếu\nSE184252", "Bảo\nSE182733", "Khoa\nSE182682"],
        RACI_ROWS,
        [2.28, 1.00, 1.00, 1.00, 1.00],
        body_size=8.0,
        header_size=7.8,
        bold_first=True,
        center_columns=(1, 2, 3, 4),
    )

    set_existing_table(communication,
                       ["Communication Item", "Who / Target", "Purpose", "When / Frequency", "Type / Tool / Method"],
                       COMMUNICATION_ROWS, [1.05, 1.00, 1.55, 0.87, 1.81], body_size=7.6, header_size=7.4)

    set_existing_table(tools, ["Category", "Tools / Infrastructure / Status"], TOOLS_ROWS,
                       [1.55, 4.73], body_size=8.2, header_size=8.3, bold_first=True)

    process_image = add_process_diagram()
    insert_process_figure(doc, process_image)
    add_references(doc)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print(f"template_sha256={template_hash}")
    print(f"docx={OUT}")
    print(f"docx_sha256={sha256(OUT)}")
    print(f"estimated_effort_person_days={TOTAL_EFFORT}")
    print(f"schedule_rows={len(SCHEDULE_ROWS)}")
    print(f"raci_rows={len(RACI_ROWS)}")
    print(f"process_diagram={process_image}")
    return OUT


if __name__ == "__main__":
    build()
