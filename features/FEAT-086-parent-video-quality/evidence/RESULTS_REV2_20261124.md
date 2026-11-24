# FEAT-086 Rev2 results — detailed LTX scene prompts

**Date:** 2026-11-24
**Scope:** Prompt research, more actionable Parent story motion directions, backend/worker prompt-length alignment, focused contract tests.
**Plan:** `plan/PLAN_REV2_DETAILED_LTX_SCENE_PROMPTS.md` (approved; SHA-256 in `approvals/TASK_APPROVAL.md`).

## Research findings

- The official [LTX image-to-video guide](https://docs.ltx.io/open-source-model/usage-guides/image-to-video) treats the input image as the visual starting point and uses text to direct what happens next, especially action and motion.
- The official [LTX prompting guide](https://docs.ltx.io/open-source-model/usage-guides/prompting-guide/) recommends clear chronological physical actions, focused single shots, and a concise natural-language description rather than a bag of disconnected tags.
- The official [LTX-2.5 workflow collection](https://github.com/Lightricks/ComfyUI-LTXVideo/tree/master/example_workflows/2.5) includes motion-track conditioning as a distinct workflow. It would require a separate model/control path and is outside this prompt-only change.
- The reviewed [LTX-2.5 Agent Prompt Skill](https://github.com/benjiyaya/LTX-2.5-Agent-Prompt-Skill) is an agent-side writing aid, not a Modal inference adapter. It was not installed into the worker because cinematic embellishment can conflict with the requirement to preserve the child's drawing.

## Changes made

1. Qwen's existing `visual_prompt` remains in the same public story JSON version and key set. It now allows 900 characters and asks for 3–4 concise English sentences in present tense: opening pose, the approved physical action in chronological beats, direction/speed/range and contact/reaction when relevant, approved prop placement, and visible end pose.
2. The review uncovered two hidden 400-character ceilings: the backend Parent-to-video manifest adapter and Modal worker visual-plan validator. Both now accept up to 900 characters and still reject longer values. This prevents a valid detailed story prompt from being dropped before LTX.
3. The LTX prompt compiler is `story-i2v-v7`. It turns the plan into a flowing paragraph with framing, starting state, one approved action, source-art preservation, permitted entity/prop movement, end pose, and camera/output constraints. It continues to use one conditioning image per scene and does not restore the duplicate SVG guide.
4. No public API schema, database, safety/admission/quota/retry behavior, or SRS target was changed.

## Verification

Focused command:

```powershell
.\.venv\Scripts\python.exe -m pytest deployment/modal/srs_v23/tests/test_parent_story_output_contract.py deployment/modal/srs_v23/tests/test_story_visual_plan.py deployment/modal/srs_v23/tests/test_silent_video_prompt.py deployment/modal/srs_v23/tests/test_video_app_contract.py backend/tests/unit/test_parent_video_candidate_manifest.py -o addopts='' --tb=no -q
```

Result: **98 passed, 4 skipped in 1.17s**. The skipped cases need optional LMFE support. These tests establish schema/parser/length/compiler/manifest contracts; they do not establish the visual quality of a generated video.

## Live inference status and limits

- No Modal inference request was sent, so this revision has no generated video to review.
- The last bounded runtime check did not establish usable prerequisites: Docker daemon access was denied and `modal app list --env dev` did not return. Per the approved plan, no generation was started without a reachable runtime.
- The available crayon-style source noted in FEAT-061 is synthetic AI-generated artwork, not a real child's drawing. No real-child media was used.
- Therefore, prompt formatting is contract-verified; action faithfulness, drawing identity preservation, scene continuity, artifacts, and actual render time remain unverified until a single gated synthetic run can be reviewed.
