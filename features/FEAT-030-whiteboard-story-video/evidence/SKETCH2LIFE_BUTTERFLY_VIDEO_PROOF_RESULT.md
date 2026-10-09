# Butterfly Drawing Video Proof — Revision 25

## Verdict

TECHNICAL_PROOF_PASS for the checks below. VISUAL_QA_NOT_PASSED / PENDING_OWNER_VIDEO_REVIEW. Approval is technical proof only, not final artwork, server Gate A/B or VideoScribe-equivalent product acceptance. One bounded offline render, no artwork/path retuning.

Artifacts: D:/Codex/Sketch2Life/butterfly_video_proof_2026-10-09/

- [Clean MP4](D:/Codex/Sketch2Life/butterfly_video_proof_2026-10-09/butterfly-clean.mp4)
- [Pen-debug MP4](D:/Codex/Sketch2Life/butterfly_video_proof_2026-10-09/butterfly-pen-debug.mp4)
- [Decoded 0/25/50/75/100 contact sheet](D:/Codex/Sketch2Life/butterfly_video_proof_2026-10-09/encoded-contact-sheet.png)
- [Decoded temporal pen review](D:/Codex/Sketch2Life/butterfly_video_proof_2026-10-09/decoded-temporal-review-pen-debug.png)
- [Final decoded frame](D:/Codex/Sketch2Life/butterfly_video_proof_2026-10-09/final-decoded-frame.png)
- [Timing/path audit](D:/Codex/Sketch2Life/butterfly_video_proof_2026-10-09/timing-and-path-report.json)

Additional files: final-native-rgba.png, final-small-rgba.png, final-raw-frame.png, target-clean-frame.png, decoded-difference-x8.png, frame-execution.json (306 samples), path-execution.json (21 actions), decoded-temporal-review-clean.png, artifact-sha256.json. Original generation manifest predates extra decoded review sheets; final-handoff-sha256.json covers final deliverables.

## Immutable baseline and presentation

Saved candidate SHA-256 c70031dadfc17b7ca8aa85254e29ae689da8d25869ac7b12787be1c93698ef4b.
Paths JSON SHA-256 a810be9cab40d85a95be70add302d37a260ff4ad53f2ab8555f04757d5366f8c.

Loaded the existing native RGBA, fill/ink layers, masks, 21 paths and smaller pen timeline from review-final. Did NOT regenerate artwork, modify masks or reorder paths. Seven OUTLINE, nine DETAIL, five COLOR; 20 pen lifts.

Actual small asset is resampled to56x40, shown both at native size in an inset and as an8x close-up on white960x540. Magnification is a fixed inspection view, not faster retiming or a garden/story scene. Downsampling makes texture less visible;8x magnification cannot restore lost detail.

## Actual encoded execution

Both MP4s: H.264/yuv420p, silent,960x540,24FPS,306 decoded frames,12.75 seconds. Drawing takes11.399049899s under unchanged smaller pacing, then1.350950101s end hold. Hold is repetition of naturally completed state, not final snap. No time stretching, opacity fade, full-region reveal or final artwork replacement.

| Schedule | Time |
| --- | --- |
| OUTLINE | 0.000–2.312s |
| DETAIL (after pen-up) | 2.395–4.562s |
| COLOR (after pen-up) | 4.645–11.399s |
| End hold | 11.399–12.750s |

All21 per-path start/end, travel lengths and pen-up/down durations are in path-execution.json. There are20 minimum two-frame pen lifts (total1.667s), with constant speed per down path. Native brush footprints drive spatial reveal of immutable pigment; debug tip uses the same arc-length endpoint. Red tip indicates DOWN; blue indicates UP/REST. Debug's colored traveled-path annotation is not artwork or an extra stroke in clean video.

## Frame audit and fidelity

- Early COLOR frames:0.
- Coverage changes while UP relative to exact previous pen-down completion:0.
- Maximum tip/active path endpoint error:0 native pixels. This checks renderer geometry; it is not an independent human perceptual judgment.
- Maximum new color coverage per frame:509 native pixels (about2.51% of20,251 pigment pixels); not a full-wing or full-canvas reveal.
- Final native RGBA byte-exact versus saved native target: true.
- Final raw presentation byte-exact versus target under identical resize/compositing: true.
- Decoded final RGB mean absolute error versus raw target:0.290936214/255, due H.264/yuv420p compression. Encoded MP4 is NOT byte-identical artwork; raw PNG is authoritative.
- Both306-frame decode counts and12.75s metadata verified.
- Render/encode/decode/contact preparation wall time15.888s; no GPU. Peak memory was not measured.

Brush covers a neighborhood of the tip (round cap/brush width) and native edge antialias; no claim that only the exact center pixel changes. Texture pixels enter by spatial footprint, not opacity blending over time.

## Quality findings from encoded temporal evidence

Inspected decoded contact sheets plus dense early-outline and first-color samples at0.125–2.000s and4.625–6.500s. This is actual MP4 decode evidence, not static synthetic rendering alone; real-time playback/owner acceptance is still pending.

1. Outline: continuous within each wing/body/antenna path; sampled progression0.125/0.250/0.375s shows one curve closing, not disconnected point clusters. At small scale a wing completes in roughly0.28–0.36s; it may feel fast in the enlarged inspection view.
2. Pen motion:20 lifts are explicit, with no in-air drawing. Each lift is roughly83ms. Repeated short travel stops and constant path speed can feel rhythmic/mechanical; no easing or pressure animation was added to baseline.
3. Ordering: all outlines precede details, all details precede pigment. No observed early color scheduling leak.
4. Coloring: follows perimeter then inward contour spirals rather than parallel horizontal scan rows. HOWEVER repeated inward laps and temporary central white holes remain regular/mechanical. This is primarily brush-trajectory design, not a compositing/order failure.
5. Texture: candidate native paper/pencil pigment is unchanged. Resampling to56x40 and8x inspection enlargement visibly soften texture and veins; encoded chroma subsampling adds minor color softness. Fine grain is not as legible as native candidate.
6. Color appearance: temporal samples show edge-following growth and gradual inward filling. No whole-region pop or completion snap detected mechanically; this does not prove pleasing natural pencil coloring.
7. Compositing: no raw final mismatch or pen-up reveal. Debug path lines are diagnostic overlays only, and do not belong to clean artwork.

No quality threshold was tuned, no second artwork generation or indefinite refinement loop. Technical pipeline works; natural VideoScribe-like motion is not accepted by these checks. Current blockers are repetitive color trajectory, constant-speed/short pen-lift cadence, and small-scale texture readability, not missing coverage or an early-color ordering error.

## Tests and checks

Executed from repository root:

```text
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_butterfly_video_proof.py backend/tests/unit/test_butterfly_candidate_refinement.py backend/tests/unit/test_whiteboard_slice_feasibility.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py
77 passed in19.83s
backend/.venv/Scripts/python.exe -m ruff check tools/render_butterfly_video_proof.py backend/tests/unit/test_butterfly_video_proof.py
All checks passed!
$env:MYPYPATH='backend/src'
backend/.venv/Scripts/python.exe -m mypy --follow-imports=silent tools/render_butterfly_video_proof.py
Success: no issues found in1 source file
git diff --check
PASS
backend/.venv/Scripts/python.exe tools/validate_repository_security.py
REPOSITORY_SECURITY_VALID
```

Mypy uses MYPYPATH=backend/src; imageio_ffmpeg alone has an explicit import-untyped exemption because upstream ships no stubs. Initial Mypy reported that missing stub and Candidate list-unpacking typing errors; fixed explicit positional layer arguments only, without changing frame behavior. Five new proof tests plus72 existing selected tests; no skips/deselections in selection. Full repository, Vision V3, HTTP, LightningAI, audio and Golden Story were not tested. No claim of repository-wide PASS.

## Safety and changed files

HEAD remains93668ffdaa7f2890fe9498596c670006a87eba4a on codex/feat-018-contract-plan, index empty. Before snapshot contains332 existing Python files; their aggregate name/content digest is unchanged after excluding two NEW proof files. Source image and all nine master mask digests validated before and after render. Original source manifest, candidate files and old artifacts remain intact. V1 default, V2 flag False; no endpoint/Gate changes.

New code:
- tools/render_butterfly_video_proof.py: isolated saved-baseline encoder/decoder/per-frame audit.
- backend/tests/unit/test_butterfly_video_proof.py: permission, pacing/order, clean/debug tip, final hold tests.

Documentation updated: feature approvals/TASK_APPROVAL.md, plan/PLAN.md, CONTEXT.md, DECISIONS.md, status/STATUS.md, evidence/README.md, evidence/SKETCH2LIFE_BUTTERFLY_VIDEO_PROOF_RESULT.md. Private copy of report and media outside Git. Earlier dirty worktree remains unchanged.

Reproduction (choose a NEW private output directory, never overwrite prior outputs):
```text
backend/.venv/Scripts/python.exe -m tools.render_butterfly_video_proof --candidate-dir D:/Codex/Sketch2Life/butterfly_refinement_2026-10-09/review-final --source-manifest D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/source-object-manifest.json --output-dir <new-private-output-directory> --confirm-technical-proof-only
```

No TTS/API/network/inference/GPU rental, commit/stage/push/deploy or Golden55s render. Stop here for owner video review. Asset/style acceptance and further slice timing remain separate gates.

