# FEAT-022 context

## Problem

The current catalog is a valid MVP baseline but is too narrow for meaningful personalization. The current evidence reports 100 activity profiles, 48 unmapped profiles, 33 concept-age gaps, and approximately 0.2326 coverage across mapped concept-age pairs. A semantic match can therefore be technically valid while still collapsing many children into the same recommendation.

## User-approved direction

- Expand toward 200-300 selectable catalog variants, with 200-250 as the first delivery target.
- Measure concept x age coverage, not only total activity count.
- Cover the four age bands: 0-3, 3-6, 6-9, and 9-12.
- Use shared activity cores with age adaptations, material variants, and challenge variants where appropriate.
- Every selectable activity must be curated, safety-reviewed, and versioned. Runtime AI must not invent activities to hide a catalog gap.
- Preserve explicit unavailable results for age bands that do not have a safe, approved candidate.
- Improve diversity so a common concept does not deterministically select one activity.
- Keep PixiJS runtime, video generation, production human gates, UI integration, and caregiver persistence outside this feature.

## Governing constraints

- Domain rules remain independent of providers, storage, queues, and UI.
- Cross-feature data travels through versioned contracts.
- Originals and provenance are preserved.
- Firebase remains authentication-only.
- No credentials, real child data, or external handbook originals may enter the repository.

## Activity preparation and printable-asset follow-up — 2026-09-23

- Owner requested a separate preparation layer for activities that need printed cards, matching
  boards, sequence sets, worksheets or other guide-prepared materials.
- The first step is classification only: every selectable activity must be marked as
  `NO_PRINTABLE_ASSET`, `PRINT_RECOMMENDED` or `PRINT_REQUIRED`, with a Vietnamese guide note and
  planned printable asset kind where applicable.
- PDF/A4 is the future parent/guide print format; editable SVG/PNG sources may be retained. Actual
  files, asset review, download endpoints and guide UI are deliberately deferred until the
  classification report is reviewed.
- The detailed draft is
  `plan/ACTIVITY_PREPARATION_ASSET_CLASSIFICATION_PLAN.md`; it was approved on 2026-09-23 and
  the classification/contract/metadata slice is implemented. Printable files, asset review,
  download endpoints and guide UI remain deferred.
