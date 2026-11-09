# FEAT-036 plan revision 7 — Login transition and password recovery entry

- Revision: 7
- Status: `APPROVED`
- Prepared: 2026-11-09
- Type: Parent login transition and recovery UI restructure
- Product baseline: FEAT-063 SRS v2.7-draft Rev57 (unsigned), routed by `docs/context/SRS_AUTHORITY.md`
- Video reference: `D:/Downloads/Ghi Màn hình 2026-10-29 lúc 23.50.22.mov`, SHA-256
  `46CF7A155F751F0FD11CF9C8CB6DA267924236E0C9E79CE9B75014443B7DA5C8`
- Screenshot reference: the user's account/security screen showing a “Quên mật khẩu” row

## Objective

Match the login startup transition to the supplied recording: play the ZIP-based full-screen splash,
then reveal the login form. Move password recovery to a dedicated route linked from login and remove
the obsolete recovery row/mock OTP flow from Settings.

## Source and current behavior

- The screen recording shows the animated splash between initial load and the stable login form.
  The first four seconds are preserved as `evidence/raw/login-transition-video-20261029/` contact
  sheets for review.
- Revision 6 already imports the ZIP background/logo/pencil and implements its animation sequence,
  but currently shows the login form over the splash artwork instead of transitioning from splash
  to form.
- `P13SettingsPage` contains a “Quên mật khẩu” row and a local OTP mock that claims to send email
  and reports successful reset without calling a provider.
- `FirebaseAuthBridge` has no password-reset operation and the repository has no reset API. The
  canonical FEAT-063 SRS defines Firebase-managed email action links in UC-13 at a high level; it
  does not define a Parent OTP reset flow. No OTP or success behavior will be invented here.
- The current SRS remains an unsigned draft; this scoped UI change does not settle Parent Web scope.

## Scope

1. On first login entry per browser session, play the approved ZIP splash full-screen, then transition
   the same route into the login form. Do not replay the splash when returning from password recovery
   in the same session.
2. Respect `prefers-reduced-motion` by skipping the animated splash and showing the login form
   immediately with a static final composition.
3. Add a visible “Quên mật khẩu?” link beside the password field. It opens a separate public
   `/p14-password-recovery` page and passes the entered email as a convenience prefill.
4. Redesign the recovery page around the registered email and email-based recovery instructions.
   Show a truthful unavailable state when the reset operation is not connected; do not simulate OTP
   delivery or claim a successful reset.
5. Remove the “Quên mật khẩu” row, `forgot` settings subview, and its fake OTP state/handler from
   `P13SettingsPage`. Keep the separate “Đổi mật khẩu” row.
6. Preserve existing sign-in, role resolution, preview behavior, and the current UI palette. Add no
   backend endpoint or identity-provider call.
7. Record video/screenshot provenance and implementation evidence in FEAT-036.

## Acceptance criteria

1. The login route displays the ZIP scene first and reveals the form after the source animation; the
   transition is one-shot per session and returning from recovery does not replay it.
2. Reduced-motion preference skips the wait/animation and presents the form immediately.
3. The login recovery link navigates to a distinct route; the recovery page has a clear return action
   to login and can prefill the entered email.
4. The Settings account/security list no longer contains “Quên mật khẩu”; no mock OTP send/success
   behavior remains there.
5. When email recovery is unconnected, the UI communicates that state and makes no false delivery or
   reset-success claim. Sign-in/auth and local preview paths are unchanged.
6. Vite serves the login/recovery routes, transformed module, styles, and applied assets; capture a
   rendered screenshot if browser tooling permits. No automated tests/builds are authorized.

## Out of scope

- Implementing an email/OTP recovery provider or backend API, changing authentication contracts,
  registration, other portals, broad redesign, deployment, publishing, commit, or push.
- Resolving Parent Web target-client scope or changing the canonical SRS.

## Implementation and review sequence

1. Record owner authorization and plan hash in `approvals/TASK_APPROVAL.md`.
2. Add splash-to-login state transition and a dedicated recovery route.
3. Remove the obsolete settings recovery menu/state and preserve password-change settings.
4. Verify route/module/style/asset responses and inspect the changed source; record any capture limit.
5. Update feature context, decisions, evidence, and status.
