# Original-art renderer POC

This package is the standalone Person 3 Sprint 1 workstream. It animates only source child-art fixtures through PixiJS and GSAP; it is not the Android app, a backend service, or a generative-image system.

## Included task outputs

- A closed Motion DSL: `MOVE`, `MOVE_TO`, `SCALE`, `ROTATE`, `FADE`, `FLY`, `JUMP`, and `DRAW_REVEAL`.
- Boundary validation for known targets, normalized coordinates, bounded duration, and asset provenance.
- Whole drawing, crop, transparent PNG, and mask provenance records.
- A synthetic butterfly fixture with reveal, flutter/scale, and fly scenes.
- Whole-drawing preserving fallback when extraction/masks are unavailable.
- Fixture tests and browser benchmark output for startup, playback FPS, and browser-reported heap usage when available.

## Run locally

From the repository root:

```powershell
pnpm install --frozen-lockfile
pnpm --filter @sketch2life/art-renderer typecheck
pnpm --filter @sketch2life/art-renderer test
pnpm --filter @sketch2life/art-renderer demo
```

The demo opens `demo.html` and provides normal and forced-fallback fixture buttons. It has no dependency on the mobile app, FastAPI, database, queues, or another Sprint 1 workstream.

For an automated browser smoke check, load `demo.html?fixture=normal` or `demo.html?fixture=fallback`; the selected fixture starts automatically.

## Provenance and preservation

Every render instruction preserves `sourceAssetId`, `sourceAssetVersion`, plus applicable crop/mask versions and source hash. The renderer applies only alpha and geometric transforms to the loaded source texture. It never regenerates or substitutes a cleaner child drawing.

## Benchmark limitation

FPS is measured while the fixture timeline runs. Browser heap memory is reported only by browsers that expose `performance.memory`; otherwise `usedHeapBytes` is `null`. This POC is not a mobile-device performance certification and must be benchmarked later through the React Native WebView bridge on the agreed Android matrix.

## Fixture asset note

`fixtures/butterfly/drawing.svg` is synthetic test media created solely for this standalone POC. It is not a product visual and cannot be copied into an approved/applied frontend asset directory without the frontend visual approval workflow.
