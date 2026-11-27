# Research: where child-friendly drawing guides can come from (2026-11-27)

Method: web search and a web reading tool. Several items come from search summaries, not from reading the whole source;
they are marked "summary".

## 1. How young children draw

- Typical shape copying: circle about 3 years, cross 3 to 4, square about 4, triangle about 5, diamond about 6; ages vary
  widely ([MSD Manual](https://www.msdmanuals.com/professional/multimedia/table/developmental-milestones),
  [HSE](https://www2.hse.ie/babies-children/checks-milestones/developmental-milestones/3-5-years)) (summary).
- No study was found that shows shape-building teaches preschoolers better than copying line art, or that tests animated
  strokes for drawing at this age. Animation helps adults learn changes over time
  ([Ploetzner et al.](https://link.springer.com/article/10.1007/s11251-021-09541-w)) (summary). The choices of this plan
  are design judgements to be checked with people, not proven facts.

## 2. Ready-made vector or stroke data

| Source | Fit |
|---|---|
| [Quick, Draw!](https://github.com/googlecreativelab/quickdraw-dataset), CC BY 4.0, 345 categories, human strokes | quick doodles of uneven quality, need filtering; no `chicken` category; stroke order in the simplified files is not guaranteed by the README |
| Icon sets (OpenMoji CC BY-SA 4.0, Lucide ISC, and similar) | made to be looked at: long paths, no teaching order |
| OmniSVG's MMSVG data, CC BY-NC-SA 4.0 | non-commercial, filled icons |
| Openclipart catalog on Modal (about 1,900 guide-eligible files, FEAT-088) | clip art, the cause of today's double lines |

No open dataset was found with step-by-step, child-level drawing lessons.

## 3. Can a "skill" make Qwen 3.8 draw SVG reliably?

- **No installable skill was found for Qwen 3.8.** "Agent skills" for SVG are instruction files for coding agents
  ([example](https://github.com/upbrew-tech/svg-creator-skill)); their ideas (fixed viewBox, build part by part, render
  and check) can be written into our own prompt and checks. None reports tests on Qwen.
- **Adapters (LoRA)** exist for Qwen2.5-Coder, Qwen3-8B and Qwen3.5 small models, not for Qwen 3.8 27B, and an adapter
  only loads onto the model it was trained on. Example: [artamrj/SVGen](https://github.com/artamrj/SVGen) draws 24 px
  line icons with a 0.5B to 1.5B base and reports that long precise shapes fail.
- **A dedicated model:** [OmniSVG 4B](https://huggingface.co/OmniSVG/OmniSVG1.1_4B) (Qwen2.5-VL-3B based, Apache-2.0
  weights, 16 GB GPU memory). It would be a second model on its own GPU; its page states nothing about line drawings or
  a drawing order.
- **Measured on off-the-shelf Qwen3.5 9B and 27B** ([arXiv 2608.28678](https://arxiv.org/html/2608.28678v1), two-page
  poster): text-to-SVG compiled 0.837 of the time in one call; constraining the output raised compile rates in the
  weaker pipelines but generally lowered picture quality; refining from the rendered picture did not help consistently.
- **Stroke-by-stroke drawing by a language model** on a numbered grid works for simple sketches
  ([SketchAgent](https://yael-vinker.github.io/sketch-agent/), CVPR 2025; the page does not name an open model).

## 4. Conclusion

1. Do not ask the model for free SVG. Ask for a **drawing recipe**: a short list of named shapes with grid positions, in
   a fixed JSON schema; our code turns it into paths. A broken path or a stray element is then impossible, and the
   geometry rules can be checked by code. The quality of the picture itself is still not guaranteed.
2. Our "skill" is the recipe vocabulary, good examples from a hand-written library, the code checks and a recognition
   check, all under our control.
3. Common subjects come from a hand-written, reviewed library. AI is only for topics the library lacks, and stays a
   draft until an adult accepts it.
4. Measure Qwen 3.8 on this recipe format before building the product route.
