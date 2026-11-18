# FEAT-066 EV-025 — Recognizable settings gear glyph (Rev22)

- Date: 2026-11-11 (Asia/Bangkok).
- Parent authorization: FEAT-066 Plan Rev21, SHA-256 D97702B032B44573A9733F3978A175EF0C9EF45A50AF5D5A88A673192104FFE2; Rev21 explicitly maps settings to a gear and approves semantic navbar glyph/path correction.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Finding: The previous settings path was a center circle with eight radial spokes, which reads as a sun at navbar size.
- Correction: Replaced the shared gear glyph with a toothed cog outline and mapped the Manager-in-Teacher-shell settings item to gear too. Kept the legacy settings path for non-navigation icon uses; no page-content icon treatment was changed.
- Style: single currentColor outline with rounded joins and the existing crayon sketch edge; no fill or multicolor glyph.
- Scope remains limited to the previously approved Teacher and School Manager settings navbar symbols.

## Preview

- Captured nine local screenshots using isolated headless Chrome through loopback ports 127.0.0.1:5172, :5173 and :5174. Files are in screenshots/role-nav-icons-v22/; script: capture_role_nav_gear_v22.mjs.
- Visually inspected Teacher desktop and School Manager desktop settings glyphs; both now read as gears. Captures cover all three roles at 1440x900 and 390x844 plus dark desktop.
- All captures report no horizontal overflow, Vite error overlay, or browser runtime exception.
- Local visual preview only; no authentication service, external provider, production data, or real user/child data.

## Validation and limits

- git diff --check passed.
- No automated tests/builds, backend/API, mobile/Parent, package/dependency changes, commit, or push.
- Existing unrelated dirty worktree changes remain preserved.