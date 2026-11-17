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
