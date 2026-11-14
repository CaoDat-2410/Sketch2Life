# Rev9 action-to-outcome crosswalk — 2026-11-14

Approved plan: `plan/PLAN_REV9_CONTINUOUS_MOCKUP_FLOWS.md`
Plan SHA-256: `29B3B3F10C87B329FB5AF327DC5767CCEE7E5CF14CCFC047CA239B1B1C62EBFC`
Branch: `FE_UI_Project_Ver2`
Scope: action continuity review of the five primary `UI_Project/` preview workspaces.

## Authority and references

- Current product baseline: FEAT-063 SRS v2.5-draft, still awaiting formal owner sign-off. `docs/context/SRS_AUTHORITY.md` is the source-routing rule.
- Leader visual/flow references: `UI_Project/design-references/ui-mockups-rev38-20261030/SCREEN_INDEX.md` (P01–P12, T01–T07, M01–M02, A01–A02) and `ui-components-rev38-20261030/COMPONENT_INDEX.md` (UI01–UI09).
- Rev38 is generated proposal material based on an older SRS/API snapshot, not an approved contract. The leader's review notes are feedback; conflicts with v2.5 are kept open rather than silently resolved.
- The supplied screenshot of the generic Teacher detail dialog was reproduced from `DetailPanel` → unknown `ActionDialog` fallback. Generic fallback actions have been removed; applicable details now open named workflow destinations or show a status-specific reason to wait/return.
- The active Parent APK entry point is `UI_Project/parent-android/apps/mobile`, which bundles `parent-ui` into a local WebView. `UI_Project/parent-android/apps/ui-mobile` is documented as a separate legacy Expo experience, not the Parent APK target; its similarly generic prerequisite screen is intentionally outside this delivery scope.

## Historical SRS comparison — v2.2 versus current v2.5

The preserved file `D:\Capstone Project\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_V2.2_PRESERVED_20261028.md` was read for historical traceability only. Per `docs/context/SRS_AUTHORITY.md`, FEAT-063 v2.5-draft remains the current working source and is still unsigned.

| Area | Preserved v2.2 flow | Current v2.5-draft flow | UI/UX implication |
|---|---|---|---|
| Parent core sequence | Optional guide → capture → idea/audio and transcript confirmation → image/subject review → choose an outdoor activity → review profile context → story/script review → video generation and safety → playback. | Optional guide → capture → idea/audio and transcript confirmation → image/subject review → review minimum profile context → story/script review → video generation and safety → playable video → show lesson activities. | Keep the current preview ordered to v2.5. The leader review's pre-video activity placement is a real open conflict; do not silently restore the older step. |
| Parent guide | Optional, generic 3–5-step line sketch before drawing; it must not use child profile/media or replace subject review after capture. | Same optional, topic-only guide; failure/skip must not block drawing/capture. | The static topic/difficulty guide is a visual fixture. It is not AI output or a child-specific drawing screen. |
| Age and activity filtering | v2.2 lists the historical 36–155 month range and filters Parent activities before story generation. | v2.5 sets 36–120 months and places configured activity details after video becomes playable. | Do not use the historical age filter or activity position as current behavior. |
| Lessons, roles and platform | v2.2 does not contain the later shared lesson platform scope. | v2.3 onward adds public/shared/assigned lesson access, school organization roles, profile grants, lesson history/feedback and scoped quota; v2.4–2.5 clarify development direction and separate target requirements from dated as-built/source observations. | Library, role workspaces and shared lesson states belong in the broader mockup; they remain fixture previews unless connected contracts are explicitly implemented. |
| Teacher guide/deck | v2.2 describes generating a shared Teacher deck after lesson-plan approval. | v2.5 makes Teacher Deck optional during the session; if enabled, it is shared across the occurrence, while the sample-video run remains separate. | A deck toggle and preview should be shown as optional. Do not imply deck creation is mandatory or that it is the Parent guide. |

This comparison explains why the preview may differ from an older Rev38 board or v2.2 paragraph while following v2.5. It does not constitute owner sign-off, leader acceptance, or evidence that any API/service flow is available.

## Interaction changes in Rev9

1. Teacher lesson details now open the preparation route only for approved/shared lessons. Drafts explain why they cannot yet be used; drafts also have a direct “Chỉnh sửa bản nháp” action that reopens the three-step authoring form with fictional editable fields. A draft edit updates that one row in Teacher preview only. A pending-review lesson explains that it must wait for review.
2. Teacher lesson authoring has explicit “Lưu bản nháp” and “Gửi quản lý rà soát” outcomes. A submitted item becomes “Chờ rà soát · preview” in the Teacher list. The UI states that Manager uses an independent fixture queue; this action does not send the item to another role or to a server.
3. Generic wizard completion has a role/route-specific named continuation for every route that renders `WizardPage`; completion also offers “Xem lại từ đầu”. The destination notice says which data is fixture-only.
4. Manager publication review keeps approval disabled until all four review gates are checked. After a preview decision, it shows the resulting status and opens the next pending fixture request, or states that none remain.
5. Read-only operational detail cards now announce “Mở chi tiết …”; their dialog action says “Đóng chi tiết” instead of “Đã hiểu”, so it does not suggest that a workflow step was completed.
6. Existing collection detail destinations are contextual: approved Teacher lesson → preparation; Teacher class → session; Manager class → lifecycle; Manager teacher → assignment; Admin organization → account/permission review. Draft/pending lesson outcomes remain status-specific.
7. Parent's optional guide was stepped from guide step 2 to step 3 and then to capture. Capture presents camera/gallery choices and keeps continuation disabled while no image is selected, with an explicit empty state.

## Rev38 screen action map

| IDs | Current entry/action → visible outcome | Remaining mismatch or boundary |
|---|---|---|
| P01 | Start story → choose child; lesson selection is available in setup. | Child selection is not surfaced as a selected-profile card on Home by owner request; Rev38 shows a library entry. Profile selection remains in story setup and Family Profile. |
| P02 | Open a lesson → read details → select it for the next story, or return to the lesson list. | Local lesson fixture; no current Parent lesson/profile API is called. |
| P03 | Optional three-step guide → next/previous → continue to capture, or skip to capture. | Static topic/difficulty fixture, not AI output. The guide appears before capture rather than integrated into a live drawing surface. |
| P04 | Capture/select image → explicit empty state; continue stays disabled until an image is available. | Camera/gallery, image analysis and mismatch result are not run against a service. No media was selected during this review. |
| P05 | Enter/edit idea or sample transcript → confirm subject and minimal context → proceed to script review. | Rev38 groups subject before idea/context; current ordering follows SRS v2.5 §5.1. The leader/SRS ordering conflict is still unresolved. Audio transcription is not performed. |
| P06 | Review local script → request a limited rewrite or continue. | Story generation and rewrite remain local preview state. |
| P07 | Continue to a clearly labeled generation/job state and back to script where offered. | No durable job, retry/reconciliation, automatic safety decision, or job resume API is mounted in the preview path. |
| P08 | Reach the local video/result state; activities remain after the playable-video step in the current SRS order. | Video playback/captions/completion are not established as production behavior; activity timing requested in the leader review still conflicts with SRS §5.1. |
| P09 | Open history, revisit a sample story and reach lesson-scoped feedback preview. | Retention windows, deletion lifecycle and a live feedback thread are not connected. |
| P10 | Open Family Profile → view/edit profile and access Settings there; profile actions are separated. | Gender is an owner-requested UI-only session field; profile CRUD/grants are not connected. |
| P11 | Open sign-in/register/recovery previews and receive local validation/preview boundary. | No end-to-end app identity/activation operation is claimed by this UI pass. |
| P12 | Open usage/quota preview and see unavailable purchase/billing state. | Numeric quota/admission and payment are not live or transacted. |
| T01 | Dashboard metric/list → lessons, classes, session or review queue. | Counts are from local source-shaped fixture rows, not analytics/API responses. |
| T02 | Soạn giáo án → 3 authoring sections → save draft or mark pending review → see row in Teacher list; draft detail reopens editor. | Manager queue is a separate static fixture. Cross-role transfer, revision persistence and publication are not performed. |
| T03 | Select a local file → review editable sample extracted fields → confirm → return to lesson library. | The file is not parsed or uploaded; extracted values are seeded examples. |
| T04 | Prepare occurrence (class, approved lesson/version, plan, activities, safety, confirmation) → open session; optional deck can be previewed from session flow. | Prepared plan and deck do not persist or become attached to a server occurrence. |
| T05 | Open classes/children preview; class detail routes to session and teacher child form has a local completion state. | Roster/profile reads and updates are fixture-only. |
| T06 | Separate sample run: eligibility confirmation → activity/artwork → idea/subject/context → script → job/result preview → presentation. | Child eligibility, consent, photo handling, job creation and video are not real. No child media was submitted. |
| T07 | Confirm selected occurrence/video → open presentation surface → proceed to run-control preview. | Playback is explicitly unavailable without a server token; no live presentation command is sent. |
| M01 | Select a version → inspect content/history → complete four gates → record preview decision → open next pending item. | Review state is local and its fixture queue is independent of Teacher T02. No public lesson is actually published. |
| M02 | Manager routes open teachers/invites/groups, assignment, roster, class lifecycle/capacity, quota and billing workspaces; actions update visible local states where offered. | Organization management, invite, assignment, transfer, entitlement and billing actions are not persisted or sent. |
| A01 | Select a moderation item → record a required preview decision/reason; visible items expose state-specific hide/reopen actions. | No moderation API write or server audit is performed. |
| A02 | Dashboard links open jobs, health, billing-ops, audit and notifications; operational card detail is read-only and can be closed. | Sensitive operational data, account entitlement and platform actions remain absent/fixture-only. |

## Rev38 component map

| ID | Current interaction/outcome | Boundary |
|---|---|---|
| UI01 | Shared controls, validation, buttons and focusable navigation are used across role workspaces. | Rev38 colors/components are references, not approved production tokens. |
| UI02 | Parent sheets/dialogs confirm lesson, subject, script/context and local preview choices; each can be closed or returned from. | State is not sent to APIs. |
| UI03 | Manager/Admin decisions require review fields/gates and show the resulting preview status. | No real permission, publish or moderation decision. |
| UI04 | Toasts/inline status describe local saves, decisions and no-op boundaries. Persistent outcomes also appear in the relevant fixture list/detail where applicable. | Toast is not evidence of server persistence. |
| UI05 | Empty image, unavailable playback, status filters and recovery-state disclosure explain the required next action or unavailable capability. | Recovery states are examples, not live server errors. |
| UI06 | Teacher import has file-choice, seeded extraction review and adult confirmation steps. | File content is not read, uploaded or parsed. |
| UI07 | Parent/Teacher job and quota routes explain stage/admission concepts and unavailable live data. | No quota charge, AI job, payment or retry is issued. |
| UI08 | Teacher/Manager role workspaces show lesson/profile/group/grant concepts and local decision controls. | Parent/child profile and cross-role grant contracts remain incomplete. |
| UI09 | Teacher/Manager feedback inbox preview shows scoped threads and local reply states. | No live notification or lesson feedback message is transmitted. |

## Manual observations and build

- Parent local browser: guide step 2 → step 3 → capture; capture explicitly showed no image and disabled continuation. This did not test camera permission, file selection, Android WebView or APK runtime.
- School Manager local browser: all four M01 checks enabled the review action; approval displayed “Đã duyệt · preview”, then “Mở yêu cầu kế tiếp”; the next fixture rendered with its own unchecked gates.
- Teacher local browser: authoring submission displayed a pending-review row and the pending detail gave status-specific guidance. The new “edit existing draft” branch was source-reviewed and build-checked, not manually clicked in this pass.
- Platform Admin moderation preview was previously walked in the same local preview session; a decision changed the displayed fixture status and stated no backend write.
- Shared portal opened with the Teacher web preview. The Parent route is the mobile UI WebView bundle, but no Android runtime was verified in this pass.
- `npm run build` from `UI_Project` passed all five workspaces (Parent, Teacher, School Manager, Platform Admin and shared web portal).
- `git diff --check` passed. No automated tests were added or run.

## Conclusion and unresolved items

The flow clarity issue was not confined to the screenshot: the Teacher lesson draft had no direct continue-edit action, generic details obscured whether a workflow or a read-only disclosure had opened, and the Manager decision previously lacked an explicit next queue item. These routes now have clearer local outcomes and named continuations.

The Rev38 folders are **not matched 100%** and this pass is **not formal leader acceptance**. The most material unresolved points are: Parent P04/P05 ordering versus canonical SRS v2.5 §5.1; activity timing in the leader review versus §5.1; the separate Teacher/Manager preview fixtures; unsupported live Parent story/AI/ASR/video/quota/profile operations; unsupported staff-role management/auth/billing/operational contracts; and UI-only gender. These are integration/requirement boundaries, not steps silently completed by the mockups.
