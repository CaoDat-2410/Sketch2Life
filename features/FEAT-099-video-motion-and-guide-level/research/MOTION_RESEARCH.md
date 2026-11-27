# FEAT-099 research: why the subject moves badly, and how to give the motion some physics (2026-11-27)

## 1. What the owner saw

Video of run `dd8a3ee8` (deer, FEAT-098): the legs do not move when they should, and at 0:45 the head is badly
deformed. Sampled frames: `evidence/feat098_scenes_2_4_5.png` (rows: scenes 2, 4, 5).

| Scene | Narration says | `action_en` sent to LTX | Result in sampled frames |
|---|---|---|---|
| 2 | walks softly on the grass | "The deer lifts one long leg slightly off the ground." | legs almost still |
| 4 | runs fast over the field | "The deer extends its front legs forward in a slow stride." | legs still, body sways |
| 5 | stands still under the tree | "The deer lowers its head gently towards the ground." | neck folds into the body, then the pose returns |

## 2. Causes found in our code

| # | Cause | Where | Confidence |
|---|---|---|---|
| C1 | **Every scene is told to end exactly as it starts.** The first frame is also an end guide at strength 0.7. A walk cannot progress (the legs must be back where they were) and a large movement must be undone inside the clip, which in a flat drawing becomes a morph | `modal_scene_renderer.py` (`END_GUIDE_STRENGTH = 0.7`), `video_app.py` `_end_guide_arguments`; introduced by FEAT-094 Rev 2 amendment A item 2 to stop camera drift. FEAT-094 experiment E2 tested a *different* end pose, not the first frame again | high for the mechanism; the effect on these scenes is not yet measured |
| C2 | **The writer may only ask for "one small, slow movement"**, written without regard to the sentence the voice speaks (runs fast becomes a slow stride), and may ask for large joint movements (head to the ground) | `learning_story.py` prompt for `action_en`; `_FAST_MOTION` filter | high |
| C3 | The motion prompt is one short sentence plus "keeps its crayon strokes ... exactly as in the first frame", which favours stillness. It says nothing about weight, ground contact or which joint bends | `video_app.py` `_ltx_animation_prompt` | medium |
| C4 | The 960x576 render (`small`, FEAT-098) softens lines; in the benchmark it smeared the chick's head and broke a leg near the end | FEAT-098 `evidence/benchmark` | medium: not isolated on the deer |
| C5 | Nothing rejects a deformed scene: the vision check only reports, and it answered "no problem" on ten of ten saved scenes with defects in FEAT-094 | `video_scene_check = report` | high |

## 3. What others do (web, 2026-11-27)

- **LTX prompting guides:** describe only the motion, one action, concrete verbs, a static-camera term, and where the
  movement ends. No animal-walking example found
  ([fal.ai guide](https://fal.ai/learn/tools/how-to-use-ltx-2-5),
  [LTX image-to-video guide](https://ltx.io/blog/ltx-2-image-to-video-text-to-video-workflow)). The official LTX-2.5
  prompt guide page could not be read.
- **Pose control (Union Control IC-LoRA):** detects *human* body keypoints and is "less effective for" scenes without
  people ([guide](https://docs.ltx.io/open-source-model/feature-guides/structural-control/union-control)). Not for
  animals.
- **Motion Track Control IC-LoRA:** the user draws a few keypoint paths and the model follows them. The weights are the
  LTX-2.3 ones reused on 2.5, which the adapter page says is no guarantee of compatibility; first-frame use of this
  adapter is not stated; it needs a second pipeline (`ICLoraPipeline`); LTX community licence
  ([model card](https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Motion-Track-Control),
  [adapters](https://docs.ltx.io/open-source-model/integration-tools/ic-lo-ra-adapters)).
- **Meta AnimatedDrawings:** archived since 2025-09-03, MIT. Built for human figures; its four-leg example converts the
  *human* skeleton and plays a human motion clip ([repo](https://github.com/facebookresearch/AnimatedDrawings),
  [quadruped example](https://github.com/facebookresearch/AnimatedDrawings/tree/main/examples/quadruped)).
- **Physics-aware video research** (2024 to 2026: PhysGen, PhysMotion, PhysAlign) needs other base models or rigid-body
  simulation; none fits a drawn animal on our pipeline.

## 4. Ways to add physics

| Way | What it is | Gain | Cost and risk |
|---|---|---|---|
| W1. Remove what fights motion | drop or weaken the end guide, match the action to the narration, a movement list per body type that a flat drawing can hold, better motion prompt | targets C1 to C3 directly, no new model | camera drift may come back (the reason for the guide); LTX still decides the joints |
| W2. Physics-posed keyframes | on CPU, cut the subject into parts (head and neck, body, legs, tail), turn them about joints with angle limits and a gait cycle with feet on the ground, and give LTX those poses as guide frames in the middle and at the end | the model is shown where the legs and head go; same model, same licence, uses the guide support the worker already has | part cutting on crayon drawings; one pose set per body type; the model may still morph between guides |
| W3. Motion Track Control | the same gait paths as keypoint trajectories for the 2.3 adapter | continuous control | unproven on 2.5 and on drawings; new weights and pipeline; GPU memory |
| W4. Paper puppet renderer | animate the cut parts directly with 2D physics, no video model for the subject | legs always move, heads never morph, near-free | replaces the generative pipeline: the SRS targets LTX image-to-video and puts drawing animation of the PixiJS kind out of scope (needs an SRS change); puppet look; body-part cutting must be reliable |
| W5. Pose control | skeleton video | none | human-only |

**Reading:** W1 first (cheap, aimed at a cause we can see in the code), then W2 for what W1 does not fix. W3 only as an
experiment if W2 fails. W4 is the strongest on physics but changes the product direction, so it is the owner's call.

## 5. Second pass (2026-11-27): measured on saved videos, no GPU

`evidence/measure_motion.py` (numbers in `evidence/motion_measure.json`). For each scene: the largest change from the
first frame, the change that is left at the end, and the movement of eight border blocks (camera drift).

| Videos | End guide | Change left at the end / largest change | Border movement (px at 320 wide) |
|---|---|---|---|
| 10 scenes: deer app run, chick run 4 | the first frame, 0.7 | 0.08 to 0.44: **every scene comes back to its start** | 0 |
| 3 clips: benchmark chick, E1 chick, E1 bicycle | none | 0.64 to 0.99: the scene ends somewhere else | 4.9 to 16.3: **the camera drifts** (the bicycle's tree slides in front of it) |

So removing the guide alone trades one fault for the other. The earlier experiment E2 showed the third option: a guide
with a *different pose over the same background* made the chick arrive at that pose. Identical background pixels hold
the camera; the new pose gives the motion somewhere to go. The caveat: different clips, drawings and prompts, so the
numbers show the pattern and not a controlled comparison.

Cut-and-pose feasibility (`evidence/part_split_prototype.py`, `part_split.png`, `part_split_poses.png`): on the
synthetic deer, with plain image morphology on the CPU, all four legs were found and turned about their hips into two
walking poses in under a minute of computing. Faults seen: specks left where the hooves were, grass erased under the
legs (the product pastes onto a clean background plate instead), a rough edge on the chest. One drawing, a colour mask
instead of the worker's SAM mask: evidence that it can work, not that it works on any drawing.

More sources:

- Guide strength sets how free the model is near that frame (noise mask `max(0, 1 - strength)`); the same image at both
  ends at full strength leaves little room for motion
  ([ComfyUI LTX guides](https://comfy.icu/node/LTXVAddGuide), [first-last-frame guide](https://ltx23.org/blog/ltx-23-first-last-frame-comfyui)).
- Several stills at chosen frames with their own strength is the documented way to steer in-between motion
  ([Diffusers LTX-2](https://huggingface.co/docs/diffusers/api/pipelines/ltx2)); our pinned code accepts guides at any
  frame (FEAT-087 study).
- Sliding and still legs: say where the feet touch the ground, where the subject starts and ends, keep travel short and
  the camera fixed ([walking prompt guide](https://www.pippit.ai/blog/how-to-prompt-walking-without-sliding),
  [motion control playbook](https://help.aliyun.com/en/model-studio/token-plan-playbook-motion-control); both vendor
  advice for photographic video).

