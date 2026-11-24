# ADR-0024: Qwen3.8-27B-FP8 development text-worker candidate

- **Date:** 2026-11-22
- **Status:** Accepted for the FEAT-082 development proof only; production selection remains open.
- **Authority:** Owner-approved FEAT-082 Plan Rev1 and Amendments A–G.
- **SRS:** FEAT-063 v2.7-draft is the current unsigned product baseline. This ADR does not amend or sign off the SRS.

## Context

The Modal language/audio development app shares one text checkpoint across Parent story and activity suggestions and Teacher lesson-plan/Sketch Deck workloads. FEAT-082 evaluates the revision-pinned Qwen3.8-27B-FP8 checkpoint on Modal L40S and improves Parent story specificity. The active Parent UI and API are in `feature/fe-mobile-remediation`; its existing persisted activity selection must be reused.

## Decision

1. Use `Qwen/Qwen3.8-27B-FP8@c3a462cc3d38cf351f3b26cbd763469eeb74ef81` for shared text workloads in the Modal `dev` app, restricted to L40S. Keep drawing VLM on Qwen3.5.
2. Preserve prior model assets and do not silently fall back to another checkpoint.
3. Pass a versioned story input containing the bounded run topic and, when present, subject-learning notes from the exact pinned lesson. Include lesson script direction only when its pinned permission flag allows it. Exclude profile identity and free-text profile interests.
4. Keep the current story output contract and safety/business gates. This candidate does not enable video generation or change the product SRS.
5. Limit live verification to the approved synthetic Parent Android UI story attempt; stop the language/audio app afterward.

## Consequences

- Parent and Teacher text API provenance must report the same Qwen3.8 revision as the worker.
- A single successful synthetic call is an integration proof, not a quality benchmark or production approval.
- Any model-load, schema, parser, or terminal worker failure is recorded and ends the authorized inference attempt; no blind retry or fallback is allowed.
- Modal volumes retain weights after the app stops; stopping the app prevents active worker containers, not storage charges for retained volume data.
