# FEAT-066 EV-026 — Full web UI crayon concept and SRS flow atlas (Rev23)

- Date: 2026-11-11 (Asia/Bangkok).
- Plan: Rev23, SHA-256 E4E6D438FE4058694EE20EA25F01F670F2AB6F33E0BD05F9C3AA8101E9552774. Approval is design-preview-only; application implementation is not approved.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Authority: docs/context/SRS_AUTHORITY.md points to FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5. It remains unsigned. Product mapping uses §§1–31; §32 is as-built evidence only.
- Scope interpretation: “toàn bộ UI” means shared web Auth plus the three web product roles Teacher, School Manager and Platform Admin. Parent Android/mobile is excluded by the established task boundary. Content Admin remains a permission in Platform Admin.

## Design approach

Recommended: one shared authentication system with three role-specific portal entry links, then server-resolved identity/permission and role-pure workspaces. Choosing a portal is navigation only and never grants the role. Show role mismatch/role discovery unavailable as an explicit state.

Use one warm paper-and-crayon system across all roles: paper #FFF9F0, board #F2EBDD, graphite #25241F/#57574F, school blue #245B9B; use restrained yellow, coral, green and teal for semantic status. No violet. Keep navbar glyphs monochrome outline-only. These colors are a user-approved design direction, not SRS requirements.

Desktop concept: stable role rail, clear page title and contextual organization/class scope, one primary next action, work list first, secondary tools grouped by task. Narrow concept: compact labeled navigation and a “Khác” menu for secondary destinations; keep task context visible, wrap controls, and preserve 44px practical targets. Avoid repeated KPI walls and nested-card stacks.

## Complete screen and flow map

| Portal / flow | Screen families represented in the design set | Canonical trace |
|---|---|---|
| Shared Auth | Choose Teacher / School Manager / Platform Admin portal; Firebase sign-in; loading; token expiry; role mismatch; role discovery unavailable; logout | §§3, 20, 21.5–21.6; separate Teacher account and server authorization |
| Teacher — preparation | Workbench; assigned organization/class; class list and roster; structured profile form; lesson library/editor/version; public-review request; document upload/extraction/revision review; occurrence setup; plan/objective/story direction/activity checklist | §5.2 steps 1–5; UC-03/04; §21.5 |
| Teacher — in-class | Optional AI Sketch Deck toggle; white 16:9 deck preview; Back/Next/skip/regenerate; no shared child canvas; one occurrence context | §5.2 steps 6–7; UC-17; NFR-33 |
| Teacher — one-child sample | Server-selected eligible child and context review; explicit teacher confirmation; exactly one chosen artwork; camera/upload; text/audio idea; transcript correction/confirmation; subject and context review | §5.2 steps 8–10; UC-05; Q-01/open decision |
| Teacher — story/video | Script/storyboard review by exact revision; bounded rewrite; truthful job and reconciliation; safety-ready playback; explicit class projection confirmation; complete/cancel/delete; error/recovery | §5.2 steps 11–15; UC-05/07/11/16; §21.6 |
| Teacher — account/records | School quota summary (no Teacher pool/purchase); occurrence/run history; feedback handling; inbox; profile/settings; sign-out | §3, §20, §21.5, UC-10/15/16 |
| School Manager — organization | Organization workbench; effective capacity; create/archive/suspend class; assign/provision Teacher; reassign/offboard with pending/read-only state; org roster; capacity restriction and recovery | §5.3; UC-06/12/13; §21.5–21.6 |
| School Manager — review | M01 pending review queue; exact lesson version detail; approve or request changes; separate decision counters; stale revision/denied state | §3; UC-04; §20; §21.6 |
| School Manager — commercial | Billing period; invoice/payment status; renewal/downgrade; select classes before downgrade; school quota/top-up; no assumed price or fabricated payment state | §2.1; §5.3; UC-08/10/16; §21.5–21.6 |
| School Manager — communication | Canonical inbox; school-scoped feedback thread and reply; unavailable/empty/error; account/settings/logout | §3; §21.5; UC-15/16; NFR-26 |
| Platform Admin — content | Permission-aware lesson library/review; Activity Catalog draft/revision/review/publish/hide; immutable published versions; stale/conflict/review state | §§3, 20; UC-14; §21.5–21.6; §31.3 |
| Platform Admin — platform operations | Aggregate health; queue/job summaries; billing reconciliation; lifecycle backlog; organization/permission context; audit; metadata-only errors | §§3, 20; §21.5–21.6; §31.3 |
| Cross-role safety and recovery | Auth re-entry; inaccessible-resource message that does not disclose existence; stale revision re-review; quota/capacity restrictions; provider unavailable; awaiting reconciliation; delete pending; throttling | §21.6 |

No Parent web/mobile screen is included. The proposed screen set covers every web surface in SRS §21.5 and the applicable web-role use cases; web endpoints not named as a screen in §21.5 are represented only where §§3/19/20 require them.
## Current FE API boundary (implementation evidence, not product requirements)

Reviewed the current worktree backendApi.tsx plus the role routes and the existing FEAT-066 EV-018/EV-023 findings. This is source inspection only; no authenticated API was called for this concept.

| Flow | Current FE contract evidence | Concept status |
|---|---|---|
| Auth | Firebase bridge is required. Teacher and School Manager role checks read organization assignments when organization_id is configured. Platform Admin login explicitly returns ROLE_DISCOVERY_UNAVAILABLE. | Server-resolved role. Show setup/loading/mismatch/denied. Platform Admin sign-in cannot imply access while role discovery is absent. |
| Teacher roster | Assignment, classes, roster profile and consent reads exist; a consent record method exists. No product profile create/update method is exposed. | Reads are contract-backed at the adapter boundary; profile create/update is visibly unavailable. Do not show fake saved roster rows. |
| Teacher lessons | Lesson list/detail/create/update/archive and public-review request methods exist. | Use real loading/empty/error state. Any preview records must be labeled as non-persistent, or omitted from generated boards. |
| Teacher document import | Upload session, parts, status/resume, completion, source-document and extracted-revision reads exist. No write method for a corrected immutable extraction revision/confirmation was found. | Upload/parse status may be designed. Stop before showing “confirmed/ready to use”; mark correction-confirmation unavailable. |
| Teacher occurrence/run | No compatible occurrence/plan/checklist, Sketch Deck, server child selection, StoryRun, job progress, playback token, projection, lifecycle, quota, history, feedback, inbox or profile/settings API methods were found. | Keep these as target-flow screens with a clear “Chưa có API sản phẩm” boundary; no fake job/progress/video/counter or selection list. |
| School Manager public review | Access-grant list, decision command and current lesson detail methods exist. There is no get-by-immutable-version method. | Review only when the exact granted version can be verified. Otherwise show stale/unavailable state; do not substitute current version. |
| School Manager organization | Assignment/class/profile reads exist. createClass and createAssignment primitives exist, but no verified integrated contract for effective capacity admission, archive/suspend, exactly-one-active-Teacher workflow, reassignment saga, Teacher provisioning or roster lifecycle was evidenced. | Mark these transitions contract-pending/unverified; don't show success. Keep current roster reads tenant-scoped. |
| School Manager billing/communication | No invoice, payment, subscription, capacity period, quota/top-up, inbox or feedback reply APIs are exposed. | Present unavailable/dependency states. No prices, payment form success, fake invoice, unread count or reply toast. |
| Platform Admin | Health endpoint and a lesson moderation method exist. The current portal lacks Admin role discovery and authenticated moderation queue/list/exact-version flow. No catalog versioning, organization, queue/job summary, billing reconciliation, quota policy or audit feed methods were found. | Health can be represented as a real service state when connected. Other operational/content flows are explicitly API-blocked until full scoped contracts exist. Never show child media/story. |

No runtime/authenticated API validation was performed, and a method name alone does not prove server-side contract correctness or production availability.

## Decisions and open boundaries

- Shared login portals route to the right workspace; they do not self-assign role. Content Admin is presented as a permission gate inside Platform Admin.
- Teacher captures only one artwork and one server-selected child per occurrence. The UI waits for explicit confirmation; no roster batch action or Teacher-picked fallback is shown.
- Exact lesson/extraction revision and context must be reviewed before any downstream command; stale revisions return to review.
- Manager review, billing pricing/payment terms where still OPEN, selection eligibility/reselection policy Q-01, accessibility/wireframe OI-17 and other owner-open policies remain unresolved.
- School Manager and Platform Admin surfaces show school/class and operational metadata only; no child image, transcript, story, video or support attachment.
- Concept boards are review artifacts, not SRS sign-off or implemented routes. Image generation may imperfectly render small Vietnamese text; the written atlas is authoritative for labels/flow coverage.