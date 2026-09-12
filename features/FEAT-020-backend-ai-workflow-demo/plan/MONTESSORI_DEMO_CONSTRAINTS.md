# FEAT-020 Demo Safety and Accessibility Constraints

**Status:** confirmed demo baseline; grouped plan milestone
**Date:** 2026-09-12

These constraints apply to the demo context only. The selected activity’s catalog safety rules remain authoritative and may make the run stricter. The workflow must never weaken an activity-specific prohibition to force a result.

## Baseline constraints for every age band

- `ADULT_SUPERVISION_REQUIRED`: an adult/guide is present for the entire activity.
- `NO_OPEN_FLAME_OR_HIGH_HEAT`: no fire, hot liquid, heated tools, or electrical heating element.
- `NO_SHARP_TOOLS_IN_UNSUPERVISED_FLOW`: scissors, blades, needles, and pointed tools are blocked unless the catalog explicitly permits them with adult handling.
- `STABLE_WORK_SURFACE`: activity is performed on a stable, uncluttered surface; no climbing or balancing setup.
- `LOW_MESS_AND_WASHABLE`: prefer washable, non-toxic, easy-to-clean materials when the catalog allows equivalent choices.
- `NO_INGESTION_INTENT`: materials are not food or medicine and must not be presented as edible.
- `NO_REAL_CHILD_DATA`: demo image/audio and evidence remain synthetic and contain no child identity data.

## Age-sensitive demo constraints

### `0-3`

- adult remains within arm’s reach;
- no loose small parts or detachable pieces that could create a choking risk;
- one-step-at-a-time instruction with visual and spoken cue;
- use only large, washable, non-toxic materials approved by the selected catalog record.

### `3-6`

- adult remains present and handles any restricted tool or substitute;
- instructions are short, concrete, and limited to one action per step;
- avoid flashing, rapid motion, or excessive simultaneous decorative assets.

### `6-9`

- adult remains available for setup, safety check, and completion;
- allow more than one ordered step only when the selected readiness criteria pass;
- provide a visible learning objective and material checklist.

### `9-12`

- adult remains available for safety review and real-world handoff;
- allow layered steps only when the selected activity record and readiness criteria permit them;
- keep visual motion optional and avoid using animation as a substitute for the hands-on activity.

## Accessibility defaults

- provide both a short visual cue and a plain-language spoken/text cue;
- avoid relying on color alone to communicate safety, state, or success;
- allow reduced-motion render intent;
- preserve high contrast and readable labels;
- expose materials and supervision as structured fields, not only icons.

These are demo defaults pending final review against each selected catalog record; they are not a replacement for professional safety or accessibility review.
