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

## Revision 15 — approved FE-only remediation checkpoint (2026-11-11)

The user asked to continue fixing issues after reviewing the complete three-role SRS v2.7 audit. Plan revision 15 and explicit approval are recorded before app source changes; plan SHA-256 is `86c6a13185797c8b5912ca3b6adb54b63f58d8ff87f1bebb16a6652434eb331e`. The baseline remains FEAT-063 v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`, unsigned; requirements are §§1–31, with §32 as implementation evidence only.

Scope is FE-only across Teacher, School Manager, and Platform Admin, their directly shared web modules, and FEAT-066 records. Existing authenticated API contracts are the limit: wire supported behavior; otherwise retain a truthful unavailable state and record the dependency. Do not change backend/contracts, Parent, additional Admin UI, mobile/native, packages, or open SRS policy. The School Manager Vite preview is running at `http://127.0.0.1:5173/`, bound to loopback. At this checkpoint no source code for revision 15 has changed.

## 2026-11-11 — Revision 15 FE remediation complete for review

Plan revision 15 (SHA-256 86c6a13185797c8b5912ca3b6adb54b63f58d8ff87f1bebb16a6652434eb331e) was authorized before source changes. The three-role remediation is complete within the FE-only scope and remains uncommitted/unpushed. School Manager exact-version review and paging, Teacher consent accuracy/paging/upload recovery, truthful API-unavailable states, and Platform Admin fixture-removal are implemented. EV-018 records the source changes, 34 local route captures, manual M01 count result, API/authentication limitations, and remaining backend/owner dependencies. No automated tests/builds or production/backend credentials were used.

## Revision 16 — shared auth and Teacher UI preview (2026-11-11)

The user directly requested an implementation preview of auth and Teacher UI using the researched/generated design direction. Plan revision 16 and its authorization were recorded before source edits; the final plan SHA-256 is 9C446770A6232A9A42B8677B345D25DECB5097D1AF4DD2FFD810A100CD3A4D5D. Canonical SRS authority and FEAT-063 v2.7-draft Rev57 SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5 were verified; the draft remains unsigned.

The shared login design now applies across Teacher, School Manager, and Platform Admin; only the Teacher authenticated app receives the new palette/shell/dashboard styles. The existing login role mapping and auth behavior remain. The Teacher Sketch Deck route continues to state that it is unavailable; there is no projection surface or supported runtime flow to present.

EV-019 records 14 desktop/narrow captures, role-link and local-preview interaction observations, and limitations. No horizontal overflow, Vite error overlay, or browser runtime exception was observed. The login submit control fits within the 390x844 first viewport. The Teacher preview uses labelled local fixture data. See evidence/notes/AUTH_TEACHER_UI_PREVIEW_V16_20261111.md and evidence/screenshots/auth-teacher-v16/.

The worktree remains uncommitted/unpushed for user review. No automated tests/builds, production/backend data, external providers, credentials, Parent UI/mobile, authenticated School Manager/Admin UI, or API/backend/contracts were used or changed.
## Revision 17 — child-friendly shared icons across the three web roles

The user's direct visual request authorizes a friendly icon refresh for Teacher, School Manager and Platform Admin. Plan Rev17 and its matching approval were recorded before source changes; plan SHA-256 49D2B35334A952201387661B50C57DA971453F6C3A8F7518E4E86D48A90AC0E4. The baseline remains canonical FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5, unsigned.

The shared apps/shared/RoleDashboardIcon.tsx renderer now applies rounded strokes and semantic crayon-color accents to the existing icons consumed by all three roles and their shared login pages. Glyph mappings, currentColor foreground contrast, labels, actions, routes, role behavior, and layout remain unchanged. No dependency or asset was added.

EV-020 contains 15 isolated loopback captures of each role's login and representative dashboard at 1440x900 and 390x844. No horizontal overflow, Vite error overlay, or observed runtime exception. The Platform Admin capture retains the existing truthful backend-unavailable view. No tests/builds, screen-reader audit, commit or push.

## Revision 18 — navbar and notification icon preview complete

The user requested a skill-guided redesign of the role navbar and notification icons, then asked to wait for the next task. Plan Rev18 and direct approval were recorded before source changes; plan SHA-256 AA075090DFD47E98B62B5287BDDABF9BD199395847CDAA9FB1275C34A789D9FA. The canonical working SRS remains FEAT-063 v2.7-draft Rev57, unsigned.

The three authenticated role shells now render full-color system emoji for navigation, adjacent role/account controls, quota/organization marks, and notification/inbox affordances. All roles use the same yellow bell for notification/inbox; unread count and unavailable status remain as before. The remaining page-content icons still use the Rev17 SVG treatment. No dependency or external asset was added.

EV-021 contains nine loopback screenshots: each role dashboard at 1440x900 and 390x844, plus dark desktop at 1440x900. No horizontal overflow, Vite overlay, or runtime exception was observed. Existing local storage/session values were restored after capture. No automated tests/builds, commit or push; changes are left for the user's review.

## Revision 19 — monochrome line icons for role navigation and notifications

The user corrected the Rev18 navbar preview and requested outline icons without multicolor emoji. Plan Rev19 and the matching direct approval were recorded before the shared source change; plan SHA-256 FABD3A9230620BE08F7E4B6D04FA178C3EAC372377F760F37C266182BB9F1141. The canonical working SRS remains FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5, unsigned.

The navigation and notification variants in apps/shared/RoleDashboardIcon.tsx now render local SVG outline glyphs in one currentColor per control; notification/inbox uses the same bell outline for all three roles. Role call sites, state, labels, accessibility attributes, routes, dimensions and non-shell page-content icon styling remain unchanged.

EV-022 records nine local captures across Teacher, School Manager and Platform Admin at desktop/narrow sizes plus dark desktop. No horizontal overflow, Vite error overlay or runtime exception was observed. Representative screenshots were visually inspected. No tests/builds or screen-reader device audit were run. The worktree remains uncommitted and unpushed for user review.

## Revision 20 — Teacher UI SRS layout diagnosis (implementation pending user review)

The user requested one diagnosis of current web UI against the latest SRS, a proposed UI demo set, and a Teacher-first trial only if the proposal is accepted. The authority-selected baseline was verified as FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; still unsigned. Plan Rev20 SHA-256 0BAAFA4133B6ABDF9C225985C93CE32AF07F62A6E3C83C69B6F251DABC337219 and its matching approval authorize audit only.

EV-023 records the Teacher route/API review and proposed seven-screen task model. Important findings: T05 preview exposes a School Manager handoff action to Teacher; local dashboard, quota and inbox metrics are fixtures; Teacher profile create and immutable extraction correction/confirmation lack product APIs; T04/T06/T07 and profile/settings routes are unavailable; current Teacher API supports class/roster reads and lesson list/detail/create/update/archive/public-review plus upload/status/revision reads. Run, occurrence, sample-selection, job, playback, projection, history, quota and inbox APIs were not found in the FE adapter. Q-01 eligibility/reselection policy remains open and was not inferred.

The proposal consolidates the sidebar to Bàn làm việc, Lớp & hồ sơ, Giáo án, Buổi dạy and Lịch sử; optional Sketch Deck and sample-video steps become contextual within an occurrence. It preserves API blockers, role/privacy boundaries, truthful preview labels, and the existing paper/graphite/school-blue design direction while reducing metric/card clutter. No application source was edited. Existing EV-018/EV-019 screenshots were visually reviewed; a fresh 127.0.0.1:5172 request was denied by sandbox socket permissions. No tests/builds, authenticated API/backend, production data or credentials were used. Wait for the user to accept the proposal before Teacher implementation.

## Rev21 — semantic monochrome navbar icon implementation

The user authorized replacing navbar symbols that did not match their functions across Teacher, School Manager, and Platform Admin, retaining a friendly rounded crayon outline style with no icon color fills. The shared navigation renderer and the three role-shell mappings now use semantic monochrome outline SVGs. Manual loopback review covered all three roles at 1440x900 and 390x844 plus dark desktop. The nine captures show no horizontal overflow, Vite overlay, or observed runtime exception. See EV-024. The independent Rev20 Teacher layout proposal remains pending user review. No tests/builds or commit/push were performed.

## Rev22 — clarify the settings glyph

User review identified that the former radial settings icon read as a sun. The navbar gear now uses a toothed cog outline; the manager settings item in the shared Teacher role shell also maps to gear. Legacy settings glyph use outside navigation was preserved. EV-025 records nine fresh local captures and visual inspection; no overflow or runtime/Vite issue was observed.

## Rev23 — full three-role web UI design preview

The direct user request authorizes a design-only preview, not application implementation. Scope is shared web Auth plus Teacher, School Manager and Platform Admin, based only on FEAT-063 v2.7-draft Rev57 (SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned). SRS §21.5 and §§5/19/20/21.6 are the screen and flow map. Content Admin is a permission, not another role; Parent/mobile is excluded. API gaps, privacy boundaries and owner-open decisions remain explicit. No fake data, success, billing, prices or policy. Generated boards stay in assets/generated until visual acceptance. Application implementation remains unapproved.
Rev23 design review is ready. EV-026 records visual inspection of the four generated boards and their limits; the complete route/flow/API atlas is in evidence/notes/WEB_UI_CRAYON_ATLAS_REV23.md, and image provenance/hashes are in assets/generated/rev23/PROVENANCE.md. The concepts represent shared Auth and all three SRS web roles at desktop/narrow widths. API-blocked flows remain visibly unavailable; no child data, fake success, billing values, prices or policies were added. No app source was changed for Rev23. Wait for user review; implementation remains unapproved.
## Revision 24 — implementation checkpoint

The user authorized a complete presentation-layer rebuild of Auth and the three SRS web roles using the Rev23 concept boards. Plan SHA-256 is 072778CC86CCF6C2CDE18CDD034276F75371A4930FF5C18924F58191187BC345 and the matching direct-user approval is recorded in approvals/TASK_APPROVAL.md. Implementation order is Auth, Teacher, School Manager, Platform Admin, with one manual SRS/UI check and evidence checkpoint after each. Preserve routes, authorization, API contracts and all pre-existing unrelated changes. No Parent/mobile/backend, automated tests/builds, commit or push.

### Rev24 Auth checkpoint — 2026-11-11

Shared Auth presentation is rebuilt against the Rev23 board. Manual local review at 1440×900 and 390×844 confirms all three role links, the login action within the first viewport, no horizontal overflow/Vite overlay/runtime exception, and isolated role-mismatch screens with a working logout affordance and no foreign role shell. Manager preview 5173 was verified as the correct worktree process but served stale transformed source; only that verified Vite process was restarted on 127.0.0.1. EV-027 records the captures and check. Next section: Teacher.

### Rev24 Teacher checkpoint — 2026-11-11

Teacher now uses a role-specific paper/crayon rail, responsive workbench, API-backed lesson/class pages, and explicit unavailable screens for unsupported SRS steps. Class lists are filtered to active Teacher assignments with a class scope, and class detail checks that exact assignment before requesting roster/consent. The local preview displays no names, classes, lessons, quota counts, unread counts or fabricated progress. Lesson/import actions remain bound to current FE contracts; extraction confirmation and the occurrence/story/video/projection lifecycle remain unavailable. EV-028 records all 12 current Teacher routes at desktop/narrow widths and keyboard menu behavior. Next section: School Manager.

### Rev24 School Manager checkpoint — 2026-11-11

School Manager has been rebuilt and manually reviewed across 11 routes at 1440×900 and 390×844. Class/roster reads require an active `school_admin` assignment; public review uses the current API grant/detail/decision methods and locks on a stale immutable version. Local preview has no fixture rows, amounts, quota values, or unread signals. Unsupported staff lifecycle, capacity transitions, billing, subscription, quota, inbox, feedback, and organization settings remain unavailable with dependencies shown. Drawer keyboard behavior, `aria-current`, logout, and local session clearing were reviewed. EV-029 records the images and observations.

### Rev24 Platform Admin checkpoint — 2026-11-11

Platform Admin has been rebuilt and manually reviewed across 12 routes at 1440×900 and 390×844. The overview distinguishes the real-but-unqueried `GET /health` contract from aggregate platform health; no call runs in preview. Moderation, catalog, org/permission, queue/job, billing reconciliation, quota policy, lifecycle, audit, inbox, and feedback dependencies are explicit. Role discovery remains unavailable, so a synthetic local session demonstrates layout only and never proves authorization. Drawer keyboard behavior, `aria-current`, logout, and local session clearing were reviewed. EV-030 records the images and observations. All four planned Rev24 sections are complete; the work remains uncommitted and unpushed pending the user's review.

## Revision 25 — dashboard alignment pass kickoff

The user asked for a second visual pass, said the base frame is acceptable, and requested closer alignment with the Rev23 demo with less clutter. Review found repeated preview notices, long copy and sidebar-duplicate quick links on the three overview dashboards. Rev25 narrows the work to those overview surfaces only; preserve the role shell, routes, supported API behavior and unavailable states. Plan SHA-256 `F3B2413CBBE5BA649BE9736BD24CB8873E43144D6CFB98B2771001DC53ABCC44`; matching direct-user approval is recorded in `approvals/TASK_APPROVAL.md` before code changes.


### Rev25 Teacher overview checkpoint — 2026-11-11

- Rechecked the current Teacher workbench against the Rev23 board at 1440×900 and 390×844 after the overview cleanup already present in the worktree. The dashboard now presents only the three work areas; the shell carries the local-preview signal and each card keeps its area-specific empty/API state.
- Both captures have no horizontal overflow, Vite overlay, runtime exception or console error. Mobile drawer keyboard check: Enter opens and focuses the first nav item; Escape closes and returns focus to the menu button. No data API was called.
- Screenshots and observations are in `evidence/screenshots/dashboard-alignment-rev25/` and were produced by `capture_dashboard_alignment_rev25.mjs`. Teacher is reviewed; proceed to School Manager.


### Rev25 School Manager overview checkpoint — 2026-11-11

- Replaced the three summary cards, repeated preview panel, four sidebar-duplicate shortcuts, and dashboard privacy strip with the two Rev23 blocks: `Tình trạng tổ chức` and `Dịch vụ`. Class count is shown only after the existing assignment-gated API read succeeds; preview shows an em dash and no sample data. Public review is marked as an existing API requiring an authenticated School Manager session. Invoice/payment, subscription/quota, inbox, and feedback remain explicitly unavailable.
- Desktop 1440×900 and narrow 390×844 captures show no horizontal overflow, Vite overlay, runtime exception or console error. Enter opens the drawer and moves focus into nav; Escape closes and returns focus. Requests were restricted to `127.0.0.1:5173`; no product API was called.
- Evidence: `evidence/screenshots/dashboard-alignment-rev25/manager-overview-1440.png`, `manager-overview-390.png`, and the refreshed `observations.json`. Manager is reviewed; proceed to Platform Admin.


### Rev25 Platform Admin checkpoint and completion — 2026-11-11

- Replaced the dashboard preview banner, duplicate role-discovery warning, nested health-state panel and six sidebar-duplicate shortcuts with four compact cards: health, queue/jobs, billing and lifecycle. Preview health remains uncalled; the card says `Chưa kiểm tra`. Queue/jobs, billing and lifecycle each state their missing API dependency. Role discovery remains on the permissions route.
- Captured and visually reviewed all three dashboards at 1440×900 and 390×844. Six observations record `documentWidth` equal to the viewport width, no Vite error overlay, no runtime exception or console error, and one visually active nav item. Enter opens each narrow drawer, focuses the first nav link, and makes logout visible; Escape closes the drawer and returns focus. Only per-app loopback requests were allowed; synthetic session flags were used and no product API was called.
- Evidence: FEAT-066-EV-031, six images and `observations.json` under `evidence/screenshots/dashboard-alignment-rev25/`.
- Known separate follow-up: React Router `NavLink` currently supplies `aria-current="page"` to all same-path School Manager (10) and Platform Admin (11) nav entries even though CSS marks only one item active. The Rev25 dashboard-only scope kept the shell unchanged; this accessibility issue is recorded for its own fix.
- Rev25 is complete pending user review. No tests/builds, Parent/mobile, backend, commit or push.


## Revision 26 kickoff — 2026-11-11

The user asked to make the background behind the web UI match the Rev23 demo. The worktree and branch were reverified as `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation` / `codex/fe-ui-web-remediation`; existing Rev24/Rev25 changes are present and will be preserved. Revision 26 is limited to a CSS paper/crayon backdrop behind authenticated content in Teacher, School Manager and Platform Admin; it leaves the accepted shell, page cards, routes, API and authorization unchanged. Plan SHA-256 is `247E06100BD2506B1872EBA47E71549ACE8DFDC200614320464933A428800B38` and the matching direct-user approval is recorded before source edits. No Parent/mobile, Auth, external asset, test/build, commit or push.

### Rev26 completion — 2026-11-11

- Added the requested demo-style paper grain and sparse crayon corner strokes behind the authenticated Teacher, School Manager and Platform Admin content canvases. The shell, cards, text, route structure and runtime states remain intact.
- Visually inspected overview and representative detail/unavailable routes for all three roles at 1440×900 and 390×844 (12 captures). All screenshots show the background behind the interface with no clipping or horizontal overflow. Capture observations report no Vite overlay, runtime exception or console error; all three mobile drawer keyboard checks pass Enter/Escape and focus return.
- Evidence is recorded in EV-032 and `evidence/notes/WEB_UI_PAPER_CRAYON_BACKGROUND_REV26_20261111.md`. Preview requests were restricted to the three local loopback apps; no product API was called.
- Rev26 is complete pending user review. No automated tests/builds, Parent/mobile, backend, commit or push.

## Revision 27 kickoff — 2026-11-11

The user directly authorized rebuilding the shared login UI. Authority was checked before planning: `docs/context/SRS_AUTHORITY.md` points to FEAT-063 SRS v2.7-draft Rev57; SHA-256 is `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; the draft is unsigned. The product roles for web are Teacher, School Manager and Platform Admin; Content Admin remains a permission, and Parent is mobile-only for this scope.

The current shared `/login` component has correct role-to-adapter mappings, three role URLs, preview labeling, form pending/error states and mismatch handling. Rev27 follows the recorded brainstorm recommendation: a Vietnamese-first crayon learning-studio layout with a clear login action and portal links, reusing the existing Three.js school model plus SVG fallback. No auth contract or route changes are authorized. Plan SHA-256 `C9EF609A920F3C53F0153ED109660B85003D4D03A8E1E76C2F46C3EB2EEF21C2` and matching direct-user approval are recorded before source edits.


### Rev27 completion — 2026-11-12

The three shared web login pages now use the approved Vietnamese-first crayon learning-studio direction. Existing auth mappings and semantics are preserved. The desktop Three.js illustration has an SVG fallback in the same scene host; a forced local shader-link failure leaves the SVG visible. Twelve screenshots and role/keyboard observations are recorded in EV-033. The full taste-skill gate reached OPEN 22 at round 3 before final manual review stabilized fallback opacity with the React scene state. After that small auth-specific fix, all 12 captures and the forced shader failure check were rerun; the stored open set is the three dependency shader-lint findings and 19 marketing-layout findings, and no fourth full round was run because the skill limit was reached. Details are in `evidence/notes/AUTH_UI_REDESIGN_REV27_20261112.md`. Rev27 is complete pending user review, uncommitted and unpushed.
## Revision 28 completion — consolidated web structure and SRS rebuild — 2026-11-16

The owner requested one clean web application, an SRS-aligned UI rebuild, one local commit, and a running local preview. FEAT-067's one-app structure and the related FEAT-066 web changes were reviewed together. The one active web entry is `apps/web`; role routes remain separate and use the existing auth/API contracts.

For this task, the owner explicitly selected the unsigned v2.7-draft Rev68 file at `F:/Downloads/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (SHA-256 `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944`). The repository authority record still points to unsigned FEAT-063 Rev60 (SHA-256 `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B`). This is recorded as an open source-register mismatch; neither SRS nor the authority record was changed.

The three role shells and shared login were rebuilt with route/API truth, keyboard and responsive states. Teacher class/lesson/import paths retain their available APIs; occurrence, slide/media, sample-run, playback, projection, quota/history and inbox dependencies remain unavailable where contracts are missing. School Manager BE1 auth/classes/review stays separate from local preview; unsupported capacity, lifecycle, billing/quota/inbox flows remain unavailable. Platform Admin remains metadata-only, with Content Admin treated as a capability and child story/media denied by default.

Nine loopback screenshots and the SRS/API route matrix are in `evidence/notes/WEB_UI_SRS_REBUILD_REV28_20261116.md` and `evidence/screenshots/web-rebuild-rev28/`. The final 390px Teacher dashboard image was recaptured after correcting an in-transition drawer capture. Build and repository validator results are recorded in the same evidence note/closeout record. No app tests, production API, child data, deployment or push were used.

### Final validation findings

Security and architecture validators pass; full `git diff --check` exits 0. Harness and skeleton remain invalid because their required `apps/mobile/package.json` was removed per the owner's prior cleanup request; harness also requires evidence directories in unrelated FEAT-070. These paths were not restored or generated for this web-only closeout. The results and first-scan provenance correction are in EV-034.

## Revision 29 — role login landing and remove local preview UX — 2026-11-16

The owner approved using the shared three-role entry as the login landing, removing the preview panel, and making the visible flows real-auth/API-backed. Plan revision 29 and its hash are recorded in the task and root approval registers before source edits. This follow-up supersedes the Rev28 local School Manager preview UX while preserving Rev28 history and the Rev68 task baseline.

/login now contains only Teacher, School Manager, and Platform Admin destinations. /teacher/login and retired /school/preview/* URLs redirect to it; Teacher sign-in is /teacher/sign-in, while School Manager keeps its BE1 login/assignment gate. The local sign-in bypass, preview app/navigation and preview login link were removed. Existing backend/API contracts stay unchanged, and Platform Admin role discovery still shows its missing-API warning.

EV-035 records eight desktop/mobile/browser captures, route destinations, no-overflow results, 3px keyboard focus, no runtime or console errors, no external requests, and the final build pass. No application tests, credential entry, authentication submission or product API calls were performed.

## Revision 30 — one shared sign-in screen — 2026-11-16

The owner corrected Rev29: the sign-in composition shown on the open Teacher route is the login entrypoint; remove the separate role-card chooser and make School Manager use this same layout instead of its second login page. Rev30 plan SHA-256 is 8D167E39A75B3A13E68FBBB1C4672C018E9282920CC4478D9DFA4B16B1DAD12F, with matching approval in the root and FEAT-066 task registers before source changes.

The /login route now opens the Teacher sign-in form by default. The Teacher, School Manager, and Platform Admin buttons update the selected role in the same layout. Compatibility sign-in URLs select their corresponding role there. Teacher continues using Firebase plus backend assignment resolution; School Manager continues using BE1/Firebase with the existing school_admin assignment gate; Platform Admin remains blocked on the missing role/capability discovery API. No provider, backend, authorization, session-bypass, or mobile behavior changed.

EV-036 records desktop/mobile captures, route aliases, focus retention, zero browser/runtime/external-request errors, and that no credential or product API request was made. Build/lint/browser results and pre-commit repository validator results are recorded in the evidence note and Rev30 status. The approved single local commit was amended after final validation; the branch remains one commit ahead and nothing was pushed.

## Revision 31 — Teacher API integration and UI rebuild plan — 2026-11-16

The owner requested a Teacher-first implementation plan mapped to the current canonical SRS and backend APIs, using the applicable frontend, UX, architecture, decomposition and repository-harness skills. New planning uses FEAT-063 v2.7-draft Rev60 (SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B) per docs/context/SRS_AUTHORITY.md. Older FEAT-066 Rev68 records remain historical and unchanged. Plan: plan/PLAN_REV31_TEACHER_API_UI_REBUILD_20261116.md (SHA-256 2EB6235B8F8DFB5EB6EC4098FA2892687102DD4D922360E16751F6D21DA0E5E7). Static API crosswalk: evidence/notes/EV-037_TEACHER_API_UI_CROSSWALK_REV31_20261116.md. The plan separates currently wired APIs, backend-present-but-unwired/version-gated routes, conditional Modal APIs and missing Teacher contracts. No implementation, approval-ledger change, runtime/API call, test, commit or push was made; implementation remains awaiting explicit approval.
## Revision 32 — Platform Admin available API wiring — 2026-11-16

The owner approved the existing safe Admin API scope. FEAT-063 v2.7-draft Rev60 remains the canonical unsigned SRS. Plan: plan/PLAN_REV32_PLATFORM_ADMIN_AVAILABLE_API_INTEGRATION_20261116.md, SHA-256 56A6985B7D486E79F1B8C9AB39B4C56275BC401C7ECF4730014D01BC167A1A92; approval is in the root task ledger. The Admin overview health panel now uses the configured API base instead of blocking non-loopback URLs, while labeling the result narrowly and retaining explicit async/error/retry states. Existing role resolution and account list/create/update integrations were retained. Moderation and other unsupported panels remain blocked. EV-038 records the change and its static-only validation limits; no live API call, test/build, commit or push was performed.
## Revision 33 — Docker API verification and FE handoff — 2026-11-17

The owner requested that BE run in Docker, its APIs be probed, and FE remain available for manual testing. Plan Rev33 (SHA-256 0AB2F79A26EDCBA27871C559016A8A6A56466DA82867519E2FB147995C8380F0) and approval are recorded before service startup. PostgreSQL and the API container are healthy; `GET /health` returns 200. Auth/account GETs return expected 401 without a credential. The generated OpenAPI document is FE-projected and omits these route families; source route registration and 401 behavior confirm their guard is reached.

Full Compose startup is partial: Quay denied the MinIO image with HTTP 401, the renderer's ignored dist-demo artifact was absent, and pnpm stopped on its offline supply-chain metadata check. A local API image omitting only the optional static renderer copy was used; MinIO, ClamAV and Redis are not running. Direct CORS is absent, so an ignored same-origin Vite proxy was started at 127.0.0.1:5174; the pre-existing 5173 server was preserved. EV-039 has exact statuses and limits. No account data, credentials, mutations, app tests, commit or push were used.

## Revision 33 rerun preflight - 2026-11-19

The owner asked to start the backend again for FE testing. The existing Rev33 approval covers the no-volume-reset Compose startup and read-only API checks. In this session, Docker Desktop's named pipes returned `permission denied`, `wsl --status` returned `Wsl/E_ACCESSDENIED`, and no PostgreSQL listener was available. The host Uvicorn fallback exited because the existing venv lacks the Dockerfile's pinned `av==18.1.0` image-admission dependency. No service was left running and no probes or data operations were performed. See EV-058; the 2026-11-17 Rev33 success above is historical and does not describe the current runtime.
## Revision 34 — Platform Admin test account — 2026-11-17

The owner requested a test account for the active Admin FE/API task. Plan Rev34 (SHA-256 3EBDE69AFFA105F09DFB04901DA5539EE555361EBCBC3F8D035831A5291A9EBE) and root approval cover one QA identity in the verified nonproduction `sketch2life-dev` project. The empty local Docker database received only the `be1_core` and `lesson_library` migration branches needed for identity/role persistence. The supported bootstrap created the Platform Admin identity; password sign-in succeeded, `/api/auth/v1/me` returned role `platform_admin`, and account-list GET returned HTTP 200 with total 1. FE port 5174 received the dev Firebase config and same-origin API base; original port 5173 remains available. Credentials and bearer token are excluded from repository records and are delivered privately in the owner-facing reply. No production project, email, Content Admin capability, child media, app suite, source edit, commit or push.
## Revision 35 — Active FE port API proxy — 2026-11-17

The owner observed a backend-data error in the in-app browser on 127.0.0.1:5173. That port was using the original Vite process without a proxy, while the same-origin workaround existed only on port 5174. Replaced only the verified worktree Vite process on 5173 with an ignored temporary `/health` and `/api` proxy, injected the already-configured `sketch2life-dev` Firebase web config in process memory, and set the FE API base to 5173. The screenshot's typed email was not the generated QA account; use the Platform Admin test account recorded in EV-040. Port 5174 remains available. EV-041 records HTTP statuses. No tracked source, account, backend, or credential was changed in this correction.

## Revision 36 — Platform Accounts crayon UX rebuild (2026-11-17)

The owner explicitly selected the attached unsigned v2.7-draft SRS dated 2026-11-13 with Rev69 amendments for this task; its hash and the repository Rev60 authority mismatch are recorded in Plan Rev36 and EV-042. The authority register remains unchanged.

The Platform Admin accounts page now uses responsive crayon styling and truthful loading/error/empty/results states. API/auth failure hides stale rows and never appears as a successful empty list. Filters submit by Enter, create is disabled until an authenticated list succeeds, and School Manager organization ID is inline. Existing GET/POST/PATCH APIs and authorization remain unchanged. Content Admin stays a permission rather than a role; child profile/media access stays denied by default.

EV-042 records visual captures at four sizes, build/lint results, no-session runtime limits, and remaining offset-vs-cursor, capability API, and audit-viewer gaps. No app test suite, account mutations, commit or push.


## Revision 37 — Platform Admin sidebar crayon redesign — 2026-11-17

The owner requested a redesign of the Platform Admin sidebar shown in EV-043. Plan Rev37 and direct-owner approval were recorded before source edits. A portal-scoped override in apps/web/src/modules/platform-admin/styles/admin-rebuild.css corrects link color hierarchy and oversized group headings, separates waiting API state, and groups the verified session with its account actions. Routes, labels, auth behavior, shared-shell JSX, and Teacher/School Manager styles remain unchanged.

EV-044 records desktop/tablet/mobile captures, successful drawer and scroll checks, no horizontal overflow or runtime exceptions, production build and diff-check passes, plus existing shared-shell lint warnings. The overview can perform its existing read-only GET /health probe; no credentials or protected mutations were submitted. No application test suite, commit, or push.

## Revision 38 — Platform Accounts zoom-width layout — 2026-11-17

The owner reported the Platform Accounts action column overlapping Revision and account email wrapping excessively when zoom narrows the effective viewport. The confirmed CSS gap was the shared shell drawer breakpoint at 820px versus the account table-to-card breakpoint at 700px; table auto layout also left the action column without a width guarantee.

Rev38 keeps a fixed 5-column table through 1120px with explicit column proportions, smaller status metadata and stacked action buttons; the action header is visible. The existing labelled account-card layout now activates through 900px to protect the reduced content width. User APIs, authorization, data, roles and mutations remain unchanged.

EV-046 records browser viewport measurements at eight sizes. The isolated browser had no Firebase credential, so it rendered the authentication recovery state without an account row; no fixture or token was injected. Build, UsersPage lint and diff check passed. The actual populated action row was not independently captured after the change. No app test suite, account mutation, commit or push.
## Revision 39 — School Manager API/UI crosswalk — 2026-11-17

The owner requested the remaining Platform Admin API check, followed by preparation for School Manager. Static inspection of `origin/dev` found no additional complete, SRS-ready Admin feature API: account GET/POST/PATCH are already wired; the lesson moderation PATCH lacks queue/exact-version reads and its backend guard does not enforce the SRS Content Admin permission. Manager planning starts from the existing public lesson review and class list/create flows. Assignment, roster/consent and Parent-group contracts are available in backend routes but not wired in the reviewed Manager UI; quota/billing and organization feedback-thread APIs were not found. Plan Rev39 and EV-047 record the crosswalk. This is planning only; no code or approval register was changed.

## Revision 40 — School Manager API integration plan — 2026-11-17

The owner requested a concrete Manager API integration plan including login and route count. Rev40 records 17 Manager business routes (six already wired, ten proposed for integration and one class-assignment command blocked by missing scoped Teacher discovery), plus shared backend `GET /api/auth/v1/me`, for 18 relevant BE routes. Firebase sign-in is performed by the FE SDK, not a BE login route. The plan sequences organization/roster/consent and Parent-group flows, preserves existing review revision gates, and defers missing quota/billing/feedback contracts. Rev40 is planning-only and awaits implementation approval.

## Revision 41 — Manager login/auth API verification — 2026-11-17

The owner approved Plan Rev41 to verify the Manager login chain, test it, and record results. Source tracing confirmed the existing FE uses Firebase SDK sign-in, shared `GET /api/auth/v1/me` role resolution, and BE1 organization assignment validation before setting the Manager portal session. A test reproduced a runtime config mismatch: the app did not read the `VITE_BE1_*` names documented by `.env.example`; the shared resolver now falls back to those names after injected and generic config. Added focused auth-flow coverage and corrected a stale Manager gate test that used a standalone route causing a redirect loop. Two focused files passed 8 tests; production build passed; full Oxlint exited 0 with warnings and no errors. Local health returned 200; unauthenticated auth and assignment routes returned 401. No FE dev server was active at 5173, and a real authenticated login was not exercised because no Manager test credentials were available; no account or role was mutated. EV-049 records exact evidence and limits.

## Revision 42 — Manager QA account and live login — 2026-11-17

The owner explicitly requested a test Manager account, live login verification, and then continuation with business APIs. Rev42 account provisioning and Rev43 conditional business API integration plans/hashes are recorded in `approvals/TASK_APPROVAL.md` before any new mutation. Read-only preflight found the dev API and PostgreSQL healthy, Firebase Admin configured for `sketch2life-dev`, one existing Platform Admin, and zero Manager identities, organizations, or assignments. The worktree currently has no Firebase Web config and port 5173 is not active. No account or organization was created; Rev42 waits for the matching local Web config so no orphan identity is left behind. Rev43 is approved only after live Manager login and both auth/scope reads pass. EV-050 records the sanitized preflight.

## Revision 44 — Manager QA bootstrap ordering repair — 2026-11-17

The owner provided the ignored Firebase Web config and requested a QA Manager account, live login check, then business API integration. Firebase password sign-in worked, but the supported BE1 first-school-admin bootstrap failed with an organization-assignment foreign-key IntegrityError. Each temporary Firebase identity was deleted; read-only database counts were one existing identity, zero organizations, and zero assignments. Plan Rev44 approves only an explicit parent flush before assignment insertion, a focused ordering test, and retry of the same local QA login flow. No QA account has been retained yet.

## Revision 45 — Manager QA login and business API integration — 2026-11-17

The owner supplied ignored Firebase Web config for sketch2life-dev. A PostgreSQL foreign-key error exposed that the supported first-school-admin bootstrap added an assignment before its parent organization row was flushed. Plan Rev44 records the focused fix and owner authorization. The first two temporary Firebase identities were deleted after rollback; the final reserved-domain QA account was retained only after password sign-in, authenticated school_manager role resolution, and the organization-wide school_admin assignment read passed.

Rev43’s conditional login gate is satisfied. The Manager UI now reads organization details, minimal class roster and consent status, and lists/creates Parent groups through the five approved operations. Roster and consent are independently loaded; opaque child IDs and child media/story are not rendered. Parent-group creation uses an explicit submit and Idempotency-Key. Class creation stays disabled because the BE route does not enforce SRS FR-T-03 capacity. Teacher assignment, Parent invitations/membership revoke, consent writes, class assignment, capacity, billing, quota and feedback remain unavailable under current source contracts.

Live authenticated organization, classes and Parent-group GETs returned 200; the QA organization has no classes or groups. No class, child, consent, group, membership, or class-create mutation was sent. The local FE at 127.0.0.1:5173 serves the Manager login route and proxies API/health successfully. No browser automation was available, so interactive Firebase SDK login is left for the owner to exercise with the delivered QA credential. EV-051 records test/build/lint evidence and limits. No commit or push.

## Revision 46 — School Manager navigation and theme restoration — 2026-11-17

The owner requested a complete School Manager navigation cleanup aligned to the latest supplied SRS. Repository authority remains FEAT-063 v2.7-draft Rev60, unsigned, per SRS_AUTHORITY.md; the supplied Rev69 copy was checked for applicable Manager scope and no SRS edit was made.

Source inspection found that PortalRoutes uses school-be1 while the four imported Manager stylesheets only matched school-preview. The Manager CSS now supports both identifiers. Navigation now covers the SRS Manager areas and distinguishes contract-backed routes from missing APIs. Unsupported Teacher assignment/groups, school feedback, capacity, quota, billing and inbox pages remain explanatory and disabled at the workflow level. Roster/consent remains minimal and read-only. The topbar Manager identity is static because there is no profile route.

Production build and focused lint passed; no app test suite was run. The FE server on 127.0.0.1:5173 remains available. No authenticated browser capture could be made because the local CDP endpoint was not running; EV-052 records this limitation. No credentials or child data were stored. No commit or push.

## Revision 47 — shared folder cleanup proposal (2026-11-17)

A proposed organization for apps/web/src/shared is recorded in plan/PLAN_REV47_SHARED_FOLDER_CLEANUP_20261117.md. The current inventory is 17 root files plus the existing assets directory, with 50 direct source references across 27 consumers. The proposed grouping is api, auth, components, navigation and styles; assets stay in place. No source file has been moved. Implementation awaits explicit owner approval of the path map.


## Revision 47 — shared folder organization implemented (2026-11-17)

Implemented the approved shared-folder path map: 17 files moved into api/auth/components/navigation/styles; assets preserved. Updated 50 import references across 27 source files, with no runtime logic change. Static scan found no old shared-root paths; 14 clean tracked moved files match HEAD aside from approved import changes, and the existing Manager navigation remains intact. Production build passed; app tests were not run. Evidence is EV-053. No commit or push.

## Revision 48 — Manager API test baseline — 2026-11-17

The 17-route Manager inventory is recorded in plan/PLAN_REV48_MANAGER_17_API_INTEGRATION_AND_TEST_20261117.md; results are in evidence/notes/EV-054_MANAGER_17_API_INTEGRATION_TEST_RECORD_REV48_20261117.md. Current FE status is 11 wired/adapter-backed and six blocked by missing policy/support contracts. Backend full route composition confirms all 17 methods are mounted; the public OpenAPI projection shows only 11. FE focused suite passed 18/18, isolated BE suite passed 90/90, build and required validators passed. No live business write or PostgreSQL acceptance test was run.

## Revision 49 — QA Admin and Manager accounts — 2026-11-17

Plan Rev49 and owner approval cover resetting the two existing dedicated QA accounts in sketch2life-dev. Both Firebase logins and role checks passed; Manager organization assignment and Admin accounts read passed. Credentials are available only in the ignored local tmp/qa-test-accounts.local.md. EV-055 contains sanitized results; no account/role/scope rows or application source were changed.

## Revision 50 — Manager Classes review — 2026-11-17

Authenticated QA GET returned HTTP 200 with zero classes, confirming the screenshot is a valid empty organization state. FR-T-03 still prevents safely enabling creation. Review also found the API-error state renders alongside the empty message. See EV-056; no source changed.

## Revision 51 — consolidated web handoff — 2026-11-17

Owner approved consolidating all current non-ignored web-remediation worktree changes into one new commit for another machine. The scope includes role portals, Admin/Manager/Teacher frontend work, shared folder reorganization, bootstrap fix/test and FEAT-066 records through Rev51. .env and QA credentials in ignored tmp remain local. Validation and file inventory are recorded in EV-057.

## School Manager API gap-closure checkpoint — MGR-1 complete (2026-11-17)

The read-only MGR-0 inventory covers 17 Manager routes and distinguishes source declaration/composition from historical runtime evidence. Owner dispositions for MGR-1 are recorded in D-066-62 and `evidence/notes/MGR_1_OWNER_DISPOSITION_20261117.md`: Manager-to-Parent discovery/invitation stays unavailable pending a separately approved scoped contract; staff cannot create or revoke effective Parent consent; assignment candidates must be verified Teachers in the same organization. The MGR plan remains DRAFT / NOT APPROVED / NOT LAUNCHED. MGR-2 contract design for Billing-owned class capacity is next; implementation remains gated by MGR-7 approval. The owner-selected external Rev69 SRS input and the unchanged repository Rev60 authority pointer are both recorded; neither SRS has been signed or replaced.

## MGR-2 independent review and disposition — 2026-11-17

MGR-2 contract Draft 1 and its source evidence received an independent planning review: ACCEPT WITH NOTES, zero actionable findings. D-066-63 records the planning direction: Billing owns effective capacity; BE1 must obtain a versioned, concurrency-safe admission result before writing; fail closed if capacity cannot be verified; preserve SRS idempotency, GRACE/RESTRICTED, effective-time suspension, and scope behavior. Billing-unavailable public mapping, exact idempotency wire details, reservation/receipt protocol, and route-prefix mapping remain OPEN. The review did not verify runtime, generated OpenAPI, or Billing integration. MGR-2 remains DRAFT / NOT APPROVED / NOT LAUNCHED; no source or official Task Approval changed. Next roadmap work is MGR-3 contract planning, subject to its listed parallel dependencies and owner availability. See `evidence/notes/MGR_2_COLD_REVIEW_OWNER_DISPOSITION_20261117.md`.

## MGR-2 Rev60 citation correction and cold review R3 — 2026-11-17

The R2 traceability finding was corrected in the MGR-2 plan and source evidence. They now state that Rev60 §9.6 line 791 contains the general idempotency-key requirement; §§21.1/21.4 provide the key scope and replay/mismatch semantics; and §9.8 line 835 provides the HTTP 400 `INVALID_IDEMPOTENCY_KEY` mapping. The proposed route-group listing at §9.6 lines 766–775 is kept distinct from those requirements. An independent cold review of the exact updated pins returned **ACCEPT, zero P0/P1/P2/P3 findings**. The review was read-only and did not inspect the external SRS or verify runtime/generated OpenAPI/Billing integration. Current plan/evidence pins and the review are recorded in `evidence/notes/MGR_2_COLD_REVIEW_DRAFT1_R3_20261117.md`.

MGR-2 remains **DRAFT / NOT APPROVED / NOT LAUNCHED**. Billing-owned protocol details, exact idempotency wire/receipt details, public outcomes for unavailable or stale Billing decisions, and route-prefix mapping remain open. No source, official approval, SRS, or decision record changed; no tests, validators, runtime, database, Docker, network/provider, or Modal commands were run.

## MGR-7 bounded BE approval checkpoint — 2026-11-18

The owner conditionally approved the exact MGR-7 package after coordinator review and its R2 cold review returned ACCEPT with no findings. The feature-local `approvals/TASK_APPROVAL.md` records the exact plan pin, six-file BE allowlist, behavior, exclusions, and verification boundary. Approval covers implementation edits only; tests/build/typecheck/lint/validators/diff-check/OpenAPI/runtime and external service commands still require a separate owner launch instruction. MGR-7 implementation has not started. MGR-2 through MGR-6 remain separate open contract gaps; MGR-9 FE integration is not approved and must follow BE implementation evidence and its own approval.

### 2026-11-18 — MGR-8 verification attempt

P1 preflight passed, but the first authorized pytest command remained pending without captured output and was interrupted. No exit code or test summary is available; the second command was not run. MGR-8 remains NOT VERIFIED. See the implementation verification evidence note.

### 2026-11-18 — MGR-8 diagnostic

D1 passed 8 tests. D2 was interrupted after about 12 minutes with no log growth for 10 minutes; faulthandler located the wait in the OpenAPI Swagger/TestClient test during AnyIO and Windows asyncio portal setup. D3 was not run. The diagnostic does not decide the MGR-8 verification gate; owner disposition remains required. See the diagnostic evidence note.

### 2026-11-18 — MGR-8 owner-run results and fixture amendment

The owner ran D2 and D3 in their own terminal, outside the Codex sandbox, which hangs on loopback sockets. D2 (OpenAPI catalog): 2 passed, 1 failed with `KeyError: 'description'` at test line 332. The cause is a pre-existing `dev` `app.py` description gate that the M2 branch already removed; the MGR-7 catalog assertions from line 460 were never reached. D3 (Lesson Library integration): 6 of 7 failed with 403 `ACCOUNT_SCOPE_UNAVAILABLE`, because the fixture created adults without `account_role`. The owner approved a scoped amendment ("Approve the fix"), recorded in Task Approval, which sets `account_role` on the four synthetic adults; no other line changed. The owner-run D3-R2 gave 6 passed and 1 failed. The passes include the MGR-7 default-25 list test and the 400 `INVALID_IDEMPOTENCY_KEY` retry assertion. The failure is the teacher PDF upload test: 503 `DEPENDENCY_UNAVAILABLE` because no ClamAV answered at 127.0.0.1:3310, and MGR-7 did not change that test. MGR-8 stays NOT VERIFIED pending owner disposition; the D2 path (wait for M2, port `app.py`, or accept the limitation) is undecided. See `evidence/notes/MGR_8_OWNER_RUN_RESULTS_20261118.md`.

### 2026-11-18 — MGR-8 owner disposition: PARTIAL

The owner's instruction was relayed by the coordinating BE session ("Theo SRS và đề xuất cho tôi sau đó đưa câu trả lời cho phiên đó đi"). MGR-8 is recorded as **PARTIAL — runtime behaviour verified, catalog pending**.

- **Runtime behaviour: verified.** D1 passed 8 tests, and D3-R2 passed 6 of 7, covering the default-25 lists (SRS §21.1) and `INVALID_IDEMPOTENCY_KEY` (SRS §21.4).
- **Environment limit, accepted:** the teacher PDF upload test failed with 503 because ClamAV was not running.
- **Catalog: not verified.** The `openapi_contract.py` change has no passing test, and SRS §9.6 requires OpenAPI reconciliation, so it must not be committed unverified.
- **D2 direction: (a), wait for M2 on `dev`.** No `app.py` port.

Next steps, each only on the owner's word: M2 reaches `dev`; S-LL is rebased onto it; the owner re-runs D2 and D3; an independent review runs (Sonnet 5.5 high); then one S-LL commit. No commit until then. See the "Owner disposition" section of `evidence/notes/MGR_8_OWNER_RUN_RESULTS_20261118.md`.

## 2026-11-18 — MGR-8 VERIFIED on the consolidated M2 branch

The S-LL work (MGR-7 change and MGR-8 verification) moved from `.worktrees/manager-api` to the root checkout's M2 branch under the owner-approved consolidation plan. The steps were:
- commit `b95fed64` (Bruno and FEAT-081 records);
- merge `b93d7334` (`dev` plus the Phase A commit `9ceaf6cf`);
- the S-LL patch applied cleanly.

The owner then ran the tests in their own terminal:

| Test | Result |
|---|---|
| D1 unit | 8 passed |
| D2 catalog | 5 passed, including the MGR-7 assertions |
| D3 integration | 6 of 7 passed: both MGR-7 behaviours pass; the PDF upload test needs ClamAV |
| `test_app_composition` | 7 passed |

The owner decision was "R ok verified làm bước 5 đi": MGR-8 is **VERIFIED**, with the ClamAV PDF test recorded as an environment limit outside MGR-7. ClamAV becomes a prerequisite for the Teacher C-T upload slice, the L5 upload runs and Phase D.

Evidence: `evidence/notes/MGR_8_ROOT_RUN_RESULTS_20261118.md` (6,785 bytes, `19A6E63C106EFF951A162CF4B48475FBF442EF3656A30D29F910FFC2CECE1601`). Next: an independent evidence review, then one S-LL commit on the owner's word.

## 2026-11-18 — CONV-1 done (BE queue slot 1)

CONV-1 applied the D-066-68 conventions to the BE1, Lesson Library, Platform Admin, auth and Teacher AI families:
- one §9.8 envelope with Vietnamese messages;
- `X-Request-ID` on every response;
- validation errors as 400 `INVALID_REQUEST`, with non-echoing field errors;
- uniform 404 for out-of-scope access, with 403 only for in-scope role refusals;
- generic code mapping;
- `If-Match` errors as 400;
- OpenAPI 400 for the catalogued BE1 and Lesson Library operations.

`/api/parent/v1/ai` and the M2 Parent families are unchanged. It was implemented and verified in `.worktrees/conv1` on the local branch `feature/feat066-conv1` (D-066-71, CV-B: never pushed). The fixture scope amendment is recorded in `approvals/TASK_APPROVAL.md`.

**Next in the BE queue:** FR-C-08 (FEAT-063), then SEED-1. Billing is frozen by the owner.

## Goal v4 Phase A web wiring - Teacher (2026-11-23)

- Current task: implement the approved Goal v4 Phase A Teacher wiring in `apps/web`, using the final Teacher route list and launch-prompt contract. This task is separate from the historical FEAT-066 School Manager and MGR work.
- Canonical requirements remain the unsigned FEAT-063 SRS v2.7-draft at the path in `docs/context/SRS_AUTHORITY.md`; the final Phase A contract controls route behavior for this integration.
- Approved plan: `plan/PLAN_V4A_FE_WEB_WIRING_20261123.md` revision 52; approval and SHA-256 are in `approvals/TASK_APPROVAL.md`.
- Worktree/branch: `D:\GitHub\Sketch2Life\.worktrees\ui`, `codex/fe-ui-web-remediation`.
- Scope includes Teacher API, services, components, pages, copy, named tests, and FEAT-066 records/evidence. Parent/mobile and backend are excluded.
- Selected behavior: if visible gates are met but the run remains in `PREPARATION_REVIEW`, show a waiting hint; do not resend context confirmation.
- No commit, push, stage, stash, branch switch, `.env`, `debug.keystore`, credentials, or model weights. Run logs stay in `E:\AI_LOG\CODEX\fe-v4a-web\`.
- Preflight found the BE worktree at `db7e3920` with final Phase A commit `930da61e` as an ancestor and additional committed/dirty BE work. This job will not edit that worktree and will report the tip difference.

## 2026-11-23 — Goal v4 Phase A Teacher implementation review

- Implementation is complete for owner review. API, UI, tests, plan, approval, decision, status, and feature evidence are recorded under FEAT-066.
- `npm --prefix apps/web run check`: exit 0; build passed; lint exited 0 with unrelated warnings; 67 test files and 684 tests passed.
- Security and architecture validators passed. `git diff --check` exited 0. Harness validation is blocked by pre-existing missing `apps/mobile/package.json` and FEAT-072 harness paths; see `evidence/notes/EV-066-059_V4A_WEB_WIRING_20261123.md`.
- The BE checkout tip is `db7e3920`; supplied final `930da61e` is an ancestor. No Teacher contract contradiction was found in the reviewed code.
- No commit, push, stage, stash, or branch switch occurred.
## Goal v4 Phase A Parent Android wiring - 2026-11-23

The owner launched the task in the prompt and the task-specific plan and approval were recorded before implementation. Scope stayed in `apps/ui-mobile`; this worktree remains uncommitted and unstaged. The adopted Phase A route list and prompt set the Parent integration contract. FEAT-063 SRS v2.7-draft remains unsigned.

Implementation covers activity list and selection, implicit first-story start from the last successful activity/context gate, run confirmation fields, safe re-confirmation and safety-block recovery, completed playback from history, and nullable post-video activities. First story creation does not call the legacy `story-revisions` route. Resuming `PREPARATION_REVIEW` reloads the activity list as needed; `SCRIPT_GENERATING` uses the first-story wait reader.

The task text has one sequencing conflict: work item 3 says load activities after both subject and context confirmation, while the final R3 text says activity selection is expected first and context confirmation last. The implementation follows the explicit final order and still handles either gate as the last successful gate. No other conflict with the supplied final route list was found during this task.

Verification: all six requested gates passed. Vitest: 18 files, 228 tests, and `UI_COPY_AND_RECOVERY_VALID`. `evidence/notes/PHASE_A_PARENT_ANDROID_WIRING_EVIDENCE_20261123.md` records the gate outputs. No lint script or native Android test suite is present in `apps/ui-mobile`; optional Gradle assembly was not run.

## Goal v4 Phase B T-7e Teacher roster paging — 2026-11-24

- Current task: update only the Teacher roster API and T05 class detail UI in apps/web for the final Phase B contract. The route list is tmp/phase-v4/PHASE_B_FINAL_ROUTE_LIST_20261124.md §1; decision D-066-100 controls eligibility, count, paging, and removed-409 behavior. FEAT-063 SRS v2.7-draft remains unsigned.
- Plan: revision 53, plan/PLAN_V4B_FE_WEB_T-7E_20261124.md; owner launch recorded in approvals/TASK_APPROVAL.md before app edits.
- The worktree decision file lacked D-066-100 even though the repository-root copy and final route list contained it. The D-066-100 record was synchronized into this worktree's FEAT-066 decision file for traceability.
- teacherRosterApi.profiles follows pages at limit 100, passes cursors through, deduplicates child IDs, returns the first page's active_profile_count, and preserves rows loaded before a later-page error. T05 renders this server-filtered list and uses the aggregate count for the safe empty state.
- teacherRosterApi.consents remains for consent purpose/status details. Its failure now shows a consent-detail warning only when that call fails; it does not suppress the roster because the roster endpoint already applies the synthetic/effective-consent filter. No per-child exclusion reason is shown. The roster-specific CONSENT_NOT_EFFECTIVE branch and rosterError carve-out are removed.
- Synthetic create success copy now allows the synthetic profile to appear in the roster. School Manager modules, backend, and mobile remain out of scope.
- Implementation and checks are recorded in evidence/notes/EV-066-060_V4B_WEB_T7E_20261124.md. The harness validator reports the repository's missing apps/mobile/package.json; no unrelated repair is included.
- No stage, commit, push, stash, or branch switch occurred. Changes remain in the named worktree for owner review.

## Goal v4 Phase B T-12b/T-12c Teacher profile wiring - 2026-11-24

- Current task: implement the Teacher profile revisions/edit and support-needs client in apps/web only, using the final Phase B route list sections 3 and 4 and D-066-101.
- Plan: revision 54 in plan/PLAN_V4B_FE_WEB_T-12BC_20261124.md; task-specific approval and plan hash are in approvals/TASK_APPROVAL.md.
- T-7e completed its implementation and left uncommitted Teacher roster changes; this task preserved and built on them.
- The worktree copy lacked D-066-101. The root decision record was synchronized before app edits. D-066-102 records the UI paging/safe-state choices; D-066-103 clarifies support-needs same-key retry behavior.
- Implemented revision history on demand at limit 100, changed-fields-only editing, safe error handling, and a support-needs panel with no-store requests and close-time state clearing.
- The BE1 support-needs routes remain outside the published SRS operation set. The final route contract controls this integration; the SRS route addition remains an owner open item.
- Evidence: evidence/notes/EV-066-061_V4B_WEB_T12BC_20261124.md. Final repository gate results are recorded there.
- No backend, mobile, or School Manager code changed. No stage, stash, branch switch, commit, or push.
