# Subject/behavior registry plan review — 2026-10-01

- Evidence ID: E-030-REGISTRY-PLAN-001
- Type: source/code architecture review for planning
- Input: inspect FEAT-030 revision-4 plan/approval, `backend/src/sketch2life/application/services/pixi_show_compiler.py`, FEAT-028 catalog/review, FEAT-030 rig archetypes, and the owner's request to add comprehensive subject behavior classes.
- Environment: local Windows checkout, branch `codex/pixi-ai-show-20261001`.
- Date: 2026-10-01.
- Finding: revision 4 separates behavior class from structural rig archetype, but its examples
  emphasize walker/flyer and the current compiler enforces a limited closed mapping. FEAT-028 has
  144 static catalog frames, not 144 animation cycles. The seven generated motion sheets now have
  owner visual approval for 28 proposed frames; they are still not rights-cleared, cropped,
  catalogued, or renderer/runtime-verified.
- Code audit: current contract exposes six behavior classes and nine subject hints; the compiler's
  current compatibility table does not yet model human gestures, plant motion, or broad
  scene/object behaviors as first-class classes.
- Output: `../../plan/PIXIJ_SUBJECT_BEHAVIOR_CLASS_REGISTRY_REV5_DRAFT_20261001.md`.
- Interpretation: propose a separate versioned subject-family / rig-archetype / behavior-class
  registry, explicit supported/static/unknown states, complete mapping of currently supported Gate-A
  and FEAT-028 topics, and deterministic AI/renderer allowlists.
- Owner clarification received: the target is full current Gate-A/FEAT-028 coverage plus a reviewed
  extension path, and a subject may hold multiple compatible capabilities for per-beat AI selection.
- Owner also confirmed that plants and relevant non-living scene/effect motion are in scope.
- Owner then expanded the requirement: every supported non-static motion class must have
  motion-sprite coverage, not only gap-driven examples. The owner clarified that one or more cycles per class
  should be reused across compatible subjects, with variants where morphology/action differs; unique
  cycles for every catalog item are not required.
- Limitations: this was a planning review, not an exhaustive domain ontology. At review time,
  revision 5 was awaiting approval; it was later approved and implemented under the recorded plan.
- No tests, model/provider requests, asset promotion, or runtime changes were part of this review.
  Later registry and renderer implementation evidence is recorded separately in FEAT-030.
