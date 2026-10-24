"""Refresh the four Review 2 dossiers from Rev7 without changing source baselines."""

from __future__ import annotations

import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from PIL import Image


FEATURE = Path(__file__).resolve().parents[1]
REPO = FEATURE.parents[1]
SOURCE = FEATURE / "artifacts" / "submission_r2_rev7"
OUTPUT = FEATURE / "artifacts" / "submission_r2_rev11"
EXPORTS = FEATURE / "evidence" / "render" / "rev11" / "supplied-diagrams-clean"
NEW_PAGES = FEATURE / "evidence" / "render" / "rev11" / "diagrams"
DIAGRAM_MASTER = FEATURE / "artifacts" / "diagrams" / "rev11" / "drawio" / "Sketch2Life-Review2-Diagram-Master.drawio"

NAMES = {
    "brief": "SWP490_FA26SE225_R2_DesignBrief",
    "registration": "SWP490_FA26SE225_R2_Registration",
    "report": "SWP490_FA26SE225_R2_Report1-5_Tracking",
    "selfreview": "SWP490_FA26SE225_R2_SelfReview",
}


def text_of(cell) -> str:
    return " ".join(cell.text.split())


def set_cell(cell, text: str) -> None:
    cell.text = text
    for p in cell.paragraphs:
        for run in p.runs:
            run.font.name = "Arial"


def set_row(table, row_index: int, values: list[str]) -> None:
    row = table.rows[row_index]
    if len(row.cells) != len(values):
        raise ValueError(f"row {row_index}: expected {len(row.cells)} cells, got {len(values)}")
    for cell, value in zip(row.cells, values):
        set_cell(cell, value)


def insert_row(table, row_index: int, values: list[str]) -> None:
    template = table.rows[max(0, row_index - 1)]
    cloned = deepcopy(template._tr)
    if row_index < len(table.rows):
        table.rows[row_index]._tr.addprevious(cloned)
    else:
        table._tbl.append(cloned)
    set_row(table, row_index, values)


def replace_text_everywhere(doc, replacements: dict[str, str]) -> None:
    for paragraph in doc.paragraphs:
        text = paragraph.text
        for old, new in replacements.items():
            text = text.replace(old, new)
        if text != paragraph.text:
            paragraph.text = text
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text
                for old, new in replacements.items():
                    text = text.replace(old, new)
                if text != cell.text:
                    set_cell(cell, text)


def find_paragraph(doc, prefix: str):
    for paragraph in doc.paragraphs:
        if paragraph.text.strip().startswith(prefix):
            return paragraph
    raise KeyError(f"paragraph not found: {prefix}")


def set_paragraph(doc, prefix: str, text: str) -> None:
    paragraph = find_paragraph(doc, prefix)
    paragraph.text = text


def field(paragraph, instruction: str) -> None:
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    begin.set(qn("w:dirty"), "true")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Updating table of contents…"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run = OxmlElement("w:r")
    run.append(begin)
    paragraph._p.append(run)
    run = OxmlElement("w:r")
    run.append(instr)
    paragraph._p.append(run)
    run = OxmlElement("w:r")
    run.append(separate)
    run.append(placeholder)
    paragraph._p.append(run)
    run = OxmlElement("w:r")
    run.append(end)
    paragraph._p.append(run)


def install_toc(doc) -> None:
    paragraph = find_paragraph(doc, "Update this table of contents")
    paragraph.clear()
    field(paragraph, 'TOC \\o "1-2" \\h \\z \\u')
    settings = doc.settings._element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "true")


def update_properties(doc, title: str, subject: str) -> None:
    doc.core_properties.title = title
    doc.core_properties.subject = subject
    doc.core_properties.keywords = "Sketch2Life, Review 2, SRS v3.3, SDD, current-state evidence"
    doc.core_properties.comments = "Review 2 draft; current-state limits and unconfirmed planning proposals are stated explicitly."


def refresh_registration() -> None:
    path = OUTPUT / f"{NAMES['registration']}.docx"
    doc = Document(path)
    replacements = {
        "FA26SE225 (inferred from filename; confirm)": "FA26SE225 (administrative project identifier from the submitted project record)",
        "BM03 v1.0": "BM03 v1.1",
        "23 October 2026": "24 October 2026",
    }
    replace_text_everywhere(doc, replacements)
    bm03 = doc.tables[3]
    set_row(bm03, 0, ["Project code", "FA26SE225 (administrative identifier from submitted project record)"])
    insert_row(bm03, 1, ["Class", "SWP490 (course/class identifier from the official Review 2 guide)"])
    set_row(bm03, 7, ["Version", "BM03 v1.1"])
    set_row(bm03, 8, ["Date", "24 October 2026"])
    set_row(doc.tables[4], 1, [
        "—", "All sections", "Supplied registration v1.2", "No changes proposed",
        "SRS v3.3/B28 refines current policies without replacing the registered project scope. FA26SE225 and SWP490 are included as administrative identifiers; the original registration form is preserved, and reviewer disposition remains blank for Review 2.",
        "Project owner",
    ])
    update_properties(doc, "Sketch2Life Review 2 Registration and BM03", "Owner-selected registration v1.2 and no-change record")
    doc.save(path)


DEMO_SCENARIOS = [
    ["DS-01", "WF-01 main", "Preconditions / synthetic data: assigned class C-TEST; draft session S-01; managed profile P-01; valid join code J-01.\nSteps: Teacher configures the session and opens the lobby; Child submits J-01; Teacher checks the roster and admits P-01; Teacher explicitly starts.\nExpected observable result: one active membership, scoped device grant and active session appear on the two surfaces; no duplicate member is created.", "Khoa"],
    ["DS-02", "WF-01 exception", "Preconditions / synthetic data: class C-TEST; expired code J-OLD and wrong-class code J-OTHER; no membership for P-02.\nSteps: Submit each code for P-02; inspect Teacher roster and backend result after each request.\nExpected observable result: both requests are denied with safe reasons; P-02 remains absent and no device grant or membership is persisted.", "Khoa"],
    ["DS-03", "WF-02 main", "Preconditions / synthetic data: active session S-02; admitted profiles P-01/P-02; shared canvas revision 0; synthetic stroke IDs OP-01/OP-02.\nSteps: Both Children submit a stroke; Teacher pauses and resumes; reconnect one client from its last acknowledged sequence.\nExpected observable result: each accepted operation appears once with its original contributor and sequence; reconnect restores the acknowledged canvas; pause/resume does not rewrite attribution.", "Bảo"],
    ["DS-04", "WF-02 exception", "Preconditions / synthetic data: active session S-03; canvas revision 4; OP-03 is pending and OP-CONFLICT reuses a prior operation ID with a different payload.\nSteps: Replay OP-03 after reconnect; submit the conflicting duplicate; inspect receipt and canvas revision.\nExpected observable result: the identical retry returns the original durable receipt and mutates once; the conflicting duplicate is rejected without changing saved canvas state.", "Bảo"],
    ["DS-05", "WF-03 main", "Preconditions / synthetic data: Child artwork version ART-01; allowed group purpose; synthetic safe suggestion SK-01; Teacher review authority.\nSteps: Child requests assistance; Teacher reviews the exact source hash and approves SK-01; Child views, hides, then declines the suggestion.\nExpected observable result: approval is tied to the reviewed version; Child choice is recorded; original strokes and artwork remain unchanged.", "Hiếu"],
    ["DS-06", "WF-03 exception", "Preconditions / synthetic data: jobs JOB-STALE and JOB-UNSAFE with a changed source hash and an unsafe typed result.\nSteps: Return each result to the review flow; inspect Child availability and Teacher status.\nExpected observable result: neither result is exposed to Child; the stale/unsafe reason is typed and visible to Teacher; source artwork remains intact.", "Hiếu"],
    ["DS-07", "WF-04 main", "Preconditions / synthetic data: approved media version VID-01 for class C-TEST; reviewed activity ACT-01; descriptive observation OBS-01.\nSteps: Teacher checks the exact audience/version and approves playback; facilitates the off-screen activity; records OBS-01 and saves the session outcome.\nExpected observable result: only VID-01 is played; activity, descriptive observation and outcome are persisted before session closure; no diagnostic inference is produced.", "Đạt"],
    ["DS-08", "WF-04 exception", "Preconditions / synthetic data: media job JOB-FAIL has exhausted retries; approved alternate media absent; session S-04 has saved work.\nSteps: Teacher reviews the typed failure and explicitly selects Skip; inspect playback and session outcome records.\nExpected observable result: skip disposition is recorded; no video is marked played; completed work remains and the session records the selected non-success outcome.", "Đạt"],
]


STATE_CROSSWALK = [
    ["Session lifecycle", "draft → scheduled; scheduled → lobby", "completed → active"],
    ["Shared learning stage", "preparation → join; join → explore_draw", "completion → active"],
    ["Group progress", "waiting → exploring; drawing → reviewing", "finished → drawing"],
    ["Admission", "pending → admitted; admitted → left", "expired → admitted"],
    ["Device connection", "connecting → authenticated; resyncing → connected", "revoked → connected"],
    ["Draft sync", "local_only → queued; sent_unacknowledged → accepted_durable", "quarantined → accepted_durable"],
    ["Sketch pipeline", "requested → analyzing; pending_teacher_review → approved", "blocked_unsafe → approved"],
    ["Child suggestion response", "available → viewed; viewed → hidden", "declined → available for the same version"],
    ["Knowledge editorial", "draft → in_review; in_review → approved_for_render", "withdrawn → in_review"],
    ["Media job", "queued → running; running → succeeded", "failed_exhausted → running on the same job"],
    ["Video delivery", "generating → ready_for_review; ready_for_review → approved", "skipped_by_teacher → playing"],
    ["Activity execution", "proposed → teacher_selected; preparation_required → ready", "completed → in_progress"],
    ["Observation", "draft → ai_suggested; ai_suggested → teacher_confirmed", "withdrawn → teacher_confirmed"],
    ["Content publication", "submitted → published; published → recalled", "recalled → published without a revised version"],
    ["Data request", "received → identity_check; scope_review → approved", "rejected → approved without a new review"],
]


def refresh_bm01() -> None:
    path = OUTPUT / f"{NAMES['brief']}.docx"
    doc = Document(path)
    replace_text_everywhere(doc, {
        "FA26SE225 (inferred from file name; confirm); class is blank in the supplied registration.": "FA26SE225 (administrative project identifier); SWP490 (course/class identifier). The submitted v1.2 registration is preserved unchanged.",
        "Review 2 draft v1.1 | 23 October 2026": "Review 2 draft v1.2 | 24 October 2026",
        "SRS v3.1": "SRS v3.3",
    })
    set_row(doc.tables[0], 1, ["Project / class", "FA26SE225 (administrative project identifier); SWP490 (course/class identifier). The submitted v1.2 form remains unchanged."])
    set_row(doc.tables[0], 4, ["Repository / tag", "github.com/CaoDat-2410/Sketch2Life; current dev baseline. The official review-2 tag/BM02 gate is run only after CI, Iteration 1, document QA, clean-tree and security gates pass."])
    set_row(doc.tables[0], 5, ["Version / date", "Review 2 draft v1.2 | 24 October 2026 | Ho Chi Minh City."])
    set_paragraph(doc, "Registration changes:", "Registration changes: none proposed. The submitted v1.2 form remains the scope authority; BM03 records no scope change. Administrative identifiers FA26SE225 (submitted project record) and SWP490 (official course/class guide) are carried separately from the original form fields.")
    set_paragraph(doc, "In scope:", "In scope: teacher-led sessions for children ages 3–12; managed profiles and QR/code admission; individual/shared drawing; reviewed AI sketches and media; off-screen group activities, reflection and descriptive records. WF-01/WF-02 have local wiring and separate checks; database-backed end-to-end acceptance is still open. WF-03/WF-04 remain gated.")
    set_paragraph(doc, "A Teacher configures", "A Teacher configures a class session, admits managed Child profiles, and controls the stages. Children draw individually or together and recover accepted work after reconnect; AI assistance and reviewed video remain policy-gated. The current repository has local WF-01/WF-02 connections, but no PostgreSQL-backed FE-to-BE acceptance; WF-03/WF-04 have no accepted classroom integration.")
    set_paragraph(doc, "All thresholds are proposed", "Thresholds are candidate targets only. The 40-child pilot target is not a hard join cap and has not been measured; privacy, recovery and latency results are not yet established.")
    set_paragraph(doc, "Each workflow involves", "The four workflows map to four activity diagrams in the Draw.io appendix. WF-03/WF-04 diagrams are target designs, not completed demonstrations.")
    for table in doc.tables:
        if table.rows and any(cell.text.strip() == "Presenter" for cell in table.rows[0].cells):
            for cell in table.rows[0].cells:
                if cell.text.strip() == "Presenter":
                    set_cell(cell, "Lead")
    for i, scenario in enumerate(DEMO_SCENARIOS, start=1):
        set_row(doc.tables[8], i, scenario)
    # Current top risks.
    t = doc.tables[2]
    set_row(t, 1, ["R1", "Nine Alembic heads have no approved clean-install/upgrade/rollback path; database-backed acceptance cannot be repeated.", "Keep N1 and approve lineage/rollback before isolated DB acceptance; owner and procedure TBD."])
    set_row(t, 2, ["R2", "WF-01/WF-02 are locally wired, but four PostgreSQL acceptance cases were skipped because BE1_TEST_DATABASE_URL is unset; device/network acceptance is also open.", "Keep N2–N4 in dependency order; review BE1 contracts, then run synthetic DB and device acceptance; operator/matrix TBD."])
    set_row(t, 3, ["R3", "Child-data consent/deletion evidence and production Modal/artifact-storage profiles are incomplete; no pilot or capacity result is evidenced.", "Keep N7 as a pre-pilot gate; defer N5/N6/N9 until contracts/runtime are approved; exact policies, service owners and cost limits TBD."])
    gaps = [
        ["ID", "Gap, evidence and closure action"],
        ["G1", "The submitted registration v1.2 remains unchanged. Administrative identifiers FA26SE225 and SWP490 are recorded from the submitted project record and official course guide; the official tagged-baseline BM02 gate remains pending."],
        ["G2", "Alembic has nine heads and no approved consolidated install/upgrade/rollback path; four PostgreSQL cases skipped without BE1_TEST_DATABASE_URL. N1/N3."],
        ["G3", "BE1 route, transaction, authorization, receipt, join-code/key lifecycle, IP trust/throttle and concurrency review remains open. N2."],
        ["G4", "WF-01/WF-02 passed separate local UI/backend checks but have no DB-backed FE-to-BE or device/network acceptance. N3/N4."],
        ["G5", "WF-03/WF-04 remain gated by FEAT-057 contracts; production Firebase login, Modal profile and artifact storage are not evidenced. N5/N6."],
        ["G6", "Consent, purpose, retention, derivative-copy purge and the 40-child workload target remain unverified; 40 is not a hard join limit. N7/N9."],
    ]
    for i, row in enumerate(gaps):
        set_row(doc.tables[3], i, row)
    set_paragraph(doc, "The Review 2 team and reviewers", "Proposed planning target only—not a measured suite or an instructor-approved commitment: 18 mandatory-feature rows + 4 workflow rows + 6 candidate NFR rows + 30 representative legal transitions + 15 rejected transitions = 73 cases. The crosswalk below selects two legal and one negative example per B19.4 registry; owners must confirm these examples and add any omitted guards. No staging result is claimed.")
    a3 = doc.tables[9]
    rows = [
        ["Source", "Count", "Minimum / item", "Target"],
        ["Mandatory features", "6", "3", "18"],
        ["Main workflows", "4", "1", "4"],
        ["Candidate measurable NFR rows", "6", "1", "6"],
        ["Representative legal state transitions", "15 registries", "2 per registry", "30"],
        ["Rejected / illegal state transitions", "15 registries", "1 per registry", "15"],
        ["Total proposed target", "", "18 + 4 + 6 + 30 + 15", "73 planning cases"],
        ["Automated-in-CI planning floor", "≥50% of target", "round up", "37 proposed cases"],
    ]
    for i, row in enumerate(rows):
        set_row(a3, i, row)
    planning_note = next((p for p in doc.paragraphs if p.text.strip().startswith("Planning arithmetic only:")), None)
    if planning_note is not None:
        planning_note._element.getparent().remove(planning_note._element)
    # Keep the appendix target matrix compact so it remains together on page 4.
    for row in a3.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
                for run in paragraph.runs:
                    run.font.size = Pt(8.5)
    for paragraph in doc.paragraphs:
        if paragraph.text.strip().startswith("Appendix A. Defense 1.1 Targets"):
            paragraph.paragraph_format.page_break_before = False
    heading = doc.add_paragraph("A3.1. Representative lifecycle transition crosswalk", style="Heading 3")
    heading.paragraph_format.keep_with_next = True
    note = doc.add_paragraph("Illustrative acceptance candidates from SRS v3.3/B19.4; the route/DTO owner must confirm each legal and rejected transition before implementation. This is not an exhaustive transition matrix or runtime evidence.")
    note.paragraph_format.keep_with_next = True
    crosswalk = doc.add_table(rows=1, cols=4)
    crosswalk.style = "Table Grid"
    for i, value in enumerate(["Registry", "Representative legal transition 1", "Representative legal transition 2", "Rejected transition"]):
        set_cell(crosswalk.rows[0].cells[i], value)
    header = crosswalk.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    header.append(repeat)
    for registry, legal, rejected in STATE_CROSSWALK:
        row = crosswalk.add_row()
        values = [registry, *legal.split("; "), rejected]
        for i, value in enumerate(values): set_cell(row.cells[i], value)
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs: run.font.size = Pt(8)
    update_properties(doc, "Sketch2Life Review 2 Design Brief", "BM01 Design Brief and Appendix A")
    doc.save(path)


CURRENT_FINDINGS = [
    ("SR-01", "Flows", "apps/child-ui; apps/teacher-ui; backend/tests/integration/test_be1_postgres_api.py", "Local WF-01/WF-02 wiring now covers join, roster/session controls, acknowledged drawing and reconnect/replay paths. Separate Child and Teacher checks passed, but four PostgreSQL cases were skipped without BE1_TEST_DATABASE_URL; no database-backed FE-to-BE acceptance receipt exists.", "High", "FEAT-060 status: Child 18 suites/26 tests; Teacher 3 suites/6 tests; focused backend 22 passed and four PostgreSQL cases skipped. Mocked UI checks plus backend checks run separately do not prove a durable end-to-end workflow.", "PLANNED proposal — Keep N3 after N1/N2. Proposed owner: Lý Anh Khoa (BE1), with a separate DB operator to confirm. Proposed target: 09 Nov 2026, subject to isolated synthetic environment and N1/N2 approval; thresholds and operator TBD."),
    ("SR-02", "Data / migrations", "backend/alembic/versions; backend/alembic/README.md; FEAT-060 status", "The current BE1 classroom migration chains from revision 20261014_0004, while Alembic reports nine independent heads overall. A clean all-module install, upgrade, and rollback lineage has not been approved.", "High", "FEAT-060 records one BE1 head plus eight independent feature heads and no approved consolidated install/upgrade/rollback path.", "PLANNED proposal — Keep N1. Proposed owner: Lý Anh Khoa (BE1 migration work); proposed approver: DB/project owner TBD. Target: 02 Nov 2026 for a delivery-path inventory and rollback proposal; approval remains outstanding."),
    ("SR-03", "Security / contracts", "backend/src/sketch2life/interfaces/http/routers/be1_sessions.py; be1_canvas.py; FEAT-060 review gates", "The local classroom routes implement room-code, admission/start, stage and receipt behavior, but BE1 review remains open for transaction races, authorization, idempotency/receipt details, join-code key lifecycle, trusted-proxy IP attribution and cross-replica throttling.", "High", "FEAT-060 status lists these as remaining BE1 owner review gates. SRS B28 defines product decisions; route/DTO and production guard details still need contract approval.", "PLANNED proposal — Keep N2 before DB acceptance. Proposed owner: Lý Anh Khoa (BE1), with Đỗ Cao Đạt as cross-surface reviewer. Target: 04 Nov 2026 for a review package; DTO/version and independent approver TBD."),
    ("SR-04", "States / design-to-code", "SRS v3.3 B19.4; Report 4 state inventory; backend/src/sketch2life/infrastructure/persistence/be1_models.py", "The SRS defines fifteen lifecycle registries. The imported Draw.io diagrams are target models; persisted BE1 wire states and feature-owned AI/media states need an approved crosswalk and transition-negative coverage. A diagram does not prove implementation.", "High", "The current BE1 session enum includes configured/lobby/active/paused/finished; several SRS outcomes and other registries have separate policy or module boundaries. FEAT-060 keeps early-end, forward-only and save-draft rules, while exact contract mapping remains review work.", "PLANNED proposal — Keep N2 state reconciliation. Proposed owners: Lý Anh Khoa for BE1 wire states; Phạm Tấn Hiếu for BE2; other registry owners TBD. Target: 06 Nov 2026 for the first crosswalk; no runtime transition coverage is claimed."),
    ("SR-05", "Privacy / child data", "SRS v3.3 B19/B24/B28; registration v1.2; FEAT-060 status", "Consent is fail-closed locally, but a complete child-data lifecycle—purpose proof, class-specific retention, derivative/shared-copy inventory, export/deletion, external purge, backup expiry and audit—is not demonstrated for a pilot.", "High", "FEAT-060 records no complete live consent/deletion flow; the registration sets 90-day session/artwork retention while other data classes have separate open policies.", "PLANNED proposal — Keep N7 as a pre-pilot gate. Proposed coordinator: Đỗ Cao Đạt; institutional/legal approver remains TBD. Proposed target: 13 Nov 2026 for a policy/evidence checklist; no child-data pilot until authority approves."),
    ("SR-06", "Flows / external services", "FEAT-057 status; ADR-0019; runtime configuration", "WF-03/WF-04 remain gated by FEAT-057 adoption and versioned cross-feature contracts. Modal is selected as a host, but no product Modal profile or production artifact-storage profile is evidenced; live AI/media workflow acceptance is absent.", "High", "FEAT-060 records partial/gated FEAT-057 slices, no adopted finalization/execution authority for related lanes, no deployed Modal profile and no production artifact store.", "PLANNED proposal — Defer N5/N6 until versioned contract and data-boundary decisions. Proposed owner: Phạm Tấn Hiếu (BE2), with P4 integration allocation separately approved. Target: 20 Nov 2026 for a decision package only; provider/storage settings and approver TBD."),
    ("SR-07", "Recovery / device acceptance", "FEAT-060 status; apps/child-ui/src/services/sessionClient.ts; device test evidence", "The code and local checks cover reconnect/replay paths, but QR/deep-link behavior, real network loss, process restart, two-device concurrency and restoration of durable acknowledgements have not been accepted on supported devices.", "High", "FEAT-060 explicitly reports no physical-device QR/deep-link or database-backed acceptance run.", "PLANNED proposal — Keep N4 after or alongside N3. Proposed owner: Vũ Chí Bảo (FE/device path), with Khoa supporting backend receipts. Target: 13 Nov 2026, subject to N1/N2 and the confirmed device matrix."),
    ("SR-08", "Capacity / NFR", "SRS v3.3 B17/B20/B25; BM01 candidate NFRs", "The one-class target of up to forty children is unmeasured. Candidate latency and recovery thresholds do not establish achieved capacity and must not become a join cap without a new decision.", "Medium", "FEAT-060 labels forty as an unmeasured pilot target, not a hard admission limit; no load profile or result is registered.", "PLANNED proposal — Defer N9 until N3/N6. Proposed measurement owner: Lý Anh Khoa (DB harness) with Phạm Tấn Hiếu (runtime profile) after a new integration allocation. Target: 30 Nov 2026; workload, thresholds and cost cap TBD."),
    ("SR-09", "Metadata / review gate", "selected registration v1.2; Review 2 guide; current Git refs", "Administrative identifiers FA26SE225 and SWP490 are recorded from the submitted project record and official guide. The required review-2 tag is not yet present; this report is not a completed tagged-baseline run.", "Medium", "Selected registration v1.2 remains unchanged; owner authorized normal commit/push and a review-2 tag/BM02 run only after CI, Iteration 1, document QA, clean-tree and security gates pass.", "PLANNED proposal — Keep the release gate. Proposed release coordinator: Đỗ Cao Đạt; course/repository tag acceptance owner TBD. Target: after all named gates pass (proposed 04 Dec 2026, not a committed date). No tag is created by this report build."),
    ("SR-10", "Architecture / runtime", "backend/src/sketch2life/classroom_main.py; demo_main.py; apps/admin-ui; runtime configuration", "Classroom-only and demo-only backend compositions now exist locally, and Admin has a local Firebase/BE1 role gate. The deployed entrypoint, live adult Firebase login, production authorization configuration and service isolation have not been demonstrated.", "Low", "FEAT-060 records separate app compositions and an Admin gate; status explicitly says no live Firebase login or deployment acceptance.", "PLANNED proposal — Retain local compositions. Proposed technical coordination owner: Đỗ Cao Đạt; product/runtime approvers TBD. Target: 20 Nov 2026 for an entrypoint/profile review after environment decisions; no deployment is proposed here."),
]


def refresh_bm02() -> None:
    path = OUTPUT / f"{NAMES['selfreview']}.docx"
    doc = Document(path)
    replace_text_everywhere(doc, {
        "23 October 2026": "24 October 2026",
        "Draft self-review v1.0": "Draft self-review v1.2",
        "SR-01": "SR-01",
    })
    t0 = doc.tables[0]
    set_row(t0, 0, ["Project code", "FA26SE225 (administrative identifier from the submitted project record)"])
    insert_row(t0, 1, ["Class", "SWP490 (course/class identifier from the official Review 2 guide)"])
    set_row(t0, 6, ["Run date", "24 October 2026"])
    set_row(t0, 7, ["Repository tag / commit", "Review 2 tag is pending CI, Iteration 1, document QA, clean-tree and security gates. This current source review is not the guide's tagged-baseline run."])
    set_row(t0, 8, ["Registration form version used", "Owner-selected Phieu_FA26SE225_v1.2; original file preserved unchanged."])
    set_row(t0, 9, ["Version", "Draft self-review v1.2; tagged-baseline execution pending gates"])
    set_row(t0, 10, ["Date", "24 October 2026"])
    findings = doc.tables[2]
    for i, item in enumerate(CURRENT_FINDINGS, start=1):
        set_row(findings, i, list(item))
    top = doc.tables[3]
    for i, item in enumerate(CURRENT_FINDINGS[:5], start=1):
        set_row(top, i, [str(i), item[0], item[3]])
    sev = {"High": 7, "Medium": 2, "Low": 1}
    set_row(doc.tables[4], 1, ["High", str(sev["High"]), "0", "0", "7"])
    set_row(doc.tables[4], 2, ["Medium", str(sev["Medium"]), "0", "0", "2"])
    set_row(doc.tables[4], 3, ["Low", str(sev["Low"]), "0", "0", "1"])
    set_paragraph(doc, "Summary.", "Summary. This source review reports 7 High, 2 Medium and 1 Low finding. Each response is a proposed Keep/Defer action with a suggested owner and target date for the owner/team to confirm; none is marked Fixed or accepted. WF-01/WF-02 have local wiring and separate checks, but database-backed end-to-end acceptance remains open; WF-03/WF-04 remain gated. The official `review-2` tag run remains conditional on CI, Iteration 1, document QA, clean-tree and security gates.")
    update_properties(doc, "Sketch2Life Review 2 Self-Review", "BM02 evidence-based draft; tagged-baseline execution is gated")
    doc.save(path)


def update_report_tables(doc) -> None:
    t = doc.tables
    revision = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    # Project identity and snapshot.
    set_row(t[4], 3, ["Project reference", "FA26SE225 — administrative identifier from the submitted project record; the selected registration v1.2 is preserved unchanged."])
    set_row(t[4], 4, ["Class", "SWP490 — course/class identifier from the official Review 2 guide."])
    set_row(t[4], 6, ["Document snapshot", f"dev@{revision}; current implementation and repository evidence reviewed on this commit. This is not a release or tagged-baseline run."])
    set_row(t[4], 7, ["Review tag", "review-2: pending the approved CI, Iteration 1, document QA, clean-tree and security gates; BM02 must be run on the tag only after they pass."])
    set_row(t[57], 1, ["dev", revision, "Source baseline reviewed for this dossier; official review-2 tag/BM02 gate remains conditional on all documented gates passing."])
    # The 61-row inventory is a draft candidate list, not an approved or executed target.
    set_row(t[55], 1, ["Functional count", "Proposed 73-case planning target: 18 feature + 4 workflow + 6 candidate NFR + 30 legal transitions + 15 rejected transitions.", "Not instructor-approved or measured; transition crosswalk and acceptance set require owner review."])
    set_row(t[55], 2, ["Main workflows", "Target: all four agreed workflows complete end-to-end on staging.", "No full staging E2E receipt; WF-03/WF-04 remain gated."])
    set_row(t[55], 3, ["Exception scenarios", "Proposed minimum: one rejected transition per each of fifteen B19.4 registries, plus feature/workflow exceptions.", "Illustrative crosswalk only; owners must add other guards and confirm legal transitions."])
    set_row(t[55], 4, ["Total pass rate", "Set after the accepted test set and fixed environment are approved.", "No approved denominator or baseline result."])
    set_row(t[55], 5, ["Defects", "No open Critical or High defect at Defense 1.1; accepted defect register required.", "Consolidated current defect register and accountable owner are not evidenced."])
    set_row(t[55], 6, ["NFRs", "Run each agreed metric with a named environment and profile.", "Latency, recovery and 40-child capacity remain unmeasured; N9 deferred."])
    for row in t[53].rows[1:]:
        set_cell(row.cells[5], "Candidate target only")
    # Surface and scope current state.
    set_row(t[6], 1, ["Child", "apps/child-ui; Expo SDK 55, React Native 0.83.10", "FEAT-060 local join, refresh, reconnect/replay and acknowledged-stroke paths; check passed 18 suites/26 tests. Mocked UI checks; no DB-backed FE-to-BE acceptance or device run."])
    set_row(t[6], 2, ["Teacher", "apps/teacher-ui; React + Vite", "Local class/lobby/roster/group/turn/stage and observation paths; check passed 3 suites/6 tests. No PostgreSQL-backed UI workflow acceptance."])
    set_row(t[6], 3, ["Super Admin", "apps/admin-ui; React + Vite", "Local Firebase/BE1 role gate and class list/create path exist; live Firebase login and deployment authorization are not evidenced."])
    set_row(t[6], 4, ["Backend", "FastAPI classroom/demo compositions, PostgreSQL adapters and module-owned migrations", "Focused local BE1 checks pass; four PostgreSQL cases skipped without BE1_TEST_DATABASE_URL. Nine Alembic heads have no approved consolidated install/rollback plan."])
    set_row(t[6], 5, ["AI hosting", "Modal selected by owner", "No configured/deployed product profile, live call, production storage profile, latency or capacity result is evidenced; values remain TBD."])
    set_row(t[7], 1, ["Child Android app; Teacher Desktop; Super Admin Console", "Separate surfaces exist; local WF-01/WF-02 wiring is checked independently but database-backed integrated release is not demonstrated."])
    set_row(t[7], 3, ["Personal/shared drawing, AI suggestion review, gallery, knowledge/video, off-screen activities, reflection and progress", "WF-01/WF-02 local paths do not close PostgreSQL/device acceptance. WF-03/WF-04 remain gated by FEAT-057 and runtime/data policy decisions."])
    set_row(t[14], 3, ["Versioned SRS/SDD and editable diagrams", "SRS v3.3/B28 is the current requirements baseline; all fifteen B19.4 lifecycle registries and WF-01–WF-04 activity diagrams are represented in the editable Rev11 Draw.io master and report appendix. Each page is labeled by diagram type; canvases contain no source attribution."])
    set_row(t[14], 4, ["Child / Teacher / Admin applications and backend", "Local FEAT-060 implementation is documented; WF-01/WF-02 remain unaccepted against PostgreSQL/devices; WF-03/WF-04 and live services are gated."])
    set_row(t[14], 5, ["Test evidence", "Historical FEAT-060 checks: Child 18 suites/26 tests; Teacher 3 suites/6 tests; backend 22 passed and four PostgreSQL cases skipped. No tests rerun for this documentation task."])
    set_row(t[14], 6, ["Release tag and deployment profile", "review-2 tag absent; Firebase, Modal, object storage, staging and rollback settings are not evidenced."])
    # Proposed schedule statuses are explicitly non-committal.
    statuses = {
        1: "Drafts exist; scope review disposition remains blank. Administrative project/class identifiers are recorded from the submitted project record and official guide.",
        2: "SRS v3.3/B28 and Rev11 diagram set are present; contracts/migration order and Review 2 acceptance remain open.",
        3: "FEAT-060 local WF-01/WF-02 code/checks exist; DB/device acceptance not proven.",
        4: "Local drawing/reconnect paths exist; durable two-device/device-network acceptance not proven.",
        5: "WF-03/WF-04 gated by FEAT-057, provider/storage configuration and consent/retention decisions.",
        6: "Planned; N1–N4/N7 gates remain, and staging, privacy, recovery and capacity evidence is absent.",
        7: "Not started; course calendar and deployment/rollback owner TBD.",
        8: "Not started; official dates and release/tag approval TBD.",
    }
    for i, status in statuses.items():
        row = t[15].rows[i]
        set_cell(row.cells[-1], status)
        set_cell(t[19].rows[i].cells[-1], status)
    for row in t[42].rows[1:]:
        set_cell(row.cells[-1], "Draft transition candidate; contract and transition test required")
    set_row(t[21], 1, ["R-01", "DB acceptance is blocked by migration and contract gates", "No repeatable PostgreSQL FE-to-BE proof; four DB cases were skipped.", "Keep N1–N3 in order; review lineage/contracts and run isolated synthetic acceptance.", "Proposed Khoa; approver/operator TBD", "Proposed 02–09 Nov 2026, dependent on approvals"])
    set_row(t[21], 2, ["R-02", "Device and network recovery are unaccepted", "QR/deep-link, restart, reconnect and concurrent-client defects may remain.", "Keep N4 after or alongside DB acceptance; define device matrix and recovery criteria.", "Proposed Bảo; matrix/owner confirmation TBD", "Proposed 13 Nov 2026, subject to N3"])
    set_row(t[21], 3, ["R-03", "Child-data lifecycle is incomplete", "Consent, derivative copies, deletion and backup expiry are not fully evidenced.", "Keep N7 as a pre-pilot gate; synthetic data only until approved.", "Proposed Đạt as coordinator; institutional approver TBD", "Proposed 13 Nov 2026; must close before pilot"])
    set_row(t[21], 4, ["R-04", "AI/media services are not configured for product use", "No production Modal or artifact storage profile; WF-03/WF-04 have adoption gates.", "Defer N5/N6; approve contracts/runtime/budget before live checks.", "Proposed Hiếu; provider/service approver TBD", "Proposed 20 Nov 2026 for decision package only"])
    set_row(t[21], 5, ["R-05", "40-child target and candidate NFRs are unmeasured", "No fixed workload, latency, error or cost profile is registered.", "Defer N9 until N3/N6; do not change the join policy into a hard cap.", "Proposed Khoa/Hiếu; acceptance owner TBD", "Proposed 30 Nov 2026, after N3/N6"])
    set_row(t[21], 6, ["R-06", "Age/safety review workload", "Content or tool may be unsuitable for an age band or class setting.", "Retain age-banded review, Teacher gate and explicit reject/recall path.", "Feature owner TBD", "Before content release"])
    set_row(t[21], 7, ["R-07", "Scope disposition and calendar are unconfirmed", "Registration reviewer fields and delivery capacity/dates are not accepted.", "Retain blank reviewer disposition and label owner/date suggestions as proposals.", "Proposed Đạt for coordination; owner/supervisor confirmation pending", "Before submission; proposed 04 Dec 2026"])
    set_row(t[21], 8, ["R-08", "State/contract drift across modules", "SRS B19.4 target registries exceed currently accepted wire-state mappings.", "Review all lifecycle diagrams against contracts and transition tests; maintain forward-only stages until OD07 is resolved.", "Feature owners TBD", "Before integration freeze"])
    # Current workstream, action register and delivery tasks; role names are not owner approvals.
    set_row(t[58], 1, ["Requested UI/BE2 branch integration", "Integrated into local dev before this authorized publication", "Historical merge evidence is in FEAT-058; the `review-2` release tag is absent."])
    set_row(t[58], 2, ["FEAT-059 structure cleanup", "Local changes and bounded historical checks are recorded", "Historical receipts do not prove a clean tagged release or all-app/staging acceptance."])
    set_row(t[58], 3, ["Child/Teacher/Admin integration", "WF-01/WF-02 local paths exist; WF-03/WF-04 remain gated", "No DB-backed UI E2E, live adult Firebase verification or accepted cross-feature WF-03/WF-04 contract."])
    set_row(t[58], 4, ["Modal and artifact runtime", "Modal selected; product profile is not evidenced", "Model/license, GPU, endpoint/auth, region, scale, timeout, secrets, artifact store and budget TBD."])
    set_row(t[58], 5, ["Schema deploy order", "Nine Alembic heads are reported", "N1: delivery-path heads, clean install/upgrade and rollback approver/procedure TBD."])
    set_row(t[58], 6, ["review-2 tag and project/class field", "Administrative IDs recorded; tag gate pending", "Use FA26SE225 from submitted project record and SWP490 from official guide; do not modify the original form. Create the tag only after all approved gates pass."])
    set_row(t[58], 7, ["Staging / pilot / E2E / load testing", "Not evidenced as completed", "Requires approved runtime, synthetic acceptance, device matrix, child-data controls and protocol."])
    set_row(t[59], 1, ["Registration and SRS/SDD", "Draft documents trace registration v1.2, SRS v3.3/B28, 66 FR, 38 use cases and the Rev11 diagrams.", "Reviewer disposition remains blank; identifiers are administrative dossier metadata, while registration v1.2 is unchanged.", "Proposed Đạt / all; confirmation pending"])
    set_row(t[59], 2, ["BE1 durable classroom foundation", "Local routes, PostgreSQL models/adapters and BE1 migration exist; historical focused checks recorded 22 passes.", "Four PostgreSQL cases skipped without BE1_TEST_DATABASE_URL; nine Alembic heads lack approved consolidated install/rollback.", "Khoa named in current docs; acceptance owner TBD"])
    set_row(t[59], 3, ["BE2 AI/media", "Job/attempt/receipt, content/video and worker-oriented module sources exist in local dev.", "FEAT-057 adoption/finalization gates remain; no production Modal/artifact profile or accepted full workflow.", "Hiếu named in current docs; acceptance owner TBD"])
    set_row(t[59], 4, ["Child Android", "Local join, refresh, reconnect/replay and acknowledged-stroke paths; historical check: 18 suites/26 tests.", "Mocked/local checks only; no PostgreSQL-backed FE-to-BE acceptance or physical-device run.", "Bảo named in current docs; acceptance owner TBD"])
    set_row(t[59], 5, ["Teacher Desktop", "Local class/lobby/roster/group/turn/stage and observation paths; historical check: 3 suites/6 tests.", "No DB-backed workflow acceptance, live identity proof or full classroom E2E.", "Bảo/Đạt named in current docs; acceptance owner TBD"])
    set_row(t[59], 6, ["Super Admin Console", "Local Firebase/BE1 role gate and class list/create path exist.", "Live adult Firebase login, production identity configuration and deployment acceptance are not evidenced.", "Đạt/Bảo named in current docs; acceptance owner TBD"])
    set_row(t[59], 7, ["Database deployment", "Nine Alembic heads are reported; new classroom migration chains from the existing BE1 head.", "Supported all-module bootstrap, upgrade order and rollback approver/procedure TBD; keep N1 before N3.", "Khoa named in current docs; migration approver TBD"])
    set_row(t[59], 8, ["Modal / AI evaluation", "Modal is owner-selected as intended AI host.", "Product endpoint/model/GPU/region/scale/secrets, production artifact store and budget are not configured/evidenced; N6 deferred.", "Proposed Hiếu; owner confirmation pending"])
    set_row(t[59], 9, ["Cross-surface verification", "Historical FEAT-060 checks: Child 18 suites/26 tests, Teacher 3 suites/6 tests, backend 22 passed; four PostgreSQL cases skipped.", "No staging E2E or device acceptance; 40-child target is unmeasured, not a hard cap. N3/N4 kept; N9 deferred.", "Named team roles exist; accountable acceptance owner TBD"])
    set_row(t[60], 1, ["Administrative project/class identifiers", "Project owner provided submission context", "FA26SE225 from submitted project record; SWP490 from official Review 2 guide; selected form v1.2 unchanged.", "Recorded for dossier metadata"])
    set_row(t[60], 2, ["N1 — migration lineage and rollback", "Proposed Khoa; DB approver TBD", "Delivery-path heads, clean install/upgrade/rollback procedure and receipt.", "Proposed 02 Nov 2026; before N3"])
    set_row(t[60], 3, ["N2 — BE1 contract and security review", "Proposed Khoa; Đạt cross-surface review", "Routes, transactions, authorization, receipts/idempotency, key lifecycle, proxy trust and throttle.", "Proposed 04 Nov 2026; before N3"])
    set_row(t[60], 4, ["N3 — synthetic PostgreSQL acceptance", "Proposed Khoa; isolated DB operator TBD", "Isolated DB profile; repeatable WF-01/WF-02 cases, recovery and migration evidence.", "Proposed 09 Nov 2026; after N1/N2"])
    set_row(t[60], 5, ["N4 — device/network acceptance", "Proposed Bảo; backend support by Khoa", "Supported device/OS/browser matrix; QR/deep-link, restart, network-loss and recovery criteria.", "Proposed 13 Nov 2026; after/alongside N3"])
    set_row(t[60], 6, ["N7 — child-data lifecycle gate", "Proposed Đạt as coordinator; institutional approver TBD", "Consent, purpose, retention, derivative copies, export/delete, purge, backup and audit.", "Proposed 13 Nov 2026; before any child-data pilot"])
    set_row(t[60], 7, ["N5/N6 — deferred contract/runtime decisions", "Proposed Hiếu; integration allocation requires separate approval", "Contract/adoption decision, approved service profile, artifact store, owner, secrets and cost limits.", "Proposed 20 Nov 2026 for decisions only; no live config"])
    set_row(t[60], 8, ["N8/N9/U3/U4 — rewind, capacity, schedule and tag", "Proposed Đạt for release coordination; product/course approvers TBD", "Keep rewind disabled; capacity after N3/N6; dates/workload/team capacity require confirmation; tag only after gates.", "Proposed 30 Nov–04 Dec 2026, dependency-gated; not committed"])
    # Current technology, composition and versioned contracts.
    set_row(t[26], 1, ["Database", "PostgreSQL with SQLAlchemy/Alembic in current BE1 slices; nine heads reported; delivery lineage and rollback are TBD."])
    set_row(t[26], 5, ["IDE / diagramming", "Microsoft Word/PDF for course reports; five supplied Draw.io sources preserved unchanged; authored lifecycle/activity pages are editable in the Rev11 Draw.io master, with diagram-type labels and no source attribution on canvases."])
    set_row(t[26], 7, ["Version control / CI", f"GitHub repository; reviewed dev baseline {revision}. Credential-free CI is included in the approved Rev11 work only; normal commit/push follows security validation. review-2 tagging remains gated on CI, Iteration 1 and document QA."])
    set_row(t[40], 1, ["Client surfaces", "apps/child-ui, apps/teacher-ui, apps/admin-ui", "WF-01/WF-02 have local paths and separate checks; no PostgreSQL-backed FE-to-BE or physical-device acceptance."])
    set_row(t[40], 2, ["HTTP composition", "Classroom-only and demo-only app compositions exist locally; compatibility create_app remains.", "Verify release entrypoint/route set before deployment; no production entrypoint acceptance is claimed."])
    set_row(t[40], 4, ["Persistence", "PostgreSQL adapters and feature/module schemas; a new BE1 classroom migration chains from 20261014_0004.", "Nine heads remain; approve supported install/upgrade/rollback path and synthetic DB acceptance."])
    set_row(t[41], 1, ["Child Android", "apps/child-ui; Expo SDK 55, React Native 0.83.10, React 19", "Local QR/deep-link request, request refresh, reconnect/replay and acknowledged stroke append paths; mocked UI check passed 18 suites/26 tests. No DB/device E2E."])
    set_row(t[41], 2, ["Teacher Desktop", "apps/teacher-ui; React/TypeScript/Vite family", "Local class/lobby/roster/group/turn/session-stage and observation paths; check passed 3 suites/6 tests. No DB-backed workflow acceptance."])
    set_row(t[41], 3, ["Super Admin", "apps/admin-ui; React/TypeScript/Vite family", "Local Firebase/BE1 role gate and class list/create path exist; live adult identity and production authorization are not established."])
    set_row(t[41], 4, ["Backend", "Python 3.12 project; FastAPI, Pydantic, SQLAlchemy and Alembic", "Focused local backend checks passed 22; four PostgreSQL tests skipped because BE1_TEST_DATABASE_URL is unset. Nine Alembic heads remain."])
    # Migration inventory row for the current classroom change.
    new = t[43].add_row()
    set_row(t[43], len(t[43].rows)-1, ["be1", "20261024_0005_classroom_srs_contracts.py", "20261024_0005", "20261014_0004", "Additive classroom SRS contract migration; BE1 head only; not a nine-head install plan"])
    set_row(t[42], 1, ["Identity / adult scope", "Verify adult token; derive principal and scoped assignments", "Local Firebase/BE1 role-gate path exists", "Live Firebase project/login verification not evidenced"])
    set_row(t[42], 2, ["Class/profile/enrollment", "Create/read assigned class, managed profile and enrollment", "BE1 durable routes / PostgreSQL models and local UI paths", "DB-backed UI acceptance and complete consent/age-policy gates remain open"])
    set_row(t[42], 3, ["Session / group", "Configure, admit, control stages, move members and close", "Local Child/Teacher connections to BE1 classroom routes", "No PostgreSQL-backed FE-to-BE acceptance; state/receipt contract review remains open"])
    set_row(t[42], 6, ["AI jobs", "Create job, claim attempt, record command/result and reject stale completion", "BE2 job/attempt/receipt schema and adapter ports", "FEAT-057 adoption gates remain; no live provider or product endpoint"])
    set_row(t[42], 7, ["Knowledge / video", "Prepare content, report generation state, review exact version and disposition failure", "Separate content/video modules and schemas", "WF-04 integration, production storage/runtime and end-to-end acceptance open"])
    set_row(t[42], 8, ["Activity / learning record", "Assign reviewed activity; record reflection, observation and portfolio evidence", "Module schemas and local Teacher observation path", "Cross-feature WF-04 integration and retention evidence incomplete"])
    set_row(t[42], 9, ["Governance / data request", "Consent, audit, retention, export/delete and incident controls", "BE1 lifecycle records plus separate policy/copy schemas", "Purpose catalogue, deletion/backup policy and external-copy proof TBD"])
    # Update current implementation/state summary against the reviewed code baseline.
    baseline = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    for p in doc.paragraphs:
        if p.text.startswith("The 15-week relative plan"):
            p.text = "The 15-week relative plan and preliminary person-day estimates remain proposals. FEAT-060 records local WF-01/WF-02 integration and separate checks; PostgreSQL-backed UI acceptance, device acceptance and staging evidence are still open. WF-03/WF-04 remain gated. Exact calendar dates, person availability, owners, milestone approvals and actual completion are TBD."
        elif p.text.startswith("Source repository:"):
            p.text = f"Source repository: https://github.com/CaoDat-2410/Sketch2Life. Project implementation evidence in this report was inspected at dev@{baseline}; this Rev11 dossier update is a documentation publication. The official `review-2` tag and tagged-baseline BM02 run remain conditional on all required gates."
        elif p.text.startswith("Document source baseline:"):
            p.text = f"Document source baseline: project implementation inspected at dev@{baseline}; this package revision is Rev11. The report distinguishes implementation evidence from design targets and open acceptance. The official `review-2` tag is created only after the approved gates pass."
        elif p.text.startswith("Keep the official registration"):
            p.text = "Keep the selected registration and supplied school templates unchanged. Supplied diagrams are preserved as provided; the Rev11 Draw.io master contains those pages and the editable lifecycle/activity pages. Diagram derivation and integrity records stay in the project evidence register, not on diagram canvases."
        elif p.text.startswith("The current route inventory"):
            p.text = p.text.replace("The current route inventory", "The historical route inventory")
        elif p.text.startswith("At the inspected baseline, Alembic reports nine"):
            p.text = "At the inspected baseline, Alembic reports nine independent heads: the new BE1 classroom head plus eight separate feature heads. The new classroom revision chains from the existing BE1 head only; there is no approved clean all-module install/rollback path. Four PostgreSQL acceptance cases were skipped because BE1_TEST_DATABASE_URL was unset."
        elif p.text.startswith("Current deployment target"):
            p.text = "The product staging/production host, runtime secrets, object store, queue, database recovery point, backup/restore rehearsal, rollout and rollback procedure are not approved. Nine Alembic heads and an additive BE1 migration are present, but no consolidated lineage is accepted. Treat local tests as local evidence only."
        elif p.text.startswith("The Review 2 minimum count"):
            p.text = "BM01 proposes a reproducible 73-case planning target: 18 mandatory-feature cases, four workflow cases, six candidate NFR rows, 30 representative legal lifecycle transitions and 15 rejected transitions. Appendix A3.1 lists two legal and one negative example for each B19.4 registry. This is a planning proposal, not a measured suite, approved denominator or instructor commitment; owners must confirm the transition matrix and CI floor."
        elif p.text.startswith("The diagrams D10–D13"):
            p.text = "Appendix D, Figures D23–D40, covers all fifteen SRS v3.3/B19.4 lifecycle registries in eighteen focused views, including session and device companion views. These are target models and do not prove runtime behavior. BE1 session values currently present in source are configured/lobby/active/paused/finished; mapping the full SRS lifecycle to versioned contracts remains open. The transition rows in Table 42 are draft candidates that still require owner review and tests."
        elif p.text.startswith("The four workflow owners map to four end-to-end activity diagrams"):
            p.text = "The four main workflows have one activity diagram each in Appendix D, Figures D41–D44. They show actors and business outcomes as target designs, not completed demonstrations. Editable final pages are in the Rev11 Draw.io master, and each figure caption names its diagram type."
        elif p.text.startswith("The 24 UI tests and 9 backend tests"):
            p.text = "The test-evidence section reports checks recorded in FEAT-060 and the Rev11 verification record. Separate mocked UI and backend checks do not prove database-backed FE-to-BE acceptance. Four PostgreSQL cases previously skipped without BE1_TEST_DATABASE_URL remain open until repeated against an approved isolated synthetic database."
        elif p.text.startswith("The current source and course authorities"):
            p.text = "Project authority: selected registration v1.2, canonical SRS v3.3/B28, current FEAT-057/FEAT-060 records and the Review 2 guide. Supplied originals remain unchanged; the Rev11 editable master contains all diagram pages with clear diagram-type labels."
        elif p.text.startswith("• Confirm official class"):
            p.text = "• U1: Use FA26SE225 from the submitted project record and SWP490 from the official guide for dossier metadata; preserve the blank fields in selected registration v1.2."
        elif p.text.startswith("• Freeze versioned contracts"):
            p.text = "• N2: Complete BE1 route, transaction, authorization, receipt, idempotency, key-lifecycle and trusted-proxy/throttle review; final contract/version remains TBD."
        elif p.text.startswith("• Approve migration order"):
            p.text = "• N1/N3: Approve the nine-head Alembic lineage and clean-install/upgrade/rollback plan, then run synthetic PostgreSQL acceptance. Four DB cases were skipped without BE1_TEST_DATABASE_URL."
        elif p.text.startswith("• Complete the Modal runtime"):
            p.text = "• N5/N6/N7/N9: Keep WF-03/WF-04 gated; approve runtime/artifact-storage and child-data lifecycle before a pilot; measure 40-child capacity only after a repeatable environment. 40 is not a hard join cap."
        elif p.text.startswith("Snapshot: local dev@"):
            p.text = f"Snapshot: implementation evidence inspected at dev@{baseline}; the Review 2 dossier is Rev11. The official `review-2` tag and tag-specific BM02 execution follow the CI, Iteration 1, document-QA, clean-tree and security gates."
        elif p.text.startswith("[3] Sketch2Life repository"):
            p.text = f"[3] Sketch2Life repository; project implementation evidence was inspected at dev@{baseline}. The official tag-specific BM02 execution remains pending the approved release gates."
        elif p.text.startswith("[2] Collaborative Learning SRS"):
            p.text = "[2] Collaborative Learning SRS v3.3, FEAT-039, repository artifact. Current owner-approved detailed actor, functional, data, state, API, privacy and acceptance source."
    update_properties(doc, "Sketch2Life Review 2 Reports 1–5 and Project Tracking", "Consolidated current-state SRS/SDD, PM plan, test plan and project tracking")


SOURCE_DIAGRAMS = [
    ("D01", "Business Context", "Context Diagram", "context_page01.png"),
    ("D02", "C4 System Context", "C4 System Context Diagram", "context_page02.png"),
    ("D03", "Use Case Overview", "UML Use Case Diagram", "usecases_page01.png"),
    ("D04", "Use Case Details — page 2", "UML Use Case Diagram", "usecases_page02.png"),
    ("D05", "Use Case Details — page 3", "UML Use Case Diagram", "usecases_page03.png"),
    ("D06", "Use Case Details — page 4", "UML Use Case Diagram", "usecases_page04.png"),
    ("D07", "Use Case Details — page 5", "UML Use Case Diagram", "usecases_page05.png"),
    ("D08", "Use Case Details — page 6", "UML Use Case Diagram", "usecases_page06.png"),
    ("D09", "Use Case Details — page 7", "UML Use Case Diagram", "usecases_page07.png"),
    ("D10", "Use Case Details — page 8", "UML Use Case Diagram", "usecases_page08.png"),
    ("D11", "Use Case Details — page 9", "UML Use Case Diagram", "usecases_page09.png"),
    ("D12", "Use Case Details — page 10", "UML Use Case Diagram", "usecases_page10.png"),
    ("D13", "Use Case Details — page 11", "UML Use Case Diagram", "usecases_page11.png"),
    ("D14", "Use Case Details — page 12", "UML Use Case Diagram", "usecases_page12.png"),
    ("D15", "Main Session Sequence", "UML Sequence Diagram", "sequence_page01.png"),
    ("D16", "Detailed Session Sequence", "UML Sequence Diagram", "sequence_page02.png"),
    ("D17", "Screen Flow", "Screen Flow Diagram", "thieu_page01.png"),
    ("D18", "Class Diagram", "UML Class Diagram", "thieu_page02.png"),
    ("D19", "Logical ERD", "Logical Entity-Relationship Diagram", "thieu_page03.png"),
    ("D20", "Khoa ERD", "Entity-Relationship Diagram", "khoa_page01.png"),
    ("D21", "System Architecture", "System Architecture Diagram", "khoa_page02.png"),
    ("D22", "Package Diagram", "UML Package Diagram", "khoa_page03.png"),
]

NEW_DIAGRAM_TITLES = [
    "Session Lifecycle", "Session Pause and Recovery", "Session Early Termination", "Shared Learning Stage",
    "Group Progress", "Participant Admission", "Device Connection", "Device Grant Revocation",
    "Draft Synchronization", "Sketch Pipeline", "Child Suggestion Response", "Knowledge Editorial",
    "AI / Media Job", "Video Delivery", "Activity Execution", "Observation", "Content Publication", "Data Request",
    "WF-01 Prepare and Admit", "WF-02 Collaborative Drawing and Recovery", "WF-03 Request and Review AI Sketch",
    "WF-04 Reviewed Learning and Session Close",
]


def remove_drawings(paragraph) -> None:
    for drawing in list(paragraph._p.xpath(".//w:drawing")):
        drawing.getparent().remove(drawing)


def add_gallery(doc) -> None:
    doc.add_page_break()
    h = doc.add_paragraph("Appendix D. Editable Draw.io Diagram Gallery", style="Heading 1")
    h.paragraph_format.keep_with_next = True
    p = doc.add_paragraph("Figures D01–D22 cover business/context, use-case, sequence, screen-flow, class, entity-relationship, architecture and package views. Figures D23–D40 represent all fifteen SRS v3.3/B19.4 lifecycle registries, with focused session/device companion views; D41–D44 provide an activity diagram for each main workflow. All 44 pages are editable in the Rev11 Draw.io master and labeled by diagram type. Lifecycle and workflow pages express design intent and do not prove runtime acceptance.")
    p.paragraph_format.space_after = Pt(8)
    pages: list[tuple[str, str, Path]] = []
    for fid, title, diagram_type, filename in SOURCE_DIAGRAMS:
        pages.append((fid, title, diagram_type, EXPORTS / filename))
    for i, title in enumerate(NEW_DIAGRAM_TITLES, start=1):
        fid = f"D{22+i:02d}"
        diagram_type = "State Machine Diagram" if i <= 18 else "Activity Diagram"
        pages.append((fid, title, diagram_type, NEW_PAGES / f"page-{i:02d}.png"))
    for fid, title, diagram_type, path in pages:
        if not path.exists():
            raise FileNotFoundError(path)
        doc.add_page_break()
        heading = doc.add_paragraph(f"Figure {fid}. {title}", style="Heading 3")
        heading.paragraph_format.keep_with_next = True
        heading.paragraph_format.space_after = Pt(6)
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.paragraph_format.space_after = Pt(4)
        caption.add_run(f"Diagram type: {diagram_type}.").italic = True
        image = Image.open(path)
        width_px, height_px = image.size
        section = doc.sections[-1]
        available_w = (section.page_width - section.left_margin - section.right_margin) / 914400
        available_h = (section.page_height - section.top_margin - section.bottom_margin) / 914400 - 1.0
        aspect = width_px / height_px
        width_in = min(available_w, available_h * aspect)
        height_in = width_in / aspect
        pic_para = doc.add_paragraph()
        pic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pic_para.paragraph_format.space_after = Pt(0)
        pic_para.add_run().add_picture(str(path), width=Inches(width_in), height=Inches(height_in))
    # Planning section is deliberately easy to locate but excluded from the lengthy diagram list in the TOC.
    doc.add_page_break()
    doc.add_paragraph("Appendix E. Current Delivery, Proposed Next Work and Unknowns", style="Heading 1")
    intro = doc.add_paragraph("Owner-delegated dependency proposal dated 24 October 2026. Keep/Defer controls only near-term sequencing; no item is omitted from registered scope. Proposed owners and dates await confirmation. Delivery capacity, acceptance thresholds, environments and service settings stay TBD until the responsible people confirm them. Administrative identifiers are recorded in the dossier metadata; the selected registration form remains unchanged.")
    intro.paragraph_format.space_after = Pt(8)
    doc.add_paragraph("E1. Current workflow status", style="Heading 2")
    wf = doc.add_table(rows=1, cols=3)
    wf.style = "Table Grid"
    for i, value in enumerate(["Workflow", "Evidence-backed current status", "Still unknown / not established"]): set_cell(wf.rows[0].cells[i], value)
    workflow_rows = [
        ["WF-01 — prepare and admit", "Local Child/Teacher/BE1 paths for lobby, QR/code request, review, admission/revoke and Start; separate Child/Teacher checks passed.", "No PostgreSQL-backed FE-to-BE acceptance; 4 DB tests skipped; no live Firebase or physical-device join evidence. Migration path and test operator TBD."],
        ["WF-02 — collaborative drawing/recovery", "Local Child/Teacher wiring for acknowledged strokes, turn/group context and reconnect/replay; UI/backend checks passed separately.", "No durable multi-client DB acceptance, real network/restart device run, supported-device matrix or recovery threshold."],
        ["WF-03 — AI sketch review", "SRS scope retained; FEAT-057 slices remain partial/gated; no classroom integration or live Modal call evidenced.", "Shared finalization/execution authority, contract version, fallback, provider profile, model, endpoint and safety review path TBD."],
        ["WF-04 — reviewed learning/video/activity/close", "SRS scope retained; FEAT-057 and storage/runtime gates remain; no accepted end-to-end classroom path evidenced.", "Approved content/storage contracts, retention/export/deletion path, activity/reflection lifecycle, service owner and runtime profile TBD."],
    ]
    for values in workflow_rows:
        row = wf.add_row()
        for i, value in enumerate(values): set_cell(row.cells[i], value)
    e2_heading = doc.add_paragraph("E2. Near-term filter for owner review", style="Heading 2")
    e2_heading.paragraph_format.page_break_before = True
    tbl = doc.add_table(rows=1, cols=3)
    tbl.style = "Table Grid"
    for i, value in enumerate(["Item / proposal", "Reason and dependency", "Open questions (TBD unless confirmed)"]): set_cell(tbl.rows[0].cells[i], value)
    header_props = tbl.rows[0]._tr.get_or_add_trPr()
    repeat_header = OxmlElement("w:tblHeader")
    repeat_header.set(qn("w:val"), "true")
    header_props.append(repeat_header)
    plans = [
        ("N1 — KEEP", "Approve one Alembic lineage, clean install/upgrade and rollback before DB acceptance; nine heads are reported.", "Which heads are in delivery path; who approves; exact clean-install and rollback procedure."),
        ("N2 — KEEP", "Review BE1 routes, transactions, authorization, receipts/idempotency, join-code key lifecycle, trusted-proxy IP and cross-replica throttle; can run alongside N1.", "DTO/version, guard and error mapping, key lifecycle, proxy trust, concurrency and accountable reviewer."),
        ("N3 — KEEP after N1/N2", "Run isolated synthetic PostgreSQL acceptance for WF-01/WF-02, migration, restart/recovery and rollback; four cases skipped without BE1_TEST_DATABASE_URL.", "Operator/URL, DB version, isolated environment, scenarios/thresholds and evidence owner."),
        ("N4 — KEEP after or alongside N3", "Accept QR/deep-link, restart, reconnect and network-loss behavior on supported devices before end-to-end claims.", "Device/OS/browser matrix, test owner, interruption scenarios and recovery criteria."),
        ("N5 — DEFER", "Integrate WF-03/WF-04 only after FEAT-057 adoption gates and versioned contracts are approved; scope remains in SRS.", "Card/contract version, owner, finalization/execution authority, fallback and human safety/review path."),
        ("N6 — DEFER after contract decisions", "Configure Firebase, Modal and production artifact storage after contract/data boundaries and before live checks; no production profile is evidenced.", "Project/tenant, storage provider/bucket/region, Modal model/GPU/endpoint, secret owner, timeout and cost ceiling."),
        ("N7 — KEEP as pre-pilot gate", "Close child consent, purpose, retention, export/delete, purge and audit before real child data; synthetic DB acceptance can proceed separately.", "Consent text, data classes, purge/backup rules, institutional/legal review and evidence owner."),
        ("N8 — DEFER; rewind disabled", "Forward-only stage progression is valid while OD07 is unresolved; no blocker while rewind remains disabled.", "Whether rewind is needed; evidence/draft preservation, guard and receipt rules if enabled."),
        ("N9 — DEFER after N3/N6", "Measure the one-class 40-child pilot target after repeatable DB/runtime exists; it is not a hard join cap.", "Workload, device/network profile, latency/error thresholds, hosting/cost limits and measurement owner."),
    ]
    for values in plans:
        row = tbl.add_row()
        for i, value in enumerate(values): set_cell(row.cells[i], value)
        row_props = row._tr.get_or_add_trPr()
        row_props.append(OxmlElement("w:cantSplit"))
    e3_heading = doc.add_paragraph("E3. Submission and planning unknowns", style="Heading 2")
    e3_heading.paragraph_format.page_break_before = True
    unknowns = doc.add_table(rows=1, cols=3)
    unknowns.style = "Table Grid"
    for i, value in enumerate(["ID", "Unknown", "Disposition in this draft"]): set_cell(unknowns.rows[0].cells[i], value)
    unknown_header_props = unknowns.rows[0]._tr.get_or_add_trPr()
    unknown_repeat_header = OxmlElement("w:tblHeader")
    unknown_repeat_header.set(qn("w:val"), "true")
    unknown_header_props.append(unknown_repeat_header)
    items = [
        ["U1", "Official project/class code", "Administrative identifiers are FA26SE225 (submitted project record) and SWP490 (official Review 2 guide). The selected registration v1.2 is preserved unchanged."],
        ["U2", "N1–N9 near-term selection", "Owner delegated the current Keep/Defer proposal; no candidate is omitted and no registered requirement is removed."],
        ["U3", "Calendar milestones, capacity, person-days and accountable owners", "The existing 15-week/252 person-day figures are draft proposals; dates/capacity/assignment acceptance remain TBD."],
        ["U4", "Official BM02 tagged baseline", "review-2 tag absent; this is an untagged source review. No tag is created by this task."],
        ["U5", "Treatment of deferred work", "All four workflows and SRS requirements remain registered; only proposed sequencing is deferred."],
    ]
    for values in items:
        row = unknowns.add_row()
        for i, value in enumerate(values): set_cell(row.cells[i], value)
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def refresh_report() -> None:
    path = OUTPUT / f"{NAMES['report']}.docx"
    doc = Document(path)
    replace_text_everywhere(doc, {
        "SRS v3.1": "SRS v3.3",
        "canonical SRS v3.1": "canonical SRS v3.3",
        "FA26SE225 (inferred from the registration filename; source form field is blank)": "FA26SE225 is the administrative project identifier from the submitted project record; selected registration v1.2 remains unchanged.",
        "The class was blank": "The class and project-code fields were blank",
        "FA26SE225 is inferred from the filename": "FA26SE225 and SWP490 are administrative identifiers from the submitted project record and official guide; the selected registration remains unchanged",
        "source diagrams remain Mermaid text in the feature package": "supplied diagram originals remain unchanged and the lifecycle/activity views are editable in the Rev11 Draw.io master",
        "diagram source is under FEAT-058 artifacts/diagrams": "all 44 editable pages are in the Rev11 Draw.io master and each report figure caption names its diagram type",
    })
    update_report_tables(doc)
    # Rebuild the TOC as a real Word field so Word pagination is current on PDF export.
    install_toc(doc)

    # Keep the contract principle with its section heading/table so it cannot leave
    # an orphaned two-line continuation on a near-empty page.
    contract_paragraph = next((p for p in doc.paragraphs if p.text.strip().startswith("Every command should carry a versioned contract")), None)
    contract_table = next((table for table in doc.tables if table.rows and text_of(table.rows[0].cells[0]) == "Contract family"), None)
    if contract_paragraph is not None and contract_table is not None:
        contract_paragraph.text = "Each command carries a versioned contract, authenticated principal, resource scope, operation ID and expected aggregate revision. Typed errors cover authorization, validation, not found, conflict/stale version, consent/policy, provider and persistence failures; recheck source version and current purpose before worker commit."
        contract_paragraph.paragraph_format.keep_together = True
        contract_table._tbl.addprevious(contract_paragraph._p)

    # Replace body figures with precise appendix references; the complete source pages appear later.
    figure_refs = {
        "Figure 1.": "Figure 1. The four workflow activity diagrams are in Appendix D, Figures D41–D44.",
        "Figure 2.": "Figure 2. Use Case Overview: Appendix D, Figure D03.",
        "Figure 3.": "Figure 3. Screen Flow: Appendix D, Figure D17.",
        "Figure 4.": "Figure 4. C4 System Context: Appendix D, Figure D02.",
        "Figure 5.": "Figure 5. System Architecture: Appendix D, Figure D21.",
        "Figure 6.": "Figure 6. Package Diagram: Appendix D, Figure D22.",
        "Figure 7.": "Figure 7. Supplied ERD; physical migration mapping is reported separately in Tables 38 and 43: Appendix D, Figure D20.",
        "Figure 8.": "Figure 8. Session Sequence: Appendix D, Figures D15–D16.",
        "Figure 9.": "Figure 9. Class Diagram: Appendix D, Figure D18.",
        "Figure 10.": "Figure 10. Session lifecycle target: Appendix D, Figures D23–D25.",
        "Figure 11.": "Figure 11. Participant admission lifecycle target: Appendix D, Figure D28.",
        "Figure 12.": "Figure 12. AI/media job lifecycle target: Appendix D, Figure D35.",
        "Figure 13.": "Figure 13. Video delivery lifecycle target: Appendix D, Figure D36.",
        "Figure 14.": "Figure 14. Logical ERD: Appendix D, Figure D19.",
        "Figure 15.": "Figure 15. WF-01 Prepare and Admit activity: Appendix D, Figure D41.",
        "Figure 16.": "Figure 16. WF-02 Collaborative Drawing and Recovery activity: Appendix D, Figure D42.",
        "Figure 17.": "Figure 17. WF-03 Request and Review AI Sketch activity: Appendix D, Figure D43.",
        "Figure 18.": "Figure 18. WF-04 Reviewed Learning and Session Close activity: Appendix D, Figure D44.",
    }
    # Identify figure captions before replacing their text, then remove their old image paragraphs.
    for caption in doc.paragraphs:
        for prefix, replacement in figure_refs.items():
            if caption.text.strip().startswith(prefix):
                caption.text = replacement
                break
    for paragraph in list(doc.paragraphs):
        if paragraph._p.xpath(".//w:drawing"):
            remove_drawings(paragraph)
    add_gallery(doc)
    update_properties(doc, "Sketch2Life Review 2 Reports 1–5 and Project Tracking", "Consolidated report with current SRS v3.3, SDD and editable Draw.io diagram gallery")
    doc.save(path)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    required = {
        NAMES["brief"]: "SWP490_FA26SE225_R2_DesignBrief.docx",
        NAMES["registration"]: "SWP490_FA26SE225_R2_Registration.docx",
        NAMES["report"]: "SWP490_FA26SE225_R2_Report1-5_Tracking.docx",
        NAMES["selfreview"]: "SWP490_FA26SE225_R2_SelfReview.docx",
    }
    for destination, source in required.items():
        shutil.copy2(SOURCE / source, OUTPUT / f"{destination}.docx")
    refresh_registration()
    refresh_bm01()
    refresh_bm02()
    refresh_report()
    print(f"created {len(required)} DOCX files in {OUTPUT}")


if __name__ == "__main__":
    main()
