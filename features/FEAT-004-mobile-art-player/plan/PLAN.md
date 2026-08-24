# FEAT-004 Mobile app and art player plan

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Owner: Person 3

## Scope

Mobile capture, upload/readiness UI, Gate A/B review surfaces, PixiJS/GSAP bridge spike, asset/provenance loader, scene graph, motion DSL, DRAW_REVEAL, fallback renderer, playback instrumentation, and frontend asset approval flow.

## Acceptance criteria

- [ ] Fixture drawing and narration can be captured/loaded on a target mobile device.
- [ ] Gate A/B screens expose review/approval, not hidden automatic bypasses.
- [ ] Bridge spike proves acceptable startup/FPS/memory on the target device matrix.
- [ ] Original asset IDs, crop/mask versions, and transform history remain traceable.
- [ ] Invalid motion/target/bounds are rejected before playback.
- [ ] Segmentation failure falls back to whole-drawing reveal or transform-only motion.
- [ ] No generated visual is applied without an approval record.

## Handoffs

- To Person 4: playback events, media timing, and handoff start events.
- From Persons 1/2/4: versioned review and experience contracts.

Implementation is blocked until this plan and the visual gate rules are approved.
