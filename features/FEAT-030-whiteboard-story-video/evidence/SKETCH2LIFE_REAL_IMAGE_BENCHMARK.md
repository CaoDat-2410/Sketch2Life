# Real family image benchmark — provisional offline run

Date: 2026-10-09 (Asia/Saigon). Current status: **BENCHMARK_FAILED / NEEDS_STROKE_REVIEW / VISUAL_QA_NOT_PASSED**. Preparation passed structurally; the owner subsequently granted **PROVISIONAL BENCHMARK APPROVAL**, not product quality or server Gate A/B.

## Actual benchmark result

The exact original JPEG and unchanged nine-mask set were inspected at native 594 × 336 resolution and passed to the current V2 engine for a requested 20-second, 24-FPS static drawing clip. This was one actual offline attempt, using `refined` strategy, with no product-code modifications or model/provider calls. Source-object manifest digest:

`693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14`

The process returned **exit 1** after approximately **1.695 seconds**, during extraction of `family-52caf90a-garden`. The scheduler and video renderer were **not reached**. The concrete failure is:

`NEEDS_STROKE_REVIEW: too many candidate ink pixels`

Module `backend/src/sketch2life/infrastructure/media/object_stroke_engine_v2.py`, `extract_object_strokes`, line 211, calls `_paths_legacy(details, limit=2000)`; `_paths_legacy` raises at line 34. Even `refined` strategy first computes legacy detail paths for comparison, so this guard fires before refined detail selection. Exception type is `StoryWorldError`; its definition module is not the module causing the extraction failure.

Independent read-only diagnostics reproduced **2,798 detail-candidate pixels** for garden (threshold 88), exceeding **2,000** by 798. Its detail density is approximately **4.95%**, below the separate 25% density guard; its 767 boundary pixels are below the 4,000 contour limit. The failed guard is specifically the absolute detail count. Garden includes both flower contours and original pencil/grass texture; the engine has not demonstrated that it separates those appropriately. A read-only diagnostic also found **3,453** detail candidates in the path region, which predicts a further limit issue; extraction of path was not attempted in this stopped run.

The five objects extracted before failure were:

| Object | Outline paths | Detail paths | Color paths |
|---|---:|---:|---:|
| Mother | 6 | 147 | 65 |
| Father | 3 | 131 | 70 |
| Child | 2 | 94 | 47 |
| House | 3 | 240 | 76 |
| Tree | 29 | 86 | 56 |

These are actual partial extraction results, not a completed drawing or evidence of natural motion. No guard threshold was increased, detail skipped, garden removed, mask split to evade the guard, synthetic replacement used, or incomplete clip encoded.

## Native detail inspection and fidelity

Source/native overlay and individual native crops of both shared hands, all feet/shoes, branches and flowers were viewed before extraction. Their original pixels remain in the complete mask partition. Small background fringes and shared-hand/branch-edge ownership are still imperfect for independently moving objects; this is a static benchmark only. No obvious detail loss from the assembled static target was observed, so masks were not changed. The approved input mask hashes and original bytes remain unchanged.

The canonical **target still** was rendered successfully by the existing `SceneStateComposer`: source → target MAE **0.0**, changed pixels **0** across all 594 × 336 pixels. Independent regional comparisons also returned zero differences for hands, feet/shoes, branches, eyes/hair/glasses/clothing and flowers. Layout, decoded JPEG colors and texture are exactly retained in this still. JPEG comparison is to the decoded source pixels, not an unavailable uncompressed original.

- **Source fidelity:** exact for the assembled static target; progressive/encoded fidelity **not evaluated** because no video exists.
- **Stroke naturalness:** **not evaluated on video**. Partial paths alone cannot establish pen speed, smoothness, timing or reveal quality.
- **Coloring texture:** source RGB/texture retained in cutouts and target; the actual progressive coloring and codec texture quality are **not evaluated**.
- **Details lost/simplified:** zero pixel differences in target and named regional comparisons; no generated geometric substitutes. Semantic mask-edge ownership remains imperfect and object animation remains unaccepted. Detail extraction for garden failed rather than silently deleting flowers or texture.
- **Visual QA:** **NOT PASSED**, because the real-image drawing clip has not completed. This result does not establish Level-2 Lightning or product acceptance.

## Actual run artifacts (outside Git)

Directory `D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/benchmark-01/`:

- `native-source-overlay.png`: original and overlay at native size; `critical-regions-native.png`: original/overlay/ownership crops, without resizing.
- `provisional-approval.json`: actual owner local benchmark permission bound to source/manifest/mask hashes; server Gate A/B remains `NOT_VERIFIED`.
- `benchmark-world.json`, `benchmark-scene.json`, `registry-cutouts/`: source-grounded offline input and unchanged-position source assets. The event/segment/fact/anchor names in this world are explicitly **local benchmark permission metadata**, not authenticated story facts, approved narration, server session/package approval or production Gate records. No story planner or HTTP job was invoked.
- `source-decoded.png`, `canonical-final.png`: decoded source and canonical target still. **The latter is not a final MP4 frame.**
- `diff-source-canonical.png`, `diff-source-canonical-x4.png`: black difference maps (zero difference); `source-canonical-difference-contact-sheet.png`: original, target and difference comparison. **This is not a 0/25/50/75/100 drawing-video sheet.**
- `partial-strokes.json`: verified extraction for the first five objects only.
- `benchmark-metrics.json`, `failure-traceback.txt`: actual failed attempt, stage, object, source bindings and elapsed time.
- `extraction-limit-diagnostics.json`, `garden-detail-candidates.png`, `garden-detail-candidates-overlay.png`: exact triggering count and visible selected detail pixels.
- `benchmark-evidence-verification.json`, `artifact-sha256.json`: independent verification and artifact digests.
- Reproduction/evidence scripts: `inspect_native_masks.py`, `run_benchmark.py`, `diagnose_detail_limits.py`, `verify_run_evidence.py`.

**Not produced:** MP4, draw schedule, video milestone sheet, final raw video frame, final decoded frame or source-versus-video difference map. The static-target comparison must not be mislabeled as any of these.

## Commands and actual outcomes for provisional run

Use `backend/.venv/Scripts/python.exe` from the checkout, with the four script paths under the private `benchmark-01/` directory:

1. `inspect_native_masks.py` — exit 0, source/mask hashes and native overlay checked; reviewed original-resolution images.
2. `run_benchmark.py` — **exit 1**, actual V2 extraction failed on garden with `NEEDS_STROKE_REVIEW` before schedule/encoding; source target still generated.
3. `diagnose_detail_limits.py` — exit 0; read-only diagnostics, no thresholds changed or render retried.
4. `verify_run_evidence.py` — exit 0; source/approved-mask manifest unchanged, static-target equality and absence of MP4 independently verified.
5. Final `git diff --check` and `tools/validate_repository_security.py` — exit 0; `REPOSITORY_SECURITY_VALID`, 1,655 publishable files scanned. Local HEAD remains `93668ff`, staged diff empty. Settings and pipeline still declare `story_render_v2_enabled: bool = False`.

No regression pytest run was repeated because this task did not modify product code. Prior Milestone 2.1 tests are separate evidence, not proof this real-image attempt passed.

## Source identity and consent

The owner reattached `<owner-downloads>/familly.jpg` after the requested `family1.jpg` was not found. Its exact machine path is recorded in the private source-object manifest, rather than published in this report. This resolves the filename mismatch; no file was renamed and no replacement image was selected. Its SHA-256 matches the original previously consented for a local-only benchmark:

`52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`

The original is readable JPEG, RGB, 594 × 336, 51,386 bytes. Pillow `verify()` and a separate full pixel decode succeeded. The provenance basis is the owner's attachment/confirmation and exact matching bytes, not an automated forensic claim about authorship. No diffusion, generated replacement, model invocation, paid API or network transfer was used.

Private evidence directory: `D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/`. The byte-for-byte preserved copy is `source-original.jpg`. Source imagery, masks, cutouts and review sheets remain outside the Git checkout.

## Candidate annotation method

The project virtual environment has NumPy and Pillow, but no `sam2`, `torch` or `cv2`; no new dependency/model download was performed. Visible object outlines were traced manually with irregular polygons on the exact source coordinate grid. Branch gaps also use an explicitly documented local cyan-sky pixel exclusion. The polygons follow visible contours rather than substitute rectangles or ellipses. Bounding boxes in the manifest are derived measurements of mask pixels only.

The first overlay was inspected and corrected around the child's feet, mother's neck/shoulder/handbag handle, the left house roof edge and sky/fence classification. These are candidate manual annotations, not automatically successful semantic segmentation. Polygon boundaries can still contain small background fringes or lose antialiased source-edge pixels. Pixels are never recolored in source cutouts.

## Identity manifest

Full manifest: `D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/source-object-manifest.json`.

Each object stores the source digest, binary-mask digest, cutout digest, source pixel bounds, method, review state and notes. Stable IDs derive from the unchanged source hash and semantic label; they do not depend on mask-array order. Current labels are proposals for this source, not authenticated product understanding.

| Stable ID | Meaning / visible pixels | Mask pixels |
|---|---|---:|
| `family-52caf90a-mother` | Woman on left, including handbag | 12,457 |
| `family-52caf90a-father` | Man on right, glasses/hair/clothes | 11,102 |
| `family-52caf90a-child` | Center child, both arms and raised shoes | 6,657 |
| `family-52caf90a-house` | House, roof, windows and door | 21,779 |
| `family-52caf90a-tree` | Visible canopy, trunk and branches | 8,466 |
| `family-52caf90a-garden` | Right-side garden region including grass, flowers and stems | 37,113 |
| `family-52caf90a-sky` | Visible sky above the fence and around foreground | 25,584 |
| `family-52caf90a-path` | Peach-colored path excluding foreground | 50,850 |
| `family-52caf90a-remaining-background` | Remaining lawn, fence, planter and gaps | 25,576 |

Garden is deliberately a **region** asset: no independent per-flower identities or motion are claimed. Bag belongs to the mother; planter/fence belong to background. The overlapping hand regions were partitioned with explicit priority child → mother → father → house → tree → garden. Raw contour overlaps removed: mother 139 pixels, father 56 pixels, house 9 pixels. The manifest discloses those adjustments; resulting zero overlap is structural evidence, not proof the proposed hand ownership is correct. No hidden/occluded pixels were invented.

The preserved preparation manifest still has `NEEDS_IDENTITY_REVIEW` / `NEEDS_MASK_REVIEW` and null full-review references. Subsequent owner approval is recorded separately in `benchmark-01/provisional-approval.json` as static/local/benchmark-only permission; it does not promote those masks to product-approved motion assets. Server Gate A/B is `NOT_VERIFIED`. Local benchmark permission does not authenticate approved story narration or a production session/package.

## Review artifacts

All paths below are relative to the private evidence directory above:

- `mask-contact-sheet.png`: nine individual mask overlays on the exact original (3 × 3).
- `foreground-cutout-contact-sheet.png`: six source assets on transparency checkerboard, useful for finding clipped limbs or leaked background.
- `identity-overview.png`: all proposed regions color-coded together.
- `overlays/<stable-id>-overlay.png`: enlarged individual overlays.
- `masks/<stable-id>.png`: nine full-source-size binary PNG masks.
- `cutouts/<stable-id>.png`: nine full-source-size RGBA PNGs; RGB values are decoded original JPEG pixels, alpha is the candidate mask.
- `source-coordinate-grid.png`, `manual-annotations.json`, `prepare_masks.py`: reproducible source-coordinate annotation evidence.
- `partition-reconstruction.png`: source reconstructed from the complete region partition.
- `candidate-validation.json`, `verify_candidates.py`: independent structural/fidelity checks.
- `artifact-sha256.json`: hashes of private files for review binding, including scripts and the local report copy.

## Checks actually run

Commands use `backend/.venv/Scripts/python.exe` from the Git checkout:

1. `D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/prepare_masks.py` — exit 0; source hash/decode/dimensions checked; candidate artifacts generated.
2. `D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/verify_candidates.py` — exit 0; nine unique stable IDs, source/mask/cutout file hashes, binary values 0/255, exact 594 × 336 dimensions and nonempty masks verified independently. Cutout RGB equals decoded source and alpha equals mask. Pairwise overlap: **0 pixels**; unassigned pixels: **0**; complete partition reconstruction MAE: **0.0**. Review fields remain pending; renderer-executed flag is false.
3. `git diff --check` — exit 0. `tools/validate_repository_security.py` — `REPOSITORY_SECURITY_VALID`, 1,655 publishable files scanned, exit 0. Its initial run detected personal machine paths in this report and the Milestone 2.1 report; those repo locators were replaced with `<owner-downloads>` while exact paths remain in private evidence. Renderer metrics and prior conclusions were unchanged.

These checks do not assess whether every contour is semantically correct. Full-partition MAE can be zero even when a pixel is assigned to the wrong object. It is not a renderer fidelity result or Visual QA PASS. No new pytest regression run is needed for this preparation: product code was not edited. The prior Milestone 2.1 regression evidence remains in its own report.

## Required human review and current limitations

Review the mask overlay and transparent cutouts for mother/father/child identity, shared hands, hair boundaries, mother's shoe/leg gap, child's bent leg, tree branch gaps and house roof edge. Check that the garden grouping and background assignment are appropriate for the benchmark. The source includes thin outlines and JPEG color mixing; manual masks are candidates and need that review before use.

Eyes, father's glasses, hair, clothing textures, tree/flower detail and background are retained in selected source RGB and the zero-difference static target. Their progressive drawing and codec quality remain untested because the actual attempt stopped during extraction. The binary partition can assign edge pixels to background instead of foreground; full static reconstruction retains them but this does not establish clean movable silhouettes. A single garden mask does not support independently moving each flower.

## Benchmark status and next step

**No real-image MP4 or 0/25/50/75/100 video contact sheet exists.** The owner provisionally approved the exact mask set and the actual attempt now shows an extraction-complexity blocker, not a missing permission blocker. Next technical work should address dense detail regions under a bounded, source-preserving tracing strategy and validate garden/path against this same original image. Merely raising the guard or removing texture/flowers would not establish natural strokes or acceptable performance. No such engine repair was implemented in this benchmark task; stop for owner review of the concrete failure first.

Verdict: **FAIL for completed real-image video benchmark; PASS only for source identity and static-target pixel fidelity**. Visual QA: **NOT_PASSED_RENDER_FAILED**. Object animation: **NOT_APPROVED**. LightningAI: **NOT_RUN**.

## Worktree and scope

Branch `codex/feat-018-contract-plan`, local HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`, index empty at task start. Existing Milestone 2.1 and V1/user edits were preserved. Preparation added this feature-local report and revision-12 records; the provisional run updates it and appends revision-13 plan/approval/context/decision/status/evidence records. Private local benchmark scripts/artifacts remain outside Git. Product renderer code and original masks are unchanged. V1 remains default and `story_render_v2_enabled` remains false. No commit, push, merge, deployment, paid inference or Milestone 3.
