# FEAT-036 — UI direction alignment

## Goal

Turn the current UI review into a traceable, prioritized remediation plan for the Sketch2Life
product direction recorded in the owner-approved SRS and current ADRs.

## Initial review state — 2026-11-09

- At the initial review, product changes were `AWAITING_APPROVAL`; that review itself was limited to
  runtime screenshot evidence and made no product UI, API-contract, generated-art, or runtime
  configuration changes. Later owner approvals and implementation batches are recorded below.
- The active visual app entry is `apps/ui-mobile/App.tsx` → `BaoApp.tsx` with 15 mobile screens.
  `apps/mobile` contains a fixture-flow screen; `packages/art-renderer` contains the separate Pixi
  demo/player. `apps/parent-web` and `apps/child-app` contain boundary READMEs, not product UIs.
- Review authority: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` (owner-approved
  operational surfaces and B30–B33 changes), ADR-0012 (complete topic+age activity set), and
  ADR-0013 (Pixi subject-only behavior and reviewed companions).
- The original `ui-current-20261005` album is preserved. A separate `ui-full-20261005` album now
  contains 13 fresh emulator PNGs with no exact duplicate hashes: 11 active route components
  (Splash through Pixi Intro), one inline voice-recording state, and one activity-prerequisite
  state. The standalone Voice route and the Video Placeholder, Outdoor Activity, and Feedback routes
  were not reachable in the native flow. Gate A and Gate B were completed with synthetic input;
  Pixi renderer preparation then failed on retry, blocking the final three routes. The app's native
  React Native Dev Menu has runtime tools but no app-screen quick switch; the 15-screen switcher and
  `?screen=<id>` selector are Web-only, and Expo Web still leaves the root empty. The selected
  drawing is clear in the live Story Preview; the default-state thumbnail contrast finding remains
  only partially verified. Details, route coverage, and hashes are in
  `evidence/screenshots/ui-full-20261005/README.md`.

## Constraints

- Do not interpret UI visibility as authorization; backend policy remains authoritative.
- Do not revive the old readiness/material questionnaire for normal activity discovery.
- Do not label missing video as `READY`, conflate Pixi with illustrated video, or let a placeholder
  bypass required gates.
- Parent Web and Guide Console are target product surfaces in the current SRS. Their implementation
  needs their own scoped/approved work and must not receive an assumed team allocation here.
- Keep external providers, credentials, production data, asset-rights promotion, and deployment out
  of this task.

## Dependencies and open questions

- Video player/status UX depends on an approved versioned video contract and its owning runtime task.
- Parent Web / Guide Console scope and any web stack choice must be reconciled with the project
  context and recorded in an ADR before implementation.
- Current Android screenshots do not establish every screen or device size. A fresh device matrix is
  part of the proposed verification plan.

## Supplemental review — 2026-11-09

- Completed a static source review of the Parent, Teacher, School Manager, and Platform Admin web
  surfaces on origin/FE_UI_Project (c384dcc). The prioritized findings, source references,
  integration blockers, and review limits are recorded in
  evidence/notes/FE_UI_PROJECT_REVIEW_20261109.md.
- The review used the repository instructions' current FEAT-063 v2.7-draft baseline. The target
  branch's source register still says v2.5-draft; synchronize that authority drift before product
  changes or requirement sign-off.
- The source review made no UI source, runtime configuration, plan, or approval-record changes.
  A follow-up owner-requested local browser capture produced 37 synthetic-preview PNGs under
  evidence/screenshots/fe-ui-project-20261109/ (Parent 21, Teacher 10, School Manager 3,
  Platform Admin 3). No tests or builds were run. Product implementation remains
  AWAITING_APPROVAL.

## Supplemental Parent UX review — 2026-11-09

- Reviewed the running Parent portal’s captured mobile flow against FEAT-063 v2.7-draft Rev57 and
  the `ui-ux-pro-max` and `code-reviewer` skills. Findings and limits are recorded in
  `evidence/notes/PARENT_UI_UX_REVIEW_20261109.md`.
- The highest-priority mismatch is the mandatory pre-video activity selection; the post-video UI
  then exposes only that selected activity. Other findings cover age bounds, Parent completion
  toggles, BGM controls, login validation/copy, assistive-technology semantics, and small touch
  targets.
- Parent Web acceptance scope remains open in the SRS, which describes Parent Android. The review
  was read-only; the later owner approval is recorded in revision 3 and does not resolve that open
  product question.

## Approved implementation batch — 2026-11-09

- The owner approved plan revision 3 to fix only the seven prioritized Parent findings in
  `plan/PLAN_REV3_PARENT_UI_SEVEN_FIXES.md`; its SHA-256 is recorded in
  `approvals/TASK_APPROVAL.md`.
- Broad redesign, general copy reduction, and the other three portals are deferred to a later owner
  request. Parent Web target scope and Parent runs without a lesson preset remain open SRS questions.
- The seven approved fixes are implemented. Manual preview findings and screenshots are recorded
  in `evidence/notes/PARENT_UI_SEVEN_FIXES_IMPLEMENTATION_20261109.md` and its screenshot folder.
  FEAT-036 remains active after this bounded Parent batch.

## Approved Parent login animation — 2026-11-09

- The owner approved plan revision 4 to apply the supplied animated splash artwork to the existing
  Parent login presentation while retaining the current UI colors. The exact scope and acceptance
  criteria are in `plan/PLAN_REV4_PARENT_LOGIN_ANIMATION.md`; the approval hash is in
  `approvals/TASK_APPROVAL.md`.
- The archive contains a standalone splash animation rather than a login form. This scope adapts its
  background and pencil artwork into the existing login page. The current `Wordmark`, form fields,
  authentication guard, preview action, notices, routing, and onboarding behavior are retained.
- Only the supplied background and pencil assets are approved for application. The archive's
  purple/amber logo image is excluded to preserve the existing wordmark palette. Source and copied
  asset hashes are recorded in `assets/manifests/PARENT_LOGIN_ANIMATION_20261109.asset.json`.
- Parent Web remains an open target-client question in the canonical FEAT-063 SRS review; this
  request authorizes a visual change to the existing local UI only and does not resolve the product
  scope question.
- The login hero is implemented with CSS motion and a reduced-motion state. Vite returned HTTP 200
  for the page module, stylesheet, and selected image assets. A rendered screenshot could not be
  captured because the local Edge CDP page did not respond; pixel-level visual review remains
  pending. Details are in `evidence/notes/PARENT_LOGIN_ANIMATION_IMPLEMENTATION_20261109.md`.

## Parent login UX restructure — 2026-11-09

- The owner explicitly requested rebuilding the login structure because its UX was wrong. Plan
  revision 5 and the bounded authorization are recorded in the feature plan and
  `approvals/TASK_APPROVAL.md`; this supersedes revision 4's preserve-onboarding constraint only
  for the login flow/layout.
- `/p11-authentication` now opens directly to sign-in. The existing three-step introduction is an
  optional action, local preview has its own action outside the credential form, and the unsupported
  registration toggle is removed. Password visibility has an accessible, touch-sized control;
  real sign-in still uses the existing Firebase bridge and role-resolution contract.
- The approved background/pencil animation and current `Wordmark` palette are retained. The
  transformed module and stylesheet returned HTTP 200 from the running Vite server, and
  `git diff --check` passed. No automated tests/builds were run. Responsive pixel-level review is
  still pending because the local Edge CDP capture did not respond, as recorded in revision 4's
  evidence.
- Parent Web target-client scope remains open in the canonical FEAT-063 SRS. This local UI change
  does not resolve that product question.

## Parent login rebuilt from supplied ZIP — 2026-11-09

- The owner clarified that the complete supplied ZIP should be carried into the login, with the
  current UI colors retained. Plan revision 6 and authorization are recorded in the feature plan
  and `approvals/TASK_APPROVAL.md`; revision 6 supersedes revision 5's compact visual composition.
- The archive contains a standalone splash, not a login form. Its exact source component, styles,
  logo, background, pencil, and four sparkle positions are preserved under FEAT-036 evidence and
  asset provenance. The route now uses the full-height scene behind the working sign-in panel.
- The original animation sequence's 80 ms/840 ms pencil entrance, 380 ms/520 ms logo entrance,
  sparkle stagger, and 1.02 s pencil float are adapted with native animation math; reduced-motion
  users receive the final static composition. Form and preview continue to use the existing auth
  and preview handlers.
- Vite returned HTTP 200 for the route/module/style during source inspection, and the new asset
  imports resolve to the approved/applied copies. Responsive rendered review remains pending; this
  change does not settle Parent Web target scope in FEAT-063.

## Parent login transition and recovery — 2026-11-09

- The owner supplied a screen recording and account/security screenshot, then approved plan revision
  7 to transition from the ZIP splash to the login form and move recovery from Settings to login.
- First login entry per browser session now shows the full-screen ZIP animation before revealing the
  form. Returning from recovery does not replay it; reduced-motion users receive the final scene and
  login form immediately.
- `/p14-password-recovery` is a separate public route linked from login and receives the entered
  email as a prefill. Its UI clearly states that email recovery is not connected and does not fake
  OTP delivery or reset success.
- The Settings “Quên mật khẩu” row and its local OTP mock were removed; “Đổi mật khẩu” remains.
- Vite served the route, transformed module, stylesheet, and three applied assets with HTTP 200;
  `git diff --check` passed. No automated tests/builds were run. Rendered pixel review remains
  pending because the local browser capture did not respond. Details are recorded in
  `evidence/notes/PARENT_LOGIN_TRANSITION_AND_RECOVERY_20261109.md`.

## Parent password-recovery visual refinement — 2026-11-09

- The owner approved revision 8 to polish the already separate recovery page. The work uses the
  existing blue/cream palette and a code-native envelope/lock illustration; no new asset or
  dependency was introduced.
- The page now has a clearer brand/back header, centered card hierarchy, email field with leading
  envelope icon, concise unavailable notice, and a focused recovery action. Dark mode and reduced
  motion are supported; email prefill, return navigation, and no-fake-send behavior remain.
- Vite served the transformed page module and stylesheet with HTTP 200; `git diff --check` passed.
  The route is open in the local in-app browser for inspection. No automated tests/builds were run.
  Implementation details are in
  `evidence/notes/PARENT_PASSWORD_RECOVERY_VISUAL_REFINEMENT_20261109.md`.

## Real-device status bar and safe area — 2026-11-10

- The owner flagged the simulated `9:41`/signal/Wi-Fi/battery row as a real-mobile issue. Revision 9
  keeps this chrome for desktop phone preview and hides it at narrow widths or on touch-first devices.
- The Parent viewport now opts into `viewport-fit=cover`. Ordinary mobile routes receive the top
  safe-area inset from the app shell; login/recovery pages keep their own inset handling, avoiding
  duplicate top padding. Bottom tab navigation retains its existing safe-area padding.
- Vite served the route, transformed layout module, and shared stylesheet with HTTP 200;
  `git diff --check` passed. No automated tests/builds were run. Details are recorded in
  `evidence/notes/REAL_DEVICE_STATUS_BAR_SAFE_AREA_20261110.md`.

## Centered create-story navigation shortcut — 2026-11-10

- The owner requested a prominent camera shortcut in the center of the Parent bottom navigation.
  Plan revision 10 and authorization are recorded in `approvals/TASK_APPROVAL.md`.
- The center action appears between the existing tabs in both the four-item local-preview and
  two-item product-nav configurations. It uses the current palette, a large camera affordance,
  the short label “Tạo”, and an accessible descriptive name.
- Activating it reuses the Home hero's existing capture-first route, optional-setup skip state, and
  no-quota warning. No story-flow or backend logic changed.
- Vite served the transformed layout module and shared stylesheet with HTTP 200; `git diff --check`
  passed. No automated tests/builds were run. Details are in
  `evidence/notes/PARENT_CREATE_STORY_NAV_SHORTCUT_20261110.md`.

## Remove unsupported Parent 2FA controls — 2026-11-10

- The owner confirmed that the current Parent 2FA UI should be removed. Revision 11 and its
  authorization are recorded in `approvals/TASK_APPROVAL.md`.
- Parent Settings no longer contains the two-factor row, subview, default-enabled toggle, method
  selector, or hard-coded/re-generated recovery codes. Password change and other account settings
  remain.
- The current FEAT-063 SRS requires MFA for organization and billing administrators but does not
  establish Parent-account 2FA or its methods. This UI removal leaves the Parent product question
  open and does not alter administrator requirements.
- Verification and the consolidated release scope are recorded in
  `evidence/notes/PARENT_2FA_REMOVAL_AND_UI_RELEASE_20261110.md`.
