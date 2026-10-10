# Real family — bounded pencil refinement, revision 16

2026-10-09. **VISUAL_QA_NOT_PASSED / PARTIAL TECHNICAL RESULT / STOP ALGORITHM TUNING.** One new 20-second MP4 was rendered. Color paths are more continuous and pen-up/down is visible, but actual drawing remains much too fast and background completion is worse at several matched timestamps. This candidate must not replace the revision-15 video whose object-first/color ordering the owner accepted. No second tuning/render iteration was performed.

## Baseline and scope

Branch `codex/feat-018-contract-plan`, HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`, index empty. Existing source/test/docs changes, three older V1 edits, unapproved hand drafts and prior artifacts were preserved. Before snapshots of extractor, schedule and renderer are private. V1/default application behavior remains unchanged; V2 flag OFF. No commit/push/merge/deploy, story motion/audio/transitions, diffusion or paid calls.

Same original `familly.jpg`, previously resolved alias for `family1.jpg`, JPEG 594×336; SHA-256 `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`. Same nine source masks and source manifest SHA-256 `693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14`. Input and each mask hash verified independently; original bytes, source pixels, texture, colors, layout and identities unchanged. Current consent is provisional static benchmark permission, not real Gate A/B or animation-mask approval.

Before-video is the retained revision-15 artifact, SHA-256 `8e6a167a132f5e45119faa7b1d4fb3bd3027642a519b761fe48586520e68d16f`. The owner's downloaded `(1)` filename is treated as a review reference, not an independently verified file-byte alias; that exact download was not found in this local Downloads directory. Comparison uses the known previous rendered artifact, not the older revision-14 clip.

## The single implemented candidate

- New explicit optional `strategy="pencil"`; previous `visual` strategy and object-first schedule remain available unchanged. Same structural/coherence classifier: no repeated threshold adjustment.
- Connect consecutive short color hatches only when endpoint distance ≤6 pixels and every sampled connector pixel lies inside the source mask. Bounded ≤256 vertices/path; narrower width-5 brush, explicit original-pixel tip coverage corrections. No invented character paths, rectangle wipe, source replacement or opacity fade. Geometry used only for the small UI pen indicator, never to redraw people or scenery.
- Retain object-first order and phase budgets. Pencil timing uses true arc length within each object/phase and explicit two-frame pen-up at object/phase boundaries. Micro pen lifts are still sub-frame; the time budget cannot visibly show all of them.
- Add optional small code-drawn pencil-tip overlay: dark tip while down, hollow amber cue while up, interpolation between previous endpoint and next start while up. It adds no source ink during transit and disappears for the final hold. No unapproved photographic hand draft is used. Static identity pose only; unsupported transformed pen-overlay scenes fail explicitly.
- Optional 0.6-second sparse background preparation: at most 16 short source-masked prefix strokes per selected sky/path/remaining-background region, width 3. It is real source-pixel hatching, not a background-opacity reveal. Original object-first order follows; this preparation delays actual object drawing by 0.6 seconds and does not solve blank-space perception.

All options default OFF/previous mode; the candidate is only used by the private benchmark driver. New optional extraction identifier `MASK_BOUNDARY_AND_PENCIL_TEXTURE_V5`; old identifiers still accepted, strict external older readers would need updates. No new HTTP or approval architecture.

## Actual result and algorithm limit

Both actual MP4s are 594×336, 24 FPS, 480 frames, 20 seconds. Before/after decoded frames sampled at 3/6/9/12/15/18/final seconds; final uses frame 479, not a nonexistent t=20 frame. New SHA-256 `545549a9a5e93b4b7ed786a781d13b97edb5b91585ef9c40ca498bfef9383b2d`.

Scheduled paths: **5,190 → 2,414**; outline unchanged 174, detail unchanged 1,303, color **3,713 → 937**. Background prefixes are additional preparatory marks, not part of that schedule count. Mother color paths 269→104; father 185→46; child 106→30; tree 166→91. Fewer pen lifts does not establish slower visible motion.

Measured actual-time arc speeds:

| Phase | Travel pixels | Median px/s | P95 px/s | Paths shorter than one frame |
| --- | ---: | ---: | ---: | ---: |
| Outline | 12,405 | 4,465 | 6,643 | 149/174 |
| Detail | 8,106 | 1,896 | 4,309 | 1,303/1,303 |
| Color | 70,644 | 9,363 | 13,904 | 914/937 |

26 macro pen-up gaps; sampled timeline has 342 pen-down, 95 pen-up, 15 preparation and 28 final-hold frames. Down/up is now distinguishable, but fast tip jumps and strokes completing inside a single frame remain. Motion speed is not reasonably natural at this canvas size. Even a diagnostic budget of 250 px/s would require **364.6 seconds of path travel alone**, excluding pauses/preparation. This is an illustrative engineering budget, not a claimed universal human drawing speed. Current raster routes retrace/overlap many pixels; compressing them into 20 seconds cannot recover an artist's gesture order. Merging paths changes pen lifts but not the fundamental travel budget.

### Matched-time evidence

| Time | Before source MAE | Candidate source MAE | Before white candidates | Candidate white candidates |
| --- | ---: | ---: | ---: | ---: |
| 3 s | 43.1303 | 45.6674 | 146,776 | 149,708 |
| 6 s | 34.3425 | 37.8610 | 127,613 | 134,403 |
| 9 s | 26.0676 | 26.6577 | 106,301 | 108,038 |
| 12 s | 18.5672 | 19.2299 | 68,744 | 72,181 |
| 15 s | 12.3828 | 13.8511 | 39,769 | 47,176 |
| 18 s | 3.6245 | 5.6758 | 5,757 | 12,859 |
| Final | 2.6166 | 2.6204 | 0 | 0 |

Intermediate MAE/white candidates measure progression, not artistic quality. These values show the candidate is not an overall improvement in completion rhythm. Actual decoded views show readable family and unchanged object order, a visible small tip, thin scattered preparation marks, remaining patch-like coloring and large late incomplete background areas. Sparse preparation does not materially fix the background issue. Explicit pauses and preparation cost time and worsen late coverage. No additional algorithm changes were made after this evidence.

Decoded maximum adjacent-frame MAE **0.651672 → 0.794878**: no claim of smoother overall progression. Penultimate→final difference zero; no measured final-source replacement. Final twelve steps maximum 0.000165 due encoding. All 480 frames decoded. This is actual encoded-video evidence, not unit-test-only review or a claim of full human perceptual acceptance.

## Fidelity and performance

Final raw artwork versus original decoded JPEG: **MAE 0, zero changed pixels, 100% mask coverage**. H.264-decoded final MAE **2.620352/255**, small codec differences; native faces/glasses/hair/clothes/hands/feet/branches/flowers comparisons retained.

Intermediate display frames intentionally contain the small pen overlay, so they are not falsely certified as exclusively source/white pixels. Separately rendering underlying artwork without the indicator at all requested timestamps verifies every pixel is exact source or white. Final display and source artwork coincide after indicator removal. Preview reveals only source pixels through the original masks.

Extraction 1.7208 s; render/encode 21.2684 s; total 23.4885 s. Parent lifetime peak working set 92,028,928 bytes (~87.8 MiB), FFmpeg child excluded; not an OS-enforced memory quota. Point/path/canvas/frame/coverage/deadline guards remain in force.

## Verification and touched files

Focused tests: **136 passed in 81.79 s**, exit 0; new/extended pencil+visual+complexity subset: 25 passed in 3.06 s. Selection includes family/ocean PNG/JPEG, dense flowers in all three strategies, mask holes/tips, every connector within allowed mask, full final coverage, pen-up overlay/no transit ink/final disappearance, exact source-only preparatory reveal, V1 planner/raster and file API regressions. No whole-repository, Vision V3 or LightningAI acceptance claim.

```powershell
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_whiteboard_v2_pencil_pass.py backend/tests/unit/test_whiteboard_v2_visual_pass.py backend/tests/unit/test_whiteboard_v2_complexity.py backend/tests/unit/test_whiteboard_v2_visual_refinement.py backend/tests/unit/test_whiteboard_v2_engine.py backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py backend/tests/contract/test_story_video_file_api.py
```

Ruff passes on four touched source modules/three touched test modules. Mypy `--follow-imports=silent` passes on four source modules, not all backend. Direct Settings and pipeline default checks both False. `git diff --check` exits 0. Configured security scanner exits 0: REPOSITORY_SECURITY_VALID, 1,662 publishable files scanned with environment/credentials/private reference classes excluded; not a comprehensive security audit. Final HEAD remains baseline and index empty; existing worktree edits remain uncommitted.

Changed in this pass: V2 extractor, V2 stroke schema, V2 drawing schedule, V2 renderer; new `test_whiteboard_v2_pencil_pass.py`; parameterized additions to `test_whiteboard_v2_visual_pass.py` and `test_whiteboard_v2_complexity.py`; feature plan/approval/context/decisions/status/evidence index; this result and the Golden Story proposal. Other existing dirty edits are not attributed to this task. No V1, original input, mask, hand draft or previous media was changed.

## Private artifacts

Root: `D:/Codex/Sketch2Life/real_pencil_refinement_2026-10-09/`.

- [Candidate MP4](D:/Codex/Sketch2Life/real_pencil_refinement_2026-10-09/real-family-v2-static.mp4).
- [Seven fixed-time before/after comparisons](D:/Codex/Sketch2Life/real_pencil_refinement_2026-10-09/before-after-3-6-9-12-15-18-20.png).
- Individual `before-*.png`, `after-*.png`, source-only `after-raw-*.png`; final raw/decoded PNGs, codec difference maps and critical feature sheet.
- `pencil-speed-diagnostics.json`, `fixed-time-comparison.json`, `after-timeline-validation.json`, `video-quality-checks.json`, `benchmark-metrics.json`, immutable-source/mask-bound world/scene/stroke/schedule JSON and cutouts.
- Private drivers `run_benchmark.py`, `compare_video.py`, `review_video.py`, `analyze_after.py`, `measure_pencil.py`; before/after module snapshots and `artifact-sha256.json`. Reproduction needs same allowed source/masks and checkout virtualenv; use a new private output directory, never overwrite this evidence.

The accepted-order revision-15 baseline stays unchanged at `D:/Codex/Sketch2Life/real_visual_refinement_2026-10-09/real-family-v2-static.mp4`. Golden Story is a proposal only: [private review copy](D:/Codex/Sketch2Life/real_pencil_refinement_2026-10-09/SKETCH2LIFE_GOLDEN_STORY_VIDEO_PLAN.md); repository source is `features/FEAT-030-whiteboard-story-video/plan/SKETCH2LIFE_GOLDEN_STORY_VIDEO_PLAN.md`.

## Stop decision

Keep revision-15 improvements; **do not promote this candidate**. Current limitations are route redundancy, sub-frame detail density, guessed raster pen history, local hatch fronts and insufficient time for full source-color pencil reveal. Cursor visibility alone is not natural drawing. Stop parameter changes and await owner review. Golden Story cannot be claimed ready until visual/timing and motion/approval/occlusion prerequisites in the separate proposal are resolved.
