# FEAT-099 plan, revision 3: move the child's own drawing by rules (rig engine)

Replaces Rev 2 for the video part if the owner chooses it (section 1). Research:
`../research/STABLE_MOTION_RESEARCH.md`. Evidence: `../evidence/walk_preview.mp4`. The drawing-guide part is Rev 1
section 3, unchanged. Nothing is built until approved.

## 1. The owner's decision

| Choice | Stable | Keeps the strokes | GPU per 50 s video | SRS |
|---|---|---|---|---|
| **R. Rig engine (this plan, recommended)** | yes: same input, same frames | yes | background painting only | **needs an amendment** |
| G. Video model guided by poses (Rev 2) | better than today, not guaranteed | redrawn by the model | as today | no change |

R changes SRS 2.7-draft: §6.2.2 stages 7 to 9 (LTX image-to-video per scene, Q144), the out-of-scope lines on drawing
animation (PixiJS kind), AC-07 and the technology table. The amendment text is written first and signed off by the owner
before code that depends on it is merged. LTX stays in the code behind a switch for rollback.

Honest limits of R: the motion looks like a cut-paper puppet; the subject cannot turn round or show a side that was not
drawn; drawings whose parts cannot be separated move only as a whole.

## 2. Flow

1. Preparation (GPU, as today, during script review): painted background; SAM mask of the subject. **New outputs:** the
   background without the subject, and the masks.
2. Rigger (CPU): cuts parts, finds joints, checks them, picks a tier.
3. Motion planner (CPU): from each scene's sentences and their voice timings, which action runs when.
4. Renderer (CPU, video worker): layers every frame at 1280x720, 24 fps.
5. Assembly, captions, part labels, playback: as today.
6. Quality gates (CPU): a scene that fails drops one tier and is rendered again. No GPU.

## 3. Components

### 3.1 Rig contract `sketch2life.drawing-rig.v1`

Body type; tier; for each part: name (`trunk`, `head`, `leg_1..n`, `tail`, `wing`, `fin`, `wheel`, `eye`), mask, parent,
pivot, angle limits, draw order; ground line; facing; checks passed; engine version. Stored with the run's lineage and
deleted with it.

### 3.2 Rigger

| Tier | When | What can move |
|---|---|---|
| A full | parts found and all checks pass | legs, wings, fins or wheels; head; tail |
| B partial | only some parts pass | head, tail, breathing; the body travels as a whole |
| C whole | everything else | travel, bob, hop, sway of the whole cut-out; **always available** |

Part finding, in order: shape rules on the mask (thin appendages below or beside the trunk; circles for wheels), then
joint points asked from the vision model as hints where rules are unsure. Checks: part count for the body type, minimum
size, legs touch the ground line, pivot inside the overlap with the parent, no part covering more than half the subject.
Body types in build order: four legs (side view), two legs and wings (bird), fish, wheels, plant, other (tier C).

### 3.3 Motion catalogue and physics

| Action | Spoken words that choose it | Rule |
|---|---|---|
| walk | đi, bước, bò | leg phases a quarter apart, duty 0.7; a standing foot does not move (travel speed = stride / (duty x period)); body bob at twice the step rate |
| run | chạy | diagonal pairs, duty 0.5, longer stride, small flight height |
| hop, jump | nhảy | parabola under constant gravity, squash at most 5% on landing |
| look | nhìn, ngó, quay đầu | head about the neck pivot, at most 12 degrees, eased |
| nod, eat | ăn, cúi | head at most 15 degrees; never to the ground |
| fly, swim | bay, bơi | wing or fin turning with a body wave; path with ease in and out |
| roll | lăn, chạy xe | wheel angle = distance / radius (no slipping) |
| rest | đứng, nằm, ngủ and anything else | breathing (1%), tail and ears as damped springs, blink only if eyes were found cleanly |

The story writer picks an action id from this list for each scene (fixed choices in its schema); the planner times it to
the sentence that names it. Secondary parts (tail, ears, antlers) follow a damped spring driven by the body's motion.
While the voice names a part, that part gets a soft outline glow (the learning point made visible).

### 3.4 Renderer

Layers: background; far parts; trunk; near parts; contact shadow; foreground strip of the ground in front of the feet;
label and glow. Parts bend about joints with a mesh and blended bone weights, so no gap opens; only the pixels of the
child's drawing are used for the subject. No random numbers. Libraries: NumPy and OpenCV (headless), added to the video
worker; the MIT as-rigid-as-possible code of Animated Drawings is the fallback if blended weights look poor.

Speed target: a 50 s video in at most 90 s of CPU (the prototype took 19 s for 6 s at a smaller size, without OpenCV and
drawing whole pictures for every part).

### 3.5 Pipeline integration

- `SceneRenderPort` gets a rig implementation in the video worker; `SKETCH2LIFE_VIDEO_ENGINE=rig|ltx` (default `rig`
  only after acceptance).
- Preparation output and its review-time cache gain the background and masks.
- Voice first (FEAT-098) already gives each sentence's time; scene length follows the voice as now.
- No LTX load, no render warm-up when the engine is `rig`.

## 4. How stable quality is enforced

| Gate (automatic, per scene) | Limit |
|---|---|
| Subject pixels taken from the drawing (outside a 2 px feathered edge) | 100% |
| Standing foot movement | at most 1 px a frame |
| Holes around joints | none larger than 8 pixels |
| Subject inside the frame | every frame |
| Same input rendered twice | identical frames |
| Render time per scene | at most 18 s |

A failed gate drops the scene one tier. The tier of every scene is recorded and shown in the run report.

**Golden set:** 12 synthetic drawings (4 four-legged, 2 birds, 2 fish, 2 vehicles, 2 plants or objects) with saved masks.
Every change renders the set; frame differences are reviewed. No real child's drawing is stored in the repository.

## 5. Work packages and order (one build; checks on the CPU as it goes)

| # | Package | GPU |
|---|---|---|
| W0 | SRS amendment draft; owner sign-off | 0 |
| W1 | Rig contract, rigger (four legs and tier C), gates, tests | 0 |
| W2 | Renderer (mesh warp, layers, glow, labels), determinism and speed | 0 |
| W3 | One job to make SAM masks and backgrounds for the golden set, saved as test fixtures | about 5 L40S min |
| W4 | Other body types, motion catalogue, planner, writer's action choice | 0 |
| W5 | Preparation outputs, engine switch, assembly integration | 0 |
| W6 | Drawing guide: one level (Rev 1 section 3) | 0 |
| T1 | The owner watches the golden-set clips | 0 |
| T2 | One video through the app | about 4 L40S min |

GPU in total: about 10 L40S minutes (cap 15, about 0.5 USD). Per product video the GPU would only paint backgrounds and
check them (estimate 2 to 3 min instead of today's 8 to 10; measured in T2).

## 6. Acceptance

1. Golden set: at least 10 of 12 drawings reach tier A or B; none shows a broken part, a hole at a joint or a sliding
   foot (gates), and the owner accepts the clips.
2. Walking and running scenes show alternating legs and forward travel.
3. The subject's strokes are the child's (pixel gate).
4. One app video: video request to ready at most 3 minutes with a reviewed script; length 30 to 90 s; voice, captions
   and labels as today.
5. `ltx` engine still selectable and its tests pass; stored stories load.
6. Drawing guide: no 3-to-5 choice.
7. Tests written first; existing tests show no new failure.

## 7. Risks

- Only one drawing has been tried. Messy outlines, front views and crossed legs may fall to tier C; the golden set shows
  how often before the app test.
- Cut-paper motion may read as less lively than a video model on good scenes; background life (clouds, grass) is a later
  option.
- Hidden areas behind moving parts are filled from the background, not redrawn: gaps can show where a leg overlapped the
  body.
- The amendment may be refused; then Rev 2 (choice G) applies.
