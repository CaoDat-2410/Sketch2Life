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

## D-066-71 - Goal v4 Phase A Parent Android integration order (2026-11-23)

**Source:** the owner-launched Phase A task prompt and `tmp/phase-v4/PHASE_A_FINAL_ROUTE_LIST_20261123.md`, sections 1, 2.3-2.10, 3.1-3.5 and 4. The task plan hash is recorded in the Phase A entry in `approvals/TASK_APPROVAL.md`.

- Parent confirms the subject, loads and selects an activity, then confirms context. Whichever of activity selection or context confirmation succeeds last starts the first story.
- First-story start is implicit in those gates; the Parent flow does not call legacy `story-revisions` for it.
- `story_confirmation_required` is authoritative when present. The app re-confirms the same story revision after a spent video review, and only then offers another video request.
- Current safety blocks route through `SCRIPT_REVIEW` plus video/job fields. The `SAFETY_BLOCKED` run state remains accepted for legacy rows.
- `post_video_activities: null` is normal. A completed run may be read and played again through a fresh playback grant.

This records the implementation contract for this task only. It does not sign off FEAT-063 SRS v2.7-draft or approve a tech-stack decision.
