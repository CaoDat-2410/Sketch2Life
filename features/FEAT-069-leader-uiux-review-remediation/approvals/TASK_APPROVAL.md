# FEAT-069 task approval

- Status: APPROVED
- **Status:** APPROVED for the exact scope in Plan Rev1.
- **Approver:** Project owner, direct instruction in this conversation: “bạn làm sao cho đáp ứng yêu cầu của leader cho tôi đi”.
- **Recorded timestamp:** 2026-11-14 00:41:49 Asia/Saigon.
- **Approved plan:** `features/FEAT-069-leader-uiux-review-remediation/plan/PLAN.md`.
- **Plan revision:** 1.
- **Approved plan SHA-256:** `F5D04A3A1FABEE62B4CD59B3E34221B4A0FA063D857195126302BC517443314F`.
- **Scope:** implement review-compatible Parent mobile and Teacher web UI improvements; preserve FEAT-063 SRS v2.5-draft and current API/security boundaries; document unresolved leader/SRS/API conflicts; build and inspect the affected UIs; update feature/source records; run security validation before the previously authorized normal push to `origin/FE_UI_Project_Ver2`.
- **Acceptance criteria:** AC1–AC10 in the hash-identified Plan Rev1.
- **Exclusions:** backend/API/database/auth/schema/SRS/provider/deployment changes; shared API writes; live ASR/AI calls; unsupported gender field; Parent outdoor activities before video; removal of required context/script confirmation; generated raster assets; Child Expo changes; force push/history rewrite.
- **Approval basis:** the user's direct request authorizes this bounded implementation. Leader transcript text is feedback, not a change to canonical product/SRS/API requirements.

## Plan Rev2 approval

- **Status:** APPROVED for the exact UI-only scope in Plan Rev2.
- **Approver:** Project owner, direct instruction in this conversation: “nói chung giờ tôi muốn bạn đáp ứng toàn bộ yêu cầu của leader được không, tôi đã cung cấp hết dữ liệu cần có để bạn làm rồi đó”.
- **Recorded timestamp:** 2026-11-14 01:28:17 Asia/Saigon.
- **Approved plan:** `features/FEAT-069-leader-uiux-review-remediation/plan/PLAN_REV2.md`.
- **Plan revision:** 2.
- **Approved plan SHA-256:** `6239B3640D367A2EA847DDA97F1FAE5DB9978222F4E3362E43BBD5065BB3B6ED`.
- **Scope:** complete the remaining Parent/Teacher leader-review UI items as review prototypes; keep SRS v2.5-draft canonical, preserve adult context confirmation, mark the requested pre-video activity and local gender field as proposed preview behavior, and disclose unavailable API/AI paths; build, visually inspect, document evidence, validate repository security, and push normally to the previously authorized `origin/FE_UI_Project_Ver2` if fast-forwardable.
- **Acceptance criteria:** AC1–AC12 in the hash-identified Plan Rev2.
- **Exclusions:** backend/API/auth/schema/database/SRS/provider changes, API writes, live AI/ASR, persistent gender, child data/media, automated tests, release signing, Child Expo changes, force push/history rewrite.
- **Approval basis:** this direct user request authorizes the UI-only implementation against the full leader transcript. It does not sign off the unsigned canonical SRS or authorize backend contract changes.

## Source boundary checkpoint — 2026-11-14

- The project owner confirmed `UI_Project/` is the primary UI/UX to revise and the top-level `apps/` tree is legacy UI excluded from this handoff. The owner also reiterated that the deliverable must satisfy the leader's complete review.
- Rev2 remains the approved implementation plan and hash above; its implementation targets remain the `UI_Project/` Parent Android/WebView and three web role workspaces.
- A read-only comparison used the permitted newer backend source `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e`. This branch includes Parent profile/story router groups that are not mounted in the delivery branch at `2518dc07`; no such routes are represented as connected in the UI handoff.
- No source from the legacy top-level `apps/` directory was copied or added to the run targets.

## Plan Rev3 approval — API-aligned UI/UX completion

- **Status:** APPROVED for the exact frontend-only scope in Plan Rev3.
- **Approver:** Project owner, direct instruction in this conversation: “dựa vào API đang có để build UIUX lên đi ... giúp tôi check xem các API để mình làm UIUX đúng ... hoàn chỉnh 100% yêu cầu của leader”.
- **Recorded timestamp:** 2026-11-14 02:30:58 Asia/Saigon.
- **Approved plan:** `features/FEAT-069-leader-uiux-review-remediation/plan/PLAN_REV3.md`.
- **Plan revision:** 3.
- **Approved plan SHA-256:** `21A1FB640990D078793918AFCA651394FBACB42BFD0F80C173B28A385BFCAEB9`.
- **Scope:** Align the Parent Android and three web role workspaces with current delivery-branch API contracts and the leader review; distinguish mounted endpoints from allowed newer-branch references; preserve preview-only behavior wherever identity or routes are missing; build, visually review, update feature evidence, validate repository security, and publish normally to the previously authorized branch if fast-forwardable.
- **Acceptance criteria:** AC1–AC10 in the hash-identified Plan Rev3.
- **Exclusions:** backend/API/schema/auth/provider/SRS changes or route merges; live API/AI calls or database writes during implementation/QA; forbidden branches as source; legacy `apps/` and Child Expo; force push/history rewrite; automated tests.
- **Approval basis:** the owner's direct request authorizes this bounded frontend work. It does not authorize backend integration changes or claim missing runtime services are working.

## Plan Rev3 Parent Library addendum approval

- **Status:** APPROVED for `plan/PLAN_REV3_ADDENDUM_PARENT_LIBRARY.md`.
- **Approver:** Project owner, direct request in this conversation to build UI/UX against the APIs currently present in the project and complete the leader's requirements.
- **Scope:** conditionally read the current Parent public/shared Lesson Library and invitation APIs when the Firebase token bridge exists; fetch selected lesson detail on demand; use the typed invitation accept/decline operation only after user selection; preserve preview/no-fallback error states; leave Parent profile/story/AI/video unsupported flows preview-only.
- **Exclusions:** backend/API/auth/schema/SRS changes, live API calls during implementation/QA, unsupported Parent flows, user/child data, automated tests.
- **Approval basis:** direct owner instruction; see exact limits in the addendum.

## Plan Rev4 UI-only clarification approval

- **Status:** APPROVED for this exact UI-only scope.
- **Approver:** Project owner, direct clarification in this conversation: “cứ làm UIUX theo đúng yêu cầu của leader là được không phải ghép hay nối API gì cả”.
- **Approved plan:** `plan/PLAN_REV4_UI_ONLY.md`.
- **Plan revision:** 4.
- **Approved plan SHA-256:** `EE85CB380638985969419A38646B1D72383C74CC390027C903D1950C387FF4C3`.
- **Scope:** Use API/source only as business-flow reference; remove conditional API/auth wiring; align role UI flows with the leader disposition, including post-video Parent activities and no unsupported gender field; show Parent Settings only on the Family Profile page; visually verify and build the UI workspaces and Parent APK.
- **Exclusions:** backend/API/auth/schema/database/SRS changes; live calls/writes; real child data/media; legacy `apps/`, Child Expo; automated tests; force push/history rewrite.
- **Approval basis:** direct owner clarification supersedes the prior Rev3 interpretation for current UI work.

## Plan Rev5 — complete API-informed UI preview states

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV5_PREVIEW_COMPLETION.md`.
- **Approver:** Project owner, direct request in this conversation to complete the mismatch, speech-to-text, drawing-guide and Teacher Dashboard UI from source/API references; add gender to Parent profile and child selection; and run the UI for review.
- **Plan revision:** 5.
- **Approved plan SHA-256:** `F49F00D71E5E0D84B2EA695A1BB63010DA2E82E8A8FAC356542BDA145279262A`.
- **Scope:** UI-only; no API calls. Mismatch-result preview modal, editable fixture transcript states, optional generic-topic drawing guide, source-shaped Teacher Dashboard preview, and local-only gender controls on Parent profile and child picker. Build and run the UI for review.
- **Exclusions:** backend/API/auth/schema/SRS changes, live service calls/writes, persisted gender, real child data, legacy top-level `apps/` implementation, automated tests and history rewrite.
- **Approval basis:** direct owner instruction. The canonical SRS is not amended; gender remains a preview-only product question.

## Plan Rev6 — streamline and polish Parent home

- **Status:** APPROVED for the exact scope in `plan/PLAN_REV6_PARENT_HOME.md`.
- **Approver:** Project owner, direct instruction in this conversation: remove the “ĐANG DÙNG HỒ SƠ” home card because a child is already selected at story start, and make the homepage visually polished.
- **Recorded timestamp:** 2026-11-14 11:02:48 Asia/Saigon.
- **Plan revision:** 6.
- **Approved plan SHA-256:** `B5AF1EB11C4DB22B2F4EC60F78786D5E62A3025E5638531BCC00BE0C24BA8CB1`.
- **Scope:** UI-only removal of the duplicate selected-child home card; refine Parent home hero/spacing; keep profile and story-start selection behavior; build and review the running Parent preview; record evidence/status.
- **Exclusions:** API/auth/persistence/data-model/SRS/backend changes; changes to other workspaces or legacy `apps/`/Child Expo; new child data/media/assets; automated tests; history rewrite.
- **Approval basis:** direct owner request. No other product or backend behavior is authorized by this approval.

## Plan Rev7 — complete project UI mockup flows

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV7_ALL_UI_MOCKUP_FLOWS.md`.
- **Approver:** Project owner, direct instruction in this conversation to complete mockups for the whole project's UI/UX according to the leader-provided flow, use sample data so future API wiring changes data rather than screen design, and not integrate API now. Owner also supplied a Parent profile screenshot showing action buttons touching/overlapping.
- **Recorded timestamp:** 2026-11-14 11:26:40 Asia/Saigon.
- **Plan revision:** 7.
- **Plan SHA-256:** `EF292106848FEAF341591D5DA002DA679F08E19BBBAF719F41F379536166C39F`.
- **Scope:** Reachable mockup flows for Parent P01–P12, Teacher T01–T07, School Manager M01–M02, Platform Admin A01–A02 and shared UI01–UI09 under `UI_Project/`, plus Parent profile action spacing fix. Use Rev38 as the requested UI flow reference and local typed fixture data/state only.
- **Exclusions:** API/auth/network integration; backend, schema, database, SRS or provider changes; real child/user data; real email/payment/AI/ASR actions or persistence; legacy top-level `apps/` and Child Expo; generated bitmap assets; automated tests; force push/history rewrite.
- **Conflict note:** The Rev38 Parent sequence differs from current unsigned FEAT-063 SRS v2.5-draft. Rev38 sequencing is approved only for this visual prototype per the owner's direct request; SRS requirements remain unchanged and the conflict remains an open product question.

## Plan Rev8 — full UI flow audit and visual polish

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV8_FULL_UI_AUDIT_AND_POLISH.md`.
- **Approver:** Project owner, direct instruction in this conversation to recheck all UI workspaces against the two leader Rev38 folders, review notes, current source and available API contracts; add missing mockups; use fictional values; improve UX and tone down bright colors; and avoid needing a UI redesign when APIs are connected later.
- **Recorded timestamp:** 2026-11-14 (Asia/Saigon).
- **Plan revision:** 8.
- **Plan SHA-256:** `1DD3518361F10CD518E152D5EC70EE3CB19F8734587EFA15A875DEFD161A7FE9`.
- **Scope:** Audit all five primary `UI_Project/` workspaces against Rev38, leader review, current SRS and source/API evidence; fix Parent sequencing/context/priority/sample-image gaps; calm and harmonize the palette; keep fixture-only behavior; build/package and visually inspect.
- **Exclusions:** API/auth/network/backend/schema/SRS/data-model changes; real values/persistence; external AI/ASR, payment, upload, mail, or production operations; legacy `apps/` and Child Expo; generated raster assets; automated tests; history rewrite.
- **Open constraints:** SRS v2.5-draft is canonical and unsigned. Keep Parent outdoor activities after the story/video as SRS §5.1 specifies, pending resolution of the leader-review conflict; gender remains a local preview field pending a canonical contract. This approval does not constitute leader sign-off or API readiness.

## Plan Rev9 — continuous mockup flows across all UI workspaces

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV9_CONTINUOUS_MOCKUP_FLOWS.md`.
- **Approver:** Project owner. Prior direct instruction authorized completion of the whole project's UI/UX with mock data and no API wiring; the latest feedback says multiple screens stop before their flow is understandable and supplied a screenshot of a generic terminal modal.
- **Recorded timestamp:** 2026-11-14 (Asia/Saigon).
- **Plan revision:** 9.
- **Plan SHA-256:** `29B3B3F10C87B329FB5AF327DC5767CCEE7E5CF14CCFC047CA239B1B1C62EBFC`.
- **Scope:** Inventory primary interactions throughout Parent, Teacher, School Manager, Platform Admin and the portal; replace ambiguous generic dead ends with context-specific local flow outcomes/navigation; compare the preserved v2.2 SRS historically while retaining v2.5-draft as current authority; build and visually review.
- **Exclusions:** API/auth/network/backend/schema/SRS changes; real data or persistence; provider, upload, payment, AI or ASR operations; legacy `apps/` and Child Expo; automated tests; formal leader/SRS sign-off claims; force push/history rewrite.
- **Approval basis:** Owner's already-authorized end-to-end mockup scope plus the latest direct feedback about widespread dead ends. This is UI-only authorization and does not resolve product conflicts or approve API integration.

## Plan Rev10 — polish Admin/Manager review screens

- **Status:** APPROVED for the exact UI-only scope in plan/PLAN_REV10_WEB_VISUAL_REFINEMENT.md.
- **Approver:** Project owner, direct request in this conversation to use the supplied screenshots to improve the UI and UX of the Platform Admin Activity Catalog, quota/reconciliation page and School Manager publication review; preserve the expected flows and make the screens visually excellent.
- **Recorded timestamp:** 2026-11-14 (Asia/Saigon).
- **Plan revision:** 10.
- **Plan SHA-256:** `0356B5B8CB6D8A2F8F0B4641158F91187823E99A9A3CE194D68EF86034F9E012`.
- **Scope:** Refine layout, styling, typography, spacing, focus/selected/disabled states and responsive behavior on the three shown UI_Project/shared/roleFlows.tsx surfaces, using existing Rev38 visual guidance and local fixtures.
- **Exclusions:** No API/auth/network/backend/schema/SRS/business-flow/data changes; no live payment/AI/provider operations; no generated imagery, hosting deployment, tests, legacy Expo or top-level legacy apps/; no force push.
- **Approval basis:** Direct owner authorization for this UI/UX refinement; no formal leader acceptance or SRS change is implied.

## Plan Rev11 — Parent green action palette

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV11_PARENT_GREEN_ACTION_PALETTE.md`.
- **Approver:** Project owner, direct instruction with screenshots to change the shown primary colors to green.
- **Recorded timestamp:** 2026-11-14 (Asia/Saigon).
- **Plan revision:** 11.
- **Plan SHA-256:** `A4C80795D266BE6220FD426F2425294C1331E2346FEB1BBFBEC0E39E8A547614`.
- **Scope:** Correct Parent UI stylesheet cascade so the “Bắt đầu kể” primary action matches the selected “Tất cả” green interaction palette, preserve gold icon accents and unrelated semantic colors, then build and visually review the Parent preview.
- **Exclusions:** No API/network/auth/backend/schema/SRS/data/flow changes; no changes to other role workspaces, legacy `apps/` or Child Expo; no generated raster assets; no automated tests; no force push/history rewrite.
- **Approval basis:** Direct owner request. The target shade is inferred from the selected green control in the supplied screenshot; this does not imply leader sign-off or production/API readiness.

## Plan Rev12 — Green palette for the three web roles

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV12_GREEN_WEB_ROLE_PALETTE.md`.
- **Approver:** Project owner, direct request to change the shown colors to green followed by a question about applying the palette to the three web roles.
- **Recorded timestamp:** 2026-11-14 (Asia/Saigon).
- **Plan revision:** 12.
- **Plan SHA-256:** `4DA12CF06585D6D7141D4A62167C657541B45562ADF045F34A2F3F20EDA1ADAC`.
- **Scope:** Change brand/action colors in Teacher, School Manager, Platform Admin, and the shared role-entry preview to a green family aligned with Parent; preserve semantic statuses and yellow accents; build and visually review all four web previews.
- **Exclusions:** No API/network/auth/backend/schema/SRS/data/flow changes; no layout or Parent changes; no generated assets; no automated tests; no force push/history rewrite.
- **Approval basis:** The owner's follow-up was interpreted as requesting the same green palette on the three web role experiences. This remains UI-only styling and does not imply formal leader acceptance or API readiness.

## Plan Rev13 — Full Leader review remediation & UX Pro Max polish in `UI_Project/`

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV13_LEADER_FULL_UX_PRO_MAX.md`.
- **Approver:** Project owner, direct instruction confirming legacy `apps/` is excluded, `UI_Project/` is the official UI/UX, and instructing implementation of Leader review requirements alongside `nextlevelbuilder/ui-ux-pro-max-skill` persona polish.
- **Recorded timestamp:** 2026-11-14 17:01:40 +07:00 (Asia/Saigon).
- **Plan revision:** 13.
- **Plan SHA-256:** `EF94D11CE9A4FA038E2ABEB42DAD6119E9A920E6D39AF0EA2B75F5F0E6C4B53A`.
- **Scope:** Complete remaining Leader review gaps in `UI_Project/parent-ui/` (global Settings gear access, removing manual context confirmation gate, moving outdoor activity selection pre-video in `script` and unlocking post-video viewing, audio transcript/copy cleanup, Parent green/sage token cleanup) and apply `ui-ux-pro-max` contrast, typography, touch-target, accessibility, and persona workflow polish across `UI_Project/parent-ui/` and `UI_Project/shared/` web workspaces; build and visually verify all 5 workspaces cleanly.
- **Exclusions:** No legacy `apps/` or `child-experience/` edits; no API/network/auth/backend/schema/SRS edits; no real child/user data, AI/ASR/payment calls, or generated raster assets; no force push/history rewrite.
- **Approval basis:** Direct owner instruction explicitly directing Leader review fixes + UX Pro Max polish on `UI_Project/`. UI-only boundary and open SRS v2.5-draft vs Leader conflicts remain documented cleanly.


## Plan Rev14 — Web sidebar consolidation & unified task workbenches (`UI_Project/shared/`)

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV14_WEB_SIDEBAR_CONSOLIDATION.md`.
- **Approver:** Project owner, direct instruction in this conversation asking to merge Teacher `Giáo án của tôi` + `Nhập & rà soát tài liệu` and consolidate similar fragmented sidebar screens across `UI_Project/` web roles (`“ok giúp tôi đi, với xem gộp được phần nào giống như vậy thì gộp cho tôi luôn, tôi muốn tối ưu UX để người dùng dễ sử dụng á”`).
- **Recorded timestamp:** 2026-11-14 18:02:15 +07:00 (Asia/Saigon).
- **Plan revision:** 14.
- **Plan SHA-256:** `3BAC2BB69B509AAF376E5F76424355E1261B6C44BE6406C66038C8D6E0D5F9EB`.
- **Scope:** Consolidate related sidebar items into unified multi-tab workspaces across Teacher (`18 -> 8` items), School Manager (`15 -> 8` items), and Platform Admin (`12 -> 9` items) inside `UI_Project/shared/` (`webWorkspace.tsx`, `roleFlows.tsx`, `rev13ProMax.css`); add alias route resolution and Topbar Bell inbox shortcut; allow saving reviewed import preview draft into Teacher library preview; build and visually verify on desktop & mobile viewports.
- **Exclusions:** No backend/API/auth/schema/SRS edits; no legacy `apps/` or `child-experience/` changes; no live parsing/OCR/AI/billing calls; no force push/history rewrite.
- **Approval basis:** Direct owner instruction explicitly directing consolidation of overlapping web sidebar views while keeping SRS workflows and boundaries intact.


## Plan Rev15 — 100% Leader UI/UX Checklist Closure in `UI_Project/` (UI-Only, No API)

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV15_LEADER_100PCT_CLOSURE.md`.
- **Approver:** Project owner, direct instruction in this conversation requesting 100% completion of all remaining Leader UI/UX review items on `UI_Project/` without backend API integration (*“giờ làm sao để thành mức đạt hết là được, nhưng nói trước là không cần nối API nhé, vì nối API là nhiệm vụ của leader sau khi check UIUX của tôi xong á, giờ bạn giúp hoàn thành 100% đi”*).
- **Recorded timestamp:** 2026-11-14 18:48:36 +07:00 (Asia/Saigon).
- **Plan revision:** 15.
- **Plan SHA-256:** `0FEE9BE921A1C3AE9D8B04A097856C61B4385A0CE08F24A9FAFE01A77D8D7D5B`.
- **Scope:** Topic-specific 4-theme/3-step SVG line sketches & removal of dead `renderSketchGuide` screen and `review` developer-test toggle pills in `UI_Project/parent-ui/`; complete seamless Teacher Session flow (class scope fix `Lớp Lá 1` / `01 Lớp phụ trách`, all 3 enabled lessons with lesson-specific activities & custom SVG line-sketch slides, inline sample-child confirm + drawing upload preview + idea/subject/script approval + video preview & class playback confirm inside `#session`); clean removal of remaining Admin SVG purple & CSS blue/draft tokens; `UI_Project/DESIGN.md` sync; full build, live browser visual check, and security check.
- **Exclusions:** No backend/API/database/auth/schema/SRS edits; no legacy `apps/` or `child-experience/` changes; no live AI/ASR/billing/external network integration; no force push/history rewrite.
- **Approval basis:** Direct owner instruction explicitly scoping this pass to 100% UI/UX completion in `UI_Project/` without API wiring.


## Plan Rev16 — CI Feature Harness Compliance (`4/5` -> `5/5`)

- **Status:** APPROVED for the exact scope in `plan/PLAN_REV16_CI_HARNESS_COMPLIANCE.md`.
- **Approver:** Project owner, direct instruction in this conversation pointing to GitHub CI commits showing `4/5` checks failing (`"bạn thấy báo lỗi 4/5 không tôi muốn bạn fix cái đó"`).
- **Recorded timestamp:** 2026-11-14 19:15:30 +07:00 (Asia/Saigon).
- **Approved plan:** `features/FEAT-069-leader-uiux-review-remediation/plan/PLAN_REV16_CI_HARNESS_COMPLIANCE.md`.
- **Plan revision:** 16.
- **Plan SHA-256:** `0AA001BF9B37015A51FD1E2C48785663B23C617F007C452685AB9796EE4A8C7C`.
- **Scope:** Restore `Repository policy checks` (`tools/validate_harness.py`) by adding 0-byte `.gitkeep` placeholders under `evidence/raw/` and `evidence/metrics/` for `FEAT-068` and `FEAT-069`, normalizing `- Status: APPROVED` formatting in `FEAT-068/approvals/TASK_APPROVAL.md` (preserving existing authorization scope verbatim) and `FEAT-069/approvals/TASK_APPROVAL.md`, updating `FEAT-069` records, verifying all 5 policy validators and clean-clone tracking, and committing/pushing normally (fast-forward) to `origin/FE_UI_Project_Ver2`.
- **Exclusions:** No runtime/UI/backend/CI-workflow/SRS/schema changes; no `--force` push or history rewrite.
- **Approval basis:** Direct owner instruction explicitly directing resolution of the GitHub `4/5` CI failure.