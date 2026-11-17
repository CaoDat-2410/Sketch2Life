# FEAT-020 Final Scope Update

**Date:** 2026-09-12
**Status:** owner-confirmed scope

This addendum supersedes the earlier strict-video completion wording in `PLAN.md` for the first backend demo.

## Confirmed decisions

- Gate decision actor: `DEMO_OPERATOR`.
- The first E2E uses both committed test assets: the Vietnamese WAV and the synthetic image.
- Video generation is deferred. The workflow must still create the story/scene/media context and return a typed `VIDEO_DEFERRED` stage, but it does not need to generate a video in this milestone.
- The first successful backend terminal state is `BACKEND_CONTEXT_READY`, not `WORKFLOW_COMPLETE`.
- The workflow must reach the selected Montessori context, experience spec, story/scene plan, original-art preservation plan, off-screen activity handoff, and feedback/history demo records.
- PixiJS is not implemented in this feature. The workflow only emits the asset IDs and render intent that a future PixiJS bridge will consume.
- PixiJS assets are author-authored vector assets whenever possible. Runtime execution must not call an image generator to fill missing PixiJS assets.

## First E2E terminal contract

```text
INPUT_VALIDATED
→ UNDERSTANDING_PROPOSED
→ GATE_A_CONFIRMED
→ CONTEXT_READY
→ GATE_B_CONFIRMED
→ EXPERIENCE_READY
→ STORY_SCENE_READY
→ ART_PLAN_READY
→ VIDEO_DEFERRED
→ HANDOFF_READY
→ FEEDBACK_RECORDED
→ BACKEND_CONTEXT_READY
```

The result must include `video.status=DEFERRED`, a reason, and the future provider contract reference. It must not claim that a micro-video was generated.

## Montessori questions remain intentionally split

The following are still open and must be answered separately before the demo context profile is frozen:

1. What is the target age in years/months?
2. What is the child’s assumed readiness or prior familiarity with the activity?
3. Which materials are available at home, and which substitutions are allowed?
4. What supervision level is required, and how long should the activity last?
5. Are there safety, allergy, motor, sensory, or accessibility constraints for the demo profile?
