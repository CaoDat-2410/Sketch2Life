# FEAT-020 Montessori Demo Profile Decisions

## M-020-01 — Readiness baseline

**Status:** confirmed
**Date:** 2026-09-12

For every supported age band, the demo uses the observable `readiness_criteria` from the current golden catalog as its baseline. The workflow must evaluate readiness together with age, prerequisite, safety, supervision, material, and active-status rules before ranking or selecting an activity.

The demo must not invent diagnostic or psychological readiness claims. If the input/context does not satisfy the catalog readiness rule, the run returns a typed blocked/no-result status rather than forcing a recommendation.

## Remaining profile questions

These remain separate decisions:

1. available materials and allowed household substitutes;
2. supervision level and activity duration;
3. safety, allergy, motor, sensory, or accessibility constraints.
