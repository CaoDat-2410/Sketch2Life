# FEAT-099 research, third pass: keep the child's strokes, move with physics, stay stable (2026-11-27)

## 1. The question

Which way of making the video keeps the child's drawing as drawn, moves it believably, and gives the same quality
every time?

## 2. Families of methods

| Family | Examples | Keeps the strokes | Physics | Stable | Cost per clip | Fits us |
|---|---|---|---|---|---|---|
| A. Video model from one picture | LTX-2.5 (today) | redraws every frame; shape can melt | learned, not guaranteed | no: seed decides | ~56 s L40S per 10 s scene (our measurement) | in use |
| B. Video model steered by poses | LTX guides (plan Rev 2), Motion Track IC-LoRA | better, still redrawn | from the poses | better, not guaranteed | as A | within the SRS |
| C. Optimise strokes with a video model | Live Sketch, AniClipart, SketchAnimator | rigidity terms keep stroke shape | from the video model | per-drawing optimisation | AniClipart: about 25 min on an RTX A6000 per clip (summary of the paper, not checked against the PDF) | no: too slow, vector input |
| D. 3D guided redraw | DrawingSpinUp, From Rigging to Waving | inpaints parts | from 3D motion | humanoid only | A100 class GPU | no: humans only |
| E. **Rig the drawing and move its own pixels** | Meta Animated Drawings (children's drawings, ARAP), our prototype | **yes: the pixels are the child's** | **exact: written as rules** | **same input, same output** | CPU seconds | needs an SRS change |

Sources: [AniClipart](https://arxiv.org/abs/2404.12347) ([code](https://github.com/kingnobro/AniClipart), no licence
shown on the repository page), [From Rigging to Waving](https://arxiv.org/abs/2509.06573),
[DrawingSpinUp](https://lordliang.github.io/DrawingSpinUp),
[Sketch animation survey](https://arxiv.org/pdf/2510.10218),
[Animated Drawings paper](https://arxiv.org/abs/2303.12741) (abstract only read; the repository is archived, MIT:
[repo](https://github.com/facebookresearch/AnimatedDrawings)). The FlipSketch paper could not be downloaded.

## 3. Pieces for family E

- **Finding parts.** The worker already makes a SAM 2.1 mask of the subject. Thin parts below the trunk are legs
  (image morphology; tried below). A vision model can add joint points. Trained animal pose models are not usable:
  SuperAnimal-Quadruped weights are for non-commercial research and trained on photographs
  ([model card](https://huggingface.co/mwmathis/DeepLabCutModelZoo-SuperAnimal-Quadruped),
  [DeepLabCut](https://github.com/deeplabcut/deeplabcut)).
- **Gait rules.** Each leg has a phase and a duty factor (share of the cycle on the ground). A walk keeps the duty
  above 0.5, a trot uses diagonal pairs at 0.5; the swinging foot follows an arc with zero speed at lift-off and
  touch-down ([gait parameters](https://arxiv.org/pdf/2412.09440), [stability](https://arxiv.org/pdf/2410.09336),
  [2D foot path and leg angles](https://wikidocs.net/417781); robotics sources).
- **Bending without seams.** Linear blend skinning on a grid mesh, or as-rigid-as-possible deformation; an MIT Python
  version is in Animated Drawings (`animated_drawings/model/arap.py`); libigl covers more (licence to be checked)
  ([search result](https://libigl.github.io/libigl-python-bindings/tut-chapter3),
  [ARAP walkthrough](https://www-ui.is.s.u-tokyo.ac.jp/~takeo/papers/takeo_jgt09_arapFlattening.pdf)).

## 4. Our own test (throwaway, CPU, one synthetic drawing)

`evidence/part_split_prototype.py` and `evidence/walk_prototype.py`; result `evidence/walk_preview.mp4`.

- The four legs of the deer were found with image morphology and turned about their hips in a four-beat walk. A foot on
  the ground follows a formula meant to hold it still; it uses the average leg length, so a longer or shorter leg
  slides a little (not measured).
- 6 s at 768x512 rendered in 19 s on this PC's CPU, with unoptimised Python image calls. No GPU, no model.
- In sampled frames the strokes, face and antlers are unchanged and no part deforms.
- Faults seen: a small gap and a loose stroke at one hip; the paper behind the subject is filled by repeating nearby
  pixels (the product would paste onto the clean painted background instead).
- Limits of the evidence: one clean side-view drawing, a colour mask made for this drawing instead of the SAM mask, the
  grass in front of the hooves is not treated as a foreground layer, and the owner has not judged it.

## 5. Reading

For **stable** quality the subject should be moved by rules on its own pixels (family E). A video model redraws the
child's picture each time, so its quality can only be filtered, not guaranteed. A model still helps where change is
harmless: painting the background (already so), and optionally gentle background life.

The conflict: SRS 2.7-draft names LTX image-to-video for the scene clips (§6.2.2 stage 8, Q144) and lists drawing
animation of the PixiJS kind as out of scope (§§ around lines 106 and 172; AC-07). Family E needs the owner's decision
and an SRS amendment.
