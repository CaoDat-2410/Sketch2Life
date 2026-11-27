# FEAT-094: Parent learning video redesign

- **Status:** APPROVED and in progress (Rev 2, option A, 2026-11-26): see `approvals/TASK_APPROVAL.md` and
  `status/STATUS.md`.
- **Owner decision of 2026-11-26:** LTX-2.5 renders every scene. The cut-out option A below is **not** chosen, so the
  FR-AI-05 / BR-45 conflicts listed below no longer apply to the plan.
- **Opened:** 2026-11-26, from the owner's chat after the two live runs of FEAT-093.
- **SRS:** FEAT-063 v2.7-draft is the baseline. Parts of this direction conflict with it (see below).

## What the owner asked for (summarised from chat)

1. Rework the AI video flow. The current video does not help a child learn or remember anything, and its quality needs
   to be reconsidered (for example a child who is not in the drawing appeared in one scene).
2. The script must use the child profile (age and interests) and teach about the drawn thing: what it is, how it is
   built, what it is for. Possibly a whiteboard-video style.
3. Add the motion-type approach below (2D cut-out animation of the child's own strokes).
4. Make LTX-2.5 rendering faster, with techniques comparable to the ones that sped up Qwen.
5. Produce a long, detailed plan, ask a few questions to settle it, and research the fixes.

## Owner-provided option A: motion-type library (pasted material, untested on any drawing)

Flow: recognise each object and give it a motion type and parts → code cuts the child's strokes into layers → the
script picks actions from a shared library → compose over an AI background → check; on failure step down a level.

| Motion type | Examples | Motion |
|---|---|---|
| Walk, run | person, dog, chicken, dinosaur | steps, bounce |
| Roll | bicycle, car, ball | wheels turn, vehicle advances |
| Fly | bird, butterfly, plane | wing beat, glide |
| Swim | fish, turtle, boat | tail wave, bob |
| Crawl, hop | worm, snake, frog | stretch, jump |
| Alive but still | tree, flower, house | sway, grow, bloom |
| In the sky | sun, cloud, star | drift, rotate, twinkle |
| Default | unknown or invented thing | whole-body bounce, tilt, jump |

Levels: (1) whole cut-out moves; (2) parts move separately; (3) skeleton for clear limbs. LTX or an API only for scenes
that really need complex morphing; if it redraws strokes or adds objects, fall back to levels 1-3. Interactions (eat,
carry, touch, chase, transform) already exist in the pipeline. Limits: 2D only; part segmentation on children's strokes
is the main risk and leaves holes to patch. Proof: about 30 synthetic drawings across the eight types, measuring error-free
videos and the share reaching level 2 (can double as the missing recognition evaluation set of FEAT-093).

## SRS conflicts to settle with the owner

- FR-AI-05: story video must be image-to-video from the drawing and must **not** use PixiJS-style drawing animation.
- BR-45 / Q144: LTX-2.5 on Modal L40S per scene is the specified video pipeline; changing it needs an owner decision,
  an ADR and updated quality, cost, latency and safety gates.
- A cut-out or whiteboard direction therefore needs an SRS amendment before implementation.

## Facts from the live runs (2026-11-26)

- Warm Run 1: story about 10 s, video 14 min (queue for the GPU about 3.5 min, then about 2 min per 6 s scene).
- Scene 5 added a child who was not drawn. The first frame of that scene (keyframe: cut-out plus background) has no
  child, so the video model painted it during the scene.
- The keyframe left white paper residue between the bicycle spokes and the subject floated above the ground.
- Run 2 stopped at the activity step: the backend gate rejected two answers for `EXPLORATION_NOT_EXPLICIT`. Unfixed.
- The ground placement and no-new-people prompt changes are deployed but not verified in a live video.
