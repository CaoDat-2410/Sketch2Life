# FEAT-069 evidence index

## Rev18 Git Source Parity, Dashboard Cleanup & GPU Motion (`UI_Project/`)

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV18_GIT_PARITY_AND_PROMAX_MOTION_20261114.md` | Plan Rev18, AC18.1–AC18.5 | Cross-checks `UI_Project/` against `origin/dev` backend routes (`parent_story_runs.py`, `parent_ai.py`, `parent_profiles.py`, `teacher_ai.py`, `lesson_library.py`, `be1_registry.py`, `be1_sessions.py`), `origin/feature/fe-mobile-remediation`, `FEAT-063` SRS `v2.5-draft`, and Leader's checklist; documents Teacher Dashboard `.teacher-session-launcher`, residual copy cleanup, GPU-only motion choreography + `prefers-reduced-motion`, 5-workspace `vite build`, live `browser` subagent verification across host-verified `http://localhost:5171`–`5175` (inspected `final_step_145.png`), and 5/5 policy checks | Browser-local fixtures only; no API/auth/payment integration; open SRS conflicts (`gender`, auto context, pre-video activity timing) preserved |
| `../plan/PLAN_REV18_GIT_PARITY_AND_PROMAX_MOTION.md` | Exact approved scope | Hash-identified approval (`6E363D2923898FBF119FDE162C20EC9B785718AE7470BD628A3F2CD5205830A3`) for UI-only parity cleanup and motion polish inside `UI_Project/` | Does not authorize backend/API changes, SRS modifications, or legacy `apps/` edits |

## Rev17 Remove Preview/API Warning Banners (`UI_Project/`)

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV17_REMOVE_PREVIEW_WARNINGS_20261114.md` | Plan Rev17, AC1–AC4 | Documents removal of all 13 `.feedback-preview-note`, 8 `.preview-inline-note`, 10+ `.prototype-note`, `.flow-boundary`, `<FlowRecoveryDisclosure />`, `.dashboard-contract-note`, `.dash-panel-note`, `.web-detail-boundary`, `.web-modal-note`, `.web-feature-side`, `.web-preview-chip`, `BẢN THỬ`, Admin `is-amber`, and `preview`/`fixture`/`minh họa` copy across `UI_Project/`, single-column `.web-feature-grid--single` layout fix, 5-workspace `vite build`, live browser verification (`http://localhost:5196`–`5200`), and 5/5 policy validators | UI-only local fixtures; no API/auth/payment/AI connections; canonical FEAT-063 SRS `v2.5-draft` remains unsigned |
| `../plan/PLAN_REV17_REMOVE_PREVIEW_WARNING_BANNERS.md` | Exact approved scope | Hash-identified approval (`ED0E1D90E681F4EC2B08BA2EDB2DD4ADACD60C4ACE99F264DBBCC6B35CF39261`) for UI-only removal of preview/API warning clutter inside `UI_Project/` | Does not authorize backend/API changes, SRS modifications, or legacy `apps/` edits |

## Rev16 CI feature harness compliance (`4/5` -> `5/5`)

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV16_CI_HARNESS_COMPLIANCE_20261114.md` | Plan Rev16, AC1–AC4 | Documents why `Repository policy checks` (`tools/validate_harness.py`) caused `4/5` CI failures since `FEAT-068` creation, verifies 0-byte `.gitkeep` coverage in Git for `FEAT-068` & `FEAT-069` `evidence/{raw,metrics}`, normalizes `TASK_APPROVAL.md` `- Status: APPROVED`, and records passing results across all 5 policy validators | Local policy validation only; remote GitHub Actions `5/5` status reflects on GitHub after pushing the fix commit |
| `../plan/PLAN_REV16_CI_HARNESS_COMPLIANCE.md` | Exact approved scope | Hash-identified approval (`0AA001BF9B37015A51FD1E2C48785663B23C617F007C452685AB9796EE4A8C7C`) for harness metadata compliance only | Does not modify CI workflows, validator logic, application source, or SRS |

## Rev15 100% Leader UI/UX checklist closure (UI-Only, No API)

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV15_LEADER_100PCT_CLOSURE_20261114.md` | Plan Rev15, AC15.1–AC15.7 | Documents Parent multi-theme SVG line sketches, dead screen & debug toggle removal, divergence derivation, blue/purple token elimination (`0` bundle leaks), Teacher scoped `Lớp Lá 1` & inline `#session` 3A–3D flow, `UI_Project/DESIGN.md` sync, 5-workspace `vite build`, and live browser checks (`http://localhost:5196`–`5200`); committed & pushed as `56980fe7` | UI-only offline fixtures; no API/auth/persistence or automated test runner |
| `../plan/PLAN_REV15_LEADER_100PCT_CLOSURE.md` | Exact approved scope | Hash-identified approval (`0FEE9BE921A1C3AE9D8B04A097856C61B4385A0CE08F24A9FAFE01A77D8D7D5B`) for Rev15 UI-only closure | Does not modify FEAT-063 SRS `v2.5-draft` or backend APIs |

## Rev14 Web sidebar consolidation & multi-tab workbenches

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV14_WEB_SIDEBAR_CONSOLIDATION_20261114.md` | Plan Rev14, AC14.1–AC14.5 | Documents Teacher (`18->8`), School Manager (`15->8`), and Platform Admin (`12->9`) hub consolidation, `resolveRoute` alias routing, Topbar Bell notification link, Teacher document-import draft preview save, 5-workspace `vite build`, and live browser checks (`1440x900` & `390x844`) | UI-only local fixtures; no real file parser, OCR, backend persistence, or automated test runner |
| `../plan/PLAN_REV14_WEB_SIDEBAR_CONSOLIDATION.md` | Exact approved scope | Hash-identified approval (`3BAC2BB69B509AAF376E5F76424355E1261B6C44BE6406C66038C8D6E0D5F9EB`) for `UI_Project/shared/` consolidation only | Does not modify FEAT-063 SRS `v2.5-draft` or backend APIs |

## Rev13 Leader UI/UX remediation & UX Pro Max polish

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV13_LEADER_UX_PRO_MAX_20261114.md` | Plan Rev13 leader fixes + UX Pro Max CSS + polish verification | Documents Parent auto-context pill, pre-video outdoor activity flow, global Settings modal, voice streaming, green contrast/FAB/`::picker-icon` fixes, 5-workspace `vite build`, and live browser verification (`375x812` & `1440x900`) | Local fixtures only; pre-video activities/omitted tick/gender remain open SRS conflicts; no backend, Android emulator runtime, or automated test suite |
| `../plan/PLAN_REV13_LEADER_FULL_UX_PRO_MAX.md` | Exact approved scope | Hash-identified approval (`EF94D11CE9A4FA038E2ABEB42DAD6119E9A920E6D39AF0EA2B75F5F0E6C4B53A`) for `UI_Project/` updates excluding legacy `apps/` and SRS/backend | Does not approve API integration, SRS modification, or production launch |

## Rev11 Parent green action palette

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV11_PARENT_GREEN_ACTION_PALETTE_20261114.md` | Plan Rev11 AC1–AC5 | Explains the late CSS override, green palette correction, five-workspace build and live Parent phone-preview observation | Focused color review only; no saved screenshot, automated tests, Android runtime, API behavior or formal leader sign-off |
| `../plan/PLAN_REV11_PARENT_GREEN_ACTION_PALETTE.md` | Exact approved scope | Hash-identified approval for Parent palette correction and verification | Does not approve API integration, SRS change or other workspaces |

## Rev10 Admin/Manager visual refinement

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV10_VISUAL_REFINEMENT_20261114.md` | Plan Rev10 AC1–AC6 | Five-workspace production build, manual desktop/narrow review of all three supplied routes, local invoice detail modal, and the corrected 18×18 retirement checkbox | No automated tests, API/backend behavior, formal leader sign-off or project-wide visual acceptance; no screenshot files were saved |
| `../plan/PLAN_REV10_WEB_VISUAL_REFINEMENT.md` | Exact approved scope | Hash-identified approval for the three screenshot pages, responsive styles and fixture-only behavior | Does not approve API integration, SRS changes, hosting or production operations |

## Rev9 continuous action outcomes

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV9_ACTION_OUTCOME_CROSSWALK_20261114.md` | Plan Rev9 AC1–AC7 | Maps Rev38 screen/component IDs to current actions, outcomes, next/return routes and local-only gaps; records the screenshot root cause, historical v2.2 versus current v2.5 flow differences, and representative preview observations | Not an exhaustive manual keyboard/screen-reader audit; no Android APK runtime or API work; no formal leader sign-off |
| `plan/PLAN_REV9_CONTINUOUS_MOCKUP_FLOWS.md` | Exact approved scope | Hash-identified UI-only continuity audit and acceptance criteria | Does not approve API integration, SRS change or formal leader sign-off |

## Rev8 full flow audit and visual polish

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/REV8_FULL_AUDIT_AND_EXECUTION_20261114.md` | Plan Rev8, AC1–AC8 | All Rev38 IDs mapped to current mockup surfaces; Parent SRS-order correction; source/API boundaries; colors reviewed; five workspace builds, Parent typecheck and debug APK package | No emulator launch because ADB daemon failed; no APIs were called; leader/SRS conflict and unsupported contracts remain open; no new PNG screenshot was saved |
| `plan/PLAN_REV8_FULL_UI_AUDIT_AND_POLISH.md` | Exact approved scope | Hash-identified UI-only audit, correction, color and verification scope | Does not approve API integration, SRS change or formal leader sign-off |

## Rev7 whole-project mockup completion

| Evidence | Scope | What it establishes | Limitations |
|---|---|---|---|
| `notes/EXECUTION.md` — Rev7 entry | AC1–AC8 | Five-workspace build, Parent Android typecheck/APK packaging, Parent profile spacing, Teacher import confirmation, Manager four-gate behavior, Admin moderation, role preview startup and device availability | Screens were inspected live but no new screenshots were saved. ADB has no attached Android emulator, so APK runtime is unverified. All UI actions are fixtures; the prototype order conflict remains open. |
| `notes/OPEN_QUESTIONS.md` — Rev7 disposition | AC2–AC7 | States which transitions are present and which capabilities remain visual-only | Does not replace SRS v2.5-draft owner sign-off or leader acceptance. |
| `plan/PLAN_REV7_ALL_UI_MOCKUP_FLOWS.md` | AC1–AC8 | Exact approved scope, roles, flows and acceptance criteria | Rev38 is a visual proposal; API contracts may evolve. |

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
