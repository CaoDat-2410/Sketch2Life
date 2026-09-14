# FEAT-022 validation

Date: 2026-09-14

## Commands

- Curated loader smoke check: 300 templates and 300 V2 profiles loaded.
- Targeted catalog and semantic suite: passed.
- Catalog expansion suite: 6 passed, including objective-age and material-substitute gates.
- Full backend suite: exit code 0.
- Ruff on changed files: passed.
- Strict mypy on changed modules: passed.
- Repository security validation: passed.
- Harness validation: passed after evidence paths were added.

## Behavior verified

- Legacy MVP loader remains 100 activities.
- V2 expansion loader returns 300 activities: 100 baseline plus 200 authored variants.
- The 200 authored variants are 50 families x 4 age bands.
- Activity IDs are unique and do not collide with the baseline.
- Every authored family covers 0-3, 3-6, 6-9 and 9-12.
- Activity family, variant, catalog revision and provenance are carried into V2 semantic profiles.
- Tiered concept-age report has no remaining scoped gaps.
- Objective-age report covers 13 objectives across 52 objective-age pairs with at least two candidates per pair and no gaps.
- Existing V2 workflow regression now succeeds for all four age bands with the expanded catalog.
- Seeded selection and family diversity reporting are covered by unit tests.

## Explicit limitation

This evidence is contract-level and local. A real-model Lightning AI run with the Qwen VLM and Whisper runtime still needs to be executed in the target Lightning Studio environment. This feature does not add PixiJS runtime, video generation, UI integration or production caregiver persistence.
