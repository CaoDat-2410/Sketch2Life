# FEAT-099 research, fourth pass: one method for every topic (2026-11-27)

## 1. Question from the owner

Judge the video quality. Legs and gaits only serve animals: what about vehicles, space and the other topics? One method
that works for all of them, with stable quality, and fast.

## 2. Quality as judged now

The author's judgement from sampled frames, 1 to 10. Not user testing; the owner has not scored them. The two columns
are not a controlled comparison (different length, picture and subject).

| Criterion | Video model (app video, FEAT-098) | Rig prototype (deer walk) |
|---|---|---|
| Keeps the child's drawing | 6: redrawn, paler, the tree comes apart (already in the prepared picture) | 9: the child's pixels; a small gap at one hip |
| Movement matches the words | 3: running scene with still legs | 7: real steps; one action only |
| No deformation / same result again | 4: one of five scenes badly bent; depends on the seed | 8: same frames every run; one drawing tried |
| Scene beauty and liveliness | 8: rich painted backgrounds | 3: bare paper, nothing else moves |
| Helps learning (shows what is named) | 5: part names in two scenes | not built |
| Speed and cost | 4: 5 min 54 s, about 8 to 10 L40S minutes | 9: CPU seconds |

Neither is good enough alone: the first is pretty and unreliable, the second reliable and plain.

## 3. How many subjects need legs

`evidence/classify_topics.py` sorts the app's 162 suggested subjects (18 topics) by the movement they need. The sorting
is a hand judgement; numbers in `evidence/topic_families.json`.

| Family | Subjects | Own part motion possible |
|---|---|---|
| stands still (cup, shirt, school bag, house) | 51 | no |
| legs | 28 | yes |
| wheels | 12 | yes |
| light (sun, moon, lamp, traffic light) | 12 | mostly effects |
| play and music | 12 | few |
| swim | 9 | yes |
| plant | 9 | sway |
| moves along a path (aeroplane, boat, rocket, kite) | 8 | whole object |
| wings | 7 | yes |
| weather | 7 | effects |
| spins | 5 | yes |
| crawls | 2 | whole object |

About 61 of 162 (38%) can use moving parts (legs, wings, swim, wheels, spin). The other 62% never needed a gait.
Clothes 9 of 9, kitchen 8 of 9, school 8 of 9 stand still. A design built on skeletons would serve one third.

## 4. A second prototype: four subjects, one engine

`evidence/universal_prototype.py`, result `evidence/universal_preview.mp4` (CPU, 480x480 per subject, parts named by
hand where a vision model would answer).

| Subject | What moved | Seen |
|---|---|---|
| Butterfly | wings narrow and lift, floats | clean |
| Rocket (drawn from the app's recipe) | shakes, lifts off, flame, smoke, stars | clean, flat cartoon effects |
| House (from the recipe) | drawn stroke by stroke, door circled, camera moves in | clean; works for anything that stands still |
| Bicycle | rides with passing road and dust | clean |

**The bicycle is the important result.** Turning its wheels broke the picture three times: the wheels are drawn as
ellipses, the frame crosses them and the pedals sit inside them. A check (turn the wheel 40 degrees: does the tyre
stay where it was?) scored 0.4 against a limit of 0.75, so the wheels were left still and the whole bicycle rode. A
part motion must prove itself before it is used; the whole-object motion underneath is always clean.

Time: 12 s of CPU for four 6 s clips.

## 5. Outside work

- Finding parts by name: SAM 3 takes short noun phrases such as a part name, 848M parameters, GPU, "SAM License"
  (no explicit commercial clause; gated weights), no statement about drawings
  ([repo](https://github.com/facebookresearch/sam3), [paper](https://arxiv.org/html/2511.16719v2)). Our stack already
  has a vision-language model (boxes) and SAM 2.1 (mask from a box), which needs no new licence.
- A language model planning how parts of a still illustration move, then code rendering it, is an established pattern
  for vector art ([Keyframer](https://machinelearning.apple.com/research/keyframer),
  [Decomate](https://arxiv.org/pdf/2511.06297)).
- Pointing at what is being talked about helps learning: a meta-analysis reports an effect of d = 0.38 for signalling
  cues, larger with animation ([review](https://link.springer.com/article/10.1007/s10648-009-9098-7), figure as
  reported by the search summary of Alpizar et al. 2020, not checked against the paper); movement that competes with
  the point can hinder
  ([children's study](https://real.mtak.hu/225238/1/1-s2.0-S0022096525001262-main.pdf)).
