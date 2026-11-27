# FEAT-099 plan, revision 1: motion with some physics, and one drawing-guide level

Research: `../research/MOTION_RESEARCH.md`. Nothing is built until the owner approves.

## 1. Goals

1. A subject that moves its legs when the story says it walks or runs.
2. No deformed head or body.
3. The drawing guide has one level (the present 6-to-10 one); the 3-to-5 level is removed.

Not in this plan: new video model, GPU change, narration length and voice waiting (FEAT-098 follow-ups).

## 2. Part A: video motion

Each phase ends with clips the owner looks at; the next phase starts only with their yes.

### A0. Find which cause matters (one GPU session, about 10 L40S minutes)

Same first frames, prompt and seed for the deer scenes 4 (stride) and 5 (head down):

| Variant | End guide | Render size |
|---|---|---|
| a (today) | first frame, 0.7 | 960x576 |
| b | none | 960x576 |
| c | none | 1280x768 |
| d | first frame, 0.3 | 1280x768 |

Reported: clips side by side, whether the camera drifts, whether the head deforms, how far the legs move.

### A1. Remove what fights motion (W1; offline work, then one GPU session, about 15 minutes)

| # | Work | Files |
|---|---|---|
| M1 | End guide as A0 shows: removed, weaker, or only for scenes meant to end where they start | `modal_scene_renderer.py`, `video_app.py` |
| M2 | Movement list per body type (four legs, bird, fish, person, vehicle, plant, other): each movement says which part moves and its limit. Four legs, for example: walk in place with alternating legs, tail flick, ear twitch, small head turn, slight nod. Never: head to the ground, rearing, turning around | new pure module in `learning_story.py` |
| M3 | The writer picks a movement from the list that matches the sentence the voice speaks ("runs" and "walks" give a walking cycle) instead of free "small and slow" text; the English prompt is built by code from the choice | `learning_story.py`, tests |
| M4 | Motion prompt: gait and speed, feet touch the ground, body parts keep their shape, camera static; the "exactly as in the first frame" clause is reworded to keep the drawing style only | `_ltx_animation_prompt` |
| M5 | `small` render size on or off, as A0 shows (owner decides; costs about 20 s per scene to switch off) | `render_options.ACCEPTED` |

### A2. Physics-posed guide frames (W2; only for what A1 leaves wrong)

1. Prototype offline on three synthetic drawings (deer, chick, bicycle): part masks with the SAM model already used,
   from part boxes of the vision model; joints with angle limits; gait cycle with ground contact; wheels that turn.
   Output: pose pictures and a plain CPU preview, shown to the owner before any GPU use.
2. LTX gets 2 to 4 of those poses as guide frames (positions 8k+1, strength chosen from a small test). A scene whose
   parts cannot be cut falls back to A1.
3. About 25 L40S minutes for the strength test and one full video.

### A3. Reject deformed scenes (after A1)

A CPU measure on the rendered clip: the subject's mask in sampled frames against the first frame (area, outline and
head-region change). A scene over the limit is rendered once more with another seed (SRS stage 9 allows up to two).
The limit is calibrated on saved good and bad scenes and reported with its false positives before it blocks anything.

## 3. Part B: one drawing-guide level

| # | Work |
|---|---|
| G1 | App: remove the two age buttons; always ask for the `simple` guide; the profile age no longer picks a level |
| G2 | Server: default `simple`; a `beginner` request from an old app build gets the `simple` guide |
| G3 | Delete the 150 `beginner` recipe files and the beginner rules (kept in git history) |
| G4 | Tests of the app and server updated first |

Effect to know: children of 3 to 5 get the longer guide (5 to 8 steps, curves allowed). No age label is shown.
SRS FR-AI-15 and AT-18 speak of choosing a difficulty; the plan does not edit the SRS and records the difference.

## 4. Acceptance

1. A: in the owner's viewing of the test set (three drawings, scenes that say walk or run, and head movements): legs
   visibly move in the walking scenes; no deformed head or body. Each failing scene is listed.
2. A: no camera drift worse than today's; time from video request to ready not more than 10% longer than 5 min 54 s,
   except the retries of A3, which are reported.
3. B: no 3-to-5 choice in the app; every profile gets the same guide; recipe, API and app tests pass.
4. Offline tests are written first and existing tests show no new failure.

## 5. Risks

- Without the end guide the camera may drift or the subject may leave the frame (why it was added).
- A video model can still bend a flat drawing; A2 lowers this and does not remove it.
- Cutting legs out of crayon drawings may fail, mostly where legs touch.
- Each GPU session costs money; the totals above are about 50 L40S minutes if every phase runs.
