# House Drawing Proof — Revision 26 (2026-10-10)

## Verdict

**Technical execution: PASS. Visual QA: FAIL / VISUAL_QA_NOT_PASSED.**

The renderer can preserve and progressively reveal the real house source asset. It does NOT currently produce a natural whiteboard drawing of the house. Nearly the first33 seconds show sparse fragments; the recognizable house arrives during COLOR. Technical PASS means faithful execution of the supplied paths/masks, not satisfactory structural line drawing. Owner review is still required.

One proof only. No artwork replacement, parameter loop, paid inference, audio or full story.

## Deliverables outside Git

Directory: D:/Codex/Sketch2Life/house_video_proof_2026-10-10/

- [Clean MP4](D:/Codex/Sketch2Life/house_video_proof_2026-10-10/house-clean.mp4)
- [Actual-tip debug MP4](D:/Codex/Sketch2Life/house_video_proof_2026-10-10/house-pen-debug.mp4)
- [Decoded 0/25/50/75/100 contact sheet](D:/Codex/Sketch2Life/house_video_proof_2026-10-10/encoded-contact-sheet.png)
- [Decoded phase/time comparison](D:/Codex/Sketch2Life/house_video_proof_2026-10-10/phase-temporal-contact-sheet.png)
- [Final decoded frame](D:/Codex/Sketch2Life/house_video_proof_2026-10-10/final-decoded-frame.png)
- [Timing/path execution report](D:/Codex/Sketch2Life/house_video_proof_2026-10-10/timing-and-path-report.json)

Other deliverables: source-house-target.png, final-native-rgba.png, final-raw-frame.png, native-difference-x8.png, decoded-difference-x8.png, source-paths.json, path-execution.json, frame-execution.json (1542 entries), artifact-sha256.json and final-handoff-sha256.json.

Contact percentage refers to drawing timeline, not video duration or color coverage. Phase sheet explicitly shows2/4/10/20/32.8/33/35/38/42/50/60s from decoded clean and debug videos. I inspected these decoded temporal sheets and decoded final, not a claim of human real-time playback acceptance.

## Source provenance and coordinate verification

Original family source SHA-256:52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3.
Stable object: family-52caf90a-house.
Master mask SHA-256:e9ed30e26766027fda5e019dbd4fa4a3b179ac3cabf2774b0543868337de3b54.
Registry asset SHA-256:3daa7b2eaf1b4056dfdd35eb0a8b9312ace0685521b458b3eb7c995d7e7179ae.
Existing paths JSON SHA-256:4e1a3d22f1d9d61a5e414dda26571745a3c104ed016e5e987b98578d5c4d614e.

Loaded228x118 registry cutout from existing real_schedule_debug world. Verified byte-exact RGBA against original image crop at[315,0,543,118] with the corresponding master mask crop. The full594x336 manifest cutout was NOT mistakenly paired with228x118 local path coordinates. No source asset or master mask was rewritten.

Paths/phase masks/timing came from the existing StepA house preparation, hash-checked against its saved manifest. Source image and all9 master masks were checked before and after. These records remain provisional local benchmark data, not production Gate A/B approval.

## Execution method

An isolated source adapter uses the same current-renderer arc-length partial-path function as butterfly, explicit UP/DOWN motion, spatial brush footprint and original RGBA pixels. House is NOT passed through butterfly artwork generation or approximated with geometry. Native paths and timings unchanged.

The progressive mask is clipped to source alpha and the authorized OUTLINE/DETAIL/COLOR masks. Completed path coverage accumulates. RGB values are read from source; no recoloring or opacity fade. Debug tip uses the exact current stroke endpoint; red=DOWN, blue=UP. Debug path annotations are absent from clean output.

Presentation is a fixed3x close-up on white960x540, preserving the source aspect ratio; no moving camera, scene rendering or transitions. All original texture/color remain in the raw completed source asset. Display resampling and encoded chroma compression introduce expected presentation softness.

## Measured timing and path execution

Both outputs:H.264/yuv420p,24FPS,960x540,1542 decoded frames,64.25s, silent.
Drawing62.865307323s; end hold1.384692677s. The request gave no house-specific12–15s limit; native pacing was preserved rather than forcing154 paths into butterfly duration.

| Phase | Paths | Authorized source pixels | Execution time |
| --- | ---: | ---: | --- |
| OUTLINE | 3 | 74 | 0.000–4.108s |
| DETAIL | 111 | 149 | 4.455–32.811s |
| COLOR | 40 | 21,779 | 33.139–62.865s |

154paths,153 pen lifts,15 zero-length/dot paths.
Total pen-up travel time14.540873341s.
1542 sampled states:1161 DOWN,347 UP,33 REST,1 IDLE.
439 DOWN frames reveal no NEW source pixel (can be already-covered ink or paths removed by phase masks; not all are necessarily fully invisible).
Color paths contain263 horizontal segments out of486 total segments; connected hatches and turns remain mostly tile-oriented.
Render/encode/decode/contact wall time21.140s on local CPU. Peak memory not measured.

## Technical checks

- Exact source crop/mask/identity match:true.
- No pixels outside permitted ink appear before COLOR:0 violations.
- No source pixel added outside current partial brush or naturally completed prior brush footprints:0 violations.
- Debug tip error against active path endpoint:0 native pixels. Same geometry is used for both; this is not an independent perceptual synchronization judgment.
- Maximum new COLOR pixels in a frame:65 (0.298% of21,779 source pixels).
- Final visible source coverage:21,779/21,779,100%.
- Final native RGBA byte-identical to source asset:true; no final snap or replacement.
- Native RGB difference map:zero. Alpha equality checked separately through complete RGBA equality.
- Decoded final RGB MAE vs identically scaled source target:0.825032793/255. MP4 is lossy, not pixel-exact.
- Each MP4 decoded1542frames at24FPS and64.25s.
- Existing production V2/default flag/source masks/Gates unchanged.

The footprint's finite brush radius can expose neighboring pixels around the tip, as real brush width would. This is not a center-pixel-only reveal or whole-region pop. No technical compositing failure detected; these checks do not validate natural illustration quality.

## Visual diagnosis: root cause, not a parameter guess

| Component | Evidence | Assessment |
| --- | --- | --- |
| Phase separation | Only74+149 disjoint ink pixels out of21,779 source pixels (1.024%). Neutral-dark heuristic rejects most colored/soft pencil contours. | PRIMARY problem: structural lines withheld until COLOR. |
| Path reconstruction | OUTLINE follows asset silhouette rather than a full roof/wall/window/door drawing graph.111 DETAIL paths/15 dot paths are raster fragments. | PRIMARY problem: no coherent semantic pen sequence. |
| Brush trajectories | Source engine pencil coloring connects horizontal hatches within32px tiles. Decoded35/38/42/50s frames show a stepped sweep of image sections. | Major visual limitation: scan-like growth despite small per-frame reveals. |
| Stroke ordering | OUTLINE then DETAIL then COLOR is respected, but spatial order inside phases is raster/tile based; long pen-up overhead and unrevealing paths consume time. | Correct phase order is not sufficient; content-aware ordering missing. |
| Pen renderer | Partial paths and tip stay synchronized;153 lifts and constant-speed trajectories visibly disrupt continuity. | Faithfully executes inadequate input; adding easing alone will not fix missing ink. |
| Compositing | Source crop/final RGBA exact, no off-brush leakage or final snap. | Not the primary root cause. Encoding adds minor color loss only. |

Compared with authored butterfly paths, source house paths show a much larger upstream structural-ink failure. This evidence does NOT justify simply widening the brush, lowering all thresholds, increasing speed or replacing the source image.

## One focused next fix proposal — NOT implemented

If owner approves a repair round, do one HOUSE SOURCE-PATH COMPILATION correction, not parallel experiments or a new architecture plan:

1. Bind roof/wall/window/door structural contours from this exact source to one reviewed continuous ink-path pack. Separate persistent contour evidence from pencil texture; join only genuine connected source contours, never invent geometry across gaps.
2. Replace the neutral-RGB-only phase gate for this pack. If neutral pencil ink must precede colored source contours, use an explicitly source-derived TEMPORARY ink layer with provenance, not silent recoloring of the original; approval is required for that derived layer. Final color must still come from immutable source pixels.
3. Give the same pack contour/region-aware brush tracks for roof, walls and windows instead of32px tile scan ordering, and remove paths whose allowed intersection is empty. Retain truthful travel/time budgets; do not speed up to conceal fragmentation.
4. Re-render ONE clean/debug comparison on the same house. Require recognizable house structure before COLOR, no ghost paths/full-region pop, exact raw final, and visible improvement in actual MP4. If it still fails, stop and report raster reconstruction limits.

This is a single focused input-to-render correction with one comparison, NOT an implementation authorization or new planning loop. No fix was applied in this proof.

## Tests

Final selected command:

```text
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_house_video_proof.py backend/tests/unit/test_butterfly_video_proof.py backend/tests/unit/test_butterfly_candidate_refinement.py backend/tests/unit/test_whiteboard_slice_feasibility.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py
85 passed in19.31s

backend/.venv/Scripts/python.exe -m ruff check tools/render_house_video_proof.py backend/tests/unit/test_house_video_proof.py
All checks passed!

$env:MYPYPATH='backend/src'
backend/.venv/Scripts/python.exe -m mypy --follow-imports=silent tools/render_house_video_proof.py
Success: no issues found in1 source file

git diff --check
PASS
backend/.venv/Scripts/python.exe tools/validate_repository_security.py
REPOSITORY_SECURITY_VALID
```

Eight new proof tests plus77 existing selected tests. Initial run:78PASS/7 fixture setup errors because synthetic ObjectStrokeV2 fixture omitted required color_rgb; fixed fixture only. Initial Ruff import/line-format issue fixed. No runtime drawing thresholds changed; final selected suite has no skips/deselections.

Mypy scope one tool, with explicit upstream imageio_ffmpeg import-untyped exemption. Full repository/Vision V3/GPU/LightningAI/audio/Gate production were not tested. Technical result is the house proof only, not repository-wide or full-story acceptance.

## Repository safety and changed files

HEAD/branch unchanged:93668ffdaa7f2890fe9498596c670006a87eba4a, codex/feat-018-contract-plan; index empty.
334preexisting Python files have unchanged combined name/content digest. Old butterfly/rig/renderer/extractor source and prior dirty edits untouched. V1 default; story_render_v2_enabled remains False.

New files:
- tools/render_house_video_proof.py: offline saved-source/path adapter, encoder/decode/audit.
- backend/tests/unit/test_house_video_proof.py: source fidelity, phase clipping, pen-up/tip/final hold/permission tests.

Feature documentation updated: approvals/TASK_APPROVAL.md, plan/PLAN.md, CONTEXT.md, DECISIONS.md, status/STATUS.md, evidence/README.md and evidence/SKETCH2LIFE_HOUSE_DRAWING_PROOF_RESULT.md. Private report/media remain outside Git.

Reproduce into a NEW private directory:
```text
backend/.venv/Scripts/python.exe -m tools.render_house_video_proof --source-manifest D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/source-object-manifest.json --world D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/benchmark-world.json --paths-dir D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/family-52caf90a-house --output-dir <new-private-output-directory> --confirm-house-proof
```

No source rewrite, full story, TTS, remote inference/upload, paid GPU, commit/stage/push/deploy. Stop after handoff for owner review.
