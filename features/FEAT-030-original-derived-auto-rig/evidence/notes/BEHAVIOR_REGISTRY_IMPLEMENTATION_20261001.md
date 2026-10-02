# FEAT-030 subject/behavior registry implementation — 2026-10-01

## Scope and result

Implemented the approved revision-5 domain taxonomy and offline motion-cycle coverage. The registry
keeps semantic family, rig archetype, behavior class, and action primitive separate. It defines 29
closed behavior classes, compatible families and source roles, cycle IDs, and readiness states.
Subjects can hold multiple capabilities; the topic map never treats a label as proof that a source
mask or sprite is ready to animate.

All 144 topic IDs in FEAT-028 catalog v2 are covered. The mapping includes explicit still/unknown
outcomes and exact morphology fixes for people, mollusks, insects, aquatic mammals, and flying
reptiles. Every behavior class has cycle provenance: 37 four-pose cycles total, comprising seven
previously visually approved concept sheets and 30 new sheets / 120 frames awaiting owner visual
review.

The registry is domain-only and is not wired into frozen FEAT-018 transport contracts or public AI
schemas. It does not enable animation by itself. Runtime selection remains empty until the sprite,
rights, technical frame, catalog, renderer, provider/contract, and device gates are met.

## Asset boundary

All new sheets are in FEAT-028 `assets/generated/`, linked in
[`SPRITE_MOTION_REVIEW_BATCH_REV2_20261001.md`](../../../FEAT-028-pixi-topic-asset-library/assets/generated/SPRITE_MOTION_REVIEW_BATCH_REV2_20261001.md).
The adjacent `motion-cycle-review-manifest.rev1.json` records file hashes, canvas dimensions,
ImageGen output IDs, prompt summaries, visual state, and common alpha/rights/technical/runtime gates.
One wooden-cube slide draft has near-identical poses and is explicitly flagged for revision/rejection
review. It is not represented as a usable cycle.

No new sheet is visually approved, rights-cleared, crop/pivot/loop verified, catalogued, promoted to
`approved/` or `applied/`, or referenced by runtime. The seven older approved sheets retain only the
previously recorded visual approval; their separate rights/technical/runtime gates remain open.

## Verification

Run from the repository root:

```powershell
python -m pytest -p no:cacheprovider backend/tests/unit/test_pixi_behavior_registry.py -q
python -m ruff check backend/src/sketch2life/domain/experience/pixi_behavior_registry.py backend/tests/unit/test_pixi_behavior_registry.py
python -m ruff format --check backend/src/sketch2life/domain/experience/pixi_behavior_registry.py backend/tests/unit/test_pixi_behavior_registry.py
```

Result: 7 focused tests passed; Ruff passed; both files were already formatted. Tests assert exactly
144 catalog topics resolve, each of 29 classes has cycle provenance, all 37 manifest cycles map to
the right class, hashes and PNG dimensions/color type match, no runtime cycle is eligible, and
unknown/static/profile morphology outcomes remain explicit.

No live AI/provider request, SAM invocation, Android run, contract edit, asset promotion, commit, or
push occurred as part of this evidence run. This evidence does not establish real drawing mask
quality, visual loop quality, renderer playback, or legal rights clearance.
