# FEAT-099 plan, revision 4: a layered video engine for every topic

Replaces Rev 3 if the owner chooses the engine route (it still needs the SRS amendment of Rev 3 section 1; Rev 2 stays
the choice within the SRS). Research: `../research/ALL_TOPICS_RESEARCH.md`. The drawing-guide part is Rev 1 section 3.
Nothing is built until approved.

## 1. Principle

Quality has a floor that every subject reaches, and extras that must prove themselves.

| Layer | What it does | Applies to | May fail? |
|---|---|---|---|
| L1 Teaching | drawing appears stroke by stroke; the named part is circled, glows and gets its label; camera moves in, pans or follows | every subject | no |
| L2 World | the painted background (as today) in two or three depth layers that shift with the camera; effects chosen by place: clouds, stars, rain, bubbles, leaves, dust, steam, smoke, flame, sparkles | every scene | no |
| L3 Whole object | travel, float, bob, hop under gravity, swing, sway, spin, squash up to 5% | every subject with a mask | no |
| L4 Parts | walk and run, wing beat, fin and tail wave, wheels, hands of a clock | only parts that pass their check | yes: falls back to L3 |

Nothing redraws the child's subject. No video model.

## 2. Motion profiles

- **Suggested subjects (162):** a table in the repository gives each its family, allowed actions, effects and part
  recipe. Hand-made from `evidence/topic_families.json`, reviewable like the knowledge cards.
- **The adult's own subject:** the vision model answers family, parts (boxes) and facing from fixed choices; anything
  unsure becomes "stands still", which is a complete video (L1 to L3).
- **The story writer** picks each scene's action and effect from the profile's choices, matching the sentence spoken.

| Family | Floor (L3) | Extra (L4) | Typical effects |
|---|---|---|---|
| legs | travel with bob, hop, look (tilt) | gait, tail | dust, grass, leaves |
| wings | float on a curved path | wing beat | petals, sparkles, night glow |
| swim | glide with a slow wave | fin, tail, arms | bubbles, light rays |
| wheels | drive with passing road | wheels (ellipse fitted) | dust, passing scenery |
| path | follow a path with thrust or wind | propeller, flame | smoke, clouds, wake |
| light, weather | pulse, drift | rays, drops | glow, rain, rainbow reveal |
| spin | turn about its centre | blades, hands | motion lines |
| plant | sway from the foot | leaves, flower opening | wind, pollen |
| play, music | bounce or swing on the voice's beat | keys, strings | note shapes |
| stands still | small settle, presence | none | camera, reveal, part circles |

## 3. Pipeline

1. During script review (GPU): background painting (as today), subject mask (SAM 2.1), part boxes for L4 (vision model,
   only for families that have parts).
2. CPU, video worker: rig and checks, scene direction (camera, action, effects timed to the voice), render 1280x720 at
   24 fps, voice, captions, assembly.
3. Switch `SKETCH2LIFE_VIDEO_ENGINE=layers|ltx`; LTX stays for rollback.

## 4. Keeping quality stable

| Gate | Limit | If it fails |
|---|---|---|
| Subject pixels come from the drawing | all but a 2 px edge | stop the scene, use L3 |
| Part check (wings, legs: coverage and joint holes; wheels: tyre stays after a turn at 0.75 or more; gait: a standing foot moves at most 1 px a frame) | per part | part does not move (L3) |
| Subject inside the frame, label not over the subject | every frame | smaller motion or move label |
| Contrast of subject against background | measured | lighten or outline behind the subject |
| Same input twice | identical frames | build error |
| Render time | 90 s CPU for a 50 s video | fewer particles |

**Golden set:** two synthetic drawings for each of the 18 topics (36), made from the app's drawing recipes and the
synthetic drawings already used, with saved masks and backgrounds. Every change renders contact sheets of all 36.

## 5. Work packages (one build, checked on the CPU as it goes)

| # | Package | GPU |
|---|---|---|
| W0 | SRS amendment draft; owner sign-off | 0 |
| W1 | Engine core: layers, camera, timing to the voice, determinism, speed, tests | 0 |
| W2 | L1 teaching and L3 whole-object motion; effects library; profiles for all 162 subjects | 0 |
| W3 | One job making masks and backgrounds for the golden set | about 8 L40S min |
| **T1** | **The owner watches the golden set with L1 to L3 only** — the floor for every topic | 0 |
| W4 | L4 parts, in order of how many subjects they serve: legs, wheels, swim, wings, spin; gates | 0 (a second mask job only if parts need it, about 4 min) |
| W5 | Writer and profile integration, preparation outputs, engine switch, assembly | 0 |
| W6 | Drawing guide: one level (Rev 1 section 3) | 0 |
| T2 | Golden set with L4; then one video through the app | about 4 L40S min |

GPU in total: about 12 to 16 L40S minutes, cap 20 (about 0.7 USD). Per product video: background painting, masks and
checks only (estimate 2 to 3 L40S min; measured in T2).

## 6. Acceptance

1. All 36 golden drawings give a complete video at L1 to L3 with every gate passed.
2. The owner accepts the golden set: floor first (T1), extras second (T2).
3. At least half of the golden drawings whose family has parts reach L4; every other one falls back cleanly.
4. One app video: video request to ready at most 2.5 minutes with a reviewed script; 30 to 90 s; voice, captions and
   labels as today.
5. `ltx` engine still selectable; stored stories load; existing tests show no new failure.
6. Drawing guide: no 3-to-5 choice.

## 7. Risks and what this is not

- It looks like a well-made animated picture book, not a film: no new poses, no turning round, simple effects.
- Parts will often fail on real drawings (the bicycle did); the floor must therefore be good on its own. T1 tests that
  before any part work.
- Masks from SAM on crayon drawings and part boxes from the vision model are unmeasured on this variety.
- 162 profiles are manual work and need the owner's review.
- The SRS amendment may be refused.
