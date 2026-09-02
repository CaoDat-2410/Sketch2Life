# Phase 2 - Contracts and fixtures

## Purpose

Define the typed boundary for Person 4's standalone learning-media POC before implementing the library, resolver, generator, or validators.

## Contract rules

- Unknown fields are rejected at the feature boundary.
- `LearningObjective` is versioned and locale-aware.
- Reviewed assets are discriminated by `asset_type`.
- Generation briefs are bounded to 5-10 seconds.
- `MicroVideoAsset` and `ReviewedStillNarrationAsset` form the player-facing learning explanation union.
- Provenance is required for reviewed assets.
- Personality, diagnosis, and psychological fields are not part of the contract.

## Verification

Run from the repository root after the backend environment is installed:

```bash
cd backend
PYTHONPATH=../features/FEAT-005-backend-experience/src pytest ../features/FEAT-005-backend-experience/tests/test_schemas.py
```
