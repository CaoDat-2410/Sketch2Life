# FEAT-020 Decision Addendum

## D-020-08 — Gate actor

**Status:** confirmed
**Decision:** use `DEMO_OPERATOR` for explicit unattended Gate A, Gate B, and demo feedback records.

## D-020-09 — Deferred video generation

**Status:** confirmed for first demo
**Decision:** create and validate the learning/video context contract, but do not call a video-generation model in the first E2E. Return `VIDEO_DEFERRED` and complete the connected backend context/handoff path.

## D-020-10 — Static PixiJS asset catalog

**Status:** confirmed for FEAT-020
**Decision:** build hand-authored SVG assets and a versioned catalog now. Do not load PixiJS or implement playback. Runtime playback must not generate missing assets with AI; catalog miss and whole-drawing fallback are explicit outcomes.
