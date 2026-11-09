# Parent login UX restructure — 2026-11-09

## Scope

Owner-approved plan revision 5 restructures only the existing Parent login route. Its plan hash and
authorization are recorded in `approvals/TASK_APPROVAL.md`. The Parent Web target-client question
remains open in the canonical FEAT-063 SRS.

## Changes

- `/p11-authentication` now presents sign-in immediately; splash and onboarding no longer block it.
- The three-step introduction remains available through a secondary action and returns directly to
  sign-in.
- Local preview uses a separate button outside the credential form. It opens synthetic, non-persistent
  data without submitting credentials or invoking the auth provider.
- The unsupported registration toggle is removed. No registration, password recovery, OAuth, or
  backend behavior was added.
- Real sign-in stays guarded by the existing Firebase auth bridge and calls the existing
  `signInAndResolveRole("parent", email, password)` contract.
- Password visibility has a keyboard-accessible button with an exposed pressed state and a 44 px
  minimum target. Unavailable-auth and error states have separate feedback.
- The approved animation, current product `Wordmark`, colors, and reduced-motion styling remain.

## Verification

- The running Vite server returned HTTP 200 for the transformed
  `apps/parent-ui/src/pages/ParentScreens.tsx` module and
  `apps/parent-ui/src/styles/parent-login-animation.css` stylesheet, and for the
  `/p11-authentication` route.
- The transformed module contains the direct sign-in and separate preview actions, no longer
  contains the unsupported registration toggle, and did not contain a Vite transform error.
- `git diff --check` passed.
- No automated tests or builds were run.
- A rendered screenshot was not captured. The local Edge CDP page did not respond during the prior
  revision's capture attempt; responsive visual/pixel review remains pending. The implementation
  status remains `IN_PROGRESS` until that review is available.

## Files updated

- `apps/parent-ui/src/pages/ParentScreens.tsx`
- `apps/parent-ui/src/styles/parent-login-animation.css`
- Feature plan, approval, context, decisions, and status records.
