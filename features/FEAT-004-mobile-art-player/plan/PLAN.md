# FEAT-004 standalone art animation plan

- Status: REVIEW
- Plan revision: 3
- Implementation status: REVIEW
- Owner: Person 3

## Scope

Implement the approved Person 3 Sprint 1 work package from the task workbook: a local standalone PixiJS/GSAP player, a closed and bounded Motion DSL, child-art asset/provenance loading, a three-scene butterfly `DRAW_REVEAL` demonstration, and an original-art-preserving fallback plus runtime benchmark. Android capture, the full Android app, Gate UI, backend integration, model inference, and production product visuals are excluded.

## Workbook task mapping

1. `P3-T1` — set up the PixiJS + GSAP standalone browser player from drawing and plan fixtures.
2. `P3-T2` — implement and validate the closed `MOVE`, `MOVE_TO`, `SCALE`, `ROTATE`, `FADE`, `FLY`, `JUMP`, and `DRAW_REVEAL` Motion DSL.
3. `P3-T3` — load whole drawing/crop/mask assets while preserving source asset, crop, and mask provenance.
4. `P3-T4` — supply the three-scene butterfly fixture: reveal, flutter/scale, then fly.
5. `P3-T5` — provide whole-drawing/transform-only fallback and reproducible startup/FPS/memory benchmark output.

## Acceptance criteria

- [x] Fixture drawings and motion plans load in a standalone player without the Android app or backend.
- [x] Renderer benchmark instrumentation records startup/FPS/browser-heap data against the butterfly fixture; unsupported heap APIs return `null` explicitly.
- [x] Original asset IDs, crop/mask versions, and transform history remain traceable in render instructions.
- [x] Invalid motion/target/bounds are rejected before playback.
- [x] Extraction/mask failure falls back to whole-drawing reveal and transform-only motion.
- [x] No generated visual is applied; the synthetic SVG is fixture-only and documented outside frontend assets.
- [x] Versioned input/output protocol fixtures and an Integration Sprint compatibility note are published in the renderer README.

## Verification plan

- Run package TypeScript checks and fixture-based unit tests.
- Build the standalone browser demo and inspect the fixture flow locally.
- Capture benchmark output from the same fixture and record its platform limitation.

## Sprint 1 output contract

- Versioned drawing, scene, motion, playback-event, and failure schemas.
- Standalone player and deterministic fixture pack.
- Compatibility note for later React Native bridge/playback integration.

Implementation is blocked until this plan and the visual gate rules are approved.
