# FEAT-036 plan revision 6 — Rebuild Parent login from supplied ZIP

- Revision: 6
- Status: `APPROVED`
- Prepared: 2026-11-09
- Type: Parent login visual rebuild from user-provided source archive
- Product baseline: FEAT-063 SRS v2.7-draft Rev57 (unsigned), routed by `docs/context/SRS_AUTHORITY.md`
- Supersedes revision 5's login composition where it conflicts; retains working authentication
  behavior and the user's requirement to keep the current UI colors

## Objective

Rebuild the existing Parent login presentation from the full source in
`D:/Zalo Received/h-y-tri-n-khai-animated.zip`. Carry over the source splash composition, assets,
four sparkle placements, and GSAP animation timing/easing while recoloring it to the current UI
palette. Preserve a usable sign-in form on the same route.

## Source inspection

- Archive SHA-256: `CEA2152B2E0CF66D1C0D645D4451F2BBD6A2490E909232ABFC83DAF7BBD39AA4`.
- The archive contains the original `SplashScreen.jsx`, `styles.css`, React/Vite shell, package
  metadata, and `background.png`, `logo.png`, and `pencil.png`.
- `SplashScreen.jsx` uses a GSAP timeline for the pencil entrance/bounce, logo entrance, and four
  sparkles. The archive contains a splash screen only; it does not contain login fields or auth.
- The owner explicitly requested transferring the complete ZIP design and keeping only the current
  UI colors. That request authorizes the included logo and animation assets, subject to recoloring.

## Scope

1. Replace the current compact hero with a full-height login scene based on the archive's source
   layout: background covering the scene, logo near the top, pencil centered, and all four sparkle
   positions.
2. Use the source GSAP sequence and timings/easing for the pencil, logo, and sparkles; honor reduced
   motion by rendering every element in its final state without animation.
3. Recolor the source composition and logo to the current Sketch2Life UI palette. Keep the provided
   background/pencil artwork, and use the provided logo rather than omitting archive content.
4. Keep email/password sign-in visible and usable on `/p11-authentication`, over the adapted scene.
   Preserve the existing Firebase auth bridge and `signInAndResolveRole` contract.
5. Keep local preview separate from credential submission. Do not add registration, recovery, OAuth,
   or new backend/auth behavior.
6. Remove the optional onboarding action from this screen; it is not part of the supplied design.
7. Record source asset provenance and implementation evidence in FEAT-036. Do not deploy, publish,
   commit, or push.

## Acceptance criteria

1. The login route uses the archive's full-screen splash composition, all three source images, the
   four sparkle positions, and source animation sequence/timing/easing.
2. The layout and assets use the current UI palette instead of the archive's purple/amber palette.
3. Sign-in is available on the login route without a splash gate; authentication and local preview
   remain separate and retain their existing behavior.
4. Reduced-motion users receive a static complete scene. The form and preview actions remain
   keyboard-accessible and usable at narrow/mobile sizes.
5. Vite serves the route, transformed module, stylesheet, and applied assets successfully; record a
   rendered visual-review limit if screenshot capture remains unavailable.
6. No automated tests/builds are authorized by this revision.

## Out of scope

- Auth/backend/provider changes, account registration/recovery, new product flows, other portals,
  broad redesign outside Parent login, deployment, publishing, commit, or push.
- Resolving Parent Web target-client scope in the SRS.

## Implementation and review sequence

1. Record owner authorization and this plan hash in `approvals/TASK_APPROVAL.md`.
2. Preserve the full supplied splash source/assets in feature-local provenance records and adapt the
   component/styles to the Parent app.
3. Keep sign-in and preview handlers separate and retain the auth contract.
4. Inspect Vite route/module/style/asset responses and attempt rendered visual review with the
   available local capture path.
5. Update feature context, decisions, evidence, and status.
