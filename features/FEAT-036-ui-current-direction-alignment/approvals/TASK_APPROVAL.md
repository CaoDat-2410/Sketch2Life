# FEAT-036 task approval

- Feature: FEAT-036 — UI direction alignment
- Approved plan: `plan/PLAN_REV3_PARENT_UI_SEVEN_FIXES.md`
- Plan revision: 3
- Plan SHA-256: `8DC17AE1791AFEB39A9FCC85DCD8059CD6D4C3C49D4A2840D3E97B679CF55048`
- Approval status: `APPROVED`
- Prepared: 2026-11-09
- Reviewer / approver: Project owner (explicit instruction in this conversation)
- Approval date: 2026-11-09

## Authorization recorded

The owner explicitly authorized fixing the seven Parent findings from
`evidence/notes/PARENT_UI_UX_REVIEW_20261109.md` on the current worktree/branch, and said broader
UI optimization (including reducing text) will be requested separately later. This approval covers
only the bounded scope and acceptance criteria in plan revision 3.

This amends the prior revision-2 review-only authorization. Revision 2 remains in
`plan/PLAN.md` as historical planning context; it does not authorize implementation beyond this
revision-3 scope.

## Approval boundaries

- Parent portal only for this batch; other portals and general redesign are deferred.
- No backend/API/auth-provider implementation, external provider calls, credentials, real child data,
  generated assets, deployment, or publishing are approved.
- The Parent Web target-client question and no-lesson-preset catalog behavior remain open SRS
  questions; this approval does not resolve either decision.

## Revision 4 authorization — Parent login animation

- Approved plan: `plan/PLAN_REV4_PARENT_LOGIN_ANIMATION.md`
- Plan revision: 4
- Plan SHA-256: `C34CC3D4D0BA996785E4E1A6DC5881DF2F0D5971D407C950748A119D7C47EDF7`
- Approval status: `APPROVED`
- Prepared / approved: 2026-11-09
- Reviewer / approver: Project owner (explicit request in this conversation)

### Authorization recorded

The owner explicitly requested using the supplied `h-y-tri-n-khai-animated.zip` for the existing
Parent login while preserving the current UI colors. This approval covers only the login's visual
hero, selected artwork, responsive styling, reduced-motion behavior, and feature-local evidence.
The source archive SHA-256 is
`CEA2152B2E0CF66D1C0D645D4451F2BBD6A2490E909232ABFC83DAF7BBD39AA4`.

### Approval boundaries

- Preserve the existing login form, authentication bridge guard, preview action, error handling,
  route, and onboarding behavior.
- Use the supplied background and pencil artwork with the current product wordmark and blue UI
  tokens. The archive's differently colored logo image is not approved for replacing the product
  wordmark.
- No auth-provider, backend/API, credential, provider-call, registration, broad redesign, other
  portal, publishing, or deployment changes are approved.
- The Parent Web target-client question remains open; this bounded implementation does not resolve
  it.

## Revision 5 authorization — Parent login UX restructure

- Approved plan: `plan/PLAN_REV5_PARENT_LOGIN_UX_RESTRUCTURE.md`
- Plan revision: 5
- Plan SHA-256: `42FECC6E3EEF15D7FDFEC777413050B78F8DDA60BE780984F0E6E58517143113`
- Approval status: `APPROVED`
- Prepared / approved: 2026-11-09
- Reviewer / approver: Project owner (explicit request in this conversation)

### Authorization recorded

The owner explicitly requested rebuilding the login UX because its current structure is wrong.
This revision makes sign-in the immediate primary task, separates local preview from credential
submission, and removes the unsupported registration affordance. It retains the revision-4
approved animation and current UI colors.

### Approval boundaries

- Change only the existing Parent login flow/layout and its local styling/evidence.
- Preserve the existing Firebase auth bridge and `signInAndResolveRole` contract; add no backend,
  provider, registration, recovery, OAuth, or external-call behavior.
- The existing introduction may remain optional; it must no longer gate access to sign-in.
- Preserve the user-approved background/pencil art and current product `Wordmark` palette.
- The Parent Web target-client question remains open; this authorization does not resolve it.
- Automated tests/builds, deployment, and publishing are outside this approval.

## Revision 6 authorization — Rebuild Parent login from supplied ZIP

- Approved plan: `plan/PLAN_REV6_PARENT_LOGIN_ZIP_REBUILD.md`
- Plan revision: 6
- Plan SHA-256: `8DBBFDBA5172906ED59322498B3BC1EF67A0E0A4A997B4FA53F75FE07DBF6AF0`
- Approval status: `APPROVED`
- Prepared / approved: 2026-11-09
- Reviewer / approver: Project owner (explicit request in this conversation)

### Authorization recorded

The owner explicitly instructed that the login UI be rebuilt from the complete supplied ZIP,
carrying over its contents as-is while retaining the current UI colors. The archive includes the
SplashScreen component, styles, GSAP animation sequence, background, logo, pencil, and four sparkle
positions. The existing email/password sign-in must remain functional because the archive contains
no login form or authentication flow.

Archive SHA-256: `CEA2152B2E0CF66D1C0D645D4451F2BBD6A2490E909232ABFC83DAF7BBD39AA4`.

### Approval boundaries

- Rebuild only the existing Parent login scene/layout and its styles/assets/evidence.
- Preserve the existing Firebase auth bridge and `signInAndResolveRole` contract; add no backend,
  provider, registration, recovery, OAuth, or external-call behavior.
- Recolor the supplied composition to the current UI palette and carry over all supplied visual
  assets and animation details.
- This revision supersedes revision 5's visual composition and optional-intro action where they
  conflict; it does not supersede revision 5's requirement to keep local preview separate from
  credential submission.
- The Parent Web target-client question remains open; this authorization does not resolve it.
- Automated tests/builds, deployment, publishing, commit, and push are outside this approval.

## Revision 7 authorization — Login transition and password recovery entry

- Approved plan: `plan/PLAN_REV7_LOGIN_TRANSITION_AND_RECOVERY.md`
- Plan revision: 7
- Plan SHA-256: `5EEF05DCEDE49C7AFA13B67A9D83D504DBCF977A381AEBB69D8FE6850B8654D7`
- Approval status: `APPROVED`
- Prepared / approved: 2026-11-09
- Reviewer / approver: Project owner (explicit request in this conversation)

### Authorization recorded

The owner supplied a screen recording and account/security screenshot, requested that password
recovery be accessible from login instead of the shown Settings row, and asked for the ZIP-based
login transition to match the recording. This revision moves recovery to a dedicated public route,
removes the Settings recovery row and mock OTP flow, and transitions from the ZIP splash to login.

### Approval boundaries

- Parent login, its public recovery route, and the Settings recovery entry only.
- Preserve the existing Firebase sign-in and local-preview behavior. No reset API, OTP provider,
  registration, external call, or false reset-success behavior is approved.
- A truthful unavailable state is required until an existing reset operation is available.
- Preserve the current UI palette and the approved ZIP artwork/animation.
- The Parent Web target-client question remains open; this authorization does not resolve it.
- Automated tests/builds, deployment, publishing, commit, and push are outside this approval.

## Revision 8 authorization — Password recovery visual refinement

- Approved plan: `plan/PLAN_REV8_PASSWORD_RECOVERY_VISUAL_REFINEMENT.md`
- Plan revision: 8
- Plan SHA-256: `B25E757BCDCE8F7D2354F6D745B8955067734FAB1872C343AF93F0576F589859`
- Approval status: `APPROVED`
- Prepared / approved: 2026-11-09
- Reviewer / approver: Project owner (explicit request in this conversation)

### Authorization recorded

The owner explicitly requested a more polished forgot-password UI. This authorizes a bounded visual
refinement of `/p14-password-recovery` using the current palette, retaining the email prefill,
return-to-login path, and truthful unavailable state. No email, OTP, or backend operation is added.

### Approval boundaries

- Update the recovery page layout, decorative UI, responsive styling, and form hierarchy only.
- Preserve dark mode, keyboard accessibility, reduced-motion support, and current login/Settings
  behavior.
- Do not introduce new assets, dependencies, backend/auth changes, or false send/reset success.
- Automated tests/builds, deployment, publishing, commit, and push are outside this approval.

## Revision 9 authorization — Real-device status bar and safe area

- Approved plan: `plan/PLAN_REV9_REAL_DEVICE_STATUS_BAR_SAFE_AREA.md`
- Plan revision: 9
- Plan SHA-256: `F8DE86A9EF812B2B74468FFA83411D0A804CDB71E01847138F20EE1C074FD4CE`
- Approval status: `APPROVED`
- Prepared / approved: 2026-11-09
- Reviewer / approver: Project owner (owner-raised mobile deployment issue)

### Authorization recorded

The owner identified the fixed simulated `9:41`/system-icons row shown in the supplied screenshot as
a real-mobile deployment concern. This revision hides that mock on mobile viewports and reserves
native safe-area insets without changing native system-bar configuration.

### Approval boundaries

- Keep the simulated status row in the desktop phone preview; suppress it at mobile widths.
- Apply the top safe-area inset once, preserving existing login/recovery page inset handling.
- Do not modify native Android/iOS code, authentication, backend behavior, or unrelated screens.
- Automated tests/builds, deployment, publishing, commit, and push are outside this approval.

## Revision 10 authorization — Centered create-story navigation shortcut

- Approved plan: `plan/PLAN_REV10_CREATE_STORY_NAV_SHORTCUT.md`
- Plan revision: 10
- Plan SHA-256: `F7BF53C0BA681C0874699545E1D4CF3783DAF4C924E4DDD6FB5C779003761547`
- Approval status: `APPROVED`
- Prepared / approved: 2026-11-10
- Reviewer / approver: Project owner (explicit request in this conversation)

### Authorization recorded

The owner explicitly requested a large camera icon centered in the bottom navbar as a shortcut into
the story-creation flow. This revision adds that action and routes it into the current capture-first
flow.

### Approval boundaries

- Preserve existing navigation entries and add a centered “Tạo” action in the local-preview and
  product-nav variants.
- Reuse `/p04-capture-subject-confirmation`, optional-setup skip behavior, and current quota warning.
- Do not modify backend/quota logic, native navigation, other portals, or flow screens.
- Automated tests/builds, deployment, publishing, commit, and push are outside this approval.

## Revision 11 authorization — Remove unsupported Parent 2FA UI and publish the UI batch

- Approved plan: `plan/PLAN_REV11_REMOVE_UNSUPPORTED_PARENT_2FA_UI.md`
- Plan revision: 11
- Plan SHA-256: `C6C29A3C3E2B56AEE304306EA1417DCFCEE119FAD23D28E651D6DF19D6AE0289`
- Approval status: `APPROVED`
- Prepared / approved: 2026-11-10
- Reviewer / approver: Project owner (explicit request in this conversation)

### Authorization recorded

The owner agreed that the unsupported Parent 2FA UI should be removed, then explicitly requested
that all current approved UI work be bundled into one commit and pushed so it can be continued on
another machine.

### Approval boundaries

- Remove the Parent-only 2FA settings row, simulated state, method controls, and backup codes; keep
  password-change and other settings. Do not change the SRS or admin MFA requirements.
- Include the existing owner-approved FEAT-036 UI work present in this worktree in one commit.
- Push one commit to the current feature branch. Do not include secrets or unrelated worktree files.
- Automated tests/builds, deployment, and site publishing are not authorized.
