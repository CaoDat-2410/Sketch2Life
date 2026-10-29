"""Shared Project Management Plan data for the standalone and consolidated reports.

All dates, effort and progress labels below are planning proposals based on the
supplied registration, current source snapshot and SEP490's relative schedule.
They are not team commitments or verified historical actuals.
"""

WBS_ROWS = [
    ("1", "Classroom and session management", "", "46"),
    ("1.1", "Class, profile, enrollment and consent administration", "Complex", "16"),
    ("1.2", "QR/session-code admission and participant verification", "Medium", "10"),
    ("1.3", "Teacher-led session stages, groups and progress", "Complex", "20"),
    ("2", "Collaborative drawing", "", "40"),
    ("2.1", "Personal/shared canvas and age-adapted tools", "Complex", "22"),
    ("2.2", "Contribution attribution, save, reconnect and recovery", "Complex", "18"),
    ("3", "AI and reviewed learning media", "", "48"),
    ("3.1", "Contextual sketch suggestions, Teacher review and child response", "Complex", "24"),
    ("3.2", "Knowledge/video authoring, versioning and approval", "Complex", "24"),
    ("4", "Activities and learning records", "", "30"),
    ("4.1", "Off-screen activity selection, adaptation and outcome", "Medium", "14"),
    ("4.2", "Reflection, portfolio and descriptive progress observations", "Medium", "16"),
    ("5", "Product surfaces", "", "54"),
    ("5.1", "Child Android application workflows", "Complex", "22"),
    ("5.2", "Teacher Desktop workflows", "Complex", "18"),
    ("5.3", "Super Admin Console workflows", "Medium", "14"),
    ("6", "Cross-cutting platform and verification", "", "34"),
    ("6.1", "Adult identity, scoped access, audit and retention controls", "Complex", "16"),
    ("6.2", "API/data integration, migration coordination, test and acceptance", "Complex", "18"),
]

TOTAL_EFFORT = 252

# Window labels are relative to the course kickoff. Map them to calendar dates
# only after the instructor's official milestone calendar is available.
SCHEDULE_ROWS = [
    ("W1 / 1 wk", "Initiation and project setup", "Kickoff / scope baseline", "Đạt; all members", "Report 1, initial plan, risk baseline", "Partially complete; confirm with supervisor"),
    ("W2-W3 / 2 wks", "Planning and requirements", "W1", "Đạt; all members", "Registration baseline, SRS, traceability, backlog", "Drafts exist; Review 2 approval pending"),
    ("W4-W5 / 2 wks", "Software design", "W2-W3", "Khoa; Đạt", "SDD, architecture, ERD, state/activity diagrams, contracts", "Drafted; migration order and contracts open"),
    ("W6-W7 / 2 wks", "Iteration 1: classroom foundation", "W4-W5; API contract", "Khoa; Đạt; Bảo", "Class/profile/session/admission vertical slice with tests", "In progress; no cross-surface E2E evidence"),
    ("W8-W9 / 2 wks", "Iteration 2: drawing and collaboration", "W6-W7", "Bảo; Khoa; Đạt", "Canvas, contribution context, reconnect/recovery slice", "Prototype/services exist; integration remains open"),
    ("W10-W11 / 2 wks", "Iteration 3: AI, content and activities", "W8-W9; provider decision", "Hiếu; Đạt; Bảo", "Reviewed sketch/media/activity workflows and tests", "Partial; Modal deployment profile TBD"),
    ("W12-W13 / 2 wks", "System verification and defect correction", "W6-W11; staging + migration rehearsal", "Đạt; all members", "E2E, security/privacy, recovery and performance receipts", "Planned; staging/capacity results absent"),
    ("W14 / 1 wk", "Transition preparation", "W12-W13 exit gate", "All members", "User guides, deployment/rollback runbook, UAT readiness", "Not started"),
    ("W15 / 1 wk", "Final package and defense preparation", "W14", "All members", "Updated reports, reproducible demo, final package", "Not started; course dates TBD"),
]

DELIVERABLE_ROWS = [
    ("1", "Project Introduction and initial Project Management Plan", "W1", "Initial draft exists in the Review 2 package; instructor dates TBD."),
    ("2", "SRS, requirement traceability and project tracking baseline", "W2-W3", "Registration v1.2 controls; review/approval remains pending."),
    ("3", "SDD, architecture, Logical ERD and editable diagrams", "W4-W5", "Current design draft; database migration order remains an open gate."),
    ("4", "Software Package 1: classroom foundation and automated tests", "W6-W7", "Proposed milestone; do not claim end-to-end acceptance before evidence."),
    ("5", "Software Package 2: collaborative drawing and recovery", "W8-W9", "Proposed milestone; API/UI integration is an explicit exit check."),
    ("6", "Software Package 3: AI/media/activity workflows", "W10-W11", "Modal selected; model/GPU/endpoint/budget and provider acceptance TBD."),
    ("7", "System test, security/privacy review and defect closure", "W12-W13", "Planned; staging and one-class capacity target must be measured."),
    ("8", "User guides, deployment/rollback, UAT and final package", "W14-W15", "Official dates and release/tag approval TBD."),
]

RACI_ROWS = [
    ("Project planning and weekly tracking", "D", "S", "S", "S"),
    ("Registration, SRS and requirement traceability", "D", "S", "S", "R"),
    ("System architecture and API contract integration", "R", "S", "I", "D"),
    ("Class/session APIs, persistence and migrations", "S", "S", "I", "D"),
    ("Child, Teacher and Admin user-interface surfaces", "R", "I", "D", "S"),
    ("AI sketch, knowledge/video and result provenance", "R", "D", "S", "S"),
    ("Cross-surface integration and acceptance coordination", "D", "R", "S", "S"),
    ("Privacy, consent, audit and retention controls", "R", "S", "I", "D"),
    ("Unit/contract/CI evidence for owned features", "S", "D", "R", "R"),
    ("WF-01 Prepare and admit classroom session", "S", "I", "S", "D"),
    ("WF-02 Join, draw and recover a collaborative canvas", "S", "S", "D", "R"),
    ("WF-03 Review an AI sketch suggestion", "R", "D", "S", "S"),
    ("WF-04 Teacher-led learning content and session close", "D", "S", "R", "S"),
    ("Review 2 reports and project documentation", "D", "S", "S", "R"),
]

TRAINING_ROWS = [
    ("Child safety, consent, privacy and descriptive assessment", "All members", "W1-W3; refresh before any child study", "Required before any real child data or recruitment"),
    ("Versioned API contracts, PostgreSQL migrations and recovery", "Khoa, Đạt; supporting members", "W4-W7", "Review contract and migration rehearsal evidence"),
    ("AI job lifecycle, safety gates and Modal deployment controls", "Hiếu, Đạt; supporting members", "W8-W11 after profile approval", "No live provider call before model/GPU/budget approval"),
    ("Cross-platform acceptance testing and CI evidence", "All members", "W6-W13", "Each member can run tests for their owned workflow"),
]

COMMUNICATION_ROWS = [
    ("Weekly feature and schedule review", "All four members; supervisor when available", "Inspect shipped evidence, blockers, estimate/schedule variance and next work", "Weekly; exact day TBD", "Team meeting + repository issue/feature record; publish decisions"),
    ("Pull-request / CI review", "Author, relevant owner and integrator", "Review contract, tests, security and acceptance criteria", "Every PR; CI on each change", "GitHub PR/checks; require owner review and passing required checks"),
    ("Scope, child-safety, data or provider decision", "Team + project owner/supervisor", "Resolve decisions that affect registered scope, consent or paid services", "Before implementation or external call", "Repository ADR/approval record; do not rely on chat-only implicit state"),
]

TOOLS_ROWS = [
    ("Technology", "Child: Expo SDK 55 / React Native 0.83.10; Teacher/Admin: React 19, Vite 8, TypeScript; backend: FastAPI/Python."),
    ("Database", "PostgreSQL with SQLAlchemy/Alembic in current backend slices; multiple migration heads remain and deployment order is TBD."),
    ("Identity and third parties", "Firebase Authentication only. Firebase Storage, Firestore and Realtime Database are prohibited."),
    ("AI hosting", "Modal selected. App/function, model, GPU, endpoint, region, scale, timeout and spending cap are TBD; no deployed product endpoint is claimed."),
    ("IDE / diagramming", "VS Code and repository-native Markdown/Mermaid; keep editable diagram sources in the feature package."),
    ("Documentation", "Microsoft Word/PDF for course reports; Markdown for feature plans, decisions and evidence."),
    ("Version control / CI", "GitHub repository, feature branches, pull requests and CI scripts. Current documentation baseline is local dev; 726 commits ahead of origin and working-tree cleanup is uncommitted."),
    ("Project management", "Feature plan/approval/evidence records plus weekly team review. GitHub Issues/Projects can hold backlog and timeline views; an active Project board is not verified."),
    ("Deployment environment", "Dev source is local. Staging/production host, rollout and rollback process remain TBD; no deployment is claimed."),
    ("AI tools", "Codex/ChatGPT assisted requirements, design, code/document review and drafting; team members validate every owned result and disclose use in Report 4."),
]
