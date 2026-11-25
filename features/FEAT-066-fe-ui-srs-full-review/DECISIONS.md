# FEAT-066 decisions

## D-066-01 — Use Rev57 as the sole product baseline

Use FEAT-063 SRS v2.7-draft Rev57 from the root authority record for this review. The FE worktree's v2.5 authority copy is stale and does not override it. The Rev57 draft remains unsigned; report its approval status accurately.

## D-066-02 — Separate target products from references and legacy surfaces

For the current plan revision 3, audit only `apps/school-manager-ui`. Do not inspect or run `apps/mobile`, `apps/parent-ui`, or `apps/ui-mobile`; do not expand to Teacher, Platform Admin, or the additional Admin UI. The earlier revision 1 review remains historical evidence and does not broaden the current task.

## D-066-03 — Review only; remediation requires separate approval

This task records findings and evidence only. No product source, tests, build artifacts, backend, credentials, or runtime data are changed or invoked.

## D-066-04 — Keep engineering risks separate from SRS gaps

Record local port overlap, missing portal test files, and preview-only behavior as implementation/validation risks, not as product requirements inferred from the SRS.

## D-066-05 — Local visual audit uses isolated fixture previews

Start only the School Manager local Vite preview, bound to loopback, and use fixture/preview states. Do not start Parent mobile, backend or provider services, invoke external APIs, or supply credentials. If a screen cannot be reached without those dependencies, stop at source review and record the limitation.

## D-066-06 — Responsive checks are exploratory outside desktop support targets

Review the target web portals at desktop sizes required by the SRS and at a narrow viewport to find layout/accessibility defects. Report narrow-viewport issues as UX robustness findings unless the SRS explicitly makes the behavior a support requirement.

## D-066-07 — Treat preview findings as UI evidence only

The School Manager local preview uses synthetic, non-persistent state. Use it to confirm visible layout and preview interaction behavior only; do not treat preview values or toast messages as evidence of backend persistence, billing state, or production workflow completion. Report backend capabilities from source inspection and preserve any SRS policy questions as open.

## D-066-08 — Direct approval for School Manager web remediation

On 2026-11-10 the user approved plan revision 4 for School Manager web only, limited to `apps/school-manager-ui` and FEAT-066 governance/evidence in `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation` on `codex/fe-ui-web-remediation`. This supersedes D-066-03's remediation-excluded scope for this bounded task. Parent mobile and all other portals remain out of scope. The approval record includes the verified plan SHA-256 before code changes.

## D-066-09 — API-compatible work only; missing capabilities stay unavailable

Use existing versioned APIs/contracts where they support the complete required operation. Do not treat a partial endpoint as support for a broader business flow: the existing class create endpoint does not enforce SRS class capacity, assignment writes have no teacher directory/selection contract, and roster profile reads do not establish full roster lifecycle management. Billing, payments, subscription, organization quota, notification inbox and School Manager feedback-reply flows have no compatible endpoint in the checked API surface. Show unsupported actions as unavailable and record backend/API dependencies; do not create local success states or transactions. Preserve School Manager's child-media deny boundary.
## D-066-10 — Record post-implementation review against the authorized FE-only scope

The implementation uses only compatible existing FE/API behavior and visibly marks unsupported organization flows unavailable. Local preview fixture state is explicitly labeled and does not claim persistence; no class creation, quota purchase, subscription, Teacher assignment, inbox, or feedback-reply success is simulated. The after-review evidence is captured at desktop 1440x900 and narrow 390x844 in EV-004. M01 keyboard review confirmed ArrowRight moves focus/selection to the second tab and exposes its linked panel. No production/backend session was used.
## D-066-11 — Reuse the existing logout callback for School Manager

Expose a visible, keyboard-accessible logout action on authenticated M01/M02 pages and call the existing `TeacherContext.logout` callback. Do not create a second session-clear path, new auth policy, backend endpoint, or provider behavior. Treat the missing control as a user-reported FE usability follow-up, not as a newly inferred SRS requirement. Verify desktop and 390px layout plus session clearing and redirect to `/login`.
Revision 5 verification: the shared logout action passed the four local dashboard/settings × desktop/narrow interactions. Enter returned to `/login`, both existing web session keys were absent, and direct protected-route navigation stayed at login. Evidence is recorded under FEAT-066-EV-005. The optional Firebase sign-out bridge was not configured in the local preview.

## D-066-12 — Trace School Manager UI test flows to canonical SRS and actual contracts

The sequential flow guide covers the School Manager screens in SRS §21.5 and related use cases/requirements. For each flow, distinguish target behavior, current FE route/state, source-checked API support, and missing dependencies. Treat local fixtures as visual/interaction evidence only, retain open SRS policy questions, and do not infer requirements from §32 or simulate unavailable backend operations. See FEAT-066-EV-006.

## D-066-13 — Keep the second-pass verification School Manager-only

The user's request to double-check before switching portals applies to the approved School Manager implementation scope and FEAT-066 evidence. Reuse only local fixture preview and source/contract inspection; do not touch Parent, Teacher, Admin, or backend code. Record live-preview findings separately from API capability. See EV-007.

## D-066-14 — Do not canonize an SRS-unstated M01 rubric

FR-PL-05 requires School Manager approval before a Teacher lesson becomes PUBLIC but does not define four pedagogical checks. Preserve the current UI behavior for this review and record the rubric as an owner clarification; do not present it as an SRS rule or change the gate by inference.
## D-066-15 — Use exactly the three SRS web portal roles

SRS §3 defines Teacher, School Manager, and Platform Admin for the web portals; current auth API role values are teacher, school_manager, and platform_admin. Content review is a Platform Admin permission. Parent is a separate Android-targeted client and is excluded from this task. Do not add another role or link the additional apps/admin-ui surface.

## D-066-16 — Treat the screen recording as visual reference

Adapt its warm editorial composition and restrained product-visual language for the login surface. Ignore any copy or instructions shown in the recording. Use a school/learning-related local Three.js scene rather than the unrelated depicted object. Keep the form functional when WebGL is unavailable or motion is reduced.

## D-066-17 — Keep portal entry URLs explicit

Local development portal links use only the verified loopback ports 5172 (Teacher), 5173 (School Manager), and 5174 (Platform Admin). The SRS gives no deployment hostnames. Production links must be explicitly configured; an unset destination is presented as unavailable instead of guessed.

## D-066-18 — Preserve authentication semantics

Use the shared login component and existing auth service. Keep the role values, backend role confirmation, error handling, preview-mode notice, and role-specific landing paths. Role links navigate to each separate app’s existing /login route. Do not fabricate login success, role access, or session policy.

## D-066-19 — Keep Three.js local and bounded

Three.js is approved only as a local dependency for the decorative login scene. Do not load models, textures, code, or fonts from a remote runtime source. Cap pixel ratio and render workload, honor reduced motion and page visibility, provide a non-WebGL fallback, and dispose of scene resources on unmount. If local dependency resolution cannot be achieved in scope, record a blocker instead of using a CDN.
## D-066-20 — Pin the requested local Three.js dependency

No Three.js runtime or matching types were installed locally, and local pnpm/npm caches were empty. Following the approved plan, pin Three.js 0.187.0 plus @types/three 0.187.0 in the three in-scope web app manifests and their npm lockfiles. Import it through each app’s local module resolution so the scene is bundled; never use a runtime CDN or remote asset. This dependency setup was completed before shared login source edits.
## D-066-21 — Record login UI evidence without claiming authentication

EV-008 covers local preview rendering, links, keyboard focus/activation, reduced-motion state, and WebGL fallback for all three web portals at desktop and narrow viewports. No credentials or backend are exercised. Keep the real auth limitations explicit: existing assignment/Firebase dependencies for Teacher and School Manager, missing Platform Admin role discovery, and unspecified production hostnames.
## D-066-22 — Revision 8 is School Manager-only and approved directly

The user's direct request on 2026-11-10 authorizes a fresh SRS v2.7-draft Rev57 flow audit and a school-themed refresh of authenticated School Manager web screens. Plan revision 8 SHA-256 `C71F0824DC4A7E4901912BB2D8883B954BA6F2ED438BAB9F9C0871CBE3B54D7C` is matched in the feature-local approval ledger before product-code edits. No root checkout or other worktree is in scope.

## D-066-23 — Missing APIs stay visibly unavailable

Treat class capacity/lifecycle, Teacher provisioning/selection/transfer, billing/invoice/payment/subscription, organization quota/top-up, notification inbox and school feedback reply as blocked until compatible API/contracts exist. Do not use fixture data or success feedback to imply a transaction. Preserve the SRS privacy boundary and unresolved pricing/policy questions.

## D-066-24 — Scope the school theme to the authenticated Manager app

Use a warm paper/chalk, forest/leaf, muted marigold/clay palette with restrained surface treatment. Keep the design professional for adult school staff. Scope tokens/styles to the local Manager shell; do not modify shared login styling, shared/global tokens, other portals or add external/generated imagery.

## D-066-25 — Do not copy files from the root checkout

The reviewed recursive FEAT-066 inventories showed no file path present only in root and missing from the authorized worktree. The root subset is stale/different on some matching paths; preserve it and do not overwrite the newer active worktree records.

## D-066-26 — Keep the school theme local to authenticated School Manager

Load the local manager stylesheet after shared styles so scoped selectors win without editing shared/global styles. Keep the school-office palette and responsive shell in apps/school-manager-ui only; do not restyle the shared login or add images, packages or business behavior. Revision 8 visual review is recorded as EV-010.

## D-066-27 — Report flow completeness from contracts, not preview appearance

EV-009/EV-010 establish that the current School Manager UI is incomplete against SRS §21.5. Keep fixture metrics labeled and API-blocked actions unavailable. Read-only class/roster and M01 grant review have relevant contracts; capacity-safe class lifecycle, Manager Teacher lifecycle, billing, organization quota/top-up, inbox and school feedback reply do not. No backend or policy assumptions are introduced.

## D-066-28 — Treat the cobalt palette as a dashboard-only experiment

The user directly requested a visual preview on the default M02 dashboard. Scope the route marker and palette tokens to that route only; keep M01 and M02 teachers/classes/quota/settings on revision 8 styling. Do not treat the preview as a permanent system decision or SRS requirement.

## D-066-29 — Use the skill's first software/saas palette result

The design-taste-frontend palette-deal returned cool-grey-cobalt first. Use its generated #EEF0F3 background, #E2E5EA surface, #0B0C0E ink, #5D6470 muted text and #1F2DE6 action with white text. The logo's blue is compatible. Preserve existing semantic status colors and information; do not invent business behavior.

## D-066-30 — Keep the palette experiment limited to the default dashboard

EV-011 records the generated Cool Grey + Cobalt palette on /m02-organization-management only. The preview is an experiment for owner review, not an SRS-derived or permanent product decision. M02 subsections and M01 retain the earlier colors; status semantics and application behavior stay intact.

## D-066-31 — Apply the supplied brand art and bright cobalt palette across browser UIs

The direct user request authorizes the attached image as the web logo and the approved Cool Grey + Cobalt direction across the five existing browser app packages and their shared styles. Parent Android and all native apps remain excluded. The parent-ui and admin-ui sources are styled only as existing browser UIs; this does not establish new product roles or flows. Keep status semantics, behavior and privacy intact.

## D-066-32 — Supersede dashboard-only palette preview with direct cross-web adoption

The user's revision 10 request authorizes the supplied artwork and Cool Grey + Cobalt across all five existing browser apps and shared web styles. This supersedes the dashboard-only limit in D-066-28/D-066-30. Keep the palette recorded as a visual decision, not an SRS requirement, and preserve semantic status colors and all existing behavior/privacy boundaries.

## D-066-33 — Keep visual validation offline and report unavailable previews

Reuse only loopback servers from the authorized worktree. If an included app cannot run because a package is missing, use the local cache with manifest/lockfile writes disabled. If the package is unavailable offline, do not reach the registry or use an unrelated checkout; document the limitation and leave its source implementation reviewable.
## D-066-34 — Share a local icon family across the three SRS web roles

Use one local inline-SVG icon family for the authenticated School Manager, Teacher, and Platform Admin dashboard shells and content icons. Keep symbols recognizable, with consistent rounded strokes and restrained duotone fills that use the existing Cool Grey + Cobalt palette. Avoid external icon providers, font downloads, and new packages. Preserve all labels, routes, actions, access checks, and accessibility names. This is a visual choice, not an SRS requirement.

## D-066-35 — Use the shared Vietnamese-capable sans-serif stack for login headlines

The direct font-fix request authorizes a bounded typography correction in apps/shared/portal-login.css. Login headlines inherit the existing Be Vietnam Pro, Segoe UI, and system sans-serif stack; the accent span stays upright and uses the same weight/tracking, with enough line height to keep Vietnamese marks clear. This is a visual/accessibility-quality correction, not an SRS requirement. Preserve the shared page layout, role copy, routes and auth behavior; do not add font downloads or dependencies.
## D-066-36 — Keep logout visible beside each role's account identity

The direct user request authorizes one logout control in each SRS web-role shell. Keep the action beside the profile at the bottom of the sidebar, where it remains visible on narrow screens. Reuse the existing logout handler and route guard. The Teacher control moves from its top bar to the sidebar; School Manager keeps its existing sidebar control; Platform Admin receives the missing control. Narrow collapsed sidebars retain a labeled-in-accessibility icon button. Do not add auth policy, backend behavior, or new routes.
## D-066-37 — Keep the three-role review read-only

The direct user request authorizes an audit/listing for Teacher, School Manager and Platform Admin only and defers UX/product fixes. Use only FEAT-063 v2.7-draft Rev57 §§1–31 as current requirements; treat feature-local notes as implementation evidence and §32 as as-built evidence. Do not infer product policy from fixture data or resolve SRS OPEN items during review.

## D-066-38 — Separate UI defects from API/backend and owner blockers

For FEAT-066-EV-016, classify product flows as blocked when the current UI/API adapter cannot complete them; record the missing/partial contract as a dependency, not as a completed mock action. Preserve unavailable states, privacy boundaries and open commercial/eligibility decisions. Do not modify application source until the user selects a remediation scope.

## D-066-39 — Remediate audit findings only at existing API boundaries

The user's 2026-11-11 follow-up authorizes FE-only implementation from EV-016 across the three SRS web roles. A flow may be wired only when the existing contract supports its auth, tenant, version and state requirements. Otherwise the UI must clearly report unavailability, remove local-only success signals, and record the missing API dependency. Do not change backend/contracts, invent product policy, broaden child-data access, or treat fixtures/§32 as target requirements.

## D-066-40 — Keep three-role remediation at verified API boundaries

For EV-016 remediation, use only product APIs whose current contract supports the necessary role, organization, version, and state semantics. Preserve a stable idempotency key across retries when the API accepts one. Recover Teacher uploads only from the existing status endpoint; reselect and hash-check the source file, and keep file bytes, filenames, tokens, and child data out of session storage. If a grant version cannot be fetched exactly, or a flow has no product API, disable the operation and state the dependency. Local previews must not imply a backend success. Keep the four M01 approval criteria and Admin/operator permission split open pending owner decision; do not infer pricing or policy.

## D-066-41 — Apply the paper-and-crayon direction to shared auth and Teacher only

For the user-approved Rev16 preview, use warm paper #FFF9F0/#F2EBDD, graphite #25241F/#57574F and primary blue #245B9B; use red, orange, yellow, green, teal and brown sparingly for semantic accents. Yellow labels use graphite text. This is a visual direction from the user's palette research/concept, not an SRS requirement. Apply login styles to the shared Teacher/School Manager/Platform Admin /login pages because they consume one component; authenticated palette changes stay in apps/teacher-ui. Preserve role/auth behavior, local fixture labels, keyboard/accessibility semantics, no-default child media, and the unavailable Sketch Deck state. Keep its eventual projection surface white and 16:9 per NFR-33; do not fabricate it in the current FE-only preview.
## D-066-42 — Use a child-friendly shared icon treatment across the three web roles

For the user's Rev17 visual request, retain the local shared SVG glyph set and semantic mappings while applying rounded strokes, visible but restrained crayon-color echoes, soft glyph tint, and gently rounded icon badges. Keep foreground strokes controlled by currentColor so active and primary controls retain their existing contrast. This is visual styling only; do not change SRS roles, route/action meaning, accessibility names, package dependencies, or app layout.

## D-066-43 — Use one shared notification bell and full-color nav glyphs

For Rev18, use familiar full-color system emoji glyphs for the three role sidebars and the adjacent role/account controls. Use the same bell glyph for Teacher notifications, the School Manager unavailable inbox, and Platform Admin notifications. Keep unread counts, unavailable labels, status dots, routes and accessible names as currently implemented. Preserve the functional chevron as a directional icon and keep page-content icons on the Rev17 SVG system.

## D-066-44 — Use monochrome outline glyphs in role navigation

For Rev19, use the existing local SVG path set as single-color line icons in the Teacher, School Manager and Platform Admin navigation and notification/inbox controls. Use currentColor for the existing control foreground, rounded caps/joins, and the same bell outline across roles. Keep unread indicators, unavailable state, accessible names, layout, routes and actions unchanged. This is a visual correction to the Rev18 emoji preview; do not alter non-shell page-content icons.

## D-066-45 — Treat Rev20 as a Teacher UI diagnosis only

Rev20 covers one SRS-to-route/API diagnosis and a proposed Teacher-first information architecture. It does not authorize app-source changes. Keep the proposed task model flow-oriented: dashboard, assigned classes/profiles, reusable lessons, guided occurrence, and history; fold optional Sketch Deck and video steps into the occurrence. Remove any Teacher-facing Manager handoff mutation. Until product contracts exist, present extraction confirmation, profile creation, occurrence/run, sketch generation, playback/projection, history, inbox and quota as explicitly unavailable. Await the user's acceptance before implementation and create a matching approved plan first.

## D-066-46 — Match monochrome crayon navbar glyphs to each role function

For Rev21, use a dedicated friendly outline glyph mapping for the Teacher, School Manager and Platform Admin navigation. Each glyph must describe the visible destination/action, use one currentColor stroke with rounded organic geometry, and contain no emoji or colored fill. Keep one bell outline for all notifications. Preserve labels, routes, role checks, actions, hit areas, and page-content icon styling. This authorizes the icon correction only; the Teacher layout proposal in Rev20 remains pending user review.

## D-066-47 — Complete Rev21 semantic outline navbar icon preview

Rev21 is implemented in the three role shells with action-matched glyphs rendered as one-color currentColor outlines using rounded, crayon-friendly geometry. Preserve icon-badge state styling and all page-content icon treatment. All nine local preview screenshots were visually reviewed with no horizontal overflow, Vite error, or browser runtime exception. Leave the worktree uncommitted for user review; the Rev20 Teacher layout proposal still requires user acceptance before any implementation.

## D-066-48 — Use a toothed cog for navbar settings

The previous settings outline had radial spokes and looked like a sun at small size. For Rev22, use a toothed cog silhouette for the Teacher and School Manager settings navigation items, including the Manager role shell rendered by Teacher UI. Retain the old settings symbol for non-navigation uses to preserve the existing approved page-content visual scope.

## D-066-49 — Design the complete crayon web UI before implementation

For Rev23, deliver a reviewable design system and screen/flow atlas for shared web Auth and the three SRS product roles: Teacher, School Manager and Platform Admin. Keep Content Admin as permission, not a role; exclude Parent/mobile. Use the user-approved warm paper/graphite/school-blue direction and monochrome outline navbar glyphs. Separate SRS target requirements from current API support; mark unavailable flows and leave open policy/pricing decisions unresolved. Keep generated visuals in assets/generated pending acceptance; do not change application source in Rev23.
## D-066-50 — Keep the Rev23 crayon UI as a design-only review artifact

The four Rev23 boards and the SRS flow atlas are ready for user review. Treat the boards as representative visual concepts and the atlas as the authoritative flow/API map. Keep all generated files in assets/generated/rev23; do not promote them to approved/applied assets or implement application code until the user accepts the visual direction. The unsigned SRS and OI-17 remain open. Unsupported APIs stay unavailable; do not infer prices, policies, consent settings or operational data.
## D-066-51 — Implement the accepted Rev23 web concept in ordered sections

The user's Rev24 instruction changes the Rev23 design-only boundary: Auth and the three web roles may now be rebuilt using the accepted crayon boards. Apply the same system with role-specific tasks, preserving supported behavior and SRS access boundaries. Implement and manually review one section at a time (Auth, Teacher, School Manager, Platform Admin), recording SRS/API findings before continuing. Unavailable APIs and owner-open rules remain unavailable/open. Keep Parent/mobile, backend, tests/builds and commit/push out of scope.

## D-066-52 — Close Auth only after role-isolation review

The Auth section is complete only after all three role links and narrow layouts are captured, and each wrong-role route is checked to show the shared mismatch page, logout action, and no foreign portal shell. Keep local sign-in labeled as non-persistent preview; Platform Admin role discovery remains unavailable until its server contract exists.

## D-066-53 — Keep Teacher UI data-backed and class-scoped

For Rev24 Teacher, show only real API results after Firebase session and organization assignment are available. Match class list/detail to active class-scoped Teacher assignments before showing class/roster data. The local design preview has no sample rows, fake quota/unread values or synthetic success. Keep lesson/import operations limited to existing APIs and label extraction confirmation, occurrence/story/video/projection, quota/history/inbox/feedback/profile/settings as unavailable until their contracts exist.

## D-066-54 — Keep School Manager API evidence separate from SRS target flows

For Rev24 School Manager, expose class and roster reads only after an active `school_admin` assignment is verified. Do not use create-class/create-assignment primitives as proof of capacity-safe lifecycle or provisioning workflows. M01 decisions require exact grant/current immutable-version equality and structured content. Count only pending items returned for the visible page; show Approved and Changes requested separately, but do not synthesize either historical total without an API aggregate. Billing, subscription, capacity/quota, inbox, feedback, and settings remain explicitly unavailable where their contracts are absent. Never render sample school/child names, prices, payment status, quota totals, or unread state in local preview.

## D-066-55 — Keep Platform Admin preview separate from administrator authorization

For Rev24 Platform Admin, the local role flag is visual preview only. Do not infer or grant server role/capability from the route. The existing moderation command cannot be used without a scoped queue and exact immutable-version read. Limit optional health checks to an authenticated bridge and loopback API base; do not call external/production services from preview. Keep catalog, org/permission context, queue/job, billing reconciliation, quota policy, lifecycle, audit, inbox, and feedback unavailable until their versioned scoped contracts exist. Content Admin remains a permission within Platform Admin, never a separate role.

## D-066-56 — Preserve the role frame and simplify overview dashboards

For the Rev25 visual pass, keep the accepted role shell and route structure. Match each role's overview to its Rev23 board with fewer content layers and shorter copy: Teacher's three work areas, School Manager's organization/service status, and Platform Admin's four operational status cards. The persistent shell preview label is sufficient; do not repeat the same preview banner in dashboard content. Remove dashboard shortcuts duplicated by the sidebar. Preserve API-truthful status, SRS permissions/privacy and all existing unavailable dependencies.

### D-066-56 outcome — Rev25 overview alignment

The overview pass is complete. Teacher's existing three-area workbench already matched the board after the prior cleanup, so this pass kept its source unchanged. School Manager uses organization status plus service availability; Platform Admin uses four operational status cards. The shell, navigation appearance, routes and logout were preserved. Missing API flows remain unavailable and are recorded without sample values or success claims. A separate same-path `aria-current` issue was found in Manager/Admin navigation and left for a focused accessibility correction outside this dashboard-only scope.

## D-066-57 — Use a restrained paper/crayon canvas behind the three web roles

For Rev26, carry the Rev23 paper surface and sparse corner crayon strokes into the content canvas behind Teacher, School Manager and Platform Admin. Preserve the accepted shell, cards, text and product interactions; the background is decorative and must not obscure or signal product state. Use CSS-native local styling without remote assets or new dependencies. Keep Auth and Parent/mobile out of scope.

### D-066-57 outcome — Rev26 paper/crayon background

The same CSS-native paper texture and sparse corner strokes are applied behind Teacher, School Manager and Platform Admin content canvases. Manual desktop/narrow visual review of all three overviews and one representative route per role passed: the background fills the visible canvas, marks stay behind content, and no overflow or browser/runtime errors were observed. Existing preview/API-unavailable states are unchanged. Evidence is in EV-032. The pass remains uncommitted pending user review.

## D-066-58 — Rebuild auth presentation without changing identity flow

For Rev27, use the brainstormed crayon learning-studio layout: keep one role-specific `/login` page per web app, make the login form the clear primary action, and retain simple links for Teacher, School Manager and Platform Admin. Reuse the existing sign-in/role-resolution adapter, URLs, preview state and mismatch handling. Reuse the existing school-model Three.js scene with an immediate SVG fallback; no new dependency, remote asset, real data or provider call. Do not add account recovery, organization selection or help flows without a SRS/API contract. The brainstorm is recorded in `evidence/notes/AUTH_UI_REDESIGN_BRAINSTORM_REV27_20261111.md`. Plan hash `C9EF609A920F3C53F0153ED109660B85003D4D03A8E1E76C2F46C3EB2EEF21C2` was approved before implementation.

### D-066-58 outcome — Rev27 shared web auth

Implemented the approved split login composition for Teacher, School Manager and Platform Admin. Kept role routing and auth behavior intact, added a keyboard skip link and mobile tap-target adjustment, and verified WebGL failure fallback in a local browser. All role/viewport captures and observations are in EV-033. The full design-taste gate ended OPEN 22 after three rounds. A final manual capture then exposed and fixed a role-specific fallback-opacity issue; the 12 screenshots and forced shader failure check were rerun, but no fourth full gate round was run. Remaining gate findings are listed and classified in the completion evidence rather than waived or forced into a marketing-site structure. No tests/builds, backend/API calls, real data, commit or push.
## D-066-59 — Keep the Rev68 task SRS trace separate from the repository source register

For this user-authorized Rev28 task, use the owner's explicitly selected unsigned Rev68 file as the screen/flow baseline and trace each role surface to the available API contracts. Record the project authority pointer's unsigned Rev60 hash as an unresolved source-register mismatch. Do not rewrite the SRS authority record or imply either draft is signed. Preserve role-scoped backend authorization, the Manager preview/BE1 distinction, and the Platform Admin child-data deny-by-default boundary. Unavailable operations remain visible as unavailable until their scoped contracts exist.

## D-066-60 — Use one role entry and remove local preview sign-in

For Rev29, /login is the role-selection entry; legacy /teacher/login resolves there, and role cards open real role sign-in routes. Remove the local preview authentication bypass, School Manager fixture-preview app and user-facing preview navigation. Redirect retired preview URLs to /login for predictable recovery. Keep the BE1 Manager authorization path and existing Teacher/Firebase role-resolution adapter; a route or local flag must never grant a role. Keep Platform Admin role discovery visibly unavailable until its backend contract exists. This revises the Rev28 Manager preview distinction without changing the selected Rev68 task baseline or API contracts.

### D-066-60 outcome — Rev29 login flow

Implemented and visually verified at desktop and 390px mobile sizes. The role destinations, redirects, form fields, focus rings, lack of preview copy, and no-external-request result are documented in EV-035. No credentials or product API were used. Platform Admin role/capability discovery remains an explicit backend limitation.

## D-066-61 — Keep all web roles in one login screen

For Rev30, /login is the direct shared sign-in screen, with Teacher selected by default. Teacher, School Manager, and Platform Admin controls change the role panel in place; they do not route to separate login designs. Compatibility paths resolve to the matching role state on /login. Keep the real role-specific identity/authorization adapters: Teacher backend assignment resolution, School Manager BE1 authentication plus school_admin assignment verification, and Platform Admin's fail-closed missing capability-discovery state. A selected UI tab never grants a role. This decision follows FEAT-063 v2.7-draft FR-C-01 and does not alter API or authorization contracts.

### D-066-61 outcome — Rev30

Implemented and inspected in the local browser at desktop and mobile sizes. Role switching stays at /login, including keyboard activation and focus retention. The evidence and current backend limitation are recorded in EV-036.

## D-066-62 — Use canonical Rev60 for the Teacher-first plan

For the Rev31 planning request, follow docs/context/SRS_AUTHORITY.md and the FEAT-063 v2.7-draft Rev60 working SRS. Preserve FEAT-066 revisions 28–30 and their Rev68 task record as history; do not rewrite or merge their requirement baselines. This is an authority and planning disposition, not a new product-policy decision. Keep Q-01, Q-13, Q193 and OI-17 open. The Teacher API/UI crosswalk and implementation dependencies are recorded in PLAN_REV31_TEACHER_API_UI_REBUILD_20261116.md and FEAT-066-EV-037. No implementation approval is granted by this decision record.
## D-066-63 — Use the configured API for the Platform Admin health probe

For FEAT-066 Rev32, the Admin overview health card uses the existing typed GET /health against the runtime-configured API base, after the authenticated Platform Admin route is entered. The UI identifies the result only as an API health probe, keeps connection/error/retry states explicit, and does not infer queue, billing, database, provider or full-platform health. Existing auth/account API wiring stays unchanged. This frontend disposition does not settle Q-13 or authorize Content Admin operations; lesson moderation remains blocked until its queue/detail and permission contracts are available.
## D-066-64 — Use a loopback FE proxy for the local API handoff

The backend health route does not emit CORS headers for the Vite origin. Preserve the existing FE server on port 5173 and run a second temporary Vite server on loopback port 5174 with same-origin `/health` and `/api` proxies to the container API. Keep this runtime workaround under ignored `tmp/`; do not add a backend CORS or FE source change as part of the handoff. Authenticated account reads remain unverified without a valid configured identity.
## D-066-65 — Keep the Admin test identity in Firebase dev only

For the owner's Admin FE test, use one local QA identity in the verified `sketch2life-dev` project and the local Docker PostgreSQL database. Create it through the supported Platform Admin bootstrap, keep its email unverified on reserved `example.com`, and set a generated password without email delivery. Never store the password or bearer token in repository files/logs. This identity does not grant Content Admin or child-media access and is not a product seed account.
## D-066-66 — Proxy the active FE port for API testing

After the owner reported the backend-data error on the active port, make the same-origin proxy available at port 5173 as well as 5174. Configure only the local Vite process and ignored `tmp/` config; do not add API CORS or alter tracked FE/backend code as part of this runtime fix. Keep both dev servers available.

## D-066-67 — Keep Platform Accounts inside existing API and role boundaries

For FEAT-066 Rev36, preserve Firebase/backend authentication and the existing account GET/POST/PATCH contracts. Represent loading, failure and successful data as distinct UI states so an API error cannot look like an empty result. Show only the four product roles; Content Admin is a scoped permission, not a role, and no child-media access is inferred. Set page size to the supplied SRS default 25 while preserving offset pagination until the backend provides the required opaque cursor contract. Capability grants and visible audit-event browsing remain unavailable because their contracts are not exposed by the current typed API. Follow the owner attachment Rev69 for this task; leave repo SRS authority Rev60 unchanged.

## D-066-68 — Keep Platform Admin sidebar styling portal-scoped

For Rev37, preserve the shared WebAppShell behavior and navigation contract. Apply presentation changes only to sidebar descendants under html[data-portal="platform"] in the existing Platform Admin stylesheet, using shared crayon tokens for paper, ink, focus and status states. Keep active route, waiting labels, auth/session actions, focus handling, responsive drawer, scrollable nav, and footer mechanics intact. This visual decision does not alter SRS requirements or authorization policy.

## D-066-69 — Adapt Platform Accounts to available content width

For Rev38, use a fixed-column table through 1120px, with a reserved stacked action column so role/state/revision content cannot push actions over a neighboring cell. At 900px and below, render the existing labelled account cards; this accounts for the persistent 238px navigation rail at tablet widths and the reduced CSS viewport under browser zoom. Show the action heading when the desktop table is visible. Preserve all account data/API/authorization behavior. Report that the populated action row was not browser-captured if no Firebase session is available; never fabricate rows or transfer session tokens for visual evidence.
## D-066-70 — Prepare School Manager after Admin API closeout (Rev39 planning)

For Rev39 planning, treat account GET/POST/PATCH and the shared health probe as the currently integrated Admin APIs. Keep platform moderation unavailable until the backend provides a queue/list, an exact immutable-version read and authorization for the SRS Content Admin permission. Prepare the next UI review around School Manager's existing tenant-scoped public-grant review and class list/create flows. Do not expose class-assignment pickers without a scoped Teacher candidate read; do not invent quota, billing or organization feedback behavior while APIs/owner decisions are absent. This records task sequencing for FEAT-066 and grants no implementation approval.

## D-066-71 — Reuse shared authentication for School Manager (Rev40 planning)

Do not create or assume a Manager-specific BE login route. Reuse Firebase SDK sign-in, shared `GET /api/auth/v1/me` for account-role resolution, and organization-scoped BE1 assignment checks for school access. Treat product role `school_manager` and organization assignment role `school_admin` as separate contract values; do not grant organization access from account role alone. This records the integration plan and does not authorize source changes.

## D-066-72 — Reuse shared role resolution for Manager login (Rev41)

The shared sign-in pipeline is the Manager auth integration: Firebase SDK sign-in, authenticated `GET /api/auth/v1/me` role check, then organization-scoped BE1 assignment check before portal session/navigation. Do not add a Manager-specific login route or duplicate account-role API call. Keep the protected Manager shell's organization-wide assignment check as defense in depth. Test the accepted and denied paths without real credentials; record live authenticated verification separately from mocked coverage.

Rev41 implementation found that `apps/web/.env.example` documents `VITE_BE1_BASE_URL` and `VITE_BE1_ORGANIZATION_ID`, but the shared API runtime did not read them. Preserve explicit injected config first, then generic `VITE_SKETCH2LIFE_*` values, then the documented BE1 fallbacks. Cover the resolver with a pure configuration test and keep the mocked login flow separately focused on endpoint order, bearer forwarding and role/assignment gating.

## D-066-73 — Isolate Manager QA account provisioning (Rev42)

Use only the nonproduction `sketch2life-dev` project. Create one reserved-domain QA identity and one dedicated organization after a matching Firebase Web config is available; establish the first organization-wide `school_admin` assignment through the supported first-school-admin bootstrap flow. Never alter the existing Platform Admin, send email, use child data, or store the generated password/ID token in repo evidence. If the config is absent, stop before creating a Firebase identity.

## D-066-74 — Gate Manager business API work on live login (Rev43)

Begin Plan Rev43 only after Rev42 verifies a live Firebase sign-in plus `/api/auth/v1/me` role and BE1 organization assignment. Connect only organization read, minimal roster read, consent-status read and Parent-group list/create; preserve the six existing calls and server-side tenant authorization. Keep synthetic Teacher-only profile creation, ambiguous Manager consent writes, Parent invitation without candidate discovery, membership revoke without membership read, class assignment without Teacher discovery, and class creation without backend capacity enforcement unavailable. Do not create live class, child, consent, Parent-group or membership rows for tests.

## D-066-75 — Flush bootstrap parent rows before assignment (Rev44)

The first-school-admin bootstrap must flush the organization and adult identity rows in the same transaction before inserting their organization assignment. This makes foreign-key ordering explicit while retaining transaction atomicity; a later assignment failure still rolls back all three records.

## D-066-76 — Align School Manager navigation with SRS scope and route contracts (Rev46)

Group the School Manager navigation by organization operations, learning-content review/feedback, school resources and notifications. Keep only verified FE/backend routes active; link unsupported SRS responsibilities to explanations that name missing contracts. Roster and consent remain minimal and read-only. Keep the Manager identity control static until a real profile/settings route exists. Preserve school-preview styles while also matching the live school-be1 portal key.

## D-066-77 — Organize shared web files by responsibility (Rev47 proposal)

Propose moving the shared root files into api, auth, components, navigation and styles, while preserving assets. Rewrite only import paths required by the moves; do not change runtime behavior or unrelated dirty content. Because the move changes shared paths across 27 source files, implementation requires explicit approval of the Rev47 plan. This decision is a proposal, not approval.

## D-066-78 — Complete approved shared-folder organization (Rev47)

Apply the owner-approved Rev47 folder boundaries under apps/web/src/shared: api, auth, components, navigation and styles; preserve assets. Keep the move path-only and preserve unrelated dirty content. Record the completed import map and build result in EV-053; no application test suite, commit or push.

## Rev48 — Preserve six Manager route guards pending contract decisions — 2026-11-17

Keep profile creation, consent writes/revocation, Parent invitations, membership removal, and Teacher assignment unavailable in the Manager UI until their actor, discovery, membership revision, or candidate-read contracts are approved. Keep class creation disabled until BE1 enforces capacity under SRS FR-T-03. Do not treat omissions from the public OpenAPI projection as proof that mounted Lesson Library routes are absent; the full app-composition contract confirms all 17 Manager method/path pairs.

## Rev49 — Keep QA credentials only in ignored tmp — 2026-11-17

At the owner's direct request, keep the current Admin and Manager QA email/password pair only in tmp/qa-test-accounts.local.md, which the repository ignores. Do not copy the values to evidence, source, .env, commit, or push. Preserve the two existing QA identities and the Manager organization assignment.

## Rev50 — Keep class creation fail-closed; separate API error from empty data

Do not enable Manager class creation before BE1 enforces the SRS capacity rule. Future page work should render the empty state only after a successful empty response and keep it hidden on API failure. This review records the issue; it does not implement a UI change.

## Rev51 — Commit pending handoff without rewriting prior history

Include all current non-ignored worktree changes in one fast-forward commit. Keep the already-pushed Rev48 record commit intact. Exclude .env, ignored tmp credentials, provider keys/tokens and external references. This supersedes earlier no-commit/push boundaries only for the currently pending worktree content.

## D-066-62 — Close Manager API MGR-1 policy boundaries (2026-11-17)

At the owner's direct instruction on 2026-11-17, close these three MGR-1 policy choices:

- **Manager-to-Parent group discovery/invitation:** Do not enable this flow in the current Manager API closure. Keep discovery and invitation unavailable until a separately approved, tenant-scoped recipient-discovery and invitation contract defines the verified Parent reference, minimum visible fields, authority, acceptance, expiry, revocation, and audit behavior. Do not infer recipient identity from a name or accept guessed principal references.
- **Staff-created consent:** A School Manager or Teacher must not create or revoke effective Parent consent on the Parent's behalf. Parent remains the actor for Parent-profile sharing consent and grants. A staff-origin `pending` record is not effective Parent consent. Any distinct school-managed consent workflow remains out of scope/open until separately defined and approved.
- **Teacher assignment candidates:** Only a verified Teacher principal belonging to the same organization is eligible for assignment. BE1 remains authoritative for organization, role, and current assignment facts; the server must validate eligibility and scope at command time. The candidate-read path and minimum response fields remain contract work; do not guess identities.

These decisions close MGR-1 policy disposition only. They do not authorize API, persistence, UI, or schema implementation and do not modify the unsigned SRS or official task approval.

## D-066-63 — Set the MGR-2 class-capacity contract direction (2026-11-17)

For MGR-2 contract planning only, use the owner-selected unsigned SRS input recorded in the MGR-2 plan (SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`). Its header describes updates through Rev69 while its revision history ends at Rev68; keep that provenance discrepancy OPEN / NOT VERIFIED. The repository SRS authority remains the in-repository Rev60 pointer. This decision does not sign, replace, or modify either SRS or the authority record.

- **Capacity owner and admission direction:** Billing owns the effective organization capacity and its effective-time suspension set. BE1 must obtain a versioned, concurrency-safe admission result before creating a class. A read-only capacity snapshot followed by an independent insert is insufficient to establish the SRS no-over-capacity invariant. Do not read Billing-owned storage directly or assume a cross-module transaction. The Billing owner must define the exact receipt/reservation, expiry, recovery, and persistence contract before MGR-7.
- **Fail closed:** Do not create a class when current effective capacity cannot be verified. Preserve the SRS outcomes `201` and `409 CLASS_CAPACITY_REACHED` where applicable. The public status, code, and retry mapping for Billing unavailable, stale, or indeterminate outcomes remains OPEN; `503 CAPACITY_UNAVAILABLE` is not selected by this decision.
- **Subscription and suspension behavior:** Permit creation during the SRS seven-day `GRACE` period only when effective capacity is verified. Block new class creation in `RESTRICTED`. Apply Billing-selected suspensions at their effective time through a versioned, idempotent BE1 projection; suspended classes remain readable and read-only, with class and roster history preserved.
- **Idempotency and correlation:** Class creation is a state-changing command and must meet the selected SRS requirements: key scope by principal/operation/target, replay the original result for the same key and payload, and return HTTP 400 `INVALID_IDEMPOTENCY_KEY` for same-key/different-payload reuse. `X-Request-ID` is correlation only. The literal idempotency header name, format/length, receipt shape, and retention remain OPEN for the reviewed API contract.
- **Scope and paths:** Apply the SRS §9.8 distinction: uniform `404` for nonexistent or out-of-scope resources, and `403` only for a known in-scope action denial. Reconcile the current BE1 source behavior in the implementation plan. The mapping between the SRS shorthand path and the existing `/api/be1/v1/...` route, generated OpenAPI output, and runtime behavior remain unverified/open; this decision does not alter routes.

This is an owner-directed planning disposition following the MGR-2 independent review. It does not approve the MGR-2 draft for implementation, authorize tests/runtime, change the official task approval, or launch work. MGR-7 still requires reviewed contracts, exact allowlists, and separate owner approval. MGR-3 contract planning may proceed under the roadmap without source changes; any dependency or owner conflict must remain explicit.

## D-066-64 — Use the D-209 SRS copy for all FEAT-066 work (2026-11-18)

**Owner selection:** "Bản 701,157 B theo D-209", confirmed for recording with "Duyệt" on 2026-11-18.

FEAT-066 uses one SRS for every lane and plan: the owner-supplied working SRS adopted by FEAT-063 D-209. It is 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`, unsigned v2.7-draft.

This supersedes, for FEAT-066 work only:
- the D-066-63 sentence "The repository SRS authority remains the in-repository Rev60 pointer", together with its scoping of the copy to MGR-2 planning;
- the SRS bullet of `evidence/notes/MGR_1_OWNER_DISPOSITION_20261117.md`;
- the authority statements in the MGR-2 and MGR-3 plans that keep the copy out of authority.

Earlier plans that cite Rev60 line numbers are re-mapped to the adopted copy in each slice's approval package.

The worktree's in-repository `SRS_AUTHORITY.md` and SRS file still point to Rev60 on `dev`. They change when the M2 branch reaches `dev` or by a separate pointer update. This decision does not sign or modify any SRS file.

## D-066-65 — Owner lanes and ownership for FEAT-066 (2026-11-18)

**Owner's scope** (owner's words: "seed data, quota … sửa lệch giữa BE và FE và ghép api vào FE ở cả 4 role và cuối cùng là viết test ở bruno"; "payment tk khác làm nên tôi ko đụng"):
- L1 seed data;
- L2 quota, covering class capacity and video quota, without payment;
- L3 API audit against the SRS, and BE–FE alignment;
- L4 FE wiring for all four roles;
- L5 Bruno tests.

**Payment** (quote, invoice, checkout, provider callbacks, slot and top-up purchases) belongs to another teammate.

**Seed scope (O-SEED):** all four roles (owner selection on 2026-11-18).

**Billing module ownership (O-PAY):** "Tôi: contract + port + Billing trừ thanh toán". The owner builds:
- the Billing contract;
- its ports;
- the Billing module, except payment.

This is **pending agreement with the payment teammate** on the payment interface (Billing Draft 7 §7.4) and on the payment-owned tables. Until that agreement, no Billing implementation slice is approved.

## D-066-66 — Billing contract direction for class capacity and video quota (2026-11-18)

**Contract of record:** `plan/PLAN_L2_BILLING_CONTRACT_DRAFT7_20261118.md`, 49,498 bytes, SHA-256 `216B33D7B146E97DD2E0E99F13B034FC852A42E0933C9B30E520FF58DAB12BD0`.

**Review history:** six cold-review rounds (Sonnet 5.5 high), the sixth granted by the owner beyond the five-round limit. The latest result was round 6, NOT READY with 0 P1, 1 P2 and 7 P3. Draft 7 is closed **without further review** by owner instruction ("Draft 7, không review"), with its F6 fixes as text edits.

**Owner selections recorded here:**
- **Admission design — "BE1 tự đếm lớp"** (replaces Q-L2-2 "Port giữ chỗ (reservation)").
  - BE1 counts its own active classes inside its class-create transaction, under a lock on the organization row.
  - Billing returns a versioned admission-capacity answer.
  - No reservation, receipt or backfill exists.
- **Stale-answer guard — "dấu version".**
  - A BE1 column `be1_organizations.capacity_version_seen` is written only under the organization lock (Draft 7 §4 step 7).
  - The downgrade use case runs under the same lock. If its outcome is indeterminate, it commits an unknown (null) stamp before releasing the lock.
  - Billing's timeouts stay strictly inside BE1's call timeout.
- **Earlier owner answers kept:**
  - Q-L2-1 "Module mới trong backend";
  - Q-L2-3 "503 BILLING_UNAVAILABLE" (this public code is still to be added to SRS §9.8);
  - Q-L2-5 "Cấu hình, giá trị tạm";
  - Q-L2-6 "Lười, lần dùng đầu";
  - Q-L2-8 "Làm sổ + đọc trước";
  - Q-L2-9 "Theo slice quy ước chung".
- **Q-L2-7 "2 lệnh, key = payment event"** was extended by the Draft 1 review answer "Thêm lệnh thứ 3" into three payment-fulfilment commands, keyed by the verified provider event receipt.
- **Q-L2-4 "Platform Admin + seed"** was refined by "Bootstrap + seed": organizations are created only by `be1_bootstrap.py`.
- **Other Draft 1 review answers:**
  - "Slot = 10 + add-on, đếm lớp active";
  - "B-1 tạo sẵn bảng rỗng";
  - "Seed giá trị tạm";
  - "Kỳ local tự gia hạn".

  "Backfill khi mở subscription" lapsed with the reservation design.
- **Residuals accepted — "Chấp nhận cả hai":**
  - **(d)** After a provider cancellation and until BE1 consumes `CapacityVersionChangedV1`, a create may still be admitted with a stale `can_create`. The result is an extra class in a cancelled subscription, never an over-capacity class.
  - **(f)** If BE1's process dies or its commit fails after Billing committed a downgrade (or Billing commits after BE1 gave up), creates holding a pre-schedule answer can exceed the new capacity at the effective time. This is bounded by the stale creates in flight, made visible by an audit event, and resolved by an operator.
- **Downgrade audit sink — "Duyệt":**
  - Use the existing `core_audit_entries`: `action` = event type, `resource_type` = `capacity_downgrade`, `resource_id` = change group ref.
  - Do not store the surplus count.
  - De-duplicate by check-before-insert under the organization lock, without a new unique constraint on the core table.
  - An HTTP read route for audit stays open, together with the downgrade route.

**Still open** (Draft 7 §12):
- the public names of the new codes and audit events;
- the concrete timeout values and the Billing pool size;
- the sweep and outbox publisher runner;
- replacing or cancelling a scheduled downgrade;
- the staging/production price version, supplied by the payment teammate;
- the register and SRS updates for the NEW items.

**Scope:** this decision fixes the contract direction only. It does not approve a Billing slice, schema, migration, test or runtime.

## D-066-67 — Amend three sentences of D-066-63 (2026-11-18)

Owner approval: "Duyệt sửa 3 câu". D-066-63 stays in place as written. For MGR-2 and Billing work its three sentences are read as follows, consistent with SRS UC-06 line 1460, §21.2 line 1649, §9.7 line 842 and §11.1 item 10 line 1027:

1. "BE1 must obtain a versioned, concurrency-safe admission result before creating a class" → Billing supplies a versioned capacity answer, and BE1 makes the admission decision itself under its own organization lock (D-066-66).
2. "A read-only capacity snapshot followed by an independent insert is insufficient" → still true; the capacity answer is read-only, but the count and the insert are one BE1 transaction under that lock, guarded by the version stamp and `valid_until`, so they are not independent.
3. "The Billing owner must define the exact receipt/reservation, expiry, recovery, and persistence contract before MGR-7" → no receipt or reservation exists in the selected design; the Billing contract of D-066-66 defines the capacity answer, the version stamp, the downgrade use case and the events instead.

The other parts of D-066-63 are unchanged:
- fail closed;
- GRACE and RESTRICTED behaviour;
- suspension at the effective time;
- idempotency semantics;
- the §9.8 404/403 distinction, now governed by D-066-68.

## D-066-68 — API conventions for the conventions slice CONV-1 (2026-11-18)

**Source:** `plan/PLAN_API_CONVENTIONS_CONTRACT_DRAFT1_20261118.md`, 13,999 bytes, SHA-256 `1F41B74AD0F0A8425D5843851FEBA0CCFFDCD6D1572EE159E967F528C7D9DB01`. The SRS checks are recorded in `OWNER_DECISION_PROPOSALS_SRS_20261118.md`.

**Owner answers:** given one question per item on 2026-11-18, each checked against the adopted SRS.

- **C-D1 "Duyệt A":** every route uses the M2 Parent error envelope.
  - The top-level §9.8 fields are `code`, `message`, `correlation_id`, `retryable`, `retry_after_seconds` and `field_errors`.
  - Two extras are allowed under §21.1 line 1635: `current_version`, returned with `STALE_REVISION` (§21.4), and `request_id`, equal to `correlation_id`.
  - This also confirms M2 limitation-ledger item O4.
- **C-D2 "Duyệt A":** the correlation header is `X-Request-ID`. The body's `correlation_id` equals it.
- **C-D3 "Duyệt A":** schema and validation failures return 400 `INVALID_REQUEST` with `field_errors`. 422 is used only for the §9.8 semantic codes.
- **C-D4 "Duyệt":** the §9.8 rule applies.
  - Uniform 404 `RESOURCE_NOT_FOUND` for an ID that does not exist or is out of scope.
  - 403 `ACTION_NOT_ALLOWED` only when the resource is in scope.
  - CONV-1 changes the shared scope guards; route-specific checks change in their own slices.
- **C-D5 "Duyệt A":** header `Idempotency-Key` with exactly one value of 1–128 visible ASCII characters, which is the existing M2 Parent rule. A missing key on a state-changing command returns 400 `INVALID_REQUEST`.
- **C-D6 "Duyệt A":** idempotency receipts are durable with no expiry, and only successful results are stored.
- **C-D7 "Duyệt A":** the revision transport stays per resource family: body `expected_revision` for M2 Parent, strong `If-Match`/`ETag` for Lesson Library. Every stale case returns 409 `STALE_REVISION` with the current version or ETag, never 412.
- **C-D8 "Duyệt A":** `limit` above 100 returns 400 `INVALID_REQUEST`. The page default is 25 with a maximum of 100; cursors are opaque.
- **C-D9 "A: giữ tạm":** the `/api/<namespace>/v1/...` paths stay for now, as the §9.6 OpenAPI reconciliation of the §21.1 `/v1` base path. This is **not a literal match of §21.1**, and an SRS reconciliation note is required. The M2 Parent and StoryRun routes stay on `/v1/...`.
- **C-D10 "Cho Parent đi trước":** the 8 M2-allowed Parent operations may be wired (C-P) before CONV-1.

**Scope:** this decision fixes conventions for later slices only. CONV-1 still needs its own Task Approval, because MGR-7 excludes `app.py` envelope mapping. Nothing is implemented by this decision.

## D-066-69 — School Manager profile visibility and account revisions (2026-11-18)

- **O-PRIV — "Duyệt theo SRS"** (SRS §31.3 permission table line 2586, School Manager: "Không đọc profile contents mặc định"):
  - By default the School Manager receives no child-profile contents: no name and no age.
  - Roster views show counts and opaque references only, until the owner approves a separate process.
  - Teachers keep the fields granted to them.
- **O-ACCREV — "Duyệt":** Platform Admin account updates need no mandatory revision precondition, because SRS §21.4 line 1699 lists only profile, lesson plan, story and script. Accounts keep returning their revision, and the idempotency key is still required (D-066-68 C-D5).

**Scope:** this decision does not implement anything. The BE and FE changes belong to their capability slices.

## D-066-70 — Parent mobile reconciliation (2026-11-18)

**Source:** `tmp/feat066-phase-a/mobile-brief/PARENT_MOBILE_RECONCILIATION_BRIEF_20261118.md`. Owner answers, given one question per item:

- **D-A "(c) Lưu rồi làm sạch":**
  - The staged FEAT-081 Plan Revision 19 / Addendum 34 work in the mobile worktree is preserved non-destructively: a patch of the staged diff plus both sides of the conflicted test under `tmp/`, or a backup branch.
  - The Parent slice C-P then starts clean from the M2 contract.
  - A FEAT-081 record marks Plan 19 as superseded. Plan 19 targets the legacy `/api/parent/v1/child-profiles…` routes, which `dev` and M2 removed and SRS §21.2 does not name.
- **D-B "Tác giả tự xử lý":** the author of the unmerged `apps/ui-mobile/tests/parentSrsBehavior.test.ts` resolves it inside the D-A preserve step. No session resolves it automatically.
- **D-C "Đúng, merge vào đó":** `origin/dev` is merged into `feature/fe-mobile-remediation` without a force-push.
  - Only after D-A and D-B are done.
  - Only after M2 has reached the base (O-0).
  - HieuNewBie joins for the `backend/alembic` changes.
- **D-D "FEAT-081 addendum":** C-P is carried by a new FEAT-081 addendum that references the FEAT-066 register rows M02–M05 and M08–M11.

**Scope:** this decision authorizes no Git operation, file move or mobile edit. Each step needs its own owner instruction.

## D-066-71 — CONV-1 owner answers and package approval (2026-11-18)

**Source:** `plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT5_20261118.md`, 47,483 bytes, SHA-256 `3FCF47412F69D8A16EFFFC7978C5E2BD107EA429EF3F42D354BCE00FF7451278`.

**Review history:**

| Round | Draft | Verdict (P1/P2/P3) |
|---|---|---|
| 1 | Draft 1 | NOT READY 1/8/7 |
| 2 | Draft 2 | NOT READY 1/1/13 |
| 3 | Draft 3 | NOT READY 0/2/8 (both D-171 stop conditions met; owner chose to continue) |
| 4 | Draft 4 | **READY WITH NOTES 0/0/5** |

Draft 5 fixes the five round-4 P3 notes and was not re-reviewed, by owner choice.

**Owner answers, given in chat on 2026-11-18:**
- **CV-B:** CONV-1 is implemented on a new branch `feature/feat066-conv1` from `08439b22`. The branch is **local only and never pushed** ("nhánh này là nhánh chỉ ở máy ko đẩy lên github cho tôi").
- **CV-1:** `/api/parent/v1/ai` stays out of CONV-1 and moves to C-P, because the mobile parser reads only `payload.detail`. This answer was asked again after review finding F5 showed that the first premise was wrong; the owner chose the option "Leave it for C-P". It is a **scoped deferral** of D-066-68 C-D1 "every route" for that family until C-P.
- **CV-2:** only the generic codes are mapped to the §9.8 codes. Upload and file codes, which also change status, go to their own slices (option "A: generic codes only").
- **CV-3:** messages come from one Vietnamese table, and route-supplied text is ignored ("còn lại có hết").
- **CV-4:** a missing `If-Match` gives 400 `INVALID_REQUEST` with a field error ("còn lại có hết").
- **CV-5:** an inactive or wrong-role account gets 404 `RESOURCE_NOT_FOUND` (option "404 RESOURCE_NOT_FOUND"). An identity-issuer mismatch also gives 404; this is the coordinator's reading of CV-5, which the owner accepted with the package.

**Approval:** the owner approved Draft 5 without re-review (option "Approve Draft 5"). The Task Approval entry for CONV-1 records the scope.

**Scope:** implementation starts only on a separate owner word. Billing is frozen and is not affected.

## D-066-72 — SEED-1 (S1 core-data seed) owner answers and package approval (2026-11-18)

**Source:** `plan/PLAN_SEED1_S1_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT4_20261118.md`, 23,121 bytes, SHA-256 `141488271D7FB37FDDAD1B0BA7005CF96ABAAA00EC627E80E2AA848638410BFA`. It builds on the seed design Draft 6 (`plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT6_20261118.md`, 28,192 bytes, `CABC4BCA…`).

**Review history** (Sonnet 5.5 at high effort, set explicitly):

| Round | Draft | Verdict (P1/P2/P3) |
|---|---|---|
| 1 | Draft 1 | NOT READY 0/4/6 |
| 2 | Draft 2 | NOT READY 0/2/6 (repeat-class condition met; the owner chose "Draft 3 + round 3, keep SQL") |
| 3 | Draft 3 | **READY WITH NOTES 0/0/7** |

Draft 4 fixes the seven round-3 P3 notes and was not re-reviewed.

**Owner answers** (chat, 2026-11-18: "SD-1 đến SD-5 theo đề xuất"):
- **SD-1:** S1 only. S2 to S4 come later as SEED-2 to SEED-4; Billing is frozen by the owner.
- **SD-2:** the code lives in `backend/tools/seed/`.
- **SD-3:** a separate database whose name contains `seed`, on a loopback port other than 5432 or 5433, prepared by the owner. The guard enforces it.
- **SD-4:** a local branch `feature/feat066-seed1`, cut from the tip of the BE queue when the slot opens, after FR-C-08. It is local only.
- **SD-5:** adult sign-in is deferred until before the FE slices. The FE-screen acceptance is deferred with it, and the seeded issuer is coupled to whatever sign-in is chosen.

**Design departures recorded with this approval:**
- `lesson.library_source_documents` and `lesson.library_document_revisions` are not seeded;
- `parent.command_receipts` and `story.command_receipts` are not seeded;
- seeded StoryRuns are static and display-only.

**Approval:** the owner instructed "làm SEED-1 tiếp đi check lại nếu ổn thì duyệt" on 2026-11-18. The coordinator re-checked Draft 4: all seven P3 fixes are present, and the design and review pins match. The package is therefore approved. Implementation starts only in its BE queue slot and on a separate owner word.

## D-066-73 — PAY-0 (payment interface skeleton) owner answers and package approval (2026-11-18)

**Source:** `plan/PLAN_PAY0_PAYMENT_INTERFACE_SKELETON_DRAFT6_20261118.md`, 68,734 bytes, SHA-256 `AE4DB60B67F935FB7F874B3498626B5DE1D38448891561906DC78B476388078E`.

**Review history** (Sonnet 5.5 at high effort, set explicitly; records in `evidence/notes/`):

| Round | Draft | Verdict (P1/P2/P3) |
|---|---|---|
| 1 | Draft 1 | NOT READY 2/12/5 |
| 2 | Draft 2 | NOT READY 1/6/7 (repeat-class condition met; owner chose Draft 3 and round 3) |
| 3 | Draft 3 | NOT READY 0/5/9 (repeat-class condition met; owner chose Draft 4 and round 4) |
| 4 | Draft 4 | NOT READY 0/3/9 (repeat-class condition met; owner chose Draft 5 and round 5) |
| 5 | Draft 5 | NOT READY 0/1/7 (last allowed round; owner chose Draft 6 without review) |

Draft 6 fixes the round-5 P2 (RC-01, double activation when two ended attempts are both paid) and the seven P3 notes, and was not re-reviewed.

**Owner answers**, given one question at a time in chat on 2026-11-18, each with the SRS or document sentence it rests on; every answer is the package recommendation:
- **PD-1:** D-066-65 is amended: the owner's lane builds the PAY-0 skeleton (ports, DTOs, the three payment tables, the callback intake with its safety rules, a fake provider and the provider contract-test kit). The payment teammate still builds the MoMo and VNPAY adapters and the real payment flows on top. Billing core stays frozen.
- **PD-2a:** PAY-0 creates `billing.invoices`, `billing.payment_attempts` and `billing.provider_event_receipts` now, with subscription references as soft refs until B-1 adds the foreign keys.
- **PD-2b:** no receipt row for an unverified callback (`INVALID`, `MALFORMED`); a safe security event only. The data register note at line 392 is to be amended accordingly.
- **PD-2c:** the NEW `payment_attempts` columns of package §4 (idempotency scope, request fingerprint, checkout claim, reconcile request and tries, review flag and reason) are added to the register.
- **PD-2d:** the NEW observed-value columns of `provider_event_receipts` (package §4) are added to the register.
- **PD-2e:** one open checkout per organization and operation (Interpretation I-6, a NEW product rule), enforced by a partial unique index; a further checkout gets 409 `CHECKOUT_IN_PROGRESS`.
- **PD-3a:** the quote stays payment-side, as D-066-65 says.
- **PD-3b:** a NEW read-only Billing port `BillingQuoteInputsPortV1`; PAY-0 uses only a fake implementation until B-1.
- **PD-4:** routes as package §7: checkout `POST /api/billing/v1/organizations/{organization_id}/subscription/checkout` (C-D9 interim mapping of SRS 1677); callback on the SRS path `/v1/payments/{provider}/callback`, outside CONV-1, answering in the provider format; NEW status route `GET /api/billing/v1/payment-attempts/{payment_attempt_id}`.
- **PD-5:** option A: the payment intake and Billing core share one database session for the fulfilment call (SRS 1012, 1028, 1869), with the lock order and the Draft 7 edits of package §6 and §6.1.
- **PD-6:** the checkout actor ("Admin billing", SRS 1677) stays open as in Draft 7 §7.5; PAY-0 uses a permission hook defaulting to School Manager for the fake flow only.
- **PD-7:** the package §9 setting defaults are placeholders, to be set with the payment teammate from the provider documents before PAY-1.
- **PD-8:** PAY-0 joins the one-at-a-time BE queue after FR-C-08 and SEED-1, as PAY-0a, PAY-0b and PAY-0c.
- **PD-9a:** the owner's lane builds the periodic job runner, as a small separate slice after PAY-0c, shared with the Billing sweep.
- **PD-9b:** the settings validator refuses `payments_enabled` outside `local` and `test` until `payments_periodic_runner_configured` is true.

**Recording rule:** at the owner's request, this row records the decisions only, not the owner's chat wording.

**Approval:** the owner approved Draft 6 on 2026-11-18. The Task Approval entry for PAY-0 records the scope. Each of PAY-0a, PAY-0b and PAY-0c still needs its own Task Approval and an owner word to start, in its BE queue slot. Nothing is implemented by this decision.

## D-066-74 — Billing payers, Billing ownership and the V1 payment provider (2026-11-18)

**Owner instruction** (chat, 2026-11-18), recorded as decisions only:
- **Billing is no longer frozen.** The owner's lane builds Billing core (Billing contract Draft 7, slices B-1 to B-5), as D-066-65 already allocated ("contract, ports and Billing except payment"). The earlier hold on Billing work is lifted.
- **Payment stays with the payment teammate** (D-066-65 as amended by D-066-73 for the PAY-0 skeleton only).
- **V1 payment provider: MoMo.** VNPAY is not in the current scope. This narrows SRS FR-B-02 and BR-28, which name both MoMo and VNPAY as V1 adapters; the PAY-0 provider contract stays provider-neutral, so VNPAY can be added later without a contract change.
- **Who pays:**
  - **School Manager pays for the school:** the organization subscription and capacity (SRS 1677 "Admin billing" = the School Manager of the organization) and the school video-quota package or top-up. Teachers then work inside what the school bought: classes through capacity and assignment, and video through the school quota of their occurrence.
  - **Parent pays for the Parent account:** the Parent account video-quota top-up.

**Reading against the SRS** (the owner asked for SRS-based decisions rather than further questions):
- SRS 168, BR-38 and FR-B-10 keep two quota scopes (school organization and Parent account) and **no Teacher-account pool**; Teacher video counts against the school quota of the occurrence. "School Manager pays, then Teachers get it" is therefore read as Teachers drawing from the school quota and the school capacity, not as per-Teacher quota pools. A per-Teacher allocation would contradict BR-38 and is not adopted.
- SRS 1621 (permission table, "Mua đơn vị quota video") leaves the purchase actor OPEN under Q193 for both the Parent ("Quyền mua package/top-up OPEN theo Q193") and the School Manager ("Quyền mua/cấp/phân bổ quota school OPEN theo Q193"). This decision closes the actor part of Q193: Parent for the Parent account, School Manager for the school. The offer itself (packages, prices, enablement) remains a commercial setting; SRS 168 gives review values only.

**Effects on earlier records** (append-only; earlier rows are not edited):
- D-066-73 **PD-6** is settled: the checkout actor for the organization is the School Manager. The PAY-0 permission hook defaults to it for real use, not only for the fake flow.
- The PAY-0 out-of-scope item "Parent top-up purchase route (SRS 1679, Q193 gate)" is no longer gated by the actor question; it stays out of PAY-0 and is planned with Billing B-3 and the payment teammate.
- C-M4 (W-CAP, class creation with capacity admission) is no longer blocked by a freeze; it now waits for Billing B-1 and B-2 to be built.
- The BE queue order (one slice at a time) is unchanged until the owner orders the Billing slices: FR-C-08, SEED-1, PAY-0a to 0c, then C-M1 and Billing B-1 in an order to be set.

**Scope:** this decision authorizes no code. Each Billing slice still needs its own reviewed contract revision where Draft 7 must change, a Task Approval and an owner word to start.

## D-066-75 — C-M (School Manager per-role slice) settled answers and package approval (2026-11-18)

**Source:** `plan/PLAN_CM_SCHOOL_MANAGER_SLICE_PACKAGE_DRAFT4_20261118.md`, 28,716 bytes, SHA-256 `401E893503D5DC96071B88AE264DB3F029F076F10AF0824CA6366DACC092CF8A`.

**Review history** (Sonnet 5.5 at high effort, set explicitly; records in `evidence/notes/`):

| Round | Draft | Verdict (P1/P2/P3) |
|---|---|---|
| 1 | Draft 1 | NOT READY 1/6/8 |
| 2 | Draft 2 | NOT READY 0/5/6 (repeat-class condition met; owner chose Draft 3 and round 3) |
| 3 | Draft 3 | NOT READY 0/2/7 (repeat-class condition met) |

Draft 4 fixes the round-3 findings and was not re-reviewed, by owner choice.

**Settled answers** (package §6). The owner asked on 2026-11-18 that package questions be settled from the SRS rather than asked one by one; each answer below is the package's SRS-grounded recommendation:
- **CM-1:** C-M may change A07, A09, A10, B01, B02, the session roster and pilot profiles (O-L3SCOPE for these rows only).
- **CM-2:** the School Manager gets 403 on the session roster and the synthetic pilot-profiles route (SRS 2586, D-066-69).
- **CM-3:** A09 for the School Manager returns a count only (`Be1ClassRosterSummaryV1`, NEW).
- **CM-4:** A10 for the School Manager returns `Be1ConsentListManagerV1` (NEW) without `child_id` and `purpose_ref`.
- **CM-5:** the School Manager summary does not run the A09 consent gate.
- **CM-6:** the FE maps the BE consent states `pending` and `revoked`; no BE rename.
- **CM-7:** A07 and A10 are paged now (SRS 1640, C-D8); A09 paging is deferred to the consent slice (MGR-5).
- **CM-8:** the BE-before-FE window of package §4 is accepted (local development only).
- **CM-9:** C-M1 BE runs on a new local-only branch `feature/feat066-cm1`, cut from the BE queue tip when its slot opens, never pushed; pins are refreshed then.
- **CM-10:** queue: FR-C-08, SEED-1, PAY-0a to 0c, then C-M1 BE, then Billing B-1.
- **CM-11:** full A09 fields and A10 Teacher items only for a `teacher` assignment row of that class; org-wide `teacher`, `guide` and `observer` rows get 403 (SRS 2586). This is a stated behaviour change.
- **CM-12:** UC-12 (G09) is planned after C-M3.

**Recorded debt:** package §8 lists School-Manager-reachable routes that still return child media or free text (canvas checkpoints, artifacts, gallery, observations and portfolio, session read `configuration`, `teacher_note`, group `display_name`, pilot assistance pending list, and the unchecked `child_id` and `purpose_ref` on consent writes). They are not changed by C-M1.

**Recording rule:** decisions only, not the owner's chat wording.

**Approval:** the owner approved Draft 4 on 2026-11-18. The Task Approval entry for C-M records the scope. C-M1 BE, C-M1 FE and the later sub-slices each still need their own Task Approval with exact paths and an owner word to start. Nothing is implemented by this decision.

## D-066-76 — Billing contract Draft 9 becomes the contract of record (2026-11-18)

**Contract of record:** `plan/PLAN_L2_BILLING_CONTRACT_DRAFT9_20261118.md`, 63,668 bytes, SHA-256 `3280BBC9486780E108D5A0C3A3921D7E8EF13E5F48A9BF2B748645739ADC7876`. It replaces Draft 7 (D-066-66) as the Billing contract of record.

**What changed:** Draft 8 (58,033 bytes, `BFD95D4D…`) applied the decisions made after Draft 7: D-066-67, D-066-68 and D-066-71 (conventions built), D-066-73 (PAY-0 skeleton and its Draft 7 edit list), D-066-74 (Billing ownership, payers, MoMo) and D-066-75 (queue). The capacity design, the version stamp, the downgrade use case and the residuals accepted in D-066-66 are unchanged.

**Review:** Draft 8 had one owner-granted round (Sonnet 5.5 high): NOT READY 0 P1 / 3 P2 / 10 P3, with no broken decision and no double-charge or over-activation path (`evidence/notes/L2_BILLING_CONTRACT_DRAFT8_COLD_REVIEW_20261118.md`, 3,777 bytes, `5F3F80F5…`). Draft 9 fixes all thirteen findings as text edits and was not re-reviewed, by owner choice.

**Contract points recorded with this approval:**
- The payment tables are created by PAY-0a; Billing B-1 extends the same `billing` Alembic branch and adds the subscription foreign keys.
- `PaymentFulfilmentPortV1` runs in the payment intake's session (one transaction inside the `billing` module), returns `FulfilmentResultV1`, and is idempotent per invoice through NEW uniques on `subscription_events` (`invoice_id`, event type) and `video_quota_grants` (`source_invoice_id`).
- NEW read-only `BillingQuoteInputsPortV1` (provider period, price per slot, paid slots), faked until B-4.
- The downgrade audit events use `core_audit_entries` as D-066-66 states.
- Billing routes use the interim `/api/billing/v1/...` paths (C-D9); the School Manager is the billing admin, resolved at call time; Teachers read the school quota of their assignment's organization.
- Interpretations marked in the contract: the owner approves the staging and production price version; `billing_admin_ref` stays null; MoMo recurring through PAY-2 is conditional on SRS OI-09.

**Queue:** FR-C-08, SEED-1, PAY-0a to 0c, C-M1 BE, then Billing B-1; the periodic runner slice (D-066-73 PD-9a) after PAY-0c; the owner sets the position of the runner and the order of B-2 to B-5.

**Recording rule:** decisions only, not the owner's chat wording.

**Scope:** this decision fixes the contract. Each Billing slice (B-1 to B-5) still needs its own Task Approval with exact paths and an owner word to start. Nothing is implemented by this decision.

## D-066-77 — SEED-1 moves ahead of FR-C-08 in the BE queue (2026-11-19)

**Owner instruction** (chat, 2026-11-19), recorded as a decision only: SEED-1 runs before FR-C-08.

**Reason recorded by the coordinator:** FR-C-08 wave 1 passed its review round 4 (READY WITH NOTES, 0 P1 / 0 P2 / 8 P3), but it still has seven blockers before an implementation approval can be requested (named module owners, SRS wording, a schema delta, a core reference-closure contract, a response-schema decision, the base-commit confirmation, and review round 5). SEED-1 is approved (D-066-72), touches none of the FR-C-08 files, and unblocks the Bruno baseline (BRU-0).

**BE queue from now:** SEED-1 → FR-C-08 (when its blockers are cleared) → PAY-0a → PAY-0b → PAY-0c → C-M1 BE → Billing B-1; the periodic runner slice (D-066-73 PD-9a) and Billing B-2 to B-5 are ordered by the owner later; C-T1 BE stays paused with C-T.

**Effect on D-066-72:** SD-4 said the SEED-1 branch is cut from the BE queue tip "after FR-C-08"; it is now cut from the current queue tip, the CONV-1 line `feature/feat066-conv1`, when SEED-1 starts. Everything else in D-066-72 is unchanged.

**Scope:** this decision changes the order only. SEED-1 coding still starts on a separate owner word, under its Task Approval entry.

## D-066-78 — SEED-1 guard live check amended for a Docker-hosted seed database (2026-11-19)

**Finding:** the first owner run against the seed database (a PostgreSQL 17 container published on `127.0.0.1:5435`) stopped at the guard, before any write: `the server port does not match the guarded port`. Through Docker port mapping the server reports its own side of the connection: `inet_server_port()` is the in-container port 5432 and `inet_server_addr()` is the container interface, not a loopback address. The live check of package §3.1 (Draft 4) therefore cannot pass for any container-hosted seed database. No row was written.

**Owner decision:** amend the live check of package §3.1.
- **Kept, server side:** `current_database()` equals the guarded database name, and `current_user` owns that database.
- **Removed, server side:** the `inet_server_port()` comparison and the loopback `inet_server_addr()` check.
- **Unchanged, client side, before any connection:** the only input is `S2L_SEED_DATABASE_URL`; the database name contains `seed` and neither `be1_acceptance` nor `m2_s1a`; the host is an explicit loopback address; the port is explicit and neither 5432 nor 5433; no query string; no libpq connection variable; the other URL variables are unset or equal; `settings.env` is `local` or `test`; the engine is built from the explicit URL and its database name, host and port are compared with the guarded values; no URL is ever printed.

**Scope:** `backend/tools/seed/guard.py` and `backend/tests/unit/test_seed_guard.py` only, inside the existing SEED-1 allowlist. The rest of the approved package (Draft 4, `141488271D7F…`) is unchanged.

## D-066-80 — Seed design Draft 11 accepted as the system-wide seed plan (2026-11-19)

- **Decision:** the owner accepted `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT11_20261119.md` (73,863 bytes, SHA-256
  `6E4EFDE08E2763B6A0B0CCAE6CC4DC5301457961B22EB46BBF520D401C727CE8`) as the FEAT-066 lane L1 seed plan for the
  whole SRS data model. It supersedes Draft 6 as the seed design; the SEED-1 implementation of stage S1
  (commit `4e2f6d96`) stays valid, with the later changes that Draft 11 §2 rule 12 and §11.8 name.
- **Review basis:** five rounds on Sonnet 5.5 high under D-171. Draft 7 R1 NOT READY (1 P1 / 11 P2 / 8 P3);
  Draft 8 R2 NOT READY (0 / 3 / 10); Draft 9 R3 NOT READY (0 / 1 / 10); Draft 10 targeted check NOT READY
  (0 / 1 / 3); Draft 11 targeted check R5 READY WITH NOTES (0 / 0 / 3). The review records are local and ignored
  under `tmp/seed-d7-review/`, `tmp/seed-d8-review/`, `tmp/seed-d9-review/` and `tmp/seed-d11-check/`; the R5
  check is 9,785 bytes, `3B53A02E0409715B…`.
- **Open notes carried forward:** the three R5 P3 notes are carried into the first stage Task Approval that
  needs them, not fixed in the plan:
  - name the two sources of the final Lesson object key (part keys from `core_upload_parts.storage_object_ref`;
    final keys derived from `core_upload_sessions`);
  - define the first object-store write as "the seed database records no seeded object", and add it to the
    re-seed procedure;
  - extend the allowed key set when the occurrence source upload, the video asset and the library visuals
    are built.
- **What this does not authorize:** no script, database, storage, Docker or provider command, and no stage
  implementation. Each stage (S5, S7 item 2a and later) needs its own Task Approval and owner launch.
- **Numbering:** first decision under the D-066-80 rule of the decision-ID reconciliation note (BE lineage).

## Decision-ID reconciliation note — two numbering lineages (2026-11-19)

- **Why:** this file was merged from two branches that numbered FEAT-066 decisions independently. Both
  histories are kept verbatim above, because earlier records pin their bytes; no entry was renumbered or
  edited.
- **Web lineage:** branch `codex/fe-ui-web-remediation`, decisions D-066-62 to D-066-78 (Revisions 31 to 51,
  2026-11-16 to 2026-11-17), followed by the Rev48 to Rev51 entries. They appear first in the merged part.
- **BE lineage:** `dev` and the local BE branches `feature/feat066-*`, decisions D-066-62 to D-066-79 as of
  2026-11-19. `dev` holds D-066-62 to D-066-70 (they follow the web entries above); D-066-71 to D-066-79 exist
  only on local BE branches so far and will arrive when those branches merge.
- **How to cite from now on:** a decision ID in the range D-066-62 to D-066-79 must carry its lineage, for
  example "D-066-62 (web)" or "D-066-62 (BE)". An ID without a lineage in that range is ambiguous.
- **Next number:** every new FEAT-066 decision, in either lineage, takes the next number from D-066-80
  upward, so the two lineages do not collide again.
- **Authority:** this note records a merge resolution approved by the owner; it decides nothing else.

## D-066-81 — BRU-0a (Bruno scaffolding and A02 baseline) approved; guard level (2026-11-19)

**Source:** the BRU-0a entry in `approvals/TASK_APPROVAL.md`, built on `plan/PLAN_L5_BRUNO_COVERAGE_DRAFT3_20261118.md` (18,584 bytes, SHA-256 `3F5AFCC727F3C43451903582FF0DBA05BC0F181290AA6D510B0B6C54973786A9`).

**Review:** round 3 of the L5 plan Draft 3 and of the draft entry (Sonnet 5.5, high): NOT READY, 0 P1 / 3 P2 / 9 P3. Report `evidence/notes/L5_DRAFT3_REVIEW_R3_20261119.md`, 34,247 bytes, SHA-256 `7766C981A0140439B571A9877FB9C309E6D32EB537FED1ECC5D32E3523E6D5CF`. The three P2 items concerned the draft entry and are closed in the approved entry; the entry was not re-reviewed.

**Owner decisions** (chat, 2026-11-19):
- **Scope:** BRU-0a is L5-0 part 1 plus A02 only. BRU-0b (A17, A20, A22, A26, A27) and A08 are not approved.
- **Guard level:** the loopback guard stays a collection-level `collection.bru`.
- **Plan:** Draft 3 is accepted for the 0a scope; a Draft 4 is needed before BRU-0b and later steps (L5R3-04, 05, 11, 12).

**Not decided:** O-BRU-AUTH, O-L3SCOPE, the S-1 rotation status.

**Scope of this decision:** it approves the entry only. The launch needs a separate owner word. No commit or push is authorized.

## D-066-82 — BRU-0a review round 4 and addendum 1 (2026-11-19)

**Review:** round 4 of the BRU-0a entry Draft 2 (Sonnet 5.5, high): NOT READY, 0 P1 / 2 P2 / 6 P3. Report `evidence/notes/BRU0A_ENTRY_D2_REVIEW_R4_20261119.md`, 29,156 bytes, SHA-256 `65569D1021575EAF6E62E87E1326E2CF640FC790E99E42907DE0F8BDFE0AEAF3`.

**Owner decision** (chat, 2026-11-19): the guard route (b): the guard is written as an unverified candidate and proven by the owner-run positive run and negative control (no stop for missing Bruno 4.3.0 material).

**Record:** addendum 1 in `approvals/TASK_APPROVAL.md` closes R4-01 to R4-07 and corrects the status of L5R3-01 and L5R3-03 to Partly. Addendum 1 was not re-reviewed. D-066-78 stays as recorded.

**Scope:** it changes the BRU-0a entry text only. The launch needs a separate owner word. No commit or push is authorized.

## D-066-83 — Bruno loopback guard parses the URL by hand for the 4.3.0 CLI (2026-11-19)

**Source:** the B2 run recorded in `evidence/notes/BRU_0A_IMPLEMENTATION_EVIDENCE_20261119.md` (guard candidate, goal run and re-run).

**Finding:** the Bruno 4.3.0 CLI script sandbox has no `URL` global, and its script preprocessor rejects a regex literal that contains slashes. The URL-parser guard of D-066-81 (drafted as D-066-78) could not run.

**Decision:** `collection.bru` keeps the collection-level guard but parses `bru.interpolate(req.getUrl())` with string methods. It rejects control characters, spaces, backslashes, non-http(s) schemes, any `@` in the authority, malformed ports and every hostname except `127.0.0.1`, `localhost` and `[::1]`. It stays fail-closed (any parse failure throws). The guard is verified for the CLI by the positive run and three negative controls; redirects and later URL changes are still not covered; the Bruno desktop is NOT VERIFIED.

**Scope:** `collection.bru` only (2,638 bytes, SHA-256 `AD0A6A9A42A5038090725FF3E7615CCB9AA3BC070B951035E6D2774C0E9B69EE`). It does not change D-066-81 or D-066-82.

## D-066-84 — Bruno requests for the first Teacher assignment; stale requests kept (2026-11-19)

**Source:** SRS section 21.2 line 1650 and section 21.4 lines 1697 and 1699; C6 M9-B evidence `evidence/notes/M9B_FIRST_ASSIGNMENT_BE_EVIDENCE_20261119.md`; C5 evidence `evidence/notes/C5_CA_BE_IMPLEMENTATION_EVIDENCE_20261119.md`.

**Decision:** the collection gains request `145` (`GET /api/be1/v1/organizations/{organization_id}/teacher-candidates`) and request `146` (`POST /api/be1/v1/classes/{class_id}/assignments`, headers `If-Match` and `Idempotency-Key`, body `{candidate_ref}`). Requests `004` and `005` stay in place and labelled stale (the routes they call are gone); `146` is their replacement. `ROLE_GUIDE.md` now says that `142` pages with a cursor and that `143` and `144` send an `Idempotency-Key` and no `If-Match` (no SRS rule names an expected revision for account role or state, C5 CA-4). No environment file was edited. Routes that still have no request are listed in `evidence/notes/B2_BRUNO_FULL_COLLECTION_RUN_20261119.md` and are left for a later Bruno task.

## D-066-85 — Full-collection run classification without tokens (2026-11-19)

**Decision:** the full collection was run against the local API with the placeholder bearer value only. No token was created or faked and no Firebase request was made. Requests are classified PASS, FAIL (real defect), BLOCKED-AUTH, BLOCKED-ENV or STALE by HTTP status and error code; Bruno's own pass/fail counter is not used because only A02 and requests 137 to 140 carry checks (five of those fail on the 503, which is BLOCKED-AUTH) and the other requests have none. Result: 4 PASS, 0 FAIL, 95 BLOCKED-AUTH (503 `IDENTITY_PROVIDER_UNAVAILABLE` or 401), 46 BLOCKED-ENV, 2 STALE. Authenticated runs wait for SD-5 and owner-approved test tokens (O-BRU-AUTH, still open).

**Numbering note:** D-066-78 and D-066-79 were used in the first BRU-0a drafts. D-066-78 already exists in both lineages (web: shared-folder organization; BE: SEED-1 guard live check), so the BRU-0a approval and review decisions are numbered D-066-81 and D-066-82 here. Cite D-066-62 to D-066-79 with their lineage, "(web)" or "(BE)".

## D-066-86 — Bruno follow-up: requests for every route, run classification (2026-11-20)

**Source:** `evidence/notes/BRUNO_POST_B2_FOLLOWUP_RUN_20261119.md`; SRS (v2.7-draft, 701,810 bytes, starts `443A3CA3`) section 9.8 and section 21 for the routes.

**Decision:** the collection holds 160 request files (159 regular plus the L5 A02 request) and every non-framework route of the running app has a request; the stale and dev-only requests stay labelled. `environments/local.bru` defines `platform_account_id` (used by request `144`). The local run of 153 requests (placeholder bearer, loopback API, guard active, requests `153` to `159` excluded) classifies as 4 PASS, 0 FAIL, 101 BLOCKED-AUTH, 46 BLOCKED-ENV, 2 STALE; the classification rules of D-066-85 are unchanged. Requests `153` to `159` (registration and the six AI routes) are written but are never run against a configured environment; they parse in Bruno CLI 4.3.0 and are stopped by the loopback guard when the base URL is not loopback.

**Not decided:** authenticated runs, O-BRU-AUTH, SD-5 timing, registration or AI-provider requests in any run.

## D-066-87 — AI routes take no client idempotency key; backend check kept open (2026-11-20)

**Source:** SRS section 21.4 (line 1697): state-changing commands carry an idempotency key; SRS section 9.8 (line 904): "AI dùng job/semantic request receipt"; SRS lines 800, 816 and 818: the Parent drawing-guide route and the idempotency/concurrency contract of new resources are not frozen and are reconciled in M0.

**Decision:** requests `154`, `155` and `157` to `159` follow their routers and send no `Idempotency-Key`. Under line 904, AI generation is deduplicated by job or semantic request receipt, not by a client key, so the missing key is not recorded as an SRS violation for the draft-generating routes (`155`, `157` to `159`). Request `154` also attaches artwork to a StoryRun (a state change); whether the route dedupes by a semantic receipt is **not verified here** and stays an open backend check (owner of the check: BE). Request `156` already requires a key. No request-side key is invented.
## D-066-80 (web) - Wait instead of resending context confirmation (2026-11-23)

- Source: owner-approved Goal v4 Phase A web wiring plan revision 52 and the final Teacher contract.
- When the visible Teacher gates appear complete but the run remains in `PREPARATION_REVIEW` with no start signal, the UI shows a waiting hint and does not resend `context-confirmation`.
- Reason: the contract says an unfulfilled hidden gate leaves the run unchanged, and the UI has no reliable signal to distinguish that state from an accepted command still settling.

## D-066-88 - Goal v4 Phase A Parent Android integration order (2026-11-23)

**Source:** the owner-launched Phase A task prompt and `tmp/phase-v4/PHASE_A_FINAL_ROUTE_LIST_20261123.md`, sections 1, 2.3-2.10, 3.1-3.5 and 4. The task plan hash is recorded in the Phase A entry in `approvals/TASK_APPROVAL.md`.

- Parent confirms the subject, loads and selects an activity, then confirms context. Whichever of activity selection or context confirmation succeeds last starts the first story.
- First-story start is implicit in those gates; the Parent flow does not call legacy `story-revisions` for it.
- `story_confirmation_required` is authoritative when present. The app re-confirms the same story revision after a spent video review, and only then offers another video request.
- Current safety blocks route through `SCRIPT_REVIEW` plus video/job fields. The `SAFETY_BLOCKED` run state remains accepted for legacy rows.
- `post_video_activities: null` is normal. A completed run may be read and played again through a fresh playback grant.

This records the implementation contract for this task only. It does not sign off FEAT-063 SRS v2.7-draft or approve a tech-stack decision.

## Goal v4 Phase B Android Parent T-12a/T-12c/BR-20 implementation record — 2026-11-24

This is an implementation record, not a new product decision. The mobile implementation follows the owner-launched contract in `tmp/phase-v4/PHASE_B_FINAL_ROUTE_LIST_20261124.md` and D-066-101. Support-needs remains unavailable when the production key source is not configured. No SRS wording, route contract, production configuration or backend behavior was changed. Verification results are in `evidence/notes/GOAL_V4_PHASE_B_ANDROID_T12AC_EVIDENCE_20261124.md`.
## D-066-100 — Teacher class roster returns the synthetic-or-consented list with a count and a cursor (2026-11-23)

**Source:** the owner decision on the Teacher roster (item A11 of `tmp/phase-v4/OWNER_QUESTIONS_V4_20261122.md`: the Teacher always gets 200, with a count and a cursor) and the later owner decision, option B: the roster lists a profile when it is synthetic or has an effective consent, with no roster DDL. The written trace of option B is `tmp/phase-v4/GOAL_V4_PHASE_B_LAUNCH_BRIEF_20261123.md`, which also records that the owner's Phase B launch word approves the DDL of the four Phase B plans; the T-7e plan has no DDL. SRS (v2.7-draft, 701,810 bytes, starts `443A3CA3`): l.2586 (the Profile row of the access matrix: a Teacher reads only the fields granted after the invitation is accepted and the class is assigned), l.832 (consent applies to real data only; a synthetic profile does not fake consent; a legacy profile of unknown origin is not consent), l.423 and l.622 (the demo runs on synthetic data), l.2673 BR-48 and l.2718 AC-49 (cross-role profile read only through invitation, consent and an active grant), l.816 and l.1640 (roster lists are paged, cursor 25 by default, 100 at most), l.1635 (additive fields are allowed in the current version), l.864-865 (uniform 404). By analogy only, not as a rule for this change: l.2201 (an aggregate roster with no eligible child and no child detail; a temporary test assumption that does not settle consent rules) and l.1449 (no per-child reason for an exclusion). Code at `930da61e`: `be1_registry.py:869-938` (`list_profiles`), `be1_common.py:314-336` (`consent_is_effective`), `be1_models.py:290-295` (consent states `pending` and `revoked` only). Basis plan: `tmp/phase-v4/plans/V4_B_T-7E_PLAN_DRAFT6_20261123.md`.

**Decision:** for `GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles`, a Teacher assigned to the class always receives 200. The body is `Be1ManagedProfileListV1` with `items` (the active profiles of the class that are synthetic, `data_origin = SYNTHETIC_DEV`, or are `REAL` with an `effective` consent by the predicate of `consent_is_effective`), `next_cursor` (nullable) and `active_profile_count` (all active profiles of the class, the same definition as the School Manager summary). A profile that is neither synthetic nor a consented `REAL` one (a `REAL` profile without an effective consent, every `LEGACY_UNCLASSIFIED` profile even with a consent row) is not listed and counts only in `active_profile_count`. `items` is empty when no profile qualifies. The SRS names the synthetic origin `SYNTHETIC_TEST` (l.832) and the code names it `SYNTHETIC_DEV`; for this rule they are one value and nothing is renamed in code or migrations. The route no longer answers 409 `CONSENT_NOT_EFFECTIVE` and no longer writes the audit row `profile.list` with decision `denied_consent_pending`, because no request is denied. The list is paged by an opaque cursor over `(created_at, child_id)` of the filtered set, 25 by default and 100 at most, bound to route, organization and class. The School Manager response (`Be1ClassRosterSummaryV1`) is unchanged and ignores the paging parameters. The consent gates of profile create, admission, canvas and the pilot profile reads are unchanged. The change supersedes the roster part of decision T-7a (blanket 409 while any row lacks consent) and the whole-class consent gate of the earlier T-7e plan.

**Consequences recorded:**
- Synthetic profiles (the demo and seed data) are listed. A `REAL` profile is listed only with an `effective` consent; until a consent grant API and the `effective` state exist (X-19, AC-49; a later task outside goal v4, with no DDL in this change) a class of `REAL` profiles shows an empty list with a non-zero `active_profile_count`.
- Privacy: the listed set together with `active_profile_count` lets a Teacher infer, by absence, that unreleased children exist in the class. No name, id or reason is returned for them.
- Tests and clients that pin the old behaviour change in the same release: `tests/integration/test_t7a_roster_privacy_postgres.py` (the gated-class case), the unit guards `test_be1_scope_guard_404_403.py` and `test_be1_roster_privacy_guards.py`, the OpenAPI catalog entry and its Teacher example, the API test kit requests that pin the Teacher roster (T-33 and its variants), and the web class screen (`T05ClassesScreen.tsx`), which must follow `next_cursor` and use the count in its empty state. The test `test_pending_consent_stays_pending_and_blocks_profile_admission_and_canvas` keeps its admission and canvas assertions; its roster assertions (409, and one `profile.list` audit row) change, as do the roster assertions of `test_t011_teacher_class_profile_list_is_unchanged` and `test_class_scoped_teacher_a09_keeps_the_gate_and_its_audit_row`. The backend commit changes backend files and this record only; web, Bruno and the API test kit follow in their own sessions.
- Pages are single statements; across pages a newly consented, revoked or moved profile can appear, disappear or be missed; there is no snapshot token.
- The api-test-kit session reruns the Teacher and Manager blocks when the task lands.

**Not decided:** that an `effective` consent row is the grant of l.2586, BR-48 and AC-49 (the `REAL` branch is an interim placeholder and is re-based on the grant when the grant API exists); the consent API and the `effective` consent state (X-19), a separate later task outside goal v4; the Vietnamese wording of the empty state; any index for the keyset order; whether the aggregate count should become a separate consented count.

## D-066-101 — Phase B open items settled against the current SRS (2026-11-24)

**Source:** the owner's instruction of 2026-11-24 to settle the Phase B open items against the latest SRS (FEAT-063 v2.7-draft with Rev70 and Rev71, `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`). SRS references: BR-20 (l.266), FR-C-07 (l.501), FR-C-10 (l.504), the retention table (l.1065), the access matrix row for support notes (l.1609), the sensitive-data row (l.1925), the trace rows for `be1.profile_support_needs` (l.2311, l.2341, l.2502), BR-27 and BR-35, and the open-decision list §31.10 items 14 and 17. This record only settles what the SRS already supports. It does not change the SRS and does not sign it off.

**Decisions:**
1. **Key source for support-needs notes (O-SEED-KEY): not approved.** The SRS requires encrypted notes (l.1925) and names no key source or key service. Production keeps answering 503 `SUPPORT_NEEDS_UNAVAILABLE` on every call of both families until a key source is approved as a technical gate. No key source is added in this phase. Synthetic and test runs use an explicit test key only.
2. **Teacher narrow-permission store: deferred, default deny stays.** §31.10 item 14 keeps principal and assignment persistence OPEN-TECHNICAL, and the access matrix gives a Teacher no access to Parent support notes (l.1609). A Teacher keeps reaching support needs only through the BE1 routes, which are gated by the class assignment and the consent predicate. No permission store is built in goal v4.
3. **The two BE1 support-needs operations: kept in the operation catalog and counted under FR-C-07 and BR-20.** The SRS already carries `be1.profile_support_needs` in the trace (l.2311, l.2341, l.2502) but lists no route for it. The routes stay in the catalog. The SRS route table gets them in the next SRS revision, together with the Rev73 batch; this commit does not edit the SRS.
4. **Role split for `be1_purge_profile`: deferred to the deployment hardening gate.** The SRS fixes no database role model. The function keeps `REVOKE ALL FROM PUBLIC` and `SET search_path = pg_catalog, public`. A dedicated purge role is a release-hardening item before real data.
5. **FR-C-10 executor wiring: not part of goal v4.** FR-C-10 (l.504) says the Teacher delete role and the account-deletion policy must be settled before real data, and no goal v4 task covers the executor. The purge function covers the profile row, revisions, support needs, eligibility proofs and the child's receipts only; other child-keyed rows are listed as executor items. The executor is a separate later task and is a release gate for real data.
6. **Real child names in the revision table: release gate, synthetic only until then.** BR-27 keeps the demo synthetic-only until review, and l.504 and l.1065 leave the real-data lifecycle open. No real child data may enter the revision table before the executor (item 5), the key source (item 1) and the retention limit (§31.10 item 17) are closed.
7. **Deploy order: web before backend.** The web Teacher roster must follow `next_cursor`, use the count in its empty state and no longer expect the old 409 before the backend of this phase is deployed to any shared environment (see D-066-100).

**Not decided:** the key source and key custody; the Teacher permission persistence design; the Vietnamese wording of the SRS route additions; the dedicated purge role; the executor design; the retention duration for real data.

## D-066-102 - T-12b/T-12c Teacher web presentation choices (2026-11-24)

**Source:** the owner-launched plan `PLAN_V4B_FE_WEB_T-12BC_20261124.md`, revision 54, plus the final Phase B route list sections 3 and 4 and D-066-101.

**Decisions:**
1. Revision history is paged on demand at limit 100. The UI follows each opaque `next_cursor` only after the user selects the load-more action.
2. Support-needs values exist only in the open panel's component state. Reads use `cache: no-store`; the panel loads only after open and unmounts on close.
3. Support-needs 404, 503, and `CONSENT_NOT_EFFECTIVE` share one neutral unavailable state. A failed write in those states clears displayed and draft values.
4. Use the existing `teacherHttp.request` error model, which preserves `current_version` as `currentVersion`; do not duplicate the error parser.

These are web presentation and implementation choices only. They do not change the route contract, support-needs production defaults, or the open SRS operation-set question.

## D-066-103 - Preserve a same-key retry for a pending support-needs write (2026-11-24)

**Source:** T-12b/T-12c acceptance rule that an unclear write retry reuses its idempotency key, together with D-066-101's production defaults.

**Clarification to D-066-102 item 3:** a support-needs GET that returns 503 clears loaded and draft values. A 404 or `CONSENT_NOT_EFFECTIVE` response clears loaded values, draft values, and any pending write. If a PUT returns 503, the panel shows only the shared neutral unavailable copy and a generic retry action; it retains that pending payload and key only in the mounted component memory so the same user action can be retried. Closing the panel unmounts it and clears the payload and key.

No value is rendered in the unavailable state, stored in browser storage, placed in a URL, or logged.
