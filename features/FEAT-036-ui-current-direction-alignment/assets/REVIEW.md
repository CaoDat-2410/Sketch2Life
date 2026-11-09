# FEAT-036 visual asset review

This review created no new UI artwork and applied no product asset. Existing Home artwork files were
inspected only to diagnose the screenshot showing blank story thumbnails. Any future generated art
must follow the generated/provenance/visual-approval/approved/applied gate in
`docs/governance/FRONTEND_ASSET_GATE.md`.

## Owner-provided Parent login animation — 2026-11-09

- Source archive: `h-y-tri-n-khai-animated.zip`; SHA-256
  `CEA2152B2E0CF66D1C0D645D4451F2BBD6A2490E909232ABFC83DAF7BBD39AA4`.
- Review basis: the owner explicitly requested using this animation for login while retaining the
  current UI colors. This request approves the selected supplied visuals for this bounded use.
- Approved source entries: `background.png` and `pencil.png`. The existing `Wordmark` is retained;
  the archive logo image is not applied because its purple/amber colors do not match the current
  product wordmark palette.
- The source archive and selected images remain unchanged. Runtime use is limited to the approved
  and applied copies recorded in `assets/manifests/PARENT_LOGIN_ANIMATION_20261109.asset.json`.

## Complete ZIP splash transfer — 2026-11-09

- The owner explicitly requested carrying the full contents of the supplied ZIP into the Parent
  login while keeping the current UI colors. This supersedes the prior exclusion of `logo.png` for
  this login revision.
- Reviewed source files and project shell (`SplashScreen.jsx`, `styles.css`, `App.jsx`, `main.jsx`,
  `index.html`, `vite.config.js`, package metadata/lockfile, and `.gitignore`) are preserved in
  `evidence/raw/parent-login-zip-source/`.
- Reviewed visual assets: `background.png`, `logo.png`, and `pencil.png`. All three source PNGs are
  preserved byte-for-byte under `assets/generated/parent-login-zip-splash/` and have been promoted
  to the approved/applied folders under the user's explicit request.
- Runtime styling uses the Sketch2Life palette for the scene wash, form surface, controls, and
  feedback. A light CSS hue/saturation adjustment harmonizes the supplied raster artwork while the
  original files and their detailed rendering remain unchanged.
- Provenance and SHA-256 values are recorded in
  `assets/manifests/PARENT_LOGIN_ZIP_SPLASH_20261109.asset.json`.
