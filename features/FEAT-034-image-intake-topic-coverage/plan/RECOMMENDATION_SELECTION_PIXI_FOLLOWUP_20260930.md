# Recommendation-selection consistency and Pixi follow-up

Status: APPROVED by owner requests “cần fix lại” and “có thể check log để fix cái bug trên”. Readiness/history question is informational, not approval to restore removed gates.

## Observations

- Latest local session successfully loaded source/package/mask; its package is unknown/CUTOUT_MICRO_MOTION, no independently renderable parts, 20-second root motion with maximum Y translation 0.012 stage units. This is not full auto-rig.
- Several filter attempts preceded successful preparation. HTTP 200 is a result envelope, not proof that selection passed.

## Plan / acceptance

Confirmed selection cause: discovery emits ACT-0106/0110/0118 although final V4 admission rejects their unsupported policy constraints. Share final safety admission with discovery; keep these constraints intact, so fewer cards may remain until their conditions have an explicit supported confirmation source. Do not represent such exclusions as readiness/history failures.

Confirmed motion mismatch: cutout player applies root translation only; bird/flower/person full-rig tracks may contain only scale/rotation or child-bone movement, making a successful cutout timeline visually stationary. Author a cutout-specific root translation track, bounded to 0.024 stage units, with multiple beats then rest and no scale/rotation. Named common animals map to existing generic-organic classification, not invented anatomy. Label cutout delivery honestly.

1. Reproduce selection of non-first suggested cards; align suggestion eligibility and final selection using the same versioned policy, without relaxing age/adult/safety rules. Preserve exact chosen activity/version and allow recovery after rejection.
2. Inspect actual Pixi timeline/render state before treating the screenshot as a playback failure. Fix verified animation/lifecycle defects and misleading progress copy. Do not invent dog anatomy, widen mask gates, add whole-image zoom/rotation, or claim full rigging without validated part masks.
3. Synthetic regressions for non-first selection and supported playback, focused tests, feature-local evidence and local restarts/builds as needed. External deployment remains separate.
4. Explain current readiness/history behavior; do not reinstate checklist/profile fields absent an explicit owner choice.
