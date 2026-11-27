# FEAT-097: drawing guides a child can follow

- **Status:** AWAITING_APPROVAL (plan `plan/PLAN_REV1.md`). No product code changed.
- **Opened:** 2026-11-27, from the owner's chat: the guide strokes of the SVG engine do not suit children.
- **SRS:** FEAT-063 v2.7-draft: §6.2.1, BR-42, BR-46, FR-P-11, FR-AI-14, FR-AI-15, AC-44, AT-18.

## Current engine (read 2026-11-27)

- `application/services/parent_svg_guide.py` looks a topic up in three local packs, in this order: Openclipart
  (butterfly, turtle), OpenMoji (butterfly, turtle, dog), Arcadia (chicken). Any other topic answers 404.
- The guide cuts the source picture's own paths into 4 to 8 steps and keeps their geometry exactly.
- The app (`ProgressiveSvgGuide.tsx`) draws earlier strokes dark and new strokes blue and solid; all new strokes of a
  step animate almost together. There is no start point or direction. The app always asks for `difficulty: beginner`.
- The request contract already has two levels: `beginner` and `simple`.
- The only AI route for guides on this branch is a FLUX picture worker (`flux_image_app.py`), which the SRS excludes.

## Problems seen (`evidence/baseline/`)

| Pack | Strokes | What goes wrong |
|---|---|---|
| Openclipart, used first | 35 to 39 | every line is drawn twice (outlines of filled shapes), tiny scattered pieces |
| Arcadia chicken | 77 | realistic feathers, 21 new strokes in one step |
| OpenMoji | 6 to 12 | one long outline holds half the animal; in the turtle some instructions name a different part than the highlighted one |

## Owner decisions (chat, 2026-11-27)

1. Ages 3 to 10 with two levels.
2. Shape-building style (A) for the younger level, simple outline style (B) for the older level.
3. Start dot with arrow, and stroke-by-stroke animation. Voice and finger tracing were not chosen.
4. Source: undecided; the owner asked for a recommendation (datasets or AI generation, and whether a skill can make
   Qwen draw SVG more reliably). See `research/SVG_GUIDE_RESEARCH.md`.
