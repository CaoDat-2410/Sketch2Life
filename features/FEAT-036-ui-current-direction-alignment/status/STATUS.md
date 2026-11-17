# FEAT-036 status

- Status: `ACTIVE`
- Updated: 2026-11-10
- Plan revision: 11
- Implementation status: `COMPLETE` for the approved Parent UI batch in revisions 3–11. Source
  verification is recorded per revision below; rendered visual and physical-device checks remain
  pending where noted. The revision-4 artwork is retained; earlier login compositions are
  superseded.
- Approval gate: `APPROVED` by the owner for
  `plan/PLAN_REV11_REMOVE_UNSUPPORTED_PARENT_2FA_UI.md`; its hash and prior approvals are in
  `approvals/TASK_APPROVAL.md`.
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
