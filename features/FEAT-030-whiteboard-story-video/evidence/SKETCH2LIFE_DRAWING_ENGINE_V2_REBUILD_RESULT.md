# SKETCH2LIFE — DRAWING ENGINE V2 REBUILD RESULT

2026-10-10 · Revision27 · **FUNCTIONAL_PARTIAL / ENGINEERING_TARGET_FAIL / VISUAL_QA_NOT_PASSED / OWNER_REVIEW_PENDING**

## Outcome and stop decision

Implemented a versioned local semantic strategy, source/new asset representation, region brush candidate planner, LOD/time feasibility, eased actual-tip spatial renderer and persistent simulated-beat adapter. The batch exposed a serious regression: automatic region brushes fragment into hundreds of runs and cleanup dots. DO NOT replace the existing butterfly/house baseline or begin Golden Story55s.

Decision: **A — Semi-automatic semantic stroke authoring**, with reviewed structural/color-region path packs. Stop automatic raster/brush threshold iteration. AI-assisted generation (B) is not authorized or benchmarked; directed image reveal (C) would not by itself meet the natural drawing target.

This report is not a new approval package. No further algorithm round is proposed for this task.

## 1. Verified root causes before implementation

Read existing extractor, V2 draw schedule, feasibility/phase separation, actual-tip proof drivers and source world/registry; inspected decoded house/butterfly and previous schedule/motion evidence.

- House baseline:154paths/153lifts,15dot paths;62.865s drawing/64.25s video. OUTLINE74pixels + DETAIL149pixels =1.024% of21,779 source pixels. Neutral-dark RGB gate discards colored contours, so useful structure arrives in COLOR.
- Existing source extraction traces mask silhouette and local raster detail;32px tile clusters and fragmented graph walks are not a house/window/door drawing sequence.
- Coloring uses tile-local hatches. Connecting those within tiles does not create coherent semantic region trajectories.
- Prior butterfly authored21paths give11.399s smaller drawing/12.75s video, but regular contour spirals/short lifts remain mechanical. That is better than the new automatic brush pack.
- Old scheduling measures every path; it has no identity-preserving semantic LOD or explicit narration budget optimizer.
- Prior real-family early background/color was a separate unscheduled-preview bypass, already removed. Do not reinterpret that as source mask damage.
- Motion Proof showed actual posture changes but bad joints/matte/background patches. Character rig remains optional and unchanged; drawing planner cannot repair its assets.
- Final source fidelity and correct pen endpoint do not establish natural intermediate drawing.

Evidence reports: evidence/SKETCH2LIFE_BUTTERFLY_VIDEO_PROOF_RESULT.md, SKETCH2LIFE_HOUSE_DRAWING_PROOF_RESULT.md, SKETCH2LIFE_SCHEDULE_DEBUG_RESULT.md and SKETCH2LIFE_MILESTONE3B_MOTION_PROOF_RESULT.md. The schedule report was read in feature evidence; there is no corresponding D-root copy, and none was assumed.

## 2. Files and actual architecture

Four NEW files; no preexisting Python file changed:

1. backend/src/sketch2life/contracts/schemas/semantic_drawing_v2.py
   - Additive local dataclasses: SemanticStroke roles PRIMARY_CONTOUR / DISTINCTIVE_DETAIL / COLOR_REGION / OPTIONAL_TEXTURE; DrawingBudget; TextStoryBeat.
   - No migration of existing frozen ObjectStrokeV2/WorldModelV2 production schemas.
2. backend/src/sketch2life/infrastructure/media/semantic_drawing_engine_v2.py
   - Explicit SemanticStrokeStrategyV1 adapter reusing existing ObjectStrokeV2, native path-length/timing helpers and actual partial-path geometry.
   - Source/new assets use one SemanticAsset. Authored overrides optional; uncertain raster packs remain NEEDS_SEMANTIC_PATH_REVIEW; protected identity without reviewed paths gets NEEDS_IDENTITY_DETAIL_REVIEW.
   - Pixel-cell global contour tracing instead of tile-boundary structural graph. Median/palette color regions are CANDIDATES, not recognized roof/face/flower semantics.
   - Actual source contours are retained; no generic house/character templates.
   - Source-derived temporary grayscale/clamped ink layer has explicit provenance. This is NOT original neutral ink recovery and NOT source mutation. Final source RGB/alpha replaces ink spatially only where brush travels.
   - PCA-oriented curved region hatches, mask-evidenced joins and explicit cleanup strokes. This implementation FAILED to keep fragmentation under useful limits.
   - HIGH_DETAIL/BALANCED/FAST_STORY optimizer removes only optional paths. It never discards distinctive features or shrinks timing mechanically.
   - Smoothstep for pen-up/down and footprint uses one eased fraction. Down/up times lengthened1.5x to respect peak speed caps, not accelerated to pass.
   - Persistent local text-beat adapter; no production HTTP/Gate binding.
3. tools/benchmark_semantic_drawing_v2.py
   - One A/B/C/D private CPU harness; common adapter/renderer, encoder/decoder, path previews, final/coverage diagnostics.
   - House/garden selection belongs to benchmark, not renderer identity logic.
4. backend/tests/unit/test_semantic_drawing_engine_v2.py
   -23 parameterized tests of contour evidence, source immutability, exact final, region coverage/clip, budget infeasibility, essential-detail retention, true eased tip, UP behavior, identity-review and unapproved/unsupported beat rejection.

Feature docs updated: approvals/TASK_APPROVAL.md, plan/PLAN.md, CONTEXT.md, DECISIONS.md, status/STATUS.md, evidence/README.md and this evidence report. Existing dirty work remains preserved.

Flow:
source/new RGBA + provenance → candidate/optional authored semantic pack → source-bound color regions → essential-only LOD + budget feasibility → ordered eased pen/brush schedule → spatial source renderer → persistent simulated text beats → local MP4.

No second production pipeline was installed. This is a versioned experimental adapter in the V2 media layer, not yet dispatched by the existing production jobs. Existing V2 public API, old strategy and V1 defaults are intact. Automatic semantics and a successful natural-color strategy remain missing, so this is not completion of the requested product engine.

## 3. Batch execution and bounded correction

First batch stopped before any MP4 on JSON serialization of ObjectStrokeV2 inside dataclass export. One correction changed serialization to model_dump(mode=json); no drawing geometry/threshold/speed was tuned. The failed output directory was preserved.

Corrected batch:
D:/Codex/Sketch2Life/drawing_engine_v2_rebuild_2026-10-10_batch-correction/

There was ONE completed batch evaluation and no subsequent algorithm/refinement run. Tests and decoded handoff sheets do not constitute another drawing render. Budget guard stops media longer than300s; source dimensions≤512x512, paths≤4096, points≤200,000. Peak process memory was not measured; these are input guards, not a process memory quota or hard wall-clock deadline.

## 4. Timing and path count — actual regression

| Test | Target drawing budget | Before | New drawing estimate | New paths / lifts | Render |
| --- | --- | --- | ---: | ---: | --- |
| A smaller butterfly | 3–5s; evaluated5s | 11.399s,21/20 | 236.717s | 629/628 | Clean/debug encoded |
| B source house | 6–8s; evaluated8s | 62.865s,154/153 | 341.472s | 801/800 | RENDER_RESOURCE_LIMIT |
| C real garden cluster | 4–6s; evaluated6s | No same-crop baseline; do not compare whole garden | 354.939s | 878/877 | RENDER_RESOURCE_LIMIT |
| D persistent slice | Simulated8+6+5s | No prior completed comparable slice | 933.128s | Combined plans | RENDER_RESOURCE_LIMIT |

All A/B/C targets: **TIMING_INFEASIBLE**. These estimates are required duration under THIS failed candidate planner/pacing, not universal minimum achievable drawing times.

Phase estimates:
- A: outline3.467s/detail3.375s/color229.875s; pen-up78.500s;374dot paths.
- B: outline5.933s/detail44.879s/color290.659s; pen-up100.328s;324dots.
- C: outline3.133s/detail33.383s/color318.422s; pen-up109.672s;313dots.

A keeps7 primary +9 distinctive authored lines, but color explodes into613paths. B has1primary +27distinctive +773color paths. C has1primary +28distinctive +849color paths. No optional paths survive these packs, so BALANCED and FAST_STORY cannot help. FAST_STORY is therefore a safe essential-only fallback, NOT a demonstrated useful faster LOD.

## 5. Root cause of new failure

Median/palette regions are disconnected and contain irregular boundary/AA fragments. The PCA hatch sampler emits a new path on every mask interruption; the residual-coverage pass emits dot footprints for unreached pixels. Thin ink-only butterfly antenna/AA regions are especially costly. Minimum visible DOWN/UP frames plus eased-speed limits amplify hundreds of paths into minutes.

This is a design failure in automatic region brush/path compilation, not an encoder failure. Global contours remove the old neutral-only structural gate, but palette-component outlines can trace color blotches and JPEG artifacts rather than meaningful object details. They require author review. The supplied source artwork was not simplified or replaced to hide that problem.

Correct phase ordering and faithful source compositing remain valid. Neither cures poor path semantics/brush continuity. Further generic thresholds or larger brushes would not demonstrate correct semantics or natural coloring.

## 6. Artifacts and what actually rendered

[New butterfly clean MP4](D:/Codex/Sketch2Life/drawing_engine_v2_rebuild_2026-10-10_batch-correction/A-butterfly/clean.mp4)
[New butterfly pen-debug MP4](D:/Codex/Sketch2Life/drawing_engine_v2_rebuild_2026-10-10_batch-correction/A-butterfly/pen-debug.mp4)
[Decoded butterfly contact](D:/Codex/Sketch2Life/drawing_engine_v2_rebuild_2026-10-10_batch-correction/A-butterfly/contact-sheet.png)
[Butterfly before/after decoded comparison](D:/Codex/Sketch2Life/drawing_engine_v2_rebuild_2026-10-10_batch-correction/butterfly-before-after-normalized.png)
[House before/after PATHS ONLY, not a new video](D:/Codex/Sketch2Life/drawing_engine_v2_rebuild_2026-10-10_batch-correction/house-before-after-paths-only.png)
[Batch report](D:/Codex/Sketch2Life/drawing_engine_v2_rebuild_2026-10-10_batch-correction/batch-report.json)
[Semantic diagnostics](D:/Codex/Sketch2Life/drawing_engine_v2_rebuild_2026-10-10_batch-correction/semantic-diagnostics.json)

Other files:
- A/B/C-plan.json: roles/region IDs, actual paths, LOD alternatives, pen travel/start/end, target/feasibility, StyleProfile/provenance.
- A/B/C-paths.png: static contour previews only.
- A-butterfly/final-native.png, source-target.png, final-decoded.png, frame-execution.json, render-report.json.
- D-simulated-beats.json:3 simulated demo cues, persistent state schedule and focus, NOT audio timestamps or server approval.
- final-handoff-sha256.json: local evidence hashes.

No B-house/C-garden/D-slice MP4 exists. Their output directories contain no successful video. No contact/final/motion acceptance is claimed for those blocked tests. There is no new before/after house MP4 or camera-continuity proof.

A playback237.750s/24FPS/5706frames per MP4; actual WALL_CLOCK_RENDER_TIME67.505s. Rendering was CPU-only. Do NOT confuse video playback length with time spent encoding.

Comparison sheet uses normalized progress timestamps, clearly labeled old11.399s versus new236.717s. It is NOT a same-duration quality comparison or secretly accelerated MP4. New A video is native art magnified for inspection; pacing scale0.22 is recorded. It is not an exported tiny56x40 garden compositing demo. Existing smaller butterfly proof is preserved and remains better.

## 7. Technical and visual quality gates

A single-object diagnostic:
- TECHNICAL_PASS for per-object final native RGBA exact, decoded5706frames in each file, no early COLOR, no consecutive UP color growth.
- Max new color pixels/frame200; source region masks clip reveal; no fade/full-region reveal/final snap.
- All temporary ink is overwritten progressively by literal source-color footprints; final native byte equality proves completion, not temporal beauty.
- Native texture/color exact at final. MP4 is H.264/yuv420p lossy; encoded final is not byte-identical.
- Pen and brush share same eased path fraction; unit geometry tests verify this, but batch does not compute an independent human perceptual error metric.
- VisualQA NOT_PASSED: very long coloring, repeated stops/dots, large white gaps remain late; human real-time playback approval not obtained.
- The new A degraded strongly compared to authored21path baseline. Do not promote it.

B/C/D:
- Timing: TIMING_INFEASIBLE.
- Technical MP4 status: NOT_RUN_RESOURCE_LIMIT, NOT_PASS.
- VisualQA: NOT_EVALUATED_IN_VIDEO / NOT_PASSED.
- Camera easing and persistent board code implemented but D media was blocked. Camera continuity, multi-object temporal popping and integrated pen synchronization remain unverified.
- No end-to-end PASS. Batch summary PARTIAL_NOT_END_TO_END_PASS is functional bookkeeping; ENGINEERING TARGET FAIL is the product conclusion.

## 8. Story/approval and generalized support limits

- Same SemanticAsset contract supports source/generated artwork; renderer has no house/butterfly identity templates.
- Per-source StyleProfile stores source hash, actual pixel hash, region inference method and source-derived temporary-ink provenance.
- Palette/contour inference is NOT automatic semantic segmentation. No roof/wall/door semantic model is implemented; no JPEG original stroke order claim.
- Manual paths/region overrides are optional review inputs, not universal fixture requirements.
- Protected character identities are flagged NEEDS_IDENTITY_DETAIL_REVIEW. There is no demonstrated automatic eyes/hair/glasses feature classifier; safe review is required.
- Local text beats have explicit local_demo_approved flag. This is NOT server authorization, immutable approval-session binding or Gate A/B.
- No audio measurement, narration cue extraction, TTS or speech synchronization. All cues are simulated and stretched to actual feasibility time; they cannot be used as production audio alignment.
- Scene state retains previous objects; partial erase/page/character walk explicitly UNSUPPORTED_ACTION.
- The test text supplies only existing local-demo concepts (house, flowers, butterfly), not new artwork/story facts. Butterfly artwork is still technical-proof-only.
- No durable storage, new-upload mask processing or production endpoint integration was added.

## 9. Actual tests and checks

```text
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_semantic_drawing_engine_v2.py backend/tests/unit/test_house_video_proof.py backend/tests/unit/test_butterfly_video_proof.py backend/tests/unit/test_butterfly_candidate_refinement.py backend/tests/unit/test_whiteboard_slice_feasibility.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py
108 passed in25.43s

backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_whiteboard_v2_complexity.py backend/tests/unit/test_whiteboard_v2_schedule_debug.py
20 passed in2.87s

backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py
32 passed in1.30s
```

160 distinct selected cases passed;23 new semantic cases. Existing multi-drawing tests include synthetic family/ocean PNG/JPEG. This is NOT160 new realistic drawings or a full-repository pass.

Ruff checks four new files:PASS.
MYPYPATH=backend/src Mypy --follow-imports=silent on new contract/engine/harness:PASS,3files.
imageio_ffmpeg has an explicit import-untyped exemption because upstream supplies no stubs.
git diff --check:PASS.
Repository security validation:PASS (final post-documentation count in handoff verification).

Full repository, Vision V3 missing-fixture suites, LightningAI, real upload, motion/rig regression, audio, production approval and full-story E2E were not run. No repository-wide or visual acceptance claim.

## 10. Safety and reproduction

HEAD93668ffdaa7f2890fe9498596c670006a87eba4a; branch codex/feat-018-contract-plan; index empty.
336preexisting Python files combined path/content digest unchanged. All old dirty files and old renders preserved; no reset/stage/commit/push/deploy.
Original family JPEG and9master mask hashes validated before/after completed batch; source/new candidate original pixels unmodified. No private media placed in Git.
V1 default; story_render_v2_enabled remains False. No HTTP/Gate/API migration.

```text
backend/.venv/Scripts/python.exe -m tools.benchmark_semantic_drawing_v2 --output-dir <new-private-output-directory> --confirm-local-rebuild-batch
```

Paths to approved local fixtures are benchmark inputs only. Do not rerun as a refinement loop or activate strategy in production.

## 11. Golden Story readiness and technical decision

**NOT READY for Golden Story55s.** New timing/brush planner regressed; B/C/D video proof is absent. Source fidelity, unit tests and versioned contracts cannot substitute for natural drawing and feasible narration timing.

Choose **A: semi-automatic semantic stroke authoring**. Retain existing21path butterfly baseline; prepare source-grounded structural strokes and semantic region brush packs through a local author/review workflow, with this budget evaluator rejecting impossible packs before long render. A human must label meaningful regions/identity details where automatic inference is uncertain. Do not pretend palette clusters are semantics.

B requires separate permission and model/path-quality evaluation; it is not a proven solution. C can provide directed narrative reveal while retaining source texture, but without reviewed paths it should not be branded natural whiteboard drawing. No additional implementation is authorized or performed in this report.

Stop and review. No further automatic raster threshold/brush tuning in this task.

