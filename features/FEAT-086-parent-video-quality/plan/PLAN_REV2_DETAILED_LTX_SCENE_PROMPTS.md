# FEAT-086 Plan Rev2 — Detailed LTX scene prompts

**State:** APPROVAL RECORDED in `approvals/TASK_APPROVAL.md` after the owner's direct request on 2026-11-24.
**Authority:** FEAT-063 working SRS v2.7-draft, Rev67 baseline; no product requirement changes.
**Base:** Plan Rev1 implementation; Rev2 expands only the scene-prompt detail and verification.

## 1. Goal

Make each LTX-2.5 scene prompt concrete enough to direct a coherent, child-friendly action from the supplied drawing: what the camera sees, what moves, how the movement unfolds, how any approved prop interacts, and where the scene settles. Preserve the original drawing and scene/story contract.

## 2. Research basis

- LTX's official I2V guide says the source image already communicates the scene's appearance; the text prompt should focus on what happens next, motion, and camera behavior.
- LTX's official prompting guide asks for a natural chronological action, present-tense physical verbs, and roughly 4–8 descriptive sentences for a single continuous shot. It also recommends starting with the core action and adding details that contribute to the shot.
- The official LTX-2.5 ComfyUI workflows include a Motion Track ICLoRA path. That requires a different control/conditioning path and model assets; it is not part of this prompt-only amendment.
- The reviewed community agent skill expands ideas cinematically, but is not a runtime/model adapter and can introduce style details that conflict with source-art preservation. Do not install it into the Modal worker.

## 3. Scope

### In scope

1. Keep `sketch2life.story-revision.v1`, all public JSON keys, and adult confirmation unchanged.
2. Raise only the existing Qwen `visual_prompt` output limit from 420 to **900 characters**, matching the backend `StorySceneV1.visual_prompt` maximum. Do not add a field or DB migration.
3. Raise the internal Parent-to-video adapter and visual-plan `model_action_instruction` ceiling from 400 to 900 so a valid detailed prompt reaches Modal instead of failing with `VIDEO_STORY_SCENE_INVALID`. Preserve the existing rejection for values above 900.
4. Ask Qwen for 3–4 concise English sentences in present tense. Cover, when relevant: the opening pose; one approved physical action broken into a short chronological progression; direction, speed/range, and contact or reaction; a story-approved prop's exact relative placement/interaction; a visible settled result and handoff pose. Keep the action tied to the adult-approved scene and established subject/anchors.
5. Compile the validated plan as one natural-language paragraph of 7–8 sentences including the Qwen action paragraph, not a numbered checklist. Include:
   - shot size/framing and the plan-approved camera behavior;
   - start condition from the original image or prior scene's final frame;
   - one action with beginning, movement/contact, reaction/result, and settling beat;
   - exact visible entities and placement, adding only plan/story-approved props;
   - source-art preservation (silhouette, proportion, palette, uneven hand-drawn/crayon marks, paper texture, composition and scale);
   - explicit end pose/state for continuity.
6. Keep scenes as single continuous shots with no cuts. Keep camera/background still unless the validated plan specifically permits a subtle camera move. Continue one conditioning image per scene; do not restore the removed SVG composite guide.
7. Retain current safety, schema, fact, admission, quota, timeout, retry, silent-output, and adult-review behavior.
8. Add focused tests for the 900-character field limits across Qwen, backend adapter and visual-plan validation; prompt detail/content; flowing paragraph composition; approved-entity restrictions; and story/version compatibility.
9. If the local runtime and selected Modal profile become reachable, use at most one real synthetic Parent video run from the existing crayon house-and-sun asset. Use existing gates, no retry, no fixture/mocks, and do not touch old runs. Review start/middle/end and representative scene transitions. If prerequisites are unavailable, record the blocker and stop without issuing a generation request.

### Out of scope

- Changing public JSON keys/version, the backend API limit (already 900), database schema, story logic, activity choice, lesson pins, SRS, approval gates, safety/quota policy, model/checkpoint, video length, GPU settings, or scene retry policy.
- Enabling a prompt-enhancer model or adding another inference stage.
- Adding Motion Track/ICLoRA nodes or weights, ComfyUI, LoRA, a new worker/provider, or an agent skill to Modal.
- Using real child media or bypassing any gate.
- Commit/push.

## 4. Exact implementation paths

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/story_visual_plan.py`
- `backend/src/sketch2life/application/services/parent_video_candidate_service.py`
- `backend/tests/unit/test_parent_video_candidate_manifest.py`
- `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`
- `deployment/modal/srs_v23/tests/test_story_visual_plan.py`
- `deployment/modal/srs_v23/tests/test_silent_video_prompt.py`
- `deployment/modal/srs_v23/tests/test_video_app_contract.py` (verification only unless a prompt contract needs an assertion)
- This feature's `CONTEXT.md`, `DECISIONS.md`, `STATUS.md`, and `evidence/` only.

No backend, public API, UI, or SRS files are in Rev2 scope.

## 5. Acceptance criteria

- **AC1 — Compatible JSON:** Qwen prompt/parser/schema all permit `visual_prompt` through 900 characters; backend contract already accepts 900. The public story schema version/key set remains byte-for-byte structurally unchanged.
- **AC2 — Detailed action:** prompt instructions cover physical verbs, relative direction, movement pace/range, contact/reaction where relevant, and final pose, while prohibiting unapproved events/props and decorative scene restyling.
- **AC3 — LTX-readable prompt:** compiler returns a flowing 4–8 sentence single-shot prompt that spells out framing, approved action progression, camera behavior, source-art preservation, and continuity. No numbered prompt checklist, duplicate source inset, cuts, captions, subtitles, logos, or audio.
- **AC4 — Existing gates:** no parser/gate/admission/retry changes; one conditioning image per scene and no extra SVG guide.
- **AC5 — Verification:** focused story/video tests pass; full real-output quality is only marked validated if the bounded synthetic Modal run succeeds and the output is visually reviewed. No success claim from source inspection alone.

## 6. Risks and limitations

- More prompt detail can overconstrain or dilute a simple action. Keep sentences concrete and relevant; do not fill out camera/light details that the source image or scene does not need.
- LTX generation remains stochastic. A single candidate is a smoke validation, not a quality benchmark.
- The crayon input is synthetic AI-generated art, not an authentic child's drawing.
- The current environment previously denied Docker daemon access and did not return a Modal app list. No live run is authorized by this plan if those conditions persist.

## 7. References

- https://docs.ltx.io/open-source-model/usage-guides/image-to-video
- https://docs.ltx.io/open-source-model/usage-guides/prompting-guide/
- https://github.com/Lightricks/ComfyUI-LTXVideo/tree/master/example_workflows/2.5
- https://github.com/benjiyaya/LTX-2.5-Agent-Prompt-Skill
