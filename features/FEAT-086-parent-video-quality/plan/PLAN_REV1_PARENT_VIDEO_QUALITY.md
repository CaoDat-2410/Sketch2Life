# Plan Rev1 — Parent story/video quality repair

**Feature:** FEAT-086 Parent video quality
**Status:** APPROVED
**Date:** 2026-11-24
**Worktree:** `<LOCAL_ROOT>\.codex-worktrees\fe`, branch `feature/fe-mobile-remediation`

## 1. Problem statement

The latest Parent video preview looks like a clean cartoon, includes a small duplicate picture/card inside the generated frame, and shows a text row beneath the player. The source asset used for that candidate is itself clean, vector-like turtle artwork, so its appearance cannot demonstrate child-like crayon art. The Qwen scene `visual_prompt` is short and the LTX prompt compiler repeats many broad identity/negative constraints. The worker also has a path that adds a second full-frame image guide in the middle of a scene to introduce an SVG prop.

The fix must improve motion instructions and scene conditioning without pretending prompt changes can turn a vector source into authentic child artwork, without changing the confirmed story or public API contract, and without making video safety/quota claims that are not established.

## 2. Authority and source evidence

- Product authority is the unsigned FEAT-063 SRS v2.7-draft Rev67, particularly FR-AI-02 through FR-AI-06 and FR-AI-13. It requires schema-validated story/video artifacts, original drawing lineage, LTX-2.5 image-to-video, and per-scene validation. This implementation work does not revise those targets.
- FEAT-085 records the prior real synthetic Parent workflow and one completed five-scene silent candidate. Its source image is vector-like and its preview is explicitly an unreviewed technical candidate.
- FEAT-061 provides a crayon-style synthetic house-and-sun image and explicit provenance stating it is AI-generated, not a real child's artwork.
- Current official LTX guidance says I2V prompts should describe the action after the initial image, use one continuous take when appropriate, and prefer plausible motion. The optional prompt enhancer performs another inference and adds latency; it is not a substitute for a suitable source image.
- The reviewed community skill is MIT licensed, but is designed for cinematic prompt enhancement and agent-side writing. It is not installed in the Modal worker and is not a model-quality adapter.

## 3. Scope

### In scope

1. Refine the existing Qwen story-generation instructions for `visual_prompt`: preserve the source illustration, express one distinct scene action through a concise beginning/action/result progression, name only story-approved props, give any needed relative placement, and avoid generic repeated bobbing, invented scenery, style restyling, and descriptive re-captioning.
2. Keep `sketch2life.story-revision.v1` and its JSON key set. Raise only the existing visual-prompt limit from 280 to 420 characters, consistently in prompt, schema, parser, and tests. Keep adult confirmation and all current hard validation gates.
3. Simplify the LTX scene prompt into a concise, action-first single-shot instruction. Explicitly prohibit duplicated source art, picture-in-picture, cards, frames, logos, and on-frame text while preserving source silhouette, palette, hand-drawn texture, position, and scale.
4. Stop supplying a second full-frame SVG-composited image guide during a scene. Continue using the normal image-to-video conditioning frame and existing scene continuity behavior. Retain unrelated SVG catalog/guide functionality.
5. Remove the visible duration/scene-count/no-audio metadata line beneath the ready video player. Keep the player, playback button, timeline, and accessibility behavior.
6. Add/adjust focused contract tests for the story prompt limit/content, compiled LTX prompt and no-secondary-guide behavior, and the Parent video screen.
7. Use synthetic crayon artwork from FEAT-061 for one visual validation when a fresh real run can be created without disturbing existing seed accounts or runs. Label it synthetic.

### Out of scope

- Changing SRS requirements, public story API keys, DB schema, adult script approval, activity selection, quotas/payments, authentication, consent, safety policy, video retry counts, or story scene counts.
- Installing new models, LoRAs, ComfyUI, a runtime “skill,” or a new video-generation provider. Official sparse-motion-track LTX workflows may be evaluated later if this bounded prompt/conditioning repair is not enough, but no new weights or inference architecture are introduced here.
- Using genuine child artwork or personal data.
- Claiming production safety validation; the existing preview remains governed by its existing status.

## 4. Exact implementation paths

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/story_visual_plan.py`
- `deployment/modal/srs_v23/video_app.py`
- `apps/ui-mobile/src/parent/presentation/screens/VideoCandidateScreen.tsx`
- `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`
- `deployment/modal/srs_v23/tests/test_story_visual_plan.py`
- `deployment/modal/srs_v23/tests/test_silent_video_prompt.py`
- `apps/ui-mobile/tests/videoCandidateProgress.test.ts`
- This feature's plan, approval, context, decisions, source register, status, and evidence only.

No other source paths may be added without a new scope approval.

## 5. Work sequence

### M0 — Baseline and provenance

- Preserve pre-existing worktree changes.
- Record the existing source image hash/provenance, prior candidate evidence, and the affected UI row/worker guide path.
- Use only the FEAT-063 SRS as product authority.

### M1 — Story JSON and prompt contract

- Keep JSON fields and version stable.
- Update the Qwen prompt so `visual_prompt` carries one concrete, image-grounded action and its visible result rather than a generic visual description.
- Increase the existing field limit to 420 characters across schema, parser, prompt instructions, and tests.
- Do not weaken strict JSON, language, safety, factual, age, or adult-review gates. Avoid adding new rejection rules that would reject otherwise valid stories solely for style preferences.

### M2 — LTX image-to-video conditioning/prompt

- Compile concise action-first prompts; source art is the visual reference, not an object to redraw or show as an inset.
- Remove the extra full-frame prop guide image and corresponding worker packaging/runtime probe if unused by this video path.
- Preserve input hash verification, first-frame/continuity behavior, silent output, scene/media validation, and current retry/admission behavior.
- Record prompt/template version and hashes as currently implemented.

### M3 — Parent UI cleanup

- Remove the visible metadata line beneath the player; keep the video controls and timeline.
- Do not show technical prompt or parser details in the user-facing screen.

### M4 — Verification and evidence

- Run the focused existing Modal story/video contract tests and the mobile video UI test/typecheck.
- If Docker/backend and the selected Modal profile are already available, perform at most one real synthetic Parent story-to-video validation with the crayon house/sun input, actual Qwen and LTX workers, existing gates enabled, no fixtures/mocks, and no retry. Do not delete or overwrite existing data. If a new session or runtime is unavailable, stop and record the blocker rather than bypassing a gate or provisioning unrelated services.
- Capture only the resulting synthetic video/artifact evidence and a UI screenshot demonstrating the absent metadata row. Store evidence under `features/FEAT-086-parent-video-quality/evidence/`.
- Record per-stage timings, worker/call IDs, source and output hashes, frame review, and limitations without logging credentials, raw child data, or provider secrets.

## 6. Acceptance criteria

- **AC1 — Compatible structured story:** Current story JSON key set/version remains valid; visual prompt maximum is consistently 420; focused parser tests pass; each model prompt instructs an explicit, unique physical action and visible outcome tied to the approved scene.
- **AC2 — Source-art fidelity:** Video worker conditions on the verified source/continuity image only; it does not send a second full-frame composite of the same drawing as a mid-scene guide. Compiled prompt prohibits a duplicate inset/card and discourages restyling while keeping the camera and background stable.
- **AC3 — Video result review:** If the single real candidate runs, inspect representative start/middle/end frames. Record whether the subject remains recognizable, source crayon marks remain visible, each approved named object/action is present once, and no duplicate inset/text appears. If any criterion fails, mark it failed/partial; do not call it fixed or retry automatically.
- **AC4 — UI:** No visible duration/scene-count/no-audio text row beneath the ready player; play/pause, timeline and accessibility controls remain.
- **AC5 — Evidence and safety:** No real child data, no gate bypass, no secrets in evidence, no unrelated data deletion, and no commit/push.

## 7. Risks and limits

- LTX is generative; prompt/conditioning changes reduce common failure modes but cannot guarantee perfect adherence. One inference is a bounded quality observation, not a benchmark.
- A synthetic crayon drawing is not authentic child artwork. It is the safe development input available in this repository.
- Official LTX motion-track conditioning could provide finer motion control, but requires a separate evaluation of adapter weights, deployment cost, latency, and model compatibility.
- The visible footer is mobile UI metadata; its removal does not alter MP4 content or server metadata.

## 8. External technical references

- LTX I2V workflow: https://docs.ltx.io/open-source-model/usage-guides/image-to-video
- LTX prompting guide: https://docs.ltx.io/open-source-model/usage-guides/prompting-guide/
- Official LTX-2.5 workflows, including motion-track I2V: https://github.com/Lightricks/ComfyUI-LTXVideo/tree/master/example_workflows/2.5
- Reviewed community prompt skill (not installed): https://github.com/benjiyaya/LTX-2.5-Agent-Prompt-Skill
