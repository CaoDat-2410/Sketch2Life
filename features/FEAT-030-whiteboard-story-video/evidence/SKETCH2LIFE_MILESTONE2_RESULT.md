# Sketch2Life Milestone 2 — offline source-preserving drawing pilot

Date: 2026-10-09. Branch `codex/feat-018-contract-plan`, HEAD before edits `c80ef1f6b6d7d33da54eb26a9ad036283aa381fb`. The worktree was already dirty with M1/M1.5 files and unrelated user edits to V1 stroke extraction/two V1 tests and `assets/`; those user edits were not overwritten. Read the M1 and M1.5 reports, the full audit at `D:/Codex/Sketch2Life/SKETCH2LIFE_FULL_WHITEBOARD_AUDIT.md`, AGENTS rules, current V2 registry/composer and V1 tracer/renderer before work. Revision-10 FEAT-030 plan and approval were recorded before code edits.

## Outcome and acceptance labels

- **ENGINE_TEST_PASS** — local CPU engine produces per-object source-bound stroke manifests, outline/detail/color schedule, three synthetic pilot MP4s and exact uncompressed final frames relative to the canonical V2 Scene Composer. PNG/JPEG A/B mechanics tested; no diffusion, GPU or paid call.
- **VISUAL_QA_NOT_PASSED** — I inspected A/B 0–100% contact sheets. They are still schematic/stiff; the family fixture itself consists largely of colored rectangles, color is revealed in visibly regular horizontal sweeps, and the ocean detail tracer yields many short paths. This is not the attractive, hand-drawn reference aesthetic. It needs real permitted drawings, better path/brush modeling and human acceptance.
- **SOURCE_IMAGE_FIDELITY_PARTIAL** — final pilot frame exactly matches the *canonical composer target* (0 changed pixels, MAE 0 before H.264). Family scene 1 also matches original input (MAE 0). Ocean original-vs-canonical MAE is 9.154 for PNG and 9.476 for JPEG because the M1 composer uses a white background and omits source water/background pixels not inside reviewed object masks. Do **not** claim entire source image preserved for those cases.
- **LIGHTNINGAI_NOT_TESTED**. **FULL_STORY_VIDEO_NOT_IMPLEMENTED**. These are six-second silent, single-scene offline drawing pilots; no story motion, TTS/audio alignment, scene transition, user endpoint or production integration.

Overall **PARTIAL / not accepted for product-quality whiteboard video**. Stop here for Architect review; no Milestone 3, commit, push or deploy.

## Architecture and implementation

`SourceAssetRegistry` (manual reviewed masks/cutout SHA-256) → `LocalObjectAwareStrokeEngine` implementing `ObjectAwareStrokePort` → `SourceObjectStrokesV2` → `build_draw_schedule` / `SceneDrawScheduleV2` → `render_scene_pilot` / `whiteboard_renderer_v2` → silent H.264 MP4, 0/25/50/75/100 contact sheet and metrics. The V2 engine is invoked only by a local synthetic CLI. The default-OFF feature flag, V1 `.run()` and V1 HTTP jobs are untouched. Current `memory:` refs are process-local, not durable Lightning transport. Fixture `review_ref` is still unverified caller metadata, not server approval.

The extractor checks source cutout and mask SHA-256 and works per stable object ID, independent of object type/name/count. It derives the object outline from binary mask boundary, finds *interior* details using local color-gradient strength and an adaptive 92nd-percentile threshold after excluding a 2-pixel edge band, and traverses adjacent 8-neighbor graph edges into paths with explicit pen lifts. It generates alternating, mask-clipped source-color brush scanlines. It does **not** regenerate a child figure, fit a generic stick-person, recover actual pen history, or use a single global darkness threshold. Dense/untraceable candidates return `NEEDS_STROKE_REVIEW`; missing/tampered source/mask returns `SOURCE_ASSET_MISMATCH` or `NEEDS_MASK_REVIEW`.

The draw schedule visits all object outlines, then details, then color paths. Length-based timing approximates pen travel; explicit pauses separate strokes, followed by a hold. Duration/fps/stroke-count limits fail `DRAW_TIMING_INFEASIBLE`. Optional beat reference is the scene's approved segment ID; no new TTS/word alignment is claimed. Renderer traces each path progressively with a round brush and reveals only the source RGBA pixels beneath it; color is **not** a rectangular-cell reveal or scene-wide opacity fade. Before encoding it verifies 100% of source-object pixels are reachable by the brush itinerary, and after encoding it compares the raw final frame pixel-by-pixel with the canonical composer target. No last-frame replacement/snap is used. Optional hand/cursor is absent; no false pen-tip claim.

The extraction is a raster approximation. 8-neighbor graph junctions can fragment paths, gradient thresholds can confuse JPEG ringing or texture for detail, and horizontal fill paths produce a rigid reveal. For highly detailed art, manual path review or a stronger object-aware vector/brush model remains necessary. The present fixture A has almost no genuine source interior detail; synthetic geometry cannot prove preservation of hair, eyes or clothing in a real child's drawing. A supplementary test adds thin violet/magenta curved marks inside a reviewed fish mask and verifies they remain in the cutout and are traced as details; this is not a third real/independent accepted drawing.

## Contract example

`SourceObjectStrokesV2` is a versioned JSON schema. The actual full exports are retained outside Git at `D:/Codex/Sketch2Life/milestone2_artifact_backup_2026-10-09/*-strokes.json`. A shortened example (not a full schema-valid object) is:

```json
{
  "contract": "SourceObjectStrokesV2", "version": "2.0",
  "object_id": "fish-blue", "source_image_sha256": "<64-char source digest>",
  "source_asset_ref": "memory:source-asset:<digest>",
  "source_mask_ref": "memory:mask:<digest>",
  "z_index": 0,
  "outline_paths": [{"stroke_id": "outline-0001", "phase": "OUTLINE",
    "points": [[0, 35], [1, 34]], "brush_width": 2,
    "color_rgb": [52, 124, 205], "pen_up_before": true}],
  "detail_paths": [], "color_paths": []
}
```

The full schema also requires source/mask/asset hashes, dimensions, extraction method and covered-source-pixel count. The actual `SceneDrawScheduleV2` export records object order and each stroke's phase, start/end seconds, pen-up pause and beat reference. The example above is explicitly illustrative, not submitted to the parser.

## Files created/modified in this milestone

1. `backend/src/sketch2life/contracts/schemas/story_strokes_v2.py` — versioned per-object stroke and scene schedule contracts.
2. `backend/src/sketch2life/infrastructure/media/object_stroke_engine_v2.py` — source-bound CPU extraction, no V1 tracer edits.
3. `backend/src/sketch2life/application/services/story_draw_schedule_v2.py` — phase/order/timing compiler.
4. `backend/src/sketch2life/infrastructure/media/whiteboard_renderer_v2.py` — progressive source-pixel brush renderer, MP4 and fidelity checks.
5. `backend/src/sketch2life/application/ports/story_world_v2_ports.py` — implementable `ObjectAwareStrokePort` signature; other Milestone-2/3 ports remain interface-only.
6. `tools/story_whiteboard_v2_pilot.py` — synthetic offline A/B/JPEG CLI and JSON evidence exports.
7. `backend/tests/unit/test_whiteboard_v2_engine.py` — stroke continuity/order, source binding, golden target, transform, codec/decode, thin detail, error and round-trip tests.
8. `features/FEAT-030-whiteboard-story-video/plan/PLAN.md`, `approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md` — scope/approval and feature evidence updates.
9. `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE2_RESULT.md` — this report.
10. Experimental exports — three silent MP4s, three contact sheets, three stroke manifests, three draw schedules and three metrics JSONs; all synthetic, excluded from Git, and backed up at `D:/Codex/Sketch2Life/milestone2_artifact_backup_2026-10-09/` with `SHA256_MANIFEST.md`. The original untracked `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/` files remain in the local checkout. Neither location is part of this documentation commit.

## A/B pilot results and artifacts

| Fixture | Objects | Outline/detail/color paths | Raw final vs canonical | Decoded MP4 last-frame MAE vs canonical | Source input vs canonical |
|---|---:|---:|---:|---:|---:|
| Family PNG A | 6 | 40 / 1 / 248 | 0 changed, MAE 0 | 0.839 | 0.000 |
| Ocean PNG B | 5 | 26 / 190 / 161 | 0 changed, MAE 0 | 0.454 | 9.154 |
| Ocean JPEG B | 5 | 26 / 230 / 161 | 0 changed, MAE 0 | 0.370 | 9.476 |

All three source-object brush coverage values are 1.0 (fraction of nontransparent **cutout** pixels, not segmentation IoU or full-image coverage). All MP4s decode as 72 frames at 12 fps, duration 6 seconds, with visibly different blank/partial/final frames. H.264 is lossy, so encoded final frames are not pixel-identical; the raw pre-encode frame is. The renderer has no generated new objects or articulated motion.

The following are **filenames in the external backup directory above, not repository links**. A clone of this repository will not contain them. Verify each file against `D:/Codex/Sketch2Life/milestone2_artifact_backup_2026-10-09/SHA256_MANIFEST.md` before review.

| Fixture | MP4 filename | 0/25/50/75/100 sheet filename | Stroke/schedule/metrics JSON filenames |
|---|---|---|---|
| A | `family-v2-pilot.mp4` | `family-v2-0-25-50-75-100.png` | `family-{strokes,draw-schedule,metrics}.json` |
| B PNG | `ocean-png-v2-pilot.mp4` | `ocean-png-v2-0-25-50-75-100.png` | `ocean-png-{strokes,draw-schedule,metrics}.json` |
| B JPEG | `ocean-jpeg-v2-pilot.mp4` | `ocean-jpeg-v2-0-25-50-75-100.png` | `ocean-jpeg-{strokes,draw-schedule,metrics}.json` |

Example offline command:

```text
backend/.venv/Scripts/python.exe -m tools.story_whiteboard_v2_pilot --fixture ocean-png --output-dir features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots --duration 6 --fps 12
```

Run once for each fixture (`family`, `ocean-png`, `ocean-jpeg`) in a local output directory; inspect and hash the results before comparing with the external backup. Reproduction uses synthetic inputs and creates no approved story job. The listed command writes to the local untracked path only; it is not required for reading this Git report.

## Verification and compatibility

New V2 unit tests, existing V2 unit/contract and V1 renderer/planner/file tests were run. The final post-edit focused run returned **101 passed, 0 failed** in 79.00 s. The final post-edit broad unit/contract run excluding four Vision V3 groups returned **1,699 passed, 5 skipped, 86 deselected, 0 failed** in 184.73 s. Ruff passed on all seven new/changed Python files. Mypy `--follow-imports=silent` passed on five V2 source modules. Repository security returned `REPOSITORY_SECURITY_VALID` with 1,650 publishable files scanned. `git diff --check` passed.

```text
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_whiteboard_v2_engine.py backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py backend/tests/contract/test_story_video_file_api.py
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit backend/tests/contract -k 'not vision_v3_quality_fixtures and not vision_v3_mapping_fixtures and not vision_v3_quality_benchmark and not vision_v3_quality_execution'
```

The four Vision V3 name groups are excluded from the broad test due the already-missing `features/FEAT-003-multimodal-understanding/fixtures/vision-v3-quality/images/v3q-fixture-01.png`; the previous unfiltered M1 run had nine failures. Five skips remain separate. Do not call the whole repository green. No V1 source/HTTP/provider code changed; the pre-existing V1 worktree edits remained untouched.

No GPU/LightningAI, child media, adult server approval, durable mask/asset store, narration synchronization, hand asset, scene motion/transition or complete 40–60-second story-video test was performed. Before Milestone 3, resolve full-source background preservation, improve natural pen paths/brush texture with permitted complex-art benchmark and human sign-off, persist reviewed assets, implement server-bound event/mask/script approval, and only then plan action/transition/audio integration. **Do not expose this prototype via upload.**
