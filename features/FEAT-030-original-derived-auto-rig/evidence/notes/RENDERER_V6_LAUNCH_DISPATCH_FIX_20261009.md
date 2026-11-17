# Pixi V6 launch dispatch fix

Date: 2026-10-09 (Asia/Saigon)

## Symptom and cause

The supplied Android screenshot showed the renderer preparation timeout. The mobile client converts the V4 show envelope into a `RendererLoadCommandV6`. The WebView receiver accepted and queued that command, but `loadLaunch` only parsed V1 through V5. The handler then returned with the page still at zero-duration `READY`; the mobile preparation watchdog correctly kept waiting because no load duration or failure event followed.

## Change

- Parse `RendererLoadCommandV6` before V5 in the WebView load handler, then pass it through the existing V6 preparation path.
- Keep V1–V5 parsing and the V6 show-plan, topic-scene, sprite-cycle, and mask handling unchanged.
- No backend, model, provider, data, or orientation behavior changed.

## Verification

- `pnpm --filter @sketch2life/art-renderer typecheck` — passed.
- `pnpm --filter @sketch2life/art-renderer build:demo` — passed; the bundled mobile renderer was emitted.
- Automated tests and live Android/Lightning inference were not run.
- `git diff --check` on the changed tracked implementation and FEAT-030 records — passed.

## Remaining runtime check

The rebuilt renderer bundle must be present in the Lightning checkout serving `/renderer/mobile.html`. After deployment/restart, reopen the Pixi screen and confirm the source/package/mask requests complete and playback advances past `INTRO_LOADING`. The screenshot also shows the device frame in portrait while this screen intentionally locks to landscape; rotate the emulator/device to see the intended landscape composition.
