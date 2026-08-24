# FEAT-004 standalone art animation plan

- Status: AWAITING_APPROVAL
- Plan revision: 2
- Implementation status: NOT_STARTED
- Owner: Person 3

## Scope

PixiJS/GSAP runtime, asset/provenance loader, scene graph, Motion DSL, `DRAW_REVEAL`, preservation checks, fallback renderer, standalone fixture player, playback instrumentation, and frontend asset approval flow. Android capture and Gate UI are excluded.

## Acceptance criteria

- [ ] Fixture drawings and motion plans load in a standalone player without the Android app or backend.
- [ ] Renderer benchmark records startup/FPS/memory against an approved local fixture matrix.
- [ ] Original asset IDs, crop/mask versions, and transform history remain traceable.
- [ ] Invalid motion/target/bounds are rejected before playback.
- [ ] Segmentation failure falls back to whole-drawing reveal or transform-only motion.
- [ ] No generated visual is applied without an approval record.
- [ ] Versioned input/output protocol fixtures and an Integration Sprint compatibility note are published.

## Sprint 1 output contract

- Versioned drawing, scene, motion, playback-event, and failure schemas.
- Standalone player and deterministic fixture pack.
- Compatibility note for later React Native bridge/playback integration.

Implementation is blocked until this plan and the visual gate rules are approved.
