# Pixi startup handshake follow-up — 2026-09-28

## Symptom and diagnosis

The owner reported that the Android experience still appeared to fall back. The supplied screen showed the native “story is taking longer than expected” state while the renderer page remained visible. In the captured backend output from the current attempt, the mobile HTML, renderer entry module and Pixi chunks were served, but no source, rig-package or rig-mask reads followed. This placed the failure before artifact retrieval, rather than proving a SAM2 mask failure.

Code inspection found that `packages/art-renderer/demo/mobile.ts` awaited `Application.init()` before installing the React Native WebView message listeners and posting `RendererBootstrap`. If Pixi GPU initialization stalls or rejects, native never receives the bootstrap and no renderer load request is sent. The mobile screen previously used one 15-second timeout for both missing handshake and slow post-handshake startup, so these failure stages looked alike.

## Change

- Install both WebView message listeners and post the bootstrap before starting asynchronous Pixi initialization.
- Queue at most one validated load message until Pixi is ready; duplicate queued launch messages collapse to one delivery.
- On Pixi initialization failure, send a sanitized `PLAYBACK_FAILED` event for the matching launch.
- Use a 15-second bootstrap timeout and a separate 45-second bounded post-bootstrap startup timeout, with different parent-facing status text.
- No model calls, provider settings, AI contracts, or learning-flow behavior changed.

## Verification

- `pnpm --filter @sketch2life/art-renderer test` — PASS, 32 tests.
- `pnpm --filter @sketch2life/art-renderer typecheck` — PASS.
- `pnpm --filter @sketch2life/art-renderer build:demo` — PASS; Vite emitted the updated mobile bundle.
- `pnpm --filter @sketch2life/art-renderer exec tsc --noEmit -p ../../apps/ui-mobile/tsconfig.json` — PASS.
- `pnpm --filter sketch2life-mobile test` — PASS (`UI_COPY_AND_RECOVERY_VALID`).
- Local backend `GET /health` — PASS; `GET /renderer/mobile.html` references the newly generated mobile bundle.
- `adb devices -l` — no connected devices; default ADB server could not start. Android + live Lightning end-to-end retest is therefore not claimed.

## Limitations / next evidence

Reconnect/start the Android emulator, reload the app, and retest a drawing for which Lightning reports SAM2 `SUCCEEDED`. Confirm native status proceeds past bootstrap, backend logs show source/package/mask reads, the mask is verified, and the subject cutout moves without a false timeout. No screenshot or child image was copied into this evidence folder.

## Correction and bridge replay retest — 2026-09-28

The preceding diagnosis that Pixi initialization was blocking the bridge was an unverified code-based hypothesis and is superseded by the emulator evidence below.

- Device/environment: `emulator-5554`, Pixel_10 AVD, Android 17, x86_64; app URL `http://10.0.2.2:8000`.
- WebView inspection confirmed WebGL 1 and WebGL 2 contexts are available. `Application.init()` completed, and one Pixi canvas was attached; page status became “Pixi sẵn sàng, đang chờ launch của đúng phiên.”
- The native app had received the initial bootstrap, but backend logs showed no source/package/mask reads before the 45-second post-handshake timeout. This isolates the missing transition to the native-to-WebView launch delivery, not SAM2 or GPU availability.
- The fix retains the early bootstrap, caches only the one schema-validated launch message, and resends the exact same message when the page re-announces bootstrap after Pixi is ready (or initialization fails). The startup gate now consumes that message at most once, even if a duplicate arrives after ready/failure. No AI request, contract change, or child media was introduced.
- Art-renderer tests: PASS, 32 tests; art-renderer typecheck: PASS; renderer Vite bundle: PASS; mobile TypeScript check: PASS.
- Limitation: a post-fix Android image-to-artifact flow was not run, because entering it again could invoke the configured live Lightning provider. No extra Qwen/SAM inference was intentionally triggered.
