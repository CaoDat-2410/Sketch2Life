# Real family — schedule diagnosis and debug, revision 17

2026-10-09. **SCHEDULE BUG FIXED / OVERALL PARTIAL / VISUAL_QA_NOT_PASSED.** Early out-of-turn background marks were caused by the previous renderer's preview bypass, not by the main object-first schedule mixing phases. One bounded fix produced clean/debug MP4s and an actual side-by-side comparison. No extraction-threshold tuning or new source art. Stop for owner review; naturalness remains insufficient.

## Exact inputs and baseline

Same original `familly.jpg` (previously resolved `family1.jpg` alias), JPEG 594×336; SHA-256 `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`. Original nine-mask manifest SHA-256 `693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14`; each original mask verified unchanged. No character/vector replacement, diffusion, recoloring, geometry redraw, identity change or new paid call. This remains provisionally permitted static benchmarking, not Gate A/B/product acceptance.

Branch `codex/feat-018-contract-plan`, HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`, index empty before work. Dirty V2/V1/test/doc/hand/pilot files preserved. Renderer/schedule before snapshots saved privately; no reset/stage/commit/push/deploy. Actual before-video is revision-16 original artifact SHA-256 `545549a9a5e93b4b7ed786a781d13b97edb5b91585ef9c40ca498bfef9383b2d`, referred to by owner as downloaded `(2)`. The downloaded alias itself is not used as an unverified input.

## 1. Why color appeared at 0.5 seconds

Revision 16 intentionally added `background_preview_ids=ids[-3:]` to the private driver (sky/path/remaining-background). `_seed_paths` selected at most sixteen short prefixes per region from COLOR paths. `_frame` drew these during an extra 0.6-second preparation window, directly into object reveal masks, **without any corresponding ScheduledStrokeV2 event**. Main object drawing was delayed by 0.6 seconds.

Thus color was visible across distant background regions while the main object schedule had not begun. This was an implementation/design error in the attempted preview improvement, not evidence of randomized model output or invalid masks. The early global marks are observable in the actual previous 0.5-second frame.

Removed the seed rendering branch and extra preview clock. A nonempty `background_preview_ids` now fails explicitly with `UNSCHEDULED_STROKE` rather than being silently ignored. The private driver no longer requests preview. Previously accepted object-first order remains; extraction, path geometry, brush widths and timing weights are not retuned.

## 2. Does the main schedule mix phases?

The actual schedule has **2,414 paths**, nine sequential object runs: mother → father → child → house → tree → garden → sky → path → remaining-background. Within each object it completes OUTLINE, then DETAIL, then COLOR. It has no intentional object interleave. The bypass was outside this schedule, so inspecting schedule JSON alone could not detect previous early color.

Another visual distinction matters: OUTLINE/DETAIL reveal original RGB under their brush, not universally black ink. A colored source outline or tiny colored facial/clothing feature may therefore appear during a legitimate outline/detail stroke. Phase labels describe path purpose, not a promise that all color-channel pixels remain white until COLOR. Forcing all such pixels black would require a different intermediate-art contract; this task did not repaint the source.

## 3. Ordering and deliberate interleave enforcement

Added `validate_draw_schedule` before offline encoding:

- every source stroke exactly once; correct object/path/phase binding;
- serial chronological strokes, no overlap, inside draw/hold budget;
- all parent-phase paths for an object completed before a child phase starts;
- no return to an earlier phase for that object;
- debug acceptance requires a nonempty explicit `interleave_reason` when an object appears in multiple timeline runs. A reason cannot override broken phase dependencies.

Deliberate interleave can pause A after its outline, draw B's outline, then resume A's detail/color; it cannot start A's color before its required outline/detail finish. Existing documented phase-first caller mode remains compatible, but debug acceptance needs its purpose supplied. This reason is diagnostic intent, not server approval or a substitute for Gate A/B. The new real clip uses no interleave.

Strict debug mode rejects non-white unscheduled base background with `UNSCHEDULED_STROKE`; such a source needs an explicit scheduled source asset. The real nine masks fully partition the image, producing a white cleared background, so it qualifies. Generic non-debug V2 background behavior is not rearchitected; no production scheduler/HTTP authorization claim is made.

## 4. Actual-path debug and sync evidence

Clean and debug outputs use the same source/masks/paths/schedule/duration/FPS. They differ only in debug overlays. Debug shows actual tip, DOWN/UP, object ID suffix, phase and stroke ID. Both source reveal and pen tip use `_stroke_fraction` and the same elapsed schedule time; tip is placed at the same partial polyline endpoint. World placement uses the same rounded source-layer origin as compositing. During UP the tip interpolates between previous endpoint and next start, without source ink. Tip/banner disappear for final hold.

Independent audit reconstructed the debug raw frames with identical settings (no extra encoded render), decoded **all 480 actual debug frames**, and independently recalculated arc-length endpoints from stored path/time data:

- maximum endpoint error **2.3988e-11 pixels**;
- timeline samples: 363 DOWN / 88 UP / 29 final-hold frames;
- reconstructed-debug versus actual H.264 mean MAE 1.516365, maximum 2.702301 (codec difference, not geometric error);
- raw clean at 0.5 seconds: **all eight objects not yet scheduled are entirely white within their masks**; only mother is drawn;
- clean raw checkpoints contain source pixels or white only; debug intentionally includes indicator/banner pixels until hold.

`frame-cursor-trace.json` records per-frame elapsed/schedule time, tip, object/stroke/phase. `debug-audit.json` stores results. This certifies sampled geometry/clock consistency, **not that all sub-frame stroke history is visually observable**. Many short paths complete between two displayed frames; a single visible tip at the sample cannot accompany every newly visible pixel from all those completed paths. Debug makes that raster/time-compression limit explicit.

## 5. Same-source, same-time actual comparison

Before, after-clean and after-debug are each **20 seconds, 24 FPS, 480 frames, 594×336**. Encoded comparison video places original decoded before/after frames side by side (1188×360 with 24-pixel labels). Contact sheet includes 0.5/3/6/9/12/15/18/final seconds. Samples use identical indices `min(479, round(t*24))`; final is frame 479 at about 19.958 seconds, not a nonexistent frame at t=20.

| Time | Before source MAE | After-clean source MAE | Observation |
| --- | ---: | ---: | --- |
| 0.5 s | 53.3024 | 52.9136 | Random-looking global background prefixes removed; mother outline/detail only. |
| 3 s | 45.6674 | 43.9685 | Starts objects without preview delay; same order. |
| 6 s | 37.8610 | 36.0438 | Family complete; house coloring. |
| 9 s | 26.6577 | 26.8150 | Not universally better progression; garden in progress. |
| 12 s | 19.2299 | 19.3788 | Patch-like sky/color completion remains. |
| 15 s | 13.8511 | 13.9091 | Large background blanks still remain. |
| 18 s | 5.6758 | 5.4332 | Remaining-background partly colored; still unfinished patches. |
| Final | 2.6204 | 2.6185 | Same final source composition, small H.264 differences. |

MAE measures completion/codec differences, not artistic naturalness. Removing early irrelevant marks is visibly correct in inspected decoded frames, but does not deliver a clearly natural whiteboard animation. The path-only extractor, detail fragments and local hatch regions remain unchanged. No threshold loop was pursued.

### Acceptance status

| Criterion | Result |
| --- | --- |
| No source marks outside their schedule turn | PASS for this exact clean benchmark and strict debug route; preview removed/rejected. |
| Tip follows active stroke | Sampled geometric/clock PASS; sub-frame visibility remains a blocker. |
| Continuous, natural main lines | PARTIAL: paths are source-connected, but too fragmented/fast perceptually. |
| No abrupt color-region appearance | NOT ACCEPTED: no region-swap/fade primitive, yet multiple hatches completing between frames still look patch-like. |
| Final artwork preserves source | PASS raw, both clean/debug; encoded stream lossy. |
| Clear overall direct-video quality improvement | NOT ESTABLISHED; VISUAL_QA_NOT_PASSED. |

## Fidelity, performance and architecture limit

Both raw final frames equal original decoded JPEG: **MAE 0, changed pixels 0, mask coverage 100%**. Clean decoded final MAE **2.618535/255**; debug decoded final **2.619787/255**. Penultimate→final clean difference zero, last twelve steps zero; no final source snap. Mask/identity hashes unchanged.

Extraction 1.7483 s; clean encode/render 20.3831 s; debug encode/render 20.2344 s; whole driver 42.8383 s. Parent lifetime peak working set 93,831,168 bytes (~89.5 MiB), excludes FFmpeg child. Existing canvas/path/frame/deadline guards retained.

Raster source reconstruction infers topology from pixels; it cannot recover original human pen order, pressure or gestures. Selecting edges/texture is heuristic. Full source-color coverage yields long redundant traversal while a 20-second/24-FPS clip samples only 480 states. Correct schedule and cursor fix causal ordering, not the travel budget or semantic pen behavior. Resolving that requires a reviewed semantic/source-grounded path representation and a feasible visible-time budget/style decision, not indefinite edge thresholds. No such architecture is implemented here, and the previous Golden proposal remains unimplemented.

## Tests, scope and changed files

Final focused suite: **144 passed in 82.86 s**, exit 0. Schedule-debug plus pencil tests: 11 passed in 2.00 s. Added checks: object-first phase completeness, explicit purposeful interleave, missing/wrong-phase/overlap/color-first rejection, shared progress endpoint, untouched not-yet-scheduled masks. Obsolete preview-success test now verifies explicit rejection and unchanged final target. Family/ocean PNG/JPEG, dense source/texture/coverage, existing V2 world/engine and V1 raster/planner/file API regression remain in selection.

```powershell
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_whiteboard_v2_schedule_debug.py backend/tests/unit/test_whiteboard_v2_pencil_pass.py backend/tests/unit/test_whiteboard_v2_visual_pass.py backend/tests/unit/test_whiteboard_v2_complexity.py backend/tests/unit/test_whiteboard_v2_visual_refinement.py backend/tests/unit/test_whiteboard_v2_engine.py backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py backend/tests/contract/test_story_video_file_api.py
```

Ruff passes two touched source/two test files. Mypy `--follow-imports=silent` passes two source files. Not whole-repository typing/tests; Vision V3 and LightningAI not run. V1 remains default; no V2 HTTP/Gate changes or automatic visual-approval promotion.

`git diff --check` exits 0. Configured repository security scan exits 0: REPOSITORY_SECURITY_VALID, 1,664 publishable files scanned, protected environment/credentials/private reference classes excluded. Both Settings and pipeline constructor V2 defaults verified False. Final HEAD remains the baseline SHA, index empty; all work remains uncommitted. This scoped scanner/test selection is not a comprehensive whole-product security or regression audit.

Changed in this task: `application/services/story_draw_schedule_v2.py` validation; `infrastructure/media/whiteboard_renderer_v2.py` preview rejection/removal, shared progress, debug/audit hooks and placement; new `tests/unit/test_whiteboard_v2_schedule_debug.py`; modified owned `tests/unit/test_whiteboard_v2_pencil_pass.py`; FEAT-030 plan/approval/context/decisions/status/evidence index and this report. Extractor/schema and three preexisting V1 source/test edits were not modified in this task.

## Private artifacts and reproduction

Root: `D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/`.

- [Clean candidate MP4](D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/real-family-v2-static.mp4).
- [Actual-path debug MP4](D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/real-family-v2-debug.mp4).
- [Side-by-side before/after MP4](D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/before-after-comparison.mp4).
- [Eight-time decoded comparison sheet](D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/before-after-0.5-3-6-9-12-15-18-20.png).
- Actual clean/debug decoded frames, source/raw/decoded final/difference PNGs and critical feature sheet; `debug-audit.json`, `frame-cursor-trace.json`, `fixed-time-comparison.json`, `video-quality-checks.json`, `after-timeline-validation.json`, `benchmark-metrics.json`.
- Same-source world/scene/stroke/schedule/permission JSON and source cutouts; before/after renderer/schedule snapshots, private drivers and final `artifact-sha256.json`.

Reproduce with checkout virtualenv and same allowed source/masks: private `run_benchmark.py`, `compare_video.py`, `review_video.py`, `analyze_after.py`, `audit_debug.py`, `make_comparison.py`. Use a new output directory, not overwrite these evidence outputs. All real derivatives stay outside Git; both prior videos remain intact.

## Stop

The schedule bypass is resolved and debug evidence is available. Overall natural whiteboard quality remains unpassed. Do not promote this candidate to production, enable V2 or start story motion/audio/transitions. Stop and request owner video review rather than further threshold tuning.
