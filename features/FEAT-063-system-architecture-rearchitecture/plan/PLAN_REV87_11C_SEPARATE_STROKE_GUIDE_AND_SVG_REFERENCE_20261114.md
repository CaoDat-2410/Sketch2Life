# Amendment Rev87.11-C — Separate progressive drawing guide from finished SVG reference

**Feature:** FEAT-063 — system architecture rearchitecture
**Date:** 2026-11-14
**Status:** Approved under the owner's direct clarification that the SVG may be a high-quality filled/color illustration while the drawing guide is a separate sequence of strokes, like the supplied HTML.
**Baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned. SRS §§1–31 remain unchanged.

## Objective

Correct the Parent chicken guide so its progressive lines teach a recognizable drawing sequence. Keep the pinned, sanitized, full-color Arcadia SVG as an independent finished illustration. Do not fade that completed picture behind the drawing steps: the current output has different poses in the reference and guide, so an underlay confuses the child and obscures the blue strokes. The guide is the default view; the child/adult can switch to the finished illustration and back without losing the selected step.

## Approved changes

1. Revise the source-specific chicken derivation to a versioned, left-facing sequence that matches the reference illustration's pose: horizontal body; connected neck/head; beak, comb and eye; tail and wing; grounded legs/feet; then feather details. Keep 4–8 progressive stages, distinct open strokes, valid part dependencies and per-path source lineage. Preserve sanitizer and hard anatomy/topology checks.
2. Keep `reference_illustration` in the existing Parent source-derived API response, preserving the pinned 77-path full-color SVG and its provenance. Render this as a separate view, never as a background beneath the drawing strokes.
3. In the Parent guide screen, default to ordered strokes on a plain white canvas. Offer one small toggle to view the completed SVG illustration, then return to the same guide step. Current-stage paths draw in blue in `animation_order`; completed paths remain dark; future paths remain hidden.
4. Render actual API/source output into evidence: intermediate stroke-only stages and the full-color reference as a separate artifact. Do not call Modal or use fixture response data.
5. Update the existing Rev87.11-B evidence/report and FEAT-063 implementation records; add only dated as-built evidence in SRS §32. Do not change requirements in §§1–31.

## Acceptance criteria

- The default guide canvas contains only the staged stroke drawing; no completed full-color subject is visible behind it.
- The 4–8 stage guide reads as the same chicken pose as the curated reference; its body is a natural horizontal form, the head/beak/comb connect, the wing and tail attach, and both legs reach the ground.
- Blue strokes appear progressively in declared order, with completed strokes dark and future paths absent.
- A separate view displays the actual sanitized full-color SVG, and returning to drawing preserves the selected stage.
- Parent source-derived route still returns its truthful draft contract and both distinct documents. Focused source/topology/API and mobile tests pass; render evidence is inspected.
- No Modal/GPU inference, database change, service restart, fixture response, account/consent/child-data mutation, commit, push, or merge.

## Scope

- `deployment/modal/srs_v23/data/arcadia_organism_strokes/arcadia-gallus-derived-guide-v2.json` (new immutable guide revision)
- `backend/src/sketch2life/contracts/schemas/svg_engine.py`
- `backend/src/sketch2life/domain/svg_engine.py` only if the approved left-facing source-matched guide requires a corresponding direction-neutral hard check
- `backend/src/sketch2life/infrastructure/svg/arcadia_gallus_guide.py`
- focused backend source/topology tests
- `apps/ui-mobile/src/parent/domain/svgGuide.ts`
- `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`
- focused mobile renderer tests
- existing EV-063-102 evidence directory and FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, evidence index, and SRS §32 only
