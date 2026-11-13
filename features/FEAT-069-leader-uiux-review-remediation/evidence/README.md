# FEAT-069 evidence index

Evidence for the leader-review UI remediation, captured 2026-11-14 (Asia/Saigon). Rev3 is the active approved scope; it preserves Rev2 review prototypes and adds conditional reads for the delivery branch's current Lesson Library/BE1 contracts. FEAT-063 SRS v2.5-draft remains unsigned and canonical.

| Evidence | AC | What it establishes | Limitations |
|---|---|---|---|
| `notes/EXECUTION.md` | AC2, AC7–AC12 | Builds/typecheck/APK packaging, manual visual review of Parent + three web roles, ordered Teacher flow and the emulator installation blocker | Browser screenshots were inspected live; saved PNGs below are the Rev1 captures and remain historical. APK runtime on the supplied emulator is unverified. |
| `notes/OPEN_QUESTIONS.md` | AC3–AC7, AC11 | Leader/SRS conflict and missing APIs, with explicit preview-only treatment | Requires owner/SRS/API resolution before product behavior or persistence is claimed. |
| `notes/API_UI_CROSSWALK_REV3.md` | AC1–AC9 | Mounted-route/source mapping, conditional screen wiring, auth gate, excluded newer-branch routes and unimplemented workflows | Source inspection only; no live API or external auth-config verification. |
| `notes/SOURCE_PROVENANCE_REV2.md` | AC11–AC12 | Approved branch/source boundary and permitted backend comparison | Branch source comparison is read-only context; current delivery branch remains the clone target. |
| `screenshots/parent-home.png` | AC8 | Parent home hierarchy, create CTA, global settings and center create action | Historical Rev1 browser preview capture; not a Rev2 APK capture. |
| `screenshots/parent-lesson-picker.png`, `parent-lesson-picker-groups.png` | AC1 | Lesson selection stays in story setup; public and school/teacher-shared groups and in-place detail affordances are visible | Historical Rev1 browser preview captures; lesson cards use local preview data. |
| `screenshots/parent-sketch-guide.png` | AC2 | Optional guide is step-based, skippable and labeled static/not AI | Historical Rev1 capture; the Rev2 live CUA review separately observed all three distinct guide states. |
| `screenshots/teacher-session.png`, `teacher-session-interaction.png` | AC9–AC10 | Teacher setup, session sequence and interaction preview | Historical Rev1 captures; the Rev2 live CUA review separately stepped through all three slides and the separate sample gate. |
| `screenshots/school-manager-dashboard.png`, `platform-admin-dashboard.png` | AC9, AC11 | Both other web role entry points render | Historical Rev1 dashboard captures; both dashboards remain fixture previews. |

No real child media/profile data was used. The current Rev2 manual observations are described explicitly in `notes/EXECUTION.md`; historical PNGs are not presented as images of the Rev2 state.
