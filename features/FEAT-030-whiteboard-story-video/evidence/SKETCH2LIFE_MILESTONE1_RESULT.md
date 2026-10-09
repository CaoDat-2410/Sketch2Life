# Sketch2Life — Milestone 1 implementation result

Date: 2026-10-09. Scope: **Level-1 local prototype only**. No GPU/model inference, paid API, real child drawing, MP4, commit, push or deploy. Level-2 LightningAI acceptance is **NOT RUN / NOT PASS**.

## Baseline and plan

- Inspected revision before edits: `c80ef1f6b6d7d33da54eb26a9ad036283aa381fb`, branch `codex/feat-018-contract-plan` (ahead of origin by four).
- Already modified before this task: `backend/src/sketch2life/infrastructure/media/whiteboard_stroke_extraction.py`, `backend/tests/unit/test_whiteboard_mvp_renderer.py`, `backend/tests/unit/test_whiteboard_stroke_extraction.py`; `assets/` already untracked. **None of these were edited by this milestone.**
- Read both exact reports: `D:/Codex/Sketch2Life/SKETCH2LIFE_FULL_WHITEBOARD_AUDIT.md` and `D:/Codex/Sketch2Life/IMAGE_TO_IMAGE_REVIEW.md`.
- Before code edits, recorded revision-8 plan and owner approval in `plan/PLAN.md` and `approvals/TASK_APPROVAL.md`. The existing V1 story job and Gate A/B behavior were not changed.

## A. What was implemented

1. New independent `StoryWorldModelV2` and `StoryScenePlanV2` contracts. Original objects use `SOURCE_DRAWING`; narration additions use `APPROVED_NARRATION`, initially `PENDING`. Event manifests have stable IDs, exact script quote, mapping rule, segment/fact/anchor references and a separate review reference. This is a **reviewed fixture contract**, not a server-authenticated adult-approval service.
2. Manual-mask source registry verifies original-image SHA-256, decodes same-size nonempty binary masks, requires an identity-review reference, rejects unusual >5% overlap of the smaller region, and produces lossless cropped RGBA assets with mask/asset hashes. Missing/invalid mask or ambiguous identity -> `NEEDS_MASK_REVIEW`; no bounding-box substitute or model call. Assets are process-local in this prototype.
3. V2 planner uses explicit reviewed event boundaries plus measured narration lengths. It emits 3–6 scenes, each 5–20 seconds, 40–60 seconds total; otherwise `DURATION_OUT_OF_RANGE` or `SCENE_PARTITION_IMPOSSIBLE` with reason. Start and target states are continuous, with stable object IDs, simple transform/camera intent and provenance. It does **not** invent events from narration text.
4. Pillow scene-state composer renders still images from the original RGBA cutouts; it supports visible source objects, translation, scaling, limited rotation and camera crop/pan/zoom. New pending assets, walking/running and other unsupported actions fail with `UNSUPPORTED_ACTION`; there is no silent V1 fallback.
5. `SKETCH2LIFE_STORY_RENDER_V2_ENABLED` defaults false. Only explicit `StoryVideoPipeline.run_v2_prototype(...)` uses V2. Existing `.run()` remains the V1 media job, including when the flag is enabled. No HTTP V2 endpoint or production deployment was added; the local prototype caller must separately enforce live session/Gate checks before any future exposure. V1 import does not load optional Pillow.
6. A deterministic synthetic family/house/tree/garden fixture has four reviewed event segments; a butterfly is an approved-text **pending** object, not a fabricated generated asset. A two-scene contact sheet tests stable source assets and a positional change. It is intentionally primitive artwork and not visual-fidelity acceptance.

## B. Exactly 17 text/source files changed by this milestone

Paths are repository-relative. The separate generated binary contact sheet is item **18**, not counted among the 17 source/text files. The three pre-existing edited whiteboard files and four pre-existing untracked `assets/generated/` hand files are **not** milestone changes.

| # | File | Function in Milestone 1 |
|---:|---|---|
| 1 | `backend/src/sketch2life/contracts/schemas/story_world_v2.py` | Versioned event, object, world and scene/state contracts; continuity validators |
| 2 | `backend/src/sketch2life/application/services/story_world_errors.py` | Typed errors without importing optional Pillow into V1 |
| 3 | `backend/src/sketch2life/application/services/story_world_model.py` | Mask registry, source hash checks, lossless RGBA cutouts, provenance validation |
| 4 | `backend/src/sketch2life/application/services/story_video_planner.py` | `compile_v2` event-aware partition and continuous state; V1 `compile` preserved |
| 5 | `backend/src/sketch2life/infrastructure/media/scene_state_composer.py` | Still-image composite from source cutouts; simple transform/camera; explicit unsupported action |
| 6 | `backend/src/sketch2life/application/services/story_video_pipeline.py` | Explicit flag-gated `run_v2_prototype`; V1 `.run()` remains media path |
| 7 | `backend/src/sketch2life/infrastructure/config/settings.py` | Default-OFF V2 prototype flag |
| 8 | `backend/src/sketch2life/interfaces/http/app.py` | Passes flag when constructing existing Lightning-dev pipeline; no V2 HTTP route |
| 9 | `backend/tests/unit/test_story_world_v2.py` | 12 local synthetic tests, positive and fail-closed cases |
| 10 | `tools/story_world_v2_fixture.py` | Deterministic one-image family fixture and contact-sheet generator |
| 11 | `features/FEAT-030-whiteboard-story-video/plan/PLAN.md` | Revision-8 scope and two-level acceptance plan |
| 12 | `features/FEAT-030-whiteboard-story-video/approvals/TASK_APPROVAL.md` | Owner approval record before this milestone's code edits |
| 13 | `features/FEAT-030-whiteboard-story-video/CONTEXT.md` | Feature context for isolated V2 prototype |
| 14 | `features/FEAT-030-whiteboard-story-video/DECISIONS.md` | Decision to keep V1/Gate semantics and defer live provider |
| 15 | `features/FEAT-030-whiteboard-story-video/status/STATUS.md` | Level-1 status and Level-2 exclusion |
| 16 | `features/FEAT-030-whiteboard-story-video/evidence/README.md` | Evidence index E-047 |
| 17 | `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE1_RESULT.md` | This review report |

Generated binary artifact: `features/FEAT-030-whiteboard-story-video/evidence/milestone1-v2-contact-sheet.png`. The later `D:/Codex/Sketch2Life/milestone1_review/` directory is a **review export**, not additional product code.

No edit to `story_video_media.py`, `lightning_story_video.py` or provider was needed for a **local-only** prototype; adding transport/runtime contracts now would imply an untested Level-2 integration. No original V1 schema was modified, so its existing serialized hashes stay intact.

### Actual V2 path today

`run_v2_prototype` called explicitly with package + exact approved script segments + original image bytes + manually reviewed mask specs + reviewed event manifest + measured durations -> package/script/source hashes checked -> `build_source_asset_registry` verifies masks/provenance and returns process-local original cutouts -> `compile_v2` creates four continuous scene states in the fixture -> `SceneStateComposer.render_scene` can render still PNGs for supported scenes. The existing job route never invokes this path. `StoryVideoPipeline.run` still performs the old V1 TTS/img2img/scene/MP4 flow regardless of the V2 flag. No V2 MP4, provider call, replayable persisted registry or server-side adult event verification exists.

## C. Contract examples

Complete `ReviewedEventV2` instance from the synthetic fixture (the review reference is a fixture marker, **not** proof of real adult approval):

```json
{
  "event_id": "event-walk",
  "segment_id": "segment-2",
  "approved_fact_ids": ["fact-2"],
  "confirmed_anchor_ids": ["anchor-2"],
  "source_quote": "Gia đình đi dạo trước nhà.",
  "mapping_rule": "EXPLICIT_REVIEWED_EVENT",
  "approval_status": "APPROVED",
  "review_ref": "fixture:adult-review-v1",
  "object_ids": ["mother", "father", "child"],
  "action": "TRANSLATE",
  "target_positions": {"mother": [0.18, 0.62], "father": [0.37, 0.59], "child": [0.28, 0.65]},
  "target_scales": {},
  "target_rotations": {},
  "camera_intent": "PAN",
  "transition_intent": "CONTINUE"
}
```

Selected fields from the four-scene plan:

```json
{
  "contract": "StoryScenePlanV2",
  "version": "2.0",
  "duration_seconds": 40.0,
  "scenes": [
    {
      "scene_id": "scene-2",
      "event_ids": ["event-walk"],
      "segment_ids": ["segment-2"],
      "source_object_ids": ["mother", "child", "father", "house", "tree", "flowers"],
      "new_object_ids": [],
      "action": "TRANSLATE",
      "duration_seconds": 10.0
    }
  ]
}
```

This is an **excerpt**, not a complete schema-valid plan: full output also includes package hash, all four scenes, start/target states, draw order, camera and transition. The fixture's butterfly belongs to `APPROVED_NARRATION` with `asset_status=PENDING`; scene 3 is planned but cannot be rendered by the composer until an asset is separately generated/reviewed.

## D. Verification and artifact

- New V2 unit test file: **12 passed** (synthetic only), including flag-ON `.run()` still taking the V1 path.
- Focused V2 + V1 story planner/media/demo/job/file contract command below: **65 passed in 54.17 s, 0 failed**. This includes the 12 V2 tests and verifies V1 behavior within those test modules.
- Broad backend unit/contract run with four Vision V3 suites excluded: **1,670 passed, 5 skipped, 86 deselected, 0 failed in 175.53 s, exit 0**. A first broader run with only two suites excluded had **9 failures** in unrelated Vision V3 quality benchmark/execution tests: their fixture manifest refers to `images/v3q-fixture-01.png`, which is absent from the inspected repository. The failures were not fixed, hidden or attributed to this milestone.
- Ruff: passed on all touched Python files. Mypy `--follow-imports=silent`: passed on six V2/V1 source modules. `git diff --check`: passed. Repository security validator: `REPOSITORY_SECURITY_VALID`. Separate import check: `Pillow loaded by V1 import: False`.
- Test command for the passing broad run:

```text
backend/.venv/Scripts/python.exe -m pytest -q backend/tests/unit backend/tests/contract -k 'not vision_v3_quality_fixtures and not vision_v3_mapping_fixtures and not vision_v3_quality_benchmark and not vision_v3_quality_execution'
```

The exact-count rerun additionally used `-o addopts= -q` before the paths. The repository config itself adds `-q`, which is why the earlier quiet run printed progress without a count. The four deselected name groups are `vision_v3_quality_fixtures`, `vision_v3_mapping_fixtures`, `vision_v3_quality_benchmark`, and `vision_v3_quality_execution`; the 5 skipped tests are reported by pytest, not presented as passes.

Focused command re-run for an exact count (overrides the repository's extra quiet setting):

```text
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_story_video_media_smoke.py backend/tests/unit/test_story_video_demo.py backend/tests/unit/test_story_video_job_input_gate.py backend/tests/contract/test_story_video_file_api.py
```

The initial broad command used `-k 'not vision_v3_quality_fixtures and not vision_v3_mapping_fixtures'`; it reached the Vision V3 quality benchmark/execution tests and produced 9 failures when `_require_relative_file` could not find `features/FEAT-003-multimodal-understanding/fixtures/vision-v3-quality/images/v3q-fixture-01.png`. An explicit `Test-Path` for that file returned `False`. These are not newly fixed or asserted to be caused by V2. The passing rerun additionally excluded `vision_v3_quality_benchmark` and `vision_v3_quality_execution`. No GPU, paid inference, child-media, LightningAI or full V2 MP4 test was run.

- Contact sheet: `evidence/milestone1-v2-contact-sheet.png`, SHA-256 `EFD4801B97BA00F30D40A3108965FFC32F0C1C57537584EC68B563A0CEC8CD59`. It shows scene 1 source object IDs and scene 2 the same source cutouts repositioned. It is not evidence of child-image fidelity or true whiteboard animation.

### Review artifact directory

The originals remain in the repository. A copy plus fully materialized synthetic exports lives at `D:/Codex/Sketch2Life/milestone1_review/`. Its `artifact-manifest.json` contains **29 SHA-256 entries**; independent verification reported **29 files, 0 hash mismatches**. Key files:

| Artifact | Full path or directory under `D:/Codex/Sketch2Life/milestone1_review/` |
|---|---|
| Report copy and prior audits | `SKETCH2LIFE_MILESTONE1_RESULT.md`, `SKETCH2LIFE_FULL_WHITEBOARD_AUDIT.md`, `IMAGE_TO_IMAGE_REVIEW.md` |
| Two-scene contact sheet | `milestone1-v2-contact-sheet.png` |
| Fixture source code | `story_world_v2_fixture.py` (original: repo `tools/story_world_v2_fixture.py`) |
| Synthetic source drawing | `synthetic-input.png` |
| Approved-package/script/event fixture | `approved-package.synthetic.json`, `story-script-segments.synthetic.json`, `reviewed-events.synthetic.json` |
| Full world/state JSON | `world-model.synthetic.json` |
| Full four-scene plan JSON | `scene-plan.synthetic.json` |
| Six original cutout assets | `assets/*.source-cutout.png` |
| Six reviewed manual masks | `masks/*.manual-mask.png` |
| Continuity inspection stills | `scene-1.prototype.png`, `scene-2.prototype.png` |
| Artifact hashes and provenance | `artifact-manifest.json`, plus copied `PLAN.md` and `TASK_APPROVAL.md` |

All of these are derived from **one** programmatic synthetic drawing. No PNG/JPEG supplied by a child, no alternate art style and no V2 video is represented by them. The export-only script `export_review.py` lives in this review folder, outside the repository; it does not change product code.

## E. Acceptance and compatibility

**Level 1: PASS for synthetic local prototype**, subject to the explicit limitations below. World schema validates, six source IDs are stable across four planned scenes, original decoded source RGB/alpha pixels are preserved in cutout assets, new/source provenance is distinct, state continuity holds, first two still scenes differ by a reviewed translation, unsupported butterfly/running paths block, fixture/contact sheet exists, and V1 targeted/broad regression checks pass with the unrelated Vision exclusions disclosed. No GPU/paid inference was used.

**Level 2: NOT RUN / NOT PASS.** There is no LightningAI check, consented real drawing, adult-approved real event manifest, SAM2 quality test, new-object generator, motion execution, audio synchronization, whiteboard stroke engine or full story MP4 from V2.

Risks/limits: `review_ref` and `identity_review_ref` are fixture/manual attestations, not cryptographically/server-verified adult approval. A reviewer can still mislabel a mask; automated identity recognition is not claimed. Mask overlap threshold is a heuristic. Asset refs are process-local and not durable. White background composition does not reconstruct arbitrary painted background behind moving objects. Rigid transforms are not jointed walking/running animation. A V2 job API and Lightning transport require separate review after Level 1; exposing this method directly would bypass full live Gate A/B orchestration.

## F. Next milestone, not started

Only after reviewing Level 1: server-bound adult event/mask approval and durable artifact refs; real-source segmentation with manual correction; reviewed asset generation for additions; persistent scene state transport; pose/action and object-aware stroke/color engine; then isolated LightningAI Level-2 test on permitted media. The earlier rejected 53.496-second V1 media smoke is not upgraded by this milestone.

## G. Direct answers for the Architect's scope review

1. **How many different drawings were tested?** Exactly **one kind**: a generated 600×360 family/house/tree/garden PNG. It is reused for all tests and two stills. **Zero** independent real drawings, **zero** JPEG inputs, **zero** alternate styles. Unit-test variation changes masks/events/timing, not the drawing class.
2. **Are family objects hardcoded?** Yes **in the synthetic fixture** (`tools/story_world_v2_fixture.py` defines mother, father, child, house, tree, flowers and pending butterfly). The registry/planner schema accepts caller-supplied IDs/types, but generalization to unseen drawings is **not proven**. There is no model that discovers those objects automatically.
3. **What happens to a new PNG/JPEG without masks?** The prototype's `run_v2_prototype` requires supplied `ManualSourceObject` masks; missing or bad masks lead to `NEEDS_MASK_REVIEW` before planning/composition. There is no automatic SAM2 route in V2, no bounding-box-as-mask success and no live HTTP upload-to-V2 path. JPEG decode is supported by Pillow in principle but **not tested** here.
4. **Are event IDs traceable to Gate A/B?** They are structurally traceable to `segment_id`, `approved_fact_ids`, `confirmed_anchor_ids` and an exact quote plus fixture `review_ref`; the builder checks membership/quote and package/script hashes. **No**, they are **not yet cryptographically or server-side bound to a real adult Gate A/B review record**. Direct prototype invocation does not call `StoryVideoJobService` Gate checks. This must be solved before any live exposure.
5. **Does unsupported action return `UNSUPPORTED_ACTION`?** Yes when `SceneStateComposer.render_scene` is asked to execute `RUN`, `WALK`, `ADD_OBJECT`/pending butterfly or any action outside its supported static/translate/scale/rotate set. The planner can still represent a reviewed unsupported action; it does not silently render it as success. Tested with butterfly and RUN. No V2 job endpoint currently translates this error to HTTP status.
6. **Can Milestone 1 run on LightningAI?** The Python prototype could be copied to a compatible Python+Pillow environment and run on the synthetic fixture, but **no LightningAI run was performed**, no V2 HTTP route/provider transport/deployment exists, and real masks/review evidence/artifact persistence are missing. Therefore it is **not a validated LightningAI workflow** and Level 2 is NOT PASS.
7. **Is there a V2 whiteboard video?** **No.** V2 currently returns a world model, scene plan, original source cutouts and composited **still PNGs**. It has no V2 stroke animation, hand drawing, narration alignment, motion clip or final MP4. The prior 53.496-second MP4 was a rejected **V1 media-only** smoke, not output of this milestone.

## H. Explicit gates before requesting Milestone 2

- Architect review of the 17-file diff, the exact synthetic JSON/artifacts and the error semantics; accept that one simplistic fixture proves only local mechanics.
- Design server-owned adult approval for event/review and mask identity, tied to immutable script/source/session hashes; a caller-supplied `review_ref` is not sufficient.
- Design durable asset/mask storage and retention/privacy policy. Current `memory:` refs cannot survive process restart or be handed to Lightning as-is.
- Decide how to obtain and correct masks on real child art, including overlapping/ambiguous figures; validate with multiple permitted drawings and JPEG/transparent PNG cases.
- Specify how pending narration-added objects become generated, reviewed assets, and how unsupported WALK/RUN/pose changes are handled without silently degrading to rigid transforms.
- Review V2 media/transport/API contract separately before connecting GPU provider or claiming final whiteboard video. Existing Vision/ASR vs media-server routing and real runtime revision remain unverified.
- Repair or provide the unrelated Vision V3 fixture set before claiming an unqualified all-backend green suite; rerun Level-1 tests after any design changes.
