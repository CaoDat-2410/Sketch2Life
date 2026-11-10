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
