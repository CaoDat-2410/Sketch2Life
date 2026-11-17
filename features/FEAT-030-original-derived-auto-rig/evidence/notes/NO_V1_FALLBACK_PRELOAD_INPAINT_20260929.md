# No-V1 fallback, early preparation and mask-bounded inpainting — 2026-09-29

- Evidence ID: `E-030-FIX-010`
- Approved plan: `plan/NO_V1_FALLBACK_PRELOAD_AND_CUTOUT_INPAINT_20260929.md` (revision 1)
- Approval: `approvals/TASK_APPROVAL.md`, owner approval at 2026-09-29 12:50 Asia/Saigon.

## Trigger and diagnosis

Android emulator `emulator-5554` (`com.sketch2life.mobile`) reported
`[art-renderer] Renderer V2 package could not start. MASK_BACKGROUND_PATCH_UNSAFE` at 12:40:09.
The WebView used the prior bundle `mobile-vRRuVPez.js`; backend access logs showed source, rig
package and four mask reads returned HTTP 200. The throw came from requiring four bright, neutral
image-corner pixels before V2 could make a subject cutout. The V2 error handler then selected the
classic whole-art Pixi animation. Android also emitted repeated WebGL `no texture bound` warnings and
a later “too many GL errors” message; these are recorded separately from the definite fallback
reason and remain a runtime follow-up to inspect after the cutout path is exercised again.

## Change

- Replaced the four-corner paper gate with local color sampling and breadth-first inpainting seeded by
  unmasked pixels neighboring the verified subject silhouette. Only pixels inside the mask are
  reconstructed; pixels outside it and the stored source image remain unchanged. Invalid mask size,
  area, dimensions, or a non-traversable reconstruction still produce an explicit typed failure.
- Removed automatic `classicPlayer`/V1 recovery from the V2 load catch. V2 errors now post
  `PLAYBACK_FAILED`, stop playback and let native show the unchanged source with retry.
- Gate-A confirmation already starts segmentation; it now displays a progress modal while the request
  runs. Gate-B approval now prepares the renderer package before navigation. PixiIntro shows a native
  loading card through WebView/package/mask startup and allows up to 90 seconds after handshake before
  presenting retryable failure.

## Verification

- `pnpm --filter @sketch2life/art-renderer test` — PASS, 43 tests, including non-neutral image-corner
  inpainting, unchanged outside-mask pixels, source immutability and subject-pixel preservation.
- `pnpm --filter @sketch2life/art-renderer typecheck` — PASS.
- `pnpm --filter @sketch2life/art-renderer build:demo` — PASS; emitted `mobile-CMtWg0Zp.js`.
- `pnpm --filter @sketch2life/art-renderer exec tsc --noEmit -p ../../apps/ui-mobile/tsconfig.json` — PASS.
- `pnpm --filter sketch2life-mobile test` — PASS (`UI_COPY_AND_RECOVERY_VALID`).
- Local backend `GET /health` — HTTP 200. `GET /renderer/mobile.html` references the new
  `assets/mobile-CMtWg0Zp.js` bundle; the running backend serves it without restart.
- No Android flow was force-reloaded, no drawing was submitted to Qwen/SAM/Lightning by Codex, and no
  visual acceptance is claimed. Re-open the owner-started flow to verify Android playback and inspect
  whether the separate WebGL warnings persist after the new cutout path runs.
