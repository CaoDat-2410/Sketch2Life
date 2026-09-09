# FEAT-018 live image and canvas context

- Status: AWAITING_APPROVAL
- Plan revision: 2 (ExperienceSpec engine refinement proposed; awaiting approval)
- Owner: shared integration allocation pending contract freeze approval
- Goal: run a non-sensitive real JPG/PNG through validation, backend-only Qwen3-VL understanding, Gate A, one-anchor/one-objective ExperienceSpec compilation, P1/Gate B, PixiJS canvas, P4 cache/fallback, off-screen handoff, gallery journey and feedback.
- Data policy: non-sensitive test image only; no child/personal data, production data, or provider credential in Git/mobile/evidence.
- Dependencies: FEAT-003 understanding contracts, FEAT-015 fixture contracts, FEAT-016 runtime/session contracts, FEAT-017 live Lightning development path, FEAT-004 PixiJS/GSAP renderer plan, ADR-0006 allocation rules.
- Contract authority: `plan/CONTRACT_FREEZE.md`.
- Pilot: 20 golden activities for full device/integration flow; 100 MVP activities for offline catalog/reference validation.

## Current state

The repository has a fixture UI and backend-only live P2 route. PixiJS/GSAP dependencies exist in `packages/art-renderer`, but the renderer runtime/bridge, approved asset pack, ExperienceSpec engine and gallery journey are not implemented. The reviewed P1 catalog is not yet promoted into the main runtime. Implementation is blocked until plan revision 2, allocation, contract freeze and visual/data boundaries are approved.
