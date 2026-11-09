# FEAT-036 plan revision 5 — Parent login UX restructure

- Revision: 5
- Status: `APPROVED`
- Prepared: 2026-11-09
- Type: bounded Parent login flow and hierarchy update
- Product baseline: FEAT-063 SRS v2.7-draft Rev57 (unsigned), routed by `docs/context/SRS_AUTHORITY.md`
- Supersedes revision 4 only for the login flow/layout; retains its approved artwork and palette

## Objective

Make sign-in the first and clearest action on the existing Parent login route. Separate account
authentication from the local preview path, remove unsupported account-creation affordances, and
retain the approved animated artwork and current UI colors.

## Source and current behavior

- The owner explicitly requested rebuilding the login structure because its UX is wrong.
- The current route starts on a splash screen, requires an onboarding step before showing login,
  combines local preview with credential submission, and presents a registration toggle that has
  no real registration flow.
- The canonical working SRS requires separate Parent/Teacher authentication through Firebase
  Authentication (FR-C-01), clear Vietnamese adult-facing states (NFR-13/NFR-21), and accessible
  keyboard/screen-reader flows (NFR-20). The SRS remains unsigned.
- Parent Web target-client scope remains open. This authorization changes only the existing local
  Parent UI and does not settle the product-surface question.
- Revision 4's user-provided background/pencil artwork and current `Wordmark` palette remain
  approved by `assets/REVIEW.md` and its manifest.

## Scope

1. Render the sign-in page immediately at `/p11-authentication`; remove the splash as a required
   pre-login step. Keep the existing three-step introduction available only through an optional
   “Tìm hiểu cách hoạt động” action, with a clear return to sign-in.
2. Restructure the page into brand/Parent context, a clear “Đăng nhập” heading and concise guidance,
   credential fields, primary sign-in action, and separate status/preview areas.
3. Keep email/password required for real sign-in. Add an accessible show/hide password control with
   a 44 px target and visible keyboard focus.
4. Make local preview a separate `type="button"` action outside the credential form so it works
   without entering email or password. Show it only in local preview mode and label its synthetic,
   non-persistent data clearly.
5. Keep sign-in disabled and explain the unavailable state when the Firebase auth bridge is absent.
   Remove the unsupported registration toggle; do not add password recovery, registration, OAuth, or
   backend behavior.
6. Preserve the approved animated background/pencil assets, current product `Wordmark`, blue
   controls, and reduced-motion behavior.
7. Store implementation evidence and update feature context, decisions, and status.

## Acceptance criteria

1. Opening `/p11-authentication` presents the login structure immediately, without first requiring
   the splash or onboarding sequence.
2. The page hierarchy clearly separates Parent branding, sign-in fields, auth-unavailable feedback,
   and local preview. No unsupported registration action remains.
3. Email and password labels remain associated with required inputs. Password visibility is
   keyboard-accessible, exposes its state, and meets the 44 px target where layout permits.
4. The local preview action can be used with blank credentials and never invokes the auth provider.
   It is absent outside local preview mode.
5. Real sign-in calls `signInAndResolveRole("parent", email, password)` only when the auth bridge is
   available. Existing error mapping and successful route behavior remain intact.
6. The animation and current palette remain visible; reduced-motion mode stays static and
   horizontal overflow is absent at 430×932 and 320×568. Vertical scrolling remains available when
   the viewport is short.
7. Local module/style/asset responses are checked and the feature records the visual-review limit if
   screenshot capture remains unavailable. Automated tests/builds are outside this authorization.

## Out of scope

- Registration, password reset, new identity providers, backend/API/auth changes, external calls,
  credential handling, other portals, broad text optimization, deployment, and publishing.
- Resolving Parent Web target scope or changing the canonical SRS.

## Implementation and review sequence

1. Record the owner request and plan hash in `approvals/TASK_APPROVAL.md`.
2. Update the Parent login component and its feature-local styles without changing the auth contract.
3. Inspect local route/style/asset responses and responsive structure; capture a screenshot if the
   local browser capture environment permits it.
4. Record evidence and update context, decisions, and status.
