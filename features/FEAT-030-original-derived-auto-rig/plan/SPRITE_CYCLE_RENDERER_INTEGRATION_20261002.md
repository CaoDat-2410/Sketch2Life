# Sprite-cycle PixiJS integration — additive task plan

- Feature: FEAT-030 with FEAT-028 asset lifecycle
- Revision: 1
- Status: APPROVED BY OWNER'S DIRECT IMPLEMENTATION REQUEST
- Date: 2026-10-02
- Parent: approved FEAT-030 plan revision 5 and ADR-030-08

## Authorized scope

The owner explicitly approved the pending sprite batch visually and requested that the cycles be
connected to the PixiJS renderer, potential bugs fixed, lifecycle gates retained, and diagnostics
added. This task records visual approval only for the 30 sheets / 120 frames in
`FEAT-028/assets/generated/motion-cycle-review-manifest.rev1.json`. It does not infer legal rights
clearance or bypass renderer/device acceptance.

1. Preserve the generated source files and their hashes. Copy visually approved sheets to
   FEAT-028 `assets/approved/`; do not put them in `applied/` until runtime/device review.
2. Add an additive, versioned motion-cycle transport and PixiJS frame player. Existing FEAT-018
   V1/V2 and FEAT-030 renderer V1/V2/V3 contracts remain byte-for-byte compatible.
3. Use stable cycle/frame IDs and capability-bound PNG frame reads. The backend must reject cycles
   unless visual review, provenance/rights, frame/crop/pivot/loop QA, catalog registration, renderer
   verification, and runtime eligibility all pass. Model/mobile data may never provide a path or URL.
4. Synchronize frame selection to the existing show playback clock so pause, seek, replay, completion,
   teardown, and loading/error behavior stay deterministic. Keep the original drawing primary,
   camera fixed, and companion sprites inside safe placement bounds.
5. Add bounded, sanitized cycle lifecycle logs and typed renderer diagnostics. Never log media,
   source/crop data, capability tokens, provider payloads, or exception messages.
6. Treat the wooden-cube slide sheet as a single-frame transform-driven slider, not a four-frame
   locomotion cycle; do not claim frame animation for repeated poses.

## Acceptance criteria

- AC-CYCLE-01: The 30-sheet batch is recorded as owner-visually-approved; original generated files
  and SHA-256 values remain unchanged, and approved copies are provenance-linked.
- AC-CYCLE-02: New backend/TypeScript contracts are additive; old contracts and old-client parsing
  tests remain unchanged and passing.
- AC-CYCLE-03: Server frame reads enforce allowlisted cycle/frame IDs, exact source hash, dimensions,
  layout bounds, per-frame PNG/hash/size limits, short-lived single-purpose capabilities and all
  runtime gates. Any incomplete or unknown gate fails closed with a safe reason code.
- AC-CYCLE-04: Pixi renders an approved four-frame cycle at a bounded frame rate using the existing
  playback time; seeks and pause/resume are deterministic; one-shot cycles settle; cleanup releases
  textures and callbacks; failures preserve the source and never trigger fallback/retry.
- AC-CYCLE-05: Gate A subject identity and Gate B activity remain authoritative; the closed registry
  chooses only a compatible cycle. No model-produced code, arbitrary URL, or unreviewed ID reaches Pixi.
- AC-CYCLE-06: Structured logs cover blocked, capability issued/read, frame decode, ready, playback,
  and failure outcomes. Logs contain bounded cycle/class/frame identifiers and allowlisted codes only.
- AC-CYCLE-07: Tests cover incomplete rights/QA/catalog gates, stale/expired/oversized/tampered frames,
  malformed layouts, unknown classes/cycles, bad hashes, clock seeks, pause/replay/teardown, and legacy
  V1/V2/V3 compatibility.
- AC-CYCLE-08: No cycle becomes production-runtime eligible until separate rights/provenance and
  technical QA are explicitly cleared, and fresh Android visual acceptance is recorded.

## Implementation sequence and verification

1. Record the visual decision and approval provenance; run the repository visual-asset gate checks.
2. Add an ADR addendum and parity-checked Python/TypeScript schemas for cycle reads and the new command.
3. Add a manifest-backed backend frame-capability service and attach only gated cycle data to the
   additive show envelope.
4. Add the Pixi clock-synchronized cycle player, safe error codes/log events, and focused unit tests.
5. Run backend/renderer tests, typecheck/build, repository harness and security validator; record
   exact outputs under FEAT-028/FEAT-030 evidence.
6. Keep live asset activation disabled if any required provenance, rights, QA, or Android gate is
   still pending; report the exact remaining blocker rather than claiming a live sprite demo.

## Risks and controls

- Atlas cell bounds can be ambiguous or off-grid: derive cell rectangles deterministically, validate
  against the declared canvas, decode each crop and reject questionable sheets without guessing.
- Sprite cycles can look like replacement art: render only as a bounded companion layer, never over
  the confirmed source subject; reject unsafe overlap.
- Rapid frame changes/own Pixi ticker can desynchronize playback: drive frames from the single show
  clock and test pause/seek/replay and texture cleanup.
- Visual approval can be mistaken for rights/production approval: keep explicit separate gates and
  leave current runtime eligibility false.
