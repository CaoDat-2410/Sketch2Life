# Amendment Rev87.11-B — Quality SVG illustration with progressive stroke overlay

**Feature:** FEAT-063 system architecture rearchitecture<br>
**Date:** 2026-11-14<br>
**Status:** Approved under the owner's clarification of the active SVG-guide fix.<br>
**Parent plan:** PLAN_REV87_11_ARCADIA_DERIVED_PARENT_SVG_GUIDE_20261114.md<br>
**Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned. SRS §§1–31 remain unchanged.

## Owner clarification

The complete SVG illustration may contain filled and colored shapes; the whole illustration is not required to be composed only of drawing strokes. The guide's purpose is to teach how the subject is formed, with ordered strokes appearing progressively like the provided HTML example: completed strokes stay visible, and the current stroke is highlighted and animated.

## Objective

Return two distinct vector layers for the supported Arcadia chicken topic:

1. A sanitized, pinned, quality full-illustration SVG parsed from the CC0 dataset, preserving its fills and colors as the visual reference.
2. The separate authored progressive stroke guide, whose paths encode the child-facing drawing order.

The Parent canvas will show the quality illustration as a quiet reference underlay and draw the ordered guide paths over it. At each stage, previous strokes remain solid and dark; strokes for the current stage are blue and animate one at a time; future strokes remain hidden. This supersedes the original Rev87.11 acceptance wording that treated the child guide itself as only newly authored outline strokes or expected dashed current strokes.

## Implementation changes

- Extend only the source-derived Parent response with a distinct reference illustration document; retain the current guide document, step metadata, source/derivation provenance, review-required draft state, and current Modal fallback for unsupported topics.
- Parse only the exact pinned Arcadia SVG hash. Resolve its six known CSS classes into explicit fill/stroke attributes and allow only the static tags/path attributes required by this source. Reject transforms, external references, scripts, entities, unexpected tags/attributes, invalid colors, overlong data, or a source-hash mismatch. Do not return raw CSS/XML or allow client-supplied SVG through this route.
- Keep the source artwork and guide geometry in separate documents with square viewBoxes; render each into the same square canvas without changing either source.
- Update the mobile renderer to layer the reference illustration under the guide. Animate current-stage paths in animation_order, leave prior paths complete, and do not render future paths. Preserve adult review and skip/capture behavior.
- Add focused source sanitizer/response tests and mobile renderer contract checks. Generate final and intermediate-stage raster evidence from the real response/source. No Modal/GPU request, no AI output fixture, no database mutation, and no service restart.
- Update the existing EV-063-102 report and SRS §32 only; target SRS §§1–31 stay unchanged.

## Additional files and acceptance criteria

Additional in-scope file: apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx. Other implementation and evidence paths remain those listed in the approved Rev87.11 plan.

Acceptance: the source response includes the pinned full-color illustration layer and a separate 4–8-stage guide; source paths retain safe fill/stroke appearance; current stage animates blue strokes in the declared order while prior stages remain visible and future strokes are absent; the output is rendered and visually checked; all existing sanitizer, source hash, anatomy/topology, adult review, and unsupported-topic fallback behavior remain intact. Focused tests pass, and the evidence report identifies that focused route tests override auth/database dependencies.
