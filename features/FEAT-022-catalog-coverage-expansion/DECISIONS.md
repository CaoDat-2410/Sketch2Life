# FEAT-022 decisions

## Decision 1: Count selectable variants and families separately

The delivery target is 200-250 selectable, approved activity variants, not 200 copies of the same task. A variant has a unique immutable `activity_id` and `version`, and points to an `activity_family_id`. Coverage and diversity reports must expose both counts:

- selectable candidate count: distinct activity IDs after filtering;
- family count: distinct activity families after filtering;
- objective diversity: distinct learning objectives;
- material/context diversity: distinct material and context profiles.

A language-only rewrite is not a new activity variant. An age adaptation must change the expected child action, success observation, or complexity. A material variant must provide a real safe substitute and a changed setup path.

## Decision 2: Use a tiered coverage target

The catalog will not be expanded uniformly. The first delivery will classify concepts into demand tiers:

- Tier A, very common: animal, plant/flower, family/person, color, shape, movement, and number. Target 5-8 safe candidates per age band where the concept is applicable.
- Tier B, common: vehicle, house/home, weather, sun/moon/space, water, sound/music, and nature. Target at least 3 safe candidates per age band.
- Tier C, specialist or sparse: language/print, practical life, science, and less common sub-concepts. Target at least 2 safe candidates per age band, with explicit unavailable output if prerequisites or safety filtering remove all candidates.

The tier is metadata and can be revised from observed scene frequencies, not hard-coded into the matcher.

## Decision 3: Coverage is measured after policy filtering

An activity counts toward coverage only after age fit, safety, prerequisite, material, supervision, and production eligibility checks. Raw catalog size must never be reported as production coverage.

## Decision 4: Authored catalog only

AI may classify a scene and rank approved catalog entries, but it may not create or mutate an activity at runtime. New catalog records require provenance, review status, safety notes, age adaptation rationale, and a catalog revision before becoming eligible.
