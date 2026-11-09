# Parent login rebuilt from supplied ZIP — 2026-11-09

## Authorization and source

Plan revision 6 and explicit owner authorization are recorded in `approvals/TASK_APPROVAL.md`.
The source archive SHA-256 is
`CEA2152B2E0CF66D1C0D645D4451F2BBD6A2490E909232ABFC83DAF7BBD39AA4`.

The archive is a React/Vite splash project, not a login implementation. Its original component,
styles, application shell, package metadata/lockfile, and `.gitignore` are preserved in
`evidence/raw/parent-login-zip-source/`. The three supplied PNGs are preserved byte-for-byte in
`assets/generated/parent-login-zip-splash/` and promoted to the approved/applied folders per the
owner's explicit request. Their hashes are in
`assets/manifests/PARENT_LOGIN_ZIP_SPLASH_20261109.asset.json`.

## Implementation

- Rebuilt the login scene from the ZIP's full-height background, source logo, pencil, and all four
  sparkle locations.
- Adapted the source animation choreography and timing: pencil starts after 80 ms and enters over
  840 ms with `elastic.out(1, 0.55)`; logo enters after 380 ms over 520 ms with `back.out(1.55)`;
  sparkles start at 740 ms with a 50 ms stagger over 240 ms using `back.out(2.4)`; pencil float
  begins at 1.02 s with a 340 ms sine-in-out cycle repeated twice with yoyo.
- Parent UI does not currently have the archive's GSAP dependency installed. The sequence and easing
  equations are adapted in a native `requestAnimationFrame` loop; no package dependency or backend
  behavior was added.
- The source artwork remains unchanged on disk. A light CSS hue/saturation adjustment and blue
  scene wash harmonize it with the current palette; the login panel, inputs, buttons, and feedback
  use existing Sketch2Life tokens.
- The email/password form remains immediately available over the scene and still calls the existing
  `signInAndResolveRole("parent", email, password)` contract. Local preview remains a separate
  button outside the form. The previous optional-introduction action is removed from this screen.
- Reduced-motion preference renders the complete final scene without animation.

## Verification

- Vite returned HTTP 200 for `/p11-authentication`, the transformed Parent page module, its
  stylesheet, and the three applied PNG assets (`image/png`). The transformed module contained no
  Vite transform error and retained distinct sign-in and preview paths.
- `git diff --check` passed.
- No automated tests or builds were run.
- A rendered screenshot was not obtained: the available Node REPL Playwright import failed before
  browser launch, and the existing local Edge CDP capture path is recorded as unresponsive in
  revision 4. Responsive pixel-level visual review remains pending; implementation status remains
  `IN_PROGRESS`.
