# Real family video — one visual refinement pass

2026-10-09, FEAT-030 revision 15. **PARTIAL / VISUAL_QA_NOT_PASSED.** A new actual MP4 was encoded and inspected through decoded frames and sequential decode. Original final artwork remains exact before encoding; drawing rhythm and early face readability improved, but coloring still visibly reveals patches. No further threshold iteration was performed. Stop for owner video review.

## Inputs, permission and Git baseline

Same original `<owner-downloads>/familly.jpg` (owner's `family1.jpg` alias), JPEG 594×336; SHA-256 `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`. Same nine source masks, identities and manifest; SHA-256 `693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14`. Private source references remain in benchmark JSON; independent validation checked all nine mask hashes. No mask, source, palette, texture, geometry or layout substitution. Permission is provisional static benchmark use, not Gate A/B/product/motion approval.

Checkout: owner's existing `Sketch2Life` Git worktree; branch `codex/feat-018-contract-plan`, HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`, index empty before changes. Existing Milestone 2.1/stroke-fix edits, three V1 source/test edits, unapproved hand drafts and pilot artifacts were preserved. Extractor, renderer and schedule were snapshotted before this pass in the private output directory. No reset, stage, commit, push, merge or deploy.

## Diagnosed causes and changes

### Fragmented lines, 5–9 seconds

Before, percentile/edge selection still identified many isolated colored-pencil/JPEG edge islands. Bounded tracing kept them correctly but converted them into thousands of little pen lifts. Tile seams also ended otherwise adjacent paths. Renderer displayed source pixels through these little marks, producing the observed confetti appearance; it was not missing-image substitution.

Added explicit offline `strategy="visual"`, leaving the previous `refined` strategy available unchanged. One fixed coherence rule defers tiny components below five selected pixels unless they contain dark ink (maximum RGB channel ≤90). Small dark marks such as eyes remain selected; continuous components remain selected. Deferred pixels are restored by original-pixel coloring, not removed from final art. This is a heuristic: a small colored semantic detail can appear only during color, and there is no claim of semantic recognition. Adjacent endpoint joining reconnects paths only across source-selected neighboring pixels, never by bridging blank coordinates; all retained coordinates are conserved, paths stay bounded to 256 vertices.

Detail path count **3,295 → 1,303**. Mother detail paths 265→78; father 338→126; child 162→29. The decline is evidence of fewer pen lifts, not a standalone proof of artistic quality. Coherence rejects noise as ink, so `retained_structural_fraction=1` refers to the post-classification selected structure, not all prior candidates or semantic details. Texture diagnostics now also include augmented thin-line candidates deferred by coherence.

### Patch-like color, 10–16 seconds

Old color tracks used long diagonal passes, width 11, ordered by recursively interleaving midpoint intervals. Large distant patches appeared before neighboring gaps were filled.

The opt-in pass uses short mask-bounded alternating pencil tracks (up to 32 pixels), width 7 and overlapping rows every three pixels, grouped locally. Pen lifts at mask holes; uncovered mask tips receive explicit source-only dot tracks. The brush reveals original RGBA, not generated fill, a rectangle primitive or opacity fade. Coverage and resource budgets are checked; no final-frame artwork replacement.

**Residual failure:** although individual tracks are smaller, their local 32×24 traversal groups still create visibly block-like completion fronts. The grouping is internal trajectory ordering, not replacement geometry, but the observed result is still insufficiently natural and is not presented as authentic pencil drawing. Color paths increased **1,379 → 3,713**; total paths 4,848→5,190. At 24 FPS in 20 seconds many short paths occur within one frame. This temporal compression plus grid-group ordering remains a concrete visual blocker. No additional tuning/render loop was run to hide that failure.

### White diagonal stripes, 17–18 seconds

Independent mask/schedule reconstruction of the old run found at 17 seconds: path had 12,328 active pixels not revealed, remaining-background had 18,692. At 18 seconds: only remaining-background had **5,497 unrevealed active pixels**. At completion every object had zero uncovered pixels. The diagonal white slits follow queued diagonal color tracks in the final region: **schedule/trajectory gaps**, not holes in reviewed masks, wrong compositing alpha or inadequate final coverage.

Replacing diagonal interleaving removes that diagonal slit pattern in the inspected new 18-second frame. It does **not** solve all unfinished-region artifacts: that frame instead has a white block-like residual area near the left background, because remaining-background coloring runs from 17.278 to 18.800 seconds. It is explicit unfinished drawing, not a restored mask or perfect coverage at 18 seconds. No concealment by full-image fade or final source snap.

### Opening and object order

Renderer reserved 18% = **3.6 seconds** for cleared background even though the nine masks partition the whole image and this cleared background is entirely white. Verified `background_contains_marks=false`; white-on-white reservation had no visual work. Renderer now skips only this blank reservation, keeping the prior behavior when actual unmasked background marks exist.

Schedule option `object_first=True` respects caller draw order: outline → detail → color for each object, with separate phase budgets 20%/25%/55% and per-object area weighting. Default schedule remains phase-first for existing callers. Same benchmark order: mother, father, child, house, tree, garden, sky, path, remaining-background. No automatic semantic planner or architecture change.

Actual new completion times: mother 1.694 s, father 3.304 s, child 4.573 s, house 6.667 s, tree 8.100 s, garden 10.817 s, sky 13.127 s, path 16.278 s, remaining-background 18.800 s; final hold 1.2 s. Shared hand pieces belong to different masks and therefore complete at different object times; static-mask acceptance does not imply a natural motion/hand sequence.

## Actual MP4 comparison

New video: silent H.264, **20 seconds, 24 FPS, 480 frames, 594×336**. Both videos sampled at identical indices `min(479, round(seconds*24))`: 3, 6, 9, 12, 15, 18 and 20 seconds. The last sample represents the final frame at approximately 19.958 seconds, not a nonexistent frame at t=20.

| Time | Before MAE to source | After MAE to source | Observed comparison |
| --- | ---: | ---: | --- |
| 3 s | 53.5568 | 43.1303 | Before effectively blank; after mother complete and father coloring. |
| 6 s | 45.3338 | 34.3425 | After family complete/readable, house in progress instead of global scattered dots. |
| 9 s | 40.2815 | 26.0676 | After earlier objects complete; garden details in progress. |
| 12 s | 22.7978 | 18.5672 | Foreground complete; sky locally revealing, still patch-like. |
| 15 s | 12.1870 | 12.3828 | After not better on this metric; path and background remain incomplete. |
| 18 s | 3.8576 | 3.6245 | Old diagonal slits gone, new unfinished background patch remains. |
| Final | 2.6179 | 2.6166 | Both preserve final composition, with H.264 codec differences. |

MAE at intermediate times measures progression toward the source, **not visual naturalness**. At 18 seconds decoded-white candidate counts actually increase 4,263→5,757 despite lower MAE. Thus this is not a blanket improvement or eradication of incomplete regions. Contact sheet and individual native frames preserve these failures for review.

All 480 encoded frames decoded successfully. Maximum adjacent decoded-frame MAE decreases **1.666712→0.651672**; this global statistic can hide local pops and is not acceptance. Penultimate→final difference is zero, final twelve steps zero; no measured end-frame snap. Raw milestone and all requested raw fixed-time samples contain exact source pixels or white only.

Final raw PNG versus decoded original JPEG: **MAE 0, changed pixels 0, full source coverage 100%**. Encoded final MAE 2.616644/255; native face/hair/glasses/hands/shoes/branches/flowers comparisons and codec difference maps are supplied. No inspected major final feature is missing; no claim of perfect semantic fidelity in every intermediate frame.

Extraction 1.9252 s (prior 1.6491), render/encode 21.3125 s (prior 21.4257), total 23.7526 s (prior 23.5934). Parent lifetime peak working set 99,512,320 bytes (~94.9 MiB), excludes FFmpeg child; no controlled repeated timing study. Existing canvas, point/path, density, per-frame schedule and cooperative deadline limits remain. The real run is under these guards.

## Tests, compatibility and limits

Final focused suite: **128 passed in 91.19 seconds, exit 0**, no skips/failures inside selection. New visual-pass suite: 7 passed in 0.91 seconds. Coverage includes source-bound family/ocean PNG/JPEG, mask-hole/tip color coverage, seam adjacency and conserved pixels, tiny noise versus dark eye marks, object-first order, exact final raw pixels, blank-background start, dense flower PNG/JPEG under both strategies, V1 raster/planner and API contracts.

```powershell
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_whiteboard_v2_visual_pass.py backend/tests/unit/test_whiteboard_v2_complexity.py backend/tests/unit/test_whiteboard_v2_visual_refinement.py backend/tests/unit/test_whiteboard_v2_engine.py backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py backend/tests/contract/test_story_video_file_api.py
```

Ruff passes on four touched source modules and two touched test files. Mypy with `--follow-imports=silent` passes on four source modules; not whole-backend typing. Old extraction literals remain accepted; optional visual mode emits `MASK_BOUNDARY_AND_COHERENT_TEXTURE_V4`/`COHERENT_SOURCE_INK_V2`. External strict older readers need updates before consuming this optional format. Old `refined` extraction and phase-first scheduling stay defaults; V1 remains default, V2 application flag OFF, no V2 HTTP/Gate changes. Repository-wide and Vision V3 tests were not run; no entire-repository PASS claimed. No LightningAI, audio, motion, transitions or full-story acceptance.

`git diff --check` exits 0. Configured repository security scanner exits 0: `REPOSITORY_SECURITY_VALID`, 1,659 publishable files scanned, protected environment/credentials/private reference classes excluded. This is not a comprehensive security assessment. Direct introspection confirms both Settings and pipeline constructor V2 defaults are False. Final HEAD remains the baseline SHA; index empty. No remote fetch or write occurred.

## Files changed in this pass

- `backend/src/sketch2life/infrastructure/media/object_stroke_engine_v2.py`: optional coherence, seam joining and localized color tracks; earlier dirty edits preserved.
- `backend/src/sketch2life/contracts/schemas/story_strokes_v2.py`: explicit optional visual extraction/heuristic identifiers, old forms retained.
- `backend/src/sketch2life/application/services/story_draw_schedule_v2.py`: opt-in object-first phase budgets.
- `backend/src/sketch2life/infrastructure/media/whiteboard_renderer_v2.py`: omit only empty white background time.
- `backend/tests/unit/test_whiteboard_v2_visual_pass.py`: new seven-case suite.
- `backend/tests/unit/test_whiteboard_v2_complexity.py`: dense flower cases additionally exercise optional visual mode.
- FEAT-030 plan, approval, context, decisions, status, evidence index and this report.

Private comparison/validation drivers and source snapshots are not Git assets. No prior V1 edits, hand drafts or historical media were overwritten.

## Artifacts and reproduction

Private root: `D:/Codex/Sketch2Life/real_visual_refinement_2026-10-09/`.

- [New actual MP4](D:/Codex/Sketch2Life/real_visual_refinement_2026-10-09/real-family-v2-static.mp4).
- [Before/after at all seven requested times](D:/Codex/Sketch2Life/real_visual_refinement_2026-10-09/before-after-3-6-9-12-15-18-20.png).
- `before-03s.png` through `before-20s.png`, corresponding `after-*.png`, raw `after-raw-*.png`.
- `real-family-v2-0-25-50-75-100-decoded.png`, `final-raw.png`, `final-decoded.png`, source/raw/decoded difference maps, critical feature/detail contact sheets.
- `before-gap-diagnosis.json`, `fixed-time-comparison.json`, `after-timeline-validation.json`, `video-quality-checks.json`, `benchmark-metrics.json`, source-bound stroke/schedule/world/scene JSON, registry cutouts, original provisional permission metadata.
- `extractor.before.py`, `renderer.before.py`, `schedule.before.py`; after snapshots and `artifact-sha256.json` for evidence provenance.
- `run_benchmark.py`, `diagnose_before.py`, `compare_video.py`, `review_video.py`, `analyze_after.py`: exact local source/mask-bound reproduction and validation. Use checkout Python virtualenv, copy driver to a new private output directory for another run rather than overwrite this evidence. Driver label corrected from inherited `refined` to actual `visual`; emitted V4 records identify the strategy actually rendered.

Original MP4 remains unchanged at `D:/Codex/Sketch2Life/real_stroke_fix_2026-10-09/real-family-v2-static.mp4`, SHA-256 `cf3c1b7f6455e1eef1d303d0b2263995f403ba9dfbf6e7a0285f714f5feb99bf`. New SHA-256 `8e6a167a132f5e45119faa7b1d4fb3bd3027642a519b761fe48586520e68d16f`.

## Review verdict and stop

**VISUAL_QA_NOT_PASSED**: more readable early figures and fewer scattered paths, but grid-like color reveal, rapid compressed pencil movements, incomplete late background and semantic uncertainty of raster pen order remain. Mask grouping and one-image inference do not recover original drawing gestures. Final artwork fidelity is not whiteboard animation quality acceptance. No further visual algorithm changes or milestone work are authorized by this result. Await owner review of the new actual MP4.
