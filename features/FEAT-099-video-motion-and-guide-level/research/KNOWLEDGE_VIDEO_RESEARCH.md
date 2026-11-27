# FEAT-099 research, fifth pass: motion alone teaches nothing; show what is said (2026-11-27)

## 1. The question

If the subject only moves, how does the video give knowledge? Can this be done on the CPU alone?

## 2. Findings on learning

- Storybook meta-analysis, 43 studies, 2,147 children (3 to 10 years): technology added a small benefit (comprehension
  g+ 0.17, expressive vocabulary 0.20). Animation, music and sound (not separable) helped; interactive hotspots and
  games distracted. For multimedia-only stories against print the summary reports g+ 0.39 on comprehension. The
  explanation given: picture and words showing the same thing at the same time lower the load; extras compete
  ([Takacs, Swart and Bus 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4647204/); the effect sizes beyond the
  abstract come from an automated reading of part of the article).
- Visual cues that point at what is talked about help children, most when attention is weak
  ([study](https://real.mtak.hu/225238/1/1-s2.0-S0022096525001262-main.pdf)); signalling in general d = 0.38
  ([review](https://link.springer.com/article/10.1007/s10648-009-9098-7), figure from a search summary).

**Design rule drawn from this:** each spoken fact gets one picture event that shows it, at the moment it is said, and
nothing that competes with it. (Our video has narration and captions, and by SRS no music or sound effects.)

## 3. What the present video does with knowledge

The video model receives one sentence of motion in English. Facts such as "antlers are shed with the seasons" or "fish
breathe with gills" are only spoken; nothing on screen can be relied on to show them. In the FEAT-098 video the fact
about fast running was shown by a deer with still legs.

## 4. A third prototype: three facts shown, CPU only

`evidence/knowledge_prototype.py`, result `evidence/knowledge_preview.mp4` (15 s at 768x512, 36 s of CPU), the
synthetic deer drawing:

| Fact | What the screen does |
|---|---|
| A deer has four legs | the legs are lit and numbered one by one, with the count in the caption |
| Antlers are shed in late winter and grow back | snow, the child's own antlers fall under gravity; in spring they grow from the head; a three-season marker |
| Deer eat young leaves | a leaf sprig arrives, labelled; the deer steps up; the leaves go one by one |

In sampled frames all three read without sound. Parts (four legs, two antlers) were found from the drawing's shapes;
the facts, the choice of picture and the timing were written by hand; the leaf was drawn by code. One drawing; not
judged by the owner or any child. Antler timing follows wildlife agency pages
([Virginia DWR](https://dwr.virginia.gov/blog/all-about-antlers/),
[Mississippi State](https://msudeer.msstate.edu/growth-cycle.php)); months differ by species and place.

## 5. Where pictures come from, and the limit of "CPU only"

| Source | Used for | GPU | Accuracy |
|---|---|---|---|
| The child's own parts | name, point, count, grow, fall, move | none (mask once) | exact: it is the drawing |
| A library of crayon-style pictures made once and checked | leaves, flowers, nests, water, tools, places | once, then none | checked once by a person |
| New pictures for custom subjects and lessons | anything not in the library | a few stills per video | must be checked before use |

A CPU can compose, move and time pictures. It cannot invent a picture it does not have: an image model is needed for
new objects (about 6 s a picture on our L40S, from the FEAT-098 preparation times). Stills are far safer than generated
video: they can be checked, redone and shown to the adult before any video exists.

Checking generated pictures: question-answering checks ([TIFA](https://arxiv.org/pdf/2303.11897)) and fact rubrics
([T2I-FactualBench](https://arxiv.org/html/2412.04300v3)) exist; image models are still weak at counting and spatial
relations (TIFA), so counts must use the drawing's parts and a person must approve new pictures.

Licence note: a search reports that the FLUX 3 Image Klein weights (the background model in use) are under a "FLUX
Kommunity License", and FLUX.2 klein 4B under Apache 2.0
([repo](https://github.com/black-forest-labs/flux-3-image-klein),
[BFL docs](https://docs.bfl.ml/flux_2/flux2_overview)). To be checked on the model cards before a larger use; this
predates FEAT-099.

## 6. How far templates reach

The 40 knowledge cards hold 241 facts: 40 "what it is", 161 about a part and what it does, 40 about use or role. Eight
picture templates cover these shapes (plan Rev 5). Some facts are abstract ("body heat follows the surroundings") and
need a diagram or stay mostly spoken; the plan counts them instead of pretending.
