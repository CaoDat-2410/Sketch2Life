# Audit of user-supplied ERD screenshots — 2026-10-23

## Conclusion

The three crops match the last-known Drive baseline, not the current FEAT-048 branch artifact. The baseline file `evidence/raw/DRIVE_BASELINE_ERD_RECHECK_20261023.drawio` has SHA-256 `4d5e2f54e0066b8f9e95108ce593ad426ba221c6d89bd43860679ccad3a4ac39`, which also matches its Drive readback recorded in `TECHNOLOGY_LOGOS_AND_MERMAID_20261023.md`. Its actual viewer render is `evidence/screenshots/erd_recheck_20261023.png`. The full baseline audit found six detached relationship diamonds (12 unbound connector targets); the supplied crops show three examples. The current published artifact has SHA-256 `b5b33a5f55ccdf88971f686e7d572537f6268620e23dd042238447b2562aa040` on `feature/feat048-srs-diagram-pack` (source commit `2c37ad97`; preceding status commit `8c47fa08`).

## Screenshot findings

- `checkpoints`: baseline connector cells 246 and 247 have no `target` reference, so the relationship diamond is genuinely detached in that copy. In the current artifact, both connectors target diamond 269: `CanvasDocument`–`checkpoints` is labeled `1`, and `CanvasSnapshot`–`checkpoints` is `0..N`. The clean current viewer render shows both vertical connectors.
- `personal canvas`: baseline connector cells 261 and 262 have no target; their endpoint labels are also reversed (`ChildParticipant` `0..N`, `CanvasDocument` `0..1`). Current connectors target diamond 271 and show `ChildParticipant` `0..1` and `CanvasDocument` `0..N`. The blue arrows and blue X marks around the diamond in the supplied crop are Draw.io selection controls; they are not part of the exported diagram.
- `reviewed`: baseline connector cells 252 and 253 have no target, leaving the `0..N` label detached from the relationship and close to the page edge. Current connectors target diamond 270, with `SketchProposal` `1` and `TeacherReview` `0..N`; the labels sit beside their respective endpoints in the clean render.
- The grey region beyond the white page is the editor canvas. In the current artifact, all vertex bounds fit within the 3400×2050 ERD page; no entity, relationship, or attribute is out of bounds.

## Full current-source check

The current ERD has 21 named relationship diamonds; every diamond has exactly two entity connectors. All edge source/target references resolve, and no vertex exceeds the page bounds. The official diagrams.net render at `evidence/screenshots/erd_final_refinement_20261023_r2.png` is 3372×1987 with no failed images, page errors, or blocked requests. The model remains 17 entities, 21 relationships, and 37 selected attributes. The SRS review and unresolved logical caveats remain in `ERD_FINAL_AUDIT_AND_LAYOUT_20261023.md`.

No diagram source change was needed in this review: the current published artifact is already corrected. The supplied screenshots expose the stale Drive copy, which was not replaced after the earlier upload was rejected by automatic approval review. This review does not update Drive or publish screenshot images; it records the source/version mismatch and gives the exact current branch artifact for review.
