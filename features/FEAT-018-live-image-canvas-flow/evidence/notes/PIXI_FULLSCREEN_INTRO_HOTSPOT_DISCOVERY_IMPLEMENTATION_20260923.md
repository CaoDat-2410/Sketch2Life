# Pixi fullscreen intro and direct hotspot discovery — implementation evidence

Date: 2026-09-23  
Branch: `codex/feat-018-pixi-exploration`  
Scope: FEAT-018 Pixi-only demo slice; video/MP4 remains excluded.

## Delivered

- Added renderer interaction phases and bounded lifecycle events for intro completion, discovery
  readiness and empty-canvas taps.
- Reworked the mobile Pixi screen into an immersive landscape stage. The artwork uses the full
  WebView viewport; header, caption, timeline and Continue are an overlay that hides after three
  seconds and returns after an empty-canvas tap or control action.
- Hotspot interaction is direct on the artwork. It is enabled only after `DISCOVERY_READY` and only
  for `SceneFocusPlanV1` targets with bounded normalized source regions. Accepted taps emit a focus
  event followed by a sanitized discovery event and short Vietnamese label. Hit areas include the
  bounded child-friendly slop from the focus plan, overlap order is deterministic, and duplicate
  taps are debounced.
- Added `SceneLocalizationPort` to keep future local/Lightning region extraction behind the
  application boundary. The current runtime accepts supervised region hints only; missing or
  invalid geometry falls back to the preserved original drawing without inventing hitboxes.
- Fixed the source crop lifecycle by reading image dimensions before closing `ImageBitmap` and
  rebuilt the bundle served at `/renderer/mobile.html`.

## Verification

| Check | Result |
|---|---|
| `pnpm --filter @sketch2life/art-renderer typecheck` | PASS |
| `pnpm --filter @sketch2life/art-renderer test` | PASS — 11 tests |
| `pnpm --filter @sketch2life/art-renderer build:demo` | PASS |
| `pnpm --filter sketch2life-mobile exec tsc --noEmit` | PASS |
| `pnpm --filter sketch2life-mobile test` | PASS — `UI_COPY_AND_RECOVERY_VALID` |
| backend renderer/live-image contract tests | PASS — 18 tests |
| backend `/health` and `/renderer/mobile.html` | HTTP 200; rebuilt mobile bundle served |
| Android x86_64 debug build/install | PASS — installed on `emulator-5554` |
| Android launch log | PASS — React Native started; no fatal/native crash |

## Runtime evidence

- `evidence/screenshots/pixi-runtime-android-2.png` records the clean Android dev-build launch
  after restarting Metro with the newly installed native navigation-bar dependency.
- The temporary pre-restart Metro red-screen was moved outside the feature evidence directory and
  is not treated as product evidence because it contained a local path and internal resolver text.
- The local mobile workflow backend is the full `sketch2life.main:app` entrypoint. The standalone
  `tools.lightning_vision_v2_server` is a vision-provider endpoint and must not replace the
  workflow server on the app's port, otherwise `/renderer/mobile.html` is intentionally absent.

## Known boundary

The composition root does not yet inject a geometry localizer. Therefore a live/demo workflow that
has no supervised `scene_focus_regions` correctly ends in `FALLBACK_REQUIRED`: the child keeps the
whole drawing and can continue, but direct subject taps are not falsely advertised. Injecting the
future local/Lightning adapter through `SceneLocalizationPort` is the next localization task and
does not require changing the Pixi/mobile contract.
