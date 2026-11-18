# Teacher UI SRS layout diagnosis and demo proposal — Rev20

- Evidence ID: FEAT-066-EV-023.
- Date: 2026-11-11 (Asia/Bangkok).
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Plan: revision 20, SHA-256 0BAAFA4133B6ABDF9C225985C93CE32AF07F62A6E3C83C69B6F251DABC337219; matching approval is audit-only. Teacher UI implementation is not approved in this checkpoint.
- SRS authority: F:/Github/Sketch2Life/docs/context/SRS_AUTHORITY.md.
- Canonical source: features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md, v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5. The authority record says the draft awaits owner sign-off. §§1–31 are target requirements; §32 is not.

## Review basis

Read the canonical role/flow/screen requirements (§§3, 4, 5.2, 7.3–7.4, 8/NFR-13 and 29–30, UC-03/04/05/17, §21.5–21.6 and §31.8). Re-read the Teacher route/layout source, API adapter, lesson/import pages, and class/roster source in the authorized worktree. Visual review used prior FEAT-066 EV-018/EV-019 screenshots: Teacher dashboard and classes at 1440x900 and 390x844, lesson page at both sizes, and the class handoff state. The new shared icon presentation changed icon appearance after those captures, not the page layout. A fresh request to local port 127.0.0.1:5172 was blocked by sandbox socket permissions; no fresh browser capture or authenticated/backend flow was claimed. No tests/builds were run.

## Findings

### SRS flow and role-boundary gaps

1. **Core Teacher lesson-to-run flow is not complete in the product UI.** The route table maps T04 Sketch Deck, T06 Story Run, T07 projection, and T08 profile/settings to explicit API-unavailable pages. The frontend API adapter has no product occurrence/plan, server sample-selection, StoryRun/job, playback-token, projection-confirmation, Teacher profile/settings, or notification-inbox methods. This is a real product-flow dependency, not a layout-only problem. Source: apps/teacher-ui/src/App.tsx; apps/shared/backendApi.tsx; FEAT-066 EV-018.
2. **Structured lesson extraction review cannot finish.** T03 can upload/resume and read source-document/revision status, but the current API client has no write contract to save edited extraction text as an immutable revision and confirm it. SRS FR-T-06/07, UC-04 and FR-PL-09–11 require review/correction/confirmation before use. Keep that final action unavailable until the contract exists.
3. **Teacher profile creation is not API-backed.** T05 reads assigned classes, roster and consent; the source audit records profile POST as synthetic-pilot-only, not a product roster contract. SRS UC-03/FR-T-04 requires a structured create-and-enroll flow. Do not expose a preview create button as persisted success.
4. **Teacher class list includes a Manager-only handoff action in local preview.** T05ClassesScreen renders “Bàn giao cho … / Hoàn tất” and calls a local force-close/transfer function. Reassignment/offboarding belongs to School Manager use cases, while Teacher can operate only assigned classes (§3, §5.2, UC-12/FR-T-14). Remove this action from any Teacher demo; if an assignment is pending, show a read-only state without a Teacher mutation.
5. **Selection policy remains partly open.** SRS §5.2/FR-T-10/FR-PL-20 require server selection of one eligible child followed by Teacher confirmation, never free selection or cross-class fallback. Eligibility, consent inputs and reselection/no-candidate handling remain open under Q-01. The prototype must not invent those rules or use a Teacher-controlled child selector.
6. **Teacher notifications and quota chips are preview state, not API-backed in the current FE client.** The bell count, notification list and quota number come from TeacherContext fixtures; no Teacher inbox/quota method appears in backendApi.tsx. SRS NFR-26 says inbox is the source of truth. Hide counts or show unavailable status unless a compatible API becomes available.
7. **Organization/class context is fixture/config driven.** The SRS screen catalog includes selecting organization/class and limiting the UI to assigned classes (§21.5). The header class dropdown is shown only in local preview; backend screens use configured organization_id and a separate assigned-class list. The demo should make class scope explicit and must not treat a preview dropdown as an authorization boundary.

### Current UI clarity and layout findings

8. **Navigation exposes workflow stages as separate destinations.** Teacher sidebar presents roughly ten destinations, including AI Assisted, sample video, and classroom projection. These are related steps in the occurrence flow; Sketch Deck is optional and is not a standalone lesson-management area (§5.2, UC-05/17). Consolidate them under a guided “Buổi dạy” workspace, keeping AI Deck optional within that flow.
9. **Dashboard relies on fixture metrics and activity cards.** Class/child/lesson counts, remaining quota, unread notifications, sample-video status and recent activity are local preview data. The sample notice is confined to the account area rather than a prominent persistent preview banner. These values are not SRS-defined dashboard metrics and must never look like live product state.
10. **Lesson page presents editable creation UI even when prerequisites fail.** EV-019 shows “Chưa có Firebase ID token” while the create button/form remains visible. The action may fail at submission, but the screen does not offer a clear usable-versus-unavailable state. Gate edit/mutation controls on verified auth/API readiness; keep read-only explanation and retry path visible.
11. **Narrow layout keeps a permanent icon-only sidebar.** At 390px the rail occupies about 76px and hides navigation labels. No horizontal overflow was reported in EV-019, and Teacher Web's formal browser support target is desktop (NFR-30); this is a responsive usability improvement rather than a claimed SRS failure. Use a labeled compact bottom bar or drawer on narrow screens, with practical 44px targets and the same destinations.
12. **The Teacher shell contains Manager/Admin nav branches.** Teacher App routing rejects a non-Teacher session, but TeacherLayout still has Manager/Admin menu definitions. Keep the Teacher prototype role-pure and show the role-mismatch state outside that shell.

## Proposed Teacher UI demo set

### Global shell

- Desktop: left navigation with five primary destinations — **Bàn làm việc**, **Lớp & hồ sơ**, **Giáo án**, **Buổi dạy**, **Lịch sử**. Keep account identity, Help, inbox/unavailable state and logout separate from the task menu. The selected organization/class scope stays visible.
- Narrow viewport: replace the persistent icon-only rail with a labeled compact bottom navigation and a “Thêm” menu/drawer for secondary account/help items. Keep tap targets at least 44px where practical.
- Keep the current warm paper/graphite/school-blue family and monochrome outline icons, but reduce nested cards, colored accents and repeated KPI tiles. Use one clear page title, one primary action, consistent content width and plainly labeled section hierarchy.
- Show a persistent “Xem thử — dữ liệu minh họa, không lưu” banner for any fixture mode. In API mode, render loading/empty/error/unavailable states from the real response; never reuse fixture counts as a fallback.

### Screens and flow

| Demo screen | SRS intent and proposed composition | Current API boundary |
|---|---|---|
| 1. Bàn làm việc | One next-action area, real server-backed drafts/runs only, then a short assigned-class and lesson shortcut list. No synthetic KPI row or activity feed. | No Teacher occurrence/history/inbox/quota summary API; show empty/unavailable explanations rather than fixture success. |
| 2. Lớp & hồ sơ | Explicit assigned-class context; compact class list then class-scoped roster; consent state per child and purpose; minimal allowed profile fields. No handoff/assignment mutation and no child media by default. | Class/assignment/roster/consent reads exist. Product profile create/update API is missing. |
| 3. Giáo án | Reusable lesson list and focused editor for structured content, activities, version and visibility. Preserve PRIVATE draft creation; public request leads to PENDING_REVIEW, never self-publishes. | List/detail/create/update/archive/public-review APIs exist; retain cursor pagination and If-Match/idempotency behavior. |
| 4. Nhập giáo án | Three visible stages: select lesson/file → upload/parse status → review/correct/confirm immutable extraction revision. Show file constraints and safe OCR/parser errors. | Upload/status/revision read exists; immutable edited revision write/confirmation is missing, so stop before “confirmed/ready to use”. |
| 5. Buổi dạy | Contextual guided flow: choose assigned class and occurrence → pin lesson/version and plan/activity → safety checklist → optional Sketch Deck toggle. Keep the Deck surface white, sparse and 16:9 only when its API is available. | Occurrence/plan/checklist and Sketch Deck product endpoints are missing; show a clearly unavailable step, no completion toast/job. |
| 6. Video mẫu | Continue within the same occurrence: server selects one eligible child → Teacher confirms child/context → one drawing/upload and idea → transcript/subject review → script/storyboard review and confirm → truthful job state → safety-ready playback → explicit projection confirmation → complete/cancel. | Sample selection, StoryRun, jobs, playback, projection and run lifecycle APIs are missing. Do not show selectable children, fake progress, a generated video, or a successful projection in demo mode. |
| 7. Lịch sử | Occurrence/run history with server status, version/lineage and allowed actions; make active/error/awaiting-reconciliation states easy to understand, without fabricated percentages or state. | No Teacher history/run API in current client; present the dependency until available. |

The flow design preserves one-child-per-run, current assignment, scoped consent, exact revision confirmation, no child-media default access, quota semantics, safety gates and the §21.6 recovery paths. Open Q-01/owner policies remain visibly unresolved.

## Recommended first implementation slice after user approval

1. Teacher shell/navigation and desktop/narrow behavior.
2. Dashboard and classes/roster visual hierarchy with API/preview status made unambiguous; remove the Teacher handoff mutation.
3. Lesson library/editor around existing Lesson Library endpoints, with auth readiness gating.
4. Import page layout with an explicit block at the unsupported extraction-correction/confirmation step.
5. Keep occurrence, Sketch Deck, video, history, quota/inbox and settings states clearly unavailable; do not create fake end-to-end behavior.

This is a design proposal only. Await user acceptance before changing Teacher source. After Teacher UI review, the user can decide whether to apply an approved system to School Manager and Platform Admin.
