# FEAT-020 Semantic Personalization V2 Decisions

Status: APPROVED — IMPLEMENTED AND VALIDATED
Date: 2026-09-13

## Owner answers

- Shared age-invariant scene understanding: CONFIRMED.
- Hybrid curated semantic engine with bounded AI/embedding suggestions: CONFIRMED.
- Fallback as a first-class non-personalized mode: CONFIRMED.
- Restore reviewed sun/moon and botanical/nature concept routes: CONFIRMED.
- Create new V2 contracts instead of silently changing V1: CONFIRMED.
- Keep video, UI, real human gates, persistence and real feedback deferred: CONFIRMED.

## Decision consequences

1. V1 contracts remain backward-compatible and are not reinterpreted.
2. V2 owns the new semantic mode, shared scene identity and mode-aware Gate B.
3. A SAFE_FALLBACK result may be operationally ready for the demo but is not a personalized recommendation.
4. The same ConfirmedSceneUnderstandingV2 must be passed to every age-band sub-run.
5. The semantic catalog must represent concepts and concept families, not only activity-title strings.
6. Real-AI acceptance is evaluated by concept family, evidence and mode truthfulness rather than one fragile provider wording.