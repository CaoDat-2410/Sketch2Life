# Semantic Drawing Authoring — Result (Revision 28)
Date: 2026-10-10. Scope: two local offline proofs only.

## Verdict

FUNCTIONAL_PARTIAL. TECHNICAL_PASS for both encoded proofs; TIMING_INFEASIBLE for both requested targets; VISUAL_QA_NOT_PASSED; OWNER_APPROVAL_PENDING. This is not a production approval, a Gate A/B verification, or readiness for the 55-second story.

The micro-path failure is substantially reduced through explicit semantic authoring. Short, natural drawing is **not solved**. Stop here for owner playback/review; no further automatic refinement.

## Baseline protection

Repository: ${LOCAL_REPOSITORY_ROOT} (actual checkout recorded in external stabilization manifest).
HEAD: 93668ffdaa7f2890fe9498596c670006a87eba4a.
Branch: codex/feat-018-contract-plan. Index empty before and after.
Before snapshot: D:/Codex/Sketch2Life/semantic_authoring_git_before_2026-10-10.json.
All 340 pre-existing backend/tools Python files retain their aggregate path/byte digest:
0bf18a182b4b935af452be82c6519165343e29e31efc860ca29ebf6992adc3c5.
Old renderer, prior dirty changes, rig experiments, and proof artifacts were not changed/deleted.
Settings.story_render_v2_enabled remains False; existing V1 wiring untouched. No new HTTP endpoint or production Gate A/B changes.
Original source: ${PRIVATE_SOURCE_DIR}/familly.jpg (family1.jpg is the benchmark alias), 594x336.
Source SHA-256: 52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3.
Original manifest SHA-256: 693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14.
All nine master mask hashes checked: 9 objects, 0 mismatches.
All new media/source copies/authoring data remain outside Git. No network/TTS/GPU/paid inference, commit, push, merge or deploy.

## Implemented modules and file changes

New code:
1. backend/src/sketch2life/contracts/schemas/semantic_authoring_v1.py — strict frozen Pydantic JSON contract, version 1.0; source hashes, provenance, explicit stroke order, semantic masks, primary/detail/color roles, authored brush widths and minimum timing. Rejects duplicate references, invalid phases, omission of essential paths, phase regression and excessive point budgets.
2. backend/src/sketch2life/infrastructure/media/semantic_authoring_v1.py — local hash-bound loader/compiler, bounds/mask/union checks, spatial brush coverage validation, missing-region previews and NEEDS_AUTHORING_REVIEW, explicit schedule, AUTO/REVIEW/FALLBACK routing policy. Reuses existing SemanticProgress renderer; no house/butterfly identity in renderer.
3. tools/semantic_drawing_author.py — reusable validate/preview/render CLI. Generates schema, phase previews, timeline, clean/debug MP4, frame traces, contacts, final/native/decoded comparisons and SHA-256 artifact manifest. Requires explicit technical-proof confirmation and a new private output directory.
4. backend/tests/unit/test_semantic_authoring_v1.py — 17 contract/compiler/routing/source-fidelity/pen-up/coverage tests.

Governance updates (append/preserve previous records):
5. features/FEAT-030-whiteboard-story-video/approvals/TASK_APPROVAL.md.
6. features/FEAT-030-whiteboard-story-video/plan/PLAN.md.
7. features/FEAT-030-whiteboard-story-video/CONTEXT.md.
8. features/FEAT-030-whiteboard-story-video/DECISIONS.md.
9. features/FEAT-030-whiteboard-story-video/status/STATUS.md.
10. features/FEAT-030-whiteboard-story-video/evidence/README.md.
11. features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_SEMANTIC_AUTHORING_RESULT.md (this report).
Private report copy: D:/Codex/Sketch2Life/SKETCH2LIFE_SEMANTIC_AUTHORING_RESULT.md.

No interactive GUI/SVG importer was implemented. Editing is JSON coordinates/widths/order/minimum durations plus local raster region masks; CLI previews allow review. Authoring overrides are optional, not wired as an upload requirement.

## Authoring examples and operation

Data root: D:/Codex/Sketch2Life/semantic_authoring_2026-10-10_final/.

- butterfly/authoring.json, asset.png, region-*.png: retained authored candidate paths plus explicit source-ink retouch region. Six semantic regions; 7 outline, 9 detail, 21 color.
- house/authoring-controlled.json, asset.png, region-*.png: actual source crop; seven windows, door, roofs, trim and walls in thirteen regions. Manual source-guided contours/details and one continuous curved sweep per color region. 7 outline, 22 detail, 13 color.
- house/authoring.json is the earlier helper-generated 216-path/132.069-second pack. Preserved for audit, NOT the final rendered pack.
- Private preparation scripts: D:/Codex/Sketch2Life/prepare_semantic_authoring_examples_2026-10-10.py and author_house_sweeps_2026-10-10.py. Asset-specific coordinates live in these example data preparations, not generic renderer.
- asset.png and semantic masks must remain beside their original authoring JSON for relative-path replay. Proof-directory snapshots are audit snapshots, not self-contained replay bundles.

Validation checks every semantic region's final brush footprint, clipped to that region, before rendering. Missing coverage produces magenta error previews, not synthetic dot cleanup. An initial butterfly pack failed with 101 uncovered fringe pixels, the next with 96. Those failed preparations remain in the earlier private directories. Final localized retouch brush width was corrected from 8 to 12 native pixels (the existing candidate's color width); paths still follow explicit ink lines and are clipped to ink-retouch. This is an authored support-footprint correction, not a global threshold/FPS/speed change, and did not make timing PASS.

Temporary outline/detail ink is declared TEMPORARY_SOURCE_DERIVED_INK. It is not recovered original pencil stroke history. COLOR restores original approved asset RGBA only under the traveling brush. No opacity fade, region pop, rectangle wipe or final snap is used. All thirteen house regions cover exactly the original 21,779 active crop pixels as a disjoint partition. Butterfly regions intentionally overlap at joins; region pixel totals must not be summed as unique coverage.

Rendering keeps previous pacing caps (ink 180, color 300, pen-up 600 presentation pixels/second), 24 FPS, and existing easing compensation. Small butterfly scale 0.22 is retained; inspection view enlarges it, with a native-size inset. No target-driven FPS reduction or speed increase.

## Measured results

| Asset | Rejected automatic rebuild | New authored proof | Earlier original proof |
|---|---|---|---|
| Butterfly | 629 paths / 236.72s drawing | 37 paths, 36 lifts / 23.2586s drawing | 21 paths / 11.3990s drawing |
| House | 801 paths / 341.47s drawing | 42 paths, 41 lifts / 106.7572s drawing | 154 paths / 62.8653s drawing |

Path reduction does not equal timing/visual success. Both new proofs are slower than the earlier original proofs, although much faster than the rejected rebuild. Do not claim universal before/after improvement.

| Metric | Butterfly | House |
|---|---:|---:|
| Outline/detail/color paths | 7 / 9 / 21 | 7 / 22 / 13 |
| Outline/detail/color time, including pen-up | 3.467 / 3.375 / 16.416s | 12.876 / 13.958 / 79.923s |
| Requested maximum | 5s | 8s |
| Actual drawing | 23.259s | 106.757s |
| MP4 duration, with end hold | 24.292s | 107.792s |
| Frames per clean/debug MP4 | 583 / 583 | 2587 / 2587 |
| Wall-clock render/encode/decode audit | 8.916s | 40.223s |
| Native final RGBA exact | true | true |
| Decoded RGB MAE, 0–255 presentation scale | 0.288 | 0.830 |
| Early-color frames | 0 | 0 |
| Consecutive pen-up color changes | 0 | 0 |
| Debug tip vs computed path endpoint error | 0 | 0 |
| Maximum new native color pixels/frame | 281 | 65 |

Every semantic region has zero missing source pixels. No zero-length COLOR cleanup paths are accepted. Peak memory was not instrumented; compiler budgets are 512x512 active canvas area, 4096 paths, 200,000 points; proof rendering guard 180s; frames streamed to FFmpeg.

The endpoint check shares renderer path geometry, so is not an independent optical verification. Early-color audit detects color before COLOR phase; it does not certify artist-correct assignment of every window edge to a manually annotated region.

## Artifact handoff

Each of butterfly-proof/ and house-proof/ under the data root contains:
- clean.mp4; pen-debug.mp4.
- contact-sheet-0-25-50-75-100.png (percentages of drawing duration).
- final-native.png; source-target.png; final-decoded.png; decoded-difference-x8.png.
- path-contact-sheet.png; outline/detail/color-path-preview.png.
- path-timing.json; frame-execution.json; result.json; artifact-sha256.json; authoring-schema.json.

Comparisons:
- comparisons/butterfly-before-after-normalized.png.
- comparisons/house-before-after-normalized.png.
These use frames decoded from old/new MP4s at normalized drawing progress, NOT equal wall-clock time; each timestamp is printed. Old MP4s remain at butterfly_video_proof_2026-10-09/ and house_video_proof_2026-10-10/ under D:/Codex/Sketch2Life.

Reproduce, from repository root with configured backend source imports:
```powershell
backend/.venv/Scripts/python.exe -m tools.semantic_drawing_author --pack D:/Codex/Sketch2Life/semantic_authoring_2026-10-10_final/butterfly/authoring.json --output-dir D:/Codex/Sketch2Life/semantic-butterfly-replay-NEW --render --confirm-local-technical-proof
backend/.venv/Scripts/python.exe -m tools.semantic_drawing_author --pack D:/Codex/Sketch2Life/semantic_authoring_2026-10-10_final/house/authoring-controlled.json --output-dir D:/Codex/Sketch2Life/semantic-house-replay-NEW --render --confirm-local-technical-proof
```
Use unused output paths; existing outputs are rejected.

## Visual findings and unresolved limits

Decoded video comparison shows house structural form now appears before pigment, unlike the earlier scattered neutral-pixel extraction. Butterfly retains source colors/texture. Final native fidelity is exact, not evidence of natural drawing.
House contours/windows are manually approximated guides and look comparatively straight/constructed; they are temporary derived ink, not substitute artwork. COLOR paths remain repetitive sweeps; curves/direction changes do not by themselves remove a scanner-like feel. Some sweeps traverse holes/outside their allowed region; compositing clips pixels correctly but the pen can travel without visible progress. Butterfly extra ink retouch causes lengthy finishing passes. Lanczos enlargement/MP4 compression soften small texture.
I inspected decoded MP4 frames/contact comparisons and execution traces, not an owner-approved full-speed playback. No claim that these videos are beautiful or accepted.

Current authored full-coverage representation needs approximately 23.26/106.76 seconds under its retained pacing. These are measured timings of these packs, not proven global minima. 3–5/6–8 seconds is not feasible for these authored trajectories. Eliminating fragmentation alone cannot shorten long full-coverage pencil sweeps sufficiently.
A genuinely different, artist-approved drawable abstraction/variable brush representation or directed path planning would be needed to pursue short natural output. That may trade temporary-phase appearance against source fidelity and needs explicit review. AI-assisted planning is unproven here, not an implemented fix or authorization for paid inference. Do not keep tuning thresholds or automatically start another loop.

## Generalization

AUTO: generic routing contract supports externally quality-validated automatic candidates; no new automatic semantic inference/confidence engine implemented.
REVIEW: candidate regions/paths can be edited, hash-bound and previewed; low coverage blocks.
FALLBACK: explicitly approved local authored pack, disclosed as such, never silent V1.
Current manual region/path preparation is specific to these two proofs. New uploads are not guaranteed to generate beautiful paths automatically. Approval strings are local metadata, not server authentication.

## Tests and checks

Actual command (repository root):
```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_semantic_authoring_v1.py backend/tests/unit/test_semantic_drawing_engine_v2.py backend/tests/unit/test_whiteboard_slice_feasibility.py backend/tests/unit/test_whiteboard_v2_engine.py backend/tests/unit/test_whiteboard_v2_complexity.py backend/tests/unit/test_whiteboard_v2_schedule_debug.py backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_pipeline_factory.py backend/tests/unit/test_whiteboard_renderer_adapter.py backend/tests/unit/test_lightning_whiteboard_provider_parser.py -q -o addopts=''
```
Result: **175 passed in 42.86s**, no failures/skips in this selected run. New authoring tests separately:17 passed.
Ruff check: PASS for the four new Python files.
Mypy --follow-imports=silent: PASS, three source/tool files.
git diff --check: PASS; staged diff empty.
Security review: scoped text search found no new HTTP/requests/httpx/credentials/eval/exec calls; refs forbid remote URLs, file hashes checked, region IDs do not become output paths. This is a limited manual/static check, not a full vulnerability audit.
Bandit attempt failed: environment has no bandit module. **Bandit NOT RUN**, not PASS. No package installation performed.

No full-repository pytest, Vision V3 fixture suites, GPU/Lightning runtime, external audio, Golden Story or universal-upload acceptance run. Prior Vision V3 missing-fixture failures were not fixed or re-tested. V1 regression evidence is limited to selected renderer/factory/adapter/provider-parser tests plus unchanged baseline code; not a repository-wide PASS.

## Stop condition

Technical reusable authoring and two real encoded proofs delivered.
TIMING_INFEASIBLE and VISUAL_QA_NOT_PASSED remain. Owner must watch clean/debug videos before any visual approval. No further renderer changes or story integration authorized by this result.
