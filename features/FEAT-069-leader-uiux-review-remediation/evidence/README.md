# FEAT-069 evidence index

## Rev38 flow audit and Rev6 home verification

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV38_FLOW_ALIGNMENT_20261114.md` | Rev38 screen/component indexes versus current `UI_Project/` and FEAT-063 SRS v2.5-draft | Role-by-role partial/gap assessment and the Parent flow ordering conflict | Source/design review, not full route-by-route interaction testing or formal leader approval; Rev38 is proposal material. |
| `notes/EXECUTION.md` — Rev6 entry | Parent home card removal, all-workspace production build and local preview check | Build passed and current Parent home accessibility tree no longer contains the child summary card; start CTA and navigation remain | Browser preview check does not prove Android APK runtime or any backend behavior. |

Evidence for the leader-review UI remediation, captured 2026-11-14 (Asia/Saigon). Rev5 is the current UI-only scope: source/API details inform business-flow decisions, but the UI makes no backend/API/auth calls. Gender, mismatch analysis, transcript and guide output are local preview fixtures; FEAT-063 SRS v2.5-draft remains unsigned and canonical.

| Evidence | AC | What it establishes | Limitations |
|---|---|---|---|
| `notes/EXECUTION.md` | AC1–AC7 | Rev5 builds/typecheck/APK packaging and live visual review of Parent guide, transcript, mismatch, profile gender, and Teacher dashboard | Screens were inspected live; saved PNGs below are historical Rev1 captures. APK runtime on the supplied emulator may remain unverified. |
| `notes/OPEN_QUESTIONS.md` | AC1–AC7 | Gender/SRS gap, local analysis/transcript fixtures and API boundaries | Requires SRS/API/owner reconciliation before any fixture is treated as live product behavior or persisted. |
| `notes/API_UI_CROSSWALK_REV3.md` | AC1–AC9 | Historical source-to-route mapping used to understand business flow | Rev3 conditional API wiring was removed in Rev4; this crosswalk does not describe current runtime UI behavior. |
| `notes/SOURCE_PROVENANCE_REV2.md` | AC11–AC12 | Approved branch/source boundary and permitted backend comparison | Branch source comparison is read-only context; current delivery branch remains the clone target. |
| `screenshots/parent-home.png` | AC8 | Parent home hierarchy, create CTA, global settings and center create action | Historical Rev1 browser preview capture; not a Rev2 APK capture. |
| `screenshots/parent-lesson-picker.png`, `parent-lesson-picker-groups.png` | AC1 | Lesson selection stays in story setup; public and school/teacher-shared groups and in-place detail affordances are visible | Historical Rev1 browser preview captures; lesson cards use local preview data. |
| `screenshots/parent-sketch-guide.png` | AC2 | Optional guide is step-based, skippable and labeled static/not AI | Historical Rev1 capture; the Rev2 live CUA review separately observed all three distinct guide states. |
| `screenshots/teacher-session.png`, `teacher-session-interaction.png` | AC9–AC10 | Teacher setup, session sequence and interaction preview | Historical Rev1 captures; the Rev2 live CUA review separately stepped through all three slides and the separate sample gate. |
| `screenshots/school-manager-dashboard.png`, `platform-admin-dashboard.png` | AC9, AC11 | Both other web role entry points render | Historical Rev1 dashboard captures; both dashboards remain fixture previews. |

No real child media/profile data was used. Rev4 manual observations are described explicitly in `notes/EXECUTION.md`; historical PNGs are not presented as images of the current state.
