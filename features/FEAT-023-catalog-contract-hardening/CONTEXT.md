# FEAT-023 context

## Scope

Harden the FEAT-022 curated catalog and recommendation contract after review of
a real backend workflow result. The follow-up addresses age-specific pedagogy,
missing butterfly coverage, explainability, demo/production governance, and
multi-day activity duration without adding UI, PixiJS, video generation, or
runtime AI activity authoring.

## Baseline facts

- FEAT-022 is pushed as commit `3c71169`.
- The current expansion has 200 authored variants across 50 families.
- The merged selectable catalog has 300 profiles.
- `FAM-PLANT-CARE` currently applies one family-level objective to all age variants.
- `ANIMAL_BUTTERFLY` has no current semantic profile.
- Current expansion records are `DEMO_ELIGIBLE` and `production_eligible=true`.
- Current duration output cannot represent a multi-day observation span.

## Non-goals

- No UI or mobile contract exposure for debug ranking data.
- No production approval of the expansion in this feature.
- No deletion of the 100-profile rollback catalog.
- No AI-generated activities at runtime.

## Implementation state

- Revision-2 loader is active by default as
  catalog-2026-09-expansion-2.
- Revision-1 rollback remains loadable explicitly through the curated loader.
- Offline evidence is recorded under this feature's evidence/metrics/ and
  uses the fixed 100-case corpus under fixtures/.
- Real-AI Lightning validation is intentionally still pending and is the only
  release-candidate gate not executed in this workspace.
