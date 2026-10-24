from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from build_revision6_package import OUT, NAVY, WHITE, set_cell, shade, fit_table_widths


def build_bm01_formatted() -> Path:
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.27), Inches(11.69)
    section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Cm(2)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Arial", Pt(11)
    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.line_spacing = 1.0
    for name, size in (("Heading 1", 15), ("Heading 2", 12.5), ("Heading 3", 11)):
        style = doc.styles[name]
        style.font.name, style.font.size, style.font.bold = "Arial", Pt(size), True
        style.font.color.rgb = RGBColor.from_string(NAVY)
        style.paragraph_format.space_before, style.paragraph_format.space_after = Pt(5), Pt(2)
        style.paragraph_format.keep_with_next = True

    def text(value: str, *, size=11, bold=False, italic=False, center=False, page_break=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.page_break_before = bool(page_break)
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(value)
        run.font.name, run.font.size = "Arial", Pt(size)
        run.bold, run.italic = bold, italic
        return p

    def heading(value: str, level=2, page_break=False):
        p = doc.add_heading(value, level=level)
        p.paragraph_format.page_break_before = bool(page_break)
        p.paragraph_format.keep_with_next = True
        return p

    def table(headers, rows, widths):
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        t.autofit = False
        t.alignment = 1
        for i, value in enumerate(headers):
            set_cell(t.rows[0].cells[i], value, bold=True, color=WHITE, size=11)
            shade(t.rows[0].cells[i], NAVY)
        tr_pr = t.rows[0]._tr.get_or_add_trPr()
        repeat = OxmlElement("w:tblHeader")
        repeat.set(qn("w:val"), "true")
        tr_pr.append(repeat)
        for ri, values in enumerate(rows):
            cells = t.add_row().cells
            for i, value in enumerate(values):
                set_cell(cells[i], value, size=11)
                if ri % 2 == 0:
                    shade(cells[i], "F3F5F8")
        for row in t.rows:
            tr_pr = row._tr.get_or_add_trPr()
            if tr_pr.find(qn("w:cantSplit")) is None:
                tr_pr.append(OxmlElement("w:cantSplit"))
            for i, cell in enumerate(row.cells):
                cell.width = Inches(widths[i])
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(1)
                    p.paragraph_format.line_spacing = 1.0
        fit_table_widths(t, widths, max_width=6.55)
        doc.add_paragraph().paragraph_format.space_after = Pt(1)
        return t

    # BM01 required body: sections 0-8, in order, at 11 pt and 2 cm margins.
    text("SWP490  |  CAPSTONE PROJECT  |  REVIEW 2  |  BM01", size=9, bold=True, center=True)
    text("Design Brief", size=22, bold=True, center=True)
    text("Sketch2Life: Collaborative Creative Learning with AI for Children", size=12, bold=True, center=True)
    heading("0. Header")
    table(["Field", "Value"], [
        ("Project / class", "FA26SE225 (inferred from file name; confirm); class is blank in the supplied registration."),
        ("Team / roles", "Đạt SE193713, leader/full-stack; Hiếu SE184252, BE2; Bảo SE182733, FE; Khoa SE182682, BE1."),
        ("Supervisor", "Lâm Hữu Khánh Phương."),
        ("Repository / tag", "github.com/CaoDat-2410/Sketch2Life; local dev snapshot 0a7ce768; review-2 tag TBD."),
        ("Version / date", "Review 2 draft v1.1 | 23 October 2026 | Ho Chi Minh City."),
    ], [1.45, 5.25])

    heading("1. Scope")
    text("Registration changes: none proposed. Supplied v1.2 remains the scope authority; this brief makes classroom workflows and acceptance evidence explicit.")
    text("In scope: teacher-led classroom sessions for children aged 3-12; managed profiles and QR/session-code admission; individual/shared drawing; optional AI sketch suggestions; Teacher-reviewed knowledge/video; group activities, reflection and descriptive records. One class of up to 40 admitted children is a planning target, not measured capacity.")
    text("Out of scope: Parent portal, payments/credits, public social features, leaderboard, diagnostic inference and unapproved provider/storage adapters.")

    heading("2. System at a Glance")
    text("A Teacher configures a class session, admits children through managed profiles and controls each shared stage. Children draw individually or together, recover acknowledged work after reconnect, and may request optional AI help. The backend keeps original strokes separate from generated suggestions; a Teacher reviews an exact suggestion before the Child may view, hide or decline it. Teachers may present approved knowledge/video, choose a class or group activity, record descriptive observations and close only after durable save. Child identity is school-managed, not a separate login. AI provider calls stay server-side. Consent, class scope, provenance, retention and deletion guard protected data. Child, Teacher and Super Admin are separate client surfaces; current UIs use fixtures/stubs, so the complete flow remains a target rather than a verified release.")

    heading("3. Key Design Decisions", page_break=True)
    table(["ID", "Selected decision and reason", "Alternative / owner / trace"], [
        ("D1", "Durable classroom runtime is the product entrypoint; isolate process-local demos so restart and audit behavior are explicit.", "Demo-first rejected; Đạt; ADR-0019 / D08."),
        ("D2", "Teacher-managed child profiles and QR/code admission; no independent Child login or age inference from artwork.", "Child credentials rejected; Khoa; FR002-004 / UC01."),
        ("D3", "Accepted drawing operations keep sequence and contributor history; turn changes never rewrite earlier strokes.", "Last-writer-wins rejected; Bảo; FR033/066 / D05."),
        ("D4", "Teacher reviews each exact AI/media version; Child may view, hide or decline a safe approved suggestion.", "Auto-publish rejected; Hiếu; FR026-029 / D12."),
        ("D5", "Modal is selected for AI hosting; deployment, model, GPU, endpoint, region, scale and budget remain TBD.", "Profile required before acceptance; Hiếu; ADR-0019."),
    ], [0.45, 3.8, 2.45])

    heading("4. Top Risks")
    table(["ID", "Risk and impact", "Control / owner / gate"], [
        ("R1", "UI fixtures and service stubs may fail when integrated with backend contracts.", "Integrate one versioned workflow at a time; require staging E2E; Đạt + owners."),
        ("R2", "Nine migration roots have no approved clean-install order; a fresh environment may diverge.", "Agree schema ownership, upgrade/rollback order and disposable-database rehearsal; Khoa."),
        ("R3", "Modal has no deployment profile or measured latency/capacity; cost and availability are unknown.", "Approve model/GPU/region/timeout/budget and bounded acceptance profile; Hiếu."),
    ], [0.45, 3.2, 3.05])

    heading("5. Known Gaps")
    table(["ID", "Gap, evidence and closure action"], [
        ("G1", "Class and project-code fields are blank; confirm with supervisor/course record before submission. [SR-09]"),
        ("G2", "Child/Teacher/Admin services contain fixtures or stubs; version contracts and prove four end-to-end workflows. [SR-01, SR-10]"),
        ("G3", "HTTP composition still mounts demo/legacy routes; isolate demo entrypoints before staging. [SR-02]"),
        ("G4", "Nine migration roots and target/current state labels lack one approved crosswalk and release order. [SR-03, SR-04]"),
        ("G5", "Consent/purpose and 90-day session/artwork retention lack full derivative-copy purge evidence. [SR-05]"),
        ("G6", "Modal profile, 61-case commitment, 31 automated cases, staging workflows and 40-child capacity are unverified. [SR-06-08]"),
    ], [0.45, 6.25])

    heading("6. Mandatory Features", page_break=True)
    table(["ID", "Feature / actor", "Acceptance criterion (pass/fail)"], [
        ("MF-01", "Managed profile and session admission / Teacher, Child", "Valid roster join is admitted once; expired, wrong-class and duplicate requests are denied without membership."),
        ("MF-02", "Teacher-controlled class, group and session stages / Teacher", "Start, pause, resume and close persist; one ready group cannot advance the whole class."),
        ("MF-03", "Collaborative drawing and recovery / Child, Teacher", "Each accepted operation persists once with its contributor; reconnect restores acknowledged sequence without relabeling earlier work."),
        ("MF-04", "Reviewed AI sketch assistance / Child, Teacher, AI", "Pending, unsafe, stale or failed output stays hidden; only Teacher-approved exact version is available to Child choice."),
        ("MF-05", "Reviewed knowledge/video and failure choice / Teacher, Child", "Exact reviewed version is shown; after retry limit Teacher explicitly retries, skips or ends; skip is never playback."),
        ("MF-06", "Off-screen activity, reflection and descriptive record / Teacher, Child", "Teacher records class/group activity and observation without individual ranking or unsupported ability inference."),
    ], [0.55, 2.3, 3.85])

    heading("7. Non-Functional Requirements")
    table(["ID", "Metric / threshold", "Verification / status"], [
        ("NFR-01", "Accepted drawing acknowledgement p95 <= 500 ms at 40 synthetic children.", "Load profile; candidate target, not measured."),
        ("NFR-02", "Accepted peer update visible p95 <= 1 s at 40 synthetic children.", "Timed multi-client test; candidate target, not measured."),
        ("NFR-03", "100% unauthorized class/purpose requests denied; zero cross-class content leak.", "API/UI boundary negative suite; planned."),
        ("NFR-04", "100% acknowledged operations restored once after restart/reconnect; RPO/RTO TBD.", "Restart/replay suite; planned."),
        ("NFR-05", "Zero pending, stale, unsafe or unapproved version served to Child.", "Negative version/policy suite; planned."),
        ("NFR-06", "Session/artwork default purge at 90 days after session end; other data classes need policy.", "Clock-controlled retention/purge test; planned."),
    ], [0.65, 3.25, 2.8])
    text("All thresholds are proposed review targets, not observed results or guarantees.", italic=True)

    heading("8. Ownership Map")
    table(["Member / role", "Owned parts", "Main workflow / trace"], [
        ("Vũ Chí Bảo | FE", "Child Android screens, join/drawing interaction, acceptance", "WF-02; D2; FR014-021."),
        ("Đỗ Cao Đạt | Leader / Full-stack", "Cross-surface integration, requirements traceability, acceptance coordination", "WF-04; D1; FR031-048."),
        ("Phạm Tấn Hiếu | BE2", "AI job/provider boundary, sketch review, knowledge/video safety", "WF-03; D4/D5; FR022-030, 034-040."),
        ("Lý Anh Khoa | BE1", "Classroom API, persistence/migrations, session/recovery contract", "WF-01; D3; FR001-017."),
    ], [1.75, 2.8, 2.15])

    # Appendix A is outside the four-page limit stated for sections 0-8.
    text("Appendix A. Defense 1.1 Targets", size=15, bold=True, page_break=True)
    heading("A1. Main Workflows", level=3)
    table(["ID", "Workflow / actors", "Trigger and expected state change", "Presenter"], [
        ("WF-01", "Prepare and admit class session / Teacher, Child, Backend", "Teacher configures class; code join is checked; membership is admitted; Session Lobby -> Active.", "Khoa"),
        ("WF-02", "Draw and recover shared canvas / Child, Teacher, Backend", "Accepted operations advance canvas revision; reconnect replays accepted sequence; attribution is preserved.", "Bảo"),
        ("WF-03", "Request and review AI sketch / Child, Teacher, AI service", "A scoped job becomes a reviewed proposal; Child choice is recorded; source artwork remains unchanged.", "Hiếu"),
        ("WF-04", "Review learning/video and close / Teacher, Child, media service", "Exact reviewed media or explicit skip is recorded; activity/observation saves before session close.", "Đạt"),
    ], [0.55, 2.0, 3.5, 0.65])
    text("Each workflow involves multiple actors and changes a main entity. The demo scenarios below are planned, not completed demonstrations.", italic=True)
    heading("A2. Demo Scenarios", level=3)
    table(["ID", "Path", "Scenario / expected result", "Presenter"], [
        ("DS-01", "WF-01 main", "Teacher admits valid synthetic profile; both surfaces show active membership.", "Khoa"),
        ("DS-02", "WF-01 exception", "Expired/wrong-class code is denied; no membership is created.", "Khoa"),
        ("DS-03", "WF-02 main", "Two synthetic clients draw; Teacher pauses/resumes and contributor history remains.", "Bảo"),
        ("DS-04", "WF-02 exception", "Retry replays once; conflicting operation is rejected without duplicate canvas mutation.", "Bảo"),
        ("DS-05", "WF-03 main", "Teacher approves exact sketch; Child may view/hide/decline; original strokes remain.", "Hiếu"),
        ("DS-06", "WF-03 exception", "Unsafe/stale result is unavailable and typed failure is visible to Teacher.", "Hiếu"),
        ("DS-07", "WF-04 main", "Teacher approves video, guides activity and saves descriptive observation.", "Đạt"),
        ("DS-08", "WF-04 exception", "After retries, Teacher skips; video is not marked played and work is saved.", "Đạt"),
    ], [0.55, 1.1, 4.4, 0.65])
    heading("A3. Functional Test Case Target", level=3)
    table(["Source", "Count", "Minimum / item", "Target"], [
        ("Mandatory features", "6", "3", "18"),
        ("Main workflows", "4", "1", "4"),
        ("Legal main-state transitions", "29", "1", "29"),
        ("Illegal transition rejection", "4", "1", "4"),
        ("Measurable candidate NFRs", "6", "1", "6"),
        ("Total proposed cases", "", "", "61"),
        ("Automated in CI", "At least 50%", "round up", "31"),
    ], [2.5, 1.0, 1.5, 1.7])
    text("The Review 2 team and reviewers must confirm the final target. These cases have not been run against staging.", italic=True)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer_run = footer.add_run("Sketch2Life | Review 2 | BM01")
    footer_run.font.name, footer_run.font.size = "Arial", Pt(8)
    output = OUT / "SWP490_FA26SE225_R2_DesignBrief.docx"
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    return output
