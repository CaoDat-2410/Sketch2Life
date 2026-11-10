# FEAT-066 — Full FE review against canonical SRS Rev57

Owner: User-requested read-only review. Review date: 2026-11-10, Asia/Bangkok.

## Authority and baseline

- Current product authority: `docs/context/SRS_AUTHORITY.md` and `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev57 dated 2026-11-09, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`.
- Approval state: draft, awaiting formal owner sign-off. This is the current working baseline, not a signed final SRS.
- Source worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`, based at commit `95433b3a9bef893a671df6623476784dbd0fd83d` when the worktree was created.
- The FE worktree's local `docs/context/SRS_AUTHORITY.md` still says v2.5-draft. It is stale relative to the canonical root authority and must not determine current requirements.
- Existing 37-screen screenshot archive is historical synthetic-preview evidence captured on an earlier commit. It does not prove current route coverage or current tablet behavior.

## Review scope

The earlier revision 1 source review covered Parent Android and `apps/ui-mobile` as context/reference, Parent Web, Teacher UI, School Manager UI, Platform Admin UI, the additional Admin UI surface, and shared authentication/API integration. The current plan revision 3 narrows all new work to `apps/school-manager-ui`: local fixture-only preview and visual/UI/UX review of its School Manager routes. Do not inspect or run Parent mobile as part of this clarified task. Teacher, Platform Admin, and the additional Admin UI are outside the current scope.

## Existing findings and open questions

The source review in `evidence/notes/FE_UI_FULL_SRS_REVIEW_REV57_20261110.md` records confirmed gaps in Teacher run/Sketch Deck integration, School Manager organization/billing coverage, Platform Admin backend mode, manual Teacher child selection, consent-state presentation, upload recovery, and manager notification behavior. It also records Parent-specific source findings and implementation risks; those are retained as earlier evidence and are not newly runtime-verified by plan revision 2.

Open questions remain: Q-01 child eligibility/consent/exclusion/reselection/no-eligible behavior and selection evidence; §31.10 Parent no-preset activity-catalog behavior; and Parent Web scope/account-creation requirements. Do not resolve these from UI appearance alone.

## Current milestone

Plan revision 3 review is complete for School Manager source and local loopback Vite preview. The focused findings and route/screenshot coverage are recorded in `evidence/notes/SCHOOL_MANAGER_WEB_UX_REVIEW_REV57_20261110.md`; the earlier broad source note remains historical evidence and does not broaden this review. Parent mobile and every other portal remain out of scope. This was an audit only; no product code changed, and remediation is still a separate task.

## Revision 4 — School Manager web remediation (2026-11-10)

The user directly authorized implementation limited to `apps/school-manager-ui` and FEAT-066 governance/evidence in the designated `codex/fe-ui-web-remediation` worktree. Plan revision 4 is approved; see `plan/PLAN.md` and `approvals/TASK_APPROVAL.md` (plan SHA-256 `D9780223AB395C1B5A9942F4011B749A2A15E3D66283A178F768AF9E9AC0CCB6`). This supersedes the revision 3 audit-only implementation restriction. Canonical SRS remains FEAT-063 v2.7-draft Rev57, unsigned, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; §32 remains as-built evidence only.

Initial contract audit: Lesson Library supports School Manager public-grant review; BE1 supports class list/create, adult assignment create/revoke, and consent-filtered profile-list reads. The class-create contract has no capacity input/guard, and the checked contracts expose no class archive/suspend, teacher directory, School Manager billing/invoice/payment/subscription, organization quota summary/top-up, inbox, or school feedback-reply flow. A read-only roster view may use the existing profile-list API; do not expose media or use real child data. Unsupported end-to-end flows must be visibly unavailable and documented rather than simulated. Before implementation started, no product source had been changed.
## Revision 4 implementation and review results

- M01 local preview now tracks approval and change requests independently; after requesting changes the reviewed item is removed from the pending queue, `Đã duyệt` remains 0, and `Yêu cầu chỉnh sửa` becomes 1. Preview notices state that the decision is local and is not sent to the API.
- M01 tabs have linked tab/panel IDs, selected state, roving tab focus, and Left/Right/Home/End keyboard navigation. The content panel and diff panel expose `tabpanel` semantics.
- The notification bell/unread indicator is replaced by a static unavailable status because the checked contracts contain no inbox API. The organization label is static context with no dropdown arrow.
- M02 fixture actions that implied class creation, Teacher invitation, quota purchase, parent-group sync, or subscription changes are disabled and labelled unavailable. API-backed class listing remains; a read-only roster panel uses the existing profiles endpoint and displays names only. Child media/story are not requested or shown.
- Class capacity-safe creation, archive/suspend, Teacher selection, billing/invoice/payment, subscription, organization quota, inbox, and School Manager feedback reply remain blocked on APIs/contracts recorded in EV-003. Commercial values and policy remain open in the unsigned SRS.
- Manual local UI review was captured at 1440x900 and 390x844 for login, M01, and M02 dashboard/teachers/classes/quota/settings. See EV-004 and `evidence/screenshots/remediation-after/`. No backend, provider, production data, credentials, tests, or builds were used.
## Revision 5 follow-up — School Manager logout (2026-11-10)

During sequential School Manager flow review, the user identified that the authenticated dashboard has no visible logout action. The existing `TeacherContext.logout` callback already clears the web role/auth session keys, calls the configured Firebase sign-out bridge when present, and transitions authenticated routes back to login; the M01/M02 `ManagerLayout` did not expose it. The SRS mentions logout as a trigger in UC-15 for Parent/Teacher notification endpoint revocation, but does not list a School Manager logout control in §21.5. This follow-up is a direct user-reported UI defect within the previously approved FE-only scope, not a new SRS requirement. Plan revision 5 and its matching approval hash were recorded before implementation.
## Revision 5 logout implementation and verification

`ManagerLayout` now exposes the existing `TeacherContext.logout` action on authenticated School Manager routes. Local keyboard review from dashboard and settings at 1440x900 and 390x844 confirmed Enter activation, removal of `s2l-web-role` / `s2l-web-authenticated`, return to `/login`, and redirect to `/login` after attempting to revisit protected routes. At 390px the collapsed icon control is 44x44px with an accessible name. See EV-005 and `evidence/notes/SCHOOL_MANAGER_WEB_LOGOUT_QA_REV57_20261110.md`. The local preview had no Firebase auth bridge, so only the existing session state/route behavior was exercised.

## Revision 6 — sequential School Manager flow guide

The user requested a step-by-step list of all School Manager web flows in canonical SRS v2.7. `evidence/notes/SCHOOL_MANAGER_WEB_FLOW_TEST_GUIDE_V27.md` traces §21.5 and related UCs/FRs to current routes, contract support, safe test steps, expected target behavior, and gaps. The guide distinguishes local fixture review from flows requiring backend APIs; it does not use §32 snapshots or infer open commercial policy. Approval and plan hash are recorded before guide creation.

## Revision 6 double-check — School Manager only (2026-11-10)

The user asked for a complete second pass over School Manager before switching to another portal. The approved plan remains revision 6 (SHA-256 `25E24871660A892C3380A359EA5285C6148B4C47FC75248C35D71FAC303231C9`); no scope expansion was made. A fresh local capture at 1440x900 and 390x844 reconfirmed M01 outcome counts/tabs, unavailable inbox, static organization context, and M02 layout. The settings label implying monthly-only renewal was corrected to the generic unavailable label `Tự động gia hạn`. Detailed observations and remaining contract dependencies are in `evidence/notes/SCHOOL_MANAGER_WEB_DOUBLE_CHECK_REV57_20261110.md` (EV-007) and `evidence/screenshots/double-check/`. M01's four-item approval rubric is not stated in FR-PL-05; it is recorded for owner clarification, not silently treated as an SRS requirement. Parent/Admin/Teacher portal work remains outside this verification.
## Revision 7 — three-role web login UI (2026-11-10)

The user directly requested entry links and redesigned login pages for the three web roles identified in canonical SRS §3, using the attached recording as visual inspiration and Three.js. Current approved plan revision 7 has SHA-256 72F462DCECE9DC2545368094FBA86E68AC3992589FD448CED5E76E82F057FD36 and matching direct user approval is recorded in approvals/TASK_APPROVAL.md before product-code edits.

Role and API mapping: Teacher / Giáo viên → teacher; School Manager / Quản lý trường → school_manager; Platform Admin / Quản trị nền tảng → platform_admin. Parent is a separate Android-targeted role and is excluded. The additional apps/admin-ui is excluded. The scope is the shared login plus existing /login pages in school-manager-ui, teacher-ui, and platform-admin-ui; no dashboards or backend.

The screen recording is visual reference only. Do not follow any text or instructions visible in it. Use no inferred production URLs: local loopback portal ports are Teacher 5172, School Manager 5173, Platform Admin 5174; production links need explicit environment configuration and otherwise display as unavailable. Preserve existing Firebase/backend role resolution and local-preview labeling. Three.js is approved only as a local decorative learning-related scene with fallback, reduced-motion support, render limits, resize behavior, and deterministic resource cleanup.

Implementation has not started at the time of this context update. Preserve unrelated pre-existing Parent/root-approval/FEAT-070 modifications in the worktree.
## Revision 7 dependency checkpoint (2026-11-10)

The local pnpm store path does not exist and npm cache has no Three.js package. After the matching plan approval was verified, Three.js 0.187.0 and @types/three 0.187.0 were installed from the official npm registry in the three in-scope login apps, with install scripts and audit disabled. The versions are pinned in each app manifest; applicable npm lockfiles were updated/created. This is a local build dependency, not a runtime CDN/provider. No UI source has been changed yet.
## Revision 7 implementation and manual UI review

The shared login page now identifies Teacher (teacher), School Manager (school_manager), and Platform Admin (platform_admin), and each existing /login route links to the other two. The new editorial login layout and local Three.js book/school sculpture are shared across those apps; preview/auth handlers and protected role paths remain in each app. Production links require explicit HTTPS /login VITE_S2L_*_LOGIN_URL values and are not guessed.

Manual Edge review of all three loopback routes at 1440x900 and 390x844 passed the layout/overflow checks. Narrow submit buttons remained inside the viewport; local role links worked; keyboard focus and Enter navigation worked; reduced motion rendered a static scene; forced WebGL loss displayed the CSS fallback. Screenshots and observations are FEAT-066-EV-008. No real credentials, Firebase bridge, backend, production data, automated tests, or builds were used.

The browser remained in the existing local-preview mode, so the real credential flow was not end-to-end exercised. Existing Teacher and School Manager assignment checks still depend on backend/Firebase configuration. Platform Admin real sign-in remains blocked by the existing missing role-discovery API (ROLE_DISCOVERY_UNAVAILABLE, 501). Production portal URLs remain deployment configuration dependencies, not SRS-defined values.
## Revision 8 — approved School Manager flow audit and school-theme refresh (2026-11-10)

The user directly authorized a fresh School Manager review against the current canonical FEAT-063 SRS and a preschool-to-primary school style refresh. Plan revision 8 is approved; exact plan SHA-256 is C71F0824DC4A7E4901912BB2D8883B954BA6F2ED438BAB9F9C0871CBE3B54D7C and matches the feature-local approvals/TASK_APPROVAL.md entry before product edits. Canonical SRS v2.7-draft Rev57 SHA-256 remains BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5, unsigned. Use §§1–31 only; §32 is as-built evidence.

The pre-redesign flow audit is recorded in evidence/notes/SCHOOL_MANAGER_WEB_SRS_FLOW_AUDIT_REV57_20261110.md. Current UI coverage is incomplete against §21.5: M01 grant review and read-only class/roster have relevant API support; dashboard and quota are fixture-only; capacity-safe class lifecycle, Manager Teacher lifecycle/transfer, billing/invoice/payment/subscription, quota/top-up, inbox and school feedback reply lack compatible contracts. Preserve explicit unavailable states and the child-media privacy boundary.

The worktree root/branch/status were reverified. Pre-existing root task-approval, Parent UI and FEAT-070 modifications are out of scope and untouched. The root FEAT-066 inventory has no root-only path to bring into the active worktree; matching old files will not overwrite current records. At this checkpoint, UI code edits have not started; the approved scope is authenticated apps/school-manager-ui screens only plus FEAT-066 evidence/governance.


## Revision 8 implementation and manual review complete (2026-11-10)

- Applied the approved school-office palette and responsive styling to the authenticated School Manager shell, M01 and M02 only. Changed App stylesheet loading order and local Manager presentation classes; no shared styles, APIs, auth logic, business rules, packages or assets were added.
- Completed local browser review and saved EV-010. Across 16 route/viewport observations (1440x900, 768x1024, 390x844), horizontal overflow count is 0 and out-of-viewport disabled-action count is 0. M01 request-changes, arrow/Home/End tab movement, linked panel semantics and keyboard logout were manually checked in preview.
- SRS flow completeness remains partial. See EV-009/EV-010 for the supported reads/review flow and missing organization summary, capacity/lifecycle, Teacher lifecycle, billing, quota, inbox and school feedback contracts. These states remain explicitly unavailable; no price/policy or child-media access was inferred.
- No root-only FEAT-066 file was missing from the active worktree, so nothing was copied. Root checkout and pre-existing unrelated worktree changes remain untouched.
## Revision 9 — dashboard cobalt palette preview (2026-11-10)

The user directly asked to preview the design-taste-frontend Cool Grey + Cobalt palette on the current School Manager dashboard. The palette was generated for software/saas; cool-grey-cobalt was the first result and is compatible with the existing blue-led logo. SRS v2.7-draft Rev57 does not prescribe product colors and remains unsigned. Plan revision 9 SHA-256 03FF50D8330884BB815CCF8D8E68186F250DBE70279D6EC9FBD163423EFB24AC is approved and recorded before code changes.

This experiment is limited to the default M02 dashboard route. It must not alter other Manager routes, mobile, shared styling, actions, API behavior, fixture notices, logout, or privacy. Keep the change local/uncommitted for visual review unless the user later asks to adopt it.

## Revision 9 palette preview result (2026-11-10)

FEAT-066-EV-011 records the Cool Grey + Cobalt experiment on the default M02 dashboard only. The desktop 1440x900 and narrow 390x844 local captures show no horizontal overflow; M02 teachers and M01 retain the revision 8 warm/green tokens. The browser review used the isolated local fixture session and loopback Vite server. The dark inverse token rules were added but not visually captured. This remains a preview, not a permanent palette choice or SRS requirement. No tests/builds, backend/provider calls, commit, or push were made.

## Revision 10 — all browser web UIs use the supplied logo and bright cobalt palette (2026-11-10)

The user directly expanded revision 9 to replace the logo with their attached artwork and apply the bright Cool Grey + Cobalt theme across the existing browser apps. Canonical FEAT-063 SRS v2.7-draft Rev57 was reverified at SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; the draft remains unsigned and does not prescribe colors. Plan revision 10 must be approved by a matching feature-local hash before app code or asset copying. Included: parent-ui browser preview, school-manager-ui, teacher-ui, platform-admin-ui, admin-ui, and shared web brand/styles. Excluded: native/mobile apps, historical inactive parent-web, backend and auth/business behavior.


## Revision 10 implementation and manual review result (2026-11-10)

- Applied the attached user logo and bright Cool Grey + Cobalt tokens to parent-ui browser preview, School Manager, Teacher, Platform Admin, Admin UI and shared browser styling. Plan revision 10 SHA-256 `9EA74203319688B6E4D456E3CB278DB7BA314F423AC0BF7581D802807255269D` was approved before app/asset edits. Source image SHA-256 is `86010669F03972BC1273DC02BEB8F34B39BD5E47C00771B2632003C1D62F9042`.
- EV-012 contains 18 local browser captures for login/primary screens at 1440x900 and 390x844; document horizontal overflow was absent in all captures. The local School Manager, Teacher and Platform Admin servers were reused from this worktree; Parent ran at 127.0.0.1:5175.
- Admin UI code and logo references are updated, but manual preview is limited by offline cache miss `ENOTCACHED` for `@tailwindcss/vite`; no network install, credentials or manifest/lockfile changes. Parent preview auto-authenticates and redirects `/p11-authentication` to `/p01-lesson-library`; no unauthenticated Parent screenshot was available without changing auth behavior.
- No automated tests/builds, backend calls, production data, commit or push. FEAT-063 v2.7-draft Rev57 remains unsigned and contains no color requirement. Native/mobile, Parent UI mobile, backend and unrelated Parent-context/mobile-layout/FEAT-070/root-approval changes remain untouched.
## Revision 11 — three-role dashboard icon refresh (approval checkpoint)

The user directly requested a new icon set across the three web-role dashboards. Canonical FEAT-063 v2.7-draft Rev57 authority was verified at SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; it remains unsigned. SRS §3 maps the web portals to Teacher (`teacher`), School Manager (`school_manager`), and Platform Admin (`platform_admin`). Plan revision 11 is approved in the feature-local ledger with SHA-256 `0B2B90980B2D2CB491DCCC15BC1E22ED6FFCEBD3D8B21AEADE795670B9875BC1` before app code changes.

The approved work changes only the authenticated dashboard iconography (shell navigation, role/status indicators, and route content using existing icon components) in those three role apps and FEAT-066 records. Use a shared local rounded duotone SVG set aligned to the bright Cool Grey + Cobalt palette; preserve labels, routes, actions, role checks, and accessibility names. No new dependencies, login redesign, Parent/Admin UI, native/mobile, backend, or production data. At this checkpoint, icon source files are unchanged; implementation and desktop/narrow visual review are pending.

## Revision 11 implementation and visual review complete (2026-11-10)

- Implemented the approved shared rounded duotone SVG family in apps/shared/RoleDashboardIcon.tsx and connected it through the existing Icon and MgIcon exports in School Manager, Teacher and Platform Admin. Shared navigation styling uses the bright Cool Grey + Cobalt palette; Teacher navigation now has the same 32×32 icon tile treatment.
- Plan revision 11 SHA-256 0B2B90980B2D2CB491DCCC15BC1E22ED6FFCEBD3D8B21AEADE795670B9875BC1 matches the feature-local approval ledger.
- EV-013 records six local browser captures of School Manager /m02-organization-management, Teacher /t01-lesson-workspace, and Platform Admin /a02-platform-operations at 1440×900 and 390×844. All six have 0 horizontal overflow, no Vite error overlay, 0 observed runtime errors, and 32×32 active nav icon tiles. Teacher's desktop document width was 1430px within the 1440px viewport.
- Shared icon glyphs are reused on the three login pages; only those glyphs changed, not login layout or authentication flow. Labels, destinations, role checks, actions and accessible names remain unchanged.
- No new packages, manifests, lockfiles, backend/API, mobile/native, Parent, additional Admin UI, real data or credentials were used. No tests/builds, commit or push. Pre-existing unrelated root approval, Parent, Admin UI and FEAT-070 changes remain in the worktree.
- Evidence: evidence/notes/WEB_DASHBOARD_ICON_REFRESH_V11_20261110.md; evidence/screenshots/web-dashboard-icons-v11/.
## Revision 12 — shared login font correction (2026-11-10)

The user reported broken Vietnamese typography in the login headline. Plan revision 12, SHA-256 00D41575B3D5912DE9A2CB2D1080DC9D588C91E366D762B79092DC7F618FBCC7, and direct authorization were recorded in FEAT-066 before app code changes. The shared login title now uses the existing Vietnamese-capable sans-serif stack, upright accent styling, less-tight tracking and more line height. Teacher, School Manager and Platform Admin login pages were manually reviewed at 1440×900 and 390×844; the six captures show clean accents, no horizontal overflow, no Vite overlay and no runtime errors. Preview storage was restored after capture. No automated tests/builds, commit or push.
## Revision 13 — visible logout controls across all three SRS web roles (2026-11-10)

The user requested logout buttons in the Teacher, School Manager, and Platform Admin UIs. Plan revision 13 and its direct approval were recorded before app code changes; plan SHA-256 5DF172969F85296D5A1100BB288337CD0EEFF06373CC157DE719EA59B3C6029B. Teacher's existing top-bar action was moved to the account area at the bottom of its sidebar for narrow-screen visibility. School Manager's existing sidebar button was retained. The missing Platform Admin sidebar button was added and wired to the existing logout handler. EV-015 records all three roles at 1440×900 and 390×844; all controls are visible and in the viewport, with no horizontal overflow. Local activation in each app returned to /login and cleared the role/auth session keys. Preview storage was restored. No tests/builds, commit, or push.
## Revision 14 — three-role web flow audit only (2026-11-10)

The user requested a full SRS v2.7 review of the three SRS web roles and explicitly deferred UX fixes. This is read-only product-source/API-contract review of apps/teacher-ui, apps/school-manager-ui, apps/platform-admin-ui; Parent and the additional apps/admin-ui are excluded. The baseline is canonical FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5, still unsigned; use §§1–31 and not §32 as target requirements.

The complete finding list is FEAT-066-EV-016 in evidence/notes/THREE_ROLE_WEB_FLOW_AUDIT_V27_REV57_20261110.md. Confirmed blockers include Teacher occurrence/story/video/projection and extraction-confirmation flows; School Manager review without content for the exact grant version, class/Teacher lifecycle, billing/quota/inbox/feedback; and Platform Admin role discovery, moderation queue, catalog publish and operations data. P2 findings cover preview-only manual child selection, consent labeling, upload recovery, cursor pagination, and idempotency retry behavior. Four M01 approval criteria and Platform Admin/operator permission separation are recorded for owner clarification, not treated as signed policy.

Only source/contracts and previous FEAT-066 evidence were reviewed. No application source, API, UX, backend, mobile, credential, production data or provider was changed or exercised. No automated tests/builds, commit or push. The designated worktree/branch resolved correctly, but git status --short --branch returned fatal: this operation must be run in a work tree; no cleanup/checkout was attempted. Remediation requires a separately scoped plan after the user reviews this report.
