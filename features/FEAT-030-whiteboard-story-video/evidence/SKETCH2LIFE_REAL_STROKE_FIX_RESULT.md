# Real image stroke overflow fix — 2026-10-09

## Decision

**TECHNICAL FIX PASS / OVERALL PARTIAL / VISUAL_QA_NOT_PASSED.** The actual family-image benchmark now produces a silent 20-second H.264 MP4, 594×336, 24 FPS, 480 decoded frames. All nine original source regions are processed. This is an experimental static drawing reveal, not object animation, a narrated story or LightningAI acceptance. Stop for owner playback/review; no Milestone 3, commit, push or deploy.

## Input and approval

The owner's `family1.jpg` name resolves to the reattached original `<owner-downloads>/familly.jpg`; no substitute/generated image was used. The exact local path is recorded in the private benchmark inputs. JPEG RGB, 594×336; source SHA-256 `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`.

Original nine-mask manifest: `D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/source-object-manifest.json`, SHA-256 `693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14`. Independent verification confirms source, original masks and manifest unchanged. Stable IDs remain `family-52caf90a-` plus mother, father, child, house, tree, garden, sky, path and remaining-background. No rectangle/ellipse substitutes, identity changes, recoloring, diffusion or geometry redraw.

Permission is **PROVISIONAL BENCHMARK APPROVAL**, not product quality or server Gate A/B approval. Local benchmark event/fact/anchor metadata is scaffolding, not authenticated approved narration. Original candidate-mask review labels were not promoted to server approval. These masks permit a static reveal only; shared hands, fine contours and grouped garden/background regions are not certified for motion.

## Cause and scoped repair

The historical run failed in `object_stroke_engine_v2.py`, `_paths_legacy(details, limit=2000)`. Garden had **2,798 interior local-contrast detail candidates**, not outline points; its outline had 767 candidates below the separate 4,000-point guard. FIND_EDGES plus the object-local percentile threshold sees both real flowers/stems/leaves and colored-pencil/grass/JPEG texture. It is not a semantic contour detector.

The 2,000 guard bounded construction/traversal of a global neighbor dictionary and edge set, repeated endpoint search, path growth and downstream rendering load. It was an implementation resource guard, not a semantic maximum object complexity. Refined extraction previously evaluated the legacy detail graph before refinement, so it failed before it could handle complexity.

The refined experimental branch now:

1. Separates candidates using persistent contrast after a small Gaussian blur, dark ink and strong chromatic accents. Extra dark thin-line candidates protect features missed by percentile selection. This is a disclosed heuristic, not semantic certainty.
2. Traces selected structure in **32×32 tiles**, retaining original asset coordinates and every selected pixel, including isolated dots/seams. Paths have at most 256 vertices; tile boundaries cause pen lifts, not source/mask edits. Small outlines retain the previous minimum-fragment strategy plus previously omitted isolated points.
3. Defers rejected high-frequency candidates to mask-clipped **original-pixel color brush reveal**. Diagonal color runs stop at mask holes, then lift; flat-color regions retain their source-mask runs. No full-image opacity fade, rectangular wipe or final-frame source replacement.
4. Fails with `NEEDS_STROKE_REVIEW` if selected structure exceeds bounded budgets or cannot be retained. Legacy detail limit remains 2,000; refined processing is not just that limit increased.

Garden: 2,798 raw candidates → 2,503 retained raw structural pixels + 31 additional dark-line pixels = **2,534 structural pixels**; **295 raw texture candidates** deferred to color. Structure still exceeds 2,000, so clustering—not pruning alone—resolves the blocker. Largest garden trace tile holds 196 pixels. Some pencil grain still passes the heuristic and can produce fragmented detail strokes.

Budgets: ≤1,024 transient trace pixels/tile; ≤24,000 selected pixels/traced phase; ≤4,096 aggregate paths/object; cutouts ≤2,048 edge and 2.07 megapixels; existing density guard remains. Renderer allows 8–30 FPS, ≤600 frames and ≤18 scheduled strokes/frame on average, checks full mask coverage before encoding and adds a default 120-second cooperative deadline. Native Pillow/FFmpeg calls cannot be forcibly interrupted by this deadline. These bound work, but are not an OS-enforced memory quota or a hard total extraction timeout.

## Actual counts and performance

Counts below are emitted paths, not raw candidate pixels. Full diagnostics and individual extraction times are in `benchmark-metrics.json`.

| Object | Outline | Detail | Color | Raw detail | Structural pixels | Texture deferred |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mother | 10 | 265 | 117 | 802 | 748 | 129 |
| father | 8 | 338 | 84 | 724 | 964 | 111 |
| child | 5 | 162 | 62 | 419 | 375 | 73 |
| house | 3 | 362 | 75 | 1607 | 1271 | 338 |
| tree | 39 | 148 | 118 | 488 | 447 | 47 |
| garden | 5 | 555 | 77 | 2798 | 2534 | 295 |
| sky | 62 | 423 | 175 | 1624 | 1260 | 365 |
| path | 20 | 741 | 282 | 3453 | 2775 | 684 |
| remaining-background | 22 | 301 | 389 | 1671 | 1435 | 241 |
| Total paths | 174 | 3295 | 1379 | | | |

Total scheduled strokes **4,848**. Extraction **1.6491 s**, render/encode/milestone extraction **21.4257 s**, whole driver **23.5934 s**. Windows parent-process lifetime peak working set **100,405,248 bytes (~95.8 MiB)**; excludes FFmpeg child and is not incremental renderer memory.

Before: failure after five objects, entire failed attempt 1.695 s; no MP4 or comparable full render/memory metric. Old mother/father/child/house/tree outline-detail-color counts: 6-147-65 / 3-131-70 / 2-94-47 / 3-240-76 / 29-86-56. New counts are higher: retention/clustering trades bounded graphs for additional fragments. Do not interpret the successful run as a demonstrated speed or stroke-naturalness improvement over a complete prior video that never existed. Before-code snapshots and historical failure artifacts are preserved outside Git.

## Fidelity and visual review

Original decoded JPEG → canonical target → final raw PNG: **MAE 0, changed pixels 0, source-mask color coverage 100%**. Final H.264-decoded frame MAE is **2.617863/255**, reflecting lossy encoding. Fidelity is measured against decoded source pixels, not JPEG compressed bytes.

Independent sequential decode verified all 480 frames. Raw 0/25/50/75/100% milestones contain source pixels or white only, not opacity-interpolated/repainted pixels. Maximum consecutive decoded-frame MAE is 1.666712 (frame 275); penultimate-to-final MAE 0; maximum over the final 12 frame steps 0.000962. This rules out a measured final full-source snap but does not certify the absence of every local sudden appearance.

Native detail comparisons show recognizable eyes, glasses, hair, clothes, shared hands, feet/shoes, tree branches and flowers in the finished frame. Every checked raw ROI has MAE 0. Decoded ROI MAE: mother face/hair 3.3984; father eyes/glasses/hair 1.6563; child face 3.2130; shared hands 2.8220; clothes 2.9877; feet 2.5524; branches 4.0141; flowers 1.9500. H.264 softens fine edges and pencil grain; difference-pixel counts are not counts of missing semantic details.

**Stroke naturalness remains inadequate:** fragmented/scattered detail reveal, mechanical tile/brush ordering, faces completing late during color, no reconstructed human pen order or hand overlay. Source coloring texture is preserved at completion but progressively revealed patches do not reproduce authentic pencil coloring gestures. No obvious major final-source omission was found in the inspected sheets, yet this is not full human playback acceptance. **VISUAL_QA_NOT_PASSED** remains unchanged.

## Changed files in this task

- `backend/src/sketch2life/infrastructure/media/object_stroke_engine_v2.py`: structural/texture split, bounded trace clusters, mask-hole-safe source-color paths and resource guards.
- `backend/src/sketch2life/contracts/schemas/story_strokes_v2.py`: optional diagnostics and explicit refined extraction-method version.
- `backend/src/sketch2life/infrastructure/media/whiteboard_renderer_v2.py`: frame/FPS bounds and cooperative render deadline; no aesthetic redesign.
- `backend/tests/unit/test_whiteboard_v2_complexity.py`: eight dense/texture/PNG/JPEG/hole/budget/deadline tests.
- `backend/tests/unit/test_whiteboard_v2_visual_refinement.py`: refined method-version expectation only in this task; file already contained Milestone 2.1 work.
- FEAT-030 `plan/PLAN.md`, `approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md`, and this report: scope, permission and results.

Other existing dirty files remain uncommitted and were not attributed wholesale to this fix. Three preexisting V1 source/test changes, four hand drafts and earlier pilot artifacts remain untouched by this task. Index remains empty.

## Tests and compatibility

Final focused regression command (run from checkout, using its virtualenv):

```powershell
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_whiteboard_v2_complexity.py backend/tests/unit/test_whiteboard_v2_visual_refinement.py backend/tests/unit/test_whiteboard_v2_engine.py backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py backend/tests/contract/test_story_video_file_api.py
```

Final result: **119 passed in 84.27 seconds, exit 0**, no failures/skips/deselections within this explicit selection. Earlier scoped run before the additional hole-direction case: 118 passed in 82.16 seconds; final 27-test complexity/refinement subset: 27 passed in 7.25 seconds. Scope includes synthetic family, ocean PNG/JPEG, two-scene state/identity, missing/invalid masks, dense textured flowers PNG/JPEG, source fidelity/coverage and V1 planner/raster/API regression. No full-repository PASS is claimed. Vision V3 suites are outside this selection; they were not rerun, and historical missing-fixture failures are not repaired here.

Ruff: five touched source/test files pass. Mypy: three touched V2 source modules pass with `--follow-imports=silent`; this is not whole-backend typing. Six prior V2 stroke records with `MASK_BOUNDARY_AND_LOCAL_CONTRAST_V2` deserialize successfully with diagnostics absent. New refined writer emits `MASK_BOUNDARY_AND_STRUCTURAL_TEXTURE_V3`; external strict old readers need a schema update before consuming it. No V2 HTTP endpoint enabled.

Both Settings and pipeline constructor defaults for V2 are verified **False**; V1 remains the default and there is no V2→V1 success fallback. No server approval, upload, LightningAI, paid inference, TTS, motion or full story acceptance test was run.

`git diff --check`: exit 0. `backend/.venv/Scripts/python.exe tools/validate_repository_security.py`: exit 0, `REPOSITORY_SECURITY_VALID`, 1,657 publishable files scanned; environment/credentials/private reference classes excluded. This is the repository's configured scanner, not a claim of comprehensive security assessment. Branch remains `codex/feat-018-contract-plan`, local HEAD and existing remote-tracking HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`; no fetch, commit or index changes. Ruff command: `backend/.venv/Scripts/python.exe -m ruff check` followed by the three modules and two tests listed above. Mypy command: `backend/.venv/Scripts/python.exe -m mypy --follow-imports=silent` followed by the three modules.

## Private evidence and reproduction

All real-image media, masks/cutouts and scripts remain **outside Git** under:

`D:/Codex/Sketch2Life/real_stroke_fix_2026-10-09/`

- `real-family-v2-static.mp4`: actual encoded static drawing benchmark.
- `real-family-v2-0-25-50-75-100-decoded.png`: milestones sampled from the encoded MP4; unsuffixed PNG is raw milestones.
- `final-raw.png`, `final-decoded.png`: exact source final versus decoded final.
- `diff-source-raw.png`, `diff-source-raw-x4.png`, `diff-source-decoded.png`, `diff-source-decoded-x4.png`.
- `critical-source-decoded-differences.png`, `source-final-difference-contact-sheet.png`: native feature/detail review.
- `benchmark-metrics.json`, `video-quality-checks.json`: counts, timings, memory, decode checks, fidelity and unchanged-source/masks verification.
- `partial-strokes.json`: despite inherited filename, contains **all nine** extracted objects; `draw-schedule.json`, `benchmark-world.json`, `benchmark-scene.json`, `provisional-approval.json`, `registry-cutouts/`.
- `*.before.py`: pre-fix module snapshots. `artifact-sha256.json`: finalized private artifact checksum inventory.
- `run_benchmark.py`, `review_video.py`: exact local input/mask-bound driver and independent artifact validation. With the same permitted source/masks present, run using the checkout virtualenv: `backend/.venv/Scripts/python.exe D:/Codex/Sketch2Life/real_stroke_fix_2026-10-09/run_benchmark.py`, then `review_video.py`. Do not overwrite these accepted evidence paths for another experiment; copy the driver and select a new output directory.

Historical baseline remains at `D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/benchmark-01/` and [the prior failure report](SKETCH2LIFE_REAL_IMAGE_BENCHMARK.md).

## Remaining limits and stop condition

The requested overflow blocker is resolved and a real MP4 exists. Automatic semantic stroke recognition, artistic pen order, seamless path joining, natural coloring, mask motion suitability, authenticated story approvals, durable product storage and LightningAI acceptance remain outside this fix. Larger/dense inputs may still return explicit review/timing errors rather than silently drop important structure. Owner should inspect this MP4 before authorizing any further visual changes. No automatic Visual QA promotion and no further algorithm iteration in this task.
