# FEAT-099 plan, revision 2: build once, test once

Replaces Rev 1 part A (staged phases with several GPU sessions), at the owner's request of 2026-11-27: one build, then
one test, because GPU time is expensive. Part B (one drawing-guide level) is Rev 1 section 3, unchanged. Research:
`../research/MOTION_RESEARCH.md`, section 5 added. Nothing is built until the owner approves.

## 1. The design in one paragraph

Each scene gets, besides its first picture, **pose pictures** made on the CPU from the child's own drawing over **the
same background**: an end pose (and for walking, one middle pose). The video model is guided to those instead of back to
the first picture. The story writer picks the movement from a fixed list that matches the spoken sentence, and the
motion prompt is written by code. The identical background holds the camera; the new pose gives the motion a place to
arrive.

## 2. Build (all offline, tests first, no GPU)

| # | Work | Files (main) |
|---|---|---|
| V1 | **Movement list** per body type (four legs, two legs, fish, vehicle, other): walk, run, look to the side, small nod, tail or ear flick, roll, swim, stay. Each entry fixes which part turns, by how much, how far the subject travels, and its English prompt (gait, feet on the ground, shape kept, camera still). Never: head to the ground, turning around, rearing | new pure module beside `learning_story.py` |
| V2 | The writer chooses a movement id from the list for each scene, matching its sentence; free `action_en` text is no longer used for new stories. Stored old stories keep working | `learning_story.py`, backend learning contract and timeline |
| V3 | **Part cutting and posing** on CPU from the subject mask the worker already makes: trunk by morphology, thin parts below it as legs, head region for a small nod; poses turn parts about joints with angle limits; walking also moves the whole subject forward a short way. A check on the cut parts (count, size, position); when it fails the scene falls back to moving the whole cut-out, or to "stay" | new module for the preparation child, `keyframe_compositor.py` |
| V4 | Preparation returns the first, middle and end pictures on one background; they are cached with FEAT-098's review-time cache | `scene_prepare*.py`, `video_app.py`, `scene_cache.py` |
| V5 | The renderer accepts a list of guide pictures with frame and strength; the "first frame again" guide is removed. "Stay" scenes keep the end pose equal to the start pose, at a weaker strength | `video_app.py`, `modal_scene_renderer.py`, pipeline ports |
| V6 | Deformation measure on the rendered clip (subject outline against the background plate, sampled frames). **Report only**: it logs and marks scenes; calibrated on the saved good and bad clips; no automatic re-render, so no extra GPU | new pure module, orchestrator |
| V7 | Switches, so the one test can compare and the choice needs no new code: motion mode (`posed`, `off`), middle pose on or off, guide strength, render size | settings, `render_options.py` |
| B | Drawing guide: one level (Rev 1 section 3, G1 to G4) | app, server, 150 recipe files |

**Gate before any GPU (free):** pose pictures and a CPU preview animation for the five deer scenes, the chick and the
bicycle, shown to the owner. A cut that looks wrong is fixed here, offline.

## 3. Test: one GPU session

One temporary Modal job (nothing left running, no idle minutes), same container doing preparation and rendering, using
the five scenes of the FEAT-098 deer story (its video is the "before"; it is not rendered again).

| Renders | Scenes | Setting |
|---|---|---|
| 5 | all five | proposed default: end and middle pose, strength 0.7, 960x576 |
| 2 | walking scene and head scene | end pose only (no middle) |
| 2 | same two | proposed default at 1280x768 |
| 1 | walking scene | strength 0.9 |

Ten renders, about 11 to 13 L40S minutes (about 0.4 USD at the rate used in FEAT-098), cap 20 minutes. The owner gets
the clips side by side with the "before", picks the settings, and the picked ones become the default by changing V7
values only. No second GPU session and no video through the app unless the owner asks.

## 4. Acceptance

1. Walking scenes: legs visibly alternate and the subject moves forward (owner judges the clips).
2. No deformed head or body in the five default renders (owner judges); the deformation measure's verdicts are listed
   next to the owner's.
3. Camera border movement no larger than 2 px at 320 wide (`measure_motion.py`).
4. Render time per scene within 10% of FEAT-098's for the same size.
5. Drawing guide: no 3-to-5 choice; every profile gets the same guide.
6. Tests written first; existing tests show no new failure.

## 5. Risks, and what "once" cannot promise

- The video model may still morph between poses. The test shows it; fixing it further would need another session, which
  is then the owner's decision.
- Cutting parts works on the one deer drawing tried; other drawings may fall back to whole-subject movement.
- The walking pose set is written for side views; a front view falls back.
- Changing the movement contract touches stored stories; old ones must still load (tested).
- Build effort is larger than Rev 1 A1 alone, spent before the first real clip.
