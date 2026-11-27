# ADR-0027: one learning script, allow-listed interests, and where its facts come from

- **Status:** Proposed (FEAT-094 phase 4; the owner approved Plan Rev 2 and Amendment A on 2026-11-26)
- **Date:** 2026-11-26
- **Supersedes:** item 3 of ADR-0024 only where it excludes interests: allow-listed interest tags may now be sent.
  Profile identity and free text are still excluded.
- **SRS:** FEAT-063 v2.7-draft, unsigned. This ADR does not amend it.

## Context

The adult confirmed one text and the video spoke another, written by a second model pass. The video taught almost
nothing about the drawn thing.

## Decision

1. A Parent story is one learning script (5 to 7 scenes of 10 s). The video speaks it as confirmed; no second text pass.
2. Facts come from the pinned lesson notes, else an owner-approved knowledge card of the confirmed main subject, else
   a model draft reviewed by a second model pass. Facts nobody checked are labelled on the confirmation screen.
3. The story request may carry the age numbers, up to eight tags from the existing interest allow list, and card text.
4. The worker checks the script and rewrites it at most twice; the backend checks the same rules and refuses the story.
5. The script is stored inside the story content (no migration). Switch: `SKETCH2LIFE_STORY_LEARNING`.
6. Each rendered scene may be looked at by the text-and-vision worker. Mode `report` logs problem codes only; `enforce`
   renders a rejected scene again with a new seed at most twice and then fails the video. `report` is the local default
   until false positives are measured.

## Consequences

- Videos are longer (50 to 70 s), so rendering takes longer; the second writing pass is gone.
- A model-drafted fact can be wrong; the adult's review is the last check.
- Rules exist twice (worker and backend) and have to change together.
- The report mode adds one vision call per scene on the Qwen container.
