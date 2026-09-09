# FEAT-018 Person 3 — PixiJS/GSAP canvas and asset bridge

## Mission

Turn the original image into a real, source-preserving canvas experience using the approved stack: PixiJS 8 + GSAP 3 inside a controlled WebView/bridge. The renderer must animate the original image or bounded derived regions without generative replacement.

## Ownership boundary

Person 3 owns the renderer package, scene/motion contracts, WebView bridge, asset manifest, preservation checks, and performance evidence. Person 3 does not own Android capture, Gate A/B policy, VLM calls, catalog eligibility, or backend credentials.

## Task cards

### P3-T1 — Renderer runtime

- Implement the PixiJS application/bootstrap in `packages/art-renderer`.
- Implement the GSAP timeline and bounded `DRAW_REVEAL`, transform, camera, and highlight primitives.
- Reject invalid target IDs, durations, bounds, missing textures, and unsupported protocol versions before playback.
- Emit validated lifecycle events: `BOOTSTRAPPED`, `ASSET_LOADED`, `REVEAL_STARTED`, `REVEAL_COMPLETED`, `FALLBACK_USED`, `RENDER_ERROR`.

### P3-T2 — Controlled WebView bridge

- Define request/response/event messages in the existing Pixi protocol.
- Keep the mobile app as the bridge host; no provider URL/token/model reference enters renderer code.
- Apply strict origin/message/schema validation and bounded payload sizes.
- Support reload, cancellation, and idempotent replay for the same scene version.

### P3-T3 — Asset pack and provenance

Every pilot scene contains:

- immutable source image reference/hash;
- optional derived mask/regions with parent hash and transform history;
- versioned `scene-manifest.v1.json`;
- versioned `motion-plan.v1.json`;
- fallback still/whole-image reveal;
- approved renderer configuration and dimensions.

Asset flow:

`assets/generated/` → visual review record → `assets/approved/` → `assets/applied/`.

A user-provided real image is a runtime source artifact and stays outside Git; only hash/metadata are evidenced.

### P3-T4 — Full pilot scene coverage

Create scene entries for all 20 golden pilot activities. Each activity must have:

- a valid source-preserving reveal;
- one activity-specific motion/highlight intent;
- a generic whole-image fallback;
- renderer error/fallback behavior.

No activity may require a generated replacement of the original image.

### P3-T5 — Device/performance evidence

Measure on the Android emulator and one additional supported profile:

- first render/startup latency;
- asset load latency;
- steady-state FPS and dropped frames;
- memory before/after playback;
- bridge error/fallback count;
- source-preservation/hash check.

## Required evidence

- Standalone renderer contract tests.
- 20 scene manifests and motion plans.
- Bridge positive/negative protocol fixtures.
- Source-preservation and invalid-plan rejection evidence.
- Screenshots/video for representative age bands and all fallback paths.
- Device performance report with unavailable metrics marked `NOT_MEASURED`.
- Asset review record for every generated visual.

## Acceptance criteria

- The original image remains visible and hash-linked throughout playback.
- PixiJS/GSAP runs inside the controlled WebView and emits validated events.
- All 20 pilot activities have a scene/fallback entry.
- Invalid plans fail closed before animation.
- Renderer can recover to whole-image reveal or still without changing P1 identity.
- No provider/mobile secret appears in renderer bundle or evidence.

## Handoff contract

P3 publishes the renderer protocol and `ArtAnimationPlan` consumed by the mobile experience step. P3 accepts source references and approved scene plans; it does not fetch provider endpoints.

## Definition of done

Pixi runtime, bridge, 20-scene asset pack, preservation/fallback checks, device evidence, and visual review records are complete.

## Contract alignment checklist (mandatory)

Before implementation, read [CONTRACT_FREEZE.md](CONTRACT_FREEZE.md). P3 owns renderer schemas but cannot alter upstream source/provenance or downstream identity fields.

### Exact inputs

- `PixiArtAssetManifestV1` with immutable source reference/hash.
- `ArtAnimationPlanV1` with `plan_id`, `plan_version`, source asset ID, bounded motions, target IDs, and durations.
- Renderer bootstrap protocol version `1` and validated bridge messages.

### Exact outputs

- Lifecycle events with protocol version, renderer instance ID, scene/plan ID+version, event type, timestamp, and typed error when applicable.
- `FALLBACK_USED` must include fallback kind and preserve the same source/activity/objective identity.
- No renderer event may contain provider credentials or raw prompts/model output.

### Contract tests owned by P3

- source hash mismatch and missing asset;
- invalid target, duration, bounds, protocol version, or payload size;
- duplicate/replay/cancel/reload;
- preservation of original source layer;
- all 20 scene entries and generic fallback;
- bridge event schema and origin validation.

P3 must publish renderer JSON Schema/message fixtures before the mobile experience screen integrates the WebView.

## Execution order and stop gates

1. Freeze renderer protocol and message fixtures.
2. Build standalone Pixi player against a synthetic source asset.
3. Add source-preserving image texture and optional derived regions.
4. Add WebView bridge and Android integration behind a feature flag.
5. Add all 20 scene entries and fallback paths.
6. Stop on source hash mismatch, invalid bounds, renderer event drift, or any generated replacement of the original.

Evidence naming: `P3_<scene-or-bridge>_<YYYYMMDD>.json` plus screenshot/performance artifacts under this feature's evidence directory.

## Revision-2 engine additions — pending approval

P3 additionally owns `FEAT018-P3-E1` through `FEAT018-P3-E3` in `ENGINE_REFINEMENT_PLAN.md`: consume the approved `ExperienceSpecV1`, map confirmed anchors to renderer profiles, preserve original artwork, and reject stale/missing spec identity or source-hash mismatch. P3 does not choose pedagogy or off-screen activity.