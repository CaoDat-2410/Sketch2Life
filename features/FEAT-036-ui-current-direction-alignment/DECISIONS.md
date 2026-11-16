# FEAT-036 decisions

## D-036-01 — Review only; no implementation approval

The owner requested an audit, prioritized findings, and a fix task while explicitly saying not to
implement. This feature records that review and its proposed work only. Product changes remain
`AWAITING_APPROVAL`; this request does not approve implementation.

## D-036-02 — Use the current owner-approved requirements as the UI target

Use the master SRS B21 and B30–B33 plus ADR-0012/0013 to evaluate UI. The stale
`apps/parent-web/README.md` statement that the web split is inactive does not override the newer SRS
scope closure. Reconcile the duplicated project-context statements before any web implementation.

## D-036-03 — Keep cross-feature work separately gated

Missing Parent Web, Guide Console, and illustrated-video runtime are recorded as product-surface
gaps. They need separately scoped/approved work and an explicit owner/allocation; this audit does not
assign them to a person or silently expand the mobile UI implementation scope.

## D-036-04 — Keep runtime captures distinct from design mockups

The screenshot album contains native emulator captures; existing screen PNGs under
`apps/ui-mobile/assets/images/` remain design assets and cannot stand in for runtime screenshots.
The source includes a 15-screen Web developer switcher (`?dev=true`) and direct screen selection
(`?screen=<id>`), but Expo Web stays blank with an empty root on local hostnames. `index.ts`
registers the app with `AppRegistry` without Expo's web root bootstrap, which appears to block this
capture route. The Android `Pixel 10` emulator now runs the app and exposes the standard React Native
Dev Menu (Bridge), but that menu has no app-route selector. Five of the 15 active screens have
runtime evidence; ten remain uncaptured. Current runtime evidence does not reproduce the earlier
Home inset overlap or solid-color story thumbnails, while the default Story Preview looks washed
out and needs a fully selected-drawing comparison. Product implementation remains
`AWAITING_APPROVAL`.

## D-036-05 — Keep runtime debug tools separate from app screen selection

The Android emulator's React Native Dev Menu is a real native debug menu (Reload, Open DevTools,
Change Bundle Location, Inspector, and related tools). It is not the app's 15-screen quick switch.
That quick switch and direct `?screen=<id>` route are Web-only. Keep the remaining screen coverage
open until a capture path is approved and available; do not treat the native Dev Menu as evidence
that all routes were reviewed.

## D-036-06 — Reclassify Home visual issues after current-runtime capture

The preserved Home screenshot suggested system-inset overlap and blank-colored story thumbnails.
Current Pixel 10 runtime evidence does not reproduce either issue: Home content respects visible
status/gesture areas and both story illustrations render. Do not schedule those fixes from the stale
capture. Keep safe-area verification in the device matrix and reopen image handling only if another
current device reproduces it. Story Preview's default placeholder remains a contrast check, not a
confirmed defect.

## D-036-07 — Record FE_UI_Project as a separate source-only review

The 2026-11-09 review covers the Parent, Teacher, School Manager, and Platform Admin web surfaces
on origin/FE_UI_Project and is recorded in
evidence/notes/FE_UI_PROJECT_REVIEW_20261109.md. Evaluate product behavior against the
repository instructions' FEAT-063 v2.7-draft baseline; the target branch's v2.5 source-register
references are documented as authority drift. This decision records review scope and evidence only:
it does not change product requirements, approve implementation, or alter the feature's
AWAITING_APPROVAL status.

## D-036-08 — Store the owner-requested FE portal screenshot set as evidence

The 2026-11-09 local preview capture contains 37 route/screen PNGs for the Parent, Teacher,
School Manager, and Platform Admin portals. The route index, per-screen manifest, and archive are
stored under evidence/screenshots/fe-ui-project-20261109/ and
evidence/FE_UI_Project_Screenshots_20261109.zip. Captures use synthetic preview data and do not
represent backend-authenticated production states. This records review evidence only; it does not
approve UI implementation or change AWAITING_APPROVAL.

## D-036-09 — Record the Parent UX/SRS review as evidence only

The 2026-11-09 Parent portal review applies the repository’s canonical FEAT-063 v2.7-draft Rev57
and the `ui-ux-pro-max` and `code-reviewer` review guidance. The findings and verification limits
are recorded in `evidence/notes/PARENT_UI_UX_REVIEW_20261109.md`. The Parent Web target surface
remains an SRS scope question because the canonical persona describes Parent Android. This decision
records the review only; implementation approval is recorded separately in D-036-10.

## D-036-10 — Approve the seven Parent UI fixes

On 2026-11-09 the owner explicitly approved plan revision 3, whose SHA-256 is
`8DC17AE1791AFEB39A9FCC85DCD8059CD6D4C3C49D4A2840D3E97B679CF55048`. The authorized work is
limited to the seven prioritized findings in `evidence/notes/PARENT_UI_UX_REVIEW_20261109.md` on
the Parent portal: activity sequencing and content, 36–120-month validation, removal of Parent
activity completion recording, background-music controls, login validation and copy, accessible
step semantics, and 44 px touch targets. General redesign and copy reduction, other portals,
backend work, and the open Parent Web and no-preset product questions remain outside this approval.

## D-036-11 — Record completion of the approved Parent UI fixes

The seven fixes approved by D-036-10 were implemented on the FE_UI_Project remediation worktree.
The implementation record, scope limits, manual-preview results, and screenshots are stored in
`evidence/notes/PARENT_UI_SEVEN_FIXES_IMPLEMENTATION_20261109.md` and
`evidence/screenshots/parent-ui-seven-fixes-20261109/`. The 430×932 preview showed both activities
after playback and validation for an invalid 121-month age in both profile forms; landscape playback
was inspected at 932×430 with its controls visible and no music toggle. No automated tests or builds
were run. FEAT-036 remains active; broader UI optimization and copy reduction are deferred.

## D-036-12 — Approve the supplied Parent login animation

On 2026-11-09 the owner explicitly approved plan revision 4, whose SHA-256 is
`C34CC3D4D0BA996785E4E1A6DC5881DF2F0D5971D407C950748A119D7C47EDF7`. Apply the supplied
background and pencil artwork to the existing Parent login hero, retain the existing product
`Wordmark` and blue UI tokens, and keep authentication behavior and onboarding unchanged. The
archive's purple/amber logo image is excluded to preserve the current palette. Asset provenance and
the owner's visual approval are recorded in `assets/REVIEW.md` and
`assets/manifests/PARENT_LOGIN_ANIMATION_20261109.asset.json`. Parent Web target-client scope remains
open; this visual-only request does not resolve it.

## D-036-13 — Record Parent login animation implementation and review limit

The revision-4 hero is implemented with the approved background and pencil assets, the current
`Wordmark`, blue UI tokens, and CSS motion with a reduced-motion state. The existing login behavior
was preserved. Vite served the page module, stylesheet, and selected images successfully. A rendered
screenshot was not captured because the local Edge CDP page did not respond, so pixel-level visual
review remains pending. See `evidence/notes/PARENT_LOGIN_ANIMATION_IMPLEMENTATION_20261109.md`;
keep FEAT-036 active until visual review is completed.

## D-036-14 — Approve the Parent login UX restructure

On 2026-11-09 the owner explicitly requested rebuilding the Parent login UX because its structure
was wrong. Plan revision 5, SHA-256
`42FECC6E3EEF15D7FDFEC777413050B78F8DDA60BE780984F0E6E58517143113`, makes sign-in the first
task, separates local preview from credential submission, and removes the unsupported registration
action. It keeps the revision-4 approved background/pencil artwork and current palette, preserves
the existing auth contract, and makes the introduction optional. This is local Parent UI scope only;
it does not resolve Parent Web's open target-client question or authorize backend/auth changes.

## D-036-15 — Record Parent login UX implementation and verification limit

The revision-5 login structure is implemented in `P11AuthenticationPage` and its feature-local
stylesheet. Vite served the transformed module and CSS with HTTP 200; the module no longer includes
the unsupported registration toggle and retains distinct authentication and local-preview paths.
`git diff --check` passed; no automated tests/builds were run. A responsive rendered screenshot was
not captured because the local Edge CDP page did not respond, so pixel-level review remains pending.
See `evidence/notes/PARENT_LOGIN_UX_RESTRUCTURE_20261109.md`; keep FEAT-036 active until visual
review is complete.

## D-036-16 — Approve complete ZIP-based Parent login rebuild

On 2026-11-09 the owner explicitly directed that the complete supplied
`h-y-tri-n-khai-animated.zip` design be carried into the login while retaining the current UI colors.
Plan revision 6, SHA-256
`8DBBFDBA5172906ED59322498B3BC1EF67A0E0A4A997B4FA53F75FE07DBF6AF0`, therefore includes the
archive's background, logo, pencil, full-screen composition, four sparkle positions, and original
animation sequence. Since the ZIP is a splash screen with no login or auth code, the working Parent
sign-in form remains on the same route and uses the existing Firebase bridge. The local preview
remains separate. This supersedes revision 5's compact visual composition and optional introduction
only; it does not authorize backend/auth changes or resolve the open Parent Web scope question.

## D-036-17 — Record ZIP-based login implementation and visual-review status

The Parent login now uses the complete source composition and all three owner-provided raster
assets, with the source timing, stagger, and easing adapted to a native animation loop. The working
login and separate local preview remain available. Vite returned HTTP 200 for the route, transformed
module, stylesheet, and source asset imports. No automated tests/builds were run. Responsive
rendered visual review remains pending; see
`evidence/notes/PARENT_LOGIN_ZIP_REBUILD_20261109.md` and keep FEAT-036 active until that review is
complete.

## D-036-18 — Approve the login transition and move password recovery out of Settings

On 2026-11-09 the owner supplied a login-transition recording and Settings screenshot and approved
plan revision 7, SHA-256
`5EEF05DCEDE49C7AFA13B67A9D83D504DBCF977A381AEBB69D8FE6850B8654D7`. The login now plays the
ZIP splash before revealing the sign-in form, with a one-time-per-session transition and a
reduced-motion path. Recovery is linked from login through a separate public route; the Settings
recovery row and fake OTP flow are removed while “Đổi mật khẩu” remains. Because no reset operation
exists in the current auth bridge/API, the recovery UI reports that it is unavailable and does not
claim delivery or success. Implementation evidence and the browser-capture limit are recorded in
`evidence/notes/PARENT_LOGIN_TRANSITION_AND_RECOVERY_20261109.md`. Pixel-level visual review remains
pending.

## D-036-19 — Approve and record password-recovery visual refinement

On 2026-11-09 the owner requested a more polished password-recovery UI and approved plan revision
8, SHA-256 `B25E757BCDCE8F7D2354F6D745B8955067734FAB1872C343AF93F0576F589859`. The recovery page
now uses the current palette, a code-native envelope/lock illustration, a clearer email field and
unavailable notice, and responsive light/dark styling. It preserves email prefill and return to
login. No external asset, backend/auth operation, email send, OTP, or success claim was added. Source
and Vite evidence are recorded in
`evidence/notes/PARENT_PASSWORD_RECOVERY_VISUAL_REFINEMENT_20261109.md`.

## D-036-20 — Record the real-device status-bar and safe-area fix

On 2026-11-10 the owner flagged the static simulated status row as a problem on real mobile devices.
Approved plan revision 9, SHA-256
`F8DE86A9EF812B2B74468FFA83411D0A804CDB71E01847138F20EE1C074FD4CE`, hides the simulated row at
narrow widths and on touch-first devices while retaining desktop phone-preview chrome. The viewport
opts into `viewport-fit=cover`; the shell applies the safe-area inset to ordinary pages while login
and recovery retain their own inset handling. Native system-bar configuration is out of scope.
Verification is recorded in `evidence/notes/REAL_DEVICE_STATUS_BAR_SAFE_AREA_20261110.md`.

## D-036-21 — Add a centered camera shortcut to Parent navigation

On 2026-11-10 the owner requested a large camera action at the center of the Parent bottom navbar
as a shortcut into story creation. Approved plan revision 10, SHA-256
`F7BF53C0BA681C0874699545E1D4CF3783DAF4C924E4DDD6FB5C779003761547`, inserts a prominent,
accessible “Tạo” action between existing destinations in both preview and product-nav variants. It
reuses the current capture-first route, optional-setup skip state, and quota warning from the Home
hero. Existing destinations remain in their current order; no backend/flow change was made. Evidence
is recorded in `evidence/notes/PARENT_CREATE_STORY_NAV_SHORTCUT_20261110.md`.

## D-036-22 — Remove unsupported Parent 2FA UI

On 2026-11-10 the owner confirmed that the current Parent 2FA UI should be removed. Approved plan
revision 11, SHA-256
`C6C29A3C3E2B56AEE304306EA1417DCFCEE119FAD23D28E651D6DF19D6AE0289`, removes the Parent Settings
row, simulated enabled state, authenticator/email selector, and placeholder backup codes. The
current FEAT-063 SRS requires MFA for organization and billing administrators but does not establish
Parent-account 2FA or supported methods; this decision leaves that open question unresolved. The
password-change row and other settings remain. Evidence is recorded in
`evidence/notes/PARENT_2FA_REMOVAL_AND_UI_RELEASE_20261110.md`.
