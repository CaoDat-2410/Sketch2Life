# Task approval — FEAT-066 School Manager web remediation and flow guide

- Status: `APPROVED_FOR_IMPLEMENTATION`
- Approver: User, direct School Manager web authorization plus follow-up logout issue report and request for a sequential SRS v2.7 School Manager flow guide in chat on 2026-11-10 (Asia/Bangkok).
- Approved scope: FEAT-066 plan revision 6; modify only `apps/school-manager-ui` and FEAT-066 governance/evidence in worktree `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`.
- Plan revision: 6
- Plan SHA-256: `25E24871660A892C3380A359EA5285C6148B4C47FC75248C35D71FAC303231C9`
- Product requirements: canonical FEAT-063 SRS v2.7-draft Rev57, verified SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; still a draft awaiting formal owner sign-off. This task approval does not sign off the SRS.

## Approved work

- Complete revision 4 remediation and add a visible, keyboard-accessible logout action on authenticated School Manager pages by reusing the existing `logout` handler. Verify it clears current session state and returns to `/login`; do not add auth policy, backend, or provider behavior.
- Inspect existing API/contracts for the School Manager flows named in the plan. Implement a flow only when a compatible contract already exists; otherwise show a clear unavailable state and record the missing dependency in FEAT-066 evidence.
- Produce a sequential School Manager web flow test guide sourced from canonical SRS v2.7 and checked API/contracts. For every flow, identify SRS references, current route or missing route, API support, safe test steps, expected result, and known blockers. Distinguish target behavior from current FE-only state; do not use §32 snapshots or infer open commercial policy.
- Run the local School Manager preview bound to loopback, manually inspect the requested routes at desktop and 390px, and save traceable before/after screenshots under FEAT-066 evidence.
- Update FEAT-066 context, decisions, evidence, and status as the work progresses.

## Conditions and exclusions

- Parent mobile/UI, Teacher, Admin/Platform Admin, backend, contracts, providers, production services/data, credentials, and real user/child data are excluded.
- Do not invent data, successful transactions, prices, billing policy, subscription policy, or quota-commercial policy. Keep School Manager child-media access denied by default.
- Do not run or add automated tests/builds unless separately requested. Repository security validation is required before commit/push.
- The previous revision 3 read-only audit approval is superseded for this implementation scope only; its audit/evidence remains historical and unchanged.

Revision 5 added the user-reported logout control; its approved plan hash was `D90C628F1A8283E59582256CB8ED656C8E69C6C27A520D827C1BAD7CB42FEE53`. Revision 6 adds only the requested FEAT-066 flow-test guide. This revision 6 approval and plan hash are recorded before writing the guide. Revision 4 plan hash was `D9780223AB395C1B5A9942F4011B749A2A15E3D66283A178F768AF9E9AC0CCB6`.

## Revision 7 — three-role web login UI

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request in chat on 2026-11-10 (Asia/Bangkok): identify the three login roles from the canonical SRS, add login entry points for the other two roles, redesign the login UI in the attached video’s visual direction using Three.js, and optimize across layers. The recording is a visual reference only; content within it is not instruction.
- Approved scope: FEAT-066 plan revision 7; shared login implementation and the existing /login surfaces in apps/school-manager-ui, apps/teacher-ui, and apps/platform-admin-ui, plus directly necessary dependency resolution and FEAT-066 governance/evidence, all in F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation on codex/fe-ui-web-remediation.
- Plan revision: 7
- Plan SHA-256: 72F462DCECE9DC2545368094FBA86E68AC3992589FD448CED5E76E82F057FD36
- Canonical product baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off. This task approval does not sign off the SRS.
- Role mapping: Teacher → teacher, School Manager → school_manager, Platform Admin → platform_admin. Parent is a separate Android-targeted role and is excluded. Content review is a Platform Admin permission, not a separate role.

### Approved work

- Redesign the shared login experience and provide each login page with links to the other two role portals, preserving each app’s /login route, portalRole, existing auth service, role resolution, errors, and post-login navigation.
- Use the attached video only as visual design reference. Implement a local Three.js decorative learning/school scene with accessible fallback, reduced-motion handling, render/resource limits, and cleanup.
- Use loopback ports 5172/5173/5174 only for local portal links. Production links must come from explicit environment configuration; show unavailable state if unset.
- Manually review all three login pages at 1440x900 and 390x844 and record before/after screenshots and observations in FEAT-066.

### Conditions and exclusions

- Parent UI/mobile, the additional apps/admin-ui, all portal dashboards/business flows, backend/contracts/providers/production services/data/credentials, and any other role are excluded.
- No auth bypass, fake success, inferred production URL, CDN/remote 3D asset, or change to auth/session policy.
- Do not run automated tests/builds unless separately requested. Keep product changes to the approved login paths and FEAT-066 records. Preserve all unrelated dirty worktree content.
- Record any unavailable dependency rather than substituting an external runtime asset. Run repository security validation before commit/push; never force-push.

This revision 7 approval supersedes prior restrictions only for the bounded login UI scope above. The completed School Manager remediation and its evidence remain historical and unchanged.

## Revision 8 — School Manager SRS flow audit and school-theme UI

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-10 (Asia/Bangkok) to re-audit the running School Manager UI against the latest canonical SRS, assess flow completeness, and restyle it for a preschool-to-primary school setting. This approval is limited to School Manager authenticated web UI and FEAT-066 governance/evidence.
- Plan revision: 8
- Plan SHA-256: C71F0824DC4A7E4901912BB2D8883B954BA6F2ED438BAB9F9C0871CBE3B54D7C
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation
- Canonical baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off. This approval does not sign off the SRS.

### Approved work

- Read-only SRS-to-route/API/contract review for all School Manager flows, with a current-vs-target matrix and dependency evidence.
- School Manager authenticated shell and M01/M02 visual refresh only, including presentation-only adjustments in ManagerLayout.tsx/ManagerScreens.tsx if needed. Preserve business/API/auth/privacy behavior and clearly unavailable flows.
- Manual local UI review and screenshots for login regression, M01, and M02 sections at desktop/narrow widths, plus representative tablet checks.
- Update FEAT-066 context, decisions, evidence, and status after meaningful steps.

### Conditions and exclusions

- Only apps/school-manager-ui and FEAT-066 records in the named worktree may change. No edits in the main checkout or other worktrees; do not touch existing Parent/mobile/Teacher/Admin/backend/shared-login changes.
- Do not add APIs, mock success, real data, guessed price/policy, provider calls, or child-media access. API-blocked flows remain explicitly unavailable.
- No new dependencies/assets, tests, or builds. Manual local preview is loopback-only; security validation is mandatory before commit/push. Preserve unrelated working-tree changes and never force-push.

This revision authorizes implementation directly; no further approval is required before the scoped School Manager UI work.

## Revision 9 — School Manager dashboard cobalt palette preview

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-10 (Asia/Bangkok) to try the generated Cool Grey + Cobalt palette on the current School Manager dashboard for visual review.
- Plan revision: 9
- Plan SHA-256: 03FF50D8330884BB815CCF8D8E68186F250DBE70279D6EC9FBD163423EFB24AC
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation
- Scope: local visual preview on the default /m02-organization-management dashboard route only; FEAT-066 evidence/governance. Other routes and all mobile apps remain unchanged.
- Palette source: design-taste-frontend v2.5.1 palette-deal for software/saas; first result cool-grey-cobalt. The palette is a design experiment, not a product requirement from the unsigned SRS.
- Conditions: preserve all behavior/data/privacy; no tests/builds, no commit/push, no backend/provider/credential use; keep unrelated dirty changes untouched.


## Revision 10 — user-supplied logo and bright palette across web UIs

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-10 (Asia/Bangkok).
- Plan revision: 10
- Plan SHA-256: 9EA74203319688B6E4D456E3CB278DB7BA314F423AC0BF7581D802807255269D
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation
- Scope: five existing browser app packages: parent-ui browser preview, school-manager-ui, teacher-ui, platform-admin-ui and admin-ui, plus apps/shared web branding/styles and FEAT-066 evidence.
- Asset: user-supplied F:/Downloads/244247a40d95f81c31620a78d34d04d8.jpg, SHA-256 86010669F03972BC1273DC02BEB8F34B39BD5E47C00771B2632003C1D62F9042; copy unchanged into apps/shared/assets.
- Exclusions: apps/mobile, apps/ui-mobile, apps/child-ui, historical apps/parent-web, backend/APIs, auth/business behavior, packages/manifests, tests/builds, commit/push.
- This is a visual direction authorized by the user, not a new SRS requirement or role. The FEAT-063 v2.7-draft Rev57 baseline remains unsigned.

## Revision 11 — three-role dashboard icon refresh

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct instruction on 2026-11-10 (Asia/Bangkok).
- Plan revision: 11
- Plan SHA-256: 0B2B90980B2D2CB491DCCC15BC1E22ED6FFCEBD3D8B21AEADE795670B9875BC1
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Scope: authenticated dashboard iconography (shell, status/role indicators, and route content using existing icon components) in the SRS §3 web-role apps school-manager-ui, teacher-ui, and platform-admin-ui, plus FEAT-066 governance/evidence.
- Direction: consistent local rounded duotone SVG family across dashboard icon usages, aligned with the existing bright Cool Grey + Cobalt palette; no dependency, font, external provider, mobile, backend, or login layout redesign.
- Preserve routes, labels, actions, role checks, keyboard behavior, and accessible names. Manually review desktop 1440x900 and narrow 390x844. No automated tests/builds, commit, or push.

## Revision 12 — Vietnamese-safe typography on shared web login pages

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-10 (Asia/Bangkok), reporting the displayed Vietnamese login headline font as broken and asking to replace it.
- Plan revision: 12
- Plan SHA-256: 00D41575B3D5912DE9A2CB2D1080DC9D588C91E366D762B79092DC7F618FBCC7
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Scope: shared headline typography in apps/shared/portal-login.css for Teacher, School Manager and Platform Admin /login routes, plus FEAT-066 context/decision/evidence/status records.
- Change: use the existing login sans-serif stack with Vietnamese glyph coverage; remove the serif/italic treatment producing poorly rendered diacritics. No new font, external import, dependency, or layout change.
- Acceptance: clean Vietnamese glyphs; responsive headline at 1440x900 and 390x844; manually inspect all three login routes and save screenshots. Preserve all login behavior and role destinations.
- Exclusions: no mobile/native, backend/API, production data, credentials, packages/manifests, automated tests/builds, commit or push. Preserve unrelated dirty files.
- Authorization is direct from the user's latest request; no additional approval is required for this scope.

## Revision 13 — visible logout controls for the three SRS web roles

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-10 (Asia/Bangkok), asking for a logout button on the three role UIs.
- Plan revision: 13
- Plan SHA-256: 5DF172969F85296D5A1100BB288337CD0EEFF06373CC157DE719EA59B3C6029B
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Scope: authenticated shell logout controls for Teacher, School Manager and Platform Admin in their three web-role apps, directly necessary responsive styles and Admin shell prop wiring, plus FEAT-066 evidence/governance.
- Placement: one visible logout button beside the account identity at the bottom of each role sidebar. Keep Manager's current button, move Teacher's current top-bar button to the sidebar, and add the missing Admin button.
- Behavior: reuse each app's existing logout handler and route guard. Preserve current session clearing/auth-bridge behavior; do not add auth policy, backend/API, or other product flow.
- Acceptance: visible labeled button at desktop and narrow widths, accessible name/focus, narrow sidebar icon state; manually activate all three and verify cleared role/auth session plus return to /login. Capture 1440x900 and 390x844 screenshots.
- Exclusions: no Parent/Admin UI, mobile/native, backend/API, package/manifest, automated test/build, commit or push. Preserve unrelated dirty files.
- Authorization is direct from the user's latest request; no additional approval is required.

## Revision 15 — FE-only remediation from the three-role v2.7 flow audit

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct follow-up in chat on 2026-11-11 (Asia/Bangkok): “Bật lên sửa tiếp nè”, after review of the three-role audit EV-016.
- Approved plan: FEAT-066 Plan revision 15.
- Plan SHA-256: 86c6a13185797c8b5912ca3b6adb54b63f58d8ff87f1bebb16a6652434eb331e.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- SRS: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; still awaiting formal owner sign-off.
- Scope: FE-only remediation of EV-016 findings in apps/teacher-ui, apps/school-manager-ui and apps/platform-admin-ui; directly shared web modules; FEAT-066 records/evidence. Implement behavior only when existing APIs/contracts support the required auth, tenant, version and state semantics. Otherwise keep the flow explicitly unavailable and document dependencies.
- Acceptance: AC1–AC9 in Plan revision 15, including consent accuracy, Teacher pagination/upload/selection semantics, exact-version Manager review, truthful Admin unavailable states, supported idempotent retries, privacy boundaries, and local desktop/narrow review.
- Exclusions: backend/contracts, Parent, additional apps/admin-ui, mobile/native, packages/lockfiles, production data, credentials/providers, inferred OPEN policy, automated tests/builds, commit and push.
- This approval authorizes only the FE remediation scope above; it does not change the SRS or close any owner decision.

## Revision 16 — shared authentication and Teacher web visual preview

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-11 (Asia/Bangkok): “Sửa vào giao diện auth và của teacher trước cho tôi xem đi dùng skill mà làm ko đc làm chay”.
- Plan revision: 16
- Plan SHA-256: 9C446770A6232A9A42B8677B345D25DECB5097D1AF4DD2FFD810A100CD3A4D5D
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Product baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned and awaiting owner sign-off.

### Approved scope

- Redesign the shared web login presentation for Teacher, School Manager, and Platform Admin in apps/shared/WebPortalLoginPage.tsx and apps/shared/portal-login.css. Preserve portal role mapping and links, auth calls, errors, destinations, and preview behavior.
- Apply the paper-and-crayons visual direction to the Teacher web app only: its semantic tokens/styles, authenticated shell/navigation, and workspace dashboard. Preserve routes, existing feature/API behavior and unavailable states; keep the Sketch Deck projection white and 16:9.
- Palette is a visual decision, not a product/SRS requirement: #FFF9F0, #FFFFFF, #F2EBDD, #25241F, #57574F, #245B9B, #B93832, #B9561E, #E0B12D, #2F7048, #287887, #765035.
- Manually preview the three shared login pages and representative Teacher screens at 1440×900 and 390×844, with screenshots recorded under FEAT-066 evidence.
- Update FEAT-066 context, decisions, evidence, and status.

### Acceptance and restrictions

- Meet plan Rev16 AC1–AC6, including responsive behavior, accessible names/focus, accurate preview labeling, no false API success, and SRS Teacher/privacy boundaries (§§2.3, 3, 5.2, 7.3; NFR-20/29/33).
- Only shared web auth, apps/teacher-ui, and FEAT-066 governance/evidence may change. No authenticated Manager/Admin UI, Parent UI/mobile, backend/contracts, packages/lockfiles, external assets/services, production data, credentials, automated tests/builds, commit, or push.
- This direct-user authorization is sufficient; implementation may begin after this record.
### Rev16 scope clarification

A source review found later important login-only rules in apps/shared/web-brand-theme.css. The approved auth presentation scope includes only its .s2l-auth-shell and .s2l-auth-* rules, to keep all three shared login routes visually consistent. Global tokens and authenticated Manager/Admin selectors remain excluded. The plan SHA-256 below has been refreshed after this clarification.
## Revision 17 — child-friendly icon family across all three web roles

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-11 (Asia/Bangkok).
- Direct instruction: “Đổi hết bộ icon của 3 role thành bộ icon thân thiện với trẻ cho tôi đi”.
- Plan revision: 17
- Plan SHA-256: 49D2B35334A952201387661B50C57DA971453F6C3A8F7518E4E86D48A90AC0E4
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Product baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned and awaiting owner sign-off. Icon style is a visual choice only.

### Approved scope

- Update the shared local SVG icon renderer at apps/shared/RoleDashboardIcon.tsx used by Teacher, School Manager and Platform Admin, covering their authenticated web UI and shared login pages.
- Use friendly rounded strokes and restrained semantic crayon accents while preserving the existing icon meanings, currentColor contrast, size, layout and role behavior.
- Record the implementation and manual desktop/narrow preview evidence in FEAT-066.

### Acceptance and restrictions

- Meet Plan Rev17 AC1–AC6: consistent child-friendly treatment across shared icon usages; meanings, accessibility and layout preserved; manual screenshots at 1440x900 and 390x844 for all three roles; FEAT-066 updated.
- No packages/lockfiles, backend/API, Parent/mobile, separate apps/admin-ui surface, external assets/providers, production data/credentials, automated tests/builds, commit or push.
- This direct request authorizes implementation; no additional approval is required.

## Revision 18 — friendly full-color role navbar and notification icons

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-11 (Asia/Bangkok), explicitly asking to use the design skill and pause after preview.
- Plan revision: 18
- Plan SHA-256: AA075090DFD47E98B62B5287BDDABF9BD199395847CDAA9FB1275C34A789D9FA
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- SRS baseline: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned. This request changes visual presentation only.

### Approved scope

- Use the design-taste-frontend and frontend-design skills for the authenticated navbar and notification/inbox icons in Teacher, School Manager and Platform Admin.
- Apply the shared full-color system emoji variant only to those three role shells, using the platform emoji font stack and no new asset, network source, package, or backend behavior.
- Preserve icon meanings, names, existing aria/keyboard behavior, role routes, current notification/unavailable states, sizes and hit areas. Keep directional chevrons in the current style.
- Record desktop/narrow/dark-mode screenshots and review results in FEAT-066.

### Acceptance and restrictions

- Meet Plan Rev18 AC1–AC6, including recognizable role-correct icons, unchanged navigation and notification semantics, all three role previews at 1440x900 and 390x844 plus dark desktop, no overflow, and FEAT-066 updates.
- No packages/lockfiles, backend/API, Parent/mobile, separate apps/admin-ui, external assets/providers, real user/child data, automated tests/builds, commit, or push.
- This direct user instruction authorizes the implementation preview. Stop after presenting it for the user's next request.

## Revision 19 — monochrome line navbar and notification icons

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct correction on 2026-11-11 (Asia/Bangkok): “navbar icon kiểu nét ko màu á”.
- Plan revision: 19
- Plan SHA-256: FABD3A9230620BE08F7E4B6D04FA178C3EAC372377F760F37C266182BB9F1141
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- SRS baseline: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned.

### Approved scope

- Replace the Rev18 emoji presentation with monochrome outline SVG icons for Teacher, School Manager and Platform Admin navbar and notification/inbox affordances.
- Use the existing local paths with currentColor, rounded ends/joins and no semantic color fills. Use a bell outline consistently for the three notification/inbox controls.
- Preserve role behavior, notification states, accessible names, sizes and layout. Do not change other icon presentation.

### Acceptance and restrictions

- Meet Plan Rev19 AC1–AC6, including nine desktop/narrow/dark previews, legible monochrome active/inactive states, unchanged notification semantics, and FEAT-066 records.
- No packages/assets, backend/API, Parent/mobile, external provider/data, automated tests/builds, commit or push.
- The user's direct correction authorizes implementation and preview; no further approval is required.

## Revision 20 — Teacher SRS layout diagnosis and demo proposal (audit only)

- Status: APPROVED_FOR_AUDIT_ONLY; IMPLEMENTATION_NOT_APPROVED.
- Approver: User, direct request on 2026-11-11 (Asia/Bangkok): diagnose the current web UI against the newest SRS, list a proposed UI demo set, and try Teacher first only if the proposal is acceptable.
- Plan revision: 20
- Plan SHA-256: 0BAAFA4133B6ABDF9C225985C93CE32AF07F62A6E3C83C69B6F251DABC337219
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical baseline: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned.

### Approved for this turn

- One read-only Teacher UI/SRS/API-boundary diagnosis, a proposed Teacher-first information architecture and demo-screen inventory, and FEAT-066 records/evidence.
- No application source edits are approved by this revision. Implementation waits for the user's review and explicit confirmation of the proposed direction.

## Revision 21 — semantic crayon outline navbar icons

- Status: APPROVED_FOR_IMPLEMENTATION.
- Approver: User, direct request on 2026-11-11 (Asia/Bangkok): “Đổi 1 bộ icon mới bộ icon này bi sai so với chức năng của navbar vẫn theo phong cách crayon và icon ko màu chỉ viền”.
- Plan revision: 21
- Plan SHA-256: D97702B032B44573A9733F3978A175EF0C9EF45A50AF5D5A88A673192104FFE2
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical baseline: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned.

### Approved scope

- Replace misleading navigation glyph mappings in Teacher, School Manager and Platform Admin shells with symbols that match each visible destination/action.
- Use the shared local SVG navigation variant, rounded crayon-friendly geometry and one currentColor outline with no colored fills or emoji.
- Preserve all labels, routes, roles, actions, accessibility behavior, hit areas, layout and page-content icon styling.
- Capture desktop, narrow and dark previews and update FEAT-066 evidence.

### Conditions

- No backend/API, Parent/mobile, apps/admin-ui, external assets, dependencies, automated tests/builds, commit or push. Preserve all pre-existing worktree changes.

## Revision 23 — full web UI crayon design preview only

- Status: APPROVED_FOR_DESIGN_PREVIEW_ONLY; APPLICATION_IMPLEMENTATION_NOT_APPROVED.
- Approver: User direct instruction on 2026-11-11 (Asia/Bangkok), requesting a complete SRS-aligned crayon UI set first for review and naming design-taste-frontend, ui-ux-pro-max and frontend-design.
- Plan revision: 23
- Plan SHA-256: E4E6D438FE4058694EE20EA25F01F670F2AB6F33E0BD05F9C3AA8101E9552774
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical source: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5; authority confirms unsigned.
- Approved now: SRS-traceable screen/flow atlas and generated review boards for shared Auth, Teacher, School Manager and Platform Admin web UI.
- Not approved by this record: application source implementation, backend/API, Parent/mobile, promotion into approved/applied assets, commit or push. Await visual review before creating implementation approval.
## Revision 24 — full three-role web UI rebuild

- Status: APPROVED_FOR_IMPLEMENTATION.
- Approver: User, direct instruction on 2026-11-11 (Asia/Bangkok), to replace the old web UI with the Rev23 crayon design, follow the latest SRS, and check each completed section before continuing.
- Plan revision: 24
- Plan SHA-256: 072778CC86CCF6C2CDE18CDD034276F75371A4930FF5C18924F58191187BC345
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical SRS: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned.
- Approved scope: shared Auth plus Teacher, School Manager and Platform Admin web UI; presentation/layout rebuild only, preserve supported routes/auth/role checks/API behavior; truthful unavailable states; no Parent/mobile, other Admin UI, backend/API, tests/builds, commit or push.
- Section gates: manually review Auth, Teacher, School Manager and Platform Admin against SRS at 1440x900 and 390x844, record evidence after each before proceeding.

## Revision 25 — dashboard alignment pass

- Status: APPROVED_FOR_IMPLEMENTATION.
- Approver: User, direct request on 2026-11-11 to improve the UI a second time, keep the base frame, and reduce visual clutter while matching the demo.
- Approved scope: refine only Teacher, School Manager and Platform Admin overview dashboards against the corresponding Rev23 boards. Preserve shell, navigation, routes, logout, SRS boundaries, existing API behavior, and unsupported-flow disclosures. Auth and detail routes are not in this pass.
- Acceptance: three overview dashboards at 1440×900 and 390×844; remove duplicate preview/status copy and redundant quick links; preserve truthful empty/loading/error/unavailable states; no overflow or browser runtime errors; update FEAT-066 evidence/status.
- Plan revision: 25
- Plan SHA-256: F3B2413CBBE5BA649BE9736BD24CB8873E43144D6CFB98B2771001DC53ABCC44.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical source: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned.
- Not approved: Auth/login redesign, detail-route changes, Parent/mobile, backend/API, packages, automated tests/builds, commit or push.


## Revision 26 — content canvas background

- Status: APPROVED_FOR_IMPLEMENTATION by the user's direct instruction on 2026-11-11.
- Approved scope: CSS-only paper texture and sparse crayon corner marks behind authenticated Teacher, School Manager, and Platform Admin web content canvases, matching the Rev23 boards. Preserve shell, cards, typography, routes, API/authorization behavior and all product/privacy boundaries.
- Acceptance: review each role overview and representative detail/unavailable route at 1440×900 and 390×844; capture screenshots; no clipping, overflow, Vite/runtime/console errors.
- Plan revision: 26
- Plan SHA-256: 247E06100BD2506B1872EBA47E71549ACE8DFDC200614320464933A428800B38
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Not approved: Auth, Parent/mobile, other roles, backend/API, external assets/services, packages, automated tests/builds, commit or push.

## Revision 27 — shared three-role web authentication redesign

- Status: APPROVED_FOR_IMPLEMENTATION by the user's direct request on 2026-11-11: “Ok bây giờ làm lại cái giao diện login cho tôi đi dùng skill và brainstorm để dựng lại UI auth cho tôi”.
- Plan revision: 27
- Plan SHA-256: C9EF609A920F3C53F0153ED109660B85003D4D03A8E1E76C2F46C3EB2EEF21C2
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, `codex/fe-ui-web-remediation`.
- Canonical source: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; draft remains unsigned per `docs/context/SRS_AUTHORITY.md`.
- Approved scope: presentation rebuild of the shared `/login` page for Teacher, School Manager and Platform Admin only, using the brainstormed crayon learning-studio direction. Keep the existing auth adapter, role resolution, routes, role mismatch and local-preview semantics. Reuse the existing Three.js scene with static SVG fallback and accessibility/performance safeguards. Record manual local captures for all three roles at 1440×900, 1024×768, 768×1024 and 390×844.
- Not approved: Parent/mobile, authenticated role UI, backend/API/contracts, changes to auth provider/role semantics, real credentials/data, external services, new dependencies/assets, tests/builds, commit or push.



## Revision 28 — Rev68 web audit, structure cleanup, UI rebuild and one commit

- Status: APPROVED_FOR_IMPLEMENTATION.
- Approver: User, direct instruction on 2026-11-16 (Asia/Bangkok): clean the app folder structure, rebuild the web UI to match the provided SRS and named UI skills, commit the requested work once, and start the app for review.
- Plan revision: 28.
- Plan SHA-256: 8A63A0C4C3B80C5628E46AF7733FF4633964A7D73DD820E877833E2F7C59D029.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Product baseline: user-selected F:/Downloads/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md, v2.7-draft Rev68, SHA-256 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944; unsigned.
- Approved: clean role ownership and duplication under apps/web; rebuild shared login and Teacher, School Manager, and Platform Admin web surfaces; preserve supported API/auth behavior; disclose missing flows as unavailable; manually inspect role routes/responsive states; keep feature-local evidence; run required precommit validators; include the approved FEAT-067 consolidation, existing FEAT-066 web changes, this revision, and related records in exactly one local commit; start and leave the local web preview running.
- Boundaries: no Parent/Android/mobile, backend/API/authorization, SRS policy/sign-off, production data/services, secrets, new dependencies, app tests, push, PR, merge, or deployment.

## FEAT-066 Revision 29 — role login landing and remove local preview UX

- **Status:** APPROVED_FOR_IMPLEMENTATION by the project owner’s direct follow-up request on 2026-11-16: replace the currently open Teacher login page with the shared role-selection login shown in the attached reference, remove the preview panel, and make this the real API-connected version.
- **Plan revision:** 29.
- **Plan SHA-256:** 87F02A9B3CD64D21F1D1D1D051445E0413B5C03AC635BFF507E7CF3F962576C0.
- **Worktree/branch:** F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- **Approved scope:** `/login` and `/teacher/login` share the role-selection page; role cards proceed to real role sign-in, the local preview panel/bypass/routes are removed from active UI, and existing auth/API boundaries remain intact. Missing server APIs remain unavailable rather than simulated.
- **Commit:** Amend the existing local web commit to retain exactly one final commit on this branch. No push, PR, merge, or deployment.
- **No application tests:** preserve the existing no-tests boundary; run build and required repository validators.

## FEAT-066 Revision 30 — shared single-screen role login

- **Status:** APPROVED_FOR_IMPLEMENTATION by the project owner's direct correction on 2026-11-16: use the attached sign-in screen as the direct login page, remove the separate role chooser, and keep School Manager in the same login flow rather than jumping to another page.
- **Plan revision:** 30.
- **Plan SHA-256:** 8D167E39A75B3A13E68FBBB1C4672C018E9282920CC4478D9DFA4B16B1DAD12F.
- **Worktree/branch:** codex/fe-ui-web-remediation; baseline commit df07438e690cabf93ec9feacedcc5b6e3ca2709d.
- **SRS:** owner-selected unsigned v2.7-draft Rev68 task baseline; repository canonical unsigned Rev60 mismatch remains open and unchanged.
- **Approved scope:** shared /login sign-in layout with inline role switching; old role-card chooser and duplicate School Manager login presentation removed; compatibility routes select the corresponding role on the same screen; retain Teacher backend role resolution, Manager BE1 authentication and assignment gate, and Platform Admin's missing role-discovery limitation.
- **Commit:** amend the existing one local commit after evidence and checks; no push.
- **Boundary:** no backend/API/auth-contract or mobile changes, no credential entry, no application tests.

## FEAT-066 Revision 47 — shared web folder organization

- Status: APPROVED_FOR_IMPLEMENTATION.
- Approver: User, direct approval “OK làm đi” after reviewing the exact Rev47 folder map and import-update scope.
- Plan: plan/PLAN_REV47_SHARED_FOLDER_CLEANUP_20261117.md.
- Plan SHA-256 reviewed at approval: 3BF53425B5467913DA8DA188219E745BDD9B2EC647B73793B785D271BD8A3457.
- Current plan SHA-256 after status-only update: 82AB4F0E97144E8070E228B0ACDA59CB33102CCFF13C5F7927A0746FFF590E22.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Approved scope: move the 17 files under apps/web/src/shared into api/, auth/, components/, navigation/ and styles/ as specified in Rev47; preserve shared/assets; update only affected internal/external import specifiers in the 27 consumer files.
- Acceptance/verification: preserve behavior and unrelated dirty content; validate path references and run the web production build. Do not run the application test suite.
- Exclusions: no deletions, auth/API/style refactors, dependency changes, .env/secret access, commit, push, PR, merge or deployment.

## FEAT-066 Revision 48 — Manager 17-route test and GitHub record

- Status: APPROVED_FOR_EXECUTION.
- Approver: User, direct instruction on 2026-11-17 (Asia/Bangkok): plan integration of all 17 Manager APIs, run tests, record results, and push the record to GitHub.
- Plan: plan/PLAN_REV48_MANAGER_17_API_INTEGRATION_AND_TEST_20261117.md.
- Plan SHA-256: 4856A0895714A8346E7666BB8ABFE4661D50E11C4F94700690A101F0F4FCDC9D.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Approved scope: route/status audit, focused Manager FE and applicable isolated BE tests, read-only local smoke, build/lint/required push validators, FEAT-066 plan/evidence records, and a docs-only commit/push of the Rev48 plan/approval/test record.
- Boundaries: do not bypass the current SRS/BE guards or enable the six blocked routes; no live business writes, child data, backend contract/schema/authorization changes, secrets/tokens in output, unrelated dirty-file staging, or application source commit.
## FEAT-066 Revision 49 — local QA Admin and Manager accounts

- Status: APPROVED_FOR_EXECUTION.
- Approver: User, direct instruction on 2026-11-17 (Asia/Bangkok): “seed lại 2 cái 1 admin vs 1 manager cho tôi đi bỏ trong tmp”.
- Plan: plan/PLAN_REV49_QA_ADMIN_MANAGER_CREDENTIALS_20261117.md.
- Plan SHA-256: E59AA5D7522FE76F9441B80D6F95169240ADC662B720D7773F6E43F12A477557.
- Scope: reset credentials only for the one active reserved-domain Platform Admin QA identity and one active reserved-domain School Manager QA identity in sketch2life-dev; preserve roles and existing organization assignment; verify Firebase login and role/scope; save credentials only to Git-ignored tmp/qa-test-accounts.local.md; record sanitized EV-055.
- Boundaries: no production, duplicate/deleted users, non-QA account changes, database role/scope mutation, email, credential/token output, repo credential storage outside ignored tmp, source changes, commit, or push.
- Approval basis: the owner directly requested both test accounts and local tmp storage. This narrowly supersedes earlier QA plans' prohibition on persisting credentials only for the explicitly Git-ignored tmp file.
## FEAT-066 Revision 50 — Manager Classes empty-state review

- Status: APPROVED_FOR_EXECUTION.
- Approver: User, direct request on 2026-11-17: “Check cái này cho tôi đi” with the School Manager Classes screenshot.
- Plan: plan/PLAN_REV50_MANAGER_CLASSES_EMPTY_STATE_REVIEW_20261117.md.
- Plan SHA-256: D1837261C56BDEB688DF1D8F02653FC19C7C1ADAAA4A8E57C734095A4A254D19.
- Scope: inspect screenshot, source, SRS FR-T-02/FR-T-03, responsive styles, and perform an authenticated read-only classes GET.
- Boundaries: no API writes, class creation, account/database changes, source edits, tests/builds, commit or push.

## FEAT-066 Revision 51 — consolidate pending web worktree

- Status: APPROVED_FOR_EXECUTION.
- Approver: User, direct instruction on 2026-11-17: “Ghi lại toàn bộ và gom thành 1 commit cho tôi để đẩy lên máy kia làm”.
- Plan: plan/PLAN_REV51_WORKTREE_CONSOLIDATION_AND_PUSH_20261117.md.
- Plan SHA-256: 487ED5EB4DAEB6326535CDC0B7BB805303720D8DB3F3DD7340135BB678CA44C6.
- Scope: stage and commit all current non-ignored web-remediation worktree changes, records and reviewed screenshots in one new commit; run focused validation and push to the existing branch upstream.
- Boundaries: keep the previously pushed Rev48 commit; no history rewrite/force push; exclude .env, tmp QA credentials, passwords/tokens, service-account keys, external references, and ignored build/runtime files.
- Approval basis: the owner directly requested one consolidated commit and push for use on another machine; this supersedes earlier no-commit/push exclusions only for the current pending worktree changes.

## FEAT-066 MGR-7 — bounded BE contract-conformance implementation

- **Status:** APPROVED_FOR_IMPLEMENTATION by the owner’s conditional instruction on 2026-11-18, following coordinator review of the exact package and its R2 cold review.
- **Approved package:** `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MGR7_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT1_20261118.md`, 34,177 bytes, SHA-256 `37B412F3E10403238FDC9B940C437941293AD91F78EFDB76E61F5DE4C97E3FC3`.
- **Review:** `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/MGR_7_COLD_REVIEW_DRAFT1_R2_20261118.md`, SHA-256 `68947A735334E641CA966EED24BEF544A008A7BC042F3C867F4680C869E191D3`, ACCEPT with no findings.
- **Worktree/baseline:** `.worktrees/manager-api`, branch `feature/feat066-manager-api-contracts`, HEAD `1c9148e88600a101887e477541c4c4893ba1c7df`.
- **Approved exact BE allowlist:** `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`; `backend/src/sketch2life/infrastructure/lesson_library/service.py`; `backend/src/sketch2life/interfaces/http/openapi_contract.py`; `backend/tests/integration/lesson_library/test_lesson_library_api.py`; `backend/tests/unit/test_lesson_library_receipt_compatibility.py`; `backend/tests/contract/test_openapi_contract_catalog.py`.
- **Approved behavior:** set only the Parent Groups and access-grants list defaults to 25 while preserving max 100, filters, cursors and stable ordering; change shared Lesson Library same-key/different-payload idempotency response to HTTP 400 `INVALID_IDEMPOTENCY_KEY`; preserve same-key/same-payload original-response replay and receipt scope/retention; align the static full OpenAPI catalog and the allowlisted tests.
- **Explicit exclusions:** no FE file or UI action; no new route/DTO, schema/table/migration, gateway/proxy, `app.py` error-envelope mapping, public SRS projection, MGR-2 capacity, MGR-3 assignment/candidate, MGR-4 invitation/member writes, MGR-5 consent writes, or MGR-6 exact-version/hash decision path. MGR-9 FE integration requires its own reviewed plan and approval after BE implementation evidence.
- **Verification boundary:** source/test-file edits are approved within the exact allowlist. Test execution, build, typecheck, lint, validators, diff-check, OpenAPI generation, runtime, database, Docker, network/provider and Modal commands remain NOT AUTHORIZED by this entry and require a separate owner command instruction with the environment boundary specified in the plan.
- **Git boundary:** no stage, commit or push is authorized by this approval.

Verification limit, 2026-11-18: The owner authorized exactly the two MGR-8 pytest commands ("Đúng 2 lệnh này", "Codex chạy") against an owner-prepared disposable local be1_acceptance database. The first command was invoked once with the root backend virtual environment interpreter and PYTHONPATH=src, then interrupted while pending without captured output; no exit code or test summary was captured. The second command was not run. No retry was made. MGR-8 remains NOT VERIFIED.

Diagnostic scope, 2026-11-18: The owner authorized exactly three diagnostic pytest commands ("Chạy chẩn đoán"), run by Codex with the root backend virtual environment interpreter, PYTHONPATH=src and PYTHONUNBUFFERED=1, against the owner-prepared disposable local be1_acceptance database. D1 exited 0 with 8 passed. D2 was interrupted after about 12 minutes when output had not grown for 10 minutes; the shell returned 1, with no pytest exit status or final summary captured. D3 was not run. The diagnostic does not decide whether MGR-8 verification is satisfied; owner disposition is required.

Scope amendment, 2026-11-18 (MGR-8 fixture): The owner approved in chat ("Approve the fix") one minimal fixture edit inside the already-allowlisted `backend/tests/integration/lesson_library/test_lesson_library_api.py`. The edit sets `account_role` on the four synthetic adult identities created by the fixture: teacher to `teacher`, manager to `school_manager`, parent to `parent`, platform admin to `platform_admin`. `role_revision` is not set because the model defaults it to 1. Reason: the owner-run D3 failed 6 of 7 tests with HTTP 403 `ACCOUNT_SCOPE_UNAVAILABLE`, because the fixture predates the account-role gate in `routers/be1_common.py` and the parent and platform-admin role checks in `routers/lesson_library.py`. No other line, test assertion, source file or file outside the six-file allowlist is approved by this amendment. The owner re-runs D3 in their own terminal; this amendment authorizes no test run by an agent. The D2 catalog failure (`KeyError: 'description'`, pre-existing on dev in `app.py`) is not decided here: no `app.py` change is approved. No stage, commit or push is authorized. MGR-8 remains NOT VERIFIED. Pre-append pin of this file: 38982 bytes, SHA-256 5272BA9768407FFF04BD8414F1536DEFE1E8C8FBC0C5EF0596513CEA0BA6CCB3.

MGR-8 verification result, 2026-11-18: the owner ran D1, D2, D3 and `tests/contract/test_app_composition.py` in their own terminal on the root checkout's M2 branch, after merge `b93d7334`. Each command was run once with the root backend virtual environment interpreter, `PYTHONPATH=src`, `PYTHONUNBUFFERED=1` and the diagnostic output flags, against the owner-prepared disposable local `be1_acceptance` database.

| Test | Result |
|---|---|
| D1 | 8 passed |
| D2 | 5 passed |
| D3 | 6 passed, 1 failed (PDF upload: 503, because ClamAV is not running; outside the MGR-7 change) |
| `test_app_composition` | 7 passed |

Owner decision: "R ok verified làm bước 5 đi" — MGR-8 VERIFIED, with the ClamAV environment limit recorded. Evidence: `evidence/notes/MGR_8_ROOT_RUN_RESULTS_20261118.md` (6,785 bytes, SHA-256 `19A6E63C106EFF951A162CF4B48475FBF442EF3656A30D29F910FFC2CECE1601`). This note does not approve a commit or push.

## FEAT-066 CONV-1 — API conventions core (BE)

- **Status:** APPROVED_FOR_IMPLEMENTATION, by the owner's chat answer of 2026-11-18 (option "Approve Draft 5"). **Not launched:** coding starts only on a separate owner word.
- **Approved package:** `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT5_20261118.md`, 47,483 bytes, SHA-256 `3FCF47412F69D8A16EFFFC7978C5E2BD107EA429EF3F42D354BCE00FF7451278`.
- **Reviews:** all four on Sonnet 5.5 at high effort, set explicitly. The records are in `evidence/notes/`:

  | Round | Record | Verdict (P1/P2/P3) |
  |---|---|---|
  | 1 | `CONV_1_COLD_REVIEW_DRAFT1_20261118.md` (`801D0246…`) | NOT READY 1/8/7 |
  | 2 | `CONV_1_COLD_REVIEW_DRAFT2_R2_20261118.md` (`73552C0B…`) | NOT READY 1/1/13 |
  | 3 | `CONV_1_COLD_REVIEW_DRAFT3_R3_20261118.md` (`80DE3C1E…`) | NOT READY 0/2/8 |
  | 4 | `CONV_1_COLD_REVIEW_DRAFT4_R4_20261118.md` (`FD63A12D…`) | READY WITH NOTES 0/0/5 |

  Draft 5 fixes the round-4 P3 notes only and was not re-reviewed.
- **Decisions:** `DECISIONS.md` D-066-68, D-066-69 and D-066-71.
- **Branch:** `feature/feat066-conv1`, created from `08439b22`. It is local only and is never pushed.
- **Approved allowlist:**
  - files 1 to 29 of package §4, each within its stated limit;
  - edits to existing tests 16 to 28 limited to status, code, envelope and message assertions;
  - the governance documents named in §4, written by the coordinator, append-only.
  - Any other file stops the task and needs an owner scope amendment.
- **Approved behaviour:** package §3.2 items 1 to 8, with the D-066-71 answers.
- **Exclusions:** package §3.3. In particular:
  - no `/api/parent/v1/ai` change;
  - no upload or file code or status alignment;
  - no route move;
  - no FE, mobile or Bruno file;
  - no migration or dependency change;
  - no OpenAPI change for Platform Admin, auth or Teacher AI.
- **Verification boundary** (package §7):
  - **Coordinator or Codex**, without a database or TestClient: ruff, mypy, the new unit tests, the four repository validators, and `git diff --check`.
  - **Owner-run** in the owner's terminal against the disposable `be1_acceptance` database: the TestClient and database tests.
  - No database, Docker, network, provider or Modal command is otherwise authorized.
- **Git boundary:** no stage or commit without a separate owner word, and never a push.

Scope amendment, 2026-11-18 (CONV-1 fixtures): the owner approved in chat ("Cho sửa fixture") one fixture change in two files that the allowlist already contains: `backend/tests/integration/test_be1_postgres_api.py` (row 23) and `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` (row 24).

**The change:** three synthetic adult identities get an `account_role`:
- `test_be1_postgres_api.py`: the School Admin fixture (about line 94) gets `school_manager`, and the observer fixture (about line 229) gets `teacher`;
- `test_be1_synthetic_pilot_postgres.py`: the pilot harness fixture (about line 425) gets `school_manager`.

**Why:** the role gate in `be1_common.require_assignment` has required `account_role` since commit `800c8e9f`. Without it, these fixtures failed at the base too, with 403 instead of 404. In the first CONV-1 owner run, 73 setups errored, so the BE1 behaviour of CONV-1 could not be verified. This is the same gap as the MGR-8 fixture amendment for the Lesson Library test.

**Unchanged:** no assertion meaning and no other file. This note authorizes no commit or push.

## FEAT-066 SEED-1 — S1 core-data seed (tool and tests)

- **Status:** APPROVED_FOR_IMPLEMENTATION, by the owner's chat instruction of 2026-11-18 ("làm SEED-1 tiếp đi check lại nếu ổn thì duyệt") after the coordinator's re-check. **Not launched:** coding starts in BE queue slot 3, after FR-C-08, and only on a separate owner word.
- **Approved package:** `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_SEED1_S1_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT4_20261118.md`, 23,121 bytes, SHA-256 `141488271D7FB37FDDAD1B0BA7005CF96ABAAA00EC627E80E2AA848638410BFA`.
- **Reviews** (in `evidence/notes/`):

  | Round | Record | Verdict (P1/P2/P3) |
  |---|---|---|
  | 1 | `SEED_1_COLD_REVIEW_DRAFT1_20261118.md` (`33C2AC3D…`) | NOT READY 0/4/6 |
  | 2 | `SEED_1_COLD_REVIEW_DRAFT2_R2_20261118.md` (`4A19BFAD…`) | NOT READY 0/2/6 |
  | 3 | `SEED_1_COLD_REVIEW_DRAFT3_R3_20261118.md` (`797C024C…`) | READY WITH NOTES 0/0/7 |

  Draft 4 fixes the P3 notes and was not re-reviewed.
- **Decision:** D-066-72.
- **Branch:** `feature/feat066-seed1`, local only and never pushed, cut from the tip of the BE queue when the slot opens.
- **Approved allowlist:** package §4 rows 1 to 9:
  - `backend/tools/seed/__init__.py`, `guard.py`, `data.py` and `s1_core.py`;
  - tests `tests/unit/test_seed_guard.py`, `tests/unit/test_seed_data.py` and `tests/integration/test_seed_s1_postgres.py`;
  - the runbook and the evidence note;
  - the governance records, written by the coordinator, append-only.

  Product modules are imported read-only. A change to any product module stops the task for an owner scope amendment.
- **Approved behaviour:** package §3 (guard, markers and column rules, idempotency and atomicity, data set, counts).
- **Exclusions:**
  - S2 to S4 and anything in Billing;
  - consent records, sessions and eligibility proofs;
  - lesson source documents and revisions, and command receipts;
  - Bruno environments;
  - FE sign-in;
  - migrations.
- **Verification boundary:**
  - **Coordinator or Codex:** the package §5 commands (ruff, mypy, unit tests 5 and 6, the four validators, `git diff --check` after `git add -N` on the nine task paths).
  - **Owner-run, against the seed database only:** the name contains `seed`; the port is neither 5432 nor 5433; never `be1_acceptance` or `sketch2life_m2_s1a`. The steps are `alembic upgrade heads` on a fresh database with `S1A_P_ALEMBIC_DATABASE_URL` set explicitly to the seed URL, S1 run twice, the counts, and test 7.
  - No other database, Docker, network, provider or Modal command is authorized.
- **Git boundary:** no stage or commit without a separate owner word, and never a push.

## FEAT-066 PAY-0 — payment interface skeleton (package)

- **Status:** PACKAGE APPROVED on 2026-11-18 (D-066-73). **Not launched.** This entry approves the PAY-0 design and its split into three slices. It authorizes no code: each of PAY-0a, PAY-0b and PAY-0c needs its own Task Approval entry with an exact allowlist and command ceiling, and an owner word to start, in its BE queue slot after FR-C-08 and SEED-1.
- **Approved package:** `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_PAY0_PAYMENT_INTERFACE_SKELETON_DRAFT6_20261118.md`, 68,734 bytes, SHA-256 `AE4DB60B67F935FB7F874B3498626B5DE1D38448891561906DC78B476388078E`.
- **Reviews** (in `evidence/notes/`):

  | Round | Record | Verdict (P1/P2/P3) |
  |---|---|---|
  | 1 | `PAY_0_COLD_REVIEW_DRAFT1_20261118.md` (`38C88823…`) | NOT READY 2/12/5 |
  | 2 | `PAY_0_COLD_REVIEW_DRAFT2_20261118.md` (`117B7F32…`) | NOT READY 1/6/7 |
  | 3 | `PAY_0_COLD_REVIEW_DRAFT3_20261118.md` (`D25733EC…`) | NOT READY 0/5/9 |
  | 4 | `PAY_0_COLD_REVIEW_DRAFT4_20261118.md` (`6679D17B…`) | NOT READY 0/3/9 |
  | 5 | `PAY_0_COLD_REVIEW_DRAFT5_20261118.md` (`B6C2512A…`) | NOT READY 0/1/7 |

  Five rounds are used. Draft 6 fixes the round-5 findings and was not re-reviewed, by owner choice.
- **Decision:** D-066-73 (amends D-066-65 for the skeleton only).
- **Slices** (package §9):
  - **PAY-0a Foundation:** domain types and the transition table, ports and DTOs, the Alembic migration for the three payment tables (branch label `billing`, independent root), repositories, the fake provider and test kit, the fake quote-inputs and fulfilment ports, and the settings with their validator.
  - **PAY-0b Callback intake:** the intake service, the organization checkout lock helper, the abuse limiter, the callback route, security and warning events, the review transaction, the `signed:` receipt path, and the provider contract suite.
  - **PAY-0c Checkout and jobs:** the checkout and status routes, the `CONV1_PREFIXES` addition and the new codes' messages, the background jobs with the job-transition rule, the one-shot command and the RQ enqueue.
- **Exclusions:** Billing core (frozen), including the real `BillingQuoteInputsPortV1` and the Billing side of `PaymentFulfilmentPortV1`; real MoMo and VNPAY code (PAY-1 onward, payment teammate); the Parent top-up route; refunds and the operator review screen (PAY-3); the periodic scheduler (a separate owner-lane slice, PD-9a); option B of package §6; notifications, FE screens and Bruno.
- **Dependency:** the CONV-1 envelope, which exists only on the local-only branch `feature/feat066-conv1` (D-066-71, CV-B). Each PAY-0 branch is cut from a queue tip that contains it.
- **Test boundary for the later slices:** cases marked PG need a disposable PostgreSQL database whose name and port the slice approval fixes; never `sketch2life_m2_s1a`, never ports 5432 or 5433; run by the owner.
- **Git boundary:** no stage or commit without a separate owner word, and never a push.

## FEAT-066 C-M — School Manager per-role slice (package)

- **Status:** PACKAGE APPROVED on 2026-11-18 (D-066-75). **Not launched.** This entry approves the C-M design, its five sub-slices and the settled answers CM-1 to CM-12. It authorizes no code: C-M1 BE, C-M1 FE, C-M2, C-M3, C-M4 and C-M5 each need their own Task Approval entry with exact paths and a command ceiling, and an owner word to start.
- **Approved package:** `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_CM_SCHOOL_MANAGER_SLICE_PACKAGE_DRAFT4_20261118.md`, 28,716 bytes, SHA-256 `401E893503D5DC96071B88AE264DB3F029F076F10AF0824CA6366DACC092CF8A`.
- **Reviews** (in `evidence/notes/`):

  | Round | Record | Verdict (P1/P2/P3) |
  |---|---|---|
  | 1 | `CM_COLD_REVIEW_DRAFT1_20261118.md` (`E435B65D…`) | NOT READY 1/6/8 |
  | 2 | `CM_COLD_REVIEW_DRAFT2_20261118.md` (`070D41F0…`) | NOT READY 0/5/6 |
  | 3 | `CM_COLD_REVIEW_DRAFT3_20261118.md` (`C861311E…`) | NOT READY 0/2/7 |

  Draft 4 fixes the round-3 findings and was not re-reviewed, by owner choice.
- **Decision:** D-066-75.
- **Sub-slices** (package §4):
  - **C-M1 Roster reads and School Manager privacy:** cursor paging on A07 and A10; the School Manager A09 summary and A10 Manager list; the class-scoped Teacher rule; School Manager 403 on the session roster and pilot profiles; the repaired outdated test and the named PostgreSQL cases. BE part first, then the FE part after O-9 and before M9-A and M9-B.
  - **C-M2 W-LESSON** (A12, A13, G06): after the MGR-6 answers and contract Draft 2; FE part is MGR-9 M9-C.
  - **C-M3 W-ASSIGN** (B02, G02): after the MGR-3 answers and contract Draft 2; FE part is MGR-9 M9-B.
  - **C-M4 W-CAP** (B01, G01): after Billing B-1 and B-2 (D-066-74); FE part is MGR-9 M9-A.
  - **C-M5 UC-12** (G09): after C-M3.
- **Queue:** C-M1 BE after FR-C-08, SEED-1 and PAY-0a to 0c, and before Billing B-1 (CM-10).
- **Branch:** C-M1 BE on the local-only branch `feature/feat066-cm1`, never pushed (CM-9). A web branch that carries a local BE merge is not pushed until an owner-approved publication step.
- **Exclusions:** consent writes and meaning (MGR-5), Parent-group invitations (MGR-4), Billing and payment, Teacher-only routes, and the privacy debt of package §8.
- **Test boundary for the later slices:** PostgreSQL cases on a disposable database whose name contains `be1_acceptance`; never `sketch2life_m2_s1a`; never ports 5432 or 5433; run by the owner.
- **Git boundary:** no stage or commit without a separate owner word, and never a push.

## FEAT-066 L2 Billing — contract of record (Draft 9)

- **Status:** CONTRACT APPROVED on 2026-11-18 (D-066-76). **Not launched.** This entry approves the Billing contract and its slice plan. It authorizes no code: each of B-1 to B-5 needs its own Task Approval entry with exact paths and a command ceiling, and an owner word to start in its BE queue slot.
- **Approved contract:** `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_L2_BILLING_CONTRACT_DRAFT9_20261118.md`, 63,668 bytes, SHA-256 `3280BBC9486780E108D5A0C3A3921D7E8EF13E5F48A9BF2B748645739ADC7876`.
- **Reviews:** Drafts 1 to 6 in six rounds (records `L2_BILLING_CONTRACT_DRAFT*_COLD_REVIEW_20261118.md`); Draft 7 closed without review (D-066-66); Draft 8 one round, NOT READY 0/3/10 (`L2_BILLING_CONTRACT_DRAFT8_COLD_REVIEW_20261118.md`, `5F3F80F5…`); Draft 9 fixes those findings and was not re-reviewed, by owner choice.
- **Decisions:** D-066-66, D-066-67, D-066-73, D-066-74, D-066-75, D-066-76.
- **Slices** (contract §11): B-1 Foundation (extends the PAY-0a `billing` branch; subscription foreign keys on the payment tables); B-2 class-create admission (BE1); B-3 video quota; B-4 the Billing side of the payment interface and the real quote-inputs port; B-5 lifecycle and downgrade. Plus the periodic runner slice of D-066-73 PD-9a.
- **Queue:** FR-C-08 → SEED-1 → PAY-0a → PAY-0b → PAY-0c → C-M1 BE → B-1; the owner sets the runner position and the order of B-2 to B-5.
- **Dependencies:** B-1 after PAY-0a; B-2 needs an approved price version in the environment and zero organizations without a subscription; B-4 after the payment teammate's review of contract §7.4 and §7.7.
- **Exclusions:** payment flows and MoMo adapters (payment teammate, PAY-1 onward); purchase routes (payment side); notifications; FE screens.
- **Test boundary for the later slices:** concurrency tests on a disposable PostgreSQL database whose name and port each slice approval fixes; never `sketch2life_m2_s1a`; never ports 5432 or 5433; run by the owner.
- **Git boundary:** no stage or commit without a separate owner word, and never a push.

### FEAT-066 SEED-1 — queue amendment (2026-11-19)

- **Amends** the "Not launched" line and the branch line of the SEED-1 entry above: by D-066-77, SEED-1 now runs **before** FR-C-08. Its branch `feature/feat066-seed1` (local only, never pushed) is cut from the current BE queue tip, the CONV-1 line `feature/feat066-conv1`, when SEED-1 starts.
- **Unchanged:** the approved package (Draft 4, `141488271D7F…`), the allowlist, the behaviour, the exclusions, the verification boundary (owner-run against the seed database only: name contains `seed`; port neither 5432 nor 5433; never `be1_acceptance` or `sketch2life_m2_s1a`), and the Git boundary.
- **Still required:** a separate owner word to start coding.

### FEAT-066 SEED-1 — guard live-check amendment (2026-11-19)

- **Amends** package §3.1 (Draft 4) by D-066-78: the server-side live check keeps the database-name and database-owner checks and drops the `inet_server_port()` and loopback `inet_server_addr()` checks, which cannot pass through Docker port mapping.
- **Paths:** `backend/tools/seed/guard.py` and `backend/tests/unit/test_seed_guard.py`, already in the SEED-1 allowlist. No new path.
- **Unchanged:** every client-side guard check, the data set, the writer, the verification boundary (owner-run against the seed database only: name contains `seed`; port neither 5432 nor 5433; never `be1_acceptance` or `sketch2life_m2_s1a`) and the Git boundary.

## FEAT-066 Phase B and C — goal v2 program APPROVED by the owner — 2026-11-19

- **Owner decision:** the owner approved the goal v2 program for Phase B and Phase C as written in
  `plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md` (13,611 bytes, SHA-256 `5DFC1EDEFC79A1C4B57CC7F1C288F284AB9DFACD1CFD18B3864ACD14374795F8`), and asked the coordinator
  to do the pre-launch setup (this record and the `pnpm install` of the web and mobile worktrees).
- **What the approval covers:** the tasks B1 to B4 and C1 to C6 and the end steps D1 to D4 of that program, each
  inside the program's ground rules (§1): decisions taken from the SRS (D-209 copy) and recorded as the goal's,
  independent review on Sonnet 5.5 high for every plan and implementation, one local commit per finished task
  after its checks, the disposable `frc08` loopback containers only, and the stated never-list. Billing
  (B-1, PAY-0a to PAY-0c, C-M1 BE, seed S2 to S4, M9-A) is deferred and not covered.
- **Git boundary:** commit locally only; **no push of any branch, no PR, no remote merge**. The owner checks the
  final result and does every push. The web branch `codex/fe-ui-web-remediation` is shared with a teammate: the
  goal fetches and merges the teammate's pushed commits locally before each web task and never rewrites them.
- **Not covered:** the launch itself (a separate owner word); any push, PR or merge; anything on the program's
  never-list. `OWNER_MODAL_CALL_APPROVED=NO`.

## FEAT-066 BRU-0a — Bruno scaffolding and A02 baseline (L5-0 part 1 plus the first positive case)

- **Status:** APPROVED_FOR_IMPLEMENTATION by the owner's chat instruction of 2026-11-19. **Not launched:** coding starts only on a separate owner launch word.
- **Scope:** the first part of plan step **L5-0** (a new loopback-guard `collection.bru`, the L5 README, the expected-failure list file, the owner-run runbook) and **one request, A02** (`GET /health`). **L5-0 is delivered in two parts.** This entry delivers 0a. O-BRU-AUTH, the runtime token variables (plan §5) and the `target` folder tags stay open in 0b. BRU-0b (A17, A20, A22, A26, A27) and A08 are **not** part of this entry; each needs its own entry after O-BRU-AUTH (and, for A08, O-L3SCOPE) is decided.
- **Approved plan:** `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_L5_BRUNO_COVERAGE_DRAFT3_20261118.md`, 18,584 bytes, SHA-256 `3F5AFCC727F3C43451903582FF0DBA05BC0F181290AA6D510B0B6C54973786A9`. Sections used: §0 (S-3), §3 (rules 2 to 6), §4, §7 (L5-0 part 1, L5-1 for A02 only).
- **Review of the plan and of this entry:** Draft 3 was reviewed in round 3 on 2026-11-19 (Sonnet 5.5, high): **NOT READY, 0 P1 / 3 P2 / 9 P3**. The report is `L5_DRAFT3_REVIEW_R3_20261119.md`, 34,247 bytes, SHA-256 `7766C981A0140439B571A9877FB9C309E6D32EB537FED1ECC5D32E3523E6D5CF` (stored in `evidence/notes/L5_DRAFT3_REVIEW_R3_20261119.md`). The three P2 items concerned the draft entry, not the plan, and are closed by the terms below (disposition table at the end). The plan itself needs a Draft 4 before BRU-0b and later steps (L5R3-04, 05, 11, 12); that is not required for 0a.
- **Gates for this entry:**

  | Gate | State |
  |---|---|
  | S-3 (`local.bru`) | Met: the owner's collection edits are committed in `b95fed64`; `environments/local.bru` holds placeholders only |
  | O-BRU-BASE | Met (`b95fed64`) |
  | **CONV-1** (`2dddc607`: `X-Request-ID` on every response, including `/health`) | Met **in the base** `4e2f6d96`; the app under test must run from that code (see Run record) |
  | G0 | Met (`08439b22`); not needed by A02 |
  | SEED-1 S1 | Met (`4e2f6d96`); A02 reads no seeded data |
  | S-1 (password rotation) | **Not a gate for 0a:** A02 uses no credential. S-1 stays open and is tracked in plan §0; it is a gate for BRU-0b. This entry does not count the launch word as proof of rotation |
  | O-BRU-AUTH, O-L3SCOPE | **Not needed:** A02 has `auth: none` and is not a CB route |

- **Decision:** D-066-81 (drafted as D-066-78; renumbered because D-066-78 is taken in both lineages).
- **Branch and base:** new local-only branch `feature/feat066-bru0` in a new worktree `D:\GitHub\Sketch2Life\.worktrees\bru0`, cut from the tip of `feature/feat066-seed1` (expected `4e2f6d96eb7d196867d0d1f049cbbf216f04c25c`). **Never pushed, no upstream.** The base is chosen for CONV-1 (the `X-Request-ID` behaviour). The BRU-0a commit therefore depends on `feature/feat066-conv1` and `feature/feat066-seed1`, which are also local-only and unmerged; it lands after them.
- **Approved allowlist** (new files only; no existing request, environment file or `bruno.json` is edited). In `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/`:
  - `collection.bru`: a pre-request script, specified under "Loopback guard" below;
  - `requests/l5/README.md`: the L5 listing, run instructions, the guard's reach, how to run a request outside loopback on purpose, labels for stale (004/005) and `dev`-only (128, 131 to 135) requests (O-BRU-LABELS). Role-variable names (upper snake case) are listed as **provisional until O-BRU-AUTH is decided**;
  - `requests/l5/shared/bru-0/001-health-get.bru`: the one A02 request, `seq: 1`. **No `folder.bru` and no other file** is added.

  In `features/FEAT-066-fe-ui-srs-full-review/`:
  - `evidence/L5_EXPECTED_TARGET_FAILURES.md` (an empty list);
  - `evidence/notes/BRU_0A_IMPLEMENTATION_EVIDENCE_20261119.md`;
  - `plan/L5_BRU0A_RUNBOOK_20261119.md` (the owner-run block).

  The governance records (this entry, DECISIONS, CONTEXT) are written by the coordinator, append-only.
- **Loopback guard (`collection.bru`):**
  - It applies to **every request in the collection** (the 144 existing request files, the Firebase helper folder included) and in the Bruno desktop as well as the CLI. This is by design. Effect: any request to a non-loopback host fails with a script error. The README documents how to run such a request deliberately (from a different collection, or on the owner's own branch without this file).
  - **Owner decision (2026-11-19):** keep the collection-level file `collection.bru` (the stricter option); it applies to every request in the collection.
  - It must check the **interpolated** URL. If the implementer cannot establish from material in the repository how to obtain the interpolated URL in a Bruno 4.3.0 pre-request script (for example `bru.interpolate(req.getUrl())`), it **stops and reports** instead of guessing. It parses the URL with a URL parser, accepts only the exact hostnames `127.0.0.1`, `localhost` and `[::1]`, rejects user-info and look-alike hosts, and **throws on any parse failure** (fail closed).
  - Not covered, and stated as such in the README: redirects, and URL changes made later by a request script. The static scan below bans `setUrl`, `sendRequest` and `runRequest` in the new files.
  - **Negative control (owner-run, in the runbook):** run the A02 request once with `baseUrl` overridden to `http://guard-test.invalid`; expected: a script error and zero HTTP traffic. Record the outcome only (counts). The override mechanism is not verified; if it does not apply, the owner edits the local, git-ignored environment value instead and reverts it.
- **Approved behaviour (A02):** positive case only: `GET {{baseUrl}}/health`, no `Authorization` header, no `X-Request-ID` sent. Three assertions, as separate named checks:
  1. status 200;
  2. JSON body equals `{"status": "ok", "service": "sketch2life-api"}` (source: `health.py:16-18`, `test_health.py:6-10`);
  3. **CONV-1 behaviour:** response header `X-Request-ID` is present and non-empty (presence only; the value is a generated id; source: `app.py` `be1_request_context`, `test_http_error_conventions.py:129-130`). Checks 1 and 2 stand without it.

  The existing request `requests/health/090-health-health-get.bru` is left untouched. "No database needed" is a statement about the route only; whether the app process starts without a database is not verified.
- **Run record (owner-run):** besides the plan's fields, the record states the **app commit**: the app is started from the `bru0` worktree and `git rev-parse HEAD` of that tree is written in the record. Running the app from the root checkout or the M2 tip (`08439b22`) is not valid for assertion 3.
- **Exclusions:** A08, A17, A20, A22, A26, A27; any request that needs a token; any state-changing request; negative and target cases other than the guard negative control; the Firebase auth helper folder (`requests/firebase-auth-helper/`) and `.env` (never opened); edits to owner files; Bruno CLI installation; SEED amendments.
- **Verification boundary:**
  - **Coordinator or Codex:** read-only checks; a static scan of the new files for `setEnvVar`, `setGlobalEnvVar`, `setUrl`, `sendRequest`, `runRequest`, `console.log`, `eyJ`, `AIza`, `@gmail.com` and any host other than `{{baseUrl}}`; byte checks (CR, trailing whitespace); `python tools/validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, `git diff --check`.
  - **Owner-run only:** `bru run` with the pinned Bruno CLI (`@usebruno/cli` 4.3.0, `--env local`, `--reporter-skip-all-headers --reporter-skip-body`), against the app described in the Run record, plus the negative control. Any report or output file goes under `tmp/feat066-l5/` (git-ignored). Report counts only.
  - Codex and the coordinator run **no** `bru`, database, Docker, network, provider or Modal command, never use ports 5432 or 5433, never read `D:\s2l-gate-secrets`, and never read or print tokens or passwords.
- **Git boundary:** no stage or commit without a separate owner word, and never a push. One commit per finished task, explicit paths only, after `python tools/validate_repository_security.py`.
- **Independent review:** after implementation, one review on Sonnet 5.5 at high effort, set explicitly, started by the coordinator.

### Disposition of review round 3 (entry-related findings)

| Finding | Disposition |
|---|---|
| L5R3-01 (P2) CONV-1 dependency, app commit | Closed: CONV-1 gate row, base rationale, Run record, assertion 3 marked CONV-1 |
| L5R3-02 (P2) guard reach | Closed: disclosed in the guard section and the README; owner decision line for collection versus folder level |
| L5R3-03 (P2) URL resolution, no guard test | Closed: interpolated-URL rule with stop condition, fail-closed parsing, owner-run negative control |
| L5R3-04 (P3) guard hazards | Partly: parser rules and ban on `setUrl`, `sendRequest`, `runRequest`; redirects documented as not covered |
| L5R3-05 (P3) secret gaps | Partly: scan list extended, output under `tmp/`; the rest goes to plan Draft 4 |
| L5R3-06 (P3) allowlist | Closed: exact request path and `seq`, no `folder.bru` |
| L5R3-07 (P3) L5-0 split, S-1 | Closed |
| L5R3-08 (P3) placeholders | Closed |
| L5R3-09 (P3) stacked local branches | Closed: dependency stated |
| L5R3-10 (P3) A02 wording | Closed: three named assertions |
| L5R3-11, 12 (P3) | Deferred to plan Draft 4 (BRU-0b and later) |

### FEAT-066 BRU-0a — addendum 1 after review round 4 (2026-11-19, owner Person 2)

- **Status:** APPROVED_FOR_IMPLEMENTATION, appended to the BRU-0a entry above; the approved text above is unchanged and this addendum prevails where they differ. **Not launched.** This addendum was not re-reviewed.
- **Review:** round 4 of entry Draft 2 (Sonnet 5.5, high): NOT READY, 0 P1 / 2 P2 / 6 P3. Report `evidence/notes/BRU0A_ENTRY_D2_REVIEW_R4_20261119.md`, 29,156 bytes, SHA-256 `65569D1021575EAF6E62E87E1326E2CF640FC790E99E42907DE0F8BDFE0AEAF3`. The in-repo entry equalled Draft 2 except for the five permitted substitutions. O-BRU-AUTH, O-L3SCOPE and S-1 are not needed for 0a (confirmed).
- **R4-01 (app code origin):** the runbook contains the app start-up step with `PYTHONPATH` set to the `bru0` worktree's `backend\src`, because the backend venv's editable install points at the root checkout (no CONV-1). The run record states `git rev-parse HEAD` of the `bru0` tree and the printed `sketch2life.__file__` under the same environment; the path must be inside the `bru0` worktree. An assertion-3 failure with a package from another tree is an invalid run, not an A02 defect.
- **R4-02 (guard route b):** the guard is written as a candidate and marked **UNVERIFIED**. The implementer uses the interpolated URL (for example `bru.interpolate(req.getUrl())`), parses it, accepts only the exact hostnames, and throws on any failure. The entry's stop condition ("cannot establish from material in the repository") is **replaced**: the implementer does not stop for lack of Bruno 4.3.0 material; it records the interpolation and sandbox questions as NOT VERIFIED in the evidence note. The guard is proven only by the two owner-run controls: the positive run on loopback passes, and the negative control fails with a script or pre-request error that names the guard. Until both are recorded, the evidence note and the README call the guard unproven. An uninterpolated URL fails to parse and throws, so a mistake in this route makes A02 fail visibly and does not open the guard.
- **R4-03 (control fallback):** if `--env-var baseUrl=...` does not apply, the owner runs the control from a throwaway copy of the collection under `tmp/feat066-l5/`, or edits the tracked `environments/local.bru` and checks that `git diff` of that file is empty after the revert. The task itself edits no environment file. Never `git add -u`.
- **R4-04 (evidence):** the expected result of the negative control is the error class: a script or pre-request error naming the guard, not a connection or DNS error. The owner records the error class and counts. "Zero HTTP traffic" is no longer the criterion. Two further controls are optional: `http://127.0.0.1@guard-test.invalid/` and `http://localhost.guard-test.invalid/`.
- **R4-05 (scan and diff check):**
  - the host and API-name scan runs on `collection.bru` and the request file only, and the loopback hostnames are allowed inside the guard;
  - the scan for `setEnvVar`, `setGlobalEnvVar`, `setUrl`, `sendRequest`, `runRequest` and `console.log` runs on the `.bru` files, so the README may name them;
  - the scan for `eyJ`, `AIza` and `@gmail.com` runs on all new files;
  - new untracked files are checked with `git diff --no-index --check` per file and a byte check for CR and trailing whitespace; `git add -N` stays forbidden;
  - the README lists role-variable names without `NAME=value` lines (the repository security validator rejects them).
- **R4-06 (guard reach):** the guard applies to every request of the collection: the 144 tracked request files, and the local-only Firebase helper folder where it exists. This is stated for the CLI. Behaviour in the Bruno desktop is **not verified** and the README must not claim it.
- **R4-07 (run command):** the owner-run command is `bru run requests/l5/shared/bru-0 --env local --reporter-skip-all-headers --reporter-skip-body` with `@usebruno/cli` 4.3.0, **never from the collection root without a path**. A02 reads no data; the run record states that no database read is expected and records whether the app is connected to the seed database or to none, as plan §3 rule 2 asks.
- **R4-08 (record):** the disposition rows L5R3-01 and L5R3-03 of the entry are **Partly**, not Closed. This addendum closes R4-01 to R4-07. No commit or push is authorized; the launch needs a separate owner word.

### FEAT-066 BRU-0a — addendum 2, B2 completion record (2026-11-19, record of work done; owner Person 2 to accept)

- **Status:** B2 IMPLEMENTED AND RUN; **owner acceptance pending**. Local commit only, never pushed. This addendum records what was done after the entry and addendum 1; it approves nothing new. Where it differs from the entry's run instructions (worktree `bru0`, port 8000), this addendum states what actually ran.
- **Where:** branch `claude/feat066-b2-bruno-d20b0c`, cut from `feature/feat066-be-integration` at `6f10ec24` (C4, C5 and M9-B included), one commit: 95a5e7ba. The six BRU-0a files were copied from the untracked state in `.worktrees/be-integration` (that copy is untouched).
- **Run:** a new disposable database on the loopback `frc08` container, `alembic upgrade heads` exit 0, API from this worktree on 127.0.0.1:8010, Bruno CLI 4.3.0, `--env-var baseUrl=http://127.0.0.1:8010`. Positive A02: 3 of 3 checks pass. The three negative controls fail with script errors that name the loopback guard (two with "only exact loopback hostnames are allowed", one with "user-info is not allowed"). The guard is therefore verified for the CLI; the Bruno desktop and the no-database start are still NOT VERIFIED.
- **Guard rewrite (supersedes the entry's guard text):** the Bruno 4.3.0 CLI sandbox has no `URL` global, and its script preprocessor rejects a regex literal that contains slashes. `collection.bru` parses the interpolated URL by hand (2,638 bytes, SHA-256 `AD0A6A9A42A5038090725FF3E7615CCB9AA3BC070B951035E6D2774C0E9B69EE`). Decision D-066-83.
- **Request set:** requests `145` (GET teacher candidates) and `146` (POST class assignment, `If-Match` and `Idempotency-Key`) added for the C6 M9-B routes; `ROLE_GUIDE.md` corrected for C5; `004` and `005` stay as labelled stale requests. The C4 and C5 header changes were already in the tree. Decision D-066-84.
- **Full collection:** 147 requests run against the local API with the placeholder bearer value, no token and no Firebase write: 4 PASS, 0 FAIL, 95 BLOCKED-AUTH, 46 BLOCKED-ENV, 2 STALE. No real defect found. Decision D-066-85. Evidence: `evidence/notes/B2_BRUNO_FULL_COLLECTION_RUN_20261119.md` and the B2 re-run record in `evidence/notes/BRU_0A_IMPLEMENTATION_EVIDENCE_20261119.md`.
- **Review:** one independent review round (Sonnet 5.5, high effort, fresh non-forked subagent, because the review was run inside this session): ACCEPTABLE WITH NOTES, 0 P1 / 3 P2 / 6 P3. Report `B2_REVIEW_R1.md` (kept outside the repository). The three P2 items (the explanation of Bruno's counter, a stale evidence-note status, and request 126 being counted as auth-blocked while its route is not mounted) and the README heading were corrected before the commit. Remaining notes: `144` uses an undefined variable, a missing `local.bru` entry for the owner to decide; the A02 run output was not retained.
- **Not covered:** any push, PR or merge; authenticated runs (need SD-5 and tokens); BRU-0b (A17, A20, A22, A26, A27) and A08, which stay unapproved; Bruno requests for the routes listed as "no request" in the full-collection note.

## FEAT-066 Bruno follow-up after B2 — environment variable, requests for uncovered routes, authenticated-run readiness (2026-11-19)

- **Status:** APPROVED_FOR_IMPLEMENTATION by the owner (Person 2) on 2026-11-19. Nothing is implemented yet; the launch needs a separate owner word.
- **Scope (three items):**
  1. Define `platform_account_id` in `environments/local.bru` as a placeholder (request `144` uses it; it is undefined). The only other edits to that file are placeholder path variables that items 2 needs and that are missing. A scripted check lists any other undefined `{{name}}` variable; they are reported, not fixed.
  2. Add one Bruno request per route that has none: `POST /v1/parent/profiles`; `PATCH` and `DELETE /v1/parent/profiles/{profile_id}`; `DELETE /v1/story-runs/{run_id}`; `POST /v1/story-runs/{run_id}/context-confirmation` and `/script-confirmation`; `POST /api/auth/v1/registrations`; `POST /api/parent/v1/ai/drawing-understandings`, `/sketch-guides`, `/story-runs/{run_id}/story-revisions`; `POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions`, `/lesson-visuals`, `/sketch-decks`. Update `ROLE_GUIDE.md` and `requests/l5/README.md` counts and labels. Re-run the route-to-request coverage check. Run the collection once against the local API with the placeholder bearer only, excluding the registration and AI requests, and record counts by class.
  3. Write one authenticated-run readiness note, `plan/L5_AUTH_RUN_READINESS_DRAFT1_20261119.md`. It prepares the run; it does not run anything and does not decide O-BRU-AUTH.
- **Base:** local branch `claude/feat066-b2-bruno-d20b0c`, tip `3b2a3580973cdec1d78e951394a55580d74e82f3` (B2, never pushed). The work happens in a new worktree and branch created by the owner or the coordinator, because the Codex sandbox cannot write `.git`. SRS pin: 701,810 bytes, SHA-256 `443A3CA37272D2FE96127564BAF400461F394E098724A6BD999D723A4E504021`.
- **Allowlist (new or edited):**
  - in `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/`: `environments/local.bru` (item 1 and missing path placeholders only), new request files under `requests/` (new `seq` numbers after `146`), `ROLE_GUIDE.md`, `requests/l5/README.md`;
  - in `features/FEAT-066-fe-ui-srs-full-review/`: one new evidence note under `evidence/notes/` (counts and request paths only, no bodies or headers) and `plan/L5_AUTH_RUN_READINESS_DRAFT1_20261119.md`.
  - Not edited: `collection.bru`, existing requests, `approvals/TASK_APPROVAL.md`, `DECISIONS.md`, any source code.
- **Safety boundary:**
  - Requests for registrations and the six AI routes are written and checked statically only; they are never run, because they can create an identity-provider account or reach a model provider.
  - The collection run uses a new disposable database on the loopback `frc08` container, the API on 127.0.0.1:8010 and `--env-var baseUrl=http://127.0.0.1:8010`; the loopback guard stays active. No database is dropped.
  - No token is created, faked or printed; no Firebase request; no Modal call; no use of ports 5432 or 5433, of `sketch2life_m2_s1a`, or of `D:\s2l-gate-secrets`.
- **Records:** the executor writes its approval entry and decisions (from D-066-86) as drafts outside the repository; the coordinator appends them after the owner approves, with the head hash checked.
- **Review and git:** one independent review on Sonnet 5.5 at high effort, set explicitly, at most 3 rounds (D-171). One local commit, explicit paths, after the three validators and `git diff --check`. No push, no PR, no merge.
- **Not covered:** authenticated runs (need SD-5 and the O-BRU-AUTH decision), BRU-0b and A08, and any change to the loopback guard.

### FEAT-066 Bruno follow-up after B2 — completion record (2026-11-20, record of work done; owner Person 2 to accept)

- **Status:** IMPLEMENTED, REVIEWED AND COMMITTED LOCALLY; **owner acceptance pending**. This addendum approves nothing new. Nothing was pushed, no PR was opened, nothing was merged.
- **Where:** branch `feature/feat066-bruno-next`, one local commit `91b52806` (`test(bruno): complete FEAT-066 L5 follow-up`), 18 paths, then cherry-picked onto `feature/backend-srs-api-and-fe-integration` without conflicts and committed there together with this record (entry, this addendum, D-066-86 and D-066-87) as one local commit; the hash is that commit's own (see `git log`). The entry's own change to `approvals/TASK_APPROVAL.md` is not in the commit.
- **Delivered:** `platform_account_id` placeholder in `environments/local.bru`; Bruno requests `147` to `159` for the 13 routes that had none; `ROLE_GUIDE.md` and `requests/l5/README.md` updated (README carries the safe run command); the authenticated-run readiness note (prepares only; O-BRU-AUTH not decided); the run evidence note.
- **Who did what:** Codex wrote the files and ran the static checks. The coordinating review session (not Codex) ran the runtime steps because the Codex sandbox had no Docker access: a disposable database on the loopback `frc08` container, the API from the worktree on 127.0.0.1:8010, the collection with the loopback guard active, the placeholder bearer only, and requests `153` to `159` excluded. Result: 153 requests, 4 PASS, 0 FAIL, 101 BLOCKED-AUTH, 46 BLOCKED-ENV, 2 STALE; no real defect found. Every route of the running app (framework routes excluded) now has a request.
- **Parse check of `153` to `159`:** after the run, the seven excluded requests were loaded by Bruno CLI 4.3.0 in a throwaway copy with the base URL overridden to a non-loopback name; each was parsed and then stopped by the loopback guard before any send (portal-auth 1 of 1, parent-ai 3 of 3, teacher-ai 3 of 3, all guard errors). This closes the "parsing NOT VERIFIED" note for them. They have still never been sent to an API.
- **Reviews (independent, fresh non-forked subagent, read-only):** round 1 on Sonnet 5.5 at high effort: ACCEPTABLE WITH NOTES, 0 P1 / 2 P2 / 8 P3. Round 2 on Sonnet 5.5 at **medium** effort at the owner's instruction (a deviation from the high-effort rule): ACCEPTABLE WITH NOTES, 0 P1 / 0 P2 / 3 P3. All findings were fixed in the commit and the final three P3 were fixed by amending it; the amended text was not reviewed a third time. Reports are kept outside the repository (`FOLLOWUP_REVIEW_R1.md`, `FOLLOWUP_REVIEW_R2.md`).
- **Checks:** `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py` and `git diff --check` exited 0 before the amend.
- **Not covered, still open:** authenticated runs (SD-5 and O-BRU-AUTH); BRU-0b and A08; any push, PR or merge into `feature/feat066-be-integration`.
