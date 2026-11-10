# FEAT-036 status

- Status: ACTIVE
- Updated: 2026-11-10
- Plan revision: 16
- Implementation status: COMPLETE for the approved Parent UI batches in revisions 3–16. Revision 16 adds touch-first tablet spacing, bounded landscape content/navigation, larger controls, and a landscape quota layout. Its main tablet screenshots were reviewed; a final landscape Home density refinement was applied after those captures, so that exact final state still needs a rendered screenshot review.
- Approval gate: APPROVED by the owner for plan/PLAN_REV16_PARENT_TABLET_LAYOUT.md; SHA-256 A48D81C858DB9B5E6AEC754AE466DDD2C6460875D11F73DBB70A6DF939AD5932 is recorded in approvals/TASK_APPROVAL.md.
- Product authority: Used FEAT-063 SRS v2.7-draft as required by the current repository instructions. The task worktree’s authority copy still records v2.5-draft; this drift remains open and was not changed.
- Current milestone: FEAT-036 remains active for future approved all-portal work and the outstanding
  rendered visual and physical-device checks documented below.
- Scope boundary: General redesign, broad copy reduction, and Teacher, School Manager, and Platform
  Admin work are deferred. Parent Web target-client scope and behavior for runs without a lesson
  preset remain open SRS questions. FEAT-036 stays active for later approved all-portal work.
- Revision 3 verification: The 430×932 local preview was manually inspected for the changed Parent screens;
  landscape playback was inspected at 932×430. Both child-age forms showed validation at 121 months,
  the create dialog remained open after an attempted save, the post-video list rendered both lesson
  activities, and no JavaScript runtime errors were observed in the captured route sequence. The
  approved `git diff --check` passed. No automated tests or builds were run.
- Revision 3 evidence: `evidence/notes/PARENT_UI_SEVEN_FIXES_IMPLEMENTATION_20261109.md` and
  `evidence/screenshots/parent-ui-seven-fixes-20261109/`.

## Revision 4 review gate

- Approved scope: Parent login hero artwork, palette, and motion behavior.
- Implementation note: `evidence/notes/PARENT_LOGIN_ANIMATION_IMPLEMENTATION_20261109.md`.
- Automated tests/builds were outside the approved revision-4 verification scope.
- Current limit: Vite served the page module, stylesheet, and PNGs successfully, but the local Edge
  CDP page did not respond, so a rendered screenshot and pixel-level review remain pending.

## Previous evidence

The preserved Android evidence from the earlier revision includes `ui-full-20261005` with 13
non-duplicate PNGs. The native React Native Dev Menu has no app-screen quick switch; the 15-screen
switcher remains Web-only and Expo Web still does not mount. Pixi renderer preparation failed after
retry, so Video Placeholder, Outdoor Activity, and Feedback could not be reached; the standalone
Voice route is not connected from the current Capture flow. These are historical limits of that
Android capture and are separate from the current Parent portal preview review.

The current Parent portal capture contains synthetic preview data and does not establish
backend-authenticated behavior. The canonical SRS describes Parent Android; this bounded approval
does not resolve whether Parent Web is a supported target client.

## Revision 5 implementation — Parent login UX restructure

- This revision's compact hero and optional intro were superseded by revision 6 after the owner
  requested the complete supplied ZIP composition.
- Approved scope: make sign-in the immediate primary task, separate local preview, and retain the
  approved animation and current palette. Plan 5 and its owner authorization are recorded in the
  feature plan and approval log.
- Implementation status: `IN_PROGRESS`; component and styles are updated, while rendered responsive
  visual review remains pending because the local Edge CDP capture issue recorded for revision 4
  prevents screenshot inspection.
- Source verification: Vite returned HTTP 200 for the transformed Parent login module and its
  stylesheet. The transformed module contains the direct login and separate preview actions, has no
  Vite transform error, and no longer contains the unsupported registration action. `git diff
  --check` passed. No automated tests or builds were run.
- Evidence: `evidence/notes/PARENT_LOGIN_UX_RESTRUCTURE_20261109.md`.

## Revision 6 implementation — Rebuild from the supplied ZIP

- Approved scope: transfer the supplied full-screen splash composition, background/logo/pencil
  assets, four sparkles, and animation sequence while retaining the current UI colors and functional
  Parent sign-in. Approval is recorded in `approvals/TASK_APPROVAL.md`.
- Implementation status: `IN_PROGRESS`; the source-based scene, login panel, and provenance records
  are in place. Responsive rendered visual review remains pending.
- Source verification: Vite returned HTTP 200 for the transformed page module, stylesheet, and
  `/p11-authentication` route. Direct sign-in and separate preview code remain present; no Vite
  transform error was returned. No automated tests/builds were run.
- Evidence: `evidence/notes/PARENT_LOGIN_ZIP_REBUILD_20261109.md`.

## Revision 7 implementation — Login transition and password recovery

- Approved scope: transition from the full-screen ZIP splash to login; move password recovery to a
  dedicated public route; remove the Settings recovery row and fake OTP behavior. Approval is
  recorded in `approvals/TASK_APPROVAL.md`.
- Implementation status: `IN_PROGRESS`; source changes and evidence are recorded. Rendered visual
  review remains pending because the local Edge CDP page did not respond.
- Source verification: Vite returned HTTP 200 for the recovery route, transformed Parent screen
  module, styles, and all three applied splash assets. `git diff --check` passed. No automated
  tests/builds were run.
- Evidence: `evidence/notes/PARENT_LOGIN_TRANSITION_AND_RECOVERY_20261109.md` and
  `evidence/raw/login-transition-video-20261029/`.

## Revision 8 implementation — Password recovery visual refinement

- Approved scope: refine `/p14-password-recovery` visuals and responsive styling only. Approval is
  recorded in `approvals/TASK_APPROVAL.md`.
- Implementation status: `IN_PROGRESS`; the recovery page source and styles are updated. The route
  is open in the local in-app browser; pixel-level screenshot evidence was not captured.
- Source verification: Vite returned HTTP 200 for the transformed module and stylesheet; the module
  contains the new envelope illustration and the CSS contains the recovery layout and dark-theme
  styles. `git diff --check` passed. No automated tests/builds were run.
- Evidence: `evidence/notes/PARENT_PASSWORD_RECOVERY_VISUAL_REFINEMENT_20261109.md`.

## Revision 9 implementation — Real-device status bar and safe area

- Approved scope: retain simulated status chrome in the desktop phone preview and hide it on narrow
  mobile or touch-first viewports; reserve the top safe area for native status chrome. Approval is
  recorded in `approvals/TASK_APPROVAL.md`.
- Implementation status: `IN_PROGRESS`; the Parent shell, mobile media rules, and viewport metadata
  are updated. Visual review on physical hardware remains pending.
- Source verification: Vite returned HTTP 200 for the recovery route, transformed `MobileLayout.tsx`,
  and `apps/shared/parent-ui.css`. The responsive CSS contains the touch/mobile rule, and the shell
  passes page-vs-shell safe-area ownership. `git diff --check` passed; no automated tests/builds ran.
- Evidence: `evidence/notes/REAL_DEVICE_STATUS_BAR_SAFE_AREA_20261110.md`.

## Revision 10 implementation — Centered create-story navigation shortcut

- Approved scope: add a prominent center camera control between existing bottom-nav destinations.
  Approval is recorded in `approvals/TASK_APPROVAL.md`.
- Implementation status: `IN_PROGRESS`; local-preview and product-nav configurations use the same
  center shortcut. Visual inspection is pending.
- Source verification: Vite returned HTTP 200 for the transformed `MobileLayout.tsx` and shared
  Parent stylesheet. The component retains all tab links and invokes the existing capture-first
  flow with its optional-step skip and quota warning. `git diff --check` passed; no automated
  tests/builds were run.
- Evidence: `evidence/notes/PARENT_CREATE_STORY_NAV_SHORTCUT_20261110.md`.

## Revision 11 implementation — Remove unsupported Parent 2FA UI

- Approved scope: remove the simulated Parent 2FA row, detail screen, state, method selector, and
  placeholder recovery codes. Approval is recorded in `approvals/TASK_APPROVAL.md`.
- Implementation status: `COMPLETE`; the Parent Settings UI and the accumulated approved Parent UI
  batch are ready for one-commit publication.
- Source verification: the source scan, Vite route/module checks, and governance checks are recorded
  in `evidence/notes/PARENT_2FA_REMOVAL_AND_UI_RELEASE_20261110.md`.
- Evidence: `evidence/notes/PARENT_2FA_REMOVAL_AND_UI_RELEASE_20261110.md`.

## Revision 12 implementation — Compact preview and recovery auth alignment

- Approved scope: compact the Parent sign-in local-preview panel and align the dedicated recovery route with the auth visual system. Approval is recorded in approvals/TASK_APPROVAL.md.
- Implementation status: COMPLETE. Recovery reuses the approved login scene and shared auth panel styles. The preview card retains a 44 px action and fits at 320 px width.
- Visual verification: Edge mobile CSS viewports at 375×812 and 320×568. Login preview document scroll widths matched viewport widths; panel bounds were 311×60 px and 264×70.4 px. Recovery document scroll widths matched viewport widths; the full form and return control fit within both screenshots. Exact bounds and SHA-256 hashes are in evidence/notes/PARENT_AUTH_UI_REFINEMENT_20261110.md.
- Source verification: Vite returned HTTP 200 for both auth routes, ParentScreens.tsx, and parent-login-animation.css. git diff --check exited successfully; Git emitted CRLF-to-LF normalization warnings for the modified FEAT-036 Markdown files. No whitespace errors were reported. No automated tests or production build were run.
- Evidence: evidence/notes/PARENT_AUTH_UI_REFINEMENT_20261110.md and local screenshots under evidence/screenshots/parent-auth-revision12/.
- Limit: the screenshots use synthetic local preview state, not a physical device or authenticated production account. Parent account-recovery behavior and Parent Web target scope remain open in the canonical SRS.

## Revision 13 implementation — Parent registration UI and sign-in entry

- Approved scope: add the Parent registration presentation at /p15-parent-registration and an accessible “Chưa có tài khoản? Đăng ký” entry on sign-in. Approval and plan hash are recorded in approvals/TASK_APPROVAL.md and plan/PLAN_REV13_PARENT_REGISTRATION_UI_AND_AUTH_LINK.md.
- Implementation status: COMPLETE for the visual-only scope. The screen uses the existing auth art and panel system, labeled email/password/confirmation fields, show/hide controls, an unavailable status, and a return-to-sign-in action. Email is passed through route state; passwords are not.
- Behavior boundary: the registration UI does not create accounts or call auth/backend services. It clearly states that no account was created. Parent registration UX remains open in the canonical FEAT-063 SRS v2.7-draft.
- Visual verification: the sign-in link and registration route were followed in a rendered local preview at 375×812 and 320×568. Document widths matched the viewport; the sign-in panel measured 343×487 and 288×475 px, and the registration panel measured 343×520 and 288×503 px. Evidence hashes and route/module responses are in evidence/notes/PARENT_REGISTRATION_UI_AND_AUTH_ENTRY_20261110.md.
- Source verification: Vite returned HTTP 200 for /p15-parent-registration, ParentScreens.tsx, and App.tsx. No automated tests or production build were run.
- Evidence: evidence/notes/PARENT_REGISTRATION_UI_AND_AUTH_ENTRY_20261110.md and local-only screenshots under evidence/screenshots/parent-registration-rev13/.
## Revision 14 implementation — Parent auth tablet layout

- Approved scope: adapt Parent sign-in, password recovery, and registration for portrait and landscape tablets while preserving phone layouts. Plan revision 14 and its SHA-256 are recorded in approvals/TASK_APPROVAL.md.
- Implementation status: COMPLETE for visual/responsive scope. At touch-first tablet widths the existing auth illustration and 420 px form panel use a two-column composition; auth controls are at least 52 px high and safe-area padding is applied.
- Rendered review: touch-emulated Edge at 768×1024 portrait and 1024×768 landscape. All three routes were inspected at both sizes. Document width matched viewport width. Panel bounds: portrait sign-in 420×551 at x316,y237; recovery 420×394 at x316,y315; registration 420×562 at x316,y231. Landscape sign-in 420×560 at x572,y104; recovery 420×403 at x572,y182; registration 420×571 at x572,y98.
- Existing phone review from revision 13 remains at 375×812 and 320×568; tablet rules start at 700 px. Screenshot hashes are in evidence/notes/PARENT_AUTH_TABLET_LAYOUT_20261110.md; the PNGs remain local under evidence/screenshots/parent-auth-tablet-rev14/ because repository ignore rules exclude them.
- Vite returned HTTP 200 for all three auth routes, ParentScreens.tsx, and parent-login-animation.css. git diff --check passed with Git line-ending normalization warnings only. No automated tests/builds were run.
- This is presentation-only; Parent Web target scope and Parent registration/recovery requirements remain open in canonical FEAT-063 SRS v2.7-draft.
## Revision 15 implementation — Parent auth guard on hard refresh

- Approved scope: send Parent users without a session to /p11-authentication after direct route loads or F5, while restoring an existing Firebase session before resolving protected routes. Plan revision 15 and its SHA-256 are recorded in approvals/TASK_APPROVAL.md.
- Root cause: ParentContext initialized isAuthenticated from isLocalPreview(). On localhost without the auth bridge, local-preview mode evaluates true, so refreshing /p01-lesson-library incorrectly appeared authenticated.
- Fix: authentication now starts signed out. Local preview requires explicit selection and stays in memory only. At startup, the existing auth bridge is checked for an ID token and backendApi.parentLessons() confirms Parent access; the route guard waits for both checks, then redirects signed-out users to authentication.
- Manual browser check: opening /p01-lesson-library in the local Vite preview with no session rendered the Parent auth scene; the lesson library content was absent. Vite returned HTTP 200 for the route and transformed ParentContext module. git diff --check passed with line-ending normalization warnings only.
- Limit: no live Firebase bridge/session was configured in this local preview, so persisted-token restoration was source-reviewed but not runtime exercised. No automated tests/builds were run. Firebase configuration and backend token/role enforcement were not changed.

## Revision 16 implementation — Parent tablet/iPad layout

- Approved scope: responsive presentation for Parent screens at iPad portrait and landscape sizes. The approved plan and hash are recorded in `approvals/TASK_APPROVAL.md`.
- Implementation: touch-first tablet rules center non-auth content up to 1080 px, bound bottom navigation to 1000 px, add safe-area spacing, and enlarge primary controls. Landscape quota content uses a two-column layout. A follow-up landscape rule tightens Home spacing and story thumbnails so more content clears the bottom navigation.
- Visual review: synthetic local-preview screenshots were captured for Home, history, capture, quota, and settings at 820×1180 and 1180×820, plus Home at 375×812. The screenshots were visually reviewed. The final landscape Home density rule was applied after the screenshot set; local browser/CDP socket access was denied in this tool session, so that final state could not be recaptured. See `evidence/notes/PARENT_TABLET_LAYOUT_REVIEW_20261110.md` for screenshot hashes and limits.
- Verification: Vite remained active on port 5171 and logged HMR updates for `apps/shared/parent-ui.css`. No automated tests/builds were run. Firebase, authentication, API behavior, assets, dependencies, and auth-page styling were not changed.

## Whole-FE SRS re-review — 2026-11-10

- Review status: COMPLETE as a read-only source review against canonical FEAT-063 v2.7-draft Rev57 from the main checkout. SRS hash: `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; the draft remains unsigned.
- Scope: Parent Android/mobile, Parent web, Teacher, School Manager, Platform Admin, shared auth/API UI, and the separate `apps/admin-ui`; `apps/ui-mobile` was treated as reference source, not the current Parent target.
- Main gaps: the Android app remains fixture-only; Teacher sample-run/Sketch Deck/presentation routes are preview-only with a real backend; Manager backend UI exposes class listing/creation but not the full billing/capacity/roster scope; Platform Admin authentication and moderation fail closed because permission/list APIs are missing. Additional P2 findings cover sample-child selection, consent-status presentation, upload resume, Parent sign-out, and the Manager notification affordance. Current Parent activity order, 36–120 month validation, removed completion/BGM controls, and F5 guard align with the reviewed target clauses.
- Evidence: `evidence/notes/FE_UI_FULL_SRS_REVIEW_REV57_20261110.md`; FEAT-036-EV-010. The old 37-screen archive is historical synthetic preview evidence from commit c384dcc and does not verify later Parent changes.
- No product source was changed; no automated tests/builds, backend/provider calls, approval, deployment, commit, or push were performed. The branch-local source register remains stale at v2.5-draft; the canonical working baseline for this review was Rev57 per the root instructions.
