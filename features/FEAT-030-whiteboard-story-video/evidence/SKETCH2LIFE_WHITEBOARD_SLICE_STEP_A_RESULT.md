# SKETCH2LIFE — WHITEBOARD SLICE STEP A RESULT

2026-10-09 · Revision23 implements approved preparation from Rev22 · **STEP_A_PREPARED / RENDER_BLOCKED / VISUAL_QA_NOT_PASSED**

## 1. Kết luận

Đã tạo **một butterfly candidate local**, xuất paths/phase masks/pen transitions và gán đầy đủ18 actions trong bản prepared riêng. Không render slice/MP4, không audio/TTS/network/paid/GPU/training/production integration. Không lập architecture plan mới.

Hai blocker chính: **15s không khả thi với nguyên bộ paths và pacing đã khai báo**; **source structural-ink paths/masks hiện chưa đủ nét liền mạch**. Chặn color ở ink phases làm lộ rõ sự thưa/rời của reconstructed ink, không được báo natural drawing PASS. Butterfly art/placement và thời lượng chờ owner review.

Script15s và nội dung local đã được owner duyệt qua latest conditional approval; không là transcript bé, final butterfly artwork approval hoặc server Gate A/B. Năm beats/persistent canvas/new butterfly/camera là scope được giữ. No walk/rig dependency. Không giảm object, đổi script hoặc tăng tốc ngoài duyệt.

## 2. Nguồn bất biến và Git

Original family1.jpg alias familly.jpg,594×336RGBJPEG SHA-256 `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`.
Master manifest SHA `693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14`.
Source/9master masks/9source cutouts hashes unchanged;327 existing Python files byte hashes unchanged.

HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`, branch `codex/feat-018-contract-plan`; index trống. Existing dirty V1/V2 code, hand drafts, rig/media/Rev22 JSON/docs không ghi đè hoặc stage. Three new isolated Python files listed below; V1/default/V2OFF/Gates/HTTP/jobs unchanged.

[Git/code/source verification](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/handoff-verification.json) and [pre-edit snapshot](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/git-before.json).

## 3. Butterfly candidate

- [Candidate preview](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/butterfly-candidate-preview.png)
- [Transparent native artwork](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/butterfly-candidate.png)
- [Placement on actual source](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/butterfly-source-placement-preview.png)
- [Draw-path preview](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/butterfly-draw-path-preview.png)
- [Manifest/art recipe/PNG SHA-256/provenance](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/butterfly-candidate-manifest.json)
- [Actual authored outline/detail/color paths](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/local-new-butterfly-01/paths.json)

Native128×92, irregular locally authored cubic control-point curves rasterized with1–2px width variations, textured orange/cyan wings drawn with deterministic grain/hatch modulation. Palette sampled by explicit color selectors from actual family image; new grain is **procedural NEW art**, not original source pixel or AI recovery. No image-generation model used. Identity `local-new-butterfly-01`, provenance NEW_LOCAL_AUTHORED_ART_NOT_SOURCE_OBJECT, art approval NEEDS_ARTWORK_APPROVAL; server Gate NOT_VERIFIED. Organic raster candidate, not replacement geometry for a source character.

Placement proposed at native original x455/y136 with scale0.60;actual preview size77×55. Position/overlap/style need review. Placement image is a **static art-position composite on full original**, NOT a whiteboard frame, story render or evidence old canvas was drawn already. Existing source image bytes untouched. SourceRGB fidelity later excludes explicitly occluded pixels under new butterfly when comparing composited final.

Paths:5outline/6detail/55color including11 zero-length coverage repair dabs. This makes66paths; color dabs/horizontal hatch style are still quality concerns. The enlarged preview is nearest-neighbor4× diagnostic and looks pixelated; don't confuse zoomed raster with a production high-resolution illustration.

One art candidate only. `candidate-01/` preserves first diagnostics; `final-preparation/` adds scaled timing/path contact sheets and corrected metadata, **butterfly PNG bytes identical**, not a new visual refinement variant.

Imagegen skill was read but remote/image-generation workflow not invoked: direct user local-only/no remote/paid constraints take precedence. Local manually authored raster/path preparation used; no child image sent anywhere.

## 4. Paths, phases, masks and pen transitions for18 actions

[Prepared18-action timeline](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/draw-action-timeline.prepared.json): original draft retained, stable action/beat IDs and windows unchanged; filled path_ids, mask_ref+SHA and asset hashes, actual computed timing estimates. It is **executable:false**, asset pending, nominal windows infeasible. `budgets_unverified:true` because assumptions/cues/naturalness not owner-validated even though path travel is calculated.

[Stroke/brush path contact sheet](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/stroke-brush-path-contact-sheet.png)
and [phase coverage contact sheet](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/phase-coverage-contact-sheet.png).

Each object folder contains:
- `paths.json`: actual phase points/widths, object/source coordinate origin and presentation scale.
- `outline/detail/color-phase-mask.png`: allowed actual pixel coverage for each phase.
- `outline/detail/color-coverage.png`: static white-composited selected RGB pixels.
- `outline/detail/color-path-preview.png`: source backdrop plus colored diagnostic path lines. Full source backdrop is for path inspection, **not early-color rendering**.
- `outline/detail/color-pen-transitions.json`: every pen-up origin/destination, native down/up lengths and down start/end under fixed assumptions. These support future actual tip-following executor; no moving tip/video was implemented.

For sources, unchanged existing `LocalObjectAwareStrokeEngine(strategy="pencil")` re-extracted verified cropped registry assets, using mask-bounded contour/detail traces and texture-aware source-color hatches. Full original master masks are not mutated. New butterfly uses locally authored paths instead of being disguised as a source object.

**Phase difference from old renderer:** old outline/detail brush could reveal sourceRGBA/colors directly. Preparation creates distinct phase masks; OUTLINE/DETAIL only selected neutral dark source pixels (maxRGB≤165 and max-min≤70) intersect path coverage/source alpha; COLOR alone can reveal all existing source RGB. No recoloring, blanket opacity fade, rectangular object mask/reveal or whole-region pop. Phase masks may overlap ink in COLOR to restore original shade, but DETAIL excludes already assigned OUTLINE pixels.

This is conservative **heuristic** not semantic ink separation. Colored borders/hair highlights are deferred to COLOR; some gray clothing/dark fills get classified candidate ink. No automatic statement every selected/missing pixel is an important structural feature. Need manual semantic/path review before these prepared masks are used in video.

Geometry checks:1086paths,225zero-length coverage/isolated-dot paths;down travel41518.704px,pen-up travel23545.708px in native path coordinates across phase records. Same-source colors are sampled through paths and clipped to masks; brush centers/source containment and zero gaps tested. Complete COLOR source coverage is100% for each of six objects; actual saved color-coverage RGB matches original cutout/new asset inside covered masks. This is **static coverage proof**, not progressive naturalness or encoded video proof.

### Structural phase findings from actual PNG review

- Father/mother/child ink previews are sparse fragments: silhouette, face/clothes are not already readable continuous drawings before color.
- House structural outline is particularly weak; many roof/window edges appear only in color.
- Garden has only33OUTLINE-selected pixels and384DETAIL pixels; original colorful flowers/grass edges are largely deferred.
- Source neutral-dark pixels not reached by ink paths: father3172, mother901, child714, house1033, garden605. Selected neutral-dark pixels include dark fills/shading, so these are **coverage diagnostics**, not a count of semantic details irretrievably lost; all original pixels are retained by COLOR.
- Source paths retain isolated dots: garden115zero-length paths overall, father49. Such segments explain why min-visible-frame timings are large and accelerated versions look scattered.
- Butterfly has recognizable authored outline/detail but108candidate neutral-dark pixels outside ink reach, partly filled body/grain; no claim exact ink-role segmentation.
- Color trajectories remain mostly alternating hatch runs. More coherent than a full-region reveal but **not yet proven natural pencil coloring** without actual video.

Consequently structural phase readiness is NEEDS_SOURCE_INK_AND_PATH_REVIEW, VisualQA NOT_PASSED. Keeping source fidelity by COLOR doesn't repair missing understandable ink drawing. No threshold tuning loop attempted, no old engine overwritten.

## 5. Timing feasibility — calculated, not actual video/audio measurement

[Full per-object/per-phase report](D:/Codex/Sketch2Life/whiteboard_slice_step_a_2026-10-09/final-preparation/object-timing-feasibility.json).

Declared native-pixel pacing:24FPS;ink180px/s,color300px/s,pen-up600px/s;each down path at least4frames,each pen lift at least2frames. These fixed values are **reviewable engineering assumptions, not user-approved or measured natural human speed**. They are not adjusted to force15s. Measurements of path counts/lengths are real; animation time is derived.

| Object | Outline estimate | Detail estimate | Color estimate | Total native estimate | Rev22 object slot |
| --- | ---: | ---: | ---: | ---: | ---: |
| Father | 6.05s | 31.85s | 19.56s | 57.46s | 2s |
| Mother | 7.56s | 19.85s | 34.44s | 61.85s | 2s |
| Child | 4.09s | 7.39s | 12.49s | 23.97s | 2s |
| House | 4.11s | 28.70s | 30.05s | 62.87s | 2.5s |
| Garden | 5.84s | 93.48s | 49.41s | 148.73s | 2.5s |
| New butterfly | 3.62s | 1.81s | 14.95s | 20.37s | 3s |

Total **375.243s native**. Butterfly actual placement scale0.60 reduces only travel-dependent terms;visible-frame/lift minima still apply: butterfly17.633s;whole proposed sequence **372.503s**, before inter-object pen travel/camera holds. This is a sum for **the current complete unsimplified path sequence under these assumptions**, not a universal minimum for any artist/VideoScribe technique. Many paths do not expose usable structural ink; future explicitly reviewed path authoring may change these counts, so don't claim372s is inevitable for the product.

All18nominal phase windows fail these pacing estimates. For example gardenDETAIL would require≈234×compression; that is unacceptable as natural drawing. No increase in speed, ignored lift/visibility or deleted butterfly used to pass.

No audio/render timing measured: actual 15s narration duration unknown. Current stage explicitly stops before MP4.

### Scope/time options requiring owner approval

**A — Preserve all18actions as currently traced:** approximately **373s + hold/camera/cross-object travel**. Not recommended merely extending this short story to six minutes; structural failures remain even if slowed. It demonstrates current raster path inefficiency, not an acceptable final storyteller.

**B — Smaller diagnostic retaining mandatory new butterfly:** child + butterfly only, modified local script e.g. “Đây là em. Một con bướm nhỏ hiện ra.” Under current paths ≈**41.61s + hold/travel**, suggest a45–50s local diagnostic slot only if approved. No father/mother/house/garden drawn; new content/script/canvas review required. This still needs structural ink/path repair; cannot claim15s, and this isn't the full3–6scene40–60s product story.

**C — Keep10–15s goal:** narrow to a reviewed small flower/leaf source ROI plus new butterfly and obtain coherent authored source-bound structural/color paths; current butterfly alone17.63s at placement scale under assumptions, so even this requires reducing path lifts/authoring better trajectories after approval, **not speed tuning**. Flower ROI mask/paths aren't yet reviewed/measured; no invented exact duration estimate. Rendering blocked until art/path/time review. Do not pretend using smaller objects automatically solves15s.

No option is auto-selected or executed. Recommended next decision: approve/reject butterfly appearance, then authorize a specifically scoped structural/path authoring fix and choose full source versus narrowed slice. No new architecture or production work needed.

## 6. Resource/performance observations

Final diagnostic run (not rendering):wall **2.523243s**,Python tracemalloc peak **6,041,658bytes (~5.76MiB)**. Not processRSS/C-native allocation/GPU VRAM. ProcessRSS not measured. Existing resource limits preserved:per object4096paths,max phase200000points,≤1920×1080pixels/maxedge2048,120s preparation budget. Render workload/budget not measured because no MP4.

Pen trajectories carry explicit up/down intervals; optional debug tip can use same paths and timeline later. These preparation tables are not proof of correct dynamic camera/pen synchronization.

## 7. Actual tests/checks

Command:
```text
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_whiteboard_slice_feasibility.py backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py backend/tests/unit/test_whiteboard_v2_engine.py backend/tests/unit/test_whiteboard_v2_schedule_debug.py backend/tests/contract/test_story_video_file_api.py
```

**132PASS,0FAIL,84.98s,exit0**. New23tests +109existing selected V1/V2/world/multidrawing/planner/API tests. Initial23-only alsoPASS0.48s. No skips/deselects inside selection. No repository-wide PASS claim; VisionV3/Lightning/GPU/audio/actual slice video/productionGate tests not run or changed.

Ruff three newPython files PASS after import ordering and redundant cast fixes. Mypy `--follow-imports=silent` **new feasibility module only**,PASS1file;not tools/all backend. Final security PASS1676publishablefiles, whitespace PASS,zero broken report links. Tiny prepared-metadata correction does not change paths/art/pacing;new23tests rerun PASS0.38s. Artifact SHA manifest mismatch0;all18actions have nonempty path IDs and existing phase masks, executable remainsfalse.

## 8. Files changed in this task

New isolated implementation:
1. `backend/src/sketch2life/infrastructure/media/whiteboard_slice_feasibility.py` — phase coverage separation, safety guards, explicit pacing/pen-travel diagnostics;no production renderer.
2. `tools/prepare_whiteboard_slice_step_a.py` — local artwork recipe,source/mask hash verification,18-action binding,PNG/JSON diagnostics and private manifests;no network/encoder.
3. `backend/tests/unit/test_whiteboard_slice_feasibility.py` —23tests;synthetic data only.

Updated6feature records: approvals/TASK_APPROVAL.md,plan/PLAN.md,CONTEXT.md,DECISIONS.md,status/STATUS.md,evidence/README.md.
New evidence report: `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_WHITEBOARD_SLICE_STEP_A_RESULT.md`;private root copy.

Existing source engine/renderer/world/model/V1/tests/rig unmodified. No pipeline integration, endpoint or flag change. Original Rev22 draftJSON remains empty-path historical proposal; preparedJSON is separately bound diagnostics,not falsely approved executable timeline. Private source-bearing artifacts stay outside Git.

## 9. Blockers before render and stop condition

1. Butterfly artwork/style/placement pending owner review, exact PNG/path hash must bind subsequent approval.
2. Source ink masks/path sequence too sparse/discontinuous;colored contours deferred;need focused semantic/path authoring review, no auto-loop.
3. Current18phase windows are infeasible;owner chooses scope/duration, cannot replace new butterfly with focus-only pass.
4. Pacing assumptions uncalibrated;actual visual naturalness only inspectable after authorized bounded video,not tests/PNGcoverage.
5. Source-derived artifacts kept local,in-memory registry stillprototype;no Lightning/durable/runtime acceptance.
6. Audio/TTS prohibited at StepA;future real cues require permitted measured audio,not fixed15s division.

**Dừng ở candidate/feasibility artifacts. Không clean/debug/full slice MP4 nào được tạo. Chờ duyệt artwork và scope/time trước execution tiếp theo.**
