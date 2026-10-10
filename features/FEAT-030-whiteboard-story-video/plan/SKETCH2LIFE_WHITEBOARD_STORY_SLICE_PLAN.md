# SKETCH2LIFE — WHITEBOARD STORY SLICE PLAN

2026-10-09 · FEAT-030 revision22 · PLAN_READY / AWAITING_OWNER_REVIEW

## 1. Ưu tiên sản phẩm và trạng thái

Main direction: **Narration -> Story Beats -> Draw Actions -> Scene State -> MP4**. Vẽ và phát triển nội dung theo lời kể; không render toàn bộ tranh trước rồi bắt mọi story phụ thuộc walk cycle. VideoScribe là tham chiếu trải nghiệm người dùng yêu cầu, không claim dùng phần mềm/API/code VideoScribe hoặc chất lượng đã tương đương.

Giữ Whiteboard Engine V2, World Model/Asset Registry và các rig/motion experiments. Không xóa/viết lại/bật main pipeline từ Motion Proof. Rig chỉ enhancement; butterfly flutter, arm/head emphasis hoặc nhẹ movement cần nội dung/artwork/phạm vi được duyệt riêng.

**Revision22 thay thế lựa chọn slice revision21**: bắt buộc có new-object drawing, không được chỉ dùng garden focus để đáp ứng tiêu chí. Con bướm được chọn, dựa trên nội dung Golden local đã duyệt nhưng exact script15s, artwork và cue timing vẫn cần review. Không dùng câu đã duyệt để tự duyệt hình bướm.

Lượt này chỉ tài liệu và storyboard source-derived static preview; không application-code edit/MP4/audio/model inference. Không Golden55s, commit/push/deploy/GPU/remote upload. V1 default, V2 flagOFF và Gate A/B production không đổi.

Git kiểm tra trước cập nhật: HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`, branch `codex/feat-018-contract-plan`, index trống, nhiều dirty/untracked files có từ trước. Không stage/reset/ghi đè code/drafts/media. Những files đó không tự coi là revision22 tạo.

## 2. Inputs, consent và approval

Source family1.jpg = alias original familly.jpg đã xác nhận,594×336RGBJPEG, SHA `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`.

- [Source +9master masks/identity manifest](D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/source-object-manifest.json).
- [Existing World Model](D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/benchmark-world.json).
- [Prior slice plan revision21, superseded for new-object criterion](SKETCH2LIFE_WHITEBOARD_STORYTELLING_SLICE_PLAN.md).
- [Motion proof findings, retained NOT_PASSED](../evidence/SKETCH2LIFE_MILESTONE3B_MOTION_PROOF_RESULT.md).

Master masks/source/cutouts bất biến. Reuse parent stable IDs; no diffusion/regeneration. New butterfly gets stable candidate ID `local-new-butterfly-01`, never masquerades as SOURCE_DRAWING. Provenance links exact quote, local-demo content approval evidence and source-derived StyleProfile. Artwork/hash/draw paths approval is independent.

Latest request authorizes this plan/preview only. Script below is proposed shortened demo, not child's transcript/voice or server Gate A/B approval. Exact text and timeline hashes bind local review; changes invalidate corresponding local approval. Caller review_ref isn't server trust. No fake approved fact/anchor/event IDs: draft JSON keeps empty IDs and server NOT_VERIFIED.

## 3. Exact script proposed for owner approval

> Đây là bố, mẹ và em trước ngôi nhà. Bên cạnh là vườn hoa. Một con bướm nhỏ hiện ra trên những bông hoa.

Source observations: family, house, garden. **Added content:** butterfly appearance, from approved local Golden concept, not visible in original. No claim child walks, releases hands or returns in this slice. Butterfly flutter omitted from exact sentence and default execution; may be proposed later with explicit motion approval, not necessary for this slice.

Mode: **SIMULATED_CUES_ONLY**, silent MP4 with cue text/times after approval. External EdgeTTS still not authorized; no audio exists or has been measured for this script. Fifteen seconds below is a designed simulated timeline, not actual spoken duration. Do not use another clip/voice or equally divide audio to claim verified speech sync.

When audio is permitted: validate exact script/audio hash, probe actual duration and annotate/import phrase onset/offset from local listening, store cue evidence. Recompile windows around those real cues. If narration doesn't fit10–15s, report infeasibility or seek approved script/window adjustment; no silent trim/stretch of speech.

## 4. Beat timeline — one continuous canvas, proposed15s

| Beat ID | Simulated window | Text / event mapping | Objects and scene state | Camera / optional motion |
| --- | --- | --- | --- | --- |
| family-01 | 0–6s | “Đây là bố, mẹ và em” — first quote span of segment01 | source father→mother→child, original position/pose; outline→detail→color each; persist completed objects | full-board framing, no rig |
| house-02 | 6–8.5s | “trước ngôi nhà.” — remaining quote span segment01 | source house drawn after family; family retained | full board, no camera reset |
| garden-03 | 8.5–11s | “Bên cạnh là vườn hoa.” — segment02 | source garden drawn; family+house retained | same coordinates, focus prepares toward garden |
| butterfly-04 | 11–14s | “Một con bướm nhỏ hiện ra trên những bông hoa.” — segment03 | **new butterfly drawn**, only after art/path review; all old objects stay | slight eased pan/zoom toward flower/butterfly; no fade |
| focus-05 | 14–15s | hold of previous quote; no extra narration/event | retain canvas/progress; no full redraw | hold gentle focus, family remains recognisable; optional motion OFF |

Exact stable beat IDs, segment refs, source status and simulated cues are in [beat-timeline.draft.json](D:/Codex/Sketch2Life/whiteboard_story_slice_review_2026-10-09/beat-timeline.draft.json).

Existing source object IDs: `family-52caf90a-{father,mother,child,house,garden}`. Garden mask represents flower+grass region, not individually segmented flowers. Tree/sky/path/background keep registry identity but remain undrawn whiteboard in this partial slice, not substituted/restored background. Do not claim frame matches whole original when only these objects complete.

## 5. Draw-action timeline and stroke semantics

[draw-action-timeline.draft.json](D:/Codex/Sketch2Life/whiteboard_story_slice_review_2026-10-09/draw-action-timeline.draft.json) contains18 phase tasks with stable IDs, beat binding/dependencies, new-asset block and camera proposal.

| Object | OUTLINE | DETAIL | COLOR | Persist after |
| --- | --- | --- | --- | --- |
| Father | 0–0.75 | 0.75–1.20 | 1.20–2.00 | 2.00 |
| Mother | 2.00–2.75 | 2.75–3.20 | 3.20–4.00 | 4.00 |
| Child | 4.00–4.75 | 4.75–5.20 | 5.20–6.00 | 6.00 |
| House | 6.00–6.90 | 6.90–7.30 | 7.30–8.50 | 8.50 |
| Garden | 8.50–9.40 | 9.40–9.80 | 9.80–11.00 | 11.00 |
| New butterfly | 11.00–12.10 | 12.10–12.50 | 12.50–14.00 | 14.00 |

These are **UNVERIFIED phase budgets**, including explicit pen-up travel to allocate within feasibility. They are not recovered source stroke order or measured spoken windows. Path IDs/phase masks are intentionally unresolved, not fake ready schedules.

Each draw action will contain object/assetID, source or NEW provenance, stroke IDs/arc-length progress, phase coverage mask, dependencies, source/mask/asset hashes, authorized window, explicit interleave reason if used. Color starts only after outline/detail prerequisite; no structural mask leakage revealing crayon color prematurely. Original RGB is retained; texture revealed by localized source-masked brush trajectories, not full-image/region opacity. Structural paths cannot replace original people with geometric art.

Feasibility must check total path travel, pen lifts, visible per-frame progress and color coverage under existing stroke/time/memory budgets. These source objects are complex: two seconds/object may be insufficient. If so, return DRAW_TIMING_INFEASIBLE/NEEDS_STROKE_REVIEW with object/phase evidence and seek approved smaller focus/script/layout, not automated speed/threshold/feature removal. **Do not omit butterfly and claim acceptance via camera focus.**

## 6. Storyboard preview and new asset gate

[Open storyboard-preview.html](D:/Codex/Sketch2Life/whiteboard_story_slice_review_2026-10-09/storyboard-preview.html).

Four target-state panels use **actual original source cutouts**: family; family+house; +garden; +butterfly location annotation. Existing cutouts are full-canvas594×336, so identities/layout preserved.

**Honest limit:** butterfly is a labeled placement placeholder, not generated or approved artwork; last panel does not contain a final butterfly image. Preview is static composition, not MP4/drawing/phase naturalness/camera execution proof. It uses local file references and must stay local; no remote resources. Placeholder box is annotation only, never segmentation mask or production drawable.

Before rendering butterfly: owner supplies art or approves a local/manual candidate-preparation task; artist makes source-style uneven child-art contours/body/wings/color layers with paths and native palette, records new pixels/art provenance, then owner reviews image/path placement. Generic diagram symbol or flat-vector substitute cannot be called source-style PASS. Content approval isn't artwork approval. No image generation service/GPU inference needed or authorized now.

## 7. Pipeline contracts and minimal modules

1. **Narration input:** exact demo text + local approval binding; optional permitted audio/hash and real cues. No automatic story expansion.
2. **Story Beats:** explicit quote spans mapped to stable source/new IDs/events/facts/anchors. Local demo versus server approval distinct.
3. **Draw Actions:** compile approved beat windows into source-bound ordered paths/phases/pen-up/camera tasks; fail-closed on absent art/invalid cues/infeasible natural-speed budget.
4. **Scene State:** single persistent canvasID/progress/layers across beats, checkpoints at cue boundaries. Camera affects presentation, not identity or draw clock. Draw-more by adding tasks; partial erase/redraw only explicit approved path/region later; no wipe every beat.
5. **MP4:** local encoded clean +debug view using same timebase, cue label/subtitle timeline, contact sheet and actual-frame audit. Not production READY and not full3–6scene40–60s story.

| Actual module | Reuse / change after approval |
| --- | --- |
| `application/services/story_world_model.py` — SourceAssetRegistry | Keep source IDs/pixels/masks unchanged; add isolated reviewed-new-asset resolver contract/adapter, not import fictional source identity. Existing missing/invalid mask/asset failures retained. |
| `contracts/schemas/story_strokes_v2.py` | Preserve existing contract; add `story_narration_draw_timeline_v2.py` versioned beat/action/canvas/new-asset contracts. Include local approval vs NOT_VERIFIED Gate status and exact text/hash mapping. |
| `application/services/story_draw_schedule_v2.py` | Existing builder uses length/phase budgets and all strokes get first segment beat_ref; rejects new objects. Keep legacy validator every-path requirement, add `narration_draw_timeline_v2.py` compiler for explicit beat/subset windows/dependencies/persistent state, don't weaken old guard. |
| `infrastructure/media/object_stroke_engine_v2.py` | Reuse complexity-aware extraction; source masks and structural-vs-texture paths remain relevant. Only bounded fixes justified by phase/path evidence; naturalness still NOT_PASSED. Butterfly uses reviewed authored paths, not source extraction claim. |
| `infrastructure/media/whiteboard_renderer_v2.py` | Add opt-in timeline entrypoint on existing V2 primitives. Current OUTLINE/DETAIL brush reveals sourceRGBA too: separate source-derived structural-ink coverage from COLOR texture coverage. Current pilot rejects new objects: add explicit approved-asset path, no guard removal/fallback. |
| `infrastructure/media/scene_state_composer.py` | Reuse canonical placement/source guards; don't use target-state still as motion proof. Persistent draw state executor and time-varying eased camera needed; existing camera is per-scene static. |
| New `whiteboard_story_canvas_v2.py` adapter | Local-only persistent layer/reveal state, unified absolute cue time, camera/pen same transform. Unsupported erase/transition/motion must fail clearly, not pretend implemented. |
| New `tools/story_whiteboard_story_slice.py` + dedicated tests | Explicit local permissions/input hashes, dry-run feasibility, one10–15s clean/debug render +actual contact sheet/coverage/cue audit. No HTTP/upload/jobs changes. |
| Existing V1 TTS/planner/subtitle/assembly | Read/reuse encode/text mechanics via local adapter; no V1 change/Edge call. V1 cue division evenly inside segment isn't actual phrase timing. Real audio integration deferred until data/voice permission and measured cues. |
| `limited_character_rig_v2.py` + `story_character_motion_proof.py` | **No changes**; optional experiment, not required import or acceptance gate for main whiteboard slice. |

Proposed new contracts/actions/modules above are **NOT implemented**. Full Story V2 duration3–6scenes5–20s/scene40–60s remains intact. This one-canvas diagnostic15s is not forced through production story acceptance or advertised as full Golden.

Pan/zoom/draw-more is scope priority. Page transition/partial erase have architecture hooks only here; not required or silently substituted into first slice. Same location needs continuity, not frequent wipe/cut. Slight butterfly movement may come later, no complete walk cycle required.

## 8. Acceptance criteria after implementation approval

- Exact script/cues approved for local demo; no unauthorized content or new asset. Butterfly needs content AND artwork/path hashes approved.
- Clip duration10–15s with explicit simulated status; later real audio uses measured duration +true phrase cues. Silence/text timeline never claimed as audio sync.
- Every spoken/text beat maps to intended object/action/phase/camera; no source/new color or ink before authorized beat.
- **At least one genuinely new butterfly is progressively drawn** in its beat, not a placeholder/fade/full-region pop; source objects retain identity, placement, RGB and texture.
- Natural continuous paths, pen-up/down and credible progress at actual fps; color travels within allowed mask, no broad block/final snap/unexplained pixels.
- One scene remains persistent: previous figures are not wiped or redrawn per beat. At least one soft focus pan/zoom executed with easing and pen/canvas consistent coordinates.
- Final authorized source regions preserve canonical original pixels and coverage; compare camera/codec effects separately. No whole-original fidelity claim for partial canvas/new butterfly.
- MP4 actual decode, contact sheet with exact quote/beat/object/phase/time at cue boundaries +0/25/50/75/100%, debug path trace, source/new manifests, final frame/diff and resource/timing evidence.
- Tests for text/hash approval, new asset rejection, phase ordering, no early reveal, partial coverage/state continuity, invalid/unsupported actions, camera/pen consistency and infeasible budget; related V1/V2 regressions/Ruff/Mypy/security scoped.
- Visual QA requires actual video review. If raster reconstruction still looks scattered/blocky, report VISUAL_QA_NOT_PASSED and specific limitation; no infinite parameter loops. Tests alone cannot pass VideoScribe-like naturalness.

## 9. Execution gates and deliverables

**Now:** plan +beat JSON +draw-action JSON +static HTML preview only. No MP4 generated.

**After owner review:** exact script/window/source layout and local permission binding → butterfly artwork/path candidate preparation/review → dry-run feasibility → bounded local slice implementation/test → one clean/debug MP4 → owner visual review. Rendering blocked while butterfly art is missing/unapproved. Do not silently fall back to revision21 focus-only variant.

Outputs remain outside Git, planned `D:/Codex/Sketch2Life/whiteboard_story_slice_review_2026-10-09/`; current review JSON/HTML are already here. Real child/source preview/media never copied into publishable repository. Repo contains only plan/governance docs, not private cutout data.

Pending: approval of exact script, 15s simulated budget, draw order, butterfly visual design/placement, scoped implementation and later audio permission. No Golden55s, no fees/network/training or production changes.

Planning checks: 327 existing Python files unchanged, no new Python; original source/9mask/9cutout hashes match; index empty. Whitespace and repository security PASS (1,672 publishable files scanned); plan links valid. Draft JSON/HTML validation: 5 beats,18 non-overlapping phase tasks,17 valid local image references. This validates static preview structure, not browser appearance, audio sync or renderer execution. No new pytest suite run because no application code changed.

**Status: PLAN_READY / AWAITING_OWNER_REVIEW. VISUAL_QA_NOT_PASSED; no implemented slice acceptance implied.**
