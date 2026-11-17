# Android WebView SHA-256 compatibility fix — 2026-09-26

## Symptom

The Android renderer fetched the source image and `RiggedArtworkPackageV1` successfully, then immediately emitted `FALLBACK_APPLIED`. The visible result was an oversized whole-drawing fallback with no V2 mesh motion.

## Root cause evidence

- Backend access log: `/renderer/launch`, `/renderer/source`, and `/v1/renderer/rig-package` all returned HTTP 200.
- Chrome DevTools Protocol against emulator WebView `com.sketch2life.mobile` reported:
  - URL origin: `http://10.0.2.2:8000`
  - `isSecureContext=false`
  - `typeof crypto.subtle === "undefined"`
  - `typeof createImageBitmap === "function"`
  - WebGL2 available.
- `packages/art-renderer/demo/mobile.ts` previously called `crypto.subtle.digest` unconditionally. Its broad V2 catch converted that runtime exception into the generic extraction fallback.

## Change

- Added `sha256Hex` with Web Crypto preference and a dependency-free, deterministic SHA-256 implementation for non-secure Android WebViews.
- The package hash remains mandatory and is still compared with the backend-issued `packageSha256`; the change does not bypass integrity validation.
- Added console-only technical diagnostics before the child-safe visual fallback.

## Verification

- `pnpm --filter @sketch2life/art-renderer typecheck`: PASS.
- `pnpm --filter @sketch2life/art-renderer test`: PASS, 18/18 tests.
- Portable SHA-256 verified against the empty string, `abc`, and quick-brown-fox standard vectors.
- `pnpm --filter @sketch2life/art-renderer build:demo`: PASS, 820 modules transformed.
- A fresh end-to-end visual run remains required because the already-consumed one-shot renderer command is intentionally not replayed by the mounted React Native screen after a DevTools-only page reload.

## Approval and boundary

The owner explicitly requested this compatibility bug fix after reviewing the runtime diagnosis. It stays inside the approved FEAT-030 renderer/package-integrity scope and adds no dependency, model, provider, or visual asset.
